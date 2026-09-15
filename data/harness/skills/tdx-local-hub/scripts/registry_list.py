#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出 tdx hub 的所有公式（含 GBK 修复后中文名）"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import json, subprocess
r = subprocess.run(["python","skills/tdx-local-hub/scripts/tdx_hub.py","registry"],
                   cwd=r"D:\C盘转移\日志\codex",
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
d = json.loads(r.stdout)
for f in d["formulas"]:
    # 尝试 GBK 解码 (registry 来源是 GBK 文本)
    name_raw = f.get("name","")
    name_gbk = ""
    try:
        name_gbk = name_raw.encode("latin-1").decode("gbk")
    except Exception:
        name_gbk = name_raw
    print(f"{f.get('kind','?'):>2}  {name_gbk:<24} (raw={name_raw!r})  core={f.get('core','?')}  size={f.get('size','?')}")
