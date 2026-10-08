import pandas as pd
import pytest
from lhbpost.snapshot_pipeline import _compute_streaks
from lhbpost.candidate_pipeline import _event_core_rank,build_candidate_feature_table
from lhbpost.market_features import build_market_features
from lhbpost.data_audit import _audit_one_dated_file,_audit_daily_security_coverage
from lhbpost.data.normalized_store import NormalizedStore

def bars():
    return pd.DataFrame([{'ts_code':'000001.SZ','trade_date':'2026-09-10','close':11,'open':10,
                         'high':11,'low':10,'l1_code':'I','ma20':10,'ma60':10,'pct_chg':.1}])

@pytest.mark.parametrize('consumer',[_compute_streaks,_event_core_rank,build_market_features])
def test_all_limit_consumers_reject_missing_stock_day(consumer):
    missing=pd.DataFrame(columns=['ts_code','trade_date','up_limit','down_limit'])
    with pytest.raises(ValueError,match='coverage'):consumer(bars(),missing)

@pytest.mark.parametrize('no_limit,up,down,ok',[(True,None,None,True),(False,None,None,False),
    ('unknown',None,None,False),(True,11,9,False),(False,11,9,True),(None,None,None,False)])
def test_front_audit_unrestricted_is_explicit(tmp_path,no_limit,up,down,ok):
    path=tmp_path/'20260910.csv'
    pd.DataFrame([{'ts_code':'000001.SZ','trade_date':'20260910','up_limit':up,'down_limit':down,'no_limit':no_limit}]).to_csv(path,index=False)
    errors=[];_audit_one_dated_file(path,'stk_limit',errors,{})
    assert (not errors)==ok,errors

def test_store_preserves_unrestricted_metadata(tmp_path):
    (tmp_path/'stk_limit').mkdir()
    pd.DataFrame([{'ts_code':'000001.SZ','trade_date':'20260910','up_limit':None,'down_limit':None,
                   'no_limit':True,'rule_evidence':'synthetic_fixture'}]).to_csv(tmp_path/'stk_limit/20260910.csv',index=False)
    x=NormalizedStore(tmp_path).limits()
    assert x.no_limit.all() and x.rule_evidence.iloc[0]=='synthetic_fixture'

def write_coverage_fixture(root):
    base=pd.DataFrame({'ts_code':['000001.SZ','000002.SZ'],'trade_date':['20260910']*2,
                       'name':['甲','乙'],'is_st':[False,False],'is_delisting_arrangement':[False,False]})
    for table in ['daily','daily_basic','adj_factor','bak_basic','stk_limit','stock_st']:
        (root/table).mkdir();base.to_csv(root/table/'20260910.csv',index=False)
    return base

@pytest.mark.parametrize('table',['daily_basic','adj_factor','bak_basic','stk_limit'])
def test_one_stock_file_not_full_universe(tmp_path,table):
    base=write_coverage_fixture(tmp_path)
    base.iloc[:1].to_csv(tmp_path/table/'20260910.csv',index=False)
    errors=[];stats={};_audit_daily_security_coverage(tmp_path,{'20260910'},errors,stats)
    assert any(table in e and '000002.SZ' in e for e in errors)
    assert stats[table+'_missing_security_days']==1

def test_empty_sparse_st_not_all_normal(tmp_path):
    base=write_coverage_fixture(tmp_path)
    base.drop(columns='is_st').to_csv(tmp_path/'bak_basic/20260910.csv',index=False)
    base.iloc[:0][['ts_code','trade_date']].to_csv(tmp_path/'stock_st/20260910.csv',index=False)
    errors=[];_audit_daily_security_coverage(tmp_path,{'20260910'},errors,{})
    assert any('稀疏名单' in e for e in errors)

def test_full_explicit_security_rows_pass_coverage(tmp_path):
    write_coverage_fixture(tmp_path)
    errors=[];_audit_daily_security_coverage(tmp_path,{'20260910'},errors,{})
    assert not errors

def test_empty_sparse_with_complete_dated_explicit_history_is_proven(tmp_path):
    base=write_coverage_fixture(tmp_path)
    base.iloc[:0][['ts_code','trade_date']].to_csv(tmp_path/'stock_st/20260910.csv',index=False)
    errors=[];_audit_daily_security_coverage(tmp_path,{'20260910'},errors,{})
    assert not errors
