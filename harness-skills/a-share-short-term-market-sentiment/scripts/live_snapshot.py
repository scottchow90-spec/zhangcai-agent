#!/usr/bin/env python3
"""Build a validated live snapshot from Lianban, Duanxianxia and local TDX."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import struct
from pathlib import Path
from typing import Any
import sys

_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_tdx_root


DAY = struct.Struct("<IIIIIfII")


def read_last(path: Path, count: int) -> list[tuple[int, int, float]]:
    if not path.is_file() or path.stat().st_size < DAY.size * count:
        return []
    with path.open("rb") as handle:
        handle.seek(-DAY.size * count, 2)
        rows = []
        for _ in range(count):
            date_i, _o, _h, _l, close_i, amount, _v, _u = DAY.unpack(handle.read(DAY.size))
            rows.append((date_i, close_i, float(amount)))
        return rows


def is_equity(path: Path) -> bool:
    name = path.stem.lower()
    return (
        name.startswith(("sh600", "sh601", "sh603", "sh605", "sh688"))
        or name.startswith(("sz000", "sz001", "sz002", "sz003", "sz300", "sz301"))
        or name.startswith(("bj4", "bj8", "bj9"))
    )


def tdx_market(tdx_root: Path, target_date: str) -> dict[str, Any]:
    target_i = int(target_date.replace("-", ""))
    files = [p for market in ("sh", "sz", "bj") for p in (tdx_root / "vipdoc" / market / "lday").glob("*.day") if is_equity(p)]
    advancers = decliners = flat = 0
    previous_advancers = previous_decliners = previous_flat = 0
    current_amount = previous_amount = 0.0
    covered = 0
    for path in files:
        rows = read_last(path, 3)
        if len(rows) != 3 or rows[-1][0] != target_i:
            continue
        covered += 1
        before_previous, previous, current = rows
        current_amount += max(0.0, current[2])
        previous_amount += max(0.0, previous[2])
        if current[1] > previous[1]:
            advancers += 1
        elif current[1] < previous[1]:
            decliners += 1
        else:
            flat += 1
        if previous[1] > before_previous[1]:
            previous_advancers += 1
        elif previous[1] < before_previous[1]:
            previous_decliners += 1
        else:
            previous_flat += 1
    index_rows = read_last(tdx_root / "vipdoc" / "sh" / "lday" / "sh000001.day", 2)
    if len(index_rows) != 2 or index_rows[1][0] != target_i:
        raise ValueError("tongdaxin_index_date_mismatch")
    if covered < 3000:
        raise ValueError(f"tongdaxin_coverage_insufficient:{covered}")
    index_change = (index_rows[1][1] / index_rows[0][1] - 1) * 100
    if previous_amount <= 0:
        raise ValueError("tongdaxin_previous_amount_missing")
    if current_amount <= 0:
        raise ValueError("tongdaxin_current_amount_missing")
    amount_change = (current_amount / previous_amount - 1) * 100
    return {
        "trading_date": target_date,
        "covered": covered,
        "advancers": advancers,
        "decliners": decliners,
        "flat": flat,
        "previous_advancers": previous_advancers,
        "previous_decliners": previous_decliners,
        "previous_flat": previous_flat,
        "index_change_pct": round(index_change, 3),
        "total_amount_billion": round(current_amount / 100_000_000, 1),
        "amount_change_pct": round(amount_change, 2),
    }


def build_snapshot(lianban_path: Path, duanxian_path: Path, tdx_root: Path) -> dict[str, Any]:
    lianban = json.loads(lianban_path.read_text(encoding="utf-8"))
    duan = json.loads(duanxian_path.read_text(encoding="utf-8"))
    target = str(lianban.get("target_date", ""))
    if lianban.get("status") != "CLEAN_PASS" or not target:
        raise ValueError("lianban_not_verified")
    for key in ("open_data", "page"):
        if lianban.get("sources", {}).get(key, {}).get("status_code") != 200:
            raise ValueError(f"lianban_source_failed:{key}")
    required = ("ztcount", "ztpool", "jinjidata", "amount")
    datasets = duan.get("datasets", {})
    failed = [key for key in required if not datasets.get(key, {}).get("success")]
    if failed:
        raise ValueError("duanxianxia_failed:" + ",".join(failed))
    duan_date = str(datasets["jinjidata"].get("data", {}).get("date", ""))
    if duan_date != target:
        raise ValueError(f"duanxianxia_date_mismatch:{duan_date}:{target}")
    tdx = tdx_market(tdx_root, target)
    market = lianban["market"]
    pool_count = datasets["ztpool"]["data"].get("count", {})
    limit_up_count = pool_count.get("limit_up_count", {})
    limit_down_count = pool_count.get("limit_down_count", {})
    today_limit_up = limit_up_count.get("today", {})
    previous_limit_up = limit_up_count.get("yesterday", {})
    previous_limit_down = limit_down_count.get("yesterday", {})
    if not isinstance(today_limit_up, dict) or today_limit_up.get("num") is None or pool_count.get("zt") is None:
        raise ValueError("duanxianxia_current_metrics_missing")
    previous_limit_up_missing = [
        key for key in ("num", "lbnum", "open_num", "rate")
        if not isinstance(previous_limit_up, dict) or previous_limit_up.get(key) is None
    ]
    previous_limit_down_missing = (
        ["limit_down.num"]
        if not isinstance(previous_limit_down, dict) or previous_limit_down.get("num") is None
        else []
    )
    if previous_limit_up_missing or previous_limit_down_missing:
        missing = previous_limit_up_missing + previous_limit_down_missing
        raise ValueError("duanxianxia_previous_metrics_missing:" + ",".join(missing))
    duan_limit_up = int(pool_count["zt"])
    topics = lianban.get("topics")
    if not isinstance(topics, list):
        raise ValueError("lianban_topics_missing")
    if any(not isinstance(row, dict) or row.get("name") is None or row.get("count") is None for row in topics):
        raise ValueError("lianban_topic_metric_missing")
    snapshot_market = {
        "index_change_pct": tdx["index_change_pct"],
        "advancers": tdx["advancers"],
        "decliners": tdx["decliners"],
        "total_amount_billion": tdx["total_amount_billion"],
        "amount_change_pct": tdx["amount_change_pct"],
        "limit_up": int(market["limit_up"]),
        "limit_down": int(market["limit_down"]),
        "consecutive": int(market["consecutive"]),
        "max_board": int(market["max_board"]),
        "seal_rate": float(market["seal_rate"]),
        "broken_board": int(market["broken_board"]),
        "topic_top_count": max((int(row["count"]) for row in topics), default=0),
        "topic_count_ge3": sum(int(row["count"]) >= 3 for row in topics),
    }
    return {
        "schema": "SHORT_TERM_SENTIMENT_SNAPSHOT_V1",
        "trading_date": target,
        "market": snapshot_market,
        "topics": topics,
        "sources": {
            "tongdaxin": {"verified": True, "trading_date": target, "root": str(tdx_root), "coverage": tdx["covered"]},
            "duanxianxia": {"verified": True, "trading_date": target, "source_url": duan.get("source_page"), "datasets": list(required)},
            "lianban": {"verified": True, "trading_date": target, "reported_stage": market.get("emotion_stage"), "source_url": lianban["sources"]["page"]["url"], "attribution": "连板网", "license": "CC BY 4.0"},
        },
        "cross_validation": {
            "limit_up_difference": duan_limit_up - int(market["limit_up"]),
            "duanxianxia_limit_up": duan_limit_up,
            "lianban_limit_up": int(market["limit_up"]),
        },
        "comparisons": {
            "previous_trading_day": {
                "advancers": tdx["previous_advancers"],
                "decliners": tdx["previous_decliners"],
                "limit_up": int(previous_limit_up["num"]),
                "limit_down": int(previous_limit_down["num"]),
                "consecutive": int(previous_limit_up["lbnum"]),
                "broken_board": int(previous_limit_up["open_num"]),
                "seal_rate": round(float(previous_limit_up["rate"]) * 100, 1),
            },
            "current_trading_day": {
                "limit_up": int(today_limit_up["num"]),
                "limit_down": int(market["limit_down"]),
                "consecutive": int(market["consecutive"]),
                "broken_board": int(market["broken_board"]),
                "seal_rate": float(market["seal_rate"]),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lianban", required=True)
    parser.add_argument("--duanxian", required=True)
    parser.add_argument("--tdx-root", default=str(resolve_tdx_root()))
    parser.add_argument("--output")
    args = parser.parse_args()
    result = build_snapshot(Path(args.lianban), Path(args.duanxian), Path(args.tdx_root))
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
