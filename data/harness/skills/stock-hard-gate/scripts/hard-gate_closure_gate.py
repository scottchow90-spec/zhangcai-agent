#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts" / "preflight.py"
VALID_CANARY = (
    "逐字回读 用户原话 禁止默认替代 禁止任务扩展 禁止单源结论 "
    "禁止热替换 输出结构服从用户 禁止缩窄范围 禁止子代理跑偏 "
    "禁止假交付"
)


def check() -> int:
    environment = {
        **os.environ,
        "ONESTOCK_STOCK_CANONICAL_CHILD": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    completed = subprocess.run(
        [sys.executable, str(PREFLIGHT), VALID_CANARY, "preflight"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        timeout=30,
    )
    errors = []
    if completed.returncode != 0:
        errors.append(f"preflight_returncode:{completed.returncode}")
    if '"status": "PASS"' not in completed.stdout:
        errors.append("preflight_pass_semantics_missing")
    payload = {
        "schema": "STOCK_HARD_GATE_CLOSURE_V1",
        "skill_id": "stock-hard-gate",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "errors": errors,
        "preflight": {
            "path": str(PREFLIGHT),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__" and os.environ.get(
    "ONESTOCK_STOCK_CANONICAL_CHILD"
) != "1":
    print(
        "canonical_stock_legacy_entry_direct_execution_blocked",
        file=sys.stderr,
    )
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(check())
