from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import json, re, time, math, os
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd
import akshare as ak

TASK_DIR = Path(os.environ.get("LIMITUP_TASK_DIR", r"D:\C盘转移\日志\codex\reports\2026-06-02_limit_up_review_word"))
TASK_DIR.mkdir(parents=True, exist_ok=True)
DATE = os.environ.get("LIMITUP_DATE", datetime.now().strftime("%Y%m%d"))
DATE_H = os.environ.get("LIMITUP_DATE_H", datetime.now().strftime("%Y-%m-%d"))
UA = {"User-Agent":"Mozilla/5.0", "Referer":"https://quote.eastmoney.com/"}
DATE_TAG = DATE


def save_df(df: pd.DataFrame, name: str):
    p_csv = TASK_DIR / f"{name}.csv"
    p_json = TASK_DIR / f"{name}.json"
    df.to_csv(p_csv, index=False, encoding="utf-8-sig")
    df.to_json(p_json, orient="records", force_ascii=False, indent=2)
    return str(p_csv)


def safe_fetch(label, fn, *args, **kwargs):
    try:
        df = fn(*args, **kwargs)
        save_df(df, label)
        return {"ok": True, "label": label, "rows": len(df), "columns": list(df.columns)}, df
    except Exception as e:
        return {"ok": False, "label": label, "error": f"{type(e).__name__}: {str(e)[:500]}"}, pd.DataFrame()


def em_get_json(url, params, retries=4, sleep=1.2):
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=20, headers=UA)
            r.raise_for_status()
            return r.json(), r.url
        except Exception as e:
            last = e
            time.sleep(sleep * (i + 1))
    raise last


def fetch_em_all_market():
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    fields = "f12,f14,f2,f3,f4,f5,f6,f15,f16,f17,f18,f8,f20,f21"
    fs = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"
    first_params = {"pn":1,"pz":100,"po":1,"np":1,"ut":"bd1d9ddb04089700cf9c27f6f7426281","fltt":2,"invt":2,"fid":"f3","fs":fs,"fields":fields}
    data, used_url = em_get_json(url, first_params)
    total = int(data.get("data", {}).get("total") or 0)
    rows = data.get("data", {}).get("diff", []) or []
    pages = math.ceil(total / 100)
    for pn in range(2, pages + 1):
        params = dict(first_params); params["pn"] = pn
        d, _ = em_get_json(url, params, retries=3, sleep=0.6)
        rows.extend(d.get("data", {}).get("diff", []) or [])
    out = []
    for x in rows:
        out.append({
            "代码": str(x.get("f12", "")).zfill(6),
            "名称": x.get("f14"),
            "最新价": x.get("f2"),
            "涨跌幅": x.get("f3"),
            "涨跌额": x.get("f4"),
            "成交量": x.get("f5"),
            "成交额": x.get("f6"),
            "最高": x.get("f15"),
            "最低": x.get("f16"),
            "今开": x.get("f17"),
            "昨收": x.get("f18"),
            "换手率": x.get("f8"),
            "总市值": x.get("f20"),
            "流通市值": x.get("f21"),
        })
    df = pd.DataFrame(out).drop_duplicates(subset=["代码"])
    return df, {"total_reported": total, "rows": len(df), "url": used_url}


def fetch_em_indices():
    url='https://push2.eastmoney.com/api/qt/ulist.np/get'
    params={'fltt':'2','invt':'2','fields':'f12,f14,f2,f3,f4','secids':'1.000001,0.399001,0.399006,1.000688'}
    data, used_url = em_get_json(url, params)
    rows = data.get('data',{}).get('diff',[]) or []
    return rows, used_url, data

status=[]
st, zt = safe_fetch(f"ak_stock_zt_pool_em_{DATE_TAG}", ak.stock_zt_pool_em, date=DATE); status.append(st)
st, zbgc = safe_fetch(f"ak_stock_zt_pool_zbgc_em_{DATE_TAG}", ak.stock_zt_pool_zbgc_em, date=DATE); status.append(st)
st, dtgc = safe_fetch(f"ak_stock_zt_pool_dtgc_em_{DATE_TAG}", ak.stock_zt_pool_dtgc_em, date=DATE); status.append(st)
st, strong = safe_fetch(f"ak_stock_zt_pool_strong_em_{DATE_TAG}", ak.stock_zt_pool_strong_em, date=DATE); status.append(st)
st, lhb_em = safe_fetch(f"ak_stock_lhb_detail_em_{DATE_TAG}", ak.stock_lhb_detail_em, start_date=DATE, end_date=DATE); status.append(st)
# Sina as degraded optional
st, lhb_sina = safe_fetch(f"ak_stock_lhb_detail_daily_sina_{DATE_TAG}", ak.stock_lhb_detail_daily_sina, date=DATE_H); status.append(st)

try:
    em_all, em_meta = fetch_em_all_market()
    save_df(em_all, f"eastmoney_all_market_spot_{DATE_TAG}")
    status.append({"ok": True, "label": "eastmoney_all_market_spot", **em_meta})
except Exception as e:
    em_all = pd.DataFrame()
    status.append({"ok": False, "label": "eastmoney_all_market_spot", "error": f"{type(e).__name__}: {str(e)[:500]}"})

try:
    index_rows, index_url, index_raw = fetch_em_indices()
    (TASK_DIR / f"eastmoney_index_ulist_{DATE_TAG}.json").write_text(json.dumps(index_raw, ensure_ascii=False, indent=2), encoding="utf-8")
    status.append({"ok": True, "label": "eastmoney_index_ulist", "rows": len(index_rows), "url": index_url})
except Exception as e:
    index_rows = []
    status.append({"ok": False, "label": "eastmoney_index_ulist", "error": f"{type(e).__name__}: {str(e)[:500]}"})


def code6(x):
    s=str(x).strip(); m=re.search(r"(\d{6})", s); return m.group(1) if m else s

def is_st(name):
    n=str(name or "").upper()
    return n.startswith("ST") or n.startswith("*ST") or "ST" in n[:5]

def threshold_by_code_name(code, name):
    c=code6(code)
    if is_st(name): return 4.8
    if c.startswith(("43","83","87","88","92")): return 29.5
    if c.startswith(("300","301","688")): return 19.5
    return 9.75


def load_tdx_stock_name_index():
    p = Path(r'C:\new_tdx_mock\T0002\hq_cache\infoharbor_ex.code')
    if not p.exists():
        return {}
    try:
        text = p.read_bytes().decode('gbk', errors='ignore')
        out = {}
        for line in text.split('\r\n'):
            line = line.strip()
            if not line or '|' not in line:
                continue
            parts = line.split('|')
            if len(parts) >= 2 and len(parts[0]) == 6 and parts[0].isdigit() and parts[1].strip():
                out[parts[0]] = parts[1].strip()
        return out
    except Exception:
        return {}


def read_local_blk_codes(filename):
    p = Path(r'C:\new_tdx_mock\T0002\blocknew') / filename
    if not p.exists():
        return []
    text = p.read_text(encoding='gbk', errors='ignore')
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.search(r'(\d{6})$', line)
        if m:
            out.append(m.group(1))
    return out

def read_tdx_block_items(filename):
    p = Path(r'C:\new_tdx_mock\T0002\blocknew') / filename
    if not p.exists():
        return []
    items = []
    for order, line in enumerate(p.read_text(encoding='gbk', errors='ignore').splitlines(), start=1):
        raw = line.strip()
        m = re.search(r'(\d{6})$', raw)
        if not m:
            continue
        prefix = raw[0] if raw else ''
        market = {'0': 'SZ', '1': 'SH', '2': 'BJ'}.get(prefix, '')
        items.append({'order': order, 'raw': raw, 'code': m.group(1), 'market': market})
    return items

name_index = load_tdx_stock_name_index()
records={}
if not zt.empty:
    for _,r in zt.iterrows():
        c=code6(r.get("代码")); rec=r.to_dict(); rec["代码"]=c; rec["来源"]="akshare.stock_zt_pool_em"; rec["全市场阈值反查"]="未命中"; records[c]=rec

threshold_hits=[]
if not em_all.empty:
    for _,r in em_all.iterrows():
        try: pct=float(r.get("涨跌幅"))
        except Exception: continue
        c=code6(r.get("代码")); name=r.get("名称"); th=threshold_by_code_name(c,name)
        # closed near daily limit: current price equals high and pct reaches board threshold
        try:
            latest=float(r.get("最新价")); high=float(r.get("最高"))
            closed_high = abs(latest-high) < 1e-6
        except Exception:
            closed_high = True
        if pct >= th and closed_high:
            hit={"代码":c,"名称":name,"涨跌幅":pct,"最新价":r.get("最新价"),"最高":r.get("最高"),"成交额":r.get("成交额"),"换手率":r.get("换手率"),"阈值":th}
            threshold_hits.append(hit)
            if c in records:
                records[c]["全市场阈值反查"]="命中"
                records[c]["全市场涨跌幅"]=pct
            else:
                records[c]={"清单序号":None,"代码":c,"名称":name,"涨跌幅":pct,"最新价":r.get("最新价"),"成交额":r.get("成交额"),"流通市值":r.get("流通市值"),"总市值":r.get("总市值"),"换手率":r.get("换手率"),"封板资金":None,"首次封板时间":None,"最后封板时间":None,"炸板次数":None,"涨停统计":None,"连板数":None,"所属行业":None,"来源":"eastmoney_all_market_threshold","全市场阈值反查":"新增","阈值":th}

threshold_df=pd.DataFrame(threshold_hits); save_df(threshold_df,f"full_market_threshold_limit_hits_{DATE_TAG}")

em_by_code = {}
if not em_all.empty and "代码" in em_all.columns:
    for _, r in em_all.iterrows():
        em_by_code[code6(r.get("代码"))] = r.to_dict()

for item in read_tdx_block_items('ZTC.blk'):
    c = item['code']
    em = em_by_code.get(c, {})
    if c in records:
        src = str(records[c].get('来源', ''))
        if 'TDX_ZTC' not in src:
            records[c]['来源'] = (src + '+TDX_ZTC').strip('+')
        records[c]['市场'] = item['market']
        records[c]['TDX_ZTC顺序'] = item['order']
        records[c]['TDX_ZTC原始行'] = item['raw']
        continue
    records[c] = {
        '清单序号': None,
        '代码': c,
        '名称': em.get('名称') or name_index.get(c, c),
        '市场': item['market'],
        '涨跌幅': em.get('涨跌幅'),
        '最新价': em.get('最新价'),
        '成交额': em.get('成交额'),
        '流通市值': em.get('流通市值'),
        '总市值': em.get('总市值'),
        '换手率': em.get('换手率'),
        '封板资金': None,
        '首次封板时间': None,
        '最后封板时间': None,
        '炸板次数': None,
        '涨停统计': None,
        '连板数': None,
        '所属行业': None,
        '来源': 'TDX_ZTC',
        '全市场阈值反查': 'TDX本地涨停池',
        '阈值': None,
        'TDX_ZTC顺序': item['order'],
        'TDX_ZTC原始行': item['raw'],
    }

# 用户纠错优先：本地 JDN_LB2 是 2板权威口径
lb2_codes = read_local_blk_codes('JDN_LB2.blk')
lb2_source = 'TDX_JDN_LB2'
if not lb2_codes:
    lb2_codes = read_local_blk_codes('ELB.blk')
    lb2_source = 'TDX_ELB'
for c in lb2_codes:
    if c in records:
        try:
            cur_i = int(float(records[c].get('连板数') or 0))
        except Exception:
            cur_i = 0
        if cur_i < 2:
            records[c]['连板数'] = 2
        src = str(records[c].get('来源', ''))
        if lb2_source not in src:
            records[c]['来源'] = (src + '+' + lb2_source).strip('+')
    else:
        records[c] = {
            '清单序号': None, '代码': c, '名称': name_index.get(c, c), '涨跌幅': None, '最新价': None,
            '成交额': None, '流通市值': None, '总市值': None, '换手率': None, '封板资金': None,
            '首次封板时间': None, '最后封板时间': None, '炸板次数': None, '涨停统计': None,
            '连板数': 2, '所属行业': None, '来源': lb2_source, '全市场阈值反查': '本地连板池补充', '阈值': None,
        }

limitups=pd.DataFrame(list(records.values()))
if not limitups.empty:
    def srt(row):
        try: lb=int(row.get("连板数") or 1)
        except Exception: lb=1
        fst=str(row.get("首次封板时间") or "999999")
        return (-lb, fst, str(row.get("代码")))
    limitups=limitups.loc[sorted(limitups.index,key=lambda i:srt(limitups.loc[i]))].reset_index(drop=True)
    if "清单序号" in limitups.columns: limitups=limitups.drop(columns=["清单序号"])
    limitups.insert(0,"清单序号",range(1,len(limitups)+1))
save_df(limitups,f"verified_limitup_union_{DATE_TAG}")

lhb_codes=set()
if not lhb_em.empty and "代码" in lhb_em.columns: lhb_codes |= {code6(x) for x in lhb_em["代码"].dropna().astype(str)}
if not lhb_sina.empty and "股票代码" in lhb_sina.columns: lhb_codes |= {code6(x) for x in lhb_sina["股票代码"].dropna().astype(str)}
limitup_lhb=limitups[limitups["代码"].astype(str).map(lambda x: code6(x) in lhb_codes)].copy() if not limitups.empty else pd.DataFrame()
save_df(limitup_lhb,f"limitup_lhb_intersection_{DATE_TAG}")

industry=limitups.get("所属行业",pd.Series(dtype=str)).fillna("未分类").replace("","未分类").value_counts().reset_index() if not limitups.empty else pd.DataFrame(columns=["行业","涨停数"])
if not industry.empty: industry.columns=["行业","涨停数"]
save_df(industry,f"industry_limitup_stats_{DATE_TAG}")

lb_counts=limitups.get("连板数",pd.Series(dtype=str)).fillna(1).replace("",1).value_counts().reset_index() if not limitups.empty else pd.DataFrame(columns=["连板数","数量"])
if not lb_counts.empty: lb_counts.columns=["连板数","数量"]
save_df(lb_counts,f"consecutive_board_stats_{DATE_TAG}")

summary={
 "generated_at":datetime.now().isoformat(timespec="seconds"),"date":DATE,"date_h":DATE_H,"status":status,
 "stock_zt_pool_em_count":int(len(zt)),"eastmoney_all_market_count":int(len(em_all)),"threshold_hit_count":int(len(threshold_df)),
 "union_limitup_count":int(len(limitups)),"union_added_by_threshold_count":int((limitups["来源"]=="eastmoney_all_market_threshold").sum()) if not limitups.empty else 0,
 "zbgc_count":int(len(zbgc)),"dtgc_count":int(len(dtgc)),"strong_count":int(len(strong)),"lhb_em_count":int(len(lhb_em)),"lhb_sina_count":int(len(lhb_sina)),"limitup_lhb_count":int(len(limitup_lhb)),"index_rows":index_rows,
 "files":[str(p) for p in sorted(TASK_DIR.glob("*.csv"))]
}
(TASK_DIR/"data_collection_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False,indent=2))
