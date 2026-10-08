#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import ast
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT.parents[1]
CLIENT_PATH = HOME / "scripts" / "lianban_daily_client.py"
RUNTIME_PATH = HOME / "scripts" / "stock_canonical_runtime.py"
CONTRACTS_PATH = ROOT / "references" / "stock_execution_contracts.json"

EXPECTED_QUERY_SKILLS = {
    "a-share-longhubang-analysis",
    "a-share-short-term-market-sentiment",
    "big-bull-analysis-scoring-system",
    "core-mainline-scoring-system",
    "a-share-bottom-fishing",
    "convertible-bond-screening-strategy",
    "buzhang-leader-mining",
    "chanlun-first-board",
    "dragon-pullback",
    "feilong-strategy",
    "five-dimension-resonance",
    "nana-teacher-five-strategies",
    "oversold-first-board",
    "quality-track-stock-selection",
    "quant-strategy-bundle-chen",
    "quantitative-trading",
    "shortline-hotspot-mining",
    "a-share-leader-deep-research",
    "a-share-limit-up-leader-classification",
    "a-share-limit-up-mining",
    "limit-up-review",
    "baimao-score-system",
    "financial-roe-analysis",
    "stock-analysis",
    "stock-research-engine",
    "stock-study",
    "stock-research-codex",
    "support-pressure-analysis-system",
    "risk-mine-clearance",
    "stock-watchlist",
    "baimao-teacher-system",
    "jigou-capital-monitoring",
    "youzi-capital-monitoring",
    "kaipanla",
    "a-share-hotspot-sentiment-analysis",
    "a-share-thinktank-brief",
    "baimao-daily-intel-review",
    "industry-chain-analysis",
    "old-leader-oversold-rebound",
}
REQUIRED_QUERY_SKILLS = {"a-share-short-term-market-sentiment"}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module_load_failed:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LianbanDailyClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = load_module(CLIENT_PATH, "lianban_daily_client_test")

    def test_build_urls_uses_requested_trading_date(self) -> None:
        urls = self.client.build_urls("2026-08-12", latest=False)
        self.assertEqual(
            urls["page"],
            "https://lianban.net/days/2026-08-12.html",
        )
        self.assertEqual(
            urls["open_data"],
            "https://lianban.net/opendata/2026-08-12.json",
        )

    def test_parse_open_data_normalizes_market_kpis_and_topics(self) -> None:
        payload = {
            "date": "2026-08-12",
            "zt": 92,
            "dt": 0,
            "lb": 16,
            "height": 7,
            "rate": 88.5,
            "zb": 12,
            "up": 4128,
            "down": 1280,
            "emotion": "高潮期",
            "plates": [
                {"name": "地产链", "count": 10},
                {"name": "算力", "count": 9},
            ],
        }
        normalized = self.client.normalize_open_data(payload)
        self.assertEqual(normalized["market"]["limit_up"], 92)
        self.assertEqual(normalized["market"]["limit_down"], 0)
        self.assertEqual(normalized["market"]["consecutive"], 16)
        self.assertEqual(normalized["market"]["max_board"], 7)
        self.assertEqual(normalized["market"]["seal_rate"], 88.5)
        self.assertEqual(normalized["market"]["broken_board"], 12)
        self.assertEqual(normalized["market"]["advancers"], 4128)
        self.assertEqual(normalized["market"]["decliners"], 1280)
        self.assertEqual(normalized["market"]["emotion_stage"], "高潮期")
        self.assertEqual(normalized["topics"][0], {"name": "地产链", "count": 10})

    def test_parse_html_extracts_title_and_stock_event_details(self) -> None:
        html = """
        <html><head><title>2026年8月12日涨停复盘 - 连板网</title></head>
        <body>
          <a href="/stock/600000.html">浦发银行</a>
          <div>事件催化：金融政策发布，板块出现异动。</div>
          <script>window.__DATA__={"code":"000001","name":"平安银行","reason":"公告利好"};</script>
        </body></html>
        """
        details = self.client.parse_html_details(html)
        self.assertEqual(details["title"], "2026年8月12日涨停复盘 - 连板网")
        self.assertIn("600000", details["stock_codes"])
        self.assertIn("000001", details["stock_codes"])
        self.assertTrue(any("金融政策发布" in item for item in details["event_texts"]))
        self.assertTrue(any(item.get("name") == "平安银行" for item in details["stock_items"]))

    def test_nested_canonical_run_reuses_current_task_clean_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "parent-lianban-daily.json"
            source.write_text(
                json.dumps({
                    "schema": "LIANBAN_DAILY_SNAPSHOT_V1",
                    "status": "CLEAN_PASS",
                    "requested_at": "2026-08-17T22:33:56+08:00",
                    "requested_date": "2026-08-17",
                    "target_date": "2026-08-17",
                    "latest_requested": False,
                    "sources": {
                        "page": {
                            "url": "https://lianban.net/days/2026-08-17.html",
                            "status_code": 200,
                        },
                        "open_data": {
                            "url": "https://lianban.net/opendata/2026-08-17.json",
                            "status_code": 200,
                        },
                    },
                    "market": {"limit_up": 106},
                    "topics": [],
                    "page_details": {"stock_items": [{"code": "600000"}]},
                    "errors": [],
                }),
                encoding="utf-8",
            )
            environment = {
                "ONESTOCK_STOCK_CANONICAL_CHILD": "1",
                "CODEX_LIANBAN_STATUS": "CLEAN_PASS",
                "CODEX_LIANBAN_SNAPSHOT": str(source),
                "CODEX_LIANBAN_SOURCE_URL": "https://lianban.net/days/2026-08-17.html",
                "CODEX_LIANBAN_OPEN_DATA_URL": "https://lianban.net/opendata/2026-08-17.json",
                "CODEX_LIANBAN_ATTRIBUTION": "连板网",
            }

            with mock.patch.dict(os.environ, environment, clear=False), mock.patch.object(
                self.client.requests,
                "get",
                side_effect=AssertionError("nested run must not refetch the same page"),
            ):
                payload = self.client.collect_snapshot(
                    "2026-08-17",
                    latest=True,
                )

            self.assertEqual(payload["status"], "CLEAN_PASS")
            self.assertEqual(payload["target_date"], "2026-08-17")
            self.assertEqual(
                payload["reuse"]["mode"],
                "current_task_inherited_snapshot",
            )
            self.assertEqual(Path(payload["reuse"]["source_path"]), source.resolve())

    def test_current_task_latest_snapshot_reuses_when_request_day_is_not_trading_day(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "parent-lianban-daily.json"
            source.write_text(
                json.dumps({
                    "schema": "LIANBAN_DAILY_SNAPSHOT_V1",
                    "status": "CLEAN_PASS",
                    "requested_at": "2026-08-18T06:19:12+08:00",
                    "requested_date": "2026-08-18",
                    "target_date": "2026-08-17",
                    "latest_requested": True,
                    "sources": {
                        "page": {"url": "https://lianban.net/days/2026-08-17.html", "status_code": 200},
                        "open_data": {"url": "https://lianban.net/opendata/latest.json", "status_code": 200},
                    },
                    "page_details": {"stock_items": [{"code": "600000"}]},
                    "errors": [],
                }),
                encoding="utf-8",
            )
            environment = {
                "ONESTOCK_STOCK_CANONICAL_CHILD": "1",
                "CODEX_LIANBAN_STATUS": "CLEAN_PASS",
                "CODEX_LIANBAN_SNAPSHOT": str(source),
                "CODEX_LIANBAN_SOURCE_URL": "https://lianban.net/days/2026-08-17.html",
                "CODEX_LIANBAN_OPEN_DATA_URL": "https://lianban.net/opendata/latest.json",
                "CODEX_LIANBAN_ATTRIBUTION": "连板网",
            }

            with mock.patch.dict(os.environ, environment, clear=False), mock.patch.object(
                self.client.requests,
                "get",
                side_effect=AssertionError("current-task latest snapshot must be reused"),
            ):
                payload = self.client.collect_snapshot("2026-08-18", latest=False)

            self.assertEqual(payload["target_date"], "2026-08-17")
            self.assertEqual(payload["reuse"]["mode"], "current_task_inherited_snapshot")


class LianbanContractIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = load_module(RUNTIME_PATH, "stock_canonical_runtime_lianban_test")

    def test_all_news_sentiment_event_query_contracts_enable_lianban(self) -> None:
        payload = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))
        contracts = {row["skill_id"]: row for row in payload["contracts"]}
        enabled = {
            skill_id
            for skill_id, row in contracts.items()
            if row.get("supplemental_sources", {}).get("lianban_daily", {}).get("enabled")
        }
        self.assertEqual(enabled, EXPECTED_QUERY_SKILLS)
        for skill_id in enabled:
            source = contracts[skill_id]["supplemental_sources"]["lianban_daily"]
            self.assertEqual(source["required"], skill_id in REQUIRED_QUERY_SKILLS)
            self.assertEqual(Path(source["client"]), CLIENT_PATH)

    def test_lianban_enabled_skills_delegate_public_entry_to_runtime(self) -> None:
        payload = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))
        enabled = [
            row["skill_id"]
            for row in payload["contracts"]
            if row.get("supplemental_sources", {})
            .get("lianban_daily", {})
            .get("enabled")
        ]

        for skill_id in enabled:
            with self.subTest(skill_id=skill_id):
                entry = HOME / "skills" / skill_id / "scripts" / "codex_entry.py"
                source = entry.read_text(encoding="utf-8-sig")
                tree = ast.parse(source)
                self.assertIn("from stock_canonical_runtime import facade_main", source)
                facade_calls = [
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "facade_main"
                    and len(node.args) == 1
                    and isinstance(node.args[0], ast.Name)
                    and node.args[0].id == "__file__"
                ]
                system_exit_calls = [
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "SystemExit"
                ]
                self.assertTrue(facade_calls)
                self.assertTrue(system_exit_calls)
                self.assertNotIn("from legacy_codex_entry import", source)

    def test_runtime_prefetches_snapshot_and_passes_environment_to_child(self) -> None:
        contract = {
            "supplemental_sources": {
                "lianban_daily": {
                    "enabled": True,
                    "required": False,
                    "client": str(CLIENT_PATH),
                    "date_mode": "latest_available",
                }
            }
        }
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            snapshot = run_dir / "lianban-daily.json"
            observed_command: list[str] = []

            def fake_run_process(
                command,
                cwd,
                timeout,
                extra_environment=None,
                process_role=None,
            ):
                observed_command[:] = [str(item) for item in command]
                snapshot.write_text(
                    json.dumps({
                        "schema": "LIANBAN_DAILY_SNAPSHOT_V1",
                        "status": "CLEAN_PASS",
                        "target_date": "2026-08-12",
                        "sources": {
                            "page": {
                                "url": "https://lianban.net/days/2026-08-12.html",
                                "status_code": 200,
                            },
                            "open_data": {
                                "url": "https://lianban.net/opendata/2026-08-12.json",
                                "status_code": 200,
                            },
                        },
                    }),
                    encoding="utf-8",
                )
                return {
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                    "started_at": "2026-08-12T12:00:00+08:00",
                    "finished_at": "2026-08-12T12:00:01+08:00",
                    "elapsed_seconds": 1.0,
                }

            with mock.patch.object(
                self.runtime,
                "STOCK_LIANBAN_CACHE_ROOT",
                run_dir / "runtime-cache",
            ), mock.patch.object(
                self.runtime,
                "run_process",
                side_effect=fake_run_process,
            ):
                result = self.runtime.prepare_lianban_daily_source(
                    contract,
                    run_dir,
                    "2026-08-12",
                )

            self.assertEqual(result["status"], "CLEAN_PASS")
            self.assertEqual(result["environment"]["CODEX_LIANBAN_STATUS"], "CLEAN_PASS")
            self.assertEqual(
                result["environment"]["CODEX_LIANBAN_SNAPSHOT"],
                str(snapshot.resolve()),
            )
            self.assertEqual(
                result["environment"]["CODEX_LIANBAN_SOURCE_URL"],
                "https://lianban.net/days/2026-08-12.html",
            )
            self.assertIn("--latest", observed_command)
            self.assertNotIn("--date", observed_command)

    def test_run_process_accepts_explicit_environment_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            probe = Path(temporary) / "probe.py"
            probe.write_text(
                "import json, os, subprocess, sys\n"
                "print(json.dumps({\n"
                "    'CODEX_LIANBAN_STATUS': os.environ.get('CODEX_LIANBAN_STATUS'),\n"
                "    'CODEX_TDX_PROCESS_GUARD': os.environ.get('CODEX_TDX_PROCESS_GUARD'),\n"
                "    'tdx_process_guard_loaded': 'tdx_process_guard' in sys.modules,\n"
                "    'popen_init_guard_installed': bool(getattr(subprocess.Popen.__init__, '_codex_tdx_process_guard', False)),\n"
                "}, sort_keys=True))\n",
                encoding="utf-8",
                newline="\n",
            )
            command = [os.sys.executable, str(probe)]
            formula_guard = {"status": "CLEAN_PASS", "errors": [], "files": []}
            process_snapshots = [
                {
                    "status": "OK",
                    "captured_at": "2026-08-24T00:00:00+08:00",
                    "processes": [],
                    "errors": [],
                },
                {
                    "status": "OK",
                    "captured_at": "2026-08-24T00:00:01+08:00",
                    "processes": [],
                    "errors": [],
                },
            ]

            with mock.patch.object(
                self.runtime,
                "validate_tdx_formula_guard",
                return_value=formula_guard,
            ), mock.patch.object(
                self.runtime,
                "capture_tdx_process_snapshot",
                side_effect=process_snapshots,
            ):
                child = self.runtime.run_process(
                    command,
                    Path.cwd(),
                    10,
                    {"CODEX_LIANBAN_STATUS": "CLEAN_PASS"},
                    process_role="supplemental",
                )

            self.assertEqual(child["returncode"], 0, child["stderr"])
            payload = json.loads(child["stdout"])
            self.assertEqual(payload["CODEX_LIANBAN_STATUS"], "CLEAN_PASS")
            self.assertEqual(payload["CODEX_TDX_PROCESS_GUARD"], "1")
            self.assertTrue(payload["tdx_process_guard_loaded"])
            self.assertTrue(payload["popen_init_guard_installed"])
            self.assertEqual(child["tdx_process_integrity"]["status"], "CLEAN_PASS")
            bootstrap = (
                HOME / "scripts" / "stock_runtime_bootstrap" / "sitecustomize.py"
            ).resolve()
            self.assertEqual(
                child["effective_command"],
                [os.sys.executable, str(bootstrap), str(probe.resolve())],
            )


if __name__ == "__main__":
    unittest.main()
