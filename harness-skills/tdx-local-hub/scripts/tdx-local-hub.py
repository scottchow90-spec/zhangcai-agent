#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

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

APP_ROOT = Path(__file__).resolve().parents[3]
APP_SCRIPTS = APP_ROOT / "scripts"
if str(APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(APP_SCRIPTS))
from tdx_path_config import resolve_data_root

WORKSPACE = resolve_data_root()
SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
LOCK = APP_ROOT / "hooks" / "skill_workflow_lock.py"
SUBSTANTIVE_GATE = APP_ROOT / "hooks" / "stock_workflow_substantive_gate.py"
PYTHON_EXE = sys.executable
SKILL_NAME_DISPLAY = "tdx-local-hub"
ENTRY_SCRIPT_NAME = "tdx-local-hub.py"
LOCKED_PRODUCTION_SCRIPT = "tdx-local-hub_closure_gate.py"
PRIMARY_BUSINESS_SCRIPT = "tdx_hub.py"


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
    target = SCRIPTS_DIR / script
    if not target.exists():
        print(f"run: script not found: {target}", file=sys.stderr)
        return 2
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.run([PYTHON_EXE, str(target)] + (args.args or []), cwd=str(SKILL_DIR), env=env).returncode


def cmd_selftest(_: argparse.Namespace) -> int:
    steps = []
    if LOCK.exists():
        r = run_capture([PYTHON_EXE, str(LOCK), "check", "--skill", SKILL_DIR.name], timeout=120)
        r["step"] = "skill_workflow_lock_check"
        stdout = r.get("stdout", "") or r.get("stdout_tail", "")
        r["ok"] = r.get("ok") and ('"status": "CLEAN_PASS"' in stdout or '"blocks": []' in stdout)
        steps.append(r)
    else:
        steps.append({"step": "skill_workflow_lock_check", "ok": False, "error": f"missing {LOCK}"})
    if SUBSTANTIVE_GATE.exists():
        r = run_capture([PYTHON_EXE, str(SUBSTANTIVE_GATE), "check", "--skill", SKILL_DIR.name], timeout=120)
        r["step"] = "stock_workflow_substantive_gate"
        stdout = r.get("stdout", "") or r.get("stdout_tail", "")
        r["ok"] = r.get("ok") and ('"status": "CLEAN_PASS"' in stdout or '"blocks": []' in stdout)
        steps.append(r)
    else:
        steps.append({"step": "stock_workflow_substantive_gate", "ok": False, "error": f"missing {SUBSTANTIVE_GATE}"})
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

    # Step 3: Run primary business script (try --help first to verify invokable)
    target = SCRIPTS_DIR / PRIMARY_BUSINESS_SCRIPT
    if not target.exists():
        steps.append({"step": "primary_business", "ok": False, "error": f"missing {target}"})
    else:
        # First try --help to verify the script is invokable
        help_r = run_capture([PYTHON_EXE, str(target), "--help"], timeout=60)
        if help_r.get("ok") and ("usage:" in (help_r.get("stdout","") + help_r.get("stdout_tail","")) or "options:" in (help_r.get("stdout","") + help_r.get("stdout_tail",""))):
            steps.append({"step": "primary_business_help", "ok": True, "script": target.name, "stdout_tail": help_r.get("stdout_tail", help_r.get("stdout",""))[-400:], "note": "script accepts --help, invokable; needs args for actual run"})
            # Now try running without args - report as best-effort
            r = run_capture([PYTHON_EXE, str(target)], timeout=600)
            r["step"] = "primary_business"
            r["script"] = target.name
            r["note"] = "script ran with no args; may have failed but the chain is invokable"
            steps.append(r)
        else:
            # Help failed or no help support; try running no-args directly
            r = run_capture([PYTHON_EXE, str(target)], timeout=600)
            r["step"] = "primary_business"
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


if __name__ == "__main__":
    raise SystemExit(main())
