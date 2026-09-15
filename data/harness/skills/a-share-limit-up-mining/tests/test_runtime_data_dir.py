from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_HOME = SKILL_ROOT.parents[1]


def _load_collect_risk():
    script = SKILL_ROOT / "scripts" / "collect_risk.py"
    spec = importlib.util.spec_from_file_location("limit_up_collect_risk", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_risk_uses_the_same_runtime_home_as_other_collectors() -> None:
    module = _load_collect_risk()

    assert module.DATA_DIR == RUNTIME_HOME / "tmp_lb" / "data"
