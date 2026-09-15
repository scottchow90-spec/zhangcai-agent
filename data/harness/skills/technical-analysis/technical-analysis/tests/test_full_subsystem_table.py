#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import importlib.util
import sys
import unittest
from pathlib import Path


SKILLS = Path(r"D:\C盘转移\日志\codex\skills")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot_load_module:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


technical = load_module(
    "technical_analysis_entry_test",
    SKILLS / "technical-analysis" / "scripts" / "entry_technical_analysis.py",
)
big_bull = load_module(
    "big_bull_analysis_test",
    SKILLS / "big-bull-analysis-scoring-system" / "scripts" / "daniuxian_analysis.py",
)
feilong = load_module(
    "feilong_analysis_test",
    SKILLS / "feilong-strategy" / "scripts" / "feilong_realtime_report.py",
)
zhuangjia = load_module(
    "zhuangjia_analysis_test",
    SKILLS / "zhuangjia-capital-monitoring" / "scripts" / "call_zhuangjia_tq.py",
)


class FullSubsystemTableTests(unittest.TestCase):
    def test_exact_expected_subsystem_contract(self):
        self.assertEqual(len(technical.EXPECTED_SUBSYSTEMS), 30)
        self.assertEqual(
            [item[2] for item in technical.EXPECTED_SUBSYSTEMS[:16]],
            [item[1] for item in big_bull.DaniuxianAnalyzer.SUBSYSTEMS],
        )
        self.assertEqual(
            [item[2] for item in technical.EXPECTED_SUBSYSTEMS[16:26]],
            [item[1] for item in feilong.SUBSYSTEMS],
        )
        self.assertEqual(
            [item[2] for item in technical.EXPECTED_SUBSYSTEMS[26:]],
            list(zhuangjia.REQUIRED_FIELDS),
        )
        self.assertEqual(
            technical.EXPECTED_SUBSYSTEMS[15],
            ("大牛线撑压版", 16, "核心黄金分割撑压"),
        )

    def test_index_rows_are_retained_and_marked(self):
        rows = big_bull.build_subsystem_rows(
            {
                "is_index": True,
                "close": 3360.10,
                "main_trend": 3340.20,
                "main_trend_prev": 3335.10,
                "trend_up": True,
            }
        )
        self.assertEqual(len(rows), 16)
        by_number = {row["序号"]: row for row in rows}
        for number in (4, 9, 10, 11, 12):
            self.assertEqual(by_number[number]["状态"], "指数不适用")
            self.assertTrue(by_number[number]["结论"])
        support_row = by_number[16]
        self.assertEqual(support_row["子系统/输出"], "核心黄金分割撑压")
        for field in ("支撑一", "支撑二", "压力一", "压力二", "OUTPUT66"):
            self.assertIn(f"{field}=NA", support_row["当前值/证据"])
        self.assertEqual(
            support_row["结论"],
            "最近有效支撑=NA，最近有效压力=NA",
        )

    def test_big_bull_core_fibonacci_support_pressure_row_uses_all_tq_fields(self):
        rows = big_bull.build_subsystem_rows(
            {
                "is_index": True,
                "close": 3866.14,
                "support_1": 3659.44,
                "support_2": None,
                "pressure_1": 4258.86,
                "pressure_2": "N/A",
                "output66": "核心黄金分割: 有效可见 防近线/防压缩",
                "nearest_support": 3659.44,
                "nearest_pressure": 4258.86,
                "support_pressure_status": "双向撑压有效",
            }
        )
        support_row = rows[15]
        self.assertEqual(support_row["序号"], 16)
        self.assertEqual(support_row["子系统/输出"], "核心黄金分割撑压")
        self.assertEqual(support_row["状态"], "双向撑压有效")
        for evidence in (
            "支撑一=3659.44",
            "支撑二=NA",
            "压力一=4258.86",
            "压力二=NA",
            "OUTPUT66=核心黄金分割: 有效可见 防近线/防压缩",
        ):
            self.assertIn(evidence, support_row["当前值/证据"])
        self.assertEqual(
            support_row["结论"],
            "最近有效支撑=3659.44，最近有效压力=4258.86",
        )

    def test_feilong_index_rows_keep_all_ten_and_use_golden_cross_terms(self):
        rows = feilong.build_subsystem_rows(
            {
                "latest_outputs": {
                    "波": {"latest": 55.0, "prev": 50.0},
                    "段": {"latest": 45.0, "prev": 44.0},
                },
                "derived": {},
                "realtime_calc": {},
            },
            is_index=True,
        )
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[7]["状态"], "金叉")
        rendered = technical.render_subsystem_table_markdown(
            big_bull.build_subsystem_rows({"is_index": True})
            + rows
            + zhuangjia.build_subsystem_rows(
                {
                    "latest": {
                        "OUTPUT3": 1,
                        "OUTPUT4": 1,
                        "控盘程度": 2.5,
                        "控盘度": 2.5,
                    }
                },
                is_index=True,
            )
        )
        for forbidden in technical.FORBIDDEN_FEILONG_RELATION_PATTERNS:
            self.assertNotIn(forbidden, rendered)

    def test_validation_requires_exact_order_unique_nonempty_rows(self):
        rows = []
        for formula, number, subsystem in technical.EXPECTED_SUBSYSTEMS:
            state = (
                "金叉状态不可判定"
                if formula == "飞龙在天" and number == 8
                else "state"
            )
            rows.append(
                {
                    "公式": formula,
                    "序号": number,
                    "子系统/输出": subsystem,
                    "当前值/证据": "evidence",
                    "状态": state,
                    "结论": "conclusion",
                    "适用性/备注": "applicable",
                }
            )
        counts = technical.validate_subsystem_table(rows)
        self.assertEqual(counts, {"大牛线撑压版": 16, "飞龙在天": 10, "庄家资金监控": 4})
        markdown = technical.render_subsystem_table_markdown(rows)
        self.assertEqual(markdown.count("| 公式 | 序号 | 子系统/输出 |"), 1)
        self.assertEqual(markdown.count("|---|---:|---|---|---|---|---|"), 1)

        duplicate = list(rows)
        duplicate[-1] = dict(duplicate[-2])
        with self.assertRaises(ValueError):
            technical.validate_subsystem_table(duplicate)

        blank = [dict(row) for row in rows]
        blank[0]["结论"] = ""
        with self.assertRaises(ValueError):
            technical.validate_subsystem_table(blank)

    def test_any_injected_formula_failure_is_blocked(self):
        for formula in technical.FORMULA_NAMES:
            with self.subTest(formula=formula):
                payload, returncode = technical.execute(
                    argparse.Namespace(
                        code="000001.SH",
                        tdx=r"C:\new_tdx_mock",
                        test_fail_formula=formula,
                    )
                )
                self.assertNotEqual(returncode, 0)
                self.assertEqual(payload["status"], "BLOCKED")
                self.assertFalse(payload["analysis_complete"])
                self.assertIn(formula, payload["failed_formulas"])

    def test_explicit_market_suffix_is_preserved(self):
        analyzer = big_bull.DaniuxianAnalyzer.__new__(big_bull.DaniuxianAnalyzer)
        analyzer._configure_symbol("000001.SH")
        self.assertEqual(analyzer.symbol, "000001.SH")
        self.assertTrue(analyzer.is_index)
        self.assertEqual(feilong.resolve_symbol("000001.SH"), "000001.SH")
        self.assertEqual(feilong.resolve_symbol("000001.SZ"), "000001.SZ")


if __name__ == "__main__":
    unittest.main()
