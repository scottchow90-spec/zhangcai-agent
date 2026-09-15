import pandas as pd, numpy as np
from lhbpost.features import build_stock_daily_features,map_industry_point_in_time,aggregate_lhb

def test_point_in_time_industry():
    s=pd.DataFrame({'ts_code':['A','A'],'trade_date':['2020-01-01','2022-01-01']})
    m=pd.DataFrame({'ts_code':['A','A'],'l1_code':['OLD','NEW'],'l1_name':['旧','新'],'in_date':['2010-01-01','2021-01-01'],'out_date':['2020-12-31',None]})
    o=map_industry_point_in_time(s,m).sort_values('trade_date'); assert o.iloc[0].l1_code=='OLD' and o.iloc[1].l1_code=='NEW'

def test_lhb_merge_same_reason_duplicates():
    tl=pd.DataFrame({'trade_date':['2025-01-01']*2,'ts_code':['A']*2,'l_buy':[100.,100.],'l_sell':[50.,50.],'reason':['x','y']})
    ti=pd.DataFrame(columns=['trade_date','ts_code','exalter','buy','sell','net_buy'])
    d=pd.DataFrame({'trade_date':['2025-01-01'],'ts_code':['A'],'amount':[1000.]})
    o=aggregate_lhb(tl,ti,d); assert o.iloc[0].lhb_buy==100 and o.iloc[0].lhb_net_buy==50

from lhbpost.features import assign_lifecycle

def test_lhb_multiple_reasons_uses_most_comprehensive_not_sum():
    tl=pd.DataFrame({'trade_date':['2025-01-01']*2,'ts_code':['A']*2,'l_buy':[100.,180.],'l_sell':[50.,80.],'l_amount':[150.,260.],'reason':['x','y']})
    ti=pd.DataFrame(columns=['trade_date','ts_code','exalter','buy','sell','net_buy'])
    d=pd.DataFrame({'trade_date':['2025-01-01'],'ts_code':['A'],'amount':[1000.]})
    o=aggregate_lhb(tl,ti,d)
    assert o.iloc[0].lhb_buy==180 and o.iloc[0].lhb_sell==80 and o.iloc[0].lhb_net_buy==100

def test_lifecycle_exact_three_trading_days():
    cal=pd.bdate_range('2025-01-01',periods=10)
    e=pd.DataFrame({'trade_date':[cal[0],cal[3],cal[4],cal[8]],'ts_code':['A']*4,'lhb_net_buy_ratio':[.01,.02,.015,.03]})
    o=assign_lifecycle(e,trade_dates=cal).sort_values('trade_date')
    assert o['lifecycle_event_no'].tolist()==[1,2,2,1]
    assert o['lifecycle_net_improving'].tolist()==[False,True,False,False]

def test_atr14_is_causal():
    dates=pd.bdate_range('2025-01-01',periods=20)
    d=pd.DataFrame({'ts_code':['A']*20,'trade_date':dates,'open':[10]*20,'high':[11]*20,'low':[9]*20,'close':[10]*20,'amount':[1e6]*20,'vol':[1e5]*20})
    a=build_stock_daily_features(d)
    assert abs(a.iloc[13].atr14-2.0)<1e-12

def test_top_inst_same_seat_on_both_sides_not_double_counted():
    tl=pd.DataFrame({'trade_date':['2025-01-01'],'ts_code':['A'],'l_buy':[100.],'l_sell':[50.]})
    ti=pd.DataFrame({'trade_date':['2025-01-01']*2,'ts_code':['A']*2,'exalter':['机构专用']*2,'side':['0','1'],'buy':[20.,20.],'sell':[5.,5.],'net_buy':[15.,15.]})
    d=pd.DataFrame({'trade_date':['2025-01-01'],'ts_code':['A'],'amount':[1000.]})
    o=aggregate_lhb(tl,ti,d)
    assert o.iloc[0].inst_net==15 and o.iloc[0].seat_buy==20
