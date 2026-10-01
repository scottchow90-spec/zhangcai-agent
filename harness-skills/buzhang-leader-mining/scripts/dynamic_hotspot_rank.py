#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import importlib.util
import json
import os
import re
import statistics
import struct
from collections import defaultdict
from pathlib import Path
from typing import Any

_app_scripts_dir = str(_OneStockEmbeddedPath(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_tdx_root

TDX_ROOT = resolve_tdx_root()
INFOHARBOR_BLOCK = TDX_ROOT / "T0002" / "hq_cache" / "infoharbor_block.dat"
BLOCKNEW = TDX_ROOT / "T0002" / "blocknew"
TQCENTER = TDX_ROOT / "PYPlugins" / "user" / "tqcenter.py"
DAY_RECORD = struct.Struct("<IIIIIfII")

EQUITY_PREFIXES = (
    "000", "001", "002", "003", "300", "301", "600", "601", "603", "605",
    "688", "689", "830", "831", "832", "834", "835", "836", "837", "838",
    "839", "870", "871", "872", "873", "874", "875", "876", "877", "878",
    "879", "880", "881", "882", "883", "884", "885", "886", "887", "888",
    "889", "890", "891", "892", "893", "894", "895", "896", "897", "898", "899",
)

RANK_BLOCKS = (
    (1, "RD01", "热点方向第1名"),
    (2, "RD02", "热点方向第2名"),
    (3, "RD03", "热点方向第3名"),
)
HOTSPOT_POOL = ("RDZL", "热点主线龙头挖掘")

SCORE_FIELDS = (
    "mean_return_1d",
    "median_return_1d",
    "mean_return_5d",
    "up_ratio",
    "limit_up_ratio",
    "median_volume_ratio_5d",
    "median_amount_ratio_5d",
)

# These labels describe classification/holding attributes rather than a
# tradable short-line direction, so they are excluded from the relative
# fallback when the whole market is weak.
NON_DIRECTION_MARKERS = (
    "含B股",
    "含H股",
    "ST板块",
    "中特估",
    "融资融券",
    "转融券",
    "机构重仓",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_concepts() -> list[dict[str, Any]]:
    text = INFOHARBOR_BLOCK.read_bytes().decode("gb18030", errors="ignore")
    concepts: list[dict[str, Any]] = []
    current_name = ""
    current_codes: list[str] = []

    def flush() -> None:
        if not current_name.startswith("GN_"):
            return
        codes = list(dict.fromkeys(
            code for code in current_codes if code[1:].startswith(EQUITY_PREFIXES)
        ))
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


def day_path(code7: str) -> Path | None:
    code = code7[1:]
    market = "sh" if code7[0] == "1" else "bj" if code7[0] == "2" else "sz"
    candidates = (
        TDX_ROOT / "vipdoc" / market / "lday" / f"{market}{code}.day",
        TDX_ROOT / "vipdoc" / "xinzeng" / market / "lday" / f"{market}{code}.day",
    )
    return next((path for path in candidates if path.is_file()), None)


def read_tail(code7: str, count: int = 7) -> list[dict[str, float | int]]:
    path = day_path(code7)
    if path is None or path.stat().st_size < DAY_RECORD.size * 2:
        return []
    records = path.stat().st_size // DAY_RECORD.size
    read_count = min(records, count)
    rows: list[dict[str, float | int]] = []
    with path.open("rb") as handle:
        handle.seek((records - read_count) * DAY_RECORD.size)
        for _ in range(read_count):
            chunk = handle.read(DAY_RECORD.size)
            if len(chunk) != DAY_RECORD.size:
                break
            date_i, _open, _high, _low, close_i, amount, volume, _unused = DAY_RECORD.unpack(chunk)
            rows.append({
                "date": int(date_i),
                "close": float(close_i) / 100.0,
                "amount": float(amount),
                "volume": int(volume),
            })
    return rows


def stock_snapshot(code7: str) -> dict[str, Any] | None:
    rows = read_tail(code7)
    if len(rows) < 6 or float(rows[-2]["close"]) <= 0 or float(rows[-6]["close"]) <= 0:
        return None
    previous_volumes = [float(row["volume"]) for row in rows[-6:-1] if float(row["volume"]) > 0]
    previous_amounts = [float(row["amount"]) for row in rows[-6:-1] if float(row["amount"]) > 0]
    if not previous_volumes or not previous_amounts:
        return None
    close = float(rows[-1]["close"])
    ret1 = close / float(rows[-2]["close"]) - 1.0
    ret5 = close / float(rows[-6]["close"]) - 1.0
    code = code7[1:]
    limit_threshold = 0.295 if code7[0] == "2" else 0.195 if code.startswith(("300", "301", "688")) else 0.095
    return {
        "date": int(rows[-1]["date"]),
        "close": close,
        "amount": float(rows[-1]["amount"]),
        "volume": int(rows[-1]["volume"]),
        "return_1d": ret1,
        "return_5d": ret5,
        "is_up": ret1 > 0,
        "is_limit_up": ret1 >= limit_threshold,
        "volume_ratio_5d": float(rows[-1]["volume"]) / statistics.fmean(previous_volumes),
        "amount_ratio_5d": float(rows[-1]["amount"]) / statistics.fmean(previous_amounts),
    }


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
        low = position
        high = position + len(keys) - 1
        percentile = 1.0 if total == 1 else ((low + high) / 2.0) / (total - 1)
        for key in keys:
            result[key] = percentile
        position += len(keys)
    return result


def build_sector_ranking(concepts: list[dict[str, Any]]) -> tuple[int, list[dict[str, Any]]]:
    all_codes = sorted({code for concept in concepts for code in concept["codes"]})
    snapshots = {code: item for code in all_codes if (item := stock_snapshot(code))}
    if not snapshots:
        return 0, []
    latest_date = max(int(item["date"]) for item in snapshots.values())
    snapshots = {code: item for code, item in snapshots.items() if int(item["date"]) == latest_date}
    sectors: list[dict[str, Any]] = []
    for concept in concepts:
        rows = [snapshots[code] for code in concept["codes"] if code in snapshots]
        coverage_count = len(rows)
        member_count = len(concept["codes"])
        coverage_ratio = coverage_count / member_count if member_count else 0.0
        if coverage_count < 3 or coverage_ratio < 0.5:
            continue
        ret1 = [float(row["return_1d"]) for row in rows]
        ret5 = [float(row["return_5d"]) for row in rows]
        sectors.append({
            "name": concept["name"],
            "source_name": concept["source_name"],
            "codes": concept["codes"],
            "member_count": member_count,
            "coverage_count": coverage_count,
            "coverage_ratio": coverage_ratio,
            "mean_return_1d": statistics.fmean(ret1),
            "median_return_1d": statistics.median(ret1),
            "mean_return_5d": statistics.fmean(ret5),
            "up_ratio": sum(bool(row["is_up"]) for row in rows) / coverage_count,
            "limit_up_count": sum(bool(row["is_limit_up"]) for row in rows),
            "limit_up_ratio": sum(bool(row["is_limit_up"]) for row in rows) / coverage_count,
            "median_volume_ratio_5d": statistics.median(float(row["volume_ratio_5d"]) for row in rows),
            "median_amount_ratio_5d": statistics.median(float(row["amount_ratio_5d"]) for row in rows),
        })
    if not sectors:
        return latest_date, []
    for field in SCORE_FIELDS:
        percentiles = percentile_map({item["source_name"]: float(item[field]) for item in sectors})
        for item in sectors:
            item.setdefault("percentiles", {})[field] = percentiles[item["source_name"]]
    for item in sectors:
        item["dynamic_score"] = 100.0 * statistics.fmean(item["percentiles"].values())
    sectors.sort(key=lambda item: (
        -float(item["dynamic_score"]),
        -float(item["mean_return_1d"]),
        -float(item["up_ratio"]),
        item["source_name"],
    ))
    for rank, item in enumerate(sectors, 1):
        item["rank"] = rank
    return latest_date, sectors


def stock_suffix(code7: str) -> str:
    market = "SH" if code7[0] == "1" else "BJ" if code7[0] == "2" else "SZ"
    return f"{code7[1:]}.{market}"


def is_direction_candidate(item: dict[str, Any]) -> bool:
    name = str(item.get("name", ""))
    return not any(marker in name for marker in NON_DIRECTION_MARKERS)


def load_tq():
    spec = importlib.util.spec_from_file_location("tdx_dynamic_hotspot_tq", TQCENTER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {TQCENTER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.tq.initialize(str(TQCENTER))
    return module.tq


def write_rank_blocks(qualified: list[dict[str, Any]], runtime_sync: bool) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    BLOCKNEW.mkdir(parents=True, exist_ok=True)
    tq = load_tq() if runtime_sync else None
    before_by_code: dict[str, dict[str, Any]] = {}
    if tq is not None:
        before_by_code = {str(row.get("Code")): row for row in tq.get_user_sector()}
    written: list[dict[str, Any]] = []
    hotspot_pool: dict[str, Any] = {}
    try:
        for index, (rank, alias, block_name) in enumerate(RANK_BLOCKS):
            sector = qualified[index] if index < len(qualified) else None
            codes = list(dict.fromkeys(sector["codes"])) if sector else []
            path = BLOCKNEW / f"{alias}.blk"
            path.write_bytes(("\r\n" + "\r\n".join(codes)).encode("ascii"))
            runtime_codes: list[str] = []
            if tq is not None:
                if alias not in before_by_code:
                    tq.create_sector(block_code=alias, block_name=block_name)
                tq.clear_sector(block_code=alias)
                symbols = [stock_suffix(code) for code in codes]
                for start in range(0, len(symbols), 200):
                    tq.send_user_block(block_code=alias, stocks=symbols[start:start + 200], show=False)
                runtime_codes = list(tq.get_stock_list_in_sector(alias, block_type=1))
            written.append({
                "rank": rank,
                "alias": alias,
                "block_name": block_name,
                "sector_name": sector["name"] if sector else None,
                "source_name": sector["source_name"] if sector else None,
                "dynamic_score": round(float(sector["dynamic_score"]), 6) if sector else None,
                "metrics": {field: round(float(sector[field]), 8) for field in SCORE_FIELDS} if sector else {},
                "percentiles": {field: round(float(sector["percentiles"][field]), 8) for field in SCORE_FIELDS} if sector else {},
                "member_count": len(codes),
                "coverage_count": sector["coverage_count"] if sector else 0,
                "coverage_ratio": round(float(sector["coverage_ratio"]), 6) if sector else 0.0,
                "path": str(path),
                "sha256": sha256(path),
                "size_bytes": path.stat().st_size,
                "runtime_count": len(runtime_codes) if tq is not None else None,
                "runtime_match": len(runtime_codes) == len(codes) if tq is not None else None,
            })
        pool_alias, pool_name = HOTSPOT_POOL
        pool_codes = sorted({code for sector in qualified[:3] for code in sector["codes"]})
        pool_path = BLOCKNEW / f"{pool_alias}.blk"
        pool_path.write_bytes(("\r\n" + "\r\n".join(pool_codes)).encode("ascii"))
        pool_runtime_codes: list[str] = []
        if tq is not None:
            if pool_alias not in before_by_code:
                tq.create_sector(block_code=pool_alias, block_name=pool_name)
            tq.clear_sector(block_code=pool_alias)
            pool_symbols = [stock_suffix(code) for code in pool_codes]
            for start in range(0, len(pool_symbols), 200):
                tq.send_user_block(block_code=pool_alias, stocks=pool_symbols[start:start + 200], show=False)
            pool_runtime_codes = list(tq.get_stock_list_in_sector(pool_alias, block_type=1))
        hotspot_pool = {
            "alias": pool_alias,
            "block_name": pool_name,
            "member_count": len(pool_codes),
            "path": str(pool_path),
            "sha256": sha256(pool_path),
            "size_bytes": pool_path.stat().st_size,
            "runtime_count": len(pool_runtime_codes) if tq is not None else None,
            "runtime_match": len(pool_runtime_codes) == len(pool_codes) if tq is not None else None,
        }
    finally:
        if tq is not None:
            try:
                tq.close()
            except Exception:
                pass
    return written, hotspot_pool


def run(out_dir: Path, manual_confirm: bool, runtime_sync: bool = True) -> dict[str, Any]:
    if not manual_confirm:
        return {"status": "BLOCKED", "mode": "rank-block", "reason": "missing --manual-confirm"}
    if not INFOHARBOR_BLOCK.is_file():
        return {"status": "BLOCKED", "mode": "rank-block", "reason": f"missing {INFOHARBOR_BLOCK}"}
    concepts = parse_concepts()
    latest_date, sectors = build_sector_ranking(concepts)
    if len(sectors) < 3:
        return {
            "status": "BLOCKED",
            "mode": "rank-block",
            "reason": "fewer than three eligible concept sectors",
            "concept_count": len(concepts),
            "eligible_sector_count": len(sectors),
        }
    scores = [float(item["dynamic_score"]) for item in sectors]
    breadths = [float(item["up_ratio"]) for item in sectors]
    returns = [float(item["mean_return_1d"]) for item in sectors]
    limit_ratios = [float(item["limit_up_ratio"]) for item in sectors]
    volume_ratios = [float(item["median_volume_ratio_5d"]) for item in sectors]
    score_median = statistics.median(scores)
    score_mad = statistics.median(abs(value - score_median) for value in scores)
    breadth_median = statistics.median(breadths)
    return_median = statistics.median(returns)
    limit_ratio_median = statistics.median(limit_ratios)
    volume_ratio_median = statistics.median(volume_ratios)
    elevated_score_floor = score_median + score_mad
    strict_qualified: list[dict[str, Any]] = []
    for item in sectors:
        absolute_strength = (
            float(item["mean_return_1d"]) > 0
            and float(item["median_return_1d"]) > 0
        )
        broad_strength = absolute_strength and float(item["up_ratio"]) > breadth_median
        limit_cluster = (
            absolute_strength
            and int(item["limit_up_count"]) >= 2
            and float(item["limit_up_ratio"]) > limit_ratio_median
            and float(item["mean_return_1d"]) > return_median
            and float(item["median_volume_ratio_5d"]) > volume_ratio_median
        )
        checks = {
            "score_above_median_plus_mad": float(item["dynamic_score"]) > elevated_score_floor,
            "positive_mean_and_median_return_1d": absolute_strength,
            "broad_strength_route": broad_strength,
            "limit_up_cluster_route": limit_cluster,
            "relative_fallback_route": False,
        }
        item["hotspot_checks"] = checks
        item["strict_hotspot_qualified"] = checks["score_above_median_plus_mad"] and absolute_strength and (broad_strength or limit_cluster)
        item["relative_fallback_selected"] = False
        item["hotspot_qualified"] = item["strict_hotspot_qualified"]
        if item["hotspot_qualified"]:
            strict_qualified.append(item)

    # Only strict same-day hotspots may receive ranks.  Greedily suppress a
    # concept when at least half of the smaller concept is already represented
    # by a higher-ranked direction, so one market theme cannot occupy two of
    # the three direction slots under different labels.
    qualified: list[dict[str, Any]] = []
    overlap_rejections: list[dict[str, Any]] = []
    for item in strict_qualified:
        item_codes = set(item["codes"])
        conflicts = []
        for selected in qualified:
            selected_codes = set(selected["codes"])
            denominator = min(len(item_codes), len(selected_codes))
            containment = len(item_codes & selected_codes) / denominator if denominator else 0.0
            if containment >= 0.5:
                conflicts.append({"sector_name": selected["name"], "containment": round(containment, 6)})
        if conflicts:
            overlap_rejections.append({"sector_name": item["name"], "conflicts": conflicts})
            continue
        qualified.append(item)
        if len(qualified) == 3:
            break
    fallback_used = False

    blocks, hotspot_pool = write_rank_blocks(qualified[:3], runtime_sync=runtime_sync)
    runtime_matches = [item["runtime_match"] is not False for item in blocks]
    runtime_matches.append(hotspot_pool.get("runtime_match") is not False)
    status = "PASS" if len(blocks) == 3 and all(runtime_matches) else "BLOCKED"
    payload = {
        "status": status,
        "mode": "rank-block",
        "target_system": "通达信",
        "trade_date": str(latest_date),
        "source": str(INFOHARBOR_BLOCK),
        "method": "all GN_ concepts; data-quality gate plus strict dynamic hotspot qualification; equal-weight mean of seven cross-sectional percentile metrics",
        "score_fields": list(SCORE_FIELDS),
        "score_formula": "dynamic_score = 100 * mean(percentile(metric_1), ..., percentile(metric_7))",
        "fixed_sector_conclusions": False,
        "concept_count": len(concepts),
        "eligible_sector_count": len(sectors),
        "hotspot_qualified_count": len(qualified),
        "strict_hotspot_qualified_count": len(strict_qualified),
        "relative_fallback_count": sum(bool(item.get("relative_fallback_selected")) for item in qualified),
        "hotspot_rank_count": min(3, len(qualified)),
        "distinct_direction_rule": "greedy dynamic rank; reject a lower-ranked concept when member overlap / smaller concept size >= 0.5",
        "overlap_rejections": overlap_rejections,
        "hotspot_gate": {
            "score_cross_section_median": round(score_median, 8),
            "score_cross_section_mad": round(score_mad, 8),
            "score_elevated_floor": round(elevated_score_floor, 8),
            "breadth_cross_section_median": round(breadth_median, 8),
            "return_cross_section_median": round(return_median, 8),
            "limit_up_ratio_cross_section_median": round(limit_ratio_median, 8),
            "volume_ratio_cross_section_median": round(volume_ratio_median, 8),
            "requirements": [
                "dynamic score > same-day cross-section median + MAD",
                "and positive same-day mean and median return",
                "and either broad route: above-median breadth",
                "or cluster route: at least two limit-up responses with above-median limit density, relative return and volume ratio",
            ],
            "forced_top3": False,
            "relative_fallback_used": fallback_used,
            "selection_mode": "strict",
            "relative_fallback_rule": "disabled; ranks are never filled when the strict gate yields fewer than three hotspots",
        },
        "rank_blocks": blocks,
        "hotspot_pool": hotspot_pool,
        "top10": [
            {
                "rank": item["rank"],
                "sector_name": item["name"],
                "source_name": item["source_name"],
                "dynamic_score": round(float(item["dynamic_score"]), 6),
                "member_count": item["member_count"],
                "coverage_count": item["coverage_count"],
                "hotspot_qualified": item["hotspot_qualified"],
                "strict_hotspot_qualified": item["strict_hotspot_qualified"],
                "relative_fallback_selected": item["relative_fallback_selected"],
                "hotspot_checks": item["hotspot_checks"],
            }
            for item in sectors[:10]
        ],
        "unverified": ["out-of-sample predictive validity; this ranking describes observed short-term market strength"],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "dynamic_hotspot_rank.json"
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    payload["result_path"] = str(result_path)
    return payload
