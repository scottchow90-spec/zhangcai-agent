#!/usr/bin/env python3
"""Canonical adapter for the point-in-time future hotspot forecast."""
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
from typing import Mapping

from forecast_gate import REQUIRED_DELIVERABLES, validate_delivery_manifest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = ROOT.name
LEGACY_ENTRY = ROOT / "scripts" / "legacy_codex_entry.py"
ALLOWED_FORECAST_STATUSES = {
    "VALIDATED_FORECAST",
    "PROVISIONAL_FORECAST",
    "DEGRADED_FORECAST",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_child_environment(
    deliverables_dir: Path,
    *,
    inherited: Mapping[str, str] | None = None,
) -> dict[str, str]:
    environment = dict(os.environ if inherited is None else inherited)
    environment.update(
        {
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
            "ONESTOCK_STOCK_CANONICAL_CHILD": "1",
            "SHORTLINE_CANONICAL_DELIVERABLES_DIR": str(deliverables_dir.resolve()),
        }
    )
    return environment


def run_child(command: list[str], timeout: int, environment: Mapping[str, str]) -> dict:
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=dict(environment),
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = (
            exc.stdout.decode("utf-8", "replace")
            if isinstance(exc.stdout, bytes)
            else exc.stdout or ""
        )
        stderr = (
            exc.stderr.decode("utf-8", "replace")
            if isinstance(exc.stderr, bytes)
            else exc.stderr or ""
        )
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


def parse_child_stdout(stdout: str) -> dict:
    try:
        payload = json.loads(stdout.strip())
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("child_stdout_not_single_json_object") from exc
    if not isinstance(payload, dict):
        raise ValueError("child_stdout_not_single_json_object")
    return payload


def validate_child_delivery(child: dict, deliverables_dir: Path) -> dict:
    errors: list[str] = []
    if child.get("status") != "CLEAN_PASS":
        errors.append("child_status_not_clean")
    forecast_status = str(child.get("forecast_status", ""))
    if forecast_status not in ALLOWED_FORECAST_STATUSES:
        errors.append("child_forecast_status_invalid")
    snapshot_id = str(child.get("snapshot_id", ""))
    resolved_trade_date = str(child.get("resolved_trade_date", ""))
    if not snapshot_id:
        errors.append("child_snapshot_id_missing")
    if not resolved_trade_date:
        errors.append("child_resolved_trade_date_missing")
    if child.get("requires_research_completion") is True:
        errors.append("child_requires_research_completion")
    expected_manifest = (deliverables_dir / "manifest.json").resolve()
    child_manifest = Path(str(child.get("manifest_path", ""))).resolve()
    if child_manifest != expected_manifest:
        errors.append("child_manifest_path_mismatch")
    for name in REQUIRED_DELIVERABLES:
        path = deliverables_dir / name
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"required_forecast_artifact_missing_or_empty:{name}")
    manifest: dict = {}
    if expected_manifest.is_file():
        try:
            manifest = json.loads(expected_manifest.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            errors.append("delivery_manifest_invalid")
    if manifest:
        gate = validate_delivery_manifest(manifest, deliverables_dir)
        errors.extend(gate["errors"])
        if str(manifest.get("snapshot_id", "")) != snapshot_id:
            errors.append("child_manifest_snapshot_mismatch")
        if str(manifest.get("resolved_trade_date", "")) != resolved_trade_date:
            errors.append("child_manifest_trade_date_mismatch")
        if str(manifest.get("forecast_status", "")) != forecast_status:
            errors.append("child_manifest_forecast_status_mismatch")
    return {
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "forecast_status": forecast_status or "BLOCKED",
        "snapshot_id": snapshot_id or None,
        "resolved_trade_date": resolved_trade_date or None,
        "manifest_path": str(expected_manifest),
        "errors": errors,
    }


def build_business_artifact_manifest(deliverables_dir: Path, delivery: dict) -> dict:
    errors = list(delivery.get("errors", []))
    records: list[dict] = []
    for name in REQUIRED_DELIVERABLES:
        path = (deliverables_dir / name).resolve()
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"business_manifest_artifact_missing:{name}")
            continue
        records.append(
            {
                "name": name,
                "path": str(path),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    status = "CLEAN_PASS" if delivery.get("status") == "CLEAN_PASS" and not errors else "BLOCKED"
    return {
        "schema": "STOCK_BUSINESS_ARTIFACT_MANIFEST_V1",
        "skill_id": SKILL_ID,
        "status": status,
        "forecast_status": delivery.get("forecast_status", "BLOCKED"),
        "snapshot_id": delivery.get("snapshot_id"),
        "validation": {"status": status, "forecast_delivery": delivery},
        "artifacts": records,
        "errors": errors,
    }


def main() -> int:
    enable_atomic_path_writes()
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("business_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    deliverables_dir = run_dir / "deliverables"

    if os.environ.get("CODEX_STOCK_CANONICAL_EXECUTION") != "1":
        print(
            json.dumps(
                {
                    "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
                    "skill_id": SKILL_ID,
                    "status": "BLOCKED",
                    "forecast_status": "BLOCKED",
                    "errors": ["canonical_execution_environment_missing"],
                },
                ensure_ascii=False,
            )
        )
        return 2
    if not LEGACY_ENTRY.is_file():
        print(
            json.dumps(
                {
                    "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
                    "skill_id": SKILL_ID,
                    "status": "BLOCKED",
                    "forecast_status": "BLOCKED",
                    "errors": [f"legacy_entry_missing:{LEGACY_ENTRY}"],
                },
                ensure_ascii=False,
            )
        )
        return 2

    requested = list(args.business_args)
    if requested and requested[0] == "--":
        requested = requested[1:]
    command = [sys.executable, str(LEGACY_ENTRY), "run"]
    if requested:
        command.extend(["--", *requested])
    child = run_child(
        command,
        args.timeout,
        build_child_environment(deliverables_dir),
    )
    stdout_path = run_dir / "business_child.stdout.txt"
    stderr_path = run_dir / "business_child.stderr.txt"
    stdout_path.write_text(str(child["stdout"]), encoding="utf-8")
    stderr_path.write_text(str(child["stderr"]), encoding="utf-8")

    child_payload: dict = {}
    parse_errors: list[str] = []
    try:
        child_payload = parse_child_stdout(str(child["stdout"]))
    except ValueError as exc:
        parse_errors.append(str(exc))
    delivery = (
        validate_child_delivery(child_payload, deliverables_dir)
        if child_payload
        else {
            "status": "BLOCKED",
            "forecast_status": "BLOCKED",
            "snapshot_id": None,
            "resolved_trade_date": None,
            "manifest_path": str((deliverables_dir / "manifest.json").resolve()),
            "errors": [],
        }
    )
    business_manifest = build_business_artifact_manifest(deliverables_dir, delivery)
    business_manifest_path = run_dir / "business_artifact_manifest.json"
    if business_manifest["status"] == "CLEAN_PASS":
        business_manifest_path.write_text(
            json.dumps(business_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    errors = [*parse_errors, *delivery["errors"]]
    if child["returncode"] != 0:
        errors.append(f"child_returncode_nonzero:{child['returncode']}")
    if business_manifest["status"] != "CLEAN_PASS":
        errors.append("business_artifact_manifest_not_clean")
    accepted = not errors
    artifacts = {
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "manifest": delivery["manifest_path"],
        "business_artifact_manifest": str(business_manifest_path),
        "deliverables": {
            name: str((deliverables_dir / name).resolve())
            for name in REQUIRED_DELIVERABLES
        },
    }
    result = {
        "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
        "skill_id": SKILL_ID,
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "forecast_status": delivery["forecast_status"],
        "snapshot_id": delivery["snapshot_id"],
        "resolved_trade_date": delivery["resolved_trade_date"],
        "manifest_path": delivery["manifest_path"],
        "warnings": child_payload.get("warnings", []) if child_payload else [],
        "errors": errors,
        "business_process": {
            "command": command,
            "cwd": str(ROOT),
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
        },
        "business_binding": {
            "path": str(LEGACY_ENTRY),
            "sha256": sha256_file(LEGACY_ENTRY),
        },
        "artifacts": artifacts,
    }
    (run_dir / "business_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
