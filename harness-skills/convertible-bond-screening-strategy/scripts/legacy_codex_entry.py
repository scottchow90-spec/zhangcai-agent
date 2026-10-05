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
import os
import struct
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime_utils import (
    GenerationPaths,
    RunInProgressError,
    RunLock,
    atomic_write_bytes,
    atomic_write_json,
    build_generation_paths,
    run_process_tree,
)
from validate_delivery_contract import (
    DELIVERY_SCHEMA,
    SCORE_COMPONENT_IDS,
    SCORE_COMPONENT_WEIGHTS,
    SCORE_CRITERIA,
    SCORE_MODEL_VERSION,
    DeliveryContractError,
    build_delivery_payload,
)
_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_tdx_root


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
RUN = (Path(__import__("os").environ["ONESTOCK_STOCK_DATA_ROOT"]) / "convertible-bond-screening-strategy" if __import__("os").environ.get("ONESTOCK_STOCK_DATA_ROOT") else ROOT / "run")
SELFTEST_STANDALONE = RUN / "selftests" / "selftest_standalone.json"
STATUS = RUN / "skill_status.json"
STATUS_READBACK = RUN / "status_readback.json"
RUN_STATE = RUN / "run_state.json"
LATEST_SUMMARY = RUN / "latest_summary.json"
RUN_LOCK = RUN / ".run.lock"
SELFTEST_LOCK = RUN / ".selftest.lock"

DAY_RECORD_SIZE = 32
TDX_ROOT = resolve_tdx_root()
DAY_INPUT_SCHEMA = "CONVERTIBLE-BOND-DAY-INPUT-MANIFEST-2"
DAY_INPUT_BINDING_MODE = "immutable_tail_snapshot_pre_and_post"
DAY_INPUT_TAIL_RECORD_LIMIT = 260
DAY_INPUT_STABLE_CAPTURE_PASSES = 2
TDX_DAY_UPDATE_RACE = "TDX_DAY_UPDATE_RACE"
MARKET_MAX_ATTEMPTS = 3
MARKET_RETRY_DELAYS_SECONDS = (1.0, 3.0)
RETRYABLE_CHILD_FAILURE_SCHEMAS = {
    "run_convertible_bond_screening.py": "CONVERTIBLE-BOND-SCAN-FAILURE-1",
    "verify_convertible_bond_screening.py": "CONVERTIBLE-BOND-VERIFY-FAILURE-1",
    "independent_heat_verifier.py": "CONVERTIBLE-BOND-VERIFY-FAILURE-1",
}

STATE_TARGETS = (
    (RUN_STATE, "CONVERTIBLE-BOND-SCREENING-RUN-STATE-1"),
    (STATUS, "CONVERTIBLE-BOND-SCREENING-SKILL-STATUS-3"),
    (STATUS_READBACK, "CONVERTIBLE-BOND-SCREENING-STATUS-READBACK-3"),
)

EXPECTED_SCORE_COMPONENT_IDS = SCORE_COMPONENT_IDS
EXPECTED_SCORE_COMPONENT_WEIGHTS = SCORE_COMPONENT_WEIGHTS
EXPECTED_SCORE_COMPONENT_WEIGHT_BY_ID = dict(SCORE_CRITERIA)

EXPECTED_TOP1_SKILLS = (
    "stock-hard-gate",
    "tdx-local-hub",
    "golden-ignition",
    "feilong-strategy",
    "youzi-capital-monitoring",
    "big-bull-analysis-scoring-system",
)
EXPECTED_C9_NORMALIZATION_RULE = "30% industry percentile heat + 40% highest concept heat score + 30% underlying trend"
EXPECTED_HARD_EXCLUSION_CODES = {
    "bond_name_z_prefix",
    "daily_gain_ge_10_and_volume_ratio_gt_4",
    "scr90_change_1d_unavailable",
    "scr90_change_1d_positive",
    "turnover_5d_gt_1000",
    "bond_close_gt_350",
    "early_redemption_announced",
    "early_redemption_unverified",
}


class ChildInvocationError(RuntimeError):
    def __init__(
        self,
        script: str,
        returncode: int,
        stdout: str | None,
        stderr: str | None,
        elapsed_seconds: float,
    ) -> None:
        diagnostic = compact_child_diagnostic(stdout, stderr)
        suffix = f"; child_diagnostic={diagnostic}" if diagnostic else ""
        super().__init__(f"{script} failed with exit code {returncode}{suffix}")
        self.script = script
        self.returncode = returncode
        self.stdout = stdout or ""
        self.stderr = stderr or ""
        self.elapsed_seconds = elapsed_seconds


class DayInputUpdateRaceError(RuntimeError):
    def __init__(self, message: str, event: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.event = event


def emit_best_effort(
    value: str,
    *,
    end: str = "\n",
    stream: Any | None = None,
) -> bool:
    """Emit diagnostics without allowing a detached caller to poison persisted work."""

    target = sys.stdout if stream is None else stream
    try:
        print(value, end=end, file=target)
    except (OSError, UnicodeError, ValueError):
        return False
    return True


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "size_bytes": path.stat().st_size, "sha256": sha256(path)}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def publish_latest_summary(
    source: Path,
    *,
    run_id: str,
    market_attempt: int,
) -> dict[str, Any]:
    if not source.is_file() or source.stat().st_size <= 0:
        raise RuntimeError(f"generation summary missing or empty: {source}")
    source_payload = load_json(source)
    if source_payload.get("run_id") != run_id:
        raise RuntimeError("generation summary run_id mismatch")
    if source_payload.get("market_attempt") != market_attempt:
        raise RuntimeError("generation summary market_attempt mismatch")

    source_bytes = source.read_bytes()
    source_size = len(source_bytes)
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    atomic_write_bytes(LATEST_SUMMARY, source_bytes)

    published_bytes = LATEST_SUMMARY.read_bytes()
    published_payload = load_json(LATEST_SUMMARY)
    published_size = LATEST_SUMMARY.stat().st_size
    published_sha256 = hashlib.sha256(published_bytes).hexdigest()
    if published_bytes != source_bytes:
        raise RuntimeError("latest summary byte readback mismatch")
    if published_size != source_size:
        raise RuntimeError("latest summary size readback mismatch")
    if published_sha256 != source_sha256:
        raise RuntimeError("latest summary SHA-256 readback mismatch")
    if published_payload.get("run_id") != run_id:
        raise RuntimeError("latest summary run_id readback mismatch")
    if published_payload.get("market_attempt") != market_attempt:
        raise RuntimeError("latest summary market_attempt readback mismatch")
    return {
        "path": str(LATEST_SUMMARY.resolve()),
        "size_bytes": published_size,
        "sha256": published_sha256,
        "run_id": run_id,
        "market_attempt": market_attempt,
    }


def prepare_generation(run_id: str, market_attempt: int) -> GenerationPaths:
    paths = build_generation_paths(RUN, run_id, market_attempt)
    paths.top1_run_logs.mkdir(parents=True, exist_ok=False)
    return paths


def require_new_targets(paths: tuple[Path, ...]) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        raise RuntimeError(f"generation target already exists: {existing}")


def bind_json_generation(path: Path, run_id: str, market_attempt: int) -> None:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"generation output missing or empty: {path}")
    payload = load_json(path)
    if payload.get("run_id") != run_id:
        raise RuntimeError(f"generation output run_id mismatch: {path}")
    declared = [
        payload[key]
        for key in ("market_attempt", "scan_attempt", "attempt")
        if key in payload
    ]
    if declared and any(
        isinstance(value, bool) or not isinstance(value, int) or value != market_attempt
        for value in declared
    ):
        raise RuntimeError(f"generation output market_attempt mismatch: {path}")
    if payload.get("market_attempt") != market_attempt:
        payload["market_attempt"] = market_attempt
        atomic_write_json(path, payload)
    persisted = load_json(path)
    if (
        persisted.get("run_id") != run_id
        or persisted.get("market_attempt") != market_attempt
        or path.stat().st_size <= 0
    ):
        raise RuntimeError(f"generation output readback mismatch: {path}")


def invoke_generation_stage(
    script: str,
    args: list[str],
    *,
    output_paths: tuple[Path, ...],
    run_id: str,
    attempt: int,
    timeout_seconds: int,
) -> float:
    require_new_targets(output_paths)
    elapsed = invoke(script, args, timeout_seconds=timeout_seconds)
    for path in output_paths:
        bind_json_generation(path, run_id, attempt)
    return elapsed


def state_documents(
    base: dict[str, Any],
    targets: tuple[tuple[Path, str], ...] | None = None,
) -> list[tuple[Path, dict[str, Any]]]:
    """Build the three state documents with target-specific schemas.

    Schema is assigned last so a caller-supplied or inherited schema can never
    replace the schema required by the destination file.
    """

    selected = targets or STATE_TARGETS
    return [(path, {**base, "schema": schema}) for path, schema in selected]


def write_state_transition(
    base: dict[str, Any],
    targets: tuple[tuple[Path, str], ...] | None = None,
) -> tuple[bool, list[str]]:
    """Best-effort all-target state transition without leaking write errors."""

    errors: list[str] = []
    for path, payload in state_documents(base, targets):
        try:
            atomic_write_json(path, payload)
        except Exception as exc:
            errors.append(f"{path}:{type(exc).__name__}:{exc}")
    return not errors, errors


def walk_path_nodes(node: Any):
    if isinstance(node, dict) and "path" in node:
        yield node
        return
    if isinstance(node, dict):
        for value in node.values():
            yield from walk_path_nodes(value)


def current_source_checks(result: dict[str, Any]) -> tuple[bool, list[dict[str, Any]], str | None]:
    checks: list[dict[str, Any]] = []
    nodes = list(walk_path_nodes(result.get("source_files") or {}))
    schema_complete = len(nodes) == 9
    for node in nodes:
        path = Path(str(node.get("path") or ""))
        expected_size = node.get("size")
        expected_hash = node.get("sha256")
        valid_schema = (
            isinstance(expected_size, int)
            and isinstance(expected_hash, str)
            and len(expected_hash) == 64
        )
        actual = artifact(path) if path.is_file() else {"path": str(path), "missing": True}
        ok = bool(
            valid_schema
            and path.is_file()
            and actual.get("size_bytes") == expected_size
            and actual.get("sha256") == expected_hash
        )
        schema_complete &= valid_schema
        checks.append({"ok": ok, "expected": node, "actual": actual})
    benchmark_date: str | None = None
    try:
        master = Path(result["source_files"]["convertible_bond_master"]["path"])
        benchmark = master.parents[2] / "vipdoc" / "sh" / "lday" / "sh999999.day"
        if benchmark.stat().st_size >= 32 and benchmark.stat().st_size % 32 == 0:
            with benchmark.open("rb") as handle:
                handle.seek(-32, 2)
                benchmark_date = f"{struct.unpack('<I', handle.read(4))[0]:08d}"
    except (KeyError, OSError, ValueError):
        benchmark_date = None
    return bool(schema_complete and checks and all(item["ok"] for item in checks)), checks, benchmark_date


def binding_matches(binding: dict[str, Any], path: Path) -> bool:
    expected_size = binding.get("size_bytes", binding.get("size"))
    return bool(
        path.is_file()
        and int(expected_size if expected_size is not None else -1) == path.stat().st_size
        and binding.get("sha256") == sha256(path)
    )


def latest_local_benchmark_date() -> str:
    benchmark = TDX_ROOT / "vipdoc" / "sh" / "lday" / "sh999999.day"
    size = benchmark.stat().st_size
    if size < DAY_RECORD_SIZE or size % DAY_RECORD_SIZE != 0:
        raise RuntimeError(f"invalid local benchmark DAY file: {benchmark}")
    with benchmark.open("rb") as handle:
        handle.seek(-DAY_RECORD_SIZE, 2)
        raw_date = handle.read(4)
    if len(raw_date) != 4:
        raise RuntimeError("cannot read latest local benchmark date")
    value = f"{struct.unpack('<I', raw_date)[0]:08d}"
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError as exc:
        raise RuntimeError(f"invalid latest local benchmark date: {value}") from exc
    return value


def binding_targets_and_matches(binding: Any, path: Path) -> bool:
    if not isinstance(binding, dict):
        return False
    try:
        bound_path = Path(str(binding.get("path") or "")).resolve()
        return bound_path == path.resolve() and binding_matches(binding, path)
    except (OSError, TypeError, ValueError):
        return False


def top1_evidence_binding_checks(
    top1: dict[str, Any], paths: GenerationPaths
) -> dict[str, bool]:
    checks = top1.get("checks")
    result_artifacts = top1.get("result_artifacts")
    skill_runs = top1.get("skill_runs")
    expected_results = {
        "golden": paths.top1_golden,
        "feilong": paths.top1_feilong,
        "bigbull": paths.top1_bigbull,
    }
    result_artifacts_exact = bool(
        isinstance(result_artifacts, dict)
        and set(result_artifacts) == set(expected_results)
        and all(
            binding_targets_and_matches(result_artifacts.get(name), path)
            for name, path in expected_results.items()
        )
    )
    skill_runs_exact = bool(
        isinstance(skill_runs, list)
        and len(skill_runs) == len(EXPECTED_TOP1_SKILLS)
        and [run.get("skill") for run in skill_runs if isinstance(run, dict)]
        == list(EXPECTED_TOP1_SKILLS)
    )
    skill_run_bindings_current = skill_runs_exact
    if skill_runs_exact:
        for run in skill_runs:
            skill = str(run["skill"])
            expected_bindings = {
                "entry": ROOT.parent / skill / "scripts" / "legacy_codex_entry.py",
                "stdout_binding": paths.top1_run_logs / f"{skill}.stdout.txt",
                "stderr_binding": paths.top1_run_logs / f"{skill}.stderr.txt",
            }
            if not all(
                binding_targets_and_matches(run.get(binding_name), path)
                for binding_name, path in expected_bindings.items()
            ):
                skill_run_bindings_current = False
                break
    return {
        "all_top1_checks_pass": bool(
            isinstance(checks, dict)
            and checks
            and all(value is True for value in checks.values())
        ),
        "top1_result_artifact_bindings_current": result_artifacts_exact,
        "top1_skill_run_set_exact": skill_runs_exact,
        "top1_skill_run_bindings_current": skill_run_bindings_current,
    }


def listed_artifacts_current(nodes: Any) -> bool:
    if not isinstance(nodes, list) or not nodes:
        return False
    for node in nodes:
        path = Path(str(node.get("path") or ""))
        if not (
            path.is_file()
            and path.stat().st_size == int(node.get("size_bytes", -1))
            and sha256(path) == node.get("sha256")
        ):
            return False
    return True


def _is_plain_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def day_input_manifest_state(
    manifest: dict[str, Any],
    *,
    expected_run_id: str | None = None,
    expected_cutoff_trade_date: str | None = None,
) -> tuple[str, str]:
    """Separate an invalid V2 contract from a valid snapshot that has gone stale."""

    if not isinstance(manifest, dict):
        return "INVALID", "manifest_not_object"
    inputs = manifest.get("inputs")
    run_id = manifest.get("run_id")
    cutoff = manifest.get("cutoff_trade_date")
    top_level_valid = bool(
        manifest.get("schema") == DAY_INPUT_SCHEMA
        and manifest.get("binding_mode") == DAY_INPUT_BINDING_MODE
        and isinstance(run_id, str)
        and bool(run_id)
        and isinstance(cutoff, str)
        and len(cutoff) == 8
        and cutoff.isdigit()
        and manifest.get("tail_record_limit") == DAY_INPUT_TAIL_RECORD_LIMIT
        and manifest.get("stable_capture_passes") == DAY_INPUT_STABLE_CAPTURE_PASSES
        and _is_plain_int(manifest.get("capture_attempt"))
        and manifest["capture_attempt"] >= 1
        and isinstance(inputs, list)
        and bool(inputs)
        and manifest.get("complete") is True
        and manifest.get("all_requested_symbols_mapped") is True
        and manifest.get("all_existing_layouts_valid") is True
        and manifest.get("missing_inputs_explicit") is True
    )
    if not top_level_valid:
        return "INVALID", "top_level_contract"
    if expected_run_id is not None and run_id != expected_run_id:
        return "INVALID", "run_id_mismatch"
    if expected_cutoff_trade_date is not None and cutoff != expected_cutoff_trade_date:
        return "INVALID", "cutoff_trade_date_mismatch"

    normalized: list[tuple[dict[str, Any], Path]] = []
    seen_paths: set[str] = set()
    seen_aliases: set[str] = set()
    existing_count = 0
    missing_count = 0
    for index, node in enumerate(inputs):
        if not isinstance(node, dict):
            return "INVALID", f"input_{index}_not_object"
        raw_path = node.get("path")
        aliases = node.get("lookup_symbols")
        if not (
            isinstance(raw_path, str)
            and bool(raw_path)
            and isinstance(aliases, list)
            and bool(aliases)
            and all(isinstance(alias, str) and bool(alias) for alias in aliases)
            and aliases == sorted(set(aliases))
            and isinstance(node.get("exists"), bool)
            and isinstance(node.get("valid_layout"), bool)
        ):
            return "INVALID", f"input_{index}_base_contract"
        path = Path(raw_path)
        try:
            resolved = path.resolve()
        except (OSError, RuntimeError):
            return "INVALID", f"input_{index}_path_resolution"
        path_key = str(resolved).casefold()
        if not path.is_absolute() or path.suffix.casefold() != ".day" or path_key in seen_paths:
            return "INVALID", f"input_{index}_path_contract"
        if any(alias in seen_aliases for alias in aliases):
            return "INVALID", f"input_{index}_duplicate_alias"
        seen_paths.add(path_key)
        seen_aliases.update(aliases)

        if node["exists"] is True:
            existing_count += 1
            file_size = node.get("file_size")
            mtime_ns = node.get("mtime_ns")
            tail_record_count = node.get("tail_record_count")
            tail_offset = node.get("tail_offset")
            tail_size = node.get("tail_size")
            tail_hash = node.get("tail_sha256")
            expected_tail_record_count = (
                min(file_size // DAY_RECORD_SIZE, DAY_INPUT_TAIL_RECORD_LIMIT)
                if _is_plain_int(file_size) and file_size > 0 and file_size % DAY_RECORD_SIZE == 0
                else -1
            )
            if not (
                node["valid_layout"] is True
                and _is_plain_int(file_size)
                and file_size > 0
                and file_size % DAY_RECORD_SIZE == 0
                and _is_plain_int(mtime_ns)
                and mtime_ns >= 0
                and _is_plain_int(tail_record_count)
                and tail_record_count == expected_tail_record_count
                and _is_plain_int(tail_size)
                and tail_size == tail_record_count * DAY_RECORD_SIZE
                and _is_plain_int(tail_offset)
                and tail_offset == file_size - tail_size
                and isinstance(tail_hash, str)
                and len(tail_hash) == 64
                and tail_hash == tail_hash.lower()
                and all(character in "0123456789abcdef" for character in tail_hash)
            ):
                return "INVALID", f"input_{index}_existing_contract"
        else:
            missing_count += 1
            if node["valid_layout"] is not False:
                return "INVALID", f"input_{index}_missing_contract"
        normalized.append((node, resolved))

    count_contract_valid = all(
        _is_plain_int(manifest.get(field)) and manifest.get(field) == expected
        for field, expected in (
            ("input_count", len(inputs)),
            ("alias_count", len(seen_aliases)),
            ("existing_input_count", existing_count),
            ("missing_input_count", missing_count),
        )
    )
    if not count_contract_valid or existing_count + missing_count != len(inputs):
        return "INVALID", "derived_count_contract"

    for index, (node, path) in enumerate(normalized):
        try:
            if node["exists"] is False:
                if path.is_file():
                    return TDX_DAY_UPDATE_RACE, f"input_{index}_missing_file_appeared"
                continue
            before = path.stat()
            tail_offset = node["tail_offset"]
            tail_size = node["tail_size"]
            with path.open("rb") as handle:
                handle.seek(tail_offset)
                raw = handle.read(tail_size)
            after = path.stat()
            stable = (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
            current_tail_record_count = min(after.st_size // DAY_RECORD_SIZE, DAY_INPUT_TAIL_RECORD_LIMIT)
            if not (
                stable
                and len(raw) == tail_size
                and after.st_size > 0
                and after.st_size % DAY_RECORD_SIZE == 0
                and after.st_size == node["file_size"]
                and after.st_mtime_ns == node["mtime_ns"]
                and current_tail_record_count == node["tail_record_count"]
                and tail_size == current_tail_record_count * DAY_RECORD_SIZE
                and tail_offset == after.st_size - tail_size
                and hashlib.sha256(raw).hexdigest() == node["tail_sha256"]
            ):
                return TDX_DAY_UPDATE_RACE, f"input_{index}_snapshot_changed"
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return TDX_DAY_UPDATE_RACE, f"input_{index}_live_read:{type(exc).__name__}:{exc}"
    return "CURRENT", "current"


def day_input_manifest_current(
    manifest: dict[str, Any],
    *,
    expected_run_id: str | None = None,
    expected_cutoff_trade_date: str | None = None,
) -> bool:
    state, _reason = day_input_manifest_state(
        manifest,
        expected_run_id=expected_run_id,
        expected_cutoff_trade_date=expected_cutoff_trade_date,
    )
    return state == "CURRENT"


def weighted_result_contract_checks(result: dict[str, Any]) -> dict[str, bool]:
    checks = {
        "scan_schema_v5": False,
        "score_model_v2_exact_ten_components": False,
        "c9_normalization_contract_exact": False,
        "universe_partition_and_counts_complete": False,
        "hard_exclusions_fail_closed": False,
        "redemption_snapshot_bound_and_complete": False,
        "ranking_order_and_top10_exact": False,
        "component_scores_recompute": False,
        "golden_ignition_uses_local_cross_only": False,
        "big_bull_is_separate_tie_break_diagnostic": False,
        "missing_local_rows_retained_and_red": False,
    }
    try:
        eligible_rows = result.get("all_results") or []
        excluded_rows = result.get("hard_excluded_results") or []
        evaluated_rows = [*eligible_rows, *excluded_rows]
        model = result.get("score_model") or {}
        criteria = model.get("criteria") or []
        criterion_ids = tuple(str(item.get("id")) for item in criteria)
        criterion_weights = tuple(float(item.get("weight")) for item in criteria)
        checks["scan_schema_v5"] = result.get("schema") == "TDX-CONVERTIBLE-BOND-WEIGHTED-SCAN-V5"
        checks["score_model_v2_exact_ten_components"] = bool(
            model.get("version") == SCORE_MODEL_VERSION
            and criterion_ids == EXPECTED_SCORE_COMPONENT_IDS
            and criterion_weights == EXPECTED_SCORE_COMPONENT_WEIGHTS
            and int(model.get("criterion_count", -1)) == len(EXPECTED_SCORE_COMPONENT_IDS)
            and abs(sum(criterion_weights) - 100.0) <= 1e-9
            and abs(float(model.get("weight_sum", -1.0)) - 100.0) <= 1e-9
            and all(
                tuple(row.get("score_components") or {}) == EXPECTED_SCORE_COMPONENT_IDS
                and all(
                    float((row.get("score_components") or {}).get(component_id, {}).get("weight"))
                    == EXPECTED_SCORE_COMPONENT_WEIGHT_BY_ID[component_id]
                    for component_id in EXPECTED_SCORE_COMPONENT_IDS
                )
                for row in evaluated_rows
            )
        )
        checks["c9_normalization_contract_exact"] = (
            (model.get("normalization_rules") or {}).get("c9_sector_heat") == EXPECTED_C9_NORMALIZATION_RULE
        )

        eligible_symbols = [str(row.get("symbol") or "") for row in eligible_rows]
        excluded_symbols = [str(row.get("symbol") or "") for row in excluded_rows]
        evaluated_symbols = [*eligible_symbols, *excluded_symbols]
        checks["universe_partition_and_counts_complete"] = bool(
            eligible_rows
            and result.get("universe_partition_complete") is True
            and len(evaluated_symbols) == len(set(evaluated_symbols))
            and set(eligible_symbols).isdisjoint(excluded_symbols)
            and len(evaluated_rows) == int(result.get("universe_count", -1))
            and len(evaluated_rows) == int(result.get("evaluated_count", -1))
            and len(evaluated_rows) == int(result.get("analyzed_count", -1))
            and len(eligible_rows) == int(result.get("eligible_count", -1))
            and len(eligible_rows) == int(result.get("ranked_count", -1))
            and len(excluded_rows) == int(result.get("hard_excluded_count", -1))
        )
        reason_counts = result.get("hard_exclusion_reason_counts") or {}
        declared_reason_codes = {
            str(item.get("reason_code") or "")
            for item in (result.get("hard_exclusion_model") or {}).get("rules") or []
        }
        checks["hard_exclusions_fail_closed"] = bool(
            declared_reason_codes == EXPECTED_HARD_EXCLUSION_CODES
            and set(reason_counts) == EXPECTED_HARD_EXCLUSION_CODES
            and all(
                row.get("hard_exclusion_pass") is True
                and not (row.get("hard_exclusion_reasons") or [])
                for row in eligible_rows
            )
            and all(
                row.get("hard_exclusion_pass") is False
                and bool(row.get("hard_exclusion_reasons"))
                and set(row.get("hard_exclusion_reasons") or []) <= EXPECTED_HARD_EXCLUSION_CODES
                and row.get("rank") is None
                for row in excluded_rows
            )
            and all(
                int(reason_counts[reason_code])
                == sum(
                    reason_code in (row.get("hard_exclusion_reasons") or [])
                    for row in excluded_rows
                )
                for reason_code in EXPECTED_HARD_EXCLUSION_CODES
            )
        )
        redemption = result.get("redemption_announcement_snapshot") or {}
        checks["redemption_snapshot_bound_and_complete"] = bool(
            redemption.get("status") == "PASS"
            and redemption.get("current_universe_complete") is True
            and redemption.get("run_id") == result.get("run_id")
            and redemption.get("cutoff") == result.get("cutoff_trade_date")
            and isinstance(redemption.get("size"), int)
            and isinstance(redemption.get("sha256"), str)
            and len(redemption.get("sha256")) == 64
            and result.get("execution_policy", {}).get("strong_redemption_announcements_verified") is True
            and all(
                row.get("early_redemption_status") in {
                    "ANNOUNCED_EARLY_REDEMPTION",
                    "NO_MATCH_AS_OF_CUTOFF",
                    "UNVERIFIED",
                }
                for row in evaluated_rows
            )
        )

        expected_order = sorted(
            eligible_rows,
            key=lambda row: (
                -float(row["score_total_raw"]),
                not bool(row["big_bull_red_preference"]),
                str(row["symbol"]),
            ),
        )
        checks["ranking_order_and_top10_exact"] = bool(
            eligible_rows == expected_order
            and [int(row.get("rank", -1)) for row in eligible_rows]
            == list(range(1, len(eligible_rows) + 1))
            and result.get("ranking_top10") == eligible_rows[:10]
        )
        checks["component_scores_recompute"] = all(
            abs(
                sum(float(component["earned_score"]) for component in row["score_components"].values())
                - float(row["score_total_raw"])
            ) <= 1e-8
            for row in evaluated_rows
        )
        checks["golden_ignition_uses_local_cross_only"] = all(
            bool(row.get("conditions", {}).get("c4_recent_ignition"))
            == bool(row.get("ignition_local_cross_dates_10"))
            == (float(row["score_components"]["c4_golden_ignition"]["earned_score"]) > 0.0)
            for row in evaluated_rows
        )
        checks["big_bull_is_separate_tie_break_diagnostic"] = bool(
            model.get("big_bull_rule")
            == "EMA5>EMA20 is a displayed exact-tie preference only and contributes zero score"
            and all(
                "bigbull_formula_diagnostic_hits" in row
                and "ignition_formula_hits" not in row
                and bool(row.get("big_bull_red_preference"))
                == bool(row.get("conditions", {}).get("c10_big_bull_red_preference"))
                for row in evaluated_rows
            )
        )

        missing_symbols = {str(symbol) for symbol in result.get("missing_local_symbols") or []}
        row_by_symbol = {str(row.get("symbol") or ""): row for row in evaluated_rows}
        checks["missing_local_rows_retained_and_red"] = bool(
            int(result.get("unavailable_local_retained_count", -1)) == len(missing_symbols)
            and missing_symbols <= set(row_by_symbol)
            and all(
                row_by_symbol[symbol].get("risk_level") == "RED"
                and bool(row_by_symbol[symbol].get("risk_veto_reasons"))
                for symbol in missing_symbols
            )
        )
    except (KeyError, TypeError, ValueError):
        pass
    return checks


def compact_child_diagnostic(stdout: str | None, stderr: str | None, limit: int = 1600) -> str:
    diagnostic = stderr or stdout or ""
    return " | ".join(line.strip() for line in diagnostic.splitlines() if line.strip())[-limit:]


def _structured_json_objects(text: str) -> list[dict[str, Any]]:
    candidates = [text.strip(), *(line.strip() for line in text.splitlines())]
    objects: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            payload = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(payload, dict):
            objects.append(payload)
    return objects


def retryable_day_race_event(
    exc: ChildInvocationError,
    *,
    run_id: str,
    attempt: int,
) -> dict[str, Any] | None:
    expected_schema = RETRYABLE_CHILD_FAILURE_SCHEMAS.get(exc.script)
    if exc.returncode != 3 or expected_schema is None:
        return None
    expected_script = str((SCRIPTS / exc.script).resolve()).casefold()
    for event in _structured_json_objects(f"{exc.stdout}\n{exc.stderr}"):
        try:
            event_script = str(Path(str(event.get("script") or "")).resolve()).casefold()
        except (OSError, RuntimeError, TypeError, ValueError):
            continue
        mismatch_count = event.get("mismatch_count")
        mismatch_paths = event.get("mismatch_paths")
        error = event.get("error")
        if (
            event.get("schema") == expected_schema
            and event.get("status") == "FAIL"
            and event.get("failure_code") == TDX_DAY_UPDATE_RACE
            and event.get("retryable") is True
            and event_script == expected_script
            and event.get("run_id") == run_id
            and _is_plain_int(event.get("attempt"))
            and event["attempt"] == attempt
            and isinstance(error, str)
            and error.startswith(f"{TDX_DAY_UPDATE_RACE}:")
            and _is_plain_int(mismatch_count)
            and mismatch_count >= 1
            and isinstance(mismatch_paths, list)
            and len(mismatch_paths) == mismatch_count
            and all(isinstance(path, str) and bool(path) for path in mismatch_paths)
        ):
            return event
    return None


def invoke(
    script: str,
    args: list[str],
    *,
    timeout_seconds: int = 360,
    forward_output: bool = True,
) -> float:
    command = [sys.executable, str(SCRIPTS / script), *args]
    started = time.perf_counter()
    try:
        result = run_process_tree(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{script} timed out after {timeout_seconds}s") from exc
    if forward_output and result.stdout:
        emit_best_effort(result.stdout, end="")
    if forward_output and result.stderr:
        emit_best_effort(result.stderr, end="", stream=sys.stderr)
    if result.returncode != 0:
        raise ChildInvocationError(
            script,
            result.returncode,
            result.stdout,
            result.stderr,
            time.perf_counter() - started,
        )
    return time.perf_counter() - started


def command_info() -> int:
    emit_best_effort(json.dumps({
        "name": "convertible-bond-screening-strategy",
        "display_name": "可转债筛选策略",
        "entry": str(Path(__file__).resolve()),
        "commands": ["info", "selftest", "run", "status", "deliver"],
        "target_system": "local Codex + C:\\new_tdx_mock",
        "mode": "post_close_manual_decision_support",
        "automatic_order": False,
        "score_criteria": 10,
        "score_weight_sum": 100,
    }, ensure_ascii=False, indent=2))
    return 0


def command_selftest(
    run_id: str | None = None,
    *,
    acquire_lock: bool = True,
    output_path: Path | None = None,
    market_attempt: int | None = None,
    emit_output: bool = True,
) -> int:
    target = output_path or SELFTEST_STANDALONE
    if acquire_lock:
        try:
            with RunLock(SELFTEST_LOCK):
                return command_selftest(
                    run_id,
                    acquire_lock=False,
                    output_path=target,
                    market_attempt=market_attempt,
                    emit_output=emit_output,
                )
        except RunInProgressError:
            if emit_output:
                emit_best_effort(json.dumps({
                    "skill_id": "convertible-bond-screening-strategy",
                    "status": "BLOCKED",
                    "errors": ["selftest_run_in_progress"],
                }, ensure_ascii=False))
            return 3
        except Exception as exc:
            if not emit_output:
                raise
            emit_best_effort(json.dumps({
                "skill_id": "convertible-bond-screening-strategy",
                "status": "BLOCKED",
                "errors": [f"selftest_exception:{type(exc).__name__}:{exc}"],
            }, ensure_ascii=False))
            return 2
    target.parent.mkdir(parents=True, exist_ok=True)
    current_run_id = run_id or f"selftest-{uuid.uuid4().hex}"
    if market_attempt is not None:
        require_new_targets((target,))
    invoke(
        "selftest.py",
        ["--output", str(target), "--run-id", current_run_id],
        forward_output=False,
    )
    if market_attempt is not None:
        bind_json_generation(target, current_run_id, market_attempt)
    persisted = load_json(target)
    if (
        persisted.get("status") != "PASS"
        or persisted.get("run_id") != current_run_id
        or not all(persisted.get("checks", {}).values())
    ):
        raise RuntimeError("persisted selftest is not PASS")
    if emit_output:
        emit_best_effort(json.dumps({
            "skill_id": "convertible-bond-screening-strategy",
            "status": "CLEAN_PASS",
            "errors": [],
        }, ensure_ascii=False))
    return 0


def write_status(
    run_id: str,
    market_attempt: int,
    stage_seconds: dict[str, float],
    paths: GenerationPaths,
) -> dict[str, Any]:
    RESULT = paths.result
    FORMULA_EVIDENCE = paths.formula_evidence
    DAY_INPUT_MANIFEST = paths.day_input_manifest
    REDEMPTION_ANNOUNCEMENTS = paths.redemption_announcements
    VERIFICATION = paths.verification
    INDEPENDENT_HEAT_VERIFICATION = paths.independent_heat_verification
    SUMMARY = paths.summary
    SELFTEST = paths.selftest
    TOP1_VALIDATION = paths.top1_validation
    TOP1_GOLDEN = paths.top1_golden
    TOP1_FEILONG = paths.top1_feilong
    TOP1_BIGBULL = paths.top1_bigbull
    result = load_json(RESULT)
    formula_evidence = load_json(FORMULA_EVIDENCE)
    day_input_manifest = load_json(DAY_INPUT_MANIFEST)
    redemption_announcements = load_json(REDEMPTION_ANNOUNCEMENTS)
    verification = load_json(VERIFICATION)
    independent_heat_verification = load_json(INDEPENDENT_HEAT_VERIFICATION)
    summary = load_json(SUMMARY)
    selftest = load_json(SELFTEST)
    top1 = load_json(TOP1_VALIDATION)
    if any(
        node.get("status") != "PASS"
        for node in (
            result,
            redemption_announcements,
            verification,
            independent_heat_verification,
            summary,
            selftest,
            top1,
        )
    ):
        raise RuntimeError("cannot persist PASS status from a non-PASS component")
    result_contract_checks = weighted_result_contract_checks(result)
    if not all(result_contract_checks.values()):
        failed = sorted(key for key, ok in result_contract_checks.items() if not ok)
        raise RuntimeError(f"weighted result contract failed: {failed}")
    component_run_ids = {
        str(node.get("run_id") or "")
        for node in (
            result,
            formula_evidence,
            day_input_manifest,
            redemption_announcements,
            verification,
            independent_heat_verification,
            summary,
            selftest,
            top1,
        )
    }
    if component_run_ids != {run_id}:
        raise RuntimeError(f"component run_id mismatch: {sorted(component_run_ids)}")
    component_attempts = {
        node.get("market_attempt")
        for node in (
            result,
            formula_evidence,
            day_input_manifest,
            redemption_announcements,
            verification,
            independent_heat_verification,
            summary,
            selftest,
            top1,
        )
    }
    if component_attempts != {market_attempt}:
        raise RuntimeError(f"component market_attempt mismatch: {sorted(component_attempts)}")
    if verification.get("input", {}).get("sha256") != sha256(RESULT):
        raise RuntimeError("verification input binding does not match current result")
    if not binding_targets_and_matches(
        independent_heat_verification.get("production_result_binding"), RESULT
    ):
        raise RuntimeError("independent heat verification result binding is not current")
    if not binding_targets_and_matches(
        independent_heat_verification.get("day_input_manifest"), DAY_INPUT_MANIFEST
    ):
        raise RuntimeError("independent heat verification day input binding is not current")
    if not bool(
        independent_heat_verification.get("run_id") == run_id
        and independent_heat_verification.get("cutoff_trade_date")
        == result.get("cutoff_trade_date")
        and int(independent_heat_verification.get("eligible_result_count", -1))
        == int(result.get("eligible_count", -2))
        and int(independent_heat_verification.get("hard_excluded_result_count", -1))
        == int(result.get("hard_excluded_count", -2))
        and int(independent_heat_verification.get("evaluated_result_count", -1))
        == int(result.get("evaluated_count", -2))
    ):
        raise RuntimeError("independent heat verification generation or pool counts mismatch")
    if summary.get("source_bindings", {}).get("scan", {}).get("sha256") != sha256(RESULT):
        raise RuntimeError("summary scan binding does not match current result")
    if summary.get("source_bindings", {}).get("verification", {}).get("sha256") != sha256(VERIFICATION):
        raise RuntimeError("summary verification binding does not match current verification")
    if summary.get("source_bindings", {}).get("redemption_announcements", {}).get("sha256") != sha256(REDEMPTION_ANNOUNCEMENTS):
        raise RuntimeError("summary redemption binding does not match current snapshot")
    if top1.get("scan_input", {}).get("sha256") != sha256(RESULT):
        raise RuntimeError("Top1 scan binding does not match current result")
    top1_binding_checks = top1_evidence_binding_checks(top1, paths)
    if not all(top1_binding_checks.values()):
        failed = sorted(key for key, ok in top1_binding_checks.items() if not ok)
        raise RuntimeError(f"Top1 evidence binding failed: {failed}")
    formula_binding = result.get("formula_evidence") or {}
    if (
        formula_binding.get("sha256") != sha256(FORMULA_EVIDENCE)
        or int(formula_binding.get("size", -1)) != FORMULA_EVIDENCE.stat().st_size
    ):
        raise RuntimeError("formula evidence binding does not match current evidence")
    day_binding = result.get("day_input_manifest") or {}
    if (
        day_binding.get("sha256") != sha256(DAY_INPUT_MANIFEST)
        or int(day_binding.get("size", -1)) != DAY_INPUT_MANIFEST.stat().st_size
    ):
        raise RuntimeError("day input manifest binding check failed")
    redemption_binding = result.get("redemption_announcement_snapshot") or {}
    if (
        redemption_binding.get("sha256") != sha256(REDEMPTION_ANNOUNCEMENTS)
        or int(redemption_binding.get("size", -1)) != REDEMPTION_ANNOUNCEMENTS.stat().st_size
        or redemption_binding.get("run_id") != run_id
        or redemption_binding.get("cutoff") != result.get("cutoff_trade_date")
        or redemption_binding.get("status") != "PASS"
        or redemption_binding.get("current_universe_complete") is not True
    ):
        raise RuntimeError("redemption announcement snapshot binding check failed")
    day_state, day_reason = day_input_manifest_state(
        day_input_manifest,
        expected_run_id=run_id,
        expected_cutoff_trade_date=str(result.get("cutoff_trade_date") or ""),
    )
    if day_state == TDX_DAY_UPDATE_RACE:
        raise RuntimeError(f"{TDX_DAY_UPDATE_RACE}:{day_reason}")
    if day_state != "CURRENT":
        raise RuntimeError(f"day input manifest V2 contract failed:{day_reason}")
    run_artifacts = [
        RESULT,
        FORMULA_EVIDENCE,
        DAY_INPUT_MANIFEST,
        REDEMPTION_ANNOUNCEMENTS,
        VERIFICATION,
        INDEPENDENT_HEAT_VERIFICATION,
        SUMMARY,
        SELFTEST,
        TOP1_VALIDATION,
        TOP1_GOLDEN,
        TOP1_FEILONG,
        TOP1_BIGBULL,
    ]
    policy = result["execution_policy"]
    payload = {
        "schema": "CONVERTIBLE-BOND-SCREENING-SKILL-STATUS-3",
        "run_id": run_id,
        "market_attempt": market_attempt,
        "skill": "convertible-bond-screening-strategy",
        "display_name": "可转债筛选策略",
        "status": "PASS",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "target_system": "local Codex + C:\\new_tdx_mock",
        "trade_date": result["cutoff_trade_date"],
        "universe_count": result["universe_count"],
        "ranked_count": result["ranked_count"],
        "eligible_count": result["eligible_count"],
        "hard_excluded_count": result["hard_excluded_count"],
        "evaluated_count": result["evaluated_count"],
        "hard_exclusion_reason_counts": result["hard_exclusion_reason_counts"],
        "score_model_version": result["score_model"]["version"],
        "score_criteria_count": result["score_model"]["criterion_count"],
        "score_weight_sum": result["score_model"]["weight_sum"],
        "risk_counts_top10": result["risk_counts_top10"],
        "execution_policy": policy,
        "automatic_order": False,
        "execution_eligible": policy["execution_eligible"],
        "top10": [
            {
                "rank": item["rank"],
                "symbol": item["symbol"],
                "name": item["name"],
                "underlying_symbol": item["underlying_symbol"],
                "underlying_name": item["underlying_name"],
                "score": item["score_total_raw"],
                "risk_level": item["risk_level"],
                "big_bull_red_preference": item["big_bull_red_preference"],
                "hard_exclusion_pass": item["hard_exclusion_pass"],
                "early_redemption_status": item["early_redemption_status"],
            }
            for item in result["ranking_top10"]
        ],
        "verification_status": verification["status"],
        "independent_heat_verification_status": independent_heat_verification["status"],
        "top1_fixed_skill_validation_status": top1["status"],
        "top1_fixed_skill_target": top1["target"],
        "weighted_result_contract_checks": result_contract_checks,
        "top1_evidence_binding_checks": top1_binding_checks,
        "performance": {
            "stage_seconds": {key: round(value, 6) for key, value in stage_seconds.items()},
            "total_seconds": round(sum(stage_seconds.values()), 6),
            "tq_batch_size": result.get("formula_coverage", {}).get("tq_batch_size"),
        },
        "artifacts": [artifact(path) for path in run_artifacts],
    }
    atomic_write_json(STATUS, payload)
    return payload


def _command_status_impl(
    *,
    acquire_lock: bool = True,
    expected_run_state: str = "PASS",
    emit_output: bool = True,
) -> int:
    if acquire_lock:
        try:
            with RunLock(RUN_LOCK):
                return _command_status_impl(
                    acquire_lock=False,
                    expected_run_state=expected_run_state,
                    emit_output=emit_output,
                )
        except RunInProgressError:
            if emit_output:
                emit_best_effort(json.dumps({"status": "RUN_IN_PROGRESS", "automatic_order": False}, ensure_ascii=False))
            return 3
    try:
        if not RUN_STATE.is_file():
            raise RuntimeError("run state artifact missing")
        run_state = load_json(RUN_STATE)
        state_run_id = run_state.get("run_id")
        state_attempt = run_state.get("market_attempt")
        paths = build_generation_paths(RUN, state_run_id, state_attempt)
        RESULT = paths.result
        FORMULA_EVIDENCE = paths.formula_evidence
        DAY_INPUT_MANIFEST = paths.day_input_manifest
        REDEMPTION_ANNOUNCEMENTS = paths.redemption_announcements
        VERIFICATION = paths.verification
        INDEPENDENT_HEAT_VERIFICATION = paths.independent_heat_verification
        SUMMARY = paths.summary
        SELFTEST = paths.selftest
        TOP1_VALIDATION = paths.top1_validation
        required = [
            STATUS,
            RUN_STATE,
            RESULT,
            FORMULA_EVIDENCE,
            DAY_INPUT_MANIFEST,
            REDEMPTION_ANNOUNCEMENTS,
            VERIFICATION,
            INDEPENDENT_HEAT_VERIFICATION,
            SUMMARY,
            SELFTEST,
            TOP1_VALIDATION,
        ]
        if expected_run_state == "PASS":
            required.append(LATEST_SUMMARY)
        if not all(path.is_file() for path in required):
            raise RuntimeError("required status artifact missing")
        status = load_json(STATUS)
        result = load_json(RESULT)
        formula_evidence = load_json(FORMULA_EVIDENCE)
        day_input_manifest = load_json(DAY_INPUT_MANIFEST)
        redemption_announcements = load_json(REDEMPTION_ANNOUNCEMENTS)
        verification = load_json(VERIFICATION)
        independent_heat_verification = load_json(INDEPENDENT_HEAT_VERIFICATION)
        summary = load_json(SUMMARY)
        latest_summary = (
            load_json(LATEST_SUMMARY)
            if expected_run_state == "PASS"
            else None
        )
        selftest = load_json(SELFTEST)
        top1 = load_json(TOP1_VALIDATION)
    except Exception as exc:
        return _persist_status_readback_failure(exc)

    artifact_checks: list[dict[str, Any]] = []
    for expected in status.get("artifacts") or []:
        path = Path(expected["path"])
        actual = artifact(path) if path.is_file() else {"path": str(path), "missing": True}
        artifact_checks.append({
            "ok": bool(path.is_file() and actual.get("size_bytes") == expected.get("size_bytes") and actual.get("sha256") == expected.get("sha256")),
            "expected": expected,
            "actual": actual,
        })

    result_symbols = [item["symbol"] for item in result["ranking_top10"]]
    status_symbols = [item["symbol"] for item in status["top10"]]
    summary_symbols = [item.get("symbol") for item in summary["top10"]]
    green_count = int(result["risk_counts_top10"]["GREEN"])
    run_id = str(status.get("run_id") or "")
    component_run_ids = {
        str(node.get("run_id") or "")
        for node in (
            result,
            formula_evidence,
            day_input_manifest,
            redemption_announcements,
            verification,
            independent_heat_verification,
            summary,
            selftest,
            top1,
        )
    }
    component_attempts = {
        node.get("market_attempt")
        for node in (
            result,
            formula_evidence,
            day_input_manifest,
            redemption_announcements,
            verification,
            independent_heat_verification,
            summary,
            selftest,
            top1,
        )
    }
    sources_current, source_checks, current_benchmark_date = current_source_checks(result)
    weighted_contract_checks = weighted_result_contract_checks(result)
    top1_binding_checks = top1_evidence_binding_checks(top1, paths)
    day_state, day_reason = day_input_manifest_state(
        day_input_manifest,
        expected_run_id=run_id,
        expected_cutoff_trade_date=str(result.get("cutoff_trade_date") or ""),
    )
    latest_summary_bytes_match_generation = True
    latest_summary_size_matches_generation = True
    latest_summary_sha256_matches_generation = True
    latest_summary_run_id_matches = True
    latest_summary_market_attempt_matches = True
    if expected_run_state == "PASS":
        generation_summary_bytes = SUMMARY.read_bytes()
        published_summary_bytes = LATEST_SUMMARY.read_bytes()
        latest_summary_bytes_match_generation = (
            published_summary_bytes == generation_summary_bytes
        )
        latest_summary_size_matches_generation = (
            LATEST_SUMMARY.stat().st_size == SUMMARY.stat().st_size
        )
        latest_summary_sha256_matches_generation = (
            sha256(LATEST_SUMMARY) == sha256(SUMMARY)
        )
        latest_summary_run_id_matches = bool(
            latest_summary is not None
            and latest_summary.get("run_id") == run_id
            and latest_summary.get("run_id") == summary.get("run_id")
        )
        latest_summary_market_attempt_matches = bool(
            latest_summary is not None
            and latest_summary.get("market_attempt") == state_attempt
            and latest_summary.get("market_attempt")
            == summary.get("market_attempt")
        )
    business_checks = {
        "status_schema_v3": status.get("schema") == "CONVERTIBLE-BOND-SCREENING-SKILL-STATUS-3",
        "run_state_pass_and_same_generation": run_state.get("status") == expected_run_state and run_state.get("run_id") == run_id,
        "run_state_and_components_same_attempt": bool(
            status.get("market_attempt") == state_attempt
            and component_attempts == {state_attempt}
        ),
        "one_run_id_across_all_artifacts": bool(run_id) and component_run_ids == {run_id},
        "all_component_statuses_pass": all(
            node.get("status") == "PASS"
            for node in (
                result,
                redemption_announcements,
                verification,
                independent_heat_verification,
                summary,
                selftest,
                top1,
            )
        ),
        "all_selftest_checks_pass": all(selftest.get("checks", {}).values()),
        "selftest_source_artifacts_current": listed_artifacts_current(selftest.get("source_artifacts")),
        "all_verification_checks_pass": all(verification.get("checks", {}).values()),
        "verification_input_binding_matches": binding_matches(verification.get("input") or {}, RESULT),
        "all_independent_heat_checks_pass": bool(
            independent_heat_verification.get("checks")
            and all(independent_heat_verification.get("checks", {}).values())
        ),
        "independent_heat_result_binding_matches": binding_targets_and_matches(
            independent_heat_verification.get("production_result_binding"), RESULT
        ),
        "independent_heat_day_manifest_binding_matches": binding_targets_and_matches(
            independent_heat_verification.get("day_input_manifest"), DAY_INPUT_MANIFEST
        ),
        "independent_heat_partition_counts_match": bool(
            int(independent_heat_verification.get("eligible_result_count", -1))
            == int(result.get("eligible_count", -2))
            and int(independent_heat_verification.get("hard_excluded_result_count", -1))
            == int(result.get("hard_excluded_count", -2))
            and int(independent_heat_verification.get("evaluated_result_count", -1))
            == int(result.get("evaluated_count", -2))
        ),
        "summary_scan_binding_matches": binding_matches(summary.get("source_bindings", {}).get("scan") or {}, RESULT),
        "summary_verification_binding_matches": binding_matches(summary.get("source_bindings", {}).get("verification") or {}, VERIFICATION),
        "summary_redemption_binding_matches": binding_matches(summary.get("source_bindings", {}).get("redemption_announcements") or {}, REDEMPTION_ANNOUNCEMENTS),
        "latest_summary_bytes_match_generation": latest_summary_bytes_match_generation,
        "latest_summary_size_matches_generation": latest_summary_size_matches_generation,
        "latest_summary_sha256_matches_generation": latest_summary_sha256_matches_generation,
        "latest_summary_run_id_matches": latest_summary_run_id_matches,
        "latest_summary_market_attempt_matches": latest_summary_market_attempt_matches,
        "top1_scan_binding_matches": binding_matches(top1.get("scan_input") or {}, RESULT),
        "formula_evidence_binding_matches": binding_matches(result.get("formula_evidence") or {}, FORMULA_EVIDENCE),
        "day_input_manifest_binding_matches": binding_matches(result.get("day_input_manifest") or {}, DAY_INPUT_MANIFEST),
        "redemption_snapshot_binding_matches": binding_matches(result.get("redemption_announcement_snapshot") or {}, REDEMPTION_ANNOUNCEMENTS),
        "redemption_snapshot_same_run_and_cutoff": bool(
            redemption_announcements.get("run_id") == run_id
            and str(redemption_announcements.get("cutoff_trade_date") or redemption_announcements.get("cutoff") or "").replace("-", "")
            == result.get("cutoff_trade_date")
            and redemption_announcements.get("current_universe_complete") is True
            and int(redemption_announcements.get("record_count", -1)) == int(result.get("universe_count", -2))
        ),
        "day_input_manifest_v2_contract": day_state != "INVALID",
        "day_input_manifest_current": day_state == "CURRENT",
        "current_source_hashes_match": sources_current,
        "current_benchmark_matches": current_benchmark_date == status.get("trade_date") == result.get("cutoff_trade_date"),
        "trade_date_matches": bool(
            status.get("trade_date")
            == result.get("cutoff_trade_date")
            == verification.get("cutoff_trade_date")
            == independent_heat_verification.get("cutoff_trade_date")
        ),
        "top10_matches": status_symbols == result_symbols == summary_symbols,
        "top1_fixed_skill_target_matches": bool(result_symbols) and top1.get("target", {}).get("bond_symbol") == result_symbols[0] and top1.get("target", {}).get("trade_date") == result.get("cutoff_trade_date"),
        **top1_binding_checks,
        "score_contract_exact": bool(
            status.get("score_criteria_count") == 10
            and float(status.get("score_weight_sum")) == 100.0
            and (result.get("score_model", {}).get("normalization_rules") or {}).get("c9_sector_heat")
            == EXPECTED_C9_NORMALIZATION_RULE
        ),
        "universe_partition_complete": result.get("universe_partition_complete") is True,
        "formula_field_coverage_complete": result.get("formula_coverage", {}).get("complete") is True,
        "automatic_order_false": status.get("automatic_order") is False and result.get("execution_policy", {}).get("automatic_order") is False,
        "execution_eligibility_exact": status.get("execution_eligible") is (green_count > 0),
        "strong_redemption_announcements_verified": result.get("execution_policy", {}).get("strong_redemption_announcements_verified") is True,
        **weighted_contract_checks,
    }
    pass_state = bool(artifact_checks and all(item["ok"] for item in artifact_checks) and all(business_checks.values()))
    payload = {
        "schema": "CONVERTIBLE-BOND-SCREENING-STATUS-READBACK-3",
        "status": "PASS" if pass_state else "FAIL",
        "run_id": run_id,
        "market_attempt": state_attempt,
        "expected_run_state": expected_run_state,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status_artifact": artifact(STATUS),
        "artifact_checks": artifact_checks,
        "source_checks": source_checks,
        "business_checks": business_checks,
        "trade_date": result["cutoff_trade_date"],
        "current_benchmark_date": current_benchmark_date,
        "universe_count": result["universe_count"],
        "ranked_count": result["ranked_count"],
        "eligible_count": result["eligible_count"],
        "hard_excluded_count": result["hard_excluded_count"],
        "evaluated_count": result["evaluated_count"],
        "hard_exclusion_reason_counts": result["hard_exclusion_reason_counts"],
        "risk_counts_top10": result["risk_counts_top10"],
        "execution_eligible": green_count > 0,
        "automatic_order": False,
        "performance": status.get("performance"),
        "top10": status["top10"],
    }
    atomic_write_json(STATUS_READBACK, payload)
    readback = load_json(STATUS_READBACK)
    if readback.get("status") != payload["status"] or readback.get("business_checks") != business_checks:
        raise RuntimeError("status readback JSON mismatch")
    if emit_output:
        emit_best_effort(json.dumps({
            "status": payload["status"],
            "run_id": run_id,
            "trade_date": payload["trade_date"],
            "universe_count": payload["universe_count"],
            "ranked_count": payload["ranked_count"],
            "risk_counts_top10": payload["risk_counts_top10"],
            "execution_eligible": payload["execution_eligible"],
            "automatic_order": False,
            "performance": payload["performance"],
            "top10": payload["top10"],
            "readback_path": str(STATUS_READBACK.resolve()),
            "readback_size": STATUS_READBACK.stat().st_size,
            "readback_sha256": sha256(STATUS_READBACK),
            "business_checks": business_checks,
        }, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


def _persist_status_readback_failure(exc: Exception) -> int:
    run_id = ""
    for candidate in (RUN_STATE, STATUS):
        try:
            if candidate.is_file():
                run_id = str(load_json(candidate).get("run_id") or run_id)
        except Exception:
            continue
    failure = {
        "schema": "CONVERTIBLE-BOND-SCREENING-STATUS-READBACK-3",
        "status": "FAIL",
        "run_id": run_id,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reason": f"status_validation_failed:{type(exc).__name__}:{exc}",
        "automatic_order": False,
    }
    try:
        atomic_write_json(STATUS_READBACK, failure)
        persisted = load_json(STATUS_READBACK)
        if persisted != failure:
            raise RuntimeError("persisted FAIL status readback does not match payload")
    except Exception as persist_exc:
        emit_best_effort(json.dumps({
            **failure,
            "reason": (
                f"{failure['reason']};status_readback_persist_failed:"
                f"{type(persist_exc).__name__}:{persist_exc}"
            ),
        }, ensure_ascii=False, indent=2), stream=sys.stderr)
        return 2
    emit_best_effort(json.dumps(failure, ensure_ascii=False, indent=2))
    return 2


def command_status(
    *,
    acquire_lock: bool = True,
    expected_run_state: str = "PASS",
    emit_output: bool = True,
) -> int:
    if acquire_lock:
        try:
            with RunLock(RUN_LOCK):
                return command_status(
                    acquire_lock=False,
                    expected_run_state=expected_run_state,
                    emit_output=emit_output,
                )
        except RunInProgressError:
            if emit_output:
                emit_best_effort(json.dumps(
                    {"status": "RUN_IN_PROGRESS", "automatic_order": False},
                    ensure_ascii=False,
                ))
            return 3
    try:
        status_code = _command_status_impl(
            acquire_lock=False,
            expected_run_state=expected_run_state,
            emit_output=emit_output if expected_run_state != "PASS" else False,
        )
        if status_code != 0 or expected_run_state != "PASS":
            return status_code

        delivery = build_delivery_payload(RUN)
        readback = load_json(STATUS_READBACK)
        if readback.get("delivery_contract_exact") is not True:
            readback["delivery_contract_exact"] = True
            atomic_write_json(STATUS_READBACK, readback)
            delivery = build_delivery_payload(RUN)

        if emit_output:
            verified_readback = load_json(STATUS_READBACK)
            emit_best_effort(json.dumps({
                "status": "PASS",
                "run_id": delivery["run_id"],
                "market_attempt": delivery["market_attempt"],
                "trade_date": verified_readback.get("trade_date"),
                "universe_count": verified_readback.get("universe_count"),
                "ranked_count": verified_readback.get("ranked_count"),
                "risk_counts_top10": verified_readback.get("risk_counts_top10"),
                "execution_eligible": verified_readback.get("execution_eligible"),
                "automatic_order": False,
                "score_model_version": delivery["score_model_version"],
                "criterion_count": delivery["criterion_count"],
                "weight_sum": delivery["weight_sum"],
                "manual_override_allowed": False,
                "cross_run_mixing_allowed": False,
                "delivery_contract_exact": True,
                "top10": delivery["top10"],
                "readback_path": str(STATUS_READBACK.resolve()),
                "readback_size": STATUS_READBACK.stat().st_size,
                "readback_sha256": sha256(STATUS_READBACK),
                "business_checks": verified_readback.get("business_checks"),
            }, ensure_ascii=False, indent=2))
        return 0
    except DeliveryContractError as exc:
        return _persist_status_readback_failure(
            RuntimeError(f"delivery_contract_blocked:{exc}")
        )
    except Exception as exc:
        return _persist_status_readback_failure(exc)


def command_deliver() -> int:
    try:
        payload = build_delivery_payload(RUN)
    except DeliveryContractError as exc:
        emit_best_effort(json.dumps({
            "schema": DELIVERY_SCHEMA,
            "status": "BLOCKED",
            "reason": str(exc),
            "automatic_order": False,
            "manual_override_allowed": False,
            "cross_run_mixing_allowed": False,
        }, ensure_ascii=False, indent=2), stream=sys.stderr)
        return 2
    except Exception as exc:
        emit_best_effort(json.dumps({
            "schema": DELIVERY_SCHEMA,
            "status": "BLOCKED",
            "reason": f"{type(exc).__name__}:{exc}",
            "automatic_order": False,
            "manual_override_allowed": False,
            "cross_run_mixing_allowed": False,
        }, ensure_ascii=False, indent=2), stream=sys.stderr)
        return 2
    emit_best_effort(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def invoke_market_stage(
    script: str,
    args: list[str],
    *,
    output_paths: tuple[Path, ...],
    run_id: str,
    attempt: int,
    timeout_seconds: int,
) -> float:
    require_new_targets(output_paths)
    try:
        elapsed = invoke(script, args, timeout_seconds=timeout_seconds)
    except ChildInvocationError as exc:
        event = retryable_day_race_event(exc, run_id=run_id, attempt=attempt)
        if event is None:
            raise
        raise DayInputUpdateRaceError(
            f"{script}:{TDX_DAY_UPDATE_RACE}:attempt={attempt}",
            event=event,
        ) from exc
    for path in output_paths:
        bind_json_generation(path, run_id, attempt)
    return elapsed


def command_run() -> int:
    RUN.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex
    try:
        with RunLock(RUN_LOCK):
            started_at = datetime.now().astimezone().isoformat(timespec="seconds")
            running_state = {
                "status": "RUNNING",
                "run_id": run_id,
                "started_at": started_at,
                "automatic_order": False,
                "generated_at": started_at,
                "market_max_attempts": MARKET_MAX_ATTEMPTS,
            }
            transition_ok, transition_errors = write_state_transition(running_state)
            if not transition_ok:
                transition_failure = {
                    **running_state,
                    "status": "FAIL",
                    "failed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "failed_stage": "running_state_transition",
                    "reason": "state_transition_write_failed:" + " | ".join(transition_errors),
                }
                recovery_ok, recovery_errors = write_state_transition(transition_failure)
                if not recovery_ok:
                    transition_failure["state_recovery_errors"] = recovery_errors
                emit_best_effort(
                    json.dumps(transition_failure, ensure_ascii=False, indent=2),
                    stream=sys.stderr,
                )
                return 2
            stages: dict[str, float] = {}
            retry_history: list[dict[str, Any]] = []
            current_stage = "selftest"
            current_attempt = 0
            try:
                for attempt in range(1, MARKET_MAX_ATTEMPTS + 1):
                    current_attempt = attempt
                    try:
                        current_stage = "prepare_generation"
                        paths = prepare_generation(run_id, attempt)
                        stage_started = time.perf_counter()
                        current_stage = "selftest"
                        command_selftest(
                            run_id,
                            acquire_lock=False,
                            output_path=paths.selftest,
                            market_attempt=attempt,
                            emit_output=False,
                        )
                        stages["selftest"] = stages.get("selftest", 0.0) + (
                            time.perf_counter() - stage_started
                        )
                        cutoff = latest_local_benchmark_date()
                        current_stage = "early_redemption_announcements"
                        stages["early_redemption_announcements"] = stages.get(
                            "early_redemption_announcements", 0.0
                        ) + invoke_generation_stage(
                            "fetch_early_redemption_announcements.py",
                            [
                                "--output", str(paths.redemption_announcements),
                                "--run-id", run_id,
                                "--cutoff", cutoff,
                                "--workers", "4",
                                "--timeout-seconds", "20",
                                "--retries", "3",
                                "--page-size", "30",
                                "--max-pages", "20",
                            ],
                            output_paths=(paths.redemption_announcements,),
                            run_id=run_id,
                            attempt=attempt,
                            timeout_seconds=1800,
                        )
                        current_stage = "scan"
                        stages["scan"] = stages.get("scan", 0.0) + invoke_market_stage(
                            "run_convertible_bond_screening.py",
                            [
                                "--output", str(paths.result),
                                "--formula-evidence-output", str(paths.formula_evidence),
                                "--day-input-manifest-output", str(paths.day_input_manifest),
                                "--redemption-announcements", str(paths.redemption_announcements),
                                "--cutoff", cutoff,
                                "--run-id", run_id,
                                "--attempt", str(attempt),
                            ],
                            output_paths=(
                                paths.result,
                                paths.formula_evidence,
                                paths.day_input_manifest,
                            ),
                            run_id=run_id,
                            attempt=attempt,
                            timeout_seconds=240,
                        )
                        current_stage = "independent_verification"
                        stages["independent_verification"] = stages.get(
                            "independent_verification", 0.0
                        ) + invoke_market_stage(
                            "verify_convertible_bond_screening.py",
                            [
                                "--input", str(paths.result),
                                "--formula-evidence", str(paths.formula_evidence),
                                "--day-input-manifest", str(paths.day_input_manifest),
                                "--redemption-announcements", str(paths.redemption_announcements),
                                "--output", str(paths.verification),
                                "--run-id", run_id,
                                "--attempt", str(attempt),
                            ],
                            output_paths=(paths.verification,),
                            run_id=run_id,
                            attempt=attempt,
                            timeout_seconds=120,
                        )
                        current_stage = "independent_heat_verification"
                        stages["independent_heat_verification"] = stages.get(
                            "independent_heat_verification", 0.0
                        ) + invoke_market_stage(
                            "independent_heat_verifier.py",
                            [
                                "--compare-result", str(paths.result),
                                "--output", str(paths.independent_heat_verification),
                                "--attempt", str(attempt),
                            ],
                            output_paths=(paths.independent_heat_verification,),
                            run_id=run_id,
                            attempt=attempt,
                            timeout_seconds=120,
                        )
                        current_stage = "summary"
                        stages["summary"] = stages.get("summary", 0.0) + invoke_generation_stage(
                            "summarize_convertible_bond_screening.py",
                            [
                                "--input", str(paths.result),
                                "--verification", str(paths.verification),
                                "--output", str(paths.summary),
                                "--run-id", run_id,
                            ],
                            output_paths=(paths.summary,),
                            run_id=run_id,
                            attempt=attempt,
                            timeout_seconds=60,
                        )
                        current_stage = "top1_fixed_skills"
                        stages["top1_fixed_skills"] = stages.get(
                            "top1_fixed_skills", 0.0
                        ) + invoke_generation_stage(
                            "validate_top1_fixed_skills.py",
                            [
                                "--input", str(paths.result),
                                "--output", str(paths.top1_validation),
                                "--run-id", run_id,
                                "--attempt", str(attempt),
                            ],
                            output_paths=(paths.top1_validation,),
                            run_id=run_id,
                            attempt=attempt,
                            timeout_seconds=360,
                        )
                        current_stage = "persist_status"
                        write_status(run_id, attempt, stages, paths)

                        finalizing_at = datetime.now().astimezone().isoformat(timespec="seconds")
                        finalizing_state = {
                            "status": "FINALIZING",
                            "run_id": run_id,
                            "started_at": started_at,
                            "generated_at": finalizing_at,
                            "market_attempt": attempt,
                            "market_max_attempts": MARKET_MAX_ATTEMPTS,
                            "retry_count": len(retry_history),
                            "retry_history": retry_history,
                            "automatic_order": False,
                        }
                        current_stage = "finalizing_state_transition"
                        transition_ok, transition_errors = write_state_transition(
                            finalizing_state,
                            targets=((RUN_STATE, "CONVERTIBLE-BOND-SCREENING-RUN-STATE-1"),),
                        )
                        if not transition_ok:
                            raise RuntimeError(
                                "finalizing state transition failed:" + " | ".join(transition_errors)
                            )
                        current_stage = "status_readback"
                        status_code = command_status(
                            acquire_lock=False,
                            expected_run_state="FINALIZING",
                            emit_output=False,
                        )
                        if status_code != 0:
                            raise RuntimeError(
                                f"final status readback failed with exit code {status_code}"
                            )

                        current_stage = "publish_latest_summary"
                        latest_summary_publication = publish_latest_summary(
                            paths.summary,
                            run_id=run_id,
                            market_attempt=attempt,
                        )

                        current_stage = "final_pass_commit"
                        final_state = {
                            "schema": "CONVERTIBLE-BOND-SCREENING-RUN-STATE-1",
                            "status": "PASS",
                            "run_id": run_id,
                            "started_at": started_at,
                            "completed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                            "market_attempt": attempt,
                            "market_max_attempts": MARKET_MAX_ATTEMPTS,
                            "retry_count": len(retry_history),
                            "retry_history": retry_history,
                            "automatic_order": False,
                        }
                        atomic_write_json(RUN_STATE, final_state)
                        if load_json(RUN_STATE) != final_state:
                            raise RuntimeError("final PASS run state readback mismatch")
                        current_stage = "final_pass_status_readback"
                        status_code = command_status(
                            acquire_lock=False,
                            expected_run_state="PASS",
                            emit_output=False,
                        )
                        if status_code != 0:
                            raise RuntimeError(
                                f"PASS status readback failed with exit code {status_code}"
                            )
                        emit_best_effort(json.dumps({
                            "status": "PASS",
                            "run_id": run_id,
                            "market_attempt": attempt,
                            "retry_count": len(retry_history),
                            "automatic_order": False,
                            "run_state_path": str(RUN_STATE.resolve()),
                            "run_state_sha256": sha256(RUN_STATE),
                            "latest_summary_publication": latest_summary_publication,
                        }, ensure_ascii=False, indent=2))
                        return 0
                    except DayInputUpdateRaceError as exc:
                        event = exc.event or {}
                        retry_record = {
                            "attempt": attempt,
                            "failed_stage": current_stage,
                            "failure_code": TDX_DAY_UPDATE_RACE,
                            "child_schema": event.get("schema"),
                            "child_script": event.get("script"),
                            "child_exit_code": 3,
                            "error": event.get("error"),
                            "retryable": True,
                        }
                        if attempt < MARKET_MAX_ATTEMPTS:
                            delay_seconds = MARKET_RETRY_DELAYS_SECONDS[attempt - 1]
                            retry_record["retry_after_seconds"] = delay_seconds
                            retry_history.append(retry_record)
                            retry_at = datetime.now().astimezone().isoformat(timespec="seconds")
                            retry_state = {
                                "status": "RUNNING",
                                "run_id": run_id,
                                "started_at": started_at,
                                "generated_at": retry_at,
                                "market_attempt": attempt,
                                "next_market_attempt": attempt + 1,
                                "market_max_attempts": MARKET_MAX_ATTEMPTS,
                                "retry_count": len(retry_history),
                                "retry_history": retry_history,
                                "last_failure_code": TDX_DAY_UPDATE_RACE,
                                "automatic_order": False,
                            }
                            current_stage = "retry_state_transition"
                            transition_ok, transition_errors = write_state_transition(retry_state)
                            if not transition_ok:
                                raise RuntimeError(
                                    "retry state transition failed:" + " | ".join(transition_errors)
                                )
                            time.sleep(delay_seconds)
                            continue
                        retry_record["retry_exhausted"] = True
                        retry_history.append(retry_record)
                        raise
            except Exception as exc:
                failure = {
                    "schema": "CONVERTIBLE-BOND-SCREENING-RUN-STATE-1",
                    "status": "FAIL",
                    "run_id": run_id,
                    "started_at": started_at,
                    "failed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "failed_stage": current_stage,
                    "reason": f"{type(exc).__name__}:{exc}",
                    "market_attempt": current_attempt,
                    "market_max_attempts": MARKET_MAX_ATTEMPTS,
                    "retry_count": len(retry_history),
                    "retry_history": retry_history,
                    "automatic_order": False,
                }
                transition_ok, transition_errors = write_state_transition(failure)
                if not transition_ok:
                    failure["state_transition_errors"] = transition_errors
                emit_best_effort(
                    json.dumps(failure, ensure_ascii=False, indent=2),
                    stream=sys.stderr,
                )
                return 2
    except RunInProgressError:
        emit_best_effort(
            json.dumps({"status": "RUN_IN_PROGRESS", "automatic_order": False}, ensure_ascii=False)
        )
        return 3


def main() -> int:
    parser = argparse.ArgumentParser(description="可转债筛选策略固定Codex入口")
    parser.add_argument("command", choices=("info", "selftest", "run", "status", "deliver"))
    args = parser.parse_args()
    if args.command == "info":
        return command_info()
    if args.command == "selftest":
        return command_selftest()
    if args.command == "run":
        return command_run()
    if args.command == "status":
        return command_status()
    if args.command == "deliver":
        return command_deliver()
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
