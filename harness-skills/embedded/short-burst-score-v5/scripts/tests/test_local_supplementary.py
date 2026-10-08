import pandas as pd
import pytest
from lhbpost.data.local_supplementary import calendar_rows,industry_intervals,parse_hfq,expand_hfq,tnf_names

def test_calendar_real_dates_preserved():
    assert calendar_rows(['20260910','20260911'],'20260910','20260911')[-1]['cal_date']=='20260911'

@pytest.mark.parametrize('dates',[[],['20260912'],['20260911','20260911']])
def test_bad_calendar_rejected(dates):
    with pytest.raises(ValueError):calendar_rows(dates,'20260910','20260911')

def test_industry_effective_interval_has_no_overlap():
    x=pd.DataFrame([{'股票代码':1,'计入日期':'2014-02-21','行业代码':480101},
        {'股票代码':1,'计入日期':'1991-04-03','行业代码':440101},
        {'股票代码':1,'计入日期':'2027-01-01','行业代码':510101}])
    rows=industry_intervals(x,'20260911')
    assert rows[0]['out_date']=='20140220' and rows[0]['l1_code']=='440000'
    assert rows[1]['in_date']=='20140221' and rows[1]['out_date']==''
    assert len(rows)==2

def test_industry_conflicting_same_date_rejected():
    x=pd.DataFrame([dict(code=1,start_date='20260910',industry_code=s) for s in ['480101','440101']])
    with pytest.raises(ValueError,match='conflicting_industry'):industry_intervals(x,'20260911')

def test_hfq_tail_comment_and_backward_effective_multiplier():
    factors=parse_hfq('var sh600000hfq={"data":[{"d":"2026-09-11","f":"2"},{"d":"1900-01-01","f":"1"}]} /* tail */')
    rows=expand_hfq('600000.SH',['20260910','20260911'],factors)
    assert [r['adj_factor'] for r in rows]==[1,2]

@pytest.mark.parametrize('text',['{}','{"data":[]}','{"data":[{"d":"2026-09-11","f":0}]}'])
def test_invalid_hfq_not_ones(text):
    with pytest.raises(ValueError):parse_hfq(text)

def test_earlier_bar_not_backfilled_future_factor():
    with pytest.raises(ValueError):expand_hfq('600000.SH',['20260910'],[('20260911',2)])

def test_tnf_360_and_full_chinese_name():
    record=bytearray(360);record[:6]=b'600519';name='贵州茅台'.encode('gbk');record[31:31+len(name)]=name
    assert tnf_names(bytes(50)+bytes(record),'SH')=={'600519.SH':'贵州茅台'}

def test_old_tnf_stride_rejected():
    with pytest.raises(ValueError):tnf_names(bytes(50+314),'SH')
