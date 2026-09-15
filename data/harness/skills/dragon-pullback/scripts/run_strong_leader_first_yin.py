#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
import statistics
import struct
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPORTS = SKILL_ROOT / "reports"
TDX_ROOT = Path(os.environ.get("ZHANGCAI_TDX_ROOT", r"C:\new_tdx_mock"))
TDX_HUB_PATH = Path(os.environ.get(
    "TDX_HUB_PATH",
    str(Path(__file__).resolve().parents[2] / "tdx-local-hub" / "scripts" / "tdx_hub.py"),
))
BASE_DBF = TDX_ROOT / "T0002" / "hq_cache" / "base.dbf"
TDXHY = TDX_ROOT / "T0002" / "hq_cache" / "tdxhy.cfg"
TNF_FILES = {
    "SZ": TDX_ROOT / "T0002" / "hq_cache" / "szs.tnf",
    "SH": TDX_ROOT / "T0002" / "hq_cache" / "shs.tnf",
    "BJ": TDX_ROOT / "T0002" / "hq_cache" / "bjs.tnf",
}
TNF_HEADER = 50
TNF_RECORD = 360
SCHEMA_VERSION = 1


def load_tdx_hub():
    spec = importlib.util.spec_from_file_location("codex_tdx_hub", TDX_HUB_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load tdx hub: {TDX_HUB_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_dbf(path: Path, wanted: set[str]) -> list[dict[str, str]]:
    raw = path.read_bytes()
    record_count = struct.unpack_from("<I", raw, 4)[0]
    header_length = struct.unpack_from("<H", raw, 8)[0]
    record_length = struct.unpack_from("<H", raw, 10)[0]
    fields: list[tuple[str, int, int]] = []
    descriptor_offset = 32
    field_offset = 1
    while descriptor_offset + 32 <= header_length and raw[descriptor_offset] != 0x0D:
        descriptor = raw[descriptor_offset : descriptor_offset + 32]
        name = descriptor[:11].split(b"\0", 1)[0].decode("ascii", errors="replace")
        length = descriptor[16]
        if name in wanted:
            fields.append((name, field_offset, length))
        field_offset += length
        descriptor_offset += 32

    records: list[dict[str, str]] = []
    for index in range(record_count):
        start = header_length + index * record_length
        record = raw[start : start + record_length]
        if len(record) != record_length or record[:1] == b"*":
            continue
        item: dict[str, str] = {}
        for name, offset, length in fields:
            value = record[offset : offset + length]
            item[name] = value.decode("gb18030", errors="replace").strip(" \x00")
        records.append(item)
    return records


def load_names() -> dict[tuple[str, str], str]:
    names: dict[tuple[str, str], str] = {}
    for market, path in TNF_FILES.items():
        if not path.exists():
            continue
        raw = path.read_bytes()
        for offset in range(TNF_HEADER, len(raw) - TNF_RECORD + 1, TNF_RECORD):
            record = raw[offset : offset + TNF_RECORD]
            code = record[:6].decode("ascii", errors="ignore")
            if len(code) != 6 or not code.isdigit():
                continue
            name = record[31:80].split(b"\0", 1)[0].decode("gb18030", errors="replace").strip()
            if name:
                names[(market, code)] = name
    return names


def load_industries() -> dict[tuple[str, str], str]:
    industries: dict[tuple[str, str], str] = {}
    if not TDXHY.exists():
        return industries
    text = TDXHY.read_text(encoding="gb18030", errors="replace")
    market_map = {"0": "SZ", "1": "SH", "2": "BJ"}
    for line in text.splitlines():
        parts = line.strip().split("|")
        if len(parts) < 3 or len(parts[1]) != 6:
            continue
        market = market_map.get(parts[0])
        if market and parts[2]:
            industries[(market, parts[1])] = parts[2]
    return industries


def market_for_code(code: str) -> str | None:
    if code.startswith(("000", "001", "002", "003", "300", "301")):
        return "SZ"
    if code.startswith(("600", "601", "603", "605", "688", "689")):
        return "SH"
    return None


def number(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def limit_percent(code: str) -> float:
    return 0.20 if code.startswith(("300", "301", "688", "689")) else 0.10


def limit_price(previous_close: float, percent: float, direction: int = 1) -> float:
    multiplier = Decimal("1") + Decimal(str(percent * direction))
    return float((Decimal(str(previous_close)) * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def is_limit_up(previous: dict[str, Any], current: dict[str, Any], code: str) -> bool:
    target = limit_price(float(previous["close"]), limit_percent(code), 1)
    return float(current["close"]) >= target - 0.011 and float(current["high"]) - float(current["close"]) <= 0.011


def is_limit_down(previous: dict[str, Any], current: dict[str, Any], code: str) -> bool:
    target = limit_price(float(previous["close"]), limit_percent(code), -1)
    return float(current["close"]) <= target + 0.011 and float(current["close"]) - float(current["low"]) <= 0.011


def build_limit_up_flags(rows: list[dict[str, Any]], code: str) -> list[bool]:
    flags = [False]
    for index in range(1, len(rows)):
        flags.append(is_limit_up(rows[index - 1], rows[index], code))
    return flags


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def safe_ratio(numerator: float, denominator: float, default: float = 0.0) -> float:
    return numerator / denominator if denominator else default


def evaluate_at(
    rows: list[dict[str, Any]],
    index: int,
    meta: dict[str, Any],
    limit_up_flags: list[bool] | None = None,
    include_failed: bool = False,
) -> dict[str, Any] | None:
    if index < 20:
        return None
    code = str(meta["code"])
    current = rows[index]
    previous = rows[index - 1]
    closes = [float(row["close"]) for row in rows]
    flags = limit_up_flags if limit_up_flags is not None else build_limit_up_flags(rows, code)

    prior_flags = flags[max(1, index - 8) : index]
    prior_limit_count = sum(1 for value in prior_flags if value)
    last_limit_index = next((j for j in range(index - 1, max(0, index - 9), -1) if flags[j]), None)
    last_limit_distance = index - last_limit_index if last_limit_index is not None else None
    current_return = safe_ratio(float(current["close"]), float(previous["close"]), 1.0) - 1.0
    prior_8_return = safe_ratio(float(previous["close"]), float(rows[index - 9]["close"]), 1.0) - 1.0
    ma5 = mean(closes[index - 4 : index + 1])
    ma10 = mean(closes[index - 9 : index + 1])
    previous_ma5 = mean(closes[index - 5 : index])
    previous_ma10 = mean(closes[index - 10 : index])
    previous_20_high = max(closes[index - 20 : index])
    volume_ratio = safe_ratio(float(current["volume"]), float(previous["volume"]), math.inf)
    float_shares = float(meta.get("float_shares", 0.0))
    turnover = safe_ratio(float(current["volume"]), float_shares, 0.0) * 100.0
    day_range = max(float(current["high"]) - float(current["low"]), 0.01)
    close_location = (float(current["close"]) - float(current["low"])) / day_range
    upper_shadow = (float(current["high"]) - max(float(current["open"]), float(current["close"]))) / day_range
    bearish = float(current["close"]) < float(current["open"])

    strict_conditions = {
        "previous_session_is_limit_up": bool(flags[index - 1]),
        "at_least_2_limit_ups_in_previous_8_sessions": prior_limit_count >= 2,
        "previous_close_within_1pct_of_previous_20_session_high": float(previous["close"]) >= previous_20_high * 0.99,
        "previous_ma5_above_ma10": previous_ma5 > previous_ma10,
        "previous_amount_at_least_300m_cny": float(previous["amount"]) >= 300_000_000,
        "current_candle_is_bearish": bearish,
        "current_return_not_below_minus_6pct": current_return >= -0.06,
        "current_close_at_or_above_ma5": float(current["close"]) >= ma5,
        "current_low_at_or_above_98pct_of_previous_low": float(current["low"]) >= float(previous["low"]) * 0.98,
        "volume_ratio_between_0_45_and_0_95": 0.45 <= volume_ratio <= 0.95,
        "turnover_rate_between_4pct_and_25pct": 4.0 <= turnover <= 25.0,
        "close_location_at_least_0_35": close_location >= 0.35,
        "upper_shadow_ratio_at_most_0_40": upper_shadow <= 0.40,
    }

    no_intermediate_bearish = False
    if last_limit_index is not None:
        no_intermediate_bearish = all(
            float(rows[j]["close"]) >= float(rows[j]["open"])
            for j in range(last_limit_index + 1, index)
        )
    last_limit_low = float(rows[last_limit_index]["low"]) if last_limit_index is not None else 0.0
    practical_conditions = {
        "last_limit_up_within_3_sessions": last_limit_distance is not None and 1 <= last_limit_distance <= 3,
        "at_least_1_limit_up_in_previous_8_sessions": prior_limit_count >= 1,
        "previous_8_session_return_at_least_15pct": prior_8_return >= 0.15,
        "first_bearish_candle_after_last_limit_up": bearish and no_intermediate_bearish,
        "current_return_not_below_minus_7pct": current_return >= -0.07,
        "current_close_at_or_above_ma10": float(current["close"]) >= ma10,
        "current_low_holds_95pct_of_last_limit_up_low": last_limit_index is not None and float(current["low"]) >= last_limit_low * 0.95,
        "volume_ratio_between_0_35_and_1_20": 0.35 <= volume_ratio <= 1.20,
        "turnover_rate_between_2pct_and_30pct": 2.0 <= turnover <= 30.0,
        "current_amount_at_least_100m_cny": float(current["amount"]) >= 100_000_000,
        "close_location_at_least_0_25": close_location >= 0.25,
        "upper_shadow_ratio_at_most_0_50": upper_shadow <= 0.50,
        "previous_amount_at_least_150m_cny": float(previous["amount"]) >= 150_000_000,
    }

    strict = all(strict_conditions.values())
    strict_except_volume = all(
        value for key, value in strict_conditions.items() if key != "volume_ratio_between_0_45_and_0_95"
    )
    turnover_divergence_conditions = {
        "all_strict_conditions_except_shrinking_volume": strict_except_volume,
        "at_least_3_limit_ups_in_previous_8_sessions": prior_limit_count >= 3,
        "previous_8_session_return_at_least_30pct": prior_8_return >= 0.30,
        "volume_ratio_above_0_95_and_at_most_1_50": 0.95 < volume_ratio <= 1.50,
        "turnover_rate_between_8pct_and_25pct": 8.0 <= turnover <= 25.0,
        "current_amount_at_least_1b_cny": float(current["amount"]) >= 1_000_000_000,
        "upper_shadow_ratio_at_most_0_35": upper_shadow <= 0.35,
    }
    turnover_divergence = all(turnover_divergence_conditions.values())
    practical = all(practical_conditions.values())
    if not strict and not turnover_divergence and not practical and not include_failed:
        return None
    grade = "S" if strict else "T" if turnover_divergence else "A" if practical else "NONE"
    metrics = {
        "date": str(current["date"]),
        "open": round(float(current["open"]), 2),
        "high": round(float(current["high"]), 2),
        "low": round(float(current["low"]), 2),
        "close": round(float(current["close"]), 2),
        "return_pct": round(current_return * 100.0, 3),
        "prior_8_return_pct": round(prior_8_return * 100.0, 3),
        "prior_limit_up_count": prior_limit_count,
        "last_limit_up_distance": last_limit_distance,
        "volume_ratio": round(volume_ratio, 4),
        "turnover_pct": round(turnover, 3),
        "ma5": round(ma5, 3),
        "ma10": round(ma10, 3),
        "close_location": round(close_location, 4),
        "upper_shadow_ratio": round(upper_shadow, 4),
        "amount_cny": round(float(current["amount"]), 2),
        "previous_amount_cny": round(float(previous["amount"]), 2),
    }
    return {
        "grade": grade,
        "strict": strict,
        "turnover_divergence": turnover_divergence,
        "practical": practical,
        "strict_conditions": strict_conditions,
        "turnover_divergence_conditions": turnover_divergence_conditions,
        "practical_conditions": practical_conditions,
        "metrics": metrics,
        "prior_two_consecutive_limit_ups": bool(index >= 2 and flags[index - 1] and flags[index - 2]),
    }


def score_candidate(candidate: dict[str, Any], market: dict[str, Any], sector_percentile: float) -> tuple[int, dict[str, int]]:
    metrics = candidate["metrics"]
    limit_count = int(metrics["prior_limit_up_count"])
    prior_return = float(metrics["prior_8_return_pct"])
    volume_ratio = float(metrics["volume_ratio"])
    turnover = float(metrics["turnover_pct"])
    upper_shadow = float(metrics["upper_shadow_ratio"])
    low_holds_previous = bool(candidate["strict_conditions"]["current_low_at_or_above_98pct_of_previous_low"])
    close_above_ma5 = bool(candidate["strict_conditions"]["current_close_at_or_above_ma5"])

    leader = (15 if limit_count >= 3 else 10 if limit_count >= 2 else 6)
    leader += 10 if candidate.get("prior_two_consecutive_limit_ups") else 0
    leader += 10 if prior_return >= 30 else 6 if prior_return >= 20 else 3
    leader += 5 if float(metrics["previous_amount_cny"]) >= 500_000_000 else 3

    first_yin = 10 if 0.45 <= volume_ratio <= 0.80 else 6 if volume_ratio <= 1.0 else 3
    first_yin += 8 if close_above_ma5 else 4
    first_yin += 7 if low_holds_previous else 4
    first_yin += 5 if upper_shadow <= 0.25 else 3 if upper_shadow <= 0.40 else 1
    first_yin += 5 if 4.0 <= turnover <= 18.0 else 3

    limit_ratio = float(market["limit_up_down_ratio"])
    breadth = float(market["advance_ratio"])
    environment = 10 if sector_percentile >= 0.70 else 6 if sector_percentile >= 0.50 else 3
    environment += 8 if limit_ratio >= 2.5 else 5 if limit_ratio >= 1.5 else 2
    environment += 7 if breadth >= 0.55 else 4 if breadth >= 0.45 else 1
    parts = {"leader_strength": leader, "first_yin_quality": first_yin, "market_sector_environment": environment}
    return min(sum(parts.values()), 100), parts


def partition_candidates(candidates: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "strict": [item for item in candidates if item.get("grade") == "S"],
        "turnover_divergence": [item for item in candidates if item.get("grade") == "T"],
        "practical": [item for item in candidates if item.get("grade") == "A"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Full-market local TDX strong-leader first-yin selector")
    parser.add_argument("--history-days", type=int, default=120)
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    started = dt.datetime.now().astimezone()
    hub = load_tdx_hub()
    if not BASE_DBF.exists() or not TDX_HUB_PATH.exists():
        print(json.dumps({"status": "BLOCKED", "reason": "missing local TDX source"}, ensure_ascii=False))
        return 2

    index_path = hub.day_path("999999.SH")
    index_rows = hub.read_records(index_path, hub.DAY_RECORD, hub.parse_day_record, 5)
    if not index_rows:
        print(json.dumps({"status": "BLOCKED", "reason": "missing Shanghai index daily data"}, ensure_ascii=False))
        return 2
    latest_trade_date = str(index_rows[-1]["date"])

    names = load_names()
    industries = load_industries()
    base_rows = parse_dbf(BASE_DBF, {"GPDM", "LTAG", "SSDATE", "HY"})
    universe: list[dict[str, Any]] = []
    for item in base_rows:
        code = item.get("GPDM", "")
        market = market_for_code(code)
        if market is None:
            continue
        name = names.get((market, code), "")
        upper_name = name.upper()
        if not name or "ST" in upper_name or "退" in name:
            continue
        float_shares = number(item.get("LTAG", "")) * 10_000.0
        if float_shares <= 0:
            continue
        universe.append(
            {
                "code": code,
                "market": market,
                "symbol": f"{code}.{market}",
                "name": name,
                "float_shares": float_shares,
                "listing_date": item.get("SSDATE", ""),
                "industry": industries.get((market, code)) or f"HY:{item.get('HY', '')}",
            }
        )

    scan_stats = defaultdict(int)
    current_candidates: list[dict[str, Any]] = []
    sector_returns: dict[str, list[float]] = defaultdict(list)
    current_market_rows: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    history_counts = {"S": 0, "T": 0, "A": 0}
    history_dates: dict[str, int] = defaultdict(int)
    history_samples: list[dict[str, Any]] = []
    near_misses: list[dict[str, Any]] = []
    source_fingerprint_rows: list[str] = []

    for meta in universe:
        path = hub.day_path(meta["symbol"])
        if not path.exists():
            scan_stats["missing_day_file"] += 1
            continue
        stat = path.stat()
        source_fingerprint_rows.append(f"{path}|{stat.st_size}|{stat.st_mtime_ns}")
        rows = hub.read_records(path, hub.DAY_RECORD, hub.parse_day_record, max(180, args.history_days + 40))
        if len(rows) < 60:
            scan_stats["insufficient_history"] += 1
            continue
        scan_stats["kline_loaded"] += 1
        if str(rows[-1]["date"]) != latest_trade_date:
            scan_stats["not_latest_trade_date"] += 1
            continue
        scan_stats["latest_trade_date"] += 1
        limit_up_flags = build_limit_up_flags(rows, meta["code"])
        current_market_rows.append((rows[-2], rows[-1], meta["code"]))
        five_return = safe_ratio(float(rows[-1]["close"]), float(rows[-6]["close"]), 1.0) - 1.0
        sector_returns[meta["industry"]].append(five_return)

        current_eval = evaluate_at(rows, len(rows) - 1, meta, limit_up_flags, include_failed=True)
        if current_eval and (current_eval["strict"] or current_eval["turnover_divergence"] or current_eval["practical"]):
            current_eval.update(
                {
                    "symbol": meta["symbol"],
                    "code": meta["code"],
                    "market": meta["market"],
                    "name": meta["name"],
                    "industry": meta["industry"],
                    "listing_date": meta["listing_date"],
                    "source": {
                        "path": str(path),
                        "size": stat.st_size,
                        "sha256": file_sha256(path),
                    },
                }
            )
            current_candidates.append(current_eval)
        elif current_eval:
            metrics = current_eval["metrics"]
            if bool(current_eval["strict_conditions"]["current_candle_is_bearish"]) and int(metrics["prior_limit_up_count"]) >= 1:
                near_misses.append(
                    {
                        "symbol": meta["symbol"],
                        "name": meta["name"],
                        "industry": meta["industry"],
                        "strict_pass_count": sum(1 for value in current_eval["strict_conditions"].values() if value),
                        "practical_pass_count": sum(1 for value in current_eval["practical_conditions"].values() if value),
                        "failed_strict_conditions": [key for key, value in current_eval["strict_conditions"].items() if not value],
                        "failed_practical_conditions": [key for key, value in current_eval["practical_conditions"].items() if not value],
                        "metrics": metrics,
                    }
                )

        history_start = max(20, len(rows) - args.history_days - 1)
        for index in range(history_start, len(rows) - 1):
            historical = evaluate_at(rows, index, meta, limit_up_flags)
            if not historical:
                continue
            grade = str(historical["grade"])
            history_counts[grade] += 1
            history_dates[str(historical["metrics"]["date"])] += 1
            history_samples.append(
                {
                    "date": historical["metrics"]["date"],
                    "symbol": meta["symbol"],
                    "name": meta["name"],
                    "grade": grade,
                    "return_pct": historical["metrics"]["return_pct"],
                    "prior_limit_up_count": historical["metrics"]["prior_limit_up_count"],
                }
            )

    advances = declines = flats = limit_ups = limit_downs = 0
    for previous, current, code in current_market_rows:
        change = safe_ratio(float(current["close"]), float(previous["close"]), 1.0) - 1.0
        if change > 0.0001:
            advances += 1
        elif change < -0.0001:
            declines += 1
        else:
            flats += 1
        limit_ups += int(is_limit_up(previous, current, code))
        limit_downs += int(is_limit_down(previous, current, code))
    breadth_denominator = max(advances + declines + flats, 1)
    market = {
        "advances": advances,
        "declines": declines,
        "flats": flats,
        "advance_ratio": round(advances / breadth_denominator, 4),
        "limit_ups": limit_ups,
        "limit_downs": limit_downs,
        "limit_up_down_ratio": round(limit_ups / max(limit_downs, 1), 4),
        "veto": limit_downs > limit_ups,
    }

    sector_medians = {key: statistics.median(values) for key, values in sector_returns.items() if values}
    ranked_sector_values = sorted(sector_medians.values())

    def sector_percentile(industry: str) -> float:
        value = sector_medians.get(industry)
        if value is None or not ranked_sector_values:
            return 0.0
        count = sum(1 for item in ranked_sector_values if item <= value)
        return count / len(ranked_sector_values)

    for candidate in current_candidates:
        percentile = sector_percentile(candidate["industry"])
        score, parts = score_candidate(candidate, market, percentile)
        candidate["sector"] = {
            "code": candidate["industry"],
            "five_session_median_return_pct": round(sector_medians.get(candidate["industry"], 0.0) * 100.0, 3),
            "strength_percentile": round(percentile, 4),
        }
        candidate["score"] = score
        candidate["score_parts"] = parts
        candidate["technical_trade_ready"] = bool(
            candidate["grade"] in {"S", "T"} and score >= 70 and not market["veto"] and percentile >= 0.45
        )
        candidate["invalidation"] = {
            "first_yin_low": candidate["metrics"]["low"],
            "close_below_first_yin_low": True,
            "three_sessions_no_new_high_and_close_below_ma5": True,
        }

    grade_order = {"S": 0, "T": 1, "A": 2}
    current_candidates.sort(key=lambda item: (grade_order.get(item["grade"], 9), -item["score"], item["symbol"]))
    near_misses.sort(
        key=lambda item: (
            -int(item["metrics"]["prior_limit_up_count"]),
            -int(item["strict_pass_count"]),
            -int(item["practical_pass_count"]),
            -float(item["metrics"]["prior_8_return_pct"]),
        )
    )
    output_candidates = current_candidates[: args.top]
    for candidate in output_candidates:
        candidate["selection_status"] = "SIGNAL"
    candidate_groups = partition_candidates(output_candidates)
    strict_candidates = candidate_groups["strict"]
    turnover_divergence_candidates = candidate_groups["turnover_divergence"]
    practical_candidates = candidate_groups["practical"]
    trade_ready_candidates = [item for item in output_candidates if item["technical_trade_ready"]]
    current_state = (
        "STRICT_NONZERO"
        if strict_candidates
        else "TURNOVER_NONZERO"
        if turnover_divergence_candidates
        else "PRACTICAL_NONZERO"
        if practical_candidates
        else "NO_CURRENT_SIGNAL"
    )
    historical_signal_count = history_counts["S"] + history_counts["T"] + history_counts["A"]
    selector_operational = scan_stats["latest_trade_date"] > 1000 and historical_signal_count > 0
    selection_status = "SIGNAL" if output_candidates else "NO_SIGNAL"
    candidate_symbols = [str(item["symbol"]) for item in output_candidates]

    source_fingerprint = hashlib.sha256("\n".join(sorted(source_fingerprint_rows)).encode("utf-8")).hexdigest()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "strategy_id": "strong-leader-first-yin-v1",
        "generated_at": started.isoformat(timespec="seconds"),
        "status": "CLEAN_PASS" if selector_operational else "BLOCKED",
        "selection_status": selection_status,
        "current_state": current_state,
        "latest_trade_date": latest_trade_date,
        "data_source": {
            "type": "local_tdx_raw_daily",
            "root": str(TDX_ROOT),
            "index_path": str(index_path),
            "index_sha256": file_sha256(index_path),
            "base_dbf": str(BASE_DBF),
            "base_dbf_sha256": file_sha256(BASE_DBF),
            "source_snapshot_sha256": source_fingerprint,
        },
        "universe": {
            "base_records": len(base_rows),
            "eligible_security_records": len(universe),
            "scan_stats": dict(scan_stats),
        },
        "market": market,
        "selection": {
            "candidate_count": len(output_candidates),
            "candidates": output_candidates,
            "strict_count": len(strict_candidates),
            "turnover_divergence_count": len(turnover_divergence_candidates),
            "practical_count": len(practical_candidates),
            "technical_trade_ready_count": len(trade_ready_candidates),
            "strict_candidates": strict_candidates,
            "turnover_divergence_candidates": turnover_divergence_candidates,
            "practical_candidates": practical_candidates,
            "technical_trade_ready_candidates": trade_ready_candidates,
            "near_miss_diagnostics": near_misses[: args.top],
        },
        "historical_replay": {
            "purpose": "signal_trigger_replay_completed",
            "lookback_sessions": args.history_days,
            "signal_count": historical_signal_count,
            "strict_signal_count": history_counts["S"],
            "turnover_divergence_signal_count": history_counts["T"],
            "practical_signal_count": history_counts["A"],
            "signal_date_count": len(history_dates),
            "latest_signal_dates": sorted(history_dates.items(), reverse=True)[:20],
            "samples": sorted(history_samples, key=lambda item: (item["date"], item["grade"]), reverse=True)[:30],
        },
        "validation": {
            "selector_operational": selector_operational,
            "full_market_latest_records_over_1000": scan_stats["latest_trade_date"] > 1000,
            "historical_replay_nonzero": historical_signal_count > 0,
            "current_selection_nonzero": bool(current_candidates),
            "candidate_count_matches": len(output_candidates) == len(candidate_symbols),
            "unique_stock_candidates": len(candidate_symbols) == len(set(candidate_symbols)),
            "all_strict_candidates_have_all_strict_conditions_true": all(
                all(item["strict_conditions"].values()) for item in strict_candidates
            ),
            "all_practical_candidates_have_all_practical_conditions_true": all(
                all(item["practical_conditions"].values()) for item in practical_candidates
            ),
            "all_turnover_divergence_candidates_have_all_conditions_true": all(
                all(item["turnover_divergence_conditions"].values()) for item in turnover_divergence_candidates
            ),
        },
        "risk_boundary": {
            "decision_scope": "local_tdx_end_of_day_technical_selection",
            "external_event_data": "not_used_in_selection",
            "entry_timing": "not_a_trade_instruction",
            "historical_validation": "signal_trigger_replay_completed",
            "guaranteed_profit": False,
        },
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    output = Path(args.output) if args.output else REPORTS / f"strong-leader-first-yin-{latest_trade_date}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_output = REPORTS / "strong-leader-first-yin-latest.json"
    latest_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "status": payload["status"],
        "strategy_id": payload["strategy_id"],
        "selection_status": selection_status,
        "current_state": current_state,
        "latest_trade_date": latest_trade_date,
        "strict_count": len(strict_candidates),
        "turnover_divergence_count": len(turnover_divergence_candidates),
        "practical_count": len(practical_candidates),
        "technical_trade_ready_count": len(trade_ready_candidates),
        "candidate_count": len(output_candidates),
        "historical_signal_count": historical_signal_count,
        "report": str(output),
        "latest_report": str(latest_output),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if selector_operational else 2


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
