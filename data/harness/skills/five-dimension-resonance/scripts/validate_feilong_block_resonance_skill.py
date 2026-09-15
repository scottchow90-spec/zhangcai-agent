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
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "five-dimension-resonance"
REPORT = ROOT / "reports" / "2026-06-03_five_dimension_feilong_block_hardening"
TDX_HUB = ROOT / "skills" / "tdx-local-hub" / "scripts" / "tdx_hub.py"
GLOBAL_SCORE_CONTRACT = ROOT / "skills" / "stock-unified" / "references" / "short_term_strong_stock_scoring_contract.json"
GLOBAL_SCORE_CONTRACT_SHA256 = hashlib.sha256(GLOBAL_SCORE_CONTRACT.read_bytes()).hexdigest()
SCORE_CONTRACT_VERSION = "A-SHARE-STRONG-26F-100-V6.1"
BLOCK_FILE = Path(r"C:\new_tdx_mock\T0002\blocknew\FLZT.blk")
SCAN_JSON = REPORT / "feilong_block_resonance_scan.json"
CANDIDATE_JSON = REPORT / "feilong_block_candidates.json"
MAPPING_JSON = REPORT / "feilong_block_mapping_evidence.json"
OUT = REPORT / "feilong_block_resonance_validation.json"

REQUIRED_SKILL_FILES = [
    SKILL / "SKILL.md",
    SKILL / "references" / "workflow-chain.md",
    SKILL / "references" / "scoring-model.md",
    SKILL / "references" / "conflict-rules.md",
    SKILL / "scripts" / "run_feilong_block_resonance.py",
    SKILL / "scripts" / "mainline_scoring.py",
    SKILL / "scripts" / "entry_five_dimension_resonance.py",
]
REQUIRED_FORMULAS = ["大牛线4.0", "飞龙在天", "游资资金监控", "机构资金监控"]
RESERVED_FORMULAS = ["庄家资金监控"]
FORBIDDEN_TEXT = ["D:\\openclaw-data\\skills\\stock\\共振选股\\SKILL.md", "reference-only", "FALLBACK", "PARTIAL", "NO_DATA", "TODO"]


def load_fresh_formula_validator():
    adapter_path = Path(__file__).with_name("canonical_business_adapter.py")
    spec = importlib.util.spec_from_file_location(
        "five_dimension_canonical_business_adapter_for_validator",
        adapter_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot_load_formula_validator:{adapter_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_formula_evidence_report


validate_formula_evidence_report_fresh = load_fresh_formula_validator()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run(cmd: list[str], timeout: int = 180) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {"returncode": proc.returncode, "stdout": (proc.stdout or "").strip(), "stderr": (proc.stderr or "").strip()}


def parse_json_stdout(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        return {}


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def count_block_rows() -> int:
    count = 0
    for line in BLOCK_FILE.read_text(encoding="gbk", errors="replace").splitlines():
        token = line.strip()
        if token and token[-6:].isdigit():
            count += 1
    return count


def validate_current_scan(
    scan: dict[str, Any],
    block_count: int,
    formula_registry: dict[str, str],
) -> tuple[list[str], dict[str, Any]]:
    issues: list[str] = []
    checks: dict[str, Any] = {}
    all_results = scan.get("all_results", []) if isinstance(scan.get("all_results"), list) else []
    candidate_pool = scan.get("candidate_pool", {})
    symbols = [str(item.get("symbol", "")) for item in all_results]
    candidate_integrated = (
        candidate_pool.get("name") == "飞龙在天"
        and candidate_pool.get("code") == "FLZT"
        and candidate_pool.get("file") == str(BLOCK_FILE)
        and candidate_pool.get("count") == block_count
        and scan.get("scan_count") == block_count
        and len(all_results) == block_count
        and len(symbols) == len(set(symbols))
        and all(symbols)
        and all(item.get("name") and item.get("name_source") for item in all_results)
    )
    checks["candidate_resolution"] = {
        "integrated": candidate_integrated,
        "candidate_pool": candidate_pool,
        "resolved_count": len(all_results),
        "unique_symbol_count": len(set(symbols)),
        "named_count": sum(bool(item.get("name")) for item in all_results),
    }
    if not candidate_integrated:
        issues.append("integrated_candidate_resolution_not_clean")

    expected_top10 = min(10, block_count)
    expected_top3 = min(3, block_count)
    required_success_count = scan.get("required_formula_success_count", scan.get("five_formula_success_count"))
    scan_clean = (
        scan.get("status") == "CLEAN_PASS"
        and scan.get("decision_status") in {"SIGNAL_FOUND", "NO_SIGNAL"}
        and scan.get("scan_count") == block_count
        and required_success_count == block_count
        and scan.get("top10_count") == expected_top10
        and scan.get("top3_count") == expected_top3
        and len(scan.get("top10", [])) == expected_top10
        and len(scan.get("top3", [])) == expected_top3
    )
    checks["scan_shape"] = {
        "clean": scan_clean,
        "expected_top10": expected_top10,
        "expected_top3": expected_top3,
        "actual_top10": len(scan.get("top10", [])),
        "actual_top3": len(scan.get("top3", [])),
    }
    if not scan_clean:
        issues.append("scan_not_clean")

    historical_used = any(
        item.get("formula_evidence", {}).get("mode") == "historical_exact_input_reuse"
        for item in all_results
    )
    audit = scan.get("formula_evidence", {})
    independent_revalidation_errors = (
        validate_formula_evidence_report_fresh(scan)
        if historical_used
        else []
    )
    required_audit_matches = [
        audit.get("candidate_binding", {}).get("matched"),
        audit.get("trade_date_binding", {}).get("matched"),
        audit.get("kline_binding", {}).get("matched"),
        audit.get("formula_executor_binding", {}).get("matched"),
        audit.get("recovery_provenance", {}).get("matched"),
        audit.get("source_artifact", {}).get("matched"),
        audit.get("source_receipt", {}).get("matched"),
        audit.get("source_receipt_artifact_binding", {}).get("matched"),
    ]
    expected_formula_order = REQUIRED_FORMULAS + RESERVED_FORMULAS
    reuse_manifest = audit.get("reuse_evidence_manifest", {})
    reuse_manifest_hash = str(audit.get("reuse_evidence_manifest_sha256", ""))
    required_manifest_keys = {
        "schema",
        "reuse_scope",
        "source_receipt",
        "source_artifact",
        "immutable_line_locator",
        "immutable_line_sha256",
        "trade_date",
        "candidates_ordered",
        "candidates_ordered_sha256",
        "kline_inputs",
        "formula_executor_inputs",
        "formula_names_ordered",
    }
    reuse_manifest_verified = not historical_used or (
        isinstance(reuse_manifest, dict)
        and required_manifest_keys.issubset(reuse_manifest)
        and reuse_manifest.get("schema") == "FIVE_DIMENSION_REUSE_EVIDENCE_MANIFEST_V1"
        and reuse_manifest.get("reuse_scope") == "raw_scan_only"
        and reuse_manifest.get("trade_date") == scan.get("trade_date")
        and reuse_manifest.get("candidates_ordered") == symbols
        and reuse_manifest.get("formula_names_ordered") == expected_formula_order
        and canonical_json_sha256(reuse_manifest) == reuse_manifest_hash
        and reuse_manifest.get("source_receipt", {}).get("sha256") == audit.get("source_receipt", {}).get("sha256")
        and reuse_manifest.get("source_artifact", {}).get("sha256") == audit.get("source_artifact", {}).get("sha256")
        and reuse_manifest.get("immutable_line_sha256") == audit.get("recovery_provenance", {}).get("line_sha256")
    )
    formula_audit_verified = not historical_used or (
        audit.get("status") == "VERIFIED"
        and all(value is True for value in required_audit_matches)
        and reuse_manifest_verified
        and not independent_revalidation_errors
    )
    checks["formula_evidence"] = {
        "historical_used": historical_used,
        "verified": formula_audit_verified,
        "status": audit.get("status"),
        "required_matches": required_audit_matches,
        "reuse_manifest_verified": reuse_manifest_verified,
        "reuse_evidence_manifest_sha256": reuse_manifest_hash,
        "independent_revalidation_errors": independent_revalidation_errors,
    }
    if not formula_audit_verified:
        issues.append("formula_evidence_audit_incomplete")
    if historical_used and not reuse_manifest_verified:
        issues.append("formula_evidence_manifest_invalid")
    if independent_revalidation_errors:
        issues.append("formula_evidence_independent_revalidation_failed")
        issues.extend(
            f"formula_evidence_fresh:{error}"
            for error in independent_revalidation_errors
        )

    formula_rows: list[dict[str, Any]] = []
    for item in all_results:
        symbol = str(item.get("symbol", ""))
        raw_scan = item.get("raw_scan", {})
        formula_items = raw_scan.get("items", []) if isinstance(raw_scan.get("items"), list) else []
        names = [entry.get("formula") for entry in formula_items]
        mappings = {str(entry.get("formula", "")): str(entry.get("tq_formula", "")) for entry in formula_items}
        matched = (
            item.get("five_formula_ok") is True
            and raw_scan.get("ok") is True
            and raw_scan.get("symbol") == symbol
            and names == expected_formula_order
            and all(entry.get("ok") is True for entry in formula_items)
            and all(mappings.get(name) == formula_registry.get(name) for name in expected_formula_order)
        )
        formula_rows.append({"symbol": symbol, "matched": matched, "mappings": mappings})
        if not matched:
            issues.append(f"formula_mapping_or_result_invalid:{symbol}")
        if item.get("formula_evidence", {}).get("mode") == "historical_exact_input_reuse":
            evidence = item.get("formula_evidence", {})
            evidence_binding_matched = (
                evidence.get("reuse_evidence_manifest_sha256") == reuse_manifest_hash
                and evidence.get("source_receipt_sha256") == audit.get("source_receipt", {}).get("sha256")
                and evidence.get("source_artifact_sha256") == audit.get("source_artifact", {}).get("sha256")
                and evidence.get("immutable_line_sha256") == audit.get("recovery_provenance", {}).get("line_sha256")
            )
            if not evidence_binding_matched:
                issues.append(f"formula_evidence_item_binding_invalid:{symbol}")
    checks["formula_rows"] = formula_rows
    return list(dict.fromkeys(issues)), checks


def main() -> int:
    # 2026-06-22 加固: 支持 --help / --dry-run 快速响应
    import argparse
    p = argparse.ArgumentParser(description="五维共振 validate (检查 skill + 业务结果)")
    p.add_argument("--dry-run", action="store_true", help="检查脚本+数据源存在后立即退出")
    p.add_argument("--help-extended", action="store_true", help="扩展帮助")
    ns, _unknown = p.parse_known_args()

    if ns.help_extended:
        print(json.dumps({
            "skill": "five-dimension-resonance",
            "name_cn": "五维共振选股",
            "required_skill_files": [str(f.relative_to(ROOT)) for f in REQUIRED_SKILL_FILES],
            "required_formulas": REQUIRED_FORMULAS,
            "reserved_formulas": RESERVED_FORMULAS,
            "report": str(OUT),
            "scan_json": str(SCAN_JSON),
            "candidate_json": str(CANDIDATE_JSON),
            "mapping_json": str(MAPPING_JSON),
            "block_file": str(BLOCK_FILE),
        }, ensure_ascii=False, indent=2))
        return 0

    if ns.dry_run:
        out = {
            "status": "DRY_RUN_OK",
            "skill": "five-dimension-resonance",
            "block_file_exists": BLOCK_FILE.exists(),
            "block_file_size": BLOCK_FILE.stat().st_size if BLOCK_FILE.exists() else 0,
            "scan_json_exists": SCAN_JSON.exists(),
            "candidate_json_exists": CANDIDATE_JSON.exists(),
            "mapping_json_exists": MAPPING_JSON.exists(),
            "report_dir_exists": REPORT.exists(),
            "tdx_hub_exists": TDX_HUB.exists(),
            "required_skill_files": [{"path": str(f.relative_to(ROOT)), "exists": f.exists()} for f in REQUIRED_SKILL_FILES],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    checks: dict[str, Any] = {}
    issues: list[str] = []

    for path in REQUIRED_SKILL_FILES:
        exists = path.exists() and path.stat().st_size > 0
        checks[f"file::{path.name}"] = {"path": str(path), "exists": path.exists(), "size": path.stat().st_size if path.exists() else 0}
        if not exists:
            issues.append(f"missing_or_empty:{path}")

    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    workflow_text = (SKILL / "references" / "workflow-chain.md").read_text(encoding="utf-8")
    scoring_text = (SKILL / "references" / "scoring-model.md").read_text(encoding="utf-8")
    entry_text = (SKILL / "scripts" / "entry_five_dimension_resonance.py").read_text(encoding="utf-8")
    combined = "\n".join([skill_text, workflow_text, scoring_text, entry_text])
    bad_controls = sorted({f"U+{ord(ch):04X}" for ch in combined if ord(ch) < 32 and ch not in "\r\n"})
    checks["control_characters"] = bad_controls
    if bad_controls:
        issues.append("control_character_present")
    checks["skill_metadata"] = {
        "skill_id_present": "name: five-dimension-resonance" in skill_text,
        "name_cn_present": "# 五维共振选股" in skill_text,
        "status_active": "scripts/mainline_scoring.py" in skill_text,
        "candidate_pool_name_present": "飞龙在天" in combined,
        "candidate_pool_file_present": "C:\\new_tdx_mock\\T0002\\blocknew\\FLZT.blk" in combined,
        "execution_script_present": "run_feilong_block_resonance.py" in skill_text,
        "legacy_entry_delegates_runner": "run_feilong_block_resonance" in entry_text and "东方财富" not in entry_text and "五维共振参考" not in entry_text,
    }
    for key, value in checks["skill_metadata"].items():
        if not value:
            issues.append(f"skill_metadata_false:{key}")
    for token in FORBIDDEN_TEXT:
        if token in combined:
            issues.append(f"forbidden_text_present:{token}")

    block_count = count_block_rows()
    checks["block_file"] = {"path": str(BLOCK_FILE), "size": BLOCK_FILE.stat().st_size, "mtime": datetime.fromtimestamp(BLOCK_FILE.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"), "count": block_count}
    if block_count <= 0:
        issues.append("block_count_zero")

    scan = load_json(SCAN_JSON)
    registry_run = run([sys.executable, str(TDX_HUB), "registry"], timeout=30)
    registry_payload = parse_json_stdout(registry_run["stdout"])
    registry_map = {
        str(item.get("name", "")): str(item.get("call_name") or item.get("name") or "")
        for item in registry_payload.get("formulas", [])
        if isinstance(item, dict)
    }
    current_scan_issues, current_scan_checks = validate_current_scan(scan, block_count, registry_map)
    issues.extend(current_scan_issues)
    checks.update(current_scan_checks)
    checks["formula_registry"] = {
        "returncode": registry_run["returncode"],
        "ok": registry_payload.get("ok"),
        "mapping": {name: registry_map.get(name) for name in REQUIRED_FORMULAS + RESERVED_FORMULAS},
    }
    if registry_run["returncode"] != 0 or registry_payload.get("ok") is not True:
        issues.append("formula_registry_not_clean")
    all_results = scan.get("all_results", [])
    top10 = scan.get("top10", [])
    checks["scan"] = {
        "status": scan.get("status"),
        "scan_count": scan.get("scan_count"),
        "five_formula_success_count": scan.get("five_formula_success_count"),
        "required_formula_success_count": scan.get("required_formula_success_count"),
        "reserved_formula_failed_count": scan.get("reserved_formula_failed_count"),
        "top10_count": scan.get("top10_count"),
        "top3_count": scan.get("top3_count"),
        "candidate_count": scan.get("candidate_pool", {}).get("count"),
        "output_size": SCAN_JSON.stat().st_size if SCAN_JSON.exists() else 0,
    }
    codes = [item.get("symbol") for item in all_results]
    if len(codes) != len(set(codes)):
        issues.append("duplicate_symbols")
    if any(not item.get("name") for item in all_results):
        issues.append("missing_stock_names")
    if any(not item.get("five_formula_ok") for item in all_results):
        issues.append("required_formula_failure_present")
    verified_scores = [item for item in all_results if item.get("score_status") == "VERIFIED"]
    data_required_scores = [item for item in all_results if item.get("score_status") == "DATA_REQUIRED"]
    if data_required_scores:
        issues.append("authoritative_v61_score_data_required")
    if any(len(item.get("risk_items", [])) != 15 for item in verified_scores):
        issues.append("verified_risk_item_count_not_15")
    if any(len(item.get("dimension_scores", [])) != 26 for item in verified_scores):
        issues.append("verified_factor_count_not_26")
    if any(len(item.get("hard_exclusions", [])) != 7 for item in verified_scores):
        issues.append("verified_hard_exclusion_count_not_7")
    if any(
        item.get("score_contract", {}).get("version") != SCORE_CONTRACT_VERSION
        or item.get("score_contract", {}).get("global_contract_sha256") != GLOBAL_SCORE_CONTRACT_SHA256
        or item.get("score_contract", {}).get("fundamental_positive_weight") != 0
        for item in verified_scores
    ):
        issues.append("verified_score_contract_mismatch")
    if any(
        any(token in str(factor.get("name", "")) for token in ("基本面", "财务安全性", "估值", "PE", "PB"))
        for item in verified_scores
        for factor in item.get("dimension_scores", [])
        if isinstance(factor, dict)
    ):
        issues.append("fundamental_positive_factor_present")
    short_term_score = scan.get("short_term_score", {})
    checks["short_term_score"] = short_term_score
    if (
        short_term_score.get("status") != "CLEAN_PASS"
        or short_term_score.get("version") != SCORE_CONTRACT_VERSION
        or short_term_score.get("global_contract_sha256") != GLOBAL_SCORE_CONTRACT_SHA256
        or short_term_score.get("fundamental_positive_weight") != 0
        or int(short_term_score.get("verified_count", 0)) + int(short_term_score.get("hard_excluded_count", 0)) != len(all_results)
    ):
        issues.append("short_term_score_handoff_mismatch")
    mainline_market = scan.get("mainline_market", {})
    checks["mainline_scoring"] = {
        "model_version": mainline_market.get("model_version"),
        "status": mainline_market.get("status"),
        "board_count": mainline_market.get("board_count"),
        "stock_count": mainline_market.get("stock_count"),
        "verified_stock_count": mainline_market.get("verified_stock_count"),
        "per_stock_evidence_count": sum("mainline_scoring" in item for item in all_results),
    }
    runner_text = (SKILL / "scripts" / "run_feilong_block_resonance.py").read_text(encoding="utf-8")
    if "sector_star = 4.0 if pct >= 9.5 else 3.0" in runner_text:
        issues.append("forbidden_stock_gain_mainline_proxy_present")
    if mainline_market.get("model_version") != "CORE-MAINLINE-100-V2":
        issues.append("mainline_model_binding_missing")
    if any("mainline_scoring" not in item for item in all_results):
        issues.append("per_stock_mainline_evidence_missing")
    if any(
        item.get("mainline_scoring", {}).get("status") == "DEGRADED"
        and item.get("mainline_scoring", {}).get("weighted_score", 0) != 0
        for item in all_results
    ):
        issues.append("degraded_mainline_awarded_points")
    flow = scan.get("flow_kept_unchanged", [])
    formula_flow_ok = "五公式扫描" in flow or "四必需公式+庄家资金监控保留项扫描" in flow
    if not formula_flow_ok or not all(step in flow for step in ["7条V6.1硬剔除", "15项V6.1风险扣分", "26因子四轴评分", "Top10信号表", "Top3深度分析", "明日观察计划"]):
        issues.append("flow_unchanged_evidence_missing")

    compile_run = run([sys.executable, "-m", "py_compile", str(TDX_HUB), str(SKILL / "scripts" / "mainline_scoring.py"), str(SKILL / "scripts" / "run_feilong_block_resonance.py"), str(SKILL / "scripts" / "entry_five_dimension_resonance.py")], timeout=120)
    checks["py_compile"] = {"returncode": compile_run["returncode"], "stdout": compile_run["stdout"], "stderr": compile_run["stderr"]}
    if compile_run["returncode"] != 0 or compile_run["stderr"]:
        issues.append("py_compile_not_clean")

    result = {
        "status": "CLEAN_PASS" if not issues else "NEEDS_REPAIR",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "skill": "five-dimension-resonance",
        "name_cn_source": str(SKILL / "SKILL.md"),
        "candidate_pool": {"name": "飞龙在天", "file": str(BLOCK_FILE), "count": block_count},
        "checks": checks,
        "issues": issues,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(OUT), "issues": issues, "scan_count": checks.get("scan", {}).get("scan_count"), "five_formula_success_count": checks.get("scan", {}).get("five_formula_success_count")}, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
