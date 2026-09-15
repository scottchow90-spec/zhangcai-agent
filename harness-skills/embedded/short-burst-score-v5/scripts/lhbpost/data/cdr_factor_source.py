"""689009 CDR adjustment from existing TDX corporate-action cache and raw bars.

Cash/bonus/rights units are per 10 receipts; prices are CNY per receipt. Factors
are dimensionless back-adjustment multipliers, anchored at first raw observation.
This component never treats an empty upstream factor response as factor one.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,importlib.util,json,math,struct

CACHE=Path(r'D:\TDX\T0002\hq_cache\gbbq')
DAY=Path(r'D:\TDX\vipdoc\sh\lday\sh689009.day')
READER=Path(r'F:\Codex\Home\skills\a-share-oss-research\runtimes\fasiondog-hikyuu\Lib\site-packages\pytdx\reader\gbbq_reader.py')

def _day(value):
    text=str(value).replace('-','')
    datetime.strptime(text,'%Y%m%d')
    return text

def build_cdr_factors(records, bars, dates, end):
    end=_day(end);target=sorted({_day(d) for d in dates})
    if not target or target[-1]>end:raise ValueError('invalid_cdr_requested_dates')
    prices={}
    for row in bars:
        day=_day(row['trade_date']);close=float(row['close'])
        if day in prices or not math.isfinite(close) or close<=0:raise ValueError('invalid_cdr_raw_prices')
        if day<=end:prices[day]=close
    if not set(target)<=set(prices):raise ValueError('cdr_raw_date_coverage_missing')
    actions={};seen=set();listing=False
    for row in records:
        if str(row['code'])!='689009' or int(row['market'])!=1:raise ValueError('cdr_action_security_mismatch')
        day=_day(row['datetime']);cat=int(row['category'])
        if day>end:continue
        if (day,cat) in seen:raise ValueError('duplicate_cdr_action')
        seen.add((day,cat))
        if cat not in (1,5):raise ValueError('unsupported_cdr_action_category_requires_review')
        if day==min(prices) and cat==5:listing=True
        if cat==1:actions[day]=row
    if not listing:raise ValueError('cdr_action_history_not_anchored_at_first_raw_session')
    if not set(actions)<=set(prices):raise ValueError('cdr_action_date_not_in_raw_trading_history')
    factors={};prev=None;factor=1.;event_evidence=[]
    for day in sorted(prices):
        if day in actions:
            if prev is None:raise ValueError('cdr_action_requires_preceding_raw_close')
            a=actions[day]
            cash,rights_price,bonus,rights=[float(a[k]) for k in ('hongli_panqianliutong','peigujia_qianzongguben','songgu_qianzongguben','peigu_houzongguben')]
            if any(not math.isfinite(v) or v<0 for v in (cash,rights_price,bonus,rights)):
                raise ValueError('invalid_cdr_corporate_action_values')
            reference=(prev-cash/10+rights_price*rights/10)/(1+bonus/10+rights/10)
            if not math.isfinite(reference) or reference<=0:raise ValueError('invalid_cdr_exright_reference')
            multiplier=prev/reference;factor*=multiplier
            event_evidence.append({'trade_date':day,'raw_previous_close':prev,'exright_reference':reference,
                                   'cash_per_10':cash,'bonus_per_10':bonus,'rights_per_10':rights,
                                   'rights_price':rights_price,'step_multiplier':multiplier})
        factors[day]=factor;prev=prices[day]
    # No-action histories require separate complete-source proof; this fallback is
    # explicitly for the observed CDR action history, not a generic identity fill.
    if not event_evidence:raise ValueError('cdr_no_observed_actions_cannot_assume_identity_factor')
    return [{'ts_code':'689009.SH','trade_date':day,'adj_factor':factors[day]} for day in target],event_evidence

def collect_cdr_factors(adapter, dates, end, *, cache=CACHE, day_file=DAY, reader=READER):
    cache=Path(cache);day_file=Path(day_file);reader=Path(reader)
    def read_stable(p):
        before=p.stat();raw=p.read_bytes();after=p.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('cdr_source_changed_during_read')
        return raw,{'path':str(p.resolve()),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'mtime_ns':after.st_mtime_ns}
    cache_raw,cache_proof=read_stable(cache);day_raw,day_proof=read_stable(day_file);_,reader_proof=read_stable(reader)
    if len(day_raw)%32 or not day_raw:raise ValueError('cdr_day_record_layout_invalid')
    count=struct.unpack('<I',cache_raw[:4])[0]
    if len(cache_raw)!=4+count*29:raise ValueError('cdr_cache_record_layout_invalid')
    cache_date=datetime.fromtimestamp(cache.stat().st_mtime,timezone(timedelta(hours=8))).strftime('%Y%m%d')
    if cache_date<_day(end):raise ValueError('cdr_local_action_cache_stale_for_requested_end')
    spec=importlib.util.spec_from_file_location('_cdr_local_gbbq_reader',reader)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    decoded=module.GbbqReader().get_df(str(cache))
    if hashlib.sha256(cache.read_bytes()).hexdigest()!=cache_proof['sha256']:raise ValueError('cdr_cache_changed_during_decode')
    if len(decoded)!=count:raise ValueError('cdr_cache_decode_count_mismatch')
    records=decoded.loc[(decoded.code=='689009')&(decoded.market==1)].to_dict('records')
    if not records:raise ValueError('cdr_no_security_action_records')
    bars=[]
    for offset in range(0,len(day_raw),32):
        day,op,high,low,close,amount,vol,reserved=struct.unpack('<IIIIIfII',day_raw[offset:offset+32])
        bars.append({'trade_date':str(day),'close':close/100})
    rows,events=build_cdr_factors(records,bars,dates,end)
    evidence={'schema':'TDX_CDR_CORPORATE_ACTION_FACTORS_V1','ts_code':'689009.SH','cache':cache_proof,
        'raw_day':day_proof,'reader':reader_proof,'source_record_count':count,'security_records':records,
        'event_calculations':events,'requested_dates':sorted(dates),'end':_day(end),
        'unit_policy':'cash/bonus/rights per 10 CDR receipts; price CNY per receipt; dimensionless multiplier',
        'formula':'factor *= previous_close / ((previous_close-cash/10+rights_price*rights/10)/(1+bonus/10+rights/10))',
        'source_scope':'existing local TDX corporate-action snapshot; not a claim of independently audited exchange completeness'}
    adapter._json('source_evidence/cdr_689009_factor_source.json',evidence)
    return rows,evidence
