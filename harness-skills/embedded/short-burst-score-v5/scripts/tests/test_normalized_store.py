import pandas as pd
from lhbpost.data.normalized_store import NormalizedStore

def test_daily_basic_units_and_free_mv(tmp_path):
    (tmp_path/'daily_basic').mkdir()
    pd.DataFrame({'ts_code':['A'],'trade_date':['20250101'],'close':[10.0],'free_share':[100.0],'circ_mv':[2000.0]}).to_csv(tmp_path/'daily_basic'/'x.csv',index=False)
    b=NormalizedStore(tmp_path).daily_basic()
    assert b.iloc[0].free_share==1_000_000
    assert b.iloc[0].circ_mv==20_000_000
    assert b.iloc[0].free_mv==10_000_000
