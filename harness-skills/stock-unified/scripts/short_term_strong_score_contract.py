#!/usr/bin/env python3
"""Load and validate the canonical short-term strong-stock score contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


CONTRACT_PATH = Path(__file__).resolve().parents[1] / "references" / "short_term_strong_stock_scoring_contract.json"
EXPECTED_SCHEMA = "SHORT_TERM_STRONG_STOCK_SCORING_CONTRACT_V1"
EXPECTED_VERSION = "A-SHARE-STRONG-26F-100-V6.1"
EXPECTED_AXES = {"爆发力": 35.0, "持续性": 35.0, "市场协同": 20.0, "可交易性": 10.0}
RANKING_ROLES = {"candidate_ranking", "candidate_evidence"}


def sha256_file(path: Path = CONTRACT_PATH) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_contract(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    factors = payload.get("factors") if isinstance(payload.get("factors"), list) else []
    risks = payload.get("risk_deductions") if isinstance(payload.get("risk_deductions"), list) else []
    hard = payload.get("hard_exclusions") if isinstance(payload.get("hard_exclusions"), list) else []
    axes = payload.get("axes") if isinstance(payload.get("axes"), dict) else {}

    if payload.get("schema") != EXPECTED_SCHEMA:
        errors.append("schema_mismatch")
    if payload.get("version") != EXPECTED_VERSION:
        errors.append("version_mismatch")
    if {str(key): float(value) for key, value in axes.items()} != EXPECTED_AXES:
        errors.append("axis_weights_mismatch")
    if len(factors) != 26:
        errors.append("factor_count_not_26")
    if len({row.get("id") for row in factors if isinstance(row, dict)}) != len(factors):
        errors.append("factor_ids_not_unique")
    if len({row.get("name") for row in factors if isinstance(row, dict)}) != len(factors):
        errors.append("factor_names_not_unique")
    if round(sum(float(row.get("weight", 0)) for row in factors if isinstance(row, dict)), 6) != 100.0:
        errors.append("positive_weight_total_not_100")
    for axis, expected in EXPECTED_AXES.items():
        actual = sum(float(row.get("weight", 0)) for row in factors if isinstance(row, dict) and row.get("axis") == axis)
        if round(actual, 6) != expected:
            errors.append(f"axis_factor_weight_mismatch:{axis}")
    allowed_roles = RANKING_ROLES | {"pool_confirmation", "market_regime"}
    if any(row.get("role") not in allowed_roles for row in factors if isinstance(row, dict)):
        errors.append("unknown_factor_role")
    if sum(row.get("role") in RANKING_ROLES for row in factors if isinstance(row, dict)) != 23:
        errors.append("ranking_factor_count_not_23")
    if len(risks) != 15:
        errors.append("risk_count_not_15")
    if len(hard) != 7:
        errors.append("hard_exclusion_count_not_7")
    if payload.get("fundamental_policy", {}).get("positive_weight") != 0:
        errors.append("fundamental_positive_weight_not_zero")
    if payload.get("consumer_policy", {}).get("missing_or_mismatched_contract") != "block_score_and_ranking":
        errors.append("consumer_fail_closed_policy_missing")
    return errors


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_contract(payload)
    if errors:
        raise RuntimeError("invalid_short_term_strong_score_contract:" + ",".join(errors))
    return payload


def contract_summary(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    payload = load_contract(path)
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "schema": payload["schema"],
        "version": payload["version"],
        "factor_count": len(payload["factors"]),
        "risk_count": len(payload["risk_deductions"]),
        "hard_exclusion_count": len(payload["hard_exclusions"]),
        "positive_weight_total": sum(float(row["weight"]) for row in payload["factors"]),
        "fundamental_positive_weight": payload["fundamental_policy"]["positive_weight"],
    }


if __name__ == "__main__":
    print(json.dumps(contract_summary(), ensure_ascii=False, indent=2))
