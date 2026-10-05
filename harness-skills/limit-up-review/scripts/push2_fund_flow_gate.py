#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate resolved push2delay fund-flow output for limit-up review."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import argparse, json, sys
from pathlib import Path
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REQUIRED_COLS = ["代码", "名称", "ok", "source", "url", "日期", "主力净流入", "超大单净流入", "主力净占比"]


def validate(path: Path, expected_count: int | None) -> dict:
    blocks=[]
    if not path.exists():
        return {"status":"BLOCKED", "blocks":[f"missing push2 fund-flow csv: {path}"], "path":str(path)}
    df=pd.read_csv(path, dtype={"代码":str})
    missing=[c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        blocks.append(f"missing columns: {missing}")
    if expected_count is not None and len(df)!=expected_count:
        blocks.append(f"row count {len(df)} != expected {expected_count}")
    if "ok" in df.columns:
        ok=df["ok"].astype(str).str.lower().isin(["true","1","yes"])
        if not ok.all():
            bad=df.loc[~ok, [c for c in ["代码","名称","source"] if c in df.columns]].to_dict("records")
            blocks.append(f"push2 unresolved rows: {bad[:20]}")
    if "url" in df.columns:
        bad_url=df[~df["url"].astype(str).str.contains("push2delay.eastmoney.com/api/qt/stock/fflow/daykline/get", na=False)]
        if len(bad_url):
            blocks.append(f"non-push2delay daykline rows: {bad_url[[c for c in ['代码','名称','url'] if c in df.columns]].head(20).to_dict('records')}")
    status="CLEAN_PASS" if not blocks else "BLOCKED"
    return {"status":status,"path":str(path),"rows":len(df),"ok_rows":int(df["ok"].astype(str).str.lower().isin(["true","1","yes"]).sum()) if "ok" in df.columns else 0,"blocks":blocks}


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--expected-count", type=int)
    ap.add_argument("--json", action="store_true")
    args=ap.parse_args()
    res=validate(Path(args.csv), args.expected_count)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(res["status"])
    return 0 if res["status"]=="CLEAN_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
