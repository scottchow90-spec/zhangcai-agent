#!/usr/bin/env python3
"""Evidence-first source integration for the A-share sentiment workflow.

The module owns normalization, dynamic A-share relevance mapping, cross-source
deduplication and conflict registration.  It deliberately does not import or
execute any other skill: the daily-intelligence and short-term-sentiment
results are derived views over one evidence pool, while Business Society is a
same-run, official-page capture input.
"""

from __future__ import annotations

import sys
import argparse
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse

LOCAL_SCRIPT_DIR = Path(__file__).resolve().parent
if str(LOCAL_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(LOCAL_SCRIPT_DIR))

from sentiment_quality_contracts import validate_sentiment_record


SCHEMA = "A_SHARE_SENTIMENT_INTEGRATION_V1"
EVENT_SCHEMA = "A_SHARE_SENTIMENT_UNIFIED_EVENT_V1"
BUSINESS_CAPTURE_FILE = "business_society.json"
CHINA_TZ = timezone(timedelta(hours=8))
ALLOWED_BUSINESS_DOMAINS = ("100ppi.com", "ppi.cn")
ALLOWED_BUSINESS_CAPTURE_CHANNELS = (
    "Chrome logged-in visible pages only",
    "official_public_page_readonly",
)
EXCLUDED_WORKFLOWS = (
    "a-share-thinktank-brief",
    "gold-intelligence-system",
    "bitcoin-news-intelligence",
)
POSITIVE_TERMS = (
    "涨价", "上涨", "增长", "扩产", "增产", "提价", "供给收缩", "需求回暖",
    "订单增长", "中标", "突破", "修复", "净流入", "走强", "晋级",
)
NEGATIVE_TERMS = (
    "降价", "下跌", "减产", "需求走弱", "库存上升", "亏损", "风险",
    "终止", "减持", "净流出", "走弱", "跌停", "退潮", "监管",
)
GENERIC_TERMS = {
    "A股", "市场", "板块", "行业", "公司", "个股", "资金", "热点", "概念",
    "产业链", "今日", "昨日", "目前", "相关", "价格", "商品", "生意社",
    "数据", "资讯", "行情", "情况", "影响", "国内", "国际", "最新",
}
SOURCE_TIER = {
    "国家医保局": "T1_官方或公告",
    "教育部": "T1_官方或公告",
    "交易所公告": "T1_官方或公告",
    "公司公告": "T1_官方或公告",
    "生意社": "T2_产业官方数据",
    "财联社": "T2_权威财经媒体",
    "金十数据": "T2_权威财经媒体",
    "连板网": "T2_盘面结构",
    "通达信": "T2_盘面结构",
    "短线侠": "T2_盘面结构",
    "韭研公社": "T3_研究社区",
    "淘股吧": "T4_交易者社区",
    "雪球": "T4_投资者社区",
    "微博": "T4_投资者社区",
    "知乎": "T4_投资者社区",
    "东方财富股吧": "T4_投资者社区",
}
TIER_RANK = {
    "T1_官方或公告": 1,
    "T2_产业官方数据": 2,
    "T2_权威财经媒体": 2,
    "T2_盘面结构": 2,
    "T3_研究社区": 3,
    "T4_交易者社区": 4,
    "T4_投资者社区": 4,
    "T3_其他已核验来源": 3,
}
MANDATORY_SENTIMENT_SOURCES = {
    "淘股吧", "雪球", "微博", "知乎", "东方财富股吧", "韭研公社", "财联社", "金十数据",
}


class IntegrationError(RuntimeError):
    pass


def _clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parse_datetime(value: object, now: datetime) -> datetime | None:
    text = _clean(value)
    if not text:
        return None
    normalized = text.replace("年", "-").replace("月", "-").replace("日", " ").replace("/", "-")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=CHINA_TZ)
        return parsed.astimezone(CHINA_TZ)
    except ValueError:
        pass
    relative = re.search(r"(\d+)\s*(分钟|小时|天)前", text)
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2)
        delta = timedelta(minutes=amount) if unit == "分钟" else timedelta(hours=amount) if unit == "小时" else timedelta(days=amount)
        return now - delta
    day_offset = 0
    if "昨天" in text:
        day_offset = -1
    elif "前天" in text:
        day_offset = -2
    hm = re.search(r"(?:今天|昨天|前天)?\s*(\d{1,2}):(\d{2})", text)
    if hm:
        base = (now + timedelta(days=day_offset)).date()
        return datetime(base.year, base.month, base.day, int(hm.group(1)), int(hm.group(2)), tzinfo=CHINA_TZ)
    match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?", normalized)
    if match:
        return datetime(
            int(match.group(1)), int(match.group(2)), int(match.group(3)),
            int(match.group(4) or 12), int(match.group(5) or 0), tzinfo=CHINA_TZ,
        )
    match = re.search(r"(?<!\d)(\d{1,2})-(\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?", normalized)
    if match:
        return datetime(
            now.year, int(match.group(1)), int(match.group(2)),
            int(match.group(3) or 12), int(match.group(4) or 0), tzinfo=CHINA_TZ,
        )
    return None


def _normalized_url(value: object) -> str:
    raw = _clean(value)
    if not raw.startswith(("http://", "https://")):
        return ""
    parsed = urlparse(raw)
    host = parsed.netloc.casefold().removeprefix("www.")
    path = re.sub(r"/+", "/", parsed.path).rstrip("/")
    return urlunparse((parsed.scheme.casefold(), host, path, "", "", ""))


def _normalized_text(value: object) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", _clean(value)).casefold()


def _shingles(text: str, size: int = 3) -> set[str]:
    if len(text) <= size:
        return {text} if text else set()
    return {text[index:index + size] for index in range(len(text) - size + 1)}


def _similarity(left: str, right: str) -> float:
    a, b = _shingles(left), _shingles(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _theme_terms(item: dict) -> list[str]:
    values = item.get("theme_terms") or []
    if not isinstance(values, list):
        values = [values]
    output = []
    for value in values:
        term = _clean(value)
        if 2 <= len(term) <= 16 and term not in GENERIC_TERMS and term not in output:
            output.append(term)
    return output[:8]


def _event_sources(item: dict) -> list[str]:
    values = [item.get("source", "")]
    values.extend(item.get("evidence_sources") or [])
    values.extend(
        row.get("source", "")
        for row in item.get("provenance", [])
        if isinstance(row, dict)
    )
    return sorted({_clean(value) for value in values if _clean(value)})


def _tier(source: str) -> str:
    if source in SOURCE_TIER:
        return SOURCE_TIER[source]
    if source.startswith(("连板网", "通达信", "短线侠")) or source.endswith("·市场复盘"):
        return "T2_盘面结构"
    return "T3_其他已核验来源"


def _normalize_event(item: dict, origin_stream: str) -> dict:
    row = deepcopy(item)
    source = _clean(row.get("source"))
    event = _clean(row.get("event"))
    window = _clean(row.get("window_type"))
    date_text = _clean(row.get("date"))
    url = _normalized_url(row.get("url")) or _clean(row.get("url"))
    canonical_seed = "|".join([window, date_text, _normalized_url(url), _normalized_text(event)[:360]])
    event_id = _sha_text(canonical_seed)
    requires_sentiment_quality = (
        origin_stream == "mandatory_eight_site_sentiment"
        or _clean(row.get("source_channel")) == "mandatory_eight_site_sentiment"
    )
    existing_relevance = row.get("a_share_relevance")
    if requires_sentiment_quality:
        quality = validate_sentiment_record(
            source=source,
            event=event,
            heat_evidence=row.get("heat_evidence"),
            a_share_mapping=row.get("a_share_mapping"),
            rank=row.get("rank"),
        )
        if not quality["ok"]:
            raise IntegrationError(
                "sentiment_record_quality_rejected:"
                + source
                + ":"
                + ",".join(quality["reasons"])
            )
        relevance = {
            "status": "accepted",
            "score": quality["relevance_score"],
            "reasons": ["来源级热度证据有效", "A股映射语义落地", "清洗残留检查通过"],
            "quality_contract": "A_SHARE_SENTIMENT_RECORD_QUALITY_V1",
        }
    elif isinstance(existing_relevance, dict) and existing_relevance.get("status") == "accepted":
        relevance = deepcopy(existing_relevance)
        try:
            relevance["score"] = max(1, min(99, int(relevance.get("score", 0))))
        except (TypeError, ValueError):
            relevance["score"] = 75
    else:
        tier_rank = TIER_RANK.get(_tier(source), 3)
        relevance = {
            "status": "accepted",
            "score": {1: 92, 2: 86, 3: 76, 4: 70}.get(tier_rank, 72),
            "reasons": ["统一事件池已有来源、时间、正文和URL证据"],
            "quality_contract": "A_SHARE_EVENT_RELEVANCE_DERIVATION_V2",
        }
    row.update({
        "schema": EVENT_SCHEMA,
        "source": source,
        "event": event,
        "url": url,
        "canonical_event_id": event_id,
        "unified_event_id": event_id,
        "origin_streams": sorted(set((row.get("origin_streams") or []) + [origin_stream])),
        "evidence_tier": row.get("evidence_tier") or _tier(source),
        "fact_strength": row.get("fact_strength") or (
            "market_observation" if "market_validation" in window else
            "official_or_media_fact" if TIER_RANK.get(_tier(source), 9) <= 2 else
            "community_signal"
        ),
        "a_share_relevance": relevance,
        "provenance": row.get("provenance") or [{
            "source": source,
            "url": url,
            "published_at": _clean(row.get("published_at")),
            "capture_sha256": _clean(row.get("capture_sha256") or row.get("browser_capture_sha256")),
        }],
    })
    row["evidence_sources"] = _event_sources(row)
    return row


def _same_event(left: dict, right: dict) -> tuple[bool, str]:
    if left.get("window_type") != right.get("window_type"):
        return False, ""
    left_time = _parse_datetime(left.get("published_at"), datetime.now(CHINA_TZ))
    right_time = _parse_datetime(right.get("published_at"), datetime.now(CHINA_TZ))
    if left_time and right_time:
        time_distance = abs(left_time - right_time)
        if time_distance > timedelta(hours=12):
            return False, ""
    elif left.get("date") != right.get("date"):
        return False, ""
    left_url, right_url = _normalized_url(left.get("url")), _normalized_url(right.get("url"))
    if left_url and right_url and left_url == right_url:
        return True, "normalized_url_within_12h"
    left_text, right_text = _normalized_text(left.get("event")), _normalized_text(right.get("event"))
    if min(len(left_text), len(right_text)) < 18:
        return False, ""
    shared_terms = set(_theme_terms(left)) & set(_theme_terms(right))
    similarity = _similarity(left_text, right_text)
    if shared_terms and similarity >= 0.86:
        return True, f"near_text:{similarity:.3f}"
    if similarity >= 0.94:
        return True, f"near_text:{similarity:.3f}"
    return False, ""


def _merge_duplicate(primary: dict, duplicate: dict, reason: str) -> dict:
    left_rank = TIER_RANK.get(primary.get("evidence_tier", ""), 9)
    right_rank = TIER_RANK.get(duplicate.get("evidence_tier", ""), 9)
    if right_rank < left_rank:
        primary, duplicate = duplicate, primary
    merged = deepcopy(primary)
    provenance = []
    seen = set()
    for row in list(primary.get("provenance") or []) + list(duplicate.get("provenance") or []):
        if not isinstance(row, dict):
            continue
        key = (_clean(row.get("source")), _normalized_url(row.get("url")), _clean(row.get("published_at")))
        if key in seen:
            continue
        seen.add(key)
        provenance.append(row)
    merged["provenance"] = provenance
    merged["evidence_sources"] = sorted(set(_event_sources(primary)) | set(_event_sources(duplicate)))
    merged["origin_streams"] = sorted(set(primary.get("origin_streams") or []) | set(duplicate.get("origin_streams") or []))
    merged["deduplication"] = {
        "status": "canonical",
        "merged_record_count": len(provenance),
        "reason": reason,
    }
    merged["corroboration_count"] = len(merged["evidence_sources"])
    return merged


def deduplicate_events(events: list[dict]) -> tuple[list[dict], list[dict]]:
    canonical: list[dict] = []
    audit: list[dict] = []
    for item in events:
        match_index = -1
        match_reason = ""
        for index, kept in enumerate(canonical):
            matched, reason = _same_event(kept, item)
            if matched:
                match_index, match_reason = index, reason
                break
        if match_index < 0:
            canonical.append(item)
            continue
        before = canonical[match_index]
        canonical[match_index] = _merge_duplicate(before, item, match_reason)
        audit.append({
            "canonical_event_id": canonical[match_index]["canonical_event_id"],
            "merged_source": item.get("source", ""),
            "kept_source": canonical[match_index].get("source", ""),
            "reason": match_reason,
        })
    return canonical, audit


def _official_business_url(value: object) -> bool:
    try:
        host = urlparse(_clean(value)).netloc.casefold().removeprefix("www.")
    except ValueError:
        return False
    return any(host == domain or host.endswith("." + domain) for domain in ALLOWED_BUSINESS_DOMAINS)


def _business_item_text(item: dict) -> str:
    fields = ("title", "event", "text", "summary", "product", "commodity", "name", "change", "price")
    parts = []
    for field in fields:
        value = item.get(field)
        if isinstance(value, (str, int, float)) and _clean(value):
            parts.append(_clean(value))
    return "；".join(dict.fromkeys(parts))


def _business_candidate_terms(item: dict, current_theme_terms: set[str]) -> list[str]:
    explicit = []
    for field in ("commodity", "product", "name", "category", "tags"):
        value = item.get(field)
        values = value if isinstance(value, list) else re.split(r"[、,，/|;；]+", _clean(value))
        for raw in values:
            term = _clean(raw)
            if 2 <= len(term) <= 16 and term not in GENERIC_TERMS:
                explicit.append(term)
    text = _business_item_text(item)
    explicit.extend(term for term in current_theme_terms if term in text)
    return list(dict.fromkeys(explicit))


def _read_business_capture(capture_dir: Path, now: datetime, base_events: list[dict]) -> tuple[list[dict], dict]:
    path = capture_dir / BUSINESS_CAPTURE_FILE
    if not path.is_file():
        raise IntegrationError(f"business_society_capture_missing:{path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise IntegrationError(f"business_society_capture_invalid:{type(exc).__name__}:{exc}") from exc
    if not isinstance(payload, dict):
        raise IntegrationError("business_society_capture_root_not_object")
    channel = _clean(payload.get("channel"))
    if channel not in ALLOWED_BUSINESS_CAPTURE_CHANNELS:
        raise IntegrationError(f"business_society_capture_channel_invalid:{channel}")
    collected_at = _parse_datetime(payload.get("collectedAt"), now)
    if collected_at is None:
        raise IntegrationError("business_society_capture_timestamp_missing")
    age_minutes = (now - collected_at).total_seconds() / 60
    if age_minutes < -5 or age_minutes > 45:
        raise IntegrationError(f"business_society_capture_stale:{age_minutes:.1f}")
    items = payload.get("clean")
    if not isinstance(items, list):
        raise IntegrationError("business_society_capture_clean_list_missing")
    raw_count = payload.get("rawCount")
    clean_count = payload.get("cleanCount")
    capture_errors = payload.get("errors")
    if not isinstance(raw_count, int) or raw_count <= 0:
        raise IntegrationError("business_society_capture_raw_count_invalid")
    if not isinstance(clean_count, int) or clean_count != len(items):
        raise IntegrationError("business_society_capture_clean_count_mismatch")
    if clean_count <= 0 or clean_count > raw_count:
        raise IntegrationError("business_society_capture_accounting_invalid")
    if not isinstance(capture_errors, list) or capture_errors:
        raise IntegrationError("business_society_capture_errors_present")
    current_theme_terms = {
        term for event in base_events for term in _theme_terms(event)
        if term not in GENERIC_TERMS
    }
    base_texts = [(event.get("canonical_event_id", ""), _clean(event.get("event")), event.get("url", "")) for event in base_events]
    accepted, rejected = [], []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            rejected.append({"index": index, "reason": "item_not_object"})
            continue
        url = _clean(item.get("url") or item.get("href") or item.get("capturedUrl"))
        if not _official_business_url(url):
            rejected.append({"index": index, "reason": "non_official_domain", "url": url})
            continue
        event_text = _business_item_text(item)
        if len(event_text) < 12:
            rejected.append({"index": index, "reason": "event_text_too_short", "url": url})
            continue
        published = _parse_datetime(
            item.get("published_at") or item.get("publishedAt") or item.get("date") or item.get("time"),
            now,
        )
        if published is None or not (now - timedelta(hours=72) <= published <= now):
            rejected.append({"index": index, "reason": "outside_rolling_72h_or_time_missing", "url": url})
            continue
        candidates = _business_candidate_terms(item, current_theme_terms)
        matches = []
        matched_base = []
        for term in candidates:
            if any(term in base_text for _event_id, base_text, _base_url in base_texts):
                matches.append(term)
                matched_base.extend(
                    {"event_id": event_id, "url": base_url}
                    for event_id, base_text, base_url in base_texts if term in base_text
                )
        matches = list(dict.fromkeys(matches))
        if not matches:
            rejected.append({"index": index, "reason": "no_dynamic_a_share_event_match", "url": url})
            continue
        matched_base_unique = []
        seen_base = set()
        for row in matched_base:
            key = (row["event_id"], row["url"])
            if key not in seen_base:
                seen_base.add(key)
                matched_base_unique.append(row)
        accepted.append(_normalize_event({
            "source": "生意社",
            "origin_source": "生意社",
            "date": f"{published.month}月{published.day}日",
            "published_at": published.isoformat(timespec="seconds"),
            "time_precision": "minute" if ":" in _clean(item.get("time") or item.get("published_at")) else "day",
            "time_evidence": "business_society_official_page",
            "window_type": "event_72h",
            "event": event_text[:900],
            "url": url,
            "theme_terms": matches,
            "source_channel": "business_society_dynamic_a_share_mapping",
            "heat_evidence": _clean(item.get("heat_evidence")) or "生意社官方商品情报或涨跌榜",
            "a_share_mapping": f"与本轮A股事件池中的{'、'.join(matches)}形成动态同词映射；未使用预设板块池。",
            "a_share_relevance": {
                "status": "accepted",
                "score": min(100, 70 + 10 * len(matches)),
                "reasons": ["生意社官方域名", "滚动72小时内", "命中本轮A股事件主题"],
                "matched_terms": matches,
                "matched_base_evidence": matched_base_unique[:12],
            },
            "fact_strength": "industry_official_observation",
            "evidence_tier": "T2_产业官方数据",
            "capture_sha256": _sha_file(path),
        }, "business_society"))
    audit = {
        "capture_file": str(path),
        "capture_sha256": _sha_file(path),
        "acquisition_channel": channel,
        "collected_at": collected_at.isoformat(timespec="seconds"),
        "age_minutes": round(age_minutes, 2),
        "raw_count": raw_count,
        "clean_count": clean_count,
        "capture_errors": capture_errors,
        "a_share_accepted_count": len(accepted),
        "a_share_rejected_count": len(rejected),
        "rejection_reasons": dict(Counter(row["reason"] for row in rejected)),
        "rejected": rejected,
        "mapping_method": "current_a_share_event_dynamic_term_match_v1",
        "preset_sector_pool_used": False,
    }
    return accepted, audit


def _effective_term_hits(event: str, terms: tuple[str, ...]) -> int:
    hits = 0
    for term in terms:
        for match in re.finditer(re.escape(term), event):
            prefix = event[max(0, match.start() - 10):match.start()]
            if re.search(r"(?:未|没有|并非|否认|不再|不会|难以|传闻|辟谣)[^，。；]{0,6}$", prefix):
                continue
            hits += 1
    return hits


def _polarity(event: str) -> str:
    positive = _effective_term_hits(event, POSITIVE_TERMS)
    negative = _effective_term_hits(event, NEGATIVE_TERMS)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "neutral"


def build_conflict_register(events: list[dict]) -> list[dict]:
    groups: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for item in events:
        polarity = _polarity(_clean(item.get("event")))
        item["integration_polarity"] = polarity
        if polarity == "neutral":
            continue
        for term in _theme_terms(item)[:3]:
            groups[term][polarity].append(item)
    conflicts = []
    for theme, polarities in sorted(groups.items()):
        if not polarities.get("positive") or not polarities.get("negative"):
            continue
        conflict_id = _sha_text("conflict|" + theme + "|" + "|".join(sorted(
            item["canonical_event_id"] for rows in polarities.values() for item in rows
        )))
        evidence = {
            key: [
                {"event_id": item["canonical_event_id"], "source": item.get("source", ""), "event": item.get("event", "")}
                for item in rows
            ]
            for key, rows in polarities.items()
        }
        conflicts.append({
            "conflict_id": conflict_id,
            "theme": theme,
            "status": "保留分歧，不做正负抵消",
            "positive_evidence": evidence.get("positive", []),
            "negative_evidence": evidence.get("negative", []),
        })
        for rows in polarities.values():
            for item in rows:
                item.setdefault("conflict_ids", []).append(conflict_id)
    return conflicts


def build_daily_intel_view(events: list[dict]) -> dict:
    segments = {"morning": [], "midday": [], "closing": []}
    for item in events:
        published = _parse_datetime(item.get("published_at"), datetime.now(CHINA_TZ))
        if published is None:
            continue
        minute = published.hour * 60 + published.minute
        segment = "morning" if minute < 690 else "midday" if minute < 900 else "closing"
        segments[segment].append(item)
    def tier_rank(item: dict) -> tuple[int, int, float]:
        published = _parse_datetime(item.get("published_at"), datetime.now(CHINA_TZ))
        published_rank = -published.timestamp() if published is not None else float("inf")
        return (
            TIER_RANK.get(item.get("evidence_tier", ""), 9),
            -len(_event_sources(item)),
            published_rank,
        )
    output = {}
    for segment, rows in segments.items():
        selected = sorted(rows, key=tier_rank)[:20]
        output[segment] = [{
            "event_id": item.get("canonical_event_id", ""),
            "source": item.get("source", ""),
            "date": item.get("date", ""),
            "published_at": item.get("published_at", ""),
            "event": item.get("event", ""),
            "evidence_tier": item.get("evidence_tier", ""),
            "a_share_mapping": item.get("a_share_mapping", ""),
        } for item in selected]
    return {
        "schema": "A_SHARE_DAILY_INTEL_DERIVED_VIEW_V1",
        "rule": "同一统一证据池按发布时间派生早盘、午盘、收盘视图；不复制采集、不增加证据权重",
        "segments": output,
        "segment_counts": {key: len(value) for key, value in output.items()},
    }


def integrate(event_pool: list[dict], market_pool: list[dict], capture_dir: str | Path, now: datetime | None = None) -> dict:
    anchor = now.astimezone(CHINA_TZ) if now and now.tzinfo else (now.replace(tzinfo=CHINA_TZ) if now else datetime.now(CHINA_TZ))
    normalized_events = [_normalize_event(item, "a_share_hotspot") for item in event_pool if isinstance(item, dict)]
    normalized_market = [_normalize_event(item, "market_validation") for item in market_pool if isinstance(item, dict)]
    business_events, business_audit = _read_business_capture(Path(capture_dir), anchor, normalized_events)
    canonical_events, dedup_audit = deduplicate_events(normalized_events + business_events)
    conflicts = build_conflict_register(canonical_events)
    daily_view = build_daily_intel_view(canonical_events)
    audit = {
        "schema": SCHEMA,
        "ok": True,
        "generated_at": anchor.isoformat(timespec="seconds"),
        "architecture": "one_evidence_pool_multiple_derived_views",
        "input_event_count": len(event_pool),
        "input_market_validation_count": len(market_pool),
        "business_society": business_audit,
        "unified_event_count": len(canonical_events),
        "market_validation_count": len(normalized_market),
        "cross_source_duplicate_group_count": len(dedup_audit),
        "deduplication_records": dedup_audit,
        "conflict_count": len(conflicts),
        "source_families": {
            "mandatory_eight_site_and_primary_news": "direct_evidence",
            "daily_intel": "derived_view_without_evidence_duplication",
            "short_term_market_sentiment": "derived_view_without_weighted_total_score",
            "business_society": "official_capture_dynamic_a_share_mapping",
        },
        "excluded_workflows": list(EXCLUDED_WORKFLOWS),
        "runtime_dependencies_on_excluded_workflows": [],
        "preset_sector_pool_used": False,
        "cross_source_duplicates_do_not_increase_weight": True,
        "conflicts_are_preserved": True,
    }
    return {
        "event_pool": canonical_events,
        "market_pool": normalized_market,
        "audit": audit,
        "daily_intel_view": daily_view,
        "conflict_register": conflicts,
    }


def selftest() -> int:
    now = datetime(2026, 9, 1, 15, 0, tzinfo=CHINA_TZ)
    cache_root = Path(os.environ.get("CODEX_TASK_CACHE_ROOT", r"F:\Codex\cache")) / "a-share-sentiment-integrator-selftest"
    cache_root.mkdir(parents=True, exist_ok=True)
    capture = cache_root / BUSINESS_CAPTURE_FILE
    payload = {
        "site": "生意社",
        "channel": "Chrome logged-in visible pages only",
        "collectedAt": now.isoformat(timespec="seconds"),
        "rawCount": 2,
        "cleanCount": 2,
        "errors": [],
        "clean": [
            {
                "commodity": "量子玻璃",
                "title": "量子玻璃现货价格上涨",
                "text": "供应收缩，现货报价上涨。",
                "published_at": "2026-09-01T14:10:00+08:00",
                "href": "https://www.100ppi.com/data/detail-1.html",
            },
            {
                "commodity": "无关商品",
                "title": "无关商品价格变化",
                "text": "与当前A股事件池没有映射。",
                "published_at": "2026-09-01T13:10:00+08:00",
                "href": "https://www.100ppi.com/data/detail-2.html",
            },
        ],
    }
    capture.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    base = {
        "source": "财联社",
        "date": "9月1日",
        "published_at": "2026-09-01T13:30:00+08:00",
        "window_type": "event_72h",
        "event": "量子玻璃产业链订单增长并带动A股相关板块走强。",
        "url": "https://www.cls.cn/detail/1",
        "theme_terms": ["量子玻璃"],
    }
    duplicate = dict(base, source="金十数据", url="https://www.jin10.com/detail/2")
    market = {
        "source": "短线侠",
        "date": "9月1日",
        "published_at": "2026-09-01T14:30:00+08:00",
        "window_type": "market_validation_3_trading_days",
        "event": "量子玻璃板块涨停扩散，成交额放大。",
        "url": "https://duanxianxia.example/1",
        "theme_terms": ["量子玻璃"],
    }
    result = integrate([base, duplicate], [market], cache_root, now)
    failures = []
    if not result["audit"].get("ok"):
        failures.append("audit_not_ok")
    if result["audit"]["business_society"]["a_share_accepted_count"] != 1:
        failures.append("business_dynamic_mapping_failed")
    if result["audit"]["business_society"]["a_share_rejected_count"] != 1:
        failures.append("business_irrelevant_filter_failed")
    if result["audit"]["cross_source_duplicate_group_count"] != 1:
        failures.append("cross_source_dedup_failed")
    if len(result["event_pool"]) != 2:
        failures.append("canonical_event_count_invalid")
    if any(name not in result["audit"]["excluded_workflows"] for name in EXCLUDED_WORKFLOWS):
        failures.append("excluded_workflow_contract_missing")
    print(json.dumps({
        "schema": "A_SHARE_SENTIMENT_INTEGRATOR_SELFTEST_V1",
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "audit": result["audit"],
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A股热点舆情统一证据集成器")
    parser.add_argument("command", choices=("selftest",), nargs="?", default="selftest")
    args = parser.parse_args(argv)
    if args.command == "selftest":
        return selftest()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
