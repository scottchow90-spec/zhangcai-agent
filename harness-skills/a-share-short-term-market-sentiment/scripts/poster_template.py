#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 7680, 4320
PREVIEW_WIDTH, PREVIEW_HEIGHT = 1920, 1080
SCALE = WIDTH // PREVIEW_WIDTH
POSTER_NAME = "short-term-market-sentiment-8k.png"
PREVIEW_NAME = "short-term-market-sentiment-preview-1920x1080.png"
AUDIT_NAME = "poster_validation.json"
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
REQUIRED_POSTER_MARKET = (
    "index_change_pct", "advancers", "decliners", "total_amount_billion",
    "amount_change_pct", "limit_up", "limit_down", "consecutive",
    "max_board", "seal_rate", "broken_board", "topic_count_ge3",
)
REQUIRED_POSTER_PREVIOUS = ("limit_up", "limit_down", "consecutive", "seal_rate", "broken_board")
FORBIDDEN_TEMPLATE_CONCLUSIONS = (
    "核心延续，跟风转弱",
    "核心延续而跟风转弱",
    "跟风弱于核心",
    "呈现冰火并存",
    "以当次多周期证据为准",
)
PHASE_GUIDE = (
    {
        "stage": "启动期",
        "core": "龙头试盘、首批涨停\n扩散尚弱",
        "strategy": "小仓观察，等换手\n周期共振；不追高",
        "significance": "识别新周期候选\n赔率拐点",
    },
    {
        "stage": "确认期",
        "core": "自然接力转好，跟风\n出现，梯队初成",
        "strategy": "聚焦换手核心，去弱\n留强；设失败条件",
        "significance": "验证启动并非脉冲\n提高确定性",
    },
    {
        "stage": "发酵期",
        "core": "跟风持续、题材扩散\n赚钱效应增强",
        "strategy": "顺主线分批参与核心\n回避边缘跟风",
        "significance": "主升盈利窗口\n重点检验持续性",
    },
    {
        "stage": "加速期",
        "core": "龙头与一二线缩量\n接力拥挤",
        "strategy": "管理前排先手\n加速不追，等换手",
        "significance": "收益与脆弱性同升\n准备迎接分歧",
    },
    {
        "stage": "高潮期",
        "core": "全面扩散，秒板与一字增多\n情绪极致",
        "strategy": "有先手逐步兑现；无先手\n等分歧确认",
        "significance": "正反馈接近极值\n风险收益开始转差",
    },
    {
        "stage": "分歧期",
        "core": "龙头断板或跟风掉队\n炸板与分化增加",
        "strategy": "降仓去弱留强\n观察核心承接与修复",
        "significance": "检验主线韧性\n决定修复还是退潮",
    },
    {
        "stage": "退潮期",
        "core": "跌停、炸板和前排补跌扩散\n高度收缩",
        "strategy": "防守并压低仓位\n等止跌与新题材共振",
        "significance": "保护本金\n寻找冰点修复与新起点",
    },
)
PHASE_COLORS = (
    ("#EFF6FF", "#1D4ED8"),
    ("#ECFEFF", "#0E7490"),
    ("#ECFDF5", "#047857"),
    ("#FFFBEB", "#B45309"),
    ("#FFF1F2", "#BE123C"),
    ("#FFF7ED", "#C2410C"),
    ("#F3F4F6", "#374151"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold and FONT_BOLD.is_file() else FONT_REGULAR
    return ImageFont.truetype(str(path), size=size)


def _format_metric(value: Any, precision: int = 0) -> str:
    return f"{float(value):.{precision}f}" if precision else str(int(value))


def _transition_text(
    label: str,
    previous: Any,
    current: Any,
    unit: str,
    *,
    precision: int = 0,
) -> str:
    previous_number = float(previous)
    current_number = float(current)
    direction = "升至" if current_number > previous_number else "降至" if current_number < previous_number else "持平于"
    return (
        f"{label}由{_format_metric(previous, precision)}{unit}{direction}"
        f"{_format_metric(current, precision)}{unit}"
    )


def _require(mapping: dict[str, Any], key: str, error_prefix: str) -> Any:
    if key not in mapping or mapping[key] is None or mapping[key] == "":
        raise ValueError(f"{error_prefix}:{key}")
    return mapping[key]


def render_poster(
    result: dict[str, Any],
    snapshot: dict[str, Any],
    run_dir: Path,
    external_poster: Path | None = None,
    *,
    visual_inspected: bool = False,
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (WIDTH, HEIGHT), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    text_runs: list[dict[str, Any]] = []
    phase_boxes = [
        [160, 1290, 1940, 2580],
        [2020, 1290, 3800, 2580],
        [3880, 1290, 5660, 2580],
        [5740, 1290, 7520, 2580],
        [160, 2660, 2560, 4000],
        [2640, 2660, 5040, 4000],
        [5120, 2660, 7520, 4000],
    ]
    sections = [
        {"name": "header", "bbox": [160, 80, 7520, 470]},
        {"name": "current", "bbox": [160, 480, 7520, 1260]},
        *[
            {"name": f"phase_{index + 1}", "bbox": box}
            for index, box in enumerate(phase_boxes)
        ],
        {"name": "footer", "bbox": [160, 4000, 7520, 4320]},
    ]

    def text(
        section: str,
        xy: tuple[int, int],
        value: str,
        size: int,
        fill: str = "#111827",
        *,
        bold: bool = False,
        role: str = "visible_text",
        anchor: str = "la",
    ) -> None:
        font = _font(size, bold)
        draw.text(xy, value, font=font, fill=fill, anchor=anchor)
        text_runs.append({
            "text": value,
            "font_px": size,
            "role": role,
            "section": section,
            "bbox": list(draw.textbbox(xy, value, font=font, anchor=anchor)),
        })

    def wrapped_text(
        section: str,
        xy: tuple[int, int],
        value: str,
        size: int,
        fill: str,
        *,
        max_width: int,
        max_lines: int,
        spacing: int = 16,
        bold: bool = False,
        role: str = "visible_text",
    ) -> None:
        font = _font(size, bold)
        lines: list[str] = []
        closing_punctuation = "，。；：、！？）》】％"
        for paragraph in value.split("\n"):
            current = ""
            for character in paragraph:
                candidate = current + character
                if current and draw.textlength(candidate, font=font) > max_width:
                    if character in closing_punctuation and len(current) > 2:
                        lines.append(current[:-2])
                        current = current[-2:] + character
                    else:
                        lines.append(current)
                        current = character
                else:
                    current = candidate
            if current:
                lines.append(current)
        if len(lines) > max_lines:
            raise ValueError(f"dynamic_conclusion_too_long:{len(lines)}")
        rendered = "\n".join(lines)
        draw.multiline_text(xy, rendered, font=font, fill=fill, spacing=spacing)
        text_runs.append({
            "text": value,
            "rendered_text": rendered,
            "font_px": size,
            "role": role,
            "section": section,
            "bbox": list(draw.multiline_textbbox(xy, rendered, font=font, spacing=spacing)),
        })

    def rule(y: int, color: str = "#D1D5DB", width: int = 4) -> None:
        draw.line((160, y, 7520, y), fill=color, width=width)

    market_raw = snapshot.get("market")
    if not isinstance(market_raw, dict):
        raise ValueError("missing_poster_market")
    market = dict(market_raw)
    missing_market = [key for key in REQUIRED_POSTER_MARKET if market.get(key) is None]
    if missing_market:
        raise ValueError("missing_poster_market_metric:" + ",".join(missing_market))
    comparisons = snapshot.get("comparisons")
    if not isinstance(comparisons, dict) or not isinstance(comparisons.get("previous_trading_day"), dict):
        raise ValueError("missing_poster_previous_metrics")
    previous = dict(comparisons["previous_trading_day"])
    missing_previous = [key for key in REQUIRED_POSTER_PREVIOUS if previous.get(key) is None]
    if missing_previous:
        raise ValueError("missing_poster_previous_metric:" + ",".join(missing_previous))
    cross_validation_raw = snapshot.get("cross_validation")
    if not isinstance(cross_validation_raw, dict) or cross_validation_raw.get("limit_up_difference") is None:
        raise ValueError("missing_poster_cross_validation:limit_up_difference")
    cross_validation = dict(cross_validation_raw)
    topics_raw = snapshot.get("topics")
    if not isinstance(topics_raw, list):
        raise ValueError("missing_poster_topics")
    if any(not isinstance(topic, dict) or topic.get("name") is None or topic.get("count") is None for topic in topics_raw):
        raise ValueError("missing_poster_topic_metric")
    topics = list(topics_raw)
    result_date = str(result.get("trading_date") or "")
    snapshot_date = str(snapshot.get("trading_date") or "")
    if not result_date or result_date != snapshot_date:
        raise ValueError("poster_trading_date_mismatch")
    date = result_date
    short_raw = result.get("short_term_stage_conclusion")
    intermediate_raw = result.get("single_stage_conclusion")
    if not isinstance(short_raw, dict) or not isinstance(intermediate_raw, dict):
        raise ValueError("missing_dynamic_conclusion")
    short = dict(short_raw)
    intermediate = dict(intermediate_raw)
    for field in ("stage", "confidence", "conclusion", "conflict_statement"):
        if short.get(field) in (None, ""):
            raise ValueError("missing_dynamic_conclusion")
    for field in ("stage", "confidence", "conclusion"):
        if intermediate.get(field) in (None, ""):
            raise ValueError("missing_dynamic_conclusion")
    result_sources = result.get("sources")
    tongdaxin_source = result_sources.get("tongdaxin") if isinstance(result_sources, dict) else None
    if not isinstance(tongdaxin_source, dict) or tongdaxin_source.get("coverage") is None:
        raise ValueError("missing_poster_source_coverage")
    coverage = int(tongdaxin_source["coverage"])
    risk_items = result.get("risk_boundary")
    if not isinstance(risk_items, list) or not risk_items or not str(risk_items[0]).strip():
        raise ValueError("missing_dynamic_risk_boundary")
    snapshot_sources = snapshot.get("sources")
    if not isinstance(snapshot_sources, dict):
        raise ValueError("missing_poster_sources")
    duanxian_source = snapshot_sources.get("duanxianxia")
    lianban_source = snapshot_sources.get("lianban")
    datasets = duanxian_source.get("datasets") if isinstance(duanxian_source, dict) else None
    if not isinstance(datasets, list) or len(datasets) != 4 or not isinstance(lianban_source, dict):
        raise ValueError("missing_poster_source_evidence")

    fact_tokens = (
        _transition_text("涨停", previous["limit_up"], market["limit_up"], "家"),
        _transition_text("封板率", previous["seal_rate"], market["seal_rate"], "%", precision=1),
        _transition_text("炸板", previous["broken_board"], market["broken_board"], "家"),
        _transition_text("跌停", previous["limit_down"], market["limit_down"], "家"),
        _transition_text("连板", previous["consecutive"], market["consecutive"], "只"),
    )
    for conclusion in (str(short["conclusion"]), str(intermediate["conclusion"])):
        if any(fragment in conclusion for fragment in FORBIDDEN_TEMPLATE_CONCLUSIONS):
            raise ValueError("forbidden_template_conclusion")
        if any(token not in conclusion for token in fact_tokens):
            raise ValueError("dynamic_conclusion_snapshot_mismatch")

    prior_limit_up = previous["limit_up"]
    prior_limit_down = previous["limit_down"]
    prior_seal_rate = previous["seal_rate"]
    prior_broken = previous["broken_board"]
    prior_consecutive_for_evidence = previous["consecutive"]
    evidence_line_one = (
        f"涨停{int(prior_limit_up)}→{int(market['limit_up'])}｜"
        f"封板{float(prior_seal_rate):.1f}%→{float(market['seal_rate']):.1f}%｜"
        f"炸板{int(prior_broken)}→{int(market['broken_board'])}｜"
        f"跌停{int(prior_limit_down)}→{int(market['limit_down'])}"
    )
    evidence_line_two = (
        f"连板{int(prior_consecutive_for_evidence)}→{int(market['consecutive'])}｜"
        f"上涨/下跌{int(market['advancers'])}/{int(market['decliners'])}｜"
        f"成交额环比{float(market['amount_change_pct']):+.2f}%"
    )
    short_conclusion = str(short["conclusion"])
    difference_text = str(cross_validation["limit_up_difference"])
    risk_text = str(risk_items[0])
    conflict_text = str(short["conflict_statement"])

    text("header", (220, 90), "短线情绪周期全景作战图", 180, bold=True, role="conclusion")
    text("header", (7460, 120), date, 112, bold=True, anchor="ra")
    text("header", (220, 290), "基于《三万字讲透 情绪周期》｜先分周期观察，再判断主导阶段", 96, "#4B5563")
    rule(475, "#B42318", 8)

    text("current", (220, 506), "当下定位", 100, "#6B7280", bold=True)
    text("current", (220, 620), f"短线阶段：{short['stage']}", 164, "#B42318", bold=True, role="conclusion")
    text("current", (2760, 620), f"中级周期：{intermediate['stage']}", 152, bold=True, role="conclusion")
    text("current", (7460, 635), f"置信度：{short['confidence']}", 136, bold=True, role="conclusion", anchor="ra")
    text("current", (220, 805), evidence_line_one, 128, bold=True, role="core_body")
    text("current", (220, 945), evidence_line_two, 128, "#B42318", bold=True, role="core_body")
    wrapped_text(
        "current",
        (220, 1095),
        short_conclusion,
        96,
        "#374151",
        max_width=7200,
        max_lines=2,
        spacing=10,
    )
    rule(1275)

    for index, (phase, box, colors) in enumerate(zip(PHASE_GUIDE, phase_boxes, PHASE_COLORS)):
        section = f"phase_{index + 1}"
        left, top, right, bottom = box
        fill_color, accent_color = colors
        border_color = "#B42318" if phase["stage"] == str(short["stage"]) else "#D1D5DB"
        border_width = 12 if phase["stage"] == str(short["stage"]) else 4
        draw.rounded_rectangle(box, radius=32, fill=fill_color, outline=border_color, width=border_width)
        current_marker = "  当前" if phase["stage"] == str(short["stage"]) else ""
        text(
            section,
            (left + 80, top + 52),
            f"{index + 1:02d}  {phase['stage']}{current_marker}",
            164,
            accent_color,
            bold=True,
            role="conclusion",
        )
        max_width = right - left - 160
        wrapped_text(
            section,
            (left + 80, top + 280),
            f"核心｜{phase['core']}",
            128,
            "#111827",
            max_width=max_width,
            max_lines=2,
            spacing=14,
            bold=True,
            role="core_body",
        )
        wrapped_text(
            section,
            (left + 80, top + 610),
            f"策略｜{phase['strategy']}",
            128,
            "#111827",
            max_width=max_width,
            max_lines=2,
            spacing=14,
            role="core_body",
        )
        wrapped_text(
            section,
            (left + 80, top + 920),
            f"意义｜{phase['significance']}",
            128,
            "#111827",
            max_width=max_width,
            max_lines=2,
            spacing=14,
            role="core_body",
        )

    source_line = (
        f"来源核验：PDF 126页｜通达信覆盖{coverage}只｜短线侠{len(datasets)}组数据｜"
        f"连板网同日（CC BY 4.0）｜涨停交叉差值{difference_text}"
    )
    risk_line = f"风险：{risk_text}｜冲突：{conflict_text}｜市场结构研判，不构成个股推荐或收益保证"
    text("footer", (220, 4038), source_line, 96, "#4B5563")
    text("footer", (220, 4145), risk_line, 96, "#6B4B16")

    poster = run_dir / POSTER_NAME
    preview = run_dir / PREVIEW_NAME
    image.save(poster, format="PNG", compress_level=7)
    image.resize((PREVIEW_WIDTH, PREVIEW_HEIGHT), Image.Resampling.LANCZOS).save(preview, format="PNG", compress_level=7)

    external_preview: Path | None = None
    if external_poster is not None:
        external_poster = external_poster.resolve()
        external_poster.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(poster, external_poster)
        external_preview = external_poster.with_name(external_poster.stem + "-preview-1920x1080.png")
        shutil.copy2(preview, external_preview)

    artifacts = [
        {"path": str(poster), "sha256": sha256(poster), "size": poster.stat().st_size},
        {"path": str(preview), "sha256": sha256(preview), "size": preview.stat().st_size},
    ]
    for path in (external_poster, external_preview):
        if path is not None:
            artifacts.append({"path": str(path), "sha256": sha256(path), "size": path.stat().st_size})

    return {
        "schema": "SHORT_TERM_SENTIMENT_POSTER_AUDIT_V1",
        "status": "CLEAN_PASS",
        "errors": [],
        "poster": str(poster),
        "preview": str(preview),
        "external_poster": str(external_poster) if external_poster else None,
        "external_preview": str(external_preview) if external_preview else None,
        "poster_dimensions": [WIDTH, HEIGHT],
        "preview_dimensions": [PREVIEW_WIDTH, PREVIEW_HEIGHT],
        "minimum_source_font_px": min(item["font_px"] for item in text_runs),
        "minimum_preview_font_px": min(item["font_px"] for item in text_runs) / SCALE,
        "minimum_core_body_preview_font_px": min(item["font_px"] for item in text_runs if item["role"] == "core_body") / SCALE,
        "minimum_conclusion_preview_font_px": min(item["font_px"] for item in text_runs if item["role"] == "conclusion") / SCALE,
        "text_runs": text_runs,
        "sections": sections,
        "layout_blocks": sections,
        "dynamic_binding": {
            "trading_date": date,
            "short_stage": str(short["stage"]),
            "intermediate_stage": str(intermediate["stage"]),
            "short_conclusion": short_conclusion,
            "intermediate_conclusion": str(intermediate["conclusion"]),
            "fact_tokens": list(fact_tokens),
            "evidence_lines": [evidence_line_one, evidence_line_two],
        },
        "methodology_binding": {
            "source_title": "三万字讲透 情绪周期",
            "source_pages": 126,
            "source_sha256": "8e3eaf9ab79b4d6c37b21810f68656dd1f6533794fdd23c54ce58ee6b505970e",
            "phases": [dict(item) for item in PHASE_GUIDE],
        },
        "artifacts": artifacts,
        "visual_inspection": {
            "inspected": visual_inspected,
            "surface": "complete_1920x1080_fit_preview",
            "result": "PASS" if visual_inspected else "PENDING",
        },
    }


def render_audited_custom_poster(
    result: dict[str, Any],
    snapshot: dict[str, Any],
    run_dir: Path,
    source_poster: Path,
    source_audit: Path,
    *,
    visual_inspected: bool = False,
) -> dict[str, Any]:
    """Bring a separately composed poster through the canonical validation path."""
    run_dir = run_dir.resolve()
    source_poster = source_poster.resolve()
    source_audit = source_audit.resolve()
    audit = json.loads(source_audit.read_text(encoding="utf-8"))

    errors: list[str] = []
    if str(audit.get("status", "")).upper() not in {"PASS", "CLEAN_PASS"}:
        errors.append("custom_audit_not_clean")
    if list(audit.get("errors") or []):
        errors.append("custom_audit_has_errors")
    if list(audit.get("dimensions") or []) != [WIDTH, HEIGHT]:
        errors.append("custom_audit_dimensions_invalid")
    if int(audit.get("minimum_font_px") or 0) < 48:
        errors.append("custom_audit_minimum_font_below_48px")
    if int(audit.get("text_run_count") or 0) < 1:
        errors.append("custom_audit_text_runs_missing")
    if not source_poster.is_file():
        errors.append("custom_poster_missing")
    elif str(audit.get("output_sha256", "")).casefold() != sha256(source_poster):
        errors.append("custom_poster_hash_mismatch")

    audit_snapshot = Path(str(audit.get("source_snapshot") or ""))
    audit_result = Path(str(audit.get("source_result") or ""))
    try:
        if json.loads(audit_snapshot.read_text(encoding="utf-8")) != snapshot:
            errors.append("custom_snapshot_binding_mismatch")
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append("custom_snapshot_binding_unreadable")
    try:
        audit_result_payload = json.loads(audit_result.read_text(encoding="utf-8"))
        audit_result_payload.pop("artifacts", None)
        current_result_payload = dict(result)
        current_result_payload.pop("artifacts", None)
        if audit_result_payload != current_result_payload:
            errors.append("custom_result_binding_mismatch")
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append("custom_result_binding_unreadable")
    if errors:
        raise ValueError(";".join(errors))

    poster = run_dir / POSTER_NAME
    preview = run_dir / PREVIEW_NAME
    shutil.copy2(source_poster, poster)
    with Image.open(poster) as image:
        if image.size != (WIDTH, HEIGHT):
            raise ValueError("custom_poster_dimensions_invalid")
        image.resize((PREVIEW_WIDTH, PREVIEW_HEIGHT), Image.Resampling.LANCZOS).save(
            preview,
            format="PNG",
            compress_level=7,
        )

    artifacts = [
        {"path": str(poster), "sha256": sha256(poster), "size": poster.stat().st_size},
        {"path": str(preview), "sha256": sha256(preview), "size": preview.stat().st_size},
        {"path": str(source_poster), "sha256": sha256(source_poster), "size": source_poster.stat().st_size},
        {"path": str(source_audit), "sha256": sha256(source_audit), "size": source_audit.stat().st_size},
    ]
    return {
        "schema": "SHORT_TERM_SENTIMENT_CUSTOM_POSTER_AUDIT_V1",
        "status": "CLEAN_PASS",
        "errors": [],
        "poster": str(poster),
        "preview": str(preview),
        "source_poster": str(source_poster),
        "source_audit": str(source_audit),
        "poster_dimensions": [WIDTH, HEIGHT],
        "preview_dimensions": [PREVIEW_WIDTH, PREVIEW_HEIGHT],
        "custom_layout_audit": audit,
        "data_binding": {
            "trading_date": str(snapshot.get("trading_date") or ""),
            "short_stage": str(result.get("short_term_stage_conclusion", {}).get("stage") or ""),
            "intermediate_stage": str(result.get("single_stage_conclusion", {}).get("stage") or ""),
        },
        "artifacts": artifacts,
        "visual_inspection": {
            "inspected": visual_inspected,
            "surface": "complete_1920x1080_fit_preview",
            "result": "PASS" if visual_inspected else "PENDING",
        },
    }


if __name__ == "__main__":
    raise SystemExit("Use the canonical sentiment business adapter")
