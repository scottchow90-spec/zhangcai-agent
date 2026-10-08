import pandas as pd,numpy as np
from lhbpost.candidate_pipeline import build_candidate_feature_table

def test_pipeline_builds_without_future_industry():
    dates=pd.bdate_range('2024-01-01',periods=140)
    daily=[];basic=[];limits=[]
    for j in range(6):
        code=f'00000{j}.SZ'
        for i,dt in enumerate(dates):
            p=10+j+i*.02
            daily.append((code,dt,p,p*1.01,p*.99,p,1000000,1e7))
            basic.append((code,dt,5.0,1e8))
            limits.append((code,dt,p*1.1,p*.9))
    daily=pd.DataFrame(daily,columns=['ts_code','trade_date','open','high','low','close','vol','amount'])
    # normalized约定amount已经元，此处直接元
    basic=pd.DataFrame(basic,columns=['ts_code','trade_date','turnover_rate','free_mv'])
    limits=pd.DataFrame(limits,columns=['ts_code','trade_date','up_limit','down_limit'])
    dt=dates[-1]
    top=pd.DataFrame({'ts_code':['000000.SZ'],'trade_date':[dt],'l_buy':[5e6],'l_sell':[1e6],'reason':['涨幅偏离']})
    inst=pd.DataFrame({'ts_code':['000000.SZ'],'trade_date':[dt],'exalter':['机构专用'],'buy':[2e6],'sell':[0.0],'net_buy':[2e6]})
    members=pd.DataFrame({'ts_code':[f'00000{j}.SZ' for j in range(6)],'l1_code':['801010.SI']*6,'l1_name':['行业']*6,'in_date':['2010-01-01']*6,'out_date':[None]*6})
    sb=pd.DataFrame({'ts_code':[f'00000{j}.SZ' for j in range(6)],'name':['股']*6,'exchange':['SZSE']*6,'market':['主板']*6,'list_date':['2010-01-01']*6,'delist_date':[None]*6})
    sb['name_as_of']=dt
    st=daily[['ts_code','trade_date']].assign(is_st=False,is_delisting_arrangement=False)
    o=build_candidate_feature_table(daily=daily,daily_basic=basic,top_list=top,top_inst=inst,sw_members=members,stock_basic=sb,st_status=st,limits=limits)
    assert len(o)==1 and o.iloc[0].l1_code=='801010.SI' and o.iloc[0].sector_core_rank==1

def test_list_days_are_trading_sessions_not_calendar_days():
    dates=pd.bdate_range('2024-01-01',periods=30)
    daily=[];basic=[];limits=[]
    for j in range(3):
        code=f'00000{j}.SZ'
        for i,dt in enumerate(dates):
            p=10+j+i*.01
            daily.append((code,dt,p,p*1.01,p*.99,p,1e6,1e7))
            basic.append((code,dt,5.0,1e8))
            limits.append((code,dt,p*1.1,p*.9))
    daily=pd.DataFrame(daily,columns=['ts_code','trade_date','open','high','low','close','vol','amount'])
    basic=pd.DataFrame(basic,columns=['ts_code','trade_date','turnover_rate','free_mv'])
    limits=pd.DataFrame(limits,columns=['ts_code','trade_date','up_limit','down_limit'])
    dt=dates[19]
    top=pd.DataFrame({'ts_code':['000000.SZ'],'trade_date':[dt],'l_buy':[1e6],'l_sell':[1e5],'reason':['涨幅偏离']})
    inst=pd.DataFrame(columns=['ts_code','trade_date','exalter','buy','sell','net_buy'])
    members=pd.DataFrame({'ts_code':[f'00000{j}.SZ' for j in range(3)],'l1_code':['I']*3,'l1_name':['行业']*3,'in_date':['2020-01-01']*3,'out_date':[None]*3})
    sb=pd.DataFrame({'ts_code':[f'00000{j}.SZ' for j in range(3)],'name':['股']*3,'exchange':['SZSE']*3,'market':['主板']*3,'list_date':[dates[0].strftime('%Y-%m-%d')]*3,'delist_date':[None]*3})
    sb['name_as_of']=dt
    st=daily[['ts_code','trade_date']].assign(is_st=False,is_delisting_arrangement=False)
    o=build_candidate_feature_table(daily=daily,daily_basic=basic,top_list=top,top_inst=inst,sw_members=members,stock_basic=sb,st_status=st,limits=limits)
    assert int(o.iloc[0].list_days)==20
