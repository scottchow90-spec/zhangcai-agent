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
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = ROOT.name
LEGACY_ENTRY = ROOT / "scripts" / "legacy_codex_entry.py"
CATALOG = ROOT / "references" / "stock_skill_ids.json"
SKILLS_ROOT = ROOT.parent
CURRENT_REPORT = Path(os.environ.get("ONESTOCK_STOCK_DATA_ROOT", str(ROOT / "reports"))) / "selftests" / "stock-unified-current.json"
DELIVERABLE_NAMES = {
    "production_readiness_report": "股票技能生产就绪报告.json",
    "per_skill_compliance_matrix": "股票技能生产控制矩阵.json",
    "production_validation_results": "股票技能生产验证结果.json",
}
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


def append_error(errors: list[str], error: str) -> None:
    if error not in errors:
        errors.append(error)


def load_catalog() -> list[str]:
    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    skills = payload.get("skills", [])
    if (
        not isinstance(skills, list)
        or not skills
        or not all(isinstance(item, str) and item for item in skills)
        or len(skills) != len(set(skills))
    ):
        raise ValueError("invalid_stock_skill_catalog")
    return skills


def validate_child_summary(stdout: str) -> list[str]:
    errors: list[str] = []
    try:
        parsed = json.loads(stdout.strip())
    except (json.JSONDecodeError, TypeError):
        return ["child_stdout_not_single_json_object"]
    if not isinstance(parsed, dict):
        return ["child_stdout_not_single_json_object"]

    try:
        skills = load_catalog()
    except Exception:
        return ["child_schema_mismatch"]

    if parsed.get("schema") != "STOCK_UNIFIED_SELFTEST_V1":
        append_error(errors, "child_schema_mismatch")
    if parsed.get("status") != "CLEAN_PASS":
        append_error(errors, "child_status_not_clean")

    skill_ids = parsed.get("skill_ids")
    if not isinstance(skill_ids, list) or not all(
        isinstance(item, str) for item in skill_ids
    ):
        append_error(errors, "child_schema_mismatch")
        append_error(errors, "child_skill_ids_mismatch")
    else:
        if len(set(skill_ids)) != len(skill_ids):
            append_error(errors, "child_skill_ids_not_unique")
        if skill_ids != skills:
            append_error(errors, "child_skill_ids_mismatch")

    expected_count = len(skills)
    expected_summary = {
        "catalog_count": expected_count,
        "entry_count": expected_count,
        "selftest_pass": expected_count,
        "failure_count": 0,
        "procedural_entry_count": 0,
        "errors": [],
    }
    if any(parsed.get(key) != value for key, value in expected_summary.items()):
        append_error(errors, "child_status_not_clean")
    regression = parsed.get("regression")
    if (
        not isinstance(regression, dict)
        or regression.get("status") != "CLEAN_PASS"
        or not isinstance(regression.get("test_count"), int)
        or regression.get("test_count", 0) < 1
        or regression.get("errors") != []
    ):
        append_error(errors, "child_regression_not_clean")

    report_binding = parsed.get("report")
    if not isinstance(report_binding, dict):
        append_error(errors, "child_schema_mismatch")
        return errors

    try:
        report_path = Path(str(report_binding.get("path", ""))).resolve()
    except (OSError, RuntimeError, TypeError, ValueError):
        append_error(errors, "child_schema_mismatch")
        return errors
    if report_path != CURRENT_REPORT.resolve():
        append_error(errors, "child_schema_mismatch")
        return errors
    if not report_path.is_file():
        append_error(errors, "child_status_not_clean")
        return errors

    report_data = report_path.read_bytes()
    if (
        report_binding.get("size") != len(report_data)
        or report_binding.get("sha256") != hashlib.sha256(report_data).hexdigest()
    ):
        append_error(errors, "child_status_not_clean")
        return errors
    try:
        report = json.loads(report_data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        append_error(errors, "child_schema_mismatch")
        return errors
    if not isinstance(report, dict):
        append_error(errors, "child_schema_mismatch")
        return errors

    if (
        report.get("schema") != "STOCK_UNIFIED_SELFTEST_V1"
        or report.get("skill_ids") != skills
    ):
        append_error(errors, "child_schema_mismatch")
    report_ids = report.get("skill_ids")
    if isinstance(report_ids, list) and len(set(report_ids)) != len(report_ids):
        append_error(errors, "child_skill_ids_not_unique")
    if report_ids != skills:
        append_error(errors, "child_skill_ids_mismatch")
    if any(report.get(key) != value for key, value in {
        "status": "CLEAN_PASS",
        **expected_summary,
    }.items()):
        append_error(errors, "child_status_not_clean")
    if report.get("regression") != regression:
        append_error(errors, "child_schema_mismatch")

    parsed_deliverables = parsed.get("deliverables")
    report_deliverables = report.get("deliverables")
    if (
        not isinstance(parsed_deliverables, dict)
        or parsed_deliverables != report_deliverables
    ):
        append_error(errors, "child_deliverables_invalid")
    else:
        for role, filename in DELIVERABLE_NAMES.items():
            artifact = parsed_deliverables.get(role)
            expected_path = CURRENT_REPORT.parent / filename
            if not isinstance(artifact, dict):
                append_error(errors, "child_deliverables_invalid")
                continue
            try:
                actual_path = Path(str(artifact.get("path", ""))).resolve()
            except (OSError, RuntimeError, TypeError, ValueError):
                append_error(errors, "child_deliverables_invalid")
                continue
            if actual_path != expected_path.resolve() or not actual_path.is_file():
                append_error(errors, "child_deliverables_invalid")
                continue
            data = actual_path.read_bytes()
            if (
                artifact.get("size") != len(data)
                or artifact.get("sha256") != hashlib.sha256(data).hexdigest()
            ):
                append_error(errors, "child_deliverables_invalid")

    rows = report.get("skills")
    if not isinstance(rows, list):
        append_error(errors, "child_schema_mismatch")
        return errors
    row_ids = [
        row.get("skill_id") if isinstance(row, dict) else None
        for row in rows
    ]
    if len(set(row_ids)) != len(row_ids):
        append_error(errors, "child_skill_ids_not_unique")
    if row_ids != skills:
        append_error(errors, "child_skill_ids_mismatch")
    for skill_id, row in zip(skills, rows):
        if not isinstance(row, dict):
            append_error(errors, "child_schema_mismatch")
            continue
        entry = SKILLS_ROOT / skill_id / "scripts" / "codex_entry.py"
        expected_command = [sys.executable, str(entry), "selftest"]
        if (
            row.get("entry") != str(entry)
            or row.get("command") != expected_command
            or row.get("returncode") != 0
            or row.get("selftest_pass") is not True
            or row.get("errors") != []
        ):
            append_error(errors, "child_status_not_clean")
    return errors


def build_industry_evidence(run_dir: Path) -> Path:
    today = datetime.now().astimezone().date().isoformat()
    observed_at = f"{today}T00:00:00+08:00"
    source = ROOT.parent / "industry-chain-analysis" / "references" / "evidence_schema.md"
    if not source.is_file():
        raise FileNotFoundError(f"industry_evidence_contract_missing:{source}")
    payload = {
        "schema": "INDUSTRY-CHAIN-ANALYSIS-INPUT-1",
        "mode": "mindset",
        "subject": "A股产业链研究证据纪律",
        "as_of": observed_at,
        "market_scope": "A-share research methodology",
        "test_mode": False,
        "evidence": [{
            "id": "E1",
            "claim": "实际产业链研究必须使用非空证据，并分开披露风险与未验证项。",
            "source_name": "本机产业链深度研究输入契约",
            "source_date": today,
            "retrieved_at": observed_at,
            "source_locator": str(source.resolve()),
        }],
        "sections": [{
            "title": "证据边界",
            "content": ["本次本地业务运行只验证证据约束和持久化链，不输出实时市场结论。"],
            "evidence_ids": ["E1"],
        }],
        "conclusion": {
            "stance": "NOT_APPLICABLE",
            "summary": "需取得具体产业链的当前公开证据后再形成市场判断。",
        },
        "risks": ["方法入口通过不代表任何具体产业链结论成立。"],
        "unverified": ["未提供具体产业链目标及当前市场、公告和财务证据。"],
    }
    path = run_dir / "industry-chain-evidence.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def business_command(run_dir: Path) -> list[str]:
    industry_input = build_industry_evidence(run_dir) if SKILL_ID == "industry-chain-analysis" else None
    overrides: dict[str, list[str]] = {
        "golden-ignition": ["run", "000001"],
        "shortline-hotspot-mining": ["run", "--date", datetime.now().strftime("%Y-%m-%d")],
        "a-share-intraday-position-monitor": [
            "run", "--symbol", "301372", "--cost", "25.0", "--shares", "200000",
            "--name", "科净源", "--stock-attestation", "off",
        ],
        "industry-chain-analysis": ["run", "--input", str(industry_input)],
        "old-leader-oversold-rebound": [
            "run",
            "--as-of",
            datetime.now().strftime("%Y-%m-%d"),
            "--tdx",
            os.environ.get("ZHANGCAI_TDX_ROOT")
            or os.environ.get("TDX_ROOT")
            or os.environ.get("ZHANGCAI_DEV_TDX_ROOT", r"C:\new_tdx_mock"),
            "--json",
            str(run_dir / "old-leader-result.json"),
            "--csv",
            str(run_dir / "old-leader-result.csv"),
        ],
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
    combined = str(child["stdout"]) + "\n" + str(child["stderr"])
    failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    validation_errors = validate_child_summary(str(child["stdout"]))
    accepted = (
        child["returncode"] == 0
        and not failure_tokens
        and not validation_errors
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
