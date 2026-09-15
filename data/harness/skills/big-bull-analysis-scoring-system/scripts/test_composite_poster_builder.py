from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from poster_builder import render_composite_poster


LIGHT_GATE_PATH = Path(__file__).resolve().parents[3] / "scripts" / "poster_light_background_gate.py"
LIGHT_GATE_SPEC = importlib.util.spec_from_file_location("poster_light_background_gate", LIGHT_GATE_PATH)
LIGHT_GATE = importlib.util.module_from_spec(LIGHT_GATE_SPEC)
assert LIGHT_GATE_SPEC.loader is not None
LIGHT_GATE_SPEC.loader.exec_module(LIGHT_GATE)


class CompositePosterBuilderTests(unittest.TestCase):
    def test_renders_contract_bound_landscape_eight_k_poster(self) -> None:
        rows = []
        for index in range(24):
            score = 80.0 - index
            rows.append({
                "rank": index + 1,
                "market_rank": index + 9,
                "symbol": f"{600000 + index:06d}.SH",
                "name": "TCL智家" if index == 5 else f"样例{index + 1}",
                "score": score,
                "formula_scores": {
                    "大牛线撑压版": score + 1.0,
                    "飞龙在天": score,
                    "庄家资金监控": score - 2.0,
                },
                "top_level_items": {
                    "大牛线撑压版": score + 1.0,
                    "飞龙在天": score,
                    "庄家资金监控": score - 2.0,
                },
                "fusion": {
                    "base_score": score - 0.5,
                    "resonance_bonus": 2.0,
                    "disagreement_penalty": 1.5,
                    "top_level_weights": {
                        "大牛线撑压版": 40.0,
                        "飞龙在天": 35.0,
                        "庄家资金监控": 25.0,
                    },
                },
            })
        payload = {
            "status": "CLEAN_PASS",
            "scoring_mode": "RESEARCH_STRUCTURAL",
            "research_only": True,
            "prediction_authorized": False,
            "score_date": "20260814",
            "board": {"name": "飞龙在天", "constituent_count": 24},
            "data": {"universe_count": 313},
            "model": {
                "system_weights": {
                    "大牛线撑压版": 39.74,
                    "飞龙在天": 35.17,
                    "庄家资金监控": 25.09,
                },
                "metadata": {"predictive_validation": "NOT_ESTABLISHED"},
            },
            "ranking": rows,
            "delivery_validation": {"status": "PASS"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "poster.png"
            validation = render_composite_poster(payload, output)
            self.assertTrue(validation["passed"], validation)
            self.assertEqual(validation["poster_row_count"], 24)
            self.assertEqual(validation["expected_poster_row_count"], 24)
            self.assertEqual(validation["source_stock_count"], 24)
            self.assertEqual(validation["board_constituent_count"], 24)
            self.assertEqual(
                validation["visible_stock_labels"],
                [f"{row['name']} {row['symbol'][:6]}" for row in rows],
            )
            self.assertGreaterEqual(validation["minimum_font_px"], 96)
            self.assertGreaterEqual(validation["minimum_preview_font_px"], 24)
            self.assertGreaterEqual(validation["core_body_preview_font_px"], 32)
            self.assertGreaterEqual(validation["primary_preview_font_px"], 34)
            self.assertEqual(validation["preview_width"], 1920)
            self.assertEqual(validation["preview_height"], 1080)
            preview = output.with_name("poster-preview-1920x1080.png")
            self.assertEqual(Path(validation["preview_path"]), preview)
            self.assertTrue(preview.is_file())
            self.assertTrue(validation["board_name_visible"])
            self.assertTrue(validation["research_only_visible"])
            self.assertEqual(validation["fixed_item_count"], 30)
            self.assertEqual(validation["top_level_system_count"], 3)
            self.assertEqual(validation["visible_english"], [])
            self.assertEqual(validation["overlaps"], [])
            self.assertEqual(validation["clipped_text"], [])
            with Image.open(output) as image:
                self.assertEqual(image.size, (7680, 4320))
            with Image.open(preview) as image:
                self.assertEqual(image.size, (1920, 1080))
            light_gate = LIGHT_GATE.validate_poster_file(output)
            self.assertEqual(light_gate["status"], "PASS", light_gate)
            self.assertGreaterEqual(
                light_gate["metrics"]["minimum_corner_luminance"],
                230.0,
            )


if __name__ == "__main__":
    unittest.main()
