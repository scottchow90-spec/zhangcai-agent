from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
FORMATTER_PATH = ROOT / "scripts" / "unified_five_theory_conclusion.py"
ENTRY_PATH = ROOT / "scripts" / "legacy_codex_entry.py"
FORMATTER = None
ENTRY = None
if FORMATTER_PATH.is_file():
    SPEC = importlib.util.spec_from_file_location("unified_five_theory_conclusion", FORMATTER_PATH)
    FORMATTER = importlib.util.module_from_spec(SPEC)
    assert SPEC.loader is not None
    SPEC.loader.exec_module(FORMATTER)
    ENTRY_SPEC = importlib.util.spec_from_file_location("support_pressure_legacy_codex_entry", ENTRY_PATH)
    ENTRY = importlib.util.module_from_spec(ENTRY_SPEC)
    assert ENTRY_SPEC.loader is not None
    ENTRY_SPEC.loader.exec_module(ENTRY)


def sample_report() -> dict:
    return {
        "status": "PASS",
        "symbol": "TEST",
        "technical_context": {
            "close": 100.0,
            "ema20": 98.0,
            "macd_histogram": 2.0,
            "volume_ratio_20": 0.9,
            "regime": "range_or_transition",
        },
        "theory_subsystems": {
            "elliott_wave": {
                "status": "PASS",
                "active_in_main_chain": True,
                "structure_state": "no_complete_impulse",
                "direction": "down",
                "wave_points": [],
                "rule_validation": {},
                "candidate_levels": [],
                "limitations": ["test boundary"],
            },
            "chan_structure": {
                "status": "PASS",
                "active_in_main_chain": True,
                "central_zones": [{"lower": 90.0, "upper": 98.0, "start_index": 10, "end_index": 20}],
                "strokes": [{"direction": "up", "start_level": 92.0, "end_level": 99.0}],
                "buy_sell_state": "buy_watch",
                "candidate_levels": [],
                "limitations": ["test boundary"],
            },
            "fibonacci": {
                "status": "PASS",
                "active_in_main_chain": True,
                "active_swing": {"start_level": 90.0, "end_level": 100.0, "direction": "up"},
                "confluence_clusters": [
                    {"center": 95.0, "count": 2},
                    {"center": 105.0, "count": 3},
                    {"center": 110.0, "count": 1},
                ],
                "candidate_levels": [],
                "limitations": ["test boundary"],
            },
            "gann": {
                "status": "PASS",
                "active_in_main_chain": True,
                "anchor": {"index": 20, "level": 90.0, "direction": "up"},
                "time_cycles": [
                    {"length": 20, "elapsed": 20, "bars_to_next": 0, "near_turn_window": True},
                    {"length": 30, "elapsed": 20, "bars_to_next": 10, "near_turn_window": False},
                ],
                "trend_slope_atr_per_bar": 0.08,
                "candidate_levels": [],
                "limitations": ["test boundary"],
            },
            "wyckoff": {
                "status": "PASS",
                "active_in_main_chain": True,
                "phase": "accumulation_or_markup",
                "trading_range": {"lower": 80.0, "upper": 110.0, "midpoint": 95.0},
                "events": [{"type": "spring", "accepted": True, "date": "2026-08-01", "event_level": 82.0}],
                "conditions": {"range_defined": True, "volume_contracting": True},
                "candidate_levels": [],
                "limitations": ["test boundary"],
            },
        },
        "conclusion": {
            "state": "UNVALIDATED_CANDIDATE_ZONES_ONLY",
            "location_state": "NEAR_SUPPORT_TEST",
            "directional_prediction": "NOT_CLAIMED",
            "confidence_cap": "D",
            "primary_support_zone": {"lower": 96.0, "center": 97.0, "upper": 98.0},
            "primary_resistance_zone": {"lower": 102.0, "center": 103.0, "upper": 104.0},
            "breakout_trigger": {"price": 105.0},
            "breakdown_trigger": {"price": 95.0},
            "support_scenario_invalidation": {"price": 94.0},
        },
        "walk_forward_validation": {
            "status": "GLOBAL_NO_EMPIRICAL_LIFT",
            "validation_grade": "D",
            "global_cross_sectional_gate": {"predictive_claim_allowed": False},
        },
    }


class UnifiedFiveTheoryDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(FORMATTER, "unified five-theory conclusion formatter is missing")
        self.assertIsNotNone(ENTRY, "formal entry did not load the unified delivery layer")

    def test_builds_required_five_theory_sections_and_explicit_conclusion(self) -> None:
        result = FORMATTER.build_unified_conclusion(sample_report())
        self.assertEqual(result["schema"], "UNIFIED_FIVE_THEORY_CONCLUSION_V1")
        self.assertTrue(result["all_subsystems_used"])
        self.assertEqual(
            result["delivery_sections"],
            ["波浪理论", "缠论", "斐波那契", "江恩理论", "威科夫", "综合结论"],
        )
        self.assertEqual(result["elliott_wave"]["confirmed_wave_position"], "UNRESOLVED_NO_COMPLETE_IMPULSE")
        self.assertIsNone(result["elliott_wave"]["wave_number"])
        self.assertEqual(result["elliott_wave"]["trend"], "DOWN_STRUCTURE")
        self.assertEqual(result["chan_structure"]["trend"], "UP_STROKE_ABOVE_CENTRAL_ZONE")
        self.assertEqual(result["fibonacci"]["nearest_support_positions"], [95.0])
        self.assertEqual(result["fibonacci"]["nearest_resistance_positions"], [105.0, 110.0])
        self.assertEqual(result["gann"]["time_window_state"], "NEAR_TIME_WINDOW")
        self.assertEqual(result["gann"]["near_cycle_lengths"], [20])
        self.assertEqual(result["wyckoff"]["range_position"], "ABOVE_RANGE_MIDPOINT")
        self.assertEqual(result["integrated_conclusion"]["structural_bias"], "STRUCTURAL_RECOVERY_NOT_TREND_CONFIRMED")
        for heading in ("1. 波浪理论：", "2. 缠论：", "3. 斐波那契：", "4. 江恩理论：", "5. 威科夫：", "6. 综合结论："):
            self.assertIn(heading, result["formatted_conclusion_cn"])

    def test_missing_or_inactive_subsystem_fails_closed(self) -> None:
        report = sample_report()
        report["theory_subsystems"].pop("gann")
        with self.assertRaises(FORMATTER.UnifiedConclusionError):
            FORMATTER.build_unified_conclusion(report)

    def test_truncated_tdx_history_fails_unified_delivery(self) -> None:
        report = sample_report()
        report["data_provenance"] = {
            "source_type": "tdx_local_hub",
            "history_scope": "TRUNCATED_TAIL",
            "full_history_required": True,
            "full_history_verified": False,
            "records_returned": 500,
            "source_records_available": 1222,
        }
        with self.assertRaisesRegex(FORMATTER.UnifiedConclusionError, "tdx_full_history_not_verified"):
            FORMATTER.build_unified_conclusion(report)

    def test_elliott_must_bind_the_same_full_history_count(self) -> None:
        report = sample_report()
        report["data_provenance"] = {
            "source_type": "tdx_local_hub",
            "history_scope": "FULL_LOCAL_TDX_FILE",
            "full_history_required": True,
            "full_history_verified": True,
            "records_returned": 1222,
            "source_records_available": 1222,
        }
        report["theory_subsystems"]["elliott_wave"].update(
            {
                "input_bar_count": 500,
                "search_scope": "RECENT_CONFIRMED_PIVOTS_ONLY",
            }
        )
        with self.assertRaisesRegex(FORMATTER.UnifiedConclusionError, "elliott_full_history_not_verified"):
            FORMATTER.build_unified_conclusion(report)

        report = sample_report()
        report["theory_subsystems"]["gann"]["active_in_main_chain"] = False
        with self.assertRaises(FORMATTER.UnifiedConclusionError):
            FORMATTER.build_unified_conclusion(report)

    def test_complete_impulse_reports_confirmed_fifth_wave_without_guessing_next_wave(self) -> None:
        report = sample_report()
        report["theory_subsystems"]["elliott_wave"].update(
            {
                "structure_state": "complete_impulse",
                "direction": "up",
                "wave_points": [{"confirmed": True} for _ in range(6)],
                "rule_validation": {
                    "wave2_not_beyond_origin": True,
                    "wave3_exceeds_wave1": True,
                    "wave3_not_shortest": True,
                    "wave4_no_wave1_overlap": True,
                    "wave5_exceeds_wave3": True,
                },
            }
        )
        result = FORMATTER.build_unified_conclusion(report)
        self.assertEqual(result["elliott_wave"]["wave_number"], 5)
        self.assertEqual(result["elliott_wave"]["confirmed_wave_position"], "CONFIRMED_IMPULSE_WAVE_5_COMPLETE")
        self.assertEqual(result["elliott_wave"]["developing_wave_position"], "UNRESOLVED_REQUIRES_RIGHT_CONFIRMATION")

    def test_malformed_wave_points_cannot_pass_complete_impulse_confirmation(self) -> None:
        report = sample_report()
        report["theory_subsystems"]["elliott_wave"].update(
            {
                "structure_state": "complete_impulse",
                "direction": "up",
                "wave_points": ["not-a-confirmed-pivot"] * 6,
                "rule_validation": {f"rule_{index}": True for index in range(5)},
            }
        )
        result = FORMATTER.build_unified_conclusion(report)
        self.assertIsNone(result["elliott_wave"]["wave_number"])
        self.assertEqual(result["elliott_wave"]["confirmed_wave_position"], "UNRESOLVED_NO_COMPLETE_IMPULSE")

    def test_no_gann_window_is_explicit_and_not_a_turning_point_claim(self) -> None:
        report = sample_report()
        report["theory_subsystems"]["gann"]["time_cycles"] = [
            {"length": 20, "elapsed": 13, "bars_to_next": 7, "near_turn_window": False},
            {"length": 30, "elapsed": 13, "bars_to_next": 17, "near_turn_window": False},
        ]
        result = FORMATTER.build_unified_conclusion(report)
        self.assertEqual(result["gann"]["time_window_state"], "NO_NEAR_TIME_WINDOW")
        self.assertEqual(result["gann"]["near_cycle_lengths"], [])
        self.assertEqual(result["gann"]["next_window_bars"], 7)
        self.assertFalse(result["gann"]["turning_point_claimed"])

    def test_enrichment_updates_report_and_summary_hash(self) -> None:
        with tempfile.TemporaryDirectory(prefix="unified-five-theory-") as raw_temp:
            root = Path(raw_temp)
            report_path = root / "TEST.scientific_support_pressure.json"
            report_path.write_text(json.dumps(sample_report(), ensure_ascii=False), encoding="utf-8")
            summary = {
                "status": "PASS",
                "items": [{
                    "symbol": "TEST",
                    "status": "PASS",
                    "artifact": {"path": str(report_path), "size": 0, "sha256": "stale", "readback_status": "PASS"},
                }],
            }
            enriched = FORMATTER.enrich_analysis_summary(summary)
            readback = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(readback["unified_five_theory_conclusion"]["status"], "PASS")
            artifact = enriched["items"][0]["artifact"]
            self.assertEqual(artifact["size"], report_path.stat().st_size)
            self.assertEqual(artifact["sha256"], hashlib.sha256(report_path.read_bytes()).hexdigest())
            self.assertEqual(enriched["items"][0]["unified_five_theory_conclusion_status"], "PASS")
            self.assertEqual(enriched["unified_delivery_schema"], "UNIFIED_FIVE_THEORY_CONCLUSION_V1")

    def test_atomic_json_temporary_name_stays_short_for_long_windows_paths(self) -> None:
        target = Path("000001_SH.scientific_support_pressure.json")
        temporary = FORMATTER._temporary_json_path(target)
        self.assertLessEqual(len(temporary.name), 18)
        self.assertEqual(temporary.parent, target.parent)
        self.assertNotEqual(temporary, target)

    def test_formal_entry_persists_and_prints_only_the_enriched_final_summary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="unified-five-theory-entry-") as raw_temp:
            root = Path(raw_temp)
            report_path = root / "TEST.scientific_support_pressure.json"
            report_path.write_text(json.dumps(sample_report(), ensure_ascii=False), encoding="utf-8")
            summary_path = root / "run_summary.json"
            disk_summary = {
                "status": "PASS",
                "items": [{
                    "symbol": "TEST",
                    "status": "PASS",
                    "artifact": {"path": str(report_path), "size": 0, "sha256": "stale", "readback_status": "PASS"},
                }],
            }
            summary_path.write_text(json.dumps(disk_summary, ensure_ascii=False), encoding="utf-8")
            engine_stdout = dict(disk_summary)
            engine_stdout["summary_artifact"] = {
                "path": str(summary_path),
                "size": summary_path.stat().st_size,
                "sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
                "readback_status": "PASS",
            }
            completed = mock.Mock(returncode=0, stdout=json.dumps(engine_stdout, ensure_ascii=False), stderr="")
            out = io.StringIO()
            err = io.StringIO()
            with mock.patch.object(ENTRY.subprocess, "run", return_value=completed) as mocked_run:
                with redirect_stdout(out), redirect_stderr(err):
                    code = ENTRY.run_primary(["--mode", "pressure", "--symbols", "TEST"])
            self.assertEqual(code, 0)
            self.assertEqual(err.getvalue(), "")
            final_summary = json.loads(out.getvalue())
            self.assertEqual(final_summary["unified_delivery_status"], "PASS")
            self.assertEqual(final_summary["items"][0]["unified_five_theory_conclusion_status"], "PASS")
            persisted = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["unified_delivery_status"], "PASS")
            self.assertNotIn("summary_artifact", persisted)
            self.assertEqual(final_summary["summary_artifact"]["sha256"], hashlib.sha256(summary_path.read_bytes()).hexdigest())
            self.assertTrue(mocked_run.call_args.kwargs["capture_output"])
            self.assertTrue(mocked_run.call_args.kwargs["text"])

    def test_authoritative_execution_contract_binds_the_unified_delivery_code(self) -> None:
        contracts_path = ROOT.parent / "stock-unified" / "references" / "stock_execution_contracts.json"
        payload = json.loads(contracts_path.read_text(encoding="utf-8"))
        contract = next(
            row for row in payload["contracts"]
            if row["skill_id"] == "support-pressure-analysis-system"
        )
        relative = "scripts/unified_five_theory_conclusion.py"
        self.assertIn(relative, contract["workflow_guard"]["required_bindings"])
        formatter_resolved = str(FORMATTER_PATH.resolve()).casefold()
        bindings = {
            str(Path(row["path"]).resolve()).casefold(): row["sha256"]
            for row in contract["business_bindings"]
        }
        self.assertEqual(bindings[formatter_resolved], hashlib.sha256(FORMATTER_PATH.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
