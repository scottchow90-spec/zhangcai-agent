#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import ast
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
SKILL_NAME_DISPLAY = "hard-gate"
ENTRY_SCRIPT_NAME = "hard-gate.py"
LOCKED_PRODUCTION_SCRIPT = "hard-gate_closure_gate.py"


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
        "locked_execution": str(SCRIPTS_DIR / LOCKED_PRODUCTION_SCRIPT),
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
    target = (SCRIPTS_DIR / script).resolve()
    try:
        target.relative_to(SCRIPTS_DIR.resolve())
    except ValueError:
        print("run: blocked script path outside the skill scripts directory", file=sys.stderr)
        return 2
    allowed = {
        "block.py",
        "hard-gate_closure_gate.py",
        "preflight.py",
        "scan_all_data.py",
    }
    if target.name not in allowed or not target.is_file():
        print(f"run: script not found: {target}", file=sys.stderr)
        return 2
    return subprocess.run([PYTHON_EXE, str(target)] + (args.args or []), cwd=str(SKILL_DIR)).returncode


def cmd_selftest(_: argparse.Namespace) -> int:
    steps = []
    required = [
        SCRIPTS_DIR / "preflight.py",
        SCRIPTS_DIR / LOCKED_PRODUCTION_SCRIPT,
    ]
    for path in required:
        errors = []
        if not path.is_file():
            errors.append(f"missing:{path}")
        else:
            try:
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            except (OSError, SyntaxError, UnicodeError) as exc:
                errors.append(f"{type(exc).__name__}:{exc}")
        steps.append({
            "step": f"source:{path.name}",
            "ok": not errors,
            "errors": errors,
        })
    ok = all(s.get("ok") for s in steps)
    print(json.dumps({
        "skill": SKILL_DIR.name,
        "mode": "selftest",
        "status": "CLEAN_PASS" if ok else "BLOCKED",
        "steps": steps,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1



def infer_auto_status(ok, steps):
    if ok:
        return "CLEAN_PASS"
    text = json.dumps(steps, ensure_ascii=False)
    blocked_markers = ("BLOCKED", "BLOCKED_BY_", "DATA_STALE", "DATA_BLOCKED", "AUDIT_BLOCKED", "TIMEOUT")
    return "BLOCKED" if any(marker in text for marker in blocked_markers) else "FAILED"

def cmd_auto(_: argparse.Namespace) -> int:
    steps = []
    selftest = run_capture([PYTHON_EXE, str(Path(__file__).resolve()), "selftest"], timeout=180)
    selftest["step"] = "selftest"
    stdout = selftest.get("stdout", "") or selftest.get("stdout_tail", "")
    selftest["ok"] = selftest.get("ok") and ('"status": "CLEAN_PASS"' in stdout or '"all_ok": true' in stdout)
    steps.append(selftest)

    target = SCRIPTS_DIR / LOCKED_PRODUCTION_SCRIPT
    if not target.exists():
        steps.append({"step": "locked_execution", "ok": False, "error": f"missing {target}"})
    else:
        r = run_capture([PYTHON_EXE, str(target)], timeout=240)
        r["step"] = "locked_execution"
        r["script"] = target.name
        steps.append(r)

    ok = all(s.get("ok") for s in steps)
    print(json.dumps({
        "skill": SKILL_DIR.name,
        "mode": "auto",
        "entry_script": str(Path(__file__).resolve()),
        "locked_execution": str(target),
        "executed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": infer_auto_status(ok, steps),
        "all_ok": ok,
        "steps": steps,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


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


if __name__ == "__main__" and os.environ.get(
    "ONESTOCK_STOCK_CANONICAL_CHILD"
) != "1":
    print(
        "canonical_stock_legacy_entry_direct_execution_blocked",
        file=sys.stderr,
    )
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
