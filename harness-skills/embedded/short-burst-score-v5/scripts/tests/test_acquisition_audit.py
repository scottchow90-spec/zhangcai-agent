from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest

from lhbpost.data.tushare_postmarket import TusharePostMarketAdapter, TushareUnavailable


def adapter(tmp_path, **apis):
    obj = TusharePostMarketAdapter.__new__(TusharePostMarketAdapter)
    obj.out = tmp_path
    obj.pro = SimpleNamespace(**apis)
    obj.sleep = 0
    obj.retries = 2
    obj.INDEX_CODES = ('000001.SH',)
    return obj


def test_index_refresh_extends_existing_range(tmp_path):
    folder = tmp_path / 'index_daily'
    folder.mkdir()
    pd.DataFrame({'ts_code': ['000001.SH'], 'trade_date': ['20250102'], 'close': [1]}).to_csv(folder / '000001_SH.csv', index=False)
    api = Mock(return_value=pd.DataFrame({'ts_code': ['000001.SH'], 'trade_date': ['20250103'], 'close': [2]}))
    adapter(tmp_path, index_daily=api).index_daily('20250103', '20250103')
    assert api.call_count == 1
    assert pd.read_csv(folder / '000001_SH.csv', dtype=str).trade_date.tolist() == ['20250102', '20250103']


def test_headerless_cache_is_downloaded_again(tmp_path):
    folder = tmp_path / 'top_list'
    folder.mkdir()
    (folder / '20250102.csv').write_text('\ufeff\n', encoding='utf-8')
    api = Mock(return_value=pd.DataFrame(columns=['ts_code', 'trade_date']))
    adapter(tmp_path, top_list=api).by_trade_date('top_list', ['20250102'])
    assert api.call_count == 1


def test_none_is_retried_and_never_cached(tmp_path):
    api = Mock(return_value=None)
    with pytest.raises(TushareUnavailable):
        adapter(tmp_path, top_list=api).by_trade_date('top_list', ['20250102'])
    assert api.call_count == 2
    assert not (tmp_path / 'top_list' / '20250102.csv').exists()


def test_valid_empty_optional_table_can_be_cached(tmp_path):
    api = Mock(return_value=pd.DataFrame(columns=['ts_code', 'trade_date']))
    obj = adapter(tmp_path, top_list=api)
    obj.by_trade_date('top_list', ['20250102'])
    obj.by_trade_date('top_list', ['20250102'])
    assert api.call_count == 1


def test_future_date_is_not_downloaded(tmp_path):
    api = Mock(return_value=pd.DataFrame(columns=['ts_code', 'trade_date']))
    tomorrow = (datetime.now(timezone(timedelta(hours=8))) + timedelta(days=1)).strftime('%Y%m%d')
    with pytest.raises(ValueError):
        adapter(tmp_path, top_list=api).by_trade_date('top_list', [tomorrow])
    api.assert_not_called()


def test_wrong_date_cache_is_replaced(tmp_path):
    folder = tmp_path / 'daily'
    folder.mkdir()
    pd.DataFrame({'ts_code': ['A'], 'trade_date': ['20250101']}).to_csv(folder / '20250102.csv', index=False)
    api = Mock(return_value=pd.DataFrame({'ts_code': ['A'], 'trade_date': ['20250102']}))
    adapter(tmp_path, daily=api).by_trade_date('daily', ['20250102'])
    assert api.call_count == 1


def test_empty_required_table_is_not_cached(tmp_path):
    api = Mock(return_value=pd.DataFrame(columns=['ts_code', 'trade_date']))
    with pytest.raises(TushareUnavailable):
        adapter(tmp_path, daily=api).by_trade_date('daily', ['20250102'])
    assert not (tmp_path / 'daily' / '20250102.csv').exists()


def test_index_large_ranges_are_split_by_year(tmp_path):
    api = Mock(return_value=pd.DataFrame(columns=['ts_code', 'trade_date']))
    adapter(tmp_path, index_daily=api).index_daily('20231229', '20250103')
    assert [(c.kwargs['start_date'], c.kwargs['end_date']) for c in api.call_args_list] == [
        ('20231229', '20231231'), ('20240101', '20241231'), ('20250101', '20250103')]


def test_invalid_index_refresh_preserves_original(tmp_path):
    folder = tmp_path / 'index_daily'
    folder.mkdir()
    path = folder / '000001_SH.csv'
    pd.DataFrame({'ts_code': ['000001.SH'], 'trade_date': ['20250102']}).to_csv(path, index=False)
    original = path.read_bytes()
    api = Mock(return_value=pd.DataFrame({'ts_code': ['WRONG'], 'trade_date': ['20250103']}))
    with pytest.raises(TushareUnavailable):
        adapter(tmp_path, index_daily=api).index_daily('20250103', '20250103')
    assert path.read_bytes() == original


def test_today_empty_optional_cache_is_refreshed(tmp_path):
    obj = adapter(tmp_path, top_list=Mock(return_value=pd.DataFrame(columns=['ts_code', 'trade_date'])))
    obj.by_trade_date('top_list', [obj._today()])
    obj.by_trade_date('top_list', [obj._today()])
    assert obj.pro.top_list.call_count == 2


def test_download_defaults_stop_at_today(tmp_path):
    api = Mock(return_value=pd.DataFrame({'cal_date': ['20250102']}))
    obj = adapter(tmp_path, trade_cal=api)
    obj.stock_basic_all = Mock()
    obj.industry_members = Mock()
    obj.index_daily = Mock()
    obj.by_trade_date = Mock()
    obj.download_core()
    assert api.call_args.kwargs['end_date'] == obj._today()
