import pandas as pd
import pytest

from lhbpost.candidate_pipeline import build_candidate_feature_table
from lhbpost.snapshot_pipeline import build_snapshot


@pytest.fixture
def raw():
    dates = pd.bdate_range('2024-01-01', periods=140)
    rows = [(f'00000{j}.SZ', dt, 10+j+i*.02) for j in range(3) for i, dt in enumerate(dates)]
    daily = pd.DataFrame(rows, columns=['ts_code', 'trade_date', 'close'])
    for col, ratio in [('open', 1), ('high', 1.01), ('low', .99)]: daily[col] = daily.close*ratio
    daily['amount'] = 1e7; daily['vol'] = 1e6; daily['pct_chg'] = .001
    basic = daily[['ts_code', 'trade_date']].copy(); basic['turnover_rate'] = 5.; basic['free_mv'] = 1e8
    limits = daily[['ts_code', 'trade_date']].copy(); limits['up_limit'] = daily.close*1.1; limits['down_limit'] = daily.close*.9
    members = pd.DataFrame({'ts_code': [f'00000{j}.SZ' for j in range(3)], 'l1_code': ['I']*3, 'l1_name': ['行业']*3, 'in_date': ['2010-01-01']*3, 'out_date': [None]*3})
    sb = pd.DataFrame({'ts_code': members.ts_code, 'name': ['股']*3, 'list_date': ['2010-01-01']*3})
    top = pd.DataFrame({'ts_code': ['000000.SZ'], 'trade_date': [dates[-1]], 'l_buy': [5e6], 'l_sell': [1e6], 'reason': ['涨幅偏离']})
    inst = pd.DataFrame({'ts_code': ['000000.SZ'], 'trade_date': [dates[-1]], 'exalter': ['机构专用'], 'buy': [2e6], 'sell': [0.], 'net_buy': [2e6]})
    # Synthetic fixture explicitly declares same-day names and both risk flags.
    status=daily[['ts_code','trade_date']].copy();status['is_st']=False;status['is_delisting_arrangement']=False
    history=daily[['ts_code','trade_date']].merge(sb[['ts_code','name']],on='ts_code')
    return dict(historical_basic=history,daily=daily, daily_basic=basic, limits=limits, sw_members=members, stock_basic=sb, top_list=top, top_inst=inst, st_status=status)


def event(raw, **kw):
    day = raw['daily'].trade_date.max().strftime('%Y-%m-%d')
    return dict(ts_code='000000.SZ', trade_date=day, public_time=day+'T16:00:00+08:00', **kw)


def snapshot(raw, events, as_of=None):
    day = raw['daily'].trade_date.max().strftime('%Y-%m-%d')
    return build_snapshot(**raw, trade_date=day, as_of=as_of or day+'T21:00:00+08:00', event_features=events)


def test_event_string_false_does_not_turn_true(raw):
    ev = pd.DataFrame([event(raw, independent_catalyst='false', severe_negative_event='false', concept_denial='false', catalyst_quality=.9)])
    snap = snapshot(raw, ev)
    assert snap['stocks'][0]['independent_catalyst'] is False
    assert snap['stocks'][0]['post_close_events'][0]['risk_level'] == 'info'
    assert snap['stocks'][0]['post_close_events'][0]['concept_denial'] is False


def test_independent_quality_must_belong_to_same_event(raw):
    ev = pd.DataFrame([event(raw, independent_catalyst=True, catalyst_quality=.1), event(raw, independent_catalyst=False, catalyst_quality=.95)])
    table = build_candidate_feature_table(**raw, event_features=ev)
    assert table.iloc[0].catalyst_quality == .1


def test_missing_public_time_is_rejected(raw):
    ev = pd.DataFrame([event(raw, independent_catalyst=True)])
    ev['public_time'] = None
    with pytest.raises(ValueError): snapshot(raw, ev)


def test_event_after_asof_is_excluded(raw):
    ev = pd.DataFrame([event(raw, independent_catalyst=True, catalyst_quality=.9)])
    day = ev.iloc[0].trade_date
    ev['public_time'] = day+'T22:00:00+08:00'
    snap = snapshot(raw, ev)
    assert snap['stocks'][0]['post_close_events'] == []
    assert snap['stocks'][0]['independent_catalyst'] is False


def test_empty_unstructured_event_feed_does_not_claim_coverage(raw):
    # An arbitrary empty table is not evidence that the event source was queried.
    try:
        snap = snapshot(raw, pd.DataFrame())
    except ValueError:
        return
    assert snap['coverage']['event_feed'] is False


def test_naive_public_time_requires_explicit_timezone(raw):
    ev = pd.DataFrame([event(raw, independent_catalyst=True)])
    ev['public_time'] = ev.iloc[0].trade_date+' 16:00:00'
    with pytest.raises(ValueError): snapshot(raw, ev)


def test_asof_day_is_compared_in_shanghai_timezone(raw):
    day = raw['daily'].trade_date.max().strftime('%Y-%m-%d')
    with pytest.raises(ValueError):
        snapshot(raw, None, as_of=day+'T23:00:00-05:00')


def test_bad_event_trade_date_is_rejected_not_silently_dropped(raw):
    ev = pd.DataFrame([event(raw, independent_catalyst=True)])
    ev['trade_date'] = 'not-a-date'
    with pytest.raises(ValueError): snapshot(raw, ev)
