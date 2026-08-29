#!/usr/bin/env python3
"""根据持有金额、持有收益和基金净值计算成本价与份额。"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from fund_holding_profit import (
    FundQueryError,
    NavDataUnavailableError,
    extract_navs,
    fetch_fund_records,
    fetch_history_record,
    load_akshare,
    parse_number,
    resolve_fund,
    reuse_skill_venv_if_needed,
)


@dataclass(frozen=True)
class ScreenshotHoldingInput:
    """一条从截图提取的持仓数据。"""

    fund: str
    holding_amount: float
    holding_profit: float
    holding_return_rate: float | None = None


@dataclass(frozen=True)
class FundHoldingRecordResult:
    """可写入记忆的基金持仓记录。"""

    fund_code: str
    fund_name: str
    cost_price: float
    shares: float
    data_date: str | None
    unit_nav: float
    holding_amount: float
    holding_profit: float
    holding_return_rate: float
    validation_status: str


@dataclass(frozen=True)
class FundHoldingRecordError:
    """无法唯一确认的截图持仓。"""

    fund: str
    error: str
    validation_status: str = "待确认"


def normalize_screenshot_identifier(value: str) -> str:
    """移除截图截断符，保留可用于唯一匹配的名称前缀。"""
    identifier = value.strip().rstrip(".…。 ")
    if not identifier:
        raise FundQueryError("基金代码或名称不能为空。")
    return identifier


def parse_record_spec(value: str) -> ScreenshotHoldingInput:
    """解析“基金,持有金额,持有收益[,收益率]”参数。"""
    parts = [part.strip() for part in value.replace("，", ",").rsplit(",", 3)]
    if len(parts) not in {3, 4} or not all(parts[:3]):
        raise FundQueryError(
            f"截图持仓参数格式错误：{value}；应为"
            "“基金,持有金额,持有收益[,收益率]”。"
        )
    return ScreenshotHoldingInput(
        fund=normalize_screenshot_identifier(parts[0]),
        holding_amount=parse_number(parts[1], "持有金额"),
        holding_profit=parse_number(parts[2], "持有收益"),
        holding_return_rate=(
            parse_number(parts[3], "持有收益率") if len(parts) == 4 else None
        ),
    )


def calculate_holding_record(
    fund_code: str,
    fund_name: str,
    data_date: str | None,
    unit_nav: float,
    holding: ScreenshotHoldingInput,
    rate_tolerance: float = 0.15,
) -> FundHoldingRecordResult:
    """根据最新公布净值计算份额和每份成本价。"""
    if holding.holding_amount <= 0:
        raise FundQueryError("持有金额必须大于零。")
    if unit_nav <= 0:
        raise FundQueryError("单位净值必须大于零。")

    total_cost = holding.holding_amount - holding.holding_profit
    if total_cost <= 0:
        raise FundQueryError("持有金额减去持有收益后必须大于零。")

    shares = holding.holding_amount / unit_nav
    cost_price = total_cost / shares
    calculated_rate = holding.holding_profit / total_cost * 100
    validation_status = "可记录"
    if (
        holding.holding_return_rate is not None
        and abs(calculated_rate - holding.holding_return_rate) > rate_tolerance
    ):
        validation_status = "待确认"

    return FundHoldingRecordResult(
        fund_code=fund_code,
        fund_name=fund_name,
        cost_price=cost_price,
        shares=shares,
        data_date=data_date,
        unit_nav=unit_nav,
        holding_amount=holding.holding_amount,
        holding_profit=holding.holding_profit,
        holding_return_rate=calculated_rate,
        validation_status=validation_status,
    )


def build_holding_records(
    records: Iterable[dict[str, Any]],
    holdings: Iterable[ScreenshotHoldingInput],
    history_loader: Any | None = None,
) -> list[FundHoldingRecordResult]:
    """匹配基金并批量计算持仓记录。"""
    rows = list(records)
    results = []
    for holding in holdings:
        record = resolve_fund(rows, holding.fund)
        fund_code = str(record.get("基金代码", "")).strip()
        fund_name = str(record.get("基金简称", "")).strip()
        try:
            data_date, unit_nav, _ = extract_navs(record)
        except NavDataUnavailableError:
            if history_loader is None:
                raise
            history_record = history_loader(fund_code, fund_name)
            data_date, unit_nav, _ = extract_navs(history_record)
        results.append(
            calculate_holding_record(
                fund_code,
                fund_name,
                data_date,
                unit_nav,
                holding,
            )
        )
    return results


def build_holding_records_with_errors(
    records: Iterable[dict[str, Any]],
    holdings: Iterable[ScreenshotHoldingInput],
    history_loader: Any | None = None,
) -> list[FundHoldingRecordResult | FundHoldingRecordError]:
    """逐条计算持仓，让歧义记录不阻断其他基金。"""
    rows = list(records)
    outputs: list[FundHoldingRecordResult | FundHoldingRecordError] = []
    for holding in holdings:
        try:
            outputs.extend(
                build_holding_records(rows, [holding], history_loader=history_loader)
            )
        except FundQueryError as exc:
            outputs.append(
                FundHoldingRecordError(fund=holding.fund, error=str(exc))
            )
    return outputs


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="从截图数据计算基金持仓记录")
    parser.add_argument(
        "--record",
        action="append",
        required=True,
        metavar="基金,持有金额,持有收益[,收益率]",
        help="增加一条截图持仓；可重复使用",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    return parser


def format_markdown_table(
    results: Iterable[FundHoldingRecordResult | FundHoldingRecordError],
) -> str:
    """输出适合确认和写入记忆的持仓表格。"""
    lines = [
        "| 基金 | 成本价 | 份额 | 处理结果 |",
        "| --- | ---: | ---: | --- |",
    ]
    for result in results:
        if isinstance(result, FundHoldingRecordError):
            lines.append(
                f"| {result.fund} | — | — | {result.validation_status}："
                f"{result.error} |"
            )
        else:
            lines.append(
                f"| {result.fund_name}（{result.fund_code}） | "
                f"{result.cost_price:.4f} | {result.shares:.2f} | "
                f"{result.validation_status} |"
            )
    return "\n".join(lines)


def main() -> int:
    """运行截图持仓计算。"""
    reuse_skill_venv_if_needed(Path(__file__).resolve())
    args = create_parser().parse_args()
    try:
        holdings = [parse_record_spec(value) for value in args.record]
        ak = load_akshare()
        results = build_holding_records_with_errors(
            fetch_fund_records(ak),
            holdings,
            history_loader=lambda code, name: fetch_history_record(ak, code, name),
        )
    except FundQueryError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                [asdict(result) for result in results],
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(format_markdown_table(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
