"""Bounded public collection components; no credentials, inferred facts or workflow claims."""
from __future__ import annotations
import json
import math
import re
import time
from pathlib import Path
import pandas as pd
import requests

CSI_URL = 'https://www.csindex.com.cn/csindex-home/perf/index-perf'
ANN_URL = 'https://np-anotice-stock.eastmoney.com/api/security/ann'

def _save(root, name, payload):
    if root is not None:
        p = Path(root); p.mkdir(parents=True, exist_ok=True)
        (p / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

def _number(value):
    x = float(value)
    if not math.isfinite(x):
        raise ValueError('source contains non-finite numeric value')
    return x

def fetch_csi2000(start, end, *, session=None, evidence_dir=None, expected_dates=None):
    """Return raw-store units: amount thousands CNY, volume lots, pct points.

    CSI tradingValue is 100 million CNY and tradingVol shares. Independently
    cross-checked against TDX CSI300 on 2026-09-10 (3906.16 vs 390616186880 CNY,
    14692255200 shares vs 146922552 lots). No synthetic index substitution.
    """
    lo = pd.Timestamp(start).strftime('%Y%m%d'); hi = pd.Timestamp(end).strftime('%Y%m%d')
    if lo > hi: raise ValueError('inverted date range')
    wanted = None
    if expected_dates is not None:
        wanted = {pd.Timestamp(d).strftime('%Y%m%d') for d in expected_dates}
        if not wanted or any(d < lo or d > hi for d in wanted):
            raise ValueError('invalid CSI expected trading dates')
        # The source inserts a chart-boundary copy when startDate is a holiday.
        # Request actual calendar endpoints; never relabel or accept that copy.
        lo, hi = min(wanted), max(wanted)
    client = session or requests.Session()
    r = client.get(CSI_URL, params={'indexCode':'932000', 'startDate':lo, 'endDate':hi}, timeout=30)
    r.raise_for_status(); data = r.json(); _save(evidence_dir, 'csi2000-response.json', data)
    if str(data.get('code')) != '200' or data.get('success') is not True:
        raise ValueError('CSI source rejected request')
    rows = []
    for x in data.get('data') or []:
        if x.get('indexCode') != '932000': raise ValueError('CSI index identity mismatch')
        day = pd.to_datetime(str(x['tradeDate']), format='%Y%m%d').strftime('%Y%m%d')
        if not lo <= day <= hi: raise ValueError('CSI response outside requested dates')
        row = {'ts_code':'932000.CSI', 'trade_date':day,
               **{k:_number(x[k]) for k in ('open','high','low','close')},
               'pct_chg':_number(x['changePct']), 'amount':_number(x['tradingValue'])*100000,
               'vol':_number(x['tradingVol'])/100, 'source':CSI_URL}
        if min(row[k] for k in ('open','high','low','close')) <= 0 or row['amount'] < 0 or row['vol'] < 0:
            raise ValueError('invalid CSI prices or turnover')
        if not row['low'] <= min(row['open'], row['close']) <= max(row['open'], row['close']) <= row['high']:
            raise ValueError('inconsistent CSI OHLC')
        rows.append(row)
    frame = pd.DataFrame(rows)
    if frame.empty or frame.duplicated(['ts_code','trade_date']).any():
        raise ValueError('empty or duplicate CSI series')
    if wanted is not None:
        if set(frame.trade_date) != wanted: raise ValueError('CSI trading-date coverage mismatch')
    return frame.sort_values('trade_date').reset_index(drop=True)

def _publication_time(value):
    # Platform display_time is publication display, not notice_date (document day)
    # nor eiTime (ingestion). Require explicit wall-clock precision in source.
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?::\d{3})?', value):
        raise ValueError('announcement display_time missing or malformed')
    if len(value) > 19: value = value[:19] + '.' + value[20:]
    return pd.Timestamp(value).tz_localize('Asia/Shanghai')

def fetch_candidate_announcements(codes, trade_date, as_of, *, session=None, evidence_dir=None,
                                  page_size=100, max_pages=100, budget_seconds=120):
    """Return (events, coverage). Coverage is source announcements ONLY.

    All reported pages are fetched, identities and totals checked. A empty result
    is accompanied by source responses and cannot establish no public events.
    Titles are not promoted to catalysts, themes or risk classifications.
    """
    cutoff = pd.Timestamp(as_of)
    if cutoff.tzinfo is None: raise ValueError('as_of requires timezone')
    day = pd.Timestamp(trade_date).strftime('%Y-%m-%d')
    close = pd.Timestamp(day+'T15:00:00+08:00')
    if cutoff < close: raise ValueError('as_of must be after market close')
    client = session or requests.Session(); rows=[]; proofs=[]
    deadline = time.monotonic() + budget_seconds
    for code in sorted(set(codes)):
        if not re.fullmatch(r'\d{6}\.(SH|SZ|BJ)', code): raise ValueError('invalid candidate identity')
        bare = code[:6]; seen=set(); total=None; pages=0
        for page in range(1,max_pages+1):
            remaining = deadline - time.monotonic()
            if remaining <= 0: raise TimeoutError('announcement_acquisition_budget_exhausted')
            r = client.get(ANN_URL, params={'sr':-1,'page_size':page_size,'page_index':page,
                'ann_type':'A','client_source':'web','stock_list':bare,'f_node':0,'s_node':0,
                'begin_time':day,'end_time':(pd.Timestamp(day)+pd.Timedelta(days=1)).strftime('%Y-%m-%d')}, timeout=min(30, remaining))
            r.raise_for_status(); response=r.json(); _save(evidence_dir,f'ann-{bare}-{page}.json',response)
            if response.get('success') != 1 or not isinstance(response.get('data'),dict):
                raise ValueError('announcement source failure')
            data=response['data']; reported=int(data['total_hits']); items=data.get('list')
            if not isinstance(items,list) or reported < 0: raise ValueError('invalid announcement page')
            if total is None: total=reported
            if reported != total: raise ValueError('announcement pagination changed during collection')
            pages=page
            for item in items:
                identity=item.get('art_code')
                if not identity or identity in seen: raise ValueError('missing or duplicate announcement identity')
                seen.add(identity)
                matches=[v for v in item.get('codes',[]) if v.get('stock_code')==bare]
                if not matches: raise ValueError('announcement candidate mismatch')
                pub=_publication_time(item.get('display_time'))
                if close < pub <= cutoff and pub.strftime('%Y-%m-%d')==day:
                    rows.append({'ts_code':code,'trade_date':day,'public_time':pub.isoformat(),
                       'title':item['title'],'event_id':identity,'source':ANN_URL,
                       'source_url':f'https://data.eastmoney.com/notices/detail/{bare}/{identity}.html',
                       'publication_time_basis':'source_display_time_Asia_Shanghai',
                       'event_type':'company_announcement','semantic_review_required':True})
            if len(seen)==total: break
            if len(seen)>total or not items: raise ValueError('announcement incomplete pagination')
        else: raise ValueError('announcement page limit prevents complete source collection')
        proofs.append({'ts_code':code,'source_total':total,'retrieved':len(seen),'pages':pages,'source_pagination_complete':True})
    coverage={'scope':'candidate_company_announcements_on_eastmoney_only','source':ANN_URL,
              'trade_date':day,'as_of':cutoff.isoformat(),'candidates':proofs,
              'all_public_events_complete':False,'semantic_review_complete':False,
              'reason':'Source pagination proves only this announcement feed; not all public events or event interpretation.'}
    _save(evidence_dir,'announcement-coverage.json',coverage)
    return pd.DataFrame(rows,columns=['ts_code','trade_date','public_time','title','event_id','source','source_url',
            'publication_time_basis','event_type','semantic_review_required']),coverage
