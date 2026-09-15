from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import csv
import datetime as dt
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "scripts" / "scientific_engine.py"
SPEC = importlib.util.spec_from_file_location("scientific_engine", ENGINE_PATH)
ENGINE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ENGINE)


def range_rows(count: int = 420, scale: float = 1.0) -> list[dict]:
    start = dt.date(2024, 1, 2)
    rows = []
    previous = 100.0
    day = start
    index = 0
    while len(rows) < count:
        if day.weekday() < 5:
            centre = 100.0 + 4.8 * math.sin(index * math.pi / 10.0)
            close = centre + 0.15 * math.sin(index * 1.71)
            open_price = previous
            high = min(105.2, max(open_price, close) + 0.55)
            low = max(94.8, min(open_price, close) - 0.55)
            rows.append(
                {
                    "date": day.isoformat(),
                    "open": open_price * scale,
                    "high": high * scale,
                    "low": low * scale,
                    "close": close * scale,
                    "volume": 1_000_000 + (index % 20) * 20_000,
                    "amount": 0,
                }
            )
            previous = close
            index += 1
        day += dt.timedelta(days=1)
    return rows


class ScientificEngineTests(unittest.TestCase):
    def test_tdx_standard_analysis_requires_full_local_history(self) -> None:
        parser = ENGINE.build_parser()
        self.assertEqual(parser.parse_args([]).limit, 0)
        with self.assertRaisesRegex(ENGINE.AnalysisBlocked, "partial_tdx_history_limit_forbidden"):
            ENGINE.load_tdx("000001.SH", 500)
        rows, source = ENGINE.load_tdx("000001.SH", 0)
        self.assertGreater(len(rows), 500)
        self.assertEqual(source["history_scope"], "FULL_LOCAL_TDX_FILE")
        self.assertTrue(source["full_history_required"])
        self.assertTrue(source["full_history_verified"])
        self.assertEqual(source["records_returned"], source["source_records_available"])
        self.assertEqual(source["records_returned"], len(rows))

    def test_analyze_rejects_truncated_tdx_provenance(self) -> None:
        source = {
            "source_type": "tdx_local_hub",
            "records_returned": 420,
            "source_records_available": 500,
            "full_history_required": True,
            "full_history_verified": False,
        }
        with self.assertRaisesRegex(ENGINE.AnalysisBlocked, "tdx_full_history_not_verified"):
            ENGINE.analyze(range_rows(420), "TEST", "pressure", source, perform_walk_forward=False)

    def test_market_suffix_is_preserved_for_tdx(self) -> None:
        self.assertEqual(ENGINE._tdx_request_symbol("000001.SH"), "sh000001")
        self.assertEqual(ENGINE._tdx_request_symbol("000001.SZ"), "sz000001")
        self.assertEqual(ENGINE._tdx_request_symbol("BJ.920001"), "bj920001")

    def test_known_range_recovers_both_sides(self) -> None:
        report = ENGINE.analyze(range_rows(), "TEST", "pressure", {"source_type": "synthetic"})
        support = report["conclusion"]["primary_support_zone"]
        major_resistance = report["conclusion"]["major_structural_resistance_zone"]
        self.assertIsNotNone(support)
        self.assertIsNotNone(major_resistance)
        self.assertLess(abs(support["center"] - 95.0), 2.0)
        self.assertLess(abs(major_resistance["center"] - 105.0), 2.0)
        self.assertIn(report["walk_forward_validation"]["validation_grade"], {"A", "B", "C", "D"})
        self.assertEqual(report["conclusion"]["directional_prediction"], "NOT_CLAIMED")
        self.assertEqual(
            ENGINE.PARAMETER_SET_ID,
            "confirmed-structure-active-swing-h10-five-theory-v2",
        )
        self.assertEqual(
            report["walk_forward_validation"]["global_cross_sectional_gate"]["status"],
            "PASS",
        )
        self.assertFalse(report["walk_forward_validation"]["global_cross_sectional_gate"]["predictive_claim_allowed"])
        self.assertEqual(report["walk_forward_validation"]["validation_grade"], "D")
        self.assertEqual(report["conclusion"]["state"], "UNVALIDATED_CANDIDATE_ZONES_ONLY")
        if report["walk_forward_validation"]["validation_grade"] == "D":
            self.assertEqual(report["conclusion"]["state"], "UNVALIDATED_CANDIDATE_ZONES_ONLY")

    def test_global_calibration_caps_even_positive_local_result(self) -> None:
        validation = ENGINE._apply_global_calibration(
            {"status": "PASS", "validation_grade": "A", "reason": "synthetic_local_pass"}
        )
        self.assertEqual(validation["local_validation_grade"], "A")
        self.assertEqual(validation["validation_grade"], "D")
        self.assertEqual(validation["status"], "GLOBAL_NO_EMPIRICAL_LIFT")

    def test_missing_global_calibration_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scientific-sr-calibration-") as raw_temp:
            missing = Path(raw_temp) / "missing.json"
            calibration = ENGINE._load_global_calibration(missing)
        self.assertEqual(calibration["status"], "MISSING_OR_INCOMPATIBLE_CALIBRATION")
        self.assertEqual(calibration["validation_grade"], "D")
        self.assertFalse(calibration["predictive_claim_allowed"])

    def test_scale_invariance(self) -> None:
        base = ENGINE.analyze(range_rows(scale=1.0), "BASE", "pressure", {"source_type": "synthetic"}, perform_walk_forward=False)
        scaled = ENGINE.analyze(range_rows(scale=10.0), "SCALED", "pressure", {"source_type": "synthetic"}, perform_walk_forward=False)
        base_support = base["conclusion"]["primary_support_zone"]["center"]
        scaled_support = scaled["conclusion"]["primary_support_zone"]["center"]
        self.assertAlmostEqual(scaled_support / base_support, 10.0, places=2)

    def test_confirmed_pivots_never_use_unconfirmed_tail(self) -> None:
        rows, _ = ENGINE.normalize_rows(range_rows(180))
        pivots = ENGINE._confirmed_pivots(rows, ENGINE._atr_series(rows))
        for pivot in pivots:
            width = int(pivot["label"].rsplit("w", 1)[1])
            self.assertLessEqual(pivot["index"], len(rows) - width - 1)

    def test_bad_ohlc_is_blocked(self) -> None:
        rows = range_rows(100)
        rows[-1]["high"] = rows[-1]["low"] - 1
        with self.assertRaises(ENGINE.AnalysisBlocked):
            ENGINE.analyze(rows, "BAD", "pressure", {"source_type": "synthetic"})

    def test_large_unadjusted_jump_is_blocked(self) -> None:
        rows = range_rows(100)
        rows[-1]["open"] *= 0.5
        rows[-1]["high"] *= 0.5
        rows[-1]["low"] *= 0.5
        rows[-1]["close"] *= 0.5
        with self.assertRaises(ENGINE.AnalysisBlocked):
            ENGINE.analyze(rows, "JUMP", "pressure", {"source_type": "synthetic"})

    def test_cli_persists_hashable_readback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scientific-sr-test-") as raw_temp:
            temp = Path(raw_temp)
            source = temp / "rows.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["date", "open", "high", "low", "close", "volume", "amount"])
                writer.writeheader()
                writer.writerows(range_rows(180))
            out_dir = temp / "out"
            result = subprocess.run(
                [sys.executable, str(ENGINE_PATH), "--input", str(source), "--symbol", "TEST", "--out-dir", str(out_dir), "--no-walk-forward"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                env={**os.environ, "ONESTOCK_STOCK_CANONICAL_CHILD": "1"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["status"], "PASS")
            report_path = Path(summary["items"][0]["artifact"]["path"])
            self.assertTrue(report_path.is_file())
            readback = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(readback["engine_version"], ENGINE.ENGINE_VERSION)
            self.assertEqual(readback["parameter_set_id"], ENGINE.PARAMETER_SET_ID)
            self.assertEqual(readback["conclusion"]["state"], "UNVALIDATED_CANDIDATE_ZONES_ONLY")

    def test_all_modes_use_local_scientific_engine(self) -> None:
        targets = set()
        for mode in ("pressure", "resistance", "technical"):
            result = subprocess.run(
                [sys.executable, str(ENGINE_PATH), "--mode", mode, "--route-check"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                env={**os.environ, "ONESTOCK_STOCK_CANONICAL_CHILD": "1"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "CLEAN_PASS")
            targets.add(payload["engine"])
        self.assertEqual(targets, {str(ENGINE_PATH.resolve())})


if __name__ == "__main__":
    unittest.main(verbosity=2)
