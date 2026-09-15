"""Explicit candidates through the original audited pipeline; no source fetching."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlsplit

SCHEMA='SHORT_BURST_FULL_SELECTED_REQUEST_V1'
REPORT='RPT_DAILYBILLBOARD_DETAILSNEW'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read(path, bindings):
    path=Path(path).resolve();raw=path.read_bytes()
    bindings[str(path)]=hashlib.sha256(raw).hexdigest()
    def constant(value):raise ValueError('nonfinite_json:'+value)
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('duplicate_json_key:'+key)
            result[key]=value
        return result
    return json.loads(raw.decode('utf-8-sig'),parse_constant=constant,object_pairs_hook=unique)


def _save(path,payload):
    Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def scoped_raw_audit(frames,codes,trade_date,as_of):
    """Check inputs consumed by the user-selected current-day market path only."""
    import numpy as np
    import pandas as pd
    from .data_audit import DataAudit
    from .pit_risk_guard import attach_pit_risk, merge_verified_limits
    from .features import map_industry_point_in_time
    td=pd.Timestamp(trade_date).normalize();errors=[];warnings=[];stats={}
    def attempt(name,fn):
        try:fn()
        except (ValueError,TypeError,KeyError,AssertionError) as exc:errors.append(name+':'+str(exc))
    def keyed(name,columns):
        df=frames[name]
        if not set(columns)<=set(df):raise ValueError('required_columns_missing:'+','.join(sorted(set(columns)-set(df))))
        if df.empty:raise ValueError('consumed_table_empty')
        if df.duplicated(['trade_date','ts_code']).any():raise ValueError('duplicate_security_date')
        if df[['trade_date','ts_code']].isna().any().any():raise ValueError('missing_security_date')
        if (df.trade_date>td).any():raise ValueError('future_rows_not_cut')
    def daily_check():
        keyed('daily',['trade_date','ts_code','open','high','low','close','amount','vol'])
        d=frames['daily'];v=d[['open','high','low','close','amount','vol']].apply(pd.to_numeric,errors='raise')
        if not np.isfinite(v.to_numpy()).all():raise ValueError('nonfinite_ohlcv')
        if (v[['open','high','low','close']]<=0).any().any() or (v[['amount','vol']]<0).any().any():raise ValueError('invalid_ohlcv_sign')
        if (v.high<v[['open','close','low']].max(axis=1)-1e-8).any() or (v.low>v[['open','close','high']].min(axis=1)+1e-8).any():raise ValueError('ohlc_price_relationship')
        cal=frames['calendar'];dates=set(pd.to_datetime(cal['cal_date']).dt.normalize())
        expected={day for day in dates if d.trade_date.min()<=day<=td}
        if set(d.trade_date)!=expected or td not in dates:raise ValueError('daily_missing_or_outside_verified_market_session')
        counts=d[d.ts_code.isin(codes)].groupby('ts_code').size()
        if set(counts.index)!=set(codes) or (counts<60).any():raise ValueError('selected_technical_history_below_60_sessions')
        suspensions=frames.get('verified_suspensions',set())
        for code in codes:
            observed=set(d.loc[d.ts_code.eq(code),'trade_date'])
            unexplained={(code,day) for day in expected-observed}-suspensions
            if unexplained:raise ValueError('selected_unexplained_missing_sessions:'+code+':'+str(len(unexplained)))
        stats.update(daily_rows=len(d),reference_stock_count=int(d[d.trade_date.eq(td)].ts_code.nunique()),selected_history_counts={k:int(v) for k,v in counts.items()})
    attempt('daily',daily_check)
    current=frames['daily'][frames['daily'].trade_date.eq(td)]
    selected=current[current.ts_code.isin(codes)]
    if len(selected)!=len(codes):errors.append('selected_T_daily_scope_not_exact')
    def factors_check():
        keyed('adj_factor',['trade_date','ts_code','adj_factor'])
        a=frames['adj_factor'];values=pd.to_numeric(a.adj_factor,errors='raise')
        if not np.isfinite(values).all() or (values<=0).any():raise ValueError('invalid_adjustment_factor')
        merged=frames['daily'][['trade_date','ts_code']].merge(a[['trade_date','ts_code','adj_factor']],on=['trade_date','ts_code'],how='left',validate='one_to_one')
        missing=merged.adj_factor.isna()
        stats['unmatched_factor_rows']=int(missing.sum())
        if missing.any():raise ValueError('consumed_reference_factor_missing:'+str(int(missing.sum())))
    attempt('adj_factor',factors_check)
    def basic_check():
        keyed('daily_basic',['trade_date','ts_code','turnover_rate','free_mv'])
        b=frames['daily_basic'];b=b[b.trade_date.eq(td)]
        if set(current.ts_code)-set(b.ts_code):raise ValueError('T_reference_basic_coverage_missing')
        b=b[b.ts_code.isin(current.ts_code)].copy()
        vals=b[['turnover_rate','free_mv']].apply(pd.to_numeric,errors='raise')
        for field in ('turnover_rate','free_mv'):
            observed=vals[field].notna()
            if not np.isfinite(vals.loc[observed,field].to_numpy()).all() or (vals.loc[observed,field]<0).any():
                raise ValueError('T_basic_invalid_values:'+field)
            selected_values=vals.loc[b.ts_code.isin(codes),field]
            if selected_values.isna().any() or (field=='free_mv' and (selected_values<=0).any()):
                raise ValueError('selected_T_basic_required_value_missing_or_invalid:'+field)
            stats[field+'_reference_effective_denominator']=int(observed.sum())
            stats[field+'_reference_missing_codes']=sorted(b.loc[~observed,'ts_code'].tolist())
            if (~observed).any():
                warnings.append(field+'参考字段不适用/缺失保留NaN，不进入该字段排名；有效分母='+str(int(observed.sum())))
    attempt('daily_basic_T',basic_check)
    attempt('limits_T',lambda:merge_verified_limits(current,frames['limits']))
    attempt('selected_security_state_T',lambda:attach_pit_risk(selected[['trade_date','ts_code']],frames['st_status'],frames['historical_basic'],frames['stock_basic']))
    def industry_check():
        mapped=map_industry_point_in_time(frames['daily'][['trade_date','ts_code']],frames['sw_members'])
        today=mapped[mapped.trade_date.eq(td)]
        if today.l1_code.isna().any():raise ValueError('T_reference_industry_mapping_missing')
        # Original sector daily features group by l1_name; IDs can provide the
        # same grouping key without inventing a human-readable industry name.
        stats['industry_T_mapped']=int(today.ts_code.nunique())
        stats['industry_historical_unmapped_rows']=int(mapped.l1_code.isna().sum())
        if mapped.l1_code.isna().any():warnings.append('历史行业未映射行不进入行业历史聚合，计数保留')
    attempt('industry',industry_check)
    def index_check():
        keyed('index_daily',['trade_date','ts_code','close'])
        ix=frames['index_daily'];ix=ix[ix.trade_date.eq(td)]
        if ix.empty:raise ValueError('T_index_missing')
        if not {'pct_chg'}<=set(ix):raise ValueError('T_index_observed_change_missing')
        if not np.isfinite(ix[['close','pct_chg']].apply(pd.to_numeric,errors='raise').to_numpy()).all():raise ValueError('T_index_nonfinite')
    attempt('index_T',index_check)
    def event_check():
        ev=frames['event_features']
        if ev is None:raise ValueError('event_source_missing')
        if not {'ts_code','trade_date','public_time'}<=set(ev):raise ValueError('event_identity_missing')
        if len(ev):
            published=pd.to_datetime(ev.public_time,utc=True,errors='raise')
            if published.isna().any() or (published>pd.Timestamp(as_of)).any():raise ValueError('event_after_cutoff')
            if (ev.trade_date>td).any():raise ValueError('event_trade_date_after_cutoff')
        stats['coverage_event_features']=True;stats['event_rows_through_asof']=len(ev)
    attempt('events',event_check)
    warnings.append('该审计证明当前请求实际消耗数据的结构和一致性，来源真实性仍由绑定的独立来源核验约束')
    stats['not_consumed_by_user_mode']=['historical_market_limits','historical_market_ST_and_names','historical_market_free_float','120_session_causal_market_features']
    return DataAudit(not errors,tuple(errors),tuple(warnings),stats)


def prepare_scoped_current_market(request,run,artifacts,reference,current_streaks):
    import pandas as pd
    from .data import NormalizedStore
    from .snapshot_pipeline import build_snapshot,_cut
    from .core import validate_snapshot
    td=pd.Timestamp(request['trade_date']);store=NormalizedStore(request['data_root'],strict=True)
    frames={name:_cut(getattr(store,method)(),td) for name,method in
        [('daily','daily'),('daily_basic','daily_basic'),('adj_factor','adj_factor'),('limits','limits'),
         ('st_status','st'),('historical_basic','historical_basic'),('index_daily','index_daily'),
         ('top_list','top_list'),('top_inst','top_inst'),('event_features','event_features')]}
    frames['daily']=frames['daily'][frames['daily'].ts_code.str.endswith(('.SH','.SZ'))].copy()
    # Only exact-day basics, names/status and limits feed this explicit mode.
    for name in ['daily_basic','limits','historical_basic','st_status']:
        frames[name]=frames[name][frames[name].trade_date.eq(td)].copy()
        frames[name]=frames[name][frames[name].ts_code.isin(frames['daily'].ts_code)].copy()
    frames['daily']=frames['daily'].drop(columns=['pct_chg'],errors='ignore')
    frames.update(stock_basic=store.stock_basic(),sw_members=store.sw_members(),calendar=store.trade_calendar())
    from .pit_risk_guard import _bool
    if 'is_open' not in frames['calendar']:raise ValueError('scoped_calendar_explicit_open_state_required')
    frames['calendar']=frames['calendar'][frames['calendar'].is_open.map(_bool)].copy()
    annual=_read(run/'historical_limit_followthrough_reference.json',{})
    suspensions=set()
    for stock in request['stocks']:
        binding=annual['source_bindings'][stock['code']+'.daily']
        if digest(binding['path'])!=binding['sha256']:raise ValueError('annual_suspension_source_changed')
        source=pd.read_csv(binding['path'],dtype=str)
        for row in source.to_dict('records'):
            if not _bool(row['tradestatus']):suspensions.add((stock['code'],pd.Timestamp(row['date']).normalize()))
    frames['verified_suspensions']=suspensions
    if 'l1_name' not in frames['sw_members']:
        frames['sw_members']['l1_name']=frames['sw_members']['l1_code'].astype(str)
    ev=frames['event_features']
    if ev is not None and len(ev):
        stamps=pd.to_datetime(ev.public_time,utc=True,errors='raise')
        frames['event_features']=ev[stamps<=pd.Timestamp(request['as_of'])].copy()
    codes=[s['code'] for s in request['stocks']]
    event_scope=verify_event_source_audit(request,run,artifacts,frames['event_features'])
    audit=scoped_raw_audit(frames,codes,request['trade_date'],request['as_of'])
    audit_path=run/'raw_data_audit.json';_save(audit_path,{'passed':audit.passed,'errors':list(audit.errors),'warnings':list(audit.warnings),'stats':audit.stats,'scope':'user_selected_current_market_actual_inputs'})
    artifacts['raw_data_audit']=str(audit_path)
    if not audit.passed:raise ValueError('scoped_raw_data_audit_failed:'+';'.join(audit.errors))
    proof_path=run/'billboard_source_audit.json'
    try:proof=verify_billboard_day(request['data_root'],request['trade_date'],frames['top_list'],proof_path)
    finally:
        if proof_path.is_file():artifacts['billboard_source_audit']=str(proof_path)
    frames['top_list'].attrs['verified_complete_dates']=proof['verified_complete_dates']
    themes=store.theme_members()
    snapshot=build_snapshot(trade_date=request['trade_date'],as_of=request['as_of'],
        **{k:v for k,v in frames.items() if k not in {'calendar','verified_suspensions'}},theme_members=themes,
        selected_codes=codes,market_reference=reference,current_streaks=current_streaks)
    snapshot['pipeline']='raw-postmarket-v5.0-audited'
    snapshot['raw_data_audit']={'passed':audit.passed,'warnings':list(audit.warnings),'stats':audit.stats,
        'scope':'user_selected_current_market_actual_inputs'}
    snapshot['coverage']['event_feed_scope']='official_company_announcements_for_requested_securities'
    snapshot['coverage']['all_public_events_complete']=False
    snapshot['workflow_trace'].insert(0,{'step':'原始数据审计','status':'完成','detail':'实际消耗行情/因子/T日基础/候选状态/行业/T日限价/指数/公开事件已核验；用户替换的120日市场因果层不再消费'})
    errors=validate_snapshot(snapshot)
    if errors:raise ValueError('scoped_snapshot_invalid:'+';'.join(errors))
    output=run/'prepared_snapshot.json';_save(output,snapshot);artifacts['prepared_snapshot']=str(output)
    return output


def _record_key(row):
    # Match source-normalized rows, including multiplicity, identity and amounts.
    def blank(value):return value is None or value=='' or (isinstance(value,float) and math.isnan(value))
    out={k:'' if blank(row.get(k)) else str(row[k]) for k in ('ts_code','trade_date','reason','source_event_id','source_change_type')}
    out['trade_date']=out['trade_date'][:10].replace('-','')
    for key in ('l_buy','l_sell','net_amount'):
        value=row.get(key)
        out[key]=None if blank(value) else float(value)
        if out[key] is not None and not math.isfinite(out[key]):raise ValueError('billboard_nonfinite_amount')
    return json.dumps(out,sort_keys=True,ensure_ascii=False,allow_nan=False)


def verify_billboard_day(data_root,trade_date,top_list,output=None):
    """Verify saved request identity + every source page + exact normalized T rows."""
    import pandas as pd
    from .data.public_window_acquisition import validate_pages
    from .data.local_postmarket import summary_record, _code
    root=Path(data_root).resolve();day=pd.Timestamp(trade_date).strftime('%Y%m%d')
    evidence=root/'source_evidence';bindings={};attempts=[]
    proof={'schema':'SHORT_BURST_BILLBOARD_DAY_PROOF_V1','trade_date':day,
           'status':'BLOCKED','bindings':bindings,'attempts':attempts,'errors':[]}
    try:
        options=[]
        for path in sorted(evidence.glob(REPORT+'-*-windows.json')):
            manifest=_read(path,bindings)
            if manifest.get('report')!=REPORT:raise ValueError('billboard_manifest_report_mismatch')
            bounds=manifest.get('range')
            if not isinstance(bounds,list) or len(bounds)!=2:raise ValueError('billboard_manifest_range_invalid')
            if not bounds[0]<=day<=bounds[1]:continue
            for window in manifest.get('completed_windows',[]):
                lo,hi=window.get('start'),window.get('end')
                if not isinstance(lo,str) or not isinstance(hi,str) or not bounds[0]<=lo<=hi<=bounds[1]:
                    raise ValueError('billboard_window_outside_requested_range')
                if lo<=day<=hi:options.append((lo,hi,window,manifest,path))
        if not options:raise ValueError('billboard_complete_window_for_day_missing')
        for lo,hi,window,manifest,path in options:
            attempt={'manifest':str(path),'start':lo,'end':hi};attempts.append(attempt)
            try:
                first_path=evidence/f'{REPORT}-{lo}-{hi}-1.json'
                first=_read(first_path,bindings)
                parts=urlsplit(first['url']);pairs=parse_qsl(parts.query,keep_blank_values=True);params=dict(pairs)
                if (parts.scheme,parts.netloc,parts.path)!=('https','datacenter-web.eastmoney.com','/api/data/v1/get'):
                    raise ValueError('billboard_source_endpoint_mismatch')
                expected={'sortColumns':'TRADE_DATE','sortTypes':'-1','pageSize':'5000','pageNumber':'1',
                          'reportName':REPORT,'columns':'ALL','source':'WEB','client':'WEB',
                          'filter':f"(TRADE_DATE>='{datetime.strptime(lo,'%Y%m%d').date().isoformat()}')(TRADE_DATE<='{datetime.strptime(hi,'%Y%m%d').date().isoformat()}')"}
                if len(pairs)!=len(params) or params!=expected:raise ValueError('billboard_request_identity_mismatch')
                pages=first.get('payload',{}).get('result',{}).get('pages')
                if type(pages) is not int or not 0<=pages<=1000:raise ValueError('billboard_page_count_invalid')
                entries=[first]+[_read(evidence/f'{REPORT}-{lo}-{hi}-{n}.json',bindings) for n in range(2,max(1,pages)+1)]
                module=SimpleNamespace(summary_url=lambda _date:first['url'])
                rows=validate_pages(module,REPORT,lo,hi,entries,max_pages=1000)
                if len(rows)!=window.get('rows'):raise ValueError('billboard_window_row_count_mismatch')
                today=[r for r in rows if str(r.get('TRADE_DATE',''))[:10].replace('-','')==day]
                normalized=[];excluded=[]
                for row in today:
                    try:_code(row['SECURITY_CODE'])
                    except ValueError:
                        excluded.append(str(row.get('SECURITY_CODE')));continue
                    normalized.append(summary_record(row))
                # Mirrors the existing source adapter's exact-row deduplication.
                source=Counter(set(_record_key(r) for r in normalized))
                csv=root/'top_list'/f'{day}.csv'
                csv_hash=digest(csv);bindings[str(csv)]=csv_hash
                stored=pd.read_csv(csv,dtype=str,keep_default_na=False)
                actual=Counter(_record_key(r) for r in stored.to_dict('records'))
                current=top_list[pd.to_datetime(top_list['trade_date']).dt.strftime('%Y%m%d').eq(day)]
                loaded=Counter(_record_key(r) for r in current.where(current.notna(),None).to_dict('records'))
                if actual!=source or loaded!=source:raise ValueError('billboard_csv_or_loaded_rows_do_not_match_source')
                for bound,checksum in bindings.items():
                    if digest(bound)!=checksum:raise ValueError('billboard_source_changed_during_verification')
                attempt['status']='PASS'
                proof.update(status='PASS',source_rows_for_day=len(today),normalized_equity_rows=len(normalized),
                             normalized_unique_rows=sum(source.values()),excluded_non_equity_codes=sorted(set(excluded)),
                             listed_codes=sorted({r['ts_code'] for r in normalized}),verified_complete_dates=[trade_date])
                return proof
            except (OSError,ValueError,KeyError,TypeError) as exc:
                attempt.update(status='BLOCKED',error=type(exc).__name__+':'+str(exc))
        raise ValueError('billboard_no_valid_complete_window:'+ ';'.join(x.get('error','') for x in attempts))
    except Exception as exc:
        proof['errors'].append(type(exc).__name__+':'+str(exc));raise
    finally:
        if output is not None:_save(output,proof)


def prepare_selected(request,request_path,run,artifacts):
    """Prepare and bind the original audited snapshot; never claims full completion."""
    from .core import load_config, validate_history_model
    from .data_audit import CORE_DIRS, CORE_FILES, OPTIONAL_SCHEMA
    from workbuddy_entry import prepare_cmd
    run=Path(run).resolve();copy=run/'full_selected_request.json'
    copy.write_bytes(Path(request_path).read_bytes());artifacts['full_selected_request']=str(copy)
    if _read(copy,{})!=request:raise ValueError('selected_request_changed_before_copy')
    allowed={'schema','trade_date','as_of','data_root','stocks','history_model','screenshot','market_reference','current_streaks','event_source_audit'}
    if request.get('schema')!=SCHEMA or set(request)-allowed:raise ValueError('full_selected_request_schema_invalid')
    stocks=request.get('stocks')
    if not isinstance(stocks,list) or not stocks:raise ValueError('full_selected_stocks_required')
    for s in stocks:
        if not isinstance(s,dict) or not re.fullmatch(r'\d{6}\.(SH|SZ|BJ)',str(s.get('code',''))):
            raise ValueError('full_selected_code_invalid')
        if set(s)-{'code','name','screenshot_close'}:raise ValueError('full_selected_stock_fields_invalid')
    codes=[s['code'] for s in stocks]
    if len(codes)!=len(set(codes)):raise ValueError('full_selected_duplicate_codes')
    screenshot=request.get('screenshot')
    if screenshot is not None:
        if not isinstance(screenshot,dict) or set(screenshot)!={'path','sha256'}:
            raise ValueError('selected_screenshot_binding_invalid')
        source=Path(screenshot['path']).resolve();checksum=digest(source)
        if screenshot['sha256']!=checksum:raise ValueError('selected_screenshot_hash_mismatch')
        copied=run/'request_screenshot.png';copied.write_bytes(source.read_bytes())
        artifacts['request_screenshot']=str(copied)
        if digest(copied)!=checksum:raise ValueError('selected_screenshot_changed_during_copy')
    if not all(isinstance(request.get(k),str) and request[k] for k in ('trade_date','as_of','data_root')):
        raise ValueError('full_selected_time_and_data_root_required')
    root=Path(request['data_root']).resolve()
    if not root.is_dir():raise ValueError('full_selected_data_root_missing')
    raw_paths=[p for name in (*CORE_DIRS,'index_daily') for p in sorted((root/name).glob('*.csv'))]
    raw_paths += [root/name for name in (*CORE_FILES,*OPTIONAL_SCHEMA) if (root/name).is_file()]
    raw_bindings={str(p.resolve()):digest(p) for p in raw_paths}
    raw_binding_path=run/'raw_input_bindings.json';_save(raw_binding_path,raw_bindings)
    artifacts['raw_input_bindings']=str(raw_binding_path)
    prepared=run/'prepared_snapshot.json';audit=run/'raw_data_audit.json';billboard=run/'billboard_source_audit.json'
    try:
        if request.get('market_reference') is not None:
            reference,streaks=load_user_market_reference(request,run,artifacts)
            prepared=prepare_scoped_current_market(request,run,artifacts,reference,streaks)
        else:
            prepare_cmd(argparse.Namespace(data_root=str(root),trade_date=request['trade_date'],as_of=request['as_of'],
                output=str(prepared),selected_codes=codes,audit_output=str(audit),billboard_audit_output=str(billboard)))
    finally:
        for name,path in [('prepared_snapshot',prepared),('raw_data_audit',audit),('billboard_source_audit',billboard)]:
            if path.is_file():artifacts[name]=str(path)
    snapshot=_read(prepared,{})
    actual={s['code']:s for s in snapshot['stocks']}
    if len(snapshot['stocks'])!=len(codes) or set(actual)!=set(codes):raise ValueError('selected_stock_scope_not_exact')
    for s in stocks:
        if s.get('name') and actual[s['code']]['name']!=s['name']:raise ValueError('selected_stock_name_mismatch:'+s['code'])
        if 'screenshot_close' in s:
            value=s['screenshot_close']
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
                raise ValueError('selected_screenshot_price_invalid')
            if not math.isclose(float(actual[s['code']]['close_price']),float(value),rel_tol=0,abs_tol=1e-6):
                raise ValueError('selected_screenshot_price_mismatch:'+s['code'])
    model=None;history_binding=None
    ref=request.get('history_model')
    if ref is not None:
        if not isinstance(ref,dict) or set(ref)-{'path','sha256'} or not isinstance(ref.get('path'),str):
            raise ValueError('history_model_reference_invalid')
        model_path=Path(ref['path']).resolve();checksum=digest(model_path)
        if ref.get('sha256') is not None and ref['sha256']!=checksum:raise ValueError('history_model_hash_mismatch')
        destination=run/'history_model.json';destination.write_bytes(model_path.read_bytes())
        artifacts['history_model']=str(destination)
        if digest(destination)!=checksum:raise ValueError('history_model_changed_during_copy')
        history_binding={'path':str(model_path),'sha256':checksum,'copied_path':str(destination)}
        model=_read(destination,{})
    history=validate_history_model(model,request['trade_date'],load_config())
    history_path=run/'history_model_validation.json'
    _save(history_path,{'schema':'SHORT_BURST_HISTORY_STATE_REVIEW_V1','model_supplied':model is not None,
                        'binding':history_binding,'validation':history,'production_qualified':False})
    artifacts['history_model_validation']=str(history_path)
    for path,checksum in raw_bindings.items():
        if digest(path)!=checksum:raise ValueError('raw_input_changed_during_preparation:'+path)
    if history.get('status')=='拒绝':raise ValueError('history_model_rejected:'+str(history.get('message')))
    return prepared,model


def load_user_market_reference(request,run,artifacts):
    import pandas as pd
    ref=request['market_reference']
    if not isinstance(ref,dict) or set(ref)!={'mode','input','sha256'} or ref['mode']!='yearly-limit-close-premium':
        raise ValueError('user_market_reference_mode_or_binding_invalid')
    path=Path(ref['input']).resolve();checksum=digest(path)
    if checksum!=ref['sha256']:raise ValueError('user_market_reference_hash_mismatch')
    target=run/'historical_limit_followthrough_reference.json';target.write_bytes(path.read_bytes())
    artifacts['historical_reference']=str(target)
    if digest(target)!=checksum:raise ValueError('user_market_reference_changed_during_copy')
    record=_read(target,{})
    if record.get('schema')!='SELECTED_ONE_YEAR_LIMIT_CLOSE_FOLLOWTHROUGH_V1':raise ValueError('user_market_reference_schema_invalid')
    if record.get('end_date')!=request['trade_date'] or record.get('as_of_date')!=request['trade_date']:
        raise ValueError('user_market_reference_date_mismatch')
    expected={s['code'] for s in request['stocks']}
    if set(record.get('requested_codes',[]))!=expected or len(record.get('requested_codes',[]))!=len(expected):
        raise ValueError('user_market_reference_requested_scope_mismatch')
    rows=record.get('stocks',[])
    if len(rows)!=len(expected) or {r.get('ts_code') for r in rows}!=expected:raise ValueError('user_market_reference_result_scope_mismatch')
    if record.get('reference_complete') is not True or record.get('production_qualified') is not False or record.get('rule_replay_verified') is not False or record.get('original_eight_causal_market_metrics_reconstructed') is not False:
        raise ValueError('user_market_reference_scope_false_claim')
    counts=['limit_up_count','settled_event_count','observed_next_session_count','next_close_premium_count',
            'next_close_no_premium_count','next_close_flat_count','next_session_suspended_count','pending_next_session_count']
    for row in rows:
        if any(type(row.get(k)) is not int or row[k]<0 for k in counts):raise ValueError('user_market_reference_count_invalid')
        if row['limit_up_count']!=row['settled_event_count']+row['pending_next_session_count']:raise ValueError('user_market_reference_total_identity')
        if row['observed_next_session_count']!=row['next_close_premium_count']+row['next_close_no_premium_count']:raise ValueError('user_market_reference_premium_identity')
        if row['settled_event_count']!=row['observed_next_session_count']+row['next_session_suspended_count']:raise ValueError('user_market_reference_settled_identity')
        if row['next_close_flat_count']>row['next_close_no_premium_count']:raise ValueError('user_market_reference_flat_identity')
    from .limit_followthrough_reference import replay_bound_reference
    replay=replay_bound_reference(record)
    replay_path=run/'historical_reference_replay.json';_save(replay_path,replay)
    artifacts['historical_reference_replay']=str(replay_path)
    streak_ref=request.get('current_streaks')
    if not isinstance(streak_ref,dict) or set(streak_ref)!={'path','sha256','proof'}:raise ValueError('user_market_current_streak_binding_required')
    streak_path=Path(streak_ref['path']).resolve();streak_sha=digest(streak_path)
    if streak_sha!=streak_ref['sha256']:raise ValueError('user_market_current_streak_hash_mismatch')
    streak_copy=run/'current_streaks.csv';streak_copy.write_bytes(streak_path.read_bytes())
    artifacts['current_streaks']=str(streak_copy)
    if digest(streak_copy)!=streak_sha:raise ValueError('user_market_current_streak_changed_during_copy')
    proof_ref=streak_ref['proof']
    if not isinstance(proof_ref,dict) or set(proof_ref)!={'path','sha256'}:raise ValueError('user_market_current_streak_proof_required')
    proof_path=Path(proof_ref['path']).resolve()
    if digest(proof_path)!=proof_ref['sha256']:raise ValueError('user_market_current_streak_proof_hash_mismatch')
    from .current_streaks_source import verify_current_streaks_evidence
    checked=verify_current_streaks_evidence(streak_path,proof_path)
    checked_path=run/'current_streaks_source_check.json';_save(checked_path,checked)
    artifacts['current_streaks_source_check']=str(checked_path)
    streaks=pd.read_csv(streak_copy,dtype={'ts_code':str})
    if not {'ts_code','trade_date','board_streak'}<=set(streaks):raise ValueError('user_market_current_streak_columns_missing')
    streaks['trade_date']=pd.to_datetime(streaks['trade_date'].astype(str),format='mixed').dt.normalize()
    if not streaks.trade_date.eq(pd.Timestamp(request['trade_date'])).all() or streaks.duplicated(['trade_date','ts_code']).any():raise ValueError('user_market_current_streak_identity_invalid')
    # Only the mode metadata enters the T snapshot. Historical outcome labels
    # remain physically separate, never passed through scoring feature fields.
    return {'mode':ref['mode'],'scope':'independent_historical_reference_only',
            'affects_scoring':False,'original_causal_market_reconstructed':False},streaks


def verify_event_source_audit(request,run,artifacts,events):
    import pandas as pd
    binding=request.get('event_source_audit')
    if not isinstance(binding,dict) or set(binding)!={'path','sha256'}:raise ValueError('official_announcement_audit_binding_required')
    source=Path(binding['path']).resolve()
    if digest(source)!=binding['sha256']:raise ValueError('official_announcement_audit_hash_mismatch')
    target=run/'event_source_audit.json';target.write_bytes(source.read_bytes());artifacts['event_source_audit']=str(target)
    report=_read(target,{})
    if digest(target)!=binding['sha256']:raise ValueError('official_announcement_audit_changed_during_copy')
    if report.get('schema')!='NINE_COMPANY_ANNOUNCEMENT_REVIEW_V1' or report.get('trade_date')!=request['trade_date'] or report.get('as_of')!=request['as_of']:
        raise ValueError('official_announcement_audit_date_or_schema')
    codes={s['code'] for s in request['stocks']};candidates=report.get('candidates',[])
    if len(candidates)!=len(codes) or {r.get('ts_code') for r in candidates}!=codes:raise ValueError('official_announcement_audit_candidate_scope')
    for row in candidates:
        if any(row.get(k) is not True for k in ['cninfo_query_success','eastmoney_query_success','cninfo_complete_for_query','eastmoney_complete_for_query']):
            raise ValueError('official_announcement_query_incomplete')
        for field in ['cninfo_query_date_range','eastmoney_query_notice_date_range']:
            lo,hi=str(row.get(field,'')).split('~')
            if not lo<=request['trade_date']<=hi:raise ValueError('official_announcement_query_date_not_covered')
        if row.get('all_public_events_complete') is not False:raise ValueError('official_announcement_scope_overclaimed')
        if not row.get('source_files'):raise ValueError('official_announcement_source_files_missing')
        for raw in row['source_files']:
            if digest(raw['path'])!=raw['sha256']:raise ValueError('official_announcement_source_file_hash_mismatch')
    count=0 if events is None else len(events)
    if report.get('event_count')!=count:raise ValueError('official_announcement_event_count_mismatch')
    if count:
        on_day=int(pd.to_datetime(events.trade_date).dt.normalize().eq(pd.Timestamp(request['trade_date'])).sum())
        if report.get('t_day_new_event_count')!=on_day:raise ValueError('official_announcement_T_event_count_mismatch')
    return {'official_announcement_query_verified':True,'all_public_events_complete':False}
