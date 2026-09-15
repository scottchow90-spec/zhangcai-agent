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


def _load_build_docx():
    script = SKILL_ROOT / "scripts" / "build_docx.py"
    spec = importlib.util.spec_from_file_location("limit_up_build_docx", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_summary_rows_are_limited_to_the_five_rows_that_are_rendered() -> None:
    module = _load_build_docx()
    scored = [{"code": f"{index:06d}"} for index in range(101)]

    rows = module.select_summary_rows([], scored)

    assert rows == scored[:5]
