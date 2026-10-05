#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[3]
SKILL_ROOT = Path(__file__).resolve().parents[1]
_DATA_ROOT = os.environ.get("ONESTOCK_STOCK_DATA_ROOT", "").strip()
REPORTS = (
    Path(_DATA_ROOT).expanduser().resolve() / "runtime" / "skills" / "oversold-first-board" / "reports"
    if _DATA_ROOT
    else SKILL_ROOT / "reports"
)
APP_ROOT = Path(__file__).resolve().parents[3]
APP_SCRIPTS = APP_ROOT / "scripts"
if str(APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(APP_SCRIPTS))
from tdx_path_config import resolve_tdx_root

TDX_ROOT = resolve_tdx_root()
TDX_HUB_PATH = APP_ROOT / "harness-skills" / "tdx-local-hub" / "scripts" / "tdx_hub.py"
TNF_FILES = {
    "SZ": TDX_ROOT / "T0002" / "hq_cache" / "szs.tnf",
    "SH": TDX_ROOT / "T0002" / "hq_cache" / "shs.tnf",
}
TNF_HEADER = 50
TNF_RECORD = 360
SCHEMA_VERSION = 1


def load_tdx_hub():
    spec = importlib.util.spec_from_file_location("oversold_first_board_tdx_hub", TDX_HUB_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load tdx hub: {TDX_HUB_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_names() -> dict[tuple[str, str], str]:
    names: dict[tuple[str, str], str] = {}
    for market, path in TNF_FILES.items():
        if not path.is_file():
            continue
        raw = path.read_bytes()
        for offset in range(TNF_HEADER, len(raw) - TNF_RECORD + 1, TNF_RECORD):
            record = raw[offset : offset + TNF_RECORD]
            code = record[:6].decode("ascii", errors="ignore")
            if len(code) != 6 or not code.isdigit():
                continue
            name = record[31:80].split(b"\0", 1)[0].decode("gb18030", errors="replace").strip()
            if name:
                names[(market, code)] = name
    return names


def is_a_share_stock(symbol: str) -> bool:
    try:
        code, market = symbol.split(".")
    except ValueError:
        return False
    if len(code) != 6 or not code.isdigit():
        return False
    if market == "SZ":
        return code.startswith(("000", "001", "002", "003", "300", "301"))
    if market == "SH":
        return code.startswith(("600", "601", "603", "605", "688", "689"))
    return False


def limit_percent(code: str) -> float:
    return 0.20 if code.startswith(("300", "301", "688", "689")) else 0.10


def limit_price(previous_close: float, percent: float) -> float:
    multiplier = Decimal("1") + Decimal(str(percent))
    return float((Decimal(str(previous_close)) * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def is_limit_up(previous: dict[str, Any], current: dict[str, Any], code: str) -> bool:
    target = limit_price(float(previous["close"]), limit_percent(code))
    return float(current["close"]) >= target - 0.011 and float(current["high"]) - float(current["close"]) <= 0.011


def rsi_at(closes: list[float], index: int, period: int = 14) -> float | None:
    if index < period:
        return None
    changes = [closes[pos] - closes[pos - 1] for pos in range(index - period + 1, index + 1)]
    gains = sum(max(change, 0.0) for change in changes) / period
    losses = sum(max(-change, 0.0) for change in changes) / period
    if losses == 0:
        return 100.0 if gains > 0 else 50.0
    relative_strength = gains / losses
    return 100.0 - 100.0 / (1.0 + relative_strength)


def evaluate_candidate(rows: list[dict[str, Any]], code: str) -> dict[str, Any] | None:
    if len(rows) < 62:
        return None
    index = len(rows) - 1
    current = rows[index]
    previous = rows[index - 1]
    if not is_limit_up(previous, current, code):
        return None
    prior_limit_count = sum(
        1
        for pos in range(max(1, index - 20), index)
        if is_limit_up(rows[pos - 1], rows[pos], code)
    )
    closes = [float(row["close"]) for row in rows]
    pre_limit_rsi = rsi_at(closes, index - 1)
    prior_window = closes[max(0, index - 60) : index]
    if pre_limit_rsi is None or not prior_window:
        return None
    prior_high = max(prior_window)
    drawdown_pct = (float(previous["close"]) / prior_high - 1.0) * 100.0 if prior_high else 0.0
    if prior_limit_count != 0 or pre_limit_rsi > 35.0 or drawdown_pct > -15.0:
        return None
    volume_base = sum(float(row["volume"]) for row in rows[index - 6 : index - 1]) / 5.0
    volume_ratio = float(current["volume"]) / volume_base if volume_base else 0.0
    return_pct = (float(current["close"]) / float(previous["close"]) - 1.0) * 100.0
    score = min(
        100,
        45
        + int(min(max(35.0 - pre_limit_rsi, 0.0), 25.0) * 0.8)
        + int(min(max(-drawdown_pct - 15.0, 0.0), 35.0) * 0.6)
        + (10 if volume_ratio >= 1.2 else 5),
    )
    return {
        "selection_status": "SIGNAL",
        "score": score,
        "metrics": {
            "date": str(current["date"]),
            "open": round(float(current["open"]), 2),
            "high": round(float(current["high"]), 2),
            "low": round(float(current["low"]), 2),
            "close": round(float(current["close"]), 2),
            "return_pct": round(return_pct, 3),
            "limit_price": limit_price(float(previous["close"]), limit_percent(code)),
            "pre_limit_rsi14": round(pre_limit_rsi, 3),
            "pre_limit_drawdown_60_pct": round(drawdown_pct, 3),
            "prior_limit_up_count_20": prior_limit_count,
            "volume_ratio_5": round(volume_ratio, 4),
            "amount_cny": round(float(current["amount"]), 2),
        },
    }


def build_business_payload(
    candidates: list[dict[str, Any]],
    *,
    latest_trade_date: str,
    universe: dict[str, Any],
    data_source: dict[str, Any],
) -> dict[str, Any]:
    candidates = sorted(candidates, key=lambda item: (-int(item["score"]), str(item["symbol"])))
    candidate_symbols = [str(item["symbol"]) for item in candidates]
    scan_stats = universe.get("scan_stats", {})
    full_market_scan = int(scan_stats.get("latest_trade_date") or 0) > 1000
    return {
        "schema_version": SCHEMA_VERSION,
        "strategy_id": "oversold-first-board-v1",
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "CLEAN_PASS" if full_market_scan else "BLOCKED",
        "selection_status": "SIGNAL" if candidates else "NO_SIGNAL",
        "latest_trade_date": latest_trade_date,
        "data_source": data_source,
        "universe": universe,
        "selection": {"candidate_count": len(candidates), "candidates": candidates},
        "validation": {
            "full_market_scan": full_market_scan,
            "candidate_count_matches": len(candidates) == len(candidate_symbols),
            "unique_stock_candidates": len(candidate_symbols) == len(set(candidate_symbols)),
        },
        "risk_boundary": {
            "decision_scope": "local_tdx_end_of_day_technical_selection",
            "external_event_data": "not_used_in_selection",
            "entry_timing": "not_a_trade_instruction",
            "guaranteed_profit": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Full-market local TDX oversold first-board selector")
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    hub = load_tdx_hub()
    index_path = hub.day_path("999999.SH")
    index_rows = hub.read_records(index_path, hub.DAY_RECORD, hub.parse_day_record, 5)
    if not index_rows:
        print(json.dumps({"status": "BLOCKED", "reason": "missing_local_tdx_index_daily"}, ensure_ascii=False))
        return 2
    latest_trade_date = str(index_rows[-1]["date"])
    names = load_names()
    securities = []
    for (market, code), name in names.items():
        symbol = f"{code}.{market}"
        upper_name = name.upper()
        if is_a_share_stock(symbol) and "ST" not in upper_name and "退" not in name and "\ufffd" not in name:
            securities.append((symbol, code, market, name))
    securities.sort()

    scan_stats = {"missing_day_file": 0, "insufficient_history": 0, "not_latest_trade_date": 0, "latest_trade_date": 0}
    candidates: list[dict[str, Any]] = []
    fingerprint_rows: list[str] = []
    for symbol, code, market, name in securities:
        path = hub.day_path(symbol)
        if not path.is_file():
            scan_stats["missing_day_file"] += 1
            continue
        stat = path.stat()
        fingerprint_rows.append(f"{path}|{stat.st_size}|{stat.st_mtime_ns}")
        rows = hub.read_records(path, hub.DAY_RECORD, hub.parse_day_record, 100)
        if len(rows) < 62:
            scan_stats["insufficient_history"] += 1
            continue
        if str(rows[-1]["date"]) != latest_trade_date:
            scan_stats["not_latest_trade_date"] += 1
            continue
        scan_stats["latest_trade_date"] += 1
        evaluated = evaluate_candidate(rows, code)
        if evaluated is None:
            continue
        evaluated.update({
            "symbol": symbol,
            "code": code,
            "market": market,
            "name": name,
            "source": {"path": str(path), "size": stat.st_size, "sha256": sha256_file(path)},
        })
        candidates.append(evaluated)

    candidates.sort(key=lambda item: (-int(item["score"]), str(item["symbol"])))
    candidates = candidates[: max(args.top, 0)]
    source_snapshot = hashlib.sha256("\n".join(sorted(fingerprint_rows)).encode("utf-8")).hexdigest()
    data_source = {
        "type": "local_tdx_raw_daily",
        "root": str(TDX_ROOT),
        "index_path": str(index_path),
        "index_sha256": sha256_file(index_path),
        "tnf_files": {
            market: {"path": str(path), "sha256": sha256_file(path)}
            for market, path in TNF_FILES.items()
            if path.is_file()
        },
        "source_snapshot_sha256": source_snapshot,
    }
    universe = {"eligible_security_records": len(securities), "scan_stats": scan_stats}
    payload = build_business_payload(candidates, latest_trade_date=latest_trade_date, universe=universe, data_source=data_source)
    REPORTS.mkdir(parents=True, exist_ok=True)
    output = Path(args.output).resolve() if args.output else REPORTS / f"oversold-first-board-{latest_trade_date}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_output = REPORTS / "oversold-first-board-latest.json"
    latest_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "status": payload["status"],
        "strategy_id": payload["strategy_id"],
        "selection_status": payload["selection_status"],
        "latest_trade_date": latest_trade_date,
        "candidate_count": len(candidates),
        "report": str(output),
        "latest_report": str(latest_output),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
