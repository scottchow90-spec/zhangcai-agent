#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "scripts" / "monitor_workflow.py"
RESULT_VERIFIER = ROOT / "scripts" / "verify_result.py"
INSTALL_VERIFIER = ROOT / "scripts" / "verify_installation.py"
ATTESTER = ROOT / "scripts" / "attest_stock_execution.py"
SUPPORT_ENTRY = Path.home() / ".codex" / "skills" / "support-pressure-analysis-system" / "scripts" / "codex_entry.py"
DISPLAY_NAME = "持仓股监控技能"


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def info() -> int:
    emit(
        {
            "skill": "a-share-intraday-position-monitor",
            "display_name": DISPLAY_NAME,
            "runtime": "Codex",
            "entry": str(Path(__file__).resolve()),
            "workflow": str(WORKFLOW),
            "dependency": str(SUPPORT_ENTRY),
            "capability": "fresh one-shot intraday holding-monitor plan",
            "continuous_daemon": False,
            "automatic_ordering": False,
        }
    )
    return 0


def selftest() -> int:
    required = [ROOT / "SKILL.md", ROOT / "agents" / "openai.yaml", WORKFLOW, RESULT_VERIFIER, INSTALL_VERIFIER, ATTESTER, ROOT / "references" / "methodology.md", SUPPORT_ENTRY]
    errors: list[str] = []
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing_or_empty:{path}")
    for script in (Path(__file__).resolve(), WORKFLOW, RESULT_VERIFIER, INSTALL_VERIFIER, ATTESTER):
        try:
            py_compile.compile(str(script), doraise=True)
        except Exception as exc:
            errors.append(f"compile_failed:{script}:{exc}")
    support_info: dict = {}
    if SUPPORT_ENTRY.is_file():
        completed = subprocess.run(
            [sys.executable, str(SUPPORT_ENTRY), "info"],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        if completed.returncode != 0:
            errors.append(f"support_entry_info_failed:{completed.stderr[-300:]}")
        else:
            try:
                support_info = json.loads(completed.stdout)
            except json.JSONDecodeError as exc:
                errors.append(f"support_entry_info_invalid_json:{exc}")
    if not errors:
        skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
        agent_text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8-sig")
        if "# 持仓股监控技能" not in skill_text:
            errors.append("display_heading_missing")
        if 'display_name: "持仓股监控技能"' not in agent_text:
            errors.append("ui_display_name_missing")
    if not errors:
        completed = subprocess.run(
            [sys.executable, str(WORKFLOW), "--selftest"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        if completed.returncode != 0 or '"status": "CLEAN_PASS"' not in completed.stdout:
            errors.append(f"workflow_selftest_failed:{completed.stdout[-400:]}:{completed.stderr[-300:]}")
    status = "CLEAN_PASS" if not errors else "BLOCKED"
    emit(
        {
            "skill": "a-share-intraday-position-monitor",
            "status": status,
            "errors": errors,
            "support_skill": support_info.get("skill"),
            "support_runtime": support_info.get("runtime"),
            "continuous_daemon": False,
            "automatic_ordering": False,
        }
    )
    return 0 if not errors else 2


def run(extra: list[str]) -> int:
    if extra[:1] == ["--"]:
        extra = extra[1:]
    env = {
        **os.environ,
        "PYTHONUTF8": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "CODEX_STOCK_TASK_CWD": os.getcwd(),
    }
    return subprocess.run([sys.executable, str(WORKFLOW), *extra], cwd=str(ROOT), env=env).returncode


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print("usage: codex_entry.py {info|selftest|run} [-- workflow arguments]")
        return 0
    command = sys.argv[1]
    if command == "info":
        return info()
    if command == "selftest":
        return selftest()
    if command == "run":
        return run(sys.argv[2:])
    emit({"status": "BLOCKED", "error": f"unknown_command:{command}"})
    return 2


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
