from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "scripts" / "canonical_business_adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location(
        "tdx_local_hub_canonical_business_adapter_test",
        ADAPTER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CanonicalBusinessArgsTests(unittest.TestCase):
    def test_news_arguments_reach_legacy_entry(self) -> None:
        adapter = load_adapter()
        command = adapter.business_command(
            ROOT / "reports" / "test-run",
            ["news", "--limit", "5"],
        )
        self.assertEqual(
            command,
            [
                sys.executable,
                str(ROOT / "scripts" / "legacy_codex_entry.py"),
                "run",
                "--",
                "news",
                "--limit",
                "5",
            ],
        )


if __name__ == "__main__":
    unittest.main()
