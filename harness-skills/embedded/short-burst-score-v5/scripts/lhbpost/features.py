from __future__ import annotations
import numpy as np
import pandas as pd
from .utils import clip


def rolling_pctile_last(s: pd.Series, window:int=120, min_periods:int=20, ascending:bool=True)->pd.Series:
    """只用当前及此前数据计算滚动经验百分位；用于盘后T日状态。"""
    vals=s.astype(float).to_numpy()
    out=np.full(len(vals),np.nan)
    for i in range(len(vals)):
        lo=max(0,i-window+1); x=vals[lo:i+1]
        x=x[np.isfinite(x)]
        if len(x)<min_periods or not np.isfinite(vals[i]): continue
        v=vals[i]
        rank=(np.sum(x < v)+0.5*np.sum(x==v))/len(x)
        out[i]=rank if ascending else 1-rank
    return pd.Series(out,index=s.index)


def build_stock_daily_features(daily:pd.DataFrame, daily_basic:pd.DataFrame|None=None, adj_factor:pd.DataFrame|None=None)->pd.DataFrame:
    """构建因果日线特征。

    执行价格保留未复权真实价格；若提供adj_factor，则技术趋势/收益类特征使用
    `未复权价格×当日复权因子` 的连续价格序列，再把均线/ATR映射回当日未复权尺度。
    这样既避免除权日制造假跌破，也不使用未来公司行动。
    """
    d=daily.copy()
    d['trade_date']=pd.to_datetime(d['trade_date'])
    if d.duplicated(['ts_code','trade_date']).any():
        raise ValueError('daily存在重复股票交易日')
    d=d.sort_values(['ts_code','trade_date'])
    if adj_factor is not None and len(adj_factor):
        a=adj_factor.copy(); a['trade_date']=pd.to_datetime(a['trade_date'])
        a['adj_factor']=pd.to_numeric(a['adj_factor'],errors='coerce')
        d=d.merge(a[['ts_code','trade_date','adj_factor']].drop_duplicates(['ts_code','trade_date']),
                  on=['ts_code','trade_date'],how='left')
        fac=d['adj_factor']
    else:
        d['adj_factor']=1.0
        fac=pd.Series(1.0,index=d.index)
    for c in ['open','high','low','close','amount','vol']:
        if c in d:d[c]=pd.to_numeric(d[c],errors='coerce')
    # signal_*只用于跨日技术计算，实际成交仍使用原始open/high/low/close。
    for c in ['open','high','low','close']:
        d[f'signal_{c}']=d[c]*fac
    # Fill only missing returns, and only from two observed adjustment factors.
    # The fallback fac=1 used to keep raw price fields available is not evidence
    # that a raw close-to-close return is valid across corporate actions.
    continuous_return=pd.Series(np.nan,index=d.index,dtype=float)
    if adj_factor is not None and len(adj_factor):
        observed_factor=np.isfinite(fac)&fac.gt(0)
        paired_factor=observed_factor&observed_factor.groupby(d['ts_code']).shift(1,fill_value=False)
        continuous_return=d.groupby('ts_code')['signal_close'].pct_change(fill_method=None).where(paired_factor)
    if 'pct_chg' in d:
        observed_return=pd.to_numeric(d['pct_chg'],errors='raise')
        if (observed_return.notna()&~np.isfinite(observed_return)).any():
            raise ValueError('daily存在非有限涨跌幅')
        d['pct_chg']=observed_return.fillna(continuous_return)
    else:
        d['pct_chg']=continuous_return
    g=d.groupby('ts_code',group_keys=False)
    for n in [5,10,20,60]:
        ma_adj=g['signal_close'].transform(lambda x:x.rolling(n,min_periods=n).mean())
        d[f'ma{n}']=ma_adj/fac
    ma20_adj=d['ma20']*fac
    d['ma20_slope5']=ma20_adj.groupby(d['ts_code']).transform(lambda x:x/x.shift(5)-1)
    prev_close_adj=g['signal_close'].shift(1)
    tr_adj=pd.concat([(d['signal_high']-d['signal_low']).abs(),
                      (d['signal_high']-prev_close_adj).abs(),
                      (d['signal_low']-prev_close_adj).abs()],axis=1).max(axis=1)
    atr_adj=tr_adj.groupby(d['ts_code']).transform(lambda x:x.rolling(14,min_periods=14).mean())
    d['atr14']=atr_adj/fac
    d['ret3']=g['signal_close'].transform(lambda x:x/x.shift(3)-1)
    d['ret5']=g['signal_close'].transform(lambda x:x/x.shift(5)-1)
    d['ret10']=g['signal_close'].transform(lambda x:x/x.shift(10)-1)
    d['ret20']=g['signal_close'].transform(lambda x:x/x.shift(20)-1)
    prev20_high_adj=g['signal_high'].transform(lambda x:x.shift(1).rolling(20,min_periods=20).max())
    d['prev20_high']=prev20_high_adj/fac
    d['breakout_20d_strength']=((d['signal_close']/prev20_high_adj-0.95)/0.05).clip(0,1)
    rng=(d['high']-d['low']).replace(0,np.nan)
    d['close_location_day']=((d['close']-d['low'])/rng).fillna(0.5).clip(0,1)
    d['vol_ratio20']=d['amount']/g['amount'].transform(lambda x:x.shift(1).rolling(20,min_periods=10).median())
    vr=d['vol_ratio20'].astype(float)
    d['volume_health']=np.where(vr<1, (vr/1).clip(0,1), np.where(vr<=3,1.0,(1-(vr-3)/3).clip(0,1)))
    low60_adj=g['signal_low'].transform(lambda x:x.rolling(60,min_periods=20).min())
    high60_adj=g['signal_high'].transform(lambda x:x.rolling(60,min_periods=20).max())
    d['loc60']=((d['signal_close']-low60_adj)/(high60_adj-low60_adj).replace(0,np.nan)).clip(0,1)
    d['startup_location_health']=(1-(d['loc60']-0.75).abs()/0.75).clip(0,1).fillna(0.5)
    d['close_above_ma20']=d['close']>d['ma20']
    d['ma5_gt_ma10_gt_ma20']=(d['ma5']>d['ma10'])&(d['ma10']>d['ma20'])
    d['ma20_gt_ma60']=d['ma20']>d['ma60']
    d['rs_20d_pctile']=d.groupby('trade_date')['ret20'].rank(pct=True)
    d['ma20_slope_pctile']=d.groupby('trade_date')['ma20_slope5'].rank(pct=True)
    if daily_basic is not None and len(daily_basic):
        b=daily_basic.copy(); b['trade_date']=pd.to_datetime(b['trade_date'])
        if b.duplicated(['ts_code','trade_date']).any():
            raise ValueError('daily_basic存在重复股票交易日')
        cols=[c for c in ['ts_code','trade_date','turnover_rate','float_share','free_share','free_mv','circ_mv','total_mv'] if c in b]
        d=d.merge(b[cols],on=['ts_code','trade_date'],how='left')
    # 短线弹性必须做横截面归一化，避免把不同板块/不同量级股票用一个绝对市值阈值硬切。
    if 'turnover_rate' in d:
        tr=pd.to_numeric(d['turnover_rate'],errors='coerce')
        d['turnover_rate_pctile']=tr.groupby(d['trade_date']).rank(pct=True)
    else:
        d['turnover_rate_pctile']=np.nan
    free=pd.to_numeric(d.get('free_mv'),errors='coerce') if 'free_mv' in d else pd.Series(np.nan,index=d.index)
    # Circulating capitalization includes non-free holdings; it cannot stand in
    # for the separately sourced free float used by the elasticity model.
    d['effective_free_mcap']=free
    d['free_mcap_pctile']=free.groupby(d['trade_date']).rank(pct=True)
    return d

def map_industry_point_in_time(stock_rows:pd.DataFrame, members:pd.DataFrame)->pd.DataFrame:
    """按in_date/out_date把股票映射到当时申万一级行业，不用今天归属回填过去。"""
    s=stock_rows.copy(); s['trade_date']=pd.to_datetime(s['trade_date'])
    m=members.copy(); m['in_date']=pd.to_datetime(m['in_date'],errors='coerce')
    m['out_date']=pd.to_datetime(m.get('out_date'),errors='coerce') if 'out_date' in m else pd.NaT
    m['out_date']=m['out_date'].fillna(pd.Timestamp('2099-12-31'))
    use=[c for c in ['ts_code','l1_code','l1_name','in_date','out_date'] if c in m]
    # 先选合法历史归属，再左联原股票行；区间缺口必须保留为缺失而不是删股。
    candidates=s[['ts_code','trade_date']].merge(m[use],on='ts_code',how='left')
    mask=(candidates['trade_date']>=candidates['in_date'])&(candidates['trade_date']<=candidates['out_date'])
    valid=candidates[mask].sort_values(['ts_code','trade_date','in_date']).drop_duplicates(['ts_code','trade_date'],keep='last')
    return s.merge(valid,on=['ts_code','trade_date'],how='left',validate='one_to_one')



def build_sector_daily_features(stock_features_with_sector:pd.DataFrame)->pd.DataFrame:
    d=stock_features_with_sector.copy()
    d=d[d['l1_code'].notna()].copy()
    if 'pct_chg' not in d:
        d=d.sort_values(['ts_code','trade_date'])
        d['pct_chg']=d.groupby('ts_code')['signal_close' if 'signal_close' in d else 'close'].pct_change()
    agg=d.groupby(['trade_date','l1_code','l1_name'],as_index=False).agg(
        sector_ret1=('pct_chg','median'), sector_ret5=('ret5','median'), sector_amount=('amount','sum'))
    agg=agg.sort_values(['l1_code','trade_date'])
    agg['amount_med20']=agg.groupby('l1_code')['sector_amount'].transform(lambda x:x.shift(1).rolling(20,min_periods=10).median())
    agg['activity_ratio']=agg['sector_amount']/agg['amount_med20']
    agg['sector_rs_5d_pctile']=agg.groupby('trade_date')['sector_ret5'].rank(pct=True)
    agg['sector_ret1_pctile']=agg.groupby('trade_date')['sector_ret1'].rank(pct=True)
    agg['sector_activity_pctile']=agg.groupby('trade_date')['activity_ratio'].rank(pct=True)
    return agg

def aggregate_lhb(top_list:pd.DataFrame, top_inst:pd.DataFrame, daily:pd.DataFrame)->pd.DataFrame:
    """同股同日多上榜原因去重，并同时保留单日/三日累计两个披露窗口。

    规则：
    1) 同一经济窗口只选覆盖额最大的代表记录，绝不把多个上榜原因简单相加；
    2) 若同时存在单日榜和三日累计榜，两套金额分别保留，决策主窗口优先使用单日榜，
       三日累计窗口仅作为连续性/背景证据；
    3) 三日累计榜的资金强度必须除以三个市场交易会话的成交额之和；
    4) 机构专用、股通专用、普通营业部分拆，且席位明细只匹配主窗口上榜原因。
    """
    tl=top_list.copy(); ti=top_inst.copy(); dd=daily.copy()
    for x in [tl,ti,dd]:
        if len(x) and 'trade_date' in x: x['trade_date']=pd.to_datetime(x['trade_date'])
    buy_col=next((c for c in ['l_buy','buy','buy_amount','buy_total'] if c in tl),None)
    sell_col=next((c for c in ['l_sell','sell','sell_amount','sell_total'] if c in tl),None)

    if buy_col and sell_col and len(tl):
        tl[buy_col]=pd.to_numeric(tl[buy_col],errors='coerce').fillna(0.0)
        tl[sell_col]=pd.to_numeric(tl[sell_col],errors='coerce').fillna(0.0)
        tl=tl.drop_duplicates().copy()
        tl['_reason']=tl['reason'].astype(str) if 'reason' in tl else ''
        tl['_is_3d']=tl['_reason'].str.contains(r'连续.{0,6}(?:三|3)个?交易日|三个交易日|3个交易日',regex=True,na=False)
        if 'l_amount' in tl: tl['_coverage']=pd.to_numeric(tl['l_amount'],errors='coerce')
        elif 'amount' in tl: tl['_coverage']=pd.to_numeric(tl['amount'],errors='coerce')
        else: tl['_coverage']=tl[buy_col].abs()+tl[sell_col].abs()
        tl['_coverage']=tl['_coverage'].fillna(tl[buy_col].abs()+tl[sell_col].abs())
        reps=(tl.sort_values(['trade_date','ts_code','_is_3d','_coverage'],ascending=[True,True,True,False])
                .drop_duplicates(['trade_date','ts_code','_is_3d'],keep='first'))
        single=(reps[~reps['_is_3d']][['trade_date','ts_code',buy_col,sell_col,'_reason']]
                .rename(columns={buy_col:'daily_lhb_buy',sell_col:'daily_lhb_sell','_reason':'daily_reason'}))
        three=(reps[reps['_is_3d']][['trade_date','ts_code',buy_col,sell_col,'_reason']]
               .rename(columns={buy_col:'three_day_lhb_buy',sell_col:'three_day_lhb_sell','_reason':'three_day_reason'}))
        keys=tl[['trade_date','ts_code']].drop_duplicates()
        grp=keys.merge(single,on=['trade_date','ts_code'],how='left').merge(three,on=['trade_date','ts_code'],how='left')
        for c in ['daily_lhb_buy','daily_lhb_sell','three_day_lhb_buy','three_day_lhb_sell']:
            grp[c]=pd.to_numeric(grp.get(c),errors='coerce')
        grp['has_daily_window']=grp['daily_lhb_buy'].notna()|grp['daily_lhb_sell'].notna()
        grp['has_three_day_window']=grp['three_day_lhb_buy'].notna()|grp['three_day_lhb_sell'].notna()
        grp['window_type']=np.where(grp['has_daily_window'],'daily','3d')
        grp['rep_reason']=np.where(grp['has_daily_window'],grp['daily_reason'].fillna(''),grp['three_day_reason'].fillna(''))
        grp['lhb_buy']=np.where(grp['has_daily_window'],grp['daily_lhb_buy'].fillna(0),grp['three_day_lhb_buy'].fillna(0))
        grp['lhb_sell']=np.where(grp['has_daily_window'],grp['daily_lhb_sell'].fillna(0),grp['three_day_lhb_sell'].fillna(0))
        grp['lhb_net_buy']=grp['lhb_buy']-grp['lhb_sell']
        grp['daily_lhb_net_buy']=grp['daily_lhb_buy'].fillna(0)-grp['daily_lhb_sell'].fillna(0)
        grp['three_day_lhb_net_buy']=grp['three_day_lhb_buy'].fillna(0)-grp['three_day_lhb_sell'].fillna(0)
        reasons=(tl.groupby(['trade_date','ts_code'])['_reason']
                   .apply(lambda x:'|'.join(dict.fromkeys(str(v) for v in x if str(v).strip())))
                   .rename('all_reasons').reset_index())
        grp=grp.merge(reasons,on=['trade_date','ts_code'],how='left')
    else:
        if len(ti)==0: raise ValueError('龙虎榜数据缺少买卖金额字段且无top_inst明细')
        td=ti.copy()
        key=[c for c in ['trade_date','ts_code','exalter','buy','sell','net_buy','reason'] if c in td]
        td=td.drop_duplicates(key)
        grp=td.groupby(['trade_date','ts_code'],as_index=False).agg(lhb_buy=('buy','sum'),lhb_sell=('sell','sum'),lhb_net_buy=('net_buy','sum'))
        grp['window_type']='daily';grp['rep_reason']='';grp['all_reasons']=''
        grp['has_daily_window']=True;grp['has_three_day_window']=False
        grp['daily_lhb_buy']=grp['lhb_buy'];grp['daily_lhb_sell']=grp['lhb_sell'];grp['daily_lhb_net_buy']=grp['lhb_net_buy']
        grp['three_day_lhb_buy']=np.nan;grp['three_day_lhb_sell']=np.nan;grp['three_day_lhb_net_buy']=np.nan

    dd2=dd[['trade_date','ts_code','amount']].copy().sort_values(['ts_code','trade_date'])
    if dd2.duplicated(['trade_date','ts_code']).any():
        raise ValueError('daily存在重复股票交易日')
    # 窗口按全市场会话定位，停牌不能把更早成交额滚入最近三天。
    cal=pd.DatetimeIndex(sorted(dd2['trade_date'].unique()))
    positions={dt:i for i,dt in enumerate(cal)}
    sums={}
    for code,g in dd2.groupby('ts_code'):
        amounts=pd.to_numeric(g.set_index('trade_date')['amount'],errors='coerce').reindex(cal).fillna(0)
        roll=amounts.rolling(3,min_periods=3).sum()
        for idx,row in g.iterrows(): sums[idx]=roll.iloc[positions[row['trade_date']]]
    dd2['amount_3d']=pd.Series(sums)
    grp=grp.merge(dd2,on=['trade_date','ts_code'],how='left')
    grp['daily_impact_denominator']=grp['amount']
    grp['three_day_impact_denominator']=grp['amount_3d']
    grp['impact_denominator']=np.where(grp['window_type'].eq('3d'),grp['amount_3d'],grp['amount'])
    grp['lhb_net_buy_ratio']=grp['lhb_net_buy']/pd.Series(grp['impact_denominator']).replace(0,np.nan)
    grp['daily_lhb_net_buy_ratio']=grp['daily_lhb_net_buy']/pd.Series(grp['daily_impact_denominator']).replace(0,np.nan)
    grp['three_day_lhb_net_buy_ratio']=grp['three_day_lhb_net_buy']/pd.Series(grp['three_day_impact_denominator']).replace(0,np.nan)
    grp['lhb_participation_ratio']=(grp['lhb_buy']+grp['lhb_sell'])/pd.Series(grp['impact_denominator']).replace(0,np.nan)
    grp['lhb_net_impact_pctile']=grp.groupby('trade_date')['lhb_net_buy_ratio'].rank(pct=True)
    grp['lhb_participation_pctile']=grp.groupby('trade_date')['lhb_participation_ratio'].rank(pct=True)

    grp['seat_detail_available']=False
    if len(ti):
        td=ti.copy()
        key=[c for c in ['trade_date','ts_code','exalter','buy','sell','net_buy','reason'] if c in td]
        td=td.drop_duplicates(key).copy()
        for c in ['buy','sell','net_buy']:
            td[c]=pd.to_numeric(td[c],errors='coerce').fillna(0.0)
        if 'reason' in td:
            keys=grp[['trade_date','ts_code','rep_reason']].copy()
            td=td.merge(keys,on=['trade_date','ts_code'],how='inner')
            same=td['rep_reason'].eq('')|td['reason'].astype(str).eq(td['rep_reason'].astype(str))
            td=td[same].copy()
        ex=td['exalter'].astype(str)
        td['is_inst']=ex.str.contains('机构专用',na=False)
        td['is_connect']=ex.str.contains('沪股通专用|深股通专用|港股通专用',regex=True,na=False)
        td['inst_net']=td['net_buy'].where(td['is_inst'],0.0)
        td['connect_net']=td['net_buy'].where(td['is_connect'],0.0)
        td['broker_net']=td['net_buy'].where(~td['is_inst']&~td['is_connect'],0.0)
        s=td.groupby(['trade_date','ts_code'],as_index=False).agg(
            inst_net=('inst_net','sum'),broker_net=('broker_net','sum'),connect_net=('connect_net','sum'),
            seat_buy=('buy','sum'),seat_sell=('sell','sum'),seat_rows=('exalter','size'))
        grp=grp.merge(s,on=['trade_date','ts_code'],how='left')
        grp['seat_detail_available']=grp['seat_rows'].fillna(0).gt(0)
    for c in ['inst_net','broker_net','connect_net','seat_buy','seat_sell']:
        if c not in grp: grp[c]=0.0
    grp[['inst_net','broker_net','connect_net','seat_buy','seat_sell']]=grp[['inst_net','broker_net','connect_net','seat_buy','seat_sell']].fillna(0.0)
    grp['inst_net_buy_ratio']=grp['inst_net']/pd.Series(grp['impact_denominator']).replace(0,np.nan)
    grp['broker_net_buy_ratio']=grp['broker_net']/pd.Series(grp['impact_denominator']).replace(0,np.nan)
    grp['inst_net_impact_pctile']=grp.groupby('trade_date')['inst_net_buy_ratio'].rank(pct=True)
    grp['broker_net_impact_pctile']=grp.groupby('trade_date')['broker_net_buy_ratio'].rank(pct=True)
    denom=(grp['seat_buy']+grp['seat_sell']).replace(0,np.nan)
    grp['buy_sell_balance']=((grp['seat_buy']-grp['seat_sell'])/denom).fillna(0.0).clip(-1,1)
    if top_inst.attrs.get('disclosed_sides'):
        from .disclosed_sides import attach_disclosed_contributions
        grp=attach_disclosed_contributions(grp,top_inst.attrs['disclosed_sides'])
    return grp

def assign_lifecycle(events:pd.DataFrame, trade_dates=None)->pd.DataFrame:
    """把3个交易日内重复龙虎榜合并到同一生命周期。

    `trade_dates` 应为市场完整交易日历；若省略，则使用events中出现的交易日期，
    仅适合测试，不适合正式回测。生命周期编号表示当前3交易日窗口内第几次上榜。
    """
    e=events.copy()
    if e.empty:
        e['lifecycle_event_no']=pd.Series(dtype='int64')
        e['lifecycle_net_improving']=pd.Series(dtype='bool')
        return e
    e['trade_date']=pd.to_datetime(e['trade_date'])
    e=e.sort_values(['ts_code','trade_date']).copy()
    if trade_dates is None:
        cal=pd.DatetimeIndex(sorted(e['trade_date'].dropna().unique()))
    else:
        cal=pd.DatetimeIndex(pd.to_datetime(pd.Series(list(trade_dates))).dropna().unique()).sort_values()
    pos={pd.Timestamp(d).normalize():i for i,d in enumerate(cal)}
    eno={}; imp={}
    for code,g in e.groupby('ts_code',sort=False):
        recent=[]  # (calendar_position, net_ratio)
        for idx,row in g.iterrows():
            dt=pd.Timestamp(row['trade_date']).normalize()
            if dt not in pos:
                raise ValueError(f'交易日历缺少龙虎榜日期: {dt.date()}')
            p=pos[dt]
            recent=[x for x in recent if 0 < p-x[0] <= 3]
            eno[idx]=len(recent)+1
            val=float(row.get('lhb_net_buy_ratio',np.nan))
            imp[idx]=bool(recent and np.isfinite(val) and np.isfinite(recent[-1][1]) and val>recent[-1][1])
            recent.append((p,val))
    e['lifecycle_event_no']=pd.Series(eno).reindex(e.index).astype(int)
    e['lifecycle_net_improving']=pd.Series(imp).reindex(e.index).fillna(False).astype(bool)
    return e
