#!/usr/bin/env python3
"""Canonical business-process adapter for one local Codex stock skill."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import codecs
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
_stock_adapter_shared_scripts = str(_OneStockEmbeddedPath(__file__).resolve().parents[3] / "scripts")
if _stock_adapter_shared_scripts not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _stock_adapter_shared_scripts)
from stock_adapter_io import atomic_write_json, atomic_write_text, enable_atomic_path_writes
from tdx_path_config import resolve_tdx_root


ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = ROOT.name
LEGACY_ENTRY = ROOT / "scripts" / "legacy_codex_entry.py"
DAILY_PRODUCTION_LOCK = ROOT / "references" / "daily-score-production-lock.json"
DAILY_PRODUCTION_LOCK_SHA256 = "1ea02a372e39e2c8d025670f73ef3ac8e94d4fbc09e7dbb4569495d56276cf4e"
DAILY_PRODUCTION_LOCK_V3 = ROOT / "references" / "daily-score-production-lock-v3.json"
DAILY_PRODUCTION_LOCK_V3_SHA256 = "8596f98a49fb954b4769edd87684f4f85972a8264ff3aea3bf0347c7987eede9"
SKILL_ENTRY = ROOT / "scripts" / "codex_entry.py"
DEFAULT_RECEIPT_ROOT = ROOT / "reports" / "executions"
CONTRACT_CATALOG = ROOT.parent / "stock-unified" / "references" / "stock_execution_contracts.json"
REPORT_TEMPLATE = ROOT / "references" / "feilong-report-template.json"
REPORT_VALIDATOR = ROOT / "scripts" / "feilong_report_validator.py"
FAILURE_TOKENS = (
    '"status": "BLOCKED"',
    '"status":"BLOCKED"',
    '"status": "FAILED"',
    '"status":"FAILED"',
    '"status": "FAIL"',
    '"status":"FAIL"',
    '"status": "ERROR"',
    '"status":"ERROR"',
    '"status": "PROCEDURAL"',
    '"status":"PROCEDURAL"',
    '"status": "DATA_REQUIRED"',
    '"status":"DATA_REQUIRED"',
    '"status": "DATA_STALE"',
    '"status":"DATA_STALE"',
    "Traceback (most recent call last)",
    "TIMEOUT after ",
)
DATA_GATE_DIMENSIONS = (
    "identity",
    "effective_trading_date",
    "quote_kline",
    "fundamentals",
    "news_announcements",
    "sector_theme",
    "source_freshness",
)
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_AUTHORIZATION_BYTES = 4 * 1024 * 1024
MAX_CONTROL_JSON_BYTES = 4 * 1024 * 1024
PHYSICAL_START = "19901219"
PHYSICAL_END = "20260826"
DELIVERY_STEM = "飞龙裸三色-全量K线回测-19901219-20260826"
CORE_RANGES = (
    ("19901219", "19961231"),
    ("19970101", "20011231"),
    ("20020101", "20021231"),
    ("20030101", "20031231"),
    ("20040101", "20041231"),
    ("20050101", "20051231"),
    ("20060101", "20061231"),
    ("20070101", "20071231"),
    ("20080101", "20081231"),
    ("20090101", "20091231"),
    ("20100101", "20101231"),
    ("20110101", "20111231"),
    ("20120101", "20121231"),
    ("20130101", "20141231"),
    ("20150101", "20161231"),
    ("20170101", "20201231"),
    ("20210101", "20260826"),
)
EXPECTED_FORMULA = {
    "selection_formula": "飞龙裸三色",
    "indicator_formula": None,
    "local_source_raw_sha256": "3029d0fda387842984f834b41f9849a9a71b933380cc7fedcb79d0d6cc73444b",
    "gbk_payload_sha256": "167fda25731a6f85da58b484769f4f3df6b0aaee8cc004223532a4dec0d9b263",
}
DELIVERY_ARTIFACT_KEYS = {
    "events_csv",
    "summary_json",
    "report_markdown",
    "day_inventory_csv",
}
EXPECTED_ZERO_BYTE_ANOMALIES = {
    ("sz/lday/sz131804.day", "ZERO_BYTE"),
    ("sz/lday/sz131807.day", "ZERO_BYTE"),
}
EXPECTED_NONSTANDARD_FILENAME = {
    "relative_path": "sz/lday/sz200b07.day",
    "filename_status": "NONSTANDARD",
    "size": 29216,
    "sha256": "c6158985199bf1009ce3b4e8c049e3c8818bcb173e020e9dce9e7abf554c163a",
}
DELIVERY_ROOT_KEYS = {
    "schema",
    "status",
    "delivery_status",
    "completion_scope",
    "formula",
    "segments",
    "inventory",
    "invariants",
    "artifacts",
    "manifest_integrity",
}
FORMULA_KEYS = set(EXPECTED_FORMULA)
SEGMENT_KEYS = {
    "core_start",
    "core_end",
    "invocation_start",
    "invocation_end",
    "formula",
    "backtest_json",
    "events_csv",
    "events_csv_size",
    "events_csv_sha256",
    "segment_manifest",
    "receipt",
    "authorization",
}
EVIDENCE_KEYS = {"path", "size", "sha256"}
AUTHORIZATION_EVIDENCE_KEYS = {
    *EVIDENCE_KEYS,
    "status",
    "delivery_kind",
    "binding_source",
    "manifest_source",
}
INVENTORY_KEYS = {
    "file_count",
    "valid_file_count",
    "anomaly_file_count",
    "nonstandard_filename_count",
    "nonstandard_filenames",
    "physical_start_date",
    "physical_end_date",
    "anomalies",
    "status",
    "validation_scope",
}
ANOMALY_KEYS = {"relative_path", "status"}
NONSTANDARD_FILENAME_KEYS = {
    "relative_path",
    "filename_status",
    "size",
    "sha256",
}
INVARIANT_KEYS = {
    "partition_violation_count",
    "nonfinite_metric_count",
    "gross_metric_below_or_equal_minus_100_count",
    "entry_date_order_violation_count",
    "mae_horizon_monotonicity_violation_count",
    "mfe_horizon_monotonicity_violation_count",
    "stress_subtraction_violation_count",
    "excursion_sign_violation_count",
    "horizon_sample_count_monotonicity_violation_count",
    "excluded_metric_violation_count",
    "tradable_entry_violation_count",
    "nonpositive_output_price_count",
    "horizon_sample_counts",
    "status",
}
HORIZON_SAMPLE_KEYS = {"1d", "3d", "5d", "10d", "20d"}
SEGMENT_MANIFEST_KEYS = {
    "schema",
    "status",
    "generated_at",
    "formula",
    "data",
    "artifacts",
    "validation",
}
SEGMENT_MANIFEST_FORMULA_KEYS = {
    "formula_type",
    "selection_formula",
    "indicator_formula",
    "local_source_path",
    "local_source_raw_sha256",
    "gbk_payload_sha256",
    "source_manifest_path",
    "source_manifest_sha256",
}
SEGMENT_DATA_KEYS = {"start_date", "end_date", "universe_count", "signal_count"}
SEGMENT_ARTIFACT_KEYS = {"backtest_json", "events_csv"}
SEGMENT_VALIDATION_KEYS = {
    "status",
    "errors",
    "formula_source_bound",
    "artifact_hashes_verified",
}
AUTHORIZATION_KEYS = {
    "schema",
    "runtime",
    "runtime_surface",
    "skill_id",
    "status",
    "delivery_kind",
    "created_at",
    "receipt",
    "artifact",
    "binding_source",
    "manifest_source",
    "errors",
    "authorization",
    "authorization_path",
}
AUTHORIZATION_RECEIPT_KEYS = {"path", "sha256", "contract_sha256"}
FINAL_ARTIFACT_FILENAMES = {
    "events_csv": f"{DELIVERY_STEM}-逐信号.csv",
    "summary_json": f"{DELIVERY_STEM}-汇总.json",
    "report_markdown": f"{DELIVERY_STEM}-报告.md",
    "day_inventory_csv": f"{DELIVERY_STEM}-全量日线清单.csv",
}
HORIZONS = (1, 3, 5, 10, 20)
EVENT_CSV_COLUMNS = (
    "symbol",
    "signal_date",
    "entry_date",
    "signal_close",
    "entry_open",
    "entry_gap_pct",
    "tradable_next_open",
    "exclusion_reason",
    *(
        column
        for horizon in HORIZONS
        for column in (
            f"return_{horizon}d_pct",
            f"net_return_{horizon}d_pct",
            f"mae_{horizon}d_pct",
            f"mfe_{horizon}d_pct",
        )
    ),
)
BACKTEST_ROOT_KEYS = {
    "schema",
    "status",
    "generated_at",
    "formula",
    "data",
    "execution_model",
    "summary",
    "signal_date_min",
    "signal_date_max",
}
BACKTEST_FORMULA_KEYS = {
    "formula_type",
    "formula_display_name",
    "selection_formula",
    "indicator_formula",
    "local_source_path",
    "local_source_encoding",
    "local_source_bom",
    "local_source_size_bytes",
    "local_source_sha256",
    "local_source_raw_sha256",
    "payload_encoding",
    "gbk_payload_size_bytes",
    "gbk_payload_sha256",
    "source_manifest_path",
    "source_manifest_sha256",
    "source_authority_scope",
    "interpretation",
    "known_semantic_risks",
}
BACKTEST_INTERPRETATION_KEYS = {"subsystem", "logic", "role_in_xg"}
BACKTEST_DATA_KEYS = {
    "source",
    "tdx_root",
    "start_date",
    "end_date",
    "latest_loaded_kline_date",
    "universe_count",
    "signal_stock_count",
    "formula_batch_count",
    "formula_calls",
}
FORMULA_CALL_KEYS = {
    "batch_start",
    "stock_count",
    "error_id",
    "signal_count",
    "formula_mode",
}
BACKTEST_EXECUTION_MODEL_KEYS = {
    "signal_confirmation",
    "entry",
    "horizons_trading_days",
    "exit",
    "one_price_limit_up_entry",
    "gross_return",
    "net_stress",
    "portfolio_curve",
}
BACKTEST_SUMMARY_KEYS = {
    "signal_count",
    "tradable_signal_count",
    "excluded_one_price_limit_up_count",
    "missing_entry_data_count",
    "horizons",
}
BACKTEST_HORIZON_KEYS = {
    "sample_count",
    "win_rate_pct",
    "mean_return_pct",
    "median_return_pct",
    "mean_net_return_pct",
    "p25_return_pct",
    "p75_return_pct",
    "min_return_pct",
    "max_return_pct",
    "worst_mae_pct",
}
RECEIPT_KEYS = {
    "binding_errors",
    "business_bindings",
    "business_stdout_validation",
    "command",
    "contract_sha256",
    "cwd",
    "elapsed_seconds",
    "entry",
    "evidence_set",
    "executor_sha256",
    "extra_args",
    "facade_sha256",
    "finished_at",
    "receipt_integrity",
    "receipt_version",
    "required_artifacts",
    "returncode",
    "run_dir",
    "runtime",
    "runtime_surface",
    "semantic_assertions",
    "skill_id",
    "started_at",
    "status",
    "stderr_artifact",
    "stdout_artifact",
    "stock_business_lease",
    "supplemental_sources",
    "tdx_process_guard",
    "tdx_process_integrity",
}
BUSINESS_BINDING_EVIDENCE_KEYS = {"path", "sha256"}
STOCK_BUSINESS_LEASE_KEYS = {
    "status",
    "skill_id",
    "lease_id",
    "root_skill_id",
    "root_lease_id",
    "lock_path",
    "pid",
    "acquired_at",
    "waited_seconds",
}
TDX_PROCESS_INTEGRITY_KEYS = {"status", "errors", "before", "after"}
TDX_PROCESS_SNAPSHOT_KEYS = {"status", "captured_at", "processes", "errors"}
TDX_PROCESS_ROW_KEYS = {"name", "pid", "start_time"}
TDX_PROCESS_GUARD_KEYS = {
    "schema",
    "status",
    "path",
    "exists",
    "event_count",
    "events",
    "errors",
    "artifact",
}
EVIDENCE_SET_KEYS = {"enabled", "status", "environment", "errors"}
SUPPLEMENTAL_SOURCE_KEYS = {"lianban_daily"}
LIANBAN_SOURCE_KEYS = {
    "enabled",
    "required",
    "status",
    "client",
    "command",
    "snapshot",
    "source_url",
    "open_data_url",
    "target_date_resolution",
    "child",
    "environment",
    "errors",
}
LIANBAN_TARGET_DATE_KEYS = {
    "status",
    "mode",
    "target_date",
    "fallback_date",
    "errors",
}
LIANBAN_CHILD_KEYS = {
    "effective_command",
    "started_at",
    "finished_at",
    "elapsed_seconds",
    "returncode",
    "stdout",
    "stderr",
    "tdx_process_integrity",
}
LIANBAN_ENVIRONMENT_KEYS = {
    "CODEX_LIANBAN_STATUS",
    "CODEX_LIANBAN_SNAPSHOT",
    "CODEX_LIANBAN_SOURCE_URL",
    "CODEX_LIANBAN_OPEN_DATA_URL",
    "CODEX_LIANBAN_ATTRIBUTION",
}
BUSINESS_STDOUT_VALIDATION_KEYS = {"ok", "errors"}
SEMANTIC_ASSERTION_KEYS = {
    "returncode_zero": {"type", "actual", "ok"},
    "stdout_nonempty": {"type", "actual_size", "ok"},
    "output_contains_any": {"type", "values", "found", "ok"},
    "output_not_contains": {"type", "values", "found", "ok"},
    "required_artifact": {
        "type",
        "path",
        "minimum_size",
        "matched",
        "ok",
    },
}
SEMANTIC_ASSERTION_TYPES = (
    "returncode_zero",
    "stdout_nonempty",
    "output_contains_any",
    "output_contains_any",
    "output_not_contains",
    "required_artifact",
    "required_artifact",
    "required_artifact",
)
BUSINESS_RESULT_KEYS = {
    "schema",
    "skill_id",
    "status",
    "business_process",
    "business_binding",
    "artifacts",
}
BUSINESS_PROCESS_KEYS = {
    "command",
    "cwd",
    "returncode",
    "timed_out",
    "failure_tokens",
}
NORMAL_BUSINESS_BINDING_KEYS = {"path", "sha256"}
NORMAL_BUSINESS_ARTIFACT_KEYS = {
    "stdout",
    "stderr",
    "backtest_json",
    "events_csv",
    "segment_manifest",
}
RECEIPT_FILENAME_RE = re.compile(
    rf"^{re.escape(SKILL_ID)}-\d{{8}}-\d{{6}}-\d{{6}}\.receipt\.json$"
)
RUN_DIR_NAME_RE = re.compile(r"^\d{8}-\d{6}-\d{6}$")
SYMBOL_RE = re.compile(r"^\d{6}\.(?:SH|SZ|BJ)$")
DATE_RE = re.compile(r"^\d{8}$")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_signature(path: Path) -> tuple[int, int, int]:
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, getattr(stat, "st_ino", 0)


def read_stable_bytes(path: Path, *, max_bytes: int | None = None) -> bytes:
    before = _file_signature(path)
    if max_bytes is not None and before[0] > max_bytes:
        raise RuntimeError(f"file exceeds size limit: {path}")
    with path.open("rb") as handle:
        content = handle.read() if max_bytes is None else handle.read(max_bytes + 1)
    after = _file_signature(path)
    if before != after or len(content) != before[0]:
        raise RuntimeError(f"file changed while reading: {path}")
    if max_bytes is not None and len(content) > max_bytes:
        raise RuntimeError(f"file exceeds size limit: {path}")
    return content


def _stable_file_evidence(
    path: Path, *, max_bytes: int | None = None
) -> tuple[bytes, dict[str, object]]:
    content = read_stable_bytes(path, max_bytes=max_bytes)
    return content, {
        "path": str(path.resolve()),
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _stream_file_evidence(path: Path) -> dict[str, object]:
    before = _file_signature(path)
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    after = _file_signature(path)
    if before != after or size != before[0]:
        raise RuntimeError(f"file changed while hashing: {path}")
    return {
        "path": str(path.resolve()),
        "size": size,
        "sha256": digest.hexdigest(),
    }


def _canonical_payload_hash(payload: dict[str, object], excluded: str) -> str:
    material = {key: value for key, value in payload.items() if key != excluded}
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_manifest_hash(payload: dict[str, object]) -> str:
    return _canonical_payload_hash(payload, "manifest_integrity")


def _require_exact_keys(value: dict, expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise RuntimeError(
            f"{label} keys mismatch: expected={sorted(expected)}, actual={sorted(actual)}"
        )


def _require_exact_dict(
    value: object, expected: set[str], label: str
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be an object")
    _require_exact_keys(value, expected, label)
    return value


def _require_nonnegative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise RuntimeError(f"{label} must be a nonnegative integer")
    return value


def _validate_process_integrity(value: object, label: str) -> None:
    integrity = _require_exact_dict(value, TDX_PROCESS_INTEGRITY_KEYS, label)
    for phase in ("before", "after"):
        snapshot = _require_exact_dict(
            integrity.get(phase), TDX_PROCESS_SNAPSHOT_KEYS, f"{label} {phase}"
        )
        processes = snapshot.get("processes")
        if not isinstance(processes, list):
            raise RuntimeError(f"{label} {phase} processes must be a list")
        for index, process in enumerate(processes, start=1):
            _require_exact_dict(
                process,
                TDX_PROCESS_ROW_KEYS,
                f"{label} {phase} process {index}",
            )
        if not isinstance(snapshot.get("errors"), list):
            raise RuntimeError(f"{label} {phase} errors must be a list")
    if not isinstance(integrity.get("errors"), list):
        raise RuntimeError(f"{label} errors must be a list")


def _validate_receipt_shape(receipt: dict[str, object], label: str) -> None:
    _require_exact_keys(receipt, RECEIPT_KEYS, label)
    bindings = receipt.get("business_bindings")
    if not isinstance(bindings, list) or not bindings:
        raise RuntimeError(f"{label} business bindings missing")
    for index, binding in enumerate(bindings, start=1):
        row = _require_exact_dict(
            binding,
            BUSINESS_BINDING_EVIDENCE_KEYS,
            f"{label} business binding {index}",
        )
        path_text = row.get("path")
        digest = row.get("sha256")
        if (
            not isinstance(path_text, str)
            or not Path(path_text).is_absolute()
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-fA-F]{64}", digest)
        ):
            raise RuntimeError(f"{label} business binding invalid")

    _require_exact_dict(
        receipt.get("stock_business_lease"),
        STOCK_BUSINESS_LEASE_KEYS,
        f"{label} stock business lease",
    )
    _validate_process_integrity(
        receipt.get("tdx_process_integrity"), f"{label} TDX process integrity"
    )
    guard = _require_exact_dict(
        receipt.get("tdx_process_guard"),
        TDX_PROCESS_GUARD_KEYS,
        f"{label} TDX process guard",
    )
    if guard.get("artifact") is not None:
        _require_exact_dict(
            guard.get("artifact"), EVIDENCE_KEYS, f"{label} TDX guard artifact"
        )
    if not isinstance(guard.get("events"), list) or not isinstance(
        guard.get("errors"), list
    ):
        raise RuntimeError(f"{label} TDX process guard list fields invalid")

    evidence_set = _require_exact_dict(
        receipt.get("evidence_set"), EVIDENCE_SET_KEYS, f"{label} evidence set"
    )
    if not isinstance(evidence_set.get("environment"), dict) or not isinstance(
        evidence_set.get("errors"), list
    ):
        raise RuntimeError(f"{label} evidence set structure invalid")

    supplemental = _require_exact_dict(
        receipt.get("supplemental_sources"),
        SUPPLEMENTAL_SOURCE_KEYS,
        f"{label} supplemental sources",
    )
    lianban = _require_exact_dict(
        supplemental.get("lianban_daily"),
        LIANBAN_SOURCE_KEYS,
        f"{label} lianban source",
    )
    _require_exact_dict(
        lianban.get("snapshot"), EVIDENCE_KEYS, f"{label} lianban snapshot"
    )
    target_date = _require_exact_dict(
        lianban.get("target_date_resolution"),
        LIANBAN_TARGET_DATE_KEYS,
        f"{label} lianban target date",
    )
    if not isinstance(target_date.get("errors"), list):
        raise RuntimeError(f"{label} lianban target-date errors invalid")
    child = _require_exact_dict(
        lianban.get("child"), LIANBAN_CHILD_KEYS, f"{label} lianban child"
    )
    _validate_process_integrity(
        child.get("tdx_process_integrity"),
        f"{label} lianban child TDX process integrity",
    )
    _require_exact_dict(
        lianban.get("environment"),
        LIANBAN_ENVIRONMENT_KEYS,
        f"{label} lianban environment",
    )
    if not isinstance(lianban.get("errors"), list):
        raise RuntimeError(f"{label} lianban errors invalid")

    stdout_validation = _require_exact_dict(
        receipt.get("business_stdout_validation"),
        BUSINESS_STDOUT_VALIDATION_KEYS,
        f"{label} business stdout validation",
    )
    if not isinstance(stdout_validation.get("errors"), list):
        raise RuntimeError(f"{label} business stdout validation errors invalid")

    assertions = receipt.get("semantic_assertions")
    if not isinstance(assertions, list) or tuple(
        row.get("type") if isinstance(row, dict) else None for row in assertions
    ) != SEMANTIC_ASSERTION_TYPES:
        raise RuntimeError(f"{label} semantic assertion structure mismatch")
    for index, assertion in enumerate(assertions, start=1):
        assertion_type = str(assertion.get("type"))
        _require_exact_keys(
            assertion,
            SEMANTIC_ASSERTION_KEYS[assertion_type],
            f"{label} semantic assertion {index}",
        )
        if assertion.get("ok") is not True:
            raise RuntimeError(f"{label} semantic assertion {index} is not clean")

    required = receipt.get("required_artifacts")
    if not isinstance(required, list) or len(required) != 3:
        raise RuntimeError(f"{label} required artifacts structure mismatch")
    for index, evidence in enumerate(required, start=1):
        _require_exact_dict(
            evidence, EVIDENCE_KEYS, f"{label} required artifact {index}"
        )
    _require_exact_dict(
        receipt.get("stdout_artifact"), EVIDENCE_KEYS, f"{label} stdout artifact"
    )
    _require_exact_dict(
        receipt.get("stderr_artifact"), EVIDENCE_KEYS, f"{label} stderr artifact"
    )


def _validate_backtest_payload(
    backtest: dict[str, object], label: str, core_end: str
) -> dict[str, object]:
    _require_exact_keys(backtest, BACKTEST_ROOT_KEYS, label)
    formula = _require_exact_dict(
        backtest.get("formula"), BACKTEST_FORMULA_KEYS, f"{label} formula"
    )
    _validate_formula_subset(formula, label)
    if formula.get("formula_type") != "condition_selection":
        raise RuntimeError(f"{label} formula type mismatch")
    for key in ("local_source_path", "source_manifest_path"):
        path_text = formula.get(key)
        if not isinstance(path_text, str) or not Path(path_text).is_absolute():
            raise RuntimeError(f"{label} formula {key} must be absolute")
    interpretation = formula.get("interpretation")
    if not isinstance(interpretation, list):
        raise RuntimeError(f"{label} formula interpretation must be a list")
    for index, row in enumerate(interpretation, start=1):
        _require_exact_dict(
            row,
            BACKTEST_INTERPRETATION_KEYS,
            f"{label} formula interpretation {index}",
        )
    if not isinstance(formula.get("known_semantic_risks"), list):
        raise RuntimeError(f"{label} formula risks must be a list")

    data = _require_exact_dict(
        backtest.get("data"), BACKTEST_DATA_KEYS, f"{label} data"
    )
    if (
        str(data.get("start_date", "")) != PHYSICAL_START
        or str(data.get("end_date", "")) != core_end
    ):
        raise RuntimeError(f"{label} invocation range mismatch")
    universe_count = _require_nonnegative_int(
        data.get("universe_count"), f"{label} universe count"
    )
    signal_stock_count = _require_nonnegative_int(
        data.get("signal_stock_count"), f"{label} signal stock count"
    )
    formula_batch_count = _require_nonnegative_int(
        data.get("formula_batch_count"), f"{label} formula batch count"
    )
    formula_calls = data.get("formula_calls")
    if not isinstance(formula_calls, list) or len(formula_calls) != formula_batch_count:
        raise RuntimeError(f"{label} formula calls mismatch")
    formula_signal_count = 0
    for index, call in enumerate(formula_calls, start=1):
        row = _require_exact_dict(
            call, FORMULA_CALL_KEYS, f"{label} formula call {index}"
        )
        _require_nonnegative_int(row.get("stock_count"), f"{label} formula stock count")
        formula_signal_count += _require_nonnegative_int(
            row.get("signal_count"), f"{label} formula signal count"
        )
    execution_model = _require_exact_dict(
        backtest.get("execution_model"),
        BACKTEST_EXECUTION_MODEL_KEYS,
        f"{label} execution model",
    )
    if execution_model.get("horizons_trading_days") != list(HORIZONS):
        raise RuntimeError(f"{label} execution horizons mismatch")

    summary = _require_exact_dict(
        backtest.get("summary"), BACKTEST_SUMMARY_KEYS, f"{label} summary"
    )
    summary_count = _require_nonnegative_int(
        summary.get("signal_count"), f"{label} summary signal count"
    )
    for key in (
        "tradable_signal_count",
        "excluded_one_price_limit_up_count",
        "missing_entry_data_count",
    ):
        _require_nonnegative_int(summary.get(key), f"{label} summary {key}")
    if formula_signal_count != summary_count:
        raise RuntimeError(f"{label} formula/summary signal count mismatch")
    horizons = _require_exact_dict(
        summary.get("horizons"),
        {f"{horizon}d" for horizon in HORIZONS},
        f"{label} summary horizons",
    )
    for horizon in HORIZONS:
        row = _require_exact_dict(
            horizons.get(f"{horizon}d"),
            BACKTEST_HORIZON_KEYS,
            f"{label} summary horizon {horizon}d",
        )
        _require_nonnegative_int(
            row.get("sample_count"), f"{label} horizon {horizon}d sample count"
        )
        for key in BACKTEST_HORIZON_KEYS - {"sample_count"}:
            metric = row.get(key)
            if metric is not None and (
                isinstance(metric, bool)
                or not isinstance(metric, (int, float))
                or not float(metric) == float(metric)
                or abs(float(metric)) == float("inf")
            ):
                raise RuntimeError(f"{label} horizon {horizon}d metric invalid")

    for key in ("signal_date_min", "signal_date_max"):
        date_value = backtest.get(key)
        if date_value is not None and (
            not isinstance(date_value, str)
            or DATE_RE.fullmatch(date_value) is None
            or not PHYSICAL_START <= date_value <= core_end
        ):
            raise RuntimeError(f"{label} {key} invalid")
    return {
        "signal_count": summary_count,
        "signal_stock_count": signal_stock_count,
        "universe_count": universe_count,
        "signal_date_min": backtest.get("signal_date_min"),
        "signal_date_max": backtest.get("signal_date_max"),
    }


def _validate_events_csv(
    value: object,
    label: str,
    *,
    expected_path: Path,
    core_start: str,
    core_end: str,
    expected_signal_count: int,
    expected_signal_stock_count: int,
    expected_signal_date_min: object,
    expected_signal_date_max: object,
) -> dict[str, object]:
    before = _file_signature(expected_path)
    _content, evidence = _validate_declared_evidence(value, label, stream=True)
    with expected_path.open("rb") as handle:
        if handle.read(3) != codecs.BOM_UTF8:
            raise RuntimeError(f"{label} must use UTF-8 BOM")
    seen: set[tuple[str, str]] = set()
    signal_dates: list[str] = []
    symbols: set[str] = set()
    numeric_columns = {
        "signal_close",
        "entry_open",
        "entry_gap_pct",
        *(
            column
            for horizon in HORIZONS
            for column in (
                f"return_{horizon}d_pct",
                f"net_return_{horizon}d_pct",
                f"mae_{horizon}d_pct",
                f"mfe_{horizon}d_pct",
            )
        ),
    }
    try:
        with expected_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
            if header is None or tuple(header) != EVENT_CSV_COLUMNS:
                raise RuntimeError(f"{label} columns mismatch")
            for line_number, values in enumerate(reader, start=2):
                if len(values) != len(EVENT_CSV_COLUMNS):
                    raise RuntimeError(f"{label} row width mismatch at line {line_number}")
                row = dict(zip(EVENT_CSV_COLUMNS, values))
                symbol = row["symbol"]
                signal_date = row["signal_date"]
                if SYMBOL_RE.fullmatch(symbol) is None:
                    raise RuntimeError(f"{label} symbol invalid at line {line_number}")
                if (
                    DATE_RE.fullmatch(signal_date) is None
                    or not core_start <= signal_date <= core_end
                ):
                    raise RuntimeError(f"{label} signal date invalid at line {line_number}")
                entry_date = row["entry_date"]
                if entry_date and DATE_RE.fullmatch(entry_date) is None:
                    raise RuntimeError(f"{label} entry date invalid at line {line_number}")
                if row["tradable_next_open"] not in {"True", "False"}:
                    raise RuntimeError(f"{label} tradable flag invalid at line {line_number}")
                for column in numeric_columns:
                    text = row[column]
                    if not text:
                        continue
                    try:
                        number = float(text)
                    except ValueError as exc:
                        raise RuntimeError(
                            f"{label} numeric value invalid at line {line_number}"
                        ) from exc
                    if not number == number or abs(number) == float("inf"):
                        raise RuntimeError(
                            f"{label} numeric value non-finite at line {line_number}"
                        )
                key = (symbol, signal_date)
                if key in seen:
                    raise RuntimeError(f"{label} duplicate signal key")
                seen.add(key)
                symbols.add(symbol)
                signal_dates.append(signal_date)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise RuntimeError(f"{label} unreadable: {exc}") from exc
    after = _file_signature(expected_path)
    if before != after:
        raise RuntimeError(f"{label} changed while validating")
    if len(seen) != expected_signal_count:
        raise RuntimeError(f"{label} signal row count mismatch")
    if len(symbols) != expected_signal_stock_count:
        raise RuntimeError(f"{label} signal stock count mismatch")
    actual_min = min(signal_dates, default=None)
    actual_max = max(signal_dates, default=None)
    if actual_min != expected_signal_date_min or actual_max != expected_signal_date_max:
        raise RuntimeError(f"{label} signal date bounds mismatch")
    return evidence


def _validate_formula(value: object, label: str) -> None:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} formula mismatch")
    _require_exact_keys(value, FORMULA_KEYS, f"{label} formula")
    if any(value.get(key) != expected for key, expected in EXPECTED_FORMULA.items()):
        raise RuntimeError(f"{label} formula mismatch")


def _validate_declared_evidence(
    value: object,
    label: str,
    *,
    max_bytes: int | None = None,
    expected_keys: set[str] = EVIDENCE_KEYS,
    stream: bool = False,
) -> tuple[bytes | None, dict[str, object]]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} evidence missing")
    _require_exact_keys(value, expected_keys, f"{label} evidence")
    path_text = value.get("path")
    if not isinstance(path_text, str) or not path_text or not Path(path_text).is_absolute():
        raise RuntimeError(f"{label} path must be absolute")
    path = Path(path_text).resolve()
    if not path.is_file():
        raise RuntimeError(f"{label} file missing: {path}")
    if stream:
        content = None
        evidence = _stream_file_evidence(path)
    else:
        content, evidence = _stable_file_evidence(path, max_bytes=max_bytes)
    if value.get("size") != evidence["size"]:
        raise RuntimeError(f"{label} artifact size mismatch")
    if str(value.get("sha256", "")).casefold() != evidence["sha256"]:
        raise RuntimeError(f"{label} artifact hash mismatch")
    return content, evidence


def _require_within(path: Path, root: Path, label: str) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"{label} must be within fixed receipt root: {root}") from exc


def _require_business_runs_path(path: Path, receipt_root: Path) -> None:
    try:
        path.resolve().relative_to((receipt_root / "runs").resolve())
    except (OSError, ValueError) as exc:
        raise RuntimeError(
            f"business result must be within business result runs root: {receipt_root / 'runs'}"
        ) from exc


def _load_json_bytes(content: bytes, label: str) -> dict[str, object]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant: {value}")

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(
            content.decode("utf-8-sig"),
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicate_keys,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"{label} unreadable: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be a JSON object")
    return value


def load_current_contract_sha256() -> str:
    content = read_stable_bytes(CONTRACT_CATALOG, max_bytes=MAX_CONTROL_JSON_BYTES)
    payload = _load_json_bytes(content, "stock execution contracts")
    contracts = payload.get("contracts")
    if not isinstance(contracts, list):
        raise RuntimeError("stock execution contracts list missing")
    rows = [
        row
        for row in contracts
        if isinstance(row, dict) and row.get("skill_id") == "feilong-strategy"
    ]
    if len(rows) != 1:
        raise RuntimeError("feilong canonical contract missing or duplicated")
    digest = rows[0].get("contract_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise RuntimeError("feilong canonical contract hash invalid")
    return digest.casefold()


def _load_control_evidence(
    value: object,
    label: str,
    *,
    max_bytes: int = MAX_CONTROL_JSON_BYTES,
    expected_keys: set[str] = EVIDENCE_KEYS,
) -> tuple[dict[str, object], dict[str, object], Path]:
    content, evidence = _validate_declared_evidence(
        value,
        label,
        max_bytes=max_bytes,
        expected_keys=expected_keys,
    )
    if content is None:
        raise RuntimeError(f"{label} control content unavailable")
    return (
        _load_json_bytes(content, label),
        evidence,
        Path(str(evidence["path"])),
    )


def _declared_evidence_path(
    value: object,
    label: str,
    *,
    expected_keys: set[str] = EVIDENCE_KEYS,
) -> Path:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} evidence missing")
    _require_exact_keys(value, expected_keys, f"{label} evidence")
    path_text = value.get("path")
    if not isinstance(path_text, str) or not path_text or not Path(path_text).is_absolute():
        raise RuntimeError(f"{label} path must be absolute")
    return Path(path_text).resolve()


def _validate_formula_subset(value: object, label: str) -> None:
    if not isinstance(value, dict) or any(
        value.get(key) != expected for key, expected in EXPECTED_FORMULA.items()
    ):
        raise RuntimeError(f"{label} formula mismatch")


def _evidence_matches(
    declared: object, actual: dict[str, object], expected_path: Path
) -> bool:
    return (
        isinstance(declared, dict)
        and set(declared) == EVIDENCE_KEYS
        and isinstance(declared.get("path"), str)
        and Path(str(declared["path"])).is_absolute()
        and Path(str(declared["path"])).resolve() == expected_path.resolve()
        and declared.get("size") == actual.get("size")
        and str(declared.get("sha256", "")).casefold()
        == str(actual.get("sha256", "")).casefold()
    )


def validate_delivery_manifest(
    manifest_path: Path,
    *,
    receipt_root: Path | None = None,
    expected_contract_sha256: str | None = None,
) -> dict[str, dict[str, object]]:
    resolved_receipt_root = (receipt_root or DEFAULT_RECEIPT_ROOT).resolve()
    contract_sha256 = (
        expected_contract_sha256.casefold()
        if expected_contract_sha256 is not None
        else load_current_contract_sha256()
    )
    if len(contract_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in contract_sha256
    ):
        raise RuntimeError("feilong canonical contract hash invalid")
    raw_path = Path(manifest_path)
    if not raw_path.is_absolute():
        raise RuntimeError("delivery manifest path must be absolute")
    path = raw_path.resolve()
    if not path.is_file():
        raise RuntimeError(f"delivery manifest missing: {path}")
    expected_manifest_name = f"{DELIVERY_STEM}-交付manifest.json"
    if path.name != expected_manifest_name:
        raise RuntimeError(
            f"delivery manifest filename mismatch: expected={expected_manifest_name}"
        )
    content, manifest_evidence = _stable_file_evidence(
        path, max_bytes=MAX_MANIFEST_BYTES
    )
    manifest = _load_json_bytes(content, "delivery manifest")
    if manifest.get("schema") != "FEILONG_NAKED_BACKTEST_DELIVERY_MANIFEST_V1":
        raise RuntimeError("delivery manifest schema mismatch")
    if manifest.get("status") != "CLEAN_PASS":
        raise RuntimeError("delivery manifest root status mismatch")
    _require_exact_keys(manifest, DELIVERY_ROOT_KEYS, "delivery manifest root")
    if manifest.get("delivery_status") != "DONE_WITH_CONCERNS":
        raise RuntimeError("delivery manifest delivery status mismatch")
    if (
        manifest.get("completion_scope")
        != "merge-acceptor-output-not-live-backtest-claim"
    ):
        raise RuntimeError("delivery manifest completion scope mismatch")
    if manifest.get("manifest_integrity") != _canonical_manifest_hash(manifest):
        raise RuntimeError("delivery manifest integrity mismatch")
    _validate_formula(manifest.get("formula"), "delivery manifest")

    segments = manifest.get("segments")
    if not isinstance(segments, list) or len(segments) != len(CORE_RANGES):
        actual_count = len(segments) if isinstance(segments, list) else -1
        raise RuntimeError(
            f"delivery manifest segment count mismatch: expected=17, actual={actual_count}"
        )
    for index, (segment, (core_start, core_end)) in enumerate(
        zip(segments, CORE_RANGES), start=1
    ):
        if not isinstance(segment, dict):
            raise RuntimeError(f"delivery manifest segment {index} invalid")
        _require_exact_keys(
            segment, SEGMENT_KEYS, f"delivery manifest segment {index}"
        )
        if (
            str(segment.get("core_start", "")) != core_start
            or str(segment.get("core_end", "")) != core_end
            or str(segment.get("invocation_start", "")) != PHYSICAL_START
            or str(segment.get("invocation_end", "")) != core_end
        ):
            raise RuntimeError(f"delivery manifest segment {index} range mismatch")
        _validate_formula(segment.get("formula"), f"delivery manifest segment {index}")
        segment_manifest_value = segment.get("segment_manifest")
        segment_manifest_path = _declared_evidence_path(
            segment_manifest_value, f"segment {index} manifest"
        )
        if segment_manifest_path.name != "feilong_backtest_segment_manifest.json":
            raise RuntimeError(f"segment {index} manifest filename mismatch")
        output_dir = segment_manifest_path.parent.resolve()
        segment_manifest, segment_manifest_evidence, loaded_segment_manifest_path = (
            _load_control_evidence(
                segment_manifest_value,
                f"segment {index} manifest",
                max_bytes=MAX_CONTROL_JSON_BYTES,
            )
        )
        if loaded_segment_manifest_path != segment_manifest_path:
            raise RuntimeError(f"segment {index} manifest path mismatch")
        _require_exact_keys(
            segment_manifest,
            SEGMENT_MANIFEST_KEYS,
            f"segment {index} manifest",
        )
        if (
            segment_manifest.get("schema")
            != "FEILONG_BACKTEST_SEGMENT_MANIFEST_V1"
            or segment_manifest.get("status") != "CLEAN_PASS"
        ):
            raise RuntimeError(f"segment {index} manifest schema/status mismatch")
        segment_formula = segment_manifest.get("formula")
        if not isinstance(segment_formula, dict):
            raise RuntimeError(f"segment {index} manifest formula mismatch")
        _require_exact_keys(
            segment_formula,
            SEGMENT_MANIFEST_FORMULA_KEYS,
            f"segment {index} manifest formula",
        )
        if segment_formula.get("formula_type") != "condition_selection":
            raise RuntimeError(f"segment {index} manifest formula type mismatch")
        _validate_formula_subset(segment_formula, f"segment {index} manifest")
        for source_key in ("local_source_path", "source_manifest_path"):
            source_text = segment_formula.get(source_key)
            if (
                not isinstance(source_text, str)
                or not source_text
                or not Path(source_text).is_absolute()
            ):
                raise RuntimeError(
                    f"segment {index} manifest formula {source_key} must be absolute"
                )
        segment_data = segment_manifest.get("data")
        if not isinstance(segment_data, dict):
            raise RuntimeError(f"segment {index} manifest data mismatch")
        _require_exact_keys(
            segment_data, SEGMENT_DATA_KEYS, f"segment {index} manifest data"
        )
        if (
            str(segment_data.get("start_date", "")) != PHYSICAL_START
            or str(segment_data.get("end_date", "")) != core_end
        ):
            raise RuntimeError(f"segment {index} manifest invocation range mismatch")
        segment_signal_count = _require_nonnegative_int(
            segment_data.get("signal_count"),
            f"segment {index} manifest signal count",
        )
        _require_nonnegative_int(
            segment_data.get("universe_count"),
            f"segment {index} manifest universe count",
        )
        segment_validation = segment_manifest.get("validation")
        if not isinstance(segment_validation, dict):
            raise RuntimeError(f"segment {index} manifest validation mismatch")
        _require_exact_keys(
            segment_validation,
            SEGMENT_VALIDATION_KEYS,
            f"segment {index} manifest validation",
        )
        if (
            segment_validation.get("status") != "CLEAN_PASS"
            or segment_validation.get("errors") != []
            or segment_validation.get("formula_source_bound") is not True
            or segment_validation.get("artifact_hashes_verified") is not True
        ):
            raise RuntimeError(f"segment {index} manifest validation is not clean")

        segment_artifacts = segment_manifest.get("artifacts")
        if not isinstance(segment_artifacts, dict):
            raise RuntimeError(f"segment {index} manifest artifacts missing")
        _require_exact_keys(
            segment_artifacts,
            SEGMENT_ARTIFACT_KEYS,
            f"segment {index} manifest artifacts",
        )
        expected_backtest_path = output_dir / "feilong_backtest.json"
        expected_events_path = output_dir / "feilong_backtest_events.csv"
        backtest_text = segment.get("backtest_json")
        events_text = segment.get("events_csv")
        if (
            not isinstance(backtest_text, str)
            or not Path(backtest_text).is_absolute()
            or Path(backtest_text).resolve() != expected_backtest_path
        ):
            raise RuntimeError(f"segment {index} backtest JSON fixed path mismatch")
        if (
            not isinstance(events_text, str)
            or not Path(events_text).is_absolute()
            or Path(events_text).resolve() != expected_events_path
        ):
            raise RuntimeError(f"segment {index} events CSV fixed path mismatch")
        backtest, backtest_evidence, backtest_path = _load_control_evidence(
            segment_artifacts.get("backtest_json"),
            f"segment {index} backtest JSON",
            max_bytes=MAX_CONTROL_JSON_BYTES,
        )
        if backtest_path != expected_backtest_path:
            raise RuntimeError(f"segment {index} backtest JSON fixed path mismatch")
        if (
            backtest.get("schema") != "FEILONG_TDX_BACKTEST_V1"
            or backtest.get("status") != "CLEAN_PASS"
        ):
            raise RuntimeError(f"segment {index} backtest JSON schema/status mismatch")
        backtest_binding = _validate_backtest_payload(
            backtest, f"segment {index} backtest JSON", core_end
        )
        if backtest_binding["signal_count"] != segment_signal_count:
            raise RuntimeError(f"segment {index} backtest/manifest signal count mismatch")
        events_evidence = _validate_events_csv(
            segment_artifacts.get("events_csv"),
            f"segment {index} events CSV",
            expected_path=expected_events_path,
            core_start=PHYSICAL_START,
            core_end=core_end,
            expected_signal_count=segment_signal_count,
            expected_signal_stock_count=int(backtest_binding["signal_stock_count"]),
            expected_signal_date_min=backtest_binding["signal_date_min"],
            expected_signal_date_max=backtest_binding["signal_date_max"],
        )
        if Path(str(events_evidence["path"])) != expected_events_path:
            raise RuntimeError(f"segment {index} events CSV fixed path mismatch")
        if int(backtest_binding["signal_stock_count"]) > int(
            backtest_binding["universe_count"]
        ):
            raise RuntimeError(
                f"segment {index} events CSV signal stock count exceeds universe"
            )
        if (
            segment.get("events_csv_size") != events_evidence["size"]
            or str(segment.get("events_csv_sha256", "")).casefold()
            != str(events_evidence["sha256"]).casefold()
        ):
            raise RuntimeError(f"segment {index} events CSV evidence mismatch")

        receipt_value = segment.get("receipt")
        receipt_path = _declared_evidence_path(
            receipt_value, f"segment {index} receipt"
        )
        _require_within(receipt_path, resolved_receipt_root, "receipt")
        if (
            receipt_path.parent != resolved_receipt_root
            or RECEIPT_FILENAME_RE.fullmatch(receipt_path.name) is None
        ):
            raise RuntimeError(f"segment {index} receipt filename mismatch")
        receipt, receipt_evidence, loaded_receipt_path = _load_control_evidence(
            receipt_value,
            f"segment {index} receipt",
            max_bytes=MAX_CONTROL_JSON_BYTES,
        )
        if loaded_receipt_path != receipt_path:
            raise RuntimeError(f"segment {index} receipt path mismatch")
        _validate_receipt_shape(receipt, f"segment {index} receipt")
        if receipt.get("receipt_integrity") != _canonical_payload_hash(
            receipt, "receipt_integrity"
        ):
            raise RuntimeError(f"segment {index} receipt integrity mismatch")
        if (
            receipt.get("runtime") != "stock-canonical-runtime-v3"
            or receipt.get("runtime_surface") != "Codex"
            or receipt.get("skill_id") != SKILL_ID
            or receipt.get("entry") != str(SKILL_ENTRY)
            or receipt.get("status") != "CLEAN_PASS"
            or str(receipt.get("contract_sha256", "")).casefold()
            != contract_sha256
            or receipt.get("binding_errors") != []
        ):
            raise RuntimeError(
                f"segment {index} receipt identity/status/contract mismatch"
            )
        expected_extra_args = [
            "--timeout",
            "900",
            "--backtest",
            "--start-date",
            PHYSICAL_START,
            "--end-date",
            core_end,
            "--out-dir",
            str(output_dir),
            "--selection-formula",
            EXPECTED_FORMULA["selection_formula"],
            "--chunk-size",
            "240",
        ]
        if receipt.get("extra_args") != expected_extra_args:
            raise RuntimeError(f"segment {index} receipt extra_args mismatch")
        run_dir_text = receipt.get("run_dir")
        if not isinstance(run_dir_text, str) or not Path(run_dir_text).is_absolute():
            raise RuntimeError(f"segment {index} receipt run dir must be absolute")
        run_dir = Path(run_dir_text).resolve()
        _require_within(run_dir, resolved_receipt_root / "runs", "receipt run dir")
        if (
            run_dir.parent != (resolved_receipt_root / "runs").resolve()
            or RUN_DIR_NAME_RE.fullmatch(run_dir.name) is None
        ):
            raise RuntimeError(f"segment {index} receipt run dir mismatch")

        authorization_value = segment.get("authorization")
        authorization_path = _declared_evidence_path(
            authorization_value,
            f"segment {index} authorization",
            expected_keys=AUTHORIZATION_EVIDENCE_KEYS,
        )
        _require_within(
            authorization_path, resolved_receipt_root, "artifact authorization"
        )
        expected_authorization_name = (
            f"{receipt_path.stem}."
            f"{str(segment_manifest_evidence['sha256'])[:16]}"
            ".delivery-authorization.json"
        )
        if (
            authorization_path.parent != resolved_receipt_root
            or authorization_path.name != expected_authorization_name
        ):
            raise RuntimeError(f"segment {index} authorization filename mismatch")
        authorization, authorization_evidence, loaded_authorization_path = (
            _load_control_evidence(
                authorization_value,
                f"segment {index} authorization",
                max_bytes=MAX_AUTHORIZATION_BYTES,
                expected_keys=AUTHORIZATION_EVIDENCE_KEYS,
            )
        )
        if loaded_authorization_path != authorization_path:
            raise RuntimeError(f"segment {index} authorization path mismatch")
        _require_exact_keys(
            authorization,
            AUTHORIZATION_KEYS,
            f"segment {index} authorization",
        )
        auth_receipt = authorization.get("receipt")
        auth_artifact = authorization.get("artifact")
        if not isinstance(auth_receipt, dict):
            raise RuntimeError(f"segment {index} authorization receipt binding mismatch")
        _require_exact_keys(
            auth_receipt,
            AUTHORIZATION_RECEIPT_KEYS,
            f"segment {index} authorization receipt",
        )
        if (
            authorization.get("schema") != "STOCK_DELIVERY_AUTHORIZATION_V1"
            or authorization.get("runtime") != "stock-canonical-runtime-v3"
            or authorization.get("runtime_surface") != "Codex"
            or authorization.get("skill_id") != SKILL_ID
            or authorization.get("status") != "CLEAN_PASS"
            or authorization.get("delivery_kind") != "stock_artifact"
            or authorization.get("binding_source") != "receipt_bound_manifest"
            or authorization.get("errors") != []
            or authorization.get("authorization") is not None
        ):
            raise RuntimeError(
                f"segment {index} authorization identity/status mismatch"
            )
        authorization_path_text = authorization.get("authorization_path")
        if (
            not isinstance(authorization_path_text, str)
            or not Path(authorization_path_text).is_absolute()
            or Path(authorization_path_text).resolve() != authorization_path
        ):
            raise RuntimeError(f"segment {index} authorization self path mismatch")
        if (
            not isinstance(auth_receipt.get("path"), str)
            or not Path(str(auth_receipt["path"])).is_absolute()
            or Path(str(auth_receipt["path"])).resolve() != receipt_path
            or str(auth_receipt.get("sha256", "")).casefold()
            != str(receipt_evidence["sha256"]).casefold()
            or str(auth_receipt.get("contract_sha256", "")).casefold()
            != contract_sha256
        ):
            raise RuntimeError(f"segment {index} authorization receipt binding mismatch")
        if not _evidence_matches(
            auth_artifact, segment_manifest_evidence, segment_manifest_path
        ):
            raise RuntimeError(f"segment {index} authorization artifact binding mismatch")

        business_result_text = authorization.get("manifest_source")
        if (
            not isinstance(business_result_text, str)
            or not business_result_text
            or not Path(business_result_text).is_absolute()
        ):
            raise RuntimeError(
                f"segment {index} business result manifest source must be absolute"
            )
        business_result_path = Path(business_result_text).resolve()
        _require_business_runs_path(business_result_path, resolved_receipt_root)
        if business_result_path != run_dir / "business_result.json":
            raise RuntimeError(f"segment {index} business result filename mismatch")
        business_content, business_result_evidence = _stable_file_evidence(
            business_result_path, max_bytes=MAX_CONTROL_JSON_BYTES
        )
        business_result = _load_json_bytes(
            business_content, f"segment {index} business result"
        )
        _require_exact_keys(
            business_result,
            BUSINESS_RESULT_KEYS,
            f"segment {index} business result",
        )
        if (
            business_result.get("schema") != "STOCK_CANONICAL_BUSINESS_RESULT_V1"
            or business_result.get("status") != "CLEAN_PASS"
            or business_result.get("skill_id") != SKILL_ID
        ):
            raise RuntimeError(f"segment {index} business result identity mismatch")
        _require_exact_dict(
            business_result.get("business_process"),
            BUSINESS_PROCESS_KEYS,
            f"segment {index} business result process",
        )
        business_binding = _require_exact_dict(
            business_result.get("business_binding"),
            NORMAL_BUSINESS_BINDING_KEYS,
            f"segment {index} business result binding",
        )
        if business_binding.get("path") != str(LEGACY_ENTRY):
            raise RuntimeError(f"segment {index} business result binding path mismatch")
        business_artifacts = business_result.get("artifacts")
        if not isinstance(business_artifacts, dict):
            raise RuntimeError(f"segment {index} business result artifacts missing")
        _require_exact_keys(
            business_artifacts,
            NORMAL_BUSINESS_ARTIFACT_KEYS,
            f"segment {index} business result artifacts",
        )
        if not _evidence_matches(
            business_artifacts.get("segment_manifest"),
            segment_manifest_evidence,
            segment_manifest_path,
        ):
            raise RuntimeError(
                f"segment {index} business result does not bind segment manifest"
            )
        if not _evidence_matches(
            business_artifacts.get("backtest_json"),
            backtest_evidence,
            backtest_path,
        ) or not _evidence_matches(
            business_artifacts.get("events_csv"),
            events_evidence,
            expected_events_path,
        ):
            raise RuntimeError(f"segment {index} business result artifact binding mismatch")
        stdout_path = run_dir / "business_child.stdout.txt"
        stderr_path = run_dir / "business_child.stderr.txt"
        if (
            business_artifacts.get("stdout") != str(stdout_path)
            or business_artifacts.get("stderr") != str(stderr_path)
        ):
            raise RuntimeError(f"segment {index} business result log path mismatch")
        _stdout_content, stdout_evidence = _stable_file_evidence(
            stdout_path, max_bytes=MAX_CONTROL_JSON_BYTES
        )
        _stderr_content, stderr_evidence = _stable_file_evidence(
            stderr_path, max_bytes=MAX_CONTROL_JSON_BYTES
        )
        required_artifacts = receipt.get("required_artifacts")
        required_bindings = (
            (stdout_evidence, stdout_path),
            (stderr_evidence, stderr_path),
            (business_result_evidence, business_result_path),
        )
        if not isinstance(required_artifacts, list) or any(
            not any(
                _evidence_matches(candidate, evidence, expected_path)
                for candidate in required_artifacts
            )
            for evidence, expected_path in required_bindings
        ):
            raise RuntimeError(
                f"segment {index} receipt required artifacts do not bind business result"
            )
        manifest_source_value = authorization_value.get("manifest_source")
        if (
            manifest_source_value != business_result_text
            or authorization_value.get("status") != authorization.get("status")
            or authorization_value.get("delivery_kind")
            != authorization.get("delivery_kind")
            or authorization_value.get("binding_source")
            != authorization.get("binding_source")
        ):
            raise RuntimeError(
                f"segment {index} authorization metadata binding mismatch"
            )

    inventory = manifest.get("inventory")
    if not isinstance(inventory, dict):
        raise RuntimeError("delivery manifest inventory missing")
    _require_exact_keys(inventory, INVENTORY_KEYS, "delivery manifest inventory")
    inventory_identity = (
        inventory.get("status"),
        inventory.get("file_count"),
        inventory.get("valid_file_count"),
        inventory.get("anomaly_file_count"),
        str(inventory.get("physical_start_date", "")),
        str(inventory.get("physical_end_date", "")),
    )
    if inventory_identity != (
        "STRUCTURE_ALIGNED",
        12217,
        12215,
        2,
        PHYSICAL_START,
        PHYSICAL_END,
    ):
        raise RuntimeError("delivery manifest inventory identity mismatch")
    anomalies = inventory.get("anomalies")
    if not isinstance(anomalies, list) or len(anomalies) != 2:
        raise RuntimeError("delivery manifest inventory anomalies mismatch")
    for index, row in enumerate(anomalies, start=1):
        if not isinstance(row, dict):
            raise RuntimeError("delivery manifest inventory anomalies mismatch")
        _require_exact_keys(row, ANOMALY_KEYS, f"inventory anomaly {index}")
    actual_anomalies = {
        (str(row.get("relative_path", "")).casefold(), str(row.get("status", "")))
        for row in anomalies
        if isinstance(row, dict)
    }
    if actual_anomalies != EXPECTED_ZERO_BYTE_ANOMALIES:
        raise RuntimeError("delivery manifest inventory anomalies mismatch")
    nonstandard = inventory.get("nonstandard_filenames")
    if isinstance(nonstandard, list):
        for index, row in enumerate(nonstandard, start=1):
            if not isinstance(row, dict):
                raise RuntimeError(
                    "delivery manifest inventory nonstandard filename mismatch"
                )
            _require_exact_keys(
                row,
                NONSTANDARD_FILENAME_KEYS,
                f"inventory nonstandard filename {index}",
            )
    if (
        inventory.get("nonstandard_filename_count") != 1
        or not isinstance(nonstandard, list)
        or nonstandard != [EXPECTED_NONSTANDARD_FILENAME]
    ):
        raise RuntimeError("delivery manifest inventory nonstandard filename mismatch")

    invariants = manifest.get("invariants")
    if not isinstance(invariants, dict) or invariants.get("status") != "CLEAN_PASS":
        raise RuntimeError("delivery manifest invariants status mismatch")
    _require_exact_keys(invariants, INVARIANT_KEYS, "delivery manifest invariants")
    horizon_samples = invariants.get("horizon_sample_counts")
    if not isinstance(horizon_samples, dict):
        raise RuntimeError("delivery manifest invariant horizon samples missing")
    _require_exact_keys(
        horizon_samples, HORIZON_SAMPLE_KEYS, "invariant horizon samples"
    )
    for key in INVARIANT_KEYS - {"horizon_sample_counts", "status"}:
        value = invariants.get(key)
        if type(value) is not int or value != 0:
            raise RuntimeError(f"delivery manifest invariant {key} must be integer zero")
    ordered_horizon_counts: list[int] = []
    for horizon in HORIZONS:
        value = horizon_samples.get(f"{horizon}d")
        ordered_horizon_counts.append(
            _require_nonnegative_int(value, f"invariant horizon {horizon}d")
        )
    if any(
        previous < current
        for previous, current in zip(
            ordered_horizon_counts, ordered_horizon_counts[1:]
        )
    ):
        raise RuntimeError("delivery manifest invariant horizon counts not monotonic")

    declared_artifacts = manifest.get("artifacts")
    if (
        not isinstance(declared_artifacts, dict)
        or set(declared_artifacts) != DELIVERY_ARTIFACT_KEYS
    ):
        raise RuntimeError("delivery manifest artifact keys mismatch")
    bound: dict[str, dict[str, object]] = {
        "delivery_manifest": manifest_evidence
    }
    for key in sorted(DELIVERY_ARTIFACT_KEYS):
        expected_artifact_path = path.parent / FINAL_ARTIFACT_FILENAMES[key]
        declared_artifact_path = _declared_evidence_path(
            declared_artifacts[key], key
        )
        if declared_artifact_path != expected_artifact_path:
            raise RuntimeError(f"{key} fixed delivery path mismatch")
        _artifact_content, artifact_evidence = _validate_declared_evidence(
            declared_artifacts[key], key, stream=True
        )
        bound[key] = artifact_evidence
    return bound


def normalize_business_args(business_args: list[str] | None) -> list[str]:
    args = list(business_args or [])
    return args[1:] if args and args[0] == "--" else args


def validate_report_manifest(
    manifest_path: Path,
) -> dict[str, dict[str, object]]:
    raw_path = Path(manifest_path)
    if not raw_path.is_absolute():
        raise RuntimeError("report manifest path must be absolute")
    path = raw_path.resolve()
    content, manifest_evidence = _stable_file_evidence(
        path, max_bytes=MAX_MANIFEST_BYTES
    )
    manifest = _load_json_bytes(content, "report manifest")
    required_keys = {
        "schema",
        "status",
        "skill_id",
        "effective_trading_date",
        "template",
        "rules_engine",
        "analysis_receipt",
        "artifact",
        "pdf",
        "validation",
        "errors",
    }
    _require_exact_keys(manifest, required_keys, "report manifest")
    if (
        manifest.get("schema") != "FEILONG_ANALYSIS_WORD_MANIFEST_V1"
        or manifest.get("status") != "CLEAN_PASS"
        or manifest.get("skill_id") != SKILL_ID
        or manifest.get("errors") != []
    ):
        raise RuntimeError("report manifest identity/status mismatch")
    validation = manifest.get("validation")
    if (
        not isinstance(validation, dict)
        or validation.get("status") != "CLEAN_PASS"
        or validation.get("errors") != []
        or validation.get("word_opened") is not True
        or validation.get("pdf_exported") is not True
        or validation.get("visual_qa_clean") is not True
        or int(validation.get("word_pages", 0)) < 1
        or int(validation.get("required_term_missing_count", -1)) != 0
        or int(validation.get("forbidden_term_hit_count", -1)) != 0
    ):
        raise RuntimeError("report manifest validation not clean")
    bound: dict[str, dict[str, object]] = {"report_manifest": manifest_evidence}
    for key, expected_path in (
        ("template", REPORT_TEMPLATE),
        ("rules_engine", REPORT_VALIDATOR),
    ):
        declared_path = _declared_evidence_path(manifest.get(key), key)
        if declared_path != expected_path.resolve():
            raise RuntimeError(f"report {key} path mismatch")
        _content, bound[key] = _validate_declared_evidence(
            manifest.get(key), key, max_bytes=MAX_CONTROL_JSON_BYTES
        )
    for key in ("analysis_receipt", "artifact", "pdf"):
        declared_path = _declared_evidence_path(manifest.get(key), key)
        if key == "artifact" and declared_path.suffix.casefold() != ".docx":
            raise RuntimeError("report artifact extension mismatch")
        if key == "pdf" and declared_path.suffix.casefold() != ".pdf":
            raise RuntimeError("report pdf extension mismatch")
        _content, bound[key] = _validate_declared_evidence(
            manifest.get(key), key, stream=True
        )
    receipt_content, _receipt_evidence = _stable_file_evidence(
        Path(str(bound["analysis_receipt"]["path"])),
        max_bytes=MAX_CONTROL_JSON_BYTES,
    )
    receipt = _load_json_bytes(receipt_content, "analysis receipt")
    readiness = receipt.get("production_readiness")
    gate = readiness.get("data_gate") if isinstance(readiness, dict) else None
    if (
        receipt.get("skill_id") != SKILL_ID
        or receipt.get("status") != "CLEAN_PASS"
        or not isinstance(readiness, dict)
        or readiness.get("status") != "CLEAN_PASS"
        or readiness.get("conclusion_eligible") is not True
        or not isinstance(gate, dict)
        or gate.get("status") != "CLEAN_PASS"
        or gate.get("errors") != []
        or gate.get("effective_trading_date")
        != manifest.get("effective_trading_date")
        or gate.get("latest_required_trading_date")
        != manifest.get("effective_trading_date")
    ):
        raise RuntimeError("analysis receipt is not clean/current")
    return bound


def business_command(run_dir: Path, business_args: list[str] | None = None) -> list[str]:
    overrides: dict[str, list[str]] = {
        "golden-ignition": ["run", "000001"],
        "shortline-hotspot-mining": ["run", "--date", datetime.now().strftime("%Y-%m-%d")],
        "a-share-intraday-position-monitor": [
            "run", "--positions-json",
            '[{"code":"000001","name":"Ping An Bank","cost":10.0,"shares":100}]',
        ],
        "industry-chain-analysis": ["run", "--topic", "artificial intelligence"],
        "old-leader-oversold-rebound": ["run", "--date", datetime.now().strftime("%Y-%m-%d")],
    }
    return [
        sys.executable,
        str(LEGACY_ENTRY),
        *overrides.get(SKILL_ID, ["run"]),
        *normalize_business_args(business_args),
    ]


def extract_backtest_artifacts(stdout: str) -> dict[str, dict[str, object]]:
    decoder = json.JSONDecoder()
    result: dict | None = None
    for offset, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            candidate, _end = decoder.raw_decode(stdout[offset:])
        except json.JSONDecodeError:
            continue
        if (
            isinstance(candidate, dict)
            and candidate.get("schema") == "FEILONG_TDX_BACKTEST_V1"
            and candidate.get("status") == "CLEAN_PASS"
        ):
            result = candidate
    if result is None:
        raise RuntimeError("clean backtest result JSON missing from business stdout")

    manifest_path = Path(str(result.get("segment_manifest", ""))).resolve()
    if not manifest_path.is_file():
        raise RuntimeError(f"backtest segment manifest missing: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("backtest segment manifest unreadable") from exc
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema") != "FEILONG_BACKTEST_SEGMENT_MANIFEST_V1"
        or manifest.get("status") != "CLEAN_PASS"
    ):
        raise RuntimeError("backtest segment manifest status/schema invalid")
    validation = manifest.get("validation")
    if (
        not isinstance(validation, dict)
        or validation.get("status") != "CLEAN_PASS"
        or validation.get("errors") != []
        or validation.get("formula_source_bound") is not True
        or validation.get("artifact_hashes_verified") is not True
    ):
        raise RuntimeError("backtest segment manifest validation is not clean")

    declared = manifest.get("artifacts")
    if not isinstance(declared, dict):
        raise RuntimeError("backtest segment manifest artifacts missing")
    bound: dict[str, dict[str, object]] = {}
    artifact_keys = ["backtest_json", "events_csv"]
    if "first_board_matches_csv" in declared or result.get("first_board_matches_csv"):
        artifact_keys.append("first_board_matches_csv")
    for key in artifact_keys:
        row = declared.get(key)
        if not isinstance(row, dict):
            raise RuntimeError(f"backtest segment artifact missing: {key}")
        path = Path(str(row.get("path", ""))).resolve()
        if path != Path(str(result.get(key, ""))).resolve():
            raise RuntimeError(f"backtest result/manifest path mismatch: {key}")
        if not path.is_file():
            raise RuntimeError(f"backtest artifact missing: {path}")
        size = path.stat().st_size
        digest = sha256_file(path)
        if row.get("size") != size:
            raise RuntimeError(f"backtest artifact size mismatch: {key}")
        if str(row.get("sha256", "")).casefold() != digest:
            raise RuntimeError(f"backtest artifact hash mismatch: {key}")
        bound[key] = {"path": str(path), "size": size, "sha256": digest}
    bound["segment_manifest"] = {
        "path": str(manifest_path),
        "size": manifest_path.stat().st_size,
        "sha256": sha256_file(manifest_path),
    }
    return bound


def extract_factor_research_artifacts(stdout: str) -> dict[str, dict[str, object]]:
    decoder = json.JSONDecoder()
    result: dict | None = None
    for offset, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            candidate, _end = decoder.raw_decode(stdout[offset:])
        except json.JSONDecodeError:
            continue
        if (
            isinstance(candidate, dict)
            and candidate.get("schema") in {
                "FEILONG_FACTOR_RESEARCH_V1",
                "FEILONG_CONTINUATION_RESEARCH_V2",
            }
            and candidate.get("status") == "CLEAN_PASS"
        ):
            result = candidate
    if result is None:
        raise RuntimeError("clean factor research result JSON missing from business stdout")
    formula = result.get("formula")
    if (
        not isinstance(formula, dict)
        or formula.get("name") != "飞龙在天"
        or formula.get("legacy_4_0_used") is not False
    ):
        raise RuntimeError("factor research formula identity invalid")
    manifest_path = Path(str(result.get("segment_manifest", ""))).resolve()
    if not manifest_path.is_file():
        raise RuntimeError(f"factor research manifest missing: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("factor research manifest unreadable") from exc
    validation = manifest.get("validation") if isinstance(manifest, dict) else None
    continuation_v2 = result.get("schema") == "FEILONG_CONTINUATION_RESEARCH_V2"
    if (
        manifest.get("schema") != "FEILONG_FACTOR_RESEARCH_MANIFEST_V1"
        or manifest.get("status") != "CLEAN_PASS"
        or manifest.get("formula_name") != "飞龙在天"
        or manifest.get("legacy_4_0_used") is not False
        or not isinstance(validation, dict)
        or validation.get("status") != "CLEAN_PASS"
        or validation.get("errors") != []
        or validation.get("formula_source_bound") is not True
        or validation.get("input_hashes_verified") is not True
        or validation.get("artifact_hashes_verified") is not True
        or validation.get("missing_values_not_imputed") is not True
        or validation.get("post_event_features_excluded") is not True
        or (
            continuation_v2
            and validation.get("all_market_first_board_denominator_used") is not True
        )
        or (
            continuation_v2
            and validation.get("migrated_158_identity_verified") is not True
        )
    ):
        raise RuntimeError("factor research manifest validation is not clean")
    declared = manifest.get("artifacts")
    if not isinstance(declared, dict):
        raise RuntimeError("factor research manifest artifacts missing")
    artifact_keys = ["research_json", "events_csv", "statistics_csv", "report_markdown"]
    bound: dict[str, dict[str, object]] = {}
    for key in artifact_keys:
        row = declared.get(key)
        if not isinstance(row, dict):
            raise RuntimeError(f"factor research artifact missing: {key}")
        path = Path(str(row.get("path", ""))).resolve()
        if path != Path(str(result.get(key, ""))).resolve():
            raise RuntimeError(f"factor research result/manifest path mismatch: {key}")
        if not path.is_file():
            raise RuntimeError(f"factor research artifact missing: {path}")
        size = path.stat().st_size
        digest = sha256_file(path)
        if row.get("size") != size or str(row.get("sha256", "")).casefold() != digest:
            raise RuntimeError(f"factor research artifact hash mismatch: {key}")
        bound[key] = {"path": str(path), "size": size, "sha256": digest}
    bound["factor_manifest"] = {
        "path": str(manifest_path),
        "size": manifest_path.stat().st_size,
        "sha256": sha256_file(manifest_path),
    }
    return bound


def extract_resonance_exhaustive_artifacts(stdout: str) -> dict[str, dict[str, object]]:
    decoder = json.JSONDecoder()
    result: dict | None = None
    for offset, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            candidate, _end = decoder.raw_decode(stdout[offset:])
        except json.JSONDecodeError:
            continue
        if (
            isinstance(candidate, dict)
            and candidate.get("schema") == "FEILONG_RESONANCE_EXHAUSTIVE_V1"
            and candidate.get("status") == "CLEAN_PASS"
        ):
            result = candidate
    if result is None:
        raise RuntimeError("clean resonance exhaustive result JSON missing from business stdout")
    formula = result.get("formula")
    if (
        not isinstance(formula, dict)
        or formula.get("name") != "飞龙在天"
        or formula.get("legacy_4_0_used") is not False
    ):
        raise RuntimeError("resonance exhaustive formula identity invalid")
    manifest_path = Path(str(result.get("segment_manifest", ""))).resolve()
    if not manifest_path.is_file():
        raise RuntimeError(f"resonance exhaustive manifest missing: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("resonance exhaustive manifest unreadable") from exc
    validation = manifest.get("validation") if isinstance(manifest, dict) else None
    required_validation = (
        "source_factor_manifest_verified",
        "source_events_hash_verified",
        "formula_source_bound",
        "all_source_columns_classified",
        "all_valid_training_thresholds_enumerated",
        "pair_and_triple_combinations_enumerated",
        "out_of_time_validation_used",
        "missing_values_not_imputed",
        "post_event_features_excluded",
        "artifact_hashes_verified",
    )
    if (
        manifest.get("schema") != "FEILONG_RESONANCE_EXHAUSTIVE_MANIFEST_V1"
        or manifest.get("status") != "CLEAN_PASS"
        or manifest.get("formula_name") != "飞龙在天"
        or manifest.get("legacy_4_0_used") is not False
        or not isinstance(validation, dict)
        or validation.get("status") != "CLEAN_PASS"
        or validation.get("errors") != []
        or any(validation.get(key) is not True for key in required_validation)
    ):
        raise RuntimeError("resonance exhaustive manifest validation is not clean")
    declared = manifest.get("artifacts")
    if not isinstance(declared, dict):
        raise RuntimeError("resonance exhaustive manifest artifacts missing")
    artifact_keys = [
        "research_json",
        "threshold_audit_csv",
        "factor_results_csv",
        "combination_results_csv",
        "report_markdown",
    ]
    bound: dict[str, dict[str, object]] = {}
    for key in artifact_keys:
        row = declared.get(key)
        if not isinstance(row, dict):
            raise RuntimeError(f"resonance exhaustive artifact missing: {key}")
        path = Path(str(row.get("path", ""))).resolve()
        if path != Path(str(result.get(key, ""))).resolve():
            raise RuntimeError(f"resonance exhaustive result/manifest path mismatch: {key}")
        if not path.is_file():
            raise RuntimeError(f"resonance exhaustive artifact missing: {path}")
        size = path.stat().st_size
        digest = sha256_file(path)
        if row.get("size") != size or str(row.get("sha256", "")).casefold() != digest:
            raise RuntimeError(f"resonance exhaustive artifact hash mismatch: {key}")
        bound[key] = {"path": str(path), "size": size, "sha256": digest}
    bound["resonance_exhaustive_manifest"] = {
        "path": str(manifest_path),
        "size": manifest_path.stat().st_size,
        "sha256": sha256_file(manifest_path),
    }
    return bound


def extract_deep_factor_artifacts(stdout: str) -> dict[str, dict[str, object]]:
    decoder = json.JSONDecoder()
    result: dict | None = None
    for offset, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            candidate, _end = decoder.raw_decode(stdout[offset:])
        except json.JSONDecodeError:
            continue
        if (
            isinstance(candidate, dict)
            and candidate.get("schema") == "FEILONG_DEEP_FACTOR_RESEARCH_V1"
            and candidate.get("status") == "CLEAN_PASS"
        ):
            result = candidate
    if result is None:
        raise RuntimeError("clean deep factor research result JSON missing from business stdout")
    formula = result.get("formula")
    if (
        not isinstance(formula, dict)
        or formula.get("name") != "飞龙在天"
        or formula.get("source_raw_sha256") != "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0"
        or formula.get("legacy_4_0_used") is not False
    ):
        raise RuntimeError("deep factor research formula identity invalid")
    manifest_path = Path(str(result.get("segment_manifest", ""))).resolve()
    if not manifest_path.is_file():
        raise RuntimeError(f"deep factor research manifest missing: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("deep factor research manifest unreadable") from exc
    validation = manifest.get("validation") if isinstance(manifest, dict) else None
    required_validation = (
        "source_manifest_verified",
        "source_events_hash_verified",
        "current_formula_bound",
        "tdx_direct_crosscheck_passed",
        "positive_only_158_audited",
        "board_regime_separated",
        "rolling_out_of_time_validation_used",
        "date_cluster_bootstrap_used",
        "symbol_cluster_bootstrap_used",
        "factor_redundancy_clustered",
        "nested_score_used",
        "advanced_interaction_research_used",
        "factor_correlation_research_used",
        "at_least_100_ranked_factors",
        "all_factor_definitions_present",
        "factor_correlation_cluster_bootstrap_used",
        "tdx_binary_date_and_unit_sanity_passed",
        "minute_coverage_limited_and_disclosed",
        "missing_values_not_imputed",
        "post_event_features_excluded",
        "artifact_hashes_verified",
    )
    if (
        manifest.get("schema") != "FEILONG_DEEP_FACTOR_RESEARCH_MANIFEST_V1"
        or manifest.get("status") != "CLEAN_PASS"
        or manifest.get("formula_name") != "飞龙在天"
        or manifest.get("formula_sha256") != "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0"
        or not isinstance(validation, dict)
        or validation.get("status") != "CLEAN_PASS"
        or validation.get("errors") != []
        or validation.get("legacy_4_0_used") is not False
        or any(validation.get(key) is not True for key in required_validation)
    ):
        raise RuntimeError("deep factor research manifest validation is not clean")
    declared = manifest.get("artifacts")
    result_artifacts = result.get("artifacts")
    if not isinstance(declared, dict) or not isinstance(result_artifacts, dict):
        raise RuntimeError("deep factor research artifacts missing")
    artifact_keys = [
        "research_json",
        "report_markdown",
        "aggregate_factors_csv",
        "fold_detail_csv",
        "strata_csv",
        "redundancy_csv",
        "score_bands_csv",
        "score_selections_csv",
        "feature_audit_csv",
        "robust_intersection_csv",
        "advanced_report_markdown",
        "advanced_research_json",
        "advanced_daily_interactions_csv",
        "advanced_minute_interactions_csv",
        "advanced_feature_audit_csv",
        "advanced_manifest",
        "correlation_ranking_csv",
        "correlation_definitions_csv",
        "correlation_stable_factors_csv",
        "correlation_event_values_csv",
        "correlation_research_json",
        "correlation_report_markdown",
        "correlation_manifest",
    ]
    bound: dict[str, dict[str, object]] = {}
    for key in artifact_keys:
        row = declared.get(key)
        if not isinstance(row, dict):
            raise RuntimeError(f"deep factor research artifact missing: {key}")
        path = Path(str(row.get("path", ""))).resolve()
        if path != Path(str(result_artifacts.get(key, ""))).resolve():
            raise RuntimeError(f"deep factor research result/manifest path mismatch: {key}")
        if not path.is_file():
            raise RuntimeError(f"deep factor research artifact missing: {path}")
        size = path.stat().st_size
        digest = sha256_file(path)
        if row.get("size") != size or str(row.get("sha256", "")).casefold() != digest:
            raise RuntimeError(f"deep factor research artifact hash mismatch: {key}")
        business_key = {
            "aggregate_factors_csv": "deep_factor_summary_csv",
            "feature_audit_csv": "deep_feature_quality_csv",
            "advanced_feature_audit_csv": "deep_advanced_feature_quality_csv",
        }.get(key, f"deep_{key}")
        bound[business_key] = {"path": str(path), "size": size, "sha256": digest}
    bound["deep_factor_manifest"] = {
        "path": str(manifest_path),
        "size": manifest_path.stat().st_size,
        "sha256": sha256_file(manifest_path),
    }
    return bound


def extract_yaogu_scoring_artifacts(stdout: str) -> dict[str, dict[str, object]]:
    decoder = json.JSONDecoder()
    result: dict | None = None
    for offset, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(stdout[offset:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and candidate.get("schema") == "FEILONG_YAOGU_32D_SCORE_RUN_V1":
            result = candidate
    if result is None:
        raise RuntimeError("32-dimension scoring result missing from stdout")
    checks = result.get("checks")
    if (
        result.get("status") != "CLEAN_PASS"
        or result.get("formula_name") != "飞龙在天"
        or result.get("formula_sha256") != "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0"
        or result.get("legacy_4_0_used") is not False
        or not isinstance(checks, dict)
        or checks.get("source_factor_rows") != 640
        or checks.get("source_rankable_factors") != 634
        or checks.get("dimensions") != 32
        or checks.get("imputed_training_cells") != 0
        or checks.get("score_nulls") != 0
        or checks.get("duplicate_oos_events") != 0
        or checks.get("future_leakage") is not False
        or checks.get("development_grade_monotonic") is not True
        or checks.get("sealed_holdout_top_grade_positive_lift") is not True
        or checks.get("production_ready") is not True
    ):
        raise RuntimeError("32-dimension scoring validation is not clean")
    declared = result.get("artifacts")
    if not isinstance(declared, dict):
        raise RuntimeError("32-dimension scoring artifacts missing")
    required_names = {
        "飞龙共振首板_32维评分规则.csv",
        "飞龙共振首板_32维评分模型配置.json",
        "飞龙共振首板_32维妖股评分体系报告.md",
        "飞龙共振首板_640因子权重与方向.csv",
        "飞龙共振首板_滚动样本外逐股评分.csv",
        "飞龙共振首板_滚动折次表现.csv",
        "飞龙共振首板_样本外等级回测.csv",
        "飞龙共振首板_样本外评分十分位回测.csv",
        "飞龙共振首板_样本外阈值回测.csv",
        "飞龙共振首板_样本逐股32维评分.csv",
        "飞龙共振首板_等级单调校准.csv",
        "飞龙共振首板_最终留出集验收.csv",
        "飞龙共振首板_冗余控制审计.csv",
        "飞龙共振首板_历史缺失排除审计.csv",
        "飞龙共振首板_生产准入决策.json",
        "构建验收清单.json",
        "apply_yaogu_scoring.py",
        "build_yaogu_scoring.py",
    }
    if not required_names.issubset(declared):
        raise RuntimeError("32-dimension scoring required artifact set incomplete")
    bound: dict[str, dict[str, object]] = {}
    for index, name in enumerate(sorted(required_names), start=1):
        row = declared.get(name)
        if not isinstance(row, dict):
            raise RuntimeError(f"32-dimension scoring artifact declaration invalid: {name}")
        path = Path(str(row.get("path", ""))).resolve()
        if not path.is_file() or path.name != name:
            raise RuntimeError(f"32-dimension scoring artifact missing: {path}")
        size = path.stat().st_size
        digest = sha256_file(path)
        if row.get("size") != size or str(row.get("sha256", "")).casefold() != digest:
            raise RuntimeError(f"32-dimension scoring artifact hash mismatch: {name}")
        bound[f"yaogu_score_artifact_{index:02d}"] = {
            "path": str(path),
            "size": size,
            "sha256": digest,
        }
    return bound


def extract_factor_correlation_v3_artifacts(stdout: str) -> dict[str, dict[str, object]]:
    decoder = json.JSONDecoder()
    result: dict | None = None
    for offset, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(stdout[offset:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and candidate.get("schema") == "FEILONG_FACTOR_CORRELATION_RESEARCH_V3":
            result = candidate
    if result is None:
        raise RuntimeError("V3 factor correlation result missing from stdout")
    coverage = result.get("coverage")
    formula = result.get("formula")
    if (
        result.get("status") != "CLEAN_PASS"
        or not isinstance(formula, dict)
        or formula.get("name") != "飞龙在天"
        or formula.get("source_raw_sha256") != "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0"
        or formula.get("legacy_4_0_used") is not False
        or not isinstance(coverage, dict)
        or coverage.get("registered_factor_count") != 1280
        or int(coverage.get("ranked_factor_count", 0)) < 1200
        or int(coverage.get("independent_dimension_count", 0)) < 96
        or coverage.get("unique_dependency_fingerprint_count") != coverage.get("independent_dimension_count")
        or int(coverage.get("window_or_threshold_variants_not_counted_as_dimensions", 0)) <= 0
    ):
        raise RuntimeError("V3 factor correlation validation is not clean")
    manifest_path = Path(str(result.get("segment_manifest", ""))).resolve()
    if not manifest_path.is_file():
        raise RuntimeError("V3 factor correlation manifest missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validation = manifest.get("validation")
    required_validation = (
        "current_formula_bound",
        "tdx_root_verified",
        "exactly_1280_registered_factors",
        "at_least_96_independent_dimensions",
        "dimension_dependency_fingerprints_unique",
        "window_and_threshold_aliases_collapsed",
        "all_registered_factors_enumerated",
        "all_factor_definitions_present",
        "date_cluster_bootstrap_used",
        "symbol_cluster_bootstrap_used",
        "multiple_testing_corrected",
        "time_stability_reported",
        "missing_values_not_imputed",
        "post_event_features_excluded",
        "artifact_hashes_verified",
    )
    if (
        manifest.get("schema") != "FEILONG_FACTOR_CORRELATION_RESEARCH_MANIFEST_V3"
        or manifest.get("status") != "CLEAN_PASS"
        or manifest.get("formula_name") != "飞龙在天"
        or not isinstance(validation, dict)
        or validation.get("status") != "CLEAN_PASS"
        or validation.get("errors") != []
        or validation.get("legacy_4_0_used") is not False
        or any(validation.get(key) is not True for key in required_validation)
    ):
        raise RuntimeError("V3 factor correlation manifest is not clean")
    declared = manifest.get("artifacts")
    result_artifacts = result.get("artifacts")
    required = (
        "ranking_csv", "definitions_csv", "stable_factors_csv", "event_values_csv",
        "research_json", "report_markdown", "dimension_catalog_csv", "anti_alias_audit_csv",
    )
    if not isinstance(declared, dict) or not isinstance(result_artifacts, dict):
        raise RuntimeError("V3 factor correlation artifacts missing")
    bound: dict[str, dict[str, object]] = {}
    for key in required:
        row = declared.get(key)
        path = Path(str(result_artifacts.get(key, ""))).resolve()
        if not isinstance(row, dict) or Path(str(row.get("path", ""))).resolve() != path or not path.is_file():
            raise RuntimeError(f"V3 factor correlation artifact missing:{key}")
        size = path.stat().st_size
        digest = sha256_file(path)
        if row.get("size") != size or str(row.get("sha256", "")).casefold() != digest:
            raise RuntimeError(f"V3 factor correlation artifact hash mismatch:{key}")
        bound[f"factor_v3_{key}"] = {"path": str(path), "size": size, "sha256": digest}
    bound["factor_v3_manifest"] = {
        "path": str(manifest_path),
        "size": manifest_path.stat().st_size,
        "sha256": sha256_file(manifest_path),
    }
    return bound


def extract_yaogu_scoring_v3_artifacts(stdout: str) -> dict[str, dict[str, object]]:
    decoder = json.JSONDecoder()
    result: dict | None = None
    for offset, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(stdout[offset:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and candidate.get("schema") == "FEILONG_YAOGU_MULTIDIM_SCORE_RUN_V3":
            result = candidate
    if result is None:
        raise RuntimeError("V3 multidimension scoring result missing from stdout")
    checks = result.get("checks")
    if (
        result.get("status") != "CLEAN_PASS"
        or result.get("formula_name") != "飞龙在天"
        or result.get("formula_sha256") != "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0"
        or result.get("legacy_4_0_used") is not False
        or not isinstance(checks, dict)
        or checks.get("source_factor_rows") != 1280
        or checks.get("source_rankable_factors") != 1273
        or checks.get("registered_dimensions") != 325
        or checks.get("effective_dimensions") != 319
        or checks.get("source_events") != 3728
        or int(checks.get("complete_case_events", 0)) <= 3000
        or checks.get("imputed_training_cells") != 0
        or checks.get("score_nulls") != 0
        or checks.get("duplicate_oos_events") != 0
        or checks.get("future_leakage") is not False
        or checks.get("development_grade_monotonic") is not True
        or checks.get("sealed_holdout_top_grade_positive_lift") is not True
        or checks.get("production_ready") is not True
    ):
        raise RuntimeError("V3 multidimension scoring validation is not clean")
    declared = result.get("artifacts")
    if not isinstance(declared, dict):
        raise RuntimeError("V3 multidimension scoring artifacts missing")
    required_names = {
        "飞龙共振首板_325维度评分规则.csv",
        "飞龙共振首板_319维评分模型配置.json",
        "飞龙共振首板_多维妖股评分体系报告.md",
        "飞龙共振首板_1280因子权重与方向.csv",
        "飞龙共振首板_滚动样本外逐股评分.csv",
        "飞龙共振首板_滚动折次表现.csv",
        "飞龙共振首板_样本外等级回测.csv",
        "飞龙共振首板_样本外评分十分位回测.csv",
        "飞龙共振首板_样本外阈值回测.csv",
        "飞龙共振首板_样本逐股319维评分.csv",
        "飞龙共振首板_等级单调校准.csv",
        "飞龙共振首板_最终留出集验收.csv",
        "飞龙共振首板_冗余控制审计.csv",
        "飞龙共振首板_历史缺失排除审计.csv",
        "飞龙共振首板_生产准入决策.json",
        "构建验收清单.json",
        "apply_yaogu_scoring.py",
        "build_yaogu_scoring.py",
    }
    if not required_names.issubset(declared):
        raise RuntimeError("V3 multidimension scoring required artifact set incomplete")
    bound: dict[str, dict[str, object]] = {}
    for index, name in enumerate(sorted(required_names), start=1):
        row = declared.get(name)
        if not isinstance(row, dict):
            raise RuntimeError(f"V3 multidimension scoring artifact declaration invalid:{name}")
        path = Path(str(row.get("path", ""))).resolve()
        if not path.is_file() or path.name != name:
            raise RuntimeError(f"V3 multidimension scoring artifact missing:{path}")
        size = path.stat().st_size
        digest = sha256_file(path)
        if row.get("size") != size or str(row.get("sha256", "")).casefold() != digest:
            raise RuntimeError(f"V3 multidimension scoring artifact hash mismatch:{name}")
        bound[f"yaogu_v3_score_artifact_{index:02d}"] = {"path": str(path), "size": size, "sha256": digest}
    return bound


def extract_daily_yaogu_scoring_artifacts(stdout: str) -> dict[str, dict[str, object]]:
    decoder = json.JSONDecoder()
    result: dict | None = None
    for offset, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(stdout[offset:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and candidate.get("schema") == "FEILONG_DAILY_YAOGU_PRODUCTION_V2":
            result = candidate
    if result is None:
        raise RuntimeError("daily 32-dimension scoring result missing from stdout")
    checks = result.get("checks")
    if (
        result.get("status") != "CLEAN_PASS"
        or result.get("formula_name") != "飞龙在天"
        or result.get("formula_sha256") != "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0"
        or result.get("legacy_4_0_used") is not False
        or not isinstance(checks, dict)
        or checks.get("factor_count") != 640
        or checks.get("rankable_factor_count") != 634
        or checks.get("dimension_count") != 32
        or checks.get("missing_factor_columns") != 0
        or checks.get("production_missing_cells") != 0
        or checks.get("production_nonfinite_cells") != 0
        or checks.get("rejected_incomplete_count") != 0
        or checks.get("target_rejected_incomplete_count") != 0
        or checks.get("score_nulls") != 0
        or checks.get("stale") is not False
        or checks.get("target_date") != checks.get("tdx_latest_date")
        or checks.get("rule_assets_locked") is not True
        or checks.get("tdx_input_snapshot_stable") is not True
        or checks.get("decision_rule_machine_only") is not True
        or checks.get("determinism_verified") is not True
        or not DAILY_PRODUCTION_LOCK.is_file()
        or sha256_file(DAILY_PRODUCTION_LOCK) != DAILY_PRODUCTION_LOCK_SHA256
    ):
        raise RuntimeError("daily 32-dimension scoring validation is not clean")
    declared = result.get("artifacts")
    required_names = {
        "飞龙在天_补档首板扫描.csv",
        "飞龙在天_补档共振候选640因子.csv",
        "飞龙在天_补档32维评分.csv",
        "飞龙在天_当日32维实战评分.csv",
        "飞龙在天_数据完整性拒绝.csv",
        "飞龙在天_生产评分决策.csv",
        "飞龙在天_零缺失审计.json",
        "飞龙在天_生产漂移锁.json",
        "飞龙在天_确定性复跑证据.json",
        "飞龙在天_实战评分报告.md",
        "飞龙在天_实战评分清单.json",
        "飞龙在天_全局旧版剔除审计.json",
    }
    if not isinstance(declared, dict) or not required_names.issubset(declared):
        raise RuntimeError("daily 32-dimension scoring required artifact set incomplete")
    bound: dict[str, dict[str, object]] = {}
    for index, name in enumerate(sorted(required_names), start=1):
        row = declared[name]
        if not isinstance(row, dict):
            raise RuntimeError(f"daily scoring artifact declaration invalid: {name}")
        path = Path(str(row.get("path", ""))).resolve()
        if not path.is_file() or path.name != name:
            raise RuntimeError(f"daily scoring artifact missing: {path}")
        size = path.stat().st_size
        digest = sha256_file(path)
        if row.get("size") != size or str(row.get("sha256", "")).casefold() != digest:
            raise RuntimeError(f"daily scoring artifact hash mismatch: {name}")
        bound[f"daily_yaogu_score_artifact_{index:02d}"] = {"path": str(path), "size": size, "sha256": digest}
    zero_missing = json.loads(Path(str(declared["飞龙在天_零缺失审计.json"]["path"])).read_text(encoding="utf-8"))
    determinism = json.loads(Path(str(declared["飞龙在天_确定性复跑证据.json"]["path"])).read_text(encoding="utf-8"))
    drift_lock = json.loads(Path(str(declared["飞龙在天_生产漂移锁.json"]["path"])).read_text(encoding="utf-8"))
    if (
        zero_missing.get("status") != "CLEAN_PASS"
        or zero_missing.get("candidate_factor_count") != 640
        or zero_missing.get("rankable_factor_count") != 634
        or zero_missing.get("source_invalid_cells") != 0
        or zero_missing.get("source_nan_cells") != 0
        or zero_missing.get("production_missing_cells") != 0
        or zero_missing.get("production_nonfinite_cells") != 0
        or zero_missing.get("rejected_incomplete_rows") != 0
        or zero_missing.get("target_rejected_incomplete_rows") != 0
        or determinism.get("status") != "CLEAN_PASS"
        or determinism.get("full_pipeline_byte_identical") is not True
        or determinism.get("score_frame_byte_identical") is not True
        or drift_lock.get("status") != "CLEAN_PASS"
        or drift_lock.get("same_run_input_snapshot_stable") is not True
        or drift_lock.get("model_schema") != "FEILONG_YAOGU_32D_SCORE_V2"
        or drift_lock.get("model_validation_status") != "CLEAN_PASS"
        or drift_lock.get("development_grade_monotonic") is not True
        or drift_lock.get("sealed_holdout_top_grade_positive_lift") is not True
        or drift_lock.get("imputed_training_cells") != 0
        or drift_lock.get("decision_rule_version") != "FEILONG_32D_DECISION_V2"
        or drift_lock.get("production_rule_lock", {}).get("sha256") != DAILY_PRODUCTION_LOCK_SHA256
    ):
        raise RuntimeError("daily production scoring hard gate is not clean")
    return bound


def extract_daily_yaogu_scoring_v3_artifacts(stdout: str) -> dict[str, dict[str, object]]:
    decoder = json.JSONDecoder()
    result: dict | None = None
    for offset, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(stdout[offset:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and candidate.get("schema") == "FEILONG_DAILY_YAOGU_PRODUCTION_V3":
            result = candidate
    if result is None:
        raise RuntimeError("daily V3 multidimension scoring result missing from stdout")
    checks = result.get("checks")
    if (
        result.get("status") != "CLEAN_PASS"
        or result.get("formula_name") != "飞龙在天"
        or result.get("formula_sha256") != "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0"
        or result.get("legacy_4_0_used") is not False
        or not isinstance(checks, dict)
        or checks.get("factor_count") != 1280
        or checks.get("rankable_factor_count") != 1273
        or checks.get("registered_dimension_count") != 325
        or checks.get("dimension_count") != 319
        or checks.get("missing_factor_columns") != 0
        or checks.get("production_missing_cells") != 0
        or checks.get("production_nonfinite_cells") != 0
        or checks.get("rejected_incomplete_count") != 0
        or checks.get("target_rejected_incomplete_count") != 0
        or checks.get("score_nulls") != 0
        or checks.get("stale") is not False
        or checks.get("target_date") != checks.get("tdx_latest_date")
        or checks.get("rule_assets_locked") is not True
        or checks.get("tdx_input_snapshot_stable") is not True
        or checks.get("decision_rule_machine_only") is not True
        or checks.get("determinism_verified") is not True
        or not DAILY_PRODUCTION_LOCK_V3.is_file()
        or sha256_file(DAILY_PRODUCTION_LOCK_V3) != DAILY_PRODUCTION_LOCK_V3_SHA256
    ):
        raise RuntimeError("daily V3 multidimension scoring validation is not clean")
    declared = result.get("artifacts")
    required_names = {
        "飞龙在天_补档首板扫描.csv",
        "飞龙在天_补档共振候选1280因子.csv",
        "飞龙在天_补档319维评分.csv",
        "飞龙在天_当日319维实战评分.csv",
        "飞龙在天_数据完整性拒绝.csv",
        "飞龙在天_生产评分决策.csv",
        "飞龙在天_零缺失审计.json",
        "飞龙在天_生产漂移锁.json",
        "飞龙在天_确定性复跑证据.json",
        "飞龙在天_实战评分报告.md",
        "飞龙在天_实战评分清单.json",
        "飞龙在天_全局旧版剔除审计.json",
    }
    if not isinstance(declared, dict) or not required_names.issubset(declared):
        raise RuntimeError("daily V3 multidimension scoring required artifact set incomplete")
    bound: dict[str, dict[str, object]] = {}
    for index, name in enumerate(sorted(required_names), start=1):
        row = declared[name]
        if not isinstance(row, dict):
            raise RuntimeError(f"daily V3 scoring artifact declaration invalid:{name}")
        path = Path(str(row.get("path", ""))).resolve()
        if not path.is_file() or path.name != name:
            raise RuntimeError(f"daily V3 scoring artifact missing:{path}")
        size = path.stat().st_size
        digest = sha256_file(path)
        if row.get("size") != size or str(row.get("sha256", "")).casefold() != digest:
            raise RuntimeError(f"daily V3 scoring artifact hash mismatch:{name}")
        bound[f"daily_yaogu_v3_score_artifact_{index:02d}"] = {"path": str(path), "size": size, "sha256": digest}
    zero_missing = json.loads(Path(str(declared["飞龙在天_零缺失审计.json"]["path"])).read_text(encoding="utf-8"))
    determinism = json.loads(Path(str(declared["飞龙在天_确定性复跑证据.json"]["path"])).read_text(encoding="utf-8"))
    drift_lock = json.loads(Path(str(declared["飞龙在天_生产漂移锁.json"]["path"])).read_text(encoding="utf-8"))
    if (
        zero_missing.get("status") != "CLEAN_PASS"
        or zero_missing.get("candidate_factor_count") != 1280
        or zero_missing.get("rankable_factor_count") != 1273
        or zero_missing.get("source_invalid_cells") != 0
        or zero_missing.get("source_nan_cells") != 0
        or zero_missing.get("production_missing_cells") != 0
        or zero_missing.get("production_nonfinite_cells") != 0
        or zero_missing.get("rejected_incomplete_rows") != 0
        or zero_missing.get("target_rejected_incomplete_rows") != 0
        or determinism.get("status") != "CLEAN_PASS"
        or determinism.get("full_pipeline_byte_identical") is not True
        or determinism.get("score_frame_byte_identical") is not True
        or drift_lock.get("status") != "CLEAN_PASS"
        or drift_lock.get("same_run_input_snapshot_stable") is not True
        or drift_lock.get("model_schema") != "FEILONG_YAOGU_MULTIDIM_SCORE_V3"
        or drift_lock.get("model_validation_status") != "CLEAN_PASS"
        or drift_lock.get("development_grade_monotonic") is not True
        or drift_lock.get("sealed_holdout_top_grade_positive_lift") is not True
        or drift_lock.get("imputed_training_cells") != 0
        or drift_lock.get("decision_rule_version") != "FEILONG_MULTIDIM_DECISION_V3"
        or drift_lock.get("production_rule_lock", {}).get("sha256") != DAILY_PRODUCTION_LOCK_V3_SHA256
    ):
        raise RuntimeError("daily V3 production scoring hard gate is not clean")
    return bound


def _daily_production_payload(stdout: str) -> dict:
    decoder = json.JSONDecoder()
    payload: dict | None = None
    for offset, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(stdout[offset:])
        except json.JSONDecodeError:
            continue
        if (
            isinstance(candidate, dict)
            and candidate.get("schema") in {
                "FEILONG_DAILY_YAOGU_PRODUCTION_V2",
                "FEILONG_DAILY_YAOGU_PRODUCTION_V3",
            }
        ):
            payload = candidate
    if payload is None:
        raise RuntimeError("daily production payload missing")
    return payload


def _iso_trade_date(value: object) -> str:
    text = str(value or "").strip()
    if len(text) == 8 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d").date().isoformat()
    return datetime.strptime(text, "%Y-%m-%d").date().isoformat()


def _declared_artifact_path(payload: dict, name: str) -> Path:
    declared = payload.get("artifacts")
    row = declared.get(name) if isinstance(declared, dict) else None
    if not isinstance(row, dict):
        raise RuntimeError(f"data gate artifact declaration missing:{name}")
    path = Path(str(row.get("path") or "")).resolve()
    if not path.is_file() or path.name != name:
        raise RuntimeError(f"data gate artifact missing:{name}")
    size = path.stat().st_size
    digest = sha256_file(path)
    if row.get("size") != size or str(row.get("sha256") or "").casefold() != digest:
        raise RuntimeError(f"data gate artifact hash mismatch:{name}")
    return path


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _csv_true(value: object) -> bool:
    return str(value or "").strip().casefold() in {"1", "true", "yes"}


def _file_evidence_is_current(row: object, expected_root: Path | None = None) -> bool:
    if not isinstance(row, dict):
        return False
    path = Path(str(row.get("path") or "")).resolve()
    if not path.is_file():
        return False
    if expected_root is not None:
        try:
            path.relative_to(expected_root.resolve())
        except ValueError:
            return False
    return (
        row.get("size") == path.stat().st_size
        and str(row.get("sha256") or "").casefold() == sha256_file(path)
    )


def build_daily_data_gate(stdout: str) -> dict:
    evidence_set_id = os.environ.get("CODEX_STOCK_EVIDENCE_SET_ID", "").strip()
    evidence_date_raw = os.environ.get("CODEX_STOCK_EVIDENCE_TRADING_DATE", "").strip()
    shared_status = os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS", "").strip()
    duanxianxia_path = Path(
        os.environ.get("CODEX_DUANXIANXIA_SNAPSHOT", "") or ".missing"
    ).resolve()
    errors: list[str] = []
    checks = {name: False for name in DATA_GATE_DIMENSIONS}
    evidence_ids = {name: [] for name in DATA_GATE_DIMENSIONS}
    effective_date = ""
    latest_required_date = ""
    try:
        payload = _daily_production_payload(stdout)
        is_v3 = payload.get("schema") == "FEILONG_DAILY_YAOGU_PRODUCTION_V3"
        manifest_path = _declared_artifact_path(payload, "飞龙在天_实战评分清单.json")
        decision_path = _declared_artifact_path(payload, "飞龙在天_生产评分决策.csv")
        today_path = _declared_artifact_path(
            payload,
            "飞龙在天_当日319维实战评分.csv" if is_v3 else "飞龙在天_当日32维实战评分.csv",
        )
        drift_path = _declared_artifact_path(payload, "飞龙在天_生产漂移锁.json")
        zero_path = _declared_artifact_path(payload, "飞龙在天_零缺失审计.json")
        legacy_path = _declared_artifact_path(payload, "飞龙在天_全局旧版剔除审计.json")
        checks_payload = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
        inputs = payload.get("inputs") if isinstance(payload.get("inputs"), dict) else {}
        drift = json.loads(drift_path.read_text(encoding="utf-8"))
        zero_missing = json.loads(zero_path.read_text(encoding="utf-8"))
        legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
        decisions = _csv_rows(decision_path)
        today_rows = _csv_rows(today_path)
        accepted = [
            row
            for row in decisions
            if str(row.get("production_decision") or "").startswith("ACCEPT_SCORE_")
        ]
        hard_rejected = [
            row
            for row in decisions
            if row.get("production_decision") == "REJECT_HARD_GATE"
        ]
        rejected = [
            row
            for row in decisions
            if row.get("production_decision") == "REJECT_DATA_INCOMPLETE"
        ]
        formally_scored = [*accepted, *hard_rejected]
        decision_keys = [
            (str(row.get("symbol") or "").strip(), str(row.get("first_board_date") or "").strip())
            for row in decisions
        ]
        today_by_key = {
            (str(row.get("symbol") or "").strip(), str(row.get("first_board_date") or "").strip()): row
            for row in today_rows
        }
        accepted_today = [today_by_key.get(key) for key in decision_keys if key in {
            (str(row.get("symbol") or "").strip(), str(row.get("first_board_date") or "").strip())
            for row in accepted
        }]

        effective_date = _iso_trade_date(checks_payload.get("target_date"))
        latest_required_date = _iso_trade_date(evidence_date_raw)
        result_ref = f"sha256:{sha256_file(manifest_path)}"
        decision_ref = f"sha256:{sha256_file(decision_path)}"
        drift_ref = f"sha256:{sha256_file(drift_path)}"
        evidence_ref = evidence_set_id or "missing"

        checks["identity"] = (
            payload.get("status") == "CLEAN_PASS"
            and len(decisions)
            == int(checks_payload.get("target_scored_count", -1))
            + int(checks_payload.get("target_hard_excluded_outside_model_domain_count", 0))
            + int(checks_payload.get("target_rejected_incomplete_count", -1))
            and len(formally_scored)
            == int(checks_payload.get("target_scored_count", -1))
            + int(checks_payload.get("target_hard_excluded_outside_model_domain_count", 0))
            and len(rejected) == int(checks_payload.get("target_rejected_incomplete_count", -1))
            and len(rejected) == 0
            and len(formally_scored) + len(rejected) == len(decisions)
            and len(decision_keys) == len(set(decision_keys))
            and all(code and name and date for (code, date), name in zip(
                decision_keys,
                [str(row.get("name") or "").strip() for row in decisions],
                strict=True,
            ))
            and all(
                row.get("decision_rule_version")
                == ("FEILONG_MULTIDIM_DECISION_V3" if is_v3 else "FEILONG_32D_DECISION_V2")
                for row in decisions
            )
        )
        checks["effective_trading_date"] = bool(
            effective_date
            and effective_date == latest_required_date
            and checks_payload.get("target_date") == checks_payload.get("tdx_latest_date")
            and checks_payload.get("stale") is False
        )
        tdx_snapshot = drift.get("tdx_input_snapshot") if isinstance(drift, dict) else {}
        checks["quote_kline"] = (
            drift.get("status") == "CLEAN_PASS"
            and drift.get("same_run_input_snapshot_stable") is True
            and checks_payload.get("tdx_input_snapshot_stable") is True
            and int(checks_payload.get("tdx_mainboard_readable_count", 0)) > 0
            and int(checks_payload.get("tdx_mainboard_at_latest_count", 0)) > 0
            and isinstance(tdx_snapshot, dict)
            and int(tdx_snapshot.get("file_count", 0)) > 0
            and len(str(tdx_snapshot.get("sha256") or "")) == 64
        )
        finance_clean = _file_evidence_is_current(
            inputs.get("finance"), resolve_tdx_root()
        )
        checks["fundamentals"] = (
            finance_clean
            and all(row is not None for row in accepted_today)
            and all(
                _csv_true(row.get("formula_resolved"))
                and not _csv_true(row.get("hard_exclusion"))
                and str(row.get("production_decision") or "").startswith("ACCEPT_SCORE_")
                for row in accepted_today
                if row is not None
            )
            and all(row.get("factor_completeness") == "REJECTED" for row in rejected)
        )
        risk_snapshot = drift.get("risk_corpus_snapshot") if isinstance(drift, dict) else {}
        checks["news_announcements"] = (
            shared_status == "CLEAN_PASS"
            and int(checks_payload.get("local_risk_corpus_file_count", 0)) > 0
            and isinstance(risk_snapshot, dict)
            and int(risk_snapshot.get("file_count", 0)) > 0
            and all(
                row is not None
                and row.get("announcement_verification_status") == "本机近14日本地资讯已扫描"
                for row in accepted_today
            )
        )
        duanxianxia: dict = {}
        if duanxianxia_path.is_file():
            duanxianxia = json.loads(duanxianxia_path.read_text(encoding="utf-8"))
        datasets = duanxianxia.get("datasets") if isinstance(duanxianxia, dict) else None
        checks["sector_theme"] = (
            shared_status == "CLEAN_PASS"
            and duanxianxia.get("source_page") == "https://duanxianxia.com/web/main"
            and isinstance(datasets, dict)
            and bool(datasets)
            and all(isinstance(item, dict) and item.get("success") is True for item in datasets.values())
        )
        checks["source_freshness"] = (
            shared_status == "CLEAN_PASS"
            and checks["effective_trading_date"]
            and checks["quote_kline"]
            and zero_missing.get("status") == "CLEAN_PASS"
            and zero_missing.get("source_invalid_cells") == 0
            and zero_missing.get("source_nan_cells") == 0
            and zero_missing.get("production_missing_cells") == 0
            and zero_missing.get("production_nonfinite_cells") == 0
            and zero_missing.get("rejected_incomplete_rows") == 0
            and zero_missing.get("target_rejected_incomplete_rows") == 0
            and legacy.get("status") == "CLEAN_PASS"
            and legacy.get("active_executable_old_formula_references") == 0
        )
        evidence_ids = {
            "identity": [f"{decision_ref}#identity_and_machine_decision"],
            "effective_trading_date": [f"{result_ref}#checks.target_date", f"{evidence_ref}#trading_date"],
            "quote_kline": [f"{drift_ref}#tdx_input_snapshot", f"{result_ref}#checks.tdx_latest_date"],
            "fundamentals": [f"{result_ref}#inputs.finance", f"{decision_ref}#hard_exclusion"],
            "news_announcements": [f"{drift_ref}#risk_corpus_snapshot", f"{evidence_ref}#duanxianxia"],
            "sector_theme": [f"{evidence_ref}#duanxianxia.datasets"],
            "source_freshness": [f"{drift_ref}#same_run_input_snapshot_stable", f"{evidence_ref}#created_at"],
        }
    except (OSError, UnicodeError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        errors.append(f"data_gate_build_failed:{type(exc).__name__}:{exc}")

    if not evidence_set_id:
        errors.append("evidence_set_id_missing")
    if shared_status != "CLEAN_PASS":
        errors.append("shared_evidence_not_clean")
    for name in DATA_GATE_DIMENSIONS:
        if not checks[name]:
            errors.append(f"data_gate_dimension_failed:{name}")
    return {
        "schema": "STOCK_DATA_GATE_V1",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "skill_id": SKILL_ID,
        "effective_trading_date": effective_date,
        "latest_required_trading_date": latest_required_date,
        "evidence_set_id": evidence_set_id,
        "dimensions": {
            name: {
                "status": "CLEAN_PASS" if checks[name] else "BLOCKED",
                "evidence_ids": evidence_ids[name],
            }
            for name in DATA_GATE_DIMENSIONS
        },
        "errors": errors,
    }


def build_realtime_data_gate(stdout: str) -> dict:
    evidence_set_id = os.environ.get("CODEX_STOCK_EVIDENCE_SET_ID", "").strip()
    evidence_date_raw = os.environ.get("CODEX_STOCK_EVIDENCE_TRADING_DATE", "").strip()
    shared_status = os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS", "").strip()
    duanxianxia_path = Path(
        os.environ.get("CODEX_DUANXIANXIA_SNAPSHOT", "") or ".missing"
    ).resolve()
    errors: list[str] = []
    checks = {name: False for name in DATA_GATE_DIMENSIONS}
    evidence_ids = {name: [] for name in DATA_GATE_DIMENSIONS}
    effective_date = ""
    latest_required_date = ""
    try:
        decoder = json.JSONDecoder()
        payload: dict | None = None
        for offset, character in enumerate(stdout):
            if character != "{":
                continue
            try:
                candidate, _ = decoder.raw_decode(stdout[offset:])
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict) and candidate.get("analysis_json"):
                payload = candidate
        if payload is None:
            raise RuntimeError("realtime output payload missing")

        report_path = Path(str(payload.get("report") or "")).resolve()
        analysis_path = Path(str(payload.get("analysis_json") or "")).resolve()
        if not report_path.is_file() or not analysis_path.is_file():
            raise RuntimeError("realtime report or analysis artifact missing")
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        date_context = analysis.get("date_context") if isinstance(analysis, dict) else None
        realtime = analysis.get("realtime_calc") if isinstance(analysis, dict) else None
        snapshot = analysis.get("snapshot") if isinstance(analysis, dict) else None
        info = analysis.get("info") if isinstance(analysis, dict) else None
        if not all(isinstance(row, dict) for row in (date_context, realtime, snapshot, info)):
            raise RuntimeError("realtime analysis structure invalid")

        effective_date = _iso_trade_date(date_context.get("analysis_as_of_date"))
        latest_required_date = _iso_trade_date(evidence_date_raw)
        symbol = str(analysis.get("symbol") or "").strip()
        name = str(analysis.get("name") or "").strip()
        checks["identity"] = bool(
            re.fullmatch(r"\d{6}\.(?:SH|SZ|BJ)", symbol)
            and name
            and info.get("Name") == name
            and info.get("ErrorId") == "0"
            and report_path.stat().st_size > 0
            and analysis_path.stat().st_size > 0
        )
        checks["effective_trading_date"] = bool(
            effective_date == latest_required_date
            and date_context.get("ok") is True
            and date_context.get("mode") == "same_day_realtime"
            and date_context.get("run_calendar_date") == date_context.get("analysis_as_of_date")
        )
        checks["quote_kline"] = bool(
            date_context.get("snapshot_available") is True
            and date_context.get("kline_has_as_of") is True
            and date_context.get("formula_has_as_of") is True
            and realtime.get("basis") == "same_day_realtime"
            and float(realtime.get("now") or 0) > 0
            and float(realtime.get("last_close") or 0) > 0
            and float(realtime.get("amount_wan") or 0) > 0
            and snapshot.get("ErrorId") == "0"
        )
        financial_fields = ("J_zzc", "J_ldzc", "J_ldfz", "J_cqfz", "J_jzc")
        checks["fundamentals"] = bool(
            info.get("IsSTGP") == "0"
            and info.get("IsQuitGP") == "0"
            and all(str(info.get(field) or "").strip() for field in financial_fields)
        )

        duanxianxia: dict = {}
        if duanxianxia_path.is_file():
            duanxianxia = json.loads(duanxianxia_path.read_text(encoding="utf-8"))
        datasets = duanxianxia.get("datasets") if isinstance(duanxianxia, dict) else None
        all_datasets_clean = bool(
            isinstance(datasets, dict)
            and datasets
            and all(isinstance(item, dict) and item.get("success") is True for item in datasets.values())
        )
        checks["news_announcements"] = shared_status == "CLEAN_PASS" and all_datasets_clean
        checks["sector_theme"] = bool(
            shared_status == "CLEAN_PASS"
            and all_datasets_clean
            and str(info.get("rs_hyname") or "").strip()
            and str(info.get("tdx_dyname") or "").strip()
        )
        generated_date = _iso_trade_date(str(analysis.get("generated_at") or "")[:10])
        checks["source_freshness"] = bool(
            checks["effective_trading_date"]
            and checks["quote_kline"]
            and generated_date == latest_required_date
            and shared_status == "CLEAN_PASS"
            and all_datasets_clean
        )
        report_ref = f"sha256:{sha256_file(report_path)}"
        analysis_ref = f"sha256:{sha256_file(analysis_path)}"
        evidence_ref = evidence_set_id or "missing"
        evidence_ids = {
            "identity": [f"{analysis_ref}#symbol,name,info"],
            "effective_trading_date": [f"{analysis_ref}#date_context", f"{evidence_ref}#trading_date"],
            "quote_kline": [f"{analysis_ref}#snapshot,realtime_calc,latest_outputs"],
            "fundamentals": [f"{analysis_ref}#info.J_zzc,J_ldzc,J_ldfz,J_cqfz,J_jzc"],
            "news_announcements": [f"{evidence_ref}#duanxianxia.datasets", report_ref],
            "sector_theme": [f"{analysis_ref}#info.rs_hyname,tdx_dyname", f"{evidence_ref}#duanxianxia.datasets"],
            "source_freshness": [f"{analysis_ref}#generated_at,date_context", f"{evidence_ref}#created_at"],
        }
    except (OSError, UnicodeError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        errors.append(f"data_gate_build_failed:{type(exc).__name__}:{exc}")

    if not evidence_set_id:
        errors.append("evidence_set_id_missing")
    if shared_status != "CLEAN_PASS":
        errors.append("shared_evidence_not_clean")
    for name in DATA_GATE_DIMENSIONS:
        if not checks[name]:
            errors.append(f"data_gate_dimension_failed:{name}")
    return {
        "schema": "STOCK_DATA_GATE_V1",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "skill_id": SKILL_ID,
        "effective_trading_date": effective_date,
        "latest_required_trading_date": latest_required_date,
        "evidence_set_id": evidence_set_id,
        "dimensions": {
            name: {
                "status": "CLEAN_PASS" if checks[name] else "BLOCKED",
                "evidence_ids": evidence_ids[name],
            }
            for name in DATA_GATE_DIMENSIONS
        },
        "errors": errors,
    }


def run_child(command: list[str], timeout: int) -> dict:
    environment = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "ONESTOCK_STOCK_CANONICAL_CHILD": "1",
    }
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=environment,
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "returncode": 124,
            "stdout": stdout,
            "stderr": stderr + f"\nTIMEOUT after {timeout}s",
            "timed_out": True,
        }
    except Exception as exc:
        return {
            "returncode": 125,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "timed_out": False,
        }


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--timeout", type=int, default=300)
    args, business_args = parser.parse_known_args(argv)
    args.business_args = business_args
    return args


def main(argv: list[str] | None = None) -> int:
    enable_atomic_path_writes()
    args = parse_cli_args(argv)
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    normalized_args = normalize_business_args(args.business_args)
    delivery_manifest_mode = "--bind-delivery-manifest" in normalized_args
    report_manifest_mode = "--bind-report-manifest" in normalized_args

    if os.environ.get("CODEX_STOCK_CANONICAL_EXECUTION") != "1":
        if delivery_manifest_mode or report_manifest_mode:
            stdout_path = run_dir / "business_child.stdout.txt"
            stderr_path = run_dir / "business_child.stderr.txt"
            result_path = run_dir / "business_result.json"
            failure_tokens = ["canonical_execution_environment_missing"]
            stdout_path.write_text("", encoding="utf-8")
            stderr_path.write_text(
                "canonical_execution_environment_missing\n", encoding="utf-8"
            )
            adapter_path = Path(__file__).resolve()
            result = {
                "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
                "skill_id": SKILL_ID,
                "status": "BLOCKED",
                "business_process": {
                    "command": [
                        sys.executable,
                        str(adapter_path),
                        *normalized_args,
                    ],
                    "cwd": str(ROOT),
                    "returncode": 2,
                    "timed_out": False,
                    "failure_tokens": failure_tokens,
                },
                "business_binding": {
                    "mode": "delivery_manifest_binding",
                    "path": str(adapter_path),
                    "sha256": sha256_file(adapter_path),
                },
                "artifacts": {
                    "stdout": str(stdout_path),
                    "stderr": str(stderr_path),
                },
            }
            result_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(json.dumps(result, ensure_ascii=False))
            return 2
        print(json.dumps({
            "skill_id": SKILL_ID,
            "status": "BLOCKED",
            "errors": ["canonical_execution_environment_missing"],
        }, ensure_ascii=False))
        return 2
    if report_manifest_mode:
        stdout_path = run_dir / "business_child.stdout.txt"
        stderr_path = run_dir / "business_child.stderr.txt"
        failure_tokens: list[str] = []
        bound_report_artifacts: dict[str, dict[str, object]] = {}
        manifest_text = ""
        if (
            len(normalized_args) == 2
            and normalized_args[0] == "--bind-report-manifest"
        ):
            manifest_text = normalized_args[1]
            try:
                bound_report_artifacts = validate_report_manifest(
                    Path(manifest_text)
                )
            except (OSError, RuntimeError) as exc:
                failure_tokens.append(f"report_manifest_binding_failed:{exc}")
        else:
            failure_tokens.append("report_manifest_binding_args_invalid")
        accepted = not failure_tokens
        stdout_path.write_text(
            f"report_manifest_binding:{manifest_text}\n" if accepted else "",
            encoding="utf-8",
        )
        stderr_path.write_text(
            "\n".join(failure_tokens) + ("\n" if failure_tokens else ""),
            encoding="utf-8",
        )
        adapter_path = Path(__file__).resolve()
        result = {
            "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
            "skill_id": SKILL_ID,
            "status": "CLEAN_PASS" if accepted else "BLOCKED",
            "business_process": {
                "command": [sys.executable, str(adapter_path), *normalized_args],
                "cwd": str(ROOT),
                "returncode": 0 if accepted else 2,
                "timed_out": False,
                "failure_tokens": failure_tokens,
            },
            "business_binding": {
                "mode": "report_manifest_binding",
                "path": str(adapter_path),
                "sha256": sha256_file(adapter_path),
            },
            "artifacts": {
                "stdout": str(stdout_path),
                "stderr": str(stderr_path),
                **bound_report_artifacts,
            },
        }
        result_path = run_dir / "business_result.json"
        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0 if accepted else 2
    if delivery_manifest_mode:
        stdout_path = run_dir / "business_child.stdout.txt"
        stderr_path = run_dir / "business_child.stderr.txt"
        failure_tokens: list[str] = []
        bound_delivery_artifacts: dict[str, dict[str, object]] = {}
        manifest_text = ""
        if (
            len(normalized_args) == 2
            and normalized_args[0] == "--bind-delivery-manifest"
        ):
            manifest_text = normalized_args[1]
            try:
                bound_delivery_artifacts = validate_delivery_manifest(
                    Path(manifest_text)
                )
            except (OSError, RuntimeError) as exc:
                failure_tokens.append(f"delivery_manifest_binding_failed:{exc}")
        else:
            failure_tokens.append("delivery_manifest_binding_args_invalid")
        accepted = not failure_tokens
        stdout_path.write_text(
            f"delivery_manifest_binding:{manifest_text}\n" if accepted else "",
            encoding="utf-8",
        )
        stderr_path.write_text(
            "\n".join(failure_tokens) + ("\n" if failure_tokens else ""),
            encoding="utf-8",
        )
        adapter_path = Path(__file__).resolve()
        result = {
            "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
            "skill_id": SKILL_ID,
            "status": "CLEAN_PASS" if accepted else "BLOCKED",
            "business_process": {
                "command": [
                    sys.executable,
                    str(adapter_path),
                    *normalized_args,
                ],
                "cwd": str(ROOT),
                "returncode": 0 if accepted else 2,
                "timed_out": False,
                "failure_tokens": failure_tokens,
            },
            "business_binding": {
                "mode": "delivery_manifest_binding",
                "path": str(adapter_path),
                "sha256": sha256_file(adapter_path),
            },
            "artifacts": {
                "stdout": str(stdout_path),
                "stderr": str(stderr_path),
                **bound_delivery_artifacts,
            },
        }
        result_path = run_dir / "business_result.json"
        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0 if accepted else 2
    if not LEGACY_ENTRY.is_file():
        print(json.dumps({
            "skill_id": SKILL_ID,
            "status": "BLOCKED",
            "errors": [f"legacy_entry_missing:{LEGACY_ENTRY}"],
        }, ensure_ascii=False))
        return 2

    command = business_command(run_dir, args.business_args)
    if "--daily-score-v3" in normalized_args and (
        not DAILY_PRODUCTION_LOCK_V3.is_file()
        or sha256_file(DAILY_PRODUCTION_LOCK_V3) != DAILY_PRODUCTION_LOCK_V3_SHA256
    ):
        child = {
            "returncode": 2,
            "stdout": "",
            "stderr": "daily_v3_production_rule_lock_drift",
            "timed_out": False,
        }
    elif "--daily-score-32d" in normalized_args and (
        not DAILY_PRODUCTION_LOCK.is_file()
        or sha256_file(DAILY_PRODUCTION_LOCK) != DAILY_PRODUCTION_LOCK_SHA256
    ):
        child = {
            "returncode": 2,
            "stdout": "",
            "stderr": "daily_production_rule_lock_drift",
            "timed_out": False,
        }
    else:
        child = run_child(command, args.timeout)
    stdout_path = run_dir / "business_child.stdout.txt"
    stderr_path = run_dir / "business_child.stderr.txt"
    stdout_path.write_text(str(child["stdout"]), encoding="utf-8")
    stderr_path.write_text(str(child["stderr"]), encoding="utf-8")
    combined = str(child["stdout"]) + "\n" + str(child["stderr"])
    failure_tokens = [token for token in FAILURE_TOKENS if token in combined]
    accepted = child["returncode"] == 0 and not failure_tokens
    bound_backtest_artifacts: dict[str, dict[str, object]] = {}
    bound_factor_artifacts: dict[str, dict[str, object]] = {}
    bound_resonance_exhaustive_artifacts: dict[str, dict[str, object]] = {}
    bound_deep_factor_artifacts: dict[str, dict[str, object]] = {}
    bound_factor_correlation_v3_artifacts: dict[str, dict[str, object]] = {}
    bound_yaogu_scoring_artifacts: dict[str, dict[str, object]] = {}
    bound_yaogu_scoring_v3_artifacts: dict[str, dict[str, object]] = {}
    bound_daily_yaogu_scoring_artifacts: dict[str, dict[str, object]] = {}
    bound_daily_yaogu_scoring_v3_artifacts: dict[str, dict[str, object]] = {}
    if accepted and "--backtest" in normalized_args:
        try:
            bound_backtest_artifacts = extract_backtest_artifacts(str(child["stdout"]))
        except RuntimeError as exc:
            failure_tokens.append(f"backtest_artifact_binding_failed:{exc}")
            accepted = False
    if accepted and "--factor-research" in normalized_args:
        try:
            bound_factor_artifacts = extract_factor_research_artifacts(str(child["stdout"]))
        except RuntimeError as exc:
            failure_tokens.append(f"factor_research_artifact_binding_failed:{exc}")
            accepted = False
    if accepted and "--factor-exhaustive" in normalized_args:
        try:
            bound_resonance_exhaustive_artifacts = extract_resonance_exhaustive_artifacts(
                str(child["stdout"])
            )
        except RuntimeError as exc:
            failure_tokens.append(f"resonance_exhaustive_artifact_binding_failed:{exc}")
            accepted = False
    if accepted and "--factor-deep" in normalized_args:
        try:
            bound_deep_factor_artifacts = extract_deep_factor_artifacts(str(child["stdout"]))
        except RuntimeError as exc:
            failure_tokens.append(f"deep_factor_artifact_binding_failed:{exc}")
            accepted = False
    if accepted and "--factor-correlation-v3" in normalized_args:
        try:
            bound_factor_correlation_v3_artifacts = extract_factor_correlation_v3_artifacts(str(child["stdout"]))
        except RuntimeError as exc:
            failure_tokens.append(f"factor_correlation_v3_artifact_binding_failed:{exc}")
            accepted = False
    if accepted and "--score-32d" in normalized_args:
        try:
            bound_yaogu_scoring_artifacts = extract_yaogu_scoring_artifacts(str(child["stdout"]))
        except RuntimeError as exc:
            failure_tokens.append(f"yaogu_scoring_artifact_binding_failed:{exc}")
            accepted = False
    if accepted and "--score-v3" in normalized_args:
        try:
            bound_yaogu_scoring_v3_artifacts = extract_yaogu_scoring_v3_artifacts(str(child["stdout"]))
        except RuntimeError as exc:
            failure_tokens.append(f"yaogu_scoring_v3_artifact_binding_failed:{exc}")
            accepted = False
    if accepted and "--daily-score-32d" in normalized_args:
        try:
            bound_daily_yaogu_scoring_artifacts = extract_daily_yaogu_scoring_artifacts(str(child["stdout"]))
        except RuntimeError as exc:
            failure_tokens.append(f"daily_yaogu_scoring_artifact_binding_failed:{exc}")
            accepted = False
    if accepted and "--daily-score-v3" in normalized_args:
        try:
            bound_daily_yaogu_scoring_v3_artifacts = extract_daily_yaogu_scoring_v3_artifacts(str(child["stdout"]))
        except RuntimeError as exc:
            failure_tokens.append(f"daily_yaogu_scoring_v3_artifact_binding_failed:{exc}")
            accepted = False
    evidence_enabled = bool(
        os.environ.get("CODEX_STOCK_EVIDENCE_SET_ID")
        or os.environ.get("CODEX_STOCK_SHARED_EVIDENCE_STATUS")
    )
    data_gate: dict | None = None
    if evidence_enabled:
        if "--daily-score-32d" in normalized_args or "--daily-score-v3" in normalized_args:
            data_gate = build_daily_data_gate(str(child["stdout"]))
        else:
            data_gate = build_realtime_data_gate(str(child["stdout"]))
        data_gate_errors = list(data_gate.get("errors", []))
        if data_gate_errors:
            failure_tokens.extend(data_gate_errors)
            accepted = False
    result = {
        "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
        "skill_id": SKILL_ID,
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "business_process": {
            "command": command,
            "cwd": str(ROOT),
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
            "failure_tokens": failure_tokens,
        },
        "business_binding": {
            "path": str(LEGACY_ENTRY),
            "sha256": sha256_file(LEGACY_ENTRY),
        },
        "artifacts": {
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            **bound_backtest_artifacts,
            **bound_factor_artifacts,
            **bound_resonance_exhaustive_artifacts,
            **bound_deep_factor_artifacts,
            **bound_factor_correlation_v3_artifacts,
            **bound_yaogu_scoring_artifacts,
            **bound_yaogu_scoring_v3_artifacts,
            **bound_daily_yaogu_scoring_artifacts,
            **bound_daily_yaogu_scoring_v3_artifacts,
        },
    }
    if data_gate is not None:
        result["data_gate"] = data_gate
    if data_gate is not None and data_gate.get("errors"):
        result["errors"] = list(data_gate["errors"])
    result_path = run_dir / "business_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
