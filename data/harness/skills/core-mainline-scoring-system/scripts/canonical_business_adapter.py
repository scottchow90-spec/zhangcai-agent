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
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
_stock_adapter_shared_scripts = str(_OneStockEmbeddedPath(__file__).resolve().parents[3] / "scripts")
if _stock_adapter_shared_scripts not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _stock_adapter_shared_scripts)
from stock_adapter_io import atomic_write_json, atomic_write_text, enable_atomic_path_writes
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT.parents[1]
SKILL_ID = ROOT.name
RUNNER = ROOT / "scripts" / "run_core_mainline_scoring.py"
DUANXIANXIA_CLIENT = HOME / "skills" / "a-share-hotspot-sentiment-analysis" / "scripts" / "duanxianxia_client.ps1"
LIANBAN_CLIENT = HOME / "scripts" / "lianban_daily_client.py"
POSTER_BUILDER = ROOT / "scripts" / "poster_builder.py"
POSTER_VALIDATOR = ROOT / "scripts" / "poster_validator.py"
POSTER_LIGHT_GATE = HOME / "scripts" / "poster_light_background_gate.py"
FAILURE_TOKENS = ("Traceback (most recent call last)", "TIMEOUT after ")
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


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def child_json(child: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(str(child.get("stdout", "")).strip())
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def build_data_gate(
    scoring_result: dict[str, Any],
    scoring_path: Path,
    duanxianxia: dict[str, Any],
    lianban_history: dict[str, Any],
) -> dict[str, Any]:
    summary = scoring_result.get("summary", {})
    source_status = scoring_result.get("source_status", {})
    session_alignment = scoring_result.get("session_alignment", {})
    boards = scoring_result.get("boards", [])
    boards = boards if isinstance(boards, list) else []
    core_name = str(summary.get("core_mainline") or "").strip()
    selected = next(
        (
            row for row in boards
            if isinstance(row, dict)
            and str(row.get("name") or "").strip() == core_name
        ),
        None,
    )
    selected_input = (
        selected.get("input_evidence", {})
        if isinstance(selected, dict)
        else {}
    )
    constituent = selected_input.get("constituent_evidence", {})
    sector_return = selected_input.get("sector_return_evidence", {})
    turnover = selected_input.get("turnover_evidence", [])
    catalyst = selected_input.get("catalyst_evidence", {})
    effective_date = str(scoring_result.get("target_date") or "").strip()
    latest_required_date = str(
        os.environ.get("CODEX_STOCK_EVIDENCE_TRADING_DATE", "")
    ).strip()
    evidence_set_id = str(
        os.environ.get("CODEX_STOCK_EVIDENCE_SET_ID", "")
    ).strip()
    expected_numeric_date = int(effective_date.replace("-", "")) if len(effective_date) == 10 else 0
    all_sources_clean = bool(source_status) and all(
        str(value) in {"CLEAN_PASS", "VERIFIED"}
        for value in source_status.values()
    )
    selected_complete = bool(
        isinstance(selected, dict)
        and selected.get("decision_eligible") is True
        and selected.get("missing_evidence") == []
        and selected.get("gate_failures") == []
    )
    turnover_current = bool(turnover) and all(
        isinstance(item, dict)
        and int(item.get("current_date") or 0) == expected_numeric_date
        and str(item.get("source_path") or "").startswith("C:\\new_tdx_mock\\vipdoc\\")
        and len(str(item.get("source_sha256") or "")) == 64
        for item in turnover
    )
    checks = {
        "identity": bool(
            scoring_result.get("execution_status") == "CLEAN_PASS"
            and int(summary.get("board_count") or 0) > 0
            and selected_complete
        ),
        "effective_trading_date": bool(
            effective_date
            and effective_date == latest_required_date
        ),
        "quote_kline": bool(
            source_status.get("tdx_turnover") == "VERIFIED"
            and isinstance(sector_return, dict)
            and int(sector_return.get("current_date") or 0) == expected_numeric_date
            and str(sector_return.get("source_path") or "").startswith("C:\\new_tdx_mock\\vipdoc\\")
            and len(str(sector_return.get("source_sha256") or "")) == 64
            and turnover_current
        ),
        "fundamentals": bool(
            source_status.get("tdx_constituents") == "VERIFIED"
            and isinstance(constituent, dict)
            and int(selected_input.get("constituent_count") or 0) > 100
            and str(constituent.get("source_path") or "").startswith("C:\\new_tdx_mock\\")
            and len(str(constituent.get("source_sha256") or "")) == 64
        ),
        "news_announcements": bool(
            selected_input.get("catalyst_verified") is True
            and int(selected_input.get("catalyst_source_count") or 0) >= 2
            and isinstance(catalyst, dict)
            and catalyst.get("verified") is True
            and int(catalyst.get("source_count") or 0) >= 2
            and bool(catalyst.get("matched_codes"))
        ),
        "sector_theme": bool(
            selected_complete
            and str(selected.get("normalized_name") or "").strip()
            and isinstance(constituent, dict)
            and str(constituent.get("match_type") or "").strip()
        ),
        "source_freshness": bool(
            os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS") == "CLEAN_PASS"
            and all_sources_clean
            and float(session_alignment.get("coverage") or 0.0) >= 0.80
            and duanxianxia.get("status") == "CLEAN_PASS"
            and lianban_history.get("status") == "CLEAN_PASS"
            and int(lianban_history.get("snapshot_count") or 0) >= 2
            and scoring_result.get("issues") == []
        ),
    }
    errors: list[str] = []
    if not evidence_set_id:
        errors.append("evidence_set_id_missing")
    for name in DATA_GATE_DIMENSIONS:
        if not checks[name]:
            errors.append(f"data_gate_dimension_failed:{name}")
    evidence_root = str(scoring_path.resolve())
    evidence_ids = {
        "identity": [f"{evidence_root}#summary", f"{evidence_root}#boards.core_mainline"],
        "effective_trading_date": [f"{evidence_root}#target_date", f"{evidence_set_id or 'missing'}#trading_date"],
        "quote_kline": [f"{evidence_root}#core.sector_return_evidence", f"{evidence_root}#core.turnover_evidence"],
        "fundamentals": [f"{evidence_root}#core.constituent_evidence", f"{evidence_root}#core.constituent_count"],
        "news_announcements": [f"{evidence_root}#core.catalyst_evidence", f"{evidence_set_id or 'missing'}#lianban_daily"],
        "sector_theme": [f"{evidence_root}#core.normalized_name", f"{evidence_root}#core.constituent_match_type"],
        "source_freshness": [f"{evidence_root}#source_status", f"{evidence_set_id or 'missing'}#created_at"],
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


def refresh_duanxianxia(run_dir: Path) -> dict[str, Any]:
    snapshot = run_dir / "duanxianxia-mainline.json"
    command = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(DUANXIANXIA_CLIENT), "-Output", str(snapshot),
    ]
    try:
        completed = subprocess.run(
            command, cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
        )
        payload = read_json(snapshot)
        required = ("ztlive", "ztplate", "ztpool", "platechart1", "platechart2", "amount")
        failed = [name for name in required if payload.get("datasets", {}).get(name, {}).get("success") is not True]
        return {
            "status": "CLEAN_PASS" if completed.returncode == 0 and not failed else "DEGRADED",
            "path": str(snapshot),
            "source_url": payload.get("source_page", "https://duanxianxia.com/web/main"),
            "returncode": completed.returncode,
            "failed_datasets": failed,
            "stderr": (completed.stderr or "")[-1000:],
        }
    except Exception as exc:
        return {
            "status": "DEGRADED", "path": str(snapshot),
            "source_url": "https://duanxianxia.com/web/main", "returncode": 125,
            "failed_datasets": ["refresh_failed"], "stderr": f"{type(exc).__name__}: {exc}",
        }


def refresh_lianban_history(run_dir: Path) -> dict[str, Any]:
    snapshots: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    for offset in range(1, 11):
        target_date = datetime.now().date() - timedelta(days=offset)
        if target_date.weekday() >= 5:
            continue
        target = target_date.isoformat()
        output = run_dir / f"lianban-{target}.json"
        command = [sys.executable, str(LIANBAN_CLIENT), "--date", target, "--output", str(output)]
        try:
            completed = subprocess.run(
                command, cwd=str(ROOT), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=45,
            )
            payload = read_json(output)
            attempts.append({"date": target, "returncode": completed.returncode, "status": payload.get("status", "DEGRADED")})
            if completed.returncode == 0 and payload.get("status") == "CLEAN_PASS":
                snapshots.append(payload)
                if len(snapshots) >= 3:
                    break
        except Exception as exc:
            attempts.append({"date": target, "returncode": 125, "status": "DEGRADED", "error": type(exc).__name__})
    combined = run_dir / "lianban-history.json"
    status = "CLEAN_PASS" if len(snapshots) >= 2 else "DEGRADED"
    combined.write_text(
        json.dumps({"status": status, "snapshots": snapshots, "attempts": attempts}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"status": status, "path": str(combined), "snapshot_count": len(snapshots), "attempts": attempts}


def run_child(command: list[str], timeout: int, environment: dict[str, str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command, cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, env=environment,
        )
        return {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {"returncode": 124, "stdout": stdout, "stderr": stderr + f"\nTIMEOUT after {timeout}s", "timed_out": True}
    except Exception as exc:
        return {"returncode": 125, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}", "timed_out": False}


def build_poster_delivery(run_dir: Path, scoring_result: Path) -> dict[str, Any]:
    manifest_path = run_dir / "poster-delivery-manifest.json"
    lianban_path = Path(os.environ.get("CODEX_LIANBAN_SNAPSHOT", ""))
    errors: list[str] = []
    if not lianban_path.is_file():
        errors.append(f"lianban_snapshot_missing:{lianban_path}")
    candidate_dir = run_dir / "poster-candidates"
    candidate = candidate_dir / "核心主线评分8K海报.png"
    candidate_preview = candidate_dir / "核心主线评分8K海报-preview-1920x1080.png"
    metadata_path = run_dir / "poster-metadata.json"
    validation_path = run_dir / "poster-validation.json"
    light_gate_path = run_dir / "poster-light-background-gate.json"
    deliverable_dir = run_dir / "deliverables"
    poster = deliverable_dir / "核心主线评分8K海报.png"
    preview = deliverable_dir / "核心主线评分8K海报-preview-1920x1080.png"
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

    builder_payload: dict[str, Any] = {"status": "BLOCKED", "errors": list(errors)}
    validation_payload: dict[str, Any] = {"status": "BLOCKED", "errors": ["builder_not_run"]}
    light_gate_payload: dict[str, Any] = {"status": "BLOCKED", "failures": ["builder_not_run"]}
    if not errors:
        builder = run_child(
            [
                sys.executable,
                str(POSTER_BUILDER),
                "--scoring",
                str(scoring_result),
                "--lianban",
                str(lianban_path),
                "--output",
                str(candidate),
                "--preview",
                str(candidate_preview),
                "--metadata",
                str(metadata_path),
            ],
            180,
            environment,
        )
        (run_dir / "poster-builder.stdout.txt").write_text(str(builder["stdout"]), encoding="utf-8")
        (run_dir / "poster-builder.stderr.txt").write_text(str(builder["stderr"]), encoding="utf-8")
        builder_payload = child_json(builder)
        if builder["returncode"] != 0 or builder_payload.get("status") != "PASS":
            errors.append("poster_builder_not_pass")

    if not errors:
        validator = run_child(
            [
                sys.executable,
                str(POSTER_VALIDATOR),
                "--input",
                str(candidate),
                "--metadata",
                str(metadata_path),
                "--scoring",
                str(scoring_result),
                "--output",
                str(validation_path),
            ],
            90,
            environment,
        )
        (run_dir / "poster-validator.stdout.txt").write_text(str(validator["stdout"]), encoding="utf-8")
        (run_dir / "poster-validator.stderr.txt").write_text(str(validator["stderr"]), encoding="utf-8")
        validation_payload = read_json(validation_path)
        if validator["returncode"] != 0 or validation_payload.get("status") != "PASS":
            errors.append("poster_validator_not_pass")

    if not errors:
        light_gate = run_child(
            [
                sys.executable,
                str(POSTER_LIGHT_GATE),
                "--input",
                str(candidate),
                "--expected-width",
                "7680",
                "--expected-height",
                "4320",
            ],
            90,
            environment,
        )
        light_gate_payload = child_json(light_gate)
        write_json(light_gate_path, light_gate_payload)
        if light_gate["returncode"] != 0 or light_gate_payload.get("status") != "PASS":
            errors.append("poster_light_background_gate_not_pass")

    if not errors:
        deliverable_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate, poster)
        shutil.copy2(candidate_preview, preview)

    artifacts = []
    for path in (poster, preview, metadata_path, validation_path, light_gate_path):
        if path.is_file():
            artifacts.append({
                "path": str(path.resolve()),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            })
    manifest = {
        "schema": "CORE_MAINLINE_POSTER_DELIVERY_MANIFEST_V1",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "requested": True,
        "errors": errors,
        "builder": builder_payload,
        "validation": validation_payload,
        "light_gate": light_gate_payload,
        "artifacts": artifacts,
    }
    write_json(manifest_path, manifest)
    return manifest


def write_no_poster_manifest(run_dir: Path) -> dict[str, Any]:
    manifest = {
        "schema": "CORE_MAINLINE_POSTER_DELIVERY_MANIFEST_V1",
        "status": "CLEAN_PASS",
        "requested": False,
        "errors": [],
        "validation": {"status": "PASS", "errors": []},
        "light_gate": {"status": "PASS", "failures": []},
        "artifacts": [],
    }
    write_json(run_dir / "poster-delivery-manifest.json", manifest)
    return manifest


def main() -> int:
    enable_atomic_path_writes()
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--input-bundle", type=Path)
    parser.add_argument("--poster", action="store_true")
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    if os.environ.get("CODEX_STOCK_CANONICAL_EXECUTION") != "1":
        print(json.dumps({"skill_id": SKILL_ID, "status": "BLOCKED", "errors": ["canonical_execution_environment_missing"]}, ensure_ascii=False))
        return 2

    if args.input_bundle:
        duanxianxia = {"status": "PROVIDED_INPUT_BUNDLE", "path": str(args.input_bundle.resolve())}
        lianban_history = {"status": "PROVIDED_INPUT_BUNDLE", "path": str(args.input_bundle.resolve()), "snapshot_count": None}
    else:
        duanxianxia = refresh_duanxianxia(run_dir)
        lianban_history = refresh_lianban_history(run_dir)

    result_path = run_dir / "core-mainline-result.json"
    command = [sys.executable, str(RUNNER), "--output", str(result_path)]
    if args.input_bundle:
        command.extend(["--input-bundle", str(args.input_bundle.resolve())])
    environment = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "ONESTOCK_STOCK_CANONICAL_CHILD": "1",
        "CODEX_DUANXIANXIA_PATH": str(duanxianxia.get("path", "")),
        "CODEX_LIANBAN_HISTORY_PATH": str(lianban_history.get("path", "")),
    }
    child = run_child(command, args.timeout, environment)
    stdout_path = run_dir / "business_child.stdout.txt"
    stderr_path = run_dir / "business_child.stderr.txt"
    stdout_path.write_text(str(child["stdout"]), encoding="utf-8")
    stderr_path.write_text(str(child["stderr"]), encoding="utf-8")
    scoring_result = read_json(result_path)
    combined = str(child["stdout"]) + "\n" + str(child["stderr"])
    validation_errors: list[str] = []
    if scoring_result.get("schema") != "CORE_MAINLINE_SCORING_RESULT_V1":
        validation_errors.append("result_schema_mismatch")
    if scoring_result.get("model_version") != "CORE-MAINLINE-CLOSE-V3":
        validation_errors.append("model_version_mismatch")
    if scoring_result.get("execution_status") != "CLEAN_PASS":
        validation_errors.append("scoring_execution_not_clean")
    if int(scoring_result.get("summary", {}).get("board_count", 0) or 0) <= 0:
        validation_errors.append("scored_board_count_zero")
    failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    validation_errors.extend(failure_tokens)
    poster_delivery = (
        build_poster_delivery(run_dir, result_path)
        if args.poster and child["returncode"] == 0 and not validation_errors
        else write_no_poster_manifest(run_dir)
    )
    if args.poster and poster_delivery.get("status") != "CLEAN_PASS":
        validation_errors.extend(str(item) for item in poster_delivery.get("errors", []))
    accepted = child["returncode"] == 0 and not validation_errors
    data_gate = build_data_gate(
        scoring_result,
        result_path,
        duanxianxia,
        lianban_history,
    )
    if os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS") == "CLEAN_PASS":
        if data_gate.get("status") != "CLEAN_PASS":
            validation_errors.extend(str(item) for item in data_gate.get("errors", []))
        accepted = accepted and data_gate.get("status") == "CLEAN_PASS"

    result = {
        "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
        "skill_id": SKILL_ID,
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "business_process": {
            "command": command,
            "cwd": str(ROOT),
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
            "validation_errors": validation_errors,
            "failure_tokens": failure_tokens,
        },
        "business_binding": {"path": str(RUNNER), "sha256": sha256_file(RUNNER)},
        "artifacts": {
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "scoring_result": str(result_path),
            "poster_manifest": str(run_dir / "poster-delivery-manifest.json"),
        },
        "scoring_summary": scoring_result.get("summary", {}),
        "decision_status": scoring_result.get("decision_status"),
        "data_gate": data_gate,
        "supplemental_sources": {"duanxianxia": duanxianxia, "lianban_history": lianban_history},
        "delivery_manifest": poster_delivery,
    }
    business_result_path = run_dir / "business_result.json"
    business_result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
