#!/usr/bin/env python3
"""Immutable, batch-scoped evidence manifests for canonical stock runs."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

SCHEMA = "STOCK_EVIDENCE_SET_V1"
BATCH_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class EvidenceSetError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_hash(payload: dict[str, Any]) -> str:
    canonical = dict(payload)
    canonical.pop("evidence_set_id", None)
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def validate_batch_id(batch_id: str) -> str:
    value = str(batch_id or "").strip()
    if not BATCH_ID_RE.fullmatch(value):
        raise EvidenceSetError("invalid_batch_id")
    return value


_validate_batch_id = validate_batch_id


def _validate_trading_date(trading_date: str) -> str:
    value = str(trading_date or "").strip()
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise EvidenceSetError("invalid_trading_date") from exc
    if parsed.isoformat() != value:
        raise EvidenceSetError("invalid_trading_date")
    return value


def _artifact_record(artifact_id: str, path: Path) -> dict[str, Any]:
    identifier = str(artifact_id or "").strip()
    if not identifier or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,79}", identifier):
        raise EvidenceSetError(f"invalid_artifact_id:{identifier}")
    resolved = path.resolve()
    if not resolved.is_file():
        raise EvidenceSetError(f"artifact_missing:{resolved}")
    return {
        "id": identifier,
        "path": str(resolved),
        "size": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def write_evidence_set(
    manifest_path: Path,
    *,
    batch_id: str,
    trading_date: str,
    artifacts: dict[str, Path],
    created_at: str | None = None,
) -> dict[str, Any]:
    batch = _validate_batch_id(batch_id)
    trade_date = _validate_trading_date(trading_date)
    if not artifacts:
        raise EvidenceSetError("artifacts_missing")
    records = [
        _artifact_record(artifact_id, Path(path))
        for artifact_id, path in sorted(artifacts.items())
    ]
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "CLEAN_PASS",
        "batch_id": batch,
        "trading_date": trade_date,
        "created_at": created_at
        or datetime.now().astimezone().isoformat(timespec="seconds"),
        "reuse_policy": {
            "read_only": True,
            "same_batch_only": True,
            "same_trading_date_only": True,
        },
        "artifacts": records,
    }
    payload["evidence_set_id"] = _canonical_hash(payload)
    target = Path(manifest_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=target.parent,
            delete=False,
            encoding="utf-8",
        ) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    readback = load_evidence_set(
        target,
        expected_batch_id=batch,
        expected_trading_date=trade_date,
    )
    if readback != payload:
        raise EvidenceSetError("manifest_readback_mismatch")
    return load_evidence_set(
        target,
        expected_batch_id=batch,
        expected_trading_date=trade_date,
    )


def load_evidence_set(
    manifest_path: Path,
    *,
    expected_batch_id: str | None = None,
    expected_trading_date: str | None = None,
) -> dict[str, Any]:
    path = Path(manifest_path).resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceSetError(f"manifest_read_failed:{type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise EvidenceSetError("manifest_not_object")
    if payload.get("schema") != SCHEMA:
        raise EvidenceSetError("schema_mismatch")
    if payload.get("status") != "CLEAN_PASS":
        raise EvidenceSetError("status_not_clean")
    batch = _validate_batch_id(str(payload.get("batch_id") or ""))
    trade_date = _validate_trading_date(str(payload.get("trading_date") or ""))
    if expected_batch_id is not None and batch != _validate_batch_id(expected_batch_id):
        raise EvidenceSetError("batch_id_mismatch")
    if (
        expected_trading_date is not None
        and trade_date != _validate_trading_date(expected_trading_date)
    ):
        raise EvidenceSetError("trading_date_mismatch")
    policy = payload.get("reuse_policy")
    if policy != {
        "read_only": True,
        "same_batch_only": True,
        "same_trading_date_only": True,
    }:
        raise EvidenceSetError("reuse_policy_mismatch")
    records = payload.get("artifacts")
    if not isinstance(records, list) or not records:
        raise EvidenceSetError("artifacts_missing")
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise EvidenceSetError("artifact_record_invalid")
        identifier = str(record.get("id") or "")
        if identifier in seen:
            raise EvidenceSetError(f"artifact_id_duplicate:{identifier}")
        seen.add(identifier)
        artifact = Path(str(record.get("path") or "")).resolve()
        if not artifact.is_file():
            raise EvidenceSetError(f"artifact_missing:{artifact}")
        if int(record.get("size", -1)) != artifact.stat().st_size:
            raise EvidenceSetError(f"artifact_size_mismatch:{identifier}")
        if str(record.get("sha256") or "").casefold() != sha256_file(artifact):
            raise EvidenceSetError(f"artifact_hash_mismatch:{identifier}")
    if str(payload.get("evidence_set_id") or "") != _canonical_hash(payload):
        raise EvidenceSetError("evidence_set_id_mismatch")
    return payload


def artifact_path(payload: dict[str, Any], artifact_id: str) -> Path:
    for record in payload.get("artifacts", []):
        if isinstance(record, dict) and record.get("id") == artifact_id:
            return Path(str(record["path"])).resolve()
    raise EvidenceSetError(f"artifact_id_missing:{artifact_id}")
