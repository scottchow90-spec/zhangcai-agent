#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

from typing import Any


MIN_INDEPENDENT_OVERLAP = 0.95


def normalize_date(value: Any) -> str:
    return str(value or "").replace("-", "")


def is_cross_validated_official_pool_date(
    payload: dict[str, Any],
    expected_date: str,
) -> bool:
    if not isinstance(payload, dict):
        return False
    expected = normalize_date(expected_date)
    requested = normalize_date(payload.get("request_date"))
    reported = normalize_date(payload.get("qdate"))
    verification = payload.get("date_verification")
    if not isinstance(verification, dict):
        return False
    try:
        declared_minimum = float(
            verification.get("minimum_independent_overlap")
        )
        tdx_overlap = float(verification.get("tdx_overlap_ratio"))
        lianban_overlap = float(verification.get("lianban_overlap_ratio"))
    except (TypeError, ValueError):
        return False
    minimum = max(MIN_INDEPENDENT_OVERLAP, declared_minimum)
    drift_warning = f"OFFICIAL_SOURCE_QDATE_METADATA_DRIFT:{reported}!={requested}"
    return all(
        (
            payload.get("status") == "CLEAN_PASS",
            payload.get("date_metadata_status") == "CROSS_VALIDATED_DEGRADED",
            not payload.get("blocks"),
            bool(expected),
            requested == expected,
            bool(reported),
            reported != expected,
            normalize_date(verification.get("requested_date")) == expected,
            normalize_date(verification.get("reported_qdate")) == reported,
            verification.get("akshare_exact_set_match") is True,
            verification.get("tdx_same_date") is True,
            tdx_overlap >= minimum,
            verification.get("lianban_same_date") is True,
            verification.get("lianban_count_matches") is True,
            lianban_overlap >= minimum,
            drift_warning in list(payload.get("warnings") or []),
        )
    )
