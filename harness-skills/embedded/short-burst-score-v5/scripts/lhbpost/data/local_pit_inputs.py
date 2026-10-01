"""Read-only TQ source capture. Date-dependent mapping requires source evidence."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import math
from datetime import datetime, timezone

_app_scripts_dir = str(Path(__file__).resolve().parents[6] / 'scripts')
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_app_root

HUB = resolve_app_root() / 'harness-skills' / 'tdx-local-hub' / 'scripts' / 'tdx_hub.py'
METHODS = ('get_stock_info', 'get_gb_info_by_date', 'get_market_snapshot', 'get_more_info',
           'get_gpjy_value_by_date', 'get_divid_factors')

def positive(value,field,allow_zero=False):
    if isinstance(value,bool):raise ValueError('invalid_numeric:'+field)
    result=float(value)
    if not math.isfinite(result) or result<0 or (result==0 and not allow_zero):
        raise ValueError('invalid_numeric:'+field)
    return result

def history_basic_rows(code,bars,share_response):
    """TQ Date/Ltgb/Zgb are daily shares; input bars use package raw lots.

    Observed three-exchange responses establish shares, corroborated against
    stock_info ActiveCapital (10k shares) and more_info fHSL. Never forward fill.
    Returned package raw daily_basic uses 10k shares / 10k CNY and percent turn.
    """
    if not isinstance(share_response,list):raise ValueError('share_response_not_list')
    shares={}
    for row in share_response:
        day=str(row['Date']);validate_request([code],day,day)
        if day in shares:raise ValueError('duplicate_share_date:'+day)
        lt=positive(row['Ltgb'],'Ltgb');total=positive(row['Zgb'],'Zgb')
        if lt>total:raise ValueError('float_exceeds_total:'+day)
        shares[day]=(lt,total)
    result=[];missing=[];seen=set()
    for bar in bars:
        if str(bar['ts_code'])!=code:continue
        day=str(bar['trade_date']).replace('-','')[:8]
        validate_request([code],day,day)
        if day in seen:raise ValueError('duplicate_bar_date:'+day)
        seen.add(day)
        if day not in shares:
            missing.append({'ts_code':code,'trade_date':day,'reason':'exact_daily_share_missing'})
            continue
        lt,total=shares[day];close=positive(bar['close'],'close')
        lots=positive(bar['vol'],'vol',allow_zero=True)
        result.append({'ts_code':code,'trade_date':day,'close':close,
            'turnover_rate':lots*100/lt*100,'float_share':lt/10000,'total_share':total/10000,
            'circ_mv':lt*close/10000,'total_mv':total*close/10000,
            'share_source':'TQ.get_gb_info_by_date','share_date':day,
            'capitalization_basis':'circulating_shares_not_free_float'})
    return result,missing

def dated_more_rows(code,more,requested_date,close):
    """Only dated current facts; this method cannot fill historical gaps."""
    validate_request([code],requested_date,requested_date)
    if not isinstance(more,dict) or str(more.get('HqDate'))!=requested_date:
        raise ValueError('more_info_date_mismatch')
    up=positive(more['ZTPrice'],'ZTPrice');down=positive(more['DTPrice'],'DTPrice')
    if down>up:raise ValueError('limit_price_order')
    free=positive(more['FreeLtgb'],'FreeLtgb')
    return ({'ts_code':code,'trade_date':requested_date,'up_limit':up,'down_limit':down,
             'source':'TQ.get_more_info','source_date':requested_date},
            {'ts_code':code,'trade_date':requested_date,'close':positive(close,'close'),
             'free_share':free,'free_share_source':'TQ.get_more_info','free_share_date':requested_date})


def dated_free_row(code,more,requested_date,close):
    """Free float remains observed even when a separate limit state is unrestricted."""
    validate_request([code],requested_date,requested_date)
    if not isinstance(more,dict) or str(more.get('HqDate'))!=requested_date:
        raise ValueError('more_info_date_mismatch')
    return {'ts_code':code,'trade_date':requested_date,'close':positive(close,'close'),
        'free_share':positive(more['FreeLtgb'],'FreeLtgb'),
        'free_share_source':'TQ.get_more_info','free_share_date':requested_date}

def capture_share_batch(codes,start,end,out,include_more=False):
    """One bounded parent-owned child per batch, one connection, atomic each code.

    Parent must call subprocess with timeout <= 60 seconds and retain partial
    evidence. No retries or desktop lifecycle operations are performed here.
    """
    if not codes or len(codes)>100 or len(set(codes))!=len(codes):
        raise ValueError('share_batch_requires_one_to_100_unique_codes')
    for code in codes:validate_request([code],start,end)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('_pit_hub',HUB)
    hub=importlib.util.module_from_spec(spec);spec.loader.exec_module(hub)
    with hub.TQLock(timeout_seconds=5):
        tq,_=hub.load_tq()
        for code in codes:
            path=out/f'{code}.get_gb_info_by_date.json'
            record={'stock_code':code,'method':'get_gb_info_by_date','request_start':start,
                    'request_end':end,'started_at':datetime.now(timezone.utc).isoformat(),'status':'STARTED'}
            atomic_json(path,record)
            try:
                response=tq.get_gb_info_by_date(stock_code=code,start_date=start,end_date=end)
                if not isinstance(response,list) or not response:raise ValueError('empty_or_invalid_share_response')
                record.update(status='RECEIVED',response=response)
            except Exception as exc:record.update(status='ERROR',error=f'{type(exc).__name__}:{exc}')
            record['completed_at']=datetime.now(timezone.utc).isoformat();atomic_json(path,record)
            if include_more:
                path=out/f'{code}.get_more_info.json'
                record={'stock_code':code,'method':'get_more_info','request_start':start,
                    'request_end':end,'started_at':datetime.now(timezone.utc).isoformat(),'status':'STARTED'}
                atomic_json(path,record)
                try:
                    response=tq.get_more_info(stock_code=code)
                    if not isinstance(response,dict) or not response:raise ValueError('empty_more_response')
                    record.update(status='RECEIVED',response=response)
                except Exception as exc:record.update(status='ERROR',error=f'{type(exc).__name__}:{exc}')
                record['completed_at']=datetime.now(timezone.utc).isoformat();atomic_json(path,record)

def atomic_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    os.replace(temp,path)

def validate_request(codes,start,end):
    if not codes or len(codes)>3 or len(set(codes))!=len(codes):
        raise ValueError('probe_requires_one_to_three_unique_codes')
    if any(not re.fullmatch(r'\d{6}\.(SH|SZ|BJ)',code) for code in codes):
        raise ValueError('invalid_stock_code')
    for day in (start,end):
        if not re.fullmatch(r'\d{8}',day):raise ValueError('invalid_date')
        datetime.strptime(day,'%Y%m%d')
    if start>end:raise ValueError('date_order')

def capture_one(code,method,start,end,path):
    if method not in METHODS:raise ValueError('method_not_read_only_allowlisted')
    validate_request([code],start,end)
    evidence={'stock_code':code,'method':method,'request_start':start,'request_end':end,
              'started_at':datetime.now(timezone.utc).isoformat(),'status':'STARTED'}
    atomic_json(path,evidence)
    try:
        spec=importlib.util.spec_from_file_location('_pit_hub',HUB)
        hub=importlib.util.module_from_spec(spec);spec.loader.exec_module(hub)
        with hub.TQLock(timeout_seconds=5):
            tq,_=hub.load_tq()
            if method=='get_gb_info_by_date':
                response=tq.get_gb_info_by_date(stock_code=code,start_date=start,end_date=end)
            elif method=='get_gpjy_value_by_date':
                response=tq.get_gpjy_value_by_date(stock_list=[code],field_list=[],
                    year=int(end[:4]),mmdd=int(end[4:]))
                evidence['field_request_policy']='source_default_empty_list_schema_probe_no_guessed_ids'
            elif method=='get_divid_factors':
                frame=tq.get_divid_factors(stock_code=code,start_time=start,end_time=end)
                response=json.loads(frame.to_json(orient='split',date_format='iso'))
                evidence['response_serialization']='pandas.DataFrame.to_json(split,iso); missing values null'
                evidence['interpretation']='raw_corporate_action_fields_not_price_adjustment_multiplier'
            else:response=getattr(tq,method)(stock_code=code)
        evidence.update(status='RECEIVED',response=response)
    except Exception as exc:
        evidence.update(status='ERROR',error=f'{type(exc).__name__}:{exc}')
    evidence['completed_at']=datetime.now(timezone.utc).isoformat()
    atomic_json(path,evidence)
    return evidence

def capture_probe(codes,start,end,out,timeout=30):
    validate_request(codes,start,end)
    if not 1<=timeout<=30:raise ValueError('timeout_out_of_bounds')
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    records=[]
    for code in codes:
        for method in METHODS:
            path=out/f'{code}.{method}.json'
            command=[sys.executable,'-B',str(Path(__file__).resolve()),'--child',
                     '--codes',code,'--start',start,'--end',end,'--out',str(path),'--method',method]
            try:
                cp=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
                record={'code':code,'method':method,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr}
            except subprocess.TimeoutExpired:
                record={'code':code,'method':method,'status':'TIMEOUT','timeout_seconds':timeout}
            records.append(record)
            atomic_json(out/'probe_receipt.json',{'records':records,'completed':False})
    atomic_json(out/'probe_receipt.json',{'records':records,'completed':True})
    return records

if __name__=='__main__':
    if os.environ.get('CODEX_STOCK_CANONICAL_EXECUTION')!='1' or os.environ.get('ONESTOCK_STOCK_CANONICAL_CHILD')!='1':
        raise SystemExit('canonical_child_required')
    p=argparse.ArgumentParser();p.add_argument('--codes',nargs='+',required=True)
    p.add_argument('--start',required=True);p.add_argument('--end',required=True)
    p.add_argument('--out',required=True);p.add_argument('--child',action='store_true')
    p.add_argument('--share-batch',action='store_true')
    p.add_argument('--include-more',action='store_true')
    p.add_argument('--method',choices=METHODS);args=p.parse_args()
    if args.share_batch:
        capture_share_batch(args.codes,args.start,args.end,args.out,args.include_more)
        raise SystemExit(0)
    if args.child:
        result=capture_one(args.codes[0],args.method,args.start,args.end,args.out)
        raise SystemExit(0 if result['status']=='RECEIVED' else 2)
    capture_probe(args.codes,args.start,args.end,args.out)
