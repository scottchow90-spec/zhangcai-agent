from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"


def _load_verifier():
    sys.path.insert(0, str(SCRIPTS))
    script = SCRIPTS / "verify_convertible_bond_screening.py"
    spec = importlib.util.spec_from_file_location("convertible_bond_verifier", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(os.name != "nt", reason="Windows device path regression")
def test_same_path_accepts_windows_device_prefix(tmp_path: Path) -> None:
    verifier = _load_verifier()
    source = tmp_path / "trusted.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    ordinary = source.resolve()
    extended = Path("\\\\?\\" + str(ordinary))

    assert verifier.same_path(extended, ordinary)
