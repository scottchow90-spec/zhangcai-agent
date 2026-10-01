#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared v9 business-result contract and workflow gate for limit-up-review."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEFAULT_SKILL_DIR = Path(__file__).resolve().parents[1]
BUSINESS_RESULT_SCHEMA_VERSION = "limit-up-review.business-result.v9"
REQUIRED_DOMAINS = (
    "data",
    "market",
    "structure",
    "direction",
    "capital",
    "catalyst",
    "continuity",
    "risk",
    "decision",
)
REQUIRED_SCENARIOS = ("strengthen", "rotation", "failure", "exogenous")
REQUIRED_CHECKPOINTS = ("premarket", "open", "intraday", "close")
ALLOWED_SIGNAL_STATUSES = {"SELECTED", "REJECTED", "UNAVAILABLE"}
ALLOWED_ANALYSIS_OPERATORS = {
    "distribution",
    "concentration",
    "cohort_compare",
    "cross_tab",
    "association",
    "divergence",
    "temporal_compare",
    "participant_attribution",
    "risk_propagation",
    "scenario_branch",
}
RECOMPUTED_METRICS = (
    "official_limit_up_count",
    "first_board_count",
    "continuation_count",
    "max_board",
)
ALLOWED_THESIS_STATUSES = {"SUPPORTED", "CONTESTED", "INSUFFICIENT", "REJECTED"}
ALLOWED_CLAIM_TYPES = {"INFERENCE", "HYPOTHESIS"}
CONFIDENCE_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
DELISTING_HARD_EXCLUSION = "delisting_hard_exclusion"


def now_iso() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def normalize_date(value: Any) -> str:
    text = str(value or "").strip()
    match = re.search(r"(20\d{2})[-_/]?(\d{2})[-_/]?(\d{2})", text)
    return "".join(match.groups()) if match else text


def code6(value: Any) -> str:
    text = str(value or "").strip()
    match = re.search(r"(\d{6})", text)
    return match.group(1) if match else text.zfill(6)


def compute_prediction_ledger_hash(
    trade_date: Any,
    theses: Any,
    scenario_tree: Any,
    watchlist: Any,
    entries: Any = None,
) -> str:
    """Return the canonical frozen-ledger hash shared by generator and gate."""
    frozen = {
        "trade_date": normalize_date(trade_date),
        "theses": theses,
        "scenario_tree": scenario_tree,
        "watchlist": watchlist,
        "entries": entries if entries is not None else [],
    }
    raw = json.dumps(
        frozen,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _as_items(value: Any, id_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if isinstance(value, list):
        items = [item for item in value if isinstance(item, dict)]
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, dict):
                record = dict(item)
                if not any(_nonempty(record.get(field)) for field in id_fields):
                    record[id_fields[0]] = str(key)
                items.append(record)
    return items


def _index_items(
    value: Any,
    id_fields: tuple[str, ...],
    label: str,
    blocks: list[str],
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    items = _as_items(value, id_fields)
    if not items:
        blocks.append(f"{label} must be a non-empty object/list")
        return index
    for position, item in enumerate(items):
        identifier = next(
            (str(item.get(field)).strip() for field in id_fields if _nonempty(item.get(field))),
            "",
        )
        if not identifier:
            blocks.append(f"{label}[{position}] missing identifier")
            continue
        if identifier in index:
            blocks.append(f"{label} duplicate identifier: {identifier}")
            continue
        index[identifier] = item
    return index


def _is_zero(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return value == 0
    return str(value).strip() in {"0", "0.0", "0.00", "0%"}


def _is_missing_record(record: dict[str, Any]) -> bool:
    status = str(
        record.get(
            "verification_status",
            record.get("availability", record.get("data_status", record.get("status", ""))),
        )
    ).strip().casefold()
    unavailable = {
        "missing",
        "unavailable",
        "not_available",
        "not-collected",
        "not_collected",
        "缺失",
        "不可用",
        "未采集",
    }
    return record.get("available") is False or status in unavailable


def _validate_missing_not_zero(value: Any, path: str, blocks: list[str]) -> None:
    if isinstance(value, dict):
        if _is_missing_record(value) and _is_zero(value.get("value")):
            blocks.append(f"{path} marks missing/unavailable data as numeric zero")
        for key, child in value.items():
            _validate_missing_not_zero(child, f"{path}.{key}", blocks)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_missing_not_zero(child, f"{path}[{index}]", blocks)


def _validate_references(
    records: Any,
    path: str,
    sources: dict[str, dict[str, Any]],
    metrics: dict[str, dict[str, Any]],
    evidence_records: dict[str, dict[str, Any]],
    blocks: list[str],
    *,
    expected_effect: str = "",
    expected_code: str = "",
    expected_thesis_id: str = "",
) -> set[str]:
    dimensions: set[str] = set()
    if not isinstance(records, list) or not records:
        blocks.append(f"{path} must be a non-empty list")
        return dimensions
    for index, record in enumerate(records):
        item_path = f"{path}[{index}]"
        if not isinstance(record, dict):
            blocks.append(f"{item_path} must be an object")
            continue
        dimension = str(record.get("dimension") or "").strip().casefold()
        if not dimension:
            blocks.append(f"{item_path} missing dimension")
        else:
            dimensions.add(dimension)
        source_id = str(record.get("source_id") or "").strip()
        metric_id = str(record.get("metric_id") or "").strip()
        evidence_id = str(record.get("evidence_id") or "").strip()
        effect = str(record.get("effect") or "").strip().upper()
        if not source_id or source_id not in sources:
            blocks.append(f"{item_path} source_id does not reference sources: {source_id!r}")
        if not evidence_id or evidence_id not in evidence_records:
            blocks.append(f"{item_path} evidence_id does not reference evidence_records: {evidence_id!r}")
        else:
            evidence = evidence_records[evidence_id]
            evidence_source = str(evidence.get("source_id") or "").strip()
            if source_id and evidence_source and source_id != evidence_source:
                blocks.append(f"{item_path} source_id conflicts with evidence source")
            if expected_code and code6(evidence.get("code")) != expected_code:
                blocks.append(f"{item_path} evidence_id is not row-level evidence for {expected_code}")
        if metric_id:
            if metric_id not in metrics:
                blocks.append(f"{item_path} metric_id does not reference metrics: {metric_id!r}")
            elif _is_missing_record(metrics[metric_id]):
                blocks.append(f"{item_path} references unavailable metric: {metric_id}")
        elif not evidence_id:
            blocks.append(f"{item_path} requires metric_id or evidence_id")
        if source_id and metric_id in metrics:
            metric_source = str(metrics[metric_id].get("source_id") or "").strip()
            if metric_source and metric_source != source_id:
                blocks.append(
                    f"{item_path} source_id {source_id!r} conflicts with metric source {metric_source!r}"
                )
        if expected_effect and effect != expected_effect:
            blocks.append(f"{item_path} effect must be {expected_effect}")
        if expected_effect == "CHALLENGES":
            if expected_thesis_id and str(record.get("challenge_to") or "").strip() != expected_thesis_id:
                blocks.append(f"{item_path} challenge_to must reference {expected_thesis_id}")
            if not _nonempty(record.get("alternative_explanation")):
                blocks.append(f"{item_path} counterevidence missing alternative_explanation")
        if not _nonempty(record.get("interpretation")):
            blocks.append(f"{item_path} missing interpretation")
        _validate_missing_not_zero(record, item_path, blocks)
    return dimensions


def _scenario_map(value: Any) -> dict[str, dict[str, Any]]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items() if isinstance(item, dict)}
    result: dict[str, dict[str, Any]] = {}
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            key = str(
                item.get("type")
                or item.get("scenario")
                or item.get("id")
                or item.get("key")
                or ""
            ).strip()
            if key:
                result[key] = item
    return result


def validate_business_result_payload(
    payload: Any,
    expected_date: str = "",
    expected_run_id: str = "",
) -> list[str]:
    """Return semantic block reasons; an empty list means the payload passes."""
    blocks: list[str] = []
    if not isinstance(payload, dict) or not payload:
        return ["business_result payload must be a non-empty object"]

    schema_version = str(payload.get("schema_version") or "").strip()
    if schema_version != BUSINESS_RESULT_SCHEMA_VERSION:
        blocks.append(
            f"schema_version mismatch: {schema_version!r} != {BUSINESS_RESULT_SCHEMA_VERSION!r}"
        )

    run = payload.get("run")
    if not isinstance(run, dict):
        blocks.append("run must be an object")
        run = {}
    run_id = str(run.get("run_id") or payload.get("run_id") or "").strip()
    trade_date = normalize_date(
        run.get("trade_date")
        or payload.get("trade_date")
        or payload.get("date")
    )
    if not run_id:
        blocks.append("run.run_id is required")
    if not re.fullmatch(r"20\d{6}", trade_date):
        blocks.append(f"run.trade_date is invalid: {trade_date!r}")
    if not _nonempty(run.get("generated_at")):
        blocks.append("run.generated_at is required")
    if not _nonempty(run.get("as_of")):
        blocks.append("run.as_of is required")
    elif normalize_date(run.get("as_of")) != trade_date:
        blocks.append("run.as_of must belong to run.trade_date")
    if str(run.get("timezone") or "").strip() != "Asia/Shanghai":
        blocks.append("run.timezone must be Asia/Shanghai")
    if normalize_date(run.get("latest_completed_trade_date")) != trade_date:
        blocks.append("run.latest_completed_trade_date must equal run.trade_date")
    current_data_fingerprint = str(run.get("current_data_fingerprint") or "").strip()
    if not re.fullmatch(r"[0-9a-f]{64}", current_data_fingerprint):
        blocks.append("run.current_data_fingerprint must be a 64-character lowercase sha256")
    if expected_run_id and run_id != str(expected_run_id).strip():
        blocks.append(f"run_id mismatch: {run_id!r} != {expected_run_id!r}")
    normalized_expected_date = normalize_date(expected_date)
    if normalized_expected_date and trade_date != normalized_expected_date:
        blocks.append(f"trade_date mismatch: {trade_date!r} != {normalized_expected_date!r}")

    declared_status = str(payload.get("status") or "").strip().upper()
    if declared_status not in {"CLEAN_PASS", "BLOCKED"}:
        blocks.append(f"invalid top-level status: {declared_status!r}")
    blocks_delivery = payload.get("blocks_delivery")
    if not isinstance(blocks_delivery, bool):
        blocks.append("blocks_delivery must be boolean")
    if blocks_delivery is True and declared_status != "BLOCKED":
        blocks.append("blocks_delivery=true requires top-level status BLOCKED")
    if declared_status == "BLOCKED":
        blocks.append("business_result declares BLOCKED")
    if declared_status == "CLEAN_PASS" and blocks_delivery is not False:
        blocks.append("CLEAN_PASS requires blocks_delivery=false")

    sources = _index_items(payload.get("sources"), ("id", "source_id"), "sources", blocks)
    for source_id, source in sources.items():
        if not _nonempty(source.get("as_of") or source.get("collected_at") or source.get("date")):
            blocks.append(f"sources[{source_id!r}] missing as_of/collected_at/date")
        if not _is_missing_record(source) and not _nonempty(source.get("uri") or source.get("path") or source.get("source")):
            blocks.append(f"sources[{source_id!r}] missing uri/path/source")
        if _is_missing_record(source) and not _nonempty(source.get("reason")):
            blocks.append(f"sources[{source_id!r}] unavailable without reason")

    metrics = _index_items(payload.get("metrics"), ("id", "metric_id"), "metrics", blocks)
    for metric_id, metric in metrics.items():
        source_id = str(metric.get("source_id") or "").strip()
        if not source_id or source_id not in sources:
            blocks.append(f"metrics[{metric_id!r}] invalid source_id: {source_id!r}")
        if "value" not in metric:
            blocks.append(f"metrics[{metric_id!r}] missing value")
        _validate_missing_not_zero(metric, f"metrics[{metric_id!r}]", blocks)
    for metric_id in RECOMPUTED_METRICS:
        if metric_id not in metrics:
            blocks.append(f"metrics missing recomputable metric: {metric_id}")

    evidence_records = _index_items(
        payload.get("evidence_records"), ("id", "evidence_id"), "evidence_records", blocks
    )
    for evidence_id, evidence in evidence_records.items():
        source_id = str(evidence.get("source_id") or "").strip()
        if not source_id or source_id not in sources:
            blocks.append(f"evidence_records[{evidence_id!r}] invalid source_id")
        if not _nonempty(evidence.get("observed_at")):
            blocks.append(f"evidence_records[{evidence_id!r}] missing observed_at")
        kind = str(evidence.get("kind") or "").strip()
        if kind not in {"aggregate_metric", "row_field"}:
            blocks.append(f"evidence_records[{evidence_id!r}] invalid kind")
        metric_id = str(evidence.get("metric_id") or "").strip()
        if kind == "aggregate_metric" and metric_id not in metrics:
            blocks.append(f"evidence_records[{evidence_id!r}] aggregate metric is invalid")
        if kind == "row_field":
            if not re.fullmatch(r"\d{6}", code6(evidence.get("code"))):
                blocks.append(f"evidence_records[{evidence_id!r}] row field missing code")
            if not _nonempty(evidence.get("field")) or "observed_value" not in evidence:
                blocks.append(f"evidence_records[{evidence_id!r}] row field missing field/value")

    domains = payload.get("domains")
    if not isinstance(domains, dict):
        blocks.append("domains must be an object")
        domains = {}
    for domain in REQUIRED_DOMAINS:
        if domain not in domains or not _nonempty(domains.get(domain)):
            blocks.append(f"domains missing/non-empty requirement: {domain}")
    _validate_missing_not_zero(domains, "domains", blocks)

    catalyst_domain = domains.get("catalyst") if isinstance(domains.get("catalyst"), dict) else {}
    if _is_missing_record(catalyst_domain) and catalyst_domain.get("item_count") is not None:
        blocks.append("unavailable catalyst domain must use item_count=null")
    data_quality = payload.get("data_quality") if isinstance(payload.get("data_quality"), dict) else {}
    if _is_missing_record(catalyst_domain) and data_quality.get("catalyst_item_count") is not None:
        blocks.append("unavailable catalyst data_quality count must be null")

    historical = payload.get("historical_baselines") if isinstance(payload.get("historical_baselines"), dict) else {}
    try:
        historical_sample_count = int(historical.get("sample_count"))
    except (TypeError, ValueError):
        historical_sample_count = -1
        blocks.append("historical_baselines.sample_count must be an integer")
    historical_status = str(historical.get("status") or "").upper()
    if historical_sample_count < 5 and historical_status != "UNAVAILABLE":
        blocks.append("historical baseline under five samples must be UNAVAILABLE")

    universe = payload.get("official_universe")
    if not isinstance(universe, dict):
        blocks.append("official_universe must be an object")
        universe = {}
    raw_codes = universe.get("codes")
    official_codes = [code6(code) for code in raw_codes] if isinstance(raw_codes, list) else []
    if not official_codes or any(not re.fullmatch(r"\d{6}", code) for code in official_codes):
        blocks.append("official_universe.codes must be a non-empty list of six-digit codes")
    if len(official_codes) != len(set(official_codes)):
        blocks.append("official_universe.codes contains duplicates")
    try:
        declared_count = int(universe.get("count"))
    except (TypeError, ValueError):
        declared_count = -1
        blocks.append("official_universe.count must be an integer")
    if declared_count != len(official_codes):
        blocks.append(
            f"official_universe.count mismatch: {declared_count} != {len(official_codes)}"
        )
    universe_source = str(universe.get("source_id") or "").strip()
    if not universe_source or universe_source not in sources:
        blocks.append(f"official_universe.source_id invalid: {universe_source!r}")
    if str(universe.get("eligibility_rule") or "") != DELISTING_HARD_EXCLUSION:
        blocks.append("official_universe.eligibility_rule missing delisting hard exclusion")
    try:
        raw_count = int(universe.get("raw_count"))
    except (TypeError, ValueError):
        raw_count = -1
        blocks.append("official_universe.raw_count must be an integer")
    excluded_items = universe.get("excluded") if isinstance(universe.get("excluded"), list) else []
    excluded_codes = [code6(item.get("code")) for item in excluded_items if isinstance(item, dict)]
    if raw_count != declared_count + len(excluded_codes):
        blocks.append("official_universe raw/eligible/excluded counts do not close")
    if set(excluded_codes) & set(official_codes):
        blocks.append("official_universe excluded codes leak into eligible codes")
    for index, item in enumerate(excluded_items):
        if not isinstance(item, dict) or not _nonempty(item.get("name")) or "退" not in str(item.get("name")):
            blocks.append(f"official_universe.excluded[{index}] lacks delisting name evidence")

    theses = payload.get("theses")
    if not isinstance(theses, list) or len(theses) < 4:
        blocks.append("theses must contain at least four thesis objects")
        theses = theses if isinstance(theses, list) else []
    thesis_ids: set[str] = set()
    for index, thesis in enumerate(theses):
        path = f"theses[{index}]"
        if not isinstance(thesis, dict):
            blocks.append(f"{path} must be an object")
            continue
        thesis_id = str(thesis.get("id") or "").strip()
        if not thesis_id:
            blocks.append(f"{path} missing id")
        elif thesis_id in thesis_ids:
            blocks.append(f"{path} duplicate id: {thesis_id}")
        else:
            thesis_ids.add(thesis_id)
        for field in ("scope", "conclusion", "status", "confidence", "practical_implication", "claim_type", "reasoning_path", "confidence_basis"):
            if not _nonempty(thesis.get(field)):
                blocks.append(f"{path} missing/non-empty field: {field}")
        claim_type = str(thesis.get("claim_type") or "").strip().upper()
        if claim_type not in ALLOWED_CLAIM_TYPES:
            blocks.append(f"{path}.claim_type is invalid")
        if str(thesis.get("scope") or "").strip() not in {"market", "structure", "direction", "risk"}:
            blocks.append(f"{path}.scope is invalid")
        status = str(thesis.get("status") or "").strip().upper()
        if status not in ALLOWED_THESIS_STATUSES:
            blocks.append(f"{path}.status is invalid")
        confidence = str(thesis.get("confidence") or "").strip().upper()
        if confidence not in CONFIDENCE_RANK:
            blocks.append(f"{path}.confidence is invalid")
        reasoning_path = thesis.get("reasoning_path")
        if not isinstance(reasoning_path, list) or len([item for item in reasoning_path if _nonempty(item)]) < 2:
            blocks.append(f"{path}.reasoning_path needs at least two steps")
        confidence_basis = thesis.get("confidence_basis")
        if not isinstance(confidence_basis, dict):
            blocks.append(f"{path}.confidence_basis must be an object")
        else:
            for field in ("supporting_dimensions", "limiting_factors", "baseline_status"):
                if not _nonempty(confidence_basis.get(field)):
                    blocks.append(f"{path}.confidence_basis missing {field}")
            if str(confidence_basis.get("baseline_status") or "").upper() != historical_status:
                blocks.append(f"{path}.confidence_basis baseline_status mismatch")
        dimensions = _validate_references(
            thesis.get("evidence"), f"{path}.evidence", sources, metrics, evidence_records, blocks, expected_effect="SUPPORTS"
        )
        if len(dimensions) < 3:
            blocks.append(f"{path} needs at least three independent evidence dimensions")
        _validate_references(
            thesis.get("counterevidence"),
            f"{path}.counterevidence",
            sources,
            metrics,
            evidence_records,
            blocks,
            expected_effect="CHALLENGES",
            expected_thesis_id=thesis_id,
        )
        if not _nonempty(thesis.get("invalidation")):
            blocks.append(f"{path}.invalidation must be non-empty")
        if confidence == "HIGH" and "catalyst" not in dimensions:
            blocks.append(f"{path} high confidence requires catalyst evidence")
        if historical_sample_count < 5 and str(thesis.get("scope") or "").strip() in {"market", "structure", "risk"}:
            if status != "INSUFFICIENT" or confidence != "LOW":
                blocks.append(f"{path} requires INSUFFICIENT/LOW while historical baseline has fewer than five samples")
        if historical_sample_count < 5 and str(thesis.get("scope") or "").strip() == "direction" and confidence != "LOW":
            blocks.append(f"{path} direction confidence must be LOW while historical baseline has fewer than five samples")

    analysis_inventory = payload.get("analysis_inventory")
    if not isinstance(analysis_inventory, dict):
        blocks.append("analysis_inventory must be an object")
        analysis_inventory = {}
    available_fields = {str(value) for value in analysis_inventory.get("available_fields", []) if _nonempty(value)}
    analyzed_fields = {str(value) for value in analysis_inventory.get("analyzed_fields", []) if _nonempty(value)}
    unused_records = analysis_inventory.get("unused_fields") if isinstance(analysis_inventory.get("unused_fields"), list) else []
    unused_fields = {str(item.get("field")) for item in unused_records if isinstance(item, dict) and _nonempty(item.get("field"))}
    for index, item in enumerate(unused_records):
        if not isinstance(item, dict) or not _nonempty(item.get("field")) or not _nonempty(item.get("reason")):
            blocks.append(f"analysis_inventory.unused_fields[{index}] needs field and reason")
    if not available_fields:
        blocks.append("analysis_inventory.available_fields must be non-empty")
    uncovered_fields = sorted(available_fields - analyzed_fields - unused_fields)
    if uncovered_fields:
        blocks.append(f"analysis_inventory has unexamined fields: {uncovered_fields}")
    if analyzed_fields - available_fields:
        blocks.append(f"analysis_inventory analyzed unknown fields: {sorted(analyzed_fields - available_fields)}")

    signal_audit = payload.get("candidate_signal_audit")
    if not isinstance(signal_audit, list) or not signal_audit:
        blocks.append("candidate_signal_audit must be a non-empty list")
        signal_audit = signal_audit if isinstance(signal_audit, list) else []
    signal_ids: set[str] = set()
    selected_signal_ids: set[str] = set()
    for index, item in enumerate(signal_audit):
        path = f"candidate_signal_audit[{index}]"
        if not isinstance(item, dict):
            blocks.append(f"{path} must be an object")
            continue
        signal_id = str(item.get("signal_id") or "").strip()
        operator = str(item.get("operator") or "").strip()
        status = str(item.get("status") or "").strip().upper()
        input_fields = {str(value) for value in item.get("input_fields", []) if _nonempty(value)} if isinstance(item.get("input_fields"), list) else set()
        if not signal_id or signal_id in signal_ids:
            blocks.append(f"{path}.signal_id missing or duplicate")
        else:
            signal_ids.add(signal_id)
        if operator not in ALLOWED_ANALYSIS_OPERATORS:
            blocks.append(f"{path}.operator is invalid")
        if status not in ALLOWED_SIGNAL_STATUSES:
            blocks.append(f"{path}.status is invalid")
        if not input_fields:
            blocks.append(f"{path}.input_fields must be non-empty")
        if input_fields - available_fields:
            blocks.append(f"{path} references unavailable input fields: {sorted(input_fields - available_fields)}")
        if not _nonempty(item.get("observed_result")) or not _nonempty(item.get("selection_reason")):
            blocks.append(f"{path} needs observed_result and selection_reason")
        if status == "SELECTED":
            selected_signal_ids.add(signal_id)

    conclusion_graph = payload.get("conclusion_graph")
    if not isinstance(conclusion_graph, list) or not conclusion_graph:
        blocks.append("conclusion_graph must contain at least one data-selected conclusion")
        conclusion_graph = conclusion_graph if isinstance(conclusion_graph, list) else []
    conclusion_ids: set[str] = set()
    linked_signal_ids: set[str] = set()
    category_ids: set[str] = set()
    headlines: set[str] = set()
    for index, item in enumerate(conclusion_graph):
        path = f"conclusion_graph[{index}]"
        if not isinstance(item, dict):
            blocks.append(f"{path} must be an object")
            continue
        conclusion_id = str(item.get("id") or "").strip()
        signal_id = str(item.get("signal_id") or "").strip()
        if not conclusion_id or conclusion_id in conclusion_ids:
            blocks.append(f"{path}.id missing or duplicate")
        else:
            conclusion_ids.add(conclusion_id)
        if signal_id not in selected_signal_ids:
            blocks.append(f"{path}.signal_id was not selected by candidate audit")
        elif signal_id in linked_signal_ids:
            blocks.append(f"{path}.signal_id is linked more than once")
        else:
            linked_signal_ids.add(signal_id)
        for field in ("topic", "category_id", "category_label", "scope_label", "angle_label", "headline"):
            if not _nonempty(item.get(field)):
                blocks.append(f"{path}.{field} is required")
        category_id = str(item.get("category_id") or "").strip()
        if category_id:
            category_ids.add(category_id)
        headline = str(item.get("headline") or "").strip()
        if headline in headlines:
            blocks.append(f"{path}.headline is duplicated")
        elif headline:
            headlines.add(headline)
        try:
            priority = int(item.get("priority"))
        except (TypeError, ValueError):
            priority = 0
        if priority < 1 or priority > 100:
            blocks.append(f"{path}.priority must be an integer from 1 to 100")
        if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("data_fingerprint") or "")):
            blocks.append(f"{path}.data_fingerprint must be a 64-character lowercase sha256")
        for field in ("conclusion", "objects", "reasoning_path", "evidence", "counterevidence", "decision_value", "confirmation", "invalidation"):
            if not _nonempty(item.get(field)):
                blocks.append(f"{path} missing/non-empty field: {field}")
        if not isinstance(item.get("objects"), list) or not any(_nonempty(value) for value in item.get("objects", [])):
            blocks.append(f"{path}.objects needs at least one named object")
        reasoning_path = item.get("reasoning_path")
        if not isinstance(reasoning_path, list) or len([value for value in reasoning_path if _nonempty(value)]) < 2:
            blocks.append(f"{path}.reasoning_path needs at least two steps")
        dimensions = _validate_references(item.get("evidence"), f"{path}.evidence", sources, metrics, evidence_records, blocks, expected_effect="SUPPORTS")
        if len(dimensions) < 2:
            blocks.append(f"{path} needs at least two independent evidence dimensions")
        _validate_references(item.get("counterevidence"), f"{path}.counterevidence", sources, metrics, evidence_records, blocks, expected_effect="CHALLENGES")
        for field in ("confirmation", "invalidation"):
            values = item.get(field)
            if not isinstance(values, list) or not any(_nonempty(value) for value in values):
                blocks.append(f"{path}.{field} needs at least one condition")
    if linked_signal_ids != selected_signal_ids:
        blocks.append(f"selected signal/conclusion graph mismatch: unlinked={sorted(selected_signal_ids - linked_signal_ids)} extra={sorted(linked_signal_ids - selected_signal_ids)}")
    if len(conclusion_graph) >= 5 and len(category_ids) < 3:
        blocks.append("conclusion_graph classification collapsed: at least three visible categories are required for five or more nodes")

    section_analysis = payload.get("section_analysis")
    if not isinstance(section_analysis, list) or len(section_analysis) != 16:
        blocks.append("section_analysis must contain exactly chapters 1 through 16")
        section_analysis = section_analysis if isinstance(section_analysis, list) else []
    expected_chapters = set(range(1, 17))
    actual_chapters: set[int] = set()
    seen_section_analyses: set[str] = set()
    forbidden_section_text = (
        "结论：", "依据：", "但要注意：", "上面判断就不成立",
        "默认结论", "固定措辞", "兜底判断", "重要方向", "看成交额、涨停扩散",
        "冻结账本", "冻结预测账本", "本地上一交易日表", "从观察池提取代码",
        "只保留当日涨停池确认样本", "事实来源", "研究动作", "论点状态与证伪条件",
        "次日四分支情景树", "工作流", "脚本", "接口", "字段",
    )
    for index, item in enumerate(section_analysis):
        path = f"section_analysis[{index}]"
        if not isinstance(item, dict):
            blocks.append(f"{path} must be an object")
            continue
        try:
            chapter = int(item.get("chapter"))
        except (TypeError, ValueError):
            chapter = 0
        if chapter not in expected_chapters or chapter in actual_chapters:
            blocks.append(f"{path}.chapter invalid or duplicate: {chapter}")
        actual_chapters.add(chapter)
        heading = str(item.get("heading") or "").strip()
        analysis = str(item.get("analysis") or "").strip()
        facts_text = str(item.get("facts") or "").strip()
        if not heading.startswith(f"{chapter}. "):
            blocks.append(f"{path}.heading does not match chapter")
        if not analysis or not facts_text:
            blocks.append(f"{path} requires non-empty analysis and facts")
        if analysis in seen_section_analyses:
            blocks.append(f"{path}.analysis duplicates another chapter")
        seen_section_analyses.add(analysis)
        hits = [term for term in forbidden_section_text if term in heading or term in analysis or term in facts_text]
        if hits:
            blocks.append(f"{path} contains fixed/process text: {hits}")
        if not re.search(r"\d", facts_text):
            blocks.append(f"{path}.facts must contain current numeric facts")
        source_signal_ids = item.get("source_signal_ids")
        if not isinstance(source_signal_ids, list) or not source_signal_ids:
            blocks.append(f"{path}.source_signal_ids must be non-empty")
        else:
            invalid_signals = [str(value) for value in source_signal_ids if str(value) not in selected_signal_ids]
            if invalid_signals:
                blocks.append(f"{path}.source_signal_ids were not selected: {invalid_signals}")
        expected_analysis_hash = hashlib.sha256(analysis.encode("utf-8")).hexdigest()
        expected_facts_hash = hashlib.sha256(facts_text.encode("utf-8")).hexdigest()
        if item.get("analysis_sha256") != expected_analysis_hash:
            blocks.append(f"{path}.analysis_sha256 mismatch")
        if item.get("facts_sha256") != expected_facts_hash:
            blocks.append(f"{path}.facts_sha256 mismatch")
    if actual_chapters != expected_chapters:
        blocks.append(f"section_analysis chapter coverage mismatch: {sorted(actual_chapters)}")

    scenario_tree = payload.get("scenario_tree")
    scenarios = _scenario_map(scenario_tree)
    for scenario_name in REQUIRED_SCENARIOS:
        scenario = scenarios.get(scenario_name)
        path = f"scenario_tree.{scenario_name}"
        if not isinstance(scenario, dict):
            blocks.append(f"{path} is required")
            continue
        triggers = scenario.get("triggers")
        if not isinstance(triggers, list) or len([item for item in triggers if _nonempty(item)]) < 2:
            blocks.append(f"{path}.triggers needs at least two conditions")
        trigger_evidence = scenario.get("trigger_evidence")
        if not isinstance(trigger_evidence, list) or len(trigger_evidence) < 2:
            blocks.append(f"{path}.trigger_evidence needs at least two traceable conditions")
        else:
            for trigger_index, trigger in enumerate(trigger_evidence):
                trigger_path = f"{path}.trigger_evidence[{trigger_index}]"
                if not isinstance(trigger, dict) or not _nonempty(trigger.get("condition")) or not _nonempty(trigger.get("threshold_basis")):
                    blocks.append(f"{trigger_path} missing condition/threshold_basis")
                    continue
                trigger_type = str(trigger.get("type") or "METRIC").upper()
                if trigger_type == "METRIC":
                    metric_id = str(trigger.get("metric_id") or "").strip()
                    source_id = str(trigger.get("source_id") or "").strip()
                    if metric_id not in metrics or _is_missing_record(metrics.get(metric_id, {})):
                        blocks.append(f"{trigger_path} invalid/unavailable metric")
                    if source_id not in sources:
                        blocks.append(f"{trigger_path} invalid source")
                    if trigger.get("threshold") is None:
                        blocks.append(f"{trigger_path} missing threshold")
                elif trigger_type == "EVENT":
                    if not _nonempty(trigger.get("verification_rule")):
                        blocks.append(f"{trigger_path} event trigger missing verification_rule")
                else:
                    blocks.append(f"{trigger_path} invalid type")
        checkpoints = scenario.get("checkpoints") or scenario.get("observation_checkpoints")
        if not isinstance(checkpoints, dict):
            blocks.append(f"{path}.checkpoints must be an object")
        else:
            for checkpoint in REQUIRED_CHECKPOINTS:
                if not _nonempty(checkpoints.get(checkpoint)):
                    blocks.append(f"{path}.checkpoints missing/non-empty: {checkpoint}")
        if not _nonempty(scenario.get("actions")):
            blocks.append(f"{path}.actions must be non-empty")
        if not _nonempty(scenario.get("invalidation")):
            blocks.append(f"{path}.invalidation must be non-empty")

    watchlist = payload.get("watchlist")
    if not isinstance(watchlist, list) or not watchlist:
        blocks.append("watchlist must be a non-empty list")
        watchlist = watchlist if isinstance(watchlist, list) else []
    official_set = set(official_codes)
    watch_codes: set[str] = set()
    for index, item in enumerate(watchlist):
        path = f"watchlist[{index}]"
        if not isinstance(item, dict):
            blocks.append(f"{path} must be an object")
            continue
        code = code6(item.get("code"))
        if not re.fullmatch(r"\d{6}", code) or code not in official_set:
            blocks.append(f"{path}.code is outside official universe: {code!r}")
        if code in watch_codes:
            blocks.append(f"{path}.code duplicate: {code}")
        watch_codes.add(code)
        for field in ("role", "rationale", "why_now", "linked_claim_ids", "counterevidence", "exclusion_conditions", "cross_sectional_comparison"):
            if not _nonempty(item.get(field)):
                blocks.append(f"{path} missing/non-empty field: {field}")
        dimensions = _validate_references(
            item.get("evidence"), f"{path}.evidence", sources, metrics, evidence_records, blocks, expected_effect="SUPPORTS", expected_code=code
        )
        if len(dimensions) < 3:
            blocks.append(f"{path} needs at least three independent evidence dimensions")
        _validate_references(
            item.get("counterevidence"), f"{path}.counterevidence", sources, metrics, evidence_records, blocks, expected_effect="CHALLENGES", expected_code=code
        )
        linked_claims = item.get("linked_claim_ids")
        if not isinstance(linked_claims, list) or not linked_claims or any(str(claim).strip() not in thesis_ids for claim in linked_claims):
            blocks.append(f"{path}.linked_claim_ids must reference thesis ids")
        comparison = item.get("cross_sectional_comparison")
        if not isinstance(comparison, dict) or not _nonempty(comparison.get("cohort_definition")) or int(comparison.get("cohort_size") or 0) < 2 or not _nonempty(comparison.get("relative_position")):
            blocks.append(f"{path}.cross_sectional_comparison is incomplete")
        if not _nonempty(item.get("confirmation") or item.get("confirmation_conditions")):
            blocks.append(f"{path} missing confirmation conditions")
        if not _nonempty(item.get("invalidation")):
            blocks.append(f"{path} missing invalidation conditions")

    ledger = payload.get("prediction_ledger")
    if not isinstance(ledger, dict):
        blocks.append("prediction_ledger must be an object")
        ledger = {}
    entries = ledger.get("entries")
    if not isinstance(entries, list) or len(entries) < len(theses) + len(watchlist):
        blocks.append("prediction_ledger.entries must cover every thesis and watchlist item")
        entries = entries if isinstance(entries, list) else []
    prediction_ids: set[str] = set()
    stock_codes = {code6(item.get("code")) for item in watchlist if isinstance(item, dict)}
    covered_claims: set[str] = set()
    covered_stocks: set[str] = set()
    for index, entry in enumerate(entries):
        entry_path = f"prediction_ledger.entries[{index}]"
        if not isinstance(entry, dict):
            blocks.append(f"{entry_path} must be an object")
            continue
        prediction_id = str(entry.get("prediction_id") or "").strip()
        if not prediction_id or prediction_id in prediction_ids:
            blocks.append(f"{entry_path} missing/duplicate prediction_id")
        prediction_ids.add(prediction_id)
        object_type = str(entry.get("object_type") or "").strip()
        object_id = str(entry.get("object_id") or "").strip()
        claim_id = str(entry.get("claim_id") or "").strip()
        if object_type not in {"thesis", "stock"}:
            blocks.append(f"{entry_path}.object_type is invalid")
        if object_type == "thesis" and (object_id not in thesis_ids or claim_id != object_id):
            blocks.append(f"{entry_path} thesis object/claim mismatch")
        if object_type == "stock" and (code6(object_id) not in stock_codes or claim_id not in thesis_ids):
            blocks.append(f"{entry_path} stock object/claim mismatch")
        if object_type == "thesis":
            covered_claims.add(object_id)
        if object_type == "stock":
            covered_stocks.add(code6(object_id))
        for field in ("horizon", "premises", "expected_observations", "confirmation_conditions", "invalidation_conditions", "scenario_links", "risk_boundaries"):
            if not _nonempty(entry.get(field)):
                blocks.append(f"{entry_path} missing/non-empty field: {field}")
    if covered_claims != thesis_ids:
        blocks.append("prediction_ledger does not cover every thesis")
    if covered_stocks != stock_codes:
        blocks.append("prediction_ledger does not cover every watchlist stock")
    for field in ("run_id", "as_of", "ledger_version", "frozen_at"):
        if not _nonempty(ledger.get(field)):
            blocks.append(f"prediction_ledger.{field} is required")
    if str(ledger.get("run_id") or "").strip() != run_id:
        blocks.append("prediction_ledger.run_id mismatch")
    if normalize_date(ledger.get("as_of")) != trade_date:
        blocks.append("prediction_ledger.as_of mismatch")
    recorded_hash = str(ledger.get("content_sha256") or "").strip().lower()
    expected_hash = compute_prediction_ledger_hash(
        trade_date,
        theses,
        scenario_tree,
        watchlist,
        entries,
    )
    if not re.fullmatch(r"[0-9a-f]{64}", recorded_hash):
        blocks.append("prediction_ledger.content_sha256 must be a SHA-256 hex digest")
    elif recorded_hash != expected_hash:
        blocks.append(
            "prediction_ledger.content_sha256 mismatch; prediction content is not frozen"
        )
    if not _nonempty(ledger.get("frozen_at")):
        blocks.append("prediction_ledger.frozen_at is required")

    _validate_missing_not_zero(payload, "business_result", blocks)
    return blocks


def build_positive_contract_canary() -> dict[str, Any]:
    date = "20990101"
    run_id = "limit-up-review-contract-canary"
    sources = {
        source_id: {
            "id": source_id,
            "verification_status": "VERIFIED",
            "date": date,
            "as_of": "2099-01-01T15:00:00+08:00",
            "source": f"canary://{source_id}",
        }
        for source_id in ("official_pool", "market", "risk", "fund", "catalyst", "previous")
    }
    metrics = {
        "official_limit_up_count": {"value": 1, "source_id": "official_pool"},
        "first_board_count": {"value": 0, "source_id": "official_pool"},
        "continuation_count": {"value": 1, "source_id": "official_pool"},
        "max_board": {"value": 3, "source_id": "official_pool"},
        "breadth_ratio": {"value": 0.55, "source_id": "market"},
        "failure_rate": {"value": 0.10, "source_id": "risk"},
        "fund_coverage": {"value": 1, "source_id": "fund"},
        "catalyst_count": {"value": 1, "source_id": "catalyst"},
    }

    evidence_records = {
        f"EV-{metric_id}": {
            "id": f"EV-{metric_id}", "kind": "aggregate_metric", "source_id": record["source_id"],
            "metric_id": metric_id, "observed_value": record["value"], "observed_at": "2099-01-01T15:00:00+08:00",
        }
        for metric_id, record in metrics.items()
    }

    def evidence(metric_id: str, source_id: str, dimension: str, *, effect: str = "SUPPORTS", challenge_to: str = "") -> dict[str, str]:
        item = {"metric_id": metric_id, "source_id": source_id, "evidence_id": f"EV-{metric_id}", "dimension": dimension, "interpretation": dimension, "effect": effect}
        if challenge_to:
            item["challenge_to"] = challenge_to
            item["alternative_explanation"] = "canary alternative"
        return item

    theses = []
    for index in range(4):
        theses.append({
            "id": f"TH-CANARY-{index}",
            "scope": ("market", "structure", "direction", "risk")[index],
            "conclusion": f"canary conclusion {index}",
            "status": "SUPPORTED",
            "confidence": "MEDIUM",
            "claim_type": "INFERENCE",
            "reasoning_path": ["fact one", "fact two"],
            "confidence_basis": {"supporting_dimensions": ["structure", "breadth", "capital"], "limiting_factors": ["canary limitation"], "baseline_status": "VERIFIED"},
            "evidence": [
                evidence("continuation_count", "official_pool", "structure"),
                evidence("breadth_ratio", "market", "breadth"),
                evidence("fund_coverage", "fund", "capital"),
            ],
            "counterevidence": [evidence("failure_rate", "risk", "counter_risk", effect="CHALLENGES", challenge_to=f"TH-CANARY-{index}")],
            "invalidation": ["canary invalidation"],
            "practical_implication": "canary action",
        })
    analysis_inventory = {
        "available_fields": ["continuation_count", "breadth_ratio", "failure_rate"],
        "analyzed_fields": ["continuation_count", "breadth_ratio", "failure_rate"],
        "unused_fields": [],
    }
    candidate_signal_audit = [{
        "signal_id": "SIG-CANARY-0",
        "operator": "divergence",
        "input_fields": ["continuation_count", "breadth_ratio", "failure_rate"],
        "status": "SELECTED",
        "observed_result": "canary observed divergence",
        "selection_reason": "canary evidence threshold met",
    }]
    conclusion_graph = []
    for index in range(1):
        conclusion_graph.append({
            "id": f"CG-CANARY-{index}",
            "signal_id": f"SIG-CANARY-{index}",
            "topic": "data-selected canary topic",
            "category_id": "canary_category",
            "category_label": "canary category",
            "scope_label": "canary scope",
            "angle_label": "canary angle",
            "headline": "canary headline",
            "priority": 10,
            "data_fingerprint": "b" * 64,
            "conclusion": f"canary dynamic conclusion {index}",
            "objects": ["canary object"],
            "reasoning_path": ["fact one", "fact two"],
            "evidence": [
                evidence("continuation_count", "official_pool", "structure"),
                evidence("breadth_ratio", "market", "breadth"),
            ],
            "counterevidence": [
                evidence("failure_rate", "risk", "counter_risk", effect="CHALLENGES", challenge_to=f"CG-CANARY-{index}")
            ],
            "decision_value": "canary decision value",
            "confirmation": ["canary confirmation"],
            "invalidation": ["canary invalidation"],
        })
    scenarios = {
        name: {
            "type": name,
            "triggers": ["trigger one", "trigger two"],
            "trigger_evidence": [
                {"type": "METRIC", "condition": "metric one moves", "metric_id": "continuation_count", "source_id": "official_pool", "threshold": 1, "threshold_basis": "canary current value"},
                {"type": "METRIC", "condition": "metric two moves", "metric_id": "failure_rate", "source_id": "risk", "threshold": 0.1, "threshold_basis": "canary current value"},
            ] if name != "exogenous" else [
                {"type": "EVENT", "condition": "event one", "threshold_basis": "canary event", "verification_rule": "verify source"},
                {"type": "EVENT", "condition": "event two", "threshold_basis": "canary event", "verification_rule": "verify source"},
            ],
            "checkpoints": {checkpoint: [f"check {checkpoint}"] for checkpoint in REQUIRED_CHECKPOINTS},
            "actions": ["canary action"],
            "invalidation": ["canary invalidation"],
        }
        for name in REQUIRED_SCENARIOS
    }
    evidence_records["EV-ROW-600000-board"] = {"id": "EV-ROW-600000-board", "kind": "row_field", "source_id": "official_pool", "code": "600000", "field": "连板数", "observed_value": 3, "observed_at": "2099-01-01T15:00:00+08:00"}
    evidence_records["EV-ROW-600000-open"] = {"id": "EV-ROW-600000-open", "kind": "row_field", "source_id": "official_pool", "code": "600000", "field": "炸板次数", "observed_value": 1, "observed_at": "2099-01-01T15:00:00+08:00"}
    evidence_records["EV-ROW-600000-time"] = {"id": "EV-ROW-600000-time", "kind": "row_field", "source_id": "official_pool", "code": "600000", "field": "首次封板时间", "observed_value": "09:30:00", "observed_at": "2099-01-01T15:00:00+08:00"}
    def row_evidence(evidence_id: str, dimension: str, *, effect: str = "SUPPORTS") -> dict[str, str]:
        item = {"evidence_id": evidence_id, "source_id": "official_pool", "dimension": dimension, "interpretation": dimension, "effect": effect}
        if effect == "CHALLENGES":
            item["alternative_explanation"] = "canary counter"
        return item
    watchlist = [{
        "code": "600000",
        "role": "canary_role",
        "rationale": "canary rationale",
        "why_now": "canary why now",
        "linked_claim_ids": ["TH-CANARY-0"],
        "evidence": [
            row_evidence("EV-ROW-600000-board", "structure"),
            row_evidence("EV-ROW-600000-open", "quality"),
            row_evidence("EV-ROW-600000-time", "timing"),
        ],
        "counterevidence": [row_evidence("EV-ROW-600000-open", "stability", effect="CHALLENGES")],
        "exclusion_conditions": ["canary exclusion"],
        "cross_sectional_comparison": {"cohort_definition": "canary cohort", "cohort_size": 2, "relative_position": "canary relative"},
        "confirmation": ["canary confirmation"],
        "invalidation": ["canary invalidation"],
    }]
    entries = []
    for thesis in theses:
        entries.append({"prediction_id": f"P-{thesis['id']}", "object_type": "thesis", "object_id": thesis["id"], "claim_id": thesis["id"], "horizon": "T+1", "premises": ["premise"], "expected_observations": ["expected"], "confirmation_conditions": ["confirm"], "invalidation_conditions": ["invalidate"], "scenario_links": list(REQUIRED_SCENARIOS), "risk_boundaries": ["risk"]})
    entries.append({"prediction_id": "P-STOCK-600000", "object_type": "stock", "object_id": "600000", "claim_id": "TH-CANARY-0", "horizon": "T+1", "premises": ["premise"], "expected_observations": ["expected"], "confirmation_conditions": ["confirm"], "invalidation_conditions": ["invalidate"], "scenario_links": list(REQUIRED_SCENARIOS), "risk_boundaries": ["risk"]})
    section_analysis = []
    for chapter in range(1, 17):
        analysis_text = f"第{chapter}章涨停市场分析{chapter}只。"
        facts_text = f"涨停{chapter}只；连板{chapter}只。"
        section_analysis.append({
            "chapter": chapter,
            "heading": f"{chapter}. canary heading {chapter}",
            "analysis": analysis_text,
            "facts": facts_text,
            "source_signal_ids": ["SIG-CANARY-0"],
            "analysis_sha256": hashlib.sha256(analysis_text.encode("utf-8")).hexdigest(),
            "facts_sha256": hashlib.sha256(facts_text.encode("utf-8")).hexdigest(),
        })
    payload = {
        "schema_version": BUSINESS_RESULT_SCHEMA_VERSION,
        "status": "CLEAN_PASS",
        "date": date,
        "run": {"run_id": run_id, "trade_date": date, "latest_completed_trade_date": date, "as_of": "2099-01-01T15:00:00+08:00", "timezone": "Asia/Shanghai", "generated_at": "2099-01-01T15:00:00+08:00", "current_data_fingerprint": "a" * 64},
        "official_universe": {"source_id": "official_pool", "eligibility_rule": DELISTING_HARD_EXCLUSION, "raw_count": 1, "excluded": [], "codes": ["600000"], "count": 1},
        "sources": sources,
        "metrics": metrics,
        "evidence_records": evidence_records,
        "domains": {domain: {"status": "VERIFIED"} for domain in REQUIRED_DOMAINS},
        "data_quality": {"catalyst_item_count": 1},
        "historical_baselines": {"status": "VERIFIED", "sample_count": 20},
        "theses": theses,
        "analysis_inventory": analysis_inventory,
        "candidate_signal_audit": candidate_signal_audit,
        "conclusion_graph": conclusion_graph,
        "section_analysis": section_analysis,
        "scenario_tree": scenarios,
        "watchlist": watchlist,
        "prediction_ledger": {"ledger_version": "v2", "run_id": run_id, "as_of": "2099-01-01T15:00:00+08:00", "frozen_at": "2099-01-01T15:00:00+08:00", "entries": entries, "content_sha256": ""},
        "blocks_delivery": False,
        "blocks": [],
    }
    payload["prediction_ledger"]["content_sha256"] = compute_prediction_ledger_hash(date, theses, scenarios, watchlist, entries)
    return payload


def _validate_public_entry_contract(
    path: Path,
    text: str,
    require_canonical: bool,
) -> list[str]:
    blocks: list[str] = []
    normalized = text.replace("\\", "/")
    forbidden = {
        "auto command": r"\bcodex_entry\.py\s+auto\b",
        "legacy entry.py": r"(?:^|[\s'\"])scripts/entry\.py\b",
        "legacy limit-up-review.py": r"(?:^|[\s'\"])scripts/limit-up-review\.py\b",
        "OpenClaw dependency": r"\bopenclaw\b",
    }
    for label, pattern in forbidden.items():
        if re.search(pattern, normalized, flags=re.I):
            blocks.append(f"{path} contains forbidden {label}")
    run_lines = [
        line.strip()
        for line in normalized.splitlines()
        if re.search(r"\.py\s+(?:run|auto)\b", line, flags=re.I)
    ]
    for line in run_lines:
        if "scripts/codex_entry.py run" not in line:
            blocks.append(f"{path} contains non-canonical run entry: {line[:180]}")
    canonical_count = len(
        re.findall(r"scripts/codex_entry\.py\s+run\b", normalized, flags=re.I)
    )
    if require_canonical and canonical_count < 1:
        blocks.append(f"{path} missing canonical public entry scripts/codex_entry.py run")
    return blocks


def validate(skill_dir: Path = DEFAULT_SKILL_DIR) -> dict[str, Any]:
    blocks: list[str] = []
    warnings: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    workflow_md = skill_dir / "references" / "workflow.md"
    business_spec_md = skill_dir / "references" / "business_spec.md"
    template_md = skill_dir / "TEMPLATE.md"
    scripts_dir = skill_dir / "scripts"
    required_docs = [skill_md, workflow_md, business_spec_md, template_md]
    required_scripts = [
        "codex_entry.py",
        "entry_limit_up_review.py",
        "collect_limitup_data_strict.py",
        "fetch_push2_fund_flow_strict.py",
        "generate_limit_up_review_strict.py",
        "limit_up_review_final_gate.py",
        "limit_up_review_workflow_contract.py",
    ]
    for path in required_docs:
        if not path.exists() or path.stat().st_size == 0:
            blocks.append(f"missing_or_empty: {path}")
    for name in required_scripts:
        path = scripts_dir / name
        if not path.exists() or path.stat().st_size == 0:
            blocks.append(f"missing_or_empty required script: {path}")

    implementation_markers = {
        "generate_limit_up_review_strict.py": [
            r"def\s+validate_entry_date_gate\b",
            r"def\s+validate_source_freshness\b",
            r"ENTRY_DATE_GATE_NOT_CLEAN",
            r"OFFICIAL_SOURCE_DATE_MISMATCH",
            r"OFFICIAL_UNIVERSE_MISMATCH",
            r"RUNTIME_LATEST_DATE_GATE",
            r"HISTORICAL_MODE_DEFAULT_DELIVERY_ROOT_FORBIDDEN",
            r"def\s+build_business_result\b",
            r"def\s+persist_and_readback_business_result\b",
            r"validate_business_result_payload\(",
            r"business_result\s*,\s*business_blocks\s*=\s*persist_and_readback_business_result\(",
            r"VISIBLE_LATIN_GATE",
            r"DELISTING_HARD_EXCLUSION",
            r"visible_latin_hits",
            r"visible_delisting_hits",
        ],
        "entry_limit_up_review.py": [
            r"def\s+evaluate_date_gate\b",
            r"LATEST_MODE_EXPLICIT_DATE_FORBIDDEN",
            r"LATEST_MODE_STALE_DATE_BLOCKED",
            r"LATEST_COMPLETED_TRADING_DATE",
            r"HISTORICAL_MODE_DEFAULT_DELIVERY_ROOT_FORBIDDEN",
            r"--historical",
            r"LIMITUP_RUN_ID",
            r"LIMITUP_BUSINESS_RESULT",
            r"LIMITUP_HISTORY_DIR",
            r"BUSINESS_DATA_ROOT\s*=\s*WORKSPACE\s*/\s*[\"']business_data[\"']\s*/\s*[\"']limit-up-review[\"']",
            r"memory_dir\s*=\s*task_dir\s*/\s*[\"']memory[\"']\s*if\s*out_dir\s+is\s+not\s+None",
            r"--analysis",
            r"--expected-run-id",
            r"final_gate_result\.json",
            r"validate_business_result_payload\(",
        ],
        "collect_limitup_data_strict.py": [
            r"def\s+validate_bound_preflight\b",
            r"def\s+fetch_official_source_snapshot\b",
            r"OFFICIAL_SOURCE_DATE_MISMATCH",
            r"OFFICIAL_UNIVERSE_MISMATCH",
            r"official_source_qdate",
            r"official_source_codes_sha256",
            r"DELISTING_HARD_EXCLUSION",
            r"eligible_official_codes",
            r"hard_exclusions",
        ],
        "limit_up_review_final_gate.py": [
            r"def\s+validate_entry_date_gate\b",
            r"def\s+validate_source_freshness\b",
            r"ENTRY_DATE_GATE_NOT_CLEAN",
            r"OFFICIAL_SOURCE_DATE_MISMATCH",
            r"OFFICIAL_UNIVERSE_MISMATCH",
            r"RUNTIME_LATEST_DATE_GATE",
            r"HISTORICAL_MODE_DEFAULT_DELIVERY_ROOT_FORBIDDEN",
            r"def\s+validate_business_result_artifact\b",
            r"--analysis",
            r"--expected-run-id",
            r"recomputed_metrics",
            r"validate_business_result_payload\(",
            r"VISIBLE_LATIN_GATE",
            r"DELISTING_HARD_EXCLUSION",
            r"def\s+validate_delisting_hard_exclusion\b",
            r"def\s+validate_visible_auxiliary\b",
        ],
    }
    for name, markers in implementation_markers.items():
        path = scripts_dir / name
        if not path.exists():
            continue
        source = read_text(path)
        for marker in markers:
            if not re.search(marker, source, flags=re.I):
                blocks.append(f"{name} missing current implementation marker: {marker}")

    business_storage_scripts = (
        "entry_limit_up_review.py",
        "generate_limit_up_review_strict.py",
        "generate_limit_up_review_full.py",
        "fetch_push2_fund_flow_fast.py",
    )
    forbidden_memory_namespace_patterns = (
        r"WORKSPACE\s*/\s*[\"']memory[\"']",
        r"\.codex[\\/]memory(?:[\\/]|\b)",
        r"\.codex[\\/]memories(?:[\\/]|\b)",
    )
    for name in business_storage_scripts:
        path = scripts_dir / name
        if not path.exists():
            continue
        source = read_text(path)
        for pattern in forbidden_memory_namespace_patterns:
            if re.search(pattern, source, flags=re.I):
                blocks.append(f"{name} writes or reads forbidden Codex memory namespace: {pattern}")

    for path in required_docs:
        if not path.exists():
            continue
        blocks.extend(
            _validate_public_entry_contract(
                path,
                read_text(path),
                require_canonical=path in {skill_md, workflow_md},
            )
        )

    combined = "\n".join(read_text(path) for path in required_docs if path.exists())
    required_markers = {
        "no_rediscovery": r"NO_REDISCOVERY",
        "locked_entry": r"LOCKED_ENTRY:\s*scripts/codex_entry\.py",
        "current_schema": re.escape(BUSINESS_RESULT_SCHEMA_VERSION),
        "official_universe": r"official_universe|官方候选宇宙|官方涨停池",
        "claim_graph": r"counterevidence|反证",
        "invalidation": r"invalidation|失效条件",
        "practical_implication": r"practical_implication|实战含义|行动含义",
        "scenario_tree": r"strengthen.*rotation.*failure.*exogenous|情景树",
        "prediction_ledger": r"prediction_ledger|预测账本",
        "blocked": r"BLOCKED|阻断",
    }
    for key, pattern in required_markers.items():
        if not re.search(pattern, combined, flags=re.I | re.S):
            blocks.append(f"missing current workflow marker: {key}")

    negative_canary_blocks = validate_business_result_payload({})
    if not negative_canary_blocks:
        blocks.append("negative empty business_result canary did not BLOCK")
    positive_payload = build_positive_contract_canary()
    positive_canary_blocks = validate_business_result_payload(
        positive_payload,
        expected_date="20990101",
        expected_run_id="limit-up-review-contract-canary",
    )
    if positive_canary_blocks:
        blocks.append(f"positive business_result canary failed: {positive_canary_blocks}")

    semantic_negative_canaries: dict[str, dict[str, Any]] = {}
    negative_cases: dict[str, Any] = {}
    missing_run = json.loads(json.dumps(positive_payload))
    missing_run["run"].pop("as_of", None)
    negative_cases["missing_run_as_of"] = missing_run
    baseline_overclaim = json.loads(json.dumps(positive_payload))
    baseline_overclaim["historical_baselines"] = {"status": "UNAVAILABLE", "sample_count": 0}
    baseline_overclaim["theses"][0]["status"] = "SUPPORTED"
    baseline_overclaim["theses"][0]["confidence"] = "MEDIUM"
    negative_cases["baseline_overclaim"] = baseline_overclaim
    missing_ledger = json.loads(json.dumps(positive_payload))
    missing_ledger["prediction_ledger"]["entries"] = []
    missing_ledger["prediction_ledger"]["content_sha256"] = compute_prediction_ledger_hash(trade_date="20990101", theses=missing_ledger["theses"], scenario_tree=missing_ledger["scenario_tree"], watchlist=missing_ledger["watchlist"], entries=[])
    negative_cases["missing_prediction_entries"] = missing_ledger
    broken_row_evidence = json.loads(json.dumps(positive_payload))
    broken_row_evidence["watchlist"][0]["evidence"][0]["evidence_id"] = "EV-ROW-MISSING"
    broken_row_evidence["prediction_ledger"]["content_sha256"] = compute_prediction_ledger_hash(trade_date="20990101", theses=broken_row_evidence["theses"], scenario_tree=broken_row_evidence["scenario_tree"], watchlist=broken_row_evidence["watchlist"], entries=broken_row_evidence["prediction_ledger"]["entries"])
    negative_cases["broken_row_evidence"] = broken_row_evidence
    delisting_leak = json.loads(json.dumps(positive_payload))
    delisting_leak["official_universe"]["raw_count"] = 2
    delisting_leak["official_universe"]["excluded"] = [{"code": "600000", "name": "样例退", "reason": "退市标识"}]
    negative_cases["delisting_code_leak"] = delisting_leak
    for name, candidate in negative_cases.items():
        candidate_blocks = validate_business_result_payload(candidate, expected_date="20990101", expected_run_id="limit-up-review-contract-canary")
        semantic_negative_canaries[name] = {"status": "BLOCKED" if candidate_blocks else "CLEAN_PASS", "blocks": candidate_blocks}
        if not candidate_blocks:
            blocks.append(f"semantic negative canary unexpectedly passed: {name}")

    status = "CLEAN_PASS" if not blocks else "BLOCKED"
    return {
        "status": status,
        "checked_at": now_iso(),
        "skill_dir": str(skill_dir),
        "business_result_schema_version": BUSINESS_RESULT_SCHEMA_VERSION,
        "required_domains": list(REQUIRED_DOMAINS),
        "required_scripts": required_scripts,
        "public_run_entry": "scripts/codex_entry.py run",
        "negative_empty_payload_canary": {
            "status": "BLOCKED" if negative_canary_blocks else "CLEAN_PASS",
            "blocks": negative_canary_blocks,
        },
        "positive_business_result_canary": {
            "status": "CLEAN_PASS" if not positive_canary_blocks else "BLOCKED",
            "blocks": positive_canary_blocks,
        },
        "semantic_negative_canaries": semantic_negative_canaries,
        "blocks": blocks,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", default=str(DEFAULT_SKILL_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate(Path(args.skill_dir))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"])
        for block in result["blocks"]:
            print(f"BLOCKED: {block}")
    return 0 if result["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
