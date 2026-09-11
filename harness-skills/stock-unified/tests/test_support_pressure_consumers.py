from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
from pathlib import Path

import pytest


DRAGON = Path(r"D:\C盘转移\日志\codex\skills\dragon-pullback\scripts\run_dragon_pullback_smoke.py")
OVERSOLD = Path(r"D:\C盘转移\日志\codex\skills\oversold-first-board\scripts\run_oversold_first_board_smoke.py")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("path", "name"),
    [(DRAGON, "dragon_support_test")],
)
def test_consumer_loads_current_support_through_shared_adapter(
    monkeypatch, tmp_path: Path, path: Path, name: str
):
    module = load_module(path, name)
    module.REPORTS = tmp_path / name
    observed = {}
    expected = {
        "candidates": [{"code": "000001.SH", "rsi14": 30.0}],
        "data_source": "support-pressure-analysis-system",
        "fallback_used": False,
    }

    def fake_run(home, out_dir, **kwargs):
        observed.update(home=home, out_dir=out_dir, kwargs=kwargs)
        return expected

    monkeypatch.setattr(module, "run_current_support_pressure", fake_run)

    assert module.load_support_data_v2(module.WORKSPACE) == expected
    assert observed["home"] == module.WORKSPACE
    assert observed["out_dir"].parent == module.REPORTS / "support-pressure-input"
    assert observed["kwargs"]["timeout"] == 600


def test_oversold_empty_selection_is_truthful_completed_scan():
    module = load_module(OVERSOLD, "oversold_empty_test")

    payload = module.build_business_payload(
        [],
        latest_trade_date="20260824",
        universe={
            "eligible_security_records": 5000,
            "scan_stats": {"latest_trade_date": 4900},
        },
        data_source={"type": "local_tdx_raw_daily"},
    )

    assert payload["status"] == "CLEAN_PASS"
    assert payload["selection_status"] == "NO_SIGNAL"
    assert payload["selection"]["candidate_count"] == 0
    assert payload["selection"]["candidates"] == []
    assert "candidate" not in payload
