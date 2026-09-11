#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elliott Wave dashboard for SH 000001 - robust multi-source.
Tries: eastmoney kline -> eastmoney push2his alt -> sina -> tdx local
"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import json, sys, urllib.request, urllib.error, time, struct, os
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent.parent.parent
RUN_ID = os.environ.get("SKILL_FULLFLOW_RUN_ID", "2026-06-12_skill_fullflow_all")
OUT_DIR = WORKSPACE / "reports" / RUN_ID / "support-resistance-analysis"
TDX_PATH = Path(r"C:\new_tdx_mock\vipdoc\sh\lday\sh000001.day")

URLS = [
    # eastmoney primary
    "https://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&secid=1.000001&end=20500101&lmt=60",
    # eastmoney backup host
    "https://44.push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&secid=1.000001&end=20500101&lmt=60",
    # sina
    "https://quotes.sina.cn/cn/api/json_v2.php=/CN_MarketDataService.getKLineData?symbol=sh000001&scale=240&ma=no&datalen=60",
]

def fetch_url(url, timeout=10):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://quote.eastmoney.com/",
        "Accept": "*/*",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", errors="ignore")
    return body

def from_eastmoney_attempts():
    last_err = None
    for attempt in range(4):
        for url in URLS[:2]:
            try:
                body = fetch_url(url, timeout=10)
                d = json.loads(body)
                k = d.get("data", {}).get("klines", [])
                if k:
                    return k, f"eastmoney@{url[:35]}... attempt={attempt+1}"
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
        time.sleep(2 + attempt)
    return [], last_err or "eastmoney_failed"

def from_sina():
    try:
        body = fetch_url(URLS[2], timeout=10)
        d = json.loads(body)
        out = []
        for row in d:
            out.append(f"{row['day']},{row['open']},{row['close']},{row['high']},{row['low']},{row.get('volume',0)},0")
        return out, "sina"
    except Exception as e:
        return [], f"sina:{type(e).__name__}: {e}"

def from_tdx(limit=60):
    if not TDX_PATH.exists():
        return [], "no_tdx"
    raw = TDX_PATH.read_bytes()
    rec = 32
    out = []
    for off in range(0, len(raw) - rec + 1, rec):
        try:
            date_i, open_i, high_i, low_i, close_i, _, _, _ = struct.unpack("<IIIIIfII", raw[off:off+rec])
            d = str(date_i)
            if len(d) != 8:
                continue
            out.append(f"{d[:4]}-{d[4:6]}-{d[6:8]},{open_i/100.0},{close_i/100.0},{high_i/100.0},{low_i/100.0},0,0")
        except Exception:
            continue
    return out[-limit:], "tdx_local"

def parse(lines):
    rows = []
    for line in lines:
        p = line.split(",")
        if len(p) < 5:
            continue
        try:
            rows.append({
                "date": p[0],
                "open": float(p[1]),
                "close": float(p[2]),
                "high": float(p[3]),
                "low":  float(p[4]),
                "vol":  float(p[5]) if len(p) > 5 else 0.0,
                "amp":  float(p[6]) if len(p) > 6 else 0.0,
            })
        except Exception:
            continue
    return rows

def find_swings(rows, lookback=2):
    highs, lows = [], []
    n = len(rows)
    for i in range(lookback, n - lookback):
        h, l = rows[i]["high"], rows[i]["low"]
        if all(h > rows[j]["high"] for j in range(i-lookback, i+lookback+1) if j != i):
            highs.append(i)
        if all(l < rows[j]["low"]  for j in range(i-lookback, i+lookback+1) if j != i):
            lows.append(i)
    return highs, lows

def main():
    sources_tried = []
    klines, src = from_eastmoney_attempts()
    sources_tried.append(("eastmoney", src if not klines else "ok"))
    if not klines:
        klines, src2 = from_sina()
        sources_tried.append(("sina", src2 if not klines else "ok"))
        if not klines:
            klines, src3 = from_tdx()
            sources_tried.append(("tdx", src3 if not klines else "ok"))
    if not klines:
        print(json.dumps({"status": "NO_DATA", "tried": sources_tried}, ensure_ascii=False))
        return 1
    rows = parse(klines)
    last = rows[-1]
    hi_idx, lo_idx = find_swings(rows, lookback=2)
    swings = []
    for i in hi_idx:
        swings.append({"idx": i, "type": "H", "date": rows[i]["date"], "price": rows[i]["high"]})
    for i in lo_idx:
        swings.append({"idx": i, "type": "L", "date": rows[i]["date"], "price": rows[i]["low"]})
    swings.sort(key=lambda x: x["idx"])
    out = {
        "skill": "elliott_wave_dashboard",
        "generated_at": datetime.now().astimezone().isoformat(),
        "symbol": "000001.SH",
        "name": "上证指数",
        "data_source": src,
        "sources_tried": sources_tried,
        "kline_count": len(rows),
        "first_date": rows[0]["date"],
        "last_date": rows[-1]["date"],
        "last_close": last["close"],
        "last_open": last["open"],
        "last_high":  last["high"],
        "last_low":   last["low"],
        "all_rows": rows,
        "swings": swings,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / "elliott_wave_dashboard.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "data_source": src,
        "sources_tried": sources_tried,
        "kline_count": len(rows),
        "first_date": rows[0]["date"],
        "last_date": rows[-1]["date"],
        "last_close": last["close"],
        "swing_highs": len(hi_idx),
        "swing_lows": len(lo_idx),
        "json_path": str(p),
    }, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
