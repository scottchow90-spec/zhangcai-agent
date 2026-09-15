"""Portable synthetic regression for the audited explicit-list request path."""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from urllib.parse import urlencode

import pandas as pd
import pytest

import local_business as local
import workbuddy_entry as entry
from lhbpost import selected_workflow as workflow
from lhbpost.data.public_window_acquisition import sha

DATE='2026-09-11'


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')


@pytest.fixture
def sources(tmp_path):
    from lhbpost.data.local_postmarket import summary_record
    root=tmp_path/'inputs';evidence=root/'source_evidence';evidence.mkdir(parents=True)
    records=[{'SECURITY_CODE':'600000','TRADE_DATE':DATE+' 00:00:00','EXPLANATION':'涨幅偏离',
              'TRADE_ID':str(101+i),'CHANGE_TYPE':'A','BILLBOARD_BUY_AMT':100+i,
              'BILLBOARD_SELL_AMT':50,'BILLBOARD_NET_AMT':50+i} for i in range(2)]
    records[1]['SECURITY_CODE']='600001'
    for page,record in enumerate(records,1):
        params={'sortColumns':'TRADE_DATE','sortTypes':'-1','pageSize':'5000','pageNumber':str(page),
                'reportName':workflow.REPORT,'columns':'ALL','source':'WEB','client':'WEB',
                'filter':f"(TRADE_DATE>='{DATE}')(TRADE_DATE<='{DATE}')"}
        payload={'success':True,'result':{'pages':2,'count':2,'data':[record]}}
        write(evidence/f'{workflow.REPORT}-20260911-20260911-{page}.json',
              {'url':'https://datacenter-web.eastmoney.com/api/data/v1/get?'+urlencode(params),
               'payload':payload,'payload_sha256':sha(payload)})
    write(evidence/f'{workflow.REPORT}-20260911-20260911-windows.json',
          {'report':workflow.REPORT,'range':['20260911','20260911'],
           'completed_windows':[{'start':'20260911','end':'20260911','rows':2}]})
    table=pd.DataFrame([summary_record(r) for r in records]);(root/'top_list').mkdir()
    table.to_csv(root/'top_list/20260911.csv',index=False)
    table['trade_date']=pd.to_datetime(table['trade_date'],format='%Y%m%d')
    return root,table


def test_source_pages_and_csv_prove_day_without_manifest_success(sources,tmp_path):
    root,table=sources
    write(root/'acquisition_manifest.json',{'status':'ACQUIRING','full_workflow_completed':False})
    proof=workflow.verify_billboard_day(root,DATE,table,tmp_path/'proof.json')
    assert proof['status']=='PASS'
    assert proof['verified_complete_dates']==[DATE]
    assert proof['listed_codes']==['600000.SH','600001.SH']
    assert len(proof['bindings'])==4


@pytest.mark.parametrize('fault',['missing_page','wrong_url_date','wrong_host','wrong_hash','wrong_count','wrong_row_date','missing_csv_row','duplicated_csv_row'])
def test_tampered_billboard_cannot_prove_absence(sources,tmp_path,fault):
    root,table=sources
    page=root/'source_evidence'/f'{workflow.REPORT}-20260911-20260911-2.json'
    data=json.loads(page.read_text(encoding='utf-8'))
    if fault=='missing_page':page.unlink()
    elif fault=='wrong_url_date':
        data['url']=data['url'].replace('2026-09-11','2026-09-10');write(page,data)
    elif fault=='wrong_host':
        data['url']=data['url'].replace('datacenter-web.eastmoney.com','invalid.example');write(page,data)
    elif fault=='wrong_hash':data['payload_sha256']='0'*64;write(page,data)
    elif fault=='wrong_count':
        data['payload']['result']['count']=3;data['payload_sha256']=sha(data['payload']);write(page,data)
    elif fault=='wrong_row_date':
        data['payload']['result']['data'][0]['TRADE_DATE']='2026-09-12 00:00:00'
        data['payload_sha256']=sha(data['payload']);write(page,data)
    elif fault=='missing_csv_row':table.iloc[:1].to_csv(root/'top_list/20260911.csv',index=False)
    else:pd.concat([table,table.iloc[:1]]).to_csv(root/'top_list/20260911.csv',index=False)
    output=tmp_path/'failed-proof.json'
    with pytest.raises((ValueError,OSError)):
        workflow.verify_billboard_day(root,DATE,table,output)
    assert json.loads(output.read_text(encoding='utf-8'))['status']=='BLOCKED'


def request_file(tmp_path,root,**extra):
    request={'schema':workflow.SCHEMA,'data_root':str(root),'trade_date':DATE,'as_of':DATE+'T23:59:59+08:00',
             'stocks':[{'code':'600000.SH','name':'股票','screenshot_close':10.0}],**extra}
    path=tmp_path/'request.json';write(path,request)
    return path,request


def fake_prepare(a):
    assert a.selected_codes==['600000.SH']
    write(Path(a.audit_output),{'passed':True,'errors':[]})
    write(Path(a.billboard_audit_output),{'status':'PASS','verified_complete_dates':[DATE]})
    write(Path(a.output),{'trade_date':DATE,'as_of':DATE+'T23:59:59+08:00',
                          'stocks':[{'code':'600000.SH','name':'股票','close_price':10.0}]})


def test_new_request_calls_original_prepare_and_history_validation(sources,tmp_path,monkeypatch):
    root,_=sources;path,request=request_file(tmp_path,root)
    run=tmp_path/'run';run.mkdir();artifacts={}
    monkeypatch.setattr(entry,'prepare_cmd',fake_prepare)
    prepared,model=workflow.prepare_selected(request,path,run,artifacts)
    assert model is None and prepared==run/'prepared_snapshot.json'
    history=json.loads((run/'history_model_validation.json').read_text(encoding='utf-8'))
    assert history['model_supplied'] is False
    assert history['validation']['status']=='未启用'
    assert history['production_qualified'] is False
    assert {'raw_data_audit','billboard_source_audit','raw_input_bindings','full_selected_request'}<=set(artifacts)


def test_research_model_is_bound_and_passed_as_third_argument(sources,tmp_path,monkeypatch):
    from lhbpost.research import build_model
    import lhbpost.core as core
    root,_=sources;events=tmp_path/'events.csv'
    events.write_text('event_date,model_bucket,return_t1,return_t3,return_t5,max_return_t5,max_drawdown_t5,code,label_end_date\n2026-08-01,x,0.01,0.02,0.03,0.04,-0.01,600000.SH,2026-08-08\n',encoding='utf-8')
    model_path=tmp_path/'model.json';model=build_model(events,'2026-09-10',model_path)
    path,request=request_file(tmp_path,root,history_model={'path':str(model_path),'sha256':workflow.digest(model_path)})
    run=tmp_path/'run';run.mkdir();called={}
    monkeypatch.setattr(entry,'prepare_cmd',fake_prepare)
    def analyze(snapshot,config,supplied_model):
        called['model']=supplied_model
        return {'results':[{'code':'600000.SH'}]}
    monkeypatch.setattr(core,'analyze_snapshot',analyze)
    monkeypatch.setattr(entry,'render_md',lambda _payload:'synthetic test')
    values=dict(action='analyze',input=str(path),data_root=None,trade_date=None,as_of=None,events=None,cutoff=None,start=None,end=None)
    artifacts=local.execute(argparse.Namespace(**values),run)
    assert called['model']==model
    assert workflow.digest(artifacts['history_model'])==workflow.digest(model_path)
    history=json.loads(Path(artifacts['history_model_validation']).read_text(encoding='utf-8'))
    assert history['validation']['status']=='研究参考'
    assert history['validation']['production_qualified'] is False


def test_raw_audit_failure_retains_evidence_in_local_result(sources,tmp_path,monkeypatch,capsys):
    root,_=sources;path,_=request_file(tmp_path,root);run=tmp_path/'run'
    monkeypatch.setenv('CODEX_STOCK_CANONICAL_EXECUTION','1')
    monkeypatch.setenv('ONESTOCK_STOCK_CANONICAL_CHILD','1')
    monkeypatch.setattr(sys,'argv',['local','--run-dir',str(run),'--action','analyze','--input',str(path)])
    assert local.main()==2
    result=json.loads(capsys.readouterr().out)
    assert result['status']=='BLOCKED' and result['full_workflow_completed'] is False
    for key in ['full_selected_request','raw_input_bindings','raw_data_audit']:
        assert Path(result['artifacts'][key]).is_file()
    audit=json.loads(Path(result['artifacts']['raw_data_audit']).read_text(encoding='utf-8'))
    assert audit['passed'] is False and audit['errors']
    assert 'analysis' not in result['artifacts']


def test_model_hash_failure_keeps_completed_preparation_evidence(sources,tmp_path,monkeypatch):
    root,_=sources;model=tmp_path/'model.json';write(model,{})
    path,request=request_file(tmp_path,root,history_model={'path':str(model),'sha256':'0'*64})
    run=tmp_path/'run';run.mkdir();artifacts={}
    monkeypatch.setattr(entry,'prepare_cmd',fake_prepare)
    with pytest.raises(ValueError,match='history_model_hash_mismatch'):
        workflow.prepare_selected(request,path,run,artifacts)
    assert {'full_selected_request','prepared_snapshot','raw_data_audit'}<=set(artifacts)


def test_screenshot_identity_failure_stops_before_prepare(sources,tmp_path,monkeypatch):
    root,_=sources;image=tmp_path/'screenshot.png';image.write_bytes(b'synthetic fixture')
    path,request=request_file(tmp_path,root,screenshot={'path':str(image),'sha256':'0'*64})
    run=tmp_path/'run';run.mkdir();artifacts={}
    monkeypatch.setattr(entry,'prepare_cmd',lambda _a:pytest.fail('must not prepare on changed request image'))
    with pytest.raises(ValueError,match='screenshot_hash_mismatch'):
        workflow.prepare_selected(request,path,run,artifacts)
    assert Path(artifacts['full_selected_request']).is_file()


@pytest.mark.parametrize('selected',[None,['600010.SH']])
def test_original_prepare_forwards_only_verified_selected_scope(sources,tmp_path,monkeypatch,selected):
    from lhbpost.data_audit import DataAudit
    import lhbpost.data_audit as audit_module
    import lhbpost.snapshot_pipeline as pipeline
    import lhbpost.core as core
    root,_=sources;seen={}
    monkeypatch.setattr(audit_module,'audit_raw_data',lambda *args,**kw:DataAudit(True,(),(),{}))
    def build(**kw):
        seen.update(kw)
        return {'stocks':[],'coverage':{},'workflow_trace':[]}
    monkeypatch.setattr(pipeline,'build_snapshot',build)
    monkeypatch.setattr(core,'validate_snapshot',lambda _snapshot:[])
    args=argparse.Namespace(data_root=str(root),trade_date=DATE,as_of=DATE+'T23:59:59+08:00',
        output=str(tmp_path/'prepared.json'),selected_codes=selected,
        audit_output=str(tmp_path/'audit.json'),billboard_audit_output=str(tmp_path/'billboard.json'))
    assert entry.prepare_cmd(args)==0
    if selected is None:
        assert 'selected_codes' not in seen
        assert not Path(args.billboard_audit_output).exists()
        assert not seen['top_list'].attrs.get('verified_complete_dates')
    else:
        assert seen['selected_codes']==selected
        assert seen['top_list'].attrs['verified_complete_dates']==[DATE]
        assert json.loads(Path(args.billboard_audit_output).read_text(encoding='utf-8'))['status']=='PASS'


def test_prepare_does_not_call_snapshot_after_invalid_source(sources,tmp_path,monkeypatch):
    from lhbpost.data_audit import DataAudit
    import lhbpost.data_audit as audit_module
    import lhbpost.snapshot_pipeline as pipeline
    root,table=sources;table.iloc[:1].to_csv(root/'top_list/20260911.csv',index=False)
    monkeypatch.setattr(audit_module,'audit_raw_data',lambda *args,**kw:DataAudit(True,(),(),{}))
    monkeypatch.setattr(pipeline,'build_snapshot',lambda **kw:pytest.fail('snapshot must not run on mismatched source'))
    args=argparse.Namespace(data_root=str(root),trade_date=DATE,as_of=DATE+'T23:59:59+08:00',
        output=str(tmp_path/'prepared.json'),selected_codes=['600010.SH'],
        audit_output=str(tmp_path/'audit.json'),billboard_audit_output=str(tmp_path/'billboard.json'))
    with pytest.raises(ValueError,match='no_valid_complete_window'):
        entry.prepare_cmd(args)
    assert Path(args.audit_output).is_file()
    assert Path(args.billboard_audit_output).is_file()
    assert not Path(args.output).exists()


@pytest.fixture
def scoped_frames():
    dates=pd.bdate_range(end=DATE,periods=65);rows=[];factors=[]
    for j,code in enumerate(['600000.SH','600001.SH']):
        for i,day in enumerate(dates):
            price=10+j+i*.01
            rows.append({'ts_code':code,'trade_date':day,'open':price,'high':price+.1,'low':price-.1,
                         'close':price,'amount':1000000,'vol':100000})
            factors.append({'ts_code':code,'trade_date':day,'adj_factor':1.0})
    daily=pd.DataFrame(rows);today=daily[daily.trade_date.eq(pd.Timestamp(DATE))].copy()
    return {'daily':daily,'adj_factor':pd.DataFrame(factors),
        'daily_basic':today[['trade_date','ts_code']].assign(turnover_rate=5.,free_mv=100000000.),
        'limits':today[['trade_date','ts_code']].assign(up_limit=13.,down_limit=8.),
        'historical_basic':pd.DataFrame([{'trade_date':pd.Timestamp(DATE),'ts_code':'600000.SH','name':'股票'}]),
        'st_status':pd.DataFrame([{'trade_date':pd.Timestamp(DATE),'ts_code':'600000.SH','is_st':False}]),
        'stock_basic':pd.DataFrame([{'ts_code':'600000.SH','name':'股票','name_as_of':DATE}]),
        'sw_members':pd.DataFrame({'ts_code':['600000.SH','600001.SH'],'l1_code':['I','I'],
                                   'l1_name':['行业','行业'],'in_date':['2010-01-01']*2,'out_date':[None]*2}),
        'calendar':pd.DataFrame({'cal_date':dates}),
        'index_daily':pd.DataFrame([{'ts_code':'000001.SH','trade_date':pd.Timestamp(DATE),'close':3000.,'pct_chg':-.01}]),
        'event_features':pd.DataFrame(columns=['ts_code','trade_date','public_time'])}


def test_scoped_audit_does_not_require_unconsumed_historical_tables(scoped_frames):
    result=workflow.scoped_raw_audit(scoped_frames,['600000.SH'],DATE,DATE+'T23:59:59+08:00')
    assert result.passed,result.errors
    assert 'historical_market_limits' in result.stats['not_consumed_by_user_mode']
    assert result.stats['selected_history_counts']=={'600000.SH':65}


def test_scoped_calendar_missing_date_is_not_a_valid_subset(scoped_frames):
    dropped=scoped_frames['daily'].trade_date.unique()[20]
    scoped_frames['daily']=scoped_frames['daily'][~scoped_frames['daily'].trade_date.eq(dropped)].copy()
    result=workflow.scoped_raw_audit(scoped_frames,['600000.SH'],DATE,DATE+'T23:59:59+08:00')
    assert not result.passed and 'market_session' in str(result.errors)


def test_scoped_individual_missing_date_requires_true_suspension(scoped_frames):
    day=scoped_frames['daily'].trade_date.unique()[20]
    scoped_frames['daily']=scoped_frames['daily'][~(scoped_frames['daily'].trade_date.eq(day)&scoped_frames['daily'].ts_code.eq('600000.SH'))].copy()
    result=workflow.scoped_raw_audit(scoped_frames,['600000.SH'],DATE,DATE+'T23:59:59+08:00')
    assert not result.passed and 'unexplained_missing' in str(result.errors)
    scoped_frames['verified_suspensions']={('600000.SH',pd.Timestamp(day))}
    result=workflow.scoped_raw_audit(scoped_frames,['600000.SH'],DATE,DATE+'T23:59:59+08:00')
    assert result.passed,result.errors


def test_unselected_reference_na_keeps_original_rank_denominator(scoped_frames):
    frame=scoped_frames['daily_basic']
    frame.loc[frame.ts_code.eq('600001.SH'),'free_mv']=float('nan')
    result=workflow.scoped_raw_audit(scoped_frames,['600000.SH'],DATE,DATE+'T23:59:59+08:00')
    assert result.passed,result.errors
    assert result.stats['free_mv_reference_effective_denominator']==1
    assert result.stats['free_mv_reference_missing_codes']==['600001.SH']
    assert pd.isna(frame.loc[frame.ts_code.eq('600001.SH'),'free_mv']).all()


@pytest.mark.parametrize('value',[float('nan'),0.0,-1.0,float('inf')])
def test_selected_free_float_never_receives_na_exemption(scoped_frames,value):
    frame=scoped_frames['daily_basic']
    frame.loc[frame.ts_code.eq('600000.SH'),'free_mv']=value
    result=workflow.scoped_raw_audit(scoped_frames,['600000.SH'],DATE,DATE+'T23:59:59+08:00')
    assert not result.passed


@pytest.mark.parametrize('value',[-1.0,float('inf'),'bad'])
def test_nonempty_invalid_reference_value_still_rejected(scoped_frames,value):
    frame=scoped_frames['daily_basic'].astype({'free_mv':'object'})
    frame.loc[frame.ts_code.eq('600001.SH'),'free_mv']=value
    scoped_frames['daily_basic']=frame
    result=workflow.scoped_raw_audit(scoped_frames,['600000.SH'],DATE,DATE+'T23:59:59+08:00')
    assert not result.passed


@pytest.mark.parametrize('fault',['missing_factor','missing_T_limits','missing_T_ST','missing_T_basic','bad_price','future_event'])
def test_scoped_audit_still_rejects_consumed_missing_or_invalid(scoped_frames,fault):
    if fault=='missing_factor':scoped_frames['adj_factor']=scoped_frames['adj_factor'].iloc[1:].copy()
    elif fault=='missing_T_limits':scoped_frames['limits']=scoped_frames['limits'].iloc[:1].copy()
    elif fault=='missing_T_ST':scoped_frames['st_status']=scoped_frames['st_status'].iloc[:0].copy()
    elif fault=='missing_T_basic':scoped_frames['daily_basic']=scoped_frames['daily_basic'].iloc[:1].copy()
    elif fault=='bad_price':scoped_frames['daily'].loc[0,'high']=1.
    else:scoped_frames['event_features']=pd.DataFrame([{'ts_code':'600000.SH','trade_date':pd.Timestamp(DATE),'public_time':'2026-09-12T01:00:00+08:00'}])
    result=workflow.scoped_raw_audit(scoped_frames,['600000.SH'],DATE,DATE+'T23:59:59+08:00')
    assert not result.passed and result.errors


def user_reference(tmp_path):
    record={'schema':'SELECTED_ONE_YEAR_LIMIT_CLOSE_FOLLOWTHROUGH_V1','start_date':'2025-09-12','end_date':DATE,'as_of_date':DATE,
            'requested_codes':['600000.SH'],'reference_complete':True,'production_qualified':False,'rule_replay_verified':False,
            'original_eight_causal_market_metrics_reconstructed':False,'stocks':[{'ts_code':'600000.SH',
                'limit_up_count':3,'settled_event_count':2,'observed_next_session_count':2,'next_close_premium_count':1,
                'next_close_no_premium_count':1,'next_close_flat_count':0,'next_session_suspended_count':0,'pending_next_session_count':1}]}
    file=tmp_path/'reference.json';write(file,record)
    streak=tmp_path/'streak.csv';pd.DataFrame([{'ts_code':'600000.SH','trade_date':DATE,'board_streak':1}]).to_csv(streak,index=False)
    proof=tmp_path/'streak-proof.json';write(proof,{'synthetic_fixture':True})
    request={'trade_date':DATE,'stocks':[{'code':'600000.SH'}],
             'market_reference':{'mode':'yearly-limit-close-premium','input':str(file),'sha256':workflow.digest(file)},
             'current_streaks':{'path':str(streak),'sha256':workflow.digest(streak),
                'proof':{'path':str(proof),'sha256':workflow.digest(proof)}}}
    return request,file


def test_year_reference_labels_stay_outside_snapshot_and_score_inputs(tmp_path,monkeypatch):
    request,file=user_reference(tmp_path);run=tmp_path/'run';run.mkdir();artifacts={}
    monkeypatch.setitem(sys.modules,'lhbpost.limit_followthrough_reference',SimpleNamespace(replay_bound_reference=lambda record:{'verified':True,'synthetic_test':True}))
    monkeypatch.setitem(sys.modules,'lhbpost.current_streaks_source',SimpleNamespace(verify_current_streaks_evidence=lambda *args:{'verified':True,'synthetic_test':True}))
    metadata,streaks=workflow.load_user_market_reference(request,run,artifacts)
    assert metadata['affects_scoring'] is False
    assert not any('next_' in str(k) for k in metadata)
    assert 'stocks' not in metadata
    assert workflow.digest(artifacts['historical_reference'])==workflow.digest(file)
    assert len(streaks)==1
    assert {'historical_reference_replay','current_streaks_source_check'}<=set(artifacts)


@pytest.mark.parametrize('fault',['false_production','wrong_scope','false_counts','wrong_date','wrong_hash'])
def test_year_reference_rejects_false_identity_or_promotion(tmp_path,fault):
    request,file=user_reference(tmp_path);record=json.loads(file.read_text())
    if fault=='false_production':record['production_qualified']=True
    elif fault=='wrong_scope':record['requested_codes']=['600099.SH']
    elif fault=='false_counts':record['stocks'][0]['next_close_premium_count']=2
    elif fault=='wrong_date':record['as_of_date']='2026-09-12'
    write(file,record);request['market_reference']['sha256']=workflow.digest(file)
    if fault=='wrong_hash':request['market_reference']['sha256']='0'*64
    run=tmp_path/'run';run.mkdir()
    with pytest.raises(ValueError):workflow.load_user_market_reference(request,run,{})


def test_reference_replay_failure_cannot_be_hidden_by_complete_summary(tmp_path,monkeypatch):
    request,file=user_reference(tmp_path);run=tmp_path/'run';run.mkdir()
    def fail(_summary):raise ValueError('source_replay_does_not_match')
    monkeypatch.setitem(sys.modules,'lhbpost.limit_followthrough_reference',SimpleNamespace(replay_bound_reference=fail))
    with pytest.raises(ValueError,match='source_replay_does_not_match'):
        workflow.load_user_market_reference(request,run,{})


@pytest.mark.parametrize('fault',[None,'scope','source_hash','query_failure','count'])
def test_official_announcement_scope_binding(tmp_path,fault):
    raw=tmp_path/'raw.json';write(raw,{'synthetic_fixture':True})
    row={'ts_code':'600000.SH','cninfo_query_success':True,'eastmoney_query_success':True,
         'cninfo_complete_for_query':True,'eastmoney_complete_for_query':True,
         'cninfo_query_date_range':DATE+'~2026-09-12','eastmoney_query_notice_date_range':DATE+'~2026-09-12',
         'all_public_events_complete':False,'source_files':[{'path':str(raw),'sha256':workflow.digest(raw)}]}
    report={'schema':'NINE_COMPANY_ANNOUNCEMENT_REVIEW_V1','trade_date':DATE,'as_of':DATE+'T23:59:59+08:00',
            'candidates':[row],'event_count':0,'t_day_new_event_count':0}
    if fault=='scope':row['all_public_events_complete']=True
    elif fault=='source_hash':row['source_files'][0]['sha256']='0'*64
    elif fault=='query_failure':row['cninfo_query_success']=False
    elif fault=='count':report['event_count']=1
    path=tmp_path/'review.json';write(path,report)
    request={'trade_date':DATE,'as_of':DATE+'T23:59:59+08:00','stocks':[{'code':'600000.SH'}],
             'event_source_audit':{'path':str(path),'sha256':workflow.digest(path)}}
    run=tmp_path/'run';run.mkdir();events=pd.DataFrame(columns=['trade_date'])
    if fault:
        with pytest.raises(ValueError):workflow.verify_event_source_audit(request,run,{},events)
    else:
        assert workflow.verify_event_source_audit(request,run,{},events)['all_public_events_complete'] is False
