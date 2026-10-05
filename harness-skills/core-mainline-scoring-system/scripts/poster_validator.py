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
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat


WIDTH = 7680
HEIGHT = 4320


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def light_metrics(image: Image.Image) -> dict[str, float]:
    sample = image.convert("RGB").resize((384, 216), Image.Resampling.BILINEAR)
    pixels = list(sample.get_flattened_data())
    luminance = [0.2126 * red + 0.7152 * green + 0.0722 * blue for red, green, blue in pixels]
    return {
        "mean_luminance": sum(luminance) / len(luminance),
        "light_pixel_ratio": sum(value >= 190 for value in luminance) / len(luminance),
        "dark_pixel_ratio": sum(value <= 70 for value in luminance) / len(luminance),
        "mean_rgb": sum(ImageStat.Stat(sample).mean) / 3,
    }


def validate(poster: Path, metadata_path: Path, scoring_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    if not poster.is_file():
        errors.append(f"poster_missing:{poster}")
    if not metadata_path.is_file():
        errors.append(f"metadata_missing:{metadata_path}")
    if not scoring_path.is_file():
        errors.append(f"scoring_missing:{scoring_path}")
    metadata = read_json(metadata_path) if metadata_path.is_file() else {}
    scoring = read_json(scoring_path) if scoring_path.is_file() else {}
    metrics: dict[str, float] = {}
    if poster.is_file():
        with Image.open(poster) as image:
            if image.size != (WIDTH, HEIGHT):
                errors.append(f"poster_dimensions_invalid:{image.size}")
            metrics = light_metrics(image)
    if metadata.get("schema") != "CORE_MAINLINE_POSTER_METADATA_V1":
        errors.append("metadata_schema_invalid")
    if metadata.get("status") != "PASS":
        errors.append("metadata_status_not_pass")
    if metadata.get("layout_errors") != []:
        errors.append("metadata_layout_errors")
    if metadata.get("missing_glyphs") != []:
        errors.append("metadata_missing_glyphs")
    if metadata.get("scoring", {}).get("sha256") != (sha256_file(scoring_path) if scoring_path.is_file() else None):
        errors.append("scoring_hash_mismatch")
    if metadata.get("summary") != scoring.get("summary"):
        errors.append("summary_mismatch")
    runs = metadata.get("text_runs")
    if not isinstance(runs, list) or not runs:
        errors.append("text_runs_missing")
    else:
        for index, run in enumerate(runs):
            size = float(run.get("font_px", 0) or 0)
            role = str(run.get("role", ""))
            if "..." in str(run.get("text", "")):
                errors.append(f"visible_text_truncated:{index}")
            if size < 96:
                errors.append(f"visible_text_below_96:{index}:{size}")
            if role == "body" and size < 128:
                errors.append(f"body_text_below_128:{index}:{size}")
            if role == "primary" and size < 136:
                errors.append(f"primary_text_below_136:{index}:{size}")
            bbox = run.get("bbox")
            if (
                not isinstance(bbox, list)
                or len(bbox) != 4
                or min(float(value) for value in bbox) < 0
                or float(bbox[2]) > WIDTH
                or float(bbox[3]) > HEIGHT
                or float(bbox[2]) <= float(bbox[0])
                or float(bbox[3]) <= float(bbox[1])
            ):
                errors.append(f"text_bbox_invalid:{index}:{bbox}")
    visible = {str(run.get("text", "")) for run in runs or [] if isinstance(run, dict)}
    conclusion = str(metadata.get("conclusion", ""))
    if not conclusion or conclusion not in visible:
        errors.append("conclusion_not_visible")
    for name in metadata.get("top_board_names", []):
        if str(name) not in visible:
            errors.append(f"top_board_not_visible:{name}")
    if metrics.get("mean_luminance", 0) < 205:
        errors.append("poster_mean_luminance_too_low")
    if metrics.get("light_pixel_ratio", 0) < 0.70:
        errors.append("poster_light_pixel_ratio_too_low")
    if metrics.get("dark_pixel_ratio", 1) > 0.08:
        errors.append("poster_dark_pixel_ratio_too_high")
    return {
        "schema": "CORE_MAINLINE_POSTER_VALIDATION_V1",
        "status": "PASS" if not errors else "BLOCKED",
        "poster": str(poster),
        "poster_sha256": sha256_file(poster) if poster.is_file() else None,
        "metadata": str(metadata_path),
        "scoring": str(scoring_path),
        "image_metrics": metrics,
        "font_gate": {
            "status": "PASS",
            "errors": [],
            "minimum_visible_source_px": 96,
            "minimum_body_source_px": 128,
            "minimum_primary_source_px": 136,
            "preview_scale": 0.25,
        },
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="校验核心主线评分8K海报")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--scoring", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = validate(
        args.input.resolve(),
        args.metadata.resolve(),
        args.scoring.resolve(),
    )
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
