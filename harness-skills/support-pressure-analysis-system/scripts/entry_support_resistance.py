#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
support-resistance-analysis-system v3.0 - Deepened 5-method framework.
Optimal implementation of:
  1. Elliott Wave (wave pattern + rule validation)
  2. Chan Structure (central zones + divergence)
  3. Fibonacci (multi-swing cluster analysis)
  4. Gann (square of 9 + multi-angle + time cycles)
  5. Wyckoff (Volume Spread Analysis + spring/upthrust + effort/result)

Combined: weighted multi-method scoring + signal quality matrix + scenario ranking.

Educational/research use only. Not investment advice.
"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import json, math, os, struct, sys, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_data_root, resolve_tdx_root

# === Config ===
WORKSPACE = resolve_data_root()


def _resolve_tdx_root():
    """Return the selected installation's vipdoc, never a guessed sibling install."""
    env_vipdoc = os.environ.get("TDX_VIPDOC_ROOT")
    if env_vipdoc:
        return Path(env_vipdoc).expanduser().resolve()
    return resolve_tdx_root() / "vipdoc"


# 模块级常量: TDX 根目录 (可被环境变量 TDX_VIPDOC_ROOT 覆盖)
TDX_ROOT = _resolve_tdx_root()
TDX_PATH = TDX_ROOT / "sh" / "lday" / "sh000001.day"  # 默认路径, fetch 时再按标的动态拼

RUN_ID = os.environ.get("SKILL_FULLFLOW_RUN_ID", "manual_run")
OUTPUT_DIR = resolve_data_root() / "reports" / RUN_ID / "support-resistance-analysis"
CST = timezone(timedelta(hours=8))
NAME_CN = "支撑压力分析系统"
SKILL = "support-pressure-analysis-system"
SYMBOL = "000001.SH"
SYMBOL_NAME = "上证指数"
KLINE_LIMIT = 120
TIMEOUT_S = 15

# ============================================================
# Section 1: Data acquisition (3-level fallback)
# ============================================================
def from_eastmoney():
    url = (
        "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        "?fields1=f1,f2,f3,f4,f5,f6"
        "&fields2=f51,f52,f53,f54,f55,f56,f57"
        "&klt=101&fqt=1&secid=1.000001"
        "&end=20500101&lmt=" + str(KLINE_LIMIT)
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://quote.eastmoney.com/",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="ignore"))
    return data.get("data", {}).get("klines", []), "eastmoney"

def from_sina():
    url = (
        "https://quotes.sina.cn/cn/api/json_v2.php"
        "=/CN_MarketDataService.getKLineData"
        "?symbol=sh000001&scale=240&ma=no&datalen=60"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="ignore"))
    out = []
    for row in data:
        out.append(
            f"{row['day']},{row['open']},{row['close']},"
            f"{row['high']},{row['low']},{row.get('volume',0)},0"
        )
    return out, "sina"

def from_tdx():
    if not TDX_PATH.exists():
        return [], "no_tdx"
    raw = TDX_PATH.read_bytes()
    rec = 32
    out = []
    for off in range(0, len(raw) - rec + 1, rec):
        try:
            date_i, open_i, high_i, low_i, close_i, amount_f, vol_i, _ = struct.unpack(
                "<IIIIIfII", raw[off:off + rec]
            )
            d = str(date_i)
            if len(d) != 8:
                continue
            out.append(
                f"{d[:4]}-{d[4:6]}-{d[6:8]},{open_i / 100.0},"
                f"{close_i / 100.0},{high_i / 100.0},"
                f"{low_i / 100.0},{float(vol_i)},{float(amount_f)}"
            )
        except Exception:
            continue
    return out[-KLINE_LIMIT:], "tdx_local"

def get_klines():
    tried = []
    for fetcher in (from_eastmoney, from_sina, from_tdx):
        name = fetcher.__name__[5:]
        try:
            klines, src = fetcher()
            if klines:
                tried.append((name, "ok"))
                return klines, src, tried
            tried.append((name, src))
        except Exception as e:
            tried.append((name, f"{type(e).__name__}: {e}"))
    return [], "no_data", tried

# ============================================================
# Section 2: Parse + indicators
# ============================================================
def parse_klines(lines):
    rows = []
    for line in lines:
        p = line.split(",")
        if len(p) < 5:
            continue
        try:
            rows.append({
                "date": p[0],
                "open": float(p[1]),
                "close": float(p[2]),
                "high": float(p[3]),
                "low": float(p[4]),
                "vol": float(p[5]) if len(p) > 5 else 0.0,
            })
        except Exception:
            continue
    return rows

def add_indicators(rows):
    """Compute RSI14, MACD, volume MA, ATR, etc."""
    n = len(rows)
    closes = [r["close"] for r in rows]
    vols = [r["vol"] for r in rows]

    # RSI14
    rsi = [50.0] * n
    gains, losses = [], []
    for i in range(1, n):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    if len(gains) >= 14:
        avg_gain = sum(gains[:14]) / 14
        avg_loss = sum(losses[:14]) / 14
        for i in range(14, len(gains)):
            avg_gain = (avg_gain * 13 + gains[i]) / 14
            avg_loss = (avg_loss * 13 + losses[i]) / 14
            rs = avg_gain / avg_loss if avg_loss > 0 else 100
            rsi[i + 1] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = [closes[0]] * n
    ema26 = [closes[0]] * n
    macd = [0] * n
    signal = [0] * n
    hist = [0] * n
    for i in range(1, n):
        ema12[i] = closes[i] * 0.15 + ema12[i - 1] * 0.85
        ema26[i] = closes[i] * 0.075 + ema26[i - 1] * 0.925
    for i in range(n):
        macd[i] = ema12[i] - ema26[i]
    for i in range(1, n):
        signal[i] = macd[i] * 0.2 + signal[i - 1] * 0.8
        hist[i] = (macd[i] - signal[i]) * 2

    # Volume MA20
    vol_ma20 = [0] * n
    for i in range(n):
        if i >= 19:
            vol_ma20[i] = sum(vols[i - 19:i + 1]) / 20.0

    # ATR
    atr = 0
    trs = []
    for i in range(1, n):
        h, l, pc = rows[i]["high"], rows[i]["low"], rows[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    if len(trs) >= 14:
        atr = sum(trs[-14:]) / 14.0

    for i in range(n):
        rows[i]["rsi14"] = round(rsi[i], 1)
        rows[i]["macd"] = round(macd[i], 4)
        rows[i]["macd_signal"] = round(signal[i], 4)
        rows[i]["macd_hist"] = round(hist[i], 4)
        rows[i]["vol_ma20"] = round(vol_ma20[i], 0) if vol_ma20[i] > 0 else 0

    return rows, round(atr, 2)


# ============================================================
# Section 3: Elliott Wave (deepened) - wave pattern + validation
# ============================================================
def find_swings_multi(rows, lookbacks=(2, 3, 5)):
    """Multi-scale swing detection."""
    results = {}
    for lb in lookbacks:
        highs, lows = [], []
        n = len(rows)
        for i in range(lb, n - lb):
            h, l = rows[i]["high"], rows[i]["low"]
            if all(h >= rows[j]["high"] for j in range(i - lb, i + lb + 1) if j != i):
                highs.append(i)
            if all(l <= rows[j]["low"] for j in range(i - lb, i + lb + 1) if j != i):
                lows.append(i)
        results[lb] = (highs, lows)
    return results


def build_wave_seq(highs, lows):
    """Build chronological sequence of H/L pivots with their prices."""
    seq = []
    for i in highs:
        seq.append({"idx": i, "type": "H", "price": -1})
    for i in lows:
        seq.append({"idx": i, "type": "L", "price": -1})
    seq.sort(key=lambda x: x["idx"])
    return seq


def attempt_wave_count(rows, highs, lows):
    """
    Attempt Elliott wave counting.
    Rules:
    - Wave 2 never retraces >100% of wave 1
    - Wave 3 is never the shortest impulse
    - Wave 4 does not overlap wave 1 (in non-diagonal)
    - Wave 5 often shows divergence
    Returns: (wave_labels, confidence, invalid_rules)
    """
    seq = build_wave_seq(highs, lows)
    if len(seq) < 4:
        return [], 0, ["insufficient_pivots"]

    # Populate prices
    for s in seq:
        r = rows[s["idx"]]
        s["price"] = r["high"] if s["type"] == "H" else r["low"]

    # Try to label as impulse: start from latest major low
    impulses = []
    # Find potential wave starts (significant low followed by higher high)
    for i in range(len(seq) - 4):
        if seq[i]["type"] == "L" and seq[i + 1]["type"] == "H":
            wave1_h = seq[i + 1]["price"]
            wave1_l = seq[i]["price"]
            wave1_size = wave1_h - wave1_l

            # Find wave 2: retracement after wave 1
            wave2_l = None
            for j in range(i + 1, len(seq)):
                if seq[j]["type"] == "L" and seq[j]["price"] < wave1_h:
                    wave2_l = seq[j]["price"]
                    wave2_idx = j
                    break
            if wave2_l is None:
                continue

            # Rule: wave 2 must not retrace >100% of wave 1
            if wave2_l < wave1_l:
                continue

            # Find wave 3: move above wave 1 high
            wave3_h = None
            for j in range(wave2_idx + 1, len(seq)):
                if seq[j]["type"] == "H" and seq[j]["price"] > wave1_h:
                    wave3_h = seq[j]["price"]
                    wave3_idx = j
                    break
            if wave3_h is None:
                continue
            wave3_size = wave3_h - wave2_l

            # Rule: wave 3 must be at least 1.0x wave 1 (can't be shortest)
            if wave3_size < wave1_size:
                continue

            # Find wave 4: retracement after wave 3
            wave4_l = None
            for j in range(wave3_idx + 1, len(seq)):
                if seq[j]["type"] == "L" and seq[j]["price"] < wave3_h:
                    wave4_l = seq[j]["price"]
                    wave4_idx = j
                    break
            if wave4_l is None:
                continue

            # Find wave 5: final move up
            wave5_h = None
            for j in range(wave4_idx + 1, len(seq)):
                if seq[j]["type"] == "H" and seq[j]["price"] > wave3_h:
                    wave5_h = seq[j]["price"]
                    wave5_idx = j
                    break
            if wave5_h is None:
                # Incomplete wave 5 - current price might be in wave 5
                wave5_h = rows[-1]["close"]
                wave5_idx = len(rows) - 1

            wave5_size = wave5_h - wave4_l

            # Rule: wave 4 should not overlap wave 1
            overlap = wave4_l <= wave1_h

            # Rule: check for divergence at wave 5
            has_divergence = False
            if wave5_idx > wave3_idx + 3:
                # Compare RSI at wave 3 high vs wave 5 high
                rsi_at_3 = rows[seq[wave3_idx]["idx"]].get("rsi14", 50)
                rsi_at_5 = rows[-1].get("rsi14", 50) if wave5_idx >= len(rows) else rows[wave5_idx].get("rsi14", 50)
                has_divergence = rsi_at_5 < rsi_at_3 - 5

            # Scoring
            rules_passed = 3  # base
            invalid = []
            if wave2_l < wave1_l:
                invalid.append("wave2 >100% wave1")
                rules_passed -= 1
            if wave3_size < wave1_size * 0.8:
                invalid.append("wave3 shorter than wave1")
                rules_passed -= 1
            if overlap:
                invalid.append("wave4 overlaps wave1")
                rules_passed -= 1

            confidence = rules_passed / 4.0  # 0-1
            labels = {
                "wave1_low": round(wave1_l, 2),
                "wave1_high": round(wave1_h, 2),
                "wave2_low": round(wave2_l, 2),
                "wave3_high": round(wave3_h, 2),
                "wave4_low": round(wave4_l, 2),
                "wave5_high": round(wave5_h, 2),
                "confidence": round(confidence, 2),
                "invalid_rules": invalid,
                "divergence_at_5": has_divergence,
            }
            impulses.append(labels)

    if impulses:
        # Return the best (highest confidence) impulse count
        best = max(impulses, key=lambda x: x["confidence"])
        return best, best["confidence"], best["invalid_rules"]
    return {}, 0, ["no_valid_pattern"]


def analyze_elliott_deep(rows, swings_h, swings_l):
    """Deepened Elliott analysis."""
    n = len(rows)
    if n < 20 or not swings_h or not swings_l:
        return {
            "trend_stage": "unclear",
            "dominant_structure": "sideways",
            "exclude_from_buying": True,
            "wave_count": {},
            "wave_confidence": 0,
        }

    # Basic trend
    recent_h = sorted(swings_h)[-6:]
    recent_l = sorted(swings_l)[-6:]
    if len(recent_h) >= 2 and len(recent_l) >= 2:
        last2_h = sorted([rows[i]["high"] for i in recent_h[-2:]])
        last2_l = sorted([rows[i]["low"] for i in recent_l[-2:]])
        if last2_h[-1] > last2_h[0] and last2_l[-1] > last2_l[0]:
            dominant = "up"
            stage = "impulse upward"
        elif last2_h[-1] < last2_h[0] and last2_l[-1] < last2_l[0]:
            dominant = "down"
            stage = "impulse downward"
        else:
            dominant = "sideways"
            stage = "correction"
    else:
        dominant = "sideways"
        stage = "correction"

    # Attempt wave count
    wave_labels, confidence, invalid = attempt_wave_count(rows, swings_h, swings_l)

    exclude = (dominant == "down") or (dominant == "sideways" and confidence < 0.5)

    return {
        "trend_stage": stage,
        "dominant_structure": dominant,
        "exclude_from_buying": exclude,
        "wave_count": wave_labels,
        "wave_confidence": round(confidence, 2),
        "invalid_rules": invalid,
        "assessment": _elliott_assessment(dominant, confidence, invalid),
    }


def _elliott_assessment(dominant, confidence, invalid):
    if dominant == "up" and confidence >= 0.75 and not invalid:
        return "艾略特强势上升浪，浪型计数有效"
    elif dominant == "up" and confidence >= 0.5:
        return f"疑似上升趋势但浪型计数不确定 (问题: {invalid})"
    elif dominant == "up":
        return "上升结构但浪型计数不可靠"
    elif dominant == "down":
        return "下降结构——回避买入"
    return "横盘整理——等待方向明确"


# ============================================================
# Section 4: Chan Structure (deepened) - central zones + divergence
# ============================================================
def find_zhongshu(rows, pivots_l, pivots_h):
    """
    Identify central zones (中枢).
    A zhongshu is formed by 3+ consecutive overlapping price ranges.
    Returns list of {high, low, start_idx, end_idx, bars}.
    """
    if len(pivots_l) < 2 or len(pivots_h) < 2:
        return []

    # Build pivot sequence
    seq = []
    for i in pivots_l:
        seq.append({"idx": i, "type": "L", "price": rows[i]["low"]})
    for i in pivots_h:
        seq.append({"idx": i, "type": "H", "price": rows[i]["high"]})
    seq.sort(key=lambda x: x["idx"])

    zones = []
    i = 0
    while i < len(seq) - 2:
        # A zhongshu needs at least 3 segments: e.g., H-L-H or L-H-L
        a, b, c = seq[i], seq[i + 1], seq[i + 2]
        z_high = min(a["price"], c["price"]) if a["type"] == "H" else min(b["price"], c["price"])
        z_low = max(a["price"], c["price"]) if a["type"] == "L" else max(b["price"], c["price"])
        if z_high > z_low:
            zones.append({
                "high": round(z_high, 2),
                "low": round(z_low, 2),
                "start_idx": seq[i]["idx"],
                "end_idx": seq[i + 2]["idx"],
                "bars": seq[i + 2]["idx"] - seq[i]["idx"],
            })
        i += 1

    # Merge overlapping/nested zones
    if not zones:
        return []
    zones.sort(key=lambda z: (z["start_idx"], z["high"]))
    merged = [zones[0]]
    for z in zones[1:]:
        prev = merged[-1]
        # If this zone starts before previous ends and overlaps in price
        if z["start_idx"] < prev["end_idx"] and z["high"] > prev["low"]:
            prev["high"] = max(prev["high"], z["high"])
            prev["low"] = min(prev["low"], z["low"])
            prev["end_idx"] = max(prev["end_idx"], z["end_idx"])
            prev["bars"] = prev["end_idx"] - prev["start_idx"]
        else:
            merged.append(z)

    return merged


def detect_divergence(rows, pivots_h, pivots_l):
    """
    Detect RSI/MACD divergence between consecutive pivots.
    Bullish: price lower low, RSI higher low
    Bearish: price higher high, RSI lower high
    """
    divergences = []

    # Check consecutive highs for bearish divergence
    for i in range(len(pivots_h) - 1):
        idx1, idx2 = pivots_h[i], pivots_h[i + 1]
        if idx2 > idx1 and rows[idx2]["high"] > rows[idx1]["high"]:
            rsi1 = rows[idx1].get("rsi14", 50)
            rsi2 = rows[idx2].get("rsi14", 50)
            if rsi2 < rsi1:
                divergences.append({
                    "type": "bearish",
                    "pivot1": idx1,
                    "pivot2": idx2,
                    "price1": round(rows[idx1]["high"], 2),
                    "price2": round(rows[idx2]["high"], 2),
                    "rsi1": rsi1,
                    "rsi2": rsi2,
                })

    # Check consecutive lows for bullish divergence
    for i in range(len(pivots_l) - 1):
        idx1, idx2 = pivots_l[i], pivots_l[i + 1]
        if idx2 > idx1 and rows[idx2]["low"] < rows[idx1]["low"]:
            rsi1 = rows[idx1].get("rsi14", 50)
            rsi2 = rows[idx2].get("rsi14", 50)
            if rsi2 > rsi1:
                divergences.append({
                    "type": "bullish",
                    "pivot1": idx1,
                    "pivot2": idx2,
                    "price1": round(rows[idx1]["low"], 2),
                    "price2": round(rows[idx2]["low"], 2),
                    "rsi1": rsi1,
                    "rsi2": rsi2,
                })

    return divergences[-3:] if len(divergences) > 3 else divergences


def analyze_chan_deep(rows, swings_h, swings_l):
    """Deepened Chan analysis."""
    n = len(rows)
    if n < 5:
        return {
            "trend_state": "unclear",
            "in_structure": True,
            "buy_point_valid": False,
            "zhongshu": [],
            "divergences": [],
        }

    last_close = rows[-1]["close"]

    # Fractals with multi-scale
    bot_fractals = []
    top_fractals = []
    for lookback in (1, 2):
        for i in range(lookback, n - lookback):
            if rows[i]["low"] < rows[i - lookback]["low"] and rows[i]["low"] < rows[i + lookback]["low"]:
                bot_fractals.append(i)
            if rows[i]["high"] > rows[i - lookback]["high"] and rows[i]["high"] > rows[i + lookback]["high"]:
                top_fractals.append(i)
    bot_fractals = sorted(set(bot_fractals))
    top_fractals = sorted(set(top_fractals))

    # Central zones
    zhongshu = find_zhongshu(rows, bot_fractals[:20] if len(bot_fractals) > 20 else bot_fractals,
                            top_fractals[:20] if len(top_fractals) > 20 else top_fractals)

    # Divergence
    divergences = detect_divergence(rows, top_fractals, bot_fractals)

    # Trend from zhongshu relationships
    trend = "consolidation"
    if len(zhongshu) >= 2:
        prev, curr = zhongshu[-2], zhongshu[-1]
        if curr["low"] > prev["high"]:
            trend = "uptrend"
        elif curr["high"] < prev["low"]:
            trend = "downtrend"

    # In structure check
    in_structure = True
    if zhongshu:
        last_zs = zhongshu[-1]
        in_structure = last_zs["low"] <= last_close <= last_zs["high"]

    # Buy point validity
    buy_valid = False
    if bot_fractals:
        last_bot = bot_fractals[-1]
        buy_valid = (last_close > rows[last_bot]["low"]) and (trend != "downtrend")

    # Composite trend
    if trend == "uptrend" and divergences and any(d["type"] == "bearish" for d in divergences[-2:]):
        trend_detail = "uptrend with bearish divergence warning"
    elif trend == "downtrend" and divergences and any(d["type"] == "bullish" for d in divergences[-2:]):
        trend_detail = "downtrend with bullish divergence signal"
    else:
        trend_detail = trend

    return {
        "trend_state": trend,
        "trend_detail": trend_detail,
        "in_structure": in_structure,
        "buy_point_valid": buy_valid,
        "zhongshu": zhongshu[-3:] if len(zhongshu) > 3 else zhongshu,
        "zhongshu_count": len(zhongshu),
        "divergences": divergences,
        "fractal_highs_count": len(top_fractals),
        "fractal_lows_count": len(bot_fractals),
    }


# ============================================================
# Section 5: Fibonacci (deepened) - multi-swing cluster analysis
# ============================================================
def multi_swing_fib(rows, swings_h, swings_l):
    """Analyze Fibonacci levels from multiple swing pairs."""
    if len(swings_h) < 2 or len(swings_l) < 2:
        return {
            "swings_analyzed": 0,
            "clusters": [],
            "harmonic_hints": [],
        }

    # Take last 5 swing pairs
    pairs = []
    seq = []
    for i in swings_h:
        seq.append({"idx": i, "type": "H", "price": rows[i]["high"]})
    for i in swings_l:
        seq.append({"idx": i, "type": "L", "price": rows[i]["low"]})
    seq.sort(key=lambda x: x["idx"])

    for i in range(len(seq) - 1):
        a, b = seq[i], seq[i + 1]
        if a["type"] != b["type"]:
            high = max(a["price"], b["price"])
            low = min(a["price"], b["price"])
            if high > low:
                pairs.append({
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "range": round(high - low, 2),
                    "start_date": rows[a["idx"]]["date"],
                    "end_date": rows[b["idx"]]["date"],
                })

    last_pairs = pairs[-5:] if len(pairs) > 5 else pairs

    # Calculate retracement clusters
    all_retrace = defaultdict(list)
    fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
    ext_ratios = [1.272, 1.618, 2.0, 2.618]

    for pp in last_pairs:
        for r in fib_ratios:
            lv = round(pp["high"] - pp["range"] * r, 2)
            bucket = round(lv / 5) * 5  # Bucket by 5-point intervals
            all_retrace[bucket].append({
                "level": lv,
                "ratio": r,
                "swing_high": pp["high"],
                "swing_low": pp["low"],
            })

    # Extension clusters
    all_ext = defaultdict(list)
    for pp in last_pairs:
        for r in ext_ratios:
            lv = round(pp["low"] + pp["range"] * r, 2)
            bucket = round(lv / 5) * 5
            all_ext[bucket].append({
                "level": lv,
                "ratio": r,
                "swing_high": pp["high"],
                "swing_low": pp["low"],
            })

    # Cluster detection
    retrace_clusters = []
    for bucket, entries in sorted(all_retrace.items()):
        if len(entries) >= 2:
            avg_level = round(sum(e["level"] for e in entries) / len(entries), 2)
            retrace_clusters.append({
                "zone": avg_level,
                "confluence_count": len(entries),
                "ratios": sorted(set(e["ratio"] for e in entries)),
            })

    ext_clusters = []
    for bucket, entries in sorted(all_ext.items()):
        if len(entries) >= 2:
            avg_level = round(sum(e["level"] for e in entries) / len(entries), 2)
            ext_clusters.append({
                "zone": avg_level,
                "confluence_count": len(entries),
            })

    # Harmonic pattern hints
    harmonic_hints = []
    for pp in last_pairs:
        rng = pp["range"]
        # Gartley: B ret ~0.618, C ext to 0.786, D at 1.272
        ret_382 = pp["high"] - rng * 0.382
        ret_618 = pp["high"] - rng * 0.618
        ext_1272 = pp["high"] + rng * 0.272
        harmonic_hints.append({
            "pattern": "potential_Gartley_if_B_near",
            "zone_B": round(ret_382, 2),
            "zone_C": round(ret_618, 2),
            "zone_D": round(ext_1272, 2),
        })

    return {
        "swings_analyzed": len(last_pairs),
        "retrace_clusters": retrace_clusters[:5] if len(retrace_clusters) > 5 else retrace_clusters,
        "extension_clusters": ext_clusters[:3] if len(ext_clusters) > 3 else ext_clusters,
        "harmonic_hints": harmonic_hints[:2] if len(harmonic_hints) > 2 else harmonic_hints,
        "last_swing": last_pairs[-1] if last_pairs else None,
    }


# ============================================================
# Section 6: Gann (deepened) - square of 9 + multi-angle + time cycles
# ============================================================
def gann_square_of_9(base_price, levels=5):
    """Gann Square of 9 levels from a significant pivot."""
    sqrt_base = math.sqrt(base_price)
    results = []
    for i in range(levels):
        above = round((sqrt_base + (i + 1) * 0.125) ** 2, 2)
        below = round((sqrt_base - (i + 1) * 0.125) ** 2, 2)
        results.append({"level": above, "direction": "above", "degree": (i + 1) * 45})
        results.append({"level": below, "direction": "below", "degree": (i + 1) * 45})
    return results


def gann_angles_extended(rows):
    """Extended Gann angle analysis with multiple pivots and time cycles."""
    if len(rows) < 20:
        return {"angles": {}, "sq9_levels": [], "time_cycles": []}

    recent = rows[-40:] if len(rows) >= 40 else rows
    highs = [r["high"] for r in recent]
    lows = [r["low"] for r in recent]
    closes = [r["close"] for r in recent]

    rng = max(highs) - min(lows)
    unit_per_day = rng / 40.0 if rng else 0
    last = closes[-1]
    n = len(recent)

    # Multi-angle from recent low and high
    recent_low = min(lows)
    recent_high = max(highs)
    low_idx = lows.index(recent_low)
    high_idx = highs.index(recent_high)

    angles = {}
    angle_ratios = {
        "8x1": 0.125, "4x1": 0.25, "3x1": 0.333, "2x1": 0.5,
        "1x1": 1.0,
        "1x2": 2.0, "1x3": 3.0, "1x4": 4.0, "1x8": 8.0,
    }

    for name, ratio in angle_ratios.items():
        days_from_low = n - low_idx
        days_from_high = n - high_idx
        angles[f"{name}_from_low"] = round(recent_low + unit_per_day * ratio * days_from_low, 2)
        angles[f"{name}_from_high"] = round(recent_high - unit_per_day * ratio * days_from_high, 2)

    # Square of 9 from recent significant pivot
    sq9 = gann_square_of_9(round(last), levels=4)

    # Time cycles
    time_cycles = []
    cycle_lengths = [20, 30, 45, 60, 90]
    for cl in cycle_lengths:
        if len(rows) >= cl:
            past = rows[-cl]
            future_target = rows[-1]["date"]  # last available confirmed bar date
            time_cycles.append({
                "cycle_days": cl,
                "past_date": past["date"],
                "past_price": round(past["close"], 2),
                "note": f"{cl}-day cycle reference",
            })

    return {
        "angles": angles,
        "sq9_levels": sq9,
        "time_cycles": time_cycles,
        "unit_per_day": round(unit_per_day, 4),
        "range_40d": round(rng, 2),
    }


# ============================================================
# Section 7: Wyckoff (deepened) - VSA + spring/upthrust + effort/result
# ============================================================
def classify_bars(rows):
    """Volume Spread Analysis: classify each bar."""
    n = len(rows)
    if n < 30:
        return []

    classifications = []
    for i in range(n):
        bar = rows[i]
        spread = bar["high"] - bar["low"]
        close_pos = (bar["close"] - bar["low"]) / spread if spread > 0 else 0.5
        is_up = bar["close"] > bar["open"]
        vol_ratio = bar["vol"] / bar["vol_ma20"] if bar.get("vol_ma20", 0) > 0 else 1.0

        # Ultra-high volume
        climactic = vol_ratio > 2.0 and spread > spread * 0.5  # relative check deferred

        cls = {
            "date": bar["date"],
            "is_up": is_up,
            "close_position": round(close_pos, 2),
            "vol_ratio": round(vol_ratio, 2),
            "climactic": False,  # set below
        }
        classifications.append(cls)

    # Set climactic flag
    spreads = [r["high"] - r["low"] for r in rows]
    avg_spread = sum(spreads[-30:]) / 30 if len(spreads) >= 30 else sum(spreads) / len(spreads)
    vols = [r["vol"] for r in rows]
    avg_vol = sum(vols[-30:]) / 30 if len(vols) >= 30 else sum(vols) / len(vols)

    for i in range(len(rows)):
        spread = spreads[i]
        vol_ratio = vols[i] / avg_vol if avg_vol > 0 else 1
        if vol_ratio > 2.0 and spread > avg_spread * 1.5:
            classifications[i]["climactic"] = True

    return classifications


def detect_spring_upthrust(rows, bars_cls):
    """Detect Spring and Upthrust patterns."""
    springs = []
    upthrusts = []
    n = len(rows)
    if n < 10:
        return springs, upthrusts

    for i in range(5, n - 2):
        bc = bars_cls[i]
        # Spring: breaks below support then closes back above it
        if bc["is_up"] and rows[i]["low"] < rows[i - 1]["low"] and rows[i]["close"] > rows[i - 1]["low"]:
            if bc["vol_ratio"] > 1.5:  # high volume spring is stronger
                springs.append({
                    "date": rows[i]["date"],
                    "low": round(rows[i]["low"], 2),
                    "close": round(rows[i]["close"], 2),
                    "vol_ratio": bc["vol_ratio"],
                    "note": "放量弹簧——看涨反转信号",
                })
            elif bc["close_position"] > 0.8:  # close near high of bar
                springs.append({
                    "date": rows[i]["date"],
                    "low": round(rows[i]["low"], 2),
                    "close": round(rows[i]["close"], 2),
                    "vol_ratio": bc["vol_ratio"],
                    "note": "弹簧收盘近高——潜在反转",
                })

        # Upthrust: breaks above resistance then closes back below it
        if not bc["is_up"] and rows[i]["high"] > rows[i - 1]["high"] and rows[i]["close"] < rows[i - 1]["high"]:
            upthrusts.append({
                "date": rows[i]["date"],
                "high": round(rows[i]["high"], 2),
                "close": round(rows[i]["close"], 2),
                "vol_ratio": bc["vol_ratio"],
                "note": "上刺——看跌反转信号",
            })

    return springs[-3:] if len(springs) > 3 else springs, upthrusts[-3:] if len(upthrusts) > 3 else upthrusts


def wyckoff_deep(rows):
    """Deepened Wyckoff analysis with VSA and pattern detection."""
    if len(rows) < 30:
        return {
            "phase": "unclear",
            "confidence": 0,
            "six_conditions": {},
            "all_six_met": False,
            "passed_count": 0,
            "springs": [],
            "upthrusts": [],
            "effort_vs_result": "insufficient data",
            "assessment": "insufficient data for Wyckoff analysis",
        }

    recent = rows[-30:]
    bars_cls = classify_bars(rows)[-30:]
    springs, upthrusts = detect_spring_upthrust(rows[-30:], bars_cls)

    closes_30 = [r["close"] for r in recent]
    vols_30 = [r["vol"] for r in recent]
    price_change_30 = (closes_30[-1] - closes_30[0]) / closes_30[0] if closes_30[0] else 0

    # Six conditions
    ranges_f = [r["high"] - r["low"] for r in recent[:15]]
    ranges_l = [r["high"] - r["low"] for r in recent[-15:]]
    early_range_avg = sum(ranges_f) / 15 if ranges_f else 0
    late_range_avg = sum(ranges_l) / 15 if ranges_l else 0
    range_contracting = late_range_avg < early_range_avg * 0.8

    early_vol_avg = sum(vols_30[:15]) / 15 if len(vols_30) >= 15 else 0
    late_vol_avg = sum(vols_30[-15:]) / 15 if len(vols_30) >= 15 else 0
    vol_declining = late_vol_avg < early_vol_avg * 0.7 if early_vol_avg > 0 else False

    accumulation = range_contracting and vol_declining
    markup = price_change_30 > 0.02 and late_vol_avg > early_vol_avg * 1.1

    avg_vol = sum(vols_30) / 30 if vols_30 else 1
    pullback_days = [cls for cls in bars_cls if not cls["is_up"]]
    pullback_low_vol = all(bc["vol_ratio"] < 1.2 for bc in pullback_days) if pullback_days else False

    up_days = [cls for cls in bars_cls if cls["is_up"]]
    breakout_vol = any(bc["climactic"] for bc in up_days) if up_days else False

    # Follow-through: check last 10 bars
    last10 = bars_cls[-10:] if len(bars_cls) >= 10 else bars_cls
    follow_through = False
    for i in range(len(last10) - 2):
        if last10[i]["is_up"] and last10[i]["vol_ratio"] > 1.3:
            if last10[i + 1]["close_position"] > 0.5 and last10[i + 2]["close_position"] > 0.5:
                follow_through = True
                break

    up_bars = sum(1 for bc in bars_cls if bc["is_up"])
    up_vols = [v for i, v in enumerate(vols_30) if bars_cls[i]["is_up"]]
    down_vols = [v for i, v in enumerate(vols_30) if not bars_cls[i]["is_up"]]
    avg_up_vol = sum(up_vols) / len(up_vols) if up_vols else 0
    avg_down_vol = sum(down_vols) / len(down_vols) if down_vols else 0
    vp_healthy = up_bars > len(bars_cls) * 0.5 and avg_up_vol > avg_down_vol and price_change_30 > 0

    six = {
        "accumulation_or_re_accumulation": accumulation,
        "markup_or_launch_attempt": markup,
        "pullback_low_volume": pullback_low_vol,
        "breakout_volume_confirmed": breakout_vol,
        "follow_through_or_acceptance": follow_through,
        "volume_price_healthy": vp_healthy,
    }
    passed = sum(1 for v in six.values() if v)
    all_six = (passed == 6)

    # Phase determination
    if springs and price_change_30 > 0:
        phase = "弹簧形成——潜在吸筹"
    elif upthrusts and price_change_30 < 0:
        phase = "上刺形成——潜在派发"
    elif accumulation and springs:
        phase = "吸筹（弹簧测试通过）"
    elif markup and all_six:
        phase = "拉升"
    elif price_change_30 < -0.05:
        phase = "下跌"
    elif not markup and not accumulation:
        phase = "派发"
    else:
        phase = "不明确"

    # Effort vs Result
    total_up_effort = sum(r["vol"] for r in recent if r["close"] > r["open"])
    total_down_effort = sum(r["vol"] for r in recent if r["close"] < r["open"])
    net_close_change = closes_30[-1] - closes_30[0]
    if abs(net_close_change) < closes_30[0] * 0.01 and max(total_up_effort, total_down_effort) > 0:
        evr = "高消耗低回报——吸收或派发"
    elif net_close_change > 0 and total_up_effort > total_down_effort:
        evr = "量价匹配——健康买盘"
    elif net_close_change < 0 and total_down_effort > total_up_effort:
        evr = "量价匹配——健康卖盘"
    else:
        evr = "信号矛盾"

    # Composite score 0-100
    score = 0
    if springs:
        score += 30
    if upthrusts:
        score -= 20
    score += passed * 10
    if evr == "量价匹配——健康买盘":
        score += 15
    score = max(0, min(100, score))

    # Assessment
    if score >= 70:
        assessment = "威科夫偏多：可见吸筹或拉升"
    elif score >= 40:
        assessment = "威科夫中性偏多：有积极信号但未完全确认"
    elif score >= 20:
        assessment = "威科夫偏空：派发或下跌概率大"
    else:
        assessment = "威科夫极弱：回避入场，明显看跌信号"

    return {
        "phase": phase,
        "confidence": score,
        "six_conditions": six,
        "all_six_met": all_six,
        "passed_count": passed,
        "springs": springs,
        "upthrusts": upthrusts,
        "effort_vs_result": evr,
        "composite_score": score,
        "assessment": assessment,
    }


# ============================================================
# Section 8: Combined Analysis (deepened)
# ============================================================
def combined_analysis(elliott, chan, fib, gann, wyckoff, rows, last_close):
    """Multi-method weighted scoring and scenario generation."""
    n = len(rows)

    # Weighted confidence scoring
    scores = {}

    # Elliott score: 0-100
    if elliott["dominant_structure"] == "up" and elliott["wave_confidence"] >= 0.75:
        scores["elliott"] = 85
    elif elliott["dominant_structure"] == "up" and elliott["wave_confidence"] >= 0.5:
        scores["elliott"] = 65
    elif elliott["dominant_structure"] == "up":
        scores["elliott"] = 50
    elif elliott["dominant_structure"] == "down":
        scores["elliott"] = 15
    else:
        scores["elliott"] = 35

    # Chan score
    if chan["trend_state"] == "uptrend" and chan["buy_point_valid"] and not any(d["type"] == "bearish" for d in chan.get("divergences", [])):
        scores["chan"] = 80
    elif chan["trend_state"] == "uptrend" and chan["buy_point_valid"]:
        scores["chan"] = 65
    elif chan["trend_state"] == "uptrend":
        scores["chan"] = 55
    elif chan["trend_state"] == "downtrend":
        scores["chan"] = 20
    else:
        scores["chan"] = 40

    # Fibonacci cluster score
    retrace_clusters = fib.get("retrace_clusters", [])
    if retrace_clusters:
        max_confluence = max(c["confluence_count"] for c in retrace_clusters)
        scores["fibonacci"] = min(85, 40 + max_confluence * 15)
    else:
        scores["fibonacci"] = 30

    # Gann score
    scores["gann"] = 50  # Always secondary

    # Wyckoff score
    scores["wyckoff"] = wyckoff["composite_score"]

    # Overall weighted score
    weights = {"elliott": 0.25, "chan": 0.25, "fibonacci": 0.15, "gann": 0.05, "wyckoff": 0.30}
    overall = sum(scores[k] * weights.get(k, 0) for k in scores) / sum(weights.values())

    # Signal quality
    if overall >= 75:
        quality = "强势看多"
    elif overall >= 55:
        quality = "中性偏多"
    elif overall >= 40:
        quality = "中性矛盾"
    elif overall >= 25:
        quality = "中性偏空"
    else:
        quality = "强势看空"

    # Collect all levels
    all_levels = []

    # From Elliott
    wc = elliott.get("wave_count", {})
    for k in ["wave1_low", "wave1_high", "wave2_low", "wave3_high", "wave4_low"]:
        if k in wc:
            all_levels.append({"level": wc[k], "method": f"浪{k}", "weight": 0.8})

    # From Chan
    for zs in chan.get("zhongshu", []):
        all_levels.append({"level": zs["high"], "method": "缠论中枢上沿", "weight": 0.8})
        all_levels.append({"level": zs["low"], "method": "缠论中枢下沿", "weight": 0.8})

    # From Fibonacci clusters
    for fc in retrace_clusters:
        all_levels.append({"level": fc["zone"], "method": f"斐波汇聚{fc['confluence_count']}x", "weight": 0.6 + fc["confluence_count"] * 0.1})
    for ec in fib.get("extension_clusters", [])[:2]:
        all_levels.append({"level": ec["zone"], "method": f"斐波扩展{ec['confluence_count']}x", "weight": 0.5})

    # From Gann Sq9
    for sq in gann.get("sq9_levels", [])[:4]:
        all_levels.append({"level": sq["level"], "method": f"江恩四方{sq['degree']}度", "weight": 0.4})

    # Confluence
    def group_levels(levels, tolerance=0.008):
        if not levels:
            return []
        sorted_lv = sorted(levels, key=lambda x: x["level"])
        groups = []
        current = [sorted_lv[0]]
        for lv in sorted_lv[1:]:
            if abs(lv["level"] - current[-1]["level"]) / current[-1]["level"] <= tolerance:
                current.append(lv)
            else:
                groups.append(current)
                current = [lv]
        groups.append(current)
        out = []
        for g in groups:
            avg = sum(x["level"] for x in g) / len(g)
            methods = sorted(set(x["method"] for x in g))
            w = sum(x.get("weight", 0.5) for x in g) / len(g)
            out.append({"level": round(avg, 2), "methods": methods, "count": len(methods), "avg_weight": round(w, 2), "strength": "strongest" if len(methods) >= 3 else ("high" if len(methods) >= 2 else "low")})
        return out

    confluence = group_levels(all_levels)
    support_confl = [z for z in confluence if z["level"] <= last_close]
    resistance_confl = [z for z in confluence if z["level"] > last_close]

    # Scenario generation
    main_parts = []
    alt_parts = []

    if quality in ("强势看多", "中性偏多"):
        main_parts.append(f"看多情景 (综合评分 {overall:.0f}/100)")
        if elliott["dominant_structure"] == "up":
            main_parts.append(f"艾略特: {elliott['assessment']}")
        if chan["buy_point_valid"]:
            main_parts.append("缠论: 买点确认")
        if wyckoff["springs"]:
            main_parts.append(f"威科夫: {len(wyckoff['springs'])}个弹簧信号")
        alt_parts.append("看空备选: 若跌破关键支撑，上行可能失败")
    elif quality in ("强势看空", "中性偏空"):
        main_parts.append(f"看空情景 (综合评分 {overall:.0f}/100)")
        if elliott["dominant_structure"] == "down":
            main_parts.append(f"艾略特: {elliott['assessment']}")
        if wyckoff["upthrusts"]:
            main_parts.append(f"威科夫: {len(wyckoff['upthrusts'])}个上刺信号")
        alt_parts.append("看多备选: 若突破关键阻力，可能反转")
    else:
        main_parts.append(f"中性矛盾 (综合评分 {overall:.0f}/100)")
        alt_parts.append("方向不明——等待突破阻力位或跌破支撑位确认方向")

    # Add support/resistance zones
    if support_confl:
        best_sup = min(support_confl, key=lambda z: abs(z["level"] - last_close))
        main_parts.append(f"关键支撑: {best_sup['level']} ({best_sup['strength']})")
    if resistance_confl:
        best_res = min(resistance_confl, key=lambda z: abs(z["level"] - last_close))
        main_parts.append(f"关键阻力: {best_res['level']} ({best_res['strength']})")

    # Add Wyckoff assessment
    main_parts.append(f"威科夫: {wyckoff['assessment']} (评分 {wyckoff['composite_score']}/100)")

    return {
        "method_scores": scores,
        "method_scores_cn": {
            "艾略特波浪": scores["elliott"],
            "缠论": scores["chan"],
            "斐波那契": scores["fibonacci"],
            "江恩": scores["gann"],
            "威科夫": scores["wyckoff"],
        },
        "overall_score": round(overall, 1),
        "signal_quality": quality,
        "confluence_zones": confluence,
        "support_zones": support_confl,
        "resistance_zones": resistance_confl,
        "main_scenario": " | ".join(main_parts) if main_parts else "insufficient data",
        "alternate_scenario": " | ".join(alt_parts) if alt_parts else "",
    }


# ============================================================
# Section 9: Main
# ============================================================
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    klines, src, tried = get_klines()
    if not klines:
        report = {"skill": SKILL, "name_cn": NAME_CN, "status": "FALLBACK", "sources_tried": tried}
        p = OUTPUT_DIR / "support_resistance_report.json"
        p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": "FALLBACK"}, ensure_ascii=False))
        return 1

    rows = parse_klines(klines)
    rows, atr = add_indicators(rows)
    last = rows[-1]
    last_close = last["close"]
    n = len(rows)

    # Basic levels
    closes = [r["close"] for r in rows]
    highs_20 = [r["high"] for r in rows[-20:]]
    lows_20 = [r["low"] for r in rows[-20:]]
    ma20 = sum(closes[-20:]) / 20
    ma60 = sum(closes[-60:]) / 60 if n >= 60 else sum(closes) / n
    recent_high = max(highs_20)
    recent_low = min(lows_20)

    # 5 methods
    swings_h, swings_l = [], []
    for lb in (2, 3):
        h, l = [], []
        for i in range(lb, n - lb):
            if all(rows[i]["high"] >= rows[j]["high"] for j in range(i - lb, i + lb + 1) if j != i):
                h.append(i)
            if all(rows[i]["low"] <= rows[j]["low"] for j in range(i - lb, i + lb + 1) if j != i):
                l.append(i)
        swings_h.extend(h)
        swings_l.extend(l)
    swings_h = sorted(set(swings_h))
    swings_l = sorted(set(swings_l))

    elliott = analyze_elliott_deep(rows, swings_h, swings_l)
    chan = analyze_chan_deep(rows, swings_h, swings_l)
    fib = multi_swing_fib(rows, swings_h, swings_l)
    gann = gann_angles_extended(rows)
    wyckoff = wyckoff_deep(rows)

    # Combined
    combined = combined_analysis(elliott, chan, fib, gann, wyckoff, rows, last_close)

    # Actual levels
    actual_sup = sorted(set([round(ma20, 2), round(ma60, 2), round(recent_low, 2)] + [round(rows[i]["low"], 2) for i in swings_l[-3:]]), reverse=True)
    actual_res = sorted(set([round(recent_high, 2)] + [round(rows[i]["high"], 2) for i in swings_h[-3:]]))
    actual_sup_below = [lv for lv in actual_sup if lv <= last_close]
    actual_res_above = [lv for lv in actual_res if lv > last_close]

    # Trigger lines
    breakout = round(actual_res_above[0] + atr * 0.5, 2) if actual_res_above else None
    breakdown = round(actual_sup_below[0] - atr * 0.5, 2) if actual_sup_below else None

    # Add display names to methods
    elliott["name_cn"] = "艾略特波浪"
    chan["name_cn"] = "缠论"
    fib["name_cn"] = "斐波那契"
    gann["name_cn"] = "江恩"
    wyckoff["name_cn"] = "威科夫"

    report = {
        "skill": SKILL, "name_cn": NAME_CN, "version": "3.0.0",
        "generated_at": datetime.now(CST).isoformat(timespec="seconds"),
        "data_source": src, "sources_tried": tried,
        "symbol": SYMBOL, "name": SYMBOL_NAME,
        "kline_count": n, "last_close": round(last_close, 2), "last_date": last["date"],
        "atr_14": round(atr, 2),

        # 7-field output
        "primary_support_zone": actual_sup_below[0] if actual_sup_below else (combined["support_zones"][0]["level"] if combined["support_zones"] else recent_low),
        "secondary_support_zone": actual_sup_below[1] if len(actual_sup_below) >= 2 else round(ma60, 2),
        "primary_resistance_zone": actual_res_above[0] if actual_res_above else (combined["resistance_zones"][0]["level"] if combined["resistance_zones"] else recent_high),
        "breakout_trigger": breakout,
        "breakdown_trigger": breakdown,
        "invalidation_line": _elliott_assessment(elliott["dominant_structure"], elliott["wave_confidence"], elliott.get("invalid_rules", [])),
        "main_scenario": combined["main_scenario"],
        "alternate_scenario": combined["alternate_scenario"],

        # Legacy compat
        "ma20": round(ma20, 2), "ma60": round(ma60, 2),
        "recent_high_20d": round(recent_high, 2), "recent_low_20d": round(recent_low, 2),
        "support_levels": actual_sup_below, "resistance_levels": actual_res_above,

        # 5 methods
        "methods": {"elliott": elliott, "chan": chan, "fibonacci": fib, "gann": gann, "wyckoff": wyckoff},

        # Combined
        "combined": combined,
        "confluence_zones": combined["confluence_zones"],

        # Hard gates
        "hard_gates": {
            "gates": [
                {"gate": "Elliott: no downside-dominated structure", "passed": not elliott["exclude_from_buying"], "detail": elliott["dominant_structure"]},
                {"gate": "Chan: buy point with fractal confirmation", "passed": chan["buy_point_valid"], "detail": f"bottom_fractal={chan.get('fractal_lows_count', 0)}"},
                {"gate": "Wyckoff: 6/6 (no partial score)", "passed": wyckoff["all_six_met"], "detail": f"{wyckoff['passed_count']}/6, score={wyckoff['composite_score']}/100"},
            ],
            "all_passed": elliott["dominant_structure"] == "up" and chan["buy_point_valid"] and wyckoff["all_six_met"],
            "overall_score": combined["overall_score"],
            "signal_quality": combined["signal_quality"],
            "summary": "eligible" if (combined["overall_score"] >= 50 and not elliott["exclude_from_buying"]) else "不纳入——硬门未全过或评分低于阈值",
        },

        "disclaimer": "Educational/research use only. Not investment advice, not a buy/sell signal, no recommendation qualification claimed.",
    }

    p = OUTPUT_DIR / "support_resistance_report.json"
    p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "PASS", "data_source": src, "kline_count": n,
        "last_close": round(last_close, 2), "last_date": last["date"],
        "overall_score": combined["overall_score"],
        "signal_quality": combined["signal_quality"],
        "elliott": elliott["dominant_structure"],
        "chan": chan["trend_state"],
        "wyckoff_score": wyckoff["composite_score"],
        "confluence_zones": len(combined["confluence_zones"]),
        "json_path": str(p),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
