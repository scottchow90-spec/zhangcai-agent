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
from scipy.stats import fisher_exact

from feilong_factor_research import (
    BINARY_FACTORS,
    MANIFEST_SCHEMA,
    NUMERIC_FACTORS,
    build_market_breadth,
    index_features,
    json_clean,
    load_industry_map,
    load_market_indices,
    safe_div,
    sha256_path,
    validate_formula_source,
)
from feilong_offline_replay import (
    DAY_RECORD,
    evaluate_installed_formula,
    front_adjust_like_tq,
    read_base_finance,
    read_gbbq,
    read_tdx_day,
)


SCHEMA = "FEILONG_CONTINUATION_RESEARCH_V2"
FORMULA_NAME = "飞龙在天"
TDX_ROOT = resolve_tdx_root()
WARMUP_START = "20180101"


def symbol_for_day_path(path: Path) -> str:
    stem = path.stem.lower()
    market = stem[:2].upper()
    code = stem[2:]
    return f"{code}.{market}"


def is_a_share_day_file(path: Path) -> bool:
    stem = path.stem.lower()
    if stem.startswith("sh"):
        return stem[2:].startswith(("600", "601", "603", "605", "688"))
    if stem.startswith("sz"):
        return stem[2:].startswith(("000", "001", "002", "003", "300", "301"))
    if stem.startswith("bj"):
        return stem[2:3] in {"4", "8", "9"}
    return False


def eligible_day_files(tdx_root: Path) -> list[Path]:
    paths: list[Path] = []
    for market in ("sh", "sz", "bj"):
        paths.extend((tdx_root / "vipdoc" / market / "lday").glob(f"{market}*.day"))
    return sorted((path for path in paths if is_a_share_day_file(path)), key=lambda value: value.name)


def normal_limit_ratio(code: str) -> float:
    if code.startswith(("300", "301", "688")):
        return 1.20
    if code.startswith(("4", "8", "9")):
        return 1.30
    return 1.10


def limit_up_flags(raw_bars: pd.DataFrame, code: str) -> pd.Series:
    previous_close = raw_bars["close"].astype(float).shift(1)
    ratio = normal_limit_ratio(code)
    limit_price = np.floor(previous_close * ratio * 100.0 + 0.5) / 100.0
    close = raw_bars["close"].astype(float)
    high = raw_bars["high"].astype(float)
    return (
        previous_close.gt(0)
        & close.ge(limit_price - 0.001)
        & close.sub(high).abs().lt(0.001)
    ).fillna(False)


def first_board_flags(limit_up: pd.Series) -> pd.Series:
    previous_one = limit_up.shift(1, fill_value=False).astype(bool)
    return (limit_up & ~previous_one).astype(bool)


def rolling_feature_frame(
    bars: pd.DataFrame,
    raw_bars: pd.DataFrame,
    formula: pd.DataFrame,
    *,
    listing_date: str,
) -> pd.DataFrame:
    close = bars["close"].astype(float)
    open_ = bars["open"].astype(float)
    high = bars["high"].astype(float)
    low = bars["low"].astype(float)
    volume = bars["volume"].astype(float)
    amount = bars["amount"].astype(float)
    previous_close = close.shift(1)
    daily_range = high - low
    returns = close.pct_change()
    true_range = pd.concat(
        [high - low, (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    ma5 = close.rolling(5, min_periods=5).mean()
    ma10 = close.rolling(10, min_periods=10).mean()
    ma20 = close.rolling(20, min_periods=20).mean()
    ma60 = close.rolling(60, min_periods=60).mean()
    ma120 = close.rolling(120, min_periods=120).mean()
    high20 = high.rolling(20, min_periods=20).max()
    high60 = high.rolling(60, min_periods=60).max()
    prior5_high = high.shift(1).rolling(5, min_periods=5).max()
    prior5_low = low.shift(1).rolling(5, min_periods=5).min()
    prior10_high = high.shift(1).rolling(10, min_periods=10).max()
    prior10_low = low.shift(1).rolling(10, min_periods=10).min()
    raw_close = raw_bars.loc[bars.index, "close"].astype(float)
    raw_previous_close = raw_close.shift(1)
    listing = datetime.strptime(str(listing_date), "%Y%m%d")
    listing_age = pd.Series(
        [
            (datetime.strptime(str(date), "%Y%m%d") - listing).days
            for date in bars.index
        ],
        index=bars.index,
        dtype=float,
    )
    frame = pd.DataFrame(index=bars.index)
    frame["first_board_return_pct"] = (raw_close / raw_previous_close - 1.0) * 100.0
    frame["open_gap_pct"] = (open_ / previous_close - 1.0) * 100.0
    frame["intraday_range_pct"] = daily_range / previous_close * 100.0
    frame["body_pct"] = (close - open_) / previous_close * 100.0
    frame["upper_shadow_pct"] = (high - pd.concat([close, open_], axis=1).max(axis=1)) / previous_close * 100.0
    frame["close_location"] = np.where(daily_range.ne(0), (close - low) / daily_range, 1.0)
    frame["volume_vs_ma5"] = volume / volume.rolling(5, min_periods=5).mean()
    frame["volume_vs_ma10"] = volume / volume.rolling(10, min_periods=10).mean()
    frame["volume_vs_ma20"] = volume / volume.rolling(20, min_periods=20).mean()
    frame["amount_vs_ma20"] = amount / amount.rolling(20, min_periods=20).mean()
    frame["amount_100m"] = amount / 1e8
    for lookback in (5, 10, 20, 60):
        frame[f"prev_{lookback}d_return_pct"] = (
            close.shift(1) / close.shift(lookback + 1) - 1.0
        ) * 100.0
    for period, moving_average in ((5, ma5), (10, ma10), (20, ma20), (60, ma60), (120, ma120)):
        frame[f"close_vs_ma{period}_pct"] = (close / moving_average - 1.0) * 100.0
    frame["distance_20d_high_pct"] = (close / high20 - 1.0) * 100.0
    frame["distance_60d_high_pct"] = (close / high60 - 1.0) * 100.0
    frame["prior_range_5d_pct"] = (prior5_high - prior5_low) / previous_close * 100.0
    frame["prior_range_10d_pct"] = (prior10_high - prior10_low) / previous_close * 100.0
    frame["atr14_pct"] = true_range.rolling(14, min_periods=14).mean() / close * 100.0
    frame["prev_volatility_20d_pct"] = returns.shift(1).rolling(20, min_periods=20).std(ddof=1) * 100.0
    frame["prior_limitups_20d"] = (
        returns.shift(1).mul(100.0).ge(9.84).rolling(20, min_periods=20).sum()
    )
    frame["listing_age_days"] = listing_age
    frame["close_at_high"] = close.sub(high).abs().lt(1e-9)
    frame["one_price_board"] = (
        pd.concat([open_, high, low, close], axis=1).max(axis=1)
        - pd.concat([open_, high, low, close], axis=1).min(axis=1)
    ).abs().lt(1e-9)
    frame["above_ma20"] = close.gt(ma20)
    frame["above_ma60"] = close.gt(ma60)
    frame["ma5_gt_ma10"] = ma5.gt(ma10)
    frame["ma10_gt_ma20"] = ma10.gt(ma20)
    frame["new_high_20d"] = high.ge(high20)
    frame["new_high_60d"] = high.ge(high60)
    for column in ("longtou", "waveband_password", "rapid_rise", "private_entry", "xs1", "xs2", "signal"):
        target = f"formula_{column}"
        frame[target] = formula[column].astype(bool) if column in formula.columns else np.nan
    return frame


def max_consecutive_boards(limit_up: pd.Series, position: int) -> int:
    count = 0
    values = limit_up.to_numpy(dtype=bool)
    for index in range(position, len(values)):
        if not values[index]:
            break
        count += 1
    return count


def benjamini_hochberg(values: list[float]) -> list[float]:
    array = np.asarray(values, dtype=float)
    result = np.full(len(array), np.nan, dtype=float)
    valid = np.flatnonzero(np.isfinite(array))
    if not len(valid):
        return result.tolist()
    ordered = valid[np.argsort(array[valid], kind="mergesort")]
    running = 1.0
    total = len(ordered)
    for rank_from_end, source_index in enumerate(ordered[::-1], start=1):
        rank = total - rank_from_end + 1
        running = min(running, float(array[source_index]) * total / rank)
        result[source_index] = min(1.0, running)
    return result.tolist()


def group_rate(frame: pd.DataFrame, mask: pd.Series, outcome: str) -> tuple[int, int, float]:
    values = frame.loc[mask, outcome].astype(bool)
    return len(values), int(values.sum()), float(values.mean()) if len(values) else math.nan


def direction_stability(
    frame: pd.DataFrame,
    outcome: str,
    favorable: pd.Series,
    unfavorable: pd.Series,
) -> dict[str, Any]:
    ordered = frame.sort_values("first_board_date", kind="mergesort")
    split = len(ordered) // 2
    date_to_favorable = dict(zip(frame.index, favorable.astype(bool)))
    date_to_unfavorable = dict(zip(frame.index, unfavorable.astype(bool)))

    def effect(group: pd.DataFrame) -> float:
        fav = pd.Series([date_to_favorable[index] for index in group.index], index=group.index)
        unfav = pd.Series([date_to_unfavorable[index] for index in group.index], index=group.index)
        fav_rate = group.loc[fav, outcome].astype(float).mean()
        unfav_rate = group.loc[unfav, outcome].astype(float).mean()
        return float(fav_rate - unfav_rate) if pd.notna(fav_rate) and pd.notna(unfav_rate) else math.nan

    early_effect = effect(ordered.iloc[:split])
    late_effect = effect(ordered.iloc[split:])
    monthly: list[int] = []
    for _month, group in ordered.groupby(ordered["first_board_date"].str.slice(0, 6), sort=True):
        value = effect(group)
        if math.isfinite(value) and abs(value) > 1e-12:
            monthly.append(1 if value > 0 else -1)
    agreement = max(monthly.count(1), monthly.count(-1)) / len(monthly) if monthly else 0.0
    return {
        "early_rate_difference": early_effect,
        "late_rate_difference": late_effect,
        "stable_direction": bool(
            math.isfinite(early_effect)
            and math.isfinite(late_effect)
            and early_effect > 0
            and late_effect > 0
        ),
        "monthly_direction_observations": len(monthly),
        "monthly_direction_agreement": agreement,
    }


def threshold_row(
    frame: pd.DataFrame,
    *,
    factor: str,
    factor_cn: str,
    outcome: str,
    scope: str,
    factor_type: str,
) -> dict[str, Any] | None:
    subset = frame[["first_board_date", factor, outcome]].dropna().copy()
    if len(subset) < 40 or subset[outcome].astype(bool).sum() < 8:
        return None
    if factor_type == "numeric":
        values = subset[factor].astype(float)
        lower = float(values.quantile(0.25))
        upper = float(values.quantile(0.75))
        if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
            return None
        bottom = values.le(lower)
        top = values.ge(upper)
        bottom_n, bottom_positive, bottom_rate = group_rate(subset, bottom, outcome)
        top_n, top_positive, top_rate = group_rate(subset, top, outcome)
        if min(bottom_n, top_n) < 10:
            return None
        if top_rate >= bottom_rate:
            favorable, unfavorable = top, bottom
            favorable_direction = "higher"
            favorable_threshold = upper
            unfavorable_threshold = lower
            fav_n, fav_positive, fav_rate = top_n, top_positive, top_rate
            unfav_n, unfav_positive, unfav_rate = bottom_n, bottom_positive, bottom_rate
        else:
            favorable, unfavorable = bottom, top
            favorable_direction = "lower"
            favorable_threshold = lower
            unfavorable_threshold = upper
            fav_n, fav_positive, fav_rate = bottom_n, bottom_positive, bottom_rate
            unfav_n, unfav_positive, unfav_rate = top_n, top_positive, top_rate
    else:
        values = subset[factor].astype(bool)
        true_mask = values
        false_mask = ~values
        true_n, true_positive, true_rate = group_rate(subset, true_mask, outcome)
        false_n, false_positive, false_rate = group_rate(subset, false_mask, outcome)
        if min(true_n, false_n) < 10:
            return None
        if true_rate >= false_rate:
            favorable, unfavorable = true_mask, false_mask
            favorable_direction = "true"
            favorable_threshold = 1.0
            unfavorable_threshold = 0.0
            fav_n, fav_positive, fav_rate = true_n, true_positive, true_rate
            unfav_n, unfav_positive, unfav_rate = false_n, false_positive, false_rate
        else:
            favorable, unfavorable = false_mask, true_mask
            favorable_direction = "false"
            favorable_threshold = 0.0
            unfavorable_threshold = 1.0
            fav_n, fav_positive, fav_rate = false_n, false_positive, false_rate
            unfav_n, unfav_positive, unfav_rate = true_n, true_positive, true_rate
    table = [
        [fav_positive, fav_n - fav_positive],
        [unfav_positive, unfav_n - unfav_positive],
    ]
    odds_ratio, p_value = fisher_exact(table, alternative="two-sided")
    stability = direction_stability(subset, outcome, favorable, unfavorable)
    return {
        "scope": scope,
        "outcome": outcome,
        "factor": factor,
        "factor_cn": factor_cn,
        "factor_type": factor_type,
        "n": len(subset),
        "favorable_direction": favorable_direction,
        "favorable_threshold": favorable_threshold,
        "unfavorable_threshold": unfavorable_threshold,
        "favorable_n": fav_n,
        "favorable_positive_n": fav_positive,
        "favorable_rate": fav_rate,
        "unfavorable_n": unfav_n,
        "unfavorable_positive_n": unfav_positive,
        "unfavorable_rate": unfav_rate,
        "rate_difference": fav_rate - unfav_rate,
        "lift": safe_div(fav_rate, unfav_rate),
        "odds_ratio": float(odds_ratio),
        "p_value": float(p_value),
        **stability,
    }


def threshold_statistics(events: pd.DataFrame) -> pd.DataFrame:
    formula_known = events.loc[events["formula_status"].eq("RESOLVED")].copy()
    scopes = [
        ("全市场首板", events),
        ("全市场非一字首板", events.loc[~events["one_price_board"].astype(bool)]),
        ("当前飞龙在天命中首板", events.loc[events["formula_signal"].eq(True)]),
        (
            "当前飞龙在天命中非一字首板",
            events.loc[events["formula_signal"].eq(True) & ~events["one_price_board"].astype(bool)],
        ),
        ("迁移包158个命中首板", events.loc[events["migrated_158"]]),
    ]
    rows: list[dict[str, Any]] = []
    for scope, frame in scopes:
        for outcome in ("reach2", "reach3"):
            for factor, factor_cn in NUMERIC_FACTORS.items():
                if factor in frame.columns:
                    row = threshold_row(
                        frame,
                        factor=factor,
                        factor_cn=factor_cn,
                        outcome=outcome,
                        scope=scope,
                        factor_type="numeric",
                    )
                    if row:
                        rows.append(row)
            for factor, factor_cn in BINARY_FACTORS.items():
                if factor in frame.columns and not factor.startswith("formula_"):
                    row = threshold_row(
                        frame,
                        factor=factor,
                        factor_cn=factor_cn,
                        outcome=outcome,
                        scope=scope,
                        factor_type="binary",
                    )
                    if row:
                        rows.append(row)
    for outcome in ("reach2", "reach3"):
        row = threshold_row(
            formula_known,
            factor="formula_signal",
            factor_cn="当前飞龙在天公式命中",
            outcome=outcome,
            scope="全市场首板（公式状态可判定）",
            factor_type="binary",
        )
        if row:
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    result = pd.DataFrame(rows)
    result["q_value"] = np.nan
    for (_scope, _outcome), indexes in result.groupby(["scope", "outcome"], sort=False).groups.items():
        adjusted = benjamini_hochberg(result.loc[indexes, "p_value"].astype(float).tolist())
        result.loc[indexes, "q_value"] = adjusted
    result["evidence_grade"] = "C_样本关联"
    effect_pass = (
        (result["outcome"].eq("reach2") & result["rate_difference"].ge(0.03))
        | (
            result["outcome"].eq("reach3")
            & result["rate_difference"].ge(0.01)
            & result["lift"].ge(1.25)
        )
    )
    grade_a = (
        result["q_value"].le(0.10)
        & result["stable_direction"]
        & result["monthly_direction_agreement"].ge(0.60)
        & effect_pass
    )
    grade_b = (
        ~grade_a
        & result["stable_direction"]
        & result["monthly_direction_agreement"].ge(0.60)
        & effect_pass
    )
    result.loc[grade_a, "evidence_grade"] = "A_显著且时间稳定"
    result.loc[grade_b, "evidence_grade"] = "B_时间稳定但未通过多重检验"
    return result.sort_values(
        ["scope", "outcome", "evidence_grade", "rate_difference"],
        ascending=[True, True, True, False],
        kind="mergesort",
    ).reset_index(drop=True)


def formula_promotion(events: pd.DataFrame) -> list[dict[str, Any]]:
    frame = events.loc[events["formula_status"].eq("RESOLVED")].copy()
    rows = []
    for outcome in ("reach2", "reach3"):
        hit = frame.loc[frame["formula_signal"].eq(True), outcome].astype(bool)
        miss = frame.loc[frame["formula_signal"].eq(False), outcome].astype(bool)
        table = [
            [int(hit.sum()), int((~hit).sum())],
            [int(miss.sum()), int((~miss).sum())],
        ]
        odds_ratio, p_value = fisher_exact(table, alternative="two-sided")
        hit_rate = float(hit.mean()) if len(hit) else math.nan
        miss_rate = float(miss.mean()) if len(miss) else math.nan
        rows.append(
            {
                "outcome": outcome,
                "formula_hit_n": len(hit),
                "formula_hit_positive_n": int(hit.sum()),
                "formula_hit_rate": hit_rate,
                "formula_miss_n": len(miss),
                "formula_miss_positive_n": int(miss.sum()),
                "formula_miss_rate": miss_rate,
                "rate_difference": hit_rate - miss_rate,
                "lift": safe_div(hit_rate, miss_rate),
                "odds_ratio": float(odds_ratio),
                "p_value": float(p_value),
            }
        )
    return rows


def industry_summary(events: pd.DataFrame, minimum_n: int = 20) -> list[dict[str, Any]]:
    rows = []
    for industry, group in events.groupby("tdx_industry", sort=True):
        if len(group) < minimum_n:
            continue
        rows.append(
            {
                "tdx_industry": str(industry),
                "sample_n": len(group),
                "reach2_n": int(group["reach2"].sum()),
                "reach2_rate": float(group["reach2"].mean()),
                "reach3_n": int(group["reach3"].sum()),
                "reach3_rate": float(group["reach3"].mean()),
            }
        )
    return sorted(rows, key=lambda row: (-row["reach2_rate"], -row["sample_n"], row["tdx_industry"]))


def format_value(value: Any, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "无数据"
    return f"{float(value):.{digits}f}"


def threshold_text(row: dict[str, Any]) -> str:
    if row["factor_type"] == "binary":
        return "条件成立" if row["favorable_direction"] == "true" else "条件不成立"
    operator = ">=" if row["favorable_direction"] == "higher" else "<="
    return f"{operator}{format_value(row['favorable_threshold'], 3)}"


def top_rows(
    statistics: pd.DataFrame,
    *,
    scope: str,
    outcome: str,
    limit: int = 12,
) -> list[dict[str, Any]]:
    subset = statistics.loc[
        statistics["scope"].eq(scope)
        & statistics["outcome"].eq(outcome)
        & statistics["evidence_grade"].isin(
            ["A_显著且时间稳定", "B_时间稳定但未通过多重检验"]
        )
    ].copy()
    subset["grade_rank"] = subset["evidence_grade"].map(
        {"A_显著且时间稳定": 0, "B_时间稳定但未通过多重检验": 1}
    )
    subset = subset.sort_values(
        ["grade_rank", "q_value", "rate_difference"],
        ascending=[True, True, False],
        kind="mergesort",
    )
    return subset.head(limit).drop(columns=["grade_rank"]).replace({np.nan: None}).to_dict("records")


def build_markdown(payload: dict[str, Any], statistics: pd.DataFrame) -> str:
    sample = payload["sample"]
    formula_rows = {row["outcome"]: row for row in payload["formula_promotion"]}
    reach2_formula = formula_rows["reach2"]
    reach3_formula = formula_rows["reach3"]
    migrated = sample["migrated_158"]
    lines = [
        "# 158个首板“飞龙在天”命中的连板基因纠正版研究",
        "",
        f"事件区间：{sample['event_date_min']}至{sample['event_date_max']}；本机通达信日线最新日期：{payload['data']['latest_kline_date']}。",
        "",
        "## 结论先行",
        "",
        f"同期全市场共识别{sample['all_first_boards']}个正常涨跌停制度下的首板，其中次日晋级二板{sample['reach2_count']}个（{sample['reach2_rate']*100:.2f}%），连续晋级三板{sample['reach3_count']}个（{sample['reach3_rate']*100:.2f}%）。这才是判断‘什么首板更容易连板’的正确母池。",
        f"当前“飞龙在天”在公式状态可判定的首板中命中{reach2_formula['formula_hit_n']}个：二板率{reach2_formula['formula_hit_rate']*100:.2f}%（未命中{reach2_formula['formula_miss_rate']*100:.2f}%），提升倍数{format_value(reach2_formula['lift'])}；三板率{reach3_formula['formula_hit_rate']*100:.2f}%（未命中{reach3_formula['formula_miss_rate']*100:.2f}%），提升倍数{format_value(reach3_formula['lift'])}。",
        f"迁移包158条已逐条在母池和当前公式中核验通过。按本股下一条实际交易记录计算，它们的二板率为{migrated['reach2_rate']*100:.2f}%（{migrated['reach2_count']}/158），连续三板率为{migrated['reach3_rate']*100:.2f}%（{migrated['reach3_count']}/158）；停牌间隔不被误判为断板。",
        "",
        "## 什么样的首板更容易连板",
        "",
        "以下只列首板当日及以前可见、且前后半段方向一致的因子。A级通过多重检验；B级仅为稳定倾向，不能当作已验证交易规则。阈值是同期样本分位点，不是人工拍脑袋参数。",
        "",
        "### 全市场首板到二板",
        "",
        "| 因子 | 有利阈值 | 有利组晋级率 | 对侧组晋级率 | 提升 | q值 | 证据 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    all_reach2 = top_rows(statistics, scope="全市场首板", outcome="reach2")
    for row in all_reach2:
        lines.append(
            f"| {row['factor_cn']} | {threshold_text(row)} | {row['favorable_rate']*100:.2f}% (n={row['favorable_n']}) | {row['unfavorable_rate']*100:.2f}% (n={row['unfavorable_n']}) | {format_value(row['lift'])}倍 | {format_value(row['q_value'], 3)} | {row['evidence_grade']} |"
        )
    if not all_reach2:
        lines.append("| 无通过时间稳定门槛的因子 | - | - | - | - | - | 样本不支持强结论 |")
    lines.extend(
        [
            "",
            "一字首板是最强统计因子，但流动性受限，也会机械压低实体、振幅和量比，不能把这一结果直接解释为普通首板的可执行优势。下面单独剔除一字首板。",
            "",
            "### 非一字首板到二板",
            "",
            "| 因子 | 有利阈值 | 有利组晋级率 | 对侧组晋级率 | 提升 | q值 | 证据 |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    non_one_reach2 = top_rows(statistics, scope="全市场非一字首板", outcome="reach2")
    for row in non_one_reach2:
        lines.append(
            f"| {row['factor_cn']} | {threshold_text(row)} | {row['favorable_rate']*100:.2f}% (n={row['favorable_n']}) | {row['unfavorable_rate']*100:.2f}% (n={row['unfavorable_n']}) | {format_value(row['lift'])}倍 | {format_value(row['q_value'], 3)} | {row['evidence_grade']} |"
        )
    if not non_one_reach2:
        lines.append("| 无通过时间稳定门槛的因子 | - | - | - | - | - | 样本不支持强结论 |")
    lines.extend(
        [
            "",
            "### 非一字首板到连续三板",
            "",
            "| 因子 | 有利阈值 | 有利组晋级率 | 对侧组晋级率 | 提升 | q值 | 证据 |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    non_one_reach3 = top_rows(statistics, scope="全市场非一字首板", outcome="reach3")
    for row in non_one_reach3:
        lines.append(
            f"| {row['factor_cn']} | {threshold_text(row)} | {row['favorable_rate']*100:.2f}% (n={row['favorable_n']}) | {row['unfavorable_rate']*100:.2f}% (n={row['unfavorable_n']}) | {format_value(row['lift'])}倍 | {format_value(row['q_value'], 3)} | {row['evidence_grade']} |"
        )
    if not non_one_reach3:
        lines.append("| 无通过时间稳定门槛的因子 | - | - | - | - | - | 样本不支持强结论 |")
    lines.extend(
        [
            "",
            "### 全市场首板到三板",
            "",
            "| 因子 | 有利阈值 | 有利组晋级率 | 对侧组晋级率 | 提升 | q值 | 证据 |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    all_reach3 = top_rows(statistics, scope="全市场首板", outcome="reach3")
    for row in all_reach3:
        lines.append(
            f"| {row['factor_cn']} | {threshold_text(row)} | {row['favorable_rate']*100:.2f}% (n={row['favorable_n']}) | {row['unfavorable_rate']*100:.2f}% (n={row['unfavorable_n']}) | {format_value(row['lift'])}倍 | {format_value(row['q_value'], 3)} | {row['evidence_grade']} |"
        )
    if not all_reach3:
        lines.append("| 无通过时间稳定门槛的因子 | - | - | - | - | - | 样本不支持强结论 |")
    lines.extend(
        [
            "",
            "### 飞龙命中首板内部的二板分化",
            "",
            "| 因子 | 有利阈值 | 有利组晋级率 | 对侧组晋级率 | 提升 | q值 | 证据 |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    formula_reach2 = top_rows(statistics, scope="当前飞龙在天命中首板", outcome="reach2")
    for row in formula_reach2:
        lines.append(
            f"| {row['factor_cn']} | {threshold_text(row)} | {row['favorable_rate']*100:.2f}% (n={row['favorable_n']}) | {row['unfavorable_rate']*100:.2f}% (n={row['unfavorable_n']}) | {format_value(row['lift'])}倍 | {format_value(row['q_value'], 3)} | {row['evidence_grade']} |"
        )
    if not formula_reach2:
        lines.append("| 无通过时间稳定门槛的因子 | - | - | - | - | - | 样本不支持强结论 |")
    lines.extend(
        [
            "",
            "### 飞龙命中且非一字首板内部的二板分化",
            "",
            "| 因子 | 有利阈值 | 有利组晋级率 | 对侧组晋级率 | 提升 | q值 | 证据 |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    formula_non_one_reach2 = top_rows(
        statistics,
        scope="当前飞龙在天命中非一字首板",
        outcome="reach2",
    )
    for row in formula_non_one_reach2:
        lines.append(
            f"| {row['factor_cn']} | {threshold_text(row)} | {row['favorable_rate']*100:.2f}% (n={row['favorable_n']}) | {row['unfavorable_rate']*100:.2f}% (n={row['unfavorable_n']}) | {format_value(row['lift'])}倍 | {format_value(row['q_value'], 3)} | {row['evidence_grade']} |"
        )
    if not formula_non_one_reach2:
        lines.append("| 无通过时间稳定门槛的因子 | - | - | - | - | - | 样本不支持强结论 |")
    lines.extend(
        [
            "",
            "### 飞龙命中且非一字首板内部的连续三板分化",
            "",
            "| 因子 | 有利阈值 | 有利组晋级率 | 对侧组晋级率 | 提升 | q值 | 证据 |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    formula_non_one_reach3 = top_rows(
        statistics,
        scope="当前飞龙在天命中非一字首板",
        outcome="reach3",
    )
    for row in formula_non_one_reach3:
        lines.append(
            f"| {row['factor_cn']} | {threshold_text(row)} | {row['favorable_rate']*100:.2f}% (n={row['favorable_n']}) | {row['unfavorable_rate']*100:.2f}% (n={row['unfavorable_n']}) | {format_value(row['lift'])}倍 | {format_value(row['q_value'], 3)} | {row['evidence_grade']} |"
        )
    if not formula_non_one_reach3:
        lines.append("| 无通过时间稳定门槛的因子 | - | - | - | - | - | 样本不支持强结论 |")
    lines.extend(
        [
            "",
            "## 飞龙公式本身是否提高连板率",
            "",
            "| 结果 | 飞龙命中 | 飞龙未命中 | 差值 | 提升倍数 | Fisher p值 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["formula_promotion"]:
        label = "次日二板" if row["outcome"] == "reach2" else "连续三板"
        lines.append(
            f"| {label} | {row['formula_hit_rate']*100:.2f}% ({row['formula_hit_positive_n']}/{row['formula_hit_n']}) | {row['formula_miss_rate']*100:.2f}% ({row['formula_miss_positive_n']}/{row['formula_miss_n']}) | {row['rate_difference']*100:.2f}个百分点 | {format_value(row['lift'])} | {format_value(row['p_value'], 4)} |"
        )
    lines.extend(
        [
            "",
            "## 因子覆盖范围",
            "",
            "本轮逐事件计算了：首板开盘缺口、实体、振幅、上影线、收盘位置、一字板；成交额、5/10/20日量比和20日额比；首板前5/10/20/60日涨幅、均线乖离、20/60日新高、前期区间宽度、ATR和波动率；上市天数；上证/深证/创业板指数环境；全市场上涨比例、涨停强度和成交额；通达信行业快照；以及当前飞龙公式各组件。完整结果在统计CSV，不以报告篇幅截断。",
            "",
            "## 样本、口径与真实性边界",
            "",
            f"- 全市场首板母池：{sample['all_first_boards']}条、{sample['stock_count']}只股票；事件日{sample['event_date_count']}个。首板定义为按主板10%、创业板/科创板20%、北交所30%的正常涨停价四舍五入到分，收盘等于最高价，且前一本股交易日未涨停。",
            f"- 公式判定覆盖：可判定{sample['formula_resolved_count']}条，因本机 `base.dbf` 缺少有效流通股本而无法判定{sample['formula_unresolved_count']}条；未判定记录没有被当作未命中。",
            f"- 迁移包核验：158/158均在同期首板母池内，158/158由当前公式源码复算命中；源码SHA-256为 `{payload['formula']['source']['sha256']}`，`legacy_4_0_used=false`。",
            f"- 本机数据：`{payload['data']['tdx_root']}`；合格 `.day` 文件{payload['data']['eligible_day_file_count']}个，可读{payload['data']['readable_day_file_count']}个，扫描错误{payload['data']['read_error_count']}个；最新日线{payload['data']['latest_kline_date']}。",
            "- 所有技术、量价和市场因子只使用首板当日及以前数据；二板、三板只作为未来标签。没有用未来最高板数反向构造因子。",
            "- 历史时点财务报表、公告、新闻和当日ST名称快照在本机结构化数据中不完整，故未伪造或用当前值倒灌。公式首板条件本身要求至少9.84%涨幅，5%涨停的ST事件不会进入母池。行业只按本机当前通达信分类作描述。",
            "- 关联不等于因果，也不构成交易指令。A级表示本样本中经过多重检验并具有时间方向稳定性，不保证未来继续有效。",
            "",
            "## 文件说明",
            "",
            "- `feilong_factor_events.csv`：同期全市场首板逐事件、公式命中和二/三板标签。",
            "- `feilong_factor_statistics.csv`：各因子阈值、样本数、晋级率、提升倍数、p/q值和稳定性。",
            "- `feilong_factor_research.json`：样本血缘、公式效果、行业分层和完整验证结果。",
        ]
    )
    return "\n".join(lines) + "\n"


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
    if root != TDX_ROOT.resolve() or not root.is_dir():
        raise RuntimeError(f"tdx_root_must_match_selected_installation:{TDX_ROOT}")
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
    if len(cycles) != 551 or len(matches) != 158:
        raise RuntimeError("migration_sample_count_mismatch")
    event_start = str(matches["first_board_date"].min())
    event_end = str(matches["first_board_date"].max())
    migrated_keys = set(zip(matches["code"], matches["first_board_date"].astype(str)))
    migrated_names = dict(zip(matches["code"], matches["name"].astype(str)))
    migrated_peak = {
        (str(row["code"]), str(row["first_board_date"])): int(row["peak_board_count"])
        for row in matches.to_dict("records")
    }

    base_path = root / "T0002" / "hq_cache" / "base.dbf"
    gbbq_path = root / "T0002" / "hq_cache" / "gbbq"
    reader_path = skill_root / "vendor" / "pytdx-1.72" / "pytdx" / "reader" / "gbbq_reader.py"
    finance = read_base_finance(base_path)
    actions = read_gbbq(gbbq_path, reader_path)
    action_groups = {
        symbol: group.drop(columns=["symbol"]).copy()
        for symbol, group in actions.groupby("symbol", sort=False)
    }
    industry_map, industry_evidence = load_industry_map(root)
    files = eligible_day_files(root)
    migrated_codes = set(matches["code"])
    rows: list[dict[str, Any]] = []
    read_errors: list[dict[str, str]] = []
    readable_count = 0
    latest_kline_date = ""
    for path in files:
        symbol = symbol_for_day_path(path)
        code = symbol[:6]
        try:
            raw_full = read_tdx_day(path)
            readable_count += 1
            latest_kline_date = max(latest_kline_date, str(raw_full.index[-1]))
            if str(raw_full.index[-1]) < event_start or str(raw_full.index[0]) > event_end:
                continue
            limit_up_full = limit_up_flags(raw_full, code)
            first_board_full = first_board_flags(limit_up_full)
            event_mask = (
                raw_full.index.to_series().between(event_start, event_end)
                & first_board_full
            )
            event_dates = raw_full.index[event_mask].astype(str).tolist()
            if not event_dates:
                continue
            use_full_history = code in migrated_codes
            raw = raw_full if use_full_history else raw_full.loc[raw_full.index >= WARMUP_START].copy()
            symbol_actions = action_groups.get(symbol, pd.DataFrame())
            adjusted = front_adjust_like_tq(raw, symbol_actions)
            finance_row = finance.get(code)
            listing_date = str(finance_row["SSDATE"]) if finance_row and str(finance_row["SSDATE"]).isdigit() else str(raw_full.index[0])
            active_capital = (
                float(finance_row["LTAG"])
                if finance_row and float(finance_row.get("LTAG", 0.0)) > 0
                else None
            )
            formula = evaluate_installed_formula(
                adjusted,
                active_capital_10k_shares=active_capital,
                listing_date=listing_date,
                code=code,
                name=migrated_names.get(code, ""),
            )
            features = rolling_feature_frame(
                adjusted,
                raw.loc[adjusted.index],
                formula,
                listing_date=listing_date,
            )
            for date in event_dates:
                if date not in features.index:
                    raise RuntimeError(f"event_outside_feature_frame:{symbol}:{date}")
                raw_position = int(raw_full.index.get_loc(date))
                board_count = max_consecutive_boards(limit_up_full, raw_position)
                event = {
                    "symbol": symbol,
                    "code": code,
                    "name": migrated_names.get(code, ""),
                    "first_board_date": date,
                    "tdx_industry": industry_map.get(code, "未分类"),
                    "migrated_158": (code, date) in migrated_keys,
                    "migrated_peak_board_count": migrated_peak.get((code, date), math.nan),
                    "max_consecutive_boards": board_count,
                    "reach2": board_count >= 2,
                    "reach3": board_count >= 3,
                    "reach4": board_count >= 4,
                    "data_status": "OK",
                }
                event.update(features.loc[date].to_dict())
                if "signal" in formula.columns:
                    event["formula_status"] = "RESOLVED"
                    event["formula_signal"] = bool(formula.loc[date, "signal"])
                else:
                    xs2 = bool(formula.loc[date, "xs2"])
                    private_entry = bool(formula.loc[date, "private_entry"])
                    if not xs2:
                        event["formula_status"] = "RESOLVED"
                        event["formula_signal"] = False
                    elif private_entry:
                        event["formula_status"] = "RESOLVED"
                        event["formula_signal"] = True
                    else:
                        event["formula_status"] = "UNRESOLVED_MISSING_ACTIVE_CAPITAL"
                        event["formula_signal"] = math.nan
                rows.append(event)
        except (OSError, RuntimeError, ValueError, KeyError) as exc:
            read_errors.append({"path": str(path), "symbol": symbol, "error": f"{type(exc).__name__}: {exc}"})

    events = pd.DataFrame(rows)
    if events.empty:
        raise RuntimeError("all_market_first_board_pool_empty")
    events = events.sort_values(["first_board_date", "code"], kind="mergesort").reset_index(drop=True)
    detected_keys = set(zip(events["code"], events["first_board_date"]))
    missing_migrated = sorted(migrated_keys - detected_keys)
    migrated_rows = events.loc[events["migrated_158"]].copy()
    formula_mismatches = migrated_rows.loc[
        ~migrated_rows["formula_status"].eq("RESOLVED")
        | ~migrated_rows["formula_signal"].eq(True),
        ["code", "first_board_date", "formula_status", "formula_signal"],
    ].to_dict("records")
    if missing_migrated or len(migrated_rows) != 158 or formula_mismatches:
        detail = {
            "missing_migrated": missing_migrated[:20],
            "detected_migrated_count": len(migrated_rows),
            "formula_mismatches": formula_mismatches[:20],
        }
        raise RuntimeError("migrated_158_identity_verification_failed:" + json.dumps(detail, ensure_ascii=False))

    event_dates = set(events["first_board_date"].astype(str))
    market_breadth, breadth_evidence = build_market_breadth(root, event_dates)
    indices = load_market_indices(root)
    for date in sorted(event_dates):
        mask = events["first_board_date"].eq(date)
        if date in market_breadth.index:
            for key, value in market_breadth.loc[date].to_dict().items():
                events.loc[mask, key] = value
        index_data: dict[str, Any] = {}
        for prefix, frame in indices.items():
            index_data.update(index_features(frame, date, prefix))
        for key, value in index_data.items():
            events.loc[mask, key] = value

    statistics = threshold_statistics(events)
    promotion = formula_promotion(events)
    migrated_rows = events.loc[events["migrated_158"]].copy()
    sample = {
        "event_date_min": event_start,
        "event_date_max": event_end,
        "all_first_boards": len(events),
        "stock_count": int(events["code"].nunique()),
        "event_date_count": int(events["first_board_date"].nunique()),
        "reach2_count": int(events["reach2"].sum()),
        "reach2_rate": float(events["reach2"].mean()),
        "reach3_count": int(events["reach3"].sum()),
        "reach3_rate": float(events["reach3"].mean()),
        "formula_resolved_count": int(events["formula_status"].eq("RESOLVED").sum()),
        "formula_unresolved_count": int((~events["formula_status"].eq("RESOLVED")).sum()),
        "migrated_158": {
            "count": len(migrated_rows),
            "identity_verified_count": int(migrated_rows["formula_signal"].eq(True).sum()),
            "reach2_count": int(migrated_rows["reach2"].sum()),
            "reach2_rate": float(migrated_rows["reach2"].mean()),
            "reach3_count": int(migrated_rows["reach3"].sum()),
            "reach3_rate": float(migrated_rows["reach3"].mean()),
        },
    }
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "CLEAN_PASS",
        "generated_at": generated_at,
        "formula": formula_evidence,
        "sample": sample,
        "formula_promotion": promotion,
        "top_factors": {
            "all_market_reach2": top_rows(statistics, scope="全市场首板", outcome="reach2"),
            "all_market_reach3": top_rows(statistics, scope="全市场首板", outcome="reach3"),
            "all_market_non_one_price_reach2": top_rows(statistics, scope="全市场非一字首板", outcome="reach2"),
            "all_market_non_one_price_reach3": top_rows(statistics, scope="全市场非一字首板", outcome="reach3"),
            "formula_hit_reach2": top_rows(statistics, scope="当前飞龙在天命中首板", outcome="reach2"),
            "formula_hit_reach3": top_rows(statistics, scope="当前飞龙在天命中首板", outcome="reach3"),
            "formula_hit_non_one_price_reach2": top_rows(statistics, scope="当前飞龙在天命中非一字首板", outcome="reach2"),
            "formula_hit_non_one_price_reach3": top_rows(statistics, scope="当前飞龙在天命中非一字首板", outcome="reach3"),
        },
        "industry_summary": industry_summary(events),
        "data": {
            "tdx_root": str(root),
            "latest_kline_date": latest_kline_date,
            "eligible_day_file_count": len(files),
            "readable_day_file_count": readable_count,
            "read_error_count": len(read_errors),
            "read_errors": read_errors,
            "base_dbf": {"path": str(base_path), "size": base_path.stat().st_size, "sha256": sha256_path(base_path)},
            "gbbq": {"path": str(gbbq_path), "size": gbbq_path.stat().st_size, "sha256": sha256_path(gbbq_path)},
            "breadth": breadth_evidence,
            "industry": industry_evidence,
            "migration_manifest": {"path": str(package_manifest_path), "size": package_manifest_path.stat().st_size, "sha256": sha256_path(package_manifest_path)},
            "cycles_csv": {"path": str(cycles_path), "size": cycles_path.stat().st_size, "sha256": sha256_path(cycles_path)},
            "matches_csv": {"path": str(matches_path), "size": matches_path.stat().st_size, "sha256": sha256_path(matches_path)},
        },
        "method": {
            "mother_pool": "all local A-share first-board events in the migrated 158 event window",
            "outcomes": "next stock trading day limit-up close for reach2; next two stock trading days both limit-up close for reach3",
            "limit_rules": "10% main board, 20% ChiNext/STAR, 30% Beijing, rounded half-up to RMB fen",
            "statistics": "favorable versus opposite quartile or binary group; Fisher exact p; Benjamini-Hochberg q",
            "stability": "positive favorable-group rate difference in both chronological halves and monthly direction agreement",
            "future_feature_exclusion": True,
            "missing_imputation": False,
        },
        "limitations": [
            "Historical point-in-time fundamentals, announcements, news and ST-name snapshots are not complete in the local structured source and are excluded.",
            "Current Tongdaxin industry mapping is descriptive only.",
            "Formula active-capital input follows the installed local base.dbf snapshot; unresolved events are never treated as misses.",
            "Association is not causality or a trading instruction.",
        ],
        "errors": [],
    }
    events_path = output_directory / "feilong_factor_events.csv"
    statistics_path = output_directory / "feilong_factor_statistics.csv"
    json_path = output_directory / "feilong_factor_research.json"
    report_path = output_directory / "飞龙在天158首板连板因子研究_纠正版.md"
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
            "all_market_first_board_denominator_used": True,
            "migrated_158_identity_verified": True,
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["segment_manifest"] = str(manifest_path)
    payload["research_json"] = str(json_path)
    payload["events_csv"] = str(events_path)
    payload["statistics_csv"] = str(statistics_path)
    payload["report_markdown"] = str(report_path)
    return payload
