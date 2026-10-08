"""The explicit user replacement must not mutate the original score formula."""
import copy
import pandas as pd
import pytest
from test_selected_candidates import inputs,td
from lhbpost import snapshot_pipeline as sp
from lhbpost.core import analyze_snapshot,load_config

def args(inputs):
    x={k:v.copy() for k,v in inputs.items()}
    date=pd.Timestamp(td(inputs))
    streak=sp._compute_streaks(x['daily'],x['limits'])
    streak=streak[streak.trade_date.eq(date)].copy()
    x['limits']=x['limits'][x['limits'].trade_date.eq(date)].copy()
    x['daily_basic']=x['daily_basic'][x['daily_basic'].trade_date.eq(date)].copy()
    return dict(**x,trade_date=td(inputs),as_of=td(inputs)+'T21:00:00+08:00',
        selected_codes=['000001.SZ'],current_streaks=streak,
        market_reference={'mode':'yearly-limit-close-premium'})

def test_explicit_reference_accepts_current_limits_without_historical_market_fabrication(inputs,monkeypatch):
    def forbidden(*a,**kw):raise AssertionError('Historical market path must not run in user replacement')
    monkeypatch.setattr(sp,'build_market_features',forbidden)
    got=sp.build_snapshot(**args(inputs))
    assert len(got['stocks'])==1
    s=got['stocks'][0]
    assert s['free_mcap_pctile']==pytest.approx(2/12)
    assert s['industry_metrics']['member_count']==6
    assert got['coverage']['current_position_universe'] is True
    assert got['coverage']['market_full_features'] is False
    assert 'causal_market' not in got['market']
    assert s['lhb']['listed'] is False

@pytest.mark.parametrize('mutation', ['missing_stock','height_conflict','wrong_rank','wrong_day','wrong_limit'])
def test_current_reference_corruption_rejected(inputs,mutation):
    a=args(inputs);x=a['current_streaks'].copy()
    if mutation=='missing_stock':x=x.iloc[1:]
    if mutation=='height_conflict':x.loc[x.index[0],'board_streak']=2
    if mutation=='wrong_rank':x.loc[x.index[0],'market_height_rank']=99
    if mutation=='wrong_day':x['trade_date']=x.trade_date+pd.Timedelta(days=1)
    if mutation=='wrong_limit':x.loc[x.index[0],'up_limit']=1
    a['current_streaks']=x
    with pytest.raises(ValueError,match='current_streaks'):sp.build_snapshot(**a)

def test_reference_statistics_cannot_change_any_original_score(inputs):
    cfg=load_config();before=copy.deepcopy(cfg)
    original=sp.build_snapshot(**args(inputs))
    # User reference values are external to the daily snapshot and not passed
    # as a qualified historical model. Reordering or changing that attachment
    # cannot affect any score or risk component.
    second=copy.deepcopy(original)
    second['market']['historical_reference_policy']['reference_note']='different display-only reference'
    first_result=analyze_snapshot(original,cfg)
    second_result=analyze_snapshot(second,cfg)
    assert first_result['results']==second_result['results']
    assert cfg==before
    assert '用户指定年度历史参考' in first_result['market_gate_method']

def test_reference_mode_needs_explicit_selection(inputs):
    a=args(inputs);a['selected_codes']=None
    with pytest.raises(ValueError,match='invalid_user_market_reference'):sp.build_snapshot(**a)

def test_reference_cannot_skip_actual_billboard_case(inputs):
    a=args(inputs);a['selected_codes']=['000009.SZ']
    with pytest.raises(ValueError,match='listed_candidate_requires_full'):sp.build_snapshot(**a)
