from __future__ import annotations
import numpy as np
import pandas as pd



def _dedupe_seat_events(st:pd.DataFrame)->pd.DataFrame:
    """同股同日同席位多上榜原因只保留一个经济事件；优先单日窗口，再按买入额覆盖度。"""
    if st.empty:return st.copy()
    x=st.copy()
    # Generic institution names are categories, never persistent seat identities.
    if 'exalter' in x:x=x[~x['exalter'].astype(str).eq('机构专用')].copy()
    if 'seat_code' in x:x=x[~x['seat_code'].astype(str).isin(['0',''])].copy()
    if 'identity_disclosed' in x:x=x[x['identity_disclosed'].astype(str).str.lower().isin(['true','1'])].copy()
    if x.empty:return x
    x['trade_date']=pd.to_datetime(x['trade_date']).dt.normalize()
    x['_reason']=x['reason'].astype(str) if 'reason' in x else ''
    x['_is_3d']=x['_reason'].str.contains(r'连续.{0,6}(?:三|3)个?交易日|三个交易日|3个交易日',regex=True,na=False)
    for c in ['buy','sell','net_buy']:
        if c in x:x[c]=pd.to_numeric(x[c],errors='coerce').fillna(0.0)
    buy_s=pd.to_numeric(x['buy'],errors='coerce').fillna(0) if 'buy' in x else pd.Series(0.0,index=x.index)
    sell_s=pd.to_numeric(x['sell'],errors='coerce').fillna(0) if 'sell' in x else pd.Series(0.0,index=x.index)
    x['_coverage']=buy_s.abs()+sell_s.abs()
    keys=[c for c in ['trade_date','ts_code','exalter'] if c in x]
    if len(keys)<3:return x.drop(columns=['_reason','_is_3d','_coverage'],errors='ignore')
    x=(x.sort_values(keys+['_is_3d','_coverage'],ascending=[True,True,True,True,False])
         .drop_duplicates(keys,keep='first'))
    return x.drop(columns=['_reason','_is_3d','_coverage'],errors='ignore')

def _market_calendar(daily: pd.DataFrame, trade_dates=None) -> pd.DatetimeIndex:
    if trade_dates is None:
        vals=pd.to_datetime(daily['trade_date']).dropna().unique()
    else:
        vals=pd.to_datetime(pd.Series(list(trade_dates))).dropna().unique()
    return pd.DatetimeIndex(vals).sort_values().normalize().unique()


def _make_labels(seat_trades:pd.DataFrame,daily:pd.DataFrame,trade_dates=None)->pd.DataFrame:
    """构造席位交易的3/5/10日标签；成熟日严格按全市场交易日历计数。"""
    st=_dedupe_seat_events(seat_trades); d=daily.copy()
    if st.empty or d.empty: return pd.DataFrame()
    st['trade_date']=pd.to_datetime(st['trade_date']).dt.normalize()
    d['trade_date']=pd.to_datetime(d['trade_date']).dt.normalize()
    cal=_market_calendar(d,trade_dates); cpos={x:i for i,x in enumerate(cal)}
    for c in ['buy','sell','net_buy']:
        if c in st: st[c]=pd.to_numeric(st[c],errors='coerce').fillna(0.0)
    # 同一席位/股票/日/经济内容去重，避免同一上榜原因重复计样本。
    keys=[c for c in ['trade_date','ts_code','exalter','buy','sell','net_buy'] if c in st]
    st=st.drop_duplicates(keys)
    if 'buy' in st: st=st[st['buy']>0]
    rows=[]
    bycode={c:g.set_index('trade_date').sort_index() for c,g in d.groupby('ts_code')}
    for _,r in st.iterrows():
        code=r['ts_code']; dt=r['trade_date']; seat=str(r.get('exalter',''))
        if not seat or code not in bycode or dt not in cpos: continue
        i=cpos[dt]
        if i+10>=len(cal): continue
        maturity=cal[i+10]
        # 必须等到第10个后续市场交易日已经完成，才成为成熟样本。
        g=bycode[code]
        hist_dates=cal[i:i+11]
        # 停牌日以最近可观察收盘价横向持有；高低价在停牌日等同前收，避免制造波动。
        z=g.reindex(hist_dates)
        cc='signal_close' if 'signal_close' in z.columns else 'close'
        hc='signal_high' if 'signal_high' in z.columns else 'high'
        lc='signal_low' if 'signal_low' in z.columns else 'low'
        close=pd.to_numeric(z[cc],errors='coerce').ffill()
        if close.iloc[0] != close.iloc[0] or close.iloc[-1] != close.iloc[-1]: continue
        high=pd.to_numeric(z.get(hc),errors='coerce') if hc in z else close.copy()
        low=pd.to_numeric(z.get(lc),errors='coerce') if lc in z else close.copy()
        high=high.where(high.notna(),close); low=low.where(low.notna(),close)
        p0=float(close.iloc[0])
        if not np.isfinite(p0) or p0<=0: continue
        rows.append({
            'exalter':seat,'ts_code':code,'event_date':dt,'mature_date':maturity,
            'ret3':float(close.iloc[3]/p0-1),'ret5':float(close.iloc[5]/p0-1),
            'hit10':float(((high.iloc[1:]/p0-1)>=0.10).any()),
            'mae':float((low.iloc[1:]/p0-1).min()),'mfe':float((high.iloc[1:]/p0-1).max()),
            'buy':float(r.get('buy',0.0) or 0.0)
        })
    return pd.DataFrame(rows)


def build_mature_seat_quality(seat_trades:pd.DataFrame, daily:pd.DataFrame, sector_daily:pd.DataFrame|None=None, trade_dates=None, half_life_sessions:int=60)->pd.DataFrame:
    """动态席位质量。

    对每个评价日，只使用：
    1) 评价日前已经完整成熟10个后续交易日的席位样本；
    2) 样本事件发生日在评价日前120个市场交易日以内；
    3) 以交易日半衰期做指数时间衰减，默认60个交易日，避免陈旧席位战绩与近期战绩等权；
    4) 五个维度：3日收益、5日收益、10日达10%概率、最大不利波动、最大有利波动。
    各维度先在同一评价日跨席位做横截面百分位，因此不使用拍脑袋收益尺度。
    最终进入个股资金质量分时还会按成熟样本数向0.5中性值收缩，避免小样本席位被放大。
    """
    lab=_make_labels(seat_trades,daily,trade_dates)
    if lab.empty: return pd.DataFrame(columns=['exalter','asof_date','seat_quality_raw','seat_quality_samples','seat_quality_pctile'])
    cal=_market_calendar(daily,trade_dates); cpos={x:i for i,x in enumerate(cal)}
    # 评价日使用全部市场交易日；只在有席位成熟历史时输出。
    snapshots=[]
    seats=sorted(lab['exalter'].dropna().unique())
    first=max(0,min(cpos.get(x,10**9) for x in lab['mature_date']))
    for p in range(first,len(cal)):
        asof=cal[p]
        lo=max(0,p-120); lo_date=cal[lo]
        # 信息成熟要求 mature_date < asof；当天盘后评分可使用当天早先已知历史，但不能使用当天刚产生未来标签。
        h=lab[(lab['mature_date']<asof)&(lab['event_date']>=lo_date)&(lab['event_date']<asof)].copy()
        if h.empty: continue
        half_life=max(10,int(half_life_sessions))
        h['_age_sessions']=h['event_date'].map(lambda x: max(0,p-cpos.get(x,p)))
        h['_time_weight']=np.power(0.5,h['_age_sessions']/float(half_life))
        rows=[]
        for seat,g in h.groupby('exalter'):
            w=pd.to_numeric(g['_time_weight'],errors='coerce').fillna(0).to_numpy(dtype=float)
            if not np.isfinite(w).all() or w.sum()<=0:
                w=np.ones(len(g),dtype=float)
            row={'exalter':seat,'seat_quality_samples':int(len(g))}
            for c in ['ret3','ret5','hit10','mae','mfe']:
                v=pd.to_numeric(g[c],errors='coerce').to_numpy(dtype=float)
                ok=np.isfinite(v)&np.isfinite(w)
                row[c]=float(np.average(v[ok],weights=w[ok])) if ok.any() and w[ok].sum()>0 else np.nan
            rows.append(row)
        q=pd.DataFrame(rows)
        # 高MAE（更接近0）更好，其余越高越好。
        for c in ['ret3','ret5','hit10','mae','mfe']:
            q[c+'_pct']=q[c].rank(pct=True,method='average')
        q['seat_quality_raw']=q[[c+'_pct' for c in ['ret3','ret5','hit10','mae','mfe']]].mean(axis=1)
        q['seat_quality_pctile']=q['seat_quality_raw'].rank(pct=True,method='average')
        q['asof_date']=asof
        snapshots.append(q[['exalter','asof_date','seat_quality_raw','seat_quality_samples','seat_quality_pctile']])
    return pd.concat(snapshots,ignore_index=True) if snapshots else pd.DataFrame(columns=['exalter','asof_date','seat_quality_raw','seat_quality_samples','seat_quality_pctile'])


def attach_event_seat_quality(events:pd.DataFrame, seat_trades:pd.DataFrame, seat_quality:pd.DataFrame)->pd.DataFrame:
    """把T日实际买方席位的历史质量附着到龙虎榜事件。

    只有历史成熟样本>=20的席位可贡献正/负质量评价；没有合格席位时保持中性所需的
    `seat_quality_samples=0, seat_quality_pctile=NaN`。
    """
    e=events.copy()
    if e.empty:
        e['seat_quality_pctile']=np.nan; e['seat_quality_samples']=0; return e
    e['trade_date']=pd.to_datetime(e['trade_date']).dt.normalize()
    st=seat_trades.copy(); sq=seat_quality.copy()
    if st.empty or sq.empty:
        e['seat_quality_pctile']=np.nan; e['seat_quality_samples']=0; return e
    st['trade_date']=pd.to_datetime(st['trade_date']).dt.normalize(); sq['asof_date']=pd.to_datetime(sq['asof_date']).dt.normalize()
    if 'buy' in st: st=st[pd.to_numeric(st['buy'],errors='coerce').fillna(0)>0].copy()
    out=[]
    for _,r in e.iterrows():
        day=r['trade_date']; code=r['ts_code']
        cur=st[(st['trade_date']==day)&(st['ts_code']==code)].copy()
        rep=str(r.get('rep_reason','') or '')
        if rep and 'reason' in cur:
            z=cur[cur['reason'].astype(str).eq(rep)]
            cur=z
        cur=_dedupe_seat_events(cur)
        if cur.empty:
            out.append((np.nan,0)); continue
        hist=sq[(sq['asof_date']==day)&(sq['seat_quality_samples']>=20)]
        cur=cur.merge(hist[['exalter','seat_quality_pctile','seat_quality_samples']],on='exalter',how='inner')
        if cur.empty:
            out.append((np.nan,0)); continue
        w=pd.to_numeric(cur.get('buy',1.0),errors='coerce').fillna(0).clip(lower=0)
        if w.sum()<=0: w=pd.Series(1.0,index=cur.index)
        q=float(np.average(cur['seat_quality_pctile'],weights=w))
        # 只需要告诉评分器“有至少一个20+成熟样本的席位”；保留最弱合格席位样本数便于审计。
        n=int(cur['seat_quality_samples'].min())
        out.append((q,n))
    e['seat_quality_pctile']=[x[0] for x in out]; e['seat_quality_samples']=[x[1] for x in out]
    return e
