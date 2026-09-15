"""Portable real-file tests for source replay, not claimed aggregate flags."""
import csv
import hashlib
import io
import json
from pathlib import Path
import pytest
from lhbpost import limit_followthrough_reference as ref

CODE='600088.SH'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write_source(path,rows,method,args):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows);raw=stream.getvalue().encode('utf-8-sig')
    path.write_bytes(raw)
    metadata={'provider':'baostock','status':'OK','method':method,'arguments':args,
              'path':str(path.resolve()),'sha256':digest(path),'bytes':len(raw),
              'fields':list(rows[0]),'row_count':len(rows),
              'attempts':[{'status':'OK','started_at':'2026-09-12T00:01:00+08:00',
                           'ended_at':'2026-09-12T00:01:01+08:00'}]}
    meta=Path(str(path)+'.source.json');meta.write_text(json.dumps(metadata),encoding='utf-8')
    return {'path':str(path.resolve()),'sha256':digest(path),'metadata_sha256':digest(meta),'row_count':len(rows)}


@pytest.fixture
def source_summary(tmp_path,monkeypatch):
    dayrows=[{'date':day,'code':'sh.600088','open':close,'high':close,'low':close,'close':close,
              'preclose':pre,'isST':'0','tradestatus':'1'} for day,close,pre in
             [('2026-09-09','11','10'),('2026-09-10','11.2','11'),('2026-09-11','11.2','11.2')]]
    calendar=[{'calendar_date':day,'is_trading_day':'1'} for day in ['2026-09-09','2026-09-10','2026-09-11']]
    basic=[{'code':'sh.600088','code_name':'9月12日才存在的新名称','ipoDate':'1997-06-16','outDate':'',
            'status':'0','type':'99'}]
    bounds={'calendar':write_source(tmp_path/'calendar.csv',calendar,'query_trade_dates',
                                    {'start_date':'2026-09-09','end_date':'2026-09-11'})}
    bounds[CODE+'.daily']=write_source(tmp_path/'daily.csv',dayrows,'query_history_k_data_plus',
        {'code':'sh.600088','fields':','.join(dayrows[0]),'start_date':'2026-09-09',
         'end_date':'2026-09-11','frequency':'d','adjustflag':'3'})
    bounds[CODE+'.basic']=write_source(tmp_path/'basic.csv',basic,'query_stock_basic',{'code':'sh.600088'})
    hashes={};rules={}
    for market,year in [('SH',2023),('SH',2026),('SZ',2023),('SZ',2026)]:
        path=tmp_path/f'{market}-{year}.rule';path.write_bytes(f'test-rule-{market}-{year}'.encode())
        hashes[(market,year)]=digest(path)
        rules[(market,year)]={'path':str(path.resolve()),'sha256':digest(path),'version':year,'exchange':market}
    monkeypatch.setattr(ref,'RULE_HASHES',hashes)
    bounds['rules']={m+str(y):r for (m,y),r in rules.items()}
    summary,labels=ref.build_reference(codes=[CODE],start='2026-09-09',end='2026-09-11',
        histories={CODE:dayrows},calendar_rows=calendar,basics={CODE:{'ipoDate':basic[0]['ipoDate'],'outDate':''}},
        rules=rules,source_bindings=bounds)
    summary['research_event_artifact_sha256']=hashlib.sha256(json.dumps(labels,ensure_ascii=False,indent=2,allow_nan=False).encode()).hexdigest()
    return summary


def rebind_metadata(summary,label,mutate):
    binding=summary['source_bindings'][label];path=Path(binding['path']+'.source.json')
    body=json.loads(path.read_text(encoding='utf-8'));mutate(body)
    path.write_text(json.dumps(body),encoding='utf-8');binding['metadata_sha256']=digest(path)


def test_replay_reads_sources_and_ignores_later_basic_names_status(source_summary):
    result=ref.replay_bound_reference(source_summary)
    assert result['verified'] and result['replayed_stock_count']==1 and result['source_count']==3
    assert result['stocks_all_fields_match'] and result['definitions_match']
    assert result['replayed_summary']['stocks']==source_summary['stocks']
    assert result['replayed_summary']['stocks'][0]['next_close_premium_count']==1
    assert result['production_qualified'] is False


@pytest.mark.parametrize('field,value',[('next_close_premium_count',0),('mean_next_close_return',0),
                                      ('next_open_premium_count_auxiliary',0),('limit_up_count',99)])
def test_tampered_stock_aggregate_cannot_pass(source_summary,field,value):
    source_summary['stocks'][0][field]=value
    with pytest.raises(ValueError,match='reference_replay_mismatch:stocks'):ref.replay_bound_reference(source_summary)


@pytest.mark.parametrize('field,value',[('primary_outcome','next_high_above_close'),
    ('production_qualified',True),('reference_complete',False),('future_outcomes_beyond_cutoff_used',True),
    ('rule_replay_verified',True),('denominator_policy','include_pending')])
def test_tampered_definition_or_completion_claim_cannot_pass(source_summary,field,value):
    source_summary[field]=value
    with pytest.raises(ValueError,match='reference_replay_mismatch:'+field):ref.replay_bound_reference(source_summary)


def test_changed_csv_bytes_rejected(source_summary):
    p=Path(source_summary['source_bindings'][CODE+'.daily']['path']);p.write_bytes(p.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='source_hash_mismatch'):ref.replay_bound_reference(source_summary)


def test_changed_source_receipt_rejected_before_loading_csv(source_summary):
    p=Path(source_summary['source_bindings'][CODE+'.daily']['path']+'.source.json')
    p.write_text(p.read_text(encoding='utf-8')+' ',encoding='utf-8')
    with pytest.raises(ValueError,match='reference_metadata_binding_mismatch'):ref.replay_bound_reference(source_summary)


@pytest.mark.parametrize('field,value',[('code','sh.600207'),('adjustflag','1'),('frequency','5'),
                                       ('extra_unapproved_argument',True)])
def test_query_identity_rejected_even_with_updated_receipt_hash(source_summary,field,value):
    rebind_metadata(source_summary,CODE+'.daily',lambda m:m['arguments'].__setitem__(field,value))
    with pytest.raises(ValueError,match='reference_source_query_identity'):ref.replay_bound_reference(source_summary)


def test_query_end_after_cutoff_cannot_hide_future_rows(source_summary):
    rebind_metadata(source_summary,CODE+'.daily',lambda m:m['arguments'].__setitem__('end_date','2026-09-14'))
    with pytest.raises(ValueError,match='reference_source_date_range_mismatch'):ref.replay_bound_reference(source_summary)


def test_rebound_source_path_metadata_must_still_match(source_summary):
    rebind_metadata(source_summary,CODE+'.daily',lambda m:m.__setitem__('path',m['path']+'.other'))
    with pytest.raises(ValueError,match='source_path_mismatch'):ref.replay_bound_reference(source_summary)


def test_source_capture_before_target_close_rejected(source_summary):
    def change(meta):
        meta['attempts'][0].update(started_at='2026-09-11T10:00:00+08:00',ended_at='2026-09-11T10:00:01+08:00')
    rebind_metadata(source_summary,CODE+'.daily',change)
    with pytest.raises(ValueError,match='reference_source_capture_time_invalid'):ref.replay_bound_reference(source_summary)


def test_changed_rule_document_cannot_be_unlocked_by_summary(source_summary):
    p=Path(source_summary['source_bindings']['rules']['SH2023']['path']);p.write_bytes(b'changed')
    with pytest.raises(ValueError,match='reference_rule_file_identity_mismatch'):ref.replay_bound_reference(source_summary)


def test_extra_bound_stock_is_rejected(source_summary):
    source_summary['source_bindings']['600207.SH.daily']=source_summary['source_bindings'][CODE+'.daily']
    with pytest.raises(ValueError,match='reference_source_binding_scope_mismatch'):ref.replay_bound_reference(source_summary)


def test_count_boolean_cannot_pass_as_integer_one(source_summary):
    source_summary['source_bindings'][CODE+'.basic']['row_count']=True
    with pytest.raises(ValueError,match='reference_source_binding_count'):ref.replay_bound_reference(source_summary)


def test_unknown_aggregate_field_does_not_enter_snapshot(source_summary):
    source_summary['pretend_source_verified']=True
    with pytest.raises(ValueError,match='reference_unverified_extra_fields'):ref.replay_bound_reference(source_summary)


def test_research_label_artifact_hash_matches_actual_replayed_events(source_summary):
    source_summary['research_event_artifact_sha256']='0'*64
    with pytest.raises(ValueError,match='reference_research_labels_replay_mismatch'):ref.replay_bound_reference(source_summary)


def test_relative_source_path_is_rejected(source_summary):
    source_summary['source_bindings']['calendar']['path']='calendar.csv'
    with pytest.raises(ValueError,match='reference_source_path_not_absolute'):ref.replay_bound_reference(source_summary)


@pytest.mark.parametrize('field,value,error',[('code','sh.600207','reference_source_row_identity'),
    ('date','2026-09-14','reference_source_row_dates')])
def test_source_row_identity_rejected_with_self_consistent_rehashed_files(source_summary,field,value,error):
    binding=source_summary['source_bindings'][CODE+'.daily'];path=Path(binding['path'])
    meta=json.loads(Path(str(path)+'.source.json').read_text(encoding='utf-8'))
    with path.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
    rows[0][field]=value
    source_summary['source_bindings'][CODE+'.daily']=write_source(path,rows,meta['method'],meta['arguments'])
    with pytest.raises(ValueError,match=error):ref.replay_bound_reference(source_summary)


def test_source_mutated_after_read_but_before_replay_acceptance_is_rejected(source_summary,monkeypatch):
    original=ref.build_reference
    path=Path(source_summary['source_bindings'][CODE+'.daily']['path'])
    def mutation(**kwargs):
        result=original(**kwargs);path.write_bytes(path.read_bytes()+b'\n');return result
    monkeypatch.setattr(ref,'build_reference',mutation)
    with pytest.raises(ValueError,match='reference_source_changed_during_replay'):ref.replay_bound_reference(source_summary)
