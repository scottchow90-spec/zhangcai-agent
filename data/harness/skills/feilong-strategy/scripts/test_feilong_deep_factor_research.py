from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from feilong_deep_factor_research import (
    best_numeric_rule,
    board_regime,
    deep_tdx_feature_row,
    nested_out_of_time_score,
    robust_intersection_analysis,
    rolling_factor_scan,
    sample_audit,
)


class FeilongDeepFactorResearchTests(unittest.TestCase):
    def test_board_regimes_are_separated(self) -> None:
        self.assertEqual(board_regime("000001"), "主板10%")
        self.assertEqual(board_regime("300001"), "创业板20%")
        self.assertEqual(board_regime("688001"), "科创板20%")
        self.assertEqual(board_regime("830001"), "北交所30%")

    def test_numeric_rule_never_selects_more_than_seventy_percent(self) -> None:
        frame = pd.DataFrame(
            {
                "factor": np.arange(100, dtype=float),
                "reach2": [False] * 70 + [True] * 30,
            }
        )
        rule, tested = best_numeric_rule(
            frame,
            factor="factor",
            outcome="reach2",
            minimum_support=10,
        )
        self.assertGreater(tested, 0)
        self.assertIsNotNone(rule)
        assert rule is not None
        selected_share = rule["train_selected_n"] / (
            rule["train_selected_n"] + rule["train_complement_n"]
        )
        self.assertLessEqual(selected_share, 0.70)
        self.assertEqual(rule["direction"], "ge")

    def test_deep_features_do_not_use_future_bars(self) -> None:
        dates = pd.date_range("2026-01-01", periods=70, freq="D").strftime("%Y%m%d")
        close = pd.Series(np.linspace(10.0, 16.9, 70), index=dates)
        bars = pd.DataFrame(
            {
                "open": close - 0.1,
                "high": close + 0.3,
                "low": close - 0.2,
                "close": close,
                "volume": np.linspace(1000.0, 3000.0, 70),
                "amount": np.linspace(1_000_000.0, 4_000_000.0, 70),
            },
            index=dates,
        )
        event_date = dates[45]
        truncated = bars.loc[:event_date].copy()
        future_changed = bars.copy()
        future_changed.loc[future_changed.index > event_date, ["open", "high", "low", "close"]] *= 1000
        future_changed.loc[future_changed.index > event_date, ["volume", "amount"]] *= 1_000_000
        left = deep_tdx_feature_row(truncated, event_date, active_capital_10k_shares=None)
        right = deep_tdx_feature_row(future_changed, event_date, active_capital_10k_shares=None)
        for key in left:
            if pd.isna(left[key]) and pd.isna(right[key]):
                continue
            self.assertEqual(left[key], right[key], key)

    def test_limited_history_keeps_same_day_checks_and_leaves_long_windows_missing(self) -> None:
        dates = pd.date_range("2026-01-01", periods=10, freq="D").strftime("%Y%m%d")
        close = pd.Series(np.linspace(10.0, 10.9, 10), index=dates)
        bars = pd.DataFrame(
            {
                "open": close - 0.05,
                "high": close + 0.2,
                "low": close - 0.1,
                "close": close,
                "volume": np.linspace(1000.0, 1900.0, 10),
                "amount": np.linspace(1_000_000.0, 1_900_000.0, 10),
            },
            index=dates,
        )
        row = deep_tdx_feature_row(bars, dates[6], active_capital_10k_shares=None)
        self.assertEqual(row["deep_history_days_available"], 6)
        self.assertTrue(pd.notna(row["check_intraday_range_pct"]))
        self.assertTrue(pd.notna(row["check_volume_vs_ma5"]))
        self.assertTrue(pd.isna(row["prior_max_drawdown_20d_pct"]))

    def test_rolling_scan_uses_only_earlier_months(self) -> None:
        rows = []
        for month_index, month in enumerate(["202601", "202602", "202603", "202604", "202605", "202606", "202607"]):
            for value in range(80):
                rows.append(
                    {
                        "month": month,
                        "factor": float(value),
                        "reach2": value >= 60,
                        "reach3": value >= 70,
                        "first_board_date": f"{month}{value % 28 + 1:02d}",
                        "symbol": f"{month_index:02d}{value:04d}.SZ",
                    }
                )
        frame = pd.DataFrame(rows)
        detail, _aggregate, _masks, folds, _tested = rolling_factor_scan(
            frame,
            {"factor": {"type": "numeric", "name": "测试因子", "family": "测试", "root_factor": "factor"}},
        )
        self.assertTrue((detail["train_end"] < detail["test_month"]).all())
        self.assertTrue(all(fold["train_end"] < fold["test_month"] for fold in folds))

    def test_nested_score_rejects_a_ninety_percent_coverage_rule(self) -> None:
        train_n, test_n = 200, 40
        frame = pd.DataFrame(
            {
                "month": ["202603"] * train_n + ["202604"] * test_n,
                "symbol": [f"{index:06d}.SZ" for index in range(train_n + test_n)],
                "code": [f"{index:06d}" for index in range(train_n + test_n)],
                "first_board_date": ["20260315"] * train_n + ["20260415"] * test_n,
                "migrated_158": False,
                "reach2": ([False, True] * ((train_n + test_n) // 2)),
                "broad": [1] * 180 + [0] * 20 + [1] * 36 + [0] * 4,
                "valid_a": ([0, 1] * (train_n // 2)) + ([0, 1] * (test_n // 2)),
                "valid_b": ([0, 0, 1, 1] * (train_n // 4)) + ([0, 0, 1, 1] * (test_n // 4)),
                "valid_c": ([0, 1, 1, 0] * (train_n // 4)) + ([0, 1, 1, 0] * (test_n // 4)),
            }
        )
        detail_rows = []
        for factor, family, selected_n, complement_n, score in (
            ("broad", "宽覆盖", 180, 20, 99.0),
            ("valid_a", "甲", 100, 100, 10.0),
            ("valid_b", "乙", 100, 100, 9.0),
            ("valid_c", "丙", 100, 100, 8.0),
        ):
            detail_rows.append(
                {
                    "outcome": "reach2",
                    "test_month": "202604",
                    "factor": factor,
                    "factor_name": factor,
                    "factor_type": "binary",
                    "family": family,
                    "direction": "eq",
                    "threshold": True,
                    "train_rate_difference": 0.05,
                    "train_selected_n": selected_n,
                    "train_complement_n": complement_n,
                    "train_score": score,
                }
            )
        specs = {
            row["factor"]: {"name": row["factor_name"], "family": row["family"], "type": "binary", "root_factor": row["factor"]}
            for row in detail_rows
        }
        _bands, selections, diagnostics = nested_out_of_time_score(frame, pd.DataFrame(detail_rows), specs)
        self.assertEqual(diagnostics["status"], "CLEAN_PASS")
        self.assertNotIn("broad", set(selections["factor"]))

    def test_positive_case_audit_does_not_treat_158_as_denominator(self) -> None:
        frame = pd.DataFrame(
            {
                "formula_signal": [True] * 5,
                "one_price_board": [False] * 5,
                "migrated_158": [True, True, True, False, False],
                "reach3": [True, True, True, True, False],
                "symbol": ["000001.SZ", "000001.SZ", "000002.SZ", "000003.SZ", "000004.SZ"],
                "first_board_date": ["20260101", "20260102", "20260103", "20260104", "20260105"],
            }
        )
        audit = sample_audit(frame)
        self.assertTrue(audit["migrated_is_positive_only_case_set"])
        self.assertEqual(audit["formula_reach3_n"], 4)
        self.assertEqual(audit["formula_reach3_outside_migrated_n"], 1)
        self.assertAlmostEqual(audit["migrated_coverage_of_formula_reach3"], 0.75)

    def test_robust_intersection_is_measured_only_on_out_of_time_months(self) -> None:
        rows = []
        for month_index, month in enumerate(["202601", "202602", "202603", "202604", "202605", "202606"]):
            for value in range(40):
                first = value < 20
                second = value % 4 < 2
                rows.append(
                    {
                        "month": month,
                        "first_board_date": f"{month}{value % 20 + 1:02d}",
                        "symbol": f"{month_index:02d}{value:04d}.SZ",
                        "reach2": first and second,
                        "reach3": first and second and value % 8 == 0,
                        "migrated_158": False,
                        "first": first,
                        "second": second,
                    }
                )
        frame = pd.DataFrame(rows)
        aggregate = pd.DataFrame(
            [
                {
                    "outcome": "reach2",
                    "factor": factor,
                    "factor_name": name,
                    "evidence_grade": "深度稳健",
                    "cluster_representative": True,
                    "cluster_q_value": 0.01,
                    "oot_rate_difference": difference,
                }
                for factor, name, difference in (("first", "甲", 0.2), ("second", "乙", 0.1))
            ]
        )
        oot_index = frame.index[frame["month"].isin(["202604", "202605", "202606"])]
        masks = {
            "reach2": {
                factor: (
                    frame.loc[oot_index, factor].astype(bool),
                    pd.Series(True, index=oot_index),
                )
                for factor in ("first", "second")
            },
            "reach3": {},
        }
        summary, bands, months = robust_intersection_analysis(
            frame,
            aggregate,
            masks,
            repetitions=100,
        )
        self.assertEqual(len(summary), 1)
        self.assertEqual(int(summary.iloc[0]["month_count"]), 3)
        self.assertEqual(int(summary.iloc[0]["selected_n"]), 30)
        self.assertEqual(set(months["month"]), {"202604", "202605", "202606"})
        self.assertEqual(set(bands["condition_score"]), {0, 1, 2})


if __name__ == "__main__":
    unittest.main()
