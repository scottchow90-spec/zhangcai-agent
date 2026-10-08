from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import datetime as dt
import importlib.util
import math
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "scripts" / "scientific_engine.py"
SPEC = importlib.util.spec_from_file_location("scientific_engine_real_kline", ENGINE_PATH)
ENGINE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ENGINE)
ADAPTER_PATH = ROOT / "scripts" / "canonical_business_adapter.py"
ADAPTER_SPEC = importlib.util.spec_from_file_location("support_pressure_adapter", ADAPTER_PATH)
ADAPTER = importlib.util.module_from_spec(ADAPTER_SPEC)
assert ADAPTER_SPEC.loader is not None
ADAPTER_SPEC.loader.exec_module(ADAPTER)


def range_rows(phase: float, count: int = 260) -> list[dict]:
    rows: list[dict] = []
    day = dt.date(2023, 1, 3)
    previous = 100.0
    index = 0
    while len(rows) < count:
        if day.weekday() < 5:
            close = 100.0 + 6.0 * math.sin(index * math.pi / 12.0 + phase)
            rows.append(
                {
                    "date": day.isoformat(),
                    "open": previous,
                    "high": max(previous, close) + 0.7,
                    "low": min(previous, close) - 0.7,
                    "close": close,
                    "volume": 1_000_000 + (index % 13) * 30_000,
                    "amount": 0,
                }
            )
            previous = close
            index += 1
        day += dt.timedelta(days=1)
    return rows


class RealKlineFiveTheoryValidationTests(unittest.TestCase):
    def test_current_calibration_is_bound_to_v2_real_kline_negative_receipt(self) -> None:
        calibration = ENGINE._load_global_calibration()
        self.assertEqual(calibration["status"], "PASS")
        self.assertEqual(calibration["parameter_set_id"], ENGINE.PARAMETER_SET_ID)
        self.assertEqual(calibration["validation_conclusion"], "NO_RELIABLE_FIVE_THEORY_OUT_OF_SAMPLE_EDGE")
        self.assertFalse(calibration["predictive_claim_allowed"])
        calibration_document = __import__("json").loads(
            ENGINE.CALIBRATION_PATH.read_text(encoding="utf-8")
        )
        self.assertEqual(
            calibration_document["source_validation_receipt"]["sha256"],
            "806eb1f94e28eb37718ca94039cc8a2503e585d706115a1730479ad27d0eca90",
        )

    def test_validation_filters_fibonacci_to_the_active_confirmed_swing(self) -> None:
        rows, _ = ENGINE.normalize_rows(range_rows(0.2, count=220))
        subsystem = ENGINE.fibonacci_subsystem(rows, ENGINE._atr_series(rows))
        filtered = ENGINE._theory_validation_candidates("fibonacci", subsystem)
        if subsystem["candidate_levels"]:
            swing_numbers = [
                int(item["label"].split("swing_", 1)[1].split("_", 1)[0])
                for item in subsystem["candidate_levels"]
            ]
            active_number = max(swing_numbers)
            self.assertTrue(filtered)
            self.assertTrue(all(f"swing_{active_number}_" in item["label"] for item in filtered))

    def test_new_validation_cohort_excludes_every_predecessor_symbol(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tdx-exclusion-") as raw_temp:
            root = Path(raw_temp)
            for market, codes in {
                "sh": ("600001", "600002", "600003", "600004", "688001", "688002", "688003", "688004"),
                "sz": ("000001", "000002", "000003", "000004", "300001", "300002", "300003", "300004"),
                "bj": ("920001", "920002", "920003", "920004"),
            }.items():
                folder = root / market / "lday"
                folder.mkdir(parents=True)
                for code in codes:
                    (folder / f"{market}{code}.day").write_bytes(b"x" * (32 * 300))
            excluded = {"600001.SH", "688001.SH", "000001.SZ", "300001.SZ", "920001.BJ"}
            selection = ENGINE.select_tdx_validation_symbols(
                root,
                symbols_per_stratum=1,
                excluded_symbols=excluded,
            )
        self.assertFalse(set(selection["development"] + selection["holdout"]) & excluded)
        self.assertEqual(selection["excluded_symbol_count"], len(excluded))

    def test_short_history_theory_result_has_complete_zero_metrics(self) -> None:
        rows, _ = ENGINE.normalize_rows(range_rows(0.0, count=125))
        result = ENGINE.walk_forward_validate_theory(rows, "elliott_wave")
        self.assertEqual(result["status"], "INSUFFICIENT_SAMPLE")
        for key in (
            "actual_successes",
            "placebo_successes",
            "paired_actual_wins",
            "paired_placebo_wins",
            "paired_ties",
        ):
            self.assertEqual(result[key], 0)

    def test_skill_contract_requires_receipt_bound_real_kline_validation(self) -> None:
        skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        workflow_text = (ROOT / "references" / "workflow.md").read_text(encoding="utf-8")
        for text in (skill_text, workflow_text):
            self.assertIn("FIVE_THEORY_REAL_KLINE_VALIDATION_V1", text)
            self.assertIn("--validate-five-theories", text)
            self.assertIn("predictive_claim_allowed=true", text)
        scientific_text = (ROOT / "references" / "scientific_method.md").read_text(encoding="utf-8")
        self.assertIn("confirmed-structure-active-swing-h10-five-theory-v2", scientific_text)
        self.assertIn("NO_RELIABLE_FIVE_THEORY_OUT_OF_SAMPLE_EDGE", scientific_text)

    def test_canonical_adapter_forwards_validation_arguments_to_locked_entry(self) -> None:
        command = ADAPTER.business_command(
            ROOT / "reports" / "test-run",
            ["--validate-five-theories", "--validation-symbols-per-stratum", "2"],
        )
        self.assertEqual(command[-5:], ["run", "--", "--validate-five-theories", "--validation-symbols-per-stratum", "2"])

    def test_validation_symbol_selection_is_deterministic_and_disjoint(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tdx-universe-") as raw_temp:
            root = Path(raw_temp)
            for market, codes in {
                "sh": ("600001", "600002", "600003", "600004", "688001", "688002", "688003", "688004"),
                "sz": ("000001", "000002", "000003", "000004", "300001", "300002", "300003", "300004"),
                "bj": ("920001", "920002", "920003", "920004"),
            }.items():
                folder = root / market / "lday"
                folder.mkdir(parents=True)
                for code in codes:
                    (folder / f"{market}{code}.day").write_bytes(b"x" * (32 * 300))
            first = ENGINE.select_tdx_validation_symbols(root, symbols_per_stratum=1)
            second = ENGINE.select_tdx_validation_symbols(root, symbols_per_stratum=1)
        self.assertEqual(first, second)
        self.assertEqual(len(first["development"]), 5)
        self.assertEqual(len(first["holdout"]), 5)
        self.assertFalse(set(first["development"]) & set(first["holdout"]))
        self.assertEqual(set(first["strata"]), {"SH_MAIN", "STAR", "SZ_MAIN", "CHINEXT", "BEIJING"})

    def test_cli_parser_accepts_five_theory_validation_mode(self) -> None:
        args = ENGINE.build_parser().parse_args(
            ["--validate-five-theories", "--validation-symbols-per-stratum", "2"]
        )
        self.assertTrue(args.validate_five_theories)
        self.assertEqual(args.validation_symbols_per_stratum, 2)

    def test_validation_keeps_five_methods_and_frozen_holdout_separate(self) -> None:
        datasets = {}
        with tempfile.TemporaryDirectory(prefix="five-theory-validation-") as raw_temp:
            temp = Path(raw_temp)
            for index, symbol in enumerate(("DEV1", "DEV2", "HOLD1", "HOLD2")):
                source_path = temp / f"{symbol}.day"
                source_path.write_bytes((symbol * 64).encode("ascii"))
                datasets[symbol] = {
                    "rows": range_rows(index * 0.4),
                    "source": {
                        "source_type": "tdx_local_hub",
                        "data_path": str(source_path),
                        "data_size": source_path.stat().st_size,
                        "data_sha256": ENGINE._sha256(source_path),
                    },
                }
            payload = ENGINE.validate_five_theory_datasets(
                datasets,
                development_symbols=["DEV1", "DEV2"],
                holdout_symbols=["HOLD1", "HOLD2"],
                bootstrap_iterations=100,
                seed=20260817,
            )
        expected = {"elliott_wave", "chan_structure", "fibonacci", "gann", "wyckoff"}
        self.assertEqual(set(payload["subsystems"]), expected)
        self.assertEqual(payload["development"]["symbols_requested"], 2)
        self.assertEqual(payload["holdout"]["symbols_requested"], 2)
        self.assertTrue(payload["design"]["holdout_frozen_before_execution"])
        self.assertFalse(set(payload["development"]["symbols"]) & set(payload["holdout"]["symbols"]))
        self.assertEqual(len(payload["data_bindings"]), 4)
        self.assertTrue(all(item["data_sha256"] for item in payload["data_bindings"]))

    def test_validation_receipt_is_hash_bound_and_round_trips(self) -> None:
        payload = {
            "schema": "FIVE_THEORY_REAL_KLINE_VALIDATION_V1",
            "parameter_set_id": ENGINE.PARAMETER_SET_ID,
            "all_subsystems_pass": False,
            "predictive_claim_allowed": False,
            "subsystems": {},
            "development": {"symbols_requested": 0, "symbols": []},
            "holdout": {"symbols_requested": 0, "symbols": []},
            "data_bindings": [],
            "design": {"data_source": "tdx_local_hub", "holdout_frozen_before_execution": True},
        }
        with tempfile.TemporaryDirectory(prefix="five-theory-receipt-") as raw_temp:
            artifact = ENGINE.write_five_theory_validation_receipt(payload, Path(raw_temp))
            path = Path(artifact["receipt_artifact"]["path"])
            self.assertTrue(path.is_file())
            self.assertEqual(artifact["schema"], "FIVE_THEORY_REAL_KLINE_VALIDATION_RECEIPT_V1")
            self.assertEqual(artifact["receipt_artifact"]["sha256"], ENGINE._sha256(path))
            self.assertEqual(artifact["receipt_artifact"]["readback_status"], "PASS")
            self.assertEqual(artifact["validation"]["predictive_claim_allowed"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
