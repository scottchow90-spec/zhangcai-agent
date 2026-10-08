import json
import pandas as pd
import pytest
from lhbpost.data import public_gap_sources as sources
from lhbpost.data import sz_historical_names
from lhbpost.data.public_supplementary import acquire_public_supplementary


@pytest.fixture(autouse=True)
def isolate_name_source(monkeypatch):
    monkeypatch.setattr(sz_historical_names,'acquire_sz_historical_names',
        lambda *a,**k:{'status':'ACQUIRED_DATED_SHORT_NAME_CHANGES','test_fixture':True})


class Adapter:
    def __init__(self, out):
        self.out=out
        self.manifest={'tables':{},'failures':[
            {'source':'sh932000','error':'no_index_bars_in_requested_range'},
            {'source':'unrelated','error':'preserve'}]}
    def _save(self, table, rows):
        x=pd.DataFrame(rows)
        for day, group in x.groupby('trade_date'):
            path=self.out/table/f'{day}.csv';path.parent.mkdir(parents=True,exist_ok=True)
            group.to_csv(path,index=False)
        self.manifest['tables'][table]={'rows':len(rows)}
    def _json(self, name, obj):
        p=self.out/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(obj),encoding='utf-8')


def test_index_merge_preserves_seven_and_unrelated_failures(tmp_path, monkeypatch):
    a=Adapter(tmp_path)
    pd.DataFrame([{'cal_date':'20260911','is_open':1}]).to_csv(tmp_path/'trade_cal.csv',index=False)
    originals=[{'ts_code':f'{i:06d}.SH','trade_date':'20260911','close':10} for i in range(7)]
    a._save('index_daily',originals)
    monkeypatch.setattr(sources,'fetch_csi2000',lambda *a,**k:pd.DataFrame([
        {'ts_code':'932000.CSI','trade_date':'20260911','close':20}]))
    acquire_public_supplementary(a,'20260911','20260911')
    merged=pd.read_csv(tmp_path/'index_daily/20260911.csv')
    assert len(merged)==8 and set(merged.ts_code)=={r['ts_code'] for r in originals}|{'932000.CSI'}
    assert not any(r['source']=='sh932000' for r in a.manifest['failures'])
    assert any(r['source']=='unrelated' for r in a.manifest['failures'])
    assert 'event_features.csv' not in a.manifest['tables']


def test_failed_source_cannot_remove_missing_index_evidence(tmp_path, monkeypatch):
    a=Adapter(tmp_path)
    acquire_public_supplementary(a,'20260911','20260911')
    assert any(r['source']=='sh932000' for r in a.manifest['failures'])
    assert 'index_daily' not in a.manifest['tables']
