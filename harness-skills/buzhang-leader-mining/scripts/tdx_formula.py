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
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from dynamic_hotspot_rank import run as run_dynamic_hotspot_rank
from sync_roles_from_rank import run as run_sync_roles_from_rank

_app_scripts_dir = str(_OneStockEmbeddedPath(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_tdx_root

SKILL_DIR = Path(__file__).resolve().parents[1]
SORT_SOURCE = SKILL_DIR / "references" / "tdx_sort_formula.txt"
TDX_ROOT = resolve_tdx_root()
GS_BAK = TDX_ROOT / "T0002" / "gs_bak"
BLOCKNEW = TDX_ROOT / "T0002" / "blocknew"
INFOHARBOR_BLOCK = TDX_ROOT / "T0002" / "hq_cache" / "infoharbor_block.dat"
TQCENTER = TDX_ROOT / "PYPlugins" / "user" / "tqcenter.py"
SORT_NAME = "补涨龙头排序.txt"

LEVEL2_FORMULA_NAMES = ("BZSTL2", "BZSECL2", "补涨龙头排序")
LEVEL2_RESULT_NAME = "level2_package_acceptance.json"
CANONICAL_SCORE_ASSIGNMENTS = (
    "RISK0", "EXCL0", "BARS0", "RET1", "RET5", "AMTR0", "CLV0",
    "MOMR0", "MAPR0", "LADR0", "CAPR0", "HH20", "LL20", "POSR0",
    "VRNG0", "RISKR0", "MOMN0", "MAPN0", "LADN0", "CAPN0", "POSN0",
    "RISKN0", "STOCK0", "CORE0",
)

REQUIRED_SORT_OUTPUTS = {
    "热点闸门",
    "热点强度",
    "补涨总分",
    "龙位编码",
    "龙1候选",
    "龙2候选",
    "龙3候选",
    "热点板块码",
    "排序键",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_binding(path: Path) -> dict:
    return {
        "path": str(path.resolve()),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
    }


def read_json_object(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def normalize_formula_expression(value: str) -> str:
    return re.sub(r"\s+", "", value).upper()


def assignment(text: str, name: str) -> str | None:
    match = re.search(rf"(?mi)^\s*{re.escape(name)}\s*:=\s*(.+?)\s*;\s*$", text)
    return normalize_formula_expression(match.group(1)) if match else None


def recursive_rows(value, key: str):
    if isinstance(value, dict):
        if key in value:
            yield value[key]
        for child in value.values():
            yield from recursive_rows(child, key)
    elif isinstance(value, list):
        for child in value:
            yield from recursive_rows(child, key)


def native_readback_check(path: Path | None, expected_source_hashes: dict[str, str], package: Path | None) -> dict:
    if path is None:
        return {"status": "NOT_VERIFIED", "reason": "native readback not supplied"}
    try:
        payload = read_json_object(path)
    except Exception as exc:
        return {"status": "FAIL", "path": str(path), "reason": f"{type(exc).__name__}:{exc}"}
    errors: list[str] = []
    if payload.get("fixture_only") is True or str(payload.get("schema", "")).upper().startswith("TEST-"):
        errors.append("test_fixture_forbidden")
    if str(payload.get("status", "")).upper() != "PASS":
        errors.append("native_status_not_pass")

    # The central stock-delivery TN6 validator performs an original-TCalc,
    # two-process import/save/reopen readback.  Its persisted rows expose the
    # materialized source through CompileGSIndex(mode=1), which is the correct
    # plaintext contract for protected TN6 records.  Accept that fail-closed
    # report directly instead of requiring the older task-local adapter shape.
    central_rows = payload.get("formulas")
    if isinstance(central_rows, list) and "package_sha256" in payload:
        rows = {row.get("name"): row for row in central_rows if isinstance(row, dict) and row.get("name")}
        if payload.get("formula_count") != 3 or set(rows) != set(LEVEL2_FORMULA_NAMES) or len(central_rows) != 3:
            errors.append("native_formula_name_set_not_exact")
        else:
            for name in LEVEL2_FORMULA_NAMES:
                row = rows[name]
                if row.get("type") != 0:
                    errors.append(f"native_formula_type_not_zero:{name}")
                if row.get("source_read_contract") != "CompileGSIndex(mode=1)" or row.get("source_read_result") != 1:
                    errors.append(f"native_materialized_source_readback_missing:{name}")
                source_text = row.get("source_text")
                if not isinstance(source_text, str):
                    errors.append(f"native_source_text_missing:{name}")
                elif hashlib.sha256(source_text.encode("gbk")).hexdigest() != expected_source_hashes.get(name):
                    errors.append(f"native_source_hash_mismatch:{name}")
        package_binding = None
        if package is None or not package.is_file():
            errors.append("package_missing")
        else:
            package_binding = file_binding(package)
            if payload.get("package_sha256") != package_binding["sha256"]:
                errors.append("native_package_binding_mismatch")
        return {
            "status": "PASS" if not errors else "FAIL",
            "input": file_binding(path),
            "package_binding": package_binding,
            "readback_contract": "original-tcalc-two-process-mode1",
            "errors": errors,
        }

    verification = payload.get("original_dll_verification")
    matches = verification.get("matches", {}) if isinstance(verification, dict) else {}
    if set(matches) != set(LEVEL2_FORMULA_NAMES):
        errors.append("native_formula_name_set_not_exact")
    elif any(not isinstance(matches[name], list) or len(matches[name]) != 1 for name in LEVEL2_FORMULA_NAMES):
        errors.append("native_formula_occurrence_not_one_each")
    if isinstance(verification, dict):
        if verification.get("actual_kind_deltas", {}).get("0") != 3:
            errors.append("native_kind0_delta_not_three")
        if verification.get("kind_deltas_exact") is not True:
            errors.append("native_kind_deltas_not_exact")
    else:
        errors.append("original_dll_verification_missing")
    compile_rows = payload.get("compile", [])
    compile_by_name = {row.get("name"): row for row in compile_rows if isinstance(row, dict)}
    if set(compile_by_name) != set(LEVEL2_FORMULA_NAMES):
        errors.append("native_compile_name_set_not_exact")
    else:
        for name in LEVEL2_FORMULA_NAMES:
            row = compile_by_name[name]
            if row.get("valid_source_exact") is not True or row.get("restored_source_exact") is not True:
                errors.append(f"native_source_readback_not_exact:{name}")
            if row.get("invalid_rejected") is not True or row.get("invalid_error_reported") is not True:
                errors.append(f"native_negative_compile_not_rejected:{name}")
            source_hash = str(row.get("source_sha256") or "")
            if source_hash != expected_source_hashes.get(name):
                errors.append(f"native_source_hash_mismatch:{name}")
    native_package = payload.get("package") if isinstance(payload.get("package"), dict) else {}
    if package is not None:
        if not package.is_file():
            errors.append("package_missing")
        else:
            current = file_binding(package)
            if native_package.get("sha256") != current["sha256"] or native_package.get("size_bytes") != current["size_bytes"]:
                errors.append("native_package_binding_mismatch")
    return {
        "status": "PASS" if not errors else "FAIL",
        "input": file_binding(path),
        "package_binding": native_package or None,
        "errors": errors,
    }


def _as_number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def runtime_readback_check(path: Path | None) -> dict:
    if path is None:
        return {"status": "NOT_VERIFIED", "reason": "runtime readback not supplied"}
    try:
        payload = read_json_object(path)
    except Exception as exc:
        return {"status": "FAIL", "path": str(path), "reason": f"{type(exc).__name__}:{exc}"}
    errors: list[str] = []
    if payload.get("fixture_only") is True or str(payload.get("schema", "")).upper().startswith("TEST-"):
        errors.append("test_fixture_forbidden")
    if str(payload.get("status", "")).upper() != "PASS":
        errors.append("runtime_status_not_pass")
    trade_date = str(payload.get("trade_date") or payload.get("latest_trading_date") or "").strip()
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", trade_date):
        errors.append("runtime_trade_date_missing_or_invalid")
    encoded = json.dumps(payload, ensure_ascii=False)
    missing_names = [name for name in LEVEL2_FORMULA_NAMES if name not in encoded]
    if missing_names:
        errors.append("runtime_formula_names_missing:" + ",".join(missing_names))
    hotspot_values = [_as_number(value) for value in recursive_rows(payload, "热点板块码")]
    sort_values = [_as_number(value) for value in recursive_rows(payload, "排序键")]
    role_values = [_as_number(value) for value in recursive_rows(payload, "龙位编码")]
    summary_hot = [_as_number(value) for value in recursive_rows(payload, "nonzero_hotspot_count")]
    summary_sort = [_as_number(value) for value in recursive_rows(payload, "nonzero_sort_count")]
    nonzero_hot = any(value is not None and value in (1, 2, 3) for value in hotspot_values) or any(value is not None and value > 0 for value in summary_hot)
    nonzero_sort = any(value is not None and value > 0 for value in sort_values) or any(value is not None and value > 0 for value in summary_sort)
    valid_roles = all(value is None or value in (0, 1, 2, 3) for value in role_values)
    if not nonzero_hot:
        errors.append("runtime_nonzero_hotspot_not_proved")
    if not nonzero_sort:
        errors.append("runtime_nonzero_sort_not_proved")
    if not valid_roles:
        errors.append("runtime_role_out_of_range")
    return {
        "status": "PASS" if not errors else "FAIL",
        "input": file_binding(path),
        "trade_date": trade_date or None,
        "formula_names_present": not missing_names,
        "nonzero_hotspot_proved": nonzero_hot,
        "nonzero_sort_proved": nonzero_sort,
        "role_range_valid": valid_roles,
        "errors": errors,
    }


def data_evidence_check(path: Path | None) -> dict:
    """Validate current-trade-date evidence without treating it as live formula runtime."""
    if path is None:
        return {"status": "NOT_VERIFIED", "reason": "data evidence not supplied"}
    try:
        payload = read_json_object(path)
    except Exception as exc:
        return {"status": "FAIL", "path": str(path), "reason": f"{type(exc).__name__}:{exc}"}
    errors: list[str] = []
    trade_date = str(payload.get("trade_date") or "").strip()
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", trade_date):
        errors.append("data_evidence_trade_date_missing_or_invalid")
    if str(payload.get("business_result_status") or "").upper() != "PASS":
        errors.append("data_evidence_business_result_not_pass")
    sources = payload.get("sources")
    provider_groups = {
        str(row.get("provider_group") or "")
        for row in sources
        if isinstance(row, dict) and row.get("provider_group")
    } if isinstance(sources, list) else set()
    if len(provider_groups) < 2:
        errors.append("data_evidence_independent_sources_lt_two")
    return {
        "status": "PASS" if not errors else "FAIL",
        "input": file_binding(path),
        "trade_date": trade_date or None,
        "independent_source_groups": sorted(provider_groups),
        "errors": errors,
    }


def level2_package(
    manifest_path: Path,
    out_dir: Path,
    canonical_path: Path | None,
    native_readback: Path | None,
    runtime_readback: Path | None,
    package: Path | None,
    data_evidence: Path | None,
) -> dict:
    """Read-only acceptance for the Level2, no-custom-block three-formula TN6."""
    errors: list[str] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        manifest = read_json_object(manifest_path)
    except Exception as exc:
        payload = {"status": "BLOCKED", "mode": "level2-package", "errors": [f"manifest:{type(exc).__name__}:{exc}"]}
        (out_dir / LEVEL2_RESULT_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return payload
    canonical = canonical_path or Path(str(manifest.get("canonical_source", {}).get("path", "")))
    if not canonical.is_file():
        errors.append("canonical_source_missing")
        canonical_text = ""
    else:
        canonical_text = canonical.read_text(encoding="utf-8-sig")
        expected = manifest.get("canonical_source", {})
        if expected.get("sha256") != sha256(canonical) or expected.get("size_bytes") != canonical.stat().st_size:
            errors.append("canonical_source_binding_mismatch")
    artifacts = manifest.get("artifacts", [])
    artifact_by_name = {row.get("name"): row for row in artifacts if isinstance(row, dict)}
    if set(artifact_by_name) != set(LEVEL2_FORMULA_NAMES) or len(artifacts) != 3:
        errors.append("formula_set_not_exactly_three")
    sources: dict[str, str] = {}
    source_hashes: dict[str, str] = {}
    for name in LEVEL2_FORMULA_NAMES:
        row = artifact_by_name.get(name, {})
        source_path = Path(str(row.get("path", "")))
        if not source_path.is_file():
            errors.append(f"source_missing:{name}")
            continue
        if row.get("sha256") != sha256(source_path) or row.get("size_bytes") != source_path.stat().st_size:
            errors.append(f"source_binding_mismatch:{name}")
        text = source_path.read_text(encoding="utf-8-sig")
        sources[name] = text
        source_hashes[name] = hashlib.sha256(text.encode("gbk")).hexdigest()
        if "INBLOCK" in text.upper():
            errors.append(f"custom_block_dependency:{name}")
    score_differences = []
    stock_source = sources.get("BZSTL2", "")
    main_source = sources.get("补涨龙头排序", "")
    for name in CANONICAL_SCORE_ASSIGNMENTS:
        expected = assignment(canonical_text, name)
        for target_name, target_text in (("BZSTL2", stock_source), ("补涨龙头排序", main_source)):
            observed = assignment(target_text, name)
            if expected is None or observed != expected:
                score_differences.append(f"{target_name}:{name}")
    risk_adjustment = "CORE0*RISKN0/100"
    if risk_adjustment not in normalize_formula_expression(canonical_text):
        errors.append("canonical_risk_adjustment_missing")
    if risk_adjustment not in normalize_formula_expression(stock_source) or risk_adjustment not in normalize_formula_expression(main_source):
        errors.append("level2_risk_adjustment_changed")
    if score_differences:
        errors.append("score_assignments_changed:" + ",".join(score_differences))
    manifest_invariants = manifest.get("score_invariants", {})
    if manifest.get("status") != "PASS" or manifest.get("formula_count", 3) != 3:
        errors.append("manifest_status_or_count_invalid")
    if manifest_invariants.get("core_expression_preserved") is not True or manifest_invariants.get("risk_adjusted_sort_preserved") is not True:
        errors.append("manifest_score_invariants_not_pass")
    if manifest_invariants.get("custom_block_dependency_count") != 0:
        errors.append("manifest_custom_block_dependency_nonzero")
    native_check = native_readback_check(native_readback, source_hashes, package)
    runtime_check = runtime_readback_check(runtime_readback)
    data_check = data_evidence_check(data_evidence)
    if native_check["status"] == "FAIL":
        errors.append("native_readback_failed")
    if runtime_check["status"] == "FAIL":
        errors.append("runtime_readback_failed")
    if data_check["status"] == "FAIL":
        errors.append("data_evidence_failed")
    verification_missing = [name for name, check in (("native", native_check), ("runtime", runtime_check)) if check["status"] == "NOT_VERIFIED"]
    status = "BLOCKED" if errors else "OBSERVE" if verification_missing else "PASS"
    payload = {
        "schema": "BUZHANG-LEVEL2-PACKAGE-ACCEPTANCE-V1",
        "status": status,
        "mode": "level2-package",
        "target": "Tongdaxin Level2 sorting indicator without custom blocks",
        "latest_trading_date": runtime_check.get("trade_date") or data_check.get("trade_date"),
        "formula_names": list(LEVEL2_FORMULA_NAMES),
        "formula_count": len(artifact_by_name),
        "manifest": file_binding(manifest_path),
        "canonical_source": file_binding(canonical) if canonical.is_file() else None,
        "package": file_binding(package) if package is not None and package.is_file() else None,
        "checks": {
            "exactly_three_formulas": set(artifact_by_name) == set(LEVEL2_FORMULA_NAMES) and len(artifacts) == 3,
            "custom_block_dependency_count": sum(text.upper().count("INBLOCK") for text in sources.values()),
            "canonical_score_assignments_preserved": not score_differences,
            "canonical_risk_adjusted_sort_preserved": "level2_risk_adjustment_changed" not in errors,
            "native_readback": native_check,
            "runtime_readback": runtime_check,
            "data_evidence": data_check,
            "persisted_result_readback": True,
        },
        "verification_missing": verification_missing,
        "errors": errors,
    }
    result_path = out_dir / LEVEL2_RESULT_NAME
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    persisted = read_json_object(result_path)
    if persisted != payload:
        raise RuntimeError("persisted Level2 acceptance readback mismatch")
    return payload


def validate_formula(path: Path, required: set[str]) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    errors: list[str] = []
    if not text.strip():
        errors.append("empty_formula")
    if "{" in text or "}" in text or "//" in text:
        errors.append("unsupported_comment_syntax")
    for forbidden in ("BARSLASTCOUNT", "RANK(", "BLOCKSUM(", "BLOCKAVG(", "INSUM(", "CON2STR("):
        if forbidden in text.upper():
            errors.append(f"unsupported_token:{forbidden}")
    balance = 0
    quote = False
    for ch in text:
        if ch == "'":
            quote = not quote
        elif not quote and ch == "(":
            balance += 1
        elif not quote and ch == ")":
            balance -= 1
            if balance < 0:
                errors.append("unbalanced_parentheses")
                break
    if quote:
        errors.append("unclosed_quote")
    if balance != 0:
        errors.append("unbalanced_parentheses")
    outputs = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if not line.endswith(";"):
            errors.append(f"missing_semicolon:{line[:32]}")
        match = re.match(r"^([^:=]+):", line)
        if match:
            outputs.add(match.group(1).strip())
    missing = sorted(required - outputs)
    if missing:
        errors.append("missing_outputs:" + ",".join(missing))
    return {
        "path": str(path),
        "exists": path.is_file(),
        "sha256": sha256(path) if path.is_file() else None,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "outputs": sorted(outputs),
        "missing_outputs": missing,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def tdx_code(code: str) -> str:
    digits = "".join(ch for ch in str(code) if ch.isdigit())[-6:].zfill(6)
    prefix = "1" if digits.startswith(("5", "6", "9")) else "2" if digits.startswith(("4", "8")) else "0"
    return prefix + digits


def stock_suffix(code7: str) -> str:
    market = "SH" if code7[0] == "1" else "BJ" if code7[0] == "2" else "SZ"
    return f"{code7[1:]}.{market}"


def sync_runtime_blocks(blocks: list[tuple[str, str, list[str]]]) -> dict:
    """Refresh the running TQ/TDX custom sectors used by INBLOCK()."""
    if not TQCENTER.is_file():
        return {"status": "OBSERVE", "error": f"missing TQ center: {TQCENTER}"}
    spec = importlib.util.spec_from_file_location("buzhang_tq_runtime_sync", TQCENTER)
    if spec is None or spec.loader is None:
        return {"status": "OBSERVE", "error": "cannot load TQ center"}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    tq = module.tq
    result: dict = {"status": "PASS", "blocks": {}}
    try:
        tq.initialize(str(TQCENTER))
        current = {str(row.get("Code")): row for row in tq.get_user_sector() if isinstance(row, dict)}
        for alias, block_name, codes in blocks:
            if alias not in current:
                tq.create_sector(block_code=alias, block_name=block_name)
            tq.clear_sector(block_code=alias)
            symbols = [stock_suffix(code) for code in codes]
            for start in range(0, len(symbols), 200):
                tq.send_user_block(block_code=alias, stocks=symbols[start:start + 200], show=False)
            runtime_codes = [str(item) for item in tq.get_stock_list_in_sector(alias, block_type=1)]
            expected = set(symbols)
            observed = set(runtime_codes)
            result["blocks"][alias] = {
                "name": block_name,
                "written_count": len(codes),
                "runtime_count": len(runtime_codes),
                "runtime_match": expected == observed,
                "runtime_codes": runtime_codes,
            }
            if expected != observed:
                result["status"] = "OBSERVE"
    except Exception as exc:
        result["status"] = "OBSERVE"
        result["error"] = f"{type(exc).__name__}:{exc}"
    finally:
        try:
            tq.close()
        except Exception:
            pass
    return result


def run_registry() -> dict:
    hub = SKILL_DIR.parent / "tdx-local-hub" / "scripts" / "tdx_hub.py"
    try:
        proc = subprocess.run([sys.executable, str(hub), "registry"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
        names = {item.get("name") for item in payload.get("formulas", [])}
        return {"exit": proc.returncode, "count": payload.get("count"), "sort_registered_in_source_registry": SORT_NAME[:-4] in names}
    except Exception as exc:
        return {"exit": None, "error": str(exc)}


def build(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    sort_out = out_dir / SORT_NAME
    shutil.copyfile(SORT_SOURCE, sort_out)
    sort_check = validate_formula(sort_out, REQUIRED_SORT_OUTPUTS)
    build_date = date.today()
    payload = {
        "status": "PASS" if sort_check["status"] == "PASS" else "FAIL",
        "mode": "build",
        "formula_name": SORT_NAME.removesuffix(".txt"),
        "trade_date": build_date.strftime("%Y%m%d"),
        "latest_trading_date": build_date.isoformat(),
        "deliverable_scope": "sorting_indicator_only",
        "sort_formula": sort_check,
        "native_tn6_registered": False,
        "gui_compile_verified": False,
    }
    (out_dir / "tdx_formula_build.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def install(out_dir: Path, manual_confirm: bool) -> dict:
    if not manual_confirm:
        return {"status": "BLOCKED", "mode": "install", "reason": "missing --manual-confirm"}
    if not TDX_ROOT.is_dir() or not GS_BAK.is_dir():
        return {"status": "BLOCKED", "mode": "install", "reason": "C:\\new_tdx_mock or T0002\\gs_bak missing"}
    built = build(out_dir)
    if built["status"] != "PASS":
        return {"status": "BLOCKED", "mode": "install", "reason": "formula static validation failed", "build": built}
    installed = []
    for name in (SORT_NAME,):
        src = out_dir / name
        dst = GS_BAK / name
        if dst.exists():
            shutil.copyfile(dst, dst.with_suffix(dst.suffix + ".bak"))
        shutil.copyfile(src, dst)
        installed.append({"path": str(dst), "sha256": sha256(dst), "size_bytes": dst.stat().st_size})
    registry = run_registry()
    payload = {
        "status": "OBSERVE",
        "mode": "install",
        "installed": installed,
        "deliverable_scope": "sorting_indicator_only",
        "source_registry": registry,
        "native_tn6_registered": False,
        "gui_compile_verified": False,
        "unverified": ["通达信排序公式编辑器编译回执", "通达信排序器实际15列展示"],
    }
    (out_dir / "tdx_formula_install.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def sync_block(result_path: Path, out_dir: Path, manual_confirm: bool) -> dict:
    if not manual_confirm:
        return {"status": "BLOCKED", "mode": "sync-block", "reason": "missing --manual-confirm"}
    data = json.loads(result_path.read_text(encoding="utf-8-sig"))
    candidates = data.get("candidates", [])
    mapping = []
    for row in candidates:
        code = str(row.get("code") or "")
        if len("".join(ch for ch in code if ch.isdigit())) >= 6:
            mapping.append({"mainline": row.get("mainline"), "role": row.get("role"), "code": code, "name": row.get("name"), "score": row.get("score")})
    prefixes = ("000", "001", "002", "003", "300", "301", "600", "601", "603", "605", "688", "689", "830", "831", "832", "834", "835", "836", "837", "838", "839", "870", "871", "872", "873", "874", "875", "876", "877", "878", "879", "880", "881", "882", "883", "884", "885", "886", "887", "888", "889", "890", "891", "892", "893", "894", "895", "896", "897", "898", "899")
    concept_blocks = []
    if INFOHARBOR_BLOCK.exists():
        text = INFOHARBOR_BLOCK.read_bytes().decode("gbk", errors="ignore")
        current_name = ""
        current_codes: list[str] = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#"):
                if current_name.startswith("GN_"):
                    concept_blocks.append((current_name, current_codes))
                current_name = line[1:].split(",", 1)[0]
                current_codes = []
                continue
            for token in line.split(","):
                token = token.strip()
                if len(token) == 8 and token[0] in "0123" and token[2:].isdigit():
                    current_codes.append(token[0] + token[2:])
        if current_name.startswith("GN_"):
            concept_blocks.append((current_name, current_codes))
    all_concept_codes = sorted({code for _, rows in concept_blocks for code in rows if code[1:].startswith(prefixes)})
    mainline_names = [str(item.get("sector") or item.get("mainline") or "").strip() for item in data.get("mainlines", []) if isinstance(item, dict)]
    hot_concept_blocks = [(name, rows) for name, rows in concept_blocks if any(key and key in name for key in mainline_names)]
    hot_codes = sorted({code for _, rows in hot_concept_blocks for code in rows if code[1:].startswith(prefixes)})
    if not hot_codes:
        hot_codes = sorted({tdx_code(str(row.get("code") or "")) for row in candidates if len("".join(ch for ch in str(row.get("code") or "") if ch.isdigit())) >= 6})
    all_concept_codes = list(dict.fromkeys(all_concept_codes))
    hot_codes = list(dict.fromkeys(hot_codes))
    BLOCKNEW.mkdir(parents=True, exist_ok=True)
    block_path = BLOCKNEW / "ZLJT.blk"
    if block_path.exists():
        shutil.copyfile(block_path, block_path.with_suffix(block_path.suffix + ".bak"))
    block_path.write_bytes(("\r\n" + "\r\n".join(all_concept_codes)).encode("ascii"))
    hot_block_path = BLOCKNEW / "RDZL.blk"
    if hot_block_path.exists():
        shutil.copyfile(hot_block_path, hot_block_path.with_suffix(hot_block_path.suffix + ".bak"))
    hot_block_path.write_bytes(("\r\n" + "\r\n".join(hot_codes)).encode("ascii"))
    role_blocks = {}
    for role, alias in (("补涨龙1", "BZL1"), ("补涨龙2", "BZL2"), ("补涨龙3", "BZL3")):
        role_codes = list(dict.fromkeys(tdx_code(str(row.get("code") or "")) for row in candidates if str(row.get("role") or "") == role and len("".join(ch for ch in str(row.get("code") or "") if ch.isdigit())) >= 6))
        role_path = BLOCKNEW / f"{alias}.blk"
        if role_path.exists():
            shutil.copyfile(role_path, role_path.with_suffix(role_path.suffix + ".bak"))
        role_path.write_bytes(("\r\n" + "\r\n".join(role_codes)).encode("ascii"))
        role_blocks[role] = {"alias": alias, "path": str(role_path), "codes": role_codes, "sha256": sha256(role_path), "size_bytes": role_path.stat().st_size}
    cfg_path = BLOCKNEW / "blocknew.cfg"
    cfg_registered = []
    cfg_sha256 = None
    if cfg_path.exists():
        raw_cfg = cfg_path.read_bytes()
        for name, alias in (("主线龙头挖掘", "ZLJT"), ("热点主线龙头挖掘", "RDZL"), ("补涨龙1", "BZL1"), ("补涨龙2", "BZL2"), ("补涨龙3", "BZL3")):
            name_bytes = name.encode("gbk")
            if name_bytes not in raw_cfg and alias.encode("ascii") not in raw_cfg:
                record = bytearray(120)
                record[: len(name_bytes)] = name_bytes
                record[50:54] = alias.encode("ascii")
                raw_cfg += bytes(record)
                cfg_registered.append(name)
        if cfg_registered:
            shutil.copyfile(cfg_path, cfg_path.with_suffix(cfg_path.suffix + ".bak"))
            cfg_path.write_bytes(raw_cfg)
        cfg_sha256 = sha256(cfg_path)
    runtime_sync = sync_runtime_blocks([
        ("ZLJT", "主线龙头挖掘", all_concept_codes),
        ("RDZL", "热点主线龙头挖掘", hot_codes),
        ("BZL1", "补涨龙1", next((item["codes"] for item in role_blocks.values() if item["alias"] == "BZL1"), [])),
        ("BZL2", "补涨龙2", next((item["codes"] for item in role_blocks.values() if item["alias"] == "BZL2"), [])),
        ("BZL3", "补涨龙3", next((item["codes"] for item in role_blocks.values() if item["alias"] == "BZL3"), [])),
    ])
    out_dir.mkdir(parents=True, exist_ok=True)
    map_path = out_dir / "热点主线龙头挖掘映射.json"
    map_path.write_text(json.dumps({"trade_date": data.get("trade_date"), "concept_block_count": len(concept_blocks), "concept_union_count": len(all_concept_codes), "mainline_names": mainline_names, "matched_hot_concept_blocks": [{"name": name, "count": len(rows)} for name, rows in hot_concept_blocks], "hot_union_count": len(hot_codes), "candidates": mapping, "runtime_sync": runtime_sync}, ensure_ascii=False, indent=2), encoding="utf-8")
    static_status = bool(all_concept_codes and hot_codes)
    status = "PASS" if static_status and runtime_sync.get("status") == "PASS" else "OBSERVE" if static_status else "BLOCKED"
    return {"status": status, "mode": "sync-block", "trade_date": data.get("trade_date"), "all_concept_block": {"name": "主线龙头挖掘", "alias": "ZLJT", "path": str(block_path), "count": len(all_concept_codes), "sha256": sha256(block_path), "size_bytes": block_path.stat().st_size}, "hot_mainline_block": {"name": "热点主线龙头挖掘", "alias": "RDZL", "path": str(hot_block_path), "count": len(hot_codes), "sha256": sha256(hot_block_path), "size_bytes": hot_block_path.stat().st_size, "matched_concept_blocks": [name for name, _ in hot_concept_blocks]}, "role_blocks": role_blocks, "cfg": {"path": str(cfg_path), "registered_now": cfg_registered, "sha256": cfg_sha256}, "runtime_sync": runtime_sync, "mapping": str(map_path)}


def main() -> int:
    p = argparse.ArgumentParser(description="补涨龙头通达信公式源与自定义热点块同步")
    p.add_argument("mode", choices=("build", "install", "sync-block", "rank-block", "level2-package"))
    p.add_argument("--out", default=str(SKILL_DIR / "runs" / "tdx-formula"))
    p.add_argument("--manual-confirm", action="store_true")
    p.add_argument("--result")
    p.add_argument("--manifest")
    p.add_argument("--canonical")
    p.add_argument("--native-readback")
    p.add_argument("--runtime-readback")
    p.add_argument("--package")
    p.add_argument("--data-evidence")
    args = p.parse_args()
    out = Path(args.out)
    if args.mode == "build":
        payload = build(out)
    elif args.mode == "install":
        payload = install(out, args.manual_confirm)
    elif args.mode == "sync-block":
        if not args.result:
            payload = {"status": "BLOCKED", "mode": "sync-block", "reason": "missing --result"}
        else:
            payload = sync_block(Path(args.result), out, args.manual_confirm)
    elif args.mode == "rank-block":
        payload = run_dynamic_hotspot_rank(out, args.manual_confirm, runtime_sync=True)
        if payload.get("status") in {"PASS", "OBSERVE"}:
            try:
                role_sync = run_sync_roles_from_rank(out / "dynamic_hotspot_rank.json")
            except Exception as exc:
                role_sync = {"status": "OBSERVE", "reason": f"role sync unavailable: {type(exc).__name__}: {exc}"}
            payload["role_sync"] = role_sync
            (out / "role_sync.json").write_text(json.dumps(role_sync, ensure_ascii=False, indent=2), encoding="utf-8")
            if payload.get("status") == "PASS" and role_sync.get("status") != "PASS":
                payload["status"] = "OBSERVE"
    else:
        if not args.manifest:
            payload = {"status": "BLOCKED", "mode": "level2-package", "errors": ["missing --manifest"]}
        else:
            payload = level2_package(
                Path(args.manifest),
                out,
                Path(args.canonical) if args.canonical else None,
                Path(args.native_readback) if args.native_readback else None,
                Path(args.runtime_readback) if args.runtime_readback else None,
                Path(args.package) if args.package else None,
                Path(args.data_evidence) if args.data_evidence else None,
            )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status") in {"PASS", "OBSERVE"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
