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
from collections import Counter
import datetime as dt
import json
import math
import os
import struct
import sys
from pathlib import Path
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SKILL_DIR = Path(__file__).resolve().parents[1]
APP_ROOT = Path(__file__).resolve().parents[3]
APP_SCRIPTS = APP_ROOT / "scripts"
if str(APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(APP_SCRIPTS))
from tdx_path_config import resolve_data_root, resolve_tdx_root

TDX_ROOT = resolve_tdx_root()
VIPDOC = TDX_ROOT / "vipdoc"
REPORT_DIR = resolve_data_root() / "reports" / "baimao-teacher-system" / "stock_score"
DAY_RECORD = struct.Struct("<IIIIIfII")
REQUIRE_CURRENT_DATE = True


def expected_trade_date() -> str:
    override = os.environ.get("BAIMAO_EXPECTED_TRADE_DATE", "").strip()
    if override:
        return override.replace("-", "")
    benchmark_paths = (
        VIPDOC / "sh" / "lday" / "sh000001.day",
        VIPDOC / "sz" / "lday" / "sz399001.day",
        VIPDOC / "sz" / "lday" / "sz399006.day",
        VIPDOC / "sz" / "lday" / "sz000001.day",
        VIPDOC / "sh" / "lday" / "sh600000.day",
        VIPDOC / "sz" / "lday" / "sz300750.day",
    )
    observed_dates: list[int] = []
    for benchmark in benchmark_paths:
        try:
            if benchmark.is_file() and benchmark.stat().st_size >= DAY_RECORD.size:
                with benchmark.open("rb") as handle:
                    handle.seek(-DAY_RECORD.size, os.SEEK_END)
                    date_i, *_rest = DAY_RECORD.unpack(handle.read(DAY_RECORD.size))
                if 19900101 <= int(date_i) <= 20991231:
                    observed_dates.append(int(date_i))
        except (OSError, ValueError, struct.error):
            continue
    if observed_dates:
        date_i, _count = max(Counter(observed_dates).items(), key=lambda item: (item[1], item[0]))
        return str(date_i)
    today = dt.date.today()
    while today.weekday() >= 5:
        today -= dt.timedelta(days=1)
    return today.strftime("%Y%m%d")


def normalize_symbol(symbol: str) -> str:
    raw = symbol.strip().lower().replace(".", "").replace("_", "")
    if raw.startswith(("sh", "sz", "bj")) and len(raw) >= 8:
        return raw[:2] + raw[-6:]
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) < 6:
        raise ValueError(f"invalid symbol: {symbol}")
    code = digits[-6:]
    if code.startswith(("5", "6", "9")):
        market = "sh"
    elif code.startswith(("4", "8")):
        market = "bj"
    else:
        market = "sz"
    return market + code


def symbol_display(symbol: str) -> str:
    value = normalize_symbol(symbol)
    return value[2:] + "." + value[:2].upper()


def day_path(symbol: str) -> Path:
    value = normalize_symbol(symbol)
    market = "bj" if value.startswith("bj") else value[:2]
    candidates = [
        VIPDOC / market / "lday" / f"{value}.day",
        VIPDOC / "xinzeng" / market / "lday" / f"{value}.day",
        VIPDOC / "xinzeng" / f"{value}.day",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def parse_day(chunk: bytes) -> dict[str, Any]:
    date_i, open_i, high_i, low_i, close_i, amount, volume, _unused = DAY_RECORD.unpack(chunk)
    return {
        "date": str(date_i),
        "open": open_i / 100.0,
        "high": high_i / 100.0,
        "low": low_i / 100.0,
        "close": close_i / 100.0,
        "amount": float(amount),
        "volume": int(volume),
    }


def read_day(symbol: str, limit: int = 260) -> tuple[Path, list[dict[str, Any]]]:
    path = day_path(symbol)
    if not path.exists():
        return path, []
    count = path.stat().st_size // DAY_RECORD.size
    if count <= 0:
        return path, []
    n = min(count, limit) if limit > 0 else count
    rows: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        handle.seek((count - n) * DAY_RECORD.size)
        for _ in range(n):
            chunk = handle.read(DAY_RECORD.size)
            if len(chunk) != DAY_RECORD.size:
                break
            rows.append(parse_day(chunk))
    return path, rows


def values(rows: list[dict[str, Any]], key: str) -> list[float]:
    return [float(row[key]) for row in rows]


def safe_div(a: float, b: float, default: float = 0.0) -> float:
    return a / b if abs(b) > 0.0000001 else default


def ma(data: list[float], n: int) -> list[float]:
    out: list[float] = []
    acc = 0.0
    for i, val in enumerate(data):
        acc += val
        if i >= n:
            acc -= data[i - n]
        count = min(i + 1, n)
        out.append(acc / count)
    return out


def ema(data: list[float], n: int) -> list[float]:
    if not data:
        return []
    alpha = 2.0 / (n + 1.0)
    out = [data[0]]
    for val in data[1:]:
        out.append(alpha * val + (1.0 - alpha) * out[-1])
    return out


def sma_tdx(data: list[float], n: int, m: int) -> list[float]:
    if not data:
        return []
    out = [data[0]]
    for val in data[1:]:
        out.append((m * val + (n - m) * out[-1]) / n)
    return out


def rolling_min(data: list[float], n: int) -> list[float]:
    return [min(data[max(0, i - n + 1) : i + 1]) for i in range(len(data))]


def rolling_max(data: list[float], n: int) -> list[float]:
    return [max(data[max(0, i - n + 1) : i + 1]) for i in range(len(data))]


def ref(data: list[float], i: int, n: int, default: float | None = None) -> float:
    j = i - n
    if j < 0:
        return data[0] if default is None and data else 0.0
    return data[j]


def cross(a: list[float], b: list[float], i: int) -> bool:
    return i > 0 and a[i] > b[i] and a[i - 1] <= b[i - 1]


def recent_true(flags: list[bool], lookback: int) -> bool:
    if not flags:
        return False
    return any(flags[max(0, len(flags) - lookback) :])


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def score_row(points: float, max_points: float, title: str, facts: list[str], risks: list[str]) -> dict[str, Any]:
    return {
        "name": title,
        "score": round(clamp(points, 0, max_points), 2),
        "max_score": max_points,
        "facts": facts,
        "risks": risks,
    }


def white_rsi_score(
    c: list[float],
    h: list[float],
    l: list[float],
    v: list[float],
    capital: float | None,
) -> dict[str, Any]:
    llv10 = rolling_min(l, 10)
    hhv25 = rolling_max(h, 25)
    raw = [safe_div(c[i] - llv10[i], hhv25[i] - llv10[i]) * 4.0 for i in range(len(c))]
    trend = ema(raw, 4)
    i = len(c) - 1
    score = 0.0
    facts = [f"趋势线={trend[i]:.3f}", "超卖线=0.300", "短线卖出线=3.200", "极度风险线=3.500"]
    risks: list[str] = []
    slope = trend[i] - ref(trend, i, 3)
    if trend[i] < 0.3:
        score += 6
        facts.append("趋势线处于超卖区域")
    elif trend[i] < 1.2:
        score += 8 if slope > 0 else 5
        facts.append("趋势线处于低位修复区")
    elif trend[i] < 2.8:
        score += 6 if slope > 0 else 4
        facts.append("趋势线处于中位区")
    elif trend[i] < 3.2:
        score += 3
        facts.append("趋势线接近短线卖出线")
    else:
        risks.append("趋势线高于短线卖出线")
    if trend[i] > 3.5:
        risks.append("趋势线高于极度风险线")
        score -= 5
    if slope > 0:
        score += 3
        facts.append(f"近3日趋势线改善={slope:.3f}")
    if len(c) >= 6 and capital is not None and math.isfinite(capital) and capital > 0:
        turnover = sum(v[-5:]) / max(capital, 1.0) * 100.0 / 5.0
        if trend[i] < 1.2 and 0 < turnover < 8:
            score += 3
            facts.append(f"低位温和换手={turnover:.2f}%")
    else:
        facts.append("换手证据缺失，未提供真实流通股本，本项不加分")
    return score_row(score, 15, "白猫RSI", facts, risks)


def dujie_score(o: list[float], h: list[float], l: list[float], c: list[float]) -> dict[str, Any]:
    avg4 = [(l[i] + o[i] + c[i] + h[i]) / 4.0 for i in range(len(c))]
    var1 = [avg4[0]] + avg4[:-1]
    low_delta = [l[i] - var1[i] for i in range(len(c))]
    abs_part = sma_tdx([abs(x) for x in low_delta], 13, 1)
    pos_part = sma_tdx([max(x, 0.0) for x in low_delta], 10, 1)
    var2 = [safe_div(abs_part[i], pos_part[i], 0.0) for i in range(len(c))]
    var3 = ema(var2, 10)
    llv33 = rolling_min(l, 33)
    trigger = [var3[i] if l[i] <= llv33[i] else 0.0 for i in range(len(c))]
    var5 = ema(trigger, 3)
    i = len(c) - 1
    pick = var5[i] > ref(var5, i, 1)
    panic_down = var5[i] < ref(var5, i, 1)
    score = 0.0
    facts = [f"VAR5={var5[i]:.3f}", f"33日低点={llv33[i]:.2f}"]
    risks: list[str] = []
    if l[i] <= llv33[i] * 1.01:
        score += 4
        facts.append("价格贴近33日低点区域")
    if pick:
        score += 6
        facts.append("主力捡尸增强")
        if c[i] >= ref(c, i, 1):
            score += 3
            facts.append("承接同步收盘改善")
    if panic_down:
        facts.append("恐慌程度下降")
        score += 2 if c[i] >= ref(c, i, 1) else 0
    if pick and c[i] < ref(c, i, 1) and l[i] < ref(l, i, 1):
        risks.append("承接增强但价格继续下探")
        score -= 3
    return score_row(score, 15, "白猫渡劫", facts, risks)


def align_index(stock_rows: list[dict[str, Any]]) -> tuple[list[float], list[float], list[float], str]:
    _path, idx_rows = read_day("sh000001", 400)
    by_date = {row["date"]: row for row in idx_rows}
    ih: list[float] = []
    il: list[float] = []
    ic: list[float] = []
    mode = "sh000001"
    last: dict[str, Any] | None = None
    for row in stock_rows:
        current = by_date.get(row["date"]) or last
        if current is None:
            current = row
            mode = "stock-self"
        last = current
        ih.append(float(current["high"]))
        il.append(float(current["low"]))
        ic.append(float(current["close"]))
    return ih, il, ic, mode


def captain_score(rows: list[dict[str, Any]], o: list[float], h: list[float], l: list[float], c: list[float]) -> dict[str, Any]:
    ih, il, ic, index_mode = align_index(rows)
    range55 = [max(rolling_max(h, 55)[i] - rolling_min(l, 55)[i], 0.0001) for i in range(len(c))]
    llv55 = rolling_min(l, 55)
    kbase = [safe_div(c[i] - llv55[i], range55[i]) * 100.0 for i in range(len(c))]
    s1 = sma_tdx(kbase, 5, 1)
    s2 = sma_tdx(s1, 3, 1)
    x16 = [3 * s1[i] - 2 * s2[i] for i in range(len(c))]
    white = ema(x16, 3)
    x17 = [(white[i] - ref(white, i, 1)) / max(abs(ref(white, i, 1)), 0.0001) * 100.0 for i in range(len(c))]
    x1 = [(c[i] * 2 + h[i] + l[i]) / 4.0 * 10.0 for i in range(len(c))]
    x2 = [ema(x1, 13)[i] - ema(x1, 34)[i] for i in range(len(c))]
    x3 = ema(x2, 5)
    x4 = [2 * (x2[i] - x3[i]) * 5.5 for i in range(len(c))]
    x6 = [x if x >= 0 else 0.0 for x in x4]
    idx_range = [max(rolling_max(ih, 8)[i] - rolling_min(il, 8)[i], 0.0001) for i in range(len(c))]
    x10 = [(ic[i] * 2 + ih[i] + il[i]) / 4.0 for i in range(len(c))]
    x11 = [ema(x10, 13)[i] - ema(x10, 34)[i] for i in range(len(c))]
    x12 = ema(x11, 3)
    x13 = [(x11[i] - x12[i]) / 2.0 for i in range(len(c))]
    x14 = [x if x >= 0 else 0.0 for x in x13]
    x15 = [x if x <= 0 else 0.0 for x in x13]
    i = len(c) - 1
    score = 0.0
    facts = [f"白猫数值={white[i]:.2f}", f"指数源={index_mode}"]
    risks: list[str] = []
    if white[i] <= 13:
        score += 4
        facts.append("白猫数值处于低位区")
        if x17[i] > 13:
            score += 6
            facts.append(f"开始反弹条件成立，X17={x17[i]:.2f}")
    elif white[i] < 50:
        score += 5
        facts.append("白猫数值处于偏低修复区")
    elif white[i] < 90:
        score += 4 if white[i] > ref(white, i, 3) else 2
        facts.append("白猫数值处于中高位")
    else:
        risks.append("白猫数值处于高位风险区")
        score -= 3
    if x14[i] > 0 and white[i] < 20:
        score += 3
        facts.append("指数正向环境配合低位")
    if x6[i] > 0 and white[i] < 30:
        score += 2
        facts.append("个股动能配合低位")
    if white[i] > 90 and white[i] < ref(white, i, 1) and x6[i] < ref(x6, i, 1):
        risks.append("风险信号成立")
        score -= 7
    if x15[i] < 0 and white[i] > 90:
        risks.append("指数负向环境叠加高位")
        score -= 3
    _ = idx_range
    return score_row(score, 15, "白猫队长", facts, risks)


def duomaomao_score(c: list[float], h: list[float], l: list[float]) -> dict[str, Any]:
    delta = [0.0] + [c[i] - c[i - 1] for i in range(1, len(c))]
    m1 = sma_tdx([max(x, 0.0) for x in delta], 12, 1)
    m2 = sma_tdx([abs(x) for x in delta], 12, 1)
    d1 = [(m1[i] * 4 - m2[i]) * 50 + 50 for i in range(len(c))]
    d2 = [(m2[i] - m1[i] * 4) * 50 + 50 for i in range(len(c))]
    state = [99 if d1[i] < 50 and d2[i] > 50 else 50 for i in range(len(c))]
    i = len(c) - 1
    score = 0.0
    ret12 = (c[i] - ref(c, i, 12)) / max(ref(c, i, 12), 0.0001) * 100.0
    high20 = max(h[max(0, i - 20) : i + 1])
    draw20 = (c[i] - high20) / max(high20, 0.0001) * 100.0
    near_low20 = c[i] <= min(l[max(0, i - 20) : i + 1]) * 1.03
    facts = [
        f"躲猫猫={state[i]}",
        f"D1={d1[i]:.2f}",
        f"D2={d2[i]:.2f}",
        f"12日涨跌幅={ret12:.2f}%",
        f"20日高点回撤={draw20:.2f}%",
    ]
    risks: list[str] = []
    if state[i] == 99:
        score += 6
        facts.append("躲猫猫=99，短期超跌/疑似神秘资金抄底窗口出现")
        if ret12 <= -8 or draw20 <= -12:
            score += 4
            facts.append("K线同步满足短期超跌条件")
        if near_low20:
            score += 2
            facts.append("价格贴近20日低位区域")
        if c[i] >= ref(c, i, 1):
            score += 3
            facts.append("超跌窗口当日收盘未继续走弱")
    else:
        facts.append("躲猫猫未触发短期超跌/抄底窗口")
        if len(state) > 1 and state[i - 1] == 99:
            score += 5
            facts.append("前一日超跌窗口后转为非99，属于短线修复确认")
    if state[i] == 99 and c[i] < ref(c, i, 1) and not near_low20:
        risks.append("躲猫猫触发但价格仍未稳定")
    return score_row(score, 15, "躲猫猫", facts, risks)


def zig_state(c: list[float], pct: float = 10.0) -> dict[str, Any]:
    if len(c) < 5:
        return {"buy": False, "sell": False, "direction": 0}
    threshold = pct / 100.0
    direction = 0
    pivot = c[0]
    pivot_i = 0
    buy_flags = [False] * len(c)
    sell_flags = [False] * len(c)
    for i in range(1, len(c)):
        price = c[i]
        if direction >= 0:
            if price >= pivot:
                pivot = price
                pivot_i = i
                direction = 1
            elif safe_div(pivot - price, pivot) >= threshold:
                sell_flags[pivot_i] = True
                direction = -1
                pivot = price
                pivot_i = i
        if direction <= 0:
            if price <= pivot:
                pivot = price
                pivot_i = i
                direction = -1
            elif safe_div(price - pivot, pivot) >= threshold:
                buy_flags[pivot_i] = True
                direction = 1
                pivot = price
                pivot_i = i
    return {
        "buy": recent_true(buy_flags, 8),
        "sell": recent_true(sell_flags, 8),
        "direction": direction,
        "pivot_price": pivot,
        "pivot_index": pivot_i,
    }


def blackwhite_score(c: list[float]) -> dict[str, Any]:
    z = zig_state(c, 10.0)
    ma5 = ma(c, 5)
    ma10 = ma(c, 10)
    ma60 = ma(c, 60)
    i = len(c) - 1
    short_bear = ma5[i] < ma10[i] < ma60[i]
    score = 0.0
    facts = [f"ZIG方向={z['direction']}", f"MA5={ma5[i]:.2f}", f"MA10={ma10[i]:.2f}", f"MA60={ma60[i]:.2f}"]
    risks: list[str] = []
    if z["buy"]:
        score += 4
        facts.append("最佳买入辅助信号在近8日内出现")
        if c[i] >= ref(c, i, 1):
            score += 2
            facts.append("辅助买入后价格未走弱")
    if z["sell"]:
        risks.append("最佳卖出辅助信号在近8日内出现")
        score -= 4
    if z["sell"] and short_bear:
        risks.append("最佳卖出叠加空头排列")
        score -= 3
    if not z["buy"] and not z["sell"] and c[i] > ma10[i]:
        score += 2
        facts.append("无拐点风险且收盘站上MA10")
    return score_row(score, 5, "黑猫白猫", facts, risks)


def avg_cost_score(o: list[float], h: list[float], l: list[float], c: list[float]) -> dict[str, Any]:
    ema12 = ema(c, 12)
    ema26 = ema(c, 26)
    diff = [100.0 * (ema12[i] - ema26[i]) for i in range(len(c))]
    dea = ema(diff, 9)
    macd = [(diff[i] - dea[i]) * 2.0 for i in range(len(c))]
    gold = [cross(diff, dea, i) for i in range(len(c))]
    dead = [cross(dea, diff, i) for i in range(len(c))]
    short1 = ema(c, 10)
    short2 = ema(short1, 3)
    short3 = ema(short2, 3)
    long1 = ema(c, 45)
    long2 = ema(long1, 3)
    ma30_ref = ma([max(o[i], h[i], l[i], c[i]) for i in range(len(c))], 30)
    i = len(c) - 1
    recent_low = min(l[max(0, i - 20) : i + 1])
    prior_lows = l[max(0, i - 80) : max(1, i - 20)]
    prior_diff = diff[max(0, i - 80) : max(1, i - 20)]
    bottom_like = bool(prior_lows and prior_diff and recent_true(gold, 6) and recent_low <= min(prior_lows) * 1.03 and min(diff[max(0, i - 20) : i + 1]) >= min(prior_diff) * 0.98)
    top_like = bool(prior_lows and recent_true(dead, 6) and max(h[max(0, i - 20) : i + 1]) >= max(h[max(0, i - 80) : max(1, i - 20)] or [h[i]]) * 0.98 and max(diff[max(0, i - 20) : i + 1]) <= max(prior_diff or [diff[i]]) * 1.02)
    score = 0.0
    facts = [f"DIFF={diff[i]:.2f}", f"DEA={dea[i]:.2f}", f"MACD={macd[i]:.2f}", f"短期1={short1[i]:.2f}", f"长期1={long1[i]:.2f}"]
    risks: list[str] = []
    if bottom_like:
        score += 8
        facts.append("底部结构条件成立")
    if c[i] > short1[i]:
        score += 4
        facts.append("收盘站上短期1")
    if short1[i] > short2[i] > short3[i] or short1[i] > ref(short1, i, 3):
        score += 5
        facts.append("短期EMA组改善")
    if short1[i] > long1[i] or long1[i] >= ref(long1, i, 5):
        score += 4
        facts.append("长期EMA骨架不弱")
    if recent_true(gold, 5):
        score += 4
        facts.append("近5日DIFF上穿DEA")
    if c[i] > ma30_ref[i] and c[i] > o[i]:
        score += 2
        facts.append("突破TYX3类结构参考线")
    if top_like:
        risks.append("顶部结构条件成立")
        score -= 8
    if short1[i] < long1[i] and c[i] < long1[i]:
        risks.append("价格仍受长期EMA压制")
        score -= 3
    if c[i] < recent_low * 1.01 and macd[i] < 0:
        risks.append("价格贴近阶段低点且MACD为负")
        score -= 3
    return score_row(score, 25, "平均成本线", facts, risks)


def resonance_score(modules: list[dict[str, Any]]) -> dict[str, Any]:
    positive = [m for m in modules if m["score"] / m["max_score"] >= 0.6]
    risk_hits = [risk for m in modules for risk in m["risks"]]
    main_ok = any(m["name"] == "平均成本线" and m["score"] >= 15 for m in modules)
    score = 0.0
    facts = [f"正向模块数={len(positive)}", f"主图确认={main_ok}"]
    risks: list[str] = []
    if main_ok and len(positive) >= 5:
        score = 10
        facts.append("五项以上同向且主图支持")
    elif main_ok and len(positive) >= 4:
        score = 6
        facts.append("四项同向且主图支持")
    elif len(positive) >= 3:
        score = 3
        facts.append("三项同向")
    if any("顶部结构" in x or "风险信号" in x or "最佳卖出" in x for x in risk_hits):
        risks.append("强风险信号限制共振分")
        score = min(score, 3)
    return score_row(score, 10, "六公式共振", facts, risks)


def rating(total: float) -> str:
    if total >= 85:
        return "A 强共振"
    if total >= 70:
        return "B 可观察"
    if total >= 55:
        return "C 弱修复"
    if total >= 40:
        return "D 风险偏高"
    return "E 排除"


def conclusion(total: float, modules: list[dict[str, Any]], latest: dict[str, Any]) -> str:
    r = rating(total)
    if r.startswith("A"):
        return "六公式高度共振，具备重点跟踪价值，仍需公告、基本面和市场环境复核。"
    if r.startswith("B"):
        return "多数模块转好，归入B级可跟踪状态，后续以短板模块补齐为升级条件。"
    if r.startswith("C"):
        return "存在局部修复信号，但共振不足，暂按跟踪处理。"
    if r.startswith("D"):
        return "趋势或风险项压制明显，不适合作为优先对象。"
    _ = modules
    _ = latest
    return "六公式综合状态偏弱，应从候选池剔除。"


def score_symbol(symbol: str, limit: int = 260) -> dict[str, Any]:
    path, rows = read_day(symbol, limit)
    if len(rows) < 90:
        return {
            "ok": False,
            "symbol": symbol_display(symbol),
            "path": str(path),
            "records": len(rows),
            "status": "DATA_BLOCKED",
            "error": "daily kline records less than 90",
        }
    latest = rows[-1]
    expected_date = expected_trade_date()
    if REQUIRE_CURRENT_DATE and latest["date"] != expected_date:
        return {
            "ok": False,
            "symbol": symbol_display(symbol),
            "normalized_symbol": normalize_symbol(symbol),
            "path": str(path),
            "records": len(rows),
            "status": "DATA_STALE",
            "expected_trade_date": expected_date,
            "latest_effective_trade_date": latest["date"],
            "error": "daily kline is not current; scoring conclusion is blocked",
            "data_gate": {
                "tdx_root": str(TDX_ROOT),
                "records": len(rows),
                "expected_trade_date": expected_date,
                "latest_effective_trade_date": latest["date"],
                "data_source": str(path),
            },
        }
    o = values(rows, "open")
    h = values(rows, "high")
    l = values(rows, "low")
    c = values(rows, "close")
    v = values(rows, "volume")
    modules = [
        avg_cost_score(o, h, l, c),
        white_rsi_score(c, h, l, v, None),
        dujie_score(o, h, l, c),
        captain_score(rows, o, h, l, c),
        duomaomao_score(c, h, l),
        blackwhite_score(c),
    ]
    res = resonance_score(modules)
    modules.append(res)
    total = round(sum(m["score"] for m in modules), 2)
    strengths = [m["name"] for m in modules if m["score"] / m["max_score"] >= 0.6]
    weaknesses = [m["name"] for m in modules if m["score"] / m["max_score"] < 0.4]
    risks = [risk for m in modules for risk in m["risks"]]
    support = min(l[-20:])
    resistance = max(h[-20:])
    payload = {
        "ok": True,
        "status": "CLEAN_PASS",
        "symbol": symbol_display(symbol),
        "normalized_symbol": normalize_symbol(symbol),
        "kline_path": str(path),
        "trade_date": latest["date"],
        "latest": latest,
        "score": total,
        "score_contract": {
            "version": "BAIMAO-SCORE-100-V2",
            "scale": 100,
            "component_max_total": 100,
            "missing_evidence_policy": "zero_without_renormalization",
            "turnover_policy": "requires_verified_float_share_capital",
            "risk_policy": "module_deductions_and_resonance_cap",
        },
        "rating": rating(total),
        "conclusion": conclusion(total, modules, latest),
        "modules": modules,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "risks": risks,
        "levels": {
            "support_20d": round(support, 2),
            "resistance_20d": round(resistance, 2),
            "invalidation": round(support * 0.99, 2),
            "trigger": round(resistance * 1.01, 2),
        },
        "data_gate": {
            "tdx_root": str(TDX_ROOT),
            "records": len(rows),
            "expected_trade_date": expected_date,
            "latest_effective_trade_date": latest["date"],
            "data_source": str(path),
        },
    }
    return payload


def write_markdown(payload: dict[str, Any], out: Path) -> None:
    lines = [
        f"# 白猫老师体系个股评分报告：{payload['symbol']}",
        "",
        f"- 日期：{payload['trade_date']}",
        f"- 总分：{payload['score']}/100",
        f"- 等级：{payload['rating']}",
        f"- 结论：{payload['conclusion']}",
        f"- 数据源：{payload['kline_path']}",
        "",
        "## 模块评分",
        "",
        "| 模块 | 得分 | 满分 | 事实 | 风险 |",
        "|---|---:|---:|---|---|",
    ]
    for module in payload["modules"]:
        facts = "；".join(module["facts"])
        risks = "；".join(module["risks"]) if module["risks"] else "无"
        lines.append(f"| {module['name']} | {module['score']} | {module['max_score']} | {facts} | {risks} |")
    lines.extend([
        "",
        "## 关键价位",
        "",
        f"- 20日支撑：{payload['levels']['support_20d']}",
        f"- 20日压力：{payload['levels']['resistance_20d']}",
        f"- 失效线：{payload['levels']['invalidation']}",
        f"- 触发线：{payload['levels']['trigger']}",
        "",
        "## 风险",
        "",
    ])
    if payload["risks"]:
        for risk in payload["risks"]:
            lines.append(f"- {risk}")
    else:
        lines.append("- 六公式层面未出现强风险项。")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_score(args: argparse.Namespace) -> int:
    payload = score_symbol(args.symbol, args.limit)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 2


def cmd_report(args: argparse.Namespace) -> int:
    payload = score_symbol(args.symbol, args.limit)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"{payload.get('normalized_symbol', normalize_symbol(args.symbol))}_{payload.get('trade_date', dt.date.today().isoformat())}"
    json_path = REPORT_DIR / f"{stem}.json"
    md_path = REPORT_DIR / f"{stem}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if payload.get("ok"):
        write_markdown(payload, md_path)
    result = {
        "ok": payload.get("ok", False),
        "symbol": payload.get("symbol"),
        "score": payload.get("score"),
        "rating": payload.get("rating"),
        "json": str(json_path),
        "markdown": str(md_path) if md_path.exists() else None,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def cmd_batch(args: argparse.Namespace) -> int:
    symbols = args.symbols
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8-sig", errors="ignore")
        symbols.extend([x.strip() for x in text.replace(",", "\n").splitlines() if x.strip()])
    results = [score_symbol(symbol, args.limit) for symbol in symbols]
    rows = sorted([r for r in results if r.get("ok")], key=lambda x: x.get("score", 0), reverse=True)
    payload = {
        "ok": bool(rows),
        "count": len(results),
        "pass_count": len(rows),
        "blocked": [r for r in results if not r.get("ok")],
        "ranking": [
            {
                "rank": i + 1,
                "symbol": row["symbol"],
                "trade_date": row["trade_date"],
                "score": row["score"],
                "rating": row["rating"],
                "strengths": row["strengths"],
                "risks": row["risks"],
            }
            for i, row in enumerate(rows)
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if rows else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="白猫老师体系个股六公式评分引擎")
    sub = parser.add_subparsers(dest="cmd", required=True)
    score = sub.add_parser("score")
    score.add_argument("symbol")
    score.add_argument("--limit", type=int, default=260)
    score.set_defaults(func=cmd_score)
    report = sub.add_parser("report")
    report.add_argument("symbol")
    report.add_argument("--limit", type=int, default=260)
    report.set_defaults(func=cmd_report)
    batch = sub.add_parser("batch")
    batch.add_argument("symbols", nargs="*")
    batch.add_argument("--file", default="")
    batch.add_argument("--limit", type=int, default=260)
    batch.set_defaults(func=cmd_batch)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
