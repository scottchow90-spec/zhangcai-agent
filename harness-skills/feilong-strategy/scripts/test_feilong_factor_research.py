from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from feilong_factor_research import (
    benjamini_hochberg,
    binary_stat,
    build_market_breadth,
    holdout_validation_status,
    numeric_stat,
)
from feilong_offline_replay import DAY_RECORD


class FeilongFactorResearchTests(unittest.TestCase):
    def test_benjamini_hochberg_is_monotone_in_p_order(self) -> None:
        p_values = [0.04, 0.001, 0.02, float("nan")]
        adjusted = benjamini_hochberg(p_values)
        ordered = sorted(
            (p_values[index], adjusted[index])
            for index in range(3)
        )
        self.assertTrue(all(left[1] <= right[1] for left, right in zip(ordered, ordered[1:])))
        self.assertTrue(np.isnan(adjusted[3]))

    def test_numeric_stat_detects_positive_direction(self) -> None:
        frame = pd.DataFrame(
            {
                "first_board_date": [f"20260{1 + index // 10:02d}{1 + index % 10:02d}" for index in range(40)],
                "factor": list(range(20)) + list(range(30, 50)),
                "outcome": [False] * 20 + [True] * 20,
            }
        )
        result = numeric_stat(frame, "factor", "测试因子", "outcome", "scope")
        self.assertGreater(result["cliff_delta"], 0.5)
        self.assertGreater(result["positive_median"], result["negative_median"])

    def test_binary_stat_uses_outcome_rate_by_factor_state(self) -> None:
        frame = pd.DataFrame(
            {
                "first_board_date": [f"20260{1 + index // 10:02d}{1 + index % 10:02d}" for index in range(40)],
                "factor": [False] * 20 + [True] * 20,
                "outcome": [False] * 16 + [True] * 4 + [False] * 4 + [True] * 16,
            }
        )
        result = binary_stat(frame, "factor", "测试条件", "outcome", "scope")
        self.assertAlmostEqual(result["factor_true_outcome_rate"], 0.8)
        self.assertAlmostEqual(result["factor_false_outcome_rate"], 0.2)
        self.assertGreater(result["odds_ratio"], 1.0)

    def test_market_breadth_reads_only_binary_event_window(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "vipdoc" / "sh" / "lday" / "sh600001.day"
            path.parent.mkdir(parents=True)
            records = b"".join(
                DAY_RECORD.pack(date, close, close, close, close, amount, 1000, 0)
                for date, close, amount in (
                    (20251231, 1000, 100000.0),
                    (20260102, 1100, 200000.0),
                    (20260105, 1080, 300000.0),
                )
            )
            path.write_bytes(records)
            frame, evidence = build_market_breadth(
                Path(temporary), {"20260102", "20260105"}
            )

        self.assertEqual(evidence["readable_day_file_count"], 1)
        self.assertAlmostEqual(frame.loc["20260102", "market_median_return_pct"], 10.0)
        self.assertEqual(frame.loc["20260102", "market_ge_9_8_count"], 1)
        self.assertLess(frame.loc["20260105", "market_median_return_pct"], 0.0)

    def test_holdout_requires_positive_lift_and_significance(self) -> None:
        self.assertEqual(holdout_validation_status(0.60, 0.40, 0.04), "CLEAN_PASS")
        self.assertEqual(
            holdout_validation_status(0.389, 0.50, 0.852),
            "REJECTED_NO_OUT_OF_TIME_LIFT",
        )
        self.assertEqual(
            holdout_validation_status(0.60, 0.40, 0.20),
            "REJECTED_NO_OUT_OF_TIME_LIFT",
        )


if __name__ == "__main__":
    unittest.main()
