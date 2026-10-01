#!/usr/bin/env python3
"""Build top-decile future activity labels from post-cutoff observations."""
from __future__ import annotations

import math
import statistics
from collections import defaultdict
from datetime import date


LABEL_WEIGHTS = {
    "excess_return": 0.30,
    "breadth_improvement": 0.20,
    "activity_expansion": 0.20,
    "limit_leader_continuity": 0.20,
    "persistence": 0.10,
}
HORIZONS = {"H1": (1, 3), "H2": (4, 7), "H3": (8, 10)}


def _as_date(value: date | str) -> date:
    return value if isinstance(value, date) else date.fromisoformat(value)


def _compound(values: list[float]) -> float:
    product = 1.0
    for value in values:
        product *= 1.0 + value
    return product - 1.0


def _stable_percentiles(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    if len(ordered) == 1:
        return {ordered[0][0]: 1.0}
    groups: dict[float, list[int]] = defaultdict(list)
    for index, (_, value) in enumerate(ordered):
        groups[value].append(index)
    result: dict[str, float] = {}
    for value, indexes in groups.items():
        percentile = statistics.fmean(indexes) / (len(ordered) - 1)
        for sector, candidate in ordered:
            if candidate == value:
                result[sector] = percentile
    return result


def build_future_activity_labels(forecast_date: date, observations: list[dict]) -> list[dict]:
    by_sector: dict[str, dict[date, dict]] = defaultdict(dict)
    for row in observations:
        trade_day = _as_date(row["trade_date"])
        if trade_day <= forecast_date:
            continue
        by_sector[str(row["sector"])][trade_day] = row
    if not by_sector:
        raise ValueError("future_label_observations_missing")
    trading_days = sorted({trade_day for rows in by_sector.values() for trade_day in rows})
    if len(trading_days) < HORIZONS["H3"][1]:
        raise ValueError("future_label_requires_ten_trading_days")

    output: list[dict] = []
    for horizon, (start, end) in HORIZONS.items():
        window_dates = trading_days[start - 1 : end]
        raw_by_sector: dict[str, dict[str, float]] = {}
        for sector, rows in by_sector.items():
            missing = [trade_day for trade_day in window_dates if trade_day not in rows]
            if missing:
                raise ValueError(
                    f"future_label_sector_dates_missing:{sector}:{horizon}:"
                    + ",".join(value.isoformat() for value in missing)
                )
            window = [rows[trade_day] for trade_day in window_dates]
            sector_return = _compound([float(row["sector_return"]) for row in window])
            market_return = _compound([float(row["market_return"]) for row in window])
            raw_by_sector[sector] = {
                "excess_return": sector_return - market_return,
                "breadth_improvement": statistics.fmean(
                    float(row["breadth"]) - float(row["baseline_breadth"])
                    for row in window
                ),
                "activity_expansion": statistics.fmean(
                    float(row["activity_expansion"]) for row in window
                ),
                "limit_leader_continuity": statistics.fmean(
                    float(row["limit_leader_continuity"]) for row in window
                ),
                "persistence": statistics.fmean(float(row["persistence"]) for row in window),
            }
        component_percentiles = {
            component: _stable_percentiles(
                {sector: values[component] for sector, values in raw_by_sector.items()}
            )
            for component in LABEL_WEIGHTS
        }
        scores = {
            sector: sum(
                LABEL_WEIGHTS[component] * component_percentiles[component][sector]
                for component in LABEL_WEIGHTS
            )
            for sector in raw_by_sector
        }
        score_percentiles = _stable_percentiles(scores)
        positive_count = max(1, math.ceil(len(scores) * 0.10))
        positives = {
            sector
            for sector, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[
                :positive_count
            ]
        }
        for sector in sorted(raw_by_sector):
            output.append(
                {
                    "forecast_date": forecast_date.isoformat(),
                    "sector": sector,
                    "horizon": horizon,
                    "window_dates": [value.isoformat() for value in window_dates],
                    **raw_by_sector[sector],
                    "component_percentiles": {
                        component: component_percentiles[component][sector]
                        for component in LABEL_WEIGHTS
                    },
                    "future_activity_score": scores[sector],
                    "future_activity_percentile": score_percentiles[sector],
                    "is_top_decile": sector in positives,
                }
            )
    return output
