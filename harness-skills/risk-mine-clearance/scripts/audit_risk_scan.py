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
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts" / "a_share_risk_scan.py"
OVERLAY = ROOT / "scripts" / "risk_warning_overlay.py"
VALIDATOR = ROOT / "scripts" / "validate_risk_run.py"
POSTER_BUILDER = ROOT / "scripts" / "poster_builder.py"
POSTER_VALIDATOR = ROOT / "scripts" / "poster_validator.py"
SHANGHAI = ZoneInfo("Asia/Shanghai")
SHARED_SCAN_FILES = (
    "capability_manifest.json",
    "confirmed_risk_candidates.csv",
    "evidence.jsonl",
    "front_candidates.csv",
    "front_source_court_defaulters_recent.csv",
    "front_source_shcpe_enterprise_notices.csv",
    "front_source_wage_arrears_gd.csv",
    "risk_candidates.csv",
    "risk_scan.sqlite",
    "run_manifest.json",
    "run_report.md",
    "source_health.csv",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay_shared_scan(
    source_dir: Path,
    output_dir: Path,
    target_date: str,
) -> dict[str, object]:
    source_dir = source_dir.resolve()
    output_dir = output_dir.resolve()
    if source_dir == output_dir:
        raise ValueError("shared_risk_scan_source_equals_target")
    manifest_path = source_dir / "run_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"shared_risk_manifest_missing:{manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if str(manifest.get("run_date")) != target_date:
        raise ValueError(
            f"shared_risk_date_mismatch:{manifest.get('run_date')}!={target_date}"
        )
    missing = [name for name in SHARED_SCAN_FILES if not (source_dir / name).is_file()]
    if missing:
        raise FileNotFoundError("shared_risk_files_missing:" + ",".join(missing))
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in SHARED_SCAN_FILES:
        source = source_dir / name
        target = output_dir / name
        shutil.copy2(source, target)
        if sha256_file(target) != sha256_file(source):
            raise RuntimeError(f"shared_risk_copy_hash_mismatch:{name}")
    return {
        "returncode": 0,
        "stdout": json.dumps(
            {
                "status": "CLEAN_PASS",
                "mode": "shared_current_task_evidence",
                "run_date": target_date,
                "candidate_count": manifest.get("candidate_count"),
                "evidence_count": manifest.get("evidence_count"),
            },
            ensure_ascii=False,
        ),
        "stderr": "",
    }


def run(command: list[str], timeout: int) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def command_summary(result: dict[str, object]) -> dict[str, object]:
    return {
        "returncode": result.get("returncode"),
        "stdout_tail": str(result.get("stdout", ""))[-2000:],
        "stderr_tail": str(result.get("stderr", ""))[-1000:],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="风险排雷技能整合执行入口")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--date")
    parser.add_argument("--deep-limit", type=int, default=8)
    parser.add_argument("--rumors", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    now = datetime.now(SHANGHAI)
    output_dir = (
        args.output_dir
        or ROOT / "reports" / "audit" / f"risk-{now:%Y%m%d-%H%M%S}"
    ).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    target_date = args.date or now.date().isoformat()

    scan_command = [
        sys.executable,
        str(SCANNER),
        "--output-dir",
        str(output_dir),
        "--deep-limit",
        str(max(0, args.deep_limit)),
        "--date",
        target_date,
    ]
    if args.rumors:
        scan_command.extend(["--rumors", str(args.rumors.resolve())])

    shared_run_dir = os.environ.get("CODEX_RISK_SHARED_RUN_DIR", "").strip()
    shared_status = os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS", "").strip()
    if shared_run_dir:
        try:
            if shared_status != "CLEAN_PASS":
                raise RuntimeError("shared_risk_evidence_status_not_clean")
            scan = replay_shared_scan(Path(shared_run_dir), output_dir, target_date)
        except Exception as exc:
            scan = {
                "returncode": 2,
                "stdout": "",
                "stderr": f"{type(exc).__name__}:{exc}",
            }
    else:
        scan = run(scan_command, timeout=900)
    overlay = run(
        [sys.executable, str(OVERLAY), "--output-dir", str(output_dir)],
        timeout=60,
    )
    validation = run(
        [sys.executable, str(VALIDATOR), "--run-dir", str(output_dir)],
        timeout=180,
    )
    poster_path = output_dir / "risk-mine-clearance-8k.png"
    poster_preview_path = output_dir / "risk-mine-clearance-preview-1920x1080.png"
    poster_metadata_path = output_dir / "poster_metadata.json"
    poster_validation_path = output_dir / "poster_validation.json"
    poster = run(
        [
            sys.executable,
            str(POSTER_BUILDER),
            "--output",
            str(poster_path),
            "--metadata",
            str(poster_metadata_path),
            "--preview",
            str(poster_preview_path),
            "--version-date",
            target_date,
        ],
        timeout=180,
    )
    poster_validation = run(
        [
            sys.executable,
            str(POSTER_VALIDATOR),
            "--input",
            str(poster_path),
            "--metadata",
            str(poster_metadata_path),
            "--output",
            str(poster_validation_path),
        ],
        timeout=180,
    )
    validation_path = output_dir / "skill_validation.json"
    validation_readback = (
        json.loads(validation_path.read_text(encoding="utf-8"))
        if validation_path.is_file()
        else {}
    )
    poster_validation_readback = (
        json.loads(poster_validation_path.read_text(encoding="utf-8"))
        if poster_validation_path.is_file()
        else {}
    )
    run_manifest_path = output_dir / "run_manifest.json"
    run_manifest_readback = (
        json.loads(run_manifest_path.read_text(encoding="utf-8-sig"))
        if run_manifest_path.is_file()
        else {}
    )
    ok = (
        scan["returncode"] == 0
        and overlay["returncode"] == 0
        and validation["returncode"] == 0
        and validation_readback.get("ok") is True
        and poster["returncode"] == 0
        and poster_validation["returncode"] == 0
        and poster_validation_readback.get("status") == "PASS"
    )
    summary = {
        "schema": "INTEGRATED_RISK_SCAN_V1",
        "status": "CLEAN_PASS" if ok else "BLOCKED",
        "name": "风险排雷技能",
        "run_date": target_date,
        "output_dir": str(output_dir),
        "components": {
            "individual_risk_scan": command_summary(scan),
            "market_risk_warning": command_summary(overlay),
            "validation": {
                **command_summary(validation),
                "ok": validation_readback.get("ok"),
            },
            "poster": {
                "build_stdout_tail": str(poster.get("stdout", ""))[-2000:],
                "build_stderr_tail": str(poster.get("stderr", ""))[-1000:],
                "build_returncode": poster["returncode"],
                "validation_stdout_tail": str(poster_validation.get("stdout", ""))[-2000:],
                "validation_stderr_tail": str(poster_validation.get("stderr", ""))[-1000:],
                "validation_returncode": poster_validation["returncode"],
                "validation_status": poster_validation_readback.get("status"),
                "artifact": str(poster_path),
                "preview": str(poster_preview_path),
            },
        },
        "metrics": {
            "candidate_count": run_manifest_readback.get("candidate_count"),
            "front_candidate_count": run_manifest_readback.get("front_candidate_count"),
            "confirmed_risk_candidate_count": run_manifest_readback.get(
                "confirmed_risk_candidate_count"
            ),
            "evidence_count": run_manifest_readback.get("evidence_count"),
            "priority_codes": (
                validation_readback.get("checks", {})
                .get("priority_selection", {})
                .get("codes", [])
            ),
            "market_risk_level": (
                validation_readback.get("checks", {})
                .get("market_risk_warning", {})
                .get("risk_level")
            ),
        },
        "evidence_sha256": {
            name: sha256_file(output_dir / name)
            for name in ("risk_candidates.csv", "evidence.jsonl", "source_health.csv")
            if (output_dir / name).is_file()
        },
        "diagnostics": {
            "source_mode": (
                "shared_current_task_evidence" if shared_run_dir else "live_collection"
            ),
            "scan_stderr_present": bool(str(scan.get("stderr", "")).strip()),
            "overlay_stderr_present": bool(str(overlay.get("stderr", "")).strip()),
            "validation_stderr_present": bool(
                str(validation.get("stderr", "")).strip()
            ),
            "poster_stderr_present": bool(str(poster.get("stderr", "")).strip()),
            "poster_validation_stderr_present": bool(
                str(poster_validation.get("stderr", "")).strip()
            ),
        },
    }
    (output_dir / "integrated_risk_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if ok else 2


if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
