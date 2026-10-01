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
FORBIDDEN_REPORT_TOKENS = (
    "OBSERVE",
    "not verified",
    "required_next_session",
    '"candidate": null',
    '"status": "BLOCKED"',
    '"status":"BLOCKED"',
    '"status": "DATA_REQUIRED"',
    '"status":"DATA_REQUIRED"',
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def business_command(run_dir: Path) -> list[str]:
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


def _is_a_share_stock(symbol: str, code: str, market: str) -> bool:
    if symbol != f"{code}.{market}" or len(code) != 6 or not code.isdigit():
        return False
    if market == "SZ":
        return code.startswith(("000", "001", "002", "003", "300", "301"))
    if market == "SH":
        return code.startswith(("600", "601", "603", "605", "688", "689"))
    return False


def derive_validated_selection(stdout: str) -> dict:
    try:
        child_payload = json.loads(stdout.lstrip("\ufeff"))
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("child_stdout_not_single_json_object") from exc
    if not isinstance(child_payload, dict) or child_payload.get("status") != "CLEAN_PASS":
        raise ValueError("child_status_not_clean")
    report_value = child_payload.get("report")
    if not isinstance(report_value, str) or not report_value.strip():
        raise ValueError("full_market_report_missing")
    report_path = Path(report_value).resolve()
    if not report_path.is_file():
        raise ValueError("full_market_report_missing")
    try:
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("full_market_report_invalid_json") from exc
    if not isinstance(report, dict):
        raise ValueError("full_market_report_invalid_json")
    serialized = json.dumps(report, ensure_ascii=False)
    forbidden = [token for token in FORBIDDEN_REPORT_TOKENS if token in serialized]
    if forbidden:
        raise ValueError(f"report_contains_unfinished_state:{','.join(forbidden)}")
    if report.get("status") != "CLEAN_PASS":
        raise ValueError("report_status_not_clean")
    if report.get("strategy_id") != "oversold-first-board-v1":
        raise ValueError("child_strategy_not_full_market")
    if report.get("data_source", {}).get("type") != "local_tdx_raw_daily":
        raise ValueError("report_data_source_not_local_tdx_daily")

    trade_date = report.get("latest_trade_date")
    if not isinstance(trade_date, str) or len(trade_date) != 8 or not trade_date.isdigit():
        raise ValueError("report_trade_date_invalid")
    universe = report.get("universe")
    scan_stats = universe.get("scan_stats") if isinstance(universe, dict) else None
    if (
        not isinstance(universe, dict)
        or not isinstance(scan_stats, dict)
        or int(universe.get("eligible_security_records") or 0) <= 1000
        or int(scan_stats.get("latest_trade_date") or 0) <= 1000
    ):
        raise ValueError("report_not_full_market_scan")

    selection = report.get("selection")
    candidates = selection.get("candidates") if isinstance(selection, dict) else None
    candidate_count = selection.get("candidate_count") if isinstance(selection, dict) else None
    if not isinstance(candidates, list) or isinstance(candidate_count, bool) or not isinstance(candidate_count, int):
        raise ValueError("candidate_collection_invalid")
    if candidate_count != len(candidates):
        raise ValueError("candidate_count_mismatch")
    selection_status = report.get("selection_status")
    expected_status = "SIGNAL" if candidates else "NO_SIGNAL"
    if selection_status != expected_status:
        raise ValueError("selection_status_count_conflict")

    verified_candidates: list[dict] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("candidate_not_object")
        symbol = str(candidate.get("symbol") or "")
        code = str(candidate.get("code") or "")
        market = str(candidate.get("market") or "")
        if symbol == "000001.SH" or not _is_a_share_stock(symbol, code, market):
            raise ValueError(f"index_candidate:{symbol}")
        if symbol in seen:
            raise ValueError(f"duplicate_candidate:{symbol}")
        seen.add(symbol)
        name = str(candidate.get("name") or "").strip()
        if not name or "\ufffd" in name:
            raise ValueError(f"candidate_name_invalid:{symbol}")
        score = candidate.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= float(score) <= 100:
            raise ValueError(f"candidate_score_invalid:{symbol}")
        if candidate.get("selection_status") != "SIGNAL":
            raise ValueError(f"candidate_status_invalid:{symbol}")
        metrics = candidate.get("metrics")
        if not isinstance(metrics, dict) or str(metrics.get("date")) != trade_date:
            raise ValueError(f"candidate_trade_date_invalid:{symbol}")
        rsi = metrics.get("pre_limit_rsi14")
        drawdown = metrics.get("pre_limit_drawdown_60_pct")
        prior_boards = metrics.get("prior_limit_up_count_20")
        if (
            isinstance(rsi, bool)
            or not isinstance(rsi, (int, float))
            or float(rsi) > 35.0
            or isinstance(drawdown, bool)
            or not isinstance(drawdown, (int, float))
            or float(drawdown) > -15.0
            or prior_boards != 0
        ):
            raise ValueError(f"candidate_not_oversold_first_board:{symbol}")
        source = candidate.get("source")
        if not isinstance(source, dict):
            raise ValueError(f"candidate_source_missing:{symbol}")
        source_path = Path(str(source.get("path") or "")).resolve()
        if not source_path.is_file():
            raise ValueError(f"candidate_source_missing:{symbol}")
        if source_path.stat().st_size != int(source.get("size") or -1):
            raise ValueError(f"candidate_source_size_mismatch:{symbol}")
        if sha256_file(source_path) != str(source.get("sha256") or ""):
            raise ValueError(f"candidate_source_hash_mismatch:{symbol}")
        verified_candidates.append({
            "symbol": symbol,
            "code": code,
            "market": market,
            "name": name,
            "score": score,
            "selection_status": "SIGNAL",
            "pre_limit_rsi14": rsi,
            "pre_limit_drawdown_60_pct": drawdown,
            "source_path": str(source_path),
            "source_sha256": source["sha256"],
        })

    validation = report.get("validation")
    if not isinstance(validation, dict) or validation.get("full_market_scan") is not True:
        raise ValueError("selector_not_full_market")
    if validation.get("candidate_count_matches") is not True or validation.get("unique_stock_candidates") is not True:
        raise ValueError("selector_validation_not_clean")
    return {
        "strategy_id": "oversold-first-board-v1",
        "selection_status": selection_status,
        "latest_trade_date": trade_date,
        "candidate_count": candidate_count,
        "candidates": verified_candidates,
        "report_evidence": {
            "path": str(report_path),
            "size": report_path.stat().st_size,
            "sha256": sha256_file(report_path),
        },
    }


def main() -> int:
    enable_atomic_path_writes()
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--timeout", type=int, default=300)
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

    command = business_command(run_dir)
    child = run_child(command, args.timeout)
    stdout_path = run_dir / "business_child.stdout.txt"
    stderr_path = run_dir / "business_child.stderr.txt"
    stdout_path.write_text(str(child["stdout"]), encoding="utf-8")
    stderr_path.write_text(str(child["stderr"]), encoding="utf-8")
    combined = str(child["stdout"]) + "\n" + str(child["stderr"])
    failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    selection: dict = {}
    validation_errors: list[str] = []
    if child["returncode"] == 0 and not failure_tokens:
        try:
            selection = derive_validated_selection(str(child["stdout"]))
        except ValueError as exc:
            validation_errors.append(str(exc))
    accepted = (
        child["returncode"] == 0
        and not failure_tokens
        and not validation_errors
        and bool(selection)
    )
    result = {
        "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
        "skill_id": SKILL_ID,
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        **selection,
        "business_process": {
            "command": command,
            "cwd": str(ROOT),
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
            "failure_tokens": failure_tokens,
            "validation_errors": validation_errors,
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
    result_path = run_dir / "business_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
