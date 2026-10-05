from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

import numpy as np
import pandas as pd


DAILY_SOURCE = "通达信日线"
V3_WINDOWS = (5, 10, 15, 20, 30, 40, 60, 90, 120, 250)


# Each row is a distinct mathematical mechanism. Windows are parameter variants
# inside the mechanism and are never counted as additional dimensions.
V3_METRICS: tuple[dict[str, str], ...] = (
    {"key": "geometric_return_pct", "name": "几何收益", "logic": "用窗口首尾收盘价计算复合收益率", "deps": "close", "unit": "%"},
    {"key": "downside_deviation_pct", "name": "下行偏差", "logic": "计算负收益相对零目标的均方根", "deps": "close", "unit": "%"},
    {"key": "upside_deviation_pct", "name": "上行偏差", "logic": "计算正收益相对零目标的均方根", "deps": "close", "unit": "%"},
    {"key": "downside_energy_share", "name": "下行波动能量占比", "logic": "负收益平方和占全部收益平方和比例", "deps": "close", "unit": "0-1"},
    {"key": "upside_energy_share", "name": "上行波动能量占比", "logic": "正收益平方和占全部收益平方和比例", "deps": "close", "unit": "0-1"},
    {"key": "return_var05_pct", "name": "收益5%分位风险", "logic": "日收益经验分布5%分位", "deps": "close", "unit": "%"},
    {"key": "return_cvar05_pct", "name": "收益左尾条件均值", "logic": "不高于5%分位的日收益均值", "deps": "close", "unit": "%"},
    {"key": "return_var95_pct", "name": "收益95%分位机会", "logic": "日收益经验分布95%分位", "deps": "close", "unit": "%"},
    {"key": "return_cvar95_pct", "name": "收益右尾条件均值", "logic": "不低于95%分位的日收益均值", "deps": "close", "unit": "%"},
    {"key": "return_tail_ratio", "name": "收益尾部比", "logic": "95%分位绝对值与5%分位绝对值之比", "deps": "close", "unit": "倍"},
    {"key": "return_gain_share", "name": "上涨幅度贡献占比", "logic": "正收益绝对和占全部绝对收益和", "deps": "close", "unit": "0-1"},
    {"key": "return_loss_share", "name": "下跌幅度贡献占比", "logic": "负收益绝对和占全部绝对收益和", "deps": "close", "unit": "0-1"},
    {"key": "return_gain_day_magnitude_pct", "name": "上涨日平均强度", "logic": "上涨日收益均值；无上涨日按定义记0", "deps": "close", "unit": "%"},
    {"key": "return_loss_day_magnitude_pct", "name": "下跌日平均强度", "logic": "下跌日收益绝对值均值；无下跌日按定义记0", "deps": "close", "unit": "%"},
    {"key": "ulcer_index_pct", "name": "溃疡指数", "logic": "相对历史峰值回撤平方均值的平方根", "deps": "close", "unit": "%"},
    {"key": "pain_index_pct", "name": "平均回撤痛苦指数", "logic": "相对历史峰值回撤绝对值均值", "deps": "close", "unit": "%"},
    {"key": "drawdown_duration_max", "name": "最长回撤持续期", "logic": "低于此前累计峰值的最长连续交易日数", "deps": "close", "unit": "天"},
    {"key": "return_mad_pct", "name": "收益中位绝对偏差", "logic": "日收益相对中位数的中位绝对偏差", "deps": "close", "unit": "%"},
    {"key": "return_abs_autocorr1", "name": "绝对收益一阶自相关", "logic": "绝对日收益与其滞后一期的相关系数", "deps": "close", "unit": "相关系数"},
    {"key": "return_squared_autocorr1", "name": "平方收益一阶自相关", "logic": "日收益平方与其滞后一期的相关系数", "deps": "close", "unit": "相关系数"},
    {"key": "return_turning_point_ratio", "name": "收益转折点占比", "logic": "相邻收益斜率异号的内部点占比", "deps": "close", "unit": "0-1"},
    {"key": "reversal_after_up_ratio", "name": "上涨后反转率", "logic": "上涨日之后转为下跌的比例", "deps": "close", "unit": "0-1"},
    {"key": "reversal_after_down_ratio", "name": "下跌后反转率", "logic": "下跌日之后转为上涨的比例", "deps": "close", "unit": "0-1"},
    {"key": "variance_ratio5", "name": "五日方差比", "logic": "五期重叠收益方差除以五倍一期收益方差", "deps": "close", "unit": "倍"},
    {"key": "hurst_rs", "name": "重标极差Hurst指数", "logic": "以窗口收益的重标极差估计长记忆强度", "deps": "close", "unit": "指数"},
    {"key": "katz_fractal_dimension", "name": "Katz分形维数", "logic": "按收盘路径长度和最大位移计算分形维数", "deps": "close", "unit": "维数"},
    {"key": "permutation_entropy3", "name": "三阶排列熵", "logic": "三点序模式概率的归一化香农熵", "deps": "close", "unit": "0-1"},
    {"key": "return_zero_crossing_rate", "name": "收益过零率", "logic": "相邻非零收益符号切换比例", "deps": "close", "unit": "0-1"},
    {"key": "parkinson_volatility_pct", "name": "Parkinson高低价波动", "logic": "按日内高低价对数区间估计波动", "deps": "high,low", "unit": "%"},
    {"key": "garman_klass_volatility_pct", "name": "Garman-Klass波动", "logic": "联合开高低收对数变动估计波动", "deps": "open,high,low,close", "unit": "%"},
    {"key": "rogers_satchell_volatility_pct", "name": "Rogers-Satchell波动", "logic": "用开高低收方向项估计非零漂移波动", "deps": "open,high,low,close", "unit": "%"},
    {"key": "close_location_mean", "name": "收盘位置均值", "logic": "收盘在当日高低区间位置的平均值", "deps": "high,low,close", "unit": "0-1"},
    {"key": "close_location_std", "name": "收盘位置离散度", "logic": "收盘在当日高低区间位置的标准差", "deps": "high,low,close", "unit": "标准差"},
    {"key": "body_range_mean", "name": "实体占振幅均值", "logic": "K线实体绝对值占高低振幅比例的平均值", "deps": "open,high,low,close", "unit": "0-1"},
    {"key": "upper_shadow_share_mean", "name": "上影占振幅均值", "logic": "上影线占高低振幅比例的平均值", "deps": "open,high,low,close", "unit": "0-1"},
    {"key": "lower_shadow_share_mean", "name": "下影占振幅均值", "logic": "下影线占高低振幅比例的平均值", "deps": "open,high,low,close", "unit": "0-1"},
    {"key": "gap_abs_mean_pct", "name": "绝对隔夜缺口均值", "logic": "开盘相对昨收绝对缺口的平均值", "deps": "open,close", "unit": "%"},
    {"key": "gap_tail_ratio", "name": "隔夜缺口尾部比", "logic": "隔夜缺口95%与5%分位绝对值之比", "deps": "open,close", "unit": "倍"},
    {"key": "intraday_tail_ratio", "name": "日内收益尾部比", "logic": "日内收益95%与5%分位绝对值之比", "deps": "open,close", "unit": "倍"},
    {"key": "overnight_variance_share", "name": "隔夜方差贡献占比", "logic": "隔夜缺口方差占隔夜与日内方差之和", "deps": "open,close", "unit": "0-1"},
    {"key": "volume_median_mean_ratio", "name": "成交量中位均值比", "logic": "窗口成交量中位数与均值之比", "deps": "volume", "unit": "倍"},
    {"key": "volume_mad_cv", "name": "成交量稳健离散系数", "logic": "成交量中位绝对偏差除以中位数", "deps": "volume", "unit": "倍"},
    {"key": "volume_log_volatility", "name": "对数成交量波动", "logic": "log(1+成交量)的标准差", "deps": "volume", "unit": "标准差"},
    {"key": "volume_change_mean", "name": "成交量变化均值", "logic": "成交量环比变化率均值", "deps": "volume", "unit": "比例"},
    {"key": "volume_change_volatility", "name": "成交量变化波动", "logic": "成交量环比变化率标准差", "deps": "volume", "unit": "标准差"},
    {"key": "amount_change_mean", "name": "成交额变化均值", "logic": "成交额环比变化率均值", "deps": "amount", "unit": "比例"},
    {"key": "amount_change_volatility", "name": "成交额变化波动", "logic": "成交额环比变化率标准差", "deps": "amount", "unit": "标准差"},
    {"key": "vwap_proxy_slope", "name": "成交均价代理斜率", "logic": "成交额除成交量所得均价代理的对数线性斜率", "deps": "amount,volume", "unit": "斜率"},
    {"key": "vwap_proxy_volatility", "name": "成交均价代理波动", "logic": "成交额除成交量所得均价代理收益标准差", "deps": "amount,volume", "unit": "标准差"},
    {"key": "return_volume_beta", "name": "收益对成交量敏感度", "logic": "收益对标准化成交量的一元回归斜率", "deps": "close,volume", "unit": "斜率"},
    {"key": "return_amount_beta", "name": "收益对成交额敏感度", "logic": "收益对标准化成交额的一元回归斜率", "deps": "close,amount", "unit": "斜率"},
    {"key": "signed_volume_imbalance", "name": "方向成交量失衡", "logic": "上涨日量减下跌日量占总成交量比例", "deps": "close,volume", "unit": "-1至1"},
    {"key": "signed_amount_imbalance", "name": "方向成交额失衡", "logic": "上涨日额减下跌日额占总成交额比例", "deps": "close,amount", "unit": "-1至1"},
    {"key": "volume_price_divergence", "name": "量价趋势背离", "logic": "标准化收盘斜率减标准化成交量斜率", "deps": "close,volume", "unit": "差值"},
    {"key": "obv_slope", "name": "OBV趋势", "logic": "按收益方向累加成交量后的标准化线性斜率", "deps": "close,volume", "unit": "斜率"},
    {"key": "pvt_slope", "name": "PVT趋势", "logic": "累加收益率乘成交量后的标准化线性斜率", "deps": "close,volume", "unit": "斜率"},
    {"key": "accumulation_distribution_slope", "name": "累积派发线趋势", "logic": "按收盘区间位置加权成交量累加后的标准化斜率", "deps": "high,low,close,volume", "unit": "斜率"},
    {"key": "chaikin_money_flow", "name": "Chaikin资金流", "logic": "收盘区间位置乘成交量之和除以成交量和", "deps": "high,low,close,volume", "unit": "-1至1"},
    {"key": "money_flow_index", "name": "资金流量指数", "logic": "典型价格与成交量构成的正负资金流强弱指数", "deps": "high,low,close,volume", "unit": "0-100"},
    {"key": "force_index_mean", "name": "Force Index均值", "logic": "收盘变动乘成交量的标准化均值", "deps": "close,volume", "unit": "标准化"},
    {"key": "ease_of_movement_mean", "name": "Ease of Movement均值", "logic": "高低价中点变化按振幅与成交量标准化", "deps": "high,low,volume", "unit": "标准化"},
    {"key": "rsi", "name": "相对强弱指数", "logic": "上涨幅度均值占上涨与下跌幅度均值之和", "deps": "close", "unit": "0-100"},
    {"key": "stochastic_k", "name": "随机指标K值", "logic": "窗口末收盘在窗口最高最低价区间的位置", "deps": "high,low,close", "unit": "0-100"},
    {"key": "williams_r", "name": "Williams百分比R", "logic": "窗口末收盘距窗口最高价占价格区间比例", "deps": "high,low,close", "unit": "-100至0"},
)


if len(V3_METRICS) != 64:
    raise RuntimeError(f"v3_metric_contract_mismatch:{len(V3_METRICS)}")


def _safe_div(numerator: float, denominator: float) -> float:
    if not math.isfinite(numerator) or not math.isfinite(denominator):
        return math.nan
    return 0.0 if denominator == 0 else numerator / denominator


def _corr(left: np.ndarray, right: np.ndarray) -> float:
    mask = np.isfinite(left) & np.isfinite(right)
    x = left[mask]
    y = right[mask]
    if len(x) < 3 or np.unique(x).size < 2 or np.unique(y).size < 2:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def _slope(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    mask = np.isfinite(values)
    if mask.sum() < 3:
        return math.nan
    y = values[mask]
    x = np.arange(len(values), dtype=float)[mask]
    scale = float(np.std(y, ddof=0))
    if scale == 0:
        return 0.0
    return float(np.polyfit(x, (y - float(np.mean(y))) / scale, 1)[0])


def _longest_true(flags: np.ndarray) -> int:
    longest = current = 0
    for flag in np.asarray(flags, dtype=bool):
        current = current + 1 if flag else 0
        longest = max(longest, current)
    return longest


def _permutation_entropy3(values: np.ndarray) -> float:
    if len(values) < 5:
        return math.nan
    patterns: list[int] = []
    for index in range(len(values) - 2):
        triple = values[index : index + 3]
        if not np.isfinite(triple).all():
            continue
        order = tuple(np.argsort(triple, kind="stable").tolist())
        patterns.append(((order[0] * 3) + order[1]) * 3 + order[2])
    if not patterns:
        return math.nan
    counts = np.asarray(list(pd.Series(patterns).value_counts().values), dtype=float)
    probabilities = counts / counts.sum()
    return float(-(probabilities * np.log(probabilities)).sum() / math.log(6.0))


def build_v3_factor_specs() -> dict[str, dict[str, str]]:
    specs: dict[str, dict[str, str]] = {}
    for metric in V3_METRICS:
        for window in V3_WINDOWS:
            factor = f"v3_prior_{metric['key']}_{window}d"
            specs[factor] = {
                "factor": factor,
                "name": f"前{window}日{metric['name']}",
                "family": "V3独立机制扩展",
                "definition": f"首板前{window}个交易日；{metric['logic']}；确定性零分母按0定义，不做缺失填补",
                "unit": metric["unit"],
                "source": DAILY_SOURCE,
                "available_at": "首板收盘后",
                "mechanism_key": f"v3_{metric['key']}",
                "dimension_name": metric["name"],
                "core_logic": metric["logic"],
                "raw_dependencies": metric["deps"],
                "operator_class": metric["key"],
                "parameter_axis": "lookback_window",
            }
    if len(specs) != 640:
        raise RuntimeError(f"v3_factor_contract_mismatch:{len(specs)}")
    return specs


V3_FACTOR_SPECS = build_v3_factor_specs()


def calculate_v3_daily_factors(bars: pd.DataFrame, date: str) -> dict[str, float]:
    result = {factor: math.nan for factor in V3_FACTOR_SPECS}
    if date not in bars.index:
        raise RuntimeError(f"event_date_missing:{date}")
    position = int(bars.index.get_loc(date))
    if position < max(V3_WINDOWS) + 1:
        return result

    close = bars["close"].astype(float)
    open_ = bars["open"].astype(float)
    high = bars["high"].astype(float)
    low = bars["low"].astype(float)
    volume = bars["volume"].astype(float)
    amount = bars["amount"].astype(float)
    previous_close = close.shift(1)

    for window in V3_WINDOWS:
        start = position - window
        section = slice(start, position)
        c = close.iloc[section].to_numpy(dtype=float)
        o = open_.iloc[section].to_numpy(dtype=float)
        h = high.iloc[section].to_numpy(dtype=float)
        l = low.iloc[section].to_numpy(dtype=float)
        v = volume.iloc[section].to_numpy(dtype=float)
        a = amount.iloc[section].to_numpy(dtype=float)
        pc = previous_close.iloc[section].to_numpy(dtype=float)
        r = c / pc - 1.0
        gap = o / pc - 1.0
        intra = c / o - 1.0
        price_path = close.iloc[start - 1 : position].to_numpy(dtype=float)
        prefix = f"v3_prior_"
        suffix = f"_{window}d"

        q05, q95 = np.quantile(r, [0.05, 0.95])
        positive = r[r > 0]
        negative = r[r < 0]
        squared = r * r
        drawdown = price_path / np.maximum.accumulate(price_path) - 1.0
        median_return = float(np.median(r))
        r_diff = np.diff(r)
        gap_q05, gap_q95 = np.quantile(gap, [0.05, 0.95])
        intra_q05, intra_q95 = np.quantile(intra, [0.05, 0.95])
        log_hl = np.log(h / l)
        log_co = np.log(c / o)
        log_ho = np.log(h / o)
        log_lo = np.log(l / o)
        log_hc = np.log(h / c)
        log_lc = np.log(l / c)
        day_range = h - l
        nonzero_range = np.where(day_range == 0, np.nan, day_range)
        close_location = np.nan_to_num((c - l) / nonzero_range, nan=0.5)
        body_share = np.nan_to_num(np.abs(c - o) / nonzero_range, nan=0.0)
        upper_share = np.nan_to_num((h - np.maximum(o, c)) / nonzero_range, nan=0.0)
        lower_share = np.nan_to_num((np.minimum(o, c) - l) / nonzero_range, nan=0.0)
        volume_change = np.nan_to_num(v[1:] / v[:-1] - 1.0, nan=0.0, posinf=0.0, neginf=0.0)
        amount_change = np.nan_to_num(a[1:] / a[:-1] - 1.0, nan=0.0, posinf=0.0, neginf=0.0)
        vwap = np.divide(a, v, out=np.zeros_like(a), where=v != 0)
        vwap_returns = np.nan_to_num(vwap[1:] / vwap[:-1] - 1.0, nan=0.0, posinf=0.0, neginf=0.0)
        volume_z = (v - float(np.mean(v))) / (float(np.std(v, ddof=0)) or 1.0)
        amount_z = (a - float(np.mean(a))) / (float(np.std(a, ddof=0)) or 1.0)
        direction = np.sign(r)
        money_flow_multiplier = np.nan_to_num(((c - l) - (h - c)) / nonzero_range, nan=0.0)
        typical = (h + l + c) / 3.0
        raw_money_flow = typical * v
        typical_direction = np.sign(np.diff(typical, prepend=typical[0]))
        positive_flow = float(raw_money_flow[typical_direction > 0].sum())
        negative_flow = float(raw_money_flow[typical_direction < 0].sum())
        rsi_up = float(positive.sum()) / window
        rsi_down = abs(float(negative.sum())) / window
        highest = float(np.max(h))
        lowest = float(np.min(l))

        one_var = float(np.var(r, ddof=1))
        five = np.convolve(r, np.ones(5), mode="valid")
        variance_ratio5 = _safe_div(float(np.var(five, ddof=1)), 5.0 * one_var) if len(five) >= 2 else 0.0
        centered = r - float(np.mean(r))
        cumulative = np.cumsum(centered)
        rs = _safe_div(float(np.max(cumulative) - np.min(cumulative)), float(np.std(r, ddof=1)))
        hurst = _safe_div(math.log(max(rs, 1e-15)), math.log(window)) if rs > 0 else 0.0
        path_steps = np.abs(np.diff(price_path))
        path_length = float(path_steps.sum())
        max_distance = float(np.max(np.abs(price_path[1:] - price_path[0]))) if len(price_path) > 1 else 0.0
        katz_denominator = math.log10(max_distance / path_length) + math.log10(window) if path_length > 0 and max_distance > 0 else 0.0
        katz = _safe_div(math.log10(window), katz_denominator) if katz_denominator != 0 else 1.0
        parkinson = math.sqrt(max(float(np.mean(log_hl * log_hl)) / (4.0 * math.log(2.0)), 0.0)) * 100.0
        gk_value = 0.5 * float(np.mean(log_hl * log_hl)) - (2.0 * math.log(2.0) - 1.0) * float(np.mean(log_co * log_co))
        rs_value = float(np.mean(log_ho * log_hc + log_lo * log_lc))
        gain_abs = float(positive.sum())
        loss_abs = abs(float(negative.sum()))
        total_abs = gain_abs + loss_abs
        total_energy = float(squared.sum())
        prior_up = r[:-1] > 0
        prior_down = r[:-1] < 0
        reversal_up = _safe_div(float(np.sum(prior_up & (r[1:] < 0))), float(np.sum(prior_up)))
        reversal_down = _safe_div(float(np.sum(prior_down & (r[1:] > 0))), float(np.sum(prior_down)))
        volume_median = float(np.median(v))
        obv = np.cumsum(direction * v)
        pvt = np.cumsum(r * v)
        adl = np.cumsum(money_flow_multiplier * v)
        force = np.diff(price_path) * v
        midpoint = (h + l) / 2.0
        box_ratio = np.divide(day_range, v, out=np.zeros_like(v), where=v != 0)
        emv = np.diff(midpoint, prepend=midpoint[0]) * box_ratio

        values = {
            "geometric_return_pct": (price_path[-1] / price_path[0] - 1.0) * 100.0,
            "downside_deviation_pct": math.sqrt(float(np.mean(np.minimum(r, 0.0) ** 2))) * 100.0,
            "upside_deviation_pct": math.sqrt(float(np.mean(np.maximum(r, 0.0) ** 2))) * 100.0,
            "downside_energy_share": _safe_div(float((negative * negative).sum()), total_energy),
            "upside_energy_share": _safe_div(float((positive * positive).sum()), total_energy),
            "return_var05_pct": float(q05 * 100.0),
            "return_cvar05_pct": float(np.mean(r[r <= q05]) * 100.0),
            "return_var95_pct": float(q95 * 100.0),
            "return_cvar95_pct": float(np.mean(r[r >= q95]) * 100.0),
            "return_tail_ratio": _safe_div(abs(float(q95)), abs(float(q05))),
            "return_gain_share": _safe_div(gain_abs, total_abs),
            "return_loss_share": _safe_div(loss_abs, total_abs),
            "return_gain_day_magnitude_pct": (float(np.mean(positive)) * 100.0) if len(positive) else 0.0,
            "return_loss_day_magnitude_pct": (abs(float(np.mean(negative))) * 100.0) if len(negative) else 0.0,
            "ulcer_index_pct": math.sqrt(float(np.mean(drawdown * drawdown))) * 100.0,
            "pain_index_pct": abs(float(np.mean(drawdown))) * 100.0,
            "drawdown_duration_max": float(_longest_true(drawdown < 0)),
            "return_mad_pct": float(np.median(np.abs(r - median_return)) * 100.0),
            "return_abs_autocorr1": _corr(np.abs(r[1:]), np.abs(r[:-1])),
            "return_squared_autocorr1": _corr(squared[1:], squared[:-1]),
            "return_turning_point_ratio": float(np.mean(r_diff[1:] * r_diff[:-1] < 0)) if len(r_diff) > 1 else 0.0,
            "reversal_after_up_ratio": reversal_up,
            "reversal_after_down_ratio": reversal_down,
            "variance_ratio5": variance_ratio5,
            "hurst_rs": hurst,
            "katz_fractal_dimension": katz,
            "permutation_entropy3": _permutation_entropy3(r),
            "return_zero_crossing_rate": float(np.mean(np.sign(r[1:]) != np.sign(r[:-1]))),
            "parkinson_volatility_pct": parkinson,
            "garman_klass_volatility_pct": math.sqrt(max(gk_value, 0.0)) * 100.0,
            "rogers_satchell_volatility_pct": math.sqrt(max(rs_value, 0.0)) * 100.0,
            "close_location_mean": float(np.mean(close_location)),
            "close_location_std": float(np.std(close_location, ddof=1)),
            "body_range_mean": float(np.mean(body_share)),
            "upper_shadow_share_mean": float(np.mean(upper_share)),
            "lower_shadow_share_mean": float(np.mean(lower_share)),
            "gap_abs_mean_pct": float(np.mean(np.abs(gap)) * 100.0),
            "gap_tail_ratio": _safe_div(abs(float(gap_q95)), abs(float(gap_q05))),
            "intraday_tail_ratio": _safe_div(abs(float(intra_q95)), abs(float(intra_q05))),
            "overnight_variance_share": _safe_div(float(np.var(gap, ddof=1)), float(np.var(gap, ddof=1) + np.var(intra, ddof=1))),
            "volume_median_mean_ratio": _safe_div(volume_median, float(np.mean(v))),
            "volume_mad_cv": _safe_div(float(np.median(np.abs(v - volume_median))), volume_median),
            "volume_log_volatility": float(np.std(np.log1p(v), ddof=1)),
            "volume_change_mean": float(np.mean(volume_change)),
            "volume_change_volatility": float(np.std(volume_change, ddof=1)),
            "amount_change_mean": float(np.mean(amount_change)),
            "amount_change_volatility": float(np.std(amount_change, ddof=1)),
            "vwap_proxy_slope": _slope(np.log1p(vwap)),
            "vwap_proxy_volatility": float(np.std(vwap_returns, ddof=1)),
            "return_volume_beta": _safe_div(float(np.cov(r, volume_z, ddof=1)[0, 1]), float(np.var(volume_z, ddof=1))),
            "return_amount_beta": _safe_div(float(np.cov(r, amount_z, ddof=1)[0, 1]), float(np.var(amount_z, ddof=1))),
            "signed_volume_imbalance": _safe_div(float(np.sum(direction * v)), float(np.sum(v))),
            "signed_amount_imbalance": _safe_div(float(np.sum(direction * a)), float(np.sum(a))),
            "volume_price_divergence": _slope(np.log(price_path[1:])) - _slope(np.log1p(v)),
            "obv_slope": _slope(obv),
            "pvt_slope": _slope(pvt),
            "accumulation_distribution_slope": _slope(adl),
            "chaikin_money_flow": _safe_div(float(np.sum(money_flow_multiplier * v)), float(np.sum(v))),
            "money_flow_index": 100.0 * _safe_div(positive_flow, positive_flow + negative_flow),
            "force_index_mean": _safe_div(float(np.mean(force)), float(np.mean(v) * np.mean(price_path))),
            "ease_of_movement_mean": _safe_div(float(np.mean(emv)), float(np.mean(np.abs(emv))) if len(emv) else 0.0),
            "rsi": 100.0 * _safe_div(rsi_up, rsi_up + rsi_down),
            "stochastic_k": 100.0 * _safe_div(float(c[-1] - lowest), highest - lowest),
            "williams_r": -100.0 * _safe_div(float(highest - c[-1]), highest - lowest),
        }
        if set(values) != {metric["key"] for metric in V3_METRICS}:
            raise RuntimeError("v3_calculation_metric_set_mismatch")
        for metric_key, value in values.items():
            result[f"{prefix}{metric_key}{suffix}"] = float(value)
    return result


def _normalized_mechanism_key(factor: str) -> str:
    value = factor.casefold()
    value = re.sub(r"_(?:5|10|15|20|30|40|60|90|120|250)d(?=_|$)", "_window", value)
    value = re.sub(r"_(?:1|2|3|5|7|10|14|15|20|30|40|60|90|120|250)d(?=_|$)", "_window", value)
    value = re.sub(r"ma(?:3|5|7|10|15|20|30|40|60|90|120|250)", "ma_window", value)
    value = re.sub(r"_(?:2|3|5|10|20|60|120)_(?:5|10|20|60|120|250)(?=_|$)", "_window_pair", value)
    value = re.sub(r"_z(?:5|10)(?=_|$)", "_zwindow", value)
    return value


def _infer_dependencies(factor: str, spec: dict[str, str]) -> str:
    key = factor.casefold()
    deps: set[str] = set()
    source = str(spec.get("source", ""))
    if "公式" in source or key.startswith("formula_"):
        deps.add("formula_subsignals")
        for token in ("longtou", "waveband", "rapid", "private", "xs1", "xs2"):
            if token in key:
                deps.add(token)
    if "gbbq" in source.casefold() or "corporate_action" in key:
        deps.add("gbbq_corporate_actions")
    if "横截面" in source or key.startswith("cross_section_rank_"):
        deps.add("same_day_resonance_pool")
    if "市场" in source or key.startswith("market_") or "index_" in key:
        deps.add("market_cross_section")
        for token in ("sh_index", "sz_index", "cyb_index"):
            if token in key:
                deps.add(token)
    if "listing_age" in key:
        deps.update(("listing_date", "event_date"))
    if "volume" in key:
        deps.add("volume")
    if "amount" in key:
        deps.add("amount")
    if "vwap" in key:
        deps.update(("amount", "volume"))
    if "gap" in key or "open" in key or "intraday" in key:
        deps.update(("open", "close"))
    if any(token in key for token in ("high", "low", "range", "atr", "shadow", "body", "doji", "breakout", "support", "resistance", "location", "stochastic", "williams")):
        deps.update(("open", "high", "low", "close"))
    if any(token in key for token in ("return", "close", "price", "trend", "drawdown", "runup", "efficiency", "limit", "ma")):
        deps.add("close")
    if not deps:
        deps.add(source or "registered_source")
    return ",".join(sorted(deps))


def annotate_factor_specs(specs: dict[str, dict[str, str]]) -> tuple[dict[str, dict[str, str]], list[dict[str, Any]]]:
    enriched: dict[str, dict[str, str]] = {}
    groups: dict[str, list[str]] = {}
    provisional: dict[str, dict[str, str]] = {}
    for factor, source_spec in specs.items():
        spec = dict(source_spec)
        mechanism = str(spec.get("mechanism_key") or _normalized_mechanism_key(factor))
        dependencies = str(spec.get("raw_dependencies") or _infer_dependencies(factor, spec))
        operator = str(spec.get("operator_class") or mechanism)
        fingerprint = hashlib.sha256(f"{dependencies}|{operator}".encode("utf-8")).hexdigest()
        spec.update({
            "mechanism_key": mechanism,
            "dimension_name": str(spec.get("dimension_name") or re.sub(r"前\d+日|\d+日|（前\d+日）", "", str(spec.get("name", factor))).strip(" _-（）")),
            "core_logic": str(spec.get("core_logic") or spec.get("definition", "")),
            "raw_dependencies": dependencies,
            "operator_class": operator,
            "parameter_axis": str(spec.get("parameter_axis") or ("lookback_window" if "_window" in mechanism else "none")),
            "dependency_fingerprint": fingerprint,
        })
        provisional[factor] = spec
        groups.setdefault(fingerprint, []).append(factor)

    ordered = sorted(groups, key=lambda fp: (provisional[groups[fp][0]]["mechanism_key"], fp))
    dimension_ids = {fingerprint: f"D{index:03d}" for index, fingerprint in enumerate(ordered, start=1)}
    catalog: list[dict[str, Any]] = []
    for fingerprint in ordered:
        factors = sorted(groups[fingerprint])
        first = provisional[factors[0]]
        dimension_id = dimension_ids[fingerprint]
        for factor in factors:
            enriched[factor] = {**provisional[factor], "dimension_id": dimension_id}
        catalog.append({
            "dimension_id": dimension_id,
            "dimension_name": first["dimension_name"],
            "mechanism_key": first["mechanism_key"],
            "core_logic": first["core_logic"],
            "raw_dependencies": first["raw_dependencies"],
            "operator_class": first["operator_class"],
            "dependency_fingerprint": fingerprint,
            "factor_count": len(factors),
            "parameter_variant_count": len(factors),
            "parameter_axes": ",".join(sorted({provisional[factor]["parameter_axis"] for factor in factors})),
            "example_factors": json.dumps(factors[:5], ensure_ascii=False),
        })
    if len(enriched) != len(specs):
        raise RuntimeError("dimension_annotation_factor_loss")
    if len({row["dependency_fingerprint"] for row in catalog}) != len(catalog):
        raise RuntimeError("dimension_dependency_fingerprint_collision")
    return enriched, catalog

