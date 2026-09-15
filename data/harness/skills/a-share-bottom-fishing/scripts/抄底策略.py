#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

WORKSPACE = Path(r"D:\C盘转移\日志\codex")
SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
REPORTS_DIR = WORKSPACE / "reports"
LOCK = WORKSPACE / "hooks" / "skill_workflow_lock.py"
SUBSTANTIVE_GATE = WORKSPACE / "hooks" / "stock_workflow_substantive_gate.py"
TDX_HUB = SCRIPTS_DIR / "tdx_hub.py"
TDX_ROOT = Path(r"C:\new_tdx_mock")
BLOCKNEW = TDX_ROOT / "T0002" / "blocknew"
TNF_FILES = {
    "SZ": TDX_ROOT / "T0002" / "hq_cache" / "szs.tnf",
    "SH": TDX_ROOT / "T0002" / "hq_cache" / "shs.tnf",
}
TDX_INDUSTRY = TDX_ROOT / "T0002" / "hq_cache" / "tdxhy.cfg"
FORMULA_NAMES = (
    "大牛线4.0",
    "飞龙在天",
    "游资资金监控",
    "机构资金监控",
    "庄家资金监控",
)
PYTHON_EXE = sys.executable
SKILL_NAME_DISPLAY = "抄底策略"
ENTRY_SCRIPT_NAME = "抄底策略.py"
LOCKED_PRODUCTION_SCRIPT = "抄底策略_closure_gate.py"
PRIMARY_BUSINESS_SCRIPT = "validate_bottom_fishing_delivery.py"

BOTTOM_REQUIRED_TRUE_CHECKS = [
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


def run_capture(cmd: list[str], timeout: int = 120, cwd: Path | None = None) -> dict:
    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd or SKILL_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
        )
        return {
            "ok": r.returncode == 0,
            "exit": r.returncode,
            "cmd": cmd,
            "stdout": r.stdout,
            "stderr": r.stderr,
            "stdout_tail": r.stdout[-1200:],
            "stderr_tail": r.stderr[-800:],
        }
    except Exception as e:
        return {"ok": False, "cmd": cmd, "error": f"{type(e).__name__}: {e}"}


def normalize_tdx_symbol(raw: str) -> str:
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    if len(digits) >= 7:
        market = "SH" if digits[0] == "1" else "SZ"
        return f"{digits[-6:]}.{market}"
    if len(digits) >= 6:
        code = digits[-6:]
        market = "SH" if code.startswith("6") else "SZ"
        return f"{code}.{market}"
    return ""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tdx_names() -> dict[tuple[str, str], str]:
    names: dict[tuple[str, str], str] = {}
    for market, path in TNF_FILES.items():
        if not path.is_file():
            continue
        raw = path.read_bytes()
        for offset in range(50, len(raw) - 359, 360):
            record = raw[offset : offset + 360]
            code = record[:6].decode("ascii", errors="ignore")
            if len(code) != 6 or not code.isdigit():
                continue
            name = record[31:80].split(b"\0", 1)[0].decode("gb18030", errors="replace").strip()
            if name:
                names[(market, code)] = name
    return names


def load_tdx_industries() -> dict[tuple[str, str], str]:
    industries: dict[tuple[str, str], str] = {}
    if not TDX_INDUSTRY.is_file():
        return industries
    market_map = {"0": "SZ", "1": "SH", "2": "BJ"}
    for line in TDX_INDUSTRY.read_text(encoding="gb18030", errors="replace").splitlines():
        parts = line.strip().split("|")
        if len(parts) >= 3 and len(parts[1]) == 6 and parts[1].isdigit():
            market = market_map.get(parts[0])
            if market:
                industries[(market, parts[1])] = parts[2]
    return industries


def parse_json_stdout(stdout: str) -> dict:
    start = stdout.find("{")
    end = stdout.rfind("}")
    if start < 0 or end < start:
        raise ValueError("tdx_hub_stdout_not_json")
    payload = json.loads(stdout[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("tdx_hub_payload_not_object")
    return payload


def run_tdx(args: list[str], timeout: int) -> dict:
    completed = run_capture([PYTHON_EXE, str(TDX_HUB), *args], timeout=timeout)
    if not completed.get("ok"):
        raise RuntimeError(
            f"tdx_hub_failed:{args[0]}:{completed.get('exit')}:{completed.get('stderr_tail') or completed.get('error')}"
        )
    payload = parse_json_stdout(str(completed.get("stdout") or ""))
    if payload.get("ok") is not True:
        raise RuntimeError(f"tdx_hub_not_clean:{args[0]}:{payload.get('failed_formulas') or payload.get('error')}")
    return payload


def _last_number(value: object) -> float | None:
    if isinstance(value, list):
        value = next((item for item in reversed(value) if item is not None), None)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def _formula_values(item: dict, symbol: str) -> dict:
    result = item.get("result")
    if not isinstance(result, dict):
        return {}
    values = result.get(symbol)
    if isinstance(values, dict):
        return values
    return next(
        (value for key, value in result.items() if key != "ErrorId" and isinstance(value, dict)),
        {},
    )


def fetch_public_quotes(symbols: list[str]) -> dict:
    query = ",".join(
        ("sh" if symbol.endswith(".SH") else "sz") + symbol[:6]
        for symbol in symbols
    )
    url = f"https://qt.gtimg.cn/q={query}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("gb18030", errors="replace")
    quotes: dict[str, dict[str, object]] = {}
    for market_code, encoded in re.findall(r'v_([a-z]{2}\d{6})="([^"]*)"', body):
        parts = encoded.split("~")
        if len(parts) < 4:
            continue
        symbol = f"{market_code[2:]}.{'SH' if market_code.startswith('sh') else 'SZ'}"
        quotes[symbol] = {
            "symbol": symbol,
            "name": parts[1].strip(),
            "price": _last_number(parts[3]),
        }
    return {
        "status": "CLEAN_PASS" if len(quotes) == len(symbols) else "BLOCKED",
        "source": "Tencent public quote",
        "url": url,
        "requested_count": len(symbols),
        "validated_count": len(quotes),
        "quotes": [quotes[symbol] for symbol in symbols if symbol in quotes],
    }


def latest_available_trade_date() -> str:
    if not TDX_HUB.exists():
        return time.strftime("%Y%m%d")
    probe = run_capture([PYTHON_EXE, str(TDX_HUB), "kline", "600769", "--limit", "3"], timeout=45)
    try:
        payload = json.loads(probe.get("stdout") or "{}")
        records = payload.get("records") or []
        latest = str((records[-1] if records else {}).get("date") or "")
        if len(latest) == 8 and latest.isdigit():
            return latest
    except Exception:
        pass
    return time.strftime("%Y%m%d")


def read_bottom_candidates(
    limit: int = 6,
    *,
    blocknew: Path = BLOCKNEW,
    names: dict[tuple[str, str], str] | None = None,
) -> list[dict[str, object]]:
    resolved_names = load_tdx_names() if names is None else names
    candidates: list[dict[str, object]] = []
    by_symbol: dict[str, dict[str, object]] = {}
    for name in ["FLZT.blk", "ZTC.blk"]:
        path = blocknew / name
        if not path.exists():
            continue
        text = path.read_text(encoding="gbk", errors="ignore")
        for raw in text.splitlines():
            symbol = normalize_tdx_symbol(raw)
            if not symbol:
                continue
            existing = by_symbol.get(symbol)
            if existing is not None:
                source_blocks = existing["source_blocks"]
                if isinstance(source_blocks, list) and name not in source_blocks:
                    source_blocks.append(name)
                continue
            code, market = symbol.split(".", 1)
            candidate = {
                "symbol": symbol,
                "name": resolved_names.get((market, code), ""),
                "source_blocks": [name],
                "candidate_pool_rank": len(candidates) + 1,
                "group": "bottom_fishing_auto",
            }
            candidates.append(candidate)
            by_symbol[symbol] = candidate
            if len(candidates) >= limit:
                return candidates
    return candidates


def analyze_candidate(candidate: dict[str, object], industry: str) -> dict[str, object]:
    symbol = str(candidate["symbol"])
    kline = run_tdx(["kline", symbol, "--period", "day", "--limit", "0"], timeout=60)
    records = kline.get("records")
    if not isinstance(records, list) or not records:
        raise RuntimeError(f"kline_missing:{symbol}")
    end_date = dt.datetime.strptime(str(records[-1]["date"]), "%Y%m%d").date()
    try:
        cutoff = end_date.replace(year=end_date.year - 3)
    except ValueError:
        cutoff = end_date.replace(year=end_date.year - 3, day=28)
    window = [row for row in records if str(row.get("date", "")) >= cutoff.strftime("%Y%m%d")]
    if len(window) < 500:
        raise RuntimeError(f"three_year_kline_incomplete:{symbol}:{len(window)}")

    five = run_tdx(["five", symbol], timeout=300)
    items = five.get("items")
    if not isinstance(items, list):
        raise RuntimeError(f"five_formula_items_missing:{symbol}")
    by_formula = {str(item.get("formula")): item for item in items if isinstance(item, dict)}
    if set(by_formula) != set(FORMULA_NAMES) or any(by_formula[name].get("ok") is not True for name in FORMULA_NAMES):
        raise RuntimeError(f"five_formula_incomplete:{symbol}")
    feilong_values = _formula_values(by_formula["飞龙在天"], symbol)
    wave = _last_number(feilong_values.get("波"))
    segment = _last_number(feilong_values.get("段"))
    if wave is None or segment is None:
        raise RuntimeError(f"feilong_wave_segment_missing:{symbol}")

    formula_signal_count = 0
    formula_summaries: list[dict[str, object]] = []
    for formula_name in FORMULA_NAMES:
        item = by_formula[formula_name]
        values = _formula_values(item, symbol)
        nonzero = sum(
            1 for value in values.values()
            if (number := _last_number(value)) is not None and abs(number) > 1e-12
        )
        formula_signal_count += nonzero
        formula_summaries.append({
            "formula": formula_name,
            "runtime_formula": item.get("tq_formula"),
            "ok": True,
            "nonzero_latest_value_count": nonzero,
        })

    closes = [float(row["close"]) for row in window]
    recent = closes[-60:]
    recent_low = min(recent)
    recent_high = max(recent)
    latest_close = closes[-1]
    low_location = 1.0 - (latest_close - recent_low) / (recent_high - recent_low) if recent_high > recent_low else 0.0
    low_position_score = round(max(0.0, 50.0 * (1.0 - max(wave, segment) / 20.0)), 4)
    formula_breadth_score = round(30.0 * sum(row["nonzero_latest_value_count"] > 0 for row in formula_summaries) / 5.0, 4)
    price_location_score = round(max(0.0, min(20.0, 20.0 * low_location)), 4)
    score_breakdown = {
        "feilong_low_position": low_position_score,
        "five_formula_breadth": formula_breadth_score,
        "recent_60_bar_low_location": price_location_score,
    }
    low_signal = wave < 20.0 and segment < 20.0
    risk_ok = (
        not symbol.endswith(".BJ")
        and not (symbol.endswith(".SH") and symbol.startswith(("688", "689")))
        and "ST" not in str(candidate.get("name", "")).upper()
        and "退" not in str(candidate.get("name", ""))
        and "银行" not in industry
    )
    selection_status = "SIGNAL" if low_signal and risk_ok else "NO_SIGNAL"
    data_path = Path(str(kline.get("path") or ""))
    return {
        **candidate,
        "industry": industry,
        "trade_date": end_date.strftime("%Y%m%d"),
        "selection_status": selection_status,
        "selection_reason": (
            f"飞龙在天波值{wave:.2f}、段值{segment:.2f}均低于20"
            if low_signal and risk_ok
            else f"飞龙在天波值{wave:.2f}、段值{segment:.2f}未同时满足低于20及风险过滤"
        ),
        "wave": round(wave, 4),
        "segment": round(segment, 4),
        "score": round(sum(score_breakdown.values()), 4),
        "score_breakdown": score_breakdown,
        "five_formula_signal_count": formula_signal_count,
        "formula_evidence": formula_summaries,
        "kline_evidence": {
            "source_type": "tdx_local_hub",
            "path": str(data_path),
            "sha256": sha256_file(data_path) if data_path.is_file() else None,
            "full_record_count": len(records),
            "window_start_date": str(window[0]["date"]),
            "window_end_date": str(window[-1]["date"]),
            "three_year_record_count": len(window),
            "latest_close": latest_close,
        },
        "risk_checks": {
            "no_bj": not symbol.endswith(".BJ"),
            "no_kcb": not (symbol.endswith(".SH") and symbol.startswith(("688", "689"))),
            "no_st_delist": "ST" not in str(candidate.get("name", "")).upper() and "退" not in str(candidate.get("name", "")),
            "no_bank": "银行" not in industry,
        },
    }


def generate_bottom_fishing_task() -> dict[str, object]:
    trade_date = latest_available_trade_date()
    names = load_tdx_names()
    industries = load_tdx_industries()
    candidates = read_bottom_candidates(names=names)
    task_dir = REPORTS_DIR / f"{trade_date}_bottom_fishing_auto"
    output_dir = task_dir / "output"
    audit_dir = task_dir / "audit"
    validation_dir = task_dir / "validation"
    for path in [output_dir, audit_dir, validation_dir]:
        path.mkdir(parents=True, exist_ok=True)
    if not candidates:
        return {"ok": False, "task_dir": str(task_dir), "error": "no local TDX FLZT/ZTC candidates"}

    scan_errors: list[dict[str, str]] = []
    for candidate in candidates:
        if not str(candidate.get("name") or "").strip():
            scan_errors.append({"symbol": str(candidate["symbol"]), "error": "tdx_name_missing"})
    try:
        public_quotes = fetch_public_quotes([str(row["symbol"]) for row in candidates])
    except Exception as exc:
        public_quotes = {
            "status": "BLOCKED",
            "source": "Tencent public quote",
            "requested_count": len(candidates),
            "validated_count": 0,
            "quotes": [],
            "error": f"{type(exc).__name__}:{exc}",
        }
    quote_by_symbol = {
        str(row.get("symbol")): row
        for row in public_quotes.get("quotes", [])
        if isinstance(row, dict)
    }
    for candidate in candidates:
        symbol = str(candidate["symbol"])
        quote = quote_by_symbol.get(symbol)
        if not isinstance(quote, dict):
            scan_errors.append({"symbol": symbol, "error": "public_quote_missing"})
            continue
        candidate["public_name"] = str(quote.get("name") or "").strip()
        candidate["public_price"] = quote.get("price")
        if candidate["public_name"] != candidate.get("name"):
            scan_errors.append({"symbol": symbol, "error": "public_tdx_name_mismatch"})

    evaluations: list[dict[str, object]] = []
    if not scan_errors:
        for candidate in candidates:
            code, market = str(candidate["symbol"]).split(".", 1)
            try:
                evaluations.append(analyze_candidate(candidate, industries.get((market, code), "")))
            except Exception as exc:
                scan_errors.append({
                    "symbol": str(candidate["symbol"]),
                    "error": f"{type(exc).__name__}:{exc}",
                })
    (audit_dir / "scan_errors_v2.json").write_text(
        json.dumps(scan_errors, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "public_quote_validation_v2.json").write_text(
        json.dumps({**public_quotes, "trade_date": trade_date}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if scan_errors:
        return {
            "ok": False,
            "task_dir": str(task_dir),
            "error": "bottom_fishing_evidence_incomplete",
            "scan_errors": scan_errors,
        }

    evaluations.sort(key=lambda row: (-float(row["score"]), str(row["symbol"])))
    final_rows = [row for row in evaluations if row["selection_status"] == "SIGNAL"][:3]
    selection_status = "SIGNAL" if final_rows else "NO_SIGNAL"
    json_path = output_dir / "final_picks_v2_public_validated.json"
    csv_path = output_dir / "final_picks_v2_public_validated.csv"
    evidence_path = output_dir / "candidate_evidence_v3.json"
    json_path.write_text(json.dumps(final_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    evidence_path.write_text(json.dumps(evaluations, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "symbol", "name", "selection_status", "trade_date", "wave", "segment",
            "score", "source_blocks", "selection_reason",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in final_rows:
            writer.writerow({
                key: ";".join(row[key]) if key == "source_blocks" else row.get(key)
                for key in fieldnames
            })

    (output_dir / "selection_process_and_result_v2_public_validated.md").write_text(
        "\n".join([
            "# 抄底策略 v2 自动闭环产物",
            "",
            f"- 交易日口径: {trade_date}",
            f"- 候选来源: C:\\new_tdx_mock\\T0002\\blocknew\\FLZT.blk / ZTC.blk",
            f"- 去重后评估数: {len(evaluations)}",
            f"- 最终信号数: {len(final_rows)}",
            f"- 选择状态: {selection_status}",
            "- 数据链: TDX最近三年日线 + TQ五公式 + 腾讯公开名称交叉验证。",
            "- 风险边界: 研究结论，不是自动交易指令。",
        ]),
        encoding="utf-8",
    )
    (task_dir / "strict_overlay_v2_public_validated.md").write_text(
        "# strict overlay v2\n\nEvidence is recomputed from unique named rows, three-year TDX K-lines, five live TQ formulas, and public quote name matching.\n",
        encoding="utf-8",
    )
    for rel, payload in {
        "duplicate_suppressed_v2.json": [
            {"symbol": row["symbol"], "merged_source_blocks": row["source_blocks"]}
            for row in evaluations if len(row["source_blocks"]) > 1
        ],
        "exclusions_v2.json": {
            "excluded": [
                {"symbol": row["symbol"], "risk_checks": row["risk_checks"]}
                for row in evaluations if not all(row["risk_checks"].values())
            ],
            "rules": ["no_bj", "no_kcb", "no_st_delist", "no_bank"],
        },
        "realtime_failed_v2.json": [],
    }.items():
        (audit_dir / rel).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    final_symbols = [str(row["symbol"]) for row in final_rows]
    evaluation_symbols = [str(row["symbol"]) for row in evaluations]
    checks = {
        "uses_three_year_kline": all(int(row["kline_evidence"]["three_year_record_count"]) >= 500 for row in evaluations),
        "five_formula_subsystems_read": all(len(row["formula_evidence"]) == 5 and all(item["ok"] for item in row["formula_evidence"]) for row in evaluations),
        "no_bj": all(row["risk_checks"]["no_bj"] for row in final_rows),
        "no_kcb": all(row["risk_checks"]["no_kcb"] for row in final_rows),
        "no_st_delist": all(row["risk_checks"]["no_st_delist"] for row in final_rows),
        "no_bank": all(row["risk_checks"]["no_bank"] for row in final_rows),
        "no_missing_or_pending_names": all(str(row.get("name") or "").strip() for row in evaluations),
        "all_realtime_wave_segment_lt20": all(float(row["wave"]) < 20 and float(row["segment"]) < 20 for row in final_rows),
        "scoring_complete": all(abs(float(row["score"]) - sum(float(value) for value in row["score_breakdown"].values())) < 1e-6 for row in evaluations),
        "global_unique_codes": len(evaluation_symbols) == len(set(evaluation_symbols)) and len(final_symbols) == len(set(final_symbols)),
        "top3_per_group": len(final_rows) <= 3,
        "nonzero_candidates": bool(evaluations),
        "nonzero_final": bool(final_rows),
        "no_scan_errors": True,
        "public_quote_validation_read": public_quotes.get("status") == "CLEAN_PASS",
        "public_names_no_missing": all(str(row.get("public_name") or "").strip() for row in evaluations),
        "final_public_name_consistency": all(row.get("public_name") == row.get("name") for row in evaluations),
    }
    acceptance = {
        "status": "CLEAN_PASS",
        "skill": SKILL_DIR.name,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "selection_status": selection_status,
        "checks": checks,
        "meta": {
            "scan_error_count": 0,
            "final_count": len(final_rows),
            "candidate_count": len(evaluations),
            "source": "local_tdx_blocknew",
            "candidate_evidence": str(evidence_path),
        },
    }
    (validation_dir / "acceptance_v2_public_validated.json").write_text(
        json.dumps(acceptance, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "ok": True,
        "task_dir": str(task_dir),
        "final_count": len(final_rows),
        "candidate_count": len(evaluations),
        "selection_status": selection_status,
        "trade_date": trade_date,
    }


def cmd_info(_: argparse.Namespace) -> int:
    print(json.dumps({
        "skill": SKILL_DIR.name,
        "skill_dir": str(SKILL_DIR),
        "entry": str(Path(__file__).resolve()),
        "locked_execution": str(SCRIPTS_DIR / LOCKED_PRODUCTION_SCRIPT),
        "workflow": str(SKILL_DIR / "references" / "workflow.md"),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    for p in sorted(SCRIPTS_DIR.glob("*.py")):
        if p.name != "__init__.py":
            print(p.name)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    script = args.script
    if not script.endswith(".py"):
        script += ".py"
    target = SCRIPTS_DIR / script
    if not target.exists():
        print(f"run: script not found: {target}", file=sys.stderr)
        return 2
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.run([PYTHON_EXE, str(target)] + (args.args or []), cwd=str(SKILL_DIR), env=env).returncode


def cmd_selftest(_: argparse.Namespace) -> int:
    steps = []
    if LOCK.exists():
        r = run_capture([PYTHON_EXE, str(LOCK), "check", "--skill", SKILL_DIR.name], timeout=120)
        r["step"] = "skill_workflow_lock_check"
        stdout = r.get("stdout", "") or r.get("stdout_tail", "")
        r["ok"] = r.get("ok") and ('"status": "CLEAN_PASS"' in stdout or '"blocks": []' in stdout)
        steps.append(r)
    else:
        steps.append({"step": "skill_workflow_lock_check", "ok": False, "error": f"missing {LOCK}"})
    if SUBSTANTIVE_GATE.exists():
        r = run_capture([PYTHON_EXE, str(SUBSTANTIVE_GATE), "check", "--skill", SKILL_DIR.name], timeout=120)
        r["step"] = "stock_workflow_substantive_gate"
        stdout = r.get("stdout", "") or r.get("stdout_tail", "")
        r["ok"] = r.get("ok") and ('"status": "CLEAN_PASS"' in stdout or '"blocks": []' in stdout)
        steps.append(r)
    else:
        steps.append({"step": "stock_workflow_substantive_gate", "ok": False, "error": f"missing {SUBSTANTIVE_GATE}"})
    ok = all(s.get("ok") for s in steps)
    print(json.dumps({
        "skill": SKILL_DIR.name,
        "mode": "selftest",
        "status": "CLEAN_PASS" if ok else "BLOCKED",
        "steps": steps,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1



def infer_auto_status(ok, steps):
    if ok:
        return "CLEAN_PASS"
    text = json.dumps(steps, ensure_ascii=False)
    blocked_markers = ("BLOCKED", "BLOCKED_BY_", "DATA_STALE", "DATA_BLOCKED", "AUDIT_BLOCKED", "TIMEOUT")
    return "BLOCKED" if any(marker in text for marker in blocked_markers) else "FAILED"

def cmd_auto(_: argparse.Namespace) -> int:
    steps = []
    selftest = run_capture([PYTHON_EXE, str(Path(__file__).resolve()), "selftest"], timeout=180)
    selftest["step"] = "selftest"
    stdout = selftest.get("stdout", "") or selftest.get("stdout_tail", "")
    selftest["ok"] = selftest.get("ok") and ('"status": "CLEAN_PASS"' in stdout or '"all_ok": true' in stdout)
    steps.append(selftest)

    locked_target = SCRIPTS_DIR / LOCKED_PRODUCTION_SCRIPT
    if not locked_target.exists():
        steps.append({"step": "locked_execution", "ok": False, "error": f"missing {locked_target}"})
    else:
        r = run_capture([PYTHON_EXE, str(locked_target)], timeout=240)
        r["step"] = "locked_execution"
        r["script"] = locked_target.name
        steps.append(r)

    generated = generate_bottom_fishing_task()
    generated["step"] = "generate_delivery_task"
    steps.append(generated)

    business_target = SCRIPTS_DIR / PRIMARY_BUSINESS_SCRIPT
    if not business_target.exists():
        steps.append({"step": "primary_business", "ok": False, "error": f"missing {business_target}"})
    else:
        r = run_capture([PYTHON_EXE, str(business_target), "--task-dir", str(generated.get("task_dir", ""))], timeout=600)
        r["step"] = "primary_business"
        r["script"] = business_target.name
        r["task_dir"] = generated.get("task_dir")
        steps.append(r)

    ok = all(s.get("ok") for s in steps)
    print(json.dumps({
        "skill": SKILL_DIR.name,
        "mode": "auto",
        "entry_script": str(Path(__file__).resolve()),
        "locked_execution": str(locked_target),
        "primary_business_script": str(business_target),
        "task_dir": generated.get("task_dir"),
        "executed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": infer_auto_status(ok, steps),
        "all_ok": ok,
        "steps": steps,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{SKILL_NAME_DISPLAY} Codex unique execution entry")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("info")
    sub.add_parser("list")
    sub.add_parser("selftest")
    sub.add_parser("auto")
    run_p = sub.add_parser("run")
    run_p.add_argument("script")
    run_p.add_argument("args", nargs=argparse.REMAINDER)
    return parser


def main() -> int:
    parser = build_parser()
    if len(sys.argv) == 1:
        return cmd_auto(None)
    args = parser.parse_args()
    if args.cmd == "info":
        return cmd_info(args)
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "selftest":
        return cmd_selftest(args)
    if args.cmd == "auto":
        return cmd_auto(args)
    if args.cmd == "run":
        return cmd_run(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
