from pathlib import Path
from types import SimpleNamespace
import importlib.util
import json
import sys
import subprocess
from datetime import datetime,timezone
import pandas as pd
import pytest
from lhbpost.data import local_pit_orchestrator as m
from lhbpost.data import historical_capital_source
from lhbpost.data import sina_float_history


@pytest.fixture(autouse=True)
def isolate_capital_cache(monkeypatch):
    monkeypatch.setattr(historical_capital_source,'collect_local_capital',
        lambda adapter,requests,end:({}, {code:'fixture_no_local_capital' for code in requests}))
    monkeypatch.setattr(sina_float_history,'collect_float_fallback',
        lambda adapter,requests,end:({}, {code:'fixture_no_sina_capital' for code in requests}))

def evidence(code='600127.SH',start='20260910',end='20260910'):
    return {'stock_code':code,'method':'get_gb_info_by_date','request_start':start,'request_end':end,
        'status':'RECEIVED','completed_at':datetime.now(timezone.utc).isoformat(),
        'response':[{'Date':int(end),'Ltgb':10000,'Zgb':20000}]}

def adapter(tmp_path,budget=10):
    (tmp_path/'daily').mkdir(exist_ok=True)
    pd.DataFrame([{'ts_code':'600127.SH','trade_date':'20260910','close':10,'vol':100}]).to_csv(tmp_path/'daily'/'20260910.csv',index=False)
    return SimpleNamespace(out=tmp_path,manifest={},pit_budget_seconds=budget,pit_cache_root=tmp_path/'cache')

def write_more(cache,end='20260910',observed=None):
    r=evidence(end=end);r['method']='get_more_info'
    r['response']={'HqDate':observed or end,'ZTPrice':11,'DTPrice':9,'FreeLtgb':1}
    m.pit.atomic_json(cache/'600127.SH.get_more_info.json',r)

def test_cache_rejects_hash_identity_range_and_outside_date(tmp_path):
    path=tmp_path/'600127.SH.get_gb_info_by_date.json';r=evidence();m.pit.atomic_json(path,r)
    ledger={path.name:m.digest(path)}
    assert m.cached_record(path,'600127.SH','get_gb_info_by_date','20260910','20260910',ledger)
    assert not m.cached_record(path,'600128.SH','get_gb_info_by_date','20260910','20260910',ledger)
    assert not m.cached_record(path,'600127.SH','get_gb_info_by_date','20260909','20260910',ledger)
    r['response'][0]['Ltgb']=9999;m.pit.atomic_json(path,r)
    assert not m.cached_record(path,'600127.SH','get_gb_info_by_date','20260910','20260910',ledger)
    r['response'][0]['Date']=20260911;m.pit.atomic_json(path,r);ledger[path.name]=m.digest(path)
    assert not m.cached_record(path,'600127.SH','get_gb_info_by_date','20260910','20260910',ledger)

def test_resume_uses_verified_cache_without_new_source_calls(tmp_path,monkeypatch):
    a=adapter(tmp_path)
    def child(command,**kwargs):
        assert kwargs['timeout']<=60
        cache=Path(command[command.index('--out')+1]);m.pit.atomic_json(cache/'600127.SH.get_gb_info_by_date.json',evidence());write_more(cache)
        return subprocess.CompletedProcess(command,0,'','')
    monkeypatch.setattr(m.subprocess,'run',child)
    r=m.acquire_pit_supplementary(a,'20260910','20260910');assert r['basic_complete']
    frame=pd.read_csv(tmp_path/'daily_basic'/'20260910.csv');assert frame.iloc[0]['turnover_rate']==100
    def no_calls(*args,**kwargs):raise AssertionError('cache should be reused')
    monkeypatch.setattr(m.subprocess,'run',no_calls)
    assert m.acquire_pit_supplementary(a,'20260910','20260910')['basic_complete']

def test_zero_budget_keeps_exact_debt(tmp_path,monkeypatch):
    a=adapter(tmp_path,0)
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k: (_ for _ in ()).throw(AssertionError('no budget')))
    r=m.acquire_pit_supplementary(a,'20260910','20260910')
    assert not r['basic_complete'] and r['daily_basic_rows']==0
    assert r['missing_keys'][0]['trade_date']=='20260910'

def test_failed_child_cannot_adopt_preexisting_untrusted_response(tmp_path,monkeypatch):
    a=adapter(tmp_path);cache=tmp_path/'cache'/'20260910-20260910';cache.mkdir(parents=True)
    m.pit.atomic_json(cache/'600127.SH.get_gb_info_by_date.json',evidence())
    monkeypatch.setattr(m.subprocess,'run',lambda command,**kw:subprocess.CompletedProcess(command,2,'','fail'))
    r=m.acquire_pit_supplementary(a,'20260910','20260910');assert not r['basic_complete']

def test_timeout_preserves_completed_atomic_item(tmp_path,monkeypatch):
    a=adapter(tmp_path)
    def child(command,**kwargs):
        cache=Path(command[command.index('--out')+1]);m.pit.atomic_json(cache/'600127.SH.get_gb_info_by_date.json',evidence());write_more(cache)
        raise subprocess.TimeoutExpired(command,kwargs['timeout'])
    monkeypatch.setattr(m.subprocess,'run',child)
    assert m.acquire_pit_supplementary(a,'20260910','20260910')['basic_complete']

def test_cross_run_cache_is_copied_and_hash_bound(tmp_path,monkeypatch):
    first=tmp_path/'first';second=tmp_path/'second';first.mkdir();second.mkdir()
    a=adapter(first);b=adapter(second);b.pit_cache_root=a.pit_cache_root
    def child(command,**kwargs):
        cache=Path(command[command.index('--out')+1]);m.pit.atomic_json(cache/'600127.SH.get_gb_info_by_date.json',evidence());write_more(cache)
        return subprocess.CompletedProcess(command,0,'','')
    monkeypatch.setattr(m.subprocess,'run',child);m.acquire_pit_supplementary(a,'20260910','20260910')
    def no_call(*a,**k):raise AssertionError('cross run cache not used')
    monkeypatch.setattr(m.subprocess,'run',no_call)
    assert m.acquire_pit_supplementary(b,'20260910','20260910')['basic_complete']
    bound=second/'source_evidence'/'pit';ledger=json.loads((bound/'cache_manifest.json').read_text(encoding='utf-8'))
    assert ledger['sha256']['600127.SH.get_gb_info_by_date.json']==m.digest(bound/'600127.SH.get_gb_info_by_date.json')

def test_observed_more_date_mismatch_not_refetched_or_backfilled(tmp_path,monkeypatch):
    a=adapter(tmp_path)
    def child(command,**kwargs):
        cache=Path(command[command.index('--out')+1]);m.pit.atomic_json(cache/'600127.SH.get_gb_info_by_date.json',evidence());write_more(cache,observed='20260911')
        return subprocess.CompletedProcess(command,0,'','')
    monkeypatch.setattr(m.subprocess,'run',child);r=m.acquire_pit_supplementary(a,'20260910','20260910')
    assert r['today_limit_rows']==0 and not r['basic_complete']
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('known mismatch repeated')))
    assert m.acquire_pit_supplementary(a,'20260910','20260910')['today_limit_rows']==0

def test_historical_only_stock_does_not_require_current_more(tmp_path,monkeypatch):
    a=adapter(tmp_path,0)
    cache=tmp_path/'cache'/'20260910-20260911';cache.mkdir(parents=True)
    response=evidence(end='20260911');response['response'][0]['Date']=20260910
    path=cache/'600127.SH.get_gb_info_by_date.json';m.pit.atomic_json(path,response)
    m.pit.atomic_json(cache/'cache_manifest.json',{path.name:m.digest(path)})
    result=m.acquire_pit_supplementary(a,'20260910','20260911')
    assert result['basic_complete'] and result['pending_codes']==[]
    assert result['today_limit_rows']==0

def test_local_event_capital_keeps_its_own_source_identity(tmp_path,monkeypatch):
    a=adapter(tmp_path,0)
    response={'600127.SH':{'response':[dict(Date=20260910,Ltgb=10000,Zgb=20000,capital_effective_date='20260901')]}}
    monkeypatch.setattr(historical_capital_source,'collect_local_capital',lambda *args:(response,{}))
    result=m.acquire_pit_supplementary(a,'20260910','20260911')
    assert result['basic_complete'] and result['local_capital_recovered_codes']==['600127.SH']
    row=pd.read_csv(tmp_path/'daily_basic/20260910.csv').iloc[0]
    assert row['share_source']=='local_tdx_gbbq_event_history' and row['capital_effective_date']==20260901
