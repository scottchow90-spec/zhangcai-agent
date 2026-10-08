import json
import pandas as pd
import pytest
from lhbpost.data.local_pit_orchestrator import verified_ipo_calendar,current_limit_with_evidence

def create_source(root):
    folder=root/'source_evidence';folder.mkdir()
    dates=['20260904','20260907']
    proof=dict(method='TQ.get_trading_dates',market='SH',request_start='20260904',request_end='20260907',
        count=-1,returncode=0,stdout='CALENDAR_JSON='+json.dumps(dates),stderr='')
    (folder/'tq_calendar_response.json').write_text(json.dumps(proof),encoding='utf-8')
    pd.DataFrame([dict(cal_date=d,is_open=1) for d in dates]).to_csv(root/'trade_cal.csv',index=False)
    return proof

def test_complete_source_expands_explicit_closed_dates(tmp_path):
    create_source(tmp_path)
    rows=verified_ipo_calendar(tmp_path,'20260904','20260907')
    assert [r['is_open'] for r in rows]==[1,0,0,1]

@pytest.mark.parametrize('field,value',[('count',1),('request_start','20260905'),('returncode',1)])
def test_incomplete_or_wrong_request_not_calendar_evidence(tmp_path,field,value):
    proof=create_source(tmp_path);proof[field]=value
    (tmp_path/'source_evidence/tq_calendar_response.json').write_text(json.dumps(proof),encoding='utf-8')
    with pytest.raises(ValueError):verified_ipo_calendar(tmp_path,'20260904','20260907')

def test_missing_open_day_in_table_is_not_called_holiday(tmp_path):
    create_source(tmp_path)
    pd.DataFrame([dict(cal_date='20260907',is_open=1)]).to_csv(tmp_path/'trade_cal.csv',index=False)
    with pytest.raises(ValueError):verified_ipo_calendar(tmp_path,'20260904','20260907')

def test_official_packaged_rule_no_limit_integration(tmp_path):
    create_source(tmp_path)
    pd.DataFrame([dict(ts_code='603448.SH',list_date='20260907')]).to_csv(tmp_path/'stock_basic.csv',index=False)
    result=current_limit_with_evidence(tmp_path,'603448.SH',dict(HqDate='20260907',ZTPrice='0.00',DTPrice='0.00',IsZCZGP='1'),'20260904','20260907')
    assert result['no_limit']==1 and result['up_limit'] is None and result['down_limit'] is None
    assert result['listing_session_no']==1 and len(result['calendar_source_sha256'])==64
