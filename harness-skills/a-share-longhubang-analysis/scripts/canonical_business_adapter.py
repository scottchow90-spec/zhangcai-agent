#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
_stock_adapter_shared_scripts = str(_OneStockEmbeddedPath(__file__).resolve().parents[3] / "scripts")
if _stock_adapter_shared_scripts not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _stock_adapter_shared_scripts)
from stock_adapter_io import atomic_write_json, atomic_write_text, enable_atomic_path_writes

ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = ROOT.name
LEGACY_ENTRY = ROOT / "scripts" / "legacy_codex_entry.py"
FAILURE_TOKENS = ('"status": "BLOCKED"', '"status":"BLOCKED"', '"status": "FAILED"', "Traceback (most recent call last)", "TIMEOUT after ")

def sha256_file(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def record(path: Path) -> dict: return {"status": "CLEAN_PASS", "path": str(path.resolve()), "size": path.stat().st_size, "sha256": sha256_file(path), "errors": []}

def build_data_gate(analysis_path: Path, environment: dict[str, str] | None = None) -> dict:
    environment = dict(os.environ if environment is None else environment)
    evidence_set_id = str(environment.get("CODEX_STOCK_EVIDENCE_SET_ID") or "").strip()
    latest_date = str(environment.get("CODEX_STOCK_EVIDENCE_TRADING_DATE") or "").strip()
    try:
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        analysis = {}

    stocks = analysis.get("stocks") if isinstance(analysis, dict) else None
    stocks = stocks if isinstance(stocks, list) else []
    sources = analysis.get("sources") if isinstance(analysis, dict) else None
    sources = sources if isinstance(sources, dict) else {}
    effective_date = str(analysis.get("trade_date") or "") if isinstance(analysis, dict) else ""
    analysis_id = f"sha256:{sha256_file(analysis_path)}" if analysis_path.is_file() else ""

    clean_analysis = (
        analysis.get("schema") == "A_SHARE_LONGHUBANG_ANALYSIS_V1"
        and analysis.get("status") == "CLEAN_PASS"
        and analysis.get("stock_count") == len(stocks)
        and bool(stocks)
    )
    identity_ok = clean_analysis and all(str(row.get("code") or "").strip() and str(row.get("name") or "").strip() for row in stocks)
    date_ok = clean_analysis and bool(latest_date) and effective_date == latest_date
    quote_ok = clean_analysis and all(
        all(isinstance(row.get(field), (int, float)) and not isinstance(row.get(field), bool) for field in ("net_amount", "buy_amount", "sell_amount"))
        and str(row.get("reason") or "").strip()
        for row in stocks
    )
    fundamentals_ok = clean_analysis and all(
        isinstance(row.get("concept_evidence"), dict)
        and bool(row["concept_evidence"].get("main_business"))
        for row in stocks
    )
    current_event_ok = (
        clean_analysis
        and all(str(row.get("reason") or "").strip() for row in stocks)
        and sources.get("duanxianxia", {}).get("status") == "CLEAN_PASS"
        and sources.get("lianban", {}).get("status") == "CLEAN_PASS"
        and environment.get("CODEX_DUANXIANXIA_STATUS") == "CLEAN_PASS"
    )
    theme_ok = clean_analysis and all(
        str(row.get("concept") or "").strip()
        and isinstance(row.get("concept_evidence"), dict)
        and bool(row["concept_evidence"].get("precise_concepts"))
        for row in stocks
    )
    freshness_ok = (
        clean_analysis
        and bool(sources)
        and all(isinstance(source, dict) and source.get("status") == "CLEAN_PASS" for source in sources.values())
        and environment.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS") == "CLEAN_PASS"
        and bool(evidence_set_id)
        and date_ok
    )

    checks = {
        "identity": (identity_ok, [f"{analysis_id}#stocks.code,name"]),
        "effective_trading_date": (date_ok, [f"{analysis_id}#trade_date", f"{evidence_set_id}#trading_date"]),
        "quote_kline": (quote_ok, [f"{analysis_id}#stocks.net_amount,buy_amount,sell_amount,reason"]),
        "fundamentals": (fundamentals_ok, [f"{analysis_id}#stocks.concept_evidence.main_business"]),
        "news_announcements": (current_event_ok, [f"{analysis_id}#stocks.reason", f"{evidence_set_id}#duanxianxia,lianban"]),
        "sector_theme": (theme_ok, [f"{analysis_id}#stocks.concept,concept_evidence.precise_concepts"]),
        "source_freshness": (freshness_ok, [f"{analysis_id}#sources", f"{evidence_set_id}#created_at,trading_date"]),
    }
    dimensions = {
        name: {"status": "CLEAN_PASS" if passed else "BLOCKED", "evidence_ids": [item for item in evidence_ids if item and not item.startswith("#")]}
        for name, (passed, evidence_ids) in checks.items()
    }
    errors = [f"data_gate_dimension_failed:{name}" for name, (passed, _) in checks.items() if not passed]
    return {
        "schema": "STOCK_DATA_GATE_V1",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "skill_id": SKILL_ID,
        "effective_trading_date": effective_date,
        "latest_required_trading_date": latest_date,
        "evidence_set_id": evidence_set_id,
        "dimensions": dimensions,
        "errors": errors,
    }

def main() -> int:
    enable_atomic_path_writes()
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True); parser.add_argument("--timeout", type=int, default=240)
    args, business_args = parser.parse_known_args(); run_dir = Path(args.run_dir).resolve(); run_dir.mkdir(parents=True, exist_ok=True)
    business_args = list(business_args)
    if business_args and business_args[0] == "--": business_args = business_args[1:]
    if os.environ.get("CODEX_STOCK_CANONICAL_EXECUTION") != "1":
        print(json.dumps({"skill_id": SKILL_ID, "status": "BLOCKED", "errors": ["canonical_execution_environment_missing"]}, ensure_ascii=False)); return 2
    command = [sys.executable, str(LEGACY_ENTRY), "run", "--run-dir", str(run_dir), *business_args]
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "ONESTOCK_STOCK_CANONICAL_CHILD": "1"}
    try:
        child = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=args.timeout, env=environment); timed_out = False
    except subprocess.TimeoutExpired as exc:
        child = subprocess.CompletedProcess(command, 124, exc.stdout or "", (exc.stderr or "") + f"\nTIMEOUT after {args.timeout}s"); timed_out = True
    stdout_path = run_dir / "business_child.stdout.txt"; stderr_path = run_dir / "business_child.stderr.txt"
    atomic_write_text(stdout_path, str(child.stdout)); atomic_write_text(stderr_path, str(child.stderr))
    combined = str(child.stdout) + "\n" + str(child.stderr); failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    analysis = run_dir / "longhubang-analysis.json"; report = run_dir / "longhubang-analysis.md"
    errors = [label for label, path in (("analysis_missing", analysis), ("report_missing", report)) if not path.is_file()]
    data_gate = None
    if not errors and environment.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS") == "CLEAN_PASS":
        data_gate = build_data_gate(analysis, environment)
        if data_gate.get("status") != "CLEAN_PASS":
            errors.extend(data_gate.get("errors") or ["data_gate_blocked"])
    artifacts = [record(analysis), record(report)] if not errors else []
    poster_dir = run_dir / "artifacts"
    for poster in sorted(poster_dir.glob("longhubang-*.png")) if poster_dir.is_dir() else []: artifacts.append(record(poster))
    inspection = run_dir / "visual-inspection.json"
    if inspection.is_file(): artifacts.append(record(inspection))
    accepted = child.returncode == 0 and not timed_out and not failure_tokens and not errors
    manifest = {"schema": "STOCK_DELIVERY_MANIFEST_V1", "status": "CLEAN_PASS" if accepted else "BLOCKED", "skill_id": SKILL_ID, "validation": {"status": "CLEAN_PASS" if accepted else "BLOCKED", "errors": errors}, "artifacts": artifacts, "template": record(ROOT / "POSTER_TEMPLATE.md"), "validator": record(ROOT / "scripts" / "poster_validator.py"), "errors": errors}
    manifest_path = run_dir / "delivery_manifest.json"; atomic_write_json(manifest_path, manifest)
    result = {"schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1", "skill_id": SKILL_ID, "status": "CLEAN_PASS" if accepted else "BLOCKED", "business_process": {"command": command, "returncode": child.returncode, "timed_out": timed_out, "failure_tokens": failure_tokens}, "business_binding": {"path": str(LEGACY_ENTRY), "sha256": sha256_file(LEGACY_ENTRY)}, "artifacts": {"analysis": str(analysis), "report": str(report), "delivery_manifest": str(manifest_path)}, "errors": errors}
    if data_gate is not None: result["data_gate"] = data_gate
    atomic_write_json(run_dir / "business_result.json", result)
    print(json.dumps(result, ensure_ascii=False)); return 0 if accepted else 2

if __name__ == "__main__": raise SystemExit(main())
