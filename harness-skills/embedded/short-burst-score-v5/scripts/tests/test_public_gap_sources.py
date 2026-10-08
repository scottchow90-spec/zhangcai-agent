import copy
import pytest
try:
    from lhbpost.data.public_gap_sources import fetch_csi2000, fetch_candidate_announcements
except ImportError:
    from public_gap_sources import fetch_csi2000, fetch_candidate_announcements

class Response:
    def __init__(self, data): self.data=data
    def raise_for_status(self): pass
    def json(self): return self.data
class Session:
    def __init__(self, *data): self.data=iter(data)
    def get(self,*a,**kw): return Response(next(self.data))

def csi():
    return {'code':'200','success':True,'data':[{'indexCode':'932000','tradeDate':'20260910',
        'open':10,'high':12,'low':9,'close':11,'changePct':1.5,'tradingValue':3906.16,'tradingVol':14692255200}]}

def ann(time='2026-09-10 20:41:29:380', **kw):
    item={'art_code':'AN1','codes':[{'stock_code':'600519'}],'display_time':time,
          'notice_date':'2026-09-11 00:00:00','eiTime':'2026-09-11 09:00:00:000','title':'真实公告'}
    item.update(kw)
    return {'success':1,'data':{'total_hits':1,'list':[item]}}

def events(*data):
    return fetch_candidate_announcements(['600519.SH'],'2026-09-10','2026-09-10T21:00:00+08:00',session=Session(*data))

def test_csi_units_and_identity():
    x=fetch_csi2000('20260910','20260910',session=Session(csi()),expected_dates=['2026-09-10']).iloc[0]
    assert x.ts_code=='932000.CSI' and x.amount==390616000 and x.vol==146922552 and x.pct_chg==1.5

@pytest.mark.parametrize('field,value',[('indexCode','000852'),('tradeDate','20260911'),('close',float('nan')),('open',0),('high',8)])
def test_csi_bad_source_rejected(field,value):
    d=csi(); d['data'][0][field]=value
    with pytest.raises(ValueError): fetch_csi2000('20260910','20260910',session=Session(d))

def test_csi_missing_day_rejected():
    with pytest.raises(ValueError): fetch_csi2000('20260901','20260910',session=Session(csi()),expected_dates=['20260909','20260910'])

def test_csi_requests_real_calendar_boundary_not_holiday():
    class Capture(Session):
        def get(self,*a,**kw):
            assert kw['params']['startDate']=='20260910'
            assert kw['params']['endDate']=='20260910'
            return super().get(*a,**kw)
    frame=fetch_csi2000('20260901','20260911',session=Capture(csi()),expected_dates=['20260910'])
    assert frame.trade_date.tolist()==['20260910']

@pytest.mark.parametrize('dates',[[],['20260831'],['20260912']])
def test_csi_invalid_calendar_scope_rejected(dates):
    with pytest.raises(ValueError):
        fetch_csi2000('20260901','20260911',session=Session(csi()),expected_dates=dates)

def test_events_source_time_not_document_day_or_ingestion():
    frame,proof=events(ann())
    assert frame.iloc[0].public_time=='2026-09-10T20:41:29.380000+08:00'
    assert proof['all_public_events_complete'] is False
    assert frame.iloc[0].semantic_review_required

@pytest.mark.parametrize('time',['2026-09-10','',None,'bad'])
def test_no_time_guessing(time):
    with pytest.raises(ValueError): events(ann(time))

def test_wrong_candidate_rejected():
    with pytest.raises(ValueError): events(ann(codes=[{'stock_code':'000001'}]))

@pytest.mark.parametrize('time',['2026-09-10 21:01:00','2026-09-10 14:59:00','2026-09-09 20:00:00'])
def test_outside_window_excluded(time):
    assert events(ann(time))[0].empty

def test_empty_source_does_not_prove_no_events():
    f,p=events({'success':1,'data':{'total_hits':0,'list':[]}})
    assert f.empty and p['all_public_events_complete'] is False

def test_pagination_incomplete_rejected():
    d=ann();d['data']['total_hits']=2
    with pytest.raises(ValueError): events(d,{'success':1,'data':{'total_hits':2,'list':[]}})

def test_pagination_total_drift_rejected():
    d=ann();d['data']['total_hits']=2
    with pytest.raises(ValueError): events(d,{'success':1,'data':{'total_hits':3,'list':[]}})

def test_duplicate_source_identity_rejected():
    d=ann();d['data']['total_hits']=2
    with pytest.raises(ValueError): events(d,copy.deepcopy(d))
