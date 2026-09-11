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
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "public_readonly_fallback.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "a_share_public_readonly_fallback_test",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SourceEndpointContractTest(unittest.TestCase):
    def test_zhihu_source_uses_verified_a_share_topic(self):
        module = load_module()

        self.assertEqual(
            module.ZHIHU_STOCK,
            "https://www.zhihu.com/topic/19570359/hot",
        )


class MarketBreadthFallbackTest(unittest.TestCase):
    def test_queries_complete_a_share_scope_including_bse(self):
        module = load_module()
        requested_params = []

        def fake_json_get(_url, *, params, session, timeout):
            requested_params.append(dict(params))
            return {
                "data": {
                    "total": 100,
                    "diff": [
                        {"f12": f"{index:06d}", "f3": 1 if index % 2 else -1}
                        for index in range(3001)
                    ],
                }
            }

        with mock.patch.object(module, "_json_get", side_effect=fake_json_get):
            result = module._eastmoney_market_breadth()

        self.assertEqual(len(requested_params), 1)
        self.assertIn("m:0+t:81+s:2048", requested_params[0]["fs"])
        self.assertEqual(result["valid"], 3001)

    def test_uses_current_intraday_lianban_with_public_quote_corroboration(self):
        module = load_module()
        now = dt.datetime(
            2026,
            8,
            18,
            14,
            30,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            review_dir = Path(temp_dir)
            (review_dir / "market_breadth_20260817.json").write_text(
                '{"up_count": 4334, "down_count": 1064}',
                encoding="utf-8",
            )
            snapshot = review_dir / "lianban-daily.json"
            snapshot.write_text(
                json.dumps(
                    {
                        "status": "CLEAN_PASS",
                        "target_date": "2026-08-18",
                        "sources": {
                            "page": {
                                "url": "https://lianban.net/days/2026-08-18.html"
                            }
                        },
                        "market": {"advancers": 2718, "decliners": 2236},
                    }
                ),
                encoding="utf-8",
            )
            module._latest_review_dir = lambda _now: review_dir
            module._eastmoney_market_breadth = lambda: {
                "up": 2691,
                "down": 2251,
                "flat": 103,
                "valid": 5045,
            }

            previous = os.environ.get("CODEX_LIANBAN_SNAPSHOT")
            os.environ["CODEX_LIANBAN_SNAPSHOT"] = str(snapshot)
            try:
                records = module._breadth_records(now)
            finally:
                if previous is None:
                    os.environ.pop("CODEX_LIANBAN_SNAPSHOT", None)
                else:
                    os.environ["CODEX_LIANBAN_SNAPSHOT"] = previous

        self.assertEqual(
            [row["source_key"] for row in records],
            ["lianban.net", "eastmoney.com"],
        )
        self.assertIn(
            "8月18日全市场上涨家数2718、下跌家数2236",
            records[0]["event"],
        )
        self.assertIn(
            "8月18日全市场约2251只个股下跌",
            records[1]["event"],
        )
        self.assertFalse(any("8月17日" in row["event"] for row in records))

    def test_uses_latest_closed_lianban_before_market_open(self):
        module = load_module()
        now = dt.datetime(
            2026,
            8,
            25,
            1,
            30,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            review_dir = Path(temp_dir)
            (review_dir / "market_breadth_20260824.json").write_text(
                '{"up_count": 1383, "down_count": 3706}',
                encoding="utf-8",
            )
            snapshot = review_dir / "lianban-daily.json"
            snapshot.write_text(
                json.dumps(
                    {
                        "status": "CLEAN_PASS",
                        "target_date": "2026-08-24",
                        "sources": {
                            "page": {
                                "url": "https://lianban.net/days/2026-08-24.html"
                            }
                        },
                        "market": {"advancers": 1460, "decliners": 3965},
                    }
                ),
                encoding="utf-8",
            )
            module._latest_review_dir = lambda _now: review_dir
            module._eastmoney_market_breadth = lambda: {
                "up": 1460,
                "down": 3965,
                "flat": 120,
                "valid": 5545,
            }

            previous = os.environ.get("CODEX_LIANBAN_SNAPSHOT")
            os.environ["CODEX_LIANBAN_SNAPSHOT"] = str(snapshot)
            try:
                records = module._breadth_records(now)
            finally:
                if previous is None:
                    os.environ.pop("CODEX_LIANBAN_SNAPSHOT", None)
                else:
                    os.environ["CODEX_LIANBAN_SNAPSHOT"] = previous

        self.assertEqual(
            [row["source_key"] for row in records],
            ["lianban.net", "eastmoney.com"],
        )
        self.assertIn(
            "8月24日全市场上涨家数1460、下跌家数3965",
            records[0]["event"],
        )
        self.assertIn(
            "8月24日全市场约3965只个股下跌（有效样本5545只）",
            records[1]["event"],
        )
        self.assertEqual(
            {row["market_date"] for row in records},
            {"2026-08-24"},
        )

    def test_adds_runtime_bound_lianban_market_breadth(self):
        module = load_module()
        now = dt.datetime(
            2026,
            8,
            13,
            22,
            0,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot = Path(temp_dir) / "lianban-daily.json"
            snapshot.write_text(
                json.dumps(
                    {
                        "status": "CLEAN_PASS",
                        "target_date": "2026-08-13",
                        "sources": {
                            "page": {
                                "url": "https://lianban.net/days/2026-08-13.html"
                            }
                        },
                        "market": {"advancers": 1142, "decliners": 4317},
                    }
                ),
                encoding="utf-8",
            )
            previous = os.environ.get("CODEX_LIANBAN_SNAPSHOT")
            os.environ["CODEX_LIANBAN_SNAPSHOT"] = str(snapshot)
            try:
                row = module._lianban_market_breadth(now)
            finally:
                if previous is None:
                    os.environ.pop("CODEX_LIANBAN_SNAPSHOT", None)
                else:
                    os.environ["CODEX_LIANBAN_SNAPSHOT"] = previous

        self.assertEqual(row["source_key"], "lianban.net")
        self.assertEqual(row["up"], 1142)
        self.assertEqual(row["down"], 4317)

    def test_uses_current_closed_session_when_same_day_snapshot_is_missing(self):
        module = load_module()
        now = dt.datetime(
            2026,
            8,
            12,
            19,
            0,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            review_dir = Path(temp_dir)
            (review_dir / "market_breadth_20260811.json").write_text(
                '{"up_count": 1615, "down_count": 3777}',
                encoding="utf-8",
            )
            module._latest_review_dir = lambda _now: review_dir
            module._eastmoney_market_breadth = lambda: {
                "up": 3860,
                "down": 1217,
                "flat": 128,
                "valid": 5205,
            }
            module._sina_market_breadth = lambda: {
                "up": 4128,
                "down": 1279,
                "flat": 135,
                "valid": 5542,
            }

            records = module._breadth_records(now)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["source_key"], "eastmoney.com")
        self.assertIn("8月12日全市场上涨家数3860、下跌家数1217", records[0]["event"])
        self.assertEqual(records[1]["source_key"], "sina.com.cn")
        self.assertIn("8月12日全市场约1279只个股下跌", records[1]["event"])

    def test_uses_latest_closed_session_on_weekend_when_snapshot_is_missing(self):
        module = load_module()
        now = dt.datetime(
            2026,
            8,
            23,
            14,
            0,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            review_dir = Path(temp_dir)
            snapshot = review_dir / "lianban-daily.json"
            snapshot.write_text(
                json.dumps(
                    {
                        "status": "CLEAN_PASS",
                        "target_date": "2026-08-21",
                        "sources": {
                            "page": {
                                "url": "https://lianban.net/days/2026-08-21.html"
                            }
                        },
                        "market": {"advancers": 2505, "decliners": 2862},
                    }
                ),
                encoding="utf-8",
            )
            module._latest_review_dir = lambda _now: review_dir
            module._eastmoney_market_breadth = lambda: {
                "up": 2521,
                "down": 2847,
                "flat": 97,
                "valid": 5465,
            }

            previous = os.environ.get("CODEX_LIANBAN_SNAPSHOT")
            os.environ["CODEX_LIANBAN_SNAPSHOT"] = str(snapshot)
            try:
                records = module._breadth_records(now)
            finally:
                if previous is None:
                    os.environ.pop("CODEX_LIANBAN_SNAPSHOT", None)
                else:
                    os.environ["CODEX_LIANBAN_SNAPSHOT"] = previous

        self.assertEqual(
            [row["source_key"] for row in records],
            ["lianban.net", "eastmoney.com"],
        )
        self.assertIn(
            "8月21日全市场上涨家数2505、下跌家数2862",
            records[0]["event"],
        )
        self.assertIn(
            "8月21日全市场约2847只个股下跌",
            records[1]["event"],
        )
        self.assertEqual(
            {row["market_date"] for row in records},
            {"2026-08-21"},
        )

    def test_breadth_capture_uses_market_date_as_time_evidence(self):
        module = load_module()
        collected_at = dt.datetime(
            2026,
            8,
            23,
            14,
            0,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        captured = module._breadth_capture_rows(
            [
                {
                    "source": "连板网",
                    "source_key": "lianban.net",
                    "market_date": "2026-08-21",
                    "event": "8月21日全市场上涨家数2505、下跌家数2862。",
                    "url": "https://lianban.net/days/2026-08-21.html",
                }
            ],
            collected_at,
        )

        self.assertEqual(captured[0]["time"], "2026-08-21")
        self.assertFalse(captured[0]["observation_time_only"])

    def test_builds_current_local_review_snapshot_from_public_sources(self):
        module = load_module()
        now = dt.datetime(
            2026,
            8,
            12,
            19,
            0,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        zt = pd.DataFrame([
            {"代码": "000802", "名称": "北京文化", "所属行业": "影视院线"},
            {"代码": "600721", "名称": "百花医药", "所属行业": "医疗服务"},
        ])
        lhb = pd.DataFrame([
            {"代码": "000802", "名称": "北京文化", "上榜日": "2026-08-12"},
        ])

        class FakeAk:
            @staticmethod
            def stock_zt_pool_em(date):
                self.assertEqual(date, "20260812")
                return zt

            @staticmethod
            def stock_lhb_detail_em(start_date, end_date):
                self.assertEqual((start_date, end_date), ("20260812", "20260812"))
                return lhb

        def fake_fund_flow(item, target_date):
            return {
                "代码": item["代码"],
                "名称": item["名称"],
                "日期": target_date,
                "主力净流入": 100,
                "超大单净流入": 60,
                "主力净占比": 5.0,
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            result = module.ensure_current_local_review(
                now,
                review_root=Path(temp_dir),
                ak_module=FakeAk,
                fund_flow_fetcher=fake_fund_flow,
                minimum_limitup_rows=1,
                minimum_fund_rows=1,
            )
            review_dir = Path(result["review_dir"])
            self.assertTrue(
                (review_dir / "ak_stock_zt_pool_em_20260812.csv").is_file()
            )
            self.assertTrue(
                (review_dir / "ak_stock_lhb_detail_em_20260812.csv").is_file()
            )
            self.assertTrue(
                (review_dir / "push2_fund_flow_resolved_20260812.csv").is_file()
            )
            self.assertEqual(result["status"], "CREATED")


class CurrentTaskPublicSnapshotReuseTest(unittest.TestCase):
    def test_supplements_short_live_zhihu_capture_from_fresh_task_snapshot(self):
        module = load_module()
        now = dt.datetime(
            2026,
            8,
            18,
            14,
            44,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        live_rows = [
            {
                "title": f"A股实时热榜样本{i}",
                "url": f"https://www.zhihu.com/question/live-{i}",
                "text": "A股市场情绪与热点板块讨论。",
                "published_at": now.isoformat(timespec="seconds"),
                "hot_value": f"站内公开热度{i}",
            }
            for i in range(1, 10)
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            snapshot_dir = base / "same-task-capture"
            snapshot_dir.mkdir()
            (snapshot_dir / "zhihu.json").write_text(
                json.dumps(
                    {
                        "schema": "A_SHARE_PUBLIC_READONLY_CAPTURE_V1",
                        "channel": "public_readonly_fallback",
                        "site": "知乎",
                        "source_url": module.ZHIHU_STOCK,
                        "collectedAt": (
                            now - dt.timedelta(minutes=12)
                        ).isoformat(timespec="seconds"),
                        "clean": [
                            {
                                "label": "知乎",
                                "title": "A股同任务热榜补充样本",
                                "text": "A股市场情绪与热点板块讨论。",
                                "href": "https://www.zhihu.com/question/same-task",
                                "capturedUrl": module.ZHIHU_STOCK,
                                "time": now.isoformat(timespec="seconds"),
                                "capturedAt": (
                                    now - dt.timedelta(minutes=12)
                                ).isoformat(timespec="seconds"),
                                "acquisition_mode": "public_readonly_fallback",
                                "source_url": module.ZHIHU_STOCK,
                                "source_key": "zhihu.com",
                                "observation_time_only": False,
                                "rank": 10,
                                "heat_evidence": "站内公开热度10",
                                "a_share_mapping": "A股市场情绪与热点板块",
                                "cookie": "must-not-be-copied",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            out_dir = base / "output"
            with mock.patch.dict(
                os.environ,
                {"CODEX_PUBLIC_READONLY_SNAPSHOT_DIR": str(snapshot_dir)},
                clear=False,
            ):
                module.write_sentiment_capture_bundle(
                    out_dir,
                    payloads={"zhihu": live_rows},
                    breadth_records=[],
                    collected_at=now,
                )

            payload = json.loads((out_dir / "zhihu.json").read_text(encoding="utf-8"))

        self.assertEqual(payload["cleanCount"], 10)
        reused = [row for row in payload["clean"] if row.get("snapshot_reused")]
        self.assertEqual(len(reused), 1)
        self.assertEqual(reused[0]["capturedAt"], now.isoformat(timespec="seconds"))
        self.assertEqual(
            reused[0]["snapshot_collected_at"],
            (now - dt.timedelta(minutes=12)).isoformat(timespec="seconds"),
        )
        self.assertNotIn("cookie", reused[0])


class WindowsLongPathWriteTest(unittest.TestCase):
    def test_sentiment_manifest_uses_extended_path_for_legacy_python(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            padding = "x" * max(1, 234 - len(str(base)) - 1)
            out_dir = base / padding
            out_dir.mkdir(parents=True)
            self.assertLess(len(str(out_dir / "primary.json")), 260)
            self.assertGreaterEqual(
                len(str(out_dir / "public_readonly_fallback_manifest.json")),
                260,
            )

            original_write_text = Path.write_text

            def legacy_windows_write_text(path, *args, **kwargs):
                if len(str(path)) >= 260 and not str(path).startswith("\\\\?\\"):
                    raise FileNotFoundError(str(path))
                return original_write_text(path, *args, **kwargs)

            with mock.patch.object(Path, "write_text", legacy_windows_write_text):
                manifest = module.write_sentiment_capture_bundle(
                    out_dir,
                    payloads={},
                    breadth_records=[],
                    collected_at=dt.datetime.now().astimezone(),
                )

            self.assertEqual(manifest["status"], "BLOCKED")
            manifest_path = out_dir / "public_readonly_fallback_manifest.json"
            extended_manifest_path = Path("\\\\?\\" + str(manifest_path.absolute()))
            try:
                self.assertTrue(extended_manifest_path.is_file())
            finally:
                if extended_manifest_path.is_file():
                    extended_manifest_path.unlink()


class MandatorySiteParserTest(unittest.TestCase):
    def test_mandatory_rows_continue_after_rank_fifty_until_minimum_is_met(self):
        module = load_module()
        collected_at = dt.datetime(
            2026,
            8,
            25,
            1,
            30,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        rows = []
        for index in range(1, 61):
            mapped = index <= 9 or index == 51
            rows.append(
                {
                    "title": (
                        f"美债市场快讯{index}"
                        if mapped
                        else f"一般国际消息{index}"
                    ),
                    "url": f"https://www.jin10.com/flash/{index}",
                    "text": "美债与实际利率变化。" if mapped else "一般事件。",
                    "published_at": collected_at.isoformat(timespec="seconds"),
                    "hot_value": "重要度1" if mapped else "重要度0",
                }
            )
        diagnostics = {}

        captured = module._mandatory_sentiment_rows(
            "jin10",
            rows,
            collected_at,
            diagnostics,
        )

        self.assertEqual(len(captured), 10)
        self.assertEqual(captured[-1]["rank"], 51)
        self.assertEqual(diagnostics["mapping_evaluated"], 51)
        self.assertEqual(diagnostics["not_evaluated_due_limit"], 9)

    def test_rejects_rows_outside_rolling_72_hours_before_counting(self):
        module = load_module()
        collected_at = dt.datetime(
            2026,
            8,
            23,
            12,
            0,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        rows = [
            {
                "title": "A股算力板块当前观察",
                "url": "https://www.cls.cn/detail/current",
                "text": "板块成交额与主力资金同步放大。",
                "published_at": (
                    collected_at - dt.timedelta(hours=72)
                ).isoformat(timespec="seconds"),
                "hot_value": "阅读1000",
            },
            {
                "title": "A股算力板块过期观察",
                "url": "https://www.cls.cn/detail/stale",
                "text": "板块成交额与主力资金同步放大。",
                "published_at": (
                    collected_at - dt.timedelta(hours=72, seconds=1)
                ).isoformat(timespec="seconds"),
                "hot_value": "阅读2000",
            },
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            with mock.patch.dict(os.environ, {}, clear=True):
                module.write_sentiment_capture_bundle(
                    out_dir,
                    payloads={"cls": rows},
                    breadth_records=[],
                    collected_at=collected_at,
                )
            payload = json.loads(
                (out_dir / "cls.json").read_text(encoding="utf-8")
            )

        self.assertEqual(payload["rawCount"], 2)
        self.assertEqual(payload["cleanCount"], 1)
        diagnostics = payload["collectionDiagnostics"]
        self.assertEqual(diagnostics["rejected_by_time_window"], 1)
        self.assertEqual(diagnostics["mapping_evaluated"], 1)
        self.assertEqual(
            diagnostics["time_window_rejections"],
            [
                {
                    "rank": 2,
                    "title": "A股算力板块过期观察",
                    "href": "https://www.cls.cn/detail/stale",
                    "published_at": "2026-08-20T11:59:59+08:00",
                    "reason": "outside_rolling_72_hours",
                }
            ],
        )

    def test_guba_stock_code_context_proves_direct_a_share_mapping(self):
        module = load_module()
        collected_at = dt.datetime(
            2026,
            8,
            23,
            12,
            0,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        parsed = module._parse_guba_posts(
            "002851",
            [
                {
                    "post_id": 1762662543,
                    "post_title": "下周会不会去141",
                    "post_click_count": 3000,
                    "post_comment_count": 48,
                    "post_forward_count": 2,
                    "post_publish_time": "2026-08-22 15:30:00",
                }
            ],
        )

        captured = module._mandatory_sentiment_rows(
            "guba",
            parsed,
            collected_at,
        )

        self.assertEqual(parsed[0]["a_share_context"], "A股股票代码002851")
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]["href"], parsed[0]["url"])
        self.assertIn("A股股票代码002851", captured[0]["text"])

    def test_records_collector_to_final_count_diagnostics(self):
        module = load_module()
        collected_at = dt.datetime(
            2026,
            8,
            23,
            12,
            0,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        rows = [
            {
                "title": "A股算力板块成交额放大",
                "url": "https://www.zhihu.com/question/a-share",
                "text": "上市公司与主力资金同步走强。",
                "published_at": collected_at.isoformat(timespec="seconds"),
                "hot_value": "88 万热度",
            },
            {
                "title": "普通课堂讨论",
                "url": "https://www.zhihu.com/question/classroom",
                "text": "一般教育话题。",
                "published_at": collected_at.isoformat(timespec="seconds"),
                "hot_value": "66 万热度",
            },
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            with mock.patch.dict(os.environ, {}, clear=True):
                module.write_sentiment_capture_bundle(
                    out_dir,
                    payloads={"zhihu": rows},
                    breadth_records=[],
                    collected_at=collected_at,
                )
            payload = json.loads(
                (out_dir / "zhihu.json").read_text(encoding="utf-8")
            )

        self.assertEqual(payload["rawCount"], 2)
        self.assertEqual(payload["cleanCount"], 1)
        diagnostics = payload["collectionDiagnostics"]
        self.assertEqual(diagnostics["collector_returned"], 2)
        self.assertEqual(diagnostics["mapping_evaluated"], 2)
        self.assertEqual(diagnostics["mapping_accepted"], 1)
        self.assertEqual(diagnostics["post_validation_accepted"], 1)
        self.assertEqual(diagnostics["snapshot_supplemented"], 0)
        self.assertEqual(diagnostics["final_accepted"], 1)
        self.assertEqual(diagnostics["rejected_by_mapping"], 1)
        self.assertEqual(diagnostics["rejected_by_post_validation"], 0)
        self.assertEqual(diagnostics["not_evaluated_due_limit"], 0)
        self.assertEqual(
            diagnostics["mapping_rejections"],
            [
                {
                    "rank": 2,
                    "title": "普通课堂讨论",
                    "href": "https://www.zhihu.com/question/classroom",
                    "reason": "no_a_share_mapping",
                }
            ],
        )

    def test_rejects_generic_social_topics_without_a_share_evidence(self):
        module = load_module()
        collected_at = dt.datetime(
            2026,
            8,
            23,
            12,
            0,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        rows = [
            {
                "title": "同样的老师同样的课堂，教育真的能抹平天赋差距吗？",
                "url": "https://www.zhihu.com/question/education",
                "text": "围绕学习方法与个人天赋的一般讨论。",
                "published_at": collected_at.isoformat(timespec="seconds"),
                "hot_value": "101 万热度",
            },
            {
                "title": "A股算力板块订单增长，上市公司披露新签合同",
                "url": "https://www.zhihu.com/question/a-share-compute",
                "text": "板块成交额与主力资金同步放大。",
                "published_at": collected_at.isoformat(timespec="seconds"),
                "hot_value": "88 万热度",
            },
        ]

        captured = module._mandatory_sentiment_rows(
            "zhihu",
            rows,
            collected_at,
        )

        self.assertEqual(module._infer_a_share_mapping(rows[0]["title"]), "")
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]["href"], rows[1]["url"])

    def test_infers_specific_a_share_sector_mapping_from_source_text(self):
        module = load_module()

        self.assertIn(
            "医药",
            module._infer_a_share_mapping(
                "AI制药提升创新药研发效率，拉动生命科学供应链需求"
            ),
        )
        self.assertIn(
            "需求提升",
            module._infer_a_share_mapping(
                "AI制药提升创新药研发效率，拉动生命科学供应链需求"
            ),
        )
        self.assertIn(
            "通信",
            module._infer_a_share_mapping(
                "对进口单模光纤继续征收反倾销税，实施期限为5年"
            ),
        )

    def test_maps_explicit_investment_sector_terms_without_generic_fallback(self):
        module = load_module()
        cases = {
            "满仓黄金股": "黄金",
            "铝企盈利分化与铜价上涨": "有色",
            "火电盈利改善": "电力",
            "白酒库存周期": "消费",
            "脑机接口全栈式解决方案": "脑机接口",
            "医疗器械注册证": "医药",
            "港口REITs盘活存量资产": "基础设施",
            "石油企业面临暴利税": "能源",
            "对美实施对等关税": "外贸",
            "糖肽产业化生产基地": "医药",
            "台风导致国铁广州局部分列车停运": "交通运输",
        }

        for source_text, expected in cases.items():
            with self.subTest(source_text=source_text):
                self.assertIn(
                    expected,
                    module._infer_a_share_mapping(source_text),
                )
        self.assertEqual(module._infer_a_share_mapping("普通课堂讨论"), "")

    def test_tgb_short_term_terms_require_tgb_source_context(self):
        module = load_module()
        source_text = "0821复盘：情绪分歧，观察补跌、买点、仓位与周期出清"

        self.assertEqual(module._infer_a_share_mapping(source_text), "")
        self.assertEqual(
            module._infer_a_share_mapping(source_text, source_key="tgb"),
            "复盘：A股短线交易情绪与风险偏好",
        )
        for live_rejected_title, trigger in (
            ("为什么修复选领涨总是屡试不爽？一位职业交易者的悟道心得", "领涨"),
            ("[红包]8.23：教你如何提前躲避周五药的调整，被套住你应该怎么办？", "被套"),
        ):
            with self.subTest(live_rejected_title=live_rejected_title):
                self.assertEqual(
                    module._infer_a_share_mapping(
                        live_rejected_title,
                        source_key="tgb",
                    ),
                    f"{trigger}：A股短线交易情绪与风险偏好",
                )
        self.assertEqual(
            module._infer_a_share_mapping(
                "三千日夜砺一剑，一营携君踏巅峰",
                source_key="tgb",
            ),
            "",
        )

    def test_parses_weibo_hot_band_with_source_onboard_time_and_heat(self):
        module = load_module()
        fixed_now = dt.datetime(
            2026,
            8,
            13,
            22,
            0,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        payload = {
            "data": {
                "band_list": [
                    {
                        "note": "A股直线跳水原因",
                        "word": "A股直线跳水原因",
                        "category": "财经",
                        "onboard_time": 1786627702,
                        "num": 202219,
                    }
                ]
            }
        }

        with mock.patch.object(module, "_local_now", return_value=fixed_now):
            rows = module._parse_weibo_hot_band(payload)

        self.assertEqual(rows[0]["published_at"], "2026-08-13T21:28:22+08:00")
        self.assertEqual(
            rows[0]["url"],
            "https://s.weibo.com/weibo?q=%23A%E8%82%A1%E7%9B%B4%E7%BA%BF%E8%B7%B3%E6%B0%B4%E5%8E%9F%E5%9B%A0%23",
        )
        self.assertIn("202219", rows[0]["hot_value"])
        self.assertIn("微博话题上榜时间", rows[0]["time_basis"])

    def test_parses_weibo_stock_channel_posts_with_original_time_url_and_heat(self):
        module = load_module()
        fixed_now = dt.datetime(
            2026,
            8,
            25,
            0,
            30,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        payload = {
            "statuses": [
                {
                    "created_at": "Mon Aug 24 21:13:00 +0800 2026",
                    "mblogid": "ReUL6rQAR",
                    "user": {"idstr": "1234567890"},
                    "text": "<p>A股收盘后，主力资金流出名单更新。</p>",
                    "attitudes_count": 34,
                    "comments_count": 19,
                    "reposts_count": 1,
                },
                {
                    "created_at": "Thu Aug 20 21:13:00 +0800 2026",
                    "mblogid": "OldOutsideWindow",
                    "user": {"idstr": "1234567890"},
                    "text": "A股旧帖",
                    "attitudes_count": 100,
                    "comments_count": 20,
                    "reposts_count": 10,
                },
            ]
        }

        with mock.patch.object(module, "_local_now", return_value=fixed_now):
            rows = module._parse_weibo_stock_channel(payload)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["published_at"], "2026-08-24T21:13:00+08:00")
        self.assertEqual(
            rows[0]["url"],
            "https://weibo.com/1234567890/ReUL6rQAR",
        )
        self.assertEqual(rows[0]["text"], "A股收盘后，主力资金流出名单更新。")
        self.assertIn("点赞34", rows[0]["hot_value"])
        self.assertIn("评论19", rows[0]["hot_value"])
        self.assertIn("转发1", rows[0]["hot_value"])

    def test_weibo_collector_prefers_stock_channel_when_it_meets_minimum(self):
        module = load_module()
        stock_rows = [
            {
                "title": f"A股热点{index}",
                "url": f"https://weibo.com/1/post{index}",
                "text": "A股板块与资金情绪",
                "published_at": "2026-08-24T20:00:00+08:00",
                "hot_value": f"点赞{index}",
            }
            for index in range(module.MANDATORY_SITE_MINIMUM)
        ]

        with mock.patch.object(
            module,
            "_weibo_stock_channel",
            return_value=stock_rows,
        ) as stock_channel, mock.patch.object(module.requests, "get") as legacy_get:
            rows = module._weibo_hot_band()

        self.assertEqual(rows, stock_rows)
        stock_channel.assert_called_once()
        legacy_get.assert_not_called()

    def test_parses_zhihu_hot_list_with_question_created_at_and_engagement(self):
        module = load_module()
        payload = {
            "data": [
                {
                    "detail_text": "330 万热度",
                    "target": {
                        "id": 2071189146777773055,
                        "title": "梁文锋打新宇树科技，怎样解读这一布局？",
                        "excerpt": "A股人形机器人第一股宇树科技科创板IPO。",
                        "created": 1786589973,
                        "answer_count": 47,
                        "follower_count": 260,
                    },
                }
            ]
        }

        fixed_now = dt.datetime(
            2026,
            8,
            13,
            12,
            0,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        with mock.patch.object(module, "_local_now", return_value=fixed_now):
            rows = module._parse_zhihu_hot_list(payload)

        self.assertEqual(rows[0]["published_at"], "2026-08-13T10:59:33+08:00")
        self.assertEqual(
            rows[0]["url"],
            "https://www.zhihu.com/question/2071189146777773055",
        )
        self.assertIn("330 万热度", rows[0]["hot_value"])
        self.assertIn("回答47", rows[0]["hot_value"])

    def test_parses_zhihu_recommend_answer_with_original_time_url_and_heat(self):
        module = load_module()
        fixed_now = dt.datetime(
            2026,
            8,
            25,
            1,
            30,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        created = int((fixed_now - dt.timedelta(hours=2)).timestamp())
        payload = {
            "data": [
                {
                    "target": {
                        "type": "answer",
                        "id": 2074432031237345945,
                        "created_time": created,
                        "updated_time": created + 300,
                        "voteup_count": 91,
                        "comment_count": 11,
                        "visited_count": 16783,
                        "excerpt": "国产游戏与数字内容产业链热度继续提升。",
                        "question": {
                            "id": 2073807705089762450,
                            "title": "《黑神话：钟馗》发布，为什么热度这么高？",
                        },
                    }
                }
            ]
        }

        with mock.patch.object(module, "_local_now", return_value=fixed_now):
            rows = module._parse_zhihu_recommend_payload(payload)

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]["url"],
            "https://www.zhihu.com/question/2073807705089762450/answer/2074432031237345945",
        )
        self.assertEqual(
            rows[0]["published_at"],
            (fixed_now - dt.timedelta(hours=2)).isoformat(timespec="seconds"),
        )
        self.assertIn("赞同91", rows[0]["hot_value"])
        self.assertIn("评论11", rows[0]["hot_value"])
        self.assertIn("浏览16783", rows[0]["hot_value"])
        self.assertIn("回答创建时间", rows[0]["time_basis"])

    def test_zhihu_collector_paginates_official_recommendations_until_ten_rows(self):
        module = load_module()
        fixed_now = dt.datetime(
            2026,
            8,
            25,
            1,
            30,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        created = int((fixed_now - dt.timedelta(hours=1)).timestamp())
        hot_payload = {
            "data": [
                {
                    "detail_text": f"热度{index}",
                    "target": {
                        "id": 2075000000000000000 + index,
                        "title": f"A股热点样本{index}",
                        "excerpt": "A股市场与板块情绪。",
                        "created": created,
                        "answer_count": index,
                        "follower_count": index + 10,
                    },
                }
                for index in range(1, 10)
            ]
        }
        first_recommend = {
            "data": [
                {
                    "target": {
                        "type": "answer",
                        "id": 1001,
                        "created_time": created,
                        "voteup_count": 5,
                        "comment_count": 1,
                        "visited_count": 30,
                        "excerpt": "普通生活讨论。",
                        "question": {"id": 2001, "title": "普通生活问题"},
                    }
                }
            ],
            "paging": {"is_end": False, "next": "https://api.zhihu.com/page-2"},
        }
        second_recommend = {
            "data": [
                {
                    "target": {
                        "type": "answer",
                        "id": 1002,
                        "created_time": created,
                        "voteup_count": 91,
                        "comment_count": 11,
                        "visited_count": 16783,
                        "excerpt": "国产游戏与数字内容产业链热度继续提升。",
                        "question": {
                            "id": 2002,
                            "title": "《黑神话：钟馗》发布，为什么热度这么高？",
                        },
                    }
                }
            ],
            "paging": {"is_end": True, "next": ""},
        }

        class FakeResponse:
            def __init__(self, payload):
                self._payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self._payload

        requested_urls = []

        def fake_get(url, **_kwargs):
            requested_urls.append(url)
            if url == module.ZHIHU_HOT_LIST:
                return FakeResponse(hot_payload)
            if url == module.ZHIHU_RECOMMEND:
                return FakeResponse(first_recommend)
            if url == "https://api.zhihu.com/page-2":
                return FakeResponse(second_recommend)
            self.fail(f"unexpected URL: {url}")

        with mock.patch.object(module, "_local_now", return_value=fixed_now), mock.patch.object(
            module.requests,
            "get",
            side_effect=fake_get,
        ):
            rows = module._zhihu_hot_list(limit=50)

        self.assertEqual(len(rows), 10)
        self.assertEqual(
            requested_urls,
            [
                module.ZHIHU_HOT_LIST,
                module.ZHIHU_RECOMMEND,
                "https://api.zhihu.com/page-2",
            ],
        )
        self.assertTrue(rows[-1]["url"].endswith("/question/2002/answer/1002"))

    def test_zhihu_collector_counts_only_final_a_share_mappings_before_stopping(self):
        module = load_module()
        fixed_now = dt.datetime(
            2026,
            8,
            25,
            1,
            30,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        created = int((fixed_now - dt.timedelta(hours=1)).timestamp())
        hot_rows = [
            {
                "detail_text": f"热度{index}",
                "target": {
                    "id": 2076000000000000000 + index,
                    "title": f"A股热点样本{index}",
                    "excerpt": "A股市场与板块情绪。",
                    "created": created,
                    "answer_count": index,
                    "follower_count": index + 10,
                },
            }
            for index in range(1, 10)
        ]
        hot_rows.append(
            {
                "detail_text": "80 万热度",
                "target": {
                    "id": 2076999999999999999,
                    "title": "大学商业管理课程应该如何选择？",
                    "excerpt": "围绕课程设置的一般教育讨论。",
                    "created": created,
                    "answer_count": 20,
                    "follower_count": 30,
                },
            }
        )
        recommend_payload = {
            "data": [
                {
                    "target": {
                        "type": "answer",
                        "id": 3001,
                        "created_time": created,
                        "voteup_count": 91,
                        "comment_count": 11,
                        "visited_count": 16783,
                        "excerpt": "国产游戏与数字内容产业链热度继续提升。",
                        "question": {
                            "id": 4001,
                            "title": "《黑神话：钟馗》发布，为什么热度这么高？",
                        },
                    }
                }
            ],
            "paging": {"is_end": True, "next": ""},
        }

        class FakeResponse:
            def __init__(self, payload):
                self._payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self._payload

        def fake_get(url, **_kwargs):
            if url == module.ZHIHU_HOT_LIST:
                return FakeResponse({"data": hot_rows})
            if url == module.ZHIHU_RECOMMEND:
                return FakeResponse(recommend_payload)
            self.fail(f"unexpected URL: {url}")

        with mock.patch.object(module, "_local_now", return_value=fixed_now), mock.patch.object(
            module.requests,
            "get",
            side_effect=fake_get,
        ):
            rows = module._zhihu_hot_list(limit=50)

        self.assertEqual(len(rows), 10)
        self.assertTrue(rows[-1]["url"].endswith("/question/4001/answer/3001"))
        self.assertTrue(
            all(
                module._infer_a_share_mapping(
                    f"{row['title']} {row['text']}",
                    source_key="zhihu",
                )
                for row in rows
            )
        )

    def test_zhihu_current_hot_industry_topics_keep_direct_a_share_mapping(self):
        module = load_module()
        fixed_now = dt.datetime(
            2026,
            8,
            25,
            0,
            30,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        cases = (
            (
                "索尼重申数字游戏仅授权使用，账号封禁后游戏库清零",
                "PlayStation数字游戏商业模式引发讨论。",
                "游戏",
            ),
            (
                "热门赛事影院直播上座率超过85%，影院为何不加场",
                "影院排片与票房增量成为焦点。",
                "影视",
            ),
            (
                "如何解读美债规模突破40万亿美元",
                "美债与实际利率变化影响黄金资产定价。",
                "黄金",
            ),
        )
        payload = {"data": []}
        for index, (title, excerpt, _expected) in enumerate(cases, 1):
            payload["data"].append(
                {
                    "detail_text": f"{200 - index} 万热度",
                    "target": {
                        "id": 2075000000000000000 + index,
                        "title": title,
                        "excerpt": excerpt,
                        "created": int(
                            (fixed_now - dt.timedelta(hours=index)).timestamp()
                        ),
                        "answer_count": 30 + index,
                        "follower_count": 100 + index,
                    },
                }
            )

        with mock.patch.object(module, "_local_now", return_value=fixed_now):
            rows = module._parse_zhihu_hot_list(payload)
        captured = module._mandatory_sentiment_rows("zhihu", rows, fixed_now)

        self.assertEqual(len(rows), 3)
        self.assertEqual(len(captured), 3)
        for row, (_title, _excerpt, expected) in zip(captured, cases):
            self.assertIn(expected, row["a_share_mapping"])

    def test_maps_current_zhihu_enterprise_rumor_case_to_listed_company_risk(self):
        module = load_module()
        fixed_now = dt.datetime(
            2026,
            8,
            18,
            13,
            30,
            tzinfo=dt.timezone(dt.timedelta(hours=8)),
        )
        title = "公安部网安局公布 14 起涉企网络谣言案例，对企业会造成哪些影响，又该如何防范？"
        excerpt = "涉企网络谣言会损害企业品牌、经营秩序与市场信心。"
        payload = {
            "data": [
                {
                    "detail_text": "109 万热度",
                    "target": {
                        "id": 2072971742117622259,
                        "title": title,
                        "excerpt": excerpt,
                        "created": int(
                            (
                                fixed_now - dt.timedelta(hours=4)
                            ).timestamp()
                        ),
                        "answer_count": 23,
                        "follower_count": 91,
                    },
                }
            ]
        }

        with mock.patch.object(module, "_local_now", return_value=fixed_now):
            rows = module._parse_zhihu_hot_list(payload)

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            module._infer_a_share_mapping(f"{title} {excerpt}"),
            "涉企网络谣言：上市公司舆情与企业经营风险",
        )

    def test_zhihu_maps_rideshare_safety_to_mobility_platform_governance(self):
        module = load_module()
        fixed_now = dt.datetime(
            2026, 8, 18, 14, 0, tzinfo=dt.timezone(dt.timedelta(hours=8))
        )
        title = "顺风车司机中途离车失联，暴露出顺风车服务哪些问题？"
        excerpt = "女孩被滞留在车内，事件涉及出行平台安全责任与服务治理。"
        payload = {
            "data": [
                {
                    "detail_text": "65 万热度",
                    "target": {
                        "id": 2072760692617077687,
                        "title": title,
                        "excerpt": excerpt,
                        "created": int((fixed_now - dt.timedelta(hours=19)).timestamp()),
                        "answer_count": 31,
                        "follower_count": 57,
                    },
                }
            ]
        }

        with mock.patch.object(module, "_local_now", return_value=fixed_now):
            rows = module._parse_zhihu_hot_list(payload)

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            module._infer_a_share_mapping(f"{title} {excerpt}"),
            "顺风车：汽车出行服务与平台治理",
        )

    def test_parses_tgb_mobile_rows_with_original_publication_time_and_heat(self):
        module = load_module()
        home_html = """
        <div class="index-content-lists" data-topicID="8648358">
          <div class="listscontent-tittle"><a href="/a/2ue9CjU3yPT">神灯实盘：差点绿了</a></div>
          <div class="listscontent-zaiyao">A股短线复盘与涨停情绪观察。</div>
          <div class="listscontent-data"><span>2.2</span>万 阅读 · <span>75</span>评论 · <span>08-13</span></div>
        </div>
        """
        detail_html = """
        <html><body>神灯实盘：差点绿了 26-08-13 15:22 24313 次浏览</body></html>
        """

        seeds = module._parse_tgb_mobile_home(home_html)
        rows = module._parse_tgb_mobile_details(
            seeds,
            lambda _url: detail_html,
        )

        self.assertEqual(rows[0]["published_at"], "2026-08-13 15:22:00")
        self.assertEqual(rows[0]["url"], "https://m.tgb.cn/a/2ue9CjU3yPT")
        self.assertIn("24313", rows[0]["hot_value"])
        self.assertIn("75", rows[0]["hot_value"])

    def test_parses_xueqiu_timeline_posts_with_created_at_and_interactions(self):
        module = load_module()
        payload = {
            "list": [
                {
                    "data": json.dumps(
                        {
                            "id": 404902709,
                            "title": "A股算力产业链订单观察",
                            "description": "订单与业绩映射。",
                            "target": "/6254064333/404902709",
                            "reply_count": 32,
                            "retweet_count": 3,
                            "view_count": 59694,
                            "like_count": 220,
                            "created_at": 1786605850000,
                        },
                        ensure_ascii=False,
                    )
                }
            ]
        }

        rows = module._parse_xueqiu_timeline(payload)

        self.assertEqual(rows[0]["published_at"], "2026-08-13T15:24:10+08:00")
        self.assertEqual(rows[0]["url"], "https://xueqiu.com/6254064333/404902709")
        self.assertIn("59694", rows[0]["hot_value"])
        self.assertIn("220", rows[0]["hot_value"])

    def test_parses_guba_posts_with_publish_time_and_interactions(self):
        module = load_module()
        posts = [
            {
                "post_id": 1758738147,
                "post_title": "中芯国际Q2净利增长超142%",
                "post_click_count": 8289,
                "post_forward_count": 85,
                "post_comment_count": 33,
                "post_publish_time": "2026-08-13 17:14:00",
            }
        ]

        rows = module._parse_guba_posts("688981", posts)

        self.assertEqual(rows[0]["published_at"], "2026-08-13 17:14:00")
        self.assertEqual(
            rows[0]["url"],
            "https://guba.eastmoney.com/news,688981,1758738147.html",
        )
        self.assertIn("8289", rows[0]["hot_value"])
        self.assertIn("33", rows[0]["hot_value"])

    def test_parses_jiuyangongshe_embedded_rows(self):
        module = load_module()
        html = """
        article_id:"3y5c8ddspkm",title:"A股AI数据中心网络设备产业链",
        comment_count:12,collect_count:23,like_count:34,forward_count:5,
        create_time:"2026-08-13 18:07:27",new_interaction_time:"2026-08-13 19:36:10",
        content:"订单先行、业绩逐步兑现。"
        """

        rows = module._parse_jiuyangongshe_html(html)

        self.assertEqual(rows[0]["published_at"], "2026-08-13 18:07:27")
        self.assertEqual(
            rows[0]["url"],
            "https://www.jiuyangongshe.com/a/3y5c8ddspkm",
        )
        self.assertIn("评论12", rows[0]["hot_value"])
        self.assertIn("收藏23", rows[0]["hot_value"])

    def test_parses_cls_telegraph_rows(self):
        module = load_module()
        payload = {
            "errno": 0,
            "data": {
                "roll_data": [
                    {
                        "id": 2453708,
                        "title": "国内铁矿项目开发专题座谈会召开",
                        "brief": "提升国内铁矿资源保障能力。",
                        "ctime": 1786620531,
                        "reading_num": 23516,
                        "comment_num": 2,
                        "share_num": 6,
                        "subjects": [{"subject_name": "钢铁"}],
                    }
                ]
            },
        }

        rows = module._parse_cls_payload(payload)

        self.assertEqual(rows[0]["published_at"], "2026-08-13T19:28:51+08:00")
        self.assertEqual(rows[0]["url"], "https://www.cls.cn/detail/2453708")
        self.assertIn("23516", rows[0]["hot_value"])
        self.assertIn("钢铁", rows[0]["text"])

    def test_cls_telegraph_uses_public_roll_list_when_cache_is_short(self):
        module = load_module()

        def payload(count):
            return {
                "errno": 0,
                "data": {
                    "roll_data": [
                        {
                            "id": 2453700 + index,
                            "title": f"A股盘面快讯{index}",
                            "brief": "当前市场热点与板块异动。",
                            "ctime": 1786620531 + index,
                        }
                        for index in range(count)
                    ]
                },
            }

        def request_payload(url, **_kwargs):
            if url == module.CLS_TELEGRAPH_CACHE:
                return payload(8)
            if url == "https://www.cls.cn/v1/roll/get_roll_list":
                self.assertEqual(
                    _kwargs["params"]["last_time"],
                    1786620531 + 7,
                )
                return payload(12)
            self.fail(f"unexpected URL: {url}")

        with mock.patch.object(
            module, "_json_get", side_effect=request_payload
        ) as request:
            rows = module._cls_telegraph()

        self.assertEqual(len(rows), 12)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(
            request.call_args_list[1].args[0],
            "https://www.cls.cn/v1/roll/get_roll_list",
        )

    def test_cls_roll_request_uses_official_double_hash_signature(self):
        module = load_module()
        cache_payload = {
            "errno": 0,
            "data": {
                "roll_data": [
                    {
                        "id": 2461516,
                        "title": "A股盘面快讯",
                        "brief": "当前市场热点与板块异动。",
                        "ctime": 1787443928,
                    }
                ]
            },
        }
        roll_payload = {
            "errno": 0,
            "data": {
                "roll_data": [
                    {
                        "id": 2461515 - index,
                        "title": f"A股分页快讯{index}",
                        "brief": "当前市场热点与板块异动。",
                        "ctime": 1787443900 - index,
                    }
                    for index in range(20)
                ]
            },
        }

        with mock.patch.object(
            module,
            "_json_get",
            side_effect=[cache_payload, roll_payload],
        ) as request:
            module._cls_telegraph(limit=21)

        self.assertEqual(
            request.call_args_list[1].kwargs["params"],
            {
                "app": "CailianpressWeb",
                "last_time": 1787443928,
                "os": "web",
                "refresh_type": 1,
                "rn": 20,
                "sv": "8.7.9",
                "sign": "509b6da86735573b2fd2b432d66f01ff",
            },
        )

    def test_cls_telegraph_paginates_even_when_raw_cache_exceeds_minimum(self):
        module = load_module()

        def payload(start, count):
            return {
                "errno": 0,
                "data": {
                    "roll_data": [
                        {
                            "id": start + index,
                            "title": f"财经快讯{start + index}",
                            "brief": "A股行业动态。",
                            "ctime": 1787460000 - start - index,
                        }
                        for index in range(count)
                    ]
                },
            }

        cache = payload(1000, 18)
        roll = payload(2000, 20)
        with mock.patch.object(
            module,
            "_json_get",
            side_effect=[cache, roll],
        ) as request:
            rows = module._cls_telegraph(limit=30)

        self.assertEqual(len(rows), 30)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(
            request.call_args_list[1].args[0],
            module.CLS_TELEGRAPH_ROLL,
        )

    def test_cls_telegraph_continues_after_a_short_nonempty_page(self):
        module = load_module()

        def payload(start_id, newest_time, count):
            return {
                "errno": 0,
                "data": {
                    "roll_data": [
                        {
                            "id": start_id + index,
                            "title": f"A股分页快讯{start_id + index}",
                            "brief": "当前市场热点与板块异动。",
                            "ctime": newest_time - index,
                        }
                        for index in range(count)
                    ]
                },
            }

        cache = payload(1000, 3000, 18)
        short_page = payload(2000, 2900, 2)
        next_page = payload(3000, 2800, 10)
        with mock.patch.object(
            module,
            "_json_get",
            side_effect=[cache, short_page, next_page],
        ) as request:
            rows = module._cls_telegraph(limit=30)

        self.assertEqual(len(rows), 30)
        self.assertEqual(request.call_count, 3)

    def test_parses_jin10_flash_rows(self):
        module = load_module()
        payload = {
            "status": 200,
            "data": [
                {
                    "id": "20260813193256856800",
                    "time": "2026-08-13 19:32:56",
                    "important": 1,
                    "data": {
                        "title": "",
                        "content": "A股存储芯片产业链出现新催化。",
                    },
                    "remark": ["重要"],
                }
            ],
        }

        rows = module._parse_jin10_payload(payload)

        self.assertEqual(rows[0]["published_at"], "2026-08-13 19:32:56")
        self.assertEqual(
            rows[0]["url"],
            "https://www.jin10.com/flash/20260813193256856800",
        )
        self.assertIn("重要度1", rows[0]["hot_value"])

    def test_jin10_flash_paginates_with_oldest_publication_cursor(self):
        module = load_module()

        def item(item_id, published_at):
            return {
                "id": item_id,
                "time": published_at,
                "important": 1,
                "data": {"content": f"A股行业快讯{item_id}"},
                "remark": [],
            }

        pages = {
            "": [
                item("20260823120000000001", "2026-08-23 12:00:00"),
                item("20260823115900000002", "2026-08-23 11:59:00"),
            ],
            "2026-08-23 11:59:00": [
                item("20260823115800000003", "2026-08-23 11:58:00")
            ],
            "2026-08-23 11:58:00": [],
        }

        class FakeResponse:
            def __init__(self, payload):
                self._payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return {"status": 200, "data": self._payload}

        requested_cursors = []

        def fake_get(_url, *, params, **_kwargs):
            cursor = params["max_time"]
            requested_cursors.append(cursor)
            return FakeResponse(pages[cursor])

        with mock.patch.object(module.requests, "get", side_effect=fake_get):
            rows = module._jin10_flash(limit=5)

        self.assertEqual(len(rows), 3)
        self.assertEqual(
            requested_cursors,
            ["", "2026-08-23 11:59:00", "2026-08-23 11:58:00"],
        )


if __name__ == "__main__":
    unittest.main()
