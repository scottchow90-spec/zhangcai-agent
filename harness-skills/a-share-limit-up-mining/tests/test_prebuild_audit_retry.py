from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "lianban_prebuild_audit_gate.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("lianban_prebuild_audit_gate", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_transient_json_decode_failure_is_retried() -> None:
    module = load_module()
    calls = 0
    sleeps: list[float] = []

    def operation():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise json.JSONDecodeError("temporary non-json response", "", 0)
        return "ok"

    result = module.call_transient_source(
        operation,
        attempts=3,
        delays=(0.0, 0.0),
        sleep=sleeps.append,
    )

    assert result == "ok"
    assert calls == 2
    assert sleeps == [0.0]


def test_non_transient_failure_is_not_retried() -> None:
    module = load_module()
    calls = 0

    def operation():
        nonlocal calls
        calls += 1
        raise ValueError("bad schema")

    try:
        module.call_transient_source(operation, attempts=3, delays=(0.0, 0.0))
    except ValueError as exc:
        assert str(exc) == "bad schema"
    else:
        raise AssertionError("non-transient failure was swallowed")

    assert calls == 1
