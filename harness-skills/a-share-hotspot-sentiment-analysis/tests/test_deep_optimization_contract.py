from __future__ import annotations

import datetime as dt
import importlib.util
import json
import shutil
from pathlib import Path

import pytest


ROOT = Path(r"D:\C盘转移\日志\codex\skills\a-share-hotspot-sentiment-analysis")
WORKFLOW = (
    ROOT
    / "components"
    / "a-share-sentiment-workflow"
    / "scripts"
    / "a-share-sentiment-workflow.py"
)
FALLBACK = ROOT / "scripts" / "public_readonly_fallback.py"
INTEGRATOR = ROOT / "scripts" / "a_share_sentiment_integrator.py"
CONTRACTS = ROOT / "scripts" / "sentiment_quality_contracts.py"
DELIVERY_VALIDATOR = ROOT / "scripts" / "report_delivery_validator.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_one_acquisition_contract_includes_business_society_everywhere():
    contracts = load_module(CONTRACTS, "sentiment_quality_contract_test")
    workflow = load_module(WORKFLOW, "sentiment_workflow_acquisition_contract_test")

    assert contracts.REQUIRED_CAPTURE_FILES == (
        "primary.json",
        "tgb.json",
        "xueqiu.json",
        "weibo.json",
        "zhihu.json",
        "guba.json",
        "jiuyangongshe.json",
        "cls.json",
        "jin10.json",
        "business_society.json",
    )
    assert tuple(workflow.required_acquisition_capture_files()) == contracts.REQUIRED_CAPTURE_FILES


def test_source_quality_gate_rejects_fake_heat_generic_mapping_and_bad_accounting():
    contracts = load_module(CONTRACTS, "sentiment_quality_negative_test")
    fallback = load_module(FALLBACK, "sentiment_quality_grounded_mapping_test")

    fake_heat = contracts.validate_sentiment_record(
        source="金十数据",
        event="金十数据宏观快讯称海外市场出现波动，页面展示重要度0。",
        heat_evidence="重要度0",
        a_share_mapping="直接涉及A股个股、板块、指数、资金或市场情绪。",
        rank=1,
    )
    assert fake_heat["ok"] is False
    assert "heat_evidence_invalid" in fake_heat["reasons"]

    generic_mapping = contracts.validate_sentiment_record(
        source="知乎",
        event="普通课堂讨论与个人成长经验分享，不涉及证券市场。",
        heat_evidence="站内高热榜第2位",
        a_share_mapping="直接涉及A股个股、板块、指数、资金或市场情绪。",
        rank=2,
    )
    assert generic_mapping["ok"] is False
    assert "a_share_mapping_not_semantically_grounded" in generic_mapping["reasons"]

    accounting = contracts.validate_capture_accounting(
        raw_count=7,
        clean_count=10,
        clean_rows=[{"href": f"https://example.test/{index}"} for index in range(10)],
    )
    assert accounting["ok"] is False
    assert "clean_count_gt_raw_count" in accounting["reasons"]

    grounded_mapping = fallback._infer_a_share_mapping("WTI原油价格上涨并影响能源产业链")
    grounded = contracts.validate_sentiment_record(
        source="金十数据",
        event="WTI原油价格上涨并影响能源产业链",
        heat_evidence="重要度1",
        a_share_mapping=grounded_mapping,
        rank=1,
    )
    assert grounded["ok"] is True
    assert "原油" in grounded["mapping"]["grounded_mapping_terms"]


def test_mandatory_collector_skips_zero_heat_until_ten_real_rows():
    fallback = load_module(FALLBACK, "sentiment_fallback_real_heat_count_test")
    collected_at = dt.datetime(2026, 9, 1, 22, 0, tzinfo=dt.timezone(dt.timedelta(hours=8)))
    rows = []
    for index in range(1, 31):
        rows.append({
            "title": f"WTI原油与A股能源产业链高热快讯{index}",
            "url": f"https://www.jin10.com/flash/{index}",
            "text": "原油价格上涨并映射A股能源产业链。",
            "published_at": collected_at.isoformat(timespec="seconds"),
            "hot_value": "重要度0" if index <= 20 else "重要度1",
        })
    diagnostics = {}

    captured = fallback._mandatory_sentiment_rows(
        "jin10",
        rows,
        collected_at,
        diagnostics,
    )

    assert len(captured) == 10
    assert captured[0]["rank"] == 21
    assert diagnostics["heat_rejected"] == 20
    assert diagnostics["quality_candidate_accepted"] == 10


def test_xueqiu_live_hot_stock_rows_have_real_rank_heat_and_a_share_identity():
    fallback = load_module(FALLBACK, "sentiment_fallback_xueqiu_hot_stock_test")
    observed_at = dt.datetime(2026, 9, 1, 15, 0, tzinfo=dt.timezone(dt.timedelta(hours=8)))

    rows = fallback._xueqiu_hot_sentiment_rows(
        [{"name": "样本股份", "symbol": "SH600000", "value": 5134, "percent": 9.99}],
        observed_at,
    )

    assert len(rows) == 1
    assert rows[0]["published_at"] == observed_at.isoformat(timespec="seconds")
    assert "热股榜第1位" in rows[0]["hot_value"]
    assert "A股股票" in rows[0]["a_share_context"]


def test_public_fallback_same_run_writes_business_society_capture(tmp_path):
    fallback = load_module(FALLBACK, "public_fallback_business_same_run_test")
    collected_at = dt.datetime(2026, 9, 1, 15, 0, tzinfo=dt.timezone(dt.timedelta(hours=8)))
    site_keys = ("tgb", "xueqiu", "weibo", "zhihu", "guba", "jiuyangongshe", "cls", "jin10")
    payloads = {
        key: [
            {
                "title": f"{key} A股算力板块高热讨论 {index}",
                "url": f"https://example.test/{key}/{index}",
                "hot_value": 10000 - index,
                "text": "算力产业订单增长，A股相关板块出现涨停扩散与资金回流。",
                "published_at": (collected_at - dt.timedelta(minutes=index)).isoformat(timespec="seconds"),
            }
            for index in range(1, 11)
        ]
        for key in site_keys
    }
    payloads.update({
        "sina": [
            {
                "title": f"A股算力产业事件 {index}",
                "url": f"https://example.test/sina/{index}",
                "intro": "算力产业订单增长并映射A股相关公司。",
                "ctime": int((collected_at - dt.timedelta(minutes=index)).timestamp()),
                "media_name": "新浪财经",
            }
            for index in range(1, 31)
        ],
        "duanxianxia": [],
        "business_society": [
            {
                "commodity": "工业硅",
                "title": "工业硅现货价格上涨",
                "text": "供应收缩，报价上涨。",
                "published_at": collected_at.isoformat(timespec="seconds"),
                "href": "https://www.100ppi.com/data/detail-test.html",
            }
        ],
    })

    manifest = fallback.write_sentiment_capture_bundle(
        tmp_path,
        payloads=payloads,
        breadth_records=[],
        collected_at=collected_at,
    )

    business_path = tmp_path / "business_society.json"
    assert manifest["status"] == "PASS"
    assert business_path.is_file()
    business = json.loads(business_path.read_text(encoding="utf-8"))
    assert business["channel"] == "official_public_page_readonly"
    assert business["cleanCount"] == 1
    assert business["rawCount"] == 1


def test_short_term_sentiment_has_five_fact_dimensions_and_confidence():
    workflow = load_module(WORKFLOW, "sentiment_workflow_five_dimension_test")
    now = dt.datetime(2026, 9, 1, 15, 5, tzinfo=workflow.CHINA_TZ)
    pool = [
        {
            "source": "连板网·市场复盘",
            "date": "9月1日",
            "published_at": now.isoformat(timespec="seconds"),
            "window_type": workflow.MARKET_VALIDATION_WINDOW_TYPE,
            "event": "9月1日全市场涨停42家，最高连板5板，二进三晋级率40%，热点扩散至3个方向，两市成交额18000亿元，较前一日放量8%。",
            "url": "https://lianban.example/2026-09-01",
            "validation_dimensions": ["热点", "涨停", "晋级", "成交额"],
        },
        {
            "source": "指数宽度甲",
            "source_key": "width-a",
            "date": "9月1日",
            "published_at": now.isoformat(timespec="seconds"),
            "window_type": workflow.MARKET_VALIDATION_WINDOW_TYPE,
            "event": "9月1日A股上涨3500家、下跌1700家，上涨占比67.3%。",
            "url": "https://width-a.example/2026-09-01",
        },
        {
            "source": "指数宽度乙",
            "source_key": "width-b",
            "date": "9月1日",
            "published_at": now.isoformat(timespec="seconds"),
            "window_type": workflow.MARKET_VALIDATION_WINDOW_TYPE,
            "event": "9月1日A股上涨3500家、下跌1700家，上涨占比67.3%。",
            "url": "https://width-b.example/2026-09-01",
        },
    ]

    result = workflow.short_term_sentiment_assessment(pool, [{"stance": "增强"}])

    assert set(result["dimensions"]) == {
        "limit_up",
        "promotion",
        "hotspot_spread",
        "turnover",
        "market_width",
    }
    assert all(row["status"] == "verified" for row in result["dimensions"].values())
    assert result["confidence"] in {"中", "高"}
    assert result["conflict_statement"]
    assert all(
        row["quality_contract"] == "exact_numeric_market_fact_only"
        for row in result["dimensions"].values()
    )


def test_short_term_sentiment_never_marks_marker_only_news_as_verified():
    workflow = load_module(WORKFLOW, "sentiment_workflow_marker_only_dimension_test")
    pool = [
        {
            "source": "财经媒体",
            "date": "9月1日",
            "event": "涨停个股风险提示，连板题材分化，成交额相关讨论升温。",
            "url": "https://example.test/news",
        },
        {
            "source": "宽度来源甲",
            "source_key": "width-a",
            "date": "9月1日",
            "event": "9月1日全市场上涨家数3200、下跌家数2000。",
            "url": "https://example.test/width-a",
        },
        {
            "source": "宽度来源乙",
            "source_key": "width-b",
            "date": "9月1日",
            "event": "9月1日全市场上涨家数3200、下跌家数2000。",
            "url": "https://example.test/width-b",
        },
    ]

    result = workflow.short_term_sentiment_assessment(pool, [{"stance": "分歧"}])

    assert result["dimension_gate_passed"] is False
    assert result["dimensions"]["limit_up"]["status"] == "missing"
    assert result["dimensions"]["promotion"]["status"] == "missing"
    assert result["dimensions"]["turnover"]["status"] == "missing"


def test_integrator_never_defaults_unproved_sentiment_relevance_to_100():
    integrator = load_module(INTEGRATOR, "sentiment_integrator_relevance_test")
    item = {
        "source": "金十数据",
        "date": "9月1日",
        "published_at": "2026-09-01T13:30:00+08:00",
        "window_type": "event_72h",
        "event": "海外市场普通快讯，页面显示重要度0，未说明A股传导。",
        "url": "https://www.jin10.com/detail/zero",
        "heat_evidence": "重要度0",
        "a_share_mapping": "直接涉及A股个股、板块、指数、资金或市场情绪。",
    }

    with pytest.raises(integrator.IntegrationError):
        integrator._normalize_event(item, "mandatory_eight_site_sentiment")


def test_cross_midnight_duplicates_merge_inside_twelve_hours():
    integrator = load_module(INTEGRATOR, "sentiment_integrator_cross_midnight_test")
    first = {
        "canonical_event_id": "event-a",
        "source": "财联社",
        "published_at": "2026-09-01T23:58:00+08:00",
        "date": "9月1日",
        "window_type": "event_72h",
        "event": "算力产业订单显著增长，A股相关板块资金回流并出现涨停扩散。",
        "url": "https://example.test/event?id=88&utm_source=feed",
        "evidence_tier": "tier_2_mainstream_financial_media",
        "provenance": [{"source": "财联社", "url": "https://example.test/event?id=88"}],
    }
    second = {
        "canonical_event_id": "event-b",
        "source": "雪球",
        "published_at": "2026-09-02T00:03:00+08:00",
        "date": "9月2日",
        "window_type": "event_72h",
        "event": "算力产业订单显著增长，A股相关板块资金回流并出现涨停扩散。",
        "url": "https://example.test/event?id=88",
        "evidence_tier": "tier_4_community_sentiment",
        "provenance": [{"source": "雪球", "url": "https://example.test/event?id=88"}],
    }

    canonical, audit = integrator.deduplicate_events([first, second])

    assert len(canonical) == 1
    assert len(audit) == 1
    assert audit[0]["reason"] == "normalized_url_within_12h"
    assert canonical[0]["corroboration_count"] == 2


def test_polarity_ignores_negated_negative_terms():
    integrator = load_module(INTEGRATOR, "sentiment_integrator_negation_test")

    assert integrator._polarity("公司否认需求走弱，新增订单增长并持续放量。") == "positive"


def test_formatted_delivery_refuses_report_without_real_word_render_audit(tmp_path):
    validator = load_module(DELIVERY_VALIDATOR, "sentiment_delivery_render_gate_test")
    report_dir = tmp_path / "sentiment"
    report_dir.mkdir()
    report = report_dir / validator.REPORT_NAME
    binding = json.loads(validator.TEMPLATE_BINDING.read_text(encoding="utf-8"))
    template = ROOT / binding["template"]["path"]
    shutil.copy2(template, report)
    report_hash = validator.sha256_file(report)
    (report_dir / validator.REDLINE_NAME).write_text(
        json.dumps({"ok": True, "reasons": []}, ensure_ascii=False), encoding="utf-8"
    )
    (report_dir / validator.DELIVERY_AUDIT_NAME).write_text(
        json.dumps(
            {
                "ok": True,
                "report": {"sha256": report_hash},
                "locked_template_profile": {"sha256": binding["template"]["sha256"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    closure = tmp_path / "closure.json"
    closure.write_text(
        json.dumps({"status": "PASS", "reasons": [], "docx_paths": [str(report)]}, ensure_ascii=False),
        encoding="utf-8",
    )
    business = tmp_path / "business.json"
    business.write_text(
        json.dumps(
            {"schema": "MERGED_STOCK_SKILL_RESULT_V2", "status": "PASS", "closure_audit": {"path": str(closure)}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    code, payload = validator.validate(business, tmp_path / "delivery.json")

    assert code == 2
    assert "word_render_audit_missing" in payload["validation"]["errors"]
