#!/usr/bin/env python3
"""Canonical business-process adapter for one local Codex stock skill."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
_stock_adapter_shared_scripts = str(_OneStockEmbeddedPath(__file__).resolve().parents[3] / "scripts")
if _stock_adapter_shared_scripts not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _stock_adapter_shared_scripts)
from stock_adapter_io import atomic_write_json, atomic_write_text, enable_atomic_path_writes


ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = ROOT.name
LEGACY_ENTRY = ROOT / "scripts" / "legacy_codex_entry.py"
FAILURE_TOKENS = (
    '"status": "BLOCKED"',
    '"status":"BLOCKED"',
    '"status": "FAILED"',
    '"status":"FAILED"',
    '"status": "FAIL"',
    '"status":"FAIL"',
    '"status": "ERROR"',
    '"status":"ERROR"',
    '"status": "PROCEDURAL"',
    '"status":"PROCEDURAL"',
    '"status": "DATA_REQUIRED"',
    '"status":"DATA_REQUIRED"',
    '"status": "DATA_STALE"',
    '"status":"DATA_STALE"',
    "Traceback (most recent call last)",
    "TIMEOUT after ",
)
RESULT_FILENAME = "a-share-15d-selection-result.json"
DATA_GATE_DIMENSIONS = (
    "identity",
    "effective_trading_date",
    "quote_kline",
    "fundamentals",
    "news_announcements",
    "sector_theme",
    "source_freshness",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _iso_trade_date(value: object) -> str:
    text = str(value or "").strip()
    if len(text) == 8 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d").date().isoformat()
    return datetime.strptime(text, "%Y-%m-%d").date().isoformat()


def build_data_gate(run_dir: Path) -> dict:
    result_path = run_dir / "deliverables" / RESULT_FILENAME
    evidence_set_id = os.environ.get("CODEX_STOCK_EVIDENCE_SET_ID", "").strip()
    evidence_date_raw = os.environ.get("CODEX_STOCK_EVIDENCE_TRADING_DATE", "").strip()
    shared_status = os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS", "").strip()
    errors: list[str] = []
    payload: dict = {}
    try:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"result_artifact_invalid:{type(exc).__name__}")

    try:
        effective_date = _iso_trade_date(payload.get("trade_date"))
    except (TypeError, ValueError):
        effective_date = ""
        errors.append("effective_trading_date_invalid")
    try:
        latest_required_date = _iso_trade_date(evidence_date_raw)
    except (TypeError, ValueError):
        latest_required_date = ""
        errors.append("evidence_trading_date_invalid")

    ranking = payload.get("ranking") if isinstance(payload.get("ranking"), list) else []
    excluded = payload.get("excluded") if isinstance(payload.get("excluded"), list) else []
    candidate_pool = payload.get("candidate_pool") if isinstance(payload.get("candidate_pool"), dict) else {}
    validation = payload.get("validation") if isinstance(payload.get("validation"), dict) else {}
    macro = payload.get("macro") if isinstance(payload.get("macro"), dict) else {}
    members = candidate_pool.get("members") if isinstance(candidate_pool.get("members"), list) else []
    result_digest = sha256_file(result_path) if result_path.is_file() else "missing"
    result_evidence = f"sha256:{result_digest}"

    checks = {
        "identity": (
            payload.get("status") == "CLEAN_PASS"
            and int(candidate_pool.get("member_count", -1)) == int(payload.get("pool_candidate_count", -2))
            and len(members) == int(candidate_pool.get("member_count", -1))
            and all(str(item.get("code") or "").strip() for item in [*ranking, *excluded])
        ),
        "effective_trading_date": bool(effective_date and effective_date == latest_required_date),
        "quote_kline": (
            validation.get("complete_scan") is True
            and validation.get("market_scope_complete") is True
            and macro.get("scan_coverage", {}).get("complete") is True
        ),
        "fundamentals": (
            all(item.get("score_contract", {}).get("fundamental_positive_weight") == 0 for item in ranking)
            and all(
                any(row.get("name") == "立案调查或财务造假" for row in item.get("hard_exclusions", []))
                for item in ranking
            )
        ),
        "news_announcements": (
            shared_status == "CLEAN_PASS"
            and all(item.get("evidence_status") == "LOCAL_TEXT_COVERED" for item in ranking)
        ),
        "sector_theme": (
            shared_status == "CLEAN_PASS"
            and all(isinstance(item.get("concepts"), list) for item in ranking)
        ),
        "source_freshness": (
            shared_status == "CLEAN_PASS"
            and validation.get("current_trade_date") is True
            and bool(effective_date and effective_date == latest_required_date)
        ),
    }
    if not evidence_set_id:
        errors.append("evidence_set_id_missing")
    if shared_status != "CLEAN_PASS":
        errors.append("shared_evidence_not_clean")
    for name in DATA_GATE_DIMENSIONS:
        if not checks[name]:
            errors.append(f"data_gate_dimension_failed:{name}")

    evidence_ids = {
        "identity": [f"{result_evidence}#candidate_pool", f"{result_evidence}#ranking_identity"],
        "effective_trading_date": [f"{result_evidence}#trade_date", f"{evidence_set_id or 'missing'}#trading_date"],
        "quote_kline": [f"{result_evidence}#source.market", f"{result_evidence}#macro.scan_coverage"],
        "fundamentals": [f"{result_evidence}#fundamental_positive_weight_zero", f"{result_evidence}#hard_financial_risk_gate"],
        "news_announcements": [f"{result_evidence}#candidate_news_coverage", f"{evidence_set_id or 'missing'}#duanxianxia"],
        "sector_theme": [f"{result_evidence}#ranking.concepts", f"{evidence_set_id or 'missing'}#duanxianxia"],
        "source_freshness": [f"{result_evidence}#validation.current_trade_date", f"{evidence_set_id or 'missing'}#created_at"],
    }
    return {
        "schema": "STOCK_DATA_GATE_V1",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "skill_id": SKILL_ID,
        "effective_trading_date": effective_date,
        "latest_required_trading_date": latest_required_date,
        "evidence_set_id": evidence_set_id,
        "dimensions": {
            name: {
                "status": "CLEAN_PASS" if checks[name] else "BLOCKED",
                "evidence_ids": evidence_ids[name],
            }
            for name in DATA_GATE_DIMENSIONS
        },
        "errors": errors,
    }


def validate_business_args(arguments: list[str]) -> list[str]:
    if not arguments:
        return []
    if (
        len(arguments) == 2
        and arguments[0] == "--candidate-block"
        and str(arguments[1]).strip()
    ):
        return []
    return ["unsupported_business_arguments:" + " ".join(arguments)]


def business_command(run_dir: Path, business_args: list[str] | None = None) -> list[str]:
    overrides: dict[str, list[str]] = {
        "a-share-15d-selection": [
            "run", "--", "--outdir", str(run_dir / "deliverables"),
        ],
        "golden-ignition": ["run", "000001"],
        "shortline-hotspot-mining": ["run", "--date", datetime.now().strftime("%Y-%m-%d")],
        "a-share-intraday-position-monitor": [
            "run", "--positions-json",
            '[{"code":"000001","name":"Ping An Bank","cost":10.0,"shares":100}]',
        ],
        "industry-chain-analysis": ["run", "--topic", "artificial intelligence"],
        "old-leader-oversold-rebound": ["run", "--date", datetime.now().strftime("%Y-%m-%d")],
    }
    return [
        sys.executable,
        str(LEGACY_ENTRY),
        *overrides.get(SKILL_ID, ["run"]),
        *(business_args or []),
    ]


def run_child(command: list[str], timeout: int) -> dict:
    environment = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "ONESTOCK_STOCK_CANONICAL_CHILD": "1",
    }
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=environment,
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "returncode": 124,
            "stdout": stdout,
            "stderr": stderr + f"\nTIMEOUT after {timeout}s",
            "timed_out": True,
        }
    except Exception as exc:
        return {
            "returncode": 125,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "timed_out": False,
        }


def main() -> int:
    enable_atomic_path_writes()
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--timeout", type=int, default=330)
    args, business_args = parser.parse_known_args()
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    if os.environ.get("CODEX_STOCK_CANONICAL_EXECUTION") != "1":
        print(json.dumps({
            "skill_id": SKILL_ID,
            "status": "BLOCKED",
            "errors": ["canonical_execution_environment_missing"],
        }, ensure_ascii=False))
        return 2
    if not LEGACY_ENTRY.is_file():
        print(json.dumps({
            "skill_id": SKILL_ID,
            "status": "BLOCKED",
            "errors": [f"legacy_entry_missing:{LEGACY_ENTRY}"],
        }, ensure_ascii=False))
        return 2

    business_arg_errors = validate_business_args(business_args)
    if business_arg_errors:
        print(json.dumps({
            "skill_id": SKILL_ID,
            "status": "BLOCKED",
            "errors": business_arg_errors,
        }, ensure_ascii=False))
        return 2

    command = business_command(run_dir, business_args)
    child = run_child(command, args.timeout)
    stdout_path = run_dir / "business_child.stdout.txt"
    stderr_path = run_dir / "business_child.stderr.txt"
    atomic_write_text(stdout_path, str(child["stdout"]))
    atomic_write_text(stderr_path, str(child["stderr"]))
    combined = str(child["stdout"]) + "\n" + str(child["stderr"])
    failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    evidence_enabled = bool(
        os.environ.get("CODEX_STOCK_EVIDENCE_SET_ID")
        or os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS")
    )
    data_gate = build_data_gate(run_dir) if evidence_enabled else None
    data_gate_errors = list(data_gate.get("errors", [])) if data_gate else []
    accepted = child["returncode"] == 0 and not failure_tokens and not data_gate_errors
    result = {
        "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
        "skill_id": SKILL_ID,
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "business_process": {
            "command": command,
            "cwd": str(ROOT),
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
            "failure_tokens": failure_tokens,
        },
        "business_binding": {
            "path": str(LEGACY_ENTRY),
            "sha256": sha256_file(LEGACY_ENTRY),
        },
        "artifacts": {
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        },
    }
    if data_gate is not None:
        result["data_gate"] = data_gate
    if data_gate_errors:
        result["errors"] = data_gate_errors
    result_path = run_dir / "business_result.json"
    atomic_write_json(result_path, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
