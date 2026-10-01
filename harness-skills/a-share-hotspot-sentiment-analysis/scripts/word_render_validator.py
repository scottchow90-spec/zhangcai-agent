#!/usr/bin/env python3
"""Perform real Word pagination, PDF export and page-image delivery checks."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "word_render_probe.ps1"
AUDIT_NAME = "a_share_sentiment_word_render_audit.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _page_metrics(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        gray = image.convert("L")
        histogram = gray.histogram()
        pixels = max(1, gray.width * gray.height)
        nonwhite = sum(histogram[:246])
        bottom_height = max(8, round(gray.height * 0.012))
        bottom = gray.crop((0, gray.height - bottom_height, gray.width, gray.height))
        bottom_histogram = bottom.histogram()
        bottom_pixels = max(1, bottom.width * bottom.height)
        bottom_nonwhite = sum(bottom_histogram[:246])
        return {
            "width": gray.width,
            "height": gray.height,
            "nonwhite_ratio": round(nonwhite / pixels, 6),
            "bottom_edge_nonwhite_ratio": round(bottom_nonwhite / bottom_pixels, 6),
        }


def _contact_sheet(page_paths: list[Path], output: Path) -> None:
    thumbnails = []
    for path in page_paths:
        with Image.open(path) as page:
            image = page.convert("RGB")
            image.thumbnail((460, 650), Image.Resampling.LANCZOS)
            thumbnails.append(image.copy())
    columns = 2
    gap = 18
    label_height = 28
    cell_width = 460
    cell_height = max(image.height for image in thumbnails) + label_height
    rows = (len(thumbnails) + columns - 1) // columns
    canvas = Image.new(
        "RGB",
        (columns * cell_width + (columns + 1) * gap, rows * cell_height + (rows + 1) * gap),
        "#e7ebef",
    )
    draw = ImageDraw.Draw(canvas)
    for index, image in enumerate(thumbnails):
        row, column = divmod(index, columns)
        x = gap + column * (cell_width + gap)
        y = gap + row * (cell_height + gap)
        draw.rectangle((x, y, x + cell_width, y + label_height), fill="#243746")
        draw.text((x + 10, y + 7), f"Page {index + 1}", fill="white")
        canvas.paste(image, (x, y + label_height))
    canvas.save(output, "JPEG", quality=78, optimize=True, progressive=True)


def validate(docx: Path, output: Path, render_dir: Path, pdf_path: Path) -> tuple[int, dict[str, Any]]:
    errors: list[str] = []
    probe_path = output.with_name("a_share_sentiment_word_probe.json")
    if not docx.is_file():
        errors.append("docx_missing")
    if not PROBE.is_file():
        errors.append("word_probe_missing")
    probe: dict[str, Any] = {}
    if not errors:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(PROBE),
                "-DocxPath",
                str(docx),
                "-PdfPath",
                str(pdf_path),
                "-ResultPath",
                str(probe_path),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        if probe_path.is_file():
            probe = json.loads(probe_path.read_text(encoding="utf-8-sig"))
        if completed.returncode != 0 or probe.get("status") != "PASS":
            errors.append("word_probe_failed")
            errors.extend(str(value) for value in probe.get("errors", []) if str(value))

    page_records: list[dict[str, Any]] = []
    contact_path = render_dir / "contact-all-pages.jpg"
    pdftoppm = shutil.which("pdftoppm")
    if not errors:
        if not pdftoppm:
            errors.append("pdftoppm_missing")
        else:
            render_dir.mkdir(parents=True, exist_ok=True)
            completed = subprocess.run(
                [pdftoppm, "-png", "-r", "120", str(pdf_path), str(render_dir / "page")],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
            )
            if completed.returncode != 0:
                errors.append("pdf_page_render_failed")
            page_paths = sorted(render_dir.glob("page-*.png"))
            if len(page_paths) != int(probe.get("word_pages", 0) or 0):
                errors.append("word_pdf_page_count_mismatch")
            for page_number, path in enumerate(page_paths, 1):
                metrics = _page_metrics(path)
                if metrics["nonwhite_ratio"] < 0.004:
                    errors.append(f"blank_page:{page_number}")
                if metrics["bottom_edge_nonwhite_ratio"] > 0.45:
                    errors.append(f"bottom_edge_overflow_risk:{page_number}")
                page_records.append({
                    "page": page_number,
                    **file_record(path),
                    **metrics,
                })
            if page_paths:
                _contact_sheet(page_paths, contact_path)

    status = "PASS" if not errors else "BLOCKED"
    payload = {
        "schema": "A_SHARE_SENTIMENT_WORD_RENDER_AUDIT_V1",
        "status": status,
        "report": file_record(docx) if docx.is_file() else None,
        "word_probe": probe,
        "pdf": file_record(pdf_path) if pdf_path.is_file() else None,
        "page_count": len(page_records),
        "pages": page_records,
        "contact_sheet": file_record(contact_path) if contact_path.is_file() else None,
        "checks": {
            "word_opened": probe.get("word_opened") is True,
            "word_page_count_valid": 1 <= int(probe.get("word_pages", 0) or 0) <= 50,
            "pdf_exported": probe.get("pdf_exported") is True and pdf_path.is_file(),
            "page_count_matches": len(page_records) == int(probe.get("word_pages", 0) or 0),
            "no_blank_pages": not any(error.startswith("blank_page:") for error in errors),
            "no_bottom_edge_overflow": not any(error.startswith("bottom_edge_overflow_risk:") for error in errors),
            "contact_sheet_created": contact_path.is_file(),
        },
        "errors": list(dict.fromkeys(errors)),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return (0 if not errors else 2), payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--render-dir", required=True)
    parser.add_argument("--pdf", required=True)
    args = parser.parse_args()
    code, payload = validate(
        Path(args.docx).resolve(),
        Path(args.output).resolve(),
        Path(args.render_dir).resolve(),
        Path(args.pdf).resolve(),
    )
    print(json.dumps(payload, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

