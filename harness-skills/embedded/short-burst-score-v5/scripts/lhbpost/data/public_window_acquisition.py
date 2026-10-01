"""Adaptive date partitions, complete server pagination, verified reusable windows."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import hashlib,json,time,urllib.parse,uuid,sys

_app_scripts_dir = str(Path(__file__).resolve().parents[6] / 'scripts')
if _app_scripts_dir not in sys.path: sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_data_root

CACHE_ROOT=resolve_data_root()/'business_data'/'a-share-short-burst-score'/'data-cache'/'public-windows'
SCHEMA='PUBLIC_LHB_COMPLETE_WINDOW_V1'


def sha(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _meta(payload):
    result=payload.get('result')
    if payload.get('success') is not True or not isinstance(result,dict) or not isinstance(result.get('data'),list):
        raise ValueError('public_response_not_valid_complete_table')
    count=result.get('count');pages=result.get('pages')
    if type(count) is not int or type(pages) is not int or count<0 or pages<0:raise ValueError('public_count_or_pages_invalid')
    if count and pages<1:raise ValueError('public_nonempty_without_pages')
    if not count and (pages>1 or result['data']):raise ValueError('public_empty_metadata_conflict')
    return result,count,pages


def _url(module,report,start,end,page):
    lo=datetime.strptime(start,'%Y%m%d').date().isoformat();hi=datetime.strptime(end,'%Y%m%d').date().isoformat()
    base,query=module.summary_url(lo).split('?',1);params=dict(urllib.parse.parse_qsl(query))
    params.update(reportName=report,pageNumber=str(page),pageSize='5000',sortColumns='TRADE_DATE',
        filter=f"(TRADE_DATE>='{lo}')(TRADE_DATE<='{hi}')")
    return base+'?'+urllib.parse.urlencode(params)


def validate_pages(module,report,start,end,entries,max_pages):
    if not entries:raise ValueError('empty_window_evidence')
    first,count,pages=_meta(entries[0]['payload'])
    if pages>max_pages:raise ValueError('window_still_exceeds_page_budget')
    if len(entries)!=max(1,pages):raise ValueError('window_page_count_incomplete')
    rows=[];fingerprints=set();first_size=len(first['data'])
    for page,entry in enumerate(entries,1):
        if entry.get('url')!=_url(module,report,start,end,page):raise ValueError('window_page_request_identity')
        if entry.get('payload_sha256')!=sha(entry['payload']):raise ValueError('window_page_hash_mismatch')
        result,current_count,current_pages=_meta(entry['payload'])
        if (current_count,current_pages)!=(count,pages):raise ValueError('public_page_metadata_changed')
        data=result['data'];fingerprint=sha(data)
        if data and fingerprint in fingerprints:raise ValueError('public_duplicate_page')
        fingerprints.add(fingerprint)
        if page<pages and len(data)!=first_size:raise ValueError('public_middle_page_size_changed')
        if count and not data:raise ValueError('public_empty_nonempty_page')
        for index,row in enumerate(data):
            date=str(row.get('TRADE_DATE',''))[:10].replace('-','')
            datetime.strptime(date,'%Y%m%d')
            if not start<=date<=end:raise ValueError('public_response_date_out_of_range')
            rows.append(dict(row,_source_page=page,_source_row=index,_source_window_start=start,_source_window_end=end))
    if len(rows)!=count:raise ValueError('public_response_total_count_mismatch')
    return rows


def acquire_windows(adapter,module,report,start,end,deadline,cache_root=CACHE_ROOT):
    if not report.replace('_','').isalnum():raise ValueError('invalid_report_name')
    cache=Path(cache_root);cache.mkdir(parents=True,exist_ok=True)
    hits=[];completed=[]
    def window(lo,hi):
        filename=f'{report}-{lo}-{hi}.json';path=cache/filename
        entries=None
        if path.exists():
            try:
                record=json.loads(path.read_text(encoding='utf-8'))
                if record.get('schema')!=SCHEMA or [record.get('report'),record.get('start'),record.get('end')]!=[report,lo,hi]:raise ValueError('window_cache_identity')
                if record.get('entries_sha256')!=sha(record['entries']):raise ValueError('window_cache_hash')
                fetched=datetime.fromisoformat(record['fetched_at']);cutoff=datetime.strptime(hi,'%Y%m%d').replace(hour=16,tzinfo=timezone(timedelta(hours=8)))
                if fetched.tzinfo is None or fetched<cutoff:raise ValueError('window_cache_before_close')
                rows=validate_pages(module,report,lo,hi,record['entries'],adapter.max_pages)
                for page,entry in enumerate(record['entries'],1):adapter._json(f'source_evidence/{report}-{lo}-{hi}-{page}.json',entry)
                hits.append(filename);completed.append({'start':lo,'end':hi,'rows':len(rows),'cached':True});return rows
            except (ValueError,KeyError,TypeError,OSError):pass
        def request(page):
            if time.monotonic()>deadline:raise TimeoutError('public_acquisition_budget_exhausted')
            url=_url(module,report,lo,hi,page);payload=module.fetch_json(url,retries=1)
            entry={'url':url,'payload':payload,'payload_sha256':sha(payload)}
            adapter._json(f'source_evidence/{report}-{lo}-{hi}-{page}.json',entry)
            return entry
        first=request(1);_,count,pages=_meta(first['payload'])
        if pages>adapter.max_pages:
            if lo==hi:raise ValueError('single_date_exceeds_page_limit')
            low=datetime.strptime(lo,'%Y%m%d');high=datetime.strptime(hi,'%Y%m%d')
            middle=low+timedelta(days=(high-low).days//2)
            left=window(lo,middle.strftime('%Y%m%d'))
            right=window((middle+timedelta(days=1)).strftime('%Y%m%d'),hi)
            if len(left)+len(right)!=count:raise ValueError('partition_count_does_not_match_parent')
            return left+right
        entries=[first]
        for page in range(2,pages+1):entries.append(request(page))
        rows=validate_pages(module,report,lo,hi,entries,adapter.max_pages)
        record={'schema':SCHEMA,'report':report,'start':lo,'end':hi,'fetched_at':datetime.now(timezone.utc).isoformat(),
            'entries':entries,'entries_sha256':sha(entries)}
        tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp');tmp.write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8');tmp.replace(path)
        completed.append({'start':lo,'end':hi,'rows':len(rows),'cached':False});return rows
    try:return window(start,end)
    finally:
        adapter._json(f'source_evidence/{report}-{start}-{end}-windows.json',{'report':report,'range':[start,end],
            'completed_windows':completed,'reused_windows':hits,'max_pages_per_window':adapter.max_pages,
            'source_scope':'every returned anonymous row preserved; no record deduplication used to hide repeated pages'})
