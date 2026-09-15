"""Portable regressions: ex-right reference prices are not prior raw closes."""
import pandas as pd
import pytest
from lhbpost.data.local_postmarket import LocalPostMarketAdapter
from lhbpost.features import build_stock_daily_features


def raw_day(day, close, **extra):
    return dict(date=day,open=close,high=close,low=close,close=close,
                volume=100,amount=1000,**extra)


@pytest.mark.parametrize('field',['preclose','pre_close'])
def test_tongda_exright_uses_actual_1173_reference(field):
    rows=[raw_day('20260512',16.50),raw_day('20260513',12.90,**{field:11.73})]
    got=LocalPostMarketAdapter._bars(rows,'sz002560','20260513','20260513')[0]
    assert got['pre_close']==11.73
    assert got['pct_chg']==pytest.approx((12.90/11.73-1)*100)
    assert got['pct_chg']>9.9
    assert got['previous_close_raw']==16.50


@pytest.mark.parametrize('extra',[{}, {'preclose':None}, {'pre_close':float('nan')}, {'preclose':''}])
def test_missing_reference_never_invents_return_from_prior_raw_close(extra):
    rows=[raw_day('20260512',16.50),raw_day('20260513',12.90,**extra)]
    got=LocalPostMarketAdapter._bars(rows,'sz002560','20260513','20260513')[0]
    assert 'pre_close' not in got and 'pct_chg' not in got
    assert got['previous_close_raw']==16.50


@pytest.mark.parametrize('value',[0,-1,float('inf'),'bad'])
def test_supplied_invalid_reference_is_rejected(value):
    with pytest.raises(ValueError):
        LocalPostMarketAdapter._bars([raw_day('20260513',12.90,preclose=value)],'sz002560','20260513','20260513')


def test_conflicting_reference_aliases_are_rejected():
    with pytest.raises(ValueError,match='conflicting'):
        LocalPostMarketAdapter._bars([raw_day('20260513',12.90,preclose=11.73,pre_close=16.50)],'sz002560','20260513','20260513')


def feature_inputs(pct=True):
    frame=pd.DataFrame([dict(ts_code='002560.SZ',trade_date=day,open=close,high=close,low=close,close=close,amount=1000,vol=100)
                        for day,close in [('2026-05-12',16.50),('2026-05-13',12.90),('2026-05-14',13.00)]])
    if pct:frame['pct_chg']=[.02,float('nan'),.007]
    adjustment=pd.DataFrame({'ts_code':['002560.SZ']*3,'trade_date':frame.trade_date,
                             'adj_factor':[1.0,16.50/11.73,16.50/11.73]})
    return frame,adjustment


def test_mixed_observed_and_missing_return_fills_only_adjusted_continuity():
    frame,adj=feature_inputs()
    got=build_stock_daily_features(frame,adj_factor=adj)
    assert got.iloc[0].pct_chg==.02 and got.iloc[2].pct_chg==.007
    assert got.iloc[1].pct_chg==pytest.approx(12.90/11.73-1)
    assert frame.iloc[1].pct_chg!=frame.iloc[1].pct_chg


@pytest.mark.parametrize('pct',[True,False])
def test_missing_adjustment_never_falls_back_to_unadjusted_drop(pct):
    frame,_=feature_inputs(pct)
    got=build_stock_daily_features(frame)
    assert pd.isna(got.iloc[1].pct_chg)
    if pct:assert got.iloc[0].pct_chg==.02 and got.iloc[2].pct_chg==.007


@pytest.mark.parametrize('missing_index',[0,1])
def test_missing_either_adjustment_endpoint_keeps_return_unknown(missing_index):
    frame,adj=feature_inputs()
    adj=adj.drop(index=missing_index)
    got=build_stock_daily_features(frame,adj_factor=adj)
    assert pd.isna(got.iloc[1].pct_chg)


def test_all_missing_returns_can_use_observed_adjustment_series():
    frame,adj=feature_inputs(False)
    got=build_stock_daily_features(frame,adj_factor=adj)
    assert pd.isna(got.iloc[0].pct_chg)
    assert got.iloc[1].pct_chg==pytest.approx(12.90/11.73-1)
    assert got.iloc[2].pct_chg==pytest.approx(13.00/12.90-1)
