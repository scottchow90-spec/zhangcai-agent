from pathlib import Path
from datetime import datetime,timedelta
import importlib.util
import hashlib
import pytest

source=Path(__file__).with_name('local_limit_state.py')
if not source.exists():source=Path(__file__).parents[1]/'lhbpost/data/local_limit_state.py'
spec=importlib.util.spec_from_file_location('limit_state',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

@pytest.fixture
def evidence(tmp_path,monkeypatch):
    raw=b'unit test only official rule fixture';sha=hashlib.sha256(raw).hexdigest()
    path=tmp_path/'rule.doc';path.write_bytes(raw)
    for exchange in ('SH','SZ'):
        monkeypatch.setitem(m.RULES,exchange,{**m.RULES[exchange],'sha256':sha})
    return {key:{**value,'path':str(path)} for key,value in m.RULES.items()}

def calendar(start='20260901',end='20260930'):
    current=datetime.strptime(start,'%Y%m%d');finish=datetime.strptime(end,'%Y%m%d');rows=[]
    while current<=finish:
        rows.append({'cal_date':current.strftime('%Y%m%d'),'is_open':int(current.weekday()<5)})
        current+=timedelta(days=1)
    return rows

def resolve(evidence,code='301689.SZ',listed='20260910',target='20260911',more=None,cal=None):
    return m.resolve_current_limit_state(code,more or {'HqDate':target,'ZTPrice':'0.00','DTPrice':'0.00','IsZCZGP':'1'},
        target,{'ts_code':code,'list_date':listed},calendar() if cal is None else cal,evidence.get(code.rsplit('.',1)[1]))

@pytest.mark.parametrize('code,listed,ordinal',[
    ('301689.SZ','20260910',2),('301699.SZ','20260909',3),
    ('603448.SH','20260907',5),('688801.SH','20260911',1)])
def test_four_observed_ipo_positions(evidence,code,listed,ordinal):
    row=resolve(evidence,code,listed)
    assert row['no_limit']==1 and row['listing_session_no']==ordinal
    assert row['up_limit'] is None and row['down_limit'] is None
    assert row['source_up_limit']==0 and row['source_down_limit']==0
    assert row['rule_sha256']==evidence[code.rsplit('.',1)[1]]['sha256']

@pytest.mark.parametrize('field,value', [('url','https://evil.example/rule.pdf'),('sha256','0'*64),
    ('id','self_declared'),('effective_from','20200101'),('notice_url','https://evil.example/notice')])
def test_exact_rule_identity_required(evidence,field,value):
    evidence['SZ'][field]=value
    with pytest.raises(ValueError,match='identity_mismatch'):resolve(evidence)

def test_tampered_original_rejected(evidence):
    Path(evidence['SZ']['path']).write_bytes(b'tampered')
    with pytest.raises(ValueError,match='hash_mismatch'):resolve(evidence)

def test_missing_rule_not_zero_means_unlimited(evidence):
    with pytest.raises(ValueError,match='evidence_missing'):resolve({})

def test_missing_calendar_day_even_closed_day_rejected(evidence):
    cal=[r for r in calendar() if r['cal_date']!='20260906']
    with pytest.raises(ValueError,match='incomplete_calendar'):resolve(evidence,listed='20260904',cal=cal)

def test_sixth_session_rejected(evidence):
    with pytest.raises(ValueError,match='outside_ipo'):resolve(evidence,listed='20260904')

@pytest.mark.parametrize('more',[
    {'HqDate':'20260911','ZTPrice':0,'DTPrice':9,'IsZCZGP':'1'},
    {'HqDate':'20260911','ZTPrice':float('nan'),'DTPrice':0,'IsZCZGP':'1'},
    {'HqDate':'20260911','ZTPrice':-1,'DTPrice':0,'IsZCZGP':'1'},
    {'HqDate':'20260910','ZTPrice':0,'DTPrice':0,'IsZCZGP':'1'},
    {'HqDate':'20260911','ZTPrice':0,'DTPrice':0,'IsZCZGP':'0'},
    {'HqDate':'20260911','ZTPrice':0,'DTPrice':0},
])
def test_bad_or_unproved_quotes_rejected(evidence,more):
    with pytest.raises(ValueError):resolve(evidence,more=more)

def test_bj_not_mistaken_for_shsz_ipo(evidence):
    with pytest.raises(ValueError,match='unsupported_no_limit_exchange'):resolve(evidence,code='920071.BJ',listed='20260911')

def test_positive_price_contradiction(evidence):
    with pytest.raises(ValueError,match='positive_limits_conflict'):
        resolve(evidence,more={'HqDate':'20260911','ZTPrice':11,'DTPrice':9,'IsZCZGP':'1'})

def test_holiday_not_counted_as_trading_day(evidence):
    cal=calendar();next(r for r in cal if r['cal_date']=='20260908')['is_open']=0
    assert resolve(evidence,listed='20260904',cal=cal)['listing_session_no']==5

def test_effective_date_not_backfilled(evidence):
    with pytest.raises(ValueError,match='effective_interval'):
        resolve(evidence,listed='20260703',target='20260706',cal=calendar('20260703','20260706'))

def test_old_stock_actual_positive_limits_remain_limited(evidence):
    row=resolve(evidence,listed='20000101',more={'HqDate':'20260911','ZTPrice':11,'DTPrice':9,'IsZCZGP':'1'})
    assert row['no_limit']==0

def test_packaged_rule_path_uses_original_skill_root(evidence,tmp_path):
    path=tmp_path/'references'/'rules';path.mkdir(parents=True)
    (path/m.RULE_FILES['SH']).write_bytes(Path(evidence['SH']['path']).read_bytes())
    resolved=m.packaged_rule_evidence('SH',tmp_path)
    assert Path(resolved['path'])==path/'sse-trading-rules-2026.docx'
