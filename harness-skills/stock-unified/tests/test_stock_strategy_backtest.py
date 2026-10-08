from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "stock_strategy_backtest.py"
SPEC = importlib.util.spec_from_file_location("stock_strategy_backtest", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def bar(date: int, price: float, *, high: float | None = None, low: float | None = None, volume: int = 1000):
    return MODULE.Bar(
        date=date,
        open=price,
        high=price if high is None else high,
        low=price if low is None else low,
        close=price,
        amount=float(price * volume),
        volume=volume,
    )


class ExecutionModelTests(unittest.TestCase):
    def test_signal_enters_on_next_trading_day(self):
        rows = [bar(20260105, 10.0), bar(20260106, 10.2), bar(20260107, 10.4)]
        trades = MODULE.execute_signals(
            "600000.SH",
            rows,
            [True, False, False],
            MODULE.ExecutionConfig(hold_days=1, slippage_bps=0),
        )
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].signal_date, 20260105)
        self.assertEqual(trades[0].entry_date, 20260106)
        self.assertEqual(trades[0].exit_date, 20260107)

    def test_one_price_limit_up_rejects_entry(self):
        rows = [bar(20260105, 10.0), bar(20260106, 11.0), bar(20260107, 10.8)]
        trades = MODULE.execute_signals(
            "600000.SH",
            rows,
            [True, False, False],
            MODULE.ExecutionConfig(hold_days=1, slippage_bps=0),
        )
        self.assertEqual(trades, [])

    def test_suspension_and_one_price_limit_down_delay_exit(self):
        rows = [
            bar(20260105, 10.0),
            bar(20260106, 10.1),
            bar(20260107, 10.1, volume=0),
            bar(20260108, 9.09),
            bar(20260109, 9.2, high=9.3, low=9.0),
        ]
        trades = MODULE.execute_signals(
            "600000.SH",
            rows,
            [True, False, False, False, False],
            MODULE.ExecutionConfig(hold_days=1, slippage_bps=0),
        )
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].exit_date, 20260109)
        self.assertEqual(trades[0].exit_delay_days, 2)

    def test_costs_include_minimum_commission_stamp_tax_and_slippage(self):
        rows = [
            bar(20260105, 10.0),
            bar(20260106, 10.0, high=10.1, low=9.9),
            bar(20260107, 10.5, high=10.6, low=10.4),
        ]
        trades = MODULE.execute_signals(
            "600000.SH",
            rows,
            [True, False, False],
            MODULE.ExecutionConfig(
                hold_days=1,
                capital_per_trade=1000,
                commission_rate=0.00025,
                minimum_commission=5,
                stamp_tax_rate=0.0005,
                slippage_bps=10,
            ),
        )
        trade = trades[0]
        self.assertAlmostEqual(trade.entry_price, 10.01, places=6)
        self.assertAlmostEqual(trade.exit_price, 10.4895, places=6)
        self.assertEqual(trade.entry_commission, 5)
        self.assertEqual(trade.exit_commission, 5)
        self.assertGreater(trade.stamp_tax, 0)
        self.assertLess(trade.net_return, trade.gross_return)

    def test_convertible_bond_uses_ten_unit_lots_without_stamp_tax(self):
        rows = [
            bar(20260105, 100.0),
            bar(20260106, 100.0, high=101.0, low=99.0),
            bar(20260107, 101.0, high=102.0, low=100.0),
        ]
        trades = MODULE.execute_signals(
            "113001.SH",
            rows,
            [True, False, False],
            MODULE.ExecutionConfig(
                hold_days=1,
                capital_per_trade=1050,
                commission_rate=0,
                minimum_commission=0,
                stamp_tax_rate=0.0005,
                slippage_bps=0,
                lot_size=10,
                asset_type="convertible_bond",
            ),
        )
        trade = trades[0]
        self.assertEqual(trade.shares, 10)
        self.assertEqual(trade.stamp_tax, 0)


class TimeSplitTests(unittest.TestCase):
    def test_chronological_split_is_disjoint_and_ordered(self):
        dates = list(range(20250101, 20250201))
        split = MODULE.chronological_split(dates, train_ratio=0.6, validation_ratio=0.2)
        self.assertLess(split.train_end, split.validation_start)
        self.assertLess(split.validation_end, split.test_start)
        train = {date for date in dates if split.contains("train", date)}
        validation = {date for date in dates if split.contains("validation", date)}
        test = {date for date in dates if split.contains("test", date)}
        self.assertFalse(train & validation)
        self.assertFalse(train & test)
        self.assertFalse(validation & test)
        self.assertEqual(train | validation | test, set(dates))


def strategy_result(
    skill: str,
    *,
    improved: bool,
    baseline: dict[str, object] | None = None,
    optimized: dict[str, object] | None = None,
):
    return {
        "skill": skill,
        "status": "PASS",
        "baseline_parameters": baseline or {"hold_days": 5},
        "optimized_parameters": optimized or {"hold_days": 8},
        "test_comparison": {"out_of_sample_improved": improved},
    }


class PaperDebugDeploymentTests(unittest.TestCase):
    def test_improved_strategy_uses_optimized_parameters_only_in_paper_debug(self):
        result = strategy_result(
            "golden-ignition",
            improved=True,
            baseline={"fast": 3, "slow": 21},
            optimized={"fast": 5, "slow": 21},
        )

        decision = MODULE.build_deployment_decision(result)

        self.assertEqual(decision["mode"], "PAPER_DEBUG_ONLY")
        self.assertEqual(decision["active_parameters"], result["optimized_parameters"])
        self.assertFalse(decision["production_skill_modified"])
        self.assertFalse(decision["automatic_order"])

    def test_non_improved_strategy_retains_baseline_parameters(self):
        result = strategy_result(
            "a-share-limit-up-mining",
            improved=False,
            baseline={"boards": 2, "hold_days": 3},
            optimized={"boards": 2, "hold_days": 2},
        )

        decision = MODULE.build_deployment_decision(result)

        self.assertEqual(decision["mode"], "BASELINE_RETAINED")
        self.assertEqual(decision["active_parameters"], result["baseline_parameters"])

    def test_validation_rejects_automatic_order_or_production_skill_changes(self):
        results = self._six_strategy_results()
        for result in results:
            result["deployment_decision"] = MODULE.build_deployment_decision(result)

        results[0]["deployment_decision"]["automatic_order"] = True
        results[1]["deployment_decision"]["production_skill_modified"] = True
        validation = MODULE.validate_deployment_decisions(results)

        self.assertEqual(validation["status"], "FAIL")
        self.assertTrue(any("automatic_order" in error for error in validation["errors"]))
        self.assertTrue(any("production_skill_modified" in error for error in validation["errors"]))

    def test_six_strategy_debug_split_is_exactly_three_and_three(self):
        results = self._six_strategy_results()
        for result in results:
            result["deployment_decision"] = MODULE.build_deployment_decision(result)

        validation = MODULE.validate_deployment_decisions(results)

        self.assertEqual(validation["status"], "PASS")
        self.assertEqual(
            validation["mode_counts"],
            {"PAPER_DEBUG_ONLY": 3, "BASELINE_RETAINED": 3},
        )
        self.assertEqual(validation["validated_strategy_count"], 6)
        self.assertEqual(validation["errors"], [])

    @staticmethod
    def _six_strategy_results():
        return [
            strategy_result("golden-ignition", improved=True),
            strategy_result("feilong-strategy", improved=False),
            strategy_result("a-share-bottom-fishing", improved=True),
            strategy_result("a-share-limit-up-mining", improved=False),
            strategy_result("convertible-bond-screening-strategy", improved=False),
            strategy_result("quality-track-stock-selection", improved=True),
        ]


if __name__ == "__main__":
    unittest.main()
