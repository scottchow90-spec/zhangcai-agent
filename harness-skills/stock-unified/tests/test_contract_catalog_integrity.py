from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGGREGATE_SCRIPT = ROOT / "scripts" / "stock-unified.py"
SYNC_SCRIPT = ROOT / "scripts" / "sync_stock_execution_contracts.py"
SPEC = importlib.util.spec_from_file_location(
    "stock_unified_contract_catalog_test",
    AGGREGATE_SCRIPT,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ContractCatalogIntegrityTests(unittest.TestCase):
    def test_contract_paths_use_physical_canonical_home(self) -> None:
        contracts_path = ROOT / "references" / "stock_execution_contracts.json"
        payload = json.loads(contracts_path.read_text(encoding="utf-8"))
        canonical_home = ROOT.parents[1].resolve()
        expected_catalog = (
            canonical_home
            / "skills"
            / "stock-unified"
            / "references"
            / "stock_skill_ids.json"
        )
        self.assertEqual(Path(payload["catalog"]), expected_catalog)

        for contract in payload["contracts"]:
            with self.subTest(skill_id=contract["skill_id"]):
                for binding in contract["business_bindings"]:
                    raw_path = Path(binding["path"])
                    self.assertEqual(raw_path, raw_path.resolve())
                    self.assertTrue(raw_path.is_relative_to(canonical_home))
                for source_policy in contract.get(
                    "supplemental_sources", {}
                ).values():
                    client = source_policy.get("client")
                    if client:
                        raw_client = Path(client)
                        self.assertEqual(raw_client, raw_client.resolve())
                        self.assertTrue(raw_client.is_relative_to(canonical_home))

    def test_every_contract_has_one_exclusive_workflow_owner(self) -> None:
        payload = json.loads(
            (ROOT / "references" / "stock_execution_contracts.json").read_text(
                encoding="utf-8"
            )
        )
        for row in payload["contracts"]:
            with self.subTest(skill_id=row["skill_id"]):
                identity = row.get("workflow_identity")
                self.assertIsInstance(identity, dict)
                self.assertEqual(identity["owner_skill_id"], row["skill_id"])
                self.assertTrue(identity["exclusive_owner"])
                self.assertEqual(
                    identity["route_authority"],
                    "canonical_stock_skill_routing_catalog",
                )

    def test_lianban_date_mode_is_explicit_and_calendar_safe(self) -> None:
        payload = json.loads(
            (ROOT / "references" / "stock_execution_contracts.json").read_text(
                encoding="utf-8"
            )
        )
        for contract in payload["contracts"]:
            source = contract.get("supplemental_sources", {}).get("lianban_daily")
            if not isinstance(source, dict) or source.get("enabled") is not True:
                continue
            with self.subTest(skill_id=contract["skill_id"]):
                self.assertIn(source.get("date_mode"), {"exact", "latest_available"})
                if isinstance(source.get("target_date_resolver"), dict):
                    self.assertEqual(source["date_mode"], "exact")
                else:
                    self.assertEqual(source["date_mode"], "latest_available")

    def test_contract_hash_catalog_matches_all_bound_files(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT), "--check"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_consistency_accepts_only_the_declared_special_facade(self) -> None:
        payload = MODULE.consistency_payload()
        self.assertEqual(payload["status"], "CLEAN_PASS", payload["errors"])
        self.assertEqual(
            payload["special_facade_count"],
            len(MODULE.SPECIAL_FACADE_SKILLS),
        )

    def test_every_contract_declares_non_bypass_workflow_guard(self) -> None:
        contracts_path = ROOT / "references" / "stock_execution_contracts.json"
        payload = json.loads(contracts_path.read_text(encoding="utf-8"))
        for contract in payload["contracts"]:
            with self.subTest(skill_id=contract["skill_id"]):
                guard = contract.get("workflow_guard")
                self.assertIsInstance(guard, dict)
                self.assertEqual(
                    guard.get("direct_legacy_execution"),
                    "blocked",
                )
                self.assertIsInstance(
                    guard.get("requires_explicit_business_args"),
                    bool,
                )
                forbidden_actions = guard.get("forbidden_business_actions")
                self.assertEqual(
                    forbidden_actions[:3],
                    ["info", "inspect", "selftest"],
                )
                self.assertEqual(len(forbidden_actions), len(set(forbidden_actions)))
                self.assertIsInstance(guard.get("required_bindings"), list)

                bound_paths = {
                    Path(binding["path"]).resolve()
                    for binding in contract["business_bindings"]
                }
                skill_root = ROOT.parent / contract["skill_id"]
                self.assertIn((skill_root / "SKILL.md").resolve(), bound_paths)
                self.assertIn(
                    (skill_root / "references" / "workflow.md").resolve(),
                    bound_paths,
                )

    def test_every_contract_declares_fail_closed_delivery_policy(self) -> None:
        contracts_path = ROOT / "references" / "stock_execution_contracts.json"
        payload = json.loads(contracts_path.read_text(encoding="utf-8"))
        expected = {
            "authorization_required": True,
            "allow_receipt_bound_artifact": True,
            "allow_manifest_bound_artifact": True,
            "require_artifact_sha256": True,
            "require_clean_manifest_validation": True,
            "formatted_artifact_requires_template_binding": True,
            "formatted_artifact_requires_validator_binding": True,
        }
        for contract in payload["contracts"]:
            with self.subTest(skill_id=contract["skill_id"]):
                self.assertEqual(contract.get("delivery_policy"), expected)

    def test_canonical_runtime_defines_current_authorization_semantics(self) -> None:
        runtime = ROOT.parents[1] / "scripts" / "stock_canonical_runtime.py"
        source = runtime.read_text(encoding="utf-8-sig", errors="replace")
        self.assertIn("authorize --receipt", source)
        self.assertIn('"match_type": "generic_default"', source)
        self.assertIn("artifact_not_receipt_or_manifest_bound", source)
        self.assertIn("manifest_validation_not_clean", source)

    def test_all_legacy_entries_block_direct_execution(self) -> None:
        catalog_path = ROOT / "references" / "stock_skill_ids.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8-sig"))
        marker = "canonical_stock_legacy_entry_direct_execution_blocked"
        for skill_id in catalog["skills"]:
            legacy = ROOT.parent / skill_id / "scripts" / "legacy_codex_entry.py"
            with self.subTest(skill_id=skill_id):
                self.assertIn(
                    marker,
                    legacy.read_text(encoding="utf-8-sig", errors="replace"),
                )


if __name__ == "__main__":
    unittest.main()
