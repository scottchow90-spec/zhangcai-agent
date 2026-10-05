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


def business_command(run_dir: Path, requested: list[str]) -> list[str]:
    values = list(requested)
    if values and values[0].casefold() in {"run", "generate", "auto"}:
        values = values[1:]
    if "--evidence" not in values:
        raise ValueError("baimao_evidence_argument_required")
    if "--output-dir" in values:
        raise ValueError("canonical_run_dir_override_forbidden")
    return [
        sys.executable,
        str(LEGACY_ENTRY),
        "run",
        "--",
        "run",
        *values,
        "--output-dir",
        str(run_dir),
    ]


def _business_payload(stdout: str) -> dict:
    try:
        payload = json.loads(stdout.strip())
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def build_business_artifact_manifest(
    run_dir: Path,
    payload: dict,
) -> dict:
    errors: list[str] = []
    if payload.get("status") != "CLEAN_PASS":
        errors.append("business_payload_status_not_clean")
    quality = payload.get("quality_gate")
    if not isinstance(quality, dict) or quality.get("status") != "CLEAN_PASS":
        errors.append("quality_gate_not_clean")
    declared = payload.get("artifacts")
    if not isinstance(declared, dict):
        errors.append("business_artifacts_missing")
        declared = {}
    records: list[dict] = []
    root = run_dir.resolve()
    for name in ("markdown", "word", "json"):
        raw = declared.get(name)
        path = Path(str(raw or "")).resolve()
        try:
            inside = os.path.commonpath((str(root), str(path))) == str(root)
        except ValueError:
            inside = False
        if not inside:
            errors.append(f"artifact_outside_run_dir:{name}")
            continue
        if not path.is_file() or path.stat().st_size <= 0:
            errors.append(f"artifact_missing:{name}")
            continue
        records.append({
            "name": name,
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return {
        "schema": "STOCK_BUSINESS_ARTIFACT_MANIFEST_V1",
        "skill_id": SKILL_ID,
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "validation": {
            "status": "CLEAN_PASS" if not errors else "BLOCKED",
            "quality_gate": quality if isinstance(quality, dict) else {},
        },
        "artifacts": records,
        "errors": errors,
    }


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
    try:
        command = business_command(run_dir, requested)
    except ValueError as exc:
        print(json.dumps({
            "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
            "skill_id": SKILL_ID,
            "status": "BLOCKED",
            "errors": [str(exc)],
        }, ensure_ascii=False))
        return 2
    child = run_child(command, args.timeout)
    stdout_path = run_dir / "business_child.stdout.txt"
    stderr_path = run_dir / "business_child.stderr.txt"
    stdout_path.write_text(str(child["stdout"]), encoding="utf-8")
    stderr_path.write_text(str(child["stderr"]), encoding="utf-8")
    combined = str(child["stdout"]) + "\n" + str(child["stderr"])
    failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    payload = _business_payload(str(child["stdout"]))
    manifest = build_business_artifact_manifest(run_dir, payload)
    manifest_path = run_dir / "business_artifact_manifest.json"
    if manifest["status"] == "CLEAN_PASS":
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    accepted = (
        child["returncode"] == 0
        and not failure_tokens
        and payload.get("status") == "CLEAN_PASS"
        and manifest["status"] == "CLEAN_PASS"
        and manifest_path.is_file()
    )
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
            "business_manifest": str(manifest_path),
        },
        "business_validation": manifest,
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
