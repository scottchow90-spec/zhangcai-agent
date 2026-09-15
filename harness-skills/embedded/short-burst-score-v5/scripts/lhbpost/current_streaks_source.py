"""Offline reconstruction of current sealed streaks from bound historical pools."""
from pathlib import Path
from decimal import Decimal,InvalidOperation
from urllib.parse import urlparse
import csv,hashlib,io,json,re

SCHEMA='CURRENT_DAY_VERIFIED_SEALED_STREAKS_V1'

def _integer(value,field):
    if isinstance(value,bool):raise ValueError('invalid_integer:'+field)
    try:v=Decimal(str(value))
    except InvalidOperation:raise ValueError('invalid_integer:'+field)
    if not v.is_finite() or v!=v.to_integral_value():raise ValueError('invalid_integer:'+field)
    return int(v)

def _read(path):
    path=Path(path).resolve();before=path.stat();raw=path.read_bytes();after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('source_changed_during_read')
    return raw,{'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def _date(value):
    from datetime import datetime
    x=str(value).replace('-','')
    if not re.fullmatch(r'\d{8}',x):raise ValueError('invalid_source_date')
    datetime.strptime(x,'%Y%m%d');return x

def _symbol(value):
    code=str(value)
    if not re.fullmatch(r'\d{6}',code):raise ValueError('invalid_pool_security')
    if code.startswith(('600','601','603','605','688','689')):return code+'.SH'
    if code.startswith(('000','001','002','003','300','301')):return code+'.SZ'
    raise ValueError('unsupported_pool_security')

def _bool(value):
    if value in (True,'True','true',1,'1'):return True
    if value in (False,'False','false',0,'0'):return False
    raise ValueError('invalid_csv_boolean')

def verify_current_streaks_evidence(csv_path,proof_path):
    """Recompute membership/streak/dense rank; supplied booleans are not proof.

    Independent full-current daily quote/limit comparison remains owned by the
    caller. The proof's current count, completed flags and CSV hash are checked,
    never trusted in place of the bound source responses and calendar sequence.
    """
    raw,proof_binding=_read(proof_path);proof=json.loads(raw)
    if proof.get('schema')!=SCHEMA:raise ValueError('current_streak_source_schema')
    target=_date(proof['trade_date'])
    csv_raw,csv_binding=_read(csv_path)
    if Path(proof['csv_path']).resolve()!=Path(csv_path).resolve() or proof.get('csv_sha256')!=csv_binding['sha256']:
        raise ValueError('current_streak_csv_identity')
    reader=csv.DictReader(io.StringIO(csv_raw.decode('utf-8-sig')));rows=list(reader)
    required={'trade_date','ts_code','board_streak','market_height_rank','is_limit_up','is_limit_down','up_limit','down_limit','no_limit'}
    if not required<=set(reader.fieldnames or []):raise ValueError('current_streak_csv_fields')
    if not rows or len(rows)!=_integer(proof['universe'],'universe'):raise ValueError('current_streak_universe_count')
    universe={}
    for row in rows:
        code=str(row['ts_code'])
        if _symbol(code[:6])!=code or code in universe:raise ValueError('current_streak_duplicate_or_invalid_security')
        if _date(row['trade_date'])!=target:raise ValueError('current_streak_csv_date')
        if _integer(row['board_streak'],'board_streak')<0:raise ValueError('negative_current_streak')
        universe[code]=row
    source_bindings=proof.get('source_bindings')
    if not isinstance(source_bindings,list) or not 2<=len(source_bindings)<=21:raise ValueError('current_streak_bound_sources_missing')
    pools={};bindings=[proof_binding,csv_binding]
    for item in source_bindings:
        day=_date(item['requested_date'])
        if day>target or day in pools:raise ValueError('current_streak_source_order_or_duplicate')
        request=item.get('request_params') or {}
        if _date(request.get('date'))!=day or _integer(request.get('page'),'page')!=1:
            raise ValueError('current_streak_request_identity')
        url=urlparse(item['url'])
        if url.scheme!='https' or url.hostname!='data.10jqka.com.cn' or url.path!='/dataapi/limit_up/limit_up_pool':
            raise ValueError('current_streak_source_endpoint')
        source_raw,binding=_read(item['path'])
        if item.get('sha256')!=binding['sha256']:raise ValueError('current_streak_raw_hash')
        obj=json.loads(source_raw);data=obj.get('data') or {};page=data.get('page') or {};info=data.get('info')
        if obj.get('status_code')!=0 or not isinstance(info,list) or _date(data.get('date'))!=day:
            raise ValueError('current_streak_source_response')
        if _integer(page.get('total'),'page.total')!=len(info) or _integer(page.get('page'),'page.page')!=1 or _integer(page.get('count'),'page.count')!=1:
            raise ValueError('current_streak_pool_incomplete')
        if _integer(item['rows'],'rows')!=len(info):raise ValueError('current_streak_bound_row_count')
        pool={}
        for stock in info:
            code=_symbol(stock['code'])
            if code in pool:raise ValueError('current_streak_duplicate_pool_member')
            latest=Decimal(str(stock['latest']))
            if not latest.is_finite() or latest<=0:raise ValueError('current_streak_pool_price')
            pool[code]=stock
        pools[day]=pool;bindings.append(dict(binding,requested_date=day))
    if target not in pools:raise ValueError('current_streak_target_pool_missing')
    # Bound calendar is mandatory: dates cannot be omitted to turn a broken
    # consecutive chain into a higher streak, or suspended days silently skipped.
    calendar=proof.get('calendar_evidence')
    if not isinstance(calendar,dict):raise ValueError('current_streak_calendar_missing')
    calendar_raw,calendar_binding=_read(calendar['path'])
    if calendar.get('sha256')!=calendar_binding['sha256']:raise ValueError('current_streak_calendar_hash')
    calendar_reader=csv.DictReader(io.StringIO(calendar_raw.decode('utf-8-sig')))
    opened=[];seen_calendar=set()
    for row in calendar_reader:
        day=_date(row.get('cal_date',row.get('calendar_date')))
        if day in seen_calendar:raise ValueError('current_streak_calendar_duplicate')
        seen_calendar.add(day)
        if _bool(row.get('is_open',row.get('is_trading_day'))) and day<=target:opened.append(day)
    opened=sorted(opened)
    if not opened or opened[-1]!=target:raise ValueError('current_streak_calendar_target')
    calendar_source_raw,calendar_source_binding=_read(calendar['source_response'])
    if calendar.get('source_response_sha256')!=calendar_source_binding['sha256']:raise ValueError('current_streak_calendar_source_hash')
    cal_source=json.loads(calendar_source_raw)
    if cal_source.get('method')!='TQ.get_trading_dates' or cal_source.get('market')!='SH' or cal_source.get('count')!=-1 or cal_source.get('returncode')!=0:
        raise ValueError('current_streak_calendar_source_identity')
    if _date(cal_source.get('request_end'))!=target:raise ValueError('current_streak_calendar_source_end')
    markers=[s.split('=',1)[1] for s in cal_source.get('stdout','').splitlines() if s.startswith('CALENDAR_JSON=')]
    if len(markers)!=1:raise ValueError('current_streak_calendar_source_response')
    observed_dates=[_date(v) for v in json.loads(markers[0])]
    if len(observed_dates)!=len(set(observed_dates)) or sorted(observed_dates)!=opened:
        raise ValueError('current_streak_calendar_source_table_mismatch')
    actual_dates=sorted(pools,reverse=True)
    if actual_dates!=list(reversed(opened))[:len(actual_dates)]:raise ValueError('current_streak_calendar_session_skipped')
    bindings.extend([calendar_binding,calendar_source_binding])
    current=set(pools[target]);remaining=set(current);streak={code:1 for code in current}
    if len(current)!=_integer(proof['current_sealed_count'],'current_sealed_count'):raise ValueError('current_streak_current_count')
    if not current<=set(universe):raise ValueError('current_streak_pool_outside_universe')
    for day in actual_dates[1:]:
        for code in remaining&set(pools[day]):streak[code]+=1
        remaining&=set(pools[day])
    if remaining:raise ValueError('current_streak_chain_unterminated')
    if sorted(proof.get('bounded_prior_pool_dates') or [],reverse=True)!=actual_dates[1:]:raise ValueError('current_streak_claimed_dates')
    levels=sorted(set(streak.values())|({0} if set(universe)-current else set()),reverse=True)
    rank={v:i+1 for i,v in enumerate(levels)}
    for code,row in universe.items():
        value=streak.get(code,0)
        if _integer(row['board_streak'],'board_streak')!=value:raise ValueError('current_streak_csv_value_mismatch:'+code)
        if _integer(row['market_height_rank'],'market_height_rank')!=rank[value]:raise ValueError('current_streak_dense_rank_mismatch:'+code)
        if _bool(row['is_limit_up'])!=(code in current):raise ValueError('current_streak_limit_flag_mismatch:'+code)
    for code,source in pools[target].items():
        label=source.get('high_days');m=re.fullmatch(r'(\d+)天(\d+)板',str(label))
        if label=='首板' and streak[code]!=1:raise ValueError('current_streak_provider_label_mismatch')
        if m and m.group(1)==m.group(2) and int(m.group(1))!=streak[code]:raise ValueError('current_streak_provider_label_mismatch')
    return {'schema':SCHEMA,'trade_date':proof['trade_date'],'verified':True,'universe':len(rows),
        'current_sealed_count':len(current),'reconstructed_streaks':streak,'source_dates':actual_dates,
        'csv_sha256':csv_binding['sha256'],'proof_sha256':proof_binding['sha256'],'source_bindings':bindings,
        'verification':'raw_source_reconstruction_plus_exact_csv_streak_and_dense_rank'}
