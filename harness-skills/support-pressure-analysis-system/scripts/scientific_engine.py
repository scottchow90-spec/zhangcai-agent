#!/usr/bin/env python3
"""Causal, validation-aware support/resistance and technical-analysis engine.

The engine deliberately separates four things that older implementations mixed:
data quality, deterministic level construction, historical validation, and the
current conditional conclusion.  Evidence scores are not return probabilities.
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
import datetime as dt
import hashlib
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_data_root, resolve_tdx_root


SKILL = "support-pressure-analysis-system"
ENGINE_VERSION = "5.1.0"
METHODOLOGY = "causal-sr-five-theory-full-history-walk-forward-cross-sectional-gated-v4"
PARAMETER_SET_ID = "confirmed-structure-active-swing-h10-five-theory-v2"
FULL_HISTORY_CONTRACT_ID = "tdx-full-local-file-all-confirmed-pivots-v1"
FIVE_THEORY_VALIDATION_SCHEMA = "FIVE_THEORY_REAL_KLINE_VALIDATION_V1"
FIVE_THEORY_RECEIPT_SCHEMA = "FIVE_THEORY_REAL_KLINE_VALIDATION_RECEIPT_V1"
THEORY_METHODS = ("elliott_wave", "chan_structure", "fibonacci", "gann", "wyckoff")
PREDECESSOR_VALIDATION_RECEIPT = {
    "path": None,
    "availability": "historical_reference_not_bundled",
    "sha256": "b767773a788d968138efb6140fdbf74d3f8f820b50376c020c01f5ceedbc04ef",
}
PREDECESSOR_VALIDATION_SYMBOLS = {
    "603489.SH", "600029.SH", "603899.SH", "600878.SH", "688646.SH", "688118.SH", "688716.SH", "688069.SH",
    "000622.SZ", "002435.SZ", "002867.SZ", "002948.SZ", "300750.SZ", "300741.SZ", "300427.SZ", "300836.SZ",
    "920403.BJ", "920028.BJ", "920751.BJ", "920261.BJ", "600857.SH", "603261.SH", "601366.SH", "600126.SH",
    "688363.SH", "688041.SH", "688271.SH", "688707.SH", "000951.SZ", "000876.SZ", "002645.SZ", "002673.SZ",
    "300003.SZ", "300472.SZ", "300982.SZ", "300763.SZ", "920016.BJ", "920080.BJ", "920011.BJ", "920627.BJ",
}
ROOT = Path(__file__).resolve().parents[1]
REPORTS_ROOT = resolve_data_root() / "runtime" / "skills" / "support-pressure-analysis-system" / "reports"
TDX_ROOT = resolve_tdx_root()
_skills_root_text = os.environ.get("STOCK_SKILLS_ROOT", str(ROOT.parent))
TDX_HUB = Path(os.environ.get("TDX_HUB_PATH") or Path(_skills_root_text) / "tdx-local-hub" / "scripts" / "tdx_hub.py").expanduser().resolve()
TDX_VIPDOC = Path(os.environ.get("TDX_VIPDOC_ROOT") or TDX_ROOT / "vipdoc").expanduser().resolve()
CALIBRATION_PATH = ROOT / "references" / "cross_sectional_calibration.json"
HARD_MIN_BARS = 80
RECOMMENDED_MIN_BARS = 250


class AnalysisBlocked(ValueError):
    """Raised when data cannot support a defensible analysis."""


def _finite(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite numeric value: {value!r}")
    return number


def _date(value: Any) -> str:
    raw = str(value).strip().replace("/", "-")
    if raw.isdigit() and len(raw) == 8:
        raw = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return dt.date.fromisoformat(raw[:10]).isoformat()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _round(value: float | None, digits: int = 4) -> float | None:
    return None if value is None else round(float(value), digits)


def normalize_rows(raw_rows: Iterable[dict[str, Any]], min_bars: int = HARD_MIN_BARS) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    for index, raw in enumerate(raw_rows):
        try:
            volume_value = raw.get("volume", raw.get("vol", 0))
            row = {
                "date": _date(raw.get("date", raw.get("datetime"))),
                "open": _finite(raw["open"]),
                "high": _finite(raw["high"]),
                "low": _finite(raw["low"]),
                "close": _finite(raw["close"]),
                "volume": max(0.0, _finite(volume_value or 0)),
                "amount": max(0.0, _finite(raw.get("amount", 0) or 0)),
            }
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"row_{index}:{type(exc).__name__}:{exc}")
            continue
        if min(row["open"], row["high"], row["low"], row["close"]) <= 0:
            errors.append(f"row_{index}:non_positive_price")
        if row["high"] < max(row["open"], row["close"], row["low"]):
            errors.append(f"row_{index}:high_inconsistent")
        if row["low"] > min(row["open"], row["close"], row["high"]):
            errors.append(f"row_{index}:low_inconsistent")
        rows.append(row)

    if len(rows) < min_bars:
        errors.append(f"insufficient_bars:{len(rows)}<{min_bars}")
    dates = [row["date"] for row in rows]
    if dates != sorted(dates):
        errors.append("dates_not_strictly_ascending")
    if len(set(dates)) != len(dates):
        errors.append("duplicate_dates")

    discontinuities: list[dict[str, Any]] = []
    for index in range(1, len(rows)):
        ratio = rows[index]["close"] / rows[index - 1]["close"]
        if ratio <= 0 or abs(math.log(ratio)) > math.log(1.35):
            discontinuities.append(
                {
                    "date": rows[index]["date"],
                    "previous_close": _round(rows[index - 1]["close"]),
                    "close": _round(rows[index]["close"]),
                    "change_ratio": _round(ratio - 1),
                }
            )
    if discontinuities:
        errors.append("possible_unadjusted_corporate_action_or_bad_tick")

    zero_volume_ratio = (
        sum(1 for row in rows if row["volume"] <= 0) / len(rows) if rows else 1.0
    )
    if zero_volume_ratio > 0.2:
        warnings.append("volume_missing_or_zero_for_more_than_20pct")
    if len(rows) < RECOMMENDED_MIN_BARS:
        warnings.append(f"short_history:{len(rows)}<{RECOMMENDED_MIN_BARS}")

    quality = {
        "status": "BLOCKED" if errors else ("DEGRADED" if warnings else "PASS"),
        "bar_count": len(rows),
        "start_date": rows[0]["date"] if rows else None,
        "end_date": rows[-1]["date"] if rows else None,
        "errors": errors,
        "warnings": warnings,
        "zero_volume_ratio": _round(zero_volume_ratio),
        "discontinuities": discontinuities,
    }
    if errors:
        raise AnalysisBlocked(json.dumps(quality, ensure_ascii=False))
    return rows, quality


def _large_scale_change(ratio: float) -> bool:
    return ratio > 0 and max(ratio, 1.0 / ratio) > 1.35


def prepare_tdx_history(raw_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Prepare unadjusted local TDX history without hiding unresolved bad data."""
    rows = [dict(row) for row in raw_rows]
    envelope_repairs: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        try:
            open_value = _finite(row["open"])
            high_value = _finite(row["high"])
            low_value = _finite(row["low"])
            close_value = _finite(row["close"])
        except (KeyError, TypeError, ValueError):
            continue
        required_high = max(open_value, close_value, low_value)
        if high_value < required_high:
            row["high"] = required_high
            envelope_repairs.append({
                "row_index": index,
                "date": str(row.get("date", row.get("datetime", ""))),
                "field": "high",
                "original_value": high_value,
                "repaired_value": required_high,
                "rule": "max_existing_open_close_low",
            })
            high_value = required_high
        required_low = min(open_value, close_value, high_value)
        if low_value > required_low:
            row["low"] = required_low
            envelope_repairs.append({
                "row_index": index,
                "date": str(row.get("date", row.get("datetime", ""))),
                "field": "low",
                "original_value": low_value,
                "repaired_value": required_low,
                "rule": "min_existing_open_close_high",
            })

    adjustment_events: list[dict[str, Any]] = []
    unresolved_breaks: list[dict[str, Any]] = []
    for index in range(1, len(rows)):
        try:
            previous_close = _finite(rows[index - 1]["close"])
            current_open = _finite(rows[index]["open"])
            current_close = _finite(rows[index]["close"])
        except (KeyError, TypeError, ValueError):
            continue
        if previous_close <= 0 or current_open <= 0 or current_close <= 0:
            continue
        close_ratio = current_close / previous_close
        if not _large_scale_change(close_ratio):
            continue

        prior_start = max(0, index - 3)
        following_end = min(len(rows), index + 3)
        try:
            prior_median = statistics.median(
                _finite(row["close"]) for row in rows[prior_start:index]
            )
            following_median = statistics.median(
                _finite(row["close"]) for row in rows[index:following_end]
            )
        except (KeyError, TypeError, ValueError, statistics.StatisticsError):
            prior_median = 0.0
            following_median = 0.0
        persistent_ratio = following_median / prior_median if prior_median > 0 else 0.0
        open_ratio = current_open / previous_close
        same_direction = (
            (close_ratio < 1.0 and open_ratio < 1.0 and persistent_ratio < 1.0)
            or (close_ratio > 1.0 and open_ratio > 1.0 and persistent_ratio > 1.0)
        )
        persistent_scale = (
            following_end - index >= 3
            and index - prior_start >= 3
            and _large_scale_change(open_ratio)
            and _large_scale_change(persistent_ratio)
            and same_direction
        )
        evidence = {
            "row_index": index,
            "date": str(rows[index].get("date", rows[index].get("datetime", ""))),
            "previous_date": str(rows[index - 1].get("date", rows[index - 1].get("datetime", ""))),
            "previous_close": previous_close,
            "current_open": current_open,
            "current_close": current_close,
            "close_ratio": _round(close_ratio, 12),
            "open_ratio": _round(open_ratio, 12),
            "prior_three_close_median": _round(prior_median, 12),
            "following_three_close_median": _round(following_median, 12),
            "persistent_scale_ratio": _round(persistent_ratio, 12),
            "persistence_confirmed": persistent_scale,
        }
        if not persistent_scale:
            unresolved_breaks.append({
                **evidence,
                "reason": "large_change_not_confirmed_as_persistent_tdx_scale_change",
            })
            continue

        factor = open_ratio
        for prior_row in rows[:index]:
            for field in ("open", "high", "low", "close"):
                prior_row[field] = _finite(prior_row[field]) * factor
        adjustment_events.append({
            **evidence,
            "method": "back_adjust_prior_history_to_current_tdx_price_scale",
            "adjustment_factor": _round(factor, 12),
            "adjusted_field_names": ["open", "high", "low", "close"],
            "adjusted_record_start_index": 0,
            "adjusted_record_end_index": index - 1,
            "adjusted_record_count": index,
            "adjusted_start_date": str(rows[0].get("date", rows[0].get("datetime", ""))),
            "adjusted_end_date": str(rows[index - 1].get("date", rows[index - 1].get("datetime", ""))),
        })

    audit = {
        "schema": "TDX_HISTORY_PREPARATION_V1",
        "status": "BLOCKED" if unresolved_breaks else "PASS",
        "source_scope": "tdx_local_hub_only",
        "input_record_count": len(raw_rows),
        "output_record_count": len(rows),
        "all_records_preserved": len(rows) == len(raw_rows),
        "input_rows_mutated": False,
        "ohlc_envelope_repair_count": len(envelope_repairs),
        "ohlc_envelope_repairs": envelope_repairs,
        "price_adjustment_event_count": len(adjustment_events),
        "price_adjustment_events": adjustment_events,
        "unresolved_scale_break_count": len(unresolved_breaks),
        "unresolved_scale_breaks": unresolved_breaks,
    }
    return rows, audit


def _sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def _ema_series(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2.0 / (period + 1.0)
    result = [values[0]]
    for value in values[1:]:
        result.append(alpha * value + (1.0 - alpha) * result[-1])
    return result


def _atr_series(rows: list[dict[str, Any]], period: int = 14) -> list[float | None]:
    if not rows:
        return []
    true_ranges = [rows[0]["high"] - rows[0]["low"]]
    for index in range(1, len(rows)):
        previous_close = rows[index - 1]["close"]
        true_ranges.append(
            max(
                rows[index]["high"] - rows[index]["low"],
                abs(rows[index]["high"] - previous_close),
                abs(rows[index]["low"] - previous_close),
            )
        )
    result: list[float | None] = [None] * len(rows)
    if len(rows) < period:
        return result
    result[period - 1] = sum(true_ranges[:period]) / period
    for index in range(period, len(rows)):
        result[index] = ((result[index - 1] or 0.0) * (period - 1) + true_ranges[index]) / period
    return result


def _rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for index in range(1, len(values)):
        delta = values[index] - values[index - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for index in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[index]) / period
        avg_loss = (avg_loss * (period - 1) + losses[index]) / period
    if avg_loss == 0:
        return 100.0
    relative = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + relative)


def _adx(rows: list[dict[str, Any]], period: int = 14) -> float | None:
    if len(rows) < period * 2 + 1:
        return None
    trs: list[float] = []
    plus_dm: list[float] = []
    minus_dm: list[float] = []
    for index in range(1, len(rows)):
        up = rows[index]["high"] - rows[index - 1]["high"]
        down = rows[index - 1]["low"] - rows[index]["low"]
        plus_dm.append(up if up > down and up > 0 else 0.0)
        minus_dm.append(down if down > up and down > 0 else 0.0)
        previous_close = rows[index - 1]["close"]
        trs.append(
            max(
                rows[index]["high"] - rows[index]["low"],
                abs(rows[index]["high"] - previous_close),
                abs(rows[index]["low"] - previous_close),
            )
        )
    tr_sum = sum(trs[:period])
    plus_sum = sum(plus_dm[:period])
    minus_sum = sum(minus_dm[:period])
    dx_values: list[float] = []
    for index in range(period, len(trs)):
        tr_sum = tr_sum - tr_sum / period + trs[index]
        plus_sum = plus_sum - plus_sum / period + plus_dm[index]
        minus_sum = minus_sum - minus_sum / period + minus_dm[index]
        plus_di = 100.0 * plus_sum / tr_sum if tr_sum else 0.0
        minus_di = 100.0 * minus_sum / tr_sum if tr_sum else 0.0
        denominator = plus_di + minus_di
        dx_values.append(100.0 * abs(plus_di - minus_di) / denominator if denominator else 0.0)
    return sum(dx_values[-period:]) / min(period, len(dx_values)) if dx_values else None


def technical_context(rows: list[dict[str, Any]], atr_values: list[float | None]) -> dict[str, Any]:
    closes = [row["close"] for row in rows]
    ema12 = _ema_series(closes, 12)
    ema20 = _ema_series(closes, 20)
    ema26 = _ema_series(closes, 26)
    ema50 = _ema_series(closes, 50)
    ema200 = _ema_series(closes, 200)
    macd_values = [a - b for a, b in zip(ema12, ema26)]
    macd_signal = _ema_series(macd_values, 9)
    atr = atr_values[-1] or max(rows[-1]["high"] - rows[-1]["low"], closes[-1] * 0.01)
    slope = (ema20[-1] - ema20[-6]) / (5.0 * atr) if len(ema20) >= 6 and atr else 0.0
    last = closes[-1]
    if last > ema20[-1] > ema50[-1] and slope > 0.03:
        regime = "uptrend"
    elif last < ema20[-1] < ema50[-1] and slope < -0.03:
        regime = "downtrend"
    else:
        regime = "range_or_transition"
    adx = _adx(rows)
    if adx is None:
        strength = "not_available"
    elif adx >= 30:
        strength = "strong"
    elif adx >= 20:
        strength = "moderate"
    else:
        strength = "weak_or_range"
    volumes = [row["volume"] for row in rows]
    volume_ma20 = _sma(volumes, 20)
    volume_ratio = volumes[-1] / volume_ma20 if volume_ma20 and volume_ma20 > 0 else None
    return {
        "regime": regime,
        "trend_strength_descriptor": strength,
        "close": _round(last),
        "ema20": _round(ema20[-1]),
        "ema50": _round(ema50[-1]),
        "ema200": _round(ema200[-1]) if len(rows) >= 200 else None,
        "ema20_slope_atr_per_bar": _round(slope),
        "macd": _round(macd_values[-1]),
        "macd_signal": _round(macd_signal[-1]),
        "macd_histogram": _round(macd_values[-1] - macd_signal[-1]),
        "rsi14": _round(_rsi(closes)),
        "adx14": _round(adx),
        "atr14": _round(atr),
        "atr_percent": _round(atr / last if last else None),
        "volume_ratio_20": _round(volume_ratio),
        "interpretation_rule": "Indicators describe state; they are not independently treated as predictive evidence.",
    }


def _confirmed_pivots(rows: list[dict[str, Any]], atr_values: list[float | None]) -> list[dict[str, Any]]:
    pivots: list[dict[str, Any]] = []
    for width, base_weight in ((2, 0.8), (5, 1.2), (10, 1.6)):
        for index in range(width, len(rows) - width):
            neighborhood = rows[index - width : index + width + 1]
            high = rows[index]["high"]
            low = rows[index]["low"]
            atr = atr_values[index] or max(high - low, rows[index]["close"] * 0.01)
            if high == max(row["high"] for row in neighborhood) and any(
                high > row["high"] for row in neighborhood if row is not rows[index]
            ):
                local_floor = min(row["low"] for row in neighborhood)
                pivots.append(
                    {
                        "level": high,
                        "family": "confirmed_pivot",
                        "label": f"pivot_high_w{width}",
                        "index": index,
                        "weight": base_weight * (1.0 + min((high - local_floor) / atr, 3.0) / 3.0),
                    }
                )
            if low == min(row["low"] for row in neighborhood) and any(
                low < row["low"] for row in neighborhood if row is not rows[index]
            ):
                local_ceiling = max(row["high"] for row in neighborhood)
                pivots.append(
                    {
                        "level": low,
                        "family": "confirmed_pivot",
                        "label": f"pivot_low_w{width}",
                        "index": index,
                        "weight": base_weight * (1.0 + min((local_ceiling - low) / atr, 3.0) / 3.0),
                    }
                )
    return pivots


def _alternating_pivots(rows: list[dict[str, Any]], atr_values: list[float | None], width: int = 2) -> list[dict[str, Any]]:
    """Return temporally ordered, right-confirmed, alternating swing points."""
    raw: list[dict[str, Any]] = []
    suffix = f"w{width}"
    for item in _confirmed_pivots(rows, atr_values):
        if not item["label"].endswith(suffix):
            continue
        raw.append(
            {
                "index": int(item["index"]),
                "date": rows[int(item["index"])]["date"],
                "kind": "H" if "high" in item["label"] else "L",
                "level": float(item["level"]),
                "confirmed": int(item["index"]) <= len(rows) - width - 1,
                "confirmation_index": int(item["index"]) + width,
            }
        )
    raw.sort(key=lambda point: (point["index"], point["kind"]))
    alternating: list[dict[str, Any]] = []
    for point in raw:
        if alternating and point["index"] == alternating[-1]["index"]:
            last = alternating[-1]
            atr = atr_values[point["index"]] or max(rows[point["index"]]["close"] * 0.01, 1e-9)
            high_distance = abs(rows[point["index"]]["high"] - rows[point["index"]]["close"]) / atr
            low_distance = abs(rows[point["index"]]["close"] - rows[point["index"]]["low"]) / atr
            preferred = "H" if high_distance >= low_distance else "L"
            if point["kind"] == preferred:
                alternating[-1] = point
            continue
        if alternating and point["kind"] == alternating[-1]["kind"]:
            last = alternating[-1]
            more_extreme = point["level"] > last["level"] if point["kind"] == "H" else point["level"] < last["level"]
            if more_extreme:
                alternating[-1] = point
            continue
        alternating.append(point)
    return alternating


def _theory_level(method: str, label: str, level: float, index: int, weight: float) -> dict[str, Any]:
    return {
        "level": float(level),
        "family": "theory_formalized",
        "method": method,
        "label": f"{method}:{label}",
        "index": int(index),
        "weight": float(weight),
    }


def elliott_subsystem(rows: list[dict[str, Any]], atr_values: list[float | None]) -> dict[str, Any]:
    """Operationalized, bidirectional Elliott impulse detection on confirmed pivots."""
    pivots = _alternating_pivots(rows, atr_values, 2)
    patterns: list[dict[str, Any]] = []
    candidate_window_count = max(0, len(pivots) - 5)
    for start in range(candidate_window_count):
        points = pivots[start : start + 6]
        kinds = "".join(point["kind"] for point in points)
        if kinds not in {"LHLHLH", "HLHLHL"}:
            continue
        direction = "up" if kinds == "LHLHLH" else "down"
        levels = [float(point["level"]) for point in points]
        if direction == "up":
            impulse_sizes = [levels[1] - levels[0], levels[3] - levels[2], levels[5] - levels[4]]
            rules = {
                "wave2_not_beyond_origin": levels[2] > levels[0],
                "wave3_exceeds_wave1": levels[3] > levels[1],
                "wave3_not_shortest": impulse_sizes[1] >= min(impulse_sizes[0], impulse_sizes[2]),
                "wave4_no_wave1_overlap": levels[4] > levels[1],
                "wave5_exceeds_wave3": levels[5] > levels[3],
            }
        else:
            impulse_sizes = [levels[0] - levels[1], levels[2] - levels[3], levels[4] - levels[5]]
            rules = {
                "wave2_not_beyond_origin": levels[2] < levels[0],
                "wave3_exceeds_wave1": levels[3] < levels[1],
                "wave3_not_shortest": impulse_sizes[1] >= min(impulse_sizes[0], impulse_sizes[2]),
                "wave4_no_wave1_overlap": levels[4] < levels[1],
                "wave5_exceeds_wave3": levels[5] < levels[3],
            }
        passed = sum(bool(value) for value in rules.values())
        patterns.append(
            {
                "direction": direction,
                "wave_points": points,
                "rules": rules,
                "rules_passed": passed,
                "complete": passed == len(rules),
                "recency": points[-1]["index"],
            }
        )
    current = max(patterns, key=lambda item: item["recency"], default=None)
    historical_best = max(
        patterns,
        key=lambda item: (item["complete"], item["rules_passed"], item["recency"]),
        default=None,
    )
    wave_points = current["wave_points"] if current else pivots[-6:]
    direction = current["direction"] if current else (
        "up" if len(pivots) >= 2 and pivots[-1]["level"] > pivots[-2]["level"] else
        "down" if len(pivots) >= 2 and pivots[-1]["level"] < pivots[-2]["level"] else "unclear"
    )
    candidates = [
        _theory_level("elliott_wave", f"wave_point_{offset}", point["level"], point["index"], 0.45)
        for offset, point in enumerate(wave_points, start=0)
    ]
    score = 20.0 if not current else current["rules_passed"] / len(current["rules"]) * 100.0
    return {
        "status": "PASS",
        "active_in_main_chain": True,
        "input_bar_count": len(rows),
        "input_start_date": rows[0]["date"] if rows else None,
        "input_end_date": rows[-1]["date"] if rows else None,
        "search_scope": "ALL_CONFIRMED_ALTERNATING_PIVOTS",
        "confirmed_pivot_count": len(pivots),
        "candidate_window_count": candidate_window_count,
        "complete_pattern_count": sum(1 for item in patterns if item["complete"]),
        "historical_best_rules_passed": historical_best["rules_passed"] if historical_best else 0,
        "current_pattern_selection_rule": "LATEST_RIGHT_CONFIRMED_SIX_PIVOT_WINDOW",
        "structure_state": "complete_impulse" if current and current["complete"] else "no_complete_impulse",
        "direction": direction,
        "wave_points": wave_points,
        "rule_validation": current["rules"] if current else {},
        "evidence_score_not_probability": _round(score),
        "candidate_levels": candidates,
        "limitations": [
            "Only right-confirmed pivots are used, so the newest unconfirmed swing is excluded.",
            "Wave labels are deterministic structural context, not a directional probability or trade signal.",
        ],
    }


def chan_subsystem(rows: list[dict[str, Any]], atr_values: list[float | None]) -> dict[str, Any]:
    """Operationalized Chan structure: confirmed fractals, alternating strokes and central zones."""
    fractals = _alternating_pivots(rows, atr_values, 2)
    strokes: list[dict[str, Any]] = []
    for left, right in zip(fractals, fractals[1:]):
        if left["kind"] == right["kind"] or right["index"] - left["index"] < 2:
            continue
        atr = atr_values[right["index"]] or max(rows[right["index"]]["close"] * 0.01, 1e-9)
        move_atr = abs(right["level"] - left["level"]) / atr
        if move_atr < 0.35:
            continue
        strokes.append(
            {
                "start_index": left["index"],
                "end_index": right["index"],
                "start_level": left["level"],
                "end_level": right["level"],
                "direction": "up" if right["level"] > left["level"] else "down",
                "move_atr": _round(move_atr),
                "confirmed": right["confirmed"],
            }
        )
    central_zones: list[dict[str, Any]] = []
    for index in range(len(strokes) - 2):
        window = strokes[index : index + 3]
        lower = max(min(item["start_level"], item["end_level"]) for item in window)
        upper = min(max(item["start_level"], item["end_level"]) for item in window)
        if upper > lower:
            central_zones.append(
                {
                    "lower": _round(lower),
                    "upper": _round(upper),
                    "start_index": window[0]["start_index"],
                    "end_index": window[-1]["end_index"],
                    "stroke_count": 3,
                }
            )
    close = rows[-1]["close"]
    latest_zone = central_zones[-1] if central_zones else None
    last_direction = strokes[-1]["direction"] if strokes else None
    if latest_zone and close > latest_zone["upper"] and last_direction == "up":
        state = "buy_watch"
    elif latest_zone and close < latest_zone["lower"] and last_direction == "down":
        state = "sell_watch"
    else:
        state = "neutral"
    candidates: list[dict[str, Any]] = []
    for zone in central_zones[-3:]:
        candidates.extend(
            [
                _theory_level("chan_structure", "central_zone_lower", zone["lower"], zone["end_index"], 0.55),
                _theory_level("chan_structure", "central_zone_upper", zone["upper"], zone["end_index"], 0.55),
            ]
        )
    score = min(100.0, len(strokes) * 5.0 + len(central_zones) * 15.0)
    return {
        "status": "PASS",
        "active_in_main_chain": True,
        "fractals": fractals,
        "strokes": strokes,
        "central_zones": central_zones,
        "buy_sell_state": state,
        "evidence_score_not_probability": _round(score),
        "candidate_levels": candidates,
        "limitations": [
            "Fractals require two completed bars on the right and strokes alternate chronologically.",
            "Buy/sell state is a structural watch state, not a personalized order instruction.",
        ],
    }


def fibonacci_subsystem(rows: list[dict[str, Any]], atr_values: list[float | None]) -> dict[str, Any]:
    """Directional, scale-adaptive Fibonacci retracement and extension levels."""
    pivots = _alternating_pivots(rows, atr_values, 2)
    tolerance = max((atr_values[-1] or rows[-1]["close"] * 0.01) * 0.35, rows[-1]["close"] * 0.002)
    if len(pivots) < 2:
        return {
            "status": "PASS", "active_in_main_chain": True, "active_swing": None,
            "cluster_tolerance": _round(tolerance), "confluence_clusters": [], "candidate_levels": [],
            "evidence_score_not_probability": 0.0,
            "limitations": ["No complete confirmed swing was available."],
        }
    pairs = [(left, right) for left, right in zip(pivots, pivots[1:]) if left["kind"] != right["kind"]][-5:]
    active_left, active_right = pairs[-1]
    direction = "up" if active_right["level"] > active_left["level"] else "down"
    active = {
        "start_index": active_left["index"], "end_index": active_right["index"],
        "start_level": active_left["level"], "end_level": active_right["level"], "direction": direction,
    }
    candidates: list[dict[str, Any]] = []
    for pair_number, (left, right) in enumerate(pairs):
        start, end = float(left["level"]), float(right["level"])
        span = abs(end - start)
        if span <= 0:
            continue
        pair_direction = "up" if end > start else "down"
        for ratio in (0.236, 0.382, 0.5, 0.618, 0.786):
            level = end - span * ratio if pair_direction == "up" else end + span * ratio
            candidates.append(_theory_level("fibonacci", f"swing_{pair_number}_retracement_{ratio}", level, right["index"], 0.45))
        for ratio in (1.272, 1.618):
            level = start + span * ratio if pair_direction == "up" else start - span * ratio
            if level > 0:
                candidates.append(_theory_level("fibonacci", f"swing_{pair_number}_extension_{ratio}", level, right["index"], 0.35))
    clusters: list[dict[str, Any]] = []
    for item in sorted(candidates, key=lambda value: value["level"]):
        if clusters and abs(item["level"] - clusters[-1]["center"]) <= tolerance:
            cluster = clusters[-1]
            cluster["levels"].append(item["level"])
            cluster["center"] = sum(cluster["levels"]) / len(cluster["levels"])
            cluster["count"] = len(cluster["levels"])
        else:
            clusters.append({"center": item["level"], "levels": [item["level"]], "count": 1})
    for cluster in clusters:
        cluster["center"] = _round(cluster["center"])
    max_count = max((cluster["count"] for cluster in clusters), default=0)
    return {
        "status": "PASS",
        "active_in_main_chain": True,
        "active_swing": active,
        "cluster_tolerance": _round(tolerance),
        "confluence_clusters": [cluster for cluster in clusters if cluster["count"] >= 2],
        "evidence_score_not_probability": _round(min(100.0, 20.0 + max_count * 15.0)),
        "candidate_levels": candidates,
        "limitations": [
            "Levels are anchored only to confirmed alternating swings and preserve swing direction.",
            "Ratios are geometric references; confluence is not treated as a success probability.",
        ],
    }


def gann_subsystem(rows: list[dict[str, Any]], atr_values: list[float | None]) -> dict[str, Any]:
    """Scale-aware Gann square, angle and cycle references with derived evidence strength."""
    close = rows[-1]["close"]
    atr = atr_values[-1] or close * 0.01
    ema20 = _ema_series([row["close"] for row in rows], 20)
    slope = (ema20[-1] - ema20[max(0, len(ema20) - 6)]) / max(atr * min(5, len(ema20) - 1), 1e-9)
    recent_start = max(0, len(rows) - 80)
    if slope >= 0:
        anchor_index = min(range(recent_start, len(rows)), key=lambda index: rows[index]["low"])
        anchor = rows[anchor_index]["low"]
        sign = 1.0
    else:
        anchor_index = max(range(recent_start, len(rows)), key=lambda index: rows[index]["high"])
        anchor = rows[anchor_index]["high"]
        sign = -1.0
    root = math.sqrt(max(anchor, 1e-9))
    square: list[dict[str, Any]] = []
    for degree in (45, 90, 135, 180, 225, 270, 315, 360):
        offset = degree / 360.0
        for direction, multiplier in (("above", 1.0), ("below", -1.0)):
            level = (root + multiplier * offset) ** 2
            if level > 0:
                square.append({"degree": degree, "direction": direction, "level": _round(level)})
    elapsed = max(1, len(rows) - 1 - anchor_index)
    angles: list[dict[str, Any]] = []
    for name, ratio in (("1x2", 0.5), ("1x1", 1.0), ("2x1", 2.0)):
        level = anchor + sign * atr * ratio * elapsed
        if level > 0:
            angles.append({"angle": name, "level": _round(level), "anchor_index": anchor_index})
    cycles = []
    for length in (20, 30, 45, 60, 90):
        remainder = elapsed % length
        cycles.append({"length": length, "elapsed": elapsed, "bars_to_next": length - remainder if remainder else 0, "near_turn_window": remainder <= 2 or length - remainder <= 2})
    proximity = min((abs(close - item["level"]) / atr for item in square + angles), default=10.0)
    cycle_hits = sum(bool(item["near_turn_window"]) for item in cycles)
    score = min(100.0, abs(slope) * 35.0 + max(0.0, 25.0 - proximity * 5.0) + cycle_hits * 8.0)
    candidates = [
        _theory_level("gann", f"square_{item['degree']}_{item['direction']}", item["level"], anchor_index, 0.25)
        for item in square if abs(item["level"] - close) <= 10 * atr
    ] + [
        _theory_level("gann", f"angle_{item['angle']}", item["level"], anchor_index, 0.25)
        for item in angles if abs(item["level"] - close) <= 10 * atr
    ]
    return {
        "status": "PASS",
        "active_in_main_chain": True,
        "anchor": {"index": anchor_index, "level": _round(anchor), "direction": "up" if sign > 0 else "down"},
        "square_of_nine_levels": square,
        "angle_levels": angles,
        "time_cycles": cycles,
        "trend_slope_atr_per_bar": _round(slope),
        "evidence_score_not_probability": _round(score),
        "candidate_levels": candidates,
        "limitations": [
            "Price angles are normalized by ATR so they do not assume one price unit equals one time unit.",
            "Cycle proximity is descriptive timing context and cannot override observed price structure.",
        ],
    }


def wyckoff_subsystem(rows: list[dict[str, Any]], atr_values: list[float | None]) -> dict[str, Any]:
    """Trading-range-aware Wyckoff events, acceptance checks and volume/spread context."""
    events: list[dict[str, Any]] = []
    lookback = 20
    for index in range(lookback, len(rows) - 1):
        prior = rows[index - lookback : index]
        lower = min(row["low"] for row in prior)
        upper = max(row["high"] for row in prior)
        atr = atr_values[index] or rows[index]["close"] * 0.01
        avg_volume = statistics.fmean(row["volume"] for row in prior) or 1.0
        volume_ratio = rows[index]["volume"] / avg_volume
        future = rows[index + 1 : min(len(rows), index + 3)]
        if rows[index]["low"] < lower - 0.05 * atr and rows[index]["close"] > lower:
            events.append(
                {
                    "type": "spring", "index": index, "date": rows[index]["date"],
                    "event_level": _round(rows[index]["low"]), "range_lower": _round(lower), "range_upper": _round(upper),
                    "volume_ratio": _round(volume_ratio), "accepted": bool(future) and all(row["close"] > lower for row in future),
                }
            )
        if rows[index]["high"] > upper + 0.05 * atr and rows[index]["close"] < upper:
            events.append(
                {
                    "type": "upthrust", "index": index, "date": rows[index]["date"],
                    "event_level": _round(rows[index]["high"]), "range_lower": _round(lower), "range_upper": _round(upper),
                    "volume_ratio": _round(volume_ratio), "accepted": bool(future) and all(row["close"] < upper for row in future),
                }
            )
    recent = rows[-min(40, len(rows)) :]
    half = max(1, len(recent) // 2)
    early, late = recent[:half], recent[half:]
    early_spread = statistics.fmean(row["high"] - row["low"] for row in early)
    late_spread = statistics.fmean(row["high"] - row["low"] for row in late)
    early_volume = statistics.fmean(row["volume"] for row in early) or 1.0
    late_volume = statistics.fmean(row["volume"] for row in late)
    range_lower = min(row["low"] for row in recent)
    range_upper = max(row["high"] for row in recent)
    close = rows[-1]["close"]
    midpoint = (range_lower + range_upper) / 2.0
    accepted_spring = any(event["type"] == "spring" and event["accepted"] for event in events[-5:])
    accepted_upthrust = any(event["type"] == "upthrust" and event["accepted"] for event in events[-5:])
    if accepted_spring and close >= midpoint:
        phase = "accumulation_or_markup"
    elif accepted_upthrust and close <= midpoint:
        phase = "distribution_or_markdown"
    elif late_spread < early_spread and late_volume < early_volume:
        phase = "range_contraction"
    else:
        phase = "undetermined_range"
    conditions = {
        "range_defined": range_upper > range_lower,
        "spread_contracting": late_spread < early_spread,
        "volume_contracting": late_volume < early_volume,
        "accepted_spring": accepted_spring,
        "accepted_upthrust": accepted_upthrust,
        "close_above_range_midpoint": close >= midpoint,
    }
    score = min(100.0, sum(bool(value) for value in conditions.values()) * 12.0 + (20.0 if accepted_spring or accepted_upthrust else 0.0))
    candidates = [
        _theory_level("wyckoff", "trading_range_lower", range_lower, len(rows) - 1, 0.5),
        _theory_level("wyckoff", "trading_range_upper", range_upper, len(rows) - 1, 0.5),
    ]
    for event in events[-3:]:
        candidates.append(_theory_level("wyckoff", event["type"], event["event_level"], event["index"], 0.45))
    return {
        "status": "PASS",
        "active_in_main_chain": True,
        "phase": phase,
        "trading_range": {"lower": _round(range_lower), "upper": _round(range_upper), "midpoint": _round(midpoint)},
        "events": events,
        "conditions": conditions,
        "evidence_score_not_probability": _round(score),
        "candidate_levels": candidates,
        "limitations": [
            "Spring and upthrust events must breach a prior 20-bar range and show subsequent acceptance.",
            "Daily OHLCV cannot identify intraday event order or full composite-operator intent.",
        ],
    }


def five_theory_subsystems(rows: list[dict[str, Any]], atr_values: list[float | None] | None = None) -> dict[str, dict[str, Any]]:
    atr_series = atr_values or _atr_series(rows)
    return {
        "elliott_wave": elliott_subsystem(rows, atr_series),
        "chan_structure": chan_subsystem(rows, atr_series),
        "fibonacci": fibonacci_subsystem(rows, atr_series),
        "gann": gann_subsystem(rows, atr_series),
        "wyckoff": wyckoff_subsystem(rows, atr_series),
    }


def _candidate_levels(rows: list[dict[str, Any]], atr_values: list[float | None]) -> list[dict[str, Any]]:
    closes = [row["close"] for row in rows]
    current_index = len(rows) - 1
    candidates = _confirmed_pivots(rows, atr_values)

    for horizon, weight in ((20, 0.9), (60, 1.2), (120, 1.5), (250, 1.8)):
        if len(rows) < horizon:
            continue
        window = rows[-horizon:]
        low_index, low_row = min(enumerate(window, start=len(rows) - horizon), key=lambda item: item[1]["low"])
        high_index, high_row = max(enumerate(window, start=len(rows) - horizon), key=lambda item: item[1]["high"])
        candidates.extend(
            [
                {"level": low_row["low"], "family": "rolling_extreme", "label": f"low_{horizon}", "index": low_index, "weight": weight},
                {"level": high_row["high"], "family": "rolling_extreme", "label": f"high_{horizon}", "index": high_index, "weight": weight},
            ]
        )

    for period, weight in ((20, 0.7), (50, 0.9), (120, 1.1), (200, 1.2)):
        if len(rows) >= period:
            candidates.append(
                {
                    "level": _ema_series(closes, period)[-1],
                    "family": "moving_average",
                    "label": f"ema_{period}",
                    "index": current_index,
                    "weight": weight,
                }
            )

    major_pivots = [item for item in candidates if item["family"] == "confirmed_pivot" and item["index"] >= len(rows) - 160]
    if major_pivots and sum(row["volume"] for row in rows[-160:]) > 0:
        anchor = max(major_pivots, key=lambda item: item["weight"] * math.exp(-(current_index - item["index"]) / 120.0))
        anchored = rows[anchor["index"] :]
        denominator = sum(row["volume"] for row in anchored)
        if denominator > 0:
            avwap = sum(((row["high"] + row["low"] + row["close"]) / 3.0) * row["volume"] for row in anchored) / denominator
            candidates.append(
                {"level": avwap, "family": "anchored_vwap", "label": f"avwap_from_{rows[anchor['index']]['date']}", "index": current_index, "weight": 1.1}
            )

    profile_rows = rows[-min(120, len(rows)) :]
    if profile_rows and sum(row["volume"] for row in profile_rows) > 0:
        prices = [(row["high"] + row["low"] + row["close"]) / 3.0 for row in profile_rows]
        lower, upper = min(prices), max(prices)
        if upper > lower:
            bins = 24
            width = (upper - lower) / bins
            totals = [0.0] * bins
            for row, price in zip(profile_rows, prices):
                bucket = min(bins - 1, int((price - lower) / width))
                totals[bucket] += row["volume"]
            for bucket in sorted(range(bins), key=lambda value: totals[value], reverse=True)[:3]:
                candidates.append(
                    {
                        "level": lower + (bucket + 0.5) * width,
                        "family": "daily_volume_proxy",
                        "label": "daily_bar_volume_profile_proxy",
                        "index": current_index,
                        "weight": 0.55,
                    }
                )

    recent_major = sorted(
        [item for item in major_pivots if item["label"].endswith(("w5", "w10"))],
        key=lambda item: item["index"],
    )
    if len(recent_major) >= 2:
        left, right = recent_major[-2], recent_major[-1]
        swing = abs(right["level"] - left["level"])
        if swing > 0:
            high, low = max(left["level"], right["level"]), min(left["level"], right["level"])
            for ratio in (0.382, 0.5, 0.618):
                level = high - swing * ratio if right["level"] > left["level"] else low + swing * ratio
                candidates.append(
                    {"level": level, "family": "retracement", "label": f"objective_swing_fib_{ratio}", "index": right["index"], "weight": 0.5}
                )

    atr = atr_values[-1] or closes[-1] * 0.01
    for index in range(max(1, len(rows) - 80), len(rows)):
        if rows[index]["low"] > rows[index - 1]["high"] + 0.25 * atr:
            candidates.extend(
                [
                    {"level": rows[index - 1]["high"], "family": "price_gap", "label": "up_gap_lower_edge", "index": index, "weight": 0.8},
                    {"level": rows[index]["low"], "family": "price_gap", "label": "up_gap_upper_edge", "index": index, "weight": 0.8},
                ]
            )
        elif rows[index]["high"] < rows[index - 1]["low"] - 0.25 * atr:
            candidates.extend(
                [
                    {"level": rows[index]["high"], "family": "price_gap", "label": "down_gap_lower_edge", "index": index, "weight": 0.8},
                    {"level": rows[index - 1]["low"], "family": "price_gap", "label": "down_gap_upper_edge", "index": index, "weight": 0.8},
                ]
            )

    for item in candidates:
        age = max(0, current_index - int(item["index"]))
        item["age_bars"] = age
        item["effective_weight"] = item["weight"] * math.exp(-age / 180.0)
    return candidates


def _wilson_lower(successes: int, total: int, z: float = 1.645) -> float | None:
    if total <= 0:
        return None
    proportion = successes / total
    denominator = 1.0 + z * z / total
    centre = proportion + z * z / (2.0 * total)
    margin = z * math.sqrt((proportion * (1.0 - proportion) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denominator)


def _touch_history(rows: list[dict[str, Any]], zone: dict[str, float], kind: str, atr_values: list[float | None]) -> dict[str, Any]:
    touches = successes = failures = unresolved = 0
    last_touch = -10
    for index in range(20, len(rows) - 5):
        if index - last_touch < 5:
            continue
        atr = atr_values[index] or rows[index]["close"] * 0.01
        if kind == "support":
            touched = rows[index]["low"] <= zone["upper"] and rows[index - 1]["close"] >= zone["center"]
        else:
            touched = rows[index]["high"] >= zone["lower"] and rows[index - 1]["close"] <= zone["center"]
        if not touched:
            continue
        touches += 1
        last_touch = index
        outcome = _evaluate_forecast(kind, zone, rows[index : index + 6], atr)
        if outcome == 1:
            successes += 1
        elif outcome == 0:
            failures += 1
        else:
            unresolved += 1
    resolved = successes + failures
    return {
        "method": "retrospective_same_level_touch_test_selection_biased",
        "touches": touches,
        "resolved": resolved,
        "successes": successes,
        "failures": failures,
        "unresolved": unresolved,
        "hold_or_rejection_rate": _round(successes / resolved) if resolved else None,
        "wilson_lower_90": _round(_wilson_lower(successes, resolved)),
    }


def _cluster_levels(rows: list[dict[str, Any]], candidates: list[dict[str, Any]], atr_values: list[float | None]) -> dict[str, Any]:
    close = rows[-1]["close"]
    atr = atr_values[-1] or close * 0.01
    tolerance = min(max(0.35 * atr, 0.004 * close), 0.015 * close)
    plausible = [item for item in candidates if close - 10 * atr <= item["level"] <= close + 10 * atr]
    plausible.sort(key=lambda item: item["level"])
    groups: list[list[dict[str, Any]]] = []
    for item in plausible:
        if not groups:
            groups.append([item])
            continue
        group = groups[-1]
        centre = sum(value["level"] * value["effective_weight"] for value in group) / sum(value["effective_weight"] for value in group)
        if abs(item["level"] - centre) <= tolerance:
            group.append(item)
        else:
            groups.append([item])

    zones: list[dict[str, Any]] = []
    for group in groups:
        denominator = sum(item["effective_weight"] for item in group)
        centre = sum(item["level"] * item["effective_weight"] for item in group) / denominator
        zone = {"lower": centre - tolerance / 2.0, "center": centre, "upper": centre + tolerance / 2.0}
        if zone["upper"] < close - 0.05 * atr:
            kind = "support"
        elif zone["lower"] > close + 0.05 * atr:
            kind = "resistance"
        else:
            kind = "current_zone"
        families = sorted({item["family"] for item in group})
        family_best = {
            family: max(item["effective_weight"] for item in group if item["family"] == family)
            for family in families
        }
        touch = _touch_history(rows, zone, kind, atr_values) if kind != "current_zone" else {}
        resolved = int(touch.get("resolved", 0))
        lower = touch.get("wilson_lower_90") or 0.0
        evidence_score = min(
            100.0,
            14.0 * len(families)
            + 8.0 * min(sum(family_best.values()), 4.0)
            + 3.0 * min(resolved, 6)
            + 20.0 * lower,
        )
        if len(families) >= 3 and resolved >= 6 and lower >= 0.45:
            local_grade = "A"
        elif len(families) >= 2 and resolved >= 3:
            local_grade = "B"
        elif len(families) >= 2 or resolved >= 3:
            local_grade = "C"
        else:
            local_grade = "D"
        zones.append(
            {
                "kind": kind,
                "lower": _round(zone["lower"]),
                "center": _round(zone["center"]),
                "upper": _round(zone["upper"]),
                "distance_atr": _round(abs(centre - close) / atr),
                "independent_family_count": len(families),
                "families": families,
                "source_labels": sorted({item["label"] for item in group}),
                "newest_source_age_bars": min(item["age_bars"] for item in group),
                "evidence_score_not_probability": _round(evidence_score, 2),
                "local_grade": local_grade,
                "historical_touch_test": touch,
            }
        )
    return {"tolerance": tolerance, "atr": atr, "zones": zones}


def _primary(zones: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    eligible = [
        zone
        for zone in zones
        if zone["kind"] == kind
        and (
            zone["independent_family_count"] >= 2
            or (
                "confirmed_pivot" in zone["families"]
                and zone["historical_touch_test"].get("resolved", 0) >= 3
            )
        )
    ]
    eligible.sort(
        key=lambda zone: (
            float(zone["distance_atr"]),
            -float(zone["evidence_score_not_probability"]),
        )
    )
    return eligible[:3]


def _major_zone(zones: list[dict[str, Any]], kind: str) -> dict[str, Any] | None:
    eligible = [
        zone
        for zone in zones
        if zone["kind"] == kind and zone["independent_family_count"] >= 2
    ]
    if not eligible:
        return None
    return max(
        eligible,
        key=lambda zone: (
            float(zone["evidence_score_not_probability"]),
            zone["independent_family_count"],
            -float(zone["distance_atr"]),
        ),
    )


def build_zones(rows: list[dict[str, Any]]) -> dict[str, Any]:
    atr_values = _atr_series(rows)
    candidates = _candidate_levels(rows, atr_values)
    theory_subsystems = five_theory_subsystems(rows, atr_values)
    theory_candidates: list[dict[str, Any]] = []
    current_index = len(rows) - 1
    for subsystem in theory_subsystems.values():
        for raw in subsystem["candidate_levels"]:
            level = float(raw["level"])
            index = min(current_index, max(0, int(raw["index"])))
            if not math.isfinite(level) or level <= 0:
                continue
            item = dict(raw)
            item["index"] = index
            item["age_bars"] = current_index - index
            item["effective_weight"] = float(item["weight"]) * math.exp(-item["age_bars"] / 180.0)
            theory_candidates.append(item)
    candidates.extend(theory_candidates)
    clustered = _cluster_levels(rows, candidates, atr_values)
    supports = _primary(clustered["zones"], "support")
    resistances = _primary(clustered["zones"], "resistance")
    return {
        "atr": clustered["atr"],
        "tolerance": clustered["tolerance"],
        "candidate_count": len(candidates),
        "theory_candidate_count": len(theory_candidates),
        "theory_subsystems": theory_subsystems,
        "candidate_families": sorted({str(item["family"]) for item in candidates}),
        "all_zones": clustered["zones"],
        "supports": supports,
        "resistances": resistances,
    }


def _evaluate_forecast(kind: str, zone: dict[str, float], future: list[dict[str, Any]], atr: float) -> int | None:
    touch_index: int | None = None
    for index, row in enumerate(future):
        if kind == "support" and row["low"] <= zone["upper"]:
            touch_index = index
            break
        if kind == "resistance" and row["high"] >= zone["lower"]:
            touch_index = index
            break
    if touch_index is None:
        return None
    for row in future[touch_index:]:
        if kind == "support":
            if row["close"] < zone["lower"] - 0.25 * atr:
                return 0
            if row["high"] >= zone["center"] + 0.75 * atr:
                return 1
        else:
            if row["close"] > zone["upper"] + 0.25 * atr:
                return 0
            if row["low"] <= zone["center"] - 0.75 * atr:
                return 1
    return None


def _placebo_zone(kind: str, actual: dict[str, Any], close: float, atr: float, seed: int) -> dict[str, float]:
    rng = random.Random(seed)
    distance = max(abs(close - actual["center"]), 0.5 * atr)
    multiplier = rng.uniform(0.55, 1.45)
    centre = close - distance * multiplier if kind == "support" else close + distance * multiplier
    half_width = max((actual["upper"] - actual["lower"]) / 2.0, 0.15 * atr)
    return {"lower": centre - half_width, "center": centre, "upper": centre + half_width}


def _exact_sign_test(wins: int, losses: int) -> float | None:
    trials = wins + losses
    if trials <= 0:
        return None
    tail = min(wins, losses)
    probability = sum(math.comb(trials, index) for index in range(tail + 1)) / (2**trials)
    return min(1.0, 2.0 * probability)


def walk_forward_validate(rows: list[dict[str, Any]], min_train: int = 120, horizon: int = 10) -> dict[str, Any]:
    actual_outcomes: list[int] = []
    placebo_outcomes: list[int] = []
    paired: list[tuple[int, int]] = []
    forecast_count = 0
    untested = 0
    if len(rows) < min_train + horizon:
        return {
            "status": "INSUFFICIENT_SAMPLE",
            "reason": f"need_at_least_{min_train + horizon}_bars",
            "validation_grade": "D",
        }
    for cutoff in range(min_train, len(rows) - horizon + 1, horizon):
        prefix = rows[:cutoff]
        future = rows[cutoff : cutoff + horizon]
        zones = build_zones(prefix)
        for kind, key in (("support", "supports"), ("resistance", "resistances")):
            if not zones[key]:
                continue
            forecast_count += 1
            actual = zones[key][0]
            actual_zone = {field: float(actual[field]) for field in ("lower", "center", "upper")}
            placebo = _placebo_zone(kind, actual_zone, prefix[-1]["close"], zones["atr"], cutoff * 17 + (1 if kind == "support" else 2))
            actual_outcome = _evaluate_forecast(kind, actual_zone, future, zones["atr"])
            placebo_outcome = _evaluate_forecast(kind, placebo, future, zones["atr"])
            if actual_outcome is None:
                untested += 1
            else:
                actual_outcomes.append(actual_outcome)
            if placebo_outcome is not None:
                placebo_outcomes.append(placebo_outcome)
            if actual_outcome is not None and placebo_outcome is not None:
                paired.append((actual_outcome, placebo_outcome))

    actual_rate = sum(actual_outcomes) / len(actual_outcomes) if actual_outcomes else None
    placebo_rate = sum(placebo_outcomes) / len(placebo_outcomes) if placebo_outcomes else None
    wins = sum(1 for actual, placebo in paired if actual > placebo)
    losses = sum(1 for actual, placebo in paired if actual < placebo)
    ties = len(paired) - wins - losses
    lift = actual_rate - placebo_rate if actual_rate is not None and placebo_rate is not None else None
    sign_p = _exact_sign_test(wins, losses)
    if len(actual_outcomes) < 12:
        status, grade, reason = "INSUFFICIENT_SAMPLE", "D", "fewer_than_12_resolved_actual_forecasts"
    elif lift is None or lift <= 0:
        status, grade, reason = "NO_EMPIRICAL_LIFT", "D", "not_better_than_distance_matched_placebo"
    elif len(paired) >= 25 and wins > losses and sign_p is not None and sign_p < 0.05 and lift >= 0.10:
        status, grade, reason = "PASS", "A", "strong_walk_forward_and_paired_placebo_evidence"
    elif len(paired) >= 12 and wins > losses and sign_p is not None and sign_p < 0.10 and lift >= 0.05:
        status, grade, reason = "PASS", "B", "moderate_walk_forward_and_paired_placebo_evidence"
    else:
        status, grade, reason = "WEAK_EVIDENCE", "C", "positive_lift_without_strong_paired_evidence"
    return {
        "status": status,
        "validation_grade": grade,
        "reason": reason,
        "design": {
            "causal": True,
            "min_train_bars": min_train,
            "forward_horizon_bars": horizon,
            "step_bars": horizon,
            "overlapping_test_windows": False,
            "placebo": "deterministic_distance_matched_same_side_level",
        },
        "forecast_count": forecast_count,
        "actual_resolved": len(actual_outcomes),
        "actual_successes": sum(actual_outcomes),
        "actual_success_rate": _round(actual_rate),
        "actual_wilson_lower_90": _round(_wilson_lower(sum(actual_outcomes), len(actual_outcomes))),
        "placebo_resolved": len(placebo_outcomes),
        "placebo_successes": sum(placebo_outcomes),
        "placebo_success_rate": _round(placebo_rate),
        "lift_vs_placebo": _round(lift),
        "paired_resolved": len(paired),
        "paired_actual_wins": wins,
        "paired_placebo_wins": losses,
        "paired_ties": ties,
        "paired_exact_sign_test_p": _round(sign_p),
        "untested_actual_forecasts": untested,
        "limitations": [
            "Daily OHLCV cannot prove intraday path order within a bar.",
            "A single-symbol history cannot establish cross-sectional generalization.",
            "Placebo comparison controls a narrow null, not all data-snooping risk.",
        ],
    }


def _theory_subsystem(method: str, rows: list[dict[str, Any]], atr_values: list[float | None]) -> dict[str, Any]:
    runners = {
        "elliott_wave": elliott_subsystem,
        "chan_structure": chan_subsystem,
        "fibonacci": fibonacci_subsystem,
        "gann": gann_subsystem,
        "wyckoff": wyckoff_subsystem,
    }
    if method not in runners:
        raise ValueError(f"unknown_theory_method:{method}")
    return runners[method](rows, atr_values)


def _theory_validation_candidates(method: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = list(result.get("candidate_levels") or [])
    if method == "elliott_wave":
        return candidates if result.get("structure_state") == "complete_impulse" else []
    if method == "chan_structure":
        return candidates if result.get("central_zones") else []
    if method == "fibonacci":
        numbered: list[tuple[int, dict[str, Any]]] = []
        for item in candidates:
            match = re.search(r"swing_(\d+)_", str(item.get("label", "")))
            if match is not None:
                numbered.append((int(match.group(1)), item))
        if not numbered:
            return []
        active_number = max(number for number, _ in numbered)
        return [item for number, item in numbered if number == active_number]
    if method == "gann":
        cycle_confirmed = any(bool(item.get("near_turn_window")) for item in result.get("time_cycles", []))
        return candidates if cycle_confirmed and float(result.get("evidence_score_not_probability") or 0) >= 45.0 else []
    if method == "wyckoff":
        confirmed_event = any(bool(item.get("accepted")) for item in result.get("events", [])[-5:])
        return candidates if confirmed_event or result.get("phase") == "range_contraction" else []
    raise ValueError(f"unknown_theory_method:{method}")


def _nearest_theory_zone(
    rows: list[dict[str, Any]],
    method: str,
    kind: str,
    atr_values: list[float | None],
) -> dict[str, float] | None:
    result = _theory_subsystem(method, rows, atr_values)
    close = float(rows[-1]["close"])
    atr = float(atr_values[-1] or close * 0.01)
    levels = [
        float(item["level"])
        for item in _theory_validation_candidates(method, result)
        if math.isfinite(float(item.get("level", 0))) and float(item.get("level", 0)) > 0
    ]
    if kind == "support":
        eligible = [level for level in levels if level < close - 0.05 * atr]
        center = max(eligible, default=None)
    elif kind == "resistance":
        eligible = [level for level in levels if level > close + 0.05 * atr]
        center = min(eligible, default=None)
    else:
        raise ValueError(f"unknown_zone_kind:{kind}")
    if center is None or abs(center - close) > 10.0 * atr:
        return None
    half_width = max(0.15 * atr, 0.001 * close)
    return {"lower": center - half_width, "center": center, "upper": center + half_width}


def walk_forward_validate_theory(
    rows: list[dict[str, Any]],
    method: str,
    min_train: int = 120,
    horizon: int = 10,
) -> dict[str, Any]:
    actual_outcomes: list[int] = []
    placebo_outcomes: list[int] = []
    paired: list[tuple[int, int]] = []
    forecast_count = 0
    untested = 0
    if len(rows) < min_train + horizon:
        return {
            "method": method,
            "status": "INSUFFICIENT_SAMPLE",
            "forecast_count": 0,
            "actual_resolved": 0,
            "actual_successes": 0,
            "actual_success_rate": None,
            "placebo_resolved": 0,
            "placebo_successes": 0,
            "placebo_success_rate": None,
            "unpaired_lift": None,
            "paired_resolved": 0,
            "paired_actual_wins": 0,
            "paired_placebo_wins": 0,
            "paired_ties": 0,
            "paired_advantage": None,
            "paired_exact_sign_test_p": None,
            "untested_actual_forecasts": 0,
        }
    for cutoff in range(min_train, len(rows) - horizon + 1, horizon):
        prefix = rows[:cutoff]
        future = rows[cutoff : cutoff + horizon]
        atr_values = _atr_series(prefix)
        atr = float(atr_values[-1] or prefix[-1]["close"] * 0.01)
        for kind in ("support", "resistance"):
            actual = _nearest_theory_zone(prefix, method, kind, atr_values)
            if actual is None:
                continue
            forecast_count += 1
            placebo = _placebo_zone(
                kind,
                actual,
                float(prefix[-1]["close"]),
                atr,
                cutoff * 131 + THEORY_METHODS.index(method) * 17 + (1 if kind == "support" else 2),
            )
            actual_outcome = _evaluate_forecast(kind, actual, future, atr)
            placebo_outcome = _evaluate_forecast(kind, placebo, future, atr)
            if actual_outcome is None:
                untested += 1
            else:
                actual_outcomes.append(actual_outcome)
            if placebo_outcome is not None:
                placebo_outcomes.append(placebo_outcome)
            if actual_outcome is not None and placebo_outcome is not None:
                paired.append((actual_outcome, placebo_outcome))
    actual_rate = sum(actual_outcomes) / len(actual_outcomes) if actual_outcomes else None
    placebo_rate = sum(placebo_outcomes) / len(placebo_outcomes) if placebo_outcomes else None
    wins = sum(1 for actual, placebo in paired if actual > placebo)
    losses = sum(1 for actual, placebo in paired if actual < placebo)
    ties = len(paired) - wins - losses
    paired_advantage = (wins - losses) / len(paired) if paired else None
    return {
        "method": method,
        "status": "PASS" if paired else "INSUFFICIENT_SAMPLE",
        "forecast_count": forecast_count,
        "actual_resolved": len(actual_outcomes),
        "actual_successes": sum(actual_outcomes),
        "actual_success_rate": _round(actual_rate, 6),
        "placebo_resolved": len(placebo_outcomes),
        "placebo_successes": sum(placebo_outcomes),
        "placebo_success_rate": _round(placebo_rate, 6),
        "unpaired_lift": _round(actual_rate - placebo_rate, 6) if actual_rate is not None and placebo_rate is not None else None,
        "paired_resolved": len(paired),
        "paired_actual_wins": wins,
        "paired_placebo_wins": losses,
        "paired_ties": ties,
        "paired_advantage": _round(paired_advantage, 6),
        "paired_exact_sign_test_p": _round(_exact_sign_test(wins, losses), 8),
        "untested_actual_forecasts": untested,
    }


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def _aggregate_theory_method(
    symbol_results: list[dict[str, Any]],
    method: str,
    *,
    bootstrap_iterations: int,
    seed: int,
) -> dict[str, Any]:
    metrics = [item["methods"][method] for item in symbol_results if method in item.get("methods", {})]
    actual_resolved = sum(int(item["actual_resolved"]) for item in metrics)
    actual_successes = sum(int(item["actual_successes"]) for item in metrics)
    placebo_resolved = sum(int(item["placebo_resolved"]) for item in metrics)
    placebo_successes = sum(int(item["placebo_successes"]) for item in metrics)
    paired = sum(int(item["paired_resolved"]) for item in metrics)
    wins = sum(int(item["paired_actual_wins"]) for item in metrics)
    losses = sum(int(item["paired_placebo_wins"]) for item in metrics)
    ties = sum(int(item["paired_ties"]) for item in metrics)
    symbol_advantages = [
        float(item["paired_advantage"])
        for item in metrics
        if int(item["paired_resolved"]) > 0 and item.get("paired_advantage") is not None
    ]
    bootstrap_values: list[float] = []
    if symbol_advantages:
        rng = random.Random(seed + THEORY_METHODS.index(method) * 1009)
        for _ in range(max(1, bootstrap_iterations)):
            sample = [symbol_advantages[rng.randrange(len(symbol_advantages))] for _ in symbol_advantages]
            bootstrap_values.append(statistics.fmean(sample))
    ci = [_percentile(bootstrap_values, 0.025), _percentile(bootstrap_values, 0.975)]
    paired_advantage = (wins - losses) / paired if paired else None
    actual_rate = actual_successes / actual_resolved if actual_resolved else None
    placebo_rate = placebo_successes / placebo_resolved if placebo_resolved else None
    sign_p = _exact_sign_test(wins, losses)
    passed = bool(
        len(symbol_advantages) >= 10
        and paired >= 100
        and paired_advantage is not None
        and paired_advantage >= 0.02
        and actual_rate is not None
        and placebo_rate is not None
        and actual_rate > placebo_rate
        and sign_p is not None
        and sign_p < 0.05
        and ci[0] is not None
        and ci[0] > 0
    )
    return {
        "method": method,
        "status": "PASS" if passed else "NO_RELIABLE_EDGE",
        "symbols_with_paired_results": len(symbol_advantages),
        "actual_resolved": actual_resolved,
        "actual_successes": actual_successes,
        "actual_success_rate": _round(actual_rate, 6),
        "placebo_resolved": placebo_resolved,
        "placebo_successes": placebo_successes,
        "placebo_success_rate": _round(placebo_rate, 6),
        "unpaired_lift": _round(actual_rate - placebo_rate, 6) if actual_rate is not None and placebo_rate is not None else None,
        "paired_resolved": paired,
        "paired_actual_wins": wins,
        "paired_placebo_wins": losses,
        "paired_ties": ties,
        "paired_advantage": _round(paired_advantage, 6),
        "paired_exact_sign_test_p": _round(sign_p, 8),
        "symbol_cluster_bootstrap_95_ci": [_round(ci[0], 6), _round(ci[1], 6)],
        "pass_criteria": {
            "minimum_symbols_with_paired_results": 10,
            "minimum_paired_resolved": 100,
            "minimum_paired_advantage": 0.02,
            "actual_rate_must_exceed_placebo": True,
            "maximum_exact_sign_test_p": 0.05,
            "bootstrap_95_ci_lower_must_exceed_zero": True,
        },
    }


def _validated_tdx_dataset(symbol: str, dataset: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = dict(dataset.get("source") or {})
    if source.get("source_type") != "tdx_local_hub":
        raise AnalysisBlocked("five_theory_validation_requires_tdx_local_hub")
    path = Path(str(source.get("data_path") or ""))
    if not path.is_file():
        raise AnalysisBlocked(f"tdx_source_file_missing:{path}")
    if source.get("data_size") != path.stat().st_size or source.get("data_sha256") != _sha256(path):
        raise AnalysisBlocked(f"tdx_source_binding_mismatch:{symbol}")
    prepared, preparation = prepare_tdx_history(dataset.get("rows") or [])
    rows, quality = normalize_rows(prepared)
    quality["tdx_history_preparation"] = preparation
    age = (dt.date.today() - dt.date.fromisoformat(quality["end_date"])).days
    if age < 0 or age > 10:
        raise AnalysisBlocked(f"tdx_data_not_current_enough:{symbol}:calendar_age_days={age}")
    return rows, source


def _evaluate_validation_split(
    datasets: dict[str, dict[str, Any]],
    symbols: list[str],
    *,
    bootstrap_iterations: int,
    seed: int,
) -> dict[str, Any]:
    passed: list[dict[str, Any]] = []
    blocked: list[dict[str, str]] = []
    for symbol in symbols:
        try:
            rows, _ = _validated_tdx_dataset(symbol, datasets[symbol])
            methods = {method: walk_forward_validate_theory(rows, method) for method in THEORY_METHODS}
            passed.append({"symbol": symbol, "methods": methods})
        except (KeyError, AnalysisBlocked, OSError, ValueError) as exc:
            blocked.append({"symbol": symbol, "error": f"{type(exc).__name__}:{exc}"})
    aggregate = {
        method: _aggregate_theory_method(
            passed,
            method,
            bootstrap_iterations=bootstrap_iterations,
            seed=seed,
        )
        for method in THEORY_METHODS
    }
    return {
        "symbols_requested": len(symbols),
        "symbols": list(symbols),
        "symbols_passed_data_quality": len(passed),
        "symbols_blocked_data_quality": len(blocked),
        "blocked_symbols": blocked,
        "methods": aggregate,
        "per_symbol": passed,
    }


def validate_five_theory_datasets(
    datasets: dict[str, dict[str, Any]],
    *,
    development_symbols: list[str],
    holdout_symbols: list[str],
    bootstrap_iterations: int = 2000,
    seed: int = 20260817,
) -> dict[str, Any]:
    if not development_symbols or not holdout_symbols:
        raise AnalysisBlocked("development_and_holdout_symbols_are_required")
    if set(development_symbols) & set(holdout_symbols):
        raise AnalysisBlocked("development_holdout_overlap")
    development = _evaluate_validation_split(
        datasets,
        development_symbols,
        bootstrap_iterations=bootstrap_iterations,
        seed=seed,
    )
    holdout = _evaluate_validation_split(
        datasets,
        holdout_symbols,
        bootstrap_iterations=bootstrap_iterations,
        seed=seed + 1_000_003,
    )
    subsystems: dict[str, Any] = {}
    for method in THEORY_METHODS:
        development_result = development["methods"][method]
        holdout_result = holdout["methods"][method]
        passed = development_result["status"] == "PASS" and holdout_result["status"] == "PASS"
        subsystems[method] = {
            "status": "PASS" if passed else "NO_RELIABLE_EDGE",
            "development": development_result,
            "holdout": holdout_result,
        }
    all_subsystems_pass = all(item["status"] == "PASS" for item in subsystems.values())
    data_bindings = []
    for symbol in [*development_symbols, *holdout_symbols]:
        source = dict(datasets.get(symbol, {}).get("source") or {})
        data_bindings.append(
            {
                "symbol": symbol,
                "split": "development" if symbol in development_symbols else "holdout",
                "source_type": source.get("source_type"),
                "data_path": source.get("data_path"),
                "data_size": source.get("data_size"),
                "data_sha256": source.get("data_sha256"),
            }
        )
    return {
        "schema": FIVE_THEORY_VALIDATION_SCHEMA,
        "status": "PASS",
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "engine": {
            "path": str(Path(__file__).resolve()),
            "sha256": _sha256(Path(__file__).resolve()),
            "version": ENGINE_VERSION,
        },
        "parameter_set_id": PARAMETER_SET_ID,
        "design": {
            "data_source": "tdx_local_hub",
            "causal_prefix_only": True,
            "min_train_bars": 120,
            "forward_horizon_bars": 10,
            "overlapping_test_windows": False,
            "placebo": "deterministic_distance_matched_same_side_level",
            "holdout_frozen_before_execution": True,
            "development_holdout_disjoint": True,
            "bootstrap_cluster": "symbol",
            "bootstrap_iterations": bootstrap_iterations,
            "random_seed": seed,
        },
        "development": development,
        "holdout": holdout,
        "subsystems": subsystems,
        "data_bindings": data_bindings,
        "all_subsystems_pass": all_subsystems_pass,
        "predictive_claim_allowed": all_subsystems_pass,
        "validation_conclusion": "POSITIVE_FIVE_THEORY_OUT_OF_SAMPLE_EDGE" if all_subsystems_pass else "NO_RELIABLE_FIVE_THEORY_OUT_OF_SAMPLE_EDGE",
        "required_output_state": "CONDITIONAL_SCENARIOS_ALLOWED" if all_subsystems_pass else "UNVALIDATED_CANDIDATE_ZONES_ONLY",
    }


def write_five_theory_validation_receipt(payload: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    document = dict(payload)
    document.pop("canonical_payload_sha256", None)
    canonical = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    document["canonical_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    path = out_dir / "five_theory_real_kline_validation.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    readback = json.loads(path.read_text(encoding="utf-8"))
    if readback.get("schema") != FIVE_THEORY_VALIDATION_SCHEMA:
        raise RuntimeError("five_theory_receipt_readback_schema_mismatch")
    return {
        "schema": FIVE_THEORY_RECEIPT_SCHEMA,
        "validation": {
            "status": readback.get("status"),
            "parameter_set_id": readback.get("parameter_set_id"),
            "all_subsystems_pass": readback.get("all_subsystems_pass"),
            "predictive_claim_allowed": readback.get("predictive_claim_allowed"),
            "validation_conclusion": readback.get("validation_conclusion"),
        },
        "receipt_artifact": {
            "path": str(path.resolve()),
            "size": path.stat().st_size,
            "sha256": _sha256(path),
            "readback_status": "PASS",
        },
    }


def _cap_grade(local_grade: str, validation_grade: str) -> str:
    order = {"A": 0, "B": 1, "C": 2, "D": 3}
    return max((local_grade, validation_grade), key=lambda grade: order.get(grade, 3))


def _load_global_calibration(path: Path | None = None) -> dict[str, Any]:
    calibration_path = path or CALIBRATION_PATH
    fallback = {
        "status": "MISSING_OR_INCOMPATIBLE_CALIBRATION",
        "parameter_set_id": PARAMETER_SET_ID,
        "validation_grade": "D",
        "predictive_claim_allowed": False,
        "validation_conclusion": "NOT_VALIDATED",
        "reason": "Cross-sectional calibration is missing, unreadable, or incompatible; predictive claims fail closed.",
        "artifact": {
            "path": str(calibration_path.resolve()),
            "exists": calibration_path.is_file(),
        },
    }
    try:
        payload = json.loads(calibration_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return fallback
    compatible = (
        payload.get("status") == "PASS"
        and payload.get("parameter_set_id") == PARAMETER_SET_ID
        and payload.get("global_validation_grade") in {"A", "B", "C", "D"}
        and isinstance(payload.get("predictive_claim_allowed"), bool)
    )
    if not compatible:
        fallback["artifact"]["sha256"] = _sha256(calibration_path)
        return fallback
    return {
        "status": "PASS",
        "parameter_set_id": PARAMETER_SET_ID,
        "validation_grade": payload["global_validation_grade"],
        "predictive_claim_allowed": payload["predictive_claim_allowed"],
        "validation_conclusion": payload.get("validation_conclusion"),
        "required_output_state": payload.get("required_output_state"),
        "reason": payload.get("reason"),
        "development": payload.get("development"),
        "holdout": payload.get("holdout"),
        "combined": payload.get("combined"),
        "artifact": {
            "path": str(calibration_path.resolve()),
            "size": calibration_path.stat().st_size,
            "sha256": _sha256(calibration_path),
        },
    }


def _apply_global_calibration(local_validation: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    validation = dict(local_validation)
    local_grade = validation.get("validation_grade", "D")
    calibration = _load_global_calibration(path)
    global_grade = calibration.get("validation_grade", "D")
    validation["local_validation_grade"] = local_grade
    validation["validation_grade"] = _cap_grade(local_grade, global_grade)
    validation["global_cross_sectional_gate"] = calibration
    if not calibration.get("predictive_claim_allowed", False):
        validation["local_status_before_global_gate"] = validation.get("status")
        validation["local_reason_before_global_gate"] = validation.get("reason")
        validation["status"] = "GLOBAL_NO_EMPIRICAL_LIFT"
        validation["reason"] = f"global_cross_sectional_gate:{calibration.get('validation_conclusion', 'NOT_VALIDATED')}"
    return validation


def _conditional_conclusion(zones: dict[str, Any], technical: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    support = zones["supports"][0] if zones["supports"] else None
    resistance = zones["resistances"][0] if zones["resistances"] else None
    major_support = _major_zone(zones["all_zones"], "support")
    major_resistance = _major_zone(zones["all_zones"], "resistance")
    atr = float(zones["atr"])
    close = float(technical["close"])
    validation_grade = validation.get("validation_grade", "D")
    for zone in (support, resistance):
        if zone:
            zone["final_grade_capped_by_walk_forward"] = _cap_grade(zone["local_grade"], validation_grade)
    if not support or not resistance:
        location_state = "INSUFFICIENT_DEFENSIBLE_ZONES"
    else:
        support_distance = max(0.0, close - float(support["upper"])) / atr
        resistance_distance = max(0.0, float(resistance["lower"]) - close) / atr
        if support_distance <= 0.5:
            location_state = "NEAR_SUPPORT_TEST"
        elif resistance_distance <= 0.5:
            location_state = "NEAR_RESISTANCE_TEST"
        else:
            location_state = "BETWEEN_ZONES_NO_IMMEDIATE_EDGE"
    state = "UNVALIDATED_CANDIDATE_ZONES_ONLY" if validation_grade == "D" else location_state
    breakout = None
    breakdown = None
    invalidation = None
    if resistance:
        breakout = {
            "price": _round(float(resistance["upper"]) + 0.10 * atr),
            "confirmation": "daily_close_above_price AND (volume_ratio_20>=1.2 OR next_close_holds_above_zone)",
            "use": "MONITORING_THRESHOLD_ONLY_NOT_A_SIGNAL" if validation_grade == "D" else "CONDITIONAL_SCENARIO_TRIGGER",
        }
    if support:
        breakdown = {
            "price": _round(float(support["lower"]) - 0.10 * atr),
            "confirmation": "daily_close_below_price OR two_consecutive_closes_below_zone_lower",
            "use": "MONITORING_THRESHOLD_ONLY_NOT_A_SIGNAL" if validation_grade == "D" else "CONDITIONAL_SCENARIO_TRIGGER",
        }
        invalidation = {
            "price": _round(float(support["lower"]) - 0.25 * atr),
            "rule": "one_close_below_price OR two_consecutive_closes_below_zone_lower invalidates the support-test scenario",
        }
    main_scenario = (
        "No empirical edge over the placebo was established; zones are observational candidates only."
        if validation_grade == "D"
        else "A scenario becomes actionable only after the stated confirmation rule; a level touch alone is not confirmation."
    )
    return {
        "state": state,
        "location_state": location_state,
        "directional_prediction": "NOT_CLAIMED",
        "confidence_cap": validation_grade,
        "confidence_reason": validation.get("reason"),
        "primary_support_zone": support,
        "secondary_support_zone": zones["supports"][1] if len(zones["supports"]) > 1 else None,
        "primary_resistance_zone": resistance,
        "secondary_resistance_zone": zones["resistances"][1] if len(zones["resistances"]) > 1 else None,
        "major_structural_support_zone": major_support,
        "major_structural_resistance_zone": major_resistance,
        "breakout_trigger": breakout,
        "breakdown_trigger": breakdown,
        "support_scenario_invalidation": invalidation,
        "main_scenario": main_scenario,
        "alternate_scenario": "If neither confirmation occurs, retain the range/transition interpretation and do not infer direction from proximity alone.",
        "zone_role_rule": "Primary means nearest structurally eligible candidate, not an actionable level; major structural means the strongest multi-family candidate and may be farther away.",
    }


def _enforce_full_tdx_history(rows: list[dict[str, Any]], source: dict[str, Any]) -> None:
    if source.get("source_type") != "tdx_local_hub":
        return
    returned = source.get("records_returned")
    available = source.get("source_records_available")
    verified = source.get("full_history_verified") is True
    if (
        source.get("history_scope") != "FULL_LOCAL_TDX_FILE"
        or source.get("full_history_required") is not True
        or not verified
        or not isinstance(returned, int)
        or not isinstance(available, int)
        or returned != available
        or returned != len(rows)
    ):
        raise AnalysisBlocked(
            "tdx_full_history_not_verified:"
            f"returned={returned}:available={available}:rows={len(rows)}:verified={verified}"
        )


def analyze(rows: list[dict[str, Any]], symbol: str, mode: str, source: dict[str, Any], perform_walk_forward: bool = True) -> dict[str, Any]:
    _enforce_full_tdx_history(rows, source)
    preparation: dict[str, Any] | None = None
    rows_for_normalization = rows
    if source.get("source_type") == "tdx_local_hub":
        rows_for_normalization, preparation = prepare_tdx_history(rows)
    try:
        normalized, quality = normalize_rows(rows_for_normalization)
    except AnalysisBlocked as exc:
        if preparation is None:
            raise
        try:
            normalization_evidence: Any = json.loads(str(exc))
        except json.JSONDecodeError:
            normalization_evidence = str(exc)
        raise AnalysisBlocked(json.dumps({
            "status": "BLOCKED",
            "tdx_history_preparation": preparation,
            "normalization": normalization_evidence,
        }, ensure_ascii=False)) from exc
    if source.get("source_type") == "tdx_local_hub":
        quality["tdx_history_preparation"] = preparation
        calendar_age = (dt.date.today() - dt.date.fromisoformat(quality["end_date"])).days
        quality["calendar_age_days"] = calendar_age
        quality["freshness_status"] = "CURRENT_OR_RECENT" if 0 <= calendar_age <= 10 else "STALE_OR_FUTURE"
        if calendar_age < 0 or calendar_age > 10:
            raise AnalysisBlocked(f"tdx_data_not_current_enough:calendar_age_days={calendar_age}")
    else:
        quality["freshness_status"] = "NOT_ASSERTED_FOR_NON_TDX_INPUT"
    atr_values = _atr_series(normalized)
    technical = technical_context(normalized, atr_values)
    zones = build_zones(normalized)
    local_validation = walk_forward_validate(normalized) if perform_walk_forward else {
        "status": "NOT_RUN",
        "validation_grade": "D",
        "reason": "walk_forward_disabled",
    }
    validation = _apply_global_calibration(local_validation)
    conclusion = _conditional_conclusion(zones, technical, validation)
    return {
        "status": "PASS",
        "skill": SKILL,
        "engine_version": ENGINE_VERSION,
        "methodology": METHODOLOGY,
        "parameter_set_id": PARAMETER_SET_ID,
        "mode": mode,
        "symbol": symbol,
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "data_provenance": source,
        "data_quality": quality,
        "technical_context": technical,
        "theory_subsystems": zones["theory_subsystems"],
        "level_construction": {
            "causal_pivots_only": True,
            "atr_adaptive_tolerance": _round(zones["tolerance"]),
            "candidate_count": zones["candidate_count"],
            "theory_candidate_count": zones["theory_candidate_count"],
            "independent_evidence_families": zones["candidate_families"],
            "theory_family_counting_rule": "All five formalized theories share one evidence family so method overlap cannot be double-counted as independent empirical confirmation.",
            "volume_profile_warning": "Daily-bar volume profile is a proxy; it is never counted as intraday volume-at-price.",
            "all_zones": zones["all_zones"],
        },
        "walk_forward_validation": validation,
        "conclusion": conclusion,
        "theory_methods_policy": {
            "elliott_wave": "formalized_active_causal_structure_and_candidate_levels",
            "chan_structure": "formalized_active_confirmed_fractals_strokes_zones",
            "fibonacci": "formalized_active_directional_scale_adaptive_levels",
            "gann": "formalized_active_atr_normalized_secondary_levels",
            "wyckoff": "formalized_active_prior_range_events_and_acceptance",
            "prediction_gate": "Theory outputs participate in the main chain, but predictive claims remain prohibited until walk-forward and frozen cross-sectional validation allow them.",
        },
        "risk_boundary": {
            "decision_support_only": True,
            "not_personalized_advice": True,
            "not_an_automatic_order_signal": True,
            "core_limit": "Historical regularities may fail after regime change, corporate action, illiquidity, or event gaps.",
        },
    }


def _load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _load_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("records", "rows", "data", "klines"):
            if isinstance(payload.get(key), list):
                return payload[key]
    raise AnalysisBlocked("input_json_has_no_row_array")


def load_input(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not path.is_file():
        raise AnalysisBlocked(f"input_missing:{path}")
    rows = _load_csv(path) if path.suffix.lower() == ".csv" else _load_json(path)
    return rows, {"source_type": "user_file", "path": str(path.resolve()), "size": path.stat().st_size, "sha256": _sha256(path)}


def _tdx_request_symbol(symbol: str) -> str:
    raw = symbol.strip().upper().replace("_", ".")
    suffix = re.fullmatch(r"(\d{6})\.(SH|SZ|BJ)", raw)
    if suffix:
        return suffix.group(2).lower() + suffix.group(1)
    prefix = re.fullmatch(r"(SH|SZ|BJ)\.?([0-9]{6})", raw)
    if prefix:
        return prefix.group(1).lower() + prefix.group(2)
    return symbol.strip()


def load_tdx(symbol: str, limit: int = 0) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not TDX_HUB.is_file():
        raise AnalysisBlocked(f"tdx_hub_missing:{TDX_HUB}")
    if limit != 0:
        raise AnalysisBlocked(f"partial_tdx_history_limit_forbidden:{limit}:use_limit_0_for_full_history")
    request_symbol = _tdx_request_symbol(symbol)
    command = [sys.executable, str(TDX_HUB), "kline", request_symbol, "--period", "day", "--limit", "0"]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if result.returncode != 0:
        raise AnalysisBlocked(f"tdx_hub_failed:{result.returncode}:{result.stderr[-400:]}")
    payload = json.loads(result.stdout.lstrip("\ufeff"))
    if not payload.get("ok") or not isinstance(payload.get("records"), list):
        raise AnalysisBlocked("tdx_hub_returned_no_records")
    path = Path(payload["path"])
    if not path.is_file() or path.stat().st_size % 32 != 0:
        raise AnalysisBlocked(f"tdx_day_file_size_invalid:{path}")
    file_record_capacity = path.stat().st_size // 32
    source_records_available = payload.get("count")
    records_returned = len(payload["records"])
    full_history_verified = (
        isinstance(source_records_available, int)
        and source_records_available == file_record_capacity
        and records_returned == source_records_available
    )
    if not full_history_verified:
        raise AnalysisBlocked(
            "tdx_full_history_not_verified_at_source:"
            f"returned={records_returned}:payload_count={source_records_available}:file_capacity={file_record_capacity}"
        )
    source = {
        "source_type": "tdx_local_hub",
        "history_scope_contract_id": FULL_HISTORY_CONTRACT_ID,
        "history_scope": "FULL_LOCAL_TDX_FILE",
        "full_history_required": True,
        "full_history_verified": True,
        "hub_path": str(TDX_HUB),
        "hub_sha256": _sha256(TDX_HUB),
        "data_path": str(path),
        "data_size": path.stat().st_size if path.is_file() else None,
        "data_sha256": _sha256(path) if path.is_file() else None,
        "tdx_symbol": payload.get("symbol"),
        "tdx_request_symbol": request_symbol,
        "period": payload.get("period"),
        "records_returned": records_returned,
        "source_records_available": source_records_available,
        "source_file_record_capacity": file_record_capacity,
        "source_start_date": payload["records"][0].get("date"),
        "source_end_date": payload["records"][-1].get("date"),
        "requested_limit": 0,
    }
    return payload["records"], source


def _tdx_validation_stratum(market: str, code: str) -> str | None:
    if market == "sh" and code.startswith("688"):
        return "STAR"
    if market == "sh" and code.startswith("6"):
        return "SH_MAIN"
    if market == "sz" and code.startswith("300"):
        return "CHINEXT"
    if market == "sz" and code.startswith(("000", "001", "002", "003")):
        return "SZ_MAIN"
    if market == "bj":
        return "BEIJING"
    return None


def select_tdx_validation_symbols(
    vipdoc_root: Path = TDX_VIPDOC,
    *,
    symbols_per_stratum: int = 4,
    excluded_symbols: set[str] | None = None,
) -> dict[str, Any]:
    if symbols_per_stratum < 1:
        raise AnalysisBlocked("symbols_per_stratum_must_be_positive")
    strata: dict[str, list[str]] = {name: [] for name in ("SH_MAIN", "STAR", "SZ_MAIN", "CHINEXT", "BEIJING")}
    for market in ("sh", "sz", "bj"):
        folder = vipdoc_root / market / "lday"
        if not folder.is_dir():
            continue
        pattern = re.compile(rf"^{market}(\d{{6}})\.day$", re.IGNORECASE)
        for path in folder.glob(f"{market}*.day"):
            match = pattern.match(path.name)
            if match is None or path.stat().st_size < 32 * (HARD_MIN_BARS + 10):
                continue
            code = match.group(1)
            stratum = _tdx_validation_stratum(market, code)
            if stratum is None:
                continue
            suffix = "SH" if market == "sh" else "SZ" if market == "sz" else "BJ"
            strata[stratum].append(f"{code}.{suffix}")
    excluded = set(excluded_symbols or set())
    development: list[str] = []
    holdout: list[str] = []
    selected_by_stratum: dict[str, dict[str, list[str]]] = {}
    for stratum, symbols in strata.items():
        ordered = sorted(
            set(symbols) - excluded,
            key=lambda symbol: hashlib.sha256(
                f"{PARAMETER_SET_ID}|{stratum}|{symbol}".encode("utf-8")
            ).hexdigest(),
        )
        required = symbols_per_stratum * 2
        if len(ordered) < required:
            raise AnalysisBlocked(f"insufficient_tdx_symbols:{stratum}:{len(ordered)}<{required}")
        development_part = ordered[:symbols_per_stratum]
        holdout_part = ordered[symbols_per_stratum:required]
        development.extend(development_part)
        holdout.extend(holdout_part)
        selected_by_stratum[stratum] = {
            "development": development_part,
            "holdout": holdout_part,
        }
    return {
        "selection_rule": "fixed_parameter_set_and_stratum_sha256_order",
        "parameter_set_id": PARAMETER_SET_ID,
        "symbols_per_stratum": symbols_per_stratum,
        "excluded_symbol_count": len(excluded),
        "development": development,
        "holdout": holdout,
        "strata": selected_by_stratum,
    }


def run_five_theory_real_kline_validation(args: argparse.Namespace) -> int:
    run_id = args.run_id or dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    out_dir = args.validation_out_dir or args.out_dir or (ROOT / "reports" / run_id / "five-theory-real-kline-validation")
    out_dir.mkdir(parents=True, exist_ok=True)
    selection = select_tdx_validation_symbols(
        TDX_VIPDOC,
        symbols_per_stratum=args.validation_symbols_per_stratum,
        excluded_symbols=PREDECESSOR_VALIDATION_SYMBOLS,
    )
    preregistration = {
        "schema": "FIVE_THEORY_TDX_PREREGISTRATION_V1",
        "created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "selection": selection,
        "engine": {
            "path": str(Path(__file__).resolve()),
            "sha256": _sha256(Path(__file__).resolve()),
            "version": ENGINE_VERSION,
        },
        "validation_limit": args.validation_limit,
        "bootstrap_iterations": args.bootstrap_iterations,
        "random_seed": args.validation_seed,
        "holdout_state": "FROZEN_BEFORE_DATA_EVALUATION",
        "predecessor_validation_receipt": PREDECESSOR_VALIDATION_RECEIPT,
        "predecessor_symbols_excluded": sorted(PREDECESSOR_VALIDATION_SYMBOLS),
    }
    preregistration_path = out_dir / "five_theory_preregistration.json"
    preregistration_path.write_text(
        json.dumps(preregistration, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    datasets: dict[str, dict[str, Any]] = {}
    load_errors: list[dict[str, str]] = []
    for symbol in [*selection["development"], *selection["holdout"]]:
        try:
            rows, source = load_tdx(symbol, args.validation_limit)
            datasets[symbol] = {"rows": rows, "source": source}
        except (AnalysisBlocked, OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            load_errors.append({"symbol": symbol, "error": f"{type(exc).__name__}:{exc}"})
    payload = validate_five_theory_datasets(
        datasets,
        development_symbols=selection["development"],
        holdout_symbols=selection["holdout"],
        bootstrap_iterations=args.bootstrap_iterations,
        seed=args.validation_seed,
    )
    payload["preregistration"] = {
        "path": str(preregistration_path.resolve()),
        "size": preregistration_path.stat().st_size,
        "sha256": _sha256(preregistration_path),
        "holdout_frozen_before_execution": True,
    }
    payload["load_errors"] = load_errors
    envelope = write_five_theory_validation_receipt(payload, out_dir)
    print(json.dumps(envelope, ensure_ascii=False, indent=2))
    return 0 if payload["predictive_claim_allowed"] else 3


def _safe_name(symbol: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in symbol).strip("_") or "UNKNOWN"


def _write_report(report: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{_safe_name(report['symbol'])}.scientific_support_pressure.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    readback = json.loads(path.read_text(encoding="utf-8"))
    if readback.get("status") != "PASS" or readback.get("engine_version") != ENGINE_VERSION:
        raise RuntimeError("persisted_report_readback_mismatch")
    return {"path": str(path), "size": path.stat().st_size, "sha256": _sha256(path), "readback_status": readback["status"]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scientific causal support/resistance analysis")
    parser.add_argument("--mode", choices=("pressure", "resistance", "technical"), default="pressure")
    parser.add_argument("--symbol", default="000001.SH")
    parser.add_argument("--symbols", help="Comma-separated symbols; overrides --symbol")
    parser.add_argument("--indices", help="Comma-separated benchmark symbols analyzed by the same engine")
    parser.add_argument("--input", type=Path, help="CSV or JSON OHLCV input; single-symbol only")
    parser.add_argument("--limit", type=int, default=0, help="TDX data must use 0: consume the entire local day file")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--run-id", help="Stable caller run id used when --out-dir is omitted")
    parser.add_argument("--no-walk-forward", action="store_true")
    parser.add_argument("--route-check", action="store_true")
    parser.add_argument("--validate-five-theories", action="store_true")
    parser.add_argument("--validation-symbols-per-stratum", type=int, default=4)
    parser.add_argument("--validation-limit", type=int, default=0, help="Validation also requires complete local TDX history")
    parser.add_argument("--bootstrap-iterations", type=int, default=2000)
    parser.add_argument("--validation-seed", type=int, default=20260817)
    parser.add_argument("--validation-out-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.route_check:
        print(json.dumps({"status": "CLEAN_PASS", "engine": str(Path(__file__).resolve()), "version": ENGINE_VERSION, "methodology": METHODOLOGY}, ensure_ascii=False))
        return 0
    if args.validate_five_theories:
        try:
            return run_five_theory_real_kline_validation(args)
        except (AnalysisBlocked, OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            print(json.dumps({
                "schema": FIVE_THEORY_RECEIPT_SCHEMA,
                "status": "BLOCKED",
                "error": f"{type(exc).__name__}:{exc}",
            }, ensure_ascii=False, indent=2))
            return 2
    requested = args.symbols.split(",") if args.symbols else [args.symbol]
    if args.indices:
        requested.extend(args.indices.split(","))
    symbols = list(dict.fromkeys(value.strip() for value in requested if value.strip()))
    if args.input and len(symbols) != 1:
        print(json.dumps({"status": "BLOCKED", "error": "file_input_supports_one_symbol"}, ensure_ascii=False))
        return 2
    run_id = args.run_id or dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    out_dir = args.out_dir or (REPORTS_ROOT / run_id / "scientific-support-pressure")
    items: list[dict[str, Any]] = []
    for symbol in symbols:
        try:
            raw_rows, source = load_input(args.input) if args.input else load_tdx(symbol, args.limit)
            report = analyze(raw_rows, symbol, args.mode, source, perform_walk_forward=not args.no_walk_forward)
            artifact = _write_report(report, out_dir)
            items.append(
                {
                    "symbol": symbol,
                    "status": "PASS",
                    "artifact": artifact,
                    "data_start_date": report["data_quality"]["start_date"],
                    "data_end_date": report["data_quality"]["end_date"],
                    "data_bar_count": report["data_quality"]["bar_count"],
                    "history_scope": report["data_provenance"].get("history_scope"),
                    "full_history_verified": report["data_provenance"].get("full_history_verified"),
                    "conclusion_state": report["conclusion"]["state"],
                    "location_state": report["conclusion"]["location_state"],
                    "confidence_cap": report["conclusion"]["confidence_cap"],
                    "primary_support_zone": report["conclusion"]["primary_support_zone"],
                    "primary_resistance_zone": report["conclusion"]["primary_resistance_zone"],
                }
            )
        except (AnalysisBlocked, json.JSONDecodeError, OSError, subprocess.SubprocessError, ValueError) as exc:
            items.append({"symbol": symbol, "status": "BLOCKED", "error": f"{type(exc).__name__}:{exc}"})
    passed = all(item["status"] == "PASS" for item in items)
    summary = {
        "status": "PASS" if passed else "BLOCKED",
        "skill": SKILL,
        "engine_version": ENGINE_VERSION,
        "methodology": METHODOLOGY,
        "mode": args.mode,
        "items": items,
    }
    summary_path = out_dir / "run_summary.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_readback = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["summary_artifact"] = {"path": str(summary_path), "size": summary_path.stat().st_size, "sha256": _sha256(summary_path), "readback_status": summary_readback["status"]}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
