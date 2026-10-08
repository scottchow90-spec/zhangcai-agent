from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import stock_contract_catalog as CATALOG_MODULE


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


AGGREGATE = load_module(
    "stock_unified_global_preflight_test",
    SCRIPTS / "stock-unified.py",
)
RUNTIME = load_module(
    "stock_canonical_runtime_global_preflight_test",
    ROOT.parents[1] / "scripts" / "stock_canonical_runtime.py",
)


class GlobalContractPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        temporary_root = Path(self.temporary.name)
        self.catalog_path = temporary_root / "stock_skill_ids.json"
        self.contracts_path = temporary_root / "stock_execution_contracts.json"
        shutil.copy2(AGGREGATE.CATALOG, self.catalog_path)
        shutil.copy2(AGGREGATE.CONTRACTS, self.contracts_path)
        payload = json.loads(self.contracts_path.read_text(encoding="utf-8"))
        targets = {"big-bull-analysis-scoring-system", "feilong-strategy"}
        for row in payload["contracts"]:
            if row["skill_id"] in targets:
                row["executor_sha256"] = "0" * 64
        self.contracts_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def preflight(self) -> dict:
        return CATALOG_MODULE.contract_catalog_preflight(
            catalog_path=self.catalog_path,
            contracts_path=self.contracts_path,
            skills_root=AGGREGATE.SKILLS_ROOT,
            runtime_path=AGGREGATE.CANONICAL_RUNTIME,
        )

    def test_global_drift_blocks_before_any_child_process(self) -> None:
        preflight = self.preflight()
        canonical_report = AGGREGATE.RESULT_DIR / "stock-unified-current.json"
        canonical_before = (
            canonical_report.read_bytes() if canonical_report.is_file() else None
        )
        self.assertEqual(preflight["status"], "BLOCKED")
        self.assertEqual(
            preflight["failure_owner"],
            "global_stock_contract_catalog",
        )
        self.assertEqual(preflight["errors"], ["global_contract_catalog_drift"])

        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            AGGREGATE,
            "contract_catalog_preflight",
            return_value=preflight,
        ), mock.patch.object(
            AGGREGATE,
            "RESULT_DIR",
            Path(temporary),
        ), mock.patch.object(
            AGGREGATE,
            "run_child",
        ) as child_mock:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                returncode = AGGREGATE.run_all()
            temporary_report_path = Path(temporary) / "stock-unified-current.json"
            temporary_report = json.loads(
                temporary_report_path.read_text(encoding="utf-8")
            )

        self.assertEqual(returncode, 2)
        child_mock.assert_not_called()
        result = json.loads(stdout.getvalue().strip())
        self.assertEqual(temporary_report["schema"], result["schema"])
        self.assertEqual(temporary_report["status"], result["status"])
        self.assertEqual(Path(result["report"]["path"]), temporary_report_path)
        canonical_after = (
            canonical_report.read_bytes() if canonical_report.is_file() else None
        )
        self.assertEqual(canonical_after, canonical_before)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["schema"], "STOCK_UNIFIED_SELFTEST_V1")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["selftest_pass"], 0)
        self.assertEqual(result["failure_count"], len(AGGREGATE.load_catalog()))

    def test_direct_runtime_drift_does_not_start_business_process(self) -> None:
        entry = (
            AGGREGATE.SKILLS_ROOT
            / "big-bull-analysis-scoring-system"
            / "scripts"
            / "codex_entry.py"
        )
        stderr = io.StringIO()
        with mock.patch.object(
            RUNTIME,
            "CATALOG_PATH",
            self.catalog_path,
        ), mock.patch.object(
            RUNTIME,
            "CONTRACTS_PATH",
            self.contracts_path,
        ), mock.patch.object(
            RUNTIME,
            "run_process",
        ) as process_mock, contextlib.redirect_stderr(stderr):
            returncode = RUNTIME.run(str(entry), [])

        self.assertEqual(returncode, 2)
        process_mock.assert_not_called()
        blocked = json.loads(stderr.getvalue())
        self.assertEqual(blocked["failure_owner"], "global_stock_contract_catalog")
        self.assertEqual(blocked["errors"], ["global_contract_catalog_drift"])

    def test_runtime_revalidates_contract_surface_after_business(self) -> None:
        source = Path(RUNTIME.__file__).read_text(
            encoding="utf-8-sig",
            errors="replace",
        )
        self.assertIn('"contract_surface_postflight"', source)
        self.assertIn("contract_surface_changed_during_business", source)
        self.assertIn("contract_surface_changed_during_postflight", source)

    def test_sync_clears_drift_without_changing_catalog_order(self) -> None:
        payload, skills = CATALOG_MODULE.load_contract_inputs(
            catalog_path=self.catalog_path,
            contracts_path=self.contracts_path,
        )
        changes = CATALOG_MODULE.synchronize_contract_payload(
            payload,
            skills,
            skills_root=AGGREGATE.SKILLS_ROOT,
            runtime_path=AGGREGATE.CANONICAL_RUNTIME,
        )
        self.assertTrue(changes)
        self.contracts_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        preflight = self.preflight()
        self.assertEqual(preflight["status"], "CLEAN_PASS", preflight)
        self.assertEqual(
            skills,
            json.loads(self.catalog_path.read_text(encoding="utf-8"))["skills"],
        )

    def test_sync_restores_five_dimension_data_required_decision_guard(self) -> None:
        payload, skills = CATALOG_MODULE.load_contract_inputs(
            catalog_path=self.catalog_path,
            contracts_path=self.contracts_path,
        )
        contract = next(
            row
            for row in payload["contracts"]
            if row["skill_id"] == "five-dimension-resonance"
        )
        forbidden = next(
            row
            for row in contract["semantic_assertions"]
            if row["type"] == "output_not_contains"
        )
        decision_guards = {
            '"decision_status": "DATA_REQUIRED"',
            '"decision_status":"DATA_REQUIRED"',
        }
        forbidden["values"] = [
            value for value in forbidden["values"] if value not in decision_guards
        ]

        changes = CATALOG_MODULE.synchronize_contract_payload(
            payload,
            skills,
            skills_root=AGGREGATE.SKILLS_ROOT,
            runtime_path=AGGREGATE.CANONICAL_RUNTIME,
        )

        self.assertTrue(decision_guards.issubset(set(forbidden["values"])))
        self.assertTrue(
            any(
                change["skill_id"] == "five-dimension-resonance"
                and change["field"]
                == "semantic_assertions.data_required_decision_guard"
                for change in changes
            )
        )

    def test_big_bull_backtest_timeout_covers_measured_runtime(self) -> None:
        payload, skills = CATALOG_MODULE.load_contract_inputs(
            catalog_path=self.catalog_path,
            contracts_path=self.contracts_path,
        )
        CATALOG_MODULE.synchronize_contract_payload(
            payload,
            skills,
            skills_root=AGGREGATE.SKILLS_ROOT,
            runtime_path=AGGREGATE.CANONICAL_RUNTIME,
        )
        contract = next(
            row
            for row in payload["contracts"]
            if row["skill_id"] == "big-bull-analysis-scoring-system"
        )
        self.assertEqual(contract["business_command"][-1], "1200")
        self.assertEqual(contract["timeout_seconds"], 1260)

    def test_runtime_structured_business_result_rejects_false_success(self) -> None:
        valid = {
            "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
            "skill_id": "alpha",
            "status": "CLEAN_PASS",
            "errors": [],
            "business_process": {
                "returncode": 0,
                "timed_out": False,
                "failure_tokens": [],
                "validation_errors": [],
            },
            "business_binding": {
                "path": "alpha.py",
                "sha256": "0" * 64,
            },
            "artifacts": {},
        }
        cases = [
            ("not-json", "business_stdout_not_single_json_object"),
            (
                json.dumps(valid) + "\n" + json.dumps(valid),
                "business_stdout_not_single_json_object",
            ),
            (
                json.dumps({"status": "PROCEDURAL"}),
                "business_schema_mismatch",
            ),
            (
                json.dumps({**valid, "skill_id": "wrong"}),
                "business_skill_id_mismatch",
            ),
            (
                json.dumps({**valid, "status": "BLOCKED"}),
                "business_status_not_clean",
            ),
        ]
        for stdout, expected in cases:
            with self.subTest(expected=expected):
                result = RUNTIME.evaluate_business_stdout("alpha", stdout)
                self.assertFalse(result["ok"])
                self.assertIn(expected, result["errors"])

        result = RUNTIME.evaluate_business_stdout("alpha", json.dumps(valid))
        self.assertTrue(result["ok"], result)

    def test_runtime_blocks_missing_or_non_business_actions_before_execution(
        self,
    ) -> None:
        contract = {
            "workflow_guard": {
                "direct_legacy_execution": "blocked",
                "requires_explicit_business_args": True,
                "forbidden_business_actions": ["info", "inspect", "selftest"],
                "required_bindings": [],
            }
        }
        self.assertEqual(
            RUNTIME.business_request_errors(contract, []),
            ["explicit_business_action_required"],
        )
        self.assertEqual(
            RUNTIME.business_request_errors(contract, ["info"]),
            ["non_business_action_forbidden:info"],
        )
        self.assertEqual(
            RUNTIME.business_request_errors(contract, ["live-market"]),
            [],
        )


if __name__ == "__main__":
    unittest.main()
