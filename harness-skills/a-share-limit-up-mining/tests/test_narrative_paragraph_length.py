from __future__ import annotations

import importlib.util
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def _load_build_docx():
    script = SKILL_ROOT / "scripts" / "build_docx.py"
    spec = importlib.util.spec_from_file_location("limit_up_build_docx_narrative_test", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _visible_text(label: str, text: str) -> str:
    return f"{label}｜{text}" if label else text


def test_long_risk_narrative_is_split_without_losing_evidence() -> None:
    module = _load_build_docx()
    label = "神奇制药风险"
    text = (
        "2026-08-24《股票交易异常波动公告》；2026-08-22《关于控股股东减持计划的提示公告》；"
        "2026-08-21《股票交易风险提示公告》。这些公告分别覆盖异常波动、股东减持和经营风险，"
        "需要完整保留原始日期、标题与风险结论，不能为了通过版式检查删掉任何一项。"
        "次日只有在风险公告不再增加、最近两天走势和资金重新转强时才重新观察；否则继续排除。"
        "同时还要持续核对交易所问询、实际控制人变化、解禁安排和诉讼进展，任何新增事项都必须原样进入风险结论。"
    )

    paragraphs = module.split_analysis_paragraphs(text, label, max_chars=220)

    assert len(paragraphs) >= 2
    assert all(len(_visible_text(part_label, part_text)) <= 220 for part_label, part_text in paragraphs)
    assert paragraphs[0][0] == label
    assert all(part_label == "" for part_label, _ in paragraphs[1:])
    assert "".join(part_text for _, part_text in paragraphs) == text


def test_short_narrative_stays_in_one_paragraph() -> None:
    module = _load_build_docx()

    paragraphs = module.split_analysis_paragraphs("最近五个交易日未发现硬风险。", "风险", max_chars=220)

    assert paragraphs == [("风险", "最近五个交易日未发现硬风险。")]
