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
import csv
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


def _json_file(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"json_object_required:{path}")
    return payload


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _evidence_id(path: Path, fragment: str) -> str:
    return f"sha256:{sha256_file(path)}#{fragment}"


def build_data_gate(run_dir: Path) -> dict:
    evidence_set_id = os.environ.get("CODEX_STOCK_EVIDENCE_SET_ID", "").strip()
    evidence_date = os.environ.get("CODEX_STOCK_EVIDENCE_TRADING_DATE", "").strip()
    shared_status = os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS", "").strip()
    duanxianxia_path = Path(
        os.environ.get("CODEX_DUANXIANXIA_SNAPSHOT", "") or ".missing"
    ).resolve()
    checks = {name: False for name in DATA_GATE_DIMENSIONS}
    evidence_ids = {name: [] for name in DATA_GATE_DIMENSIONS}
    errors: list[str] = []
    effective_date = ""
    try:
        candidates_path = run_dir / "risk_candidates.csv"
        health_path = run_dir / "source_health.csv"
        validation_path = run_dir / "skill_validation.json"
        warning_path = run_dir / "market_risk_warning.json"
        summary_path = run_dir / "integrated_risk_summary.json"
        manifest_path = run_dir / "run_manifest.json"
        evidence_path = run_dir / "evidence.jsonl"
        candidates = _csv_rows(candidates_path)
        health_rows = _csv_rows(health_path)
        health = {row.get("name", ""): row for row in health_rows}
        validation = _json_file(validation_path)
        warning = _json_file(warning_path)
        summary = _json_file(summary_path)
        manifest = _json_file(manifest_path)
        duanxianxia = _json_file(duanxianxia_path)
        effective_date = str(summary.get("run_date") or "")
        selected_datasets = set(duanxianxia.get("selected_datasets") or [])
        datasets = duanxianxia.get("datasets") or {}
        all_datasets_clean = bool(selected_datasets) and all(
            isinstance(datasets.get(name), dict)
            and datasets[name].get("success") is True
            for name in selected_datasets
        )
        required_theme_datasets = {"hotlist", "ztplate", "platechart1", "platechart2"}

        def source_ok(name: str, *, require_rows: bool = True) -> bool:
            row = health.get(name) or {}
            if row.get("status") != "ok":
                return False
            if not require_rows:
                return True
            try:
                return int(float(row.get("rows", "0") or 0)) > 0
            except ValueError:
                return False

        all_sources = (
            bool(health_rows)
            and all(row.get("status") == "ok" for row in health_rows)
            and validation.get("checks", {}).get("all_sources", {}).get("ok") is True
            and validation.get("checks", {}).get("all_sources", {}).get("failure_count") == 0
        )
        candidate_count = int(summary.get("metrics", {}).get("candidate_count") or 0)
        checks["identity"] = bool(
            candidates
            and len(candidates) == candidate_count
            and all(row.get("code") and row.get("name") for row in candidates)
        )
        checks["effective_trading_date"] = bool(
            effective_date
            and effective_date == evidence_date
            and str(manifest.get("run_date") or "") == effective_date
            and str(warning.get("generated_at") or "")[:10] == effective_date
        )
        indexes = warning.get("indexes") or {}
        checks["quote_kline"] = bool(
            warning.get("status") == "CLEAN_PASS"
            and warning.get("data_source") == "本地通达信日线"
            and len(indexes) >= 3
            and all(row.get("price") is not None and row.get("change_pct") is not None for row in indexes.values())
        )
        checks["fundamentals"] = all(
            source_ok(name) for name in ("guarantees", "pledge_ratio", "pledge_detail")
        )
        checks["news_announcements"] = bool(
            source_ok("notices")
            and source_ok("lawsuits")
            and shared_status == "CLEAN_PASS"
            and all_datasets_clean
        )
        checks["sector_theme"] = bool(
            shared_status == "CLEAN_PASS"
            and required_theme_datasets.issubset(selected_datasets)
            and all(datasets[name].get("success") is True for name in required_theme_datasets)
        )
        checks["source_freshness"] = bool(
            summary.get("status") == "CLEAN_PASS"
            and validation.get("ok") is True
            and all_sources
            and shared_status == "CLEAN_PASS"
            and str(duanxianxia.get("generated_at") or "")[:10] == effective_date
            and evidence_path.is_file()
            and evidence_path.stat().st_size > 0
        )
        evidence_ids = {
            "identity": [_evidence_id(candidates_path, "code,name"), _evidence_id(summary_path, "metrics.candidate_count")],
            "effective_trading_date": [_evidence_id(manifest_path, "run_date"), f"{evidence_set_id or 'missing'}#trading_date"],
            "quote_kline": [_evidence_id(warning_path, "data_source,indexes")],
            "fundamentals": [_evidence_id(health_path, "guarantees,pledge_ratio,pledge_detail")],
            "news_announcements": [_evidence_id(health_path, "notices,lawsuits"), f"{evidence_set_id or 'missing'}#duanxianxia.datasets"],
            "sector_theme": [_evidence_id(duanxianxia_path, "datasets.hotlist,ztplate,platechart1,platechart2")],
            "source_freshness": [_evidence_id(validation_path, "checks.all_sources"), _evidence_id(summary_path, "run_date,status")],
        }
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"data_gate_build_failed:{type(exc).__name__}:{exc}")
    if not evidence_set_id:
        errors.append("evidence_set_id_missing")
    if shared_status != "CLEAN_PASS":
        errors.append("shared_evidence_not_clean")
    for name in DATA_GATE_DIMENSIONS:
        if not checks[name]:
            errors.append(f"data_gate_dimension_failed:{name}")
    return {
        "schema": "STOCK_DATA_GATE_V1",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "skill_id": SKILL_ID,
        "effective_trading_date": effective_date,
        "latest_required_trading_date": evidence_date,
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


def business_command(run_dir: Path, extra: list[str]) -> list[str]:
    overrides: dict[str, list[str]] = {
        "golden-ignition": ["run", "000001"],
        "shortline-hotspot-mining": ["run", "--date", datetime.now().strftime("%Y-%m-%d")],
        "a-share-intraday-position-monitor": [
            "run", "--positions-json",
            '[{"code":"000001","name":"Ping An Bank","cost":10.0,"shares":100}]',
        ],
        "industry-chain-analysis": ["run", "--topic", "artificial intelligence"],
        "old-leader-oversold-rebound": ["run", "--date", datetime.now().strftime("%Y-%m-%d")],
        "risk-mine-clearance": ["run", "--", "--output-dir", str(run_dir)],
    }
    return [
        sys.executable,
        str(LEGACY_ENTRY),
        *overrides.get(SKILL_ID, ["run"]),
        *extra,
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
    parser.add_argument("--timeout", type=int, default=300)
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

    if "--output-dir" in business_args:
        print(json.dumps({
            "skill_id": SKILL_ID,
            "status": "BLOCKED",
            "errors": ["canonical_run_dir_override_forbidden"],
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
    evidence_enabled = bool(
        os.environ.get("CODEX_STOCK_EVIDENCE_SET_ID")
        or os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS")
    )
    data_gate: dict | None = None
    if accepted and evidence_enabled:
        data_gate = build_data_gate(run_dir)
        data_gate_errors = list(data_gate.get("errors", []))
        if data_gate_errors:
            failure_tokens.extend(data_gate_errors)
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
    }
    if data_gate is not None:
        result["data_gate"] = data_gate
    if data_gate is not None and data_gate.get("errors"):
        result["errors"] = list(data_gate["errors"])
    result_path = run_dir / "business_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
