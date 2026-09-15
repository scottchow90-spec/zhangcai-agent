from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

import analysis_scoring
import poster_builder
import three_formula_composite_backtest as composite_backtest


ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = ROOT / "assets" / "three_formula_composite_weights.json"


def passing_model_fixture() -> dict:
    rows = composite_backtest.subsystem_catalog()
    systems = list(composite_backtest.FORMULAS)
    for row in rows:
        if (
            row["key"] not in poster_builder.MODEL_SCORE_STANDARDS
            and not row["forced_zero_reason"]
        ):
            row["forced_zero_reason"] = "测试夹具区分度不足"
    for system in systems:
        active = [
            row
            for row in rows
            if row["formula"] == system and not row["forced_zero_reason"]
        ]
        local_weight = 100.0 / len(active)
        for row in rows:
            if row["formula"] == system:
                row["local_weight"] = (
                    0.0 if row["forced_zero_reason"] else local_weight
                )
    return {
        "status": "CLEAN_PASS",
        "generated_at": "2026-08-17T12:00:00+08:00",
        "model": {
            "system_weights": {
                systems[0]: 34.0,
                systems[1]: 33.0,
                systems[2]: 33.0,
            },
            "subsystem_weights": rows,
        },
    }


class CompositeModelPosterBuilderTests(unittest.TestCase):
    def test_business_entry_renders_readable_structural_poster_when_current_model_is_rejected(self) -> None:
        self.assertTrue(
            hasattr(analysis_scoring, "run_composite_structure_poster"),
            "评分结构海报业务入口尚未实现",
        )
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            source = temporary_path / "historical-clean-model.json"
            source.write_text(
                json.dumps(passing_model_fixture(), ensure_ascii=False),
                encoding="utf-8",
            )
            output_dir = temporary_path / "deliverables"
            result = analysis_scoring.run_composite_structure_poster(
                output_dir,
                ["--weight-source", str(source)],
            )

            self.assertEqual(result["status"], "CLEAN_PASS", result)
            self.assertEqual(result["mode"], "综合评分结构海报")
            self.assertEqual(result["current_model_status"], "PREDICTIVE_REJECTED")
            poster = Path(result["artifacts"]["poster"]["path"])
            preview = Path(result["artifacts"]["preview"]["path"])
            self.assertTrue(poster.is_file())
            self.assertTrue(preview.is_file())
            validation = result["artifacts"]["poster"]["validation"]
            self.assertTrue(validation["passed"], validation)
            self.assertEqual(validation["factor_count"], 30)
            self.assertEqual(validation["system_count"], 3)
            self.assertGreaterEqual(validation["minimum_font_px"], 96)
            self.assertGreaterEqual(validation["minimum_preview_font_px"], 24)
            self.assertGreaterEqual(validation["core_body_preview_font_px"], 32)
            self.assertGreaterEqual(validation["primary_preview_font_px"], 34)
            self.assertEqual(validation["overlaps"], [])
            self.assertEqual(validation["clipped_text"], [])
            self.assertGreaterEqual(validation["mean_brightness"], 190)
            self.assertAlmostEqual(validation["system_weight_sum"], 100.0)
            self.assertEqual(set(validation["system_weights"]), set(composite_backtest.FORMULAS))
            with Image.open(poster) as image:
                self.assertEqual(image.size, (7680, 4320))
            with Image.open(preview) as image:
                self.assertEqual(image.size, (1920, 1080))

    def test_renders_all_thirty_items_as_landscape_eight_k_poster(self) -> None:
        self.assertTrue(
            hasattr(poster_builder, "render_composite_model_poster"),
            "模型说明海报构建器尚未实现",
        )
        payload = passing_model_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "model-poster.png"
            validation = poster_builder.render_composite_model_poster(payload, output)
            self.assertTrue(validation["passed"], validation)
            self.assertEqual(validation["factor_count"], 30)
            self.assertEqual(validation["system_count"], 3)
            self.assertEqual(validation["minimum_font_px"], 72)
            self.assertEqual(validation["overlaps"], [])
            self.assertEqual(validation["clipped_text"], [])
            self.assertEqual(validation["local_weight_sum_failures"], [])
            self.assertEqual(validation["system_weight_sum"], 100.0)
            self.assertIn(
                "visible_english",
                validation,
                "海报验收尚未检查可见英文",
            )
            self.assertIn(
                "code_like_expressions",
                validation,
                "海报验收尚未检查代码式表达",
            )
            self.assertEqual(validation["visible_english"], [])
            self.assertEqual(validation["code_like_expressions"], [])
            with Image.open(output) as image:
                self.assertEqual(image.size, (7680, 4320))

    def test_chinese_poster_gate_rejects_english_and_code_expressions(self) -> None:
        self.assertTrue(
            hasattr(poster_builder, "validate_chinese_poster_text"),
            "中文纯净度硬闸尚未实现",
        )
        clean = poster_builder.validate_chinese_poster_text(["全部使用中文自然语言"])
        self.assertEqual(clean["visible_english"], [])
        self.assertEqual(clean["code_like_expressions"], [])

        contaminated = poster_builder.validate_chinese_poster_text(
            ["含有ABC", "数值=1", "甲／乙", "三项＋四项", "左｜右"]
        )
        self.assertEqual(contaminated["visible_english"], ["ABC"])
        self.assertEqual(
            contaminated["code_like_expressions"],
            ["三项＋四项", "左｜右", "数值=1", "甲／乙"],
        )

    def test_business_entry_blocks_model_poster_for_rejected_formal_state(self) -> None:
        self.assertTrue(
            hasattr(analysis_scoring, "run_composite_model_poster"),
            "模型说明海报业务入口尚未实现",
        )
        with tempfile.TemporaryDirectory() as temporary:
            result = analysis_scoring.run_composite_model_poster(Path(temporary), [])
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["mode"], "三公式综合评分模型说明海报")
            self.assertEqual(result["artifacts"], {})
            self.assertEqual(result["model"]["status"], "PREDICTIVE_REJECTED")
            self.assertTrue(result["model"]["model_is_null"])
            self.assertEqual(len(result["model"]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
