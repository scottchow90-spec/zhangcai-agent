#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
from pathlib import Path

from PIL import Image, ImageStat


WIDTH = 7680
HEIGHT = 4320
EXPECTED_CATEGORIES = {
    "监管与退市",
    "偿债与司法",
    "财务与经营",
    "担保质押与资本",
    "票据欠薪与失信",
    "市场与舆情",
}
EXPECTED_OUTPUT_LEVELS = {"硬剔除", "前置核查", "票据历史异常", "市场观察"}


def image_light_metrics(image: Image.Image) -> dict[str, float]:
    sample = image.convert("RGB").resize((384, 216), Image.Resampling.BILINEAR)
    pixels = list(sample.get_flattened_data())
    luminance = [0.2126 * red + 0.7152 * green + 0.0722 * blue for red, green, blue in pixels]
    corners = (
        sample.getpixel((0, 0)),
        sample.getpixel((383, 0)),
        sample.getpixel((0, 215)),
        sample.getpixel((383, 215)),
    )
    corner_luminance = [
        0.2126 * red + 0.7152 * green + 0.0722 * blue for red, green, blue in corners
    ]
    return {
        "mean_luminance": sum(luminance) / len(luminance),
        "light_pixel_ratio": sum(value >= 190 for value in luminance) / len(luminance),
        "dark_pixel_ratio": sum(value <= 70 for value in luminance) / len(luminance),
        "minimum_corner_luminance": min(corner_luminance),
        "mean_rgb": sum(ImageStat.Stat(sample).mean) / 3,
    }


def text_layout_errors(metadata: dict[str, object]) -> list[str]:
    errors: list[str] = []
    runs = metadata.get("text_runs")
    if not isinstance(runs, list) or not runs:
        return ["text_runs_missing"]
    for index, run in enumerate(runs):
        if not isinstance(run, dict):
            errors.append(f"text_run_invalid:{index}")
            continue
        size = float(run.get("font_px", 0))
        role = str(run.get("role", ""))
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
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验风险排雷技能8K海报")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    poster = args.input.resolve()
    metadata_path = args.metadata.resolve()
    if not poster.is_file():
        errors.append(f"poster_missing:{poster}")
    if not metadata_path.is_file():
        errors.append(f"metadata_missing:{metadata_path}")

    metadata: dict[str, object] = {}
    metrics: dict[str, float] = {}
    if not errors:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        with Image.open(poster) as image:
            if image.size != (WIDTH, HEIGHT):
                errors.append(f"poster_dimensions_invalid:{image.size}")
            metrics = image_light_metrics(image)

        if metadata.get("schema") != "RISK_MINE_CLEARANCE_POSTER_V1":
            errors.append("poster_metadata_schema_invalid")
        if set(metadata.get("categories", [])) != EXPECTED_CATEGORIES:
            errors.append("poster_categories_incomplete")
        if set(metadata.get("output_levels", [])) != EXPECTED_OUTPUT_LEVELS:
            errors.append("poster_output_levels_incomplete")
        if metadata.get("missing_glyphs") != []:
            errors.append("poster_missing_glyphs")
        errors.extend(text_layout_errors(metadata))

        if metrics.get("mean_luminance", 0) < 205:
            errors.append("poster_mean_luminance_too_low")
        if metrics.get("light_pixel_ratio", 0) < 0.70:
            errors.append("poster_light_pixel_ratio_too_low")
        if metrics.get("dark_pixel_ratio", 1) > 0.08:
            errors.append("poster_dark_pixel_ratio_too_high")
        if metrics.get("minimum_corner_luminance", 0) < 220:
            errors.append("poster_corner_background_too_dark")

    payload = {
        "schema": "RISK_MINE_CLEARANCE_POSTER_VALIDATION_V1",
        "status": "PASS" if not errors else "BLOCKED",
        "poster": str(poster),
        "metadata": str(metadata_path),
        "image_metrics": metrics,
        "font_gate": {
            "minimum_visible_source_px": 96,
            "minimum_body_source_px": 128,
            "minimum_primary_source_px": 136,
            "preview_scale": 0.25,
        },
        "errors": errors,
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
