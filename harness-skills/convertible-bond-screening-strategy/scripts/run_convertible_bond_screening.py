from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Iterable

from runtime_utils import (
    atomic_write_json,
    canonical_business_sum,
    canonicalize_business_payload,
)
_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_tdx_root


SKILL_ROOT = Path(__file__).resolve().parent.parent
TDX_ROOT = resolve_tdx_root()
SKILLS_ROOT = SKILL_ROOT.parent
HQ_CACHE = TDX_ROOT / "T0002" / "hq_cache"
BOND_SOURCE = HQ_CACHE / "speckzzdata.txt"
TDXHY = HQ_CACHE / "tdxhy.cfg"
TDXZS = HQ_CACHE / "tdxzs3.cfg"
INFOHARBOR = HQ_CACHE / "infoharbor_block.dat"
TDX_HUB = SKILLS_ROOT / "tdx-local-hub" / "scripts" / "tdx_hub.py"
TQ_RUNTIME = TDX_ROOT / "PYPlugins" / "user" / "tqcenter.py"
TDX_FORMULA_STORE = TDX_ROOT / "T0002" / "PriGS.dat"
TQ_STRATEGY_PATH = Path(__file__).resolve()
TNF_FILES = {"sh": HQ_CACHE / "shs.tnf", "sz": HQ_CACHE / "szs.tnf"}
MARKET_BY_FLAG = {"1": "sh", "0": "sz"}
TNF_HEADER = 50
TNF_RECORD = 360
TQ_BATCH_SIZE = 320
TQ_LONG_FORMULA_HISTORY_COUNT = 600
MARKET_SNAPSHOT_WORKERS = min(12, max(4, os.cpu_count() or 4))
DAY_RECORD_SIZE = 32
DAY_INPUT_TAIL_RECORD_LIMIT = 260
DAY_INPUT_SCHEMA = "CONVERTIBLE-BOND-DAY-INPUT-MANIFEST-2"
DAY_INPUT_BINDING_MODE = "immutable_tail_snapshot_pre_and_post"
SOURCE_BINDING_MODE = "stable_sha256_pre_and_post_run"
TDX_DAY_UPDATE_RACE = "TDX_DAY_UPDATE_RACE"
NON_DIRECTION_MARKERS = (
    "含B股", "含H股", "ST板块", "中特估", "融资融券", "转融券", "机构重仓",
)
EQUITY_PREFIXES = (
    "000", "001", "002", "003", "300", "301", "600", "601", "603", "605",
    "688", "689", "830", "831", "832", "834", "835", "836", "837", "838",
    "839", "870", "871", "872", "873", "874", "875", "876", "877", "878",
    "879", "880", "881", "882", "883", "884", "885", "886", "887", "888",
    "889", "890", "891", "892", "893", "894", "895", "896", "897", "898", "899",
)
SCORE_CRITERIA = (
    {
        "id": "c1_price_activity",
        "name_zh": "近5日强势涨幅",
        "weight": 6.0,
        "full_score_anchor": "近5日涨幅>=5%；下跌不加分",
    },
    {
        "id": "c2_remaining_scale",
        "name_zh": "剩余流通规模",
        "weight": 8.0,
        "full_score_anchor": "剩余流通规模<=5亿元",
    },
    {
        "id": "c3_premium",
        "name_zh": "转股溢价率",
        "weight": 12.0,
        "full_score_anchor": "转股溢价率<=10%；50%以内保留至少一半得分",
    },
    {
        "id": "c4_golden_ignition",
        "name_zh": "近期黄金点火",
        "weight": 14.0,
        "full_score_anchor": "正股最近交易日触发EMA3上穿EMA21",
    },
    {
        "id": "c5_feilong_cross",
        "name_zh": "飞龙在天20以下金叉",
        "weight": 15.0,
        "full_score_anchor": "飞龙低位金叉，且金叉形成时波、段均低于20",
    },
    {
        "id": "c6_youzi_inflow",
        "name_zh": "游资资金开始流入",
        "weight": 15.0,
        "full_score_anchor": "买方意向近期上穿0、当前为正且继续增强",
    },
    {
        "id": "c7_scr90_convergence",
        "name_zh": "90%筹码峰收敛",
        "weight": 6.0,
        "full_score_anchor": "绝对缩小>=10个百分点且相对缩小>=1/3（30降到20为满分）",
    },
    {
        "id": "c8_scr70_convergence",
        "name_zh": "70%筹码峰集中度收敛",
        "weight": 8.0,
        "full_score_anchor": "SCR70较5个交易日前缩小>=3个百分点",
    },
    {
        "id": "c9_sector_heat",
        "name_zh": "行业、概念热度与正股趋势",
        "weight": 8.0,
        "full_score_anchor": "行业热度30%+最强概念热度40%+正股趋势30%",
    },
    {
        "id": "c11_turnover5",
        "name_zh": "近5日累计换手率",
        "weight": 8.0,
        "full_score_anchor": "近5日累计换手率>=150%",
    },
)
C9_NORMALIZATION_RULE = "30% industry percentile heat + 40% highest concept heat score + 30% underlying trend"
EARLY_REDEMPTION_SCHEMA = "CONVERTIBLE-BOND-EARLY-REDEMPTION-SNAPSHOT-1"
EARLY_REDEMPTION_STATUSES = {
    "ANNOUNCED_EARLY_REDEMPTION",
    "NO_MATCH_AS_OF_CUTOFF",
    "UNVERIFIED",
}
HARD_EXCLUSION_MODEL = {
    "id": "CB-HARD-EXCLUSION-1",
    "rules": [
        {
            "reason_code": "bond_name_z_prefix",
            "definition": "bond name, stripped and upper-cased, starts with ASCII Z",
        },
        {
            "reason_code": "daily_gain_ge_10_and_volume_ratio_gt_4",
            "definition": "daily_return_pct >= 10.0 and bond_volume_ratio_5d > 4.0",
        },
        {
            "reason_code": "scr90_change_1d_positive",
            "definition": "scr90_latest - scr90_previous > 0.0 percentage points",
        },
        {
            "reason_code": "scr90_change_1d_unavailable",
            "definition": "the exact latest two-session SCR90 comparison is unavailable",
        },
        {
            "reason_code": "turnover_5d_gt_1000",
            "definition": "turnover_5d_pct > 1000.0",
        },
        {
            "reason_code": "bond_close_gt_350",
            "definition": "bond_close > 350.0",
        },
        {
            "reason_code": "early_redemption_announced",
            "definition": "official announcement snapshot status is ANNOUNCED_EARLY_REDEMPTION",
        },
        {
            "reason_code": "early_redemption_unverified",
            "definition": "official announcement snapshot status is UNVERIFIED",
        },
    ],
}
PERSONAL_KB_CONFIRMATION_MODEL = {
    "version": "CB-PERSONAL-A-SHARE-KB-CONFIRMATION-1",
    "knowledge_source": {
        "id": "personal_a_share_investment_kb",
        "scope": "accepted category-level A-share method principles",
        "source_tables": ["knowledge_cards", "a_share_mappings"],
        "snapshot_counts": {
            "entities": 300,
            "knowledge_cards": 300,
            "claims": 900,
            "a_share_mappings": 300,
        },
        "person_attribution": False,
    },
    "score_invariance": "does_not_modify_score_components_or_score_total_raw",
    "ranking_scope": "exact_score_total_raw_ties_only",
    "automatic_order": False,
}
PERSONAL_KB_CONFIRMATION_CHECKS = (
    ("kb_liquidity_capacity_fragile", 18.0),
    ("kb_trading_cost_or_slippage_risk", 14.0),
    ("kb_gap_jump_risk", 10.0),
    ("kb_suspension_or_stale_quote_risk", 14.0),
    ("kb_data_anomaly_integrity_risk", 18.0),
    ("kb_exit_delay_risk", 16.0),
    ("kb_recomputable_evidence_missing", 10.0),
)

if not math.isclose(sum(float(item["weight"]) for item in SCORE_CRITERIA), 100.0, abs_tol=1e-12):
    raise RuntimeError("score weights must sum to 100")


def _personal_kb_finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def build_personal_kb_confirmation(item: dict[str, Any]) -> dict[str, Any]:
    turnover = _personal_kb_finite_number(item.get("turnover_5d_pct"))
    remaining = _personal_kb_finite_number(item.get("remaining_yi"))
    bond_close = _personal_kb_finite_number(item.get("bond_close"))
    premium = _personal_kb_finite_number(item.get("premium_pct"))
    daily_return = _personal_kb_finite_number(item.get("daily_return_pct"))
    coverage = _personal_kb_finite_number(item.get("score_coverage_weight"))
    intraday_status = str(item.get("intraday_status") or "").upper()
    early_redemption_status = str(item.get("early_redemption_status") or "")
    risk_level = str(item.get("risk_level") or "")

    checks = {
        "kb_liquidity_capacity_fragile": bool(
            turnover is not None
            and turnover >= 150.0
            and remaining is not None
            and remaining > 0.0
            and bond_close is not None
            and bond_close > 0.0
        ),
        "kb_trading_cost_or_slippage_risk": bool(
            item.get("volume_structure_available") is True
            and item.get("volume_structure_pass") is True
            and item.get("sudden_abnormal_volume_contraction") is False
            and intraday_status not in {"", "MISSING", "WEAK"}
        ),
        "kb_gap_jump_risk": bool(
            daily_return is not None
            and abs(daily_return) <= 20.0
            and item.get("sudden_abnormal_volume_contraction") is False
        ),
        "kb_suspension_or_stale_quote_risk": bool(
            item.get("bond_current") is True
            and item.get("stock_current") is True
            and intraday_status not in {"", "MISSING"}
        ),
        "kb_data_anomaly_integrity_risk": bool(
            turnover is not None
            and 0.0 <= turnover <= 1000.0
            and remaining is not None
            and remaining > 0.0
            and bond_close is not None
            and 0.0 < bond_close <= 350.0
            and premium is not None
            and daily_return is not None
            and early_redemption_status != "UNVERIFIED"
        ),
        "kb_exit_delay_risk": bool(
            risk_level != "RED"
            and early_redemption_status
            not in {"", "UNVERIFIED", "ANNOUNCED_EARLY_REDEMPTION"}
            and bond_close is not None
            and 0.0 < bond_close <= 350.0
            and remaining is not None
            and remaining > 0.0
            and turnover is not None
            and 0.0 < turnover <= 1000.0
        ),
        "kb_recomputable_evidence_missing": bool(
            coverage == 100.0
            and item.get("score_missing_criteria") == []
            and item.get("score_partial_criteria") == []
            and item.get("bond_full_lookback") is True
            and item.get("stock_signal_available") is True
            and item.get("volume_structure_available") is True
        ),
    }
    risk_labels = [
        label for label, _weight in PERSONAL_KB_CONFIRMATION_CHECKS
        if not checks[label]
    ]
    quality_score = 100.0 - sum(
        weight for label, weight in PERSONAL_KB_CONFIRMATION_CHECKS
        if not checks[label]
    )
    quality_score = min(100.0, max(0.0, quality_score))
    red_risk_cap_applied = risk_level == "RED"
    if red_risk_cap_applied:
        quality_score = min(quality_score, 59.0)
    level = "HIGH" if quality_score >= 85.0 else "MEDIUM" if quality_score >= 60.0 else "LOW"
    return {
        "model_version": PERSONAL_KB_CONFIRMATION_MODEL["version"],
        "quality_score": quality_score,
        "level": level,
        "risk_labels": risk_labels,
        "checks": checks,
        "red_risk_cap_applied": red_risk_cap_applied,
        "ranking_scope": "exact_score_total_raw_ties_only",
    }


def ranking_key(item: dict[str, Any]) -> tuple[float, float, bool, str]:
    return (
        -float(item.get("score_total_raw") or 0.0),
        -float(
            (item.get("personal_kb_confirmation") or {}).get("quality_score")
            or 0.0
        ),
        not bool(item.get("big_bull_red_preference")),
        str(item.get("symbol") or ""),
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class DayInputUpdateRace(RuntimeError):
    def __init__(self, message: str, diagnostics: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics or []


def file_meta(path: Path) -> dict[str, Any]:
    before = path.stat()
    digest = sha256(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError(f"source changed while hashing: {path}")
    return {
        "path": str(path),
        "size": after.st_size,
        "mtime_ns": after.st_mtime_ns,
        "sha256": digest,
        "updated_at": dt.datetime.fromtimestamp(after.st_mtime).astimezone().isoformat(),
    }


def build_source_files() -> dict[str, Any]:
    return {
        "convertible_bond_master": file_meta(BOND_SOURCE),
        "tdx_hub": file_meta(TDX_HUB),
        "industry_membership": file_meta(TDXHY),
        "industry_names": file_meta(TDXZS),
        "concept_membership": file_meta(INFOHARBOR),
        "tnf": {market: file_meta(path) for market, path in TNF_FILES.items()},
        "tq_runtime": file_meta(TQ_RUNTIME),
        "tdx_formula_store": file_meta(TDX_FORMULA_STORE),
    }


def load_early_redemption_snapshot(
    path: Path,
    *,
    run_id: str,
    cutoff: str,
    bonds: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if not path.is_file():
        raise RuntimeError(f"early-redemption snapshot missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("schema") != EARLY_REDEMPTION_SCHEMA or payload.get("status") != "PASS":
        raise RuntimeError("early-redemption snapshot is not a PASS V1 artifact")
    if payload.get("current_universe_complete") is not True:
        raise RuntimeError("early-redemption snapshot does not cover the current universe")
    if str(payload.get("run_id") or "") != run_id:
        raise RuntimeError("early-redemption snapshot run_id mismatch")
    snapshot_cutoff = str(payload.get("cutoff_trade_date") or payload.get("cutoff") or "").replace("-", "")
    if snapshot_cutoff != cutoff:
        raise RuntimeError("early-redemption snapshot cutoff mismatch")
    records = payload.get("records")
    if not isinstance(records, list):
        raise RuntimeError("early-redemption snapshot records are missing")
    expected_symbols = {str(bond["symbol"]) for bond in bonds}
    by_symbol: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise RuntimeError("early-redemption record is not an object")
        symbol = str(record.get("symbol") or "")
        status = str(record.get("early_redemption_status") or "")
        if symbol in by_symbol:
            raise RuntimeError(f"duplicate early-redemption record: {symbol}")
        if symbol not in expected_symbols:
            raise RuntimeError(f"unexpected early-redemption record: {symbol}")
        if status not in EARLY_REDEMPTION_STATUSES:
            raise RuntimeError(f"invalid early-redemption status for {symbol}: {status}")
        by_symbol[symbol] = record
    if set(by_symbol) != expected_symbols:
        missing = sorted(expected_symbols - set(by_symbol))
        raise RuntimeError(f"early-redemption snapshot universe incomplete: {missing[:10]}")
    coverage = payload.get("coverage") or {}
    if coverage and int(coverage.get("record_count", len(records))) != len(records):
        raise RuntimeError("early-redemption snapshot coverage count mismatch")
    snapshot_meta = file_meta(path)
    snapshot_meta.update({
        "run_id": run_id,
        "cutoff": cutoff,
        "status": "PASS",
        "current_universe_complete": True,
    })
    return by_symbol, snapshot_meta


def day_tail_meta(
    path: Path,
    lookup_symbols: list[str],
    max_records: int = DAY_INPUT_TAIL_RECORD_LIMIT,
    *,
    include_raw: bool = False,
) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        return {
            "lookup_symbols": sorted(lookup_symbols),
            "path": str(resolved),
            "exists": False,
            "valid_layout": False,
            **({"_raw": b""} if include_raw else {}),
        }
    before = resolved.stat()
    valid_layout = before.st_size > 0 and before.st_size % DAY_RECORD_SIZE == 0
    record_count = before.st_size // DAY_RECORD_SIZE if valid_layout else 0
    tail_record_count = min(record_count, max_records)
    tail_size = tail_record_count * DAY_RECORD_SIZE
    tail_offset = before.st_size - tail_size
    raw = b""
    if tail_size:
        with resolved.open("rb") as handle:
            handle.seek(tail_offset)
            raw = handle.read(tail_size)
    after = resolved.stat()
    if len(raw) != tail_size or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise DayInputUpdateRace(f"{TDX_DAY_UPDATE_RACE}:day_file_changed_while_capturing:{resolved}")
    node = {
        "lookup_symbols": sorted(lookup_symbols),
        "path": str(resolved),
        "exists": True,
        "valid_layout": valid_layout,
        "file_size": after.st_size,
        "mtime_ns": after.st_mtime_ns,
        "tail_record_count": tail_record_count,
        "tail_offset": tail_offset,
        "tail_size": tail_size,
        "tail_sha256": hashlib.sha256(raw).hexdigest(),
    }
    if include_raw:
        node["_raw"] = raw
    return node


def _day_path_groups(hub, lookup_symbols: Iterable[str]) -> dict[str, dict[str, Any]]:
    symbols = sorted(set(str(value) for value in lookup_symbols))
    by_path: dict[str, dict[str, Any]] = {}
    for lookup_symbol in symbols:
        path = Path(hub.day_path(lookup_symbol)).resolve()
        key = str(path).casefold()
        by_path.setdefault(key, {"path": path, "lookup_symbols": []})["lookup_symbols"].append(lookup_symbol)
    return by_path


def _capture_day_inputs(hub, lookup_symbols: Iterable[str]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    by_path = _day_path_groups(hub, lookup_symbols)
    inputs = [
        day_tail_meta(node["path"], node["lookup_symbols"], include_raw=True)
        for node in sorted(by_path.values(), key=lambda item: str(item["path"]).casefold())
    ]
    alias_paths = {
        alias: str(node["path"])
        for node in inputs
        for alias in node["lookup_symbols"]
    }
    return inputs, alias_paths


def _public_day_nodes(inputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: value for key, value in node.items() if key != "_raw"} for node in inputs]


def _day_capture_signature(inputs: list[dict[str, Any]], alias_paths: dict[str, str]) -> tuple[Any, ...]:
    return (
        tuple(sorted((alias, path.casefold()) for alias, path in alias_paths.items())),
        tuple(
            (
                str(node.get("path") or "").casefold(),
                tuple(node.get("lookup_symbols") or []),
                node.get("exists"),
                node.get("valid_layout"),
                node.get("file_size"),
                node.get("mtime_ns"),
                node.get("tail_record_count"),
                node.get("tail_offset"),
                node.get("tail_size"),
                node.get("tail_sha256"),
            )
            for node in inputs
        ),
    )


class FrozenDayHub:
    def __init__(self, base_hub, inputs: list[dict[str, Any]], alias_paths: dict[str, str]) -> None:
        self._base_hub = base_hub
        self._nodes = {str(node["path"]).casefold(): node for node in inputs}
        self._alias_paths = dict(alias_paths)

    def day_path(self, symbol: str) -> Path:
        path = self._alias_paths.get(str(symbol))
        if path is None:
            raise RuntimeError(f"uncaptured day symbol: {symbol}")
        return Path(path)

    def day_price_divisor(self, symbol: str) -> float:
        return float(self._base_hub.day_price_divisor(symbol))

    def read_day_records(self, symbol: str, limit: int) -> list[dict[str, Any]]:
        if not isinstance(limit, int) or limit <= 0 or limit > DAY_INPUT_TAIL_RECORD_LIMIT:
            raise RuntimeError(f"invalid frozen day record limit: {limit}")
        path = self.day_path(symbol)
        node = self._nodes.get(str(path).casefold())
        if node is None:
            raise RuntimeError(f"uncaptured day path: {path}")
        if node.get("exists") is not True or node.get("valid_layout") is not True:
            return []
        raw = node.get("_raw")
        if not isinstance(raw, bytes) or len(raw) % DAY_RECORD_SIZE:
            raise RuntimeError(f"invalid frozen day bytes: {path}")
        selected = raw[-limit * DAY_RECORD_SIZE :]
        divisor = self.day_price_divisor(symbol)
        rows: list[dict[str, Any]] = []
        for offset in range(0, len(selected), DAY_RECORD_SIZE):
            chunk = selected[offset : offset + DAY_RECORD_SIZE]
            if len(chunk) != DAY_RECORD_SIZE:
                raise RuntimeError(f"short frozen day record: {path}")
            rows.append(self._base_hub.parse_day_record(chunk, divisor))
        return rows

    def read_lc5_records(self, symbol: str, limit: int) -> list[dict[str, Any]]:
        return self._base_hub.read_records(
            self._base_hub.lc5_path(symbol),
            self._base_hub.LC5_RECORD,
            self._base_hub.parse_lc5_record,
            limit,
        )


def capture_day_input_snapshot(
    hub,
    lookup_symbols: Iterable[str],
    run_id: str,
    cutoff: str,
    *,
    max_attempts: int = 3,
) -> tuple[FrozenDayHub, dict[str, Any]]:
    symbols = sorted(set(str(value) for value in lookup_symbols))
    if not symbols:
        raise RuntimeError("day input snapshot requires at least one symbol")
    last_reason = ""
    for attempt in range(1, max_attempts + 1):
        try:
            first_inputs, first_alias_paths = _capture_day_inputs(hub, symbols)
            second_inputs, second_alias_paths = _capture_day_inputs(hub, symbols)
            if _day_capture_signature(first_inputs, first_alias_paths) != _day_capture_signature(
                second_inputs, second_alias_paths
            ):
                raise DayInputUpdateRace(f"{TDX_DAY_UPDATE_RACE}:day_snapshot_passes_differ")
            inputs = second_inputs
            alias_paths = second_alias_paths
            break
        except DayInputUpdateRace as exc:
            last_reason = str(exc)
            if attempt >= max_attempts:
                raise
            time.sleep(0.2 * attempt)
    else:
        raise DayInputUpdateRace(f"{TDX_DAY_UPDATE_RACE}:{last_reason or 'capture_failed'}")
    public_inputs = _public_day_nodes(inputs)
    all_requested_symbols_mapped = sum(len(item["lookup_symbols"]) for item in public_inputs) == len(symbols)
    all_existing_layouts_valid = all(
        not item.get("exists") or item.get("valid_layout") is True for item in public_inputs
    )
    missing_inputs_explicit = all("exists" in item for item in public_inputs)
    complete = bool(all_requested_symbols_mapped and all_existing_layouts_valid and missing_inputs_explicit)
    manifest = {
        "schema": DAY_INPUT_SCHEMA,
        "binding_mode": DAY_INPUT_BINDING_MODE,
        "run_id": run_id,
        "cutoff_trade_date": cutoff,
        "tail_record_limit": DAY_INPUT_TAIL_RECORD_LIMIT,
        "stable_capture_passes": 2,
        "capture_attempt": attempt,
        "input_count": len(public_inputs),
        "alias_count": len(symbols),
        "existing_input_count": sum(bool(item.get("exists")) for item in public_inputs),
        "missing_input_count": sum(not bool(item.get("exists")) for item in public_inputs),
        "all_requested_symbols_mapped": all_requested_symbols_mapped,
        "all_existing_layouts_valid": all_existing_layouts_valid,
        "missing_inputs_explicit": missing_inputs_explicit,
        "complete": complete,
        "inputs": public_inputs,
    }
    return FrozenDayHub(hub, inputs, alias_paths), manifest


def build_day_input_manifest(hub, lookup_symbols: Iterable[str], run_id: str, cutoff: str) -> dict[str, Any]:
    _frozen_hub, manifest = capture_day_input_snapshot(hub, lookup_symbols, run_id, cutoff)
    return manifest


def validate_day_input_manifest_current(
    hub,
    manifest: dict[str, Any],
    *,
    expected_run_id: str | None = None,
    expected_cutoff: str | None = None,
    trusted_day_root: Path | None = None,
) -> tuple[bool, list[dict[str, Any]]]:
    raw_inputs = manifest.get("inputs")
    inputs = raw_inputs if isinstance(raw_inputs, list) else []
    diagnostics: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    all_aliases: list[str] = []
    existing_count = 0
    missing_count = 0
    trusted_root = (trusted_day_root or (TDX_ROOT / "vipdoc")).resolve()

    for index, raw_node in enumerate(inputs):
        node = raw_node if isinstance(raw_node, dict) else {}
        mismatches: list[str] = []
        aliases_raw = node.get("lookup_symbols")
        aliases = [str(alias) for alias in aliases_raw] if isinstance(aliases_raw, list) else []
        aliases_contract = bool(
            isinstance(aliases_raw, list)
            and aliases
            and all(isinstance(alias, str) and alias for alias in aliases_raw)
            and aliases == sorted(aliases)
            and len(aliases) == len(set(aliases))
        )
        if not aliases_contract:
            mismatches.append("lookup_symbols_contract")
        all_aliases.extend(aliases)

        path_text = node.get("path") if isinstance(node.get("path"), str) else ""
        path = Path(path_text) if path_text else None
        resolved_path = path.resolve() if path is not None else None
        key = str(resolved_path).casefold() if resolved_path is not None else ""
        unique = bool(key) and key not in seen_paths
        if key:
            seen_paths.add(key)
        if not unique:
            mismatches.append("path_unique")
        try:
            trusted_path = bool(
                resolved_path is not None
                and resolved_path.suffix.casefold() == ".day"
                and os.path.commonpath((str(resolved_path), str(trusted_root))).casefold()
                == str(trusted_root).casefold()
            )
        except (OSError, ValueError):
            trusted_path = False
        if not trusted_path:
            mismatches.append("trusted_tdx_root")

        exists = node.get("exists")
        valid_layout = node.get("valid_layout")
        if isinstance(exists, bool):
            existing_count += int(exists)
            missing_count += int(not exists)
        else:
            mismatches.append("exists_boolean")
        if not isinstance(valid_layout, bool):
            mismatches.append("valid_layout_boolean")

        node_contract = False
        if exists is True:
            file_size = node.get("file_size")
            mtime_ns = node.get("mtime_ns")
            tail_count = node.get("tail_record_count")
            tail_offset = node.get("tail_offset")
            tail_size = node.get("tail_size")
            tail_sha = node.get("tail_sha256")
            integer_fields = (file_size, mtime_ns, tail_count, tail_offset, tail_size)
            plain_integers = all(isinstance(value, int) and not isinstance(value, bool) for value in integer_fields)
            expected_records = (
                file_size // DAY_RECORD_SIZE
                if plain_integers and file_size > 0 and file_size % DAY_RECORD_SIZE == 0
                else -1
            )
            expected_tail_count = min(expected_records, DAY_INPUT_TAIL_RECORD_LIMIT) if expected_records >= 0 else -1
            node_contract = bool(
                valid_layout is True
                and plain_integers
                and mtime_ns >= 0
                and tail_count == expected_tail_count
                and tail_size == expected_tail_count * DAY_RECORD_SIZE
                and tail_offset == file_size - tail_size
                and isinstance(tail_sha, str)
                and re.fullmatch(r"[0-9a-f]{64}", tail_sha) is not None
            )
        elif exists is False:
            node_contract = valid_layout is False
        if not node_contract:
            mismatches.append("node_v2_fields")

        alias_routes: dict[str, str] = {}
        resolved_aliases_current = bool(aliases_contract and key)
        for alias in aliases:
            try:
                alias_path = Path(hub.day_path(alias)).resolve()
                alias_routes[alias] = str(alias_path)
                if str(alias_path).casefold() != key:
                    resolved_aliases_current = False
                    mismatches.append(f"alias_routing:{alias}")
            except (OSError, RuntimeError, TypeError, ValueError) as exc:
                resolved_aliases_current = False
                alias_routes[alias] = f"{type(exc).__name__}:{exc}"
                mismatches.append(f"alias_routing:{alias}")

        try:
            current_node = day_tail_meta(path, aliases) if path is not None else {"error": "missing path"}
            fields = (
                "lookup_symbols", "path", "exists", "valid_layout", "file_size", "mtime_ns",
                "tail_record_count", "tail_offset", "tail_size", "tail_sha256",
            )
            current = bool(
                path is not None
                and all(current_node.get(field) == node.get(field) for field in fields)
                and resolved_aliases_current
                and trusted_path
            )
            if not current:
                mismatches.append("current_values")
        except (OSError, RuntimeError, TypeError, ValueError, DayInputUpdateRace) as exc:
            current = False
            current_node = {"error": f"{type(exc).__name__}:{exc}", "alias_routes": alias_routes}
            mismatches.append("current_read_error")
        diagnostics.append({
            "index": index,
            "path": path_text,
            "lookup_symbols": aliases,
            "unique": unique,
            "trusted_tdx_root": trusted_path,
            "resolved_aliases_current": resolved_aliases_current,
            "contract": bool(isinstance(raw_node, dict) and aliases_contract and unique and trusted_path and node_contract),
            "current": current,
            "mismatches": mismatches,
            "expected": node,
            "actual": current_node,
        })

    run_id = manifest.get("run_id")
    cutoff = manifest.get("cutoff_trade_date")
    plain_capture_attempt = isinstance(manifest.get("capture_attempt"), int) and not isinstance(
        manifest.get("capture_attempt"), bool
    )
    plain_counts = all(
        isinstance(manifest.get(field), int) and not isinstance(manifest.get(field), bool)
        for field in ("input_count", "alias_count", "existing_input_count", "missing_input_count")
    )
    manifest_conditions = {
        "schema_v2": manifest.get("schema") == DAY_INPUT_SCHEMA,
        "binding_mode_exact": manifest.get("binding_mode") == DAY_INPUT_BINDING_MODE,
        "run_id_valid": isinstance(run_id, str) and bool(run_id) and (expected_run_id is None or run_id == expected_run_id),
        "cutoff_valid": isinstance(cutoff, str) and re.fullmatch(r"20\d{6}", cutoff) is not None
        and (expected_cutoff is None or cutoff == expected_cutoff),
        "tail_record_limit_260": manifest.get("tail_record_limit") == DAY_INPUT_TAIL_RECORD_LIMIT,
        "stable_capture_passes_2": manifest.get("stable_capture_passes") == 2,
        "capture_attempt_valid": plain_capture_attempt and manifest.get("capture_attempt") >= 1,
        "counts_exact": bool(
            plain_counts
            and manifest.get("input_count") == len(inputs)
            and manifest.get("alias_count") == len(all_aliases) == len(set(all_aliases))
            and manifest.get("existing_input_count") == existing_count
            and manifest.get("missing_input_count") == missing_count
        ),
        "all_requested_symbols_mapped": manifest.get("all_requested_symbols_mapped") is True,
        "all_existing_layouts_valid": manifest.get("all_existing_layouts_valid") is True,
        "missing_inputs_explicit": manifest.get("missing_inputs_explicit") is True,
        "complete": manifest.get("complete") is True,
        "inputs_nonempty": bool(inputs),
    }
    structure_ok = all(manifest_conditions.values())
    diagnostics.insert(0, {
        "index": None,
        "path": "<manifest>",
        "lookup_symbols": [],
        "unique": True,
        "trusted_tdx_root": True,
        "resolved_aliases_current": True,
        "contract": structure_ok,
        "current": True,
        "mismatches": [name for name, passed in manifest_conditions.items() if not passed],
        "expected": {"run_id": expected_run_id, "cutoff_trade_date": expected_cutoff},
        "actual": manifest_conditions,
    })
    node_diagnostics = diagnostics[1:]
    return bool(
        structure_ok
        and node_diagnostics
        and all(item["contract"] and item["current"] for item in node_diagnostics)
    ), diagnostics


def load_hub():
    spec = importlib.util.spec_from_file_location("tdx_hub_cb_scan", TDX_HUB)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {TDX_HUB}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_day_records(hub, symbol: str, limit: int) -> list[dict[str, Any]]:
    reader = getattr(hub, "read_day_records", None)
    if callable(reader):
        return reader(symbol, limit)
    return hub.read_records(hub.day_path(symbol), hub.DAY_RECORD, hub.parse_day_record, limit)


def decode_tnf_name(raw_field: bytes) -> str:
    if len(raw_field) != 16:
        raise ValueError(f"unexpected TNF name field width: {len(raw_field)}")
    raw = raw_field.split(b"\x00", 1)[0]
    try:
        return raw.decode("gb18030", errors="strict").strip()
    except UnicodeDecodeError as exc:
        if (
            len(raw) != len(raw_field)
            or exc.end != len(raw)
            or exc.reason != "incomplete multibyte sequence"
        ):
            raise ValueError("invalid GB18030 bytes inside TNF name field") from exc
        for drop_count in range(1, min(3, len(raw) - 1) + 1):
            try:
                return raw[:-drop_count].decode("gb18030", errors="strict").strip()
            except UnicodeDecodeError:
                continue
        raise ValueError("TNF name field has no valid prefix before truncated tail") from exc


def parse_tnf(path: Path) -> dict[str, str]:
    data = path.read_bytes()
    if len(data) < TNF_HEADER or (len(data) - TNF_HEADER) % TNF_RECORD:
        raise ValueError(f"unexpected TNF layout: {path}")
    result: dict[str, str] = {}
    for offset in range(TNF_HEADER, len(data), TNF_RECORD):
        row = data[offset : offset + TNF_RECORD]
        code = row[:6].decode("ascii", errors="strict").strip("\x00 ")
        if len(code) != 6 or not code.isdigit():
            continue
        name = decode_tnf_name(row[31:47])
        result[code] = name
    return result


def as_float(value: str | None) -> float | None:
    try:
        number = float(value or "")
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def parse_term_date(value: str | None, field_present: bool = True) -> dict[str, Any]:
    if not field_present:
        return {"raw": None, "status": "FIELD_ABSENT", "date": None}
    text = str(value or "").strip()
    if not text:
        return {"raw": text, "status": "MISSING", "date": None}
    if not re.fullmatch(r"20\d{6}", text):
        return {"raw": text, "status": "INVALID_FORMAT", "date": None}
    try:
        parsed = dt.datetime.strptime(text, "%Y%m%d").date()
    except ValueError:
        return {"raw": text, "status": "INVALID_CALENDAR", "date": None}
    return {"raw": text, "status": "VALID", "date": parsed}


def parse_date(value: str | None) -> dt.date | None:
    return parse_term_date(value).get("date")


def parse_bonds(cutoff: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]], dict[str, Any]]:
    tnf = {market: parse_tnf(path) for market, path in TNF_FILES.items()}
    cutoff_date = dt.datetime.strptime(cutoff, "%Y%m%d").date()
    bonds: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {
        "source_rows": 0,
        "accepted_rows": 0,
        "short_rows": 0,
        "unsupported_market_rows": 0,
        "invalid_or_unresolved_source_rows": 0,
        "explained_not_current_rows": 0,
        "master_current_candidate_rows": 0,
        "source_current_candidate_missing_tnf": [],
        "invalid_or_unresolved_sample": [],
        "explained_not_current_sample": [],
        "unsupported_market_sample": [],
        "duplicate_symbols": [],
    }
    seen_symbols: set[str] = set()
    with BOND_SOURCE.open("r", encoding="utf-8", newline="") as handle:
        for line_no, fields in enumerate(csv.reader(handle), 1):
            diagnostics["source_rows"] += 1
            if len(fields) < 13:
                diagnostics["short_rows"] += 1
                continue
            flag, code, underlying = fields[0].strip(), fields[1].strip(), fields[2].strip()
            market = MARKET_BY_FLAG.get(flag)
            if market is None:
                diagnostics["unsupported_market_rows"] += 1
                if len(diagnostics["unsupported_market_sample"]) < 25:
                    diagnostics["unsupported_market_sample"].append({"line": line_no, "flag": flag, "code": code})
                continue
            conv_price = as_float(fields[3])
            remaining_wan = as_float(fields[12])
            maturity = parse_term_date(fields[10], field_present=len(fields) > 10)
            last_trade = parse_term_date(fields[17] if len(fields) > 17 else None, field_present=len(fields) > 17)
            invalid_reasons: list[str] = []
            if not re.fullmatch(r"\d{6}", code):
                invalid_reasons.append("invalid_bond_code")
            if not re.fullmatch(r"\d{6}", underlying):
                invalid_reasons.append("invalid_underlying_code")
            if conv_price is None or conv_price <= 0:
                invalid_reasons.append("invalid_conversion_price")
            if remaining_wan is None or remaining_wan <= 0:
                invalid_reasons.append("invalid_remaining_scale")
            if maturity["status"] != "VALID":
                invalid_reasons.append(f"maturity_date_{str(maturity['status']).lower()}")
            if last_trade["status"] not in ("VALID", "MISSING"):
                invalid_reasons.append(f"known_last_trade_date_{str(last_trade['status']).lower()}")
            if maturity["date"] and last_trade["date"] and last_trade["date"] > maturity["date"]:
                invalid_reasons.append("known_last_trade_after_maturity")
            if invalid_reasons:
                diagnostics["invalid_or_unresolved_source_rows"] += 1
                if len(diagnostics["invalid_or_unresolved_sample"]) < 25:
                    diagnostics["invalid_or_unresolved_sample"].append({
                        "line": line_no,
                        "flag": flag,
                        "code": code,
                        "reasons": invalid_reasons,
                        "maturity_date": {key: value.isoformat() if isinstance(value, dt.date) else value for key, value in maturity.items()},
                        "known_last_trade_date": {key: value.isoformat() if isinstance(value, dt.date) else value for key, value in last_trade.items()},
                    })
                continue
            not_current_reasons: list[str] = []
            if maturity["date"] and maturity["date"] <= cutoff_date:
                not_current_reasons.append("matured_on_or_before_cutoff")
            if last_trade["date"] and last_trade["date"] <= cutoff_date:
                not_current_reasons.append("last_trade_on_or_before_cutoff")
            if not_current_reasons:
                diagnostics["explained_not_current_rows"] += 1
                if len(diagnostics["explained_not_current_sample"]) < 25:
                    diagnostics["explained_not_current_sample"].append({
                        "line": line_no,
                        "symbol": f"{code}.{market.upper()}",
                        "reasons": not_current_reasons,
                    })
                continue
            symbol = f"{code}.{market.upper()}"
            if symbol in seen_symbols:
                diagnostics["duplicate_symbols"].append(symbol)
                diagnostics["invalid_or_unresolved_source_rows"] += 1
                continue
            seen_symbols.add(symbol)
            underlying_market = "sh" if underlying.startswith(("5", "6", "9")) else "bj" if underlying.startswith(("4", "8")) else "sz"
            underlying_name = tnf.get(underlying_market, {}).get(underlying, "")
            tnf_confirmed = code in tnf[market]
            if not tnf_confirmed:
                diagnostics["source_current_candidate_missing_tnf"].append(symbol)
            bonds.append({
                "line": line_no,
                "market": market,
                "code": code,
                "symbol": symbol,
                "name": tnf[market].get(code, code),
                "tnf_confirmed": tnf_confirmed,
                "underlying": underlying,
                "underlying_symbol": f"{underlying}.{underlying_market.upper()}",
                "underlying_name": underlying_name or underlying,
                "conversion_price": conv_price,
                "remaining_wan": remaining_wan,
                "remaining_yi": remaining_wan / 10000.0,
                "maturity_date": str(maturity["raw"] or ""),
                "maturity_date_status": maturity["status"],
                "known_last_trade_date": str(last_trade["raw"] or ""),
                "known_last_trade_date_status": last_trade["status"],
                "known_last_trade_date_semantic": "not_announced" if last_trade["status"] == "MISSING" else "announced",
                "rating": fields[15].strip() if len(fields) > 15 else "",
            })
            diagnostics["accepted_rows"] += 1
            diagnostics["master_current_candidate_rows"] += 1
    diagnostics["classification_count"] = (
        diagnostics["short_rows"]
        + diagnostics["unsupported_market_rows"]
        + diagnostics["invalid_or_unresolved_source_rows"]
        + diagnostics["explained_not_current_rows"]
        + diagnostics["master_current_candidate_rows"]
    )
    diagnostics["classification_complete"] = diagnostics["classification_count"] == diagnostics["source_rows"]
    diagnostics["tnf_reconciliation_complete"] = not diagnostics["source_current_candidate_missing_tnf"]
    diagnostics["integrity_complete"] = (
        diagnostics["short_rows"] == 0
        and diagnostics["invalid_or_unresolved_source_rows"] == 0
        and not diagnostics["duplicate_symbols"]
        and diagnostics["classification_complete"]
    )
    return bonds, tnf, diagnostics


def ema(values: list[float], period: int) -> list[float]:
    alpha = 2.0 / (period + 1.0)
    out: list[float] = []
    for value in values:
        out.append(value if not out else alpha * value + (1.0 - alpha) * out[-1])
    return out


def recent_cross_dates(a: list[float], b: list[float], dates: list[str], lookback: int) -> list[str]:
    crosses = [dates[i] for i in range(1, len(dates)) if a[i] > b[i] and a[i - 1] <= b[i - 1]]
    allowed = set(dates[-lookback:])
    return [value for value in crosses if value in allowed]


def percentile_map(values: dict[str, float]) -> dict[str, float]:
    groups: dict[float, list[str]] = defaultdict(list)
    for key, value in values.items():
        groups[value].append(key)
    ordered = sorted(groups)
    total = len(values)
    result: dict[str, float] = {}
    position = 0
    for value in ordered:
        keys = groups[value]
        low, high = position, position + len(keys) - 1
        pct = 1.0 if total == 1 else ((low + high) / 2.0) / (total - 1)
        for key in keys:
            result[key] = pct
        position += len(keys)
    return result


def code7(code: str) -> str:
    flag = "1" if code.startswith(("5", "6", "9")) else "2" if code.startswith(("4", "8")) else "0"
    return flag + code


def suffix_symbol(code: str) -> str:
    market = "SH" if code.startswith(("5", "6", "9")) else "BJ" if code.startswith(("4", "8")) else "SZ"
    return f"{code}.{market}"


def benchmark_calendar(hub, cutoff: str) -> list[str]:
    rows = [row for row in read_day_records(hub, "999999.SH", 30) if row["date"] <= cutoff]
    dates = [str(row["date"]) for row in rows[-11:]]
    if len(dates) != 11 or dates[-1] != cutoff:
        raise RuntimeError(f"benchmark calendar unavailable for {cutoff}: {dates}")
    return dates


def stock_snapshot(hub, code: str, cutoff: str, calendar: list[str], cache: dict[str, dict[str, Any] | None]) -> dict[str, Any] | None:
    if code in cache:
        return cache[code]
    rows = [row for row in read_day_records(hub, code, 20) if row["date"] <= cutoff]
    if len(rows) < 11 or [str(row["date"]) for row in rows[-11:]] != calendar or float(rows[-6]["close"]) <= 0 or float(rows[-2]["close"]) <= 0:
        cache[code] = None
        return None
    previous_volumes = [float(row["volume"]) for row in rows[-6:-1] if float(row["volume"]) > 0]
    previous_amounts = [float(row["amount"]) for row in rows[-6:-1] if float(row["amount"]) > 0]
    if not previous_volumes or not previous_amounts:
        cache[code] = None
        return None
    latest = rows[-1]
    close = float(latest["close"])
    ret1 = close / float(rows[-2]["close"]) - 1.0
    ret5 = close / float(rows[-6]["close"]) - 1.0
    threshold = 0.295 if code.startswith(("4", "8")) else 0.195 if code.startswith(("300", "301", "688")) else 0.095
    snap = {
        "date": str(latest["date"]),
        "return_1d": ret1,
        "return_5d": ret5,
        "is_up_1d": ret1 > 0,
        "is_up_5d": ret5 > 0,
        "is_limit_up": ret1 >= threshold,
        "volume_ratio_5d": float(latest["volume"]) / statistics.fmean(previous_volumes),
        "amount_ratio_5d": float(latest["amount"]) / statistics.fmean(previous_amounts),
        "sum_amount_last5": sum(float(row["amount"]) for row in rows[-5:]),
        "sum_amount_prev5": sum(float(row["amount"]) for row in rows[-10:-5]),
        "amount_active_ratio_5d": (sum(float(row["amount"]) for row in rows[-5:]) / sum(float(row["amount"]) for row in rows[-10:-5])) if sum(float(row["amount"]) for row in rows[-10:-5]) > 0 else 0.0,
        "above_ma5": close > statistics.fmean(float(row["close"]) for row in rows[-5:]),
    }
    cache[code] = snap
    return snap


def preload_stock_snapshots(
    hub,
    codes: Iterable[str],
    cutoff: str,
    calendar: list[str],
    cache: dict[str, dict[str, Any] | None],
) -> None:
    pending = sorted(set(str(code) for code in codes) - set(cache))
    if not pending:
        return

    def load_one(code: str) -> tuple[str, dict[str, Any] | None]:
        return code, stock_snapshot(hub, code, cutoff, calendar, {})

    with ThreadPoolExecutor(max_workers=min(MARKET_SNAPSHOT_WORKERS, len(pending))) as executor:
        for code, snapshot in executor.map(load_one, pending):
            cache[code] = snapshot


def parse_industry_inputs() -> tuple[dict[str, str], dict[str, list[str]], dict[str, str]]:
    stock_industry: dict[str, str] = {}
    members: dict[str, list[str]] = defaultdict(list)
    for line in TDXHY.read_text(encoding="gb18030", errors="strict").splitlines():
        fields = line.split("|")
        if len(fields) < 3 or not re.fullmatch(r"[012]\|?", fields[0]) or not re.fullmatch(r"\d{6}", fields[1]):
            continue
        industry_code = fields[2].strip()
        if not industry_code.startswith("T"):
            continue
        key = fields[0] + fields[1]
        stock_industry[key] = industry_code
        members[industry_code].append(fields[1])
    industry_names: dict[str, str] = {}
    for line in TDXZS.read_text(encoding="gb18030", errors="strict").splitlines():
        fields = line.split("|")
        if len(fields) >= 6 and fields[-1].startswith("T"):
            industry_names[fields[-1].strip()] = fields[0].strip()
    return stock_industry, dict(members), industry_names


def build_industry_heat(
    hub,
    cutoff: str,
    calendar: list[str],
    cache: dict[str, dict[str, Any] | None],
    parsed_inputs: tuple[dict[str, str], dict[str, list[str]], dict[str, str]] | None = None,
) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    stock_industry, members, industry_names = parsed_inputs or parse_industry_inputs()
    preload_stock_snapshots(hub, (code for codes in members.values() for code in codes), cutoff, calendar, cache)
    rows: dict[str, dict[str, Any]] = {}
    for industry_code, codes in members.items():
        snapshots = [item for code in codes if (item := stock_snapshot(hub, code, cutoff, calendar, cache)) and item["date"] == cutoff]
        coverage_ratio = len(snapshots) / len(codes) if codes else 0.0
        if len(snapshots) < 10 or coverage_ratio < 0.70:
            continue
        rows[industry_code] = {
            "industry_code": industry_code,
            "industry_name": industry_names.get(industry_code, industry_code),
            "member_count": len(codes),
            "coverage_count": len(snapshots),
            "coverage_ratio": coverage_ratio,
            "median_return_5d": statistics.median(float(item["return_5d"]) for item in snapshots),
            "up_ratio_5d": sum(bool(item["is_up_5d"]) for item in snapshots) / len(snapshots),
            "median_amount_active_ratio_5d": statistics.median(float(item["amount_active_ratio_5d"]) for item in snapshots),
            "above_ma5_ratio": sum(bool(item["above_ma5"]) for item in snapshots) / len(snapshots),
        }
    fields = ("median_return_5d", "up_ratio_5d", "median_amount_active_ratio_5d", "above_ma5_ratio")
    weights = {"median_return_5d": 0.35, "up_ratio_5d": 0.25, "median_amount_active_ratio_5d": 0.20, "above_ma5_ratio": 0.20}
    for field in fields:
        pcts = percentile_map({key: float(value[field]) for key, value in rows.items()})
        for key, value in rows.items():
            value.setdefault("percentiles", {})[field] = pcts[key]
    for value in rows.values():
        value["heat_score"] = 100.0 * sum(weights[field] * float(value["percentiles"][field]) for field in fields)
    return stock_industry, rows


def parse_concepts() -> list[dict[str, Any]]:
    text = INFOHARBOR.read_bytes().decode("gb18030", errors="strict")
    concepts: list[dict[str, Any]] = []
    current_name = ""
    current_codes: list[str] = []

    def flush() -> None:
        if not current_name.startswith("GN_"):
            return
        codes = list(dict.fromkeys(value for value in current_codes if value[1:].startswith(EQUITY_PREFIXES)))
        if codes:
            concepts.append({"name": current_name[3:], "source_name": current_name, "codes": codes})

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            flush()
            current_name = line[1:].split(",", 1)[0].strip()
            current_codes = []
            continue
        for token in line.split(","):
            match = re.fullmatch(r"([0123])#(\d{6})", token.strip())
            if match:
                current_codes.append(match.group(1) + match.group(2))
    flush()
    return concepts


def build_concept_heat(
    hub,
    cutoff: str,
    calendar: list[str],
    cache: dict[str, dict[str, Any] | None],
    concepts: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    concepts = concepts if concepts is not None else parse_concepts()
    preload_stock_snapshots(
        hub,
        (item_code[1:] for concept in concepts for item_code in concept["codes"]),
        cutoff,
        calendar,
        cache,
    )
    sectors: list[dict[str, Any]] = []
    for concept in concepts:
        snapshots = [item for item_code in concept["codes"] if (item := stock_snapshot(hub, item_code[1:], cutoff, calendar, cache)) and item["date"] == cutoff]
        coverage = len(snapshots)
        if coverage < 3 or coverage / len(concept["codes"]) < 0.5:
            continue
        sectors.append({
            **concept,
            "member_count": len(concept["codes"]),
            "coverage_count": coverage,
            "mean_return_1d": statistics.fmean(float(item["return_1d"]) for item in snapshots),
            "median_return_1d": statistics.median(float(item["return_1d"]) for item in snapshots),
            "mean_return_5d": statistics.fmean(float(item["return_5d"]) for item in snapshots),
            "median_return_5d": statistics.median(float(item["return_5d"]) for item in snapshots),
            "up_ratio": sum(bool(item["is_up_1d"]) for item in snapshots) / coverage,
            "up_ratio_5d": sum(bool(item["is_up_5d"]) for item in snapshots) / coverage,
            "limit_up_ratio": sum(bool(item["is_limit_up"]) for item in snapshots) / coverage,
            "median_volume_ratio_5d": statistics.median(float(item["volume_ratio_5d"]) for item in snapshots),
            "median_amount_ratio_5d": statistics.median(float(item["amount_ratio_5d"]) for item in snapshots),
        })
    score_fields = (
        "mean_return_1d", "median_return_1d", "mean_return_5d", "median_return_5d", "up_ratio", "up_ratio_5d",
        "limit_up_ratio", "median_volume_ratio_5d", "median_amount_ratio_5d",
    )
    for field in score_fields:
        pcts = percentile_map({item["source_name"]: float(item[field]) for item in sectors})
        for item in sectors:
            item.setdefault("percentiles", {})[field] = pcts[item["source_name"]]
    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in sectors:
        item["heat_score"] = 100.0 * statistics.fmean(item["percentiles"].values())
        if any(marker in item["name"] for marker in NON_DIRECTION_MARKERS):
            continue
        compact = {key: item[key] for key in ("name", "source_name", "member_count", "coverage_count", "heat_score", "mean_return_1d", "mean_return_5d", "median_return_5d", "up_ratio", "up_ratio_5d", "limit_up_ratio")}
        for member in item["codes"]:
            by_code[member].append(compact)
    for values in by_code.values():
        values.sort(key=lambda item: (-float(item["heat_score"]), item["name"]))
    sectors.sort(key=lambda item: (-float(item["heat_score"]), item["name"]))
    return by_code, sectors


def normalize_series(raw: Any, cutoff: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return result
    for index, item in enumerate(raw):
        if isinstance(item, dict):
            date = str(item.get("Date") or "")
            value = as_float(str(item.get("Value")))
        else:
            date = ""
            value = as_float(str(item))
        if value is not None and (not date or date <= cutoff):
            result.append({"date": date or f"index-{index}", "value": value})
    return result


def validate_exact_formula_window(raw: Any, cutoff: str, required_dates: list[str]) -> dict[str, Any]:
    reasons: list[str] = []
    parsed: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return {
            "complete": False,
            "reasons": ["series_not_list"],
            "required_dates": list(required_dates),
            "actual_dates": [],
            "actual_tail_dates": [],
            "point_count": 0,
            "values": {},
        }
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            reasons.append(f"item_{index}_not_object")
            continue
        date = str(item.get("Date") or "")
        value = as_float(str(item.get("Value")))
        if not re.fullmatch(r"20\d{6}", date):
            reasons.append(f"item_{index}_invalid_date")
            continue
        try:
            dt.datetime.strptime(date, "%Y%m%d")
        except ValueError:
            reasons.append(f"item_{index}_invalid_calendar_date")
            continue
        if value is None:
            reasons.append(f"item_{index}_invalid_value")
            continue
        parsed.append({"date": date, "value": value})
        if date > cutoff:
            reasons.append(f"item_{index}_date_after_cutoff")
    dates = [item["date"] for item in parsed]
    if len(set(dates)) != len(dates):
        reasons.append("duplicate_dates")
    if dates != sorted(dates):
        reasons.append("dates_not_strictly_ascending")
    actual_tail_dates = dates[-len(required_dates):] if required_dates else []
    if dates != list(required_dates):
        reasons.append("dates_not_exact_benchmark_window")
    values = {item["date"]: item["value"] for item in parsed if item["date"] in set(required_dates)}
    return {
        "complete": not reasons,
        "reasons": reasons,
        "required_dates": list(required_dates),
        "actual_dates": dates,
        "actual_tail_dates": actual_tail_dates,
        "point_count": len(parsed),
        "values": values,
    }


def formula_field_coverage(
    nodes: dict[str, Any],
    symbols: list[str],
    fields: tuple[str, ...],
    cutoff: str,
    min_points: int,
    require_all_fields: bool = True,
    required_dates: list[str] | None = None,
) -> dict[str, Any]:
    invalid: list[dict[str, Any]] = []
    complete_count = 0
    for symbol in symbols:
        node = nodes.get(symbol)
        reasons: list[str] = []
        if not isinstance(node, dict):
            reasons.append("node_missing")
        else:
            present_fields = 0
            for field in fields:
                raw = node.get(field)
                series = normalize_series(raw, cutoff)
                if not series and not require_all_fields:
                    continue
                present_fields += int(bool(series))
                if required_dates is not None:
                    exact = validate_exact_formula_window(raw, cutoff, required_dates)
                    if not exact["complete"]:
                        reasons.extend(f"{field}:{reason}" for reason in exact["reasons"])
                elif len(series) < min_points:
                    reasons.append(f"{field}:points<{min_points}")
                elif str(series[-1].get("date")) != cutoff:
                    reasons.append(f"{field}:latest_date={series[-1].get('date')}")
            if not require_all_fields and present_fields == 0:
                reasons.append("all_required_fields_missing")
        if reasons:
            if len(invalid) < 25:
                invalid.append({"symbol": symbol, "reasons": reasons})
        else:
            complete_count += 1
    return {
        "expected_count": len(symbols),
        "complete_count": complete_count,
        "invalid_count": len(symbols) - complete_count,
        "invalid_sample": invalid,
        "complete": complete_count == len(symbols),
        "required_fields": list(fields),
        "minimum_points": min_points,
        "require_all_fields": require_all_fields,
        "required_latest_date": cutoff,
        "required_dates": list(required_dates) if required_dates is not None else None,
    }


def compact_formula_nodes(nodes: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for symbol, node in nodes.items():
        if isinstance(node, dict):
            compact[symbol] = {field: node.get(field) for field in fields}
    return compact


def merge_formula_batches(
    tq,
    formula: str,
    symbols: list[str],
    cutoff: str,
    return_count: int,
    dividend_type: int,
    formula_arg: str | None = None,
    chunk_size: int = TQ_BATCH_SIZE,
    history_count: int = 0,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    merged: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    for start in range(0, len(symbols), chunk_size):
        batch = symbols[start : start + chunk_size]
        kwargs: dict[str, Any] = {
            "stock_list": batch,
            "count": history_count,
            "return_count": return_count,
            "return_date": True,
            "end_time": cutoff,
            "dividend_type": dividend_type,
        }
        if formula_arg is not None:
            kwargs["formula_arg"] = formula_arg
        try:
            payload = tq.formula_process_mul_zb(formula, **kwargs)
            error_id = str(payload.get("ErrorId", "")) if isinstance(payload, dict) else "not-dict"
            if not isinstance(payload, dict) or error_id not in ("", "0"):
                errors.append({"formula": formula, "start": start, "size": len(batch), "error_id": error_id})
                continue
            for symbol in batch:
                node = payload.get(symbol)
                if isinstance(node, dict):
                    merged[symbol] = node
        except Exception as exc:
            errors.append({"formula": formula, "start": start, "size": len(batch), "error": f"{type(exc).__name__}:{exc}"})
    return merged, errors


def require_tdx_client() -> None:
    if os.name != "nt":
        return
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq TdxW.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"tdx_client_probe_failed:{type(exc).__name__}:{exc}") from exc
    if result.returncode != 0:
        detail = " ".join((result.stderr or result.stdout or "").split())[-500:]
        raise RuntimeError(f"tdx_client_probe_failed:exit={result.returncode}:{detail}")
    if "tdxw.exe" not in result.stdout.lower():
        raise RuntimeError("tdx_client_not_running:TdxW.exe")


def load_tq():
    require_tdx_client()
    if not TQ_RUNTIME.is_file():
        raise RuntimeError(f"tq_runtime_missing:{TQ_RUNTIME}")
    user_dir = TDX_ROOT / "PYPlugins" / "user"
    if str(user_dir) not in sys.path:
        sys.path.insert(0, str(user_dir))
    sys.argv = ["tqcenter", "--run_tdx", "0"]
    from tqcenter import tq  # type: ignore

    try:
        # TQ requires a stable strategy file identity, not the Tongdaxin root directory.
        tq.initialize(str(TQ_STRATEGY_PATH))
    except Exception as exc:
        raise RuntimeError(
            f"tq_initialize_failed:strategy_path={TQ_STRATEGY_PATH}:{type(exc).__name__}:{exc}"
        ) from exc
    return tq


def eval_feilong(node: dict[str, Any] | None, cutoff: str) -> dict[str, Any]:
    wave = normalize_series((node or {}).get("波"), cutoff)
    segment = normalize_series((node or {}).get("段"), cutoff)
    w = {item["date"]: item["value"] for item in wave}
    s = {item["date"]: item["value"] for item in segment}
    dates = sorted(set(w) & set(s))
    crosses: list[dict[str, Any]] = []
    score_crosses: list[dict[str, Any]] = []
    recent = set(dates[-5:])
    score_recent = set(dates[-10:])
    for index in range(1, len(dates)):
        date, prev = dates[index], dates[index - 1]
        if date in score_recent and w[date] > s[date] and w[prev] <= s[prev]:
            cross = {
                "date": date,
                "wave": w[date],
                "segment": s[date],
                "prev_wave": w[prev],
                "prev_segment": s[prev],
                "below20": w[date] < 20 and s[date] < 20,
            }
            score_crosses.append(cross)
            if date in recent and cross["below20"]:
                crosses.append(cross)
    return {
        "pass": bool(crosses),
        "recent_crosses": crosses,
        "score_window_crosses": score_crosses,
        "latest_date": dates[-1] if dates else None,
        "latest_wave": w[dates[-1]] if dates else None,
        "latest_segment": s[dates[-1]] if dates else None,
        "point_count": len(dates),
    }


def eval_scr(
    node90: dict[str, Any] | None,
    node70: dict[str, Any] | None,
    cutoff: str,
    required_dates: list[str],
) -> dict[str, Any]:
    check90 = validate_exact_formula_window((node90 or {}).get("SCR"), cutoff, required_dates)
    check70 = validate_exact_formula_window((node70 or {}).get("SCR"), cutoff, required_dates)
    if not check90["complete"] or not check70["complete"]:
        return {
            "pass90": False,
            "pass70": False,
            "window_complete": False,
            "required_dates": list(required_dates),
            "scr90_window_check": check90,
            "scr70_window_check": check70,
            "reason": "exact_benchmark_window_unavailable",
        }
    old_date, previous_date, new_date = required_dates[0], required_dates[-2], required_dates[-1]
    v90 = check90["values"]
    v70 = check70["values"]
    shrink90 = v90[old_date] - v90[new_date]
    shrink70 = v70[old_date] - v70[new_date]
    relative_shrink90 = shrink90 / v90[old_date] if v90[old_date] > 0 else None
    return {
        "pass90": shrink90 >= 10.0 and relative_shrink90 is not None and relative_shrink90 >= (1.0 / 3.0),
        "pass70": shrink70 >= 3.0,
        "window_complete": True,
        "required_dates": list(required_dates),
        "old_date": old_date,
        "previous_date": previous_date,
        "latest_date": new_date,
        "scr90_old": v90[old_date],
        "scr90_previous": v90[previous_date],
        "scr90_latest": v90[new_date],
        "scr90_change_1d_pp": v90[new_date] - v90[previous_date],
        "shrink90_pp": shrink90,
        "relative_shrink90": relative_shrink90,
        "scr70_old": v70[old_date],
        "scr70_latest": v70[new_date],
        "shrink70_pp": shrink70,
        "point_count": len(required_dates),
    }


def formula_triggered(node: dict[str, Any] | None, cutoff: str) -> tuple[bool, list[dict[str, Any]]]:
    hits: list[dict[str, Any]] = []
    for field in ("OUTPUT59", "OUTPUT60", "OUTPUT61"):
        series = normalize_series((node or {}).get(field), cutoff)
        for item in series[-5:]:
            if float(item["value"]) > 0:
                hits.append({"field": field, **item})
    return bool(hits), hits


def detect_bottom_patterns(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def price(row: dict[str, Any], field: str) -> float:
        return float(row.get(field, row.get("close", 0.0)))

    flags = {"bullish_engulfing": False, "morning_star": False, "piercing_pattern": False, "double_bottom": False}
    if len(rows) >= 2:
        previous, latest = rows[-2], rows[-1]
        po, pc = price(previous, "open"), price(previous, "close")
        lo, lc = price(latest, "open"), price(latest, "close")
        flags["bullish_engulfing"] = pc < po and lc > lo and lo <= pc and lc >= po
        flags["piercing_pattern"] = pc < po and lc > lo and lo < pc and (po + pc) / 2.0 < lc < po
    if len(rows) >= 3:
        first, middle, latest = rows[-3], rows[-2], rows[-1]
        fo, fc = price(first, "open"), price(first, "close")
        mo, mc = price(middle, "open"), price(middle, "close")
        lo, lc = price(latest, "open"), price(latest, "close")
        first_body = abs(fo - fc)
        first_range = max(price(first, "high") - price(first, "low"), 1e-12)
        flags["morning_star"] = (
            fc < fo and first_body >= 0.5 * first_range
            and abs(mo - mc) <= 0.4 * first_body
            and lc > lo and lc >= (fo + fc) / 2.0
        )
    window = rows[-20:]
    if len(window) >= 10:
        lows = [price(row, "low") for row in window]
        candidates = sorted(range(len(lows)), key=lambda index: lows[index])
        for first_index in candidates:
            for second_index in candidates:
                if second_index - first_index < 3:
                    continue
                first_low, second_low = lows[first_index], lows[second_index]
                if min(first_low, second_low) <= 0:
                    continue
                similar = abs(first_low - second_low) / min(first_low, second_low) <= 0.03
                rebound = max(price(row, "high") for row in window[first_index : second_index + 1])
                if similar and rebound >= 1.05 * max(first_low, second_low):
                    flags["double_bottom"] = True
                    break
            if flags["double_bottom"]:
                break
    return {"flags": flags, "matches": [name for name, matched in flags.items() if matched]}


def analyze_intraday(hub, symbol: str, cutoff: str) -> dict[str, Any]:
    missing = {
        "intraday_status": "MISSING",
        "intraday_date": None,
        "intraday_point_count": 0,
        "intraday_close_position": None,
        "intraday_vwap": None,
        "intraday_close_vs_vwap": None,
        "intraday_afternoon_hold_ratio": None,
        "intraday_max_drawdown_pct": None,
    }
    reader = getattr(hub, "read_lc5_records", None)
    if not callable(reader):
        return missing
    try:
        rows = list(reader(symbol, 240))
    except (OSError, RuntimeError, ValueError):
        return missing
    session = [row for row in rows if str(row.get("date") or "").replace("-", "") == cutoff]
    if len(session) < 12:
        return {**missing, "intraday_point_count": len(session)}
    closes = [float(row["close"]) for row in session]
    highs = [float(row["high"]) for row in session]
    lows = [float(row["low"]) for row in session]
    session_high, session_low, latest_close = max(highs), min(lows), closes[-1]
    close_position = 0.5 if session_high <= session_low else (latest_close - session_low) / (session_high - session_low)
    total_volume = sum(max(0.0, float(row.get("volume") or 0.0)) for row in session)
    total_amount = sum(max(0.0, float(row.get("amount") or 0.0)) for row in session)
    vwap = None
    if total_volume > 0 and total_amount > 0:
        raw = total_amount / total_volume
        vwap = min((raw, raw / 10.0, raw / 100.0), key=lambda value: abs(value - latest_close))
    afternoon = [float(row["close"]) for row in session if str(row.get("time") or "") >= "13:00:00"]
    hold_ratio = (
        sum(value >= float(vwap) for value in afternoon) / len(afternoon)
        if afternoon and vwap is not None
        else None
    )
    peak = closes[0]
    max_drawdown = 0.0
    for value in closes:
        peak = max(peak, value)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - value) / peak * 100.0)
    if vwap is None or hold_ratio is None:
        status = "MISSING"
    elif close_position >= 0.65 and latest_close >= vwap and hold_ratio >= 0.60 and max_drawdown <= 3.0:
        status = "STRONG"
    elif close_position <= 0.35 or latest_close < 0.99 * vwap or hold_ratio < 0.40 or max_drawdown > 5.0:
        status = "WEAK"
    else:
        status = "NEUTRAL"
    return {
        "intraday_status": status,
        "intraday_date": cutoff,
        "intraday_point_count": len(session),
        "intraday_close_position": close_position,
        "intraday_vwap": vwap,
        "intraday_close_vs_vwap": (latest_close / vwap - 1.0) * 100.0 if vwap else None,
        "intraday_afternoon_hold_ratio": hold_ratio,
        "intraday_max_drawdown_pct": max_drawdown,
    }


def analyze_local(
    hub,
    bond: dict[str, Any],
    cutoff: str,
    calendar: list[str],
) -> tuple[dict[str, Any] | None, str | None]:
    bond_rows = [row for row in read_day_records(hub, bond["symbol"], 260) if row["date"] <= cutoff]
    stock_rows = [row for row in read_day_records(hub, bond["underlying_symbol"], 260) if row["date"] <= cutoff]
    bond_latest_date = str(bond_rows[-1]["date"]) if bond_rows else None
    stock_latest_date = str(stock_rows[-1]["date"]) if stock_rows else None
    bond_current = bond_latest_date == cutoff
    stock_current = stock_latest_date == cutoff
    bond_two_session_window = (
        len(bond_rows) >= 2
        and [str(row["date"]) for row in bond_rows[-2:]] == calendar[-2:]
    )
    bond_full_lookback = (
        len(bond_rows) >= 6
        and [str(row["date"]) for row in bond_rows[-6:]] == calendar[-6:]
        and float(bond_rows[-6]["close"]) > 0
    )
    bond_turnover_lookback = (
        len(bond_rows) >= 5
        and [str(row["date"]) for row in bond_rows[-5:]] == calendar[-5:]
    )
    stock_signal_available = (
        len(stock_rows) >= 30
        and [str(row["date"]) for row in stock_rows[-6:]] == calendar[-6:]
        and float(stock_rows[-1]["close"]) > 0
    )
    bond_close = float(bond_rows[-1]["close"]) if bond_rows else None
    stock_close = float(stock_rows[-1]["close"]) if stock_rows else None
    conversion_value = (
        stock_close / float(bond["conversion_price"]) * 100.0
        if stock_current and stock_close is not None
        else None
    )
    premium = (
        (bond_close / conversion_value - 1.0) * 100.0
        if bond_current and bond_close is not None and conversion_value is not None and conversion_value > 0
        else None
    )
    weekly_return = (
        (float(bond_close) / float(bond_rows[-6]["close"]) - 1.0) * 100.0
        if bond_full_lookback and bond_close is not None
        else None
    )
    daily_return = (
        (float(bond_close) / float(bond_rows[-2]["close"]) - 1.0) * 100.0
        if bond_two_session_window and bond_close is not None and float(bond_rows[-2]["close"]) > 0
        else None
    )
    previous_five_mean_volume = (
        statistics.mean(float(row["volume"]) for row in bond_rows[-6:-1])
        if bond_full_lookback
        else None
    )
    bond_volume_ratio_5d = (
        float(bond_rows[-1]["volume"]) / previous_five_mean_volume
        if previous_five_mean_volume is not None and previous_five_mean_volume > 0
        else None
    )
    turnover5 = (
        sum(float(row["volume"]) for row in bond_rows[-5:]) / (float(bond["remaining_wan"]) * 10.0) * 100.0
        if bond_turnover_lookback
        else None
    )
    volume_structure_available = (
        len(bond_rows) >= 10
        and [str(row["date"]) for row in bond_rows[-10:]] == calendar[-10:]
    )
    recent_mean_volume = previous_period_mean_volume = volume_expansion_ratio = None
    recent_volume_cv = max_daily_volume_share = None
    uniform_volume_expansion = healthy_volume_contraction = sudden_abnormal_volume_contraction = False
    if volume_structure_available:
        recent_volumes = [float(row["volume"]) for row in bond_rows[-5:]]
        previous_period_volumes = [float(row["volume"]) for row in bond_rows[-10:-5]]
        recent_mean_volume = statistics.mean(recent_volumes)
        previous_period_mean_volume = statistics.mean(previous_period_volumes)
        volume_expansion_ratio = (
            recent_mean_volume / previous_period_mean_volume if previous_period_mean_volume > 0 else None
        )
        recent_volume_cv = (
            statistics.pstdev(recent_volumes) / recent_mean_volume if recent_mean_volume > 0 else None
        )
        recent_volume_sum = sum(recent_volumes)
        max_daily_volume_share = max(recent_volumes) / recent_volume_sum if recent_volume_sum > 0 else None
        uniform_volume_expansion = bool(
            volume_expansion_ratio is not None and volume_expansion_ratio >= 1.20
            and recent_volume_cv is not None and recent_volume_cv <= 0.65
            and max_daily_volume_share is not None and max_daily_volume_share <= 0.35
        )
        prior_four_mean = statistics.mean(recent_volumes[:-1])
        healthy_volume_contraction = bool(
            uniform_volume_expansion and recent_volumes[-1] < recent_volumes[-2]
            and recent_volumes[-1] >= 0.50 * prior_four_mean
        )
        sudden_abnormal_volume_contraction = bool(
            uniform_volume_expansion and recent_volumes[-1] < 0.50 * prior_four_mean
        )
    volume_structure_pass = uniform_volume_expansion and not sudden_abnormal_volume_contraction
    bottom_patterns = detect_bottom_patterns(bond_rows)
    intraday = analyze_intraday(hub, bond["symbol"], cutoff)

    stock_closes = [float(row["close"]) for row in stock_rows]
    stock_dates = [str(row["date"]) for row in stock_rows]
    if stock_signal_available:
        ema3, ema21 = ema(stock_closes, 3), ema(stock_closes, 21)
        benchmark_dates_10 = set(calendar[-10:])
        ignition_crosses_10 = [
            date
            for date in recent_cross_dates(ema3, ema21, stock_dates, 10)
            if date in benchmark_dates_10
        ]
        ignition_crosses = [date for date in ignition_crosses_10 if date in set(stock_dates[-5:])]
        ema5, ema20 = ema(stock_closes, 5), ema(stock_closes, 20)
        ma5_latest = statistics.mean(stock_closes[-5:])
        ma10_latest = statistics.mean(stock_closes[-10:])
        ma20_latest = statistics.mean(stock_closes[-20:])
        stock_return5 = (stock_closes[-1] / stock_closes[-6] - 1.0) * 100.0
        stock_ema_bullish = ema3[-1] > ema21[-1]
        stock_ma_bullish = ma5_latest > ma10_latest > ma20_latest
        underlying_trend_score = (
            0.40 * clip(stock_return5 / 5.0)
            + 0.30 * float(stock_ema_bullish)
            + 0.30 * float(stock_ma_bullish)
        )
        aaa = [a - b for a, b in zip(ema(stock_closes, 5), ema(stock_closes, 30))]
        ddd = ema(aaa, 5)
        buy = [(a - d) * 2.0 for a, d in zip(aaa, ddd)]
        buy_crosses_5 = recent_cross_dates(buy, [0.0] * len(buy), stock_dates, 5)
        buy_crosses = [date for date in buy_crosses_5 if date in set(stock_dates[-3:])]
        youzi_pass = bool(buy_crosses_5) and buy[-1] > 0 and buy[-1] >= buy[-2]
        ema3_latest, ema21_latest = ema3[-1], ema21[-1]
        ema5_latest, ema20_latest = ema5[-1], ema20[-1]
        buy_latest, buy_prev = buy[-1], buy[-2]
        big_bull_red = ema5_latest > ema20_latest
    else:
        ignition_crosses_10 = []
        ignition_crosses = []
        buy_crosses_5 = []
        buy_crosses = []
        youzi_pass = False
        ema3_latest = ema21_latest = None
        ema5_latest = ema20_latest = None
        buy_latest = buy_prev = None
        big_bull_red = False
        ma5_latest = ma10_latest = ma20_latest = None
        stock_return5 = None
        stock_ema_bullish = stock_ma_bullish = False
        underlying_trend_score = None

    today = dt.datetime.strptime(cutoff, "%Y%m%d").date()
    maturity_declared_status = str(bond.get("maturity_date_status") or "")
    last_trade_declared_status = str(bond.get("known_last_trade_date_status") or "")
    maturity_info = parse_term_date(
        bond.get("maturity_date"),
        field_present=maturity_declared_status != "FIELD_ABSENT",
    )
    last_trade_info = parse_term_date(
        bond.get("known_last_trade_date"),
        field_present=last_trade_declared_status != "FIELD_ABSENT",
    )
    maturity = maturity_info["date"]
    last_trade = last_trade_info["date"]
    risks: list[str] = []
    if not bond.get("tnf_confirmed", False):
        risks.append("source_current_candidate_missing_tnf")
    if not bond_rows:
        risks.append("bond_history_missing")
    elif not bond_current:
        risks.append(f"bond_latest_date_mismatch:{bond_latest_date}:{cutoff}")
    if bond_rows and len(bond_rows) < 6:
        risks.append(f"insufficient_bond_history_lt_6:{len(bond_rows)}")
    elif bond_rows and not bond_full_lookback:
        risks.append("bond_last_6_sessions_mismatch")
    if not stock_rows:
        risks.append("underlying_history_missing")
    elif not stock_signal_available:
        risks.append(f"underlying_signal_history_unavailable:{len(stock_rows)}:{stock_latest_date}")
    if maturity_declared_status and maturity_declared_status != maturity_info["status"]:
        risks.append("maturity_date_status_mismatch")
    if last_trade_declared_status and last_trade_declared_status != last_trade_info["status"]:
        risks.append("known_last_trade_date_status_mismatch")
    if maturity_info["status"] != "VALID":
        risks.append(f"maturity_date_{str(maturity_info['status']).lower()}")
    if last_trade_info["status"] not in ("VALID", "MISSING"):
        risks.append(f"known_last_trade_date_{str(last_trade_info['status']).lower()}")
    if maturity and last_trade and last_trade > maturity:
        risks.append("known_last_trade_after_maturity")
    if maturity and (maturity - today).days <= 60:
        risks.append(f"maturity_within_60d:{maturity.isoformat()}")
    if last_trade and (last_trade - today).days <= 20:
        risks.append(f"known_last_trade_within_20d:{last_trade.isoformat()}")
    if "退" in str(bond["name"]):
        risks.append("bond_name_delisting_marker")
    if "ST" in str(bond["underlying_name"]).upper() or "退" in str(bond["underlying_name"]):
        risks.append("underlying_st_or_delisting_marker")
    latest_volume = float(bond_rows[-1]["volume"]) if bond_rows else None
    if latest_volume is not None and latest_volume <= 0:
        risks.append("latest_volume_zero")
    return {
        "bond_latest_date": bond_latest_date,
        "stock_latest_date": stock_latest_date,
        "bond_history_points": len(bond_rows),
        "stock_history_points": len(stock_rows),
        "bond_current": bond_current,
        "stock_current": stock_current,
        "bond_full_lookback": bond_full_lookback,
        "bond_turnover_lookback": bond_turnover_lookback,
        "stock_signal_available": stock_signal_available,
        "bond_close": bond_close,
        "stock_close": stock_close,
        "conversion_value": conversion_value,
        "premium_pct": premium,
        "weekly_return_pct": weekly_return,
        "daily_return_pct": daily_return,
        "bond_volume_ratio_5d": bond_volume_ratio_5d,
        "volume_ratio_denominator": "mean(previous_5_trading_sessions_volume_excluding_current)",
        "turnover_5d_pct": turnover5,
        "volume_structure_available": volume_structure_available,
        "recent_5d_mean_volume": recent_mean_volume,
        "previous_5d_mean_volume": previous_period_mean_volume,
        "volume_expansion_ratio_5d": volume_expansion_ratio,
        "recent_5d_volume_cv": recent_volume_cv,
        "max_daily_volume_share_5d": max_daily_volume_share,
        "uniform_volume_expansion": uniform_volume_expansion,
        "healthy_volume_contraction": healthy_volume_contraction,
        "sudden_abnormal_volume_contraction": sudden_abnormal_volume_contraction,
        "volume_structure_pass": volume_structure_pass,
        "bottom_pattern_flags": bottom_patterns["flags"],
        "bottom_patterns": bottom_patterns["matches"],
        **intraday,
        "ignition_local_cross_dates": ignition_crosses,
        "ignition_local_cross_dates_10": ignition_crosses_10,
        "ema3_latest": ema3_latest,
        "ema21_latest": ema21_latest,
        "youzi_buy_latest": buy_latest,
        "youzi_buy_prev": buy_prev,
        "youzi_recent_cross_dates": buy_crosses,
        "youzi_recent_cross_dates_5": buy_crosses_5,
        "youzi_pass": youzi_pass,
        "big_bull_red": big_bull_red,
        "ema5_latest": ema5_latest,
        "ema20_latest": ema20_latest,
        "stock_return5_pct": stock_return5,
        "stock_ema_bullish": stock_ema_bullish,
        "stock_ma5_latest": ma5_latest,
        "stock_ma10_latest": ma10_latest,
        "stock_ma20_latest": ma20_latest,
        "stock_ma_bullish": stock_ma_bullish,
        "underlying_trend_score": underlying_trend_score,
        "latest_volume": latest_volume,
        "maturity_date_status_checked": maturity_info["status"],
        "known_last_trade_date_status_checked": last_trade_info["status"],
        "known_last_trade_date_semantic_checked": "not_announced" if last_trade_info["status"] == "MISSING" else "announced",
        "risk_veto_reasons": risks,
    }, None


def clip(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return min(upper, max(lower, float(value)))


def newest_session_age(dates: Iterable[str], calendar: list[str], window: int = 10) -> int | None:
    positions = {date: index for index, date in enumerate(calendar)}
    latest_index = len(calendar) - 1
    ages = [latest_index - positions[date] for date in dates if date in positions]
    valid = [age for age in ages if 0 <= age < window]
    return min(valid) if valid else None


def score_component(
    criterion_id: str,
    normalized_score: float,
    raw_value: Any,
    data_status: str = "AVAILABLE",
    detail: str = "",
    coverage_fraction: float | None = None,
) -> dict[str, Any]:
    weight = next(float(item["weight"]) for item in SCORE_CRITERIA if item["id"] == criterion_id)
    normalized = clip(normalized_score)
    if coverage_fraction is None:
        coverage_fraction = 0.0 if data_status == "MISSING" else 0.5 if data_status == "PARTIAL" else 1.0
    return {
        "weight": weight,
        "normalized_score": normalized,
        "earned_score": weight * normalized,
        "data_status": data_status,
        "coverage_fraction": clip(coverage_fraction),
        "raw_value": raw_value,
        "detail": detail,
    }


def build_score_components(
    bond: dict[str, Any],
    local: dict[str, Any],
    feilong: dict[str, Any],
    scr: dict[str, Any],
    industry: dict[str, Any],
    concepts: list[dict[str, Any]],
    calendar: list[str],
) -> dict[str, dict[str, Any]]:
    weekly_return = local.get("weekly_return_pct")
    price_status = "AVAILABLE" if weekly_return is not None else "MISSING"
    price_norm = clip(float(weekly_return) / 5.0) if weekly_return is not None else 0.0

    remaining_yi = float(bond["remaining_yi"])
    scale_norm = 1.0 if remaining_yi <= 5.0 else clip((15.0 - remaining_yi) / 10.0)

    premium = local.get("premium_pct")
    if premium is None or not math.isfinite(float(premium)):
        premium_norm, premium_status = 0.0, "MISSING"
    else:
        premium = float(premium)
        premium_status = "AVAILABLE"
        if premium <= 10.0:
            premium_norm = 1.0
        elif premium <= 50.0:
            premium_norm = 1.0 - 0.5 * (premium - 10.0) / 40.0
        elif premium <= 100.0:
            premium_norm = 0.5 * (100.0 - premium) / 50.0
        else:
            premium_norm = 0.0

    ignition_dates = list(local.get("ignition_local_cross_dates_10") or [])
    ignition_age = newest_session_age(ignition_dates, calendar, 10)
    ignition_norm = 0.0 if ignition_age is None else max(0.5, 1.0 - ignition_age / 18.0)
    ignition_status = "AVAILABLE" if local.get("stock_signal_available") is True else "MISSING"

    feilong_available = int(feilong.get("point_count") or 0) >= 2
    valid_crosses = [item for item in feilong.get("score_window_crosses", []) if item.get("below20")]
    feilong_age = newest_session_age((str(item["date"]) for item in valid_crosses), calendar, 10)
    if not feilong_available:
        feilong_norm, feilong_status = 0.0, "MISSING"
    elif feilong_age is not None:
        newest_cross = max(valid_crosses, key=lambda item: str(item["date"]))
        cross_level = max(float(newest_cross["wave"]), float(newest_cross["segment"]))
        low_position = clip((25.0 - cross_level) / 15.0, 0.35, 1.0)
        recency = max(0.5, 1.0 - feilong_age / 18.0)
        feilong_norm, feilong_status = 0.75 * recency + 0.25 * low_position, "AVAILABLE"
    else:
        wave = feilong.get("latest_wave")
        segment = feilong.get("latest_segment")
        if wave is None or segment is None:
            feilong_norm, feilong_status = 0.0, "MISSING"
        else:
            wave, segment = float(wave), float(segment)
            if wave < 20.0 and segment < 20.0 and wave > segment:
                feilong_norm = 0.40
            elif wave < 20.0 and segment < 20.0:
                feilong_norm = 0.20
            elif wave < 30.0 and segment < 30.0 and wave > segment:
                feilong_norm = 0.15
            else:
                feilong_norm = 0.0
            feilong_status = "AVAILABLE"

    buy_latest = local.get("youzi_buy_latest")
    buy_prev = local.get("youzi_buy_prev")
    buy_crosses_5 = list(local.get("youzi_recent_cross_dates_5") or [])
    youzi_status = "AVAILABLE" if buy_latest is not None and buy_prev is not None else "MISSING"
    youzi_norm = (
        0.25 * float(float(buy_latest) > 0.0)
        + 0.35 * float(float(buy_latest) > float(buy_prev))
        + 0.40 * float(bool(buy_crosses_5))
        if youzi_status == "AVAILABLE"
        else 0.0
    )

    shrink90 = scr.get("shrink90_pp")
    shrink70 = scr.get("shrink70_pp")
    scr90_status = "AVAILABLE" if shrink90 is not None else "MISSING"
    scr70_status = "AVAILABLE" if shrink70 is not None else "MISSING"
    old_scr90 = scr.get("scr90_old")
    relative_shrink90 = (
        float(shrink90) / float(old_scr90)
        if shrink90 is not None and old_scr90 is not None and float(old_scr90) > 0
        else None
    )
    scr90_absolute_norm = clip(float(shrink90) / 10.0) if shrink90 is not None else 0.0
    scr90_relative_norm = clip(float(relative_shrink90) / (1.0 / 3.0)) if relative_shrink90 is not None else 0.0
    scr90_norm = 0.50 * scr90_absolute_norm + 0.50 * scr90_relative_norm
    scr70_norm = clip(float(shrink70) / 3.0) if shrink70 is not None else 0.0

    industry_score = industry.get("heat_score")
    industry_norm = clip(float(industry_score) / 100.0) if industry_score is not None else 0.0
    concept_candidates: list[dict[str, Any]] = []
    for item in concepts:
        heat = clip(float(item.get("heat_score") or 0.0) / 100.0)
        concept_candidates.append({
            "name": item.get("name"),
            "heat_score": item.get("heat_score"),
            "mean_return_5d": item.get("mean_return_5d"),
            "up_ratio_5d": item.get("up_ratio_5d"),
            "normalized_heat": heat,
        })
    best_concept = min(
        concept_candidates,
        key=lambda item: (-float(item["heat_score"] or 0.0), str(item["name"] or "")),
        default=None,
    )
    concept_norm = float(best_concept["normalized_heat"]) if best_concept else 0.0
    underlying_trend = local.get("underlying_trend_score")
    trend_norm = clip(float(underlying_trend)) if underlying_trend is not None else 0.0
    heat_norm = 0.30 * industry_norm + 0.40 * concept_norm + 0.30 * trend_norm
    heat_coverage = (
        0.30 * float(industry_score is not None)
        + 0.40 * float(best_concept is not None)
        + 0.30 * float(underlying_trend is not None)
    )
    heat_status = "AVAILABLE" if math.isclose(heat_coverage, 1.0) else "MISSING" if heat_coverage == 0.0 else "PARTIAL"

    turnover5 = local.get("turnover_5d_pct")
    turnover_status = "AVAILABLE" if turnover5 is not None else "MISSING"
    turnover_norm = clip(float(turnover5) / 150.0) if turnover5 is not None else 0.0

    return {
        "c1_price_activity": score_component(
            "c1_price_activity", price_norm, {"weekly_return_pct": weekly_return}, price_status, "5日涨幅/5%，下跌记0分，上限1"
        ),
        "c2_remaining_scale": score_component(
            "c2_remaining_scale", scale_norm, {"remaining_yi": remaining_yi}, detail="5亿元以内满分，5至15亿元线性递减"
        ),
        "c3_premium": score_component(
            "c3_premium", premium_norm, {"premium_pct": premium}, premium_status, "10%以内满分，10%至100%分段递减"
        ),
        "c4_golden_ignition": score_component(
            "c4_golden_ignition", ignition_norm,
            {"cross_dates_10": sorted(set(ignition_dates)), "newest_age_sessions": ignition_age, "ema3_latest": local.get("ema3_latest"), "ema21_latest": local.get("ema21_latest")},
            ignition_status, "仅按正股EMA3上穿EMA21的10交易日新鲜度计分；大牛线仅作独立诊断",
        ),
        "c5_feilong_cross": score_component(
            "c5_feilong_cross", feilong_norm,
            {"newest_age_sessions": feilong_age, "valid_below20_crosses": valid_crosses, "latest_wave": feilong.get("latest_wave"), "latest_segment": feilong.get("latest_segment"), "point_count": feilong.get("point_count")},
            feilong_status, "20以下金叉按新鲜度和低位程度计分；低位临界结构给部分分",
        ),
        "c6_youzi_inflow": score_component(
            "c6_youzi_inflow", youzi_norm,
            {"buy_latest": buy_latest, "buy_prev": buy_prev, "cross_dates_5": buy_crosses_5},
            youzi_status, "正值25%+继续增强35%+5日内上穿0为40%",
        ),
        "c7_scr90_convergence": score_component(
            "c7_scr90_convergence", scr90_norm,
            {"shrink90_pp": shrink90, "relative_shrink90": relative_shrink90, "old": old_scr90, "latest": scr.get("scr90_latest")},
            scr90_status, "绝对收缩/10与相对收缩/(1/3)各占50%",
        ),
        "c8_scr70_convergence": score_component(
            "c8_scr70_convergence", scr70_norm,
            {"shrink70_pp": shrink70, "old": scr.get("scr70_old"), "latest": scr.get("scr70_latest")},
            scr70_status, "缩小3个百分点达到满分",
        ),
        "c9_sector_heat": score_component(
            "c9_sector_heat", heat_norm,
            {"industry_heat_score": industry_score, "industry_normalized": industry_norm, "best_concept": best_concept, "underlying_trend_score": underlying_trend},
            heat_status, "行业30%+最强方向概念40%+正股趋势30%", heat_coverage,
        ),
        "c11_turnover5": score_component(
            "c11_turnover5", turnover_norm, {"turnover_5d_pct": turnover5}, turnover_status, "近5日累计换手率/150%，上限1"
        ),
    }


def _main_impl() -> int:
    total_started = time.perf_counter()
    stage_started = total_started
    stage_seconds: dict[str, float] = {}
    parser = argparse.ArgumentParser(description="Weighted full-market convertible-bond scanner on local TDX")
    parser.add_argument("--cutoff", default=None, help="YYYYMMDD; omitted means latest local SH benchmark close")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--formula-evidence-output", type=Path, default=None)
    parser.add_argument("--day-input-manifest-output", type=Path, default=None)
    parser.add_argument("--redemption-announcements", required=True, type=Path)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--skip-tq", action="store_true")
    args = parser.parse_args()
    run_id = str(args.run_id or f"standalone-{uuid.uuid4().hex}")
    formula_evidence_output = args.formula_evidence_output or args.output.with_name(
        f"{args.output.stem}_formula_evidence.json"
    )
    day_input_manifest_output = args.day_input_manifest_output or args.output.with_name(
        f"{args.output.stem}_day_input_manifest.json"
    )
    if args.attempt <= 0:
        raise SystemExit("invalid --attempt")
    source_files = build_source_files()
    base_hub = load_hub()
    if args.cutoff:
        cutoff = args.cutoff.replace("-", "")
        if not re.fullmatch(r"20\d{6}", cutoff):
            raise SystemExit("invalid --cutoff")
    else:
        preliminary_hub, _preliminary_manifest = capture_day_input_snapshot(
            base_hub,
            ["999999.SH"],
            run_id,
            "UNRESOLVED",
        )
        benchmark_rows = read_day_records(preliminary_hub, "999999.SH", 10)
        if not benchmark_rows:
            raise RuntimeError("cannot resolve latest local benchmark close")
        cutoff = str(benchmark_rows[-1]["date"])
    bonds, _tnf, master_diagnostics = parse_bonds(cutoff)
    early_redemption_by_symbol, redemption_snapshot_meta = load_early_redemption_snapshot(
        args.redemption_announcements,
        run_id=run_id,
        cutoff=cutoff,
        bonds=bonds,
    )
    parsed_industry_inputs = parse_industry_inputs()
    concepts = parse_concepts()
    heat_codes = {
        code
        for codes in parsed_industry_inputs[1].values()
        for code in codes
    }
    heat_codes.update(
        item_code[1:]
        for concept in concepts
        for item_code in concept["codes"]
    )
    day_lookup_symbols = {
        "999999.SH",
        *heat_codes,
        *(suffix_symbol(code) for code in heat_codes),
    }
    day_lookup_symbols.update(bond["symbol"] for bond in bonds)
    day_lookup_symbols.update(bond["underlying_symbol"] for bond in bonds)
    hub, day_input_manifest_payload = capture_day_input_snapshot(
        base_hub,
        day_lookup_symbols,
        run_id,
        cutoff,
    )
    day_input_manifest_payload["market_attempt"] = args.attempt
    frozen_benchmark_rows = read_day_records(hub, "999999.SH", 10)
    if not frozen_benchmark_rows or str(frozen_benchmark_rows[-1]["date"]) != cutoff:
        raise DayInputUpdateRace(
            f"{TDX_DAY_UPDATE_RACE}:benchmark_cutoff_changed_during_snapshot"
        )
    calendar = benchmark_calendar(hub, cutoff)
    stage_seconds["resolve_inputs"] = time.perf_counter() - stage_started
    stage_started = time.perf_counter()
    cache: dict[str, dict[str, Any] | None] = {}
    stock_industry, industry_heat = build_industry_heat(
        hub, cutoff, calendar, cache, parsed_industry_inputs
    )
    concept_by_code, concept_rank = build_concept_heat(hub, cutoff, calendar, cache, concepts)
    stage_seconds["market_heat"] = time.perf_counter() - stage_started
    stage_started = time.perf_counter()

    local_rows: dict[str, dict[str, Any]] = {}
    missing_local: list[str] = []
    missing_local_details: list[dict[str, str]] = []
    for bond in bonds:
        item, reason = analyze_local(hub, bond, cutoff, calendar)
        if item is None:
            raise RuntimeError(f"analyze_local contract violation for {bond['symbol']}: {reason or 'no row'}")
        local_rows[bond["symbol"]] = item
        missing_parts: list[str] = []
        if int(item.get("bond_history_points") or 0) == 0:
            missing_parts.append("bond_day_history_missing")
        if int(item.get("stock_history_points") or 0) == 0:
            missing_parts.append("underlying_day_history_missing")
        if missing_parts:
            missing_local.append(bond["symbol"])
            missing_local_details.append({"symbol": bond["symbol"], "reason": ";".join(missing_parts)})
    stage_seconds["local_analysis"] = time.perf_counter() - stage_started
    stage_started = time.perf_counter()

    tq_errors: list[dict[str, Any]] = []
    feilong_nodes: dict[str, Any] = {}
    scr90_nodes: dict[str, Any] = {}
    scr70_nodes: dict[str, Any] = {}
    bigbull_nodes: dict[str, Any] = {}
    formula_seconds: dict[str, float] = {}
    stock_symbols = sorted({
        bond["underlying_symbol"]
        for bond in bonds
        if local_rows[bond["symbol"]].get("stock_signal_available") is True
    })
    formula_bond_symbols = sorted(
        symbol for symbol, node in local_rows.items() if node.get("bond_full_lookback") is True
    )
    if not args.skip_tq:
        formula_started = time.perf_counter()
        tq = load_tq()
        formula_seconds["initialize"] = time.perf_counter() - formula_started
        try:
            formula_started = time.perf_counter()
            feilong_nodes, errors = merge_formula_batches(
                tq,
                "飞龙在天",
                stock_symbols,
                cutoff,
                12,
                1,
                history_count=TQ_LONG_FORMULA_HISTORY_COUNT,
            )
            formula_seconds["feilong"] = time.perf_counter() - formula_started
            tq_errors.extend(errors)
            formula_started = time.perf_counter()
            scr90_nodes, errors = merge_formula_batches(tq, "SCR", formula_bond_symbols, cutoff, 6, 0, "90")
            formula_seconds["scr90"] = time.perf_counter() - formula_started
            tq_errors.extend(errors)
            formula_started = time.perf_counter()
            scr70_nodes, errors = merge_formula_batches(tq, "SCR", formula_bond_symbols, cutoff, 6, 0, "70")
            formula_seconds["scr70"] = time.perf_counter() - formula_started
            tq_errors.extend(errors)
            formula_started = time.perf_counter()
            bigbull_nodes, errors = merge_formula_batches(
                tq,
                "大牛线撑压版",
                stock_symbols,
                cutoff,
                5,
                1,
                history_count=TQ_LONG_FORMULA_HISTORY_COUNT,
            )
            formula_seconds["bigbull"] = time.perf_counter() - formula_started
            tq_errors.extend(errors)
        finally:
            try:
                tq.close()
            except Exception:
                pass
    stage_seconds["tq_formulas"] = time.perf_counter() - stage_started
    stage_started = time.perf_counter()

    evaluated_results: list[dict[str, Any]] = []
    diagnostic_condition_keys = ["c1_weekly_gain_ge_5", "c2_remaining_lt_5yi", "c3_premium_lt_50", "c4_recent_ignition", "c5_feilong_below20_cross", "c6_youzi_inflow_start", "c7_scr90_significant_contraction", "c8_scr70_shrink_ge_3pp", "c9_hot_industry_and_concept", "c11_turnover5_ge_150"]
    for bond in bonds:
        local = local_rows.get(bond["symbol"])
        if local is None:
            raise RuntimeError(f"ranked universe lost local placeholder for {bond['symbol']}")
        feilong = eval_feilong(feilong_nodes.get(bond["underlying_symbol"]), cutoff)
        scr = eval_scr(
            scr90_nodes.get(bond["symbol"]),
            scr70_nodes.get(bond["symbol"]),
            cutoff,
            calendar[-6:],
        )
        _bigbull_formula_hit, bigbull_formula_diagnostic_hits = formula_triggered(
            bigbull_nodes.get(bond["underlying_symbol"]), cutoff
        )
        industry_code = stock_industry.get(code7(bond["underlying"]))
        industry = industry_heat.get(industry_code or "", {})
        concepts = concept_by_code.get(code7(bond["underlying"]), [])[:5]
        top_concept_score = max((float(item["heat_score"]) for item in concepts), default=None)
        industry_score = as_float(str(industry.get("heat_score")))
        underlying_trend_score = local.get("underlying_trend_score")
        heat_pass = (
            industry_score is not None and industry_score / 100.0 >= 0.60
            and top_concept_score is not None and top_concept_score / 100.0 >= 0.60
            and underlying_trend_score is not None and float(underlying_trend_score) >= 0.60
        )
        premium = local["premium_pct"]
        conditions = {
            "c1_weekly_gain_ge_5": local.get("weekly_return_pct") is not None and float(local["weekly_return_pct"]) >= 5.0,
            "c2_remaining_lt_5yi": float(bond["remaining_yi"]) < 5.0,
            "c3_premium_lt_50": premium is not None and float(premium) < 50.0,
            "c4_recent_ignition": bool(local["ignition_local_cross_dates_10"]),
            "c5_feilong_below20_cross": bool(feilong["pass"]),
            "c6_youzi_inflow_start": bool(local["youzi_pass"]),
            "c7_scr90_significant_contraction": bool(scr.get("pass90")),
            "c8_scr70_shrink_ge_3pp": bool(scr.get("pass70")),
            "c9_hot_industry_and_concept": heat_pass,
            "c10_big_bull_red_preference": bool(local["big_bull_red"]),
            "c11_turnover5_ge_150": local.get("turnover_5d_pct") is not None and float(local["turnover_5d_pct"]) >= 150.0,
        }
        combat_checks = (
            ("weekly_gain_below_5pct", conditions["c1_weekly_gain_ge_5"]),
            ("turnover_5d_below_150pct", conditions["c11_turnover5_ge_150"]),
            ("scr90_contraction_not_significant", conditions["c7_scr90_significant_contraction"]),
            ("feilong_below20_cross_missing", conditions["c5_feilong_below20_cross"]),
            ("underlying_trend_or_hotspot_failed", conditions["c9_hot_industry_and_concept"]),
            ("uniform_volume_expansion_failed", bool(local.get("volume_structure_pass"))),
            ("intraday_weak_or_missing", local.get("intraday_status") not in ("WEAK", "MISSING")),
        )
        combat_readiness_reasons = [reason for reason, passed in combat_checks if not passed]
        combat_readiness_pass = not combat_readiness_reasons
        score_components = build_score_components(bond, local, feilong, scr, industry, concepts, calendar)
        score_total_raw = canonical_business_sum(
            float(item["earned_score"]) for item in score_components.values()
        )
        score_coverage_weight = sum(
            float(item["weight"]) * float(item["coverage_fraction"])
            for item in score_components.values()
        )
        score_missing_criteria = [key for key, item in score_components.items() if item["data_status"] == "MISSING"]
        score_partial_criteria = [key for key, item in score_components.items() if item["data_status"] == "PARTIAL"]
        risk_warning_labels: list[str] = []
        if float(bond["remaining_yi"]) <= 0.5:
            risk_warning_labels.append("very_small_remaining_scale_le_0_5yi")
        if local.get("bond_close") is not None and float(local["bond_close"]) >= 150.0:
            risk_warning_labels.append("high_bond_price_ge_150")
        if premium is not None and float(premium) >= 80.0:
            risk_warning_labels.append("high_premium_ge_80pct")
        if local.get("weekly_return_pct") is not None and float(local["weekly_return_pct"]) <= -10.0:
            risk_warning_labels.append("weekly_drop_ge_10pct")
        risk_level = "RED" if local["risk_veto_reasons"] else "YELLOW" if risk_warning_labels else "GREEN"
        early_redemption_record = early_redemption_by_symbol[bond["symbol"]]
        early_redemption_status = str(early_redemption_record["early_redemption_status"])
        hard_exclusion_reasons: list[str] = []
        if str(bond["name"]).strip().upper().startswith("Z"):
            hard_exclusion_reasons.append("bond_name_z_prefix")
        if (
            local.get("daily_return_pct") is not None
            and float(local["daily_return_pct"]) >= 10.0
            and local.get("bond_volume_ratio_5d") is not None
            and float(local["bond_volume_ratio_5d"]) > 4.0
        ):
            hard_exclusion_reasons.append("daily_gain_ge_10_and_volume_ratio_gt_4")
        if scr.get("scr90_change_1d_pp") is None:
            hard_exclusion_reasons.append("scr90_change_1d_unavailable")
        elif float(scr["scr90_change_1d_pp"]) > 0.0:
            hard_exclusion_reasons.append("scr90_change_1d_positive")
        if local.get("turnover_5d_pct") is not None and float(local["turnover_5d_pct"]) > 1000.0:
            hard_exclusion_reasons.append("turnover_5d_gt_1000")
        if local.get("bond_close") is not None and float(local["bond_close"]) > 350.0:
            hard_exclusion_reasons.append("bond_close_gt_350")
        if early_redemption_status == "ANNOUNCED_EARLY_REDEMPTION":
            hard_exclusion_reasons.append("early_redemption_announced")
        elif early_redemption_status == "UNVERIFIED":
            hard_exclusion_reasons.append("early_redemption_unverified")
        evaluated_results.append({
            **bond,
            **local,
            "industry": industry,
            "top_concepts": concepts,
            "top_concept_heat_score": top_concept_score,
            "feilong": feilong,
            "scr": scr,
            "scr90_previous": scr.get("scr90_previous"),
            "scr90_latest": scr.get("scr90_latest"),
            "scr90_change_1d_pp": scr.get("scr90_change_1d_pp"),
            "early_redemption_status": early_redemption_status,
            "early_redemption_record": early_redemption_record,
            "hard_exclusion_reasons": hard_exclusion_reasons,
            "hard_exclusion_pass": not hard_exclusion_reasons,
            "combat_readiness_pass": combat_readiness_pass,
            "combat_readiness_reasons": combat_readiness_reasons,
            "recommendation_tier": "实战候选" if combat_readiness_pass else "仅观察",
            "bigbull_formula_diagnostic_hits": bigbull_formula_diagnostic_hits,
            "conditions": conditions,
            "score_components": score_components,
            "score_total_raw": score_total_raw,
            "score_coverage_weight": score_coverage_weight,
            "score_missing_criteria": score_missing_criteria,
            "score_partial_criteria": score_partial_criteria,
            "diagnostic_condition_pass_count": sum(bool(conditions[key]) for key in diagnostic_condition_keys),
            "big_bull_red_preference": bool(conditions["c10_big_bull_red_preference"]),
            "risk_warning_labels": risk_warning_labels,
            "risk_level": risk_level,
        })

    for item in evaluated_results:
        item["personal_kb_confirmation"] = build_personal_kb_confirmation(item)

    evaluated_results = canonicalize_business_payload(evaluated_results)
    results = [item for item in evaluated_results if item["hard_exclusion_pass"]]
    hard_excluded_results = [item for item in evaluated_results if not item["hard_exclusion_pass"]]
    results.sort(key=ranking_key)
    for position, item in enumerate(results, start=1):
        item["rank"] = position
    for item in hard_excluded_results:
        item["rank"] = None
    hard_excluded_results.sort(key=lambda item: item["symbol"])
    ranking_top10 = results[:10]
    risk_counts_top10 = {
        level: sum(item["risk_level"] == level for item in ranking_top10)
        for level in ("RED", "YELLOW", "GREEN")
    }
    stage_seconds["score_and_rank"] = time.perf_counter() - stage_started
    stage_started = time.perf_counter()

    expected_underlyings = len(stock_symbols)
    field_coverage = {
        "feilong": formula_field_coverage(feilong_nodes, stock_symbols, ("波", "段"), cutoff, 2),
        "scr90": formula_field_coverage(
            scr90_nodes, formula_bond_symbols, ("SCR",), cutoff, 6, required_dates=calendar[-6:]
        ),
        "scr70": formula_field_coverage(
            scr70_nodes, formula_bond_symbols, ("SCR",), cutoff, 6, required_dates=calendar[-6:]
        ),
        "bigbull": formula_field_coverage(
            bigbull_nodes,
            stock_symbols,
            ("OUTPUT59", "OUTPUT60", "OUTPUT61"),
            cutoff,
            1,
            require_all_fields=False,
        ),
    }
    formula_evidence_payload = {
        "schema": "CONVERTIBLE-BOND-FORMULA-EVIDENCE-1",
        "run_id": run_id,
        "market_attempt": args.attempt,
        "cutoff_trade_date": cutoff,
        "tq_runtime": {
            "client_process": "TdxW.exe",
            "strategy_path": str(TQ_STRATEGY_PATH),
            "history_count": {
                "feilong": TQ_LONG_FORMULA_HISTORY_COUNT,
                "scr90": 0,
                "scr70": 0,
                "bigbull": TQ_LONG_FORMULA_HISTORY_COUNT,
            },
            "formula_seconds": {key: round(value, 6) for key, value in formula_seconds.items()},
        },
        "formulas": {
            "feilong": compact_formula_nodes(feilong_nodes, ("波", "段")),
            "scr90": compact_formula_nodes(scr90_nodes, ("SCR",)),
            "scr70": compact_formula_nodes(scr70_nodes, ("SCR",)),
            "bigbull": compact_formula_nodes(bigbull_nodes, ("OUTPUT59", "OUTPUT60", "OUTPUT61")),
        },
    }
    node_counts_complete = (
        len(feilong_nodes) == expected_underlyings
        and len(bigbull_nodes) == expected_underlyings
        and len(scr90_nodes) == len(formula_bond_symbols)
        and len(scr70_nodes) == len(formula_bond_symbols)
    )
    formula_complete = (
        not args.skip_tq
        and not tq_errors
        and node_counts_complete
        and all(item["complete"] for item in field_coverage.values())
    )
    result_symbols = [item["symbol"] for item in results]
    excluded_symbols = [item["symbol"] for item in hard_excluded_results]
    evaluated_symbols = [*result_symbols, *excluded_symbols]
    universe_partition_complete = (
        len(evaluated_results) == len(bonds)
        and len(evaluated_symbols) == len(set(evaluated_symbols))
        and set(result_symbols).isdisjoint(excluded_symbols)
        and set(evaluated_symbols) == {bond["symbol"] for bond in bonds}
    )
    scan_integrity_complete = bool(
        master_diagnostics["integrity_complete"]
        and universe_partition_complete
        and day_input_manifest_payload["complete"]
    )
    scan_status = "PASS" if results and formula_complete and scan_integrity_complete else "PARTIAL" if results else "BLOCKED"
    day_inputs_current, day_input_diagnostics = validate_day_input_manifest_current(
        base_hub,
        day_input_manifest_payload,
        expected_run_id=run_id,
        expected_cutoff=cutoff,
    )
    if not day_inputs_current:
        mismatches = [
            item for item in day_input_diagnostics
            if item.get("unique") is not True or item.get("current") is not True
        ]
        raise DayInputUpdateRace(
            f"{TDX_DAY_UPDATE_RACE}:day_input_manifest_changed:count={len(mismatches)}",
            mismatches,
        )
    source_files_after = build_source_files()
    if source_files_after != source_files:
        raise RuntimeError("source input changed during run")
    redemption_snapshot_after = file_meta(args.redemption_announcements)
    if any(
        redemption_snapshot_after.get(key) != redemption_snapshot_meta.get(key)
        for key in ("path", "size", "mtime_ns", "sha256", "updated_at")
    ):
        raise RuntimeError("early-redemption snapshot changed during run")
    day_input_manifest_output.parent.mkdir(parents=True, exist_ok=True)
    formula_evidence_output.parent.mkdir(parents=True, exist_ok=True)
    day_input_manifest_payload = canonicalize_business_payload(
        day_input_manifest_payload
    )
    formula_evidence_payload = canonicalize_business_payload(
        formula_evidence_payload
    )
    atomic_write_json(day_input_manifest_output, day_input_manifest_payload)
    day_input_manifest_meta = file_meta(day_input_manifest_output)
    atomic_write_json(formula_evidence_output, formula_evidence_payload)
    formula_evidence_meta = file_meta(formula_evidence_output)
    stage_seconds["integrity_and_source_binding"] = time.perf_counter() - stage_started
    payload = {
        "status": scan_status,
        "schema": "TDX-CONVERTIBLE-BOND-WEIGHTED-SCAN-V5",
        "run_id": run_id,
        "market_attempt": args.attempt,
        "scan_attempt": args.attempt,
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "cutoff_trade_date": cutoff,
        "source_binding_mode": SOURCE_BINDING_MODE,
        "day_input_binding_mode": DAY_INPUT_BINDING_MODE,
        "universe_definition": "All current eligible SH/SZ convertible-bond rows in speckzzdata.txt are evaluated. The declared hard exclusions are applied before ranking; only hard_exclusion_pass=true rows enter the weighted ranking. TNF confirmation and local history availability are independently disclosed. Unsupported-market directed convertibles are excluded.",
        "universe_count": len(bonds),
        "local_synchronized_count": sum(
            node.get("bond_current") is True and node.get("stock_current") is True
            for node in local_rows.values()
        ),
        "full_lookback_count": sum(node.get("bond_full_lookback") is True for node in local_rows.values()),
        "technical_partial_count": sum(
            node.get("bond_full_lookback") is not True or node.get("stock_signal_available") is not True
            for node in local_rows.values()
        ),
        "technical_partial_details": [
            {
                "symbol": symbol,
                "bond_latest_date": node.get("bond_latest_date"),
                "stock_latest_date": node.get("stock_latest_date"),
                "bond_history_points": node.get("bond_history_points"),
                "stock_history_points": node.get("stock_history_points"),
                "risk_veto_reasons": node.get("risk_veto_reasons"),
            }
            for symbol, node in sorted(local_rows.items())
            if node.get("bond_full_lookback") is not True or node.get("stock_signal_available") is not True
        ],
        "missing_local_count": len(missing_local),
        "missing_local_symbols": missing_local,
        "missing_local_details": missing_local_details,
        "unavailable_local_retained_count": len(missing_local),
        "universe_partition_complete": universe_partition_complete,
        "hard_exclusion_model": HARD_EXCLUSION_MODEL,
        "personal_kb_confirmation_model": PERSONAL_KB_CONFIRMATION_MODEL,
        "hard_exclusion_reason_counts": {
            reason["reason_code"]: sum(
                reason["reason_code"] in item["hard_exclusion_reasons"]
                for item in hard_excluded_results
            )
            for reason in HARD_EXCLUSION_MODEL["rules"]
        },
        "bond_master_diagnostics": master_diagnostics,
        "formula_coverage": {
            "expected_underlyings": expected_underlyings,
            "expected_bonds": len(formula_bond_symbols),
            "scored_bonds": len(local_rows),
            "formula_ineligible_bonds": sorted(set(local_rows) - set(formula_bond_symbols)),
            "feilong_underlyings": len(feilong_nodes),
            "scr90_bonds": len(scr90_nodes),
            "scr70_bonds": len(scr70_nodes),
            "bigbull_underlyings": len(bigbull_nodes),
            "node_counts_complete": node_counts_complete,
            "field_coverage": field_coverage,
            "tq_batch_size": TQ_BATCH_SIZE,
            "history_count": {
                "feilong": TQ_LONG_FORMULA_HISTORY_COUNT,
                "scr90": 0,
                "scr70": 0,
                "bigbull": TQ_LONG_FORMULA_HISTORY_COUNT,
            },
            "errors": tq_errors,
            "complete": formula_complete,
        },
        "score_model": {
            "version": "CB-WEIGHTED-10-V2",
            "criteria": list(SCORE_CRITERIA),
            "criterion_count": len(SCORE_CRITERIA),
            "weight_sum": sum(float(item["weight"]) for item in SCORE_CRITERIA),
            "score_formula": "score_total_raw = sum(weight * normalized_score) across exactly 10 criteria; missing components score zero and are never renormalized",
            "normalization_rules": {
                "c1_price_activity": "clip(return5_pct/5,0,1); negative returns score zero",
                "c2_remaining_scale": "1 if remaining_yi<=5 else clip((15-remaining_yi)/10,0,1)",
                "c3_premium": "1 through 10%; linearly to 0.5 at 50%; linearly to 0 at 100%",
                "c4_golden_ignition": "latest local EMA3 upward-cross EMA21 within 10 benchmark sessions: max(0.5,1-age/18); Big Bull OUTPUT59/60/61 is diagnostic only",
                "c5_feilong_cross": "below20 cross recency 75% plus low-position 25%; low-position pre-cross structures receive limited partial credit",
                "c6_youzi_inflow": "positive latest 25% + rising latest 35% + cross above zero within 5 sessions 40%",
                "c7_scr90_convergence": "50%*clip(shrink90_pp/10,0,1) + 50%*clip(relative_shrink90/(1/3),0,1)",
                "c8_scr70_convergence": "clip(shrink70_pp/3,0,1)",
                "c9_sector_heat": C9_NORMALIZATION_RULE,
                "c11_turnover5": "clip(turnover5_pct/150,0,1)",
            },
            "tie_break_rule": "score_total_raw DESC; exact ties prefer personal knowledge-base confirmation quality DESC; then big_bull_red=True; then convertible-bond symbol ASC",
            "big_bull_rule": "EMA5>EMA20 is a displayed exact-tie preference only and contributes zero score",
            "risk_rule": "base risk labels do not change score_total_raw; personal knowledge-base confirmation affects exact-score ties only",
        },
        "benchmark_calendar": calendar,
        "industry_heat_method": "strict 11-session benchmark alignment, N>=10 and coverage>=70%; 35% median 5d return percentile + 25% positive-breadth percentile + 20% median 5d amount-active-ratio percentile + 20% above-MA5 breadth percentile",
        "concept_heat_method": "all local GN_ concepts; equal mean of nine current/5d cross-sectional percentiles, then absolute gate of positive mean 5d return and >=50% 5d positive breadth",
        "ranking_top10": ranking_top10,
        "ranking_top10_red_risk_count": sum(item["risk_level"] == "RED" for item in ranking_top10),
        "risk_counts_top10": risk_counts_top10,
        "execution_policy": {
            "mode": "post_close_manual_decision_support",
            "automatic_order": False,
            "execution_eligible": risk_counts_top10["GREEN"] > 0,
            "eligibility_meaning": "At least one GREEN candidate may enter manual review; this is never a direct order instruction.",
            "strong_redemption_announcements_verified": True,
        },
        "condition_pass_counts": {key: sum(bool(item["conditions"][key]) for item in results) for key in [*diagnostic_condition_keys, "c10_big_bull_red_preference"]},
        "ranked_count": len(results),
        "eligible_count": len(results),
        "hard_excluded_count": len(hard_excluded_results),
        "evaluated_count": len(evaluated_results),
        "analyzed_count": len(evaluated_results),
        "all_results": results,
        "hard_excluded_results": hard_excluded_results,
        "industry_count": len(industry_heat),
        "eligible_concept_count": len(concept_rank),
        "source_files": source_files,
        "formula_evidence": formula_evidence_meta,
        "day_input_manifest": day_input_manifest_meta,
        "redemption_announcement_snapshot": redemption_snapshot_meta,
        "performance": {
            "tq_batch_size": TQ_BATCH_SIZE,
            "market_snapshot_workers": MARKET_SNAPSHOT_WORKERS,
            "market_snapshot_cache_count": len(cache),
            "formula_seconds": {key: round(value, 6) for key, value in formula_seconds.items()},
            "stage_seconds": {key: round(value, 6) for key, value in stage_seconds.items()},
            "elapsed_before_serialization_seconds": round(time.perf_counter() - total_started, 6),
        },
        "risk_boundary": [
            "This is rule-based decision support, not a return guarantee or personalized investment advice.",
            "SCR/COST is a Tongdaxin turnover-price model estimate, not exchange account-level holdings.",
            "The scan is a synchronized local-TDX closing snapshot at cutoff_trade_date, not an intraday execution signal.",
            "Risk labels are displayed separately and do not alter the raw weighted ranking.",
            "Official early-redemption announcements are a hard exclusion; unverified bond-level announcement status is fail-closed and excluded.",
        ],
    }
    payload = canonicalize_business_payload(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(args.output, payload)
    readback = json.loads(args.output.read_text(encoding="utf-8"))
    summary = {
        "status": payload["status"],
        "output": str(args.output),
        "output_size": args.output.stat().st_size,
        "output_sha256": sha256(args.output),
        "readback_schema": readback.get("schema"),
        "cutoff_trade_date": cutoff,
        "universe_count": len(bonds),
        "evaluated_count": len(evaluated_results),
        "eligible_count": len(results),
        "hard_excluded_count": len(hard_excluded_results),
        "analyzed_count": len(evaluated_results),
        "ranking_top10": [
            {
                "rank": item["rank"],
                "symbol": item["symbol"],
                "name": item["name"],
                "underlying_symbol": item["underlying_symbol"],
                "underlying_name": item["underlying_name"],
                "score": round(float(item["score_total_raw"]), 4),
                "personal_kb_confirmation_quality": round(
                    float(
                        (item.get("personal_kb_confirmation") or {}).get("quality_score")
                        or 0.0
                    ),
                    2,
                ),
                "personal_kb_confirmation_level": (
                    item.get("personal_kb_confirmation") or {}
                ).get("level"),
                "personal_kb_confirmation_risk_labels": (
                    item.get("personal_kb_confirmation") or {}
                ).get("risk_labels", []),
                "big_bull_red_preference": item["big_bull_red_preference"],
                "risk_level": item["risk_level"],
                "risk_labels": [*item["risk_veto_reasons"], *item["risk_warning_labels"]],
            }
            for item in ranking_top10
        ],
        "formula_coverage": payload["formula_coverage"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


def _cli_argument_value(option: str, default: str = "") -> str:
    for index, value in enumerate(sys.argv[:-1]):
        if value == option:
            return str(sys.argv[index + 1])
    return default


def main() -> int:
    try:
        return _main_impl()
    except DayInputUpdateRace as exc:
        run_id = _cli_argument_value("--run-id", "unknown")
        attempt_raw = _cli_argument_value("--attempt", "1")
        try:
            attempt = int(attempt_raw)
        except ValueError:
            attempt = 1
        event = {
            "schema": "CONVERTIBLE-BOND-SCAN-FAILURE-1",
            "status": "FAIL",
            "failure_code": TDX_DAY_UPDATE_RACE,
            "retryable": True,
            "script": str(Path(__file__).resolve()),
            "run_id": run_id,
            "attempt": attempt,
            "error": str(exc),
            "mismatch_count": len(exc.diagnostics),
            "mismatch_paths": [str(item.get("path") or "") for item in exc.diagnostics],
        }
        print(json.dumps(event, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
