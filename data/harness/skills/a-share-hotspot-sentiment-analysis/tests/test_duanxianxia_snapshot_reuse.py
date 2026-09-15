from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import subprocess
from pathlib import Path


CLIENT = Path(__file__).resolve().parents[1] / "scripts" / "duanxianxia_client.ps1"


def test_explicit_current_task_snapshot_is_reused_without_network(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    output = tmp_path / "output.json"
    source.write_text(
        json.dumps(
            {
                "generated_at": "2026-08-18T10:00:00+08:00",
                "source_page": "https://duanxianxia.com/web/main",
                "access_scope": "public HTTP data only; no browser credentials exported",
                "datasource": {"istrade": 1, "data_url": "https://example.invalid"},
                "selected_datasets": ["hotlist", "ztplate", "ztpool"],
                "datasets": {
                    "hotlist": {"success": True, "data": {"sentinel": "same-task"}},
                    "ztplate": {"success": True, "data": {"list": []}},
                    "ztpool": {"success": True, "data": {"list": []}},
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            (
                f"& '{CLIENT}' -InputSnapshot '{source}' "
                f"-Dataset @('hotlist','ztplate') -Output '{output}'"
            ),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output.read_text(encoding="utf-8-sig"))
    assert payload["selected_datasets"] == ["hotlist", "ztplate"]
    assert set(payload["datasets"]) == {"hotlist", "ztplate"}
    assert payload["datasets"]["hotlist"]["data"]["sentinel"] == "same-task"
    assert payload["reuse"]["mode"] == "current_task_inherited_snapshot"
    assert payload["access_scope"] == "public HTTP data only; no browser credentials exported"
