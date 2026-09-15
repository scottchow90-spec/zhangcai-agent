from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENTRY = load_module("bottom_fishing_truthful_entry", ROOT / "scripts" / "抄底策略.py")
VALIDATOR = load_module(
    "bottom_fishing_truthful_validator",
    ROOT / "scripts" / "validate_bottom_fishing_delivery.py",
)


class TruthfulBottomFishingTests(unittest.TestCase):
    def test_candidate_pool_is_unique_and_has_local_tdx_names(self) -> None:
        with TemporaryDirectory() as temporary:
            blocknew = Path(temporary)
            (blocknew / "FLZT.blk").write_text(
                "0002192\n1603333\n",
                encoding="gbk",
            )
            (blocknew / "ZTC.blk").write_text(
                "0002192\n",
                encoding="gbk",
            )
            names = {
                ("SZ", "002192"): "融捷股份",
                ("SH", "603333"): "尚纬股份",
            }

            rows = ENTRY.read_bottom_candidates(
                limit=6,
                blocknew=blocknew,
                names=names,
            )

        self.assertEqual([row["symbol"] for row in rows], ["002192.SZ", "603333.SH"])
        self.assertEqual(rows[0]["name"], "融捷股份")
        self.assertEqual(rows[0]["source_blocks"], ["FLZT.blk", "ZTC.blk"])

    def test_validator_recomputes_duplicate_and_name_checks_from_final_rows(self) -> None:
        with TemporaryDirectory() as temporary:
            task_dir = Path(temporary)
            output = task_dir / "output"
            audit = task_dir / "audit"
            validation = task_dir / "validation"
            output.mkdir()
            audit.mkdir()
            validation.mkdir()
            rows = [
                {"symbol": "002192.SZ", "name": "", "selection_status": "SIGNAL"},
                {"symbol": "002192.SZ", "name": "", "selection_status": "SIGNAL"},
            ]
            (output / "final_picks_v2_public_validated.json").write_text(
                json.dumps(rows, ensure_ascii=False),
                encoding="utf-8",
            )
            (output / "final_picks_v2_public_validated.csv").write_text(
                "symbol,name,selection_status\n002192.SZ,,SIGNAL\n002192.SZ,,SIGNAL\n",
                encoding="utf-8",
            )
            (output / "candidate_evidence_v3.json").write_text(
                json.dumps(rows, ensure_ascii=False),
                encoding="utf-8",
            )
            (output / "public_quote_validation_v2.json").write_text(
                json.dumps({"status": "CLEAN_PASS", "quotes": []}),
                encoding="utf-8",
            )
            (output / "selection_process_and_result_v2_public_validated.md").write_text(
                "truthful fixture",
                encoding="utf-8",
            )
            (task_dir / "strict_overlay_v2_public_validated.md").write_text(
                "truthful fixture",
                encoding="utf-8",
            )
            for name, payload in {
                "scan_errors_v2.json": [],
                "duplicate_suppressed_v2.json": [],
                "exclusions_v2.json": {"excluded": []},
                "realtime_failed_v2.json": [],
            }.items():
                (audit / name).write_text(json.dumps(payload), encoding="utf-8")
            (validation / "acceptance_v2_public_validated.json").write_text(
                json.dumps(
                    {
                        "status": "CLEAN_PASS",
                        "selection_status": "SIGNAL",
                        "checks": {key: True for key in VALIDATOR.REQUIRED_TRUE_CHECKS},
                        "meta": {"scan_error_count": 0, "candidate_count": 2, "final_count": 2},
                    }
                ),
                encoding="utf-8",
            )

            failures = VALIDATOR.validate_task(task_dir)

        self.assertTrue(any("duplicate_symbol" in item for item in failures), failures)
        self.assertTrue(any("missing_name" in item for item in failures), failures)


if __name__ == "__main__":
    unittest.main(verbosity=2)
