from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_ROOT = ROOT.parents[1]
SKILLS_ROOT = ROOT.parent
CATALOG = ROOT / "references" / "stock_skill_ids.json"
CONTRACTS = ROOT / "references" / "stock_execution_contracts.json"
PRODUCTION_MODULE = ROOT / "scripts" / "stock_production_readiness.py"
PRODUCTION_AUDITOR = ROOT / "scripts" / "audit_stock_production_readiness.py"
RUNTIME = CODEX_ROOT / "scripts" / "stock_canonical_runtime.py"
CACHE_TEMP = Path(r"F:\Codex\cache\temp")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class StockProductionReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8-sig"))
        cls.contract_payload = json.loads(CONTRACTS.read_text(encoding="utf-8-sig"))
        cls.production = (
            load_module("stock_production_readiness_test", PRODUCTION_MODULE)
            if PRODUCTION_MODULE.is_file()
            else None
        )

    def test_production_module_and_auditor_exist(self) -> None:
        self.assertTrue(PRODUCTION_MODULE.is_file())
        self.assertTrue(PRODUCTION_AUDITOR.is_file())

    def test_all_53_contracts_have_exact_policy_and_shared_bindings(self) -> None:
        self.assertIsNotNone(self.production)
        if self.production is None:
            return
        skills = self.catalog["skills"]
        contracts = self.contract_payload["contracts"]
        self.assertEqual(len(skills), 53)
        self.assertEqual(len(contracts), 53)
        self.assertEqual([row["skill_id"] for row in contracts], skills)
        required_shared = {
            str(path.resolve()).casefold()
            for path in self.production.required_shared_runtime_paths(
                codex_root=CODEX_ROOT,
                skills_root=SKILLS_ROOT,
            )
        }
        for contract in contracts:
            with self.subTest(skill_id=contract["skill_id"]):
                self.assertEqual(
                    contract.get("production_policy"),
                    self.production.PRODUCTION_POLICY,
                )
                self.assertEqual(
                    contract.get("catalog_sha256"),
                    self.production.sha256_file(CATALOG),
                )
                bindings = contract.get("business_bindings")
                self.assertIsInstance(bindings, list)
                paths = [
                    str(Path(str(item["path"])).resolve()).casefold()
                    for item in bindings
                ]
                self.assertEqual(len(paths), len(set(paths)))
                self.assertTrue(required_shared.issubset(set(paths)))
                for binding in bindings:
                    path = Path(binding["path"])
                    self.assertTrue(path.is_file(), path)
                    self.assertEqual(
                        binding["sha256"],
                        self.production.sha256_file(path),
                    )

        stock_unified = next(
            row for row in contracts if row["skill_id"] == "stock-unified"
        )
        required_artifacts = {
            item["path"] for item in stock_unified["required_artifacts"]
        }
        self.assertTrue({
            r"{stock_data_root}\selftests\股票技能生产就绪报告.json",
            r"{stock_data_root}\selftests\股票技能生产控制矩阵.json",
            r"{stock_data_root}\selftests\股票技能生产验证结果.json",
            r"{stock_data_root}\selftests\stock-unified-current.json",
        }.issubset(required_artifacts))

    def test_all_53_business_adapters_start_and_expose_help(self) -> None:
        cache = Path(r"F:\Codex\cache\pycache")

        def invoke(skill_id: str) -> tuple[str, int, str]:
            adapter = SKILLS_ROOT / skill_id / "scripts" / "canonical_business_adapter.py"
            completed = subprocess.run(
                [sys.executable, str(adapter), "--help"],
                cwd=str(adapter.parent.parent),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                env={
                    **__import__("os").environ,
                    "PYTHONPYCACHEPREFIX": str(cache),
                },
            )
            return skill_id, completed.returncode, completed.stdout + completed.stderr

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(invoke, self.catalog["skills"]))
        self.assertEqual(len(results), 53)
        for skill_id, returncode, output in results:
            with self.subTest(skill_id=skill_id):
                self.assertEqual(returncode, 0, output)
                self.assertIn("usage:", output.casefold())

    def test_request_validation_blocks_execution_and_secret_fields(self) -> None:
        self.assertIsNotNone(self.production)
        if self.production is None:
            return
        blocked_cases = (
            ["place-order"],
            ["run", "--broker-account", "abc"],
            ["run", '--payload={"api_key":"secret"}'],
            ["run", "bad\x00value"],
            ["x"] * (self.production.MAX_BUSINESS_ARGS + 1),
        )
        for arguments in blocked_cases:
            with self.subTest(arguments=arguments[:3]):
                self.assertTrue(
                    self.production.validate_request_arguments(arguments)
                )
        self.assertEqual(
            self.production.validate_request_arguments(
                ["score", "--symbol", "000001", "--price", "10.50"]
            ),
            [],
        )

    def test_business_output_is_strict_and_trade_execution_free(self) -> None:
        self.assertIsNotNone(self.production)
        if self.production is None:
            return
        base = {
            "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
            "skill_id": "stock-unified",
            "status": "CLEAN_PASS",
            "business_process": {
                "returncode": 0,
                "timed_out": False,
                "failure_tokens": [],
                "validation_errors": [],
            },
            "business_binding": {"path": str(RUNTIME), "sha256": "0" * 64},
            "artifacts": {},
        }
        clean = self.production.evaluate_business_result(
            base,
            skill_id="stock-unified",
        )
        self.assertEqual(clean["errors"], [])
        unsafe = json.loads(json.dumps(base))
        unsafe["order_submission"] = {"account_id": "live"}
        result = self.production.evaluate_business_result(
            unsafe,
            skill_id="stock-unified",
        )
        self.assertIn("forbidden_execution_field:order_submission", result["errors"])

    def test_conclusion_gate_requires_all_current_data_dimensions(self) -> None:
        self.assertIsNotNone(self.production)
        if self.production is None:
            return
        missing = self.production.validate_data_gate(
            None,
            skill_id="stock-analysis",
        )
        self.assertIn("data_gate_missing", missing)
        clean_gate = {
            "schema": "STOCK_DATA_GATE_V1",
            "status": "CLEAN_PASS",
            "skill_id": "stock-analysis",
            "effective_trading_date": "2026-08-31",
            "latest_required_trading_date": "2026-08-31",
            "evidence_set_id": "batch-20260831",
            "dimensions": {
                name: {"status": "CLEAN_PASS", "evidence_ids": [f"E-{index}"]}
                for index, name in enumerate(
                    self.production.REQUIRED_DATA_GATE_DIMENSIONS,
                    start=1,
                )
            },
            "errors": [],
        }
        self.assertEqual(
            self.production.validate_data_gate(
                clean_gate,
                skill_id="stock-analysis",
            ),
            [],
        )
        clean_gate["dimensions"].pop("fundamentals")
        self.assertIn(
            "data_gate_dimension_missing:fundamentals",
            self.production.validate_data_gate(
                clean_gate,
                skill_id="stock-analysis",
            ),
        )

    def test_request_fingerprint_is_deterministic_and_contract_bound(self) -> None:
        self.assertIsNotNone(self.production)
        if self.production is None:
            return
        first = self.production.request_fingerprint(
            "stock-analysis", "a" * 64, ["run", "000001"], "readiness_validation"
        )
        second = self.production.request_fingerprint(
            "stock-analysis", "a" * 64, ["run", "000001"], "readiness_validation"
        )
        changed = self.production.request_fingerprint(
            "stock-analysis", "b" * 64, ["run", "000001"], "readiness_validation"
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)

    def test_atomic_write_has_verified_readback_and_no_temporary_residue(self) -> None:
        self.assertIsNotNone(self.production)
        if self.production is None:
            return
        CACHE_TEMP.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=CACHE_TEMP) as temporary:
            target = Path(temporary) / "atomic.json"
            artifact = self.production.atomic_write_text(target, '{"ok":true}\n')
            self.assertEqual(target.read_text(encoding="utf-8"), '{"ok":true}\n')
            self.assertEqual(artifact["sha256"], self.production.sha256_file(target))
            self.assertEqual(list(target.parent.glob(f".{target.name}.*.tmp")), [])

    def test_failure_classification_is_total(self) -> None:
        self.assertIsNotNone(self.production)
        if self.production is None:
            return
        cases = {
            (0, False, False): "NONE",
            (124, True, False): "TIMEOUT",
            (122, False, True): "RESOURCE_LIMIT",
            (126, False, False): "SAFETY_VIOLATION",
            (125, False, False): "RUNTIME_ERROR",
            (2, False, False): "BUSINESS_REJECTED",
        }
        for arguments, expected in cases.items():
            with self.subTest(arguments=arguments):
                self.assertEqual(
                    self.production.classify_failure(*arguments),
                    expected,
                )

    def test_production_auditor_reports_every_skill_clean(self) -> None:
        self.assertTrue(PRODUCTION_AUDITOR.is_file())
        if not PRODUCTION_AUDITOR.is_file():
            return
        completed = subprocess.run(
            [sys.executable, str(PRODUCTION_AUDITOR)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "CLEAN_PASS")
        self.assertEqual(payload["catalog_count"], 53)
        self.assertEqual(payload["contract_count"], 53)
        self.assertEqual(payload["compliant_count"], 53)
        self.assertEqual(payload["missing_count"], 0)
        self.assertEqual(payload["drift_count"], 0)
        self.assertEqual(payload["passed_control_count"], payload["total_control_count"])
        for row in payload["skills"]:
            with self.subTest(skill_id=row["skill_id"]):
                self.assertEqual(row["passed_control_count"], row["control_count"])
                self.assertTrue(all(row["controls"].values()))
        self.assertEqual(payload["errors"], [])


if __name__ == "__main__":
    unittest.main()
