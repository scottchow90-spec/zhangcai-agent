from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageStat

WIDTH = 7680
HEIGHT = 4320
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
MINIMUM_FONT = 72
COMPOSITE_MINIMUM_FONT = 96

COLORS = {
    "background": "#F4F7FA",
    "paper": "#FFFFFF",
    "ink": "#112A3D",
    "muted": "#52697A",
    "line": "#D6E1E9",
    "navy": "#173C5A",
    "navy_light": "#E7EFF6",
    "blue": "#347DB5",
    "green": "#21816B",
    "green_light": "#E0F1EB",
    "gold": "#BE8A19",
    "gold_light": "#F8EDCD",
    "red": "#C64A4A",
    "red_light": "#F9E7E7",
    "gray_band": "#EEF3F6",
}


@lru_cache(maxsize=None)
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold and FONT_BOLD.is_file() else FONT_REGULAR
    if not path.is_file():
        raise FileNotFoundError(f"中文字体不存在：{path}")
    return ImageFont.truetype(str(path), size=size)


def text_width(draw: ImageDraw.ImageDraw, value: str, size: int, bold: bool = False) -> float:
    box = draw.textbbox((0, 0), value, font=font(size, bold))
    return float(box[2] - box[0])


def shorten(
    draw: ImageDraw.ImageDraw,
    value: str,
    maximum_width: int,
    size: int,
    bold: bool = False,
) -> str:
    if text_width(draw, value, size, bold) <= maximum_width:
        return value
    suffix = "…"
    current = value
    while current and text_width(draw, current + suffix, size, bold) > maximum_width:
        current = current[:-1]
    return current + suffix


def render_index_analysis_poster(
    payload: dict[str, Any],
    output: Path,
) -> dict[str, Any]:
    """Render the fixed sixteen-subsystem index analysis as a readable 8K poster."""
    if payload.get("status") != "CLEAN_PASS":
        raise RuntimeError("指数分析海报源数据不是通过状态")
    rows = list(payload.get("subsystems", []))
    expected_numbers = list(range(1, 17))
    if [int(row.get("序号", 0)) for row in rows] != expected_numbers:
        raise RuntimeError("指数分析海报没有按固定顺序完整覆盖十六项")
    assessment = payload.get("assessment")
    if not isinstance(assessment, dict):
        raise RuntimeError("指数分析海报缺少综合研判")
    dimensions = assessment.get("dimensions")
    expected_dimensions = ["趋势结构", "短线动量", "参与强度", "进攻信号", "位置与风险"]
    if not isinstance(dimensions, dict) or list(dimensions) != expected_dimensions:
        raise RuntimeError("指数分析海报缺少固定五维评分")
    clear_conclusion = assessment.get("clear_conclusion")
    if not isinstance(clear_conclusion, str) or not clear_conclusion.strip():
        raise RuntimeError("指数分析海报结论缺失")
    conclusion_provenance = assessment.get("conclusion_provenance")
    if not isinstance(conclusion_provenance, dict):
        raise RuntimeError("指数分析海报结论缺少当前运行证据绑定")
    if conclusion_provenance.get("fallback_used") is not False:
        raise RuntimeError("指数分析海报结论使用了兜底判断")
    if conclusion_provenance.get("legacy_fixed_conclusion_match") is not False:
        raise RuntimeError("指数分析海报结论命中旧固定措辞")
    if conclusion_provenance.get("method") != "CURRENT_RUN_EVIDENCE_CLAUSES_V1":
        raise RuntimeError("指数分析海报结论证据生成方法不受支持")
    if int(conclusion_provenance.get("fact_count") or 0) < 8:
        raise RuntimeError("指数分析海报结论证据不足")
    if str(conclusion_provenance.get("trade_date") or "") != str(payload.get("trade_date") or ""):
        raise RuntimeError("指数分析海报结论证据日期与海报数据日期不一致")

    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    draw = ImageDraw.Draw(image)
    visible_texts: list[str] = []
    used_sizes: list[int] = []
    role_sizes: dict[str, list[int]] = {"minimum": [], "core": [], "primary": []}
    text_boxes: list[tuple[str, tuple[int, int, int, int]]] = []

    def rectangle(
        xy: tuple[int, int, int, int],
        fill: str,
        outline: str | None = None,
        width: int = 1,
        radius: int = 0,
    ) -> None:
        if radius:
            draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
        else:
            draw.rectangle(xy, fill=fill, outline=outline, width=width)

    def put(
        value: str,
        x: int,
        y: int,
        size: int,
        color: str = COLORS["ink"],
        bold: bool = False,
        anchor: str = "ls",
        tag: str = "",
        maximum_width: int | None = None,
        role: str = "minimum",
    ) -> str:
        shown = str(value)
        if maximum_width is not None:
            shown = shorten(draw, shown, maximum_width, size, bold)
        selected_font = font(size, bold)
        box = draw.textbbox((x, y), shown, font=selected_font, anchor=anchor)
        visible_texts.append(shown)
        used_sizes.append(size)
        role_sizes[role].append(size)
        text_boxes.append((tag or shown, box))
        draw.text((x, y), shown, font=selected_font, fill=color, anchor=anchor)
        return shown

    def wrap_lines(value: str, maximum_width: int, size: int, maximum_lines: int) -> list[str]:
        remaining = str(value).strip()
        lines: list[str] = []
        while remaining and len(lines) < maximum_lines:
            if text_width(draw, remaining, size, True) <= maximum_width:
                lines.append(remaining)
                remaining = ""
                break
            split = len(remaining)
            while split > 1 and text_width(draw, remaining[:split], size, True) > maximum_width:
                split -= 1
            if len(lines) == maximum_lines - 1:
                lines.append(shorten(draw, remaining, maximum_width, size, True))
                remaining = ""
                break
            lines.append(remaining[:split])
            remaining = remaining[split:]
        return lines

    def compact_support_pressure(value: str) -> str:
        compact = str(value)
        replacements = (
            ("第五输出字段为", "第五字段"),
            ("第五输出字段", "第五字段"),
            ("OUTPUT66", "第五字段"),
            ("核心黄金分割", "黄金分割"),
            ("支撑一", "支一"),
            ("支撑二", "支二"),
            ("压力一", "压一"),
            ("压力二", "压二"),
            ("，", "｜"),
            ("=", ""),
        )
        for source, target in replacements:
            compact = compact.replace(source, target)
        return compact

    def row_name(row: dict[str, Any]) -> str:
        return str(row.get("子系统/输出") or row.get("子系统") or "未命名子系统")

    def row_evidence(row: dict[str, Any]) -> str:
        return str(row.get("当前值/证据") or row.get("证据") or "无可用证据")

    rectangle((0, 240, 48, HEIGHT - 240), COLORS["gold"])
    rectangle((48, 0, WIDTH, 30), COLORS["gold_light"])
    put(
        f"{payload.get('name', '指数')}｜大牛线十六子系统综合研判",
        300, 245, 208, COLORS["ink"], True, tag="主标题", role="primary",
    )
    put(
        f"{payload.get('trade_date', '')}收盘｜代码{payload.get('code', '')}｜数据源：{payload.get('data_source', '本机通达信')}",
        305, 430, 96, COLORS["muted"], True, tag="数据日期",
        maximum_width=7050,
    )

    metric_specs = [
        (f"{float(payload.get('close', 0.0)):.2f}", "最新收盘", COLORS["navy"], COLORS["navy_light"]),
        (f"{float(payload.get('change_pct', 0.0)):+.2f}%", "当日涨跌", COLORS["red"], COLORS["red_light"]),
        (f"{int(assessment.get('score', 0))}分", "综合评分", COLORS["green"], COLORS["green_light"]),
        (str(assessment.get("rating", "未评级")), "综合评级", COLORS["gold"], COLORS["gold_light"]),
    ]
    for index, (value, label, accent, light) in enumerate(metric_specs):
        x1 = 280 + index * 1805
        x2 = x1 + 1680
        rectangle((x1, 510, x2, 900), light, accent, 4, 8)
        put(value, (x1 + x2) // 2, 680, 176, accent, True, "mm", f"指标值{index}", role="primary")
        put(label, (x1 + x2) // 2, 830, 128, COLORS["ink"], True, "mm", f"指标名{index}", role="core")

    rectangle((280, 965, 7400, 1390), COLORS["paper"], COLORS["line"], 4, 8)
    rectangle((280, 965, 320, 1390), COLORS["red"])
    put(
        f"当前阶段：{assessment.get('market_phase', '阶段未判定')}",
        420, 1115, 152, COLORS["red"], True, tag="当前阶段", role="primary",
        maximum_width=6750,
    )
    conclusion_lines = wrap_lines(clear_conclusion, 6750, 128, 2)
    for index, line in enumerate(conclusion_lines):
        put(line, 420, 1260 + index * 150, 128, COLORS["ink"], True,
            tag=f"明确结论{index}", role="core")

    dimension_colors = [COLORS["navy"], COLORS["blue"], COLORS["green"], COLORS["red"], COLORS["gold"]]
    for index, name in enumerate(expected_dimensions):
        x1 = 280 + index * 1440
        x2 = x1 + 1320
        rectangle((x1, 1450, x2, 1740), COLORS["paper"], COLORS["line"], 4, 6)
        put(name, x1 + 100, 1580, 128, dimension_colors[index], True,
            tag=f"维度名{index}", role="core")
        put(f"{float(dimensions[name].get('score', 0.0)):.1f}", x2 - 100, 1690, 144,
            dimension_colors[index], True, "rs", f"维度分{index}", role="primary")

    card_colors = [COLORS["navy"], COLORS["blue"], COLORS["green"], COLORS["gold"]]
    for index, row in enumerate(rows[:14]):
        column = index // 7
        row_index = index % 7
        x1 = 280 if column == 0 else 3880
        x2 = 3740 if column == 0 else 7400
        y1 = 1810 + row_index * 230
        y2 = y1 + 205
        accent = card_colors[index % len(card_colors)]
        rectangle((x1, y1, x2, y2), COLORS["paper"], COLORS["line"], 3, 6)
        rectangle((x1, y1, x1 + 20, y2), accent)
        put(
            f"{int(row['序号']):02d}　{row_name(row)}", x1 + 90, y1 + 145, 96,
            accent, True, tag=f"子系统标题{index}", maximum_width=980,
        )
        summary = f"{row.get('状态', '未判定')}｜{row.get('结论', '结论缺失')}"
        put(summary, x1 + 1160, y1 + 145, 128, COLORS["ink"], True,
            tag=f"子系统结论{index}", maximum_width=x2 - x1 - 1250, role="core")

    for offset, row in enumerate(rows[14:]):
        y1 = 3440 + offset * 270
        y2 = y1 + 235
        accent = COLORS["green"] if offset == 0 else COLORS["red"]
        rectangle((280, y1, 7400, y2), COLORS["paper"], COLORS["line"], 3, 6)
        rectangle((280, y1, 300, y2), accent)
        put(
            f"{int(row['序号']):02d}　{row_name(row)}", 390, y1 + 155, 112,
            accent, True, tag=f"底部子系统标题{offset}", maximum_width=1550,
        )
        if int(row["序号"]) == 16:
            evidence = compact_support_pressure(row_evidence(row))
            put(evidence, 2050, y1 + 155, 128, COLORS["ink"], True,
                tag="黄金撑压五字段", maximum_width=5150, role="core")
        else:
            summary = f"{row.get('状态', '未判定')}｜{row.get('结论', '结论缺失')}"
            put(summary, 2050, y1 + 155, 128,
                COLORS["ink"], True, tag="布林结论", maximum_width=5150, role="core")

    put(
        f"转强：{assessment.get('bullish_trigger', '')}",
        300, 4250, 96, COLORS["green"], True, tag="转强条件",
        maximum_width=4200,
    )
    put(
        "研究用途，不构成交易依据",
        7380, 4250, 96, COLORS["muted"], True, "rs", tag="用途边界",
    )

    overlaps: list[dict[str, str]] = []
    for left_index, (left_tag, left_box) in enumerate(text_boxes):
        for right_tag, right_box in text_boxes[left_index + 1:]:
            x_overlap = min(left_box[2], right_box[2]) - max(left_box[0], right_box[0])
            y_overlap = min(left_box[3], right_box[3]) - max(left_box[1], right_box[1])
            if x_overlap > 3 and y_overlap > 3:
                overlaps.append({"left": left_tag, "right": right_tag})
    clipped_text = [
        tag for tag, box in text_boxes
        if box[0] < 0 or box[1] < 0 or box[2] > WIDTH or box[3] > HEIGHT
    ]

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)
    preview = output.with_name(f"{output.stem}-preview-1920x1080.png")
    image.resize((1920, 1080), Image.Resampling.LANCZOS).save(preview, format="PNG", optimize=True)
    brightness = sum(ImageStat.Stat(image.resize((160, 90))).mean[:3]) / 3.0
    preview_scale = 1920 / WIDTH
    required_support_tokens = ("支一", "支二", "压一", "压二", "第五字段")
    support_pressure_visible = all(
        any(token in value for value in visible_texts) for token in required_support_tokens
    )
    validation = {
        "width": image.width,
        "height": image.height,
        "preview_width": 1920,
        "preview_height": 1080,
        "preview_path": str(preview),
        "subsystem_count": len(rows),
        "minimum_font_px": min(used_sizes),
        "minimum_preview_font_px": min(used_sizes) * preview_scale,
        "core_body_preview_font_px": min(role_sizes["core"]) * preview_scale,
        "primary_preview_font_px": min(role_sizes["primary"]) * preview_scale,
        "mean_brightness": round(brightness, 2),
        "overlaps": overlaps,
        "clipped_text": clipped_text,
        "support_pressure_visible": support_pressure_visible,
    }
    validation["passed"] = (
        image.size == (7680, 4320)
        and preview.is_file()
        and validation["subsystem_count"] == 16
        and validation["minimum_preview_font_px"] >= 24
        and validation["core_body_preview_font_px"] >= 32
        and validation["primary_preview_font_px"] >= 34
        and validation["mean_brightness"] >= 190
        and not overlaps
        and not clipped_text
        and support_pressure_visible
    )
    if not validation["passed"]:
        output.unlink(missing_ok=True)
        preview.unlink(missing_ok=True)
        raise RuntimeError(f"指数分析海报验收失败：{validation}")
    return validation


def render_poster(payload: dict[str, Any], output: Path) -> dict[str, Any]:
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["paper"])
    draw = ImageDraw.Draw(image)
    visible_texts: list[str] = []
    used_sizes: list[int] = []
    role_sizes: dict[str, list[int]] = {"minimum": [], "core": [], "primary": []}
    text_boxes: list[tuple[str, tuple[int, int, int, int]]] = []

    def rectangle(
        xy: tuple[int, int, int, int],
        fill: str,
        outline: str | None = None,
        width: int = 1,
        radius: int = 0,
    ) -> None:
        if radius:
            draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
        else:
            draw.rectangle(xy, fill=fill, outline=outline, width=width)

    def put(
        value: str,
        x: int,
        y: int,
        size: int,
        color: str = COLORS["ink"],
        bold: bool = False,
        anchor: str = "ls",
        tag: str = "",
        maximum_width: int | None = None,
        role: str = "minimum",
    ) -> str:
        shown = str(value)
        if maximum_width is not None:
            shown = shorten(draw, shown, maximum_width, size, bold)
        selected_font = font(size, bold)
        box = draw.textbbox((x, y), shown, font=selected_font, anchor=anchor)
        visible_texts.append(shown)
        used_sizes.append(size)
        role_sizes[role].append(size)
        text_boxes.append((tag or shown, box))
        draw.text((x, y), shown, font=selected_font, fill=color, anchor=anchor)
        return shown

    rows = list(payload["rows"])
    poster_rows = rows
    qualified = [row for row in rows if row.get("eligible")]
    board = payload["board"]
    constituent_count = int(board.get("constituent_count", -1))
    if len(rows) != constituent_count:
        raise RuntimeError("海报评分行数与板块成分数不一致")
    score_date = str(payload["score_date"])
    date_text = (
        f"{score_date[:4]}年{int(score_date[4:6])}月{int(score_date[6:8])}日"
        if len(score_date) == 8
        else score_date
    )

    rectangle((80, 180, 120, HEIGHT - 180), COLORS["gold"])
    rectangle((120, 80, WIDTH - 120, 110), COLORS["gold_light"])

    put(f"本机通达信｜{board['name']}自定义板块", 300, 220, 96, COLORS["muted"], True)
    put("大牛线百分制评分排名", 294, 450, 200, COLORS["ink"], True, role="primary")
    subtitle = f"{date_text}统一评分｜{len(rows)}只成分股｜先排除，再比较总分"
    put(subtitle, 300, 625, 96, COLORS["blue"], True)
    put(f"成分 {len(rows)}", 4300, 430, 144, COLORS["navy"], True, role="primary")
    put(f"通过 {len(qualified)}", 5350, 430, 144, COLORS["green"], True, role="primary")
    put(
        f"排后 {len(rows) - len(qualified)}",
        6400,
        430,
        144,
        COLORS["red"],
        True,
        role="primary",
    )
    put("完整评分榜｜全部成分股逐只可见", 300, 800, 128, COLORS["navy"], True, role="core")
    put("通过者在前；其余股票按总分排列，硬条件仍然有效", 7380, 800, 96, COLORS["muted"], True, "rs")

    columns = [
        (280, 300, "排序"),
        (580, 1100, "股票与代码"),
        (1680, 420, "总分"),
        (2100, 620, "方向30"),
        (2720, 620, "劲头25"),
        (3340, 620, "当天20"),
        (3960, 620, "空间20"),
        (4580, 620, "额外5"),
        (5200, 2180, "核对状态与排后原因"),
    ]
    table_y = 880
    header_height = 150
    rectangle((280, table_y, 7380, table_y + header_height), COLORS["navy"])
    for x, width, label in columns:
        put(label, x + width // 2, table_y + header_height // 2, 128, COLORS["paper"], True, "mm", role="core")

    row_height = 137
    visible_stock_labels: list[str] = []
    for index, row in enumerate(poster_rows):
        y = table_y + header_height + index * row_height
        fill = (
            COLORS["green_light"]
            if row.get("eligible")
            else COLORS["paper"]
            if index % 2 == 0
            else COLORS["gray_band"]
        )
        rectangle((280, y, 7380, y + row_height), fill, COLORS["line"], 2)
        rectangle((280, y, 294, y + row_height), COLORS["green"] if row.get("eligible") else COLORS["red"])
        center_y = y + row_height // 2
        put(str(row["rank"]), 430, center_y, 96, COLORS["green"] if row.get("eligible") else COLORS["muted"], True, "mm")
        stock_label = f"{row['name']} {row['symbol'][:6]}"
        visible_stock_labels.append(stock_label)
        put(stock_label, 630, center_y, 96, COLORS["ink"], True, "lm", maximum_width=990)
        put(str(row["score"]), 1890, center_y, 136, COLORS["green"] if row.get("eligible") else COLORS["navy"], True, "mm", role="primary")

        values = [
            (2410, row["components"]["方向位置"], COLORS["navy"]),
            (3030, row["components"]["上涨劲头"], COLORS["green"]),
            (3650, row["components"]["当天表现"], COLORS["blue"]),
            (4270, row["components"]["上下空间"], COLORS["gold"]),
            (4890, row["components"]["额外提醒"], COLORS["red"]),
        ]
        for x, value, color in values:
            put(str(value), x, center_y, 136, color, True, "mm", role="primary")

        state = "通过" if row.get("eligible") else "排后"
        state_color = COLORS["green"] if row.get("eligible") else COLORS["red"]
        reason = "无硬排除" if row.get("eligible") else "｜".join(row.get("hard_reasons", []))
        status_text = f"{state}｜{row.get('signal_source', '日线核对')}｜{reason}"
        put(status_text, 5300, center_y, 96, state_color, True, "lm", maximum_width=1980)

    note_y = table_y + header_height + len(poster_rows) * row_height + 35
    rectangle((280, note_y, 7380, note_y + 250), COLORS["gold_light"], COLORS["gold"], 4, 6)
    put("排序规则", 420, note_y + 90, 128, COLORS["gold"], True, role="core")
    put("先看硬条件，再看总分；同分不强行分胜负", 420, note_y + 205, 96, COLORS["ink"], True)
    put(f"通过{len(qualified)}只｜排后{len(rows) - len(qualified)}只", 3320, note_y + 145, 136, COLORS["green"], True, role="primary")
    put("研究整理，不代表未来结果", 7080, note_y + 145, 96, COLORS["red"], True, "rs")

    update_text = (
        f"板块更新时间：{board['updated_at_text']}｜评分数据：本机通达信未复权日线"
    )
    put(update_text, 300, 4260, 96, COLORS["muted"], False)
    put("研究用途｜不得仅凭总分直接参与", 7380, 4260, 96, COLORS["muted"], False, "rs")

    visible = "".join(visible_texts)
    forbidden = [word for word in ("买点", "卖点") if word in visible]
    english = sorted(set(re.findall(r"[A-Za-z]+", visible)))
    overlaps: list[dict[str, str]] = []
    clipped_text = [
        tag for tag, box in text_boxes
        if box[0] < 0 or box[1] < 0 or box[2] > WIDTH or box[3] > HEIGHT
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)
    preview = output.with_name(f"{output.stem}-preview-1920x1080.png")
    image.resize((1920, 1080), Image.Resampling.LANCZOS).save(preview, format="PNG", optimize=True)
    brightness = sum(ImageStat.Stat(image.resize((160, 90))).mean[:3]) / 3.0
    preview_scale = 1920 / WIDTH
    validation = {
        "width": WIDTH,
        "height": HEIGHT,
        "preview_width": 1920,
        "preview_height": 1080,
        "preview_path": str(preview),
        "minimum_font_px": min(used_sizes),
        "minimum_preview_font_px": min(used_sizes) * preview_scale,
        "core_body_preview_font_px": min(role_sizes["core"]) * preview_scale,
        "primary_preview_font_px": min(role_sizes["primary"]) * preview_scale,
        "mean_brightness": round(brightness, 2),
        "forbidden_words": forbidden,
        "visible_english": english,
        "poster_row_count": len(poster_rows),
        "expected_poster_row_count": len(rows),
        "source_stock_count": len(rows),
        "board_constituent_count": constituent_count,
        "artifact_visible_stock_count": len(visible_stock_labels),
        "visible_stock_labels": visible_stock_labels,
        "overlaps": overlaps,
        "clipped_text": clipped_text,
    }
    validation["passed"] = (
        validation["width"] == 7680
        and validation["height"] == 4320
        and preview.is_file()
        and validation["minimum_preview_font_px"] >= 24
        and validation["core_body_preview_font_px"] >= 32
        and validation["primary_preview_font_px"] >= 34
        and validation["mean_brightness"] >= 190
        and not forbidden
        and not clipped_text
        and validation["poster_row_count"]
        == validation["expected_poster_row_count"]
        == validation["source_stock_count"]
        == validation["board_constituent_count"]
        == validation["artifact_visible_stock_count"]
    )
    if not validation["passed"]:
        output.unlink(missing_ok=True)
        preview.unlink(missing_ok=True)
        raise RuntimeError(f"海报验收失败：{validation}")
    return validation


def render_composite_poster(payload: dict[str, Any], output: Path) -> dict[str, Any]:
    """Render the contract-bound 16+10+4 composite ranking poster."""
    rows = list(payload.get("ranking", []))
    if payload.get("status") != "CLEAN_PASS":
        raise RuntimeError("综合评分源数据不是通过状态")
    if payload.get("delivery_validation", {}).get("status") != "PASS":
        raise RuntimeError("综合评分完整性交付校验未通过")
    if len(rows) != int(payload.get("board", {}).get("constituent_count", -1)):
        raise RuntimeError("综合评分成分数量不一致")
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    draw = ImageDraw.Draw(image)
    visible_texts: list[str] = []
    used_sizes: list[int] = []
    role_sizes: dict[str, list[int]] = {"core": [], "primary": []}
    text_boxes: list[tuple[str, tuple[int, int, int, int]]] = []

    def rectangle(
        xy: tuple[int, int, int, int],
        fill: str,
        outline: str | None = None,
        width: int = 1,
        radius: int = 0,
    ) -> None:
        if radius:
            draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
        else:
            draw.rectangle(xy, fill=fill, outline=outline, width=width)

    def put(
        value: str,
        x: int,
        y: int,
        size: int,
        color: str = COLORS["ink"],
        bold: bool = False,
        anchor: str = "ls",
        tag: str = "",
        role: str = "minimum",
    ) -> None:
        value = str(value)
        selected_font = font(size, bold)
        visible_texts.append(value)
        used_sizes.append(size)
        if role in role_sizes:
            role_sizes[role].append(size)
        bbox = draw.textbbox((x, y), value, font=selected_font, anchor=anchor)
        text_boxes.append((tag or value, bbox))
        draw.text((x, y), value, font=selected_font, fill=color, anchor=anchor)

    score_date = str(payload["score_date"])
    date_text = f"{score_date[:4]}年{int(score_date[4:6])}月{int(score_date[6:8])}日"
    board_name = str(payload["board"]["name"])
    research_only = payload.get("scoring_mode") == "RESEARCH_STRUCTURAL"
    rectangle((0, 260, 42, HEIGHT - 260), COLORS["gold"])
    rectangle((42, 0, WIDTH, 30), COLORS["gold_light"])
    put(f"{board_name}板块｜三体系综合评分榜", 300, 300, 194, COLORS["ink"], True, tag="标题", role="primary")
    put("固定30项｜大牛线16项＋飞龙在天10项＋庄家资金监控4项", 306, 510, 96, COLORS["blue"], True, tag="副标题")
    put(
        f"评分日 {date_text}｜板块{len(rows)}只｜全市场横截面 {payload['data']['universe_count']}只｜海报完整展示{len(rows)}只",
        310, 680, 96, COLORS["muted"], True, tag="口径",
    )

    card_y1, card_y2 = 825, 1250
    cards = [
        (300, 2530, COLORS["green_light"], COLORS["green"]),
        (2690, 4950, COLORS["navy_light"], COLORS["blue"]),
        (5110, 7380, COLORS["gold_light"], COLORS["gold"]),
    ]
    for x1, x2, fill, outline in cards:
        rectangle((x1, card_y1, x2, card_y2), fill, outline, 5, 26)

    leader = rows[0]
    put("综合第一", 470, 905, 96, COLORS["green"], True, tag="冠军标签")
    put(f"{leader['name']}  {leader['score']:.2f}分", 470, 1080, 136, COLORS["ink"], True, tag="冠军名称", role="primary")
    top_scores = leader["top_level_items"]
    strongest = max(top_scores, key=top_scores.get)
    put(
        f"市场第{leader['market_rank']}｜最强项目：{strongest} {top_scores[strongest]:.2f}分",
        470, 1190, 96, COLORS["muted"], True, tag="冠军说明",
    )
    weights = leader["fusion"]["top_level_weights"]
    put("三体系权重", 2860, 905, 96, COLORS["blue"], True, tag="权重标签")
    put(
        f"大牛线 {weights['大牛线撑压版']:.2f}%｜飞龙 {weights['飞龙在天']:.2f}%",
        2860, 1035, 136, COLORS["ink"], True, tag="大牛线和飞龙权重", role="primary",
    )
    put(
        f"庄家 {weights['庄家资金监控']:.2f}%｜合计 100%",
        2860, 1205, 136, COLORS["muted"], True, tag="庄家权重", role="primary",
    )
    put("唯一总分口径", 5280, 905, 96, COLORS["gold"], True, tag="总分标签")
    put("体系加权基础分＋共振加分", 5280, 1050, 128, COLORS["ink"], True, tag="公式上", role="core")
    put("－体系分歧扣分｜限制在0至100分", 5280, 1195, 128, COLORS["muted"], True, tag="公式下", role="core")

    table_x1, table_x2, table_y = 230, 7450, 1370
    header_h = 145
    row_area_h = 2240
    poster_rows = rows
    visible_stock_labels: list[str] = []
    if len(rows) <= 16:
        columns = [
            (table_x1, 320, "板块"),
            (table_x1 + 320, 1400, "股票"),
            (table_x1 + 1720, 600, "市场"),
            (table_x1 + 2320, 650, "总分"),
            (table_x1 + 2970, 700, "大牛线"),
            (table_x1 + 3670, 700, "飞龙在天"),
            (table_x1 + 4370, 700, "庄家资金"),
            (table_x1 + 5070, 700, "基础分"),
            (table_x1 + 5770, 650, "共振"),
            (table_x1 + 6420, 650, "分歧"),
        ]
        rectangle((table_x1, table_y, table_x2, table_y + header_h), COLORS["navy"], radius=18)
        for x, width, label in columns:
            put(label, x + width // 2, table_y + 76, 96, COLORS["paper"], True, "mm", f"表头{label}")

        row_h = min(194, row_area_h // len(rows))
        for index, row in enumerate(poster_rows):
            y = table_y + header_h + index * row_h
            fill = COLORS["gold_light"] if index == 0 else COLORS["green_light"] if index < 3 else COLORS["gray_band"] if index % 2 else COLORS["paper"]
            rectangle((table_x1, y, table_x2, y + row_h), fill, COLORS["line"], 2)
            accent = COLORS["gold"] if index == 0 else COLORS["green"] if index < 3 else COLORS["blue"]
            rectangle((table_x1, y, table_x1 + 14, y + row_h), accent)
            formula_scores = row["formula_scores"]
            fusion = row["fusion"]
            stock_label = f"{row['name']}  {row['symbol'][:6]}"
            visible_stock_labels.append(f"{row['name']} {row['symbol'][:6]}")
            values = [
                str(row["rank"]), stock_label, f"第{row['market_rank']}",
                f"{row['score']:.2f}", f"{formula_scores['大牛线撑压版']:.2f}",
                f"{formula_scores['飞龙在天']:.2f}", f"{formula_scores['庄家资金监控']:.2f}",
                f"{fusion['base_score']:.2f}", f"＋{fusion['resonance_bonus']:.2f}",
                f"－{fusion['disagreement_penalty']:.2f}",
            ]
            sizes = [96] * 10
            colors = [accent, COLORS["ink"], COLORS["muted"], accent] + [COLORS["ink"]] * 6
            bolds = [True, True, True, True, False, False, False, False, True, True]
            for col_index, ((x, width, _), value, size, color, bold) in enumerate(zip(columns, values, sizes, colors, bolds)):
                put(value, x + width // 2, y + row_h // 2, size, color, bold, "mm", f"第{index + 1}行第{col_index + 1}列")
    else:
        panel_count = 3
        rows_per_panel = (len(rows) + panel_count - 1) // panel_count
        if rows_per_panel > 8:
            raise RuntimeError("综合评分成分过多，单张海报无法在最小字号限制内完整展示")
        panel_gap = 54
        panel_width = (table_x2 - table_x1 - panel_gap * (panel_count - 1)) // panel_count
        row_h = min(255, row_area_h // rows_per_panel)
        for panel_index in range(panel_count):
            start = panel_index * rows_per_panel
            panel_rows = rows[start:start + rows_per_panel]
            if not panel_rows:
                continue
            panel_x1 = table_x1 + panel_index * (panel_width + panel_gap)
            panel_x2 = panel_x1 + panel_width
            rectangle((panel_x1, table_y, panel_x2, table_y + header_h), COLORS["navy"], radius=18)
            put(
                f"第{panel_rows[0]['rank']}至{panel_rows[-1]['rank']}名｜股票与三体系分",
                (panel_x1 + panel_x2) // 2,
                table_y + 76,
                96,
                COLORS["paper"],
                True,
                "mm",
                f"第{panel_index + 1}栏表头",
            )
            for row_index, row in enumerate(panel_rows):
                index = start + row_index
                y = table_y + header_h + row_index * row_h
                fill = COLORS["gold_light"] if index == 0 else COLORS["green_light"] if index < 3 else COLORS["gray_band"] if index % 2 else COLORS["paper"]
                rectangle((panel_x1, y, panel_x2, y + row_h), fill, COLORS["line"], 2)
                accent = COLORS["gold"] if index == 0 else COLORS["green"] if index < 3 else COLORS["blue"]
                rectangle((panel_x1, y, panel_x1 + 14, y + row_h), accent)
                formula_scores = row["formula_scores"]
                stock_label = f"{row['name']}  {row['symbol'][:6]}"
                visible_stock_labels.append(f"{row['name']} {row['symbol'][:6]}")
                put(str(row["rank"]), panel_x1 + 80, y + 72, 96, accent, True, "mm", f"第{index + 1}行排名")
                put(stock_label, panel_x1 + 180, y + 72, 96, COLORS["ink"], True, "lm", f"第{index + 1}行股票")
                put(f"{row['score']:.2f}", panel_x2 - 80, y + 72, 136, accent, True, "rm", f"第{index + 1}行总分", role="primary")
                put(
                    f"大牛 {formula_scores['大牛线撑压版']:.2f}｜飞龙 {formula_scores['飞龙在天']:.2f}｜庄家 {formula_scores['庄家资金监控']:.2f}",
                    panel_x1 + 180,
                    y + 190,
                    96,
                    COLORS["muted"],
                    False,
                    "lm",
                    f"第{index + 1}行三体系",
                )

    rectangle((300, 3785, 7380, 4205), COLORS["paper"], COLORS["line"], 4, 24)
    put("模型状态", 470, 3915, 96, COLORS["red"], True, tag="模型标签")
    model_status_text = (
        "三十项结构预测｜未来五至十日"
        if research_only
        else "正式预测模型｜预测验收通过"
    )
    put(model_status_text, 470, 4080, 136, COLORS["ink"], True, tag="模型值", role="primary")
    put("数据边界", 2850, 3930, 96, COLORS["blue"], True, tag="数据标签")
    put("固定30项先形成三体系子分｜三体系权重合计100%｜不增加其他项目", 2850, 4055, 96, COLORS["ink"], True, tag="数据值")
    put("预测边界", 6400, 3930, 96, COLORS["gold"], True, tag="用途标签")
    put("方向判断不是概率", 6400, 4055, 96, COLORS["ink"], True, tag="用途值")
    put(f"单张海报完整展示板块全部{len(rows)}只成分｜预测失效条件见完整报告", 3840, 4280, 96, COLORS["muted"], False, "ms", "底注")

    visible = "".join(visible_texts)
    allowed_stock_name_english = {
        token
        for row in rows
        for token in re.findall(r"[A-Za-z]+", str(row.get("name", "")))
    }
    english = sorted(
        set(re.findall(r"[A-Za-z]+", visible)) - allowed_stock_name_english
    )
    forbidden = [word for word in ("买点", "卖点") if word in visible]
    overlaps: list[dict[str, Any]] = []
    for left_index, (left_tag, left_box) in enumerate(text_boxes):
        for right_tag, right_box in text_boxes[left_index + 1:]:
            x_overlap = min(left_box[2], right_box[2]) - max(left_box[0], right_box[0])
            y_overlap = min(left_box[3], right_box[3]) - max(left_box[1], right_box[1])
            if x_overlap > 3 and y_overlap > 3:
                overlaps.append({"left": left_tag, "right": right_tag})
    clipped_text = [
        tag for tag, box in text_boxes
        if box[0] < 0 or box[1] < 0 or box[2] > WIDTH or box[3] > HEIGHT
    ]

    preview = output.with_name(f"{output.stem}-preview-1920x1080.png")
    preview.unlink(missing_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)
    image.resize((1920, 1080), Image.Resampling.LANCZOS).save(
        preview,
        format="PNG",
        optimize=True,
    )
    brightness = sum(ImageStat.Stat(image.resize((160, 90))).mean[:3]) / 3.0
    validation = {
        "width": image.width,
        "height": image.height,
        "preview_width": 1920,
        "preview_height": 1080,
        "preview_path": str(preview),
        "minimum_font_px": min(used_sizes),
        "minimum_preview_font_px": min(used_sizes) * 1920 / WIDTH,
        "core_body_preview_font_px": min(role_sizes["core"]) * 1920 / WIDTH,
        "primary_preview_font_px": min(role_sizes["primary"]) * 1920 / WIDTH,
        "mean_brightness": round(brightness, 2),
        "visible_english": english,
        "forbidden_words": forbidden,
        "poster_row_count": len(poster_rows),
        "expected_poster_row_count": len(rows),
        "source_stock_count": len(rows),
        "board_constituent_count": int(payload["board"]["constituent_count"]),
        "visible_stock_labels": visible_stock_labels,
        "fixed_item_count": 30,
        "top_level_system_count": 3,
        "board_name_visible": board_name in visible,
        "research_only_visible": (
            not research_only or "三十项结构预测｜未来五至十日" in visible
        ),
        "overlaps": overlaps,
        "clipped_text": clipped_text,
    }
    validation["passed"] = (
        image.size == (7680, 4320)
        and preview.is_file()
        and validation["minimum_font_px"] >= COMPOSITE_MINIMUM_FONT
        and validation["minimum_preview_font_px"] >= 24
        and validation["core_body_preview_font_px"] >= 32
        and validation["primary_preview_font_px"] >= 34
        and validation["mean_brightness"] >= 190
        and not english and not forbidden and not overlaps and not clipped_text
        and validation["fixed_item_count"] == 30
        and validation["top_level_system_count"] == 3
        and validation["board_name_visible"]
        and validation["research_only_visible"]
        and visible_stock_labels == [f"{row['name']} {row['symbol'][:6]}" for row in rows]
        and len(poster_rows) == len(rows) == int(payload["board"]["constituent_count"])
    )
    if not validation["passed"]:
        output.unlink(missing_ok=True)
        preview.unlink(missing_ok=True)
        raise RuntimeError(f"综合评分海报验收失败：{validation}")
    return validation


MODEL_SCORE_STANDARDS = {
    "dnx_main_trend": "趋势位置和线体斜率越强越优",
    "dnx_ema_layers": "五项多头条件满足率，越高越优",
    "dnx_k_color": "五日均线高于二十日均线时评分更高",
    "dnx_dx": "短线动量及当日变化越强越优",
    "dnx_control": "控盘程度原值，越高越优",
    "dnx_caishen": "财神线相对神线越强越优",
    "dnx_dealer_in_out": "庄进优先，庄出扣减，其余中性",
    "dnx_dragon_pullback": "出现龙回头信号时评分更高",
    "dnx_ignition": "出现点火或第九输出信号时评分更高",
    "dnx_boll_ma": "布林位置和均线强度越高越优",
    "fl_box": "近36日出现实体重叠箱体",
    "fl_wave": "波值及当日变化越强越优",
    "fl_segment": "段值及当日变化越强越优",
    "zj_control_degree": "控盘程度越高越优",
    "zj_cost_pressure": "成本压力越低越优",
    "zj_fund_strength": "资金强度越高越优",
    "zj_control_spread": "控盘差值越高越优",
}

MODEL_DISPLAY_NAMES = {
    "dnx_ema_layers": ["指数均线分层"],
    "dnx_k_color": ["日线颜色信号"],
    "dnx_dx": ["短线动量指标"],
    "dnx_dealer_in_out": ["庄进与庄出"],
    "dnx_theme_resonance": ["起爆与题材共振"],
    "dnx_boll_ma": ["布林线与多重均线"],
    "fl_trend_filter": ["趋势过滤", "中长期均线强势条件"],
    "fl_box": ["四日实体重叠箱体", "波段密码底层形态"],
    "fl_unique_limit": ["首板与唯一涨停确认"],
    "fl_surge": ["量价模型与暴涨启动"],
    "fl_wave": ["波段随机强弱之波"],
    "fl_segment": ["波段随机强弱之段"],
    "zj_cost_pressure": ["成本压力"],
    "zj_fund_strength": ["资金强度"],
    "zj_control_spread": ["控盘差值"],
}


def validate_chinese_poster_text(values: list[str]) -> dict[str, list[str]]:
    visible_english = sorted(set(re.findall(r"[A-Za-z]+", "".join(values))))
    code_pattern = re.compile(r"[=<>+*/\\{}\[\]();|]|[＋－×÷／Σ｜]")
    code_like_expressions = sorted(
        {str(value) for value in values if code_pattern.search(str(value))}
    )
    return {
        "visible_english": visible_english,
        "code_like_expressions": code_like_expressions,
    }


def _model_zero_weight_standard(reason: str) -> str:
    if "历史时点财务快照" in reason:
        return "缺历史时点快照，不计分"
    if "DYNAINFO" in reason:
        return "实时字段不可复原，不计分"
    if "重复绘图输出" in reason:
        return "重复输出，零权重"
    if "公式常量" in reason:
        return "公式常量，零权重"
    return "区分度不足，零权重"


def render_composite_model_poster(
    payload: dict[str, Any],
    output: Path,
) -> dict[str, Any]:
    """Render the fixed 16+10+4 factor, weight and scoring-standard poster."""
    if payload.get("status") != "CLEAN_PASS":
        raise RuntimeError("正式模型不是通过状态")
    model = payload.get("model")
    if not isinstance(model, dict):
        raise RuntimeError("正式模型内容缺失")
    rows = list(model.get("subsystem_weights", []))
    systems = ["大牛线撑压版", "飞龙在天", "庄家资金监控"]
    expected_counts = {"大牛线撑压版": 16, "飞龙在天": 10, "庄家资金监控": 4}
    original_system_weights = dict(model.get("system_weights", {}))
    if len(rows) != 30 or set(original_system_weights) != set(systems):
        raise RuntimeError("正式模型未完整覆盖固定三十项和三套体系")
    system_weights = {
        name: float(original_system_weights[name]) for name in systems
    }

    grouped = {name: [row for row in rows if row.get("formula") == name] for name in systems}
    if any(len(grouped[name]) != expected_counts[name] for name in systems):
        raise RuntimeError("正式模型的16＋10＋4顺序或数量不完整")
    if any(
        [int(row.get("number", 0)) for row in grouped[name]]
        != list(range(1, expected_counts[name] + 1))
        for name in systems
    ):
        raise RuntimeError("正式模型因子顺序不符合固定清单")

    local_weight_sum_failures = [
        name
        for name in systems
        if abs(sum(float(row["local_weight"]) for row in grouped[name]) - 100.0) > 1e-5
    ]
    system_weight_sum = round(sum(float(system_weights[name]) for name in system_weights), 8)
    if local_weight_sum_failures or abs(system_weight_sum - 100.0) > 1e-5:
        raise RuntimeError("正式模型权重未归一")

    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    draw = ImageDraw.Draw(image)
    visible_texts: list[str] = []
    used_sizes: list[int] = []
    text_boxes: list[tuple[str, tuple[int, int, int, int]]] = []

    def rectangle(
        xy: tuple[int, int, int, int],
        fill: str,
        outline: str | None = None,
        width: int = 1,
        radius: int = 0,
    ) -> None:
        if radius:
            draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
        else:
            draw.rectangle(xy, fill=fill, outline=outline, width=width)

    def put(
        value: str,
        x: int,
        y: int,
        size: int,
        color: str = COLORS["ink"],
        bold: bool = False,
        anchor: str = "ls",
        tag: str = "",
        maximum_width: int | None = None,
    ) -> None:
        selected_font = font(size, bold)
        box = draw.textbbox((x, y), str(value), font=selected_font, anchor=anchor)
        if maximum_width is not None and box[2] - box[0] > maximum_width:
            raise RuntimeError(f"海报文字超出列宽：{tag or value}")
        visible_texts.append(str(value))
        used_sizes.append(size)
        text_boxes.append((tag or str(value), box))
        draw.text((x, y), str(value), font=selected_font, fill=color, anchor=anchor)

    rectangle((0, 0, 42, HEIGHT), COLORS["gold"])
    rectangle((42, 0, WIDTH, 30), COLORS["gold_light"])
    put("三体系综合评分模型", 290, 290, 184, COLORS["ink"], True, tag="主标题")
    put(
        "固定三体系三十项　评分项目・评分权重・评分标准",
        300, 475, 82, COLORS["blue"], True, tag="副标题",
    )
    put("正式审计结构模型", 7380, 245, 82, COLORS["red"], True, "rs", "模型状态")
    generated = str(payload.get("generated_at", ""))[:10].replace("-", "年", 1).replace("-", "月", 1)
    if generated:
        generated += "日"
    put(f"模型日期 {generated}", 7380, 385, 72, COLORS["muted"], True, "rs", "模型日期")

    card_specs = [
        (280, 2520, "大牛线　十六项", systems[0], COLORS["navy_light"], COLORS["navy"]),
        (2620, 4860, "飞龙在天　十项", systems[1], COLORS["green_light"], COLORS["green"]),
        (4960, 7400, "庄家资金　四项", systems[2], COLORS["gold_light"], COLORS["gold"]),
    ]
    for index, (x1, x2, label, weight_name, fill, accent) in enumerate(card_specs):
        rectangle((x1, 565, x2, 955), fill, accent, 5, 8)
        put(label, x1 + 150, 725, 86, accent, True, tag=f"体系{index + 1}")
        put(
            f"项目权重 {float(system_weights[weight_name]):.3f}%",
            x1 + 150, 870, 112, COLORS["ink"], True, tag=f"体系权重{index + 1}",
        )

    rectangle((280, 1005, 7400, 1260), COLORS["paper"], COLORS["line"], 4, 8)
    put("权重列左侧为体系内权重，右侧为总分基础权重", 430, 1110, 76, COLORS["navy"], True, tag="权重图例")
    put(
        "每项先按同日全市场百分位换算，再按体系内权重形成子分",
        430, 1210, 72, COLORS["muted"], True, tag="子分公式",
    )
    put(
        "共振奖励系数百分之八，分歧扣减系数百分之八，总分最高一百分",
        3550, 1160, 76, COLORS["gold"], True, "lm", "总分公式",
    )

    panel_specs = [
        (240, 3090, 146, grouped[systems[0]], COLORS["navy"], COLORS["navy_light"], 720),
        (3170, 5520, 232, grouped[systems[1]], COLORS["green"], COLORS["green_light"], 720),
        (5600, 7440, 580, grouped[systems[2]], COLORS["gold"], COLORS["gold_light"], 480),
    ]

    for panel_index, (x1, x2, row_height, panel_rows, accent, light, factor_width) in enumerate(panel_specs):
        panel_top = 1340
        header_bottom = 1480
        number_width = 90
        weight_width = 680 if panel_index < 2 else 570
        factor_start = x1 + number_width
        weight_start = factor_start + factor_width
        standard_start = weight_start + weight_width
        rectangle((x1, panel_top, x2, header_bottom), accent, radius=8)
        put("序", x1 + number_width // 2, 1410, 72, COLORS["paper"], True, "mm", f"表头序{panel_index}")
        put("评分因子", factor_start + factor_width // 2, 1410, 72, COLORS["paper"], True, "mm", f"表头因子{panel_index}")
        put("权重", weight_start + weight_width // 2, 1410, 72, COLORS["paper"], True, "mm", f"表头权重{panel_index}")
        put("评分标准", standard_start + (x2 - standard_start) // 2, 1410, 72, COLORS["paper"], True, "mm", f"表头标准{panel_index}")

        for row_index, row in enumerate(panel_rows):
            y1 = header_bottom + row_index * row_height
            y2 = y1 + row_height
            zero_weight = float(row["local_weight"]) == 0.0
            fill = COLORS["gray_band"] if zero_weight else light if row_index % 2 == 0 else COLORS["paper"]
            rectangle((x1, y1, x2, y2), fill, COLORS["line"], 2)
            rectangle((x1, y1, x1 + 10, y2), COLORS["muted"] if zero_weight else accent)
            center_y = (y1 + y2) // 2
            put(str(row["number"]), x1 + number_width // 2, center_y, 72, accent, True, "mm", f"序号{panel_index}-{row_index}")

            display_lines = MODEL_DISPLAY_NAMES.get(str(row["key"]), [str(row["name"])])
            if len(display_lines) == 1:
                put(
                    display_lines[0], factor_start + 25, center_y, 72, COLORS["ink"], True, "lm",
                    f"因子{panel_index}-{row_index}", factor_width - 45,
                )
            else:
                put(
                    display_lines[0], factor_start + 25, center_y - 43, 72, COLORS["ink"], True, "lm",
                    f"因子上{panel_index}-{row_index}", factor_width - 45,
                )
                put(
                    display_lines[1], factor_start + 25, center_y + 43, 72, COLORS["ink"], True, "lm",
                    f"因子下{panel_index}-{row_index}", factor_width - 45,
                )

            local_weight = float(row["local_weight"])
            effective_weight = local_weight * float(system_weights[str(row["formula"])]) / 100.0
            if panel_index == 2:
                put(
                    f"内{local_weight:.3f}", weight_start + weight_width // 2, center_y - 44, 72,
                    COLORS["red"] if zero_weight else accent, True, "mm",
                    f"内权重{panel_index}-{row_index}", weight_width - 30,
                )
                put(
                    f"总{effective_weight:.3f}", weight_start + weight_width // 2, center_y + 44, 72,
                    COLORS["red"] if zero_weight else accent, True, "mm",
                    f"总权重{panel_index}-{row_index}", weight_width - 30,
                )
            else:
                weight_text = f"内{local_weight:.3f} 总{effective_weight:.3f}"
                put(
                    weight_text, weight_start + weight_width // 2, center_y, 72,
                    COLORS["red"] if zero_weight else accent, True, "mm",
                    f"权重{panel_index}-{row_index}", weight_width - 30,
                )
            standard = (
                _model_zero_weight_standard(str(row.get("forced_zero_reason", "")))
                if zero_weight
                else MODEL_SCORE_STANDARDS[str(row["key"])]
            )
            put(
                standard, standard_start + 24, center_y, 72, COLORS["muted"] if zero_weight else COLORS["ink"],
                True, "lm", f"标准{panel_index}-{row_index}", x2 - standard_start - 42,
            )

    rectangle((280, 3910, 7400, 4270), COLORS["navy_light"], COLORS["navy"], 4, 8)
    put(
        "固定三十项仅来自大牛线、飞龙在天和庄家资金监控",
        430, 4015, 76, COLORS["navy"], True, tag="固定项目",
    )
    put(
        "每项只在所属体系内部形成子分；重复输出、常量与不可回溯字段保持零权重审计",
        430, 4125, 72, COLORS["ink"], True, tag="体系内标准",
    )
    put(
        "三体系融合　大牛线、飞龙在天与庄家资金监控权重合计百分之百",
        430, 4235, 72, COLORS["navy"], True, tag="审计提示",
    )

    overlaps: list[dict[str, str]] = []
    for left_index, (left_tag, left_box) in enumerate(text_boxes):
        for right_tag, right_box in text_boxes[left_index + 1:]:
            x_overlap = min(left_box[2], right_box[2]) - max(left_box[0], right_box[0])
            y_overlap = min(left_box[3], right_box[3]) - max(left_box[1], right_box[1])
            if x_overlap > 3 and y_overlap > 3:
                overlaps.append({"left": left_tag, "right": right_tag})
    clipped_text = [
        tag for tag, box in text_boxes
        if box[0] < 0 or box[1] < 0 or box[2] > WIDTH or box[3] > HEIGHT
    ]
    language_validation = validate_chinese_poster_text(visible_texts)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)
    brightness = sum(ImageStat.Stat(image.resize((160, 90))).mean[:3]) / 3.0
    validation = {
        "width": image.width,
        "height": image.height,
        "factor_count": len(rows),
        "system_count": len(systems),
        "minimum_font_px": min(used_sizes),
        "mean_brightness": round(brightness, 2),
        "overlaps": overlaps,
        "clipped_text": clipped_text,
        "local_weight_sum_failures": local_weight_sum_failures,
        "system_weight_sum": round(system_weight_sum, 6),
        **language_validation,
    }
    validation["passed"] = (
        image.size == (7680, 4320)
        and validation["factor_count"] == 30
        and validation["system_count"] == 3
        and validation["minimum_font_px"] >= MINIMUM_FONT
        and validation["mean_brightness"] >= 190
        and not overlaps and not clipped_text and not local_weight_sum_failures
        and not validation["visible_english"]
        and not validation["code_like_expressions"]
        and abs(validation["system_weight_sum"] - 100.0) <= 1e-5
    )
    if not validation["passed"]:
        output.unlink(missing_ok=True)
        raise RuntimeError(f"综合评分模型海报验收失败：{validation}")
    return validation


def render_composite_structure_poster(
    payload: dict[str, Any],
    output: Path,
) -> dict[str, Any]:
    """Render the fixed 30-item scoring architecture without claiming model approval."""
    if payload.get("status") != "CLEAN_PASS":
        raise RuntimeError("评分结构海报源数据不是通过状态")
    model = payload.get("model")
    if not isinstance(model, dict):
        raise RuntimeError("评分结构海报缺少模型结构")

    systems = ["大牛线撑压版", "飞龙在天", "庄家资金监控"]
    expected_counts = {"大牛线撑压版": 16, "飞龙在天": 10, "庄家资金监控": 4}
    rows = list(model.get("subsystem_weights", []))
    original_system_weights = dict(model.get("system_weights", {}))
    if len(rows) != 30 or set(original_system_weights) != set(systems):
        raise RuntimeError("评分结构源未完整覆盖固定三十项和三套体系")
    grouped = {
        name: [row for row in rows if row.get("formula") == name]
        for name in systems
    }
    if any(len(grouped[name]) != expected_counts[name] for name in systems):
        raise RuntimeError("评分结构源的十六项、十项、四项不完整")
    system_weights = {
        name: float(original_system_weights[name]) for name in systems
    }
    system_weight_sum = round(sum(float(value) for value in system_weights.values()), 8)
    if abs(system_weight_sum - 100.0) > 1e-5:
        raise RuntimeError("评分结构三体系权重未归一")

    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    draw = ImageDraw.Draw(image)
    visible_texts: list[str] = []
    used_sizes: list[int] = []
    role_sizes: dict[str, list[int]] = {"minimum": [], "core": [], "primary": []}
    text_boxes: list[tuple[str, tuple[int, int, int, int]]] = []

    def rectangle(
        xy: tuple[int, int, int, int],
        fill: str,
        outline: str | None = None,
        width: int = 1,
        radius: int = 0,
    ) -> None:
        if radius:
            draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
        else:
            draw.rectangle(xy, fill=fill, outline=outline, width=width)

    def put(
        value: str,
        x: int,
        y: int,
        size: int,
        color: str = COLORS["ink"],
        bold: bool = False,
        anchor: str = "ls",
        tag: str = "",
        maximum_width: int | None = None,
        role: str = "minimum",
    ) -> None:
        value = str(value)
        selected_font = font(size, bold)
        box = draw.textbbox((x, y), value, font=selected_font, anchor=anchor)
        if maximum_width is not None and box[2] - box[0] > maximum_width:
            raise RuntimeError(f"评分结构海报文字超出列宽：{tag or value}")
        visible_texts.append(value)
        used_sizes.append(size)
        role_sizes[role].append(size)
        text_boxes.append((tag or value, box))
        draw.text((x, y), value, font=selected_font, fill=color, anchor=anchor)

    def factor_name(row: dict[str, Any]) -> str:
        display = MODEL_DISPLAY_NAMES.get(str(row.get("key")))
        if display:
            return str(display[0])
        value = str(row.get("name", ""))
        return (
            value.replace("/", "与")
            .replace("+", "与")
            .replace("-", "之")
        )

    rectangle((0, 0, 48, HEIGHT), COLORS["gold"])
    rectangle((48, 0, WIDTH, 32), COLORS["gold_light"])
    put("大牛线综合评分系统", 300, 285, 216, COLORS["ink"], True, tag="主标题", role="primary")
    put(
        "固定三十项　评分项目、权重与分值",
        305, 505, 112, COLORS["blue"], True, tag="副标题",
    )
    put("评分结构说明", 7380, 260, 128, COLORS["red"], True, "rs", "状态", role="core")
    source_date = str(payload.get("weight_source_date", ""))
    put(
        f"三体系比例来源 {source_date}",
        7380, 445, 96, COLORS["muted"], True, "rs", "比例来源日期",
    )

    metrics = [
        ("30", "固定评分项目", COLORS["navy"], COLORS["navy_light"]),
        ("3", "顶层评分体系", COLORS["green"], COLORS["green_light"]),
        ("0至100", "综合分值范围", COLORS["gold"], COLORS["gold_light"]),
        ("100%", "三体系权重合计", COLORS["red"], COLORS["red_light"]),
    ]
    for index, (value, label, accent, light) in enumerate(metrics):
        x1 = 280 + index * 1810
        x2 = x1 + 1690
        rectangle((x1, 620, x2, 1035), light, accent, 5, 8)
        put(value, (x1 + x2) // 2, 790, 176, accent, True, "mm", f"指标值{index}", role="primary")
        put(label, (x1 + x2) // 2, 965, 128, COLORS["ink"], True, "mm", f"指标名{index}", role="core")

    panel_specs = [
        (280, 2520, "大牛线撑压版", "十六项", systems[0], COLORS["navy"], COLORS["navy_light"]),
        (2650, 4890, "飞龙在天", "十项", systems[1], COLORS["green"], COLORS["green_light"]),
        (5020, 7400, "庄家资金监控", "四项", systems[2], COLORS["gold"], COLORS["gold_light"]),
    ]
    for index, (x1, x2, title, count_label, weight_name, accent, light) in enumerate(panel_specs):
        rectangle((x1, 1120, x2, 3560), COLORS["paper"], COLORS["line"], 4, 8)
        rectangle((x1, 1120, x2, 1745), light, accent, 5, 8)
        put(title, x1 + 120, 1300, 128, accent, True, tag=f"项目名{index}", role="core")
        put(count_label, x2 - 120, 1300, 96, accent, True, "rs", f"项目数{index}")
        weight_value = float(system_weights[weight_name])
        put(
            f"权重 {weight_value:.3f}%", x1 + 120, 1510, 176, COLORS["ink"], True,
            tag=f"项目权重{index}", role="primary",
        )
        put(
            "项目分值 0至100分", x1 + 120, 1690, 136, COLORS["muted"], True,
            tag=f"项目分值{index}", role="primary",
        )

    for row_index, row in enumerate(grouped[systems[0]]):
        y = 1860 + row_index * 104
        put(f"{row_index + 1:02d}", 400, y, 96, COLORS["navy"], True, tag=f"大牛线序{row_index}")
        put(factor_name(row), 620, y, 96, COLORS["ink"], True, tag=f"大牛线因子{row_index}", maximum_width=1800)

    for row_index, row in enumerate(grouped[systems[1]]):
        y = 1880 + row_index * 145
        put(f"{row_index + 1:02d}", 2770, y, 96, COLORS["green"], True, tag=f"飞龙序{row_index}")
        put(factor_name(row), 2990, y, 96, COLORS["ink"], True, tag=f"飞龙因子{row_index}", maximum_width=1750)
    put("十项先形成飞龙子分", 2770, 3400, 128, COLORS["green"], True, tag="飞龙说明", role="core")

    for row_index, row in enumerate(grouped[systems[2]]):
        y = 1900 + row_index * 185
        put(f"{row_index + 1:02d}", 5140, y, 96, COLORS["gold"], True, tag=f"庄家序{row_index}")
        put(factor_name(row), 5360, y, 96, COLORS["ink"], True, tag=f"庄家因子{row_index}", maximum_width=1850)
    put("四项先形成庄家资金子分", 5140, 2790, 128, COLORS["gold"], True, tag="庄家说明一", role="core")
    put("零权重项目保留审计，不补分", 5140, 2980, 128, COLORS["ink"], True, tag="庄家说明二", role="core")

    rectangle((280, 3635, 7400, 4290), COLORS["paper"], COLORS["line"], 4, 8)
    rectangle((280, 3635, 320, 4290), COLORS["red"])
    put(
        "总分由三体系加权基础分、共振加分与分歧扣分共同形成",
        430, 3825, 144, COLORS["navy"], True, tag="总分公式", role="primary",
    )
    put(
        f"权重来源　{source_date}最后一次已执行模型比例，三体系权重合计百分之百",
        430, 3990, 104, COLORS["muted"], True, tag="权重来源", maximum_width=6750,
    )
    put(
        "当前正式预测验收未通过；本海报展示评分结构，不授权生产评分",
        430, 4135, 128, COLORS["red"], True, tag="模型边界", role="core",
    )
    put(
        "固定三十项之外不增加评分项目；研究用途，不构成交易依据",
        430, 4265, 128, COLORS["ink"], True, tag="用途边界", role="core",
    )

    overlaps: list[dict[str, str]] = []
    for left_index, (left_tag, left_box) in enumerate(text_boxes):
        for right_tag, right_box in text_boxes[left_index + 1:]:
            x_overlap = min(left_box[2], right_box[2]) - max(left_box[0], right_box[0])
            y_overlap = min(left_box[3], right_box[3]) - max(left_box[1], right_box[1])
            if x_overlap > 3 and y_overlap > 3:
                overlaps.append({"left": left_tag, "right": right_tag})
    clipped_text = [
        tag for tag, box in text_boxes
        if box[0] < 0 or box[1] < 0 or box[2] > WIDTH or box[3] > HEIGHT
    ]
    language_validation = validate_chinese_poster_text(visible_texts)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)
    preview = output.with_name(f"{output.stem}-preview-1920x1080.png")
    image.resize((1920, 1080), Image.Resampling.LANCZOS).save(preview, format="PNG", optimize=True)
    brightness = sum(ImageStat.Stat(image.resize((160, 90))).mean[:3]) / 3.0
    preview_scale = 1920 / WIDTH
    validation = {
        "width": image.width,
        "height": image.height,
        "preview_width": 1920,
        "preview_height": 1080,
        "preview_path": str(preview),
        "factor_count": len(rows),
        "system_count": len(systems),
        "minimum_font_px": min(used_sizes),
        "minimum_preview_font_px": min(used_sizes) * preview_scale,
        "core_body_preview_font_px": min(role_sizes["core"]) * preview_scale,
        "primary_preview_font_px": min(role_sizes["primary"]) * preview_scale,
        "mean_brightness": round(brightness, 2),
        "overlaps": overlaps,
        "clipped_text": clipped_text,
        "system_weight_sum": round(system_weight_sum, 6),
        "system_weights": {name: round(float(value), 8) for name, value in system_weights.items()},
        **language_validation,
    }
    validation["passed"] = (
        image.size == (7680, 4320)
        and preview.is_file()
        and validation["factor_count"] == 30
        and validation["system_count"] == 3
        and validation["minimum_preview_font_px"] >= 24
        and validation["core_body_preview_font_px"] >= 32
        and validation["primary_preview_font_px"] >= 34
        and validation["mean_brightness"] >= 190
        and not overlaps and not clipped_text
        and not validation["visible_english"]
        and not validation["code_like_expressions"]
        and abs(validation["system_weight_sum"] - 100.0) <= 1e-5
    )
    if not validation["passed"]:
        output.unlink(missing_ok=True)
        preview.unlink(missing_ok=True)
        raise RuntimeError(f"综合评分结构海报验收失败：{validation}")
    return validation
