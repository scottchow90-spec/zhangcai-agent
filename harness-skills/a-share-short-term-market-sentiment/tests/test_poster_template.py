from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import copy
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from poster_template import render_poster
from poster_validator import validate_poster_bundle


class PosterTemplateTests(unittest.TestCase):
    def test_uses_live_comparisons_and_current_result_copy(self):
        result = {
            "trading_date": "2026-08-18",
            "single_stage_conclusion": {
                "stage": "亏钱效应出现",
                "confidence": "MEDIUM",
                "conclusion": "当前中级周期处于亏钱效应出现阶段。涨停由106家降至79家、封板率由89.8%降至77.5%、炸板由12家升至23家、跌停由1家升至5家；连板由15只升至18只。",
            },
            "short_term_stage_conclusion": {
                "stage": "分歧期",
                "confidence": "MEDIUM",
                "conclusion": "当前短线市场情绪处于分歧期。涨停由106家降至79家、封板率由89.8%降至77.5%、炸板由12家升至23家、跌停由1家升至5家；连板由15只升至18只。",
                "conflicts": [],
                "conflict_statement": "未发现足以改变短线情绪阶段判定的直接冲突。",
            },
            "risk_boundary": ["当日炸板23家、跌停5家"],
            "sources": {"tongdaxin": {"coverage": 5538}},
        }
        snapshot = {
            "trading_date": "2026-08-18",
            "market": {
                "index_change_pct": 0.192,
                "advancers": 2119,
                "decliners": 3292,
                "total_amount_billion": 24362.1,
                "amount_change_pct": 0.63,
                "limit_up": 79,
                "limit_down": 5,
                "consecutive": 18,
                "max_board": 4,
                "seal_rate": 77.5,
                "broken_board": 23,
                "topic_count_ge3": 8,
            },
            "topics": [
                {"name": "农业", "count": 23}, {"name": "芯片", "count": 8},
                {"name": "中报增长", "count": 7}, {"name": "机器人概念", "count": 7},
                {"name": "医药", "count": 5}, {"name": "操作系统", "count": 4},
                {"name": "通信", "count": 3}, {"name": "零售", "count": 3},
            ],
            "comparisons": {
                "previous_trading_day": {
                    "limit_up": 106,
                    "limit_down": 1,
                    "consecutive": 15,
                    "seal_rate": 89.8,
                    "broken_board": 12,
                }
            },
            "cross_validation": {"limit_up_difference": 0},
            "sources": {
                "duanxianxia": {"datasets": ["ztcount", "ztpool", "jinjidata", "amount"]},
                "lianban": {"reported_stage": "降温期"},
            },
        }
        with tempfile.TemporaryDirectory() as temp:
            bundle = render_poster(result, snapshot, Path(temp), visual_inspected=True)
        self.assertEqual(
            bundle["dynamic_binding"]["short_conclusion"],
            result["short_term_stage_conclusion"]["conclusion"],
        )
        visible_copy = "\n".join(item["text"] for item in bundle["text_runs"])
        for expected in (
            "涨停106→79｜封板89.8%→77.5%｜炸板12→23｜跌停1→5",
            "连板15→18｜上涨/下跌2119/3292｜成交额环比+0.63%",
            result["short_term_stage_conclusion"]["conclusion"],
            result["risk_boundary"][0],
            result["short_term_stage_conclusion"]["conflict_statement"],
        ):
            self.assertIn(expected, visible_copy)
        for stale in (
            "固定30项：",
            "研判框架",
            "各周期并列研判",
            "不生成加权总分",
            "核心延续，跟风转弱",
            "核心延续而跟风转弱",
            "跟风弱于核心",
            "呈现冰火并存",
            "\n前日 62\n",
            "\n前日 10\n",
            "\n前日 76.5%\n",
            "\n前日 19\n",
            "高潮不代表",
            "未定",
            "N/A",
            "未提供",
        ):
            self.assertNotIn(stale, visible_copy)

        missing_conclusion = copy.deepcopy(result)
        del missing_conclusion["short_term_stage_conclusion"]["conclusion"]
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "missing_dynamic_conclusion"):
                render_poster(missing_conclusion, snapshot, Path(temp), visual_inspected=True)

        stale_conclusion = copy.deepcopy(result)
        stale_conclusion["short_term_stage_conclusion"]["conclusion"] += "核心延续，跟风转弱。"
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "forbidden_template_conclusion"):
                render_poster(stale_conclusion, snapshot, Path(temp), visual_inspected=True)

        one_topic = copy.deepcopy(snapshot)
        one_topic["topics"] = [{"name": "农业", "count": 23}]
        with tempfile.TemporaryDirectory() as temp:
            one_topic_bundle = render_poster(result, one_topic, Path(temp), visual_inspected=True)
        one_topic_copy = "\n".join(item["text"] for item in one_topic_bundle["text_runs"])
        self.assertNotIn("通信\n20家", one_topic_copy)

        missing_metric = copy.deepcopy(snapshot)
        del missing_metric["market"]["amount_change_pct"]
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "missing_poster_market_metric:amount_change_pct"):
                render_poster(result, missing_metric, Path(temp), visual_inspected=True)

    def test_renders_8k_poster_and_readable_fit_preview(self):
        result = {
            "trading_date": "2026-08-17",
            "single_stage_conclusion": {
                "stage": "赚钱效应高潮",
                "confidence": "HIGH",
                "conclusion": "当前中级周期处于赚钱效应高潮阶段。涨停由62家升至106家、封板率由76.5%升至89.8%、炸板由19家降至12家、跌停由10家降至1家；连板由11只升至15只。",
            },
            "short_term_stage_conclusion": {
                "stage": "高潮期",
                "confidence": "HIGH",
                "conclusion": "当前短线市场情绪处于高潮期。涨停由62家升至106家、封板率由76.5%升至89.8%、炸板由19家降至12家、跌停由10家降至1家；连板由11只升至15只。",
                "conflict_statement": "未发现足以改变短线情绪阶段判定的直接冲突。",
            },
            "conflicts": [],
            "risk_boundary": ["当日炸板12家、跌停1家"],
            "sources": {"tongdaxin": {"coverage": 5538}},
        }
        snapshot = {
            "trading_date": "2026-08-17",
            "market": {
                "index_change_pct": 1.412,
                "advancers": 4335,
                "decliners": 1063,
                "total_amount_billion": 24203.5,
                "amount_change_pct": 11.41,
                "limit_up": 106,
                "limit_down": 1,
                "consecutive": 15,
                "max_board": 4,
                "seal_rate": 89.8,
                "broken_board": 12,
                "topic_count_ge3": 8,
            },
            "topics": [
                {"name": "通信", "count": 20}, {"name": "芯片", "count": 15},
                {"name": "农业", "count": 8}, {"name": "算力", "count": 7},
                {"name": "机器人", "count": 7}, {"name": "医药", "count": 6},
                {"name": "化工", "count": 4}, {"name": "食品饮料", "count": 4},
            ],
            "comparisons": {
                "previous_trading_day": {
                    "limit_up": 62,
                    "limit_down": 10,
                    "consecutive": 11,
                    "seal_rate": 76.5,
                    "broken_board": 19,
                }
            },
            "cross_validation": {"limit_up_difference": 0},
            "sources": {
                "duanxianxia": {"datasets": ["ztcount", "ztpool", "jinjidata", "amount"]},
                "lianban": {"reported_stage": "高潮期"},
            },
        }
        with tempfile.TemporaryDirectory() as temp:
            bundle = render_poster(result, snapshot, Path(temp), visual_inspected=True)
            validation = validate_poster_bundle(bundle)
            tampered = copy.deepcopy(bundle)
            for item in tampered["text_runs"]:
                if item["text"] == result["short_term_stage_conclusion"]["conclusion"]:
                    item["text"] = "固定模板结论"
                    break
            tampered_validation = validate_poster_bundle(tampered)
        self.assertEqual(validation["status"], "CLEAN_PASS", validation["errors"])
        self.assertIn("dynamic_conclusion_not_visible", tampered_validation["errors"])
        self.assertEqual(bundle["poster_dimensions"], [7680, 4320])
        self.assertEqual(bundle["preview_dimensions"], [1920, 1080])
        self.assertGreaterEqual(bundle["minimum_source_font_px"], 96)
        self.assertGreaterEqual(bundle["minimum_preview_font_px"], 24)
        self.assertGreaterEqual(bundle["minimum_core_body_preview_font_px"], 32)
        self.assertGreaterEqual(bundle["minimum_conclusion_preview_font_px"], 34)
        sections = {item["name"]: item["bbox"] for item in bundle["sections"]}
        for item in bundle["text_runs"]:
            self.assertIn(item["section"], sections)
            left, top, right, bottom = sections[item["section"]]
            x1, y1, x2, y2 = item["bbox"]
            self.assertGreaterEqual(x1, left + 48)
            self.assertGreaterEqual(y1, top + 48)
            self.assertLessEqual(x2, right - 48)
            self.assertLessEqual(y2, bottom - 48)
        visible_copy = "\n".join(item["text"] for item in bundle["text_runs"])
        for noise in ("以市场生态判阶段", "不压缩为情绪分数", "收盘数据"):
            self.assertNotIn(noise, visible_copy)


if __name__ == "__main__":
    unittest.main(verbosity=2)
