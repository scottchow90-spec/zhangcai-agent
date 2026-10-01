#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import json
import os
import struct
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch


SKILLS = Path(r"D:\C盘转移\日志\codex\skills")
DAY_RECORD = struct.Struct("<IIIIIfII")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_day(path: Path, trade_date: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(DAY_RECORD.pack(trade_date, 1000, 1050, 950, 1020, 1_000_000.0, 100_000, 0))


class StockScoringIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baimao = load_module(
            "baimao_score_system_engine",
            SKILLS / "baimao-score-system" / "scripts" / "baimao_stock_score.py",
        )
        cls.baimao_teacher = load_module(
            "baimao_teacher_engine",
            SKILLS / "baimao-teacher-system" / "scripts" / "baimao_stock_score.py",
        )
        cls.five_dimension = load_module(
            "five_dimension_engine",
            SKILLS / "five-dimension-resonance" / "scripts" / "run_feilong_block_resonance.py",
        )
        cls.selection_15d = load_module(
            "selection_15d_engine",
            SKILLS / "a-share-15d-selection" / "scripts" / "run_a_share_15d.py",
        )
        cls.short_term_contract = json.loads(
            (SKILLS / "stock-unified" / "references" / "short_term_strong_stock_scoring_contract.json").read_text(encoding="utf-8")
        )
        cls.quality_track = load_module(
            "quality_track_engine",
            SKILLS / "quality-track-stock-selection" / "scripts" / "quality_track_live.py",
        )
        cls.baimao_daily = load_module(
            "baimao_daily_engine",
            SKILLS / "baimao-daily-intel-review" / "scripts" / "baimao-daily-intel-review.py",
        )

    def test_baimao_engines_anchor_freshness_to_market_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            vipdoc = Path(temp) / "vipdoc"
            write_day(vipdoc / "sh" / "lday" / "sh000001.day", 20260807)
            with patch.dict(os.environ, {"BAIMAO_EXPECTED_TRADE_DATE": ""}):
                for engine in (self.baimao, self.baimao_teacher):
                    with self.subTest(engine=engine.__name__):
                        with patch.object(engine, "VIPDOC", vipdoc):
                            self.assertEqual(engine.expected_trade_date(), "20260807")

    def test_baimao_missing_share_capital_does_not_create_turnover_points(self) -> None:
        closes = [10.0] * 100
        highs = [10.2] * 100
        lows = [9.8] * 100
        volumes = [100_000.0] * 100
        for engine in (self.baimao, self.baimao_teacher):
            with self.subTest(engine=engine.__name__):
                result = engine.white_rsi_score(closes, highs, lows, volumes, None)
                self.assertTrue(any("换手证据缺失" in fact for fact in result["facts"]))
                self.assertFalse(any("低位温和换手" in fact for fact in result["facts"]))

    def test_five_dimension_without_authoritative_v61_record_cannot_create_proxy_score(self) -> None:
        symbol = "000001.SZ"
        scan = {
            "items": [
                {
                    "formula": "大牛线4.0",
                    "ok": True,
                    "result": {symbol: {"EMA9": 3, "EMA10": 2, "EMA11": 1, "OUTPUT30": 1}},
                },
                {
                    "formula": "飞龙在天",
                    "ok": True,
                    "result": {symbol: {"波": 60, "段": 60, "OUTPUT6": 1}},
                },
                {
                    "formula": "游资资金监控",
                    "ok": True,
                    "result": {symbol: {"买方意向": 3}},
                },
                {
                    "formula": "机构资金监控",
                    "ok": True,
                    "result": {symbol: {"机构大单进": 3, "机构大单出": 0}},
                },
                {
                    "formula": "庄家资金监控",
                    "ok": True,
                    "result": {symbol: {"控盘程度": 60}},
                },
            ]
        }
        result = self.five_dimension.build_analysis(
            {"code": "000001", "symbol": symbol},
            {"name": "测试股份", "pct": 9.8, "open_count": 1, "streak": 1, "industry": "测试行业"},
            scan,
            5.0,
        )
        self.assertEqual(result["score_status"], "DATA_REQUIRED")
        self.assertEqual(result["dimension_scores"], [])
        self.assertEqual(result["risk_items"], [])
        self.assertEqual(result["final_score"], 0.0)
        self.assertFalse(result["decision_eligible"])
        self.assertEqual(result["score_confidence"], "DEGRADED")

    def test_v61_has_no_positive_fundamental_factor_and_missing_catalyst_scores_zero(self) -> None:
        rows = [
            {
                "date": f"2026{i // 28 + 1:02d}{i % 28 + 1:02d}",
                "open": 10.0,
                "high": 10.2,
                "low": 9.8,
                "close": 10.0,
                "amount": 600_000_000.0,
                "volume": 100_000.0,
            }
            for i in range(90)
        ]
        item = {
            "rows": rows,
            "formula_fields": {
                "大牛线4.0": {},
                "飞龙在天": {},
                "游资资金监控": {},
                "机构资金监控": {},
                "庄家资金监控": {},
            },
            "wave": 20.0,
            "segment": 20.0,
            "ignition": False,
            "risk_hits": [],
            "reduction_hits": [],
            "catalyst_hits": [],
            "lhb_hits": [],
            "concepts": [],
            "candidate_text_source_count": 0,
            "limit_price": 10.0,
            "pct": 10.0,
            "is_one_price": False,
            "recent_gain_3d_pct": 0.0,
            "recent_gain_5d_pct": 0.0,
            "recent_gain_10d_pct": 0.0,
        }
        result = self.selection_15d.score_candidate(item, Counter())
        dimensions = {row["name"]: row for row in result["positive_dimensions"]}
        forbidden = ("基本面", "财务", "估值", "ROE", "PE", "PB")
        self.assertEqual(len(dimensions), 26)
        self.assertFalse(any(any(token in name for token in forbidden) for name in dimensions))
        catalyst = dimensions["催化延续证据"]
        self.assertEqual(catalyst["stars"], 0.0)
        self.assertEqual(catalyst["score"], 0.0)
        self.assertIn("0分", catalyst["evidence"])
        self.assertEqual(result["score_contract"]["fundamental_positive_weight"], 0)

    def test_global_short_term_contract_is_single_26_factor_authority(self) -> None:
        contract = self.short_term_contract
        self.assertEqual(contract["version"], "A-SHARE-STRONG-26F-100-V6.1")
        self.assertEqual(contract["axes"], {"爆发力": 35, "持续性": 35, "市场协同": 20, "可交易性": 10})
        self.assertEqual(len(contract["factors"]), 26)
        self.assertEqual(sum(float(item["weight"]) for item in contract["factors"]), 100)
        self.assertEqual(contract["fundamental_policy"]["positive_weight"], 0)
        self.assertEqual(len(contract["hard_exclusions"]), 7)
        self.assertEqual(len(contract["risk_deductions"]), 15)
        self.assertEqual(
            [(name, weight) for name, weight in self.selection_15d.POSITIVE_DIMENSIONS],
            [(item["name"], item["weight"]) for item in contract["factors"]],
        )

    def test_quality_track_preliminary_score_is_bounded_to_100(self) -> None:
        code7 = "1000001"
        symbol = "000001.SH"
        selected_sectors = [{
            "codes": [code7],
            "quality_track_score": 100.0,
            "name": "高景气赛道",
            "source_name": "高景气赛道",
            "track_group": "测试",
        }]
        snapshots = {
            code7: {
                "close": 10.0,
                "average_amount_20d": 100_000_000_000.0,
                "is_limit_up": False,
                "return_5d": 0.10,
                "ma20": 9.0,
                "ma60": 8.0,
                "ma20_prev5": 8.0,
                "volume_ratio_5d": 1.5,
                "atr_pct": 0.05,
            }
        }
        news = [
            {
                "recid": f"N{i}",
                "mtime": "2026-08-09T09:00:00+08:00",
                "title": f"测试股份获得订单{i}",
                "excerpt": "测试股份中标并增长",
                "source_path": "fixture",
            }
            for i in range(4)
        ]
        rows = self.quality_track.preliminary_candidates(
            selected_sectors,
            snapshots,
            {symbol: "测试股份"},
            news,
        )
        self.assertEqual(len(rows), 1)
        self.assertGreater(rows[0]["preliminary_score_raw"], 100.0)
        self.assertEqual(rows[0]["preliminary_score"], 100.0)

    def test_baimao_daily_rejects_theme_scores_outside_0_to_100(self) -> None:
        blocks: list[str] = []
        evidence = {
            "sources": [{"id": "S1", "name": "测试源"}],
            "theme_clusters": [
                {
                    "name": "测试主题",
                    "score": 101,
                    "conclusion": "测试",
                    "evidence": "测试",
                    "logic": "测试",
                    "market_feedback": "测试",
                    "capital_feedback": "测试",
                    "watch_targets": ["测试股份"],
                    "next_observation": "测试",
                    "invalidation": "测试",
                    "source": "S1",
                },
                {
                    "name": "第二主题",
                    "score": 60,
                    "conclusion": "测试",
                    "evidence": "测试",
                    "logic": "测试",
                    "market_feedback": "测试",
                    "capital_feedback": "测试",
                    "watch_targets": ["测试股份"],
                    "next_observation": "测试",
                    "invalidation": "测试",
                    "source": "S1",
                },
            ],
        }
        self.baimao_daily.validate_enhanced_modules(blocks, evidence)
        self.assertTrue(any("score 必须在0到100之间" in item for item in blocks))


if __name__ == "__main__":
    unittest.main(verbosity=2)
