#!/usr/bin/env python3
"""查询开放式基金持仓收益、收益率、日涨幅和当日收益。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import re
import shlex
import sys
import unicodedata
from dataclasses import asdict, dataclass, replace
from datetime import datetime, time
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo


def find_skill_venv_python(skill_root: Path | None = None) -> Path | None:
    """查找技能目录中持久化虚拟环境的 Python。"""
    root = skill_root or Path(__file__).resolve().parents[1]
    candidates = (
        root / ".venv" / "bin" / "python",
        root / ".venv" / "Scripts" / "python.exe",
    )
    return next((path for path in candidates if path.is_file()), None)


def reuse_skill_venv_if_needed(script_path: Path | None = None) -> None:
    """当前解释器缺少 AkShare 时，自动切换到技能虚拟环境。"""
    if importlib.util.find_spec("akshare") is not None:
        return

    venv_python = find_skill_venv_python()
    if venv_python is None:
        return

    current_python = Path(sys.executable).absolute()
    if current_python == venv_python.absolute():
        return

    target_script = script_path or Path(__file__).resolve()
    os.execv(
        str(venv_python),
        [str(venv_python), str(target_script), *sys.argv[1:]],
    )


class FundQueryError(Exception):
    """基金查询无法完成。"""


class NavDataUnavailableError(FundQueryError):
    """最新净值数据不可用。"""


@dataclass(frozen=True)
class HoldingInput:
    """一只基金的持仓输入。"""

    fund: str
    cost_price: float
    shares: float


@dataclass(frozen=True)
class FundHoldingProfitResult:
    """基金持仓收益查询结果。"""

    fund_code: str
    fund_name: str
    data_date: str | None
    unit_nav: float
    previous_unit_nav: float | None
    daily_growth_rate: float | None
    cost_price: float
    shares: float
    total_cost: float
    current_value: float
    holding_profit: float
    holding_return_rate: float
    daily_profit: float | None
    price_type: str = "已公布净值"


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


def parse_optional_number(value: Any) -> float | None:
    """解析可为空的数字字段。"""
    try:
        return parse_number(value, "数值")
    except FundQueryError:
        return None


def normalize_data_date(value: Any) -> str | None:
    """将接口日期字段规范为 YYYY-MM-DD。"""
    match = re.match(r"(\d{4}-\d{2}-\d{2})", str(value).strip())
    return match.group(1) if match else None


def normalize_identifier(identifier: str) -> str:
    """规范基金代码或名称查询值。"""
    value = identifier.strip()
    if not value:
        raise FundQueryError("基金代码或名称不能为空。")
    if value.isdigit() and len(value) <= 6:
        return value.zfill(6)
    return value


def normalize_fund_name_for_match(value: Any) -> str:
    """规范基金名称中常见的全半角、标点和币种修饰。"""
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    for token in ("人民币", "美元现汇", "美元现钞"):
        text = text.replace(token, "")
    return re.sub(r"[\W_]+", "", text)


def parse_holding_spec(value: str) -> HoldingInput:
    """解析“基金,成本价,份额”格式的批量持仓参数。"""
    parts = [part.strip() for part in value.replace("，", ",").rsplit(",", 2)]
    if len(parts) != 3 or not all(parts):
        raise FundQueryError(
            f"持仓参数格式错误：{value}；应为“基金代码或名称,成本价,份额”。"
        )
    return HoldingInput(
        fund=parts[0],
        cost_price=parse_number(parts[1], "持仓成本价"),
        shares=parse_number(parts[2], "持有份额"),
    )


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
    if not partial_matches:
        normalized_query = normalize_fund_name_for_match(query)
        partial_matches = [
            row
            for row in rows
            if normalized_query
            and normalized_query
            in normalize_fund_name_for_match(row.get("基金简称", ""))
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
        raise NavDataUnavailableError("单位净值为空，无法计算持仓收益。")
    return None, current_nav, previous_nav


def calculate_result(
    *,
    fund_code: str,
    fund_name: str,
    data_date: str | None,
    unit_nav: float,
    previous_unit_nav: float | None,
    daily_growth_rate: float | None,
    cost_price: float,
    shares: float,
    price_type: str,
) -> FundHoldingProfitResult:
    """根据选定的净值或估值计算持仓结果。"""
    if cost_price <= 0:
        raise FundQueryError("持仓成本价必须大于零。")
    if shares <= 0:
        raise FundQueryError("持有份额必须大于零。")

    if daily_growth_rate is None and previous_unit_nav not in {None, 0}:
        daily_growth_rate = (unit_nav - previous_unit_nav) / previous_unit_nav * 100

    total_cost = cost_price * shares
    current_value = unit_nav * shares
    holding_profit = current_value - total_cost
    holding_return_rate = holding_profit / total_cost * 100
    daily_profit = None
    if previous_unit_nav is not None:
        daily_profit = (unit_nav - previous_unit_nav) * shares

    return FundHoldingProfitResult(
        fund_code=fund_code,
        fund_name=fund_name,
        data_date=data_date,
        unit_nav=unit_nav,
        previous_unit_nav=previous_unit_nav,
        daily_growth_rate=daily_growth_rate,
        cost_price=cost_price,
        shares=shares,
        total_cost=total_cost,
        current_value=current_value,
        holding_profit=holding_profit,
        holding_return_rate=holding_return_rate,
        daily_profit=daily_profit,
        price_type=price_type,
    )


def build_result(
    record: dict[str, Any], cost_price: float, shares: float
) -> FundHoldingProfitResult:
    """根据成本价、份额和最新净值计算持仓收益。"""
    data_date, unit_nav, previous_unit_nav = extract_navs(record)
    return calculate_result(
        fund_code=str(record.get("基金代码", "")).strip(),
        fund_name=str(record.get("基金简称", "")).strip(),
        data_date=data_date,
        unit_nav=unit_nav,
        previous_unit_nav=previous_unit_nav,
        daily_growth_rate=parse_optional_number(record.get("日增长率")),
        cost_price=cost_price,
        shares=shares,
        price_type="已公布净值",
    )


def build_results(
    records: Iterable[dict[str, Any]], holdings: Iterable[HoldingInput]
) -> list[FundHoldingProfitResult]:
    """按输入顺序计算多只基金的持仓收益。"""
    rows = list(records)
    return [
        build_result(
            resolve_fund(rows, holding.fund),
            cost_price=holding.cost_price,
            shares=holding.shares,
        )
        for holding in holdings
    ]


def determine_market_stage(now: datetime | None = None) -> str:
    """按中国内地基金交易时段判断当前市场阶段。"""
    current = now or datetime.now(ZoneInfo("Asia/Shanghai"))
    if current.tzinfo is None:
        current = current.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    else:
        current = current.astimezone(ZoneInfo("Asia/Shanghai"))

    if current.weekday() >= 5:
        return "非交易日"
    current_time = current.time().replace(tzinfo=None)
    if current_time < time(9, 30):
        return "盘前"
    if current_time < time(15, 0):
        return "盘中"
    return "盘后"


def extract_estimation(
    record: dict[str, Any], fallback_date: str
) -> tuple[str | None, float | None, float | None]:
    """提取估算日期、估算净值和估算增长率。"""
    estimate_date = None
    estimate_nav = None
    estimate_growth = None
    for column, value in record.items():
        column_text = str(column)
        if column_text.endswith("-估算数据-估算值"):
            estimate_nav = parse_optional_number(value)
            estimate_date = normalize_data_date(column_text) or fallback_date
        elif column_text.endswith("-估算数据-估算增长率"):
            estimate_growth = parse_optional_number(value)
    return estimate_date, estimate_nav, estimate_growth


def normalize_estimation_records(
    records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """统一估值接口和净值接口的基金名称字段。"""
    normalized = []
    for record in records:
        row = dict(record)
        row["基金简称"] = row.get("基金简称") or row.get("基金名称")
        normalized.append(row)
    return normalized


def select_market_result(
    published: FundHoldingProfitResult,
    estimation_record: dict[str, Any] | None,
    holding: HoldingInput,
    market_stage: str,
    today: str,
) -> FundHoldingProfitResult:
    """根据盘中、盘后和数据可用性选择计算价格。"""
    estimate_date = None
    estimate_nav = None
    estimate_growth = None
    if estimation_record is not None:
        estimate_date, estimate_nav, estimate_growth = extract_estimation(
            estimation_record, today
        )
    estimate_is_current = estimate_date == today and estimate_nav is not None

    if market_stage == "盘中" and estimate_is_current:
        return calculate_result(
            fund_code=published.fund_code,
            fund_name=published.fund_name,
            data_date=estimate_date,
            unit_nav=estimate_nav,
            previous_unit_nav=published.unit_nav,
            daily_growth_rate=estimate_growth,
            cost_price=holding.cost_price,
            shares=holding.shares,
            price_type="盘中估值",
        )

    if market_stage == "盘后":
        if published.data_date == today:
            return replace(published, price_type="盘后净值")
        if estimate_is_current:
            return calculate_result(
                fund_code=published.fund_code,
                fund_name=published.fund_name,
                data_date=estimate_date,
                unit_nav=estimate_nav,
                previous_unit_nav=published.unit_nav,
                daily_growth_rate=estimate_growth,
                cost_price=holding.cost_price,
                shares=holding.shares,
                price_type="盘后估值（净值待公布）",
            )
        return replace(published, price_type="最新净值（待更新）")

    if market_stage == "盘中":
        return replace(published, price_type="最新净值（暂无盘中估值）")
    if market_stage == "盘前":
        return replace(published, price_type="盘前最新净值")
    return replace(published, price_type="非交易日最新净值")


def merge_published_with_history(
    published: FundHoldingProfitResult,
    history: FundHoldingProfitResult,
    holding: HoldingInput,
) -> FundHoldingProfitResult:
    """使用历史数据补齐批量接口缺失的前一净值。"""
    if not published.data_date or (
        history.data_date and history.data_date >= published.data_date
    ):
        return history

    return calculate_result(
        fund_code=published.fund_code,
        fund_name=published.fund_name,
        data_date=published.data_date,
        unit_nav=published.unit_nav,
        previous_unit_nav=history.unit_nav,
        daily_growth_rate=published.daily_growth_rate,
        cost_price=holding.cost_price,
        shares=holding.shares,
        price_type=published.price_type,
    )


def build_market_results(
    published_records: Iterable[dict[str, Any]],
    estimation_records: Iterable[dict[str, Any]],
    holdings: Iterable[HoldingInput],
    *,
    market_stage: str,
    today: str,
    history_loader: Any = None,
) -> list[FundHoldingProfitResult]:
    """按市场阶段批量构建持仓结果，并在净值缺失时读取历史数据。"""
    published_rows = list(published_records)
    estimation_rows = normalize_estimation_records(estimation_records)
    results = []
    for holding in holdings:
        published_record = resolve_fund(published_rows, holding.fund)
        try:
            published = build_result(
                published_record, holding.cost_price, holding.shares
            )
        except NavDataUnavailableError:
            if history_loader is None:
                raise
            history_record = history_loader(
                str(published_record.get("基金代码", "")).strip(),
                str(published_record.get("基金简称", "")).strip(),
            )
            published = build_result(history_record, holding.cost_price, holding.shares)

        if published.previous_unit_nav is None and history_loader is not None:
            history_record = history_loader(
                published.fund_code,
                published.fund_name,
            )
            history = build_result(
                history_record, holding.cost_price, holding.shares
            )
            published = merge_published_with_history(published, history, holding)

        estimation_record = None
        try:
            estimation_record = resolve_fund(estimation_rows, published.fund_code)
        except FundQueryError:
            pass
        results.append(
            select_market_result(
                published,
                estimation_record,
                holding,
                market_stage,
                today,
            )
        )
    return results


def load_akshare() -> Any:
    """导入 AkShare，并给出可恢复的依赖提示。"""
    try:
        import akshare as ak
    except ImportError as exc:
        install_script = Path(__file__).resolve().with_name("install_akshare.sh")
        install_command = f"bash {shlex.quote(str(install_script))}"
        raise FundQueryError(
            "未安装 AkShare。请先征得用户同意，再运行 "
            f"{install_command}；安装成功后重试原查询。"
        ) from exc
    return ak


def fetch_fund_records(ak: Any) -> list[dict[str, Any]]:
    """通过 AkShare 获取开放式基金最新公布净值数据。"""
    try:
        data = ak.fund_open_fund_daily_em()
    except Exception as exc:
        raise FundQueryError(f"获取基金数据失败：{exc}") from exc

    if data is None or data.empty:
        raise FundQueryError("基金数据为空，请稍后重试。")
    return data.to_dict(orient="records")


def fetch_estimation_records(ak: Any) -> list[dict[str, Any]]:
    """获取当日基金估值；上游不可用时返回空列表并使用净值兜底。"""
    try:
        data = ak.fund_value_estimation_em(symbol="全部")
    except Exception:
        return []
    if data is None or data.empty:
        return []
    return data.to_dict(orient="records")


def history_rows_to_record(
    rows: Iterable[dict[str, Any]], fund_code: str, fund_name: str
) -> dict[str, Any]:
    """将单只基金历史净值转换为统一的最新净值记录。"""
    nav_rows = []
    for row in rows:
        data_date = normalize_data_date(row.get("净值日期"))
        unit_nav = parse_optional_number(row.get("单位净值"))
        if data_date and unit_nav is not None:
            nav_rows.append((data_date, unit_nav, row.get("日增长率")))
    nav_rows.sort(reverse=True)
    if not nav_rows:
        raise NavDataUnavailableError(f"基金 {fund_code} 暂无完整历史净值数据。")

    latest_date, latest_nav, growth = nav_rows[0]
    record: dict[str, Any] = {
        "基金代码": fund_code,
        "基金简称": fund_name,
        "单位净值": latest_nav,
        "日增长率": growth,
        f"{latest_date}-单位净值": latest_nav,
    }
    if len(nav_rows) > 1:
        previous_date, previous_nav, _ = nav_rows[1]
        record["前交易日-单位净值"] = previous_nav
        record[f"{previous_date}-单位净值"] = previous_nav
    return record


def fetch_history_record(ak: Any, fund_code: str, fund_name: str) -> dict[str, Any]:
    """在批量净值字段为空时读取单只基金历史净值兜底。"""
    try:
        data = ak.fund_open_fund_info_em(
            symbol=fund_code, indicator="单位净值走势"
        )
    except Exception as exc:
        raise FundQueryError(f"获取基金 {fund_code} 历史净值失败：{exc}") from exc
    if data is None or data.empty:
        raise NavDataUnavailableError(f"基金 {fund_code} 暂无历史净值数据。")
    return history_rows_to_record(data.to_dict(orient="records"), fund_code, fund_name)


def format_markdown_table(
    results: Iterable[FundHoldingProfitResult], today: str | None = None
) -> str:
    """将一只或多只基金的结果格式化为 Markdown 表格。"""
    rows = list(results)
    headers = [
        "基金",
        "日期",
        "日涨幅",
        "持有成本",
        "持仓收益",
        "收益率",
        "当日收益",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for result in rows:
        fund_name = result.fund_name.replace("|", "\\|")
        daily_profit = (
            f"{result.daily_profit:+,.2f} 元"
            if result.daily_profit is not None
            else "暂无"
        )
        daily_growth = (
            f"{result.daily_growth_rate:+.2f}%"
            if result.daily_growth_rate is not None
            else "暂无"
        )
        values = [
            f"{fund_name}（{result.fund_code}）",
            result.data_date or "接口未提供",
            daily_growth,
            f"{result.total_cost:,.2f} 元",
            f"{result.holding_profit:+,.2f} 元",
            f"{result.holding_return_rate:+.2f}%",
            daily_profit,
        ]
        lines.append("| " + " | ".join(values) + " |")

    total_cost = sum(result.total_cost for result in rows)
    total_holding_profit = sum(result.holding_profit for result in rows)
    daily_profits = [result.daily_profit for result in rows]
    total_daily_profit = (
        sum(profit for profit in daily_profits if profit is not None)
        if all(profit is not None for profit in daily_profits)
        else None
    )
    daily_profit_summary = (
        f"**¥{total_daily_profit:,.2f}**"
        if total_daily_profit is not None
        else "**暂无**"
    )
    lines.extend(
        [
            "",
            f"合计持有成本 **¥{total_cost:,.2f}**，"
            f"持仓收益 **¥{total_holding_profit:,.2f}**，"
            f"当日收益 {daily_profit_summary}",
        ]
    )

    current_date = today or datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    if any("估值" in result.price_type for result in rows):
        lines.extend(["", "提示：估值数据仅供盘中参考，最终收益以基金公司公布净值为准。"])
    if any(result.data_date != current_date for result in rows):
        lines.extend(
            ["", "提示：当天净值尚未公布或今天不是交易日，表中展示最新已公布数据。"]
        )
    return "\n".join(lines)


def format_text(result: FundHoldingProfitResult) -> str:
    """兼容单只基金调用并输出 Markdown 表格。"""
    return format_markdown_table([result])


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="查询开放式基金持仓收益")
    parser.add_argument("fund", nargs="?", help="基金代码、完整名称或名称片段")
    parser.add_argument(
        "--cost-price",
        type=float,
        help="每份基金的持仓成本价，单位为元",
    )
    parser.add_argument(
        "--shares",
        type=float,
        help="当前持有份额",
    )
    parser.add_argument(
        "--holding",
        action="append",
        default=[],
        metavar="基金,成本价,份额",
        help="增加一只基金持仓；可重复使用以批量查询",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    return parser


def build_holding_inputs(args: argparse.Namespace) -> list[HoldingInput]:
    """根据命令行参数生成单只或批量持仓输入。"""
    if args.holding:
        if args.fund is not None or args.cost_price is not None or args.shares is not None:
            raise FundQueryError(
                "批量查询时只能重复使用 --holding，不能同时使用单只基金参数。"
            )
        return [parse_holding_spec(value) for value in args.holding]

    if args.fund is None or args.cost_price is None or args.shares is None:
        raise FundQueryError(
            "请提供基金代码或名称、--cost-price 和 --shares，"
            "或至少提供一个 --holding。"
        )
    return [HoldingInput(args.fund, args.cost_price, args.shares)]


def main() -> int:
    """运行命令行查询。"""
    reuse_skill_venv_if_needed()
    args = create_parser().parse_args()
    try:
        holdings = build_holding_inputs(args)
        ak = load_akshare()
        current = datetime.now(ZoneInfo("Asia/Shanghai"))
        today = current.date().isoformat()
        market_stage = determine_market_stage(current)
        published_records = fetch_fund_records(ak)
        estimation_records = (
            fetch_estimation_records(ak)
            if market_stage in {"盘中", "盘后"}
            else []
        )
        results = build_market_results(
            published_records,
            estimation_records,
            holdings,
            market_stage=market_stage,
            today=today,
            history_loader=lambda code, name: fetch_history_record(
                ak, code, name
            ),
        )
    except FundQueryError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    if args.json:
        payload: Any = asdict(results[0]) if len(results) == 1 else [
            asdict(result) for result in results
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_markdown_table(results, today=today))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
