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
import json
import math
import re
import statistics
import struct
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

from runtime_utils import atomic_write_json, canonicalize_business_payload
from independent_heat_verifier import recompute_heat


EXPECTED_IDS = (
    "c1_price_activity",
    "c2_remaining_scale",
    "c3_premium",
    "c4_golden_ignition",
    "c5_feilong_cross",
    "c6_youzi_inflow",
    "c7_scr90_convergence",
    "c8_scr70_convergence",
    "c9_sector_heat",
    "c11_turnover5",
)
EXPECTED_WEIGHTS = {
    "c1_price_activity": 6.0,
    "c2_remaining_scale": 8.0,
    "c3_premium": 12.0,
    "c4_golden_ignition": 14.0,
    "c5_feilong_cross": 15.0,
    "c6_youzi_inflow": 15.0,
    "c7_scr90_convergence": 6.0,
    "c8_scr70_convergence": 8.0,
    "c9_sector_heat": 8.0,
    "c11_turnover5": 8.0,
}
EXPECTED_C9_NORMALIZATION_RULE = "30% industry percentile heat + 40% highest concept heat score + 30% underlying trend"
TNF_HEADER = 50
TNF_RECORD = 360
DAY_RECORD = struct.Struct("<IIIIIfII")
DAY_INPUT_SCHEMA = "CONVERTIBLE-BOND-DAY-INPUT-MANIFEST-2"
DAY_INPUT_BINDING_MODE = "immutable_tail_snapshot_pre_and_post"
DAY_INPUT_TAIL_RECORD_LIMIT = 260
DAY_INPUT_STABLE_CAPTURE_PASSES = 2
SOURCE_BINDING_MODE = "stable_sha256_pre_and_post_run"
TDX_DAY_UPDATE_RACE = "TDX_DAY_UPDATE_RACE"
BOND_PREFIXES = ("110", "111", "113", "118", "123", "127", "128", "132")
MARKET_BY_FLAG = {"1": "sh", "0": "sz"}
TERM_DATE_STATUSES = {"FIELD_ABSENT", "MISSING", "INVALID_FORMAT", "INVALID_CALENDAR", "VALID"}
TRUSTED_TDX_ROOT = Path(r"C:\new_tdx_mock")
TRUSTED_VIPDOC_ROOT = TRUSTED_TDX_ROOT / "vipdoc"
TRUSTED_HQ_CACHE = TRUSTED_TDX_ROOT / "T0002" / "hq_cache"
TRUSTED_SOURCE_PATHS = {
    "convertible_bond_master": TRUSTED_HQ_CACHE / "speckzzdata.txt",
    "tdx_hub": Path(r"D:\C盘转移\日志\codex\skills\tdx-local-hub\scripts\tdx_hub.py"),
    "industry_membership": TRUSTED_HQ_CACHE / "tdxhy.cfg",
    "industry_names": TRUSTED_HQ_CACHE / "tdxzs3.cfg",
    "concept_membership": TRUSTED_HQ_CACHE / "infoharbor_block.dat",
    "tnf.sh": TRUSTED_HQ_CACHE / "shs.tnf",
    "tnf.sz": TRUSTED_HQ_CACHE / "szs.tnf",
    "tq_runtime": TRUSTED_TDX_ROOT / "PYPlugins" / "user" / "tqcenter.py",
    "tdx_formula_store": TRUSTED_TDX_ROOT / "T0002" / "PriGS.dat",
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


def _personal_kb_finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def recompute_personal_kb_confirmation(item: dict[str, Any]) -> dict[str, Any]:
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


def personal_kb_ranking_key(item: dict[str, Any]) -> tuple[float, float, bool, str]:
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


def clip(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def close(a: float, b: float, tol: float = 0.0011) -> bool:
    return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a) - float(b)) <= tol


def same_path(left: Any, right: Path) -> bool:
    try:
        def identity(value: Any) -> str:
            resolved = str(Path(str(value)).resolve())
            if resolved.startswith("\\\\?\\UNC\\"):
                resolved = "\\\\" + resolved[8:]
            elif resolved.startswith("\\\\?\\"):
                resolved = resolved[4:]
            return resolved.casefold()

        return identity(left) == identity(right)
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def _is_plain_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _path_key(value: Any) -> str:
    if not isinstance(value, str) or not value:
        return ""
    try:
        return str(Path(value).resolve()).casefold()
    except (OSError, RuntimeError, TypeError, ValueError):
        return ""


def _is_trusted_day_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        Path(value).resolve().relative_to(TRUSTED_VIPDOC_ROOT.resolve())
        return True
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def _normalize_day_symbol(symbol: str) -> str:
    raw = symbol.strip().lower().replace("_", "")
    suffix_match = re.fullmatch(r"(\d{6})\.?(sh|sz|bj)", raw)
    if suffix_match:
        return suffix_match.group(2) + suffix_match.group(1)
    prefix_match = re.fullmatch(r"(sh|sz|bj)\.?(\d{6})", raw)
    if prefix_match:
        return prefix_match.group(1) + prefix_match.group(2)
    raw = raw.replace(".", "")
    if raw.startswith(("sh", "sz", "bj")) and len(raw) >= 8:
        return raw[:2] + raw[-6:]
    digits = "".join(char for char in raw if char.isdigit())
    if len(digits) < 6:
        raise ValueError(f"invalid symbol: {symbol}")
    code = digits[-6:]
    market = "sh" if code.startswith(("5", "6", "9")) else "bj" if code.startswith(("4", "8")) else "sz"
    return market + code


def _trusted_day_path(symbol: str) -> Path:
    value = _normalize_day_symbol(symbol)
    market = "bj" if value.startswith("bj") else value[:2]
    candidates = (
        TRUSTED_VIPDOC_ROOT / market / "lday" / f"{value}.day",
        TRUSTED_VIPDOC_ROOT / "xinzeng" / market / "lday" / f"{value}.day",
        TRUSTED_VIPDOC_ROOT / "xinzeng" / f"{value}.day",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def trusted_source_paths_exact(source_files: Any) -> bool:
    if not isinstance(source_files, dict):
        return False
    try:
        actual = {
            "convertible_bond_master": source_files["convertible_bond_master"]["path"],
            "tdx_hub": source_files["tdx_hub"]["path"],
            "industry_membership": source_files["industry_membership"]["path"],
            "industry_names": source_files["industry_names"]["path"],
            "concept_membership": source_files["concept_membership"]["path"],
            "tnf.sh": source_files["tnf"]["sh"]["path"],
            "tnf.sz": source_files["tnf"]["sz"]["path"],
            "tq_runtime": source_files["tq_runtime"]["path"],
            "tdx_formula_store": source_files["tdx_formula_store"]["path"],
        }
    except (KeyError, TypeError):
        return False
    return all(same_path(actual[name], trusted) for name, trusted in TRUSTED_SOURCE_PATHS.items())


def optional_close(a: Any, b: Any, tol: float = 0.0011) -> bool:
    if a is None or b is None:
        return a is None and b is None
    try:
        return close(float(a), float(b), tol)
    except (TypeError, ValueError):
        return False


def code7(code: str) -> str:
    flag = "1" if code.startswith(("5", "6", "9")) else "2" if code.startswith(("4", "8")) else "0"
    return flag + code


def independent_best_concept(concepts: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for item in concepts:
        heat = clip(float(item.get("heat_score") or 0.0) / 100.0)
        candidates.append({
            "name": item.get("name"),
            "heat_score": item.get("heat_score"),
            "mean_return_5d": item.get("mean_return_5d"),
            "up_ratio_5d": item.get("up_ratio_5d"),
            "normalized_heat": heat,
        })
    return min(
        candidates,
        key=lambda item: (-float(item["heat_score"] or 0.0), str(item["name"] or "")),
        default=None,
    )


def parse_tnf_codes(path: Path) -> set[str]:
    data = path.read_bytes()
    if len(data) < TNF_HEADER or (len(data) - TNF_HEADER) % TNF_RECORD:
        raise ValueError(f"invalid TNF layout: {path}")
    codes: set[str] = set()
    for offset in range(TNF_HEADER, len(data), TNF_RECORD):
        code = data[offset : offset + 6].decode("ascii", errors="strict").strip("\x00 ")
        if len(code) == 6 and code.isdigit():
            codes.add(code)
    return codes


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


def latest_tdx_benchmark_date(_payload: dict[str, Any]) -> str:
    path = TRUSTED_TDX_ROOT / "vipdoc" / "sh" / "lday" / "sh999999.day"
    size = path.stat().st_size
    if size < 32 or size % 32:
        raise ValueError(f"invalid benchmark day file: {path}")
    with path.open("rb") as handle:
        handle.seek(-32, 2)
        row = handle.read(32)
    date_value = struct.unpack("<I", row[:4])[0]
    return f"{date_value:08d}"


def parse_tnf_names(path: Path) -> dict[str, str]:
    data = path.read_bytes()
    if len(data) < TNF_HEADER or (len(data) - TNF_HEADER) % TNF_RECORD:
        raise ValueError(f"invalid TNF layout: {path}")
    names: dict[str, str] = {}
    for offset in range(TNF_HEADER, len(data), TNF_RECORD):
        row = data[offset : offset + TNF_RECORD]
        code = row[:6].decode("ascii", errors="strict").strip("\x00 ")
        if len(code) == 6 and code.isdigit():
            names[code] = decode_tnf_name(row[31:47])
    return names


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def parse_term_date(value: Any, field_present: bool = True) -> dict[str, Any]:
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


def independent_bond_records(
    payload: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    master = TRUSTED_SOURCE_PATHS["convertible_bond_master"]
    tnf_paths = {market: TRUSTED_SOURCE_PATHS[f"tnf.{market}"] for market in ("sh", "sz")}
    names = {market: parse_tnf_names(path) for market, path in tnf_paths.items()}
    cutoff = dt.datetime.strptime(str(payload["cutoff_trade_date"]), "%Y%m%d").date()
    records: dict[str, dict[str, Any]] = {}
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
    with master.open("r", encoding="utf-8", newline="") as handle:
        for line_no, fields in enumerate(csv.reader(handle), 1):
            diagnostics["source_rows"] += 1
            if len(fields) < 13:
                diagnostics["short_rows"] += 1
                continue
            flag = fields[0].strip()
            market = MARKET_BY_FLAG.get(flag)
            code = fields[1].strip()
            underlying = fields[2].strip()
            if market is None:
                diagnostics["unsupported_market_rows"] += 1
                if len(diagnostics["unsupported_market_sample"]) < 25:
                    diagnostics["unsupported_market_sample"].append(
                        {"line": line_no, "flag": flag, "code": code}
                    )
                continue
            conversion_price = finite_float(fields[3])
            remaining_wan = finite_float(fields[12])
            maturity = parse_term_date(fields[10], field_present=len(fields) > 10)
            last_trade = parse_term_date(fields[17] if len(fields) > 17 else None, field_present=len(fields) > 17)
            invalid_reasons: list[str] = []
            if not re.fullmatch(r"\d{6}", code):
                invalid_reasons.append("invalid_bond_code")
            if not re.fullmatch(r"\d{6}", underlying):
                invalid_reasons.append("invalid_underlying_code")
            if conversion_price is None or conversion_price <= 0:
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
                        "maturity_date": {
                            key: value.isoformat() if isinstance(value, dt.date) else value
                            for key, value in maturity.items()
                        },
                        "known_last_trade_date": {
                            key: value.isoformat() if isinstance(value, dt.date) else value
                            for key, value in last_trade.items()
                        },
                    })
                continue
            not_current_reasons: list[str] = []
            if maturity["date"] and maturity["date"] <= cutoff:
                not_current_reasons.append("matured_on_or_before_cutoff")
            if last_trade["date"] and last_trade["date"] <= cutoff:
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
            underlying_market = "sh" if underlying.startswith(("5", "6", "9")) else "bj" if underlying.startswith(("4", "8")) else "sz"
            symbol = f"{code}.{market.upper()}"
            if symbol in records:
                diagnostics["duplicate_symbols"].append(symbol)
                diagnostics["invalid_or_unresolved_source_rows"] += 1
                continue
            tnf_confirmed = code in names.get(market, {})
            if not tnf_confirmed:
                diagnostics["source_current_candidate_missing_tnf"].append(symbol)
            records[symbol] = {
                "line": line_no,
                "market": market,
                "code": code,
                "symbol": symbol,
                "name": names.get(market, {}).get(code, code),
                "tnf_confirmed": tnf_confirmed,
                "underlying": underlying,
                "underlying_symbol": f"{underlying}.{underlying_market.upper()}",
                "underlying_name": names.get(underlying_market, {}).get(underlying, underlying),
                "conversion_price": conversion_price,
                "remaining_wan": remaining_wan,
                "remaining_yi": remaining_wan / 10000.0,
                "maturity_date": str(maturity["raw"] or ""),
                "maturity_date_status": maturity["status"],
                "known_last_trade_date": str(last_trade["raw"] or ""),
                "known_last_trade_date_status": last_trade["status"],
                "known_last_trade_date_semantic": "not_announced" if last_trade["status"] == "MISSING" else "announced",
                "rating": fields[15].strip() if len(fields) > 15 else "",
            }
            diagnostics["accepted_rows"] += 1
            diagnostics["master_current_candidate_rows"] += 1
    diagnostics["classification_count"] = sum(
        int(diagnostics[key])
        for key in (
            "short_rows",
            "unsupported_market_rows",
            "invalid_or_unresolved_source_rows",
            "explained_not_current_rows",
            "master_current_candidate_rows",
        )
    )
    diagnostics["classification_complete"] = diagnostics["classification_count"] == diagnostics["source_rows"]
    diagnostics["tnf_reconciliation_complete"] = not diagnostics["source_current_candidate_missing_tnf"]
    diagnostics["integrity_complete"] = bool(
        diagnostics["short_rows"] == 0
        and diagnostics["invalid_or_unresolved_source_rows"] == 0
        and not diagnostics["duplicate_symbols"]
        and diagnostics["classification_complete"]
    )
    return records, diagnostics


def day_path(tdx_root: Path, symbol: str) -> Path:
    code, market = symbol.split(".")
    market = market.lower()
    prefix = f"{market}{code}"
    candidates = (
        tdx_root / "vipdoc" / market / "lday" / f"{prefix}.day",
        tdx_root / "vipdoc" / "xinzeng" / market / "lday" / f"{prefix}.day",
        tdx_root / "vipdoc" / "xinzeng" / f"{prefix}.day",
    )
    return next((path for path in candidates if path.is_file()), candidates[0])


def read_day_rows(tdx_root: Path, symbol: str, limit: int) -> list[dict[str, Any]]:
    path = day_path(tdx_root, symbol)
    if not path.is_file():
        return []
    size = path.stat().st_size
    if size == 0 or size % DAY_RECORD.size:
        raise ValueError(f"invalid day layout: {path}")
    count = size // DAY_RECORD.size
    read_count = min(count, limit)
    divisor = 10000.0 if symbol.split(".", 1)[0].startswith(BOND_PREFIXES) else 100.0
    rows: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        handle.seek((count - read_count) * DAY_RECORD.size)
        for _ in range(read_count):
            chunk = handle.read(DAY_RECORD.size)
            if len(chunk) != DAY_RECORD.size:
                raise ValueError(f"short day read: {path}")
            date_i, _open, _high, _low, close_i, amount, volume, _unused = DAY_RECORD.unpack(chunk)
            date_text = str(date_i)
            try:
                dt.datetime.strptime(date_text, "%Y%m%d")
            except ValueError as exc:
                raise ValueError(f"invalid day date {date_text}: {path}") from exc
            close_value = close_i / divisor
            amount_value = float(amount)
            if close_value <= 0 or not math.isfinite(amount_value) or amount_value < 0:
                raise ValueError(f"invalid day numeric value for {date_text}: {path}")
            if rows and date_text <= rows[-1]["date"]:
                raise ValueError(f"non-increasing day dates: {path}")
            rows.append({"date": date_text, "close": close_value, "amount": amount_value, "volume": int(volume)})
    return rows


def parse_day_tail(raw: bytes, symbol: str, source: str) -> list[dict[str, Any]]:
    if not raw or len(raw) % DAY_RECORD.size:
        raise ValueError(f"invalid frozen day layout: {source}")
    divisor = 10000.0 if symbol.split(".", 1)[0].startswith(BOND_PREFIXES) else 100.0
    rows: list[dict[str, Any]] = []
    for offset in range(0, len(raw), DAY_RECORD.size):
        chunk = raw[offset:offset + DAY_RECORD.size]
        date_i, _open, _high, _low, close_i, amount, volume, _unused = DAY_RECORD.unpack(chunk)
        date_text = str(date_i)
        try:
            dt.datetime.strptime(date_text, "%Y%m%d")
        except ValueError as exc:
            raise ValueError(f"invalid frozen day date {date_text}: {source}") from exc
        close_value = close_i / divisor
        amount_value = float(amount)
        if close_value <= 0 or not math.isfinite(amount_value) or amount_value < 0:
            raise ValueError(f"invalid frozen day numeric value for {date_text}: {source}")
        if rows and date_text <= rows[-1]["date"]:
            raise ValueError(f"non-increasing frozen day dates: {source}")
        rows.append({"date": date_text, "close": close_value, "amount": amount_value, "volume": int(volume)})
    return rows


class FrozenManifestDayReader:
    def __init__(self, raw_by_alias: dict[str, bytes | None], path_by_alias: dict[str, str]):
        self._raw_by_alias = dict(raw_by_alias)
        self._path_by_alias = dict(path_by_alias)

    def read_rows(self, symbol: str, limit: int) -> list[dict[str, Any]]:
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= DAY_INPUT_TAIL_RECORD_LIMIT:
            raise ValueError(f"invalid frozen day limit: {limit}")
        if symbol not in self._raw_by_alias:
            raise RuntimeError(f"day symbol was not captured in bound manifest: {symbol}")
        raw = self._raw_by_alias[symbol]
        if raw is None:
            return []
        rows = parse_day_tail(raw, symbol, self._path_by_alias[symbol])
        return rows[-limit:]


def ema(values: list[float], period: int) -> list[float]:
    alpha = 2.0 / (period + 1.0)
    output: list[float] = []
    for value in values:
        output.append(value if not output else alpha * value + (1.0 - alpha) * output[-1])
    return output


def recent_cross_dates(left: list[float], right: list[float], dates: list[str], lookback: int) -> list[str]:
    allowed = set(dates[-lookback:])
    return [
        dates[index]
        for index in range(1, len(dates))
        if dates[index] in allowed and left[index] > right[index] and left[index - 1] <= right[index - 1]
    ]


def newest_session_age(dates: list[str], calendar: list[str], window: int = 10) -> int | None:
    positions = {date: index for index, date in enumerate(calendar)}
    latest = len(calendar) - 1
    ages = [latest - positions[date] for date in dates if date in positions]
    valid = [age for age in ages if 0 <= age < window]
    return min(valid) if valid else None


def recompute_local_and_risk(
    payload: dict[str, Any],
    master: dict[str, Any],
    day_reader: Callable[[str, int], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    tdx_root = TRUSTED_TDX_ROOT
    cutoff = str(payload["cutoff_trade_date"])
    calendar = [str(value) for value in payload["benchmark_calendar"]]
    reader = day_reader or (lambda symbol, limit: read_day_rows(tdx_root, symbol, limit))
    bond_rows = [row for row in reader(master["symbol"], 260) if row["date"] <= cutoff]
    stock_rows = [row for row in reader(master["underlying_symbol"], 260) if row["date"] <= cutoff]
    bond_latest_date = bond_rows[-1]["date"] if bond_rows else None
    stock_latest_date = stock_rows[-1]["date"] if stock_rows else None
    bond_current = bond_latest_date == cutoff
    stock_current = stock_latest_date == cutoff
    bond_two_session_window = (
        len(bond_rows) >= 2
        and [row["date"] for row in bond_rows[-2:]] == calendar[-2:]
    )
    bond_six_session_window = (
        len(bond_rows) >= 6
        and [row["date"] for row in bond_rows[-6:]] == calendar[-6:]
    )
    bond_full_lookback = bond_six_session_window and float(bond_rows[-6]["close"]) > 0
    bond_turnover_lookback = (
        len(bond_rows) >= 5
        and [row["date"] for row in bond_rows[-5:]] == calendar[-5:]
    )
    stock_signal_available = (
        len(stock_rows) >= 30
        and [row["date"] for row in stock_rows[-6:]] == calendar[-6:]
        and float(stock_rows[-1]["close"]) > 0
    )
    bond_close = float(bond_rows[-1]["close"]) if bond_rows else None
    stock_close = float(stock_rows[-1]["close"]) if stock_rows else None
    conversion_value = (
        stock_close / float(master["conversion_price"]) * 100.0
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
        if bond_two_session_window
        and bond_close is not None
        and float(bond_rows[-2]["close"]) > 0
        else None
    )
    previous_5_volume_mean = (
        statistics.fmean(float(row["volume"]) for row in bond_rows[-6:-1])
        if bond_six_session_window
        else None
    )
    bond_volume_ratio_5d = (
        float(bond_rows[-1]["volume"]) / previous_5_volume_mean
        if previous_5_volume_mean is not None and previous_5_volume_mean > 0
        else None
    )
    turnover5 = (
        sum(float(row["volume"]) for row in bond_rows[-5:]) / (float(master["remaining_wan"]) * 10.0) * 100.0
        if bond_turnover_lookback
        else None
    )
    stock_closes = [float(row["close"]) for row in stock_rows]
    stock_dates = [str(row["date"]) for row in stock_rows]
    if stock_signal_available:
        ema3, ema21 = ema(stock_closes, 3), ema(stock_closes, 21)
        ignition_dates_10 = recent_cross_dates(ema3, ema21, stock_dates, 10)
        ignition_dates = [date for date in ignition_dates_10 if date in set(stock_dates[-5:])]
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
        buy_latest, buy_prev = buy[-1], buy[-2]
        ema5_latest, ema20_latest = ema5[-1], ema20[-1]
        big_bull_red = ema5_latest > ema20_latest
    else:
        ignition_dates_10 = []
        ignition_dates = []
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
    maturity_declared_status = str(master.get("maturity_date_status") or "")
    last_trade_declared_status = str(master.get("known_last_trade_date_status") or "")
    maturity_info = parse_term_date(
        master.get("maturity_date"),
        field_present=maturity_declared_status != "FIELD_ABSENT",
    )
    last_trade_info = parse_term_date(
        master.get("known_last_trade_date"),
        field_present=last_trade_declared_status != "FIELD_ABSENT",
    )
    maturity = maturity_info["date"]
    last_trade = last_trade_info["date"]
    veto: list[str] = []
    if not master.get("tnf_confirmed", False):
        veto.append("source_current_candidate_missing_tnf")
    if not bond_rows:
        veto.append("bond_history_missing")
    elif not bond_current:
        veto.append(f"bond_latest_date_mismatch:{bond_latest_date}:{cutoff}")
    if bond_rows and len(bond_rows) < 6:
        veto.append(f"insufficient_bond_history_lt_6:{len(bond_rows)}")
    elif bond_rows and not bond_full_lookback:
        veto.append("bond_last_6_sessions_mismatch")
    if not stock_rows:
        veto.append("underlying_history_missing")
    elif not stock_signal_available:
        veto.append(f"underlying_signal_history_unavailable:{len(stock_rows)}:{stock_latest_date}")
    if maturity_declared_status and maturity_declared_status != maturity_info["status"]:
        veto.append("maturity_date_status_mismatch")
    if last_trade_declared_status and last_trade_declared_status != last_trade_info["status"]:
        veto.append("known_last_trade_date_status_mismatch")
    if maturity_info["status"] != "VALID":
        veto.append(f"maturity_date_{str(maturity_info['status']).lower()}")
    if last_trade_info["status"] not in ("VALID", "MISSING"):
        veto.append(f"known_last_trade_date_{str(last_trade_info['status']).lower()}")
    if maturity and last_trade and last_trade > maturity:
        veto.append("known_last_trade_after_maturity")
    if maturity and (maturity - today).days <= 60:
        veto.append(f"maturity_within_60d:{maturity.isoformat()}")
    if last_trade and (last_trade - today).days <= 20:
        veto.append(f"known_last_trade_within_20d:{last_trade.isoformat()}")
    if "退" in str(master["name"]):
        veto.append("bond_name_delisting_marker")
    if "ST" in str(master["underlying_name"]).upper() or "退" in str(master["underlying_name"]):
        veto.append("underlying_st_or_delisting_marker")
    latest_volume = float(bond_rows[-1]["volume"]) if bond_rows else None
    if latest_volume is not None and latest_volume <= 0:
        veto.append("latest_volume_zero")
    warnings: list[str] = []
    if float(master["remaining_yi"]) <= 0.5:
        warnings.append("very_small_remaining_scale_le_0_5yi")
    if bond_close is not None and bond_close >= 150.0:
        warnings.append("high_bond_price_ge_150")
    if premium is not None and premium >= 80.0:
        warnings.append("high_premium_ge_80pct")
    if weekly_return is not None and weekly_return <= -10.0:
        warnings.append("weekly_drop_ge_10pct")
    risk_level = "RED" if veto else "YELLOW" if warnings else "GREEN"
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
        "turnover_5d_pct": turnover5,
        "ignition_local_cross_dates": ignition_dates,
        "ignition_local_cross_dates_10": ignition_dates_10,
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
        "known_last_trade_date_semantic_checked": (
            "not_announced" if last_trade_info["status"] == "MISSING" else "announced"
        ),
        "risk_veto_reasons": veto,
        "risk_warning_labels": warnings,
        "risk_level": risk_level,
    }


def recompute_normalized(criterion_id: str, raw: dict[str, Any]) -> float:
    if criterion_id == "c1_price_activity":
        value = raw.get("weekly_return_pct")
        return 0.0 if value is None else clip(float(value) / 5.0)
    if criterion_id == "c2_remaining_scale":
        value = float(raw["remaining_yi"])
        return 1.0 if value <= 5.0 else clip((15.0 - value) / 10.0)
    if criterion_id == "c3_premium":
        value = raw.get("premium_pct")
        if value is None:
            return 0.0
        value = float(value)
        if value <= 10.0:
            return 1.0
        if value <= 50.0:
            return 1.0 - 0.5 * (value - 10.0) / 40.0
        if value <= 100.0:
            return 0.5 * (100.0 - value) / 50.0
        return 0.0
    if criterion_id == "c4_golden_ignition":
        age = raw.get("newest_age_sessions")
        return 0.0 if age is None else max(0.5, 1.0 - float(age) / 18.0)
    if criterion_id == "c5_feilong_cross":
        age = raw.get("newest_age_sessions")
        crosses = raw.get("valid_below20_crosses") or []
        if age is not None and crosses:
            newest = max(crosses, key=lambda item: str(item["date"]))
            level = max(float(newest["wave"]), float(newest["segment"]))
            low_position = min(1.0, max(0.35, (25.0 - level) / 15.0))
            recency = max(0.5, 1.0 - float(age) / 18.0)
            return 0.75 * recency + 0.25 * low_position
        wave, segment = raw.get("latest_wave"), raw.get("latest_segment")
        if wave is None or segment is None:
            return 0.0
        wave, segment = float(wave), float(segment)
        if wave < 20.0 and segment < 20.0 and wave > segment:
            return 0.40
        if wave < 20.0 and segment < 20.0:
            return 0.20
        if wave < 30.0 and segment < 30.0 and wave > segment:
            return 0.15
        return 0.0
    if criterion_id == "c6_youzi_inflow":
        if raw.get("buy_latest") is None or raw.get("buy_prev") is None:
            return 0.0
        latest = float(raw["buy_latest"])
        previous = float(raw["buy_prev"])
        return 0.25 * float(latest > 0.0) + 0.35 * float(latest > previous) + 0.40 * float(bool(raw.get("cross_dates_5")))
    if criterion_id == "c7_scr90_convergence":
        shrink = raw.get("shrink90_pp")
        relative = raw.get("relative_shrink90")
        absolute_norm = 0.0 if shrink is None else clip(float(shrink) / 10.0)
        relative_norm = 0.0 if relative is None else clip(float(relative) / (1.0 / 3.0))
        return 0.50 * absolute_norm + 0.50 * relative_norm
    if criterion_id == "c8_scr70_convergence":
        value = raw.get("shrink70_pp")
        return 0.0 if value is None else clip(float(value) / 3.0)
    if criterion_id == "c9_sector_heat":
        industry = float(raw.get("industry_normalized") or 0.0)
        best = raw.get("best_concept")
        if best:
            concept = clip(float(best.get("heat_score") or 0.0) / 100.0)
            if not close(concept, float(best["normalized_heat"]), 0.0003):
                raise AssertionError("best concept heat mismatch")
        else:
            concept = 0.0
        trend = clip(float(raw.get("underlying_trend_score") or 0.0))
        return 0.30 * industry + 0.40 * concept + 0.30 * trend
    if criterion_id == "c11_turnover5":
        value = raw.get("turnover_5d_pct")
        return 0.0 if value is None else clip(float(value) / 150.0)
    raise KeyError(criterion_id)


def walk_path_nodes(node: Any):
    if isinstance(node, dict) and "path" in node:
        yield node
        return
    if isinstance(node, dict):
        for value in node.values():
            yield from walk_path_nodes(value)


def valid_source_node(node: dict[str, Any]) -> bool:
    return (
        isinstance(node.get("path"), str)
        and isinstance(node.get("size"), int)
        and isinstance(node.get("sha256"), str)
        and len(node["sha256"]) == 64
        and all(char in "0123456789abcdef" for char in node["sha256"].lower())
    )


def validate_day_input_manifest(
    manifest: dict[str, Any],
    run_id: str,
    cutoff: str,
) -> tuple[bool, bool, list[dict[str, Any]], FrozenManifestDayReader | None]:
    raw_inputs = manifest.get("inputs")
    inputs = raw_inputs if isinstance(raw_inputs, list) else []
    diagnostics: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    all_aliases: list[str] = []
    existing_count = 0
    missing_count = 0
    raw_by_alias: dict[str, bytes | None] = {}
    path_by_alias: dict[str, str] = {}

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
        key = _path_key(path_text)
        unique = bool(key) and key not in seen_paths
        if key:
            seen_paths.add(key)
        if not unique:
            mismatches.append("path_unique")
        trusted_tdx_root = _is_trusted_day_path(path_text)
        if not trusted_tdx_root:
            mismatches.append("trusted_tdx_root")

        expected_exists = node.get("exists")
        expected_valid_layout = node.get("valid_layout")
        if not isinstance(expected_exists, bool):
            mismatches.append("exists_boolean")
        elif expected_exists:
            existing_count += 1
        else:
            missing_count += 1
        if not isinstance(expected_valid_layout, bool):
            mismatches.append("valid_layout_boolean")

        if expected_exists is True:
            file_size = node.get("file_size")
            mtime_ns = node.get("mtime_ns")
            tail_record_count = node.get("tail_record_count")
            tail_offset = node.get("tail_offset")
            tail_size = node.get("tail_size")
            tail_sha256 = node.get("tail_sha256")
            expected_record_count = (
                file_size // DAY_RECORD.size
                if _is_plain_int(file_size) and file_size > 0 and file_size % DAY_RECORD.size == 0
                else -1
            )
            expected_tail_records = min(expected_record_count, DAY_INPUT_TAIL_RECORD_LIMIT) if expected_record_count >= 0 else -1
            node_field_contract = bool(
                expected_valid_layout is True
                and expected_record_count > 0
                and _is_plain_int(mtime_ns)
                and mtime_ns >= 0
                and _is_plain_int(tail_record_count)
                and tail_record_count == expected_tail_records
                and _is_plain_int(tail_size)
                and tail_size == expected_tail_records * DAY_RECORD.size
                and _is_plain_int(tail_offset)
                and tail_offset == file_size - tail_size
                and isinstance(tail_sha256, str)
                and re.fullmatch(r"[0-9a-f]{64}", tail_sha256) is not None
            )
            if not node_field_contract:
                mismatches.append("existing_node_v2_fields")
        elif expected_exists is False:
            node_field_contract = expected_valid_layout is False
            if not node_field_contract:
                mismatches.append("missing_node_v2_fields")
        else:
            node_field_contract = False

        alias_routes: dict[str, str] = {}
        resolved_aliases_current = aliases_contract and bool(key)
        for alias in aliases:
            try:
                alias_path = _trusted_day_path(alias)
                alias_routes[alias] = str(alias_path)
                if _path_key(str(alias_path)) != key:
                    resolved_aliases_current = False
                    mismatches.append(f"alias_routing:{alias}")
            except (OSError, RuntimeError, TypeError, ValueError) as exc:
                resolved_aliases_current = False
                alias_routes[alias] = f"{type(exc).__name__}:{exc}"
                mismatches.append(f"alias_routing:{alias}")

        actual: dict[str, Any]
        current = False
        if expected_exists is True and path is not None:
            try:
                before = path.stat()
                valid_layout = before.st_size > 0 and before.st_size % DAY_RECORD.size == 0
                record_count = before.st_size // DAY_RECORD.size if valid_layout else 0
                actual_tail_records = min(record_count, DAY_INPUT_TAIL_RECORD_LIMIT)
                actual_tail_size = actual_tail_records * DAY_RECORD.size
                actual_tail_offset = before.st_size - actual_tail_size
                with path.open("rb") as handle:
                    handle.seek(actual_tail_offset)
                    raw = handle.read(actual_tail_size)
                after = path.stat()
                stable_read = bool(
                    (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
                    and len(raw) == actual_tail_size
                )
                actual = {
                    "lookup_symbols": aliases,
                    "path": str(path.resolve()),
                    "exists": True,
                    "valid_layout": valid_layout,
                    "file_size": after.st_size,
                    "mtime_ns": after.st_mtime_ns,
                    "tail_record_count": actual_tail_records,
                    "tail_offset": actual_tail_offset,
                    "tail_size": actual_tail_size,
                    "tail_sha256": hashlib.sha256(raw).hexdigest(),
                    "stable_read": stable_read,
                    "alias_routes": alias_routes,
                }
                fields = (
                    "lookup_symbols",
                    "exists",
                    "valid_layout",
                    "file_size",
                    "mtime_ns",
                    "tail_record_count",
                    "tail_offset",
                    "tail_size",
                    "tail_sha256",
                )
                differing_fields = [field for field in fields if node.get(field) != actual.get(field)]
                if not same_path(node.get("path"), Path(actual["path"])):
                    differing_fields.append("path")
                if not stable_read:
                    differing_fields.append("stable_read")
                mismatches.extend(f"current_field:{field}" for field in differing_fields)
                current = bool(
                    not differing_fields
                    and resolved_aliases_current
                    and trusted_tdx_root
                )
                if current:
                    for alias in aliases:
                        raw_by_alias[alias] = raw
                        path_by_alias[alias] = str(path.resolve())
            except (OSError, RuntimeError, TypeError, ValueError) as exc:
                actual = {"error": f"{type(exc).__name__}:{exc}", "alias_routes": alias_routes}
                mismatches.append("current_read_error")
        elif expected_exists is False and path is not None:
            try:
                actual_is_file = path.is_file()
                actual = {
                    "lookup_symbols": aliases,
                    "path": str(path.resolve()),
                    "exists": actual_is_file,
                    "valid_layout": False,
                    "alias_routes": alias_routes,
                }
                current = bool(
                    not actual_is_file
                    and node.get("valid_layout") is False
                    and same_path(node.get("path"), Path(actual["path"]))
                    and resolved_aliases_current
                    and trusted_tdx_root
                )
                if actual_is_file:
                    mismatches.append("current_field:exists")
                elif current:
                    for alias in aliases:
                        raw_by_alias[alias] = None
                        path_by_alias[alias] = str(path.resolve())
            except (OSError, RuntimeError, TypeError, ValueError) as exc:
                actual = {"error": f"{type(exc).__name__}:{exc}", "alias_routes": alias_routes}
                mismatches.append("current_read_error")
        else:
            actual = {"error": "invalid manifest path or exists flag", "alias_routes": alias_routes}
            mismatches.append("current_read_unavailable")

        node_contract = bool(
            isinstance(raw_node, dict)
            and aliases_contract
            and unique
            and trusted_tdx_root
            and isinstance(expected_exists, bool)
            and isinstance(expected_valid_layout, bool)
            and node_field_contract
        )
        diagnostics.append({
            "index": index,
            "path": path_text,
            "lookup_symbols": aliases,
            "unique": unique,
            "trusted_tdx_root": trusted_tdx_root,
            "resolved_aliases_current": resolved_aliases_current,
            "contract": node_contract,
            "current": current,
            "mismatches": mismatches,
            "expected": node,
            "actual": actual,
        })

    manifest_conditions = {
        "schema_v2": manifest.get("schema") == DAY_INPUT_SCHEMA,
        "binding_mode_exact": manifest.get("binding_mode") == DAY_INPUT_BINDING_MODE,
        "run_id_exact": manifest.get("run_id") == run_id,
        "cutoff_trade_date_exact": manifest.get("cutoff_trade_date") == cutoff,
        "tail_record_limit_260": manifest.get("tail_record_limit") == DAY_INPUT_TAIL_RECORD_LIMIT,
        "stable_capture_passes_2": manifest.get("stable_capture_passes") == DAY_INPUT_STABLE_CAPTURE_PASSES,
        "capture_attempt_valid": _is_plain_int(manifest.get("capture_attempt")) and manifest.get("capture_attempt") >= 1,
        "input_count_exact": _is_plain_int(manifest.get("input_count")) and manifest.get("input_count") == len(inputs),
        "alias_count_exact": bool(
            _is_plain_int(manifest.get("alias_count"))
            and manifest.get("alias_count") == len(all_aliases)
            and manifest.get("alias_count") == len(set(all_aliases))
        ),
        "existing_input_count_exact": bool(
            _is_plain_int(manifest.get("existing_input_count"))
            and manifest.get("existing_input_count") == existing_count
        ),
        "missing_input_count_exact": bool(
            _is_plain_int(manifest.get("missing_input_count"))
            and manifest.get("missing_input_count") == missing_count
        ),
        "all_requested_symbols_mapped": manifest.get("all_requested_symbols_mapped") is True,
        "all_existing_layouts_valid": manifest.get("all_existing_layouts_valid") is True,
        "missing_inputs_explicit": manifest.get("missing_inputs_explicit") is True,
        "complete": manifest.get("complete") is True,
        "inputs_nonempty": bool(inputs),
    }
    top_contract = all(manifest_conditions.values())
    diagnostics.insert(0, {
        "index": None,
        "path": "<manifest>",
        "lookup_symbols": [],
        "unique": True,
        "trusted_tdx_root": True,
        "resolved_aliases_current": True,
        "contract": top_contract,
        "current": True,
        "mismatches": [name for name, passed in manifest_conditions.items() if not passed],
        "expected": {
            "schema": DAY_INPUT_SCHEMA,
            "binding_mode": DAY_INPUT_BINDING_MODE,
            "run_id": run_id,
            "cutoff_trade_date": cutoff,
            "tail_record_limit": DAY_INPUT_TAIL_RECORD_LIMIT,
            "stable_capture_passes": DAY_INPUT_STABLE_CAPTURE_PASSES,
        },
        "actual": {name: manifest.get(name) for name in (
            "schema",
            "binding_mode",
            "run_id",
            "cutoff_trade_date",
            "tail_record_limit",
            "stable_capture_passes",
            "capture_attempt",
            "input_count",
            "alias_count",
            "existing_input_count",
            "missing_input_count",
            "all_requested_symbols_mapped",
            "all_existing_layouts_valid",
            "missing_inputs_explicit",
            "complete",
        )},
    })
    node_diagnostics = diagnostics[1:]
    contract_ok = bool(top_contract and node_diagnostics and all(item["contract"] for item in node_diagnostics))
    current_ok = bool(contract_ok and all(item["current"] for item in node_diagnostics))
    frozen_reader = FrozenManifestDayReader(raw_by_alias, path_by_alias) if current_ok else None
    return contract_ok, current_ok, diagnostics, frozen_reader


def emit_day_update_race(
    output_path: Path,
    run_id: str,
    attempt: int,
    checks: dict[str, bool],
    diagnostics: list[dict[str, Any]],
) -> int:
    mismatch_paths = [
        str(item.get("path") or "")
        for item in diagnostics
        if item.get("path") != "<manifest>" and not item.get("current")
    ]
    if not mismatch_paths:
        mismatch_paths = ["<day-input-manifest>"]
    event = {
        "schema": "CONVERTIBLE-BOND-VERIFY-FAILURE-1",
        "status": "FAIL",
        "failure_code": TDX_DAY_UPDATE_RACE,
        "retryable": True,
        "script": str(Path(__file__).resolve()),
        "run_id": run_id,
        "attempt": attempt,
        "error": f"{TDX_DAY_UPDATE_RACE}:day_input_manifest_changed:count={len(mismatch_paths)}",
        "mismatch_count": len(mismatch_paths),
        "mismatch_paths": mismatch_paths,
    }
    failure = {
        "status": "FAIL",
        "schema": "TDX-CONVERTIBLE-BOND-VERIFY-FAIL-1",
        "run_id": run_id,
        "attempt": attempt,
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "diagnostics": {"day_input_mismatches": diagnostics},
        "retry_event": event,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output_path, failure)
    print(json.dumps(event, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    return 3


def emit_day_manifest_failure(
    output_path: Path,
    run_id: str,
    attempt: int,
    checks: dict[str, bool],
    diagnostics: list[dict[str, Any]],
) -> int:
    failure = {
        "status": "FAIL",
        "schema": "TDX-CONVERTIBLE-BOND-WEIGHTED-VERIFY-V5",
        "run_id": run_id,
        "attempt": attempt,
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "diagnostics": {"day_input_mismatches": diagnostics},
        "top10": [],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output_path, failure)
    print(json.dumps({
        "status": "FAIL",
        "output": str(output_path),
        "failed_checks": failure["failed_checks"],
    }, ensure_ascii=False, sort_keys=True))
    return 2


def normalize_formula_series(raw: Any, cutoff: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return rows
    for index, item in enumerate(raw):
        if isinstance(item, dict):
            date = str(item.get("Date") or "")
            value = item.get("Value")
        else:
            date = ""
            value = item
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number) and (not date or date <= cutoff):
            rows.append({"date": date or f"index-{index}", "value": number})
    return rows


def recompute_feilong(node: dict[str, Any] | None, cutoff: str) -> dict[str, Any]:
    wave = normalize_formula_series((node or {}).get("波"), cutoff)
    segment = normalize_formula_series((node or {}).get("段"), cutoff)
    wave_by_date = {item["date"]: item["value"] for item in wave}
    segment_by_date = {item["date"]: item["value"] for item in segment}
    dates = sorted(set(wave_by_date) & set(segment_by_date))
    recent_dates = set(dates[-5:])
    score_dates = set(dates[-10:])
    recent_crosses: list[dict[str, Any]] = []
    score_crosses: list[dict[str, Any]] = []
    for index in range(1, len(dates)):
        date, previous = dates[index], dates[index - 1]
        if (
            date in score_dates
            and wave_by_date[date] > segment_by_date[date]
            and wave_by_date[previous] <= segment_by_date[previous]
        ):
            cross = {
                "date": date,
                "wave": wave_by_date[date],
                "segment": segment_by_date[date],
                "prev_wave": wave_by_date[previous],
                "prev_segment": segment_by_date[previous],
                "below20": wave_by_date[date] < 20 and segment_by_date[date] < 20,
            }
            score_crosses.append(cross)
            if date in recent_dates and cross["below20"]:
                recent_crosses.append(cross)
    return {
        "pass": bool(recent_crosses),
        "recent_crosses": recent_crosses,
        "score_window_crosses": score_crosses,
        "latest_date": dates[-1] if dates else None,
        "latest_wave": wave_by_date[dates[-1]] if dates else None,
        "latest_segment": segment_by_date[dates[-1]] if dates else None,
        "point_count": len(dates),
    }


def validate_exact_formula_window(
    raw: Any,
    cutoff: str,
    required_dates: list[str],
) -> dict[str, Any]:
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
        value = finite_float(item.get("Value"))
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
    required = set(required_dates)
    return {
        "complete": not reasons,
        "reasons": reasons,
        "required_dates": list(required_dates),
        "actual_dates": dates,
        "actual_tail_dates": actual_tail_dates,
        "point_count": len(parsed),
        "values": {item["date"]: item["value"] for item in parsed if item["date"] in required},
    }


def recompute_scr(
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
            "scr90_previous": None,
            "scr90_latest": None,
            "scr90_change_1d_pp": None,
            "reason": "exact_benchmark_window_unavailable",
        }
    old_date, previous_date, latest_date = required_dates[0], required_dates[-2], required_dates[-1]
    values90 = check90["values"]
    values70 = check70["values"]
    shrink90 = values90[old_date] - values90[latest_date]
    shrink70 = values70[old_date] - values70[latest_date]
    scr90_change_1d = values90[latest_date] - values90[previous_date]
    relative_shrink90 = shrink90 / values90[old_date] if values90[old_date] > 0 else None
    return {
        "pass90": shrink90 >= 10.0 and relative_shrink90 is not None and relative_shrink90 >= (1.0 / 3.0),
        "pass70": shrink70 >= 3.0,
        "window_complete": True,
        "required_dates": list(required_dates),
        "old_date": old_date,
        "previous_date": previous_date,
        "latest_date": latest_date,
        "scr90_old": values90[old_date],
        "scr90_previous": values90[previous_date],
        "scr90_latest": values90[latest_date],
        "scr90_change_1d_pp": scr90_change_1d,
        "shrink90_pp": shrink90,
        "relative_shrink90": relative_shrink90,
        "scr70_old": values70[old_date],
        "scr70_latest": values70[latest_date],
        "shrink70_pp": shrink70,
        "point_count": len(required_dates),
    }


def recompute_formula_hits(node: dict[str, Any] | None, cutoff: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for field in ("OUTPUT59", "OUTPUT60", "OUTPUT61"):
        for item in normalize_formula_series((node or {}).get(field), cutoff)[-5:]:
            if float(item["value"]) > 0:
                hits.append({"field": field, **item})
    return hits


def deep_close(left: Any, right: Any, tolerance: float = 0.0011) -> bool:
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(deep_close(left[key], right[key], tolerance) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(deep_close(a, b, tolerance) for a, b in zip(left, right))
    if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(right, (int, float)) and not isinstance(right, bool):
        return math.isfinite(float(left)) and math.isfinite(float(right)) and abs(float(left) - float(right)) <= tolerance
    return left == right


def _legacy_v3_main() -> int:
    parser = argparse.ArgumentParser(description="Independent verifier for weighted convertible-bond ranking")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--formula-evidence", type=Path, default=None)
    parser.add_argument("--day-input-manifest", type=Path, default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}
    checks["scan_status_pass"] = payload.get("status") == "PASS"
    checks["schema_v3"] = payload.get("schema") == "TDX-CONVERTIBLE-BOND-WEIGHTED-SCAN-V3"
    run_id = str(payload.get("run_id") or "")
    checks["run_id_exact"] = bool(run_id) and (args.run_id is None or run_id == str(args.run_id))

    evidence_meta = payload.get("formula_evidence") or {}
    evidence_path = args.formula_evidence or Path(str(evidence_meta.get("path") or ""))
    try:
        formula_evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig")) if evidence_path.is_file() else {}
    except (OSError, json.JSONDecodeError):
        formula_evidence = {}
    checks["formula_evidence_binding_exact"] = bool(
        evidence_path.is_file()
        and evidence_path.stat().st_size == int(evidence_meta.get("size", -1))
        and sha256(evidence_path) == evidence_meta.get("sha256")
        and formula_evidence.get("schema") == "CONVERTIBLE-BOND-FORMULA-EVIDENCE-1"
        and formula_evidence.get("run_id") == run_id
        and formula_evidence.get("cutoff_trade_date") == payload.get("cutoff_trade_date")
    )
    day_meta = payload.get("day_input_manifest") or {}
    day_manifest_path = args.day_input_manifest or Path(str(day_meta.get("path") or ""))
    try:
        day_manifest = json.loads(day_manifest_path.read_text(encoding="utf-8-sig")) if day_manifest_path.is_file() else {}
    except (OSError, json.JSONDecodeError):
        day_manifest = {}
    checks["day_input_manifest_binding_exact"] = bool(
        day_manifest_path.is_file()
        and day_manifest_path.stat().st_size == int(day_meta.get("size", -1))
        and sha256(day_manifest_path) == day_meta.get("sha256")
    )
    day_manifest_contract, day_inputs_current, day_input_checks, _legacy_frozen_day_reader = validate_day_input_manifest(
        day_manifest,
        run_id,
        str(payload.get("cutoff_trade_date") or ""),
    )
    checks["day_input_manifest_v2_contract_exact"] = day_manifest_contract
    checks["day_input_manifest_current"] = day_inputs_current

    model = payload.get("score_model") or {}
    criteria = model.get("criteria") or []
    ids = tuple(item.get("id") for item in criteria)
    weights = {item.get("id"): float(item.get("weight")) for item in criteria}
    checks["weights_count_10"] = len(criteria) == 10 and len(set(ids)) == 10 and ids == EXPECTED_IDS
    checks["weights_exact"] = weights == EXPECTED_WEIGHTS
    checks["weights_sum_100"] = close(sum(weights.values()), 100.0, 1e-9) and close(float(model.get("weight_sum")), 100.0, 1e-9)
    checks["big_bull_zero_score"] = all("big_bull" not in criterion_id for criterion_id in ids) and "contributes zero score" in str(model.get("big_bull_rule"))

    results = payload.get("all_results") or []
    symbols = [item.get("symbol") for item in results]
    checks["pool_unique_and_complete"] = (
        len(results) == int(payload.get("analyzed_count", -1)) == int(payload.get("ranked_count", -1))
        and len(symbols) == len(set(symbols))
        and all(item.get("rank") == index for index, item in enumerate(results, 1))
    )

    master_records = independent_bond_records(payload)
    source_files = payload.get("source_files") or {}
    tdx_root = TRUSTED_TDX_ROOT
    heat = recompute_heat(
        tdx_root,
        TRUSTED_SOURCE_PATHS["industry_membership"],
        TRUSTED_SOURCE_PATHS["industry_names"],
        TRUSTED_SOURCE_PATHS["concept_membership"],
        str(payload.get("cutoff_trade_date") or ""),
        [str(value) for value in payload.get("benchmark_calendar") or []],
    )
    heat_stock_industry = heat["stock_industry"]
    heat_industries = heat["industry_heat"]
    heat_concepts = heat["concept_by_code"]
    heat_values_exact = bool(results)
    heat_mismatch_symbols: list[str] = []
    local_values_exact = bool(results)
    master_mapping_exact = bool(results)
    risk_values_exact = bool(results)
    local_conditions_exact = bool(results)
    local_condition_mismatches: list[dict[str, Any]] = []
    component_raw_bindings_exact = bool(results)
    component_raw_mismatches: list[str] = []
    recomputed_local_by_symbol: dict[str, dict[str, Any]] = {}
    evidence_formulas_for_local = formula_evidence.get("formulas") or {}
    for item in results:
        symbol = str(item.get("symbol") or "")
        master = master_records.get(symbol)
        if master is None:
            master_mapping_exact = False
            local_values_exact = False
            risk_values_exact = False
            local_conditions_exact = False
            continue
        master_mapping_exact &= (
            item.get("name") == master["name"]
            and item.get("underlying_symbol") == master["underlying_symbol"]
            and item.get("underlying_name") == master["underlying_name"]
            and close(item.get("conversion_price"), master["conversion_price"])
            and close(item.get("remaining_yi"), master["remaining_yi"])
        )
        underlying_key = code7(str(item.get("underlying_symbol") or "").split(".", 1)[0])
        expected_industry_code = heat_stock_industry.get(underlying_key)
        expected_industry = heat_industries.get(expected_industry_code or "", {})
        expected_concepts = (heat_concepts.get(underlying_key) or [])[:5]
        heat_match = deep_close(item.get("industry") or {}, expected_industry, 1e-9) and deep_close(
            item.get("top_concepts") or [], expected_concepts, 1e-9
        )
        if not heat_match and len(heat_mismatch_symbols) < 25:
            heat_mismatch_symbols.append(symbol)
        heat_values_exact &= heat_match
        recalculated = recompute_local_and_risk(payload, item, master)
        if recalculated is None:
            local_values_exact = False
            risk_values_exact = False
            local_conditions_exact = False
            continue
        recomputed_local_by_symbol[symbol] = recalculated
        for field in (
            "bond_close",
            "stock_close",
            "conversion_value",
            "premium_pct",
            "weekly_return_pct",
            "turnover_5d_pct",
            "ema3_latest",
            "ema21_latest",
            "youzi_buy_latest",
            "youzi_buy_prev",
            "stock_return5_pct",
            "stock_ma5_latest",
            "stock_ma10_latest",
            "stock_ma20_latest",
            "underlying_trend_score",
        ):
            local_values_exact &= optional_close(item.get(field), recalculated[field])
        for field in (
            "bond_latest_date",
            "stock_latest_date",
            "bond_history_points",
            "stock_history_points",
            "bond_current",
            "stock_current",
            "bond_full_lookback",
            "bond_turnover_lookback",
            "stock_signal_available",
            "stock_ema_bullish",
            "stock_ma_bullish",
        ):
            local_values_exact &= item.get(field) == recalculated[field]
        local_values_exact &= bool(item.get("big_bull_red_preference")) is bool(recalculated["big_bull_red"])
        risk_values_exact &= (
            item.get("risk_veto_reasons") == recalculated["risk_veto_reasons"]
            and item.get("risk_warning_labels") == recalculated["risk_warning_labels"]
            and item.get("risk_level") == recalculated["risk_level"]
        )
        conditions = item.get("conditions") or {}
        formula_hits = recompute_formula_hits(
            (evidence_formulas_for_local.get("bigbull") or {}).get(str(item.get("underlying_symbol") or "")),
            str(payload.get("cutoff_trade_date")),
        )
        expected_conditions = {
            "c1_weekly_gain_ge_5": recalculated["weekly_return_pct"] is not None
            and float(recalculated["weekly_return_pct"]) >= 5.0,
            "c2_remaining_lt_5yi": float(master["remaining_yi"]) < 5.0,
            "c3_premium_lt_50": recalculated["premium_pct"] is not None
            and float(recalculated["premium_pct"]) < 50.0,
            "c4_recent_ignition": bool(recalculated["ignition_local_cross_dates_10"]),
            "c6_youzi_inflow_start": recalculated["youzi_buy_latest"] is not None
            and recalculated["youzi_buy_prev"] is not None
            and bool(recalculated["youzi_recent_cross_dates_5"])
            and float(recalculated["youzi_buy_latest"]) > 0.0
            and float(recalculated["youzi_buy_latest"]) >= float(recalculated["youzi_buy_prev"]),
            "c10_big_bull_red_preference": bool(recalculated["big_bull_red"]),
            "c11_turnover5_ge_150": recalculated["turnover_5d_pct"] is not None
            and float(recalculated["turnover_5d_pct"]) >= 150.0,
        }
        condition_mismatch = {
            key: {"actual": conditions.get(key), "expected": value}
            for key, value in expected_conditions.items()
            if conditions.get(key) is not value
        }
        if condition_mismatch and len(local_condition_mismatches) < 25:
            local_condition_mismatches.append({"symbol": symbol, "mismatches": condition_mismatch})
        local_conditions_exact &= not condition_mismatch

        components = item.get("score_components") or {}
        raw1 = (components.get("c1_price_activity") or {}).get("raw_value") or {}
        raw2 = (components.get("c2_remaining_scale") or {}).get("raw_value") or {}
        raw3 = (components.get("c3_premium") or {}).get("raw_value") or {}
        raw4 = (components.get("c4_golden_ignition") or {}).get("raw_value") or {}
        raw5 = (components.get("c5_feilong_cross") or {}).get("raw_value") or {}
        raw6 = (components.get("c6_youzi_inflow") or {}).get("raw_value") or {}
        raw7 = (components.get("c7_scr90_convergence") or {}).get("raw_value") or {}
        raw8 = (components.get("c8_scr70_convergence") or {}).get("raw_value") or {}
        raw9 = (components.get("c9_sector_heat") or {}).get("raw_value") or {}
        raw11 = (components.get("c11_turnover5") or {}).get("raw_value") or {}
        stock_symbol = str(item.get("underlying_symbol") or "")
        expected_feilong = recompute_feilong((evidence_formulas_for_local.get("feilong") or {}).get(stock_symbol), str(payload.get("cutoff_trade_date")))
        expected_scr = recompute_scr(
            (evidence_formulas_for_local.get("scr90") or {}).get(symbol),
            (evidence_formulas_for_local.get("scr70") or {}).get(symbol),
            str(payload.get("cutoff_trade_date")),
        )
        ignition_dates = sorted(set(recalculated["ignition_local_cross_dates_10"]))
        calendar = [str(value) for value in payload.get("benchmark_calendar") or []]
        valid_feilong_crosses = [
            cross for cross in expected_feilong.get("score_window_crosses", []) if cross.get("below20")
        ]
        component_binding = all(
            (
                optional_close(raw1.get("weekly_return_pct"), recalculated["weekly_return_pct"]),
                close(raw2.get("remaining_yi"), master["remaining_yi"]),
                optional_close(raw3.get("premium_pct"), recalculated["premium_pct"]),
                raw4.get("cross_dates_10") == ignition_dates,
                raw4.get("newest_age_sessions") == newest_session_age(ignition_dates, calendar, 10),
                optional_close(raw4.get("ema3_latest"), recalculated["ema3_latest"]),
                optional_close(raw4.get("ema21_latest"), recalculated["ema21_latest"]),
                raw5.get("newest_age_sessions") == newest_session_age(
                    [str(cross["date"]) for cross in valid_feilong_crosses], calendar, 10
                ),
                deep_close(raw5.get("valid_below20_crosses") or [], valid_feilong_crosses),
                optional_close(raw5.get("latest_wave"), expected_feilong.get("latest_wave")),
                optional_close(raw5.get("latest_segment"), expected_feilong.get("latest_segment")),
                int(raw5.get("point_count", -1)) == int(expected_feilong.get("point_count", -2)),
                optional_close(raw6.get("buy_latest"), recalculated["youzi_buy_latest"]),
                optional_close(raw6.get("buy_prev"), recalculated["youzi_buy_prev"]),
                raw6.get("cross_dates_5") == recalculated["youzi_recent_cross_dates_5"],
                optional_close(raw7.get("shrink90_pp"), expected_scr.get("shrink90_pp")),
                optional_close(raw7.get("relative_shrink90"), expected_scr.get("relative_shrink90")),
                optional_close(raw8.get("shrink70_pp"), expected_scr.get("shrink70_pp")),
                optional_close(raw11.get("turnover_5d_pct"), recalculated["turnover_5d_pct"]),
                optional_close(raw9.get("industry_heat_score"), (item.get("industry") or {}).get("heat_score")),
                optional_close(raw9.get("industry_heat_score"), expected_industry.get("heat_score")),
                deep_close(raw9.get("best_concept"), independent_best_concept(expected_concepts), 1e-9),
                optional_close(raw9.get("underlying_trend_score"), recalculated.get("underlying_trend_score")),
            )
        )
        if not component_binding and len(component_raw_mismatches) < 25:
            component_raw_mismatches.append(symbol)
        component_raw_bindings_exact &= component_binding
    checks["master_mapping_and_terms_exact"] = master_mapping_exact
    checks["local_day_values_recomputed"] = local_values_exact
    checks["risk_labels_recomputed_from_raw"] = risk_values_exact
    checks["local_conditions_recomputed"] = local_conditions_exact
    checks["component_raw_values_bound_to_evidence"] = component_raw_bindings_exact
    checks["sector_heat_recomputed_from_raw_day_inputs"] = heat_values_exact

    component_bounds = True
    component_recomputed = True
    totals_equal_sum = True
    missing_zero = True
    component_keys_exact = True
    coverage_fields_exact = True
    for item in results:
        components = item.get("score_components") or {}
        component_keys_exact &= tuple(components.keys()) == EXPECTED_IDS
        earned_sum = 0.0
        coverage_sum = 0.0
        expected_missing: list[str] = []
        expected_partial: list[str] = []
        for criterion_id in EXPECTED_IDS:
            component = components.get(criterion_id) or {}
            weight = float(component.get("weight", math.nan))
            normalized = float(component.get("normalized_score", math.nan))
            earned = float(component.get("earned_score", math.nan))
            status = component.get("data_status")
            coverage_fraction = float(component.get("coverage_fraction", math.nan))
            component_bounds &= (
                math.isfinite(weight)
                and math.isfinite(normalized)
                and math.isfinite(earned)
                and close(weight, EXPECTED_WEIGHTS[criterion_id], 1e-9)
                and -1e-9 <= normalized <= 1.0 + 1e-9
                and -1e-9 <= earned <= weight + 0.0011
                and status in {"AVAILABLE", "PARTIAL", "MISSING"}
                and math.isfinite(coverage_fraction)
                and -1e-9 <= coverage_fraction <= 1.0 + 1e-9
            )
            if status == "MISSING":
                missing_zero &= close(normalized, 0.0) and close(earned, 0.0)
            try:
                expected_normalized = recompute_normalized(criterion_id, component.get("raw_value") or {})
                component_recomputed &= close(normalized, expected_normalized) and close(earned, weight * expected_normalized)
            except (AssertionError, KeyError, TypeError, ValueError):
                component_recomputed = False
            earned_sum += earned
            if status == "MISSING":
                expected_coverage = 0.0
                expected_missing.append(criterion_id)
            elif status == "PARTIAL":
                expected_partial.append(criterion_id)
                if criterion_id == "c9_sector_heat":
                    raw = component.get("raw_value") or {}
                    expected_coverage = (
                        0.30 * float(raw.get("industry_heat_score") is not None)
                        + 0.40 * float(raw.get("best_concept") is not None)
                        + 0.30 * float(raw.get("underlying_trend_score") is not None)
                    )
                else:
                    expected_coverage = 0.5
            else:
                expected_coverage = 1.0
            coverage_fields_exact &= close(coverage_fraction, expected_coverage, 1e-9)
            coverage_sum += weight * coverage_fraction
        totals_equal_sum &= close(float(item.get("score_total_raw", math.nan)), earned_sum)
        coverage_fields_exact &= (
            close(float(item.get("score_coverage_weight", math.nan)), coverage_sum, 1e-9)
            and item.get("score_missing_criteria") == expected_missing
            and item.get("score_partial_criteria") == expected_partial
        )
    checks["component_keys_exact"] = component_keys_exact
    checks["all_component_bounds"] = component_bounds
    checks["all_component_recomputed"] = component_recomputed
    checks["missing_components_score_zero"] = missing_zero
    checks["all_totals_equal_sum"] = totals_equal_sum
    checks["coverage_fields_exact"] = coverage_fields_exact

    reranked = sorted(results, key=lambda item: (-float(item["score_total_raw"]), not bool(item["big_bull_red_preference"]), item["symbol"]))
    top10 = payload.get("ranking_top10") or []
    top10_symbols = [item.get("symbol") for item in top10]
    checks["top10_exact_from_full_pool"] = len(top10) == 10 and top10_symbols == [item["symbol"] for item in reranked[:10]]
    checks["tie_rule_exact"] = symbols == [item["symbol"] for item in reranked]
    checks["risk_labels_preserved"] = all(
        top10[index].get("risk_veto_reasons") == reranked[index].get("risk_veto_reasons")
        and top10[index].get("risk_warning_labels") == reranked[index].get("risk_warning_labels")
        and top10[index].get("risk_level") == reranked[index].get("risk_level")
        for index in range(min(10, len(top10), len(reranked)))
    )

    cutoff = str(payload.get("cutoff_trade_date"))
    checks["cutoff_matches_tdx"] = cutoff == latest_tdx_benchmark_date(payload) == str(payload.get("benchmark_calendar", [None])[-1])
    local_synchronized_count = sum(
        node.get("bond_current") is True and node.get("stock_current") is True
        for node in recomputed_local_by_symbol.values()
    )
    full_lookback_count = sum(node.get("bond_full_lookback") is True for node in recomputed_local_by_symbol.values())
    technical_partial = {
        symbol
        for symbol, node in recomputed_local_by_symbol.items()
        if node.get("bond_full_lookback") is not True or node.get("stock_signal_available") is not True
    }
    formula_ineligible = {
        symbol for symbol, node in recomputed_local_by_symbol.items() if node.get("bond_full_lookback") is not True
    }
    persisted_partial = {str(node.get("symbol") or "") for node in payload.get("technical_partial_details") or []}
    checks["technical_data_partition_exact"] = bool(
        len(recomputed_local_by_symbol) == len(results)
        and int(payload.get("local_synchronized_count", -1)) == local_synchronized_count
        and int(payload.get("full_lookback_count", -1)) == full_lookback_count
        and int(payload.get("technical_partial_count", -1)) == len(technical_partial)
        and persisted_partial == technical_partial
    )
    evidence_formulas = formula_evidence.get("formulas") or {}
    formula_values_exact = bool(results) and checks["formula_evidence_binding_exact"]
    for item in results:
        stock_symbol = str(item.get("underlying_symbol") or "")
        bond_symbol = str(item.get("symbol") or "")
        expected_feilong = recompute_feilong((evidence_formulas.get("feilong") or {}).get(stock_symbol), cutoff)
        expected_scr = recompute_scr(
            (evidence_formulas.get("scr90") or {}).get(bond_symbol),
            (evidence_formulas.get("scr70") or {}).get(bond_symbol),
            cutoff,
        )
        expected_hits = recompute_formula_hits((evidence_formulas.get("bigbull") or {}).get(stock_symbol), cutoff)
        formula_values_exact &= deep_close(expected_feilong, item.get("feilong") or {})
        formula_values_exact &= deep_close(expected_scr, item.get("scr") or {})
        formula_values_exact &= deep_close(expected_hits, item.get("bigbull_ignition_formula_hits") or [])
    checks["formula_values_recomputed_from_bound_evidence"] = formula_values_exact
    formula = payload.get("formula_coverage") or {}
    field_coverage = formula.get("field_coverage") or {}
    checks["formula_coverage_complete"] = bool(
        formula.get("complete")
        and formula.get("node_counts_complete")
        and not formula.get("errors")
        and set(field_coverage) == {"feilong", "scr90", "scr70", "bigbull"}
        and all(node.get("complete") for node in field_coverage.values())
        and formula.get("history_count") == {"feilong": 600, "scr90": 0, "scr70": 0, "bigbull": 600}
        and int(formula.get("scored_bonds", -1)) == len(results)
        and int(formula.get("expected_bonds", -1)) == full_lookback_count
        and set(formula.get("formula_ineligible_bonds") or []) == formula_ineligible
    )

    risk_counts = {
        level: sum(item.get("risk_level") == level for item in top10)
        for level in ("RED", "YELLOW", "GREEN")
    }
    policy = payload.get("execution_policy") or {}
    checks["risk_counts_top10_exact"] = payload.get("risk_counts_top10") == risk_counts
    checks["execution_policy_exact"] = (
        policy.get("automatic_order") is False
        and policy.get("execution_eligible") is (risk_counts["GREEN"] > 0)
        and policy.get("strong_redemption_announcements_verified") is False
    )

    source_nodes = list(walk_path_nodes(payload.get("source_files") or {}))
    checks["source_metadata_schema_complete"] = len(source_nodes) == 9 and all(valid_source_node(node) for node in source_nodes)
    source_hashes_match = checks["source_metadata_schema_complete"]
    for node in source_nodes:
        if not valid_source_node(node):
            source_hashes_match = False
            continue
        path = Path(node["path"])
        source_hashes_match &= path.is_file() and path.stat().st_size == int(node["size"]) and sha256(path) == node["sha256"]
    checks["source_hashes_match"] = source_hashes_match
    universe_count, universe_symbols = independent_universe_count(payload)
    checks["universe_recomputed"] = universe_count == int(payload.get("universe_count", -1)) and set(symbols).issubset(universe_symbols)
    missing_symbols = set(payload.get("missing_local_symbols") or [])
    checks["universe_partition_exact"] = bool(
        payload.get("universe_partition_complete")
        and not (set(symbols) & missing_symbols)
        and set(symbols) | missing_symbols == universe_symbols
        and len(symbols) + len(missing_symbols) == universe_count
        and int(payload.get("missing_local_count", -1)) == len(missing_symbols)
    )
    manifest_aliases = {
        str(alias)
        for node in day_manifest.get("inputs") or []
        for alias in node.get("lookup_symbols") or []
    }
    required_day_aliases = {"999999.SH", *symbols, *(str(item.get("underlying_symbol")) for item in results)}
    required_day_aliases.update(str(value) for value in heat.get("attempted_lookup_symbols") or [])
    checks["day_manifest_scoring_and_heat_inputs_complete"] = required_day_aliases.issubset(manifest_aliases)
    master_diagnostics = payload.get("bond_master_diagnostics") or {}
    checks["bond_master_integrity_complete"] = bool(master_diagnostics.get("integrity_complete"))

    status = "PASS" if checks and all(checks.values()) else "FAIL"
    output = {
        "status": status,
        "run_id": run_id,
        "input": {
            "path": str(args.input),
            "size": args.input.stat().st_size,
            "sha256": sha256(args.input),
        },
        "cutoff_trade_date": cutoff,
        "universe_count_recomputed": universe_count,
        "analyzed_count": len(results),
        "score_model": {"criterion_ids": list(ids), "weights": weights, "weight_sum": sum(weights.values())},
        "risk_counts_top10": risk_counts,
        "execution_policy": policy,
        "checks": checks,
        "diagnostics": {
            "local_condition_mismatches": local_condition_mismatches,
            "component_raw_mismatch_symbols": component_raw_mismatches,
            "sector_heat_mismatch_symbols": heat_mismatch_symbols,
            "day_input_mismatches": [
                item for item in day_input_checks
                if not item["contract"] or not item["unique"] or not item["current"]
            ],
        },
        "top10": [
            {
                "rank": item["rank"],
                "symbol": item["symbol"],
                "name": item["name"],
                "underlying_symbol": item["underlying_symbol"],
                "underlying_name": item["underlying_name"],
                "score": item["score_total_raw"],
                "big_bull_red_preference": item["big_bull_red_preference"],
                "risk_level": item["risk_level"],
                "risk_labels": [*item.get("risk_veto_reasons", []), *item.get("risk_warning_labels", [])],
            }
            for item in top10
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output = canonicalize_business_payload(output)
    atomic_write_json(args.output, output)
    readback = json.loads(args.output.read_text(encoding="utf-8"))
    if readback.get("status") != status or readback.get("top10") != output["top10"]:
        raise RuntimeError("verification JSON readback mismatch")
    print(json.dumps({
        "status": status,
        "output": str(args.output),
        "output_size": args.output.stat().st_size,
        "output_sha256": sha256(args.output),
        "checks": checks,
        "top10": output["top10"],
    }, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 2


def _read_bound_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig")) if path.is_file() else {}
    except (OSError, json.JSONDecodeError, UnicodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _redemption_record_map(snapshot: dict[str, Any]) -> tuple[dict[str, str], bool]:
    records = snapshot.get("records")
    if not isinstance(records, list):
        return {}, False
    mapped: dict[str, str] = {}
    valid = True
    for record in records:
        if not isinstance(record, dict):
            valid = False
            continue
        symbol = str(record.get("symbol") or "")
        status = record.get("early_redemption_status")
        if not symbol or symbol in mapped or not isinstance(status, str) or not status:
            valid = False
            continue
        mapped[symbol] = status
    return mapped, valid and len(mapped) == len(records)


def _expected_hard_exclusion_reasons(
    master: dict[str, Any],
    local: dict[str, Any],
    scr: dict[str, Any],
    early_redemption_status: str,
) -> list[str]:
    reasons: list[str] = []
    if str(master.get("name") or "").strip().upper().startswith("Z"):
        reasons.append("bond_name_z_prefix")
    daily_return = finite_float(local.get("daily_return_pct"))
    volume_ratio = finite_float(local.get("bond_volume_ratio_5d"))
    if daily_return is not None and volume_ratio is not None and daily_return >= 10.0 and volume_ratio > 4.0:
        reasons.append("daily_gain_ge_10_and_volume_ratio_gt_4")
    scr90_change = finite_float(scr.get("scr90_change_1d_pp"))
    if scr90_change is None:
        reasons.append("scr90_change_1d_unavailable")
    elif scr90_change > 0.0:
        reasons.append("scr90_change_1d_positive")
    turnover = finite_float(local.get("turnover_5d_pct"))
    if turnover is not None and turnover > 1000.0:
        reasons.append("turnover_5d_gt_1000")
    bond_close = finite_float(local.get("bond_close"))
    if bond_close is not None and bond_close > 350.0:
        reasons.append("bond_close_gt_350")
    if early_redemption_status == "ANNOUNCED_EARLY_REDEMPTION":
        reasons.append("early_redemption_announced")
    elif early_redemption_status == "UNVERIFIED" or not early_redemption_status:
        reasons.append("early_redemption_unverified")
    return reasons


def _main_impl() -> int:
    parser = argparse.ArgumentParser(description="Independent V5 verifier for weighted convertible-bond ranking")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--formula-evidence", type=Path, default=None)
    parser.add_argument("--day-input-manifest", type=Path, default=None)
    parser.add_argument("--redemption-announcements", required=True, type=Path)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.attempt < 1:
        raise SystemExit("invalid --attempt")

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}
    checks["scan_status_pass"] = payload.get("status") == "PASS"
    checks["schema_v5"] = payload.get("schema") == "TDX-CONVERTIBLE-BOND-WEIGHTED-SCAN-V5"
    checks["source_binding_mode_exact"] = payload.get("source_binding_mode") == SOURCE_BINDING_MODE
    checks["day_input_binding_mode_exact"] = payload.get("day_input_binding_mode") == DAY_INPUT_BINDING_MODE
    run_id = str(payload.get("run_id") or "")
    checks["run_id_exact"] = bool(run_id) and (args.run_id is None or run_id == str(args.run_id))
    cutoff = str(payload.get("cutoff_trade_date") or "")
    calendar = [str(value) for value in payload.get("benchmark_calendar") or []]
    required_scr_dates = calendar[-6:]
    checks["benchmark_calendar_valid"] = bool(
        len(calendar) == 11
        and calendar == sorted(calendar)
        and len(calendar) == len(set(calendar))
        and all(re.fullmatch(r"20\d{6}", value) for value in calendar)
        and cutoff == calendar[-1]
        and len(required_scr_dates) == 6
    )

    redemption_meta = payload.get("redemption_announcement_snapshot") or {}
    redemption_path = args.redemption_announcements.resolve()
    redemption_snapshot = _read_bound_json(redemption_path)
    try:
        redemption_size_exact = redemption_path.stat().st_size == int(redemption_meta.get("size", -1))
    except (OSError, TypeError, ValueError):
        redemption_size_exact = False
    checks["redemption_announcement_snapshot_binding_exact"] = bool(
        redemption_path.is_file()
        and same_path(redemption_meta.get("path"), redemption_path)
        and redemption_size_exact
        and sha256(redemption_path) == redemption_meta.get("sha256")
        and redemption_meta.get("run_id") == run_id
        and redemption_meta.get("cutoff") == cutoff
        and redemption_meta.get("status") == "PASS"
        and redemption_meta.get("current_universe_complete") is True
        and redemption_snapshot.get("run_id") == run_id
        and redemption_snapshot.get("cutoff") == cutoff
        and redemption_snapshot.get("status") == "PASS"
        and redemption_snapshot.get("current_universe_complete") is True
    )

    evidence_meta = payload.get("formula_evidence") or {}
    evidence_path = args.formula_evidence or Path(str(evidence_meta.get("path") or ""))
    formula_evidence = _read_bound_json(evidence_path)
    checks["formula_evidence_binding_exact"] = bool(
        evidence_path.is_file()
        and evidence_path.stat().st_size == int(evidence_meta.get("size", -1))
        and sha256(evidence_path) == evidence_meta.get("sha256")
        and formula_evidence.get("schema") == "CONVERTIBLE-BOND-FORMULA-EVIDENCE-1"
        and formula_evidence.get("run_id") == run_id
        and formula_evidence.get("cutoff_trade_date") == cutoff
    )

    day_meta = payload.get("day_input_manifest") or {}
    day_manifest_path = args.day_input_manifest or Path(str(day_meta.get("path") or ""))
    day_manifest = _read_bound_json(day_manifest_path)
    checks["day_input_manifest_binding_exact"] = bool(
        day_manifest_path.is_file()
        and day_manifest_path.stat().st_size == int(day_meta.get("size", -1))
        and sha256(day_manifest_path) == day_meta.get("sha256")
    )
    day_manifest_contract, day_inputs_current, day_input_checks, frozen_day_reader = validate_day_input_manifest(
        day_manifest,
        run_id,
        cutoff,
    )
    checks["day_input_manifest_v2_contract_exact"] = day_manifest_contract
    checks["day_input_manifest_current"] = day_inputs_current
    if not checks["day_input_manifest_binding_exact"] or not day_manifest_contract:
        return emit_day_manifest_failure(args.output, run_id, args.attempt, checks, day_input_checks)
    if not day_inputs_current:
        return emit_day_update_race(args.output, run_id, args.attempt, checks, day_input_checks)
    if frozen_day_reader is None:
        raise RuntimeError("validated day manifest did not produce a frozen reader")

    model = payload.get("score_model") or {}
    criteria = model.get("criteria") or []
    try:
        ids = tuple(item.get("id") for item in criteria)
        weights = {str(item.get("id")): float(item.get("weight")) for item in criteria}
        declared_weight_sum = float(model.get("weight_sum"))
    except (AttributeError, TypeError, ValueError):
        ids, weights, declared_weight_sum = (), {}, math.nan
    checks["score_model_version_v2"] = model.get("version") == "CB-WEIGHTED-10-V2"
    checks["weights_count_10"] = len(criteria) == 10 and len(set(ids)) == 10 and ids == EXPECTED_IDS
    checks["weights_exact"] = weights == EXPECTED_WEIGHTS
    checks["weights_sum_100"] = close(sum(weights.values()), 100.0, 1e-9) and close(declared_weight_sum, 100.0, 1e-9)
    checks["c9_normalization_contract_exact"] = (
        (model.get("normalization_rules") or {}).get("c9_sector_heat") == EXPECTED_C9_NORMALIZATION_RULE
    )
    checks["personal_kb_confirmation_model_exact"] = (
        payload.get("personal_kb_confirmation_model")
        == PERSONAL_KB_CONFIRMATION_MODEL
    )
    checks["big_bull_zero_score"] = bool(
        all("big_bull" not in criterion_id for criterion_id in ids)
        and "contributes zero score" in str(model.get("big_bull_rule"))
        and "diagnostic only" in str((model.get("normalization_rules") or {}).get("c4_golden_ignition"))
    )

    raw_results = payload.get("all_results")
    raw_excluded_results = payload.get("hard_excluded_results")
    results_well_formed = isinstance(raw_results, list) and all(isinstance(item, dict) for item in raw_results)
    excluded_well_formed = isinstance(raw_excluded_results, list) and all(
        isinstance(item, dict) for item in raw_excluded_results
    )
    results = raw_results if results_well_formed else []
    excluded_results = raw_excluded_results if excluded_well_formed else []
    evaluated_results = [*results, *excluded_results]
    symbols = [str(item.get("symbol") or "") for item in results]
    excluded_symbols = [str(item.get("symbol") or "") for item in excluded_results]
    evaluated_symbols = [*symbols, *excluded_symbols]
    master_records, independent_master_diagnostics = independent_bond_records(payload)
    master_symbols = list(master_records)
    master_symbol_set = set(master_symbols)
    redemption_by_symbol, redemption_records_well_formed = _redemption_record_map(redemption_snapshot)
    checks["redemption_announcement_records_complete"] = bool(
        redemption_records_well_formed
        and set(redemption_by_symbol) == master_symbol_set
        and len(redemption_by_symbol) == len(master_records)
    )
    try:
        pool_counts_exact = bool(
            int(payload.get("universe_count", -1)) == len(master_records) == len(evaluated_results)
            and int(payload.get("evaluated_count", -1)) == len(evaluated_results)
            and int(payload.get("eligible_count", -1)) == len(results)
            and int(payload.get("ranked_count", -1)) == len(results)
            and int(payload.get("hard_excluded_count", -1)) == len(excluded_results)
        )
    except (TypeError, ValueError):
        pool_counts_exact = False
    checks["result_pools_partition_master_exact"] = bool(
        results_well_formed
        and excluded_well_formed
        and bool(evaluated_results)
        and all(evaluated_symbols)
        and len(symbols) == len(set(symbols))
        and len(excluded_symbols) == len(set(excluded_symbols))
        and set(symbols).isdisjoint(excluded_symbols)
        and set(evaluated_symbols) == master_symbol_set
        and len(evaluated_symbols) == len(master_records)
        and pool_counts_exact
        and payload.get("universe_partition_complete") is True
        and all(item.get("rank") == index for index, item in enumerate(results, 1))
    )
    checks["bond_master_diagnostics_exact"] = deep_close(
        payload.get("bond_master_diagnostics") or {}, independent_master_diagnostics, 1e-9
    )

    source_files = payload.get("source_files") or {}
    checks["trusted_source_paths_exact"] = trusted_source_paths_exact(source_files)
    tdx_root = TRUSTED_TDX_ROOT
    heat = recompute_heat(
        tdx_root,
        TRUSTED_SOURCE_PATHS["industry_membership"],
        TRUSTED_SOURCE_PATHS["industry_names"],
        TRUSTED_SOURCE_PATHS["concept_membership"],
        cutoff,
        calendar,
        day_reader=frozen_day_reader.read_rows,
    )
    evidence_formulas = formula_evidence.get("formulas") or {}

    master_mapping_exact = results_well_formed
    term_dates_strict = results_well_formed
    local_values_exact = results_well_formed
    risk_values_exact = results_well_formed
    sector_heat_exact = results_well_formed
    conditions_exact = results_well_formed
    formula_values_exact = results_well_formed and checks["formula_evidence_binding_exact"]
    c4_local_only = results_well_formed
    component_keys_exact = results_well_formed
    component_raw_exact = results_well_formed
    component_bounds = results_well_formed
    component_recomputed = results_well_formed
    component_status_exact = results_well_formed
    coverage_fields_exact = results_well_formed
    totals_equal_sum = results_well_formed
    missing_zero = True
    recomputed_local_by_symbol: dict[str, dict[str, Any]] = {}
    local_condition_mismatches: list[dict[str, Any]] = []
    component_mismatch_symbols: list[str] = []
    formula_mismatch_symbols: list[str] = []
    heat_mismatch_symbols: list[str] = []
    hard_exclusion_mismatches: list[dict[str, Any]] = []
    personal_kb_confirmation_exact = bool(evaluated_results)
    personal_kb_confirmation_mismatch_symbols: list[str] = []

    master_fields = (
        "line", "market", "code", "symbol", "name", "tnf_confirmed", "underlying",
        "underlying_symbol", "underlying_name", "conversion_price", "remaining_wan",
        "remaining_yi", "maturity_date", "maturity_date_status", "known_last_trade_date",
        "known_last_trade_date_status", "known_last_trade_date_semantic", "rating",
    )
    local_float_fields = (
        "bond_close", "stock_close", "conversion_value", "premium_pct", "weekly_return_pct",
        "daily_return_pct", "bond_volume_ratio_5d", "turnover_5d_pct", "ema3_latest", "ema21_latest", "youzi_buy_latest",
        "youzi_buy_prev", "ema5_latest", "ema20_latest", "stock_return5_pct",
        "stock_ma5_latest", "stock_ma10_latest", "stock_ma20_latest",
        "underlying_trend_score", "latest_volume",
    )
    local_exact_fields = (
        "bond_latest_date", "stock_latest_date", "bond_history_points", "stock_history_points",
        "bond_current", "stock_current", "bond_full_lookback", "bond_turnover_lookback",
        "stock_signal_available", "ignition_local_cross_dates", "ignition_local_cross_dates_10",
        "youzi_recent_cross_dates", "youzi_recent_cross_dates_5", "youzi_pass", "big_bull_red",
        "stock_ema_bullish", "stock_ma_bullish",
        "maturity_date_status_checked", "known_last_trade_date_status_checked",
        "known_last_trade_date_semantic_checked", "risk_veto_reasons", "risk_warning_labels", "risk_level",
    )
    diagnostic_condition_keys = (
        "c1_weekly_gain_ge_5", "c2_remaining_lt_5yi", "c3_premium_lt_50",
        "c4_recent_ignition", "c5_feilong_below20_cross", "c6_youzi_inflow_start",
        "c7_scr90_significant_contraction", "c8_scr70_shrink_ge_3pp",
        "c9_hot_industry_and_concept", "c11_turnover5_ge_150",
    )

    all_rows_master_mapping_exact = bool(evaluated_results)
    hard_filter_values_exact = bool(evaluated_results)
    redemption_status_per_bond_exact = bool(
        evaluated_results and checks["redemption_announcement_records_complete"]
    )
    hard_exclusion_partition_exact = bool(evaluated_results)
    eligible_symbol_set = set(symbols)
    for item in evaluated_results:
        symbol = str(item.get("symbol") or "")
        expected_confirmation = recompute_personal_kb_confirmation(item)
        if item.get("personal_kb_confirmation") != expected_confirmation:
            personal_kb_confirmation_exact = False
            personal_kb_confirmation_mismatch_symbols.append(symbol)
        master = master_records.get(symbol)
        if master is None:
            all_rows_master_mapping_exact = False
            hard_filter_values_exact = False
            redemption_status_per_bond_exact = False
            hard_exclusion_partition_exact = False
            if len(hard_exclusion_mismatches) < 25:
                hard_exclusion_mismatches.append({"symbol": symbol, "error": "missing_master_record"})
            continue
        row_master_exact = deep_close(
            {field: item.get(field) for field in master_fields},
            {field: master.get(field) for field in master_fields},
            1e-9,
        )
        all_rows_master_mapping_exact &= row_master_exact
        local = recompute_local_and_risk(payload, master, frozen_day_reader.read_rows)
        recomputed_local_by_symbol[symbol] = local
        expected_scr = recompute_scr(
            (evidence_formulas.get("scr90") or {}).get(symbol),
            (evidence_formulas.get("scr70") or {}).get(symbol),
            cutoff,
            required_scr_dates,
        )
        row_values_exact = bool(
            optional_close(item.get("bond_close"), local.get("bond_close"))
            and optional_close(item.get("turnover_5d_pct"), local.get("turnover_5d_pct"))
            and optional_close(item.get("daily_return_pct"), local.get("daily_return_pct"))
            and optional_close(item.get("bond_volume_ratio_5d"), local.get("bond_volume_ratio_5d"))
            and optional_close(item.get("scr90_previous"), expected_scr.get("scr90_previous"))
            and optional_close(item.get("scr90_latest"), expected_scr.get("scr90_latest"))
            and optional_close(item.get("scr90_change_1d_pp"), expected_scr.get("scr90_change_1d_pp"))
        )
        hard_filter_values_exact &= row_values_exact
        expected_redemption_status = redemption_by_symbol.get(symbol, "")
        row_redemption_exact = item.get("early_redemption_status") == expected_redemption_status
        redemption_status_per_bond_exact &= row_redemption_exact
        expected_reasons = _expected_hard_exclusion_reasons(
            master,
            local,
            expected_scr,
            expected_redemption_status,
        )
        expected_pass = not expected_reasons
        actual_reasons = item.get("hard_exclusion_reasons")
        row_partition_exact = bool(
            actual_reasons == expected_reasons
            and item.get("hard_exclusion_pass") is expected_pass
            and (symbol in eligible_symbol_set) is expected_pass
        )
        hard_exclusion_partition_exact &= row_partition_exact
        if (
            not row_values_exact
            or not row_redemption_exact
            or not row_partition_exact
            or not row_master_exact
        ) and len(hard_exclusion_mismatches) < 25:
            hard_exclusion_mismatches.append({
                "symbol": symbol,
                "pool": "eligible" if symbol in eligible_symbol_set else "hard_excluded",
                "expected": {
                    "bond_close": local.get("bond_close"),
                    "turnover_5d_pct": local.get("turnover_5d_pct"),
                    "daily_return_pct": local.get("daily_return_pct"),
                    "bond_volume_ratio_5d": local.get("bond_volume_ratio_5d"),
                    "scr90_previous": expected_scr.get("scr90_previous"),
                    "scr90_latest": expected_scr.get("scr90_latest"),
                    "scr90_change_1d_pp": expected_scr.get("scr90_change_1d_pp"),
                    "early_redemption_status": expected_redemption_status,
                    "hard_exclusion_reasons": expected_reasons,
                    "hard_exclusion_pass": expected_pass,
                },
                "actual": {
                    "bond_close": item.get("bond_close"),
                    "turnover_5d_pct": item.get("turnover_5d_pct"),
                    "daily_return_pct": item.get("daily_return_pct"),
                    "bond_volume_ratio_5d": item.get("bond_volume_ratio_5d"),
                    "scr90_previous": item.get("scr90_previous"),
                    "scr90_latest": item.get("scr90_latest"),
                    "scr90_change_1d_pp": item.get("scr90_change_1d_pp"),
                    "early_redemption_status": item.get("early_redemption_status"),
                    "hard_exclusion_reasons": actual_reasons,
                    "hard_exclusion_pass": item.get("hard_exclusion_pass"),
                },
            })

    checks["all_rows_master_mapping_exact"] = all_rows_master_mapping_exact
    checks["hard_filter_fields_recomputed"] = hard_filter_values_exact
    checks["redemption_status_per_bond_exact"] = redemption_status_per_bond_exact
    checks["hard_exclusion_partition_recomputed"] = hard_exclusion_partition_exact

    for item in results:
        symbol = str(item.get("symbol") or "")
        master = master_records.get(symbol)
        if master is None:
            master_mapping_exact = term_dates_strict = local_values_exact = False
            risk_values_exact = sector_heat_exact = conditions_exact = formula_values_exact = False
            component_raw_exact = component_recomputed = False
            continue
        master_mapping_exact &= deep_close(
            {field: item.get(field) for field in master_fields},
            {field: master.get(field) for field in master_fields},
            1e-9,
        )
        maturity = parse_term_date(item.get("maturity_date"), item.get("maturity_date_status") != "FIELD_ABSENT")
        last_trade = parse_term_date(
            item.get("known_last_trade_date"), item.get("known_last_trade_date_status") != "FIELD_ABSENT"
        )
        cutoff_date = dt.datetime.strptime(cutoff, "%Y%m%d").date()
        term_dates_strict &= bool(
            item.get("maturity_date_status") in TERM_DATE_STATUSES
            and item.get("known_last_trade_date_status") in TERM_DATE_STATUSES
            and maturity["status"] == "VALID"
            and maturity["date"] > cutoff_date
            and last_trade["status"] in ("VALID", "MISSING")
            and (last_trade["date"] is None or last_trade["date"] > cutoff_date)
            and (last_trade["date"] is None or last_trade["date"] <= maturity["date"])
            and item.get("known_last_trade_date_semantic")
            == ("not_announced" if last_trade["status"] == "MISSING" else "announced")
        )

        local = recompute_local_and_risk(payload, master, frozen_day_reader.read_rows)
        recomputed_local_by_symbol[symbol] = local
        local_values_exact &= all(optional_close(item.get(field), local.get(field)) for field in local_float_fields)
        local_values_exact &= all(item.get(field) == local.get(field) for field in local_exact_fields)
        local_values_exact &= item.get("big_bull_red_preference") is bool(local["big_bull_red"])
        risk_values_exact &= bool(
            item.get("risk_veto_reasons") == local["risk_veto_reasons"]
            and item.get("risk_warning_labels") == local["risk_warning_labels"]
            and item.get("risk_level") == local["risk_level"]
        )

        underlying_key = code7(master["underlying"])
        industry_code = heat["stock_industry"].get(underlying_key)
        expected_industry = heat["industry_heat"].get(industry_code or "", {})
        expected_concepts = (heat["concept_by_code"].get(underlying_key) or [])[:5]
        expected_best_concept = independent_best_concept(expected_concepts)
        expected_top_concept_score = max(
            (float(node["heat_score"]) for node in expected_concepts), default=None
        )
        heat_match = bool(
            deep_close(item.get("industry") or {}, expected_industry, 1e-9)
            and deep_close(item.get("top_concepts") or [], expected_concepts, 1e-9)
            and optional_close(item.get("top_concept_heat_score"), expected_top_concept_score, 1e-9)
        )
        sector_heat_exact &= heat_match
        if not heat_match and len(heat_mismatch_symbols) < 25:
            heat_mismatch_symbols.append(symbol)

        stock_symbol = master["underlying_symbol"]
        expected_feilong = recompute_feilong((evidence_formulas.get("feilong") or {}).get(stock_symbol), cutoff)
        expected_scr = recompute_scr(
            (evidence_formulas.get("scr90") or {}).get(symbol),
            (evidence_formulas.get("scr70") or {}).get(symbol),
            cutoff,
            required_scr_dates,
        )
        expected_bigbull_hits = recompute_formula_hits(
            (evidence_formulas.get("bigbull") or {}).get(stock_symbol), cutoff
        )
        formula_match = bool(
            deep_close(item.get("feilong") or {}, expected_feilong)
            and deep_close(item.get("scr") or {}, expected_scr)
            and deep_close(item.get("bigbull_formula_diagnostic_hits") or [], expected_bigbull_hits)
            and "bigbull_ignition_formula_hits" not in item
        )
        formula_values_exact &= formula_match
        if not formula_match and len(formula_mismatch_symbols) < 25:
            formula_mismatch_symbols.append(symbol)

        industry_score = finite_float(expected_industry.get("heat_score"))
        heat_pass = bool(
            industry_score is not None and industry_score / 100.0 >= 0.60
            and expected_top_concept_score is not None and expected_top_concept_score / 100.0 >= 0.60
            and local.get("underlying_trend_score") is not None
            and float(local["underlying_trend_score"]) >= 0.60
        )
        expected_conditions = {
            "c1_weekly_gain_ge_5": local["weekly_return_pct"] is not None and float(local["weekly_return_pct"]) >= 5.0,
            "c2_remaining_lt_5yi": float(master["remaining_yi"]) < 5.0,
            "c3_premium_lt_50": local["premium_pct"] is not None and float(local["premium_pct"]) < 50.0,
            "c4_recent_ignition": bool(local["ignition_local_cross_dates_10"]),
            "c5_feilong_below20_cross": bool(expected_feilong["pass"]),
            "c6_youzi_inflow_start": bool(local["youzi_pass"]),
            "c7_scr90_significant_contraction": bool(expected_scr.get("pass90")),
            "c8_scr70_shrink_ge_3pp": bool(expected_scr.get("pass70")),
            "c9_hot_industry_and_concept": heat_pass,
            "c10_big_bull_red_preference": bool(local["big_bull_red"]),
            "c11_turnover5_ge_150": local["turnover_5d_pct"] is not None and float(local["turnover_5d_pct"]) >= 150.0,
        }
        actual_conditions = item.get("conditions") or {}
        condition_match = actual_conditions == expected_conditions
        conditions_exact &= condition_match
        if not condition_match and len(local_condition_mismatches) < 25:
            local_condition_mismatches.append({
                "symbol": symbol,
                "actual": actual_conditions,
                "expected": expected_conditions,
            })
        conditions_exact &= int(item.get("diagnostic_condition_pass_count", -1)) == sum(
            bool(expected_conditions[key]) for key in diagnostic_condition_keys
        )

        valid_feilong_crosses = [
            cross for cross in expected_feilong.get("score_window_crosses", []) if cross.get("below20")
        ]
        ignition_dates = sorted(set(local["ignition_local_cross_dates_10"]))
        expected_raws = {
            "c1_price_activity": {"weekly_return_pct": local["weekly_return_pct"]},
            "c2_remaining_scale": {"remaining_yi": master["remaining_yi"]},
            "c3_premium": {"premium_pct": local["premium_pct"]},
            "c4_golden_ignition": {
                "cross_dates_10": ignition_dates,
                "newest_age_sessions": newest_session_age(ignition_dates, calendar, 10),
                "ema3_latest": local["ema3_latest"],
                "ema21_latest": local["ema21_latest"],
            },
            "c5_feilong_cross": {
                "newest_age_sessions": newest_session_age(
                    [str(cross["date"]) for cross in valid_feilong_crosses], calendar, 10
                ),
                "valid_below20_crosses": valid_feilong_crosses,
                "latest_wave": expected_feilong.get("latest_wave"),
                "latest_segment": expected_feilong.get("latest_segment"),
                "point_count": expected_feilong.get("point_count"),
            },
            "c6_youzi_inflow": {
                "buy_latest": local["youzi_buy_latest"],
                "buy_prev": local["youzi_buy_prev"],
                "cross_dates_5": local["youzi_recent_cross_dates_5"],
            },
            "c7_scr90_convergence": {
                "shrink90_pp": expected_scr.get("shrink90_pp"),
                "relative_shrink90": expected_scr.get("relative_shrink90"),
                "old": expected_scr.get("scr90_old"),
                "latest": expected_scr.get("scr90_latest"),
            },
            "c8_scr70_convergence": {
                "shrink70_pp": expected_scr.get("shrink70_pp"),
                "old": expected_scr.get("scr70_old"),
                "latest": expected_scr.get("scr70_latest"),
            },
            "c9_sector_heat": {
                "industry_heat_score": industry_score,
                "industry_normalized": clip(industry_score / 100.0) if industry_score is not None else 0.0,
                "best_concept": expected_best_concept,
                "underlying_trend_score": local.get("underlying_trend_score"),
            },
            "c11_turnover5": {"turnover_5d_pct": local["turnover_5d_pct"]},
        }
        heat_coverage = (
            0.30 * float(industry_score is not None)
            + 0.40 * float(expected_best_concept is not None)
            + 0.30 * float(local.get("underlying_trend_score") is not None)
        )
        heat_status = "AVAILABLE" if close(heat_coverage, 1.0, 1e-9) else "PARTIAL" if heat_coverage > 0 else "MISSING"
        expected_statuses = {
            "c1_price_activity": "AVAILABLE" if local["weekly_return_pct"] is not None else "MISSING",
            "c2_remaining_scale": "AVAILABLE",
            "c3_premium": "AVAILABLE" if local["premium_pct"] is not None else "MISSING",
            "c4_golden_ignition": "AVAILABLE" if local["stock_signal_available"] is True else "MISSING",
            "c5_feilong_cross": "AVAILABLE" if int(expected_feilong.get("point_count") or 0) >= 2 else "MISSING",
            "c6_youzi_inflow": "AVAILABLE" if local["youzi_buy_latest"] is not None and local["youzi_buy_prev"] is not None else "MISSING",
            "c7_scr90_convergence": "AVAILABLE" if expected_scr.get("shrink90_pp") is not None else "MISSING",
            "c8_scr70_convergence": "AVAILABLE" if expected_scr.get("shrink70_pp") is not None else "MISSING",
            "c9_sector_heat": heat_status,
            "c11_turnover5": "AVAILABLE" if local["turnover_5d_pct"] is not None else "MISSING",
        }
        expected_coverages = {
            key: (
                heat_coverage if key == "c9_sector_heat"
                else 0.0 if status == "MISSING"
                else 0.5 if status == "PARTIAL"
                else 1.0
            )
            for key, status in expected_statuses.items()
        }
        components = item.get("score_components") or {}
        component_keys_exact &= tuple(components) == EXPECTED_IDS
        item_component_exact = tuple(components) == EXPECTED_IDS
        earned_sum = 0.0
        coverage_sum = 0.0
        expected_missing_criteria: list[str] = []
        expected_partial_criteria: list[str] = []
        for criterion_id in EXPECTED_IDS:
            component = components.get(criterion_id) or {}
            expected_raw = expected_raws[criterion_id]
            item_component_exact &= deep_close(component.get("raw_value") or {}, expected_raw)
            expected_normalized = recompute_normalized(criterion_id, expected_raw)
            expected_status = expected_statuses[criterion_id]
            expected_coverage = expected_coverages[criterion_id]
            try:
                actual_weight = float(component.get("weight"))
                actual_normalized = float(component.get("normalized_score"))
                actual_earned = float(component.get("earned_score"))
                actual_coverage = float(component.get("coverage_fraction"))
            except (TypeError, ValueError):
                actual_weight = actual_normalized = actual_earned = actual_coverage = math.nan
            component_bounds &= bool(
                math.isfinite(actual_weight)
                and math.isfinite(actual_normalized)
                and math.isfinite(actual_earned)
                and math.isfinite(actual_coverage)
                and -1e-9 <= actual_normalized <= 1.0 + 1e-9
                and -1e-9 <= actual_earned <= EXPECTED_WEIGHTS[criterion_id] + 0.0011
                and -1e-9 <= actual_coverage <= 1.0 + 1e-9
            )
            component_recomputed &= bool(
                close(actual_weight, EXPECTED_WEIGHTS[criterion_id], 1e-9)
                and close(actual_normalized, expected_normalized)
                and close(actual_earned, EXPECTED_WEIGHTS[criterion_id] * expected_normalized)
            )
            component_status_exact &= component.get("data_status") == expected_status
            coverage_fields_exact &= close(actual_coverage, expected_coverage, 1e-9)
            if expected_status == "MISSING":
                expected_missing_criteria.append(criterion_id)
                missing_zero &= close(actual_normalized, 0.0) and close(actual_earned, 0.0)
            elif expected_status == "PARTIAL":
                expected_partial_criteria.append(criterion_id)
            earned_sum += actual_earned
            coverage_sum += EXPECTED_WEIGHTS[criterion_id] * expected_coverage
        component_raw_exact &= item_component_exact
        if not item_component_exact and len(component_mismatch_symbols) < 25:
            component_mismatch_symbols.append(symbol)
        totals_equal_sum &= close(float(item.get("score_total_raw", math.nan)), earned_sum)
        coverage_fields_exact &= bool(
            close(float(item.get("score_coverage_weight", math.nan)), coverage_sum, 1e-9)
            and item.get("score_missing_criteria") == expected_missing_criteria
            and item.get("score_partial_criteria") == expected_partial_criteria
        )
        raw4 = (components.get("c4_golden_ignition") or {}).get("raw_value") or {}
        c4_local_only &= bool(
            raw4.get("cross_dates_10") == ignition_dates
            and actual_conditions.get("c4_recent_ignition") is bool(ignition_dates)
            and item.get("bigbull_formula_diagnostic_hits") == expected_bigbull_hits
            and "bigbull_ignition_formula_hits" not in item
        )

    checks["master_mapping_exact"] = master_mapping_exact
    checks["term_dates_strictly_after_cutoff"] = term_dates_strict
    checks["local_day_values_recomputed"] = local_values_exact
    checks["risk_labels_recomputed_from_raw"] = risk_values_exact
    checks["sector_heat_recomputed_from_raw_day_inputs"] = sector_heat_exact
    checks["all_conditions_recomputed"] = conditions_exact
    checks["formula_values_recomputed_from_bound_evidence"] = formula_values_exact
    checks["c4_local_ema_only_bigbull_diagnostic_separate"] = c4_local_only
    checks["component_keys_exact"] = component_keys_exact
    checks["component_raw_values_bound_to_evidence"] = component_raw_exact
    checks["all_component_bounds"] = component_bounds
    checks["all_component_recomputed"] = component_recomputed
    checks["component_data_status_exact"] = component_status_exact
    checks["coverage_fields_exact"] = coverage_fields_exact
    checks["missing_components_score_zero"] = missing_zero
    checks["all_totals_equal_sum"] = totals_equal_sum
    checks["personal_kb_confirmation_recomputed_exact"] = (
        personal_kb_confirmation_exact
    )

    reranked = sorted(results, key=personal_kb_ranking_key)
    top10 = payload.get("ranking_top10") or []
    expected_top_count = min(10, len(results))
    checks["top10_exact_from_eligible_pool"] = bool(
        isinstance(top10, list)
        and len(top10) == expected_top_count
        and [item.get("symbol") for item in top10] == [item.get("symbol") for item in reranked[:expected_top_count]]
    )
    checks["tie_rule_exact"] = symbols == [str(item.get("symbol") or "") for item in reranked]
    checks["top10_risk_labels_preserved"] = all(
        deep_close(top10[index], reranked[index]) for index in range(min(len(top10), len(reranked)))
    )

    expected_missing_symbols: list[str] = []
    expected_missing_details: list[dict[str, str]] = []
    missing_unavailable_zero = True
    for symbol in master_symbols:
        local = recomputed_local_by_symbol.get(symbol) or {}
        reasons: list[str] = []
        unavailable: set[str] = set()
        if int(local.get("bond_history_points") or 0) == 0:
            reasons.append("bond_day_history_missing")
            unavailable.update(("c1_price_activity", "c3_premium", "c7_scr90_convergence", "c8_scr70_convergence", "c11_turnover5"))
        if int(local.get("stock_history_points") or 0) == 0:
            reasons.append("underlying_day_history_missing")
            unavailable.update(("c3_premium", "c4_golden_ignition", "c5_feilong_cross", "c6_youzi_inflow"))
        if reasons:
            expected_missing_symbols.append(symbol)
            expected_missing_details.append({"symbol": symbol, "reason": ";".join(reasons)})
            item = next((node for node in evaluated_results if node.get("symbol") == symbol), {})
            missing_unavailable_zero &= item.get("risk_level") == "RED"
            for criterion_id in unavailable:
                component = (item.get("score_components") or {}).get(criterion_id) or {}
                missing_unavailable_zero &= bool(
                    component.get("data_status") == "MISSING"
                    and close(float(component.get("normalized_score", math.nan)), 0.0)
                    and close(float(component.get("earned_score", math.nan)), 0.0)
                )
    checks["missing_local_retained_exact"] = bool(
        payload.get("missing_local_symbols") == expected_missing_symbols
        and payload.get("missing_local_details") == expected_missing_details
        and int(payload.get("missing_local_count", -1)) == len(expected_missing_symbols)
        and int(payload.get("unavailable_local_retained_count", -1)) == len(expected_missing_symbols)
        and set(expected_missing_symbols).issubset(set(evaluated_symbols))
        and missing_unavailable_zero
    )

    expected_partial_details = [
        {
            "symbol": symbol,
            "bond_latest_date": local.get("bond_latest_date"),
            "stock_latest_date": local.get("stock_latest_date"),
            "bond_history_points": local.get("bond_history_points"),
            "stock_history_points": local.get("stock_history_points"),
            "risk_veto_reasons": local.get("risk_veto_reasons"),
        }
        for symbol, local in sorted(recomputed_local_by_symbol.items())
        if local.get("bond_full_lookback") is not True or local.get("stock_signal_available") is not True
    ]
    local_synchronized_count = sum(
        local.get("bond_current") is True and local.get("stock_current") is True
        for local in recomputed_local_by_symbol.values()
    )
    full_lookback_count = sum(
        local.get("bond_full_lookback") is True for local in recomputed_local_by_symbol.values()
    )
    checks["technical_data_partition_exact"] = bool(
        len(recomputed_local_by_symbol) == len(master_records)
        and int(payload.get("local_synchronized_count", -1)) == local_synchronized_count
        and int(payload.get("full_lookback_count", -1)) == full_lookback_count
        and int(payload.get("technical_partial_count", -1)) == len(expected_partial_details)
        and deep_close(payload.get("technical_partial_details") or [], expected_partial_details)
    )

    stock_symbols = sorted({
        master_records[symbol]["underlying_symbol"]
        for symbol, local in recomputed_local_by_symbol.items()
        if local.get("stock_signal_available") is True
    })
    formula_bond_symbols = sorted(
        symbol for symbol, local in recomputed_local_by_symbol.items() if local.get("bond_full_lookback") is True
    )
    formula = payload.get("formula_coverage") or {}
    field_coverage = formula.get("field_coverage") or {}
    checks["formula_coverage_complete"] = bool(
        formula.get("complete") is True
        and formula.get("node_counts_complete") is True
        and not formula.get("errors")
        and set(field_coverage) == {"feilong", "scr90", "scr70", "bigbull"}
        and all(node.get("complete") is True for node in field_coverage.values())
        and formula.get("history_count") == {"feilong": 600, "scr90": 0, "scr70": 0, "bigbull": 600}
        and int(formula.get("expected_underlyings", -1)) == len(stock_symbols)
        and int(formula.get("expected_bonds", -1)) == len(formula_bond_symbols)
        and int(formula.get("scored_bonds", -1)) == len(evaluated_results) == len(master_records)
        and formula.get("formula_ineligible_bonds") == sorted(master_symbol_set - set(formula_bond_symbols))
        and int(formula.get("feilong_underlyings", -1)) == len(stock_symbols)
        and int(formula.get("bigbull_underlyings", -1)) == len(stock_symbols)
        and int(formula.get("scr90_bonds", -1)) == len(formula_bond_symbols)
        and int(formula.get("scr70_bonds", -1)) == len(formula_bond_symbols)
        and set((evidence_formulas.get("feilong") or {})) == set(stock_symbols)
        and set((evidence_formulas.get("bigbull") or {})) == set(stock_symbols)
        and set((evidence_formulas.get("scr90") or {})) == set(formula_bond_symbols)
        and set((evidence_formulas.get("scr70") or {})) == set(formula_bond_symbols)
    )

    risk_counts = {level: sum(item.get("risk_level") == level for item in top10) for level in ("RED", "YELLOW", "GREEN")}
    policy = payload.get("execution_policy") or {}
    checks["risk_counts_top10_exact"] = payload.get("risk_counts_top10") == risk_counts
    checks["execution_policy_exact"] = bool(
        policy.get("mode") == "post_close_manual_decision_support"
        and policy.get("automatic_order") is False
        and policy.get("execution_eligible") is (risk_counts["GREEN"] > 0)
        and policy.get("strong_redemption_announcements_verified") is True
    )
    expected_condition_counts = {
        key: sum(bool(item.get("conditions", {}).get(key)) for item in results)
        for key in (*diagnostic_condition_keys, "c10_big_bull_red_preference")
    }
    checks["condition_pass_counts_exact"] = payload.get("condition_pass_counts") == expected_condition_counts

    source_nodes = list(walk_path_nodes(source_files))
    checks["source_metadata_schema_complete"] = len(source_nodes) == 9 and all(valid_source_node(node) for node in source_nodes)
    source_hashes_match = checks["source_metadata_schema_complete"]
    for node in source_nodes:
        if not valid_source_node(node):
            source_hashes_match = False
            continue
        path = Path(node["path"])
        source_hashes_match &= bool(
            path.is_file() and path.stat().st_size == int(node["size"]) and sha256(path) == node["sha256"]
        )
    checks["source_hashes_match"] = source_hashes_match
    try:
        latest_benchmark = latest_tdx_benchmark_date(payload)
    except (OSError, KeyError, ValueError):
        latest_benchmark = ""
    checks["cutoff_matches_tdx"] = cutoff == latest_benchmark == (calendar[-1] if calendar else "")
    manifest_aliases = {
        str(alias)
        for node in day_manifest.get("inputs") or []
        for alias in node.get("lookup_symbols") or []
    }
    required_day_aliases = {"999999.SH", *master_symbol_set}
    required_day_aliases.update(master["underlying_symbol"] for master in master_records.values())
    required_day_aliases.update(str(value) for value in heat.get("attempted_lookup_symbols") or [])
    checks["day_manifest_scoring_and_heat_inputs_complete"] = required_day_aliases.issubset(manifest_aliases)

    final_day_contract, final_day_current, final_day_checks, _final_day_reader = validate_day_input_manifest(
        day_manifest,
        run_id,
        cutoff,
    )
    checks["day_input_manifest_v2_contract_exact"] = bool(
        checks["day_input_manifest_v2_contract_exact"] and final_day_contract
    )
    checks["day_input_manifest_current"] = bool(checks["day_input_manifest_current"] and final_day_current)
    day_input_checks = final_day_checks
    if final_day_contract and not final_day_current:
        return emit_day_update_race(args.output, run_id, args.attempt, checks, final_day_checks)

    status = "PASS" if checks and all(checks.values()) else "FAIL"
    output = {
        "status": status,
        "schema": "TDX-CONVERTIBLE-BOND-WEIGHTED-VERIFY-V5",
        "run_id": run_id,
        "input": {"path": str(args.input), "size": args.input.stat().st_size, "sha256": sha256(args.input)},
        "cutoff_trade_date": cutoff,
        "universe_count_recomputed": len(master_records),
        "evaluated_count": len(evaluated_results),
        "eligible_count": len(results),
        "ranked_count": len(results),
        "hard_excluded_count": len(excluded_results),
        "score_model": {"version": model.get("version"), "criterion_ids": list(ids), "weights": weights, "weight_sum": sum(weights.values())},
        "risk_counts_top10": risk_counts,
        "execution_policy": policy,
        "checks": checks,
        "diagnostics": {
            "independent_bond_master": independent_master_diagnostics,
            "local_condition_mismatches": local_condition_mismatches,
            "component_mismatch_symbols": component_mismatch_symbols,
            "formula_mismatch_symbols": formula_mismatch_symbols,
            "sector_heat_mismatch_symbols": heat_mismatch_symbols,
            "hard_exclusion_mismatches": hard_exclusion_mismatches,
            "personal_kb_confirmation_mismatch_symbols": (
                personal_kb_confirmation_mismatch_symbols
            ),
            "day_input_mismatches": [
                item for item in day_input_checks
                if not item["contract"] or not item["unique"] or not item["current"]
            ],
        },
        "top10": [
            {
                "rank": item.get("rank"),
                "symbol": item.get("symbol"),
                "name": item.get("name"),
                "underlying_symbol": item.get("underlying_symbol"),
                "underlying_name": item.get("underlying_name"),
                "score": item.get("score_total_raw"),
                "big_bull_red_preference": item.get("big_bull_red_preference"),
                "risk_level": item.get("risk_level"),
                "risk_labels": [*item.get("risk_veto_reasons", []), *item.get("risk_warning_labels", [])],
            }
            for item in top10
        ],
    }
    output = canonicalize_business_payload(output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(args.output, output)
    readback = json.loads(args.output.read_text(encoding="utf-8"))
    if readback.get("status") != status or readback.get("checks") != checks or readback.get("top10") != output["top10"]:
        raise RuntimeError("V5 verification JSON readback mismatch")
    failed_checks = [name for name, passed in checks.items() if not passed]
    print(json.dumps({
        "status": status,
        "output": str(args.output),
        "output_size": args.output.stat().st_size,
        "output_sha256": sha256(args.output),
        "failed_checks": failed_checks,
        "top10": output["top10"],
    }, ensure_ascii=False, indent=2))
    if status == "PASS":
        return 0
    return 2


def _argument_path(option: str) -> Path | None:
    arguments = sys.argv[1:]
    for index, value in enumerate(arguments):
        if value == option and index + 1 < len(arguments):
            return Path(arguments[index + 1])
        prefix = option + "="
        if value.startswith(prefix):
            return Path(value[len(prefix):])
    return None


def _persist_structured_failure(exc: BaseException) -> int:
    output_path = _argument_path("--output")
    input_path = _argument_path("--input")
    failure = {
        "status": "FAIL",
        "schema": "TDX-CONVERTIBLE-BOND-VERIFY-FAIL-1",
        "input": str(input_path) if input_path is not None else None,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "checks": {"structured_execution": False},
        "failed_checks": ["structured_execution"],
    }
    if isinstance(exc, SystemExit):
        failure["exit_code"] = exc.code
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(output_path, failure)
        readback = json.loads(output_path.read_text(encoding="utf-8"))
        if readback.get("status") != "FAIL" or readback.get("error_type") != type(exc).__name__:
            raise RuntimeError("structured failure JSON readback mismatch") from exc
    print(json.dumps(failure, ensure_ascii=False, indent=2))
    return 2


def main() -> int:
    try:
        return _main_impl()
    except SystemExit as exc:
        if exc.code in (None, 0):
            raise
        return _persist_structured_failure(exc)
    except Exception as exc:
        return _persist_structured_failure(exc)


if __name__ == "__main__":
    raise SystemExit(main())
