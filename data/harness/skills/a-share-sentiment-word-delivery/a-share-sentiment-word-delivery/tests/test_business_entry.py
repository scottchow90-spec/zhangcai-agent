from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts" / "legacy_codex_entry.py"


def test_business_entry_no_longer_depends_on_deleted_system_skill_entry() -> None:
    text = ENTRY.read_text(encoding="utf-8")
    assert "unified_skill_entry.py" not in text
    assert '"status": "CLEAN_PASS"' in text


def test_business_entry_run_returns_clean_pass() -> None:
    environment = {**os.environ, "ONESTOCK_STOCK_CANONICAL_CHILD": "1"}
    completed = subprocess.run(
        [sys.executable, str(ENTRY), "run"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert '"status": "CLEAN_PASS"' in completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["validated_files"]
    assert all("relative_path" in item for item in payload["validated_files"])
    assert all(item["contract_binding_required"] is True for item in payload["validated_files"])
    assert all("sha256" not in item for item in payload["validated_files"])
