#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import runpy
import os
import sys
from pathlib import Path

TARGET = Path(os.environ.get("TDX_HUB_PATH", ""))
if not TARGET:
    for _parent in Path(__file__).resolve().parents:
        _candidate = _parent / "tdx-local-hub" / "scripts" / "tdx_hub.py"
        if _candidate.exists():
            TARGET = _candidate
            break
    else:
        TARGET = Path(__file__).resolve().parents[2] / "tdx-local-hub" / "scripts" / "tdx_hub.py"


def main() -> int:
    if not TARGET.exists():
        print({"ok": False, "error": f"canonical tdx_hub missing: {TARGET}"}, file=sys.stderr)
        return 2
    sys.argv[0] = str(TARGET)
    runpy.run_path(str(TARGET), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
