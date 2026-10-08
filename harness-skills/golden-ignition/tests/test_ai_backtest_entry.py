from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ADAPTER = load(
    "golden_ignition_adapter_test",
    ROOT / "scripts" / "canonical_business_adapter.py",
)
ENTRY = load(
    "golden_ignition_entry_test",
    ROOT / "scripts" / "entry_golden_ignition.py",
)


class CanonicalBusinessArgumentTests(unittest.TestCase):
    def test_explicit_backtest_arguments_are_forwarded_to_legacy_entry(self):
        command = ADAPTER.business_command(
            Path("F:/temporary-run"),
            ["backtest", "--formula", "黄金点火AI", "--start-date", "20210101"],
        )
        self.assertEqual(command[2:4], ["run", "backtest"])
        self.assertEqual(
            command[3:],
            ["backtest", "--formula", "黄金点火AI", "--start-date", "20210101"],
        )

    def test_child_delivery_artifacts_are_bound_only_after_hash_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            report.write_text("verified report\n", encoding="utf-8")
            digest = hashlib.sha256(report.read_bytes()).hexdigest()
            payload = {
                "status": "PASS",
                "artifacts": {
                    "markdown": {
                        "path": str(report),
                        "size_bytes": report.stat().st_size,
                        "sha256": digest,
                    }
                },
            }
            artifacts, errors = ADAPTER.verified_child_artifacts(
                json.dumps(payload, ensure_ascii=False)
            )
            self.assertEqual(errors, [])
            self.assertEqual(artifacts["markdown"]["sha256"], digest)

            payload["artifacts"]["markdown"]["sha256"] = "0" * 64
            artifacts, errors = ADAPTER.verified_child_artifacts(
                json.dumps(payload, ensure_ascii=False)
            )
            self.assertEqual(artifacts, {})
            self.assertIn("child_artifact_hash_mismatch:markdown", errors)


class FormulaSeriesTests(unittest.TestCase):
    def test_historical_xg_call_requests_dates_and_requested_bar_count(self):
        class FakeTq:
            def __init__(self):
                self.kwargs = None
                self.released = False

            def formula_process_mul_xg(self, **kwargs):
                self.kwargs = kwargs
                return {"000001.SZ": {"XG": [0, 1], "DATE": [20260106, 20260107]}, "ErrorId": "0"}

            def _release(self):
                self.released = True

        class FakeLock:
            waited_ms = 0.0

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

        tq = FakeTq()

        class FakeHub:
            TQLock = FakeLock

            @staticmethod
            def load_tq():
                return tq, Path("C:/new_tdx_mock/PYPlugins/user/tdxdata_test.py")

        result = ENTRY.tq_xg_history(
            FakeHub,
            "黄金点火AI",
            ["000001.SZ"],
            count=120,
            dividend_type=1,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(tq.kwargs["count"], 120)
        self.assertTrue(tq.kwargs["return_date"])
        self.assertEqual(tq.kwargs["return_count"], 0)
        self.assertTrue(tq.released)

    def test_extracts_positive_dates_from_dated_xg_records(self):
        dates = ENTRY.extract_xg_signal_dates(
            [
                {"Date": "20260106", "Value": "0"},
                {"Date": "20260107", "Value": "1"},
                {"Date": "20260108", "Value": 0},
            ],
            fallback_dates=["20260106", "20260107", "20260108"],
        )
        self.assertEqual(dates, ["20260107"])

    def test_formula_failure_diagnostics_preserve_tq_evidence(self):
        text = ENTRY.formula_failure_diagnostics(
            {
                "ok": False,
                "attempts": [{"attempt": 1, "ok": False, "empty": True}],
                "result": {},
                "tq_stdout": "批量执行失败: 公式不存在",
                "tq_stderr": "runtime detail",
            }
        )
        self.assertIn("公式不存在", text)
        self.assertIn("runtime detail", text)
        self.assertIn('"attempts"', text)

    def test_formula_series_are_aligned_to_the_tail_of_daily_dates(self):
        aligned = ENTRY.align_formula_series(
            ["20260102", "20260105", "20260106", "20260107"],
            [0, 1],
        )
        self.assertEqual(aligned, {"20260106": 0.0, "20260107": 1.0})

    def test_signal_field_selection_prefers_sparse_boolean_pulses(self):
        field = ENTRY.select_signal_field(
            {
                "OUTPUT1": [10.0, 10.5, 11.0, 11.5, 12.0],
                "OUTPUT2": [0.0, 1.0, 0.0, 0.0, 1.0],
                "OUTPUT3": [0.0, 0.0, 0.0, 0.0, 0.0],
            },
            expected_length=5,
        )
        self.assertEqual(field, "OUTPUT2")


class BacktestCoreTests(unittest.TestCase):
    def test_parameter_grid_is_bounded_and_contains_baseline(self):
        baseline, grid = ENTRY.ai_parameter_grid()
        self.assertIn(baseline, grid)
        self.assertLessEqual(len(grid), 48)

    def test_candidate_selection_uses_validation_only_after_train_shortlist(self):
        rows = [
            {"parameters": {"id": "a"}, "train_objective": 0.9, "validation_objective": 0.1},
            {"parameters": {"id": "b"}, "train_objective": 0.8, "validation_objective": 0.7},
            {"parameters": {"id": "c"}, "train_objective": 0.1, "validation_objective": 9.0},
            {"parameters": {"id": "d"}, "train_objective": 0.0, "validation_objective": 8.0},
        ]
        selected = ENTRY.select_validation_candidate(rows)
        self.assertEqual(selected["parameters"], {"id": "b"})

    def test_dual_goal_selection_falls_back_to_baseline_when_no_candidate_improves_both(self):
        baseline = {"id": "baseline"}
        rows = [
            {
                "parameters": baseline,
                "train_objective": 0.80,
                "validation_objective": 0.50,
                "validation_metrics": {
                    "trade_count": 60,
                    "win_rate": 0.50,
                    "payoff_ratio": 1.50,
                },
            },
            {
                "parameters": {"id": "eight_day_four_percent_stop"},
                "train_objective": 0.90,
                "validation_objective": 0.70,
                "validation_metrics": {
                    "trade_count": 60,
                    "win_rate": 0.40,
                    "payoff_ratio": 3.00,
                },
            },
            {
                "parameters": {"id": "higher_win_lower_payoff"},
                "train_objective": 0.85,
                "validation_objective": 0.60,
                "validation_metrics": {
                    "trade_count": 60,
                    "win_rate": 0.60,
                    "payoff_ratio": 1.40,
                },
            },
        ]
        decision = ENTRY.select_dual_goal_candidate(
            rows,
            baseline_parameters=baseline,
            minimum_trades=20,
        )
        self.assertEqual(decision["selected"]["parameters"], baseline)
        self.assertEqual(decision["status"], "baseline_fallback_no_dual_improvement")
        self.assertEqual(len(decision["rejected_single_goal_candidates"]), 2)

    def test_dual_goal_selection_accepts_only_candidate_improving_both_metrics(self):
        baseline = {"id": "baseline"}
        eligible = {"id": "eligible"}
        rows = [
            {
                "parameters": baseline,
                "train_objective": 0.80,
                "validation_objective": 0.50,
                "validation_metrics": {
                    "trade_count": 60,
                    "win_rate": 0.50,
                    "payoff_ratio": 1.50,
                },
            },
            {
                "parameters": eligible,
                "train_objective": 0.90,
                "validation_objective": 0.70,
                "validation_metrics": {
                    "trade_count": 60,
                    "win_rate": 0.55,
                    "payoff_ratio": 1.70,
                },
            },
            {
                "parameters": {"id": "excluded_by_train_shortlist"},
                "train_objective": 0.10,
                "validation_objective": 9.00,
                "validation_metrics": {
                    "trade_count": 60,
                    "win_rate": 0.90,
                    "payoff_ratio": 4.00,
                },
            },
        ]
        decision = ENTRY.select_dual_goal_candidate(
            rows,
            baseline_parameters=baseline,
            minimum_trades=20,
        )
        self.assertEqual(decision["selected"]["parameters"], eligible)
        self.assertEqual(decision["status"], "dual_goal_validation_improved")

    def test_fallback_recommendations_do_not_recommend_rejected_parameters(self):
        recommendations = ENTRY.build_ai_recommendations(
            selection_status="baseline_fallback_no_dual_improvement",
            baseline={
                "hold_days": 5,
                "stop_loss_pct": 0.08,
                "trend_filter": "none",
                "volume_ratio": 0.0,
            },
            selected={
                "hold_days": 5,
                "stop_loss_pct": 0.08,
                "trend_filter": "none",
                "volume_ratio": 0.0,
            },
            rejected_single_goal_candidates=[
                {
                    "parameters": {
                        "hold_days": 8,
                        "stop_loss_pct": 0.04,
                        "trend_filter": "none",
                        "volume_ratio": 0.0,
                    },
                    "reasons": ["validation_win_rate_not_improved"],
                }
            ],
        )
        text = "\n".join(recommendations)
        self.assertIn("保留基线", text)
        self.assertNotIn("持有期建议：8", text)

    def test_ai_signal_dates_map_to_same_day_close_signals(self):
        bars = [
            SimpleNamespace(date=20260105, close=10.0, amount=100.0),
            SimpleNamespace(date=20260106, close=10.2, amount=120.0),
            SimpleNamespace(date=20260107, close=10.4, amount=130.0),
        ]
        signals = ENTRY.build_ai_signals(
            bars,
            {"20260106"},
            {"trend_filter": "none", "volume_ratio": 0.0},
        )
        self.assertEqual(signals, [False, True, False])

    def test_trend_filter_uses_only_values_available_on_signal_day(self):
        bars = [
            SimpleNamespace(date=20260100 + index, close=float(index), amount=100.0)
            for index in range(1, 26)
        ]
        signals = ENTRY.build_ai_signals(
            bars,
            {str(bars[-1].date)},
            {"trend_filter": "ma20_rising", "volume_ratio": 0.0},
        )
        self.assertTrue(signals[-1])
        self.assertFalse(any(signals[:-1]))

    def test_trade_metrics_report_payoff_ratio(self):
        trades = [
            SimpleNamespace(net_return=0.10),
            SimpleNamespace(net_return=0.05),
            SimpleNamespace(net_return=-0.05),
            SimpleNamespace(net_return=-0.10),
        ]
        metrics = ENTRY.ai_trade_metrics(trades)
        self.assertAlmostEqual(metrics["win_rate"], 0.5)
        self.assertAlmostEqual(metrics["average_win"], 0.075)
        self.assertAlmostEqual(metrics["average_loss"], 0.075)
        self.assertAlmostEqual(metrics["payoff_ratio"], 1.0)

    def test_dual_objective_penalizes_tiny_samples(self):
        tiny = ENTRY.dual_objective(
            {"trade_count": 3, "win_rate": 0.9, "payoff_ratio": 3.0, "profit_factor": 4.0, "max_drawdown": -0.02},
            minimum_trades=20,
        )
        stable = ENTRY.dual_objective(
            {"trade_count": 40, "win_rate": 0.6, "payoff_ratio": 1.5, "profit_factor": 2.0, "max_drawdown": -0.08},
            minimum_trades=20,
        )
        self.assertGreater(stable, tiny)


class SkillContractDocumentationTests(unittest.TestCase):
    def test_ai_formula_backtest_contract_is_documented(self):
        documents = [
            (ROOT / "SKILL.md").read_text(encoding="utf-8"),
            (ROOT / "references" / "business_spec.md").read_text(encoding="utf-8"),
            (ROOT / "references" / "workflow.md").read_text(encoding="utf-8"),
        ]
        combined = "\n".join(documents)
        for phrase in ("黄金点火AI", "条件选股公式", "XG", "双目标", "不改写"):
            self.assertIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
