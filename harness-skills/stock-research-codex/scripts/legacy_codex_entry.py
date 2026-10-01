#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import py_compile
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "scripts" / "run_stock_research_codex.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="stock-research-codex business dispatcher")
    parser.add_argument("command", choices=("info", "selftest", "run"), nargs="?", default="info")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args()

    if parsed.command == "info":
        print(json.dumps({
            "skill": "stock-research-codex",
            "primary": str(PRIMARY),
            "runtime": "Codex",
        }, ensure_ascii=False, indent=2))
        return 0

    if parsed.command == "selftest":
        errors: list[str] = []
        if not PRIMARY.is_file():
            errors.append(f"primary_missing:{PRIMARY}")
        else:
            try:
                py_compile.compile(str(PRIMARY), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"compile:{exc.msg}")
        print(json.dumps({
            "status": "PASS" if not errors else "FAIL",
            "skill": "stock-research-codex",
            "primary": str(PRIMARY),
            "errors": errors,
        }, ensure_ascii=False, indent=2))
        return 0 if not errors else 2

    extra = parsed.args[1:] if parsed.args and parsed.args[0] == "--" else parsed.args
    return subprocess.run(
        [sys.executable, str(PRIMARY), *extra],
        cwd=str(ROOT),
    ).returncode


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
