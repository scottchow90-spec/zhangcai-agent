#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strict entrypoint for limit-up-review.

The stock universe must come from the same-day official limit-up pool. Local
custom blocks are diagnostic annotations only; they must not add stocks to the
visible report or to the final CSV.
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import hashlib
import uuid
from datetime import date as date_type, datetime, time as time_type, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

WORKSPACE = Path(r"D:\C盘转移\日志\codex")
SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
REPORT_ROOT = WORKSPACE / "reports"
BUSINESS_DATA_ROOT = WORKSPACE / "business_data" / "limit-up-review"
DEFAULT_TDX_ROOT = Path(r"C:\new_tdx_mock")
DEFAULT_DELIVERY_ROOT = Path(r"F:\小龙虾6月交付")
LATEST_CLOSE_TIME = time_type(15, 5)
STRICT_STEPS = [
    "collect_limitup_data_strict.py",
    "fetch_push2_fund_flow_strict.py",
    "generate_limit_up_review_strict.py",
]


def now_iso() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object required: {path}")
    return payload


def has_akshare(python_exe: str) -> bool:
    try:
        proc = subprocess.run(
            [python_exe, "-c", "import akshare"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=12,
        )
        return proc.returncode == 0
    except Exception:
        return False


def resolve_python() -> str:
    candidates = [
        os.environ.get("LIMITUP_PYTHON", ""),
        sys.executable,
        "python",
    ]
    for candidate in candidates:
        if candidate and has_akshare(candidate):
            return candidate
    return sys.executable


def default_date() -> str:
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")


def normalize_date(value: str) -> str:
    value = (value or default_date()).strip()
    if re.fullmatch(r"\d{8}", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    raise ValueError(f"date must be YYYY-MM-DD or YYYYMMDD, got: {value}")


def path_is_within(path: Path, root: Path) -> bool:
    candidate = os.path.normcase(str(path.resolve(strict=False)))
    boundary = os.path.normcase(str(root.resolve(strict=False)))
    try:
        return os.path.commonpath([candidate, boundary]) == boundary
    except ValueError:
        return False


def validate_historical_output(out_dir: Path | None) -> list[str]:
    if out_dir is None:
        return ["HISTORICAL_MODE_REQUIRES_EXPLICIT_OUT_DIR"]
    delivery = out_dir / "delivery"
    if path_is_within(delivery, DEFAULT_DELIVERY_ROOT):
        return [f"HISTORICAL_MODE_DEFAULT_DELIVERY_ROOT_FORBIDDEN:{delivery}"]
    return []


def load_trade_calendar_dates() -> set[date_type]:
    import akshare as ak

    frame = ak.tool_trade_date_hist_sina()
    if frame.empty or "trade_date" not in frame.columns:
        raise RuntimeError("trade calendar is empty or missing trade_date")
    dates: set[date_type] = set()
    for value in frame["trade_date"].tolist():
        text = str(value)[:10]
        dates.add(datetime.strptime(text, "%Y-%m-%d").date())
    if not dates:
        raise RuntimeError("trade calendar contains no dates")
    return dates


def evaluate_date_gate(
    requested_date: str,
    mode: str,
    *,
    now: datetime | None = None,
    calendar_dates: set[date_type] | None = None,
) -> dict[str, Any]:
    current = now or datetime.now(timezone(timedelta(hours=8)))
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone(timedelta(hours=8)))
    mode = str(mode or "latest").strip().lower()
    requested = normalize_date(requested_date) if str(requested_date or "").strip() else ""
    blocks: list[str] = []
    if mode == "historical":
        if not requested:
            blocks.append("HISTORICAL_MODE_REQUIRES_EXPLICIT_DATE")
        return {
            "status": "BLOCKED" if blocks else "CLEAN_PASS",
            "mode": mode,
            "checked_at": current.isoformat(timespec="seconds"),
            "requested_date": requested,
            "target_date": requested or current.strftime("%Y-%m-%d"),
            "blocks": blocks,
            "rule": "historical mode is isolated and never writes the default delivery root",
        }
    if mode != "latest":
        return {
            "status": "BLOCKED",
            "mode": mode,
            "checked_at": current.isoformat(timespec="seconds"),
            "requested_date": requested,
            "target_date": requested or current.strftime("%Y-%m-%d"),
            "blocks": [f"UNKNOWN_DATE_MODE:{mode}"],
        }
    try:
        calendar = calendar_dates if calendar_dates is not None else load_trade_calendar_dates()
    except Exception as exc:
        return {
            "status": "BLOCKED",
            "mode": mode,
            "checked_at": current.isoformat(timespec="seconds"),
            "requested_date": requested,
            "target_date": requested or current.strftime("%Y-%m-%d"),
            "blocks": [f"TRADE_CALENDAR_UNAVAILABLE:{type(exc).__name__}:{exc}"],
        }
    today = current.date()
    is_trading_day = today in calendar
    session_complete = not is_trading_day or current.timetz().replace(tzinfo=None) >= LATEST_CLOSE_TIME
    if is_trading_day and session_complete:
        expected = today
    else:
        prior = [day for day in calendar if day < today]
        if not prior:
            return {
                "status": "BLOCKED",
                "mode": mode,
                "checked_at": current.isoformat(timespec="seconds"),
                "requested_date": requested,
                "target_date": requested or current.strftime("%Y-%m-%d"),
                "blocks": ["NO_PRIOR_TRADING_DATE_IN_CALENDAR"],
            }
        expected = max(prior)
    expected_text = expected.isoformat()
    if requested:
        blocks.append(f"LATEST_MODE_EXPLICIT_DATE_FORBIDDEN:{requested}")
        if requested != expected_text:
            blocks.append(f"LATEST_MODE_STALE_DATE_BLOCKED:{requested}!={expected_text}")
    return {
        "status": "BLOCKED" if blocks else "CLEAN_PASS",
        "mode": mode,
        "checked_at": current.isoformat(timespec="seconds"),
        "requested_date": requested,
        "target_date": expected_text,
        "expected_latest_date": expected_text,
        "today": today.isoformat(),
        "today_is_trading_day": is_trading_day,
        "session_complete": session_complete,
        "calendar_count": len(calendar),
        "blocks": blocks,
        "rule": "LATEST_COMPLETED_TRADING_DATE: latest mode selects the most recent fully completed exchange trading day and forbids explicit dates",
    }


def load_sibling(module_name: str, file_name: str):
    path = SCRIPTS_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(str(path))
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_contract() -> dict[str, Any]:
    mod = load_sibling("limit_up_review_workflow_contract", "limit_up_review_workflow_contract.py")
    return mod.validate(SKILL_DIR)


def run_ztc_gate(tdx_root: Path) -> dict[str, Any]:
    try:
        mod = load_sibling("tdx_ztc_source_gate", "tdx_ztc_source_gate.py")
        return mod.validate(tdx_root)
    except Exception as exc:
        return {"status": "DIAGNOSTIC_FAILED", "blocks": [f"{type(exc).__name__}: {exc}"]}


def preflight(date: str, tdx_root: Path, out_dir: Path | None = None, run_id: str = "", mode: str = "latest") -> dict[str, Any]:
    date_gate = evaluate_date_gate(date, mode)
    target_date = str(date_gate.get("target_date") or default_date())
    run_id = run_id or f"limit-up-review-{target_date.replace('-', '')}-{uuid.uuid4().hex[:12]}"
    contract = run_contract()
    ztc = run_ztc_gate(tdx_root)
    blocks: list[str] = list(date_gate.get("blocks") or [])
    historical_output_blocks: list[str] = []
    if mode == "historical":
        historical_output_blocks = validate_historical_output(out_dir)
        blocks.extend(historical_output_blocks)
    if contract.get("status") != "CLEAN_PASS":
        blocks.extend(contract.get("blocks", []))
    if out_dir is not None and not historical_output_blocks:
        task_dir = out_dir
    elif blocks:
        task_dir = REPORT_ROOT / "_blocked" / run_id
    else:
        task_dir = REPORT_ROOT / f"{target_date.replace('-', '')}_limit_up_review_closed_loop"
    task_dir.mkdir(parents=True, exist_ok=True)
    status = "CLEAN_PASS" if not blocks else "BLOCKED"
    audit = {
        "status": status,
        "checked_at": now_iso(),
        "skill": "limit-up-review",
        "run_id": run_id,
        "date": target_date,
        "date_gate": date_gate,
        "task_dir": str(task_dir),
        "tdx_root": str(tdx_root),
        "contract": contract,
        "local_block_diagnostic": ztc,
        "blocks": blocks,
        "next_action": "Continue strict data collection" if status == "CLEAN_PASS" else "Fix blocked contract items first",
        "data_red_line": "Official same-day limit-up pool is the only stock universe; local custom blocks cannot add rows.",
    }
    audit_path = task_dir / "preflight_audit.json"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    audit["audit_path"] = str(audit_path)
    return audit


def self_test() -> dict[str, Any]:
    required = [
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "TEMPLATE.md",
        SKILL_DIR / "references" / "workflow.md",
        SKILL_DIR / "references" / "business_spec.md",
        SKILL_DIR / "agents" / "openai.yaml",
        SCRIPTS_DIR / "codex_entry.py",
        SCRIPTS_DIR / "limit_up_review_workflow_contract.py",
        SCRIPTS_DIR / "limit_up_review_final_gate.py",
        SCRIPTS_DIR / "entry_limit_up_review.py",
        SCRIPTS_DIR / "collect_limitup_data_strict.py",
        SCRIPTS_DIR / "fetch_push2_fund_flow_strict.py",
        SCRIPTS_DIR / "generate_limit_up_review_strict.py",
    ]
    missing = [str(path) for path in required if not path.exists() or (path.is_file() and path.stat().st_size == 0)]
    contract = run_contract()
    canary_blocks: list[str] = []
    try:
        contract_mod = load_sibling("limit_up_review_workflow_contract_canary", "limit_up_review_workflow_contract.py")
        negative = contract_mod.validate_business_result_payload({})
        if not negative:
            canary_blocks.append("empty business_result unexpectedly passed")
    except Exception as exc:
        canary_blocks.append(f"business_result negative canary failed: {type(exc).__name__}: {exc}")
    calendar = {date_type(2026, 7, 10), date_type(2026, 7, 13)}
    intraday_now = datetime(2026, 7, 13, 12, 0, tzinfo=timezone(timedelta(hours=8)))
    after_close_now = datetime(2026, 7, 13, 15, 10, tzinfo=timezone(timedelta(hours=8)))
    stale_date_canary = evaluate_date_gate("2026-07-09", "latest", now=intraday_now, calendar_dates=calendar)
    intraday_canary = evaluate_date_gate("", "latest", now=intraday_now, calendar_dates=calendar)
    after_close_canary = evaluate_date_gate("", "latest", now=after_close_now, calendar_dates=calendar)
    if stale_date_canary.get("status") != "BLOCKED" or not any("LATEST_MODE_STALE_DATE_BLOCKED" in item for item in stale_date_canary.get("blocks", [])):
        canary_blocks.append("latest stale-date canary did not block")
    if not any("LATEST_MODE_EXPLICIT_DATE_FORBIDDEN" in item for item in stale_date_canary.get("blocks", [])):
        canary_blocks.append("latest explicit-date canary did not block")
    if intraday_canary.get("status") != "CLEAN_PASS" or intraday_canary.get("target_date") != "2026-07-10":
        canary_blocks.append("intraday latest-completed-date canary did not select prior completed trading day")
    if after_close_canary.get("status") != "CLEAN_PASS" or after_close_canary.get("target_date") != "2026-07-13":
        canary_blocks.append("after-close latest-date canary did not pass")
    historical_default_blocks = validate_historical_output(DEFAULT_DELIVERY_ROOT / "historical-probe")
    if not any("HISTORICAL_MODE_DEFAULT_DELIVERY_ROOT_FORBIDDEN" in item for item in historical_default_blocks):
        canary_blocks.append("historical default-delivery-root canary did not block")
    if contract.get("status") != "CLEAN_PASS":
        canary_blocks.extend(contract.get("blocks") or ["workflow contract failed"])
    blocks = missing + canary_blocks
    return {
        "status": "CLEAN_PASS" if not blocks else "BLOCKED",
        "checked_at": now_iso(),
        "missing_or_empty": missing,
        "contract": contract,
        "canary_blocks": canary_blocks,
        "entrypoint": str(Path(__file__).resolve()),
        "strict_steps": STRICT_STEPS,
        "date_gate_canaries": {
            "stale_date": stale_date_canary,
            "intraday_latest_completed": intraday_canary,
            "after_close_latest": after_close_canary,
            "historical_default_delivery": {
                "status": "BLOCKED" if historical_default_blocks else "CLEAN_PASS",
                "blocks": historical_default_blocks,
            },
        },
    }


def run_python(script_name: str, env: dict[str, str], extra_args: list[str] | None = None) -> dict[str, Any]:
    script = SCRIPTS_DIR / script_name
    python_exe = resolve_python()
    proc = subprocess.run(
        [python_exe, str(script), *(extra_args or [])],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return {
        "script": str(script),
        "python": python_exe,
        "code": proc.returncode,
        "stdout": proc.stdout[-8000:],
        "stderr": proc.stderr[-4000:],
    }


def full_run(date: str, tdx_root: Path, out_dir: Path | None = None, delivery_root: str = r"F:\小龙虾6月交付", mode: str = "latest") -> dict[str, Any]:
    audit = preflight(date, tdx_root, out_dir=out_dir, mode=mode)
    if audit.get("status") != "CLEAN_PASS":
        return audit
    date = str(audit["date"])
    run_id = str(audit["run_id"])
    task_dir = Path(audit["task_dir"])
    if mode == "historical":
        historical_blocks = validate_historical_output(out_dir)
        if historical_blocks:
            raise RuntimeError(";".join(historical_blocks))
        delivery_root = str(out_dir / "delivery")
    env = os.environ.copy()
    env["LIMITUP_DATE_H"] = date
    env["LIMITUP_DATE"] = date.replace("-", "")
    env["LIMITUP_TASK_DIR"] = str(task_dir)
    memory_dir = task_dir / "memory" if out_dir is not None else BUSINESS_DATA_ROOT
    history_dir = memory_dir if out_dir is not None else BUSINESS_DATA_ROOT
    env["LIMITUP_MEM_DIR"] = str(memory_dir)
    env["LIMITUP_HISTORY_DIR"] = str(history_dir)
    env["LIMITUP_DELIVERY"] = delivery_root
    env["LIMITUP_TABLE"] = str(task_dir / f"verified_limitup_union_{date.replace('-', '')}.csv")
    business_result_path = task_dir / "business_result.json"
    env["LIMITUP_RUN_ID"] = run_id
    env["LIMITUP_BUSINESS_RESULT"] = str(business_result_path)

    steps: list[dict[str, Any]] = []
    for script_name in STRICT_STEPS:
        step = run_python(script_name, env)
        steps.append(step)
        if step["code"] != 0:
            return {
                "status": "BLOCKED",
                "checked_at": now_iso(),
                "skill": "limit-up-review",
                "run_id": run_id,
                "date": date,
                "task_dir": str(task_dir),
                "blocks": [f"script_failed: {script_name}"],
                "steps": steps,
                "audit_path": audit.get("audit_path", ""),
            }

    try:
        analysis_payload = read_json(business_result_path)
        contract_mod = load_sibling("limit_up_review_workflow_contract_runtime", "limit_up_review_workflow_contract.py")
        analysis_blocks = contract_mod.validate_business_result_payload(
            analysis_payload,
            expected_date=date.replace("-", ""),
            expected_run_id=run_id,
        )
    except Exception as exc:
        analysis_payload = {}
        analysis_blocks = [f"business_result readback failed: {type(exc).__name__}: {exc}"]
    if analysis_payload.get("status") != "CLEAN_PASS":
        analysis_blocks = list(analysis_blocks) + ["business_result status is not CLEAN_PASS"]
    if analysis_blocks:
        return {
            "status": "BLOCKED",
            "checked_at": now_iso(),
            "skill": "limit-up-review",
            "run_id": run_id,
            "date": date,
            "task_dir": str(task_dir),
            "business_result": str(business_result_path),
            "blocks": sorted(set(analysis_blocks)),
            "steps": steps,
            "audit_path": audit.get("audit_path", ""),
        }

    report = Path(delivery_root) / f"涨停板深度复盘_{date}_事实结论版.docx"
    report_md = memory_dir / f"{date}-limit-up-review.md"
    table = memory_dir / f"{date}-limit-up-table.csv"
    watch = memory_dir / f"{date}-limit-up-watchlist.md"
    fund = task_dir / f"push2_fund_flow_resolved_{date.replace('-', '')}.csv"
    gate = run_python(
        "limit_up_review_final_gate.py",
        env,
        [
            "--report", str(report_md),
            "--docx", str(report),
            "--table", str(table),
            "--watchlist", str(watch),
            "--fund-flow", str(fund),
            "--task-dir", str(task_dir),
            "--analysis", str(business_result_path),
            "--expected-run-id", run_id,
            "--json",
        ],
    )
    steps.append(gate)
    final_gate_path = task_dir / "final_gate_result.json"
    gate_blocks: list[str] = []
    try:
        final_gate_payload = read_json(final_gate_path)
    except Exception as exc:
        final_gate_payload = {}
        gate_blocks.append(f"final_gate_result readback failed: {type(exc).__name__}: {exc}")
    if gate["code"] != 0:
        gate_blocks.append(f"final gate process exit={gate['code']}")
    if final_gate_payload.get("status") != "CLEAN_PASS":
        gate_blocks.append("final_gate_result status is not CLEAN_PASS")
    if final_gate_payload.get("run_id") != run_id:
        gate_blocks.append("final_gate_result run_id mismatch")
    gate_status = "CLEAN_PASS" if not gate_blocks else "BLOCKED"
    return {
        "status": gate_status,
        "checked_at": now_iso(),
        "skill": "limit-up-review",
        "run_id": run_id,
        "date": date,
        "task_dir": str(task_dir),
        "audit_path": audit.get("audit_path", ""),
        "report": str(report),
        "report_md": str(report_md),
        "table": str(table),
        "watchlist": str(watch),
        "fund_flow": str(fund),
        "business_result": str(business_result_path),
        "business_result_sha256": sha256(business_result_path),
        "final_gate_result": str(final_gate_path),
        "final_gate_result_sha256": sha256(final_gate_path) if final_gate_path.exists() else "",
        "steps": steps,
        "blocks": gate_blocks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="limit-up-review strict entrypoint")
    parser.add_argument("--date", default="")
    parser.add_argument("--tdx-root", default=str(DEFAULT_TDX_ROOT))
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--delivery-root", default=str(DEFAULT_DELIVERY_ROOT))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--historical", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        result = self_test()
    else:
        date = str(args.date or "")
        mode = "historical" if args.historical else "latest"
        out_dir = Path(args.out_dir) if args.out_dir else None
        if args.preflight_only:
            result = preflight(date, Path(args.tdx_root), out_dir=out_dir, mode=mode)
        else:
            result = full_run(date, Path(args.tdx_root), out_dir=out_dir, delivery_root=args.delivery_root, mode=mode)

    if result.get("task_dir"):
        entry_result_path = Path(result["task_dir"]) / "entry_result.json"
        entry_result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["entry_result"] = str(entry_result_path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"])
        if result.get("audit_path"):
            print(result["audit_path"])
        for block in result.get("blocks", [])[:10]:
            print(f"BLOCKED: {block}")
    return 0 if result.get("status") == "CLEAN_PASS" else 2


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
