"""The user's one-year, exact-list, next-close limit-up reference.

This module does not calculate the original eight market percentiles, set a
market state, or authorize a production history model. Future-price event labels
are exported to a research directory; daily snapshot input contains aggregates
of observations already mature at the target-day close.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any
import csv
import hashlib
import io
import json
import math
import re

SCHEMA='SELECTED_ONE_YEAR_LIMIT_CLOSE_FOLLOWTHROUGH_V1'
RULE_EFFECTIVE=date(2026,7,6)
RULE_HASHES={
 ('SH',2023):'7aa2319f6dcf597be1e86b3b69d7c2ad0e6acb2a5d0cc6be48a01af602fded40',
 ('SH',2026):'fc922c433438b2636cb631eab25cca405209712acbb6aaded768c45456ff8888',
 ('SZ',2023):'7018114a6e11deb239c2a72e71e49defc6e8841b3e2c093b3bbf809282c67222',
 ('SZ',2026):'9b66f8b0db70f84a25ef1ccb4ee2351001724e408117552d75f6d8993483c586',
}

def _day(value: Any) -> date:
    text=str(value)
    if len(text)==8 and text.isdigit():text=text[:4]+'-'+text[4:6]+'-'+text[6:]
    return date.fromisoformat(text)

def _flag(value: Any,field: str) -> bool:
    if value in (True,1,'1','true','True'):return True
    if value in (False,0,'0','false','False'):return False
    raise ValueError('invalid_boolean:'+field)

def _number(value: Any,field: str,positive: bool=True) -> Decimal:
    if isinstance(value,bool):raise ValueError('invalid_number:'+field)
    try:result=Decimal(str(value))
    except (InvalidOperation,ValueError):raise ValueError('invalid_number:'+field)
    if not result.is_finite() or (positive and result<=0):raise ValueError('invalid_number:'+field)
    return result

def _json_number(value: Decimal|None):
    return None if value is None else float(value)

def load_bound_csv(path: str|Path, *, method: str, arguments: dict[str,Any], required: set[str]):
    """Validate existing source CSV identity before it enters calculations."""
    path=Path(path).resolve();meta_path=Path(str(path)+'.source.json')
    meta=json.loads(meta_path.read_text(encoding='utf-8'))
    if meta.get('status')!='OK' or meta.get('provider')!='baostock' or meta.get('method')!=method:
        raise ValueError('source_not_successful:'+path.name)
    if any(meta.get('arguments',{}).get(k)!=v for k,v in arguments.items()):
        raise ValueError('source_arguments_mismatch:'+path.name)
    if Path(meta.get('path','')).resolve()!=path:raise ValueError('source_path_mismatch:'+path.name)
    before=path.stat();raw=path.read_bytes();after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('source_changed_during_read')
    digest=hashlib.sha256(raw).hexdigest()
    if meta.get('sha256')!=digest or meta.get('bytes')!=len(raw):raise ValueError('source_hash_mismatch:'+path.name)
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')));rows=list(reader)
    if list(reader.fieldnames or [])!=meta.get('fields') or not required<=set(reader.fieldnames or []):
        raise ValueError('source_fields_mismatch:'+path.name)
    if len(rows)!=meta.get('row_count') or meta.get('validation_issues'):raise ValueError('source_row_validation:'+path.name)
    return rows,{'path':str(path),'sha256':digest,'metadata_sha256':hashlib.sha256(meta_path.read_bytes()).hexdigest(),'row_count':len(rows)}

def load_rules(folder: str|Path):
    folder=Path(folder);bound={}
    for key,digest in RULE_HASHES.items():
        suffix='.docx' if key[0]=='SH' else '.pdf';path=folder/(digest+suffix)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('official_rule_identity_mismatch')
        bound[key]={'sha256':digest,'path':str(path),'version':key[1],'exchange':key[0]}
    return bound

def _calendar(rows: list[dict[str,Any]],start: date,end: date):
    seen={}
    for row in rows:
        day=_day(row.get('calendar_date',row.get('cal_date')))
        if not start<=day<=end:continue
        if day in seen:raise ValueError('duplicate_calendar_date')
        seen[day]=_flag(row.get('is_trading_day',row.get('is_open')),'calendar')
    expected={start+timedelta(days=i) for i in range((end-start).days+1)}
    if set(seen)!=expected:raise ValueError('calendar_date_coverage_missing')
    opened=sorted(day for day,value in seen.items() if value)
    if not opened or opened[-1]!=end:raise ValueError('target_is_not_open_session')
    return opened

def _limits(row: dict[str,Any],code: str,day: date,basic: dict[str,Any],open_dates: list[date],
            rules: dict,exceptions: dict[tuple[str,date],dict]):
    """Exact documented mainboard arithmetic, retaining explicit exceptions."""
    if not (code.endswith('.SH') and code.startswith(('600','601','603','605')) or
            code.endswith('.SZ') and code.startswith(('000','001','002','003'))):
        raise ValueError('reference_only_supports_requested_mainboard_equities')
    listed=_day(basic.get('ipoDate',basic.get('list_date')))
    delisted=basic.get('outDate',basic.get('delist_date'))
    if day<listed or delisted and day>_day(delisted):raise ValueError('row_outside_listing_interval')
    version=2023 if day<RULE_EFFECTIVE else 2026
    rule=rules[(code[-2:],version)]
    if rule.get('sha256')!=RULE_HASHES[(code[-2:],version)]:raise ValueError('rule_binding_mismatch')
    explicit=exceptions.get((code,day))
    if explicit is not None:
        if not explicit.get('source_sha256') or not explicit.get('reason'):raise ValueError('exception_evidence_missing')
        if _flag(explicit.get('no_limit'),'no_limit'):return None,None,{'no_limit':True,'reason':explicit['reason'],'rule_sha256':rule['sha256']}
        if 'up_limit' in explicit and 'down_limit' in explicit:
            up=_number(explicit['up_limit'],'up_limit');down=_number(explicit['down_limit'],'down_limit')
            if up<down:raise ValueError('inverted_explicit_limit_prices')
            return up,down,{'no_limit':False,'reason':'explicit_source_limits','rule_sha256':rule['sha256']}
    if (day-listed).days<=40:
        if listed not in open_dates:raise ValueError('ipo_calendar_interval_missing')
        ordinal=sum(listed<=d<=day for d in open_dates)
        if ordinal<=5:return None,None,{'no_limit':True,'reason':'registered_ipo_first_five_sessions','rule_sha256':rule['sha256']}
    st=_flag(row['isST'],'isST');rate=Decimal('.05') if st and version==2023 else Decimal('.10')
    pre=_number(row['preclose'],'preclose');step=Decimal('.01')
    up=(pre*(1+rate)).quantize(step,rounding=ROUND_HALF_UP)
    down=(pre*(1-rate)).quantize(step,rounding=ROUND_HALF_UP)
    if up-pre<step:up=pre+step
    if pre-down<step:down=pre-step
    down=max(step,down)
    return up,down,{'no_limit':False,'reference_price':float(pre),'rate':float(rate),'is_st':st,
        'rule_sha256':rule['sha256'],'reason':'mainboard_rule_reconstruction_from_dated_source_preclose'}

def build_reference(*,codes: list[str],start: str,end: str,histories: dict[str,list[dict[str,Any]]],
                    calendar_rows: list[dict[str,Any]],basics: dict[str,dict[str,Any]],rules: dict,
                    explicit_exceptions: list[dict[str,Any]]|None=None,source_bindings: dict|None=None):
    begin=_day(start);cutoff=_day(end)
    if begin>cutoff or not codes or len(codes)!=len(set(codes)):raise ValueError('invalid_scope_or_range')
    if set(histories)!=set(codes) or set(basics)!=set(codes):raise ValueError('exact_requested_scope_mismatch')
    opened=_calendar(calendar_rows,begin,cutoff);positions={d:i for i,d in enumerate(opened)}
    exceptions={}
    for r in explicit_exceptions or []:
        key=(str(r['ts_code']),_day(r['trade_date']))
        if key in exceptions:raise ValueError('duplicate_exception')
        exceptions[key]=r
    all_events=[];summaries=[];checks=[]
    for code in codes:
        indexed={}
        for row in histories[code]:
            day=_day(row.get('date',row.get('trade_date')))
            if not begin<=day<=cutoff:continue  # physical cutoff before any label work
            expected_code=code[-2:].lower()+'.'+code[:6]
            if row.get('code',row.get('ts_code')) not in (code,expected_code):raise ValueError('history_security_mismatch')
            if day in indexed:raise ValueError('duplicate_security_date')
            if day not in positions:raise ValueError('history_on_closed_market_date')
            _flag(row['isST'],'isST');_flag(row['tradestatus'],'tradestatus')
            indexed[day]=dict(row)
        missing=set(opened)-set(indexed)
        if missing:raise ValueError('full_year_daily_status_missing:'+code+':'+','.join(map(str,sorted(missing))))
        own_events=[];unlimited=[];suspended_days=[]
        for day in opened:
            row=indexed[day]
            if not _flag(row['tradestatus'],'tradestatus'):
                suspended_days.append(str(day));continue
            close=_number(row['close'],'close');high=_number(row['high'],'high');low=_number(row['low'],'low');op=_number(row['open'],'open')
            if not low<=min(close,op)<=max(close,op)<=high:raise ValueError('invalid_daily_price_relations')
            up,down,basis=_limits(row,code,day,basics[code],opened,rules,exceptions)
            if basis['no_limit']:
                unlimited.append({'date':str(day),'basis':basis});continue
            if high>up or low<down:raise ValueError('price_limit_exception_or_source_conflict:'+code+':'+str(day))
            if close!=up:continue  # touched but unsealed never counts
            i=positions[day];nextday=opened[i+1] if i+1<len(opened) else None
            event={'ts_code':code,'limit_date':str(day),'limit_close':float(close),'limit_price':float(up),
                'limit_basis':basis,'next_market_session':None if nextday is None else str(nextday),
                'outcome':'PENDING_NEXT_MARKET_SESSION','next_close_premium':None,
                'next_close_return':None,'next_open_premium':None,'next_open_return':None,
                'next_high_premium':None,'next_high_return':None,'next_close':None,'next_open':None,'next_high':None}
            if nextday is not None:
                nxt=indexed[nextday]
                if not _flag(nxt['tradestatus'],'tradestatus'):event['outcome']='NEXT_SESSION_SUSPENDED'
                else:
                    event['outcome']='OBSERVED_NEXT_SESSION'
                    for field in ('close','open','high'):
                        val=_number(nxt[field],'next_'+field)
                        event['next_'+field]=float(val)
                        event['next_'+field+'_premium']=bool(val>close)
                        event['next_'+field+'_return']=float(val/close-1)
            own_events.append(event)
        observed=[e for e in own_events if e['outcome']=='OBSERVED_NEXT_SESSION']
        pending=sum(e['outcome']=='PENDING_NEXT_MARKET_SESSION' for e in own_events)
        suspended=sum(e['outcome']=='NEXT_SESSION_SUSPENDED' for e in own_events)
        settled=len(own_events)-pending
        n=len(observed);wins=sum(e['next_close_premium'] is True for e in observed)
        stats={'ts_code':code,'limit_up_count':len(own_events),'settled_event_count':settled,
            'observed_next_session_count':n,'next_close_premium_count':wins,
            'next_close_no_premium_count':n-wins,'next_close_flat_count':sum(e['next_close_return']==0 for e in observed),
            'next_session_suspended_count':suspended,'pending_next_session_count':pending,
            'next_close_premium_rate_observed':wins/n if n else None,
            'confirmed_close_premium_fraction_of_settled':wins/settled if settled else None,
            'mean_next_close_return':sum(e['next_close_return'] for e in observed)/n if n else None,
            'next_open_premium_count_auxiliary':sum(e['next_open_premium'] is True for e in observed),
            'next_high_premium_count_auxiliary':sum(e['next_high_premium'] is True for e in observed)}
        if stats['limit_up_count']!=n+pending+suspended:raise AssertionError('event_denominator_not_closed')
        summaries.append(stats);all_events.extend(own_events)
        checks.append({'ts_code':code,'required_sessions':len(opened),'observed_dated_rows':len(indexed),
            'suspended_source_sessions':suspended_days,'explicit_no_limit_sessions':unlimited,
            'price_limit_rule_validation':'all_trading_ohlc_within_dated_rules_or_explicit_exception'})
    summary={'schema':SCHEMA,'start_date':str(begin),'end_date':str(cutoff),'as_of_date':str(cutoff),
        'requested_codes':codes,'scope':'only_user_selected_securities_not_market_universe',
        'primary_outcome':'next_market_session_close_strictly_greater_than_limit_day_close',
        'denominator_policy':'observed_next_session_rate_excludes_suspensions_and_pending; settled_fraction_retains_suspensions; pending_never_in_settled_denominator',
        'stocks':summaries,'source_bindings':source_bindings or {},'reference_complete':True,
        'original_eight_causal_market_metrics_reconstructed':False,'production_qualified':False,
        'rule_replay_verified':False,'evidence_scope':'user_defined_descriptive_history_reference',
        'future_outcomes_beyond_cutoff_used':False}
    labels={'schema':SCHEMA+'_EVENT_LABELS','cutoff_date':str(cutoff),'scope':codes,'events':all_events,'source_checks':checks}
    return summary,labels

def write_reference(summary: dict,labels: dict,destination: str|Path):
    destination=Path(destination);research=destination/'research';inputs=destination/'snapshot-inputs'
    research.mkdir(parents=True,exist_ok=True);inputs.mkdir(parents=True,exist_ok=True)
    events=research/'limit-followthrough-event-labels.json';safe=inputs/'historical-limit-followthrough-reference.json'
    events.write_text(json.dumps(labels,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    # No per-event price columns are copied to the daily-snapshot aggregate file.
    body=dict(summary);body['research_event_artifact_sha256']=hashlib.sha256(events.read_bytes()).hexdigest()
    safe.write_text(json.dumps(body,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    return {'aggregate_path':str(safe),'aggregate_sha256':hashlib.sha256(safe.read_bytes()).hexdigest(),
        'research_labels_path':str(events),'research_labels_sha256':hashlib.sha256(events.read_bytes()).hexdigest()}


def replay_bound_reference(summary: dict) -> dict:
    """Recompute a supplied aggregate from its bound, read-only source files.

    This verifies a descriptive reference only. It neither accepts claimed
    completion flags as evidence nor uses later stock_basic names/statuses as
    historical state. The returned summary is calculated from the original CSVs.
    """
    if not isinstance(summary,dict) or summary.get('schema')!=SCHEMA:
        raise ValueError('reference_schema_mismatch')
    codes=summary.get('requested_codes')
    if not isinstance(codes,list) or not codes or len(codes)!=len(set(codes)) or any(
            not isinstance(code,str) or not re.fullmatch(r'\d{6}\.(SH|SZ)',code) for code in codes):
        raise ValueError('reference_scope_invalid')
    begin=_day(summary.get('start_date'));end=_day(summary.get('end_date'))
    if begin>end or summary.get('as_of_date')!=str(end):raise ValueError('reference_range_invalid')
    bindings=summary.get('source_bindings')
    expected={'calendar','rules'}|{code+suffix for code in codes for suffix in ('.daily','.basic')}
    if not isinstance(bindings,dict) or set(bindings)!=expected:
        raise ValueError('reference_source_binding_scope_mismatch')
    consumed=[];used_paths=set()
    def exact(value):
        try:return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
        except (ValueError,TypeError) as exc:raise ValueError('reference_noncanonical_value') from exc
    def source(label,method,required,allowed,provider_code=None):
        binding=bindings[label]
        if not isinstance(binding,dict) or set(binding)!={'path','sha256','metadata_sha256','row_count'}:
            raise ValueError('reference_source_binding_invalid:'+label)
        if type(binding['row_count']) is not int or binding['row_count']<1:
            raise ValueError('reference_source_binding_count:'+label)
        if any(not isinstance(binding.get(key),str) or not re.fullmatch(r'[0-9a-f]{64}',binding[key])
               for key in ('sha256','metadata_sha256')):
            raise ValueError('reference_source_binding_digest:'+label)
        path=Path(binding['path'])
        if not path.is_absolute():raise ValueError('reference_source_path_not_absolute:'+label)
        path=path.resolve()
        if path in used_paths:raise ValueError('reference_source_path_reused:'+label)
        used_paths.add(path)
        meta_path=Path(str(path)+'.source.json');meta_raw=meta_path.read_bytes()
        if hashlib.sha256(meta_raw).hexdigest()!=binding['metadata_sha256']:
            raise ValueError('reference_metadata_binding_mismatch:'+label)
        meta=json.loads(meta_raw)
        if not isinstance(meta,dict) or not isinstance(meta.get('arguments'),dict):
            raise ValueError('reference_source_metadata_invalid:'+label)
        args=meta['arguments'];fields=meta.get('fields')
        if not isinstance(fields,list) or len(fields)!=len(set(fields)) or not required<=set(fields) or not set(fields)<=allowed:
            raise ValueError('reference_source_fields_invalid:'+label)
        if method=='query_stock_basic':
            expected_args={'code':provider_code}
        else:
            lo=_day(args.get('start_date'));hi=_day(args.get('end_date'))
            if lo>begin or hi!=end:raise ValueError('reference_source_date_range_mismatch:'+label)
            expected_args={'start_date':str(lo),'end_date':str(hi)}
            if method=='query_history_k_data_plus':
                expected_args.update(code=provider_code,fields=','.join(fields),frequency='d',adjustflag='3')
        if exact(args)!=exact(expected_args):raise ValueError('reference_source_query_identity:'+label)
        attempts=meta.get('attempts')
        if not isinstance(attempts,list) or not attempts or attempts[-1].get('status')!='OK':
            raise ValueError('reference_source_success_attempt_missing:'+label)
        attempt=attempts[-1]
        try:
            started=datetime.fromisoformat(attempt['started_at']);ended=datetime.fromisoformat(attempt['ended_at'])
            if started.tzinfo is None or ended.tzinfo is None or ended<started:raise ValueError('invalid_interval')
            if method=='query_history_k_data_plus' and ended<datetime.fromisoformat(str(end)+'T15:00:00+08:00'):
                raise ValueError('source_before_target_close')
        except (ValueError,TypeError,KeyError) as exc:
            raise ValueError('reference_source_capture_time_invalid:'+label) from exc
        rows,verified=load_bound_csv(path,method=method,arguments=expected_args,required=required)
        if exact(verified)!=exact(binding):raise ValueError('reference_csv_binding_mismatch:'+label)
        if meta_path.read_bytes()!=meta_raw:raise ValueError('reference_metadata_changed_during_replay:'+label)
        if method!='query_stock_basic':
            seen=set();date_field='calendar_date' if method=='query_trade_dates' else 'date'
            for row in rows:
                day=_day(row.get(date_field))
                if not lo<=day<=hi or day in seen:raise ValueError('reference_source_row_dates:'+label)
                seen.add(day)
                if provider_code is not None and row.get('code')!=provider_code:
                    raise ValueError('reference_source_row_identity:'+label)
            if method=='query_trade_dates':_calendar(rows,lo,hi)
        consumed.append({'label':label,**verified,'captured_at':ended.isoformat()})
        return rows
    cal=source('calendar','query_trade_dates',{'calendar_date','is_trading_day'},
               {'calendar_date','is_trading_day'})
    rules_binding=bindings['rules'];rules={}
    if not isinstance(rules_binding,dict) or set(rules_binding)!={m+str(y) for m,y in RULE_HASHES}:
        raise ValueError('reference_rule_binding_scope_mismatch')
    for key,digest in RULE_HASHES.items():
        rule=rules_binding[key[0]+str(key[1])]
        if not isinstance(rule,dict) or set(rule)!={'sha256','path','version','exchange'} or rule['sha256']!=digest or \
                type(rule['version']) is not int or rule['version']!=key[1] or rule['exchange']!=key[0]:
            raise ValueError('reference_rule_metadata_mismatch')
        path=Path(rule['path'])
        if not path.is_absolute() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('reference_rule_file_identity_mismatch')
        rules[key]=dict(rule)
    histories={};basics={}
    required_daily={'date','code','open','high','low','close','preclose','isST','tradestatus'}
    allowed_daily=required_daily|{'volume','amount','turn','pctChg'}
    for code in codes:
        provider_code=code[-2:].lower()+'.'+code[:6]
        histories[code]=source(code+'.daily','query_history_k_data_plus',required_daily,allowed_daily,provider_code)
        basic=source(code+'.basic','query_stock_basic',{'code','ipoDate','outDate'},
                     {'code','code_name','ipoDate','outDate','type','status'},provider_code)
        if len(basic)!=1 or basic[0].get('code')!=provider_code:
            raise ValueError('reference_basic_identity_mismatch:'+code)
        listed=_day(basic[0]['ipoDate']);delisted=basic[0].get('outDate')
        if listed>end or delisted and _day(delisted)<listed:raise ValueError('reference_listing_interval_invalid:'+code)
        # Later queried metadata can confirm historical listing dates only.
        # Never import code_name/status/type as T-day or historical classifications.
        basics[code]={'ipoDate':str(listed),'outDate':str(_day(delisted)) if delisted and _day(delisted)<=end else ''}
    rebuilt,labels=build_reference(codes=codes,start=str(begin),end=str(end),histories=histories,
        calendar_rows=cal,basics=basics,rules=rules,source_bindings=bindings)
    for key,value in rebuilt.items():
        if key not in summary or exact(summary[key])!=exact(value):
            raise ValueError('reference_replay_mismatch:'+key)
    extra=set(summary)-set(rebuilt)
    if extra-{'research_event_artifact_sha256'}:raise ValueError('reference_unverified_extra_fields')
    if 'research_event_artifact_sha256' in summary:
        label_text=json.dumps(labels,ensure_ascii=False,indent=2,allow_nan=False)
        # write_reference uses the platform's text newline convention. Both
        # encodings represent the identical reconstructed labels, not new data.
        label_hashes={hashlib.sha256(text.encode('utf-8')).hexdigest()
                      for text in (label_text,label_text.replace('\n','\r\n'))}
        if summary['research_event_artifact_sha256'] not in label_hashes:
            raise ValueError('reference_research_labels_replay_mismatch')
    # A hash checked before one stock's calculation must still refer to the
    # same files when the entire multi-stock replay is accepted.
    for item in consumed:
        path=Path(item['path']);meta_path=Path(str(path)+'.source.json')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256'] or \
                hashlib.sha256(meta_path.read_bytes()).hexdigest()!=item['metadata_sha256']:
            raise ValueError('reference_source_changed_during_replay:'+item['label'])
    for rule in rules.values():
        if hashlib.sha256(Path(rule['path']).read_bytes()).hexdigest()!=rule['sha256']:
            raise ValueError('reference_rule_changed_during_replay')
    return {'schema':'SELECTED_LIMIT_REFERENCE_SOURCE_REPLAY_V1','verified':True,
        'replayed_stock_count':len(codes),'source_count':len(consumed),'source_bindings':consumed,
        'rules_verified':len(rules),'stocks_all_fields_match':True,'definitions_match':True,
        'basic_usage':'ipoDate/outDate only; later names and status never backfilled',
        'reference_scope':'user_defined_descriptive_history_reference','production_qualified':False,
        'replayed_summary':rebuilt}
