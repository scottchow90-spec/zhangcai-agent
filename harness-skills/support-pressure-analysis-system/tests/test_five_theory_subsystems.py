from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import datetime as dt
import importlib.util
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "scripts" / "scientific_engine.py"
SPEC = importlib.util.spec_from_file_location("scientific_engine_five_theory", ENGINE_PATH)
ENGINE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ENGINE)


def rows_from_anchors(
    anchors: list[float],
    *,
    scale: float = 1.0,
    bars_per_leg: int = 5,
    base_volume: float = 1_000_000,
) -> list[dict]:
    closes: list[float] = []
    for left, right in zip(anchors, anchors[1:]):
        for step in range(bars_per_leg):
            closes.append(left + (right - left) * step / bars_per_leg)
    closes.append(anchors[-1])
    rows: list[dict] = []
    day = dt.date(2024, 1, 2)
    previous = closes[0]
    for index, close in enumerate(closes):
        while day.weekday() >= 5:
            day += dt.timedelta(days=1)
        open_price = previous
        high = max(open_price, close) + 0.35
        low = min(open_price, close) - 0.35
        rows.append(
            {
                "date": day.isoformat(),
                "open": open_price * scale,
                "high": high * scale,
                "low": low * scale,
                "close": close * scale,
                "volume": base_volume * (1.0 + (index % 7) * 0.03),
                "amount": 0,
            }
        )
        previous = close
        day += dt.timedelta(days=1)
    return rows


def repeating_range_rows(count: int = 420) -> list[dict]:
    day = dt.date(2024, 1, 2)
    rows: list[dict] = []
    previous = 100.0
    index = 0
    while len(rows) < count:
        if day.weekday() < 5:
            close = 100.0 + 5.0 * math.sin(index * math.pi / 10.0)
            rows.append(
                {
                    "date": day.isoformat(),
                    "open": previous,
                    "high": max(previous, close) + 0.5,
                    "low": min(previous, close) - 0.5,
                    "close": close,
                    "volume": 1_000_000 + (index % 20) * 25_000,
                    "amount": 0,
                }
            )
            previous = close
            index += 1
        day += dt.timedelta(days=1)
    return rows


class FiveTheorySubsystemTests(unittest.TestCase):
    def test_elliott_searches_all_confirmed_pivots_from_full_input(self) -> None:
        normalized, _ = ENGINE.normalize_rows(repeating_range_rows(420))
        atr_values = ENGINE._atr_series(normalized)
        pivots = ENGINE._alternating_pivots(normalized, atr_values, 2)
        result = ENGINE.elliott_subsystem(normalized, atr_values)
        self.assertEqual(result["input_bar_count"], len(normalized))
        self.assertEqual(result["input_start_date"], normalized[0]["date"])
        self.assertEqual(result["input_end_date"], normalized[-1]["date"])
        self.assertEqual(result["search_scope"], "ALL_CONFIRMED_ALTERNATING_PIVOTS")
        self.assertEqual(result["confirmed_pivot_count"], len(pivots))
        self.assertEqual(result["candidate_window_count"], max(0, len(pivots) - 5))
        self.assertGreater(result["confirmed_pivot_count"], 14)

    def test_elliott_is_bidirectional_and_uses_temporal_pivots(self) -> None:
        self.assertTrue(hasattr(ENGINE, "elliott_subsystem"))
        upward, _ = ENGINE.normalize_rows(
            rows_from_anchors([105, 100, 108, 104, 116, 110, 121, 115]), min_bars=20
        )
        downward, _ = ENGINE.normalize_rows(
            rows_from_anchors([116, 121, 113, 117, 105, 111, 99, 104]), min_bars=20
        )
        up = ENGINE.elliott_subsystem(upward, ENGINE._atr_series(upward))
        down = ENGINE.elliott_subsystem(downward, ENGINE._atr_series(downward))
        self.assertEqual(up["status"], "PASS")
        self.assertEqual(down["status"], "PASS")
        self.assertEqual(up["direction"], "up")
        self.assertEqual(down["direction"], "down")
        self.assertGreaterEqual(len(up["wave_points"]), 6)
        self.assertEqual(
            [point["index"] for point in up["wave_points"]],
            sorted(point["index"] for point in up["wave_points"]),
        )
        self.assertTrue(all(point["confirmed"] for point in up["wave_points"]))

    def test_chan_builds_confirmed_fractals_strokes_and_central_zones(self) -> None:
        self.assertTrue(hasattr(ENGINE, "chan_subsystem"))
        normalized, _ = ENGINE.normalize_rows(
            rows_from_anchors([100, 110, 102, 109, 101, 108, 103, 111, 104, 112]), min_bars=20
        )
        result = ENGINE.chan_subsystem(normalized, ENGINE._atr_series(normalized))
        self.assertEqual(result["status"], "PASS")
        self.assertGreaterEqual(len(result["fractals"]), 6)
        self.assertGreaterEqual(len(result["strokes"]), 5)
        self.assertTrue(all(stroke["end_index"] > stroke["start_index"] for stroke in result["strokes"]))
        self.assertTrue(all(
            left["direction"] != right["direction"]
            for left, right in zip(result["strokes"], result["strokes"][1:])
        ))
        self.assertTrue(result["central_zones"])
        self.assertIn(result["buy_sell_state"], {"buy_watch", "sell_watch", "neutral"})

    def test_fibonacci_is_directional_and_scale_invariant(self) -> None:
        self.assertTrue(hasattr(ENGINE, "fibonacci_subsystem"))
        base, _ = ENGINE.normalize_rows(rows_from_anchors([100, 120, 108, 130, 116, 136]), min_bars=20)
        scaled, _ = ENGINE.normalize_rows(rows_from_anchors([100, 120, 108, 130, 116, 136], scale=10.0), min_bars=20)
        first = ENGINE.fibonacci_subsystem(base, ENGINE._atr_series(base))
        second = ENGINE.fibonacci_subsystem(scaled, ENGINE._atr_series(scaled))
        self.assertEqual(first["status"], "PASS")
        self.assertGreaterEqual(len(first["candidate_levels"]), 5)
        self.assertGreater(first["cluster_tolerance"], 0)
        self.assertAlmostEqual(
            second["cluster_tolerance"] / first["cluster_tolerance"], 10.0, places=2
        )
        base_levels = sorted(item["level"] for item in first["candidate_levels"])
        scaled_levels = sorted(item["level"] for item in second["candidate_levels"])
        self.assertAlmostEqual(scaled_levels[0] / base_levels[0], 10.0, places=2)
        self.assertIn(first["active_swing"]["direction"], {"up", "down"})

    def test_gann_score_is_derived_not_constant(self) -> None:
        self.assertTrue(hasattr(ENGINE, "gann_subsystem"))
        trending, _ = ENGINE.normalize_rows(rows_from_anchors([80, 88, 84, 94, 90, 101]), min_bars=20)
        ranging, _ = ENGINE.normalize_rows(rows_from_anchors([100, 102, 99, 101, 98, 100]), min_bars=20)
        trend_result = ENGINE.gann_subsystem(trending, ENGINE._atr_series(trending))
        range_result = ENGINE.gann_subsystem(ranging, ENGINE._atr_series(ranging))
        self.assertEqual(trend_result["status"], "PASS")
        self.assertTrue(trend_result["square_of_nine_levels"])
        self.assertTrue(trend_result["angle_levels"])
        self.assertNotEqual(
            trend_result["evidence_score_not_probability"],
            range_result["evidence_score_not_probability"],
        )
        self.assertTrue(all(item["level"] > 0 for item in trend_result["candidate_levels"]))

    def test_wyckoff_uses_prior_range_for_spring_and_acceptance(self) -> None:
        self.assertTrue(hasattr(ENGINE, "wyckoff_subsystem"))
        rows = rows_from_anchors([100, 102, 99, 101, 98.5, 101, 99, 102], bars_per_leg=5)
        spring_index = len(rows)
        last_date = dt.date.fromisoformat(rows[-1]["date"])
        rows.extend(
            [
                {
                    "date": (last_date + dt.timedelta(days=1)).isoformat(),
                    "open": 99.0,
                    "high": 100.5,
                    "low": 96.5,
                    "close": 99.6,
                    "volume": 3_500_000,
                    "amount": 0,
                },
                {
                    "date": (last_date + dt.timedelta(days=2)).isoformat(),
                    "open": 99.6,
                    "high": 101.4,
                    "low": 99.2,
                    "close": 101.0,
                    "volume": 2_000_000,
                    "amount": 0,
                },
            ]
        )
        normalized, _ = ENGINE.normalize_rows(rows, min_bars=30)
        result = ENGINE.wyckoff_subsystem(normalized, ENGINE._atr_series(normalized))
        self.assertEqual(result["status"], "PASS")
        springs = [event for event in result["events"] if event["type"] == "spring"]
        self.assertTrue(springs)
        self.assertEqual(springs[-1]["index"], spring_index)
        self.assertTrue(springs[-1]["accepted"])
        self.assertIn("range_lower", springs[-1])

    def test_five_subsystems_are_present_in_formal_main_chain(self) -> None:
        self.assertTrue(hasattr(ENGINE, "five_theory_subsystems"))
        report = ENGINE.analyze(
            repeating_range_rows(),
            "TEST",
            "pressure",
            {"source_type": "synthetic"},
            perform_walk_forward=False,
        )
        expected = {"elliott_wave", "chan_structure", "fibonacci", "gann", "wyckoff"}
        self.assertEqual(set(report["theory_subsystems"]), expected)
        for subsystem in report["theory_subsystems"].values():
            self.assertEqual(subsystem["status"], "PASS")
            self.assertTrue(subsystem["active_in_main_chain"])
            self.assertIn("candidate_levels", subsystem)
            self.assertIn("limitations", subsystem)
        self.assertGreater(report["level_construction"]["theory_candidate_count"], 0)
        families = set(report["level_construction"]["independent_evidence_families"])
        self.assertTrue(any(family.startswith("theory_") for family in families))
        self.assertEqual(report["conclusion"]["directional_prediction"], "NOT_CLAIMED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
