import math,json
from pathlib import Path
import pandas as pd
import pytest
from lhbpost.disclosed_sides import side_records,attach_disclosed_contributions,PROTOCOL
from lhbpost.features import aggregate_lhb
from lhbpost.seat_quality import _dedupe_seat_events
from lhbpost.core import lhb_evidence


def raw(amount,side='BUY',name='机构专用'):
    return dict(SECURITY_CODE='600000',TRADE_DATE='2026-09-11',EXPLANATION='一日榜',OPERATEDEPT_CODE='0',OPERATEDEPT_NAME=name,
        **{side:amount,('SELL' if side=='BUY' else 'BUY'):None})


def event():
    return pd.DataFrame([dict(ts_code='600000.SH',trade_date=pd.Timestamp('2026-09-11'),rep_reason='一日榜',impact_denominator=1000)])


def test_identical_anonymous_rows_each_contribute_without_identity_merge():
    rows=side_records({'BUY':[raw(100),raw(100)],'SELL':[raw(50,'SELL')]})
    result=attach_disclosed_contributions(event(),rows).iloc[0]
    assert result['institution_disclosed_buy']==200 and result['institution_disclosed_sell']==50
    assert result['institution_disclosed_balance']==150
    assert math.isnan(result['inst_net'])


def test_own_side_unknown_fails_other_side_unknown_is_not_zero():
    assert side_records({'BUY':[raw(100)]})[0]['counterpart_disclosure']=='not_observable'
    with pytest.raises((TypeError,ValueError)):side_records({'BUY':[raw(None)]})


def test_unknown_other_side_does_not_prevent_complete_ranked_sides():
    rows=side_records({'BUY':[raw(100)],'SELL':[raw(50,'SELL')]})
    assert attach_disclosed_contributions(event(),rows).iloc[0]['disclosed_sides_complete']


def test_missing_side_not_complete():
    result=attach_disclosed_contributions(event(),side_records({'BUY':[raw(100)]})).iloc[0]
    assert not result['disclosed_sides_complete']


def test_different_reason_never_mixed():
    other=raw(999);other['EXPLANATION']='三日榜'
    rows=side_records({'BUY':[raw(100),other],'SELL':[raw(50,'SELL')]})
    assert attach_disclosed_contributions(event(),rows).iloc[0]['institution_disclosed_buy']==100


def test_top_list_different_scope_not_forced_to_side_totals():
    tl=pd.DataFrame([dict(ts_code='600000.SH',trade_date='2026-09-11',reason='一日榜',l_buy=1000,l_sell=800)])
    ti=pd.DataFrame(columns=['ts_code','trade_date','exalter','buy','sell','net_buy','reason'])
    ti.attrs['disclosed_sides']=side_records({'BUY':[raw(100)],'SELL':[raw(50,'SELL')]})
    daily=pd.DataFrame([dict(ts_code='600000.SH',trade_date='2026-09-11',amount=5000)])
    result=aggregate_lhb(tl,ti,daily).iloc[0]
    assert result['lhb_buy']==1000 and result['lhb_net_buy']==200
    assert result['institution_disclosed_balance']==50


def test_anonymous_cannot_become_mature_identity():
    x=pd.DataFrame([dict(ts_code='600000.SH',trade_date='2026-09-11',exalter='机构专用',buy=100,sell=20,net_buy=80)])
    assert _dedupe_seat_events(x).empty


def test_disclosure_report_does_not_claim_unknown_actual_net():
    cfg={'lhb':{'negative_net_ratio':-.05,'extreme_institution_sell_ratio':-.05,'concentration_risk':.8,'confirm_net_ratio':.03,'confirm_buy_sell_ratio':1.2}}
    s=dict(capital_observation_protocol=PROTOCOL,turnover=1000,institution_disclosed_impact_pctile=.9,broker_disclosed_impact_pctile=.2,
        disclosed_buy_sell_balance=.5,lhb=dict(listed=True,buy5=100,sell5=80,institution_net=None,disclosed_sides={'institution_disclosed_buy':100,'institution_disclosed_sell':50}))
    role,metrics,reasons=lhb_evidence(s,cfg)
    assert metrics['institution_net_ratio'] is None
    assert metrics['institution_impact_pctile']==.9 and metrics['capital_observation_protocol']==PROTOCOL
    assert not any('机构专用净额 0' in reason for reason in reasons)
    assert any('不代表席位实际净买' in reason for reason in reasons)


def test_source_duplicate_record_is_rejected():
    rows=side_records({'BUY':[raw(100)],'SELL':[raw(50,'SELL')]})
    with pytest.raises(ValueError,match='duplicate_disclosed'):attach_disclosed_contributions(event(),rows+[rows[0]])


def test_conflicting_named_seat_same_trade_id_not_added_or_selected():
    first=raw(297050369.58,name='深股通专用');first.update(OPERATEDEPT_CODE='10634757',SELL=233052072.72,TRADE_ID='100264316')
    second={**first,'BUY':114383656.9,'SELL':121553440.85}
    rows=side_records({'BUY':[first,second],'SELL':[first]})
    assert len(rows)==3 and all(r['group_amount_conflict'] for r in rows)
    assert rows[0]['source_row']==0 and rows[1]['source_row']==1
    assert rows[0]['source_trade_id']==rows[1]['source_trade_id']=='100264316'
    assert rows[0]['disclosed_amount']==first['BUY'] and rows[1]['counterpart_amount']==second['SELL']
    result=attach_disclosed_contributions(event(),rows).iloc[0]
    assert not result.disclosed_sides_complete and result.disclosed_group_amount_conflict
    assert 'connect_disclosed_buy' not in result.index
    assert math.isnan(result.inst_net)


def test_conflicted_group_does_not_discard_other_stock_history():
    from lhbpost.data.local_postmarket import merge_public_seats
    first=raw(100,name='普通席位');first.update(OPERATEDEPT_CODE='123',SELL=30)
    second={**first,'BUY':200}
    clean={**first,'SECURITY_CODE':'600001','BUY':300,'SELL':40}
    evidence,accepted,coverage=merge_public_seats({'BUY':[first,second,clean]})
    assert coverage['conflicting_seats']==1 and coverage['raw_source_row_count']==3
    assert len(accepted)==1 and accepted[0]['ts_code']=='600001.SH' and accepted[0]['net_buy']==260
    rows=side_records({'BUY':[first,second,clean],'SELL':[clean]})
    events=pd.concat([event(),event().assign(ts_code='600001.SH')],ignore_index=True)
    result=attach_disclosed_contributions(events,rows).set_index('ts_code')
    assert not result.loc['600000.SH','disclosed_sides_complete']
    assert result.loc['600001.SH','disclosed_sides_complete']
    assert result.loc['600001.SH','broker_disclosed_buy']==300

def test_disclosure_table_is_serializable_without_future_raw_labels(tmp_path):
    from lhbpost.data.local_postmarket import LocalPostMarketAdapter
    item=raw(100);item['RISE_PROBABILITY_3DAY']=99.0
    rows=side_records({'BUY':[item]})
    adapter=LocalPostMarketAdapter(tmp_path)
    adapter._save('disclosed_sides',rows)
    path=tmp_path/'disclosed_sides'/'20260911.csv'
    frame=pd.read_csv(path)
    assert len(frame)==1 and 'raw_source_record' not in frame
    assert 'RISE_PROBABILITY_3DAY' not in path.read_text(encoding='utf-8-sig')
