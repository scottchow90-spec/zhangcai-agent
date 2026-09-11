#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

from typing import Any


CANONICAL_SCORING_MODE = "score-research-composite"
DEFAULT_BOARD_NAME = "黄金点火"
DEFAULT_BOARD_CODE = "HJDH"
SCORING_CONTRACT_ID = "BIG_BULL_30_ITEM_COMPOSITE_V1"
LEGACY_COMPATIBILITY_FLAG = "--legacy-five-dimension-compat"
LEGACY_MODE_ALIASES = frozenset({"score-board", "score", "评分"})
SCORING_UNIVERSE_POLICY = "tdx_csi300_fixed_reference_v1"
COMPONENT_ITEM_COUNTS = [16, 10, 4]
TOP_LEVEL_WEIGHTS = [40.0, 35.0, 25.0]


def normalize_business_args(
    arguments: list[str],
    *,
    inherited_legacy_authorization: bool = False,
) -> list[str]:
    values = list(arguments) if arguments else [CANONICAL_SCORING_MODE]
    mode = values[0]
    if mode not in LEGACY_MODE_ALIASES:
        if LEGACY_COMPATIBILITY_FLAG in values:
            raise ValueError("legacy_compatibility_flag_without_legacy_mode")
        if mode in {CANONICAL_SCORING_MODE, "研究型综合评分"} and not any(
            flag in values[1:]
            for flag in ("--board-name", "--board-code", "--board-file")
        ):
            values.extend(
                ["--board-name", DEFAULT_BOARD_NAME, "--board-code", DEFAULT_BOARD_CODE]
            )
        return values

    explicitly_authorized = LEGACY_COMPATIBILITY_FLAG in values
    if not explicitly_authorized and not inherited_legacy_authorization:
        raise ValueError(
            "legacy_five_dimension_mode_blocked:"
            f"use {LEGACY_COMPATIBILITY_FLAG} only for explicit compatibility work"
        )
    return [value for value in values if value != LEGACY_COMPATIBILITY_FLAG]


def validate_composite_ranking_identity(payload: dict[str, Any]) -> dict[str, Any]:
    identity = payload.get("scoring_identity")
    if not isinstance(identity, dict):
        raise ValueError("composite_scoring_identity_missing")
    expected = {
        "contract_id": SCORING_CONTRACT_ID,
        "canonical_mode": CANONICAL_SCORING_MODE,
        "universe_policy": SCORING_UNIVERSE_POLICY,
        "tdx_market": "23",
        "component_item_counts": COMPONENT_ITEM_COUNTS,
        "top_level_weights": TOP_LEVEL_WEIGHTS,
    }
    for key, value in expected.items():
        if identity.get(key) != value:
            raise ValueError(f"composite_scoring_identity_invalid:{key}")
    if str(identity.get("score_date", "")) != str(payload.get("score_date", "")):
        raise ValueError("composite_scoring_identity_invalid:score_date")
    if int(identity.get("universe_count", 0)) <= 0:
        raise ValueError("composite_scoring_identity_invalid:universe_count")
    for key in ("universe_sha256", "model_sha256", "formula_catalog_sha256"):
        value = str(identity.get(key, ""))
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError(f"composite_scoring_identity_invalid:{key}")
    return {
        "status": "PASS",
        "contract_id": SCORING_CONTRACT_ID,
        "universe_sha256": identity["universe_sha256"],
        "model_sha256": identity["model_sha256"],
        "formula_catalog_sha256": identity["formula_catalog_sha256"],
    }
