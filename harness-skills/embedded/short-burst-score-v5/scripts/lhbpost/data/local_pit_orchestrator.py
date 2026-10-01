"""Resumable exact-date TQ share acquisition, never fabricating PIT facts."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib
import json
import subprocess
import sys
import time
import shutil
import pandas as pd
_app_scripts_dir = str(Path(__file__).resolve().parents[6] / 'scripts')
if _app_scripts_dir not in sys.path: sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_data_root
try:
    from . import local_pit_inputs as pit
except ImportError:
    import local_pit_inputs as pit

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verified_ipo_calendar(out,start,end):
    """Expand the explicitly complete TQ open-date response, never weekdays."""
    path=Path(out)/'source_evidence/tq_calendar_response.json'
    proof=json.loads(path.read_text(encoding='utf-8'))
    required={'method':'TQ.get_trading_dates','market':'SH','request_start':start,'request_end':end,'count':-1,'returncode':0}
    if any(proof.get(k)!=v for k,v in required.items()):raise ValueError('ipo_calendar_request_not_verified')
    markers=[line.split('=',1)[1] for line in proof['stdout'].splitlines() if line.startswith('CALENDAR_JSON=')]
    if len(markers)!=1:raise ValueError('ipo_calendar_response_not_unique')
    from .local_supplementary import calendar_rows
    opens={r['cal_date'] for r in calendar_rows(json.loads(markers[0]),start,end)}
    frame=pd.read_csv(Path(out)/'trade_cal.csv',dtype=str)
    if frame.cal_date.duplicated().any() or set(frame.cal_date)!=opens or not frame.is_open.eq('1').all():
        raise ValueError('ipo_calendar_table_source_mismatch')
    return [{'cal_date':d.strftime('%Y%m%d'),'is_open':int(d.strftime('%Y%m%d') in opens)}
        for d in pd.date_range(start,end)]


def current_limit_with_evidence(out,code,more,start,end):
    from .local_limit_state import resolve_current_limit_state,RULES,packaged_rule_evidence
    if float(more.get('ZTPrice',float('nan')))!=0 or float(more.get('DTPrice',float('nan')))!=0:
        return resolve_current_limit_state(code,more,end,None,[])
    basic=Path(out)/'stock_basic.csv'
    frame=pd.read_csv(basic,dtype=str);selected=frame[frame.ts_code.eq(code)]
    if len(selected)!=1:raise ValueError('ipo_listing_record_not_unique')
    exchange=code.split('.')[1]
    if exchange not in RULES:raise ValueError('unsupported_ipo_rule_exchange')
    evidence=packaged_rule_evidence(exchange,Path(__file__).resolve().parents[3])
    calendar=verified_ipo_calendar(out,start,end)
    result=resolve_current_limit_state(code,more,end,selected.iloc[0].to_dict(),calendar,evidence)
    result.update(listing_source_sha256=digest(basic),calendar_source_sha256=digest(Path(out)/'source_evidence/tq_calendar_response.json'))
    return result

def cached_record(path,code,method,start,end,ledger):
    path=Path(path)
    if not path.is_file() or ledger.get(path.name)!=digest(path):return None
    try:
        record=json.loads(path.read_text(encoding='utf-8'))
        if any(record.get(k)!=v for k,v in {'stock_code':code,'method':method,
            'request_start':start,'request_end':end,'status':'RECEIVED'}.items()):return None
        stamp=datetime.fromisoformat(record['completed_at'])
        if stamp.tzinfo is None:return None
        if method=='get_gb_info_by_date':
            values=record['response']
            if not isinstance(values,list) or not values:return None
            pit.history_basic_rows(code,[],values)
            if any(not start<=str(row['Date'])<=end for row in values):return None
        elif method=='get_more_info':
            # Persist the observed source date even when it cannot serve this
            # historical request. Do not repeatedly request known mismatch.
            day=str(record['response'].get('HqDate',''))
            pit.validate_request([code],day,day)
        else:return None
        return record
    except (KeyError,TypeError,ValueError,OverflowError):return None

def acquire_pit_supplementary(adapter,start,end):
    """Resume shared range cache. Whole invocation budget defaults to 5400s.

    Every child <=60s and every record atomically written by child. Complete
    means exact coverage of all actual daily rows, not merely files present.
    Current-day more data is never expanded onto other dates.
    """
    pit.validate_request(['600000.SH'],start,end)
    today=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d')
    if end>today:raise ValueError('future_data_request')
    out=Path(adapter.out).resolve()
    cache_root=Path(getattr(adapter,'pit_cache_root',resolve_data_root()/'business_data'/'a-share-short-burst-score'/'data-cache'/'pit'))
    cache=cache_root/f'{start}-{end}';cache.mkdir(parents=True,exist_ok=True)
    run_evidence=out/'source_evidence'/'pit';run_evidence.mkdir(parents=True,exist_ok=True)
    ledger_path=cache/'cache_manifest.json'
    try:ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    except (FileNotFoundError,ValueError):ledger={}
    if not isinstance(ledger,dict):ledger={}
    by_code={};files=sorted((out/'daily').glob('*.csv'))
    for path in files:
        if not start<=path.stem<=end:continue
        frame=pd.read_csv(path,dtype={'ts_code':str,'trade_date':str})
        for row in frame.to_dict('records'):
            day=str(row['trade_date']).replace('-','')[:8]
            if day!=path.stem:raise ValueError('daily_file_date_mismatch:'+path.name)
            row['trade_date']=day;code=str(row['ts_code'])
            pit.validate_request([code],day,day)
            by_code.setdefault(code,[]).append(row)
    if not by_code:raise ValueError('no_actual_daily_bars')
    methods=['get_gb_info_by_date','get_more_info']
    needs_current={code:any(bar['trade_date']==end for bar in bars) for code,bars in by_code.items()}
    def records_for(code):
        return {method:cached_record(cache/f'{code}.{method}.json',code,method,start,end,ledger) for method in methods}
    pending=[code for code in sorted(by_code) if not all(records_for(code)[key]
        for key in (methods if needs_current[code] else ['get_gb_info_by_date']))]
    budget=float(getattr(adapter,'pit_budget_seconds',5400))
    if not 0<=budget<=7200:raise ValueError('pit_budget_out_of_bounds')
    deadline=time.monotonic()+budget;attempts=[]
    for offset in range(0,len(pending),20):
        remain=deadline-time.monotonic()
        if remain<1:break
        codes=pending[offset:offset+20]
        command=[sys.executable,'-B',str(Path(pit.__file__).resolve()),'--share-batch','--codes',*codes,
                 '--start',start,'--end',end,'--out',str(cache)]
        command.append('--include-more')
        previous={f'{code}.{method}.json':digest(cache/f'{code}.{method}.json')
                  for code in codes for method in methods if (cache/f'{code}.{method}.json').is_file()}
        try:
            child=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=min(60,remain))
            attempt={'codes':codes,'returncode':child.returncode,'stdout':child.stdout,'stderr':child.stderr}
        except subprocess.TimeoutExpired:attempt={'codes':codes,'status':'TIMEOUT'}
        attempts.append(attempt)
        # Trust only files this canonical-owned child has completed and atomically
        # persisted. Ledger hashes detect later mutation before cache reuse.
        for code in codes:
            for method in methods:
                path=cache/f'{code}.{method}.json'
                if path.is_file():
                    new_hash=digest(path)
                    if previous.get(path.name)==new_hash:continue
                    trial=dict(ledger);trial[path.name]=new_hash
                    if cached_record(path,code,method,start,end,trial):ledger[path.name]=trial[path.name]
        pit.atomic_json(ledger_path,ledger)
        pit.atomic_json(run_evidence/'batch_receipt.json',{'start':start,'end':end,'attempts':attempts})
    local_capital={};local_capital_failures={}
    missing_share_requests={code:[r['trade_date'] for r in bars] for code,bars in by_code.items()
        if records_for(code)['get_gb_info_by_date'] is None}
    if missing_share_requests:
        try:
            from .historical_capital_source import collect_local_capital
            local_capital,local_capital_failures=collect_local_capital(adapter,missing_share_requests,end)
        except Exception as exc:
            local_capital_failures={code:type(exc).__name__+':'+str(exc) for code in missing_share_requests}
    float_capital={};float_capital_failures={}
    remaining_requests={code:by_code[code] for code in missing_share_requests if code not in local_capital}
    if remaining_requests:
        try:
            from .sina_float_history import collect_float_fallback
            float_capital,float_capital_failures=collect_float_fallback(adapter,remaining_requests,end)
        except Exception as exc:
            float_capital_failures={code:type(exc).__name__+':'+str(exc) for code in remaining_requests}
    basic=[];limits=[];gaps=[];pending_codes=[];used_ledger={}
    for code,bars in sorted(by_code.items()):
        record=records_for(code)
        for method,value in record.items():
            if value:
                name=f'{code}.{method}.json';source=cache/name;target=run_evidence/name
                shutil.copy2(source,target)
                if digest(target)!=ledger[name]:raise ValueError('cache_changed_during_copy:'+name)
                used_ledger[name]=ledger[name]
        share=record.get('get_gb_info_by_date')
        using_local_capital=False
        if share is None and code in local_capital:
            share=local_capital[code];using_local_capital=True
        if not share and code not in float_capital:
            pending_codes.append(code)
            gaps.extend({'ts_code':code,'trade_date':b['trade_date'],'reason':'historical_share_source_unavailable'} for b in bars)
            continue
        if share:
            rows,missing=pit.history_basic_rows(code,bars,share['response'])
        else:
            rows,missing=float_capital[code]['rows'],float_capital[code]['missing']
        gaps.extend(missing)
        if using_local_capital:
            effective={str(r['Date']):r['capital_effective_date'] for r in share['response']}
            for row in rows:
                row.update(share_source='local_tdx_gbbq_event_history',capital_effective_date=effective[row['trade_date']],
                    capital_evidence='source_evidence/local_historical_capital.json')
        more=record.get('get_more_info')
        for row in rows:
            if row['trade_date']==end and more:
                try:
                    limit=current_limit_with_evidence(out,code,more['response'],start,end)
                    free=pit.dated_free_row(code,more['response'],end,row['close'])
                    limits.append(limit);row.update({k:v for k,v in free.items() if k not in ('ts_code','trade_date','close')})
                except (ValueError,KeyError,TypeError) as exc:gaps.append({'ts_code':code,'trade_date':end,'reason':str(exc)})
            elif row['trade_date']==end and not more:
                gaps.append({'ts_code':code,'trade_date':end,'reason':'dated_more_source_unavailable'})
        basic.extend(rows)
        if not more and needs_current[code]:pending_codes.append(code)
    target=out/'daily_basic';target.mkdir(parents=True,exist_ok=True)
    frame=pd.DataFrame(basic,columns=['ts_code','trade_date','close','turnover_rate','float_share','total_share',
        'circ_mv','total_mv','share_source','share_date','capitalization_basis','free_share','free_share_source','free_share_date',
        'capital_effective_date','capital_evidence','unobserved_capital_fields'])
    # Rebuild every requested daily file so stale rows cannot survive a newly
    # rejected cache. Empty dated files deliberately fail the raw-data audit.
    for day in sorted({bar['trade_date'] for bars in by_code.values() for bar in bars}):
        group=frame[frame['trade_date']==day]
        path=target/f'{day}.csv';tmp=path.with_suffix('.csv.tmp')
        group.to_csv(tmp,index=False,encoding='utf-8-sig');tmp.replace(path)
    target=out/'stk_limit';target.mkdir(parents=True,exist_ok=True)
    path=target/f'{end}.csv';tmp=path.with_suffix('.csv.tmp')
    pd.DataFrame(limits,columns=['ts_code','trade_date','up_limit','down_limit','source','source_date','no_limit','limit_status',
        'listing_session_no','rule_id','rule_url','rule_sha256','rule_effective_from','listing_date','no_limit_reason',
        'listing_source_sha256','calendar_source_sha256','source_up_limit','source_down_limit']).to_csv(tmp,index=False,encoding='utf-8-sig');tmp.replace(path)
    summary={'expected_bar_rows':sum(map(len,by_code.values())),'daily_basic_rows':len(basic),
        'stock_count':len(by_code),'pending_codes':sorted(set(pending_codes)),
        'missing_keys':gaps,'today_limit_rows':len(limits),'verified_ipo_no_limit_rows':sum(r.get('no_limit')==1 for r in limits),
        'source':'TQ.get_gb_info_by_date with separately evidenced local event-effective fallback',
        'local_capital_recovered_codes':sorted(local_capital),'local_capital_failures':local_capital_failures,
        'sina_float_recovered_codes':sorted(float_capital),'sina_float_failures':float_capital_failures,
        'sina_float_optional_total_capital_unobserved':sorted(float_capital),
        'historical_name_st_observed':False,'historical_limit_price_observed':False,
        'history_free_float_observed':False,'basic_complete':not gaps and not pending_codes and len(basic)==sum(map(len,by_code.values())),
        'asof_name_policy':'current_name_not_backfilled','share_date_policy':'exact_daily_key_no_ffill'}
    pit.atomic_json(run_evidence/'cache_manifest.json',{'cache_root':str(cache),'start':start,'end':end,'sha256':used_ledger})
    pit.atomic_json(run_evidence/'pit_acquisition_summary.json',summary)
    adapter.manifest.setdefault('tables',{})['daily_basic']={'rows':len(basic),'source':summary['source'],
        'exact_daily_coverage':summary['basic_complete'],'pending_stock_count':len(summary['pending_codes'])}
    if limits:adapter.manifest['tables']['stk_limit']={'rows':len(limits),'source':'TQ.get_more_info','scope':end}
    if not summary['basic_complete']:
        adapter.manifest.setdefault('failures',[]).append({'source':'daily_basic','error':'exact_daily_coverage_incomplete',
            'missing_key_count':len(gaps),'pending_stock_count':len(summary['pending_codes'])})
    return summary
