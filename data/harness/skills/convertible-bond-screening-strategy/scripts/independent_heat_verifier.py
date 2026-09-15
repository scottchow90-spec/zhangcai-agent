from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

"""Independent Tongdaxin industry/concept heat recomputation.

This module intentionally does not import the production scanner or tdx-local-hub.
It parses Tongdaxin ``.day`` files with the Python standard library and provides
an independent implementation of the scanner's market-heat mathematics.
"""

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import statistics
import struct
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Sequence

from runtime_utils import canonicalize_business_payload


DAY_RECORD = struct.Struct("<IIIIIfII")
TRUSTED_TDX_ROOT = Path(r"C:\new_tdx_mock")
TRUSTED_VIPDOC_ROOT = TRUSTED_TDX_ROOT / "vipdoc"
TRUSTED_HQ_CACHE = TRUSTED_TDX_ROOT / "T0002" / "hq_cache"
TRUSTED_HEAT_SOURCES = {
    "industry_membership": TRUSTED_HQ_CACHE / "tdxhy.cfg",
    "industry_names": TRUSTED_HQ_CACHE / "tdxzs3.cfg",
    "concept_membership": TRUSTED_HQ_CACHE / "infoharbor_block.dat",
}
EXPECTED_PRODUCTION_SCHEMA = "TDX-CONVERTIBLE-BOND-WEIGHTED-SCAN-V5"
EXPECTED_SOURCE_BINDING_MODE = "stable_sha256_pre_and_post_run"
DAY_INPUT_SCHEMA = "CONVERTIBLE-BOND-DAY-INPUT-MANIFEST-2"
DAY_INPUT_BINDING_MODE = "immutable_tail_snapshot_pre_and_post"
DAY_INPUT_TAIL_RECORD_LIMIT = 260
DAY_INPUT_STABLE_CAPTURE_PASSES = 2
TDX_DAY_UPDATE_RACE = "TDX_DAY_UPDATE_RACE"
INDEPENDENT_VERIFY_SCHEMA = "CONVERTIBLE-BOND-INDEPENDENT-HEAT-VERIFY-2"
EXPECTED_C9_NORMALIZATION_RULE = "30% industry percentile heat + 40% highest concept heat score + 30% underlying trend"
EXPECTED_C9_WEIGHT = 8.0
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
NON_DIRECTION_MARKERS = (
    "含B股",
    "含H股",
    "ST板块",
    "中特估",
    "融资融券",
    "转融券",
    "机构重仓",
)
EQUITY_PREFIXES = (
    "000",
    "001",
    "002",
    "003",
    "300",
    "301",
    "600",
    "601",
    "603",
    "605",
    "688",
    "689",
    "830",
    "831",
    "832",
    "834",
    "835",
    "836",
    "837",
    "838",
    "839",
    "870",
    "871",
    "872",
    "873",
    "874",
    "875",
    "876",
    "877",
    "878",
    "879",
    "880",
    "881",
    "882",
    "883",
    "884",
    "885",
    "886",
    "887",
    "888",
    "889",
    "890",
    "891",
    "892",
    "893",
    "894",
    "895",
    "896",
    "897",
    "898",
    "899",
)
INDUSTRY_FIELDS = (
    "median_return_5d",
    "up_ratio_5d",
    "median_amount_active_ratio_5d",
    "above_ma5_ratio",
)
INDUSTRY_WEIGHTS = {
    "median_return_5d": 0.35,
    "up_ratio_5d": 0.25,
    "median_amount_active_ratio_5d": 0.20,
    "above_ma5_ratio": 0.20,
}
CONCEPT_SCORE_FIELDS = (
    "mean_return_1d",
    "median_return_1d",
    "mean_return_5d",
    "median_return_5d",
    "up_ratio",
    "up_ratio_5d",
    "limit_up_ratio",
    "median_volume_ratio_5d",
    "median_amount_ratio_5d",
)


class DayInputUpdateRace(RuntimeError):
    def __init__(
        self,
        reason: str,
        *,
        mismatch_paths: Sequence[str | Path] | None = None,
        run_id: str | None = None,
    ) -> None:
        paths = [str(value) for value in (mismatch_paths or ["<day-input-manifest>"])]
        self.mismatch_paths = sorted(set(paths), key=str.casefold)
        self.run_id = run_id
        self.reason = reason
        super().__init__(
            f"{TDX_DAY_UPDATE_RACE}:day_input_manifest_changed:count={len(self.mismatch_paths)}"
        )


class FrozenDayInputSnapshot:
    def __init__(
        self,
        *,
        manifest_path: Path,
        manifest_raw: bytes,
        manifest_stat: tuple[int, int],
        manifest_binding: dict[str, Any],
        manifest: dict[str, Any],
        nodes: list[dict[str, Any]],
        raw_by_alias: dict[str, bytes | None],
        path_by_alias: dict[str, str],
    ) -> None:
        self.manifest_path = manifest_path
        self.manifest_raw = manifest_raw
        self.manifest_stat = manifest_stat
        self.manifest_binding = dict(manifest_binding)
        self.manifest = manifest
        self.nodes = nodes
        self.raw_by_alias = dict(raw_by_alias)
        self.path_by_alias = dict(path_by_alias)
        code_aliases: dict[str, list[str]] = defaultdict(list)
        for alias in self.raw_by_alias:
            code_aliases[alias[:6]].append(alias)
        self.code_aliases = {
            code: aliases[0]
            for code, aliases in code_aliases.items()
            if len(aliases) == 1
        }

    def read_rows(self, symbol: str, limit: int) -> list[dict[str, Any]]:
        if not _is_plain_int(limit) or not 1 <= limit <= DAY_INPUT_TAIL_RECORD_LIMIT:
            raise ValueError(f"invalid frozen day limit: {limit}")
        raw_symbol = str(symbol).strip().upper()
        alias = raw_symbol if raw_symbol in self.raw_by_alias else None
        if alias is None:
            match = re.fullmatch(r"(\d{6})(?:\.(SH|SZ|BJ))?", raw_symbol)
            if match:
                alias = (
                    f"{match.group(1)}.{match.group(2)}"
                    if match.group(2)
                    else self.code_aliases.get(match.group(1))
                )
        if alias is None or alias not in self.raw_by_alias:
            raise ValueError(f"day symbol was not captured in bound manifest: {symbol}")
        raw = self.raw_by_alias[alias]
        if raw is None:
            return []
        return _parse_day_records_bytes(raw, self.path_by_alias[alias], limit)


def _normalize_calendar(cutoff: str, benchmark_calendar: Sequence[str]) -> tuple[str, list[str]]:
    cutoff_value = str(cutoff).replace("-", "").strip()
    calendar = [str(value).replace("-", "").strip() for value in benchmark_calendar]
    if not re.fullmatch(r"20\d{6}", cutoff_value):
        raise ValueError(f"invalid cutoff: {cutoff}")
    if (
        len(calendar) != 11
        or len(set(calendar)) != 11
        or calendar != sorted(calendar)
        or calendar[-1] != cutoff_value
        or any(not re.fullmatch(r"20\d{6}", value) for value in calendar)
    ):
        raise ValueError(f"benchmark_calendar must be 11 ordered sessions ending at {cutoff_value}")
    return cutoff_value, calendar


def _stock_market(code: str) -> str:
    if code.startswith(("5", "6", "9")):
        return "sh"
    if code.startswith(("4", "8")):
        return "bj"
    return "sz"


def _symbol_suffix(code: str) -> str:
    return f"{code}.{_stock_market(code).upper()}"


def _is_plain_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _path_key(value: str | Path) -> str:
    try:
        return str(Path(value).resolve()).casefold()
    except (OSError, RuntimeError, TypeError, ValueError):
        return ""


def _manifest_alias_parts(alias: Any) -> tuple[str, str, str]:
    if not isinstance(alias, str):
        raise ValueError(f"invalid day-input alias type: {type(alias).__name__}")
    match = re.fullmatch(r"(\d{6})(?:\.(SH|SZ|BJ))?", alias)
    if match is None:
        raise ValueError(f"invalid day-input alias: {alias}")
    code, market = match.groups()
    resolved_market = market.lower() if market else _stock_market(code)
    return code, resolved_market, alias


def _trusted_day_candidates(alias: str) -> tuple[Path, Path, Path]:
    code, market, _canonical = _manifest_alias_parts(alias)
    filename = f"{market}{code}.day"
    return (
        (TRUSTED_VIPDOC_ROOT / market / "lday" / filename).resolve(),
        (TRUSTED_VIPDOC_ROOT / "xinzeng" / market / "lday" / filename).resolve(),
        (TRUSTED_VIPDOC_ROOT / "xinzeng" / filename).resolve(),
    )


def _trusted_day_path(alias: str) -> Path:
    candidates = _trusted_day_candidates(alias)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _stable_read_bytes(
    path: Path,
    *,
    offset: int = 0,
    size: int | None = None,
    run_id: str | None = None,
) -> tuple[bytes, tuple[int, int]]:
    try:
        before = path.stat()
        with path.open("rb") as handle:
            handle.seek(offset)
            raw = handle.read() if size is None else handle.read(size)
        after = path.stat()
    except OSError as exc:
        raise DayInputUpdateRace(
            "stable_read_error",
            mismatch_paths=[path],
            run_id=run_id,
        ) from exc
    expected_size = before.st_size - offset if size is None else size
    if (
        (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)
        or len(raw) != expected_size
    ):
        raise DayInputUpdateRace(
            "file_changed_while_reading",
            mismatch_paths=[path],
            run_id=run_id,
        )
    return raw, (after.st_size, after.st_mtime_ns)


def _day_path(tdx_root: Path, code: str) -> Path:
    market = _stock_market(code)
    filename = f"{market}{code}.day"
    candidates = (
        tdx_root / "vipdoc" / market / "lday" / filename,
        tdx_root / "vipdoc" / "xinzeng" / market / "lday" / filename,
        tdx_root / "vipdoc" / "xinzeng" / filename,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _parse_day_records_bytes(
    raw: bytes,
    source: str | Path,
    limit: int = 20,
) -> list[dict[str, Any]]:
    size = len(raw)
    if size < DAY_RECORD.size or size % DAY_RECORD.size:
        raise ValueError(f"invalid .day layout: {source} size={size}")
    record_count = size // DAY_RECORD.size
    read_count = min(record_count, limit) if limit > 0 else record_count
    selected = raw[(record_count - read_count) * DAY_RECORD.size :]
    rows: list[dict[str, Any]] = []
    previous_date: str | None = None
    for offset in range(0, len(selected), DAY_RECORD.size):
        chunk = selected[offset : offset + DAY_RECORD.size]
        if len(chunk) != DAY_RECORD.size:
            raise ValueError(f"short .day read: {source}")
        date_i, _open_i, _high_i, _low_i, close_i, amount, volume, _unused = DAY_RECORD.unpack(chunk)
        date_value = str(date_i)
        try:
            dt.datetime.strptime(date_value, "%Y%m%d")
        except ValueError as exc:
            raise ValueError(f"invalid .day date: {source} value={date_value}") from exc
        if previous_date is not None and date_value <= previous_date:
            raise ValueError(f"non-increasing .day dates: {source}")
        if close_i <= 0 or not math.isfinite(float(amount)) or float(amount) < 0.0:
            raise ValueError(f"invalid .day numeric value: {source} date={date_value}")
        previous_date = date_value
        rows.append(
            {
                "date": date_value,
                "close": close_i / 100.0,
                "amount": float(amount),
                "volume": int(volume),
            }
        )
    return rows


def _read_day_records(tdx_root: Path, code: str, limit: int = 20) -> list[dict[str, Any]]:
    path = _day_path(tdx_root, code)
    if not path.is_file():
        return []
    size = path.stat().st_size
    if size < DAY_RECORD.size or size % DAY_RECORD.size:
        raise ValueError(f"invalid .day layout: {path} size={size}")
    record_count = size // DAY_RECORD.size
    read_count = min(record_count, limit) if limit > 0 else record_count
    with path.open("rb") as handle:
        handle.seek((record_count - read_count) * DAY_RECORD.size)
        raw = handle.read(read_count * DAY_RECORD.size)
    if len(raw) != read_count * DAY_RECORD.size:
        raise ValueError(f"short .day read: {path}")
    return _parse_day_records_bytes(raw, path, 0)


def _read_strict_text(path: Path, encoding: str) -> str:
    try:
        return path.read_bytes().decode(encoding, errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"strict decode failed: {path} encoding={encoding}") from exc


def _percentile_map(values: dict[str, float]) -> dict[str, float]:
    groups: dict[float, list[str]] = defaultdict(list)
    for key, value in values.items():
        groups[value].append(key)
    total = len(values)
    result: dict[str, float] = {}
    position = 0
    for value in sorted(groups):
        keys = groups[value]
        low = position
        high = position + len(keys) - 1
        percentile = 1.0 if total == 1 else ((low + high) / 2.0) / (total - 1)
        for key in keys:
            result[key] = percentile
        position += len(keys)
    return result


def _parse_industry_membership(path: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    stock_industry: dict[str, str] = {}
    members: dict[str, list[str]] = defaultdict(list)
    for line in _read_strict_text(path, "gb18030").splitlines():
        fields = line.split("|")
        if len(fields) < 3 or not re.fullmatch(r"[012]\|?", fields[0]) or not re.fullmatch(r"\d{6}", fields[1]):
            continue
        industry_code = fields[2].strip()
        if not industry_code.startswith("T"):
            continue
        key = fields[0] + fields[1]
        stock_industry[key] = industry_code
        members[industry_code].append(fields[1])
    return stock_industry, members


def _parse_industry_names(path: Path) -> dict[str, str]:
    names: dict[str, str] = {}
    for line in _read_strict_text(path, "gb18030").splitlines():
        fields = line.split("|")
        if len(fields) >= 6 and fields[-1].startswith("T"):
            names[fields[-1].strip()] = fields[0].strip()
    return names


def _parse_concepts(path: Path) -> list[dict[str, Any]]:
    text = _read_strict_text(path, "gb18030")
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


def recompute_heat(
    tdx_root: str | Path,
    tdxhy_cfg: str | Path,
    tdxzs3_cfg: str | Path,
    infoharbor_block_dat: str | Path,
    cutoff: str,
    benchmark_calendar: Sequence[str],
    day_reader: Callable[[str, int], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Recompute industry/concept heat independently from local TDX files.

    Returns a dictionary with exactly four public result surfaces:
    ``stock_industry``, ``industry_heat``, ``concept_by_code`` and
    ``attempted_lookup_symbols``.  Seven-character Tongdaxin membership keys
    are retained for the first three mappings; attempted symbols use the
    explicit ``NNNNNN.MARKET`` form.
    """

    root = Path(tdx_root).resolve()
    industry_path = Path(tdxhy_cfg).resolve()
    industry_names_path = Path(tdxzs3_cfg).resolve()
    concept_path = Path(infoharbor_block_dat).resolve()
    for required in (industry_path, industry_names_path, concept_path):
        if not required.is_file():
            raise FileNotFoundError(required)
    cutoff_value, calendar = _normalize_calendar(cutoff, benchmark_calendar)
    read_day_rows = day_reader or (lambda code, limit: _read_day_records(root, code, limit))

    cache: dict[str, dict[str, Any] | None] = {}
    attempted_codes: set[str] = set()

    def stock_snapshot(code: str) -> dict[str, Any] | None:
        if code in cache:
            return cache[code]
        attempted_codes.add(code)
        rows = [row for row in read_day_rows(code, 20) if row["date"] <= cutoff_value]
        if (
            len(rows) < 11
            or [str(row["date"]) for row in rows[-11:]] != calendar
            or float(rows[-6]["close"]) <= 0
            or float(rows[-2]["close"]) <= 0
        ):
            cache[code] = None
            return None
        previous_volumes = [float(row["volume"]) for row in rows[-6:-1] if float(row["volume"]) > 0]
        previous_amounts = [float(row["amount"]) for row in rows[-6:-1] if float(row["amount"]) > 0]
        if not previous_volumes or not previous_amounts:
            cache[code] = None
            return None
        latest = rows[-1]
        close = float(latest["close"])
        return_1d = close / float(rows[-2]["close"]) - 1.0
        return_5d = close / float(rows[-6]["close"]) - 1.0
        threshold = 0.295 if code.startswith(("4", "8")) else 0.195 if code.startswith(("300", "301", "688")) else 0.095
        sum_amount_last5 = sum(float(row["amount"]) for row in rows[-5:])
        sum_amount_prev5 = sum(float(row["amount"]) for row in rows[-10:-5])
        snapshot = {
            "date": str(latest["date"]),
            "return_1d": return_1d,
            "return_5d": return_5d,
            "is_up_1d": return_1d > 0,
            "is_up_5d": return_5d > 0,
            "is_limit_up": return_1d >= threshold,
            "volume_ratio_5d": float(latest["volume"]) / statistics.fmean(previous_volumes),
            "amount_ratio_5d": float(latest["amount"]) / statistics.fmean(previous_amounts),
            "sum_amount_last5": sum_amount_last5,
            "sum_amount_prev5": sum_amount_prev5,
            "amount_active_ratio_5d": sum_amount_last5 / sum_amount_prev5 if sum_amount_prev5 > 0 else 0.0,
            "above_ma5": close > statistics.fmean(float(row["close"]) for row in rows[-5:]),
        }
        cache[code] = snapshot
        return snapshot

    stock_industry, industry_members = _parse_industry_membership(industry_path)
    industry_names = _parse_industry_names(industry_names_path)
    industry_heat: dict[str, dict[str, Any]] = {}
    for industry_code, codes in industry_members.items():
        snapshots = [item for code in codes if (item := stock_snapshot(code)) and item["date"] == cutoff_value]
        coverage_ratio = len(snapshots) / len(codes) if codes else 0.0
        if len(snapshots) < 10 or coverage_ratio < 0.70:
            continue
        industry_heat[industry_code] = {
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
    for field in INDUSTRY_FIELDS:
        percentiles = _percentile_map({key: float(value[field]) for key, value in industry_heat.items()})
        for key, value in industry_heat.items():
            value.setdefault("percentiles", {})[field] = percentiles[key]
    for value in industry_heat.values():
        value["heat_score"] = 100.0 * sum(
            INDUSTRY_WEIGHTS[field] * float(value["percentiles"][field]) for field in INDUSTRY_FIELDS
        )

    sectors: list[dict[str, Any]] = []
    for concept in _parse_concepts(concept_path):
        snapshots = [
            item
            for member in concept["codes"]
            if (item := stock_snapshot(member[1:])) and item["date"] == cutoff_value
        ]
        coverage_count = len(snapshots)
        if coverage_count < 3 or coverage_count / len(concept["codes"]) < 0.50:
            continue
        sectors.append(
            {
                **concept,
                "member_count": len(concept["codes"]),
                "coverage_count": coverage_count,
                "mean_return_1d": statistics.fmean(float(item["return_1d"]) for item in snapshots),
                "median_return_1d": statistics.median(float(item["return_1d"]) for item in snapshots),
                "mean_return_5d": statistics.fmean(float(item["return_5d"]) for item in snapshots),
                "median_return_5d": statistics.median(float(item["return_5d"]) for item in snapshots),
                "up_ratio": sum(bool(item["is_up_1d"]) for item in snapshots) / coverage_count,
                "up_ratio_5d": sum(bool(item["is_up_5d"]) for item in snapshots) / coverage_count,
                "limit_up_ratio": sum(bool(item["is_limit_up"]) for item in snapshots) / coverage_count,
                "median_volume_ratio_5d": statistics.median(float(item["volume_ratio_5d"]) for item in snapshots),
                "median_amount_ratio_5d": statistics.median(float(item["amount_ratio_5d"]) for item in snapshots),
            }
        )
    for field in CONCEPT_SCORE_FIELDS:
        percentiles = _percentile_map({item["source_name"]: float(item[field]) for item in sectors})
        for item in sectors:
            item.setdefault("percentiles", {})[field] = percentiles[item["source_name"]]

    concept_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in sectors:
        item["heat_score"] = 100.0 * statistics.fmean(item["percentiles"].values())
        if any(marker in item["name"] for marker in NON_DIRECTION_MARKERS):
            continue
        compact = {
            key: item[key]
            for key in (
                "name",
                "source_name",
                "member_count",
                "coverage_count",
                "heat_score",
                "mean_return_1d",
                "mean_return_5d",
                "median_return_5d",
                "up_ratio",
                "up_ratio_5d",
                "limit_up_ratio",
            )
        }
        for member in item["codes"]:
            concept_by_code[member].append(compact)
    for values in concept_by_code.values():
        values.sort(key=lambda item: (-float(item["heat_score"]), item["name"]))

    return {
        "stock_industry": stock_industry,
        "industry_heat": industry_heat,
        "concept_by_code": dict(concept_by_code),
        "attempted_lookup_symbols": sorted(_symbol_suffix(code) for code in attempted_codes),
    }


def _code7(code: str) -> str:
    flag = "1" if code.startswith(("5", "6", "9")) else "2" if code.startswith(("4", "8")) else "0"
    return flag + code


def _equivalent(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=1e-12, abs_tol=1e-12)
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(_equivalent(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_equivalent(a, b) for a, b in zip(left, right))
    return left == right


def _same_path(left: str | Path, right: str | Path) -> bool:
    try:
        return str(Path(left).resolve()).casefold() == str(Path(right).resolve()).casefold()
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_node_matches(node: Any, trusted_path: Path) -> bool:
    if not isinstance(node, dict) or not trusted_path.is_file():
        return False
    try:
        return bool(
            _same_path(node.get("path", ""), trusted_path)
            and int(node.get("size", -1)) == trusted_path.stat().st_size
            and str(node.get("sha256") or "").lower() == _sha256(trusted_path)
        )
    except (OSError, TypeError, ValueError):
        return False


def _day_manifest_binding_contract(binding: Any) -> bool:
    if not isinstance(binding, dict):
        return False
    path_text = binding.get("path")
    digest = binding.get("sha256")
    return bool(
        isinstance(path_text, str)
        and path_text
        and Path(path_text).is_absolute()
        and Path(path_text).suffix.casefold() == ".json"
        and _is_plain_int(binding.get("size"))
        and binding["size"] > 0
        and _is_plain_int(binding.get("mtime_ns"))
        and binding["mtime_ns"] >= 0
        and isinstance(digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
    )


def _decode_day_manifest(raw: bytes, path: Path) -> dict[str, Any]:
    try:
        decoded = raw.decode("utf-8", errors="strict")
        manifest = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid bound day-input manifest JSON: {path}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("bound day-input manifest must be an object")
    return manifest


def _validate_day_manifest_contract(
    manifest: dict[str, Any],
    *,
    run_id: str,
    cutoff: str,
) -> list[tuple[dict[str, Any], Path, list[str]]]:
    inputs = manifest.get("inputs")
    top_level_valid = bool(
        manifest.get("schema") == DAY_INPUT_SCHEMA
        and manifest.get("binding_mode") == DAY_INPUT_BINDING_MODE
        and manifest.get("run_id") == run_id
        and manifest.get("cutoff_trade_date") == cutoff
        and manifest.get("tail_record_limit") == DAY_INPUT_TAIL_RECORD_LIMIT
        and manifest.get("stable_capture_passes") == DAY_INPUT_STABLE_CAPTURE_PASSES
        and _is_plain_int(manifest.get("capture_attempt"))
        and manifest["capture_attempt"] >= 1
        and isinstance(inputs, list)
        and bool(inputs)
        and manifest.get("all_requested_symbols_mapped") is True
        and manifest.get("all_existing_layouts_valid") is True
        and manifest.get("missing_inputs_explicit") is True
        and manifest.get("complete") is True
    )
    if not top_level_valid:
        raise ValueError("day-input manifest V2 top-level contract mismatch")

    normalized: list[tuple[dict[str, Any], Path, list[str]]] = []
    seen_paths: set[str] = set()
    seen_aliases: set[str] = set()
    existing_count = 0
    missing_count = 0
    for index, raw_node in enumerate(inputs):
        if not isinstance(raw_node, dict):
            raise ValueError(f"day-input manifest node {index} must be an object")
        aliases_raw = raw_node.get("lookup_symbols")
        if not (
            isinstance(aliases_raw, list)
            and bool(aliases_raw)
            and all(isinstance(alias, str) and bool(alias) for alias in aliases_raw)
            and aliases_raw == sorted(set(aliases_raw))
        ):
            raise ValueError(f"day-input manifest node {index} has invalid aliases")
        aliases = list(aliases_raw)
        for alias in aliases:
            _manifest_alias_parts(alias)
            if alias in seen_aliases:
                raise ValueError(f"duplicate day-input alias: {alias}")
            seen_aliases.add(alias)

        path_text = raw_node.get("path")
        if not isinstance(path_text, str) or not path_text or not Path(path_text).is_absolute():
            raise ValueError(f"day-input manifest node {index} has invalid path")
        path = Path(path_text).resolve()
        path_key = _path_key(path)
        if not path_key or path.suffix.casefold() != ".day" or path_key in seen_paths:
            raise ValueError(f"day-input manifest node {index} violates path contract")
        seen_paths.add(path_key)
        for alias in aliases:
            candidate_keys = {_path_key(candidate) for candidate in _trusted_day_candidates(alias)}
            if path_key not in candidate_keys:
                raise ValueError(f"untrusted day-input route for {alias}: {path}")

        exists = raw_node.get("exists")
        valid_layout = raw_node.get("valid_layout")
        if not isinstance(exists, bool) or not isinstance(valid_layout, bool):
            raise ValueError(f"day-input manifest node {index} has invalid state flags")
        if exists:
            existing_count += 1
            file_size = raw_node.get("file_size")
            mtime_ns = raw_node.get("mtime_ns")
            tail_count = raw_node.get("tail_record_count")
            tail_offset = raw_node.get("tail_offset")
            tail_size = raw_node.get("tail_size")
            tail_hash = raw_node.get("tail_sha256")
            expected_tail_count = (
                min(file_size // DAY_RECORD.size, DAY_INPUT_TAIL_RECORD_LIMIT)
                if _is_plain_int(file_size)
                and file_size > 0
                and file_size % DAY_RECORD.size == 0
                else -1
            )
            if not (
                valid_layout is True
                and expected_tail_count > 0
                and _is_plain_int(mtime_ns)
                and mtime_ns >= 0
                and _is_plain_int(tail_count)
                and tail_count == expected_tail_count
                and _is_plain_int(tail_size)
                and tail_size == tail_count * DAY_RECORD.size
                and _is_plain_int(tail_offset)
                and tail_offset == file_size - tail_size
                and isinstance(tail_hash, str)
                and re.fullmatch(r"[0-9a-f]{64}", tail_hash) is not None
            ):
                raise ValueError(f"day-input manifest node {index} has invalid V2 metadata")
        else:
            missing_count += 1
            if valid_layout is not False:
                raise ValueError(f"day-input manifest node {index} has invalid missing state")
        normalized.append((raw_node, path, aliases))

    count_contract = all(
        _is_plain_int(manifest.get(field)) and manifest[field] == expected
        for field, expected in (
            ("input_count", len(normalized)),
            ("alias_count", len(seen_aliases)),
            ("existing_input_count", existing_count),
            ("missing_input_count", missing_count),
        )
    )
    if not count_contract or existing_count + missing_count != len(normalized):
        raise ValueError("day-input manifest derived count contract mismatch")
    return normalized


def _load_bound_day_input_snapshot(production: dict[str, Any]) -> FrozenDayInputSnapshot:
    binding = production.get("day_input_manifest")
    if not _day_manifest_binding_contract(binding):
        raise ValueError("production day-input manifest binding contract mismatch")
    assert isinstance(binding, dict)
    run_id = str(production.get("run_id") or "")
    cutoff = str(production.get("cutoff_trade_date") or "")
    manifest_path = Path(str(binding["path"])).resolve()
    if not manifest_path.is_file():
        raise ValueError(f"bound day-input manifest is missing: {manifest_path}")
    manifest_raw, manifest_stat = _stable_read_bytes(manifest_path, run_id=run_id)
    if not (
        manifest_stat == (binding["size"], binding["mtime_ns"])
        and hashlib.sha256(manifest_raw).hexdigest() == binding["sha256"]
    ):
        raise ValueError("production day-input manifest binding is not current")
    manifest = _decode_day_manifest(manifest_raw, manifest_path)
    nodes = _validate_day_manifest_contract(manifest, run_id=run_id, cutoff=cutoff)

    raw_by_alias: dict[str, bytes | None] = {}
    path_by_alias: dict[str, str] = {}
    race_paths: list[Path] = []
    for node, path, aliases in nodes:
        if any(_path_key(_trusted_day_path(alias)) != _path_key(path) for alias in aliases):
            race_paths.append(path)
            continue
        if node["exists"] is False:
            if path.is_file():
                race_paths.append(path)
                continue
            raw: bytes | None = None
        else:
            try:
                raw, stat = _stable_read_bytes(
                    path,
                    offset=node["tail_offset"],
                    size=node["tail_size"],
                    run_id=run_id,
                )
            except DayInputUpdateRace as exc:
                race_paths.extend(Path(value) for value in exc.mismatch_paths)
                continue
            if not (
                stat == (node["file_size"], node["mtime_ns"])
                and len(raw) == node["tail_size"]
                and hashlib.sha256(raw).hexdigest() == node["tail_sha256"]
            ):
                race_paths.append(path)
                continue
        for alias in aliases:
            raw_by_alias[alias] = raw
            path_by_alias[alias] = str(path)
    if race_paths:
        raise DayInputUpdateRace(
            "bound_day_inputs_not_current",
            mismatch_paths=race_paths,
            run_id=run_id,
        )
    return FrozenDayInputSnapshot(
        manifest_path=manifest_path,
        manifest_raw=manifest_raw,
        manifest_stat=manifest_stat,
        manifest_binding=binding,
        manifest=manifest,
        nodes=[node for node, _path, _aliases in nodes],
        raw_by_alias=raw_by_alias,
        path_by_alias=path_by_alias,
    )


def _assert_day_input_snapshot_current(snapshot: FrozenDayInputSnapshot) -> None:
    run_id = str(snapshot.manifest.get("run_id") or "")
    race_paths: list[Path] = []
    try:
        manifest_raw, manifest_stat = _stable_read_bytes(snapshot.manifest_path, run_id=run_id)
    except DayInputUpdateRace as exc:
        race_paths.extend(Path(value) for value in exc.mismatch_paths)
    else:
        binding = snapshot.manifest_binding
        if not (
            manifest_raw == snapshot.manifest_raw
            and manifest_stat == snapshot.manifest_stat
            and manifest_stat == (binding["size"], binding["mtime_ns"])
            and hashlib.sha256(manifest_raw).hexdigest() == binding["sha256"]
        ):
            race_paths.append(snapshot.manifest_path)

    for node in snapshot.nodes:
        path = Path(str(node["path"])).resolve()
        aliases = list(node["lookup_symbols"])
        if any(_path_key(_trusted_day_path(alias)) != _path_key(path) for alias in aliases):
            race_paths.append(path)
            continue
        if node["exists"] is False:
            if path.is_file():
                race_paths.append(path)
            continue
        try:
            raw, stat = _stable_read_bytes(
                path,
                offset=node["tail_offset"],
                size=node["tail_size"],
                run_id=run_id,
            )
        except DayInputUpdateRace as exc:
            race_paths.extend(Path(value) for value in exc.mismatch_paths)
            continue
        if not (
            stat == (node["file_size"], node["mtime_ns"])
            and len(raw) == node["tail_size"]
            and hashlib.sha256(raw).hexdigest() == node["tail_sha256"]
        ):
            race_paths.append(path)
    if race_paths:
        raise DayInputUpdateRace(
            "day_inputs_changed_after_recompute",
            mismatch_paths=race_paths,
            run_id=run_id,
        )


def _best_concept(concepts: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        {
            "name": item.get("name"),
            "heat_score": item.get("heat_score"),
            "mean_return_5d": item.get("mean_return_5d"),
            "up_ratio_5d": item.get("up_ratio_5d"),
            "normalized_heat": min(1.0, max(0.0, float(item.get("heat_score") or 0.0) / 100.0)),
        }
        for item in concepts
    ]
    return min(
        candidates,
        key=lambda item: (-float(item.get("heat_score") or 0.0), str(item.get("name") or "")),
        default=None,
    )


def _ema(values: list[float], period: int) -> list[float]:
    alpha = 2.0 / (period + 1.0)
    output = [values[0]]
    for value in values[1:]:
        output.append(alpha * value + (1.0 - alpha) * output[-1])
    return output


def _underlying_trend_score(
    rows: list[dict[str, Any]],
    cutoff: str,
    benchmark_calendar: Sequence[str],
) -> float | None:
    calendar = [str(value) for value in benchmark_calendar]
    usable = [row for row in rows if str(row["date"]) <= cutoff]
    if (
        len(usable) < 30
        or len(calendar) < 6
        or [str(row["date"]) for row in usable[-6:]] != calendar[-6:]
        or float(usable[-1]["close"]) <= 0
    ):
        return None
    closes = [float(row["close"]) for row in usable]
    ema3 = _ema(closes, 3)
    ema21 = _ema(closes, 21)
    ma5 = statistics.mean(closes[-5:])
    ma10 = statistics.mean(closes[-10:])
    ma20 = statistics.mean(closes[-20:])
    return5 = (closes[-1] / closes[-6] - 1.0) * 100.0
    return (
        0.40 * min(1.0, max(0.0, return5 / 5.0))
        + 0.30 * float(ema3[-1] > ema21[-1])
        + 0.30 * float(ma5 > ma10 > ma20)
    )


def _expected_c9_component(
    industry: dict[str, Any],
    concepts: list[dict[str, Any]],
    trend_score: float | None,
) -> dict[str, Any]:
    industry_score = industry.get("heat_score") if industry else None
    industry_norm = (
        min(1.0, max(0.0, float(industry_score) / 100.0))
        if industry_score is not None
        else 0.0
    )
    best_concept = _best_concept(concepts)
    concept_norm = float(best_concept["normalized_heat"]) if best_concept else 0.0
    trend_norm = min(1.0, max(0.0, float(trend_score))) if trend_score is not None else 0.0
    normalized = 0.30 * industry_norm + 0.40 * concept_norm + 0.30 * trend_norm
    coverage = (
        0.30 * float(industry_score is not None)
        + 0.40 * float(best_concept is not None)
        + 0.30 * float(trend_score is not None)
    )
    status = "AVAILABLE" if math.isclose(coverage, 1.0, abs_tol=1e-12) else "PARTIAL" if coverage > 0 else "MISSING"
    return {
        "weight": EXPECTED_C9_WEIGHT,
        "normalized_score": normalized,
        "earned_score": normalized * EXPECTED_C9_WEIGHT,
        "data_status": status,
        "coverage_fraction": coverage,
        "raw_value": {
            "industry_heat_score": industry_score,
            "industry_normalized": industry_norm,
            "best_concept": best_concept,
            "underlying_trend_score": trend_score,
        },
    }


def _c9_component_matches(actual: Any, expected: dict[str, Any]) -> bool:
    if not isinstance(actual, dict):
        return False
    return all(
        _equivalent(actual.get(key), expected[key])
        for key in (
            "weight",
            "normalized_score",
            "earned_score",
            "data_status",
            "coverage_fraction",
            "raw_value",
        )
)


def _personal_kb_finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _expected_personal_kb_confirmation(item: dict[str, Any]) -> dict[str, Any]:
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


def _personal_kb_ranking_key(item: dict[str, Any]) -> tuple[float, float, bool, str]:
    return (
        -float(item.get("score_total_raw") or 0.0),
        -float(
            (item.get("personal_kb_confirmation") or {}).get("quality_score")
            or 0.0
        ),
        not bool(item.get("big_bull_red_preference")),
        str(item.get("symbol") or ""),
    )


def _personal_kb_confirmation_shape(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    quality_score = _personal_kb_finite_number(value.get("quality_score"))
    checks = value.get("checks")
    risk_labels = value.get("risk_labels")
    expected_labels = [label for label, _weight in PERSONAL_KB_CONFIRMATION_CHECKS]
    return bool(
        value.get("model_version") == PERSONAL_KB_CONFIRMATION_MODEL["version"]
        and quality_score is not None
        and 0.0 <= quality_score <= 100.0
        and value.get("level") in {"HIGH", "MEDIUM", "LOW"}
        and isinstance(risk_labels, list)
        and all(label in expected_labels for label in risk_labels)
        and isinstance(checks, dict)
        and list(checks) == expected_labels
        and all(isinstance(checks[label], bool) for label in expected_labels)
        and isinstance(value.get("red_risk_cap_applied"), bool)
        and value.get("ranking_scope") == "exact_score_total_raw_ties_only"
    )


def _production_contract_checks(
    production: Any,
    *,
    tdx_root: Path,
    tdxhy_path: Path,
    tdxzs_path: Path,
    concept_path: Path,
) -> dict[str, bool]:
    if not isinstance(production, dict):
        return {"production_object": False}
    rows = production.get("all_results")
    excluded_rows = production.get("hard_excluded_results")
    row_list = rows if isinstance(rows, list) else []
    excluded_list = excluded_rows if isinstance(excluded_rows, list) else []
    row_dicts = isinstance(rows, list) and all(isinstance(item, dict) for item in row_list)
    excluded_dicts = isinstance(excluded_rows, list) and all(
        isinstance(item, dict) for item in excluded_list
    )
    symbols = [str(item.get("symbol") or "") for item in row_list if isinstance(item, dict)]
    excluded_symbols = [
        str(item.get("symbol") or "") for item in excluded_list if isinstance(item, dict)
    ]
    combined_symbols = [*symbols, *excluded_symbols]
    ranks = [item.get("rank") for item in row_list if isinstance(item, dict)]
    counts_match = False
    try:
        counts_match = bool(
            int(production.get("universe_count", -1)) == len(combined_symbols)
            and int(production.get("evaluated_count", -1)) == len(combined_symbols)
            and int(production.get("eligible_count", -1)) == len(row_list)
            and int(production.get("ranked_count", -1)) == len(row_list)
            and int(production.get("hard_excluded_count", -1)) == len(excluded_list)
        )
    except (TypeError, ValueError):
        pass
    model = production.get("score_model") or {}
    criteria = model.get("criteria") if isinstance(model, dict) else []
    c9 = next(
        (item for item in criteria or [] if isinstance(item, dict) and item.get("id") == "c9_sector_heat"),
        None,
    )
    c9_contract = False
    try:
        c9_contract = bool(
            isinstance(c9, dict)
            and math.isclose(float(c9.get("weight")), EXPECTED_C9_WEIGHT, abs_tol=1e-12)
            and (model.get("normalization_rules") or {}).get("c9_sector_heat")
            == EXPECTED_C9_NORMALIZATION_RULE
        )
    except (TypeError, ValueError):
        pass
    sources = production.get("source_files") or {}
    top10 = production.get("ranking_top10")
    expected_top10 = row_list[: min(10, len(row_list))]
    policy = production.get("execution_policy") or {}
    redemption_meta = production.get("redemption_announcement_snapshot") or {}
    redemption_binding_shape = bool(
        isinstance(redemption_meta, dict)
        and isinstance(redemption_meta.get("path"), str)
        and bool(redemption_meta.get("path"))
        and _is_plain_int(redemption_meta.get("size"))
        and redemption_meta.get("size") > 0
        and isinstance(redemption_meta.get("sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", redemption_meta.get("sha256") or "")
        and redemption_meta.get("run_id") == production.get("run_id")
        and redemption_meta.get("cutoff") == production.get("cutoff_trade_date")
        and redemption_meta.get("status") == "PASS"
        and redemption_meta.get("current_universe_complete") is True
    )
    return {
        "production_object": True,
        "production_status_pass": production.get("status") == "PASS",
        "production_schema_exact": production.get("schema") == EXPECTED_PRODUCTION_SCHEMA,
        "run_id_present": bool(str(production.get("run_id") or "")),
        "source_binding_mode_exact": production.get("source_binding_mode")
        == EXPECTED_SOURCE_BINDING_MODE,
        "day_input_binding_mode_exact": production.get("day_input_binding_mode")
        == DAY_INPUT_BINDING_MODE,
        "day_input_manifest_binding_shape": _day_manifest_binding_contract(
            production.get("day_input_manifest")
        ),
        "trusted_tdx_root_exact": _same_path(tdx_root, TRUSTED_TDX_ROOT),
        "trusted_tdxhy_exact": _same_path(tdxhy_path, TRUSTED_HEAT_SOURCES["industry_membership"]),
        "trusted_tdxzs_exact": _same_path(tdxzs_path, TRUSTED_HEAT_SOURCES["industry_names"]),
        "trusted_concept_source_exact": _same_path(
            concept_path, TRUSTED_HEAT_SOURCES["concept_membership"]
        ),
        "source_industry_membership_current": _source_node_matches(
            sources.get("industry_membership"), TRUSTED_HEAT_SOURCES["industry_membership"]
        ),
        "source_industry_names_current": _source_node_matches(
            sources.get("industry_names"), TRUSTED_HEAT_SOURCES["industry_names"]
        ),
        "source_concept_membership_current": _source_node_matches(
            sources.get("concept_membership"), TRUSTED_HEAT_SOURCES["concept_membership"]
        ),
        "score_model_c9_exact": c9_contract,
        "personal_kb_confirmation_model_exact": (
            production.get("personal_kb_confirmation_model")
            == PERSONAL_KB_CONFIRMATION_MODEL
        ),
        "personal_kb_confirmation_shape_exact": bool(
            combined_symbols
            and all(
                _personal_kb_confirmation_shape(item.get("personal_kb_confirmation"))
                for item in [*row_list, *excluded_list]
            )
        ),
        "result_pools_well_formed": bool(row_dicts and excluded_dicts and combined_symbols),
        "symbols_unique_nonempty": bool(
            all(combined_symbols)
            and len(combined_symbols) == len(set(combined_symbols))
            and set(symbols).isdisjoint(excluded_symbols)
        ),
        "ranks_contiguous": row_dicts and ranks == list(range(1, len(row_list) + 1)),
        "declared_counts_match": counts_match,
        "universe_partition_complete": production.get("universe_partition_complete") is True,
        "hard_exclusion_flags_exact": bool(
            all(
                item.get("hard_exclusion_pass") is True
                and item.get("hard_exclusion_reasons") == []
                for item in row_list
            )
            and all(
                item.get("hard_exclusion_pass") is False
                and isinstance(item.get("hard_exclusion_reasons"), list)
                and bool(item.get("hard_exclusion_reasons"))
                for item in excluded_list
            )
        ),
        "redemption_announcement_binding_shape": redemption_binding_shape,
        "strong_redemption_announcements_verified": bool(
            isinstance(policy, dict)
            and policy.get("strong_redemption_announcements_verified") is True
        ),
        "ranking_top10_exact": isinstance(top10, list) and _equivalent(top10, expected_top10),
    }


def compare_latest_result(
    latest_result: str | Path,
    *,
    tdx_root: str | Path = r"C:\new_tdx_mock",
    tdxhy_cfg: str | Path | None = None,
    tdxzs3_cfg: str | Path | None = None,
    infoharbor_block_dat: str | Path | None = None,
) -> dict[str, Any]:
    """Recompute heat and scores for every evaluated row; rerank eligible rows only."""

    started = time.perf_counter()
    result_path = Path(latest_result).resolve()
    result_raw, result_stat = _stable_read_bytes(result_path)
    production = json.loads(result_raw.decode("utf-8-sig"))
    result_binding = {
        "path": str(result_path),
        "size": result_stat[0],
        "mtime_ns": result_stat[1],
        "sha256": hashlib.sha256(result_raw).hexdigest(),
    }
    root = Path(tdx_root).resolve()
    tdxhy_path = Path(tdxhy_cfg or TRUSTED_HEAT_SOURCES["industry_membership"]).resolve()
    tdxzs_path = Path(tdxzs3_cfg or TRUSTED_HEAT_SOURCES["industry_names"]).resolve()
    concept_path = Path(infoharbor_block_dat or TRUSTED_HEAT_SOURCES["concept_membership"]).resolve()
    checks = _production_contract_checks(
        production,
        tdx_root=root,
        tdxhy_path=tdxhy_path,
        tdxzs_path=tdxzs_path,
        concept_path=concept_path,
    )
    rows = production.get("all_results") if isinstance(production, dict) else None
    excluded_rows = (
        production.get("hard_excluded_results") if isinstance(production, dict) else None
    )
    row_list = rows if isinstance(rows, list) else []
    excluded_list = excluded_rows if isinstance(excluded_rows, list) else []
    evaluated_list = [*row_list, *excluded_list]
    count_fields = {
        "result_count": len(evaluated_list),
        "eligible_result_count": len(row_list),
        "hard_excluded_result_count": len(excluded_list),
        "evaluated_result_count": len(evaluated_list),
    }
    if not all(checks.values()):
        return {
            "status": "FAIL",
            "schema": INDEPENDENT_VERIFY_SCHEMA,
            "production_result": str(result_path),
            "run_id": production.get("run_id") if isinstance(production, dict) else None,
            "production_result_binding": result_binding,
            **count_fields,
            "checks": checks,
            "failed_checks": sorted(name for name, passed in checks.items() if not passed),
            "elapsed_seconds": round(time.perf_counter() - started, 6),
        }
    try:
        day_snapshot = _load_bound_day_input_snapshot(production)
    except ValueError as exc:
        checks["day_input_manifest_binding_current"] = False
        checks["day_input_manifest_v2_contract_exact"] = False
        checks["day_input_snapshot_frozen"] = False
        return {
            "status": "FAIL",
            "schema": INDEPENDENT_VERIFY_SCHEMA,
            "production_result": str(result_path),
            "run_id": production.get("run_id"),
            "production_result_binding": result_binding,
            **count_fields,
            "checks": checks,
            "failed_checks": sorted(name for name, passed in checks.items() if not passed),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "elapsed_seconds": round(time.perf_counter() - started, 6),
        }
    checks["day_input_manifest_binding_current"] = True
    checks["day_input_manifest_v2_contract_exact"] = True
    checks["day_input_snapshot_frozen"] = True
    try:
        recomputed = recompute_heat(
            TRUSTED_TDX_ROOT,
            TRUSTED_HEAT_SOURCES["industry_membership"],
            TRUSTED_HEAT_SOURCES["industry_names"],
            TRUSTED_HEAT_SOURCES["concept_membership"],
            str(production.get("cutoff_trade_date") or ""),
            production.get("benchmark_calendar") or [],
            day_reader=day_snapshot.read_rows,
        )
    except ValueError as exc:
        checks["frozen_day_recompute_completed"] = False
        return {
            "status": "FAIL",
            "schema": INDEPENDENT_VERIFY_SCHEMA,
            "production_result": str(result_path),
            "run_id": production.get("run_id"),
            "production_result_binding": result_binding,
            **count_fields,
            "checks": checks,
            "failed_checks": sorted(name for name, passed in checks.items() if not passed),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "elapsed_seconds": round(time.perf_counter() - started, 6),
        }
    checks["frozen_day_recompute_completed"] = True
    checks["attempted_symbols_bound_to_manifest"] = set(
        recomputed["attempted_lookup_symbols"]
    ).issubset(day_snapshot.raw_by_alias)
    _assert_day_input_snapshot_current(day_snapshot)
    checks["day_input_post_recompute_unchanged"] = True
    result_raw_after, result_stat_after = _stable_read_bytes(
        result_path,
        run_id=str(production.get("run_id") or ""),
    )
    checks["production_result_post_recompute_unchanged"] = bool(
        result_raw_after == result_raw and result_stat_after == result_stat
    )

    industry_mismatches: list[dict[str, Any]] = []
    concept_mismatches: list[dict[str, Any]] = []
    component_mismatches: list[dict[str, Any]] = []
    total_mismatches: list[str] = []
    personal_kb_confirmation_mismatches: list[str] = []
    for item in evaluated_list:
        if item.get("personal_kb_confirmation") != _expected_personal_kb_confirmation(item):
            personal_kb_confirmation_mismatches.append(str(item.get("symbol") or ""))
        underlying = str(item.get("underlying") or "")
        membership_key = _code7(underlying)
        industry_code = recomputed["stock_industry"].get(membership_key)
        actual_industry = recomputed["industry_heat"].get(industry_code or "", {})
        actual_concepts = recomputed["concept_by_code"].get(membership_key, [])[:5]
        if not _equivalent(item.get("industry") or {}, actual_industry):
            industry_mismatches.append(
                {
                    "bond_symbol": item.get("symbol"),
                    "underlying": underlying,
                    "expected_industry_code": (item.get("industry") or {}).get("industry_code"),
                    "actual_industry_code": actual_industry.get("industry_code"),
                }
            )
        if not _equivalent(item.get("top_concepts") or [], actual_concepts):
            concept_mismatches.append(
                {
                    "bond_symbol": item.get("symbol"),
                    "underlying": underlying,
                    "expected": [value.get("source_name") for value in (item.get("top_concepts") or [])],
                    "actual": [value.get("source_name") for value in actual_concepts],
                }
            )
        actual_component = ((item.get("score_components") or {}).get("c9_sector_heat") or {})
        trend_score = _underlying_trend_score(
            day_snapshot.read_rows(str(item["underlying_symbol"]), 260),
            str(production.get("cutoff_trade_date") or ""),
            production.get("benchmark_calendar") or [],
        )
        expected_component = _expected_c9_component(actual_industry, actual_concepts, trend_score)
        if not _c9_component_matches(actual_component, expected_component):
            component_mismatches.append(
                {
                    "bond_symbol": item.get("symbol"),
                    "actual": {key: actual_component.get(key) for key in expected_component},
                    "expected": expected_component,
                }
            )
        try:
            total = sum(float(component.get("earned_score")) for component in (item.get("score_components") or {}).values())
            if not math.isclose(total, float(item.get("score_total_raw")), rel_tol=1e-12, abs_tol=1e-12):
                total_mismatches.append(str(item.get("symbol") or ""))
        except (AttributeError, TypeError, ValueError):
            total_mismatches.append(str(item.get("symbol") or ""))

    reranked = sorted(row_list, key=_personal_kb_ranking_key)
    ranking_exact = [item.get("symbol") for item in reranked] == [item.get("symbol") for item in row_list]
    ranking_exact = ranking_exact and all(item.get("rank") == index for index, item in enumerate(reranked, 1))
    checks["industry_recomputed_exact"] = not industry_mismatches
    checks["top_concepts_recomputed_exact"] = not concept_mismatches
    checks["c9_component_recomputed_exact"] = not component_mismatches
    checks["score_totals_recomputed_exact"] = not total_mismatches
    checks["personal_kb_confirmation_recomputed_exact"] = (
        not personal_kb_confirmation_mismatches
    )
    checks["full_ranking_recomputed_exact"] = ranking_exact
    passed = all(checks.values())
    return {
        "status": "PASS" if passed else "FAIL",
        "schema": INDEPENDENT_VERIFY_SCHEMA,
        "production_result": str(result_path),
        "production_result_binding": result_binding,
        "run_id": production.get("run_id"),
        "cutoff_trade_date": production.get("cutoff_trade_date"),
        **count_fields,
        "industry_count": len(recomputed["industry_heat"]),
        "concept_membership_key_count": len(recomputed["concept_by_code"]),
        "attempted_lookup_symbol_count": len(recomputed["attempted_lookup_symbols"]),
        "day_input_manifest": {
            "path": str(day_snapshot.manifest_path),
            "size": day_snapshot.manifest_stat[0],
            "mtime_ns": day_snapshot.manifest_stat[1],
            "sha256": hashlib.sha256(day_snapshot.manifest_raw).hexdigest(),
            "input_count": day_snapshot.manifest.get("input_count"),
            "alias_count": day_snapshot.manifest.get("alias_count"),
            "tail_record_limit": day_snapshot.manifest.get("tail_record_limit"),
        },
        "checks": checks,
        "failed_checks": sorted(name for name, passed in checks.items() if not passed),
        "industry_mismatch_count": len(industry_mismatches),
        "top_concepts_mismatch_count": len(concept_mismatches),
        "c9_component_mismatch_count": len(component_mismatches),
        "score_total_mismatch_count": len(total_mismatches),
        "personal_kb_confirmation_mismatch_count": len(
            personal_kb_confirmation_mismatches
        ),
        "industry_mismatches": industry_mismatches[:20],
        "top_concepts_mismatches": concept_mismatches[:20],
        "c9_component_mismatches": component_mismatches[:20],
        "score_total_mismatch_symbols": total_mismatches[:20],
        "personal_kb_confirmation_mismatch_symbols": (
            personal_kb_confirmation_mismatches[:20]
        ),
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Independent TDX industry/concept heat verifier")
    parser.add_argument("--compare-result", type=Path, required=True, help="Production latest_result.json to verify read-only")
    parser.add_argument("--tdx-root", type=Path, default=Path(r"C:\new_tdx_mock"))
    parser.add_argument("--tdxhy", type=Path)
    parser.add_argument("--tdxzs3", type=Path)
    parser.add_argument("--infoharbor", type=Path)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.attempt < 1:
        raise SystemExit("invalid --attempt")
    exit_code = 2
    try:
        report = compare_latest_result(
            args.compare_result,
            tdx_root=args.tdx_root,
            tdxhy_cfg=args.tdxhy,
            tdxzs3_cfg=args.tdxzs3,
            infoharbor_block_dat=args.infoharbor,
        )
        exit_code = 0 if report["status"] == "PASS" else 2
    except DayInputUpdateRace as exc:
        event = {
            "schema": "CONVERTIBLE-BOND-VERIFY-FAILURE-1",
            "status": "FAIL",
            "failure_code": TDX_DAY_UPDATE_RACE,
            "retryable": True,
            "script": str(Path(__file__).resolve()),
            "run_id": exc.run_id,
            "attempt": args.attempt,
            "error": str(exc),
            "reason": exc.reason,
            "mismatch_count": len(exc.mismatch_paths),
            "mismatch_paths": exc.mismatch_paths,
        }
        report = {
            "status": "FAIL",
            "schema": INDEPENDENT_VERIFY_SCHEMA,
            "production_result": str(args.compare_result.resolve()),
            "run_id": exc.run_id,
            "attempt": args.attempt,
            "failure_code": TDX_DAY_UPDATE_RACE,
            "retryable": True,
            "checks": {"day_input_post_recompute_unchanged": False},
            "failed_checks": ["day_input_post_recompute_unchanged"],
            "retry_event": event,
        }
        print(json.dumps(event, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        exit_code = 3
    except Exception as exc:
        report = {
            "status": "FAIL",
            "schema": INDEPENDENT_VERIFY_SCHEMA,
            "production_result": str(args.compare_result.resolve()),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "checks": {"structured_execution": False},
            "failed_checks": ["structured_execution"],
        }
    report = canonicalize_business_payload(report)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(args.output)
        readback = json.loads(args.output.read_text(encoding="utf-8"))
        if not _equivalent(readback, report):
            raise RuntimeError("independent verifier JSON readback mismatch")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
