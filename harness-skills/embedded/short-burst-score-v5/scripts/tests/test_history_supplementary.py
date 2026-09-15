import json
import pytest
from lhbpost.data.history_supplementary import select_source

def test_only_completed_covering_source_can_be_selected(tmp_path):
    for name,status in [('a','ACQUIRED_WITH_COVERAGE_GAPS'),('b','ACQUIRING')]:
        path=tmp_path/name/'market_history_source';path.mkdir(parents=True)
        (path/'acquisition_manifest.json').write_text(json.dumps({
            'schema':'BAOSTOCK_MARKET_HISTORY_SOURCE_V1','status':status,
            'start_date':'2025-01-01','target_date':'2026-09-11'}))
    assert select_source('20260101','20260911',tmp_path).parent.name=='a'
    with pytest.raises(ValueError,match='no_completed'):
        select_source('20240101','20260911',tmp_path)


def test_invalid_json_shape_cannot_mask_older_completed_source(tmp_path):
    valid=tmp_path/'a'/'market_history_source';valid.mkdir(parents=True)
    (valid/'acquisition_manifest.json').write_text(json.dumps({
        'schema':'BAOSTOCK_MARKET_HISTORY_SOURCE_V1','status':'ACQUIRED_PROVIDER_SCOPE',
        'start_date':'2025-01-01','target_date':'2026-09-11'}))
    malformed=tmp_path/'z'/'market_history_source';malformed.mkdir(parents=True)
    (malformed/'acquisition_manifest.json').write_text('[]')
    assert select_source('20260101','20260911',tmp_path)==valid
