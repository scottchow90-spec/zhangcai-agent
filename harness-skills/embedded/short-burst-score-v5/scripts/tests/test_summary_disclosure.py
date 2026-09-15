import pytest
from lhbpost.data.local_postmarket import summary_record

def source():
    return dict(SECURITY_CODE='688755',TRADE_DATE='2026-05-07 00:00:00',
        EXPLANATION='单只标的证券的当日融资买入数量达到当日该证券总交易量的50%以上',
        BILLBOARD_BUY_AMT=16675700,BILLBOARD_SELL_AMT=None,BILLBOARD_NET_AMT=16675700,
        TRADE_ID=100319459,CHANGE_TYPE='137003001')

def test_one_sided_financing_disclosure_keeps_unknown_counterparty():
    row=summary_record(source())
    assert row['l_sell'] is None and row['l_buy']==16675700
    assert not row['amount_disclosure_complete'] and row['missing_amount_fields']=='l_sell'
    assert row['source_event_id']=='100319459'

@pytest.mark.parametrize('value',[float('nan'),float('inf'),'bad'])
def test_null_support_does_not_accept_invalid_supplied_amount(value):
    row=source();row['BILLBOARD_BUY_AMT']=value
    with pytest.raises(ValueError):summary_record(row)

def test_zero_is_observed_zero_and_complete_is_explicit():
    row=source();row['BILLBOARD_SELL_AMT']=0
    result=summary_record(row)
    assert result['l_sell']==0 and result['amount_disclosure_complete']
