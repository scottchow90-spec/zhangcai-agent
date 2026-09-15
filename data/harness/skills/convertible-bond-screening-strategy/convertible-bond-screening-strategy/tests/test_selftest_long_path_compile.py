from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "selftest.py"


def _load_selftest_module():
    spec = importlib.util.spec_from_file_location("convertible_bond_selftest", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(os.name != "nt", reason="Windows extended path regression")
def test_compile_scripts_uses_explicit_cache_for_extended_windows_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_selftest_module()
    source = tmp_path / "sample.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    extended_source = Path("\\\\?\\" + str(source.resolve()))
    compile_root = tmp_path / "compiled-bytecode"
    monkeypatch.setattr(sys, "pycache_prefix", str(tmp_path / "central-pycache"))

    errors = module.compile_scripts([extended_source], compile_root)

    assert errors == []
    assert len(list(compile_root.glob("*.pyc"))) == 1
