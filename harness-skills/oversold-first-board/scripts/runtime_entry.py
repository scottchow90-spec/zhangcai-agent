#!/usr/bin/env python3
"""3003-local strategy runtime entry for DeepSeek Harness/web execution."""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_ROOT = Path(os.environ.get("ZHANGCAI_APP_ROOT", Path(__file__).resolve().parents[3]))
SCRIPTS_ROOT = APP_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from stock_canonical_runtime import facade_main


if __name__ == "__main__":
    raise SystemExit(facade_main(__file__))

