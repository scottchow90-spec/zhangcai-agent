"""SZSE short-name change export; current 证券简称 is never a history baseline."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import hashlib,io,json,re,urllib.request,urllib.parse
import pandas as pd

SOURCE_CODE=Path(r'C:\Users\25296\AppData\Local\Programs\Python\Python313\Lib\site-packages\akshare\stock\stock_info.py')
URL='https://www.szse.cn/api/report/ShowReport?'+urllib.parse.urlencode({'SHOWTYPE':'xlsx','CATALOGID':'SSGSGMXX','TABKEY':'tab2'})


def _field(columns,before):
    marker='变更前' if before else '变更后'
    matches=[c for c in columns if marker in c and '简称' in c and '全称' not in c]
    if len(matches)!=1:raise ValueError('short_name_old_new_header_not_unambiguously_observed:'+marker)
    return matches[0]


def parse_short_name_changes(frame,*,source_sha256):
    columns=[str(c).strip() for c in frame.columns];x=frame.copy();x.columns=columns
    if len(columns)!=len(set(columns)) or not {'证券代码','变更日期'}<=set(columns):raise ValueError('name_change_schema_invalid')
    before=_field(columns,True);after=_field(columns,False)
    changes=[];seen={}
    for offset,r in enumerate(x.to_dict('records')):
        code=str(r['证券代码']).removesuffix('.0').zfill(6)
        if not re.fullmatch(r'\d{6}',code):raise ValueError('name_change_code_invalid')
        if not code.startswith(('000','001','002','003','300','301')):continue
        date=pd.to_datetime(r['变更日期'],errors='coerce')
        if pd.isna(date):raise ValueError('name_change_effective_date_invalid')
        date=date.date().isoformat()
        if pd.isna(r[before]) or pd.isna(r[after]):raise ValueError('name_change_old_or_new_missing')
        old=str(r[before]).strip();new=str(r[after]).strip()
        if not old or not new:raise ValueError('name_change_old_or_new_empty')
        key=(code,date)
        if key in seen:
            if seen[key]!=(old,new):raise ValueError('conflicting_name_changes_same_date')
            raise ValueError('duplicate_name_change_source_record')
        seen[key]=(old,new)
        changes.append({'ts_code':code+'.SZ','effective_date':date,'old_name':old,'new_name':new,
            'source_row':offset,'source_sha256':source_sha256,'old_name_field':before,'new_name_field':after})
    intervals=[]
    for code in sorted({r['ts_code'] for r in changes}):
        rows=sorted([r for r in changes if r['ts_code']==code],key=lambda r:r['effective_date'])
        for i,r in enumerate(rows):
            if i and rows[i-1]['new_name']!=r['old_name']:raise ValueError('name_change_chain_gap:'+code)
            end=(datetime.strptime(rows[i+1]['effective_date'],'%Y-%m-%d')-timedelta(days=1)).date().isoformat() if i+1<len(rows) else None
            intervals.append({**r,'name':r['new_name'],'in_date':r['effective_date'],'out_date':end,
                'name_temporality':'exchange_effective_change_history','coverage_before_first_change':'not_proven'})
    return {'observed_columns':columns,'verified_field_mapping':{'date':'变更日期','code':'证券代码','old_name':before,'new_name':after},
        'changes':changes,'intervals':intervals,'current_security_name_column_used':False}


def name_as_of(intervals,code,day):
    datetime.strptime(day,'%Y-%m-%d')
    eligible=[r for r in intervals if r['ts_code']==code and r['in_date']<=day and (r['out_date'] is None or day<=r['out_date'])]
    if len(eligible)>1:raise ValueError('overlapping_historical_name_intervals')
    return eligible[0] if eligible else None


def acquire_sz_historical_names(out_dir,*,fetch=None,timeout_seconds=20):
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    result={'schema':'SZSE_HISTORICAL_SHORT_NAME_V1','url':URL,'status':'ACQUIRING','source_code':str(SOURCE_CODE),
        'source_code_sha256':hashlib.sha256(SOURCE_CODE.read_bytes()).hexdigest(),'data_scope':'SZSE short-name changes; no SH/BJ inference',
        'publication_time_archive_verified':False}
    try:
        if fetch is None:
            request=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.szse.cn/www/market/stock/changename/index.html'})
            with urllib.request.urlopen(request,timeout=timeout_seconds) as response:raw=response.read(30_000_001)
        else:raw=fetch(URL,timeout_seconds)
        if len(raw)>30_000_000:raise ValueError('name_export_response_size_limit')
        (out/'sz-name-changes.xlsx').write_bytes(raw)
        checksum=hashlib.sha256(raw).hexdigest();result['raw_sha256']=checksum
        # Examine actual tab2 headers, never borrow the documented tab1 full-name columns.
        frame=pd.read_excel(io.BytesIO(raw),dtype=object)
        result['observed_columns']=[str(c) for c in frame.columns]
        parsed=parse_short_name_changes(frame,source_sha256=checksum)
        (out/'sz-name-intervals.json').write_text(json.dumps(parsed,ensure_ascii=False,indent=2),encoding='utf-8')
        result.update(status='ACQUIRED_DATED_SHORT_NAME_CHANGES',change_rows=len(parsed['changes']),
            covered_codes=len({r['ts_code'] for r in parsed['intervals']}),
            no_change_or_before_first_change_names_not_imputed=True)
    except Exception as exc:result.update(status='BLOCKED',error=f'{type(exc).__name__}:{exc}')
    result['fetched_at']=datetime.now(timezone.utc).isoformat()
    (out/'sz-name-source.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
