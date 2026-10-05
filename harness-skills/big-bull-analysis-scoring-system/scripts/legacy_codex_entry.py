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

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_data_root, resolve_tdx_root

from scoring_mode_gate import (
    CANONICAL_SCORING_MODE,
    LEGACY_COMPATIBILITY_FLAG,
    normalize_business_args,
)


SKILL = "big-bull-analysis-scoring-system"
ROOT = Path(__file__).resolve().parents[1]
TDX_ROOT = resolve_tdx_root()
PRIMARY_REL = "scripts/analysis_scoring.py"
DEFAULT_ARGS = [
    "--output-dir",
    str(resolve_data_root() / "reports" / "skills" / "big-bull-analysis-scoring-system" / "latest"),
    CANONICAL_SCORING_MODE,
]


def selftest() -> int:
    errors: list[str] = []
    for script in sorted((ROOT / "scripts").glob("*.py")):
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"compile:{script.name}:{exc.msg}")
    for required in (
        ROOT / "SKILL.md",
        ROOT / "references" / "workflow.md",
        ROOT / "scripts" / "daniuxian_analysis.py",
        ROOT / "scripts" / "big_bull_scoring.py",
        ROOT / "scripts" / "analysis_scoring.py",
        TDX_ROOT,
    ):
        if not required.exists():
            errors.append(f"missing:{required}")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "skill": SKILL,
        "primary": PRIMARY_REL,
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def run_primary(extra: list[str]) -> int:
    primary = ROOT / PRIMARY_REL
    args = extra if extra else list(DEFAULT_ARGS)
    business_offset = 2 if args[:1] == ["--output-dir"] else 0
    business_args = args[business_offset:]
    normalized_business_args = normalize_business_args(business_args)
    args = [*args[:business_offset], *normalized_business_args]
    environment = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }
    if LEGACY_COMPATIBILITY_FLAG in business_args:
        environment["CODEX_BIG_BULL_LEGACY_COMPAT_AUTHORIZED"] = "1"
    else:
        environment.pop("CODEX_BIG_BULL_LEGACY_COMPAT_AUTHORIZED", None)
    return subprocess.run(
        [sys.executable, str(primary), *args],
        cwd=str(ROOT),
        env=environment,
    ).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("info", "selftest", "run"), nargs="?", default="info")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args()
    if parsed.command == "info":
        print(json.dumps({
            "skill": SKILL,
            "primary": PRIMARY_REL,
            "modes": [
                "analyze",
                "backtest-composite",
                "sync-composite-state",
                "score-composite",
                "score-research-composite",
                "verify-cross-board-consistency",
                "refresh-composite-poster",
                "structure-poster",
                "score-board (explicit legacy compatibility only)",
            ],
            "default_args": DEFAULT_ARGS,
        }, ensure_ascii=False, indent=2))
        return 0
    if parsed.command == "selftest":
        return selftest()
    extra = parsed.args[1:] if parsed.args and parsed.args[0] == "--" else parsed.args
    return run_primary(extra)


if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
