#!/usr/bin/env python3
"""查询开放式基金持仓收益、收益率、日涨幅和当日收益。"""

from __future__ import annotations

import argparse
import json
import math
import re
import shlex
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable


class FundQueryError(Exception):
    """基金查询无法完成。"""


@dataclass(frozen=True)
class FundHoldingProfitResult:
    """基金持仓收益查询结果。"""

    fund_code: str
    fund_name: str
    data_date: str | None
    unit_nav: float
    previous_unit_nav: float | None
    daily_growth_rate: float
    cost_price: float
    shares: float
    total_cost: float
    current_value: float
    holding_profit: float
    holding_return_rate: float
    daily_profit: float | None


def parse_number(value: Any, field_name: str) -> float:
    """将接口中的数字或百分数字符串转换为浮点数。"""
    if value is None:
        raise FundQueryError(f"{field_name}为空。")

    text = str(value).strip().replace(",", "").replace("%", "")
    if not text or text in {"--", "---", "None", "nan", "NaN"}:
        raise FundQueryError(f"{field_name}为空。")

    try:
        number = float(text)
    except (TypeError, ValueError) as exc:
        raise FundQueryError(f"无法解析{field_name}：{value}") from exc

    if not math.isfinite(number):
        raise FundQueryError(f"{field_name}不是有效数字。")
    return number


def normalize_identifier(identifier: str) -> str:
    """规范基金代码或名称查询值。"""
    value = identifier.strip()
    if not value:
        raise FundQueryError("基金代码或名称不能为空。")
    if value.isdigit() and len(value) <= 6:
        return value.zfill(6)
    return value


def resolve_fund(records: Iterable[dict[str, Any]], identifier: str) -> dict[str, Any]:
    """按基金代码、完整名称或唯一的名称片段定位基金。"""
    query = normalize_identifier(identifier)
    rows = list(records)

    code_matches = [row for row in rows if str(row.get("基金代码", "")).strip() == query]
    if code_matches:
        return code_matches[0]

    exact_name_matches = [
        row for row in rows if str(row.get("基金简称", "")).strip().casefold() == query.casefold()
    ]
    if len(exact_name_matches) == 1:
        return exact_name_matches[0]

    partial_matches = [
        row for row in rows if query.casefold() in str(row.get("基金简称", "")).strip().casefold()
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    if len(partial_matches) > 1:
        candidates = "、".join(
            f"{row.get('基金代码', '')} {row.get('基金简称', '')}" for row in partial_matches[:10]
        )
        suffix = "等" if len(partial_matches) > 10 else ""
        raise FundQueryError(f"基金名称匹配到多个结果，请改用基金代码：{candidates}{suffix}")

    raise FundQueryError(f"未找到基金：{identifier}")


def extract_navs(record: dict[str, Any]) -> tuple[str | None, float, float | None]:
    """提取数据日期、最新单位净值和前一交易日单位净值。"""
    current_nav = None
    previous_nav = None

    if "单位净值" in record:
        try:
            current_nav = parse_number(record["单位净值"], "单位净值")
        except FundQueryError:
            pass
    if "前交易日-单位净值" in record:
        try:
            previous_nav = parse_number(record["前交易日-单位净值"], "前交易日单位净值")
        except FundQueryError:
            pass

    dated_columns: list[tuple[str, str]] = []
    for column in record:
        match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})-单位净值", str(column))
        if match:
            dated_columns.append((match.group(1), str(column)))

    dated_navs: list[tuple[str, float]] = []
    for data_date, column in sorted(dated_columns, reverse=True):
        try:
            dated_navs.append((data_date, parse_number(record[column], "单位净值")))
        except FundQueryError:
            continue

    if dated_navs:
        data_date, dated_current_nav = dated_navs[0]
        current_nav = current_nav if current_nav is not None else dated_current_nav
        if previous_nav is None and len(dated_navs) > 1:
            previous_nav = dated_navs[1][1]
        return data_date, current_nav, previous_nav

    if current_nav is None:
        raise FundQueryError("单位净值为空，无法计算持仓收益。")
    return None, current_nav, previous_nav


def build_result(
    record: dict[str, Any], cost_price: float, shares: float
) -> FundHoldingProfitResult:
    """根据成本价、份额和最新净值计算持仓收益。"""
    if cost_price <= 0:
        raise FundQueryError("持仓成本价必须大于零。")
    if shares <= 0:
        raise FundQueryError("持有份额必须大于零。")

    growth_rate = parse_number(record.get("日增长率"), "日增长率")
    data_date, unit_nav, previous_unit_nav = extract_navs(record)
    total_cost = cost_price * shares
    current_value = unit_nav * shares
    holding_profit = current_value - total_cost
    holding_return_rate = holding_profit / total_cost * 100
    daily_profit = None
    if previous_unit_nav is not None:
        daily_profit = (unit_nav - previous_unit_nav) * shares

    return FundHoldingProfitResult(
        fund_code=str(record.get("基金代码", "")).strip(),
        fund_name=str(record.get("基金简称", "")).strip(),
        data_date=data_date,
        unit_nav=unit_nav,
        previous_unit_nav=previous_unit_nav,
        daily_growth_rate=growth_rate,
        cost_price=cost_price,
        shares=shares,
        total_cost=total_cost,
        current_value=current_value,
        holding_profit=holding_profit,
        holding_return_rate=holding_return_rate,
        daily_profit=daily_profit,
    )


def fetch_fund_records() -> list[dict[str, Any]]:
    """通过 AkShare 获取开放式基金最新净值数据。"""
    try:
        import akshare as ak
    except ImportError as exc:
        install_script = Path(__file__).resolve().with_name("install_akshare.sh")
        install_command = f"bash {shlex.quote(str(install_script))}"
        raise FundQueryError(
            "未安装 AkShare。请先征得用户同意，再运行 "
            f"{install_command}；安装成功后重试原查询。"
        ) from exc

    try:
        data = ak.fund_open_fund_daily_em()
    except Exception as exc:
        raise FundQueryError(f"获取基金数据失败：{exc}") from exc

    if data is None or data.empty:
        raise FundQueryError("基金数据为空，请稍后重试。")
    return data.to_dict(orient="records")


def format_text(result: FundHoldingProfitResult) -> str:
    """生成面向用户的中文文本。"""
    data_date = result.data_date or "接口未提供"
    lines = [
        f"基金：{result.fund_name}（{result.fund_code}）",
        f"数据日期：{data_date}",
        f"最新单位净值：{result.unit_nav:.4f} 元",
        f"持仓成本价：{result.cost_price:.4f} 元",
        f"持有份额：{result.shares:.2f}",
        f"持有成本：{result.total_cost:,.2f} 元",
        f"当前市值：{result.current_value:,.2f} 元",
        f"持仓收益：{result.holding_profit:+,.2f} 元",
        f"收益率：{result.holding_return_rate:+.2f}%",
        f"日涨幅：{result.daily_growth_rate:+.2f}%",
    ]
    if result.daily_profit is not None:
        lines.append(f"当日收益：{result.daily_profit:+,.2f} 元")
    if result.data_date and result.data_date != date.today().isoformat():
        lines.append("提示：当天净值尚未公布或今天不是交易日，以上为最新已公布数据。")
    return "\n".join(lines)


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="查询开放式基金持仓收益")
    parser.add_argument("fund", help="基金代码、完整名称或名称片段")
    parser.add_argument(
        "--cost-price",
        type=float,
        required=True,
        help="每份基金的持仓成本价，单位为元",
    )
    parser.add_argument(
        "--shares",
        type=float,
        required=True,
        help="当前持有份额",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    return parser


def main() -> int:
    """运行命令行查询。"""
    args = create_parser().parse_args()
    try:
        record = resolve_fund(fetch_fund_records(), args.fund)
        result = build_result(record, args.cost_price, args.shares)
    except FundQueryError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(format_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
