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


HOME = Path(__file__).resolve().parents[3]
ADAPTER = HOME / "scripts" / "stock_custom_audit_adapter.py"
AUDIT_SKILLS = (
    "a-share-leader-deep-research",
    "a-share-limit-up-leader-classification",
    "buzhang-leader-mining",
    "nana-teacher-five-strategies",
)


def load_adapter():
    spec = importlib.util.spec_from_file_location("portable_stock_audit_adapter", ADAPTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_shared_audit_adapter_derives_relocated_runtime_home(tmp_path: Path):
    module = load_adapter()
    relocated = tmp_path / "Home" / "scripts" / "stock_custom_audit_adapter.py"

    assert module.runtime_home(relocated) == tmp_path / "Home"


@pytest.mark.parametrize("skill_id", AUDIT_SKILLS)
def test_stock_audit_entry_does_not_launch_through_user_home(skill_id: str):
    source = (HOME / "skills" / skill_id / "scripts" / "audit_entry.py").read_text(
        encoding="utf-8-sig"
    )

    assert "Path.home()" not in source
    assert "stock_custom_audit_adapter.py" in source
