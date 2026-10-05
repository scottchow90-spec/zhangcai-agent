# -*- coding: utf-8 -*-
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import hashlib
import math
import os
import re
import struct
from pathlib import Path
from typing import Any


RAW_SCORE_VERSION = "CORE-MAINLINE-100-V2"
MODEL_VERSION = "CORE-MAINLINE-CLOSE-V3"
COMPONENT_WEIGHTS = {
    "market_strength": 15,
    "breadth": 15,
    "hierarchy": 10,
    "ladder_completeness": 10,
    "constituent_scale": 10,
    "capital": 15,
    "catalyst": 10,
    "continuity": 10,
    "dominance": 5,
}
REQUIRED_BOARD_FIELDS = (
    "rank",
    "sector_return_pct",
    "limit_up_count",
    "market_limit_up_count",
    "leader_count",
    "mid_tier_count",
    "first_board_count",
    "capacity_count",
    "three_board_count",
    "two_board_count",
    "one_board_count",
    "constituent_count",
    "capital_concentration_pct",
    "turnover_expansion_ratio",
    "catalyst_verified",
    "catalyst_level",
    "catalyst_source_count",
    "continuity_days",
    "divergence_repaired",
    "reflow_confirmed",
    "runner_up_gap_pct",
)
CLOSE_CONFIRMATION_FIELDS = (
    "source_session_coverage",
    "intraday_sample_count",
    "intraday_coverage_ratio",
    "early_seal_ratio",
    "zero_open_ratio",
    "late_reseal_ratio",
    "seal_fund_turnover_ratio",
    "market_early_seal_ratio",
    "market_zero_open_ratio",
    "market_late_reseal_ratio",
    "market_seal_fund_turnover_ratio",
    "market_seal_rate",
)
CLOSE_CONFIRMATION_THRESHOLDS = {
    "raw_score_min": 60.0,
    "rank_max": 5,
    "limit_up_market_share_min_pct": 8.0,
    "source_session_coverage_min": 0.80,
    "intraday_sample_count_min": 3,
    "intraday_coverage_ratio_min": 0.60,
    "relative_quality_signal_count_min": 2,
}
THEME_ALIASES = {
    "ai应用": "人工智能应用",
    "人工智能应用": "人工智能应用",
    "机器人": "机器人",
    "算力": "算力",
}
TDX_DAY_RECORD = struct.Struct("<IIIIIfII")
_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_tdx_root

TDX_ROOT = resolve_tdx_root()
TDX_VIPDOC = Path(os.environ.get("TDX_VIPDOC", str(TDX_ROOT / "vipdoc"))).expanduser().resolve()
TDX_HQ_CACHE = Path(os.environ.get("TDX_HQ_CACHE", str(TDX_ROOT / "T0002" / "hq_cache"))).expanduser().resolve()
TDX_INFOHARBOR_BLOCK = Path(os.environ.get(
    "TDX_INFOHARBOR_BLOCK",
    str(TDX_HQ_CACHE / "infoharbor_block.dat"),
)).expanduser().resolve()
TDX_ZS_CONFIG = Path(os.environ.get("TDX_ZS_CONFIG", str(TDX_HQ_CACHE / "tdxzs.cfg")))
TDX_HY_CONFIG = Path(os.environ.get("TDX_HY_CONFIG", str(TDX_HQ_CACHE / "tdxhy.cfg")))
TDX_BASE_DBF = Path(os.environ.get("TDX_BASE_DBF", str(TDX_HQ_CACHE / "base.dbf")))
TDX_CW_DIR = Path(os.environ.get("TDX_CW_DIR", str(TDX_VIPDOC / "cw")))
TDX_GPCW_HEADER = struct.Struct("<hIHIII")
TDX_GPCW_ITEM = struct.Struct("<6scI")
TDX_PARENT_NET_PROFIT_INDEX = 95
TDX_EQUITY_PREFIXES = (
    "000", "001", "002", "003", "300", "301", "600", "601", "603", "605",
    "688", "689", "830", "831", "832", "834", "835", "836", "837", "838",
    "839", "870", "871", "872", "873", "874", "875", "876", "877", "878",
    "879", "880", "881", "882", "883", "884", "885", "886", "887", "888",
    "889", "890", "891", "892", "893", "894", "895", "896", "897", "898", "899", "920",
)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    return int(_float(value, float(default)))


def _points(value: float, bands: list[tuple[float, float]]) -> float:
    for threshold, points in bands:
        if value >= threshold:
            return points
    return 0.0


def normalize_code(value: Any) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits[-6:] if len(digits) >= 6 else digits.zfill(6) if digits else ""


def normalize_theme(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[\s\-_·/\\（）()]+", "", text)
    for suffix in ("产业链", "概念板块", "行业板块", "概念", "板块", "行业"):
        if text.endswith(suffix) and len(text) > len(suffix):
            text = text[: -len(suffix)]
            break
    return THEME_ALIASES.get(text, text)


def split_themes(value: Any) -> list[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = re.split(r"[、,，;；|/+]+", str(value or ""))
    result: list[str] = []
    for item in raw:
        normalized = normalize_theme(item)
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def _clock_seconds(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    if ":" in text:
        parts = text.split(":")
        if len(parts) not in {2, 3} or not all(part.isdigit() for part in parts):
            return None
        hour, minute = int(parts[0]), int(parts[1])
        second = int(parts[2]) if len(parts) == 3 else 0
    else:
        digits = re.sub(r"\D", "", text)
        if not digits:
            return None
        digits = digits[-6:].zfill(6)
        hour, minute, second = int(digits[:2]), int(digits[2:4]), int(digits[4:])
    if hour > 23 or minute > 59 or second > 59:
        return None
    return hour * 3600 + minute * 60 + second


def _ratio(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    is_percent = text.endswith("%")
    number = _float(text.rstrip("%"), float("nan"))
    if math.isnan(number):
        return None
    if is_percent or number > 1:
        number /= 100
    return min(1.0, max(0.0, number))


def parse_duanxianxia_pool_row(row: Any) -> dict[str, Any] | None:
    if not isinstance(row, list) or len(row) < 9:
        return None
    code = normalize_code(row[0])
    if not code:
        return None
    return {
        "code": code,
        "name": row[1] if len(row) > 1 else "",
        "seal_fund": _float(row[3]) if len(row) > 3 else None,
        "open_count": _int(row[4]) if len(row) > 4 and row[4] is not None else None,
        "latest_seal_time": row[5] if len(row) > 5 else None,
        "reason": row[6] if len(row) > 6 else "",
        "board_label": row[7] if len(row) > 7 else "",
        "turnover_amount": _float(row[8]) if len(row) > 8 else None,
        "free_float_market_cap": _float(row[9]) if len(row) > 9 else None,
        "source_nature": row[10] if len(row) > 10 else None,
        "first_seal_time": row[12] if len(row) > 12 else None,
    }


def close_quality_metrics(stocks: list[dict[str, Any]], denominator: int) -> dict[str, Any]:
    samples = [
        stock for stock in stocks
        if _clock_seconds(stock.get("first_seal_time")) is not None
        and _clock_seconds(stock.get("latest_seal_time")) is not None
        and stock.get("open_count") is not None
    ]
    sample_count = len(samples)
    early_cutoff = 10 * 3600 + 30 * 60
    late_cutoff = 14 * 3600 + 30 * 60
    positive_turnover = [stock for stock in stocks if _float(stock.get("turnover_amount")) > 0]
    total_turnover = sum(_float(stock.get("turnover_amount")) for stock in positive_turnover)
    total_seal_fund = sum(max(0.0, _float(stock.get("seal_fund"))) for stock in positive_turnover)
    return {
        "intraday_sample_count": sample_count,
        "intraday_coverage_ratio": min(1.0, sample_count / denominator) if denominator > 0 else None,
        "early_seal_ratio": (
            sum(_clock_seconds(stock.get("first_seal_time")) <= early_cutoff for stock in samples) / sample_count
            if sample_count else None
        ),
        "zero_open_ratio": (
            sum(_int(stock.get("open_count")) == 0 for stock in samples) / sample_count
            if sample_count else None
        ),
        "late_reseal_ratio": (
            sum(_clock_seconds(stock.get("latest_seal_time")) >= late_cutoff for stock in samples) / sample_count
            if sample_count else None
        ),
        "seal_fund_turnover_ratio": total_seal_fund / total_turnover if total_turnover > 0 else None,
    }


def source_session_alignment(dxx_codes: set[str], lianban_codes: set[str]) -> dict[str, Any]:
    if not dxx_codes or not lianban_codes:
        return {
            "coverage": None,
            "intersection_count": 0,
            "dxx_count": len(dxx_codes),
            "lianban_count": len(lianban_codes),
            "jaccard": None,
        }
    intersection = dxx_codes & lianban_codes
    union = dxx_codes | lianban_codes
    return {
        "coverage": min(len(intersection) / len(dxx_codes), len(intersection) / len(lianban_codes)),
        "intersection_count": len(intersection),
        "dxx_count": len(dxx_codes),
        "lianban_count": len(lianban_codes),
        "jaccard": len(intersection) / len(union),
    }


def theme_mentioned_in_text(theme: Any, text: Any) -> bool:
    normalized_theme = normalize_theme(theme)
    normalized_text = str(text or "").strip().lower()
    normalized_text = re.sub(r"[\s\-_·/\\（）()]+", "", normalized_text)
    variants = {normalized_theme}
    variants.update(
        alias for alias, canonical in THEME_ALIASES.items()
        if canonical == normalized_theme
    )
    return bool(normalized_theme and any(item in normalized_text for item in variants if item))


def deduplicate_stocks(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for source in items:
        code = normalize_code(source.get("code"))
        if not code:
            continue
        current = merged.setdefault(code, {"code": code, "themes": []})
        themes = split_themes(source.get("themes", []))
        for theme in themes:
            if theme not in current["themes"]:
                current["themes"].append(theme)
        for key, value in source.items():
            if key in {"code", "themes"} or value in (None, "", []):
                continue
            if key in {"board_count", "amount"}:
                current[key] = max(_float(current.get(key)), _float(value))
            elif key == "reason" and current.get(key):
                if str(value) not in str(current[key]):
                    current[key] = f"{current[key]}; {value}"
            else:
                current[key] = value
    return list(merged.values())


def attach_historical_stock_authenticity(
    stocks: list[dict[str, Any]],
    lianban_history: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = [dict(stock) for stock in stocks]
    by_code = {
        normalize_code(stock.get("code")): stock
        for stock in result
        if normalize_code(stock.get("code"))
    }
    for snapshot in lianban_history:
        if not isinstance(snapshot, dict) or snapshot.get("status") != "CLEAN_PASS":
            continue
        target_date = str(snapshot.get("target_date", "")).strip()
        sources = snapshot.get("sources", {})
        page = sources.get("page", {}) if isinstance(sources, dict) else {}
        source_url = str(page.get("url", "")).strip() if isinstance(page, dict) else ""
        if not target_date or not source_url:
            continue
        details = snapshot.get("page_details", {})
        items = details.get("stock_items", []) if isinstance(details, dict) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            code = normalize_code(item.get("code"))
            themes = split_themes([item.get("theme"), item.get("board")])
            if not code or not themes:
                continue
            stock = by_code.get(code)
            if stock is None:
                stock = {"code": code, "themes": []}
                result.append(stock)
                by_code[code] = stock
            evidence = {
                "source": "连板网",
                "source_status": "CLEAN_PASS",
                "target_date": target_date,
                "source_url": source_url,
                "themes": themes,
                "reason": str(item.get("reason", "")).strip(),
            }
            records = stock.setdefault("historical_theme_evidence", [])
            if evidence not in records:
                records.append(evidence)
    return result


def stock_theme_candidates(stock: dict[str, Any]) -> list[str]:
    themes = split_themes(stock.get("themes", []))
    records = stock.get("historical_theme_evidence", [])
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        if (
            record.get("source_status") != "CLEAN_PASS"
            or not str(record.get("target_date", "")).strip()
            or not str(record.get("source_url", "")).strip()
        ):
            continue
        for theme in split_themes(record.get("themes", [])):
            if theme not in themes:
                themes.append(theme)
    return themes


def load_tdx_constituent_catalog(path: Path = TDX_INFOHARBOR_BLOCK) -> list[dict[str, Any]]:
    try:
        raw_bytes = path.read_bytes()
        text = raw_bytes.decode("gb18030", errors="ignore")
    except OSError:
        return []
    catalog: list[dict[str, Any]] = []
    source_name = ""
    index_code = ""
    codes: list[str] = []
    source_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    def flush() -> None:
        if not source_name:
            return
        unique_codes = list(dict.fromkeys(
            code for code in codes if code.startswith(TDX_EQUITY_PREFIXES)
        ))
        display_name = re.sub(r"^[A-Z0-9]{2,8}_", "", source_name).strip()
        if display_name and unique_codes:
            catalog.append({
                "name": display_name,
                "source_name": source_name,
                "codes": unique_codes,
                "member_count": len(unique_codes),
                "index_code": index_code,
                "source_path": str(path),
                "source_sha256": source_sha256,
                "match_basis": "infoharbor_named_block",
            })

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            flush()
            header = line[1:].split(",")
            source_name = header[0].strip()
            index_code = normalize_code(header[2]) if len(header) > 2 else ""
            codes = []
            continue
        for token in line.split(","):
            match = re.fullmatch(r"[0123]#(\d{6})", token.strip())
            if match:
                codes.append(match.group(1))
    flush()
    return catalog


def load_tdx_industry_catalog(
    zs_path: Path = TDX_ZS_CONFIG,
    hy_path: Path = TDX_HY_CONFIG,
) -> list[dict[str, Any]]:
    try:
        zs_bytes = zs_path.read_bytes()
        hy_bytes = hy_path.read_bytes()
    except OSError:
        return []
    zs_text = zs_bytes.decode("gb18030", errors="ignore")
    hy_text = hy_bytes.decode("gb18030", errors="ignore")
    industry_rows: list[tuple[str, str]] = []
    for raw in hy_text.splitlines():
        parts = raw.strip().split("|")
        if len(parts) < 3:
            continue
        code = normalize_code(parts[1])
        block_code = parts[2].strip()
        if code.startswith(TDX_EQUITY_PREFIXES) and block_code:
            industry_rows.append((code, block_code))
    catalog: list[dict[str, Any]] = []
    for raw in zs_text.splitlines():
        parts = raw.strip().split("|")
        if len(parts) < 6:
            continue
        name = parts[0].strip()
        index_code = normalize_code(parts[1])
        block_code = parts[5].strip()
        if not name or not index_code or not block_code.startswith("T"):
            continue
        codes = list(dict.fromkeys(
            code for code, member_block in industry_rows
            if member_block.startswith(block_code)
        ))
        if not codes:
            continue
        catalog.append({
            "name": name,
            "source_name": f"TDXHY_{block_code}_{name}",
            "codes": codes,
            "member_count": len(codes),
            "index_code": index_code,
            "source_path": f"{zs_path}|{hy_path}",
            "source_sha256": {
                "tdxzs": hashlib.sha256(zs_bytes).hexdigest(),
                "tdxhy": hashlib.sha256(hy_bytes).hexdigest(),
            },
            "match_basis": "tdxhy_descendant_prefix",
        })
    return catalog


def _read_tdx_base_dbf(path: Path) -> dict[str, dict[str, str]]:
    try:
        data = path.read_bytes()
    except OSError:
        return {}
    if len(data) < 33:
        return {}
    record_count = struct.unpack_from("<I", data, 4)[0]
    header_length = struct.unpack_from("<H", data, 8)[0]
    record_length = struct.unpack_from("<H", data, 10)[0]
    if header_length > len(data) or record_length <= 1:
        return {}
    fields: list[tuple[str, int]] = []
    cursor = 32
    while cursor + 32 <= header_length and data[cursor] != 0x0D:
        descriptor = data[cursor : cursor + 32]
        name = descriptor[:11].split(b"\0", 1)[0].decode("ascii", errors="ignore")
        fields.append((name, descriptor[16]))
        cursor += 32
    rows: dict[str, dict[str, str]] = {}
    for index in range(record_count):
        start = header_length + index * record_length
        record = data[start : start + record_length]
        if len(record) != record_length or record[:1] == b"*":
            continue
        position = 1
        row: dict[str, str] = {}
        for name, length in fields:
            row[name] = record[position : position + length].decode("ascii", errors="ignore").strip()
            position += length
        code = normalize_code(row.get("GPDM"))
        if code.startswith(TDX_EQUITY_PREFIXES):
            rows[code] = row
    return rows


def _read_tdx_gpcw_field(path: Path, field_index: int) -> dict[str, float]:
    try:
        data = path.read_bytes()
    except OSError:
        return {}
    if len(data) < TDX_GPCW_HEADER.size:
        return {}
    _version, _report_date, stock_count, _unused, report_size, _reserved = TDX_GPCW_HEADER.unpack_from(data, 0)
    field_count = report_size // 4
    if field_index < 0 or field_index >= field_count:
        return {}
    values: dict[str, float] = {}
    for index in range(stock_count):
        item_offset = TDX_GPCW_HEADER.size + index * TDX_GPCW_ITEM.size
        if item_offset + TDX_GPCW_ITEM.size > len(data):
            break
        code_raw, _market, record_offset = TDX_GPCW_ITEM.unpack_from(data, item_offset)
        value_offset = record_offset + field_index * 4
        if value_offset + 4 > len(data):
            continue
        value = struct.unpack_from("<f", data, value_offset)[0]
        code = normalize_code(code_raw.decode("ascii", errors="ignore"))
        if code.startswith(TDX_EQUITY_PREFIXES) and math.isfinite(value):
            values[code] = float(value)
    return values


def load_tdx_interim_growth_catalog(
    trade_date: Any,
    base_path: Path = TDX_BASE_DBF,
    prior_path: Path | None = None,
) -> dict[str, Any] | None:
    digits = re.sub(r"\D", "", str(trade_date or ""))[:8]
    if len(digits) != 8:
        return None
    trade_date_int = int(digits)
    year = trade_date_int // 10000
    disclosure_start = year * 10000 + 701
    disclosure_end = min(trade_date_int, year * 10000 + 831)
    if disclosure_end < disclosure_start:
        return None
    active_prior_path = prior_path or (TDX_CW_DIR / f"gpcw{year - 1}0630.dat")
    current_rows = _read_tdx_base_dbf(base_path)
    prior_profit = _read_tdx_gpcw_field(active_prior_path, TDX_PARENT_NET_PROFIT_INDEX)
    codes: list[str] = []
    for code, row in current_rows.items():
        update_date = _int(row.get("GXRQ"))
        if not (disclosure_start <= update_date <= disclosure_end) or code not in prior_profit:
            continue
        current_profit = _float(row.get("JLY"), float("nan")) * 1000.0
        if math.isfinite(current_profit) and current_profit > prior_profit[code]:
            codes.append(code)
    codes.sort()
    if not codes:
        return None
    try:
        base_sha256 = hashlib.sha256(base_path.read_bytes()).hexdigest()
        prior_sha256 = hashlib.sha256(active_prior_path.read_bytes()).hexdigest()
    except OSError:
        return None
    return {
        "name": "中报增长",
        "source_name": "TDX_FINANCE_INTERIM_GROWTH",
        "codes": codes,
        "member_count": len(codes),
        "index_code": "",
        "source_path": f"{base_path}|{active_prior_path}",
        "base_dbf_sha256": base_sha256,
        "prior_gpcw_sha256": prior_sha256,
        "match_basis": "tdx_current_parent_profit_vs_prior_h1",
        "disclosure_window": [disclosure_start, disclosure_end],
        "current_profit_unit": "base_dbf_JLY_thousand_cny",
        "prior_profit_field": "gpcw_col96_parent_net_profit_cny",
    }


def load_runtime_tdx_constituent_catalog(trade_date: Any) -> list[dict[str, Any]]:
    catalog = load_tdx_constituent_catalog()
    catalog.extend(load_tdx_industry_catalog())
    interim_growth = load_tdx_interim_growth_catalog(trade_date)
    if interim_growth:
        catalog.append(interim_growth)
    return catalog


def resolve_tdx_constituent_block(
    theme: str,
    member_codes: list[str],
    catalog: list[dict[str, Any]],
) -> dict[str, Any] | None:
    normalized_theme = normalize_theme(theme)
    active_codes = {normalize_code(code) for code in member_codes if normalize_code(code)}
    candidates: list[tuple[tuple[int, int, float, int], dict[str, Any]]] = []
    for item in catalog:
        normalized_name = normalize_theme(item.get("name"))
        if not normalized_name:
            continue
        exact_name = normalized_name == normalized_theme
        related_name = bool(
            normalized_theme
            and normalized_name
            and (normalized_theme in normalized_name or normalized_name in normalized_theme)
        )
        if not exact_name and not related_name:
            continue
        codes = {normalize_code(code) for code in item.get("codes", []) if normalize_code(code)}
        overlap = len(active_codes & codes)
        if not exact_name and overlap < 1:
            continue
        overlap_ratio = overlap / len(active_codes) if active_codes else 0.0
        constituent_count = _int(item.get("member_count"), len(codes))
        rank_key = (1 if exact_name else 0, overlap, overlap_ratio, constituent_count)
        candidates.append((rank_key, {
            "source_name": str(item.get("source_name", "")),
            "name": str(item.get("name", "")),
            "constituent_count": constituent_count,
            "overlap_count": overlap,
            "overlap_ratio": round(overlap_ratio, 6),
            "match_type": "exact_name" if exact_name else "related_name_with_member_overlap",
            "match_basis": item.get("match_basis"),
            "index_code": normalize_code(item.get("index_code")),
            "source_path": item.get("source_path"),
            "source_sha256": item.get("source_sha256"),
            "base_dbf_sha256": item.get("base_dbf_sha256"),
            "prior_gpcw_sha256": item.get("prior_gpcw_sha256"),
        }))
    if not candidates:
        return None
    candidates.sort(key=lambda pair: pair[0], reverse=True)
    return candidates[0][1]


def exact_board_level(stock: dict[str, Any]) -> int:
    count = _int(stock.get("board_count"))
    if count > 0:
        return count
    label = str(stock.get("board_label", ""))
    match = re.search(r"(?<!天)(\d+)连板", label)
    if match:
        return int(match.group(1))
    return 1 if label in {"首板", "首板涨停"} else 0


def _tdx_day_amounts(code: str, expected_date: Any = None) -> dict[str, Any] | None:
    prefix = "sh" if code.startswith(("5", "6", "9")) else "bj" if code.startswith(("4", "8")) else "sz"
    path = TDX_VIPDOC / prefix / "lday" / f"{prefix}{code}.day"
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < TDX_DAY_RECORD.size * 2:
        return None
    previous = TDX_DAY_RECORD.unpack(data[-TDX_DAY_RECORD.size * 2 : -TDX_DAY_RECORD.size])
    current = TDX_DAY_RECORD.unpack(data[-TDX_DAY_RECORD.size :])
    expected_digits = re.sub(r"\D", "", str(expected_date or ""))[:8]
    if expected_digits and current[0] != int(expected_digits):
        return None
    if current[0] <= previous[0] or previous[5] <= 0 or current[5] <= 0:
        return None
    return {
        "previous_day_amount": float(previous[5]),
        "current_day_amount": float(current[5]),
        "previous_day_date": previous[0],
        "current_day_date": current[0],
        "turnover_source_path": str(path),
        "turnover_source_sha256": hashlib.sha256(data).hexdigest(),
    }


def read_tdx_sector_return(
    index_code: Any,
    expected_date: Any = None,
    vipdoc: Path = TDX_VIPDOC,
) -> dict[str, Any] | None:
    code = normalize_code(index_code)
    if not code:
        return None
    prefix = "sh" if code.startswith(("0", "8", "9")) else "sz"
    path = vipdoc / prefix / "lday" / f"{prefix}{code}.day"
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < TDX_DAY_RECORD.size * 2 or len(data) % TDX_DAY_RECORD.size:
        return None
    previous = TDX_DAY_RECORD.unpack(data[-TDX_DAY_RECORD.size * 2 : -TDX_DAY_RECORD.size])
    current = TDX_DAY_RECORD.unpack(data[-TDX_DAY_RECORD.size :])
    expected_digits = re.sub(r"\D", "", str(expected_date or ""))[:8]
    if expected_digits and current[0] != int(expected_digits):
        return None
    previous_close = _float(previous[4]) / 100.0
    current_close = _float(current[4]) / 100.0
    if current[0] <= previous[0] or previous_close <= 0 or current_close <= 0:
        return None
    return {
        "index_code": code,
        "return_pct": (current_close / previous_close - 1.0) * 100.0,
        "previous_date": previous[0],
        "current_date": current[0],
        "previous_close": previous_close,
        "current_close": current_close,
        "source_path": str(path),
        "source_sha256": hashlib.sha256(data).hexdigest(),
    }


def cross_validate_theme_catalyst(
    theme: Any,
    duanxianxia_live_items: list[dict[str, Any]],
    lianban_stock_items: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized_theme = normalize_theme(theme)
    dxx_by_code = {
        normalize_code(item.get("code")): str(item.get("ztyy", "")).strip()
        for item in duanxianxia_live_items
        if isinstance(item, dict)
        and normalize_code(item.get("code"))
        and theme_mentioned_in_text(normalized_theme, item.get("ztyy", ""))
    }
    lianban_by_code = {
        normalize_code(item.get("code")): str(item.get("reason", "")).strip()
        for item in lianban_stock_items
        if isinstance(item, dict)
        and normalize_code(item.get("code"))
        and theme_mentioned_in_text(normalized_theme, item.get("reason", ""))
    }
    matched_codes = sorted(set(dxx_by_code) & set(lianban_by_code))
    return {
        "verified": bool(matched_codes),
        "source_count": 2 if matched_codes else 0,
        "matched_codes": matched_codes,
        "evidence": [
            {
                "code": code,
                "duanxianxia_reason": dxx_by_code[code],
                "lianban_reason": lianban_by_code[code],
            }
            for code in matched_codes
        ],
        "match_basis": "same_stock_theme_reason_cross_source",
    }


def compute_return_lead_gaps(theme_returns: dict[str, Any]) -> dict[str, float | None]:
    available = sorted(
        (
            (normalize_theme(name), float(value))
            for name, value in theme_returns.items()
            if normalize_theme(name) and value is not None and math.isfinite(_float(value, float("nan")))
        ),
        key=lambda item: (-item[1], item[0]),
    )
    result = {normalize_theme(name): None for name in theme_returns if normalize_theme(name)}
    if len(available) < 2:
        return result
    leader_name, leader_return = available[0]
    runner_return = available[1][1]
    result[leader_name] = leader_return - runner_return
    for name, value in available[1:]:
        result[name] = value - leader_return
    return result


def unavailable_mainline(reason: str) -> dict[str, Any]:
    return {
        "model_version": MODEL_VERSION,
        "raw_score_version": RAW_SCORE_VERSION,
        "name": "",
        "status": "DEGRADED",
        "score": 0.0,
        "raw_score": 0.0,
        "stars": 0.0,
        "decision_eligible": False,
        "components": {name: {"score": 0.0, "weight": weight, "evidence": []} for name, weight in COMPONENT_WEIGHTS.items()},
        "missing_evidence": [reason],
        "gate_failures": [],
        "hard_gates": {"three_two_one_ladder": None, "constituent_count_gt_100": None},
        "close_confirmation": {
            "status": "NOT_EVALUATED",
            "quality_signals": {},
            "quality_signal_count": 0,
            "failures": [reason],
            "thresholds": CLOSE_CONFIRMATION_THRESHOLDS,
        },
        "classification_basis": "required_evidence_missing_zero_without_renormalization_then_close_confirmation",
    }


def unavailable_stock_fit(code: str, reason: str) -> dict[str, Any]:
    return {
        "code": normalize_code(code),
        "theme": "",
        "status": "DEGRADED",
        "score": 0.0,
        "stars": 0.0,
        "decision_eligible": False,
        "evidence": [],
        "missing_evidence": [reason],
    }


def _missing_board_evidence(board: dict[str, Any]) -> list[str]:
    missing = [
        name
        for name in REQUIRED_BOARD_FIELDS + CLOSE_CONFIRMATION_FIELDS
        if name not in board or board.get(name) is None
    ]
    if board.get("catalyst_verified") is not True:
        missing.append("verified_catalyst")
    if _int(board.get("catalyst_source_count")) <= 0:
        missing.append("catalyst_source")
    return list(dict.fromkeys(missing))


def score_board(board: dict[str, Any]) -> dict[str, Any]:
    rank = _int(board.get("rank"), 9999)
    sector_return = _float(board.get("sector_return_pct"))
    limit_up_count = _int(board.get("limit_up_count"))
    market_limit_up_count = _int(board.get("market_limit_up_count"))
    limit_up_ratio = limit_up_count / market_limit_up_count * 100 if market_limit_up_count > 0 else 0.0

    market_score = _points(float(-rank), [(-1, 8), (-3, 6), (-5, 4), (-10, 2)])
    market_score += _points(sector_return, [(3.0, 7), (2.0, 5), (1.0, 3), (0.01, 1)])
    breadth_score = _points(limit_up_count, [(16, 9), (9, 7), (5, 5), (2, 2), (1, 1)])
    breadth_score += _points(limit_up_ratio, [(15, 6), (8, 5), (4, 3), (0.01, 1)])
    hierarchy_score = (
        (4 if _int(board.get("leader_count")) >= 1 else 0)
        + (3 if _int(board.get("mid_tier_count")) >= 2 else 2 if _int(board.get("mid_tier_count")) == 1 else 0)
        + (2 if _int(board.get("first_board_count")) >= 5 else 1 if _int(board.get("first_board_count")) >= 2 else 0)
        + (1 if _int(board.get("capacity_count")) >= 1 else 0)
    )
    three_board_count = _int(board.get("three_board_count"))
    two_board_count = _int(board.get("two_board_count"))
    one_board_count = _int(board.get("one_board_count"))
    constituent_count = _int(board.get("constituent_count"))
    ladder_score = (
        (4 if three_board_count >= 1 else 0)
        + (3 if two_board_count >= 1 else 0)
        + (3 if one_board_count >= 1 else 0)
    )
    constituent_score = _points(constituent_count, [(501, 10), (301, 8), (201, 6), (101, 4)])
    capital_score = _points(_float(board.get("capital_concentration_pct")), [(15, 8), (8, 6), (4, 3), (0.01, 1)])
    capital_score += _points(_float(board.get("turnover_expansion_ratio")), [(1.5, 7), (1.2, 5), (1.0, 3), (0.8, 1)])
    catalyst_level = str(board.get("catalyst_level", "")).lower()
    catalyst_score = {"policy": 8, "industry": 6, "company": 4}.get(catalyst_level, 0)
    if board.get("catalyst_verified") is True and _int(board.get("catalyst_source_count")) >= 2:
        catalyst_score = min(10, catalyst_score + 2)
    elif board.get("catalyst_verified") is not True:
        catalyst_score = 0
    continuity_score = _points(_int(board.get("continuity_days")), [(3, 6), (2, 4), (1, 2)])
    continuity_score += 2 if board.get("divergence_repaired") is True else 0
    continuity_score += 2 if board.get("reflow_confirmed") is True else 0
    gap = _float(board.get("runner_up_gap_pct"))
    if rank == 1:
        dominance_score = _points(gap, [(1.5, 5), (0.8, 4), (0.3, 3), (0.01, 2)])
    elif rank <= 3:
        dominance_score = 2 if gap > 0 else 1
    else:
        dominance_score = 0

    components = {
        "market_strength": {"score": min(15.0, market_score), "weight": 15, "evidence": [f"rank={rank}", f"return={sector_return:.2f}%"]},
        "breadth": {"score": min(15.0, breadth_score), "weight": 15, "evidence": [f"limit_up={limit_up_count}", f"market_share={limit_up_ratio:.2f}%"]},
        "hierarchy": {"score": min(10.0, float(hierarchy_score)), "weight": 10, "evidence": [f"leader={_int(board.get('leader_count'))}", f"mid={_int(board.get('mid_tier_count'))}", f"first={_int(board.get('first_board_count'))}", f"capacity={_int(board.get('capacity_count'))}"]},
        "ladder_completeness": {"score": min(10.0, float(ladder_score)), "weight": 10, "evidence": [f"three_board={three_board_count}", f"two_board={two_board_count}", f"one_board={one_board_count}"]},
        "constituent_scale": {"score": min(10.0, constituent_score), "weight": 10, "evidence": [f"constituent_count={constituent_count}"]},
        "capital": {"score": min(15.0, capital_score), "weight": 15, "evidence": [f"concentration={_float(board.get('capital_concentration_pct')):.2f}%", f"turnover_expansion={_float(board.get('turnover_expansion_ratio')):.2f}x"]},
        "catalyst": {"score": min(10.0, float(catalyst_score)), "weight": 10, "evidence": [f"verified={board.get('catalyst_verified') is True}", f"level={catalyst_level or 'missing'}", f"sources={_int(board.get('catalyst_source_count'))}"]},
        "continuity": {"score": min(10.0, float(continuity_score)), "weight": 10, "evidence": [f"days={_int(board.get('continuity_days'))}", f"divergence_repaired={board.get('divergence_repaired') is True}", f"reflow={board.get('reflow_confirmed') is True}"]},
        "dominance": {"score": min(5.0, float(dominance_score)), "weight": 5, "evidence": [f"runner_up_gap={gap:.2f}%"]},
    }
    raw_score = round(sum(item["score"] for item in components.values()), 2)
    missing = _missing_board_evidence(board)
    ladder_gate = three_board_count >= 1 and two_board_count >= 1 and one_board_count >= 1
    constituent_gate = constituent_count > 100
    gate_failures: list[str] = []
    if not missing:
        if not ladder_gate:
            gate_failures.append("three_two_one_ladder_incomplete")
        if not constituent_gate:
            gate_failures.append("constituent_count_not_greater_than_100")
    quality_signals = {
        "early_seal_not_weaker_than_market": _float(board.get("early_seal_ratio")) >= _float(board.get("market_early_seal_ratio")),
        "zero_open_not_weaker_than_market": _float(board.get("zero_open_ratio")) >= _float(board.get("market_zero_open_ratio")),
        "late_reseal_not_worse_than_market": _float(board.get("late_reseal_ratio")) <= _float(board.get("market_late_reseal_ratio")),
        "seal_fund_turnover_not_weaker_than_market": _float(board.get("seal_fund_turnover_ratio")) >= _float(board.get("market_seal_fund_turnover_ratio")),
    }
    quality_signal_count = sum(value is True for value in quality_signals.values())
    close_failures: list[str] = []
    if not missing and not gate_failures:
        if raw_score < CLOSE_CONFIRMATION_THRESHOLDS["raw_score_min"]:
            close_failures.append("raw_score_below_60")
        if rank > CLOSE_CONFIRMATION_THRESHOLDS["rank_max"]:
            close_failures.append("plate_rank_below_top_5")
        if limit_up_ratio < CLOSE_CONFIRMATION_THRESHOLDS["limit_up_market_share_min_pct"]:
            close_failures.append("limit_up_market_share_below_8_pct")
        if _float(board.get("source_session_coverage")) < CLOSE_CONFIRMATION_THRESHOLDS["source_session_coverage_min"]:
            close_failures.append("source_session_coverage_below_80_pct")
        if _int(board.get("intraday_sample_count")) < CLOSE_CONFIRMATION_THRESHOLDS["intraday_sample_count_min"]:
            close_failures.append("intraday_sample_count_below_3")
        if _float(board.get("intraday_coverage_ratio")) < CLOSE_CONFIRMATION_THRESHOLDS["intraday_coverage_ratio_min"]:
            close_failures.append("intraday_coverage_ratio_below_60_pct")
        if quality_signal_count < CLOSE_CONFIRMATION_THRESHOLDS["relative_quality_signal_count_min"]:
            close_failures.append("relative_close_quality_signals_below_2")
    if missing:
        score = 0.0
        stars = 0.0
        status = "DEGRADED"
    elif gate_failures:
        score = 0.0
        stars = 0.0
        status = "GATE_FAILED"
    elif close_failures:
        score = 0.0
        stars = 0.0
        status = "CLOSE_UNCONFIRMED"
    else:
        score = raw_score
        status = "VERIFIED"
        if rank == 1 and limit_up_count > 15 and score >= 80:
            stars = 5.0
        elif rank <= 3 and limit_up_count > 8 and score >= 60:
            stars = 4.0
        elif rank > 3 and 5 <= limit_up_count <= 10 and score >= 40:
            stars = 3.0
        elif limit_up_count >= 1 and sector_return > 0:
            stars = 2.0
        else:
            stars = 1.0
    return {
        "model_version": MODEL_VERSION,
        "raw_score_version": RAW_SCORE_VERSION,
        "name": str(board.get("name", "")),
        "normalized_name": normalize_theme(board.get("name")),
        "status": status,
        "score": score,
        "raw_score": raw_score,
        "stars": stars,
        "decision_eligible": status == "VERIFIED",
        "components": components,
        "missing_evidence": missing,
        "gate_failures": gate_failures,
        "hard_gates": {
            "three_two_one_ladder": ladder_gate if not missing else None,
            "constituent_count_gt_100": constituent_gate if not missing else None,
        },
        "close_confirmation": {
            "status": "CONFIRMED" if status == "VERIFIED" else "NOT_EVALUATED" if status in {"DEGRADED", "GATE_FAILED"} else "UNCONFIRMED",
            "quality_signals": quality_signals if not missing else {},
            "quality_signal_count": quality_signal_count if not missing else 0,
            "failures": close_failures,
            "thresholds": CLOSE_CONFIRMATION_THRESHOLDS,
            "evidence": {
                name: board.get(name)
                for name in CLOSE_CONFIRMATION_FIELDS
            },
        },
        "classification_basis": "nine_component_raw_score_then_existing_hard_gates_then_dynamic_close_confirmation",
    }


def score_stock_fit(stock: dict[str, Any], board_name: str) -> dict[str, Any]:
    theme = normalize_theme(board_name)
    current_themes = split_themes(stock.get("themes", []))
    current_theme_match = bool(theme and theme in current_themes)
    current_reason_match = theme_mentioned_in_text(theme, stock.get("reason", ""))
    historical_evidence: list[dict[str, Any]] = []
    records = stock.get("historical_theme_evidence", [])
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        record_themes = split_themes(record.get("themes", []))
        historical_theme_match = bool(theme and theme in record_themes)
        reason_themes = [item for item in record_themes if item != "其他"]
        structured_reason_match = bool(
            historical_theme_match
            and any(theme_mentioned_in_text(item, record.get("reason", "")) for item in reason_themes)
        )
        cross_source_reason_match = bool(
            current_theme_match
            and theme
            and theme_mentioned_in_text(theme, record.get("reason", ""))
        )
        historical_reason_match = structured_reason_match or cross_source_reason_match
        if historical_theme_match or historical_reason_match:
            historical_evidence.append({
                **record,
                "theme_match": historical_theme_match,
                "reason_match": historical_reason_match,
            })
    historical_theme_match = any(
        item.get("theme_match") is True for item in historical_evidence
    )
    historical_reason_match = any(
        item.get("reason_match") is True for item in historical_evidence
    )
    theme_match = current_theme_match or historical_theme_match
    reason_match = current_reason_match or historical_reason_match
    business_verified = stock.get("business_theme_verified") is True
    announcement_verified = stock.get("announcement_theme_verified") is True
    hierarchy_role = str(stock.get("hierarchy_role", "")).lower()
    hierarchy_points = {"leader": 10, "mid_tier": 8, "capacity": 8, "first_board": 5}.get(hierarchy_role, 0)
    score = (
        (30 if theme_match else 0)
        + (25 if reason_match else 0)
        + (25 if business_verified else 0)
        + (10 if announcement_verified else 0)
        + hierarchy_points
    )
    authenticity_verified = theme_match and (reason_match or business_verified or announcement_verified)
    if authenticity_verified:
        status = "VERIFIED"
        stars = 5.0 if score >= 85 else 4.0 if score >= 70 else 3.0 if score >= 55 else 2.0
        missing: list[str] = []
    else:
        status = "DEGRADED"
        score = min(score, 40)
        stars = 2.0 if score >= 25 else 1.0 if score > 0 else 0.0
        missing = ["stock_theme_authenticity"]
    return {
        "code": normalize_code(stock.get("code")),
        "theme": theme,
        "status": status,
        "score": float(score),
        "stars": stars,
        "decision_eligible": status == "VERIFIED",
        "evidence": [
            f"theme_match={theme_match}",
            f"reason_match={reason_match}",
            f"current_theme_match={current_theme_match}",
            f"current_reason_match={current_reason_match}",
            f"historical_theme_match={historical_theme_match}",
            f"historical_reason_match={historical_reason_match}",
            f"business_verified={business_verified}",
            f"announcement_verified={announcement_verified}",
            f"hierarchy_role={hierarchy_role or 'none'}",
        ],
        "historical_evidence": historical_evidence,
        "missing_evidence": missing,
    }


def combine_board_and_stock(board: dict[str, Any], stock_fit: dict[str, Any], weight: float = 14.0) -> dict[str, Any]:
    eligible = board.get("decision_eligible") is True and stock_fit.get("decision_eligible") is True
    stars = min(_float(board.get("stars")), _float(stock_fit.get("stars"))) if eligible else 0.0
    if not eligible and (board.get("status") == "DEGRADED" or stock_fit.get("status") == "DEGRADED"):
        status = "DEGRADED"
    elif not eligible and board.get("status") == "GATE_FAILED":
        status = "GATE_FAILED"
    else:
        status = "VERIFIED"
    return {
        "dimension": "板块强度与主线契合度",
        "weight": weight,
        "stars": stars,
        "weighted_score": round(stars / 5.0 * weight, 2),
        "status": status,
        "decision_eligible": eligible,
        "board": board,
        "stock_fit": stock_fit,
        "cap_rule": "zero_if_evidence_degraded_or_mainline_hard_gate_failed_else_min(board_stars, stock_authenticity_stars)",
    }


def _dataset(payload: dict[str, Any], name: str) -> tuple[dict[str, Any], bool]:
    wrapper = payload.get("datasets", {}).get(name, {}) if isinstance(payload, dict) else {}
    data = wrapper.get("data", {}) if isinstance(wrapper, dict) else {}
    return (data if isinstance(data, dict) else {}), wrapper.get("success") is True


def _lianban_theme_returns(lianban: dict[str, Any], themes: list[str]) -> dict[str, float]:
    details = lianban.get("page_details", {}) if isinstance(lianban, dict) else {}
    texts = details.get("event_texts", []) if isinstance(details, dict) else []
    joined = "\n".join(str(item) for item in texts if isinstance(item, str))
    result: dict[str, float] = {}
    for theme in themes:
        display_variants = {theme}
        if theme == "机器人":
            display_variants.add("机器人概念")
        for display in display_variants:
            matches = re.findall(rf"{re.escape(display)}\s*([+-]\d+(?:\.\d+)?)%", joined, flags=re.IGNORECASE)
            if matches:
                result[theme] = float(matches[0])
                break
    return result


def build_context(
    duanxianxia: dict[str, Any],
    lianban: dict[str, Any],
    lianban_history: list[dict[str, Any]] | None = None,
    tdx_catalog: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    plate_data, plate_ok = _dataset(duanxianxia, "platechart1")
    pool_data, pool_ok = _dataset(duanxianxia, "ztpool")
    ztplate_data, ztplate_ok = _dataset(duanxianxia, "ztplate")
    live_data, live_ok = _dataset(duanxianxia, "ztlive")
    source_status = {
        "duanxianxia_plate": "VERIFIED" if plate_ok else "DEGRADED",
        "duanxianxia_pool": "VERIFIED" if pool_ok else "DEGRADED",
        "duanxianxia_membership": "VERIFIED" if ztplate_ok and live_ok else "DEGRADED",
        "lianban": str(lianban.get("status", "DEGRADED")),
    }
    target_date = str(lianban.get("target_date", "")).strip()
    active_tdx_catalog = (
        load_runtime_tdx_constituent_catalog(target_date)
        if tdx_catalog is None
        else tdx_catalog
    )
    source_status["tdx_constituents"] = "VERIFIED" if active_tdx_catalog else "DEGRADED"
    raw_stocks: list[dict[str, Any]] = []
    for item in ztplate_data.get("list", []) if isinstance(ztplate_data.get("list"), list) else []:
        if isinstance(item, dict):
            raw_stocks.append({"code": item.get("code"), "themes": split_themes(item.get("plate")) + split_themes(item.get("concept"))})
    live_items = live_data.get("list", []) if isinstance(live_data.get("list"), list) else []
    for item in live_items:
        if isinstance(item, dict):
            raw_stocks.append({"code": item.get("code"), "name": item.get("name"), "reason": item.get("ztyy"), "themes": split_themes(item.get("ztyy")), "board_label": item.get("zt")})
    page_details = lianban.get("page_details", {}) if isinstance(lianban, dict) else {}
    lianban_stock_items = page_details.get("stock_items", []) if isinstance(page_details, dict) and isinstance(page_details.get("stock_items"), list) else []
    for item in lianban_stock_items:
        if isinstance(item, dict):
            raw_stocks.append({
                "code": item.get("code"), "name": item.get("name"), "themes": [item.get("theme"), item.get("board")],
                "reason": item.get("reason"), "board_count": item.get("board_count"), "board_label": item.get("board_label"),
            })
    pool_rows = pool_data.get("list", []) if isinstance(pool_data.get("list"), list) else []
    parsed_pool = [item for item in (parse_duanxianxia_pool_row(row) for row in pool_rows) if item]
    turnover_amounts: list[tuple[str, float]] = []
    for item in parsed_pool:
        turnover_amount = _float(item.get("turnover_amount"))
        turnover_amounts.append((item["code"], turnover_amount))
        raw_stocks.append({
            **item,
            "amount": turnover_amount,
        })
    dxx_codes = {item["code"] for item in parsed_pool}
    lianban_codes = {
        normalize_code(item.get("code"))
        for item in lianban_stock_items
        if isinstance(item, dict) and normalize_code(item.get("code"))
    }
    session_alignment = source_session_alignment(dxx_codes, lianban_codes)
    source_status["current_session_alignment"] = (
        "VERIFIED"
        if session_alignment["coverage"] is not None
        and session_alignment["coverage"] >= CLOSE_CONFIRMATION_THRESHOLDS["source_session_coverage_min"]
        else "DEGRADED"
    )
    stocks = attach_historical_stock_authenticity(
        deduplicate_stocks(raw_stocks),
        lianban_history or [],
    )
    by_code = {item["code"]: item for item in stocks}
    positive_amounts = sorted((amount for _code, amount in turnover_amounts if amount > 0), reverse=True)
    capacity_cutoff = positive_amounts[max(0, len(positive_amounts) // 5 - 1)] if positive_amounts else float("inf")
    for stock in stocks:
        label = str(stock.get("board_label", ""))
        level = exact_board_level(stock)
        stock["exact_board_level"] = level
        if level >= 3:
            stock["hierarchy_role"] = "leader"
        elif level == 2:
            stock["hierarchy_role"] = "mid_tier"
        elif level == 1 and _float(stock.get("amount")) >= capacity_cutoff:
            stock["hierarchy_role"] = "capacity"
        elif level == 1:
            stock["hierarchy_role"] = "first_board"
        else:
            stock["hierarchy_role"] = "none"
        day_amounts = _tdx_day_amounts(stock["code"], target_date)
        if day_amounts:
            stock.update(day_amounts)

    count_today = pool_data.get("count", {}).get("limit_up_count", {}).get("today", {})
    count_today = count_today if isinstance(count_today, dict) else {}
    market_count = _int(count_today.get("num"))
    if market_count <= 0:
        market_count = len(parsed_pool)
    market_close_quality = close_quality_metrics(parsed_pool, market_count)
    market_seal_rate = _ratio(count_today.get("rate"))
    if market_seal_rate is None:
        open_count = _int(count_today.get("open_num", count_today.get("open_count")))
        market_seal_rate = market_count / (market_count + open_count) if market_count + open_count > 0 else None
    plates = plate_data.get("plates", {})
    plate_rows = list(plates.values()) if isinstance(plates, dict) else plates if isinstance(plates, list) else []
    parsed_plates = [row for row in plate_rows if isinstance(row, dict) and normalize_theme(row.get("name"))]
    parsed_plates.sort(key=lambda row: _float(row.get("val")), reverse=True)
    total_pool_amount = sum(amount for _code, amount in turnover_amounts if amount > 0)
    lianban_topics = {normalize_theme(item.get("name")): _int(item.get("count")) for item in lianban.get("topics", []) if isinstance(item, dict)}
    theme_returns = _lianban_theme_returns(lianban, [normalize_theme(row.get("name")) for row in parsed_plates])
    historical_topics = [
        {normalize_theme(item.get("name")): _int(item.get("count")) for item in snapshot.get("topics", []) if isinstance(item, dict)}
        for snapshot in (lianban_history or [])
        if isinstance(snapshot, dict) and snapshot.get("status") == "CLEAN_PASS"
    ]
    source_status["lianban_history"] = "VERIFIED" if len(historical_topics) >= 2 else "DEGRADED"
    source_status["tdx_turnover"] = "VERIFIED" if any("current_day_amount" in stock for stock in stocks) else "DEGRADED"
    pending_board_inputs: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(parsed_plates, 1):
        name = normalize_theme(row.get("name"))
        members = [stock for stock in stocks if name in stock.get("themes", [])]
        constituent_match = resolve_tdx_constituent_block(
            name,
            [str(stock.get("code", "")) for stock in members],
            active_tdx_catalog,
        )
        catalyst_evidence = cross_validate_theme_catalyst(
            name,
            live_items,
            lianban_stock_items,
        )
        current_return = theme_returns.get(name)
        sector_return_evidence = None
        if current_return is None and constituent_match and constituent_match.get("index_code"):
            sector_return_evidence = read_tdx_sector_return(
                constituent_match["index_code"],
                target_date,
            )
            if sector_return_evidence:
                current_return = sector_return_evidence["return_pct"]
                theme_returns[name] = current_return
        turnover_members = [stock for stock in members if _float(stock.get("previous_day_amount")) > 0 and _float(stock.get("current_day_amount")) > 0]
        previous_turnover = sum(_float(stock.get("previous_day_amount")) for stock in turnover_members)
        current_turnover = sum(_float(stock.get("current_day_amount")) for stock in turnover_members)
        turnover_expansion = current_turnover / previous_turnover if previous_turnover > 0 else None
        board_close_quality = close_quality_metrics(
            members,
            max(_int(lianban_topics.get(name, _int(row.get("ztcount")))), len(members)),
        )
        continuity_days: int | None = None
        divergence_repaired: bool | None = None
        reflow_confirmed: bool | None = None
        if lianban.get("status") == "CLEAN_PASS" and len(historical_topics) >= 2:
            continuity_days = 1 if name in lianban_topics else 0
            if continuity_days:
                for snapshot_topics in historical_topics:
                    if name not in snapshot_topics:
                        break
                    continuity_days += 1
            current_topic_count = lianban_topics.get(name, 0)
            previous_topic_count = historical_topics[0].get(name, 0)
            prior_topic_count = historical_topics[1].get(name, 0)
            reflow_confirmed = current_topic_count > previous_topic_count
            divergence_repaired = previous_topic_count < prior_topic_count and reflow_confirmed
        board_input = {
            "name": row.get("name"),
            "rank": index,
            "sector_return_pct": current_return,
            "sector_strength_raw": _float(row.get("val")),
            "limit_up_count": lianban_topics.get(name, _int(row.get("ztcount"))),
            "market_limit_up_count": market_count,
            "leader_count": sum(stock.get("hierarchy_role") == "leader" for stock in members),
            "mid_tier_count": sum(stock.get("hierarchy_role") == "mid_tier" for stock in members),
            "first_board_count": sum(stock.get("hierarchy_role") == "first_board" for stock in members),
            "capacity_count": sum(stock.get("hierarchy_role") == "capacity" for stock in members),
            "three_board_count": sum(_int(stock.get("exact_board_level")) == 3 for stock in members),
            "two_board_count": sum(_int(stock.get("exact_board_level")) == 2 for stock in members),
            "one_board_count": sum(_int(stock.get("exact_board_level")) == 1 for stock in members),
            "constituent_count": constituent_match.get("constituent_count") if constituent_match else None,
            "constituent_source": constituent_match.get("source_name") if constituent_match else None,
            "constituent_overlap_count": constituent_match.get("overlap_count") if constituent_match else None,
            "constituent_match_type": constituent_match.get("match_type") if constituent_match else None,
            "constituent_index_code": constituent_match.get("index_code") if constituent_match else None,
            "constituent_evidence": constituent_match,
            "capital_concentration_pct": (sum(_float(stock.get("amount")) for stock in members) / total_pool_amount * 100) if total_pool_amount else None,
            "turnover_expansion_ratio": turnover_expansion,
            "turnover_evidence": [
                {
                    "code": stock["code"],
                    "previous_date": stock.get("previous_day_date"),
                    "current_date": stock.get("current_day_date"),
                    "source_path": stock.get("turnover_source_path"),
                    "source_sha256": stock.get("turnover_source_sha256"),
                }
                for stock in turnover_members
            ],
            "catalyst_verified": catalyst_evidence["verified"],
            "catalyst_level": "industry" if catalyst_evidence["verified"] else None,
            "catalyst_source_count": catalyst_evidence["source_count"],
            "catalyst_evidence": catalyst_evidence,
            "continuity_days": continuity_days,
            "divergence_repaired": divergence_repaired,
            "reflow_confirmed": reflow_confirmed,
            "runner_up_gap_pct": None,
            "sector_return_evidence": sector_return_evidence,
            "source_session_coverage": session_alignment["coverage"],
            **board_close_quality,
            "market_early_seal_ratio": market_close_quality["early_seal_ratio"],
            "market_zero_open_ratio": market_close_quality["zero_open_ratio"],
            "market_late_reseal_ratio": market_close_quality["late_reseal_ratio"],
            "market_seal_fund_turnover_ratio": market_close_quality["seal_fund_turnover_ratio"],
            "market_seal_rate": market_seal_rate,
            "close_quality_evidence": {
                "session_alignment": session_alignment,
                "board": board_close_quality,
                "market": market_close_quality,
                "time_cutoffs": {"early_seal_at_or_before": "10:30:00", "late_final_seal_at_or_after": "14:30:00"},
                "turnover_field": "duanxianxia_ztpool_row_8",
                "free_float_market_cap_field": "duanxianxia_ztpool_row_9",
            },
        }
        pending_board_inputs[name] = board_input
    return_gaps = compute_return_lead_gaps({
        name: board_input.get("sector_return_pct")
        for name, board_input in pending_board_inputs.items()
    })
    boards: dict[str, dict[str, Any]] = {}
    for name, board_input in pending_board_inputs.items():
        board_input["runner_up_gap_pct"] = return_gaps.get(name)
        boards[name] = score_board(board_input)
        boards[name]["input_evidence"] = board_input
    return {
        "model_version": MODEL_VERSION,
        "target_date": target_date,
        "status": (
            "VERIFIED"
            if boards and any(item["decision_eligible"] for item in boards.values())
            else "CLOSE_UNCONFIRMED"
            if boards and any(item.get("status") == "CLOSE_UNCONFIRMED" for item in boards.values())
            else "GATE_FAILED"
            if boards and any(item.get("status") == "GATE_FAILED" for item in boards.values())
            else "DEGRADED"
        ),
        "source_status": source_status,
        "session_alignment": session_alignment,
        "boards": boards,
        "stocks": by_code,
        "issues": [] if boards else ["no_board_market_data"],
    }


def load_context_from_environment() -> dict[str, Any]:
    dxx_path = Path(os.environ.get("CODEX_DUANXIANXIA_PATH", ""))
    lianban_path = Path(os.environ.get("CODEX_LIANBAN_SNAPSHOT", os.environ.get("CODEX_LIANBAN_PATH", "")))
    issues: list[str] = []
    try:
        dxx = json.loads(dxx_path.read_text(encoding="utf-8")) if dxx_path.is_file() else {}
    except (OSError, json.JSONDecodeError) as exc:
        dxx = {}
        issues.append(f"duanxianxia_unreadable:{type(exc).__name__}")
    try:
        lianban = json.loads(lianban_path.read_text(encoding="utf-8")) if lianban_path.is_file() else {}
    except (OSError, json.JSONDecodeError) as exc:
        lianban = {}
        issues.append(f"lianban_unreadable:{type(exc).__name__}")
    history_path = Path(os.environ.get("CODEX_LIANBAN_HISTORY_PATH", ""))
    try:
        history_payload = json.loads(history_path.read_text(encoding="utf-8")) if history_path.is_file() else {}
        lianban_history = history_payload.get("snapshots", []) if isinstance(history_payload, dict) else []
    except (OSError, json.JSONDecodeError) as exc:
        lianban_history = []
        issues.append(f"lianban_history_unreadable:{type(exc).__name__}")
    if not dxx:
        issues.append("duanxianxia_snapshot_missing")
    if not lianban:
        issues.append("lianban_snapshot_missing")
    if len(lianban_history) < 2:
        issues.append("lianban_history_insufficient")
    context = build_context(dxx, lianban, lianban_history) if dxx else {"model_version": MODEL_VERSION, "status": "DEGRADED", "source_status": {}, "boards": {}, "stocks": {}, "issues": []}
    context["issues"] = list(dict.fromkeys(context.get("issues", []) + issues))
    context["source_paths"] = {"duanxianxia": str(dxx_path) if str(dxx_path) else "", "lianban": str(lianban_path) if str(lianban_path) else "", "lianban_history": str(history_path) if str(history_path) else ""}
    return context


def score_stock_in_context(code: str, context: dict[str, Any]) -> dict[str, Any]:
    stock = context.get("stocks", {}).get(normalize_code(code))
    if not stock:
        board = unavailable_mainline("stock_board_membership_missing")
        fit = unavailable_stock_fit(code, "stock_board_membership_missing")
        return combine_board_and_stock(board, fit)
    candidates: list[dict[str, Any]] = []
    for theme in stock_theme_candidates(stock):
        board = context.get("boards", {}).get(normalize_theme(theme))
        if board:
            candidates.append(combine_board_and_stock(board, score_stock_fit(stock, theme)))
    if not candidates:
        return combine_board_and_stock(unavailable_mainline("matched_board_missing"), unavailable_stock_fit(code, "matched_board_missing"))
    return max(
        candidates,
        key=lambda item: (
            item["weighted_score"],
            item["stock_fit"].get("decision_eligible") is True,
            _float(item["stock_fit"].get("score")),
            _float(item["board"].get("raw_score")),
        ),
    )
