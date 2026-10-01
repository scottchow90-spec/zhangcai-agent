#!/usr/bin/env python3
"""Read local TDX daily bars and calculate an auditable sector snapshot."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import statistics
import struct
from datetime import date
from pathlib import Path
from typing import Optional

_app_scripts_dir = str(Path(__file__).resolve().parents[5] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_tdx_root

VIPDOC_CANDIDATES = (resolve_tdx_root() / "vipdoc",)
DAY_RECORD = struct.Struct("<IIIIIIfI")


def _market_dir(code6: str) -> str:
    if code6.startswith(("5", "6", "9")):
        return "sh"
    if code6.startswith(("4", "8")):
        return "bj"
    return "sz"


def _day_path(code6: str) -> Optional[Path]:
    market = _market_dir(code6)
    for vipdoc in VIPDOC_CANDIDATES:
        for path in (
            vipdoc / "xinzeng" / market / "lday" / f"{market}{code6}.day",
            vipdoc / market / "lday" / f"{market}{code6}.day",
        ):
            if path.is_file() and path.stat().st_size >= DAY_RECORD.size * 2:
                return path
    return None


def read_last_two_days(code6: str) -> Optional[dict]:
    path = _day_path(code6)
    if path is None:
        return None
    try:
        with path.open("rb") as handle:
            handle.seek(-DAY_RECORD.size * 2, 2)
            raw = handle.read(DAY_RECORD.size * 2)
        previous = DAY_RECORD.unpack_from(raw, 0)
        latest = DAY_RECORD.unpack_from(raw, DAY_RECORD.size)
        value = latest[0]
        latest_date = date(value // 10000, (value // 100) % 100, value % 100)
        previous_close = previous[4]
        latest_close = latest[4]
        if previous_close <= 0 or latest_close <= 0:
            return None
        return {
            "code": code6,
            "latest_date": latest_date,
            "latest_close": latest_close / 100.0,
            "previous_close": previous_close / 100.0,
            "pct_change": (latest_close - previous_close) / previous_close * 100.0,
            "path": str(path),
        }
    except (OSError, ValueError, struct.error):
        return None


def _limit_threshold(code6: str) -> float:
    if code6.startswith(("300", "301", "688")):
        return 19.5
    if code6.startswith(("4", "8")):
        return 29.5
    return 9.5


def sector_pct_from_tdx(codes: list[str]) -> Optional[dict]:
    observations = [item for code in dict.fromkeys(codes) if (item := read_last_two_days(code))]
    if not observations:
        return None
    latest_date = max(item["latest_date"] for item in observations)
    current = [item for item in observations if item["latest_date"] == latest_date]
    stale_count = len(observations) - len(current)
    if not current:
        return None
    current.sort(key=lambda item: item["pct_change"], reverse=True)
    changes = [item["pct_change"] for item in current]
    leader = current[0]
    top5 = changes[:5]
    limit_up_count = sum(item["pct_change"] >= _limit_threshold(item["code"]) for item in current)
    return {
        "latest_date": latest_date.isoformat(),
        "pct_change": round(statistics.fmean(changes), 2),
        "median_pct": round(statistics.median(changes), 2),
        "top5_mean_pct": round(statistics.fmean(top5), 2),
        "leader_code": leader["code"],
        "leader_pct": round(leader["pct_change"], 2),
        "limit_up_count": limit_up_count,
        "up_count": sum(value > 0 for value in changes),
        "down_count": sum(value < 0 for value in changes),
        "flat_count": sum(value == 0 for value in changes),
        "up_ratio": round(sum(value > 0 for value in changes) / len(changes), 4),
        "coverage_count": len(current),
        "requested_count": len(dict.fromkeys(codes)),
        "stale_count": stale_count,
        "source": "tdx_local_day",
        "sample_paths": [item["path"] for item in current[:3]],
    }


if __name__ == "__main__":
    raise SystemExit("Import sector_pct_from_tdx from run.py; this module has no standalone workflow.")

