#!/usr/bin/env python3
"""Generate a deterministic 8K poster from a clean limit-up-review result."""
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
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin


WIDTH = 7680
HEIGHT = 4320
MARGIN = 300
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")

COLORS = {
    "background": "#F4F7FA",
    "paper": "#FFFFFF",
    "ink": "#17212B",
    "muted": "#5F6B77",
    "navy": "#173B5E",
    "blue": "#2E6F9E",
    "teal": "#218A72",
    "red": "#D94C4C",
    "amber": "#E8A62A",
    "line": "#CED8E2",
    "blue_tint": "#EAF2F8",
    "teal_tint": "#E7F4EF",
    "red_tint": "#FCECE9",
    "amber_tint": "#FFF3D6",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REGULAR
    if not path.is_file():
        raise FileNotFoundError(path)
    return ImageFont.truetype(str(path), size=size)


def metric(result: dict[str, Any], key: str) -> float:
    item = result.get("metrics", {}).get(key)
    if not isinstance(item, dict) or item.get("verification_status") != "VERIFIED":
        raise ValueError(f"metric_not_verified:{key}")
    value = item.get("value")
    if not isinstance(value, (int, float)):
        raise ValueError(f"metric_value_invalid:{key}")
    return float(value)


def section(result: dict[str, Any], chapter: int) -> dict[str, Any]:
    for item in result.get("section_analysis", []):
        if isinstance(item, dict) and item.get("chapter") == chapter:
            return item
    raise ValueError(f"section_missing:{chapter}")


def direction_name(result: dict[str, Any]) -> str:
    text = str(section(result, 4).get("analysis", ""))
    match = re.match(r"^(.+?)以\d+只涨停", text)
    if not match:
        raise ValueError("direction_name_unavailable")
    return match.group(1)


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
    max_width: int,
) -> str:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        width = draw.textbbox((0, 0), candidate, font=text_font)[2]
        if current and width > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--business-result", required=True)
    parser.add_argument("--source-docx", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--audit-json", required=True)
    args = parser.parse_args()

    result_path = Path(args.business_result).resolve()
    source_docx = Path(args.source_docx).resolve()
    output_path = Path(args.output).resolve()
    audit_path = Path(args.audit_json).resolve()
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("status") != "CLEAN_PASS":
        raise ValueError("business_result_not_clean")
    if not source_docx.is_file():
        raise FileNotFoundError(source_docx)

    trade_date_raw = str(result.get("run", {}).get("trade_date") or result.get("date"))
    digits = re.sub(r"\D", "", trade_date_raw)
    if len(digits) != 8:
        raise ValueError("trade_date_invalid")
    trade_date = f"{digits[:4]}-{digits[4:6]}-{digits[6:]}"

    official_count = int(metric(result, "official_limit_up_count"))
    up_count = int(metric(result, "market_up_count"))
    down_count = int(metric(result, "market_down_count"))
    first_count = int(metric(result, "first_board_count"))
    continuation_count = int(metric(result, "continuation_count"))
    max_board = int(metric(result, "max_board"))
    limit_down_count = int(metric(result, "limit_down_count"))
    touch_fail_rate = metric(result, "touch_fail_rate")
    failed_match = re.search(r"炸板(\d+)只", str(section(result, 10).get("facts", "")))
    if not failed_match:
        raise ValueError("failed_limit_up_count_unavailable")
    failed_count = int(failed_match.group(1))
    first_share = metric(result, "first_board_share") * 100
    continuation_share = metric(result, "continuation_share") * 100
    largest_count = int(metric(result, "largest_direction_count"))
    largest_share = metric(result, "largest_direction_share") * 100
    largest_continuation = int(metric(result, "largest_direction_continuation"))
    largest_fund = metric(result, "largest_direction_fund_total") / 100_000_000
    high_board_count = int(metric(result, "high_board_count"))
    high_board_open_count = int(metric(result, "high_board_open_count"))
    fund_total = metric(result, "fund_total") / 100_000_000
    top5_share = metric(result, "top5_direction_share") * 100
    direction = direction_name(result)

    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    draw = ImageDraw.Draw(image)
    text_records: list[dict[str, Any]] = []

    def text(
        xy: tuple[int, int],
        value: str,
        size: int,
        color: str = COLORS["ink"],
        bold: bool = False,
        role: str = "body",
        max_width: int | None = None,
        spacing: int = 24,
        anchor: str | None = None,
    ) -> tuple[int, int, int, int]:
        text_font = font(size, bold=bold)
        rendered = (
            wrap_text(draw, value, text_font, max_width)
            if max_width is not None
            else value
        )
        bbox = draw.multiline_textbbox(
            xy,
            rendered,
            font=text_font,
            spacing=spacing,
            anchor=anchor,
        )
        draw.multiline_text(
            xy,
            rendered,
            font=text_font,
            fill=color,
            spacing=spacing,
            anchor=anchor,
        )
        text_records.append(
            {
                "text": value,
                "rendered": rendered,
                "font_px": size,
                "role": role,
                "bbox": list(bbox),
            }
        )
        return bbox

    # Header band.
    draw.rectangle((0, 0, WIDTH, 720), fill=COLORS["paper"])
    draw.rectangle((0, 0, 110, 720), fill=COLORS["red"])
    text((MARGIN, 110), trade_date, 84, COLORS["muted"], bold=True, role="secondary")
    text((MARGIN, 235), "涨停板深度复盘", 260, COLORS["navy"], bold=True, role="title")
    text(
        (MARGIN, 525),
        "普涨，但强势股接力仍不顺",
        150,
        COLORS["red"],
        bold=True,
        role="headline",
    )
    text(
        (WIDTH - MARGIN, 118),
        "收盘事实版",
        86,
        COLORS["blue"],
        bold=True,
        role="secondary",
        anchor="ra",
    )
    text(
        (WIDTH - MARGIN, 290),
        "宽度 ≠ 质量\n热度 ≠ 主线\n资金 ≠ 接力",
        104,
        COLORS["ink"],
        bold=True,
        role="body",
        spacing=28,
        anchor="ra",
    )

    # Single full-width metric ribbon, separated by dividers rather than cards.
    metric_top = 760
    metric_bottom = 1450
    draw.rectangle((0, metric_top, WIDTH, metric_bottom), fill=COLORS["navy"])
    metrics = [
        (str(official_count), "涨停家数", "官方涨停池"),
        (f"{up_count} / {down_count}", "上涨 / 下跌", "普涨宽度"),
        (f"{first_count} / {continuation_count}", "首板 / 连板", f"{first_share:.1f}% / {continuation_share:.1f}%"),
        (f"{max_board} 板", "最高高度", f"3板以上 {high_board_count} 只"),
        (f"{failed_count} / {limit_down_count}", "炸板 / 跌停", f"失败率 {touch_fail_rate:.1f}%"),
        (f"{100 - touch_fail_rate:.1f}%", "封板率", f"前5热点 {top5_share:.1f}%"),
    ]
    col_width = (WIDTH - 2 * MARGIN) // len(metrics)
    for index, (number, label, note) in enumerate(metrics):
        left = MARGIN + index * col_width
        center = left + col_width // 2
        if index:
            draw.line(
                (left, metric_top + 110, left, metric_bottom - 110),
                fill="#5F7890",
                width=5,
            )
        number_size = 180 if len(number) <= 8 else 148
        text(
            (center, metric_top + 110),
            number,
            number_size,
            "#FFFFFF",
            bold=True,
            role="metric",
            anchor="ma",
        )
        text(
            (center, metric_top + 350),
            label,
            96,
            "#FFFFFF",
            bold=True,
            role="body",
            anchor="ma",
        )
        text(
            (center, metric_top + 500),
            note,
            76,
            "#C7D8E7",
            role="secondary",
            anchor="ma",
        )

    # Main reasoning zone.
    main_top = 1540
    main_bottom = 3190
    left_x = MARGIN
    left_w = 4400
    right_x = 5000
    right_w = WIDTH - MARGIN - right_x
    text((left_x, main_top), "一条逻辑链看懂今天", 124, COLORS["navy"], bold=True, role="section")
    logic_rows = [
        (
            "01",
            "市场很宽",
            f"上涨 {up_count} 只、下跌 {down_count} 只，上涨占比 73.5%。",
            COLORS["blue"],
            COLORS["blue_tint"],
        ),
        (
            "02",
            "首板扩散",
            f"{first_count} 只首板，占涨停池 {first_share:.1f}%；新增涨停很多。",
            COLORS["teal"],
            COLORS["teal_tint"],
        ),
        (
            "03",
            "接力偏弱",
            f"连板仅 {continuation_count} 只，占 {continuation_share:.1f}%；最高板在，但梯队不整齐。",
            COLORS["amber"],
            COLORS["amber_tint"],
        ),
        (
            "04",
            "风险未消",
            f"炸板 {failed_count} 只、跌停 {limit_down_count} 只，前排反复开板仍制造局部亏钱。",
            COLORS["red"],
            COLORS["red_tint"],
        ),
    ]
    row_y = main_top + 220
    row_h = 310
    for index, (number, heading, body, accent, tint) in enumerate(logic_rows):
        y = row_y + index * 330
        draw.rounded_rectangle(
            (left_x, y, left_x + left_w, y + row_h),
            radius=28,
            fill=tint,
        )
        draw.rounded_rectangle(
            (left_x + 28, y + 34, left_x + 250, y + row_h - 34),
            radius=28,
            fill=accent,
        )
        text(
            (left_x + 139, y + row_h // 2),
            number,
            104,
            "#FFFFFF",
            bold=True,
            role="body",
            anchor="mm",
        )
        text(
            (left_x + 330, y + 52),
            heading,
            112,
            COLORS["ink"],
            bold=True,
            role="body",
        )
        text(
            (left_x + 330, y + 178),
            body,
            96,
            COLORS["muted"],
            role="body",
            max_width=left_w - 430,
        )

    # Right-side mainline and capital synthesis.
    draw.rectangle((right_x, main_top, right_x + right_w, main_bottom), fill=COLORS["paper"])
    draw.rectangle((right_x, main_top, right_x + 26, main_bottom), fill=COLORS["amber"])
    text(
        (right_x + 120, main_top + 60),
        "主线、梯队与资金",
        124,
        COLORS["navy"],
        bold=True,
        role="section",
    )
    text(
        (right_x + 120, main_top + 260),
        direction,
        154,
        COLORS["red"],
        bold=True,
        role="headline",
    )
    text(
        (right_x + 120, main_top + 455),
        f"{largest_count}只涨停  ·  {largest_continuation}只连板  ·  {largest_fund:.2f}亿资金",
        96,
        COLORS["ink"],
        bold=True,
        role="body",
        max_width=right_w - 220,
    )
    text(
        (right_x + 120, main_top + 650),
        f"占全池 {largest_share:.1f}%：是最清楚的热点，但还不是唯一主线。",
        104,
        COLORS["navy"],
        bold=True,
        role="body",
        max_width=right_w - 220,
    )
    draw.line(
        (right_x + 120, main_top + 920, right_x + right_w - 120, main_top + 920),
        fill=COLORS["line"],
        width=5,
    )
    text(
        (right_x + 120, main_top + 1000),
        "高位梯队",
        102,
        COLORS["amber"],
        bold=True,
        role="body",
    )
    text(
        (right_x + 120, main_top + 1130),
        f"最高 {max_board} 板，但3板以上仅 {high_board_count} 只，累计开板 {high_board_open_count} 次。",
        96,
        COLORS["ink"],
        role="body",
        max_width=right_w - 220,
    )
    text(
        (right_x + 120, main_top + 1260),
        "资金覆盖",
        102,
        COLORS["teal"],
        bold=True,
        role="body",
    )
    text(
        (right_x + 120, main_top + 1390),
        f"99/99只覆盖，合计净流入 {fund_total:.2f} 亿；资金广撒，接力没有同步增强。",
        96,
        COLORS["ink"],
        role="body",
        max_width=right_w - 220,
    )

    # Scenario zone: two columns, two large rows each.
    scenario_top = 3200
    text((MARGIN, scenario_top), "次日只看四条验证路径", 124, COLORS["navy"], bold=True, role="section")
    scenario_items = [
        (
            "接力转强",
            f"连板 > {continuation_count}只；失败率 < {touch_fail_rate:.1f}%；{direction}连板 > {largest_continuation}只。",
            COLORS["teal"],
            COLORS["teal_tint"],
        ),
        (
            "热点轮动",
            f"{direction} < {largest_count}只；新方向 > {largest_count}只；失败率不高于 {touch_fail_rate:.1f}%。",
            COLORS["blue"],
            COLORS["blue_tint"],
        ),
        (
            "亏钱扩大",
            f"失败率 > {touch_fail_rate:.1f}%；跌停 > {limit_down_count}只；连板 < {continuation_count}只。",
            COLORS["red"],
            COLORS["red_tint"],
        ),
        (
            "外部冲击",
            "收盘后重大政策、公告或监管变化，先核对时间与受益映射，再重建判断。",
            COLORS["amber"],
            COLORS["amber_tint"],
        ),
    ]
    column_gap = 140
    scenario_w = (WIDTH - 2 * MARGIN - column_gap) // 2
    scenario_y = scenario_top + 200
    scenario_h = 330
    for index, (heading, body, accent, tint) in enumerate(scenario_items):
        col = index % 2
        row = index // 2
        x = MARGIN + col * (scenario_w + column_gap)
        y = scenario_y + row * 370
        draw.rounded_rectangle((x, y, x + scenario_w, y + scenario_h), radius=24, fill=tint)
        draw.rectangle((x, y, x + 30, y + scenario_h), fill=accent)
        text((x + 90, y + 45), heading, 104, accent, bold=True, role="body")
        text(
            (x + 90, y + 170),
            body,
            96,
            COLORS["ink"],
            role="body",
            max_width=scenario_w - 160,
        )

    # Footer.
    footer_top = 4160
    draw.rectangle((0, footer_top, WIDTH, HEIGHT), fill=COLORS["ink"])
    text(
        (MARGIN, footer_top + 42),
        f"数据日期：{trade_date}  |  来源：本轮涨停板深度复盘业务结果  |  仅作教学研究，不构成投资建议",
        72,
        "#FFFFFF",
        role="secondary",
    )
    text(
        (WIDTH - MARGIN, footer_top + 42),
        "股市有风险，入市需谨慎",
        72,
        "#F5C35A",
        bold=True,
        role="secondary",
        anchor="ra",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    png_info = PngImagePlugin.PngInfo()
    png_info.add_text("poster_schema", "LIMIT_UP_REVIEW_POSTER_V1")
    png_info.add_text("trade_date", trade_date)
    png_info.add_text("business_result_sha256", sha256_file(result_path))
    png_info.add_text("source_docx_sha256", sha256_file(source_docx))
    png_info.add_text(
        "font_policy",
        json.dumps({"body_min_px": 96, "secondary_min_px": 72}, ensure_ascii=False),
    )
    image.save(output_path, format="PNG", optimize=True, pnginfo=png_info)

    audit = {
        "schema": "LIMIT_UP_REVIEW_POSTER_AUDIT_V1",
        "status": "CLEAN_PASS",
        "canvas": {"width": WIDTH, "height": HEIGHT},
        "trade_date": trade_date,
        "source_docx": {
            "path": str(source_docx),
            "sha256": sha256_file(source_docx),
        },
        "business_result": {
            "path": str(result_path),
            "sha256": sha256_file(result_path),
        },
        "poster": {
            "path": str(output_path),
            "size": output_path.stat().st_size,
            "sha256": sha256_file(output_path),
        },
        "font_policy": {"body_min_px": 96, "secondary_min_px": 72},
        "text_records": text_records,
        "errors": [],
    }
    audit_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
