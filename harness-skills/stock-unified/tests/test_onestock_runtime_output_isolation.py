from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
from pathlib import Path


HOME = Path(__file__).resolve().parents[3]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_onestock_runtime_outputs_are_outside_immutable_skill_home(monkeypatch, tmp_path):
    monkeypatch.setenv("ONESTOCK_STOCK_DATA_ROOT", str(tmp_path))

    oversold = load_module(
        HOME / "skills" / "oversold-first-board" / "scripts" / "run_oversold_first_board_smoke.py",
        "oversold_runtime_output_isolation",
    )
    dragon = load_module(
        HOME / "skills" / "dragon-pullback" / "scripts" / "run_dragon_pullback_smoke.py",
        "dragon_runtime_output_isolation",
    )
    support = load_module(
        HOME / "skills" / "support-pressure-analysis-system" / "scripts" / "scientific_engine.py",
        "support_runtime_output_isolation",
    )
    tdx = load_module(
        HOME / "skills" / "tdx-local-hub" / "scripts" / "tdx_hub.py",
        "tdx_runtime_output_isolation",
    )

    assert oversold.REPORTS == tmp_path / "runtime" / "skills" / "oversold-first-board" / "reports"
    assert dragon.REPORTS == tmp_path / "runtime" / "skills" / "dragon-pullback" / "reports"
    assert support.REPORTS_ROOT == tmp_path / "runtime" / "skills" / "support-pressure-analysis-system" / "reports"
    assert tdx.TQ_LOCK_PATH == tmp_path / "runtime" / "skills" / "tdx-local-hub" / "tq.lock"


def test_fifteen_dimension_audit_uses_onestock_data_root(monkeypatch, tmp_path):
    monkeypatch.setenv("ONESTOCK_STOCK_DATA_ROOT", str(tmp_path))
    audit = load_module(
        HOME / "skills" / "a-share-15d-selection" / "scripts" / "audit_engine.py",
        "fifteen_dimension_onestock_audit_output",
    )

    assert audit.audit_reports_root() == (
        tmp_path / "stock-custom-audit" / "a-share-15d-selection"
    )


def test_fifteen_dimension_audit_uses_runtime_home_without_onestock_root(monkeypatch):
    monkeypatch.delenv("ONESTOCK_STOCK_DATA_ROOT", raising=False)
    audit = load_module(
        HOME / "skills" / "a-share-15d-selection" / "scripts" / "audit_engine.py",
        "fifteen_dimension_codex_audit_output",
    )

    assert audit.audit_reports_root() == (
        HOME / "skills" / "a-share-15d-selection" / "reports" / "audit"
    )


def test_shared_stock_audit_uses_onestock_data_root(monkeypatch, tmp_path):
    monkeypatch.setenv("ONESTOCK_STOCK_DATA_ROOT", str(tmp_path))
    audit = load_module(
        HOME / "scripts" / "stock_audit_business.py",
        "shared_stock_audit_onestock_output",
    )

    assert audit.audit_reports_root("stock-study") == (
        tmp_path / "stock-custom-audit" / "stock-study"
    )


def test_shared_stock_audit_uses_skill_home_without_onestock_root(monkeypatch):
    monkeypatch.delenv("ONESTOCK_STOCK_DATA_ROOT", raising=False)
    audit = load_module(
        HOME / "scripts" / "stock_audit_business.py",
        "shared_stock_audit_codex_output",
    )

    assert audit.audit_reports_root("stock-study") == (
        HOME / "skills" / "stock-study" / "reports" / "audit"
    )
