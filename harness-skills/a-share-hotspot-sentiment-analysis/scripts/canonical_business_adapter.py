#!/usr/bin/env python3
"""Canonical adapter for a merged local Codex stock skill."""
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
from datetime import date
from pathlib import Path
_stock_adapter_shared_scripts = str(_OneStockEmbeddedPath(__file__).resolve().parents[3] / "scripts")
if _stock_adapter_shared_scripts not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _stock_adapter_shared_scripts)
from stock_adapter_io import atomic_write_json, atomic_write_text, enable_atomic_path_writes


ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = ROOT.name
LEGACY_ENTRY = ROOT / "scripts" / "legacy_codex_entry.py"
DELIVERY_VALIDATOR = ROOT / "scripts" / "report_delivery_validator.py"
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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _json_from_stdout(stdout: str) -> dict:
    try:
        payload = json.loads(stdout.strip())
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _evidence_id(path: Path, fragment: str) -> str:
    return f"sha256:{sha256_file(path)}#{fragment}"


def build_data_gate(merged: dict, environment: dict[str, str]) -> dict:
    component_root = Path(str(merged.get("run_dir") or ""))
    sentiment_dir = component_root / "sentiment"
    paths = {
        "events": sentiment_dir / "a_share_sentiment_event_pool.json",
        "scores": sentiment_dir / "a_share_sentiment_scores.json",
        "clusters": sentiment_dir / "a_share_sentiment_clusters.json",
        "mandatory": sentiment_dir / "a_share_sentiment_mandatory_sources_audit.json",
        "cross": sentiment_dir / "a_share_sentiment_market_cross_validation_audit.json",
        "market": sentiment_dir / "a_share_sentiment_market_validation_pool.json",
        "acquisition": sentiment_dir / "a_share_sentiment_acquisition_audit.json",
        "integration": sentiment_dir / "a_share_sentiment_source_integration_audit.json",
        "delivery": sentiment_dir / "a_share_sentiment_delivery_audit.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    payloads = {name: _read_json(path) for name, path in paths.items() if path.is_file()}
    events = payloads.get("events") if isinstance(payloads.get("events"), list) else []
    scores = payloads.get("scores") if isinstance(payloads.get("scores"), list) else []
    clusters = payloads.get("clusters") if isinstance(payloads.get("clusters"), list) else []
    mandatory = payloads.get("mandatory") if isinstance(payloads.get("mandatory"), dict) else {}
    cross = payloads.get("cross") if isinstance(payloads.get("cross"), dict) else {}
    market = payloads.get("market") if isinstance(payloads.get("market"), list) else []
    acquisition = payloads.get("acquisition") if isinstance(payloads.get("acquisition"), dict) else {}
    integration = payloads.get("integration") if isinstance(payloads.get("integration"), dict) else {}
    delivery = payloads.get("delivery") if isinstance(payloads.get("delivery"), dict) else {}

    latest = str(environment.get("CODEX_STOCK_EVIDENCE_TRADING_DATE") or "")
    latest_label = ""
    try:
        latest_date = date.fromisoformat(latest)
        latest_label = f"{latest_date.month}月{latest_date.day}日"
    except ValueError:
        latest_date = None
    effective_market_sources = {
        str(row.get("source") or "").strip()
        for row in market
        if isinstance(row, dict)
        and str(row.get("market_date") or row.get("date") or "").strip()
        in {latest, latest_label}
    }
    required_effective_sources = {"通达信", "连板网"}
    effective = (
        latest
        if latest_date is not None
        and all(
            any(required in source for source in effective_market_sources)
            for required in required_effective_sources
        )
        else ""
    )
    evidence_set_id = str(environment.get("CODEX_STOCK_EVIDENCE_SET_ID") or "")
    required_sources = list(mandatory.get("required_sources") or [])
    source_counts = mandatory.get("source_counts") if isinstance(mandatory.get("source_counts"), dict) else {}
    present_sources = set(cross.get("present_sources") or [])
    business_audit = integration.get("business_society") if isinstance(integration.get("business_society"), dict) else {}
    event_identity_ok = all(
        isinstance(row, dict)
        and str(row.get("source") or "").strip()
        and str(row.get("event") or "").strip()
        and str(row.get("published_at") or "").strip()
        for row in events[:20]
    )
    theme_names = [
        str(row.get("name") or row.get("cluster_name") or row.get("theme") or "").strip()
        for row in clusters
        if isinstance(row, dict)
    ]
    checks = {
        "identity": not missing and len(events) >= 20 and event_identity_ok,
        "effective_trading_date": bool(effective and latest) and effective == latest,
        "quote_kline": cross.get("ok") is True and {"通达信", "短线侠", "连板网"}.issubset(present_sources),
        "fundamentals": (
            integration.get("ok") is True
            and int(integration.get("unified_event_count") or 0) >= 20
            and business_audit.get("preset_sector_pool_used") is False
            and str(business_audit.get("capture_sha256") or "").strip() != ""
            and int(business_audit.get("raw_count") or 0) > 0
            and int(business_audit.get("clean_count") or 0) > 0
            and business_audit.get("capture_errors") == []
        ),
        "news_announcements": (
            mandatory.get("ok") is True
            and len(required_sources) >= 8
            and all(int(source_counts.get(name) or 0) >= 10 for name in required_sources)
        ),
        "sector_theme": (
            len(scores) >= 2
            and len(clusters) >= 2
            and sum(bool(name) for name in theme_names) >= 2
            and delivery.get("ok") is True
        ),
        "source_freshness": (
            acquisition.get("ok") is True
            and integration.get("ok") is True
            and environment.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS") == "CLEAN_PASS"
            and bool(evidence_set_id)
        ),
    }
    evidence_ids = {
        "identity": [_evidence_id(paths["events"], "source,event,published_at")],
        "effective_trading_date": [
            _evidence_id(paths["market"], "market_date,date,source"),
            f"{evidence_set_id or 'missing'}#trading_date",
        ],
        "quote_kline": [_evidence_id(paths["cross"], "present_sources,dimension_sources")],
        "fundamentals": [_evidence_id(paths["integration"], "unified_event_count,business_society")],
        "news_announcements": [_evidence_id(paths["mandatory"], "required_sources,source_counts")],
        "sector_theme": [_evidence_id(paths["clusters"], "themes"), _evidence_id(paths["scores"], "ranking")],
        "source_freshness": [_evidence_id(paths["acquisition"], "event_window_start,event_window_end"), f"{evidence_set_id or 'missing'}#created_at,trading_date"],
    } if not missing else {name: [f"missing#{name}"] for name in checks}
    errors = [f"data_gate_dimension_failed:{name}" for name, passed in checks.items() if not passed]
    errors.extend(f"data_gate_artifact_missing:{name}" for name in missing)
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
        "effective_market_sources": sorted(effective_market_sources),
        "dimensions": {
            name: {
                "status": "CLEAN_PASS" if passed else "BLOCKED",
                "evidence_ids": evidence_ids[name],
            }
            for name, passed in checks.items()
        },
        "errors": errors,
    }


def main() -> int:
    enable_atomic_path_writes()
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("business_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
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

    requested = list(args.business_args)
    if requested and requested[0] == "--":
        requested = requested[1:]
    command = [sys.executable, str(LEGACY_ENTRY), "run"]
    if requested:
        command.extend(["--", *requested])
    child = run_child(command, args.timeout)
    merged_result = _json_from_stdout(str(child["stdout"]))
    stdout_path = run_dir / "business_child.stdout.txt"
    stderr_path = run_dir / "business_child.stderr.txt"
    stdout_path.write_text(str(child["stdout"]), encoding="utf-8")
    stderr_path.write_text(str(child["stderr"]), encoding="utf-8")
    combined = str(child["stdout"]) + "\n" + str(child["stderr"])
    failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    accepted = child["returncode"] == 0 and not failure_tokens
    delivery_manifest_path = run_dir / "formatted_delivery_manifest.json"
    validator_stdout_path = run_dir / "delivery_validator.stdout.txt"
    validator_stderr_path = run_dir / "delivery_validator.stderr.txt"
    validator = {
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "timed_out": False,
    }
    if accepted:
        validator = run_child(
            [
                sys.executable,
                str(DELIVERY_VALIDATOR),
                "--business-stdout",
                str(stdout_path),
                "--output",
                str(delivery_manifest_path),
            ],
            min(args.timeout, 120),
        )
        validator_stdout_path.write_text(
            str(validator["stdout"]),
            encoding="utf-8",
        )
        validator_stderr_path.write_text(
            str(validator["stderr"]),
            encoding="utf-8",
        )
        accepted = (
            validator["returncode"] == 0
            and delivery_manifest_path.is_file()
            and delivery_manifest_path.stat().st_size > 100
        )
    else:
        validator_stdout_path.write_text("", encoding="utf-8")
        validator_stderr_path.write_text("", encoding="utf-8")
    data_gate = None
    data_gate_errors = []
    if accepted and os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS") == "CLEAN_PASS":
        data_gate = build_data_gate(merged_result, dict(os.environ))
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
        "delivery_validation": {
            "validator": str(DELIVERY_VALIDATOR),
            "returncode": validator["returncode"],
            "timed_out": validator["timed_out"],
            "manifest": str(delivery_manifest_path),
        },
        "artifacts": {
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "delivery_manifest": str(delivery_manifest_path),
            "validator_stdout": str(validator_stdout_path),
            "validator_stderr": str(validator_stderr_path),
        },
        "errors": data_gate_errors,
    }
    if data_gate is not None:
        result["data_gate"] = data_gate
    (run_dir / "business_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
