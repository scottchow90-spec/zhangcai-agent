#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""烟雾测试：5 只股票 + 主升启动 + 波<25 过滤逻辑"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import os, sys, json
from pathlib import Path
TDX_ROOT = Path(r"C:\new_tdx_mock")
TQ_INIT = TDX_ROOT / "PYPlugins" / "user" / "tdxdata_test.py"
os.chdir(str(TDX_ROOT))
sys.path.insert(0, str(TDX_ROOT / "PYPlugins" / "user"))
from tqcenter import tq
tq.initialize(str(TQ_INIT))
batch = ["002771.SZ", "000001.SZ", "600519.SH", "300750.SZ", "601318.SH"]
r = tq.formula_process_mul_zb("飞龙在天", stock_list=batch, count=0, return_count=2, return_date=False, dividend_type=1)
print("ErrorId:", r.get("ErrorId"))
for sym in batch:
    node = r.get(sym, {})
    print(f"\n=== {sym} ===")
    for k, v in node.items():
        if isinstance(v, list):
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: {v!r}")
tq.close()
