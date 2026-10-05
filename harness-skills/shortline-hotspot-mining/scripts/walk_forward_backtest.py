#!/usr/bin/env python3
"""Expanding point-in-time walk-forward splits, metrics and promotion gates."""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import date
from typing import Iterable, Sequence

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, brier_score_loss


@dataclass(frozen=True)
class WalkForwardSplit:
    train_dates: tuple[date, ...]
    validation_dates: tuple[date, ...]
    test_dates: tuple[date, ...]
    embargo_dates: int


def _as_date(value: date | str) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def expanding_walk_forward_splits(
    trade_dates: Iterable[date | str],
    *,
    min_train_dates: int = 252,
    validation_dates: int = 60,
    test_dates: int = 60,
    embargo_dates: int = 10,
    step_dates: int = 60,
) -> list[WalkForwardSplit]:
    ordered = sorted({_as_date(value) for value in trade_dates})
    required = min_train_dates + embargo_dates + validation_dates + embargo_dates + test_dates
    if len(ordered) < required:
        raise ValueError(f"walk_forward_dates_insufficient:{len(ordered)}:{required}")
    splits: list[WalkForwardSplit] = []
    train_end = min_train_dates
    while train_end + embargo_dates + validation_dates + embargo_dates + test_dates <= len(ordered):
        validation_start = train_end + embargo_dates
        validation_end = validation_start + validation_dates
        test_start = validation_end + embargo_dates
        test_end = test_start + test_dates
        splits.append(
            WalkForwardSplit(
                train_dates=tuple(ordered[:train_end]),
                validation_dates=tuple(ordered[validation_start:validation_end]),
                test_dates=tuple(ordered[test_start:test_end]),
                embargo_dates=embargo_dates,
            )
        )
        train_end += step_dates
    return splits


def partition_rows_by_split(rows: Sequence[dict], split: WalkForwardSplit) -> dict[str, list[dict]]:
    date_sets = {
        "train": set(split.train_dates),
        "validation": set(split.validation_dates),
        "test": set(split.test_dates),
    }
    partition = {name: [] for name in date_sets}
    for row in rows:
        row_date = _as_date(row["trade_date"])
        matches = [name for name, dates in date_sets.items() if row_date in dates]
        if len(matches) > 1:
            raise ValueError(f"walk_forward_date_partition_overlap:{row_date.isoformat()}")
        if matches:
            partition[matches[0]].append(row)
    return partition


def _rank_ic(rows: Sequence[dict]) -> float:
    values: list[float] = []
    dates = sorted({_as_date(row["trade_date"]) for row in rows})
    for trade_day in dates:
        group = [row for row in rows if _as_date(row["trade_date"]) == trade_day]
        actual = [float(row["future_activity_score"]) for row in group]
        probability = [float(row["probability"]) for row in group]
        if len(group) >= 3 and len(set(actual)) > 1 and len(set(probability)) > 1:
            correlation = spearmanr(actual, probability).statistic
            if correlation is not None and math.isfinite(float(correlation)):
                values.append(float(correlation))
    return statistics.fmean(values) if values else float("nan")


def _precision_at_top5(rows: Sequence[dict]) -> float:
    values: list[float] = []
    for trade_day in sorted({_as_date(row["trade_date"]) for row in rows}):
        group = [row for row in rows if _as_date(row["trade_date"]) == trade_day]
        selected = sorted(group, key=lambda row: (-float(row["probability"]), str(row["sector"])))[:5]
        if selected:
            values.append(statistics.fmean(int(row["is_top_decile"]) for row in selected))
    return statistics.fmean(values) if values else float("nan")


def expected_calibration_error(rows: Sequence[dict], bins: int = 10) -> float:
    if not rows:
        return float("nan")
    weighted = 0.0
    for index in range(bins):
        low = index / bins
        high = (index + 1) / bins
        group = [
            row
            for row in rows
            if low <= float(row["probability"]) < high
            or index == bins - 1 and float(row["probability"]) == 1.0
        ]
        if group:
            confidence = statistics.fmean(float(row["probability"]) for row in group)
            frequency = statistics.fmean(int(row["is_top_decile"]) for row in group)
            weighted += len(group) / len(rows) * abs(confidence - frequency)
    return weighted


def compute_oos_metrics(rows: Sequence[dict]) -> dict:
    if not rows:
        raise ValueError("oos_predictions_missing")
    actual = np.asarray([int(row["is_top_decile"]) for row in rows], dtype=int)
    probability = np.asarray([float(row["probability"]) for row in rows], dtype=float)
    base_rate = float(actual.mean())
    model_brier = float(brier_score_loss(actual, probability))
    baseline_brier = float(brier_score_loss(actual, np.full(len(actual), base_rate)))
    precision = _precision_at_top5(rows)
    baseline_precision = float(
        statistics.fmean(float(row.get("baseline_top5_precision", base_rate)) for row in rows)
    )
    return {
        "observation_count": len(rows),
        "date_count": len({_as_date(row["trade_date"]) for row in rows}),
        "base_rate": base_rate,
        "precision_at_top5": precision,
        "precision_lift_vs_best_baseline": (
            precision / baseline_precision - 1.0 if baseline_precision > 0 else float("nan")
        ),
        "pr_auc": float(average_precision_score(actual, probability)),
        "pr_auc_above_base_rate": float(average_precision_score(actual, probability)) > base_rate,
        "rank_ic": _rank_ic(rows),
        "brier_skill_score": (
            1.0 - model_brier / baseline_brier if baseline_brier > 0 else float("nan")
        ),
        "ece": expected_calibration_error(rows),
    }


def _gate(condition: bool, reason: str, reasons: list[str]) -> None:
    if not condition:
        reasons.append(reason)


def determine_forecast_status(metrics: dict, *, point_in_time_membership: bool) -> dict:
    reasons: list[str] = []
    _gate(point_in_time_membership, "point_in_time_membership_not_proven", reasons)
    _gate(float(metrics.get("precision_at_top5", -math.inf)) >= 0.20, "precision_at_top5_below_0_20", reasons)
    _gate(
        float(metrics.get("precision_lift_vs_best_baseline", -math.inf)) >= 0.25,
        "precision_lift_below_25_percent",
        reasons,
    )
    _gate(bool(metrics.get("pr_auc_above_base_rate", False)), "pr_auc_not_above_base_rate", reasons)
    _gate(float(metrics.get("pr_auc_delta_ci_lower", -math.inf)) > 0.0, "pr_auc_delta_ci_lower_not_positive", reasons)
    _gate(float(metrics.get("rank_ic", -math.inf)) > 0.0, "rank_ic_not_positive", reasons)
    _gate(float(metrics.get("rank_ic_ci_lower", -math.inf)) > 0.0, "rank_ic_ci_lower_not_positive", reasons)
    _gate(float(metrics.get("brier_skill_score", -math.inf)) > 0.0, "brier_skill_not_positive", reasons)
    _gate(float(metrics.get("ece", math.inf)) <= 0.08, "ece_above_0_08", reasons)
    _gate(float(metrics.get("windows_led_fraction", -math.inf)) >= 0.70, "windows_led_fraction_below_0_70", reasons)
    regimes = ("bull", "bear", "sideways")
    regime_days = metrics.get("regime_days", {})
    regime_rank_ic = metrics.get("regime_rank_ic", {})
    for regime in regimes:
        _gate(int(regime_days.get(regime, 0)) >= 60, f"regime_days_below_60:{regime}", reasons)
        _gate(float(regime_rank_ic.get(regime, -math.inf)) >= 0.0, f"regime_rank_ic_negative:{regime}", reasons)
    return {
        "forecast_status": "VALIDATED_FORECAST" if not reasons else "PROVISIONAL_FORECAST",
        "reasons": reasons,
    }


def block_bootstrap_interval(
    rows: Sequence[dict],
    metric,
    *,
    block_dates: int = 20,
    samples: int = 500,
    seed: int = 20260823,
) -> tuple[float, float]:
    dates = sorted({_as_date(row["trade_date"]) for row in rows})
    if not dates:
        return (float("nan"), float("nan"))
    blocks = [dates[index : index + block_dates] for index in range(0, len(dates), block_dates)]
    rng = np.random.default_rng(seed)
    values: list[float] = []
    for _ in range(samples):
        chosen = [blocks[index] for index in rng.integers(0, len(blocks), len(blocks))]
        selected_dates = [value for block in chosen for value in block]
        sampled: list[dict] = []
        for sampled_date in selected_dates:
            sampled.extend(row for row in rows if _as_date(row["trade_date"]) == sampled_date)
        value = float(metric(sampled))
        if math.isfinite(value):
            values.append(value)
    if not values:
        return (float("nan"), float("nan"))
    return (float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975)))


def _pr_auc_delta(rows: Sequence[dict]) -> float:
    actual = np.asarray([int(row["is_top_decile"]) for row in rows], dtype=int)
    if len(np.unique(actual)) < 2:
        return float("nan")
    model = np.asarray([float(row["probability"]) for row in rows], dtype=float)
    baseline = np.asarray(
        [float(row.get("baseline_probability", actual.mean())) for row in rows],
        dtype=float,
    )
    return float(
        average_precision_score(actual, model)
        - average_precision_score(actual, baseline)
    )


def _windows_led_fraction(rows: Sequence[dict]) -> float:
    comparisons: list[bool] = []
    keys = sorted(
        {
            (_as_date(row["trade_date"]), str(row["horizon"]))
            for row in rows
        }
    )
    for trade_day, horizon in keys:
        group = [
            row
            for row in rows
            if _as_date(row["trade_date"]) == trade_day
            and str(row["horizon"]) == horizon
        ]
        model_precision = _precision_at_top5(group)
        baseline_precision = statistics.fmean(
            float(row.get("baseline_top5_precision", 0.0)) for row in group
        )
        comparisons.append(model_precision > baseline_precision)
    return statistics.fmean(comparisons) if comparisons else float("nan")


def run_walk_forward_backtest(
    rows: Sequence[dict],
    *,
    feature_names: Sequence[str],
    split_kwargs: dict | None = None,
    bootstrap_samples: int = 500,
    point_in_time_membership: bool | None = None,
) -> dict:
    from forecast_model import train_horizon_models

    split_kwargs = dict(split_kwargs or {})
    splits = expanding_walk_forward_splits(
        (_as_date(row["trade_date"]) for row in rows),
        **split_kwargs,
    )
    predictions: list[dict] = []
    fold_reports: list[dict] = []
    for fold_index, split in enumerate(splits, start=1):
        partition = partition_rows_by_split(rows, split)
        models = train_horizon_models(
            partition["train"],
            partition["validation"],
            feature_names=feature_names,
        )
        for horizon, model in models.items():
            test_rows = [
                row for row in partition["test"] if str(row.get("horizon")) == horizon
            ]
            probabilities = model.predict_probabilities(test_rows)
            for source, probability in zip(test_rows, probabilities):
                predictions.append(
                    {
                        "fold": fold_index,
                        "trade_date": _as_date(source["trade_date"]).isoformat(),
                        "horizon": horizon,
                        "sector": str(source["sector"]),
                        "probability": float(probability),
                        "is_top_decile": int(source["is_top_decile"]),
                        "future_activity_score": float(source["future_activity_score"]),
                        "baseline_probability": float(
                            source.get("baseline_probability", 0.10)
                        ),
                        "baseline_top5_precision": float(
                            source.get("baseline_top5_precision", 0.10)
                        ),
                        "regime": str(source.get("regime", "unknown")),
                    }
                )
        fold_reports.append(
            {
                "fold": fold_index,
                "train_dates": [value.isoformat() for value in split.train_dates],
                "validation_dates": [
                    value.isoformat() for value in split.validation_dates
                ],
                "test_dates": [value.isoformat() for value in split.test_dates],
                "embargo_dates": split.embargo_dates,
                "models": {
                    horizon: model.to_model_card() for horizon, model in models.items()
                },
            }
        )

    metrics = compute_oos_metrics(predictions)
    rank_interval = block_bootstrap_interval(
        predictions,
        _rank_ic,
        samples=bootstrap_samples,
    )
    pr_delta_interval = block_bootstrap_interval(
        predictions,
        _pr_auc_delta,
        samples=bootstrap_samples,
    )
    metrics["rank_ic_ci_lower"] = rank_interval[0]
    metrics["rank_ic_ci_upper"] = rank_interval[1]
    metrics["pr_auc_delta_ci_lower"] = pr_delta_interval[0]
    metrics["pr_auc_delta_ci_upper"] = pr_delta_interval[1]
    metrics["windows_led_fraction"] = _windows_led_fraction(predictions)
    metrics["regime_rank_ic"] = {}
    metrics["regime_days"] = {}
    for regime in ("bull", "bear", "sideways"):
        group = [row for row in predictions if row["regime"] == regime]
        metrics["regime_days"][regime] = len(
            {_as_date(row["trade_date"]) for row in group}
        )
        metrics["regime_rank_ic"][regime] = _rank_ic(group) if group else float("nan")
    if point_in_time_membership is None:
        point_in_time_membership = bool(rows) and all(
            bool(row.get("point_in_time_membership", False)) for row in rows
        )
    status = determine_forecast_status(
        metrics,
        point_in_time_membership=point_in_time_membership,
    )
    return {
        "schema": "SHORTLINE_WALK_FORWARD_BACKTEST_V1",
        "forecast_status": status["forecast_status"],
        "status_reasons": status["reasons"],
        "fold_count": len(splits),
        "folds": fold_reports,
        "metrics": metrics,
        "predictions": predictions,
    }
