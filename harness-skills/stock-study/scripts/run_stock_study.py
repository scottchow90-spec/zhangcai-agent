#!/usr/bin/env python3
"""Private business delegate for the stock-study fixed entry."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import subprocess
import sys
from pathlib import Path


def main() -> int:
    engine = Path.home() / ".codex" / "scripts" / "stock_audit_business.py"
    return subprocess.run(
        [sys.executable, str(engine), "--skill", "stock-study", *sys.argv[1:]],
        check=False,
    ).returncode


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
