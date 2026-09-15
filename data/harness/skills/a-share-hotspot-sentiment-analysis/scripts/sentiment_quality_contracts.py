#!/usr/bin/env python3
"""Shared acquisition and evidence-quality contracts for A-share sentiment."""
from __future__ import annotations

import re
from typing import Any, Iterable


MANDATORY_CAPTURE_STEMS = (
    "tgb",
    "xueqiu",
    "weibo",
    "zhihu",
    "guba",
    "jiuyangongshe",
    "cls",
    "jin10",
)
REQUIRED_CAPTURE_FILES = (
    "primary.json",
    *(f"{stem}.json" for stem in MANDATORY_CAPTURE_STEMS),
    "business_society.json",
)

GENERIC_A_SHARE_MAPPINGS = {
    "直接涉及a股个股、板块、指数、资金或市场情绪",
    "直接涉及a股市场情绪、板块或资金",
    "直接映射a股产业链",
    "a股相关",
    "a股映射",
}

A_SHARE_SIGNAL_TERMS = (
    "A股", "沪指", "深证", "创业板", "科创板", "北交所", "上市公司",
    "个股", "板块", "产业链", "概念", "涨停", "跌停",
    "连板", "晋级", "成交额", "主力资金", "融资", "龙虎榜", "股民",
    "市值", "IPO", "上证指数", "深证成指",
)

UI_RESIDUE_TERMS = (
    "移动版", "网页版", "首页", "打开APP", "下载APP", "登录后查看",
    "点击展开", "阅读全文", "返回顶部", "加载更多", "导航", "分享按钮",
)

ZERO_HEAT_PATTERNS = (
    r"重要度\s*[:：]?\s*0(?:\D|$)",
    r"热度\s*[:：]?\s*0(?:\D|$)",
    r"点赞\s*0(?:\D|$).*评论\s*0(?:\D|$).*转发\s*0(?:\D|$)",
)


def _clean(value: Any, limit: int = 2000) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _normalized(value: Any) -> str:
    return re.sub(r"[\W_]+", "", _clean(value).casefold())


def required_capture_files() -> tuple[str, ...]:
    return REQUIRED_CAPTURE_FILES


def ui_residue_hits(text: Any) -> list[str]:
    value = _clean(text, 6000)
    return [term for term in UI_RESIDUE_TERMS if term in value]


def validate_heat_evidence(source: str, heat_evidence: Any, rank: Any = None) -> dict[str, Any]:
    value = _clean(heat_evidence, 240)
    reasons: list[str] = []
    if not value:
        reasons.append("heat_evidence_missing")
    if any(re.search(pattern, value, flags=re.I) for pattern in ZERO_HEAT_PATTERNS):
        reasons.append("heat_evidence_invalid")
    has_rank = str(rank).isdigit() and int(rank) > 0
    has_numeric_heat = bool(re.search(r"\d", value))
    has_named_high_heat = any(
        marker in value
        for marker in ("高热", "热榜", "热股", "电报", "关注", "浏览", "讨论", "点赞", "评论", "转发")
    )
    if value and not (has_rank or has_numeric_heat or has_named_high_heat):
        reasons.append("heat_evidence_unverifiable")
    return {
        "ok": not reasons,
        "source": _clean(source, 80),
        "value": value,
        "rank": rank,
        "reasons": list(dict.fromkeys(reasons)),
    }


def validate_a_share_mapping(event: Any, mapping: Any) -> dict[str, Any]:
    event_text = _clean(event, 6000)
    mapping_text = _clean(mapping, 800)
    reasons: list[str] = []
    if not mapping_text:
        reasons.append("a_share_mapping_missing")
    event_signal_terms = [term for term in A_SHARE_SIGNAL_TERMS if term.casefold() in event_text.casefold()]
    mapping_tokens = [
        token
        for token in re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,16}", mapping_text)
        if _normalized(token) not in GENERIC_A_SHARE_MAPPINGS
        and token not in {"直接涉及", "相关板块", "市场情绪", "风险偏好", "资金反馈"}
    ]
    grounded_tokens = [token for token in mapping_tokens if token.casefold() in event_text.casefold()]
    mapping_is_generic = _normalized(mapping_text.rstrip("。；;")) in {
        _normalized(value) for value in GENERIC_A_SHARE_MAPPINGS
    }
    if mapping_text and not event_signal_terms and not grounded_tokens:
        reasons.append("a_share_mapping_not_semantically_grounded")
    if mapping_is_generic and not event_signal_terms:
        reasons.append("a_share_mapping_not_semantically_grounded")
    return {
        "ok": not reasons,
        "mapping": mapping_text,
        "event_signal_terms": event_signal_terms,
        "grounded_mapping_terms": grounded_tokens,
        "mapping_is_generic": mapping_is_generic,
        "reasons": list(dict.fromkeys(reasons)),
    }


def validate_sentiment_record(
    *,
    source: str,
    event: Any,
    heat_evidence: Any,
    a_share_mapping: Any,
    rank: Any = None,
) -> dict[str, Any]:
    heat = validate_heat_evidence(source, heat_evidence, rank)
    mapping = validate_a_share_mapping(event, a_share_mapping)
    residue = ui_residue_hits(event)
    reasons = [*heat["reasons"], *mapping["reasons"]]
    if residue:
        reasons.append("webpage_ui_residue")
    return {
        "ok": not reasons,
        "source": _clean(source, 80),
        "heat": heat,
        "mapping": mapping,
        "residue_hits": residue,
        "reasons": list(dict.fromkeys(reasons)),
        "relevance_score": (
            min(99, 70 + 4 * len(mapping["event_signal_terms"]) + 6 * len(mapping["grounded_mapping_terms"]))
            if not reasons
            else 0
        ),
    }


def validate_capture_accounting(
    *,
    raw_count: int,
    clean_count: int,
    clean_rows: Iterable[dict[str, Any]],
    supplemented_count: int = 0,
) -> dict[str, Any]:
    rows = list(clean_rows)
    reasons: list[str] = []
    if raw_count < 0 or clean_count < 0 or supplemented_count < 0:
        reasons.append("negative_capture_count")
    if clean_count != len(rows):
        reasons.append("clean_count_mismatch")
    if clean_count > raw_count + supplemented_count:
        reasons.append("clean_count_gt_raw_count")
    identities = []
    for row in rows:
        href = _clean(row.get("href") or row.get("url"), 1000)
        title = _normalized(row.get("title"))[:180]
        identities.append((href, title))
    if len(identities) != len(set(identities)):
        reasons.append("duplicate_clean_rows")
    return {
        "ok": not reasons,
        "raw_count": raw_count,
        "clean_count": clean_count,
        "supplemented_count": supplemented_count,
        "reasons": list(dict.fromkeys(reasons)),
    }
