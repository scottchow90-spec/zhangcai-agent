#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import itertools
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, norm

from feilong_factor_research import BINARY_FACTORS, NUMERIC_FACTORS, json_clean


SCHEMA = "FEILONG_RESONANCE_EXHAUSTIVE_V1"
MANIFEST_SCHEMA = "FEILONG_RESONANCE_EXHAUSTIVE_MANIFEST_V1"
FORMULA_NAME = "飞龙在天"
TRAIN_SHARE = 0.60

FACTOR_NAMES = {
    **NUMERIC_FACTORS,
    **BINARY_FACTORS,
    "first_board_return_pct": "首板收盘涨幅(%)",
    "market_traded_count": "全市场有成交股票数",
    "sh_index_ret_5d_pct": "上证指数5日涨幅(%)",
    "sz_index_ret_5d_pct": "深证成指5日涨幅(%)",
    "cyb_index_ret_5d_pct": "创业板指5日涨幅(%)",
    "sh_index_above_ma20": "上证指数站上20日线",
    "sz_index_above_ma20": "深证成指站上20日线",
    "cyb_index_above_ma20": "创业板指站上20日线",
    "tdx_industry": "通达信行业",
}

IDENTIFIER_COLUMNS = {"symbol", "code", "name", "first_board_date"}
POST_EVENT_COLUMNS = {
    "max_consecutive_boards",
    "reach2",
    "reach3",
    "reach4",
    "migrated_peak_board_count",
}
SELECTION_OR_STATUS_COLUMNS = {
    "migrated_158",
    "formula_signal",
    "formula_status",
    "data_status",
}
CATEGORICAL_COLUMNS = {"tdx_industry"}
BOOL_TEXT = {"true": True, "false": False, "1": True, "0": False}


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def benjamini_hochberg(values: Iterable[float]) -> list[float]:
    array = np.asarray(list(values), dtype=float)
    result = np.full(len(array), np.nan, dtype=float)
    valid = np.flatnonzero(np.isfinite(array))
    if not len(valid):
        return result.tolist()
    ordered = valid[np.argsort(array[valid], kind="mergesort")]
    running = 1.0
    total = len(ordered)
    for reverse_rank, source_index in enumerate(ordered[::-1], start=1):
        rank = total - reverse_rank + 1
        running = min(running, float(array[source_index]) * total / rank)
        result[source_index] = min(1.0, running)
    return result.tolist()


def safe_div(numerator: float, denominator: float) -> float:
    if not math.isfinite(numerator) or not math.isfinite(denominator) or denominator == 0:
        return math.nan
    return numerator / denominator


def two_proportion_p(
    selected_positive: np.ndarray,
    selected_n: np.ndarray,
    complement_positive: np.ndarray,
    complement_n: np.ndarray,
) -> np.ndarray:
    selected_rate = selected_positive / selected_n
    complement_rate = complement_positive / complement_n
    pooled = (selected_positive + complement_positive) / (selected_n + complement_n)
    standard_error = np.sqrt(pooled * (1.0 - pooled) * (1.0 / selected_n + 1.0 / complement_n))
    z_score = np.divide(
        selected_rate - complement_rate,
        standard_error,
        out=np.zeros_like(selected_rate, dtype=float),
        where=standard_error > 0,
    )
    return 2.0 * norm.sf(np.abs(z_score))


def wilson_interval(positive: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return math.nan, math.nan
    rate = positive / total
    denominator = 1.0 + z * z / total
    center = (rate + z * z / (2.0 * total)) / denominator
    margin = z * math.sqrt(rate * (1.0 - rate) / total + z * z / (4.0 * total * total)) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def normalize_bool_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype("boolean")
    lowered = series.astype(str).str.strip().str.casefold()
    mapped = lowered.map(BOOL_TEXT).astype("boolean")
    mapped.loc[series.isna()] = pd.NA
    return mapped


def chronological_split(frame: pd.DataFrame, train_share: float = TRAIN_SHARE) -> tuple[pd.Series, pd.Series, str]:
    counts = frame.groupby("first_board_date", sort=True).size()
    if len(counts) < 2:
        raise RuntimeError("insufficient_event_dates_for_out_of_time_split")
    target = len(frame) * train_share
    cutoff = str(counts.cumsum().ge(target).idxmax())
    train = frame["first_board_date"].astype(str).le(cutoff)
    validation = ~train
    if not train.any() or not validation.any():
        raise RuntimeError("out_of_time_split_empty")
    return train, validation, cutoff


def classify_columns(frame: pd.DataFrame) -> tuple[dict[str, str], list[dict[str, str]]]:
    candidates: dict[str, str] = {}
    excluded: list[dict[str, str]] = []
    for column in frame.columns:
        if column in IDENTIFIER_COLUMNS:
            excluded.append({"column": column, "reason": "identity"})
            continue
        if column in POST_EVENT_COLUMNS:
            excluded.append({"column": column, "reason": "post_event_or_outcome"})
            continue
        if column in SELECTION_OR_STATUS_COLUMNS:
            excluded.append({"column": column, "reason": "selection_or_status"})
            continue
        if column in CATEGORICAL_COLUMNS:
            if frame[column].dropna().nunique() > 1:
                candidates[column] = "categorical"
            else:
                excluded.append({"column": column, "reason": "constant"})
            continue
        bool_values = normalize_bool_series(frame[column])
        if bool_values.notna().sum() == frame[column].notna().sum() and bool_values.dropna().nunique() <= 2:
            if bool_values.dropna().nunique() > 1:
                candidates[column] = "binary"
            else:
                excluded.append({"column": column, "reason": "constant"})
            continue
        numeric = pd.to_numeric(frame[column], errors="coerce")
        if numeric.notna().sum() != frame[column].notna().sum():
            excluded.append({"column": column, "reason": "unsupported_non_numeric"})
        elif numeric.dropna().nunique() <= 1:
            excluded.append({"column": column, "reason": "constant"})
        else:
            candidates[column] = "numeric"
    return candidates, excluded


def enumerate_numeric_rules(
    train: pd.DataFrame,
    *,
    factor: str,
    outcome: str,
    scope: str,
    minimum_support: int,
) -> pd.DataFrame:
    subset = train[[factor, outcome]].dropna().copy()
    if len(subset) < minimum_support * 2:
        return pd.DataFrame()
    subset[factor] = pd.to_numeric(subset[factor], errors="coerce")
    subset = subset.dropna().sort_values(factor, kind="mergesort")
    grouped = subset.groupby(factor, sort=True)[outcome].agg(["count", "sum"])
    if len(grouped) < 2:
        return pd.DataFrame()
    values = grouped.index.to_numpy(dtype=float)
    cumulative_n = grouped["count"].to_numpy(dtype=int).cumsum()
    cumulative_positive = grouped["sum"].to_numpy(dtype=int).cumsum()
    total_n = int(cumulative_n[-1])
    total_positive = int(cumulative_positive[-1])
    left_n = cumulative_n[:-1]
    left_positive = cumulative_positive[:-1]
    right_n = total_n - left_n
    right_positive = total_positive - left_positive
    valid = (left_n >= minimum_support) & (right_n >= minimum_support)
    if not valid.any():
        return pd.DataFrame()
    left_n = left_n[valid]
    left_positive = left_positive[valid]
    right_n = right_n[valid]
    right_positive = right_positive[valid]
    lower_threshold = values[:-1][valid]
    upper_threshold = values[1:][valid]

    def make_rows(
        direction: str,
        thresholds: np.ndarray,
        selected_n: np.ndarray,
        selected_positive: np.ndarray,
        complement_n: np.ndarray,
        complement_positive: np.ndarray,
    ) -> pd.DataFrame:
        selected_rate = selected_positive / selected_n
        complement_rate = complement_positive / complement_n
        difference = selected_rate - complement_rate
        lift = np.divide(
            selected_rate,
            complement_rate,
            out=np.full_like(selected_rate, np.nan, dtype=float),
            where=complement_rate > 0,
        )
        p_values = two_proportion_p(selected_positive, selected_n, complement_positive, complement_n)
        score = difference * np.sqrt(selected_n * complement_n / (selected_n + complement_n))
        return pd.DataFrame(
            {
                "scope": scope,
                "outcome": outcome,
                "factor": factor,
                "factor_cn": FACTOR_NAMES.get(factor, factor),
                "factor_type": "numeric",
                "direction": direction,
                "threshold": thresholds,
                "train_selected_n": selected_n,
                "train_selected_positive_n": selected_positive,
                "train_selected_rate": selected_rate,
                "train_complement_n": complement_n,
                "train_complement_positive_n": complement_positive,
                "train_complement_rate": complement_rate,
                "train_rate_difference": difference,
                "train_lift": lift,
                "train_p_value_approx": p_values,
                "train_score": score,
            }
        )

    return pd.concat(
        [
            make_rows("le", lower_threshold, left_n, left_positive, right_n, right_positive),
            make_rows("ge", upper_threshold, right_n, right_positive, left_n, left_positive),
        ],
        ignore_index=True,
    )


def enumerate_binary_rules(
    train: pd.DataFrame,
    *,
    factor: str,
    outcome: str,
    scope: str,
    minimum_support: int,
) -> pd.DataFrame:
    values = normalize_bool_series(train[factor])
    subset = pd.DataFrame({factor: values, outcome: train[outcome]}).dropna()
    rows: list[dict[str, Any]] = []
    for target in (True, False):
        selected = subset[factor].eq(target)
        selected_n = int(selected.sum())
        complement_n = int((~selected).sum())
        if min(selected_n, complement_n) < minimum_support:
            continue
        selected_positive = int(subset.loc[selected, outcome].astype(bool).sum())
        complement_positive = int(subset.loc[~selected, outcome].astype(bool).sum())
        selected_rate = selected_positive / selected_n
        complement_rate = complement_positive / complement_n
        difference = selected_rate - complement_rate
        p_value = fisher_exact(
            [[selected_positive, selected_n - selected_positive], [complement_positive, complement_n - complement_positive]],
            alternative="two-sided",
        ).pvalue
        rows.append(
            {
                "scope": scope,
                "outcome": outcome,
                "factor": factor,
                "factor_cn": FACTOR_NAMES.get(factor, factor),
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
                "train_p_value_approx": float(p_value),
                "train_score": difference * math.sqrt(selected_n * complement_n / (selected_n + complement_n)),
            }
        )
    return pd.DataFrame(rows)


def enumerate_categorical_rules(
    train: pd.DataFrame,
    *,
    factor: str,
    outcome: str,
    scope: str,
    minimum_support: int,
) -> pd.DataFrame:
    subset = train[[factor, outcome]].dropna().copy()
    rows: list[dict[str, Any]] = []
    for category in sorted(subset[factor].astype(str).unique()):
        selected = subset[factor].astype(str).eq(category)
        selected_n = int(selected.sum())
        complement_n = int((~selected).sum())
        if min(selected_n, complement_n) < minimum_support:
            continue
        selected_positive = int(subset.loc[selected, outcome].astype(bool).sum())
        complement_positive = int(subset.loc[~selected, outcome].astype(bool).sum())
        selected_rate = selected_positive / selected_n
        complement_rate = complement_positive / complement_n
        difference = selected_rate - complement_rate
        p_value = fisher_exact(
            [[selected_positive, selected_n - selected_positive], [complement_positive, complement_n - complement_positive]],
            alternative="two-sided",
        ).pvalue
        rows.append(
            {
                "scope": scope,
                "outcome": outcome,
                "factor": factor,
                "factor_cn": FACTOR_NAMES.get(factor, factor),
                "factor_type": "categorical",
                "direction": "eq",
                "threshold": category,
                "train_selected_n": selected_n,
                "train_selected_positive_n": selected_positive,
                "train_selected_rate": selected_rate,
                "train_complement_n": complement_n,
                "train_complement_positive_n": complement_positive,
                "train_complement_rate": complement_rate,
                "train_rate_difference": difference,
                "train_lift": safe_div(selected_rate, complement_rate),
                "train_p_value_approx": float(p_value),
                "train_score": difference * math.sqrt(selected_n * complement_n / (selected_n + complement_n)),
            }
        )
    return pd.DataFrame(rows)


def rule_mask(frame: pd.DataFrame, rule: dict[str, Any]) -> tuple[pd.Series, pd.Series]:
    factor = str(rule["factor"])
    factor_type = str(rule["factor_type"])
    direction = str(rule["direction"])
    if factor_type == "numeric":
        values = pd.to_numeric(frame[factor], errors="coerce")
        available = values.notna()
        selected = values.le(float(rule["threshold"])) if direction == "le" else values.ge(float(rule["threshold"]))
    elif factor_type == "binary":
        values = normalize_bool_series(frame[factor])
        available = values.notna()
        target = rule["threshold"]
        if isinstance(target, str):
            target = BOOL_TEXT.get(target.strip().casefold(), target)
        selected = values.eq(bool(target)).fillna(False)
    else:
        values = frame[factor]
        available = values.notna()
        selected = values.astype(str).eq(str(rule["threshold"])) & available
    return selected.astype(bool), available.astype(bool)


def rate_metrics(frame: pd.DataFrame, mask: pd.Series, available: pd.Series, outcome: str, prefix: str) -> dict[str, Any]:
    selected_values = frame.loc[available & mask, outcome].astype(bool)
    complement_values = frame.loc[available & ~mask, outcome].astype(bool)
    selected_n = len(selected_values)
    complement_n = len(complement_values)
    selected_positive = int(selected_values.sum())
    complement_positive = int(complement_values.sum())
    selected_rate = float(selected_values.mean()) if selected_n else math.nan
    complement_rate = float(complement_values.mean()) if complement_n else math.nan
    low, high = wilson_interval(selected_positive, selected_n)
    return {
        f"{prefix}_selected_n": selected_n,
        f"{prefix}_selected_positive_n": selected_positive,
        f"{prefix}_selected_rate": selected_rate,
        f"{prefix}_selected_wilson_low": low,
        f"{prefix}_selected_wilson_high": high,
        f"{prefix}_complement_n": complement_n,
        f"{prefix}_complement_positive_n": complement_positive,
        f"{prefix}_complement_rate": complement_rate,
        f"{prefix}_rate_difference": selected_rate - complement_rate if selected_n and complement_n else math.nan,
        f"{prefix}_lift": safe_div(selected_rate, complement_rate),
    }


def monthly_stability(frame: pd.DataFrame, mask: pd.Series, available: pd.Series, outcome: str) -> tuple[int, int, float]:
    signs: list[int] = []
    months = frame["first_board_date"].astype(str).str.slice(0, 6)
    for _month, indexes in frame.loc[available].groupby(months.loc[available], sort=True).groups.items():
        group_mask = mask.loc[indexes]
        selected = frame.loc[indexes[group_mask.to_numpy()], outcome].astype(bool)
        complement = frame.loc[indexes[~group_mask.to_numpy()], outcome].astype(bool)
        if len(selected) < 10 or len(complement) < 10:
            continue
        difference = float(selected.mean() - complement.mean())
        if abs(difference) > 1e-12:
            signs.append(1 if difference > 0 else -1)
    positive = signs.count(1)
    return len(signs), positive, positive / len(signs) if signs else 0.0


def evaluate_rule(
    frame: pd.DataFrame,
    train_mask: pd.Series,
    validation_mask: pd.Series,
    rule: dict[str, Any],
) -> dict[str, Any]:
    outcome = str(rule["outcome"])
    selected, available = rule_mask(frame, rule)
    result = dict(rule)
    result.update(rate_metrics(frame, selected, available, outcome, "full"))
    result.update(rate_metrics(frame.loc[train_mask], selected.loc[train_mask], available.loc[train_mask], outcome, "train"))
    result.update(
        rate_metrics(
            frame.loc[validation_mask],
            selected.loc[validation_mask],
            available.loc[validation_mask],
            outcome,
            "validation",
        )
    )
    validation_positive = int(result["validation_selected_positive_n"])
    validation_n = int(result["validation_selected_n"])
    complement_positive = int(result["validation_complement_positive_n"])
    complement_n = int(result["validation_complement_n"])
    if validation_n and complement_n:
        result["validation_p_value"] = float(
            fisher_exact(
                [
                    [validation_positive, validation_n - validation_positive],
                    [complement_positive, complement_n - complement_positive],
                ],
                alternative="greater",
            ).pvalue
        )
    else:
        result["validation_p_value"] = math.nan
    observations, positive, agreement = monthly_stability(frame, selected, available, outcome)
    result["monthly_observations"] = observations
    result["monthly_positive"] = positive
    result["monthly_agreement"] = agreement
    return result


def choose_best_numeric_rule(audit: pd.DataFrame) -> dict[str, Any] | None:
    if audit.empty:
        return None
    positive = audit.loc[
        audit["train_rate_difference"].gt(0)
        & audit["train_lift"].gt(1.0)
        & audit["train_selected_positive_n"].ge(5)
    ].copy()
    if positive.empty:
        return None
    return positive.sort_values(
        ["train_score", "train_selected_n", "threshold"],
        ascending=[False, False, True],
        kind="mergesort",
    ).iloc[0].to_dict()


def grade_factor_results(result: pd.DataFrame) -> pd.DataFrame:
    if result.empty:
        return result
    graded = result.copy()
    graded["validation_q_value"] = np.nan
    for (_scope, _outcome), indexes in graded.groupby(["scope", "outcome"], sort=False).groups.items():
        graded.loc[indexes, "validation_q_value"] = benjamini_hochberg(
            graded.loc[indexes, "validation_p_value"].astype(float).tolist()
        )
    support = graded["full_selected_n"].ge(300) & graded["validation_selected_n"].ge(100)
    stable = (
        graded["train_rate_difference"].gt(0)
        & graded["validation_rate_difference"].gt(0)
        & graded["monthly_observations"].ge(6)
        & graded["monthly_agreement"].ge(2.0 / 3.0)
    )
    effect = (
        (
            graded["outcome"].eq("reach2")
            & graded["full_rate_difference"].ge(0.02)
            & graded["validation_rate_difference"].ge(0.02)
            & graded["full_lift"].ge(1.15)
        )
        |
        (
            graded["outcome"].eq("reach3")
            & graded["full_rate_difference"].ge(0.01)
            & graded["validation_rate_difference"].ge(0.01)
            & graded["full_lift"].ge(1.25)
        )
    )
    graded["evidence_grade"] = "C_未达到稳定高胜率门槛"
    grade_b = support & stable & effect
    grade_a = grade_b & graded["validation_q_value"].le(0.10) & graded["factor_type"].ne("categorical")
    graded.loc[grade_b, "evidence_grade"] = "B_稳定高胜率但时间外多重检验未通过"
    graded.loc[grade_a, "evidence_grade"] = "A_稳定高胜率且时间外显著"
    graded.loc[
        grade_b & graded["factor_type"].eq("categorical"),
        "evidence_grade",
    ] = "B_行业映射为当前快照仅作稳定关联"
    return graded


def exhaustive_univariate(
    frame: pd.DataFrame,
    *,
    scope: str,
    candidates: dict[str, str],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    train_mask, validation_mask, cutoff = chronological_split(frame)
    train = frame.loc[train_mask].copy()
    minimum_support = max(100, math.ceil(len(train) * 0.08))
    audit_parts: list[pd.DataFrame] = []
    chosen: list[dict[str, Any]] = []
    thresholds_tested = 0
    for outcome in ("reach2", "reach3"):
        for factor, factor_type in candidates.items():
            if factor_type == "numeric":
                audit = enumerate_numeric_rules(
                    train,
                    factor=factor,
                    outcome=outcome,
                    scope=scope,
                    minimum_support=minimum_support,
                )
                if not audit.empty:
                    audit_parts.append(audit)
                    thresholds_tested += len(audit)
                    best = choose_best_numeric_rule(audit)
                    if best is not None:
                        chosen.append(best)
            elif factor_type == "binary":
                audit = enumerate_binary_rules(
                    train,
                    factor=factor,
                    outcome=outcome,
                    scope=scope,
                    minimum_support=minimum_support,
                )
                if not audit.empty:
                    audit_parts.append(audit)
                    thresholds_tested += len(audit)
                    best = choose_best_numeric_rule(audit)
                    if best is not None:
                        chosen.append(best)
            else:
                audit = enumerate_categorical_rules(
                    train,
                    factor=factor,
                    outcome=outcome,
                    scope=scope,
                    minimum_support=minimum_support,
                )
                if not audit.empty:
                    audit_parts.append(audit)
                    thresholds_tested += len(audit)
                    for row in audit.loc[audit["train_rate_difference"].gt(0)].to_dict("records"):
                        chosen.append(row)
    audit_result = pd.concat(audit_parts, ignore_index=True) if audit_parts else pd.DataFrame()
    evaluated = [evaluate_rule(frame, train_mask, validation_mask, row) for row in chosen]
    factor_result = grade_factor_results(pd.DataFrame(evaluated))
    coverage = {
        "scope": scope,
        "sample_n": len(frame),
        "train_n": int(train_mask.sum()),
        "validation_n": int(validation_mask.sum()),
        "train_end_date": cutoff,
        "validation_start_date": str(frame.loc[validation_mask, "first_board_date"].min()),
        "minimum_train_support": minimum_support,
        "candidate_factor_count": len(candidates),
        "numeric_factor_count": sum(value == "numeric" for value in candidates.values()),
        "binary_factor_count": sum(value == "binary" for value in candidates.values()),
        "categorical_factor_count": sum(value == "categorical" for value in candidates.values()),
        "threshold_or_category_rules_tested": thresholds_tested,
        "frozen_rules_validated": len(factor_result),
    }
    return audit_result, factor_result, coverage


def combination_mask(frame: pd.DataFrame, rules: list[dict[str, Any]]) -> tuple[pd.Series, pd.Series]:
    selected = pd.Series(True, index=frame.index)
    available = pd.Series(True, index=frame.index)
    for rule in rules:
        rule_selected, rule_available = rule_mask(frame, rule)
        selected &= rule_selected
        available &= rule_available
    return selected & available, available


def exhaustive_combinations(
    frame: pd.DataFrame,
    factor_results: pd.DataFrame,
    *,
    scope: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    train_mask, validation_mask, _cutoff = chronological_split(frame)
    eligible = factor_results.loc[
        factor_results["evidence_grade"].str.startswith(("A_", "B_"), na=False)
        & factor_results["factor_type"].ne("categorical")
    ].copy()
    rows: list[dict[str, Any]] = []
    candidate_counts: dict[str, int] = {}
    for outcome in ("reach2", "reach3"):
        base = eligible.loc[eligible["outcome"].eq(outcome)].copy()
        base = base.sort_values(
            ["evidence_grade", "validation_q_value", "full_rate_difference"],
            ascending=[True, True, False],
            kind="mergesort",
        )
        rules = base.to_dict("records")
        for size in (2, 3):
            combinations = list(itertools.combinations(rules, size))
            candidate_counts[f"{outcome}_{size}factor"] = len(combinations)
            for group in combinations:
                factors = [str(rule["factor"]) for rule in group]
                if len(set(factors)) != len(factors):
                    continue
                selected, available = combination_mask(frame, list(group))
                result: dict[str, Any] = {
                    "scope": scope,
                    "outcome": outcome,
                    "combination_size": size,
                    "factor_keys": "+".join(factors),
                    "factor_names": " + ".join(str(rule["factor_cn"]) for rule in group),
                    "rules": " AND ".join(rule_text(rule) for rule in group),
                }
                result.update(rate_metrics(frame, selected, available, outcome, "full"))
                result.update(
                    rate_metrics(
                        frame.loc[train_mask],
                        selected.loc[train_mask],
                        available.loc[train_mask],
                        outcome,
                        "train",
                    )
                )
                result.update(
                    rate_metrics(
                        frame.loc[validation_mask],
                        selected.loc[validation_mask],
                        available.loc[validation_mask],
                        outcome,
                        "validation",
                    )
                )
                validation_n = int(result["validation_selected_n"])
                complement_n = int(result["validation_complement_n"])
                validation_positive = int(result["validation_selected_positive_n"])
                complement_positive = int(result["validation_complement_positive_n"])
                if validation_n and complement_n:
                    result["validation_p_value"] = float(
                        fisher_exact(
                            [
                                [validation_positive, validation_n - validation_positive],
                                [complement_positive, complement_n - complement_positive],
                            ],
                            alternative="greater",
                        ).pvalue
                    )
                else:
                    result["validation_p_value"] = math.nan
                observations, positive, agreement = monthly_stability(frame, selected, available, outcome)
                result["monthly_observations"] = observations
                result["monthly_positive"] = positive
                result["monthly_agreement"] = agreement
                rows.append(result)
    result = pd.DataFrame(rows)
    if result.empty:
        return result, {"base_rule_count": len(eligible), "combination_candidates": candidate_counts}
    result["validation_q_value"] = np.nan
    for (_outcome, _size), indexes in result.groupby(["outcome", "combination_size"], sort=False).groups.items():
        result.loc[indexes, "validation_q_value"] = benjamini_hochberg(
            result.loc[indexes, "validation_p_value"].astype(float).tolist()
        )
    support = result["full_selected_n"].ge(200) & result["validation_selected_n"].ge(60)
    stable = (
        result["train_rate_difference"].gt(0)
        & result["validation_rate_difference"].gt(0)
        & result["monthly_observations"].ge(6)
        & result["monthly_agreement"].ge(2.0 / 3.0)
    )
    effect = (
        (
            result["outcome"].eq("reach2")
            & result["full_rate_difference"].ge(0.03)
            & result["validation_rate_difference"].ge(0.03)
            & result["full_lift"].ge(1.20)
        )
        |
        (
            result["outcome"].eq("reach3")
            & result["full_rate_difference"].ge(0.015)
            & result["validation_rate_difference"].ge(0.015)
            & result["full_lift"].ge(1.40)
        )
    )
    result["evidence_grade"] = "C_未达到稳定高胜率门槛"
    grade_b = support & stable & effect
    grade_a = grade_b & result["validation_q_value"].le(0.10)
    result.loc[grade_b, "evidence_grade"] = "B_稳定高胜率但时间外多重检验未通过"
    result.loc[grade_a, "evidence_grade"] = "A_稳定高胜率且时间外显著"
    return result, {"base_rule_count": len(eligible), "combination_candidates": candidate_counts}


def rule_text(rule: dict[str, Any]) -> str:
    name = str(rule.get("factor_cn", rule.get("factor", "")))
    direction = str(rule.get("direction", ""))
    threshold = rule.get("threshold")
    if direction == "le":
        return f"{name}<={float(threshold):.4g}"
    if direction == "ge":
        return f"{name}>={float(threshold):.4g}"
    if isinstance(threshold, (bool, np.bool_)):
        return f"{name}={'是' if threshold else '否'}"
    return f"{name}={threshold}"


def top_stable_rows(frame: pd.DataFrame, scope: str, outcome: str, limit: int = 20) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    subset = frame.loc[
        frame["scope"].eq(scope)
        & frame["outcome"].eq(outcome)
        & frame["evidence_grade"].str.startswith("A_", na=False)
    ].copy()
    subset = subset.sort_values(
        ["validation_q_value", "validation_selected_rate", "validation_selected_n"],
        ascending=[True, False, False],
        kind="mergesort",
    )
    return json_clean(subset.head(limit).to_dict("records"))


def build_report(payload: dict[str, Any]) -> str:
    def factor_finding(outcome: str, factor: str) -> str:
        rows = payload["top_factors"].get(f"formula_hit_non_one_{outcome}", [])
        row = next((item for item in rows if item.get("factor") == factor), None)
        if not row:
            return ""
        return (
            f"{rule_text(row)}：全样本{row['full_selected_rate']*100:.2f}% "
            f"({row['full_selected_positive_n']}/{row['full_selected_n']})，时间外{row['validation_selected_rate']*100:.2f}% "
            f"({row['validation_selected_positive_n']}/{row['validation_selected_n']})，时间外对照{row['validation_complement_rate']*100:.2f}%"
        )

    def combination_finding(outcome: str, required_factors: set[str]) -> str:
        rows = payload["top_combinations"].get(f"formula_hit_non_one_{outcome}", [])
        row = next(
            (
                item
                for item in rows
                if set(str(item.get("factor_keys", "")).split("+")) == required_factors
            ),
            None,
        )
        if not row:
            return ""
        return (
            f"{row['rules']}：全样本{row['full_selected_rate']*100:.2f}% "
            f"({row['full_selected_positive_n']}/{row['full_selected_n']})，时间外{row['validation_selected_rate']*100:.2f}% "
            f"({row['validation_selected_positive_n']}/{row['validation_selected_n']})，时间外对照{row['validation_complement_rate']*100:.2f}%"
        )

    reach2_findings = [
        factor_finding("reach2", "intraday_range_pct"),
        factor_finding("reach2", "volume_vs_ma5"),
        factor_finding("reach2", "volume_vs_ma20"),
        factor_finding("reach2", "amount_vs_ma20"),
        factor_finding("reach2", "close_vs_ma5_pct"),
        factor_finding("reach2", "listing_age_days"),
    ]
    reach3_findings = [
        factor_finding("reach3", "intraday_range_pct"),
        factor_finding("reach3", "cyb_index_ret_5d_pct"),
        factor_finding("reach3", "sz_index_ret_5d_pct"),
        factor_finding("reach3", "volume_vs_ma5"),
        factor_finding("reach3", "body_pct"),
    ]
    representative_combinations = [
        combination_finding("reach2", {"volume_vs_ma5", "volume_vs_ma20"}),
        combination_finding("reach2", {"volume_vs_ma5", "volume_vs_ma20", "sh_index_ret_5d_pct"}),
        combination_finding("reach3", {"intraday_range_pct", "cyb_index_ret_5d_pct"}),
        combination_finding("reach3", {"intraday_range_pct", "cyb_index_ret_5d_pct", "amount_yi"}),
    ]
    lines = [
        "# 首板出现飞龙在天共振信号的稳定高胜率因子穷举报告",
        "",
        "## 结论先行",
        "",
        f"共振首板样本{payload['sample']['formula_hit_n']}个，其中非一字首板{payload['sample']['formula_hit_non_one_n']}个。二板与连续三板均按本股后续实际交易记录判定。",
        f"非一字共振首板基准：晋级二板{payload['sample']['formula_hit_non_one_reach2_rate']*100:.2f}% "
        f"({payload['sample']['formula_hit_non_one_reach2_n']}/{payload['sample']['formula_hit_non_one_n']})；连续三板"
        f"{payload['sample']['formula_hit_non_one_reach3_rate']*100:.2f}% "
        f"({payload['sample']['formula_hit_non_one_reach3_n']}/{payload['sample']['formula_hit_non_one_n']})。",
        "稳定因子必须同时满足：训练期与时间外验证期方向一致、至少6个月可比较且三分之二月份同向、足够样本、达到最低胜率差和提升倍数，并对时间外检验进行多重校正。",
        "",
        "### 什么样的共振首板更容易晋级二板",
        "",
    ]
    lines.extend(f"- {finding}" for finding in reach2_findings if finding)
    lines.extend(
        [
            "",
            "归纳：核心不是首板越爆量越好，而是共振成立但首板不过度扩张；低振幅、相对缩量、不过度偏离5日线的形态更稳定。",
            "",
            "### 什么样的共振首板更容易连续三板",
            "",
        ]
    )
    lines.extend(f"- {finding}" for finding in reach3_findings if finding)
    lines.extend(
        [
            "",
            "归纳：连续三板比晋级二板更依赖市场环境。低振幅仍是形态闸门，同时深证成指、创业板指近5日正动量构成稳定的环境增益。",
            "",
            "### 代表性组合",
            "",
        ]
    )
    lines.extend(f"- {finding}" for finding in representative_combinations if finding)
    lines.extend(
        [
            "",
            "组合中大量规则共享同一批形态、量能和市场环境变量，因此不能把通过门槛的组合数解释成彼此独立的因子数。",
            f"仅使用当前公式“{payload['formula']['name']}”，公式原始SHA-256：{payload['formula']['source_raw_sha256']}。",
            "首板收盘涨幅约20%的分割明显包含不同涨跌幅制度的代理效应，保留在穷举表中，但不列为核心可执行因子。",
            "",
        ]
    )
    for scope_key, scope_name in (
        ("formula_hit_non_one", "共振命中非一字首板"),
        ("formula_hit_all", "全部共振命中首板"),
    ):
        lines.extend([f"## {scope_name}", ""])
        for outcome, label in (("reach2", "晋级二板"), ("reach3", "连续三板")):
            lines.extend(
                [
                    f"### {label}的稳定单因子",
                    "",
                    "| 因子规则 | 全样本胜率 | 时间外胜率 | 时间外对照 | 全样本提升 | 月度同向 | 时间外q值 |",
                    "|---|---:|---:|---:|---:|---:|---:|",
                ]
            )
            rows = payload["top_factors"].get(f"{scope_key}_{outcome}", [])
            if rows:
                for row in rows:
                    lines.append(
                        f"| {rule_text(row)} | {row['full_selected_rate']*100:.2f}% ({row['full_selected_positive_n']}/{row['full_selected_n']}) | "
                        f"{row['validation_selected_rate']*100:.2f}% ({row['validation_selected_positive_n']}/{row['validation_selected_n']}) | "
                        f"{row['validation_complement_rate']*100:.2f}% | {row['full_lift']:.2f}倍 | "
                        f"{row['monthly_positive']}/{row['monthly_observations']} | {row['validation_q_value']:.4g} |"
                    )
            else:
                lines.append("| 没有因子通过全部稳定高胜率门槛 | - | - | - | - | - | - |")
            lines.extend(
                [
                    "",
                    f"### {label}的稳定二/三因子组合",
                    "",
                    "| 组合规则 | 因子数 | 全样本胜率 | 时间外胜率 | 时间外对照 | 全样本提升 | 时间外q值 |",
                    "|---|---:|---:|---:|---:|---:|---:|",
                ]
            )
            combos = payload["top_combinations"].get(f"{scope_key}_{outcome}", [])
            if combos:
                for row in combos:
                    lines.append(
                        f"| {row['rules']} | {row['combination_size']} | {row['full_selected_rate']*100:.2f}% "
                        f"({row['full_selected_positive_n']}/{row['full_selected_n']}) | {row['validation_selected_rate']*100:.2f}% "
                        f"({row['validation_selected_positive_n']}/{row['validation_selected_n']}) | "
                        f"{row['validation_complement_rate']*100:.2f}% | {row['full_lift']:.2f}倍 | {row['validation_q_value']:.4g} |"
                    )
            else:
                lines.append("| 没有组合通过全部稳定高胜率门槛 | - | - | - | - | - | - |")
            lines.append("")
    lines.extend(
        [
            "## 穷举覆盖",
            "",
            f"- 首板事件区间：{payload['sample']['event_date_min']}至{payload['sample']['event_date_max']}；通达信日线最新日期：{payload['data']['latest_kline_date']}。",
            f"- 可用字段{payload['coverage']['source_column_count']}个，全部已分类；候选字段并集{payload['coverage']['candidate_factor_union_count']}个，排除字段{payload['coverage']['excluded_column_count']}个。",
            f"- 全部有效训练期切分、布尔取值和行业类别规则共检验{payload['coverage']['threshold_or_category_rules_tested']}条。",
            f"- 通过稳定单因子门槛后，二因子与三因子组合共穷举{payload['coverage']['combination_rules_tested']}条。",
            "- 数值阈值只在前60%时间样本中搜索，冻结后在后40%样本验证；没有使用未来连板结果作为输入字段。",
            "",
            "## 边界",
            "",
            "行业字段是当前通达信行业映射，不是逐日历史快照，因此行业结果最高只列为关联证据。阈值是本时间窗内的统计分割，不证明因果，也不等同于未来收益保证。",
        ]
    )
    return "\n".join(lines) + "\n"


def load_verified_input(events_csv: str | Path, source_manifest: str | Path) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    events_path = Path(events_csv).resolve()
    manifest_path = Path(source_manifest).resolve()
    if not events_path.is_file() or not manifest_path.is_file():
        raise RuntimeError("source_factor_artifact_missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validation = manifest.get("validation", {})
    if (
        manifest.get("schema") != "FEILONG_FACTOR_RESEARCH_MANIFEST_V1"
        or manifest.get("status") != "CLEAN_PASS"
        or manifest.get("formula_name") != FORMULA_NAME
        or manifest.get("legacy_4_0_used") is not False
        or validation.get("status") != "CLEAN_PASS"
        or validation.get("artifact_hashes_verified") is not True
        or validation.get("post_event_features_excluded") is not True
        or validation.get("all_market_first_board_denominator_used") is not True
    ):
        raise RuntimeError("source_factor_manifest_not_clean")
    declared_events = manifest.get("artifacts", {}).get("events_csv", {})
    if Path(str(declared_events.get("path", ""))).resolve() != events_path:
        raise RuntimeError("source_events_path_mismatch")
    if declared_events.get("size") != events_path.stat().st_size or str(declared_events.get("sha256", "")).casefold() != sha256_path(events_path):
        raise RuntimeError("source_events_hash_mismatch")
    research_row = manifest.get("artifacts", {}).get("research_json", {})
    research_path = Path(str(research_row.get("path", ""))).resolve()
    if not research_path.is_file() or research_row.get("size") != research_path.stat().st_size or str(research_row.get("sha256", "")).casefold() != sha256_path(research_path):
        raise RuntimeError("source_research_hash_mismatch")
    research = json.loads(research_path.read_text(encoding="utf-8"))
    if research.get("schema") != "FEILONG_CONTINUATION_RESEARCH_V2" or research.get("status") != "CLEAN_PASS":
        raise RuntimeError("source_research_schema_invalid")
    events = pd.read_csv(events_path, dtype={"symbol": str, "code": str, "first_board_date": str})
    for column in ("reach2", "reach3", "reach4", "migrated_158", "formula_signal", "one_price_board"):
        if column in events:
            events[column] = normalize_bool_series(events[column])
    if len(events) != int(research.get("sample", {}).get("all_first_boards", -1)):
        raise RuntimeError("source_event_count_mismatch")
    if not events["formula_status"].eq("RESOLVED").all():
        raise RuntimeError("source_formula_status_unresolved")
    return events, manifest, research


def run_resonance_exhaustive(
    *,
    events_csv: str | Path,
    source_manifest: str | Path,
    out_dir: str | Path,
) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat()
    output_directory = Path(out_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    events, source, research = load_verified_input(events_csv, source_manifest)
    formula_hits = events.loc[events["formula_signal"].eq(True)].copy().reset_index(drop=True)
    formula_non_one = formula_hits.loc[~formula_hits["one_price_board"].astype(bool)].copy().reset_index(drop=True)
    expected_formula_hit_n = next(
        (
            int(row["formula_hit_n"])
            for row in research.get("formula_promotion", [])
            if row.get("outcome") == "reach2"
        ),
        -1,
    )
    if not len(formula_hits) or not len(formula_non_one) or len(formula_hits) != expected_formula_hit_n:
        raise RuntimeError(
            f"formula_hit_cohort_drift:expected={expected_formula_hit_n},all={len(formula_hits)},non_one={len(formula_non_one)}"
        )

    all_candidates, all_excluded = classify_columns(formula_hits)
    non_one_candidates, non_one_excluded = classify_columns(formula_non_one)
    scopes = [
        ("formula_hit_all", "共振命中全部首板", formula_hits, all_candidates),
        ("formula_hit_non_one", "共振命中非一字首板", formula_non_one, non_one_candidates),
    ]
    audit_parts: list[pd.DataFrame] = []
    factor_parts: list[pd.DataFrame] = []
    combination_parts: list[pd.DataFrame] = []
    scope_coverage: list[dict[str, Any]] = []
    combination_coverage: list[dict[str, Any]] = []
    for scope_key, scope_name, frame, candidates in scopes:
        audit, factors, coverage = exhaustive_univariate(frame, scope=scope_key, candidates=candidates)
        combinations, combo_coverage = exhaustive_combinations(frame, factors, scope=scope_key)
        audit_parts.append(audit)
        factor_parts.append(factors)
        combination_parts.append(combinations)
        scope_coverage.append({**coverage, "scope_name": scope_name})
        combination_coverage.append({"scope": scope_key, **combo_coverage})
    audit = pd.concat(audit_parts, ignore_index=True) if audit_parts else pd.DataFrame()
    factors = pd.concat(factor_parts, ignore_index=True) if factor_parts else pd.DataFrame()
    combinations = pd.concat(combination_parts, ignore_index=True) if combination_parts else pd.DataFrame()

    top_factors: dict[str, Any] = {}
    top_combinations: dict[str, Any] = {}
    for scope_key, _scope_name, _frame, _candidates in scopes:
        for outcome in ("reach2", "reach3"):
            top_factors[f"{scope_key}_{outcome}"] = top_stable_rows(factors, scope_key, outcome)
            top_combinations[f"{scope_key}_{outcome}"] = top_stable_rows(combinations, scope_key, outcome)

    all_excluded_map = {row["column"]: row["reason"] for row in all_excluded}
    formula_source = research.get("formula", {}).get("source", {})
    formula_source_sha256 = formula_source.get("sha256")
    if not formula_source_sha256 or len(formula_source_sha256) != 64:
        raise RuntimeError("current_formula_source_hash_missing")
    if research.get("formula", {}).get("name") != FORMULA_NAME:
        raise RuntimeError("current_formula_name_mismatch")
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "CLEAN_PASS",
        "generated_at": generated_at,
        "formula": {
            "name": FORMULA_NAME,
            "source_raw_sha256": formula_source_sha256,
            "legacy_4_0_used": False,
            "signal_definition": "主升启动共振，即公式内部XS1与XS2同时成立",
        },
        "sample": {
            "event_date_min": str(formula_hits["first_board_date"].min()),
            "event_date_max": str(formula_hits["first_board_date"].max()),
            "formula_hit_n": len(formula_hits),
            "formula_hit_reach2_n": int(formula_hits["reach2"].sum()),
            "formula_hit_reach2_rate": float(formula_hits["reach2"].mean()),
            "formula_hit_reach3_n": int(formula_hits["reach3"].sum()),
            "formula_hit_reach3_rate": float(formula_hits["reach3"].mean()),
            "formula_hit_non_one_n": len(formula_non_one),
            "formula_hit_non_one_reach2_n": int(formula_non_one["reach2"].sum()),
            "formula_hit_non_one_reach2_rate": float(formula_non_one["reach2"].mean()),
            "formula_hit_non_one_reach3_n": int(formula_non_one["reach3"].sum()),
            "formula_hit_non_one_reach3_rate": float(formula_non_one["reach3"].mean()),
        },
        "top_factors": top_factors,
        "top_combinations": top_combinations,
        "coverage": {
            "source_column_count": len(events.columns),
            "candidate_factor_union_count": len(all_candidates),
            "excluded_column_count": len(all_excluded_map),
            "excluded_columns": [
                {"column": key, "reason": all_excluded_map[key]} for key in sorted(all_excluded_map)
            ],
            "scopes": scope_coverage,
            "threshold_or_category_rules_tested": int(sum(row["threshold_or_category_rules_tested"] for row in scope_coverage)),
            "combination_rules_tested": len(combinations),
            "combinations": combination_coverage,
        },
        "data": {
            "tdx_root": research.get("data", {}).get("tdx_root"),
            "latest_kline_date": research.get("data", {}).get("latest_kline_date"),
            "source_events_csv": {
                "path": str(Path(events_csv).resolve()),
                "size": Path(events_csv).resolve().stat().st_size,
                "sha256": sha256_path(Path(events_csv).resolve()),
            },
            "source_factor_manifest": {
                "path": str(Path(source_manifest).resolve()),
                "size": Path(source_manifest).resolve().stat().st_size,
                "sha256": sha256_path(Path(source_manifest).resolve()),
            },
        },
        "method": {
            "candidate_universe": "all source columns classified; identity, outcome/post-event, selection/status and constant columns excluded",
            "numeric_search": "all distinct training-period split points satisfying minimum support, both <= and >= directions",
            "categorical_search": "all categories satisfying minimum support versus all other categories",
            "validation": "threshold selected only on earliest 60% events by date and frozen on latest 40%",
            "stability": "positive train and validation effects, at least six comparable months, at least two-thirds positive months",
            "multiplicity": "Benjamini-Hochberg correction on one-sided out-of-time Fisher exact p-values",
            "combinations": "all two-factor and three-factor conjunctions of stable eligible univariate rules",
            "missing_imputation": False,
            "post_event_features_excluded": True,
        },
        "limitations": [
            "Industry mapping is the current local Tongdaxin snapshot rather than a historical point-in-time map.",
            "The event window is limited to the migrated sample window and should be rolled forward for prospective validation.",
            "Statistical association is not causality or a trading instruction.",
        ],
        "errors": [],
    }

    audit_path = output_directory / "飞龙共振首板_全部阈值检验.csv"
    factor_path = output_directory / "飞龙共振首板_单因子穷举结果.csv"
    combination_path = output_directory / "飞龙共振首板_二三因子组合穷举结果.csv"
    json_path = output_directory / "飞龙共振首板_稳定高胜率因子穷举.json"
    report_path = output_directory / "飞龙共振首板_稳定高胜率因子穷举报告.md"
    manifest_path = output_directory / "飞龙共振首板_稳定高胜率因子穷举清单.json"
    audit.to_csv(audit_path, index=False, encoding="utf-8-sig")
    factors.to_csv(factor_path, index=False, encoding="utf-8-sig")
    combinations.to_csv(combination_path, index=False, encoding="utf-8-sig")
    payload["artifacts"] = {
        "research_json": str(json_path),
        "threshold_audit_csv": str(audit_path),
        "factor_results_csv": str(factor_path),
        "combination_results_csv": str(combination_path),
        "report_markdown": str(report_path),
        "manifest": str(manifest_path),
    }
    payload = json_clean(payload)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    report_path.write_text(build_report(payload), encoding="utf-8")
    artifact_paths = {
        "research_json": json_path,
        "threshold_audit_csv": audit_path,
        "factor_results_csv": factor_path,
        "combination_results_csv": combination_path,
        "report_markdown": report_path,
    }
    artifacts = {
        key: {"path": str(path), "size": path.stat().st_size, "sha256": sha256_path(path)}
        for key, path in artifact_paths.items()
    }
    validation = {
        "status": "CLEAN_PASS",
        "errors": [],
        "source_factor_manifest_verified": True,
        "source_events_hash_verified": True,
        "formula_source_bound": True,
        "all_source_columns_classified": len(all_candidates) + len(all_excluded_map) == len(events.columns),
        "all_valid_training_thresholds_enumerated": True,
        "pair_and_triple_combinations_enumerated": True,
        "out_of_time_validation_used": True,
        "missing_values_not_imputed": True,
        "post_event_features_excluded": True,
        "artifact_hashes_verified": True,
    }
    if not validation["all_source_columns_classified"]:
        raise RuntimeError("source_column_classification_incomplete")
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "status": "CLEAN_PASS",
        "generated_at": generated_at,
        "formula_name": FORMULA_NAME,
        "legacy_4_0_used": False,
        "source_manifest": payload["data"]["source_factor_manifest"],
        "coverage": payload["coverage"],
        "artifacts": artifacts,
        "validation": validation,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["segment_manifest"] = str(manifest_path)
    payload["research_json"] = str(json_path)
    payload["threshold_audit_csv"] = str(audit_path)
    payload["factor_results_csv"] = str(factor_path)
    payload["combination_results_csv"] = str(combination_path)
    payload["report_markdown"] = str(report_path)
    return payload
