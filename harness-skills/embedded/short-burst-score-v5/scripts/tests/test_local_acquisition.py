import json
import math
from pathlib import Path
from types import SimpleNamespace
import pytest
from lhbpost.data import local_postmarket as local


def test_local_units_preserve_yuan_and_shares():
    rows=[dict(date='20260910',open=10,high=11,low=9,close=10,volume=100,amount=1000),
          dict(date='20260911',open=10,high=12,low=9,close=11,volume=200,amount=2200,preclose=10)]
    got=local.LocalPostMarketAdapter._bars(rows,'sh600000','20260911','20260911')[0]
    assert got['amount']==2.2 and got['vol']==2 and got['pre_close']==10
    assert got['pct_chg']==pytest.approx(10)
    assert got['ts_code']=='600000.SH'


@pytest.mark.parametrize('value',['2026-09-11','20261301','20990101'])
def test_invalid_dates_rejected(tmp_path,value):
    with pytest.raises(ValueError):local.LocalPostMarketAdapter(tmp_path).download_core(value,value)


def test_no_invented_preclose():
    got=local.LocalPostMarketAdapter._bars([dict(date='20260910',open=10,high=11,low=9,close=10,volume=100,amount=1000)],'sh600000','20260910','20260910')[0]
    assert 'pre_close' not in got


def test_network_error_retains_local_artifacts_and_manifest(tmp_path,monkeypatch):
    adapter=local.LocalPostMarketAdapter(tmp_path)
    monkeypatch.setattr(adapter,'_supplementary',lambda s,e:None)
    monkeypatch.setattr(adapter,'_local',lambda s,e:adapter._save('daily',[{'trade_date':s,'ts_code':'600000.SH','close':10}]))
    def fail(*a):raise TimeoutError('bounded')
    monkeypatch.setattr(adapter,'_public',fail)
    adapter.download_core('20260910','20260910')
    result=json.loads((tmp_path/'acquisition_manifest.json').read_text(encoding='utf-8'))
    assert result['status']=='PARTIAL' and not result['full_workflow_completed']
    assert (tmp_path/'daily/20260910.csv').exists()
    assert 'stock_st' in result['missing_tables']
    assert not (tmp_path/'stock_st').exists()


def test_wrong_date_public_data_rejected_with_raw_evidence(tmp_path):
    fake=SimpleNamespace(summary_url=lambda d:'https://example.test/?a=1',fetch_json=lambda *a,**k:{'success':True,'result':{'pages':1,'count':1,'data':[{'TRADE_DATE':'2026-09-09'}]}})
    with pytest.raises(ValueError,match='date_out_of_range'):
        local.LocalPostMarketAdapter(tmp_path)._public_rows(fake,'TEST','20260910','20260910',math.inf)
    assert (tmp_path/'source_evidence/TEST-20260910-20260910-1.json').exists()


def test_pagination_not_silently_truncated(tmp_path):
    fake=SimpleNamespace(summary_url=lambda d:'https://example.test/?a=1',fetch_json=lambda *a,**k:{'success':True,'result':{'pages':2,'count':2,'data':[{'TRADE_DATE':'2026-09-10'}]}})
    with pytest.raises(ValueError,match='single_date_exceeds_page_limit'):
        local.LocalPostMarketAdapter(tmp_path,max_pages=1)._public_rows(fake,'TEST','20260910','20260910',math.inf)


def test_bj_prefix_not_shanghai():
    assert local._code('920001')=='920001.BJ'
    with pytest.raises(ValueError):local._code('510050')


def test_nonfinite_rejected():
    with pytest.raises(ValueError):local._number({'x':float('nan')},'x')


def seat(buy,sell,**kwargs):
    return dict(SECURITY_CODE='600127',TRADE_DATE='2026-09-11',EXPLANATION='三日榜',
        OPERATEDEPT_NAME='沪股通专用',OPERATEDEPT_CODE='100',BUY=buy,SELL=sell,**kwargs)


def test_cross_side_merge_avoids_double_count():
    evidence,accepted,coverage=local.merge_public_seats({'buy':[seat(100,None)],'sell':[seat(None,30)]})
    assert len(accepted)==1 and accepted[0]['net_buy']==70
    assert evidence[0]['source_sides']==['buy','sell']


def test_same_value_duplicate_deduplicated():
    evidence,accepted,coverage=local.merge_public_seats({'buy':[seat(100,30),seat(100,30)],'sell':[seat(100,30)]})
    assert len(accepted)==1 and accepted[0]['buy']==100


def test_conflicting_amount_preserved_but_not_accepted():
    evidence,accepted,coverage=local.merge_public_seats({'buy':[seat(100,30)],'sell':[seat(101,30)]})
    assert not accepted and coverage['conflicting_seats']==1
    assert evidence[0]['buy'] is None and evidence[0]['net_buy'] is None
    assert len(evidence[0]['raw_source_rows'])==2


def test_unknown_counterpart_not_zero_or_claimed_net():
    evidence,accepted,coverage=local.merge_public_seats({'buy':[seat(100,None,NET=100)]})
    assert evidence[0]['sell'] is None and evidence[0]['net_buy'] is None
    assert accepted==[] and coverage['incomplete_seats']==1


def test_incomplete_group_excludes_its_complete_seats():
    second=seat(40,20);second['OPERATEDEPT_CODE']='101';second['OPERATEDEPT_NAME']='另一席位'
    evidence,accepted,coverage=local.merge_public_seats({'buy':[seat(100,None),second]})
    assert len(evidence)==2 and accepted==[]


def test_distinct_reasons_never_merged():
    other=seat(None,30);other['EXPLANATION']='一日榜'
    evidence,accepted,coverage=local.merge_public_seats({'buy':[seat(100,None)],'sell':[other]})
    assert len(evidence)==2 and accepted==[]


def test_anonymous_institutions_are_not_a_single_unique_seat():
    one=seat(100,30);one.update(OPERATEDEPT_CODE='0',OPERATEDEPT_NAME='机构专用')
    two=dict(one,BUY=200)
    evidence,accepted,coverage=local.merge_public_seats({'buy':[one,two],'sell':[one]})
    assert len(evidence)==3 and accepted==[]
    assert coverage['anonymous_unmergeable_rows']==3


@pytest.mark.parametrize('code',['110001','123001','510050','900901','200001','700001'])
def test_non_a_share_rejected(code):
    with pytest.raises(ValueError):local._code(code)


@pytest.mark.parametrize("code",["899050","899601"])
def test_bse_indices_never_enter_equity_universe(code):
    with pytest.raises(ValueError,match="non_a_share_index"):local._code(code)
