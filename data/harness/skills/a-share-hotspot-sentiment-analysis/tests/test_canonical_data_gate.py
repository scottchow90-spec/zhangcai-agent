from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "scripts" / "canonical_business_adapter.py"
SPEC = importlib.util.spec_from_file_location("sentiment_canonical_adapter_test", RUNTIME)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_build_data_gate_binds_all_required_dimensions(tmp_path):
    sentiment = tmp_path / "sentiment"
    sentiment.mkdir()
    event = {"source": "财联社", "event": "A股主题事件", "published_at": "2026-09-01T14:00:00+08:00"}
    _write(sentiment / "a_share_sentiment_event_pool.json", [event] * 20)
    _write(sentiment / "a_share_sentiment_scores.json", [{"name": "主题甲"}, {"name": "主题乙"}])
    _write(sentiment / "a_share_sentiment_clusters.json", [{"name": "主题甲"}, {"name": "主题乙"}])
    sources = ["淘股吧", "雪球", "微博", "知乎", "股吧", "韭研公社", "财联社", "金十数据"]
    _write(sentiment / "a_share_sentiment_mandatory_sources_audit.json", {
        "ok": True, "required_sources": sources, "source_counts": {name: 10 for name in sources},
    })
    _write(sentiment / "a_share_sentiment_market_cross_validation_audit.json", {
        "ok": True, "present_sources": ["通达信", "短线侠", "连板网"],
    })
    _write(sentiment / "a_share_sentiment_market_validation_pool.json", [
        {"source": "通达信·市场复盘", "market_date": "9月1日", "event": "涨停42家"},
        {"source": "连板网·市场复盘", "date": "9月1日", "event": "涨停43家"},
    ])
    _write(sentiment / "a_share_sentiment_acquisition_audit.json", {
        "ok": True, "event_window_start": "2026-08-30T00:00:00+08:00", "event_window_end": "2026-09-01T15:00:00+08:00",
    })
    _write(sentiment / "a_share_sentiment_source_integration_audit.json", {
        "ok": True, "unified_event_count": 20,
        "business_society": {
            "preset_sector_pool_used": False,
            "capture_sha256": "a" * 64,
            "raw_count": 80,
            "clean_count": 80,
            "capture_errors": [],
        },
    })
    _write(sentiment / "a_share_sentiment_delivery_audit.json", {"ok": True})
    gate = MODULE.build_data_gate(
        {"run_dir": str(tmp_path), "target_date": "20260901"},
        {
            "CODEX_STOCK_EVIDENCE_TRADING_DATE": "2026-09-01",
            "CODEX_STOCK_EVIDENCE_SET_ID": "sha256:" + "b" * 64,
            "CODEX_STOCK_SHARED_EVIDENCE_STATUS": "CLEAN_PASS",
        },
    )
    assert gate["status"] == "CLEAN_PASS"
    assert gate["errors"] == []
    assert set(gate["dimensions"]) == {
        "identity", "effective_trading_date", "quote_kline", "fundamentals",
        "news_announcements", "sector_theme", "source_freshness",
    }
    assert gate["effective_trading_date"] == "2026-09-01"
    assert gate["effective_market_sources"] == ["连板网·市场复盘", "通达信·市场复盘"]


def test_build_data_gate_never_uses_report_generation_day_as_trading_day(tmp_path):
    sentiment = tmp_path / "sentiment"
    sentiment.mkdir()
    required = {
        "a_share_sentiment_event_pool.json": [],
        "a_share_sentiment_scores.json": [],
        "a_share_sentiment_clusters.json": [],
        "a_share_sentiment_mandatory_sources_audit.json": {},
        "a_share_sentiment_market_cross_validation_audit.json": {},
        "a_share_sentiment_market_validation_pool.json": [
            {"source": "短线侠·市场复盘", "date": "9月2日", "event": "盘前快照"},
        ],
        "a_share_sentiment_acquisition_audit.json": {},
        "a_share_sentiment_source_integration_audit.json": {},
        "a_share_sentiment_delivery_audit.json": {"report": {"mtime": "2026-09-02T00:30:00+08:00"}},
    }
    for name, payload in required.items():
        _write(sentiment / name, payload)

    gate = MODULE.build_data_gate(
        {"run_dir": str(tmp_path), "target_date": "20260902"},
        {
            "CODEX_STOCK_EVIDENCE_TRADING_DATE": "2026-09-01",
            "CODEX_STOCK_EVIDENCE_SET_ID": "sha256:" + "b" * 64,
            "CODEX_STOCK_SHARED_EVIDENCE_STATUS": "CLEAN_PASS",
        },
    )

    assert gate["effective_trading_date"] == ""
    assert gate["dimensions"]["effective_trading_date"]["status"] == "BLOCKED"
