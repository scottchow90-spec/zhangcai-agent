from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import math
import sys
from pathlib import Path

import numpy as np


CORE_DIR = Path(r"D:\C盘转移\日志\codex\skills\stock-unified\scripts")
sys.path.insert(0, str(CORE_DIR))
import stock_strategy_backtest as core  # noqa: E402


def ema(values: np.ndarray, period: int) -> np.ndarray:
    output = np.empty(len(values), dtype=float)
    if not len(values):
        return output
    alpha = 2.0 / (period + 1.0)
    output[0] = values[0]
    for index in range(1, len(values)):
        output[index] = alpha * values[index] + (1.0 - alpha) * output[index - 1]
    return output


def rolling_mean(values: np.ndarray, period: int) -> np.ndarray:
    output = np.full(len(values), np.nan, dtype=float)
    if len(values) < period:
        return output
    cumulative = np.cumsum(np.insert(values, 0, 0.0))
    output[period - 1 :] = (cumulative[period:] - cumulative[:-period]) / period
    return output


def smooth(values: np.ndarray, period: int, weight: int = 1) -> np.ndarray:
    output = np.empty(len(values), dtype=float)
    if not len(values):
        return output
    alpha = weight / period
    output[0] = values[0]
    for index in range(1, len(values)):
        output[index] = alpha * values[index] + (1.0 - alpha) * output[index - 1]
    return output


def rolling_extreme(values: np.ndarray, period: int, mode: str) -> np.ndarray:
    output = np.full(len(values), np.nan, dtype=float)
    for index in range(period - 1, len(values)):
        window = values[index - period + 1 : index + 1]
        output[index] = np.max(window) if mode == "max" else np.min(window)
    return output


def indicator_pack(bars: list[core.Bar]) -> dict[str, np.ndarray]:
    close = np.array([bar.close for bar in bars], dtype=float)
    open_ = np.array([bar.open for bar in bars], dtype=float)
    high = np.array([bar.high for bar in bars], dtype=float)
    low = np.array([bar.low for bar in bars], dtype=float)
    amount = np.array([bar.amount for bar in bars], dtype=float)

    ema3 = ema(close, 3)
    ema5 = ema(close, 5)
    ema8 = ema(close, 8)
    ema10 = ema(close, 10)
    ema13 = ema(close, 13)
    ema20 = ema(close, 20)
    ema21 = ema(close, 21)
    main_trend = ema(ema10, 10)
    ma5 = rolling_mean(close, 5)
    ma20 = rolling_mean(close, 20)

    movement = np.diff(close, prepend=close[0])
    dx_num = ema(ema(movement, 6), 6)
    dx_den = ema(ema(np.abs(movement), 6), 6)
    dx = np.divide(dx_num * 100.0, dx_den, out=np.zeros_like(dx_num), where=dx_den != 0)
    dx_ma2 = rolling_mean(dx, 2)

    control_base = ema(ema13, 13)
    control = np.zeros(len(close), dtype=float)
    valid = control_base[:-1] != 0
    control[1:][valid] = (
        (control_base[1:][valid] - control_base[:-1][valid])
        / control_base[:-1][valid]
        * 1000.0
    )

    fortune = (ema8 - ema21) * 50.0
    fortune_slow = ema(fortune, 3)
    difference = ema(close, 12) - ema(close, 26)
    signal = ema(difference, 9)
    momentum_bar = 2.0 * (difference - signal)

    highest9 = rolling_extreme(high, 9, "max")
    lowest9 = rolling_extreme(low, 9, "min")
    spread9 = highest9 - lowest9
    raw9 = np.divide(
        (close - lowest9) * 100.0,
        spread9,
        out=np.full(len(close), 50.0),
        where=np.isfinite(spread9) & (spread9 != 0),
    )
    fast9 = smooth(raw9, 3, 1)
    slow9 = smooth(fast9, 3, 1)

    return {
        "close": close,
        "open": open_,
        "high": high,
        "low": low,
        "amount": amount,
        "ema3": ema3,
        "ema5": ema5,
        "ema10": ema10,
        "ema20": ema20,
        "ema21": ema21,
        "main": main_trend,
        "ma5": ma5,
        "ma20": ma20,
        "dx": dx,
        "dx_ma2": dx_ma2,
        "control": control,
        "fortune": fortune,
        "fortune_slow": fortune_slow,
        "momentum_bar": momentum_bar,
        "fast9": fast9,
        "slow9": slow9,
    }


def nearest_levels(
    high: np.ndarray,
    low: np.ndarray,
    close: float,
    index: int,
    main_trend: float,
    ma20: float,
) -> tuple[float, float, float, float, float]:
    start = max(2, index - 120)
    supports: list[float] = []
    pressures: list[float] = []
    if math.isfinite(main_trend) and main_trend < close:
        supports.append(float(main_trend))
    if math.isfinite(ma20) and ma20 < close:
        supports.append(float(ma20))
    for cursor in range(start, max(start, index - 1)):
        if cursor + 2 >= index:
            break
        high_window = high[cursor - 2 : cursor + 3]
        low_window = low[cursor - 2 : cursor + 3]
        if high[cursor] >= np.max(high_window) and high[cursor] > close * 1.002:
            pressures.append(float(high[cursor]))
        if low[cursor] <= np.min(low_window) and low[cursor] < close * 0.998:
            supports.append(float(low[cursor]))
    support = max(supports) if supports else float(np.min(low[max(0, index - 60) : index]))
    if pressures:
        pressure = min(pressures)
    else:
        prior_high = float(np.max(high[max(0, index - 120) : index]))
        pressure = prior_high if prior_high > close else close * 1.15
    risk = max(0.001, close / support - 1.0)
    room = max(0.0, pressure / close - 1.0)
    ratio = room / risk
    return support, pressure, risk, room, ratio


def is_recent_limit_up(
    bars: list[core.Bar],
    symbol: str,
    index: int,
    lookback: int = 13,
) -> bool:
    ratio = core.limit_ratio(symbol, "equity")
    for cursor in range(max(1, index - lookback), index):
        if bars[cursor].close / bars[cursor - 1].close - 1.0 >= ratio * 0.98:
            return True
    return False


def recent_crosses(
    bars: list[core.Bar],
    pack: dict[str, np.ndarray],
    index: int,
    lookback: int,
) -> list[dict]:
    output: list[dict] = []
    start = max(1, index - lookback + 1)
    for cursor in range(start, index + 1):
        if (
            pack["ema3"][cursor - 1] <= pack["ema21"][cursor - 1]
            and pack["ema3"][cursor] > pack["ema21"][cursor]
        ):
            output.append({
                "date": str(bars[cursor].date),
                "short_line": round(float(pack["ema3"][cursor]), 4),
                "long_line": round(float(pack["ema21"][cursor]), 4),
                "close": bars[cursor].close,
            })
    return output


def score_event(
    bars: list[core.Bar],
    symbol: str,
    index: int,
    pack: dict[str, np.ndarray],
) -> tuple[int, dict[str, int], list[str], dict[str, float]]:
    close = pack["close"]
    open_ = pack["open"]
    high = pack["high"]
    low = pack["low"]
    amount = pack["amount"]
    main = pack["main"]
    ma20 = pack["ma20"]
    dx = pack["dx"]
    dx_ma2 = pack["dx_ma2"]
    control = pack["control"]
    fortune = pack["fortune"]
    fortune_slow = pack["fortune_slow"]
    momentum_bar = pack["momentum_bar"]
    fast9 = pack["fast9"]
    slow9 = pack["slow9"]

    current_close = close[index]
    bar_range = max(high[index] - low[index], 0.01)
    body = abs(current_close - open_[index])
    upper_shadow = high[index] - max(open_[index], current_close)
    close_location = (current_close - low[index]) / bar_range
    previous_amount = amount[max(0, index - 5) : index]
    amount_base = (
        float(np.mean(previous_amount[previous_amount > 0]))
        if np.any(previous_amount > 0)
        else 0.0
    )
    amount_ratio = amount[index] / amount_base if amount_base > 0 else 1.0
    day_change = current_close / close[index - 1] - 1.0

    support, pressure, risk, room, room_ratio = nearest_levels(
        high,
        low,
        current_close,
        index,
        main[index],
        ma20[index],
    )

    direction = 0
    direction += 10 if main[index] > main[index - 1] else 0
    direction += 8 if current_close > main[index] else 0
    direction += 7 if pack["ema5"][index] > pack["ema10"][index] > pack["ema20"][index] else 0
    distance = current_close / main[index] - 1.0 if main[index] > 0 else 9.0
    direction += 5 if 0 <= distance <= 0.08 else (2 if 0.08 < distance <= 0.15 else 0)

    strength = 0
    strength += 7 if dx[index] > dx[index - 1] else 0
    strength += 5 if dx[index] > 0 else 0
    strength += 6 if control[index] > control[index - 1] else 0
    strength += 7 if fortune[index] > fortune_slow[index] else 0

    day_quality = 0
    day_quality += 6 if current_close > open_[index] else 0
    day_quality += 6 if close_location >= 0.75 else (3 if close_location >= 0.60 else 0)
    day_quality += 4 if 1.0 <= amount_ratio <= 2.5 else (2 if 0.8 <= amount_ratio <= 3.5 else 0)
    day_quality += 4 if 0.01 <= day_change <= 0.07 else (2 if 0.0 <= day_change <= 0.10 else 0)

    space = 0
    space += 7 if risk <= 0.05 else (4 if risk <= 0.08 else (2 if risk <= 0.12 else 0))
    space += 7 if room >= 0.10 else (5 if room >= 0.07 else (2 if room >= 0.04 else 0))
    space += 6 if room_ratio >= 2.0 else (4 if room_ratio >= 1.5 else (2 if room_ratio >= 1.0 else 0))

    bonus = 0
    recent_limit = is_recent_limit_up(bars, symbol, index)
    if recent_limit and current_close > pack["ma5"][index] and current_close > close[index - 1]:
        bonus += 2
    fast_cross = fast9[index - 1] <= slow9[index - 1] and fast9[index] > slow9[index]
    if fast_cross and momentum_bar[index] > momentum_bar[index - 1]:
        bonus += 2
    prior_high20 = float(np.max(high[max(0, index - 20) : index]))
    if current_close > prior_high20:
        bonus += 1

    hard_reasons: list[str] = []
    if main[index] <= main[index - 1]:
        hard_reasons.append("大方向向下")
    if current_close <= main[index]:
        hard_reasons.append("收盘仍在大方向线下方")

    recent_dx = dx[max(0, index - 6) : index + 1]
    recent_dx2 = dx[max(0, index - 1) : index + 1]
    leave_reminder = (
        len(recent_dx) >= 7
        and np.max(recent_dx2) >= np.max(recent_dx) - 1e-9
        and np.sum(recent_dx2 > 50) > 0
        and math.isfinite(dx_ma2[index - 1])
        and math.isfinite(dx_ma2[index])
        and dx_ma2[index - 1] <= dx[index - 1]
        and dx_ma2[index] > dx[index]
    )
    if leave_reminder:
        hard_reasons.append("短线力量出现离场提醒")
    if room < 0.03:
        hard_reasons.append("上方阻挡近")
    if room_ratio < 1.0:
        hard_reasons.append("上方余地不足")
    if (
        upper_shadow > max(body * 1.5, bar_range * 0.25)
        and close_location < 0.55
        and amount_ratio >= 1.8
    ):
        hard_reasons.append("当天冲高回落且成交异常放大")

    components = {
        "方向位置": direction,
        "上涨劲头": strength,
        "当天表现": day_quality,
        "上下空间": space,
        "额外提醒": bonus,
    }
    levels = {
        "support": round(float(support), 4),
        "pressure": round(float(pressure), 4),
        "risk": round(float(risk), 6),
        "room": round(float(room), 6),
        "room_ratio": round(float(room_ratio), 4),
        "amount_ratio": round(float(amount_ratio), 4),
        "day_change": round(float(day_change), 6),
    }
    return sum(components.values()), components, hard_reasons, levels
