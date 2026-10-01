from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import unittest
from collections import Counter

from live_data_pipeline import board_for, leading_boards, stock_exclusion_reason
from logic_analysis import analyze_board, shared_event_evidence


class BoardClassificationTests(unittest.TestCase):
    def test_beijing_stock_exchange_codes_are_excluded(self):
        for code in ("430001", "830001", "920856"):
            with self.subTest(code=code):
                self.assertEqual(stock_exclusion_reason(code, "测试股份"), "北交所")

    def test_st_and_delisting_names_are_excluded(self):
        cases = {
            "ST测试": "ST",
            "*ST测试": "ST",
            "S*ST测试": "ST",
            "退市测试": "退市",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(stock_exclusion_reason("600001", name), expected)

    def test_regular_shanghai_and_shenzhen_stock_is_retained(self):
        self.assertIsNone(stock_exclusion_reason("600001", "测试股份"))

    def test_pharmaceutical_company_is_not_consumer(self):
        self.assertEqual(
            board_for(
                "医疗服务",
                "医药",
                "CRO、减肥药",
                "金华国资入主+CRO+创新药",
            ),
            "医药生物",
        )

    def test_medical_plate_overrides_food_industry(self):
        self.assertEqual(
            board_for(
                "食品加工",
                "医药",
                "合成生物、医药",
                "辅酶Q10+NMN概念+外销",
            ),
            "医药生物",
        )

    def test_secondary_hospital_concept_does_not_override_new_energy(self):
        self.assertEqual(
            board_for(
                "装修装饰",
                "光伏",
                "光伏、民营医院",
                "BIPV+海外订单+民营医院",
            ),
            "新能源",
        )

    def test_secondary_hospital_concept_does_not_override_chemicals(self):
        self.assertEqual(
            board_for(
                "农化制品",
                "化工",
                "甲醇、民营医院",
                "甲醇+尿素+煤化工+中报预计扭亏",
            ),
            "周期资源",
        )

    def test_food_and_beverage_remains_consumer(self):
        self.assertEqual(
            board_for(
                "饮料乳品",
                "食品饮料",
                "乳业、食品饮料",
                "乳业+烘焙食品+冷链物流",
            ),
            "大消费",
        )

    def test_equal_counts_are_reported_as_co_leaders(self):
        self.assertEqual(
            leading_boards(
                Counter(
                    {
                        "新能源": 18,
                        "周期资源": 18,
                        "医药生物": 15,
                        "大消费": 13,
                    }
                )
            ),
            (["新能源", "周期资源"], 18),
        )

    def test_board_logic_separates_mechanism_event_causality_and_validation(self):
        members = [
            {
                "stock_code": "600001",
                "stock_name": "高度样本",
                "event_drivers": ["机器人", "并购重组"],
                "secondary_concepts": ["机器人概念"],
                "source_nature": "机器人",
                "consecutive_limit_count": 3,
                "recent_limit_count": 3,
                "recent_limit_up_label": "3天3板",
                "first_limit_time": "09:25:00",
                "final_limit_time": "09:25:00",
                "open_count": 0,
                "amount": 500_000_000,
                "turnover_rate": 8.0,
            },
            {
                "stock_code": "600002",
                "stock_name": "容量样本",
                "event_drivers": ["机器人", "数据中心"],
                "secondary_concepts": ["机器人概念", "算力"],
                "source_nature": "机器人",
                "consecutive_limit_count": 2,
                "recent_limit_count": 2,
                "recent_limit_up_label": "2天2板",
                "first_limit_time": "09:35:00",
                "final_limit_time": "14:20:00",
                "open_count": 3,
                "amount": 1_800_000_000,
                "turnover_rate": 18.0,
            },
            {
                "stock_code": "600003",
                "stock_name": "跟随样本",
                "event_drivers": ["机器人"],
                "secondary_concepts": ["机器人概念"],
                "source_nature": "机器人",
                "consecutive_limit_count": 1,
                "recent_limit_count": 1,
                "recent_limit_up_label": "1天1板",
                "first_limit_time": "09:50:00",
                "final_limit_time": "09:50:00",
                "open_count": 0,
                "amount": 200_000_000,
                "turnover_rate": 5.0,
            },
        ]

        result = analyze_board("高端制造", members)

        self.assertIn("共同机制", result["logic_statement"])
        self.assertIn("时序共振", result["logic_statement"])
        self.assertIn("不证明前者导致后者涨停", result["logic_statement"])
        self.assertIn("不把题材共现等同于外生事件因果", result["logic_statement"])
        self.assertIn("盘面验证", result["validation_statement"])
        self.assertIn("结构约束", result["validation_statement"])
        self.assertEqual(result["shared_mechanisms"][0]["stock_count"], 3)
        self.assertEqual(result["common_event_evidence"], [])
        self.assertEqual(
            result["temporal_sequence"]["height_anchor"],
            "600001",
        )
        self.assertEqual(
            result["temporal_sequence"]["capacity_anchor"],
            "600002",
        )
        self.assertNotIn("transmission", result)
        self.assertTrue(result["constraints"])
        self.assertIn(
            result["structural_evidence_strength"],
            {"高", "中", "低"},
        )
        self.assertIsInstance(result["structural_evidence_score"], int)
        self.assertNotIn("confidence", result)
        self.assertNotIn("confidence_score", result)
        self.assertIn("只衡量共同机制覆盖", result["validation_statement"])
        self.assertIn("不代表事件因果已被证实", result["validation_statement"])
        self.assertIn("龙1", result["position_conclusion"])
        self.assertIn("高于龙2", result["position_conclusion"])
        self.assertIn("但", result["position_conclusion"])
        position_reasons = []
        for row in result["position_top"]:
            with self.subTest(position_rank=row["rank"]):
                self.assertTrue(row["rank_driver"])
                self.assertTrue(row["relative_comparison"])
                self.assertTrue(row["weakness"])
                self.assertTrue(row["invalidation"])
                self.assertIn("胜出依据：", row["reason"])
                self.assertIn("相对位置：", row["reason"])
                self.assertIn("主要短板：", row["reason"])
                self.assertIn("失效条件：", row["reason"])
                self.assertNotIn("仅表示时序共振", row["reason"])
                position_reasons.append(row["reason"])
        self.assertEqual(len(position_reasons), len(set(position_reasons)))

    def test_generic_repeated_event_labels_are_not_common_event_evidence(self):
        members = [
            {
                "stock_code": "600001",
                "event_drivers": ["半年报增长", "并购重组"],
            },
            {
                "stock_code": "600002",
                "event_drivers": ["半年报增长", "并购重组"],
            },
        ]

        self.assertEqual(shared_event_evidence(members), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
