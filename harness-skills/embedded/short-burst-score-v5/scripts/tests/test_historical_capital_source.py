import pytest
try:
    from lhbpost.data.historical_capital_source import capital_history,native_shares
except ImportError:
    from historical_capital_source import capital_history,native_shares

def state(date,bf=100,bt=200,af=100,at=200,cat=5):
    return {'code':'000001','market':0,'datetime':date,'category':cat,
        'hongli_panqianliutong':bf,'peigujia_qianzongguben':bt,
        'songgu_qianzongguben':af,'peigu_houzongguben':at}

def run(records,dates=('20260629','20260630','20260701')):
    return capital_history('000001.SZ',records,dates,'20260701')

def test_event_date_uses_after_state_not_before_or_future():
    rows,proof=run([state('20260101'),state('20260630',af=120,at=250)])
    assert [r['Ltgb'] for r in rows]==[1000000,1200000,1200000]
    assert [r['Zgb'] for r in rows]==[2000000,2500000,2500000]
    assert proof['first_baseline_date']=='20260101'

@pytest.mark.parametrize('records',[[],[state('20260630')]])
def test_future_state_cannot_fill_missing_baseline(records):
    with pytest.raises(ValueError,match='baseline'):run(records)

def test_conflicting_states_and_chain_rejected():
    with pytest.raises(ValueError,match='ambiguous'):run([state('20260101'),state('20260101',af=120)])
    with pytest.raises(ValueError,match='discontinuity'):run([state('20260101'),state('20260630',bf=110)])

def test_share_bonus_without_explicit_state_rejected():
    with pytest.raises(ValueError,match='without_effective'):run([state('20260101'),state('20260630',cat=1,af=10,at=0)])

def test_cash_dividend_not_mistaken_for_shares():
    rows,_=run([state('20260101'),state('20260630',cat=1,bf=10,bt=0,af=0,at=0)])
    assert all(r['Ltgb']==1000000 for r in rows)

def test_wrong_market_rejected():
    s=state('20260101');s['market']=1
    with pytest.raises(ValueError,match='identity'):run([s])

def test_future_event_cannot_change_existing_history():
    assert run([state('20260101')])[0]==run([state('20260101'),state('20260702',af=500,at=600)])[0]

def test_older_prelisting_zero_record_does_not_replace_valid_dated_baseline():
    rows,_=run([state('20200101',bf=0,bt=0,af=0,at=0),state('20260101')])
    assert rows[0]['Ltgb']==1000000

@pytest.mark.parametrize('values,native',[
    ([1940560.125,1940591.875,1940568.5,1940591.875],[19405600768,19405918208,19405684736,19405918208]),
    ([971693.5625,1193071.0,971511.3125,1193071.0],[9716935680,11930710016,9715112960,11930710016]),
    ([134998.484375,134999.5,134999.5,134999.5],[1349984896,1349995008,1349995008,1349995008])])
def test_three_real_tq_change_date_crosschecks_exact(values,native):
    # Existing successful TQ cache: 000001/000002/000006, 2026-06-29 and 06-30.
    assert [native_shares(x) for x in values]==native
