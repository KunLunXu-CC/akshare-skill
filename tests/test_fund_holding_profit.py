#!/usr/bin/env python3
"""基金持仓收益能力的离线测试。"""

import importlib.util
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "fund_holding_profit.py"
SPEC = importlib.util.spec_from_file_location("fund_holding_profit", SCRIPT_PATH)
assert SPEC and SPEC.loader
FUND_HOLDING = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FUND_HOLDING
SPEC.loader.exec_module(FUND_HOLDING)


class FundHoldingProfitTest(unittest.TestCase):
    """验证基金匹配、字段解析和收益计算。"""

    def setUp(self):
        self.records = [
            {
                "基金代码": "270023",
                "基金简称": "广发全球精选股票(QDII)",
                "2026-08-26-单位净值": "6.2376",
                "2026-08-25-单位净值": "6.1000",
                "日增长率": "2.26%",
            },
            {
                "基金代码": "000002",
                "基金简称": "示例成长混合C",
                "2026-08-28-单位净值": "1.1000",
                "日增长率": "-0.50",
            },
        ]

    def test_查找技能持久化虚拟环境(self):
        with tempfile.TemporaryDirectory() as directory:
            skill_root = Path(directory)
            venv_python = skill_root / ".venv" / "bin" / "python"
            venv_python.parent.mkdir(parents=True)
            venv_python.touch()

            self.assertEqual(
                FUND_HOLDING.find_skill_venv_python(skill_root),
                venv_python,
            )

    def test_按截图参数计算持仓收益(self):
        record = FUND_HOLDING.resolve_fund(self.records, "270023")
        result = FUND_HOLDING.build_result(record, cost_price=4.5071, shares=11778.31)

        self.assertEqual(result.fund_code, "270023")
        self.assertEqual(result.data_date, "2026-08-26")
        self.assertAlmostEqual(result.unit_nav, 6.2376)
        self.assertAlmostEqual(result.total_cost, 53086.02, places=2)
        self.assertAlmostEqual(result.current_value, 73468.39, places=2)
        self.assertAlmostEqual(result.holding_profit, 20382.37, places=2)
        self.assertAlmostEqual(result.holding_return_rate, 38.39, places=2)
        self.assertAlmostEqual(result.daily_profit, 1620.70, places=2)

    def test_按完整名称查询(self):
        record = FUND_HOLDING.resolve_fund(self.records, "示例成长混合C")
        self.assertEqual(record["基金代码"], "000002")

    def test_名称不唯一时要求使用代码(self):
        records = self.records + [
            {"基金代码": "000003", "基金简称": "示例成长混合B"}
        ]
        with self.assertRaisesRegex(FUND_HOLDING.FundQueryError, "匹配到多个结果"):
            FUND_HOLDING.resolve_fund(records, "示例成长")

    def test_拒绝无效成本和份额(self):
        with self.assertRaisesRegex(FUND_HOLDING.FundQueryError, "成本价必须大于零"):
            FUND_HOLDING.build_result(self.records[0], 0, 100)
        with self.assertRaisesRegex(FUND_HOLDING.FundQueryError, "持有份额必须大于零"):
            FUND_HOLDING.build_result(self.records[0], 1, 0)

    def test_批量查询保持输入顺序(self):
        holdings = [
            FUND_HOLDING.parse_holding_spec("270023,4.5071,11778.31"),
            FUND_HOLDING.parse_holding_spec("示例成长混合C，1.0000，2000"),
        ]
        results = FUND_HOLDING.build_results(self.records, holdings)

        self.assertEqual([result.fund_code for result in results], ["270023", "000002"])
        self.assertAlmostEqual(results[1].holding_profit, 200.0)

        table = FUND_HOLDING.format_markdown_table(results)
        self.assertEqual(table.count("\n| "), 3)
        self.assertIn("270023", table)
        self.assertIn("000002", table)
        self.assertIn("| 基金 | 日期 | 日涨幅 |", table)
        self.assertNotIn("数据日期", table)
        self.assertNotIn("前一净值", table)
        self.assertNotIn("前净值", table)
        self.assertIn("持仓收益", table)
        self.assertNotIn("价格状态", table)
        self.assertNotIn("单位净值", table)
        self.assertNotIn("成本价", table)
        self.assertNotIn("份额", table)
        self.assertNotIn("当前市值", table)
        self.assertIn("当日收益 **暂无**", table)

        complete_table = FUND_HOLDING.format_markdown_table(
            [results[0], FUND_HOLDING.replace(results[1], daily_profit=90.0)]
        )
        self.assertIn(
            "合计持有成本 **¥55,086.02**，持仓收益 **¥20,582.37**，"
            "当日收益 **¥1,710.70**",
            complete_table,
        )

    def test_拒绝错误的批量参数格式(self):
        with self.assertRaisesRegex(FUND_HOLDING.FundQueryError, "格式错误"):
            FUND_HOLDING.parse_holding_spec("270023,4.5071")

    def test_空日增长率时按前后净值计算(self):
        record = dict(self.records[0])
        record["日增长率"] = ""
        result = FUND_HOLDING.build_result(record, 4.5071, 11778.31)

        self.assertAlmostEqual(result.daily_growth_rate, 2.2557, places=4)
        self.assertAlmostEqual(result.daily_profit, 1620.70, places=2)

    def test_识别盘中盘后和非交易日(self):
        self.assertEqual(
            FUND_HOLDING.determine_market_stage(datetime(2026, 8, 28, 10, 30)),
            "盘中",
        )
        self.assertEqual(
            FUND_HOLDING.determine_market_stage(datetime(2026, 8, 28, 16, 30)),
            "盘后",
        )
        self.assertEqual(
            FUND_HOLDING.determine_market_stage(datetime(2026, 8, 29, 10, 30)),
            "非交易日",
        )

    def test_盘中优先使用当日估值(self):
        holding = FUND_HOLDING.HoldingInput("270023", 4.5071, 11778.31)
        estimations = [
            {
                "基金代码": "270023",
                "基金名称": "广发全球精选股票(QDII)",
                "2026-08-28-估算数据-估算值": "6.3000",
                "2026-08-28-估算数据-估算增长率": "1.00%",
            }
        ]
        result = FUND_HOLDING.build_market_results(
            self.records,
            estimations,
            [holding],
            market_stage="盘中",
            today="2026-08-28",
        )[0]

        self.assertEqual(result.price_type, "盘中估值")
        self.assertEqual(result.data_date, "2026-08-28")
        self.assertAlmostEqual(result.unit_nav, 6.3)
        self.assertAlmostEqual(result.daily_profit, (6.3 - 6.2376) * 11778.31)

    def test_盘后优先使用已公布当日净值(self):
        record = {
            "基金代码": "270023",
            "基金简称": "广发全球精选股票(QDII)",
            "2026-08-28-单位净值": "6.4000",
            "2026-08-27-单位净值": "6.3000",
            "日增长率": "",
        }
        holding = FUND_HOLDING.HoldingInput("270023", 4.5071, 11778.31)
        result = FUND_HOLDING.build_market_results(
            [record],
            [],
            [holding],
            market_stage="盘后",
            today="2026-08-28",
        )[0]

        self.assertEqual(result.price_type, "盘后净值")
        self.assertAlmostEqual(result.daily_growth_rate, 1.5873, places=4)

    def test_盘后净值未公布时使用当日估值并标记待确认(self):
        holding = FUND_HOLDING.HoldingInput("270023", 4.5071, 11778.31)
        estimations = [
            {
                "基金代码": "270023",
                "基金名称": "广发全球精选股票(QDII)",
                "2026-08-28-估算数据-估算值": "6.3000",
                "2026-08-28-估算数据-估算增长率": "1.00%",
            }
        ]
        result = FUND_HOLDING.build_market_results(
            self.records,
            estimations,
            [holding],
            market_stage="盘后",
            today="2026-08-28",
        )[0]

        self.assertEqual(result.price_type, "盘后估值（净值待公布）")
        table = FUND_HOLDING.format_markdown_table([result], today="2026-08-28")
        self.assertIn("最终收益以基金公司公布净值为准", table)

    def test_净值字段为空时使用历史净值兜底(self):
        record = {
            "基金代码": "270023",
            "基金简称": "广发全球精选股票(QDII)",
            "单位净值": "",
            "日增长率": "",
        }
        history_rows = [
            {"净值日期": "2026-08-25", "单位净值": "6.1000", "日增长率": ""},
            {"净值日期": "2026-08-26", "单位净值": "6.2376", "日增长率": ""},
        ]
        holding = FUND_HOLDING.HoldingInput("270023", 4.5071, 11778.31)
        result = FUND_HOLDING.build_market_results(
            [record],
            [],
            [holding],
            market_stage="非交易日",
            today="2026-08-29",
            history_loader=lambda code, name: FUND_HOLDING.history_rows_to_record(
                history_rows, code, name
            ),
        )[0]

        self.assertEqual(result.price_type, "非交易日最新净值")
        self.assertEqual(result.data_date, "2026-08-26")
        self.assertAlmostEqual(result.unit_nav, 6.2376)

    def test_当前净值存在但前一净值缺失时读取历史数据补齐(self):
        record = {
            "基金代码": "270023",
            "基金简称": "广发全球精选股票(QDII)人民币A",
            "2026-08-27-单位净值": "6.3308",
            "日增长率": "",
        }
        history_rows = [
            {"净值日期": "2026-08-26", "单位净值": "6.2376", "日增长率": ""},
            {"净值日期": "2026-08-27", "单位净值": "6.3308", "日增长率": ""},
        ]
        holding = FUND_HOLDING.HoldingInput("270023", 4.5071, 11778.31)
        result = FUND_HOLDING.build_market_results(
            [record],
            [],
            [holding],
            market_stage="非交易日",
            today="2026-08-29",
            history_loader=lambda code, name: FUND_HOLDING.history_rows_to_record(
                history_rows, code, name
            ),
        )[0]

        self.assertAlmostEqual(result.previous_unit_nav, 6.2376)
        self.assertAlmostEqual(result.daily_growth_rate, 1.4942, places=4)
        self.assertAlmostEqual(
            result.daily_profit,
            (6.3308 - 6.2376) * 11778.31,
        )
        table = FUND_HOLDING.format_markdown_table([result], today="2026-08-29")
        self.assertNotIn("前净值", table)
        self.assertNotIn("6.2376 元", table)


if __name__ == "__main__":
    unittest.main()
