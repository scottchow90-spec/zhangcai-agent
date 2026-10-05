#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SKILL_DIR = Path(__file__).resolve().parents[1]
ENTRY = SKILL_DIR / "scripts" / "baimao-teacher-system.py"
REPORT_DIR = SKILL_DIR / "reports" / "workflow_acceptance"
PYTHON_EXE = sys.executable


def run_capture(cmd: list[str], timeout: int = 180, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(SKILL_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
            env=env,
        )
        return {
            "ok": result.returncode == 0,
            "exit": result.returncode,
            "cmd": cmd,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-1000:],
        }
    except Exception as exc:
        return {"ok": False, "cmd": cmd, "error": f"{type(exc).__name__}: {exc}"}


def parse_json(text: str) -> Any:
    clean = (text or "").lstrip("\ufeff").strip()
    if not clean:
        raise ValueError("empty json text")
    start_obj = clean.find("{")
    start_arr = clean.find("[")
    starts = [x for x in [start_obj, start_arr] if x >= 0]
    if starts:
        clean = clean[min(starts) :]
    return json.loads(clean)


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def main() -> int:
    checks: list[dict[str, Any]] = []

    verify = run_capture([PYTHON_EXE, str(ENTRY), "verify-installed"], timeout=90)
    try:
        verify_payload = parse_json(verify.get("stdout", ""))
        verify_ok = verify.get("ok") and verify_payload.get("status") == "CLEAN_PASS" and verify_payload.get("found_count") == 6
    except Exception as exc:
        verify_payload = {"parse_error": str(exc), "stdout_tail": verify.get("stdout_tail")}
        verify_ok = False
    checks.append(check("formula_installation_gate", verify_ok, verify_payload))

    score = run_capture([PYTHON_EXE, str(ENTRY), "score", "000001"], timeout=120)
    try:
        score_payload = parse_json(score.get("stdout", ""))
        modules = score_payload.get("modules", [])
        max_by_name = {m.get("name"): m.get("max_score") for m in modules}
        expected_max = {
            "平均成本线": 25,
            "白猫RSI": 15,
            "白猫渡劫": 15,
            "白猫队长": 15,
            "躲猫猫": 15,
            "黑猫白猫": 5,
            "六公式共振": 10,
        }
        duomaomao = next((m for m in modules if m.get("name") == "躲猫猫"), {})
        score_ok = (
            score.get("ok")
            and score_payload.get("status") == "CLEAN_PASS"
            and score_payload.get("ok") is True
            and sum(float(m.get("max_score", 0)) for m in modules) == 100
            and max_by_name == expected_max
            and "data_gate" in score_payload
            and "短期超跌/抄底窗口" in "；".join(duomaomao.get("facts", []))
        )
    except Exception as exc:
        score_payload = {"parse_error": str(exc), "stdout_tail": score.get("stdout_tail")}
        score_ok = False
    checks.append(check("single_stock_score_execution", score_ok, score_payload))

    report = run_capture([PYTHON_EXE, str(ENTRY), "report", "000001"], timeout=120)
    try:
        report_payload = parse_json(report.get("stdout", ""))
        json_path = Path(report_payload.get("json", ""))
        md_path = Path(report_payload.get("markdown", ""))
        report_ok = (
            report.get("ok")
            and report_payload.get("ok") is True
            and json_path.exists()
            and json_path.stat().st_size > 0
            and md_path.exists()
            and md_path.stat().st_size > 0
        )
        report_payload["json_size"] = json_path.stat().st_size if json_path.exists() else 0
        report_payload["markdown_size"] = md_path.stat().st_size if md_path.exists() else 0
    except Exception as exc:
        report_payload = {"parse_error": str(exc), "stdout_tail": report.get("stdout_tail")}
        report_ok = False
    checks.append(check("report_artifact_generation", report_ok, report_payload))

    batch = run_capture([PYTHON_EXE, str(ENTRY), "batch", "000001", "600000", "300750"], timeout=120)
    try:
        batch_payload = parse_json(batch.get("stdout", ""))
        batch_ok = batch.get("ok") and batch_payload.get("ok") is True and batch_payload.get("pass_count") == 3 and len(batch_payload.get("ranking", [])) == 3
    except Exception as exc:
        batch_payload = {"parse_error": str(exc), "stdout_tail": batch.get("stdout_tail")}
        batch_ok = False
    checks.append(check("batch_score_execution", batch_ok, batch_payload))

    blocked = run_capture([PYTHON_EXE, str(ENTRY), "score", "123456"], timeout=90)
    try:
        blocked_payload = parse_json(blocked.get("stdout", ""))
        blocked_ok = blocked.get("exit") != 0 and blocked_payload.get("ok") is False and blocked_payload.get("status") == "DATA_BLOCKED"
    except Exception as exc:
        blocked_payload = {"parse_error": str(exc), "stdout_tail": blocked.get("stdout_tail")}
        blocked_ok = False
    checks.append(check("missing_kline_degrades_to_data_blocked", blocked_ok, blocked_payload))

    stale_env = os.environ.copy()
    stale_env["BAIMAO_EXPECTED_TRADE_DATE"] = "20991231"
    stale = run_capture([PYTHON_EXE, str(ENTRY), "score", "000001"], timeout=90, env=stale_env)
    try:
        stale_payload = parse_json(stale.get("stdout", ""))
        stale_ok = stale.get("exit") != 0 and stale_payload.get("ok") is False and stale_payload.get("status") == "DATA_STALE"
    except Exception as exc:
        stale_payload = {"parse_error": str(exc), "stdout_tail": stale.get("stdout_tail")}
        stale_ok = False
    checks.append(check("stale_kline_blocks_current_conclusion", stale_ok, stale_payload))

    ok = all(item.get("ok") for item in checks)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "skill": "baimao-teacher-system",
        "mode": "workflow_acceptance",
        "status": "CLEAN_PASS" if ok else "BLOCKED",
        "executed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "entry": str(ENTRY),
        "acceptance_report_dir": str(REPORT_DIR),
        "checks": checks,
        "blocks": [item for item in checks if not item.get("ok")],
    }
    out = REPORT_DIR / "latest_workflow_acceptance.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    payload["acceptance_report"] = str(out)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
