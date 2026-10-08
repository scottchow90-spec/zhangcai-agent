from pathlib import Path
from datetime import date,timedelta
import json
import pytest
from lhbpost.limit_followthrough_reference import build_reference,write_reference,RULE_HASHES

CODE='600088.SH'
RULES={k:{'sha256':v} for k,v in RULE_HASHES.items()}
def row(d,c,h=None,o=None,pre='10',st='0',status='1'):
    return {'date':d,'code':'sh.600088','open':o or c,'close':c,'high':h or c,'low':min(float(c),float(o or c)), 'preclose':pre,'isST':st,'tradestatus':status}
def run(rows,start='2026-09-09',end='2026-09-11'):
    a=date.fromisoformat(start);b=date.fromisoformat(end)
    cal=[{'calendar_date':str(a+timedelta(days=i)),'is_trading_day':'1' if (a+timedelta(days=i)).weekday()<5 else '0'} for i in range((b-a).days+1)]
    return build_reference(codes=[CODE],start=start,end=end,histories={CODE:rows},calendar_rows=cal,
        basics={CODE:{'ipoDate':'1997-06-16','outDate':''}},rules=RULES)

def test_close_is_primary_and_flat_not_premium():
    s,l=run([row('2026-09-09','11'),row('2026-09-10','11',h='12',pre='11'),row('2026-09-11','12.1',pre='11')])
    e=l['events'][0];assert e['next_close_premium'] is False and e['next_high_premium'] is True
    x=s['stocks'][0];assert x['limit_up_count']==2 and x['pending_next_session_count']==1
    assert x['observed_next_session_count']==1 and x['next_close_premium_count']==0

def test_touch_without_close_does_not_count():
    s,l=run([row('2026-09-09','10.9',h='11'),row('2026-09-10','10.9',pre='10.9'),row('2026-09-11','10.9',pre='10.9')])
    assert s['stocks'][0]['limit_up_count']==0 and l['events']==[]

def test_suspension_does_not_skip_to_resume():
    s,l=run([row('2026-09-09','11'),row('2026-09-10','11',pre='11',status='0'),row('2026-09-11','12',pre='11')])
    e=l['events'][0];assert e['outcome']=='NEXT_SESSION_SUSPENDED' and e['next_close_premium'] is None
    assert s['stocks'][0]['observed_next_session_count']==0 and s['stocks'][0]['settled_event_count']==1

def test_market_calendar_weekend_exact_next():
    s,l=run([row('2026-09-04','11'),row('2026-09-07','11.2',pre='11')],start='2026-09-04',end='2026-09-07')
    assert l['events'][0]['next_market_session']=='2026-09-07'
    assert s['stocks'][0]['next_close_premium_count']==1

def test_dated_st_rules_switch_on_effective_day():
    s,l=run([row('2026-07-03','10.5',st='1'),row('2026-07-06','11.55',pre='10.5',st='1')],start='2026-07-03',end='2026-07-06')
    assert [e['limit_basis']['rate'] for e in l['events']]==[.05,.1]

def test_half_up_not_bankers_round():
    s,l=run([row('2026-09-09','9.74',pre='8.85'),row('2026-09-10','9.8',pre='9.74'),row('2026-09-11','9.8',pre='9.8')])
    assert l['events'][0]['limit_price']==9.74

def test_future_rows_physically_ignored():
    data=[row('2026-09-09','10'),row('2026-09-10','10'),row('2026-09-11','11'),row('2026-09-14','12.1',pre='11')]
    s,l=run(data);assert l['events'][0]['outcome']=='PENDING_NEXT_MARKET_SESSION'
    assert s['future_outcomes_beyond_cutoff_used'] is False

def test_missing_date_is_not_fake_suspension():
    with pytest.raises(ValueError,match='full_year_daily_status_missing'):run([row('2026-09-09','11'),row('2026-09-11','12',pre='11')])

def test_price_outside_rule_requires_explicit_exception():
    with pytest.raises(ValueError,match='price_limit_exception'):run([row('2026-09-09','12'),row('2026-09-10','12',pre='12'),row('2026-09-11','12',pre='12')])

def test_labels_are_not_in_snapshot_input(tmp_path):
    s,l=run([row('2026-09-09','11'),row('2026-09-10','11.2',pre='11'),row('2026-09-11','11.2',pre='11.2')])
    artifacts=write_reference(s,l,tmp_path)
    q=json.loads(Path(artifacts['aggregate_path']).read_text(encoding='utf-8'))
    assert 'events' not in q and 'next_close' not in q and q['production_qualified'] is False
