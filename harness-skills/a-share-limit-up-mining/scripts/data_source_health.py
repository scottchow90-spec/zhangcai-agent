#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import importlib.util
import json
from datetime import datetime
from pathlib import Path

ZTC = Path(r"C:\new_tdx_mock\T0002\blocknew\ZTC.blk")
TDX_DAY_DIRS = (Path(r"C:\new_tdx_mock\vipdoc\sh\lday"), Path(r"C:\new_tdx_mock\vipdoc\sz\lday"))
DEFAULT_TEMPLATE = Path(r"F:\小龙虾6月交付\6月1日连板挖掘5标的.docx")


def file_fact(path: Path) -> dict:
    return {
        "path": str(path),
        "exists": path.is_file(),
        "size": path.stat().st_size if path.is_file() else 0,
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds") if path.is_file() else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="连板挖掘数据源前置健康检查")
    parser.add_argument("action", choices=("recommend", "check"), nargs="?", default="recommend")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    args = parser.parse_args()
    facts = {
        "ztc": file_fact(ZTC),
        "tdx_day_dirs": [{"path": str(path), "exists": path.is_dir()} for path in TDX_DAY_DIRS],
        "template": file_fact(Path(args.template).expanduser()),
        "python_modules": {
            name: importlib.util.find_spec(name) is not None for name in ("akshare", "docx", "pandas")
        },
    }
    local_present = facts["ztc"]["exists"] and all(item["exists"] for item in facts["tdx_day_dirs"])
    payload = {
        "status": "PASS",
        "scope": "preflight_only",
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "local_market_files_present": local_present,
        "local_freshness_verified_for_trade_date": False,
        "remote_endpoints_verified": False,
        "formal_run_ready": False,
        "reason": "远程接口必须在目标交易日由正式采集器真实返回后才能标记成功；可导入不等于接口成功。",
        "recommended_order": ["TDX ZTC", "TDX day files", "same-date limit-up endpoint", "same-date LHB", "stock-bound research", "stock-bound news"],
        "facts": facts,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
