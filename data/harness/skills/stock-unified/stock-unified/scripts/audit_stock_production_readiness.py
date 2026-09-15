#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stock_contract_catalog import (
    STOCK_UNIFIED_REQUIRED_DELIVERABLES,
    contract_catalog_preflight,
    contract_sha256,
    load_stock_catalog,
)
from stock_production_readiness import (
    PRODUCTION_POLICY,
    required_shared_runtime_paths,
    sha256_file,
)


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
CODEX_ROOT = ROOT.parents[1]
CATALOG = ROOT / "references" / "stock_skill_ids.json"
CONTRACTS = ROOT / "references" / "stock_execution_contracts.json"
RUNTIME = CODEX_ROOT / "scripts" / "stock_canonical_runtime.py"
CONTROL_NAMES = (
    "required_files_complete",
    "canonical_facade_bound",
    "contract_hash_current",
    "catalog_hash_current",
    "runtime_hash_current",
    "business_command_valid",
    "business_cwd_valid",
    "business_timeout_bounded",
    "semantic_assertions_present",
    "business_bindings_complete",
    "shared_runtime_bindings_complete",
    "adapter_atomic_output",
    "strict_input_output_validation",
    "strict_data_gate",
    "atomic_persistence",
    "contract_bound_idempotency",
    "stage_observability",
    "current_delivery_authorization",
    "read_only_trading_boundary",
)


def audit_skill(contract: dict[str, Any], catalog_sha256: str) -> dict[str, Any]:
    skill_id = str(contract.get("skill_id") or "")
    skill_root = SKILLS_ROOT / skill_id
    errors: list[str] = []
    adapter = skill_root / "scripts" / "canonical_business_adapter.py"
    required_files = (
        skill_root / "SKILL.md",
        skill_root / "references" / "workflow.md",
        skill_root / "scripts" / "codex_entry.py",
        adapter,
        skill_root / "scripts" / "legacy_codex_entry.py",
    )
    for path in required_files:
        if not path.is_file():
            errors.append(f"required_file_missing:{path}")
    if contract.get("production_policy") != PRODUCTION_POLICY:
        errors.append("production_policy_mismatch")
    if contract.get("catalog_sha256") != catalog_sha256:
        errors.append("catalog_hash_mismatch")
    if contract.get("contract_sha256") != contract_sha256(contract):
        errors.append("contract_hash_mismatch")
    entry = skill_root / "scripts" / "codex_entry.py"
    if entry.is_file():
        source = entry.read_text(encoding="utf-8-sig", errors="replace")
        if "stock_canonical_runtime" not in source or "facade_main" not in source:
            errors.append("canonical_facade_binding_missing")
        if contract.get("facade_sha256") != sha256_file(entry):
            errors.append("facade_hash_mismatch")
    if contract.get("executor_sha256") != sha256_file(RUNTIME):
        errors.append("executor_hash_mismatch")
    adapter_atomic_output = False
    if adapter.is_file():
        adapter_source = adapter.read_text(encoding="utf-8-sig", errors="replace")
        adapter_atomic_output = (
            "from stock_adapter_io import" in adapter_source
            and "enable_atomic_path_writes()" in adapter_source
        )
    if not adapter_atomic_output:
        errors.append("adapter_atomic_output_missing")
    command = contract.get("business_command")
    if not isinstance(command, list) or not command or not all(
        isinstance(item, str) and item for item in command
    ):
        errors.append("business_command_invalid")
    if not isinstance(contract.get("cwd"), str) or not contract.get("cwd"):
        errors.append("business_cwd_invalid")
    timeout = contract.get("timeout_seconds")
    if not isinstance(timeout, int) or not 1 <= timeout <= 3600:
        errors.append("business_timeout_invalid")
    assertions = contract.get("semantic_assertions")
    if not isinstance(assertions, list) or not assertions:
        errors.append("semantic_assertions_missing")
    required_artifacts = contract.get("required_artifacts")
    if not isinstance(required_artifacts, list):
        errors.append("required_artifacts_invalid")
        required_artifacts = []
    if skill_id == "stock-unified":
        required_artifact_paths = {
            item.get("path")
            for item in required_artifacts
            if isinstance(item, dict)
        }
        for requirement in STOCK_UNIFIED_REQUIRED_DELIVERABLES:
            if requirement["path"] not in required_artifact_paths:
                errors.append(
                    f"delivery_artifact_binding_missing:{requirement['path']}"
                )
    bindings = contract.get("business_bindings")
    binding_paths: set[str] = set()
    if not isinstance(bindings, list) or not bindings:
        errors.append("business_bindings_missing")
        bindings = []
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            errors.append(f"business_binding_invalid:{index}")
            continue
        path = Path(str(binding.get("path") or "")).resolve()
        path_key = str(path).casefold()
        if path_key in binding_paths:
            errors.append(f"business_binding_duplicate:{path}")
        binding_paths.add(path_key)
        if not path.is_file():
            errors.append(f"business_binding_missing:{path}")
        elif binding.get("sha256") != sha256_file(path):
            errors.append(f"business_binding_drift:{path}")
    shared_paths = {
        str(path.resolve()).casefold()
        for path in required_shared_runtime_paths(
            codex_root=CODEX_ROOT,
            skills_root=SKILLS_ROOT,
        )
    }
    for missing in sorted(shared_paths - binding_paths):
        errors.append(f"shared_runtime_binding_missing:{missing}")
    policy = contract.get("production_policy")
    policy_clean = policy == PRODUCTION_POLICY
    policy_values = policy if isinstance(policy, dict) else {}
    controls = {
        "required_files_complete": not any(
            error.startswith("required_file_missing:") for error in errors
        ),
        "canonical_facade_bound": entry.is_file() and not any(
            error in {"canonical_facade_binding_missing", "facade_hash_mismatch"}
            for error in errors
        ),
        "contract_hash_current": "contract_hash_mismatch" not in errors,
        "catalog_hash_current": "catalog_hash_mismatch" not in errors,
        "runtime_hash_current": "executor_hash_mismatch" not in errors,
        "business_command_valid": "business_command_invalid" not in errors,
        "business_cwd_valid": "business_cwd_invalid" not in errors,
        "business_timeout_bounded": "business_timeout_invalid" not in errors,
        "semantic_assertions_present": "semantic_assertions_missing" not in errors,
        "business_bindings_complete": not any(
            error.startswith((
                "business_bindings_missing",
                "business_binding_invalid:",
                "business_binding_duplicate:",
                "business_binding_missing:",
                "business_binding_drift:",
            ))
            for error in errors
        ),
        "shared_runtime_bindings_complete": not any(
            error.startswith("shared_runtime_binding_missing:") for error in errors
        ),
        "adapter_atomic_output": adapter_atomic_output and policy_clean and (
            policy_values.get("adapter_persistence")
            == "atomic_path_write_with_verified_readback"
        ),
        "strict_input_output_validation": policy_clean and (
            policy_values.get("input_validation") == "strict_fail_closed"
            and policy_values.get("output_validation") == "strict_fail_closed"
        ),
        "strict_data_gate": policy_clean and (
            policy_values.get("data_gate") == "required_for_stock_conclusion"
            and policy_values.get("required_data_dimensions")
            == PRODUCTION_POLICY["required_data_dimensions"]
        ),
        "atomic_persistence": policy_clean and (
            policy_values.get("persistence") == "atomic_replace_with_verified_readback"
        ),
        "contract_bound_idempotency": policy_clean and (
            policy_values.get("idempotency") == "contract_bound_request_fingerprint"
        ),
        "stage_observability": policy_clean and (
            policy_values.get("observability")
            == "stage_telemetry_and_failure_classification"
        ),
        "current_delivery_authorization": policy_clean and (
            policy_values.get("delivery_authorization")
            == "current_receipt_and_surface_required"
        ) and not any(
            error.startswith((
                "required_artifacts_invalid",
                "delivery_artifact_binding_missing:",
            ))
            for error in errors
        ),
        "read_only_trading_boundary": policy_clean and (
            policy_values.get("execution_boundary")
            == "research_signal_only_no_brokerage_or_orders"
        ),
    }
    for name in CONTROL_NAMES:
        if not controls.get(name):
            errors.append(f"production_control_failed:{name}")
    return {
        "skill_id": skill_id,
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "required_file_count": len(required_files),
        "binding_count": len(bindings),
        "control_count": len(CONTROL_NAMES),
        "passed_control_count": sum(bool(controls[name]) for name in CONTROL_NAMES),
        "controls": controls,
        "errors": sorted(set(errors)),
    }


def build_audit() -> dict[str, Any]:
    catalog = load_stock_catalog(catalog_path=CATALOG, skills_root=SKILLS_ROOT)
    contract_payload = json.loads(CONTRACTS.read_text(encoding="utf-8-sig"))
    skills = catalog["skills"]
    contracts = contract_payload.get("contracts", [])
    rows = [audit_skill(contract, sha256_file(CATALOG)) for contract in contracts]
    errors: list[str] = []
    if len(skills) != 53:
        errors.append("catalog_count_mismatch")
    if len(contracts) != 53:
        errors.append("contract_count_mismatch")
    if [row.get("skill_id") for row in contracts] != skills:
        errors.append("catalog_contract_order_mismatch")
    preflight = contract_catalog_preflight(
        catalog_path=CATALOG,
        contracts_path=CONTRACTS,
        skills_root=SKILLS_ROOT,
        runtime_path=RUNTIME,
    )
    if preflight.get("status") != "CLEAN_PASS":
        errors.extend(str(item) for item in preflight.get("errors", []))
    blocked = [row for row in rows if row["status"] != "CLEAN_PASS"]
    errors.extend(
        f"{row['skill_id']}:{error}"
        for row in blocked
        for error in row["errors"]
    )
    missing_count = sum(
        error.startswith((
            "required_file_missing:",
            "business_binding_missing:",
            "shared_runtime_binding_missing:",
        ))
        for row in rows
        for error in row["errors"]
    )
    drift_count = sum(
        "mismatch" in error or "drift" in error
        for row in rows
        for error in row["errors"]
    )
    total_control_count = sum(row["control_count"] for row in rows)
    passed_control_count = sum(row["passed_control_count"] for row in rows)
    return {
        "schema": "STOCK_PRODUCTION_READINESS_AUDIT_V1",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "catalog": str(CATALOG),
        "contracts": str(CONTRACTS),
        "catalog_count": len(skills),
        "contract_count": len(contracts),
        "compliant_count": len(rows) - len(blocked),
        "missing_count": missing_count,
        "drift_count": drift_count,
        "total_control_count": total_control_count,
        "passed_control_count": passed_control_count,
        "contract_preflight": preflight,
        "skills": rows,
        "errors": sorted(set(errors)),
    }


def main() -> int:
    payload = build_audit()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
