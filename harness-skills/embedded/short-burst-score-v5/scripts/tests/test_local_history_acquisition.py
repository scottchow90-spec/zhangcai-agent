import json,time
from types import SimpleNamespace
import pytest
from lhbpost.data import local_history_acquisition as m

def source(root,status='ACQUIRED_WITH_COVERAGE_GAPS'):
    root.mkdir()
    (root/'acquisition_manifest.json').write_text(json.dumps(dict(schema='BAOSTOCK_MARKET_HISTORY_SOURCE_V1',
        status=status,start_date='2025-10-01',target_date='2026-09-11')),encoding='utf-8')
    return root

def test_range_and_completion_required(tmp_path):
    root=source(tmp_path/'source')
    assert m.validate_source(root,'20260101','20260911')['status']=='ACQUIRED_WITH_COVERAGE_GAPS'
    with pytest.raises(ValueError):m.validate_source(root,'20240101','20260911')
    with pytest.raises(ValueError):m.validate_source(root,'20260101','20260910')

def test_in_progress_source_is_never_reused(tmp_path):
    root=source(tmp_path/'source','ACQUIRING')
    with pytest.raises(ValueError):m.validate_source(root,'20260101','20260911')

def test_verified_cache_does_not_restart_provider(tmp_path,monkeypatch):
    root=source(tmp_path/'source');provider=tmp_path/'provider.py';provider.write_text('test fixture')
    monkeypatch.setattr(m,'PROVIDER',provider)
    cache=tmp_path/'cache';cache.mkdir()
    proof=dict(provider_sha256=m.sha(provider),source_root=str(root),manifest_sha256=m.sha(root/'acquisition_manifest.json'))
    (cache/'20260101-20260911.json').write_text(json.dumps(proof),encoding='utf-8')
    adapter=SimpleNamespace(out=tmp_path,history_provider_cache=cache,_json=lambda *a:None)
    monkeypatch.setattr(m.subprocess,'Popen',lambda *a,**k:(_ for _ in ()).throw(AssertionError('unexpected restart')))
    assert m.acquire_or_reuse(adapter,'20260101','20260911')==root

def test_no_budget_does_not_launch_and_child_requires_canonical(tmp_path,monkeypatch):
    provider=tmp_path/'provider.py';provider.write_text('test fixture');monkeypatch.setattr(m,'PROVIDER',provider)
    adapter=SimpleNamespace(out=tmp_path,history_provider_cache=tmp_path/'cache',acquisition_deadline=time.monotonic(),_json=lambda *a:None)
    with pytest.raises(TimeoutError):m.acquire_or_reuse(adapter,'20260101','20260911')
    monkeypatch.delenv('CODEX_STOCK_CANONICAL_EXECUTION',raising=False)
    with pytest.raises(ValueError,match='canonical_parent_required'):m.child_main(str(tmp_path),'20260911','bad','')
