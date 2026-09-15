from __future__ import annotations

import unittest

import pandas as pd

from feilong_resonance_exhaustive import (
    chronological_split,
    classify_columns,
    enumerate_numeric_rules,
    rule_mask,
)


class FeilongResonanceExhaustiveTests(unittest.TestCase):
    def test_numeric_search_enumerates_every_valid_split_in_both_directions(self) -> None:
        frame = pd.DataFrame(
            {
                "factor": list(range(10)),
                "reach2": [False, False, False, False, False, True, True, True, True, True],
            }
        )
        result = enumerate_numeric_rules(
            frame,
            factor="factor",
            outcome="reach2",
            scope="test",
            minimum_support=2,
        )
        self.assertEqual(len(result), 14)
        self.assertEqual(set(result["direction"]), {"le", "ge"})
        self.assertEqual(result.loc[result["direction"].eq("le"), "threshold"].tolist(), list(range(1, 8)))
        self.assertEqual(result.loc[result["direction"].eq("ge"), "threshold"].tolist(), list(range(2, 9)))

    def test_chronological_split_never_splits_the_same_date(self) -> None:
        frame = pd.DataFrame(
            {
                "first_board_date": ["20260101"] * 3 + ["20260102"] * 3 + ["20260103"] * 4,
            }
        )
        train, validation, cutoff = chronological_split(frame, train_share=0.50)
        self.assertEqual(cutoff, "20260102")
        self.assertEqual(set(frame.loc[train, "first_board_date"]), {"20260101", "20260102"})
        self.assertEqual(set(frame.loc[validation, "first_board_date"]), {"20260103"})

    def test_column_classification_excludes_identity_outcome_selection_and_constants(self) -> None:
        frame = pd.DataFrame(
            {
                "symbol": ["000001.SZ", "000002.SZ"],
                "first_board_date": ["20260101", "20260102"],
                "reach2": [True, False],
                "formula_signal": [True, True],
                "one_price_board": [True, False],
                "numeric_factor": [1.0, 2.0],
                "constant_factor": [7.0, 7.0],
                "tdx_industry": ["银行", "地产"],
            }
        )
        candidates, excluded = classify_columns(frame)
        reasons = {row["column"]: row["reason"] for row in excluded}
        self.assertEqual(candidates["one_price_board"], "binary")
        self.assertEqual(candidates["numeric_factor"], "numeric")
        self.assertEqual(candidates["tdx_industry"], "categorical")
        self.assertEqual(reasons["symbol"], "identity")
        self.assertEqual(reasons["reach2"], "post_event_or_outcome")
        self.assertEqual(reasons["formula_signal"], "selection_or_status")
        self.assertEqual(reasons["constant_factor"], "constant")

    def test_rule_mask_keeps_missing_values_out_of_both_groups(self) -> None:
        frame = pd.DataFrame({"factor": [1.0, 2.0, None, 4.0]})
        selected, available = rule_mask(
            frame,
            {
                "factor": "factor",
                "factor_type": "numeric",
                "direction": "le",
                "threshold": 2.0,
            },
        )
        self.assertEqual(selected.tolist(), [True, True, False, False])
        self.assertEqual(available.tolist(), [True, True, False, True])


if __name__ == "__main__":
    unittest.main()

