#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
RUNTIME = Path.home() / ".codex" / "scripts"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
from stock_closure_gate import check
if __name__ == "__main__":
    raise SystemExit(check('golden-ignition'))
