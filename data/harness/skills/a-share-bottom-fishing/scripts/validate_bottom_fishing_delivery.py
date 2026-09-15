#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate bottom-fishing v2 strict delivery artifacts.

This script is intentionally lightweight: it verifies the presence and key
boolean gates of the standard v2 strict task directory. It does not replace
project-level stock_selection_final_gate.py when that hook is available.
"""

from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

REQUIRED_TRUE_CHECKS = [
    "uses_three_year_kline",
    "five_formula_subsystems_read",
    "no_bj",
    "no_kcb",
    "no_st_delist",
    "no_bank",
    "no_missing_or_pending_names",
    "all_realtime_wave_segment_lt20",
    "scoring_complete",
    "global_unique_codes",
    "top3_per_group",
    "nonzero_candidates",
    "nonzero_final",
    "no_scan_errors",
    "public_quote_validation_read",
    "public_names_no_missing",
    "final_public_name_consistency",
]

REQUIRED_RELATIVE_PATHS = [
    "validation/acceptance_v2_public_validated.json",
    "strict_overlay_v2_public_validated.md",
    "output/selection_process_and_result_v2_public_validated.md",
    "output/public_quote_validation_v2.json",
    "output/candidate_evidence_v3.json",
    "audit/scan_errors_v2.json",
    "audit/duplicate_suppressed_v2.json",
    "audit/exclusions_v2.json",
    "audit/realtime_failed_v2.json",
]

ANY_OF_PATH_GROUPS = [
    ["output/final_picks_v2_public_validated.csv", "output/final_picks_v2.csv"],
    ["output/final_picks_v2_public_validated.json", "output/final_picks_v2.json"],
]


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(f"FAILED: cannot read JSON {path}: {exc}") from exc


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_name(value: object, symbol: str) -> bool:
    name = str(value or "").strip()
    code = symbol.split(".", 1)[0]
    return bool(name) and name != code and name != symbol and not any(
        token in name for token in ("待查", "待确认", "缺失")
    )


def validate_task(task_dir: Path) -> list[str]:
    task_dir = task_dir.resolve()
    failures: list[str] = []
    if not task_dir.exists():
        return [f"task_dir missing: {task_dir}"]

    for rel in REQUIRED_RELATIVE_PATHS:
        if not (task_dir / rel).exists():
            failures.append(f"missing required artifact: {rel}")
    for group in ANY_OF_PATH_GROUPS:
        if not any((task_dir / rel).exists() for rel in group):
            failures.append(f"missing one of artifacts: {group}")

    def read(rel: str, default):
        path = task_dir / rel
        if not path.is_file():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"invalid_json:{rel}:{type(exc).__name__}:{exc}")
            return default

    final_rows = read("output/final_picks_v2_public_validated.json", [])
    evaluations = read("output/candidate_evidence_v3.json", [])
    quotes = read("output/public_quote_validation_v2.json", {})
    acceptance = read("validation/acceptance_v2_public_validated.json", {})
    scan_errors = read("audit/scan_errors_v2.json", ["unreadable"])
    if not isinstance(final_rows, list):
        failures.append("final_rows_not_list")
        final_rows = []
    if not isinstance(evaluations, list):
        failures.append("candidate_evidence_not_list")
        evaluations = []
    if not isinstance(scan_errors, list):
        failures.append("scan_errors_not_list")
        scan_errors = ["invalid"]

    evaluation_symbols = [str(row.get("symbol") or "") for row in evaluations if isinstance(row, dict)]
    final_symbols = [str(row.get("symbol") or "") for row in final_rows if isinstance(row, dict)]
    for symbols, label in ((evaluation_symbols, "candidate"), (final_symbols, "final")):
        seen: set[str] = set()
        for symbol in symbols:
            if symbol in seen:
                failures.append(f"duplicate_symbol:{label}:{symbol}")
            seen.add(symbol)

    quote_rows = quotes.get("quotes", []) if isinstance(quotes, dict) else []
    quote_by_symbol = {
        str(row.get("symbol")): row
        for row in quote_rows
        if isinstance(row, dict)
    }
    formula_names = {
        "大牛线4.0", "飞龙在天", "游资资金监控", "机构资金监控", "庄家资金监控"
    }
    evaluation_by_symbol: dict[str, dict] = {}
    for row in evaluations:
        if not isinstance(row, dict):
            failures.append("candidate_row_not_object")
            continue
        symbol = str(row.get("symbol") or "")
        evaluation_by_symbol[symbol] = row
        if not _valid_name(row.get("name"), symbol):
            failures.append(f"missing_name:{symbol}")
        if row.get("selection_status") not in {"SIGNAL", "NO_SIGNAL"}:
            failures.append(f"invalid_selection_status:{symbol}:{row.get('selection_status')}")
        quote = quote_by_symbol.get(symbol)
        if not isinstance(quote, dict) or not _valid_name(quote.get("name"), symbol):
            failures.append(f"public_name_missing:{symbol}")
        elif quote.get("name") != row.get("name") or row.get("public_name") != row.get("name"):
            failures.append(f"public_name_mismatch:{symbol}")
        formulas = row.get("formula_evidence")
        formula_map = {
            str(item.get("formula")): item
            for item in formulas if isinstance(item, dict)
        } if isinstance(formulas, list) else {}
        if set(formula_map) != formula_names or any(item.get("ok") is not True for item in formula_map.values()):
            failures.append(f"five_formula_incomplete:{symbol}")
        kline = row.get("kline_evidence")
        if not isinstance(kline, dict) or int(kline.get("three_year_record_count") or 0) < 500:
            failures.append(f"three_year_kline_incomplete:{symbol}")
        elif not (path := Path(str(kline.get("path") or ""))).is_file():
            failures.append(f"kline_source_missing:{symbol}")
        elif str(kline.get("sha256") or "") != _sha256(path):
            failures.append(f"kline_source_hash_mismatch:{symbol}")
        breakdown = row.get("score_breakdown")
        if not isinstance(breakdown, dict):
            failures.append(f"score_breakdown_missing:{symbol}")
        else:
            try:
                if abs(float(row.get("score")) - sum(float(value) for value in breakdown.values())) > 1e-6:
                    failures.append(f"score_breakdown_mismatch:{symbol}")
            except (TypeError, ValueError):
                failures.append(f"score_not_numeric:{symbol}")

    for row in final_rows:
        if not isinstance(row, dict):
            failures.append("final_row_not_object")
            continue
        symbol = str(row.get("symbol") or "")
        evidence = evaluation_by_symbol.get(symbol)
        if evidence is None or evidence.get("selection_status") != "SIGNAL":
            failures.append(f"final_not_bound_to_signal:{symbol}")
        try:
            if float(row.get("wave")) >= 20 or float(row.get("segment")) >= 20:
                failures.append(f"final_not_low_wave_segment:{symbol}")
        except (TypeError, ValueError):
            failures.append(f"final_wave_segment_missing:{symbol}")
        risk = row.get("risk_checks")
        if not isinstance(risk, dict) or not all(risk.get(key) is True for key in ("no_bj", "no_kcb", "no_st_delist", "no_bank")):
            failures.append(f"final_risk_check_failed:{symbol}")

    csv_path = task_dir / "output" / "final_picks_v2_public_validated.csv"
    if csv_path.is_file():
        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))
            if [row.get("symbol") for row in csv_rows] != final_symbols:
                failures.append("final_csv_json_symbol_mismatch")
            if [row.get("name") for row in csv_rows] != [str(row.get("name") or "") for row in final_rows]:
                failures.append("final_csv_json_name_mismatch")
        except Exception as exc:
            failures.append(f"final_csv_invalid:{type(exc).__name__}:{exc}")

    checks = acceptance.get("checks", {}) if isinstance(acceptance, dict) else {}
    final_risks = [row.get("risk_checks", {}) for row in final_rows if isinstance(row, dict)]
    computed = {
        "uses_three_year_kline": bool(evaluations) and not any(item.startswith("three_year_kline") or item.startswith("kline_source") for item in failures),
        "five_formula_subsystems_read": bool(evaluations) and not any(item.startswith("five_formula_incomplete") for item in failures),
        "no_bj": all(risk.get("no_bj") is True for risk in final_risks),
        "no_kcb": all(risk.get("no_kcb") is True for risk in final_risks),
        "no_st_delist": all(risk.get("no_st_delist") is True for risk in final_risks),
        "no_bank": all(risk.get("no_bank") is True for risk in final_risks),
        "no_missing_or_pending_names": bool(evaluations) and not any(item.startswith("missing_name") for item in failures),
        "all_realtime_wave_segment_lt20": not any(item.startswith("final_not_low_wave_segment") or item.startswith("final_wave_segment") for item in failures),
        "scoring_complete": bool(evaluations) and not any(item.startswith("score_") for item in failures),
        "global_unique_codes": len(evaluation_symbols) == len(set(evaluation_symbols)) and len(final_symbols) == len(set(final_symbols)),
        "top3_per_group": len(final_rows) <= 3,
        "nonzero_candidates": bool(evaluations),
        "nonzero_final": bool(final_rows),
        "no_scan_errors": not scan_errors,
        "public_quote_validation_read": isinstance(quotes, dict) and quotes.get("status") == "CLEAN_PASS",
        "public_names_no_missing": bool(evaluations) and not any(item.startswith("public_name_missing") for item in failures),
        "final_public_name_consistency": bool(evaluations) and not any(item.startswith("public_name_mismatch") for item in failures),
    }
    selection_status = acceptance.get("selection_status") if isinstance(acceptance, dict) else None
    legal_empty = selection_status == "NO_SIGNAL" and not final_rows
    for key in REQUIRED_TRUE_CHECKS:
        actual = computed.get(key)
        if checks.get(key) is not actual:
            failures.append(f"acceptance_check_not_recomputed:{key}:declared={checks.get(key)!r}:actual={actual!r}")
        if actual is not True and not (key == "nonzero_final" and legal_empty):
            failures.append(f"check_not_true:{key}={actual!r}")
    if acceptance.get("status") != "CLEAN_PASS":
        failures.append(f"acceptance_status_not_clean:{acceptance.get('status')!r}")
    meta = acceptance.get("meta", {}) if isinstance(acceptance, dict) else {}
    if int(meta.get("candidate_count") or -1) != len(evaluations):
        failures.append("candidate_count_mismatch")
    if int(meta.get("final_count") if meta.get("final_count") is not None else -1) != len(final_rows):
        failures.append("final_count_mismatch")
    if int(meta.get("scan_error_count") if meta.get("scan_error_count") is not None else -1) != len(scan_errors):
        failures.append("scan_error_count_mismatch")
    if selection_status not in {"SIGNAL", "NO_SIGNAL"}:
        failures.append(f"invalid_overall_selection_status:{selection_status}")
    elif (selection_status == "SIGNAL") != bool(final_rows):
        failures.append("selection_status_final_count_mismatch")
    return failures


def _latest_v2_task_dir() -> str:
    """2026-06-30 加固: 自动找 reports/ 下最新的 v2 task 目录 (含 final_picks_v2.json)."""
    reports = Path('C:/Users/Administrator/.openclaw/workspace/reports')
    if not reports.exists():
        return ''
    candidates = []
    for sub in reports.iterdir():
        if not sub.is_dir():
            continue
        for pick in ('final_picks_v2.json', 'final_picks_v2_public_validated.json'):
            if (sub / 'output' / pick).exists():
                candidates.append((sub.stat().st_mtime, str(sub)))
                break
    if not candidates:
        return ''
    candidates.sort(reverse=True)
    return candidates[0][1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", default=None, help="v2 strict report task directory (default: latest v2 in reports/)")
    args = parser.parse_args()
    if args.task_dir is None:
        # 2026-06-30 加固: 默认用 reports/ 下最新的 task 目录中含 final_picks_v2.json 的那个
        args.task_dir = _latest_v2_task_dir()
    task_dir = Path(args.task_dir).resolve()
    failures = validate_task(task_dir)

    status = "CLEAN_PASS" if not failures else "BLOCKED"
    print(json.dumps({"status": status, "task_dir": str(task_dir), "failures": failures}, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
