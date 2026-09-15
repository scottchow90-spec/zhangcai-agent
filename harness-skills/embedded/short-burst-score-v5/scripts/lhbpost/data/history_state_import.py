"""Import completed, hash-bound source CSVs; never opens a data-provider session."""
from pathlib import Path
from datetime import datetime
import csv,hashlib,io,json,re
import pandas as pd


def day(value):
    value=str(value)
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise ValueError('source_date_format')
    datetime.strptime(value,'%Y-%m-%d')
    return value


def symbol(value):
    if not re.fullmatch(r'(sh|sz|bj)\.\d{6}',value):raise ValueError('source_stock_code_format')
    market,code=value.split('.')
    from .local_postmarket import _code
    normalized=_code(code)
    if normalized!=code+'.'+market.upper():raise ValueError('source_market_code_mismatch')
    return normalized


def read_bound(root,relative,method,arguments,required):
    root=Path(root).resolve();path=(root/relative).resolve()
    if not path.is_relative_to(root):raise ValueError('source_path_escape')
    meta_path=Path(str(path)+'.source.json')
    meta=json.loads(meta_path.read_text(encoding='utf-8'))
    if meta.get('provider')!='baostock' or meta.get('status')!='OK' or meta.get('method')!=method:
        raise ValueError('source_not_successful_expected_query:'+relative)
    if not isinstance(meta.get('arguments'),dict) or any(meta['arguments'].get(k)!=v for k,v in arguments.items()):
        raise ValueError('source_query_argument_mismatch:'+relative)
    if Path(meta.get('path','')).resolve()!=path:raise ValueError('source_csv_identity_mismatch')
    before=path.stat();raw=path.read_bytes();after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('source_changed_during_read')
    if hashlib.sha256(raw).hexdigest()!=meta.get('sha256') or len(raw)!=meta.get('bytes'):
        raise ValueError('source_hash_or_size_mismatch:'+relative)
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')));rows=list(reader)
    if not required<=set(reader.fieldnames or []):raise ValueError('source_fields_missing:'+relative)
    if list(reader.fieldnames or [])!=meta.get('fields') or len(rows)!=meta.get('row_count'):
        raise ValueError('source_row_count_or_field_evidence_mismatch:'+relative)
    if meta.get('validation_issues'):raise ValueError('source_validation_issues:'+relative)
    return rows,{'relative':relative,'sha256':meta['sha256'],'source_json_sha256':hashlib.sha256(meta_path.read_bytes()).hexdigest(),'row_count':len(rows)}


def import_history_states(source_root,out_dir,start,end):
    """Only complete target daily cross-sections produce sparse stock_st snapshots.

    Unknown or absent rows never become non-ST. Other acquired data is retained in
    source_evidence/history_state_observations.json and explicit coverage failures.
    """
    root=Path(source_root).resolve();out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    start=day(start);end=day(end)
    if start>end:raise ValueError('history_import_range_reversed')
    acquisition=json.loads((root/'acquisition_manifest.json').read_text(encoding='utf-8'))
    if acquisition.get('schema')!='BAOSTOCK_MARKET_HISTORY_SOURCE_V1' or acquisition.get('status') not in ('ACQUIRED_PROVIDER_SCOPE','ACQUIRED_WITH_COVERAGE_GAPS'):
        raise ValueError('history_source_not_completed')
    evidence=[];failures=[];expected={}
    for path in sorted((out/'daily').glob('*.csv')):
        for row in pd.read_csv(path,dtype=str,usecols=['trade_date','ts_code']).to_dict('records'):
            date=datetime.strptime(row['trade_date'],'%Y%m%d').strftime('%Y-%m-%d')
            if start<=date<=end:
                key=(date,row['ts_code'])
                if key in expected:raise ValueError('duplicate_target_daily_key')
                expected[key]=True
    if not expected:raise ValueError('target_daily_universe_missing')
    dates=sorted({key[0] for key in expected});members={};history={};basic={}
    def failed(source,exc):failures.append({'source':source,'error':f'{type(exc).__name__}:{exc}'})
    for date in dates:
        relative=f'membership/{date}.csv'
        try:
            rows,binding=read_bound(root,relative,'query_all_stock',{'day':date},{'code','code_name','tradeStatus'})
            selected={}
            for row in rows:
                try:code=symbol(row['code'])
                except ValueError:continue
                if code in selected:raise ValueError('duplicate_daily_membership_code')
                if row['tradeStatus'] not in ('0','1') or not row['code_name'].strip():raise ValueError('unknown_membership_status_or_name')
                selected[code]=row
            members.update({(date,code):r for code,r in selected.items()});evidence.append(binding)
        except Exception as exc:failed(relative,exc)
    source_codes=sorted({code[-2:].lower()+'.'+code[:6] for _,code in expected})
    source_start=acquisition.get('start_date');source_end=acquisition.get('target_date')
    if not source_start or not source_end or not day(source_start)<=start<=end<=day(source_end):
        raise ValueError('source_range_does_not_cover_requested_range')
    for code in source_codes:
        relative=f'history/{code}.csv'
        try:
            rows,binding=read_bound(root,relative,'query_history_k_data_plus',{'code':code,'start_date':source_start,
                'end_date':source_end,'frequency':'d','adjustflag':'3'},{'date','code','isST','tradestatus','preclose','turn'})
            selected={};previous=''
            for row in rows:
                date=day(row['date'])
                if row['code']!=code or not source_start<=date<=source_end or date<=previous:raise ValueError('history_code_date_or_order_invalid')
                if row['isST'] not in ('0','1') or row['tradestatus'] not in ('0','1'):raise ValueError('unknown_historical_state')
                previous=date
                if start<=date<=end:selected[(date,symbol(code))]=row
            history.update(selected);evidence.append(binding)
        except Exception as exc:failed(relative,exc)
    try:
        rows,binding=read_bound(root,'stock_basic.csv','query_stock_basic',{}, {'code','code_name','ipoDate','outDate','type','status'})
        for row in rows:
            if row['type']!='1':continue
            try:code=symbol(row['code'])
            except ValueError:continue
            if code in basic:raise ValueError('duplicate_stock_basic')
            listed=day(row['ipoDate'])
            delisted=day(row['outDate']) if row['outDate'] else ''
            if delisted and delisted<listed:raise ValueError('invalid_listing_delisting_range')
            basic[code]=dict(row)
        evidence.append(binding)
    except Exception as exc:basic={};failed('stock_basic.csv',exc)
    observations=[];missing=[];state_observations=[]
    for date,code in sorted(expected):
        m=members.get((date,code));h=history.get((date,code));b=basic.get(code)
        if h is not None:
            state_observations.append({'trade_date':date.replace('-',''),'ts_code':code,'is_st':int(h['isST']),
                'trade_status':int(h['tradestatus']),'status_source':'baostock.query_history_k_data_plus:code='+h['code']+':date='+date})
        reasons=[]
        if m is None:reasons.append('historical_membership_missing')
        if h is None:reasons.append('historical_state_missing')
        if b is None:reasons.append('listing_metadata_missing')
        if m is not None and h is not None and m['tradeStatus']!=h['tradestatus']:reasons.append('source_trade_status_conflict')
        if b is not None and (date<b['ipoDate'] or (b['outDate'] and date>b['outDate'])):reasons.append('observation_outside_listing_dates')
        if reasons:missing.append({'trade_date':date,'ts_code':code,'reasons':reasons});continue
        observations.append({'trade_date':date.replace('-',''),'ts_code':code,'unverified_display_name':m['code_name'],
            'name_temporality':'current_or_unverified','historical_name_observed':False,
            'is_st':int(h['isST']),'trade_status':int(h['tradestatus']),'raw_preclose':h['preclose'],
            'raw_turn_percent':h['turn'],'list_date':b['ipoDate'].replace('-',''),'delist_date':b['outDate'].replace('-',''),
            'historical_status_observed':True,'name_source':'baostock.query_all_stock:day='+date,
            'status_source':'baostock.query_history_k_data_plus:code='+h['code']+':date='+date,
            'listing_source':'baostock.query_stock_basic:code='+h['code'],
            'source_root':str(root),'source_evidence_reference':'source_evidence/history_state_import.json'})
    incomplete={r['trade_date'] for r in missing};written=[]
    for date in dates:
        if date in incomplete:continue
        rows=[r for r in observations if r['trade_date']==date.replace('-','')]
        for table,cols,values in [('bak_basic',['ts_code','trade_date','unverified_display_name','name_temporality','historical_name_observed','trade_status','is_st','list_date','delist_date',
            'historical_status_observed','name_source','status_source','listing_source','source_root','source_evidence_reference'],rows)]:
            path=out/table/(date.replace('-','')+'.csv');path.parent.mkdir(parents=True,exist_ok=True)
            pd.DataFrame(values,columns=cols).to_csv(path,index=False,encoding='utf-8-sig')
        written.append(date)
    state_written=[]
    state_keys={(r['trade_date'],r['ts_code']) for r in state_observations}
    for date in dates:
        compact=date.replace('-','')
        if any((compact,code) not in state_keys for dt,code in expected if dt==date):continue
        positives=[dict(ts_code=r['ts_code'],trade_date=compact,type_name='ST') for r in state_observations if r['trade_date']==compact and r['is_st']==1]
        path=out/'stock_st'/(compact+'.csv');path.parent.mkdir(parents=True,exist_ok=True)
        pd.DataFrame(positives,columns=['ts_code','trade_date','type_name']).to_csv(path,index=False,encoding='utf-8-sig')
        state_written.append(date)
    failures.append({'source':'historical_names','error':'query_all_stock_code_name_current_or_unverified; not historical evidence'})
    summary={'schema':'VERIFIED_HISTORY_STATE_IMPORT_V1','source_root':str(root),'source_manifest_sha256':hashlib.sha256((root/'acquisition_manifest.json').read_bytes()).hexdigest(),
        'requested_range':[start,end],'expected_daily_rows':len(expected),'verified_rows':len(observations),
        'written_complete_dates':written,'incomplete_dates':sorted(incomplete),'missing_rows':missing,'source_failures':failures,
        'source_bindings':evidence,'complete':False,'historical_name_coverage_complete':False,
        'historical_state_complete':len(state_observations)==len(expected),'state_written_complete_dates':state_written,
        'source_market_complete_verified':acquisition.get('market_complete_verified') is True,
        'policy':'stock_st only contains observed isST=1; zero-ST empty snapshot emitted only after every target code has valid state for that date'}
    folder=out/'source_evidence';folder.mkdir(exist_ok=True)
    (folder/'history_state_observations.json').write_text(json.dumps(observations,ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'independent_daily_state_observations.json').write_text(json.dumps(state_observations,ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'history_state_import.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    return summary
