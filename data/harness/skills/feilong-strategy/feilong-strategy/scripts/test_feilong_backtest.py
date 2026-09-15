#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import canonical_business_adapter
import feilong_offline_replay as offline_module
import feilong_realtime_report as report_module
from feilong_realtime_report import (
    FORMULA_CALL_NAME,
    SELECTION_FORMULA_CALL_NAME,
    build_formula_risks,
    build_formula_interpretation,
    build_event_rows,
    extract_xg_signals,
    extract_indicator_main_rise_signals,
    main,
    normalize_stock_universe,
    run_backtest,
    run_formula_signal_batches,
    summarize_event_rows,
)


class FeilongBacktestTests(unittest.TestCase):
    class FakeTq:
        def __init__(self) -> None:
            self.formula_names = []
            self.closed = False

        def formula_process_mul_xg(self, **kwargs):
            self.formula_names.append(kwargs["formula_name"])
            return {"ErrorId": "0", "002192.SZ": {"XG": []}}

        def close(self) -> None:
            self.closed = True

    def test_finance_three_risk_describes_main_board_scope(self) -> None:
        risks = build_formula_risks()

        self.assertTrue(any("沪深主板" in risk for risk in risks))
        self.assertFalse(any("仅上证A股" in risk or "缩窄到上证A股" in risk for risk in risks))

    def test_selection_formula_name_matches_live_tq_registry(self) -> None:
        self.assertEqual(SELECTION_FORMULA_CALL_NAME, "飞龙在天")

    def test_realtime_selector_formula_source_is_registered(self) -> None:
        evidence = report_module.resolve_formula_source("飞龙共振实时选股")

        self.assertEqual(evidence["formula_name"], "飞龙共振实时选股")
        self.assertEqual(
            Path(evidence["source_path"]),
            Path(
                r"D:\C盘转移\日志\codex\skills\feilong-strategy\references\formulas\飞龙共振实时选股.tdx.txt"
            ),
        )
        self.assertEqual(
            evidence["source_raw_sha256"],
            "ed526509f7afed185ade2fc3ff70a6702c9bbaf0ab53a69c781c2b0c0cd72df2",
        )
        self.assertEqual(
            evidence["gbk_payload_sha256"],
            "3d95fd3365a2e28caf53ae706fc94f530520a7aab4625e622211a352975b8402",
        )

    def test_formula_batches_accept_an_explicit_selection_formula(self) -> None:
        class FakeTq:
            formula_name = None

            def formula_process_mul_xg(self, **kwargs):
                self.formula_name = kwargs["formula_name"]
                return {"ErrorId": "0", "002192.SZ": {"XG": []}}

        tq = FakeTq()
        run_formula_signal_batches(
            tq=tq,
            universe=["002192.SZ"],
            start_date="20260821",
            end_date="20260821",
            chunk_size=1,
            selection_formula="飞龙裸三色",
        )

        self.assertEqual(tq.formula_name, "飞龙裸三色")

    def test_backtest_cli_forwards_selection_formula_without_changing_default(self) -> None:
        with patch("feilong_realtime_report.run_backtest", return_value={"status": "CLEAN_PASS"}) as mocked:
            with redirect_stdout(StringIO()):
                main(
                    [
                        "--backtest",
                        "--start-date",
                        "20260821",
                        "--end-date",
                        "20260821",
                        "--selection-formula",
                        "飞龙裸三色",
                    ]
                )

        self.assertEqual(mocked.call_args.kwargs["selection_formula"], "飞龙裸三色")

    def test_canonical_adapter_preserves_exact_naked_formula_extra_args(self) -> None:
        business_args = [
            "--",
            "--backtest",
            "--start-date",
            "20260821",
            "--end-date",
            "20260821",
            "--symbols",
            "002192.SZ",
            "--chunk-size",
            "1",
            "--selection-formula",
            "飞龙裸三色",
        ]

        command = canonical_business_adapter.business_command(
            Path(r"C:\unused-run-dir"),
            business_args,
        )

        self.assertEqual(command[2], "run")
        self.assertEqual(command[3:], business_args[1:])

    def test_naked_formula_backtest_output_binds_canonical_source_and_hashes(self) -> None:
        fake_tq = self.FakeTq()
        with tempfile.TemporaryDirectory() as temporary:
            with patch("feilong_realtime_report.init_tq", return_value=fake_tq):
                result = run_backtest(
                    start_date="20260821",
                    end_date="20260821",
                    out_dir=temporary,
                    symbols=["002192.SZ"],
                    chunk_size=1,
                    selection_formula="飞龙裸三色",
                )

            payload = json.loads(
                Path(result["backtest_json"]).read_text(encoding="utf-8")
            )
            segment_manifest = json.loads(
                Path(result["segment_manifest"]).read_text(encoding="utf-8")
            )
            for key in ("backtest_json", "events_csv"):
                artifact = segment_manifest["artifacts"][key]
                artifact_path = Path(artifact["path"])
                self.assertTrue(artifact_path.is_file())
                self.assertEqual(artifact["size"], artifact_path.stat().st_size)
                self.assertEqual(
                    artifact["sha256"],
                    hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
                )

        formula = payload["formula"]
        expected_source = (
            Path(r"D:\C盘转移\日志\codex\skills\feilong-strategy")
            / "references"
            / "formulas"
            / "飞龙裸三色.tdx.txt"
        )
        self.assertEqual(fake_tq.formula_names, ["飞龙裸三色"])
        self.assertTrue(fake_tq.closed)
        self.assertEqual(formula["formula_type"], "condition_selection")
        self.assertEqual(formula["formula_display_name"], "飞龙裸三色")
        self.assertEqual(formula["selection_formula"], "飞龙裸三色")
        self.assertIsNone(formula["indicator_formula"])
        self.assertEqual(Path(formula["local_source_path"]), expected_source)
        self.assertEqual(
            formula["local_source_raw_sha256"],
            "3029d0fda387842984f834b41f9849a9a71b933380cc7fedcb79d0d6cc73444b",
        )
        self.assertEqual(
            formula["gbk_payload_sha256"],
            "167fda25731a6f85da58b484769f4f3df6b0aaee8cc004223532a4dec0d9b263",
        )
        self.assertNotEqual(
            Path(formula["local_source_path"]),
            Path(r"C:\new_tdx_mock\T0002\gs_bak\飞龙在天.txt"),
        )
        self.assertEqual(
            segment_manifest["schema"],
            "FEILONG_BACKTEST_SEGMENT_MANIFEST_V1",
        )
        self.assertEqual(segment_manifest["status"], "CLEAN_PASS")
        self.assertEqual(
            segment_manifest["formula"]["selection_formula"], "飞龙裸三色"
        )
        self.assertEqual(
            segment_manifest["formula"]["local_source_raw_sha256"],
            "3029d0fda387842984f834b41f9849a9a71b933380cc7fedcb79d0d6cc73444b",
        )
        self.assertEqual(
            segment_manifest["formula"]["gbk_payload_sha256"],
            "167fda25731a6f85da58b484769f4f3df6b0aaee8cc004223532a4dec0d9b263",
        )
        self.assertEqual(segment_manifest["validation"]["status"], "CLEAN_PASS")
        self.assertEqual(segment_manifest["validation"]["errors"], [])

    def test_canonical_adapter_binds_clean_backtest_manifest_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            backtest_json = root / "feilong_backtest.json"
            events_csv = root / "feilong_backtest_events.csv"
            segment_manifest = root / "feilong_backtest_segment_manifest.json"
            backtest_json.write_text('{"status":"CLEAN_PASS"}\n', encoding="utf-8")
            events_csv.write_text("symbol,signal_date\n", encoding="utf-8")

            def artifact(path: Path) -> dict[str, object]:
                return {
                    "path": str(path),
                    "size": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }

            segment_manifest.write_text(
                json.dumps(
                    {
                        "schema": "FEILONG_BACKTEST_SEGMENT_MANIFEST_V1",
                        "status": "CLEAN_PASS",
                        "formula": {"selection_formula": "飞龙裸三色"},
                        "artifacts": {
                            "backtest_json": artifact(backtest_json),
                            "events_csv": artifact(events_csv),
                        },
                        "validation": {
                            "status": "CLEAN_PASS",
                            "errors": [],
                            "formula_source_bound": True,
                            "artifact_hashes_verified": True,
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            stdout = "TQ初始化\n" + json.dumps(
                {
                    "schema": "FEILONG_TDX_BACKTEST_V1",
                    "status": "CLEAN_PASS",
                    "backtest_json": str(backtest_json),
                    "events_csv": str(events_csv),
                    "segment_manifest": str(segment_manifest),
                },
                ensure_ascii=False,
                indent=2,
            )

            bound = canonical_business_adapter.extract_backtest_artifacts(stdout)

            self.assertEqual(set(bound), {
                "backtest_json", "events_csv", "segment_manifest"
            })
            for evidence in bound.values():
                path = Path(evidence["path"])
                self.assertEqual(
                    evidence["sha256"],
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                )

    def test_canonical_adapter_rejects_tampered_backtest_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            backtest_json = root / "feilong_backtest.json"
            events_csv = root / "feilong_backtest_events.csv"
            segment_manifest = root / "feilong_backtest_segment_manifest.json"
            backtest_json.write_text('{"status":"CLEAN_PASS"}\n', encoding="utf-8")
            events_csv.write_text("symbol,signal_date\n", encoding="utf-8")
            manifest = {
                "schema": "FEILONG_BACKTEST_SEGMENT_MANIFEST_V1",
                "status": "CLEAN_PASS",
                "artifacts": {
                    "backtest_json": {
                        "path": str(backtest_json),
                        "size": backtest_json.stat().st_size,
                        "sha256": hashlib.sha256(backtest_json.read_bytes()).hexdigest(),
                    },
                    "events_csv": {
                        "path": str(events_csv),
                        "size": events_csv.stat().st_size,
                        "sha256": hashlib.sha256(events_csv.read_bytes()).hexdigest(),
                    },
                },
                "validation": {
                    "status": "CLEAN_PASS",
                    "errors": [],
                    "formula_source_bound": True,
                    "artifact_hashes_verified": True,
                },
            }
            segment_manifest.write_text(json.dumps(manifest), encoding="utf-8")
            events_csv.write_bytes(b"X" * events_csv.stat().st_size)
            stdout = json.dumps(
                {
                    "schema": "FEILONG_TDX_BACKTEST_V1",
                    "status": "CLEAN_PASS",
                    "backtest_json": str(backtest_json),
                    "events_csv": str(events_csv),
                    "segment_manifest": str(segment_manifest),
                }
            )

            with self.assertRaisesRegex(RuntimeError, "artifact hash mismatch"):
                canonical_business_adapter.extract_backtest_artifacts(stdout)

    def test_default_backtest_output_uses_current_formula_identity(self) -> None:
        fake_tq = self.FakeTq()
        with tempfile.TemporaryDirectory() as temporary:
            with patch("feilong_realtime_report.init_tq", return_value=fake_tq):
                result = run_backtest(
                    start_date="20260821",
                    end_date="20260821",
                    out_dir=temporary,
                    symbols=["002192.SZ"],
                    chunk_size=1,
                )

            payload = json.loads(
                Path(result["backtest_json"]).read_text(encoding="utf-8")
            )

        formula = payload["formula"]
        self.assertEqual(formula["formula_type"], "condition_selection")
        self.assertEqual(formula["formula_display_name"], "飞龙在天")
        self.assertEqual(formula["selection_formula"], "飞龙在天")
        self.assertEqual(formula["indicator_formula"], "飞龙在天")

    def test_default_formula_source_uses_verified_migration_source(self) -> None:
        resolver = getattr(report_module, "resolve_formula_source", None)
        self.assertIsNotNone(resolver, "resolve_formula_source must exist")

        evidence = resolver(SELECTION_FORMULA_CALL_NAME)

        self.assertEqual(evidence["formula_name"], "飞龙在天")
        self.assertEqual(
            Path(evidence["source_path"]),
            Path(r"D:\C盘转移\日志\codex\skills\feilong-strategy\references\formulas\飞龙在天.tdx.txt"),
        )
        self.assertEqual(
            evidence["source_raw_sha256"],
            "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0",
        )
        self.assertEqual(
            evidence["gbk_payload_sha256"],
            "1c53d05809316d4daf2bc283f66e12812a7390636481109f3df9545d9cd6be72",
        )

    def test_all_formula_source_binding_drift_blocks_before_business_output_or_tq(self) -> None:
        canonical_manifest = json.loads(
            report_module.FORMULA_SOURCE_MANIFEST.read_text(encoding="utf-8")
        )
        canonical_spec = canonical_manifest["formulas"]["飞龙裸三色"]
        canonical_source_bytes = Path(canonical_spec["source_path"]).read_bytes()
        drift_cases = (
            ("unknown", "formula_source_not_registered"),
            ("raw_hash", "formula_source_raw_hash_mismatch"),
            ("size", "formula_source_size_mismatch"),
            ("bom", "formula_source_bom_mismatch"),
            ("source_encoding", "formula_source_encoding_invalid"),
            ("payload_encoding", "formula_payload_encoding_invalid"),
            ("payload_size", "formula_payload_size_mismatch"),
            ("payload_hash", "formula_payload_hash_mismatch"),
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for case_name, expected_error in drift_cases:
                with self.subTest(case=case_name):
                    case_root = root / case_name
                    case_root.mkdir()
                    source_path = case_root / "飞龙裸三色.tdx.txt"
                    source_bytes = bytearray(canonical_source_bytes)
                    manifest = json.loads(json.dumps(canonical_manifest, ensure_ascii=False))
                    source_spec = manifest["formulas"]["飞龙裸三色"]
                    source_spec["source_path"] = str(source_path)
                    selection_formula = "飞龙裸三色"

                    if case_name == "unknown":
                        selection_formula = "未登记公式"
                    elif case_name == "raw_hash":
                        source_bytes[-1] ^= 1
                    elif case_name == "size":
                        source_bytes.extend(b"\n")
                    elif case_name == "bom":
                        source_spec["source_bom"] = True
                    elif case_name == "source_encoding":
                        source_spec["source_encoding"] = "gbk"
                    elif case_name == "payload_encoding":
                        source_spec["payload_encoding"] = "utf-8"
                    elif case_name == "payload_size":
                        source_spec["payload_size_bytes"] += 1
                    elif case_name == "payload_hash":
                        source_spec["gbk_payload_sha256"] = "0" * 64

                    source_path.write_bytes(source_bytes)
                    manifest_path = case_root / "formula-source-manifest.json"
                    manifest_path.write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    output = case_root / "business-out"
                    with patch.object(
                        report_module,
                        "FORMULA_SOURCE_MANIFEST",
                        manifest_path,
                    ):
                        with patch("feilong_realtime_report.init_tq") as mocked_init:
                            with self.assertRaisesRegex(RuntimeError, expected_error):
                                run_backtest(
                                    start_date="20260821",
                                    end_date="20260821",
                                    out_dir=str(output),
                                    symbols=["002192.SZ"],
                                    chunk_size=1,
                                    selection_formula=selection_formula,
                                )

                    mocked_init.assert_not_called()
                    self.assertFalse(output.exists())
                    self.assertFalse((output / "feilong_backtest.json").exists())
                    self.assertFalse((output / "feilong_backtest_events.csv").exists())

    def test_formula_interpretation_keeps_all_ten_subsystems_in_order(self) -> None:
        rows = build_formula_interpretation()

        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0]["subsystem"], "龙头战法")
        self.assertEqual(rows[-1]["subsystem"], "主升启动共振")

    def test_normalize_stock_universe_accepts_tq_strings_and_dicts(self) -> None:
        raw = [
            "600000.SH",
            {"Code": "000001", "Market": "SZ"},
            {"StockCode": "300750.SZ"},
            {"Code": "430001", "Market": "BJ"},
            {"Code": "not-a-stock"},
        ]

        self.assertEqual(
            normalize_stock_universe(raw),
            ["000001.SZ", "300750.SZ", "430001.BJ", "600000.SH"],
        )

    def test_extract_xg_signals_keeps_only_truthy_values_and_dates(self) -> None:
        formula_result = {
            "ErrorId": "0",
            "600000.SH": {
                "XG": [
                    {"Date": "2026-01-05", "Value": 0},
                    {"Date": "20260106", "Value": 1},
                    {"Date": "20260106", "Value": 100},
                ]
            },
            "000001.SZ": [
                {"Date": "20260107", "Value": True},
                {"Date": "bad-date", "Value": 1},
            ],
        }

        self.assertEqual(
            extract_xg_signals(formula_result),
            [
                {"symbol": "000001.SZ", "signal_date": "20260107"},
                {"symbol": "600000.SH", "signal_date": "20260106"},
            ],
        )

    def test_indicator_main_rise_uses_any_visible_final_formula_output(self) -> None:
        formula_result = {
            "ErrorId": "0",
            "600000.SH": {
                "OUTPUT3": [
                    {"Date": "20260105", "Value": 100},
                    {"Date": "20260106", "Value": 0},
                    {"Date": "20260107", "Value": 0},
                    {"Date": "20260108", "Value": 0},
                ],
                "OUTPUT4": [
                    {"Date": "20260105", "Value": 0},
                    {"Date": "20260106", "Value": 100},
                    {"Date": "20260107", "Value": 0},
                    {"Date": "20260108", "Value": 0},
                ],
                "OUTPUT5": [
                    {"Date": "20260105", "Value": 0},
                    {"Date": "20260106", "Value": 0},
                    {"Date": "20260107", "Value": 100},
                    {"Date": "20260108", "Value": 0},
                ],
                "OUTPUT6": [
                    {"Date": "20260105", "Value": 0},
                    {"Date": "20260106", "Value": 0},
                    {"Date": "20260107", "Value": 0},
                    {"Date": "20260108", "Value": 1},
                ],
            },
        }

        self.assertEqual(
            extract_indicator_main_rise_signals(formula_result),
            [
                {"symbol": "600000.SH", "signal_date": "20260105"},
                {"symbol": "600000.SH", "signal_date": "20260106"},
                {"symbol": "600000.SH", "signal_date": "20260107"},
                {"symbol": "600000.SH", "signal_date": "20260108"},
            ],
        )

    def test_front_adjustment_includes_rights_subscription_cash(self) -> None:
        bars = pd.DataFrame(
            [
                {"open": 10.0, "high": 10.0, "low": 10.0, "close": 10.0},
                {"open": 7.4, "high": 7.4, "low": 7.4, "close": 7.4},
            ],
            index=["20260105", "20260106"],
        )
        actions = pd.DataFrame(
            [
                {
                    "date": "20260106",
                    "cash_dividend_per_10": 1.0,
                    "rights_price": 4.0,
                    "bonus_shares_per_10": 2.0,
                    "rights_shares_per_10": 3.0,
                }
            ]
        )

        adjusted = offline_module.front_adjust_like_tq(bars, actions)

        self.assertAlmostEqual(adjusted.loc["20260105", "close"], 7.4)
        self.assertAlmostEqual(adjusted.loc["20260106", "close"], 7.4)

    def test_missing_finance_xs2_false_is_a_proven_negative(self) -> None:
        independent = pd.DataFrame(
            {"xs2": [False], "private_entry": [False]},
            index=["20260105"],
        )

        signal_dates, proofs = offline_module.resolve_missing_finance_candidates(
            independent,
            candidate_dates=["20260105"],
            symbol="600000.SH",
        )

        self.assertEqual(signal_dates, [])
        self.assertEqual(
            proofs,
            [
                {
                    "candidate_date": "20260105",
                    "xs2": False,
                    "private_entry": False,
                    "signal": False,
                    "reason": "xs2_false",
                }
            ],
        )

    def test_missing_finance_signal_dependency_still_blocks(self) -> None:
        independent = pd.DataFrame(
            {"xs2": [True], "private_entry": [False]},
            index=["20260105"],
        )

        with self.assertRaisesRegex(
            RuntimeError,
            r"active capital is required: 600000\.SH 20260105",
        ):
            offline_module.resolve_missing_finance_candidates(
                independent,
                candidate_dates=["20260105"],
                symbol="600000.SH",
            )

    def test_missing_finance_replay_records_local_short_circuit_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tdx_root = Path(temporary)
            base_path = tdx_root / "T0002" / "hq_cache" / "base.dbf"
            gbbq_path = tdx_root / "T0002" / "hq_cache" / "gbbq"
            day_path = tdx_root / "vipdoc" / "sh" / "lday" / "sh600000.day"
            cw_path = tdx_root / "vipdoc" / "cw" / "gpsh600000.dat"
            for path, content in (
                (base_path, b"base"),
                (gbbq_path, b"gbbq"),
                (day_path, b"day"),
                (cw_path, b"cw"),
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            dates = pd.date_range("2025-01-01", periods=400, freq="D").strftime("%Y%m%d")
            bars = pd.DataFrame(
                {
                    "open": 10.0,
                    "high": 10.0,
                    "low": 10.0,
                    "close": 10.0,
                    "amount": 1_000_000.0,
                    "volume": 1_000_000.0,
                },
                index=dates,
            )
            empty_actions = pd.DataFrame(columns=["symbol", "date"])

            with (
                patch.object(offline_module, "read_base_finance", return_value={}),
                patch.object(offline_module, "read_gbbq", return_value=empty_actions),
                patch.object(offline_module, "read_tdx_day", return_value=bars),
            ):
                signals, evidence = offline_module.replay_installed_formula_signals(
                    symbols=["600000.SH"],
                    start_date="20251201",
                    end_date="20251201",
                    tdx_root=tdx_root,
                    candidate_dates={"600000.SH": ["20251201"]},
                )

        self.assertEqual(signals, [])
        resolution = evidence["missing_finance_resolutions"][0]
        self.assertEqual(resolution["symbol"], "600000.SH")
        self.assertEqual(resolution["candidate_proofs"][0]["reason"], "xs2_false")
        self.assertEqual(resolution["day_source"]["sha256"], hashlib.sha256(b"day").hexdigest())
        self.assertEqual(resolution["cw_source"]["sha256"], hashlib.sha256(b"cw").hexdigest())

    def test_indicator_main_rise_accepts_boolean_one_from_real_tq_output(self) -> None:
        formula_result = {
            "ErrorId": "0",
            "600000.SH": {
                "OUTPUT3": [{"Date": "20260105", "Value": 100}],
                "OUTPUT4": [],
                "OUTPUT5": [{"Date": "20260105", "Value": 1}],
                "OUTPUT6": [],
            },
        }

        self.assertEqual(
            extract_indicator_main_rise_signals(formula_result),
            [{"symbol": "600000.SH", "signal_date": "20260105"}],
        )

    def test_indicator_main_rise_batches_use_installed_indicator_formula(self) -> None:
        class FakeTq:
            formula_name = None

            def formula_process_mul_zb(self, **kwargs):
                self.formula_name = kwargs["formula_name"]
                return {
                    "ErrorId": "0",
                    "002192.SZ": {
                        key: [{"Date": "20260821", "Value": 0}]
                        for key in ("OUTPUT3", "OUTPUT4", "OUTPUT5", "OUTPUT6")
                    },
                }

        tq = FakeTq()
        signals, calls = run_formula_signal_batches(
            tq=tq,
            universe=["002192.SZ"],
            start_date="20260821",
            end_date="20260821",
            chunk_size=1,
            selection_formula=FORMULA_CALL_NAME,
            formula_mode="installed_indicator_main_rise",
        )

        self.assertEqual(tq.formula_name, "飞龙在天")
        self.assertEqual(signals, [])
        self.assertEqual(calls[0]["formula_mode"], "installed_indicator_main_rise")

    def test_indicator_main_rise_backtest_uses_installed_formula_mode(self) -> None:
        class FakeTq:
            formula_names = []
            closed = False

            def formula_process_mul_zb(self, **kwargs):
                self.formula_names.append(kwargs["formula_name"])
                return {
                    "ErrorId": "0",
                    "002192.SZ": {
                        "OUTPUT3": [{"Date": "20260821", "Value": 0}],
                        "OUTPUT4": [{"Date": "20260821", "Value": 0}],
                        "OUTPUT5": [{"Date": "20260821", "Value": 0}],
                        "OUTPUT6": [{"Date": "20260821", "Value": 0}],
                    },
                }

            def close(self):
                self.closed = True

        fake_tq = FakeTq()
        with tempfile.TemporaryDirectory() as temporary:
            with patch("feilong_realtime_report.init_tq", return_value=fake_tq):
                result = run_backtest(
                    start_date="20260821",
                    end_date="20260821",
                    out_dir=temporary,
                    symbols=["002192.SZ"],
                    chunk_size=1,
                    selection_formula=FORMULA_CALL_NAME,
                    formula_mode="installed_indicator_main_rise",
                )
            payload = json.loads(Path(result["backtest_json"]).read_text(encoding="utf-8"))

        self.assertEqual(fake_tq.formula_names, ["飞龙在天"])
        self.assertTrue(fake_tq.closed)
        self.assertEqual(payload["formula"]["formula_type"], "installed_indicator_main_rise")
        self.assertEqual(payload["formula"]["selection_formula"], "飞龙在天")
        self.assertEqual(payload["formula"]["indicator_formula"], "飞龙在天")
        self.assertEqual(
            payload["data"]["formula_calls"][0]["formula_mode"],
            "installed_indicator_main_rise",
        )

    def test_offline_replay_matches_real_tq_signal_dates(self) -> None:
        replay = getattr(report_module, "replay_installed_formula_signals", None)
        self.assertIsNotNone(replay)

        signals, _evidence = replay(
            symbols=["002989.SZ", "002192.SZ", "603095.SH", "688502.SH"],
            start_date="20260427",
            end_date="20260821",
        )

        self.assertEqual(
            signals,
            [
                {"symbol": "002192.SZ", "signal_date": "20260624"},
                {"symbol": "002192.SZ", "signal_date": "20260821"},
                {"symbol": "002989.SZ", "signal_date": "20260428"},
                {"symbol": "002989.SZ", "signal_date": "20260616"},
                {"symbol": "002989.SZ", "signal_date": "20260804"},
                {"symbol": "002989.SZ", "signal_date": "20260814"},
                {"symbol": "603095.SH", "signal_date": "20260821"},
                {"symbol": "688502.SH", "signal_date": "20260709"},
                {"symbol": "688502.SH", "signal_date": "20260805"},
            ],
        )

    def test_first_board_join_keeps_only_same_stock_same_date(self) -> None:
        joiner = getattr(report_module, "match_first_board_cycles", None)
        self.assertIsNotNone(joiner)
        cycles = pd.DataFrame(
            [
                {
                    "code": "002989",
                    "name": "中天精装",
                    "cycle_sequence": 1,
                    "first_board_date": "20260616",
                },
                {
                    "code": "002192",
                    "name": "融捷股份",
                    "cycle_sequence": 1,
                    "first_board_date": "20260324",
                },
            ]
        )
        signals = [
            {"symbol": "002989.SZ", "signal_date": "20260616"},
            {"symbol": "002192.SZ", "signal_date": "20260624"},
        ]

        matched = joiner(cycles, signals)

        self.assertEqual(len(matched), 1)
        self.assertEqual(matched.iloc[0]["code"], "002989")
        self.assertEqual(matched.iloc[0]["signal_date"], "20260616")

    def test_offline_backtest_filters_candidate_cycles_without_tq(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidates = root / "three_board_cycles.csv"
            pd.DataFrame(
                [
                    {
                        "code": "002989",
                        "name": "中天精装",
                        "cycle_sequence": 1,
                        "first_board_date": "20260616",
                    },
                    {
                        "code": "002192",
                        "name": "融捷股份",
                        "cycle_sequence": 1,
                        "first_board_date": "20260324",
                    },
                ]
            ).to_csv(candidates, index=False, encoding="utf-8-sig")

            with patch("feilong_realtime_report.init_tq") as mocked_init:
                result = run_backtest(
                    start_date="20260324",
                    end_date="20260616",
                    out_dir=str(root / "out"),
                    selection_formula=FORMULA_CALL_NAME,
                    formula_mode="offline_installed_formula_replay",
                    candidate_cycles_csv=str(candidates),
                )

            mocked_init.assert_not_called()
            matched = pd.read_csv(
                result["first_board_matches_csv"], dtype={"code": str}
            )
            payload = json.loads(
                Path(result["backtest_json"]).read_text(encoding="utf-8")
            )
            bound = canonical_business_adapter.extract_backtest_artifacts(
                json.dumps(result, ensure_ascii=False)
            )

        self.assertEqual(matched[["code", "signal_date"]].to_dict("records"), [
            {"code": "002192", "signal_date": 20260324},
            {"code": "002989", "signal_date": 20260616},
        ])
        self.assertEqual(
            payload["data"]["source"],
            "local Tongdaxin daily files with installed formula offline replay",
        )
        self.assertEqual(payload["data"]["candidate_cycle_count"], 2)
        self.assertEqual(payload["data"]["first_board_match_count"], 2)
        self.assertEqual(
            Path(bound["first_board_matches_csv"]["path"]),
            Path(result["first_board_matches_csv"]).resolve(),
        )

    def test_offline_backtest_passes_exact_first_board_dates_to_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidates = root / "three_board_cycles.csv"
            pd.DataFrame(
                [
                    {
                        "code": "600000",
                        "name": "浦发银行",
                        "cycle_sequence": 1,
                        "first_board_date": "20260105",
                    },
                    {
                        "code": "600000",
                        "name": "浦发银行",
                        "cycle_sequence": 2,
                        "first_board_date": "20260206",
                    },
                    {
                        "code": "000001",
                        "name": "平安银行",
                        "cycle_sequence": 1,
                        "first_board_date": "20260309",
                    },
                ]
            ).to_csv(candidates, index=False, encoding="utf-8-sig")

            def replay_with_candidate_evidence(*, candidate_dates, **_kwargs):
                return [], {"candidate_dates_seen": candidate_dates}

            with patch(
                "feilong_realtime_report.replay_installed_formula_signals",
                side_effect=replay_with_candidate_evidence,
            ):
                result = run_backtest(
                    start_date="20260105",
                    end_date="20260309",
                    out_dir=str(root / "out"),
                    selection_formula=FORMULA_CALL_NAME,
                    formula_mode="offline_installed_formula_replay",
                    candidate_cycles_csv=str(candidates),
                )
            payload = json.loads(
                Path(result["backtest_json"]).read_text(encoding="utf-8")
            )

        self.assertEqual(
            payload["data"]["offline_replay_evidence"]["candidate_dates_seen"],
            {
                "000001.SZ": ["20260309"],
                "600000.SH": ["20260105", "20260206"],
            },
        )

    def test_event_rows_enter_next_open_and_exclude_one_price_limit_up(self) -> None:
        bars = {
            "600000.SH": pd.DataFrame(
                {
                    "Open": [10.00, 10.20, 10.30, 10.40],
                    "High": [10.10, 10.30, 10.50, 10.60],
                    "Low": [9.90, 10.10, 10.20, 10.30],
                    "Close": [10.00, 10.25, 10.45, 10.50],
                },
                index=["20260105", "20260106", "20260107", "20260108"],
            ),
            "600001.SH": pd.DataFrame(
                {
                    "Open": [10.00, 11.00, 11.10],
                    "High": [10.00, 11.00, 11.30],
                    "Low": [10.00, 11.00, 11.00],
                    "Close": [10.00, 11.00, 11.20],
                },
                index=["20260105", "20260106", "20260107"],
            ),
        }
        signals = [
            {"symbol": "600000.SH", "signal_date": "20260105"},
            {"symbol": "600001.SH", "signal_date": "20260105"},
        ]

        rows = build_event_rows(signals, bars, horizons=(1, 2))

        tradable = next(row for row in rows if row["symbol"] == "600000.SH")
        self.assertEqual(tradable["entry_date"], "20260106")
        self.assertAlmostEqual(tradable["return_1d_pct"], (10.25 / 10.20 - 1) * 100)
        self.assertAlmostEqual(tradable["return_2d_pct"], (10.45 / 10.20 - 1) * 100)
        locked = next(row for row in rows if row["symbol"] == "600001.SH")
        self.assertFalse(locked["tradable_next_open"])
        self.assertEqual(locked["exclusion_reason"], "next_open_one_price_limit_up")

    def test_summary_uses_only_tradable_rows_and_reports_coverage(self) -> None:
        rows = [
            {"tradable_next_open": True, "return_1d_pct": 2.0},
            {"tradable_next_open": True, "return_1d_pct": -1.0},
            {"tradable_next_open": False, "return_1d_pct": 20.0},
            {"tradable_next_open": True, "return_1d_pct": None},
        ]

        summary = summarize_event_rows(rows, horizons=(1,))

        self.assertEqual(summary["signal_count"], 4)
        self.assertEqual(summary["tradable_signal_count"], 3)
        self.assertEqual(summary["horizons"]["1d"]["sample_count"], 2)
        self.assertEqual(summary["horizons"]["1d"]["win_rate_pct"], 50.0)
        self.assertEqual(summary["horizons"]["1d"]["mean_return_pct"], 0.5)
        self.assertIsNone(summary["horizons"]["1d"]["mean_net_return_pct"])


if __name__ == "__main__":
    unittest.main()
