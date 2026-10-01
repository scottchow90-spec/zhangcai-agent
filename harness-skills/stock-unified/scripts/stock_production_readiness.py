#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any


PRODUCTION_POLICY_SCHEMA = "STOCK_PRODUCTION_POLICY_V1"
DATA_GATE_SCHEMA = "STOCK_DATA_GATE_V1"
PRODUCTION_READINESS_SCHEMA = "STOCK_PRODUCTION_READINESS_V1"
RECEIPT_VERSION = 4
MAX_BUSINESS_ARGS = 128
MAX_ARGUMENT_BYTES = 65536
MAX_TOTAL_ARGUMENT_BYTES = 1048576
MAX_PROCESS_OUTPUT_BYTES = 16777216
REQUIRED_DATA_GATE_DIMENSIONS = (
    "identity",
    "effective_trading_date",
    "quote_kline",
    "fundamentals",
    "news_announcements",
    "sector_theme",
    "source_freshness",
)
PRODUCTION_POLICY = {
    "schema": PRODUCTION_POLICY_SCHEMA,
    "profile": "offline_research_signal_production",
    "authority_mode": "single_canonical_runtime",
    "input_validation": "strict_fail_closed",
    "output_validation": "strict_fail_closed",
    "data_gate": "required_for_stock_conclusion",
    "required_data_dimensions": list(REQUIRED_DATA_GATE_DIMENSIONS),
    "contract_drift": "preflight_postflight_and_authorization_fail_closed",
    "persistence": "atomic_replace_with_verified_readback",
    "adapter_persistence": "atomic_path_write_with_verified_readback",
    "concurrency": "bounded_per_workflow_lease",
    "max_business_args": MAX_BUSINESS_ARGS,
    "max_argument_bytes": MAX_ARGUMENT_BYTES,
    "max_total_argument_bytes": MAX_TOTAL_ARGUMENT_BYTES,
    "max_process_output_bytes": MAX_PROCESS_OUTPUT_BYTES,
    "idempotency": "contract_bound_request_fingerprint",
    "observability": "stage_telemetry_and_failure_classification",
    "delivery_authorization": "current_receipt_and_surface_required",
    "execution_boundary": "research_signal_only_no_brokerage_or_orders",
}
FORBIDDEN_ACTIONS = frozenset({
    "buy",
    "sell",
    "order",
    "place-order",
    "submit-order",
    "execute-trade",
    "live-trade",
    "下单",
    "买入",
    "卖出",
    "委托",
    "撤单",
})
FORBIDDEN_OPTIONS = frozenset({
    "--account",
    "--account-id",
    "--broker",
    "--broker-account",
    "--broker-token",
    "--api-key",
    "--api-secret",
    "--secret",
    "--credential",
    "--credentials",
    "--place-order",
    "--submit-order",
    "--live-trading",
    "--enable-auto-trading",
})
FORBIDDEN_STRUCTURED_KEYS = frozenset({
    "account_id",
    "api_key",
    "api_secret",
    "broker_account",
    "broker_token",
    "credential",
    "credentials",
    "live_order",
    "order_request",
    "order_submission",
    "place_order",
    "submit_order",
})
FAILURE_CLASSES = frozenset({
    "NONE",
    "TIMEOUT",
    "RESOURCE_LIMIT",
    "SAFETY_VIOLATION",
    "RUNTIME_ERROR",
    "BUSINESS_REJECTED",
})


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(encoded)


def production_policy_sha256() -> str:
    return canonical_hash(PRODUCTION_POLICY)


def required_shared_runtime_paths(
    *,
    codex_root: Path,
    skills_root: Path,
) -> tuple[Path, ...]:
    return (
        codex_root / "scripts" / "stock_evidence_set.py",
        codex_root / "scripts" / "stock_adapter_io.py",
        codex_root / "scripts" / "lianban_daily_client.py",
        codex_root / "scripts" / "stock_runtime_bootstrap" / "sitecustomize.py",
        codex_root / "scripts" / "stock_runtime_bootstrap" / "tdx_process_guard.py",
        skills_root / "stock-unified" / "scripts" / "stock_contract_catalog.py",
        skills_root / "stock-unified" / "scripts" / "stock_production_readiness.py",
        skills_root / "stock-unified" / "scripts" / "audit_stock_production_readiness.py",
        skills_root / "stock-unified" / "scripts" / "sync_stock_execution_contracts.py",
        skills_root
        / "a-share-hotspot-sentiment-analysis"
        / "scripts"
        / "duanxianxia_client.ps1",
    )


def atomic_write_bytes(path: Path, data: bytes) -> dict[str, Any]:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if temporary_path.read_bytes() != data:
            raise RuntimeError("atomic_write_temporary_readback_mismatch")
        os.replace(temporary_path, path)
        temporary_path = None
        readback = path.read_bytes()
        if readback != data:
            raise RuntimeError("atomic_write_final_readback_mismatch")
        return {
            "path": str(path),
            "size": len(readback),
            "sha256": sha256_bytes(readback),
        }
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def atomic_write_text(path: Path, text: str) -> dict[str, Any]:
    return atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, payload: Any) -> dict[str, Any]:
    return atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )


def _structured_forbidden_fields(node: Any) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            normalized = str(key).strip().casefold().replace("-", "_")
            if normalized in FORBIDDEN_STRUCTURED_KEYS:
                found.append(normalized)
            found.extend(_structured_forbidden_fields(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(_structured_forbidden_fields(value))
    return sorted(set(found))


def _argument_json(argument: str) -> Any | None:
    candidate = argument.split("=", 1)[1] if "=" in argument else argument
    candidate = candidate.strip()
    if not candidate.startswith(("{", "[")):
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def validate_request_arguments(arguments: list[str]) -> list[str]:
    errors: list[str] = []
    if len(arguments) > MAX_BUSINESS_ARGS:
        errors.append("business_argument_count_exceeded")
    total_bytes = 0
    for index, value in enumerate(arguments):
        if not isinstance(value, str):
            errors.append(f"business_argument_not_string:{index}")
            continue
        encoded_size = len(value.encode("utf-8"))
        total_bytes += encoded_size
        if encoded_size > MAX_ARGUMENT_BYTES:
            errors.append(f"business_argument_size_exceeded:{index}")
        if "\x00" in value or any(ord(character) < 32 for character in value):
            errors.append(f"business_argument_control_character:{index}")
        option = value.split("=", 1)[0].strip().casefold()
        if option in FORBIDDEN_OPTIONS:
            errors.append(f"forbidden_execution_option:{option}")
        normalized_value = value.strip().casefold()
        action_value = (
            normalized_value.split("=", 1)[1].strip()
            if "=" in normalized_value
            else normalized_value
        )
        if action_value in FORBIDDEN_ACTIONS:
            errors.append(f"forbidden_execution_action:{action_value}")
        structured = _argument_json(value)
        for key in _structured_forbidden_fields(structured):
            errors.append(f"forbidden_execution_field:{key}")
    if total_bytes > MAX_TOTAL_ARGUMENT_BYTES:
        errors.append("business_argument_total_size_exceeded")
    return sorted(set(errors))


def validate_data_gate(
    payload: Any,
    *,
    skill_id: str,
) -> list[str]:
    if not isinstance(payload, dict):
        return ["data_gate_missing"]
    errors: list[str] = []
    if payload.get("schema") != DATA_GATE_SCHEMA:
        errors.append("data_gate_schema_mismatch")
    if payload.get("status") != "CLEAN_PASS":
        errors.append("data_gate_status_not_clean")
    if payload.get("skill_id") != skill_id:
        errors.append("data_gate_skill_mismatch")
    if payload.get("errors") != []:
        errors.append("data_gate_errors_not_empty")
    if not str(payload.get("evidence_set_id") or "").strip():
        errors.append("data_gate_evidence_set_id_missing")
    effective = str(payload.get("effective_trading_date") or "")
    latest = str(payload.get("latest_required_trading_date") or "")
    try:
        parsed_effective = date.fromisoformat(effective)
        parsed_latest = date.fromisoformat(latest)
    except ValueError:
        errors.append("data_gate_trading_date_invalid")
    else:
        if parsed_effective != parsed_latest:
            errors.append("data_gate_trading_date_stale")
        if parsed_effective > date.today():
            errors.append("data_gate_trading_date_future")
    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, dict):
        errors.append("data_gate_dimensions_invalid")
        dimensions = {}
    extra_dimensions = sorted(set(dimensions) - set(REQUIRED_DATA_GATE_DIMENSIONS))
    for name in extra_dimensions:
        errors.append(f"data_gate_dimension_unknown:{name}")
    for name in REQUIRED_DATA_GATE_DIMENSIONS:
        dimension = dimensions.get(name)
        if not isinstance(dimension, dict):
            errors.append(f"data_gate_dimension_missing:{name}")
            continue
        if dimension.get("status") != "CLEAN_PASS":
            errors.append(f"data_gate_dimension_not_clean:{name}")
        evidence_ids = dimension.get("evidence_ids")
        if (
            not isinstance(evidence_ids, list)
            or not evidence_ids
            or not all(isinstance(item, str) and item.strip() for item in evidence_ids)
            or len(evidence_ids) != len(set(evidence_ids))
        ):
            errors.append(f"data_gate_dimension_evidence_invalid:{name}")
    return sorted(set(errors))


def evaluate_business_result(
    payload: Any,
    *,
    skill_id: str,
    require_data_gate: bool = False,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"ok": False, "errors": ["business_stdout_not_single_json_object"]}
    errors: list[str] = []
    if payload.get("schema") != "STOCK_CANONICAL_BUSINESS_RESULT_V1":
        errors.append("business_schema_mismatch")
    if payload.get("skill_id") != skill_id:
        errors.append("business_skill_id_mismatch")
    if payload.get("status") != "CLEAN_PASS":
        errors.append("business_status_not_clean")
    if payload.get("errors") not in (None, []):
        errors.append("business_errors_not_empty")
    process = payload.get("business_process")
    if not isinstance(process, dict):
        errors.append("business_process_missing")
    else:
        if process.get("returncode") != 0:
            errors.append("business_returncode_not_zero")
        if process.get("timed_out") is not False:
            errors.append("business_timeout_state_invalid")
        if process.get("failure_tokens") != []:
            errors.append("business_failure_tokens_not_empty")
        if process.get("validation_errors") not in (None, []):
            errors.append("business_validation_errors_not_empty")
    binding = payload.get("business_binding")
    if not isinstance(binding, dict):
        errors.append("business_binding_missing")
    else:
        if not str(binding.get("path") or "").strip():
            errors.append("business_binding_path_missing")
        digest = str(binding.get("sha256") or "")
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest.casefold()):
            errors.append("business_binding_sha256_invalid")
    if not isinstance(payload.get("artifacts"), dict):
        errors.append("business_artifacts_invalid")
    for key in _structured_forbidden_fields(payload):
        errors.append(f"forbidden_execution_field:{key}")
    data_gate = payload.get("data_gate")
    if require_data_gate:
        errors.extend(validate_data_gate(data_gate, skill_id=skill_id))
    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "data_gate": data_gate if isinstance(data_gate, dict) else None,
    }


def request_fingerprint(
    skill_id: str,
    contract_sha256: str,
    arguments: list[str],
    execution_purpose: str,
) -> str:
    return canonical_hash({
        "skill_id": skill_id,
        "contract_sha256": contract_sha256,
        "arguments": list(arguments),
        "execution_purpose": execution_purpose,
    })


def classify_failure(
    returncode: int,
    timed_out: bool,
    output_limited: bool,
) -> str:
    if output_limited or returncode == 122:
        return "RESOURCE_LIMIT"
    if timed_out or returncode == 124:
        return "TIMEOUT"
    if returncode == 126:
        return "SAFETY_VIOLATION"
    if returncode == 125:
        return "RUNTIME_ERROR"
    if returncode == 0:
        return "NONE"
    return "BUSINESS_REJECTED"


def validate_receipt_schema(receipt: Any) -> list[str]:
    if not isinstance(receipt, dict):
        return ["receipt_not_object"]
    errors: list[str] = []
    if receipt.get("receipt_version") != RECEIPT_VERSION:
        errors.append("receipt_version_mismatch")
    if receipt.get("execution_purpose") not in {
        "readiness_validation",
        "stock_conclusion",
    }:
        errors.append("receipt_execution_purpose_invalid")
    fingerprint = str(receipt.get("request_fingerprint") or "")
    if len(fingerprint) != 64:
        errors.append("receipt_request_fingerprint_invalid")
    failure_class = receipt.get("failure_class")
    if failure_class not in FAILURE_CLASSES:
        errors.append("receipt_failure_class_invalid")
    if receipt.get("status") == "CLEAN_PASS" and failure_class != "NONE":
        errors.append("receipt_clean_failure_class_mismatch")
    if receipt.get("production_policy_sha256") != production_policy_sha256():
        errors.append("receipt_production_policy_mismatch")
    readiness = receipt.get("production_readiness")
    if not isinstance(readiness, dict):
        errors.append("receipt_production_readiness_missing")
    elif readiness.get("schema") != PRODUCTION_READINESS_SCHEMA:
        errors.append("receipt_production_readiness_schema_mismatch")
    else:
        if readiness.get("status") != receipt.get("status"):
            errors.append("receipt_production_readiness_status_mismatch")
        if readiness.get("execution_purpose") != receipt.get("execution_purpose"):
            errors.append("receipt_production_readiness_purpose_mismatch")
        expected_eligibility = (
            receipt.get("status") == "CLEAN_PASS"
            and receipt.get("execution_purpose") == "stock_conclusion"
        )
        if readiness.get("conclusion_eligible") is not expected_eligibility:
            errors.append("receipt_conclusion_eligibility_mismatch")
        if readiness.get("request_fingerprint") != receipt.get("request_fingerprint"):
            errors.append("receipt_production_request_fingerprint_mismatch")
        if readiness.get("policy_sha256") != production_policy_sha256():
            errors.append("receipt_production_readiness_policy_mismatch")
        if readiness.get("failure_class") != failure_class:
            errors.append("receipt_production_failure_class_mismatch")
        if readiness.get("persistence") != PRODUCTION_POLICY["persistence"]:
            errors.append("receipt_production_persistence_mismatch")
        output_bytes = readiness.get("output_bytes")
        if not isinstance(output_bytes, dict):
            errors.append("receipt_output_bytes_missing")
        else:
            stdout_size = output_bytes.get("stdout")
            stderr_size = output_bytes.get("stderr")
            if (
                not isinstance(stdout_size, int)
                or stdout_size < 0
                or not isinstance(stderr_size, int)
                or stderr_size < 0
            ):
                errors.append("receipt_output_bytes_invalid")
            if output_bytes.get("limit") != MAX_PROCESS_OUTPUT_BYTES:
                errors.append("receipt_output_limit_mismatch")
            if receipt.get("status") == "CLEAN_PASS" and output_bytes.get("limited") is not False:
                errors.append("receipt_clean_output_limit_state_invalid")
        if receipt.get("status") == "CLEAN_PASS" and readiness.get("errors") != []:
            errors.append("receipt_production_readiness_errors_not_empty")
    stages = receipt.get("workflow_telemetry")
    if not isinstance(stages, list) or not stages:
        errors.append("receipt_workflow_telemetry_missing")
    elif any(not isinstance(stage, dict) or not stage.get("name") for stage in stages):
        errors.append("receipt_workflow_telemetry_invalid")
    else:
        names = {str(stage.get("name")) for stage in stages}
        required_names = {
            "request_validation",
            "global_contract_preflight",
            "workflow_queue_wait",
            "binding_validation",
            "tdx_control_scan",
            "evidence_set",
            "supplemental_target_date",
            "supplemental_lianban",
            "business_process",
            "contract_surface_postflight",
            "result_validation",
            "production_gate",
            "runtime_inside_lease",
            "total_runtime_to_receipt",
        }
        for missing in sorted(required_names - names):
            errors.append(f"receipt_workflow_stage_missing:{missing}")
    return sorted(set(errors))
