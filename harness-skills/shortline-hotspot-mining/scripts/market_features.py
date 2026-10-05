#!/usr/bin/env python3
"""Derive auditable sector features from a frozen TDX snapshot."""
from __future__ import annotations

import math
import statistics
from datetime import date
from pathlib import Path
from typing import Iterable

from point_in_time_snapshot import DailyBar, SnapshotBlocked, read_tdx_day_file, sha256_file


LOOKBACKS = (1, 3, 5, 10, 20)


def _mean(values: Iterable[float]) -> float | None:
    materialized = [float(value) for value in values if math.isfinite(float(value))]
    return statistics.fmean(materialized) if materialized else None


def _member_return(bars: list[DailyBar], lookback: int) -> float | None:
    if len(bars) <= lookback or bars[-lookback - 1].close <= 0:
        return None
    return bars[-1].close / bars[-lookback - 1].close - 1.0


def _daily_returns(bars: list[DailyBar], count: int) -> list[float]:
    tail = bars[-(count + 1) :]
    return [
        right.close / left.close - 1.0
        for left, right in zip(tail, tail[1:])
        if left.close > 0
    ]


def _market_limit_threshold(code: str) -> float:
    if code.startswith(("300", "301", "688")):
        return 0.195
    if code.startswith(("4", "8")):
        return 0.295
    return 0.095


def _load_member_bars(source: dict, cutoff: date) -> list[DailyBar]:
    path = Path(source["path"])
    if sha256_file(path) != source["sha256"]:
        raise SnapshotBlocked(f"snapshot_source_hash_mismatch:{path}")
    bars = read_tdx_day_file(path, cutoff_date=cutoff)
    if not bars or bars[-1].trade_date != cutoff:
        raise SnapshotBlocked(f"feature_source_date_mismatch:{path}:{cutoff.isoformat()}")
    return bars


def _sector_row(sector: dict, cutoff: date, snapshot_id: str) -> dict:
    histories = {
        source["code"]: _load_member_bars(source, cutoff)
        for source in sector.get("current_member_sources", [])
    }
    returns = {
        lookback: _mean(
            value
            for bars in histories.values()
            if (value := _member_return(bars, lookback)) is not None
        )
        for lookback in LOOKBACKS
    }
    one_day_by_code = {
        code: value
        for code, bars in histories.items()
        if (value := _member_return(bars, 1)) is not None
    }
    breadth = (
        sum(value > 0 for value in one_day_by_code.values()) / len(one_day_by_code)
        if one_day_by_code
        else None
    )
    five_day_by_code = {
        code: value
        for code, bars in histories.items()
        if (value := _member_return(bars, min(5, len(bars) - 1))) is not None
    }
    prior_breadth = (
        sum(value > 0 for value in five_day_by_code.values()) / len(five_day_by_code)
        if five_day_by_code
        else None
    )
    breadth_change = (
        breadth - prior_breadth
        if breadth is not None and prior_breadth is not None
        else None
    )
    amount_ratios: list[float] = []
    for bars in histories.values():
        prior_amounts = [bar.amount for bar in bars[-21:-1] if bar.amount > 0]
        if bars[-1].amount > 0 and prior_amounts:
            amount_ratios.append(bars[-1].amount / statistics.fmean(prior_amounts))
    amount_ratio = _mean(amount_ratios)
    limit_up_density = (
        sum(
            value >= _market_limit_threshold(code)
            for code, value in one_day_by_code.items()
        )
        / len(one_day_by_code)
        if one_day_by_code
        else None
    )
    positive = [value for value in one_day_by_code.values() if value > 0]
    leader_concentration = max(positive) / sum(positive) if positive else None

    sector_daily_returns: list[float] = []
    max_available = max((len(bars) for bars in histories.values()), default=0)
    for offset in range(min(10, max(0, max_available - 1)), 0, -1):
        values = []
        for bars in histories.values():
            if len(bars) > offset and bars[-offset - 1].close > 0:
                values.append(bars[-offset].close / bars[-offset - 1].close - 1.0)
        value = _mean(values)
        if value is not None:
            sector_daily_returns.append(value)
    persistence = (
        sum(value > 0 for value in sector_daily_returns[-5:])
        / len(sector_daily_returns[-5:])
        if sector_daily_returns
        else None
    )
    volatility = (
        statistics.pstdev(sector_daily_returns)
        if len(sector_daily_returns) >= 2
        else 0.0 if sector_daily_returns else None
    )
    trend_slope = (
        _mean(
            (index + 1) * value
            for index, value in enumerate(sector_daily_returns)
        )
        if sector_daily_returns
        else None
    )
    drawdowns: list[float] = []
    for bars in histories.values():
        closes = [bar.close for bar in bars[-20:] if bar.close > 0]
        if closes:
            drawdowns.append(closes[-1] / max(closes) - 1.0)
    drawdown = _mean(drawdowns)

    coverage_ratio = float(sector.get("coverage_ratio", 0.0))
    rank_eligible = bool(
        sector.get("eligible_for_high_confidence", False)
        and histories
        and returns[1] is not None
    )
    raw_score = None
    if rank_eligible:
        raw_score = (
            0.18 * (returns[1] or 0.0)
            + 0.18 * (returns[3] or 0.0)
            + 0.10 * (returns[5] or 0.0)
            + 0.12 * ((breadth or 0.0) - 0.5)
            + 0.10 * (breadth_change or 0.0)
            + 0.10 * math.log(max(amount_ratio or 1.0, 0.01))
            + 0.10 * (limit_up_density or 0.0)
            + 0.07 * ((persistence or 0.0) - 0.5)
            - 0.03 * (leader_concentration or 0.0)
            - 0.05 * (volatility or 0.0)
            + 0.05 * (drawdown or 0.0)
        )
    return {
        "snapshot_id": snapshot_id,
        "sector": sector["sector"],
        "feature_cutoff_date": cutoff.isoformat(),
        **{f"return_{lookback}d": returns[lookback] for lookback in LOOKBACKS},
        "breadth": breadth,
        "breadth_change": breadth_change,
        "amount_ratio": amount_ratio,
        "limit_up_density": limit_up_density,
        "leader_concentration": leader_concentration,
        "persistence": persistence,
        "trend_slope": trend_slope,
        "volatility": volatility,
        "drawdown": drawdown,
        "coverage_ratio": coverage_ratio,
        "coverage_missing": int(not histories),
        "rank_eligible": rank_eligible,
        "raw_rank_score": raw_score,
        "rank_percentile": None,
    }


def _assign_stable_percentiles(rows: list[dict]) -> None:
    eligible = [row for row in rows if row["raw_rank_score"] is not None]
    eligible.sort(key=lambda row: (row["raw_rank_score"], row["sector"]))
    if not eligible:
        return
    if len(eligible) == 1:
        eligible[0]["rank_percentile"] = 1.0
        return
    groups: dict[float, list[int]] = {}
    for index, row in enumerate(eligible):
        groups.setdefault(float(row["raw_rank_score"]), []).append(index)
    for indexes in groups.values():
        percentile = statistics.fmean(indexes) / (len(eligible) - 1)
        for index in indexes:
            eligible[index]["rank_percentile"] = percentile


def build_market_features(snapshot: dict) -> dict:
    snapshot_id = str(snapshot.get("snapshot_id", ""))
    if not snapshot_id:
        raise SnapshotBlocked("feature_snapshot_id_missing")
    try:
        cutoff = date.fromisoformat(str(snapshot["resolved_trade_date"]))
    except (KeyError, ValueError) as exc:
        raise SnapshotBlocked("feature_cutoff_date_invalid") from exc
    rows = [_sector_row(sector, cutoff, snapshot_id) for sector in snapshot.get("sectors", [])]
    _assign_stable_percentiles(rows)
    for lookback in LOOKBACKS:
        values = [row[f"return_{lookback}d"] for row in rows if row[f"return_{lookback}d"] is not None]
        market_return = statistics.fmean(values) if values else None
        for row in rows:
            value = row[f"return_{lookback}d"]
            row[f"relative_return_{lookback}d"] = (
                value - market_return
                if value is not None and market_return is not None
                else None
            )
            row[f"return_{lookback}d_missing"] = int(value is None)
    return {
        "schema": "SHORTLINE_MARKET_FEATURE_SNAPSHOT_V1",
        "snapshot_id": snapshot_id,
        "feature_cutoff_date": cutoff.isoformat(),
        "sectors": rows,
    }
