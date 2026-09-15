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


def derive_validated_selection(stdout: str) -> dict:
    try:
        payload = json.loads(stdout.lstrip("\ufeff"))
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("child_stdout_not_single_json_object") from exc
    if not isinstance(payload, dict):
        raise ValueError("child_stdout_not_single_json_object")
    if payload.get("status") != "CLEAN_PASS":
        raise ValueError("child_status_not_clean")
    if payload.get("stage") != "generate_and_validate":
        raise ValueError("child_stage_not_validated_selection")

    generated = payload.get("generated")
    if not isinstance(generated, dict) or generated.get("ok") is not True:
        raise ValueError("generation_not_clean")
    if payload.get("validator_returncode") != 0:
        raise ValueError("validator_not_clean")
    try:
        validator_payload = json.loads(
            str(payload.get("validator_stdout") or "").lstrip("\ufeff")
        )
    except json.JSONDecodeError as exc:
        raise ValueError("validator_evidence_not_json") from exc
    if (
        not isinstance(validator_payload, dict)
        or validator_payload.get("status") != "CLEAN_PASS"
        or validator_payload.get("failures") not in ([], None)
    ):
        raise ValueError("validator_not_clean")

    trade_date = generated.get("trade_date")
    final_count = generated.get("final_count")
    task_dir = generated.get("task_dir")
    if not isinstance(trade_date, str) or len(trade_date) != 8 or not trade_date.isdigit():
        raise ValueError("validated_trade_date_missing")
    if isinstance(final_count, bool) or not isinstance(final_count, int) or final_count < 0:
        raise ValueError("validated_candidate_count_missing")
    if not isinstance(task_dir, str) or not task_dir.strip():
        raise ValueError("validated_task_dir_missing")

    return {
        "forecast_status": "VALIDATED_SELECTION",
        "selection_status": "VALIDATED_SELECTION",
        "trade_date": trade_date,
        "candidate_count": final_count,
        "task_dir": task_dir,
        "validator_evidence": {
            "validated": True,
            "returncode": 0,
            "status": validator_payload["status"],
            "failure_count": len(validator_payload.get("failures") or []),
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
    atomic_write_text(stdout_path, str(child["stdout"]))
    atomic_write_text(stderr_path, str(child["stderr"]))
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
    atomic_write_json(result_path, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
