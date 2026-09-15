#!/usr/bin/env python3
"""Validate point-in-time catalyst evidence and apply bounded probability fusion."""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Sequence


REQUIRED_EVIDENCE_FIELDS = (
    "evidence_id",
    "sector",
    "published_time",
    "collected_time",
    "source_grade",
    "novelty",
    "directness",
    "magnitude",
    "pollution_state",
    "counter_evidence",
)
SOURCE_WEIGHTS = {"A": 1.0, "B": 0.70, "C": 0.40, "D": 0.15}
POLLUTION_STATES = {"PASS", "SOFT_FAIL", "HARD_FAIL"}


class EvidenceBlocked(RuntimeError):
    """Raised when catalyst evidence violates the point-in-time contract."""


def _as_utc(value: datetime | str, field: str) -> datetime:
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise EvidenceBlocked(f"evidence_datetime_invalid:{field}:{value}") from exc
    if parsed.tzinfo is None:
        raise EvidenceBlocked(f"evidence_datetime_timezone_missing:{field}:{value}")
    return parsed.astimezone(timezone.utc)


def _bounded_unit(value: object, field: str, evidence_id: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceBlocked(f"evidence_numeric_invalid:{evidence_id}:{field}") from exc
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise EvidenceBlocked(f"evidence_numeric_out_of_range:{evidence_id}:{field}")
    return number


def _counter_penalty(value: object) -> float:
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    if isinstance(value, (list, tuple, set)):
        return min(1.0, 0.20 * len(value))
    return 0.25 if str(value).strip() else 0.0


def validate_evidence_rows(rows: Sequence[dict], cutoff: datetime) -> list[dict]:
    cutoff_utc = _as_utc(cutoff, "cutoff")
    normalized: list[dict] = []
    seen: set[str] = set()
    for source in rows:
        missing = [field for field in REQUIRED_EVIDENCE_FIELDS if field not in source]
        if missing:
            raise EvidenceBlocked("evidence_fields_missing:" + ",".join(missing))
        evidence_id = str(source["evidence_id"]).strip()
        sector = str(source["sector"]).strip()
        if not evidence_id or not sector:
            raise EvidenceBlocked("evidence_identity_empty")
        if evidence_id in seen:
            raise EvidenceBlocked(f"evidence_id_duplicate:{evidence_id}")
        seen.add(evidence_id)
        published = _as_utc(source["published_time"], "published_time")
        collected = _as_utc(source["collected_time"], "collected_time")
        if published > cutoff_utc or collected > cutoff_utc:
            raise EvidenceBlocked(f"evidence_after_cutoff:{evidence_id}")
        if collected < published:
            raise EvidenceBlocked(f"evidence_collected_before_publication:{evidence_id}")
        grade = str(source["source_grade"]).strip().upper()
        if grade not in SOURCE_WEIGHTS:
            raise EvidenceBlocked(f"evidence_source_grade_invalid:{evidence_id}:{grade}")
        pollution = str(source["pollution_state"]).strip().upper()
        if pollution not in POLLUTION_STATES:
            raise EvidenceBlocked(
                f"evidence_pollution_state_invalid:{evidence_id}:{pollution}"
            )
        normalized.append(
            {
                **source,
                "evidence_id": evidence_id,
                "sector": sector,
                "published_time": published.isoformat(),
                "collected_time": collected.isoformat(),
                "source_grade": grade,
                "novelty": _bounded_unit(source["novelty"], "novelty", evidence_id),
                "directness": _bounded_unit(
                    source["directness"], "directness", evidence_id
                ),
                "magnitude": _bounded_unit(
                    source["magnitude"], "magnitude", evidence_id
                ),
                "pollution_state": pollution,
                "counter_evidence": source["counter_evidence"],
                "age_hours": max(0.0, (cutoff_utc - published).total_seconds() / 3600.0),
            }
        )
    return normalized


def evidence_score(row: dict) -> float:
    decay = 0.5 ** (float(row["age_hours"]) / 72.0)
    positive = (
        SOURCE_WEIGHTS[row["source_grade"]]
        * float(row["novelty"])
        * float(row["directness"])
        * float(row["magnitude"])
        * decay
    )
    net = positive - _counter_penalty(row["counter_evidence"])
    pollution = row["pollution_state"]
    if pollution == "SOFT_FAIL":
        net = min(net, 0.0) if net < 0 else net * 0.5
    elif pollution == "HARD_FAIL":
        net = -abs(net if net else positive or 0.1)
    return max(-1.0, min(1.0, net))


def apply_catalyst_adjustment(
    market_probability: float,
    catalyst_score: float,
    forecast_status: str,
    pollution_state: str = "PASS",
) -> float:
    base = max(0.0, min(1.0, float(market_probability)))
    status = str(forecast_status).upper()
    cap = 0.10 if status in {"PROVISIONAL_FORECAST", "DEGRADED_FORECAST"} else 0.20
    score = max(-1.0, min(1.0, float(catalyst_score)))
    scaled = cap * min(1.0, abs(score) / 0.80)
    if str(pollution_state).upper() == "HARD_FAIL":
        adjustment = -scaled if score else -cap
    else:
        adjustment = math.copysign(scaled, score) if score else 0.0
    return max(0.0, min(1.0, base + adjustment))


def fuse_catalysts(
    forecasts: Sequence[dict],
    evidence_rows: Sequence[dict],
    cutoff: datetime,
    forecast_status: str,
) -> list[dict]:
    evidence = validate_evidence_rows(evidence_rows, cutoff) if evidence_rows else []
    grouped: dict[tuple[str, str | None], list[dict]] = defaultdict(list)
    for row in evidence:
        grouped[(row["sector"], row.get("horizon"))].append(row)
    output: list[dict] = []
    for forecast in forecasts:
        sector = str(forecast["sector"])
        horizon = forecast.get("horizon")
        matched = [
            *grouped.get((sector, horizon), []),
            *grouped.get((sector, None), []),
        ]
        scores = [evidence_score(row) for row in matched]
        combined_score = max(-1.0, min(1.0, sum(scores))) if scores else 0.0
        pollution = (
            "HARD_FAIL"
            if any(row["pollution_state"] == "HARD_FAIL" for row in matched)
            else "SOFT_FAIL"
            if any(row["pollution_state"] == "SOFT_FAIL" for row in matched)
            else "PASS"
        )
        base = float(forecast["market_probability"])
        final = (
            apply_catalyst_adjustment(base, combined_score, forecast_status, pollution)
            if matched
            else base
        )
        output.append(
            {
                **forecast,
                "catalyst_score": combined_score,
                "catalyst_adjustment": round(final - base, 12),
                "final_probability": final,
                "evidence_ids": [row["evidence_id"] for row in matched],
                "catalyst_pollution_state": pollution,
                "forecast_status": forecast_status,
            }
        )
    return output
