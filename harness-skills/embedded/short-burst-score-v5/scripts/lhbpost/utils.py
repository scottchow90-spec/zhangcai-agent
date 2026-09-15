from __future__ import annotations
import math, hashlib, json
from pathlib import Path
from typing import Any


def clip(x: float, lo: float=0.0, hi: float=1.0) -> float:
    try:
        if x is None or math.isnan(float(x)):
            return lo
    except Exception:
        return lo
    return min(hi, max(lo, float(x)))


def pct_rank(values):
    import pandas as pd
    s = pd.Series(values, dtype='float64')
    return s.rank(method='average', pct=True)


def stable_hash(obj: Any) -> str:
    b = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(b).hexdigest()


def file_sha256(path: str|Path) -> str:
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def parse_date_series(s):
    """可靠解析YYYYMMDD整数/字符串或普通日期字符串，避免pandas把20250101整数当纳秒。"""
    import pandas as pd
    x=pd.Series(s,index=getattr(s,'index',None))
    st=x.astype('string').str.replace(r'\.0$','',regex=True).str.strip()
    out=pd.to_datetime(st,errors='coerce')
    mask=st.str.fullmatch(r'\d{8}',na=False)
    if mask.any():out.loc[mask]=pd.to_datetime(st.loc[mask],format='%Y%m%d',errors='coerce')
    return out


def normalize_event_features(frame):
    """Parse event booleans and aware timestamps before filtering or aggregation."""
    import pandas as pd
    if frame is None: return None
    x=frame.copy()
    required={'ts_code','trade_date','public_time'}
    if not required <= set(x.columns): raise ValueError('event_features缺字段:'+','.join(sorted(required-set(x.columns))))
    def boolean(v):
        if pd.isna(v): return False
        if isinstance(v, str):
            val=v.strip().lower()
            if val in {'false','0',''}: return False
            if val in {'true','1'}: return True
            raise ValueError('事件布尔值无法解析:'+v)
        if v in (True,1): return True
        if v in (False,0): return False
        raise ValueError('事件布尔值无法解析')
    for col in ('independent_catalyst','severe_negative_event','concept_denial'):
        x[col]=x[col].map(boolean) if col in x else False
    for col in ('risk_penalty','catalyst_quality'):
        if col in x:
            values=pd.to_numeric(x[col],errors='coerce')
            if (x[col].notna() & (values.isna() | ~values.between(0,1))).any():
                raise ValueError('事件数值必须在0到1之间:'+col)
            x[col]=values.fillna(0) if col=='risk_penalty' else values
    for value in x['public_time']:
        try: stamp=pd.Timestamp(value)
        except Exception as ex: raise ValueError('事件发布时间无效') from ex
        if pd.isna(stamp) or stamp.tzinfo is None: raise ValueError('事件public_time必须带明确时区')
    x['public_time']=pd.to_datetime(x['public_time'],utc=True)
    x['trade_date']=parse_date_series(x['trade_date'])
    if x['trade_date'].isna().any() or x['ts_code'].isna().any(): raise ValueError('事件日期或股票代码缺失')
    return x
