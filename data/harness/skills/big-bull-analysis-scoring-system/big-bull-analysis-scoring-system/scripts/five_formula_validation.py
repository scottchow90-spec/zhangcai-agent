"""Leakage-resistant validation utilities for the five-formula research protocol.

This module deliberately contains validation only: it does not fit a model,
run a backtest, or produce a stock score.
"""

from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


_DATE8 = re.compile(r"\d{8}")
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _normalize_date(value: object, *, field: str = "date") -> str:
    if type(value) is not str:
        raise ValueError(f"{field}_must_be_string")
    raw = value.strip()
    if _DATE8.fullmatch(raw):
        fmt = "%Y%m%d"
    elif _ISO_DATE.fullmatch(raw):
        fmt = "%Y-%m-%d"
    else:
        raise ValueError(f"{field}_must_be_strict_yyyymmdd_or_iso_date")
    try:
        return date.fromisoformat(
            f"{raw[:4]}-{raw[4:6]}-{raw[6:]}" if fmt == "%Y%m%d" else raw
        ).strftime("%Y%m%d")
    except ValueError as exc:
        raise ValueError(f"{field}_invalid_calendar_date:{value}") from exc


def _date_values(values: object, *, field: str = "dates") -> list[str]:
    if isinstance(values, (str, bytes, bytearray, Mapping)) or not isinstance(values, Sequence):
        raise TypeError(f"{field}_must_be_sequence")
    normalized = [_normalize_date(value, field=field) for value in values]
    if not normalized:
        raise ValueError(f"{field}_empty")
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field}_duplicate_after_normalization")
    if normalized != sorted(normalized):
        raise ValueError(f"{field}_must_be_strictly_chronological")
    return normalized


def _require_frame(frame: object, *, label: str = "frame") -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{label}_must_be_dataframe")
    if frame.empty:
        raise ValueError(f"{label}_empty")
    return frame


def _finite_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if type(column) is not str or column not in frame.columns:
        raise ValueError(f"missing_column:{column}")
    try:
        values = pd.to_numeric(frame[column], errors="raise").astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"column_must_be_numeric:{column}") from exc
    if values.isna().any() or not np.isfinite(values.to_numpy()).all():
        raise ValueError(f"column_must_be_finite:{column}")
    return values


def _normalized_frame_dates(frame: pd.DataFrame, column: str) -> list[str]:
    if column not in frame.columns:
        raise ValueError(f"missing_column:{column}")
    return [_normalize_date(value, field=column) for value in frame[column].tolist()]


def purged_chronological_split(
    dates: Sequence[str],
    purge_dates: int = 10,
    train_fraction: float = .6,
    validation_fraction: float = .2,
) -> dict[str, Any]:
    normalized = _date_values(dates)
    if type(purge_dates) is not int or purge_dates < 10:
        raise ValueError("purge_dates_must_be_integer_at_least_10")
    if isinstance(train_fraction, bool) or isinstance(validation_fraction, bool):
        raise TypeError("fractions_must_be_numeric")
    train_fraction = float(train_fraction)
    validation_fraction = float(validation_fraction)
    if not (0 < train_fraction < 1 and 0 < validation_fraction < 1 and train_fraction + validation_fraction < 1):
        raise ValueError("invalid_split_fractions")
    # The caller supplies the unique signal-date index.  Purging therefore
    # removes actual entries from that index, not inferred rebalance periods.
    purge_slots = purge_dates
    usable = len(normalized) - 2 * purge_slots
    if usable < 3:
        raise ValueError("insufficient_rebalance_dates_for_three_splits_and_purges")
    train_count = max(1, round(usable * train_fraction))
    validation_count = max(1, round(usable * validation_fraction))
    if train_count + validation_count >= usable:
        validation_count = max(1, usable - train_count - 1)
    test_count = usable - train_count - validation_count
    if min(train_count, validation_count, test_count) < 1:
        raise ValueError("insufficient_rebalance_dates_for_nonempty_splits")
    first = train_count
    second = first + purge_slots
    third = second + validation_count
    fourth = third + purge_slots
    return {
        "train_dates": normalized[:first],
        "purged_train_validation_dates": normalized[first:second],
        "validation_dates": normalized[second:third],
        "purged_validation_test_dates": normalized[third:fourth],
        "final_test_dates": normalized[fourth:],
        "purge_rebalance_date_count_per_boundary": purge_slots,
        "purge_trading_dates_per_boundary": purge_slots,
        "requested_fractions": {"train": train_fraction, "validation": validation_fraction, "final_test": 1 - train_fraction - validation_fraction},
        "actual_counts": {"train": train_count, "validation": validation_count, "final_test": test_count},
    }


def newey_west_mean_statistics(values: Sequence[float], *, horizon: int | None = None, lag: int | None = None) -> dict[str, Any]:
    if isinstance(values, (str, bytes, bytearray, Mapping)) or not isinstance(values, Sequence):
        raise TypeError("values_must_be_sequence")
    if not values:
        raise ValueError("values_empty")
    try:
        sample = np.asarray(list(values), dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("values_must_be_numeric") from exc
    if sample.ndim != 1 or not np.isfinite(sample).all():
        raise ValueError("values_must_be_finite_one_dimensional")
    if horizon is not None and horizon not in (5, 10):
        raise ValueError("horizon_must_be_5_or_10")
    if lag is None:
        selected_lag = {5: 4, 10: 9}.get(horizon, 0)
    else:
        if type(lag) is not int or lag < 0:
            raise ValueError("lag_must_be_nonnegative_integer")
        selected_lag = lag
    mean = float(sample.mean())
    centered = sample - mean
    count = len(sample)
    long_run_variance = float(np.dot(centered, centered) / count)
    for step in range(1, min(selected_lag, count - 1) + 1):
        covariance = float(np.dot(centered[step:], centered[:-step]) / count)
        long_run_variance += 2 * (1 - step / (selected_lag + 1)) * covariance
    standard_error = math.sqrt(max(0.0, long_run_variance) / count)
    inference_available = count >= selected_lag + 2 and standard_error > 1e-15
    t_stat = mean / standard_error if inference_available else None
    return {
        "count": count, "mean": mean, "standard_error": standard_error,
        "t_stat": t_stat,
        "ci95_lower": mean - 1.96 * standard_error if inference_available else None,
        "ci95_upper": mean + 1.96 * standard_error if inference_available else None,
        "inference_available": inference_available, "lag": selected_lag,
        "horizon": horizon,
    }


def date_block_bootstrap(frame: pd.DataFrame, *, value_column: str, date_column: str = "date", block_dates: int = 20, replicates: int = 2000, seed: int = 20260819) -> dict[str, Any]:
    frame = _require_frame(frame)
    if type(block_dates) is not int or block_dates != 20:
        raise ValueError("fixed_bootstrap_block_dates_must_equal_20")
    if type(replicates) is not int or replicates != 2000:
        raise ValueError("fixed_bootstrap_replicates_must_equal_2000")
    if type(seed) is not int or seed != 20260819:
        raise ValueError("fixed_bootstrap_seed_must_equal_20260819")
    normalized_dates = _normalized_frame_dates(frame, date_column)
    if normalized_dates != sorted(normalized_dates):
        raise ValueError("frame_dates_must_be_chronological")
    values = _finite_series(frame, value_column).to_numpy()
    unique_dates = list(dict.fromkeys(normalized_dates))
    if len(unique_dates) < block_dates:
        raise ValueError("at least_20_unique_signal_dates_required")
    by_date = {day: values[np.asarray(normalized_dates) == day] for day in unique_dates}
    rng = np.random.default_rng(seed)
    means: list[float] = []
    max_start = len(unique_dates) - block_dates
    for _ in range(replicates):
        selected: list[str] = []
        while len(selected) < len(unique_dates):
            start = int(rng.integers(0, max_start + 1))
            selected.extend(unique_dates[start:start + block_dates])
        sampled = np.concatenate([by_date[day] for day in selected[:len(unique_dates)]])
        means.append(float(sampled.mean()))
    return {
        "observed_mean": float(values.mean()), "bootstrap_standard_error": float(np.std(means, ddof=1)),
        "ci95_lower": float(np.quantile(means, .025)), "ci95_upper": float(np.quantile(means, .975)),
        "block_dates": block_dates, "replicates": replicates, "seed": seed,
        "unique_date_count": len(unique_dates), "replicate_means": means,
        "sampling_unit": "whole_signal_date_contiguous_block",
    }


def _rank_correlation(left: pd.Series, right: pd.Series) -> float | None:
    pair = pd.DataFrame({"left": pd.to_numeric(left, errors="coerce"), "right": pd.to_numeric(right, errors="coerce")}).dropna()
    pair = pair[np.isfinite(pair["left"]) & np.isfinite(pair["right"])]
    if len(pair) < 2 or pair["left"].nunique() < 2 or pair["right"].nunique() < 2:
        return None
    value = pair["left"].rank().corr(pair["right"].rank())
    return float(value) if pd.notna(value) else None


def decile_monotonicity(frame: pd.DataFrame, *, score_column: str, target_column: str, date_column: str = "date") -> dict[str, Any]:
    frame = _require_frame(frame)
    _normalized_frame_dates(frame, date_column)
    _finite_series(frame, score_column); _finite_series(frame, target_column)
    rows: list[pd.DataFrame] = []
    for _, group in frame.groupby(date_column, sort=True):
        if len(group) < 10 or group[score_column].nunique() < 10:
            continue
        work = group[[score_column, target_column]].copy()
        work["decile"] = np.ceil(work[score_column].rank(method="first", pct=True) * 10).astype(int).clip(1, 10)
        rows.append(work)
    if not rows:
        raise ValueError("no_date_has_ten_informative_scores")
    pooled = pd.concat(rows, ignore_index=True)
    means = pooled.groupby("decile")[target_column].mean().reindex(range(1, 11))
    if means.isna().any():
        raise ValueError("all_ten_deciles_required")
    values = [float(value) for value in means]
    increases = sum(values[i] >= values[i - 1] for i in range(1, 10))
    corr = _rank_correlation(pd.Series(range(1, 11)), pd.Series(values))
    return {"decile_means": [{"decile": i, "mean_target": values[i - 1]} for i in range(1, 11)], "adjacent_increases": increases, "monotonic_increasing": increases == 9, "decile_rank_correlation": corr, "date_count": len(rows)}


def slice_market_regimes(frame: pd.DataFrame, *, return_column: str, date_column: str = "date") -> dict[str, Any]:
    frame = _require_frame(frame)
    dates = _normalized_frame_dates(frame, date_column)
    values = _finite_series(frame, return_column)
    work = pd.DataFrame({"date": dates, "value": values})
    daily = work.groupby("date", sort=True)["value"].mean()
    lower, upper = (float(value) for value in daily.quantile([1 / 3, 2 / 3]))
    date_regime = {day: ("bear" if value <= lower else "bull" if value >= upper else "sideways") for day, value in daily.items()}
    regimes: dict[str, dict[str, Any]] = {}
    for name in ("bear", "sideways", "bull"):
        selected_dates = [day for day, regime in date_regime.items() if regime == name]
        mask = work["date"].isin(selected_dates)
        regimes[name] = {"date_count": len(selected_dates), "row_count": int(mask.sum()), "mean_return": float(work.loc[mask, "value"].mean()) if mask.any() else None, "dates": selected_dates}
    return {"regimes": regimes, "thresholds": {"lower_tercile": lower, "upper_tercile": upper}, "date_regime": date_regime}


def exposure_diagnostics(frame: pd.DataFrame, *, score_column: str, date_column: str = "date", exposure_columns: Sequence[str]) -> dict[str, Any]:
    frame = _require_frame(frame)
    _normalized_frame_dates(frame, date_column)
    _finite_series(frame, score_column)
    if isinstance(exposure_columns, (str, bytes, Mapping)) or not isinstance(exposure_columns, Sequence) or not exposure_columns:
        raise TypeError("exposure_columns_must_be_nonempty_sequence")
    diagnostics: dict[str, Any] = {}
    for column in exposure_columns:
        _finite_series(frame, column)
        daily = [value for _, group in frame.groupby(date_column, sort=True) if (value := _rank_correlation(group[score_column], group[column])) is not None]
        diagnostics[column] = {"overall_rank_correlation": _rank_correlation(frame[score_column], frame[column]), "mean_daily_rank_correlation": float(np.mean(daily)) if daily else None, "max_abs_daily_rank_correlation": max(map(abs, daily)) if daily else None, "date_count": len(daily)}
    return {"exposures": diagnostics, "score_column": score_column}


def run_leakage_canaries(frame: pd.DataFrame, *, feature_columns: Sequence[str], label_columns: Sequence[str], date_column: str = "date") -> dict[str, Any]:
    frame = _require_frame(frame)
    dates = _normalized_frame_dates(frame, date_column)
    if isinstance(feature_columns, (str, bytes, Mapping)) or not isinstance(feature_columns, Sequence):
        raise TypeError("feature_columns_must_be_sequence")
    if isinstance(label_columns, (str, bytes, Mapping)) or not isinstance(label_columns, Sequence):
        raise TypeError("label_columns_must_be_sequence")
    for column in [*feature_columns, *label_columns]:
        if column not in frame.columns:
            raise ValueError(f"missing_column:{column}")
    def tokens(value: object) -> set[str]:
        camel_split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(value))
        return {
            token.lower()
            for token in re.split(r"(?:[^A-Za-z0-9]+|_+)", camel_split)
            if token
        }

    future_tokens = {"future", "forward", "label", "target"}
    future = any(tokens(column) & future_tokens for column in feature_columns)
    for feature in feature_columns:
        for label in label_columns:
            corr = _rank_correlation(frame[feature], frame[label])
            future = future or (corr is not None and abs(corr) >= .999999)
    shuffled = dates != sorted(dates)
    split_columns = [column for column in frame.columns if str(column).lower() in {"split", "partition", "dataset_split", "sample_split"}]
    pollution_tokens = {"final", "test", "holdout"}
    polluted = any(
        any(tokens(value) & pollution_tokens for value in frame[column].tolist())
        for column in split_columns
    )
    checks = {"future_injection": future, "date_shuffle": shuffled, "test_contamination": polluted}
    triggered = [name for name, value in checks.items() if value]
    return {"passed": not triggered, "triggered": triggered, "canaries": checks}


def _daily_rank_correlations(frame: pd.DataFrame, feature: str, target: str, date_column: str) -> list[float]:
    return [value for _, group in frame.groupby(date_column, sort=True) if (value := _rank_correlation(group[feature], group[target])) is not None]


def _bh_rejections(p_values: dict[str, float], q: float) -> tuple[set[str], list[dict[str, Any]]]:
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    cutoff = -1
    for index, (_, p_value) in enumerate(ordered, start=1):
        if p_value <= q * index / len(ordered):
            cutoff = index
    rejected = {key for key, _ in ordered[:cutoff]} if cutoff >= 1 else set()
    return rejected, [{"key": key, "p_value": value, "rank": i, "critical_value": q * i / len(ordered), "rejected": key in rejected} for i, (key, value) in enumerate(ordered, start=1)]


def evaluate_train_only_eligibility(train_frame: pd.DataFrame, *, catalog: Sequence[Mapping[str, Any]], feature_columns: Sequence[str], target_column: str, date_column: str = "date", q: float = .10, correlation_threshold: float = .90) -> dict[str, Any]:
    frame = _require_frame(train_frame, label="train_frame")
    dates = _normalized_frame_dates(frame, date_column)
    _finite_series(frame, target_column)
    if not (0 < q < 1) or not (0 < correlation_threshold <= 1):
        raise ValueError("invalid_q_or_correlation_threshold")
    if isinstance(catalog, (str, bytes, Mapping)) or not isinstance(catalog, Sequence):
        raise TypeError("catalog_must_be_sequence")
    catalog_by_key = {str(item.get("key")): dict(item) for item in catalog if isinstance(item, Mapping) and item.get("key") is not None}
    if isinstance(feature_columns, (str, bytes, Mapping)) or not isinstance(feature_columns, Sequence) or not feature_columns:
        raise TypeError("feature_columns_must_be_nonempty_sequence")
    unique_dates = sorted(set(dates))
    digest = hashlib.sha256(("\n".join(unique_dates) + "\n").encode("ascii")).hexdigest()
    diagnostics: dict[str, Any] = {}; demotions: dict[str, list[str]] = {}; p_values: dict[str, float] = {}
    for key in feature_columns:
        if key not in catalog_by_key or key not in frame.columns:
            raise ValueError(f"feature_missing_from_catalog_or_frame:{key}")
        numeric = pd.to_numeric(frame[key], errors="coerce").astype(float)
        finite = numeric.notna() & np.isfinite(numeric)
        daily_coverage = finite.groupby(pd.Series(dates, index=frame.index)).mean()
        coverage = float(finite.mean()); median_coverage = float(daily_coverage.median())
        correlations = _daily_rank_correlations(frame, key, target_column, date_column)
        mean_ic = float(np.mean(correlations)) if correlations else None
        reasons: list[str] = []
        if not bool(catalog_by_key[key].get("model_eligible", True)): reasons.append("catalog_model_ineligible")
        if coverage < .8: reasons.append("coverage_below_0.80")
        if numeric[finite].nunique() < 2 or not correlations: reasons.append("uninformative")
        direction = str(catalog_by_key[key].get("expected_direction", ""))
        if mean_ic is not None and ((direction == "higher_is_bullish" and mean_ic <= 0) or (direction == "lower_is_bullish" and mean_ic >= 0)): reasons.append("unexpected_direction")
        if correlations:
            stats = newey_west_mean_statistics(correlations, horizon=5)
            t_value = stats["t_stat"]
            if stats["inference_available"] and t_value is not None:
                p_values[key] = math.erfc(abs(float(t_value)) / math.sqrt(2))
        diagnostics[key] = {"coverage": coverage, "median_daily_coverage": median_coverage, "informative_date_count": len(correlations), "mean_daily_rank_correlation": mean_ic, "expected_direction": direction, "p_value": p_values.get(key)}
        if reasons: demotions[key] = reasons
    rejected, bh_rows = _bh_rejections(p_values, q) if p_values else (set(), [])
    for key in feature_columns:
        if key not in rejected:
            demotions.setdefault(key, []).append("bh_fdr_not_significant")
    eligible_for_grouping = [key for key in feature_columns if key not in demotions]
    parent = {key: key for key in eligible_for_grouping}
    def find(key: str) -> str:
        while parent[key] != key:
            parent[key] = parent[parent[key]]; key = parent[key]
        return key
    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb: parent[max(ra, rb)] = min(ra, rb)
    daily_ranks = {key: frame.groupby(date_column, sort=False)[key].rank(pct=True) for key in eligible_for_grouping}
    for i, left in enumerate(eligible_for_grouping):
        for right in eligible_for_grouping[i + 1:]:
            corr = _rank_correlation(daily_ranks[left], daily_ranks[right])
            if corr is not None and abs(corr) >= correlation_threshold: union(left, right)
    components: dict[str, list[str]] = {}
    for key in eligible_for_grouping: components.setdefault(find(key), []).append(key)
    groups: list[dict[str, Any]] = []
    selected: list[str] = []
    for members in sorted(components.values(), key=lambda item: min(item)):
        representative = sorted(members, key=lambda key: (-diagnostics[key]["median_daily_coverage"], key))[0]
        selected.append(representative)
        for key in members:
            if key != representative: demotions.setdefault(key, []).append(f"correlated_group_representative:{representative}")
        groups.append({"members": sorted(members), "representative": representative, "threshold": correlation_threshold})
    return {"eligible_features": sorted(selected), "demotions": {key: value for key, value in sorted(demotions.items())}, "diagnostics": diagnostics, "correlation_groups": groups, "bh_fdr": {"q": q, "tests": bh_rows, "rejected_keys": sorted(rejected)}, "training_dates": unique_dates, "training_date_sha256": digest, "scope": "train_only"}


def select_candidate(train_frame: pd.DataFrame, validation_frame: pd.DataFrame, *, frozen_protocol: Mapping[str, Any]) -> dict[str, Any]:
    train = _require_frame(train_frame, label="train_frame"); validation = _require_frame(validation_frame, label="validation_frame")
    if not isinstance(frozen_protocol, Mapping): raise TypeError("frozen_protocol_must_be_mapping")
    protocol = dict(frozen_protocol)
    candidates = protocol.get("candidate_grid", protocol.get("frozen_candidates"))
    if isinstance(candidates, (str, bytes, Mapping)) or not isinstance(candidates, Sequence) or not candidates:
        raise ValueError("frozen_candidate_grid_must_be_nonempty")
    target = protocol.get("target_column")
    date_column = str(protocol.get("date_column", "date"))
    if type(target) is not str or target not in validation.columns: raise ValueError("frozen_target_column_missing")
    _normalized_frame_dates(train, date_column); _normalized_frame_dates(validation, date_column)
    evaluated: list[dict[str, Any]] = []
    for raw in candidates:
        if not isinstance(raw, Mapping): raise TypeError("candidate_must_be_mapping")
        key = str(raw.get("key", "")); score_column = raw.get("score_column", key)
        if not key or type(score_column) is not str or score_column not in train.columns or score_column not in validation.columns: raise ValueError(f"frozen_candidate_column_missing:{key}")
        correlations = _daily_rank_correlations(validation, score_column, target, date_column)
        if not correlations: raise ValueError(f"candidate_not_evaluable:{key}")
        evaluated.append({"key": key, "score_column": score_column, "validation_mean_rank_correlation": float(np.mean(correlations)), "validation_date_count": len(correlations)})
    selected = sorted(evaluated, key=lambda item: (-item["validation_mean_rank_correlation"], item["key"]))[0]
    protocol_sha = hashlib.sha256(json.dumps(protocol, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"selected_candidate": selected["key"], "selected_metrics": selected, "candidate_results": evaluated, "frozen_protocol_sha256": protocol_sha, "data_scope": "train_and_validation_only", "final_test_read": False}


def load_final_test_rows(path: str | Path) -> pd.DataFrame:
    if not isinstance(path, (str, Path)): raise TypeError("path_must_be_string_or_path")
    source = Path(path)
    if not source.is_file(): raise FileNotFoundError(source)
    suffix = source.suffix.lower()
    if suffix == ".csv": frame = pd.read_csv(source)
    elif suffix in {".parquet", ".pq"}: frame = pd.read_parquet(source)
    elif suffix in {".jsonl", ".ndjson"}: frame = pd.read_json(source, lines=True)
    elif suffix == ".json": frame = pd.read_json(source)
    else: raise ValueError(f"unsupported_final_test_format:{suffix or '<none>'}")
    if frame.empty: raise ValueError("final_test_rows_empty")
    return frame.copy(deep=True)


__all__ = [
    "purged_chronological_split", "newey_west_mean_statistics", "date_block_bootstrap",
    "decile_monotonicity", "slice_market_regimes", "exposure_diagnostics",
    "run_leakage_canaries", "evaluate_train_only_eligibility", "select_candidate",
    "load_final_test_rows",
]
