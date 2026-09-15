"""Canonical-owned continuation of the installed read-only historical provider."""
from pathlib import Path
from datetime import datetime
import hashlib,json,os,subprocess,sys,time

PROVIDER=Path(r'F:\Codex\Home\skills\a-share-market-environment\scripts\market_history_source.py')
CACHE=Path(r'F:\Codex\Home\business_data\a-share-short-burst-score\data-cache\history-provider')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_source(source,start,end):
    metadata=json.loads((Path(source)/'acquisition_manifest.json').read_text(encoding='utf-8'))
    lo=datetime.strptime(start,'%Y%m%d').strftime('%Y-%m-%d')
    hi=datetime.strptime(end,'%Y%m%d').strftime('%Y-%m-%d')
    if metadata.get('schema')!='BAOSTOCK_MARKET_HISTORY_SOURCE_V1' or metadata.get('status') not in ('ACQUIRED_PROVIDER_SCOPE','ACQUIRED_WITH_COVERAGE_GAPS'):
        raise ValueError('historical_provider_source_not_completed')
    if metadata.get('target_date')!=hi or not metadata.get('start_date') or metadata['start_date']>lo:
        raise ValueError('historical_provider_source_range_mismatch')
    return metadata

def acquire_or_reuse(adapter,start,end,resume=None):
    checksum=sha(PROVIDER);cache=Path(getattr(adapter,'history_provider_cache',CACHE));cache.mkdir(parents=True,exist_ok=True)
    pointer=cache/(start+'-'+end+'.json')
    if pointer.exists():
        try:
            prior=json.loads(pointer.read_text(encoding='utf-8'));source=Path(prior['source_root'])
            if prior['provider_sha256']==checksum and sha(source/'acquisition_manifest.json')==prior['manifest_sha256']:
                validate_source(source,start,end)
                adapter._json('source_evidence/history_provider_execution.json',dict(prior,reused=True))
                return source
        except (ValueError,KeyError,OSError):pass
    output=adapter.out/'history-provider';output.mkdir(parents=True,exist_ok=True)
    remaining=getattr(adapter,'acquisition_deadline',time.monotonic()+1860)-time.monotonic()-60
    budget=min(1800,max(0,remaining))
    if budget<1:raise TimeoutError('history_provider_remaining_budget_exhausted')
    command=[sys.executable,'-B',str(Path(__file__).resolve()),'--child',str(output),end,checksum,str(resume or '')]
    proof={'provider':str(PROVIDER),'provider_sha256':checksum,'resume_source':str(resume) if resume else None,
        'requested_start':start,'requested_end':end,'timeout_seconds':budget,'reused':False}
    with (output/'stdout.txt').open('w',encoding='utf-8') as stdout,(output/'stderr.txt').open('w',encoding='utf-8') as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,encoding='utf-8')
        try:proof['returncode']=child.wait(timeout=budget)
        except subprocess.TimeoutExpired:
            # Only the process tree created immediately above is terminated.
            if os.name=='nt':subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=15)
            else:child.kill()
            child.wait(timeout=15);proof.update(returncode=124,error='history_provider_budget_exhausted')
    source=output/'market_history_source';manifest=source/'acquisition_manifest.json'
    proof['source_root']=str(source)
    if sha(PROVIDER)!=checksum:proof['error']='historical_provider_changed_during_execution'
    if manifest.exists():
        proof['manifest_sha256']=sha(manifest)
        metadata=json.loads(manifest.read_text(encoding='utf-8'));proof['source_status']=metadata.get('status')
    adapter._json('source_evidence/history_provider_execution.json',proof)
    if proof.get('returncode')!=0 or proof.get('error') or proof.get('source_status') not in ('ACQUIRED_PROVIDER_SCOPE','ACQUIRED_WITH_COVERAGE_GAPS'):
        raise ValueError('historical_provider_continuation_incomplete:'+str(proof.get('error',proof.get('source_status'))))
    validate_source(source,start,end)
    pointer.write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
    return source

def child_main(output,end,checksum,resume):
    if os.environ.get('CODEX_STOCK_CANONICAL_EXECUTION')!='1' or os.environ.get('ONESTOCK_STOCK_CANONICAL_CHILD')!='1':
        raise ValueError('canonical_parent_required')
    if sha(PROVIDER)!=checksum:raise ValueError('historical_provider_identity_mismatch')
    sys.path.insert(0,str(PROVIDER.parent))
    import market_history_source
    result=market_history_source.acquire(output,datetime.strptime(end,'%Y%m%d').strftime('%Y-%m-%d'),resume or None)
    print(json.dumps({'status':result['status'],'source_root':str(Path(output)/'market_history_source')}))

if __name__=='__main__':
    if len(sys.argv)!=6 or sys.argv[1]!='--child':raise SystemExit('unsupported_direct_action')
    child_main(*sys.argv[2:])
