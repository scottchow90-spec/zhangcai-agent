from __future__ import annotations

import datetime as dt
import importlib.util
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "scripts" / "scientific_engine.py"
SPEC = importlib.util.spec_from_file_location("scientific_engine_tdx_preparation", ENGINE_PATH)
ENGINE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(ENGINE)


def range_rows(count: int = 260) -> list[dict]:
    rows: list[dict] = []
    trading_days: list[dt.date] = []
    day = dt.date.today()
    while len(trading_days) < count:
        if day.weekday() < 5:
            trading_days.append(day)
        day -= dt.timedelta(days=1)
    trading_days.reverse()
    previous = 100.0
    for index, trading_day in enumerate(trading_days):
        close = 100.0 + 4.0 * math.sin(index * math.pi / 16.0)
        rows.append(
            {
                "date": trading_day.isoformat(),
                "open": previous,
                "high": max(previous, close) + 0.8,
                "low": min(previous, close) - 0.8,
                "close": close,
                "volume": 1_000_000 + index * 100,
                "amount": 0,
            }
        )
        previous = close
    return rows


class TdxHistoryPreparationTests(unittest.TestCase):
    def test_repairs_ohlc_envelope_from_existing_open_close_with_audit(self) -> None:
        rows = range_rows()
        rows[40]["high"] = rows[40]["close"] - 0.25
        rows[70]["low"] = rows[70]["open"] + 0.25

        prepared, audit = ENGINE.prepare_tdx_history(rows)

        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["ohlc_envelope_repair_count"], 2)
        self.assertGreaterEqual(prepared[40]["high"], prepared[40]["close"])
        self.assertLessEqual(prepared[70]["low"], prepared[70]["open"])
        ENGINE.normalize_rows(prepared)

    def test_back_adjusts_corporate_action_gap_and_preserves_all_rows(self) -> None:
        rows = range_rows()
        split_index = 90
        for row in rows[split_index:]:
            for field in ("open", "high", "low", "close"):
                row[field] *= 0.5

        prepared, audit = ENGINE.prepare_tdx_history(rows)

        self.assertEqual(len(prepared), len(rows))
        self.assertEqual(audit["price_adjustment_event_count"], 1)
        self.assertAlmostEqual(prepared[split_index - 1]["close"], prepared[split_index]["open"], places=6)
        normalized, quality = ENGINE.normalize_rows(prepared)
        self.assertEqual(len(normalized), len(rows))
        self.assertEqual(quality["status"], "PASS")

    def test_single_bad_tick_is_not_silently_treated_as_a_scale_change(self) -> None:
        rows = range_rows()
        bad_index = 90
        for field in ("open", "high", "low", "close"):
            rows[bad_index][field] *= 0.5

        prepared, audit = ENGINE.prepare_tdx_history(rows)

        self.assertEqual(audit["price_adjustment_event_count"], 0)
        self.assertEqual(len(audit["unresolved_scale_breaks"]), 2)
        with self.assertRaisesRegex(
            ENGINE.AnalysisBlocked,
            "possible_unadjusted_corporate_action_or_bad_tick",
        ):
            ENGINE.normalize_rows(prepared)

    def test_tdx_analysis_exposes_preparation_audit(self) -> None:
        rows = range_rows()
        split_index = 90
        for row in rows[split_index:]:
            for field in ("open", "high", "low", "close"):
                row[field] *= 0.5
        source = {
            "source_type": "tdx_local_hub",
            "history_scope": "FULL_LOCAL_TDX_FILE",
            "full_history_required": True,
            "full_history_verified": True,
            "records_returned": len(rows),
            "source_records_available": len(rows),
        }

        report = ENGINE.analyze(
            rows,
            "TEST.SZ",
            "pressure",
            source,
            perform_walk_forward=False,
        )

        audit = report["data_quality"]["tdx_history_preparation"]
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["price_adjustment_event_count"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
