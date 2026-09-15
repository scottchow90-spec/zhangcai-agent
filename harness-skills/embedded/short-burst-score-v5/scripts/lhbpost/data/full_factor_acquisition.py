"""Whole-universe, bounded and resumable acquisition of original HFQ evidence."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
import hashlib,json,re,time,uuid
import pandas as pd

CACHE_ROOT=Path(r'F:\Codex\Home\business_data\a-share-short-burst-score\data-cache\hfq')
SCHEMA='SINA_HFQ_RAW_RESPONSE_V1'
TZ=timezone(timedelta(hours=8))


def digest(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()


def validate_record(record,code,end):
    if record.get('schema')!=SCHEMA or record.get('ts_code')!=code:raise ValueError('hfq_cache_identity')
    digits,market=code.split('.');symbol=market.lower()+digits
    expected=f'https://finance.sina.com.cn/realstock/company/{symbol}/hfq.js'
    if record.get('source_url')!=expected:raise ValueError('hfq_cache_source')
    raw=record['raw_text']
    if digest(raw)!=record.get('raw_sha256'):raise ValueError('hfq_cache_hash')
    if not re.search(r'\bvar\s+'+re.escape(symbol)+r'hfq\s*=',raw):raise ValueError('hfq_response_symbol_mismatch')
    fetched=datetime.fromisoformat(record['fetched_at'])
    cutoff=datetime.strptime(end,'%Y%m%d').replace(tzinfo=TZ,hour=16)
    if fetched.tzinfo is None or fetched<cutoff:raise ValueError('hfq_cache_predates_requested_close')
    from .local_supplementary import parse_hfq
    return parse_hfq(raw)


def save_record(path,record):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    tmp.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp.replace(path)


def fetch_record(code,end,fetch,cache_root=CACHE_ROOT,evidence_dir=None):
    path=Path(cache_root)/(code.replace('.','_')+'.json')
    if path.exists():
        try:
            record=json.loads(path.read_text(encoding='utf-8'));factors=validate_record(record,code,end)
            return record,factors,True
        except (ValueError,KeyError,OSError,TypeError):pass
    digits,market=code.split('.');url=f'https://finance.sina.com.cn/realstock/company/{market.lower()}{digits}/hfq.js'
    raw=fetch(url,8).decode('utf-8-sig')
    record={'schema':SCHEMA,'ts_code':code,'source_url':url,'fetched_at':datetime.now(TZ).isoformat(),
        'raw_text':raw,'raw_sha256':digest(raw)}
    if evidence_dir is not None:
        save_record(Path(evidence_dir)/(code.replace('.','_')+'.response.json'),record)
    factors=validate_record(record,code,end)
    save_record(path,record)
    return record,factors,False


def collect_full_factors(adapter,end,*,budget_seconds=240,workers=4,cache_root=CACHE_ROOT,fetch=None):
    from .local_supplementary import _fetch,expand_hfq
    fetch=fetch or _fetch
    frames=[pd.read_csv(p,dtype={'ts_code':str,'trade_date':str},usecols=['ts_code','trade_date'])
        for p in sorted((adapter.out/'daily').glob('*.csv'))]
    if not frames:raise ValueError('full_factor_universe_daily_missing')
    bars=pd.concat(frames,ignore_index=True)
    grouped={code:sorted(set(group.trade_date)) for code,group in bars.groupby('ts_code')}
    codes=sorted(grouped)
    if not codes:raise ValueError('full_factor_universe_empty')
    start=time.monotonic();deadline=start+float(budget_seconds)
    succeeded=[];failed={};pending=set(codes);rows=[];hits=0;fetched=0;fallbacks=[]
    evidence=adapter.out/'source_evidence/hfq';evidence.mkdir(parents=True,exist_ok=True)
    def one(code):
        record,factors,hit=fetch_record(code,end,fetch,cache_root,evidence)
        expanded=expand_hfq(code,grouped[code],factors)
        # Bind every emitted row to a verified original response in the run itself.
        save_record(evidence/(code.replace('.','_')+'.json'),record)
        return expanded,hit
    iterator=iter(codes)
    with ThreadPoolExecutor(max_workers=max(1,min(int(workers),4))) as executor:
        running={}
        def fill():
            while len(running)<max(1,min(int(workers),4)) and time.monotonic()<deadline:
                try:code=next(iterator)
                except StopIteration:break
                running[executor.submit(one,code)]=code
        fill()
        while running:
            done,_=wait(running,return_when=FIRST_COMPLETED)
            for future in done:
                code=running.pop(future);pending.discard(code)
                try:
                    expanded,hit=future.result();rows.extend(expanded);succeeded.append(code)
                    hits+=int(hit);fetched+=int(not hit)
                except Exception as exc:failed[code]=f'{type(exc).__name__}:{exc}'
            fill()
    if '689009.SH' in failed:
        primary_error=failed['689009.SH']
        try:
            from .cdr_factor_source import collect_cdr_factors
            cdr_rows,_=collect_cdr_factors(adapter,grouped['689009.SH'],end)
            rows.extend(cdr_rows);succeeded.append('689009.SH');del failed['689009.SH']
            fallbacks.append({'ts_code':'689009.SH','primary_error':primary_error,
                'source':'local_tdx_corporate_actions','rows':len(cdr_rows),
                'evidence':'source_evidence/cdr_689009_factor_source.json'})
        except Exception as exc:
            failed['689009.SH']=primary_error+'; local_cdr_fallback:'+type(exc).__name__+':'+str(exc)
    adapter._save('adj_factor',rows)
    result={'universe_symbols':len(codes),'completed_symbols':len(succeeded),'failed_symbols':failed,
        'pending_symbols':sorted(pending),'cache_hits':hits,'fresh_responses':fetched,
        'complete':len(succeeded)==len(codes),'requested_bar_rows':len(bars),'produced_factor_rows':len(rows),
        'verified_source_fallbacks':fallbacks,
        'full_universe_no_candidate_cap':True,'budget_seconds':budget_seconds,'elapsed_seconds':round(time.monotonic()-start,3),
        'cache_root':str(cache_root),'resume_policy':'rerun same date range; revalidate cached response code/hash/close-time then fetch remaining',
        'multiplier_policy':'back-adjustment multiplier from Sina or explicitly evidenced local CDR corporate actions; no future-effective action',
        'factor_source_point_in_time_revision_archive_verified':False}
    adapter.manifest['adjustment_coverage']=result
    adapter._json('source_evidence/full_factor_checkpoint.json',result)
    if not result['complete']:
        adapter.manifest['failures'].append({'source':'adj_factor_coverage','error':'full_universe_incomplete',
            'failed_count':len(failed),'pending_count':len(pending),'checkpoint':'source_evidence/full_factor_checkpoint.json'})
    return result
