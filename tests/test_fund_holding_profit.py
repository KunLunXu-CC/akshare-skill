#!/usr/bin/env python3
"""基金持仓收益能力的离线测试。"""

import importlib.util
import sys
import unittest
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


if __name__ == "__main__":
    unittest.main()
