#!/usr/bin/env python3
"""Rank stock leaders only inside the current forecast candidate sectors."""
from __future__ import annotations

import math
import statistics
from datetime import date
from pathlib import Path
from typing import Sequence

from point_in_time_snapshot import read_tdx_day_file, sha256_file


class LeaderBlocked(RuntimeError):
    """Raised when forecast-to-member lineage cannot be proven."""


def _sigmoid(value: float) -> float:
    bounded = max(-30.0, min(30.0, value))
    return 1.0 / (1.0 + math.exp(-bounded))


def _safe(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _source_features(source: dict, cutoff: date | None) -> dict:
    if "path" not in source or "sha256" not in source or cutoff is None:
        return {
            **source,
            "code": str(source.get("code", "")),
            "relative_strength": _safe(source.get("relative_strength")),
            "amount_ratio": _safe(source.get("amount_ratio"), 1.0),
            "limit_up_continuity": _safe(source.get("limit_up_continuity")),
            "persistence": _safe(source.get("persistence"), 0.5),
            "volatility": _safe(source.get("volatility")),
            "drawdown": _safe(source.get("drawdown")),
        }
    path = Path(source["path"])
    if sha256_file(path) != source["sha256"]:
        raise LeaderBlocked(f"leader_source_hash_mismatch:{path}")
    bars = read_tdx_day_file(path, cutoff_date=cutoff)
    if not bars or bars[-1].trade_date != cutoff:
        raise LeaderBlocked(f"leader_source_date_mismatch:{path}")
    daily_returns = [
        right.close / left.close - 1.0
        for left, right in zip(bars[-11:-1], bars[-10:])
        if left.close > 0
    ]
    one_day = daily_returns[-1] if daily_returns else 0.0
    prior_amounts = [bar.amount for bar in bars[-21:-1] if bar.amount > 0]
    amount_ratio = (
        bars[-1].amount / statistics.fmean(prior_amounts)
        if prior_amounts and bars[-1].amount > 0
        else 1.0
    )
    limit_threshold = 0.195 if source["code"].startswith(("300", "301", "688")) else 0.095
    limit_streak = 0
    for value in reversed(daily_returns):
        if value >= limit_threshold:
            limit_streak += 1
        else:
            break
    closes = [bar.close for bar in bars[-20:] if bar.close > 0]
    return {
        **source,
        "code": str(source["code"]),
        "relative_strength": one_day,
        "amount_ratio": amount_ratio,
        "limit_up_continuity": min(1.0, limit_streak / 3.0),
        "persistence": (
            sum(value > 0 for value in daily_returns[-5:]) / len(daily_returns[-5:])
            if daily_returns
            else 0.0
        ),
        "volatility": statistics.pstdev(daily_returns) if len(daily_returns) >= 2 else 0.0,
        "drawdown": closes[-1] / max(closes) - 1.0 if closes else 0.0,
    }


def _sector_sources(sector: dict, cutoff: date | None) -> list[dict]:
    sources = list(sector.get("current_member_sources", []))
    if not sources:
        sources = [value for value in sector.get("members", []) if isinstance(value, dict)]
    return [
        _source_features(source, cutoff)
        for source in sources
        if str(source.get("code", "")).strip()
    ]


def rank_leaders(
    snapshot: dict,
    forecasts: Sequence[dict],
    *,
    leaders_per_sector: int = 3,
    max_sector_rank: int = 5,
) -> list[dict]:
    snapshot_id = str(snapshot.get("snapshot_id", ""))
    if not snapshot_id:
        raise LeaderBlocked("leader_snapshot_id_missing")
    selected = [
        row
        for row in forecasts
        if row.get("market_rank") is None or int(row["market_rank"]) <= max_sector_rank
    ]
    for row in selected:
        if str(row.get("snapshot_id", snapshot_id)) != snapshot_id:
            raise LeaderBlocked(f"leader_forecast_snapshot_mismatch:{row.get('sector')}")
    sectors = {str(row["sector"]): row for row in snapshot.get("sectors", [])}
    try:
        cutoff = date.fromisoformat(str(snapshot["resolved_trade_date"]))
    except (KeyError, ValueError):
        cutoff = None
    output: list[dict] = []
    for forecast in selected:
        sector_name = str(forecast["sector"])
        sector = sectors.get(sector_name)
        if sector is None:
            raise LeaderBlocked(f"leader_forecast_sector_not_in_snapshot:{sector_name}")
        sources = _sector_sources(sector, cutoff)
        allowed_codes = {
            str(item.get("code")) if isinstance(item, dict) else str(item)
            for item in sector.get("members", [])
        }
        if not allowed_codes:
            allowed_codes = {str(item["code"]) for item in sources}
        if any(str(item["code"]) not in allowed_codes for item in sources):
            raise LeaderBlocked(f"leader_member_not_in_frozen_sector:{sector_name}")
        strengths = [max(0.0, _safe(item.get("relative_strength"))) for item in sources]
        second_tier_support = sum(value > 0.02 for value in strengths[1:]) / max(1, len(strengths) - 1)
        scored: list[tuple[float, dict]] = []
        for source in sources:
            relative_strength = _safe(source.get("relative_strength"))
            amount_ratio = max(0.01, _safe(source.get("amount_ratio"), 1.0))
            continuity = _safe(source.get("limit_up_continuity"))
            persistence = _safe(source.get("persistence"), 0.5)
            volatility = _safe(source.get("volatility"))
            drawdown = _safe(source.get("drawdown"))
            score = (
                3.0 * relative_strength
                + 0.35 * math.log(amount_ratio)
                + 0.90 * continuity
                + 0.55 * persistence
                + 0.25 * second_tier_support
                - 1.50 * volatility
                + 0.80 * drawdown
            )
            scored.append((score, source))
        scored.sort(key=lambda item: (-item[0], str(item[1]["code"])))
        positive_strength = sum(max(0.0, value) for value in strengths)
        dependency = (
            max(strengths, default=0.0) / positive_strength if positive_strength > 0 else 1.0
        )
        probability = float(
            forecast.get("final_probability", forecast.get("market_probability", 0.0))
        )
        for rank, (score, source) in enumerate(scored[:leaders_per_sector], start=1):
            output.append(
                {
                    "snapshot_id": snapshot_id,
                    "resolved_trade_date": cutoff.isoformat() if cutoff else None,
                    "sector": sector_name,
                    "horizon": forecast.get("horizon"),
                    "sector_forecast_probability": probability,
                    "sector_forecast_rank": forecast.get("market_rank"),
                    "code": str(source["code"]),
                    "leader_rank": rank,
                    "leader_score": score,
                    "leader_probability": _sigmoid(score),
                    "sector_dependency": dependency,
                    "member_of_frozen_sector": True,
                    "reasons": [
                        f"relative_strength={_safe(source.get('relative_strength')):.4f}",
                        f"amount_ratio={_safe(source.get('amount_ratio'), 1.0):.4f}",
                        f"persistence={_safe(source.get('persistence'), 0.5):.4f}",
                    ],
                    "risks": [
                        f"volatility={_safe(source.get('volatility')):.4f}",
                        f"drawdown={_safe(source.get('drawdown')):.4f}",
                        "future_hotspot_forecast_can_fail",
                    ],
                    "invalidation": [
                        "sector_drops_out_of_forecast_top_set",
                        "relative_strength_turns_non_positive",
                        "snapshot_or_membership_lineage_changes",
                    ],
                }
            )
    return output
