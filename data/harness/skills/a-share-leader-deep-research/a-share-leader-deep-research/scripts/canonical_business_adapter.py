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
from datetime import date, datetime
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

DEFAULT_ACTIONS: dict[str, list[str]] = {
    "a-share-leader-deep-research": ["run"],
    "a-share-limit-up-leader-classification": ["info"],
    "nana-teacher-five-strategies": ["run"],
    "quality-track-stock-selection": ["run"],
    "stock-recap-video": ["info"],
    "wechat-public-writing": ["inspect"],
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence_id(path: Path, fragment: str) -> str:
    return f"{path.name}:{sha256_file(path)}#{fragment}"


def build_data_gate(run_dir: Path, environment: dict[str, str]) -> dict:
    payload_paths = sorted(run_dir.rglob("leader_payload.json"))
    payload_path = payload_paths[-1] if payload_paths else run_dir / "leader_payload.json"
    payload = {}
    if payload_path.is_file():
        try:
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
    stocks = payload.get("stocks") if isinstance(payload.get("stocks"), list) else []
    concepts = payload.get("concept_summary") if isinstance(payload.get("concept_summary"), list) else []
    sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
    evidence = payload.get("evidence") if isinstance(payload.get("evidence"), list) else []
    latest = str(environment.get("CODEX_STOCK_EVIDENCE_TRADING_DATE") or "")
    effective = str(payload.get("trade_date") or "")
    evidence_set_id = str(environment.get("CODEX_STOCK_EVIDENCE_SET_ID") or "")
    stock_identity_ok = len(stocks) >= 70 and all(
        isinstance(row, dict)
        and len(str(row.get("stock_code") or "")) == 6
        and bool(str(row.get("stock_name") or "").strip())
        for row in stocks
    )
    market_fields_ok = all(
        isinstance(row, dict)
        and row.get("limit_up_price") is not None
        and row.get("amount") is not None
        and bool(str(row.get("first_limit_time") or "").strip())
        for row in stocks
    )
    classification_ok = all(
        isinstance(row, dict)
        and bool(str(row.get("primary_concept") or "").strip())
        and bool(str(row.get("classification_basis") or "").strip())
        and bool(row.get("field_evidence"))
        for row in stocks
    )
    source_groups = {str(row.get("provider_group") or "") for row in sources if isinstance(row, dict)}
    source_dates_ok = bool(sources) and all(
        str(row.get("trade_date") or "") == effective
        and bool(str(row.get("fetched_at") or "").strip())
        and bool(str(row.get("sha256") or "").strip())
        for row in sources if isinstance(row, dict)
    )
    evidence_ok = len(evidence) >= len(stocks) * 2 and all(
        bool(str(row.get("evidence_id") or "").strip())
        and str(row.get("trade_date") or "") == effective
        for row in evidence if isinstance(row, dict)
    )
    concept_ok = len(concepts) >= 3 and all(
        int(row.get("verified_limit_up_count") or 0) > 0
        and bool(str(row.get("logic_summary") or "").strip())
        and bool(str(row.get("mechanism_evidence") or "").strip())
        and bool(str(row.get("validation_constraints") or "").strip())
        for row in concepts[:3] if isinstance(row, dict)
    )
    checks = {
        "identity": payload_path.is_file() and stock_identity_ok,
        "effective_trading_date": bool(effective and latest) and effective == latest,
        "quote_kline": market_fields_ok and {"东方财富", "短线侠", "连板网"}.issubset(source_groups),
        "fundamentals": classification_ok,
        "news_announcements": evidence_ok and not list(payload.get("unresolved_critical_conflicts") or []),
        "sector_theme": concept_ok,
        "source_freshness": (
            source_dates_ok
            and environment.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS") == "CLEAN_PASS"
            and bool(evidence_set_id)
        ),
    }
    evidence_ids = {
        name: [_evidence_id(payload_path, fragment)] if payload_path.is_file() else [f"missing#{name}"]
        for name, fragment in {
            "identity": "stocks.stock_code,stocks.stock_name",
            "effective_trading_date": "trade_date",
            "quote_kline": "stocks.limit_up_price,stocks.amount,stocks.first_limit_time,sources",
            "fundamentals": "stocks.primary_concept,stocks.classification_basis,stocks.field_evidence",
            "news_announcements": "evidence,unresolved_critical_conflicts",
            "sector_theme": "concept_summary[0:3].logic_summary,mechanism_evidence,validation_constraints",
            "source_freshness": "sources.trade_date,sources.fetched_at,sources.sha256",
        }.items()
    }
    evidence_ids["effective_trading_date"].append(f"{evidence_set_id or 'missing'}#trading_date")
    evidence_ids["source_freshness"].append(f"{evidence_set_id or 'missing'}#created_at,trading_date")
    errors = [f"data_gate_dimension_failed:{name}" for name, passed in checks.items() if not passed]
    try:
        if effective:
            date.fromisoformat(effective)
    except ValueError:
        errors.append("effective_trading_date_invalid")
    return {
        "schema": "STOCK_DATA_GATE_V1",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "skill_id": SKILL_ID,
        "effective_trading_date": effective,
        "latest_required_trading_date": latest,
        "evidence_set_id": evidence_set_id,
        "dimensions": {
            name: {"status": "CLEAN_PASS" if passed else "BLOCKED", "evidence_ids": evidence_ids[name]}
            for name, passed in checks.items()
        },
        "errors": errors,
    }


def business_command(
    run_dir: Path,
    business_args: list[str],
) -> list[str]:
    overrides: dict[str, list[str]] = {
        "golden-ignition": ["run", "000001"],
        "shortline-hotspot-mining": ["run", "--date", datetime.now().strftime("%Y-%m-%d")],
        "a-share-intraday-position-monitor": [
            "run", "--positions-json",
            '[{"code":"000001","name":"Ping An Bank","cost":10.0,"shares":100}]',
        ],
        "industry-chain-analysis": ["run", "--topic", "artificial intelligence"],
        "old-leader-oversold-rebound": ["run", "--date", datetime.now().strftime("%Y-%m-%d")],
    }
    if SKILL_ID == "a-share-leader-deep-research" and (
        not business_args or business_args[0] in {"run", "replay"}
    ):
        actions = list(business_args or ["run"])
        if "--run-dir" not in actions:
            actions.extend(["--run-dir", str(run_dir)])
    else:
        actions = (
            business_args
            or DEFAULT_ACTIONS.get(SKILL_ID)
            or overrides.get(SKILL_ID)
            or ["run"]
        )
    return [sys.executable, str(LEGACY_ENTRY), *actions]


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
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("business_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    business_args = [str(item) for item in args.business_args]
    if business_args and business_args[0] == "--":
        business_args = business_args[1:]

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

    command = business_command(run_dir, business_args)
    child = run_child(command, args.timeout)
    stdout_path = run_dir / "business_child.stdout.txt"
    stderr_path = run_dir / "business_child.stderr.txt"
    stdout_path.write_text(str(child["stdout"]), encoding="utf-8")
    stderr_path.write_text(str(child["stderr"]), encoding="utf-8")
    combined = str(child["stdout"]) + "\n" + str(child["stderr"])
    failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    accepted = child["returncode"] == 0 and not failure_tokens
    data_gate = None
    data_gate_errors: list[str] = []
    if accepted and os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS") == "CLEAN_PASS":
        data_gate = build_data_gate(run_dir, dict(os.environ))
        if data_gate.get("status") != "CLEAN_PASS":
            data_gate_errors = list(data_gate.get("errors") or ["data_gate_blocked"])
            accepted = False
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
        "errors": data_gate_errors,
    }
    if data_gate is not None:
        result["data_gate"] = data_gate
    result_path = run_dir / "business_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
