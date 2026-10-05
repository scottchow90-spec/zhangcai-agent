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
import os
import py_compile
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIMARY_REL = "scripts/audit_risk_scan.py"
PRIMARY = ROOT / PRIMARY_REL
REQUIRED = (
    PRIMARY,
    ROOT / "scripts" / "a_share_risk_scan.py",
    ROOT / "scripts" / "risk_warning_overlay.py",
    ROOT / "scripts" / "validate_risk_run.py",
)


def selftest() -> int:
    errors: list[str] = []
    for path in REQUIRED:
        if not path.is_file():
            errors.append(f"missing:{path}")
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"compile:{path.name}:{exc.msg}")
    print(
        json.dumps(
            {
                "status": "CLEAN_PASS" if not errors else "BLOCKED",
                "name": "风险排雷技能",
                "primary": PRIMARY_REL,
                "errors": errors,
            },
            ensure_ascii=False,
        )
    )
    return 0 if not errors else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("info", "selftest", "run"),
        nargs="?",
        default="info",
    )
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args()
    if parsed.command == "info":
        print(
            json.dumps(
                {"name": "风险排雷技能", "primary": PRIMARY_REL},
                ensure_ascii=False,
            )
        )
        return 0
    if parsed.command == "selftest":
        return selftest()
    extra = (
        parsed.args[1:]
        if parsed.args and parsed.args[0] == "--"
        else parsed.args
    )
    return subprocess.run(
        [sys.executable, str(PRIMARY), *extra],
        cwd=str(ROOT),
    ).returncode


if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
