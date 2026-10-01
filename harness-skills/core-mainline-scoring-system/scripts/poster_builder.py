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
from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


WIDTH = 7680
HEIGHT = 4320
PREVIEW_SIZE = (1920, 1080)
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")

COLORS = {
    "background": "#F4F7FA",
    "paper": "#FFFFFF",
    "ink": "#132A3A",
    "muted": "#5C6F7C",
    "line": "#D7E0E6",
    "blue": "#246B91",
    "blue_light": "#E7F1F7",
    "green": "#277A65",
    "green_light": "#E5F3EE",
    "red": "#B84242",
    "red_light": "#F9EAEA",
    "gold": "#A87512",
    "gold_light": "#F8EFCF",
    "gray_light": "#EEF2F5",
}

WEIGHTS = (
    ("市场强度", 15),
    ("涨停广度", 15),
    ("原梯队质量", 10),
    ("精确3/2/1梯队", 10),
    ("完整成分股规模", 10),
    ("资金结构", 15),
    ("已核验催化", 10),
    ("跨日连续性", 10),
    ("领先优势", 5),
)

STATUS_LABELS = {
    "VERIFIED": "通过",
    "GATE_FAILED": "失败",
    "DEGRADED": "降级",
}

MISSING_LABELS = {
    "constituent_count": "缺成分",
    "catalyst_level": "缺催化级别",
    "runner_up_gap_pct": "缺领先优势",
    "verified_catalyst": "催化未核验",
    "catalyst_source": "缺催化来源",
    "sector_return_pct": "缺板块涨幅",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON对象无效：{path}")
    return payload


@lru_cache(maxsize=None)
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold and FONT_BOLD.is_file() else FONT_REGULAR
    if not path.is_file():
        raise FileNotFoundError(f"中文字体不存在：{path}")
    return ImageFont.truetype(str(path), size=size)


def text_width(draw: ImageDraw.ImageDraw, value: str, size: int, bold: bool = False) -> int:
    box = draw.textbbox((0, 0), value, font=font(size, bold), anchor="lt")
    return int(box[2] - box[0])


def shorten(
    draw: ImageDraw.ImageDraw,
    value: str,
    maximum_width: int,
    size: int,
    bold: bool = False,
) -> str:
    text = str(value)
    if text_width(draw, text, size, bold) <= maximum_width:
        return text
    suffix = "..."
    while text and text_width(draw, text + suffix, size, bold) > maximum_width:
        text = text[:-1]
    return text + suffix


def reason_text(board: dict[str, Any]) -> str:
    status = str(board.get("status", ""))
    if status == "VERIFIED":
        return "通过：证据与门槛完整"
    reasons: list[str] = []
    failures = set(str(item) for item in board.get("gate_failures", []))
    if "three_two_one_ladder_incomplete" in failures:
        evidence = board.get("input_evidence", {})
        missing_ladder = []
        if int(evidence.get("three_board_count", 0) or 0) < 1:
            missing_ladder.append("3板")
        if int(evidence.get("two_board_count", 0) or 0) < 1:
            missing_ladder.append("2板")
        if int(evidence.get("one_board_count", 0) or 0) < 1:
            missing_ladder.append("首板")
        reasons.append("缺" + "/".join(missing_ladder or ["完整梯队"]))
    if "constituent_count_not_greater_than_100" in failures:
        reasons.append("成分股≤100")
    missing = {str(item) for item in board.get("missing_evidence", [])}
    grouped_missing = (
        ("缺成分", {"constituent_count"}),
        ("缺催化", {"catalyst_level", "verified_catalyst", "catalyst_source"}),
        ("缺领先", {"runner_up_gap_pct"}),
        ("缺涨幅", {"sector_return_pct"}),
    )
    grouped_fields: set[str] = set()
    for label, fields in grouped_missing:
        if missing & fields:
            reasons.append(label)
            grouped_fields.update(fields)
    for item in sorted(missing - grouped_fields):
        label = MISSING_LABELS.get(item, "缺其他证据")
        if label not in reasons:
            reasons.append(label)
    prefix = STATUS_LABELS.get(status, status or "未判定")
    return f"{prefix}：{'/'.join(reasons) if reasons else '原因未记录'}"


def layout_errors(text_runs: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    boxes: list[tuple[int, int, int, int]] = []
    for index, run in enumerate(text_runs):
        bbox = tuple(int(value) for value in run["bbox"])
        if bbox[0] < 0 or bbox[1] < 0 or bbox[2] > WIDTH or bbox[3] > HEIGHT:
            errors.append(f"text_out_of_bounds:{index}:{bbox}")
        if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
            errors.append(f"text_bbox_invalid:{index}:{bbox}")
        boxes.append(bbox)
    for left in range(len(boxes)):
        a = boxes[left]
        for right in range(left + 1, len(boxes)):
            b = boxes[right]
            if min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1]):
                errors.append(f"text_overlap:{left}:{right}")
    return errors


def render_poster(
    scoring: dict[str, Any],
    lianban: dict[str, Any],
    output: Path,
    preview: Path,
    metadata_output: Path,
    *,
    scoring_path: Path,
    lianban_path: Path,
) -> dict[str, Any]:
    if scoring.get("execution_status") != "CLEAN_PASS":
        raise RuntimeError("评分结果不是CLEAN_PASS")
    boards = sorted(
        (item for item in scoring.get("boards", []) if isinstance(item, dict)),
        key=lambda item: float(item.get("raw_score", 0) or 0),
        reverse=True,
    )
    if not boards:
        raise RuntimeError("评分结果没有板块")
    summary = scoring.get("summary", {})
    market = lianban.get("market", {}) if isinstance(lianban, dict) else {}
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    draw = ImageDraw.Draw(image)
    text_runs: list[dict[str, Any]] = []

    def rectangle(
        box: tuple[int, int, int, int],
        fill: str,
        outline: str | None = None,
        width: int = 1,
        radius: int = 0,
    ) -> None:
        if radius:
            draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
        else:
            draw.rectangle(box, fill=fill, outline=outline, width=width)

    def put(
        value: Any,
        x: int,
        y: int,
        size: int,
        color: str = COLORS["ink"],
        bold: bool = False,
        *,
        anchor: str = "lt",
        maximum_width: int | None = None,
        role: str = "minimum",
        tag: str = "",
    ) -> str:
        shown = str(value)
        if maximum_width is not None:
            shown = shorten(draw, shown, maximum_width, size, bold)
        selected = font(size, bold)
        bbox = draw.textbbox((x, y), shown, font=selected, anchor=anchor)
        draw.text((x, y), shown, font=selected, fill=color, anchor=anchor)
        text_runs.append({
            "text": shown,
            "font_px": size,
            "role": role,
            "bbox": [int(value) for value in bbox],
            "tag": tag or shown,
        })
        return shown

    rectangle((0, 0, WIDTH, 36), COLORS["gold_light"])
    rectangle((0, 520, 48, 3950), COLORS["blue"])
    put("核心主线评分｜当日市场结论", 320, 115, 208, bold=True, role="primary", tag="主标题")
    put(
        f"模型 {scoring.get('model_version', '')} ｜ 最新运行 {scoring.get('generated_at', '')}",
        325,
        390,
        96,
        COLORS["muted"],
        bold=True,
        maximum_width=7000,
        tag="运行时间",
    )

    rectangle((280, 570, 7400, 1240), COLORS["paper"], COLORS["line"], 4, 8)
    rectangle((280, 570, 318, 1240), COLORS["red"])
    put("严格决策结论", 430, 665, 112, COLORS["red"], True, role="minimum")
    core = summary.get("core_mainline")
    if isinstance(core, dict) and core.get("name"):
        conclusion = f"核心主线：{core['name']}"
    else:
        conclusion = "今日无合格核心主线"
    put(conclusion, 430, 815, 200, COLORS["red"], True, role="primary", maximum_width=6550, tag="核心结论")
    strongest = boards[0]
    strongest_evidence = strongest.get("input_evidence", {})
    candidate_line = (
        f"最强候选：{strongest.get('name', '')} ｜ 原始分{float(strongest.get('raw_score', 0)):.0f} "
        f"｜ 涨幅{float(strongest_evidence.get('sector_return_pct', 0) or 0):+.1f}% "
        f"｜ 涨停{int(strongest_evidence.get('limit_up_count', 0) or 0)}只 ｜ {reason_text(strongest)}"
    )
    put(candidate_line, 435, 1060, 136, COLORS["ink"], True, role="primary", maximum_width=6550, tag="最强候选")

    metric_specs = (
        (str(int(summary.get("board_count", 0) or 0)), "已评分板块", COLORS["blue"], COLORS["blue_light"]),
        (str(int(summary.get("passed_count", 0) or 0)), "通过硬门槛", COLORS["green"], COLORS["green_light"]),
        (str(int(summary.get("gate_failed_count", 0) or 0)), "硬门槛失败", COLORS["red"], COLORS["red_light"]),
        (str(int(summary.get("degraded_count", 0) or 0)), "证据降级", COLORS["gold"], COLORS["gold_light"]),
        (str(market.get("emotion_stage", "未判定")), "市场情绪", COLORS["ink"], COLORS["gray_light"]),
    )
    for index, (value, label, accent, light) in enumerate(metric_specs):
        x1 = 280 + index * 1435
        x2 = x1 + 1310
        rectangle((x1, 1330, x2, 1770), light, accent, 4, 8)
        put(value, (x1 + x2) // 2, 1400, 160, accent, True, anchor="mt", role="primary", tag=f"指标值{index}")
        put(label, (x1 + x2) // 2, 1605, 96, COLORS["ink"], True, anchor="mt", tag=f"指标名{index}")

    put("原始分前五方向｜原始分不等于决策通过", 300, 1840, 128, COLORS["ink"], True, role="body", tag="前五标题")
    columns = (
        ("方向", 320, 760),
        ("原始/决策", 1280, 760),
        ("涨幅", 2280, 500),
        ("涨停", 2980, 500),
        ("精确3/2/1", 3660, 900),
        ("成分股", 4740, 650),
        ("状态与原因", 5300, 2040),
    )
    rectangle((280, 2005, 7400, 2160), COLORS["blue_light"])
    for label, x, width in columns:
        put(label, x, 2030, 96, COLORS["blue"], True, maximum_width=width, tag=f"表头{label}")
    for index, board in enumerate(boards[:5]):
        y1 = 2180 + index * 190
        if index % 2 == 0:
            rectangle((280, y1 - 10, 7400, y1 + 165), COLORS["paper"])
        evidence = board.get("input_evidence", {})
        values = (
            (board.get("name", ""), 320, 760, COLORS["ink"], True),
            (f"{float(board.get('raw_score', 0) or 0):.0f} / {float(board.get('score', 0) or 0):.0f}", 1280, 760, COLORS["red"] if float(board.get("score", 0) or 0) == 0 else COLORS["green"], True),
            (f"{float(evidence.get('sector_return_pct', 0) or 0):+.1f}%", 2280, 500, COLORS["ink"], True),
            (f"{int(evidence.get('limit_up_count', 0) or 0)}只", 2980, 500, COLORS["ink"], True),
            (f"{int(evidence.get('three_board_count', 0) or 0)}/{int(evidence.get('two_board_count', 0) or 0)}/{int(evidence.get('one_board_count', 0) or 0)}", 3660, 900, COLORS["ink"], True),
            (f"{int(evidence.get('constituent_count', 0) or 0)}只", 4740, 650, COLORS["ink"], True),
            (reason_text(board), 5300, 2040, COLORS["red"] if board.get("status") != "VERIFIED" else COLORS["green"], True),
        )
        for column_index, (value, x, width, color, bold) in enumerate(values):
            put(value, x, y1, 128, color, bold, role="body", maximum_width=width, tag=f"前五{index}-{column_index}")

    rectangle((280, 3180, 4720, 3975), COLORS["paper"], COLORS["line"], 4, 8)
    rectangle((4860, 3180, 7400, 3975), COLORS["red_light"], COLORS["red"], 4, 8)
    put("九项权重｜合计100分", 390, 3260, 128, COLORS["blue"], True, role="body", tag="权重标题")
    for index, (name, weight) in enumerate(WEIGHTS):
        column = index % 3
        row = index // 3
        put(
            f"{name} {weight}",
            420 + column * 1410,
            3450 + row * 165,
            128,
            COLORS["ink"],
            True,
            role="body",
            maximum_width=1320,
            tag=f"权重{index}",
        )
    put("两道一票否决硬门槛", 4980, 3260, 128, COLORS["red"], True, role="body", tag="硬门槛标题")
    put("1｜精确3板、2板、首板各至少1只", 5000, 3480, 128, COLORS["ink"], True, role="body", maximum_width=2250, tag="硬门槛1")
    put("2｜本地通达信完整成分股", 5000, 3700, 128, COLORS["ink"], True, role="body", maximum_width=2250, tag="硬门槛2上")
    put("必须严格大于100只", 5270, 3850, 128, COLORS["red"], True, role="body", maximum_width=1950, tag="硬门槛2下")

    market_line = (
        f"市场环境｜涨停{int(market.get('limit_up', 0) or 0)}  跌停{int(market.get('limit_down', 0) or 0)}  "
        f"连板{int(market.get('consecutive', 0) or 0)}  最高{int(market.get('max_board', 0) or 0)}板  "
        f"封板率{float(market.get('seal_rate', 0) or 0):.1f}%  上涨{int(market.get('advancers', 0) or 0)} / 下跌{int(market.get('decliners', 0) or 0)}"
    )
    put(market_line, 300, 4020, 128, COLORS["ink"], True, role="body", maximum_width=7050, tag="市场环境")
    source_line = (
        "数据源：本地通达信、短线侠、连板网（CC BY 4.0）｜"
        f"连板网：{lianban.get('sources', {}).get('page', {}).get('url', '')}｜仅供研究，不构成投资建议"
    )
    put(source_line, 305, 4180, 96, COLORS["muted"], True, maximum_width=7050, tag="来源与声明")

    errors = layout_errors(text_runs)
    metadata = {
        "schema": "CORE_MAINLINE_POSTER_METADATA_V1",
        "status": "PASS" if not errors else "BLOCKED",
        "dimensions": [WIDTH, HEIGHT],
        "preview_dimensions": list(PREVIEW_SIZE),
        "scoring": {"path": str(scoring_path.resolve()), "sha256": sha256_file(scoring_path)},
        "lianban": {"path": str(lianban_path.resolve()), "sha256": sha256_file(lianban_path)},
        "summary": summary,
        "top_board_names": [str(item.get("name", "")) for item in boards[:5]],
        "conclusion": conclusion,
        "text_runs": text_runs,
        "missing_glyphs": [],
        "layout_errors": errors,
    }
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        raise RuntimeError("海报文字布局校验失败：" + ",".join(errors[:10]))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", compress_level=6)
    preview.parent.mkdir(parents=True, exist_ok=True)
    resized = image.resize(PREVIEW_SIZE, Image.Resampling.LANCZOS)
    resized.save(preview, format="PNG", compress_level=6)
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="生成核心主线评分8K浅色海报")
    parser.add_argument("--scoring", required=True, type=Path)
    parser.add_argument("--lianban", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    args = parser.parse_args()
    scoring_path = args.scoring.resolve()
    lianban_path = args.lianban.resolve()
    metadata = render_poster(
        read_json(scoring_path),
        read_json(lianban_path),
        args.output.resolve(),
        args.preview.resolve(),
        args.metadata.resolve(),
        scoring_path=scoring_path,
        lianban_path=lianban_path,
    )
    print(json.dumps({
        "schema": "CORE_MAINLINE_POSTER_BUILD_V1",
        "status": "PASS",
        "output": str(args.output.resolve()),
        "preview": str(args.preview.resolve()),
        "metadata": str(args.metadata.resolve()),
        "text_run_count": len(metadata["text_runs"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
