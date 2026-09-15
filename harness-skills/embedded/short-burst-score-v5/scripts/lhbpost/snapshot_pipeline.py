from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd
from .candidate_pipeline import build_candidate_feature_table
from .features import build_stock_daily_features, map_industry_point_in_time, rolling_pctile_last
from .market_features import build_market_features
from .utils import normalize_event_features
from .pit_risk_guard import merge_verified_limits


def _pct(v):
    try:
        x=float(v)
        return None if not np.isfinite(x) else x*100.0
    except Exception:return None


def _finite_or(v, default=0.0):
    try:
        x=float(v)
        return x if np.isfinite(x) else default
    except (TypeError,ValueError):
        return default


def _cut(df:pd.DataFrame|None, td:pd.Timestamp, *, date_col:str='trade_date')->pd.DataFrame|None:
    """物理截断到T日，防止下游任何新代码意外读取未来行。"""
    if df is None:return None
    x=df.copy()
    if len(x) and date_col in x:
        x[date_col]=pd.to_datetime(x[date_col],errors='coerce').dt.normalize()
        x=x[x[date_col].notna()&(x[date_col]<=td)].copy()
    if 'disclosed_sides' in x.attrs:
        # Source completeness was checked before this cut. Attached evidence must
        # obey the same physical boundary as rows, including an empty top_inst.
        rows=x.attrs['disclosed_sides']
        if not isinstance(rows,list):raise ValueError('invalid_disclosed_side_attachment')
        retained=[]
        for row in rows:
            if not isinstance(row,dict) or 'trade_date' not in row:
                raise ValueError('disclosed_side_attachment_date_missing')
            date=pd.to_datetime(str(row['trade_date']),errors='coerce')
            if pd.isna(date):raise ValueError('invalid_disclosed_side_attachment_date')
            if date.normalize()<=td:retained.append(dict(row))
        x.attrs['disclosed_sides']=retained
    return x


def _compute_streaks(daily: pd.DataFrame, limits: pd.DataFrame) -> pd.DataFrame:
    x=merge_verified_limits(daily,limits)
    x=x.sort_values(['ts_code','trade_date'])
    vals=[]
    for _,g in x.groupby('ts_code',sort=False):
        cur=0
        for idx,row in g.iterrows():
            cur=cur+1 if bool(row['is_limit_up']) else 0
            vals.append((idx,cur))
    st=pd.Series({i:v for i,v in vals},name='board_streak')
    x=x.join(st)
    x['market_height_rank']=x.groupby('trade_date')['board_streak'].rank(method='dense',ascending=False).fillna(99).astype(int)
    return x[['trade_date','ts_code','board_streak','market_height_rank','is_limit_up','is_limit_down','up_limit','down_limit']]


def _group_snapshot(sf:pd.DataFrame, streak:pd.DataFrame, group_code:str, group_name:str)->pd.DataFrame:
    """行业/题材统一的盘后群体状态。"""
    x=sf.merge(streak[['trade_date','ts_code','board_streak','is_limit_up']],on=['trade_date','ts_code'],how='left')
    x=x[x[group_code].notna()].copy()
    if x.empty:return pd.DataFrame()
    if 'pct_chg' not in x:
        x=x.sort_values(['ts_code','trade_date']); x['pct_chg']=x.groupby('ts_code')['signal_close'].pct_change()
    market=x.groupby('trade_date').agg(mkt_ret3=('ret3','median'),mkt_ret5=('ret5','median')).reset_index()
    x=x.merge(market,on='trade_date',how='left')
    x['is_up']=pd.to_numeric(x['pct_chg'],errors='coerce')>0
    def agg(g):
        r3=pd.to_numeric(g['ret3'],errors='coerce').median(); r5=pd.to_numeric(g['ret5'],errors='coerce').median()
        return pd.Series({
            'member_count':int(g['ts_code'].nunique()),
            'day_change_pct':float(pd.to_numeric(g['pct_chg'],errors='coerce').median()*100),
            'up_ratio':float(g['is_up'].mean()),
            'limit_up_count':int(g['is_limit_up'].fillna(False).sum()),
            'two_plus_board_count':int((pd.to_numeric(g['board_streak'],errors='coerce').fillna(0)>=2).sum()),
            'rel_strength_3d':float((r3-pd.to_numeric(g['mkt_ret3'],errors='coerce').median())*100) if pd.notna(r3) else 0.0,
            'rel_strength_5d':float((r5-pd.to_numeric(g['mkt_ret5'],errors='coerce').median())*100) if pd.notna(r5) else 0.0,
            'leader_advanced':bool((pd.to_numeric(g['board_streak'],errors='coerce').fillna(0)>=2).any()),
        })
    out=x.groupby(['trade_date',group_code],as_index=False).apply(agg,include_groups=False)
    if isinstance(out.index,pd.MultiIndex):out=out.reset_index()
    # 兼容部分pandas版本groupby.apply输出列。
    if group_name in x and group_name not in out:
        names=x[['trade_date',group_code,group_name]].drop_duplicates(['trade_date',group_code])
        out=out.merge(names,on=['trade_date',group_code],how='left')
    return out


def _short_term_core_rank(sf:pd.DataFrame, streak:pd.DataFrame, group_code:str, suffix:str)->pd.DataFrame:
    """短线地位：连板高度→是否涨停→当日涨幅→5日强度→成交额，避免只按5日涨幅误判核心。"""
    x=sf.merge(streak[['trade_date','ts_code','board_streak','is_limit_up']],on=['trade_date','ts_code'],how='left')
    x=x[x[group_code].notna()].copy()
    x['_pct']=pd.to_numeric(x.get('pct_chg'),errors='coerce').fillna(0)
    x['_ret5']=pd.to_numeric(x.get('ret5'),errors='coerce').fillna(-999)
    x['_amount']=pd.to_numeric(x.get('amount'),errors='coerce').fillna(0)
    x=x.sort_values(['trade_date',group_code,'board_streak','is_limit_up','_pct','_ret5','_amount','ts_code'],
                    ascending=[True,True,False,False,False,False,False,True])
    x[f'{suffix}_core_rank']=x.groupby(['trade_date',group_code]).cumcount()+1
    x[f'{suffix}_amount_rank']=x.groupby(['trade_date',group_code])['_amount'].rank(method='min',ascending=False)
    return x[['trade_date','ts_code',group_code,f'{suffix}_core_rank',f'{suffix}_amount_rank']]


def _map_theme_pit(sf:pd.DataFrame, theme_members:pd.DataFrame|None)->pd.DataFrame:
    if theme_members is None or theme_members.empty:return pd.DataFrame()
    req={'ts_code','theme_code','in_date'}
    if not req.issubset(theme_members.columns):return pd.DataFrame()
    m=theme_members.copy();m['in_date']=pd.to_datetime(m['in_date'],errors='coerce').dt.normalize()
    m['out_date']=pd.to_datetime(m.get('out_date'),errors='coerce').dt.normalize() if 'out_date' in m else pd.NaT
    m['out_date']=m['out_date'].fillna(pd.Timestamp('2099-12-31'))
    use=[c for c in ['ts_code','theme_code','theme_name','in_date','out_date'] if c in m]
    z=sf.merge(m[use],on='ts_code',how='inner')
    z=z[(z['trade_date']>=z['in_date'])&(z['trade_date']<=z['out_date'])].copy()
    return z


def _best_theme_for_day(theme_sf:pd.DataFrame, theme_ctx:pd.DataFrame, theme_rank:pd.DataFrame, td:pd.Timestamp)->pd.DataFrame:
    if theme_sf.empty or theme_ctx.empty:return pd.DataFrame()
    mem=theme_sf[theme_sf['trade_date'].dt.normalize()==td][['ts_code','theme_code']+[c for c in ['theme_name'] if c in theme_sf]].drop_duplicates()
    ctx=theme_ctx[theme_ctx['trade_date'].dt.normalize()==td].copy()
    z=mem.merge(ctx,on=['trade_date','theme_code'],how='left') if 'trade_date' in mem else None
    if z is None:
        mem['trade_date']=td;z=mem.merge(ctx,on=['trade_date','theme_code'],how='left')
    tr=theme_rank[theme_rank['trade_date'].dt.normalize()==td]
    z=z.merge(tr[['trade_date','ts_code','theme_code','theme_core_rank','theme_amount_rank']],on=['trade_date','ts_code','theme_code'],how='left')
    # 只考虑至少5个成分的题材，防止微型标签制造“强题材”。
    z=z[pd.to_numeric(z.get('member_count'),errors='coerce').fillna(0)>=5].copy()
    if z.empty:return z
    sort_cols=['ts_code','two_plus_board_count','limit_up_count','rel_strength_5d','up_ratio','day_change_pct','theme_core_rank','theme_code']
    z=z.sort_values(sort_cols,ascending=[True,False,False,False,False,False,True,True])
    return z.drop_duplicates('ts_code',keep='first')


def _market_snapshot(sf:pd.DataFrame, streak:pd.DataFrame, limits:pd.DataFrame, index_daily:pd.DataFrame|None,
                     trade_date:pd.Timestamp, full_market:pd.DataFrame|None)->dict[str,Any]:
    d=sf[sf['trade_date'].dt.normalize()==trade_date].merge(streak,on=['trade_date','ts_code'],how='left')
    pct=pd.to_numeric(d.get('pct_chg'),errors='coerce')
    up=int((pct>0).sum()); down=int((pct<0).sum()); flat=int((pct==0).sum())
    lu=int(d['is_limit_up'].fillna(False).sum()); ld=int(d['is_limit_down'].fillna(False).sum())
    broken=int(((pd.to_numeric(d['high'],errors='coerce')>=pd.to_numeric(d['up_limit'],errors='coerce')-1e-8)&~d['is_limit_up'].fillna(False)).sum())
    total=float(pd.to_numeric(d['amount'],errors='coerce').sum())
    dates=pd.DatetimeIndex(sorted(sf['trade_date'].dt.normalize().unique()))
    pos=dates.searchsorted(trade_date)
    prev_total=None; prev_lu_ret=None
    if pos>0 and pos<len(dates) and pd.Timestamp(dates[pos])==trade_date:
        prev_date=pd.Timestamp(dates[pos-1])
        prev=sf[sf['trade_date'].dt.normalize()==prev_date]
        prev_total=float(pd.to_numeric(prev['amount'],errors='coerce').sum())
        prev_lu=streak[(streak['trade_date']==prev_date)&streak['is_limit_up'].fillna(False)]['ts_code'].astype(str)
        if len(prev_lu):
            cur_ret=sf[(sf['trade_date'].dt.normalize()==trade_date)&sf['ts_code'].astype(str).isin(set(prev_lu))]
            if len(cur_ret):prev_lu_ret=float(pd.to_numeric(cur_ret['pct_chg'],errors='coerce').median()*100)
    change=(total/prev_total-1)*100 if prev_total and prev_total>0 else 0.0
    idx={}
    if index_daily is not None and len(index_daily):
        ix=index_daily.copy();ix['trade_date']=pd.to_datetime(ix['trade_date']).dt.normalize();cur=ix[ix['trade_date']==trade_date]
        if len(cur):
            for _,r in cur.iterrows():
                v=r.get('pct_chg')
                if pd.notna(v):idx[str(r.get('ts_code'))]=float(v)*100.0
    out={'up_count':up,'down_count':down,'flat_count':flat,'limit_up_count':lu,'limit_down_count':ld,'broken_limit_up_count':broken,
         'turnover_total':total,'turnover_change_pct':change,'index_changes':idx,'prev_limit_up_avg_return':prev_lu_ret,
         'source_time':trade_date.strftime('%Y-%m-%d')+'T18:00:00+08:00'}
    if full_market is not None and len(full_market):
        q=full_market[pd.to_datetime(full_market['trade_date']).dt.normalize()==trade_date]
        if len(q):
            r=q.iloc[-1]
            out['causal_market']={
                'state':str(r.get('market_state','')),
                'permission':str(r.get('market_permission','')),
                'raw_permission':str(r.get('raw_market_permission','')),
                'data_quality':str(r.get('market_data_quality','insufficient')),
                'composite':None if pd.isna(r.get('market_composite')) else float(r.get('market_composite')),
                'breadth_pctile':None if pd.isna(r.get('breadth_pctile')) else float(r.get('breadth_pctile')),
                'sentiment_pctile':None if pd.isna(r.get('sentiment_pctile')) else float(r.get('sentiment_pctile')),
                'trend_pctile':None if pd.isna(r.get('trend_pctile')) else float(r.get('trend_pctile')),
                'liquidity_pctile':None if pd.isna(r.get('liquidity_pctile')) else float(r.get('liquidity_pctile')),
                'risk_pctile':None if pd.isna(r.get('risk_pctile')) else float(r.get('risk_pctile')),
                'divergence_pctile':None if pd.isna(r.get('divergence_pctile')) else float(r.get('divergence_pctile')),
                'improvement':None if pd.isna(r.get('improvement')) else float(r.get('improvement')),
                'model':'causal_rolling_market_v5.0'
            }
    return out


def _validate_current_streaks(daily, limits, current_streaks, td):
    required={'ts_code','trade_date','board_streak','market_height_rank','is_limit_up','is_limit_down','up_limit','down_limit'}
    if not isinstance(current_streaks,pd.DataFrame) or not required.issubset(current_streaks):
        raise ValueError('current_streaks_schema_invalid')
    x=current_streaks.copy();x['trade_date']=pd.to_datetime(x.trade_date).dt.normalize()
    if x.empty or not x.trade_date.eq(td).all() or x.duplicated(['ts_code','trade_date']).any():
        raise ValueError('current_streaks_date_or_duplicate')
    observed=merge_verified_limits(daily[pd.to_datetime(daily.trade_date).dt.normalize().eq(td)],limits)
    if set(x.ts_code)!=set(observed.ts_code):raise ValueError('current_streaks_reference_universe_not_exact')
    z=observed.merge(x,on=['ts_code','trade_date'],suffixes=('_raw','_evidence'),validate='one_to_one')
    from .pit_risk_guard import _bool
    for key in ('is_limit_up','is_limit_down'):
        x[key]=x[key].map(_bool)
        if not z[key+'_raw'].eq(z[key+'_evidence'].map(_bool)).all():
            raise ValueError('current_streaks_conflict_with_dated_limits')
    for key in ('up_limit','down_limit'):
        a=pd.to_numeric(z[key+'_raw'],errors='coerce');b=pd.to_numeric(z[key+'_evidence'],errors='coerce')
        if not ((a.isna()&b.isna())|((a-b).abs()<1e-8)).all():raise ValueError('current_streaks_limit_price_mismatch')
    heights=pd.to_numeric(x.board_streak,errors='raise')
    if not np.isfinite(heights).all() or (heights<0).any() or (heights%1!=0).any():
        raise ValueError('current_streaks_invalid_height')
    if not heights.gt(0).eq(x.is_limit_up).all():raise ValueError('current_streaks_height_conflict')
    expected=heights.rank(method='dense',ascending=False).astype(int)
    if not expected.eq(pd.to_numeric(x.market_height_rank,errors='raise')).all():
        raise ValueError('current_streaks_height_rank_conflict')
    return x


def _current_reference_market(sf, streak, limits, index_daily, td):
    """Original T gate and original climax inputs; no invented 120-day market values."""
    from .core import market_state,load_config
    raw=_market_snapshot(sf,streak,limits,index_daily,td,None)
    state,_=market_state(raw,load_config())
    totals=sf.groupby('trade_date').amount.sum().sort_index()
    liquidity=rolling_pctile_last(totals)
    turnover_extreme=bool(liquidity.loc[td]>=.9)
    index_extreme=False
    if index_daily is not None and len(index_daily):
        ix=index_daily.copy();ix['trade_date']=pd.to_datetime(ix.trade_date)
        ix=ix.sort_values(['ts_code','trade_date'])
        ix['ret1']=(pd.to_numeric(ix.pct_chg,errors='coerce') if 'pct_chg' in ix
                    else ix.groupby('ts_code').close.pct_change(fill_method=None))
        returns=ix.groupby('trade_date').ret1.median().sort_index()
        ranks=rolling_pctile_last(returns)
        if td in returns.index:index_extreme=bool(returns.loc[td]>0 and ranks.loc[td]>=.9)
    return pd.DataFrame([{'trade_date':td,'market_state':state,
        'market_permission':'用户指定历史参考','raw_market_permission':'原始宽度闸门',
        'market_data_quality':'user_reference','index_extreme_up':index_extreme,
        'turnover_extreme':turnover_extreme}])


def build_snapshot(*, trade_date:str, as_of:str, daily:pd.DataFrame, daily_basic:pd.DataFrame, top_list:pd.DataFrame,
                   top_inst:pd.DataFrame, sw_members:pd.DataFrame, stock_basic:pd.DataFrame, st_status:pd.DataFrame,
                   limits:pd.DataFrame, index_daily:pd.DataFrame|None=None, adj_factor:pd.DataFrame|None=None,
                   historical_basic:pd.DataFrame|None=None, event_features:pd.DataFrame|None=None,
                   theme_members:pd.DataFrame|None=None,selected_codes=None,
                   market_reference=None,current_streaks=None)->dict[str,Any]:
    """从原始盘后数据生成T日快照。

    与V4.1不同，本函数先物理截断所有可按交易日截断的数据，再执行完整市场→阶段→板块/题材→地位→
    透支→龙虎榜→事件链条；不会在快照层另走一条“简化市场模型”。
    """
    td=pd.Timestamp(trade_date).normalize(); cutoff=pd.Timestamp(as_of)
    if cutoff.tzinfo is None:raise ValueError('as_of必须带时区')
    local_cutoff=cutoff.tz_convert('Asia/Shanghai')
    if local_cutoff.date()!=td.date():raise ValueError('as_of日期必须等于trade_date')
    if local_cutoff.hour<15:raise ValueError('仅接受中国交易日收盘后的as_of')
    event_features=normalize_event_features(event_features)

    def require_cols(name,df,cols):
        if df is None: raise ValueError(f'{name}数据缺失')
        miss=set(cols)-set(df.columns)
        if miss: raise ValueError(f'{name}缺字段:{sorted(miss)}')

    # 生产关键数据在真正计算前再次做列级硬校验，避免只依赖外层审计。
    require_cols('daily',daily,{'ts_code','trade_date','open','high','low','close','amount'})
    require_cols('daily_basic',daily_basic,{'ts_code','trade_date'})
    require_cols('top_list',top_list,{'ts_code','trade_date'})
    require_cols('top_inst',top_inst,{'ts_code','trade_date'})
    require_cols('sw_members',sw_members,{'ts_code','l1_code','in_date','out_date'})
    require_cols('stock_basic',stock_basic,{'ts_code','name','list_date'})
    require_cols('stk_limit',limits,{'ts_code','trade_date','up_limit','down_limit'})
    if theme_members is not None and len(theme_members):
        require_cols('theme_members',theme_members,{'ts_code','theme_code','in_date','out_date'})
    if event_features is not None and len(event_features):
        require_cols('event_features',event_features,{'ts_code','trade_date','public_time'})
        pts=pd.to_datetime(event_features['public_time'],errors='coerce',utc=True)
        if pts.isna().any():raise ValueError('event_features存在无法解析的public_time；禁止用as_of代填')

    # 物理时间截断：即使数据目录已经包含T+1，也不允许下游看到。
    daily=_cut(daily,td);daily_basic=_cut(daily_basic,td);top_list=_cut(top_list,td);top_inst=_cut(top_inst,td)
    st_status=_cut(st_status,td);limits=_cut(limits,td);index_daily=_cut(index_daily,td);adj_factor=_cut(adj_factor,td)
    historical_basic=_cut(historical_basic,td);event_features=_cut(event_features,td)
    # PIT成员表不能简单按in_date<=T裁掉out_date，但未来in_date条目可安全删除。
    sw_members=sw_members.copy()
    if len(sw_members) and 'in_date' in sw_members:
        sw_members=sw_members[pd.to_datetime(sw_members['in_date'],errors='coerce').dt.normalize()<=td].copy()
    if theme_members is not None:
        theme_members=theme_members.copy()
        if len(theme_members) and 'in_date' in theme_members:
            theme_members=theme_members[pd.to_datetime(theme_members['in_date'],errors='coerce').dt.normalize()<=td].copy()
    if event_features is not None and len(event_features):
        # 强制统一UTC比较；缺失/坏时间已在上方硬失败，绝不把as_of冒充事件发布时间。
        pt=pd.to_datetime(event_features['public_time'],errors='raise',utc=True)
        co=pd.Timestamp(as_of).tz_convert('UTC')
        event_features=event_features[pt<=co].copy()
        event_features['public_time']=pt.loc[event_features.index]

    reference_mode=market_reference is not None or current_streaks is not None
    reference_market=None
    if reference_mode:
        if (not isinstance(market_reference,dict) or market_reference.get('mode')!='yearly-limit-close-premium'
                or selected_codes is None or current_streaks is None):
            raise ValueError('invalid_user_market_reference_mode')
        # The replacement concerns historical market reference. Current market
        # and industry position always retain the full Shanghai/Shenzhen set.
        daily=daily[daily.ts_code.str.endswith(('.SH','.SZ'))].copy()
        daily_basic=daily_basic[pd.to_datetime(daily_basic.trade_date).eq(td)].copy()
        sf=build_stock_daily_features(daily,daily_basic,adj_factor=adj_factor)
        sf['trade_date']=pd.to_datetime(sf.trade_date).dt.normalize()
        streak=_validate_current_streaks(daily,limits,current_streaks,td)
        reference_market=_current_reference_market(sf,streak,limits,index_daily,td)

    if top_list.empty and top_inst.empty and selected_codes is None:
        # 已审计的空龙虎榜快照代表零候选；市场分析仍必须完整运行。
        table=pd.DataFrame({'trade_date':pd.Series(dtype='datetime64[ns]'),
                            'ts_code':pd.Series(dtype='object'),'l1_code':pd.Series(dtype='object')})
    else:
        table=build_candidate_feature_table(daily=daily,daily_basic=daily_basic,top_list=top_list,top_inst=top_inst,
            sw_members=sw_members,stock_basic=stock_basic,st_status=st_status,limits=limits,index_daily=index_daily,
            adj_factor=adj_factor,historical_basic=historical_basic,event_features=event_features,
            selected_codes=selected_codes,selected_trade_date=trade_date if selected_codes is not None else None,
            current_streaks=streak if reference_mode else None,reference_market=reference_market)

    sf=build_stock_daily_features(daily,daily_basic,adj_factor=adj_factor);sf['trade_date']=pd.to_datetime(sf['trade_date']).dt.normalize()
    sf_pit=map_industry_point_in_time(sf,sw_members)
    if not reference_mode:streak=_compute_streaks(daily,limits)
    industry_ctx=_group_snapshot(sf_pit,streak,'l1_code','l1_name')
    industry_rank=_short_term_core_rank(sf_pit,streak,'l1_code','industry')
    full_market=(None if reference_mode else build_market_features(sf,limits,index_daily,recovery_confirm_days=2))

    theme_sf=_map_theme_pit(sf,theme_members)
    theme_ctx=_group_snapshot(theme_sf,streak,'theme_code','theme_name') if len(theme_sf) else pd.DataFrame()
    theme_rank=_short_term_core_rank(theme_sf,streak,'theme_code','theme') if len(theme_sf) else pd.DataFrame()
    best_theme=_best_theme_for_day(theme_sf,theme_ctx,theme_rank,td) if len(theme_sf) else pd.DataFrame()

    cur=table[pd.to_datetime(table['trade_date']).dt.normalize()==td].copy()
    cur=cur.merge(streak,on=['trade_date','ts_code'],how='left',suffixes=('','_streak'))
    if len(industry_ctx):cur=cur.merge(industry_ctx,on=['trade_date','l1_code'],how='left',suffixes=('','_industry'))
    if len(industry_rank):
        cur=cur.merge(industry_rank[['trade_date','ts_code','l1_code','industry_core_rank','industry_amount_rank']],
                      on=['trade_date','ts_code','l1_code'],how='left')
    if len(best_theme):
        # 列名加前缀，避免与行业上下文冲突。
        keep=['ts_code','theme_code']+[c for c in ['theme_name','theme_name_x','theme_name_y','member_count','day_change_pct','up_ratio','limit_up_count',
              'two_plus_board_count','rel_strength_3d','rel_strength_5d','leader_advanced','theme_core_rank','theme_amount_rank'] if c in best_theme]
        bt=best_theme[keep].drop_duplicates('ts_code').copy()
        # candidate_pipeline也可能带事件主题字段；PIT题材必须使用独立列名，禁止merge后被_x/_y静默吞掉。
        ren={'theme_code':'pit_theme_code','theme_name':'pit_theme_name','theme_name_x':'pit_theme_name','theme_name_y':'pit_theme_name'}
        ren.update({c:'theme_'+c for c in keep if c not in {'ts_code','theme_code','theme_name','theme_name_x','theme_name_y','theme_core_rank','theme_amount_rank'}})
        bt=bt.rename(columns=ren)
        # 若不同来源产生重复题材名列，只保留第一个非空值。
        if list(bt.columns).count('pit_theme_name')>1:
            cols=[i for i,c in enumerate(bt.columns) if c=='pit_theme_name']
            vals=bt.iloc[:,cols].bfill(axis=1).iloc[:,0]
            bt=bt.loc[:,~bt.columns.duplicated()].copy();bt['pit_theme_name']=vals
        cur=cur.merge(bt,on='ts_code',how='left')

    stocks=[]
    ti=top_inst.copy(); ti['trade_date']=pd.to_datetime(ti['trade_date']).dt.normalize() if len(ti) else pd.to_datetime([])
    ev=event_features.copy() if event_features is not None else pd.DataFrame()
    if len(ev):
        ev['trade_date']=pd.to_datetime(ev['trade_date']).dt.normalize()
        ev['public_time']=pd.to_datetime(ev['public_time'],errors='raise',utc=True)
    for _,r in cur.iterrows():
        code=str(r['ts_code']); l1=str(r.get('l1_name') or r.get('l1_code') or '')
        rep_reason=str(r.get('rep_reason') or '')
        buy1=0.0
        if len(ti):
            z=ti[(ti['trade_date']==td)&(ti['ts_code'].astype(str)==code)]
            if rep_reason and 'reason' in z:
                zz=z[z['reason'].astype(str).eq(rep_reason)]
                z=zz
            if len(z) and 'buy' in z:buy1=float(pd.to_numeric(z['buy'],errors='coerce').fillna(0).max())
        events=[]
        if len(ev):
            z=ev[(ev['trade_date']==td)&(ev['ts_code'].astype(str)==code)]
            for _,er in z.iterrows():
                risk=float(er.get('risk_penalty',0)) if pd.notna(er.get('risk_penalty',0)) else 0.; severe=bool(er.get('severe_negative_event',False))
                events.append({
                    'title':str(er.get('title') or er.get('event_type') or '盘后事件'),
                    'risk_level':'hard' if severe else ('medium' if risk>=.5 else ('low' if risk>0 else 'info')),
                    'risk_penalty':risk,
                    'public_time':er['public_time'].isoformat(),
                    'concept_denial':bool(er.get('concept_denial',False)),
                    'independent_catalyst':bool(er.get('independent_catalyst',False)),
                    'catalyst_quality':None if pd.isna(er.get('catalyst_quality')) else float(er.get('catalyst_quality')),
                })
        industry_metrics={k:(bool(r[k]) if k=='leader_advanced' else float(r[k]) if pd.notna(r.get(k)) else 0.0) for k in
                          ['member_count','day_change_pct','up_ratio','limit_up_count','two_plus_board_count','rel_strength_3d','rel_strength_5d','leader_advanced'] if k in r.index}
        theme_metrics={}
        for k in ['member_count','day_change_pct','up_ratio','limit_up_count','two_plus_board_count','rel_strength_3d','rel_strength_5d','leader_advanced']:
            col='theme_'+k
            if col in r.index and pd.notna(r.get(col)):theme_metrics[k]=bool(r[col]) if k=='leader_advanced' else float(r[col])
        list_days=int(r.get('list_days',0) or 0)
        new_unlimited=0<list_days<=5
        recent_ipo_immature=5<list_days<20
        prev20=float(r.get('prev20_high',np.nan)) if pd.notna(r.get('prev20_high')) else np.nan
        close=float(r.get('close',0) or 0)
        dist20=(close/prev20-1)*100 if np.isfinite(prev20) and prev20>0 else None
        atr14=float(r.get('atr14',np.nan)) if pd.notna(r.get('atr14')) else np.nan
        dist20_atr=(close-prev20)/atr14 if np.isfinite(prev20) and prev20>0 and np.isfinite(atr14) and atr14>0 else None
        free_mv=r.get('free_mv')
        stock={
            'code':code,'name':str(r.get('name') or code),'board':str(r.get('market') or r.get('exchange') or ''),
            'risk_warning':bool(r.get('is_st',False)),'delisting_risk':bool(r.get('is_delisting_arrangement',False)),
            'list_days':list_days,'new_unlimited':new_unlimited,'recent_ipo_immature':recent_ipo_immature,
            'data_quality':str(r.get('data_quality','normal')),
            'missing_score_features':list(r.get('missing_score_features',[])),
            'score_data_quality':str(r.get('score_data_quality','insufficient')),
            'change_pct':float(r.get('pct_chg',0))*100 if pd.notna(r.get('pct_chg')) else 0.0,
            'turnover':float(r.get('amount',0) or 0),'turnover_rate':_finite_or(r.get('turnover_rate')),
            'free_float_mcap':_finite_or(free_mv,None),
            'days_return':{'3':_pct(r.get('ret3')) or 0,'5':_pct(r.get('ret5')) or 0,'10':_pct(r.get('ret10')) or 0,'20':_pct(r.get('ret20')) or 0},
            'board_streak':int(r.get('board_streak',0) or 0),'market_height_rank':int(r.get('market_height_rank',99) or 99),
            'sector':l1,'industry_core_rank':int(r['industry_core_rank']) if pd.notna(r.get('industry_core_rank')) else 99,
            'industry_capacity_core':bool(float(r.get('industry_amount_rank',99) or 99)<=2),'industry_metrics':industry_metrics,
            'theme':str(r.get('pit_theme_name') or r.get('pit_theme_code') or ''),'theme_code':str(r.get('pit_theme_code') or ''),
            'theme_verified':bool(theme_metrics),'theme_core_rank':int(r.get('theme_core_rank',99) or 99) if pd.notna(r.get('theme_core_rank')) else 99,
            'theme_capacity_core':bool(float(r.get('theme_amount_rank',99) or 99)<=2) if pd.notna(r.get('theme_amount_rank')) else False,
            'theme_metrics':theme_metrics,
            'close_location':float(r.get('close_location_day',.5)) if pd.notna(r.get('close_location_day')) else .5,'volume_ratio20':_finite_or(r.get('vol_ratio20')),
            'distance_to_prev20_high_pct':dist20,'distance_to_prev20_high_atr':dist20_atr,
            'atr14':None if not np.isfinite(atr14) else atr14,'close_price':close,
            'breakout_20d_strength':_finite_or(r.get('breakout_20d_strength')),
            # V5.0真正进入短线爆发力评分的个股技术/量价/弹性特征。
            'rs_20d_pctile':float(r.get('rs_20d_pctile',.5) if pd.notna(r.get('rs_20d_pctile')) else .5),
            'ma20_slope_pctile':float(r.get('ma20_slope_pctile',.5) if pd.notna(r.get('ma20_slope_pctile')) else .5),
            'close_above_ma20':bool(r.get('close_above_ma20',False)),
            'ma5_gt_ma10_gt_ma20':bool(r.get('ma5_gt_ma10_gt_ma20',False)),
            'ma20_gt_ma60':bool(r.get('ma20_gt_ma60',False)),
            'volume_health':float(r.get('volume_health',.5) if pd.notna(r.get('volume_health')) else .5),
            'startup_location_health':float(r.get('startup_location_health',.5) if pd.notna(r.get('startup_location_health')) else .5),
            'turnover_rate_pctile':float(r.get('turnover_rate_pctile',.5) if pd.notna(r.get('turnover_rate_pctile')) else .5),
            'free_mcap_pctile':float(r.get('free_mcap_pctile',.5) if pd.notna(r.get('free_mcap_pctile')) else .5),
            'lhb_net_free_float_pctile':float(r.get('lhb_net_free_float_pctile',.5) if pd.notna(r.get('lhb_net_free_float_pctile')) else .5),
            'sector_rs_5d_pctile':float(r.get('sector_rs_5d_pctile',.5) if pd.notna(r.get('sector_rs_5d_pctile')) else .5),
            'sector_activity_pctile':float(r.get('sector_activity_pctile',.5) if pd.notna(r.get('sector_activity_pctile')) else .5),
            'lhb_net_impact_pctile':float(r.get('lhb_net_impact_pctile',.5) if pd.notna(r.get('lhb_net_impact_pctile')) else .5),
            'lhb_participation_pctile':float(r.get('lhb_participation_pctile',.5) if pd.notna(r.get('lhb_participation_pctile')) else .5),
            'inst_net_impact_pctile':float(r.get('inst_net_impact_pctile',.5) if pd.notna(r.get('inst_net_impact_pctile')) else .5),
            'broker_net_impact_pctile':float(r.get('broker_net_impact_pctile',.5) if pd.notna(r.get('broker_net_impact_pctile')) else .5),
            'buy_sell_balance':float(r.get('buy_sell_balance',0) if pd.notna(r.get('buy_sell_balance')) else 0),
            'independent_catalyst':bool(r.get('independent_catalyst',False)),
            'catalyst_quality':None if pd.isna(r.get('catalyst_quality')) else float(r.get('catalyst_quality')),
            'catalyst_public_before_cutoff':bool(r.get('catalyst_public_before_cutoff',False)),
            'market_climax':bool(r.get('market_climax',False)),
            'risk_penalty':float(r.get('risk_penalty',0) or 0),
            'downward_anomaly_without_reversal':bool(r.get('downward_anomaly_without_reversal',False)),
            'three_day_surge_high_climax':bool(r.get('three_day_surge_high_climax',False)),
            'extreme_volume_inst_sell_weak_relay':bool(r.get('extreme_volume_inst_sell_weak_relay',False)),
            'severe_negative_event':bool(r.get('severe_negative_event',False)),
            'broken_limit_weak_close':bool((not bool(r.get('is_limit_up',False))) and (float(r.get('close_location_day',.5)) if pd.notna(r.get('close_location_day')) else .5)<.45 and float(r.get('pct_chg',0) or 0)>0.03),
            'lhb':({
                'listed':True,'buy5':float(r.get('lhb_buy',0) or 0),'sell5':float(r.get('lhb_sell',0) or 0),'net_buy':float(r.get('lhb_net_buy',0) or 0),
                'buy1':buy1,'impact_denominator':float(r.get('impact_denominator',r.get('amount',0)) or 0),
                'window_type':str(r.get('window_type') or 'daily'),'trigger_reason':rep_reason,'all_reasons':str(r.get('all_reasons') or rep_reason),
                'daily_net_buy_ratio':None if pd.isna(r.get('daily_lhb_net_buy_ratio')) else float(r.get('daily_lhb_net_buy_ratio')),
                'three_day_net_buy_ratio':None if pd.isna(r.get('three_day_lhb_net_buy_ratio')) else float(r.get('three_day_lhb_net_buy_ratio')),
                'institution_net':float(r.get('inst_net',0) or 0),'connect_net':float(r.get('connect_net',0) or 0),'broker_net':float(r.get('broker_net',0) or 0),
                'lifecycle_event_no':int(r.get('lifecycle_event_no',1) or 1),'lifecycle_net_improving':bool(r.get('lifecycle_net_improving',False)),
                'seat_detail_available':bool(r.get('seat_detail_available',False)),
                'seat_quality_pctile':None if pd.isna(r.get('seat_quality_pctile')) else float(r.get('seat_quality_pctile')),
                'seat_quality_samples':int(r.get('seat_quality_samples',0) or 0)
            } if bool(r.get('lhb_listed',True)) else {
                'listed':False,'source_date':td.strftime('%Y%m%d'),
                'absence_verified_in_complete_saved_billboard':bool(r.get('lhb_absence_verified',False)),
                'applicability':'no_current_disclosed_event',
            }),
            'post_close_events':events,'source_time':as_of,
            'feature_provenance':{'pipeline':'raw-postmarket-v5.0-unverified','source_time':as_of,'physical_cutoff':trade_date}
        }
        if r.get('capital_observation_protocol')=='DISCLOSED_RANKED_SIDE_CONTRIBUTIONS_V1':
            stock['capital_observation_protocol']='DISCLOSED_RANKED_SIDE_CONTRIBUTIONS_V1'
            stock['lhb']['actual_seat_net_observability']='not_observable'
            for old in ['institution_net','connect_net','broker_net']:stock['lhb'][old]=None
            for old in ['inst_net_impact_pctile','broker_net_impact_pctile','buy_sell_balance']:stock[old]=None
            stock['lhb']['disclosed_sides_complete']=bool(r.get('disclosed_sides_complete',False))
            stock['lhb']['disclosed_sides']={key:(float(r[key]) if pd.notna(r.get(key)) else None)
                for category in ('institution','broker','connect') for key in [f'{category}_disclosed_buy',f'{category}_disclosed_sell',f'{category}_disclosed_balance']}
            for key in ['institution_disclosed_impact_pctile','broker_disclosed_impact_pctile','disclosed_buy_sell_balance']:
                stock[key]=float(r[key]) if pd.notna(r.get(key)) else None
            stock['lhb']['buy1']=float(r.get('disclosed_buy1',0)) if pd.notna(r.get('disclosed_buy1')) else None
        stocks.append(stock)

    if selected_codes is not None:
        returned=[s['code'] for s in stocks]
        if len(returned)!=len(selected_codes) or set(returned)!=set(selected_codes):
            raise ValueError('selected_stock_scope_not_exact')

    market=_market_snapshot(sf,streak,limits,index_daily,td,full_market);market['source_time']=as_of
    if reference_mode:
        # Keep labels and T+1 prices physically outside the daily snapshot.
        market['historical_reference_policy']={'mode':'yearly-limit-close-premium',
            'use':'reference_only','affects_scoring_formula':False}
    index_available=bool(index_daily is not None and len(index_daily))
    causal_ok=bool(market.get('causal_market') and market['causal_market'].get('data_quality')=='normal')
    today_industry=sf_pit[sf_pit['trade_date'].dt.normalize()==td]
    industry_total=int(today_industry['ts_code'].nunique())
    industry_mapped=int(today_industry.loc[today_industry['l1_code'].notna(),'ts_code'].nunique())
    coverage={
        'market_full_features':bool(causal_ok and index_available),
        'index_daily':index_available,
        'industry_pit':bool(industry_total>0 and industry_mapped==industry_total),
        'industry_pit_total':industry_total,
        'industry_pit_mapped':industry_mapped,
        'industry_pit_missing':industry_total-industry_mapped,
        'industry_pit_coverage_rate':industry_mapped/industry_total if industry_total else 0.0,
        'theme_pit':bool(theme_members is not None and len(theme_members)),
        'event_feed':bool(event_features is not None),
        'event_rows_through_asof':int(len(event_features)) if event_features is not None else 0,
        'seat_detail':bool(stocks) and all(bool(s['lhb'].get('disclosed_sides_complete')) if s.get('capital_observation_protocol')=='DISCLOSED_RANKED_SIDE_CONTRIBUTIONS_V1' else bool(s['lhb'].get('seat_detail_available')) for s in stocks),
        'disclosed_side_candidate_events':sum(s.get('capital_observation_protocol')=='DISCLOSED_RANKED_SIDE_CONTRIBUTIONS_V1' for s in stocks),
        'complete_disclosed_side_events':sum(s.get('capital_observation_protocol')=='DISCLOSED_RANKED_SIDE_CONTRIBUTIONS_V1' and bool(s['lhb'].get('disclosed_sides_complete')) for s in stocks),
        'mature_identified_seat_eligible_events':sum(int(s['lhb'].get('seat_quality_samples',0))>=20 for s in stocks),
        'history_model':'external_at_analyze'
    }
    if selected_codes is not None:
        coverage.update(
            selected_candidate_count=len(stocks),
            listed_candidate_count=sum(bool(s['lhb']['listed']) for s in stocks),
            verified_absent_candidate_count=sum(not s['lhb']['listed'] and bool(s['lhb'].get('absence_verified_in_complete_saved_billboard')) for s in stocks),
            lhb_step_checked=bool(stocks) and all(
                bool(s['lhb'].get('absence_verified_in_complete_saved_billboard')) if not s['lhb']['listed']
                else (bool(s['lhb'].get('disclosed_sides_complete')) if s.get('capital_observation_protocol')=='DISCLOSED_RANKED_SIDE_CONTRIBUTIONS_V1' else bool(s['lhb'].get('seat_detail_available')))
                for s in stocks))
    if reference_mode:
        coverage.update(historical_market_reference_replaced_by_user=True,
                        current_market_limits=True,current_position_universe=True)
    workflow=[
        {'step':'时间截断','status':'完成','detail':f'所有按交易日数据物理截断至{trade_date}，事件截断至{as_of}'},
        {'step':'历史时点状态','status':'完成','detail':'行业/ST/退市按T日状态映射'},
        {'step':'市场环境','status':'完成' if coverage['market_full_features'] else '降级','detail':'120日因果市场特征+原始宽度双轨校验'},
        {'step':'强势阶段','status':'完成','detail':'首板/2板/3板以上/趋势强势分层'},
        {'step':'板块与题材','status':'完成' if coverage['theme_pit'] else '行业层完成/题材缺失','detail':'行业PIT必跑；有历史题材成员时额外运行题材层'},
        {'step':'市场/板块地位','status':'完成','detail':'连板高度→当日强度→5日强度→成交额的短线地位排序'},
        {'step':'价格透支','status':'完成','detail':'3/5/10/20日涨幅+换手+量比+前高距离+收盘位置'},
        {'step':'龙虎榜','status':'完成' if coverage.get('lhb_step_checked',coverage['seat_detail']) else '数据源缺失','detail':'多原因/单日三日窗口隔离；逐候选检查公开买卖榜侧贡献完整性，差额不代表实际净买；匿名身份与未披露对侧明确不可观测；成熟实名席位资格单独检验，无样本不伪造'+('；已核实未上榜的候选保留，资金/席位/生命周期不适用，按原规则中性' if coverage.get('verified_absent_candidate_count',0) else '')},
        {'step':'盘后事件','status':'完成' if coverage['event_feed'] else '数据源缺失','detail':'仅使用as_of前带公开时间事件；已核验独立催化进入小权重事件分；风险独立扣分/否决'},
        {'step':'历史样本','status':'分析阶段外接','detail':'只有通过滚动样本外生产验收且当前桶表现为正，才允许核心候选晋级'},
        {'step':'爆发力评分','status':'分析阶段执行','detail':'技术/结构/资金/弹性/催化/历史六维归一化评分，风险项独立扣分'},
        {'step':'风险否决与排序','status':'分析阶段执行','detail':'硬否决先行；最终按短线爆发力得分排序，分项与扣分全部可审计'},
    ]
    if reference_mode:
        for item in workflow:
            if item['step']=='市场环境':
                item.update(status='按用户替代口径执行',detail='原始T日宽度闸门；历史参考替换为近一年涨停及次日收盘溢价，独立输出，不改变原计分公式')
    return {'trade_date':trade_date,'as_of':as_of,'market':market,'stocks':stocks,'pipeline':'raw-postmarket-v5.0-unverified',
            'coverage':coverage,'workflow_trace':workflow}
