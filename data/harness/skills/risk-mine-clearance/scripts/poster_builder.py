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
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont


WIDTH = 7680
HEIGHT = 4320
PREVIEW_WIDTH = 1920
PREVIEW_HEIGHT = 1080
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
SHANGHAI = ZoneInfo("Asia/Shanghai")

BACKGROUND = (248, 250, 247)
INK = (28, 45, 43)
MUTED = (79, 91, 88)
WHITE = (255, 255, 255)
BORDER = (214, 223, 218)

CARDS = (
    {
        "title": "监管与退市",
        "accent": (18, 126, 116),
        "fill": (232, 247, 242),
        "lines": (
            "立案 / 处罚 / 警示函",
            "问询 / 重大违法",
            "退市风险 / 终止上市",
            "ST 与停复牌单独核验",
        ),
    },
    {
        "title": "偿债与司法",
        "accent": (221, 78, 65),
        "fill": (253, 238, 234),
        "lines": (
            "债务、贷款逾期 / 无法清偿",
            "账户或股份冻结 / 执行",
            "重大诉讼 / 仲裁",
            "破产重整 / 持续经营异常",
        ),
    },
    {
        "title": "财务与经营",
        "accent": (44, 111, 173),
        "fill": (235, 244, 252),
        "lines": (
            "预亏 / 预减 / 会计差错",
            "商誉、资产减值 / 坏账",
            "停产事故 / 订单客户变化",
            "回款、库存、借款异常",
        ),
    },
    {
        "title": "担保质押与资本",
        "accent": (190, 133, 29),
        "fill": (252, 246, 226),
        "lines": (
            "违规担保 / 担保压力",
            "高比例质押 / 补充质押",
            "解禁、减持、解除质押",
            "控制权与治理变化",
        ),
    },
    {
        "title": "票据欠薪与失信",
        "accent": (125, 83, 154),
        "fill": (245, 238, 249),
        "lines": (
            "票交所企业披露",
            "欠薪失信 / 司法失信",
            "核验上市公司与子公司关系",
            "已结清与仍逾期必须分开",
        ),
    },
    {
        "title": "市场与舆情",
        "accent": (42, 139, 84),
        "fill": (235, 247, 233),
        "lines": (
            "价格、换手、热度共振",
            "投资者问答与传闻",
            "指数跌幅 / 涨停数量",
            "只做环境观察，不证实经营风险",
        ),
    },
)

OUTPUT_LEVELS = (
    ("硬剔除", "公开强证据", (221, 78, 65), (253, 238, 234)),
    ("前置核查", "线索待证实", (190, 133, 29), (252, 246, 226)),
    ("票据历史异常", "关系与结清分开", (125, 83, 154), (245, 238, 249)),
    ("市场观察", "只写环境条件", (44, 111, 173), (235, 244, 252)),
)

EVIDENCE_RULES = (
    "同源转载只算 1 个来源",
    "来源 + 日期 + 原文链接",
    "仅计本轮真实返回数据",
    "资本事项无独证不升硬剔除",
)


def load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold and FONT_BOLD.is_file() else FONT_REGULAR
    if not path.is_file():
        raise FileNotFoundError(f"Chinese font missing: {path}")
    return ImageFont.truetype(str(path), size=size)


def missing_glyphs(text: str, font: ImageFont.FreeTypeFont) -> list[str]:
    missing: list[str] = []
    for character in text:
        if character.isspace():
            continue
        if font.getmask(character).getbbox() is None:
            missing.append(character)
    return sorted(set(missing))


def render_poster(version_date: str) -> tuple[Image.Image, dict[str, object]]:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    text_runs: list[dict[str, object]] = []
    unresolved_glyphs: set[str] = set()

    def text(
        xy: tuple[int, int],
        value: str,
        size: int,
        *,
        fill: tuple[int, int, int] = INK,
        bold: bool = False,
        role: str = "body",
        anchor: str = "lt",
    ) -> tuple[int, int, int, int]:
        font = load_font(size, bold=bold)
        unresolved_glyphs.update(missing_glyphs(value, font))
        bbox = tuple(int(item) for item in draw.textbbox(xy, value, font=font, anchor=anchor))
        if bbox[0] < 0 or bbox[1] < 0 or bbox[2] > WIDTH or bbox[3] > HEIGHT:
            raise ValueError(f"text_out_of_bounds:{value}:{bbox}")
        draw.text(xy, value, font=font, fill=fill, anchor=anchor)
        text_runs.append(
            {
                "text": value,
                "font_px": size,
                "preview_font_px": size / 4,
                "role": role,
                "bbox": list(bbox),
            }
        )
        return bbox

    # Header
    text((240, 125), "风险排雷技能", 280, bold=True, role="primary")
    text((240, 500), "排雷项目 · 判定标准 · 证据硬闸", 128, bold=True, role="body")
    text(
        (7440, 210),
        "六大风险域 · 四级处置",
        136,
        fill=(18, 126, 116),
        bold=True,
        role="primary",
        anchor="rt",
    )
    text(
        (7440, 515),
        "研究风控用途 | 不构成投资建议",
        96,
        fill=MUTED,
        role="visible",
        anchor="rt",
    )
    draw.line((240, 735, 7440, 735), fill=BORDER, width=8)

    # Six risk-domain cards.
    card_width = 2346
    card_height = 1000
    card_x = (240, 2667, 5094)
    card_y = (850, 1940)
    for index, card in enumerate(CARDS):
        x = card_x[index % 3]
        y = card_y[index // 3]
        draw.rounded_rectangle(
            (x, y, x + card_width, y + card_height),
            radius=28,
            fill=card["fill"],
            outline=BORDER,
            width=5,
        )
        draw.rectangle((x, y + 28, x + 24, y + card_height - 28), fill=card["accent"])
        draw.ellipse((x + 82, y + 78, x + 270, y + 266), fill=card["accent"])
        text(
            (x + 176, y + 170),
            f"{index + 1:02d}",
            128,
            fill=WHITE,
            bold=True,
            role="visible",
            anchor="mm",
        )
        text(
            (x + 330, y + 92),
            str(card["title"]),
            144,
            bold=True,
            role="primary",
        )
        for line_index, line in enumerate(card["lines"]):
            line_y = y + 350 + line_index * 158
            draw.rectangle(
                (x + 100, line_y + 51, x + 124, line_y + 75),
                fill=card["accent"],
            )
            text((x + 165, line_y), str(line), 128, role="body")

    # Bottom output and evidence band.
    draw.line((240, 3095, 7440, 3095), fill=BORDER, width=8)
    text((240, 3205), "四级处置输出", 152, bold=True, role="primary")
    output_positions = ((240, 3460), (2350, 3460), (240, 3810), (2350, 3810))
    for (title, description, accent, fill), (x, y) in zip(
        OUTPUT_LEVELS, output_positions, strict=True
    ):
        draw.rounded_rectangle(
            (x, y, x + 1990, y + 280),
            radius=28,
            fill=fill,
            outline=accent,
            width=5,
        )
        draw.rectangle((x, y + 28, x + 22, y + 252), fill=accent)
        text((x + 75, y + 28), title, 140, fill=accent, bold=True, role="primary")
        text((x + 75, y + 158), description, 128, role="body")

    text((4680, 3205), "证据硬标准", 152, bold=True, role="primary")
    for index, rule in enumerate(EVIDENCE_RULES):
        y = 3460 + index * 185
        draw.rounded_rectangle(
            (4680, y + 38, 4740, y + 98),
            radius=12,
            fill=(18, 126, 116),
        )
        text((4800, y), rule, 128, role="body")

    footer = f"标准版 {version_date} | 重点结论必须可追溯、可复核、可解除警报"
    text((7440, 4175), footer, 96, fill=MUTED, role="visible", anchor="rt")

    if unresolved_glyphs:
        raise ValueError("missing_glyphs:" + "".join(sorted(unresolved_glyphs)))

    metadata: dict[str, object] = {
        "schema": "RISK_MINE_CLEARANCE_POSTER_V1",
        "status": "BUILT",
        "canvas": {"width": WIDTH, "height": HEIGHT},
        "preview": {
            "width": PREVIEW_WIDTH,
            "height": PREVIEW_HEIGHT,
            "scale": 0.25,
        },
        "version_date": version_date,
        "minimum_source_font_px": min(int(item["font_px"]) for item in text_runs),
        "minimum_body_font_px": min(
            int(item["font_px"]) for item in text_runs if item["role"] == "body"
        ),
        "minimum_primary_font_px": min(
            int(item["font_px"]) for item in text_runs if item["role"] == "primary"
        ),
        "minimum_preview_font_px": min(
            float(item["preview_font_px"]) for item in text_runs
        ),
        "categories": [str(item["title"]) for item in CARDS],
        "output_levels": [item[0] for item in OUTPUT_LEVELS],
        "evidence_rules": list(EVIDENCE_RULES),
        "missing_glyphs": [],
        "text_runs": text_runs,
    }
    return image, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="生成风险排雷技能8K浅色海报")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--version-date")
    args = parser.parse_args()

    version_date = args.version_date or datetime.now(SHANGHAI).date().isoformat()
    image, metadata = render_poster(version_date)
    output = args.output.resolve()
    metadata_path = args.metadata.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True, compress_level=7)
    metadata["poster"] = {"path": str(output), "bytes": output.stat().st_size}

    if args.preview:
        preview = args.preview.resolve()
        preview.parent.mkdir(parents=True, exist_ok=True)
        resized = image.resize((PREVIEW_WIDTH, PREVIEW_HEIGHT), Image.Resampling.LANCZOS)
        resized.save(preview, format="PNG", optimize=True, compress_level=7)
        metadata["preview"]["path"] = str(preview)
        metadata["preview"]["bytes"] = preview.stat().st_size

    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "BUILT", "poster": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
