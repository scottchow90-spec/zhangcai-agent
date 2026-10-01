#!/usr/bin/env python3
"""Validate an 8K limit-up-review poster and its layout audit."""
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
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--poster", required=True)
    parser.add_argument("--audit-json", required=True)
    parser.add_argument("--report-json", required=True)
    args = parser.parse_args()

    poster_path = Path(args.poster).resolve()
    audit_path = Path(args.audit_json).resolve()
    report_path = Path(args.report_json).resolve()
    errors: list[str] = []

    try:
        audit: dict[str, Any] = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        audit = {}
        errors.append(f"audit_unreadable:{type(exc).__name__}")

    if audit.get("schema") != "LIMIT_UP_REVIEW_POSTER_AUDIT_V1":
        errors.append("audit_schema_invalid")
    if audit.get("status") != "CLEAN_PASS":
        errors.append("audit_status_not_clean")
    if audit.get("errors"):
        errors.append("audit_contains_errors")

    if not poster_path.is_file():
        errors.append("poster_missing")
    if not report_path.is_file():
        errors.append("business_result_missing")
    if poster_path.is_file() and audit.get("poster", {}).get("sha256") != sha256_file(poster_path):
        errors.append("poster_hash_mismatch")

    image_info: dict[str, Any] = {}
    if poster_path.is_file():
        with Image.open(poster_path) as image:
            image.load()
            image_info = {
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "format": image.format,
                "mean_rgb": [round(value, 2) for value in ImageStat.Stat(image.convert("RGB")).mean],
            }
            if image.size != (7680, 4320):
                errors.append("poster_size_invalid")
            if image.format != "PNG":
                errors.append("poster_format_invalid")
            if image.mode not in {"RGB", "RGBA"}:
                errors.append("poster_mode_invalid")
            if image.getbbox() is None:
                errors.append("poster_blank")
            if image.info.get("poster_schema") != "LIMIT_UP_REVIEW_POSTER_V1":
                errors.append("poster_metadata_schema_invalid")
            if report_path.is_file() and image.info.get("business_result_sha256") != sha256_file(report_path):
                errors.append("poster_business_result_hash_mismatch")

    policy = audit.get("font_policy", {})
    body_min = int(policy.get("body_min_px", 0))
    secondary_min = int(policy.get("secondary_min_px", 0))
    if body_min < 96:
        errors.append("body_font_policy_below_96")
    if secondary_min < 72:
        errors.append("secondary_font_policy_below_72")

    records = audit.get("text_records")
    if not isinstance(records, list) or not records:
        errors.append("text_records_missing")
        records = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"text_record_invalid:{index}")
            continue
        role = str(record.get("role", "body"))
        size = int(record.get("font_px", 0))
        minimum = secondary_min if role == "secondary" else body_min
        if size < minimum:
            errors.append(f"text_font_too_small:{index}:{size}<{minimum}")
        bbox = record.get("bbox")
        if not (
            isinstance(bbox, list)
            and len(bbox) == 4
            and all(isinstance(value, (int, float)) for value in bbox)
        ):
            errors.append(f"text_bbox_invalid:{index}")
            continue
        left, top, right, bottom = bbox
        if left < 0 or top < 0 or right > 7680 or bottom > 4320:
            errors.append(f"text_out_of_canvas:{index}:{bbox}")
        if right <= left or bottom <= top:
            errors.append(f"text_bbox_empty:{index}")
        if top < 4160 < bottom:
            errors.append(f"text_overlaps_footer:{index}:{bbox}")
        if left >= 5000 and 1540 <= top < 3200 and bottom > 3190:
            errors.append(f"text_exits_main_panel:{index}:{bbox}")

    result = {
        "schema": "LIMIT_UP_REVIEW_POSTER_VALIDATION_V1",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "poster": {
            "path": str(poster_path),
            "size": poster_path.stat().st_size if poster_path.is_file() else None,
            "sha256": sha256_file(poster_path) if poster_path.is_file() else None,
        },
        "audit": {
            "path": str(audit_path),
            "sha256": sha256_file(audit_path) if audit_path.is_file() else None,
        },
        "business_result": {
            "path": str(report_path),
            "sha256": sha256_file(report_path) if report_path.is_file() else None,
        },
        "image": image_info,
        "text_record_count": len(records),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
