"""Codex transport for the original package's audited business functions."""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
ACTIONS = ('diagnose','analyze','prepare-analyze','research','download','inspect-inputs')

class IncompleteAcquisition(ValueError):
    def __init__(self, errors, artifacts):
        super().__init__('local_input_incomplete:'+';'.join(errors))
        self.artifacts=artifacts

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_run_dir(value):
    path = Path(value).resolve()
    protected = Path(r'F:\Codex\Home\skills').resolve()
    if path == ROOT or ROOT in path.parents or path == protected or protected in path.parents:
        raise ValueError('output_inside_skill_directory_forbidden')
    path.mkdir(parents=True, exist_ok=True)
    return path

def confined_output(run, value):
    p = Path(value)
    p = (p if p.is_absolute() else run / p).resolve()
    if p == run or run not in p.parents:
        raise ValueError('output_outside_run_dir_forbidden')
    return p

def require(a, *names):
    missing = [n for n in names if not getattr(a,n,None)]
    if missing:
        raise ValueError('required_arguments_missing:' + ','.join('--'+n.replace('_','-') for n in missing))

def parser():
    p=argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument('--run-dir',required=True)
    p.add_argument('--action',required=True,choices=ACTIONS)
    for name in ('input','data-root','trade-date','as-of','events','cutoff','start','end'):
        p.add_argument('--'+name)
    return p

def execute(a, run, artifacts=None):
    allowed = {'diagnose':set(), 'analyze':{'input'}, 'prepare-analyze':{'data_root','trade_date','as_of'}, 'research':{'events','cutoff'}, 'download':{'data_root','start','end'}, 'inspect-inputs':{'data_root','start','end'}}
    for name in ('input','data_root','trade_date','as_of','events','cutoff','start','end'):
        if getattr(a,name,None) is not None and name not in allowed[a.action]:
            raise ValueError('argument_not_applicable_to_action:'+name)
    if artifacts is None:artifacts = {}
    if a.action=='inspect-inputs':
        require(a,'data_root','start','end')
        import pandas as pd
        from lhbpost.data.local_pit_inputs import capture_probe
        src=Path(a.data_root).resolve()
        codes=set()
        for p in (src/'top_list').glob('*.csv'):
            codes.update(pd.read_csv(p,dtype={'ts_code':str}).ts_code)
        chosen=[]
        for market in ('SH','SZ','BJ'):
            found=sorted(c for c in codes if c.endswith('.'+market))
            if found:chosen.append(found[0])
        if not chosen:raise ValueError('no_actual_candidate_for_input_inspection')
        destination=run/'input-probe'
        capture_probe(chosen,a.start,a.end,destination,timeout=30)
        artifacts={p.stem:str(p.resolve()) for p in destination.glob('*.json')}
        if not artifacts:raise ValueError('input_probe_evidence_missing')
        return artifacts
    if a.action == 'diagnose':
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
        scratch=run/'tmp';scratch.mkdir(exist_ok=True)
        env.update(TEMP=str(scratch),TMP=str(scratch),CODEX_SHORT_BURST_TEST_ROOT=str(run/'test-work'),PYTEST_ADDOPTS='-p no:cacheprovider --basetemp="'+str(run/'pytest-temp')+'"')
        for action in ('verify','selftest'):
            cp=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/workbuddy_entry.py'),action],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=360,env=env)
            log=run/(action+'.txt');log.write_text(cp.stdout+'\n'+cp.stderr,encoding='utf-8');artifacts[action]=str(log)
            if cp.returncode != 0:
                raise ValueError(action+'_failed:see '+str(log))
            required_marker = 'VERIFY_OK' if action=='verify' else 'ALL_TESTS_PASSED'
            if required_marker not in cp.stdout:
                raise ValueError(action+'_completion_marker_missing')
        return artifacts
    if a.action in ('analyze','prepare-analyze'):
        from lhbpost.core import analyze_snapshot, load_config, load_json
        model=None
        if a.action=='prepare-analyze':
            require(a,'data_root','trade_date','as_of')
            from workbuddy_entry import prepare_cmd
            snapshot=run/'prepared_snapshot.json'
            prepare_cmd(argparse.Namespace(data_root=a.data_root,trade_date=a.trade_date,as_of=a.as_of,output=str(snapshot)))
            artifacts['snapshot']=str(snapshot)
        else:
            require(a,'input');snapshot=Path(a.input).resolve()
            if not snapshot.is_file():raise ValueError('snapshot_input_missing')
            requested=load_json(snapshot)
            if requested.get('schema')=='SHORT_BURST_FULL_SELECTED_REQUEST_V1':
                from lhbpost.selected_workflow import prepare_selected
                snapshot,model=prepare_selected(requested,snapshot,run,artifacts)
            elif requested.get('schema')=='SHORT_BURST_SELECTED_REQUEST_V1':
                from lhbpost.selected_scoring import build_selected_snapshot
                request_copy=run/'selected_request.json';request_copy.write_bytes(snapshot.read_bytes())
                artifacts['selected_request']=str(request_copy)
                selected=build_selected_snapshot(requested,run)
                snapshot=run/'selected_snapshot.json'
                snapshot.write_text(json.dumps(selected,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
                artifacts['selected_snapshot']=str(snapshot)
                artifacts['selected_source_bindings']=str(run/'selected_source_bindings.json')
        before=digest(snapshot)
        payload=analyze_snapshot(load_json(snapshot),load_config(),model)
        if 'selected_request' in artifacts or 'full_selected_request' in artifacts:
            wanted={s['code'] for s in requested['stocks']}
            returned={s['code'] for s in payload['results']}
            if returned!=wanted or len(payload['results'])!=len(wanted):raise ValueError('selected_stock_scope_not_exact')
        if before!=digest(snapshot):raise ValueError('snapshot_changed_during_analysis')
        result=run/'analysis.json';result.write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        artifacts['analysis']=str(result)
        from workbuddy_entry import render_md
        report=run/'analysis.md';report.write_text(render_md(payload)+'\n',encoding='utf-8');artifacts['report']=str(report)
        binding=run/'input_binding.json';binding.write_text(json.dumps({'path':str(snapshot),'sha256':before},ensure_ascii=False)+'\n',encoding='utf-8');artifacts['input_binding']=str(binding)
    elif a.action=='research':
        require(a,'events','cutoff')
        from lhbpost.research import build_model
        events=Path(a.events).resolve()
        if not events.is_file():raise ValueError('research_events_missing')
        before=digest(events);output=run/'research_model.json'
        build_model(str(events),a.cutoff,str(output))
        if before!=digest(events):raise ValueError('research_input_changed_during_execution')
        artifacts['research_model']=str(output)
        binding=run/'input_binding.json';binding.write_text(json.dumps({'path':str(events),'sha256':before},ensure_ascii=False)+'\n',encoding='utf-8');artifacts['input_binding']=str(binding)
    elif a.action=='download':
        destination=confined_output(run,a.data_root or 'raw-data')
        today=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d')
        start=a.start or today;end=a.end or today
        try:
            for value in (start,end):
                if len(value)!=8 or not value.isdigit():raise ValueError()
                datetime.strptime(value,'%Y%m%d')
            if start>end or end>today:raise ValueError()
        except ValueError:raise ValueError('date_range_invalid') from None
        from lhbpost.data.local_postmarket import LocalPostMarketAdapter
        from lhbpost.data_audit import audit_raw_data
        destination.mkdir(parents=True,exist_ok=True)
        acquisition_errors=[]
        try:
            LocalPostMarketAdapter(out_dir=str(destination)).download_core(start=start,end=end)
        except Exception as exc:
            acquisition_errors.append(type(exc).__name__+':'+str(exc))
        audit=audit_raw_data(destination,require_end=end)
        errors=acquisition_errors+list(audit.errors)
        manifest=destination/'acquisition_manifest.json'
        if not manifest.is_file():errors.append('acquisition_manifest_missing')
        else:
            try:
                acquired=json.loads(manifest.read_text(encoding='utf-8'))
                if acquired.get('start')!=start or acquired.get('end')!=end:
                    errors.append('acquisition_date_binding_mismatch')
                for failure in acquired.get('failures',[]):
                    errors.append('source_failure:'+str(failure))
                for missing in acquired.get('missing_tables',[]):
                    errors.append('source_missing:'+str(missing))
                if acquired.get('full_workflow_completed') is not False:
                    errors.append('acquisition_scope_invalid')
            except (OSError,ValueError,AttributeError,TypeError):errors.append('acquisition_manifest_invalid')
        readiness={'schema':'SHORT_BURST_LIVE_READINESS_V1','ready_for_scoring':not errors,
            'full_workflow_completed':False,'requested_start':start,'requested_end':end,
            'errors':errors,'warnings':list(audit.warnings),'stats':audit.stats,
            'scope':'actual_acquisition_and_raw_input_audit_only'}
        (destination/'readiness.json').write_text(json.dumps(readiness,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        for i,p in enumerate(sorted(destination.rglob('*'))):
            if p.is_file():artifacts['download_'+str(i)]=str(p.resolve())
        if errors:raise IncompleteAcquisition(errors,artifacts)
    return artifacts

def main():
    if os.environ.get('CODEX_STOCK_CANONICAL_EXECUTION')!='1' or os.environ.get('ONESTOCK_STOCK_CANONICAL_CHILD')!='1':
        print(json.dumps({'status':'BLOCKED','errors':['canonical_stock_legacy_entry_direct_execution_blocked']}));return 2
    a=parser().parse_args()
    try:run=validate_run_dir(a.run_dir)
    except Exception as exc:
        print(json.dumps({'status':'BLOCKED','errors':[str(exc)]}));return 2
    captured=io.StringIO();errors=[];artifacts={}
    try:
        with contextlib.redirect_stdout(captured),contextlib.redirect_stderr(captured):artifacts=execute(a,run,artifacts)
    except Exception as exc:
        message=str(exc)
        token=os.environ.get('TUSHARE_TOKEN')
        if token:message=message.replace(token,'[REDACTED]')
        if isinstance(exc,IncompleteAcquisition):artifacts.update(exc.artifacts)
        errors.append(type(exc).__name__+':'+message)
    log_text=captured.getvalue()
    token=os.environ.get('TUSHARE_TOKEN')
    if token:log_text=log_text.replace(token,'[REDACTED]')
    log=run/'local_execution.txt';log.write_text(log_text,encoding='utf-8');artifacts['execution_log']=str(log)
    payload={'schema':'SHORT_BURST_LOCAL_RESULT_V1','status':'BLOCKED' if errors else 'CLEAN_PASS','action':a.action,'full_workflow_completed':False,'claim_scope':'synthetic_test' if a.action=='diagnose' else 'contract_execution','artifacts':artifacts,'errors':errors}
    (run/'local_result.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False));return 2 if errors else 0

if __name__=='__main__':raise SystemExit(main())
