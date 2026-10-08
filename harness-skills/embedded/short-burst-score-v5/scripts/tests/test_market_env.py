from lhbpost.market_env import classify_market

def test_bull():
    r=classify_market(dict(breadth_pctile=.9,sentiment_pctile=.85,trend_pctile=.8,liquidity_pctile=.7,smallcap_relative_pctile=.8,risk_pctile=.1,divergence_pctile=.1,improvement=.2))
    assert r.permission=='正常' and r.state in ('全面主升','结构性主升')

def test_panic():
    r=classify_market(dict(breadth_pctile=.08,sentiment_pctile=.1,trend_pctile=.1,liquidity_pctile=.2,smallcap_relative_pctile=.1,risk_pctile=.95,divergence_pctile=.9,improvement=-.8))
    assert r.state=='恐慌' and r.permission=='暂停'

def test_missing_blocks():
    assert classify_market({}).permission=='暂停'
