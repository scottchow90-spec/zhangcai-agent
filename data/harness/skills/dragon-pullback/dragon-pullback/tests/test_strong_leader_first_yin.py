from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_strong_leader_first_yin.py"
SPEC = importlib.util.spec_from_file_location("strong_leader_first_yin", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def row(day: int, open_price: float, high: float, low: float, close: float, amount: float, volume: int):
    return {
        "date": f"202601{day:02d}",
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "amount": amount,
        "volume": volume,
    }


def passing_rows():
    rows = []
    close = 10.0
    for day in range(1, 31):
        open_price = close
        close = round(close + 0.03, 2)
        rows.append(row(day, open_price, close + 0.03, open_price - 0.03, close, 360_000_000, 30_000_000))
    for index in (25, 29):
        previous_close = rows[index - 1]["close"]
        close = MODULE.limit_price(previous_close, 0.10)
        rows[index] = row(index + 1, previous_close * 1.03, close, previous_close * 1.02, close, 520_000_000, 30_000_000)
    previous = rows[-1]
    current_open = round(previous["close"] * 1.01, 2)
    current_close = round(previous["close"] * 0.985, 2)
    rows.append(
        row(
            31,
            current_open,
            round(current_open * 1.005, 2),
            round(previous["low"] * 0.995, 2),
            current_close,
            390_000_000,
            21_000_000,
        )
    )
    return rows


class StrongLeaderFirstYinTests(unittest.TestCase):
    def setUp(self):
        self.meta = {"code": "002001", "float_shares": 500_000_000}

    def test_strict_candidate_has_every_condition(self):
        rows = passing_rows()
        result = MODULE.evaluate_at(rows, len(rows) - 1, self.meta)
        self.assertIsNotNone(result)
        self.assertTrue(result["strict"])
        self.assertTrue(all(result["strict_conditions"].values()))

    def test_excess_volume_rejects_strict_candidate(self):
        rows = passing_rows()
        rows[-1]["volume"] = 40_000_000
        result = MODULE.evaluate_at(rows, len(rows) - 1, self.meta)
        self.assertTrue(result is None or not result["strict"])

    def test_limit_price_uses_half_up_rounding(self):
        self.assertEqual(MODULE.limit_price(10.05, 0.10), 11.06)

    def test_high_turnover_leader_uses_separate_t_grade(self):
        rows = passing_rows()
        rows[21] = row(22, 9.0, 9.1, 8.9, 9.0, 360_000_000, 30_000_000)
        previous_close = rows[21]["close"]
        close = MODULE.limit_price(previous_close, 0.10)
        rows[22] = row(23, previous_close * 1.03, close, previous_close * 1.02, close, 520_000_000, 30_000_000)
        rows[-1]["volume"] = 40_500_000
        rows[-1]["amount"] = 1_500_000_000
        result = MODULE.evaluate_at(rows, len(rows) - 1, self.meta)
        self.assertIsNotNone(result)
        self.assertEqual(result["grade"], "T")
        self.assertTrue(result["turnover_divergence"])
        self.assertTrue(all(result["turnover_divergence_conditions"].values()))

    def test_candidate_groups_are_exclusive_by_assigned_grade(self):
        candidates = [
            {"grade": "T", "strict": False, "turnover_divergence": True, "practical": True},
            {"grade": "A", "strict": False, "turnover_divergence": False, "practical": True},
        ]

        groups = MODULE.partition_candidates(candidates)

        self.assertEqual(len(groups["strict"]), 0)
        self.assertEqual(len(groups["turnover_divergence"]), 1)
        self.assertEqual(len(groups["practical"]), 1)
        self.assertEqual(sum(len(group) for group in groups.values()), len(candidates))


if __name__ == "__main__":
    unittest.main()
