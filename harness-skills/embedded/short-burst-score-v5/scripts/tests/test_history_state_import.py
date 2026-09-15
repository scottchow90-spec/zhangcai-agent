import json,hashlib
import pandas as pd
import pytest
from lhbpost.data.history_state_import import import_history_states,read_bound


def source(root,relative,method,args,rows):
    p=root/relative;p.parent.mkdir(parents=True,exist_ok=True)
    frame=pd.DataFrame(rows);frame.to_csv(p,index=False,encoding='utf-8-sig');raw=p.read_bytes()
    meta=dict(provider='baostock',status='OK',method=method,arguments=args,path=str(p.resolve()),
        sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),row_count=len(frame),fields=list(frame.columns))
    p.with_name(p.name+'.source.json').write_text(json.dumps(meta),encoding='utf-8')
    return p


def fixture(tmp_path,st='0',missing=False):
    root=tmp_path/'source';out=tmp_path/'out';root.mkdir();(out/'daily').mkdir(parents=True)
    (root/'acquisition_manifest.json').write_text(json.dumps(dict(schema='BAOSTOCK_MARKET_HISTORY_SOURCE_V1',
        status='ACQUIRED_PROVIDER_SCOPE',start_date='2026-09-10',target_date='2026-09-11',market_complete_verified=False)))
    for date in ['2026-09-10','2026-09-11']:
        pd.DataFrame([dict(ts_code='600000.SH',trade_date=date.replace('-',''))]).to_csv(out/'daily'/(date.replace('-','')+'.csv'),index=False)
        source(root,f'membership/{date}.csv','query_all_stock',{'day':date},[dict(code='sh.600000',code_name='当日历史名',tradeStatus='1')])
    rows=[dict(date=d,code='sh.600000',isST=st,tradestatus='1',preclose='10.2',turn='1.2') for d in ['2026-09-10','2026-09-11'] if not missing or d!='2026-09-11']
    source(root,'history/sh.600000.csv','query_history_k_data_plus',dict(code='sh.600000',start_date='2026-09-10',end_date='2026-09-11',frequency='d',adjustflag='3'),rows)
    source(root,'stock_basic.csv','query_stock_basic',{},[dict(code='sh.600000',code_name='当前名称不用作历史',ipoDate='1999-11-10',outDate='',type='1',status='1')])
    return root,out


def test_non_st_empty_snapshot_only_with_complete_evidence(tmp_path):
    root,out=fixture(tmp_path)
    result=import_history_states(root,out,'2026-09-10','2026-09-11')
    assert not result['complete'] and result['historical_state_complete'] and result['verified_rows']==2
    assert pd.read_csv(out/'stock_st/20260911.csv').empty
    assert 'name' not in pd.read_csv(out/'bak_basic/20260911.csv').columns
    dense=pd.read_csv(out/'bak_basic/20260911.csv',dtype=str).iloc[0]
    assert dense['is_st']=='0' and dense['list_date']=='19991110'
    assert dense['historical_status_observed']=='True' and 'date=2026-09-11' in dense['status_source']


def test_st_positive_only_sparse_table(tmp_path):
    root,out=fixture(tmp_path,'1')
    result=import_history_states(root,out,'2026-09-10','2026-09-11')
    assert result['historical_state_complete'] and len(pd.read_csv(out/'stock_st/20260911.csv'))==1


def test_missing_state_does_not_become_non_st(tmp_path):
    root,out=fixture(tmp_path,missing=True)
    result=import_history_states(root,out,'2026-09-10','2026-09-11')
    assert not result['complete'] and result['incomplete_dates']==['2026-09-11']
    assert not (out/'stock_st/20260911.csv').exists()
    assert (out/'stock_st/20260910.csv').exists()


def test_mutated_raw_csv_cannot_pass_metadata_hash(tmp_path):
    root,out=fixture(tmp_path)
    p=root/'history/sh.600000.csv';p.write_bytes(p.read_bytes().replace(b'10.2',b'10.3'))
    result=import_history_states(root,out,'2026-09-10','2026-09-11')
    assert not result['complete'] and 'source_hash' in result['source_failures'][0]['error']


def test_unknown_raw_status_not_false(tmp_path):
    root,out=fixture(tmp_path,st='')
    result=import_history_states(root,out,'2026-09-10','2026-09-11')
    assert not result['complete'] and result['verified_rows']==0


def test_running_source_not_accepted(tmp_path):
    root,out=fixture(tmp_path)
    p=root/'acquisition_manifest.json';data=json.loads(p.read_text());data['status']='ACQUIRING';p.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='not_completed'):import_history_states(root,out,'2026-09-10','2026-09-11')


def test_source_query_wrong_code_blocks(tmp_path):
    root,out=fixture(tmp_path)
    p=root/'history/sh.600000.csv.source.json';data=json.loads(p.read_text());data['arguments']['code']='sh.600001';p.write_text(json.dumps(data))
    result=import_history_states(root,out,'2026-09-10','2026-09-11')
    assert not result['complete'] and result['verified_rows']==0


def test_same_reported_name_cannot_override_observed_st_transition(tmp_path):
    root,out=fixture(tmp_path)
    for date in ['2026-09-10','2026-09-11']:
        source(root,f'membership/{date}.csv','query_all_stock',{'day':date},[dict(code='sh.600000',code_name='*ST九鼎',tradeStatus='1')])
    source(root,'history/sh.600000.csv','query_history_k_data_plus',dict(code='sh.600000',start_date='2026-09-10',end_date='2026-09-11',frequency='d',adjustflag='3'),
        [dict(date=date,code='sh.600000',isST=st,tradestatus='1',preclose='10',turn='1') for date,st in [('2026-09-10','0'),('2026-09-11','1')]])
    result=import_history_states(root,out,'2026-09-10','2026-09-11')
    assert not result['historical_name_coverage_complete'] and result['historical_state_complete']
    assert pd.read_csv(out/'stock_st/20260910.csv').empty
    assert len(pd.read_csv(out/'stock_st/20260911.csv'))==1
    for path in (out/'bak_basic').glob('*.csv'):
        x=pd.read_csv(path);assert 'name' not in x and x.name_temporality.eq('current_or_unverified').all()
