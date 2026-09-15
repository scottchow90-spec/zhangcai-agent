"""Strict consumers for historical security status and price limits.

Sparse ST event lists are not complete negative evidence. Exact-date historical
basic records may supply explicit ST values; delisting derives from dated names.
"""
import numpy as np
import pandas as pd

KEYS=['trade_date','ts_code']

def keyed(frame, label):
    if frame is None or not set(KEYS)<=set(frame):
        raise ValueError(label+': missing dated security identity')
    x=frame.copy();x['trade_date']=pd.to_datetime(x.trade_date.astype(str),errors='raise',format='mixed').dt.normalize()
    if x[KEYS].isna().any().any() or x.duplicated(KEYS).any():
        raise ValueError(label+': null or duplicate dated security identity')
    return x

def _bool(value):
    # Never let bool('0'), bool('False') or bool(nan) become a true risk flag.
    if isinstance(value,(bool,np.bool_)): return bool(value)
    if isinstance(value,(int,float,np.integer,np.floating)) and value in (0,1): return bool(value)
    if isinstance(value,str) and value.strip().lower() in ('0','1','true','false'):
        return value.strip().lower() in ('1','true')
    raise ValueError('security status boolean missing or invalid')

def attach_pit_risk(candidates, st_status, historical_basic=None, stock_basic=None):
    """Replace current-name fallback and sparse-ST membership inference.

    Historical names must match date exactly. A current cache name is usable only
    on its explicit name_as_of day. Missing history is not backfilled from today.
    """
    e=keyed(candidates,'candidates')
    fields=['is_st','is_delisting_arrangement']
    st=keyed(st_status,'stock_st') if st_status is not None else pd.DataFrame(columns=KEYS)
    e=e.drop(columns=fields+['name','hist_name'],errors='ignore')
    names=[]
    if historical_basic is not None and len(historical_basic):
        hb=keyed(historical_basic,'historical_basic')
        if 'name' not in hb: raise ValueError('historical_basic: missing dated name')
        names.append(hb[KEYS+['name']])
    if stock_basic is not None and len(stock_basic) and {'name','name_as_of','ts_code'}<=set(stock_basic):
        sb=stock_basic[['ts_code','name','name_as_of']].rename(columns={'name_as_of':'trade_date'})
        names.append(keyed(sb,'current_name_cache'))
    if not names: raise ValueError('historical_basic: no exact-date name evidence')
    nm=pd.concat(names,ignore_index=True).drop_duplicates(KEYS+['name'])
    if nm.duplicated(KEYS).any(): raise ValueError('historical_basic: conflicting dated names')
    if nm['name'].isna().any() or nm['name'].astype(str).str.strip().eq('').any():
        raise ValueError('historical_basic: empty dated name')
    e=e.merge(nm,on=KEYS,how='left',validate='one_to_one')
    if e['name'].isna().any(): raise ValueError('historical_basic: date coverage missing; current-name backfill forbidden')
    # Explicit daily is_st can come from complete historical basic records.
    hb=keyed(historical_basic,'historical_basic') if historical_basic is not None else pd.DataFrame(columns=KEYS)
    if 'is_st' in hb:
        statuses=hb[KEYS+['is_st']].copy();statuses['is_st']=statuses.is_st.map(_bool)
        if 'is_st' in st:
            q=st[KEYS+['is_st']].copy();q['is_st']=q.is_st.map(_bool)
            check=q.merge(statuses,on=KEYS,how='left',suffixes=('_source','_history'))
            if check.is_st_history.isna().any() or check.is_st_source.ne(check.is_st_history).any():
                raise ValueError('historical ST sources contradict each other')
        elif len(st):
            # Sparse positives may only be interpreted when explicitly identified.
            if 'type_name' not in st or not st.type_name.isin(['ST','*ST','SST','S*ST']).all():
                raise ValueError('sparse ST rows lack explicit positive status semantics')
            check=st[KEYS].merge(statuses,on=KEYS,how='left')
            if check.is_st.isna().any() or not check.is_st.all():
                raise ValueError('sparse ST positives contradict dated history')
    elif 'is_st' in st:
        statuses=st[KEYS+['is_st']].copy();statuses['is_st']=statuses.is_st.map(_bool)
    else: raise ValueError('stock_st: explicit historical ST state required')
    e=e.merge(statuses,on=KEYS,how='left',validate='one_to_one')
    if e.is_st.isna().any(): raise ValueError('stock_st: historical status coverage missing; absence is not non-ST')
    name_st=e.name.str.match(r'^(?:S\*?ST|\*?ST)',case=False)
    name_delist=e.name.str.contains('退市',regex=False)|e.name.str.startswith('退')
    e['is_delisting_arrangement']=name_delist
    e['delisting_status_basis']='derived_from_dated_name'
    if 'is_delisting_arrangement' in st:
        explicit=st[KEYS+['is_delisting_arrangement']].copy()
        explicit['is_delisting_arrangement']=explicit.is_delisting_arrangement.map(_bool)
        check=e[KEYS+['is_delisting_arrangement']].merge(explicit,on=KEYS,how='inner',suffixes=('_name','_source'))
        if check.is_delisting_arrangement_name.ne(check.is_delisting_arrangement_source).any():
            raise ValueError('dated name contradicts explicit delisting state')
    if (name_st&~e.is_st).any(): raise ValueError('dated name contradicts explicit historical risk status')
    return e

def merge_verified_limits(daily, limits):
    """Join complete daily limits; explicit no_limit is distinct from missing.

    Existing computed columns must use these returned flags, not fillna(False).
    No-limit sessions require both prices null and no_limit=True. Restricted days
    require finite positive limits, including actual exchange rounding in source.
    """
    d=keyed(daily,'daily');l=keyed(limits,'stk_limit')
    if not {'up_limit','down_limit'}<=set(l): raise ValueError('stk_limit: missing limits')
    if 'no_limit' not in l: l['no_limit']=False
    else: l['no_limit']=l.no_limit.map(_bool)
    for field in ['up_limit','down_limit']:
        l[field]=pd.to_numeric(l[field],errors='raise')
    bounded=~l.no_limit
    if l.loc[bounded,['up_limit','down_limit']].isna().any().any():
        raise ValueError('stk_limit: missing price is not an unrestricted session')
    if not np.isfinite(l.loc[bounded,['up_limit','down_limit']].to_numpy()).all():
        raise ValueError('stk_limit: nonfinite price')
    if (l.loc[bounded,['up_limit','down_limit']]<=0).any().any(): raise ValueError('stk_limit: nonpositive price')
    if (l.loc[bounded,'up_limit']<l.loc[bounded,'down_limit']).any(): raise ValueError('stk_limit: inverted prices')
    if l.loc[~bounded,['up_limit','down_limit']].notna().any().any():
        raise ValueError('stk_limit: unrestricted flag contradicts prices')
    d=d.drop(columns=['up_limit','down_limit','no_limit'],errors='ignore')
    d=d.merge(l[KEYS+['up_limit','down_limit','no_limit']],on=KEYS,how='left',validate='one_to_one',indicator='_limit_match')
    if not d['_limit_match'].eq('both').all():
        raise ValueError('stk_limit: dated universe coverage missing; cannot compute market counts')
    d=d.drop(columns='_limit_match')
    # Existing prices are unadjusted exchange daily quotes; compare like for like.
    for field in ['close','high','low']:
        if field in d:
            d[field]=pd.to_numeric(d[field],errors='raise')
            if not np.isfinite(d[field]).all(): raise ValueError('daily: nonfinite price')
    d['is_limit_up']=(~d.no_limit)&(d.close>=d.up_limit-1e-8)
    d['is_limit_down']=(~d.no_limit)&(d.close<=d.down_limit+1e-8)
    if 'high' in d: d['touch_up']=(~d.no_limit)&(d.high>=d.up_limit-1e-8)
    return d
