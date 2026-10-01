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
import subprocess
from pathlib import Path

from pdf2image import convert_from_path, pdfinfo_from_path


POPPLER_BIN = (
    Path.home()
    / ".cache"
    / "codex-runtimes"
    / "codex-primary-runtime"
    / "dependencies"
    / "native"
    / "poppler"
    / "Library"
    / "bin"
)


def ps_literal(value: str) -> str:
    return value.replace("'", "''")


def word_com_compatible_path(path: Path) -> str:
    """Return a Win32 path accepted by Word COM and Poppler subprocesses."""
    value = str(path)
    unc_prefix = "\\\\?\\UNC\\"
    extended_prefix = "\\\\?\\"
    if value.casefold().startswith(unc_prefix.casefold()):
        return "\\\\" + value[len(unc_prefix) :]
    if value.startswith(extended_prefix):
        return value[len(extended_prefix) :]
    return value


def export_with_word(docx_path: Path, pdf_path: Path) -> dict:
    word_docx_path = word_com_compatible_path(docx_path)
    word_pdf_path = word_com_compatible_path(pdf_path)
    script = f"""
$ErrorActionPreference = 'Stop'
$word = $null
$doc = $null
try {{
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open('{ps_literal(word_docx_path)}', $false, $true)
    $pages = $doc.ComputeStatistics(2)
    $doc.ExportAsFixedFormat('{ps_literal(word_pdf_path)}', 17)
    [pscustomobject]@{{
        status = 'PASS'
        pages = $pages
        pdf = '{ps_literal(word_pdf_path)}'
    }} | ConvertTo-Json -Compress
}}
finally {{
    if ($doc -ne $null) {{
        $doc.Close(0)
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($doc)
    }}
    if ($word -ne $null) {{
        $word.Quit()
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)
    }}
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}}
"""
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"word_com_export_failed:rc={completed.returncode}:"
            f"stderr={completed.stderr[-1000:]}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("word_com_export_missing_result")
    result = json.loads(lines[-1])
    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        raise RuntimeError("word_com_pdf_missing")
    return result


def rasterize(pdf_path: Path, output_dir: Path) -> list[Path]:
    if not POPPLER_BIN.is_dir():
        raise RuntimeError(f"poppler_missing:{POPPLER_BIN}")
    subprocess_pdf_path = word_com_compatible_path(pdf_path)
    info = pdfinfo_from_path(subprocess_pdf_path, poppler_path=str(POPPLER_BIN))
    expected_pages = int(info.get("Pages") or 0)
    images = convert_from_path(
        subprocess_pdf_path,
        dpi=150,
        fmt="png",
        poppler_path=str(POPPLER_BIN),
        thread_count=2,
    )
    if expected_pages <= 0 or len(images) != expected_pages:
        raise RuntimeError(
            f"pdf_page_count_mismatch:expected={expected_pages}:actual={len(images)}"
        )
    pages = []
    for index, image in enumerate(images, start=1):
        page_path = output_dir / f"page-{index}.png"
        image.save(page_path, "PNG")
        pages.append(page_path)
    return pages


def main() -> int:
    parser = argparse.ArgumentParser(description="使用 Microsoft Word 重开 DOCX 并导出逐页图")
    parser.add_argument("docx", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    docx_path = args.docx.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{docx_path.stem}.pdf"
    word_result = export_with_word(docx_path, pdf_path)
    pages = rasterize(pdf_path, output_dir)
    result = {
        "status": "PASS",
        "renderer": "microsoft_word_com",
        "docx": str(docx_path),
        "pdf": str(pdf_path),
        "word_page_count": int(word_result["pages"]),
        "render_page_count": len(pages),
        "pages": [str(path) for path in pages],
    }
    if result["word_page_count"] != result["render_page_count"]:
        result["status"] = "BLOCKED"
        result["error"] = "word_pdf_page_count_mismatch"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
