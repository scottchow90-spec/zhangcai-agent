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


def build_industry_evidence(run_dir: Path) -> Path:
    today = datetime.now().astimezone().date().isoformat()
    observed_at = f"{today}T00:00:00+08:00"
    industry_root = (
        ROOT
        if SKILL_ID == "industry-chain-analysis"
        else ROOT.parent / "industry-chain-analysis"
    )
    source = industry_root / "references" / "evidence_schema.md"
    if not source.is_file():
        raise FileNotFoundError(f"industry_evidence_contract_missing:{source}")
    payload = {
        "schema": "INDUSTRY-CHAIN-ANALYSIS-INPUT-1",
        "mode": "mindset",
        "subject": "A股产业链研究证据纪律",
        "as_of": observed_at,
        "market_scope": "A-share research methodology",
        "test_mode": False,
        "evidence": [
            {
                "id": "E1",
                "claim": "实际产业链研究必须使用非空证据，并分开披露风险与未验证项。",
                "source_name": "本机产业链深度研究输入契约",
                "source_date": today,
                "retrieved_at": observed_at,
                "source_locator": str(source.resolve()),
            }
        ],
        "sections": [
            {
                "title": "证据边界",
                "content": [
                    "本次本地业务运行只验证证据约束和持久化链，不输出实时市场结论。"
                ],
                "evidence_ids": ["E1"],
            }
        ],
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
            r"C:\\new_tdx_mock",
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
    accepted = child["returncode"] == 0 and not failure_tokens
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
