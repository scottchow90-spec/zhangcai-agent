"""Synthetic offline data: verifies CLI wiring, never represents live market evidence."""
import json
import subprocess
import sys
from pathlib import Path
import pandas as pd
from test_event_audit import raw

def test_full_audit_prepare_analyze_cli(raw, tmp_path):
    data=tmp_path/'data'; data.mkdir()
    daily=raw['daily'].copy(); dates=sorted(daily.trade_date.unique())
    basic=raw['daily_basic'].copy()
    basic['close']=daily['close']; basic['free_share']=basic['free_mv']/basic['close']/10000
    daily['vol']/=100; daily['amount']/=1000; daily['pct_chg']*=100
    historical=daily[['ts_code','trade_date']].merge(raw['stock_basic'][['ts_code','name']],on='ts_code')
    factor=daily[['ts_code','trade_date']].copy(); factor['adj_factor']=1.
    tables={'daily':daily,'daily_basic':basic,'adj_factor':factor,'bak_basic':historical,
            'stock_st':raw['st_status'],'stk_limit':raw['limits'],'top_list':raw['top_list'],'top_inst':raw['top_inst']}
    for name,table in tables.items():
        (data/name).mkdir()
        for dt in dates:
            part=table[table.trade_date.eq(dt)].copy()
            part['trade_date']=pd.to_datetime(part['trade_date']).dt.strftime('%Y%m%d')
            part.to_csv(data/name/(pd.Timestamp(dt).strftime('%Y%m%d')+'.csv'),index=False)
    pd.DataFrame({'cal_date':[pd.Timestamp(d).strftime('%Y%m%d') for d in dates],'is_open':1}).to_csv(data/'trade_cal.csv',index=False)
    raw['sw_members'].to_csv(data/'sw_members.csv',index=False)
    raw['stock_basic'].to_csv(data/'stock_basic.csv',index=False)
    pd.DataFrame(columns=['ts_code','trade_date','public_time']).to_csv(data/'event_features.csv',index=False)
    (data/'index_daily').mkdir()
    pd.DataFrame({'ts_code':'000001.SH','trade_date':[pd.Timestamp(d).strftime('%Y%m%d') for d in dates],
                  'close':3000.,'pct_chg':.1}).to_csv(data/'index_daily/index.csv',index=False)
    root=Path(__file__).resolve().parents[2]; day=pd.Timestamp(dates[-1]).strftime('%Y-%m-%d')
    snapshot=tmp_path/'snapshot.json'; output=tmp_path/'result.json'
    def run(*args):
        result=subprocess.run([sys.executable,str(root/'scripts/workbuddy_entry.py'),*args],capture_output=True,text=True,encoding='utf-8')
        assert result.returncode==0,result.stdout+result.stderr
        return result
    run('prepare-snapshot','--data-root',str(data),'--trade-date',day,'--as-of',day+'T21:00:00+08:00','--output',str(snapshot))
    snap=json.loads(snapshot.read_text(encoding='utf-8'))
    assert snap['raw_data_audit']['passed'] is True and snap['pipeline']=='raw-postmarket-v5.0-audited'
    run('analyze','--input',str(snapshot),'--format','json','--output',str(output))
    result=json.loads(output.read_text(encoding='utf-8'))
    assert len(result['results'])==1
    assert result['history_model']['production_qualified'] is False
    assert result['results'][0]['conclusion']!='核心候选'
