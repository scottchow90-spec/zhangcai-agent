from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import pandas as pd


HOME = Path(r"D:\C盘转移\日志\codex")
BIG_BULL = HOME / "skills" / "big-bull-analysis-scoring-system"
SCRIPTS = BIG_BULL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
CONTRACTS = (
    HOME
    / "skills"
    / "stock-unified"
    / "references"
    / "stock_execution_contracts.json"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


LEGACY = load_module("big_bull_legacy_confusion_test", SCRIPTS / "legacy_codex_entry.py")
BACKTEST = load_module(
    "big_bull_composite_confusion_test",
    SCRIPTS / "three_formula_composite_backtest.py",
)


class BigBullSkillConfusionGateTests(unittest.TestCase):
    def test_default_execution_is_the_fixed_30_item_composite(self) -> None:
        self.assertEqual(LEGACY.DEFAULT_ARGS[-1], "score-research-composite")

    def test_default_composite_targets_the_canonical_hjdh_board(self) -> None:
        self.assertEqual(
            LEGACY.normalize_business_args([]),
            [
                "score-research-composite",
                "--board-name",
                "黄金点火",
                "--board-code",
                "HJDH",
            ],
        )

    def test_legacy_five_dimension_mode_requires_explicit_compatibility_flag(self) -> None:
        self.assertTrue(hasattr(LEGACY, "normalize_business_args"))
        with self.assertRaisesRegex(ValueError, "legacy_five_dimension_mode_blocked"):
            LEGACY.normalize_business_args(["score-board"])
        self.assertEqual(
            LEGACY.normalize_business_args(
                ["score-board", "--legacy-five-dimension-compat"]
            ),
            ["score-board"],
        )

    def test_scoring_universe_never_depends_on_board_membership(self) -> None:
        first = BACKTEST.merge_scoring_universe(
            ["000001.SZ", "600000.SH"],
            ["000002.SZ"],
            0,
        )
        second = BACKTEST.merge_scoring_universe(
            ["600000.SH", "000001.SZ"],
            ["300001.SZ"],
            0,
        )
        self.assertEqual(first, ["000001.SZ", "600000.SH"])
        self.assertEqual(second, first)

    def test_target_stocks_do_not_change_reference_percentiles(self) -> None:
        catalog = BACKTEST.subsystem_catalog()
        _, model = BACKTEST.build_fixed_research_model_payload()

        def row(symbol: str, offset: float) -> dict:
            values = {
                item["key"]: float(item["number"]) + offset
                for item in catalog
            }
            return {"date": "20260817", "symbol": symbol, **values}

        reference = ["000001.SZ", "600000.SH"]
        base = pd.DataFrame([
            row(reference[0], 0.0),
            row(reference[1], 10.0),
            row("000002.SZ", 5.0),
        ])
        expanded = pd.concat(
            [base, pd.DataFrame([row("300001.SZ", 100.0)])],
            ignore_index=True,
        )
        first = BACKTEST.score_feature_frame(
            base,
            model,
            reference_symbols=reference,
        )
        second = BACKTEST.score_feature_frame(
            expanded,
            model,
            reference_symbols=reference,
        )
        first_target = first[first["symbol"] == "000002.SZ"].iloc[0]
        second_target = second[second["symbol"] == "000002.SZ"].iloc[0]
        for field in (
            "score",
            "formula_scores",
            "top_level_items",
            "fusion",
            "contributions",
        ):
            self.assertEqual(first_target[field], second_target[field])

    def test_cross_board_gate_rejects_identity_or_score_drift(self) -> None:
        self.assertTrue(hasattr(BACKTEST, "validate_cross_board_score_consistency"))
        base = {
            "scoring_identity": {
                "contract_id": "BIG_BULL_30_ITEM_COMPOSITE_V1",
                "canonical_mode": "score-research-composite",
                "score_date": "20260817",
                "universe_policy": "tdx_csi300_fixed_reference_v1",
                "tdx_market": "23",
                "universe_count": 2,
                "universe_sha256": "a" * 64,
                "model_sha256": "b" * 64,
                "formula_catalog_sha256": "c" * 64,
                "component_item_counts": [16, 10, 4],
                "top_level_weights": [40.0, 35.0, 25.0],
            },
            "score_date": "20260817",
            "ranking": [
                {
                    "symbol": "000001.SZ",
                    "score": 60.0,
                    "formula_scores": {"大牛线撑压版": 60.0},
                    "top_level_items": [],
                    "fusion": {"base_score": 60.0},
                    "contributions": [],
                }
            ],
        }
        same = json.loads(json.dumps(base, ensure_ascii=False))
        result = BACKTEST.validate_cross_board_score_consistency([base, same])
        self.assertEqual(result["status"], "PASS")

        drifted = json.loads(json.dumps(base, ensure_ascii=False))
        drifted["ranking"][0]["score"] = 59.5
        with self.assertRaisesRegex(ValueError, "cross_board_score_drift"):
            BACKTEST.validate_cross_board_score_consistency([base, drifted])

        wrong_universe = json.loads(json.dumps(base, ensure_ascii=False))
        wrong_universe["scoring_identity"]["universe_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "cross_board_identity_drift"):
            BACKTEST.validate_cross_board_score_consistency([base, wrong_universe])

    def test_integrated_contract_declares_exclusive_owner_and_absorbed_components(self) -> None:
        payload = json.loads(CONTRACTS.read_text(encoding="utf-8"))
        row = next(
            item
            for item in payload["contracts"]
            if item["skill_id"] == "big-bull-analysis-scoring-system"
        )
        identity = row["workflow_identity"]
        self.assertEqual(identity["owner_skill_id"], row["skill_id"])
        self.assertTrue(identity["exclusive_owner"])
        self.assertEqual(identity["canonical_mode"], "score-research-composite")
        self.assertEqual(identity["contract_id"], "BIG_BULL_30_ITEM_COMPOSITE_V1")
        self.assertEqual(
            identity["absorbed_skill_ids"],
            ["feilong-strategy", "zhuangjia-capital-monitoring"],
        )
        self.assertEqual(identity["component_item_counts"], [16, 10, 4])
        self.assertEqual(identity["top_level_weights"], [40.0, 35.0, 25.0])
        self.assertEqual(
            identity["universe_policy"],
            "tdx_csi300_fixed_reference_v1",
        )
        self.assertIn(
            "scripts/scoring_mode_gate.py",
            row["workflow_guard"]["required_bindings"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
