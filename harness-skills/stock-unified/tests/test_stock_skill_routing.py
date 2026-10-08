from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "references" / "stock_skill_ids.json"
SKILLS_ROOT = ROOT.parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNTIME = load_module(
    "stock_canonical_runtime_routing_test",
    ROOT.parents[1] / "scripts" / "stock_canonical_runtime.py",
)
CATALOG = load_module(
    "stock_contract_catalog_routing_test",
    ROOT / "scripts" / "stock_contract_catalog.py",
)
VALIDATOR = load_module(
    "validate_skill_routing_test",
    ROOT / "scripts" / "validate_skill_routing.py",
)


class StockSkillRoutingTests(unittest.TestCase):
    def route(self, query: str) -> list[str]:
        result = RUNTIME.route_stock_query(
            query,
            catalog_path=CATALOG_PATH,
            skills_root=SKILLS_ROOT,
        )
        return result["skill_ids"]

    def test_exact_workflow_names_route_to_specialized_skills(self) -> None:
        self.assertEqual(
            self.route("大牛线"),
            ["big-bull-analysis-scoring-system"],
        )
        self.assertEqual(self.route("飞龙在天"), ["feilong-strategy"])

    def test_short_term_sentiment_scoring_name_routes_to_specialized_skill(self) -> None:
        self.assertEqual(
            self.route("独立跑一次短线市场情绪评分系统，使用最新数据，给实跑结果"),
            ["a-share-short-term-market-sentiment"],
        )

    def test_convertible_bond_skill_name_routes_to_specialized_skill(self) -> None:
        self.assertEqual(
            self.route("可转债筛选技能"),
            ["convertible-bond-screening-strategy"],
        )

    def test_multiple_workflows_preserve_user_order(self) -> None:
        self.assertEqual(
            self.route("大牛线+飞龙在天"),
            ["big-bull-analysis-scoring-system", "feilong-strategy"],
        )
        self.assertEqual(
            self.route("飞龙在天+大牛线"),
            ["feilong-strategy", "big-bull-analysis-scoring-system"],
        )

    def test_three_system_composite_scoring_routes_to_integrated_owner(self) -> None:
        self.assertEqual(
            self.route(
                "使用大牛线16项＋飞龙在天10项＋庄家资金监控4项"
                "综合评分系统对自定义板块评分"
            ),
            ["big-bull-analysis-scoring-system"],
        )

    def test_three_system_30_item_optimization_routes_to_integrated_owner(self) -> None:
        self.assertEqual(
            self.route(
                "根据优化的结果同步优化大牛线+飞龙在天+"
                "庄家资金监控30项评分系统"
            ),
            ["big-bull-analysis-scoring-system"],
        )

    def test_remove_added_projects_and_keep_exact_thirty_routes_to_owner(self) -> None:
        self.assertEqual(
            self.route(
                "大牛线评分系统中仅保留大牛线+飞龙在天+"
                "庄家资金监控共30项目，其他新增的剔除，请全局修改"
            ),
            ["big-bull-analysis-scoring-system"],
        )

    def test_custom_board_names_do_not_route_as_independent_workflows(self) -> None:
        self.assertEqual(
            self.route(
                "使用大牛线综合评分系统对本机通达信中名为黄金点火和"
                "飞龙在天的自定义板块中的成分股进行评分，交付两张独立的"
                "8K高清海报横版，是原版的大牛线评分系统30项"
            ),
            ["big-bull-analysis-scoring-system"],
        )

    def test_longest_exact_workflow_name_wins(self) -> None:
        self.assertEqual(
            self.route("飞龙在天波段<20"),
            ["a-share-bottom-fishing"],
        )

    def test_explicit_skill_id_and_generic_default(self) -> None:
        self.assertEqual(
            self.route("$feilong-strategy"),
            ["feilong-strategy"],
        )
        self.assertEqual(
            self.route("请研究一只未指定固定流程的普通股票"),
            ["stock-research-codex"],
        )

    def test_stock_workflow_governance_routes_to_unified_audit(self) -> None:
        self.assertEqual(
            self.route("全面审计本机所有股票技能工作流"),
            ["stock-unified"],
        )

    def test_stock_workflow_correction_continuation_routes_to_unified_audit(
        self,
    ) -> None:
        self.assertEqual(
            self.route(
                "审计深度不够，每个技能，每个流程跑一遍，"
                "重点解决横跳+漂移+拖延交付的问题"
            ),
            ["stock-unified"],
        )

    def test_stock_workflow_governance_intent_routes_to_unified_audit(self) -> None:
        self.assertEqual(
            self.route(
                "我要确保股票技能100%按照技能工作流和模板进行，"
                "100%不得漂移和偏离模板"
            ),
            ["stock-unified"],
        )

    def test_global_skill_confusion_correction_routes_to_unified_audit(self) -> None:
        self.assertEqual(
            self.route("全局纠正不同技能混淆的问题，全局查找全局纠正"),
            ["stock-unified"],
        )

    def test_stock_skill_inventory_questions_route_to_unified_audit(self) -> None:
        self.assertEqual(
            self.route("本机股票技能中，有几套评分系统"),
            ["stock-unified"],
        )
        self.assertEqual(
            self.route("盘点本机股票技能有哪些评分体系"),
            ["stock-unified"],
        )

    def test_leader_deep_analysis_alias_does_not_fall_back_to_generic(self) -> None:
        self.assertEqual(
            self.route("龙头深度分析"),
            ["a-share-leader-deep-research"],
        )
        self.assertEqual(
            self.route("调用龙头深度技能，使用最新数据，交付精美的word文档"),
            ["a-share-leader-deep-research"],
        )
        self.assertEqual(
            self.route("龙头深度"),
            ["a-share-leader-deep-research"],
        )

    def test_merged_legacy_explicit_ids_route_to_canonical_skills(self) -> None:
        self.assertEqual(
            self.route("$support-resistance-analysis-system"),
            ["support-pressure-analysis-system"],
        )
        self.assertEqual(
            self.route("$a-share-five-site-sentiment"),
            ["a-share-hotspot-sentiment-analysis"],
        )

    def test_support_pressure_short_chinese_name_routes_to_specialized_workflow(self) -> None:
        self.assertEqual(
            self.route("今后使用支撑压力系统进行分析，必须使用全部子系统"),
            ["support-pressure-analysis-system"],
        )

    def test_unknown_explicit_skill_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "unknown_explicit_stock_skill_id:not-a-stock-skill",
        ):
            self.route("$not-a-stock-skill")

    def test_every_catalog_skill_id_is_reachable(self) -> None:
        catalog = CATALOG.load_stock_catalog(
            catalog_path=CATALOG_PATH,
            skills_root=SKILLS_ROOT,
        )
        for skill_id in catalog["skills"]:
            with self.subTest(skill_id=skill_id):
                self.assertEqual(self.route(f"${skill_id}"), [skill_id])

    def test_every_workflow_name_is_reachable(self) -> None:
        catalog = CATALOG.load_stock_catalog(
            catalog_path=CATALOG_PATH,
            skills_root=SKILLS_ROOT,
        )
        for skill_id, workflow_names in catalog["workflow_names"].items():
            for workflow_name in workflow_names:
                with self.subTest(
                    skill_id=skill_id,
                    workflow_name=workflow_name,
                ):
                    self.assertEqual(self.route(workflow_name), [skill_id])

    def test_catalog_rejects_unknown_skill_duplicate_name_and_missing_names(
        self,
    ) -> None:
        original = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        mutations = []

        unknown = json.loads(json.dumps(original, ensure_ascii=False))
        unknown["skills"][0] = "not-an-installed-stock-skill"
        mutations.append((unknown, "unknown_catalog_skill_id"))

        duplicate = json.loads(json.dumps(original, ensure_ascii=False))
        duplicate["workflow_names"]["feilong-strategy"].append(" 大牛线 ")
        mutations.append((duplicate, "duplicate_normalized_workflow_name"))

        missing = json.loads(json.dumps(original, ensure_ascii=False))
        missing["workflow_names"].pop("big-bull-analysis-scoring-system")
        mutations.append((missing, "workflow_name_skill_set_mismatch"))

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "stock_skill_ids.json"
            for payload, expected in mutations:
                path.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                with self.subTest(expected=expected):
                    with self.assertRaisesRegex(ValueError, expected):
                        CATALOG.load_stock_catalog(
                            catalog_path=path,
                            skills_root=SKILLS_ROOT,
                        )


class CodexHomeIdentityTests(unittest.TestCase):
    def test_compat_junction_is_the_same_physical_home(self) -> None:
        self.assertTrue(
            VALIDATOR.same_physical_home(
                Path(r"D:\C盘转移\日志\codex"),
                Path(r"D:\C盘转移\日志\codex"),
            )
        )
        with mock.patch.object(VALIDATOR, "is_reparse_point", return_value=True):
            result = VALIDATOR.validate_home_identity(
                canonical_home=Path(r"D:\C盘转移\日志\codex"),
                compat_home=Path(r"D:\C盘转移\日志\codex"),
                process_home=Path(r"D:\C盘转移\日志\codex"),
                user_home=Path(r"D:\C盘转移\日志\codex"),
            )
        self.assertEqual(result["errors"], [], result)

    def test_independent_second_directory_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            second_home = Path(temporary)
            self.assertFalse(
                VALIDATOR.same_physical_home(
                    second_home,
                    Path(r"D:\C盘转移\日志\codex"),
                )
            )

    def test_wrong_junction_target_is_blocked(self) -> None:
        with mock.patch.object(
            VALIDATOR.os.path,
            "samefile",
            return_value=False,
        ):
            result = VALIDATOR.validate_home_identity(
                canonical_home=Path(r"D:\C盘转移\日志\codex"),
                compat_home=Path(r"D:\C盘转移\日志\codex"),
                process_home=Path(r"D:\C盘转移\日志\codex"),
                user_home=Path(r"D:\C盘转移\日志\codex"),
            )
        self.assertIn("compat_home_wrong_target", result["errors"])

    def test_second_active_catalog_or_alias_authority_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            canonical = (
                home
                / "skills"
                / "stock-unified"
                / "references"
                / "stock_skill_ids.json"
            )
            canonical.parent.mkdir(parents=True)
            shutil.copy2(CATALOG_PATH, canonical)

            second = home / "skills" / "other" / "stock_skill_ids.json"
            second.parent.mkdir(parents=True)
            shutil.copy2(CATALOG_PATH, second)
            result = VALIDATOR.validate_stock_authority_topology(home)
            self.assertIn("multiple_active_stock_catalogs", result["errors"])

            second.unlink()
            alias = home / "skills" / "other" / "skill_router.py"
            alias.write_text("# alternate stock routing authority\n", encoding="utf-8")
            result = VALIDATOR.validate_stock_authority_topology(home)
            self.assertIn("alternate_stock_routing_authority", result["errors"])

    def test_second_contract_or_runtime_authority_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            canonical_root = home / "skills" / "stock-unified" / "references"
            canonical_root.mkdir(parents=True)
            shutil.copy2(CATALOG_PATH, canonical_root / "stock_skill_ids.json")
            source_contracts = ROOT / "references" / "stock_execution_contracts.json"
            shutil.copy2(
                source_contracts,
                canonical_root / "stock_execution_contracts.json",
            )
            runtime = home / "scripts" / "stock_canonical_runtime.py"
            runtime.parent.mkdir(parents=True)
            runtime.write_text("# canonical runtime\n", encoding="utf-8")

            second_contract = (
                home / "skills" / "other" / "stock_execution_contracts.json"
            )
            second_contract.parent.mkdir(parents=True)
            shutil.copy2(source_contracts, second_contract)
            result = VALIDATOR.validate_stock_authority_topology(home)
            self.assertIn("multiple_active_stock_contracts", result["errors"])

            second_contract.unlink()
            second_runtime = (
                home / "skills" / "other" / "stock_canonical_runtime.py"
            )
            second_runtime.write_text("# alternate runtime\n", encoding="utf-8")
            result = VALIDATOR.validate_stock_authority_topology(home)
            self.assertIn("multiple_active_stock_runtimes", result["errors"])


if __name__ == "__main__":
    unittest.main()
