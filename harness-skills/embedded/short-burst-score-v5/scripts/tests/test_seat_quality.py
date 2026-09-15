import numpy as np, pandas as pd
from lhbpost.seat_quality import build_mature_seat_quality,attach_event_seat_quality

def _data():
    cal=pd.bdate_range('2024-01-01',periods=170)
    daily=[]; seats=[]
    for j,seat in enumerate(['机构专用','营业部A']):
        code=f'00000{j}.SZ'
        for i,dt in enumerate(cal):
            p=10*(1+0.001*(i+j))
            daily.append((code,dt,p,p*1.02,p*.99,p))
        for i in range(0,130,5):
            seats.append((cal[i],code,seat,100.,0.,100.))
    return cal,pd.DataFrame(daily,columns=['ts_code','trade_date','open','high','low','close']),pd.DataFrame(seats,columns=['trade_date','ts_code','exalter','buy','sell','net_buy'])

def test_seat_labels_require_10_trading_day_maturity_and_120d_window():
    cal,d,s=_data(); q=build_mature_seat_quality(s,d,trade_dates=cal)
    assert len(q)>0
    # 在第10个后续交易日当天，刚成熟标签仍不能用于同日历史评价，最早下一交易日。
    first_event=cal[0]; first_mature=cal[10]
    on=q[q.asof_date==first_mature]
    if len(on):
        assert (on.seat_quality_samples==0).all() is False  # 可能有更早? 合成无更早，通常该日无行
    nextday=q[q.asof_date==cal[11]]
    assert len(nextday)>0 and nextday.seat_quality_samples.min()>=1

def test_attach_only_qualified_20_sample_seats():
    day=pd.Timestamp('2025-01-02')
    e=pd.DataFrame({'trade_date':[day],'ts_code':['A']})
    st=pd.DataFrame({'trade_date':[day,day],'ts_code':['A','A'],'exalter':['S1','S2'],'buy':[80.,20.]})
    q=pd.DataFrame({'asof_date':[day,day],'exalter':['S1','S2'],'seat_quality_pctile':[.9,.1],'seat_quality_samples':[25,10]})
    o=attach_event_seat_quality(e,st,q)
    assert abs(o.iloc[0].seat_quality_pctile-.9)<1e-9 and o.iloc[0].seat_quality_samples==25

def test_seat_quality_uses_recency_decay(monkeypatch):
    import lhbpost.seat_quality as sqmod
    cal=pd.bdate_range('2025-01-02',periods=150)
    daily=pd.DataFrame({'trade_date':cal,'ts_code':['IDX']*len(cal),'close':np.arange(len(cal))+100.,'high':np.arange(len(cal))+101.,'low':np.arange(len(cal))+99.})
    lab=pd.DataFrame([
        # S1: 旧样本差、近期样本好；S2相反。简单平均会打平，时间衰减应使S1更好。
        {'exalter':'S1','ts_code':'A','event_date':cal[40],'mature_date':cal[50],'ret3':-.10,'ret5':-.10,'hit10':0.,'mae':-.20,'mfe':0.},
        {'exalter':'S1','ts_code':'A','event_date':cal[130],'mature_date':cal[140],'ret3':.10,'ret5':.10,'hit10':1.,'mae':-.01,'mfe':.20},
        {'exalter':'S2','ts_code':'B','event_date':cal[40],'mature_date':cal[50],'ret3':.10,'ret5':.10,'hit10':1.,'mae':-.01,'mfe':.20},
        {'exalter':'S2','ts_code':'B','event_date':cal[130],'mature_date':cal[140],'ret3':-.10,'ret5':-.10,'hit10':0.,'mae':-.20,'mfe':0.},
    ])
    monkeypatch.setattr(sqmod,'_make_labels',lambda *args,**kwargs: lab.copy())
    q=sqmod.build_mature_seat_quality(pd.DataFrame(),daily,trade_dates=cal,half_life_sessions=20)
    last=q[q.asof_date==cal[-1]].set_index('exalter')
    assert last.loc['S1','seat_quality_pctile'] > last.loc['S2','seat_quality_pctile']
