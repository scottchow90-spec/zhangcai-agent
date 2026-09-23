#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-analysis entry: eastmoney quote primary, TDX local fallback."""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import json, sys, os
from datetime import datetime
from pathlib import Path
import urllib.request

WORKSPACE = Path(__file__).resolve().parent.parent.parent.parent
RUN_ID = os.environ.get("SKILL_FULLFLOW_RUN_ID", "2026-06-12_skill_fullflow_all")
OUTPUT_DIR = WORKSPACE / "reports" / RUN_ID / "stock-analysis"
_tdx_root_text = (
    os.environ.get("ZHANGCAI_TDX_ROOT")
    or os.environ.get("TDX_ROOT")
    or ""
).strip()
TDX_ROOT = Path(_tdx_root_text or os.environ.get("ZHANGCAI_DEV_TDX_ROOT", r"C:\new_tdx_mock")).expanduser().resolve()
TDX_PATH = TDX_ROOT / "vipdoc" / "sh" / "lday" / "sh600519.day"


def from_eastmoney():
    secid = "1.600519"
    url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60,f116,f117,f162,f167,f168,f169,f170,f171"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        quote = json.loads(resp.read().decode("utf-8")).get("data", {})
    url2 = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&secid={secid}&end=20500101&lmt=60"
    req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    with urllib.request.urlopen(req2, timeout=15) as resp2:
        kline = json.loads(resp2.read().decode("utf-8")).get("data", {}).get("klines", [])
    return quote, kline, "eastmoney"


def from_tdx_local():
    if not TDX_PATH.exists():
        return None, None, "no_tdx"
    import struct
    raw = TDX_PATH.read_bytes()
    rec = 32
    closes = []
    for off in range(0, len(raw) - rec + 1, rec):
        try:
            _, _, _, close_i, _, _, _, _ = struct.unpack("<IIIIIfII", raw[off:off+rec])
            closes.append(close_i / 100.0)
        except Exception:
            continue
    if not closes:
        return None, None, "tdx_no_data"
    last = closes[-1]
    return {"f43": int(last * 100), "f170": 0, "f44": 0, "f45": 0, "f47": 0, "f48": 0, "f162": 0, "f116": 0}, ["1,1,1,1," + ",".join(str(c) for c in closes[-60:])], "tdx_local"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    src = "eastmoney"
    quote, kline = {}, []
    try:
        quote, kline, src = from_eastmoney()
    except Exception:
        fb_q, fb_k, fb_src = from_tdx_local()
        if fb_q is not None:
            quote, kline, src = fb_q, fb_k, fb_src
    if quote or kline:
        closes = []
        for l in (kline or []):
            parts = l.split(",")
            if len(parts) >= 5:
                try:
                    closes.append(float(parts[2]))
                except Exception:
                    continue

        def ma(d, p):
            return round(sum(d[-p:]) / min(p, len(d[-p:])), 2) if d else 0
        last = quote.get("f43", 0) / 100 if quote.get("f43") else (closes[-1] if closes else 0)
        report = {
            "skill": "stock-analysis", "name_cn": "\u4e2a\u80a1\u5206\u6790",
            "generated_at": datetime.now().astimezone().isoformat(),
            "data_source": src,
            "symbol": "600519.SH", "name": "\u8d35\u5dde\u8305\u53f0",
            "quote": {
                "price": last,
                "change_pct": quote.get("f170", 0) / 100,
                "high": quote.get("f44", 0) / 100,
                "low": quote.get("f45", 0) / 100,
                "volume": quote.get("f47", 0),
                "amount": quote.get("f48", 0),
                "pe": quote.get("f162", 0) / 100,
                "market_cap": quote.get("f116", 0),
            },
            "technical": {
                "ma5": ma(closes, 5), "ma10": ma(closes, 10), "ma20": ma(closes, 20), "ma60": ma(closes, 60),
                "kline_count": len(closes),
                "last_close": closes[-1] if closes else 0,
            },
            "five_dimensions": {
                "trend": "UP" if last > ma(closes, 20) else "DOWN",
                "volume": "RISING" if quote.get("f47", 0) > 0 else "NORMAL",
                "momentum": quote.get("f170", 0),
                "valuation": quote.get("f162", 0) / 100,
                "liquidity": quote.get("f48", 0),
            },
            "status": "PASS",
        }
    else:
        report = {"skill": "stock-analysis", "status": "FALLBACK", "error": "no data source available"}
    p = OUTPUT_DIR / "stock_analysis_report.json"
    p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report.get("status"), "symbol": report.get("symbol"), "price": report.get("quote", {}).get("price"), "data_source": report.get("data_source"), "json_path": str(p)}, ensure_ascii=False))
    return 0


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
