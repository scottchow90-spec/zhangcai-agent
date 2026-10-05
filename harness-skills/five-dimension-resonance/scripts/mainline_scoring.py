# -*- coding: utf-8 -*-
"""Compatibility import for the independent core mainline scoring owner."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
from pathlib import Path


OWNER = (
    Path(__file__).resolve().parents[2]
    / "core-mainline-scoring-system"
    / "scripts"
    / "mainline_scoring.py"
)
_spec = importlib.util.spec_from_file_location("core_mainline_scoring_owner", OWNER)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load independent core mainline scorer: {OWNER}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

for _name in dir(_module):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_module, _name)

__canonical_owner__ = "core-mainline-scoring-system"
