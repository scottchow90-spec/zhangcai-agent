from __future__ import annotations

import math
import unittest

import numpy as np
import pandas as pd

from feilong_factor_correlation_research import (
    FACTOR_SPECS,
    _cluster_bootstrap_corr,
    _plain_corr,
    factor_row,
    listing_age_days,
)


class FactorCorrelationResearchTests(unittest.TestCase):
    def _bars(self, count: int = 320) -> pd.DataFrame:
        dates = pd.bdate_range("2024-01-02", periods=count).strftime("%Y%m%d")
        base = 10.0 + np.arange(count, dtype=float) * 0.01
        close = base + np.sin(np.arange(count) / 7.0) * 0.08
        open_ = close * (1.0 + np.cos(np.arange(count) / 11.0) * 0.002)
        high = np.maximum(open_, close) * 1.012
        low = np.minimum(open_, close) * 0.988
        volume = 1_000_000.0 + np.arange(count, dtype=float) * 2_000.0
        amount = volume * ((open_ + close + high + low) / 4.0)
        return pd.DataFrame(
            {"open": open_, "high": high, "low": low, "close": close, "amount": amount, "volume": volume},
            index=dates,
        )

    def test_factor_dictionary_exceeds_100_and_definitions_are_complete(self) -> None:
        self.assertGreaterEqual(len(FACTOR_SPECS), 100)
        self.assertGreaterEqual(len({row["family"] for row in FACTOR_SPECS.values()}), 10)
        self.assertTrue(all(row["definition"].strip() for row in FACTOR_SPECS.values()))
        self.assertTrue(all(row["available_at"] == "首板收盘后" for row in FACTOR_SPECS.values()))

    def test_factor_row_does_not_read_future_bars(self) -> None:
        bars = self._bars()
        date = str(bars.index[280])
        truncated = factor_row(bars.loc[:date].copy(), date)
        complete = factor_row(bars.copy(), date)
        self.assertEqual(set(truncated), set(complete))
        for key in truncated:
            left = truncated[key]
            right = complete[key]
            if isinstance(left, float) and math.isnan(left):
                self.assertTrue(isinstance(right, float) and math.isnan(right), key)
            else:
                self.assertAlmostEqual(float(left), float(right), places=12, msg=key)

    def test_short_history_keeps_long_windows_missing(self) -> None:
        bars = self._bars(40)
        date = str(bars.index[-1])
        row = factor_row(bars, date)
        self.assertTrue(math.isnan(row["prior_return_120d_pct"]))
        self.assertTrue(math.isnan(row["prior_gap_sum_20d_pct"]) is False)
        self.assertTrue(math.isnan(row["prior_limitup_age_120d"]))

    def test_listing_age_uses_actual_first_local_day_record(self) -> None:
        self.assertEqual(listing_age_days("20200102", "20240229"), 1519)
        with self.assertRaisesRegex(RuntimeError, "event_before_first_day_record"):
            listing_age_days("20240229", "20200102")

    def test_monthly_minimum_can_be_lower_than_full_sample_gate(self) -> None:
        x = pd.Series(np.arange(60, dtype=float))
        y = pd.Series(([0, 1] * 30), dtype=float)
        full = _plain_corr(x, y)
        monthly = _plain_corr(x, y, minimum_n=50)
        self.assertTrue(math.isnan(full[0]))
        self.assertTrue(math.isfinite(monthly[0]))

    def test_cluster_bootstrap_p_value_is_not_limited_by_repetition_grid(self) -> None:
        rng = np.random.default_rng(7)
        x = pd.Series(rng.normal(size=800))
        y = pd.Series((x + rng.normal(scale=0.6, size=800) > 0).astype(float))
        clusters = pd.Series(np.repeat(np.arange(80), 10))
        _low, _high, p_value = _cluster_bootstrap_corr(x, y, clusters, "strong-synthetic")
        self.assertLess(p_value, 1.0 / 501.0)


if __name__ == "__main__":
    unittest.main()
