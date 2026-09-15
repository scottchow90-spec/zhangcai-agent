from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "scripts" / "a_share_sentiment_integrator.py"
SPEC = importlib.util.spec_from_file_location("a_share_sentiment_integrator_test", RUNTIME)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
CHINA_TZ = timezone(timedelta(hours=8))


def _base_event(source="财联社", polarity="上涨"):
    return {
        "source": source,
        "date": "9月1日",
        "published_at": "2026-09-01T13:30:00+08:00",
        "window_type": "event_72h",
        "event": f"量子玻璃产业链订单增长，价格{polarity}并带动A股相关板块走强。",
        "url": f"https://example.cn/{source}/{polarity}",
        "theme_terms": ["量子玻璃"],
    }


def _write_business_capture(path: Path, now: datetime, channel="Chrome logged-in visible pages only"):
    payload = {
        "channel": channel,
        "collectedAt": now.isoformat(timespec="seconds"),
        "rawCount": 2,
        "cleanCount": 2,
        "errors": [],
        "clean": [
            {
                "commodity": "量子玻璃",
                "title": "量子玻璃价格上涨",
                "text": "供应收缩，现货报价上涨。",
                "published_at": "2026-09-01T14:10:00+08:00",
                "href": "https://www.100ppi.com/data/accepted.html",
            },
            {
                "commodity": "无关商品",
                "title": "无关商品价格上涨",
                "text": "供应稳定。",
                "published_at": "2026-09-01T14:10:00+08:00",
                "href": "https://www.100ppi.com/data/rejected.html",
            },
        ],
    }
    (path / MODULE.BUSINESS_CAPTURE_FILE).write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )


def test_dynamic_business_mapping_and_cross_source_dedup(tmp_path):
    now = datetime(2026, 9, 1, 15, 0, tzinfo=CHINA_TZ)
    _write_business_capture(tmp_path, now)
    first = _base_event("财联社")
    duplicate = dict(first, source="金十数据", url="https://www.jin10.com/detail/duplicate")
    result = MODULE.integrate([first, duplicate], [], tmp_path, now)

    audit = result["audit"]
    assert audit["ok"] is True
    assert audit["business_society"]["a_share_accepted_count"] == 1
    assert audit["business_society"]["a_share_rejected_count"] == 1
    assert audit["cross_source_duplicate_group_count"] == 1
    assert audit["preset_sector_pool_used"] is False
    assert len(result["event_pool"]) == 2
    merged = next(row for row in result["event_pool"] if "财联社" in row["evidence_sources"])
    assert set(merged["evidence_sources"]) == {"财联社", "金十数据"}


def test_official_public_page_readonly_business_channel_is_strictly_accepted(tmp_path):
    now = datetime(2026, 9, 1, 15, 0, tzinfo=CHINA_TZ)
    _write_business_capture(tmp_path, now, channel="official_public_page_readonly")
    result = MODULE.integrate([_base_event()], [], tmp_path, now)

    audit = result["audit"]["business_society"]
    assert audit["acquisition_channel"] == "official_public_page_readonly"
    assert audit["a_share_accepted_count"] == 1
    assert audit["capture_sha256"]


def test_business_capture_refuses_zero_raw_collection(tmp_path):
    now = datetime(2026, 9, 1, 15, 0, tzinfo=CHINA_TZ)
    _write_business_capture(tmp_path, now, channel="official_public_page_readonly")
    path = tmp_path / MODULE.BUSINESS_CAPTURE_FILE
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update({"rawCount": 0, "cleanCount": 0, "clean": []})
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    try:
        MODULE.integrate([_base_event()], [], tmp_path, now)
    except MODULE.IntegrationError as exc:
        assert "business_society_capture_raw_count_invalid" in str(exc)
    else:
        raise AssertionError("zero-row official acquisition must be blocked")


def test_conflicting_evidence_is_preserved(tmp_path):
    now = datetime(2026, 9, 1, 15, 0, tzinfo=CHINA_TZ)
    _write_business_capture(tmp_path, now)
    positive = _base_event("财联社", "上涨")
    negative = _base_event("交易所公告", "下跌")
    negative["event"] = "量子玻璃产业链需求走弱，价格下跌并提示A股相关板块风险。"
    result = MODULE.integrate([positive, negative], [], tmp_path, now)

    assert len(result["conflict_register"]) == 1
    conflict = result["conflict_register"][0]
    assert conflict["status"] == "保留分歧，不做正负抵消"
    assert conflict["positive_evidence"]
    assert conflict["negative_evidence"]


def test_excluded_workflows_have_no_runtime_dependency(tmp_path):
    now = datetime(2026, 9, 1, 15, 0, tzinfo=CHINA_TZ)
    _write_business_capture(tmp_path, now)
    result = MODULE.integrate([_base_event()], [], tmp_path, now)

    assert result["audit"]["runtime_dependencies_on_excluded_workflows"] == []
    assert set(result["audit"]["excluded_workflows"]) == set(MODULE.EXCLUDED_WORKFLOWS)


def test_daily_view_prefers_fresher_evidence_within_same_tier():
    older = _base_event("财经媒体甲")
    newer = dict(
        _base_event("财经媒体乙"),
        published_at="2026-09-01T14:20:00+08:00",
        event="量子玻璃产业链最新订单继续增长，并带动A股相关板块走强。",
    )
    rows = [MODULE._normalize_event(older, "test"), MODULE._normalize_event(newer, "test")]

    view = MODULE.build_daily_intel_view(rows)

    assert view["segments"]["midday"][0]["source"] == "财经媒体乙"
