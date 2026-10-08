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
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNTIME = load_module(
    "stock_canonical_runtime_delivery_authorization_test",
    Path(__file__).resolve().parents[3] / "scripts" / "stock_canonical_runtime.py",
)

DELIVERY_POLICY = {
    "authorization_required": True,
    "allow_receipt_bound_artifact": True,
    "allow_manifest_bound_artifact": True,
    "require_artifact_sha256": True,
    "require_clean_manifest_validation": True,
    "formatted_artifact_requires_template_binding": True,
    "formatted_artifact_requires_validator_binding": True,
}


class DeliveryAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "alpha-stock-skill"
        self.entry = self.root / "scripts" / "codex_entry.py"
        self.entry.parent.mkdir(parents=True)
        self.entry.write_text("# canonical facade\n", encoding="utf-8")
        self.template = self.root / "references" / "report_template_contract.json"
        self.template.parent.mkdir(parents=True)
        self.template.write_text('{"schema":"template"}\n', encoding="utf-8")
        self.validator = self.root / "scripts" / "report_validator.py"
        self.validator.write_text("# validator\n", encoding="utf-8")
        self.run_dir = self.root / "reports" / "executions" / "runs" / "canary"
        self.run_dir.mkdir(parents=True)
        self.artifact = self.run_dir / "report.docx"
        self.artifact.write_bytes(b"canonical formatted artifact")
        self.manifest = self.run_dir / "run_result.json"
        self.stdout = self.run_dir / "stdout.txt"
        self.stderr = self.run_dir / "stderr.txt"
        effective_date = date.today().isoformat()
        dimensions = {
            name: {
                "status": "CLEAN_PASS",
                "evidence_ids": [f"evidence-{index}"],
            }
            for index, name in enumerate(
                RUNTIME.PRODUCTION_POLICY["required_data_dimensions"],
                start=1,
            )
        }
        self.stdout.write_text(
            json.dumps({
                "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
                "skill_id": self.root.name,
                "status": "CLEAN_PASS",
                "errors": [],
                "business_process": {
                    "returncode": 0,
                    "timed_out": False,
                    "failure_tokens": [],
                    "validation_errors": [],
                },
                "business_binding": {
                    "path": str(self.entry.resolve()),
                    "sha256": RUNTIME.sha256_file(self.entry),
                },
                "artifacts": {},
                "data_gate": {
                    "schema": RUNTIME.DATA_GATE_SCHEMA,
                    "status": "CLEAN_PASS",
                    "skill_id": self.root.name,
                    "errors": [],
                    "evidence_set_id": "test-evidence-set",
                    "effective_trading_date": effective_date,
                    "latest_required_trading_date": effective_date,
                    "dimensions": dimensions,
                },
            }),
            encoding="utf-8",
        )
        self.stdout.write_bytes(self.stdout.read_bytes() + b"\r\n")
        self.stderr.write_text("", encoding="utf-8")
        self.receipt_path = self.root / "reports" / "executions" / "receipt.json"
        self.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_manifest(validation_status="PASS")
        self.contract = self._build_contract(
            include_template=True,
            include_validator=True,
        )
        self._write_receipt()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_manifest(self, *, validation_status: str) -> None:
        artifact_hash = RUNTIME.sha256_file(self.artifact)
        payload = {
            "status": "PASS",
            "docx": str(self.artifact.resolve()),
            "docx_sha256": artifact_hash,
            "validation": {
                "status": validation_status,
                "errors": [] if validation_status == "PASS" else ["failed"],
                "docx": str(self.artifact.resolve()),
                "docx_sha256": artifact_hash,
            },
        }
        self.manifest.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _build_contract(
        self,
        *,
        include_template: bool,
        include_validator: bool,
    ) -> dict:
        bindings = []
        for path, include in (
            (self.template, include_template),
            (self.validator, include_validator),
        ):
            if include:
                bindings.append(RUNTIME.file_artifact(path))
        contract = {
            "skill_id": self.root.name,
            "business_command": [sys.executable, "-c", "print('unused')"],
            "cwd": "{skill_root}",
            "timeout_seconds": 30,
            "semantic_assertions": [{"type": "returncode_zero"}],
            "required_artifacts": [],
            "facade_sha256": RUNTIME.sha256_file(self.entry),
            "executor_sha256": RUNTIME.sha256_file(Path(RUNTIME.__file__)),
            "business_bindings": bindings,
            "workflow_guard": {
                "direct_legacy_execution": "blocked",
                "requires_explicit_business_args": False,
                "forbidden_business_actions": ["info", "inspect", "selftest"],
                "required_bindings": [],
            },
            "delivery_policy": dict(DELIVERY_POLICY),
            "production_policy": dict(RUNTIME.PRODUCTION_POLICY),
            "catalog_sha256": RUNTIME.sha256_file(RUNTIME.CATALOG_PATH),
        }
        contract["contract_sha256"] = RUNTIME.contract_sha256(contract)
        return contract

    def _write_receipt(self) -> None:
        command, cwd, _ = RUNTIME.expanded_execution(
            self.contract,
            self.root,
            self.run_dir,
        )
        stdout_text = self.stdout.read_bytes().decode("utf-8")
        execution_purpose = "stock_conclusion"
        fingerprint = RUNTIME.request_fingerprint(
            self.root.name,
            self.contract["contract_sha256"],
            [],
            execution_purpose,
        )
        business_validation = RUNTIME.evaluate_business_stdout(
            self.root.name,
            stdout_text,
            require_data_gate=True,
        )
        stage_names = [
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
        receipt = {
            "receipt_version": RUNTIME.RECEIPT_VERSION,
            "runtime": RUNTIME.RUNTIME_ID,
            "runtime_surface": "Codex",
            "skill_id": self.root.name,
            "entry": str(self.entry.resolve()),
            "run_dir": str(self.run_dir.resolve()),
            "command": command,
            "extra_args": [],
            "cwd": str(cwd),
            "returncode": 0,
            "status": "CLEAN_PASS",
            "execution_purpose": execution_purpose,
            "request_fingerprint": fingerprint,
            "failure_class": "NONE",
            "production_policy_sha256": RUNTIME.production_policy_sha256(),
            "production_surface_signature": RUNTIME.contract_surface_signature(),
            "production_readiness": {
                "schema": RUNTIME.PRODUCTION_READINESS_SCHEMA,
                "status": "CLEAN_PASS",
                "execution_purpose": execution_purpose,
                "conclusion_eligible": True,
                "request_fingerprint": fingerprint,
                "policy_sha256": RUNTIME.production_policy_sha256(),
                "data_gate": business_validation["data_gate"],
                "failure_class": "NONE",
                "output_bytes": {
                    "stdout": len(stdout_text.encode("utf-8")),
                    "stderr": 0,
                    "limit": RUNTIME.MAX_PROCESS_OUTPUT_BYTES,
                    "limited": False,
                },
                "persistence": RUNTIME.PRODUCTION_POLICY["persistence"],
                "errors": [],
            },
            "facade_sha256": self.contract["facade_sha256"],
            "executor_sha256": self.contract["executor_sha256"],
            "contract_sha256": self.contract["contract_sha256"],
            "business_bindings": self.contract["business_bindings"],
            "evidence_set": {
                "enabled": False,
                "status": "DISABLED",
                "environment": {},
                "errors": [],
            },
            "binding_errors": [],
            "business_stdout_validation": business_validation,
            "semantic_assertions": RUNTIME.evaluate_semantic_assertions(
                self.contract["semantic_assertions"],
                0,
                stdout_text,
                "",
            ),
            "required_artifacts": [RUNTIME.file_artifact(self.manifest)],
            "stdout_artifact": RUNTIME.file_artifact(self.stdout),
            "stderr_artifact": RUNTIME.file_artifact(self.stderr),
            "workflow_telemetry": [
                {
                    "name": name,
                    "status": "CLEAN_PASS",
                    "elapsed_seconds": 0.0,
                }
                for name in stage_names
            ],
        }
        receipt["receipt_integrity"] = RUNTIME.receipt_integrity(receipt)
        self.receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _authorize(self, artifact: Path | None) -> tuple[int, dict]:
        stdout = io.StringIO()
        with mock.patch.object(
            RUNTIME,
            "skill_context",
            return_value=(self.root, self.root.name, self.contract),
        ), contextlib.redirect_stdout(stdout):
            returncode = RUNTIME.authorize_delivery(
                str(self.entry),
                str(self.receipt_path),
                str(artifact) if artifact is not None else None,
            )
        return returncode, json.loads(stdout.getvalue())

    def test_clean_manifest_bound_artifact_is_authorized(self) -> None:
        returncode, result = self._authorize(self.artifact)
        self.assertEqual(returncode, 0, result)
        self.assertEqual(result["schema"], "STOCK_DELIVERY_AUTHORIZATION_V1")
        self.assertEqual(result["status"], "CLEAN_PASS")
        self.assertEqual(
            Path(result["artifact"]["path"]),
            self.artifact.resolve(),
        )
        self.assertTrue(Path(result["authorization"]["path"]).is_file())

    def test_unmanifested_artifact_is_rejected(self) -> None:
        arbitrary = self.run_dir / "arbitrary.docx"
        arbitrary.write_bytes(b"manual file")
        returncode, result = self._authorize(arbitrary)
        self.assertEqual(returncode, 2)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("artifact_not_receipt_or_manifest_bound", result["errors"])

    def test_hash_drifted_manifest_artifact_is_rejected(self) -> None:
        self.artifact.write_bytes(b"changed after canonical run")
        returncode, result = self._authorize(self.artifact)
        self.assertEqual(returncode, 2)
        self.assertIn("artifact_manifest_hash_mismatch", result["errors"])

    def test_formatted_artifact_without_template_or_validator_is_rejected(
        self,
    ) -> None:
        self.contract = self._build_contract(
            include_template=False,
            include_validator=False,
        )
        self._write_receipt()
        returncode, result = self._authorize(self.artifact)
        self.assertEqual(returncode, 2)
        self.assertIn("formatted_artifact_template_binding_missing", result["errors"])
        self.assertIn("formatted_artifact_validator_binding_missing", result["errors"])

    def test_failed_nested_manifest_validation_is_rejected(self) -> None:
        self._write_manifest(validation_status="BLOCKED")
        self._write_receipt()
        returncode, result = self._authorize(self.artifact)
        self.assertEqual(returncode, 2)
        self.assertIn("manifest_validation_not_clean", result["errors"])

    def test_clean_receipt_authorizes_stock_conclusion(self) -> None:
        returncode, result = self._authorize(None)
        self.assertEqual(returncode, 0, result)
        self.assertEqual(result["delivery_kind"], "stock_conclusion")
        self.assertIsNone(result["artifact"])

    def test_completion_gate_retries_contract_drift_until_authorized(self) -> None:
        runs: list[int] = []
        authorizations: list[str] = []

        def run_attempt(attempt: int) -> dict:
            runs.append(attempt)
            return {
                "status": "CLEAN_PASS",
                "receipt": f"receipt-{attempt}.json",
            }

        def authorize_attempt(receipt: str) -> dict:
            authorizations.append(receipt)
            if receipt == "receipt-1.json":
                return {
                    "status": "BLOCKED",
                    "errors": ["receipt_contract_sha256_mismatch"],
                }
            return {"status": "CLEAN_PASS", "errors": []}

        result = RUNTIME.complete_with_retry(
            run_attempt,
            authorize_attempt,
            max_attempts=3,
        )
        self.assertEqual(result["status"], "CLEAN_PASS", result)
        self.assertEqual(result["attempt_count"], 2)
        self.assertEqual(runs, [1, 2])
        self.assertEqual(
            authorizations,
            ["receipt-1.json", "receipt-2.json"],
        )

    def test_completion_gate_reconciles_business_binding_drift_before_retry(
        self,
    ) -> None:
        runs: list[int] = []
        reconciliations: list[tuple[set[str], int]] = []

        def run_attempt(attempt: int) -> dict:
            runs.append(attempt)
            return {
                "status": "CLEAN_PASS",
                "receipt": f"receipt-{attempt}.json",
            }

        def authorize_attempt(receipt: str) -> dict:
            if receipt == "receipt-1.json":
                return {
                    "status": "BLOCKED",
                    "errors": [
                        "business_file_hash_mismatch:D:\\C盘转移\\日志\\codex\\AGENTS.md",
                    ],
                }
            return {"status": "CLEAN_PASS", "errors": []}

        def prepare_retry(errors: set[str], attempt: int) -> dict:
            reconciliations.append((errors, attempt))
            return {"status": "CLEAN_PASS", "errors": []}

        result = RUNTIME.complete_with_retry(
            run_attempt,
            authorize_attempt,
            prepare_retry=prepare_retry,
            max_attempts=3,
        )
        self.assertEqual(result["status"], "CLEAN_PASS", result)
        self.assertEqual(result["attempt_count"], 2)
        self.assertEqual(runs, [1, 2])
        self.assertEqual(
            reconciliations,
            [({"business_file_hash_mismatch:D:\\C盘转移\\日志\\codex\\AGENTS.md"}, 1)],
        )
        self.assertEqual(
            result["attempts"][0]["retry_preparation"]["status"],
            "CLEAN_PASS",
        )

    def test_completion_drift_reconciliation_never_rewrites_contracts(self) -> None:
        check_result = {
            "status": "CLEAN_PASS",
            "changed_field_count": 0,
            "changes": [],
        }
        child = {
            "returncode": 0,
            "stdout": json.dumps(check_result),
            "stderr": "",
        }
        stable = {"status": "CLEAN_PASS", "errors": []}
        with mock.patch.object(
            RUNTIME,
            "run_process",
            return_value=child,
        ) as run_mock, mock.patch.object(
            RUNTIME,
            "wait_for_contract_stability",
            return_value=stable,
        ):
            result = RUNTIME.reconcile_completion_contract_drift(
                {"receipt_contract_sha256_mismatch"},
                1,
            )

        self.assertEqual(result["status"], "CLEAN_PASS", result)
        command = run_mock.call_args.args[0]
        self.assertIn("--check", command)
        self.assertNotIn("--write", command)

    def test_completion_gate_parser_preserves_business_arguments(self) -> None:
        parsed = RUNTIME.parse_complete_request([
            "--artifact-relative",
            r"deliverables\三公式综合评分8K海报.png",
            "--max-attempts",
            "4",
            "--",
            "score-composite",
            "--board-name",
            "飞龙在天",
        ])
        self.assertEqual(parsed["max_attempts"], 4)
        self.assertEqual(
            parsed["artifact_relative"],
            r"deliverables\三公式综合评分8K海报.png",
        )
        self.assertEqual(
            parsed["business_args"],
            ["score-composite", "--board-name", "飞龙在天"],
        )

    def test_completion_run_command_consumes_lone_run_intent(self) -> None:
        entry = Path(__file__).resolve().parents[1] / "scripts" / "codex_entry.py"
        command = RUNTIME.completion_run_command(entry, ["run"])
        self.assertEqual(command, [sys.executable, str(entry), "run"])

    def test_completion_run_command_preserves_action_specific_arguments(self) -> None:
        entry = Path(__file__).resolve().parents[2] / "feilong-strategy" / "scripts" / "codex_entry.py"
        business_args = ["score-composite", "--board-name", "飞龙在天"]
        command = RUNTIME.completion_run_command(entry, business_args)
        self.assertEqual(
            command,
            [sys.executable, str(entry), "run", "--", *business_args],
        )


if __name__ == "__main__":
    unittest.main()
