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
from datetime import datetime, timedelta
from pathlib import Path
_stock_adapter_shared_scripts = str(_OneStockEmbeddedPath(__file__).resolve().parents[3] / "scripts")
if _stock_adapter_shared_scripts not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _stock_adapter_shared_scripts)
from stock_adapter_io import atomic_write_json, atomic_write_text, enable_atomic_path_writes

from run_feilong_block_resonance import (
    HISTORICAL_FORMULA_EVIDENCE_MANIFEST,
    HISTORICAL_FORMULA_EVIDENCE_MANIFEST_SHA256,
    canonical_json_sha256,
    load_historical_formula_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = ROOT.name
LEGACY_ENTRY = ROOT / "scripts" / "legacy_codex_entry.py"
HOME = ROOT.parents[1]
SKILLS_ROOT = HOME / "harness-skills"
DUANXIANXIA_CLIENT = SKILLS_ROOT / "a-share-hotspot-sentiment-analysis" / "scripts" / "duanxianxia_client.ps1"
LIANBAN_CLIENT = HOME / "scripts" / "lianban_daily_client.py"
SCAN_JSON = HOME / "reports" / "2026-06-03_five_dimension_feilong_block_hardening" / "feilong_block_resonance_scan.json"
GLOBAL_SCORE_CONTRACT = SKILLS_ROOT / "stock-unified" / "references" / "short_term_strong_stock_scoring_contract.json"
GLOBAL_SCORE_CONTRACT_SHA256 = hashlib.sha256(GLOBAL_SCORE_CONTRACT.read_bytes()).hexdigest()
SCORE_CONTRACT_VERSION = "A-SHARE-STRONG-26F-100-V6.1"
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


def refresh_duanxianxia(run_dir: Path) -> dict:
    snapshot = run_dir / "duanxianxia-mainline.json"
    command = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(DUANXIANXIA_CLIENT), "-Output", str(snapshot),
    ]
    try:
        completed = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        payload = json.loads(snapshot.read_text(encoding="utf-8")) if snapshot.is_file() else {}
        required = ("ztlive", "ztplate", "ztpool", "platechart1", "platechart2", "amount")
        failed = [name for name in required if payload.get("datasets", {}).get(name, {}).get("success") is not True]
        status = "CLEAN_PASS" if completed.returncode == 0 and not failed else "DEGRADED"
        return {
            "status": status,
            "command": command,
            "returncode": completed.returncode,
            "path": str(snapshot),
            "size": snapshot.stat().st_size if snapshot.is_file() else 0,
            "failed_datasets": failed,
            "source_url": payload.get("source_page", "https://duanxianxia.com/web/main"),
            "stderr": (completed.stderr or "")[-1000:],
        }
    except Exception as exc:
        return {
            "status": "DEGRADED", "command": command, "returncode": 125,
            "path": str(snapshot), "size": 0, "failed_datasets": ["refresh_failed"],
            "source_url": "https://duanxianxia.com/web/main", "stderr": f"{type(exc).__name__}: {exc}",
        }


def refresh_lianban_history(run_dir: Path) -> dict:
    snapshots: list[dict] = []
    attempts: list[dict] = []
    for offset in range(1, 11):
        target = (datetime.now().date() - timedelta(days=offset)).isoformat()
        output = run_dir / f"lianban-{target}.json"
        command = [sys.executable, str(LIANBAN_CLIENT), "--date", target, "--output", str(output)]
        try:
            completed = subprocess.run(
                command,
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45,
            )
        except subprocess.TimeoutExpired as exc:
            attempts.append({
                "date": target,
                "returncode": 124,
                "status": "DEGRADED",
                "error": f"TimeoutExpired: {exc}",
            })
            continue
        except OSError as exc:
            attempts.append({
                "date": target,
                "returncode": 125,
                "status": "DEGRADED",
                "error": f"{type(exc).__name__}: {exc}",
            })
            continue
        try:
            payload = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else {}
        except (OSError, json.JSONDecodeError):
            payload = {}
        attempts.append({"date": target, "returncode": completed.returncode, "status": payload.get("status", "DEGRADED")})
        if completed.returncode == 0 and payload.get("status") == "CLEAN_PASS":
            snapshots.append(payload)
            if len(snapshots) >= 3:
                break
    combined_path = run_dir / "lianban-history.json"
    status = "CLEAN_PASS" if len(snapshots) >= 2 else "DEGRADED"
    combined_path.write_text(json.dumps({"status": status, "snapshots": snapshots, "attempts": attempts}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": status, "path": str(combined_path), "snapshot_count": len(snapshots), "attempts": attempts}


def validate_mainline_report() -> list[str]:
    if not SCAN_JSON.is_file():
        return ["mainline_report_missing"]
    try:
        report = json.loads(SCAN_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["mainline_report_unreadable"]
    market = report.get("mainline_market", {})
    errors: list[str] = []
    if report.get("status") != "CLEAN_PASS":
        errors.append("mainline_execution_not_clean")
    if market.get("model_version") != "CORE-MAINLINE-100-V2":
        errors.append("mainline_model_binding_missing")
    results = report.get("all_results", [])
    if not results or any("mainline_scoring" not in item for item in results):
        errors.append("per_stock_mainline_evidence_missing")
        return errors
    dimensions = [item.get("mainline_scoring", {}) for item in results]
    eligible_count = sum(item.get("decision_eligible") is True for item in results)
    authenticity_count = sum(
        item.get("stock_fit", {}).get("status") == "VERIFIED"
        for item in dimensions
    )
    gate_failed_count = sum(item.get("status") == "GATE_FAILED" for item in dimensions)
    degraded_count = sum(item.get("status") == "DEGRADED" for item in dimensions)
    score_data_required_count = sum(item.get("score_status") == "DATA_REQUIRED" for item in results)
    score_handoff = report.get("short_term_score", {})
    if (
        score_handoff.get("status") != "CLEAN_PASS"
        or score_handoff.get("version") != SCORE_CONTRACT_VERSION
        or score_handoff.get("global_contract_sha256") != GLOBAL_SCORE_CONTRACT_SHA256
        or score_handoff.get("fundamental_positive_weight") != 0
        or int(score_handoff.get("verified_count", 0)) + int(score_handoff.get("hard_excluded_count", 0)) != len(results)
    ):
        errors.append("short_term_score_handoff_mismatch")
    for index, item in enumerate(results, 1):
        if item.get("score_status") != "VERIFIED":
            continue
        contract = item.get("score_contract", {})
        if (
            contract.get("version") != SCORE_CONTRACT_VERSION
            or contract.get("global_contract_sha256") != GLOBAL_SCORE_CONTRACT_SHA256
            or contract.get("fundamental_positive_weight") != 0
            or len(item.get("dimension_scores", [])) != 26
            or len(item.get("risk_items", [])) != 15
            or len(item.get("hard_exclusions", [])) != 7
        ):
            errors.append(f"candidate_{index}_short_term_score_contract_mismatch")
    if int(report.get("scan_count", 0) or 0) != len(results):
        errors.append("mainline_scan_count_mismatch")
    expected_counts = {
        "verified_stock_count": eligible_count,
        "authenticity_verified_stock_count": authenticity_count,
        "gate_failed_stock_count": gate_failed_count,
        "degraded_stock_count": degraded_count,
    }
    for field, expected in expected_counts.items():
        if int(market.get(field, -1) or 0) != expected:
            errors.append(f"mainline_{field}_mismatch")
    if authenticity_count != len(results):
        errors.append("mainline_stock_authenticity_incomplete")

    decision_status = report.get("decision_status")
    if decision_status == "SIGNAL_FOUND":
        if market.get("status") != "VERIFIED" or eligible_count <= 0:
            errors.append("signal_found_without_verified_candidate")
    elif decision_status == "NO_SIGNAL":
        if degraded_count > 0:
            errors.append("no_signal_contains_degraded_candidate")
        if (
            market.get("status") != "GATE_FAILED"
            or eligible_count != 0
            or gate_failed_count != len(results)
        ):
            errors.append("no_signal_not_proven_by_complete_hard_gate_failures")
    elif decision_status == "DATA_REQUIRED":
        reasons = market.get("data_required_reasons", [])
        if eligible_count != 0 or (degraded_count <= 0 and score_data_required_count <= 0) or not reasons:
            errors.append("data_required_decision_boundary_invalid")
    else:
        errors.append("mainline_decision_status_invalid")
    return errors


def validate_formula_evidence_report(report: dict) -> list[str]:
    results = report.get("all_results", []) if isinstance(report.get("all_results"), list) else []
    errors: list[str] = []
    if not results:
        return ["formula_evidence_results_missing"]
    historical_results = [
        item for item in results
        if item.get("formula_evidence", {}).get("mode") == "historical_exact_input_reuse"
    ]
    allowed_modes = {"live_tq_execution", "historical_exact_input_reuse"}
    for item in results:
        symbol = str(item.get("symbol", ""))
        evidence = item.get("formula_evidence", {})
        if evidence.get("mode") not in allowed_modes:
            errors.append(f"formula_evidence_mode_invalid:{symbol}")
        if item.get("five_formula_ok") is not True:
            errors.append(f"required_formula_failure_present:{symbol}")
    if not historical_results:
        return errors

    rows = [{"code": str(item.get("symbol", ""))[:6], "symbol": str(item.get("symbol", ""))} for item in results]
    audit, scans = load_historical_formula_evidence(
        rows,
        HISTORICAL_FORMULA_EVIDENCE_MANIFEST,
        HISTORICAL_FORMULA_EVIDENCE_MANIFEST_SHA256,
        str(report.get("trade_date", "")),
    )
    if audit.get("status") != "VERIFIED":
        errors.append("historical_formula_evidence_revalidation_failed")
        errors.extend(f"historical_formula_evidence:{error}" for error in audit.get("errors", []))
    report_audit = report.get("formula_evidence", {})
    if (
        report_audit.get("status") != "VERIFIED"
        or report_audit.get("manifest", {}).get("sha256") != HISTORICAL_FORMULA_EVIDENCE_MANIFEST_SHA256
        or report_audit.get("source_artifact", {}).get("matched") is not True
        or report_audit.get("source_receipt", {}).get("matched") is not True
        or report_audit.get("recovery_provenance", {}).get("matched") is not True
        or report_audit.get("candidate_binding", {}).get("matched") is not True
        or report_audit.get("trade_date_binding", {}).get("matched") is not True
        or report_audit.get("kline_binding", {}).get("matched") is not True
        or report_audit.get("formula_executor_binding", {}).get("matched") is not True
        or report_audit.get("source_receipt_artifact_binding", {}).get("matched") is not True
    ):
        errors.append("historical_formula_report_audit_invalid")
    expected_reuse_manifest = audit.get("reuse_evidence_manifest", {})
    expected_reuse_hash = audit.get("reuse_evidence_manifest_sha256", "")
    if (
        not expected_reuse_manifest
        or canonical_json_sha256(expected_reuse_manifest) != expected_reuse_hash
        or report_audit.get("reuse_evidence_manifest") != expected_reuse_manifest
        or report_audit.get("reuse_evidence_manifest_sha256") != expected_reuse_hash
    ):
        errors.append("historical_formula_report_reuse_manifest_mismatch")
    for item in historical_results:
        symbol = str(item.get("symbol", ""))
        evidence = item.get("formula_evidence", {})
        if evidence.get("historical_evidence_status") != "VERIFIED":
            errors.append(f"historical_formula_status_invalid:{symbol}")
        if evidence.get("historical_manifest_sha256") != HISTORICAL_FORMULA_EVIDENCE_MANIFEST_SHA256:
            errors.append(f"historical_formula_manifest_binding_mismatch:{symbol}")
        if evidence.get("reuse_evidence_manifest_sha256") != expected_reuse_hash:
            errors.append(f"historical_formula_reuse_manifest_binding_mismatch:{symbol}")
        if evidence.get("source_receipt_sha256") != audit.get("source_receipt", {}).get("sha256"):
            errors.append(f"historical_formula_source_receipt_binding_mismatch:{symbol}")
        if evidence.get("source_artifact_sha256") != audit.get("source_artifact", {}).get("sha256"):
            errors.append(f"historical_formula_source_artifact_binding_mismatch:{symbol}")
        if evidence.get("immutable_line_sha256") != audit.get("recovery_provenance", {}).get("line_sha256"):
            errors.append(f"historical_formula_immutable_line_binding_mismatch:{symbol}")
        if symbol not in scans:
            errors.append(f"historical_formula_scan_missing:{symbol}")
    return list(dict.fromkeys(errors))


def build_reuse_evidence_binding(report: dict) -> dict:
    audit = report.get("formula_evidence", {}) if isinstance(report, dict) else {}
    manifest = audit.get("reuse_evidence_manifest", {})
    manifest_hash = str(audit.get("reuse_evidence_manifest_sha256", ""))
    if not isinstance(manifest, dict) or not manifest:
        return {
            "status": "NOT_USED",
            "reuse_scope": None,
            "reuse_evidence_manifest": None,
            "reuse_evidence_manifest_sha256": None,
        }
    computed_hash = canonical_json_sha256(manifest)
    verified = (
        audit.get("status") == "VERIFIED"
        and manifest.get("reuse_scope") == "raw_scan_only"
        and computed_hash == manifest_hash
        and audit.get("source_receipt_artifact_binding", {}).get("matched") is True
    )
    return {
        "status": "VERIFIED" if verified else "REJECTED",
        "reuse_scope": manifest.get("reuse_scope"),
        "reuse_evidence_manifest": manifest,
        "reuse_evidence_manifest_sha256": manifest_hash,
        "computed_manifest_sha256": computed_hash,
        "source_receipt_sha256": audit.get("source_receipt", {}).get("sha256"),
        "source_artifact_sha256": audit.get("source_artifact", {}).get("sha256"),
        "immutable_line_sha256": audit.get("recovery_provenance", {}).get("line_sha256"),
        "source_receipt_artifact_binding": audit.get("source_receipt_artifact_binding", {}),
    }


def run_child(command: list[str], timeout: int, extra_environment: dict[str, str] | None = None) -> dict:
    environment = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "ONESTOCK_STOCK_CANONICAL_CHILD": "1",
        **(extra_environment or {}),
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
    # 全量候选需要逐只读取五个 TQ 公式；300 秒在 30+ 只候选时会误判为
    # Harness/业务失败。允许环境覆盖，并把默认窗口提高到 15 分钟。
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("FIVE_DIMENSION_TIMEOUT_SECONDS", "900")))
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

    duanxianxia = refresh_duanxianxia(run_dir)
    lianban_history = refresh_lianban_history(run_dir)
    command = business_command(run_dir)
    child = run_child(command, args.timeout, {
        "CODEX_DUANXIANXIA_STATUS": duanxianxia["status"],
        "CODEX_DUANXIANXIA_PATH": duanxianxia["path"],
        "CODEX_DUANXIANXIA_SOURCE_URL": duanxianxia["source_url"],
        "CODEX_LIANBAN_HISTORY_PATH": lianban_history["path"],
    })
    stdout_path = run_dir / "business_child.stdout.txt"
    stderr_path = run_dir / "business_child.stderr.txt"
    stdout_path.write_text(str(child["stdout"]), encoding="utf-8")
    stderr_path.write_text(str(child["stderr"]), encoding="utf-8")
    combined = str(child["stdout"]) + "\n" + str(child["stderr"])
    failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    try:
        mainline_report = json.loads(SCAN_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        mainline_report = {}
    mainline_validation_errors = validate_mainline_report()
    formula_evidence_validation_errors = validate_formula_evidence_report(mainline_report)
    mainline_validation_errors.extend(formula_evidence_validation_errors)
    reuse_evidence = build_reuse_evidence_binding(mainline_report)
    if reuse_evidence.get("status") == "REJECTED":
        mainline_validation_errors.append("reuse_evidence_business_binding_rejected")
    accepted = child["returncode"] == 0 and not failure_tokens and not mainline_validation_errors
    result = {
        "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
        "skill_id": SKILL_ID,
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "decision_status": mainline_report.get("decision_status"),
        "business_process": {
            "command": command,
            "cwd": str(ROOT),
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
            "failure_tokens": failure_tokens,
            "mainline_validation_errors": mainline_validation_errors,
            "formula_evidence_validation_errors": formula_evidence_validation_errors,
        },
        "business_binding": {
            "path": str(LEGACY_ENTRY),
            "sha256": sha256_file(LEGACY_ENTRY),
        },
        "artifacts": {
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "mainline_report": str(SCAN_JSON),
            "mainline_report_sha256": sha256_file(SCAN_JSON) if SCAN_JSON.is_file() else "",
        },
        "reuse_evidence": reuse_evidence,
        "supplemental_sources": {"duanxianxia": duanxianxia, "lianban_history": lianban_history},
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
