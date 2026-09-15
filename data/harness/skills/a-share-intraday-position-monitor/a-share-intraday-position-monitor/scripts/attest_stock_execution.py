#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRIMARY_SKILL = "a-share-intraday-position-monitor"
SUPPORT_SKILL = "support-pressure-analysis-system"
PRIMARY_ENTRY = ROOT / "scripts" / "codex_entry.py"
SUPPORT_ENTRY = Path.home() / ".codex" / "skills" / SUPPORT_SKILL / "scripts" / "codex_entry.py"
STOCK_GATE = Path.home() / "plugins" / "stock-freshness-delivery-gate" / "scripts" / "stock_freshness_delivery_hook.py"
SCHEMA = "CN-STOCK-SKILL-EXECUTION-RECEIPT-V1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def binding(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return {"path": str(resolved), "sha256": sha256(resolved), "size_bytes": resolved.stat().st_size}


def run_gate(arguments: list[str]) -> dict[str, Any]:
    if not STOCK_GATE.is_file():
        raise FileNotFoundError(f"stock gate missing: {STOCK_GATE}")
    completed = subprocess.run(
        [sys.executable, str(STOCK_GATE), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"stock gate invalid JSON: {error}: {completed.stdout[-500:]} {completed.stderr[-500:]}") from error
    if completed.returncode != 0:
        raise RuntimeError(f"stock gate failed: {payload}")
    return payload


def build_and_attest(
    *,
    result_path: Path,
    support_report_path: Path,
    support_argv: list[str],
    primary_argv: list[str],
    target_name: str,
    output_dir: Path,
) -> dict[str, Any]:
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not thread_id:
        return {"status": "NOT_VERIFIED", "reason": "CODEX_THREAD_ID_missing"}
    task_cwd = os.environ.get("CODEX_STOCK_TASK_CWD", "").strip() or os.getcwd()
    result = json.loads(result_path.read_text(encoding="utf-8-sig"))
    support = json.loads(support_report_path.read_text(encoding="utf-8-sig"))
    symbol = str(result["symbol"]).upper()
    trade_date = str(result["technical"]["last_date"])
    if support.get("engine_version"):
        if support.get("status") != "PASS" or str(support.get("symbol", "")).upper() != symbol:
            raise RuntimeError(f"scientific support target mismatch: {symbol}")
        support_assertions = [
            {"category": "status", "pointer": "/status", "operator": "eq", "expected": "PASS"},
            {"category": "identity", "pointer": "/symbol", "operator": "eq", "expected": symbol},
            {"category": "trade_date", "pointer": "/data_quality/end_date", "operator": "eq", "expected": trade_date},
        ]
    else:
        support_index = next(
            (index for index, row in enumerate(support.get("results", [])) if row.get("symbol") == symbol),
            None,
        )
        if support_index is None:
            raise RuntimeError(f"support target missing: {symbol}")
        support_assertions = [
            {"category": "status", "pointer": f"/results/{support_index}/status", "operator": "eq", "expected": "PASS"},
            {"category": "identity", "pointer": f"/results/{support_index}/symbol", "operator": "eq", "expected": symbol},
            {"category": "trade_date", "pointer": f"/results/{support_index}/last_date", "operator": "eq", "expected": trade_date},
        ]
    inventory_payload = run_gate(["inventory"])
    installed = inventory_payload.get("installed_stock_skills")
    if inventory_payload.get("status") != "PASS" or not isinstance(installed, list):
        raise RuntimeError(f"stock inventory invalid: {inventory_payload}")

    selected = sorted([PRIMARY_SKILL, SUPPORT_SKILL])
    result_hash = sha256(result_path)
    support_hash = sha256(support_report_path)
    consumer_path = output_dir / "stock_skill_integration_consumer.json"
    receipt_path = output_dir / "stock_skill_execution_receipt.json"
    consumer = {
        "gate_status": "PASS",
        "symbol": symbol,
        "target_name": target_name or symbol.split(".")[0],
        "latest_trade_date": trade_date,
        "selected_skills": selected,
        "results": {PRIMARY_SKILL: result_hash, SUPPORT_SKILL: support_hash},
    }
    consumer_path.write_text(json.dumps(consumer, ensure_ascii=False, indent=2), encoding="utf-8")

    receipt = {
        "schema": SCHEMA,
        "thread_id": thread_id,
        "cwd": str(Path(task_cwd).resolve()),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": {
            "symbol": symbol,
            "name": target_name or symbol.split(".")[0],
            "latest_trade_date": trade_date,
        },
        "inventory": {
            "installed": installed,
            "selected": selected,
            "obvious_unselected": {
                "stock-analysis": "本次是持仓监控技能实跑，不重复执行个股深度研究流程。",
                "stock-watchlist": "本次不新增、删除或维护自选股列表。",
                "stock-delivery-risk-gate": "本次仅生成技能内部JSON和Markdown，不发布股票Office文件。",
                "stock-unified": "本次不是选股任务，直接执行专用持仓监控技能。",
            },
        },
        "executions": [
            {
                "skill": PRIMARY_SKILL,
                "entry_binding": binding(PRIMARY_ENTRY),
                "argv": primary_argv,
                "exit_code": 0,
                "result_binding": binding(result_path),
                "assertions": [
                    {"category": "status", "pointer": "/status", "operator": "eq", "expected": "PASS"},
                    {"category": "identity", "pointer": "/symbol", "operator": "eq", "expected": symbol},
                    {"category": "trade_date", "pointer": "/technical/last_date", "operator": "eq", "expected": trade_date},
                ],
            },
            {
                "skill": SUPPORT_SKILL,
                "entry_binding": binding(SUPPORT_ENTRY),
                "argv": support_argv,
                "exit_code": 0,
                "result_binding": binding(support_report_path),
                "assertions": support_assertions,
            },
        ],
        "integration": {
            "consumer_binding": binding(consumer_path),
            "assertions": [
                {"category": "gate", "pointer": "/gate_status", "operator": "eq", "expected": "PASS"},
                {"category": "identity", "pointer": "/symbol", "operator": "eq", "expected": symbol},
                {"category": "trade_date", "pointer": "/latest_trade_date", "operator": "eq", "expected": trade_date},
                {
                    "category": "inclusion",
                    "skill": PRIMARY_SKILL,
                    "pointer": f"/results/{PRIMARY_SKILL}",
                    "operator": "eq",
                    "expected": result_hash,
                },
                {
                    "category": "inclusion",
                    "skill": SUPPORT_SKILL,
                    "pointer": f"/results/{SUPPORT_SKILL}",
                    "operator": "eq",
                    "expected": support_hash,
                },
            ],
        },
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    verification = run_gate(["verify-receipt", "--receipt", str(receipt_path)])
    if verification.get("ok") is not True:
        raise RuntimeError(f"stock receipt verification failed: {verification}")
    attestation = run_gate(["attest", "--receipt", str(receipt_path)])
    if attestation.get("ok") is not True:
        raise RuntimeError(f"stock receipt attestation failed: {attestation}")
    return {
        "status": "PASS",
        "receipt_path": str(receipt_path),
        "receipt_sha256": sha256(receipt_path),
        "consumer_path": str(consumer_path),
        "consumer_sha256": sha256(consumer_path),
        "attestation_id": attestation.get("attestation_id"),
        "selected_skills": selected,
        "latest_trade_date": trade_date,
    }
