"""Automatically load the TongDaXin lifecycle guard for canonical stock runs."""
from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def _install_guard() -> None:
    bootstrap_dir = Path(__file__).resolve().parent
    if str(bootstrap_dir) not in sys.path:
        sys.path.insert(0, str(bootstrap_dir))
    from tdx_process_guard import install_tdx_import_guard

    install_tdx_import_guard()


def _run_guarded_target(arguments: list[str]) -> None:
    if not arguments:
        raise SystemExit("tdx_guarded_python_target_missing")
    target = Path(arguments[0]).resolve()
    if target.suffix.casefold() != ".py" or not target.is_file():
        raise SystemExit(f"tdx_guarded_python_target_invalid:{target}")
    _install_guard()
    if str(target.parent) not in sys.path:
        sys.path.insert(0, str(target.parent))
    sys.argv = [str(target), *arguments[1:]]
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    _run_guarded_target(sys.argv[1:])
elif os.environ.get("CODEX_TDX_PROCESS_GUARD") == "1":
    _install_guard()
