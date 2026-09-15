#!/usr/bin/env python3
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
from pathlib import Path
_stock_adapter_shared_scripts = str(_OneStockEmbeddedPath(__file__).resolve().parents[3] / "scripts")
if _stock_adapter_shared_scripts not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _stock_adapter_shared_scripts)
from stock_adapter_io import atomic_write_json, atomic_write_text, enable_atomic_path_writes

from poster_template import (
    POSTER_NAME,
    PREVIEW_NAME,
    render_audited_custom_poster,
    render_poster,
)
from poster_validator import write_validation


ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "scripts" / "legacy_codex_entry.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_data_gate(
    sentiment_result: Path,
    sentiment_snapshot: Path,
    environment: dict[str, str] | None = None,
) -> dict:
    environment = dict(os.environ if environment is None else environment)
    result_payload = json.loads(sentiment_result.read_text(encoding="utf-8"))
    snapshot_payload = json.loads(sentiment_snapshot.read_text(encoding="utf-8"))
    evidence_set_id = str(environment.get("CODEX_STOCK_EVIDENCE_SET_ID") or "").strip()
    latest_date = str(environment.get("CODEX_STOCK_EVIDENCE_TRADING_DATE") or "").strip()
    effective_date = str(result_payload.get("trading_date") or "").strip()
    market = snapshot_payload.get("market") if isinstance(snapshot_payload, dict) else None
    market = market if isinstance(market, dict) else {}
    topics = snapshot_payload.get("topics") if isinstance(snapshot_payload, dict) else None
    topics = topics if isinstance(topics, list) else []
    sources = result_payload.get("sources") if isinstance(result_payload, dict) else None
    sources = sources if isinstance(sources, dict) else {}
    tdx = sources.get("tongdaxin") if isinstance(sources.get("tongdaxin"), dict) else {}
    duanxianxia = sources.get("duanxianxia") if isinstance(sources.get("duanxianxia"), dict) else {}
    lianban = sources.get("lianban") if isinstance(sources.get("lianban"), dict) else {}
    clean = (
        result_payload.get("status") == "CLEAN_PASS"
        and result_payload.get("schema") == "SHORT_TERM_MARKET_SENTIMENT_PDF_STRICT_V1"
        and snapshot_payload.get("schema") == "SHORT_TERM_SENTIMENT_SNAPSHOT_V1"
        and snapshot_payload.get("trading_date") == effective_date
    )
    numeric_market_fields = (
        "index_change_pct", "advancers", "decliners", "total_amount_billion",
        "amount_change_pct", "limit_up", "limit_down", "consecutive",
        "max_board", "seal_rate", "broken_board",
    )
    source_dates_current = all(
        isinstance(source, dict)
        and source.get("verified") is True
        and str(source.get("trading_date") or "") == effective_date
        for source in (tdx, duanxianxia, lianban)
    )
    checks = {
        "identity": clean and int(tdx.get("coverage") or 0) > 0,
        "effective_trading_date": clean and bool(latest_date) and effective_date == latest_date,
        "quote_kline": (
            clean
            and tdx.get("verified") is True
            and str(tdx.get("root") or "") == r"C:\new_tdx_mock"
            and all(isinstance(market.get(field), (int, float)) and not isinstance(market.get(field), bool) for field in numeric_market_fields)
        ),
        "fundamentals": (
            clean
            and int(tdx.get("coverage") or 0) > 0
            and int(market.get("advancers") or 0) + int(market.get("decliners") or 0) > 0
        ),
        "news_announcements": (
            clean
            and duanxianxia.get("verified") is True
            and len(duanxianxia.get("datasets") or []) >= 4
            and lianban.get("verified") is True
            and environment.get("CODEX_DUANXIANXIA_STATUS") == "CLEAN_PASS"
        ),
        "sector_theme": (
            clean
            and bool(topics)
            and all(isinstance(row, dict) and str(row.get("name") or "").strip() and int(row.get("count") or 0) > 0 for row in topics)
            and int(market.get("topic_count_ge3") or 0) == len(topics)
        ),
        "source_freshness": (
            clean
            and source_dates_current
            and environment.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS") == "CLEAN_PASS"
            and bool(evidence_set_id)
        ),
    }
    result_id = f"sha256:{sha256(sentiment_result)}"
    snapshot_id = f"sha256:{sha256(sentiment_snapshot)}"
    evidence_ids = {
        "identity": [f"{snapshot_id}#sources.tongdaxin.coverage"],
        "effective_trading_date": [f"{result_id}#trading_date", f"{evidence_set_id or 'missing'}#trading_date"],
        "quote_kline": [f"{snapshot_id}#market", f"{snapshot_id}#sources.tongdaxin"],
        "fundamentals": [f"{snapshot_id}#sources.tongdaxin.coverage", f"{snapshot_id}#market.advancers,decliners"],
        "news_announcements": [f"{snapshot_id}#sources.duanxianxia", f"{snapshot_id}#sources.lianban"],
        "sector_theme": [f"{snapshot_id}#topics", f"{snapshot_id}#market.topic_count_ge3"],
        "source_freshness": [f"{result_id}#sources", f"{evidence_set_id or 'missing'}#created_at,trading_date"],
    }
    errors = [f"data_gate_dimension_failed:{name}" for name, passed in checks.items() if not passed]
    if not evidence_set_id:
        errors.append("evidence_set_id_missing")
    return {
        "schema": "STOCK_DATA_GATE_V1",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "skill_id": ROOT.name,
        "effective_trading_date": effective_date,
        "latest_required_trading_date": latest_date,
        "evidence_set_id": evidence_set_id,
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
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--poster", action="store_true")
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    if os.environ.get("CODEX_STOCK_CANONICAL_EXECUTION") != "1":
        print(json.dumps({"schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1", "skill_id": ROOT.name, "status": "BLOCKED", "errors": ["canonical_execution_environment_missing"]}, ensure_ascii=False))
        return 2
    command = [sys.executable, str(LEGACY), "run", "--run-dir", str(run_dir)]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "ONESTOCK_STOCK_CANONICAL_CHILD": "1"}
    try:
        child = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=args.timeout, env=env)
        stdout, stderr, returncode = child.stdout, child.stderr, child.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {args.timeout}s"
        returncode = 124
    stdout_path = run_dir / "business_child.stdout.txt"
    stderr_path = run_dir / "business_child.stderr.txt"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    clean_child = False
    try:
        clean_child = json.loads(stdout.strip().splitlines()[-1]).get("status") == "CLEAN_PASS"
    except (IndexError, json.JSONDecodeError):
        pass
    sentiment_result = run_dir / "sentiment_result.json"
    sentiment_snapshot = run_dir / "sentiment_snapshot.json"
    validation_path = run_dir / "poster_validation.json"
    poster_path = run_dir / POSTER_NAME
    preview_path = run_dir / PREVIEW_NAME
    poster_status = "BLOCKED"
    data_gate = None
    data_gate_errors = []
    if returncode == 0 and clean_child and sentiment_result.is_file() and sentiment_snapshot.is_file():
        result_payload = json.loads(sentiment_result.read_text(encoding="utf-8"))
        snapshot_payload = json.loads(sentiment_snapshot.read_text(encoding="utf-8"))
        external_raw = os.environ.get("CODEX_SENTIMENT_POSTER_OUTPUT", "").strip()
        custom_poster_raw = os.environ.get("CODEX_SENTIMENT_CUSTOM_POSTER_SOURCE", "").strip()
        custom_audit_raw = os.environ.get("CODEX_SENTIMENT_CUSTOM_POSTER_AUDIT", "").strip()
        if custom_poster_raw or custom_audit_raw:
            if not custom_poster_raw or not custom_audit_raw:
                raise ValueError("custom_poster_source_and_audit_must_be_paired")
            bundle = render_audited_custom_poster(
                result_payload,
                snapshot_payload,
                run_dir,
                Path(custom_poster_raw),
                Path(custom_audit_raw),
                visual_inspected=os.environ.get("CODEX_POSTER_VISUAL_INSPECTED") == "1",
            )
        else:
            bundle = render_poster(
                result_payload,
                snapshot_payload,
                run_dir,
                Path(external_raw) if external_raw else None,
                visual_inspected=os.environ.get("CODEX_POSTER_VISUAL_INSPECTED") == "1",
            )
        poster_status = write_validation(bundle, validation_path)["status"]
        if os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS") == "CLEAN_PASS":
            data_gate = build_data_gate(sentiment_result, sentiment_snapshot, env)
            data_gate_errors = list(data_gate.get("errors") or [])
    accepted = (
        returncode == 0
        and clean_child
        and sentiment_result.is_file()
        and sentiment_snapshot.is_file()
        and poster_path.is_file()
        and preview_path.is_file()
        and validation_path.is_file()
        and poster_status == "CLEAN_PASS"
        and not data_gate_errors
    )
    result = {
        "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
        "skill_id": ROOT.name,
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "business_process": {
            "command": command,
            "returncode": returncode,
            "timed_out": returncode == 124,
            "failure_tokens": [],
        },
        "business_binding": {"path": str(LEGACY), "sha256": sha256(LEGACY)},
        "artifacts": {
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "snapshot": str(sentiment_snapshot),
            "sentiment_result": str(sentiment_result),
            "poster": str(poster_path),
            "preview": str(preview_path),
            "poster_validation": str(validation_path),
        },
        "errors": data_gate_errors,
    }
    if data_gate is not None:
        result["data_gate"] = data_gate
    (run_dir / "business_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
