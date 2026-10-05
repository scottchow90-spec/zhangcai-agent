#!/usr/bin/env python3
"""Fail-closed delivery and lineage gates for the future forecast pipeline."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_DELIVERABLES = (
    "forecast_snapshot.json",
    "feature_snapshot.json",
    "forecast_rank.csv",
    "leader_rank.csv",
    "evidence.json",
    "model_card.json",
    "backtest_report.json",
    "audit.json",
    "manifest.json",
    "report.md",
)
MANIFEST_BOUND_DELIVERABLES = tuple(
    value for value in REQUIRED_DELIVERABLES if value != "manifest.json"
)
FORECAST_STATUSES = {
    "VALIDATED_FORECAST",
    "PROVISIONAL_FORECAST",
    "DEGRADED_FORECAST",
    "BLOCKED",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_delivery_manifest(
    output_dir: Path,
    *,
    snapshot_id: str,
    resolved_trade_date: str,
    forecast_status: str,
    model_version: str,
) -> dict:
    artifacts: list[dict] = []
    for name in MANIFEST_BOUND_DELIVERABLES:
        path = output_dir / name
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"manifest_artifact_missing_or_empty:{name}")
        artifacts.append(
            {
                "name": name,
                "path": name,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "schema": "SHORTLINE_FORECAST_DELIVERY_MANIFEST_V1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_id": snapshot_id,
        "resolved_trade_date": resolved_trade_date,
        "forecast_status": forecast_status,
        "model_version": model_version,
        "requires_research_completion": False,
        "artifacts": artifacts,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def validate_delivery_manifest(manifest: dict, output_dir: Path) -> dict:
    errors: list[str] = []
    if manifest.get("schema") != "SHORTLINE_FORECAST_DELIVERY_MANIFEST_V1":
        errors.append("manifest_schema_invalid")
    if not str(manifest.get("snapshot_id", "")):
        errors.append("manifest_snapshot_id_missing")
    if not str(manifest.get("resolved_trade_date", "")):
        errors.append("manifest_resolved_trade_date_missing")
    if manifest.get("forecast_status") not in FORECAST_STATUSES - {"BLOCKED"}:
        errors.append("manifest_forecast_status_invalid")
    if manifest.get("requires_research_completion") is True:
        errors.append("manifest_requires_research_completion")
    entries = manifest.get("artifacts")
    if not isinstance(entries, list):
        entries = []
        errors.append("manifest_artifacts_invalid")
    by_name = {
        str(entry.get("name")): entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("name")
    }
    expected = set(MANIFEST_BOUND_DELIVERABLES)
    if set(by_name) != expected:
        missing = sorted(expected - set(by_name))
        extra = sorted(set(by_name) - expected)
        if missing:
            errors.append("manifest_artifacts_missing:" + ",".join(missing))
        if extra:
            errors.append("manifest_artifacts_extra:" + ",".join(extra))
    resolved_output = output_dir.resolve()
    for name in MANIFEST_BOUND_DELIVERABLES:
        entry = by_name.get(name)
        if entry is None:
            continue
        path = (output_dir / str(entry.get("path", ""))).resolve()
        if path.parent != resolved_output or path.name != name:
            errors.append(f"artifact_path_outside_delivery:{name}")
            continue
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"artifact_missing_or_empty:{name}")
            continue
        if path.stat().st_size != int(entry.get("size", -1)):
            errors.append(f"artifact_size_mismatch:{name}")
        if sha256_file(path) != str(entry.get("sha256", "")):
            errors.append(f"artifact_hash_mismatch:{name}")
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.is_file() or manifest_path.stat().st_size == 0:
        errors.append("manifest_file_missing_or_empty")
    else:
        try:
            readback = json.loads(manifest_path.read_text(encoding="utf-8"))
            if readback != manifest:
                errors.append("manifest_readback_mismatch")
        except (OSError, UnicodeError, json.JSONDecodeError):
            errors.append("manifest_readback_invalid")
    return {
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "forecast_status": manifest.get("forecast_status", "BLOCKED"),
        "snapshot_id": manifest.get("snapshot_id"),
        "errors": errors,
    }


def validate_pipeline_lineage(
    snapshot: dict,
    feature_snapshot: dict,
    forecasts: list[dict],
    leaders: list[dict],
) -> dict:
    errors: list[str] = []
    snapshot_id = str(snapshot.get("snapshot_id", ""))
    if not snapshot_id:
        errors.append("lineage_snapshot_id_missing")
    if str(feature_snapshot.get("snapshot_id", "")) != snapshot_id:
        errors.append("lineage_feature_snapshot_mismatch")
    if any(str(row.get("snapshot_id", "")) != snapshot_id for row in forecasts):
        errors.append("lineage_forecast_snapshot_mismatch")
    if any(str(row.get("snapshot_id", "")) != snapshot_id for row in leaders):
        errors.append("lineage_leader_snapshot_mismatch")
    forecast_sectors = {str(row.get("sector", "")) for row in forecasts}
    leader_sectors = {str(row.get("sector", "")) for row in leaders}
    if not leader_sectors.issubset(forecast_sectors):
        errors.append("lineage_leader_sector_outside_forecast_candidates")
    snapshot_members = {
        str(sector.get("sector")): {
            str(value.get("code")) if isinstance(value, dict) else str(value)
            for value in sector.get("members", [])
        }
        for sector in snapshot.get("sectors", [])
    }
    if any(
        str(row.get("code")) not in snapshot_members.get(str(row.get("sector")), set())
        for row in leaders
    ):
        errors.append("lineage_leader_code_outside_frozen_members")
    return {"status": "PASS" if not errors else "BLOCKED", "errors": errors}
