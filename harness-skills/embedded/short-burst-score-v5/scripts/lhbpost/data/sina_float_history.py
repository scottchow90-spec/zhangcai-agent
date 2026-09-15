"""Dated Sina outstanding shares; no total/free-share inference or prehistory fill."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib, json, re, urllib.request

SOURCE_CODE = Path(r'C:\Users\25296\AppData\Local\Programs\Python\Python313\Lib\site-packages\akshare\stock\stock_zh_a_sina.py')
URL = 'https://stock.finance.sina.com.cn/stock/api/jsonp.php/var%20KKE_ShareAmount_{0}=/StockService.getAmountBySymbol?_=20&symbol={0}'

def _symbol(symbol):
    if not re.fullmatch(r'(?:sh|sz)\d{6}', symbol):
        raise ValueError('invalid_symbol')
    return symbol

def _day(day):
    if not isinstance(day, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day):
        raise ValueError('invalid_date')
    return datetime.strptime(day, '%Y-%m-%d').date()

def _positive(value):
    if isinstance(value, bool): raise ValueError('invalid_amount')
    try: result = Decimal(str(value))
    except InvalidOperation: raise ValueError('invalid_amount')
    if not result.is_finite() or result <= 0: raise ValueError('invalid_amount')
    return result

def parse_float_history(raw, symbol):
    """AkShare adapter establishes positional date/amount and 10000 share scale.

    Effective history is provider-reconstructed, not archived publication proof.
    Unknown object schemas fail rather than guessing by dictionary order.
    """
    _symbol(symbol)
    text = raw.decode('utf-8-sig').strip()
    match = re.fullmatch(r'var\s+KKE_ShareAmount_' + re.escape(symbol) + r'\s*=\s*\(?\s*(\[.*\])\s*\)?\s*;?', text, re.S)
    if not match: raise ValueError('source_identity_or_wrapper_invalid')
    from akshare.utils import demjson
    rows = demjson.decode(match.group(1))
    if not isinstance(rows, list) or not rows: raise ValueError('empty_or_invalid_history')
    observations = {}
    for row in rows:
        if isinstance(row, dict):
            if set(row) == {'date', 'amount'}: day, amount = row['date'], row['amount']
            elif set(row) == {'date', 'outstanding_share'}: day, amount = row['date'], row['outstanding_share']
            else: raise ValueError('unverified_object_field_schema')
        elif isinstance(row, list) and len(row) == 2: day, amount = row
        else: raise ValueError('invalid_history_row')
        _day(day)
        shares = _positive(amount) * 10000
        if shares != shares.to_integral_value(): raise ValueError('fractional_shares')
        if day in observations: raise ValueError('duplicate_effective_date')
        observations[day] = int(shares)
    dates = sorted(observations)
    digest = hashlib.sha256(raw).hexdigest()
    return [{'symbol': symbol, 'in_date': day,
             'out_date': (_day(dates[i+1])-timedelta(days=1)).isoformat() if i+1<len(dates) else None,
             'float_share': observations[day], 'total_share': None, 'free_share': None,
             'source_unit': '10000_shares', 'normalized_unit': 'shares',
             'source_sha256': digest, 'publication_time_archive_verified': False,
             'temporal_scope': 'provider_effective_history_retrieved_now'} for i, day in enumerate(dates)]

def float_as_of(intervals, symbol, day):
    _symbol(symbol); _day(day)
    matches = [r for r in intervals if r['symbol']==symbol and r['in_date']<=day and (r['out_date'] is None or day<=r['out_date'])]
    if len(matches)>1: raise ValueError('overlapping_share_intervals')
    return dict(matches[0]) if matches else None

def derive_observed_metrics(intervals, symbol, day, *, unadjusted_close, volume_shares):
    row = float_as_of(intervals, symbol, day)
    if row is None: return None
    close = _positive(unadjusted_close)
    volume = Decimal(str(volume_shares))
    if not volume.is_finite() or volume<0: raise ValueError('invalid_volume')
    return {**row, 'trade_date':day, 'circ_mv_yuan':float(close*row['float_share']),
            'turnover_rate_percent':float(volume/row['float_share']*100), 'total_mv_yuan':None}

def acquire_float_history(symbol, out_dir, *, fetch=None, timeout_seconds=20):
    """Canonical caller only. Bounded single-symbol raw fetch; never retries silently."""
    _symbol(symbol)
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    url=URL.format(symbol)
    receipt={'schema':'SINA_DATED_FLOAT_SHARES_V1','symbol':symbol,'url':url,'status':'ACQUIRING',
             'source_code':str(SOURCE_CODE),'source_code_sha256':hashlib.sha256(SOURCE_CODE.read_bytes()).hexdigest(),
             'unit_evidence':'AkShare stock_zh_a_daily outstanding_share multiplied by 10000',
             'publication_time_archive_verified':False}
    try:
        if fetch is None:
            request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(request,timeout=timeout_seconds) as response: raw=response.read(2_000_001)
        else: raw=fetch(url,timeout_seconds)
        if len(raw)>2_000_000: raise ValueError('response_size_limit')
        raw_path=out/(symbol+'-float-history.js'); raw_path.write_bytes(raw)
        receipt.update(raw_file=raw_path.name,raw_sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw),fetched_at=datetime.now(timezone.utc).isoformat())
        receipt['intervals']=parse_float_history(raw,symbol)
        receipt['status']='OBSERVED_EFFECTIVE_HISTORY'
    except Exception as exc:
        receipt.update(status='FAILED',error=type(exc).__name__+':'+str(exc))
    (out/(symbol+'-float-history.receipt.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    return receipt


def collect_float_fallback(adapter,bars_by_code,end):
    """Recover only fields actually supplied by the dated float-share history."""
    succeeded={};failed={}
    for code,bars in sorted(bars_by_code.items()):
        if not code.endswith(('.SH','.SZ')):
            failed[code]='sina_float_exchange_not_supported';continue
        symbol=code[-2:].lower()+code[:6]
        evidence=adapter.out/'source_evidence/sina_float_history'/code
        receipt=acquire_float_history(symbol,evidence,timeout_seconds=10)
        if receipt['status']!='OBSERVED_EFFECTIVE_HISTORY':
            failed[code]=receipt.get('error','float_history_unavailable');continue
        rows=[];missing=[]
        for bar in bars:
            day=datetime.strptime(str(bar['trade_date']),'%Y%m%d').strftime('%Y-%m-%d')
            if str(bar['trade_date'])>end:raise ValueError('float_fallback_future_bar')
            observed=derive_observed_metrics(receipt['intervals'],symbol,day,
                unadjusted_close=bar['close'],volume_shares=Decimal(str(bar['vol']))*100)
            if observed is None:
                missing.append({'ts_code':code,'trade_date':bar['trade_date'],'reason':'sina_float_prebaseline_unobserved'});continue
            rows.append({'ts_code':code,'trade_date':bar['trade_date'],'close':bar['close'],
                'turnover_rate':observed['turnover_rate_percent'],'float_share':observed['float_share']/10000,
                'circ_mv':observed['circ_mv_yuan']/10000,'total_share':None,'total_mv':None,
                'share_source':'Sina.StockService.getAmountBySymbol','share_date':bar['trade_date'],
                'capital_effective_date':observed['in_date'].replace('-',''),
                'capital_evidence':str(evidence.relative_to(adapter.out)/(symbol+'-float-history.receipt.json')),
                'capitalization_basis':'circulating_shares_not_free_float','unobserved_capital_fields':'total_share|total_mv'})
        succeeded[code]={'rows':rows,'missing':missing}
    return succeeded,failed
