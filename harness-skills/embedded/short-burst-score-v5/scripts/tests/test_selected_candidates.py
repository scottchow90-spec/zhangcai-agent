"""Synthetic unit tests only; never runs local_business or source acquisition."""
import json

import pandas as pd
import pytest

from lhbpost import candidate_pipeline as candidate
from lhbpost import snapshot_pipeline as snapshot


@pytest.fixture(scope='module')
def inputs():
    dates=pd.bdate_range('2024-01-01',periods=140)
    rows=[];basics=[];limits=[];adj=[]
    codes=[f'{j:06d}.SZ' for j in range(12)]
    for j,code in enumerate(codes):
        for i,dt in enumerate(dates):
            p=10+j+i*(.01+j*.002)
            rows.append((code,dt,p,p*1.01,p*.99,p,1e6,1e7*(j+1),.001*(j+1)))
            basics.append((code,dt,2+j*.7,1e8*(j+1),5e7))
            limits.append((code,dt,p*1.1,p*.9))
            adj.append((code,dt,1.0))
    daily=pd.DataFrame(rows,columns=['ts_code','trade_date','open','high','low','close','vol','amount','pct_chg'])
    basic=pd.DataFrame(basics,columns=['ts_code','trade_date','turnover_rate','free_mv','free_share'])
    lim=pd.DataFrame(limits,columns=['ts_code','trade_date','up_limit','down_limit'])
    adjustment=pd.DataFrame(adj,columns=['ts_code','trade_date','adj_factor'])
    dt=dates[-1]
    top=pd.DataFrame({'ts_code':codes[9:],'trade_date':[dt]*3,'l_buy':[5e6,7e6,9e6],
                      'l_sell':[1e6,2e6,1e6],'reason':['涨幅偏离']*3})
    top.attrs['verified_complete_dates']=[dt.strftime('%Y-%m-%d')]
    inst=pd.DataFrame({'ts_code':codes[9:],'trade_date':[dt]*3,'exalter':['机构专用']*3,
                       'buy':[2e6,3e6,5e6],'sell':[0.0]*3,'net_buy':[2e6,3e6,5e6],
                       'reason':['涨幅偏离']*3})
    members=pd.DataFrame({'ts_code':codes,'l1_code':['I'+str(j//6) for j in range(12)],
                          'l1_name':['行业'+str(j//6) for j in range(12)],'in_date':['2010-01-01']*12,'out_date':[None]*12})
    sb=pd.DataFrame({'ts_code':codes,'name':['股票'+str(j) for j in range(12)],'exchange':['SZSE']*12,
                     'market':['主板']*12,'list_date':['2010-01-01']*12,'delist_date':[None]*12,'name_as_of':[dt]*12})
    st=daily[['ts_code','trade_date']].assign(is_st=False,is_delisting_arrangement=False)
    ix=pd.DataFrame({'ts_code':['000001.SH']*140,'trade_date':dates,'close':[3000+i for i in range(140)],'pct_chg':[.001]*140})
    return dict(daily=daily,daily_basic=basic,top_list=top,top_inst=inst,sw_members=members,
                stock_basic=sb,st_status=st,limits=lim,index_daily=ix,adj_factor=adjustment)


def td(inputs):
    return inputs['daily'].trade_date.max().strftime('%Y-%m-%d')


def snap(inputs,codes=None):
    return snapshot.build_snapshot(trade_date=td(inputs),as_of=td(inputs)+'T21:00:00+08:00',
                                   selected_codes=codes,**inputs)


def test_default_candidate_scope_is_actual_billboard(inputs):
    actual=candidate.build_candidate_feature_table(**inputs)
    assert set(actual['ts_code'])=={'000009.SZ','000010.SZ','000011.SZ'}
    result=snap(inputs)
    assert len(result['stocks'])==3
    assert {s['code'] for s in result['stocks']}==set(actual['ts_code'])
    assert all(s['lhb']['listed'] is True for s in result['stocks'])


def test_nine_nonlisted_preserved_without_fake_capital(inputs):
    codes=[f'{j:06d}.SZ' for j in range(9)]
    result=snap(inputs,codes)
    assert {s['code'] for s in result['stocks']}==set(codes)
    assert len(result['stocks'])==9
    for s in result['stocks']:
        assert s['lhb']['listed'] is False
        assert s['lhb']['absence_verified_in_complete_saved_billboard'] is True
        assert not set(s['lhb']) & {'buy5','sell5','net_buy','buy1','institution_net','lifecycle_event_no','seat_quality_samples'}
        assert 'lhb_net_impact_pctile' in s['missing_score_features']
    assert result['coverage']['lhb_step_checked'] is True
    assert result['coverage']['seat_detail'] is False
    assert result['coverage']['verified_absent_candidate_count']==9
    json.dumps(result,allow_nan=False)


def test_reference_universe_not_restricted_to_selected(inputs):
    selected=candidate.build_candidate_feature_table(**inputs,selected_codes=['000001.SZ'],selected_trade_date=td(inputs))
    from lhbpost.features import build_stock_daily_features
    sf=build_stock_daily_features(inputs['daily'],inputs['daily_basic'],adj_factor=inputs['adj_factor'])
    ref=sf[(sf.ts_code=='000001.SZ') & (sf.trade_date==pd.Timestamp(td(inputs)))].iloc[0]
    for col in ['rs_20d_pctile','ma20_slope_pctile','free_mcap_pctile','turnover_rate_pctile']:
        assert selected.iloc[0][col]==ref[col]
    assert selected.iloc[0]['free_mcap_pctile']==pytest.approx(2/12)
    full=snap(inputs)
    one=snap(inputs,['000001.SZ'])
    assert one['market']==full['market']
    assert one['stocks'][0]['industry_metrics']['member_count']==6


def test_real_lhb_association_preserves_full_billboard_percentiles(inputs):
    full=candidate.build_candidate_feature_table(**inputs).set_index('ts_code')
    selected=candidate.build_candidate_feature_table(**inputs,selected_codes=['000009.SZ','000001.SZ'],selected_trade_date=td(inputs)).set_index('ts_code')
    for col in ['lhb_buy','lhb_sell','lhb_net_buy','lhb_net_free_float_pctile','lhb_net_impact_pctile']:
        assert selected.loc['000009.SZ',col]==full.loc['000009.SZ',col]
        assert pd.isna(selected.loc['000001.SZ',col])
    assert selected.loc['000009.SZ','lhb_net_free_float_pctile']==pytest.approx(1/3)
    output={s['code']:s for s in snap(inputs,['000009.SZ','000001.SZ'])['stocks']}
    assert output['000009.SZ']['lhb']['listed'] is True
    assert output['000009.SZ']['lhb']['net_buy']==4e6
    assert output['000001.SZ']['lhb']['listed'] is False


@pytest.mark.parametrize('codes,date,error',[
    (['000001.SZ','000001.SZ'],None,'重复'),
    (['999999.SZ'],None,'未知'),
    (['000001.SZ'],'1990-01-01','实际交易日'),
    (['000001.SZ'],'2024-01-01T16:00:00','无效'),
    ('000001.SZ',None,'非空代码列表'),
    ([],None,'非空代码列表'),
])
def test_reject_invalid_selected_request(inputs,codes,date,error):
    with pytest.raises(ValueError,match=error):
        candidate.build_candidate_feature_table(**inputs,selected_codes=codes,selected_trade_date=date or td(inputs))


def test_absence_needs_verified_current_date(inputs):
    changed=dict(inputs)
    changed['top_list']=inputs['top_list'].copy()
    changed['top_list'].attrs['verified_complete_dates']=['1990-01-01']
    with pytest.raises(ValueError,match='verified_complete_date'):
        snap(changed,['000001.SZ'])


def test_selected_join_retains_boolean_risk_semantics(inputs):
    changed=dict(inputs)
    changed['top_list']=inputs['top_list'].copy()
    changed['top_list'].loc[changed['top_list'].ts_code=='000009.SZ','reason']='跌幅偏离'
    changed['top_inst']=inputs['top_inst'].copy()
    changed['top_inst'].loc[changed['top_inst'].ts_code=='000009.SZ','reason']='跌幅偏离'
    selected=candidate.build_candidate_feature_table(**changed,selected_codes=['000009.SZ','000001.SZ'],selected_trade_date=td(inputs))
    assert pd.api.types.is_bool_dtype(selected['close_above_ma20'])
    assert selected['close_above_ma20'].all()
    assert not selected['downward_anomaly_without_reversal'].any()


def test_verified_empty_billboard_and_unknown_date(inputs):
    changed=dict(inputs)
    changed['top_list']=inputs['top_list'].iloc[:0].copy()
    changed['top_inst']=inputs['top_inst'].iloc[:0].copy()
    result=snap(changed,['000001.SZ'])
    assert len(result['stocks'])==1 and result['stocks'][0]['lhb']['listed'] is False
    assert not snap(changed)['stocks']


def test_selected_daily_missing_not_dropped(inputs):
    changed=dict(inputs)
    changed['daily']=inputs['daily'][~((inputs['daily'].ts_code=='000001.SZ') & (inputs['daily'].trade_date==pd.Timestamp(td(inputs))))].copy()
    with pytest.raises(ValueError,match='当日daily缺失'):
        snap(changed,['000001.SZ'])
