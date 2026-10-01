"""Bounded read-only supplements; every missing input remains explicit."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
import importlib.util
import io,json,math,re,subprocess,sys,time,urllib.request
import pandas as pd

_app_scripts_dir = str(Path(__file__).resolve().parents[6] / 'scripts')
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_app_root, resolve_tdx_root

SW_URL='https://www.swsresearch.com/swindex/pdf/SwClass2021/StockClassifyUse_stock.xls'
APP_ROOT=resolve_app_root()
TDX_ROOT=resolve_tdx_root()
TDX_HUB=APP_ROOT/'harness-skills'/'tdx-local-hub'/'scripts'/'tdx_hub.py'
DBF=TDX_ROOT/'T0002'/'hq_cache'/'base.dbf'
LISTING_READER=APP_ROOT/'harness-skills'/'stock-unified'/'scripts'/'installed_formula_market_scan.py'


def _date(value):
    text=str(value).strip()[:10].replace('-','')
    if not re.fullmatch(r'\d{8}',text):raise ValueError('invalid_date:'+text)
    datetime.strptime(text,'%Y%m%d')
    return text


def calendar_rows(values,start,end):
    if not isinstance(values,list) or not values:raise ValueError('empty_tq_calendar')
    dates=[_date(v) for v in values]
    if len(set(dates))!=len(dates):raise ValueError('duplicate_calendar_date')
    if any(d<start or d>end for d in dates):raise ValueError('calendar_date_out_of_range')
    return [{'exchange':'SSE','cal_date':d,'is_open':1} for d in sorted(dates)]


def industry_intervals(frame,end):
    rename={'股票代码':'code','计入日期':'start_date','行业代码':'industry_code','更新日期':'update_date'}
    x=frame.rename(columns=rename).copy()
    if not {'code','start_date','industry_code'}<=set(x):raise ValueError('industry_schema_missing')
    if x[['code','start_date','industry_code']].isna().any().any():raise ValueError('industry_required_value_missing')
    from lhbpost.data.local_postmarket import _code
    rows=[]
    for row in x.to_dict('records'):
        code=str(row['code']).removesuffix('.0').zfill(6)
        try:ts=_code(code)
        except ValueError:continue
        sector=str(row['industry_code']).removesuffix('.0').zfill(6)
        if not re.fullmatch(r'\d{6}',sector):raise ValueError('invalid_industry_code')
        day=_date(row['start_date'])
        if day>end:continue
        rows.append({'ts_code':ts,'industry_code':sector,'l1_code':sector[:2]+'0000','in_date':day})
    result=[]
    for code in sorted({r['ts_code'] for r in rows}):
        changes=sorted({(r['in_date'],r['industry_code'],r['l1_code']) for r in rows if r['ts_code']==code})
        if len({r[0] for r in changes})!=len(changes):raise ValueError('conflicting_industry_same_effective_date:'+code)
        for i,(day,sector,l1) in enumerate(changes):
            out=(datetime.strptime(changes[i+1][0],'%Y%m%d')-timedelta(days=1)).strftime('%Y%m%d') if i+1<len(changes) else ''
            result.append({'ts_code':code,'l1_code':l1,'industry_code':sector,'in_date':day,'out_date':out})
    if not result:raise ValueError('no_industry_history')
    return result


def parse_hfq(text):
    brace=text.find('{')
    if brace<0:raise ValueError('hfq_json_missing')
    payload,_=json.JSONDecoder().raw_decode(text[brace:]);data=payload.get('data')
    if not isinstance(data,list) or not data:raise ValueError('hfq_empty')
    values={}
    for item in data:
        date=_date(item['d']);factor=float(item['f'])
        if not math.isfinite(factor) or factor<=0:raise ValueError('invalid_hfq_multiplier')
        if date in values and values[date]!=factor:raise ValueError('conflicting_hfq_same_date')
        values[date]=factor
    return sorted(values.items())


def expand_hfq(code,dates,factors):
    rows=[];i=0;current=None
    for day in sorted(set(dates)):
        while i<len(factors) and factors[i][0]<=day:
            current=factors[i][1];i+=1
        if current is None:raise ValueError('factor_history_does_not_cover_bar:'+day)
        rows.append({'ts_code':code,'trade_date':day,'adj_factor':current})
    return rows


def _fetch(url,timeout=12):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://finance.sina.com.cn/'})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        data=response.read(20_000_001)
    if len(data)>20_000_000:raise ValueError('response_size_limit')
    return data


def tnf_names(raw,market):
    if len(raw)<50 or (len(raw)-50)%360:raise ValueError('invalid_tnf_length')
    result={}
    from lhbpost.data.local_postmarket import _code
    for offset in range(50,len(raw),360):
        record=raw[offset:offset+360]
        try:code=_code(record[:6].decode('ascii'))
        except (ValueError,UnicodeError):continue
        if not code.endswith('.'+market):continue
        end=record.find(b'\0',31,96)
        if end<0:raise ValueError('tnf_name_terminator_missing')
        name=record[31:end].decode('gbk').strip()
        if not name or code in result:raise ValueError('tnf_name_missing_or_duplicate')
        result[code]=name
    return result


def _calendar_child(start,end):
    spec=importlib.util.spec_from_file_location('_tq_data_bridge',TDX_HUB)
    hub=importlib.util.module_from_spec(spec);spec.loader.exec_module(hub)
    with hub.TQLock(timeout_seconds=5):
        tq,_=hub.load_tq()
        dates=tq.get_trading_dates(market='SH',start_time=start,end_time=end,count=-1)
    print('CALENDAR_JSON='+json.dumps(dates,ensure_ascii=False))


def acquire_supplementary(adapter,start,end):
    out=adapter.out;manifest=adapter.manifest
    def failure(source,exc):manifest['failures'].append({'source':source,'error':f'{type(exc).__name__}:{exc}'})
    try:
        result=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--calendar-child',start,end],
            capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
        adapter._json('source_evidence/tq_calendar_response.json',{'method':'TQ.get_trading_dates','market':'SH',
            'request_start':start,'request_end':end,'count':-1,
            'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        lines=[l.split('=',1)[1] for l in result.stdout.splitlines() if l.startswith('CALENDAR_JSON=')]
        if result.returncode or len(lines)!=1:raise ValueError('tq_calendar_child_failed')
        rows=calendar_rows(json.loads(lines[0]),start,end)
        pd.DataFrame(rows).to_csv(out/'trade_cal.csv',index=False,encoding='utf-8-sig')
        manifest['tables']['trade_cal.csv']={'rows':len(rows),'source':'TQ.get_trading_dates(SH)','date_scope':[start,end]}
    except Exception as exc:failure('trade_cal.csv',exc)
    try:
        raw=_fetch(SW_URL,20);p=out/'source_evidence/StockClassifyUse_stock.xls';p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(raw)
        rows=industry_intervals(pd.read_excel(io.BytesIO(raw)),end)
        pd.DataFrame(rows).to_csv(out/'sw_members.csv',index=False,encoding='utf-8-sig')
        manifest['tables']['sw_members.csv']={'rows':len(rows),'source':SW_URL,'interval_policy':'effective start inclusive; next effective start minus one calendar day inclusive',
            'point_in_time_revision_archive_verified':False}
    except Exception as exc:failure('sw_members.csv',exc)
    # Read only the DBF descriptor; no invented stock_basic listing dates.
    try:
        with DBF.open('rb') as fh:
            header=fh.read(32);hlen=int.from_bytes(header[8:10],'little');descriptors=fh.read(max(0,hlen-32))
        fields=[]
        for i in range(0,len(descriptors)-31,32):
            b=descriptors[i:i+32]
            if b[0]==13:break
            fields.append({'name':b[:11].split(b'\0')[0].decode('ascii',errors='replace'),'type':chr(b[11]),'length':b[16]})
        adapter._json('source_evidence/base_dbf_fields.json',{'source':str(DBF),'fields':fields,
            'policy':'descriptor-only; no stock_basic emitted without verified listing date semantics'})
    except Exception as exc:failure('stock_basic_descriptor',exc)
    try:
        today=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d')
        if end!=today:raise ValueError('current_names_require_current_asof; historical_name_snapshots_not_available')
        symbols=set()
        for p in (out/'daily').glob('*.csv'):symbols.update(pd.read_csv(p,dtype={'ts_code':str}).ts_code)
        spec=importlib.util.spec_from_file_location('_listing_reader',LISTING_READER)
        reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
        info=reader.read_listing_dbf(DBF,symbols)
        adapter._json('source_evidence/listing_date_records.json',info)
        names={}
        for market in ('SH','SZ','BJ'):
            p=DBF.parent/f'{market.lower()}s.tnf'
            names.update(tnf_names(p.read_bytes(),market))
        rows=[];unknown=[]
        for code in sorted(symbols):
            try:
                listed=_date(info['rows'][code]['SSDATE'])
                if listed>end:raise ValueError('listing_after_requested_date')
                rows.append({'ts_code':code,'name':names[code],'list_date':listed,'name_as_of':today})
            except (ValueError,KeyError):unknown.append(code)
        if rows:
            pd.DataFrame(rows).to_csv(out/'stock_basic.csv',index=False,encoding='utf-8-sig')
            manifest['tables']['stock_basic.csv']={'rows':len(rows),'current_name_only':True,'listing_source':'base.dbf SSDATE',
                'unavailable_symbols':unknown,'historical_delisted_universe_verified':False}
        if unknown:failure('stock_basic_coverage',ValueError(f'{len(unknown)} symbols missing verified listing/name'))
        failure('historical_delisted_universe',ValueError('current_cache_does_not_prove_complete_delisted_population'))
    except Exception as exc:failure('stock_basic.csv',exc)
    # Acquire the entire actual daily universe, with verified resumable source evidence.
    try:
        from .full_factor_acquisition import collect_full_factors
        collect_full_factors(adapter,end)
    except Exception as exc:failure('adj_factor',exc)
    try:
        from .public_supplementary import acquire_public_supplementary
        acquire_public_supplementary(adapter,start,end)
    except Exception as exc:failure('public_supplementary',exc)
    try:
        from .local_pit_orchestrator import acquire_pit_supplementary
        acquire_pit_supplementary(adapter,start,end)
    except Exception as exc:failure('pit_supplementary',exc)
    try:
        from .history_supplementary import acquire_history_supplementary
        acquire_history_supplementary(adapter,start,end)
    except Exception as exc:failure('historical_state',exc)
    manifest['missing_tables']=[name for name in manifest['missing_tables'] if name not in manifest['tables']]


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--calendar-child':_calendar_child(sys.argv[2],sys.argv[3])
    else:raise SystemExit('unsupported_direct_action')
