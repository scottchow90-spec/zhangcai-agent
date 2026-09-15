#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TDX 涨停池主源硬闸。

用于每日涨停板深度复盘：先确认通达信本地自定义板块“涨停池”存在、映射到 ZTC，
再读取 ZTC.blk 作为今日涨停名单主源。AK/东财只能做字段补全和差异校验，不能替代主源。
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEFAULT_TDX_ROOT = Path(r"C:\new_tdx_mock")


def read_text(path: Path) -> str:
    return path.read_text(encoding="gbk", errors="replace")


def validate(tdx_root: Path) -> dict:
    block_dir = tdx_root / "T0002" / "blocknew"
    cfg = block_dir / "blocknew.cfg"
    blk = block_dir / "ZTC.blk"
    blocks: list[str] = []
    warnings: list[str] = []

    if not cfg.exists():
        blocks.append(f"blocknew.cfg missing: {cfg}")
        cfg_text = ""
    else:
        cfg_text = read_text(cfg)
        if "涨停池" not in cfg_text or "ZTC" not in cfg_text:
            blocks.append("blocknew.cfg does not map Chinese board name 涨停池 to code ZTC")
        else:
            idx_cn = cfg_text.find("涨停池")
            idx_id = cfg_text.find("ZTC", max(0, idx_cn - 200))
            if idx_cn >= 0 and idx_id >= 0 and abs(idx_id - idx_cn) > 300:
                warnings.append("涨停池 and ZTC both exist but are far apart in blocknew.cfg; verify mapping manually")

    if not blk.exists():
        blocks.append(f"ZTC.blk missing: {blk}")
        raw_lines = []
    else:
        raw_lines = [x.strip() for x in blk.read_text(encoding="gbk", errors="replace").splitlines() if x.strip()]
        if not raw_lines:
            blocks.append(f"ZTC.blk is empty: {blk}")

    invalid = [x for x in raw_lines if not re.fullmatch(r"[012]\d{6}", x)]
    if invalid:
        blocks.append(f"invalid ZTC raw code rows: {invalid[:10]}")

    codes = []
    markets = {"0": "SZ", "1": "SH", "2": "BJ"}
    for row in raw_lines:
        if re.fullmatch(r"[012]\d{6}", row):
            codes.append({"raw": row, "market": markets[row[0]], "code": row[-6:]})
    dupes = sorted({x["code"] for x in codes if [y["code"] for y in codes].count(x["code"]) > 1})
    if dupes:
        warnings.append(f"duplicate codes in ZTC.blk: {dupes[:20]}")

    status = "CLEAN_PASS" if not blocks else "BLOCKED"
    return {
        "status": status,
        "tdx_root": str(tdx_root),
        "blocknew_cfg": str(cfg),
        "ztc_blk": str(blk),
        "ztc_count": len(codes),
        "sample": codes[:10],
        "blocks": blocks,
        "warnings": warnings,
        "rule": "TDX ZTC.blk is the primary source for limit-up review stock list; AK/Eastmoney only supplements fields and differences.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tdx-root", default=str(DEFAULT_TDX_ROOT))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = validate(Path(args.tdx_root))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"])
        print(f"ZTC count: {result['ztc_count']}")
    return 0 if result["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
