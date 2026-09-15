from __future__ import annotations

import json
import os
import random
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from zoneinfo import ZoneInfo

from engine import exchange_of, is_mainboard

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153 Safari/537.36"


class DataError(RuntimeError):
    pass


def _get_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 12, retries: int = 3) -> Dict[str, Any]:
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    last: Optional[Exception] = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://quote.eastmoney.com/"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            return json.loads(raw.decode("utf-8", errors="replace"))
        except Exception as e:
            last = e
            if i + 1 < retries:
                time.sleep((0.7 * (2 ** i)) + random.random() * 0.4)
    raise DataError(f"HTTP失败: {url} :: {last}")




def _get_text(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 12, retries: int = 3, referer: str = "https://quote.eastmoney.com/") -> str:
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    last: Optional[Exception] = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            last = e
            if i + 1 < retries:
                time.sleep((0.7 * (2 ** i)) + random.random() * 0.4)
    raise DataError(f"HTTP失败: {url} :: {last}")


def eastmoney_universe() -> List[Dict[str, Any]]:
    data = _get_json(
        "https://push2.eastmoney.com/api/qt/clist/get",
        {
            "pn": 1, "pz": 8000, "po": 1, "np": 1, "fltt": 2, "invt": 2, "fid": "f3",
            "fs": "m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f12,f14,f13,f2,f3,f4,f5,f6,f7,f8,f10,f15,f16,f17,f18,f20,f21",
        },
    )
    rows = (((data or {}).get("data") or {}).get("diff") or [])
    out = []
    for x in rows:
        code = str(x.get("f12") or "")
        if len(code) != 6:
            continue
        out.append({
            "code": code,
            "name": str(x.get("f14") or code),
            "market_id": int(x.get("f13") or (1 if code.startswith("6") else 0)),
            "pct": x.get("f3"), "change": x.get("f4"), "volume": x.get("f5"),
            "amount": x.get("f6"),
            "turnover": x.get("f8"), "volume_ratio": x.get("f10"),
            "last": x.get("f2"), "high": x.get("f15"), "low": x.get("f16"), "open": x.get("f17"), "pre_close": x.get("f18"),
        })
    if len(out) < 3000:
        raise DataError(f"股票池返回异常，仅{len(out)}只")
    return out


def _secid(code: str, market_id: Optional[int] = None) -> str:
    if market_id is None:
        market_id = 1 if code.startswith(("5", "6", "9")) else 0
    return f"{market_id}.{code}"


def eastmoney_kline(code: str, end_date: str, count_days: int = 260, market_id: Optional[int] = None) -> List[Dict[str, Any]]:
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    beg = end - timedelta(days=max(30, int(count_days * 2.1) + 20))
    data = _get_json(
        "https://push2his.eastmoney.com/api/qt/stock/kline/get",
        {
            "secid": _secid(code, market_id), "klt": 101, "fqt": 0,
            "beg": beg.strftime("%Y%m%d"), "end": end.strftime("%Y%m%d"),
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        },
    )
    kl = (((data or {}).get("data") or {}).get("klines") or [])
    out: List[Dict[str, Any]] = []
    for line in kl:
        p = str(line).split(",")
        if len(p) < 11:
            continue
        try:
            out.append({
                "date": p[0], "open": float(p[1]), "close": float(p[2]), "high": float(p[3]), "low": float(p[4]),
                "volume": float(p[5]), "amount": float(p[6]), "amplitude": float(p[7]), "pct_change": float(p[8]),
                "change": float(p[9]), "turnover": float(p[10]),
            })
        except ValueError:
            continue
    return out[-count_days:]


def eastmoney_index_kline(secid: str, end_date: str, count_days: int = 80) -> List[Dict[str, Any]]:
    code = secid.split(".", 1)[1]
    market_id = int(secid.split(".", 1)[0])
    return eastmoney_kline(code, end_date, count_days, market_id)


def eastmoney_industry_name(code: str) -> Optional[str]:
    data = _get_json(
        "https://push2.eastmoney.com/api/qt/stock/get",
        {"secid": _secid(code), "fields": "f57,f58,f127,f128,f129"},
    )
    d = (data or {}).get("data") or {}
    v = d.get("f127")
    if v in (None, "-", ""):
        return None
    return str(v).strip()


def eastmoney_industry_boards() -> Dict[str, str]:
    data = _get_json(
        "https://push2.eastmoney.com/api/qt/clist/get",
        {
            "pn": 1, "pz": 1200, "po": 1, "np": 1, "fltt": 2, "invt": 2, "fid": "f3",
            "fs": "m:90+t:2+f:!50", "fields": "f12,f14",
        },
    )
    rows = (((data or {}).get("data") or {}).get("diff") or [])
    return {str(x.get("f14") or "").strip(): str(x.get("f12") or "").strip() for x in rows if x.get("f12") and x.get("f14")}


def eastmoney_board_kline(board_code: str, end_date: str, count_days: int = 30) -> List[Dict[str, Any]]:
    # 行业板块使用市场90。
    return eastmoney_kline(board_code, end_date, count_days, 90)




def eastmoney_board_constituents(board_code: str, page_size: int = 600) -> List[Dict[str, Any]]:
    """行业板块当前成分快照，用于行业内部扩散、资金广度和龙头梯队。
    这是当前时点快照；历史重放仍受PIT门禁限制，禁止把当前成分回填为正式历史。
    """
    data=_get_json(
        "https://push2.eastmoney.com/api/qt/clist/get",
        {
            "pn":1,"pz":page_size,"po":1,"np":1,"fltt":2,"invt":2,"fid":"f3",
            "fs":f"b:{board_code}",
            "fields":"f12,f14,f13,f2,f3,f5,f6,f8,f10,f15,f16,f17,f18",
        },
    )
    rows=(((data or {}).get("data") or {}).get("diff") or [])
    out=[]
    for x in rows:
        code=str(x.get("f12") or "")
        if len(code)!=6: continue
        out.append({
            "code":code,"name":str(x.get("f14") or code),"market_id":x.get("f13"),
            "last":x.get("f2"),"pct":x.get("f3"),"volume":x.get("f5"),"amount":x.get("f6"),
            "turnover":x.get("f8"),"volume_ratio":x.get("f10"),"high":x.get("f15"),"low":x.get("f16"),"open":x.get("f17"),"pre_close":x.get("f18"),
        })
    return out


def eastmoney_news_search(keyword: str, count: int = 30) -> List[Dict[str, Any]]:
    """东方财富公开搜索的新闻证据。只返回原始事实，不在数据层主观评分。"""
    cb="jQuery_workbuddy_news"
    inner=json.dumps({
        "uid":"","keyword":str(keyword),"type":["cmsArticleWebOld"],"client":"web","clientType":"web","clientVersion":"curr",
        "param":{"cmsArticleWebOld":{"searchScope":"default","sort":"default","pageIndex":1,"pageSize":int(count),"preTag":"","postTag":""}},
    },ensure_ascii=False,separators=(',',':'))
    text=_get_text("https://search-api-web.eastmoney.com/search/jsonp",{"cb":cb,"param":inner},referer="https://so.eastmoney.com/")
    l=text.find('('); r=text.rfind(')')
    if l<0 or r<=l: raise DataError("东方财富新闻JSONP解析失败")
    data=json.loads(text[l+1:r])
    block=((data or {}).get("result") or {}).get("cmsArticleWebOld") or {}
    articles=block.get("list") if isinstance(block,dict) else []
    out=[]
    for a in articles or []:
        title=re.sub(r'<[^>]+>','',str(a.get('title') or ''))
        content=re.sub(r'<[^>]+>','',str(a.get('content') or ''))
        out.append({"time":a.get("date"),"title":title,"content":content[:600],"source":a.get("mediaName") or "","url":a.get("url") or ""})
    return out


def tencent_kline(code: str, count: int = 260) -> List[Dict[str, Any]]:
    prefix = "sh" if code.startswith("6") else "sz"
    symbol = prefix + code
    url = "https://web.ifzq.gtimg.cn/appstock/app/kline/kline"
    data = _get_json(url, {"param": f"{symbol},day,,,{count}"})
    d = (((data or {}).get("data") or {}).get(symbol) or {})
    rows = d.get("day") or d.get("qfqday") or []
    out: List[Dict[str, Any]] = []
    for r in rows:
        if len(r) < 6:
            continue
        try:
            out.append({"date": r[0], "open": float(r[1]), "close": float(r[2]), "high": float(r[3]), "low": float(r[4]), "volume": float(r[5])})
        except Exception:
            pass
    return out


def latest_completed_trade_date(mode: str) -> str:
    now_cn = datetime.now(ZoneInfo("Asia/Shanghai"))
    end = now_cn.strftime("%Y-%m-%d")
    bars = eastmoney_index_kline("1.000001", end, 10)
    if not bars:
        raise DataError("无法确定最新交易日")
    latest = bars[-1]["date"]
    if mode == "realtime":
        return latest
    # 盘后模式在15:10之前绝不把当日未完成K线作为盘后结果。
    if latest == now_cn.strftime("%Y-%m-%d") and (now_cn.hour, now_cn.minute) < (15, 10):
        if len(bars) < 2:
            raise DataError("盘后模式无法取得上一交易日")
        return bars[-2]["date"]
    return latest


def china_market_session_status() -> str:
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    hm = now.hour * 60 + now.minute
    if 9 * 60 + 15 <= hm < 9 * 60 + 30:
        return "auction"
    if 9 * 60 + 30 <= hm <= 11 * 60 + 30 or 13 * 60 <= hm < 15 * 60:
        return "trading"
    if 11 * 60 + 30 < hm < 13 * 60:
        return "lunch"
    return "closed"


class Cache:
    def __init__(self, root: Optional[str] = None):
        self.root = Path(root or os.path.expanduser("~/.workbuddy-cache/a_share_quant_v63"))
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, kind: str, key: str) -> Path:
        p = self.root / kind
        p.mkdir(parents=True, exist_ok=True)
        return p / (key.replace("/", "_") + ".json")

    def get(self, kind: str, key: str) -> Optional[Any]:
        p = self.path(kind, key)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text("utf-8"))
        except Exception:
            return None

    def put(self, kind: str, key: str, value: Any) -> None:
        self.path(kind, key).write_text(json.dumps(value, ensure_ascii=False), "utf-8")


def fetch_histories(universe: List[Dict[str, Any]], trade_date: str, workers: int = 12, cache: Optional[Cache] = None, count_days: int = 260, kline_fetcher=None) -> Tuple[Dict[str, List[Dict[str, Any]]], List[str]]:
    cache = cache or Cache()
    kline_fetcher = kline_fetcher or eastmoney_kline
    out: Dict[str, List[Dict[str, Any]]] = {}
    errors: List[str] = []

    def one(item: Dict[str, Any]):
        code = item["code"]
        key = f"{trade_date}_{code}_{count_days}"
        cached = cache.get("kline", key)
        if cached and cached[-1].get("date") == trade_date:
            return code, cached, None
        try:
            bars = kline_fetcher(code, trade_date, count_days, item.get("market_id"))
            if bars and bars[-1]["date"] == trade_date:
                cache.put("kline", key, bars)
                return code, bars, None
            return code, bars, "目标交易日无K线"
        except Exception as e:
            return code, [], str(e)

    with ThreadPoolExecutor(max_workers=max(1, min(workers, 24))) as ex:
        futures = [ex.submit(one, x) for x in universe]
        total = len(futures)
        done = 0
        for fut in as_completed(futures):
            done += 1
            if done == 1 or done % 250 == 0 or done == total:
                print(f"    [历史K线] {done}/{total}", flush=True)
            code, bars, err = fut.result()
            if bars and bars[-1]["date"] == trade_date:
                out[code] = bars
            if err:
                errors.append(f"{code}:{err}")
    return out, errors


def fetch_breadth_for_date(all_universe: List[Dict[str, Any]], histories_main: Dict[str, List[Dict[str, Any]]], trade_date: str, workers: int = 12, cache: Optional[Cache] = None, kline_fetcher=None) -> Dict[str, Any]:
    cache = cache or Cache()
    kline_fetcher = kline_fetcher or eastmoney_kline
    up = down = flat = covered = 0
    missing = []

    def classify_bar(bar: Dict[str, Any]) -> int:
        pct = bar.get("pct_change")
        if pct is not None:
            v = float(pct)
        else:
            chg = float(bar.get("change", 0.0) or 0.0)
            v = chg
        return 1 if v > 0 else (-1 if v < 0 else 0)

    remaining = []
    for x in all_universe:
        code = x["code"]
        if code in histories_main:
            s = classify_bar(histories_main[code][-1])
            covered += 1
            up += s > 0; down += s < 0; flat += s == 0
        else:
            remaining.append(x)

    def one(item: Dict[str, Any]):
        code = item["code"]
        key = f"breadth_{trade_date}_{code}"
        c = cache.get("breadth", key)
        if c:
            return code, c, None
        try:
            bars = kline_fetcher(code, trade_date, 3, item.get("market_id"))
            if bars and bars[-1]["date"] == trade_date:
                b = bars[-1]
                cache.put("breadth", key, b)
                return code, b, None
            return code, None, "无目标日K线"
        except Exception as e:
            return code, None, str(e)

    if remaining:
        with ThreadPoolExecutor(max_workers=max(1, min(workers, 24))) as ex:
            futures = [ex.submit(one, x) for x in remaining]
            total = len(futures)
            done = 0
            for fut in as_completed(futures):
                done += 1
                if done == 1 or done % 250 == 0 or done == total:
                    print(f"    [市场宽度补采] {done}/{total}", flush=True)
                code, bar, err = fut.result()
                if bar:
                    s = classify_bar(bar)
                    covered += 1
                    up += s > 0; down += s < 0; flat += s == 0
                elif err:
                    missing.append(f"{code}:{err}")

    denom = up + down
    breadth = up / denom if denom else 0.0
    return {"up": int(up), "down": int(down), "flat": int(flat), "covered": covered, "universe": len(all_universe), "breadth": breadth, "missing": missing}


def eastmoney_intraday_trends(code: str, market_id: Optional[int] = None) -> List[Dict[str, Any]]:
    data=_get_json("https://push2his.eastmoney.com/api/qt/stock/trends2/get",{
        "secid":_secid(code,market_id),"ndays":1,"iscr":0,"iscca":0,
        "fields1":"f1,f2,f3,f4,f5,f6,f7,f8","fields2":"f51,f52,f53,f54,f55,f56,f57,f58"
    })
    rows=(((data or {}).get("data") or {}).get("trends") or [])
    out=[]
    for line in rows:
        p=str(line).split(',')
        if len(p)<6: continue
        try: out.append({"time":p[0],"close":float(p[2]),"volume":float(p[5])})
        except Exception: pass
    return out

# ==================== V6.3 盘中快照工具 ====================
def _as_float_or_none(v):
    if v is None or isinstance(v,bool): return None
    if isinstance(v,str) and v.strip() in ('','-','--','None','null','nan','NaN'): return None
    try:
        x=float(v)
        if x!=x or x in (float('inf'),float('-inf')): return None
        return x
    except Exception: return None


def realtime_breadth_from_universe(universe: List[Dict[str,Any]]) -> Dict[str,Any]:
    up=down=flat=covered=0; missing=[]
    for x in universe:
        pct=_as_float_or_none(x.get('pct'))
        if pct is None:
            missing.append(str(x.get('code') or '')); continue
        covered+=1
        if pct>0: up+=1
        elif pct<0: down+=1
        else: flat+=1
    return {'up':up,'down':down,'flat':flat,'covered':covered,'universe':len(universe),'breadth':up/max(up+down,1),'missing':missing}


def build_realtime_bars(bars: List[Dict[str,Any]], snapshot: Dict[str,Any], trade_date:str) -> List[Dict[str,Any]]:
    """删除缓存中的当日未完成K线，再用当前股票池快照重建当日K线。
    这避免同一交易日多次运行时命中旧缓存，把早盘快照冒充当前实时数据。
    """
    hist=[dict(x) for x in bars if str(x.get('date'))!=str(trade_date)]
    if not hist: return []
    prev=float(hist[-1]['close'])
    last=_as_float_or_none(snapshot.get('last')); op=_as_float_or_none(snapshot.get('open')); hi=_as_float_or_none(snapshot.get('high')); lo=_as_float_or_none(snapshot.get('low'))
    # 为了让背景数学可运行，价格缺失时只构造中性占位；evaluate_realtime_stock仍从snapshot识别缺失并传播UNKNOWN。
    math_last=last if last is not None else prev
    math_open=op if op is not None else math_last
    math_high=hi if hi is not None else max(math_open,math_last)
    math_low=lo if lo is not None else min(math_open,math_last)
    vol=_as_float_or_none(snapshot.get('volume')); amount=_as_float_or_none(snapshot.get('amount')); turn=_as_float_or_none(snapshot.get('turnover')); pct=_as_float_or_none(snapshot.get('pct')); ch=_as_float_or_none(snapshot.get('change'))
    hist.append({'date':str(trade_date),'open':math_open,'close':math_last,'high':math_high,'low':math_low,'volume':vol or 0.0,'amount':amount or 0.0,'amplitude':((math_high-math_low)/prev*100 if prev else 0.0),'pct_change':pct if pct is not None else ((math_last/prev-1)*100 if prev else 0.0),'change':ch if ch is not None else math_last-prev,'turnover':turn or 0.0})
    return hist


def intraday_reference_price(rows: List[Dict[str,Any]], minutes_back:int=5) -> Optional[float]:
    if not rows: return None
    # 趋势接口通常为1分钟；优先取倒数(minutes_back+1)条，数据不足时不猜。
    n=int(minutes_back)+1
    if len(rows)<n: return None
    try: return float(rows[-n]['close'])
    except Exception: return None


def china_realtime_window_status(min_minutes_from_open:int=30) -> str:
    """盘中实时模型时段。默认开盘30分钟后才允许，午休/集合竞价/收盘后均阻断。"""
    now=datetime.now(ZoneInfo('Asia/Shanghai'))
    hm=now.hour*60+now.minute
    morning_start=9*60+30+int(min_minutes_from_open)
    if 9*60+30 <= hm < morning_start: return 'warmup'
    if morning_start <= hm <= 11*60+30: return 'realtime'
    if 13*60 <= hm < 15*60: return 'realtime'
    return china_market_session_status()
