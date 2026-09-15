import pandas as pd
import pytest
try:
    from lhbpost.data.sz_historical_names import parse_short_name_changes,name_as_of
except ImportError:
    from sz_historical_names import parse_short_name_changes,name_as_of


def fixture():
    return pd.DataFrame([{'证券代码':'000004','变更日期':'2025-01-01','变更前简称':'国华网安','变更后简称':'ST国华','证券简称':'当前任意名'},
        {'证券代码':'000004','变更日期':'2026-08-03','变更前简称':'ST国华','变更后简称':'*ST国华','证券简称':'当前任意名'}])


def test_current_name_not_backfilled_and_change_date_inclusive():
    result=parse_short_name_changes(fixture(),source_sha256='fixture')
    assert name_as_of(result['intervals'],'000004.SZ','2026-08-02')['name']=='ST国华'
    assert name_as_of(result['intervals'],'000004.SZ','2026-08-03')['name']=='*ST国华'
    assert name_as_of(result['intervals'],'000004.SZ','2024-12-31') is None
    assert not result['current_security_name_column_used']


def test_tab1_full_name_headers_not_accepted_as_short_names():
    frame=fixture().rename(columns={'变更前简称':'变更前全称','变更后简称':'变更后全称'})
    with pytest.raises(ValueError,match='header_not_unambiguously'):parse_short_name_changes(frame,source_sha256='fixture')


def test_current_security_name_alone_never_used():
    with pytest.raises(ValueError):parse_short_name_changes(fixture().drop(columns=['变更前简称','变更后简称']),source_sha256='fixture')


def test_incomplete_chain_cannot_extend_prior_name_through_gap():
    frame=fixture();frame.loc[1,'变更前简称']='另一个名字'
    with pytest.raises(ValueError,match='chain_gap'):parse_short_name_changes(frame,source_sha256='fixture')


def test_missing_old_name_not_string_nan():
    frame=fixture();frame.loc[0,'变更前简称']=None
    with pytest.raises(ValueError):parse_short_name_changes(frame,source_sha256='fixture')


def test_other_market_not_imputed():
    result=parse_short_name_changes(fixture(),source_sha256='fixture')
    assert name_as_of(result['intervals'],'600053.SH','2026-08-03') is None
