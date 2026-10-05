import unittest

import numpy as np
import pandas as pd

from feilong_advanced_factor_research import (
    LC5_DTYPE,
    _lc5_date_codes,
    _trading_minutes_from_open,
    advanced_daily_feature_row,
    minute_feature_row,
    scan_interactions,
)


class FeilongAdvancedFactorResearchTests(unittest.TestCase):
    def test_lc5_date_decoder_keeps_day_inside_month_day_bits(self) -> None:
        bars = np.zeros(2, dtype=LC5_DTYPE)
        bars["date_word"] = np.array(
            [(2025 - 2004) * 2048 + 12 * 100 + 23, (2026 - 2004) * 2048 + 5 * 100 + 15]
        )
        np.testing.assert_array_equal(_lc5_date_codes(bars), np.array([20251223, 20260515]))

    def test_trading_minutes_exclude_lunch_break(self) -> None:
        actual = _trading_minutes_from_open(np.array([570, 690, 780, 900]))
        np.testing.assert_array_equal(actual, np.array([0, 120, 120, 240]))

    def test_daily_features_do_not_read_bars_after_event(self) -> None:
        dates = pd.date_range("2025-01-01", periods=90, freq="B").strftime("%Y%m%d")
        close = pd.Series(np.linspace(8.0, 12.0, len(dates)), index=dates)
        frame = pd.DataFrame(
            {
                "open": close * 0.995,
                "high": close * 1.01,
                "low": close * 0.99,
                "close": close,
                "amount": np.linspace(5e7, 9e7, len(dates)),
                "volume": np.linspace(8e4, 12e4, len(dates)),
            },
            index=dates,
        )
        event_date = dates[65]
        before = advanced_daily_feature_row(frame, event_date)
        changed = frame.copy()
        changed.loc[dates[66]:, ["open", "high", "low", "close"]] *= 10
        after = advanced_daily_feature_row(changed, event_date)
        for key in before:
            if np.isnan(before[key]):
                self.assertTrue(np.isnan(after[key]))
            else:
                self.assertAlmostEqual(before[key], after[key], places=10)

    def test_minute_features_capture_break_and_reseal(self) -> None:
        bars = np.zeros(48, dtype=LC5_DTYPE)
        bars["minute_word"] = np.arange(575, 575 + 48 * 5, 5)
        bars["open"] = 9.5
        bars["high"] = 9.8
        bars["low"] = 9.4
        bars["close"] = 9.6
        bars["amount"] = 1e6
        bars["volume"] = 100000
        bars["high"][10:] = 10.0
        bars["close"][10:] = 10.0
        bars["close"][20:25] = 9.9
        result = minute_feature_row(bars, 10.0)
        self.assertEqual(result["seal_first_minutes"], 55)
        self.assertEqual(result["reseal_count"], 2)
        self.assertEqual(result["final_lock_bars"], 23)
        self.assertGreater(result["post_hit_broken_ratio"], 0)
        self.assertAlmostEqual(result["close_vwap_premium_lc5_pct"], 0.0, places=7)

    def test_interaction_scan_finds_cross_family_rule(self) -> None:
        rows = []
        rng = np.random.default_rng(20260830)
        months = ["202601", "202602", "202603", "202604", "202605", "202606", "202607"]
        for month_index, month in enumerate(months):
            for value in range(120):
                factor_a = rng.uniform()
                factor_b = rng.uniform()
                interaction = factor_a <= 0.45 and factor_b >= 0.55
                baseline = (value + month_index) % 17 == 0
                rows.append(
                    {
                        "month": month,
                        "first_board_date": f"{month}{value % 20 + 1:02d}",
                        "symbol": f"{month_index:02d}{value:04d}.SZ",
                        "factor_a": factor_a,
                        "factor_b": factor_b,
                        "reach2": interaction or baseline,
                        "reach3": interaction and value % 3 == 0,
                    }
                )
        frame = pd.DataFrame(rows)
        specs = {
            "factor_a": {"name": "甲", "family": "路径", "type": "numeric"},
            "factor_b": {"name": "乙", "family": "环境", "type": "numeric"},
        }
        result, diagnostics, _masks = scan_interactions(
            frame,
            specs,
            outcome="reach2",
            max_order=2,
            minimum_selected=25,
            required_positive_folds=3,
        )
        self.assertEqual(diagnostics["interaction_rules_tested"], 1)
        self.assertEqual(len(result), 1)
        self.assertGreater(result.iloc[0]["selected_rate"], result.iloc[0]["complement_rate"])
        self.assertGreaterEqual(result.iloc[0]["positive_folds"], 3)


if __name__ == "__main__":
    unittest.main()
