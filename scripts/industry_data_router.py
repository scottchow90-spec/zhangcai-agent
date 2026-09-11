#!/usr/bin/env python3
"""Shared public-industry data router with verified multi-source failover."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterable


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


class AllIndustrySourcesFailed(RuntimeError):
    def __init__(self, attempts: list[dict[str, Any]]) -> None:
        super().__init__("all public industry sources failed or returned no usable rows")
        self.attempts = attempts


@dataclass(frozen=True)
class Source:
    name: str
    function: Callable[[], list[dict[str, Any]]]
    retries: int = 1


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def numeric(value: Any, default: float = 0.0) -> float:
    if value is None or value == "" or str(value).strip() in {"-", "--", "nan", "None"}:
        return default
    try:
        return float(str(value).replace(",", "").replace("%", ""))
    except (TypeError, ValueError):
        return default


def integer(value: Any, default: int = 0) -> int:
    try:
        return int(numeric(value, float(default)))
    except (TypeError, ValueError, OverflowError):
        return default


def first(item: Any, names: Iterable[str], default: Any = None) -> Any:
    for name in names:
        try:
            value = item.get(name)
        except AttributeError:
            continue
        if value is not None and str(value).strip() not in {"", "nan", "None"}:
            return value
    return default


def standard_row(
    *,
    name: str,
    source: str,
    pct_change: float,
    leader_code: str = "",
    leader_name: str = "",
    leader_pct: float = 0.0,
    member_count: int = 0,
    up_count: int | None = None,
    down_count: int | None = None,
) -> dict[str, Any]:
    total = (up_count or 0) + (down_count or 0)
    return {
        "name": name.strip(),
        "source": source,
        "source_path": source,
        "latest_date": date.today().isoformat(),
        "pct_change": pct_change,
        "median_pct": None,
        "top5_mean_pct": None,
        "leader_code": leader_code.strip(),
        "leader_name": leader_name.strip(),
        "leader_pct": leader_pct,
        "limit_up_count": None,
        "up_count": up_count,
        "down_count": down_count,
        "up_ratio": round((up_count or 0) / total, 4) if total else 0.0,
        "member_count": member_count or total,
        "coverage_count": 0,
        "coverage_ratio": 0.0,
        "local_codes": [],
        "sample_paths": [],
        "needs_tdx_confirmation": True,
    }


def eastmoney_akshare() -> list[dict[str, Any]]:
    import akshare as ak

    frame = ak.stock_board_industry_name_em()
    rows: list[dict[str, Any]] = []
    for _, item in frame.iterrows():
        name = str(first(item, ("板块名称", "名称", "板块"), "")).strip()
        if not name:
            continue
        up_count = integer(first(item, ("上涨家数",), 0))
        down_count = integer(first(item, ("下跌家数",), 0))
        rows.append(standard_row(
            name=name,
            source="akshare.stock_board_industry_name_em",
            pct_change=numeric(first(item, ("涨跌幅",), 0)),
            leader_code=str(first(item, ("领涨股票代码", "领涨股票"), "")),
            leader_name=str(first(item, ("领涨股票名称", "领涨股票"), "")),
            leader_pct=numeric(first(item, ("领涨股票涨跌幅", "领涨股-涨跌幅"), 0)),
            member_count=up_count + down_count,
            up_count=up_count,
            down_count=down_count,
        ))
    return rows


def sina_akshare() -> list[dict[str, Any]]:
    import akshare as ak

    frame = ak.stock_sector_spot(indicator="新浪行业")
    rows: list[dict[str, Any]] = []
    for _, item in frame.iterrows():
        name = str(first(item, ("板块", "名称"), "")).strip()
        if not name:
            continue
        rows.append(standard_row(
            name=name,
            source="akshare.stock_sector_spot:新浪行业",
            pct_change=numeric(first(item, ("涨跌幅",), 0)),
            leader_code=str(first(item, ("股票代码",), "")),
            leader_name=str(first(item, ("股票名称",), "")),
            leader_pct=numeric(first(item, ("个股-涨跌幅",), 0)),
            member_count=integer(first(item, ("公司家数",), 0)),
        ))
    return rows


def validate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    required = {"name", "source", "latest_date", "pct_change", "leader_name", "member_count"}
    usable = [row for row in rows if required.issubset(row) and str(row.get("name", "")).strip()]
    if not usable:
        raise ValueError("source returned no standardized usable industry rows")
    return usable


def fetch_industry_snapshot(sources: list[Source] | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    active_sources = sources or [
        Source("eastmoney_akshare", eastmoney_akshare, retries=2),
        Source("sina_akshare", sina_akshare, retries=2),
    ]
    attempts: list[dict[str, Any]] = []
    for source in active_sources:
        for attempt_number in range(1, max(1, source.retries) + 1):
            started = time.perf_counter()
            try:
                rows = validate_rows(source.function())
                attempt = {
                    "source": source.name,
                    "attempt": attempt_number,
                    "status": "PASS",
                    "row_count": len(rows),
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                }
                attempts.append(attempt)
                return rows, {
                    "status": "PASS",
                    "selected_source": source.name,
                    "row_count": len(rows),
                    "generated_at": now_iso(),
                    "attempts": attempts,
                    "failover_used": any(item["status"] != "PASS" for item in attempts[:-1]),
                }
            except Exception as exc:
                attempts.append({
                    "source": source.name,
                    "attempt": attempt_number,
                    "status": "FAIL",
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:500],
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                })
                if attempt_number < source.retries:
                    time.sleep(0.35 * attempt_number)
    raise AllIndustrySourcesFailed(attempts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch a verified public A-share industry snapshot with failover")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        rows, audit = fetch_industry_snapshot()
        result = {"status": "PASS", "audit": audit, "rows": rows}
        exit_code = 0
    except AllIndustrySourcesFailed as exc:
        result = {"status": "FAIL", "reason": str(exc), "attempts": exc.attempts, "rows": []}
        exit_code = 3
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
