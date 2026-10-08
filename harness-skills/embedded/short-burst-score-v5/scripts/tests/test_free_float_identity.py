import pandas as pd
from lhbpost.features import build_stock_daily_features

def bars():
    return pd.DataFrame([dict(ts_code='600000.SH',trade_date=d,open=10,high=11,low=9,close=10,vol=100,amount=1000)
        for d in pd.bdate_range('2026-08-01',periods=25)])

def test_circulating_value_cannot_impute_unknown_free_float():
    daily=bars();basic=daily[['ts_code','trade_date']].copy()
    basic['circ_mv']=100000;basic['turnover_rate']=2
    result=build_stock_daily_features(daily,basic)
    assert result.effective_free_mcap.isna().all() and result.free_mcap_pctile.isna().all()
    assert result.circ_mv.eq(100000).all()

def test_observed_free_float_is_used_and_missing_days_stay_missing():
    daily=bars();basic=daily[['ts_code','trade_date']].copy()
    basic['circ_mv']=100000;basic['free_mv']=float('nan');basic.loc[basic.index[-1],'free_mv']=60000
    result=build_stock_daily_features(daily,basic)
    assert result.effective_free_mcap.iloc[:-1].isna().all()
    assert result.effective_free_mcap.iloc[-1]==60000
