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
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SKILL_DIR = Path(__file__).resolve().parents[1]
ENTRY = SKILL_DIR / "scripts" / "baimao_score_system.py"
REPORTS = SKILL_DIR / "reports" / "acceptance"
PYTHON_EXE = sys.executable


def run(cmd: list[str], timeout: int = 180) -> dict[str, Any]:
    try:
        r = subprocess.run(cmd, cwd=str(SKILL_DIR), capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=timeout)
        return {"ok": r.returncode == 0, "exit": r.returncode, "cmd": cmd, "stdout": r.stdout, "stderr": r.stderr, "stdout_tail": r.stdout[-1600:]}
    except Exception as exc:
        return {"ok": False, "cmd": cmd, "error": f"{type(exc).__name__}: {exc}"}


def parse(text: str) -> Any:
    clean = (text or "").lstrip("\ufeff").strip()
    clean = clean[clean.find("{"):]
    return json.loads(clean)


def main() -> int:
    checks = []
    for name, cmd in [
        ("info", [PYTHON_EXE, str(ENTRY), "info"]),
        ("score", [PYTHON_EXE, str(ENTRY), "score", "301372"]),
        ("analyze", [PYTHON_EXE, str(ENTRY), "analyze", "301372"]),
        ("report", [PYTHON_EXE, str(ENTRY), "report", "301372"]),
    ]:
        r = run(cmd, timeout=240)
        detail: Any = r.get("stdout_tail") or r.get("error")
        ok = bool(r.get("ok"))
        if name in {"score", "analyze", "report"}:
            payload = parse(r.get("stdout", ""))
            detail = payload
            status = payload.get("status")
            controlled_block = status in {"DATA_STALE", "DATA_BLOCKED"}
            ok = (payload.get("ok") is True and status == "CLEAN_PASS") or (payload.get("ok") is False and controlled_block)
            if name == "analyze":
                if status == "CLEAN_PASS":
                    ok = ok and "finance" in payload and "recheck_conditions" in payload and payload.get("trade_date") == payload.get("technical", {}).get("data_gate", {}).get("expected_trade_date")
                else:
                    ok = ok and payload.get("conclusion") == "数据闸门未通过，禁止输出综合结论。"
            if name == "report":
                if status == "CLEAN_PASS":
                    p = Path(payload.get("docx", ""))
                    ok = ok and p.exists() and p.stat().st_size > 0
                    payload["docx_size"] = p.stat().st_size if p.exists() else 0
                else:
                    ok = ok and payload.get("conclusion") == "数据闸门未通过，禁止输出综合结论。"
        checks.append({"name": name, "ok": ok, "detail": detail})
    ok = all(c["ok"] for c in checks)
    REPORTS.mkdir(parents=True, exist_ok=True)
    payload = {
        "skill": "baimao-score-system",
        "display_name": "白猫老师评分体系",
        "mode": "acceptance",
        "executed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": "CLEAN_PASS" if ok else "BLOCKED",
        "checks": checks,
        "blocks": [c for c in checks if not c["ok"]],
    }
    out = REPORTS / "latest_acceptance.json"
    payload["acceptance_report"] = str(out)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
