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
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from nana_freshness_guard import (
    bind_quote_json_file,
    canonical_sha256,
    normalize_trade_date,
)


ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts" / "nana_five_strategy_scanner.py"
FRESHNESS_GUARD = ROOT / "scripts" / "nana_freshness_guard.py"
QUOTE_FETCHER = ROOT / "scripts" / "nana_quote_fetcher.py"
STRATEGIES = ["元宝藏金", "地极破晓", "游龙吸水", "负阴抱阳", "黄金双响"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise TypeError(f"json_root_not_object:{path}")
    return payload


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def artifact_record(path: Path, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": str(path.resolve()),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
    }


def verify_receipt(receipt_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    verified_artifacts: list[str] = []
    try:
        receipt = load_json_object(receipt_path)
    except Exception as exc:
        return {
            "status": "BLOCKED",
            "receipt": str(receipt_path.resolve()),
            "errors": [f"receipt_unreadable:{type(exc).__name__}:{exc}"],
        }
    if receipt.get("schema_version") != 3:
        errors.append(f"receipt_schema_invalid:{receipt.get('schema_version')}")
    if receipt.get("kind") != "NANA_TEACHER_FIVE_STRATEGY_RUN_V3":
        errors.append(f"receipt_kind_invalid:{receipt.get('kind')}")
    if receipt.get("status") != "PASS":
        errors.append(f"receipt_status_not_pass:{receipt.get('status')}")
    if not re.fullmatch(r"20\d{6}", str(receipt.get("target_trade_date") or "")):
        errors.append("receipt_target_trade_date_invalid")
    data_route = str(receipt.get("data_route") or "")
    expected_roles = {
        "local_day": {"scan_json", "current_csv"},
        "validated_quote_append": {"scan_json", "current_csv", "quote_json"},
    }.get(data_route)
    if expected_roles is None:
        errors.append(f"receipt_data_route_invalid:{data_route}")
        expected_roles = set()
    artifacts = receipt.get("artifacts")
    expected_count = len(expected_roles)
    if not isinstance(artifacts, list) or len(artifacts) != expected_count:
        errors.append(
            f"receipt_artifact_count_invalid:{len(artifacts) if isinstance(artifacts, list) else 'non_list'}!={expected_count}"
        )
        artifacts = []
    scan_path: Path | None = None
    quote_path: Path | None = None
    roles: set[str] = set()
    artifact_by_role: dict[str, dict[str, Any]] = {}
    for item in artifacts:
        if not isinstance(item, dict):
            errors.append("receipt_artifact_not_object")
            continue
        role = str(item.get("role") or "")
        if role in roles:
            errors.append(f"artifact_role_duplicate:{role}")
        roles.add(role)
        path = Path(str(item.get("path") or ""))
        artifact_by_role[role] = item
        if not path.is_absolute() or str(path) != str(path.resolve()):
            errors.append(f"artifact_path_not_canonical:{path}")
        if not path.is_file():
            errors.append(f"artifact_missing:{path}")
            continue
        actual_size = path.stat().st_size
        actual_hash = sha256(path)
        if actual_size != int(item.get("size_bytes", -1)):
            errors.append(f"artifact_size_mismatch:{path}")
        if actual_hash != str(item.get("sha256") or ""):
            errors.append(f"artifact_hash_mismatch:{path}")
        if actual_size == int(item.get("size_bytes", -1)) and actual_hash == str(
            item.get("sha256") or ""
        ):
            verified_artifacts.append(str(path.resolve()))
        if role == "scan_json":
            scan_path = path
        elif role == "quote_json":
            quote_path = path
    if roles != expected_roles:
        errors.append(f"artifact_roles_invalid:{sorted(roles)}")
    scan: dict[str, Any] = {}
    if scan_path and scan_path.is_file():
        try:
            scan = load_json_object(scan_path)
        except Exception as exc:
            errors.append(f"scan_json_unreadable:{type(exc).__name__}:{exc}")
        else:
            if scan.get("status") != "PASS":
                errors.append(f"scan_status_not_pass:{scan.get('status')}")
            if scan.get("target_trade_date") != receipt.get("target_trade_date"):
                errors.append("scan_receipt_trade_date_mismatch")
            if scan.get("freshness_gate", {}).get("status") != "PASS":
                errors.append("scan_freshness_gate_not_pass")
            if scan.get("freshness_gate", {}).get("schema") != "nana-selector-freshness-gate/v3":
                errors.append("scan_freshness_gate_schema_invalid")
            if scan.get("freshness_gate", {}).get("selected_data_route") != data_route:
                errors.append("scan_receipt_data_route_mismatch")
            fingerprint = scan.get("input_fingerprint") or {}
            if fingerprint.get("schema") != "nana-scan-input/v2":
                errors.append("scan_input_fingerprint_schema_invalid")
            if not re.fullmatch(r"[0-9a-f]{64}", str(fingerprint.get("sha256") or "")):
                errors.append("scan_input_fingerprint_invalid")
            if list((scan.get("strategy_summary") or {}).keys()) != STRATEGIES:
                errors.append("scan_strategy_set_or_order_invalid")
            if canonical_sha256(scan.get("freshness_gate")) != canonical_sha256(
                receipt.get("freshness_gate")
            ):
                errors.append("scan_receipt_freshness_gate_mismatch")
            if canonical_sha256(fingerprint) != canonical_sha256(
                receipt.get("input_fingerprint")
            ):
                errors.append("scan_receipt_input_fingerprint_mismatch")
    source_code = receipt.get("source_code") or {}
    source_paths = (
        ("runner", Path(__file__).resolve()),
        ("scanner", SCANNER),
        ("freshness_guard", FRESHNESS_GUARD),
        ("quote_fetcher", QUOTE_FETCHER),
    )
    for name, path in source_paths:
        record = source_code.get(name) if isinstance(source_code, dict) else None
        if not isinstance(record, dict):
            errors.append(f"source_code_record_missing:{name}")
            continue
        expected = str(record.get("sha256") or "")
        recorded_path = Path(str(record.get("path") or ""))
        if str(recorded_path) != str(path.resolve()):
            errors.append(f"source_code_path_mismatch:{name}")
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            errors.append(f"source_code_hash_invalid:{name}")
        elif not path.is_file() or sha256(path) != expected:
            errors.append(f"source_code_hash_mismatch:{name}")
    if scan:
        fingerprint = scan.get("input_fingerprint") or {}
        if fingerprint.get("scanner_sha256") != source_code.get("scanner", {}).get("sha256"):
            errors.append("fingerprint_scanner_hash_mismatch")
        if fingerprint.get("freshness_guard_sha256") != source_code.get(
            "freshness_guard", {}
        ).get("sha256"):
            errors.append("fingerprint_freshness_guard_hash_mismatch")
    if data_route == "validated_quote_append":
        if quote_path is None or not quote_path.is_file():
            errors.append("quote_artifact_missing")
        else:
            _quote_payload, actual_binding = bind_quote_json_file(quote_path)
            if actual_binding.get("status") != "PASS":
                errors.extend(
                    f"quote_binding:{item}" for item in actual_binding.get("errors") or []
                )
            if actual_binding.get("trade_date") != receipt.get("target_trade_date"):
                errors.append("quote_receipt_trade_date_mismatch")
            quote_artifact = artifact_by_role.get("quote_json") or {}
            if quote_artifact.get("sha256") != actual_binding.get("file_sha256"):
                errors.append("quote_artifact_binding_hash_mismatch")
            if quote_artifact.get("size_bytes") != actual_binding.get("size_bytes"):
                errors.append("quote_artifact_binding_size_mismatch")
            binding_candidates = {
                "receipt": receipt.get("quote_file"),
                "receipt_freshness": (receipt.get("freshness_gate") or {}).get("quote_file"),
                "scan_freshness": (scan.get("freshness_gate") or {}).get("quote_file"),
                "scan_fingerprint": (scan.get("input_fingerprint") or {}).get("quote_file"),
            }
            for label, binding in binding_candidates.items():
                if canonical_sha256(binding) != canonical_sha256(actual_binding):
                    errors.append(f"quote_binding_mismatch:{label}")
            if (scan.get("input_fingerprint") or {}).get("quote_json_sha256") != actual_binding.get(
                "file_sha256"
            ):
                errors.append("fingerprint_quote_file_hash_mismatch")
    elif data_route == "local_day":
        if receipt.get("quote_file") is not None:
            errors.append("local_route_receipt_quote_binding_present")
        if scan and (scan.get("input_fingerprint") or {}).get("quote_file") is not None:
            errors.append("local_route_fingerprint_quote_binding_present")
    return {
        "status": "PASS" if not errors else "BLOCKED",
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "receipt": str(receipt_path.resolve()),
        "receipt_sha256": sha256(receipt_path),
        "target_trade_date": receipt.get("target_trade_date"),
        "verified_artifacts": verified_artifacts,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run or verify the fixed Nana teacher five-strategy selector."
    )
    parser.add_argument("--verify-receipt", type=Path)
    parser.add_argument("--target-date")
    parser.add_argument("--quote-json")
    parser.add_argument("--history-days", type=int, default=80)
    parser.add_argument(
        "--output-dir", type=Path, default=Path.cwd() / "outputs" / "娜娜老师5策略_运行"
    )
    args = parser.parse_args()
    if args.verify_receipt:
        result = verify_receipt(args.verify_receipt.resolve())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "PASS" else 2

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_json = output_dir / "nana_five_strategy_scan.json"
    output_csv = output_dir / "nana_five_strategy_current.csv"
    receipt_path = output_dir / "nana_five_strategy_run_receipt.json"
    for managed_path in (output_json, output_csv, receipt_path):
        if managed_path.is_file():
            managed_path.unlink()
    argv = [
        sys.executable,
        str(SCANNER),
        "--history-days",
        str(args.history_days),
        "--output-json",
        str(output_json),
        "--output-csv",
        str(output_csv),
    ]
    if args.target_date:
        argv.extend(["--target-date", args.target_date])
    if args.quote_json:
        argv.extend(["--quote-json", str(Path(args.quote_json).resolve())])
    completed = subprocess.run(
        argv,
        cwd=str(Path.cwd()),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=900,
        check=False,
    )
    scan_errors: list[str] = []
    try:
        scan = load_json_object(output_json)
    except Exception as exc:
        scan = {}
        scan_errors.append(f"scan_output_unreadable:{type(exc).__name__}:{exc}")
    if completed.returncode != 0:
        scan_errors.append(f"scanner_exit_code:{completed.returncode}")
    if scan.get("status") != "PASS":
        scan_errors.append(f"scan_status_not_pass:{scan.get('status')}")
    if scan.get("freshness_gate", {}).get("status") != "PASS":
        scan_errors.append("freshness_gate_not_pass")
    if scan.get("freshness_gate", {}).get("schema") != "nana-selector-freshness-gate/v3":
        scan_errors.append("freshness_gate_schema_invalid")
    if list((scan.get("strategy_summary") or {}).keys()) != STRATEGIES:
        scan_errors.append("strategy_set_or_order_invalid")
    fingerprint = scan.get("input_fingerprint") or {}
    if fingerprint.get("schema") != "nana-scan-input/v2":
        scan_errors.append("input_fingerprint_schema_invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", str(fingerprint.get("sha256") or "")):
        scan_errors.append("input_fingerprint_invalid")

    data_route = str(scan.get("freshness_gate", {}).get("selected_data_route") or "")
    if data_route not in {"local_day", "validated_quote_append"}:
        scan_errors.append(f"data_route_invalid:{data_route}")
    if data_route == "validated_quote_append":
        quote_binding = scan.get("freshness_gate", {}).get("quote_file")
        if not isinstance(quote_binding, dict) or quote_binding.get("status") != "PASS":
            scan_errors.append("quote_file_binding_not_pass")
        if fingerprint.get("quote_file") != quote_binding:
            scan_errors.append("fingerprint_quote_binding_mismatch")
    else:
        quote_binding = None

    artifacts: list[dict[str, Any]] = []
    if output_json.is_file():
        artifacts.append(artifact_record(output_json, "scan_json"))
    if output_csv.is_file():
        artifacts.append(artifact_record(output_csv, "current_csv"))
    if data_route == "validated_quote_append" and args.quote_json:
        quote_artifact_path = Path(args.quote_json).resolve()
        if quote_artifact_path.is_file():
            artifacts.append(artifact_record(quote_artifact_path, "quote_json"))
        else:
            scan_errors.append(f"quote_artifact_missing:{quote_artifact_path}")
    expected_artifact_count = 3 if data_route == "validated_quote_append" else 2
    if len(artifacts) != expected_artifact_count:
        scan_errors.append(
            f"artifact_count_invalid:{len(artifacts)}!={expected_artifact_count}"
        )
    status = "PASS" if not scan_errors else "BLOCKED"
    receipt = {
        "schema_version": 3,
        "kind": "NANA_TEACHER_FIVE_STRATEGY_RUN_V3",
        "status": status,
        "reason": None if not scan_errors else "RUN_VERIFICATION_BLOCKED",
        "skill": "nana-teacher-five-strategies",
        "run_id": str(uuid.uuid4()),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "target_trade_date": scan.get("target_trade_date"),
        "target_trade_date_inferred": scan.get("target_trade_date_inferred"),
        "data_route": data_route,
        "scanned_symbols": scan.get("scanned_symbols"),
        "strategy_count": len(scan.get("strategy_summary", {})),
        "current_counts": {
            name: data.get("current_count")
            for name, data in scan.get("strategy_summary", {}).items()
        },
        "history_counts": {
            name: data.get("history_signal_count")
            for name, data in scan.get("strategy_summary", {}).items()
        },
        "freshness_gate": scan.get("freshness_gate"),
        "input_fingerprint": scan.get("input_fingerprint"),
        "quote_file": quote_binding,
        "source_code": {
            "runner": {
                "path": str(Path(__file__).resolve()),
                "sha256": sha256(Path(__file__).resolve()),
            },
            "scanner": {"path": str(SCANNER), "sha256": sha256(SCANNER)},
            "freshness_guard": {
                "path": str(FRESHNESS_GUARD),
                "sha256": sha256(FRESHNESS_GUARD),
            },
            "quote_fetcher": {
                "path": str(QUOTE_FETCHER),
                "sha256": sha256(QUOTE_FETCHER),
            },
        },
        "command": argv,
        "exit_code": completed.returncode,
        "stdout_tail": completed.stdout[-1600:],
        "stderr_tail": completed.stderr[-1600:],
        "errors": list(dict.fromkeys(scan_errors)),
        "artifacts": artifacts,
    }
    atomic_write_json(receipt_path, receipt)
    if status == "PASS":
        readback = verify_receipt(receipt_path)
        if readback["status"] != "PASS":
            receipt["status"] = "BLOCKED"
            receipt["reason"] = "PERSISTED_RECEIPT_READBACK_BLOCKED"
            receipt["errors"] = readback["errors"]
            atomic_write_json(receipt_path, receipt)
            status = "BLOCKED"
    print(
        json.dumps(
            {
                "status": status,
                "target_trade_date": receipt["target_trade_date"],
                "scanned_symbols": receipt["scanned_symbols"],
                "current_counts": receipt["current_counts"],
                "history_counts": receipt["history_counts"],
                "errors": receipt["errors"],
                "receipt": str(receipt_path),
            },
            ensure_ascii=False,
        )
    )
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
