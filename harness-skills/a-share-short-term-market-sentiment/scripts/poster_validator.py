#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
from pathlib import Path
from typing import Any

from PIL import Image

from poster_template import HEIGHT, PREVIEW_HEIGHT, PREVIEW_WIDTH, WIDTH, sha256


def _overlap(a: list[int], b: list[int]) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def validate_poster_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    poster = Path(str(bundle.get("poster") or ""))
    preview = Path(str(bundle.get("preview") or ""))
    if not poster.is_file() or not preview.is_file():
        errors.append("poster_or_preview_missing")
    else:
        with Image.open(poster) as image:
            if image.size != (WIDTH, HEIGHT):
                errors.append("poster_dimensions_invalid")
        with Image.open(preview) as image:
            if image.size != (PREVIEW_WIDTH, PREVIEW_HEIGHT):
                errors.append("preview_dimensions_invalid")

    if bundle.get("schema") == "SHORT_TERM_SENTIMENT_CUSTOM_POSTER_AUDIT_V1":
        audit = dict(bundle.get("custom_layout_audit") or {})
        if str(audit.get("status", "")).upper() not in {"PASS", "CLEAN_PASS"}:
            errors.append("custom_layout_audit_not_clean")
        if list(audit.get("errors") or []):
            errors.append("custom_layout_audit_has_errors")
        if list(audit.get("dimensions") or []) != [WIDTH, HEIGHT]:
            errors.append("custom_layout_dimensions_invalid")
        if int(audit.get("minimum_font_px") or 0) < 48:
            errors.append("custom_layout_minimum_font_below_48px")
        if int(audit.get("text_run_count") or 0) < 1:
            errors.append("custom_layout_text_runs_missing")
        binding = dict(bundle.get("data_binding") or {})
        if not binding.get("trading_date"):
            errors.append("custom_trading_date_missing")
        if not binding.get("short_stage") or not binding.get("intermediate_stage"):
            errors.append("custom_stage_binding_missing")
        for artifact in bundle.get("artifacts") or []:
            path = Path(str(artifact.get("path") or ""))
            if not path.is_file() or artifact.get("sha256") != sha256(path):
                errors.append(f"artifact_hash_mismatch:{path}")
        visual = dict(bundle.get("visual_inspection") or {})
        if visual.get("inspected") is not True or visual.get("result") != "PASS":
            errors.append("full_preview_visual_inspection_missing")
        payload = dict(bundle)
        payload["status"] = "CLEAN_PASS" if not errors else "BLOCKED"
        payload["errors"] = errors
        return payload

    if float(bundle.get("minimum_preview_font_px") or 0) < 24:
        errors.append("preview_minimum_text_below_24px")
    if float(bundle.get("minimum_core_body_preview_font_px") or 0) < 32:
        errors.append("preview_core_body_below_32px")
    if float(bundle.get("minimum_conclusion_preview_font_px") or 0) < 34:
        errors.append("preview_conclusion_below_34px")

    runs = list(bundle.get("text_runs") or [])
    for index, item in enumerate(runs):
        box = item.get("bbox") or []
        if len(box) != 4 or box[0] < 0 or box[1] < 0 or box[2] > WIDTH or box[3] > HEIGHT:
            errors.append(f"text_out_of_bounds:{index}")
    for left in range(len(runs)):
        for right in range(left + 1, len(runs)):
            if _overlap(runs[left]["bbox"], runs[right]["bbox"]):
                errors.append(f"text_overlap:{left}:{right}")

    blocks = list(bundle.get("layout_blocks") or [])
    for index, item in enumerate(blocks):
        box = item.get("bbox") or []
        if len(box) != 4 or box[0] < 0 or box[1] < 0 or box[2] > WIDTH or box[3] > HEIGHT:
            errors.append(f"block_out_of_bounds:{index}")
    for artifact in bundle.get("artifacts") or []:
        path = Path(str(artifact.get("path") or ""))
        if not path.is_file() or artifact.get("sha256") != sha256(path):
            errors.append(f"artifact_hash_mismatch:{path}")

    section_by_name = {
        str(item.get("name")): item.get("bbox")
        for item in bundle.get("sections") or []
        if isinstance(item, dict)
    }
    for index, item in enumerate(runs):
        section = section_by_name.get(str(item.get("section")))
        box = item.get("bbox") or []
        if not section or len(box) != 4:
            errors.append(f"text_section_missing:{index}")
            continue
        if not (
            box[0] >= section[0] + 48
            and box[1] >= section[1] + 48
            and box[2] <= section[2] - 48
            and box[3] <= section[3] - 48
        ):
            errors.append(f"text_section_margin_violation:{index}")

    binding = bundle.get("dynamic_binding")
    visible_texts = [str(item.get("text") or "") for item in runs]
    if not isinstance(binding, dict):
        errors.append("dynamic_binding_missing")
    else:
        short_conclusion = str(binding.get("short_conclusion") or "")
        intermediate_conclusion = str(binding.get("intermediate_conclusion") or "")
        fact_tokens = binding.get("fact_tokens")
        evidence_lines = binding.get("evidence_lines")
        if not short_conclusion or short_conclusion not in visible_texts:
            errors.append("dynamic_conclusion_not_visible")
        if not intermediate_conclusion:
            errors.append("dynamic_intermediate_conclusion_missing")
        if not isinstance(fact_tokens, list) or not fact_tokens:
            errors.append("dynamic_fact_binding_missing")
        elif any(token not in short_conclusion or token not in intermediate_conclusion for token in fact_tokens):
            errors.append("dynamic_conclusion_fact_mismatch")
        if not isinstance(evidence_lines, list) or any(str(line) not in visible_texts for line in evidence_lines):
            errors.append("dynamic_evidence_not_visible")
        short_stage = str(binding.get("short_stage") or "")
        intermediate_stage = str(binding.get("intermediate_stage") or "")
        if f"短线阶段：{short_stage}" not in visible_texts or f"中级周期：{intermediate_stage}" not in visible_texts:
            errors.append("dynamic_stage_not_visible")

    methodology = bundle.get("methodology_binding")
    expected_stages = ["启动期", "确认期", "发酵期", "加速期", "高潮期", "分歧期", "退潮期"]
    if not isinstance(methodology, dict):
        errors.append("phase_guide_binding_missing")
    else:
        phases = methodology.get("phases")
        stages = [str(item.get("stage") or "") for item in phases] if isinstance(phases, list) else []
        if stages != expected_stages:
            errors.append("phase_guide_stage_coverage_invalid")
        if methodology.get("source_title") != "三万字讲透 情绪周期":
            errors.append("phase_guide_source_binding_invalid")
        if isinstance(phases, list):
            for index, phase in enumerate(phases):
                if not isinstance(phase, dict):
                    errors.append(f"phase_guide_item_invalid:{index}")
                    continue
                for key, label in (("core", "核心"), ("strategy", "策略"), ("significance", "意义")):
                    value = str(phase.get(key) or "")
                    if not value:
                        errors.append(f"phase_guide_field_missing:{index}:{key}")
                    elif f"{label}｜{value}" not in visible_texts:
                        errors.append(f"phase_guide_text_not_visible:{index}:{key}")
        if "三万字讲透 情绪周期" not in "\n".join(visible_texts):
            errors.append("phase_guide_source_not_visible")
    visible_copy = "\n".join(visible_texts)
    for forbidden in (
        "未定", "N/A", "未提供", "固定模板结论",
        "核心延续，跟风转弱", "核心延续而跟风转弱",
        "跟风弱于核心", "呈现冰火并存", "以当次多周期证据为准",
    ):
        if forbidden in visible_copy:
            errors.append(f"forbidden_template_copy:{forbidden}")

    visual = dict(bundle.get("visual_inspection") or {})
    if visual.get("inspected") is not True or visual.get("result") != "PASS":
        errors.append("full_preview_visual_inspection_missing")

    payload = dict(bundle)
    payload["status"] = "CLEAN_PASS" if not errors else "BLOCKED"
    payload["errors"] = errors
    return payload


def write_validation(bundle: dict[str, Any], path: Path) -> dict[str, Any]:
    payload = validate_poster_bundle(bundle)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload
