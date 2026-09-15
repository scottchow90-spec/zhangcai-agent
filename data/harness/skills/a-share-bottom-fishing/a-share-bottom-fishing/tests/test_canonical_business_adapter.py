from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "scripts" / "canonical_business_adapter.py"
SPEC = importlib.util.spec_from_file_location("bottom_fishing_canonical_adapter", ADAPTER_PATH)
ADAPTER = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(ADAPTER)


class BottomFishingCanonicalAdapterTests(unittest.TestCase):
    def test_validated_selection_status_is_derived_from_business_evidence(self) -> None:
        child_stdout = json.dumps(
            {
                "status": "CLEAN_PASS",
                "stage": "generate_and_validate",
                "generated": {
                    "ok": True,
                    "task_dir": r"D:\C盘转移\日志\codex\reports\20260824_bottom_fishing_auto",
                    "final_count": 6,
                    "trade_date": "20260824",
                },
                "validator_returncode": 0,
                "validator_stdout": '{"status":"CLEAN_PASS","failures":[]}',
                "validator_stderr": "",
            },
            ensure_ascii=False,
        )

        result = ADAPTER.derive_validated_selection(child_stdout)

        self.assertEqual(result["forecast_status"], "VALIDATED_SELECTION")
        self.assertEqual(result["selection_status"], "VALIDATED_SELECTION")
        self.assertEqual(result["trade_date"], "20260824")
        self.assertEqual(result["candidate_count"], 6)
        self.assertTrue(result["validator_evidence"]["validated"])

    def test_clean_label_without_validator_evidence_is_rejected(self) -> None:
        child_stdout = json.dumps(
            {
                "status": "CLEAN_PASS",
                "stage": "generate_and_validate",
                "generated": {"ok": True, "final_count": 6, "trade_date": "20260824"},
                "validator_returncode": 1,
            }
        )

        with self.assertRaisesRegex(ValueError, "validator_not_clean"):
            ADAPTER.derive_validated_selection(child_stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
