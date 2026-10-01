#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import os
import struct
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import sys


SHANGHAI = ZoneInfo("Asia/Shanghai")
_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_tdx_root

TDX_ROOT = resolve_tdx_root()
ZTC = TDX_ROOT / "T0002" / "blocknew" / "ZTC.blk"
TDX_INDEXES = {
    "上证指数": ("000001", TDX_ROOT / "vipdoc" / "sh" / "lday" / "sh000001.day"),
    "深证成指": ("399001", TDX_ROOT / "vipdoc" / "sz" / "lday" / "sz399001.day"),
    "创业板指": ("399006", TDX_ROOT / "vipdoc" / "sz" / "lday" / "sz399006.day"),
}
INDEX_API = (
    "https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&"
    "fields=f2,f3,f4,f12,f14&secids=1.000001,0.399001,0.399006"
)


def read_limit_up_count(path: Path = ZTC) -> int:
    if not path.is_file():
        return 0
    text = path.read_text(encoding="gbk", errors="ignore")
    return sum(
        1
        for line in text.splitlines()
        if len(line.strip()) >= 6 and line.strip()[-6:].isdigit()
    )


def read_tdx_index(path: Path) -> dict[str, float] | None:
    if not path.is_file():
        return None
    raw = path.read_bytes()
    record_size = 32
    if len(raw) < record_size * 2:
        return None
    previous = struct.unpack("<IIIIIfII", raw[-record_size * 2 : -record_size])
    latest = struct.unpack("<IIIIIfII", raw[-record_size:])
    previous_close = previous[4] / 100.0
    latest_close = latest[4] / 100.0
    change_pct = (
        (latest_close / previous_close - 1.0) * 100.0 if previous_close else 0.0
    )
    return {"price": latest_close, "change_pct": round(change_pct, 4)}


def fetch_index_quotes() -> tuple[dict[str, dict[str, Any]], str]:
    local_indexes: dict[str, dict[str, Any]] = {}
    for name, (code, path) in TDX_INDEXES.items():
        values = read_tdx_index(path)
        if values:
            local_indexes[name] = {"code": code, **values}
    if len(local_indexes) == len(TDX_INDEXES):
        return local_indexes, "本地通达信日线"

    request = urllib.request.Request(
        INDEX_API,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://quote.eastmoney.com/",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rows = (payload.get("data") or {}).get("diff") or []
        indexes = {
            str(row.get("f14") or row.get("f12")): {
                "code": str(row.get("f12") or ""),
                "price": float(row.get("f2") or 0),
                "change_pct": float(row.get("f3") or 0),
            }
            for row in rows
        }
        if indexes:
            return indexes, "东方财富公开指数行情"
    except Exception:
        pass

    return local_indexes, "本地通达信日线"


def build_market_warning(
    indexes: dict[str, dict[str, Any]],
    *,
    limit_up_count: int,
    data_source: str,
    generated_at: str,
) -> dict[str, Any]:
    warnings: list[dict[str, Any]] = []
    for name, values in indexes.items():
        change_pct = float(values.get("change_pct") or 0)
        if change_pct < -2:
            warnings.append(
                {"type": "major_index_drop", "index": name, "change_pct": change_pct}
            )
        elif change_pct < -1:
            warnings.append(
                {
                    "type": "moderate_index_drop",
                    "index": name,
                    "change_pct": change_pct,
                }
            )
    if 0 < limit_up_count < 30:
        warnings.append({"type": "low_limit_up_count", "count": limit_up_count})
    risk_level = (
        "HIGH" if len(warnings) >= 2 else "MODERATE" if warnings else "LOW"
    )
    return {
        "schema": "INTEGRATED_RISK_WARNING_V1",
        "status": "CLEAN_PASS" if indexes else "DATA_DEGRADED",
        "generated_at": generated_at,
        "data_source": data_source,
        "indexes": indexes,
        "limit_up_count": limit_up_count,
        "warnings": warnings,
        "risk_level": risk_level,
        "boundary": "市场风险仅用于环境和失效条件，不证明个股经营风险。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="风险排雷技能市场风险叠加器")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    indexes, source = fetch_index_quotes()
    report = build_market_warning(
        indexes,
        limit_up_count=read_limit_up_count(),
        data_source=source,
        generated_at=datetime.now(SHANGHAI).isoformat(timespec="seconds"),
    )
    path = output_dir / "market_risk_warning.json"
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({**report, "output": str(path)}, ensure_ascii=False))
    return 0 if report["status"] == "CLEAN_PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
