#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse, json, os, py_compile, subprocess, sys
from pathlib import Path

SKILL = "a-share-longhubang-analysis"
ROOT = Path(__file__).resolve().parents[1]
PRIMARY_REL = "scripts/longhubang_workflow.py"
DIRECT_GUARD = "canonical_stock_legacy_entry_direct_execution_blocked"

def selftest() -> int:
    errors: list[str] = []
    for script in sorted((ROOT / "scripts").glob("*.py")):
        try: py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc: errors.append(f"compile:{script.name}:{exc.msg}")
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "skill": SKILL, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("info", "selftest", "run"), nargs="?", default="info")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args()
    if parsed.command == "info":
        print(json.dumps({"skill": SKILL, "primary": PRIMARY_REL}, ensure_ascii=False)); return 0
    if parsed.command == "selftest": return selftest()
    extra = parsed.args[1:] if parsed.args and parsed.args[0] == "--" else parsed.args
    return subprocess.run([sys.executable, str(ROOT / PRIMARY_REL), *extra], cwd=str(ROOT)).returncode

if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print(DIRECT_GUARD, file=sys.stderr); raise SystemExit(2)
if __name__ == "__main__": raise SystemExit(main())
