from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import subprocess
import sys
import unittest
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[2]
ENTRY = (
    SKILLS_ROOT
    / "convertible-bond-screening-strategy"
    / "scripts"
    / "codex_entry.py"
)


class ConvertibleBondSelftestContractTests(unittest.TestCase):
    def test_stdout_is_one_runtime_bound_canonical_json_object(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ENTRY), "selftest"],
            cwd=ENTRY.parent.parent,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["runtime"], "stock-canonical-runtime-v3")
        self.assertEqual(
            payload["skill_id"],
            "convertible-bond-screening-strategy",
        )
        self.assertEqual(payload["status"], "CLEAN_PASS")
        self.assertEqual(payload["errors"], [])
        self.assertRegex(payload["contract_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(payload["semantic_assertions"])


if __name__ == "__main__":
    unittest.main()
