from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "harness-skills" / "stock-unified" / "scripts"))

from stock_contract_catalog import canonical_contract_path, resolve_contract_path


class PortableContractPathTests(unittest.TestCase):
    def test_development_and_legacy_paths_become_app_relative(self) -> None:
        self.assertEqual(
            canonical_contract_path(
                ROOT / "harness-skills" / "tdx-local-hub" / "scripts" / "tdx_hub.py"
            ),
            "harness-skills/tdx-local-hub/scripts/tdx_hub.py",
        )
        self.assertEqual(
            canonical_contract_path(
                r"D:\C盘转移\日志\codex\scripts\lianban_daily_client.py"
            ),
            "scripts/lianban_daily_client.py",
        )

    def test_relative_binding_resolves_under_each_install_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zhangcai-path-root-") as temporary:
            simulated_app = Path(temporary) / "resources" / "app"
            resolved = resolve_contract_path(
                "harness-skills/tdx-local-hub/scripts/tdx_hub.py",
                app_root=simulated_app,
            )
            self.assertEqual(
                resolved,
                simulated_app.resolve()
                / "harness-skills"
                / "tdx-local-hub"
                / "scripts"
                / "tdx_hub.py",
            )

    def test_contract_catalog_contains_only_portable_binding_paths(self) -> None:
        contracts_path = (
            ROOT
            / "harness-skills"
            / "stock-unified"
            / "references"
            / "stock_execution_contracts.json"
        )
        payload = json.loads(contracts_path.read_text(encoding="utf-8"))
        for contract in payload["contracts"]:
            for binding in contract.get("business_bindings", []):
                path = binding["path"]
                self.assertEqual(path, canonical_contract_path(path))
                self.assertFalse(Path(path).is_absolute(), path)
                self.assertNotRegex(path, r"^[A-Za-z]:")
            client = contract.get("supplemental_sources", {}).get("lianban_daily", {}).get("client")
            if client:
                self.assertEqual(client, canonical_contract_path(client))


if __name__ == "__main__":
    unittest.main()
