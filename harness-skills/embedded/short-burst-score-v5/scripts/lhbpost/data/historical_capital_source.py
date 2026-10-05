"""Event-effective shares from existing TDX gbbq, never current-state backfill.

pytdx get_xdxr_info categories 2..10 store before-float, before-total,
after-float, after-total. gbbq stores ten-thousand-share float32 values.
Conversion float32(value*10000) matches native TQ Ltgb/Zgb shares, including
12 before/after values on 000001/000002/000006 at 2026-06-30, exactly.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import struct,math,hashlib,importlib.util,sys

_app_scripts_dir = str(Path(__file__).resolve().parents[6] / 'scripts')
if _app_scripts_dir not in sys.path: sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_app_root, resolve_tdx_root

APP_ROOT=resolve_app_root();TDX_ROOT=resolve_tdx_root()
CACHE=TDX_ROOT/'T0002'/'hq_cache'/'gbbq'
READER=APP_ROOT/'harness-skills'/'feilong-strategy'/'vendor'/'pytdx-1.72'/'pytdx'/'reader'/'gbbq_reader.py'
FIELDS=('hongli_panqianliutong','peigujia_qianzongguben','songgu_qianzongguben','peigu_houzongguben')

def day(value):
    text=str(value).replace('-','')
    if len(text)!=8 or not text.isdigit():raise ValueError('invalid_capital_date')
    datetime.strptime(text,'%Y%m%d');return text

def native_shares(value):
    x=float(value)
    if not math.isfinite(x) or x<0:raise ValueError('invalid_capital_value')
    return struct.unpack('<f',struct.pack('<f',x*10000))[0]

def capital_history(code, records, dates, end):
    end=day(end);dates=sorted({day(d) for d in dates})
    if not dates or dates[-1]>end:raise ValueError('invalid_requested_capital_range')
    suffix=code[-2:];market={'SH':1,'SZ':0,'BJ':2}.get(suffix)
    if market is None or len(code)!=9:raise ValueError('invalid_capital_security')
    candidates=[day(r['datetime']) for r in records if int(r['category']) in range(2,11) and day(r['datetime'])<=dates[0]]
    if not candidates:raise ValueError('historical_capital_baseline_missing')
    relevant_anchor=max(candidates)
    states={};other=[]
    for row in records:
        if str(row['code'])!=code[:6] or int(row['market'])!=market:raise ValueError('capital_security_identity_mismatch')
        dt=day(row['datetime'])
        if dt>end:continue
        if dt<relevant_anchor:continue
        cat=int(row['category'])
        if cat not in range(2,11):other.append((dt,cat,row));continue
        before_float,before_total,after_float,after_total=[native_shares(row[k]) for k in FIELDS]
        if after_total<=0 or after_float<=0 or after_float>after_total or before_float>before_total:
            raise ValueError('invalid_capital_structure')
        values=(before_float,before_total,after_float,after_total)
        if dt in states and states[dt]['values']!=values:raise ValueError('ambiguous_same_date_capital_states')
        states[dt]={'values':values,'category':cat,'raw':dict(row)}
    baseline=[d for d in states if d<=dates[0]]
    if not baseline:raise ValueError('historical_capital_baseline_missing')
    anchor=max(baseline);current=states[anchor]['values'][2:];effective=anchor
    for dt,cat,row in other:
        if dt<anchor:continue
        if cat!=1:raise ValueError('unsupported_capital_event_requires_review')
        # Cash dividends leave shares unchanged; share bonuses/rights require an
        # explicit same-day post-event share record, never inferred from prices.
        bonus=float(row[FIELDS[2]]);rights=float(row[FIELDS[3]])
        if any(not math.isfinite(v) or v<0 for v in (bonus,rights)):raise ValueError('invalid_capital_action')
        if (bonus or rights) and dt not in states:raise ValueError('share_changing_action_without_effective_capital_state')
    changes=sorted(d for d in states if d>anchor);i=0;response=[];used={anchor}
    for dt in dates:
        while i<len(changes) and changes[i]<=dt:
            event=changes[i];state=states[event]
            if state['values'][:2]!=current:raise ValueError('capital_event_chain_discontinuity')
            current=state['values'][2:];effective=event;used.add(event);i+=1
        response.append({'Date':int(dt),'Ltgb':current[0],'Zgb':current[1],
                         'capital_effective_date':effective,'capital_source':'local_tdx_gbbq_event_history'})
    proof={'ts_code':code,'first_baseline_date':anchor,'requested_dates':dates,
           'used_states':{d:states[d] for d in sorted(used)},
           'unit_policy':'native_float32(gbbq_ten_thousand_shares*10000) = shares',
           'date_policy':'post-event values effective on event date; last confirmed state carries until next event',
           'source_scope':'current local corporate-action cache; no independent completeness claim'}
    return response,proof

def collect_local_capital(adapter, requests_by_code, end, *, cache=CACHE,reader=READER):
    """Returns successful code responses and explicit per-code failures."""
    cache=Path(cache);reader=Path(reader);end=day(end)
    def read(p):
        before=p.stat();raw=p.read_bytes();after=p.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('capital_source_changed')
        return raw,{'path':str(p.resolve()),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'mtime_ns':after.st_mtime_ns}
    raw,source=read(cache);_,decoder=read(reader)
    count=struct.unpack('<I',raw[:4])[0]
    if len(raw)!=4+count*29:raise ValueError('capital_cache_layout_invalid')
    stamp=datetime.fromtimestamp(cache.stat().st_mtime,timezone(timedelta(hours=8))).strftime('%Y%m%d')
    if stamp<end:raise ValueError('capital_cache_stale_for_requested_end')
    spec=importlib.util.spec_from_file_location('_historical_capital_gbbq',reader)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    decoded=module.GbbqReader().get_df(str(cache))
    if len(decoded)!=count or hashlib.sha256(cache.read_bytes()).hexdigest()!=source['sha256']:
        raise ValueError('capital_cache_decode_count_or_identity_changed')
    success={};failure={};observations={}
    for code,dates in requests_by_code.items():
        market={'SH':1,'SZ':0,'BJ':2}.get(code[-2:])
        records=decoded.loc[(decoded.code==code[:6])&(decoded.market==market)].to_dict('records')
        observations[code]=records
        try:
            response,proof=capital_history(code,records,dates,end)
            success[code]={'response':response,'proof':proof}
        except (ValueError,KeyError,TypeError,OverflowError) as exc:
            failure[code]=f'{type(exc).__name__}:{exc}'
    evidence={'schema':'TDX_EVENT_EFFECTIVE_CAPITAL_V1','source':source,'decoder':decoder,
        'source_record_count':count,'requested_codes':sorted(requests_by_code),
        'observations':observations,'successful':success,'failures':failure,
        'policy':'missing records/baseline/chain remain missing; no current shares or guessed delisting'}
    adapter._json('source_evidence/local_historical_capital.json',evidence)
    return success,failure
