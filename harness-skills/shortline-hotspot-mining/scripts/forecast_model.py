#!/usr/bin/env python3
"""Independent H1/H2/H3 models for future hotspot probabilities."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Sequence

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score


HORIZONS = ("H1", "H2", "H3")
DEFAULT_FEATURES = (
    "return_1d",
    "return_3d",
    "relative_return_5d",
    "breadth",
    "amount_ratio",
    "limit_up_density",
    "persistence",
    "volatility",
    "drawdown",
    "coverage_ratio",
)
PROVISIONAL_COEFFICIENTS = {
    "H1": {
        "intercept": -1.35,
        "return_1d": 4.0,
        "return_3d": 3.0,
        "relative_return_5d": 2.5,
        "breadth": 0.80,
        "amount_ratio": 0.35,
        "limit_up_density": 1.30,
        "persistence": 0.45,
        "volatility": -2.0,
        "drawdown": 1.0,
        "coverage_ratio": 0.40,
    },
    "H2": {
        "intercept": -1.55,
        "return_1d": 1.8,
        "return_3d": 3.4,
        "relative_return_5d": 3.1,
        "breadth": 0.95,
        "amount_ratio": 0.30,
        "limit_up_density": 0.90,
        "persistence": 0.60,
        "volatility": -1.6,
        "drawdown": 0.8,
        "coverage_ratio": 0.35,
    },
    "H3": {
        "intercept": -1.75,
        "return_1d": 0.8,
        "return_3d": 1.9,
        "relative_return_5d": 3.5,
        "breadth": 0.70,
        "amount_ratio": 0.20,
        "limit_up_density": 0.55,
        "persistence": 0.75,
        "volatility": -1.2,
        "drawdown": 0.6,
        "coverage_ratio": 0.30,
    },
}


def _finite(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _sigmoid(value: float) -> float:
    bounded = max(-30.0, min(30.0, value))
    return 1.0 / (1.0 + math.exp(-bounded))


def _provisional_value(feature: str, row: dict) -> float:
    value = _finite(row.get(feature))
    if feature == "breadth":
        return value - 0.5
    if feature == "amount_ratio":
        return math.log(max(value, 0.01))
    if feature == "persistence":
        return value - 0.5
    if feature == "coverage_ratio":
        return value - 0.8
    return value


class TrainOnlyPreprocessor:
    """Median-impute, standardize and append missing flags using train rows only."""

    def __init__(self, feature_names: Sequence[str]):
        self.feature_names = tuple(feature_names)
        self.fit_row_count = 0
        self.medians: dict[str, float] = {}
        self.means: dict[str, float] = {}
        self.scales: dict[str, float] = {}

    def fit(self, rows: Sequence[dict]) -> "TrainOnlyPreprocessor":
        if not rows:
            raise ValueError("preprocessor_training_rows_missing")
        self.fit_row_count = len(rows)
        for feature in self.feature_names:
            values = [
                float(row[feature])
                for row in rows
                if row.get(feature) is not None and math.isfinite(float(row[feature]))
            ]
            median = float(np.median(values)) if values else 0.0
            imputed = np.asarray(
                [
                    float(row[feature])
                    if row.get(feature) is not None and math.isfinite(float(row[feature]))
                    else median
                    for row in rows
                ],
                dtype=float,
            )
            mean = float(imputed.mean())
            scale = float(imputed.std())
            self.medians[feature] = median
            self.means[feature] = mean
            self.scales[feature] = scale if scale > 1e-12 else 1.0
        return self

    def transform(self, rows: Sequence[dict]) -> np.ndarray:
        if not self.fit_row_count:
            raise ValueError("preprocessor_not_fit")
        numeric: list[list[float]] = []
        missing: list[list[float]] = []
        for row in rows:
            values: list[float] = []
            flags: list[float] = []
            for feature in self.feature_names:
                raw = row.get(feature)
                absent = raw is None
                if not absent:
                    try:
                        absent = not math.isfinite(float(raw))
                    except (TypeError, ValueError):
                        absent = True
                value = self.medians[feature] if absent else float(raw)
                values.append((value - self.means[feature]) / self.scales[feature])
                flags.append(float(absent))
            numeric.append(values)
            missing.append(flags)
        if not rows:
            return np.empty((0, len(self.feature_names) * 2), dtype=float)
        return np.hstack((np.asarray(numeric, dtype=float), np.asarray(missing, dtype=float)))

    def to_model_card(self) -> dict:
        return {
            "feature_names": list(self.feature_names),
            "fit_row_count": self.fit_row_count,
            "medians": dict(self.medians),
            "means": dict(self.means),
            "scales": dict(self.scales),
            "missing_indicators": [f"{value}_missing" for value in self.feature_names],
        }


def forecast_with_provisional_models(feature_snapshot: dict) -> dict:
    snapshot_id = str(feature_snapshot.get("snapshot_id", ""))
    forecasts: list[dict] = []
    excluded: list[dict] = []
    for row in feature_snapshot.get("sectors", []):
        if not row.get("rank_eligible", False):
            excluded.append({"sector": row.get("sector"), "reason": "rank_ineligible"})
            continue
        for horizon in HORIZONS:
            coefficients = PROVISIONAL_COEFFICIENTS[horizon]
            contributions = {
                feature: coefficients[feature] * _provisional_value(feature, row)
                for feature in DEFAULT_FEATURES
            }
            logit = coefficients["intercept"] + sum(contributions.values())
            forecasts.append(
                {
                    "snapshot_id": snapshot_id,
                    "feature_cutoff_date": feature_snapshot.get("feature_cutoff_date"),
                    "sector": row["sector"],
                    "horizon": horizon,
                    "market_probability": _sigmoid(logit),
                    "model_version": f"transparent-provisional-{horizon.lower()}-v1",
                    "calibration_version": "none-provisional",
                    "feature_contributions": contributions,
                    "forecast_status": "PROVISIONAL_FORECAST",
                }
            )
    for horizon in HORIZONS:
        candidates = [row for row in forecasts if row["horizon"] == horizon]
        candidates.sort(key=lambda row: (-row["market_probability"], row["sector"]))
        for rank, row in enumerate(candidates, start=1):
            row["market_rank"] = rank
    return {
        "schema": "SHORTLINE_FORECAST_RESULT_V1",
        "snapshot_id": snapshot_id,
        "forecast_status": "PROVISIONAL_FORECAST",
        "forecasts": forecasts,
        "excluded_sectors": excluded,
        "model_card": {
            "schema": "SHORTLINE_MODEL_CARD_V1",
            "forecast_status": "PROVISIONAL_FORECAST",
            "promotion_state": "not_promoted",
            "reason": "walk_forward_point_in_time_validation_not_available",
            "models": {
                horizon: {
                    "version": f"transparent-provisional-{horizon.lower()}-v1",
                    "coefficients": PROVISIONAL_COEFFICIENTS[horizon],
                    "calibration": "none",
                }
                for horizon in HORIZONS
            },
        },
    }


@dataclass
class FittedHorizonModel:
    horizon: str
    feature_names: tuple[str, ...]
    preprocessor: TrainOnlyPreprocessor
    selected_name: str
    estimator: object
    calibrator: IsotonicRegression | None
    training_dates: tuple[str, ...]
    validation_dates: tuple[str, ...]

    def predict_probabilities(self, rows: Sequence[dict]) -> np.ndarray:
        matrix = self.preprocessor.transform(rows)
        raw = np.asarray(self.estimator.predict_proba(matrix)[:, 1], dtype=float)
        calibrated = self.calibrator.predict(raw) if self.calibrator is not None else raw
        return np.clip(np.asarray(calibrated, dtype=float), 0.0, 1.0)

    def to_model_card(self) -> dict:
        estimator_card: dict = {
            "selected_model": self.selected_name,
            "training_dates": list(self.training_dates),
            "validation_dates": list(self.validation_dates),
            "calibration_fit_dates": list(self.validation_dates) if self.calibrator else [],
            "preprocessing": self.preprocessor.to_model_card(),
        }
        if hasattr(self.estimator, "coef_"):
            estimator_card["coefficients"] = np.asarray(self.estimator.coef_).tolist()
            estimator_card["intercept"] = np.asarray(self.estimator.intercept_).tolist()
        return estimator_card


def _trade_date_text(row: dict) -> str:
    value = row["trade_date"]
    return value.isoformat() if isinstance(value, date) else str(value)


def train_horizon_models(
    training_rows: Sequence[dict],
    validation_rows: Sequence[dict],
    *,
    feature_names: Sequence[str] = DEFAULT_FEATURES,
) -> dict[str, FittedHorizonModel]:
    models: dict[str, FittedHorizonModel] = {}
    for horizon in HORIZONS:
        train = [row for row in training_rows if row.get("horizon") == horizon]
        validation = [row for row in validation_rows if row.get("horizon") == horizon]
        if not train or not validation:
            raise ValueError(f"model_rows_missing:{horizon}")
        train_y = np.asarray([int(row["is_top_decile"]) for row in train], dtype=int)
        validation_y = np.asarray(
            [int(row["is_top_decile"]) for row in validation],
            dtype=int,
        )
        if len(np.unique(train_y)) < 2:
            raise ValueError(f"model_training_class_missing:{horizon}")
        preprocessor = TrainOnlyPreprocessor(feature_names).fit(train)
        train_x = preprocessor.transform(train)
        validation_x = preprocessor.transform(validation)
        baseline = LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=1000,
            random_state=20260823,
        ).fit(train_x, train_y)
        challenger = HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_depth=3,
            max_iter=100,
            random_state=20260823,
        ).fit(train_x, train_y)
        candidates = {"logistic": baseline, "hist_gradient_boosting": challenger}
        validation_scores: dict[str, float] = {}
        for name, estimator in candidates.items():
            probabilities = estimator.predict_proba(validation_x)[:, 1]
            validation_scores[name] = (
                float(average_precision_score(validation_y, probabilities))
                if len(np.unique(validation_y)) >= 2
                else float("-inf")
            )
        selected_name = max(
            validation_scores,
            key=lambda name: (validation_scores[name], name == "logistic"),
        )
        estimator = candidates[selected_name]
        validation_probability = estimator.predict_proba(validation_x)[:, 1]
        calibrator = None
        if len(np.unique(validation_y)) >= 2:
            calibrator = IsotonicRegression(out_of_bounds="clip").fit(
                validation_probability,
                validation_y,
            )
        models[horizon] = FittedHorizonModel(
            horizon=horizon,
            feature_names=tuple(feature_names),
            preprocessor=preprocessor,
            selected_name=selected_name,
            estimator=estimator,
            calibrator=calibrator,
            training_dates=tuple(sorted({_trade_date_text(row) for row in train})),
            validation_dates=tuple(sorted({_trade_date_text(row) for row in validation})),
        )
    return models
