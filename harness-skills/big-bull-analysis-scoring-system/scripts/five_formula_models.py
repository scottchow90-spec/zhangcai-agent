from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import copy
import itertools
import math
import warnings
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import logsumexp
from scipy.stats import norm, spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNet


SYSTEMS = (
    "大牛线撑压版",
    "飞龙在天",
    "游资资金监控",
    "庄家资金监控",
    "机构资金监控",
)
ALPHA_GRID = (1e-6, 1e-5, 1e-4, 1e-3, 1e-2)
L1_RATIO_GRID = (0.25, 0.5, 0.75, 1.0)
MAIN_COLUMNS = SYSTEMS
INTERACTION_COLUMNS = tuple(
    f"sqrt_resonance::{left}|{right}"
    for left, right in itertools.combinations(SYSTEMS, 2)
) + ("agreement",)
FUSION_COLUMNS = MAIN_COLUMNS + INTERACTION_COLUMNS
_ELASTIC_NET = {
    "positive": True,
    "fit_intercept": False,
    "max_iter": 100000,
    "tol": 1e-8,
}
_NONLINEAR_PARAMETERS = {
    "learning_rate": 0.05,
    "max_iter": 300,
    "max_leaf_nodes": 15,
    "l2_regularization": 1.0,
    "min_samples_leaf": 20,
    "random_state": 20260819,
}
MIN_BAYESIAN_STANDARD_ERROR = math.sqrt(np.finfo(float).eps)


class BayesianInputError(ValueError):
    """Raised when Bayesian inputs cannot support stable inference."""


def _default_catalog() -> list[dict[str, Any]]:
    try:
        from five_formula_catalog import subsystem_catalog

        return subsystem_catalog()
    except ImportError:
        return []


def frozen_model_protocol() -> dict[str, Any]:
    """Return the immutable-by-copy five-formula modelling contract."""

    catalog = _default_catalog()
    return {
        "schema": "FIVE_FORMULA_FROZEN_MODEL_PROTOCOL_V1",
        "systems": list(SYSTEMS),
        "alpha_grid": list(ALPHA_GRID),
        "l1_ratio_grid": list(L1_RATIO_GRID),
        "elastic_net": dict(_ELASTIC_NET),
        "feature_columns": [str(row["key"]) for row in catalog],
        "system_by_feature": {
            str(row["key"]): str(row["formula"]) for row in catalog
        },
        "roles": {str(row["key"]): str(row["role"]) for row in catalog},
        "expected_directions": {
            str(row["key"]): str(row["expected_direction"]) for row in catalog
        },
        "date": "signal_date",
        "symbol": "symbol",
        "target_5d": "excess_return_5d",
        "target_10d": "excess_return_10d",
        "mae": "mae_5d",
        "drawdown": "max_drawdown_5d",
        "turnover": "top10_turnover",
        "top_k": 10,
        "fold_count": 5,
        "direction_conflict_tolerance": 1e-12,
        "coefficient_aggregation": "expanding_fold_median",
        "bayesian_estimator": "normal_normal_quadrature",
        "bayesian_prior_scales": [0.005, 0.01, 0.02],
        "bayesian_tau_grid": np.exp(
            np.linspace(math.log(1e-6), math.log(0.20), 81)
        ).tolist(),
        "nonlinear_comparator": dict(_NONLINEAR_PARAMETERS),
    }


def _require_frame(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError(f"{name}_must_be_nonempty_dataframe")
    return frame.copy(deep=True)


def _validate_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(protocol, Mapping):
        raise TypeError("protocol_must_be_mapping")
    result = copy.deepcopy(dict(protocol))
    required = {
        "feature_columns", "system_by_feature", "roles", "expected_directions",
        "target_5d", "target_10d", "mae", "drawdown", "turnover", "date",
    }
    missing = sorted(required - set(result))
    if missing:
        raise ValueError(f"protocol_missing:{','.join(missing)}")
    features = list(result["feature_columns"])
    if not features or len(features) != len(set(features)):
        raise ValueError("feature_columns_must_be_unique_nonempty")
    for field in ("system_by_feature", "roles", "expected_directions"):
        if set(result[field]) != set(features):
            raise ValueError(f"{field}_must_cover_feature_columns")
    if set(result["system_by_feature"].values()) - set(SYSTEMS):
        raise ValueError("unknown_system_in_protocol")
    return result


def _numeric_matrix(frame: pd.DataFrame, columns: Sequence[str]) -> np.ndarray:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"missing_columns:{','.join(missing)}")
    values = frame[list(columns)].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    if np.isinf(values).any():
        raise ValueError("feature_values_must_not_be_infinite")
    return values


def _percentile_vector(values: np.ndarray) -> np.ndarray:
    series = pd.Series(values, dtype=float)
    finite = series.notna()
    count = int(finite.sum())
    result = np.full(len(series), 0.5, dtype=float)
    if count <= 1:
        return result
    ranked = series[finite].rank(method="average")
    result[finite.to_numpy()] = ((ranked - 1.0) / (count - 1.0)).to_numpy(float)
    return np.clip(result, 0.0, 1.0)


def _oriented_percentiles(
    frame: pd.DataFrame, protocol: Mapping[str, Any]
) -> pd.DataFrame:
    features = list(protocol["feature_columns"])
    date_column = str(protocol["date"])
    if date_column not in frame:
        raise ValueError(f"missing_date_column:{date_column}")
    raw = _numeric_matrix(frame, features)
    result = pd.DataFrame(index=frame.index, columns=features, dtype=float)
    dates = frame[date_column].astype(str)
    for indexes in dates.groupby(dates, sort=True).groups.values():
        positions = frame.index.get_indexer(indexes)
        for column_index, feature in enumerate(features):
            ranked = _percentile_vector(raw[positions, column_index])
            direction = str(protocol["expected_directions"][feature])
            if direction == "lower_is_bullish":
                ranked = 1.0 - ranked
            result.loc[indexes, feature] = ranked
    return result.astype(float)


def _direction_demotions(
    train: pd.DataFrame,
    percentiles: pd.DataFrame,
    protocol: Mapping[str, Any],
) -> tuple[set[str], list[dict[str, str]]]:
    target = pd.to_numeric(train[str(protocol["target_5d"])], errors="coerce").to_numpy(float)
    demoted: set[str] = set()
    rows: list[dict[str, str]] = []
    tolerance = float(protocol.get("direction_conflict_tolerance", 1e-12))
    dates = train[str(protocol["date"])].astype(str)
    for feature in protocol["feature_columns"]:
        role = str(protocol["roles"][feature])
        if role != "predictive_candidate":
            demoted.add(feature)
            rows.append({"feature": feature, "reason": f"non_predictive_role:{role}"})
            continue
        informative = any(
            percentiles.loc[indexes, feature].nunique(dropna=True) > 1
            for indexes in dates.groupby(dates, sort=True).groups.values()
        )
        if not informative:
            demoted.add(feature)
            rows.append({"feature": feature, "reason": "uninformative"})
            continue
        statistic = spearmanr(percentiles[feature].to_numpy(float), target).statistic
        if math.isfinite(float(statistic)) and float(statistic) < -tolerance:
            demoted.add(feature)
            rows.append({"feature": feature, "reason": "direction_conflict"})
    return demoted, rows


def _new_elastic_net(alpha: float, l1_ratio: float) -> ElasticNet:
    return ElasticNet(alpha=alpha, l1_ratio=l1_ratio, selection="cyclic", **_ELASTIC_NET)


def _fit_coefficients(
    x: np.ndarray, y: np.ndarray, alpha: float, l1_ratio: float
) -> np.ndarray:
    if x.shape[1] == 0:
        return np.zeros(0, dtype=float)
    model = _new_elastic_net(alpha, l1_ratio)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(x, y)
    result = np.maximum(np.asarray(model.coef_, dtype=float), 0.0)
    result[np.abs(result) < 1e-15] = 0.0
    return result


def _max_drawdown_magnitude(returns: Sequence[float]) -> float:
    values = np.asarray(returns, dtype=float)
    if values.size == 0:
        return 0.0
    equity = np.cumprod(1.0 + values)
    peak = np.maximum.accumulate(equity)
    return float(max(0.0, -np.min(equity / peak - 1.0)))


def _metrics(
    frame: pd.DataFrame,
    score: np.ndarray,
    protocol: Mapping[str, Any],
) -> dict[str, float]:
    date_column = str(protocol["date"])
    symbol_column = str(protocol.get("symbol", "symbol"))
    y5_column = str(protocol["target_5d"])
    y10_column = str(protocol["target_10d"])
    work = pd.DataFrame(
        {
            "date": frame[date_column].astype(str).to_numpy(),
            "symbol": frame[symbol_column].astype(str).to_numpy()
            if symbol_column in frame else np.arange(len(frame)).astype(str),
            "y5": pd.to_numeric(frame[y5_column], errors="raise").to_numpy(float),
            "y10": pd.to_numeric(frame[y10_column], errors="raise").to_numpy(float),
            "score": np.asarray(score, dtype=float),
        }
    )
    if not np.isfinite(work[["y5", "y10", "score"]].to_numpy()).all():
        raise ValueError("targets_and_scores_must_be_finite")
    selected_returns: list[float] = []
    selected_sets: list[set[str]] = []
    top5: list[float] = []
    top10: list[float] = []
    ics: list[float] = []
    for _, group in work.groupby("date", sort=True):
        ranked = group.sort_values(["score", "symbol"], ascending=[False, True], kind="mergesort")
        chosen = ranked.head(min(int(protocol.get("top_k", 10)), len(ranked)))
        top5.append(float(chosen["y5"].mean()))
        top10.append(float(chosen["y10"].mean()))
        selected_returns.append(float(chosen["y5"].mean()))
        selected_sets.append(set(chosen["symbol"]))
        if group["score"].nunique() > 1 and group["y5"].nunique() > 1:
            value = spearmanr(group["score"], group["y5"]).statistic
            if math.isfinite(float(value)):
                ics.append(float(value))
    turnovers = [
        1.0 - len(left & right) / max(len(left), len(right), 1)
        for left, right in zip(selected_sets, selected_sets[1:])
    ]
    y5 = work["y5"].to_numpy(float)
    return {
        "top10_5d_net_excess": float(np.mean(top5)),
        "top10_10d_net_excess": float(np.mean(top10)),
        "ic": float(np.mean(ics)) if ics else 0.0,
        "mae_5d": float(np.mean(np.abs(y5 - work["score"].to_numpy(float)))),
        "drawdown_5d": _max_drawdown_magnitude(selected_returns),
        "turnover": float(np.mean(turnovers)) if turnovers else 0.0,
    }


def _candidate_search(
    train_x: np.ndarray,
    train_y: np.ndarray,
    validation_x: np.ndarray,
    validation_frame: pd.DataFrame,
    equal_prediction: np.ndarray,
    protocol: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, float]]:
    equal_metrics = _metrics(validation_frame, equal_prediction, protocol)
    candidates: list[dict[str, Any]] = []
    for alpha in protocol.get("alpha_grid", ALPHA_GRID):
        for ratio in protocol.get("l1_ratio_grid", L1_RATIO_GRID):
            coefficients = _fit_coefficients(train_x, train_y, float(alpha), float(ratio))
            prediction = validation_x @ coefficients
            metrics = _metrics(validation_frame, prediction, protocol)
            eligible = (
                metrics["top10_10d_net_excess"] > 0.0
                and metrics["mae_5d"] <= equal_metrics["mae_5d"] + 1e-12
                and metrics["drawdown_5d"] <= equal_metrics["drawdown_5d"] + 1e-12
            )
            candidates.append(
                {
                    "alpha": float(alpha),
                    "l1_ratio": float(ratio),
                    "eligible": bool(eligible),
                    "metrics": metrics,
                    "coefficients": coefficients,
                }
            )
    pool = [row for row in candidates if row["eligible"]] or candidates
    selected = max(
        pool,
        key=lambda row: (
            row["metrics"]["top10_5d_net_excess"],
            row["metrics"]["ic"],
            -row["metrics"]["turnover"],
            row["alpha"],
            row["l1_ratio"],
        ),
    )
    return selected, candidates, equal_metrics


def _expanding_median(
    x: np.ndarray,
    y: np.ndarray,
    dates: Sequence[str],
    *,
    alpha: float,
    l1_ratio: float,
    fold_count: int,
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    unique_dates = np.array(sorted(set(map(str, dates))))
    if unique_dates.size == 0:
        raise ValueError("expanding_dates_empty")
    starts = np.linspace(max(1, math.ceil(unique_dates.size / 2)), unique_dates.size, max(1, fold_count), dtype=int)
    cutoffs = sorted(set(int(value) for value in starts))
    coefficients: list[np.ndarray] = []
    folds: list[dict[str, Any]] = []
    date_values = np.asarray(list(map(str, dates)))
    for fold_index, cutoff in enumerate(cutoffs, start=1):
        included = unique_dates[:cutoff]
        mask = np.isin(date_values, included)
        fitted = _fit_coefficients(x[mask], y[mask], alpha, l1_ratio)
        coefficients.append(fitted)
        folds.append(
            {
                "fold": fold_index,
                "through_date": str(included[-1]),
                "observations": int(mask.sum()),
                "coefficients": fitted.tolist(),
            }
        )
    median = np.median(np.vstack(coefficients), axis=0)
    median[np.abs(median) < 1e-15] = 0.0
    return median, folds


def _system_score_matrix(
    percentiles: pd.DataFrame,
    features: Sequence[str],
    system_by_feature: Mapping[str, str],
    coefficients: Mapping[str, np.ndarray],
) -> pd.DataFrame:
    output: dict[str, np.ndarray] = {}
    feature_positions = {feature: index for index, feature in enumerate(features)}
    for system in SYSTEMS:
        owned = [feature for feature in features if system_by_feature[feature] == system]
        raw = coefficients[system]
        total = math.fsum(float(value) for value in raw)
        if total <= 0.0:
            output[system] = np.zeros(len(percentiles), dtype=float)
            continue
        positions = [feature_positions[feature] for feature in owned]
        output[system] = percentiles[owned].to_numpy(float) @ (raw[positions] / total)
    return pd.DataFrame(output, index=percentiles.index)


def compute_fusion_terms(
    system_scores: pd.DataFrame | Mapping[str, Any],
) -> pd.DataFrame | dict[str, float]:
    """Create five main effects, ten square-root resonances, and agreement."""

    scalar = isinstance(system_scores, Mapping)
    if scalar:
        missing = set(SYSTEMS) - set(system_scores)
        if missing:
            raise ValueError(f"missing_system_scores:{sorted(missing)}")
        frame = pd.DataFrame([{system: system_scores[system] for system in SYSTEMS}])
    elif isinstance(system_scores, pd.DataFrame):
        missing = set(SYSTEMS) - set(system_scores.columns)
        if missing:
            raise ValueError(f"missing_system_scores:{sorted(missing)}")
        frame = system_scores.loc[:, SYSTEMS].copy()
    else:
        raise TypeError("system_scores_must_be_dataframe_or_mapping")
    values = frame.apply(pd.to_numeric, errors="raise").astype(float)
    if not np.isfinite(values.to_numpy()).all() or ((values < 0) | (values > 1)).any().any():
        raise ValueError("system_scores_must_be_finite_in_0_1")
    output = values.copy()
    for left, right in itertools.combinations(SYSTEMS, 2):
        output[f"sqrt_resonance::{left}|{right}"] = np.sqrt(values[left] * values[right])
    output["agreement"] = 1.0 - np.clip(
        2.0 * values.to_numpy(float).std(axis=1, ddof=0), 0.0, 1.0
    )
    output = output.loc[:, FUSION_COLUMNS]
    if scalar:
        return {key: float(output.iloc[0][key]) for key in FUSION_COLUMNS}
    return output


def _candidate_public(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "alpha": float(row["alpha"]),
        "l1_ratio": float(row["l1_ratio"]),
        "eligible": bool(row["eligible"]),
        "metrics": dict(row["metrics"]),
        "nonzero_coefficients": int(np.count_nonzero(row["coefficients"])),
    }


def fit_hierarchical_candidate(
    train_frame: pd.DataFrame,
    validation_frame: pd.DataFrame,
    *,
    protocol: Mapping[str, Any],
    catalog: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Fit frozen positive two-level ElasticNet models without weight floors."""

    protocol = _validate_protocol(protocol)
    train = _require_frame(train_frame, "train_frame")
    validation = _require_frame(validation_frame, "validation_frame")
    features = list(protocol["feature_columns"])
    required = set(features) | {
        str(protocol["date"]), str(protocol["target_5d"]), str(protocol["target_10d"])
    }
    for name, frame in (("train", train), ("validation", validation)):
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"{name}_missing_columns:{','.join(missing)}")
    if catalog is not None:
        catalog_keys = [str(row["key"]) for row in catalog]
        if catalog_keys != features:
            raise ValueError("catalog_feature_order_mismatch")

    train_p = _oriented_percentiles(train, protocol)
    validation_p = _oriented_percentiles(validation, protocol)
    demoted, demotions = _direction_demotions(train, train_p, protocol)
    y_train = pd.to_numeric(train[str(protocol["target_5d"])], errors="raise").to_numpy(float)
    all_frame = pd.concat([train, validation], ignore_index=True)
    all_p = pd.concat([train_p, validation_p], ignore_index=True)
    y_all = pd.to_numeric(all_frame[str(protocol["target_5d"])], errors="raise").to_numpy(float)
    raw_by_system: dict[str, np.ndarray] = {}
    system_rejections: list[dict[str, Any]] = []
    folds: dict[str, Any] = {"systems": {}, "fusion": []}
    grid_payload: dict[str, Any] = {"specifications": [], "systems": {}, "fusion": []}
    for alpha in protocol.get("alpha_grid", ALPHA_GRID):
        for ratio in protocol.get("l1_ratio_grid", L1_RATIO_GRID):
            grid_payload["specifications"].append({"alpha": float(alpha), "l1_ratio": float(ratio)})

    feature_positions = {feature: index for index, feature in enumerate(features)}
    for system in SYSTEMS:
        owned = [feature for feature in features if protocol["system_by_feature"][feature] == system]
        active = [feature for feature in owned if feature not in demoted]
        full = np.zeros(len(features), dtype=float)
        if not active:
            raw_by_system[system] = full
            folds["systems"][system] = []
            grid_payload["systems"][system] = []
            continue
        x_train = train_p[active].to_numpy(float)
        x_validation = validation_p[active].to_numpy(float)
        equal = x_validation.mean(axis=1)
        selected, candidates, _ = _candidate_search(
            x_train, y_train, x_validation, validation, equal, protocol
        )
        grid_payload["systems"][system] = [_candidate_public(row) for row in candidates]
        eligible_count = sum(bool(row["eligible"]) for row in candidates)
        if eligible_count == 0:
            raw_by_system[system] = full
            folds["systems"][system] = []
            system_rejections.append(
                {
                    "system": system,
                    "reason": "no_validation_eligible_candidate",
                    "candidate_count": len(candidates),
                    "eligible_candidate_count": 0,
                }
            )
            continue
        median, system_folds = _expanding_median(
            all_p[active].to_numpy(float),
            y_all,
            all_frame[str(protocol["date"])].astype(str).tolist(),
            alpha=float(selected["alpha"]),
            l1_ratio=float(selected["l1_ratio"]),
            fold_count=int(protocol.get("fold_count", 5)),
        )
        for feature, coefficient in zip(active, median, strict=True):
            full[feature_positions[feature]] = float(coefficient)
        raw_by_system[system] = full
        folds["systems"][system] = system_folds

    if system_rejections:
        node_weights: dict[str, float] = dict.fromkeys(features, 0.0)
        for system in SYSTEMS:
            values = raw_by_system[system]
            total = math.fsum(float(value) for value in values)
            if total > 0.0:
                for feature, value in zip(features, values, strict=True):
                    if protocol["system_by_feature"][feature] == system:
                        node_weights[feature] = float(value / total * 100.0)
        return {
            "schema": "FIVE_FORMULA_HIERARCHICAL_MODEL_V1",
            "status": "REJECTED",
            "system_weights": dict.fromkeys(SYSTEMS, 0.0),
            "node_weights": node_weights,
            "fusion_weights": dict.fromkeys(FUSION_COLUMNS, 0.0),
            "interaction_weights": dict.fromkeys(INTERACTION_COLUMNS, 0.0),
            "demotions": demotions,
            "folds": folds,
            "candidate_grid": grid_payload,
            "rejection_reasons": [
                f"system_validation_constraints_failed:{row['system']}"
                for row in system_rejections
            ],
            "system_rejections": system_rejections,
            "feature_columns": features,
            "system_by_feature": dict(protocol["system_by_feature"]),
            "roles": dict(protocol["roles"]),
            "expected_directions": dict(protocol["expected_directions"]),
            "selected": {"fusion": None},
        }

    train_systems = _system_score_matrix(train_p, features, protocol["system_by_feature"], raw_by_system)
    validation_systems = _system_score_matrix(validation_p, features, protocol["system_by_feature"], raw_by_system)
    all_systems = _system_score_matrix(all_p, features, protocol["system_by_feature"], raw_by_system)
    train_fusion = compute_fusion_terms(train_systems)
    validation_fusion = compute_fusion_terms(validation_systems)
    all_fusion = compute_fusion_terms(all_systems)
    assert isinstance(train_fusion, pd.DataFrame)
    assert isinstance(validation_fusion, pd.DataFrame)
    assert isinstance(all_fusion, pd.DataFrame)
    selected_fusion, fusion_candidates, _ = _candidate_search(
        train_fusion.to_numpy(float),
        y_train,
        validation_fusion.to_numpy(float),
        validation,
        validation_systems.mean(axis=1).to_numpy(float),
        protocol,
    )
    fusion_raw, fusion_folds = _expanding_median(
        all_fusion.to_numpy(float),
        y_all,
        all_frame[str(protocol["date"])].astype(str).tolist(),
        alpha=float(selected_fusion["alpha"]),
        l1_ratio=float(selected_fusion["l1_ratio"]),
        fold_count=int(protocol.get("fold_count", 5)),
    )
    folds["fusion"] = fusion_folds
    grid_payload["fusion"] = [_candidate_public(row) for row in fusion_candidates]

    node_weights: dict[str, float] = dict.fromkeys(features, 0.0)
    for system in SYSTEMS:
        values = raw_by_system[system]
        total = math.fsum(float(value) for value in values)
        if total > 0.0:
            for feature, value in zip(features, values, strict=True):
                if protocol["system_by_feature"][feature] == system:
                    node_weights[feature] = float(value / total * 100.0)
    main_raw = fusion_raw[: len(SYSTEMS)]
    base = math.fsum(float(value) for value in main_raw)
    fusion_total = math.fsum(float(value) for value in fusion_raw)
    reasons: list[str] = []
    if base <= 0.0:
        reasons.append("fusion_main_base_zero")
    if fusion_total <= 0.0:
        reasons.append("fusion_all_sixteen_zero")
    if not selected_fusion["eligible"]:
        reasons.append("fusion_validation_constraints_failed")
    system_weights = {
        system: (float(main_raw[index] / base * 100.0) if base > 0.0 else 0.0)
        for index, system in enumerate(SYSTEMS)
    }
    fusion_weights = {
        key: (float(fusion_raw[index] / fusion_total * 100.0) if fusion_total > 0.0 else 0.0)
        for index, key in enumerate(FUSION_COLUMNS)
    }
    interaction_weights = {key: fusion_weights[key] for key in INTERACTION_COLUMNS}
    return {
        "schema": "FIVE_FORMULA_HIERARCHICAL_MODEL_V1",
        "status": "PASS" if not reasons else "REJECTED",
        "system_weights": system_weights,
        "node_weights": node_weights,
        "fusion_weights": fusion_weights,
        "interaction_weights": interaction_weights,
        "demotions": demotions,
        "folds": folds,
        "candidate_grid": grid_payload,
        "rejection_reasons": reasons,
        "system_rejections": [],
        "feature_columns": features,
        "system_by_feature": dict(protocol["system_by_feature"]),
        "roles": dict(protocol["roles"]),
        "expected_directions": dict(protocol["expected_directions"]),
        "selected": {
            "fusion": {"alpha": selected_fusion["alpha"], "l1_ratio": selected_fusion["l1_ratio"]},
        },
    }


def score_hierarchical_candidate(
    model: Mapping[str, Any], node_percentiles: Mapping[str, Any]
) -> dict[str, Any]:
    """Score one stock and expose an exactly reconstructable 51+11 ledger."""

    if not isinstance(model, Mapping) or not isinstance(node_percentiles, Mapping):
        raise TypeError("model_and_node_percentiles_must_be_mappings")
    status = model.get("status")
    if status not in {"PASS", "PREDICTIVE_PASS"}:
        raise ValueError(f"model_status_not_scoreable:{status}")
    system_weights = model.get("system_weights")
    if not isinstance(system_weights, Mapping) or set(system_weights) != set(SYSTEMS):
        raise ValueError("system_weights_must_cover_five_systems")
    if math.fsum(abs(float(system_weights[system])) for system in SYSTEMS) <= 0.0:
        raise ValueError("system_weights_all_zero")
    fusion_weights = model.get("fusion_weights")
    if not isinstance(fusion_weights, Mapping) or not set(FUSION_COLUMNS) <= set(fusion_weights):
        raise ValueError("fusion_weights_must_cover_sixteen_terms")
    if math.fsum(abs(float(fusion_weights[system])) for system in SYSTEMS) <= 0.0:
        raise ValueError("fusion_main_base_all_zero")
    features = list(model["feature_columns"])
    if set(node_percentiles) != set(features):
        raise ValueError("node_percentiles_must_exactly_cover_features")
    values: dict[str, float] = {}
    for feature in features:
        value = float(node_percentiles[feature])
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"node_percentile_out_of_range:{feature}")
        values[feature] = value
    system_scores: dict[str, float] = {}
    for system in SYSTEMS:
        owned = [feature for feature in features if model["system_by_feature"][feature] == system]
        system_scores[system] = math.fsum(
            values[feature] * float(model["node_weights"][feature]) / 100.0
            for feature in owned
        )
    fusion_terms = compute_fusion_terms(system_scores)
    assert isinstance(fusion_terms, dict)
    if max(system_scores.values(), default=0.0) <= 0.0:
        fusion_terms["agreement"] = 0.0
    latent = []
    for feature in features:
        system = str(model["system_by_feature"][feature])
        contribution = (
            values[feature]
            * float(model["node_weights"][feature]) / 100.0
            * float(model["fusion_weights"][system])
        )
        latent.append(
            {
                "feature": feature,
                "system": system,
                "contribution": float(contribution),
            }
        )
    interactions = [
        {
            "term": key,
            "contribution": float(fusion_terms[key] * float(model["fusion_weights"][key])),
        }
        for key in INTERACTION_COLUMNS
    ]
    direct = math.fsum(
        float(fusion_terms[key]) * float(model["fusion_weights"][key])
        for key in FUSION_COLUMNS
    )
    reconstructed = math.fsum(row["contribution"] for row in latent) + math.fsum(
        row["contribution"] for row in interactions
    )
    error = abs(direct - reconstructed)
    if error > 1e-9:
        raise ValueError(f"contribution_reconstruction_failed:{error}")
    return {
        "total_score": float(min(100.0, max(0.0, direct))),
        "system_scores": system_scores,
        "fusion_terms": fusion_terms,
        "latent_contributions": latent,
        "interaction_contributions": interactions,
        "reconstruction_error": float(error),
    }


def _feature_summaries(frame: pd.DataFrame) -> dict[str, tuple[float, float, int]]:
    output: dict[str, tuple[float, float, int]] = {}
    for feature, group in frame.groupby("feature", sort=True):
        effects = group["effect"].to_numpy(float)
        errors = group["standard_error"].to_numpy(float)
        precision = 1.0 / np.square(errors)
        output[str(feature)] = (
            float(np.dot(precision, effects) / precision.sum()),
            float(math.sqrt(1.0 / precision.sum())),
            len(group),
        )
    return output


def _system_hyperposterior(
    summaries: Sequence[tuple[float, float]], prior_scale: float, tau_grid: np.ndarray
) -> list[dict[str, float]]:
    means = np.array([item[0] for item in summaries], dtype=float)
    errors = np.array([item[1] for item in summaries], dtype=float)
    log_evidence: list[float] = []
    rows: list[dict[str, float]] = []
    for tau in tau_grid:
        variances = np.square(errors) + tau * tau
        precision = 1.0 / (prior_scale * prior_scale) + float(np.sum(1.0 / variances))
        mu_sd = math.sqrt(1.0 / precision)
        mu_mean = mu_sd * mu_sd * float(np.sum(means / variances))

        def log_integrand(mu: float) -> float:
            return float(norm.logpdf(mu, 0.0, prior_scale) + np.sum(norm.logpdf(means, mu, np.sqrt(variances))))

        anchor = log_integrand(mu_mean)
        bound = max(0.25, abs(mu_mean) + 12.0 * max(mu_sd, prior_scale, float(tau)))
        integral, _ = quad(
            lambda mu: math.exp(log_integrand(mu) - anchor),
            -bound,
            bound,
            epsabs=1e-11,
            epsrel=1e-9,
            limit=200,
        )
        log_evidence.append(anchor + math.log(max(integral, np.finfo(float).tiny)))
        rows.append({"tau": float(tau), "mu_mean": mu_mean, "mu_sd": mu_sd})
    weights = np.exp(np.asarray(log_evidence) - logsumexp(log_evidence))
    for row, weight in zip(rows, weights, strict=True):
        row["weight"] = float(weight)
    return rows


def _feature_posterior(
    summary: tuple[float, float, int], hyper: Sequence[Mapping[str, float]]
) -> dict[str, float]:
    observed, observed_se, _ = summary
    components: list[tuple[float, float, float]] = []
    probability = 0.0
    for row in hyper:
        tau = float(row["tau"])
        mu_mean = float(row["mu_mean"])
        mu_var = float(row["mu_sd"]) ** 2
        weight = float(row["weight"])
        theta_var_cond = 1.0 / (1.0 / (observed_se * observed_se) + 1.0 / (tau * tau))
        coefficient = theta_var_cond / (tau * tau)
        theta_mean = theta_var_cond * (
            observed / (observed_se * observed_se) + mu_mean / (tau * tau)
        )
        theta_var = theta_var_cond + coefficient * coefficient * mu_var
        theta_sd = math.sqrt(max(theta_var, np.finfo(float).tiny))
        components.append((weight, theta_mean, theta_sd))
        probability += weight * float(norm.cdf(theta_mean / theta_sd))
    mean = math.fsum(weight * center for weight, center, _ in components)
    variance = math.fsum(
        weight * (spread * spread + center * center)
        for weight, center, spread in components
    ) - mean * mean
    span = max(0.5, abs(mean) + 12.0 * math.sqrt(max(variance, 1e-12)))

    def mixture_cdf(value: float) -> float:
        return math.fsum(
            weight * float(norm.cdf((value - center) / spread))
            for weight, center, spread in components
        )

    lower = brentq(lambda value: mixture_cdf(value) - 0.025, -span, span)
    upper = brentq(lambda value: mixture_cdf(value) - 0.975, -span, span)
    return {
        "posterior_mean": float(mean),
        "ci95_lower": float(lower),
        "ci95_upper": float(upper),
        "probability_positive": float(probability),
    }


def bayesian_hierarchical_review(
    fold_effects: pd.DataFrame | Sequence[Mapping[str, Any]],
    *,
    system_by_feature: Mapping[str, str],
    prior_scales: Sequence[float] = (0.005, 0.01, 0.02),
) -> dict[str, Any]:
    """Review rolling OOS effects with a two-level normal-normal hierarchy."""

    frame = pd.DataFrame(fold_effects).copy()
    required = {"feature", "effect", "standard_error"}
    if frame.empty or not required <= set(frame.columns):
        raise ValueError("fold_effects_missing_required_columns")
    frame["feature"] = frame["feature"].astype(str)
    frame["effect"] = pd.to_numeric(frame["effect"], errors="raise").astype(float)
    frame["standard_error"] = pd.to_numeric(frame["standard_error"], errors="raise").astype(float)
    if not np.isfinite(frame[["effect", "standard_error"]].to_numpy()).all() or (frame["standard_error"] <= 0).any():
        raise ValueError("fold_effects_must_be_finite_with_positive_standard_error")
    if (frame["standard_error"] < MIN_BAYESIAN_STANDARD_ERROR).any():
        minimum = float(frame["standard_error"].min())
        raise BayesianInputError(
            "standard_error_below_numerical_floor:"
            f"minimum={minimum:.17g}:floor={MIN_BAYESIAN_STANDARD_ERROR:.17g}"
        )
    unknown = set(frame["feature"]) - set(system_by_feature)
    if unknown:
        raise ValueError(f"feature_system_binding_missing:{sorted(unknown)}")
    scales = [float(value) for value in prior_scales]
    if not scales or any(not math.isfinite(value) or value <= 0 for value in scales):
        raise ValueError("prior_scales_must_be_positive_finite")
    summaries = _feature_summaries(frame)
    tau_grid = np.exp(np.linspace(math.log(1e-6), math.log(0.20), 81))
    sensitivity_by_feature: dict[str, list[dict[str, float]]] = {
        feature: [] for feature in summaries
    }
    for scale in scales:
        for system in SYSTEMS:
            owned = [
                feature for feature in summaries if system_by_feature[feature] == system
            ]
            if not owned:
                continue
            hyper = _system_hyperposterior(
                [(summaries[feature][0], summaries[feature][1]) for feature in owned],
                scale,
                tau_grid,
            )
            for feature in owned:
                posterior = _feature_posterior(summaries[feature], hyper)
                sensitivity_by_feature[feature].append(
                    {"prior_scale": scale, **posterior}
                )
    default_scale = min(scales, key=lambda value: abs(value - 0.01))
    rows = []
    rejected: list[str] = []
    for feature in sorted(summaries):
        sensitivity = sensitivity_by_feature[feature]
        primary = next(row for row in sensitivity if row["prior_scale"] == default_scale)
        accepted = all(row["probability_positive"] >= 0.90 for row in sensitivity)
        if not accepted:
            rejected.append(feature)
        rows.append(
            {
                "feature": feature,
                "system": system_by_feature[feature],
                "fold_count": summaries[feature][2],
                "posterior_mean": primary["posterior_mean"],
                "ci95_lower": primary["ci95_lower"],
                "ci95_upper": primary["ci95_upper"],
                "probability_positive": primary["probability_positive"],
                "accepted_all_prior_scales": accepted,
                "sensitivity": sensitivity,
            }
        )
    return {
        "schema": "FIVE_FORMULA_BAYESIAN_REVIEW_V1",
        "method": "normal_normal_adaptive_quadrature",
        "status": "PASS" if not rejected else "REJECTED",
        "prior_scales": scales,
        "tau_grid": tau_grid.tolist(),
        "features": rows,
        "rejected_features": rejected,
    }


def fit_nonlinear_comparator(
    train_frame: pd.DataFrame,
    validation_frame: pd.DataFrame,
    *,
    feature_columns: Sequence[str],
    target_column: str,
) -> dict[str, Any]:
    """Fit the frozen nonlinear benchmark; it never emits deployable weights."""

    train = _require_frame(train_frame, "train_frame")
    validation = _require_frame(validation_frame, "validation_frame")
    features = list(feature_columns)
    if not features:
        raise ValueError("feature_columns_must_not_be_empty")
    x_train = _numeric_matrix(train, features)
    x_validation = _numeric_matrix(validation, features)
    y_train = pd.to_numeric(train[target_column], errors="raise").to_numpy(float)
    y_validation = pd.to_numeric(validation[target_column], errors="raise").to_numpy(float)
    model = HistGradientBoostingRegressor(**_NONLINEAR_PARAMETERS)
    model.fit(x_train, y_train)
    prediction = model.predict(x_validation)
    return {
        "schema": "FIVE_FORMULA_NONLINEAR_COMPARATOR_V1",
        "role": "comparator_only",
        "estimator": "HistGradientBoostingRegressor",
        "parameters": dict(_NONLINEAR_PARAMETERS),
        "validation": {
            "observations": int(len(validation)),
            "mae": float(np.mean(np.abs(y_validation - prediction))),
            "rmse": float(math.sqrt(np.mean(np.square(y_validation - prediction)))),
            "prediction_checksum": float(math.fsum(float(value) for value in prediction)),
        },
    }
