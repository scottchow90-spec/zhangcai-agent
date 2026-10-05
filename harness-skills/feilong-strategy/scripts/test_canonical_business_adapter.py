#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import csv
import hashlib
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

import canonical_business_adapter as adapter
from canonical_business_adapter import business_command, parse_cli_args


CORE_RANGES = (
    ("19901219", "19961231"),
    ("19970101", "20011231"),
    ("20020101", "20021231"),
    ("20030101", "20031231"),
    ("20040101", "20041231"),
    ("20050101", "20051231"),
    ("20060101", "20061231"),
    ("20070101", "20071231"),
    ("20080101", "20081231"),
    ("20090101", "20091231"),
    ("20100101", "20101231"),
    ("20110101", "20111231"),
    ("20120101", "20121231"),
    ("20130101", "20141231"),
    ("20150101", "20161231"),
    ("20170101", "20201231"),
    ("20210101", "20260826"),
)
FORMULA = {
    "selection_formula": "飞龙裸三色",
    "indicator_formula": None,
    "local_source_raw_sha256": "3029d0fda387842984f834b41f9849a9a71b933380cc7fedcb79d0d6cc73444b",
    "gbk_payload_sha256": "167fda25731a6f85da58b484769f4f3df6b0aaee8cc004223532a4dec0d9b263",
}
NONSTANDARD_HASH = "c6158985199bf1009ce3b4e8c049e3c8818bcb173e020e9dce9e7abf554c163a"
DELIVERY_STEM = "飞龙裸三色-全量K线回测-19901219-20260826"
TEST_CONTRACT_SHA256 = "a" * 64
SKILL_ENTRY = r"D:\C盘转移\日志\codex\skills\feilong-strategy\scripts\codex_entry.py"
LEGACY_ENTRY = r"D:\C盘转移\日志\codex\skills\feilong-strategy\scripts\legacy_codex_entry.py"
HORIZONS = (1, 3, 5, 10, 20)
EVENT_CSV_COLUMNS = (
    "symbol",
    "signal_date",
    "entry_date",
    "signal_close",
    "entry_open",
    "entry_gap_pct",
    "tradable_next_open",
    "exclusion_reason",
    *(
        column
        for horizon in HORIZONS
        for column in (
            f"return_{horizon}d_pct",
            f"net_return_{horizon}d_pct",
            f"mae_{horizon}d_pct",
            f"mfe_{horizon}d_pct",
        )
    ),
)
BACKTEST_HORIZON_KEYS = {
    "sample_count",
    "win_rate_pct",
    "mean_return_pct",
    "median_return_pct",
    "mean_net_return_pct",
    "p25_return_pct",
    "p75_return_pct",
    "min_return_pct",
    "max_return_pct",
    "worst_mae_pct",
}


def canonical_hash(payload: dict) -> str:
    material = {key: value for key, value in payload.items() if key != "manifest_integrity"}
    encoded = json.dumps(
        material, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def artifact(path: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "path": str(path.resolve()),
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8-sig"
    )


def receipt_hash(payload: dict) -> str:
    material = {key: value for key, value in payload.items() if key != "receipt_integrity"}
    encoded = json.dumps(
        material, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_empty_events_csv(path: Path) -> None:
    path.write_text(",".join(EVENT_CSV_COLUMNS) + "\n", encoding="utf-8-sig")


def valid_event_row(symbol: str = "600000.SH", signal_date: str = "19960102") -> dict:
    row = {column: "" for column in EVENT_CSV_COLUMNS}
    row.update(
        {
            "symbol": symbol,
            "signal_date": signal_date,
            "tradable_next_open": "False",
            "exclusion_reason": "signal_bar_missing",
        }
    )
    return row


def write_event_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVENT_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def valid_backtest_payload(root: Path, core_end: str) -> dict:
    return {
        "schema": "FEILONG_TDX_BACKTEST_V1",
        "status": "CLEAN_PASS",
        "generated_at": "2026-08-29T00:00:00+08:00",
        "formula": {
            "formula_type": "condition_selection",
            "formula_display_name": "飞龙裸三色",
            "selection_formula": FORMULA["selection_formula"],
            "indicator_formula": FORMULA["indicator_formula"],
            "local_source_path": str((root / "飞龙裸三色.tdx.txt").resolve()),
            "local_source_encoding": "utf-8-sig",
            "local_source_bom": "utf-8-sig",
            "local_source_size_bytes": 1,
            "local_source_sha256": FORMULA["local_source_raw_sha256"],
            "local_source_raw_sha256": FORMULA["local_source_raw_sha256"],
            "payload_encoding": "gbk",
            "gbk_payload_size_bytes": 1,
            "gbk_payload_sha256": FORMULA["gbk_payload_sha256"],
            "source_manifest_path": str((root / "formula-source-manifest.json").resolve()),
            "source_manifest_sha256": "b" * 64,
            "source_authority_scope": "fixture-production-shape",
            "interpretation": [
                {
                    "subsystem": f"subsystem-{index}",
                    "logic": "fixture",
                    "role_in_xg": "fixture",
                }
                for index in range(1, 11)
            ],
            "known_semantic_risks": ["fixture-risk"],
        },
        "data": {
            "source": "local Tongdaxin TQ formula engine and D-drive daily K-line data",
            "tdx_root": str((root / "TDX").resolve()),
            "start_date": "19901219",
            "end_date": core_end,
            "latest_loaded_kline_date": core_end,
            "universe_count": 1,
            "signal_stock_count": 0,
            "formula_batch_count": 1,
            "formula_calls": [
                {
                    "batch_start": "000001.SZ",
                    "stock_count": 1,
                    "error_id": "0",
                    "signal_count": 0,
                    "formula_mode": "condition_selection",
                }
            ],
        },
        "execution_model": {
            "signal_confirmation": "signal day close",
            "entry": "next trading day open",
            "horizons_trading_days": list(HORIZONS),
            "exit": "horizon day close",
            "one_price_limit_up_entry": "excluded from tradable statistics",
            "gross_return": "before fees and slippage",
            "net_stress": "gross return minus fixed 0.20 percentage points round trip",
            "portfolio_curve": (
                "not calculated because the formula defines no exit, sizing, or concurrency rule"
            ),
        },
        "summary": {
            "signal_count": 0,
            "tradable_signal_count": 0,
            "excluded_one_price_limit_up_count": 0,
            "missing_entry_data_count": 0,
            "horizons": {
                f"{horizon}d": {
                    key: 0 if key == "sample_count" else None
                    for key in BACKTEST_HORIZON_KEYS
                }
                for horizon in HORIZONS
            },
        },
        "signal_date_min": None,
        "signal_date_max": None,
    }


def clean_process_snapshot() -> dict:
    return {
        "status": "OK",
        "captured_at": "2026-08-29T00:00:00+08:00",
        "processes": [],
        "errors": [],
    }


def clean_process_integrity() -> dict:
    return {
        "status": "CLEAN_PASS",
        "errors": [],
        "before": clean_process_snapshot(),
        "after": clean_process_snapshot(),
    }


def write_valid_delivery_manifest(
    root: Path, *, receipt_root: Path | None = None
) -> tuple[Path, dict]:
    delivery = root / "delivery"
    delivery.mkdir(parents=True)
    receipt_root = (receipt_root or root / "executions").resolve()
    receipt_root.mkdir(parents=True, exist_ok=True)
    declared_artifacts: dict[str, dict[str, object]] = {}
    for key, suffix in (
        ("events_csv", "-逐信号.csv"),
        ("summary_json", "-汇总.json"),
        ("report_markdown", "-报告.md"),
        ("day_inventory_csv", "-全量日线清单.csv"),
    ):
        path = delivery / f"{DELIVERY_STEM}{suffix}"
        path.write_text(f"{key}\n", encoding="utf-8")
        declared_artifacts[key] = artifact(path)

    segments = []
    for index, (core_start, core_end) in enumerate(CORE_RANGES, start=1):
        output_dir = root / "segments" / f"segment-{index:02d}"
        output_dir.mkdir(parents=True)
        backtest_json = output_dir / "feilong_backtest.json"
        events_csv = output_dir / "feilong_backtest_events.csv"
        segment_manifest = output_dir / "feilong_backtest_segment_manifest.json"
        run_id = f"20260829-00{index:02d}00-{index:06d}"
        receipt_stamp = f"20260829-00{index:02d}01-{index:06d}"
        receipt = receipt_root / f"feilong-strategy-{receipt_stamp}.receipt.json"
        run_dir = receipt_root / "runs" / run_id
        business_result = run_dir / "business_result.json"
        business_stdout = run_dir / "business_child.stdout.txt"
        business_stderr = run_dir / "business_child.stderr.txt"
        write_json(backtest_json, valid_backtest_payload(root, core_end))
        write_empty_events_csv(events_csv)
        write_json(
            segment_manifest,
            {
                "schema": "FEILONG_BACKTEST_SEGMENT_MANIFEST_V1",
                "status": "CLEAN_PASS",
                "generated_at": "2026-08-29T00:00:00+08:00",
                "formula": {
                    "formula_type": "condition_selection",
                    "selection_formula": FORMULA["selection_formula"],
                    "indicator_formula": FORMULA["indicator_formula"],
                    "local_source_path": str((root / "飞龙裸三色.tdx.txt").resolve()),
                    "local_source_raw_sha256": FORMULA["local_source_raw_sha256"],
                    "gbk_payload_sha256": FORMULA["gbk_payload_sha256"],
                    "source_manifest_path": str((root / "formula-source-manifest.json").resolve()),
                    "source_manifest_sha256": "b" * 64,
                },
                "data": {
                    "start_date": "19901219",
                    "end_date": core_end,
                    "universe_count": 1,
                    "signal_count": 0,
                },
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
        )
        business_stdout.parent.mkdir(parents=True, exist_ok=True)
        business_stdout.write_text("fixture business stdout\n", encoding="utf-8")
        business_stderr.write_text("", encoding="utf-8")
        write_json(
            business_result,
            {
                "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
                "skill_id": "feilong-strategy",
                "status": "CLEAN_PASS",
                "business_process": {
                    "command": ["python", LEGACY_ENTRY, "run"],
                    "cwd": str(Path(LEGACY_ENTRY).parent.parent),
                    "returncode": 0,
                    "timed_out": False,
                    "failure_tokens": [],
                },
                "business_binding": {
                    "path": LEGACY_ENTRY,
                    "sha256": "c" * 64,
                },
                "artifacts": {
                    "stdout": str(business_stdout.resolve()),
                    "stderr": str(business_stderr.resolve()),
                    "backtest_json": artifact(backtest_json),
                    "events_csv": artifact(events_csv),
                    "segment_manifest": artifact(segment_manifest),
                },
            },
        )
        expected_extra_args = [
            "--timeout",
            "900",
            "--backtest",
            "--start-date",
            "19901219",
            "--end-date",
            core_end,
            "--out-dir",
            str(output_dir.resolve()),
            "--selection-formula",
            "飞龙裸三色",
            "--chunk-size",
            "240",
        ]
        receipt_stdout = receipt_root / f"{receipt.stem.removesuffix('.receipt')}.stdout.txt"
        receipt_stderr = receipt_root / f"{receipt.stem.removesuffix('.receipt')}.stderr.txt"
        receipt_stdout.write_text("fixture business stdout\n", encoding="utf-8")
        receipt_stderr.write_text("", encoding="utf-8")
        lianban_snapshot = run_dir / "lianban-daily.json"
        write_json(
            lianban_snapshot,
            {
                "schema": "LIANBAN_DAILY_SNAPSHOT_V1",
                "status": "CLEAN_PASS",
                "target_date": core_end,
            },
        )
        receipt_payload = {
            "receipt_version": 3,
            "runtime": "stock-canonical-runtime-v3",
            "runtime_surface": "Codex",
            "skill_id": "feilong-strategy",
            "entry": SKILL_ENTRY,
            "run_dir": str(run_dir.resolve()),
            "command": ["python", SKILL_ENTRY, "run", *expected_extra_args],
            "extra_args": expected_extra_args,
            "cwd": str(Path(SKILL_ENTRY).parent.parent),
            "started_at": "2026-08-29T00:00:00+08:00",
            "finished_at": "2026-08-29T00:00:01+08:00",
            "elapsed_seconds": 1.0,
            "returncode": 0,
            "status": "CLEAN_PASS",
            "facade_sha256": "d" * 64,
            "executor_sha256": "e" * 64,
            "contract_sha256": TEST_CONTRACT_SHA256,
            "business_bindings": [
                {
                    "path": str(Path(__file__).with_name("canonical_business_adapter.py")),
                    "sha256": "f" * 64,
                }
            ],
            "stock_business_lease": {
                "status": "ACQUIRED",
                "skill_id": "feilong-strategy",
                "lease_id": f"fixture-{index:02d}",
                "root_skill_id": "feilong-strategy",
                "root_lease_id": f"fixture-{index:02d}",
                "lock_path": str((receipt_root / "stock-business.lock").resolve()),
                "pid": 1,
                "acquired_at": "2026-08-29T00:00:00+08:00",
                "waited_seconds": 0.0,
            },
            "tdx_process_integrity": clean_process_integrity(),
            "tdx_process_guard": {
                "schema": "TDX_PROCESS_GUARD_AUDIT_V1",
                "status": "CLEAN_PASS",
                "path": str((run_dir / "tdx_process_guard.jsonl").resolve()),
                "exists": False,
                "event_count": 0,
                "events": [],
                "errors": [],
                "artifact": None,
            },
            "evidence_set": {
                "enabled": False,
                "status": "DISABLED",
                "environment": {},
                "errors": [],
            },
            "supplemental_sources": {
                "lianban_daily": {
                    "enabled": True,
                    "required": False,
                    "status": "CLEAN_PASS",
                    "client": r"D:\C盘转移\日志\codex\scripts\lianban_daily_client.py",
                    "command": ["python", "lianban_daily_client.py"],
                    "snapshot": artifact(lianban_snapshot),
                    "source_url": f"https://lianban.net/days/{core_end}.html",
                    "open_data_url": f"https://lianban.net/opendata/{core_end}.json",
                    "target_date_resolution": {
                        "status": "CLEAN_PASS",
                        "mode": "latest_available",
                        "target_date": core_end,
                        "fallback_date": core_end,
                        "errors": [],
                    },
                    "child": {
                        "effective_command": ["python", "lianban_daily_client.py"],
                        "started_at": "2026-08-29T00:00:00+08:00",
                        "finished_at": "2026-08-29T00:00:01+08:00",
                        "elapsed_seconds": 1.0,
                        "returncode": 0,
                        "stdout": "",
                        "stderr": "",
                        "tdx_process_integrity": clean_process_integrity(),
                    },
                    "environment": {
                        "CODEX_LIANBAN_STATUS": "CLEAN_PASS",
                        "CODEX_LIANBAN_SNAPSHOT": str(lianban_snapshot.resolve()),
                        "CODEX_LIANBAN_SOURCE_URL": f"https://lianban.net/days/{core_end}.html",
                        "CODEX_LIANBAN_OPEN_DATA_URL": f"https://lianban.net/opendata/{core_end}.json",
                        "CODEX_LIANBAN_ATTRIBUTION": "连板网",
                    },
                    "errors": [],
                }
            },
            "binding_errors": [],
            "business_stdout_validation": {"ok": True, "errors": []},
            "semantic_assertions": [
                {"type": "returncode_zero", "actual": 0, "ok": True},
                {"type": "stdout_nonempty", "actual_size": 1, "ok": True},
                {
                    "type": "output_contains_any",
                    "values": [
                        '"schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1"',
                        '"schema":"STOCK_CANONICAL_BUSINESS_RESULT_V1"',
                    ],
                    "found": ['"schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1"'],
                    "ok": True,
                },
                {
                    "type": "output_contains_any",
                    "values": [
                        '"status": "CLEAN_PASS"',
                        '"status":"CLEAN_PASS"',
                    ],
                    "found": ['"status": "CLEAN_PASS"'],
                    "ok": True,
                },
                {
                    "type": "output_not_contains",
                    "values": ["BLOCKED"],
                    "found": [],
                    "ok": True,
                },
                {
                    "type": "required_artifact",
                    "path": str(business_stdout.resolve()),
                    "minimum_size": 0,
                    "matched": 1,
                    "ok": True,
                },
                {
                    "type": "required_artifact",
                    "path": str(business_stderr.resolve()),
                    "minimum_size": 0,
                    "matched": 1,
                    "ok": True,
                },
                {
                    "type": "required_artifact",
                    "path": str(business_result.resolve()),
                    "minimum_size": 100,
                    "matched": 1,
                    "ok": True,
                },
            ],
            "required_artifacts": [
                artifact(business_stdout),
                artifact(business_stderr),
                artifact(business_result),
            ],
            "stdout_artifact": artifact(receipt_stdout),
            "stderr_artifact": artifact(receipt_stderr),
        }
        receipt_payload["receipt_integrity"] = receipt_hash(receipt_payload)
        write_json(receipt, receipt_payload)
        authorization = receipt_root / (
            f"{receipt.stem}.{artifact(segment_manifest)['sha256'][:16]}"
            ".delivery-authorization.json"
        )
        write_json(
            authorization,
            {
                "schema": "STOCK_DELIVERY_AUTHORIZATION_V1",
                "runtime": "stock-canonical-runtime-v3",
                "runtime_surface": "Codex",
                "skill_id": "feilong-strategy",
                "status": "CLEAN_PASS",
                "delivery_kind": "stock_artifact",
                "created_at": "2026-08-29T00:00:00+08:00",
                "receipt": {
                    "path": str(receipt.resolve()),
                    "sha256": artifact(receipt)["sha256"],
                    "contract_sha256": TEST_CONTRACT_SHA256,
                },
                "artifact": artifact(segment_manifest),
                "binding_source": "receipt_bound_manifest",
                "manifest_source": str(business_result.resolve()),
                "errors": [],
                "authorization": None,
                "authorization_path": str(authorization.resolve()),
            },
        )
        segments.append(
            {
                "core_start": core_start,
                "core_end": core_end,
                "invocation_start": "19901219",
                "invocation_end": core_end,
                "formula": dict(FORMULA),
                "backtest_json": str(backtest_json.resolve()),
                "events_csv": str(events_csv.resolve()),
                "events_csv_size": events_csv.stat().st_size,
                "events_csv_sha256": artifact(events_csv)["sha256"],
                "segment_manifest": artifact(segment_manifest),
                "receipt": artifact(receipt),
                "authorization": {
                    **artifact(authorization),
                    "status": "CLEAN_PASS",
                    "delivery_kind": "stock_artifact",
                    "binding_source": "receipt_bound_manifest",
                    "manifest_source": str(business_result.resolve()),
                },
            }
        )

    payload = {
        "schema": "FEILONG_NAKED_BACKTEST_DELIVERY_MANIFEST_V1",
        "status": "CLEAN_PASS",
        "delivery_status": "DONE_WITH_CONCERNS",
        "completion_scope": "merge-acceptor-output-not-live-backtest-claim",
        "formula": dict(FORMULA),
        "segments": segments,
        "inventory": {
            "status": "STRUCTURE_ALIGNED",
            "file_count": 12217,
            "valid_file_count": 12215,
            "anomaly_file_count": 2,
            "physical_start_date": "19901219",
            "physical_end_date": "20260826",
            "anomalies": [
                {"relative_path": "sz/lday/sz131804.day", "status": "ZERO_BYTE"},
                {"relative_path": "sz/lday/sz131807.day", "status": "ZERO_BYTE"},
            ],
            "nonstandard_filename_count": 1,
            "nonstandard_filenames": [
                {
                    "relative_path": "sz/lday/sz200b07.day",
                    "filename_status": "NONSTANDARD",
                    "size": 29216,
                    "sha256": NONSTANDARD_HASH,
                }
            ],
            "validation_scope": (
                "zero-byte anomalies, 32-byte record alignment, and first/last physical dates only; "
                "intermediate OHLC content not validated"
            ),
        },
        "invariants": {
            "partition_violation_count": 0,
            "nonfinite_metric_count": 0,
            "gross_metric_below_or_equal_minus_100_count": 0,
            "entry_date_order_violation_count": 0,
            "mae_horizon_monotonicity_violation_count": 0,
            "mfe_horizon_monotonicity_violation_count": 0,
            "stress_subtraction_violation_count": 0,
            "excursion_sign_violation_count": 0,
            "horizon_sample_count_monotonicity_violation_count": 0,
            "excluded_metric_violation_count": 0,
            "tradable_entry_violation_count": 0,
            "nonpositive_output_price_count": 0,
            "horizon_sample_counts": {key: 0 for key in ("1d", "3d", "5d", "10d", "20d")},
            "status": "CLEAN_PASS",
        },
        "artifacts": declared_artifacts,
    }
    payload["manifest_integrity"] = canonical_hash(payload)
    path = delivery / f"{DELIVERY_STEM}-交付manifest.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8-sig"
    )
    return path, payload


def validate_fixture(path: Path) -> dict[str, dict[str, object]]:
    return adapter.validate_delivery_manifest(
        path,
        receipt_root=path.parent.parent / "executions",
        expected_contract_sha256=TEST_CONTRACT_SHA256,
    )


def rewrite_manifest(path: Path, payload: dict, *, recompute: bool = True) -> None:
    if recompute:
        payload["manifest_integrity"] = canonical_hash(payload)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8-sig"
    )


def refresh_segment_chain(path: Path, payload: dict, index: int = 0) -> None:
    segment = payload["segments"][index]
    backtest_path = Path(segment["backtest_json"])
    events_path = Path(segment["events_csv"])
    segment_manifest_path = Path(segment["segment_manifest"]["path"])
    segment_manifest = json.loads(
        segment_manifest_path.read_text(encoding="utf-8-sig")
    )
    segment_manifest["artifacts"] = {
        "backtest_json": artifact(backtest_path),
        "events_csv": artifact(events_path),
    }
    write_json(segment_manifest_path, segment_manifest)

    old_authorization_path = Path(segment["authorization"]["path"])
    authorization = json.loads(
        old_authorization_path.read_text(encoding="utf-8-sig")
    )
    business_result_path = Path(authorization["manifest_source"])
    business_result = json.loads(
        business_result_path.read_text(encoding="utf-8-sig")
    )
    business_result["artifacts"]["backtest_json"] = artifact(backtest_path)
    business_result["artifacts"]["events_csv"] = artifact(events_path)
    business_result["artifacts"]["segment_manifest"] = artifact(
        segment_manifest_path
    )
    write_json(business_result_path, business_result)

    receipt_path = Path(segment["receipt"]["path"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    receipt["required_artifacts"] = [
        {
            **candidate,
            **artifact(Path(candidate["path"])),
        }
        for candidate in receipt["required_artifacts"]
    ]
    receipt["receipt_integrity"] = receipt_hash(receipt)
    write_json(receipt_path, receipt)

    new_authorization_path = receipt_path.parent / (
        f"{receipt_path.stem}.{artifact(segment_manifest_path)['sha256'][:16]}"
        ".delivery-authorization.json"
    )
    authorization["receipt"] = {
        "path": str(receipt_path.resolve()),
        "sha256": artifact(receipt_path)["sha256"],
        "contract_sha256": TEST_CONTRACT_SHA256,
    }
    authorization["artifact"] = artifact(segment_manifest_path)
    authorization["authorization_path"] = str(new_authorization_path.resolve())
    write_json(new_authorization_path, authorization)
    if old_authorization_path != new_authorization_path and old_authorization_path.exists():
        old_authorization_path.unlink()

    segment["events_csv_size"] = events_path.stat().st_size
    segment["events_csv_sha256"] = artifact(events_path)["sha256"]
    segment["segment_manifest"] = artifact(segment_manifest_path)
    segment["receipt"] = artifact(receipt_path)
    segment["authorization"] = {
        **artifact(new_authorization_path),
        "status": authorization["status"],
        "delivery_kind": authorization["delivery_kind"],
        "binding_source": authorization["binding_source"],
        "manifest_source": authorization["manifest_source"],
    }
    rewrite_manifest(path, payload)


def set_segment_signal_count(payload: dict, count: int, index: int = 0) -> None:
    segment = payload["segments"][index]
    backtest_path = Path(segment["backtest_json"])
    backtest = json.loads(backtest_path.read_text(encoding="utf-8-sig"))
    backtest["summary"]["signal_count"] = count
    backtest["data"]["signal_stock_count"] = count
    backtest["data"]["formula_calls"][0]["signal_count"] = count
    write_json(backtest_path, backtest)
    segment_manifest_path = Path(segment["segment_manifest"]["path"])
    segment_manifest = json.loads(
        segment_manifest_path.read_text(encoding="utf-8-sig")
    )
    segment_manifest["data"]["signal_count"] = count
    write_json(segment_manifest_path, segment_manifest)


class BusinessCommandTests(unittest.TestCase):
    def test_cli_parser_forwards_option_like_business_arguments(self) -> None:
        args = parse_cli_args(
            ["--run-dir", "run", "--timeout", "30", "--backtest", "--start-date", "20250101"]
        )

        self.assertEqual(args.run_dir, "run")
        self.assertEqual(args.business_args, ["--backtest", "--start-date", "20250101"])

    def test_default_command_ends_with_run(self) -> None:
        self.assertEqual(business_command(Path("unused"))[-1:], ["run"])

    def test_forwards_stock_and_json_arguments(self) -> None:
        self.assertEqual(
            business_command(Path("unused"), ["--", "300911", "--json"])[-3:],
            ["run", "300911", "--json"],
        )

    def test_valid_delivery_manifest_binding_returns_manifest_and_four_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            manifest_path, payload = write_valid_delivery_manifest(root)

            bound = validate_fixture(manifest_path)

            self.assertEqual(
                set(bound),
                {
                    "delivery_manifest",
                    "events_csv",
                    "summary_json",
                    "report_markdown",
                    "day_inventory_csv",
                },
            )
            self.assertEqual(bound["delivery_manifest"], artifact(manifest_path))
            for key in payload["artifacts"]:
                self.assertEqual(bound[key], payload["artifacts"][key])

    def test_delivery_manifest_rejects_missing_root_status(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            payload.pop("status")
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "root status"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_bad_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            payload["manifest_integrity"] = "0" * 64
            rewrite_manifest(path, payload, recompute=False)
            with self.assertRaisesRegex(RuntimeError, "integrity"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_wrong_formula_and_segment_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path, payload = write_valid_delivery_manifest(root / "formula")
            payload["formula"]["selection_formula"] = "飞龙在天AI"
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "formula"):
                validate_fixture(path)

            path, payload = write_valid_delivery_manifest(root / "segments")
            payload["segments"].pop()
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "segment count"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_inventory_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            payload["inventory"]["nonstandard_filenames"][0]["sha256"] = "0" * 64
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "inventory"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_artifact_hash_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            payload["artifacts"]["events_csv"]["sha256"] = "0" * 64
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "artifact hash"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_missing_artifact_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            Path(payload["artifacts"]["events_csv"]["path"]).unlink()
            with self.assertRaisesRegex(RuntimeError, "file missing"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_unknown_extra_artifact_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path, payload = write_valid_delivery_manifest(root)
            extra = root / "unexpected.txt"
            extra.write_text("unexpected\n", encoding="utf-8")
            payload["artifacts"]["unexpected"] = artifact(extra)
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "artifact keys"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_unknown_root_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            payload["unknown_root"] = "ACCEPTED"
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "root keys"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_unknown_nan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            payload["unknown_nan"] = float("nan")
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "non-finite"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_infinity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            payload["unknown_infinity"] = float("inf")
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "non-finite"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, _payload = write_valid_delivery_manifest(Path(temporary).resolve())
            text = path.read_text(encoding="utf-8-sig")
            text = text.replace(
                '  "status": "CLEAN_PASS",',
                '  "status": "BLOCKED",\n  "status": "CLEAN_PASS",',
                1,
            )
            path.write_text(text, encoding="utf-8-sig")
            with self.assertRaisesRegex(RuntimeError, "duplicate JSON key"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_unknown_nested_backtest_keys(self) -> None:
        mutations = (
            ("root", lambda payload: payload.__setitem__("unknown_root", True)),
            ("formula", lambda payload: payload["formula"].__setitem__("unknown_formula", True)),
            ("data", lambda payload: payload["data"].__setitem__("unknown_data", True)),
            (
                "execution_model",
                lambda payload: payload["execution_model"].__setitem__(
                    "unknown_execution_model", True
                ),
            ),
            ("summary", lambda payload: payload["summary"].__setitem__("unknown_summary", True)),
            (
                "horizon",
                lambda payload: payload["summary"]["horizons"]["1d"].__setitem__(
                    "unknown_horizon", True
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for label, mutate in mutations:
                with self.subTest(label=label):
                    path, payload = write_valid_delivery_manifest(root / label)
                    backtest_path = Path(payload["segments"][0]["backtest_json"])
                    backtest = json.loads(
                        backtest_path.read_text(encoding="utf-8-sig")
                    )
                    mutate(backtest)
                    write_json(backtest_path, backtest)
                    refresh_segment_chain(path, payload)
                    with self.assertRaisesRegex(RuntimeError, "backtest JSON.*keys"):
                        validate_fixture(path)

    def test_delivery_manifest_rejects_unknown_receipt_and_evidence_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for label in ("receipt", "required_artifact"):
                with self.subTest(label=label):
                    path, payload = write_valid_delivery_manifest(root / label)
                    receipt_path = Path(payload["segments"][0]["receipt"]["path"])
                    receipt = json.loads(
                        receipt_path.read_text(encoding="utf-8-sig")
                    )
                    if label == "receipt":
                        receipt["unknown_receipt_key"] = True
                    else:
                        receipt["required_artifacts"][0]["unknown_evidence_key"] = True
                    receipt["receipt_integrity"] = receipt_hash(receipt)
                    write_json(receipt_path, receipt)
                    refresh_segment_chain(path, payload)
                    with self.assertRaisesRegex(RuntimeError, "receipt.*keys"):
                        validate_fixture(path)

    def test_delivery_manifest_rejects_unknown_business_result_and_artifact_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for label in ("business_result", "artifacts"):
                with self.subTest(label=label):
                    path, payload = write_valid_delivery_manifest(root / label)
                    authorization_path = Path(
                        payload["segments"][0]["authorization"]["path"]
                    )
                    authorization = json.loads(
                        authorization_path.read_text(encoding="utf-8-sig")
                    )
                    business_path = Path(authorization["manifest_source"])
                    business = json.loads(
                        business_path.read_text(encoding="utf-8-sig")
                    )
                    if label == "business_result":
                        business["unknown_business_key"] = True
                    else:
                        business["artifacts"]["unknown_artifact"] = artifact(
                            business_path
                        )
                    write_json(business_path, business)
                    refresh_segment_chain(path, payload)
                    with self.assertRaisesRegex(RuntimeError, "business result.*keys"):
                        validate_fixture(path)

    def test_delivery_manifest_rejects_invalid_events_csv_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            events_path = Path(payload["segments"][0]["events_csv"])
            events_path.write_bytes(b"\x00\xffnot-a-csv")
            refresh_segment_chain(path, payload)
            with self.assertRaisesRegex(RuntimeError, "events CSV"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_events_csv_schema_and_row_drift(self) -> None:
        cases = (
            ("invalid_symbol", [valid_event_row(symbol="evil")], 1),
            ("out_of_range", [valid_event_row(signal_date="20270101")], 1),
            ("duplicate", [valid_event_row(), valid_event_row()], 2),
            ("count_mismatch", [valid_event_row()], 0),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for label, rows, declared_count in cases:
                with self.subTest(label=label):
                    path, payload = write_valid_delivery_manifest(root / label)
                    events_path = Path(payload["segments"][0]["events_csv"])
                    write_event_rows(events_path, rows)
                    set_segment_signal_count(payload, declared_count)
                    refresh_segment_chain(path, payload)
                    with self.assertRaisesRegex(RuntimeError, "events CSV"):
                        validate_fixture(path)

    def test_delivery_manifest_rejects_invalid_invariant_values(self) -> None:
        mutations = (
            (
                "nonzero_violation",
                lambda value: value.__setitem__("partition_violation_count", 999),
            ),
            (
                "bool_violation",
                lambda value: value.__setitem__("partition_violation_count", False),
            ),
            (
                "float_violation",
                lambda value: value.__setitem__("partition_violation_count", 0.0),
            ),
            (
                "negative_horizon",
                lambda value: value["horizon_sample_counts"].__setitem__("1d", -1),
            ),
            (
                "string_horizon",
                lambda value: value["horizon_sample_counts"].__setitem__("1d", "0"),
            ),
            (
                "null_horizon",
                lambda value: value["horizon_sample_counts"].__setitem__("1d", None),
            ),
            (
                "nonmonotonic_horizon",
                lambda value: value["horizon_sample_counts"].update(
                    {"1d": 0, "3d": 1, "5d": 0, "10d": 0, "20d": 0}
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for label, mutate in mutations:
                with self.subTest(label=label):
                    path, payload = write_valid_delivery_manifest(root / label)
                    mutate(payload["invariants"])
                    rewrite_manifest(path, payload)
                    with self.assertRaisesRegex(RuntimeError, "invariant"):
                        validate_fixture(path)

    def test_delivery_manifest_rejects_oversized_root_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, _payload = write_valid_delivery_manifest(Path(temporary).resolve())
            with path.open("ab") as handle:
                handle.write(b" " * (5 * 1024 * 1024))
            with self.assertRaisesRegex(RuntimeError, "size limit"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_forged_receipt_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            receipt_path = Path(payload["segments"][0]["receipt"]["path"])
            receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
            receipt["runtime"] = "forged-runtime"
            receipt["receipt_integrity"] = receipt_hash(receipt)
            write_json(receipt_path, receipt)
            payload["segments"][0]["receipt"] = artifact(receipt_path)
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "receipt identity"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_forged_authorization_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            authorization_path = Path(payload["segments"][0]["authorization"]["path"])
            authorization = json.loads(
                authorization_path.read_text(encoding="utf-8-sig")
            )
            authorization["receipt"]["sha256"] = "0" * 64
            write_json(authorization_path, authorization)
            payload["segments"][0]["authorization"] = {
                **artifact(authorization_path),
                "status": "CLEAN_PASS",
                "delivery_kind": "stock_artifact",
                "binding_source": "receipt_bound_manifest",
                "manifest_source": authorization["manifest_source"],
            }
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "authorization receipt binding"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_receipt_outside_fixed_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path, payload = write_valid_delivery_manifest(root)
            original = Path(payload["segments"][0]["receipt"]["path"])
            escaped = root / "outside" / original.name
            escaped.parent.mkdir()
            escaped.write_bytes(original.read_bytes())
            payload["segments"][0]["receipt"] = artifact(escaped)
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "fixed receipt root"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_authorization_outside_fixed_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path, payload = write_valid_delivery_manifest(root)
            original = Path(payload["segments"][0]["authorization"]["path"])
            escaped = root / "outside" / original.name
            escaped.parent.mkdir()
            escaped.write_bytes(original.read_bytes())
            payload["segments"][0]["authorization"] = {
                **artifact(escaped),
                "status": "CLEAN_PASS",
                "delivery_kind": "stock_artifact",
                "binding_source": "receipt_bound_manifest",
                "manifest_source": payload["segments"][0]["authorization"]["manifest_source"],
            }
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "fixed receipt root"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_business_result_outside_runs_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path, payload = write_valid_delivery_manifest(root)
            authorization_path = Path(payload["segments"][0]["authorization"]["path"])
            authorization = json.loads(
                authorization_path.read_text(encoding="utf-8-sig")
            )
            original = Path(authorization["manifest_source"])
            escaped = root / "outside" / "business_result.json"
            escaped.parent.mkdir()
            escaped.write_bytes(original.read_bytes())
            authorization["manifest_source"] = str(escaped.resolve())
            write_json(authorization_path, authorization)
            payload["segments"][0]["authorization"] = {
                **artifact(authorization_path),
                "status": "CLEAN_PASS",
                "delivery_kind": "stock_artifact",
                "binding_source": "receipt_bound_manifest",
                "manifest_source": str(escaped.resolve()),
            }
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "business result runs root"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_noncanonical_control_filenames(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()

            path, payload = write_valid_delivery_manifest(root / "receipt")
            segment = payload["segments"][0]
            old_receipt = Path(segment["receipt"]["path"])
            renamed_receipt = old_receipt.parent / "arbitrary.receipt.json"
            renamed_receipt.write_bytes(old_receipt.read_bytes())
            old_receipt.unlink()
            authorization_path = Path(segment["authorization"]["path"])
            authorization = json.loads(
                authorization_path.read_text(encoding="utf-8-sig")
            )
            authorization["receipt"]["path"] = str(renamed_receipt.resolve())
            authorization["receipt"]["sha256"] = artifact(renamed_receipt)["sha256"]
            write_json(authorization_path, authorization)
            segment["receipt"] = artifact(renamed_receipt)
            segment["authorization"] = {
                **artifact(authorization_path),
                "status": authorization["status"],
                "delivery_kind": authorization["delivery_kind"],
                "binding_source": authorization["binding_source"],
                "manifest_source": authorization["manifest_source"],
            }
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "receipt filename"):
                validate_fixture(path)

            path, payload = write_valid_delivery_manifest(root / "authorization")
            segment = payload["segments"][0]
            old_authorization = Path(segment["authorization"]["path"])
            authorization = json.loads(
                old_authorization.read_text(encoding="utf-8-sig")
            )
            renamed_authorization = old_authorization.parent / "arbitrary-authorization.json"
            authorization["authorization_path"] = str(
                renamed_authorization.resolve()
            )
            write_json(renamed_authorization, authorization)
            old_authorization.unlink()
            segment["authorization"] = {
                **artifact(renamed_authorization),
                "status": authorization["status"],
                "delivery_kind": authorization["delivery_kind"],
                "binding_source": authorization["binding_source"],
                "manifest_source": authorization["manifest_source"],
            }
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "authorization filename"):
                validate_fixture(path)

            path, payload = write_valid_delivery_manifest(root / "business")
            segment = payload["segments"][0]
            authorization_path = Path(segment["authorization"]["path"])
            authorization = json.loads(
                authorization_path.read_text(encoding="utf-8-sig")
            )
            old_business = Path(authorization["manifest_source"])
            renamed_business = old_business.with_name("arbitrary-result.json")
            renamed_business.write_bytes(old_business.read_bytes())
            old_business.unlink()
            receipt_path = Path(segment["receipt"]["path"])
            receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
            receipt["required_artifacts"] = [
                artifact(renamed_business)
                if Path(candidate["path"]).name == "business_result.json"
                else artifact(Path(candidate["path"]))
                for candidate in receipt["required_artifacts"]
            ]
            receipt["receipt_integrity"] = receipt_hash(receipt)
            write_json(receipt_path, receipt)
            authorization["receipt"]["sha256"] = artifact(receipt_path)["sha256"]
            authorization["manifest_source"] = str(renamed_business.resolve())
            write_json(authorization_path, authorization)
            segment["receipt"] = artifact(receipt_path)
            segment["authorization"] = {
                **artifact(authorization_path),
                "status": authorization["status"],
                "delivery_kind": authorization["delivery_kind"],
                "binding_source": authorization["binding_source"],
                "manifest_source": authorization["manifest_source"],
            }
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "business result filename"):
                validate_fixture(path)

    def test_delivery_manifest_rejects_oversized_control_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            receipt_path = Path(payload["segments"][0]["receipt"]["path"])
            with receipt_path.open("ab") as handle:
                handle.write(b" " * (5 * 1024 * 1024))
            payload["segments"][0]["receipt"] = artifact(receipt_path)
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "size limit"):
                validate_fixture(path)

    def test_large_final_artifact_is_streamed_not_read_whole(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            events_path = Path(payload["artifacts"]["events_csv"]["path"]).resolve()
            original_reader = adapter.read_stable_bytes

            def guarded_reader(candidate: Path, *, max_bytes=None):
                if Path(candidate).resolve() == events_path:
                    raise RuntimeError("large artifact was read whole")
                return original_reader(candidate, max_bytes=max_bytes)

            with mock.patch.object(adapter, "read_stable_bytes", side_effect=guarded_reader):
                try:
                    bound = validate_fixture(path)
                except RuntimeError as exc:
                    self.fail(str(exc))
            self.assertEqual(bound["events_csv"], artifact(events_path))

    def test_streamed_artifact_rejects_stat_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / "large.bin"
            path.write_bytes(b"X" * 1024)
            streamer = getattr(adapter, "_stream_file_evidence", None)
            self.assertIsNotNone(streamer, "streaming evidence helper missing")
            signature = adapter._file_signature(path)
            with mock.patch.object(
                adapter,
                "_file_signature",
                side_effect=[signature, (signature[0], signature[1] + 1, signature[2])],
            ):
                with self.assertRaisesRegex(RuntimeError, "changed while hashing"):
                    streamer(path)

    def test_delivery_manifest_rejects_relative_evidence_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path, payload = write_valid_delivery_manifest(Path(temporary).resolve())
            payload["segments"][0]["receipt"]["path"] = "relative-receipt.json"
            rewrite_manifest(path, payload)
            with self.assertRaisesRegex(RuntimeError, "absolute"):
                validate_fixture(path)

    def test_special_mode_never_calls_legacy_child_and_writes_clean_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            manifest_path, payload = write_valid_delivery_manifest(root)
            run_dir = root / "run"
            stdout = StringIO()
            with mock.patch.dict(
                os.environ, {"CODEX_STOCK_CANONICAL_EXECUTION": "1"}, clear=False
            ), mock.patch.object(
                adapter, "DEFAULT_RECEIPT_ROOT", root / "executions"
            ), mock.patch.object(
                adapter,
                "load_current_contract_sha256",
                return_value=TEST_CONTRACT_SHA256,
            ), mock.patch.object(
                adapter, "run_child", side_effect=AssertionError("legacy child called")
            ) as child, redirect_stdout(stdout):
                returncode = adapter.main(
                    [
                        "--run-dir",
                        str(run_dir),
                        "--",
                        "--bind-delivery-manifest",
                        str(manifest_path),
                    ]
                )

            child.assert_not_called()
            self.assertEqual(returncode, 0)
            self.assertIn("STOCK_CANONICAL_BUSINESS_RESULT_V1", stdout.getvalue())
            self.assertIn("CLEAN_PASS", stdout.getvalue())
            result = json.loads((run_dir / "business_result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "CLEAN_PASS")
            self.assertEqual(result["artifacts"]["delivery_manifest"], artifact(manifest_path))
            for key in payload["artifacts"]:
                self.assertEqual(result["artifacts"][key], payload["artifacts"][key])
            self.assertTrue((run_dir / "business_child.stdout.txt").is_file())
            self.assertTrue((run_dir / "business_child.stderr.txt").is_file())

    def test_special_mode_without_canonical_environment_writes_blocked_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            manifest_path, _payload = write_valid_delivery_manifest(root)
            run_dir = root / "run"
            stdout = StringIO()
            with mock.patch.dict(
                os.environ, {"CODEX_STOCK_CANONICAL_EXECUTION": ""}, clear=False
            ), mock.patch.object(
                adapter, "run_child", side_effect=AssertionError("legacy child called")
            ) as child, redirect_stdout(stdout):
                returncode = adapter.main(
                    [
                        "--run-dir",
                        str(run_dir),
                        "--bind-delivery-manifest",
                        str(manifest_path),
                    ]
                )

            child.assert_not_called()
            self.assertEqual(returncode, 2)
            for name in (
                "business_child.stdout.txt",
                "business_child.stderr.txt",
                "business_result.json",
            ):
                self.assertTrue((run_dir / name).is_file(), name)
            result = json.loads(
                (run_dir / "business_result.json").read_text(encoding="utf-8")
            )
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn(
                "canonical_execution_environment_missing",
                result["business_process"]["failure_tokens"],
            )

    def test_invalid_special_mode_still_writes_blocked_result_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            manifest_path, payload = write_valid_delivery_manifest(root)
            payload["manifest_integrity"] = "0" * 64
            rewrite_manifest(manifest_path, payload, recompute=False)
            run_dir = root / "run"
            with mock.patch.dict(
                os.environ, {"CODEX_STOCK_CANONICAL_EXECUTION": "1"}, clear=False
            ), mock.patch.object(adapter, "run_child") as child, redirect_stdout(StringIO()):
                returncode = adapter.main(
                    [
                        "--run-dir",
                        str(run_dir),
                        "--bind-delivery-manifest",
                        str(manifest_path),
                    ]
                )

            child.assert_not_called()
            self.assertEqual(returncode, 2)
            result = json.loads((run_dir / "business_result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(result["business_process"]["failure_tokens"])
            self.assertTrue((run_dir / "business_child.stdout.txt").is_file())
            self.assertTrue((run_dir / "business_child.stderr.txt").is_file())


if __name__ == "__main__":
    unittest.main()
