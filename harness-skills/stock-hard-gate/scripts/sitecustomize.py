"""Load the canonical TongDaXin lifecycle guard for this recovered skill."""
from __future__ import annotations

import os
import sys
from pathlib import Path

BOOTSTRAP = (
    Path(__file__).resolve().parents[3]
    / "scripts"
    / "stock_runtime_bootstrap"
)
if str(BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(BOOTSTRAP))

if os.environ.get("CODEX_TDX_PROCESS_GUARD") == "1":
    from tdx_process_guard import install_tdx_import_guard

    install_tdx_import_guard()
