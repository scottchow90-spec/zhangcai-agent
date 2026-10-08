import pytest
try:
    from lhbpost.data.cdr_factor_source import build_cdr_factors
except ImportError:
    from cdr_factor_source import build_cdr_factors

def action(day,cat=1,**kw):
    row={'code':'689009','market':1,'datetime':day,'category':cat,
         'hongli_panqianliutong':0,'peigujia_qianzongguben':0,'songgu_qianzongguben':0,'peigu_houzongguben':0}
    row.update(kw);return row
def bars():return [{'trade_date':'20260909','close':10},{'trade_date':'20260910','close':9}]
def run(records):return build_cdr_factors(records,bars(),['20260909','20260910'],'20260910')

def test_cash_action_is_real_factor_not_identity_fill():
    rows,proof=run([action('20260909',5),action('20260910',hongli_panqianliutong=10)])
    assert rows[0]['adj_factor']==1 and rows[1]['adj_factor']==pytest.approx(10/9)
    assert proof[0]['exright_reference']==9

def test_rights_payment_included_in_reference():
    rows,proof=run([action('20260909',5),action('20260910',peigu_houzongguben=10,peigujia_qianzongguben=4)])
    assert proof[0]['exright_reference']==7 and rows[1]['adj_factor']==pytest.approx(10/7)

def test_share_bonus_units_per_ten():
    rows,_=run([action('20260909',5),action('20260910',songgu_qianzongguben=10)])
    assert rows[-1]['adj_factor']==2

@pytest.mark.parametrize('records',[[],[action('20260909',5)],
    [action('20260910',hongli_panqianliutong=10)],
    [action('20260909',5),action('20260910',11)],
    [action('20260909',5),action('20260910',hongli_panqianliutong=float('nan'))],
    [action('20260909',5),action('20260910',hongli_panqianliutong=1000)]])
def test_incomplete_or_unsupported_evidence_rejected(records):
    with pytest.raises(ValueError):run(records)

def test_future_action_cannot_change_past_factor():
    base=[action('20260909',5),action('20260910',hongli_panqianliutong=10)]
    assert run(base)[0]==run(base+[action('20260911',hongli_panqianliutong=20)])[0]
