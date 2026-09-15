from pathlib import Path
from types import SimpleNamespace
import json,math,re,urllib.parse
import pytest
from lhbpost.data.public_window_acquisition import acquire_windows


class Adapter:
    def __init__(self,out,max_pages=2):self.out=out;self.max_pages=max_pages;out.mkdir()
    def _json(self,relative,value):
        path=self.out/relative;path.parent.mkdir(exist_ok=True,parents=True);path.write_text(json.dumps(value),encoding='utf-8')


class Server:
    def __init__(self,mode='normal'):self.calls=[];self.mode=mode
    def summary_url(self,date):return 'https://example.test/?pageSize=5000'
    def fetch_json(self,url,retries):
        q=dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query));self.calls.append(q)
        lo,hi=re.findall(r"'(\d{4}-\d{2}-\d{2})'",q['filter']);page=int(q['pageNumber'])
        rows=[{'TRADE_DATE':f'2026-09-{d:02d}','SECURITY_CODE':'600000','anonymous_occurrence':i}
            for d in range(7,12) if lo<=f'2026-09-{d:02d}'<=hi for i in range(500)]
        data=rows[(page-1)*500:page*500]
        if self.mode=='repeat' and page>1:data=rows[:500]
        count=len(rows)+(1 if self.mode=='bad_count' else 0)
        return {'success':True,'result':{'count':count,'pages':math.ceil(len(rows)/500),'data':data}}


def test_server_500_cap_splits_dates_and_preserves_all_rows(tmp_path):
    server=Server();adapter=Adapter(tmp_path/'run')
    rows=acquire_windows(adapter,server,'RPT_TEST','20260907','20260911',math.inf,tmp_path/'cache')
    assert len(rows)==2500
    assert len({(r['TRADE_DATE'],r['anonymous_occurrence']) for r in rows})==2500
    assert all(q['pageSize']=='5000' for q in server.calls)
    assert all(r['_source_page']<=2 for r in rows)
    assert len(list((tmp_path/'cache').glob('*.json')))==3
    files=list((adapter.out/'source_evidence').glob('*.json'))
    assert len(files)>3 and any('20260907-20260909' in p.name for p in files)


def test_completed_subwindows_reused_with_hash_validation(tmp_path):
    server=Server();adapter=Adapter(tmp_path/'first')
    acquire_windows(adapter,server,'RPT_TEST','20260907','20260911',math.inf,tmp_path/'cache')
    server.calls=[]
    rows=acquire_windows(Adapter(tmp_path/'second'),server,'RPT_TEST','20260907','20260911',math.inf,tmp_path/'cache')
    assert len(rows)==2500 and len(server.calls)==2  # only oversized parent headers rechecked
    p=next((tmp_path/'cache').glob('*.json'));record=json.loads(p.read_text());record['entries_sha256']='bad';p.write_text(json.dumps(record))
    server.calls=[]
    assert len(acquire_windows(Adapter(tmp_path/'third'),server,'RPT_TEST','20260907','20260911',math.inf,tmp_path/'cache'))==2500
    assert len(server.calls)>2


def test_duplicate_page_not_hidden_by_deduplication(tmp_path):
    adapter=Adapter(tmp_path/'run');server=Server('repeat')
    with pytest.raises(ValueError,match='duplicate_page'):
        acquire_windows(adapter,server,'RPT_TEST','20260907','20260908',math.inf,tmp_path/'cache')
    assert not list((tmp_path/'cache').glob('*.json'))
    assert len(list((adapter.out/'source_evidence').glob('*.json')))>=2


def test_wrong_count_rejected_without_cache_publication(tmp_path):
    with pytest.raises(ValueError,match='total_count_mismatch'):
        acquire_windows(Adapter(tmp_path/'run'),Server('bad_count'),'RPT_TEST','20260907','20260908',math.inf,tmp_path/'cache')
    assert not list((tmp_path/'cache').glob('*.json'))


def test_failed_later_partition_retains_completed_window_for_resume(tmp_path):
    server=Server();original=server.fetch_json
    def fail_later(url,retries):
        q=dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        if "TRADE_DATE>='2026-09-10'" in q['filter']:raise TimeoutError('specific later window unavailable')
        return original(url,retries)
    server.fetch_json=fail_later
    with pytest.raises(TimeoutError):acquire_windows(Adapter(tmp_path/'run'),server,'RPT_TEST','20260907','20260911',math.inf,tmp_path/'cache')
    assert len(list((tmp_path/'cache').glob('*.json')))==2
