#!/usr/bin/env python3
"""Check or synchronize immutable merged-skill component file hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
CATALOG = ROOT / "references" / "stock_skill_ids.json"
IGNORED_DIRS = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def component_files(component_root: Path) -> dict[str, Path]:
    return {
        path.relative_to(component_root).as_posix(): path
        for path in sorted(component_root.rglob("*"), key=str)
        if path.is_file()
        and not any(part in IGNORED_DIRS for part in path.parts)
        and path.suffix.casefold() not in IGNORED_SUFFIXES
    }


def audit_manifest(manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    skill_root = manifest_path.parents[1]
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {}, [], [f"manifest_invalid:{manifest_path}:{exc}"]
    schema = payload.get("schema") if isinstance(payload, dict) else None
    sources = payload.get("sources") if isinstance(payload, dict) else None
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(schema, str) or not schema.startswith("MERGED_SKILL_SOURCE_MANIFEST_V"):
        return payload, [], [f"manifest_schema_invalid:{manifest_path}"]
    if not isinstance(sources, list) or not all(isinstance(item, str) and item for item in sources):
        return payload, [], [f"manifest_sources_invalid:{manifest_path}"]
    if len(sources) != len(set(sources)) or not isinstance(files, dict) or set(files) != set(sources):
        return payload, [], [f"manifest_source_set_invalid:{manifest_path}"]

    changes: list[dict[str, str]] = []
    errors: list[str] = []
    for source_id in sources:
        listed = files.get(source_id)
        if not isinstance(listed, dict) or not all(
            isinstance(relative, str) and isinstance(expected, str)
            for relative, expected in listed.items()
        ):
            errors.append(f"manifest_files_invalid:{manifest_path}:{source_id}")
            continue
        component_root = (skill_root / "components" / source_id).resolve()
        if not component_root.is_dir():
            errors.append(f"component_missing:{manifest_path}:{source_id}")
            continue
        actual = component_files(component_root)
        for relative in sorted(set(actual) - set(listed)):
            errors.append(f"unlisted_component_file:{manifest_path}:{source_id}:{relative}")
        for relative in sorted(set(listed) - set(actual)):
            errors.append(f"listed_component_file_missing:{manifest_path}:{source_id}:{relative}")
        if errors:
            continue
        for relative, path in actual.items():
            expected = listed[relative]
            current = sha256_file(path)
            if current != expected:
                changes.append(
                    {
                        "manifest": str(manifest_path),
                        "source_id": source_id,
                        "relative": relative,
                        "previous": expected,
                        "actual": current,
                    }
                )
    return payload, changes, errors


def manifest_paths() -> list[Path]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8-sig"))
    return [
        path
        for skill_id in catalog["skills"]
        if (path := SKILLS_ROOT / skill_id / "references" / "source-manifest.json").is_file()
    ]


def write_manifest(manifest_path: Path, payload: dict[str, Any], changes: list[dict[str, str]]) -> None:
    for change in changes:
        payload["files"][change["source_id"]][change["relative"]] = change["actual"]
    payload["last_synchronized_at"] = datetime.now(timezone.utc).isoformat()
    temporary = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    readback_payload, readback_changes, readback_errors = audit_manifest(temporary)
    if readback_payload != payload or readback_changes or readback_errors:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"source_manifest_readback_failed:{manifest_path}")
    os.replace(temporary, manifest_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check or synchronize merged source manifests.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()

    audits = []
    all_changes: list[dict[str, str]] = []
    all_errors: list[str] = []
    for path in manifest_paths():
        payload, changes, errors = audit_manifest(path)
        audits.append((path, payload, changes, errors))
        all_changes.extend(changes)
        all_errors.extend(errors)

    if args.write and not all_errors:
        for path, payload, changes, _ in audits:
            if changes:
                write_manifest(path, payload, changes)

    status = "CLEAN_PASS" if not all_errors and (args.write or not all_changes) else "BLOCKED"
    result = {
        "schema": "MERGED_SKILL_SOURCE_MANIFEST_SYNC_V1",
        "status": status,
        "mode": "write" if args.write else "check",
        "manifest_count": len(audits),
        "source_count": sum(len(payload.get("sources", [])) for _, payload, _, _ in audits),
        "listed_file_count": sum(
            sum(len(rows) for rows in payload.get("files", {}).values())
            for _, payload, _, _ in audits
        ),
        "changed_hash_count": len(all_changes),
        "error_count": len(all_errors),
        "changes": all_changes,
        "errors": all_errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
