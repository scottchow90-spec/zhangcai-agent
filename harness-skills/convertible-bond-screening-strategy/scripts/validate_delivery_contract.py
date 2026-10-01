from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "run"

DELIVERY_SCHEMA = "CONVERTIBLE-BOND-SCREENING-DELIVERY-1"
SCORE_MODEL_VERSION = "CB-WEIGHTED-10-V2"
SCORE_CRITERIA = (
    ("c1_price_activity", 6.0),
    ("c2_remaining_scale", 8.0),
    ("c3_premium", 12.0),
    ("c4_golden_ignition", 14.0),
    ("c5_feilong_cross", 15.0),
    ("c6_youzi_inflow", 15.0),
    ("c7_scr90_convergence", 6.0),
    ("c8_scr70_convergence", 8.0),
    ("c9_sector_heat", 8.0),
    ("c11_turnover5", 8.0),
)
SCORE_COMPONENT_IDS = tuple(criterion_id for criterion_id, _weight in SCORE_CRITERIA)
SCORE_COMPONENT_WEIGHTS = tuple(weight for _criterion_id, weight in SCORE_CRITERIA)
SCORE_WEIGHTS = dict(SCORE_CRITERIA)

AUTHORITATIVE_FILENAMES = (
    "run_state",
    "status_readback",
    "skill_status",
    "latest_summary",
)
AUTHORITATIVE_RELATIVE_PATHS = {
    "run_state": Path("run_state.json"),
    "status_readback": Path("status_readback.json"),
    "skill_status": Path("skill_status.json"),
    "latest_summary": Path("latest_summary.json"),
}
AUTHORITATIVE_SCHEMAS = {
    "run_state": "CONVERTIBLE-BOND-SCREENING-RUN-STATE-1",
    "status_readback": "CONVERTIBLE-BOND-SCREENING-STATUS-READBACK-3",
    "skill_status": "CONVERTIBLE-BOND-SCREENING-SKILL-STATUS-3",
    "latest_summary": "CONVERTIBLE-BOND-SCREENING-SUMMARY-3",
}
RUN_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
CHINESE_NAME_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


class DeliveryContractError(RuntimeError):
    pass


def _fail(message: str) -> None:
    raise DeliveryContractError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _strict_number(value: Any, label: str) -> float:
    _require(type(value) in (int, float), f"{label}:expected_number")
    number = float(value)
    _require(math.isfinite(number), f"{label}:expected_finite_number")
    return number


def _number_equal(actual: Any, expected: float, label: str) -> None:
    number = _strict_number(actual, label)
    _require(
        math.isclose(number, expected, rel_tol=0.0, abs_tol=1e-9),
        f"{label}:expected={expected}:actual={number}",
    )


def _verified_chinese_name(value: Any, label: str) -> str:
    _require(type(value) is str, f"{label}:must_be_string")
    name = value.strip()
    _require(bool(name), f"{label}:missing")
    _require(len(name) <= 64, f"{label}:too_long")
    _require(CHINESE_NAME_PATTERN.search(name) is not None, f"{label}:chinese_name_required")
    return name


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _ordinary_file(path: Path, label: str) -> None:
    _require(path.exists(), f"{label}:missing:{path}")
    _require(path.is_file(), f"{label}:not_file:{path}")
    _require(not path.is_symlink(), f"{label}:symlink_forbidden:{path}")


def _load_json(path: Path, label: str) -> dict[str, Any]:
    _ordinary_file(path, label)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DeliveryContractError(
            f"{label}:json_read_failed:{type(exc).__name__}:{exc}"
        ) from exc
    _require(type(payload) is dict, f"{label}:root_must_be_object")
    return payload


def _canonical_authoritative_paths(run_root: Path) -> dict[str, Path]:
    return {
        name: run_root / relative_path
        for name, relative_path in AUTHORITATIVE_RELATIVE_PATHS.items()
    }


def _validated_authoritative_paths(
    run_root: Path,
    authoritative_paths: Mapping[str, Path] | None,
) -> dict[str, Path]:
    canonical = _canonical_authoritative_paths(run_root)
    supplied = canonical if authoritative_paths is None else dict(authoritative_paths)
    _require(
        tuple(supplied) == AUTHORITATIVE_FILENAMES,
        "authoritative_sources:exact_names_and_order_required",
    )
    validated: dict[str, Path] = {}
    for name in AUTHORITATIVE_FILENAMES:
        actual = Path(supplied[name])
        expected = canonical[name]
        _require(
            actual.resolve(strict=False) == expected.resolve(strict=False),
            (
                f"authoritative_sources:{name}:non_whitelisted_path:"
                f"{actual}:expected:{expected}"
            ),
        )
        _ordinary_file(actual, f"authoritative_sources:{name}")
        validated[name] = actual
    return validated


def _validate_score_model(model: Any, label: str) -> list[dict[str, Any]]:
    _require(type(model) is dict, f"{label}:must_be_object")
    _require(
        model.get("version") == SCORE_MODEL_VERSION,
        f"{label}:version_must_equal:{SCORE_MODEL_VERSION}",
    )
    criteria = model.get("criteria")
    _require(type(criteria) is list, f"{label}:criteria_must_be_list")
    _require(len(criteria) == len(SCORE_CRITERIA), f"{label}:criterion_count_must_be_10")
    _require(
        type(model.get("criterion_count")) is int
        and model["criterion_count"] == len(SCORE_CRITERIA),
        f"{label}:declared_criterion_count_must_be_10",
    )
    _number_equal(model.get("weight_sum"), 100.0, f"{label}:weight_sum")

    actual_ids: list[str] = []
    for index, ((expected_id, expected_weight), criterion) in enumerate(
        zip(SCORE_CRITERIA, criteria, strict=True)
    ):
        _require(type(criterion) is dict, f"{label}:criterion_{index}:must_be_object")
        actual_id = criterion.get("id")
        actual_ids.append(str(actual_id))
        _require(
            actual_id == expected_id,
            f"{label}:criterion_{index}:id_must_equal:{expected_id}",
        )
        _number_equal(
            criterion.get("weight"),
            expected_weight,
            f"{label}:{expected_id}:weight",
        )
    _require(
        tuple(actual_ids) == SCORE_COMPONENT_IDS,
        f"{label}:criterion_ids_and_order_drift",
    )
    _require(
        not any("big_bull" in criterion_id.lower() for criterion_id in actual_ids),
        f"{label}:big_bull_cannot_be_scored",
    )
    _require(
        "big_bull_red=True" in str(model.get("tie_break_rule") or ""),
        f"{label}:big_bull_tie_break_rule_missing",
    )
    _require(
        "contributes zero score" in str(model.get("big_bull_rule") or ""),
        f"{label}:big_bull_zero_score_rule_missing",
    )
    return copy.deepcopy(criteria)


def _validate_result_top10(
    result: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rows = result.get("ranking_top10")
    _require(type(rows) is list and len(rows) == 10, "result:ranking_top10_must_have_10")
    seen_symbols: set[str] = set()
    rows_by_symbol: dict[str, dict[str, Any]] = {}
    prior_score = math.inf

    for expected_rank, row in enumerate(rows, start=1):
        label = f"result:top10:{expected_rank}"
        _require(type(row) is dict, f"{label}:must_be_object")
        _require(
            type(row.get("rank")) is int and row["rank"] == expected_rank,
            f"{label}:rank_mismatch",
        )
        symbol = row.get("symbol")
        _require(type(symbol) is str and bool(symbol), f"{label}:symbol_missing")
        _require(symbol not in seen_symbols, f"{label}:duplicate_symbol:{symbol}")
        seen_symbols.add(symbol)
        _verified_chinese_name(row.get("name"), f"{label}:name")
        _require(
            type(row.get("underlying_symbol")) is str
            and bool(row["underlying_symbol"]),
            f"{label}:underlying_symbol_missing",
        )
        _verified_chinese_name(
            row.get("underlying_name"),
            f"{label}:underlying_name",
        )

        components = row.get("score_components")
        _require(type(components) is dict, f"{label}:score_components_must_be_object")
        _require(
            tuple(components) == SCORE_COMPONENT_IDS,
            f"{label}:score_component_ids_or_order_drift",
        )
        earned_total = 0.0
        for criterion_id, expected_weight in SCORE_CRITERIA:
            component = components.get(criterion_id)
            _require(type(component) is dict, f"{label}:{criterion_id}:must_be_object")
            _number_equal(
                component.get("weight"),
                expected_weight,
                f"{label}:{criterion_id}:weight",
            )
            normalized = _strict_number(
                component.get("normalized_score"),
                f"{label}:{criterion_id}:normalized_score",
            )
            _require(
                -1e-9 <= normalized <= 1.0 + 1e-9,
                f"{label}:{criterion_id}:normalized_score_out_of_range",
            )
            earned = _strict_number(
                component.get("earned_score"),
                f"{label}:{criterion_id}:earned_score",
            )
            _require(
                math.isclose(
                    earned,
                    expected_weight * normalized,
                    rel_tol=0.0,
                    abs_tol=1e-8,
                ),
                f"{label}:{criterion_id}:earned_score_recompute_failed",
            )
            earned_total += earned

        total = _strict_number(row.get("score_total_raw"), f"{label}:score_total_raw")
        _require(
            math.isclose(total, earned_total, rel_tol=0.0, abs_tol=1e-8),
            f"{label}:score_total_raw_recompute_failed",
        )
        _require(total <= prior_score + 1e-9, f"{label}:ranking_score_order_invalid")
        prior_score = total
        _require(
            type(row.get("big_bull_red_preference")) is bool,
            f"{label}:big_bull_must_be_boolean_tie_break_only",
        )
        rows_by_symbol[symbol] = row

    return rows, rows_by_symbol


def _validate_status_top10(
    payload: dict[str, Any],
    result_rows: list[dict[str, Any]],
    label: str,
) -> None:
    rows = payload.get("top10")
    _require(type(rows) is list and len(rows) == 10, f"{label}:top10_must_have_10")
    for expected, actual in zip(result_rows, rows, strict=True):
        rank = expected["rank"]
        _require(type(actual) is dict, f"{label}:top10:{rank}:must_be_object")
        _require(actual.get("rank") == rank, f"{label}:top10:{rank}:rank_mismatch")
        _require(
            actual.get("symbol") == expected["symbol"],
            f"{label}:top10:{rank}:symbol_mismatch",
        )
        _require(
            actual.get("name") == expected["name"],
            f"{label}:top10:{rank}:name_mismatch",
        )
        _require(
            actual.get("underlying_symbol") == expected["underlying_symbol"],
            f"{label}:top10:{rank}:underlying_symbol_mismatch",
        )
        _require(
            actual.get("underlying_name") == expected["underlying_name"],
            f"{label}:top10:{rank}:underlying_name_mismatch",
        )
        _number_equal(
            actual.get("score"),
            float(expected["score_total_raw"]),
            f"{label}:top10:{rank}:score",
        )
        _require(
            actual.get("big_bull_red_preference")
            is expected["big_bull_red_preference"],
            f"{label}:top10:{rank}:big_bull_tie_break_mismatch",
        )


def _validate_summary_top10(
    summary: dict[str, Any],
    result_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = summary.get("top10")
    _require(type(rows) is list and len(rows) == 10, "summary:top10_must_have_10")
    for expected, actual in zip(result_rows, rows, strict=True):
        rank = expected["rank"]
        label = f"summary:top10:{rank}"
        _require(type(actual) is dict, f"{label}:must_be_object")
        _require(actual.get("rank") == rank, f"{label}:rank_mismatch")
        _require(actual.get("symbol") == expected["symbol"], f"{label}:symbol_mismatch")
        _require(
            actual.get("bond") == f'{expected["name"]}（{expected["symbol"]}）',
            f"{label}:bond_display_mismatch",
        )
        _require(
            actual.get("underlying_symbol") == expected["underlying_symbol"],
            f"{label}:underlying_symbol_mismatch",
        )
        _require(
            actual.get("underlying")
            == f'{expected["underlying_name"]}（{expected["underlying_symbol"]}）',
            f"{label}:underlying_display_mismatch",
        )
        _number_equal(
            actual.get("score"),
            round(float(expected["score_total_raw"]), 2),
            f"{label}:score",
        )
        component_scores = actual.get("component_scores")
        _require(type(component_scores) is dict, f"{label}:component_scores_must_be_object")
        _require(
            tuple(component_scores) == SCORE_COMPONENT_IDS,
            f"{label}:component_score_ids_or_order_drift",
        )
        for criterion_id, _weight in SCORE_CRITERIA:
            _number_equal(
                component_scores.get(criterion_id),
                round(
                    float(
                        expected["score_components"][criterion_id]["earned_score"]
                    ),
                    2,
                ),
                f"{label}:{criterion_id}:component_score",
            )
        _require(
            actual.get("big_bull_red_preference")
            is expected["big_bull_red_preference"],
            f"{label}:big_bull_tie_break_mismatch",
        )
    delivery_rows = copy.deepcopy(rows)
    for expected, delivery_row in zip(result_rows, delivery_rows, strict=True):
        delivery_row["name"] = expected["name"]
        delivery_row["underlying_name"] = expected["underlying_name"]
    return delivery_rows


def build_delivery_payload(
    run_root: Path = RUN,
    *,
    authoritative_paths: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    run_root = Path(run_root)
    paths = _validated_authoritative_paths(run_root, authoritative_paths)
    documents = {
        name: _load_json(path, f"authoritative_sources:{name}")
        for name, path in paths.items()
    }

    for name, expected_schema in AUTHORITATIVE_SCHEMAS.items():
        payload = documents[name]
        _require(
            payload.get("schema") == expected_schema,
            f"authoritative_sources:{name}:schema_mismatch",
        )
        _require(
            payload.get("status") == "PASS",
            f"authoritative_sources:{name}:status_must_be_PASS",
        )

    run_ids = {payload.get("run_id") for payload in documents.values()}
    _require(len(run_ids) == 1, "authoritative_sources:cross_run_mixing_rejected")
    run_id = next(iter(run_ids))
    _require(
        type(run_id) is str and RUN_ID_PATTERN.fullmatch(run_id) is not None,
        "authoritative_sources:run_id_must_be_32_lower_hex",
    )
    attempts = {payload.get("market_attempt") for payload in documents.values()}
    _require(
        len(attempts) == 1,
        "authoritative_sources:cross_attempt_mixing_rejected",
    )
    market_attempt = next(iter(attempts))
    _require(
        type(market_attempt) is int and market_attempt > 0,
        "authoritative_sources:market_attempt_must_be_positive_integer",
    )

    for name in ("run_state", "status_readback", "skill_status"):
        _require(
            documents[name].get("automatic_order") is False,
            f"authoritative_sources:{name}:automatic_order_must_be_false",
        )
    _require(
        (documents["latest_summary"].get("personal_kb_confirmation_model") or {}).get(
            "automatic_order"
        )
        is False,
        "authoritative_sources:latest_summary:automatic_order_must_be_false",
    )

    generation_dir = (
        run_root / "generations" / run_id / f"attempt-{market_attempt}"
    )
    generation_result_path = generation_dir / "latest_result.json"
    generation_summary_path = generation_dir / "latest_summary.json"
    result = _load_json(generation_result_path, "generation:latest_result")
    generation_summary = _load_json(
        generation_summary_path,
        "generation:latest_summary",
    )
    published_summary = documents["latest_summary"]

    _require(
        generation_summary_path.read_bytes() == paths["latest_summary"].read_bytes(),
        "latest_summary:published_bytes_do_not_match_current_generation",
    )
    _require(
        _sha256(generation_summary_path) == _sha256(paths["latest_summary"]),
        "latest_summary:published_sha256_does_not_match_current_generation",
    )
    _require(
        generation_summary == published_summary,
        "latest_summary:published_json_does_not_match_current_generation",
    )

    for label, payload, expected_schema in (
        ("generation:latest_result", result, "TDX-CONVERTIBLE-BOND-WEIGHTED-SCAN-V5"),
        (
            "generation:latest_summary",
            generation_summary,
            "CONVERTIBLE-BOND-SCREENING-SUMMARY-3",
        ),
    ):
        _require(payload.get("schema") == expected_schema, f"{label}:schema_mismatch")
        _require(payload.get("status") == "PASS", f"{label}:status_must_be_PASS")
        _require(payload.get("run_id") == run_id, f"{label}:run_id_mismatch")
        _require(
            payload.get("market_attempt") == market_attempt,
            f"{label}:market_attempt_mismatch",
        )

    _require(
        (result.get("personal_kb_confirmation_model") or {}).get("automatic_order")
        is False,
        "generation:latest_result:automatic_order_must_be_false",
    )
    result_criteria = _validate_score_model(
        result.get("score_model"),
        "generation:latest_result:score_model",
    )
    _validate_score_model(
        generation_summary.get("score_model"),
        "generation:latest_summary:score_model",
    )

    skill_status = documents["skill_status"]
    _require(
        skill_status.get("score_model_version") == SCORE_MODEL_VERSION,
        "skill_status:score_model_version_mismatch",
    )
    _require(
        type(skill_status.get("score_criteria_count")) is int
        and skill_status["score_criteria_count"] == len(SCORE_CRITERIA),
        "skill_status:score_criteria_count_mismatch",
    )
    _number_equal(
        skill_status.get("score_weight_sum"),
        100.0,
        "skill_status:score_weight_sum",
    )

    result_rows, _rows_by_symbol = _validate_result_top10(result)
    _validate_status_top10(skill_status, result_rows, "skill_status")
    _validate_status_top10(
        documents["status_readback"],
        result_rows,
        "status_readback",
    )
    summary_rows = _validate_summary_top10(generation_summary, result_rows)

    delivery_top10 = [
        {
            **row,
            "run_id": run_id,
            "market_attempt": market_attempt,
        }
        for row in summary_rows
    ]
    return {
        "schema": DELIVERY_SCHEMA,
        "status": "PASS",
        "run_id": run_id,
        "market_attempt": market_attempt,
        "score_model_version": SCORE_MODEL_VERSION,
        "criterion_count": len(SCORE_CRITERIA),
        "weight_sum": sum(SCORE_COMPONENT_WEIGHTS),
        "automatic_order": False,
        "manual_override_allowed": False,
        "cross_run_mixing_allowed": False,
        "delivery_contract_exact": True,
        "score_criteria": result_criteria,
        "top10": delivery_top10,
        "authoritative_sources": {
            name: _artifact(path) for name, path in paths.items()
        },
        "verified_generation_sources": {
            "latest_result": _artifact(generation_result_path),
            "latest_summary": _artifact(generation_summary_path),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and emit the fixed convertible-bond delivery contract."
    )
    parser.add_argument("--run-root", type=Path, default=RUN)
    args = parser.parse_args()
    try:
        payload = build_delivery_payload(args.run_root)
    except DeliveryContractError as exc:
        print(
            json.dumps(
                {
                    "schema": DELIVERY_SCHEMA,
                    "status": "BLOCKED",
                    "reason": str(exc),
                    "automatic_order": False,
                    "manual_override_allowed": False,
                    "cross_run_mixing_allowed": False,
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
