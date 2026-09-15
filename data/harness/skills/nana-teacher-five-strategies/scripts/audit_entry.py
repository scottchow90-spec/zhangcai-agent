#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import subprocess, sys
from pathlib import Path
if __name__ == "__main__":
    home = Path(__file__).resolve().parents[3]
    adapter = home / "scripts" / "stock_custom_audit_adapter.py"
    raise SystemExit(subprocess.run([sys.executable, str(adapter), '--skill', 'nana-teacher-five-strategies', *sys.argv[1:]]).returncode)
