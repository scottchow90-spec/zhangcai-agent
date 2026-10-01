from __future__ import annotations

import unittest

import pandas as pd

from feilong_continuation_research import (
    first_board_flags,
    limit_up_flags,
    max_consecutive_boards,
    threshold_row,
)


class FeilongContinuationResearchTests(unittest.TestCase):
    def test_main_board_limit_price_uses_fen_rounding(self) -> None:
        bars = pd.DataFrame(
            {
                "open": [10.03, 11.03, 12.13],
                "high": [10.03, 11.03, 12.13],
                "low": [10.03, 11.03, 12.13],
                "close": [10.03, 11.03, 12.13],
                "amount": [1.0, 1.0, 1.0],
                "volume": [1.0, 1.0, 1.0],
            },
            index=["20260101", "20260102", "20260105"],
        )
        flags = limit_up_flags(bars, "600001")
        self.assertFalse(bool(flags.iloc[0]))
        self.assertTrue(bool(flags.iloc[1]))
        self.assertTrue(bool(flags.iloc[2]))

    def test_first_board_and_consecutive_labels_are_distinct(self) -> None:
        limit_up = pd.Series(
            [False, True, True, True, False, True],
            index=[f"2026010{index + 1}" for index in range(6)],
        )
        first = first_board_flags(limit_up)
        self.assertTrue(bool(first.iloc[1]))
        self.assertFalse(bool(first.iloc[2]))
        self.assertEqual(max_consecutive_boards(limit_up, 1), 3)
        self.assertEqual(max_consecutive_boards(limit_up, 5), 1)

    def test_limit_up_after_one_break_is_a_new_first_board(self) -> None:
        limit_up = pd.Series([True, False, True])
        first = first_board_flags(limit_up)
        self.assertTrue(bool(first.iloc[0]))
        self.assertFalse(bool(first.iloc[1]))
        self.assertTrue(bool(first.iloc[2]))

    def test_threshold_row_selects_higher_quartile_when_rate_is_higher(self) -> None:
        frame = pd.DataFrame(
            {
                "first_board_date": [f"20260{1 + index // 20:02d}{1 + index % 20:02d}" for index in range(80)],
                "factor": list(range(80)),
                "reach2": [False] * 40 + [True] * 40,
            }
        )
        row = threshold_row(
            frame,
            factor="factor",
            factor_cn="测试因子",
            outcome="reach2",
            scope="测试",
            factor_type="numeric",
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["favorable_direction"], "higher")
        self.assertGreater(row["favorable_rate"], row["unfavorable_rate"])


if __name__ == "__main__":
    unittest.main()
