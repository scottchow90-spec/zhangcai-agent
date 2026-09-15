import importlib.util
from pathlib import Path
import json
import subprocess
import pytest

source=Path(__file__).with_name('local_pit_inputs.py')
if not source.exists():source=Path(__file__).parents[1]/'lhbpost/data/local_pit_inputs.py'
spec=importlib.util.spec_from_file_location('local_pit_inputs',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

@pytest.mark.parametrize('codes,start,end',[
    ([], '20260101','20260911'),
    (['600000.SH']*2,'20260101','20260911'),
    (['600000.SH;evil'],'20260101','20260911'),
    (['600000.SH'],'20261301','20260911'),
    (['600000.SH'],'20260912','20260911'),
])
def test_invalid_request(codes,start,end):
    with pytest.raises(ValueError):m.validate_request(codes,start,end)

def test_atomic_unicode(tmp_path):
    p=tmp_path/'a.json';m.atomic_json(p,{'name':'中文'})
    assert json.loads(p.read_text(encoding='utf-8'))=={'name':'中文'}
    assert not p.with_name('a.json.tmp').exists()

def test_orders_not_allowed(tmp_path):
    with pytest.raises(ValueError,match='read_only_allowlisted'):
        m.capture_one('600000.SH','send_order','20260101','20260911',tmp_path/'a.json')

def test_timeout_preserves_per_item_receipt(monkeypatch,tmp_path):
    def timeout(*args,**kwargs):raise subprocess.TimeoutExpired(args[0],kwargs['timeout'])
    monkeypatch.setattr(m.subprocess,'run',timeout)
    records=m.capture_probe(['600000.SH'],'20260101','20260911',tmp_path)
    assert len(records)==len(m.METHODS)
    assert all(r['status']=='TIMEOUT' and r['timeout_seconds']==30 for r in records)
    assert json.loads((tmp_path/'probe_receipt.json').read_text(encoding='utf-8'))['completed']

def test_observed_share_units_and_turnover():
    bars=[{'ts_code':'600127.SH','trade_date':'20260911','close':13.55,'vol':2445674}]
    rows,gaps=m.history_basic_rows('600127.SH',bars,[{'Date':20260911,'Ltgb':641783232,'Zgb':641783232}])
    assert not gaps
    assert rows[0]['float_share']==pytest.approx(64178.3232)
    assert round(rows[0]['turnover_rate'],2)==38.11
    assert rows[0]['circ_mv']==pytest.approx(869616.27936)
    assert 'free_share' not in rows[0]

def test_historical_share_gap_never_filled_from_later_or_prior():
    bars=[{'ts_code':'600127.SH','trade_date':'20260910','close':14,'vol':1}]
    rows,gaps=m.history_basic_rows('600127.SH',bars,[{'Date':20260911,'Ltgb':10,'Zgb':10}])
    assert not rows and gaps[0]['trade_date']=='20260910'

@pytest.mark.parametrize('response',[
    [{'Date':20260911,'Ltgb':0,'Zgb':10}],
    [{'Date':20260911,'Ltgb':11,'Zgb':10}],
    [{'Date':20260911,'Ltgb':float('nan'),'Zgb':10}],
    [{'Date':20260911,'Ltgb':10,'Zgb':10}]*2,
    {},
])
def test_invalid_share_response(response):
    with pytest.raises(ValueError):m.history_basic_rows('600127.SH',[],response)

def test_more_info_only_same_date():
    more={'HqDate':'20260911','ZTPrice':'15.40','DTPrice':'12.60','FreeLtgb':'50318.42'}
    limits,free=m.dated_more_rows('600127.SH',more,'20260911',13.55)
    assert limits['up_limit']==15.4 and free['free_share']==50318.42
    with pytest.raises(ValueError,match='date_mismatch'):
        m.dated_more_rows('600127.SH',more,'20260910',14)

def test_batch_validation_before_tq():
    with pytest.raises(ValueError):m.capture_share_batch(['600127.SH']*101,'20260101','20260911','unused')

def fake_hub(monkeypatch,tq):
    from contextlib import nullcontext
    from types import SimpleNamespace
    hub=SimpleNamespace(TQLock=lambda **kw:nullcontext(),load_tq=lambda:(tq,None))
    spec=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module:None))
    monkeypatch.setattr(m.importlib.util,'spec_from_file_location',lambda *a:spec)
    monkeypatch.setattr(m.importlib.util,'module_from_spec',lambda *a:hub)

def test_documented_gpjy_request_has_integer_year_mmdd_and_no_guessed_fields(monkeypatch,tmp_path):
    from types import SimpleNamespace
    called={}
    def source(**kwargs):called.update(kwargs);return {'observed':'schema'}
    fake_hub(monkeypatch,SimpleNamespace(get_gpjy_value_by_date=source))
    result=m.capture_one('600127.SH','get_gpjy_value_by_date','20260101','20260911',tmp_path/'a.json')
    assert result['status']=='RECEIVED'
    assert called=={'stock_list':['600127.SH'],'field_list':[],'year':2026,'mmdd':911}

def test_dividend_probe_preserves_actions_without_treating_them_as_factors(monkeypatch,tmp_path):
    from types import SimpleNamespace
    import pandas as pd
    called={}
    def source(**kwargs):
        called.update(kwargs)
        return pd.DataFrame({'Type':[1],'Bonus':[2.5],'AllotPrice':[0],'ShareBonus':[0],'Allotment':[0]},index=pd.to_datetime(['2026-07-03']))
    fake_hub(monkeypatch,SimpleNamespace(get_divid_factors=source))
    result=m.capture_one('920071.BJ','get_divid_factors','20260101','20260911',tmp_path/'a.json')
    assert called=={'stock_code':'920071.BJ','start_time':'20260101','end_time':'20260911'}
    assert result['response']['columns']==['Type','Bonus','AllotPrice','ShareBonus','Allotment']
    assert result['response']['data'][0][1]==2.5
    assert 'not_price_adjustment_multiplier' in result['interpretation']
