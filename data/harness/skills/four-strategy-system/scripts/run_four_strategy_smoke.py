#!/usr/bin/env python3
"""Deterministic four-strategy A-share scanner over local TDX daily data."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import json
import struct
from datetime import datetime
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TDX_ROOT = Path(r"C:\new_tdx_mock")
REPORT = SKILL_ROOT / "reports" / "four-strategy-current.json"
MARKETS = ("sh", "sz", "bj")


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def read_day(path: Path) -> list[dict]:
    raw = path.read_bytes()
    if len(raw) < 120 * 32 or len(raw) % 32:
        return []
    rows = []
    for offset in range(max(0, len(raw) - 260 * 32), len(raw), 32):
        date, op, high, low, close, amount, volume, _ = struct.unpack("<IIIIIfII", raw[offset:offset + 32])
        if not date or not close:
            continue
        rows.append({
            "date": str(date),
            "open": op / 100,
            "high": high / 100,
            "low": low / 100,
            "close": close / 100,
            "amount": float(amount),
            "volume": int(volume),
        })
    return rows


def evaluate(path: Path) -> list[dict]:
    rows = read_day(path)
    if len(rows) < 120:
        return []
    closes = [row["close"] for row in rows]
    volumes = [row["volume"] for row in rows]
    latest = rows[-1]
    ma5, ma10, ma20, ma60 = (mean(closes[-n:]) for n in (5, 10, 20, 60))
    vol5 = mean(volumes[-5:])
    vol20 = mean(volumes[-20:]) or 1
    low20, low60 = min(closes[-20:]), min(closes[-60:])
    high20_prev = max(closes[-21:-1])
    momentum3 = latest["close"] / closes[-4] - 1
    momentum5 = latest["close"] / closes[-6] - 1
    drawdown20 = min(closes[-20:]) / max(closes[-60:]) - 1
    day_return = latest["close"] / closes[-2] - 1
    volume_ratio = vol5 / vol20
    common = {
        "symbol": path.stem[2:].upper() + "." + path.stem[:2].upper(),
        "trade_date": latest["date"],
        "close": latest["close"],
        "source_path": str(path),
        "ma5": round(ma5, 4),
        "ma10": round(ma10, 4),
        "ma20": round(ma20, 4),
        "ma60": round(ma60, 4),
        "volume_ratio_5_20": round(volume_ratio, 4),
    }
    signals = []
    definitions = {
        "起浪坑": (
            drawdown20 <= -0.15 and latest["close"] <= low60 * 1.18 and latest["close"] > ma5 and momentum3 > 0,
            round(momentum3 * 100 - abs(latest["close"] / low60 - 1) * 20, 4),
            round(low20, 4),
        ),
        "临空": (
            latest["close"] >= high20_prev and ma5 > ma10 > ma20 and volume_ratio >= 1.2,
            round((latest["close"] / high20_prev - 1) * 100 + volume_ratio, 4),
            round(ma20, 4),
        ),
        "接体": (
            momentum5 >= 0.08 and closes[-2] < closes[-3] and latest["close"] > closes[-2] and latest["close"] >= ma10,
            round(momentum5 * 100 + day_return * 100, 4),
            round(ma10, 4),
        ),
        "伏虎": (
            ma20 > ma60 and abs(latest["close"] / ma20 - 1) <= 0.03 and latest["close"] > closes[-2] and low20 > ma60 * 0.95,
            round((ma20 / ma60 - 1) * 100 - abs(latest["close"] / ma20 - 1) * 100, 4),
            round(min(ma20, low20), 4),
        ),
    }
    for name, (matched, score, invalidation) in definitions.items():
        if matched:
            signals.append({**common, "strategy": name, "score": score, "invalidation": invalidation})
    return signals


def main() -> int:
    files = []
    for market in MARKETS:
        directory = TDX_ROOT / "vipdoc" / market / "lday"
        if directory.is_dir():
            files.extend(sorted(directory.glob(f"{market}[03689]*.day")))
    results = {name: [] for name in ("起浪坑", "临空", "接体", "伏虎")}
    scanned = 0
    latest_trade_date = ""
    for path in files:
        signals = evaluate(path)
        if not signals:
            continue
        scanned += 1
        for signal in signals:
            latest_trade_date = max(latest_trade_date, signal["trade_date"])
            results[signal["strategy"]].append(signal)
    for name in results:
        results[name] = sorted(results[name], key=lambda row: row["score"], reverse=True)[:10]
    payload = {
        "schema": "FOUR_STRATEGY_EXECUTION_V1",
        "status": "CLEAN_PASS",
        "signal_state": "SIGNAL" if any(results.values()) else "NO_SIGNAL",
        "executed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "data_source": "LOCAL_TDX_DAILY",
        "tdx_root": str(TDX_ROOT),
        "file_count": len(files),
        "files_with_signal": scanned,
        "latest_trade_date": latest_trade_date,
        "strategy_count": 4,
        "definitions": {
            "起浪坑": "60日回撤至少15%，距60日低点不超过18%，收盘重上MA5且3日动量转正",
            "临空": "收盘突破前20日高点，MA5>MA10>MA20，5日对20日量比至少1.2",
            "接体": "5日涨幅至少8%，前一日回落，当日转强且收盘不低于MA10",
            "伏虎": "MA20>MA60，收盘贴近MA20正负3%，当日转强且20日低点未有效跌破MA60",
        },
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    readback = json.loads(REPORT.read_text(encoding="utf-8"))
    data = REPORT.read_bytes()
    summary = {
        "status": readback["status"],
        "signal_state": readback["signal_state"],
        "report": str(REPORT),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "file_count": readback["file_count"],
        "latest_trade_date": readback["latest_trade_date"],
        "strategy_count": readback["strategy_count"],
        "signal_counts": {name: len(rows) for name, rows in readback["results"].items()},
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
