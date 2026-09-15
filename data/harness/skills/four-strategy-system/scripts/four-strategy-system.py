#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
PYTHON_EXE = sys.executable
SKILL_NAME_DISPLAY = "four-strategy-system"
ENTRY_SCRIPT_NAME = "four-strategy-system.py"
PRIMARY_BUSINESS_SCRIPT = "run_four_strategy_smoke.py"


def run_capture(cmd: list[str], timeout: int = 120, cwd: Path | None = None) -> dict:
    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd or SKILL_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
        )
        return {
            "ok": r.returncode == 0,
            "exit": r.returncode,
            "cmd": cmd,
            "stdout": r.stdout,
            "stderr": r.stderr,
            "stdout_tail": r.stdout[-1200:],
            "stderr_tail": r.stderr[-800:],
        }
    except Exception as e:
        return {"ok": False, "cmd": cmd, "error": f"{type(e).__name__}: {e}"}


def cmd_info(_: argparse.Namespace) -> int:
    print(json.dumps({
        "skill": SKILL_DIR.name,
        "skill_dir": str(SKILL_DIR),
        "entry": str(Path(__file__).resolve()),
        "direct_execution": str(SCRIPTS_DIR / PRIMARY_BUSINESS_SCRIPT),
        "workflow": str(SKILL_DIR / "references" / "workflow.md"),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    for p in sorted(SCRIPTS_DIR.glob("*.py")):
        if p.name != "__init__.py":
            print(p.name)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    script = args.script
    if not script.endswith(".py"):
        script += ".py"
    target = SCRIPTS_DIR / script
    if not target.exists():
        print(f"run: script not found: {target}", file=sys.stderr)
        return 2
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.run([PYTHON_EXE, str(target)] + (args.args or []), cwd=str(SKILL_DIR), env=env).returncode


def cmd_selftest(_: argparse.Namespace) -> int:
    target = SCRIPTS_DIR / PRIMARY_BUSINESS_SCRIPT
    ok = target.is_file()
    print(json.dumps({
        "skill": SKILL_DIR.name,
        "mode": "selftest",
        "status": "PASS" if ok else "FAIL",
        "direct_execution": str(target),
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1



def cmd_auto(_: argparse.Namespace) -> int:
    target = SCRIPTS_DIR / PRIMARY_BUSINESS_SCRIPT
    if not target.exists():
        print(f"direct execution script not found: {target}", file=sys.stderr)
        return 2
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.run([PYTHON_EXE, str(target)], cwd=str(SKILL_DIR), env=env).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{SKILL_NAME_DISPLAY} Codex unique execution entry")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("info")
    sub.add_parser("list")
    sub.add_parser("selftest")
    sub.add_parser("auto")
    run_p = sub.add_parser("run")
    run_p.add_argument("script")
    run_p.add_argument("args", nargs=argparse.REMAINDER)
    return parser


def main() -> int:
    parser = build_parser()
    if len(sys.argv) == 1:
        return cmd_auto(None)
    args = parser.parse_args()
    if args.cmd == "info":
        return cmd_info(args)
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "selftest":
        return cmd_selftest(args)
    if args.cmd == "auto":
        return cmd_auto(args)
    if args.cmd == "run":
        return cmd_run(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
