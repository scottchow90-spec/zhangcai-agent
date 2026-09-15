from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import json, time, re, os
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd

TASK = Path(os.environ.get("LIMITUP_TASK_DIR", r"D:\C盘转移\日志\codex\reports\2026-06-02_limit_up_review_word"))
TABLE = Path(os.environ.get("LIMITUP_TABLE", str(Path.home() / ".codex" / "business_data" / "limit-up-review" / "2026-06-02-limit-up-table.csv")))
DATE_H = os.environ.get("LIMITUP_DATE_H", datetime.now().strftime("%Y-%m-%d"))
DATE = os.environ.get("LIMITUP_DATE", datetime.now().strftime("%Y%m%d"))
UA = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Referer":"https://quote.eastmoney.com/",
    "Accept":"application/json,text/plain,*/*",
    "Connection":"close",
}
DAY_URL = "https://push2delay.eastmoney.com/api/qt/stock/fflow/daykline/get"
DAY_HIS_URL = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
GET_URL = "https://push2delay.eastmoney.com/api/qt/stock/get"


def code6(x):
    s=str(x).strip(); m=re.search(r"(\d{6})",s); return m.group(1) if m else s.zfill(6)

def secid_for(code, market):
    c=code6(code)
    return "1."+c if str(market).upper()=="SH" or c.startswith("6") else "0."+c

def req_json(url, params, timeout=8):
    r=requests.get(url, params=params, headers=UA, timeout=timeout)
    r.raise_for_status()
    return r.json(), r.url

def parse_day(data, used):
    line=data["data"]["klines"][-1]
    p=line.split(",")
    return {"ok":True,"source":"push2_fflow_daykline","url":used,"日期":p[0],"主力净流入":float(p[1]),"小单净流入":float(p[2]),"中单净流入":float(p[3]),"大单净流入":float(p[4]),"超大单净流入":float(p[5]),"主力净占比":float(p[6]),"小单净占比":float(p[7]),"中单净占比":float(p[8]),"大单净占比":float(p[9]),"超大单净占比":float(p[10]),"收盘价":float(p[11]),"涨跌幅":float(p[12])}

def fetch_day(secid):
    params={"secid":secid,"lmt":1,"klt":101,"fields1":"f1,f2,f3,f7","fields2":"f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63"}
    errors=[]
    for url in (DAY_URL, DAY_HIS_URL):
        try:
            data, used=req_json(url, params, timeout=8)
            if data.get("rc")==0 and data.get("data") and data["data"].get("klines"):
                return parse_day(data, used)
            errors.append(f"{url}: rc={data.get('rc')}")
        except Exception as e:
            errors.append(f"{url}: {type(e).__name__}:{str(e)[:120]}")
    return {"ok":False,"source":"push2_fflow_daykline","error":" | ".join(errors)}

def fetch_quote(secid):
    params={"secid":secid,"fields":"f12,f14,f2,f3,f62,f66,f69,f72,f75,f78,f81,f84,f87,f164,f165"}
    try:
        data, used=req_json(GET_URL, params, timeout=8)
        d=data.get("data") if data.get("rc")==0 else None
        if not d:
            return {"ok":False,"source":"push2_stock_get_fund_fields","error":f"rc={data.get('rc')}","url":used}
        return {"ok":True,"source":"push2_stock_get_fund_fields","url":used,"日期":DATE_H,"主力净流入":d.get("f62"),"超大单净流入":d.get("f66"),"超大单净占比":d.get("f69"),"大单净流入":d.get("f72"),"大单净占比":d.get("f75"),"中单净流入":d.get("f78"),"中单净占比":d.get("f81"),"小单净流入":d.get("f84"),"小单净占比":d.get("f87"),"收盘价":d.get("f2"),"涨跌幅":d.get("f3")}
    except Exception as e:
        return {"ok":False,"source":"push2_stock_get_fund_fields","error":f"{type(e).__name__}:{str(e)[:160]}"}

def main():
    df=pd.read_csv(TABLE, dtype={"代码":str})
    rows=[]
    for idx,r in df.iterrows():
        code=code6(r["代码"]); market=str(r.get("市场") or "")
        secid=secid_for(code,market)
        # push2delay 的 daykline fflow 对沪深京均可用；先走日K资金流，失败才退到 quote-level 字段。
        result=fetch_day(secid)
        if not result.get("ok"):
            q=fetch_quote(secid)
            if q.get("ok"):
                q["daykline_error"]=result.get("error")
            result=q if q.get("ok") else result
        out={"代码":code,"名称":r.get("名称"),"市场":market,"secid":secid,**result}
        rows.append(out)
        print(f"{idx+1}/{len(df)} {code} {r.get('名称')} {result.get('source')} ok={result.get('ok')}", flush=True)
        time.sleep(0.08)
    outdf=pd.DataFrame(rows)
    out_csv=TASK/f"push2_fund_flow_resolved_{DATE}.csv"
    out_json=TASK/f"push2_fund_flow_resolved_{DATE}.json"
    outdf.to_csv(out_csv,index=False,encoding="utf-8-sig")
    out_json.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    ok=outdf["ok"].astype(bool)
    fail_cols=[c for c in ["代码","名称","市场","secid","source","error"] if c in outdf.columns]
    failed_codes=outdf.loc[~ok,fail_cols].to_dict("records") if fail_cols else []
    summary={"total":len(outdf),"ok":int(ok.sum()),"failed":int((~ok).sum()),"daykline_ok":int((ok & (outdf["source"]=="push2_fflow_daykline")).sum()),"quote_fallback_ok":int((ok & (outdf["source"]=="push2_stock_get_fund_fields")).sum()),"failed_codes":failed_codes,"csv":str(out_csv),"json":str(out_json)}
    (TASK/f"push2_fund_flow_resolved_summary_{DATE}.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2), flush=True)
    if summary["failed"]:
        raise SystemExit(2)

if __name__=="__main__": main()
