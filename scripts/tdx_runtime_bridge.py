#!/usr/bin/env python3
"""Read-only bridge for a running Tongdaxin client and its public data feeds."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("ZHANGCAI_TDX_ROOT", r"C:\new_tdx_mock"))
USER = ROOT / "PYPlugins" / "user"
OUT = Path(os.environ.get("ZHANGCAI_DATA_DIR", Path(__file__).resolve().parents[1] / "data")) / "runtime"
FORMULAS = ["大牛线4.0", "飞龙在天", "游资资金监控", "机构资金监控", "庄家资金监控"]

def process_rows():
    completed = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Process TdxW,tdxcef -ErrorAction SilentlyContinue | Select Name,Id,StartTime,Path | ConvertTo-Json -Compress"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    try:
        rows = json.loads(completed.stdout or "[]")
        return rows if isinstance(rows, list) else [rows]
    except json.JSONDecodeError:
        return []

def latest(paths):
    rows = [p for p in paths if p.exists()]
    if not rows: return None
    p = max(rows, key=lambda x: x.stat().st_mtime)
    return {"path": str(p), "updatedAt": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"), "size": p.stat().st_size}

def status():
    cache = ROOT / "T0002" / "hq_cache"
    day = ROOT / "vipdoc" / "sh" / "lday" / "sh000001.day"
    return {"generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"), "tdxRoot": str(ROOT), "processes": process_rows(), "formulaRegistry": {"directory": str(ROOT / "T0002" / "gs_bak"), "formulaFiles": [p.name for p in (ROOT / "T0002" / "gs_bak").glob("*.txt")]}, "freshness": {"indexDay": latest([day]), "marketCache": latest([cache / "sh.tnf", cache / "sz.tnf", cache / "bj.tnf", cache / "tdxhy.cfg", cache / "infoharbor_block.dat"]), "blockPools": latest([ROOT / "T0002" / "blocknew" / "ZTC.blk", ROOT / "T0002" / "blocknew" / "FLZT.blk"]), "intradayAvailable": any((ROOT / "vipdoc" / market / "fzline").glob("*.lc5") for market in ("sh", "sz", "bj"))}, "tq": {"tqcenter": str(USER / "tqcenter.py"), "strategyConfig": (ROOT / "PYPlugins" / "py_strategy.cfg").read_text(encoding="utf-8", errors="replace") if (ROOT / "PYPlugins" / "py_strategy.cfg").exists() else "", "formulas": FORMULAS}}

def quote(symbol):
    sys.path.insert(0, str(USER)); os.chdir(ROOT)
    from tqcenter import tq
    tq.initialize(str(USER / "tdxdata_test.py"))
    data = tq.get_market_data(stock_list=[symbol], period="1m", count=1)
    row = {"symbol": symbol, "fetchedAt": datetime.now().astimezone().isoformat(timespec="seconds"), "source": "Tongdaxin TQ 1m"}
    for key, value in data.items():
        try:
            series = value[symbol] if hasattr(value, "__getitem__") else None
            latest_value = series.iloc[-1] if hasattr(series, "iloc") else None
            row[key.lower()] = float(latest_value) if latest_value is not None else None
        except Exception: pass
    tq.close()
    return row

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["status", "quote"])
    parser.add_argument("--symbol")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "quote" and not args.symbol: parser.error("quote requires --symbol")
    payload = quote(args.symbol) if args.command == "quote" else status()
    if args.output:
        output = args.output
    elif args.command == "status":
        output = OUT / "tdx-runtime-status.json"
    else:
        # 行情查询保留为独立快照，不能覆盖客户端连接状态。
        stamp = datetime.now().strftime("%Y%m%d/%H%M%S")
        output = OUT / "quotes" / stamp.split("/")[0] / f"{args.symbol.replace('.', '_')}-{stamp.split('/')[1]}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))

if __name__ == "__main__": main()
