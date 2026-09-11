from __future__ import annotations

import sys
import csv
import importlib.util
import json
import struct
import tempfile
import unittest
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from point_in_time_snapshot import (
    DAY_RECORD,
    SnapshotBlocked,
    build_point_in_time_snapshot,
    load_blocknew_universe,
    read_tdx_day_file,
    resolve_trade_date,
    validate_strong_data_dates,
)
def write_day_file(path: Path, rows: list[tuple[date, float, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = bytearray()
    for trade_day, close, amount in rows:
        encoded_day = trade_day.year * 10000 + trade_day.month * 100 + trade_day.day
        close_cents = int(round(close * 100))
        payload.extend(
            struct.pack(
                "<IIIIIfII",
                encoded_day,
                close_cents,
                close_cents,
                close_cents,
                close_cents,
                float(amount),
                1000,
                0,
            )
        )
    path.write_bytes(bytes(payload))


def write_blocknew(blocknew: Path, blocks: list[tuple[str, str, list[str]]]) -> None:
    blocknew.mkdir(parents=True, exist_ok=True)
    config = bytearray()
    for name, alias, codes in blocks:
        record = bytearray(120)
        encoded_name = name.encode("gbk")
        encoded_alias = alias.encode("gbk")
        record[: len(encoded_name)] = encoded_name
        record[50 : 50 + len(encoded_alias)] = encoded_alias
        config.extend(record)
        (blocknew / f"{alias}.blk").write_text(
            "\n".join(codes) + "\n",
            encoding="gbk",
        )
    (blocknew / "blocknew.cfg").write_bytes(bytes(config))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ScientificForecastContractTests(unittest.TestCase):
    def test_tdx_day_parser_retains_only_records_at_or_before_cutoff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sz000001.day"
            write_day_file(
                path,
                [
                    (date(2026, 8, 20), 10.0, 1_000.0),
                    (date(2026, 8, 21), 10.5, 2_000.0),
                    (date(2026, 8, 24), 11.0, 3_000.0),
                ],
            )
            bars = read_tdx_day_file(path, cutoff_date=date(2026, 8, 21))
        self.assertEqual(DAY_RECORD.size, 32)
        self.assertEqual([bar.trade_date for bar in bars], [date(2026, 8, 20), date(2026, 8, 21)])
        self.assertEqual(bars[-1].close, 10.5)

    def test_blocknew_loader_reads_every_registered_block_without_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            blocknew = Path(temporary)
            blocks = [
                (f"Sector {index}", f"block{index:03d}", [f"{index:06d}"])
                for index in range(12)
            ]
            write_blocknew(blocknew, blocks)
            loaded = load_blocknew_universe(blocknew)
        self.assertEqual(len(loaded), 12)
        self.assertEqual({item["sector"] for item in loaded}, {item[0] for item in blocks})

    def test_snapshot_id_is_stable_and_low_coverage_sector_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            blocknew = root / "T0002" / "blocknew"
            vipdoc = root / "vipdoc"
            codes = [f"00000{index}" for index in range(1, 7)]
            write_blocknew(blocknew, [("Alpha", "alpha", codes)])
            for code in codes[:4]:
                write_day_file(
                    vipdoc / "sz" / "lday" / f"sz{code}.day",
                    [(date(2026, 8, 21), 10.0, 1_000.0)],
                )
            first = build_point_in_time_snapshot(
                requested_date=date(2026, 8, 23),
                cutoff_time=time(15, 0),
                blocknew_dir=blocknew,
                vipdoc_roots=[vipdoc],
            )
            second = build_point_in_time_snapshot(
                requested_date=date(2026, 8, 23),
                cutoff_time=time(15, 0),
                blocknew_dir=blocknew,
                vipdoc_roots=[vipdoc],
            )
        self.assertEqual(first["snapshot_id"], second["snapshot_id"])
        self.assertEqual(first["resolved_trade_date"], "2026-08-21")
        self.assertEqual(first["sectors"][0]["coverage_count"], 4)
        self.assertFalse(first["sectors"][0]["eligible_for_high_confidence"])

    def test_market_features_ignore_bars_after_snapshot_cutoff(self) -> None:
        from market_features import build_market_features

        def create_snapshot(root: Path, future_close: float) -> dict:
            blocknew = root / "T0002" / "blocknew"
            vipdoc = root / "vipdoc"
            codes = [f"00000{index}" for index in range(1, 6)]
            write_blocknew(blocknew, [("Alpha", "alpha", codes)])
            for index, code in enumerate(codes):
                write_day_file(
                    vipdoc / "sz" / "lday" / f"sz{code}.day",
                    [
                        (date(2026, 8, 18), 9.8 + index, 900.0),
                        (date(2026, 8, 19), 10.0 + index, 1_000.0),
                        (date(2026, 8, 20), 10.2 + index, 1_100.0),
                        (date(2026, 8, 21), 10.4 + index, 1_200.0),
                        (date(2026, 8, 24), future_close + index, 9_000.0),
                    ],
                )
            return build_point_in_time_snapshot(
                requested_date=date(2026, 8, 21),
                cutoff_time=time(15, 0),
                blocknew_dir=blocknew,
                vipdoc_roots=[vipdoc],
            )

        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = build_market_features(create_snapshot(Path(first_dir), 20.0))
            second = build_market_features(create_snapshot(Path(second_dir), 200.0))
        comparable_fields = (
            "return_1d",
            "return_3d",
            "breadth",
            "amount_ratio",
            "volatility",
            "drawdown",
        )
        for field in comparable_fields:
            self.assertAlmostEqual(first["sectors"][0][field], second["sectors"][0][field])
        self.assertEqual(first["feature_cutoff_date"], "2026-08-21")

    def test_zero_coverage_sector_cannot_receive_a_rank(self) -> None:
        from market_features import build_market_features

        snapshot = {
            "snapshot_id": "snapshot-1",
            "resolved_trade_date": "2026-08-21",
            "sectors": [
                {
                    "sector": "NoData",
                    "member_count": 6,
                    "coverage_count": 0,
                    "coverage_ratio": 0.0,
                    "eligible_for_high_confidence": False,
                    "current_member_sources": [],
                }
            ],
        }
        row = build_market_features(snapshot)["sectors"][0]
        self.assertIsNone(row["rank_percentile"])
        self.assertFalse(row["rank_eligible"])
        self.assertEqual(row["coverage_missing"], 1)

    def test_future_horizons_use_distinct_trading_day_slices(self) -> None:
        from future_labels import HORIZONS, build_future_activity_labels

        trading_days = [date(2026, 8, 24 + offset) for offset in range(8)] + [
            date(2026, 9, 1),
            date(2026, 9, 2),
        ]
        rows: list[dict] = []
        for sector in ("Alpha", "Beta"):
            for index, trade_day in enumerate(trading_days, start=1):
                alpha_hot = sector == "Alpha" and index <= 3
                beta_hot = sector == "Beta" and index >= 4
                hot = alpha_hot or beta_hot
                rows.append(
                    {
                        "sector": sector,
                        "trade_date": trade_day,
                        "sector_return": 0.03 if hot else -0.01,
                        "market_return": 0.0,
                        "breadth": 0.8 if hot else 0.2,
                        "baseline_breadth": 0.5,
                        "activity_expansion": 0.7 if hot else -0.2,
                        "limit_leader_continuity": 0.9 if hot else 0.1,
                        "persistence": 0.9 if hot else 0.1,
                    }
                )
        labels = build_future_activity_labels(date(2026, 8, 21), rows)
        by_key = {(row["sector"], row["horizon"]): row for row in labels}
        self.assertEqual(HORIZONS, {"H1": (1, 3), "H2": (4, 7), "H3": (8, 10)})
        self.assertGreater(
            by_key[("Alpha", "H1")]["future_activity_score"],
            by_key[("Beta", "H1")]["future_activity_score"],
        )
        self.assertGreater(
            by_key[("Beta", "H2")]["future_activity_score"],
            by_key[("Alpha", "H2")]["future_activity_score"],
        )
        self.assertEqual(by_key[("Alpha", "H1")]["window_dates"], [
            "2026-08-24",
            "2026-08-25",
            "2026-08-26",
        ])
        self.assertEqual(len(by_key[("Alpha", "H3")]["window_dates"]), 3)

    def test_walk_forward_splits_are_grouped_and_apply_two_embargoes(self) -> None:
        from walk_forward_backtest import expanding_walk_forward_splits

        dates = [date(2024, 1, 1) + timedelta(days=index) for index in range(410)]
        split = expanding_walk_forward_splits(dates)[0]
        self.assertEqual(len(split.train_dates), 252)
        self.assertEqual(len(split.validation_dates), 60)
        self.assertEqual(len(split.test_dates), 60)
        index_by_date = {value: index for index, value in enumerate(dates)}
        self.assertEqual(
            index_by_date[split.validation_dates[0]] - index_by_date[split.train_dates[-1]],
            11,
        )
        self.assertEqual(
            index_by_date[split.test_dates[0]] - index_by_date[split.validation_dates[-1]],
            11,
        )
        self.assertTrue(set(split.train_dates).isdisjoint(split.validation_dates))
        self.assertTrue(set(split.validation_dates).isdisjoint(split.test_dates))

    def test_walk_forward_row_partition_never_splits_a_trade_date(self) -> None:
        from walk_forward_backtest import expanding_walk_forward_splits, partition_rows_by_split

        dates = [date(2024, 1, 1) + timedelta(days=index) for index in range(410)]
        rows = [
            {"trade_date": trade_day, "sector": sector}
            for trade_day in dates
            for sector in ("Alpha", "Beta", "Gamma")
        ]
        split = expanding_walk_forward_splits(dates)[0]
        partition = partition_rows_by_split(rows, split)
        date_sets = {
            name: {row["trade_date"] for row in values}
            for name, values in partition.items()
        }
        self.assertTrue(date_sets["train"].isdisjoint(date_sets["validation"]))
        self.assertTrue(date_sets["validation"].isdisjoint(date_sets["test"]))
        self.assertEqual(len(partition["train"]), 252 * 3)

    def test_preprocessing_is_fit_on_training_rows_only(self) -> None:
        from forecast_model import TrainOnlyPreprocessor

        preprocessor = TrainOnlyPreprocessor(["momentum", "breadth"])
        preprocessor.fit(
            [
                {"momentum": 1.0, "breadth": None},
                {"momentum": 3.0, "breadth": 0.6},
            ]
        )
        before = preprocessor.to_model_card()
        transformed = preprocessor.transform(
            [{"momentum": 1_000_000.0, "breadth": None}]
        )
        after = preprocessor.to_model_card()
        self.assertEqual(before, after)
        self.assertEqual(before["fit_row_count"], 2)
        self.assertEqual(before["medians"]["momentum"], 2.0)
        self.assertEqual(transformed.shape, (1, 4))

    def test_provisional_models_emit_independent_bounded_horizon_probabilities(self) -> None:
        from forecast_model import forecast_with_provisional_models

        feature_snapshot = {
            "snapshot_id": "snapshot-1",
            "feature_cutoff_date": "2026-08-21",
            "sectors": [
                {
                    "sector": "Alpha",
                    "rank_eligible": True,
                    "return_1d": 0.05,
                    "return_3d": 0.08,
                    "relative_return_5d": 0.06,
                    "breadth": 0.8,
                    "amount_ratio": 1.8,
                    "limit_up_density": 0.2,
                    "persistence": 0.8,
                    "volatility": 0.03,
                    "drawdown": -0.02,
                    "coverage_ratio": 1.0,
                }
            ],
        }
        result = forecast_with_provisional_models(feature_snapshot)
        rows = result["forecasts"]
        self.assertEqual({row["horizon"] for row in rows}, {"H1", "H2", "H3"})
        probabilities = [row["market_probability"] for row in rows]
        self.assertTrue(all(0.0 <= value <= 1.0 for value in probabilities))
        self.assertEqual(len(set(probabilities)), 3)
        self.assertEqual(result["forecast_status"], "PROVISIONAL_FORECAST")
        self.assertEqual(set(result["model_card"]["models"]), {"H1", "H2", "H3"})

    def test_validation_status_requires_every_scientific_gate(self) -> None:
        from walk_forward_backtest import determine_forecast_status

        passing = {
            "precision_at_top5": 0.25,
            "precision_lift_vs_best_baseline": 0.30,
            "pr_auc_above_base_rate": True,
            "pr_auc_delta_ci_lower": 0.01,
            "rank_ic": 0.05,
            "rank_ic_ci_lower": 0.01,
            "brier_skill_score": 0.10,
            "ece": 0.05,
            "windows_led_fraction": 0.75,
            "regime_rank_ic": {"bull": 0.02, "bear": 0.01, "sideways": 0.03},
            "regime_days": {"bull": 80, "bear": 70, "sideways": 90},
        }
        accepted = determine_forecast_status(passing, point_in_time_membership=True)
        self.assertEqual(accepted["forecast_status"], "VALIDATED_FORECAST")
        failing = dict(passing)
        failing["rank_ic_ci_lower"] = -0.001
        rejected = determine_forecast_status(failing, point_in_time_membership=True)
        self.assertEqual(rejected["forecast_status"], "PROVISIONAL_FORECAST")
        self.assertIn("rank_ic_ci_lower_not_positive", rejected["reasons"])

    def test_walk_forward_calibration_never_fits_test_dates(self) -> None:
        from walk_forward_backtest import run_walk_forward_backtest

        dates = [date(2026, 1, 1) + timedelta(days=index) for index in range(24)]
        rows: list[dict] = []
        for horizon_index, horizon in enumerate(("H1", "H2", "H3")):
            for day_index, trade_day in enumerate(dates):
                for sector_index, sector in enumerate(("Alpha", "Beta", "Gamma")):
                    positive = sector == ("Alpha" if day_index % 2 == 0 else "Beta")
                    rows.append(
                        {
                            "trade_date": trade_day,
                            "horizon": horizon,
                            "sector": sector,
                            "momentum": (1.0 if positive else -0.5) + horizon_index * 0.1,
                            "is_top_decile": int(positive),
                            "future_activity_score": 0.9 if positive else 0.1 + sector_index * 0.01,
                            "baseline_top5_precision": 1 / 3,
                            "regime": ("bull", "bear", "sideways")[day_index % 3],
                        }
                    )
        result = run_walk_forward_backtest(
            rows,
            feature_names=["momentum"],
            split_kwargs={
                "min_train_dates": 8,
                "validation_dates": 6,
                "test_dates": 6,
                "embargo_dates": 2,
                "step_dates": 6,
            },
            bootstrap_samples=20,
        )
        self.assertEqual(result["fold_count"], 1)
        fold = result["folds"][0]
        test_dates = set(fold["test_dates"])
        for card in fold["models"].values():
            self.assertTrue(set(card["training_dates"]).isdisjoint(test_dates))
            self.assertTrue(set(card["validation_dates"]).isdisjoint(test_dates))
            self.assertEqual(set(card["calibration_fit_dates"]), set(card["validation_dates"]))
        self.assertEqual(
            {row["trade_date"] for row in result["predictions"]},
            test_dates,
        )

    def test_post_cutoff_catalyst_evidence_is_rejected(self) -> None:
        from catalyst_features import EvidenceBlocked, validate_evidence_rows

        cutoff = datetime(2026, 8, 21, 15, 0, tzinfo=timezone.utc)
        evidence = [
            {
                "evidence_id": "e-1",
                "sector": "Alpha",
                "published_time": "2026-08-21T15:01:00+00:00",
                "collected_time": "2026-08-21T15:02:00+00:00",
                "source_grade": "A",
                "novelty": 1.0,
                "directness": 1.0,
                "magnitude": 1.0,
                "pollution_state": "PASS",
                "counter_evidence": 0.0,
            }
        ]
        with self.assertRaises(EvidenceBlocked):
            validate_evidence_rows(evidence, cutoff)

    def test_low_grade_evidence_is_weaker_and_provisional_fusion_is_bounded(self) -> None:
        from catalyst_features import fuse_catalysts

        cutoff = datetime(2026, 8, 21, 15, 0, tzinfo=timezone.utc)
        forecast = [{"sector": "Alpha", "horizon": "H1", "market_probability": 0.30}]

        def evidence(grade: str) -> list[dict]:
            return [
                {
                    "evidence_id": f"e-{grade}",
                    "sector": "Alpha",
                    "published_time": "2026-08-21T14:00:00+00:00",
                    "collected_time": "2026-08-21T14:30:00+00:00",
                    "source_grade": grade,
                    "novelty": 1.0,
                    "directness": 1.0,
                    "magnitude": 1.0,
                    "pollution_state": "PASS",
                    "counter_evidence": 0.0,
                }
            ]

        official = fuse_catalysts(forecast, evidence("A"), cutoff, "PROVISIONAL_FORECAST")[0]
        social = fuse_catalysts(forecast, evidence("D"), cutoff, "PROVISIONAL_FORECAST")[0]
        self.assertGreater(official["catalyst_adjustment"], social["catalyst_adjustment"])
        self.assertLessEqual(abs(official["catalyst_adjustment"]), 0.10)
        self.assertLessEqual(abs(social["catalyst_adjustment"]), 0.10)

    def test_missing_catalyst_evidence_has_zero_adjustment(self) -> None:
        from catalyst_features import fuse_catalysts

        row = fuse_catalysts(
            [{"sector": "Alpha", "horizon": "H1", "market_probability": 0.30}],
            [],
            datetime(2026, 8, 21, 15, 0, tzinfo=timezone.utc),
            "PROVISIONAL_FORECAST",
        )[0]
        self.assertEqual(row["catalyst_adjustment"], 0.0)
        self.assertEqual(row["final_probability"], 0.30)
        self.assertEqual(row["evidence_ids"], [])

    def test_leader_rows_preserve_snapshot_sector_and_member_lineage(self) -> None:
        from leader_ranker import rank_leaders

        snapshot = {
            "snapshot_id": "snapshot-1",
            "resolved_trade_date": "2026-08-21",
            "sectors": [
                {
                    "sector": "Alpha",
                    "members": ["000001", "000002"],
                    "current_member_sources": [
                        {"code": "000001", "relative_strength": 0.08, "amount_ratio": 2.0},
                        {"code": "000002", "relative_strength": 0.03, "amount_ratio": 1.2},
                    ],
                },
                {
                    "sector": "Beta",
                    "members": ["000003"],
                    "current_member_sources": [
                        {"code": "000003", "relative_strength": 0.20, "amount_ratio": 3.0}
                    ],
                },
            ],
        }
        forecasts = [
            {
                "snapshot_id": "snapshot-1",
                "sector": "Alpha",
                "horizon": "H1",
                "market_rank": 1,
                "final_probability": 0.70,
            }
        ]
        rows = rank_leaders(snapshot, forecasts)
        self.assertTrue(rows)
        self.assertLessEqual({row["code"] for row in rows}, {"000001", "000002"})
        self.assertEqual({row["snapshot_id"] for row in rows}, {"snapshot-1"})
        self.assertEqual({row["sector"] for row in rows}, {"Alpha"})
        for row in rows:
            self.assertEqual(row["sector_forecast_probability"], 0.70)
            self.assertTrue(row["reasons"])
            self.assertTrue(row["risks"])
            self.assertTrue(row["invalidation"])

    def test_manifest_hash_mismatch_blocks_delivery(self) -> None:
        from forecast_gate import REQUIRED_DELIVERABLES, write_delivery_manifest, validate_delivery_manifest

        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            for name in REQUIRED_DELIVERABLES:
                if name != "manifest.json":
                    (output_dir / name).write_text(f"content:{name}\n", encoding="utf-8")
            manifest = write_delivery_manifest(
                output_dir,
                snapshot_id="snapshot-1",
                resolved_trade_date="2026-08-21",
                forecast_status="PROVISIONAL_FORECAST",
                model_version="transparent-provisional-v1",
            )
            clean = validate_delivery_manifest(manifest, output_dir)
            (output_dir / "report.md").write_text("tampered\n", encoding="utf-8")
            blocked = validate_delivery_manifest(manifest, output_dir)
        self.assertEqual(clean["status"], "CLEAN_PASS")
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertTrue(any("artifact_hash_mismatch:report.md" in value for value in blocked["errors"]))

    def test_all_mode_accepts_explicit_date_and_writes_one_lineage_bound_delivery(self) -> None:
        from forecast_gate import REQUIRED_DELIVERABLES
        from merged_workflow import run_forecast

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            blocknew = root / "T0002" / "blocknew"
            vipdoc = root / "vipdoc"
            output_dir = root / "deliverables"
            codes = [f"00000{index}" for index in range(1, 7)]
            write_blocknew(blocknew, [("Alpha", "alpha", codes)])
            dates = [date(2026, 8, 14) + timedelta(days=index) for index in range(8)]
            for member_index, code in enumerate(codes):
                write_day_file(
                    vipdoc / "sz" / "lday" / f"sz{code}.day",
                    [
                        (
                            trade_day,
                            10.0 + member_index + day_index * 0.15,
                            1_000.0 + day_index * 100,
                        )
                        for day_index, trade_day in enumerate(dates)
                    ],
                )
            result = run_forecast(
                mode="all",
                requested_date=date(2026, 8, 23),
                output_dir=output_dir,
                blocknew_dir=blocknew,
                vipdoc_roots=[vipdoc],
                evidence_rows=[],
            )
            snapshot = json.loads((output_dir / "forecast_snapshot.json").read_text(encoding="utf-8"))
            features = json.loads((output_dir / "feature_snapshot.json").read_text(encoding="utf-8"))
            with (output_dir / "forecast_rank.csv").open(encoding="utf-8", newline="") as handle:
                forecasts = list(csv.DictReader(handle))
            with (output_dir / "leader_rank.csv").open(encoding="utf-8", newline="") as handle:
                leaders = list(csv.DictReader(handle))
            existing = {path.name for path in output_dir.iterdir() if path.is_file()}
        self.assertEqual(result["status"], "CLEAN_PASS")
        self.assertEqual(result["forecast_status"], "PROVISIONAL_FORECAST")
        self.assertEqual(result["resolved_trade_date"], "2026-08-21")
        self.assertEqual(existing, set(REQUIRED_DELIVERABLES))
        self.assertEqual(snapshot["snapshot_id"], result["snapshot_id"])
        self.assertEqual(features["snapshot_id"], result["snapshot_id"])
        self.assertEqual({row["snapshot_id"] for row in forecasts}, {result["snapshot_id"]})
        self.assertEqual({row["snapshot_id"] for row in leaders}, {result["snapshot_id"]})
        self.assertEqual({row["horizon"] for row in forecasts}, {"H1", "H2", "H3"})
        self.assertLessEqual({row["sector"] for row in leaders}, {row["sector"] for row in forecasts})

    def test_legacy_selftest_requires_every_scientific_forecast_module(self) -> None:
        legacy = load_module("scientific_forecast_legacy_test", SCRIPTS / "legacy_codex_entry.py")
        required = set(legacy.REQUIRED)
        self.assertTrue(
            {
                "references/2026-08-23-scientific-forecast-design.md",
                "references/2026-08-23-scientific-forecast-implementation-plan.md",
                "scripts/point_in_time_snapshot.py",
                "scripts/market_features.py",
                "scripts/future_labels.py",
                "scripts/forecast_model.py",
                "scripts/walk_forward_backtest.py",
                "scripts/catalyst_features.py",
                "scripts/leader_ranker.py",
                "scripts/forecast_gate.py",
            }.issubset(required)
        )

    def test_adapter_accepts_complete_provisional_delivery_without_relabeling(self) -> None:
        from canonical_business_adapter import validate_child_delivery
        from forecast_gate import REQUIRED_DELIVERABLES, write_delivery_manifest

        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            for name in REQUIRED_DELIVERABLES:
                if name != "manifest.json":
                    (output_dir / name).write_text(f"content:{name}\n", encoding="utf-8")
            write_delivery_manifest(
                output_dir,
                snapshot_id="snapshot-1",
                resolved_trade_date="2026-08-21",
                forecast_status="PROVISIONAL_FORECAST",
                model_version="transparent-provisional-v1",
            )
            child = {
                "status": "CLEAN_PASS",
                "forecast_status": "PROVISIONAL_FORECAST",
                "snapshot_id": "snapshot-1",
                "resolved_trade_date": "2026-08-21",
                "manifest_path": str(output_dir / "manifest.json"),
            }
            accepted = validate_child_delivery(child, output_dir)
        self.assertEqual(accepted["status"], "CLEAN_PASS")
        self.assertEqual(accepted["forecast_status"], "PROVISIONAL_FORECAST")
        self.assertEqual(accepted["snapshot_id"], "snapshot-1")

    def test_adapter_blocks_when_any_forecast_artifact_is_missing(self) -> None:
        from canonical_business_adapter import validate_child_delivery
        from forecast_gate import REQUIRED_DELIVERABLES, write_delivery_manifest

        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            for name in REQUIRED_DELIVERABLES:
                if name != "manifest.json":
                    (output_dir / name).write_text(f"content:{name}\n", encoding="utf-8")
            write_delivery_manifest(
                output_dir,
                snapshot_id="snapshot-1",
                resolved_trade_date="2026-08-21",
                forecast_status="PROVISIONAL_FORECAST",
                model_version="transparent-provisional-v1",
            )
            (output_dir / "leader_rank.csv").unlink()
            child = {
                "status": "CLEAN_PASS",
                "forecast_status": "PROVISIONAL_FORECAST",
                "snapshot_id": "snapshot-1",
                "resolved_trade_date": "2026-08-21",
                "manifest_path": str(output_dir / "manifest.json"),
            }
            blocked = validate_child_delivery(child, output_dir)
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertTrue(any("leader_rank.csv" in value for value in blocked["errors"]))

    def test_adapter_canonical_output_environment_overrides_inherited_value(self) -> None:
        from canonical_business_adapter import build_child_environment

        environment = build_child_environment(
            Path(r"C:\canonical-run\deliverables"),
            inherited={"SHORTLINE_CANONICAL_DELIVERABLES_DIR": r"C:\user-controlled"},
        )
        self.assertEqual(
            environment["SHORTLINE_CANONICAL_DELIVERABLES_DIR"],
            str(Path(r"C:\canonical-run\deliverables").resolve()),
        )

    def test_requested_weekend_resolves_to_latest_tdx_trade_date(self) -> None:
        available = [date(2026, 8, 20), date(2026, 8, 21)]
        self.assertEqual(
            resolve_trade_date(date(2026, 8, 23), available),
            date(2026, 8, 21),
        )

    def test_mixed_strong_data_dates_block_snapshot(self) -> None:
        with self.assertRaises(SnapshotBlocked):
            validate_strong_data_dates(
                date(2026, 8, 21),
                {date(2026, 8, 20), date(2026, 8, 21)},
            )

    def test_provisional_catalyst_adjustment_is_clamped(self) -> None:
        from catalyst_features import apply_catalyst_adjustment

        self.assertAlmostEqual(
            apply_catalyst_adjustment(
                0.30,
                0.80,
                "PROVISIONAL_FORECAST",
            ),
            0.40,
        )

    def test_hard_fail_cannot_increase_probability(self) -> None:
        from catalyst_features import apply_catalyst_adjustment

        adjusted = apply_catalyst_adjustment(
            0.30,
            0.80,
            "PROVISIONAL_FORECAST",
            "HARD_FAIL",
        )
        self.assertLessEqual(adjusted, 0.30)

    def test_leaders_are_limited_to_forecast_sector_members(self) -> None:
        from leader_ranker import rank_leaders

        snapshot = {
            "snapshot_id": "snapshot-1",
            "sectors": [
                {
                    "sector": "Alpha",
                    "members": [
                        {"code": "000001", "relative_strength": 0.8},
                        {"code": "000002", "relative_strength": 0.5},
                    ],
                },
                {
                    "sector": "Beta",
                    "members": [
                        {"code": "000003", "relative_strength": 0.9},
                    ],
                },
            ],
        }
        forecasts = [
            {
                "snapshot_id": "snapshot-1",
                "sector": "Alpha",
                "final_probability": 0.70,
            }
        ]
        rows = rank_leaders(snapshot, forecasts)
        self.assertLessEqual(
            {row["sector"] for row in rows},
            {row["sector"] for row in forecasts},
        )

    def test_incomplete_manifest_is_not_clean(self) -> None:
        from forecast_gate import validate_delivery_manifest

        incomplete_manifest = {
            "snapshot_id": "snapshot-1",
            "forecast_status": "PROVISIONAL_FORECAST",
            "artifacts": [],
        }
        with tempfile.TemporaryDirectory() as temporary:
            result = validate_delivery_manifest(
                incomplete_manifest,
                Path(temporary),
            )
        self.assertEqual(result["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
