from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
CATALOG_PATH = ROOT / "references" / "stock_skill_ids.json"
CONTRACTS_PATH = ROOT / "references" / "stock_execution_contracts.json"
RUNTIME_PATH = ROOT.parents[1] / "scripts" / "stock_canonical_runtime.py"
SHARED_INDUSTRY_ROUTER = RUNTIME_PATH.parent / "industry_data_router.py"
SENTIMENT_ID = "a-share-hotspot-sentiment-analysis"
HOTSPOT_ID = "shortline-hotspot-mining"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


RUNTIME = load_module("stock_canonical_runtime_merge_test", RUNTIME_PATH)
SENTIMENT_WORKFLOW = load_module(
    "merged_sentiment_workflow_test",
    SKILLS_ROOT / SENTIMENT_ID / "scripts" / "merged_workflow.py",
)
HOTSPOT_WORKFLOW = load_module(
    "merged_hotspot_workflow_test",
    SKILLS_ROOT / HOTSPOT_ID / "scripts" / "merged_workflow.py",
)
HOTSPOT_LEADER_RANKER = load_module(
    "merged_hotspot_leader_ranker_test",
    SKILLS_ROOT / HOTSPOT_ID / "scripts" / "leader_ranker.py",
)


class MergedSkillContractTests(unittest.TestCase):
    def route(self, query: str) -> list[str]:
        return RUNTIME.route_stock_query(
            query,
            catalog_path=CATALOG_PATH,
            skills_root=SKILLS_ROOT,
        )["skill_ids"]

    def test_legacy_names_route_to_current_merged_skills(self) -> None:
        sentiment_queries = (
            "A股热点舆情研判",
            "A股舆情分析工作流",
            "五站A股舆情研判",
            "市场情报",
            "三端社媒财经简报",
            "$a-share-sentiment-workflow",
            "$market-intel",
            "$social-finance-brief",
        )
        for query in sentiment_queries:
            with self.subTest(query=query):
                self.assertEqual(self.route(query), [SENTIMENT_ID])

        for query in ("短线热点挖掘", "热点龙头", "$hotspot-leader"):
            with self.subTest(query=query):
                self.assertEqual(self.route(query), [HOTSPOT_ID])

    def test_retired_skills_are_not_independent_authorities(self) -> None:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        retired = {
            "a-share-sentiment-workflow",
            "market-intel",
            "social-finance-brief",
            "a-share-research-content-agents",
            "hotspot-leader",
        }
        self.assertTrue(retired.isdisjoint(catalog["skills"]))
        self.assertTrue(retired.isdisjoint(catalog["workflow_names"]))
        for skill_id in retired:
            self.assertFalse((SKILLS_ROOT / skill_id).exists(), skill_id)

    def test_sentiment_v2_manifest_binds_active_and_retired_components(self) -> None:
        skill_root = SKILLS_ROOT / SENTIMENT_ID
        manifest = json.loads(
            (skill_root / "references" / "source-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["schema"], "MERGED_SKILL_SOURCE_MANIFEST_V2")
        self.assertEqual(manifest["sources"], ["a-share-sentiment-workflow"])
        retired = {item["name"]: item for item in manifest["retired_components"]}
        self.assertEqual(set(retired), {"market-intel", "social-finance-brief"})
        for item in retired.values():
            self.assertEqual(item["status"], "historical_reports_only")
            self.assertEqual(item["redirect"], "canonical_unified_workflow")

        component_root = skill_root / "components" / manifest["sources"][0]
        for relative, expected_hash in manifest["files"][manifest["sources"][0]].items():
            path = component_root / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(sha256_file(path), expected_hash, relative)

    def test_sentiment_plan_uses_current_unified_component(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary)
            plan = SENTIMENT_WORKFLOW.build_execution_plan(
                ["all"],
                run_root=run_root,
                target_day=date(2026, 8, 16),
            )
        self.assertEqual([item["mode"] for item in plan["components"]], ["sentiment"])
        component = plan["components"][0]
        self.assertEqual(component["source"], "a-share-sentiment-workflow")
        self.assertEqual(component["steps"][0]["args"][0], "generate")
        for alias in ("market-intel", "social-finance", "市场情报", "三端社媒财经简报"):
            mode, extra, selected = SENTIMENT_WORKFLOW._selected_modes([alias])
            self.assertEqual((mode, extra, selected), ("sentiment", [], ["sentiment"]))

    def test_shortline_leaders_keep_candidate_snapshot_and_member_lineage(self) -> None:
        snapshot_id = "snapshot-20260821"
        candidate_members = {"000001", "000002"}
        snapshot = {
            "snapshot_id": snapshot_id,
            "resolved_trade_date": "2026-08-21",
            "sectors": [
                {
                    "sector": "候选板块",
                    "members": [
                        {
                            "code": "000001",
                            "relative_strength": 0.08,
                            "amount_ratio": 1.8,
                            "persistence": 0.8,
                        },
                        {
                            "code": "000002",
                            "relative_strength": 0.04,
                            "amount_ratio": 1.3,
                            "persistence": 0.6,
                        },
                    ],
                },
                {
                    "sector": "非候选板块",
                    "members": [{"code": "000003", "relative_strength": 0.20}],
                },
            ],
        }
        forecasts = [
            {
                "snapshot_id": snapshot_id,
                "sector": "候选板块",
                "horizon": "H1",
                "market_rank": 1,
                "final_probability": 0.72,
            },
            {
                "snapshot_id": snapshot_id,
                "sector": "非候选板块",
                "horizon": "H1",
                "market_rank": 6,
                "final_probability": 0.99,
            },
        ]

        leaders = HOTSPOT_LEADER_RANKER.rank_leaders(snapshot, forecasts)

        self.assertTrue(leaders)
        self.assertEqual({row["snapshot_id"] for row in leaders}, {snapshot_id})
        self.assertEqual({row["sector"] for row in leaders}, {"候选板块"})
        self.assertLessEqual({row["code"] for row in leaders}, candidate_members)
        self.assertTrue(all(row["member_of_frozen_sector"] for row in leaders))
        with self.assertRaises(HOTSPOT_LEADER_RANKER.LeaderBlocked):
            HOTSPOT_LEADER_RANKER.rank_leaders(
                snapshot,
                [
                    {
                        "snapshot_id": "wrong-snapshot",
                        "sector": "候选板块",
                        "horizon": "H1",
                        "market_rank": 2,
                        "final_probability": 0.80,
                    }
                ],
            )

    def test_shortline_contract_binds_shared_industry_router(self) -> None:
        payload = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))
        contract = next(
            row for row in payload["contracts"] if row["skill_id"] == HOTSPOT_ID
        )
        bound_paths = {
            Path(binding["path"]).resolve()
            for binding in contract["business_bindings"]
        }
        self.assertIn(SHARED_INDUSTRY_ROUTER.resolve(), bound_paths)

    def test_shortline_contract_requires_forecast_delivery_and_status(self) -> None:
        payload = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))
        contract = next(
            row for row in payload["contracts"] if row["skill_id"] == HOTSPOT_ID
        )
        required = {item["path"] for item in contract["required_artifacts"]}
        expected = {
            rf"{{run_dir}}\deliverables\{name}"
            for name in (
                "forecast_snapshot.json",
                "feature_snapshot.json",
                "forecast_rank.csv",
                "leader_rank.csv",
                "evidence.json",
                "model_card.json",
                "backtest_report.json",
                "audit.json",
                "manifest.json",
                "report.md",
            )
        }
        self.assertTrue(expected.issubset(required))
        assertions = contract["semantic_assertions"]
        contains = [row for row in assertions if row["type"] == "output_contains_any"]
        forbidden = [row for row in assertions if row["type"] == "output_not_contains"]
        deliverable_forecast_statuses = {
            f'"forecast_status": "{status}"'
            for status in (
                "VALIDATED_FORECAST",
                "PROVISIONAL_FORECAST",
                "DEGRADED_FORECAST",
            )
        } | {
            f'"forecast_status":"{status}"'
            for status in (
                "VALIDATED_FORECAST",
                "PROVISIONAL_FORECAST",
                "DEGRADED_FORECAST",
            )
        }
        self.assertTrue(
            any(
                set(row.get("values", [])) >= deliverable_forecast_statuses
                for row in contains
            )
        )
        forbidden_forecast_statuses = {
            '"forecast_status": ""',
            '"forecast_status":""',
            '"forecast_status": "BLOCKED"',
            '"forecast_status":"BLOCKED"',
        }
        self.assertTrue(
            any(
                set(row.get("values", []))
                >= ({
                    '"requires_research_completion": true',
                    '"requires_research_completion":true',
                } | forbidden_forecast_statuses)
                for row in forbidden
            )
        )

    def test_shortline_docs_define_one_scientific_forecast_chain(self) -> None:
        skill_root = SKILLS_ROOT / HOTSPOT_ID
        documents = {
            "SKILL.md": (skill_root / "SKILL.md").read_text(encoding="utf-8"),
            "references/workflow.md": (
                skill_root / "references" / "workflow.md"
            ).read_text(encoding="utf-8"),
        }
        deliverables = (
            "forecast_snapshot.json",
            "feature_snapshot.json",
            "forecast_rank.csv",
            "leader_rank.csv",
            "evidence.json",
            "model_card.json",
            "backtest_report.json",
            "audit.json",
            "manifest.json",
            "report.md",
        )
        forbidden_legacy_meanings = (
            "先执行原短线热点流程",
            "再执行原热点龙头流程",
            "组件正常执行",
        )
        for label, text in documents.items():
            with self.subTest(document=label):
                self.assertIn("stock_canonical_runtime.py", text)
                self.assertIn("route", text)
                self.assertIn("authorize --receipt", text)
                self.assertIn("点时快照", text)
                for horizon in ("H1", "H2", "H3"):
                    self.assertIn(horizon, text)
                self.assertIn("forecast_status", text)
                for deliverable in deliverables:
                    self.assertIn(deliverable, text)
                for phrase in forbidden_legacy_meanings:
                    self.assertNotIn(phrase, text)

    def test_shortline_contract_binds_every_forecast_module(self) -> None:
        payload = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))
        contract = next(
            row for row in payload["contracts"] if row["skill_id"] == HOTSPOT_ID
        )
        required = set(contract["workflow_guard"]["required_bindings"])
        self.assertTrue(
            {
                "references/2026-08-23-scientific-forecast-design.md",
                "references/2026-08-23-scientific-forecast-implementation-plan.md",
                "scripts/point_in_time_snapshot.py",
                "scripts/market_features.py",
                "scripts/future_labels.py",
                "scripts/forecast_model.py",
                "scripts/walk_forward_backtest.py",
                "scripts/catalyst_features.py",
                "scripts/leader_ranker.py",
                "scripts/forecast_gate.py",
            }.issubset(required)
        )

    def test_only_top_level_skill_files_are_discoverable(self) -> None:
        for skill_id in (SENTIMENT_ID, HOTSPOT_ID):
            root = SKILLS_ROOT / skill_id
            self.assertEqual(
                [path.relative_to(root).as_posix() for path in root.rglob("SKILL.md")],
                ["SKILL.md"],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
