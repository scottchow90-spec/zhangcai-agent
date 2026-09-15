#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import json, subprocess, sys
from pathlib import Path


def main() -> int:
    scripts = Path(__file__).resolve().parent
    target = scripts / ("stock_watchlist.py" if len(sys.argv) > 1 else "test_stock_watchlist.py")
    proc = subprocess.run([sys.executable, str(target), *sys.argv[1:]], cwd=str(scripts.parent))
    if len(sys.argv) == 1:
        print(json.dumps({"status": "CLEAN_PASS" if proc.returncode == 0 else "BLOCKED", "mode": "OFFLINE_INTEGRATION_SUITE", "tests": 10}, ensure_ascii=False))
    return proc.returncode


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
