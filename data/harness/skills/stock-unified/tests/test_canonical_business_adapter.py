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
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "scripts" / "canonical_business_adapter.py"
RUNTIME_PATH = ROOT.parents[1] / "scripts" / "stock_canonical_runtime.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ADAPTER = load_module(
    "stock_unified_canonical_business_adapter_test",
    ADAPTER_PATH,
)
RUNTIME = load_module(
    "stock_canonical_runtime_compile_test",
    RUNTIME_PATH,
)


def load_skill_adapter(skill_id: str):
    return load_module(
        f"{skill_id.replace('-', '_')}_business_adapter_test",
        ROOT.parent / skill_id / "scripts" / "canonical_business_adapter.py",
    )


class CanonicalBusinessAdapterTests(unittest.TestCase):
    def test_runtime_syntax_check_does_not_write_to_fresh_pycache_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "deep" / "skill" / "scripts" / "entry.py"
            script.parent.mkdir(parents=True)
            script.write_text("VALUE = 1\n", encoding="utf-8")
            cache_prefix = root / "fresh-cache"
            errors: list[str] = []
            with mock.patch.dict(
                os.environ,
                {"PYTHONPYCACHEPREFIX": str(cache_prefix)},
            ):
                RUNTIME.compile_script_syntax(script, errors)

            self.assertEqual(errors, [])
            self.assertFalse(cache_prefix.exists())
            self.assertFalse((script.parent / "__pycache__").exists())

    def run_adapter(self, child: dict) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as temporary:
            stdout = io.StringIO()
            with mock.patch.dict(
                os.environ,
                {"CODEX_STOCK_CANONICAL_EXECUTION": "1"},
            ), mock.patch.object(
                ADAPTER,
                "run_child",
                return_value=child,
            ), mock.patch.object(
                sys,
                "argv",
                [
                    str(ADAPTER_PATH),
                    "--run-dir",
                    temporary,
                ],
            ), contextlib.redirect_stdout(stdout):
                returncode = ADAPTER.main()
        return returncode, json.loads(stdout.getvalue())

    def test_info_payload_is_rejected_even_when_child_returns_zero(self) -> None:
        info_payload = {
            "runtime_surface": "Codex",
            "entry": str(ROOT / "scripts" / "stock-unified.py"),
            "catalog": str(ROOT / "references" / "stock_skill_ids.json"),
            "contracts": str(
                ROOT / "references" / "stock_execution_contracts.json"
            ),
            "commands": ["consistency", "run-all"],
        }
        child = {
            "returncode": 0,
            "stdout": json.dumps(info_payload, ensure_ascii=False),
            "stderr": "",
            "timed_out": False,
        }
        returncode, result = self.run_adapter(child)
        self.assertEqual(returncode, 2)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn(
            "child_schema_mismatch",
            result["business_process"]["validation_errors"],
        )

    def test_malformed_mixed_and_procedural_payloads_are_rejected(self) -> None:
        cases = [
            ("not-json", "child_stdout_not_single_json_object"),
            (
                '{"schema":"STOCK_UNIFIED_SELFTEST_V1"}\n'
                '{"schema":"STOCK_UNIFIED_SELFTEST_V1"}',
                "child_stdout_not_single_json_object",
            ),
            (
                json.dumps(
                    {
                        "schema": "STOCK_UNIFIED_SELFTEST_V1",
                        "status": "PROCEDURAL",
                    }
                ),
                "child_status_not_clean",
            ),
        ]
        for stdout, expected in cases:
            with self.subTest(expected=expected):
                returncode, result = self.run_adapter(
                    {
                        "returncode": 0,
                        "stdout": stdout,
                        "stderr": "",
                        "timed_out": False,
                    }
                )
                self.assertEqual(returncode, 2)
                self.assertIn(
                    expected,
                    result["business_process"]["validation_errors"],
                )

    def test_incomplete_duplicate_or_wrong_order_summary_is_rejected(self) -> None:
        skills = json.loads(
            (ROOT / "references" / "stock_skill_ids.json").read_text(
                encoding="utf-8"
            )
        )["skills"]
        cases = [
            (skills[:-1], "child_skill_ids_mismatch"),
            (skills[:-1] + [skills[0]], "child_skill_ids_not_unique"),
            (list(reversed(skills)), "child_skill_ids_mismatch"),
        ]
        for skill_ids, expected in cases:
            expected_count = len(skills)
            payload = {
                "schema": "STOCK_UNIFIED_SELFTEST_V1",
                "status": "CLEAN_PASS",
                "catalog_count": expected_count,
                "entry_count": expected_count,
                "selftest_pass": expected_count,
                "failure_count": 0,
                "errors": [],
                "skill_ids": skill_ids,
                "report": {
                    "path": str(ROOT / "reports" / "executions" / "missing.json"),
                    "size": 1,
                    "sha256": "0" * 64,
                },
            }
            returncode, result = self.run_adapter(
                {
                    "returncode": 0,
                    "stdout": json.dumps(payload),
                    "stderr": "",
                    "timed_out": False,
                }
            )
            self.assertEqual(returncode, 2)
            self.assertIn(
                expected,
                result["business_process"]["validation_errors"],
            )

    def test_valid_summary_requires_matching_report_readback(self) -> None:
        skills = json.loads(
            (ROOT / "references" / "stock_skill_ids.json").read_text(
                encoding="utf-8"
            )
        )["skills"]
        with tempfile.TemporaryDirectory() as temporary:
            report_path = Path(temporary) / "stock-unified-current.json"
            rows = []
            for skill_id in skills:
                entry = ROOT.parent / skill_id / "scripts" / "codex_entry.py"
                rows.append(
                    {
                        "skill_id": skill_id,
                        "entry": str(entry),
                        "command": [sys.executable, str(entry), "selftest"],
                        "returncode": 0,
                        "selftest_pass": True,
                        "errors": [],
                    }
                )
            report = {
                "schema": "STOCK_UNIFIED_SELFTEST_V1",
                "status": "CLEAN_PASS",
                "catalog_count": len(skills),
                "entry_count": len(skills),
                "selftest_pass": len(skills),
                "failure_count": 0,
                "procedural_entry_count": 0,
                "errors": [],
                "regression": {
                    "status": "CLEAN_PASS",
                    "test_count": 1,
                    "errors": [],
                },
                "skill_ids": skills,
                "skills": rows,
            }
            deliverables = {}
            for role, filename in ADAPTER.DELIVERABLE_NAMES.items():
                deliverable_path = report_path.parent / filename
                deliverable_path.write_text(
                    json.dumps({"status": "CLEAN_PASS", "role": role}) + "\n",
                    encoding="utf-8",
                )
                deliverables[role] = {
                    "path": str(deliverable_path),
                    "size": deliverable_path.stat().st_size,
                    "sha256": ADAPTER.sha256_file(deliverable_path),
                }
            report["deliverables"] = deliverables
            encoded = (
                json.dumps(report, ensure_ascii=False, indent=2) + "\n"
            ).encode("utf-8")
            report_path.write_bytes(encoded)
            payload = {
                **report,
                "report": {
                    "path": str(report_path),
                    "size": len(encoded),
                    "sha256": ADAPTER.sha256_file(report_path),
                },
            }
            payload.pop("skills")
            with mock.patch.object(
                ADAPTER,
                "CURRENT_REPORT",
                report_path,
            ):
                returncode, result = self.run_adapter(
                    {
                        "returncode": 0,
                        "stdout": json.dumps(payload, ensure_ascii=False),
                        "stderr": "",
                        "timed_out": False,
                    }
                )
        self.assertEqual(returncode, 0, result)
        self.assertEqual(result["status"], "CLEAN_PASS")
        self.assertEqual(
            result["business_process"]["validation_errors"],
            [],
        )


class SkillBusinessArgumentTests(unittest.TestCase):
    def test_intraday_monitor_uses_supported_holding_arguments(self) -> None:
        adapter = load_skill_adapter("a-share-intraday-position-monitor")
        with tempfile.TemporaryDirectory() as temporary:
            command = adapter.business_command(Path(temporary))
        self.assertEqual(
            command[2:],
            [
                "run",
                "--symbol",
                "301372",
                "--cost",
                "25.0",
                "--shares",
                "200000",
                "--name",
                "科净源",
                "--stock-attestation",
                "off",
            ],
        )
        self.assertNotIn("--positions-json", command)

    def test_industry_chain_builds_real_contract_evidence_input(self) -> None:
        adapter = load_skill_adapter("industry-chain-analysis")
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            command = adapter.business_command(run_dir)
            evidence_path = Path(command[command.index("--input") + 1])
            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        self.assertEqual(command[2:4], ["run", "--input"])
        self.assertEqual(payload["schema"], "INDUSTRY-CHAIN-ANALYSIS-INPUT-1")
        self.assertEqual(payload["mode"], "mindset")
        self.assertIs(payload["test_mode"], False)
        self.assertTrue(payload["evidence"])
        self.assertTrue(Path(payload["evidence"][0]["source_locator"]).is_file())
        self.assertNotIn("--topic", command)

    def test_old_leader_writes_required_outputs_in_current_run(self) -> None:
        adapter = load_skill_adapter("old-leader-oversold-rebound")
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary).resolve()
            command = adapter.business_command(run_dir)
        self.assertEqual(command[2], "run")
        self.assertIn("--as-of", command)
        self.assertEqual(Path(command[command.index("--tdx") + 1]), Path(r"C:\new_tdx_mock"))
        self.assertEqual(
            Path(command[command.index("--json") + 1]),
            run_dir / "old-leader-result.json",
        )
        self.assertEqual(
            Path(command[command.index("--csv") + 1]),
            run_dir / "old-leader-result.csv",
        )
        self.assertNotIn("--date", command)


if __name__ == "__main__":
    unittest.main()
