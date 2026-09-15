#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from mainline_scoring import MODEL_VERSION, build_context, load_context_from_environment, score_board


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json_object_required:{path}")
    return payload


def context_from_bundle(bundle: dict[str, Any]) -> tuple[dict[str, Any], str]:
    pre_scored = bundle.get("pre_scored_boards")
    if isinstance(pre_scored, list):
        boards: dict[str, dict[str, Any]] = {}
        for raw in pre_scored:
            if not isinstance(raw, dict):
                continue
            scored = score_board(raw)
            scored["input_evidence"] = raw
            boards[scored["normalized_name"] or scored["name"]] = scored
        return {
            "model_version": MODEL_VERSION,
            "target_date": str(bundle.get("target_date", "")).strip() or None,
            "status": (
                "VERIFIED"
                if any(row["decision_eligible"] for row in boards.values())
                else "CLOSE_UNCONFIRMED"
                if any(row.get("status") == "CLOSE_UNCONFIRMED" for row in boards.values())
                else "GATE_FAILED"
            ),
            "source_status": {"fixture": "VERIFIED"},
            "source_paths": {},
            "boards": boards,
            "stocks": {},
            "issues": [],
        }, "pre_scored_board_audit"

    history = bundle.get("lianban_history", [])
    if isinstance(history, dict):
        history = history.get("snapshots", [])
    context = build_context(
        bundle.get("duanxianxia", {}),
        bundle.get("lianban", {}),
        history if isinstance(history, list) else [],
        bundle.get("tdx_catalog") if isinstance(bundle.get("tdx_catalog"), list) else None,
    )
    return context, "source_bundle"


def rank_boards(context: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(context.get("boards", {}).values())
    return sorted(
        rows,
        key=lambda row: (
            row.get("decision_eligible") is True,
            int(row.get("close_confirmation", {}).get("quality_signal_count", 0) or 0),
            float(row.get("score", 0) or 0),
            float(row.get("raw_score", 0) or 0),
            -int(row.get("input_evidence", {}).get("rank", 9999) or 9999),
        ),
        reverse=True,
    )


def build_result(context: dict[str, Any], input_mode: str) -> dict[str, Any]:
    boards = rank_boards(context)
    counts = Counter(str(row.get("status", "DEGRADED")) for row in boards)
    passed = [row for row in boards if row.get("decision_eligible") is True]
    ambiguous_candidates: list[str] = []
    if len(passed) >= 2:
        first, second = passed[:2]
        first_quality = int(first.get("close_confirmation", {}).get("quality_signal_count", 0) or 0)
        second_quality = int(second.get("close_confirmation", {}).get("quality_signal_count", 0) or 0)
        raw_score_gap = abs(float(first.get("raw_score", 0) or 0) - float(second.get("raw_score", 0) or 0))
        if first_quality == second_quality and raw_score_gap <= 5.0:
            ambiguous_candidates = [str(first.get("name", "")), str(second.get("name", ""))]
    decision_status = (
        "AMBIGUOUS_CLOSE"
        if ambiguous_candidates
        else "CONFIRMED_MAINLINE"
        if passed
        else "NO_CONFIRMED_MAINLINE"
    )
    return {
        "schema": "CORE_MAINLINE_SCORING_RESULT_V1",
        "execution_status": "CLEAN_PASS" if boards else "DATA_REQUIRED",
        "model_version": MODEL_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "target_date": context.get("target_date"),
        "input_mode": input_mode,
        "decision_status": decision_status,
        "source_status": context.get("source_status", {}),
        "source_paths": context.get("source_paths", {}),
        "session_alignment": context.get("session_alignment", {}),
        "issues": context.get("issues", []),
        "summary": {
            "board_count": len(boards),
            "passed_count": len(passed),
            "close_confirmed_count": len(passed),
            "close_unconfirmed_count": counts.get("CLOSE_UNCONFIRMED", 0),
            "gate_failed_count": counts.get("GATE_FAILED", 0),
            "degraded_count": counts.get("DEGRADED", 0),
            "core_mainline": passed[0]["name"] if passed and not ambiguous_candidates else None,
            "ambiguous_candidates": ambiguous_candidates,
        },
        "boards": boards,
        "policy": {
            "missing_evidence": "zero_without_weight_renormalization",
            "hard_gates": ["exact_three_two_one_ladder", "constituent_count_strictly_greater_than_100"],
            "close_confirmation": [
                "raw_score_at_least_60",
                "plate_rank_top_5",
                "limit_up_market_share_at_least_8_pct",
                "source_session_coverage_at_least_80_pct",
                "intraday_sample_at_least_3",
                "intraday_coverage_at_least_60_pct",
                "same_day_relative_close_quality_signals_at_least_2_of_4",
            ],
            "ambiguity_abstention": "same_quality_signal_count_and_raw_score_gap_at_most_5",
            "research_only": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="核心主线九项100分、双硬门槛与收盘确认层独立评分")
    parser.add_argument("--input-bundle", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.input_bundle:
        context, input_mode = context_from_bundle(load_json(args.input_bundle))
    else:
        context, input_mode = load_context_from_environment(), "canonical_live_sources"
    result = build_result(context, input_mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["execution_status"] == "CLEAN_PASS" else 2


if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
