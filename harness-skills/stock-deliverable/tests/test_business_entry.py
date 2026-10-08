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
PRIMARY = ROOT / "scripts" / "stock-deliverable.py"
LEGACY = ROOT / "scripts" / "legacy_codex_entry.py"


def _environment() -> dict[str, str]:
    return {**os.environ, "ONESTOCK_STOCK_CANONICAL_CHILD": "1"}


def test_primary_no_longer_references_deleted_legacy_gates() -> None:
    text = PRIMARY.read_text(encoding="utf-8")
    for deleted in (
        "skill_workflow_lock.py",
        "stock_workflow_substantive_gate.py",
        "stock_deliverable_executor.py",
        "stock_delivery_risk_gate.py",
    ):
        assert deleted not in text


def test_canonical_business_sample_validates_current_skill_assets() -> None:
    completed = subprocess.run(
        [sys.executable, str(LEGACY), "run"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_environment(),
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert '"status": "CLEAN_PASS"' in completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["validated_files"]
    assert all("relative_path" in item for item in payload["validated_files"])
    assert all(item["contract_binding_required"] is True for item in payload["validated_files"])
    assert all("sha256" not in item for item in payload["validated_files"])
