#!/usr/bin/env python3
"""Aggregate runner for the canonical Codex stock-skill execution chain."""
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
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from stock_contract_catalog import contract_catalog_preflight, sha256_file
from audit_stock_production_readiness import build_audit
from stock_production_readiness import PRODUCTION_POLICY, atomic_write_text


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
CATALOG = ROOT / "references" / "stock_skill_ids.json"
CONTRACTS = ROOT / "references" / "stock_execution_contracts.json"
BUSINESS_SPEC = ROOT / "references" / "business_spec.md"
CANONICAL_RUNTIME = ROOT.parent.parent / "scripts" / "stock_canonical_runtime.py"
SPECIAL_FACADE_SKILLS = {"convertible-bond-screening-strategy"}
RESULT_DIR = Path(__import__("os").environ.get("ONESTOCK_STOCK_DATA_ROOT", str(ROOT / "reports"))) / "selftests"
READINESS_REPORT_NAME = "股票技能生产就绪报告.json"
CONTROL_MATRIX_NAME = "股票技能生产控制矩阵.json"
VALIDATION_RESULTS_NAME = "股票技能生产验证结果.json"
REGRESSION_TIMEOUT_SECONDS = 240


def load_catalog() -> list[str]:
    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    skills = payload.get("skills", [])
    if not isinstance(skills, list) or not all(isinstance(item, str) for item in skills):
        raise ValueError("invalid_stock_skill_catalog")
    return skills


def load_catalog_payload() -> dict[str, Any]:
    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("invalid_stock_skill_catalog")
    return payload


def chinese_workflow_name(skill_id: str, catalog_payload: dict[str, Any]) -> str:
    workflow_names = catalog_payload.get("workflow_names")
    names = workflow_names.get(skill_id, []) if isinstance(workflow_names, dict) else []
    for name in names if isinstance(names, list) else []:
        if isinstance(name, str) and any("\u4e00" <= char <= "\u9fff" for char in name):
            return name
    raise ValueError(f"chinese_workflow_name_missing:{skill_id}")


def load_contracts() -> dict[str, dict[str, Any]]:
    payload = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    rows = payload.get("contracts", [])
    if not isinstance(rows, list):
        raise ValueError("invalid_stock_execution_contracts")
    return {str(row["skill_id"]): row for row in rows}


def facade_fingerprint(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    normalized = text.rstrip("\n") + "\n"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def acceptance_source_errors(skills: list[str]) -> list[str]:
    errors: list[str] = []
    if not BUSINESS_SPEC.is_file():
        errors.append("business_spec_missing")
    else:
        text = BUSINESS_SPEC.read_text(encoding="utf-8-sig")
        if re.search(r"\d+\s*个[^\n]{0,24}技能", text):
            errors.append("business_spec_hardcoded_catalog_count")
        if "references/stock_skill_ids.json" not in text or "即时条目数" not in text:
            errors.append("business_spec_catalog_authority_missing")

    for skill_id in skills:
        skill_root = SKILLS_ROOT / skill_id
        manifest_path = skill_root / "references" / "source-manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            errors.append(f"{skill_id}:source_manifest_invalid")
            continue
        files = manifest.get("files") if isinstance(manifest, dict) else None
        if not isinstance(files, dict):
            errors.append(f"{skill_id}:source_manifest_files_invalid")
            continue
        for source_id, source_files in files.items():
            if not isinstance(source_id, str) or not isinstance(source_files, dict):
                errors.append(f"{skill_id}:source_manifest_files_invalid")
                continue
            component_root = (skill_root / "components" / source_id).resolve()
            for relative, expected_hash in source_files.items():
                if not isinstance(relative, str) or not isinstance(expected_hash, str):
                    errors.append(f"{skill_id}:source_manifest_files_invalid")
                    continue
                path = (component_root / relative).resolve()
                try:
                    path.relative_to(component_root)
                except ValueError:
                    errors.append(
                        f"{skill_id}:source_manifest_path_escape:{source_id}:{relative}"
                    )
                    continue
                if not path.is_file():
                    errors.append(
                        f"{skill_id}:source_manifest_file_missing:{source_id}:{relative}"
                    )
                elif sha256_file(path) != expected_hash:
                    errors.append(
                        f"{skill_id}:source_manifest_hash_mismatch:{source_id}:{relative}"
                    )
    return errors


def consistency_payload() -> dict[str, Any]:
    skills = load_catalog()
    contracts = load_contracts()
    errors: list[str] = []
    if len(set(skills)) != len(skills):
        errors.append("catalog_duplicates")
    if set(contracts) != set(skills):
        errors.append("contract_skill_set_mismatch")
    canonical_facade_hashes: set[str] = set()
    special_facade_count = 0
    legacy_count = 0
    for skill_id in skills:
        scripts = SKILLS_ROOT / skill_id / "scripts"
        entry = scripts / "codex_entry.py"
        legacy = scripts / "legacy_codex_entry.py"
        if not entry.is_file():
            errors.append(f"{skill_id}:missing_entry")
        elif skill_id in SPECIAL_FACADE_SKILLS:
            special_facade_count += 1
        else:
            canonical_facade_hashes.add(facade_fingerprint(entry))
        if legacy.is_file():
            legacy_count += 1
        else:
            errors.append(f"{skill_id}:missing_legacy_entry")
    if len(canonical_facade_hashes) != 1:
        errors.append(f"canonical_facade_hash_count:{len(canonical_facade_hashes)}")
    if special_facade_count != len(SPECIAL_FACADE_SKILLS):
        errors.append(
            f"special_facade_count:{special_facade_count}:{len(SPECIAL_FACADE_SKILLS)}"
        )
    contract_preflight = contract_catalog_preflight(
        catalog_path=CATALOG,
        contracts_path=CONTRACTS,
        skills_root=SKILLS_ROOT,
        runtime_path=CANONICAL_RUNTIME,
    )
    errors.extend(contract_preflight["errors"])
    errors.extend(acceptance_source_errors(skills))
    return {
        "schema": "STOCK_UNIFIED_CONSISTENCY_V3",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "runtime_surface": "Codex",
        "catalog_count": len(skills),
        "contract_count": len(contracts),
        "uniform_entry_count": (
            len(skills) - special_facade_count
            if len(canonical_facade_hashes) == 1
            else 0
        ),
        "special_facade_count": special_facade_count,
        "legacy_entry_count": legacy_count,
        "failure_owner": contract_preflight.get("failure_owner"),
        "contract_preflight": contract_preflight,
        "errors": errors,
    }


def consistency() -> int:
    payload = consistency_payload()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "CLEAN_PASS" else 2


def run_child(command: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
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
            "stderr": f"{stderr}\nTIMEOUT after {timeout}s",
            "timed_out": True,
        }
    except Exception as exc:
        return {
            "returncode": 125,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "timed_out": False,
        }


def selftest_payload_errors(skill_id: str, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("skill_id") != skill_id:
        errors.append("selftest_skill_id_mismatch")
    if payload.get("status") != "CLEAN_PASS":
        errors.append("selftest_status_not_pass")
    if payload.get("errors") != []:
        errors.append("selftest_errors_not_empty")
    return errors


def run_one_selftest(skill_id: str, timeout: int) -> dict[str, Any]:
    root = SKILLS_ROOT / skill_id
    entry = root / "scripts" / "codex_entry.py"
    command = [sys.executable, str(entry), "selftest"]
    result = run_child(command, root, timeout)
    errors: list[str] = []
    payload: dict[str, Any] | None = None
    try:
        parsed = json.loads(str(result["stdout"]).strip())
        if isinstance(parsed, dict):
            payload = parsed
        else:
            errors.append("selftest_stdout_not_single_json_object")
    except (json.JSONDecodeError, TypeError):
        errors.append("selftest_stdout_not_single_json_object")
    if result["returncode"] != 0:
        errors.append(f"selftest_returncode:{result['returncode']}")
    if payload is not None:
        errors.extend(selftest_payload_errors(skill_id, payload))
    row: dict[str, Any] = {
        "skill_id": skill_id,
        "entry": str(entry),
        "command": command,
        "returncode": result["returncode"],
        "timed_out": bool(result.get("timed_out")),
        "selftest_pass": not errors,
        "payload_status": payload.get("status") if payload else None,
        "stdout_tail": str(result["stdout"])[-1600:],
        "stderr_tail": str(result["stderr"])[-1600:],
        "errors": errors,
    }
    return row


def execute_all(
    skills: list[str],
    *,
    timeout: int = 300,
    max_workers: int = 1,
) -> list[dict[str, Any]]:
    workers = max(1, min(int(max_workers), 8, max(1, len(skills))))
    if workers == 1:
        return [run_one_selftest(skill_id, timeout) for skill_id in skills]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(
            executor.map(
                lambda skill_id: run_one_selftest(skill_id, timeout),
                skills,
            )
        )


def configured_selftest_workers(skill_count: int) -> int:
    raw = os.environ.get("CODEX_STOCK_SELFTEST_WORKERS", "8").strip()
    try:
        requested = int(raw)
    except ValueError:
        requested = 8
    return max(1, min(requested, 8, max(1, skill_count)))


def run_regression_suite(timeout: int = REGRESSION_TIMEOUT_SECONDS) -> dict[str, Any]:
    cache_root = Path(r"F:\Codex\cache")
    pytest_cache = cache_root / "pytest" / "stock-unified"
    pytest_temp = pytest_cache / f"run-{os.getpid()}-{time.time_ns()}"
    pytest_temp.mkdir(parents=True, exist_ok=False)
    command = [
        sys.executable,
        "-m",
        "pytest",
        str(ROOT / "tests"),
        "-q",
        "--tb=short",
        "-o",
        f"cache_dir={pytest_cache / 'cache'}",
        "--basetemp",
        str(pytest_temp),
    ]
    environment = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONPYCACHEPREFIX": str(cache_root / "pycache"),
        "TEMP": str(cache_root / "temp"),
        "TMP": str(cache_root / "temp"),
    }
    (cache_root / "temp").mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
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
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        stdout = (
            exc.stdout.decode("utf-8", "replace")
            if isinstance(exc.stdout, bytes)
            else (exc.stdout or "")
        )
        stderr = (
            exc.stderr.decode("utf-8", "replace")
            if isinstance(exc.stderr, bytes)
            else (exc.stderr or "")
        )
        timed_out = True
    except Exception as exc:
        returncode = 125
        stdout = ""
        stderr = f"{type(exc).__name__}: {exc}"
        timed_out = False
    matches = list(
        re.finditer(
            r"(?P<tests>\d+) passed(?:, (?P<subtests>\d+) subtests passed)?",
            stdout,
        )
    )
    test_count = int(matches[-1].group("tests")) if matches else 0
    subtest_text = matches[-1].group("subtests") if matches else None
    subtest_count = int(subtest_text) if subtest_text else 0
    errors: list[str] = []
    if returncode != 0:
        errors.append(f"regression_returncode:{returncode}")
    if timed_out:
        errors.append("regression_timeout")
    if test_count < 1:
        errors.append("regression_pass_summary_missing")
    clean = not errors
    return {
        "schema": "STOCK_PRODUCTION_REGRESSION_V1",
        "status": "CLEAN_PASS" if clean else "BLOCKED",
        "command": command,
        "returncode": returncode,
        "timed_out": timed_out,
        "test_count": test_count,
        "subtest_count": subtest_count,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "diagnostic_tail": "" if clean else (stdout + "\n" + stderr)[-6000:],
        "errors": errors,
    }


def blocked_preflight_rows(skills: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for skill_id in skills:
        entry = SKILLS_ROOT / skill_id / "scripts" / "codex_entry.py"
        rows.append({
            "skill_id": skill_id,
            "entry": str(entry),
            "command": [sys.executable, str(entry), "selftest"],
            "returncode": None,
            "timed_out": False,
            "selftest_pass": False,
            "payload_status": None,
            "stdout_tail": "",
            "stderr_tail": "",
            "errors": ["blocked_by_global_contract_preflight"],
        })
    return rows


def run_all(max_workers: int | None = None) -> int:
    current_report = RESULT_DIR / "stock-unified-current.json"
    skills = load_catalog()
    contract_preflight = contract_catalog_preflight(
        catalog_path=CATALOG,
        contracts_path=CONTRACTS,
        skills_root=SKILLS_ROOT,
        runtime_path=CANONICAL_RUNTIME,
    )
    acceptance_errors = acceptance_source_errors(skills)
    production_audit = build_audit()
    production_errors = list(production_audit.get("errors", []))
    preflight_clean = (
        contract_preflight.get("status") == "CLEAN_PASS"
        and not acceptance_errors
        and not production_errors
    )
    workers = (
        configured_selftest_workers(len(skills))
        if max_workers is None
        else max(1, min(int(max_workers), 8, max(1, len(skills))))
    )
    selftest_started = time.monotonic()
    rows = (
        execute_all(skills, max_workers=workers)
        if preflight_clean
        else blocked_preflight_rows(skills)
    )
    selftest_elapsed_seconds = round(time.monotonic() - selftest_started, 3)
    selftest_pass = sum(bool(row.get("selftest_pass")) for row in rows)
    failure_count = len(skills) - selftest_pass
    procedural_entry_count = sum(
        row.get("payload_status") == "PROCEDURAL" for row in rows
    )
    selftests_clean = (
        len(set(skills)) == len(skills)
        and len(rows) == len(skills)
        and selftest_pass == len(skills)
        and failure_count == 0
        and procedural_entry_count == 0
    )
    regression = (
        run_regression_suite()
        if preflight_clean and selftests_clean
        else {
            "schema": "STOCK_PRODUCTION_REGRESSION_V1",
            "status": "BLOCKED",
            "command": [],
            "returncode": None,
            "timed_out": False,
            "test_count": 0,
            "subtest_count": 0,
            "elapsed_seconds": 0.0,
            "diagnostic_tail": "",
            "errors": ["blocked_by_preceding_production_gate"],
        }
    )
    clean = preflight_clean and selftests_clean and regression["status"] == "CLEAN_PASS"
    report_payload = {
        "schema": "STOCK_UNIFIED_SELFTEST_V1",
        "status": "CLEAN_PASS" if clean else "BLOCKED",
        "runtime_surface": "Codex",
        "executed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "catalog": str(CATALOG),
        "contracts": str(CONTRACTS),
        "failure_owner": (
            "stock_unified_acceptance_sources"
            if acceptance_errors
            else contract_preflight.get("failure_owner")
        ),
        "errors": [
            *list(contract_preflight.get("errors", [])),
            *acceptance_errors,
            *production_errors,
        ],
        "contract_preflight": contract_preflight,
        "acceptance_source_validation": {
            "status": "CLEAN_PASS" if not acceptance_errors else "BLOCKED",
            "errors": acceptance_errors,
        },
        "production_readiness": production_audit,
        "catalog_count": len(skills),
        "entry_count": len(rows),
        "selftest_pass": selftest_pass,
        "failure_count": failure_count,
        "procedural_entry_count": procedural_entry_count,
        "selftest_workers": workers,
        "selftest_elapsed_seconds": selftest_elapsed_seconds,
        "regression": regression,
        "skill_ids": list(skills),
        "skills": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    catalog_payload = load_catalog_payload()
    generated_at = report_payload["executed_at"]
    readiness_payload = {
        "schema": "STOCK_PRODUCTION_READINESS_REPORT_V1",
        "status": report_payload["status"],
        "generated_at": generated_at,
        "scope": "权威目录内全部股票技能的离线研究、分析、信号、回测与模拟执行链",
        "catalog_count": len(skills),
        "compliant_count": production_audit.get("compliant_count", 0),
        "missing_count": production_audit.get("missing_count", 0),
        "drift_count": production_audit.get("drift_count", 0),
        "total_control_count": production_audit.get("total_control_count", 0),
        "passed_control_count": production_audit.get("passed_control_count", 0),
        "selftest_pass": selftest_pass,
        "regression_test_count": regression["test_count"],
        "regression_subtest_count": regression["subtest_count"],
        "production_policy": PRODUCTION_POLICY,
        "execution_boundary": "不连接券商账户、不生成或发送订单、不启动自动交易",
        "errors": report_payload["errors"] + regression["errors"],
    }
    matrix_rows = []
    for audit_row in production_audit.get("skills", []):
        skill_id = str(audit_row.get("skill_id", ""))
        matrix_rows.append({
            "技能名称": chinese_workflow_name(skill_id, catalog_payload),
            "状态": "通过" if audit_row.get("status") == "CLEAN_PASS" else "阻断",
            "控制总数": audit_row.get("control_count", 0),
            "通过控制数": audit_row.get("passed_control_count", 0),
            "控制项": audit_row.get("controls", {}),
            "错误": audit_row.get("errors", []),
        })
    control_matrix_payload = {
        "schema": "STOCK_PRODUCTION_CONTROL_MATRIX_V1",
        "status": report_payload["status"],
        "generated_at": generated_at,
        "技能总数": len(matrix_rows),
        "控制总数": production_audit.get("total_control_count", 0),
        "通过控制数": production_audit.get("passed_control_count", 0),
        "技能": matrix_rows,
    }
    validation_payload = {
        "schema": "STOCK_PRODUCTION_VALIDATION_RESULTS_V1",
        "status": report_payload["status"],
        "generated_at": generated_at,
        "合同预检": contract_preflight,
        "生产审计": {
            key: production_audit.get(key)
            for key in (
                "status",
                "catalog_count",
                "contract_count",
                "compliant_count",
                "missing_count",
                "drift_count",
                "total_control_count",
                "passed_control_count",
                "errors",
            )
        },
        "逐技能自检": {
            "status": "CLEAN_PASS" if selftests_clean else "BLOCKED",
            "技能总数": len(skills),
            "通过数": selftest_pass,
            "失败数": failure_count,
            "过程占位数": procedural_entry_count,
            "并发上限": workers,
            "耗时秒": selftest_elapsed_seconds,
        },
        "完整回归": regression,
        "故障注入覆盖": [
            "危险交易与凭证输入",
            "参数与输出资源上限",
            "陈旧、缺失及未来日期数据",
            "回执遥测缺失与篡改",
            "业务绑定缺失与哈希漂移",
            "原子写入中断残留",
            "超时与输出洪泛",
            "重复审计确定性",
        ],
        "交易安全边界": "研究、分析、信号、回测和模拟；账户、订单、券商接口及实盘交易均阻断",
        "错误": report_payload["errors"] + regression["errors"],
    }
    deliverable_payloads = {
        "production_readiness_report": (
            RESULT_DIR / READINESS_REPORT_NAME,
            readiness_payload,
        ),
        "per_skill_compliance_matrix": (
            RESULT_DIR / CONTROL_MATRIX_NAME,
            control_matrix_payload,
        ),
        "production_validation_results": (
            RESULT_DIR / VALIDATION_RESULTS_NAME,
            validation_payload,
        ),
    }
    deliverables: dict[str, dict[str, Any]] = {}
    for role, (path, payload) in deliverable_payloads.items():
        deliverables[role] = atomic_write_text(
            path,
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        )
    report_payload["deliverables"] = deliverables
    encoded = json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n"
    atomic_write_text(current_report, encoded)
    summary = {
        key: report_payload[key]
        for key in (
            "schema",
            "status",
            "runtime_surface",
            "executed_at",
            "catalog",
            "contracts",
            "failure_owner",
            "errors",
            "contract_preflight",
            "production_readiness",
            "catalog_count",
            "entry_count",
            "selftest_pass",
            "failure_count",
            "procedural_entry_count",
            "selftest_workers",
            "selftest_elapsed_seconds",
            "regression",
            "skill_ids",
        )
    }
    summary["deliverables"] = deliverables
    summary["report"] = {
        "path": str(current_report.resolve()),
        "size": current_report.stat().st_size,
        "sha256": sha256_file(current_report),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if report_payload["status"] == "CLEAN_PASS" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Canonical Codex stock-skill aggregate executor")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("info", "consistency", "run-all"),
        default="info",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="bounded worker count for run-all (1-8)",
    )
    args = parser.parse_args()
    if args.command == "info":
        print(json.dumps({
            "runtime_surface": "Codex",
            "entry": str(Path(__file__).resolve()),
            "catalog": str(CATALOG),
            "contracts": str(CONTRACTS),
            "commands": ["consistency", "run-all"],
        }, ensure_ascii=False, indent=2))
        return 0
    if args.command == "consistency":
        return consistency()
    return run_all(args.workers)


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
