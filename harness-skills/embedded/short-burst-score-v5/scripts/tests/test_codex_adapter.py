import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
import local_business as local
import canonical_business_adapter as adapter

def args(action,**kw):
    values=dict(action=action,input=None,data_root=None,trade_date=None,as_of=None,events=None,cutoff=None,start=None,end=None)
    values.update(kw);return argparse.Namespace(**values)

def test_output_rejects_skill_directory():
    with pytest.raises(ValueError,match='inside_skill'):local.validate_run_dir(local.ROOT/'outputs')

def test_output_rejects_escape(tmp_path):
    with pytest.raises(ValueError,match='outside_run'):local.confined_output(tmp_path,'../escape')

def test_legacy_rejects_missing_environment():
    env=dict(os.environ);env.pop('CODEX_STOCK_CANONICAL_EXECUTION',None);env.pop('ONESTOCK_STOCK_CANONICAL_CHILD',None)
    r=subprocess.run([sys.executable,'-B',str(local.ROOT/'scripts/legacy_codex_entry.py')],capture_output=True,text=True,env=env)
    assert r.returncode==2 and 'canonical_stock_legacy_entry_direct_execution_blocked' in r.stdout

def test_adapter_rejects_missing_environment(monkeypatch,capsys):
    monkeypatch.delenv('CODEX_STOCK_CANONICAL_EXECUTION',raising=False)
    assert adapter.main()==2
    assert json.loads(capsys.readouterr().out)['status']=='BLOCKED'

def test_analyze_missing_input_is_not_diagnose(tmp_path):
    with pytest.raises(ValueError,match='required_arguments_missing'):local.execute(args('analyze'),tmp_path)

def test_bad_snapshot_blocks(tmp_path):
    p=tmp_path/'bad.json';p.write_text('{}',encoding='utf-8')
    with pytest.raises((ValueError,KeyError)):local.execute(args('analyze',input=str(p)),tmp_path)
    assert not (tmp_path/'analysis.json').exists()

def test_download_without_token_uses_local_and_keeps_evidence(monkeypatch,tmp_path):
    import types
    monkeypatch.delenv('TUSHARE_TOKEN',raising=False)
    class Source:
        def __init__(self,out_dir): self.out=Path(out_dir)
        def download_core(self,start,end):
            self.out.mkdir(parents=True,exist_ok=True)
            (self.out/'acquisition_manifest.json').write_text(json.dumps({'source':'local','start':start,'end':end}),encoding='utf-8')
    monkeypatch.setitem(sys.modules,'lhbpost.data.local_postmarket',types.SimpleNamespace(LocalPostMarketAdapter=Source))
    with pytest.raises(local.IncompleteAcquisition) as error:
        local.execute(args('download',start='20260910',end='20260910'),tmp_path)
    assert any(Path(p).name=='acquisition_manifest.json' for p in error.value.artifacts.values())
    readiness=json.loads((tmp_path/'raw-data'/'readiness.json').read_text(encoding='utf-8'))
    assert readiness['ready_for_scoring'] is False
    assert readiness['errors'] and 'TUSHARE_TOKEN_missing' not in str(error.value)


def test_download_rejects_future_before_source(monkeypatch,tmp_path):
    with pytest.raises(ValueError,match='date_range_invalid'):
        local.execute(args('download',start='20990101',end='20990101'),tmp_path)


def test_wrong_action_option_rejected(tmp_path):
    with pytest.raises(ValueError,match='not_applicable'):local.execute(args('diagnose',input='not-used'),tmp_path)

def test_diagnose_checks_real_child_markers(monkeypatch,tmp_path):
    calls=[]
    def run(command,**kwargs):
        calls.append((command,kwargs))
        return subprocess.CompletedProcess(command,0,'VERIFY_OK' if command[-1]=='verify' else 'ALL_TESTS_PASSED','')
    monkeypatch.setattr(local.subprocess,'run',run)
    result=local.execute(args('diagnose'),tmp_path)
    assert len(calls)==2 and set(result)=={'verify','selftest'}
    assert all(c[0][0]==sys.executable for c in calls)
    assert '--basetemp=' in calls[1][1]['env']['PYTEST_ADDOPTS']

def test_diagnose_zero_without_marker_blocks(monkeypatch,tmp_path):
    monkeypatch.setattr(local.subprocess,'run',lambda cmd,**kw:subprocess.CompletedProcess(cmd,0,'',''))
    with pytest.raises(ValueError,match='marker_missing'):local.execute(args('diagnose'),tmp_path)

def test_adapter_manifest_and_scope(monkeypatch,tmp_path,capsys):
    monkeypatch.setenv('CODEX_STOCK_CANONICAL_EXECUTION','1')
    monkeypatch.setattr(sys,'argv',['adapter','--run-dir',str(tmp_path),'--action','diagnose'])
    child={'status':'CLEAN_PASS','action':'diagnose','full_workflow_completed':False,'artifacts':{},'errors':[]}
    (tmp_path/'local_result.json').write_text(json.dumps(child),encoding='utf-8')
    monkeypatch.setattr(adapter.subprocess,'run',lambda cmd,**kw:subprocess.CompletedProcess(cmd,0,json.dumps(child),''))
    assert adapter.main()==0
    result=json.loads(capsys.readouterr().out)
    assert result['execution_purpose']=='SYNTHETIC_INTEGRATION_TEST'
    assert result['business_summary']['full_workflow_completed'] is False
    manifest=json.loads((tmp_path/'business_artifact_manifest.json').read_text(encoding='utf-8'))
    for row in manifest['artifacts']:
        assert local.digest(row['path'])==row['sha256']

@pytest.mark.parametrize('stdout',['[]',json.dumps({'artifacts':None,'errors':[]}),json.dumps({'artifacts':{},'errors':None})])
def test_adapter_malformed_child_blocks(monkeypatch,tmp_path,capsys,stdout):
    monkeypatch.setenv('CODEX_STOCK_CANONICAL_EXECUTION','1')
    monkeypatch.setattr(sys,'argv',['adapter','--run-dir',str(tmp_path),'--action','analyze','--input','absent'])
    monkeypatch.setattr(adapter.subprocess,'run',lambda cmd,**kw:subprocess.CompletedProcess(cmd,0,stdout,''))
    assert adapter.main()==2
    result=json.loads(capsys.readouterr().out)
    assert result['execution_purpose']=='CONTRACT_EXECUTION_ONLY'
    assert 'child_result_invalid_or_missing' in result['errors']


def test_source_failure_cannot_be_hidden_by_structural_audit(monkeypatch,tmp_path):
    import types
    import lhbpost.data_audit as audit
    class Source:
        def __init__(self,out_dir):self.out=Path(out_dir)
        def download_core(self,start,end):
            payload={'start':start,'end':end,'full_workflow_completed':False,'failures':[{'source':'seat','error':'undisclosed_side'}],'missing_tables':[]}
            (self.out/'acquisition_manifest.json').write_text(json.dumps(payload),encoding='utf-8')
    monkeypatch.setitem(sys.modules,'lhbpost.data.local_postmarket',types.SimpleNamespace(LocalPostMarketAdapter=Source))
    monkeypatch.setattr(audit,'audit_raw_data',lambda *a,**k:types.SimpleNamespace(errors=[],warnings=[],stats={}))
    with pytest.raises(local.IncompleteAcquisition,match='undisclosed_side'):
        local.execute(args('download',start='20260910',end='20260910'),tmp_path)
