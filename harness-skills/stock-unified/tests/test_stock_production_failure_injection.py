from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRODUCTION = load_module(
    "stock_production_readiness_failure_injection_test",
    SCRIPTS / "stock_production_readiness.py",
)
AUDIT = load_module(
    "stock_production_audit_failure_injection_test",
    SCRIPTS / "audit_stock_production_readiness.py",
)
RUNTIME = load_module(
    "stock_canonical_runtime_failure_injection_test",
    Path(__file__).resolve().parents[3] / "scripts" / "stock_canonical_runtime.py",
)


def clean_data_gate(skill_id: str) -> dict:
    effective = date.today().isoformat()
    return {
        "schema": PRODUCTION.DATA_GATE_SCHEMA,
        "status": "CLEAN_PASS",
        "skill_id": skill_id,
        "errors": [],
        "evidence_set_id": "failure-injection-evidence",
        "effective_trading_date": effective,
        "latest_required_trading_date": effective,
        "dimensions": {
            name: {
                "status": "CLEAN_PASS",
                "evidence_ids": [f"evidence-{index}"],
            }
            for index, name in enumerate(
                PRODUCTION.REQUIRED_DATA_GATE_DIMENSIONS,
                start=1,
            )
        },
    }


def clean_business_result(skill_id: str) -> dict:
    return {
        "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
        "skill_id": skill_id,
        "status": "CLEAN_PASS",
        "errors": [],
        "execution_id": "telemetry-only",
        "business_process": {
            "returncode": 0,
            "timed_out": False,
            "failure_tokens": [],
            "validation_errors": [],
        },
        "business_binding": {
            "path": "business.py",
            "sha256": "0" * 64,
        },
        "artifacts": {},
        "data_gate": clean_data_gate(skill_id),
    }


def clean_receipt() -> dict:
    fingerprint = "0" * 64
    purpose = "readiness_validation"
    readiness = {
        "schema": PRODUCTION.PRODUCTION_READINESS_SCHEMA,
        "status": "CLEAN_PASS",
        "execution_purpose": purpose,
        "conclusion_eligible": False,
        "request_fingerprint": fingerprint,
        "policy_sha256": PRODUCTION.production_policy_sha256(),
        "data_gate": None,
        "failure_class": "NONE",
        "output_bytes": {
            "stdout": 128,
            "stderr": 0,
            "limit": PRODUCTION.MAX_PROCESS_OUTPUT_BYTES,
            "limited": False,
        },
        "persistence": PRODUCTION.PRODUCTION_POLICY["persistence"],
        "errors": [],
    }
    required_stages = [
        "request_validation",
        "global_contract_preflight",
        "workflow_queue_wait",
        "binding_validation",
        "tdx_control_scan",
        "evidence_set",
        "supplemental_target_date",
        "supplemental_lianban",
        "business_process",
        "contract_surface_postflight",
        "result_validation",
        "production_gate",
        "runtime_inside_lease",
        "total_runtime_to_receipt",
    ]
    return {
        "receipt_version": PRODUCTION.RECEIPT_VERSION,
        "status": "CLEAN_PASS",
        "execution_purpose": purpose,
        "request_fingerprint": fingerprint,
        "failure_class": "NONE",
        "production_policy_sha256": PRODUCTION.production_policy_sha256(),
        "production_readiness": readiness,
        "workflow_telemetry": [
            {"name": name, "status": "CLEAN_PASS", "elapsed_seconds": 0.0}
            for name in required_stages
        ],
    }


class StockProductionFailureInjectionTests(unittest.TestCase):
    def test_trade_actions_credentials_and_oversized_requests_fail_closed(self) -> None:
        cases = [
            (["buy"], "forbidden_execution_action:buy"),
            (["run", "--action=sell"], "forbidden_execution_action:sell"),
            (["run", "--account-id=1"], "forbidden_execution_option:--account-id"),
            (
                ["run", '{"order_request":{"symbol":"000001"}}'],
                "forbidden_execution_field:order_request",
            ),
            (
                ["run", "x" * (PRODUCTION.MAX_ARGUMENT_BYTES + 1)],
                "business_argument_size_exceeded:1",
            ),
        ]
        for arguments, expected in cases:
            with self.subTest(expected=expected):
                errors = PRODUCTION.validate_request_arguments(arguments)
                self.assertIn(expected, errors)

    def test_stale_incomplete_and_future_data_gates_fail_closed(self) -> None:
        stale = clean_data_gate("alpha")
        stale["effective_trading_date"] = "2020-01-01"
        self.assertIn(
            "data_gate_trading_date_stale",
            PRODUCTION.validate_data_gate(stale, skill_id="alpha"),
        )

        incomplete = clean_data_gate("alpha")
        incomplete["dimensions"].pop("fundamentals")
        self.assertIn(
            "data_gate_dimension_missing:fundamentals",
            PRODUCTION.validate_data_gate(incomplete, skill_id="alpha"),
        )

        future = clean_data_gate("alpha")
        future["effective_trading_date"] = "2999-01-01"
        future["latest_required_trading_date"] = "2999-01-01"
        self.assertIn(
            "data_gate_trading_date_future",
            PRODUCTION.validate_data_gate(future, skill_id="alpha"),
        )

    def test_business_output_blocks_order_fields_but_allows_trace_id(self) -> None:
        valid = clean_business_result("alpha")
        result = PRODUCTION.evaluate_business_result(
            valid,
            skill_id="alpha",
            require_data_gate=True,
        )
        self.assertTrue(result["ok"], result)

        poisoned = copy.deepcopy(valid)
        poisoned["order_submission"] = {"symbol": "000001"}
        result = PRODUCTION.evaluate_business_result(
            poisoned,
            skill_id="alpha",
            require_data_gate=True,
        )
        self.assertFalse(result["ok"])
        self.assertIn("forbidden_execution_field:order_submission", result["errors"])

    def test_atomic_write_has_verified_hash_and_no_temporary_residue(self) -> None:
        cache_root = Path(r"F:\Codex\cache")
        cache_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache_root) as temporary:
            target = Path(temporary) / "atomic.json"
            artifact = PRODUCTION.atomic_write_json(target, {"value": 7})
            self.assertEqual(artifact["sha256"], PRODUCTION.sha256_file(target))
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"value": 7})
            self.assertEqual(list(target.parent.glob(f".{target.name}.*.tmp")), [])

    def test_bounded_process_terminates_output_flood_and_timeout(self) -> None:
        cache_root = Path(r"F:\Codex\cache")
        cache_root.mkdir(parents=True, exist_ok=True)
        environment = dict(os.environ)
        with mock.patch.object(RUNTIME, "MAX_PROCESS_OUTPUT_BYTES", 1024):
            flooded = RUNTIME.communicate_bounded(
                [
                    sys.executable,
                    "-c",
                    "import sys;sys.stdout.write('x'*65536);sys.stdout.flush()",
                ],
                cache_root,
                10,
                environment,
            )
        self.assertEqual(flooded["returncode"], 122, flooded)
        self.assertTrue(flooded["output_limited"])
        self.assertGreater(flooded["stdout_bytes"], 1024)
        self.assertLessEqual(len(flooded["stdout"].encode("utf-8")), 1024)

        timed_out = RUNTIME.communicate_bounded(
            [sys.executable, "-c", "import time;time.sleep(2)"],
            cache_root,
            1,
            environment,
        )
        self.assertEqual(timed_out["returncode"], 124, timed_out)
        self.assertTrue(timed_out["timed_out"])

    def test_receipt_tampering_and_missing_telemetry_fail_closed(self) -> None:
        receipt = clean_receipt()
        self.assertEqual(PRODUCTION.validate_receipt_schema(receipt), [])

        tampered = copy.deepcopy(receipt)
        tampered["production_readiness"]["request_fingerprint"] = "1" * 64
        self.assertIn(
            "receipt_production_request_fingerprint_mismatch",
            PRODUCTION.validate_receipt_schema(tampered),
        )

        missing_stage = copy.deepcopy(receipt)
        missing_stage["workflow_telemetry"] = missing_stage["workflow_telemetry"][:-1]
        self.assertIn(
            "receipt_workflow_stage_missing:total_runtime_to_receipt",
            PRODUCTION.validate_receipt_schema(missing_stage),
        )

    def test_contract_binding_removal_and_hash_drift_are_detected(self) -> None:
        payload = json.loads(AUDIT.CONTRACTS.read_text(encoding="utf-8-sig"))
        catalog_hash = PRODUCTION.sha256_file(AUDIT.CATALOG)
        original = payload["contracts"][0]

        missing = copy.deepcopy(original)
        production_path = str(
            (AUDIT.SKILLS_ROOT / "stock-unified" / "scripts" / "stock_production_readiness.py").resolve()
        ).casefold()
        missing["business_bindings"] = [
            binding
            for binding in missing["business_bindings"]
            if str(Path(binding["path"]).resolve()).casefold() != production_path
        ]
        missing["contract_sha256"] = AUDIT.contract_sha256(missing)
        result = AUDIT.audit_skill(missing, catalog_hash)
        self.assertTrue(
            any(error.startswith("shared_runtime_binding_missing:") for error in result["errors"]),
            result,
        )

        drifted = copy.deepcopy(original)
        drifted["business_bindings"][0]["sha256"] = "f" * 64
        drifted["contract_sha256"] = AUDIT.contract_sha256(drifted)
        result = AUDIT.audit_skill(drifted, catalog_hash)
        self.assertTrue(
            any(error.startswith("business_binding_drift:") for error in result["errors"]),
            result,
        )

    def test_failure_classification_is_total_and_deterministic(self) -> None:
        cases = {
            (0, False, False): "NONE",
            (124, True, False): "TIMEOUT",
            (122, False, True): "RESOURCE_LIMIT",
            (126, False, False): "SAFETY_VIOLATION",
            (125, False, False): "RUNTIME_ERROR",
            (2, False, False): "BUSINESS_REJECTED",
        }
        for arguments, expected in cases.items():
            with self.subTest(expected=expected):
                self.assertEqual(PRODUCTION.classify_failure(*arguments), expected)

    def test_full_audit_is_deterministic(self) -> None:
        first = AUDIT.build_audit()
        second = AUDIT.build_audit()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "CLEAN_PASS", first)


if __name__ == "__main__":
    unittest.main()
