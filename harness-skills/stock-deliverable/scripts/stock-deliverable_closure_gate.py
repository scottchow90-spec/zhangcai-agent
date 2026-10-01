#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import sys
import os
from pathlib import Path
RUNTIME_HOME = Path(os.environ.get("ONESTOCK_STOCK_RUNTIME_HOME", "")).resolve() if os.environ.get("ONESTOCK_STOCK_RUNTIME_HOME", "").strip() else Path(__file__).resolve().parents[3]
RUNTIME = RUNTIME_HOME / "scripts"
sys.path.insert(0, str(RUNTIME)) if str(RUNTIME) not in sys.path else None
from stock_closure_gate import check
if __name__ == "__main__":
    raise SystemExit(check("stock-deliverable"))
