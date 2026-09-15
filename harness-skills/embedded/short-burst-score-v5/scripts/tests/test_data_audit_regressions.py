import pandas as pd
import pytest
from lhbpost.features import map_industry_point_in_time, aggregate_lhb, build_stock_daily_features
from lhbpost.seat_quality import attach_event_seat_quality
from lhbpost.data.normalized_store import NormalizedStore
from lhbpost.snapshot_pipeline import _market_snapshot


def test_industry_gap_preserves_stock():
    d=pd.DataFrame({'ts_code':['A','A'],'trade_date':['2025-01-01','2025-01-03'],'close':[10,11]})
    m=pd.DataFrame({'ts_code':['A'],'in_date':['2025-01-02'],'out_date':[None],'l1_code':['X']})
    z=map_industry_point_in_time(d,m)
    assert len(z)==2 and pd.isna(z.iloc[0].l1_code) and z.iloc[1].l1_code=='X'


def test_three_day_denominator_uses_market_sessions():
    dates=pd.bdate_range('2025-01-01',periods=5)
    d=pd.DataFrame({'ts_code':['B']*5+['A']*3,'trade_date':list(dates)+list(dates[[0,1,4]]),'amount':[1]*5+[100,200,300]})
    t=pd.DataFrame({'ts_code':['A'],'trade_date':[dates[-1]],'l_buy':[30],'l_sell':[0],'reason':['连续三个交易日']})
    z=aggregate_lhb(t,pd.DataFrame(),d)
    assert z.iloc[0].impact_denominator==300
    assert z.iloc[0].lhb_net_buy_ratio==.1


def test_wrong_window_never_borrows_seat_quality():
    dt=pd.Timestamp('2025-01-01')
    e=pd.DataFrame({'ts_code':['A'],'trade_date':[dt],'rep_reason':['single']})
    st=pd.DataFrame({'ts_code':['A'],'trade_date':[dt],'exalter':['seat'],'buy':[10],'sell':[0],'net_buy':[10],'reason':['other']})
    sq=pd.DataFrame({'exalter':['seat'],'asof_date':[dt],'seat_quality_samples':[30],'seat_quality_pctile':[1.]})
    z=attach_event_seat_quality(e,st,sq)
    assert z.iloc[0].seat_quality_samples==0 and pd.isna(z.iloc[0].seat_quality_pctile)


def test_empty_source_retains_schema(tmp_path):
    (tmp_path/'top_inst').mkdir()
    pd.DataFrame(columns=['ts_code','trade_date','buy']).to_csv(tmp_path/'top_inst'/'20250101.csv',index=False)
    assert set(NormalizedStore(tmp_path).top_inst().columns)=={'ts_code','trade_date','buy'}


def test_duplicate_daily_rejected():
    d=pd.DataFrame({'ts_code':['A','A'],'trade_date':['2025-01-01']*2})
    with pytest.raises(ValueError,match='重复'): build_stock_daily_features(d)


def test_index_extreme_return_keeps_decimal_contract():
    dt=pd.Timestamp('2025-01-01')
    sf=pd.DataFrame({'ts_code':['A'],'trade_date':[dt],'pct_chg':[0.],'amount':[1.],'high':[1.]})
    st=pd.DataFrame({'ts_code':['A'],'trade_date':[dt],'is_limit_up':[False],'is_limit_down':[False],'up_limit':[2.]})
    ix=pd.DataFrame({'ts_code':['IX'],'trade_date':[dt],'pct_chg':[1.2]})
    z=_market_snapshot(sf,st,pd.DataFrame(),ix,dt,None)
    assert z['index_changes']['IX']==120.


def test_lowest_close_remains_zero_through_snapshot(monkeypatch):
    import test_snapshot_pipeline_smoke as smoke
    original=smoke.build_snapshot
    def wrapped(**kwargs):
        daily=kwargs['daily'].copy()
        mask=(daily['ts_code']=='000000.SZ')&(daily['trade_date']==daily['trade_date'].max())
        daily.loc[mask,'low']=daily.loc[mask,'close']
        daily.loc[mask,'high']=daily.loc[mask,'close']*1.01
        kwargs['daily']=daily
        snap=original(**kwargs)
        assert snap['stocks'][0]['close_location']==0.0
        return snap
    monkeypatch.setattr(smoke,'build_snapshot',wrapped)
    smoke.test_raw_postmarket_to_snapshot_to_analysis()


def test_empty_lhb_snapshot_still_reports_market(monkeypatch):
    import test_snapshot_pipeline_smoke as smoke
    original=smoke.build_snapshot
    def wrapped(**kwargs):
        kwargs['top_list']=kwargs['top_list'].iloc[:0]
        kwargs['top_inst']=kwargs['top_inst'].iloc[:0]
        snap=original(**kwargs)
        assert snap['stocks']==[] and snap['market']['turnover_total']>0
        # 原烟测检查固定一只股票，这里单独结束复用的数据构建。
        raise Finished
    class Finished(Exception): pass
    monkeypatch.setattr(smoke,'build_snapshot',wrapped)
    with pytest.raises(Finished):smoke.test_raw_postmarket_to_snapshot_to_analysis()


@pytest.mark.parametrize('column,value',[('open','bad'),('close',float('inf')),('amount',-1),('high',.5)])
def test_numeric_raw_audit_rejects_invalid_values(tmp_path,column,value):
    from lhbpost.data_audit import _audit_one_dated_file
    p=tmp_path/'20250101.csv'
    row={'ts_code':'A','trade_date':'20250101','open':1.,'high':2.,'low':1.,'close':1.,'vol':10.,'amount':10.}
    row[column]=value
    pd.DataFrame([row]).to_csv(p,index=False)
    errors=[]
    _audit_one_dated_file(p,'daily',errors,{})
    assert errors


def test_static_duplicate_and_overlap_rejected(tmp_path):
    from lhbpost.data_audit import audit_raw_data
    pd.DataFrame({'ts_code':['A','A'],'name':['a','a'],'list_date':['20200101']*2}).to_csv(tmp_path/'stock_basic.csv',index=False)
    pd.DataFrame({'cal_date':['20250101']}).to_csv(tmp_path/'trade_cal.csv',index=False)
    pd.DataFrame({'ts_code':['A','A'],'l1_code':['X','Y'],'in_date':['20200101','20210101'],'out_date':[None,None]}).to_csv(tmp_path/'sw_members.csv',index=False)
    errors=audit_raw_data(tmp_path).errors
    assert any('stock_basic.csv存在重复主键' in e for e in errors)
    assert any('重叠行业归属区间' in e for e in errors)


@pytest.mark.parametrize('unmapped_code',['000005.SZ','000000.SZ'])
def test_missing_scoring_inputs_are_explicit_and_industry_coverage_is_current(monkeypatch,unmapped_code):
    import test_snapshot_pipeline_smoke as smoke
    original=smoke.build_snapshot
    class Finished(Exception):pass
    def wrapped(**kwargs):
        kwargs['daily_basic']=kwargs['daily_basic'].drop(columns=['free_mv','turnover_rate'])
        # 缺失的是非候选股票的当日行业归属，不能用成员表非空声称全覆盖。
        members=kwargs['sw_members'].copy()
        members.loc[members['ts_code']==unmapped_code,'out_date']='2020-01-01'
        kwargs['sw_members']=members
        snap=original(**kwargs)
        stock=snap['stocks'][0]
        assert {'free_mcap_pctile','lhb_net_free_float_pctile','turnover_rate_pctile'}<=set(stock['missing_score_features'])
        assert stock['score_data_quality']=='insufficient'
        if unmapped_code=='000000.SZ':
            assert stock['industry_core_rank']==99 and stock['data_quality']=='insufficient'
        assert snap['coverage']['industry_pit'] is False
        assert snap['coverage']['industry_pit_total']==6 and snap['coverage']['industry_pit_missing']==1
        assert snap['coverage']['industry_pit_coverage_rate']==5/6
        raise Finished
    monkeypatch.setattr(smoke,'build_snapshot',wrapped)
    with pytest.raises(Finished):smoke.test_raw_postmarket_to_snapshot_to_analysis()
