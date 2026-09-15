from __future__ import annotations
import numpy as np
import pandas as pd
import re
from .features import build_stock_daily_features,map_industry_point_in_time,build_sector_daily_features,aggregate_lhb,assign_lifecycle
from .market_features import build_market_features
from .schema import CandidateFeatures
from .utils import normalize_event_features
from .pit_risk_guard import attach_pit_risk, merge_verified_limits
from .seat_quality import build_mature_seat_quality, attach_event_seat_quality


def _selected_seeds(codes, trade_date, daily, daily_basic, stock_basic):
    if not isinstance(codes, (list, tuple)) or not codes:
        raise ValueError('selected_codes必须为非空代码列表')
    if any(not isinstance(c, str) or not re.fullmatch(r'\d{6}\.(SH|SZ|BJ)', c) for c in codes):
        raise ValueError('selected_codes包含无效股票代码')
    if len(set(codes)) != len(codes):
        raise ValueError('selected_codes包含重复股票')
    try:
        td = pd.Timestamp(trade_date)
        if pd.isna(td) or td.tzinfo is not None or td != td.normalize():
            raise ValueError()
    except (TypeError, ValueError):
        raise ValueError('selected_trade_date无效') from None
    if td not in set(pd.to_datetime(daily['trade_date']).dt.normalize()):
        raise ValueError('selected_trade_date不在实际交易日中')
    unknown = set(codes) - set(stock_basic['ts_code'].astype(str))
    if unknown:
        raise ValueError('selected_codes包含未知股票:'+','.join(sorted(unknown)))
    for name, frame in [('daily', daily), ('daily_basic', daily_basic)]:
        current = frame[pd.to_datetime(frame['trade_date']).dt.normalize().eq(td)]
        missing = set(codes) - set(current['ts_code'].astype(str))
        if missing:
            raise ValueError('selected_codes当日'+name+'缺失:'+','.join(sorted(missing)))
    return pd.DataFrame({'trade_date': [td] * len(codes), 'ts_code': list(codes)})


def _empty_lhb_table():
    # A verified empty source has a schema, but supplies no observed amounts.
    cols = ['lhb_buy','lhb_sell','lhb_net_buy','lhb_net_buy_ratio','inst_net_buy_ratio',
            'broker_net_buy_ratio','lhb_net_impact_pctile','lhb_participation_pctile',
            'inst_net_impact_pctile','broker_net_impact_pctile','buy_sell_balance',
            'seat_detail_available','lifecycle_event_no','lifecycle_net_improving']
    return pd.DataFrame({'trade_date':pd.Series(dtype='datetime64[ns]'),
                         'ts_code':pd.Series(dtype='object'),
                         **{c:pd.Series(dtype='float64') for c in cols}})


def _event_core_rank(d:pd.DataFrame, limits:pd.DataFrame|None=None, current_streaks=None)->pd.Series:
    """与最终决策一致的短线行业核心：连板高度→是否涨停→当日强度→5日强度→成交额。

    该字段主要供工程层/兼容接口使用；最终快照仍会从全市场重新计算一次，避免候选子集污染。
    """
    cols=[c for c in ['trade_date','l1_code','ts_code','ret5','amount','pct_chg','ret1','close'] if c in d]
    x=d[cols].copy();x['_orig_index']=d.index.to_numpy();x['trade_date']=pd.to_datetime(x['trade_date']).dt.normalize()
    pct_src=x['pct_chg'] if 'pct_chg' in x else (x['ret1'] if 'ret1' in x else pd.Series(0.0,index=x.index))
    ret5_src=x['ret5'] if 'ret5' in x else pd.Series(-999.0,index=x.index)
    amount_src=x['amount'] if 'amount' in x else pd.Series(0.0,index=x.index)
    x['_pct']=pd.to_numeric(pct_src,errors='coerce').fillna(0)
    x['_ret5']=pd.to_numeric(ret5_src,errors='coerce').fillna(-999)
    x['_amount']=pd.to_numeric(amount_src,errors='coerce').fillna(0)
    x['_is_lu']=False;x['_streak']=0
    if current_streaks is None:
        x=merge_verified_limits(x,limits)
        x['_is_lu']=x['is_limit_up']
        x=x.sort_values(['ts_code','trade_date'])
        vals=[]
        for _,g in x.groupby('ts_code',sort=False):
            cur=0
            for idx,row in g.iterrows():
                cur=cur+1 if bool(row['_is_lu']) else 0;vals.append((idx,cur))
        x['_streak']=pd.Series(dict(vals))
    else:
        # The user-selected reference replaces historical market rolls only.
        # Current industry position still uses the entire observed T universe.
        x=x.merge(current_streaks[['ts_code','trade_date','board_streak','is_limit_up']],
                  on=['ts_code','trade_date'],how='inner',validate='one_to_one')
        x['_is_lu']=x['is_limit_up'];x['_streak']=x['board_streak']
    x=x.sort_values(['trade_date','l1_code','_streak','_is_lu','_pct','_ret5','_amount','ts_code'],
                    ascending=[True,True,False,False,False,False,False,True])
    x['_rank']=x.groupby(['trade_date','l1_code']).cumcount()+1
    out=pd.Series(x['_rank'].to_numpy(),index=x['_orig_index'].to_numpy(),dtype=float)
    return out.reindex(d.index)


def build_candidate_feature_table(*,daily:pd.DataFrame,daily_basic:pd.DataFrame,top_list:pd.DataFrame,top_inst:pd.DataFrame,
                                  sw_members:pd.DataFrame,stock_basic:pd.DataFrame,st_status:pd.DataFrame,limits:pd.DataFrame,
                                  index_daily:pd.DataFrame|None=None,adj_factor:pd.DataFrame|None=None,
                                  historical_basic:pd.DataFrame|None=None,event_features:pd.DataFrame|None=None,
                                  recovery_confirm_days:int=2,selected_codes=None,selected_trade_date=None,
                                  current_streaks=None,reference_market=None)->pd.DataFrame:
    seeds = None if selected_codes is None else _selected_seeds(
        selected_codes, selected_trade_date, daily, daily_basic, stock_basic)
    # Validate before expensive features; absence never means ordinary/non-limit.
    reference_mode=current_streaks is not None or reference_market is not None
    if reference_mode:
        if seeds is None or current_streaks is None or reference_market is None:
            raise ValueError('user_reference_requires_selected_current_market_evidence')
        current=daily[pd.to_datetime(daily.trade_date).eq(pd.Timestamp(selected_trade_date))]
        merge_verified_limits(current,limits)
    else:
        merge_verified_limits(daily,limits)
    attach_pit_risk(seeds if seeds is not None else top_list[['trade_date','ts_code']].drop_duplicates(),st_status,historical_basic,stock_basic)
    sf=build_stock_daily_features(daily,daily_basic,adj_factor=adj_factor)
    sf=map_industry_point_in_time(sf,sw_members)
    sf['sector_core_rank']=_event_core_rank(sf,limits,current_streaks)
    sec=build_sector_daily_features(sf)
    trade_dates=sorted(pd.to_datetime(sf['trade_date']).dropna().unique())
    if reference_mode:
        today=top_list[pd.to_datetime(top_list.trade_date).eq(pd.Timestamp(selected_trade_date))]
        if today.ts_code.isin(selected_codes).any():
            raise ValueError('user_reference_listed_candidate_requires_full_capital_path')
    lhb=(_empty_lhb_table() if reference_mode or (seeds is not None and top_list.empty and top_inst.empty)
         else assign_lifecycle(aggregate_lhb(top_list,top_inst,daily), trade_dates=trade_dates))
    if not reference_mode and top_inst is not None and len(top_inst):
        # 席位标签使用与个股技术特征相同的连续价格尺度，避免除权送转把3/5/10日结果污染。
        sq=build_mature_seat_quality(top_inst,sf,trade_dates=trade_dates)
        lhb=attach_event_seat_quality(lhb,top_inst,sq)
    market=(reference_market if reference_mode else
            build_market_features(sf,limits,index_daily,recovery_confirm_days=recovery_confirm_days))
    e=lhb.merge(sf,on=['trade_date','ts_code'],how='left',suffixes=('','_stock'))
    # 资金推动弹性：使用同日龙虎榜样本内的净买/自由流通市值横截面百分位，
    # 只表达相对推动能力，不把某个绝对市值阈值硬编码为“越小越好”。
    ff=pd.to_numeric(e.get('effective_free_mcap'),errors='coerce') if 'effective_free_mcap' in e else pd.Series(np.nan,index=e.index)
    e['lhb_net_free_float_ratio']=pd.to_numeric(e.get('lhb_net_buy'),errors='coerce')/ff.replace(0,np.nan)
    e['lhb_net_free_float_pctile']=e.groupby('trade_date')['lhb_net_free_float_ratio'].rank(pct=True)
    if seeds is not None:
        # Calculate all reference percentiles before selecting the user's rows.
        selected = seeds.merge(e,on=['trade_date','ts_code'],how='left',validate='one_to_one',indicator='_lhb_merge')
        selected['lhb_listed'] = selected.pop('_lhb_merge').eq('both')
        absent = ~selected['lhb_listed']
        if absent.any():
            complete = {pd.Timestamp(d).normalize() for d in top_list.attrs.get('verified_complete_dates', [])}
            if pd.Timestamp(selected_trade_date).normalize() not in complete:
                raise ValueError('selected_lhb_absence_requires_verified_complete_date')
        reference = seeds.merge(sf,on=['trade_date','ts_code'],how='left',validate='one_to_one')
        for col in sf.columns.difference(['trade_date','ts_code']):
            selected.loc[absent, col] = reference.loc[absent, col]
            # A left join with absent events promotes bool to object; restore
            # logical negation semantics before the risk expressions below.
            if pd.api.types.is_bool_dtype(reference[col]):
                selected[col] = selected[col].astype(bool)
        selected['lhb_absence_verified'] = absent
        e = selected
    sec_cols=['trade_date','l1_code','sector_ret1','sector_ret5','sector_rs_5d_pctile','sector_ret1_pctile','sector_activity_pctile']
    e=e.merge(sec[sec_cols],on=['trade_date','l1_code'],how='left')
    market_cols=['trade_date','market_state','market_permission','raw_market_permission','market_data_quality','index_extreme_up','turnover_extreme']
    e=e.merge(market[market_cols],on='trade_date',how='left')

    sb=stock_basic.copy(); sb['list_date']=pd.to_datetime(sb['list_date'],errors='coerce'); sb['delist_date']=pd.to_datetime(sb.get('delist_date'),errors='coerce') if 'delist_date' in sb else pd.NaT
    e=e.merge(sb[[c for c in ['ts_code','name','exchange','market','list_date','delist_date'] if c in sb]],on='ts_code',how='left')
    cal=pd.DatetimeIndex(trade_dates).normalize().sort_values()
    def _list_sessions(r):
        ld=pd.Timestamp(r['list_date']).normalize() if pd.notna(r['list_date']) else pd.NaT
        td=pd.Timestamp(r['trade_date']).normalize()
        if pd.isna(ld): return 0
        if len(cal) and ld<cal[0]: return 20+int(cal.searchsorted(td,side='right'))
        return int(cal.searchsorted(td,side='right')-cal.searchsorted(ld,side='left'))
    e['list_days']=e.apply(_list_sessions,axis=1)

    e=attach_pit_risk(e,st_status,historical_basic,stock_basic)

    if 'reason' in top_list:
        rs=top_list.copy(); rs['trade_date']=pd.to_datetime(rs['trade_date']); reason=rs.groupby(['trade_date','ts_code'])['reason'].apply(lambda x:'|'.join(map(str,x))).rename('reason_text').reset_index(); e=e.merge(reason,on=['trade_date','ts_code'],how='left')
    else: e['reason_text']=''
    sf2=sf.sort_values(['ts_code','trade_date']).copy(); sf2['ret3']=sf2.groupby('ts_code')['signal_close' if 'signal_close' in sf2 else 'close'].pct_change(3); sf2['amount_ratio']=sf2['amount']/sf2.groupby('ts_code')['amount'].transform(lambda x:x.shift(1).rolling(20,min_periods=10).median())
    sf2['ret3p']=sf2.groupby('trade_date')['ret3'].rank(pct=True); sf2['amountp']=sf2.groupby('trade_date')['amount_ratio'].rank(pct=True)
    e=e.merge(sf2[['trade_date','ts_code','ret3p','amountp']],on=['trade_date','ts_code'],how='left')
    e['three_day_surge_high_climax']=(e['ret3p']>=.95)&(e['amountp']>=.95)&(e['close_location_day']>=.8)
    e['extreme_volume_inst_sell_weak_relay']=(e['amountp']>=.95)&(e['inst_net_buy_ratio']<0)&(e['lhb_net_buy_ratio']<=0)
    e['downward_anomaly_without_reversal']=e['reason_text'].astype(str).str.contains('跌幅|下跌',na=False)&(~e['close_above_ma20'])
    # 风险/事件模块只接受可审计、带公开时间戳的外部特征。没有数据时保持中性，绝不由语言模型临场补分。
    e['risk_penalty']=0.0; e['severe_negative_event']=False
    e['independent_catalyst']=False; e['catalyst_quality']=np.nan; e['catalyst_public_before_cutoff']=False
    e['theme_code']='__UNKNOWN_THEME__'; e['theme_verified']=False
    if event_features is not None and len(event_features):
        ev=normalize_event_features(event_features)
        need={'trade_date','ts_code','public_time'}
        miss=need-set(ev.columns)
        if miss: raise ValueError('event_features缺字段:'+','.join(sorted(miss)))
        ev['trade_date']=pd.to_datetime(ev['trade_date'],errors='coerce').dt.normalize()
        ev['public_time']=pd.to_datetime(ev['public_time'],errors='coerce',utc=True)
        if ev['trade_date'].isna().any() or ev['public_time'].isna().any():
            raise ValueError('event_features存在无法解析的trade_date/public_time')
        # 兼容直接调用工程层：事件发布时间的上海交易日不得晚于其标注trade_date。
        local_day=ev['public_time'].dt.tz_convert('Asia/Shanghai').dt.tz_localize(None).dt.normalize()
        ev=ev[local_day<=ev['trade_date']].copy()
        if len(ev):
            def _agg(g):
                independent=g['independent_catalyst'].eq(True)
                q=pd.to_numeric(g.loc[independent,'catalyst_quality'],errors='coerce') if 'catalyst_quality' in g else pd.Series(dtype=float)
                rp=pd.to_numeric(g.get('risk_penalty'),errors='coerce') if 'risk_penalty' in g else pd.Series(dtype=float)
                return pd.Series({
                    'ev_independent':bool(g.get('independent_catalyst',pd.Series(False,index=g.index)).fillna(False).astype(bool).any()),
                    'ev_quality':float(q.max()) if len(q.dropna()) else np.nan,
                    'ev_severe':bool(g.get('severe_negative_event',pd.Series(False,index=g.index)).fillna(False).astype(bool).any()),
                    'ev_risk':float(rp.max()) if len(rp.dropna()) else 0.0,
                    'ev_public':True,
                })
            ea=ev.groupby(['trade_date','ts_code'],as_index=False).apply(_agg,include_groups=False).reset_index()
            keep=[c for c in ['trade_date','ts_code','ev_independent','ev_quality','ev_severe','ev_risk','ev_public'] if c in ea]
            if {'trade_date','ts_code'}<=set(keep):
                e=e.merge(ea[keep],on=['trade_date','ts_code'],how='left')
                e['independent_catalyst']=e.get('ev_independent',False).fillna(False).astype(bool)
                e['catalyst_quality']=pd.to_numeric(e.get('ev_quality'),errors='coerce')
                e['severe_negative_event']=e.get('ev_severe',False).fillna(False).astype(bool)
                e['risk_penalty']=pd.to_numeric(e.get('ev_risk'),errors='coerce').fillna(0).clip(0,1)
                e['catalyst_public_before_cutoff']=e.get('ev_public',False).fillna(False).astype(bool)
    # 题材只接受独立的历史时点theme_members管线；事件文本/事件表不得暗中生成题材加分。
    if 'seat_quality_pctile' not in e: e['seat_quality_pctile']=np.nan
    if 'seat_quality_samples' not in e: e['seat_quality_samples']=0

    # 盘后板块退潮：与延迟分支使用同一可复现口径，修复此前字段从未生成导致否决失效的问题。
    e['sector_is_ebb']=(pd.to_numeric(e['sector_rs_5d_pctile'],errors='coerce')<.30)&(pd.to_numeric(e['sector_ret5'],errors='coerce')<0)
    # 高潮风险必须同时属于“指数单日极端上涨+成交极端+本板块单日集体强+个股加速”，不再用全市场情绪替代个股加速。
    e['market_climax']=(e['index_extreme_up'].fillna(False)&e['turnover_extreme'].fillna(False)&
                        (pd.to_numeric(e['sector_ret1_pctile'],errors='coerce')>=.90)&
                        (pd.to_numeric(e['ret3p'],errors='coerce')>=.95)&(pd.to_numeric(e['close_location_day'],errors='coerce')>=.80))

    required=['close','amount','l1_code','sector_rs_5d_pctile','market_permission']
    missing=e[required].isna().any(axis=1)
    if adj_factor is not None and len(adj_factor):missing=missing|e['adj_factor'].isna()
    # 席位结构是必审证据；明细缺失不能被误当成“净买0”。
    if 'seat_detail_available' in e:
        applicable=e['lhb_listed'] if 'lhb_listed' in e else pd.Series(True,index=e.index)
        missing=missing|(applicable & ~e['seat_detail_available'].fillna(False).astype(bool))
    missing=missing|(e['market_data_quality'].fillna('insufficient')=='insufficient')
    e['data_quality']=np.where(missing,'insufficient','normal')
    # 保留评分所需数据在占位前的缺失证据；关键行情硬门槛与可降级评分分开。
    score_sources={
        'rs_20d_pctile':['rs_20d_pctile'], 'ma20_slope_pctile':['ma20_slope_pctile'],
        'breakout_20d_strength':['breakout_20d_strength'], 'close_location':['high','low','close'],
        'volume_health':['vol_ratio20','volume_health'], 'startup_location_health':['loc60'],
        'close_above_ma20':['ma20'], 'ma5_gt_ma10_gt_ma20':['ma5','ma10','ma20'],
        'ma20_gt_ma60':['ma20','ma60'], 'sector_rs_5d_pctile':['sector_rs_5d_pctile'],
        'sector_activity_pctile':['sector_activity_pctile'], 'turnover_rate_pctile':['turnover_rate_pctile'],
        'free_mcap_pctile':['free_mcap_pctile'], 'lhb_net_free_float_pctile':['lhb_net_free_float_pctile'],
        'lhb_net_impact_pctile':['lhb_net_impact_pctile'], 'lhb_participation_pctile':['lhb_participation_pctile'],
        'inst_net_impact_pctile':['inst_net_impact_pctile'], 'broker_net_impact_pctile':['broker_net_impact_pctile'],
        'buy_sell_balance':['buy_sell_balance'],
    }
    absent={name:~np.isfinite(e.reindex(columns=cols).apply(pd.to_numeric,errors='coerce')).all(axis=1)
            for name,cols in score_sources.items()}
    if 'capital_observation_protocol' in e:
        from .disclosed_sides import PROTOCOL
        use=e['capital_observation_protocol'].eq(PROTOCOL)
        for old,new in [('inst_net_impact_pctile','institution_disclosed_impact_pctile'),
                        ('broker_net_impact_pctile','broker_disclosed_impact_pctile'),
                        ('buy_sell_balance','disclosed_buy_sell_balance')]:
            absent[old]=absent[old]&~use
            absent[new]=use&~np.isfinite(pd.to_numeric(e.get(new,pd.Series(float('nan'),index=e.index)),errors='coerce'))
    e['missing_score_features']=[[name for name,bad in absent.items() if bool(bad.loc[idx])] for idx in e.index]
    e['score_data_quality']=np.where(e['missing_score_features'].map(bool),'insufficient','normal')
    return e


def to_candidate_features(row)->CandidateFeatures:
    def g(k,default=None):
        v=row[k] if k in row.index else default
        return default if pd.isna(v) else v
    return CandidateFeatures(
        trade_date=pd.Timestamp(g('trade_date')).strftime('%Y-%m-%d'), ts_code=str(g('ts_code')), name=str(g('name','')),
        exchange=str(g('exchange','')),board=str(g('market','')),list_days=int(g('list_days',0)),is_st=bool(g('is_st',False)),is_delisting_arrangement=bool(g('is_delisting_arrangement',False)),data_quality=str(g('data_quality','insufficient')),
        market_state=str(g('market_state','震荡可做')),market_permission=str(g('market_permission','暂停')),market_climax=bool(g('market_climax',False)),
        sector_code=str(g('l1_code','')),theme_code=str(g('theme_code','__UNKNOWN_THEME__')),theme_verified=bool(g('theme_verified',False)),sector_rs_5d_pctile=float(g('sector_rs_5d_pctile',0)),sector_activity_pctile=float(g('sector_activity_pctile',0)),sector_core_rank=int(g('sector_core_rank',99)),sector_is_ebb=bool(g('sector_is_ebb',False)),
        independent_catalyst=bool(g('independent_catalyst',False)),catalyst_quality=g('catalyst_quality',None),catalyst_public_before_cutoff=bool(g('catalyst_public_before_cutoff',False)),
        rs_20d_pctile=float(g('rs_20d_pctile',0)),ma20_slope_pctile=float(g('ma20_slope_pctile',0)),close_above_ma20=bool(g('close_above_ma20',False)),ma5_gt_ma10_gt_ma20=bool(g('ma5_gt_ma10_gt_ma20',False)),ma20_gt_ma60=bool(g('ma20_gt_ma60',False)),
        breakout_20d_strength=float(g('breakout_20d_strength',0)),close_location_day=float(g('close_location_day',.5)),volume_health=float(g('volume_health',0)),startup_location_health=float(g('startup_location_health',0)),
        turnover_rate_pctile=float(g('turnover_rate_pctile',.5)),free_mcap_pctile=float(g('free_mcap_pctile',.5)),lhb_net_free_float_pctile=float(g('lhb_net_free_float_pctile',.5)),
        lhb_net_buy_ratio=float(g('lhb_net_buy_ratio',0)),lhb_net_impact_pctile=float(g('lhb_net_impact_pctile',0)),lhb_participation_pctile=float(g('lhb_participation_pctile',0)),
        inst_net_buy_ratio=float(g('inst_net_buy_ratio',0)),inst_net_impact_pctile=float(g('inst_net_impact_pctile',0)),broker_net_buy_ratio=float(g('broker_net_buy_ratio',0)),broker_net_impact_pctile=float(g('broker_net_impact_pctile',0)),buy_sell_balance=float(g('buy_sell_balance',0)),
        lifecycle_event_no=int(g('lifecycle_event_no',1)),lifecycle_net_improving=bool(g('lifecycle_net_improving',False)),seat_quality_pctile=g('seat_quality_pctile',None),seat_quality_samples=int(g('seat_quality_samples',0)),risk_penalty=float(g('risk_penalty',0)),
        downward_anomaly_without_reversal=bool(g('downward_anomaly_without_reversal',False)),three_day_surge_high_climax=bool(g('three_day_surge_high_climax',False)),extreme_volume_inst_sell_weak_relay=bool(g('extreme_volume_inst_sell_weak_relay',False)),severe_negative_event=bool(g('severe_negative_event',False)),
        extra={'amount':float(g('amount',0)),'t_close':float(g('close',0)),'lhb_low':float(g('low',0)),'atr14':float(g('atr14',0)),
               'theme_code':str(g('theme_code','__UNKNOWN_THEME__')),'theme_verified':bool(g('theme_verified',False))}
    )
