#!/usr/bin/env python3
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
from pathlib import Path
import sys

RUNTIME = Path(__file__).resolve().parents[5] / "scripts" / "stock_canonical_runtime.py"
sys.path.insert(0, str(RUNTIME.parent))

from stock_canonical_runtime import facade_main

if __name__ == "__main__":
    raise SystemExit(facade_main(__file__))
