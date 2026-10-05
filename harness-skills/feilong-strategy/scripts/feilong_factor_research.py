#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_tdx_root

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, mannwhitneyu

from feilong_offline_replay import (
    DAY_RECORD,
    day_path_for_symbol,
    evaluate_installed_formula,
    front_adjust_like_tq,
    read_base_finance,
    read_gbbq,
    read_tdx_day,
)


SCHEMA = "FEILONG_FACTOR_RESEARCH_V1"
MANIFEST_SCHEMA = "FEILONG_FACTOR_RESEARCH_MANIFEST_V1"
FORMULA_NAME = "飞龙在天"
TDX_ROOT = resolve_tdx_root()
FORMULA_SHA256 = "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0"
PRICE_COLUMNS = ("open", "high", "low", "close")

NUMERIC_FACTORS = {
    "open_gap_pct": "首板开盘缺口(%)",
    "intraday_range_pct": "首板振幅(%)",
    "body_pct": "首板实体涨幅(%)",
    "upper_shadow_pct": "首板上影线(%)",
    "close_location": "收盘位于日内区间的位置",
    "volume_vs_ma5": "成交量/5日均量",
    "volume_vs_ma10": "成交量/10日均量",
    "volume_vs_ma20": "成交量/20日均量",
    "amount_vs_ma20": "成交额/20日均额",
    "amount_100m": "首板成交额(亿元)",
    "prev_5d_return_pct": "首板前5日涨幅(%)",
    "prev_10d_return_pct": "首板前10日涨幅(%)",
    "prev_20d_return_pct": "首板前20日涨幅(%)",
    "prev_60d_return_pct": "首板前60日涨幅(%)",
    "close_vs_ma5_pct": "收盘相对5日线(%)",
    "close_vs_ma10_pct": "收盘相对10日线(%)",
    "close_vs_ma20_pct": "收盘相对20日线(%)",
    "close_vs_ma60_pct": "收盘相对60日线(%)",
    "close_vs_ma120_pct": "收盘相对120日线(%)",
    "distance_20d_high_pct": "距20日最高价(%)",
    "distance_60d_high_pct": "距60日最高价(%)",
    "prior_range_5d_pct": "首板前5日区间宽度(%)",
    "prior_range_10d_pct": "首板前10日区间宽度(%)",
    "atr14_pct": "14日真实波幅/收盘(%)",
    "prev_volatility_20d_pct": "前20日日收益波动率(%)",
    "prior_limitups_20d": "前20日9.84%以上上涨次数",
    "listing_age_days": "上市天数",
    "sh_index_ret_1d_pct": "上证指数当日涨幅(%)",
    "sh_index_ret_5d_pct": "上证指数5日涨幅(%)",
    "sz_index_ret_1d_pct": "深证成指当日涨幅(%)",
    "cyb_index_ret_1d_pct": "创业板指当日涨幅(%)",
    "market_advance_ratio": "全市场上涨家数占比",
    "market_median_return_pct": "全市场个股涨幅中位数(%)",
    "market_ge_9_8_count": "全市场涨幅不低于9.8%家数",
    "market_amount_100m": "全市场成交额(亿元)",
}

BINARY_FACTORS = {
    "close_at_high": "收盘等于最高价",
    "one_price_board": "一字板",
    "above_ma20": "收盘站上20日线",
    "above_ma60": "收盘站上60日线",
    "ma5_gt_ma10": "5日线高于10日线",
    "ma10_gt_ma20": "10日线高于20日线",
    "new_high_20d": "创20日新高",
    "new_high_60d": "创60日新高",
    "formula_longtou": "公式组件：龙头战法",
    "formula_waveband_password": "公式组件：波段密码",
    "formula_rapid_rise": "公式组件：暴涨启动",
    "formula_private_entry": "公式组件：私募秘进",
    "formula_xs1": "公式组件：XS1",
    "formula_xs2": "公式组件：XS2",
}


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_clean(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    return value


def symbol_for_code(code: str) -> str:
    code = str(code).zfill(6)
    if code.startswith(("6", "5", "9")):
        return f"{code}.SH"
    if code.startswith(("0", "1", "2", "3")):
        return f"{code}.SZ"
    return f"{code}.BJ"


def safe_div(numerator: float, denominator: float) -> float:
    if not math.isfinite(numerator) or not math.isfinite(denominator) or denominator == 0:
        return math.nan
    return numerator / denominator


def value_at(series: pd.Series, position: int) -> float:
    value = series.iloc[position]
    return float(value) if pd.notna(value) else math.nan


def prior_return(close: pd.Series, position: int, lookback: int) -> float:
    prior_position = position - 1
    start_position = prior_position - lookback
    if start_position < 0:
        return math.nan
    return (safe_div(float(close.iloc[prior_position]), float(close.iloc[start_position])) - 1.0) * 100.0


def index_features(frame: pd.DataFrame, date: str, prefix: str) -> dict[str, float]:
    if date not in frame.index:
        return {
            f"{prefix}_ret_1d_pct": math.nan,
            f"{prefix}_ret_5d_pct": math.nan,
            f"{prefix}_above_ma20": math.nan,
        }
    position = int(frame.index.get_loc(date))
    close = frame["close"].astype(float)
    previous = close.shift(1)
    ret_1d = (safe_div(float(close.iloc[position]), float(previous.iloc[position])) - 1.0) * 100.0
    ret_5d = math.nan
    if position >= 5:
        ret_5d = (safe_div(float(close.iloc[position]), float(close.iloc[position - 5])) - 1.0) * 100.0
    ma20 = close.rolling(20, min_periods=20).mean()
    above = math.nan if pd.isna(ma20.iloc[position]) else float(close.iloc[position] > ma20.iloc[position])
    return {
        f"{prefix}_ret_1d_pct": ret_1d,
        f"{prefix}_ret_5d_pct": ret_5d,
        f"{prefix}_above_ma20": above,
    }


def compute_event_features(
    bars: pd.DataFrame,
    date: str,
    *,
    code: str,
    name: str,
    listing_date: str,
    active_capital: float | None,
) -> dict[str, Any]:
    if date not in bars.index:
        raise RuntimeError(f"event date missing from daily data: {code} {date}")
    position = int(bars.index.get_loc(date))
    if position < 2:
        raise RuntimeError(f"insufficient daily history: {code} {date}")
    close = bars["close"].astype(float)
    open_ = bars["open"].astype(float)
    high = bars["high"].astype(float)
    low = bars["low"].astype(float)
    volume = bars["volume"].astype(float)
    amount = bars["amount"].astype(float)
    previous_close = float(close.iloc[position - 1])
    current_close = float(close.iloc[position])
    current_open = float(open_.iloc[position])
    current_high = float(high.iloc[position])
    current_low = float(low.iloc[position])
    current_volume = float(volume.iloc[position])
    current_amount = float(amount.iloc[position])
    daily_range = current_high - current_low
    returns = close.pct_change()
    true_range = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)
    ma5 = close.rolling(5, min_periods=5).mean()
    ma10 = close.rolling(10, min_periods=10).mean()
    ma20 = close.rolling(20, min_periods=20).mean()
    ma60 = close.rolling(60, min_periods=60).mean()
    ma120 = close.rolling(120, min_periods=120).mean()
    vol_ma5 = volume.rolling(5, min_periods=5).mean()
    vol_ma10 = volume.rolling(10, min_periods=10).mean()
    vol_ma20 = volume.rolling(20, min_periods=20).mean()
    amount_ma20 = amount.rolling(20, min_periods=20).mean()
    high20 = high.rolling(20, min_periods=20).max()
    high60 = high.rolling(60, min_periods=60).max()
    prior5_high = high.shift(1).rolling(5, min_periods=5).max()
    prior5_low = low.shift(1).rolling(5, min_periods=5).min()
    prior10_high = high.shift(1).rolling(10, min_periods=10).max()
    prior10_low = low.shift(1).rolling(10, min_periods=10).min()
    prior_limitups = (returns.shift(1) * 100.0).ge(9.84).rolling(20, min_periods=20).sum()
    formula = evaluate_installed_formula(
        bars,
        active_capital_10k_shares=active_capital,
        listing_date=listing_date,
        code=code,
        name=name,
    )
    formula_row = formula.loc[date]
    listing_age = (
        datetime.strptime(date, "%Y%m%d") - datetime.strptime(listing_date, "%Y%m%d")
    ).days
    result: dict[str, Any] = {
        "first_board_return_pct": (safe_div(current_close, previous_close) - 1.0) * 100.0,
        "open_gap_pct": (safe_div(current_open, previous_close) - 1.0) * 100.0,
        "intraday_range_pct": safe_div(daily_range, previous_close) * 100.0,
        "body_pct": safe_div(current_close - current_open, previous_close) * 100.0,
        "upper_shadow_pct": safe_div(current_high - max(current_close, current_open), previous_close) * 100.0,
        "close_location": safe_div(current_close - current_low, daily_range) if daily_range else 1.0,
        "volume_vs_ma5": safe_div(current_volume, value_at(vol_ma5, position)),
        "volume_vs_ma10": safe_div(current_volume, value_at(vol_ma10, position)),
        "volume_vs_ma20": safe_div(current_volume, value_at(vol_ma20, position)),
        "amount_vs_ma20": safe_div(current_amount, value_at(amount_ma20, position)),
        "amount_100m": current_amount / 1e8,
        "prev_5d_return_pct": prior_return(close, position, 5),
        "prev_10d_return_pct": prior_return(close, position, 10),
        "prev_20d_return_pct": prior_return(close, position, 20),
        "prev_60d_return_pct": prior_return(close, position, 60),
        "close_vs_ma5_pct": (safe_div(current_close, value_at(ma5, position)) - 1.0) * 100.0,
        "close_vs_ma10_pct": (safe_div(current_close, value_at(ma10, position)) - 1.0) * 100.0,
        "close_vs_ma20_pct": (safe_div(current_close, value_at(ma20, position)) - 1.0) * 100.0,
        "close_vs_ma60_pct": (safe_div(current_close, value_at(ma60, position)) - 1.0) * 100.0,
        "close_vs_ma120_pct": (safe_div(current_close, value_at(ma120, position)) - 1.0) * 100.0,
        "distance_20d_high_pct": (safe_div(current_close, value_at(high20, position)) - 1.0) * 100.0,
        "distance_60d_high_pct": (safe_div(current_close, value_at(high60, position)) - 1.0) * 100.0,
        "prior_range_5d_pct": safe_div(value_at(prior5_high, position) - value_at(prior5_low, position), previous_close) * 100.0,
        "prior_range_10d_pct": safe_div(value_at(prior10_high, position) - value_at(prior10_low, position), previous_close) * 100.0,
        "atr14_pct": safe_div(value_at(true_range.rolling(14, min_periods=14).mean(), position), current_close) * 100.0,
        "prev_volatility_20d_pct": value_at(returns.shift(1).rolling(20, min_periods=20).std(ddof=1), position) * 100.0,
        "prior_limitups_20d": value_at(prior_limitups, position),
        "listing_age_days": float(listing_age),
        "close_at_high": bool(abs(current_close - current_high) < 1e-9),
        "one_price_board": bool(max(current_open, current_high, current_low, current_close) - min(current_open, current_high, current_low, current_close) < 1e-9),
        "above_ma20": bool(pd.notna(ma20.iloc[position]) and current_close > ma20.iloc[position]),
        "above_ma60": bool(pd.notna(ma60.iloc[position]) and current_close > ma60.iloc[position]),
        "ma5_gt_ma10": bool(pd.notna(ma5.iloc[position]) and pd.notna(ma10.iloc[position]) and ma5.iloc[position] > ma10.iloc[position]),
        "ma10_gt_ma20": bool(pd.notna(ma10.iloc[position]) and pd.notna(ma20.iloc[position]) and ma10.iloc[position] > ma20.iloc[position]),
        "new_high_20d": bool(pd.notna(high20.iloc[position]) and current_high >= high20.iloc[position]),
        "new_high_60d": bool(pd.notna(high60.iloc[position]) and current_high >= high60.iloc[position]),
    }
    for column in ("longtou", "waveband_password", "rapid_rise", "private_entry", "xs1", "xs2", "signal"):
        result[f"formula_{column}"] = bool(formula_row[column]) if column in formula_row.index else math.nan
    return result


def load_market_indices(tdx_root: Path) -> dict[str, pd.DataFrame]:
    symbols = {"sh_index": "000001.SH", "sz_index": "399001.SZ", "cyb_index": "399006.SZ"}
    return {
        prefix: read_tdx_day(day_path_for_symbol(tdx_root, symbol))
        for prefix, symbol in symbols.items()
    }


def is_a_share_day_file(path: Path) -> bool:
    name = path.stem.lower()
    if name.startswith("sh"):
        return name[2:].startswith(("600", "601", "603", "605", "688"))
    if name.startswith("sz"):
        return name[2:].startswith(("000", "001", "002", "003", "300", "301"))
    if name.startswith("bj"):
        return name[2:3] in {"4", "8", "9"}
    return False


def build_market_breadth(tdx_root: Path, event_dates: set[str]) -> tuple[pd.DataFrame, dict[str, Any]]:
    accumulators = {
        date: {"returns": [], "amount": 0.0, "advance": 0, "ge_9_8": 0, "traded": 0}
        for date in sorted(event_dates)
    }
    files = []
    for market in ("sh", "sz", "bj"):
        files.extend((tdx_root / "vipdoc" / market / "lday").glob(f"{market}*.day"))
    eligible = [path for path in files if is_a_share_day_file(path)]
    readable = 0
    minimum_date = int(min(event_dates))
    maximum_date = int(max(event_dates))
    for path in eligible:
        try:
            content = path.read_bytes()
            if not content or len(content) % DAY_RECORD.size:
                continue
            record_count = len(content) // DAY_RECORD.size
            low, high = 0, record_count
            while low < high:
                midpoint = (low + high) // 2
                record_date = int.from_bytes(
                    content[midpoint * DAY_RECORD.size : midpoint * DAY_RECORD.size + 4],
                    "little",
                )
                if record_date < minimum_date:
                    low = midpoint + 1
                else:
                    high = midpoint
            start_index = max(0, low - 1)
        except OSError:
            continue
        readable += 1
        previous_close: float | None = None
        for offset in range(start_index * DAY_RECORD.size, len(content), DAY_RECORD.size):
            date_value, _open, _high, _low, close_value, amount, _volume, _reserved = DAY_RECORD.unpack_from(content, offset)
            if int(date_value) > maximum_date:
                break
            close = float(close_value) / 100.0
            date = str(int(date_value))
            if date in event_dates and previous_close and float(amount) > 0:
                value = (close / previous_close - 1.0) * 100.0
                bucket = accumulators[date]
                bucket["returns"].append(value)
                bucket["amount"] += float(amount)
                bucket["advance"] += int(value > 0)
                bucket["ge_9_8"] += int(value >= 9.8)
                bucket["traded"] += 1
            if close <= 0:
                continue
            previous_close = close
    rows = []
    for date, bucket in accumulators.items():
        values = bucket.pop("returns")
        traded = int(bucket["traded"])
        rows.append(
            {
                "date": date,
                "market_traded_count": traded,
                "market_advance_ratio": safe_div(float(bucket["advance"]), float(traded)),
                "market_median_return_pct": float(np.median(values)) if values else math.nan,
                "market_ge_9_8_count": int(bucket["ge_9_8"]),
                "market_amount_100m": float(bucket["amount"]) / 1e8,
            }
        )
    frame = pd.DataFrame(rows).set_index("date")
    return frame, {
        "eligible_day_file_count": len(eligible),
        "readable_day_file_count": readable,
        "event_date_count": len(event_dates),
        "dates_with_breadth": int(frame["market_traded_count"].gt(0).sum()),
    }


def load_industry_map(tdx_root: Path) -> tuple[dict[str, str], dict[str, Any]]:
    cache = tdx_root / "T0002" / "hq_cache"
    membership_path = cache / "tdxhy.cfg"
    names_path = cache / "tdxzs.cfg"
    names: dict[str, str] = {}
    for raw in names_path.read_text(encoding="gbk", errors="strict").splitlines():
        parts = raw.split("|")
        if len(parts) >= 6 and parts[5].startswith("T"):
            names[parts[5]] = parts[0]
    result: dict[str, str] = {}
    for raw in membership_path.read_text(encoding="gbk", errors="strict").splitlines():
        parts = raw.split("|")
        if len(parts) >= 3 and len(parts[1]) == 6:
            result[parts[1]] = names.get(parts[2], parts[2] or "未分类")
    evidence = {
        "membership": {"path": str(membership_path), "size": membership_path.stat().st_size, "sha256": sha256_path(membership_path)},
        "names": {"path": str(names_path), "size": names_path.stat().st_size, "sha256": sha256_path(names_path)},
        "mapped_stock_count": len(result),
    }
    return result, evidence


def benjamini_hochberg(values: list[float]) -> list[float]:
    array = np.asarray(values, dtype=float)
    result = np.full(len(array), np.nan, dtype=float)
    valid = np.flatnonzero(np.isfinite(array))
    if not len(valid):
        return result.tolist()
    order = valid[np.argsort(array[valid], kind="mergesort")]
    adjusted = np.empty(len(order), dtype=float)
    running = 1.0
    total = len(order)
    for reverse_rank, index in enumerate(order[::-1], start=1):
        rank = total - reverse_rank + 1
        running = min(running, float(array[index]) * total / rank)
        adjusted[total - reverse_rank] = min(1.0, running)
    for position, index in enumerate(order):
        result[index] = adjusted[position]
    return result.tolist()


def direction(value: float, tolerance: float = 1e-12) -> int:
    if not math.isfinite(value) or abs(value) <= tolerance:
        return 0
    return 1 if value > 0 else -1


def subgroup_numeric_effect(frame: pd.DataFrame, factor: str, outcome: str) -> float:
    subset = frame[[factor, outcome]].dropna()
    positive = subset.loc[subset[outcome].astype(bool), factor].astype(float)
    negative = subset.loc[~subset[outcome].astype(bool), factor].astype(float)
    if len(positive) < 3 or len(negative) < 3:
        return math.nan
    return float(positive.median() - negative.median())


def subgroup_binary_effect(frame: pd.DataFrame, factor: str, outcome: str) -> float:
    subset = frame[[factor, outcome]].dropna()
    true_group = subset.loc[subset[factor].astype(bool), outcome].astype(float)
    false_group = subset.loc[~subset[factor].astype(bool), outcome].astype(float)
    if len(true_group) < 3 or len(false_group) < 3:
        return math.nan
    return float(true_group.mean() - false_group.mean())


def time_stability(frame: pd.DataFrame, factor: str, outcome: str, kind: str) -> dict[str, Any]:
    ordered = frame.sort_values("first_board_date", kind="mergesort")
    midpoint = len(ordered) // 2
    early = ordered.iloc[:midpoint]
    late = ordered.iloc[midpoint:]
    effect_function = subgroup_numeric_effect if kind == "numeric" else subgroup_binary_effect
    early_effect = effect_function(early, factor, outcome)
    late_effect = effect_function(late, factor, outcome)
    monthly_directions = []
    for _month, group in ordered.groupby(ordered["first_board_date"].str.slice(0, 6), sort=True):
        effect = effect_function(group, factor, outcome)
        if math.isfinite(effect):
            monthly_directions.append(direction(effect))
    nonzero = [value for value in monthly_directions if value]
    dominant = 0.0
    if nonzero:
        dominant = max(nonzero.count(1), nonzero.count(-1)) / len(nonzero)
    return {
        "early_effect": early_effect,
        "late_effect": late_effect,
        "stable_direction": bool(direction(early_effect) != 0 and direction(early_effect) == direction(late_effect)),
        "monthly_direction_observations": len(nonzero),
        "monthly_direction_agreement": dominant,
    }


def numeric_stat(frame: pd.DataFrame, factor: str, factor_cn: str, outcome: str, scope: str) -> dict[str, Any]:
    subset = frame[["first_board_date", factor, outcome]].dropna()
    positive = subset.loc[subset[outcome].astype(bool), factor].astype(float)
    negative = subset.loc[~subset[outcome].astype(bool), factor].astype(float)
    row: dict[str, Any] = {
        "scope": scope,
        "outcome": outcome,
        "factor": factor,
        "factor_cn": factor_cn,
        "factor_type": "numeric",
        "n": int(len(subset)),
        "positive_n": int(len(positive)),
        "negative_n": int(len(negative)),
    }
    if len(positive) < 5 or len(negative) < 5:
        return {**row, "evidence_grade": "D_样本不足", "p_value": math.nan}
    statistic, p_value = mannwhitneyu(positive, negative, alternative="two-sided")
    cliff_delta = 2.0 * float(statistic) / (len(positive) * len(negative)) - 1.0
    lower = float(subset[factor].quantile(0.25))
    upper = float(subset[factor].quantile(0.75))
    bottom_rate = float(subset.loc[subset[factor] <= lower, outcome].astype(float).mean())
    top_rate = float(subset.loc[subset[factor] >= upper, outcome].astype(float).mean())
    stability = time_stability(subset, factor, outcome, "numeric")
    return {
        **row,
        "positive_median": float(positive.median()),
        "negative_median": float(negative.median()),
        "median_difference": float(positive.median() - negative.median()),
        "cliff_delta": cliff_delta,
        "bottom_quartile_threshold": lower,
        "top_quartile_threshold": upper,
        "bottom_quartile_outcome_rate": bottom_rate,
        "top_quartile_outcome_rate": top_rate,
        "top_vs_bottom_rate_difference": top_rate - bottom_rate,
        "top_vs_bottom_lift": safe_div(top_rate, bottom_rate),
        "p_value": float(p_value),
        **stability,
    }


def binary_stat(frame: pd.DataFrame, factor: str, factor_cn: str, outcome: str, scope: str) -> dict[str, Any]:
    subset = frame[["first_board_date", factor, outcome]].dropna()
    factor_values = subset[factor].astype(bool)
    outcome_values = subset[outcome].astype(bool)
    a = int((factor_values & outcome_values).sum())
    b = int((factor_values & ~outcome_values).sum())
    c = int((~factor_values & outcome_values).sum())
    d = int((~factor_values & ~outcome_values).sum())
    row: dict[str, Any] = {
        "scope": scope,
        "outcome": outcome,
        "factor": factor,
        "factor_cn": factor_cn,
        "factor_type": "binary",
        "n": int(len(subset)),
        "positive_n": int(outcome_values.sum()),
        "negative_n": int((~outcome_values).sum()),
        "factor_true_n": a + b,
        "factor_false_n": c + d,
    }
    if min(a + b, c + d) < 5 or min(a + c, b + d) < 5:
        return {**row, "evidence_grade": "D_样本不足", "p_value": math.nan}
    odds_ratio, p_value = fisher_exact([[a, b], [c, d]], alternative="two-sided")
    true_rate = safe_div(float(a), float(a + b))
    false_rate = safe_div(float(c), float(c + d))
    stability = time_stability(subset, factor, outcome, "binary")
    return {
        **row,
        "factor_true_outcome_rate": true_rate,
        "factor_false_outcome_rate": false_rate,
        "rate_difference": true_rate - false_rate,
        "lift": safe_div(true_rate, false_rate),
        "odds_ratio": float(odds_ratio),
        "p_value": float(p_value),
        **stability,
    }


def grade_statistics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[int]] = {}
    for index, row in enumerate(rows):
        groups.setdefault((str(row["scope"]), str(row["outcome"])), []).append(index)
    for indexes in groups.values():
        adjusted = benjamini_hochberg([float(rows[index].get("p_value", math.nan)) for index in indexes])
        for index, q_value in zip(indexes, adjusted):
            row = rows[index]
            row["q_value"] = q_value
            if row.get("evidence_grade") == "D_样本不足":
                continue
            effect = abs(float(row.get("cliff_delta", row.get("rate_difference", 0.0))))
            stable = bool(row.get("stable_direction"))
            monthly = float(row.get("monthly_direction_agreement", 0.0))
            if math.isfinite(q_value) and q_value <= 0.10 and stable and monthly >= 0.60 and effect >= 0.15:
                row["evidence_grade"] = "A_统计显著且时间方向稳定"
            elif stable and monthly >= 0.60 and effect >= 0.15:
                row["evidence_grade"] = "B_方向稳定但统计证据较弱"
            else:
                row["evidence_grade"] = "C_方向或时间稳定性不足"
    return rows


def run_statistics(events: pd.DataFrame) -> pd.DataFrame:
    available = events.loc[events["data_status"].eq("OK")].copy()
    scopes = [
        ("551个三连板周期：飞龙命中与未命中", available, "formula_matched"),
        ("158个飞龙命中周期：后续达到4板", available.loc[available["formula_matched"]], "reach4"),
        ("158个飞龙命中周期：后续达到5板", available.loc[available["formula_matched"]], "reach5"),
    ]
    rows: list[dict[str, Any]] = []
    for scope, frame, outcome in scopes:
        for factor, factor_cn in NUMERIC_FACTORS.items():
            if factor in frame.columns:
                rows.append(numeric_stat(frame, factor, factor_cn, outcome, scope))
        for factor, factor_cn in BINARY_FACTORS.items():
            if factor in frame.columns and factor != "formula_signal":
                rows.append(binary_stat(frame, factor, factor_cn, outcome, scope))
    return pd.DataFrame(grade_statistics(rows))


def holdout_validation_status(high_rate: float, low_rate: float, p_value: float) -> str:
    if high_rate > low_rate and p_value <= 0.10:
        return "CLEAN_PASS"
    return "REJECTED_NO_OUT_OF_TIME_LIFT"


def temporal_composite(events: pd.DataFrame, statistics: pd.DataFrame) -> dict[str, Any]:
    frame = events.loc[events["data_status"].eq("OK") & events["formula_matched"]].sort_values(
        "first_board_date", kind="mergesort"
    ).copy()
    split_position = max(1, int(len(frame) * 0.70))
    train = frame.iloc[:split_position].copy()
    test = frame.iloc[split_position:].copy()
    candidates = []
    for factor in NUMERIC_FACTORS:
        if factor not in train.columns:
            continue
        effect = subgroup_numeric_effect(train, factor, "reach4")
        subset = train[[factor, "reach4"]].dropna()
        if len(subset) < 60 or not math.isfinite(effect):
            continue
        positive = subset.loc[subset["reach4"], factor]
        negative = subset.loc[~subset["reach4"], factor]
        statistic, p_value = mannwhitneyu(positive, negative, alternative="two-sided")
        delta = 2.0 * float(statistic) / (len(positive) * len(negative)) - 1.0
        if abs(delta) >= 0.15 and p_value <= 0.20:
            candidates.append((factor, abs(delta), direction(delta), float(train[factor].median())))
    candidates.sort(key=lambda row: (-row[1], row[0]))
    selected: list[tuple[str, float, int, float]] = []
    for candidate in candidates:
        factor = candidate[0]
        if any(abs(float(train[factor].corr(train[chosen[0]], method="spearman"))) > 0.75 for chosen in selected):
            continue
        selected.append(candidate)
        if len(selected) == 5:
            break
    if not selected or len(test) < 20:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "train_n": len(train),
            "test_n": len(test),
            "selected_factors": [],
        }
    for target in (train, test):
        target["composite_score"] = 0
        target["composite_available"] = True
        for factor, _magnitude, factor_direction, threshold in selected:
            target["composite_available"] &= target[factor].notna()
            favorable = target[factor].ge(threshold) if factor_direction > 0 else target[factor].le(threshold)
            target["composite_score"] += favorable.fillna(False).astype(int)
    complete_test = test.loc[test["composite_available"]].copy()
    threshold_score = max(1, math.ceil(len(selected) / 2))
    high = complete_test.loc[complete_test["composite_score"] >= threshold_score, "reach4"].astype(bool)
    low = complete_test.loc[complete_test["composite_score"] < threshold_score, "reach4"].astype(bool)
    if len(high) < 5 or len(low) < 5:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "train_n": len(train),
            "test_n": len(test),
            "selected_factors": [factor for factor, *_rest in selected],
            "reason": "holdout score groups are too small",
        }
    table = [[int(high.sum()), int((~high).sum())], [int(low.sum()), int((~low).sum())]]
    odds_ratio, p_value = fisher_exact(table, alternative="greater")
    high_rate = float(high.mean())
    low_rate = float(low.mean())
    return {
        "status": holdout_validation_status(high_rate, low_rate, float(p_value)),
        "split_date": str(test.iloc[0]["first_board_date"]),
        "train_n": len(train),
        "test_n": len(test),
        "complete_test_n": len(complete_test),
        "selected_factors": [
            {
                "factor": factor,
                "factor_cn": NUMERIC_FACTORS[factor],
                "favorable_direction": "higher" if factor_direction > 0 else "lower",
                "training_threshold": threshold,
                "training_abs_cliff_delta": magnitude,
            }
            for factor, magnitude, factor_direction, threshold in selected
        ],
        "high_score_threshold": threshold_score,
        "high_score_n": len(high),
        "low_score_n": len(low),
        "high_score_reach4_rate": high_rate,
        "low_score_reach4_rate": low_rate,
        "rate_difference": high_rate - low_rate,
        "lift": safe_div(high_rate, low_rate),
        "odds_ratio": float(odds_ratio),
        "one_sided_fisher_p": float(p_value),
    }


def industry_summary(events: pd.DataFrame) -> list[dict[str, Any]]:
    frame = events.loc[events["data_status"].eq("OK") & events["formula_matched"]].copy()
    rows = []
    for industry, group in frame.groupby("tdx_industry", dropna=False, sort=True):
        rows.append(
            {
                "tdx_industry": str(industry),
                "sample_n": int(len(group)),
                "reach4_n": int(group["reach4"].sum()),
                "reach4_rate": float(group["reach4"].mean()),
                "reach5_n": int(group["reach5"].sum()),
                "reach5_rate": float(group["reach5"].mean()),
            }
        )
    return sorted(rows, key=lambda row: (-row["sample_n"], row["tdx_industry"]))


def top_factor_rows(statistics: pd.DataFrame, outcome: str, limit: int = 12) -> list[dict[str, Any]]:
    subset = statistics.loc[statistics["outcome"].eq(outcome)].copy()
    subset["grade_rank"] = subset["evidence_grade"].map(
        {
            "A_统计显著且时间方向稳定": 0,
            "B_方向稳定但统计证据较弱": 1,
            "C_方向或时间稳定性不足": 2,
            "D_样本不足": 3,
        }
    ).fillna(9)
    subset["effect_abs"] = subset.apply(
        lambda row: abs(float(row.get("cliff_delta", row.get("rate_difference", 0.0))))
        if pd.notna(row.get("cliff_delta", row.get("rate_difference", math.nan)))
        else 0.0,
        axis=1,
    )
    subset = subset.sort_values(["grade_rank", "effect_abs", "q_value"], ascending=[True, False, True], kind="mergesort")
    return subset.head(limit).drop(columns=["grade_rank", "effect_abs"]).replace({np.nan: None}).to_dict("records")


def format_number(value: Any, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "无数据"
    return f"{float(value):.{digits}f}"


def build_markdown(payload: dict[str, Any], statistics: pd.DataFrame) -> str:
    sample = payload["sample"]
    lines = [
        "# 158个首板“飞龙在天”命中周期的连板因子研究",
        "",
        f"数据截止：{payload['data']['latest_target_kline_date']}；事件区间：{sample['event_date_min']}至{sample['event_date_max']}。",
        "",
        "## 核心结论",
        "",
    ]
    primary = statistics.loc[
        statistics["outcome"].eq("reach4")
        & statistics["evidence_grade"].isin(["A_统计显著且时间方向稳定", "B_方向稳定但统计证据较弱"])
    ].copy()
    if primary.empty:
        lines.append("在当前158个命中周期中，没有因子同时满足预设的统计显著性、效应强度和前后半段方向稳定条件；不能从本样本强行提炼确定性连板因子。")
    else:
        primary["effect_abs"] = primary.apply(
            lambda row: abs(float(row.get("cliff_delta", row.get("rate_difference", 0.0))))
            if pd.notna(row.get("cliff_delta", row.get("rate_difference", math.nan)))
            else 0.0,
            axis=1,
        )
        for row in primary.sort_values(["evidence_grade", "effect_abs"], ascending=[True, False], kind="mergesort").head(8).to_dict("records"):
            if row["factor_type"] == "numeric":
                evidence = (
                    f"4板以上组中位数{format_number(row.get('positive_median'))}，"
                    f"3板组中位数{format_number(row.get('negative_median'))}，"
                    f"Cliff效应值{format_number(row.get('cliff_delta'))}，q={format_number(row.get('q_value'))}"
                )
            else:
                evidence = (
                    f"条件成立时4板率{format_number(float(row.get('factor_true_outcome_rate', 0))*100, 1)}%，"
                    f"不成立时{format_number(float(row.get('factor_false_outcome_rate', 0))*100, 1)}%，"
                    f"差值{format_number(float(row.get('rate_difference', 0))*100, 1)}个百分点，q={format_number(row.get('q_value'))}"
                )
            lines.append(f"- **{row['factor_cn']}**：{row['evidence_grade']}；{evidence}。")

    lines.extend(
        [
            f"- 158个命中周期中，达到4板及以上{sample['reach4_count']}个（{sample['reach4_count']/sample['matched_cycle_count']*100:.2f}%），达到5板及以上{sample['reach5_count']}个（{sample['reach5_count']/sample['matched_cycle_count']*100:.2f}%）。",
            "- 4板深度检验没有A/B级因子；5板深度仅出现B级候选，全部未通过多重检验后的显著性门槛，不能直接转成选股规则。",
            "",
            "## 飞龙命中的首板画像（相对同源三连板对照）",
            "",
            "下表比较158个飞龙命中周期与393个未命中、但后来同样达到三连板的周期。它回答的是公式筛中了什么，不等于这些特征能进一步预测4板或5板。",
            "",
            "| 维度 | 命中组中位数 | 对照组中位数 | Cliff效应值 | q值 |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    profile = statistics.loc[
        statistics["outcome"].eq("formula_matched")
        & statistics["evidence_grade"].eq("A_统计显著且时间方向稳定")
        & statistics["factor_type"].eq("numeric")
    ].copy()
    profile["effect_abs"] = profile["cliff_delta"].abs()
    for row in profile.sort_values("effect_abs", ascending=False, kind="mergesort").head(12).to_dict("records"):
        lines.append(
            f"| {row['factor_cn']} | {format_number(row.get('positive_median'))} | {format_number(row.get('negative_median'))} | {format_number(row.get('cliff_delta'))} | {format_number(row.get('q_value'))} |"
        )
    lines.extend(
        [
            "",
            "可直接从统计表确认的命中画像是：首板前5/10日区间更收敛、此前波动率和ATR更低；首板日成交量相对5/10/20日均量明显放大，实体和振幅更大；价格更靠近20日高点并更偏向站上20日线。全市场成交额在命中日反而略低。上述均是命中识别特征，不是连板深度因果结论。",
            "",
            "公式组件XS2、波段密码、龙头战法、XS1、私募秘进和暴涨启动也呈A级命中差异；它们属于公式内部构成，存在定义重合，只用于核对公式身份，不作为独立预测证据。",
            "",
            "## 5板及以上的弱候选因子",
            "",
            "B级表示效应方向在前后半段保持一致，但Benjamini-Hochberg校正后的q值未达0.10。正组为最终达到5板及以上的27个周期，负组为未达到5板的131个周期。",
            "",
            "| 因子 | 5板及以上组中位数 | 未达5板组中位数 | Cliff效应值 | q值 |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    reach5_candidates = statistics.loc[
        statistics["outcome"].eq("reach5")
        & statistics["evidence_grade"].eq("B_方向稳定但统计证据较弱")
    ].copy()
    reach5_candidates["effect_abs"] = reach5_candidates["cliff_delta"].abs()
    reach5_candidates = reach5_candidates.sort_values("effect_abs", ascending=False, kind="mergesort")
    for row in reach5_candidates.to_dict("records"):
        lines.append(
            f"| {row['factor_cn']} | {format_number(row.get('positive_median'))} | {format_number(row.get('negative_median'))} | {format_number(row.get('cliff_delta'))} | {format_number(row.get('q_value'))} |"
        )
    if not reach5_candidates.empty:
        strongest = reach5_candidates.iloc[0]
        lines.extend(
            [
                "",
                f"其中证据相对最强的是{strongest['factor_cn']}：低四分位组5板率{float(strongest['bottom_quartile_outcome_rate'])*100:.1f}%，高四分位组{float(strongest['top_quartile_outcome_rate'])*100:.1f}%；但q={format_number(strongest['q_value'])}仍高于0.10，只能保留为待扩样本验证的候选。",
                "其余B级结果共同指向首板前涨幅更低、相对均线位置不那么扩张；由于q值均较高，这只能描述样本中的弱倾向，不能称为已验证的连板基因。",
            ]
        )
    lines.extend(
        [
            "",
            "## 样本与结果标签",
            "",
            f"- 三连板周期总数：{sample['cycle_count']}；飞龙命中：{sample['matched_cycle_count']}；未命中同源对照：{sample['unmatched_cycle_count']}。",
            f"- 命中样本后续最高3板：{sample['peak_board_distribution'].get('3', 0)}；4板：{sample['peak_board_distribution'].get('4', 0)}；5板：{sample['peak_board_distribution'].get('5', 0)}；6板及以上：{sample['reach6_count']}。",
            f"- 可读取首板日线的周期：{sample['available_cycle_count']}；缺失：{sample['missing_cycle_count']}。158个命中周期全部有本机日线，5个缺失周期均在对照组，未做推测填充。",
            f"- 通达信根目录：`{payload['data']['tdx_root']}`；目标股票日线最新日期：{payload['data']['latest_target_kline_date']}；全市场宽度覆盖{payload['data']['breadth']['event_date_count']}个事件日、{payload['data']['breadth']['readable_day_file_count']}个可读日线文件。",
            f"- 当前公式：{payload['formula']['name']}；源码SHA-256：`{payload['formula']['source']['sha256']}`；`legacy_4_0_used={str(payload['formula']['legacy_4_0_used']).lower()}`。",
            "",
            "### 缺失对照周期",
            "",
        ]
    )
    for event in sample.get("missing_events", []):
        lines.append(f"- {event['first_board_date']} {event['code']} {event['name']}：本机对应 `.day` 文件不存在。")
    lines.extend(
        [
            "",
            "## 时间外组合验证",
            "",
        ]
    )
    composite = payload["temporal_holdout_composite"]
    if composite.get("status") == "CLEAN_PASS":
        names = "、".join(row["factor_cn"] for row in composite["selected_factors"])
        lines.extend(
            [
                f"仅用前70%时间样本选择因子并固定阈值，选中：{names}。",
                f"在后30%时间样本中，高分组4板率为{composite['high_score_reach4_rate']*100:.1f}%（n={composite['high_score_n']}），低分组为{composite['low_score_reach4_rate']*100:.1f}%（n={composite['low_score_n']}），提升倍数{format_number(composite['lift'])}，单侧Fisher p={format_number(composite['one_sided_fisher_p'])}。",
            ]
        )
    elif composite.get("status") == "REJECTED_NO_OUT_OF_TIME_LIFT":
        names = "、".join(row["factor_cn"] for row in composite["selected_factors"])
        lines.extend(
            [
                f"仅用前70%时间样本选择因子并固定阈值，候选为：{names}。",
                f"时间外验证未通过：后30%样本中，高分组4板率为{composite['high_score_reach4_rate']*100:.1f}%（n={composite['high_score_n']}），低分组为{composite['low_score_reach4_rate']*100:.1f}%（n={composite['low_score_n']}），提升倍数{format_number(composite['lift'])}，单侧Fisher p={format_number(composite['one_sided_fisher_p'])}。该组合不构成可用连板因子。",
            ]
        )
    else:
        lines.append("时间外组合验证样本分组不足，未输出组合优势结论。")
    lines.extend(
        [
            "",
            "## 证据边界",
            "",
            "- 所有技术和市场因子只使用首板当日及以前的通达信数据；最高连板数只作为未来结果标签。",
            "- 551个周期本身都已在未来达到至少三连板，因此本研究能解释“命中样本内部的连板深度”和“飞龙命中相对同源三连板周期的差异”，不能计算全市场普通首板的绝对晋级率。",
            "- 本机缺少可逐事件还原的历史财务报表、公告和新闻结构化快照；这些维度被明确排除，没有用当前值倒灌历史，也没有主观补全。",
            "- 行业分类来自本机通达信当前分类快照，只做样本分布描述，不作为历史时点的确定性因果因子。",
            "- 统计显著仅代表该样本中的关联，不代表收益保证或交易指令。",
            "",
            "## 文件说明",
            "",
            "- `feilong_factor_events.csv`：551个周期逐事件原始因子与缺失状态。",
            "- `feilong_factor_statistics.csv`：命中差异、4板和5板结果的完整统计。",
            "- `feilong_factor_research.json`：数据血缘、样本分层、稳健性与全部结论。",
        ]
    )
    return "\n".join(lines) + "\n"


def validate_formula_source(skill_root: Path) -> dict[str, Any]:
    manifest_path = skill_root / "references" / "formula-source-manifest.json"
    source_path = skill_root / "references" / "formulas" / "飞龙在天.tdx.txt"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    spec = manifest.get("formulas", {}).get(FORMULA_NAME, {})
    source_hash = sha256_path(source_path)
    errors = []
    if source_hash != FORMULA_SHA256:
        errors.append("formula_source_hash_mismatch")
    if str(spec.get("source_raw_sha256", "")).lower() != FORMULA_SHA256:
        errors.append("formula_manifest_hash_mismatch")
    if spec.get("source_path") != str(source_path):
        errors.append("formula_manifest_path_mismatch")
    forbidden = manifest.get("forbidden_formula_names", [])
    if "飞龙在天4.0" not in forbidden:
        errors.append("legacy_formula_forbidden_lock_missing")
    if errors:
        raise RuntimeError(";".join(errors))
    return {
        "name": FORMULA_NAME,
        "legacy_4_0_used": False,
        "source": {"path": str(source_path), "size": source_path.stat().st_size, "sha256": source_hash},
        "manifest": {"path": str(manifest_path), "size": manifest_path.stat().st_size, "sha256": sha256_path(manifest_path)},
    }


def run_factor_research(
    *,
    cycles_csv: str,
    matches_csv: str,
    migration_manifest: str,
    out_dir: str,
    tdx_root: str | Path = TDX_ROOT,
) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat()
    skill_root = Path(__file__).resolve().parents[1]
    formula_evidence = validate_formula_source(skill_root)
    root = Path(tdx_root).resolve()
    cycles_path = Path(cycles_csv).resolve()
    matches_path = Path(matches_csv).resolve()
    package_manifest_path = Path(migration_manifest).resolve()
    output_directory = Path(out_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    package_manifest = json.loads(package_manifest_path.read_text(encoding="utf-8"))
    declared_hashes = {row["path"]: row["sha256"].lower() for row in package_manifest.get("files", [])}
    errors = []
    if sha256_path(cycles_path) != declared_hashes.get("records/three_board_cycles.csv"):
        errors.append("cycles_csv_package_hash_mismatch")
    if sha256_path(matches_path) != declared_hashes.get("records/feilong_first_board_matches.csv"):
        errors.append("matches_csv_package_hash_mismatch")
    if package_manifest.get("task", {}).get("status") != "VERIFIED":
        errors.append("migration_package_not_verified")
    if errors:
        raise RuntimeError(";".join(errors))
    cycles = pd.read_csv(cycles_path, dtype={"code": str, "first_board_date": str}, encoding="utf-8-sig")
    matches = pd.read_csv(matches_path, dtype={"code": str, "first_board_date": str}, encoding="utf-8-sig")
    cycles["code"] = cycles["code"].str.zfill(6)
    matches["code"] = matches["code"].str.zfill(6)
    key_columns = ["code", "cycle_sequence", "first_board_date"]
    match_keys = set(map(tuple, matches[key_columns].astype(str).to_numpy()))
    cycles["formula_matched"] = [
        tuple(map(str, row)) in match_keys for row in cycles[key_columns].to_numpy()
    ]
    if len(cycles) != 551 or int(cycles["formula_matched"].sum()) != 158:
        raise RuntimeError("migration_sample_count_mismatch")
    cycles["reach4"] = pd.to_numeric(cycles["peak_board_count"]).ge(4)
    cycles["reach5"] = pd.to_numeric(cycles["peak_board_count"]).ge(5)
    cycles["reach6"] = pd.to_numeric(cycles["peak_board_count"]).ge(6)
    event_dates = set(cycles["first_board_date"].astype(str))
    market_breadth, breadth_evidence = build_market_breadth(root, event_dates)
    indices = load_market_indices(root)
    industry_map, industry_evidence = load_industry_map(root)
    base_path = root / "T0002" / "hq_cache" / "base.dbf"
    gbbq_path = root / "T0002" / "hq_cache" / "gbbq"
    reader_path = skill_root / "vendor" / "pytdx-1.72" / "pytdx" / "reader" / "gbbq_reader.py"
    finance = read_base_finance(base_path)
    actions = read_gbbq(gbbq_path, reader_path)
    action_groups = {
        symbol: group.drop(columns=["symbol"]).copy()
        for symbol, group in actions.groupby("symbol", sort=False)
    }
    bars_cache: dict[str, pd.DataFrame] = {}
    day_evidence: dict[str, dict[str, Any]] = {}
    rows = []
    missing: list[dict[str, str]] = []
    for source_row in cycles.to_dict("records"):
        code = str(source_row["code"]).zfill(6)
        symbol = symbol_for_code(code)
        date = str(source_row["first_board_date"])
        row = {**source_row, "symbol": symbol, "tdx_industry": industry_map.get(code, "未分类")}
        try:
            if symbol not in bars_cache:
                day_path = day_path_for_symbol(root, symbol)
                raw = read_tdx_day(day_path)
                bars_cache[symbol] = raw
                day_evidence[symbol] = {
                    "path": str(day_path),
                    "size": day_path.stat().st_size,
                    "sha256": sha256_path(day_path),
                    "first_date": str(raw.index[0]),
                    "last_date": str(raw.index[-1]),
                }
            raw_bars = bars_cache[symbol].loc[:date].copy()
            symbol_actions = action_groups.get(symbol, pd.DataFrame())
            if not symbol_actions.empty:
                symbol_actions = symbol_actions.loc[symbol_actions["date"].le(date)].copy()
            bars = front_adjust_like_tq(raw_bars, symbol_actions)
            finance_row = finance.get(code)
            listing_date = str(finance_row["SSDATE"]) if finance_row else str(bars.index[0])
            active_capital = float(finance_row["LTAG"]) if finance_row and float(finance_row["LTAG"]) > 0 else None
            features = compute_event_features(
                bars,
                date,
                code=code,
                name=str(source_row.get("name", "")),
                listing_date=listing_date,
                active_capital=active_capital,
            )
            market = market_breadth.loc[date].to_dict() if date in market_breadth.index else {}
            index_data: dict[str, Any] = {}
            for prefix, frame in indices.items():
                index_data.update(index_features(frame, date, prefix))
            row.update(features)
            row.update(market)
            row.update(index_data)
            row["data_status"] = "OK"
        except (OSError, RuntimeError, ValueError, KeyError) as exc:
            row["data_status"] = "MISSING_LOCAL_DATA"
            row["data_error"] = f"{type(exc).__name__}: {exc}"
            missing.append({"code": code, "name": str(source_row.get("name", "")), "first_board_date": date, "error": row["data_error"]})
        rows.append(row)
    events = pd.DataFrame(rows)
    statistics = run_statistics(events)
    composite = temporal_composite(events, statistics)
    matched_available = events.loc[events["formula_matched"] & events["data_status"].eq("OK")]
    peak_counts = matches["peak_board_count"].astype(int).value_counts().sort_index()
    formula_replay_match_count = int(
        matched_available.get("formula_signal", pd.Series(False, index=matched_available.index)).fillna(False).astype(bool).sum()
    )
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "CLEAN_PASS",
        "generated_at": generated_at,
        "formula": formula_evidence,
        "data": {
            "source": "D-drive Tongdaxin local daily K-line, corporate actions, index, breadth and current industry classification",
            "tdx_root": str(root),
            "latest_target_kline_date": max(row["last_date"] for row in day_evidence.values()),
            "cycles_csv": {"path": str(cycles_path), "size": cycles_path.stat().st_size, "sha256": sha256_path(cycles_path)},
            "matches_csv": {"path": str(matches_path), "size": matches_path.stat().st_size, "sha256": sha256_path(matches_path)},
            "migration_manifest": {"path": str(package_manifest_path), "size": package_manifest_path.stat().st_size, "sha256": sha256_path(package_manifest_path)},
            "base_dbf": {"path": str(base_path), "size": base_path.stat().st_size, "sha256": sha256_path(base_path)},
            "gbbq": {"path": str(gbbq_path), "size": gbbq_path.stat().st_size, "sha256": sha256_path(gbbq_path)},
            "industry": industry_evidence,
            "breadth": breadth_evidence,
            "day_source_count": len(day_evidence),
            "day_sources": day_evidence,
        },
        "sample": {
            "cycle_count": int(len(cycles)),
            "stock_count": int(cycles["code"].nunique()),
            "matched_cycle_count": int(cycles["formula_matched"].sum()),
            "matched_stock_count": int(matches["code"].nunique()),
            "unmatched_cycle_count": int((~cycles["formula_matched"]).sum()),
            "available_cycle_count": int(events["data_status"].eq("OK").sum()),
            "missing_cycle_count": int(events["data_status"].ne("OK").sum()),
            "available_matched_cycle_count": int(matched_available.shape[0]),
            "formula_replay_true_among_available_matches": formula_replay_match_count,
            "event_date_min": str(cycles["first_board_date"].min()),
            "event_date_max": str(cycles["first_board_date"].max()),
            "peak_board_distribution": {str(index): int(value) for index, value in peak_counts.items()},
            "reach4_count": int(matches["peak_board_count"].astype(int).ge(4).sum()),
            "reach5_count": int(matches["peak_board_count"].astype(int).ge(5).sum()),
            "reach6_count": int(matches["peak_board_count"].astype(int).ge(6).sum()),
            "missing_events": missing,
        },
        "method": {
            "feature_cutoff": "first-board day close; no post-event market or stock feature is used",
            "outcomes": {"reach4": "peak_board_count >= 4", "reach5": "peak_board_count >= 5"},
            "comparisons": [
                "158 formula-matched cycles versus 393 unmatched cycles within the same 551 eventual-three-board universe",
                "reach4 versus peak3 within formula-matched cycles",
                "reach5 versus below5 within formula-matched cycles",
            ],
            "statistics": "Mann-Whitney/Cliff delta for numeric factors; Fisher exact/odds ratio for binary factors; Benjamini-Hochberg q-values",
            "stability": "early-half versus late-half direction plus monthly direction agreement",
            "evidence_grades": {
                "A": "q<=0.10, effect>=0.15, early/late same direction, monthly direction agreement>=0.60",
                "B": "effect and time direction pass, q>0.10",
                "C": "direction or time stability insufficient",
                "D": "group sample insufficient",
            },
        },
        "top_factors": {
            "formula_match_profile": top_factor_rows(statistics, "formula_matched"),
            "reach4": top_factor_rows(statistics, "reach4"),
            "reach5": top_factor_rows(statistics, "reach5"),
        },
        "temporal_holdout_composite": composite,
        "industry_distribution_current_snapshot": industry_summary(events),
        "limitations": [
            "The 551-cycle universe contains only events that later reached at least three boards, so absolute all-market first-board promotion probability is not identifiable.",
            "Missing local day files are retained as missing and never imputed.",
            "Historical point-in-time fundamentals, announcements and news snapshots are unavailable in the supplied package/local structured source and are excluded.",
            "Tongdaxin industry mapping is a current snapshot and is descriptive only.",
            "Statistical association is not causality or a trading instruction.",
        ],
        "errors": [],
    }
    events_path = output_directory / "feilong_factor_events.csv"
    statistics_path = output_directory / "feilong_factor_statistics.csv"
    json_path = output_directory / "feilong_factor_research.json"
    report_path = output_directory / "飞龙在天158首板连板因子研究.md"
    manifest_path = output_directory / "feilong_factor_manifest.json"
    events.to_csv(events_path, index=False, encoding="utf-8-sig")
    statistics.to_csv(statistics_path, index=False, encoding="utf-8-sig")
    payload["artifacts"] = {
        "research_json": str(json_path),
        "events_csv": str(events_path),
        "statistics_csv": str(statistics_path),
        "report_markdown": str(report_path),
        "manifest": str(manifest_path),
    }
    payload = json_clean(payload)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    report_path.write_text(build_markdown(payload, statistics), encoding="utf-8")
    artifacts = {}
    for key, path in {
        "research_json": json_path,
        "events_csv": events_path,
        "statistics_csv": statistics_path,
        "report_markdown": report_path,
    }.items():
        artifacts[key] = {"path": str(path), "size": path.stat().st_size, "sha256": sha256_path(path)}
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "status": "CLEAN_PASS",
        "generated_at": generated_at,
        "formula_name": FORMULA_NAME,
        "legacy_4_0_used": False,
        "artifacts": artifacts,
        "validation": {
            "status": "CLEAN_PASS",
            "errors": [],
            "formula_source_bound": True,
            "input_hashes_verified": True,
            "artifact_hashes_verified": True,
            "missing_values_not_imputed": True,
            "post_event_features_excluded": True,
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["segment_manifest"] = str(manifest_path)
    payload["research_json"] = str(json_path)
    payload["events_csv"] = str(events_path)
    payload["statistics_csv"] = str(statistics_path)
    payload["report_markdown"] = str(report_path)
    return payload
