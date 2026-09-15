"""Explicit no-limit state, grounded in pinned 2026 exchange rule originals.

Zero source prices are never sufficient evidence. IPO date, complete daily
calendar, registration flag and exact official document identity are required.
Other no-limit reasons (delisting/relisting) need their own explicit evidence.
"""
from pathlib import Path
from datetime import datetime,timedelta
import hashlib,math,re

RULES={
 'SH':{
  'id':'SSE_2026_3.3.13_6.6_IPO',
  'url':'https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/10816482/files/959da0158c65434daa8a43a6e32be7ba.docx',
  'sha256':'fc922c433438b2636cb631eab25cca405209712acbb6aaded768c45456ff8888',
  'effective_from':'20260706',
  'notice_url':'https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/c_20260424_10816482.shtml'},
 'SZ':{
  'id':'SZSE_2026_3.3.15_IPO',
  'url':'http://docs.static.szse.cn/www/lawrules/rule/trade/current/W020260424690713155663.pdf',
  'sha256':'9b66f8b0db70f84a25ef1ccb4ee2351001724e408117552d75f6d8993483c586',
  'effective_from':'20260706',
  'notice_url':'https://www.szse.cn/lawrules/rule/trade/current/t20260424_620190.html'},
}
RULE_FILES={'SH':'sse-trading-rules-2026.docx','SZ':'szse-trading-rules-2026.pdf'}

def packaged_rule_evidence(exchange,skill_root):
    if exchange not in RULES:raise ValueError('unsupported_no_limit_exchange')
    evidence={**RULES[exchange],'path':str(Path(skill_root)/'references'/'rules'/RULE_FILES[exchange])}
    verify_rule_document(exchange,evidence)
    return evidence

def day(value):
    value=str(value)
    if not re.fullmatch(r'\d{8}',value):raise ValueError('invalid_date')
    datetime.strptime(value,'%Y%m%d')
    return value

def numeric(value):
    if isinstance(value,bool):raise ValueError('invalid_limit_number')
    value=float(value)
    if not math.isfinite(value) or value<0:raise ValueError('invalid_limit_number')
    return value

def verify_rule_document(exchange,evidence):
    rule=RULES.get(exchange)
    if not rule:raise ValueError('unsupported_no_limit_exchange')
    if not isinstance(evidence,dict):raise ValueError('rule_evidence_missing')
    for field in ('id','url','sha256','effective_from','notice_url'):
        if evidence.get(field)!=rule[field]:raise ValueError('rule_evidence_identity_mismatch:'+field)
    path=Path(evidence['path'])
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=rule['sha256']:
        raise ValueError('rule_document_hash_mismatch')
    return rule

def listing_session_no(list_date,trade_date,calendar):
    start=day(list_date);end=day(trade_date)
    if start>end:raise ValueError('listing_after_target')
    # Current function is narrowly for newly-listed stocks. Avoid scanning years
    # or accepting a missing-calendar shortcut as a first-five-session proof.
    if (datetime.strptime(end,'%Y%m%d')-datetime.strptime(start,'%Y%m%d')).days>40:
        raise ValueError('ipo_window_out_of_scope')
    observed={}
    for row in calendar:
        date=day(row['cal_date'])
        if not start<=date<=end:continue
        if date in observed:raise ValueError('duplicate_calendar_date')
        value=str(row['is_open'])
        if value not in ('0','1'):raise ValueError('invalid_calendar_flag')
        observed[date]=int(value)
    cursor=datetime.strptime(start,'%Y%m%d');finish=datetime.strptime(end,'%Y%m%d')
    expected=set()
    while cursor<=finish:
        expected.add(cursor.strftime('%Y%m%d'));cursor+=timedelta(days=1)
    if set(observed)!=expected:raise ValueError('incomplete_calendar_interval')
    if observed[start]!=1 or observed[end]!=1:raise ValueError('listing_or_target_not_open')
    return sum(observed.values())

def resolve_current_limit_state(code,more,trade_date,listing,calendar,rule_evidence=None):
    """Return CSV-safe explicit state; raises on unproved zero/contradiction.

    listing must be the source-bound stock_basic record, not a name-derived
    guess. Its source identity is bound by the parent canonical acquisition.
    """
    target=day(trade_date)
    if not re.fullmatch(r'\d{6}\.(SH|SZ|BJ)',code):raise ValueError('invalid_stock_code')
    if not isinstance(more,dict) or str(more.get('HqDate'))!=target:raise ValueError('quote_date_mismatch')
    up=numeric(more['ZTPrice']);down=numeric(more['DTPrice'])
    base={'ts_code':code,'trade_date':target,'up_limit':up,'down_limit':down,
          'source':'TQ.get_more_info','source_date':target,'no_limit':0,'limit_status':'LIMITED'}
    if up>0 and down>0:
        if down>up:raise ValueError('limit_price_order')
        if rule_evidence and str(more.get('IsZCZGP'))=='1' and isinstance(listing,dict) and listing.get('ts_code')==code:
            listed=day(listing['list_date'])
            gap=(datetime.strptime(target,'%Y%m%d')-datetime.strptime(listed,'%Y%m%d')).days
            if 0<=gap<=40 and listed>=rule_evidence.get('effective_from','99999999'):
                verify_rule_document(code.rsplit('.',1)[1],rule_evidence)
                if listing_session_no(listed,target,calendar)<=5:raise ValueError('positive_limits_conflict_with_ipo_rule')
        return base
    if up!=0 or down!=0:raise ValueError('one_sided_zero_limit')
    exchange=code.rsplit('.',1)[1]
    if exchange=='SH' and not code.startswith(('600','601','603','605','688','689')):
        raise ValueError('unsupported_ipo_security')
    if exchange=='SZ' and not code.startswith(('000','001','002','003','300','301')):
        raise ValueError('unsupported_ipo_security')
    rule=verify_rule_document(exchange,rule_evidence)
    if not isinstance(listing,dict) or listing.get('ts_code')!=code:raise ValueError('listing_identity_mismatch')
    listed=day(listing['list_date'])
    if target<rule['effective_from'] or listed<rule['effective_from']:
        raise ValueError('rule_effective_interval_not_proven')
    if str(more.get('IsZCZGP'))!='1':raise ValueError('registration_status_not_proven')
    ordinal=listing_session_no(listed,target,calendar)
    if not 1<=ordinal<=5:raise ValueError('outside_ipo_first_five_sessions')
    base.update(no_limit=1,up_limit=None,down_limit=None,source_up_limit=up,source_down_limit=down,
        limit_status='NO_LIMIT_REGISTERED_IPO',listing_session_no=ordinal,
        rule_id=rule['id'],rule_url=rule['url'],rule_sha256=rule['sha256'],rule_effective_from=rule['effective_from'],
        listing_date=listed,no_limit_reason='official_registered_ipo_first_five_sessions')
    return base
