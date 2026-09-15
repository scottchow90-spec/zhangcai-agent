import pandas as pd
import pytest
from lhbpost.pit_risk_guard import attach_pit_risk,merge_verified_limits

def frame(**kw):
    row={'trade_date':'2026-09-10','ts_code':'000001.SZ'};row.update(kw)
    return pd.DataFrame([row])

def test_current_name_cannot_backfill_past():
    with pytest.raises(ValueError,match='backfill'):
        attach_pit_risk(frame(name='ST当前名'),frame(is_st=False,is_delisting_arrangement=False),
                       stock_basic=pd.DataFrame([{'ts_code':'000001.SZ','name':'ST当前名','name_as_of':'2026-09-11'}]))

def test_historical_name_and_explicit_false_preserved():
    x=attach_pit_risk(frame(name='ST当前名'),frame(is_st='0',is_delisting_arrangement='False'),frame(name='历史名称'))
    assert x.iloc[0]['name']=='历史名称' and not x.iloc[0].is_st

def test_dense_non_st_rows_not_treated_as_positive_membership():
    x=attach_pit_risk(frame(),frame(is_st=0,is_delisting_arrangement=0),frame(name='历史名称'))
    assert not x.is_st.any()

@pytest.mark.parametrize('st',[None,pd.DataFrame(columns=['trade_date','ts_code']),frame(type_name='ST'),frame(is_st=None,is_delisting_arrangement=False)])
def test_absent_status_not_non_st(st):
    with pytest.raises(ValueError): attach_pit_risk(frame(),st,frame(name='历史名称'))

def test_st_name_contradiction_rejected():
    with pytest.raises(ValueError,match='contradicts'):
        attach_pit_risk(frame(),frame(is_st=False,is_delisting_arrangement=False),frame(name='*ST公司'))

def test_limit_unknown_is_not_not_limit_up():
    with pytest.raises(ValueError): merge_verified_limits(frame(close=10),frame(up_limit=None,down_limit=None))

def test_limit_missing_day_blocks_market_counts():
    with pytest.raises(ValueError,match='coverage'):
        merge_verified_limits(frame(close=10),frame(trade_date='2026-09-09',up_limit=11,down_limit=9))

def test_explicit_unrestricted_distinguished():
    x=merge_verified_limits(frame(close=22,high=23),frame(up_limit=None,down_limit=None,no_limit=True))
    assert not x.is_limit_up.any() and not x.is_limit_down.any() and not x.touch_up.any()

@pytest.mark.parametrize('kw',[{'up_limit':float('inf'),'down_limit':9},{'up_limit':11,'down_limit':12},
                             {'up_limit':11,'down_limit':9,'no_limit':True}])
def test_bad_limits_rejected(kw):
    with pytest.raises(ValueError): merge_verified_limits(frame(close=10),frame(**kw))

def test_bounded_flags():
    x=merge_verified_limits(frame(close=11,high=11),frame(up_limit=11,down_limit=9))
    assert x.is_limit_up.all() and x.touch_up.all() and not x.is_limit_down.any()

def test_integer_dates_are_calendar_not_nanoseconds():
    x=merge_verified_limits(frame(trade_date=20260910,close=11),frame(up_limit=11,down_limit=9))
    assert x.is_limit_up.all()

def test_complete_history_supplies_status_without_invented_delisting_flag():
    x=attach_pit_risk(frame(),pd.DataFrame(columns=['ts_code','trade_date']),frame(name='普通公司',is_st='0'))
    assert not x.is_st.any() and not x.is_delisting_arrangement.any()
    assert x.delisting_status_basis.iloc[0]=='derived_from_dated_name'

def test_dated_delisting_name_is_preserved():
    x=attach_pit_risk(frame(),pd.DataFrame(columns=['ts_code','trade_date']),frame(name='退市公司',is_st='1'))
    assert x.is_delisting_arrangement.all()

def test_sparse_st_conflicts_with_explicit_history():
    with pytest.raises(ValueError,match='contradict'):
        attach_pit_risk(frame(),frame(type_name='ST'),frame(name='普通公司',is_st='0'))
