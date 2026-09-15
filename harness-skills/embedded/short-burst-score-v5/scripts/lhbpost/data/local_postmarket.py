"""Read existing local TDX bars and the registered public billboard sources.

Missing point-in-time data stays missing. Acquisition success is not scoring readiness.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import math
import re
import time
import urllib.parse
import pandas as pd

HOME = Path(r'F:\Codex\Home')
TDX_MODULE = HOME / 'skills/tdx-local-hub/scripts/tdx_hub.py'
LHB_MODULE = HOME / 'skills/a-share-longhubang-analysis/scripts/longhubang_workflow.py'


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _code(code):
    code = str(code)
    if not re.fullmatch(r'\d{6}', code):
        raise ValueError('invalid_security_code')
    from .non_equity_scope import verified_bond_identity
    if verified_bond_identity(code): raise ValueError('verified_non_equity_bond')
    if code.startswith('899'): raise ValueError('non_a_share_index')
    if code.startswith(('4', '8', '92')): return code + '.BJ'
    if code.startswith(('600','601','603','605','688','689')): return code + '.SH'
    if code.startswith(('000','001','002','003','300','301')): return code + '.SZ'
    raise ValueError('non_a_share')


def _number(row, key):
    value = float(row[key])
    if not math.isfinite(value): raise ValueError('invalid_number:' + key)
    return value


def summary_record(row):
    code=_code(row['SECURITY_CODE'])
    item={'ts_code':code,'trade_date':str(row['TRADE_DATE'])[:10].replace('-',''),
        'reason':str(row.get('EXPLANATION') or row.get('EXPLAIN') or ''),
        'source_event_id':str(row.get('TRADE_ID') or ''),
        'source_change_type':str(row.get('CHANGE_TYPE') or '')}
    if not item['reason']:raise ValueError('missing_listing_reason')
    for target,source in [('l_buy','BILLBOARD_BUY_AMT'),('l_sell','BILLBOARD_SELL_AMT'),('net_amount','BILLBOARD_NET_AMT')]:
        item[target]=None if row.get(source) is None else _number(row,source)
    item['amount_disclosure_complete']=all(item[k] is not None for k in ('l_buy','l_sell','net_amount'))
    item['missing_amount_fields']='|'.join(k for k in ('l_buy','l_sell','net_amount') if item[k] is None)
    return item


def merge_public_seats(raw_by_side):
    """Unknown counterpart amounts stay unknown, including source NET placeholders."""
    merged={}
    for source_side, raw in raw_by_side.items():
        for occurrence,row in enumerate(raw):
            try: code=_code(row['SECURITY_CODE'])
            except ValueError: continue
            date=str(row['TRADE_DATE'])[:10].replace('-','')
            reason=str(row.get('EXPLANATION') or row.get('EXPLAIN') or '')
            name=str(row.get('OPERATEDEPT_NAME') or '').strip()
            dept=str(row.get('OPERATEDEPT_CODE') or '').strip()
            if not reason or not name or not dept:raise ValueError('missing_complete_seat_identity')
            identity_disclosed=dept!='0' and name!='机构专用'
            # Anonymous institution rows are not unique seats; cross-side linking is unknowable.
            key=(code,date,reason,dept,name) if identity_disclosed else (code,date,reason,dept,name,source_side,occurrence)
            item=merged.setdefault(key,dict(ts_code=code,trade_date=date,reason=reason,
                exalter=name,seat_code=dept,buy=None,sell=None,source_sides=[],identity_disclosed=identity_disclosed,
                conflict_fields=[],raw_source_rows=[]))
            if source_side not in item['source_sides']:item['source_sides'].append(source_side)
            item['raw_source_rows'].append({'source_side':source_side,'source_row':occurrence,'raw':dict(row)})
            for field,source in [('buy','BUY'),('sell','SELL')]:
                if row.get(source) is None:continue
                value=_number(row,source)
                if value<0:raise ValueError('negative_seat_amount')
                if field in item['conflict_fields']:continue
                if item[field] is not None and item[field]!=value:
                    item['conflict_fields'].append(field);item[field]=None
                else:item[field]=value
    evidence=list(merged.values())
    incomplete_groups=set()
    for row in evidence:
        row['amount_conflict']=bool(row['conflict_fields'])
        row['amounts_complete']=not row['amount_conflict'] and row['buy'] is not None and row['sell'] is not None
        row['net_buy']=row['buy']-row['sell'] if row['amounts_complete'] else None
        if not row['amounts_complete'] or not row['identity_disclosed']:
            incomplete_groups.add((row['ts_code'],row['trade_date'],row['reason']))
    # A complete seat within an incomplete stock/reason group cannot establish totals.
    accepted=[{k:v for k,v in row.items() if k not in {'source_sides','raw_source_rows','conflict_fields'}} for row in evidence
        if (row['ts_code'],row['trade_date'],row['reason']) not in incomplete_groups]
    return evidence,accepted,{'unique_seats':len(evidence),'complete_seats':sum(r['amounts_complete'] for r in evidence),
        'incomplete_seats':sum(not r['amounts_complete'] for r in evidence),
        'anonymous_unmergeable_rows':sum(not r['identity_disclosed'] for r in evidence),
        'conflicting_seats':sum(r['amount_conflict'] for r in evidence),
        'conflicting_groups':[list(k) for k in sorted({(r['ts_code'],r['trade_date'],r['reason']) for r in evidence if r['amount_conflict']})],
        'raw_source_row_count':sum(len(r['raw_source_rows']) for r in evidence),
        'excluded_incomplete_groups':[list(k) for k in sorted(incomplete_groups)],'accepted_seats':len(accepted)}


class LocalPostMarketAdapter:
    INDEX_SYMBOLS = ('sh000001','sz399001','sh000300','sh000905','sh000852','sh932000','sz399006','sh000688')
    MISSING = ('daily_basic','adj_factor','bak_basic','stock_st','stk_limit','stock_basic.csv','sw_members.csv','event_features.csv')

    def __init__(self, out_dir='data_raw', *, max_pages=20, public_budget_seconds=900):
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.max_pages = max(1, min(int(max_pages), 20))
        self.public_budget_seconds = max(1, min(float(public_budget_seconds), 900))
        self.manifest = {'status':'PARTIAL','full_workflow_completed':False,
            'source_mode':'local_tdx_and_registered_public_eastmoney', 'tables':{}, 'failures':[],
            'missing_tables':list(self.MISSING), 'sources':[],
            'units':{'daily.amount':'千元','daily.vol':'手','top_list':'元','top_inst':'元'},
            'boundaries':['No current industry or ST snapshot substitutes historical state.',
                'TDX bars are unadjusted; no artificial adjustment factor is emitted.',
                'Observed index dates are not an authoritative complete exchange calendar.']}

    def _json(self, relative, value):
        p=self.out/relative; p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
        return p

    def _save(self, table, rows):
        if not rows: return
        df=pd.DataFrame(rows).drop_duplicates()
        for date, group in df.groupby('trade_date'):
            p=self.out/table/f'{date}.csv';p.parent.mkdir(parents=True,exist_ok=True)
            group.to_csv(p,index=False,encoding='utf-8-sig')
        self.manifest['tables'][table]={'rows':len(df),'dates':sorted(df.trade_date.unique().tolist()),
            'files':[str(p.relative_to(self.out)) for p in sorted((self.out/table).glob('*.csv'))]}

    @staticmethod
    def _bars(rows, symbol, start, end):
        result=[]; prev=None
        for row in sorted(rows,key=lambda r:r['date']):
            date=str(row['date'])
            close=_number(row,'close')
            if start<=date<=end:
                datetime.strptime(date,'%Y%m%d')
                item={'ts_code':symbol[2:]+'.'+symbol[:2].upper(),'trade_date':date,
                    **{k:_number(row,k) for k in ('open','high','low','close')},
                    'vol':_number(row,'volume')/100,'amount':_number(row,'amount')/1000}
                if prev is not None and prev>0:
                    item['previous_close_raw']=prev
                # A .day file's prior raw close is not the exchange reference on
                # ex-right days. Only an explicitly observed reference may set
                # pre_close/pct_chg; retain missing references as missing.
                references=[]
                for key in ('preclose','pre_close'):
                    value=row.get(key)
                    if value is None or (isinstance(value,str) and not value.strip()) or pd.isna(value):
                        continue
                    reference=_number(row,key)
                    if reference<=0:raise ValueError('nonpositive_source_reference_price:'+key)
                    references.append(reference)
                if references:
                    if any(value!=references[0] for value in references[1:]):
                        raise ValueError('conflicting_source_reference_prices')
                    item.update(pre_close=references[0],pct_chg=(close/references[0]-1)*100)
                result.append(item)
            prev=close
        return result

    def _local(self, start, end):
        hub=_load(TDX_MODULE,'_short_burst_tdx_data')
        # Files can contain dates after a historical request; the tail must reach start.
        days=(datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)-datetime.strptime(start,'%Y%m%d')).days+370
        rows=[]; files=[]; exclusions=[]; classification_pending=[]
        for p in sorted(hub.VIPDOC.rglob('*.day')):
            symbol=p.stem.lower()
            if not re.fullmatch(r'(sh|sz|bj)\d{6}',symbol): continue
            # Classify only the same authoritative day file that the hub will read.
            if hub.day_path(symbol).resolve()!=p.resolve(): continue
            try:
                if _code(symbol[2:]).split('.')[1].lower()!=symbol[:2]: continue
            except ValueError as exc:
                if str(exc)=='verified_non_equity_bond':
                    from .non_equity_scope import exclusion_record
                    exclusions.append(exclusion_record(symbol[2:],p))
                continue
            from .non_equity_scope import VERIFIED_NON_EQUITY
            if symbol[2:] in VERIFIED_NON_EQUITY:
                classification_pending.append({'symbol':symbol,'path':str(p),'reason':'bond_name_class_or_security_master_layout_unverified; retained_for_review'})
            # Follow the same hub precedence; ignore duplicate backfill copies.
            if hub.day_path(symbol).resolve()!=p.resolve(): continue
            try:
                size=p.stat().st_size
                if size%hub.DAY_RECORD.size: raise ValueError('truncated_day_file')
                source_rows=hub.read_day_records(symbol,days)
                got=self._bars(source_rows,symbol,start,end)
                if got:
                    rows.extend(got);files.append({'path':str(p),'size':size,'mtime_ns':p.stat().st_mtime_ns,
                        'first_date':got[0]['trade_date'],'last_date':got[-1]['trade_date'],
                        'source_latest_date':max(str(r['date']) for r in source_rows)})
            except Exception as exc: self.manifest['failures'].append({'source':str(p),'error':str(exc)})
        self._save('daily',rows)
        self._json('source_evidence/tdx_files.json',files)
        self._json('source_evidence/excluded_non_equity_files.json',exclusions)
        self.manifest['excluded_non_equity_sources']=exclusions
        self.manifest['security_classification_pending']=classification_pending
        if classification_pending:self.manifest['failures'].append({'source':'security_classification','error':'unverified_changed_security_identity','count':len(classification_pending)})
        self.manifest['local_coverage']={'symbols_with_requested_bars':len(files),
            'markets':{m:len({r['ts_code'] for r in rows if r['ts_code'].endswith('.'+m)}) for m in ('SH','SZ','BJ')},
            'source_latest_date':max((f['source_latest_date'] for f in files),default=None),
            'requested_end_symbols':len({r['ts_code'] for r in rows if r['trade_date']==end})}
        indices=[]
        for symbol in self.INDEX_SYMBOLS:
            got=self._bars(hub.read_day_records(symbol,days),symbol,start,end)
            indices.extend(got)
            if not got:self.manifest['failures'].append({'source':symbol,'error':'no_index_bars_in_requested_range'})
        self._save('index_daily',indices)
        # Keep observed dates as evidence, not a fabricated production trade_cal.
        self._json('source_evidence/observed_index_dates.json',sorted({r['trade_date'] for r in indices}))
        self.manifest['missing_tables'].append('trade_cal.csv')
        if not rows:self.manifest['failures'].append({'source':'TDX','error':'no_daily_bars_in_requested_range'})

    def _public_rows(self, module, report, start, end, deadline):
        from .public_window_acquisition import acquire_windows
        return acquire_windows(self,module,report,start,end,deadline)

    def _public(self,start,end):
        module=_load(LHB_MODULE,'_short_burst_lhb_data')
        deadline=time.monotonic()+self.public_budget_seconds
        seat_sources={}
        for report,table in ((module.SUMMARY_REPORT,'top_list'),('RPT_BILLBOARD_DAILYDETAILSBUY','top_inst_buy'),('RPT_BILLBOARD_DAILYDETAILSSELL','top_inst_sell')):
            try:
                raw=self._public_rows(module,report,start,end,deadline); rows=[]
                if table!='top_list':
                    seat_sources[table]=raw
                    continue
                for row in raw:
                    try: code=_code(row['SECURITY_CODE'])
                    except ValueError: continue
                    item=summary_record(row)
                    rows.append(item)
                self._save(table,rows)
                incomplete=[r for r in rows if not r['amount_disclosure_complete']]
                self.manifest['summary_disclosure_coverage']={'rows':len(rows),'complete_amount_rows':len(rows)-len(incomplete),
                    'incomplete_amount_rows':len(incomplete),'policy':'source null retained; no zero or counterparty inference'}
                if incomplete:self._json('source_evidence/summary_incomplete_amounts.json',incomplete)
            except Exception as exc:self.manifest['failures'].append({'source':report,'error':f'{type(exc).__name__}:{exc}'})
        # Only merge seat sides when both endpoints completed, deduplicating identical seats.
        if len(seat_sources)==2:
            from ..disclosed_sides import side_records
            disclosed=side_records(seat_sources)
            self._save('disclosed_sides',disclosed)
            self.manifest['disclosed_sides']={'protocol':'DISCLOSED_RANKED_SIDE_CONTRIBUTIONS_V1',
                'acquisition_complete':True,'rows':len(disclosed),'counterpart_or_anonymous_identity':'not_observable',
                'does_not_equal_top_list_actual_net_scope':True}
            evidence,accepted,coverage=merge_public_seats(seat_sources)
            self._json('source_evidence/seat_disclosure_evidence.json',evidence)
            self.manifest['seat_disclosure_coverage']=coverage
            self._save('top_inst',accepted)
            for dt in sorted({r['trade_date'] for r in disclosed}):
                path=self.out/'top_inst'/f'{dt}.csv'
                if not path.exists():
                    path.parent.mkdir(parents=True,exist_ok=True)
                    pd.DataFrame(columns=['ts_code','trade_date','exalter','buy','sell','net_buy','reason','seat_code','identity_disclosed']).to_csv(path,index=False,encoding='utf-8-sig')
            self.manifest['tables'].setdefault('top_inst',{'rows':len(accepted),'purpose':'identifiable_actual_seat_subset_only; ranked sides separately complete'})
            if coverage['excluded_incomplete_groups']:
                self.manifest['seat_identity_observability']={'status':'not_observable','incomplete_seats':coverage['incomplete_seats'],
                    'policy':'ranked_side_contributions_preserved; anonymous_or_unknown_actual_net_not_used_as_real_seat_net'}
        else:self.manifest['missing_tables'].append('top_inst')
        if 'top_list' not in self.manifest['tables']:self.manifest['missing_tables'].append('top_list')

    def _supplementary(self,start,end):
        from .local_supplementary import acquire_supplementary
        acquire_supplementary(self,start,end)

    def download_core(self,start='20180101',end=None):
        self.acquisition_deadline=time.monotonic()+6900
        now=datetime.now(timezone(timedelta(hours=8)))
        end=end or now.strftime('%Y%m%d');start=str(start);end=str(end)
        for value in (start,end):
            if not re.fullmatch(r'\d{8}',value):raise ValueError('date_must_be_YYYYMMDD')
            datetime.strptime(value,'%Y%m%d')
        if start>end or end>now.strftime('%Y%m%d'):raise ValueError('invalid_date_range')
        if end==now.strftime('%Y%m%d') and now.hour<16:raise ValueError('postmarket_data_requires_16_00_Asia_Shanghai')
        self.manifest.update(start=start,end=end,fetched_at=now.isoformat())
        self.manifest.update(status='ACQUIRING',phase='source_identity')
        self._json('acquisition_manifest.json',self.manifest)
        for p in (TDX_MODULE,LHB_MODULE):
            self.manifest['sources'].append({'module':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        for fn in (self._local,self._public):
            self.manifest['phase']=fn.__name__
            self._json('acquisition_manifest.json',self.manifest)
            try:fn(start,end)
            except Exception as exc:self.manifest['failures'].append({'source':fn.__name__,'error':f'{type(exc).__name__}:{exc}'})
            self._json('acquisition_manifest.json',self.manifest)
        self.manifest['phase']='supplementary'
        self._json('acquisition_manifest.json',self.manifest)
        try:
            self._supplementary(start,end)
        except Exception as exc:self.manifest['failures'].append({'source':'supplementary','error':f'{type(exc).__name__}:{exc}'})
        self.manifest['status']='PARTIAL' if self.manifest['tables'] else 'BLOCKED'
        self.manifest['phase']='acquisition_finished_pending_readiness_audit'
        self._json('acquisition_manifest.json',self.manifest)
        return self.out
