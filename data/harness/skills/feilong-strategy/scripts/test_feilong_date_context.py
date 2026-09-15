#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import unittest

from feilong_realtime_report import (
    REQUIRED_FORMULA_OUTPUTS,
    build_date_context,
    golden_cross_status,
    report_title,
)


def output_dates(*dates: str) -> dict[str, list[str]]:
    return {key: list(dates) for key in REQUIRED_FORMULA_OUTPUTS}


class DateContextTests(unittest.TestCase):
    def test_golden_cross_status_uses_fixed_public_terms(self) -> None:
        self.assertEqual(golden_cross_status(20.01, 20.0), "金叉")
        self.assertEqual(golden_cross_status(20.0, 20.0), "未形成金叉")
        self.assertEqual(golden_cross_status(19.99, 20.0), "未形成金叉")
        self.assertEqual(golden_cross_status(None, 20.0), "金叉状态不可判定")

    def test_explicit_as_of_matching_formula_and_kline_is_same_day(self) -> None:
        context = build_date_context(
            run_calendar_date="20260804",
            requested_as_of_date="20260804",
            output_dates=output_dates("20260804"),
            kline_dates=["20260804"],
            snapshot_available=True,
        )
        self.assertTrue(context["ok"])
        self.assertEqual(context["mode"], "same_day_realtime")
        self.assertEqual(context["analysis_as_of_date"], "20260804")

    def test_text_label_output_does_not_block_same_day_alignment(self) -> None:
        dates = output_dates("20260901")
        dates["OUTPUT6"] = []
        context = build_date_context(
            run_calendar_date="20260901",
            requested_as_of_date="20260901",
            output_dates=dates,
            kline_dates=["20260901"],
            snapshot_available=True,
        )
        self.assertTrue(context["ok"])
        self.assertTrue(context["formula_has_as_of"])
        self.assertEqual(context["mode"], "same_day_realtime")

    def test_midnight_run_uses_latest_common_trading_date_without_realtime_claim(self) -> None:
        context = build_date_context(
            run_calendar_date="20260805",
            requested_as_of_date=None,
            output_dates=output_dates("20260804"),
            kline_dates=["20260801", "20260804"],
            snapshot_available=True,
        )
        self.assertTrue(context["ok"])
        self.assertEqual(context["mode"], "as_of_close")
        self.assertEqual(context["analysis_as_of_date"], "20260804")
        self.assertIn("截至 2026-08-04 分析", report_title("测试股", "000001.SZ", context))
        self.assertNotIn("今日实时分析", report_title("测试股", "000001.SZ", context))

    def test_stale_data_cannot_satisfy_requested_as_of_date(self) -> None:
        context = build_date_context(
            run_calendar_date="20260804",
            requested_as_of_date="20260804",
            output_dates=output_dates("20260801"),
            kline_dates=["20260801"],
            snapshot_available=True,
        )
        self.assertFalse(context["ok"])
        self.assertEqual(context["mode"], "blocked")
        self.assertIn("formula_outputs_missing_as_of:20260804", context["errors"])
        self.assertIn("kline_missing_as_of:20260804", context["errors"])


if __name__ == "__main__":
    unittest.main()
