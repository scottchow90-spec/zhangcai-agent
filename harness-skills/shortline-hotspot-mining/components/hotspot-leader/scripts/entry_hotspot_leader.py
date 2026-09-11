# -*- coding: utf-8 -*-
"""hotspot-leader AKShare版入口：热点龙头分析"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path
import akshare as ak
WORKSPACE = Path(__file__).resolve().parent.parent.parent.parent
def main():
    parser = argparse.ArgumentParser(description="热点龙头 AKShare 执行入口")
    parser.add_argument("--date", default=datetime.date.today().strftime("%Y%m%d"))
    parser.add_argument("--out-dir", default="")
    args = parser.parse_args()
    if not re.fullmatch(r"20\d{6}", args.date):
        print(json.dumps({"status": "BLOCKED", "reason": "--date must be YYYYMMDD"}, ensure_ascii=False))
        return 2
    run_id = os.environ.get(
        "SKILL_FULLFLOW_RUN_ID",
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
    )
    output_dir = Path(args.out_dir).resolve() if args.out_dir else WORKSPACE / "reports" / run_id / "hotspot-leader"
    output_dir.mkdir(parents=True, exist_ok=True)
    td = args.date
    try:
        df = ak.stock_zt_pool_em(date=td)
    except Exception as exc:
        print(json.dumps({
            "status": "BLOCKED",
            "trade_date": td,
            "reason": f"{type(exc).__name__}: {exc}",
        }, ensure_ascii=False))
        return 2
    zt_list = df.to_dict(orient="records")
    sectors = {}
    for s in zt_list:
        hy = s.get("所属行业","未知")
        sectors[hy] = sectors.get(hy, {"count":0,"stocks":[]})
        sectors[hy]["count"] += 1
        sectors[hy]["stocks"].append(s.get("名称","?"))
    top = sorted(sectors.items(), key=lambda x: x[1]["count"], reverse=True)[:10]
    report = {"skill":"hotspot-leader","name_cn":"热点龙头分析","generated_at":datetime.datetime.now().astimezone().isoformat(),"trade_date":td,"data_source":"AKShare","total_zt":len(zt_list),"top_sectors":[{"sector":k,"count":v["count"],"stocks":v["stocks"][:5]} for k,v in top],"status":"PASS" if zt_list else "NO_DATA"}
    p = output_dir / "hotspot_leader_report.json"
    p.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":report["status"],"zt":len(zt_list),"top_sectors":len(top),"json_path":str(p),"json_size":p.stat().st_size},ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 2
if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__=="__main__": raise SystemExit(main())
