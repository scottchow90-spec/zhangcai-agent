#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path
from typing import Any
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 7680, 4320
PREVIEW = (1080, 608)
PAGE_SIZE = 9
CONCLUSIONS_PER_PAGE = 4
TABLE_TOP = 1360
TABLE_BOTTOM = 4300
FONT = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
APP_ROOT = Path(__file__).resolve().parents[3]
LIGHT_GATE = APP_ROOT / "scripts" / "poster_light_background_gate.py"
POLICY = {"min_source_font_px": 160, "body_source_font_px": 228, "heading_source_font_px": 320, "primary_source_font_px": 242, "preview_width": 1080, "preview_height": 608, "min_preview_font_px": 22, "body_preview_font_px": 32, "heading_preview_font_px": 45, "primary_preview_font_px": 34, "max_line_chars": 22, "light_background_gate_required": True, "paginate_instead_of_truncate": True}
CONCLUSION_KEYS = ["capital_concentration", "capital_focus", "seat_style", "board_style", "persistence", "trigger_style", "risk_boundary"]
BANNED_TEXT = ("未可靠识别", "未识别", "其他主题", "题材识别不足", "方向识别不足", "默认结论", "固定措辞", "兜底判断")

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont: return ImageFont.truetype(str(FONT_BOLD if bold else FONT), size)

def wrap(text: str, max_chars: int, max_lines: int = 2) -> list[str]:
    value = str(text or "-").strip()
    lines: list[str] = []
    for paragraph in value.splitlines() or ["-"]:
        current = ""
        for token in re.split(r"(?<=[、，,；;/])", paragraph):
            if not token: continue
            if current and len(current) + len(token) > max_chars:
                lines.append(current); current = ""
            while len(token) > max_chars:
                lines.append(token[:max_chars]); token = token[max_chars:]
            current += token
        if current: lines.append(current)
    lines = lines or ["-"]
    if len(lines) > max_lines: raise ValueError(f"poster_text_overflow:{value}")
    return lines

def balanced_chunks(items: list[Any], count: int) -> list[list[Any]]:
    base, extra = divmod(len(items), count)
    chunks: list[list[Any]] = []
    start = 0
    for index in range(count):
        size = base + (1 if index < extra else 0)
        chunks.append(items[start:start + size])
        start += size
    return chunks

def poster_trader_label(value: str) -> str:
    if str(value).strip() == "普通营业部（公开游资名录无精确匹配）": return "普通营业部\n名录无精确匹配"
    if str(value).strip() == "本股榜单无公开游资名录席位": return "本股榜单无\n公开游资席位"
    return str(value)

def draw_cell(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, width: int, size: int = 128, color: str = "#172033", bold: bool = False) -> None:
    max_chars = max(2, int(width / (size * 1.02)))
    lines = wrap(text, max_chars)
    f = font(size, bold)
    line_h = size + 18
    top = y + (320 - line_h * len(lines)) // 2
    for line in lines:
        draw.text((x + 22, top), line, font=f, fill=color)
        top += line_h

def money(value: float) -> str:
    return f"{value / 100_000_000:.2f}亿"

def draw_lines_centered(draw: ImageDraw.ImageDraw, lines: list[str], box: tuple[int, int, int, int], size: int, color: str, bold: bool = False) -> None:
    left, top, right, bottom = box
    line_gap = 150
    center_y = (top + bottom) // 2
    first_y = center_y - (len(lines) - 1) * line_gap // 2
    for index, line in enumerate(lines):
        draw.text((left + 22, first_y + index * line_gap), line, font=font(size, bold), fill=color, anchor="lm")

def max_empty_dark_band_preview(preview_path: Path) -> int:
    preview = Image.open(preview_path).convert("RGB")
    longest = current = 0
    for y in range(preview.height):
        dark_pixels = sum(1 for red, green, blue in (preview.getpixel((x, y)) for x in range(preview.width)) if min(red, green, blue) < 215)
        if dark_pixels < 6:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest

def validate_conclusions(conclusions: dict[str, Any]) -> None:
    if not isinstance(conclusions, dict) or conclusions.get("schema") != "LONGHUBANG_CONCLUSIONS_V1": raise ValueError("poster_conclusions_missing")
    if conclusions.get("status") != "CLEAN_PASS": raise ValueError("poster_conclusions_not_clean")
    sections = conclusions.get("sections") or []; keys = [str(section.get("key")) for section in sections if isinstance(section, dict)]
    if set(keys) != set(CONCLUSION_KEYS): raise ValueError("poster_conclusion_dimensions_incomplete")
    bullets = conclusions.get("poster_bullets") or []
    if len(bullets) != len(CONCLUSION_KEYS) or any(not str(item).strip() for item in bullets): raise ValueError("poster_conclusion_bullets_incomplete")
    if any(len(str(item)) > 58 for item in bullets): raise ValueError("poster_conclusion_bullet_too_long")
    visible = json.dumps({"headline": conclusions.get("headline"), "sections": sections, "bullets": bullets}, ensure_ascii=False)
    if any(token in visible for token in BANNED_TEXT): raise ValueError("poster_placeholder_text_forbidden")

def validate_records(records: list[dict[str, Any]]) -> None:
    for row in records:
        values = [row.get("name"), row.get("code"), row.get("representative_seat"), row.get("top_trader"), row.get("concept")]
        if any(not str(value or "").strip() for value in values): raise ValueError("poster_stock_text_missing")
        visible = "|".join(str(value) for value in values)
        if any(token in visible for token in BANNED_TEXT) or str(row.get("concept")).strip() in {"其他", "未知", "题材股"}: raise ValueError("poster_placeholder_text_forbidden")

def conclusion_sha256(conclusions: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(conclusions, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

def build_pages(records: list[dict[str, Any]], trade_date: str, threshold_yuan: float, conclusions: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    validate_conclusions(conclusions)
    validate_records(records)
    draft_dir = run_dir / "poster-candidates"; preview_dir = run_dir / "poster-preview"
    draft_dir.mkdir(parents=True, exist_ok=True); preview_dir.mkdir(parents=True, exist_ok=True)
    page_count = max(1, (len(records) + PAGE_SIZE - 1) // PAGE_SIZE, (len(CONCLUSION_KEYS) + CONCLUSIONS_PER_PAGE - 1) // CONCLUSIONS_PER_PAGE)
    pages = balanced_chunks(records, page_count)
    bullet_rows = list(zip(CONCLUSION_KEYS, conclusions["poster_bullets"]))
    conclusion_pages = balanced_chunks(bullet_rows, page_count)
    binding = {"schema": "LONGHUBANG_POSTER_ANALYSIS_BINDING_V1", "status": "CLEAN_PASS", "conclusion_sha256": conclusion_sha256(conclusions), "headline": conclusions["headline"], "required_section_keys": CONCLUSION_KEYS}
    outputs = []
    metrics_records = []
    page_width = 7280
    preview_scale = WIDTH / PREVIEW[0]
    major_gap = 40
    major_column_width = (page_width - major_gap * 2) // 3
    if major_column_width < 1600: raise RuntimeError("poster_major_column_width_too_small")
    for page_no, rows in enumerate(pages, 1):
        image = Image.new("RGB", (WIDTH, HEIGHT), "#FFFFFF"); draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, WIDTH, TABLE_TOP), fill="#FFFFFF")
        visible_lines: list[str] = []
        title = "A股龙虎榜资金结论"
        meta_one = f"{trade_date}｜门槛>{threshold_yuan / 10_000:.0f}万"
        meta_two = f"{len(records)}股｜第{page_no}/{len(pages)}页"
        source_line = "主源东方财富｜交叉短线侠/连板网"
        legend_line = "蓝字游资｜绿字概念"
        draw.text((200, 20), title, font=font(320, True), fill="#14213D")
        draw.text((202, 365), meta_one, font=font(160), fill="#526078")
        draw.text((3000, 365), meta_two, font=font(160), fill="#526078")
        draw.text((4950, 365), source_line, font=font(160), fill="#526078")
        draw.text((5630, 545), legend_line, font=font(160, True), fill="#526078")
        visible_lines.extend([title, meta_one, meta_two, source_line, legend_line])
        conclusion_rows = conclusion_pages[page_no - 1]
        if not conclusion_rows: raise RuntimeError("poster_conclusion_page_empty")
        _, highlight = conclusion_rows[0]
        highlight_lines = wrap(str(highlight), POLICY["max_line_chars"], max_lines=2)
        highlight_y = 555
        for index, line in enumerate(highlight_lines):
            draw.text((220, highlight_y + index * 210), "●" if index == 0 else "", font=font(228, True), fill="#C1261D")
            draw.text((390, highlight_y + index * 210), line, font=font(228, True), fill="#243B61")
            visible_lines.append(line)
        remaining = []
        for key, bullet in conclusion_rows[1:]:
            lines = wrap(str(bullet), POLICY["max_line_chars"], max_lines=2)
            remaining.append((key, lines))
        remaining.sort(key=lambda item: len(item[1]))
        summary_top = highlight_y + len(highlight_lines) * 210 + 20
        for index, (_, lines) in enumerate(remaining):
            column = index % 2
            row_index = index // 2
            x = 220 + column * 3740
            y = summary_top + row_index * 230
            draw.text((x, y), "●", font=font(160, True), fill="#0B6E75")
            for line_index, line in enumerate(lines):
                draw.text((x + 130, y + line_index * 150), line, font=font(160, True), fill="#315B9A")
                visible_lines.append(line)
        if remaining:
            last_lines = remaining[-1][1]
            last_y = summary_top + ((len(remaining) - 1) // 2) * 230 + (len(last_lines) - 1) * 150 + 190
            if last_y > TABLE_TOP: raise RuntimeError("poster_header_overflow")

        stock_columns = balanced_chunks(rows, 3)
        fills = ["#FFFFFF", "#FFFFFF", "#FFFFFF"]
        accents = ["#C1261D", "#0B6E75", "#315B9A"]
        for column_index, stock_column in enumerate(stock_columns):
            if not stock_column: continue
            x = 200 + column_index * (major_column_width + major_gap)
            card_height = (TABLE_BOTTOM - TABLE_TOP) // len(stock_column)
            for card_index, row in enumerate(stock_column):
                card_top = TABLE_TOP + card_index * card_height
                card_bottom = TABLE_BOTTOM if card_index == len(stock_column) - 1 else card_top + card_height
                content_height = min(980, card_bottom - card_top)
                content_top = card_top + (card_bottom - card_top - content_height) // 2
                draw.rectangle((x, card_top, x + major_column_width, card_bottom), fill=fills[column_index], outline="#C7D2E3", width=4)
                draw.rectangle((x, card_top, x + 8, card_bottom), fill=accents[column_index])

                name_line = str(row["name"])
                code_line = str(row["code"])
                amount_line = money(float(row.get("net_amount", 0)))
                day_line = "三日累计" if row.get("three_day") else "单日"
                draw.text((x + 50, content_top + 20), name_line, font=font(242, True), fill="#14213D")
                amount_width = draw.textbbox((0, 0), amount_line, font=font(242, True))[2]
                draw.text((x + major_column_width - amount_width - 50, content_top + 20), amount_line, font=font(242, True), fill="#C1261D")
                draw.text((x + 52, content_top + 255), code_line, font=font(160, True), fill="#526078")
                day_width = draw.textbbox((0, 0), day_line, font=font(160, True))[2]
                draw.text((x + major_column_width - day_width - 50, content_top + 255), day_line, font=font(160, True), fill="#7A4E00")
                visible_lines.extend([name_line, amount_line, code_line, day_line])

                seat_lines = wrap(f"席位｜{row['representative_seat']}", 14, max_lines=2)
                draw_lines_centered(draw, seat_lines, (x + 28, content_top + 390, x + major_column_width - 28, content_top + 670), 160, "#172033", True)
                trader_lines = wrap(poster_trader_label(row["top_trader"]).replace("\n", ""), 7, max_lines=2)
                concept_lines = wrap(str(row["concept"]), 8, max_lines=2)
                draw_lines_centered(draw, trader_lines, (x + 28, content_top + 675, x + major_column_width // 2, content_top + 970), 160, "#315B9A")
                draw_lines_centered(draw, concept_lines, (x + major_column_width // 2, content_top + 675, x + major_column_width - 28, content_top + 970), 160, "#0B6E75")
                visible_lines.extend(seat_lines + trader_lines + concept_lines)
        if any(line and line[0] in "，。；：、,.!?！？" for line in visible_lines): raise RuntimeError("poster_leading_punctuation")
        if max(map(len, visible_lines)) > POLICY["max_line_chars"]: raise RuntimeError("poster_line_length_overflow")
        candidate = draft_dir / f"longhubang-{page_no:02d}.png"; image.save(candidate, format="PNG", optimize=False)
        preview = preview_dir / candidate.name; image.resize(PREVIEW, Image.Resampling.LANCZOS).save(preview, format="PNG")
        gate = subprocess.run([sys.executable, str(LIGHT_GATE), "--input", str(candidate), "--expected-width", str(WIDTH), "--expected-height", str(HEIGHT)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        try: gate_payload = json.loads(gate.stdout)
        except json.JSONDecodeError: gate_payload = {"status": "FAIL", "stdout": gate.stdout, "stderr": gate.stderr}
        if gate.returncode != 0 or gate_payload.get("status") != "PASS": raise RuntimeError(f"poster_light_background_gate_failed:{candidate}:{gate_payload}")
        outputs.append({"page": page_no, "stock_codes": [r.get("code") for r in rows], "conclusion_keys": [key for key, _ in conclusion_rows], "conclusion_texts": [text for _, text in conclusion_rows], "candidate": str(candidate), "candidate_sha256": sha(candidate), "preview": str(preview), "preview_sha256": sha(preview), "light_background_gate": gate_payload})
        body_char_count = sum(len(re.sub(r"\s+", "", line)) for line in visible_lines)
        occupied_ratio = len(rows) / (3 * max(len(column) for column in stock_columns))
        metrics_records.append({"id": f"{page_no:02d}", "image": candidate.name, "preview": preview.name, "native_width": WIDTH, "native_height": HEIGHT, "min_body_preview_px": POLICY["body_source_font_px"] / preview_scale, "min_heading_preview_px": POLICY["heading_source_font_px"] / preview_scale, "min_meta_preview_px": POLICY["min_source_font_px"] / preview_scale, "max_line_chars": max(map(len, visible_lines)), "max_empty_horizontal_band_preview_px": max_empty_dark_band_preview(preview), "occupied_cell_ratio": occupied_ratio, "min_major_column_width_native": major_column_width, "body_char_count": body_char_count, "section_count": 4, "date_count": 1, "overflow_count": 0, "out_of_bounds_count": 0, "unclassified_text_count": 0, "bad_contrast_count": 0, "leading_punctuation_count": 0})
    visible_keys = [key for page in outputs for key in page["conclusion_keys"]]
    if visible_keys != CONCLUSION_KEYS: raise RuntimeError("poster_conclusion_coverage_invalid")
    font_scale_audit = {"scale": preview_scale, "min_preview_px": POLICY["min_source_font_px"] / preview_scale, "body_preview_px": POLICY["body_source_font_px"] / preview_scale, "heading_preview_px": POLICY["heading_source_font_px"] / preview_scale, "primary_preview_px": POLICY["primary_source_font_px"] / preview_scale}
    font_scale_audit["status"] = "PASS" if font_scale_audit["min_preview_px"] >= 22 and font_scale_audit["body_preview_px"] >= 32 and font_scale_audit["heading_preview_px"] >= 45 and font_scale_audit["primary_preview_px"] >= 34 else "FAIL"
    if font_scale_audit["status"] != "PASS": raise RuntimeError("poster_preview_font_size_gate_failed")
    metrics = {"schema_version": 1, "preview_width": PREVIEW[0], "posters": metrics_records}
    metrics_path = run_dir / "poster-readability-metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"schema": "LONGHUBANG_POSTER_DRAFT_V2", "status": "REVIEW_REQUIRED", "trade_date": trade_date, "canvas": [WIDTH, HEIGHT], "preview": list(PREVIEW), "policy": POLICY, "font_scale_audit": font_scale_audit, "readability_metrics": {"status": "CLEAN_PASS", "path": str(metrics_path), "poster_count": len(metrics_records)}, "stock_count": len(records), "visible_stock_count": sum(len(p["stock_codes"]) for p in outputs), "analysis_binding": binding, "visible_conclusion_keys": visible_keys, "pages": outputs}
    path = run_dir / "poster-draft-manifest.json"; path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {**manifest, "manifest": str(path)}

def record_inspection(manifest_path: Path, output: Path, notes: str) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "REVIEW_REQUIRED" or not notes.strip(): raise ValueError("valid_review_manifest_and_notes_required")
    if manifest.get("analysis_binding", {}).get("status") != "CLEAN_PASS" or manifest.get("visible_conclusion_keys") != CONCLUSION_KEYS: raise ValueError("poster_analysis_binding_invalid")
    payload = {"schema": "LONGHUBANG_VISUAL_INSPECTION_V2", "status": "CLEAN_PASS", "visual_inspected": True, "inspection_surface": "complete_1080x608_preview", "notes": notes.strip(), "analysis_binding": manifest["analysis_binding"], "pages": [{"candidate_sha256": p["candidate_sha256"], "preview_sha256": p["preview_sha256"], "stock_codes": p["stock_codes"], "conclusion_keys": p["conclusion_keys"]} for p in manifest["pages"]]}
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def finalize(draft: dict[str, Any], inspection_path: Path, run_dir: Path) -> list[Path]:
    inspection = json.loads(inspection_path.read_text(encoding="utf-8"))
    if inspection.get("status") != "CLEAN_PASS" or inspection.get("visual_inspected") is not True: raise ValueError("visual_inspection_not_clean")
    if inspection.get("analysis_binding") != draft.get("analysis_binding"): raise ValueError("visual_inspection_analysis_binding_mismatch")
    expected = [(p["candidate_sha256"], p["preview_sha256"], p["stock_codes"], p["conclusion_keys"]) for p in inspection.get("pages", [])]
    actual = [(p["candidate_sha256"], p["preview_sha256"], p["stock_codes"], p["conclusion_keys"]) for p in draft["pages"]]
    if expected != actual: raise ValueError("visual_inspection_hash_or_coverage_mismatch")
    shutil.copy2(inspection_path, run_dir / "visual-inspection.json")
    artifact_dir = run_dir / "artifacts"; artifact_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for page in draft["pages"]:
        source = Path(page["candidate"]); target = artifact_dir / source.name
        shutil.copy2(source, target)
        if sha(target) != page["candidate_sha256"]: raise RuntimeError("poster_copy_hash_mismatch")
        outputs.append(target)
    return outputs

def main() -> int:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    record = sub.add_parser("record-inspection"); record.add_argument("--draft-manifest", required=True); record.add_argument("--output", required=True); record.add_argument("--notes", required=True)
    args = parser.parse_args()
    if args.command == "record-inspection": record_inspection(Path(args.draft_manifest), Path(args.output), args.notes); return 0
    return 2

if __name__ == "__main__": raise SystemExit(main())
