from __future__ import annotations
import numpy as np
import pandas as pd
from .pit_risk_guard import merge_verified_limits
from .features import rolling_pctile_last
from .market_env import classify_market


def _safe_rank_roll(df,col,ascending=True,window=120,minp=20):
    return rolling_pctile_last(df[col],window=window,min_periods=minp,ascending=ascending)

def _safe_median(s, default=0.0):
    x=pd.to_numeric(s,errors='coerce').dropna()
    return float(x.median()) if len(x) else float(default)


def _apply_slow_open_fast_close(m:pd.DataFrame,recovery_confirm_days:int=2)->pd.DataFrame:
    """市场权限慢开快关。

    风险恶化允许当天直接降到原始权限；改善不允许跨级恢复，且至少连续2天改善后才上调一级。
    这是对既有“暂停→小仓试错→精选→正常”语义的确定性工程实现，不使用盲测调参。
    """
    if m.empty:return m
    levels={'暂停':0,'小仓试错':1,'精选':2,'正常':3}; rev={v:k for k,v in levels.items()}
    current=None; streak=0; out=[]
    for _,r in m.sort_values('trade_date').iterrows():
        raw=str(r['raw_market_permission']); rawlv=levels.get(raw,0)
        if current is None:
            current=rawlv;streak=0
        elif rawlv<current:
            current=rawlv;streak=0
        elif rawlv>current:
            improving=float(r.get('improvement',0) or 0)>0
            streak=streak+1 if improving else 0
            if streak>=max(2,int(recovery_confirm_days)):
                current=min(current+1,rawlv);streak=0
        else:
            streak=0
        out.append(rev[current])
    m=m.sort_values('trade_date').copy();m['market_permission']=out
    return m


def build_market_features(stock_features:pd.DataFrame, limits:pd.DataFrame|None=None, index_daily:pd.DataFrame|None=None,
                          recovery_confirm_days:int=2)->pd.DataFrame:
    """只使用当日及过去数据构建市场环境输入；收益率约定为小数。"""
    d=stock_features.copy(); d['trade_date']=pd.to_datetime(d['trade_date'])
    # 本策略执行股票池为沪深A股；北交所未完成独立验证，不得污染市场宽度和情绪统计。
    if 'ts_code' in d:
        d=d[d['ts_code'].astype(str).str.endswith(('.SH','.SZ'))].copy()
    if 'pct_chg' not in d:
        d=d.sort_values(['ts_code','trade_date']); d['pct_chg']=d.groupby('ts_code')['signal_close' if 'signal_close' in d else 'close'].pct_change()
    else:
        d['pct_chg']=pd.to_numeric(d['pct_chg'],errors='coerce')
    d=merge_verified_limits(d,limits)
    d['is_up']=d['pct_chg']>0
    d['above20']=d['close']>d['ma20']; d['above60']=d['close']>d['ma60']
    d['blast']=d['touch_up']&~d['is_limit_up']
    d=d.sort_values(['ts_code','trade_date'])
    d['prev_limit_up']=d.groupby('ts_code')['is_limit_up'].shift(1).astype('boolean').fillna(False).astype(bool)
    d['prev20max']=d.groupby('ts_code')['signal_high' if 'signal_high' in d else 'high'].transform(lambda x:x.shift(1).rolling(20,min_periods=20).max())
    d['prev20min']=d.groupby('ts_code')['signal_low' if 'signal_low' in d else 'low'].transform(lambda x:x.shift(1).rolling(20,min_periods=20).min())
    sigc=d['signal_close'] if 'signal_close' in d else d['close']
    d['newhigh20']=sigc>d['prev20max']; d['newlow20']=sigc<d['prev20min']

    rows=[]
    for dt,g in d.groupby('trade_date'):
        touched=int(g['touch_up'].sum()); blasts=int(g['blast'].sum());prev=g[g['prev_limit_up']]
        nh=int(g['newhigh20'].sum()); nl=int(g['newlow20'].sum())
        free_mv=pd.to_numeric(g.get('free_mv',pd.Series(index=g.index,dtype=float)),errors='coerce')
        if free_mv.notna().sum()>=50:
            med=free_mv.median(); small=_safe_median(g[free_mv<=med]['pct_chg']); large=_safe_median(g[free_mv>free_mv.quantile(.7)]['pct_chg']); smallrel=float(small-large)
        else: smallrel=0.0
        rows.append({
            'trade_date':dt,'pct_up':float(g['is_up'].mean()),'pct_above_ma20':float(g['above20'].mean()),'pct_above_ma60':float(g['above60'].mean()),
            'median_return':_safe_median(g['pct_chg']),'limit_up_count':int(g['is_limit_up'].sum()),'limit_down_count':int(g['is_limit_down'].sum()),
            'blast_rate':float(blasts/touched) if touched else 0.0,'prev_limit_median_return':_safe_median(prev['pct_chg']) if len(prev) else 0.0,
            'prev_limit_red_rate':float((prev['pct_chg']>0).mean()) if len(prev) else 0.5,
            'newhigh_low_balance':float((nh-nl)/(nh+nl)) if nh+nl else 0.0,'total_amount':float(g['amount'].sum()),'smallcap_relative':smallrel,
            'cross_section_vol':float(pd.to_numeric(g['pct_chg'],errors='coerce').std(ddof=0) or 0.0),
        })
    m=pd.DataFrame(rows).sort_values('trade_date').reset_index(drop=True)
    for c in ['pct_up','pct_above_ma20','pct_above_ma60','limit_up_count','prev_limit_median_return','prev_limit_red_rate','newhigh_low_balance','total_amount','smallcap_relative']:
        m[c+'_p']=_safe_rank_roll(m,c,True)
    for c in ['limit_down_count','blast_rate','cross_section_vol']:
        m[c+'_riskp']=_safe_rank_roll(m,c,True)
    # 取消隐藏手工权重：同类维度只做等权中位聚合，风险保持独立维度，不再从情绪中二次扣减。
    m['breadth_pctile']=m[['pct_up_p','pct_above_ma20_p','pct_above_ma60_p','newhigh_low_balance_p']].median(axis=1,skipna=True)
    m['sentiment_pctile']=m[['limit_up_count_p','prev_limit_median_return_p','prev_limit_red_rate_p']].median(axis=1,skipna=True)
    m['liquidity_pctile']=m['total_amount_p'];m['smallcap_relative_pctile']=m['smallcap_relative_p']
    m['risk_pctile']=m[['limit_down_count_riskp','blast_rate_riskp','cross_section_vol_riskp']].median(axis=1,skipna=True)
    m['trend_pctile']=m[['pct_above_ma20_p','pct_above_ma60_p']].median(axis=1,skipna=True)
    m['index_return']=np.nan;m['index_return_pctile']=np.nan
    if index_daily is not None and len(index_daily):
        ix=index_daily.copy(); ix['trade_date']=pd.to_datetime(ix['trade_date']); ix=ix.sort_values(['ts_code','trade_date'])
        ix['close']=pd.to_numeric(ix['close'],errors='coerce')
        ix['ma20']=ix.groupby('ts_code')['close'].transform(lambda x:x.rolling(20,min_periods=20).mean());ix['above']=ix['close']>ix['ma20']
        if 'pct_chg' in ix: ix['ret1']=pd.to_numeric(ix['pct_chg'],errors='coerce')
        else: ix['ret1']=ix.groupby('ts_code')['close'].pct_change()
        ib=ix.groupby('trade_date').agg(index_above20=('above','mean'),index_return=('ret1','median')).reset_index()
        m=m.merge(ib,on='trade_date',how='left',suffixes=('','_ix'))
        if 'index_return_ix' in m:
            m['index_return']=m['index_return_ix'];m=m.drop(columns=['index_return_ix'])
        m['index_above20_pctile']=_safe_rank_roll(m,'index_above20',True)
        # 指数趋势与个股宽度先各自转成滚动百分位，再等权中位聚合；不再使用65/35人工权重。
        m['trend_pctile']=m[['pct_above_ma20_p','pct_above_ma60_p','index_above20_pctile']].median(axis=1,skipna=True).clip(0,1)
        m['index_return_pctile']=_safe_rank_roll(m,'index_return',True)
    ret_by=[]
    for dt,g in d.groupby('trade_date'):
        a=pd.to_numeric(g['amount'],errors='coerce').fillna(0); r=pd.to_numeric(g['pct_chg'],errors='coerce').fillna(0)
        wret=float((r*a).sum()/a.sum()) if a.sum()>0 else float(r.mean());ret_by.append((dt,abs(wret-_safe_median(r))))
    div=pd.DataFrame(ret_by,columns=['trade_date','divraw']); div['divergence_pctile']=_safe_rank_roll(div,'divraw',True)
    m=m.merge(div[['trade_date','divergence_pctile']],on='trade_date',how='left')
    # 改善速度来自完整市场健康中位值的3日变化，不再人为乘2放大。
    health_parts=pd.concat([m['breadth_pctile'],m['sentiment_pctile'],m['trend_pctile'],m['liquidity_pctile'],
                            m['smallcap_relative_pctile'],1-m['risk_pctile'],1-m['divergence_pctile']],axis=1)
    m['market_health_median']=health_parts.median(axis=1,skipna=True).clip(0,1)
    m['improvement']=(m['market_health_median']-m['market_health_median'].shift(3)).fillna(0).clip(-1,1)
    # 高潮中的“指数大涨”改为真实指数单日涨幅滚动极端，而不是把趋势强度误当成单日暴涨。
    m['index_extreme_up']=(m['index_return_pctile']>=.90)&(m['index_return']>0)
    m['turnover_extreme']=m['liquidity_pctile']>=.90
    results=[]
    for _,r in m.iterrows():
        inp={k:r[k] for k in ['breadth_pctile','sentiment_pctile','trend_pctile','liquidity_pctile','smallcap_relative_pctile','risk_pctile','divergence_pctile','improvement']}
        inp.update({'index_extreme_up':False,'turnover_extreme':bool(r['turnover_extreme']),'sector_broad_surge':False,'individual_accelerating':False})
        if any(pd.isna(inp[k]) for k in ['breadth_pctile','sentiment_pctile','trend_pctile','liquidity_pctile','smallcap_relative_pctile','risk_pctile','divergence_pctile']):
            state='震荡可做';perm='暂停';comp=np.nan;q='insufficient'
        else:
            rr=classify_market(inp);state=rr.state;perm=rr.permission;comp=rr.composite;q=rr.data_quality
        results.append((state,perm,comp,q))
    m[['market_state','raw_market_permission','market_composite','market_data_quality']]=pd.DataFrame(results,index=m.index)
    m=_apply_slow_open_fast_close(m,recovery_confirm_days=recovery_confirm_days)
    return m
