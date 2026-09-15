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

from _date_utils import resolve_latest_trade_date


ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = ROOT.name
LEGACY_ENTRY = ROOT / "scripts" / "legacy_codex_entry.py"
BUNDLED_AUTHORING_PYTHON = Path(sys.executable)
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
SOURCE_FETCH_MAX_AGE_SECONDS = 24 * 60 * 60
SOURCE_FETCH_FUTURE_SKEW_SECONDS = 5 * 60


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _iso_trade_date(value: object) -> str:
    text = str(value or "").strip()
    if len(text) == 8 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d").date().isoformat()
    return datetime.strptime(text, "%Y-%m-%d").date().isoformat()


def _is_fresh_source_timestamp(
    value: object,
    *,
    now: datetime | None = None,
) -> bool:
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        return False
    reference = now or datetime.now().astimezone()
    if reference.tzinfo is None:
        return False
    age_seconds = reference.timestamp() - parsed.timestamp()
    return (
        -SOURCE_FETCH_FUTURE_SKEW_SECONDS
        <= age_seconds
        <= SOURCE_FETCH_MAX_AGE_SECONDS
    )


def _load_bound_json(path_value: object, expected_sha256: object) -> tuple[Path | None, dict, list[str]]:
    errors: list[str] = []
    path = Path(str(path_value or "")).resolve()
    payload: dict = {}
    if not path.is_file():
        return None, payload, [f"bound_json_missing:{path}"]
    actual_sha256 = sha256_file(path)
    if actual_sha256 != str(expected_sha256 or "").strip().casefold():
        errors.append(f"bound_json_hash_mismatch:{path.name}")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"bound_json_invalid:{path.name}:{type(exc).__name__}")
    else:
        if isinstance(loaded, dict):
            payload = loaded
        else:
            errors.append(f"bound_json_not_object:{path.name}")
    return path, payload, errors


def build_full_data_gate(evidence_path: Path) -> dict:
    evidence_set_id = os.environ.get("CODEX_STOCK_EVIDENCE_SET_ID", "").strip()
    evidence_date_raw = os.environ.get("CODEX_STOCK_EVIDENCE_TRADING_DATE", "").strip()
    shared_status = os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS", "").strip()
    errors: list[str] = []
    evidence: dict = {}
    try:
        loaded = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"data_evidence_invalid:{type(exc).__name__}")
    else:
        if isinstance(loaded, dict):
            evidence = loaded
        else:
            errors.append("data_evidence_not_object")

    raw_path, raw, raw_errors = _load_bound_json(
        evidence.get("business_data_path"),
        evidence.get("business_data_sha256"),
    )
    analysis_path, analyzed, analysis_errors = _load_bound_json(
        evidence.get("analysis_path"),
        evidence.get("analysis_sha256"),
    )
    errors.extend(raw_errors)
    errors.extend(analysis_errors)
    try:
        effective_date = _iso_trade_date(evidence.get("trade_date"))
    except (TypeError, ValueError):
        effective_date = ""
        errors.append("effective_trading_date_invalid")
    try:
        latest_required_date = _iso_trade_date(evidence_date_raw)
    except (TypeError, ValueError):
        latest_required_date = ""
        errors.append("evidence_trading_date_invalid")

    strict_stocks = analyzed.get("zt_scored") if isinstance(analyzed.get("zt_scored"), list) else []
    picks = analyzed.get("picks") if isinstance(analyzed.get("picks"), list) else []
    lines = analyzed.get("lines") if isinstance(analyzed.get("lines"), list) else []
    qsyb_collection = raw.get("qsyb_collection") if isinstance(raw.get("qsyb_collection"), dict) else {}
    rdxz_collection = raw.get("rdxz_collection") if isinstance(raw.get("rdxz_collection"), dict) else {}
    risk_collection = raw.get("risk_collection") if isinstance(raw.get("risk_collection"), dict) else {}
    sources = evidence.get("sources") if isinstance(evidence.get("sources"), list) else []
    evidence_digest = sha256_file(evidence_path) if evidence_path.is_file() else "missing"
    evidence_ref = f"sha256:{evidence_digest}"
    raw_ref = f"sha256:{sha256_file(raw_path)}" if raw_path is not None else "missing"
    analysis_ref = f"sha256:{sha256_file(analysis_path)}" if analysis_path is not None else "missing"

    checks = {
        "identity": (
            evidence.get("status") == "PASS"
            and bool(strict_stocks)
            and all(
                len(str(stock.get("code") or "")) == 6
                and bool(str(stock.get("name") or "").strip())
                for stock in strict_stocks
            )
        ),
        "effective_trading_date": (
            bool(effective_date)
            and effective_date == latest_required_date
            and evidence.get("business_data_trade_date") == effective_date
            and evidence.get("market_date") == effective_date
        ),
        "quote_kline": (
            int(evidence.get("limit_up_count") or 0) > 0
            and int(evidence.get("local_tdx_limit_up_count") or 0) > 0
            and int(evidence.get("strict_intersection_count") or -1) == len(strict_stocks)
            and all(
                stock.get("k_line_verify") == "PASS"
                and stock.get("k_line_detail", {}).get("source_kind") == "TDX_LOCAL_DAY"
                for stock in strict_stocks
            )
        ),
        "fundamentals": (
            int(evidence.get("risk_review_error_count", -1)) == 0
            and int(evidence.get("risk_review_complete_count") or -1) == len(strict_stocks)
            and int(risk_collection.get("review_complete_codes") or -1)
            == int(risk_collection.get("codes_probed") or -2)
            and risk_collection.get("errors") == []
            and all(stock.get("risk_review_complete") is True for stock in strict_stocks)
        ),
        "news_announcements": (
            int(qsyb_collection.get("review_complete_codes") or -1)
            == int(qsyb_collection.get("codes_probed") or -2)
            and qsyb_collection.get("errors") == []
            and int(rdxz_collection.get("rows") or 0) > 0
            and rdxz_collection.get("errors") == []
            and all(
                stock.get("qsyb_bound") is True
                and stock.get("rdxz_bound") is True
                for stock in picks
            )
        ),
        "sector_theme": (
            bool(lines)
            and all(str(row.get("line") or "").strip() for row in lines)
            and all(
                str(stock.get("line") or "").strip()
                and str(stock.get("topic") or "").strip()
                for stock in picks
            )
        ),
        "source_freshness": (
            shared_status == "CLEAN_PASS"
            and bool(evidence_set_id)
            and bool(sources)
            and all(source.get("trade_date") == latest_required_date for source in sources)
            and _is_fresh_source_timestamp(evidence.get("data_cutoff"))
            and all(
                _is_fresh_source_timestamp(source.get("fetched_at"))
                for source in sources
            )
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
        "identity": [f"{raw_ref}#zt_pool", f"{analysis_ref}#zt_scored"],
        "effective_trading_date": [f"{evidence_ref}#trade_date", f"{evidence_set_id or 'missing'}#trading_date"],
        "quote_kline": [f"{analysis_ref}#zt_scored.k_line_detail", f"{evidence_ref}#strict_intersection_count"],
        "fundamentals": [f"{raw_ref}#risk_collection", f"{analysis_ref}#zt_scored.risk_result"],
        "news_announcements": [f"{raw_ref}#qsyb_collection", f"{raw_ref}#rdxz_collection"],
        "sector_theme": [f"{analysis_ref}#lines", f"{analysis_ref}#picks.topic"],
        "source_freshness": [f"{evidence_ref}#sources", f"{evidence_set_id or 'missing'}#created_at"],
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


def business_command(run_dir: Path, args: argparse.Namespace) -> list[str]:
    if SKILL_ID == "a-share-limit-up-mining":
        date = args.date or resolve_latest_trade_date()
        output_dir = Path(args.out).resolve() if args.out else run_dir / "business-output"
        if args.mode == "daily":
            command = [
                sys.executable,
                str(LEGACY_ENTRY),
                "run",
                "--mode",
                "daily",
                "--date",
                date,
                "--out",
                str(output_dir),
            ]
            if args.manual_confirm:
                command.append("--manual-confirm")
            return command
        if args.mode == "research":
            command = [
                sys.executable,
                str(LEGACY_ENTRY),
                "run",
                "--mode",
                args.mode,
                "--date",
                date,
                "--out",
                str(output_dir),
                "--min-total-score",
                str(args.min_total_score),
                "--k-line-mode",
                args.k_line_mode,
            ]
            if args.manual_confirm:
                command.append("--manual-confirm")
            if args.risk_json:
                command.extend(["--risk-json", args.risk_json])
            if args.skip_infra:
                command.append("--skip-infra")
            if args.diagnostic:
                command.append("--diagnostic")
            return command

        command = [
            sys.executable,
            str(LEGACY_ENTRY),
            "run",
            "--mode",
            "full",
            "--date",
            date,
            "--manual-confirm",
            "--authoring-python",
            str(args.authoring_python or BUNDLED_AUTHORING_PYTHON),
            "--data-evidence",
            str(args.data_evidence or run_dir / f"stock-data-evidence-{date}.json"),
            "--out-dir",
            str(output_dir),
        ]
        if args.template:
            command.extend(["--template", args.template])
        if args.skip_collect:
            command.append("--skip-collect")
        if args.skip_build:
            command.append("--skip-build")
        if args.skip_gate:
            command.append("--skip-gate")
        if args.diagnostic:
            command.append("--diagnostic")
        return command
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
    return [sys.executable, str(LEGACY_ENTRY), *overrides.get(SKILL_ID, ["run"])]


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
    parser.add_argument("--timeout", type=int, default=1500)
    parser.add_argument("--mode", choices=("daily", "full", "research"), default="full")
    parser.add_argument("--date")
    parser.add_argument("--manual-confirm", action="store_true")
    parser.add_argument("--out")
    parser.add_argument("--min-total-score", type=int, default=70)
    parser.add_argument("--k-line-mode", choices=("limit", "connected"), default="connected")
    parser.add_argument("--risk-json")
    parser.add_argument("--skip-infra", action="store_true")
    parser.add_argument("--authoring-python")
    parser.add_argument("--data-evidence")
    parser.add_argument("--template")
    parser.add_argument("--skip-collect", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-gate", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
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

    command = business_command(run_dir, args)
    child = run_child(command, args.timeout)
    stdout_path = run_dir / "business_child.stdout.txt"
    stderr_path = run_dir / "business_child.stderr.txt"
    stdout_path.write_text(str(child["stdout"]), encoding="utf-8")
    stderr_path.write_text(str(child["stderr"]), encoding="utf-8")
    combined = str(child["stdout"]) + "\n" + str(child["stderr"])
    failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    evidence_enabled = bool(
        os.environ.get("CODEX_STOCK_EVIDENCE_SET_ID")
        or os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS")
    )
    data_gate = None
    if evidence_enabled and SKILL_ID == "a-share-limit-up-mining" and args.mode == "full":
        evidence_path = Path(command[command.index("--data-evidence") + 1]).resolve()
        data_gate = build_full_data_gate(evidence_path)
    data_gate_errors = list(data_gate.get("errors", [])) if data_gate else []
    delivery_artifact = None
    delivery_errors: list[str] = []
    if SKILL_ID == "a-share-limit-up-mining" and args.mode == "full":
        date = command[command.index("--date") + 1]
        date_pretty = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        output_dir = Path(command[command.index("--out-dir") + 1]).resolve()
        docx_path = output_dir / f"连板挖掘_{date_pretty}.docx"
        if docx_path.is_file():
            delivery_artifact = {
                "path": str(docx_path),
                "size": docx_path.stat().st_size,
                "sha256": sha256_file(docx_path),
            }
        else:
            delivery_errors.append("delivery_docx_missing")
    accepted = (
        child["returncode"] == 0
        and not failure_tokens
        and not delivery_errors
        and not data_gate_errors
    )
    artifacts = {
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }
    if delivery_artifact is not None:
        artifacts["docx"] = delivery_artifact
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
        "artifacts": artifacts,
    }
    if SKILL_ID == "a-share-limit-up-mining" and args.mode == "full":
        result["delivery_validation"] = {
            "status": "CLEAN_PASS" if not delivery_errors else "BLOCKED",
            "errors": delivery_errors,
        }
    if data_gate is not None:
        result["data_gate"] = data_gate
    if data_gate_errors:
        result["errors"] = data_gate_errors
    result_path = run_dir / "business_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
