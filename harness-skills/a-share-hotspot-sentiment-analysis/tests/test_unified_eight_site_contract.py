from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
from unittest import mock

from docx import Document


ROOT = Path(r"D:\C盘转移\日志\codex\skills\a-share-hotspot-sentiment-analysis")
WORKFLOW_SCRIPT = (
    ROOT
    / "components"
    / "a-share-sentiment-workflow"
    / "scripts"
    / "a-share-sentiment-workflow.py"
)
MERGED_SCRIPT = ROOT / "scripts" / "merged_workflow.py"
PUBLIC_FALLBACK_SCRIPT = ROOT / "scripts" / "public_readonly_fallback.py"
TOP_LEVEL_SKILL = ROOT / "SKILL.md"
TOP_LEVEL_WORKFLOW = ROOT / "references" / "workflow.md"
SOURCE_MANIFEST = ROOT / "references" / "source-manifest.json"
SOCIAL_COMPONENT = ROOT / "components" / "social-finance-brief"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def long_artifact_path(tmp_path: Path, filename: str) -> Path:
    padding = "x" * max(1, 250 - len(str(tmp_path)) - 1)
    out_dir = tmp_path / padding
    Path("\\\\?\\" + str(out_dir.absolute())).mkdir(parents=True)
    target = out_dir / filename
    assert len(str(out_dir)) < 260
    assert len(str(target)) >= 260
    return target


def legacy_windows_method(original):
    def guarded(path, *args, **kwargs):
        if len(str(path)) >= 260 and not str(path).startswith("\\\\?\\"):
            raise FileNotFoundError(str(path))
        return original(path, *args, **kwargs)

    return guarded


def test_workflow_json_io_uses_extended_path_for_long_artifacts(tmp_path):
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_long_path_test")
    target = long_artifact_path(
        tmp_path,
        "a_share_sentiment_market_cross_validation_audit.json",
    )
    extended = Path("\\\\?\\" + str(target.absolute()))

    with (
        mock.patch.object(
            Path,
            "write_text",
            legacy_windows_method(Path.write_text),
        ),
        mock.patch.object(
            Path,
            "read_text",
            legacy_windows_method(Path.read_text),
        ),
    ):
        workflow.write_json_text(target, {"ok": True})
        assert workflow.read_json_or_none(target) == {"ok": True}

    try:
        assert extended.is_file()
    finally:
        extended.unlink(missing_ok=True)


def test_merged_closure_audit_uses_extended_path(tmp_path):
    merged = load_module(MERGED_SCRIPT, "merged_workflow_long_path_test")
    closure_path = long_artifact_path(tmp_path, "merged_closure_audit.json")
    run_root = closure_path.parent
    extended = Path("\\\\?\\" + str(closure_path.absolute()))
    plan = {"mode": "data", "target_date": "20260818"}
    results = [{"mode": "data", "status": "PASS", "steps": []}]

    with mock.patch.object(
        Path,
        "write_text",
        legacy_windows_method(Path.write_text),
    ):
        payload = merged.write_closure_audit(plan, results, run_root)

    try:
        assert payload["status"] == "PASS"
        assert extended.is_file()
    finally:
        extended.unlink(missing_ok=True)


def site_event(workflow, source: str, index: int, now: dt.datetime) -> dict:
    return {
        "source": source,
        "date": workflow.cn_date(now.date()),
        "published_at": now.isoformat(timespec="seconds"),
        "time_precision": "minute",
        "time_evidence": now.isoformat(timespec="minutes"),
        "window_type": workflow.EVENT_WINDOW_TYPE,
        "event": f"{source}高热A股舆情第{index}条，涉及市场情绪、热点板块与资金反馈。",
        "url": f"https://example.test/{source}/{index}",
        "source_channel": workflow.MANDATORY_SENTIMENT_CHANNEL,
        "heat_evidence": f"站内热榜第{index}位",
        "a_share_mapping": "直接涉及A股市场情绪、板块或资金。",
    }


def test_all_mode_is_one_unified_report_without_social_template(tmp_path):
    merged = load_module(MERGED_SCRIPT, "merged_workflow_unified_test")

    plan = merged.build_execution_plan(
        ["all"],
        run_root=tmp_path,
        target_day=dt.date(2026, 8, 13),
    )

    assert [component["mode"] for component in plan["components"]] == ["sentiment"]
    required = [
        artifact
        for component in plan["components"]
        for step in component["steps"]
        for artifact in step["required_artifacts"]
    ]
    assert not any("social-output" in artifact for artifact in required)
    assert not any("三端社媒财经简报" in artifact for artifact in required)
    assert any(
        artifact.endswith("a_share_sentiment_mandatory_sources_audit.json")
        for artifact in required
    )
    assert any(
        artifact.endswith("a_share_sentiment_market_cross_validation_audit.json")
        for artifact in required
    )


def test_eight_sites_are_mandatory_with_ten_valid_items_each():
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_eight_site_test")
    now = workflow._china_datetime()

    assert workflow.REQUIRED_SENTIMENT_SOURCES == [
        "淘股吧",
        "雪球",
        "微博",
        "知乎",
        "东方财富股吧",
        "韭研公社",
        "财联社",
        "金十数据",
    ]
    assert workflow.MANDATORY_SENTIMENT_MIN_PER_SOURCE == 10

    events = [
        site_event(workflow, source, index, now)
        for source in workflow.REQUIRED_SENTIMENT_SOURCES
        for index in range(1, 11)
    ]
    audit = workflow.mandatory_sentiment_source_audit(events, now=now)
    assert audit["ok"] is True
    assert set(audit["source_counts"].values()) == {10}

    incomplete = [
        event
        for event in events
        if not (event["source"] == "金十数据" and event["url"].endswith("/10"))
    ]
    blocked = workflow.mandatory_sentiment_source_audit(incomplete, now=now)
    assert blocked["ok"] is False
    assert "金十数据:valid_count_lt_10" in blocked["reasons"]


def test_structured_a_share_mapping_extracts_canonical_sector_terms():
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_mapping_terms_test")

    terms = workflow._structured_causal_terms(
        "A股映射：医药板块（创新药、AI制药）；通信板块（光通信与光纤产业链）"
    )

    assert "医药" in terms
    assert "通信" in terms


def test_foreign_primary_capture_without_explicit_a_share_link_is_excluded(
    tmp_path,
    monkeypatch,
):
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_foreign_primary_test")
    now = dt.datetime(2026, 8, 23, 15, 0, tzinfo=workflow.CHINA_TZ)
    collected_at = now.isoformat(timespec="seconds")
    foreign_item = {
        "label": "新浪港股",
        "title": "大摩：太古地产维持增持评级",
        "text": "太古地产01972获维持增持评级，看好香港写字楼基本面改善。",
        "href": "https://finance.sina.com.cn/stock/hkstock/hkgg/example.shtml",
        "capturedUrl": "https://feed.mix.sina.com.cn/api/roll/get",
        "time": collected_at,
        "capturedAt": collected_at,
        "source_key": "sina.com.cn",
        "source_url": "https://feed.mix.sina.com.cn/api/roll/get",
        "observation_time_only": False,
        "a_share_mapping": "",
    }

    for file_name in [
        "primary.json",
        *[f"{stem}.json" for stem in workflow.MANDATORY_SENTIMENT_CAPTURE_FILES],
        workflow.BUSINESS_SOCIETY_CAPTURE_FILE,
    ]:
        payload = {
            "channel": (
                "Chrome logged-in visible pages only"
                if file_name == workflow.BUSINESS_SOCIETY_CAPTURE_FILE
                else workflow.PUBLIC_READONLY_FALLBACK_CHANNEL
            ),
            "site": "A股公开主来源" if file_name == "primary.json" else file_name,
            "source_url": "https://example.test/source",
            "collectedAt": collected_at,
            "rawCount": 1 if file_name == "primary.json" else 0,
            "clean": [foreign_item] if file_name == "primary.json" else [],
            "errors": [],
        }
        (tmp_path / file_name).write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )

    monkeypatch.setenv(workflow.CHROME_CAPTURE_ENV, str(tmp_path))
    monkeypatch.setenv(workflow.PUBLIC_READONLY_FALLBACK_ENV, "1")

    events = workflow.collect_chrome_capture_events(now)

    assert not any("太古地产" in item.get("event", "") for item in events)


def test_generic_verb_chuxian_cannot_become_causal_theme_or_cluster():
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_generic_verb_test")
    now = workflow._china_datetime()
    market_date = workflow.cn_date(workflow.recent_trading_dates(now)[-1])
    event_base = {
        "date": workflow.cn_date(now.date()),
        "published_at": now.isoformat(timespec="seconds"),
        "time_precision": "minute",
        "time_evidence": now.isoformat(timespec="minutes"),
        "window_type": workflow.EVENT_WINDOW_TYPE,
        "source_channel": "primary_public_readonly_fallback",
    }
    market_base = {
        "date": market_date,
        "market_date": market_date,
        "published_at": now.isoformat(timespec="seconds"),
        "time_precision": "market_close",
        "time_evidence": market_date,
        "window_type": workflow.MARKET_VALIDATION_WINDOW_TYPE,
    }
    pool = [
        dict(
            event_base,
            source="新浪财经",
            url="https://finance.sina.com.cn/example-1",
            event="供应高峰预计在年内出现，产业需求增长，所属行业为出现。",
        ),
        dict(
            event_base,
            source="交易所公告",
            url="https://www.sse.com.cn/example-2",
            event="新增订单已经出现并改变收入预期，所属环节为出现。",
        ),
        dict(
            market_base,
            source="连板网·市场复盘",
            url="https://lianban.net/example-3",
            event="所属概念为出现，该方向走强并出现涨停扩散。",
        ),
        dict(
            market_base,
            source="融资数据",
            url="local-fund-review",
            event="所属概念为出现，该方向机构融资资金出现净流入。",
        ),
    ]

    assert workflow.causal_label_is_clean("出现") is False
    assert "出现" not in workflow.causal_candidate_terms(pool)
    assert "出现" not in {cluster["name"] for cluster in workflow.cluster_and_score(pool)}


def test_strict_event_pool_filter_uses_one_stable_runtime_anchor():
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_event_anchor_test")
    anchor = dt.datetime(
        2026,
        8,
        13,
        22,
        17,
        3,
        tzinfo=dt.timezone(dt.timedelta(hours=8)),
    )
    cutoff = anchor - dt.timedelta(hours=workflow.EVENT_WINDOW_HOURS)
    common = {
        "source": "雪球",
        "date": workflow.cn_date(cutoff.date()),
        "window_type": workflow.EVENT_WINDOW_TYPE,
        "event": "A股通信板块高热舆情。",
        "url": "https://xueqiu.com/example",
        "heat_evidence": "站内公开热度阅读305886",
        "a_share_mapping": "通信板块",
    }
    events = [
        dict(common, published_at=cutoff.isoformat(timespec="seconds")),
        dict(
            common,
            url="https://xueqiu.com/stale",
            published_at=(cutoff - dt.timedelta(seconds=1)).isoformat(
                timespec="seconds"
            ),
        ),
    ]

    filtered = workflow.filter_current_event_pool(events, now=anchor)

    assert len(filtered) == 1
    assert filtered[0]["url"] == "https://xueqiu.com/example"
    assert all(workflow._is_current_event(item, anchor) for item in filtered)


def test_market_cross_validation_requires_lianban_tdx_and_duanxianxia():
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_market_sources_test")
    now = workflow._china_datetime()
    market_date = workflow.cn_date(workflow.recent_trading_dates(now)[-1])
    common = {
        "date": market_date,
        "market_date": market_date,
        "published_at": now.isoformat(timespec="seconds"),
        "time_precision": "market_close",
        "time_evidence": market_date,
        "window_type": workflow.MARKET_VALIDATION_WINDOW_TYPE,
        "event": f"{market_date}热点、板块、涨停、晋级和成交额验证。",
    }
    events = [
        dict(
            common,
            source="连板网·市场复盘",
            source_channel="lianban_daily_market_cross_validation",
        ),
        dict(
            common,
            source="通达信·市场复盘",
            source_channel="tdx_local_market_cross_validation",
        ),
        dict(
            common,
            source="短线侠·市场复盘",
            source_channel="duanxianxia_market_cross_validation",
        ),
    ]

    audit = workflow.market_cross_validation_audit(events)
    assert audit["ok"] is True
    assert set(audit["present_sources"]) == {"连板网", "通达信", "短线侠"}

    blocked = workflow.market_cross_validation_audit(events[:-1])
    assert blocked["ok"] is False
    assert blocked["missing_sources"] == ["短线侠"]


def test_tdx_market_validation_uses_latest_completed_local_day_intraday(tmp_path):
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_tdx_intraday_test")
    block_root = tmp_path / "blocknew"
    block_root.mkdir()
    block_time = dt.datetime(
        2026,
        8,
        17,
        19,
        41,
        tzinfo=workflow.CHINA_TZ,
    ).timestamp()
    for stem, symbols in (("ZTC", "1600000\n0000001\n"), ("ELB", "1600000\n")):
        path = block_root / f"{stem}.blk"
        path.write_text(symbols, encoding="utf-8")
        os.utime(path, (block_time, block_time))

    turnover = {
        "target_date": "20260817",
        "amount_yuan": 1_530_590_755_827.84,
        "amount_yi": 15_305.91,
        "stock_count": 9_411,
        "newest_mtime": block_time,
    }
    now = dt.datetime(2026, 8, 18, 13, 30, tzinfo=workflow.CHINA_TZ)
    with (
        mock.patch.object(workflow, "TDX_BLOCK_ROOT", block_root),
        mock.patch.object(workflow, "_latest_tdx_turnover", return_value=turnover),
    ):
        events = workflow.collect_tdx_market_validation_events(now)

    assert len(events) == 1
    assert events[0]["time_evidence"] == "2026-08-17"
    assert events[0]["turnover"]["target_date"] == "20260817"


def _write_tdx_block_fixture(block_root, block_time):
    block_root.mkdir()
    for stem, symbols in (("ZTC", "1600000\n0000001\n"), ("ELB", "1600000\n")):
        path = block_root / f"{stem}.blk"
        path.write_text(symbols, encoding="utf-8")
        os.utime(path, (block_time, block_time))


def _write_tdx_day_fixture(workflow, path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"".join(
            workflow.TDX_DAY_RECORD.pack(
                date_value,
                open_value,
                high_value,
                low_value,
                close_value,
                amount,
                volume,
                0,
            )
            for (
                date_value,
                open_value,
                high_value,
                low_value,
                close_value,
                amount,
                volume,
            ) in rows
        )
    )


def _write_tdx_tnf_fixture(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = bytearray(50)
    for code, name in records:
        record = bytearray(360)
        record[:6] = code.encode("ascii")
        encoded_name = name.encode("gbk")[:18]
        record[31 : 31 + len(encoded_name)] = encoded_name
        payload.extend(record)
    path.write_bytes(payload)


def test_tdx_turnover_rebuild_filters_non_a_share_and_derives_latest_pools(tmp_path):
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_tdx_rebuild_test")
    root = tmp_path / "tdx"
    common_rows = [
        (20260820, 900, 900, 900, 900, 50_000_000.0, 1_000),
        (20260821, 990, 990, 990, 990, 80_000_000.0, 1_100),
        (20260824, 1089, 1089, 1089, 1089, 100_000_000.0, 1_200),
    ]
    growth_rows = [
        (20260820, 1000, 1000, 1000, 1000, 40_000_000.0, 900),
        (20260821, 1000, 1000, 1000, 1000, 60_000_000.0, 950),
        (20260824, 1200, 1200, 1200, 1200, 200_000_000.0, 1_500),
    ]
    risk_warning_rows = [
        (20260820, 1000, 1000, 1000, 1000, 20_000_000.0, 500),
        (20260821, 1000, 1000, 1000, 1000, 30_000_000.0, 600),
        (20260824, 1100, 1100, 1100, 1100, 100_000_000.0, 700),
    ]
    index_rows = [
        (20260820, 300000, 300000, 300000, 300000, 900_000_000_000.0, 1),
        (20260821, 310000, 310000, 310000, 310000, 900_000_000_000.0, 1),
        (20260824, 320000, 320000, 320000, 320000, 900_000_000_000.0, 1),
    ]
    _write_tdx_day_fixture(
        workflow,
        root / "vipdoc" / "sh" / "lday" / "sh600000.day",
        common_rows,
    )
    _write_tdx_day_fixture(
        workflow,
        root / "vipdoc" / "sz" / "lday" / "sz300001.day",
        growth_rows,
    )
    _write_tdx_day_fixture(
        workflow,
        root / "vipdoc" / "sh" / "lday" / "sh000001.day",
        index_rows,
    )
    _write_tdx_day_fixture(
        workflow,
        root / "vipdoc" / "sz" / "lday" / "sz001999.day",
        risk_warning_rows,
    )
    _write_tdx_tnf_fixture(
        root / "T0002" / "hq_cache" / "szs.tnf",
        [("001999", "*ST测试")],
    )

    with mock.patch.object(workflow, "TDX_ROOT", root):
        snapshot = workflow._latest_tdx_turnover()

    assert snapshot["target_date"] == "20260824"
    assert snapshot["stock_count"] == 3
    assert snapshot["amount_yi"] == 4.0
    assert snapshot.get("limit_up_count") == 2
    assert snapshot.get("two_day_limit_up_count") == 1
    assert snapshot.get("source_mode") == "tdx_lday_market_rebuild"


def test_tdx_market_validation_rebuilds_from_latest_day_when_blocks_are_stale(tmp_path):
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_tdx_stale_pool_rebuild_test")
    block_root = tmp_path / "blocknew"
    stale_time = dt.datetime(2026, 8, 22, 0, 22, tzinfo=workflow.CHINA_TZ).timestamp()
    _write_tdx_block_fixture(block_root, stale_time)
    turnover = {
        "target_date": "20260824",
        "amount_yuan": 1_696_134_000_000.0,
        "amount_yi": 16_961.34,
        "stock_count": 4_585,
        "newest_mtime": dt.datetime(2026, 8, 24, 20, 18, tzinfo=workflow.CHINA_TZ).timestamp(),
        "limit_up_count": 46,
        "two_day_limit_up_count": 10,
        "source_mode": "tdx_lday_market_rebuild",
        "source_files": ["C:\\new_tdx_mock\\vipdoc\\sh\\lday", "C:\\new_tdx_mock\\vipdoc\\sz\\lday"],
    }
    now = dt.datetime(2026, 8, 25, 1, 30, tzinfo=workflow.CHINA_TZ)
    trading_dates = [
        dt.date(2026, 8, 21),
        dt.date(2026, 8, 24),
        dt.date(2026, 8, 25),
    ]
    with (
        mock.patch.object(workflow, "TDX_BLOCK_ROOT", block_root),
        mock.patch.object(workflow, "_latest_tdx_turnover", return_value=turnover),
        mock.patch.object(workflow, "recent_trading_dates", return_value=trading_dates),
    ):
        events = workflow.collect_tdx_market_validation_events(now)

    assert len(events) == 1
    assert events[0]["time_evidence"] == "2026-08-24"
    assert events[0]["tdx_pool_mode"] == "tdx_lday_market_rebuild"
    assert "涨停46只" in events[0]["event"]
    assert "连续两日涨停10只" in events[0]["event"]
    assert "ZTC" not in events[0]["event"]
    assert "ELB" not in events[0]["event"]


def test_tdx_market_validation_accepts_post_close_weekend_block_refresh(tmp_path):
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_tdx_weekend_refresh_test")
    block_root = tmp_path / "blocknew"
    block_time = dt.datetime(
        2026,
        8,
        22,
        17,
        27,
        tzinfo=workflow.CHINA_TZ,
    ).timestamp()
    _write_tdx_block_fixture(block_root, block_time)
    turnover = {
        "target_date": "20260821",
        "amount_yuan": 1_530_590_755_827.84,
        "amount_yi": 15_305.91,
        "stock_count": 9_411,
        "newest_mtime": block_time,
    }
    now = dt.datetime(2026, 8, 23, 13, 30, tzinfo=workflow.CHINA_TZ)
    trading_dates = [
        dt.date(2026, 8, 19),
        dt.date(2026, 8, 20),
        dt.date(2026, 8, 21),
    ]
    with (
        mock.patch.object(workflow, "TDX_BLOCK_ROOT", block_root),
        mock.patch.object(workflow, "_latest_tdx_turnover", return_value=turnover),
        mock.patch.object(workflow, "recent_trading_dates", return_value=trading_dates),
    ):
        events = workflow.collect_tdx_market_validation_events(now)

    assert len(events) == 1
    assert events[0]["time_evidence"] == "2026-08-21"


def test_tdx_market_validation_rejects_pre_close_block_snapshot(tmp_path):
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_tdx_pre_close_test")
    block_root = tmp_path / "blocknew"
    block_time = dt.datetime(
        2026,
        8,
        21,
        11,
        30,
        tzinfo=workflow.CHINA_TZ,
    ).timestamp()
    _write_tdx_block_fixture(block_root, block_time)
    turnover = {
        "target_date": "20260821",
        "amount_yuan": 1_530_590_755_827.84,
        "amount_yi": 15_305.91,
        "stock_count": 9_411,
        "newest_mtime": block_time,
    }
    now = dt.datetime(2026, 8, 23, 13, 30, tzinfo=workflow.CHINA_TZ)
    trading_dates = [
        dt.date(2026, 8, 19),
        dt.date(2026, 8, 20),
        dt.date(2026, 8, 21),
    ]
    with (
        mock.patch.object(workflow, "TDX_BLOCK_ROOT", block_root),
        mock.patch.object(workflow, "_latest_tdx_turnover", return_value=turnover),
        mock.patch.object(workflow, "recent_trading_dates", return_value=trading_dates),
    ):
        events = workflow.collect_tdx_market_validation_events(now)

    assert events == []


def test_tdx_market_validation_rejects_non_latest_closed_trading_day(tmp_path):
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_tdx_non_latest_test")
    block_root = tmp_path / "blocknew"
    block_time = dt.datetime(
        2026,
        8,
        20,
        16,
        0,
        tzinfo=workflow.CHINA_TZ,
    ).timestamp()
    _write_tdx_block_fixture(block_root, block_time)
    turnover = {
        "target_date": "20260820",
        "amount_yuan": 1_530_590_755_827.84,
        "amount_yi": 15_305.91,
        "stock_count": 9_411,
        "newest_mtime": block_time,
    }
    now = dt.datetime(2026, 8, 23, 13, 30, tzinfo=workflow.CHINA_TZ)
    trading_dates = [
        dt.date(2026, 8, 19),
        dt.date(2026, 8, 20),
        dt.date(2026, 8, 21),
    ]
    with (
        mock.patch.object(workflow, "TDX_BLOCK_ROOT", block_root),
        mock.patch.object(workflow, "_latest_tdx_turnover", return_value=turnover),
        mock.patch.object(workflow, "recent_trading_dates", return_value=trading_dates),
    ):
        events = workflow.collect_tdx_market_validation_events(now)

    assert events == []


def test_intraday_market_width_compares_downside_ratio_across_source_universes():
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_intraday_width_test")
    now = dt.datetime(2026, 8, 18, 14, 36, tzinfo=workflow.CHINA_TZ)
    date_text = workflow.cn_date(now.date())
    pool = [
        {
            "source": "连板网·市场复盘",
            "source_key": "lianban.net",
            "date": date_text,
            "event": "全市场上涨家数1923、下跌家数3220。",
            "url": "https://lianban.net/days/2026-08-18.html",
        },
        {
            "source": "东方财富全A行情逐股涨跌幅延迟节点·市场复盘",
            "source_key": "eastmoney.com",
            "date": date_text,
            "event": "全市场约3111只个股下跌（有效样本4952只）。",
            "url": "https://push2delay.eastmoney.com/api/qt/clist/get",
        },
    ]

    with mock.patch.object(workflow, "_china_datetime", return_value=now):
        width = workflow.parse_width_fact(pool)

    assert width is not None
    assert width["cross_source_mode"] == "downside_approx"
    assert width["source_keys"] == ["eastmoney.com", "lianban.net"]
    assert width["up"] == "1923"
    assert width["down"] == "3220"


def test_premarket_market_width_uses_latest_completed_session():
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_premarket_width_test")
    now = dt.datetime(2026, 8, 25, 1, 30, tzinfo=workflow.CHINA_TZ)
    pool = [
        {
            "source": "连板网",
            "source_key": "lianban.net",
            "date": "8月24日",
            "event": "全市场上涨家数1460、下跌家数3965。",
            "url": "https://lianban.net/days/2026-08-24.html",
        },
        {
            "source": "东方财富全A行情逐股涨跌幅延迟节点",
            "source_key": "eastmoney.com",
            "date": "8月24日",
            "event": "全市场约3965只个股下跌（有效样本5545只）。",
            "url": "https://push2delay.eastmoney.com/api/qt/clist/get",
        },
    ]
    trading_dates = [
        dt.date(2026, 8, 21),
        dt.date(2026, 8, 24),
        dt.date(2026, 8, 25),
    ]

    with (
        mock.patch.object(workflow, "_china_datetime", return_value=now),
        mock.patch.object(workflow, "recent_trading_dates", return_value=trading_dates),
    ):
        width = workflow.parse_width_fact(pool)

    assert width is not None
    assert width["date"] == "8月24日"
    assert width["up"] == "1460"
    assert width["down"] == "3965"
    assert width["cross_source_mode"] == "downside_approx"


def test_report_core_conclusion_contains_explicit_short_term_sentiment(tmp_path):
    workflow = load_module(WORKFLOW_SCRIPT, "sentiment_workflow_short_term_test")
    now = workflow._china_datetime()
    trading_dates = workflow.recent_trading_dates(now)
    trading_day = trading_dates[-1]
    if (
        trading_day == now.date()
        and now.weekday() < 5
        and (now.hour, now.minute) < (9, 30)
    ):
        trading_day = trading_dates[-2]
    date_text = workflow.cn_date(trading_day)
    target_date = trading_day.isoformat()
    pool = []
    clusters = []

    for theme in ("算力", "机器人"):
        events = [
            {
                "source": "财联社",
                "date": date_text,
                "published_at": now.isoformat(timespec="seconds"),
                "time_precision": "minute",
                "time_evidence": now.isoformat(timespec="minutes"),
                "window_type": workflow.EVENT_WINDOW_TYPE,
                "source_channel": workflow.MANDATORY_SENTIMENT_CHANNEL,
                "url": "https://www.cls.cn/example",
                "event": f"{theme}产业需求持续增长，相关企业新增订单并扩大产能。",
                "heat_evidence": "财联社电报高热",
                "a_share_mapping": "直接映射A股产业链。",
            },
            {
                "source": "连板网·市场复盘",
                "date": date_text,
                "market_date": date_text,
                "published_at": now.isoformat(timespec="seconds"),
                "time_precision": "market_close",
                "time_evidence": target_date,
                "window_type": workflow.MARKET_VALIDATION_WINDOW_TYPE,
                "source_channel": "lianban_daily_market_cross_validation",
                "event": f"{date_text}{theme}方向共有4只涨停，板块出现涨停扩散。",
                "url": f"https://lianban.net/days/{target_date}.html",
            },
            {
                "source": "融资数据",
                "date": date_text,
                "market_date": date_text,
                "published_at": now.isoformat(timespec="seconds"),
                "time_precision": "market_close",
                "time_evidence": target_date,
                "window_type": workflow.MARKET_VALIDATION_WINDOW_TYPE,
                "source_channel": "local_participant_topic_aggregation",
                "event": f"{theme}方向机构与融资资金净流入，参与者确认增强。",
                "url": "local-fund-review",
            },
        ]
        pool.extend(events)
        clusters.append(workflow._build_causal_cluster(theme, events))

    pool.extend(
        [
            {
                "source": "东方财富全A行情逐股涨跌幅延迟节点·市场复盘",
                "source_key": "eastmoney.com",
                "date": date_text,
                "published_at": now.isoformat(timespec="seconds"),
                "time_precision": "market_close",
                "time_evidence": target_date,
                "window_type": workflow.MARKET_VALIDATION_WINDOW_TYPE,
                "event": f"{date_text}全市场上涨家数3860、下跌家数1217。",
                "url": "https://push2delay.eastmoney.com/example",
            },
            {
                "source": "新浪财经·市场复盘",
                "source_key": "sina.com.cn",
                "date": date_text,
                "published_at": now.isoformat(timespec="seconds"),
                "time_precision": "market_close",
                "time_evidence": target_date,
                "window_type": workflow.MARKET_VALIDATION_WINDOW_TYPE,
                "event": f"{date_text}全市场约1217只个股下跌。",
                "url": "https://finance.sina.com.cn/example",
            },
        ]
    )

    report = tmp_path / "unified-report.docx"
    workflow.build_report(clusters, report, pool)
    text = "\n".join(paragraph.text for paragraph in Document(report).paragraphs)

    assert "短线情绪判断：" in text
    assert any(
        label in text
        for label in ("强势", "偏强", "中性分化", "偏弱", "退潮")
    )


def test_delivery_closure_requires_eight_site_and_market_cross_validation():
    merged = load_module(MERGED_SCRIPT, "merged_workflow_closure_test")

    closed = {
        "ok": True,
        "mandatory_sentiment_sources": {"ok": True},
        "market_cross_validation": {"ok": True},
        "short_term_sentiment": {"label": "偏强"},
    }
    assert merged.sentiment_delivery_audit_is_closed(closed) is True

    missing_eight_site = dict(
        closed,
        mandatory_sentiment_sources={"ok": False},
    )
    assert merged.sentiment_delivery_audit_is_closed(missing_eight_site) is False

    missing_market_validation = dict(
        closed,
        market_cross_validation={"ok": False},
    )
    assert merged.sentiment_delivery_audit_is_closed(missing_market_validation) is False


def test_skill_contract_has_no_active_independent_social_brief():
    skill_text = TOP_LEVEL_SKILL.read_text(encoding="utf-8")
    workflow_text = TOP_LEVEL_WORKFLOW.read_text(encoding="utf-8")
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))

    assert "唯一业务名称为“A股热点舆情研判”" in skill_text
    assert "每站至少 10 条" in skill_text
    assert "短线情绪判断" in skill_text
    assert "独立三端社媒财经简报" not in skill_text
    assert "市场情报、三端社媒财经简报仅作为兼容路由名称" in workflow_text
    assert manifest["sources"] == ["a-share-sentiment-workflow"]
    assert "social-finance-brief" not in manifest["files"]
    assert not (SOCIAL_COMPONENT / "scripts" / "social_finance_brief.py").exists()


def test_public_fallback_deprecates_social_word_without_old_template_identity():
    fallback = load_module(PUBLIC_FALLBACK_SCRIPT, "public_fallback_deprecation_test")
    result = fallback.collect_and_write_social(Path("unused"))

    assert result["status"] == "BLOCKED"
    assert result["redirect"] == "A股热点舆情研判"
    assert "独立Word" in result["reason"]
    assert result.get("skill") != "三端社媒财经简报"


def test_public_fallback_writes_eight_site_files_and_enforces_ten(tmp_path):
    fallback = load_module(PUBLIC_FALLBACK_SCRIPT, "public_fallback_eight_site_test")
    collected_at = dt.datetime(
        2026,
        8,
        13,
        16,
        30,
        tzinfo=dt.timezone(dt.timedelta(hours=8)),
    )
    site_keys = (
        "tgb",
        "xueqiu",
        "weibo",
        "zhihu",
        "guba",
        "jiuyangongshe",
        "cls",
        "jin10",
    )
    payloads = {
        key: [
            {
                "title": f"{key} A股热点舆情 {index}",
                "url": f"https://example.test/{key}/{index}",
                "hot_value": 10000 - index,
                "text": "A股热点板块、涨停晋级、成交额与短线情绪讨论。",
                "published_at": (
                    collected_at - dt.timedelta(minutes=index)
                ).isoformat(timespec="seconds"),
            }
            for index in range(1, 11)
        ]
        for key in site_keys
    }
    payloads.update(
        {
            "sina": [
                {
                    "title": f"A股主流财经事件 {index}",
                    "url": f"https://example.test/sina/{index}",
                    "intro": "A股市场热点、成交额和风险偏好更新。",
                    "ctime": int(
                        (
                            collected_at - dt.timedelta(minutes=index)
                        ).timestamp()
                    ),
                    "media_name": "新浪财经",
                }
                for index in range(1, 31)
            ],
            "duanxianxia": [],
        }
    )

    manifest = fallback.write_sentiment_capture_bundle(
        tmp_path,
        payloads=payloads,
        breadth_records=[],
        collected_at=collected_at,
    )

    assert manifest["status"] == "PASS"
    assert manifest["missing_sources"] == []
    assert manifest["primary_count"] == 30
    for key in site_keys:
        path = tmp_path / f"{key}.json"
        assert path.is_file()
        capture = json.loads(path.read_text(encoding="utf-8"))
        assert capture["cleanCount"] == 10
        for row in capture["clean"]:
            assert row["heat_evidence"]
            assert row["a_share_mapping"]
            assert row["href"].startswith("https://")
            assert row["observation_time_only"] is False

    payloads["jin10"] = payloads["jin10"][:-1]
    incomplete = fallback.write_sentiment_capture_bundle(
        tmp_path / "incomplete",
        payloads=payloads,
        breadth_records=[],
        collected_at=collected_at,
    )
    assert incomplete["status"] == "BLOCKED"
    assert incomplete["missing_sources"] == ["jin10"]

    no_real_times = {
        key: [
            {
                "title": f"{key} A股热点舆情 {index}",
                "url": f"https://example.test/{key}/observed/{index}",
                "hot_value": 9000 - index,
                "text": "A股热点板块、涨停晋级、成交额与短线情绪讨论。",
            }
            for index in range(1, 11)
        ]
        for key in site_keys
    }
    no_real_times.update(
        {
            "sina": payloads["sina"],
            "duanxianxia": [],
        }
    )
    observed_only = fallback.write_sentiment_capture_bundle(
        tmp_path / "observed-only",
        payloads=no_real_times,
        breadth_records=[],
        collected_at=collected_at,
    )
    assert observed_only["status"] == "BLOCKED"
    assert set(observed_only["missing_sources"]) == set(site_keys)
