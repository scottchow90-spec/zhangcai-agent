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
from typing import Any

_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_app_root, resolve_data_root

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"
REPORTS = resolve_data_root() / "reports" / "skills" / "baimao-score-system"
WORKSPACE = resolve_app_root()
WORKFLOW_LOCK = WORKSPACE / "hooks" / "skill_workflow_lock.py"
SUBSTANTIVE_GATE = WORKSPACE / "hooks" / "stock_workflow_substantive_gate.py"
LOCKED_EXECUTION_SCRIPT = SCRIPTS / "baimao-score-system_closure_gate.py"
PYTHON_EXE = sys.executable


def run_capture(cmd: list[str], timeout: int = 180) -> dict[str, Any]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(SKILL_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
        )
        return {
            "ok": result.returncode == 0,
            "exit": result.returncode,
            "cmd": cmd,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "stdout_tail": result.stdout[-1800:],
            "stderr_tail": result.stderr[-900:],
        }
    except Exception as exc:
        return {"ok": False, "cmd": cmd, "error": f"{type(exc).__name__}: {exc}"}


def parse_json(text: str) -> Any:
    clean = (text or "").lstrip("\ufeff").strip()
    if not clean:
        raise ValueError("empty json")
    starts = [i for i in [clean.find("{"), clean.find("[")] if i >= 0]
    if starts:
        clean = clean[min(starts):]
    return json.loads(clean)


def cmd_info(_: argparse.Namespace) -> int:
    payload = {
        "skill": "baimao-score-system",
        "display_name": "白猫老师评分体系",
        "skill_dir": str(SKILL_DIR),
        "entry": str(Path(__file__).resolve()),
        "workflow": str(SKILL_DIR / "references" / "workflow.md"),
        "reports": str(REPORTS),
        "capabilities": [
            "six_formula_technical_score",
            "financial_quality",
            "cashflow",
            "announcement_event",
            "industry_business",
            "liquidity",
            "risk_and_recheck_conditions",
            "docx_report",
            "closure_acceptance",
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    return subprocess.run([PYTHON_EXE, str(SCRIPTS / "baimao_stock_score.py"), "score", args.symbol], cwd=str(SKILL_DIR)).returncode


def cmd_analyze(args: argparse.Namespace) -> int:
    return subprocess.run(
        [PYTHON_EXE, str(SCRIPTS / "baimao_comprehensive_analysis.py"), "analyze", args.symbol],
        cwd=str(SKILL_DIR),
    ).returncode


def cmd_report(args: argparse.Namespace) -> int:
    return subprocess.run(
        [PYTHON_EXE, str(SCRIPTS / "baimao_comprehensive_analysis.py"), "report", args.symbol],
        cwd=str(SKILL_DIR),
    ).returncode


def cmd_acceptance(_: argparse.Namespace) -> int:
    return subprocess.run([PYTHON_EXE, str(SCRIPTS / "baimao_score_acceptance.py")], cwd=str(SKILL_DIR)).returncode


def cmd_auto(_: argparse.Namespace) -> int:
    steps = []
    for name, cmd in [
        ("skill_workflow_lock", [PYTHON_EXE, str(WORKFLOW_LOCK), "check", "--skill", SKILL_DIR.name]),
        ("stock_workflow_substantive_gate", [PYTHON_EXE, str(SUBSTANTIVE_GATE), "check", "--skill", SKILL_DIR.name]),
        ("info", [PYTHON_EXE, str(Path(__file__).resolve()), "info"]),
        ("locked_execution", [PYTHON_EXE, str(LOCKED_EXECUTION_SCRIPT)]),
    ]:
        result = run_capture(cmd, timeout=300)
        result["step"] = name
        steps.append(result)
    ok = all(step.get("ok") for step in steps)
    payload = {
        "skill": "baimao-score-system",
        "display_name": "白猫老师评分体系",
        "mode": "auto",
        "executed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": "CLEAN_PASS" if ok else "BLOCKED",
        "all_ok": ok,
        "steps": steps,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="白猫老师评分体系综合个股分析入口")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("info")
    score = sub.add_parser("score")
    score.add_argument("symbol")
    analyze = sub.add_parser("analyze")
    analyze.add_argument("symbol")
    report = sub.add_parser("report")
    report.add_argument("symbol")
    sub.add_parser("acceptance")
    sub.add_parser("auto")
    return parser


def main() -> int:
    parser = build_parser()
    if len(sys.argv) == 1:
        return cmd_auto(argparse.Namespace())
    args = parser.parse_args()
    if args.cmd == "info":
        return cmd_info(args)
    if args.cmd == "score":
        return cmd_score(args)
    if args.cmd == "analyze":
        return cmd_analyze(args)
    if args.cmd == "report":
        return cmd_report(args)
    if args.cmd == "acceptance":
        return cmd_acceptance(args)
    if args.cmd == "auto":
        return cmd_auto(args)
    parser.print_help()
    return 0


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
