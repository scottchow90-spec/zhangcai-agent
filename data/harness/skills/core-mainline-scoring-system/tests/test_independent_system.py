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
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL = Path(__file__).resolve().parents[1]
HOME = SKILL.parents[1]
ROUTER = HOME / "scripts" / "stock_canonical_runtime.py"
SCORER = SKILL / "scripts" / "mainline_scoring.py"
RUNNER = SKILL / "scripts" / "run_core_mainline_scoring.py"
ADAPTER = SKILL / "scripts" / "canonical_business_adapter.py"
OLD_SCORER = HOME / "skills" / "five-dimension-resonance" / "scripts" / "mainline_scoring.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def complete_board(**overrides):
    board = {
        "name": "通信",
        "rank": 1,
        "sector_return_pct": 3.6,
        "limit_up_count": 18,
        "market_limit_up_count": 90,
        "leader_count": 2,
        "mid_tier_count": 4,
        "first_board_count": 12,
        "capacity_count": 2,
        "three_board_count": 2,
        "two_board_count": 4,
        "one_board_count": 12,
        "constituent_count": 600,
        "capital_concentration_pct": 18.0,
        "turnover_expansion_ratio": 1.6,
        "catalyst_verified": True,
        "catalyst_level": "policy",
        "catalyst_source_count": 2,
        "continuity_days": 4,
        "divergence_repaired": True,
        "reflow_confirmed": True,
        "runner_up_gap_pct": 1.6,
        "source_session_coverage": 0.95,
        "intraday_sample_count": 18,
        "intraday_coverage_ratio": 1.0,
        "early_seal_ratio": 0.72,
        "zero_open_ratio": 0.78,
        "late_reseal_ratio": 0.06,
        "seal_fund_turnover_ratio": 0.12,
        "market_early_seal_ratio": 0.48,
        "market_zero_open_ratio": 0.55,
        "market_late_reseal_ratio": 0.18,
        "market_seal_fund_turnover_ratio": 0.08,
        "market_seal_rate": 0.82,
    }
    board.update(overrides)
    return board


class IndependentCoreMainlineSystemTests(unittest.TestCase):
    def test_lianban_history_skips_weekends_before_invoking_client(self) -> None:
        adapter = load_module("core_mainline_weekend_history", ADAPTER)
        fixed_now = adapter.datetime(2026, 8, 23, 12, 0, 0)
        called_dates: list[str] = []

        class FixedDateTime:
            @classmethod
            def now(cls):
                return fixed_now

        def fake_run(command, **kwargs):
            del kwargs
            target = command[command.index("--date") + 1]
            called_dates.append(target)
            output = Path(command[command.index("--output") + 1])
            output.write_text(
                json.dumps(
                    {"status": "CLEAN_PASS", "target_date": target},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as directory:
            with (
                mock.patch.object(adapter, "datetime", FixedDateTime),
                mock.patch.object(adapter.subprocess, "run", side_effect=fake_run),
            ):
                result = adapter.refresh_lianban_history(Path(directory))

        self.assertEqual(
            called_dates,
            ["2026-08-21", "2026-08-20", "2026-08-19"],
        )
        self.assertEqual(result["status"], "CLEAN_PASS")
        self.assertEqual(result["snapshot_count"], 3)
        self.assertTrue(all(item["returncode"] == 0 for item in result["attempts"]))

    def test_canonical_router_owns_core_mainline_names(self) -> None:
        for query in ("核心主线评分", "核心主线评分系统", "核心主线确定逻辑"):
            completed = subprocess.run(
                [sys.executable, str(ROUTER), "route", "--query", query],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["skill_ids"], ["core-mainline-scoring-system"])

    def test_nine_raw_weights_and_hard_gates_are_preserved(self) -> None:
        scoring = load_module("independent_core_mainline", SCORER)
        self.assertEqual(scoring.RAW_SCORE_VERSION, "CORE-MAINLINE-100-V2")
        self.assertEqual(scoring.MODEL_VERSION, "CORE-MAINLINE-CLOSE-V3")
        self.assertEqual(sum(scoring.COMPONENT_WEIGHTS.values()), 100)
        self.assertEqual(scoring.score_board(complete_board())["score"], 100.0)
        for field in ("three_board_count", "two_board_count", "one_board_count"):
            result = scoring.score_board(complete_board(**{field: 0}))
            self.assertEqual(result["status"], "GATE_FAILED")
            self.assertEqual(result["score"], 0.0)
        boundary = scoring.score_board(complete_board(constituent_count=100))
        self.assertEqual(boundary["status"], "GATE_FAILED")
        self.assertEqual(boundary["score"], 0.0)

    def test_high_raw_score_with_weak_close_quality_is_not_decision_eligible(self) -> None:
        scoring = load_module("core_mainline_close_rejection", SCORER)
        result = scoring.score_board(complete_board(
            early_seal_ratio=0.10,
            zero_open_ratio=0.10,
            late_reseal_ratio=0.80,
            seal_fund_turnover_ratio=0.01,
        ))

        self.assertEqual(result["raw_score"], 100.0)
        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["status"], "CLOSE_UNCONFIRMED")
        self.assertFalse(result["decision_eligible"])
        self.assertIn(
            "relative_close_quality_signals_below_2",
            result["close_confirmation"]["failures"],
        )

    def test_close_quality_is_compared_with_same_day_market_baseline(self) -> None:
        scoring = load_module("core_mainline_dynamic_close_baseline", SCORER)
        result = scoring.score_board(complete_board(
            early_seal_ratio=0.35,
            zero_open_ratio=0.45,
            late_reseal_ratio=0.30,
            seal_fund_turnover_ratio=0.05,
            market_early_seal_ratio=0.30,
            market_zero_open_ratio=0.40,
            market_late_reseal_ratio=0.35,
            market_seal_fund_turnover_ratio=0.06,
        ))

        self.assertEqual(result["status"], "VERIFIED")
        self.assertTrue(result["decision_eligible"])
        self.assertEqual(result["close_confirmation"]["quality_signal_count"], 3)

    def test_source_session_mismatch_blocks_close_confirmation(self) -> None:
        scoring = load_module("core_mainline_source_session_gate", SCORER)
        result = scoring.score_board(complete_board(source_session_coverage=0.50))

        self.assertEqual(result["status"], "CLOSE_UNCONFIRMED")
        self.assertIn(
            "source_session_coverage_below_80_pct",
            result["close_confirmation"]["failures"],
        )

    def test_duanxianxia_close_fields_keep_turnover_and_market_cap_separate(self) -> None:
        scoring = load_module("core_mainline_duanxianxia_close_fields", SCORER)
        row = [
            "600000", "样本股", 10.0, 120.0, 2, 145500,
            "通信催化", "2连板", 1000.0, 9000.0, "换手板", None, 93000,
        ]

        parsed = scoring.parse_duanxianxia_pool_row(row)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["turnover_amount"], 1000.0)
        self.assertEqual(parsed["free_float_market_cap"], 9000.0)
        metrics = scoring.close_quality_metrics([parsed], 1)
        self.assertEqual(metrics["intraday_sample_count"], 1)
        self.assertEqual(metrics["early_seal_ratio"], 1.0)
        self.assertEqual(metrics["zero_open_ratio"], 0.0)
        self.assertEqual(metrics["late_reseal_ratio"], 1.0)
        self.assertAlmostEqual(metrics["seal_fund_turnover_ratio"], 0.12)

    def test_runner_writes_auditable_board_ranking(self) -> None:
        scoring = load_module("independent_core_mainline_runner_fixture", SCORER)
        fixture = {
            "pre_scored_boards": [
                complete_board(name="通信", rank=2, sector_return_pct=2.4, limit_up_count=20,
                               three_board_count=1, two_board_count=2, one_board_count=17,
                               constituent_count=146, turnover_expansion_ratio=1.0,
                               runner_up_gap_pct=0.5),
                complete_board(name="芯片", rank=1, three_board_count=0, constituent_count=875),
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            fixture_path = directory_path / "fixture.json"
            output_path = directory_path / "result.json"
            fixture_path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(RUNNER), "--input-bundle", str(fixture_path), "--output", str(output_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "ONESTOCK_STOCK_CANONICAL_CHILD": "1"},
                check=True,
            )
            payload = json.loads(completed.stdout)
            saved = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload, saved)
        self.assertEqual(saved["schema"], "CORE_MAINLINE_SCORING_RESULT_V1")
        self.assertEqual(saved["model_version"], scoring.MODEL_VERSION)
        self.assertEqual(saved["execution_status"], "CLEAN_PASS")
        self.assertEqual(saved["summary"]["passed_count"], 1)
        self.assertEqual(saved["boards"][0]["name"], "通信")
        self.assertEqual(saved["boards"][0]["score"], 83.0)
        self.assertEqual(saved["boards"][0]["stars"], 4.0)
        self.assertEqual(saved["summary"]["close_confirmed_count"], 1)

    def test_runner_abstains_when_two_close_confirmed_boards_are_ambiguous(self) -> None:
        fixture = {
            "pre_scored_boards": [
                complete_board(name="通信", rank=1, runner_up_gap_pct=1.0),
                complete_board(name="芯片", rank=2, sector_return_pct=3.5,
                               runner_up_gap_pct=0.9),
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            fixture_path = directory_path / "fixture.json"
            output_path = directory_path / "result.json"
            fixture_path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            subprocess.run(
                [sys.executable, str(RUNNER), "--input-bundle", str(fixture_path), "--output", str(output_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "ONESTOCK_STOCK_CANONICAL_CHILD": "1"},
                check=True,
            )
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision_status"], "AMBIGUOUS_CLOSE")
        self.assertIsNone(saved["summary"]["core_mainline"])
        self.assertEqual(saved["summary"]["ambiguous_candidates"], ["通信", "芯片"])

    def test_five_dimension_uses_compatibility_shim(self) -> None:
        source = OLD_SCORER.read_text(encoding="utf-8")
        self.assertIn("core-mainline-scoring-system", source)
        self.assertNotIn("COMPONENT_WEIGHTS = {", source)
        old = load_module("five_dimension_core_mainline_compat", OLD_SCORER)
        new = load_module("independent_core_mainline_owner", SCORER)
        self.assertEqual(old.MODEL_VERSION, new.MODEL_VERSION)
        self.assertEqual(old.score_board(complete_board()), new.score_board(complete_board()))

    def test_clean_historical_stock_reason_supplements_authenticity_only(self) -> None:
        scoring = load_module("historical_stock_authenticity", SCORER)
        current = [{
            "code": "000019",
            "themes": [],
            "board_count": 3,
            "board_label": "3连板",
            "hierarchy_role": "leader",
            "announcement_theme_verified": False,
        }]
        history = [{
            "status": "CLEAN_PASS",
            "target_date": "2026-08-18",
            "sources": {"page": {"url": "https://lianban.net/days/2026-08-18.html"}},
            "page_details": {"stock_items": [{
                "code": "000019",
                "theme": "农业",
                "board": "农业",
                "reason": "农业；公司主营粮食仓储与农产品供应。",
                "board_count": 1,
                "board_label": "首板",
            }]},
        }]

        enriched = scoring.attach_historical_stock_authenticity(current, history)
        stock = enriched[0]
        self.assertEqual(stock["themes"], [])
        self.assertNotIn("reason", stock)
        self.assertEqual(stock["board_count"], 3)
        self.assertEqual(stock["board_label"], "3连板")
        self.assertEqual(stock["hierarchy_role"], "leader")
        self.assertFalse(stock["announcement_theme_verified"])
        self.assertEqual(scoring.stock_theme_candidates(stock), ["农业"])

        fit = scoring.score_stock_fit(stock, "农业")
        self.assertEqual(fit["status"], "VERIFIED")
        self.assertTrue(fit["decision_eligible"])
        self.assertEqual(fit["score"], 65.0)
        self.assertEqual(fit["historical_evidence"][0]["target_date"], "2026-08-18")
        self.assertEqual(
            fit["historical_evidence"][0]["source_url"],
            "https://lianban.net/days/2026-08-18.html",
        )
        self.assertIn("historical_reason_match=True", fit["evidence"])
        self.assertIn("announcement_verified=False", fit["evidence"])

    def test_degraded_or_unauditable_history_cannot_verify_authenticity(self) -> None:
        scoring = load_module("degraded_historical_stock_authenticity", SCORER)
        current = [{"code": "000019", "themes": []}]
        snapshots = [
            {
                "status": "DEGRADED",
                "target_date": "2026-08-18",
                "sources": {"page": {"url": "https://lianban.net/days/2026-08-18.html"}},
                "page_details": {"stock_items": [{
                    "code": "000019", "theme": "农业", "board": "农业", "reason": "农业；主营粮食。",
                }]},
            },
            {
                "status": "CLEAN_PASS",
                "target_date": "",
                "sources": {"page": {"url": "https://lianban.net/days/2026-08-18.html"}},
                "page_details": {"stock_items": [{
                    "code": "000019", "theme": "农业", "board": "农业", "reason": "农业；主营粮食。",
                }]},
            },
        ]

        enriched = scoring.attach_historical_stock_authenticity(current, snapshots)
        self.assertEqual(scoring.stock_theme_candidates(enriched[0]), [])
        fit = scoring.score_stock_fit(enriched[0], "农业")
        self.assertEqual(fit["status"], "DEGRADED")
        self.assertFalse(fit["decision_eligible"])

    def test_historical_theme_without_matching_reason_stays_degraded(self) -> None:
        scoring = load_module("theme_only_historical_stock_authenticity", SCORER)
        history = [{
            "status": "CLEAN_PASS",
            "target_date": "2026-08-18",
            "sources": {"page": {"url": "https://lianban.net/days/2026-08-18.html"}},
            "page_details": {"stock_items": [{
                "code": "000019", "theme": "农业", "board": "农业", "reason": "主营信息待核验",
            }]},
        }]

        stock = scoring.attach_historical_stock_authenticity([], history)[0]
        fit = scoring.score_stock_fit(stock, "农业")
        self.assertEqual(fit["status"], "DEGRADED")
        self.assertFalse(fit["decision_eligible"])
        self.assertIn("historical_reason_match=False", fit["evidence"])

    def test_stock_theme_selection_prefers_verified_authenticity_before_raw_board_score(self) -> None:
        scoring = load_module("historical_stock_theme_selection", SCORER)
        stock = scoring.attach_historical_stock_authenticity(
            [{"code": "000852", "themes": ["基础建设"], "hierarchy_role": "none"}],
            [{
                "status": "CLEAN_PASS",
                "target_date": "2026-08-18",
                "sources": {"page": {"url": "https://lianban.net/days/2026-08-18.html"}},
                "page_details": {"stock_items": [{
                    "code": "000852",
                    "theme": "石油石化",
                    "board": "其他",
                    "reason": "石油石化；公司主营油气装备。",
                }]},
            }],
        )[0]
        context = {
            "stocks": {"000852": stock},
            "boards": {
                "基础建设": {
                    **scoring.unavailable_mainline("board_evidence_missing"),
                    "name": "基础建设",
                    "raw_score": 90.0,
                },
                "石油石化": {
                    **scoring.unavailable_mainline("board_evidence_missing"),
                    "name": "石油石化",
                    "raw_score": 20.0,
                },
            },
        }

        result = scoring.score_stock_in_context("000852", context)
        self.assertEqual(result["stock_fit"]["theme"], "石油石化")
        self.assertEqual(result["stock_fit"]["status"], "VERIFIED")
        self.assertEqual(result["status"], "DEGRADED")
        self.assertFalse(result["decision_eligible"])

    def test_historical_board_reason_may_match_its_explicit_page_subtheme(self) -> None:
        scoring = load_module("historical_board_subtheme_reason", SCORER)
        history = [{
            "status": "CLEAN_PASS",
            "target_date": "2026-08-18",
            "sources": {"page": {"url": "https://lianban.net/days/2026-08-18.html"}},
            "page_details": {"stock_items": [{
                "code": "603280",
                "theme": "工程机械",
                "board": "基础建设",
                "reason": "工程机械；产品用于道路、桥梁和基础设施建设。",
            }]},
        }]

        stock = scoring.attach_historical_stock_authenticity([], history)[0]
        fit = scoring.score_stock_fit(stock, "基础建设")
        self.assertEqual(fit["status"], "VERIFIED")
        self.assertTrue(fit["decision_eligible"])
        self.assertIn("historical_reason_match=True", fit["evidence"])

    def test_tdx_industry_parent_uses_all_descendant_members_and_bound_index(self) -> None:
        scoring = load_module("tdx_industry_parent_catalog", SCORER)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            zs_path = root / "tdxzs.cfg"
            hy_path = root / "tdxhy.cfg"
            zs_path.write_text(
                "化工|880335|2|1|0|T0204\n化工原料|880336|2|1|1|T020401\n",
                encoding="gb18030",
            )
            hy_path.write_text(
                "0|000001|T020401|||X1\n0|000002|T020402|||X2\n1|600001|T020406|||X3\n",
                encoding="gb18030",
            )

            catalog = scoring.load_tdx_industry_catalog(zs_path, hy_path)

        parent = next(item for item in catalog if item["name"] == "化工")
        self.assertEqual(parent["index_code"], "880335")
        self.assertEqual(parent["member_count"], 3)
        self.assertEqual(parent["codes"], ["000001", "000002", "600001"])
        self.assertEqual(parent["match_basis"], "tdxhy_descendant_prefix")

    def test_tdx_sector_return_reads_real_day_record_and_rejects_stale_date(self) -> None:
        scoring = load_module("tdx_sector_day_return", SCORER)
        with tempfile.TemporaryDirectory() as directory:
            vipdoc = Path(directory)
            day_dir = vipdoc / "sh" / "lday"
            day_dir.mkdir(parents=True)
            path = day_dir / "sh880335.day"
            path.write_bytes(
                scoring.TDX_DAY_RECORD.pack(20260821, 10000, 10100, 9900, 10000, 1.0, 10, 0)
                + scoring.TDX_DAY_RECORD.pack(20260824, 9900, 9950, 9700, 9800, 2.0, 20, 0)
            )

            result = scoring.read_tdx_sector_return("880335", "2026-08-24", vipdoc)
            stale = scoring.read_tdx_sector_return("880335", "2026-08-25", vipdoc)
            expected_hash = __import__("hashlib").sha256(path.read_bytes()).hexdigest()

        self.assertAlmostEqual(result["return_pct"], -2.0)
        self.assertEqual(result["previous_date"], 20260821)
        self.assertEqual(result["current_date"], 20260824)
        self.assertEqual(result["source_sha256"], expected_hash)
        self.assertIsNone(stale)

    def test_tdx_turnover_expansion_rejects_stale_latest_record(self) -> None:
        scoring = load_module("tdx_turnover_date_gate", SCORER)
        with tempfile.TemporaryDirectory() as directory:
            vipdoc = Path(directory)
            day_dir = vipdoc / "sz" / "lday"
            day_dir.mkdir(parents=True)
            (day_dir / "sz000001.day").write_bytes(
                scoring.TDX_DAY_RECORD.pack(20260831, 1000, 1010, 990, 1000, 100.0, 10, 0)
                + scoring.TDX_DAY_RECORD.pack(20260901, 1010, 1030, 1000, 1020, 150.0, 20, 0)
            )
            with mock.patch.object(scoring, "TDX_VIPDOC", vipdoc):
                current = scoring._tdx_day_amounts("000001", "2026-09-01")
                stale = scoring._tdx_day_amounts("000001", "2026-09-02")

        self.assertEqual(current["previous_day_amount"], 100.0)
        self.assertEqual(current["current_day_amount"], 150.0)
        self.assertEqual(current["previous_day_date"], 20260831)
        self.assertEqual(current["current_day_date"], 20260901)
        self.assertTrue(current["turnover_source_sha256"])
        self.assertIsNone(stale)

    def test_adapter_emits_clean_current_data_gate_for_confirmed_mainline(self) -> None:
        adapter = load_module("core_mainline_data_gate", ADAPTER)
        target_date = "2026-09-01"
        scoring_result = {
            "execution_status": "CLEAN_PASS",
            "target_date": target_date,
            "decision_status": "CONFIRMED_MAINLINE",
            "summary": {
                "board_count": 1,
                "passed_count": 1,
                "degraded_count": 250,
                "core_mainline": "AI应用",
            },
            "source_status": {
                "duanxianxia_plate": "VERIFIED",
                "duanxianxia_pool": "VERIFIED",
                "duanxianxia_membership": "VERIFIED",
                "lianban": "CLEAN_PASS",
                "tdx_constituents": "VERIFIED",
                "current_session_alignment": "VERIFIED",
                "lianban_history": "VERIFIED",
                "tdx_turnover": "VERIFIED",
            },
            "session_alignment": {"coverage": 0.90},
            "issues": [],
            "boards": [{
                "name": "AI应用",
                "normalized_name": "人工智能应用",
                "decision_eligible": True,
                "missing_evidence": [],
                "gate_failures": [],
                "input_evidence": {
                    "constituent_count": 1070,
                    "constituent_evidence": {
                        "source_path": r"C:\new_tdx_mock\T0002\hq_cache\infoharbor_block.dat",
                        "source_sha256": "a" * 64,
                        "match_type": "related_name_with_member_overlap",
                    },
                    "sector_return_evidence": {
                        "current_date": 20260901,
                        "source_path": r"C:\new_tdx_mock\vipdoc\sh\lday\sh880948.day",
                        "source_sha256": "b" * 64,
                    },
                    "turnover_evidence": [{
                        "current_date": 20260901,
                        "source_path": r"C:\new_tdx_mock\vipdoc\sh\lday\sh600000.day",
                        "source_sha256": "c" * 64,
                    }],
                    "catalyst_verified": True,
                    "catalyst_source_count": 2,
                    "catalyst_evidence": {
                        "verified": True,
                        "source_count": 2,
                        "matched_codes": ["600000"],
                    },
                },
            }],
        }
        with mock.patch.dict(os.environ, {
            "CODEX_STOCK_SHARED_EVIDENCE_STATUS": "CLEAN_PASS",
            "CODEX_STOCK_EVIDENCE_SET_ID": "evidence-set-1",
            "CODEX_STOCK_EVIDENCE_TRADING_DATE": target_date,
        }, clear=False):
            gate = adapter.build_data_gate(
                scoring_result,
                Path(r"F:\Codex\cache\core-mainline-test\core-mainline-result.json"),
                {"status": "CLEAN_PASS"},
                {"status": "CLEAN_PASS", "snapshot_count": 3},
            )

        self.assertEqual(gate["schema"], "STOCK_DATA_GATE_V1")
        self.assertEqual(gate["errors"], [])
        self.assertEqual(gate["status"], "CLEAN_PASS")
        self.assertEqual(gate["skill_id"], "core-mainline-scoring-system")
        self.assertEqual(gate["effective_trading_date"], target_date)
        self.assertEqual(gate["latest_required_trading_date"], target_date)
        self.assertTrue(all(
            item["status"] == "CLEAN_PASS"
            for item in gate["dimensions"].values()
        ))

    def test_local_tdx_interim_growth_catalog_compares_current_dbf_with_prior_h1(self) -> None:
        scoring = load_module("tdx_interim_growth_catalog", SCORER)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dbf_path = root / "base.dbf"
            prior_path = root / "gpcw20250630.dat"
            fields = [("GPDM", "C", 6, 0), ("GXRQ", "N", 8, 0), ("JLY", "N", 14, 1)]
            records = [
                ("002192", "20260818", "1000.0"),
                ("000001", "20260820", "100.0"),
                ("000002", "20260630", "900.0"),
            ]
            header_len = 32 + len(fields) * 32 + 1
            record_len = 1 + sum(item[2] for item in fields)
            header = bytearray(32)
            header[0] = 3
            struct.pack_into("<I", header, 4, len(records))
            struct.pack_into("<H", header, 8, header_len)
            struct.pack_into("<H", header, 10, record_len)
            descriptors = bytearray()
            for name, field_type, length, decimal in fields:
                descriptor = bytearray(32)
                descriptor[: len(name)] = name.encode("ascii")
                descriptor[11] = ord(field_type)
                descriptor[16] = length
                descriptor[17] = decimal
                descriptors.extend(descriptor)
            body = bytearray()
            for record in records:
                body.extend(b" ")
                for value, (_name, field_type, length, _decimal) in zip(record, fields):
                    encoded = value.encode("ascii")
                    body.extend(encoded.ljust(length) if field_type == "C" else encoded.rjust(length))
            dbf_path.write_bytes(bytes(header) + bytes(descriptors) + b"\r" + bytes(body) + b"\x1a")

            field_count = 96
            report_size = field_count * 4
            item_size = struct.calcsize("<6scI")
            data_offset = struct.calcsize("<hIHIII") + len(records) * item_size
            prior_header = struct.pack("<hIHIII", 1, 20250630, len(records), 0, report_size, 0)
            items = bytearray()
            values = bytearray()
            for index, (code, prior_profit) in enumerate(
                [("002192", 500000.0), ("000001", 200000.0), ("000002", 100000.0)]
            ):
                items.extend(struct.pack("<6scI", code.encode("ascii"), b"0", data_offset + index * report_size))
                row = [0.0] * field_count
                row[95] = prior_profit
                values.extend(struct.pack(f"<{field_count}f", *row))
            prior_path.write_bytes(prior_header + bytes(items) + bytes(values))

            result = scoring.load_tdx_interim_growth_catalog(
                "2026-08-24",
                dbf_path,
                prior_path,
            )

        self.assertEqual(result["name"], "中报增长")
        self.assertEqual(result["codes"], ["002192"])
        self.assertEqual(result["member_count"], 1)
        self.assertEqual(result["match_basis"], "tdx_current_parent_profit_vs_prior_h1")
        self.assertIn("base_dbf_sha256", result)
        self.assertIn("prior_gpcw_sha256", result)

    def test_catalyst_cross_validation_uses_same_stock_reasons_outside_hot_topic_list(self) -> None:
        scoring = load_module("per_stock_catalyst_cross_validation", SCORER)
        result = scoring.cross_validate_theme_catalyst(
            "化工",
            [{"code": "600610", "ztyy": "化工；季戊四醇"}],
            [{"code": "600610", "reason": "化工；半年报披露主营精细化工"}],
        )

        self.assertTrue(result["verified"])
        self.assertEqual(result["source_count"], 2)
        self.assertEqual(result["matched_codes"], ["600610"])

    def test_return_lead_gap_is_sorted_by_real_return_not_strength_value(self) -> None:
        scoring = load_module("real_return_lead_gap", SCORER)
        gaps = scoring.compute_return_lead_gaps({
            "强度第一但涨幅较低": 1.0,
            "真实涨幅第一": 5.0,
            "真实涨幅第二": 3.0,
        })

        self.assertEqual(gaps["真实涨幅第一"], 2.0)
        self.assertEqual(gaps["真实涨幅第二"], -2.0)
        self.assertEqual(gaps["强度第一但涨幅较低"], -4.0)

    def test_build_context_wires_runtime_tdx_return_and_catalyst_evidence(self) -> None:
        scoring = load_module("runtime_tdx_context_evidence", SCORER)
        duanxianxia = {
            "datasets": {
                "platechart1": {
                    "success": True,
                    "data": {"plates": {
                        "1": {"name": "AI应用", "val": 99, "ztcount": 1},
                        "2": {"name": "化工", "val": 10, "ztcount": 1},
                    }},
                },
                "ztpool": {
                    "success": True,
                    "data": {
                        "list": [
                            ["003040", "楚天龙", None, None, None, None, "AI应用", "首板", None, 20.0],
                            ["600610", "中毅达", None, None, None, None, "化工", "首板", None, 10.0],
                        ],
                        "count": {"limit_up_count": {"today": {"num": 20}}},
                    },
                },
                "ztplate": {
                    "success": True,
                    "data": {"list": [
                        {"code": "003040", "plate": "AI应用"},
                        {"code": "600610", "plate": "化工"},
                    ]},
                },
                "ztlive": {
                    "success": True,
                    "data": {"list": [
                        {"code": "003040", "name": "楚天龙", "ztyy": "AI应用；数字身份", "zt": "首板"},
                        {"code": "600610", "name": "中毅达", "ztyy": "化工；季戊四醇", "zt": "首板"},
                    ]},
                },
            },
        }
        lianban = {
            "status": "CLEAN_PASS",
            "target_date": "2026-08-24",
            "topics": [],
            "page_details": {"stock_items": [
                {"code": "003040", "theme": "AI应用", "reason": "AI应用；数字身份服务", "board_count": 1},
                {"code": "600610", "theme": "化工", "reason": "化工；主营精细化工", "board_count": 1},
            ]},
        }
        catalog = [
            {
                "name": "人工智能",
                "source_name": "GN_人工智能",
                "codes": ["003040"] * 101,
                "member_count": 101,
                "index_code": "880948",
                "source_path": "tdxzs.cfg|tdxhy.cfg",
                "source_sha256": {"tdxzs": "zs-ai", "tdxhy": "hy-ai"},
                "match_basis": "tdxhy_descendant_prefix",
            },
            {
                "name": "化工",
                "source_name": "TDXHY_T0204_化工",
                "codes": ["600610"] * 455,
                "member_count": 455,
                "index_code": "880335",
                "source_path": "tdxzs.cfg|tdxhy.cfg",
                "source_sha256": {"tdxzs": "zs-chemical", "tdxhy": "hy-chemical"},
                "match_basis": "tdxhy_descendant_prefix",
            },
        ]
        sector_evidence = {
            "880948": {
                "index_code": "880948", "return_pct": -1.52969723,
                "previous_date": 20260821, "current_date": 20260824,
                "previous_close": 100.0, "current_close": 98.47030277,
                "source_path": "sh880948.day", "source_sha256": "day-ai",
            },
            "880335": {
                "index_code": "880335", "return_pct": -1.35338486,
                "previous_date": 20260821, "current_date": 20260824,
                "previous_close": 100.0, "current_close": 98.64661514,
                "source_path": "sh880335.day", "source_sha256": "day-chemical",
            },
        }

        with (
            mock.patch.object(scoring, "load_runtime_tdx_constituent_catalog", return_value=catalog) as load_runtime,
            mock.patch.object(scoring, "load_tdx_constituent_catalog", return_value=catalog),
            mock.patch.object(scoring, "read_tdx_sector_return", side_effect=lambda code, date: sector_evidence[code]),
        ):
            context = scoring.build_context(duanxianxia, lianban)

        load_runtime.assert_called_once_with("2026-08-24")
        chemical = context["boards"]["化工"]["input_evidence"]
        self.assertAlmostEqual(chemical["sector_return_pct"], -1.35338486)
        self.assertAlmostEqual(chemical["runner_up_gap_pct"], 0.17631237)
        self.assertTrue(chemical["catalyst_verified"])
        self.assertEqual(chemical["catalyst_evidence"]["matched_codes"], ["600610"])
        self.assertEqual(chemical["constituent_evidence"]["source_sha256"]["tdxhy"], "hy-chemical")
        self.assertEqual(chemical["sector_return_evidence"]["current_date"], 20260824)
        self.assertEqual(chemical["sector_return_evidence"]["source_sha256"], "day-chemical")


if __name__ == "__main__":
    unittest.main(verbosity=2)
