from pathlib import Path
import csv,hashlib,json
import pytest
from lhbpost.current_streaks_source import verify_current_streaks_evidence

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj),encoding='utf-8')
def fixture(tmp_path):
    target='20260911';sources=[]
    for day,info in [('20260911',[{'code':'600088','latest':11,'high_days':'首板'}]),('20260910',[])]:
        path=tmp_path/(day+'.json');save(path,{'status_code':0,'data':{'date':day,'info':info,'page':{'total':len(info),'page':1,'count':1}}})
        sources.append({'requested_date':day,'path':str(path),'sha256':sha(path),'rows':len(info),'url':'https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool','request_params':{'date':day,'page':1}})
    path=tmp_path/'streaks.csv'
    fields=['trade_date','ts_code','board_streak','market_height_rank','is_limit_up','is_limit_down','up_limit','down_limit','no_limit']
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows([
            dict(zip(fields,['20260911','600088.SH',1,1,True,False,11,9,False])),
            dict(zip(fields,['20260911','002242.SZ',0,2,False,False,11,9,False]))])
    cal=tmp_path/'calendar.csv';cal.write_text('cal_date,is_open\n20260910,1\n20260911,1\n')
    response=tmp_path/'calendar-source.json';save(response,{'method':'TQ.get_trading_dates','market':'SH','count':-1,'returncode':0,'request_end':target,'stdout':'CALENDAR_JSON=["20260910","20260911"]'})
    p=tmp_path/'proof.json';proof={'schema':'CURRENT_DAY_VERIFIED_SEALED_STREAKS_V1','trade_date':'2026-09-11','universe':2,'current_sealed_count':1,'csv_path':str(path),'csv_sha256':sha(path),'bounded_prior_pool_dates':['20260910'],'source_bindings':sources,'calendar_evidence':{'path':str(cal),'sha256':sha(cal),'source_response':str(response),'source_response_sha256':sha(response)}};save(p,proof)
    return path,p,proof

def test_rebuilds_streaks_from_bound_raw(tmp_path):
    path,p,proof=fixture(tmp_path);r=verify_current_streaks_evidence(path,p)
    assert r['reconstructed_streaks']=={'600088.SH':1} and r['verified']

def test_rejects_csv_edit_even_when_csv_hash_is_updated(tmp_path):
    path,p,proof=fixture(tmp_path)
    path.write_text(path.read_text().replace('600088.SH,1,1','600088.SH,2,1'))
    proof['csv_sha256']=sha(path);save(p,proof)
    with pytest.raises(ValueError,match='csv_value_mismatch'):verify_current_streaks_evidence(path,p)

def test_rejects_dense_rank_edit_even_when_hash_updated(tmp_path):
    path,p,proof=fixture(tmp_path)
    path.write_text(path.read_text().replace('002242.SZ,0,2','002242.SZ,0,1'))
    proof['csv_sha256']=sha(path);save(p,proof)
    with pytest.raises(ValueError,match='dense_rank_mismatch'):verify_current_streaks_evidence(path,p)

def test_rejects_raw_hash_tamper(tmp_path):
    path,p,proof=fixture(tmp_path);Path(proof['source_bindings'][0]['path']).write_text('{}')
    with pytest.raises(ValueError,match='raw_hash'):verify_current_streaks_evidence(path,p)

def test_rejects_incomplete_page_even_when_bound_hash_updated(tmp_path):
    path,p,proof=fixture(tmp_path);q=Path(proof['source_bindings'][0]['path']);r=json.loads(q.read_text());r['data']['page']['total']=2;save(q,r);proof['source_bindings'][0]['sha256']=sha(q);save(p,proof)
    with pytest.raises(ValueError,match='pool_incomplete'):verify_current_streaks_evidence(path,p)

def test_rejects_returned_date_even_when_bound_hash_updated(tmp_path):
    path,p,proof=fixture(tmp_path);q=Path(proof['source_bindings'][0]['path']);r=json.loads(q.read_text());r['data']['date']='20260910';save(q,r);proof['source_bindings'][0]['sha256']=sha(q);save(p,proof)
    with pytest.raises(ValueError,match='source_response'):verify_current_streaks_evidence(path,p)

def test_rejects_unterminated_chain(tmp_path):
    path,p,proof=fixture(tmp_path);q=Path(proof['source_bindings'][1]['path']);r=json.loads(q.read_text());r['data']['info']=[{'code':'600088','latest':10}];r['data']['page']['total']=1;save(q,r);proof['source_bindings'][1]['sha256']=sha(q);proof['source_bindings'][1]['rows']=1;save(p,proof)
    with pytest.raises(ValueError,match='chain_unterminated'):verify_current_streaks_evidence(path,p)

def test_rejects_calendar_source_fabrication_by_csv_edit(tmp_path):
    path,p,proof=fixture(tmp_path);q=Path(proof['calendar_evidence']['path']);q.write_text('cal_date,is_open\n20260911,1\n');proof['calendar_evidence']['sha256']=sha(q);save(p,proof)
    with pytest.raises(ValueError,match='source_table_mismatch'):verify_current_streaks_evidence(path,p)

def test_rejects_duplicate_pool_member_even_updated_hash(tmp_path):
    path,p,proof=fixture(tmp_path);q=Path(proof['source_bindings'][0]['path']);r=json.loads(q.read_text());r['data']['info']*=2;r['data']['page']['total']=2;save(q,r);proof['source_bindings'][0]['sha256']=sha(q);proof['source_bindings'][0]['rows']=2;save(p,proof)
    with pytest.raises(ValueError,match='duplicate_pool_member'):verify_current_streaks_evidence(path,p)
