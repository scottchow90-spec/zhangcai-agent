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
import subprocess
import sys
from pathlib import Path
_stock_adapter_shared_scripts = str(_OneStockEmbeddedPath(__file__).resolve().parents[3] / "scripts")
if _stock_adapter_shared_scripts not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _stock_adapter_shared_scripts)
from stock_adapter_io import atomic_write_json, atomic_write_text, enable_atomic_path_writes

from scoring_mode_gate import (
    normalize_business_args,
    validate_composite_ranking_identity,
)

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
    "Traceback (most recent call last)",
    "TIMEOUT after ",
)
DELIVERABLE_NAMES = (
    "analysis_report.txt",
    "ranking.json",
    "poster.png",
    "三公式综合评分回测报告.md",
    "三公式综合评分回测证据.json",
    "三公式综合评分正式模型.json",
    "三公式综合评分状态同步收据.json",
    "三公式综合评分同步后模型状态.json",
    "三公式综合评分样本外明细.csv",
    "三公式综合评分样本外分期.csv",
    "三公式综合评分最新排名.json",
    "三公式综合评分最新排名.csv",
    "三公式综合评分30项贡献明细.csv",
    "三公式综合评分最新排名报告.md",
    "三公式综合评分8K海报.png",
    "三公式综合评分8K海报-preview-1920x1080.png",
    "三公式综合评分因子权重标准8K海报.png",
    "大牛线综合评分系统30项权重分值8K海报.png",
    "大牛线综合评分系统30项权重分值8K海报-preview-1920x1080.png",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json_object(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON根节点不是对象：{path.name}")
    return payload


def _csv_has_data_rows(path: Path) -> bool:
    if not path.is_file():
        return False
    return sum(1 for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()) > 1


def inspect_composite_scientific_outcome(deliverables: Path) -> dict | None:
    evidence_path = deliverables / "三公式综合评分回测证据.json"
    if not evidence_path.is_file():
        return None
    model_path = deliverables / "三公式综合评分正式模型.json"
    if not model_path.is_file():
        raise ValueError("三公式回测缺少正式模型状态文件")
    evidence = _read_json_object(evidence_path)
    formal = _read_json_object(model_path)
    predictive = evidence.get("predictive_validation")
    formal_predictive = formal.get("predictive_validation")
    status = predictive.get("status") if isinstance(predictive, dict) else None
    formal_status = (
        formal_predictive.get("status")
        if isinstance(formal_predictive, dict)
        else None
    )
    if status not in {"PREDICTIVE_PASS", "PREDICTIVE_REJECTED", "BLOCKED"}:
        raise ValueError(f"回测预测终态无效：{status!r}")
    if formal_status != status:
        raise ValueError("回测证据与正式模型的预测终态不一致")

    rows_nonempty = _csv_has_data_rows(
        deliverables / "三公式综合评分样本外明细.csv"
    )
    dates_nonempty = _csv_has_data_rows(
        deliverables / "三公式综合评分样本外分期.csv"
    )
    validation = evidence.get("validation_gates")
    failed_gates = (
        list(validation.get("failed", [])) if isinstance(validation, dict) else []
    )
    model = formal.get("model")
    if status == "PREDICTIVE_PASS":
        if (
            formal.get("status") != "CLEAN_PASS"
            or not isinstance(model, dict)
            or not rows_nonempty
            or not dates_nonempty
            or not isinstance(validation, dict)
            or validation.get("status") != "PASS"
        ):
            raise ValueError("预测通过结果缺少可用模型、样本外证据或通过状态")
    elif model is not None:
        raise ValueError("预测拒绝结果仍携带可用模型")

    return {
        "status": status,
        "model_usable": status == "PREDICTIVE_PASS",
        "oos_rows_nonempty": rows_nonempty,
        "oos_dates_nonempty": dates_nonempty,
        "failed_gates": failed_gates,
    }


def run_child(
    command: list[str],
    timeout: int,
    extra_environment: dict[str, str] | None = None,
) -> dict:
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


def main() -> int:
    enable_atomic_path_writes()
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--timeout", type=int, default=300)
    args, business_args = parser.parse_known_args()
    if business_args and business_args[0] == "--":
        business_args = business_args[1:]
    run_dir = Path(args.run_dir).resolve()
    deliverables = run_dir / "deliverables"
    deliverables.mkdir(parents=True, exist_ok=True)

    if os.environ.get("CODEX_STOCK_CANONICAL_EXECUTION") != "1":
        print(json.dumps({
            "skill_id": SKILL_ID,
            "status": "BLOCKED",
            "errors": ["canonical_execution_environment_missing"],
        }, ensure_ascii=False))
        return 2

    try:
        normalized_business_args = normalize_business_args(business_args)
    except ValueError as exc:
        print(json.dumps({
            "skill_id": SKILL_ID,
            "status": "BLOCKED",
            "errors": [str(exc)],
        }, ensure_ascii=False))
        return 2

    command = [
        sys.executable,
        str(LEGACY_ENTRY),
        "run",
        "--",
        "--output-dir",
        str(deliverables),
        *business_args,
    ]
    child = run_child(command, args.timeout)
    stdout_path = run_dir / "business_child.stdout.txt"
    stderr_path = run_dir / "business_child.stderr.txt"
    stdout_path.write_text(str(child["stdout"]), encoding="utf-8")
    stderr_path.write_text(str(child["stderr"]), encoding="utf-8")
    result_file = deliverables / "result.json"
    combined = str(child["stdout"]) + "\n" + str(child["stderr"])
    failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    scientific_outcome = None
    scientific_errors: list[str] = []
    try:
        scientific_outcome = inspect_composite_scientific_outcome(deliverables)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        scientific_errors.append(f"scientific_outcome_invalid:{type(exc).__name__}:{exc}")
    if normalized_business_args[0] in {
        "score-research-composite",
        "研究型综合评分",
        "score-composite",
        "综合评分",
    }:
        ranking_path = deliverables / "三公式综合评分最新排名.json"
        try:
            if not ranking_path.is_file():
                raise ValueError("composite_ranking_missing")
            validate_composite_ranking_identity(
                json.loads(ranking_path.read_text(encoding="utf-8"))
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            scientific_errors.append(
                f"composite_identity_invalid:{type(exc).__name__}:{exc}"
            )
    accepted = (
        child["returncode"] == 0
        and not failure_tokens
        and result_file.is_file()
        and not scientific_errors
    )
    artifacts: dict[str, object] = {
        "result": {
            "path": str(result_file),
            "sha256": sha256_file(result_file) if result_file.is_file() else None,
        },
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }
    for name in DELIVERABLE_NAMES:
        path = deliverables / name
        if path.is_file():
            artifacts[name] = {
                "path": str(path),
                "sha256": sha256_file(path),
            }
    result = {
        "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
        "skill_id": SKILL_ID,
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "status_scope": "execution_and_artifact_integrity_only",
        "business_outcome": scientific_outcome,
        "scientific_errors": scientific_errors,
        "business_process": {
            "command": command,
            "cwd": str(ROOT),
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
            "failure_tokens": failure_tokens,
        },
        "artifacts": artifacts,
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
