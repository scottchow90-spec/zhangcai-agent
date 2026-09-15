"""Translate package execution into existing Codex receipts, without semantic promotion."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
from local_business import ROOT, digest, parser, validate_run_dir

SKILL_ID='a-share-short-burst-score'

def main():
    if os.environ.get('CODEX_STOCK_CANONICAL_EXECUTION')!='1':
        print(json.dumps({'status':'BLOCKED','errors':['canonical_execution_environment_missing']}));return 2
    a=parser().parse_args()
    try:run=validate_run_dir(a.run_dir)
    except Exception as exc:
        print(json.dumps({'status':'BLOCKED','errors':[str(exc)]}));return 2
    command=[sys.executable,'-B',str(ROOT/'scripts/legacy_codex_entry.py'),'--run-dir',str(run),'--action',a.action]
    for name in ('input','data_root','trade_date','as_of','events','cutoff','start','end'):
        if getattr(a,name,None) is not None:command.extend(['--'+name.replace('_','-'),getattr(a,name)])
    env=dict(os.environ,ONESTOCK_STOCK_CANONICAL_CHILD='1',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
    errors=[];payload={};returncode=2;timed_out=False
    try:
        cp=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=7200 if a.action=='download' else 780,env=env)
        stdout,stderr,returncode=cp.stdout,cp.stderr,cp.returncode
    except subprocess.TimeoutExpired:
        stdout,stderr='', 'business_child_timeout';timed_out=True;errors.append('business_child_timeout')
    except OSError as exc:
        stdout,stderr='',type(exc).__name__+':'+str(exc);errors.append('business_child_launch_failed')
    stdout_path=run/'business_child.stdout.txt';stderr_path=run/'business_child.stderr.txt'
    stdout_path.write_text(stdout,encoding='utf-8');stderr_path.write_text(stderr,encoding='utf-8')
    try:
        payload=json.loads(stdout)
        if not isinstance(payload,dict):raise ValueError('child_result_not_object')
        if not isinstance(payload.get('artifacts'),dict):raise ValueError('child_artifacts_not_object')
        if not isinstance(payload.get('errors'),list) or not all(isinstance(x,str) for x in payload['errors']):raise ValueError('child_errors_invalid')
        if not all(isinstance(k,str) and isinstance(v,str) for k,v in payload['artifacts'].items()):raise ValueError('child_artifact_paths_invalid')
        persisted=json.loads((run/'local_result.json').read_text(encoding='utf-8'))
        if payload!=persisted:errors.append('child_result_readback_mismatch')
        if payload.get('action')!=a.action:errors.append('child_action_mismatch')
        if payload.get('full_workflow_completed') is not False:errors.append('child_scope_invalid')
        errors.extend(payload.get('errors',[]))
    except (OSError,ValueError,AttributeError):
        payload={};errors.append('child_result_invalid_or_missing')
    if returncode!=0 or payload.get('status')!='CLEAN_PASS':errors.append('child_not_clean')
    artifacts={'stdout':str(stdout_path),'stderr':str(stderr_path)}
    if (run/'local_result.json').is_file():artifacts['local_result']=str(run/'local_result.json')
    for name,value in payload.get('artifacts',{}).items():
        p=Path(value).resolve()
        if run not in p.parents or not p.is_file():errors.append('child_artifact_outside_run_or_missing:'+name)
        else:artifacts[name]=str(p)
    status='BLOCKED' if errors else 'CLEAN_PASS'
    manifest=run/'business_artifact_manifest.json';resultpath=run/'business_result.json'
    result={'schema':'STOCK_CANONICAL_BUSINESS_RESULT_V1','skill_id':SKILL_ID,'status':status,
        'execution_purpose':'SYNTHETIC_INTEGRATION_TEST' if a.action=='diagnose' else 'CONTRACT_EXECUTION_ONLY',
        'business_summary':{'action':a.action,'claim_scope':'synthetic_test' if a.action=='diagnose' else 'contract_execution','full_workflow_completed':False},
        'business_process':{'command':command,'cwd':str(ROOT),'returncode':returncode,'timed_out':timed_out},
        'artifacts':dict(artifacts,business_manifest=str(manifest)),'errors':sorted(set(errors))}
    resultpath.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    paths={str(resultpath),*artifacts.values()}
    rows=[{'name':Path(p).name,'path':p,'size':Path(p).stat().st_size,'sha256':digest(p)} for p in sorted(paths)]
    manifest.write_text(json.dumps({'schema':'STOCK_BUSINESS_ARTIFACT_MANIFEST_V1','skill_id':SKILL_ID,'status':status,'validation':{'status':status,'full_workflow_completed':False},'artifacts':rows,'errors':sorted(set(errors))},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False));return 2 if errors else 0

if __name__=='__main__':raise SystemExit(main())
