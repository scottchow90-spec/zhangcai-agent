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


SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "legacy_codex_entry.py"


def load_module():
    spec = importlib.util.spec_from_file_location("stock_recap_video_lock_test", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_package_lock_semantic_hash_ignores_json_formatting_but_not_versions(
    tmp_path: Path,
):
    module = load_module()
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    changed = tmp_path / "changed.json"
    payload = {
        "lockfileVersion": 3,
        "packages": {"": {"dependencies": {"remotion": "4.0.1"}}},
    }
    left.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    right.write_text(
        '{"packages":{"":{"dependencies":{"remotion":"4.0.1"}}},"lockfileVersion":3}',
        encoding="utf-8",
    )
    changed.write_text(
        '{"packages":{"":{"dependencies":{"remotion":"4.0.2"}}},"lockfileVersion":3}',
        encoding="utf-8",
    )

    assert module.package_lock_semantic_sha256(left) == module.package_lock_semantic_sha256(right)
    assert module.package_lock_semantic_sha256(left) != module.package_lock_semantic_sha256(changed)
