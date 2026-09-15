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


def build_delivery_manifest(run_dir: Path, child: dict) -> tuple[Path | None, list[str]]:
    if SKILL_ID != "limit-up-review" or child["returncode"] != 0:
        return None, []

    errors: list[str] = []
    preflight_path: Path | None = None
    for line in str(child["stdout"]).splitlines():
        candidate = Path(line.strip())
        if candidate.name == "preflight_audit.json" and candidate.is_file():
            preflight_path = candidate.resolve()
            break
    if preflight_path is None:
        return None, ["delivery_manifest_preflight_path_missing"]

    entry_result_path = preflight_path.parent / "entry_result.json"
    try:
        entry_result = json.loads(entry_result_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [f"delivery_manifest_entry_result_unreadable:{type(exc).__name__}"]

    if entry_result.get("status") != "CLEAN_PASS":
        errors.append("delivery_manifest_entry_result_not_clean")

    report_path = Path(str(entry_result.get("report", ""))).resolve()
    analysis_path = Path(str(entry_result.get("business_result", ""))).resolve()
    final_gate_path = Path(str(entry_result.get("final_gate_result", ""))).resolve()
    template_path = ROOT / "TEMPLATE.md"
    validator_path = ROOT / "scripts" / "limit_up_review_final_gate.py"
    poster_path: Path | None = None
    poster_audit_path: Path | None = None
    poster_validation_path: Path | None = None
    poster_template_path: Path | None = None
    poster_generator_path: Path | None = None
    poster_validator_path: Path | None = None
    poster_source_path: Path | None = None
    required_files = {
        "report": report_path,
        "business_result": analysis_path,
        "final_gate": final_gate_path,
        "template": template_path,
        "validator": validator_path,
    }
    for label, path in required_files.items():
        if not path.is_file():
            errors.append(f"delivery_manifest_{label}_missing:{path}")

    final_gate: dict = {}
    if final_gate_path.is_file():
        try:
            final_gate = json.loads(final_gate_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"delivery_manifest_final_gate_unreadable:{type(exc).__name__}")
    if final_gate.get("status") != "CLEAN_PASS":
        errors.append("delivery_manifest_final_gate_not_clean")

    poster_output = os.environ.get("LIMITUP_POSTER_OUTPUT", "").strip()
    if poster_output and not errors:
        poster_path = Path(poster_output).resolve()
        poster_audit_path = run_dir / "poster_layout_audit.json"
        poster_validation_path = run_dir / "poster_validation.json"
        poster_template_path = ROOT / "POSTER_TEMPLATE.md"
        poster_generator_path = ROOT / "scripts" / "generate_limit_up_review_poster.py"
        poster_validator_path = ROOT / "scripts" / "validate_limit_up_review_poster.py"
        poster_source_path = Path(
            os.environ.get("LIMITUP_POSTER_SOURCE_DOCX", str(report_path))
        ).resolve()
        poster_required = {
            "poster_template": poster_template_path,
            "poster_generator": poster_generator_path,
            "poster_validator": poster_validator_path,
            "poster_source": poster_source_path,
        }
        for label, path in poster_required.items():
            if not path.is_file():
                errors.append(f"delivery_manifest_{label}_missing:{path}")

        if not errors:
            poster_path.parent.mkdir(parents=True, exist_ok=True)
            generate = subprocess.run(
                [
                    sys.executable,
                    str(poster_generator_path),
                    "--business-result",
                    str(analysis_path),
                    "--source-docx",
                    str(poster_source_path),
                    "--output",
                    str(poster_path),
                    "--audit-json",
                    str(poster_audit_path),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
            (run_dir / "poster_generate.stdout.txt").write_text(
                generate.stdout,
                encoding="utf-8",
            )
            (run_dir / "poster_generate.stderr.txt").write_text(
                generate.stderr,
                encoding="utf-8",
            )
            if generate.returncode != 0:
                errors.append(f"poster_generate_failed:{generate.returncode}")

        if not errors:
            validate = subprocess.run(
                [
                    sys.executable,
                    str(poster_validator_path),
                    "--poster",
                    str(poster_path),
                    "--audit-json",
                    str(poster_audit_path),
                    "--report-json",
                    str(analysis_path),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
            poster_validation_path.write_text(validate.stdout, encoding="utf-8")
            (run_dir / "poster_validate.stderr.txt").write_text(
                validate.stderr,
                encoding="utf-8",
            )
            if validate.returncode != 0:
                errors.append(f"poster_validation_failed:{validate.returncode}")
            else:
                try:
                    poster_validation = json.loads(validate.stdout)
                except json.JSONDecodeError:
                    poster_validation = {}
                    errors.append("poster_validation_json_invalid")
                if poster_validation.get("status") != "CLEAN_PASS":
                    errors.append("poster_validation_not_clean")

    if errors:
        return None, errors

    def record(path: Path) -> dict:
        return {
            "status": "CLEAN_PASS",
            "path": str(path.resolve()),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
            "errors": [],
        }

    manifest = {
        "schema": "STOCK_DELIVERY_MANIFEST_V1",
        "status": "CLEAN_PASS",
        "skill_id": SKILL_ID,
        "run_id": entry_result.get("run_id"),
        "validation": {
            "status": "CLEAN_PASS",
            "errors": [],
        },
        "artifact": record(report_path),
        "business_result": record(analysis_path),
        "final_gate": record(final_gate_path),
        "template": record(template_path),
        "validator": record(validator_path),
        "errors": [],
    }
    if (
        poster_path is not None
        and poster_audit_path is not None
        and poster_validation_path is not None
        and poster_template_path is not None
        and poster_generator_path is not None
        and poster_validator_path is not None
        and poster_source_path is not None
    ):
        manifest["artifacts"] = [
            record(report_path),
            record(poster_path),
        ]
        manifest["poster"] = record(poster_path)
        manifest["poster_audit"] = record(poster_audit_path)
        manifest["poster_validation"] = record(poster_validation_path)
        manifest["poster_template"] = record(poster_template_path)
        manifest["poster_generator"] = record(poster_generator_path)
        manifest["poster_validator"] = record(poster_validator_path)
        manifest["poster_source"] = record(poster_source_path)
    manifest_path = run_dir / "delivery_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path, []


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
    delivery_manifest, manifest_errors = build_delivery_manifest(run_dir, child)
    combined = str(child["stdout"]) + "\n" + str(child["stderr"])
    failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    accepted = child["returncode"] == 0 and not failure_tokens and not manifest_errors
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
            "delivery_manifest": str(delivery_manifest) if delivery_manifest else "",
        },
        "manifest_errors": manifest_errors,
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
