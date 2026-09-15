#!/usr/bin/env python3
"""Shared stock execution-contract catalog validation and synchronization."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import ast
import copy
import hashlib
import json
import unicodedata
from pathlib import Path
import os
from typing import Any

from stock_production_readiness import (
    PRODUCTION_POLICY,
    required_shared_runtime_paths,
)


MUTABLE_GLOBAL_AGENTS_PATH = Path(__file__).resolve().parents[3] / "AGENTS.md"


def _is_mutable_global_agents_path(value: object) -> bool:
    candidate = Path(str(value))
    try:
        return os.path.samefile(candidate, MUTABLE_GLOBAL_AGENTS_PATH)
    except (FileNotFoundError, OSError):
        return candidate.resolve(strict=False) == MUTABLE_GLOBAL_AGENTS_PATH.resolve(
            strict=False
        )
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SKILLS_ROOT = ROOT.parent
DEFAULT_CATALOG_PATH = ROOT / "references" / "stock_skill_ids.json"
DEFAULT_CONTRACTS_PATH = ROOT / "references" / "stock_execution_contracts.json"
DEFAULT_RUNTIME_PATH = ROOT.parent.parent / "scripts" / "stock_canonical_runtime.py"
FAILURE_OWNER = "global_stock_contract_catalog"
DRIFT_ERROR = "global_contract_catalog_drift"
CATALOG_SCHEMA = "STOCK_SKILL_CATALOG_V2"
CATALOG_AUTHORITY = "canonical_stock_skill_routing_catalog"
DEFAULT_STOCK_SKILL = "stock-research-codex"
EXPECTED_STOCK_SKILL_COUNT = 53
DIRECT_EXECUTION_GUARD = "canonical_stock_legacy_entry_direct_execution_blocked"
FORBIDDEN_BUSINESS_ACTIONS = ["info", "inspect", "selftest"]
DELIVERY_POLICY = {
    "authorization_required": True,
    "allow_receipt_bound_artifact": True,
    "allow_manifest_bound_artifact": True,
    "require_artifact_sha256": True,
    "require_clean_manifest_validation": True,
    "formatted_artifact_requires_template_binding": True,
    "formatted_artifact_requires_validator_binding": True,
}
FIVE_DIMENSION_DATA_REQUIRED_DECISION_GUARDS = (
    '"decision_status": "DATA_REQUIRED"',
    '"decision_status":"DATA_REQUIRED"',
)
STOCK_UNIFIED_REQUIRED_DELIVERABLES = (
    {
        "path": "{stock_data_root}\\selftests\\股票技能生产就绪报告.json",
        "min_size": 100,
    },
    {
        "path": "{stock_data_root}\\selftests\\股票技能生产控制矩阵.json",
        "min_size": 100,
    },
    {
        "path": "{stock_data_root}\\selftests\\股票技能生产验证结果.json",
        "min_size": 100,
    },
    {
        "path": "{stock_data_root}\\selftests\\stock-unified-current.json",
        "min_size": 100,
    },
)
SHORT_TERM_SCORE_CONSUMER_BINDINGS = {
    "stock-unified": (
        "stock-unified/references/short_term_strong_stock_scoring_contract.json",
        "stock-unified/scripts/short_term_strong_score_contract.py",
        "stock-unified/scripts/test_stock_scoring_integrity.py",
        "stock-unified/scripts/stock_workflow_smoke.py",
        "stock-unified/scripts/runtime_truth_audit.py",
        "stock-unified/assets/stock_skill_names_zh.json",
    ),
    "a-share-15d-selection": (
        "stock-unified/references/short_term_strong_stock_scoring_contract.json",
    ),
    "five-dimension-resonance": (
        "stock-unified/references/short_term_strong_stock_scoring_contract.json",
        "stock-unified/scripts/short_term_strong_score_contract.py",
        "a-share-15d-selection/scripts/run_a_share_15d.py",
        "five-dimension-resonance/references/workflow-chain.md",
    ),
    "limit-up-review": (
        "stock-unified/references/short_term_strong_stock_scoring_contract.json",
        "limit-up-review/scripts/generate_limit_up_review_full.py",
    ),
    "lobster-ai": (
        "stock-unified/references/short_term_strong_stock_scoring_contract.json",
        "lobster-ai/scripts/stock_dashboard.py",
    ),
    "tdx-local-hub": (
        "stock-unified/references/short_term_strong_stock_scoring_contract.json",
        "tdx-local-hub/references/source-map.md",
    ),
}


def expected_workflow_identity(skill_id: str) -> dict[str, Any]:
    identity: dict[str, Any] = {
        "owner_skill_id": skill_id,
        "exclusive_owner": True,
        "route_authority": CATALOG_AUTHORITY,
    }
    if skill_id == "big-bull-analysis-scoring-system":
        identity.update({
            "contract_id": "BIG_BULL_30_ITEM_COMPOSITE_V1",
            "canonical_mode": "score-research-composite",
            "legacy_modes": ["score-board", "score", "评分"],
            "legacy_compatibility_flag": "--legacy-five-dimension-compat",
            "absorbed_skill_ids": [
                "feilong-strategy",
                "zhuangjia-capital-monitoring",
            ],
            "component_item_counts": [16, 10, 4],
            "top_level_weights": [40.0, 35.0, 25.0],
            "universe_policy": "tdx_csi300_fixed_reference_v1",
            "cross_board_consistency": "same_identity_same_stock_same_score",
        })
    return identity


def expected_workflow_variants(skill_id: str) -> dict[str, Any]:
    if skill_id != "big-bull-analysis-scoring-system":
        return {}
    return {
        "five_formula_scientific": {
            "contract_id": "BIG_BULL_51_ITEM_FIVE_FORMULA_V1",
            "canonical_backtest_mode": "backtest-five-formula",
            "canonical_score_mode": "score-five-formula",
            "absorbed_skill_ids": [
                "feilong-strategy",
                "youzi-capital-monitoring",
                "zhuangjia-capital-monitoring",
                "jigou-capital-monitoring",
            ],
            "component_item_counts": [16, 10, 5, 4, 16],
            "weight_policy": "learned_no_artificial_floor",
            "universe_policy": "point_in_time_all_a_tradable_v1",
            "terminal_states": [
                "PREDICTIVE_PASS",
                "PREDICTIVE_REJECTED",
                "BLOCKED",
            ],
        }
    }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_contract_path(value: object) -> str:
    """Return the physical path used by the active runtime, not a junction alias."""
    candidate = Path(str(value))
    try:
        return str(candidate.resolve(strict=True))
    except (FileNotFoundError, OSError):
        return str(candidate.resolve(strict=False))


def contract_sha256(contract: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in contract.items()
        if key != "contract_sha256"
    }
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalize_workflow_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()


def load_stock_catalog(
    *,
    catalog_path: Path = DEFAULT_CATALOG_PATH,
    skills_root: Path = DEFAULT_SKILLS_ROOT,
) -> dict[str, Any]:
    payload = json.loads(catalog_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("invalid_stock_skill_catalog")
    if payload.get("schema") != CATALOG_SCHEMA:
        raise ValueError("invalid_stock_skill_catalog_schema")
    if payload.get("authority") != CATALOG_AUTHORITY:
        raise ValueError("invalid_stock_skill_catalog_authority")
    if payload.get("default_skill") != DEFAULT_STOCK_SKILL:
        raise ValueError("invalid_stock_skill_catalog_default")

    skills = payload.get("skills")
    if not isinstance(skills, list) or not all(
        isinstance(item, str) and item for item in skills
    ):
        raise ValueError("invalid_stock_skill_catalog")
    if len(skills) != EXPECTED_STOCK_SKILL_COUNT:
        raise ValueError("stock_skill_count_mismatch")
    if len(set(skills)) != len(skills):
        raise ValueError("duplicate_stock_skill_id")
    if DEFAULT_STOCK_SKILL not in skills:
        raise ValueError("default_stock_skill_missing")

    for skill_id in skills:
        skill_dir = skills_root / skill_id
        if not (skill_dir / "SKILL.md").is_file():
            raise ValueError(f"unknown_catalog_skill_id:{skill_id}")
        if not (skill_dir / "scripts" / "codex_entry.py").is_file():
            raise ValueError(f"missing_catalog_skill_entry:{skill_id}")

    workflow_names = payload.get("workflow_names")
    if not isinstance(workflow_names, dict):
        raise ValueError("invalid_workflow_names")
    if set(workflow_names) != set(skills):
        raise ValueError("workflow_name_skill_set_mismatch")

    normalized_names: dict[str, tuple[str, str]] = {}
    for skill_id in skills:
        names = workflow_names.get(skill_id)
        if not isinstance(names, list) or not names or not all(
            isinstance(name, str) and name.strip() for name in names
        ):
            raise ValueError(f"missing_workflow_names:{skill_id}")
        for name in names:
            normalized = normalize_workflow_name(name)
            previous = normalized_names.get(normalized)
            if previous is not None:
                raise ValueError(
                    "duplicate_normalized_workflow_name:"
                    f"{normalized}:{previous[0]}:{skill_id}"
                )
            normalized_names[normalized] = (skill_id, name)

    return payload


def load_contract_inputs(
    *,
    catalog_path: Path = DEFAULT_CATALOG_PATH,
    contracts_path: Path = DEFAULT_CONTRACTS_PATH,
) -> tuple[dict[str, Any], list[str]]:
    payload = json.loads(contracts_path.read_text(encoding="utf-8"))
    catalog_payload = load_stock_catalog(
        catalog_path=catalog_path,
        skills_root=DEFAULT_SKILLS_ROOT,
    )
    contracts = payload.get("contracts")
    skills = catalog_payload.get("skills")
    if not isinstance(contracts, list):
        raise ValueError("invalid_stock_execution_contracts")
    if not isinstance(skills, list) or not all(isinstance(item, str) for item in skills):
        raise ValueError("invalid_stock_skill_catalog")
    if not all(isinstance(row, dict) for row in contracts):
        raise ValueError("invalid_stock_execution_contract_row")
    contract_ids = [str(row.get("skill_id", "")) for row in contracts]
    if not all(contract_ids):
        raise ValueError("missing_contract_skill_id")
    if len(set(contract_ids)) != len(contract_ids):
        raise ValueError("duplicate_contract_skill_id")
    if set(contract_ids) != set(skills):
        raise ValueError("contract_skill_set_mismatch")
    for row in contracts:
        guard = row.get("workflow_guard")
        skill_id = str(row["skill_id"])
        if not isinstance(guard, dict):
            raise ValueError(f"{skill_id}:workflow_guard_missing")
        if guard.get("direct_legacy_execution") != "blocked":
            raise ValueError(f"{skill_id}:legacy_execution_not_blocked")
        if not isinstance(guard.get("requires_explicit_business_args"), bool):
            raise ValueError(f"{skill_id}:explicit_args_policy_invalid")
        forbidden_actions = guard.get("forbidden_business_actions")
        if (
            not isinstance(forbidden_actions, list)
            or not all(
                isinstance(item, str) and item.strip()
                for item in forbidden_actions
            )
            or len(set(forbidden_actions)) != len(forbidden_actions)
            or forbidden_actions[: len(FORBIDDEN_BUSINESS_ACTIONS)]
            != FORBIDDEN_BUSINESS_ACTIONS
        ):
            raise ValueError(f"{skill_id}:forbidden_business_actions_invalid")
        required_bindings = guard.get("required_bindings")
        if not isinstance(required_bindings, list) or not all(
            isinstance(item, str) and item
            for item in required_bindings
        ):
            raise ValueError(f"{skill_id}:required_bindings_invalid")
    return payload, skills


def declared_primary_business_script(legacy_entry: Path) -> Path | None:
    try:
        tree = ast.parse(legacy_entry.read_text(encoding="utf-8-sig"))
    except (OSError, SyntaxError, UnicodeError):
        return None
    for node in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        if value is None or not any(
            isinstance(target, ast.Name) and target.id == "PRIMARY_REL"
            for target in targets
        ):
            continue
        try:
            relative = ast.literal_eval(value)
        except (ValueError, TypeError):
            return None
        if not isinstance(relative, str) or not relative:
            return None
        return legacy_entry.parents[1] / relative
    return None


def synchronize_contract_payload(
    payload: dict[str, Any],
    skills: list[str],
    *,
    skills_root: Path = DEFAULT_SKILLS_ROOT,
    runtime_path: Path = DEFAULT_RUNTIME_PATH,
) -> list[dict[str, str]]:
    rows = payload.get("contracts")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("invalid_stock_execution_contracts")
    contracts = {str(row.get("skill_id", "")): row for row in rows}
    if len(contracts) != len(rows):
        raise ValueError("duplicate_contract_skill_id")
    if set(contracts) != set(skills):
        raise ValueError("contract_skill_set_mismatch")

    changes: list[dict[str, str]] = []
    current_order = [str(row.get("skill_id", "")) for row in rows]
    if current_order != skills:
        payload["contracts"] = [contracts[skill_id] for skill_id in skills]
        changes.append({
            "skill_id": "stock-unified",
            "field": "contract_order",
            "previous": json.dumps(current_order, ensure_ascii=False),
            "actual": json.dumps(skills, ensure_ascii=False),
        })

    expected_catalog = canonical_contract_path(
        skills_root / "stock-unified" / "references" / "stock_skill_ids.json"
    )
    previous_catalog = str(payload.get("catalog", ""))
    if previous_catalog != expected_catalog:
        payload["catalog"] = expected_catalog
        changes.append({
            "skill_id": "stock-unified",
            "field": "catalog",
            "previous": previous_catalog,
            "actual": expected_catalog,
        })

    def update(row: dict[str, Any], field: str, actual: str, label: str) -> None:
        previous = str(row.get(field, ""))
        if previous == actual:
            return
        row[field] = actual
        changes.append({
            "skill_id": str(row["skill_id"]),
            "field": label,
            "previous": previous,
            "actual": actual,
        })

    runtime_hash = sha256_file(runtime_path)
    catalog_path = (
        skills_root / "stock-unified" / "references" / "stock_skill_ids.json"
    )
    catalog_hash = sha256_file(catalog_path)
    shared_runtime_paths = required_shared_runtime_paths(
        codex_root=skills_root.parent,
        skills_root=skills_root,
    )
    for skill_id in skills:
        row = contracts[skill_id]
        skill_root = skills_root / skill_id
        entry = skill_root / "scripts" / "codex_entry.py"
        if not entry.is_file():
            raise FileNotFoundError(f"missing_facade:{entry}")
        update(row, "facade_sha256", sha256_file(entry), "facade_sha256")
        update(row, "executor_sha256", runtime_hash, "executor_sha256")
        update(row, "catalog_sha256", catalog_hash, "catalog_sha256")
        if row.get("production_policy") != PRODUCTION_POLICY:
            previous_policy = row.get("production_policy")
            row["production_policy"] = copy.deepcopy(PRODUCTION_POLICY)
            changes.append({
                "skill_id": skill_id,
                "field": "production_policy",
                "previous": json.dumps(
                    previous_policy,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "actual": json.dumps(
                    PRODUCTION_POLICY,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            })

        if skill_id == "stock-unified":
            required_artifacts = row.get("required_artifacts")
            if not isinstance(required_artifacts, list):
                raise ValueError("stock-unified:required_artifacts_invalid")
            by_path = {
                item.get("path"): item
                for item in required_artifacts
                if isinstance(item, dict)
            }
            for requirement in STOCK_UNIFIED_REQUIRED_DELIVERABLES:
                path = requirement["path"]
                current = by_path.get(path)
                if current == requirement:
                    continue
                previous = copy.deepcopy(current)
                if current is None:
                    required_artifacts.append(copy.deepcopy(requirement))
                    by_path[path] = required_artifacts[-1]
                else:
                    current.clear()
                    current.update(copy.deepcopy(requirement))
                changes.append({
                    "skill_id": skill_id,
                    "field": f"required_artifacts.{path}",
                    "previous": json.dumps(previous, ensure_ascii=False, sort_keys=True),
                    "actual": json.dumps(requirement, ensure_ascii=False, sort_keys=True),
                })

        if skill_id == "big-bull-analysis-scoring-system":
            command = list(row.get("business_command", []))
            try:
                timeout_index = command.index("--timeout") + 1
            except ValueError as exc:
                raise ValueError("big_bull_business_timeout_missing") from exc
            if timeout_index >= len(command):
                raise ValueError("big_bull_business_timeout_value_missing")
            if command[timeout_index] != "1200":
                previous = str(command[timeout_index])
                command[timeout_index] = "1200"
                row["business_command"] = command
                changes.append({
                    "skill_id": skill_id,
                    "field": "business_command.timeout",
                    "previous": previous,
                    "actual": "1200",
                })
            if row.get("timeout_seconds") != 1260:
                previous = str(row.get("timeout_seconds", ""))
                row["timeout_seconds"] = 1260
                changes.append({
                    "skill_id": skill_id,
                    "field": "timeout_seconds",
                    "previous": previous,
                    "actual": "1260",
                })

        expected_identity = expected_workflow_identity(skill_id)
        if row.get("workflow_identity") != expected_identity:
            previous_identity = row.get("workflow_identity")
            row["workflow_identity"] = copy.deepcopy(expected_identity)
            changes.append({
                "skill_id": skill_id,
                "field": "workflow_identity",
                "previous": json.dumps(
                    previous_identity,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "actual": json.dumps(
                    expected_identity,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            })

        expected_variants = expected_workflow_variants(skill_id)
        if expected_variants and row.get("workflow_variants") != expected_variants:
            previous_variants = row.get("workflow_variants")
            row["workflow_variants"] = copy.deepcopy(expected_variants)
            changes.append({
                "skill_id": skill_id,
                "field": "workflow_variants",
                "previous": json.dumps(
                    previous_variants,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "actual": json.dumps(
                    expected_variants,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            })
        elif not expected_variants and "workflow_variants" in row:
            previous_variants = row.pop("workflow_variants")
            changes.append({
                "skill_id": skill_id,
                "field": "workflow_variants",
                "previous": json.dumps(
                    previous_variants,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "actual": "",
            })

        bindings = row.get("business_bindings", [])
        if not isinstance(bindings, list):
            raise ValueError(f"{skill_id}:invalid_business_bindings")
        filtered_bindings = [
            binding
            for binding in bindings
            if not (
                isinstance(binding, dict)
                and binding.get("path")
                and _is_mutable_global_agents_path(binding["path"])
            )
        ]
        if len(filtered_bindings) != len(bindings):
            row["business_bindings"] = filtered_bindings
            changes.append({
                "skill_id": skill_id,
                "field": "business_bindings.mutable_global_agents",
                "previous": str(len(bindings) - len(filtered_bindings)),
                "actual": "0",
            })
            bindings = filtered_bindings

        for index, binding in enumerate(bindings):
            if not isinstance(binding, dict):
                raise ValueError(f"{skill_id}:invalid_business_binding:{index}")
            previous_path = str(binding.get("path", ""))
            canonical_path = canonical_contract_path(previous_path)
            if previous_path != canonical_path:
                binding["path"] = canonical_path
                changes.append({
                    "skill_id": skill_id,
                    "field": f"business_bindings[{index}].path",
                    "previous": previous_path,
                    "actual": canonical_path,
                })

        unique_bindings: list[dict[str, Any]] = []
        seen_binding_paths: set[str] = set()
        for binding in bindings:
            path_key = os.path.normcase(str(Path(str(binding["path"])).resolve()))
            if path_key in seen_binding_paths:
                changes.append({
                    "skill_id": skill_id,
                    "field": "business_bindings.duplicate",
                    "previous": str(binding["path"]),
                    "actual": "",
                })
                continue
            seen_binding_paths.add(path_key)
            unique_bindings.append(binding)
        if len(unique_bindings) != len(bindings):
            row["business_bindings"] = unique_bindings
            bindings = unique_bindings

        guard = row.get("workflow_guard")
        if not isinstance(guard, dict):
            raise ValueError(f"{skill_id}:workflow_guard_missing")
        required_binding = {
            "big-bull-analysis-scoring-system": "scripts/scoring_mode_gate.py",
            "tdx-local-hub": "scripts/tdx_hub.py",
        }.get(skill_id)
        if required_binding:
            current_required = list(guard.get("required_bindings", []))
            if required_binding not in current_required:
                current_required.append(required_binding)
                guard["required_bindings"] = current_required
                changes.append({
                    "skill_id": skill_id,
                    "field": "workflow_guard.required_bindings",
                    "previous": json.dumps(
                        current_required[:-1],
                        ensure_ascii=False,
                    ),
                    "actual": json.dumps(
                        current_required,
                        ensure_ascii=False,
                    ),
                })
        if row.get("delivery_policy") != DELIVERY_POLICY:
            row["delivery_policy"] = copy.deepcopy(DELIVERY_POLICY)
            changes.append({
                "skill_id": skill_id,
                "field": "delivery_policy",
                "previous": str(row.get("delivery_policy", "")),
                "actual": json.dumps(
                    DELIVERY_POLICY,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            })

        if skill_id == "five-dimension-resonance":
            assertions = row.get("semantic_assertions")
            if not isinstance(assertions, list):
                raise ValueError(f"{skill_id}:semantic_assertions_invalid")
            forbidden = next(
                (
                    assertion
                    for assertion in assertions
                    if isinstance(assertion, dict)
                    and assertion.get("type") == "output_not_contains"
                ),
                None,
            )
            if forbidden is None or not isinstance(forbidden.get("values"), list):
                raise ValueError(f"{skill_id}:output_not_contains_assertion_missing")
            previous_values = list(forbidden["values"])
            missing_guards = [
                value
                for value in FIVE_DIMENSION_DATA_REQUIRED_DECISION_GUARDS
                if value not in previous_values
            ]
            if missing_guards:
                forbidden["values"] = [*previous_values, *missing_guards]
                changes.append({
                    "skill_id": skill_id,
                    "field": "semantic_assertions.data_required_decision_guard",
                    "previous": json.dumps(previous_values, ensure_ascii=False),
                    "actual": json.dumps(forbidden["values"], ensure_ascii=False),
                })

        legacy_entry = skill_root / "scripts" / "legacy_codex_entry.py"
        if not legacy_entry.is_file():
            raise FileNotFoundError(f"missing_legacy_entry:{legacy_entry}")
        if DIRECT_EXECUTION_GUARD not in legacy_entry.read_text(
            encoding="utf-8-sig",
            errors="replace",
        ):
            raise ValueError(f"{skill_id}:legacy_direct_guard_missing")

        required_paths = [
            skill_root / "SKILL.md",
            skill_root / "references" / "workflow.md",
            skill_root / "scripts" / "canonical_business_adapter.py",
            legacy_entry,
            *shared_runtime_paths,
        ]
        primary = declared_primary_business_script(legacy_entry)
        if primary is not None:
            if DIRECT_EXECUTION_GUARD not in primary.read_text(
                encoding="utf-8-sig",
                errors="replace",
            ):
                raise ValueError(f"{skill_id}:primary_direct_guard_missing:{primary}")
            required_paths.append(primary)
        if skill_id == "five-dimension-resonance":
            required_paths.append(
                skills_root
                / "core-mainline-scoring-system"
                / "scripts"
                / "mainline_scoring.py"
            )
        required_paths.extend(
            skills_root / relative
            for relative in SHORT_TERM_SCORE_CONSUMER_BINDINGS.get(skill_id, ())
        )
        for relative in guard.get("required_bindings", []):
            candidate = (skill_root / str(relative)).resolve()
            try:
                candidate.relative_to(skill_root.resolve())
            except ValueError as exc:
                raise ValueError(
                    f"{skill_id}:required_binding_outside_skill:{relative}"
                ) from exc
            required_paths.append(candidate)

        binding_by_path = {
            str(Path(str(binding.get("path", ""))).resolve()): binding
            for binding in bindings
            if isinstance(binding, dict)
        }
        for path in required_paths:
            if not path.is_file():
                raise FileNotFoundError(f"missing_business_binding:{path}")
            resolved = str(path.resolve())
            if resolved not in binding_by_path:
                binding = {"path": resolved, "sha256": sha256_file(path)}
                bindings.append(binding)
                binding_by_path[resolved] = binding
                changes.append({
                    "skill_id": skill_id,
                    "field": f"business_bindings[{len(bindings) - 1}]",
                    "previous": "",
                    "actual": resolved,
                })

        for index, binding in enumerate(bindings):
            if not isinstance(binding, dict):
                raise ValueError(f"{skill_id}:invalid_business_binding:{index}")
            path = Path(str(binding.get("path", "")))
            if not path.is_file():
                raise FileNotFoundError(f"missing_business_binding:{path}")
            previous = str(binding.get("sha256", ""))
            actual = sha256_file(path)
            if previous != actual:
                binding["sha256"] = actual
                changes.append({
                    "skill_id": skill_id,
                    "field": f"business_bindings[{index}].sha256",
                    "previous": previous,
                    "actual": actual,
                })

        supplemental_sources = row.get("supplemental_sources")
        if supplemental_sources is not None:
            if not isinstance(supplemental_sources, dict):
                raise ValueError(f"{skill_id}:invalid_supplemental_sources")
            for source_id, source_policy in supplemental_sources.items():
                if not isinstance(source_policy, dict) or not source_policy.get("client"):
                    continue
                previous_client = str(source_policy["client"])
                canonical_client = canonical_contract_path(previous_client)
                if previous_client != canonical_client:
                    source_policy["client"] = canonical_client
                    changes.append({
                        "skill_id": skill_id,
                        "field": f"supplemental_sources.{source_id}.client",
                        "previous": previous_client,
                        "actual": canonical_client,
                    })
                if source_id == "lianban_daily" and source_policy.get("enabled") is True:
                    previous_mode = source_policy.get("date_mode")
                    if previous_mode is None:
                        canonical_mode = (
                            "exact"
                            if isinstance(source_policy.get("target_date_resolver"), dict)
                            else "latest_available"
                        )
                        source_policy["date_mode"] = canonical_mode
                        changes.append({
                            "skill_id": skill_id,
                            "field": f"supplemental_sources.{source_id}.date_mode",
                            "previous": None,
                            "actual": canonical_mode,
                        })
                    elif previous_mode not in {"exact", "latest_available"}:
                        raise ValueError(
                            f"{skill_id}:invalid_lianban_date_mode:{previous_mode}"
                        )

        update(
            row,
            "contract_sha256",
            contract_sha256(row),
            "contract_sha256",
        )

    payload["contract_count"] = len(rows)
    return changes


def contract_catalog_preflight(
    *,
    catalog_path: Path = DEFAULT_CATALOG_PATH,
    contracts_path: Path = DEFAULT_CONTRACTS_PATH,
    skills_root: Path = DEFAULT_SKILLS_ROOT,
    runtime_path: Path = DEFAULT_RUNTIME_PATH,
    payload: dict[str, Any] | None = None,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    try:
        if payload is None or skills is None:
            loaded_payload, loaded_skills = load_contract_inputs(
                catalog_path=catalog_path,
                contracts_path=contracts_path,
            )
            if payload is None:
                payload = loaded_payload
            if skills is None:
                skills = loaded_skills
        candidate = copy.deepcopy(payload)
        changes = synchronize_contract_payload(
            candidate,
            list(skills),
            skills_root=skills_root,
            runtime_path=runtime_path,
        )
    except Exception as exc:
        return {
            "schema": "STOCK_EXECUTION_CONTRACT_PREFLIGHT_V1",
            "status": "BLOCKED",
            "failure_owner": FAILURE_OWNER,
            "errors": ["global_contract_catalog_invalid"],
            "error_detail": f"{type(exc).__name__}:{exc}",
            "changed_field_count": 0,
            "changed_skill_count": 0,
            "changes": [],
        }

    blocked = bool(changes)
    return {
        "schema": "STOCK_EXECUTION_CONTRACT_PREFLIGHT_V1",
        "status": "BLOCKED" if blocked else "CLEAN_PASS",
        "failure_owner": FAILURE_OWNER if blocked else None,
        "errors": [DRIFT_ERROR] if blocked else [],
        "changed_field_count": len(changes),
        "changed_skill_count": len({row["skill_id"] for row in changes}),
        "changes": changes,
    }
