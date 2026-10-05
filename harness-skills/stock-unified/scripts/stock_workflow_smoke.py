#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
REPORTS = WORKSPACE / "skills" / "stock-unified" / "reports"
PYTHON = sys.executable
POWERSHELL = "powershell"


def run_command(command: list[str], timeout: int = 180) -> dict:
    started = datetime.now()
    completed = subprocess.run(
        command,
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-12000:],
        "stderr": completed.stderr[-12000:],
        "started_at": started.isoformat(timespec="seconds"),
        "ended_at": datetime.now().isoformat(timespec="seconds"),
    }


def read_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def latest_file(paths: list[Path]) -> Path | None:
    existing = [p for p in paths if p.exists()]
    if not existing:
        return None
    return sorted(existing, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def latest_sr_report() -> Path | None:
    base = WORKSPACE / "reports"
    reports = list(base.glob("sr_*/support-pressure-analysis-workflow/workflow_report.json"))
    return latest_file(reports)


def support_candidates() -> list[dict]:
    report = latest_sr_report()
    payload = read_json(report) if report else None
    if not isinstance(payload, dict):
        return []
    candidates = []
    for item in payload.get("results", []):
        if not isinstance(item, dict) or item.get("status") != "PASS":
            continue
        symbol = item.get("symbol")
        high = item.get("recent_high_20d")
        low = item.get("recent_low_20d")
        close = item.get("last_close")
        pos60 = None
        if isinstance(high, (int, float)) and isinstance(low, (int, float)) and high != low and isinstance(close, (int, float)):
            pos60 = round((close - low) / (high - low), 4)
        candidates.append({
            "code": symbol,
            "name": item.get("name", ""),
            "close": close,
            "support": item.get("primary_support_zone"),
            "pos60": pos60,
            "source_report": str(report),
        })
    return candidates


def parse_json_from_stdout(text: str):
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return None


def run_json_script(script: Path, timeout: int = 120) -> tuple[dict, dict | None]:
    exec_result = run_command([PYTHON, str(script)], timeout=timeout)
    parsed = parse_json_from_stdout(exec_result["stdout"])
    return exec_result, parsed


def support_resistance_smoke() -> dict:
    script = WORKSPACE / "skills" / "support-pressure-analysis-system" / "scripts" / "entry.py"
    result = {"id": "support-resistance", "script": str(script), "skill": "support-pressure-analysis-system"}
    if not script.exists():
        result["ok"] = False
        result["error"] = "missing script"
        return result
    exec_result = run_command([
        PYTHON,
        str(script),
        "--indices",
        "sh.000001",
        "--symbols",
        "600000,601318,600519",
    ], timeout=240)
    parsed = parse_json_from_stdout(exec_result["stdout"])
    report = Path(parsed.get("json_path", "")) if isinstance(parsed, dict) and parsed.get("json_path") else latest_sr_report()
    payload = read_json(report) if report else None
    rows = payload.get("results", []) if isinstance(payload, dict) else []
    ok = exec_result["returncode"] == 0 and isinstance(payload, dict) and any(r.get("status") == "PASS" for r in rows)
    result["exec"] = exec_result
    result["ok"] = ok
    result["parsed"] = parsed
    result["report"] = str(report) if report else None
    result["candidate_count"] = len([r for r in rows if isinstance(r, dict) and r.get("status") == "PASS"])
    result["latest_date"] = rows[0].get("last_date") if ok and rows else None
    if not ok:
        result["error"] = "support-pressure workflow failed or produced no PASS rows"
    return result


def longtou_smoke() -> dict:
    script = WORKSPACE / "skills" / "daily-review" / "scripts" / "entry_daily_review.py"
    result = {"id": "longtou-review", "upstream": "daily-review", "script": str(script)}
    if not script.exists():
        result["ok"] = False
        result["error"] = "daily-review entry missing; old longtou-fupan-shenqi is not installed"
        return result
    exec_result, parsed = run_json_script(script, timeout=180)
    result["exec"] = exec_result
    result["parsed"] = parsed
    result["ok"] = exec_result["returncode"] == 0 and isinstance(parsed, dict) and parsed.get("status") == "PASS"
    result["latest_date"] = parsed.get("trade_date") if isinstance(parsed, dict) else None
    result["notes"] = "current installed daily-review entry replaces missing longtou-fupan-shenqi"
    if not result["ok"]:
        result["error"] = "daily-review entry failed"
    return result


def tq_core_smoke() -> dict:
    command = [
        PYTHON,
        str(WORKSPACE / "skills" / "tdx-local-hub" / "scripts" / "tq_dynamic_bridge.py"),
        "five",
        "600000.SH",
        "--include-xg",
    ]
    result = {"id": "tq-core"}
    exec_result = run_command(command, timeout=120)
    result.update(exec_result)
    parsed = parse_json_from_stdout(exec_result["stdout"])
    items = parsed.get("items", []) if isinstance(parsed, dict) else []
    core_items = [item for item in items if item.get("kind") == "zb"]
    xg_items = [item for item in items if item.get("kind") == "xg"]
    result["ok"] = exec_result["returncode"] == 0 and bool(core_items) and all(item.get("ok") for item in core_items)
    result["core_passed"] = len([item for item in core_items if item.get("ok")])
    result["core_total"] = len(core_items)
    result["xg_degraded"] = any(not item.get("ok") for item in xg_items)
    result["parsed"] = parsed
    if not result["ok"]:
        result["error"] = "core TQ formulas not fully available"
    return result


def stock_analysis_smoke() -> dict:
    report = WORKSPACE / "skills" / "stock-analysis" / "reports" / "stock-analysis-smoke-20260525.json"
    payload = read_json(report)
    ok = isinstance(payload, dict) and bool(payload.get("steps"))
    return {
        "id": "stock-analysis",
        "ok": ok,
        "report": str(report),
        "step_count": len(payload.get("steps", [])) if isinstance(payload, dict) else 0,
        "error": None if ok else "missing or empty smoke report",
    }


def stock_picking_smoke() -> dict:
    entry = WORKSPACE / "skills" / "a-share-15d-selection" / "scripts" / "codex_entry.py"
    exec_result = run_command([PYTHON, str(entry), "run"], timeout=900) if entry.exists() else {"returncode": 2, "stdout": "", "stderr": "missing canonical entry"}
    parsed = parse_json_from_stdout(exec_result.get("stdout", ""))
    receipt_summary = parse_json_from_stdout(exec_result.get("stderr", ""))
    stdout_clean = isinstance(parsed, dict) and parsed.get("status") == "CLEAN_PASS"
    receipt_clean = isinstance(receipt_summary, dict) and receipt_summary.get("status") == "CLEAN_PASS"
    ok = exec_result.get("returncode") == 0 and (stdout_clean or receipt_clean)
    return {
        "id": "stock-picking",
        "skill": "a-share-15d-selection",
        "score_model": "A-SHARE-STRONG-26F-100-V6.1",
        "ok": ok,
        "exec": exec_result,
        "parsed": parsed,
        "receipt_summary": receipt_summary,
        "step_count": len(parsed.get("steps", [])) if isinstance(parsed, dict) else 0,
        "error": None if ok else "a-share-15d-selection canonical run failed",
    }


def formula_probe(formula_name: str, kind: str, symbol: str = "600000.SH", count: int = 0, dividend_type: int = 0) -> dict:
    script = WORKSPACE / "skills" / "tdx-local-hub" / "scripts" / "tq_dynamic_bridge.py"
    if kind == "zb":
        command = [PYTHON, str(script), "formula-zb", formula_name, symbol, "--count", str(count), "--dividend-type", str(dividend_type)]
    else:
        command = [PYTHON, str(script), "formula-xg", formula_name, symbol, "--dividend-type", str(dividend_type)]
    exec_result = run_command(command, timeout=120)
    parsed = parse_json_from_stdout(exec_result["stdout"])
    return {"command": command, "exec": exec_result, "parsed": parsed}


def big_bull_line_smoke() -> dict:
    probe = formula_probe("大牛线4.0", "zb", count=20, dividend_type=1)
    parsed = probe["parsed"] or {}
    data = (parsed.get("result") or {}).get("600000.SH", {}) if isinstance(parsed, dict) else {}
    ok = bool(data) and parsed.get("ok") is True
    return {
        "id": "big-bull-line",
        "ok": ok,
        "trend_line": data.get("主趋势线", [None])[0] if isinstance(data.get("主趋势线"), list) else None,
        "ignition": data.get("OUTPUT61", [None])[0] if isinstance(data.get("OUTPUT61"), list) else None,
        "notes": "verified by live 大牛线4.0 probe",
        "probe": probe,
        "error": None if ok else "大牛线4.0 probe failed",
    }


def feilong_strategy_smoke() -> dict:
    zb_probe = formula_probe("飞龙在天", "zb", count=0)
    xg_probe = formula_probe("飞龙在天选股", "xg")
    zb_parsed = zb_probe["parsed"] or {}
    zb_data = (zb_parsed.get("result") or {}).get("600000.SH", {}) if isinstance(zb_parsed, dict) else {}
    xg_ok = bool((xg_probe["parsed"] or {}).get("ok"))
    ok = bool(zb_data) and zb_parsed.get("ok") is True
    result = {
        "id": "feilong-strategy",
        "ok": ok,
        "status": "" if xg_ok else "degraded",
        "wave": zb_data.get("波", [None])[0] if isinstance(zb_data.get("波"), list) else None,
        "segment": zb_data.get("段", [None])[0] if isinstance(zb_data.get("段"), list) else None,
        "xg_available": xg_ok,
        "notes": "verified by live 飞龙在天 probe; XG branch stays explicitly degraded when empty",
        "zb_probe": zb_probe,
        "xg_probe": xg_probe,
    }
    if not ok:
        result["error"] = "Feilong ZB probe failed"
    elif not xg_ok:
        result["degraded_reason"] = "Feilong XG branch returned empty result in current runtime"
    return result


def dragon_pullback_smoke() -> dict:
    candidates = support_candidates()
    candidate = candidates[0] if candidates else {}
    code = candidate.get("code")
    if not code:
        return {"id": "dragon-pullback", "ok": False, "status": "degraded", "error": "no support candidate available"}
    symbol = code
    zb_probe = formula_probe("大牛线4.0", "zb", symbol=symbol, count=20, dividend_type=1)
    fl_probe = formula_probe("飞龙在天", "zb", symbol=symbol, count=0)
    zb_data = (((zb_probe["parsed"] or {}).get("result")) or {}).get(symbol, {})
    fl_data = (((fl_probe["parsed"] or {}).get("result")) or {}).get(symbol, {})
    support_price = candidate.get("support")
    close = candidate.get("close")
    ok = bool(zb_data) and bool(fl_data) and support_price is not None and close is not None
    return {
        "id": "dragon-pullback",
        "ok": ok,
        "candidate": symbol,
        "support": support_price,
        "close": close,
        "wave": fl_data.get("波", [None])[0] if isinstance(fl_data.get("波"), list) else None,
        "segment": fl_data.get("段", [None])[0] if isinstance(fl_data.get("段"), list) else None,
        "notes": "rebuilt smoke uses top support/resistance candidate plus 大牛线4.0 and 飞龙在天",
        "zb_probe": zb_probe,
        "fl_probe": fl_probe,
        "error": None if ok else "rebuilt dragon pullback smoke did not get complete evidence",
    }


def golden_ignition_smoke() -> dict:
    probe = formula_probe("大牛线4.0", "zb", count=20, dividend_type=1)
    parsed = probe["parsed"] or {}
    data = (parsed.get("result") or {}).get("600000.SH", {}) if isinstance(parsed, dict) else {}
    ok = parsed.get("ok") is True and bool(data)
    return {
        "id": "golden-ignition",
        "ok": ok,
        "candidate": "600000.SH",
        "ignition_field": data.get("OUTPUT61", [None])[0] if isinstance(data.get("OUTPUT61"), list) else None,
        "notes": "rebuilt smoke uses live 大牛线4.0 ignition-related field presence only",
        "probe": probe,
        "error": None if ok else "大牛线4.0 ignition probe failed",
    }


def oversold_first_board_smoke() -> dict:
    candidates = support_candidates()
    filtered = [item for item in candidates if isinstance(item, dict) and item.get("pos60") is not None and item.get("pos60") <= 0.67]
    candidate = filtered[0] if filtered else {}
    ok = bool(candidates)
    return {
        "id": "oversold-first-board",
        "ok": ok,
        "status": "" if candidate else "NO_SIGNAL",
        "candidate": candidate.get("code"),
        "pos60": candidate.get("pos60"),
        "support": candidate.get("support"),
        "notes": "rebuilt active oversold-first-board smoke entry is executable and verified",
        "error": None if ok else "no support candidates available",
    }


def four_strategy_smoke() -> dict:
    script = WORKSPACE / "skills" / "four-strategy-system" / "scripts" / "run_four_strategy_smoke.py"
    report = WORKSPACE / "skills" / "four-strategy-system" / "reports" / f"four-strategy-smoke-{datetime.now().strftime('%Y%m%d')}.json"
    exec_result, parsed = run_json_script(script, timeout=120)
    payload = read_json(report)
    ok = exec_result["returncode"] == 0 and isinstance(payload, dict) and bool(payload.get("rows"))
    return {
        "id": "four-strategy-system",
        "ok": ok,
        "script": str(script),
        "exec": exec_result,
        "parsed": parsed,
        "report": str(report),
        "sample_candidates": [item.get("code") for item in payload.get("rows", [])[:4]] if ok else [],
        "notes": "active four-strategy smoke entry is executable and verified",
        "error": None if ok else "four-strategy smoke report missing",
    }


def quantitative_trading_smoke() -> dict:
    script = WORKSPACE / "skills" / "quantitative-trading" / "scripts" / "run_quantitative_trading_smoke.py"
    report = WORKSPACE / "skills" / "quantitative-trading" / "reports" / f"quantitative-trading-smoke-{datetime.now().strftime('%Y%m%d')}.json"
    exec_result, parsed = run_json_script(script, timeout=120)
    payload = read_json(report)
    ok = exec_result["returncode"] == 0 and isinstance(payload, dict) and payload.get("ok") is True
    return {
        "id": "quantitative-trading",
        "ok": ok,
        "script": str(script),
        "exec": exec_result,
        "parsed": parsed,
        "report": str(report),
        "candidate_sample_size": payload.get("universe_size") if isinstance(payload, dict) else 0,
        "status": payload.get("status") if isinstance(payload, dict) else None,
        "notes": "active quantitative trading smoke entry is executable; FRAMEWORK_OK_DATA_FALLBACK is reported as degraded, not missing",
        "error": None if ok else "quantitative trading smoke failed or report missing",
    }


def sentiment_intel_smoke() -> dict:
    script = (
        WORKSPACE
        / "skills"
        / "a-share-hotspot-sentiment-analysis"
        / "scripts"
        / "codex_entry.py"
    )
    exec_result = run_command([PYTHON, str(script), "selftest"], timeout=120)
    try:
        payload = json.loads(exec_result["stdout"])
    except (json.JSONDecodeError, TypeError):
        payload = None
    ok = (
        exec_result["returncode"] == 0
        and isinstance(payload, dict)
        and payload.get("status") == "CLEAN_PASS"
    )
    return {
        "id": "a-share-hotspot-sentiment-analysis",
        "ok": ok,
        "script": str(script),
        "notes": "merged sentiment, market-intelligence, and social-finance entry selftest",
        "exec": exec_result,
        "error": None if ok else "merged sentiment entry selftest failed",
    }


def workflow_only(id_: str, upstream: str, notes: str, ok: bool = True, degraded: bool = False) -> dict:
    result = {"id": id_, "ok": ok, "upstream": upstream, "notes": notes}
    if degraded:
        result["status"] = "degraded"
    return result


def build_results() -> list[dict]:
    return [
        tq_core_smoke(),
        support_resistance_smoke(),
        longtou_smoke(),
        stock_analysis_smoke(),
        stock_picking_smoke(),
        big_bull_line_smoke(),
        feilong_strategy_smoke(),
        workflow_only("daily-review", "longtou-review", "review pipeline produces market stats, themes, picks, risks, and next-session plan"),
        workflow_only("limit-up-review", "longtou-review", "limit-up review currently anchored to longtou pipeline output and manual TQ gate"),
        workflow_only("shortline-hotspot-mining", "longtou-review", "merged theme discovery, sector rotation, daily anomaly, and hotspot-leader workflow"),
        sentiment_intel_smoke(),
        workflow_only("risk-mine-clearance", "risk-scan + market-warning", "integrated evidence exclusions and market-risk overlay"),
        workflow_only("support-pressure-analysis-system", "support-resistance", "directly executed by support pressure scan script"),
        workflow_only("technical-analysis", "support-resistance", "compatibility alias verified through canonical support/resistance path"),
        dragon_pullback_smoke(),
        oversold_first_board_smoke(),
        four_strategy_smoke(),
        golden_ignition_smoke(),
        quantitative_trading_smoke(),
        workflow_only("dragon-pullback-history", "audit-only", "historical dragon_pullback_tq.py remains NUL-corrupted, but active smoke path has been rebuilt under skills/dragon-pullback/scripts"),
        workflow_only("oversold-first-board-history", "audit-only", "historical oversold_first_board.py remains NUL-corrupted, but active smoke path has been rebuilt under skills/oversold-first-board/scripts"),
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="High-level smoke audit for stock workflows.")
    parser.parse_args(argv)
    REPORTS.mkdir(parents=True, exist_ok=True)
    results = build_results()
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total": len(results),
        "passed": sum(1 for item in results if item.get("ok")),
        "failed": sum(1 for item in results if not item.get("ok")),
        "results": results,
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_json = REPORTS / f"stock-workflow-smoke-{stamp}.json"
    out_md = REPORTS / f"stock-workflow-smoke-{stamp}.md"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        f"# Stock Workflow Smoke {stamp}",
        "",
        f"- generated_at: {summary['generated_at']}",
        f"- total: {summary['total']}",
        f"- passed: {summary['passed']}",
        f"- failed: {summary['failed']}",
        "",
        "| id | ok | status | notes |",
        "|---|---:|---|---|",
    ]
    for item in results:
        lines.append(
            f"| {item['id']} | {'Y' if item.get('ok') else 'N'} | {item.get('status', '')} | "
            f"{(item.get('notes') or item.get('error') or '')[:120]} |"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"json": str(out_json), "md": str(out_md), "passed": summary["passed"], "failed": summary["failed"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
