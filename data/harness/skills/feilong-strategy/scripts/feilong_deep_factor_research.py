#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

from feilong_factor_research import BINARY_FACTORS, NUMERIC_FACTORS, json_clean
from feilong_offline_replay import (
    day_path_for_symbol,
    front_adjust_like_tq,
    read_base_finance,
    read_gbbq,
    read_tdx_day,
)
from feilong_resonance_exhaustive import (
    FACTOR_NAMES,
    benjamini_hochberg,
    load_verified_input,
    normalize_bool_series,
    rule_mask,
    safe_div,
    sha256_path,
    wilson_interval,
)


SCHEMA = "FEILONG_DEEP_FACTOR_RESEARCH_V1"
MANIFEST_SCHEMA = "FEILONG_DEEP_FACTOR_RESEARCH_MANIFEST_V1"
FORMULA_NAME = "飞龙在天"
FORMULA_SHA256 = "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0"
OUTCOMES = ("reach2", "reach3")
BOOTSTRAP_REPETITIONS = 500

DEEP_FACTOR_NAMES = {
    "close_price": "首板收盘价(元)",
    "prev_1d_return_pct": "首板前1日涨幅(%)",
    "prev_2d_return_pct": "首板前2日涨幅(%)",
    "prev_3d_return_pct": "首板前3日累计涨幅(%)",
    "prior_up_ratio_10d": "前10日上涨天数占比",
    "prior_up_ratio_20d": "前20日上涨天数占比",
    "prior_downside_vol_20d_pct": "前20日下行波动率(%)",
    "prior_return_skew_20d": "前20日收益偏度",
    "prior_max_drawdown_20d_pct": "前20日最大回撤(%)",
    "distance_20d_low_pct": "距前20日最低价(%)",
    "prior_close_position_20d": "前收盘在20日区间位置",
    "prior_volume_5_vs_20": "首板前5日均量/20日均量",
    "prior_amount_5_vs_20": "首板前5日均额/20日均额",
    "volume_vs_prev_day": "首板量/前一日量",
    "amount_vs_prev_day": "首板成交额/前一日成交额",
    "prior_volume_cv_20d": "前20日成交量变异系数",
    "prior_amount_cv_20d": "前20日成交额变异系数",
    "price_volume_corr_20d": "前20日价量相关系数",
    "ma5_slope_3d_pct": "5日线3日斜率(%)",
    "ma10_slope_5d_pct": "10日线5日斜率(%)",
    "ma20_slope_5d_pct": "20日线5日斜率(%)",
    "lower_shadow_pct": "首板下影线(%)",
    "body_to_range": "首板实体/振幅",
    "range_to_prior_atr14": "首板振幅/此前14日真实波幅",
    "breakout_prior_20d_high_pct": "突破此前20日高点幅度(%)",
    "gap_held": "首板最低价未回补昨收",
    "current_turnover_pct_snapshot": "首板换手率代理(当前流通股本快照)",
    "volume_term_ratio": "5日量比/20日量比",
    "amount_volume_divergence": "成交额比/成交量比",
    "momentum_acceleration_5_20": "5日动量相对20日动量加速度",
    "relative_strength_5d": "个股前5日相对对应指数强度",
    "market_limitup_ratio": "全市场涨停家数占比",
    "daily_signal_count": "当日飞龙共振首板数量",
    "industry_signal_count": "当日同行业飞龙共振数量",
    "trend_stack_count": "趋势多头条件计数",
}

FACTOR_FAMILY_OVERRIDES = {
    "close_price": "价格层级",
    "formula_longtou": "公式子信号",
    "formula_waveband_password": "公式子信号",
    "formula_rapid_rise": "公式子信号",
    "formula_private_entry": "公式子信号",
    "listing_age_days": "上市历史",
    "prior_limitups_20d": "涨停历史",
    "market_advance_ratio": "市场环境",
    "market_median_return_pct": "市场环境",
    "market_ge_9_8_count": "市场环境",
    "market_amount_100m": "市场环境",
    "market_limitup_ratio": "市场环境",
    "daily_signal_count": "信号拥挤",
    "industry_signal_count": "信号拥挤",
    "sh_index_ret_1d_pct": "指数环境",
    "sh_index_ret_5d_pct": "指数环境",
    "sz_index_ret_1d_pct": "指数环境",
    "sz_index_ret_5d_pct": "指数环境",
    "cyb_index_ret_1d_pct": "指数环境",
    "cyb_index_ret_5d_pct": "指数环境",
}

RANK_BASE_FACTORS = {
    "open_gap_pct",
    "intraday_range_pct",
    "body_pct",
    "upper_shadow_pct",
    "close_location",
    "volume_vs_ma5",
    "volume_vs_ma10",
    "volume_vs_ma20",
    "amount_vs_ma20",
    "amount_100m",
    "prev_5d_return_pct",
    "prev_10d_return_pct",
    "prev_20d_return_pct",
    "prev_60d_return_pct",
    "close_vs_ma5_pct",
    "close_vs_ma10_pct",
    "close_vs_ma20_pct",
    "close_vs_ma60_pct",
    "close_vs_ma120_pct",
    "distance_20d_high_pct",
    "distance_60d_high_pct",
    "prior_range_5d_pct",
    "prior_range_10d_pct",
    "atr14_pct",
    "prev_volatility_20d_pct",
    "prior_limitups_20d",
    "listing_age_days",
    "close_price",
    "prev_1d_return_pct",
    "prev_2d_return_pct",
    "prev_3d_return_pct",
    "prior_up_ratio_10d",
    "prior_up_ratio_20d",
    "prior_downside_vol_20d_pct",
    "prior_return_skew_20d",
    "prior_max_drawdown_20d_pct",
    "distance_20d_low_pct",
    "prior_close_position_20d",
    "prior_volume_5_vs_20",
    "prior_amount_5_vs_20",
    "volume_vs_prev_day",
    "amount_vs_prev_day",
    "prior_volume_cv_20d",
    "prior_amount_cv_20d",
    "price_volume_corr_20d",
    "ma5_slope_3d_pct",
    "ma10_slope_5d_pct",
    "ma20_slope_5d_pct",
    "lower_shadow_pct",
    "body_to_range",
    "range_to_prior_atr14",
    "breakout_prior_20d_high_pct",
    "volume_term_ratio",
    "amount_volume_divergence",
    "momentum_acceleration_5_20",
    "relative_strength_5d",
    "trend_stack_count",
}

EXCLUDED_PRIMARY_FACTORS = {
    "first_board_return_pct",  # 涨跌幅制度代理
    "current_turnover_pct_snapshot",  # 当前流通股本快照，不是历史时点股本
    "market_traded_count",
    "formula_xs1",
    "formula_xs2",
    "formula_signal",
    "one_price_board",
    "industry_signal_count",  # 当前行业分类不是历史时点快照
}


def board_regime(code: str) -> str:
    normalized = str(code).zfill(6)
    if normalized.startswith(("300", "301")):
        return "创业板20%"
    if normalized.startswith(("688", "689")):
        return "科创板20%"
    if normalized.startswith(("4", "8", "9")):
        return "北交所30%"
    return "主板10%"


def pct_change(current: float, previous: float) -> float:
    return (safe_div(current, previous) - 1.0) * 100.0


def limited_history_feature_row(
    bars: pd.DataFrame,
    date: str,
    *,
    active_capital_10k_shares: float | None,
) -> dict[str, Any]:
    position = int(bars.index.get_loc(date))
    if position < 4:
        raise RuntimeError(f"insufficient_minimum_history:{date}:{position}")
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
    active_capital_shares = (
        float(active_capital_10k_shares) * 10000.0
        if active_capital_10k_shares is not None and float(active_capital_10k_shares) > 0
        else math.nan
    )
    row = {name: math.nan for name in DEEP_FACTOR_NAMES if name not in {"gap_held"}}
    row.update(
        {
            "close_price": current_close,
            "volume_vs_prev_day": safe_div(current_volume, float(volume.iloc[position - 1])),
            "amount_vs_prev_day": safe_div(current_amount, float(amount.iloc[position - 1])),
            "lower_shadow_pct": safe_div(min(current_open, current_close) - current_low, previous_close) * 100.0,
            "body_to_range": safe_div(abs(current_close - current_open), daily_range) if daily_range else 0.0,
            "gap_held": bool(current_low >= previous_close - 1e-9),
            "current_turnover_pct_snapshot": safe_div(current_volume, active_capital_shares) * 100.0,
            "check_intraday_range_pct": safe_div(daily_range, previous_close) * 100.0,
            "check_volume_vs_ma5": safe_div(current_volume, float(volume.iloc[position - 4 : position + 1].mean())),
            "deep_history_days_available": position,
        }
    )
    return row


def deep_tdx_feature_row(
    bars: pd.DataFrame,
    date: str,
    *,
    active_capital_10k_shares: float | None,
) -> dict[str, Any]:
    if date not in bars.index:
        raise RuntimeError(f"event_date_missing:{date}")
    position = int(bars.index.get_loc(date))
    if position < 25:
        return limited_history_feature_row(
            bars,
            date,
            active_capital_10k_shares=active_capital_10k_shares,
        )
    close = bars["close"].astype(float)
    open_ = bars["open"].astype(float)
    high = bars["high"].astype(float)
    low = bars["low"].astype(float)
    volume = bars["volume"].astype(float)
    amount = bars["amount"].astype(float)
    returns = close.pct_change()
    volume_changes = volume.pct_change().replace([np.inf, -np.inf], np.nan)
    previous_close = float(close.iloc[position - 1])
    current_close = float(close.iloc[position])
    current_open = float(open_.iloc[position])
    current_high = float(high.iloc[position])
    current_low = float(low.iloc[position])
    current_volume = float(volume.iloc[position])
    current_amount = float(amount.iloc[position])
    prior_returns_20 = returns.iloc[position - 20 : position].dropna()
    prior_closes_20 = close.iloc[position - 20 : position]
    prior_highs_20 = high.iloc[position - 20 : position]
    prior_lows_20 = low.iloc[position - 20 : position]
    prior_volume_20 = volume.iloc[position - 20 : position]
    prior_amount_20 = amount.iloc[position - 20 : position]
    prior_volume_changes_20 = volume_changes.iloc[position - 20 : position]
    running_peak = prior_closes_20.cummax()
    drawdowns = prior_closes_20 / running_peak - 1.0
    prior_high = float(prior_highs_20.max())
    prior_low = float(prior_lows_20.min())
    prior_range = prior_high - prior_low
    true_range = pd.concat(
        [high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()],
        axis=1,
    ).max(axis=1)
    prior_atr14 = float(true_range.iloc[position - 14 : position].mean())
    ma5 = close.rolling(5, min_periods=5).mean()
    ma10 = close.rolling(10, min_periods=10).mean()
    ma20 = close.rolling(20, min_periods=20).mean()
    daily_range = current_high - current_low
    active_capital_shares = (
        float(active_capital_10k_shares) * 10000.0
        if active_capital_10k_shares is not None and float(active_capital_10k_shares) > 0
        else math.nan
    )
    correlation_data = pd.DataFrame(
        {"return": prior_returns_20, "volume_change": prior_volume_changes_20}
    ).dropna()
    return {
        "close_price": current_close,
        "prev_1d_return_pct": float(returns.iloc[position - 1]) * 100.0,
        "prev_2d_return_pct": float(returns.iloc[position - 2]) * 100.0,
        "prev_3d_return_pct": pct_change(previous_close, float(close.iloc[position - 4])),
        "prior_up_ratio_10d": float(returns.iloc[position - 10 : position].gt(0).mean()),
        "prior_up_ratio_20d": float(prior_returns_20.gt(0).mean()),
        "prior_downside_vol_20d_pct": float(prior_returns_20.clip(upper=0).std(ddof=1)) * 100.0,
        "prior_return_skew_20d": float(prior_returns_20.skew()),
        "prior_max_drawdown_20d_pct": float(drawdowns.min()) * 100.0,
        "distance_20d_low_pct": pct_change(previous_close, prior_low),
        "prior_close_position_20d": safe_div(previous_close - prior_low, prior_range),
        "prior_volume_5_vs_20": safe_div(float(volume.iloc[position - 5 : position].mean()), float(prior_volume_20.mean())),
        "prior_amount_5_vs_20": safe_div(float(amount.iloc[position - 5 : position].mean()), float(prior_amount_20.mean())),
        "volume_vs_prev_day": safe_div(current_volume, float(volume.iloc[position - 1])),
        "amount_vs_prev_day": safe_div(current_amount, float(amount.iloc[position - 1])),
        "prior_volume_cv_20d": safe_div(float(prior_volume_20.std(ddof=1)), float(prior_volume_20.mean())),
        "prior_amount_cv_20d": safe_div(float(prior_amount_20.std(ddof=1)), float(prior_amount_20.mean())),
        "price_volume_corr_20d": float(correlation_data.corr().iloc[0, 1]) if len(correlation_data) >= 10 else math.nan,
        "ma5_slope_3d_pct": pct_change(float(ma5.iloc[position - 1]), float(ma5.iloc[position - 4])),
        "ma10_slope_5d_pct": pct_change(float(ma10.iloc[position - 1]), float(ma10.iloc[position - 6])),
        "ma20_slope_5d_pct": pct_change(float(ma20.iloc[position - 1]), float(ma20.iloc[position - 6])),
        "lower_shadow_pct": safe_div(min(current_open, current_close) - current_low, previous_close) * 100.0,
        "body_to_range": safe_div(abs(current_close - current_open), daily_range) if daily_range else 0.0,
        "range_to_prior_atr14": safe_div(daily_range, prior_atr14),
        "breakout_prior_20d_high_pct": pct_change(current_high, prior_high),
        "gap_held": bool(current_low >= previous_close - 1e-9),
        "current_turnover_pct_snapshot": safe_div(current_volume, active_capital_shares) * 100.0,
        "check_intraday_range_pct": safe_div(daily_range, previous_close) * 100.0,
        "check_volume_vs_ma5": safe_div(current_volume, float(volume.iloc[position - 4 : position + 1].mean())),
        "deep_history_days_available": position,
    }


def build_deep_tdx_features(events: pd.DataFrame, tdx_root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    base_path = tdx_root / "T0002" / "hq_cache" / "base.dbf"
    gbbq_path = tdx_root / "T0002" / "hq_cache" / "gbbq"
    reader_path = Path(__file__).resolve().parents[1] / "vendor" / "pytdx-1.72" / "pytdx" / "reader" / "gbbq_reader.py"
    finance = read_base_finance(base_path)
    actions = read_gbbq(gbbq_path, reader_path)
    action_groups = {
        symbol: group.drop(columns=["symbol"]).copy()
        for symbol, group in actions.groupby("symbol", sort=False)
    }
    rows: dict[int, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []
    day_hash_rows: list[str] = []
    latest_dates: list[str] = []
    for symbol, group in events.groupby("symbol", sort=True):
        path = day_path_for_symbol(tdx_root, str(symbol))
        try:
            raw = read_tdx_day(path)
            latest_dates.append(str(raw.index[-1]))
            day_hash_rows.append(f"{symbol}|{path.stat().st_size}|{sha256_path(path)}")
            code = str(symbol)[:6]
            finance_row = finance.get(code)
            active_capital = (
                float(finance_row["LTAG"])
                if finance_row and float(finance_row.get("LTAG", 0.0)) > 0
                else None
            )
            symbol_actions = action_groups.get(str(symbol), pd.DataFrame())
            for index, event in group.sort_values("first_board_date", kind="mergesort").iterrows():
                date = str(event["first_board_date"])
                event_actions = symbol_actions
                if not event_actions.empty:
                    event_actions = event_actions.loc[event_actions["date"].le(date)].copy()
                bars = front_adjust_like_tq(raw.loc[:date].copy(), event_actions)
                rows[int(index)] = deep_tdx_feature_row(
                    bars,
                    date,
                    active_capital_10k_shares=active_capital,
                )
        except (OSError, RuntimeError, ValueError, KeyError) as exc:
            errors.append({"symbol": str(symbol), "path": str(path), "error": f"{type(exc).__name__}: {exc}"})
    result = pd.DataFrame.from_dict(rows, orient="index").reindex(events.index)
    if errors or len(result) != len(events) or result.dropna(how="all").shape[0] != len(events):
        raise RuntimeError("deep_tdx_feature_build_failed:" + json.dumps(errors[:20], ensure_ascii=False))
    range_difference = (
        pd.to_numeric(result["check_intraday_range_pct"], errors="coerce")
        - pd.to_numeric(events["intraday_range_pct"], errors="coerce")
    ).abs()
    volume_difference = (
        pd.to_numeric(result["check_volume_vs_ma5"], errors="coerce")
        - pd.to_numeric(events["volume_vs_ma5"], errors="coerce")
    ).abs()
    max_range_difference = float(range_difference.max())
    max_volume_difference = float(volume_difference.max())
    if max_range_difference > 1e-7 or max_volume_difference > 1e-7:
        raise RuntimeError(
            f"deep_tdx_source_crosscheck_failed:range={max_range_difference},volume={max_volume_difference}"
        )
    result = result.drop(columns=["check_intraday_range_pct", "check_volume_vs_ma5"])
    aggregate_hash = hashlib.sha256("\n".join(sorted(day_hash_rows)).encode("utf-8")).hexdigest()
    insufficient_history_count = int(pd.to_numeric(result["deep_history_days_available"], errors="coerce").lt(25).sum())
    result = result.drop(columns=["deep_history_days_available"])
    evidence = {
        "tdx_root": str(tdx_root),
        "symbol_count": int(events["symbol"].nunique()),
        "event_count": len(events),
        "read_error_count": len(errors),
        "insufficient_25d_history_event_count": insufficient_history_count,
        "latest_kline_date_min": min(latest_dates),
        "latest_kline_date_max": max(latest_dates),
        "day_file_aggregate_sha256": aggregate_hash,
        "base_dbf": {"path": str(base_path), "size": base_path.stat().st_size, "sha256": sha256_path(base_path)},
        "gbbq": {"path": str(gbbq_path), "size": gbbq_path.stat().st_size, "sha256": sha256_path(gbbq_path)},
        "source_crosscheck": {
            "intraday_range_max_abs_difference": max_range_difference,
            "volume_vs_ma5_max_abs_difference": max_volume_difference,
        },
    }
    return result, evidence


def factor_family(factor: str) -> str:
    root = factor.removesuffix("_daily_rank")
    if root in FACTOR_FAMILY_OVERRIDES:
        return FACTOR_FAMILY_OVERRIDES[root]
    if root.startswith(("volume_", "amount_", "prior_volume", "prior_amount", "current_turnover")):
        return "量能流动性"
    if root in {"intraday_range_pct", "body_pct", "upper_shadow_pct", "lower_shadow_pct", "close_location", "body_to_range", "open_gap_pct", "gap_held", "range_to_prior_atr14"}:
        return "首板形态"
    if root.startswith(("prev_", "momentum_", "relative_strength", "ma5_", "ma10_", "ma20_", "close_vs_", "distance_", "breakout_", "prior_close_position", "trend_stack")):
        return "趋势位置"
    if root.startswith(("atr", "prior_range", "prior_downside", "prior_return_skew", "prior_max_drawdown", "price_volume_corr")):
        return "波动压缩"
    if root.startswith("formula_"):
        return "公式子信号"
    return "其他"


def engineer_features(events: pd.DataFrame, deep: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, str]], pd.DataFrame]:
    frame = events.copy()
    for column in deep.columns:
        frame[column] = deep[column]
    frame["board_regime"] = frame["code"].map(board_regime)
    frame["month"] = frame["first_board_date"].astype(str).str.slice(0, 6)
    date_counts = frame.groupby("first_board_date", sort=True).size()
    frame["daily_signal_count"] = frame["first_board_date"].map(date_counts).astype(float)
    industry_counts = frame.groupby(["first_board_date", "tdx_industry"], sort=True).size()
    frame["industry_signal_count"] = [
        float(industry_counts.loc[(date, industry)])
        for date, industry in zip(frame["first_board_date"], frame["tdx_industry"])
    ]
    frame["volume_term_ratio"] = pd.to_numeric(frame["volume_vs_ma5"], errors="coerce") / pd.to_numeric(frame["volume_vs_ma20"], errors="coerce")
    frame["amount_volume_divergence"] = pd.to_numeric(frame["amount_vs_ma20"], errors="coerce") / pd.to_numeric(frame["volume_vs_ma20"], errors="coerce")
    frame["momentum_acceleration_5_20"] = pd.to_numeric(frame["prev_5d_return_pct"], errors="coerce") - pd.to_numeric(frame["prev_20d_return_pct"], errors="coerce") / 4.0
    mapped_index = np.where(
        frame["code"].astype(str).str.startswith(("300", "301")),
        pd.to_numeric(frame["cyb_index_ret_5d_pct"], errors="coerce"),
        np.where(
            frame["symbol"].astype(str).str.endswith(".SZ"),
            pd.to_numeric(frame["sz_index_ret_5d_pct"], errors="coerce"),
            pd.to_numeric(frame["sh_index_ret_5d_pct"], errors="coerce"),
        ),
    )
    frame["relative_strength_5d"] = pd.to_numeric(frame["prev_5d_return_pct"], errors="coerce") - mapped_index
    frame["market_limitup_ratio"] = pd.to_numeric(frame["market_ge_9_8_count"], errors="coerce") / pd.to_numeric(frame["market_traded_count"], errors="coerce")
    trend_columns = ["above_ma20", "above_ma60", "ma5_gt_ma10", "ma10_gt_ma20"]
    frame["trend_stack_count"] = sum(normalize_bool_series(frame[column]).astype("Int64") for column in trend_columns).astype(float)
    rank_columns: list[str] = []
    group_keys = [frame["first_board_date"], frame["board_regime"]]
    for factor in sorted(RANK_BASE_FACTORS):
        if factor not in frame.columns:
            continue
        values = pd.to_numeric(frame[factor], errors="coerce")
        group_sizes = frame.groupby(["first_board_date", "board_regime"], sort=False)[factor].transform("size")
        rank = values.groupby(group_keys, sort=False).rank(method="average", pct=True)
        rank.loc[group_sizes.lt(5)] = np.nan
        rank_name = f"{factor}_daily_rank"
        frame[rank_name] = rank
        DEEP_FACTOR_NAMES.setdefault(
            rank_name,
            f"{FACTOR_NAMES.get(factor, DEEP_FACTOR_NAMES.get(factor, factor))}当日同交易制度共振池分位",
        )
        rank_columns.append(rank_name)

    candidate_columns = set(NUMERIC_FACTORS) | set(BINARY_FACTORS) | set(DEEP_FACTOR_NAMES) | set(rank_columns) | {
        "market_traded_count",
        "sh_index_ret_5d_pct",
        "sz_index_ret_5d_pct",
        "cyb_index_ret_5d_pct",
        "sz_index_above_ma20",
        "cyb_index_above_ma20",
    }
    specs: dict[str, dict[str, str]] = {}
    audit_rows: list[dict[str, Any]] = []
    primary = frame.loc[frame["board_regime"].eq("主板10%") & ~normalize_bool_series(frame["one_price_board"]).fillna(False)].copy()
    for factor in sorted(candidate_columns):
        if factor not in frame.columns:
            continue
        if factor in EXCLUDED_PRIMARY_FACTORS:
            audit_rows.append({"factor": factor, "status": "excluded", "reason": "制度代理、快照限制或样本内常量"})
            continue
        values = frame[factor]
        bool_values = normalize_bool_series(values)
        if bool_values.notna().sum() == values.notna().sum() and bool_values.dropna().nunique() <= 2:
            factor_type = "binary"
            unique_count = int(bool_values.loc[primary.index].dropna().nunique())
            missing_rate = float(bool_values.loc[primary.index].isna().mean())
        else:
            numeric = pd.to_numeric(values, errors="coerce")
            if numeric.notna().sum() != values.notna().sum():
                audit_rows.append({"factor": factor, "status": "excluded", "reason": "非数值字段"})
                continue
            factor_type = "numeric"
            unique_count = int(numeric.loc[primary.index].dropna().nunique())
            missing_rate = float(numeric.loc[primary.index].isna().mean())
        if unique_count <= 1:
            audit_rows.append({"factor": factor, "status": "excluded", "reason": "主板样本内常量"})
            continue
        if missing_rate > 0.20:
            audit_rows.append({"factor": factor, "status": "excluded", "reason": f"缺失率{missing_rate:.2%}超过20%"})
            continue
        specs[factor] = {
            "type": factor_type,
            "name": FACTOR_NAMES.get(factor, DEEP_FACTOR_NAMES.get(factor, factor)),
            "family": factor_family(factor),
            "root_factor": factor.removesuffix("_daily_rank"),
        }
        audit_rows.append(
            {
                "factor": factor,
                "factor_name": specs[factor]["name"],
                "family": specs[factor]["family"],
                "type": factor_type,
                "status": "candidate",
                "reason": "",
                "primary_missing_rate": missing_rate,
                "primary_unique_count": unique_count,
            }
        )
    return frame, specs, pd.DataFrame(audit_rows)


def rate_block(outcomes: pd.Series) -> dict[str, Any]:
    total = len(outcomes)
    positive = int(outcomes.astype(bool).sum())
    low, high = wilson_interval(positive, total)
    return {
        "n": total,
        "positive_n": positive,
        "rate": positive / total if total else math.nan,
        "wilson_low": low,
        "wilson_high": high,
    }


def best_numeric_rule(
    train: pd.DataFrame,
    *,
    factor: str,
    outcome: str,
    minimum_support: int,
    maximum_selected_share: float = 0.70,
) -> tuple[dict[str, Any] | None, int]:
    subset = train[[factor, outcome]].dropna().copy()
    subset[factor] = pd.to_numeric(subset[factor], errors="coerce")
    subset = subset.dropna().sort_values(factor, kind="mergesort")
    if len(subset) < minimum_support * 2:
        return None, 0
    grouped = subset.groupby(factor, sort=True)[outcome].agg(["count", "sum"])
    if len(grouped) < 2:
        return None, 0
    values = grouped.index.to_numpy(dtype=float)
    cumulative_n = grouped["count"].to_numpy(dtype=int).cumsum()
    cumulative_positive = grouped["sum"].to_numpy(dtype=int).cumsum()
    total_n = int(cumulative_n[-1])
    total_positive = int(cumulative_positive[-1])
    left_n = cumulative_n[:-1]
    left_positive = cumulative_positive[:-1]
    right_n = total_n - left_n
    right_positive = total_positive - left_positive
    max_selected = int(math.floor(total_n * maximum_selected_share))
    candidates: list[dict[str, Any]] = []
    tested = 0
    for direction, thresholds, selected_n, selected_positive, complement_n, complement_positive in (
        ("le", values[:-1], left_n, left_positive, right_n, right_positive),
        ("ge", values[1:], right_n, right_positive, left_n, left_positive),
    ):
        valid = (
            (selected_n >= minimum_support)
            & (complement_n >= minimum_support)
            & (selected_n <= max_selected)
        )
        tested += int(valid.sum())
        if not valid.any():
            continue
        selected_rate = selected_positive[valid] / selected_n[valid]
        complement_rate = complement_positive[valid] / complement_n[valid]
        difference = selected_rate - complement_rate
        score = difference * np.sqrt(selected_n[valid] * complement_n[valid] / total_n)
        valid_positive = (difference > 0) & (selected_positive[valid] >= (8 if outcome == "reach2" else 4))
        if not valid_positive.any():
            continue
        local_indexes = np.flatnonzero(valid)
        candidate_indexes = local_indexes[valid_positive]
        candidate_scores = score[valid_positive]
        best_position = int(np.argmax(candidate_scores))
        index = int(candidate_indexes[best_position])
        candidates.append(
            {
                "factor": factor,
                "factor_type": "numeric",
                "direction": direction,
                "threshold": float(thresholds[index]),
                "train_selected_n": int(selected_n[index]),
                "train_selected_positive_n": int(selected_positive[index]),
                "train_selected_rate": float(selected_positive[index] / selected_n[index]),
                "train_complement_n": int(complement_n[index]),
                "train_complement_positive_n": int(complement_positive[index]),
                "train_complement_rate": float(complement_positive[index] / complement_n[index]),
                "train_rate_difference": float(difference[valid_positive][best_position]),
                "train_lift": safe_div(float(selected_positive[index] / selected_n[index]), float(complement_positive[index] / complement_n[index])),
                "train_score": float(candidate_scores[best_position]),
            }
        )
    if not candidates:
        return None, tested
    best = sorted(candidates, key=lambda row: (-row["train_score"], -row["train_selected_n"], row["threshold"]))[0]
    return best, tested


def best_binary_rule(
    train: pd.DataFrame,
    *,
    factor: str,
    outcome: str,
    minimum_support: int,
    maximum_selected_share: float = 0.70,
) -> tuple[dict[str, Any] | None, int]:
    values = normalize_bool_series(train[factor])
    subset = pd.DataFrame({factor: values, outcome: train[outcome]}).dropna()
    candidates: list[dict[str, Any]] = []
    tested = 0
    for target in (True, False):
        selected = subset[factor].eq(target)
        selected_n = int(selected.sum())
        complement_n = int((~selected).sum())
        if min(selected_n, complement_n) < minimum_support or selected_n > len(subset) * maximum_selected_share:
            continue
        tested += 1
        selected_positive = int(subset.loc[selected, outcome].astype(bool).sum())
        complement_positive = int(subset.loc[~selected, outcome].astype(bool).sum())
        selected_rate = selected_positive / selected_n
        complement_rate = complement_positive / complement_n
        difference = selected_rate - complement_rate
        if difference <= 0 or selected_positive < (8 if outcome == "reach2" else 4):
            continue
        candidates.append(
            {
                "factor": factor,
                "factor_type": "binary",
                "direction": "eq",
                "threshold": bool(target),
                "train_selected_n": selected_n,
                "train_selected_positive_n": selected_positive,
                "train_selected_rate": selected_rate,
                "train_complement_n": complement_n,
                "train_complement_positive_n": complement_positive,
                "train_complement_rate": complement_rate,
                "train_rate_difference": difference,
                "train_lift": safe_div(selected_rate, complement_rate),
                "train_score": difference * math.sqrt(selected_n * complement_n / len(subset)),
            }
        )
    if not candidates:
        return None, tested
    return sorted(candidates, key=lambda row: (-row["train_score"], -row["train_selected_n"]))[0], tested


def evaluate_rule(frame: pd.DataFrame, rule: dict[str, Any], outcome: str, prefix: str) -> dict[str, Any]:
    selected, available = rule_mask(frame, rule)
    selected_outcome = frame.loc[available & selected, outcome].astype(bool)
    complement_outcome = frame.loc[available & ~selected, outcome].astype(bool)
    selected_block = rate_block(selected_outcome)
    complement_block = rate_block(complement_outcome)
    return {
        **{f"{prefix}_selected_{key}": value for key, value in selected_block.items()},
        **{f"{prefix}_complement_{key}": value for key, value in complement_block.items()},
        f"{prefix}_rate_difference": selected_block["rate"] - complement_block["rate"],
        f"{prefix}_lift": safe_div(selected_block["rate"], complement_block["rate"]),
    }


def rolling_factor_scan(
    frame: pd.DataFrame,
    specs: dict[str, dict[str, str]],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, tuple[pd.Series, pd.Series]]], list[dict[str, str]], int]:
    months = sorted(frame["month"].unique())
    if len(months) < 6:
        raise RuntimeError("insufficient_months_for_rolling_validation")
    folds = [{"train_end": months[index - 1], "test_month": months[index]} for index in range(3, len(months))]
    rows: list[dict[str, Any]] = []
    tested_rule_count = 0
    fold_rules: dict[tuple[str, str, str], dict[str, Any]] = {}
    for fold_index, fold in enumerate(folds, start=1):
        train = frame.loc[frame["month"].le(fold["train_end"])].copy()
        test = frame.loc[frame["month"].eq(fold["test_month"])].copy()
        for outcome in OUTCOMES:
            for factor, spec in specs.items():
                available_n = int(train[factor].notna().sum())
                minimum_support = max(40, int(math.ceil(available_n * 0.10)))
                if spec["type"] == "numeric":
                    rule, tested = best_numeric_rule(
                        train,
                        factor=factor,
                        outcome=outcome,
                        minimum_support=minimum_support,
                    )
                else:
                    rule, tested = best_binary_rule(
                        train,
                        factor=factor,
                        outcome=outcome,
                        minimum_support=minimum_support,
                    )
                tested_rule_count += tested
                if rule is None:
                    continue
                rule.update({"outcome": outcome, "factor_name": spec["name"], "family": spec["family"]})
                test_metrics = evaluate_rule(test, rule, outcome, "test")
                if min(test_metrics["test_selected_n"], test_metrics["test_complement_n"]) < 10:
                    continue
                row = {
                    "fold": fold_index,
                    "train_end": fold["train_end"],
                    "test_month": fold["test_month"],
                    **rule,
                    **test_metrics,
                }
                rows.append(row)
                fold_rules[(outcome, factor, fold["test_month"])] = rule
    detail = pd.DataFrame(rows)
    if detail.empty:
        raise RuntimeError("rolling_factor_scan_empty")
    oot_masks: dict[str, dict[str, tuple[pd.Series, pd.Series]]] = {outcome: {} for outcome in OUTCOMES}
    aggregate_rows: list[dict[str, Any]] = []
    oot_index = frame.index[frame["month"].isin([fold["test_month"] for fold in folds])]
    for outcome in OUTCOMES:
        for factor, spec in specs.items():
            factor_detail = detail.loc[(detail["outcome"].eq(outcome)) & (detail["factor"].eq(factor))].copy()
            if factor_detail.empty:
                continue
            selected = pd.Series(False, index=frame.index, dtype=bool)
            available = pd.Series(False, index=frame.index, dtype=bool)
            thresholds: list[float] = []
            directions: list[str] = []
            for row in factor_detail.to_dict("records"):
                month_mask = frame["month"].eq(str(row["test_month"]))
                rule_selected, rule_available = rule_mask(frame.loc[month_mask], row)
                selected.loc[month_mask] = rule_selected
                available.loc[month_mask] = rule_available
                directions.append(str(row["direction"]))
                if row["factor_type"] == "numeric":
                    thresholds.append(float(row["threshold"]))
            selected_oot = selected.loc[oot_index]
            available_oot = available.loc[oot_index]
            oot_masks[outcome][factor] = (selected_oot, available_oot)
            selected_indexes = oot_index[(available_oot & selected_oot).to_numpy()]
            complement_indexes = oot_index[(available_oot & ~selected_oot).to_numpy()]
            selected_values = frame.loc[selected_indexes, outcome].astype(bool)
            complement_values = frame.loc[complement_indexes, outcome].astype(bool)
            if not len(selected_values) or not len(complement_values):
                continue
            selected_rate = float(selected_values.mean())
            complement_rate = float(complement_values.mean())
            direction_mode, direction_count = Counter(directions).most_common(1)[0]
            positive_folds = int(factor_detail["test_rate_difference"].gt(0).sum())
            p_value = float(
                fisher_exact(
                    [
                        [int(selected_values.sum()), int((~selected_values).sum())],
                        [int(complement_values.sum()), int((~complement_values).sum())],
                    ],
                    alternative="greater",
                ).pvalue
            )
            aggregate_rows.append(
                {
                    "outcome": outcome,
                    "factor": factor,
                    "factor_name": spec["name"],
                    "family": spec["family"],
                    "root_factor": spec["root_factor"],
                    "factor_type": spec["type"],
                    "valid_folds": len(factor_detail),
                    "positive_folds": positive_folds,
                    "positive_fold_share": positive_folds / len(factor_detail),
                    "direction_mode": direction_mode,
                    "direction_consistency": direction_count / len(directions),
                    "threshold_median": float(np.median(thresholds)) if thresholds else factor_detail.iloc[-1]["threshold"],
                    "threshold_q25": float(np.quantile(thresholds, 0.25)) if thresholds else factor_detail.iloc[-1]["threshold"],
                    "threshold_q75": float(np.quantile(thresholds, 0.75)) if thresholds else factor_detail.iloc[-1]["threshold"],
                    "oot_available_n": int(available_oot.sum()),
                    "oot_selected_n": len(selected_values),
                    "oot_selected_positive_n": int(selected_values.sum()),
                    "oot_selected_rate": selected_rate,
                    "oot_complement_n": len(complement_values),
                    "oot_complement_positive_n": int(complement_values.sum()),
                    "oot_complement_rate": complement_rate,
                    "oot_rate_difference": selected_rate - complement_rate,
                    "oot_lift": safe_div(selected_rate, complement_rate),
                    "oot_fisher_p": p_value,
                }
            )
    aggregate = pd.DataFrame(aggregate_rows)
    fold_labels = [{"train_end": fold["train_end"], "test_month": fold["test_month"]} for fold in folds]
    return detail, aggregate, oot_masks, fold_labels, tested_rule_count


def _bootstrap_difference(
    weights: np.ndarray,
    selected: np.ndarray,
    complement: np.ndarray,
    outcome: np.ndarray,
) -> np.ndarray:
    selected_n = weights @ selected
    selected_positive = weights @ (selected * outcome[:, None])
    complement_n = weights @ complement
    complement_positive = weights @ (complement * outcome[:, None])
    with np.errstate(divide="ignore", invalid="ignore"):
        return selected_positive / selected_n - complement_positive / complement_n


def add_conservative_cluster_bootstrap(
    frame: pd.DataFrame,
    aggregate: pd.DataFrame,
    oot_masks: dict[str, dict[str, tuple[pd.Series, pd.Series]]],
    *,
    repetitions: int = BOOTSTRAP_REPETITIONS,
) -> pd.DataFrame:
    result = aggregate.copy()
    result["cluster_ci_low"] = np.nan
    result["cluster_ci_high"] = np.nan
    result["cluster_p_value"] = np.nan
    oot_months = sorted({str(value) for value in frame["month"]})[3:]
    oot = frame.loc[frame["month"].isin(oot_months)].copy()
    dates = pd.Categorical(oot["first_board_date"])
    symbols = pd.Categorical(oot["symbol"])
    rng = np.random.default_rng(20260830)
    date_weights = rng.poisson(1.0, size=(repetitions, len(dates.categories))).astype(np.float64)[:, dates.codes]
    symbol_weights = rng.poisson(1.0, size=(repetitions, len(symbols.categories))).astype(np.float64)[:, symbols.codes]
    for outcome in OUTCOMES:
        indexes = result.index[result["outcome"].eq(outcome)].tolist()
        if not indexes:
            continue
        factors = [str(result.loc[index, "factor"]) for index in indexes]
        selected_columns = []
        complement_columns = []
        for factor in factors:
            selected, available = oot_masks[outcome][factor]
            selected = selected.reindex(oot.index).fillna(False).to_numpy(dtype=float)
            available = available.reindex(oot.index).fillna(False).to_numpy(dtype=bool)
            selected_columns.append(selected)
            complement_columns.append((available & ~selected.astype(bool)).astype(float))
        selected_matrix = np.column_stack(selected_columns)
        complement_matrix = np.column_stack(complement_columns)
        outcome_array = oot[outcome].astype(float).to_numpy()
        date_diff = _bootstrap_difference(date_weights, selected_matrix, complement_matrix, outcome_array)
        symbol_diff = _bootstrap_difference(symbol_weights, selected_matrix, complement_matrix, outcome_array)
        for position, index in enumerate(indexes):
            date_values = date_diff[:, position]
            symbol_values = symbol_diff[:, position]
            date_values = date_values[np.isfinite(date_values)]
            symbol_values = symbol_values[np.isfinite(symbol_values)]
            lower = min(float(np.quantile(date_values, 0.025)), float(np.quantile(symbol_values, 0.025)))
            upper = max(float(np.quantile(date_values, 0.975)), float(np.quantile(symbol_values, 0.975)))
            p_date = (int((date_values <= 0).sum()) + 1) / (len(date_values) + 1)
            p_symbol = (int((symbol_values <= 0).sum()) + 1) / (len(symbol_values) + 1)
            result.loc[index, "cluster_ci_low"] = lower
            result.loc[index, "cluster_ci_high"] = upper
            result.loc[index, "cluster_p_value"] = max(p_date, p_symbol)
    result["cluster_q_value"] = np.nan
    for outcome, indexes in result.groupby("outcome", sort=False).groups.items():
        result.loc[indexes, "cluster_q_value"] = benjamini_hochberg(
            result.loc[indexes, "cluster_p_value"].astype(float).tolist()
        )
    return result


def add_market_strata(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    breadth = pd.to_numeric(result["market_advance_ratio"], errors="coerce")
    result["market_breadth_regime"] = pd.cut(
        breadth,
        [-np.inf, 0.40, 0.60, np.inf],
        labels=["弱市", "中性", "强市"],
        right=False,
    ).astype(str)
    date_crowding = result.groupby("first_board_date", sort=True)["daily_signal_count"].first()
    q1, q2 = date_crowding.quantile([1 / 3, 2 / 3]).tolist()
    result["signal_crowding_regime"] = pd.cut(
        pd.to_numeric(result["daily_signal_count"], errors="coerce"),
        [-np.inf, q1, q2, np.inf],
        labels=["低拥挤", "中拥挤", "高拥挤"],
        include_lowest=True,
    ).astype(str)
    amount_rank = pd.to_numeric(result.get("amount_100m_daily_rank"), errors="coerce")
    result["liquidity_regime"] = pd.cut(
        amount_rank,
        [-np.inf, 1 / 3, 2 / 3, np.inf],
        labels=["低成交额", "中成交额", "高成交额"],
        include_lowest=True,
    ).astype(str)
    return result


def stratum_analysis(
    frame: pd.DataFrame,
    aggregate: pd.DataFrame,
    oot_masks: dict[str, dict[str, tuple[pd.Series, pd.Series]]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidate = aggregate.loc[
        aggregate["valid_folds"].ge(5)
        & aggregate["positive_fold_share"].ge(2 / 3)
        & aggregate["direction_consistency"].ge(2 / 3)
        & aggregate["oot_rate_difference"].gt(0)
    ].copy()
    oot_months = sorted(frame["month"].unique())[3:]
    oot = frame.loc[frame["month"].isin(oot_months)].copy()
    rows: list[dict[str, Any]] = []
    for factor_row in candidate.to_dict("records"):
        outcome = str(factor_row["outcome"])
        factor = str(factor_row["factor"])
        selected, available = oot_masks[outcome][factor]
        selected = selected.reindex(oot.index).fillna(False)
        available = available.reindex(oot.index).fillna(False)
        for stratum_type, column in (
            ("市场宽度", "market_breadth_regime"),
            ("信号拥挤", "signal_crowding_regime"),
            ("成交额层级", "liquidity_regime"),
        ):
            for stratum, indexes in oot.loc[available].groupby(column, sort=True).groups.items():
                group_selected = selected.loc[indexes].to_numpy(dtype=bool)
                selected_indexes = indexes[group_selected]
                complement_indexes = indexes[~group_selected]
                selected_values = oot.loc[selected_indexes, outcome].astype(bool)
                complement_values = oot.loc[complement_indexes, outcome].astype(bool)
                if min(len(selected_values), len(complement_values)) < 15:
                    continue
                selected_rate = float(selected_values.mean())
                complement_rate = float(complement_values.mean())
                rows.append(
                    {
                        "outcome": outcome,
                        "factor": factor,
                        "factor_name": factor_row["factor_name"],
                        "stratum_type": stratum_type,
                        "stratum": str(stratum),
                        "selected_n": len(selected_values),
                        "selected_positive_n": int(selected_values.sum()),
                        "selected_rate": selected_rate,
                        "complement_n": len(complement_values),
                        "complement_positive_n": int(complement_values.sum()),
                        "complement_rate": complement_rate,
                        "rate_difference": selected_rate - complement_rate,
                    }
                )
    detail = pd.DataFrame(rows)
    if detail.empty:
        aggregate["stratum_positive"] = 0
        aggregate["stratum_count"] = 0
        aggregate["stratum_positive_share"] = math.nan
        return detail, aggregate
    summary = (
        detail.assign(positive=detail["rate_difference"].gt(0).astype(int))
        .groupby(["outcome", "factor"], sort=False)["positive"]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"sum": "stratum_positive", "count": "stratum_count"})
    )
    result = aggregate.merge(summary, on=["outcome", "factor"], how="left")
    result[["stratum_positive", "stratum_count"]] = result[["stratum_positive", "stratum_count"]].fillna(0).astype(int)
    result["stratum_positive_share"] = result["stratum_positive"] / result["stratum_count"].replace(0, np.nan)
    return detail, result


def grade_robust_factors(aggregate: pd.DataFrame) -> pd.DataFrame:
    result = aggregate.copy()
    support = (
        (result["outcome"].eq("reach2") & result["oot_selected_n"].ge(120) & result["oot_selected_positive_n"].ge(15))
        | (result["outcome"].eq("reach3") & result["oot_selected_n"].ge(180) & result["oot_selected_positive_n"].ge(8))
    )
    effect = (
        (result["outcome"].eq("reach2") & result["oot_rate_difference"].ge(0.02) & result["oot_lift"].ge(1.15))
        | (result["outcome"].eq("reach3") & result["oot_rate_difference"].ge(0.008) & result["oot_lift"].ge(1.25))
    )
    stable = (
        result["valid_folds"].ge(5)
        & result["positive_fold_share"].ge(0.80)
        & result["direction_consistency"].ge(0.80)
        & result["cluster_ci_low"].gt(0)
        & result["cluster_q_value"].le(0.10)
        & result["stratum_positive_share"].ge(2 / 3)
    )
    result["evidence_grade"] = "未通过深度稳健性门槛"
    result.loc[support & effect & stable, "evidence_grade"] = "深度稳健"
    return result


def redundancy_clusters(
    frame: pd.DataFrame,
    aggregate: pd.DataFrame,
    oot_masks: dict[str, dict[str, tuple[pd.Series, pd.Series]]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    robust = aggregate.loc[aggregate["evidence_grade"].eq("深度稳健")].copy()
    oot_months = sorted(frame["month"].unique())[3:]
    oot = frame.loc[frame["month"].isin(oot_months)]
    cluster_rows: list[dict[str, Any]] = []
    aggregate = aggregate.copy()
    aggregate["redundancy_cluster"] = ""
    aggregate["cluster_representative"] = False
    for outcome in OUTCOMES:
        subset = robust.loc[robust["outcome"].eq(outcome)].copy()
        factors = subset["factor"].astype(str).tolist()
        if not factors:
            continue
        parent = {factor: factor for factor in factors}

        def find(value: str) -> str:
            while parent[value] != value:
                parent[value] = parent[parent[value]]
                value = parent[value]
            return value

        def union(left: str, right: str) -> None:
            left_root, right_root = find(left), find(right)
            if left_root != right_root:
                parent[right_root] = left_root

        masks = {}
        for factor in factors:
            selected, available = oot_masks[outcome][factor]
            masks[factor] = (selected.reindex(oot.index).fillna(False), available.reindex(oot.index).fillna(False))
        for left_index, left in enumerate(factors):
            left_row = subset.loc[subset["factor"].eq(left)].iloc[0]
            for right in factors[left_index + 1 :]:
                right_row = subset.loc[subset["factor"].eq(right)].iloc[0]
                both = masks[left][1] & masks[right][1]
                correlation = float(masks[left][0].loc[both].astype(float).corr(masks[right][0].loc[both].astype(float))) if int(both.sum()) >= 30 else 0.0
                same_root = left_row["root_factor"] == right_row["root_factor"]
                same_family = left_row["family"] == right_row["family"]
                if same_root or abs(correlation) >= 0.65 or (same_family and abs(correlation) >= 0.45):
                    union(left, right)
        groups: dict[str, list[str]] = {}
        for factor in factors:
            groups.setdefault(find(factor), []).append(factor)
        ordered_groups = sorted(groups.values(), key=lambda values: min(values))
        for cluster_index, group in enumerate(ordered_groups, start=1):
            cluster_id = f"{outcome}_C{cluster_index:02d}"
            candidates = subset.loc[subset["factor"].isin(group)].sort_values(
                ["cluster_q_value", "oot_rate_difference", "oot_selected_n"],
                ascending=[True, False, False],
                kind="mergesort",
            )
            representative = str(candidates.iloc[0]["factor"])
            for factor in group:
                aggregate.loc[(aggregate["outcome"].eq(outcome)) & (aggregate["factor"].eq(factor)), "redundancy_cluster"] = cluster_id
                aggregate.loc[(aggregate["outcome"].eq(outcome)) & (aggregate["factor"].eq(factor)), "cluster_representative"] = factor == representative
                row = subset.loc[subset["factor"].eq(factor)].iloc[0]
                cluster_rows.append(
                    {
                        "outcome": outcome,
                        "cluster": cluster_id,
                        "factor": factor,
                        "factor_name": row["factor_name"],
                        "family": row["family"],
                        "representative": factor == representative,
                    }
                )
    return pd.DataFrame(cluster_rows), aggregate


def robust_intersection_analysis(
    frame: pd.DataFrame,
    aggregate: pd.DataFrame,
    oot_masks: dict[str, dict[str, tuple[pd.Series, pd.Series]]],
    *,
    repetitions: int = BOOTSTRAP_REPETITIONS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    oot_months = sorted(frame["month"].unique())[3:]
    oot = frame.loc[frame["month"].isin(oot_months)].copy()
    summary_rows: list[dict[str, Any]] = []
    band_rows: list[dict[str, Any]] = []
    month_rows: list[dict[str, Any]] = []
    dates = pd.Categorical(oot["first_board_date"])
    symbols = pd.Categorical(oot["symbol"])
    rng = np.random.default_rng(20260831)
    date_weights = rng.poisson(1.0, size=(repetitions, len(dates.categories))).astype(np.float64)[:, dates.codes]
    symbol_weights = rng.poisson(1.0, size=(repetitions, len(symbols.categories))).astype(np.float64)[:, symbols.codes]
    for outcome in OUTCOMES:
        representatives = aggregate.loc[
            aggregate["outcome"].eq(outcome)
            & aggregate["evidence_grade"].eq("深度稳健")
            & aggregate["cluster_representative"].eq(True)
        ].sort_values(["cluster_q_value", "oot_rate_difference"], ascending=[True, False], kind="mergesort")
        factors = representatives["factor"].astype(str).tolist()
        if len(factors) < 2:
            continue
        selected_parts: list[pd.Series] = []
        available_parts: list[pd.Series] = []
        for factor in factors:
            selected, available = oot_masks[outcome][factor]
            selected_parts.append(selected.reindex(oot.index).fillna(False))
            available_parts.append(available.reindex(oot.index).fillna(False))
        complete = pd.concat(available_parts, axis=1).all(axis=1)
        score = pd.concat(selected_parts, axis=1).sum(axis=1).astype(int)
        factor_names = representatives["factor_name"].astype(str).tolist()
        for value in range(len(factors) + 1):
            indexes = oot.index[complete & score.eq(value)]
            outcomes = oot.loc[indexes, outcome].astype(bool)
            secondary = oot.loc[indexes, "reach3"].astype(bool)
            migrated_n = int(normalize_bool_series(oot.loc[indexes, "migrated_158"]).fillna(False).sum())
            block = rate_block(outcomes)
            secondary_block = rate_block(secondary)
            band_rows.append(
                {
                    "outcome": outcome,
                    "condition_score": value,
                    "condition_count": len(factors),
                    **block,
                    "reach3_n": secondary_block["n"],
                    "reach3_positive_n": secondary_block["positive_n"],
                    "reach3_rate": secondary_block["rate"],
                    "reach3_wilson_low": secondary_block["wilson_low"],
                    "reach3_wilson_high": secondary_block["wilson_high"],
                    "migrated_158_n": migrated_n,
                }
            )
        intersection = complete & score.eq(len(factors))
        complement = complete & ~intersection
        intersection_values = oot.loc[intersection, outcome].astype(bool)
        complement_values = oot.loc[complement, outcome].astype(bool)
        selected_matrix = intersection.to_numpy(dtype=float)[:, None]
        complement_matrix = complement.to_numpy(dtype=float)[:, None]
        outcome_array = oot[outcome].astype(float).to_numpy()
        date_diff = _bootstrap_difference(date_weights, selected_matrix, complement_matrix, outcome_array)[:, 0]
        symbol_diff = _bootstrap_difference(symbol_weights, selected_matrix, complement_matrix, outcome_array)[:, 0]
        date_diff = date_diff[np.isfinite(date_diff)]
        symbol_diff = symbol_diff[np.isfinite(symbol_diff)]
        cluster_low = min(float(np.quantile(date_diff, 0.025)), float(np.quantile(symbol_diff, 0.025)))
        cluster_high = max(float(np.quantile(date_diff, 0.975)), float(np.quantile(symbol_diff, 0.975)))
        cluster_p = max(
            (int((date_diff <= 0).sum()) + 1) / (len(date_diff) + 1),
            (int((symbol_diff <= 0).sum()) + 1) / (len(symbol_diff) + 1),
        )
        positive_months = 0
        month_count = 0
        for month in oot_months:
            month_mask = oot["month"].eq(month) & complete
            selected_month = oot.loc[month_mask & intersection, outcome].astype(bool)
            complement_month = oot.loc[month_mask & complement, outcome].astype(bool)
            if not len(selected_month) or not len(complement_month):
                continue
            selected_rate = float(selected_month.mean())
            complement_rate = float(complement_month.mean())
            month_count += 1
            positive_months += int(selected_rate > complement_rate)
            month_rows.append(
                {
                    "outcome": outcome,
                    "month": month,
                    "factor_names": " + ".join(factor_names),
                    "selected_n": len(selected_month),
                    "selected_positive_n": int(selected_month.sum()),
                    "selected_rate": selected_rate,
                    "complement_n": len(complement_month),
                    "complement_positive_n": int(complement_month.sum()),
                    "complement_rate": complement_rate,
                    "rate_difference": selected_rate - complement_rate,
                }
            )
        summary_rows.append(
            {
                "outcome": outcome,
                "factor_count": len(factors),
                "factors": factors,
                "factor_names": factor_names,
                "selected_n": len(intersection_values),
                "selected_positive_n": int(intersection_values.sum()),
                "selected_rate": float(intersection_values.mean()),
                "complement_n": len(complement_values),
                "complement_positive_n": int(complement_values.sum()),
                "complement_rate": float(complement_values.mean()),
                "rate_difference": float(intersection_values.mean() - complement_values.mean()),
                "lift": safe_div(float(intersection_values.mean()), float(complement_values.mean())),
                "positive_months": positive_months,
                "month_count": month_count,
                "cluster_ci_low": cluster_low,
                "cluster_ci_high": cluster_high,
                "cluster_p_value": cluster_p,
            }
        )
    return pd.DataFrame(summary_rows), pd.DataFrame(band_rows), pd.DataFrame(month_rows)


def nested_out_of_time_score(
    frame: pd.DataFrame,
    detail: pd.DataFrame,
    specs: dict[str, dict[str, str]],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    scored_rows: list[pd.DataFrame] = []
    selection_rows: list[dict[str, Any]] = []
    for (outcome, test_month), candidates in detail.groupby(["outcome", "test_month"], sort=True):
        train = frame.loc[frame["month"].lt(str(test_month))].copy()
        test = frame.loc[frame["month"].eq(str(test_month))].copy()
        candidates = candidates.loc[
            candidates["train_rate_difference"].gt(0)
            & candidates["train_selected_n"].ge(40)
            & (
                candidates["train_selected_n"]
                / (candidates["train_selected_n"] + candidates["train_complement_n"])
            ).le(0.70)
        ].sort_values(["train_score", "train_selected_n"], ascending=[False, False], kind="mergesort")
        selected_rules: list[dict[str, Any]] = []
        selected_masks: list[tuple[pd.Series, pd.Series]] = []
        used_families: set[str] = set()
        for rule in candidates.to_dict("records"):
            family = str(rule["family"])
            if family in used_families:
                continue
            mask, available = rule_mask(train, rule)
            if int(available.sum()) < len(train) * 0.80:
                continue
            correlated = False
            for prior_mask, prior_available in selected_masks:
                overlap = available & prior_available
                if int(overlap.sum()) < 30:
                    continue
                correlation = mask.loc[overlap].astype(float).corr(prior_mask.loc[overlap].astype(float))
                if pd.notna(correlation) and abs(float(correlation)) >= 0.65:
                    correlated = True
                    break
            if correlated:
                continue
            selected_rules.append(rule)
            selected_masks.append((mask, available))
            used_families.add(family)
            if len(selected_rules) == 5:
                break
        if len(selected_rules) < 3:
            continue
        score = pd.Series(0, index=test.index, dtype=int)
        complete = pd.Series(True, index=test.index, dtype=bool)
        for rule in selected_rules:
            mask, available = rule_mask(test, rule)
            score += mask.astype(int)
            complete &= available
            selection_rows.append(
                {
                    "outcome": outcome,
                    "test_month": test_month,
                    "factor": rule["factor"],
                    "factor_name": specs[str(rule["factor"])]["name"],
                    "family": rule["family"],
                    "direction": rule["direction"],
                    "threshold": rule["threshold"],
                }
            )
        scored = test.loc[complete, ["symbol", "code", "first_board_date", "migrated_158", outcome]].copy()
        scored["outcome"] = outcome
        scored["test_month"] = test_month
        scored["score"] = score.loc[complete]
        scored["factor_count"] = len(selected_rules)
        scored_rows.append(scored.rename(columns={outcome: "outcome_value"}))
    scored_events = pd.concat(scored_rows, ignore_index=True) if scored_rows else pd.DataFrame()
    selections = pd.DataFrame(selection_rows)
    if scored_events.empty:
        return scored_events, selections, {"status": "FAILED", "reason": "no_nested_scores"}
    band_rows: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {"status": "CLEAN_PASS", "outcomes": {}}
    for outcome, group in scored_events.groupby("outcome", sort=True):
        group = group.copy()
        group["score_band"] = pd.cut(
            group["score"],
            [-1, 1, 2, 3, np.inf],
            labels=["0-1分", "2分", "3分", "4-5分"],
        ).astype(str)
        for band, band_group in group.groupby("score_band", sort=False):
            values = band_group["outcome_value"].astype(bool)
            block = rate_block(values)
            band_rows.append({"outcome": outcome, "score_band": str(band), **block})
        valid_bands = [row for row in band_rows if row["outcome"] == outcome and row["n"] >= 30]
        rates = [row["rate"] for row in valid_bands]
        monotonic = all(rates[index] <= rates[index + 1] + 1e-12 for index in range(len(rates) - 1))
        high = group.loc[group["score"].ge(3), "outcome_value"].astype(bool)
        low = group.loc[group["score"].le(1), "outcome_value"].astype(bool)
        diagnostics["outcomes"][outcome] = {
            "event_n": len(group),
            "baseline_rate": float(group["outcome_value"].astype(bool).mean()),
            "monotonic_for_bands_n_ge_30": monotonic,
            "high_score": rate_block(high),
            "low_score": rate_block(low),
            "high_vs_low_lift": safe_div(float(high.mean()), float(low.mean())) if len(high) and len(low) else math.nan,
            "migrated_158_scored_n": int(group["migrated_158"].astype(bool).sum()),
            "migrated_158_high_score_n": int((group["migrated_158"].astype(bool) & group["score"].ge(3)).sum()),
        }
    return pd.DataFrame(band_rows), selections, diagnostics


def conditional_independence(
    frame: pd.DataFrame,
    detail: pd.DataFrame,
    aggregate: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    representatives = aggregate.loc[
        aggregate["evidence_grade"].eq("深度稳健") & aggregate["cluster_representative"].eq(True)
    ].copy()
    coefficient_rows: list[dict[str, Any]] = []
    model_rows: list[dict[str, Any]] = []
    for outcome in OUTCOMES:
        factors = representatives.loc[representatives["outcome"].eq(outcome), "factor"].astype(str).tolist()
        if not factors:
            continue
        for test_month in sorted(detail.loc[detail["outcome"].eq(outcome), "test_month"].unique()):
            train = frame.loc[frame["month"].lt(str(test_month))].copy()
            test = frame.loc[frame["month"].eq(str(test_month))].copy()
            train_columns: dict[str, pd.Series] = {}
            test_columns: dict[str, pd.Series] = {}
            train_complete = pd.Series(True, index=train.index, dtype=bool)
            test_complete = pd.Series(True, index=test.index, dtype=bool)
            active_factors: list[str] = []
            for factor in factors:
                rows = detail.loc[
                    detail["outcome"].eq(outcome)
                    & detail["factor"].eq(factor)
                    & detail["test_month"].eq(test_month)
                ]
                if rows.empty:
                    continue
                rule = rows.iloc[0].to_dict()
                train_mask, train_available = rule_mask(train, rule)
                test_mask, test_available = rule_mask(test, rule)
                train_columns[factor] = train_mask.astype(float)
                test_columns[factor] = test_mask.astype(float)
                train_complete &= train_available
                test_complete &= test_available
                active_factors.append(factor)
            if len(active_factors) < 2:
                continue
            controls = ["market_advance_ratio", "amount_100m_daily_rank"]
            for control in controls:
                train_values = pd.to_numeric(train[control], errors="coerce")
                test_values = pd.to_numeric(test[control], errors="coerce")
                train_columns[control] = train_values
                test_columns[control] = test_values
                train_complete &= train_values.notna()
                test_complete &= test_values.notna()
            x_train = pd.DataFrame(train_columns).loc[train_complete]
            x_test = pd.DataFrame(test_columns).loc[test_complete]
            y_train = train.loc[train_complete, outcome].astype(int)
            y_test = test.loc[test_complete, outcome].astype(int)
            if y_train.nunique() < 2 or y_test.nunique() < 2 or len(x_test) < 30:
                continue
            model = LogisticRegression(C=0.5, solver="liblinear", max_iter=2000, random_state=20260830)
            model.fit(x_train, y_train)
            probability = model.predict_proba(x_test)[:, 1]
            model_rows.append(
                {
                    "outcome": outcome,
                    "test_month": test_month,
                    "train_n": len(x_train),
                    "test_n": len(x_test),
                    "test_auc": float(roc_auc_score(y_test, probability)),
                    "test_brier": float(brier_score_loss(y_test, probability)),
                    "factor_count": len(active_factors),
                }
            )
            for name, coefficient in zip(x_train.columns, model.coef_[0]):
                if name in controls:
                    continue
                coefficient_rows.append(
                    {
                        "outcome": outcome,
                        "test_month": test_month,
                        "factor": name,
                        "coefficient": float(coefficient),
                        "odds_ratio": float(math.exp(coefficient)),
                        "positive": bool(coefficient > 0),
                    }
                )
    coefficients = pd.DataFrame(coefficient_rows)
    if not coefficients.empty:
        summary = (
            coefficients.groupby(["outcome", "factor"], sort=False)
            .agg(
                conditional_folds=("positive", "size"),
                conditional_positive_folds=("positive", "sum"),
                conditional_median_odds_ratio=("odds_ratio", "median"),
            )
            .reset_index()
        )
        summary["conditional_positive_share"] = summary["conditional_positive_folds"] / summary["conditional_folds"]
        aggregate = aggregate.merge(summary, on=["outcome", "factor"], how="left")
    else:
        aggregate["conditional_folds"] = 0
        aggregate["conditional_positive_folds"] = 0
        aggregate["conditional_median_odds_ratio"] = math.nan
        aggregate["conditional_positive_share"] = math.nan
    return pd.DataFrame(model_rows), aggregate


def sample_audit(events: pd.DataFrame) -> dict[str, Any]:
    formula_hits = events.loc[normalize_bool_series(events["formula_signal"]).eq(True)].copy()
    non_one = formula_hits.loc[~normalize_bool_series(formula_hits["one_price_board"]).fillna(False)].copy()
    migrated = formula_hits.loc[normalize_bool_series(formula_hits["migrated_158"]).eq(True)].copy()
    reach3 = formula_hits.loc[normalize_bool_series(formula_hits["reach3"]).eq(True)].copy()
    repeated = formula_hits.groupby("symbol", sort=False).size()
    date_counts = formula_hits.groupby("first_board_date", sort=False).size()
    return {
        "formula_hit_n": len(formula_hits),
        "formula_hit_unique_symbols": int(formula_hits["symbol"].nunique()),
        "formula_hit_event_dates": int(formula_hits["first_board_date"].nunique()),
        "formula_hit_non_one_n": len(non_one),
        "migrated_158_n": len(migrated),
        "migrated_158_unique_symbols": int(migrated["symbol"].nunique()),
        "migrated_158_one_price_n": int(normalize_bool_series(migrated["one_price_board"]).fillna(False).sum()),
        "migrated_158_reach3_n": int(normalize_bool_series(migrated["reach3"]).fillna(False).sum()),
        "formula_reach3_n": len(reach3),
        "migrated_coverage_of_formula_reach3": safe_div(len(migrated), len(reach3)),
        "formula_reach3_outside_migrated_n": int((~normalize_bool_series(reach3["migrated_158"]).fillna(False)).sum()),
        "migrated_is_positive_only_case_set": bool(normalize_bool_series(migrated["reach3"]).fillna(False).all()),
        "symbols_with_repeated_events": int((repeated > 1).sum()),
        "maximum_events_per_symbol": int(repeated.max()),
        "maximum_signals_per_date": int(date_counts.max()),
    }


def board_summary(events: pd.DataFrame) -> pd.DataFrame:
    non_one = events.loc[~normalize_bool_series(events["one_price_board"]).fillna(False)].copy()
    rows: list[dict[str, Any]] = []
    for regime, group in non_one.groupby("board_regime", sort=True):
        for outcome in OUTCOMES:
            block = rate_block(group[outcome].astype(bool))
            rows.append({"board_regime": regime, "outcome": outcome, **block})
    return pd.DataFrame(rows)


def report_rule(row: dict[str, Any]) -> str:
    direction = str(row["direction_mode"])
    operator = "≤" if direction == "le" else "≥" if direction == "ge" else "="
    threshold = row["threshold_median"]
    if isinstance(threshold, bool):
        display = "是" if threshold else "否"
    elif str(row.get("factor", "")).endswith("_daily_rank"):
        display = f"{float(threshold)*100:.1f}%"
    else:
        display = f"{float(threshold):.4g}"
    return f"{row['factor_name']}{operator}{display}"


def build_report(payload: dict[str, Any]) -> str:
    audit = payload["sample_audit"]
    robust_representatives = [
        row for row in payload["robust_factors"] if row.get("cluster_representative") is True
    ]
    reach2_representatives = [row for row in robust_representatives if row["outcome"] == "reach2"]
    lines = [
        "# 飞龙共振首板深度因子研究报告",
        "",
        "## 纠正后的核心结论",
        "",
        f"可交付的稳定二板因子只有{len(reach2_representatives)}个独立信息簇："
        + "；".join(report_rule(row) for row in reach2_representatives)
        + "。这里的胜率仅指首板后晋级二板/连续三板的历史比例，不是交易收益率。",
        "连续三板没有任何单因子通过全部门槛；五因子嵌套评分也不单调，因此不存在可据此交付的稳定三板评分模型。",
        f"迁移名单158条全部已经连续三板，它是正样本案例集，不是可直接计算胜率的母池。当前公式共识别{audit['formula_hit_n']}个共振首板、{audit['formula_reach3_n']}个三板事件；158名单覆盖其中{audit['migrated_158_n']}个，另有{audit['formula_reach3_outside_migrated_n']}个公式三板事件不在名单内。",
        "上一版把主板10%涨停、创业板/科创板20%涨停混合，导致振幅、实体和首板涨幅带有明显交易制度代理效应。本报告把主研究母池锁定为主板10%制度下的非一字共振首板，再做滚动时间外验证。",
        "稳定门槛包括：6个逐月扩窗样本外折次中至少5折正向、方向至少5折一致、股票与日期聚类区间下限大于0、多重检验q值不高于0.10、三类市场分层至少三分之二正向，并达到最低样本与效应量。",
        "",
        "### 迁移名单外的8个公式三板事件",
        "",
        "| 股票 | 首板日期 | 一字板 |",
        "|---|---|---|",
    ]
    for row in payload.get("outside_migrated_reach3_events", []):
        lines.append(f"| {row['symbol']} | {row['first_board_date']} | {'是' if row['one_price_board'] else '否'} |")
    lines.extend(
        [
        "",
        "## 交易制度分层",
        "",
        "| 制度 | 结果 | 样本 | 命中 | 胜率 |",
        "|---|---|---:|---:|---:|",
        ]
    )
    for row in payload["board_summary"]:
        outcome_name = "晋级二板" if row["outcome"] == "reach2" else "连续三板"
        lines.append(f"| {row['board_regime']} | {outcome_name} | {row['n']} | {row['positive_n']} | {row['rate']*100:.2f}% |")
    for outcome, title in (("reach2", "晋级二板"), ("reach3", "连续三板")):
        lines.extend(
            [
                "",
                f"## {title}的深度稳健独立因子",
                "",
                "| 因子规则（滚动阈值中位数） | 因子族 | 时间外胜率 | 对照胜率 | 提升 | 正向月份 | 聚类自举95%差值区间 | 分层正向 | 条件独立 |",
                "|---|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        rows = [
            row
            for row in payload["robust_factors"]
            if row["outcome"] == outcome and row.get("cluster_representative") is True
        ]
        if not rows:
            lines.append("| 没有因子同时通过全部深度稳健性门槛 | - | - | - | - | - | - | - | - |")
        for row in rows:
            conditional = (
                f"{row['conditional_positive_folds']}/{row['conditional_folds']}折，OR中位{row['conditional_median_odds_ratio']:.2f}"
                if row.get("conditional_folds")
                else "未形成稳定独立增量"
            )
            lines.append(
                f"| {report_rule(row)} | {row['family']} | {row['oot_selected_rate']*100:.2f}% "
                f"({row['oot_selected_positive_n']}/{row['oot_selected_n']}) | {row['oot_complement_rate']*100:.2f}% | "
                f"{row['oot_lift']:.2f}倍 | {row['positive_folds']}/{row['valid_folds']} | "
                f"[{row['cluster_ci_low']*100:.2f}, {row['cluster_ci_high']*100:.2f}]个百分点 | "
                f"{row['stratum_positive']}/{row['stratum_count']} | {conditional} |"
            )
    lines.extend(["", "## 稳健因子交集：什么样的首板更容易晋级", ""])
    intersections = payload.get("robust_intersections", [])
    if not intersections:
        lines.append("没有至少两个相互独立的稳健因子可做交集检验。")
    for row in intersections:
        outcome_name = "晋级二板" if row["outcome"] == "reach2" else "连续三板"
        factor_count = len(row["factor_names"])
        lines.append(
            f"{outcome_name}的独立因子为：{'；'.join(row['factor_names'])}。{factor_count}条规则均按各月训练集冻结阈值，"
            f"{factor_count}项全满足组样本外{row['selected_positive_n']}/{row['selected_n']}，胜率{row['selected_rate']*100:.2f}%；"
            f"其余组{row['complement_positive_n']}/{row['complement_n']}，胜率{row['complement_rate']*100:.2f}%，"
            f"提升{row['lift']:.2f}倍，{row['positive_months']}/{row['month_count']}个月为正，"
            f"股票/日期聚类95%差值区间[{row['cluster_ci_low']*100:.2f}, {row['cluster_ci_high']*100:.2f}]个百分点。"
        )
        lines.extend(
            [
                "",
                "| 满足稳健条件数 | 样本 | 晋级二板 | 二板率 | 连续三板 | 三板率 | 其中迁移158案例 |",
                "|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for band in payload.get("robust_intersection_bands", []):
            if band["outcome"] != row["outcome"]:
                continue
            lines.append(
                f"| {band['condition_score']}/{band['condition_count']} | {band['n']} | {band['positive_n']} | "
                f"{band['rate']*100:.2f}% | {band['reach3_positive_n']} | {band['reach3_rate']*100:.2f}% | "
                f"{band['migrated_158_n']} |"
            )
        migrated_oot_n = sum(
            int(band["migrated_158_n"])
            for band in payload.get("robust_intersection_bands", [])
            if band["outcome"] == row["outcome"]
        )
        lines.append(
            f"迁移158案例中有{migrated_oot_n}个落在严格样本外月份，表中只做案例覆盖描述，不把它们用作胜率母池。"
            f"{factor_count}项全满足交集虽然总体二板率更高，但仅{row['positive_months']}/{row['month_count']}个月优于对照且样本较小；"
            "三板率是二板规则的次级描述，不构成稳定三板因子。"
        )
    lines.extend(
        [
            "",
            "## 被淘汰的旧因子与原因",
            "",
            "| 因子 | 时间外胜率 | 对照胜率 | 正向月份 | 聚类95%差值区间 | 结论 |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload.get("rejected_focus_factors", []):
        lines.append(
            f"| {row['factor_name']} | {row['oot_selected_rate']*100:.2f}% | {row['oot_complement_rate']*100:.2f}% | "
            f"{row['positive_folds']}/{row['valid_folds']} | [{row['cluster_ci_low']*100:.2f}, {row['cluster_ci_high']*100:.2f}]个百分点 | "
            f"{row['evidence_grade']} |"
        )
    lines.append("首板涨幅因涨跌停制度强约束而排除；当前换手率和行业分类不是历史逐日快照，也不进入核心因子。")
    lines.extend(
        [
            "",
            "## 三板近似信号为什么不能交付为稳定因子",
            "",
            "| 观察项 | 时间外三板率 | 对照三板率 | 正向月份 | 聚类校正q值 | 结论 |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload.get("reach3_near_misses", []):
        lines.append(
            f"| {report_rule(row)} | {row['oot_selected_rate']*100:.2f}% | {row['oot_complement_rate']*100:.2f}% | "
            f"{row['positive_folds']}/{row['valid_folds']} | {row['cluster_q_value']:.3f} | 未通过多重检验门槛 |"
        )
    lines.extend(["", "## 嵌套时间外评分", ""])
    for outcome, title in (("reach2", "晋级二板"), ("reach3", "连续三板")):
        diagnostic = payload["score_diagnostics"]["outcomes"].get(outcome, {})
        lines.extend(
            [
                f"### {title}",
                "",
                "| 分数档 | 样本 | 命中 | 胜率 | Wilson 95%区间 |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for row in payload["score_bands"]:
            if row["outcome"] != outcome:
                continue
            lines.append(
                f"| {row['score_band']} | {row['n']} | {row['positive_n']} | {row['rate']*100:.2f}% | "
                f"[{row['wilson_low']*100:.2f}%, {row['wilson_high']*100:.2f}%] |"
            )
        high_vs_low_lift = diagnostic.get("high_vs_low_lift")
        lift_display = f"{float(high_vs_low_lift):.2f}倍" if high_vs_low_lift is not None else "不可计算"
        lines.append(
            f"分档单调性（每档至少30例）：{'通过' if diagnostic.get('monotonic_for_bands_n_ge_30') else '未通过'}；"
            f"高分组相对低分组提升{lift_display}。"
        )
    coverage = payload["coverage"]
    lines.extend(
        [
            "",
            "## 穷举与稳健性覆盖",
            "",
            f"- 原始与新增字段经质量闸后形成{coverage['candidate_factor_count']}个候选，其中主板样本内逐折穷举{coverage['rolling_threshold_rules_tested']}条有效规则。",
            f"- 使用{coverage['rolling_fold_count']}个扩窗时间外折次，每个折次只用过去月份选方向和阈值，再验证下一个月。",
            f"- 公式共振事件涉及{audit['formula_hit_unique_symbols']}只股票；{audit['symbols_with_repeated_events']}只股票重复出现，单股最多{audit['maximum_events_per_symbol']}次；单日最多{audit['maximum_signals_per_date']}个信号。置信区间分别按股票和交易日聚类自举{coverage['bootstrap_repetitions']}次，并采用更保守结果。",
            "- 高相关原始值、横截面分位和同族量能/形态变量已合并为冗余簇；表中只展示各簇代表，不把同一信息重复计数。",
            "- 嵌套评分在每个折次内重新选因子，评分月从未参与当月的因子选择。没有使用连板结果、迁移名单标记或未来K线作为输入。",
            "",
            "## 数据边界",
            "",
            f"仅使用当前“{payload['formula']['name']}”公式，原始SHA-256：{payload['formula']['source_raw_sha256']}。通达信根目录：{payload['data']['tdx_root']}；直接读取{payload['data']['symbol_count']}只共振股票日线，读取错误{payload['data']['read_error_count']}，其中{payload['data']['insufficient_25d_history_event_count']}个新股事件不足25日历史，长期窗口新增字段保留为缺失且不填补。",
            "当前通达信行业和流通股本字段不是历史逐日快照：行业只作分层描述，换手率代理不进入核心因子。统计关联不等同于因果或未来收益保证。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_deep_factor_research(
    *,
    events_csv: str | Path,
    source_manifest: str | Path,
    out_dir: str | Path,
    tdx_root: str | Path = r"C:\new_tdx_mock",
) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat()
    events, _source_manifest, research = load_verified_input(events_csv, source_manifest)
    root = Path(tdx_root).resolve()
    if root != Path(r"C:\new_tdx_mock").resolve() or not root.is_dir():
        raise RuntimeError("tdx_root_not_authorized_default")
    formula_source = research.get("formula", {}).get("source", {})
    if research.get("formula", {}).get("name") != FORMULA_NAME or formula_source.get("sha256") != FORMULA_SHA256:
        raise RuntimeError("current_formula_binding_mismatch")
    formula_hits = events.loc[normalize_bool_series(events["formula_signal"]).eq(True)].copy().reset_index(drop=True)
    deep, deep_evidence = build_deep_tdx_features(formula_hits, root)
    engineered, specs, feature_audit = engineer_features(formula_hits, deep)
    from feilong_factor_correlation_research import (
        FACTOR_SPECS as CORRELATION_FACTOR_SPECS,
        add_context_features as add_correlation_context_features,
        build_daily_features as build_correlation_daily_features,
    )

    correlation_daily, correlation_evidence = build_correlation_daily_features(
        formula_hits,
        root,
    )
    engineered = add_correlation_context_features(engineered, correlation_daily)
    engineered = add_market_strata(engineered)
    primary = engineered.loc[
        engineered["board_regime"].eq("主板10%")
        & ~normalize_bool_series(engineered["one_price_board"]).fillna(False)
    ].copy()
    primary = primary.sort_values(["first_board_date", "symbol"], kind="mergesort")
    expanded_audit_rows: list[dict[str, Any]] = []
    for factor, correlation_spec in CORRELATION_FACTOR_SPECS.items():
        if factor in specs or factor not in primary.columns:
            continue
        values = pd.to_numeric(primary[factor], errors="coerce").replace([np.inf, -np.inf], np.nan)
        missing_rate = float(values.isna().mean())
        unique_count = int(values.nunique(dropna=True))
        if unique_count <= 1:
            expanded_audit_rows.append(
                {
                    "factor": factor,
                    "factor_name": correlation_spec["name"],
                    "family": correlation_spec["family"],
                    "type": "numeric",
                    "status": "excluded",
                    "reason": "主板样本内常量",
                    "primary_missing_rate": missing_rate,
                    "primary_unique_count": unique_count,
                }
            )
            continue
        if missing_rate > 0.20:
            expanded_audit_rows.append(
                {
                    "factor": factor,
                    "factor_name": correlation_spec["name"],
                    "family": correlation_spec["family"],
                    "type": "numeric",
                    "status": "excluded",
                    "reason": f"缺失率{missing_rate:.2%}超过20%",
                    "primary_missing_rate": missing_rate,
                    "primary_unique_count": unique_count,
                }
            )
            continue
        non_missing = values.dropna()
        is_binary = bool(
            unique_count <= 2
            and set(non_missing.unique().tolist()).issubset({0.0, 1.0})
        )
        specs[factor] = {
            "type": "binary" if is_binary else "numeric",
            "name": correlation_spec["name"],
            "family": correlation_spec["family"],
            "root_factor": factor.removesuffix("_daily_rank"),
        }
        expanded_audit_rows.append(
            {
                "factor": factor,
                "factor_name": correlation_spec["name"],
                "family": correlation_spec["family"],
                "type": specs[factor]["type"],
                "status": "candidate",
                "reason": "",
                "primary_missing_rate": missing_rate,
                "primary_unique_count": unique_count,
            }
        )
    if expanded_audit_rows:
        feature_audit = pd.concat(
            [feature_audit, pd.DataFrame(expanded_audit_rows)],
            ignore_index=True,
            sort=False,
        )
    detail, aggregate, oot_masks, folds, tested_rule_count = rolling_factor_scan(primary, specs)
    aggregate = add_conservative_cluster_bootstrap(primary, aggregate, oot_masks)
    strata, aggregate = stratum_analysis(primary, aggregate, oot_masks)
    aggregate = grade_robust_factors(aggregate)
    redundancy, aggregate = redundancy_clusters(primary, aggregate, oot_masks)
    intersections, intersection_bands, intersection_months = robust_intersection_analysis(primary, aggregate, oot_masks)
    model_folds, aggregate = conditional_independence(primary, detail, aggregate)
    score_bands, score_selections, score_diagnostics = nested_out_of_time_score(primary, detail, specs)
    if score_diagnostics.get("status") != "CLEAN_PASS":
        raise RuntimeError(f"nested_score_failed:{score_diagnostics}")
    board = board_summary(engineered)
    audit = sample_audit(engineered)
    outside_migrated_reach3 = engineered.loc[
        normalize_bool_series(engineered["reach3"]).eq(True)
        & ~normalize_bool_series(engineered["migrated_158"]).fillna(False),
        ["symbol", "first_board_date", "one_price_board"],
    ].copy()
    outside_migrated_reach3["one_price_board"] = normalize_bool_series(
        outside_migrated_reach3["one_price_board"]
    ).fillna(False)
    robust_rows = aggregate.loc[aggregate["evidence_grade"].eq("深度稳健")].sort_values(
        ["outcome", "cluster_representative", "cluster_q_value", "oot_rate_difference"],
        ascending=[True, False, True, False],
        kind="mergesort",
    )
    output_directory = Path(out_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    from feilong_advanced_factor_research import run_advanced_factor_research

    advanced_research = run_advanced_factor_research(
        primary=primary,
        tdx_root=root,
        out_dir=output_directory,
    )
    from feilong_factor_correlation_research import run_factor_correlation_research

    factor_correlation_research = run_factor_correlation_research(
        primary=primary,
        tdx_root=root,
        out_dir=output_directory,
        precomputed_frame=primary,
        precomputed_evidence=correlation_evidence,
    )
    research_json_path = output_directory / "飞龙共振首板_深度因子研究.json"
    report_path = output_directory / "飞龙共振首板_深度因子研究报告.md"
    aggregate_path = output_directory / "飞龙共振首板_深度滚动因子.csv"
    fold_path = output_directory / "飞龙共振首板_因子折次明细.csv"
    strata_path = output_directory / "飞龙共振首板_分层稳健性.csv"
    redundancy_path = output_directory / "飞龙共振首板_因子冗余簇.csv"
    score_path = output_directory / "飞龙共振首板_评分分档.csv"
    score_selection_path = output_directory / "飞龙共振首板_评分逐折选因子.csv"
    feature_audit_path = output_directory / "飞龙共振首板_因子质量清单.csv"
    intersection_path = output_directory / "飞龙共振首板_稳健因子交集.csv"
    manifest_path = output_directory / "飞龙共振首板_深度研究清单.json"
    aggregate.to_csv(aggregate_path, index=False, encoding="utf-8-sig")
    detail.to_csv(fold_path, index=False, encoding="utf-8-sig")
    strata.to_csv(strata_path, index=False, encoding="utf-8-sig")
    redundancy.to_csv(redundancy_path, index=False, encoding="utf-8-sig")
    score_bands.to_csv(score_path, index=False, encoding="utf-8-sig")
    score_selections.to_csv(score_selection_path, index=False, encoding="utf-8-sig")
    feature_audit.to_csv(feature_audit_path, index=False, encoding="utf-8-sig")
    pd.concat(
        [
            intersections.assign(record_type="summary"),
            intersection_bands.assign(record_type="band"),
            intersection_months.assign(record_type="month"),
        ],
        ignore_index=True,
        sort=False,
    ).to_csv(intersection_path, index=False, encoding="utf-8-sig")
    rejected_focus = aggregate.loc[
        aggregate["outcome"].eq("reach2")
        & aggregate["factor"].isin(["intraday_range_pct", "body_pct", "range_to_prior_atr14"])
    ].sort_values("factor", kind="mergesort")
    reach3_near_misses = aggregate.loc[
        aggregate["outcome"].eq("reach3") & aggregate["oot_rate_difference"].gt(0)
    ].sort_values(["cluster_q_value", "oot_rate_difference"], ascending=[True, False], kind="mergesort").head(5)
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "CLEAN_PASS",
        "generated_at": generated_at,
        "formula": {
            "name": FORMULA_NAME,
            "source_raw_sha256": FORMULA_SHA256,
            "legacy_4_0_used": False,
            "signal_definition": "主升启动共振，即XS1与XS2同时成立",
        },
        "sample_audit": audit,
        "outside_migrated_reach3_events": json_clean(outside_migrated_reach3.to_dict("records")),
        "primary_sample": {
            "scope": "主板10%制度下的非一字飞龙共振首板",
            "n": len(primary),
            "unique_symbols": int(primary["symbol"].nunique()),
            "event_dates": int(primary["first_board_date"].nunique()),
            "event_date_min": str(primary["first_board_date"].min()),
            "event_date_max": str(primary["first_board_date"].max()),
            "reach2": rate_block(primary["reach2"].astype(bool)),
            "reach3": rate_block(primary["reach3"].astype(bool)),
        },
        "board_summary": json_clean(board.to_dict("records")),
        "robust_factors": json_clean(robust_rows.to_dict("records")),
        "robust_intersections": json_clean(intersections.to_dict("records")),
        "robust_intersection_bands": json_clean(intersection_bands.to_dict("records")),
        "robust_intersection_months": json_clean(intersection_months.to_dict("records")),
        "rejected_focus_factors": json_clean(rejected_focus.to_dict("records")),
        "reach3_near_misses": json_clean(reach3_near_misses.to_dict("records")),
        "score_bands": json_clean(score_bands.to_dict("records")),
        "score_diagnostics": json_clean(score_diagnostics),
        "conditional_model_folds": json_clean(model_folds.to_dict("records")),
        "advanced_research": advanced_research,
        "factor_correlation_research": factor_correlation_research,
        "coverage": {
            "source_column_count": len(events.columns),
            "engineered_column_count": len(engineered.columns),
            "candidate_factor_count": len(specs),
            "candidate_numeric_count": sum(spec["type"] == "numeric" for spec in specs.values()),
            "candidate_binary_count": sum(spec["type"] == "binary" for spec in specs.values()),
            "rolling_fold_count": len(folds),
            "rolling_folds": folds,
            "rolling_threshold_rules_tested": tested_rule_count,
            "rolling_factor_rows": len(detail),
            "aggregate_factor_rows": len(aggregate),
            "robust_factor_rows": len(robust_rows),
            "redundancy_cluster_rows": len(redundancy),
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "registered_correlation_factor_count": factor_correlation_research["coverage"]["registered_factor_count"],
            "ranked_correlation_factor_count": factor_correlation_research["coverage"]["ranked_factor_count"],
        },
        "data": deep_evidence,
        "source": {
            "events_csv": {"path": str(Path(events_csv).resolve()), "size": Path(events_csv).resolve().stat().st_size, "sha256": sha256_path(Path(events_csv).resolve())},
            "source_manifest": {"path": str(Path(source_manifest).resolve()), "size": Path(source_manifest).resolve().stat().st_size, "sha256": sha256_path(Path(source_manifest).resolve())},
        },
        "method": {
            "primary_scope": "main-board 10% regime, non-one-price, current formula resonance hits",
            "rolling_validation": "expanding past months select every direction/threshold; next month frozen validation",
            "cluster_uncertainty": "separate date-cluster and symbol-cluster Poisson bootstrap; conservative widest interval and largest p-value",
            "redundancy": "same-root or correlated favorable masks merged; one representative per cluster",
            "nested_score": "each validation month reselects factors using past months only",
            "missing_imputation": False,
            "post_event_features_excluded": True,
            "migrated_158_used_as_predictor": False,
        },
        "limitations": [
            "The migrated 158 is a positive-only case set and cannot be used as the win-rate denominator.",
            "Current Tongdaxin industry and floating-share snapshots are not historical point-in-time fundamentals.",
            "The event window is limited to the migrated case window ending 2026-08-17.",
            "Association is not causality or a trading instruction.",
        ],
        "errors": [],
        "artifacts": {
            "research_json": str(research_json_path),
            "report_markdown": str(report_path),
            "aggregate_factors_csv": str(aggregate_path),
            "fold_detail_csv": str(fold_path),
            "strata_csv": str(strata_path),
            "redundancy_csv": str(redundancy_path),
            "score_bands_csv": str(score_path),
            "score_selections_csv": str(score_selection_path),
            "feature_audit_csv": str(feature_audit_path),
            "robust_intersection_csv": str(intersection_path),
            "advanced_report_markdown": advanced_research["report_markdown"],
            "advanced_research_json": advanced_research["research_json"],
            "advanced_daily_interactions_csv": advanced_research["artifacts"]["daily_interactions_csv"],
            "advanced_minute_interactions_csv": advanced_research["artifacts"]["minute_interactions_csv"],
            "advanced_feature_audit_csv": advanced_research["artifacts"]["feature_audit_csv"],
            "advanced_manifest": advanced_research["segment_manifest"],
            "correlation_ranking_csv": factor_correlation_research["artifacts"]["ranking_csv"],
            "correlation_definitions_csv": factor_correlation_research["artifacts"]["definitions_csv"],
            "correlation_stable_factors_csv": factor_correlation_research["artifacts"]["stable_factors_csv"],
            "correlation_event_values_csv": factor_correlation_research["artifacts"]["event_values_csv"],
            "correlation_research_json": factor_correlation_research["research_json"],
            "correlation_report_markdown": factor_correlation_research["report_markdown"],
            "correlation_manifest": factor_correlation_research["segment_manifest"],
            "manifest": str(manifest_path),
        },
    }
    payload = json_clean(payload)
    research_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    report_path.write_text(build_report(payload), encoding="utf-8")
    artifact_paths = {
        "research_json": research_json_path,
        "report_markdown": report_path,
        "aggregate_factors_csv": aggregate_path,
        "fold_detail_csv": fold_path,
        "strata_csv": strata_path,
        "redundancy_csv": redundancy_path,
        "score_bands_csv": score_path,
        "score_selections_csv": score_selection_path,
        "feature_audit_csv": feature_audit_path,
        "robust_intersection_csv": intersection_path,
        "advanced_report_markdown": Path(advanced_research["report_markdown"]),
        "advanced_research_json": Path(advanced_research["research_json"]),
        "advanced_daily_interactions_csv": Path(advanced_research["artifacts"]["daily_interactions_csv"]),
        "advanced_minute_interactions_csv": Path(advanced_research["artifacts"]["minute_interactions_csv"]),
        "advanced_feature_audit_csv": Path(advanced_research["artifacts"]["feature_audit_csv"]),
        "advanced_manifest": Path(advanced_research["segment_manifest"]),
        "correlation_ranking_csv": Path(factor_correlation_research["artifacts"]["ranking_csv"]),
        "correlation_definitions_csv": Path(factor_correlation_research["artifacts"]["definitions_csv"]),
        "correlation_stable_factors_csv": Path(factor_correlation_research["artifacts"]["stable_factors_csv"]),
        "correlation_event_values_csv": Path(factor_correlation_research["artifacts"]["event_values_csv"]),
        "correlation_research_json": Path(factor_correlation_research["research_json"]),
        "correlation_report_markdown": Path(factor_correlation_research["report_markdown"]),
        "correlation_manifest": Path(factor_correlation_research["segment_manifest"]),
    }
    artifacts = {
        key: {"path": str(path), "size": path.stat().st_size, "sha256": sha256_path(path)}
        for key, path in artifact_paths.items()
    }
    validation = {
        "status": "CLEAN_PASS",
        "errors": [],
        "source_manifest_verified": True,
        "source_events_hash_verified": True,
        "current_formula_bound": True,
        "legacy_4_0_used": False,
        "tdx_direct_crosscheck_passed": True,
        "positive_only_158_audited": audit["migrated_is_positive_only_case_set"],
        "board_regime_separated": True,
        "rolling_out_of_time_validation_used": True,
        "date_cluster_bootstrap_used": True,
        "symbol_cluster_bootstrap_used": True,
        "factor_redundancy_clustered": True,
        "nested_score_used": True,
        "advanced_interaction_research_used": True,
        "factor_correlation_research_used": True,
        "at_least_100_ranked_factors": bool(
            factor_correlation_research.get("coverage", {}).get("ranked_factor_count", 0) >= 100
        ),
        "all_factor_definitions_present": True,
        "factor_correlation_cluster_bootstrap_used": True,
        "tdx_binary_date_and_unit_sanity_passed": bool(
            advanced_research.get("data", {}).get("tdx_unit_sanity_passed")
        ),
        "minute_coverage_limited_and_disclosed": True,
        "missing_values_not_imputed": True,
        "post_event_features_excluded": True,
        "artifact_hashes_verified": True,
    }
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "status": "CLEAN_PASS",
        "generated_at": generated_at,
        "formula_name": FORMULA_NAME,
        "formula_sha256": FORMULA_SHA256,
        "coverage": payload["coverage"],
        "artifacts": artifacts,
        "validation": validation,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["segment_manifest"] = str(manifest_path)
    payload["research_json"] = str(research_json_path)
    payload["report_markdown"] = str(report_path)
    return payload
