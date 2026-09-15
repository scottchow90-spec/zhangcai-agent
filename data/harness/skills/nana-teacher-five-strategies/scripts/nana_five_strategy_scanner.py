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
import math
import os
import re
import statistics
import struct
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from nana_freshness_guard import (
    build_freshness_guard,
    canonical_sha256,
    normalize_trade_date,
    sha256_file,
)


TDX_ROOT = Path(r"C:\new_tdx_mock")
DAY = struct.Struct("<IIIIIfII")
TNF_HEADER = 50
TNF_RECORD = 360
TNF_NAME_OFFSET = 31
TNF_NAME_SIZE = 18
MARKETS = {
    "SH": (TDX_ROOT / "vipdoc" / "sh" / "lday", TDX_ROOT / "T0002" / "hq_cache" / "shs.tnf"),
    "SZ": (TDX_ROOT / "vipdoc" / "sz" / "lday", TDX_ROOT / "T0002" / "hq_cache" / "szs.tnf"),
    "BJ": (TDX_ROOT / "vipdoc" / "bj" / "lday", TDX_ROOT / "T0002" / "hq_cache" / "bjs.tnf"),
}
STRATEGIES = ["元宝藏金", "地极破晓", "游龙吸水", "负阴抱阳", "黄金双响"]


def decode(raw: bytes) -> str:
    return raw.split(b"\0", 1)[0].decode("gbk", errors="ignore").strip()


def load_names(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    data = path.read_bytes()
    for offset in range(TNF_HEADER, len(data) - TNF_RECORD + 1, TNF_RECORD):
        row = data[offset : offset + TNF_RECORD]
        code = decode(row[:6])
        name = decode(row[TNF_NAME_OFFSET : TNF_NAME_OFFSET + TNF_NAME_SIZE])
        if len(code) == 6 and code.isdigit() and name:
            result[code] = name
    return result


def valid_code(market: str, code: str) -> bool:
    if market == "SH":
        return code.startswith(("600", "601", "603", "605", "688", "689"))
    if market == "SZ":
        return code.startswith(("000", "001", "002", "003", "300", "301"))
    return code.startswith(("4", "8", "9"))


def load_day(path: Path, limit: int = 320) -> dict[str, Any]:
    stat = path.stat()
    count = stat.st_size // DAY.size
    take = min(count, limit)
    if take <= 0:
        return {}
    with path.open("rb") as handle:
        handle.seek((count - take) * DAY.size)
        data = handle.read(take * DAY.size)
    fields: dict[str, list] = {name: [] for name in ("date", "open", "high", "low", "close", "amount", "volume")}
    for offset in range(0, len(data), DAY.size):
        raw = data[offset : offset + DAY.size]
        if len(raw) != DAY.size:
            continue
        date, open_i, high_i, low_i, close_i, amount, volume, _ = DAY.unpack(raw)
        if close_i <= 0 or len(str(date)) != 8:
            continue
        fields["date"].append(str(date))
        fields["open"].append(open_i / 100.0)
        fields["high"].append(high_i / 100.0)
        fields["low"].append(low_i / 100.0)
        fields["close"].append(close_i / 100.0)
        fields["amount"].append(float(amount))
        fields["volume"].append(float(volume))
    fields["_input_sha256"] = hashlib.sha256(data).hexdigest()
    fields["_file_size"] = stat.st_size
    fields["_mtime_ns"] = stat.st_mtime_ns
    fields["_record_count"] = count
    return fields


def infer_latest_trade_date(universe: list[tuple[str, str, str, Path]]) -> str:
    counts: Counter[str] = Counter()
    for _market, _code, _name, path in universe:
        try:
            if path.stat().st_size < DAY.size:
                continue
            with path.open("rb") as handle:
                handle.seek(-DAY.size, 2)
                raw = handle.read(DAY.size)
            date = str(DAY.unpack(raw)[0])
            if len(date) == 8 and date.isdigit():
                counts[date] += 1
        except (OSError, struct.error):
            continue
    if not counts:
        return ""
    coverage_floor = max(1000, int(len(universe) * 0.40))
    sufficiently_covered = [date for date, count in counts.items() if count >= coverage_floor]
    return max(sufficiently_covered) if sufficiently_covered else counts.most_common(1)[0][0]


def append_quote(rows: dict[str, list], quote: dict[str, Any], target_date: str) -> None:
    if not rows or rows["date"][-1] >= target_date:
        return
    required = ("open", "high", "low", "close", "amount", "volume", "preclose")
    if any(quote.get(key) is None for key in required):
        return
    if abs(float(rows["close"][-1]) - float(quote["preclose"])) > max(0.03, float(quote["preclose"]) * 0.005):
        return
    rows["date"].append(target_date)
    for key in ("open", "high", "low", "close", "amount", "volume"):
        rows[key].append(float(quote[key]))


def rolling_mean(values: list[float], n: int) -> list[float]:
    out = [math.nan] * len(values)
    total = 0.0
    for i, value in enumerate(values):
        total += value
        if i >= n:
            total -= values[i - n]
        if i >= n - 1:
            out[i] = total / n
    return out


def ema(values: list[float], n: int) -> list[float]:
    alpha = 2.0 / (n + 1)
    out = [values[0]]
    for value in values[1:]:
        out.append(alpha * value + (1 - alpha) * out[-1])
    return out


def tdx_sma(values: list[float], n: int, m: int) -> list[float]:
    out = [values[0]]
    for value in values[1:]:
        out.append((m * value + (n - m) * out[-1]) / n)
    return out


def precompute(rows: dict[str, list]) -> dict[str, list[float]]:
    close = rows["close"]
    low = rows["low"]
    high = rows["high"]
    ma5 = rolling_mean(close, 5)
    ma10 = rolling_mean(close, 10)
    ma20 = rolling_mean(close, 20)
    vma5 = rolling_mean(rows["volume"], 5)
    vma10 = rolling_mean(rows["volume"], 10)
    vma20 = rolling_mean(rows["volume"], 20)
    e12 = ema(close, 12)
    e26 = ema(close, 26)
    dif = [a - b for a, b in zip(e12, e26)]
    dea = ema(dif, 9)
    rsv = []
    for i, value in enumerate(close):
        start = max(0, i - 8)
        lo = min(low[start : i + 1])
        hi = max(high[start : i + 1])
        rsv.append((value - lo) / (hi - lo) * 100 if hi > lo else 50.0)
    k = tdx_sma(rsv, 3, 1)
    d = tdx_sma(k, 3, 1)
    return {"ma5": ma5, "ma10": ma10, "ma20": ma20, "vma5": vma5, "vma10": vma10, "vma20": vma20, "dif": dif, "dea": dea, "k": k, "d": d}


def pct(rows: dict[str, list], i: int) -> float:
    prev = float(rows["close"][i - 1])
    return (float(rows["close"][i]) / prev - 1) if prev else 0.0


def is_limit_like(rows: dict[str, list], i: int) -> bool:
    return i > 0 and pct(rows, i) >= 0.095 and float(rows["close"][i]) >= float(rows["high"][i]) - 0.011


def common_ok(name: str, rows: dict[str, list], i: int, min_price: float) -> bool:
    if i < 120 or re.search(r"(?:\*?ST|退市|^N|^C)", name, re.I):
        return False
    return float(rows["close"][i]) > min_price and float(rows["amount"][i]) >= 30_000_000


def base_record(strategy: str, variant: str, rows: dict[str, list], calc: dict[str, list], i: int, extra: dict[str, Any]) -> dict[str, Any]:
    record = {
        "strategy": strategy,
        "variant": variant,
        "signal_date": rows["date"][i],
        "close": round(float(rows["close"][i]), 2),
        "pct_change": round(pct(rows, i) * 100, 2),
        "amount_yi": round(float(rows["amount"][i]) / 100_000_000, 2),
        "ma5": round(float(calc["ma5"][i]), 2),
        "ma10": round(float(calc["ma10"][i]), 2),
        "ma20": round(float(calc["ma20"][i]), 2),
    }
    record.update(extra)
    entry = float(rows["close"][i])
    for days in (1, 3, 5):
        record[f"forward_{days}d_pct"] = round((float(rows["close"][i + days]) / entry - 1) * 100, 2) if i + days < len(rows["close"]) else None
    if i + 5 < len(rows["close"]):
        record["max_drawdown_5d_pct"] = round((min(float(value) for value in rows["low"][i + 1 : i + 6]) / entry - 1) * 100, 2)
    else:
        record["max_drawdown_5d_pct"] = None
    return record


def scaled_score(value: float | None, low: float, high: float, points: float) -> float:
    if value is None or high <= low:
        return 0.0
    return max(0.0, min(points, (float(value) - low) / (high - low) * points))


def apply_quality_score(item: dict[str, Any], metrics: dict[str, Any]) -> None:
    three = metrics.get("forward_3d", {})
    five = metrics.get("forward_5d", {})
    history_score = (
        scaled_score(three.get("average_pct"), -2.0, 2.0, 8.0)
        + scaled_score(three.get("win_rate_pct"), 30.0, 60.0, 7.0)
        + scaled_score(five.get("average_pct"), -2.0, 2.0, 8.0)
        + scaled_score(five.get("win_rate_pct"), 30.0, 60.0, 7.0)
    )

    close = float(item["close"])
    ma5 = float(item["ma5"])
    ma10 = float(item["ma10"])
    ma20 = float(item["ma20"])
    pct_change = float(item["pct_change"])
    trend_score = (
        (7.0 if close > ma5 else 0.0)
        + (6.0 if ma5 > ma10 else 0.0)
        + (5.0 if ma10 >= ma20 else 0.0)
        + (4.0 if close > ma20 else 0.0)
        + (3.0 if 0.0 < pct_change <= 7.0 else 0.0)
    )

    amount_yi = max(float(item["amount_yi"]), 0.3)
    liquidity_score = max(8.0, min(20.0, 8.0 + 6.0 * math.log10(amount_yi / 0.3)))

    invalidation = float(item.get("invalidation") or 0.0)
    risk_buffer_pct = (close / invalidation - 1.0) * 100.0 if invalidation > 0 else -1.0
    if risk_buffer_pct <= 0:
        risk_score = 0.0
    elif risk_buffer_pct <= 3.0:
        risk_score = 4.0 + risk_buffer_pct * 2.0
    elif risk_buffer_pct <= 10.0:
        risk_score = 10.0 + (risk_buffer_pct - 3.0) * 5.0 / 7.0
    elif risk_buffer_pct <= 20.0:
        risk_score = 15.0 - (risk_buffer_pct - 10.0) * 0.5
    else:
        risk_score = max(0.0, 10.0 - (risk_buffer_pct - 20.0) * 0.5)

    total = round(10.0 + history_score + trend_score + liquidity_score + risk_score, 1)
    item.update(
        {
            "quality_score": total,
            "quality_tier": "优先复核" if total >= 75.0 else "通过质量门槛" if total >= 60.0 else "观察",
            "quality_gate_pass": total >= 60.0,
            "strategy_history_score": round(history_score, 1),
            "trend_score": round(trend_score, 1),
            "liquidity_score": round(liquidity_score, 1),
            "risk_buffer_score": round(risk_score, 1),
            "risk_buffer_pct": round(risk_buffer_pct, 2),
        }
    )


def scan_ybzj(name: str, rows: dict[str, list], c: dict[str, list], i: int) -> dict[str, Any] | None:
    if not common_ok(name, rows, i, 3) or not (c["ma5"][i] > c["ma10"][i] >= c["ma20"][i]):
        return None
    volume = rows["volume"]
    for offset in range(3, 8):
        base = i - offset
        midpoint = (rows["open"][base] + rows["close"][base]) / 2
        pull_lows = rows["low"][base + 1 : i]
        if is_limit_like(rows, base) and pull_lows and min(pull_lows) >= midpoint and rows["close"][i] > rows["high"][i - 1] and rows["close"][i] > rows["open"][i] and volume[i] > c["vma5"][i] * 1.20:
            return base_record("元宝藏金", "阳线元宝", rows, c, i, {"base_date": rows["date"][base], "base_midpoint": round(midpoint, 2), "invalidation": round(min(pull_lows) * 0.97, 2), "evidence": f"涨停基柱后{offset-1}日不破实体中轴，今日放量突破"})
    for offset in range(3, 6):
        base = i - offset
        body_drop = (rows["open"][base] - rows["close"][base]) / rows["open"][base]
        middle = range(base + 1, i)
        contained = middle and max(max(rows["open"][j], rows["close"][j]) for j in middle) <= rows["open"][base] and min(min(rows["open"][j], rows["close"][j]) for j in middle) >= rows["close"][base]
        base_volume_ok = volume[base] > c["vma10"][base] * 1.20 if not math.isnan(c["vma10"][base]) else False
        if rows["close"][base] < rows["open"][base] and body_drop > 0.05 and base_volume_ok and contained and rows["close"][i] > rows["open"][base] and rows["close"][i] > rows["open"][i] and volume[i] > c["vma5"][i] * 1.20:
            return base_record("元宝藏金", "阴线元宝", rows, c, i, {"base_date": rows["date"][base], "base_open": round(rows["open"][base], 2), "invalidation": round(min(rows["low"][base : i + 1]) * 0.97, 2), "evidence": f"放量大阴后{offset-1}日箱体沉淀，今日阳线过阴顶"})
    return None


def scan_dlq(name: str, rows: dict[str, list], c: dict[str, list], i: int) -> dict[str, Any] | None:
    if not common_ok(name, rows, i, 2) or i < 128:
        return None
    low_count = 0
    narrow_count = 0
    for j in range(i - 7, i + 1):
        if rows["volume"][j] < c["vma20"][j] * 0.60:
            low_count += 1
        if max(rows["high"][j - 4 : j + 1]) / min(rows["low"][j - 4 : j + 1]) < 1.08:
            narrow_count += 1
    group = low_count >= 5 and narrow_count >= 4
    nolow = rows["low"][i] > min(rows["low"][i - 60 : i]) * 0.98
    maup = c["ma10"][i] >= c["ma10"][i - 3] and rows["close"][i] > c["ma5"][i]
    macd_ok = c["dif"][i] > c["dea"][i]
    kdj_ok = c["k"][i] > c["d"][i]
    boll_ok = rows["close"][i] > c["ma20"][i]
    confirm_score = sum((macd_ok, kdj_ok, boll_ok))
    breakout = rows["close"][i] > rows["open"][i] and pct(rows, i) > 0.03 and rows["volume"][i] > c["vma5"][i] * 1.20 and boll_ok
    cross5 = rows["close"][i] > c["ma5"][i] and rows["close"][i - 1] <= c["ma5"][i - 1]
    if group and nolow and maup and (breakout or (cross5 and confirm_score >= 2)):
        return base_record("地极破晓", "地量群放量确认" if breakout else "地量群均线确认", rows, c, i, {"low_volume_days": low_count, "narrow_days": narrow_count, "confirm_score": confirm_score, "invalidation": round(min(rows["low"][i - 8 : i + 1]) * 0.97, 2), "evidence": f"8日内低量{low_count}日、窄幅{narrow_count}日，确认分{confirm_score}"})
    return None


def scan_ylxs(name: str, rows: dict[str, list], c: dict[str, list], i: int) -> dict[str, Any] | None:
    if not common_ok(name, rows, i, 3) or not (c["ma10"][i] > c["ma20"][i] >= c["ma20"][i - 3] and rows["close"][i] > c["ma20"][i]):
        return None
    if not (rows["volume"][i] < c["vma5"][i] * 0.85 and rows["close"][i] > rows["open"][i] and rows["close"][i] > rows["close"][i - 1] and rows["close"][i] > c["ma10"][i]):
        return None
    macd_ok = c["dif"][i] > c["dea"][i]
    cross5 = rows["close"][i] > c["ma5"][i] and rows["close"][i - 1] <= c["ma5"][i - 1]
    if not (macd_ok or cross5):
        return None
    for offset in range(3, 11):
        gap = i - offset
        gap_up = rows["low"][gap] > rows["high"][gap - 1] * 1.005 and pct(rows, gap) > 0.03
        support = rows["low"][i] <= rows["low"][gap] * 1.03 and rows["low"][i] >= rows["high"][gap - 1] * 0.98 and rows["close"][i] >= rows["high"][gap - 1]
        if gap_up and support:
            return base_record("游龙吸水", "缺口缩量回踩", rows, c, i, {"gap_date": rows["date"][gap], "gap_lower": round(rows["high"][gap - 1], 2), "gap_upper": round(rows["low"][gap], 2), "invalidation": round(rows["high"][gap - 1] * 0.95, 2), "evidence": f"{offset}日前向上缺口，今日缩量回踩缺口并收阳"})
    return None


def scan_fyby(name: str, rows: dict[str, list], c: dict[str, list], i: int) -> dict[str, Any] | None:
    if not common_ok(name, rows, i, 3) or not (c["ma5"][i] > c["ma10"][i] >= c["ma20"][i]):
        return None
    fake = i - 1
    pre = i - 2
    avg_price = rows["amount"][fake] / rows["volume"][fake] if rows["volume"][fake] else rows["close"][fake]
    visible = rows["open"][fake] > rows["close"][pre] * 1.01 and rows["close"][fake] < rows["open"][fake] and rows["close"][fake] > rows["close"][pre] and avg_price > rows["close"][pre]
    hidden = rows["open"][fake] > rows["close"][pre] * 1.01 and rows["close"][fake] < rows["open"][fake] and rows["close"][fake] <= rows["close"][pre] and avg_price > rows["close"][pre]
    safe_volume = rows["volume"][fake] > rows["volume"][pre] * 1.05 and rows["volume"][fake] < c["vma20"][fake] * 3
    fake_ok = (visible or hidden) and safe_volume and (rows["close"][fake] > c["ma5"][fake] or c["ma5"][fake] > c["ma10"][fake])
    stable = rows["close"][i] > rows["open"][i] and rows["volume"][i] < rows["volume"][fake] * 0.70 and rows["close"][i] > rows["close"][pre]
    reclaim = rows["close"][i] > rows["open"][fake] and rows["close"][i] > rows["open"][i] and rows["volume"][i] > rows["volume"][fake] * 0.80
    technical = c["dif"][i] > c["dea"][i] or c["k"][i] > c["d"][i]
    if fake_ok and (stable or reclaim) and rows["low"][i] > rows["low"][fake] * 0.97 and technical:
        return base_record("负阴抱阳", "显性次日确认" if visible else "隐性次日确认", rows, c, i, {"fake_date": rows["date"][fake], "fake_open": round(rows["open"][fake], 2), "avg_price": round(avg_price, 2), "confirm_type": "反包" if reclaim else "缩量企稳", "invalidation": round(rows["low"][fake] * 0.97, 2), "evidence": f"假阴均价高于昨收，次日{'反包' if reclaim else '缩量企稳'}"})
    return None


def scan_hjsx(name: str, rows: dict[str, list], c: dict[str, list], i: int) -> dict[str, Any] | None:
    if not common_ok(name, rows, i, 3) or not (c["ma5"][i] > c["ma10"][i] >= c["ma20"][i] and rows["close"][i] > c["ma20"][i]):
        return None
    second_big = rows["close"][i] > rows["open"][i] and pct(rows, i) >= 0.05
    if not second_big:
        return None
    for offset in range(3, 8):
        first = i - offset
        first_big = rows["close"][first] > rows["open"][first] and pct(rows, first) >= 0.05 and rows["volume"][first] > c["vma5"][first] * 1.30
        middle = list(range(first + 1, i))
        if not first_big or not middle:
            continue
        volume_shrink = sum(rows["volume"][j] for j in middle) / len(middle) < rows["volume"][first] * 0.70
        structure_ok = min(rows["low"][j] for j in middle) >= rows["open"][first] * 0.97 and rows["close"][i] > max(rows["high"][j] for j in middle)
        second_volume = rows["volume"][i] >= rows["volume"][first] * 0.80
        if volume_shrink and structure_ok and second_volume:
            first_limit = is_limit_like(rows, first)
            second_limit = is_limit_like(rows, i)
            if first_limit and second_limit:
                variant = "涨停+涨停"
            elif first_limit:
                variant = "涨停+大阳"
            else:
                variant = "大阳+大阳"
            return base_record("黄金双响", variant, rows, c, i, {"first_shot_date": rows["date"][first], "interval_days": offset - 1, "first_volume_ratio": round(rows["volume"][first] / c["vma5"][first], 2), "second_vs_first_volume": round(rows["volume"][i] / rows["volume"][first], 2), "invalidation": round(min(rows["low"][first : i + 1]) * 0.97, 2), "evidence": f"前炮后{offset-1}日缩量整理，后炮量为前炮{rows['volume'][i]/rows['volume'][first]:.2f}倍并过平台"})
    return None


SCANNERS = [scan_ybzj, scan_dlq, scan_ylxs, scan_fyby, scan_hjsx]


CSV_FIELDS = [
    "strategy",
    "signal_date",
    "symbol",
    "name",
    "variant",
    "quality_score",
    "quality_tier",
    "quality_gate_pass",
    "strategy_history_score",
    "trend_score",
    "liquidity_score",
    "risk_buffer_score",
    "risk_buffer_pct",
    "close",
    "pct_change",
    "amount_yi",
    "ma5",
    "ma10",
    "ma20",
    "invalidation",
    "evidence",
]


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def atomic_write_csv(
    path: Path, current: dict[str, list[dict[str, Any]]] | None = None
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8-sig",
        newline="",
        dir=path.parent,
        suffix=".tmp",
        delete=False,
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        if current:
            for strategy in STRATEGIES:
                for item in current[strategy]:
                    writer.writerow({key: item.get(key) for key in writer.fieldnames})
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-date")
    parser.add_argument("--quote-json")
    parser.add_argument("--history-days", type=int, default=60)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    args = parser.parse_args()
    output_json = Path(args.output_json).resolve()
    output_csv = Path(args.output_csv).resolve()
    forced_errors: list[str] = []
    quote_path = Path(args.quote_json).resolve() if args.quote_json else None
    quote_payload: dict[str, Any] | None = None
    if quote_path is not None:
        try:
            loaded = json.loads(quote_path.read_text(encoding="utf-8-sig"))
            if not isinstance(loaded, dict):
                raise TypeError("quote_json_root_not_object")
            quote_payload = loaded
        except Exception as exc:
            quote_payload = {}
            forced_errors.append(f"quote_json_unreadable:{type(exc).__name__}:{exc}")
    quote_date = normalize_trade_date(
        quote_payload.get("trade_date") if quote_payload is not None else ""
    )
    explicit_date = normalize_trade_date(args.target_date)
    if args.target_date and not explicit_date:
        forced_errors.append(f"target_trade_date_invalid:{args.target_date}")
    if quote_payload is not None and not quote_date:
        forced_errors.append("quote_trade_date_missing_or_invalid")
    if explicit_date and quote_date and explicit_date != quote_date:
        forced_errors.append(f"target_quote_trade_date_mismatch:{explicit_date}!={quote_date}")
    requested_date = explicit_date or quote_date

    universe = []
    name_count = 0
    for market, (folder, tnf) in MARKETS.items():
        names = load_names(tnf)
        name_count += len(names)
        for path in sorted(folder.glob(f"{market.lower()}*.day")):
            code = path.stem[-6:]
            if valid_code(market, code) and code in names:
                universe.append((market, code, names[code], path))
    freshness = build_freshness_guard(
        universe=universe,
        requested_trade_date=requested_date,
        quote_payload=quote_payload,
        quote_json_path=quote_path,
        forced_errors=forced_errors,
    )
    target_date = str(freshness.get("requested_trade_date") or requested_date)
    inferred_target_date = not bool(explicit_date or quote_date)
    if freshness.get("status") != "PASS":
        blocked = {
            "status": "BLOCKED",
            "reason": "FRESHNESS_GATE_BLOCKED",
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "target_trade_date": target_date,
            "target_trade_date_inferred": inferred_target_date,
            "universe_files": len(universe),
            "name_records": name_count,
            "freshness_gate": freshness,
            "strategy_summary": {},
            "risk_boundary": "数据新鲜度未通过，禁止生成或沿用选股结果。",
        }
        atomic_write_json(output_json, blocked)
        atomic_write_csv(output_csv)
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "reason": "FRESHNESS_GATE_BLOCKED",
                    "target_trade_date": target_date,
                    "errors": freshness.get("errors", []),
                    "output_json": str(output_json),
                    "output_csv": str(output_csv),
                },
                ensure_ascii=False,
            )
        )
        return 2
    quotes = quote_payload.get("quotes", {}) if quote_payload is not None else {}
    use_quote_append = freshness.get("selected_data_route") == "validated_quote_append"
    current: dict[str, list[dict[str, Any]]] = {name: [] for name in STRATEGIES}
    history: dict[str, list[dict[str, Any]]] = {name: [] for name in STRATEGIES}
    data_dates: Counter[str] = Counter()
    input_digest = hashlib.sha256()
    input_digest.update(canonical_sha256(freshness).encode("ascii"))
    bound_input_symbols = 0
    scanned = 0
    target_covered = 0
    for index, (market, code, name, path) in enumerate(universe, 1):
        if index % 800 == 0:
            print(f"SCAN_PROGRESS {index}/{len(universe)}", flush=True)
        rows = load_day(path)
        if not rows or len(rows["date"]) < 125:
            continue
        symbol = f"{code}.{market}"
        if use_quote_append and quote_date == target_date and symbol in quotes:
            append_quote(rows, quotes[symbol], target_date)
        data_dates[rows["date"][-1]] += 1
        if not target_date:
            continue
        if rows["date"][-1] != target_date:
            continue
        target_covered += 1
        input_digest.update(
            (
                f"{symbol}\0{rows['_input_sha256']}\0{rows['_file_size']}\0"
                f"{rows['_record_count']}\0{rows['date'][-1]}\n"
            ).encode("utf-8")
        )
        bound_input_symbols += 1
        calc = precompute(rows)
        scanned += 1
        start = max(120, len(rows["date"]) - args.history_days)
        for i in range(start, len(rows["date"])):
            for scanner in SCANNERS:
                signal = scanner(name, rows, calc, i)
                if not signal:
                    continue
                signal.update({"market": market, "code": code, "symbol": symbol, "name": name, "data_path": str(path)})
                history[signal["strategy"]].append(signal)
                if i == len(rows["date"]) - 1:
                    current[signal["strategy"]].append(signal)
    for strategy in STRATEGIES:
        history[strategy].sort(key=lambda item: (item["signal_date"], item["code"]), reverse=True)
    strategy_metrics: dict[str, tuple[Counter, dict[str, Any]]] = {}
    for strategy in STRATEGIES:
        dates = Counter(item["signal_date"] for item in history[strategy])
        metrics = {}
        for days in (1, 3, 5):
            values = [float(item[f"forward_{days}d_pct"]) for item in history[strategy] if item.get(f"forward_{days}d_pct") is not None]
            metrics[f"forward_{days}d"] = {
                "evaluated": len(values),
                "average_pct": round(statistics.fmean(values), 3) if values else None,
                "median_pct": round(statistics.median(values), 3) if values else None,
                "win_rate_pct": round(sum(value > 0 for value in values) / len(values) * 100, 2) if values else None,
            }
        drawdowns = [float(item["max_drawdown_5d_pct"]) for item in history[strategy] if item.get("max_drawdown_5d_pct") is not None]
        metrics["max_drawdown_5d"] = {"evaluated": len(drawdowns), "average_pct": round(statistics.fmean(drawdowns), 3) if drawdowns else None, "worst_pct": round(min(drawdowns), 3) if drawdowns else None}
        strategy_metrics[strategy] = (dates, metrics)

    summary = {}
    for strategy in STRATEGIES:
        dates, metrics = strategy_metrics[strategy]
        for item in current[strategy]:
            apply_quality_score(item, metrics)
        current[strategy].sort(key=lambda item: (-item["quality_score"], -item["amount_yi"], item["code"]))
        quality_candidates = [item for item in current[strategy] if item["quality_gate_pass"]]
        summary[strategy] = {
            "current_count": len(current[strategy]),
            "quality_pass_count": len(quality_candidates),
            "history_signal_count": len(history[strategy]),
            "history_distinct_symbols": len({item["symbol"] for item in history[strategy]}),
            "recent_signal_dates": dates.most_common(10),
            "backtest_metrics": metrics,
            "current_top20": current[strategy][:20],
            "quality_top20": quality_candidates[:20],
            "recent_history_top20": history[strategy][:20],
        }
    required_coverage = int(
        freshness.get("local_data", {}).get("required_target_coverage") or 4000
    )
    scan_errors: list[str] = []
    if scanned < required_coverage:
        scan_errors.append(f"scanned_symbol_coverage_insufficient:{scanned}<{required_coverage}")
    if bound_input_symbols != scanned:
        scan_errors.append(f"input_binding_count_mismatch:{bound_input_symbols}!={scanned}")
    for strategy in STRATEGIES:
        if summary[strategy]["history_signal_count"] <= 0:
            scan_errors.append(f"strategy_history_empty:{strategy}")
    status = "PASS" if not scan_errors else "BLOCKED"
    result = {
        "status": status,
        "reason": None if not scan_errors else "SCAN_COMPLETENESS_BLOCKED",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "target_trade_date": target_date,
        "target_trade_date_inferred": inferred_target_date,
        "data_source": "C:\\new_tdx_mock vipdoc + validated current quote append" if use_quote_append else "C:\\new_tdx_mock vipdoc",
        "quote_source": quote_payload.get("source") if quote_payload is not None else None,
        "universe_files": len(universe),
        "target_date_covered": target_covered,
        "scanned_symbols": scanned,
        "name_records": name_count,
        "data_date_distribution_top10": data_dates.most_common(10),
        "freshness_gate": freshness,
        "input_fingerprint": {
            "schema": "nana-scan-input/v2",
            "algorithm": "sha256",
            "sha256": input_digest.hexdigest(),
            "bound_symbol_count": bound_input_symbols,
            "scanner_sha256": sha256_file(Path(__file__).resolve()),
            "freshness_guard_sha256": sha256_file(
                Path(__file__).resolve().with_name("nana_freshness_guard.py")
            ),
            "quote_file": freshness.get("quote_file"),
            "quote_json_sha256": freshness.get("quote_json_sha256"),
        },
        "quality_model": {
            "schema": "nana-technical-quality/v1",
            "score_range": [0, 100],
            "gate_threshold": 60,
            "priority_threshold": 75,
            "components": {
                "formula_match": 10,
                "strategy_3d_5d_history": 30,
                "trend_structure": 25,
                "liquidity": 20,
                "invalidation_distance": 15,
            },
            "scope": "仅用于原公式命中后的技术候选排序，不代表基本面质量或收益保证。",
        },
        "strategy_summary": summary,
        "errors": scan_errors,
        "risk_boundary": "候选为量价形态信号，不是收益承诺；需按工作流核对公告、板块和可交易性。",
    }
    atomic_write_json(output_json, result)
    atomic_write_csv(output_csv, current if status == "PASS" else None)
    print(json.dumps({"status": status, "target_trade_date": target_date, "scanned_symbols": scanned, "current_counts": {name: len(current[name]) for name in STRATEGIES}, "quality_pass_counts": {name: sum(bool(item["quality_gate_pass"]) for item in current[name]) for name in STRATEGIES}, "history_counts": {name: len(history[name]) for name in STRATEGIES}, "errors": scan_errors, "output_json": str(output_json), "output_csv": str(output_csv)}, ensure_ascii=False))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
