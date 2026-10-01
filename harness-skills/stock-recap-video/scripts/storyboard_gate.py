#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "stock-recap-storyboard-receipt.v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_storyboard(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [f"storyboard_unreadable:{type(exc).__name__}:{exc}"]
    if data.get("schema") != "stock-recap-storyboard.v1":
        errors.append("storyboard_schema_invalid")
    if len(str(data.get("art_direction") or "").strip()) < 20:
        errors.append("art_direction_too_short")
    fmt = data.get("format") if isinstance(data.get("format"), dict) else {}
    if (fmt.get("width"), fmt.get("height"), fmt.get("fps"), fmt.get("duration_frames")) != (1080, 1920, 30, 2100):
        errors.append("format_contract_invalid")
    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    if len(scenes) < 5:
        errors.append("at_least_five_business_scenes_required")
    ids: list[str] = []
    grammars: list[str] = []
    duration_sum = 0
    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            errors.append(f"scene_{index}:not_object")
            continue
        scene_id = str(scene.get("id") or "").strip()
        grammar = str(scene.get("visual_grammar") or "").strip()
        ids.append(scene_id)
        grammars.append(grammar)
        duration_sum += int(scene.get("duration_frames") or 0)
        if not scene_id or not str(scene.get("purpose") or "").strip() or not str(scene.get("focal") or "").strip():
            errors.append(f"scene_{index}:identity_or_purpose_missing")
        if len(grammar) < 8:
            errors.append(f"scene_{index}:visual_grammar_missing")
        layers = scene.get("motion_layers") if isinstance(scene.get("motion_layers"), list) else []
        if len({str(item).strip() for item in layers if str(item).strip()}) < 3:
            errors.append(f"scene_{index}:three_motion_layers_required")
        if not str(scene.get("transition") or "").strip():
            errors.append(f"scene_{index}:transition_missing")
        if int(scene.get("duration_frames") or 0) < 240:
            errors.append(f"scene_{index}:duration_too_short")
    if len(set(ids)) != len(ids):
        errors.append("scene_ids_not_unique")
    if len(set(grammars)) != len(grammars):
        errors.append("visual_grammars_not_distinct")
    if duration_sum < 1950:
        errors.append("business_duration_not_covered")
    return errors


def prepare(project: Path, receipt: Path) -> dict:
    project = project.resolve()
    storyboard = project / "public" / "storyboard.json"
    errors = ["storyboard_missing"] if not storyboard.is_file() else validate_storyboard(storyboard)
    payload = {
        "schema": SCHEMA,
        "gate_sha256": sha256_file(Path(__file__)),
        "status": "PASS" if not errors else "FAIL",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": str(project),
        "storyboard": str(storyboard.resolve()),
        "storyboard_sha256": sha256_file(storyboard) if storyboard.is_file() else None,
        "storyboard_size_bytes": storyboard.stat().st_size if storyboard.is_file() else None,
        "errors": errors,
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def verify(project: Path, receipt: Path) -> dict:
    errors: list[str] = []
    try:
        payload = json.loads(receipt.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"status": "FAIL", "errors": [f"receipt_unreadable:{type(exc).__name__}:{exc}"]}
    storyboard = project.resolve() / "public" / "storyboard.json"
    if payload.get("schema") != SCHEMA or payload.get("gate_sha256") != sha256_file(Path(__file__)):
        errors.append("gate_version_or_hash_mismatch")
    if payload.get("status") != "PASS":
        errors.append("receipt_not_pass")
    if str(project.resolve()) != str(payload.get("project") or ""):
        errors.append("project_binding_mismatch")
    if not storyboard.is_file() or payload.get("storyboard_sha256") != sha256_file(storyboard) or payload.get("storyboard_size_bytes") != storyboard.stat().st_size:
        errors.append("storyboard_missing_or_hash_mismatch")
    errors.extend(validate_storyboard(storyboard) if storyboard.is_file() else [])
    return {"status": "PASS" if not errors else "FAIL", "receipt": str(receipt.resolve()), "storyboard": str(storyboard), "storyboard_sha256": payload.get("storyboard_sha256"), "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description="Storyboard and art-direction hard gate")
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("prepare"); make.add_argument("--project", required=True); make.add_argument("--receipt", required=True)
    check = sub.add_parser("verify"); check.add_argument("--project", required=True); check.add_argument("--receipt", required=True)
    args = parser.parse_args()
    result = prepare(Path(args.project), Path(args.receipt).resolve()) if args.command == "prepare" else verify(Path(args.project), Path(args.receipt).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
