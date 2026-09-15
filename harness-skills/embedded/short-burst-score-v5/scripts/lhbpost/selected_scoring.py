"""Score the user's exact list with the original engine and existing saved data."""
from pathlib import Path
import hashlib,json,math
import numpy as np
import pandas as pd
from .features import build_stock_daily_features
from .core import SCORING_FEATURES

def build_selected_snapshot(request,run):
    if request.get('schema')!='SHORT_BURST_SELECTED_REQUEST_V1':raise ValueError('selected_request_schema')
    selected=request['stocks'];codes=[r['code'] for r in selected]
    if not codes or len(codes)!=len(set(codes)):raise ValueError('selected_list_empty_or_duplicate')
    day=pd.Timestamp(request['trade_date']);compact=day.strftime('%Y%m%d')
    root=Path(request['data_root']);base=Path(request['basic_root']);bindings={}
    def read(path):
        raw=path.read_bytes();bindings[str(path)]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
        return pd.read_csv(path,dtype={'ts_code':str,'trade_date':str,'list_date':str,'in_date':str,'out_date':str,'l1_code':str})
    dates=sorted(p for p in (root/'daily').glob('*.csv') if p.stem<=compact)[-80:]
    if not dates or dates[-1].stem!=compact:raise ValueError('selected_close_date_missing')
    daily=pd.concat([read(p) for p in dates],ignore_index=True)
    factor=pd.concat([read(base/'adj_factor'/p.name) for p in dates],ignore_index=True)
    current=daily[daily.trade_date.eq(compact)].copy()
    if not set(codes)<=set(current.ts_code):raise ValueError('selected_stock_missing')
    basic=read(base/'daily_basic'/f'{compact}.csv')
    names=read(base/'stock_basic.csv').set_index('ts_code')
    limits=read(base/'stk_limit'/f'{compact}.csv')
    top=read(root/'top_list'/f'{compact}.csv')
    # A selected stock need not be on the billboard. Its true absence is retained.
    if top.ts_code.isin(codes).any():raise ValueError('selected_billboard_present_requires_existing_detail_path')
    merged=daily.merge(factor[['ts_code','trade_date','adj_factor']],on=['ts_code','trade_date'],how='left',validate='one_to_one')
    if merged[merged.ts_code.isin(codes)].adj_factor.isna().any():raise ValueError('selected_adjustment_missing')
    adjusted=merged.assign(value=merged.close*merged.adj_factor).pivot(index='trade_date',columns='ts_code',values='value').sort_index()
    rets={n:adjusted.iloc[-1]/adjusted.iloc[-n-1]-1 for n in (3,5,10,20)}
    ma20=adjusted.rolling(20,min_periods=20).mean()
    slope=ma20.iloc[-1]/ma20.iloc[-6]-1
    ref=current.set_index('ts_code').join(basic.set_index('ts_code')[['turnover_rate','free_share']],rsuffix='_basic')
    ref['free_mv']=ref.free_share*10000*ref.close
    ref['ret3']=rets[3];ref['ret5']=rets[5]
    ref=ref.join(limits.set_index('ts_code')[['up_limit','down_limit']])
    ref['is_limit_up']=ref.up_limit.notna()&(ref.close>=ref.up_limit-1e-8)
    members=read(base/'sw_members.csv')
    members=members[(pd.to_datetime(members.in_date)<=day)&(pd.to_datetime(members.out_date,errors='coerce').fillna(pd.Timestamp('2099-12-31'))>=day)]
    members=members.sort_values('in_date').drop_duplicates('ts_code',keep='last').set_index('ts_code')
    ref=ref.join(members[['l1_code']])
    sector=ref.dropna(subset=['l1_code']).groupby('l1_code').agg(day_change_pct=('pct_chg','median'),
        up_ratio=('pct_chg',lambda x:float((x>0).mean())),limit_up_count=('is_limit_up','sum'),
        rel_strength_3d=('ret3','median'),rel_strength_5d=('ret5','median'),member_count=('close','size'))
    sector.rel_strength_3d=(sector.rel_strength_3d-ref.ret3.median())*100
    sector.rel_strength_5d=(sector.rel_strength_5d-ref.ret5.median())*100
    sector_rs=sector.rel_strength_5d.rank(pct=True)
    # Technical features use only these requested securities. Existing cross-
    # sectional reference files supply percentile denominators without downloads.
    chosen=daily[daily.ts_code.isin(codes)].copy();chosen['amount']*=1000;chosen['vol']*=100;chosen['pct_chg']/=100
    db=basic[basic.ts_code.isin(codes)].copy();db['free_mv']=db.free_share*10000*db.close
    af=factor[factor.ts_code.isin(codes)]
    features=build_stock_daily_features(chosen,db,af)
    latest=features[features.trade_date.eq(day)].set_index('ts_code')
    previous=daily[daily.trade_date.eq(dates[-2].stem)].set_index('ts_code')
    stocks=[]
    for item in selected:
        code=item['code'];r=latest.loc[code];q=ref.loc[code];name=names.loc[code]
        if str(name.get('name_as_of',''))!=compact:raise ValueError('selected_name_date_unverified:'+code)
        if abs(float(item['screenshot_close'])-float(r.close))>.000001:raise ValueError('screenshot_close_mismatch:'+code)
        if not bool(q.is_limit_up) or not (-100<float(previous.loc[code,'pct_chg'])<4.5 and float(previous.loc[code,'close'])>2):
            raise ValueError('selected_first_board_evidence_requires_review:'+code)
        if pd.Timestamp(name['list_date'])>day-pd.Timedelta(days=40):raise ValueError('selected_ipo_requires_separate_rule')
        s={key:None for key in SCORING_FEATURES}
        for key in ('breakout_20d_strength','volume_health','startup_location_health','close_above_ma20','ma5_gt_ma10_gt_ma20','ma20_gt_ma60'):
            value=r[key];s[key]=bool(value) if isinstance(value,(bool,np.bool_)) else float(value)
        s.update(code=code,name=str(name['name']),board='主板',data_quality='warning',
            risk_warning=str(name['name']).upper().startswith(('ST','*ST','SST','S*ST')),
            delisting_risk=('退' in str(name['name'])),new_unlimited=False,recent_ipo_immature=False,
            change_pct=float(q.pct_chg),turnover=float(r.amount),turnover_rate=float(q.turnover_rate),
            free_float_mcap=float(q.free_mv),days_return={str(n):float(rets[n][code]*100) for n in rets},
            board_streak=1,sector=str(q.l1_code),industry_metrics=sector.loc[q.l1_code].to_dict() if pd.notna(q.l1_code) else {},
            rs_20d_pctile=float(rets[20].rank(pct=True)[code]),ma20_slope_pctile=float(slope.rank(pct=True)[code]),
            close_location=float(r.close_location_day),volume_ratio20=float(r.vol_ratio20),
            sector_rs_5d_pctile=float(sector_rs.get(q.l1_code,float('nan'))),
            turnover_rate_pctile=float(ref.turnover_rate.rank(pct=True)[code]),free_mcap_pctile=float(ref.free_mv.rank(pct=True)[code]),
            distance_to_prev20_high_pct=float((r.close/r.prev20_high-1)*100),
            distance_to_prev20_high_atr=float((r.close-r.prev20_high)/r.atr14),
            lhb={'listed':False,'source_date':compact,'absence_verified_in_complete_saved_billboard':True},
            post_close_events=[],feature_provenance={'pipeline':'selected_saved_postmarket','physical_cutoff':compact,
                'candidate_scope':'user_explicit_list','event_semantics_verified':False,'history_model_verified':False,
                'first_board_basis':'dated_limit_up_and_previous_return_below_applicable_price_limit_floor'})
        s={k:(None if isinstance(v,float) and not math.isfinite(v) else v) for k,v in s.items()}
        s['missing_score_features']=sorted(k for k in SCORING_FEATURES if s.get(k) is None)
        stocks.append(s)
    idx=read(base/'index_daily'/f'{compact}.csv')
    prior=read(base/'daily'/dates[-2].name)
    market={'up_count':int((current.pct_chg>0).sum()),'down_count':int((current.pct_chg<0).sum()),'flat_count':int((current.pct_chg==0).sum()),
        'limit_up_count':int(ref.is_limit_up.sum()),'limit_down_count':int((ref.down_limit.notna()&(ref.close<=ref.down_limit+1e-8)).sum()),
        'broken_limit_up_count':int((ref.up_limit.notna()&(ref.high>=ref.up_limit-1e-8)&~ref.is_limit_up).sum()),
        'turnover_total':float(current.amount.sum()*1000),'turnover_change_pct':float((current.amount.sum()/prior.amount.sum()-1)*100),
        'index_changes':{r.ts_code:float(r.pct_chg) for r in idx.itertuples()}}
    snapshot={'trade_date':day.strftime('%Y-%m-%d'),'as_of':request['as_of'],'pipeline':'selected-postmarket-observation',
        'market':market,'stocks':stocks,'coverage':{'market_full_features':False,'index_daily':True,'industry_pit':False,
            'theme_pit':False,'event_feed':False,'seat_detail':False,'history_model':False},
        'selection_scope':{'requested_codes':codes,'output_count':len(stocks),'new_acquisition_performed':False},
        'limitations':['仅指定名单观察评分；非完整生产验收','盘后事件、题材、独立历史验证未核实，缺项按原评分规则中性处理','全部指定股票当日不在已保存龙虎榜中']}
    (Path(run)/'selected_source_bindings.json').write_text(json.dumps(bindings,ensure_ascii=False,indent=2),encoding='utf-8')
    return snapshot
