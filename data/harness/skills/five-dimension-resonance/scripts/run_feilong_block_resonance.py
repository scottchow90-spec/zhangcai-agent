# -*- coding: utf-8 -*-
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import importlib.util
import json
import os
import struct
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mainline_scoring import (
    MODEL_VERSION as MAINLINE_MODEL_VERSION,
    load_context_from_environment,
    score_stock_in_context,
)

ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "reports" / "2026-06-03_five_dimension_feilong_block_hardening"
REPORT.mkdir(parents=True, exist_ok=True)
AUTHORITATIVE_SCORE_ENGINE = ROOT / "skills" / "a-share-15d-selection" / "scripts" / "run_a_share_15d.py"
GLOBAL_SCORE_CONTRACT = ROOT / "skills" / "stock-unified" / "references" / "short_term_strong_stock_scoring_contract.json"
GLOBAL_SCORE_CONTRACT_PAYLOAD = json.loads(GLOBAL_SCORE_CONTRACT.read_text(encoding="utf-8"))
GLOBAL_SCORE_CONTRACT_SHA256 = hashlib.sha256(GLOBAL_SCORE_CONTRACT.read_bytes()).hexdigest()
SCORE_CONTRACT_VERSION = str(GLOBAL_SCORE_CONTRACT_PAYLOAD.get("version", ""))
if SCORE_CONTRACT_VERSION != "A-SHARE-STRONG-26F-100-V6.1":
    raise RuntimeError("global_short_term_score_contract_version_mismatch")
if GLOBAL_SCORE_CONTRACT_PAYLOAD.get("fundamental_policy", {}).get("positive_weight") != 0:
    raise RuntimeError("global_short_term_score_contract_fundamental_weight_not_zero")
TDX_HUB = ROOT / "skills" / "tdx-local-hub" / "scripts" / "tdx_hub.py"
CACHE = Path(os.environ.get("OPENCLAW_STOCK_DATA_CACHE", ROOT / "data_sources" / "stock_skill_data_cache.json"))
NAME_CACHE = Path(r"E:\Codex\15_validation\stock_names_cache.json")
BLOCK_FILE = Path(r"C:\new_tdx_mock\T0002\blocknew\FLZT.blk")
TDX_TNF_FILES = [
    Path(r"C:\new_tdx_mock\T0002\hq_cache\szs.tnf"),
    Path(r"C:\new_tdx_mock\T0002\hq_cache\shs.tnf"),
    Path(r"C:\new_tdx_mock\T0002\hq_cache\bjs.tnf"),
]
TNF_HEADER_SIZE = 50
TNF_RECORD_SIZE = 360
TNF_NAME_OFFSET = 31
TNF_NAME_SIZE = 18

REQUIRED_FORMULA_ORDER = ["大牛线4.0", "飞龙在天", "游资资金监控", "机构资金监控"]
RESERVED_FORMULA_ORDER = ["庄家资金监控"]
FORMULA_ORDER = REQUIRED_FORMULA_ORDER + RESERVED_FORMULA_ORDER
HISTORICAL_FORMULA_EVIDENCE_MANIFEST = SCRIPT_DIR.parent / "reports" / "recovered" / "historical-formula-evidence-20260824.json"
HISTORICAL_FORMULA_EVIDENCE_MANIFEST_SHA256 = "bafcace42909283ca9a959e9293b4a91ea855bad44c48d945be7caf799010003"


def run_json(cmd: list[str], timeout: int = 90) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    out = (proc.stdout or "").strip()
    if not out:
        return {"ok": False, "returncode": proc.returncode, "stdout": "", "stderr": (proc.stderr or "").strip()}
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "returncode": proc.returncode, "stdout": out[-2000:], "stderr": (proc.stderr or "").strip()[-2000:]}
    data["returncode"] = proc.returncode
    if proc.stderr:
        data["stderr"] = proc.stderr[-1000:]
    return data


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_authoritative_short_term_scoring(outdir: Path) -> dict[str, Any]:
    """Run the exact V6.1 calculator for the Feilong block and validate its handoff."""
    script_dir = str(AUTHORITATIVE_SCORE_ENGINE.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(
        "a_share_26f_engine_for_five_dimension",
        AUTHORITATIVE_SCORE_ENGINE,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("authoritative_score_engine_import_failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = module.execute(outdir, "飞龙在天", generate_formatted_artifacts=False)
    ranking = payload.get("ranking") if isinstance(payload.get("ranking"), list) else []
    excluded = payload.get("excluded") if isinstance(payload.get("excluded"), list) else []
    errors: list[str] = []
    for index, item in enumerate(ranking, 1):
        contract = item.get("score_contract") if isinstance(item, dict) else None
        if not isinstance(contract, dict) or contract.get("version") != SCORE_CONTRACT_VERSION:
            errors.append(f"ranking_{index}_score_contract_version_mismatch")
        elif contract.get("global_contract_sha256") != GLOBAL_SCORE_CONTRACT_SHA256:
            errors.append(f"ranking_{index}_score_contract_hash_mismatch")
        if len(item.get("positive_dimensions", [])) != 26:
            errors.append(f"ranking_{index}_factor_count_not_26")
        if len(item.get("risks", [])) != 15:
            errors.append(f"ranking_{index}_risk_count_not_15")
        if len(item.get("hard_exclusions", [])) != 7:
            errors.append(f"ranking_{index}_hard_exclusion_count_not_7")
    if payload.get("source", {}).get("score_contract_sha256") != GLOBAL_SCORE_CONTRACT_SHA256:
        errors.append("result_score_contract_hash_mismatch")
    if errors:
        raise RuntimeError("authoritative_score_handoff_blocked:" + ",".join(errors))
    return {
        "status": "CLEAN_PASS",
        "version": SCORE_CONTRACT_VERSION,
        "global_contract_path": str(GLOBAL_SCORE_CONTRACT),
        "global_contract_sha256": GLOBAL_SCORE_CONTRACT_SHA256,
        "trade_date": payload.get("trade_date"),
        "candidate_pool": payload.get("candidate_pool", {}),
        "ranking": {str(item.get("code")): item for item in ranking if isinstance(item, dict)},
        "excluded": {str(item.get("code")): item for item in excluded if isinstance(item, dict)},
        "artifact": str(outdir / "a-share-15d-selection-result.json"),
        "artifact_sha256": sha256_file(outdir / "a-share-15d-selection-result.json"),
    }


def symbol_list_sha256(symbols: list[str]) -> str:
    payload = json.dumps(symbols, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalized_path_key(value: str | Path) -> str:
    return os.path.normcase(str(Path(value).resolve(strict=False)))


def nested_text_contains(value: Any, expected: str) -> bool:
    if isinstance(value, str):
        return expected in value or json.dumps(expected, ensure_ascii=False)[1:-1] in value
    if isinstance(value, dict):
        return any(nested_text_contains(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(nested_text_contains(item, expected) for item in value)
    return False


def latest_day_trade_date(path: Path) -> str:
    size = path.stat().st_size
    if size < 32 or size % 32:
        return ""
    with path.open("rb") as handle:
        handle.seek(-32, os.SEEK_END)
        record = handle.read(32)
    value = struct.unpack("<I", record[:4])[0]
    text = str(value)
    return text if len(text) == 8 and text.isdigit() else ""


def local_day_path(symbol: str) -> Path:
    code, market = symbol.split(".", 1)
    prefix = market.lower()
    return Path(r"C:\new_tdx_mock\vipdoc") / prefix / "lday" / f"{prefix}{code}.day"


def resolve_current_trade_date(rows: list[dict[str, str]]) -> str:
    dates = {latest_day_trade_date(local_day_path(row["symbol"])) for row in rows}
    dates.discard("")
    return dates.pop() if len(dates) == 1 else ""


def _fingerprint_matches(path: Path, expected: dict[str, Any]) -> bool:
    if not path.is_file():
        return False
    stat = path.stat()
    return (
        sha256_file(path) == str(expected.get("sha256", "")).lower()
        and stat.st_size == int(expected.get("size", -1))
        and stat.st_mtime_ns == int(expected.get("mtime_ns", -1))
    )


def load_historical_formula_evidence(
    rows: list[dict[str, str]],
    manifest_path: Path,
    expected_manifest_sha256: str,
    trade_date: str,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    audit: dict[str, Any] = {
        "schema": "FIVE_DIMENSION_FORMULA_EVIDENCE_AUDIT_V2",
        "mode": "historical_exact_input_reuse",
        "status": "REJECTED",
        "manifest": {"path": str(manifest_path), "sha256": ""},
        "errors": [],
    }
    errors: list[str] = audit["errors"]
    if not manifest_path.is_file():
        errors.append("historical_formula_evidence_manifest_missing")
        return audit, {}
    actual_manifest_hash = sha256_file(manifest_path)
    audit["manifest"]["sha256"] = actual_manifest_hash
    if not expected_manifest_sha256 or actual_manifest_hash != expected_manifest_sha256.lower():
        errors.append("historical_formula_evidence_manifest_hash_mismatch")
        return audit, {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        errors.append("historical_formula_evidence_manifest_unreadable")
        return audit, {}
    if manifest.get("schema") != "FIVE_DIMENSION_HISTORICAL_FORMULA_EVIDENCE_V1" or manifest.get("status") != "VERIFIED":
        errors.append("historical_formula_evidence_manifest_invalid")

    artifacts: dict[str, dict[str, Any]] = {}
    for key in ("source_artifact", "source_receipt"):
        item = manifest.get(key, {})
        path = Path(str(item.get("path", "")))
        actual_hash = sha256_file(path) if path.is_file() else ""
        expected_hash = str(item.get("sha256", "")).lower()
        artifact_row = {
            "path": str(path.resolve(strict=False)),
            "sha256": actual_hash,
            "matched": bool(actual_hash and actual_hash == expected_hash),
        }
        if key == "source_artifact":
            artifact_row["origin_path"] = str(Path(str(item.get("origin_path", item.get("path", "")))).resolve(strict=False))
        artifacts[key] = artifact_row
        if not artifacts[key]["matched"]:
            errors.append(f"{key}_hash_mismatch")
    audit.update(artifacts)

    provenance = manifest.get("recovery_provenance", {})
    provenance_path = Path(str(provenance.get("path", "")))
    provenance_ordinal = int(provenance.get("ordinal", -1))
    provenance_line = b""
    provenance_event: dict[str, Any] = {}
    if provenance_path.is_file():
        for raw_line in provenance_path.read_bytes().splitlines():
            try:
                event = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if int(event.get("ordinal", -2)) == provenance_ordinal:
                provenance_line = raw_line
                provenance_event = event
                break
    provenance_line_hash = hashlib.sha256(provenance_line).hexdigest() if provenance_line else ""
    provenance_artifact_hash = str(provenance.get("artifact_sha256", "")).lower()
    source_origin_path = str(manifest.get("source_artifact", {}).get("origin_path", ""))
    provenance_matched = (
        bool(provenance_line)
        and provenance_line_hash == str(provenance.get("line_sha256", "")).lower()
        and provenance_artifact_hash == str(manifest.get("source_artifact", {}).get("sha256", "")).lower()
        and provenance_artifact_hash.encode("ascii") in provenance_line
        and bool(source_origin_path)
        and nested_text_contains(provenance_event, source_origin_path)
    )
    audit["recovery_provenance"] = {
        "path": str(provenance_path),
        "ordinal": provenance_ordinal,
        "line_sha256": provenance_line_hash,
        "artifact_sha256": provenance_artifact_hash,
        "origin_path": str(Path(source_origin_path).resolve(strict=False)) if source_origin_path else "",
        "matched": provenance_matched,
    }
    if not provenance_matched:
        errors.append("recovery_provenance_mismatch")

    report: dict[str, Any] = {}
    receipt: dict[str, Any] = {}
    if artifacts.get("source_artifact", {}).get("matched"):
        try:
            report = json.loads(Path(artifacts["source_artifact"]["path"]).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            errors.append("source_artifact_unreadable")
    if artifacts.get("source_receipt", {}).get("matched"):
        try:
            receipt = json.loads(Path(artifacts["source_receipt"]["path"]).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            errors.append("source_receipt_unreadable")
    if report.get("status") != "CLEAN_PASS":
        errors.append("source_artifact_not_clean")
    if (
        receipt.get("status") != "CLEAN_PASS"
        or receipt.get("skill_id") != "five-dimension-resonance"
        or receipt.get("tdx_process_integrity", {}).get("status") != "CLEAN_PASS"
        or receipt.get("tdx_process_integrity", {}).get("errors")
    ):
        errors.append("source_receipt_not_clean")

    receipt_business_result: dict[str, Any] = {}
    receipt_business_result_path = Path()
    receipt_business_result_hash = ""
    receipt_business_result_entries = [
        item
        for item in receipt.get("required_artifacts", [])
        if isinstance(item, dict) and Path(str(item.get("path", ""))).name.casefold() == "business_result.json"
    ]
    receipt_business_result_artifact = (
        receipt_business_result_entries[0]
        if len(receipt_business_result_entries) == 1
        else {}
    )
    if receipt_business_result_artifact:
        receipt_business_result_path = Path(str(receipt_business_result_artifact.get("path", "")))
        if receipt_business_result_path.is_file():
            receipt_business_result_hash = sha256_file(receipt_business_result_path)
            try:
                receipt_business_result = json.loads(receipt_business_result_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                receipt_business_result = {}
    receipt_bound_artifact_path = str(
        receipt_business_result.get("artifacts", {}).get("mainline_report", "")
    )
    expected_origin_path = str(
        manifest.get("source_artifact", {}).get("origin_path", "")
    )
    source_receipt_artifact_matched = (
        len(receipt_business_result_entries) == 1
        and bool(receipt_business_result_hash)
        and receipt_business_result_hash == str(receipt_business_result_artifact.get("sha256", "")).lower()
        and receipt_business_result_path.stat().st_size == int(receipt_business_result_artifact.get("size", -1))
        and receipt_business_result.get("schema") == "STOCK_CANONICAL_BUSINESS_RESULT_V1"
        and receipt_business_result.get("skill_id") == "five-dimension-resonance"
        and receipt_business_result.get("status") == "CLEAN_PASS"
        and bool(receipt_bound_artifact_path)
        and bool(expected_origin_path)
        and normalized_path_key(receipt_bound_artifact_path) == normalized_path_key(expected_origin_path)
        and normalized_path_key(expected_origin_path) == normalized_path_key(source_origin_path)
    )
    audit["source_receipt_artifact_binding"] = {
        "matched": source_receipt_artifact_matched,
        "business_result_path": str(receipt_business_result_path.resolve(strict=False)) if receipt_business_result_artifact else "",
        "business_result_sha256": receipt_business_result_hash,
        "receipt_bound_artifact_path": str(Path(receipt_bound_artifact_path).resolve(strict=False)) if receipt_bound_artifact_path else "",
        "expected_origin_path": str(Path(expected_origin_path).resolve(strict=False)) if expected_origin_path else "",
    }
    if not source_receipt_artifact_matched:
        if (
            receipt_business_result_hash
            and receipt_business_result_hash == str(receipt_business_result_artifact.get("sha256", "")).lower()
            and receipt_bound_artifact_path
            and expected_origin_path
            and normalized_path_key(receipt_bound_artifact_path) != normalized_path_key(expected_origin_path)
        ):
            errors.append("source_receipt_artifact_path_mismatch")
        else:
            errors.append("source_receipt_business_result_binding_mismatch")

    if manifest.get("reuse_scope") != "raw_scan_only":
        errors.append("historical_formula_reuse_scope_invalid")
    if manifest.get("formula_names_ordered") != FORMULA_ORDER:
        errors.append("historical_formula_order_binding_mismatch")

    current_symbols = [row["symbol"] for row in rows]
    expected_symbols = manifest.get("candidate_binding", {}).get("symbols", [])
    expected_symbols_hash = manifest.get("candidate_binding", {}).get("sha256")
    report_results = report.get("all_results", []) if isinstance(report.get("all_results"), list) else []
    report_symbols = [str(item.get("symbol", "")) for item in report_results]
    candidate_matched = (
        current_symbols == expected_symbols == report_symbols
        and symbol_list_sha256(current_symbols) == expected_symbols_hash
        and report.get("scan_count") == len(current_symbols)
        and report.get("candidate_pool", {}).get("count") == len(current_symbols)
        and report.get("five_formula_success_count") == len(current_symbols)
    )
    audit["candidate_binding"] = {
        "matched": candidate_matched,
        "symbols": current_symbols,
        "sha256": symbol_list_sha256(current_symbols),
    }
    if not candidate_matched:
        errors.append("candidate_binding_mismatch")

    manifest_trade_date = str(manifest.get("trade_date", ""))
    trade_date_matched = bool(trade_date and trade_date == manifest_trade_date)
    audit["trade_date_binding"] = {"matched": trade_date_matched, "trade_date": trade_date, "expected": manifest_trade_date}
    if not trade_date_matched:
        errors.append("trade_date_binding_mismatch")

    kline_by_symbol = {str(item.get("symbol", "")): item for item in manifest.get("kline_inputs", []) if isinstance(item, dict)}
    report_by_symbol = {str(item.get("symbol", "")): item for item in report_results if isinstance(item, dict)}
    kline_checks: list[dict[str, Any]] = []
    for symbol in current_symbols:
        expected = kline_by_symbol.get(symbol, {})
        path = Path(str(expected.get("path", "")))
        report_path = str(report_by_symbol.get(symbol, {}).get("kline_evidence", {}).get("path", ""))
        matched = (
            bool(expected)
            and _fingerprint_matches(path, expected)
            and latest_day_trade_date(path) == trade_date
            and str(expected.get("latest_trade_date", "")) == trade_date
            and report_path == str(path)
        )
        stat = path.stat() if path.is_file() else None
        kline_checks.append({
            "symbol": symbol,
            "path": str(path.resolve(strict=False)),
            "sha256": sha256_file(path) if path.is_file() else "",
            "size": stat.st_size if stat else -1,
            "mtime_ns": stat.st_mtime_ns if stat else -1,
            "latest_trade_date": latest_day_trade_date(path) if path.is_file() else "",
            "matched": matched,
        })
        if not matched:
            errors.append(f"kline_fingerprint_mismatch:{symbol}")
    audit["kline_binding"] = {"matched": bool(current_symbols) and all(item["matched"] for item in kline_checks), "items": kline_checks}

    required_roles = {"tdx_hub", "tq_init", "tqcenter", "reserved_formula"}
    executor_checks: list[dict[str, Any]] = []
    manifest_roles: set[str] = set()
    for expected in manifest.get("formula_executor_inputs", []):
        if not isinstance(expected, dict):
            continue
        role = str(expected.get("role", ""))
        manifest_roles.add(role)
        path = Path(str(expected.get("path", "")))
        matched = _fingerprint_matches(path, expected)
        stat = path.stat() if path.is_file() else None
        executor_checks.append({
            "role": role,
            "path": str(path.resolve(strict=False)),
            "sha256": sha256_file(path) if path.is_file() else "",
            "size": stat.st_size if stat else -1,
            "mtime_ns": stat.st_mtime_ns if stat else -1,
            "matched": matched,
        })
        if not matched:
            errors.append(f"formula_executor_fingerprint_mismatch:{role}")
    if manifest_roles != required_roles:
        errors.append("formula_executor_roles_incomplete")
    audit["formula_executor_binding"] = {
        "matched": manifest_roles == required_roles and all(item["matched"] for item in executor_checks),
        "items": executor_checks,
    }

    scans: dict[str, dict[str, Any]] = {}
    for symbol in current_symbols:
        source_result = report_by_symbol.get(symbol, {})
        scan = source_result.get("raw_scan", {}) if isinstance(source_result, dict) else {}
        items = scan.get("items", []) if isinstance(scan, dict) else []
        formula_names = [item.get("formula") for item in items if isinstance(item, dict)]
        item_init_paths = {str(item.get("init_path", "")) for item in items if isinstance(item, dict)}
        reserved_paths = {str(item.get("registry_path", "")) for item in items if isinstance(item, dict) and item.get("registry_path")}
        manifest_executor_paths = {item["role"]: item["path"] for item in executor_checks}
        valid_scan = (
            scan.get("ok") is True
            and scan.get("symbol") == symbol
            and formula_names == FORMULA_ORDER
            and all(item.get("ok") is True for item in items)
            and not scan.get("failed_formulas")
            and item_init_paths == {manifest_executor_paths.get("tq_init", "")}
            and reserved_paths == {manifest_executor_paths.get("reserved_formula", "")}
        )
        if not valid_scan:
            errors.append(f"source_formula_scan_invalid:{symbol}")
        else:
            scans[symbol] = scan

    if errors:
        return audit, {}
    reuse_evidence_manifest = {
        "schema": "FIVE_DIMENSION_REUSE_EVIDENCE_MANIFEST_V1",
        "reuse_scope": "raw_scan_only",
        "source_receipt": {
            "path": artifacts["source_receipt"]["path"],
            "sha256": artifacts["source_receipt"]["sha256"],
            "business_result_path": audit["source_receipt_artifact_binding"]["business_result_path"],
            "business_result_sha256": audit["source_receipt_artifact_binding"]["business_result_sha256"],
        },
        "source_artifact": {
            "path": artifacts["source_artifact"]["path"],
            "origin_path": artifacts["source_artifact"]["origin_path"],
            "sha256": artifacts["source_artifact"]["sha256"],
        },
        "immutable_line_locator": {
            "path": str(provenance_path.resolve(strict=False)),
            "ordinal": provenance_ordinal,
        },
        "immutable_line_sha256": provenance_line_hash,
        "trade_date": trade_date,
        "candidates_ordered": current_symbols,
        "candidates_ordered_sha256": symbol_list_sha256(current_symbols),
        "kline_inputs": [
            {key: item[key] for key in ("symbol", "path", "sha256", "size", "mtime_ns", "latest_trade_date")}
            for item in kline_checks
        ],
        "formula_executor_inputs": [
            {key: item[key] for key in ("role", "path", "sha256", "size", "mtime_ns")}
            for item in executor_checks
        ],
        "formula_names_ordered": list(FORMULA_ORDER),
    }
    audit["reuse_evidence_manifest"] = reuse_evidence_manifest
    audit["reuse_evidence_manifest_sha256"] = canonical_json_sha256(reuse_evidence_manifest)
    audit["status"] = "VERIFIED"
    audit["formula_result_count"] = len(scans)
    return audit, scans


def parse_block(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="gbk", errors="replace")
    rows = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw:
            continue
        code = raw[-6:]
        if not code.isdigit():
            continue
        market = "SZ" if code.startswith(("0", "1", "2", "3")) else "SH"
        rows.append({"raw": raw, "code": code, "symbol": f"{code}.{market}", "market": market, "market_prefix": raw[:-6]})
    return rows


def decode_tnf_field(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("gbk", errors="ignore").strip()


def load_tdx_tnf_names() -> dict[str, dict[str, Any]]:
    names: dict[str, dict[str, Any]] = {}
    for path in TDX_TNF_FILES:
        if not path.exists():
            continue
        data = path.read_bytes()
        usable = len(data) - TNF_HEADER_SIZE
        if usable <= 0:
            continue
        record_count = usable // TNF_RECORD_SIZE
        for idx in range(record_count):
            offset = TNF_HEADER_SIZE + idx * TNF_RECORD_SIZE
            record = data[offset : offset + TNF_RECORD_SIZE]
            code = decode_tnf_field(record[:6])
            if len(code) != 6 or not code.isdigit():
                continue
            name = decode_tnf_field(record[TNF_NAME_OFFSET : TNF_NAME_OFFSET + TNF_NAME_SIZE])
            if name:
                names.setdefault(code, {"code": code, "name": name, "source": f"tdx_tnf:{path.name}"})
    return names


def load_cache_maps() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    data = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    by_code: dict[str, dict[str, Any]] = {}
    for key in ["zt_pool"]:
        for item in data.get(key, []):
            code = str(item.get("code", "")).zfill(6)
            if code:
                by_code[code] = dict(item)
    if NAME_CACHE.exists():
        names = json.loads(NAME_CACHE.read_text(encoding="utf-8"))
        for code, name in names.items():
            by_code.setdefault(str(code).zfill(6), {"code": str(code).zfill(6), "name": name, "source": "stock_names_cache"})
    for code, item in load_tdx_tnf_names().items():
        by_code.setdefault(code, item)
    return by_code, data


def first_value(fields: dict[str, Any], name: str, default: Any = 0) -> Any:
    value = fields.get(name, default)
    if isinstance(value, list):
        if not value:
            return default
        value = value[-1]
    if value is None:
        return default
    return value


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        text = str(value).strip()
        if not text or text.lower() == "none":
            return default
        return float(text)
    except Exception:
        return default


def fields_for(scan: dict[str, Any], formula: str, symbol: str) -> dict[str, Any]:
    for item in scan.get("items", []):
        if item.get("formula") == formula:
            res = item.get("result", {})
            return res.get(symbol, {}) if isinstance(res, dict) else {}
    return {}


def item_ok(scan: dict[str, Any], formula: str) -> bool:
    for item in scan.get("items", []):
        if item.get("formula") == formula:
            return bool(item.get("ok"))
    return False


def formula_state(scan: dict[str, Any]) -> tuple[dict[str, bool], dict[str, bool]]:
    required = {f: item_ok(scan, f) for f in REQUIRED_FORMULA_ORDER}
    reserved = {f: item_ok(scan, f) for f in RESERVED_FORMULA_ORDER}
    return required, reserved


def kline_3day_pct(symbol: str) -> tuple[float, dict[str, Any]]:
    data = run_json([sys.executable, str(TDX_HUB), "kline", symbol, "--period", "day", "--limit", "5"], timeout=30)
    rows = data.get("rows", []) or data.get("data", []) or []
    if len(rows) >= 4:
        prev = to_float(rows[-4].get("close"))
        last = to_float(rows[-1].get("close"))
        pct = (last - prev) / prev * 100 if prev else 0.0
        return round(pct, 2), data
    return 0.0, data


def classify_wave(wave: float, segment: float) -> str:
    if wave >= 90:
        return "极高位过热"
    if wave >= 80:
        return "高位钝化"
    if wave >= 50 and segment >= 50:
        return "主升健康"
    if wave >= 20:
        return "修复确认"
    return "低位观察"


def stars_to_score(stars: float, weight: float) -> float:
    return stars / 5.0 * weight


def build_analysis(
    row: dict[str, str],
    info: dict[str, Any],
    scan: dict[str, Any],
    kline_pct3: float,
    mainline_context: dict[str, Any] | None = None,
    authoritative_score: dict[str, Any] | None = None,
    authoritative_exclusion: dict[str, Any] | None = None,
) -> dict[str, Any]:
    symbol = row["symbol"]
    name = str(info.get("name", "")).strip()
    dnx = fields_for(scan, "大牛线4.0", symbol)
    fl = fields_for(scan, "飞龙在天", symbol)
    yz = fields_for(scan, "游资资金监控", symbol)
    jg = fields_for(scan, "机构资金监控", symbol)
    zj = fields_for(scan, "庄家资金监控", symbol)

    ema9 = to_float(first_value(dnx, "EMA9"))
    ema10 = to_float(first_value(dnx, "EMA10"))
    ema11 = to_float(first_value(dnx, "EMA11"))
    trend = "多头" if ema9 > ema10 > ema11 else ("空头" if ema9 < ema10 < ema11 else "中性")
    dnx_bottom = str(first_value(dnx, "OUTPUT30", "0.00")) != "0.00"
    dnx_signal = "多头抄底共振" if trend == "多头" and dnx_bottom else ("多头趋势" if trend == "多头" else ("抄底信号" if dnx_bottom else f"{trend}趋势"))

    wave = to_float(first_value(fl, "波"))
    segment = to_float(first_value(fl, "段"))
    wave_label = classify_wave(wave, segment)
    burst_flags = []
    for key, label in [("OUTPUT3", "波段密码打板"), ("OUTPUT4", "私募秘进"), ("OUTPUT5", "暴涨启动"), ("OUTPUT6", "主升启动")]:
        value = first_value(fl, key, "0.00")
        if str(value).strip() not in {"", "0", "0.0", "0.00"}:
            burst_flags.append(label)
    burst = "+".join(burst_flags) if burst_flags else "未触发爆发"

    youzi = to_float(first_value(yz, "买方意向"))
    youzi_label = "强攻击" if youzi > 2 else ("正向攻击" if youzi > 0.5 else ("弱正向" if youzi >= 0 else "游资退潮"))
    jigou_in = to_float(first_value(jg, "机构大单进"))
    jigou_out = to_float(first_value(jg, "机构大单出"))
    jigou_label = "强机构参与" if jigou_in > 2 else ("机构参与" if jigou_in > 0.5 else ("弱参与" if jigou_in >= 0 else "机构转弱"))
    if jigou_out >= 1:
        jigou_label += "+机构出货预警"
    zhuang = to_float(first_value(zj, "控盘程度"))
    zhuang_label = "高控盘" if zhuang > 100 else ("控盘增强" if zhuang >= 50 else ("初步控盘" if zhuang > 0 else "无显著控盘"))

    pct = to_float(info.get("pct"))
    open_count = int(to_float(info.get("open_count"), 0))
    streak = int(to_float(info.get("streak"), 1))
    industry = str(info.get("industry", "行业已解析"))

    mainline_dimension = score_stock_in_context(row["code"], mainline_context or {})
    score_record = authoritative_score if isinstance(authoritative_score, dict) else None
    exclusion_record = authoritative_exclusion if isinstance(authoritative_exclusion, dict) else None
    contract = score_record.get("score_contract") if score_record else None
    contract_valid = (
        isinstance(contract, dict)
        and contract.get("version") == SCORE_CONTRACT_VERSION
        and contract.get("global_contract_sha256") == GLOBAL_SCORE_CONTRACT_SHA256
        and contract.get("factor_count") == 26
        and contract.get("fundamental_positive_weight") == 0
        and len(score_record.get("positive_dimensions", [])) == 26
        and len(score_record.get("risks", [])) == 15
        and len(score_record.get("hard_exclusions", [])) == 7
    )
    if contract_valid:
        score_status = "VERIFIED"
        hard_exclusions = list(score_record.get("hard_exclusions", []))
        hard_status = "通过" if score_record.get("passed_hard_gate") is True else "剔除"
        risk_items = list(score_record.get("risks", []))
        dimension_scores = list(score_record.get("positive_dimensions", []))
        positive = float(score_record.get("positive_score", 0.0))
        risk_deduction = float(score_record.get("risk_deduction", 0.0))
        final = float(score_record.get("final_score", 0.0))
        score_contract = dict(contract)
    elif exclusion_record:
        score_status = "HARD_EXCLUDED"
        hard_exclusions = list(exclusion_record.get("reasons", []))
        hard_status = "剔除"
        risk_items = []
        dimension_scores = []
        positive = risk_deduction = final = 0.0
        score_contract = {
            "version": SCORE_CONTRACT_VERSION,
            "global_contract_path": str(GLOBAL_SCORE_CONTRACT),
            "global_contract_sha256": GLOBAL_SCORE_CONTRACT_SHA256,
            "status": "NOT_SCORED_HARD_EXCLUDED",
            "fundamental_positive_weight": 0,
        }
    else:
        score_status = "DATA_REQUIRED"
        hard_exclusions = ["权威V6.1评分记录缺失或契约不匹配"]
        hard_status = "数据不足"
        risk_items = []
        dimension_scores = []
        positive = risk_deduction = final = 0.0
        score_contract = {
            "version": SCORE_CONTRACT_VERSION,
            "global_contract_path": str(GLOBAL_SCORE_CONTRACT),
            "global_contract_sha256": GLOBAL_SCORE_CONTRACT_SHA256,
            "status": "DATA_REQUIRED",
            "fundamental_positive_weight": 0,
        }
    grade = "S" if final >= 80 else ("A" if final >= 70 else ("B" if final >= 55 else "C"))
    if hard_status != "通过":
        grade = "C"

    required_formulas_ok, reserved_formulas_ok = formula_state(scan)
    formulas_ok = {**required_formulas_ok, **reserved_formulas_ok}
    return {
        "code": row["code"],
        "symbol": symbol,
        "name": name,
        "name_source": info.get("source", ""),
        "industry": industry,
        "pct": round(pct, 2),
        "price": info.get("price", 0),
        "limit_stat": info.get("limit_stat", "已解析"),
        "open_count": open_count,
        "streak": streak,
        "three_day_pct": kline_pct3,
        "formulas_ok": formulas_ok,
        "required_formulas_ok": required_formulas_ok,
        "reserved_formulas_ok": reserved_formulas_ok,
        "reserved_failed_formulas": [name for name, ok in reserved_formulas_ok.items() if not ok],
        "five_formula_ok": all(required_formulas_ok.values()),
        "signals": {
            "大牛线": dnx_signal,
            "飞龙波段": f"{wave_label}(波{wave:.2f}/段{segment:.2f})",
            "飞龙爆发": burst,
            "游资": f"{youzi_label}(买方意向{youzi:.2f})",
            "机构": f"{jigou_label}(机构大单进{jigou_in:.2f})",
            "庄家": f"{zhuang_label}(控盘{zhuang:.2f}, 保留项)",
            "主线": (
                f"{mainline_dimension['board'].get('name') or '未匹配主线'}，"
                f"板块{mainline_dimension['board'].get('status')}，"
                f"个股正宗度{mainline_dimension['stock_fit'].get('status')}"
            ),
        },
        "hard_exclusion_status": hard_status,
        "hard_exclusions": hard_exclusions,
        "passed_hard_gate": score_record.get("passed_hard_gate") is True if score_record else False,
        "risk_items": risk_items,
        "risk_deduction": risk_deduction,
        "unverified_risk_count": 0,
        "dimension_scores": dimension_scores,
        "mainline_scoring": mainline_dimension,
        "positive_score": round(positive, 2),
        "final_score": final,
        "grade": grade,
        "decision_eligible": score_status == "VERIFIED" and hard_status == "通过" and mainline_dimension["decision_eligible"],
        "score_confidence": "VERIFIED" if score_status == "VERIFIED" else "DEGRADED",
        "score_status": score_status,
        "score_contract": score_contract,
        "score_source": {
            "owner_skill_id": "a-share-15d-selection",
            "reuse_mode": "authoritative_score_reuse_with_mainline_enrichment",
            "mainline_model_version": MAINLINE_MODEL_VERSION,
        },
        "next_session_plan": {
            "进攻确认": "板块继续放量且个股维持五公式正向共振",
            "强弱分界": "飞龙波段不转退潮、游资/机构资金不同时转弱",
            "防守位": "跌破当日强势K线低点或主趋势线降级",
            "放弃条件": "触发V6.1硬闸、机构出货叠加飞龙退潮或趋势失效",
            "只观察不参与条件": "连续一字或开盘无承接",
            "次日重点看": "竞价强度、开板承接、资金三件套是否继续同步",
        },
        "raw_scan": scan,
    }


REQUIRED_MAINLINE_SOURCES = (
    "duanxianxia_plate",
    "duanxianxia_pool",
    "duanxianxia_membership",
    "lianban",
    "lianban_history",
    "tdx_constituents",
    "tdx_turnover",
)
VERIFIED_SOURCE_STATES = {"VERIFIED", "CLEAN_PASS"}


def classify_execution_outcome(
    execution_ok: bool,
    analyses: list[dict[str, Any]],
    mainline_context: dict[str, Any],
) -> dict[str, Any]:
    dimensions = [item.get("mainline_scoring", {}) for item in analyses]
    eligible_count = sum(item.get("decision_eligible") is True for item in analyses)
    score_verified_count = sum(item.get("score_status") == "VERIFIED" for item in analyses)
    score_excluded_count = sum(item.get("score_status") == "HARD_EXCLUDED" for item in analyses)
    score_data_required_count = sum(item.get("score_status") == "DATA_REQUIRED" for item in analyses)
    authenticity_count = sum(
        item.get("stock_fit", {}).get("status") == "VERIFIED"
        for item in dimensions
    )
    gate_failed_count = sum(item.get("status") == "GATE_FAILED" for item in dimensions)
    degraded_count = sum(item.get("status") == "DEGRADED" for item in dimensions)
    reasons: list[str] = []
    source_status = mainline_context.get("source_status", {})
    for name in REQUIRED_MAINLINE_SOURCES:
        state = source_status.get(name) if isinstance(source_status, dict) else None
        if state not in VERIFIED_SOURCE_STATES:
            reasons.append(f"mainline_source_not_verified:{name}:{state or 'missing'}")
    for issue in mainline_context.get("issues", []) if isinstance(mainline_context, dict) else []:
        reasons.append(f"mainline_issue:{issue}")
    if authenticity_count != len(analyses):
        reasons.append("stock_authenticity_incomplete")
    if score_data_required_count:
        reasons.append(f"authoritative_v61_score_incomplete:{score_data_required_count}")
    if score_verified_count + score_excluded_count != len(analyses):
        reasons.append("authoritative_v61_pool_coverage_incomplete")

    if not execution_ok:
        execution_status = "NEEDS_REPAIR"
        decision_status = "DATA_REQUIRED"
        reasons.append("formula_or_scan_execution_incomplete")
    elif reasons:
        execution_status = "DATA_REQUIRED"
        decision_status = "DATA_REQUIRED"
    else:
        execution_status = "CLEAN_PASS"
        if eligible_count > 0:
            decision_status = "SIGNAL_FOUND"
        elif analyses and gate_failed_count == len(analyses):
            decision_status = "NO_SIGNAL"
        else:
            decision_status = "DATA_REQUIRED"
            reasons.append("candidate_board_evidence_incomplete")

    return {
        "execution_status": execution_status,
        "decision_status": decision_status,
        "decision_eligible_count": eligible_count,
        "score_verified_count": score_verified_count,
        "score_excluded_count": score_excluded_count,
        "score_data_required_count": score_data_required_count,
        "authenticity_verified_count": authenticity_count,
        "gate_failed_count": gate_failed_count,
        "degraded_count": degraded_count,
        "data_required_reasons": list(dict.fromkeys(reasons)),
    }


def main() -> int:
    # 2026-06-22 加固: 支持 --help / --dry-run 快速响应 (不触发业务逻辑, 避免 150s/row tdx_hub 调用)
    import argparse
    p = argparse.ArgumentParser(description="五维共振 / 飞龙在天共振扫描 (统一入口 --help)")
    p.add_argument("--help-extended", action="store_true", help="扩展帮助")
    p.add_argument("--dry-run", action="store_true", help="检查环境/数据源后立即退出")
    ns, _unknown = p.parse_known_args()
    if ns.help_extended:
        print(json.dumps({
            "skill": "five-dimension-resonance",
            "name_cn": "五维共振选股",
            "candidate_pool": str(BLOCK_FILE),
            "data_cache": str(CACHE),
            "report_dir": str(REPORT),
            "note": "业务逻辑默认执行; --help 立即返回; --dry-run 检查环境后退出",
        }, ensure_ascii=False, indent=2))
        return 0
    if ns.dry_run:
        out = {
            "status": "DRY_RUN_OK",
            "skill": "five-dimension-resonance",
            "block_file_exists": BLOCK_FILE.exists(),
            "block_file_size": BLOCK_FILE.stat().st_size if BLOCK_FILE.exists() else 0,
            "cache_exists": CACHE.exists(),
            "tdx_hub_exists": TDX_HUB.exists(),
            "report_dir_exists": REPORT.exists(),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    start = time.perf_counter()
    rows = parse_block(BLOCK_FILE)
    info_map, cache = load_cache_maps()
    mainline_context = load_context_from_environment()
    current_trade_date = resolve_current_trade_date(rows)
    try:
        score_handoff = run_authoritative_short_term_scoring(REPORT / "authoritative_v61")
        covered_codes = set(score_handoff["ranking"]) | set(score_handoff["excluded"])
        expected_codes = {row["code"] for row in rows}
        if score_handoff.get("trade_date") != current_trade_date:
            raise RuntimeError("authoritative_score_trade_date_mismatch")
        if covered_codes != expected_codes:
            raise RuntimeError("authoritative_score_candidate_coverage_mismatch")
    except Exception as exc:
        score_handoff = {
            "status": "DATA_REQUIRED",
            "version": SCORE_CONTRACT_VERSION,
            "global_contract_path": str(GLOBAL_SCORE_CONTRACT),
            "global_contract_sha256": GLOBAL_SCORE_CONTRACT_SHA256,
            "trade_date": current_trade_date,
            "ranking": {},
            "excluded": {},
            "error": f"{type(exc).__name__}: {exc}",
        }
    historical_formula_evidence, historical_scans = load_historical_formula_evidence(
        rows,
        HISTORICAL_FORMULA_EVIDENCE_MANIFEST,
        HISTORICAL_FORMULA_EVIDENCE_MANIFEST_SHA256,
        current_trade_date,
    )
    analyses = []
    scan_outputs = []
    for idx, row in enumerate(rows, 1):
        info = info_map.get(row["code"], {"code": row["code"], "name": "", "source": "missing"})
        live_scan = run_json([sys.executable, str(TDX_HUB), "five", row["symbol"]], timeout=150)
        live_required_ok, _live_reserved_ok = formula_state(live_scan)
        historical_scan = historical_scans.get(row["symbol"])
        historical_reused = not all(live_required_ok.values()) and historical_formula_evidence.get("status") == "VERIFIED" and historical_scan is not None
        scan = historical_scan if historical_reused else live_scan
        pct3, kline = kline_3day_pct(row["symbol"])
        analysis = build_analysis(
            row,
            info,
            scan,
            pct3,
            mainline_context,
            score_handoff.get("ranking", {}).get(row["code"]),
            score_handoff.get("excluded", {}).get(row["code"]),
        )
        analysis["rank_scan_order"] = idx
        analysis["kline_evidence"] = {"ok": bool(kline.get("ok")), "path": kline.get("path"), "count": kline.get("count"), "tail": kline.get("rows", [])[-3:] if isinstance(kline.get("rows"), list) else []}
        analysis["formula_evidence"] = {
            "mode": "historical_exact_input_reuse" if historical_reused else "live_tq_execution",
            "historical_evidence_status": historical_formula_evidence.get("status"),
            "historical_manifest_sha256": historical_formula_evidence.get("manifest", {}).get("sha256"),
            "reuse_evidence_manifest_sha256": historical_formula_evidence.get("reuse_evidence_manifest_sha256"),
            "source_receipt_sha256": historical_formula_evidence.get("source_receipt", {}).get("sha256"),
            "source_artifact_sha256": historical_formula_evidence.get("source_artifact", {}).get("sha256"),
            "immutable_line_sha256": historical_formula_evidence.get("recovery_provenance", {}).get("line_sha256"),
            "live_scan_ok": all(live_required_ok.values()),
            "live_scan": live_scan if historical_reused else None,
        }
        analyses.append(analysis)
        scan_outputs.append({"symbol": row["symbol"], "name": analysis["name"], "five_formula_ok": analysis["five_formula_ok"], "final_score": analysis["final_score"]})
        print(json.dumps({"progress": f"{idx}/{len(rows)}", "symbol": row["symbol"], "name": analysis["name"], "five_formula_ok": analysis["five_formula_ok"], "score": analysis["final_score"]}, ensure_ascii=False), flush=True)

    ranked = sorted(
        [item for item in analyses if item.get("score_status") == "VERIFIED" and item.get("passed_hard_gate") is True],
        key=lambda item: (-float(item["final_score"]), -float(item["positive_score"]), item["code"]),
    )
    top10 = []
    for i, item in enumerate(ranked[:10], 1):
        top10.append({
            "rank": i,
            "symbol": item["symbol"],
            "name": item["name"],
            "score": item["final_score"],
            "grade": item["grade"],
            "大牛线": item["signals"]["大牛线"],
            "飞龙波段": item["signals"]["飞龙波段"],
            "飞龙爆发": item["signals"]["飞龙爆发"],
            "游资": item["signals"]["游资"],
            "机构": item["signals"]["机构"],
            "庄家": item["signals"]["庄家"],
            "主线": item["signals"]["主线"],
            "风险": item["hard_exclusion_status"] + f"/扣{item['risk_deduction']}",
        })
    top3 = ranked[:3]
    wave_distribution: dict[str, int] = {}
    for item in ranked[:10]:
        label = item["signals"]["飞龙波段"].split("(")[0]
        wave_distribution[label] = wave_distribution.get(label, 0) + 1

    execution_ok = bool(rows) and len(analyses) == len(rows) and all(x["five_formula_ok"] for x in analyses)
    outcome = classify_execution_outcome(bool(execution_ok), analyses, mainline_context)
    mainline_verified_count = outcome["decision_eligible_count"]
    result = {
        "status": outcome["execution_status"],
        "decision_status": outcome["decision_status"],
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "skill": "five-dimension-resonance",
        "name_cn": "五维共振选股",
        "candidate_pool": {
            "name": "飞龙在天",
            "code": "FLZT",
            "file": str(BLOCK_FILE),
            "file_size": BLOCK_FILE.stat().st_size,
            "file_mtime": datetime.fromtimestamp(BLOCK_FILE.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(rows),
        },
        "data_cache": {"source": "runtime_stock_cache", "exists": CACHE.exists(), "status": cache.get("status"), "generated_at": cache.get("generated_at"), "trade_date": cache.get("trade_date")},
        "trade_date": current_trade_date,
        "formula_evidence": historical_formula_evidence,
        "short_term_score": {
            "status": score_handoff.get("status"),
            "version": score_handoff.get("version"),
            "global_contract_path": score_handoff.get("global_contract_path"),
            "global_contract_sha256": score_handoff.get("global_contract_sha256"),
            "owner_skill_id": "a-share-15d-selection",
            "reuse_mode": "authoritative_score_reuse_with_mainline_enrichment",
            "trade_date": score_handoff.get("trade_date"),
            "candidate_pool": score_handoff.get("candidate_pool", {}),
            "artifact": score_handoff.get("artifact"),
            "artifact_sha256": score_handoff.get("artifact_sha256"),
            "error": score_handoff.get("error"),
            "verified_count": outcome["score_verified_count"],
            "hard_excluded_count": outcome["score_excluded_count"],
            "data_required_count": outcome["score_data_required_count"],
            "fundamental_positive_weight": 0,
        },
        "mainline_market": {
            "model_version": mainline_context.get("model_version"),
            "status": mainline_context.get("status"),
            "source_status": mainline_context.get("source_status", {}),
            "source_paths": mainline_context.get("source_paths", {}),
            "issues": mainline_context.get("issues", []),
            "board_count": len(mainline_context.get("boards", {})),
            "stock_count": len(mainline_context.get("stocks", {})),
            "verified_stock_count": mainline_verified_count,
            "authenticity_verified_stock_count": outcome["authenticity_verified_count"],
            "gate_failed_stock_count": outcome["gate_failed_count"],
            "degraded_stock_count": outcome["degraded_count"],
            "data_required_reasons": outcome["data_required_reasons"],
            "missing_evidence_policy": "zero_without_renormalization",
        },
        "scan_count": len(analyses),
        "five_formula_success_count": sum(1 for x in analyses if x["five_formula_ok"]),
        "required_formula_success_count": sum(1 for x in analyses if all(x.get("required_formulas_ok", {}).values())),
        "reserved_formula_failed_count": sum(1 for x in analyses if x.get("reserved_failed_formulas")),
        "top10_count": len(top10),
        "top3_count": len(top3),
        "flow_kept_unchanged": ["四必需公式+庄家资金监控保留项扫描", "7条V6.1硬剔除", "15项V6.1风险扣分", "26因子四轴评分", "Top10信号表", "Top3深度分析", "明日观察计划"],
        "top10": top10,
        "top3": [{"symbol": x["symbol"], "name": x["name"], "score": x["final_score"], "grade": x["grade"], "plan": x["next_session_plan"]} for x in top3],
        "wave_distribution_top10": wave_distribution,
        "all_results": analyses,
        "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
    }
    out = REPORT / "feilong_block_resonance_scan.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {k: result[k] for k in ["status", "decision_status", "generated_at", "scan_count", "five_formula_success_count", "top10_count", "top3_count", "elapsed_ms"]}
    summary["mainline_verified_stock_count"] = mainline_verified_count
    summary["mainline_status"] = mainline_context.get("status")
    summary["output"] = str(out)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
