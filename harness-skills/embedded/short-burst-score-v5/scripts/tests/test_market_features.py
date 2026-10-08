import numpy as np,pandas as pd
from lhbpost.features import build_stock_daily_features
from lhbpost.market_features import build_market_features

def test_market_feature_no_future_mutation():
    dates=pd.bdate_range('2024-01-01',periods=150)
    rows=[]
    for j in range(30):
        for i,d in enumerate(dates):
            p=10+j*.1+i*.01
            rows.append((f'{j:06d}.SZ',d,p,p*1.01,p*.99,p,1e7+j*1e5,1e6))
    raw=pd.DataFrame(rows,columns=['ts_code','trade_date','open','high','low','close','amount','vol'])
    sf=build_stock_daily_features(raw)
    limits=raw[['ts_code','trade_date']].copy()
    limits['up_limit']=raw['close']*1.1
    limits['down_limit']=raw['close']*.9
    a=build_market_features(sf,limits)
    # 改最后一天，倒数第二天以前结果必须完全不变。
    raw2=raw.copy(); raw2.loc[raw2.trade_date==dates[-1],'close']*=2
    sf2=build_stock_daily_features(raw2); b=build_market_features(sf2,limits)
    cols=['breadth_pctile','sentiment_pctile','risk_pctile','market_state','market_permission']
    pd.testing.assert_frame_equal(a.iloc[:-1][cols].reset_index(drop=True),b.iloc[:-1][cols].reset_index(drop=True),check_dtype=False)
