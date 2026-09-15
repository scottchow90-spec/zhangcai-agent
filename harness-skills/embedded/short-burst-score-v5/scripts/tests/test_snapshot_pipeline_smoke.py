import pandas as pd
from lhbpost.snapshot_pipeline import build_snapshot
from lhbpost.core import analyze_snapshot


def test_physical_cut_removes_future_attached_disclosed_sides():
    from lhbpost.snapshot_pipeline import _cut
    for empty in (False,True):
        frame=pd.DataFrame(columns=['trade_date','ts_code']) if empty else pd.DataFrame([
            {'trade_date':'2026-09-11','ts_code':'600000.SH'},
            {'trade_date':'2026-09-12','ts_code':'600000.SH'}])
        frame.attrs['disclosed_sides']=[
            {'trade_date':'20260911','ts_code':'600000.SH','side':'buy','disclosed_amount':100},
            {'trade_date':pd.Timestamp('2026-09-12'),'ts_code':'600000.SH','side':'buy','disclosed_amount':999}]
        frame.attrs['acquisition_complete']=True
        result=_cut(frame,pd.Timestamp('2026-09-11'))
        assert len(result.attrs['disclosed_sides'])==1
        assert result.attrs['disclosed_sides'][0]['disclosed_amount']==100
        assert result.attrs['acquisition_complete'] is True
        assert len(frame.attrs['disclosed_sides'])==2
        assert empty or len(result)==1

def test_raw_postmarket_to_snapshot_to_analysis():
    dates=pd.bdate_range('2024-01-01',periods=140)
    daily=[];basic=[];limits=[];adj=[]
    for j in range(6):
        code=f'00000{j}.SZ'
        for i,dt in enumerate(dates):
            p=10+j+i*.02
            daily.append((code,dt,p,p*1.01,p*.99,p,1e6,1e7,0.001))
            basic.append((code,dt,5.0,1e8,5e7));limits.append((code,dt,p*1.1,p*.9));adj.append((code,dt,1.0))
    daily=pd.DataFrame(daily,columns=['ts_code','trade_date','open','high','low','close','vol','amount','pct_chg'])
    basic=pd.DataFrame(basic,columns=['ts_code','trade_date','turnover_rate','free_mv','free_share'])
    limits=pd.DataFrame(limits,columns=['ts_code','trade_date','up_limit','down_limit']);adj=pd.DataFrame(adj,columns=['ts_code','trade_date','adj_factor'])
    dt=dates[-1];prev=dates[-2]
    for d in [prev,dt]:
        m=(daily.ts_code=='000000.SZ')&(daily.trade_date==d);base=float(daily.loc[m,'close'].iloc[0]);up=base*1.1
        daily.loc[m,['close','high']]=up;limits.loc[(limits.ts_code=='000000.SZ')&(limits.trade_date==d),'up_limit']=up
    top=pd.DataFrame({'ts_code':['000000.SZ'],'trade_date':[dt],'l_buy':[5e6],'l_sell':[1e6],'reason':['涨幅偏离']})
    inst=pd.DataFrame({'ts_code':['000000.SZ'],'trade_date':[dt],'exalter':['机构专用'],'buy':[2e6],'sell':[0.0],'net_buy':[2e6],'reason':['涨幅偏离']})
    members=pd.DataFrame({'ts_code':[f'00000{j}.SZ' for j in range(6)],'l1_code':['801010.SI']*6,'l1_name':['行业']*6,'in_date':['2010-01-01']*6,'out_date':[None]*6})
    sb=pd.DataFrame({'ts_code':[f'00000{j}.SZ' for j in range(6)],'name':['股']*6,'exchange':['SZSE']*6,'market':['主板']*6,'list_date':['2010-01-01']*6,'delist_date':[None]*6})
    themes=pd.DataFrame({'ts_code':[f'00000{j}.SZ' for j in range(6)],'theme_code':['T001']*6,'theme_name':['题材甲']*6,'in_date':['2010-01-01']*6,'out_date':[None]*6})
    sb['name_as_of']=dt
    st=daily[['ts_code','trade_date']].assign(is_st=False,is_delisting_arrangement=False);ix=pd.DataFrame({'ts_code':['000001.SH']*140,'trade_date':dates,'close':[3000]*140,'pct_chg':[.001]*140})
    snap=build_snapshot(trade_date=dt.strftime('%Y-%m-%d'),as_of=dt.strftime('%Y-%m-%d')+'T21:00:00+08:00',daily=daily,daily_basic=basic,top_list=top,top_inst=inst,sw_members=members,stock_basic=sb,st_status=st,limits=limits,index_daily=ix,adj_factor=adj,theme_members=themes)
    assert len(snap['stocks'])==1 and snap['stocks'][0]['board_streak']==2
    assert snap['stocks'][0]['theme_verified'] is True and snap['stocks'][0]['theme_code']=='T001'
    out=analyze_snapshot(snap)
    assert out['results'][0]['stage']=='2板'
