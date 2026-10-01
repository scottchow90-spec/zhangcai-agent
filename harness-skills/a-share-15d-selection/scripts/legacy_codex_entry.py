#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIMARY_REL = "scripts/run_a_share_15d.py"
BUSINESS_ENTRY = ROOT / PRIMARY_REL


def main() -> int:
    arguments = sys.argv[1:]
    command = arguments[0] if arguments else "info"
    if command == "info":
        print(json.dumps({
            "skill_id": ROOT.name,
            "business_entry": str(BUSINESS_ENTRY),
        }, ensure_ascii=False, indent=2))
        return 0
    if command == "selftest":
        if not BUSINESS_ENTRY.is_file():
            print(f"missing_business_entry:{BUSINESS_ENTRY}", file=sys.stderr)
            return 2
        py_compile.compile(str(BUSINESS_ENTRY), doraise=True)
        return 0
    if command == "run":
        extra = arguments[2:] if len(arguments) > 1 and arguments[1] == "--" else arguments[1:]
        return subprocess.run(
            [sys.executable, str(BUSINESS_ENTRY), *extra],
            cwd=str(ROOT),
        ).returncode
    print("usage: legacy_codex_entry.py {info|selftest|run}", file=sys.stderr)
    return 2


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
