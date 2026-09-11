from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SOURCE = Path(__file__).with_name("canonical_business_adapter.py")
SPEC = importlib.util.spec_from_file_location("stock_research_adapter_test", SOURCE)
assert SPEC is not None and SPEC.loader is not None
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


def test_load_delivery_manifest_binds_verified_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    artifact.write_text('{"status":"CLEAN_PASS"}\n', encoding="utf-8")
    manifest_path = tmp_path / "delivery.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema": "STOCK_PROJECT_DELIVERY_MANIFEST_V1",
                "status": "CLEAN_PASS",
                "errors": [],
                "artifacts": [
                    {
                        "path": str(artifact.resolve()),
                        "size": artifact.stat().st_size,
                        "sha256": ADAPTER.sha256_file(artifact),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest, errors = ADAPTER.load_delivery_manifest(str(manifest_path))

    assert errors == []
    assert manifest is not None
    assert manifest["status"] == "CLEAN_PASS"
    assert manifest["payload"]["artifacts"][0]["path"] == str(artifact.resolve())


def test_load_delivery_manifest_rejects_hash_drift(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    artifact.write_text("{}\n", encoding="utf-8")
    manifest_path = tmp_path / "delivery.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema": "STOCK_PROJECT_DELIVERY_MANIFEST_V1",
                "status": "CLEAN_PASS",
                "errors": [],
                "artifacts": [
                    {
                        "path": str(artifact.resolve()),
                        "size": artifact.stat().st_size,
                        "sha256": "0" * 64,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest, errors = ADAPTER.load_delivery_manifest(str(manifest_path))

    assert "delivery_manifest_artifact_0_sha256_mismatch" in errors
    assert manifest is not None
    assert manifest["status"] == "BLOCKED"
