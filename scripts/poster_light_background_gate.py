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
from typing import Any

from PIL import Image, ImageStat


SCHEMA = "POSTER_LIGHT_BACKGROUND_GATE_V1"
DEFAULT_EXPECTED_SIZE = (7680, 4320)
MIN_MEAN_LUMINANCE = 205.0
MIN_LIGHT_PIXEL_RATIO = 0.70
MAX_DARK_PIXEL_RATIO = 0.12
MIN_CORNER_LUMINANCE = 230.0


def _corner_luminance(image: Image.Image) -> list[float]:
    width, height = image.size
    edge = max(1, min(width, height) // 20)
    boxes = [
        (0, 0, edge, edge),
        (width - edge, 0, width, edge),
        (0, height - edge, edge, height),
        (width - edge, height - edge, width, height),
    ]
    return [round(ImageStat.Stat(image.crop(box).convert("L")).mean[0], 2) for box in boxes]


def validate_poster_file(
    path: str | Path,
    *,
    expected_size: tuple[int, int] = DEFAULT_EXPECTED_SIZE,
) -> dict[str, Any]:
    target = Path(path)
    failures: list[str] = []
    if not target.is_file():
        return {
            "schema": SCHEMA,
            "status": "BLOCKED",
            "path": str(target),
            "expected_size": list(expected_size),
            "actual_size": None,
            "thresholds": {},
            "metrics": {},
            "failures": ["poster_file_missing"],
        }

    try:
        with Image.open(target) as source:
            image = source.convert("RGB")
    except Exception as exc:
        return {
            "schema": SCHEMA,
            "status": "BLOCKED",
            "path": str(target),
            "expected_size": list(expected_size),
            "actual_size": None,
            "thresholds": {},
            "metrics": {},
            "failures": [f"poster_unreadable:{type(exc).__name__}"],
        }

    if image.size != expected_size:
        failures.append(f"dimensions_not_{expected_size[0]}x{expected_size[1]}")

    sample = image.resize((320, 180), Image.Resampling.BOX).convert("L")
    histogram = sample.histogram()
    pixel_count = sample.width * sample.height
    mean_luminance = round(ImageStat.Stat(sample).mean[0], 2)
    light_ratio = round(sum(histogram[200:]) / pixel_count, 6)
    dark_ratio = round(sum(histogram[:80]) / pixel_count, 6)
    corner_luminance = _corner_luminance(image)
    minimum_corner = min(corner_luminance)

    if mean_luminance < MIN_MEAN_LUMINANCE:
        failures.append("mean_luminance_below_205")
    if light_ratio < MIN_LIGHT_PIXEL_RATIO:
        failures.append("light_pixel_ratio_below_0.70")
    if dark_ratio > MAX_DARK_PIXEL_RATIO:
        failures.append("dark_pixel_ratio_above_0.12")
    if minimum_corner < MIN_CORNER_LUMINANCE:
        failures.append("corner_background_luminance_below_230")

    return {
        "schema": SCHEMA,
        "status": "PASS" if not failures else "BLOCKED",
        "path": str(target),
        "expected_size": list(expected_size),
        "actual_size": list(image.size),
        "thresholds": {
            "minimum_mean_luminance": MIN_MEAN_LUMINANCE,
            "minimum_light_pixel_ratio": MIN_LIGHT_PIXEL_RATIO,
            "maximum_dark_pixel_ratio": MAX_DARK_PIXEL_RATIO,
            "minimum_corner_luminance": MIN_CORNER_LUMINANCE,
        },
        "metrics": {
            "mean_luminance": mean_luminance,
            "light_pixel_ratio": light_ratio,
            "dark_pixel_ratio": dark_ratio,
            "corner_luminance": corner_luminance,
            "minimum_corner_luminance": minimum_corner,
        },
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="4K/8K海报浅色背景交付硬闸")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--expected-width", type=int, default=7680)
    parser.add_argument("--expected-height", type=int, default=4320)
    args = parser.parse_args()
    result = validate_poster_file(
        args.input,
        expected_size=(args.expected_width, args.expected_height),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
