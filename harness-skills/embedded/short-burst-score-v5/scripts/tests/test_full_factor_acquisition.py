import json
from pathlib import Path
from datetime import datetime,timezone,timedelta
import pandas as pd
import pytest
from lhbpost.data.full_factor_acquisition import collect_full_factors,validate_record,digest,SCHEMA


class Adapter:
    def __init__(self,out):self.out=out;self.manifest={'failures':[]};out.mkdir(exist_ok=True)
    def _save(self,table,rows):
        if rows:
            p=self.out/table;p.mkdir(exist_ok=True);pd.DataFrame(rows).to_csv(p/'20260911.csv',index=False)
    def _json(self,path,value):
        p=self.out/path;p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(value),encoding='utf-8')


def bars(out,count=130):
    p=out/'daily';p.mkdir(exist_ok=True,parents=True)
    pd.DataFrame([{'ts_code':f'{600000+i:06d}.SH','trade_date':'20260911'} for i in range(count)]).to_csv(p/'20260911.csv',index=False)


def fetch(url,timeout):
    symbol=url.split('/')[-2]
    return ('var '+symbol+'hfq={"data":[{"d":"1900-01-01","f":"2"}]} /* tail */').encode()


def test_entire_universe_over_old_120_cap_and_resume(tmp_path):
    first=Adapter(tmp_path/'first');bars(first.out)
    result=collect_full_factors(first,'20260911',cache_root=tmp_path/'cache',fetch=fetch)
    assert result['complete'] and result['completed_symbols']==130
    second=Adapter(tmp_path/'second');bars(second.out)
    def forbidden(*a):raise AssertionError('valid source should be reused')
    result=collect_full_factors(second,'20260911',cache_root=tmp_path/'cache',fetch=forbidden)
    assert result['complete'] and result['cache_hits']==130


def test_budget_preserves_explicit_pending_then_resume(tmp_path):
    first=Adapter(tmp_path/'first');bars(first.out,4)
    result=collect_full_factors(first,'20260911',budget_seconds=0,cache_root=tmp_path/'cache',fetch=fetch)
    assert not result['complete'] and len(result['pending_symbols'])==4
    assert first.manifest['failures'][0]['error']=='full_universe_incomplete'
    result=collect_full_factors(first,'20260911',cache_root=tmp_path/'cache',fetch=fetch)
    assert result['complete']


def record():
    raw=fetch('https://finance.sina.com.cn/realstock/company/sh600000/hfq.js',8).decode()
    return {'schema':SCHEMA,'ts_code':'600000.SH','source_url':'https://finance.sina.com.cn/realstock/company/sh600000/hfq.js',
        'raw_text':raw,'raw_sha256':digest(raw),'fetched_at':'2026-09-11T18:00:00+08:00'}


@pytest.mark.parametrize('field,value',[('raw_sha256','bad'),('ts_code','600001.SH'),('fetched_at','2026-09-11T15:00:00+08:00')])
def test_cache_identity_hash_and_close_cutoff(field,value):
    r=record();r[field]=value
    with pytest.raises(ValueError):validate_record(r,'600000.SH','20260911')


def test_bad_cached_symbol_response_not_accepted(tmp_path):
    adapter=Adapter(tmp_path/'run');bars(adapter.out,1)
    def wrong(url,timeout):return fetch('https://finance.sina.com.cn/realstock/company/sh600001/hfq.js',timeout)
    result=collect_full_factors(adapter,'20260911',cache_root=tmp_path/'cache',fetch=wrong)
    assert not result['complete'] and result['failed_symbols']
    assert not list((tmp_path/'cache').glob('*.json'))


def test_historical_120_days_each_get_effective_factor(tmp_path):
    adapter=Adapter(tmp_path/'run');p=adapter.out/'daily';p.mkdir()
    dates=pd.bdate_range(end='2026-09-11',periods=120)
    for dt in dates:
        day=dt.strftime('%Y%m%d');pd.DataFrame([dict(ts_code='600000.SH',trade_date=day)]).to_csv(p/(day+'.csv'),index=False)
    result=collect_full_factors(adapter,'20260911',cache_root=tmp_path/'cache',fetch=fetch)
    assert result['produced_factor_rows']==120 and result['complete']

@pytest.mark.parametrize('fallback_fails',[False,True])
def test_cdr_fallback_preserves_primary_failure_and_requires_evidence(tmp_path,monkeypatch,fallback_fails):
    from lhbpost.data import cdr_factor_source
    adapter=Adapter(tmp_path/'run');p=adapter.out/'daily';p.mkdir()
    pd.DataFrame([dict(ts_code='689009.SH',trade_date='20260911')]).to_csv(p/'20260911.csv',index=False)
    def empty(*a):return b'var sh689009hfq={"data":[]};'
    def fallback(a,dates,end):
        assert dates==['20260911'] and end=='20260911'
        if fallback_fails:raise ValueError('missing_corporate_actions')
        return [dict(ts_code='689009.SH',trade_date=end,adj_factor=1.23)],{}
    monkeypatch.setattr(cdr_factor_source,'collect_cdr_factors',fallback)
    result=collect_full_factors(adapter,'20260911',cache_root=tmp_path/'cache',fetch=empty)
    assert result['complete'] is (not fallback_fails)
    if fallback_fails:
        assert 'missing_corporate_actions' in result['failed_symbols']['689009.SH']
    else:
        assert result['produced_factor_rows']==1
        assert 'hfq_empty' in result['verified_source_fallbacks'][0]['primary_error']
