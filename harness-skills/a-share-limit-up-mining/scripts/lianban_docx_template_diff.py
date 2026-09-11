#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare a Lianban delivered DOCX against the approved DOCX template.

The script reads the DOCX package directly and reports table structure,
header text, shading fills, and early title typography. It is intentionally
stdlib-only so the gate can run on the Codex host without Office.
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DYNAMIC_ROW_TABLES = {2} | set(range(4, 18)) | {18, 19}
EXPECTED_STYLE_FIELDS = {"header_fills", "first_data_fills", "unique_fills"}


def normalized_headers(values: list[str]) -> list[str]:
    return [re.sub(r"[A-Za-z]+", "", value) for value in values]


def attr(node: ET.Element | None, name: str) -> str:
    if node is None:
        return ""
    return node.attrib.get(W + name, "")


def text_of(node: ET.Element) -> str:
    return "".join(t.text or "" for t in node.findall(".//w:t", NS)).strip()


def paragraph_runs(p: ET.Element) -> list[dict[str, str]]:
    runs: list[dict[str, str]] = []
    for r in p.findall("w:r", NS):
        rpr = r.find("w:rPr", NS)
        text = "".join(t.text or "" for t in r.findall(".//w:t", NS))
        if not text:
            continue
        runs.append(
            {
                "text": text,
                "size_half_points": attr(rpr.find("w:sz", NS) if rpr is not None else None, "val"),
                "color": attr(rpr.find("w:color", NS) if rpr is not None else None, "val"),
                "font_east_asia": attr(rpr.find("w:rFonts", NS) if rpr is not None else None, "eastAsia"),
                "bold": "1" if rpr is not None and rpr.find("w:b", NS) is not None else "0",
            }
        )
    return runs


def para_style(p: ET.Element) -> str:
    ps = p.find("w:pPr/w:pStyle", NS)
    return attr(ps, "val")


def cell_signature(tc: ET.Element) -> dict[str, Any]:
    tcpr = tc.find("w:tcPr", NS)
    grid_span = ""
    vmerge = ""
    fill = ""
    if tcpr is not None:
        grid_span = attr(tcpr.find("w:gridSpan", NS), "val")
        vmerge = attr(tcpr.find("w:vMerge", NS), "val")
        fill = attr(tcpr.find("w:shd", NS), "fill")
    return {
        "text": text_of(tc),
        "fill": fill,
        "grid_span": grid_span,
        "vmerge": vmerge,
    }


def table_signature(tbl: ET.Element, index: int) -> dict[str, Any]:
    rows: list[list[dict[str, Any]]] = []
    for tr in tbl.findall("w:tr", NS):
        row = [cell_signature(tc) for tc in tr.findall("w:tc", NS)]
        if row:
            rows.append(row)
    row_lengths = [len(r) for r in rows]
    header = rows[0] if rows else []
    first_data = rows[1] if len(rows) > 1 else []
    fills = sorted({c["fill"] for r in rows for c in r if c.get("fill")})
    return {
        "index": index,
        "rows": len(rows),
        "cols_max": max(row_lengths) if row_lengths else 0,
        "row_lengths": row_lengths,
        "header_texts": [c["text"] for c in header],
        "header_fills": [c["fill"] for c in header],
        "first_data_fills": [c["fill"] for c in first_data],
        "unique_fills": fills,
    }


def load_docx(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    body = root.find("w:body", NS)
    top_paras: list[dict[str, Any]] = []
    if body is not None:
        for child in body:
            if child.tag == W + "p":
                txt = text_of(child)
                if txt:
                    top_paras.append(
                        {
                            "text": txt,
                            "style": para_style(child),
                            "runs": paragraph_runs(child),
                        }
                    )
            elif child.tag == W + "tbl":
                if len(top_paras) >= 12:
                    break
    tables = [table_signature(tbl, i + 1) for i, tbl in enumerate(root.findall(".//w:tbl", NS))]
    return {
        "path": str(path),
        "size": path.stat().st_size,
        "top_paragraphs": top_paras[:12],
        "tables": tables,
        "table_count": len(tables),
    }


def table_diff(template: dict[str, Any], output: dict[str, Any]) -> list[dict[str, Any]]:
    diffs: list[dict[str, Any]] = []
    output_pool = list(output["tables"])
    for t in template["tables"]:
        table_number = t["index"]
        match_at = next(
            (
                i for i, candidate in enumerate(output_pool)
                if normalized_headers(candidate["header_texts"]) == normalized_headers(t["header_texts"])
                and candidate["cols_max"] == t["cols_max"]
            ),
            None,
        )
        o = output_pool.pop(match_at) if match_at is not None else None
        item: dict[str, Any] = {"table": table_number, "status": "MATCH", "differences": []}
        if o is None:
            item["status"] = "MISSING_OUTPUT_TABLE"
            item["template"] = t
            diffs.append(item)
            continue
        checks = [
            ("rows", t["rows"], o["rows"]),
            ("cols_max", t["cols_max"], o["cols_max"]),
            ("row_lengths", t["row_lengths"], o["row_lengths"]),
            ("header_texts", t["header_texts"], o["header_texts"]),
            ("header_fills", t["header_fills"], o["header_fills"]),
            ("first_data_fills", t["first_data_fills"], o["first_data_fills"]),
            ("unique_fills", t["unique_fills"], o["unique_fills"]),
        ]
        for field, expected, actual in checks:
            if expected != actual:
                expected_dynamic = table_number in DYNAMIC_ROW_TABLES and field in {"rows", "row_lengths"}
                expected_style = field in EXPECTED_STYLE_FIELDS
                expected_header = (
                    field == "header_texts"
                    and normalized_headers(expected) == normalized_headers(actual)
                )
                if (expected_dynamic or expected_header) and item["status"] in {"MATCH", "EXPECTED_STYLE_CHANGE"}:
                    item["status"] = "EXPECTED_CONTENT_CHANGE"
                elif expected_style and item["status"] == "MATCH":
                    item["status"] = "EXPECTED_STYLE_CHANGE"
                elif not expected_dynamic and not expected_style and not expected_header:
                    item["status"] = "STRUCTURAL_DIFFERENT"
                item["differences"].append({
                    "field": field,
                    "template": expected,
                    "output": actual,
                    "expected_dynamic": expected_dynamic,
                    "expected_style": expected_style,
                    "expected_header": expected_header,
                })
        diffs.append(item)
    for o in output_pool:
        diffs.append({
            "table": o.get("index"),
            "status": "EXTRA_OUTPUT_TABLE",
            "differences": [],
            "output": o,
        })
    return diffs


def title_diff(template: dict[str, Any], output: dict[str, Any]) -> list[dict[str, Any]]:
    diffs: list[dict[str, Any]] = []
    for i in range(max(len(template["top_paragraphs"]), len(output["top_paragraphs"]), 4)):
        if i >= 8:
            break
        t = template["top_paragraphs"][i] if i < len(template["top_paragraphs"]) else None
        o = output["top_paragraphs"][i] if i < len(output["top_paragraphs"]) else None
        if t != o:
            diffs.append({"paragraph": i + 1, "template": t, "output": o})
    return diffs


def render_md(result: dict[str, Any]) -> str:
    lines = [
        "# 连板挖掘 Word 模板差异取证报告",
        "",
        "## 文件",
        f"- 模板: `{result['template']['path']}` size={result['template']['size']}",
        f"- 产物: `{result['output']['path']}` size={result['output']['size']}",
        "",
        "## 总览",
        f"- 模板表格数: {result['template']['table_count']}",
        f"- 产物表格数: {result['output']['table_count']}",
        f"- 预期动态表变化: {result['summary']['expected_dynamic_tables']}",
        f"- 预期样式表变化: {result['summary']['expected_style_tables']}",
        f"- 结构漂移表格: {result['summary']['structural_drift_tables']}",
        f"- 缺失表格: {result['summary']['missing_tables']}",
        f"- 额外表格: {result['summary']['extra_tables']}",
        f"- 标题/开篇段落差异: {len(result['title_diffs'])}",
        "",
        "## 标题与开篇段落差异",
    ]
    for item in result["title_diffs"]:
        lines.append(f"### Paragraph {item['paragraph']}")
        lines.append(f"- 模板: `{json.dumps(item['template'], ensure_ascii=False)}`")
        lines.append(f"- 产物: `{json.dumps(item['output'], ensure_ascii=False)}`")
    lines.extend(["", "## 逐表差异"])
    for item in result["table_diffs"]:
        if item["status"] == "MATCH":
            lines.append(f"### Table {item['table']} - MATCH")
            continue
        lines.append(f"### Table {item['table']} - {item['status']}")
        if item["status"] in {"MISSING_OUTPUT_TABLE", "EXTRA_OUTPUT_TABLE"}:
            lines.append(f"```json\n{json.dumps(item, ensure_ascii=False, indent=2)}\n```")
            continue
        for diff in item["differences"]:
            lines.append(f"- `{diff['field']}`")
            lines.append(f"  - 模板: `{json.dumps(diff['template'], ensure_ascii=False)}`")
            lines.append(f"  - 产物: `{json.dumps(diff['output'], ensure_ascii=False)}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--md-out", required=True)
    args = parser.parse_args()

    template = load_docx(Path(args.template))
    output = load_docx(Path(args.output))
    table_diffs = table_diff(template, output)
    title_diffs = title_diff(template, output)
    result = {
        "status": "CLEAN_PASS" if not any(
            item["status"] in {"MISSING_OUTPUT_TABLE", "EXTRA_OUTPUT_TABLE", "STRUCTURAL_DIFFERENT"}
            for item in table_diffs
        ) else "BLOCKED",
        "template": template,
        "output": output,
        "title_diffs": title_diffs,
        "table_diffs": table_diffs,
        "summary": {
            "different_tables": sum(1 for item in table_diffs if item["status"] != "MATCH"),
            "expected_dynamic_tables": sum(1 for item in table_diffs if item["status"] == "EXPECTED_CONTENT_CHANGE"),
            "expected_style_tables": sum(1 for item in table_diffs if item["status"] == "EXPECTED_STYLE_CHANGE"),
            "structural_drift_tables": sum(1 for item in table_diffs if item["status"] == "STRUCTURAL_DIFFERENT"),
            "missing_tables": sum(1 for item in table_diffs if item["status"] == "MISSING_OUTPUT_TABLE"),
            "extra_tables": sum(1 for item in table_diffs if item["status"] == "EXTRA_OUTPUT_TABLE"),
        },
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md_out.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({"status": result["status"], "json": str(json_out), "md": str(md_out), "summary": result["summary"]}, ensure_ascii=False))
    return 0 if result["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
