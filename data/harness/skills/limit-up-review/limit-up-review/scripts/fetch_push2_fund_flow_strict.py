#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch auxiliary fund-flow rows for the strict limit-up table.

The script never invents unavailable fund-flow values. A failed row is kept as
ok=False so downstream reports can show coverage instead of fake precision.
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TASK_DIR = Path(os.environ.get("LIMITUP_TASK_DIR", r"D:\C盘转移\日志\codex\reports\limit_up_review"))
TABLE = Path(os.environ.get("LIMITUP_TABLE", TASK_DIR / "verified_limitup_union.csv"))
DATE = os.environ.get("LIMITUP_DATE", datetime.now().strftime("%Y%m%d"))
DATE_H = os.environ.get("LIMITUP_DATE_H", f"{DATE[:4]}-{DATE[4:6]}-{DATE[6:]}")

DAY_URLS = [
    "https://push2delay.eastmoney.com/api/qt/stock/fflow/daykline/get",
    "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get",
]
QUOTE_URL = "https://push2delay.eastmoney.com/api/qt/stock/get"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Referer": "https://quote.eastmoney.com/",
    "Accept": "application/json,text/plain,*/*",
}


def code6(value: Any) -> str:
    text = str(value or "").strip()
    match = re.search(r"(\d{6})", text)
    return match.group(1) if match else text.zfill(6)


def secid_for(code: str, market: str = "") -> str:
    code = code6(code)
    market = str(market or "").upper()
    if market == "SH" or code.startswith("6"):
        return "1." + code
    return "0." + code


def req_json(url: str, params: dict[str, Any], timeout: int = 10) -> tuple[dict[str, Any], str]:
    response = requests.get(url, params=params, headers=UA, timeout=timeout)
    response.raise_for_status()
    return response.json(), response.url


def parse_day(data: dict[str, Any], used_url: str) -> dict[str, Any]:
    line = data["data"]["klines"][-1]
    parts = line.split(",")
    return {
        "ok": True,
        "source": "push2_fflow_daykline",
        "url": used_url,
        "日期": parts[0],
        "主力净流入": float(parts[1]),
        "小单净流入": float(parts[2]),
        "中单净流入": float(parts[3]),
        "大单净流入": float(parts[4]),
        "超大单净流入": float(parts[5]),
        "主力净占比": float(parts[6]),
        "收盘价": float(parts[11]),
        "涨跌幅": float(parts[12]),
    }


def fetch_day(secid: str) -> dict[str, Any]:
    params = {
        "secid": secid,
        "lmt": 1,
        "klt": 101,
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63",
    }
    errors: list[str] = []
    for url in DAY_URLS:
        try:
            data, used = req_json(url, params)
            if data.get("rc") == 0 and data.get("data") and data["data"].get("klines"):
                return parse_day(data, used)
            errors.append(f"{url}: rc={data.get('rc')}")
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {str(exc)[:160]}")
    return {"ok": False, "source": "push2_fflow_daykline", "error": " | ".join(errors)}


def fetch_quote(secid: str) -> dict[str, Any]:
    params = {"secid": secid, "fields": "f12,f14,f2,f3,f62,f66,f69,f72,f75,f78,f81,f84,f87"}
    try:
        data, used = req_json(QUOTE_URL, params)
        row = data.get("data") if data.get("rc") == 0 else None
        if not row:
            return {"ok": False, "source": "push2_stock_get_fund_fields", "url": used, "error": f"rc={data.get('rc')}"}
        return {
            "ok": True,
            "source": "push2_stock_get_fund_fields",
            "url": used,
            "日期": DATE_H,
            "主力净流入": row.get("f62"),
            "超大单净流入": row.get("f66"),
            "主力净占比": row.get("f69"),
            "大单净流入": row.get("f72"),
            "中单净流入": row.get("f78"),
            "小单净流入": row.get("f84"),
            "收盘价": row.get("f2"),
            "涨跌幅": row.get("f3"),
        }
    except Exception as exc:
        return {"ok": False, "source": "push2_stock_get_fund_fields", "error": f"{type(exc).__name__}: {str(exc)[:160]}"}


def main() -> int:
    if not TABLE.exists():
        print(json.dumps({"status": "BLOCKED", "blocks": [f"missing table: {TABLE}"]}, ensure_ascii=False, indent=2))
        return 2
    df = pd.read_csv(TABLE, dtype={"代码": str})
    required = [c for c in ["代码", "名称", "市场"] if c not in df.columns]
    if required:
        print(json.dumps({"status": "BLOCKED", "blocks": [f"table missing columns: {required}"]}, ensure_ascii=False, indent=2))
        return 2

    rows: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        code = code6(row["代码"])
        name = row.get("名称", "")
        market = row.get("市场", "")
        secid = secid_for(code, market)
        result = fetch_day(secid)
        if not result.get("ok"):
            quote = fetch_quote(secid)
            if quote.get("ok"):
                quote["daykline_error"] = result.get("error")
                result = quote
        rows.append({"代码": code, "名称": name, "市场": market, "secid": secid, **result})
        print(f"{idx + 1}/{len(df)} {code} {name} ok={result.get('ok')} source={result.get('source')}", flush=True)
        time.sleep(0.06)

    out = pd.DataFrame(rows)
    out_csv = TASK_DIR / f"push2_fund_flow_resolved_{DATE}.csv"
    out_json = TASK_DIR / f"push2_fund_flow_resolved_{DATE}.json"
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = out["ok"].astype(bool) if "ok" in out.columns else pd.Series([False] * len(out))
    summary = {
        "status": "CLEAN_PASS",
        "date": DATE,
        "total": int(len(out)),
        "ok": int(ok.sum()),
        "failed": int((~ok).sum()),
        "csv": str(out_csv),
        "json": str(out_json),
        "failed_codes": out.loc[~ok, [c for c in ["代码", "名称", "市场", "secid", "source", "error"] if c in out.columns]].to_dict("records"),
    }
    (TASK_DIR / f"push2_fund_flow_resolved_summary_{DATE}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
