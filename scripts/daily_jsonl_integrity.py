#!/usr/bin/env python3
"""流式校验应用内日线 JSONL，不把整份大文件载入内存。"""
from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APP_ROOT = Path(os.environ.get("ZHANGCAI_APP_ROOT", Path(__file__).resolve().parents[1]))
DATA_ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR", APP_ROOT / "app-data"))


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYYMMDD 或 YYYY-MM-DD")
    args = parser.parse_args()
    date = str(args.date).replace("-", "")
    if len(date) != 8 or not date.isdigit():
        raise SystemExit("--date 必须是 YYYYMMDD")
    manifest_path = DATA_ROOT / "market" / "daily" / date / "manifest.json"
    manifest = read_json(manifest_path, {})
    rel_file = str(manifest.get("file") or "market/daily/aggregate/tdx-bars.jsonl") if isinstance(manifest, dict) else "market/daily/aggregate/tdx-bars.jsonl"
    bars_path = DATA_ROOT / rel_file
    required = ("symbol", "market", "date", "open", "high", "low", "close", "amount", "volume")
    lines = 0
    invalid = 0
    symbols: set[str] = set()
    dates: Counter[str] = Counter()
    first_date = ""
    last_date = ""
    try:
        with bars_path.open("r", encoding="utf-8") as stream:
            for line in stream:
                lines += 1
                try:
                    row = json.loads(line)
                    valid = isinstance(row, dict) and all(key in row for key in required)
                    valid = valid and isinstance(row.get("date"), str) and len(row["date"]) == 8 and row["date"].isdigit()
                    for key in ("open", "high", "low", "close", "amount", "volume"):
                        value = row.get(key) if isinstance(row, dict) else None
                        valid = valid and isinstance(value, (int, float)) and math.isfinite(float(value))
                    if not valid:
                        invalid += 1
                        continue
                    symbol = str(row["symbol"])
                    symbols.add(symbol)
                    dates[row["date"]] += 1
                    first_date = first_date or row["date"]
                    last_date = row["date"]
                except (TypeError, ValueError, json.JSONDecodeError):
                    invalid += 1
    except OSError as exc:
        report = {"schema": "ZHANGCAI_DAILY_JSONL_INTEGRITY_V1", "status": "BLOCKED", "trade_date": date, "file": rel_file, "error": f"{type(exc).__name__}: {exc}", "checked_at": now_iso()}
        output = DATA_ROOT / "runtime" / f"daily-jsonl-integrity-{date}.json"
        write_json(output, report)
        report["report"] = str(output)
        print(json.dumps(report, ensure_ascii=False))
        return 2
    expected = int(manifest.get("bar_records") or 0) if isinstance(manifest, dict) else 0
    report = {
        "schema": "ZHANGCAI_DAILY_JSONL_INTEGRITY_V1",
        "status": "CLEAN_PASS" if invalid == 0 and (expected == 0 or expected == lines) else "BLOCKED",
        "trade_date": date, "file": rel_file, "manifest": f"market/daily/{date}/manifest.json",
        "checked_at": now_iso(), "line_count": lines, "manifest_bar_records": expected,
        "bad_records": invalid, "symbol_count": len(symbols), "date_count": len(dates),
        "first_seen_date": first_date, "last_seen_date": last_date,
        "target_trade_date_records": dates.get(date, 0), "top_dates": dates.most_common(10),
        "note": "流式逐行 JSON 结构与必需数值字段校验；文件 SHA-256 由统一来源清单另行校验。",
    }
    output = DATA_ROOT / "runtime" / f"daily-jsonl-integrity-{date}.json"
    report["report"] = str(output)
    write_json(output, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
