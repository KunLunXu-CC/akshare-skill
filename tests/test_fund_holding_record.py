#!/usr/bin/env python3
"""基金持仓记录能力的离线测试。"""

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPTS_PATH = Path(__file__).parents[1] / "scripts"
SCRIPT_PATH = SCRIPTS_PATH / "fund_holding_record.py"
sys.path.insert(0, str(SCRIPTS_PATH))
SPEC = importlib.util.spec_from_file_location("fund_holding_record", SCRIPT_PATH)
assert SPEC and SPEC.loader
FUND_RECORD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FUND_RECORD
SPEC.loader.exec_module(FUND_RECORD)


class FundHoldingRecordTest(unittest.TestCase):
    """验证截图参数解析和持仓计算。"""

    def test_解析截图参数并移除截断符(self):
        holding = FUND_RECORD.parse_record_spec(
            "广发纳斯达克100ETF联接…，43645.48，9352.72，27.27%"
        )

        self.assertEqual(holding.fund, "广发纳斯达克100ETF联接")
        self.assertAlmostEqual(holding.holding_amount, 43645.48)
        self.assertAlmostEqual(holding.holding_profit, 9352.72)
        self.assertAlmostEqual(holding.holding_return_rate, 27.27)

    def test_根据截图金额和净值计算成本价与份额(self):
        holding = FUND_RECORD.ScreenshotHoldingInput(
            fund="270023",
            holding_amount=74566.12,
            holding_profit=21480.10,
            holding_return_rate=40.46,
        )
        result = FUND_RECORD.calculate_holding_record(
            "270023",
            "广发全球精选股票(QDII)人民币A",
            "2026-08-27",
            6.3308,
            holding,
        )

        self.assertAlmostEqual(result.shares, 11778.31, places=2)
        self.assertAlmostEqual(result.cost_price, 4.5071, places=4)
        self.assertEqual(result.validation_status, "可记录")

    def test_截图收益率不一致时标记待确认(self):
        holding = FUND_RECORD.ScreenshotHoldingInput(
            fund="270023",
            holding_amount=74566.12,
            holding_profit=21480.10,
            holding_return_rate=30.0,
        )
        result = FUND_RECORD.calculate_holding_record(
            "270023",
            "示例基金",
            "2026-08-27",
            6.3308,
            holding,
        )

        self.assertEqual(result.validation_status, "待确认")

    def test_批量匹配基金并输出表格(self):
        records = [
            {
                "基金代码": "270023",
                "基金简称": "广发全球精选股票(QDII)人民币A",
                "2026-08-27-单位净值": "6.3308",
            }
        ]
        holdings = [
            FUND_RECORD.ScreenshotHoldingInput(
                fund="广发全球精选",
                holding_amount=74566.12,
                holding_profit=21480.10,
                holding_return_rate=40.46,
            )
        ]
        results = FUND_RECORD.build_holding_records(records, holdings)
        table = FUND_RECORD.format_markdown_table(results)

        self.assertEqual(results[0].fund_code, "270023")
        self.assertIn("| 基金 | 成本价 | 份额 | 处理结果 |", table)
        self.assertIn("4.5071", table)
        self.assertIn("11778.31", table)

    def test_歧义基金不阻断其他记录(self):
        records = [
            {
                "基金代码": "270023",
                "基金简称": "广发全球精选股票(QDII)人民币A",
                "2026-08-27-单位净值": "6.3308",
            },
            {
                "基金代码": "270042",
                "基金简称": "广发纳斯达克100ETF联接人民币(QDII)A",
                "2026-08-27-单位净值": "8.2095",
            },
            {
                "基金代码": "006479",
                "基金简称": "广发纳斯达克100ETF联接人民币(QDII)C",
                "2026-08-27-单位净值": "7.9000",
            },
        ]
        holdings = [
            FUND_RECORD.ScreenshotHoldingInput("270023", 74566.12, 21480.10),
            FUND_RECORD.ScreenshotHoldingInput(
                "广发纳斯达克100ETF联接", 43645.48, 9352.72
            ),
        ]
        outputs = FUND_RECORD.build_holding_records_with_errors(records, holdings)

        self.assertIsInstance(outputs[0], FUND_RECORD.FundHoldingRecordResult)
        self.assertIsInstance(outputs[1], FUND_RECORD.FundHoldingRecordError)
        self.assertEqual(outputs[1].validation_status, "待确认")


if __name__ == "__main__":
    unittest.main()
