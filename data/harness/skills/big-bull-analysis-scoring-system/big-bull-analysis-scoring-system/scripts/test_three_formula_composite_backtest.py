from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import importlib.util
import json
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pytest


MODULE_PATH = Path(__file__).with_name("three_formula_composite_backtest.py")
SPEC = importlib.util.spec_from_file_location("three_formula_composite_backtest", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_subsystem_catalog_has_fixed_30_rows():
    catalog = MODULE.subsystem_catalog()

    assert len(catalog) == 30
    assert [row["formula"] for row in catalog].count("大牛线撑压版") == 16
    assert [row["formula"] for row in catalog].count("飞龙在天") == 10
    assert [row["formula"] for row in catalog].count("庄家资金监控") == 4
    assert [row["key"] for row in catalog] == list(dict.fromkeys(row["key"] for row in catalog))


def test_dealer_catalog_uses_four_real_formula_variables_not_plot_outputs():
    catalog = MODULE.subsystem_catalog()
    dealer = [row for row in catalog if row["formula"] == "庄家资金监控"]

    assert [row["name"] for row in dealer] == [
        "成本压力B2",
        "资金强度B5",
        "控盘差值B6",
        "控盘程度",
    ]
    assert all(not row["forced_zero_reason"] for row in dealer)


def test_all_thirty_subsystems_are_real_formula_features_without_forced_zero_weights():
    catalog = MODULE.subsystem_catalog()

    assert len(catalog) == 30
    assert all(not row["forced_zero_reason"] for row in catalog)
    assert [
        row["key"] for row in catalog if row["formula"] == MODULE.DEALER_FORMULA
    ] == [
        "zj_cost_pressure",
        "zj_fund_strength",
        "zj_control_spread",
        "zj_control_degree",
    ]


def test_research_model_requires_and_weights_every_one_of_thirty_items():
    catalog = MODULE.subsystem_catalog()
    symbols = ["000001.SZ", "000002.SZ", "600000.SH", "600001.SH"]
    rows = []
    for position, symbol in enumerate(symbols, start=1):
        values = {
            row["key"]: float(position + index)
            for index, row in enumerate(catalog)
        }
        values["fl_dragon"] = 0.0
        rows.append({"date": "20260818", "symbol": symbol, **values})

    _, model = MODULE.build_research_model_for_frame(
        MODULE.pd.DataFrame(rows), symbols
    )

    assert len(model["subsystem_weights"]) == 30
    assert all(row["local_weight"] > 0 for row in model["subsystem_weights"])
    assert all(not row["forced_zero_reason"] for row in model["subsystem_weights"])
    assert model["metadata"]["active_subsystem_count"] == 30


def test_research_model_fails_closed_when_any_real_item_is_missing():
    catalog = MODULE.subsystem_catalog()
    symbols = ["000001.SZ", "000002.SZ", "600000.SH", "600001.SH"]
    rows = []
    for position, symbol in enumerate(symbols, start=1):
        values = {
            row["key"]: float(position + index)
            for index, row in enumerate(catalog)
        }
        if symbol == symbols[-1]:
            values["zj_control_degree"] = np.nan
        rows.append({"date": "20260818", "symbol": symbol, **values})

    with pytest.raises(ValueError, match="thirty_item_data_incomplete"):
        MODULE.build_research_model_for_frame(MODULE.pd.DataFrame(rows), symbols)


def test_chronological_split_keeps_holdout_strictly_after_training():
    dates = np.array([f"2024{i:04d}" for i in range(1, 101)])
    split = MODULE.chronological_split(
        dates,
        train_ratio=0.6,
        validation_ratio=0.2,
        purge_dates=2,
    )

    assert split["train"].sum() == 58
    assert split["validation"].sum() == 18
    assert split["test"].sum() == 20
    assert max(dates[split["train"]]) < min(dates[split["validation"]])
    assert max(dates[split["validation"]]) < min(dates[split["test"]])
    assert split["purged_train_dates"].tolist() == ["20240059", "20240060"]
    assert split["purged_validation_dates"].tolist() == ["20240079", "20240080"]


def test_information_constraints_are_fit_on_training_dates_only():
    catalog = MODULE.subsystem_catalog()
    keys = [row["key"] for row in catalog]
    rows = []
    dates = [f"2024{i:04d}" for i in range(1, 101)]
    for date_index, date in enumerate(dates):
        for symbol_index in range(10):
            row = {
                "date": date,
                "symbol": f"S{symbol_index:03d}",
                "target": float(symbol_index) / 100.0,
            }
            row.update({key: float(symbol_index) for key in keys})
            row["dnx_main_trend"] = (
                float(symbol_index) if date_index >= 80 else 1.0
            )
            rows.append(row)
    raw_frame = MODULE.pd.DataFrame(rows)

    frame, audited, diagnostics, split = MODULE.prepare_backtest_frame(
        raw_frame,
        catalog,
        purge_dates=2,
    )

    main_trend = next(row for row in audited if row["key"] == "dnx_main_trend")
    assert "无横截面区分度" in main_trend["forced_zero_reason"]
    assert diagnostics["dnx_main_trend"]["informative_dates"] == 0
    assert len(frame) == len(raw_frame)
    assert split["test"].sum() == 200


def test_percentile_score_is_bounded_and_monotonic():
    raw = np.array([-3.0, 1.0, 1.0, 8.0])
    scores = MODULE.percentile_scores(raw)

    assert np.all(scores >= 0)
    assert np.all(scores <= 100)
    assert scores[0] < scores[1] == scores[2] < scores[3]


def test_normalized_weight_table_sums_to_100_and_preserves_forced_zero():
    catalog = MODULE.subsystem_catalog()
    coefficients = np.arange(1, len(catalog) + 1, dtype=float)
    rows = MODULE.build_weight_table(catalog, coefficients)

    assert round(sum(row["weight"] for row in rows), 8) == 100.0
    for row in rows:
        if row["forced_zero_reason"]:
            assert row["weight"] == 0
            assert row["coefficient"] == 0


def test_zero_coefficients_are_rejected_instead_of_becoming_fake_equal_weights():
    catalog = MODULE.subsystem_catalog()

    with pytest.raises(ValueError, match="优化器没有产生有效非零系数"):
        MODULE.build_weight_table(catalog, np.zeros(len(catalog)))


def test_global_rebalance_dates_require_broad_cross_section():
    frame = MODULE.pd.DataFrame(
        {
            "date": ["20240101"] * 250
            + ["20240102"] * 2
            + ["20240103"] * 260
            + ["20240104"] * 255,
            "symbol": [f"S{i:03d}" for i in range(250)]
            + ["S000", "S001"]
            + [f"S{i:03d}" for i in range(260)]
            + [f"S{i:03d}" for i in range(255)],
        }
    )

    dates = MODULE.global_rebalance_dates(
        frame, stock_count=300, rebalance_days=2, minimum_fraction=0.7
    )

    assert dates == ["20240101", "20240104"]


def test_entry_tradability_requires_exact_next_market_session():
    records = [
        {
            "date": "20240102",
            "open": 10.0,
            "high": 10.2,
            "low": 9.9,
            "close": 10.0,
            "volume": 100000.0,
            "amount": 1000000.0,
        },
        {
            "date": "20240104",
            "open": 10.1,
            "high": 10.3,
            "low": 10.0,
            "close": 10.2,
            "volume": 100000.0,
            "amount": 1000000.0,
        },
    ]

    result = MODULE.assess_entry_tradability(
        "000001.SZ",
        records,
        signal_date="20240102",
        market_calendar=["20240102", "20240103", "20240104"],
        minimum_amount=100000.0,
    )

    assert result["tradable"] is False
    assert result["reason"] == "entry_session_bar_missing"


def test_entry_tradability_rejects_zero_liquidity_and_one_price_limit_up():
    base = {
        "date": "20240102",
        "open": 10.0,
        "high": 10.2,
        "low": 9.9,
        "close": 10.0,
        "volume": 100000.0,
        "amount": 1000000.0,
    }
    zero_liquidity = [
        base,
        {
            "date": "20240103",
            "open": 10.0,
            "high": 10.0,
            "low": 10.0,
            "close": 10.0,
            "volume": 0.0,
            "amount": 0.0,
        },
    ]
    one_price_limit = [
        base,
        {
            "date": "20240103",
            "open": 11.0,
            "high": 11.0,
            "low": 11.0,
            "close": 11.0,
            "volume": 100000.0,
            "amount": 1100000.0,
        },
    ]

    illiquid = MODULE.assess_entry_tradability(
        "000001.SZ",
        zero_liquidity,
        signal_date="20240102",
        market_calendar=["20240102", "20240103"],
        minimum_amount=100000.0,
    )
    locked = MODULE.assess_entry_tradability(
        "000001.SZ",
        one_price_limit,
        signal_date="20240102",
        market_calendar=["20240102", "20240103"],
        minimum_amount=100000.0,
    )

    assert illiquid["reason"] == "entry_session_insufficient_liquidity"
    assert locked["reason"] == "entry_session_one_price_limit_up"


def test_temporal_validation_robustness_rejects_full_period_win_from_one_segment():
    rows = []
    candidate = []
    benchmark = []
    for date_index in range(12):
        date = f"202401{date_index + 1:02d}"
        for symbol_index in range(20):
            target = float(symbol_index)
            rows.append(
                {
                    "date": date,
                    "symbol": f"S{symbol_index:03d}",
                    "target": target,
                    "return_3d": target / 1000.0,
                    "return_5d": target / 800.0,
                    "return_10d": target / 600.0,
                }
            )
            benchmark.append(float(symbol_index))
            candidate.append(
                float(symbol_index) if date_index >= 4 else float(-symbol_index)
            )
    frame = MODULE.pd.DataFrame(rows)

    result = MODULE.temporal_validation_robustness(
        frame,
        np.asarray(candidate, dtype=float),
        np.asarray(benchmark, dtype=float),
        segments=3,
    )

    assert result["status"] == "REJECTED"
    assert result["segment_count"] == 3
    assert result["segments"][0]["candidate_mean_ic"] < 0
    assert result["segments"][1]["candidate_mean_ic"] > 0


def test_evaluation_cross_section_uses_full_universe_not_selected_decile():
    symbols = [f"S{i:03d}" for i in range(20)]
    frame = MODULE.pd.DataFrame(
        {
            "date": ["20240105"] * 20,
            "symbol": symbols,
            "target": np.linspace(-1.0, 1.0, 20),
            "return_3d": np.linspace(-0.02, 0.03, 20),
            "return_5d": np.linspace(-0.03, 0.05, 20),
            "return_10d": np.linspace(-0.04, 0.08, 20),
        }
    )

    metrics = MODULE.evaluate_predictions(frame, np.arange(20, dtype=float))

    assert metrics["median_cross_section"] == 20
    assert metrics["minimum_cross_section"] == 20
    assert metrics["date_metrics"][0]["universe_count"] == 20
    assert metrics["date_metrics"][0]["selected_count"] == 5


def test_hierarchical_scoring_returns_three_system_scores_and_fusion_total():
    catalog = MODULE.subsystem_catalog()
    feature_keys = [row["key"] for row in catalog]
    frame = MODULE.pd.DataFrame(
        [
            {"date": "20260812", "symbol": "000001.SZ", **dict.fromkeys(feature_keys, 1.0)},
            {"date": "20260812", "symbol": "600000.SH", **dict.fromkeys(feature_keys, 2.0)},
        ]
    )
    model = MODULE.build_hierarchical_model(
        catalog,
        {
            formula: np.array(
                [
                    1.0 if row["formula"] == formula and not row["forced_zero_reason"] else 0.0
                    for row in catalog
                ]
            )
            for formula in MODULE.FORMULAS
        },
        {
            "大牛线撑压版": 40.0,
            "飞龙在天": 35.0,
            "庄家资金监控": 25.0,
        },
        resonance_bonus=0.15,
        disagreement_penalty=0.10,
    )

    scored = MODULE.score_feature_frame(frame, model)

    assert list(scored["symbol"]) == ["600000.SH", "000001.SZ"]
    assert all(0 <= row["score"] <= 100 for _, row in scored.iterrows())
    assert all(len(row["contributions"]) == 30 for _, row in scored.iterrows())
    assert all(
        set(row["formula_scores"]) == set(MODULE.FORMULAS)
        for _, row in scored.iterrows()
    )
    assert all(
        row["score"] == pytest.approx(
            min(
                100.0,
                max(
                    0.0,
                    row["fusion"]["base_score"]
                    + row["fusion"]["resonance_bonus"]
                    - row["fusion"]["disagreement_penalty"],
                ),
            )
        )
        for _, row in scored.iterrows()
    )
    assert model["model_type"] == "hierarchical_three_system_resonance"
    assert sum(model["system_weights"].values()) == pytest.approx(100.0)
    for formula in MODULE.FORMULAS:
        local = [
            row["local_weight"]
            for row in model["subsystem_weights"]
            if row["formula"] == formula
        ]
        assert sum(local) == pytest.approx(100.0)


def test_hierarchical_fusion_rewards_consensus_and_penalizes_disagreement():
    system_weights = {
        "大牛线撑压版": 40.0,
        "飞龙在天": 35.0,
        "庄家资金监控": 25.0,
    }

    consensus = MODULE.fuse_system_scores(
        {
            "大牛线撑压版": 80.0,
            "飞龙在天": 80.0,
            "庄家资金监控": 80.0,
        },
        system_weights,
        resonance_bonus=0.15,
        disagreement_penalty=0.10,
    )
    disagreement = MODULE.fuse_system_scores(
        {
            "大牛线撑压版": 100.0,
            "飞龙在天": 80.0,
            "庄家资金监控": 48.0,
        },
        system_weights,
        resonance_bonus=0.15,
        disagreement_penalty=0.10,
    )

    assert consensus["base_score"] == pytest.approx(disagreement["base_score"])
    assert consensus["total_score"] > disagreement["total_score"]
    assert consensus["resonance_bonus"] > disagreement["resonance_bonus"]
    assert consensus["disagreement_penalty"] < disagreement["disagreement_penalty"]


def test_negative_local_direction_uses_inverse_percentile_before_system_score():
    catalog = MODULE.subsystem_catalog()
    feature_keys = [row["key"] for row in catalog]
    coefficients = {}
    for formula in MODULE.FORMULAS:
        values = np.zeros(len(catalog), dtype=float)
        active = [
            index
            for index, row in enumerate(catalog)
            if row["formula"] == formula and not row["forced_zero_reason"]
        ]
        values[active[0]] = -1.0 if formula == "飞龙在天" else 1.0
        coefficients[formula] = values
    model = MODULE.build_hierarchical_model(
        catalog,
        coefficients,
        dict.fromkeys(MODULE.FORMULAS, 1.0),
        resonance_bonus=0.06,
        disagreement_penalty=0.05,
    )
    frame = MODULE.pd.DataFrame(
        [
            {"date": "20260812", "symbol": "LOW.SZ", **dict.fromkeys(feature_keys, 1.0)},
            {"date": "20260812", "symbol": "HIGH.SH", **dict.fromkeys(feature_keys, 2.0)},
        ]
    )

    scored = MODULE.score_feature_frame(frame, model).set_index("symbol")

    assert model["subsystem_weights"][16]["direction"] == -1
    assert (
        scored.loc["LOW.SZ", "formula_scores"]["飞龙在天"]
        > scored.loc["HIGH.SH", "formula_scores"]["飞龙在天"]
    )


def test_backtest_system_score_uses_same_inverse_percentile_rule():
    features = np.array(
        [
            [0.10, 0.20],
            [0.90, 0.80],
        ]
    )
    coefficients = np.array([-0.75, 0.25])

    scores = MODULE.directed_system_score(features, coefficients)

    assert scores[0] > scores[1]
    assert scores[0] == pytest.approx(0.725)
    assert scores[1] == pytest.approx(0.275)


def test_newey_west_statistics_distinguish_stable_edge_from_noise():
    stable = MODULE.newey_west_mean_statistics([0.02] * 40)
    noisy = MODULE.newey_west_mean_statistics(
        [0.02 if index % 2 == 0 else -0.02 for index in range(40)]
    )

    assert stable["mean"] == pytest.approx(0.02)
    assert stable["ci95_lower"] > 0
    assert noisy["ci95_lower"] <= 0 <= noisy["ci95_upper"]


def test_market_data_parser_builds_front_adjusted_bar_records():
    index = MODULE.pd.to_datetime(["2026-08-14", "2026-08-17"])
    market_data = {
        "Open": MODULE.pd.DataFrame({"600519.SH": [1355.0, 1295.0]}, index=index),
        "High": MODULE.pd.DataFrame({"600519.SH": [1359.0, 1301.0]}, index=index),
        "Low": MODULE.pd.DataFrame({"600519.SH": [1338.14, 1280.34]}, index=index),
        "Close": MODULE.pd.DataFrame({"600519.SH": [1341.99, 1284.97]}, index=index),
        "Volume": MODULE.pd.DataFrame({"600519.SH": [2985315.0, 5392526.0]}, index=index),
        "Amount": MODULE.pd.DataFrame({"600519.SH": [402406.56, 695734.69]}, index=index),
    }

    bars = MODULE.market_data_to_bars(market_data, ["600519.SH"])

    assert [row["date"] for row in bars["600519.SH"]] == ["20260814", "20260817"]
    assert bars["600519.SH"][0]["open"] == pytest.approx(1355.0)
    assert bars["600519.SH"][1]["close"] == pytest.approx(1284.97)
    assert bars["600519.SH"][0]["amount"] == pytest.approx(4_024_065_600.0)


def test_formula_history_retries_missing_batch_nodes_one_symbol_at_a_time():
    class FakeTq:
        def __init__(self):
            self.calls = []

        def formula_process_mul_zb(self, formula, **kwargs):
            symbols = kwargs["stock_list"]
            self.calls.append(list(symbols))
            node = {
                "主趋势线": [
                    {"Date": "20260817", "Value": "1.25"},
                ]
            }
            if len(symbols) > 1:
                return {"ErrorId": "19", symbols[1]: node}
            return {"ErrorId": "0", symbols[0]: node}

    tq = FakeTq()
    maps, errors = MODULE.fetch_formula_history(
        tq,
        MODULE.BIG_BULL_FORMULA,
        ["000001.SZ", "000002.SZ"],
        ("主趋势线",),
        count=1300,
        dividend_type=1,
        batch_size=2,
    )

    assert errors == []
    assert tq.calls == [["000001.SZ", "000002.SZ"], ["000001.SZ"]]
    assert maps["000001.SZ"]["20260817"]["主趋势线"] == pytest.approx(1.25)
    assert maps["000002.SZ"]["20260817"]["主趋势线"] == pytest.approx(1.25)


def test_adjusted_history_retries_truncated_batch_symbol_individually():
    class FakeTq:
        def __init__(self):
            self.calls = []

        def get_market_data(self, **kwargs):
            symbols = kwargs["stock_list"]
            self.calls.append(list(symbols))
            index = MODULE.pd.to_datetime(["2026-08-14", "2026-08-17"])
            data = {}
            for field in ("Open", "High", "Low", "Close", "Volume", "Amount"):
                columns = {}
                for symbol in symbols:
                    values = [1.0, 2.0]
                    if len(symbols) > 1 and symbol == "000001.SZ":
                        values = [np.nan, 2.0]
                    columns[symbol] = values
                data[field] = MODULE.pd.DataFrame(columns, index=index)
            return data

    tq = FakeTq()
    bars, errors = MODULE.fetch_adjusted_market_history(
        tq,
        ["000001.SZ", "000002.SZ"],
        count=2,
        batch_size=2,
    )

    assert errors == []
    assert tq.calls == [["000001.SZ", "000002.SZ"], ["000001.SZ"]]
    assert len(bars["000001.SZ"]) == 2
    assert len(bars["000002.SZ"]) == 2


def test_structural_fallback_is_a_formal_three_system_model():
    catalog = MODULE.subsystem_catalog()
    diagnostics = {
        row["key"]: {
            "coverage": 1.0,
            "informative_dates": 80 if row["formula"] != "庄家资金监控" else 70,
            "total_dates": 100,
        }
        for row in catalog
    }

    model = MODULE.build_structural_fallback_model(
        catalog,
        diagnostics,
        reason="预测优势未建立",
    )

    MODULE.validate_hierarchical_model(model)
    assert model["metadata"]["model_origin"] == "audited_structural_fallback"
    assert set(model["system_weights"]) == set(MODULE.FORMULAS)
    assert sum(model["system_weights"].values()) == pytest.approx(100.0)
    assert model["fusion"]["resonance_bonus"] > 0
    assert model["fusion"]["disagreement_penalty"] > 0


def test_fixed_research_model_uses_declared_non_predictive_weights():
    payload, model = MODULE.build_fixed_research_model_payload()

    MODULE.validate_hierarchical_model(model)
    assert payload["status"] == "RESEARCH_ONLY"
    assert payload["predictive_validation"]["status"] == "NOT_APPLICABLE"
    assert model["metadata"]["model_origin"] == "fixed_research_structural"
    assert model["system_weights"] == {
        MODULE.BIG_BULL_FORMULA: 40.0,
        MODULE.FEILONG_FORMULA: 35.0,
        MODULE.DEALER_FORMULA: 25.0,
    }


def test_percentile_scores_use_midrank_and_constant_values_are_neutral():
    assert MODULE.percentile_scores(np.array([1.0, 1.0, 1.0])).tolist() == pytest.approx(
        [50.0, 50.0, 50.0]
    )
    assert MODULE.percentile_scores(np.array([1.0, 2.0, 3.0])).tolist() == pytest.approx(
        [100.0 / 6.0, 50.0, 500.0 / 6.0]
    )


def test_research_model_keeps_cross_sectionally_constant_real_items_active():
    catalog = MODULE.subsystem_catalog()
    symbols = ["000001.SZ", "000002.SZ", "600000.SH", "600001.SH"]
    rows = []
    for position, symbol in enumerate(symbols, start=1):
        values = {
            row["key"]: float(position + index)
            for index, row in enumerate(catalog)
        }
        values["fl_dragon"] = 1.0
        rows.append({"date": "20260818", "symbol": symbol, **values})
    frame = MODULE.pd.DataFrame(rows)

    payload, model = MODULE.build_research_model_for_frame(frame, symbols)

    weights = {row["key"]: row for row in model["subsystem_weights"]}
    assert payload["status"] == "RESEARCH_ONLY"
    assert weights["fl_dragon"]["local_weight"] == 10.0
    assert weights["fl_dragon"]["forced_zero_reason"] == ""
    assert model["metadata"]["research_information_diagnostics"]["fl_dragon"][
        "neutral_observation"
    ] is True
    for formula in MODULE.FORMULAS:
        assert sum(
            row["local_weight"]
            for row in model["subsystem_weights"]
            if row["formula"] == formula
        ) == pytest.approx(100.0)


def test_system_reliability_shrinks_sparse_system_score_toward_neutral():
    catalog = MODULE.subsystem_catalog()
    coefficients = {}
    for formula in MODULE.FORMULAS:
        values = np.zeros(len(catalog), dtype=float)
        active = [
            index
            for index, row in enumerate(catalog)
            if row["formula"] == formula and not row["forced_zero_reason"]
        ]
        values[active] = 1.0
        coefficients[formula] = values
    model = MODULE.build_hierarchical_model(
        catalog,
        coefficients,
        dict(zip(MODULE.FORMULAS, (40.0, 35.0, 25.0), strict=True)),
        resonance_bonus=0.08,
        disagreement_penalty=0.08,
        metadata={
            "system_reliability": {
                MODULE.BIG_BULL_FORMULA: 1.0,
                MODULE.FEILONG_FORMULA: 1.0,
                MODULE.DEALER_FORMULA: 0.25,
            }
        },
    )
    keys = [row["key"] for row in catalog]
    frame = MODULE.pd.DataFrame(
        [
            {"date": "20260818", "symbol": "LOW.SZ", **dict.fromkeys(keys, 1.0)},
            {"date": "20260818", "symbol": "HIGH.SH", **dict.fromkeys(keys, 2.0)},
        ]
    )

    high = MODULE.score_feature_frame(frame, model).set_index("symbol").loc["HIGH.SH"]

    assert high["formula_scores"][MODULE.DEALER_FORMULA] == pytest.approx(56.25)
    dealer_item = next(
        row
        for row in high["contributions"]
        if row["key"] == "zj_control_degree"
    )
    assert dealer_item["system_reliability"] == pytest.approx(0.25)
    assert dealer_item["effective_percentile"] == pytest.approx(56.25)


def test_research_model_keeps_real_constant_system_as_neutral_observation():
    catalog = MODULE.subsystem_catalog()
    symbols = ["000001.SZ", "000002.SZ", "600000.SH", "600001.SH"]
    rows = []
    for position, symbol in enumerate(symbols, start=1):
        values = {
            row["key"]: (
                1.0
                if row["formula"] == MODULE.DEALER_FORMULA
                else float(position + index)
            )
            for index, row in enumerate(catalog)
        }
        rows.append({"date": "20260818", "symbol": symbol, **values})
    frame = MODULE.pd.DataFrame(rows)

    _, model = MODULE.build_research_model_for_frame(frame, symbols)
    scored = MODULE.score_feature_frame(
        frame,
        model,
        reference_symbols=symbols,
    )

    assert model["metadata"]["system_reliability"][MODULE.DEALER_FORMULA] == 1.0
    assert model["metadata"]["neutralized_systems"] == []
    assert sum(
        row["local_weight"]
        for row in model["subsystem_weights"]
        if row["formula"] == MODULE.DEALER_FORMULA
    ) == 100.0
    for _, score_row in scored.iterrows():
        assert score_row["formula_scores"][MODULE.DEALER_FORMULA] == 50.0
        dealer_rows = [
            row
            for row in score_row["contributions"]
            if row["formula"] == MODULE.DEALER_FORMULA
        ]
        assert {row["system_reliability"] for row in dealer_rows} == {1.0}
        assert {row["effective_percentile"] for row in dealer_rows} == {50.0}
        assert {row["local_weight"] for row in dealer_rows} == {25.0}


def test_current_scoring_accepts_board_stock_shorter_than_requested_window():
    symbols = ["603285.SH", "600000.SH"]
    bars = {
        "603285.SH": [{}] * 514,
        "600000.SH": [{}] * 259,
    }

    assert MODULE.eligible_current_symbols(symbols, bars) == ["603285.SH"]


def test_write_csv_keeps_fields_introduced_by_later_subsystem_rows(tmp_path):
    path = tmp_path / "contributions.csv"
    MODULE.write_csv(
        path,
        [
            {"number": 1, "score": 70.0},
            {"number": 2, "score": 80.0, "status": "VERIFIED"},
        ],
    )

    header = path.read_text(encoding="utf-8-sig").splitlines()[0]
    assert header == "number,score,status"


def test_failed_validation_selection_still_returns_best_candidate_for_one_oos_audit():
    candidates = [
        {
            "objective": 0.01,
            "metrics": {
                "mean_ic": -0.01,
                "top_decile": {
                    "5d": {"excess_return": -0.001},
                    "10d": {"excess_return": 0.001},
                },
            },
        },
        {
            "objective": 0.02,
            "metrics": {
                "mean_ic": 0.01,
                "top_decile": {
                    "5d": {"excess_return": 0.001},
                    "10d": {"excess_return": -0.001},
                },
            },
        },
    ]

    selected, evidence = MODULE.select_fusion_candidate(
        candidates,
        equal_weight_objective=0.03,
    )

    assert selected is candidates[1]
    assert evidence["status"] == "VALIDATION_REJECTED"
    assert evidence["eligible_candidate_count"] == 0
    assert evidence["candidate_count"] == 2


def test_validation_selection_requires_each_temporal_segment_to_pass():
    unstable = {
        "objective": 0.08,
        "metrics": {
            "mean_ic": 0.03,
            "top_decile": {
                "5d": {"excess_return": 0.01},
                "10d": {"excess_return": 0.01},
            },
        },
        "temporal_robustness": {"status": "REJECTED"},
    }
    stable = {
        "objective": 0.06,
        "metrics": {
            "mean_ic": 0.02,
            "top_decile": {
                "5d": {"excess_return": 0.008},
                "10d": {"excess_return": 0.008},
            },
        },
        "temporal_robustness": {"status": "PASS"},
    }

    selected, evidence = MODULE.select_fusion_candidate(
        [unstable, stable],
        equal_weight_objective=0.04,
    )

    assert selected is stable
    assert evidence["status"] == "VALIDATION_PASS"
    assert evidence["eligible_candidate_count"] == 1


def test_board_symbols_are_fetched_without_changing_reference_universe():
    reference_symbols = MODULE.merge_scoring_universe(
        ["600000.SH", "000001.SZ", "000002.SZ"],
        ["000002.SZ", "603890.SH", "002066.SZ"],
        max_stocks=2,
    )

    assert reference_symbols == ["000001.SZ", "000002.SZ"]
    assert MODULE.merge_fetch_symbols(
        reference_symbols,
        ["000002.SZ", "603890.SH", "002066.SZ"],
    ) == ["000001.SZ", "000002.SZ", "002066.SZ", "603890.SH"]


def test_latest_broad_feature_frame_uses_latest_well_covered_date():
    frame = MODULE.pd.DataFrame(
        {
            "date": ["20260811"] * 10 + ["20260812"] * 8 + ["20260813"] * 2,
            "symbol": [f"S{i:02d}" for i in range(10)]
            + [f"S{i:02d}" for i in range(8)]
            + ["S00", "S01"],
        }
    )

    selected, score_date = MODULE.latest_broad_feature_frame(
        frame,
        stock_count=10,
        minimum_fraction=0.7,
    )

    assert score_date == "20260812"
    assert len(selected) == 8
    assert set(selected["date"]) == {"20260812"}


def test_current_scoring_date_gate_blocks_previous_day_on_shanghai_weekday():
    now = datetime(2026, 8, 13, 17, 30, tzinfo=ZoneInfo("Asia/Shanghai"))

    with pytest.raises(MODULE.ScoringDateBlocked) as caught:
        MODULE.enforce_current_scoring_date("20260812", now=now)

    assert caught.value.evidence == {
        "status": "BLOCKED",
        "timezone": "Asia/Shanghai",
        "beijing_date": "20260813",
        "beijing_weekday": 3,
        "score_date": "20260812",
        "required_score_date": "20260813",
        "rule": "SHANGHAI_WEEKDAY_SCORE_DATE_MUST_EQUAL_TODAY",
        "reason": "本机行情未更新到北京时间当天，禁止生成或交付评分榜单",
    }
    assert "当前日期20260813" in str(caught.value)
    assert "实际评分日20260812" in str(caught.value)


def test_current_scoring_date_gate_passes_same_shanghai_date():
    now = datetime(2026, 8, 13, 17, 30, tzinfo=ZoneInfo("Asia/Shanghai"))

    evidence = MODULE.enforce_current_scoring_date("20260813", now=now)

    assert evidence == {
        "status": "PASS",
        "timezone": "Asia/Shanghai",
        "beijing_date": "20260813",
        "beijing_weekday": 3,
        "score_date": "20260813",
        "required_score_date": "20260813",
        "rule": "SHANGHAI_WEEKDAY_SCORE_DATE_MUST_EQUAL_TODAY",
        "reason": "",
    }


def test_current_scoring_date_gate_allows_latest_complete_date_before_market_open():
    now = datetime(2026, 8, 18, 0, 32, tzinfo=ZoneInfo("Asia/Shanghai"))

    evidence = MODULE.enforce_current_scoring_date("20260817", now=now)

    assert evidence == {
        "status": "PASS",
        "timezone": "Asia/Shanghai",
        "beijing_date": "20260818",
        "beijing_weekday": 1,
        "score_date": "20260817",
        "required_score_date": "20260817",
        "rule": "SHANGHAI_PREOPEN_LATEST_COMPLETE_TRADING_DAY",
        "reason": "开盘前使用本机最近完整交易日",
    }


def test_current_scoring_date_gate_allows_last_session_on_weekend():
    now = datetime(2026, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    evidence = MODULE.enforce_current_scoring_date("20260814", now=now)

    assert evidence["status"] == "PASS"
    assert evidence["beijing_date"] == "20260815"
    assert evidence["beijing_weekday"] == 5
    assert evidence["score_date"] == "20260814"


def test_current_scoring_blocks_stale_data_before_writing_and_removes_old_artifacts(
    monkeypatch,
    tmp_path,
):
    symbols = [f"{index:06d}.SZ" for index in range(1, 251)]
    for name in MODULE.CURRENT_SCORE_ARTIFACTS:
        (tmp_path / name).write_text("stale", encoding="utf-8")

    class FakeTq:
        def get_stock_list(self, market):
            assert market == "23"
            return symbols

        def close(self):
            return None

    day_files = {}
    for symbol in symbols:
        path = tmp_path / f"{symbol}.day"
        path.write_bytes(b"day")
        day_files[symbol] = path

    formula_map = {
        symbol: {"20260812": {"value": 1.0}}
        for symbol in symbols
    }
    feature_frame = MODULE.pd.DataFrame(
        {
            "date": ["20260812"] * len(symbols),
            "symbol": symbols,
        }
    )
    monkeypatch.setattr(MODULE, "load_formal_weights", lambda path: ({}, {}))
    monkeypatch.setattr(MODULE, "load_board_symbols", lambda *args: (None, None))
    monkeypatch.setattr(MODULE, "initialize_tq", FakeTq)
    monkeypatch.setattr(MODULE, "day_path", lambda symbol: day_files[symbol])
    monkeypatch.setattr(MODULE, "read_day_file", lambda path: [{}] * 260)
    monkeypatch.setattr(
        MODULE,
        "fetch_formula_history",
        lambda *args, **kwargs: (formula_map, []),
    )
    monkeypatch.setattr(
        MODULE,
        "fetch_dealer_history_official",
        lambda *args, **kwargs: (formula_map, []),
    )
    monkeypatch.setattr(
        MODULE,
        "build_current_feature_frame",
        lambda *args, **kwargs: (feature_frame, []),
    )
    monkeypatch.setattr(
        MODULE,
        "shanghai_now",
        lambda now=None: datetime(
            2026,
            8,
            13,
            17,
            30,
            tzinfo=ZoneInfo("Asia/Shanghai"),
        ),
    )
    args = Namespace(
        output_dir=str(tmp_path),
        weights_file=str(tmp_path / "weights.json"),
        board_code="",
        board_file="",
        board_name="",
        max_stocks=250,
        count=220,
        batch_size=2,
    )

    with pytest.raises(MODULE.ScoringDateBlocked):
        MODULE.run_current_scoring(args)

    assert all(
        not (tmp_path / name).exists()
        for name in MODULE.CURRENT_SCORE_ARTIFACTS
    )


def test_research_scoring_builds_model_from_unified_reference_frame(
    monkeypatch,
    tmp_path,
):
    symbols = [f"{index:06d}.SZ" for index in range(1, 251)]

    class FakeTq:
        def get_stock_list(self, market):
            assert market == "23"
            return symbols

        def close(self):
            return None

    day_files = {}
    for symbol in symbols:
        path = tmp_path / f"{symbol}.day"
        path.write_bytes(b"day")
        day_files[symbol] = path
    formula_map = {
        symbol: {"20260818": {"value": 1.0}}
        for symbol in symbols
    }
    feature_frame = MODULE.pd.DataFrame(
        {"date": ["20260818"] * len(symbols), "symbol": symbols}
    )

    class ResearchModelBuilt(RuntimeError):
        pass

    def build_model(frame, reference_symbols):
        assert len(frame) == 250
        assert reference_symbols == symbols
        raise ResearchModelBuilt

    monkeypatch.setattr(MODULE, "load_tdx_stock_names", lambda: {})
    monkeypatch.setattr(MODULE, "load_board_symbols", lambda *args: (None, None))
    monkeypatch.setattr(MODULE, "initialize_tq", FakeTq)
    monkeypatch.setattr(MODULE, "day_path", lambda symbol: day_files[symbol])
    monkeypatch.setattr(MODULE, "read_day_file", lambda path: [{}] * 260)
    monkeypatch.setattr(
        MODULE, "fetch_formula_history", lambda *args, **kwargs: (formula_map, [])
    )
    monkeypatch.setattr(
        MODULE, "fetch_dealer_history_official", lambda *args, **kwargs: (formula_map, [])
    )
    monkeypatch.setattr(
        MODULE,
        "build_current_feature_frame",
        lambda *args, **kwargs: (feature_frame, []),
    )
    monkeypatch.setattr(MODULE, "build_research_model_for_frame", build_model)
    monkeypatch.setattr(
        MODULE,
        "shanghai_now",
        lambda now=None: datetime(
            2026, 8, 18, 17, 30, tzinfo=ZoneInfo("Asia/Shanghai")
        ),
    )
    args = Namespace(
        output_dir=str(tmp_path),
        weights_file=str(tmp_path / "weights.json"),
        board_code="",
        board_file="",
        board_name="",
        max_stocks=250,
        count=220,
        batch_size=2,
        research_structural=True,
    )

    with pytest.raises(ResearchModelBuilt):
        MODULE.run_current_scoring(args)


def _complete_current_score_payload():
    contributions = []
    for row in MODULE.subsystem_catalog():
        item_count = {
            MODULE.BIG_BULL_FORMULA: 16,
            MODULE.FEILONG_FORMULA: 10,
            MODULE.DEALER_FORMULA: 4,
        }[row["formula"]]
        local_weight = 100.0 / item_count
        contributions.append(
            {
                "formula": row["formula"],
                "number": row["number"],
                "key": row["key"],
                "name": row["name"],
                "raw_value": 1.25,
                "percentile": 66.0,
                "effective_percentile": 66.0,
                "system_reliability": 1.0,
                "direction": 1,
                "local_weight": local_weight,
                "local_contribution": 66.0 * local_weight / 100.0,
                "system_weight": 33.33333333,
                "base_contribution": 1.1,
                "forced_zero_reason": row["forced_zero_reason"],
            }
        )
    formula_scores = {
        MODULE.BIG_BULL_FORMULA: 85.9715,
        MODULE.FEILONG_FORMULA: 49.7250,
        MODULE.DEALER_FORMULA: 96.6887,
    }
    original_weights = {
        MODULE.BIG_BULL_FORMULA: 39.0,
        MODULE.FEILONG_FORMULA: 35.0,
        MODULE.DEALER_FORMULA: 26.0,
    }
    fusion = MODULE.fuse_system_scores(
        formula_scores,
        original_weights,
        resonance_bonus=0.06,
        disagreement_penalty=0.08,
    )
    fusion["top_level_scores"] = dict(formula_scores)
    fusion["top_level_weights"] = dict(original_weights)
    fusion["top_level_item_count"] = 3
    payload = {
        "status": "CLEAN_PASS",
        "scoring_mode": "RESEARCH_STRUCTURAL",
        "research_only": True,
        "prediction_authorized": False,
        "directional_forecast_authorized": True,
        "score_is_probability": False,
        "forecast_mode": "RULE_BASED_STRUCTURAL_FORECAST",
        "forecast_horizon": "未来5至10个交易日",
        "forecast_is_probability": False,
        "score_interpretation": "固定参考母体横截面结构分位，不是上涨概率",
        "generated_at": "2026-08-13T18:00:00+08:00",
        "score_date": "20260813",
        "stock_count": 1,
        "date_gate": {
            "status": "PASS",
            "timezone": "Asia/Shanghai",
            "beijing_date": "20260813",
        },
        "board": {
            "name": "黄金点火",
            "code": "HJDH",
            "constituent_count": 1,
        },
        "model_file": {
            "path": "weights.json",
            "sha256": "a" * 64,
            "source_backtest_sha256": "b" * 64,
        },
        "model": {
            "system_weights": original_weights,
            "metadata": {
                "predictive_validation": "NOT_ESTABLISHED",
            },
        },
        "data": {
            "stock_name_source": "C:\\new_tdx_mock\\T0002\\hq_cache\\infoharbor_ex.code",
        },
        "ranking": [
            {
                "rank": 1,
                "market_rank": 16,
                "market_percentile": 94.83333333,
                "date": "20260813",
                "symbol": "603118.SH",
                "name": "共进股份",
                "score": fusion["total_score"],
                "formula_scores": formula_scores,
                "top_level_items": formula_scores,
                "fusion": fusion,
                "conclusion": "未来5至10个交易日结构偏强；固定母体前10%；最强体系为庄家资金监控，最弱体系为飞龙在天；三体系分歧继续扩大则预测失效。",
                "contributions": contributions,
            }
        ],
    }
    payload["scoring_identity"] = MODULE.build_scoring_identity(
        [f"{index:06d}.SZ" for index in range(1, 301)],
        payload["score_date"],
        payload["model"],
    )
    return payload


def test_current_score_conclusion_uses_market_percentile_not_absolute_score():
    row = {
        "score": 90.0,
        "market_percentile": 20.0,
        "formula_scores": {
            MODULE.BIG_BULL_FORMULA: 80.0,
            MODULE.FEILONG_FORMULA: 70.0,
            MODULE.DEALER_FORMULA: 60.0,
        },
    }

    conclusion = MODULE.current_score_conclusion(row)

    assert conclusion.startswith("未来5至10个交易日结构偏弱")
    assert "固定母体后30%" in conclusion
    assert "预测失效" in conclusion
    assert "综合强势" not in conclusion


def test_rank_percentile_uses_fixed_reference_universe_midpoint():
    assert MODULE.market_percentile_from_rank(1, 300) == pytest.approx(99.83333333)
    assert MODULE.market_percentile_from_rank(300, 300) == pytest.approx(0.16666667)


def test_current_score_report_exposes_all_user_visible_scoring_evidence():
    payload = _complete_current_score_payload()

    evidence = MODULE.validate_current_score_delivery(payload)
    report = MODULE.render_current_score_report(payload)

    assert evidence["status"] == "PASS"
    assert evidence["stock_count"] == 1
    assert evidence["contribution_row_count"] == 30
    for label in (
        "股票名称",
        "全市场排名",
        "全市场分位",
        "三体系加权基础分",
        "三体系共振加分",
        "三体系分歧扣分",
        "大牛线撑压版",
        "飞龙在天",
        "庄家资金监控",
        "综合结论",
        "固定30项完整明细",
        "原始值",
        "横截面百分位",
        "可靠性调整后百分位",
        "体系信息可靠性",
        "体系内权重",
        "逐项基础贡献",
        "零权重/审计原因",
        "报告完整性：PASS",
        "不是上涨概率",
    ):
        assert label in report
    assert "共进股份" in report
    assert "603118.SH" in report
    detail = report.split("### 1. 共进股份（603118.SH）", 1)[1]
    assert detail.count("| 大牛线撑压版 |") == 16
    assert detail.count("| 飞龙在天 |") == 10
    assert detail.count("| 庄家资金监控 |") == 4
    table_rows = [line for line in detail.splitlines() if line.startswith("|")]
    assert table_rows
    assert {line.count("|") for line in table_rows} == {13}


def test_current_score_delivery_rejects_probability_claim():
    payload = _complete_current_score_payload()
    payload["score_is_probability"] = True

    with pytest.raises(ValueError, match="不得解释为上涨概率"):
        MODULE.validate_current_score_delivery(payload)


def test_current_score_delivery_rejects_missing_information_adjustment_fields():
    payload = _complete_current_score_payload()
    payload["ranking"][0]["contributions"][0].pop("effective_percentile")

    with pytest.raises(ValueError, match="可靠性调整后百分位缺失或无效"):
        MODULE.validate_current_score_delivery(payload)


def test_current_score_delivery_keeps_exactly_thirty_items():
    payload = _complete_current_score_payload()
    original_score = payload["ranking"][0]["score"]

    evidence = MODULE.validate_current_score_delivery(payload)

    assert payload["ranking"][0]["score"] == original_score
    assert len(payload["ranking"][0]["contributions"]) == 30
    assert set(payload["ranking"][0]["top_level_items"]) == set(MODULE.FORMULAS)


def test_current_score_delivery_rejects_missing_name_or_incomplete_30_items():
    payload = _complete_current_score_payload()
    payload["ranking"][0]["name"] = ""

    with pytest.raises(ValueError, match="股票名称缺失"):
        MODULE.validate_current_score_delivery(payload)

    payload = _complete_current_score_payload()
    payload["ranking"][0]["contributions"] = payload["ranking"][0][
        "contributions"
    ][:-1]

    with pytest.raises(ValueError, match="30项贡献不完整"):
        MODULE.validate_current_score_delivery(payload)


def test_load_tdx_stock_names_reads_local_infoharbor_index(tmp_path):
    index_path = tmp_path / "infoharbor_ex.code"
    index_path.write_bytes(
        "603118|共进股份|通信设备\r\n002066|瑞泰科技|建筑材料\r\n".encode(
            "gbk"
        )
    )

    names = MODULE.load_tdx_stock_names(index_path)

    assert names == {
        "603118": "共进股份",
        "002066": "瑞泰科技",
    }


def test_build_current_feature_frame_keeps_common_dates_and_all_30_features(
    monkeypatch,
):
    catalog = MODULE.subsystem_catalog()
    feature_keys = [row["key"] for row in catalog]
    dates = np.array([f"2026{i:04d}" for i in range(1, 231)])
    features = {
        key: np.arange(230, dtype=float) + index
        for index, key in enumerate(feature_keys)
    }
    market = {"date": dates}
    monkeypatch.setattr(
        MODULE,
        "formula_feature_arrays",
        lambda *args: (features, market),
    )
    common = {dates[-2]: {}, dates[-1]: {}}

    frame, errors = MODULE.build_current_feature_frame(
        ["000001.SZ"],
        {"000001.SZ": [{}] * 230},
        {"000001.SZ": common},
        {"000001.SZ": common},
        {"000001.SZ": common},
        count=2,
    )

    assert errors == []
    assert list(frame["date"]) == list(dates[-2:])
    assert list(frame["symbol"]) == ["000001.SZ", "000001.SZ"]
    assert set(feature_keys).issubset(frame.columns)


def test_load_formal_weights_rejects_backtest_hash_mismatch(tmp_path):
    backtest = tmp_path / "backtest.json"
    backtest.write_text('{"status":"CLEAN_PASS"}', encoding="utf-8")
    weights_path = tmp_path / "weights.json"
    catalog = MODULE.subsystem_catalog()
    model = MODULE.build_hierarchical_model(
        catalog,
        {
            formula: np.array(
                [
                    1.0 if row["formula"] == formula and not row["forced_zero_reason"] else 0.0
                    for row in catalog
                ]
            )
            for formula in MODULE.FORMULAS
        },
        dict.fromkeys(MODULE.FORMULAS, 1.0),
        resonance_bonus=0.06,
        disagreement_penalty=0.05,
    )
    weights_path.write_text(
        json.dumps(
                {
                    "status": "CLEAN_PASS",
                    "methodology_version": MODULE.METHODOLOGY_VERSION,
                    "predictive_validation": {"status": "PREDICTIVE_PASS"},
                    "source_backtest": str(backtest),
                "source_backtest_sha256": hashlib.sha256(b"different").hexdigest(),
                "model": model,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="回测证据哈希不匹配"):
        MODULE.load_formal_weights(weights_path)


def test_load_formal_weights_rejects_predictive_not_established(tmp_path):
    backtest = tmp_path / "backtest.json"
    backtest.write_text('{"status":"BLOCKED"}', encoding="utf-8")
    catalog = MODULE.subsystem_catalog()
    diagnostics = {
        row["key"]: {
            "coverage": 1.0,
            "informative_dates": 80,
            "total_dates": 100,
        }
        for row in catalog
    }
    model = MODULE.build_structural_fallback_model(
        catalog,
        diagnostics,
        reason="预测优势未建立",
    )
    weights_path = tmp_path / "weights.json"
    weights_path.write_text(
        json.dumps(
                {
                    "status": "CLEAN_PASS",
                    "methodology_version": MODULE.METHODOLOGY_VERSION,
                    "predictive_validation": {"status": "PREDICTIVE_PASS"},
                    "source_backtest": str(backtest),
                "source_backtest_sha256": hashlib.sha256(
                    backtest.read_bytes()
                ).hexdigest(),
                "predictive_validation": {"status": "NOT_ESTABLISHED"},
                "model": model,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="预测验证未通过"):
        MODULE.load_formal_weights(weights_path)


def test_validation_gates_require_nonempty_independent_oos_rows():
    catalog = MODULE.subsystem_catalog()
    model = MODULE.build_hierarchical_model(
        catalog,
        {
            formula: np.array(
                [
                    1.0
                    if row["formula"] == formula
                    and not row["forced_zero_reason"]
                    else 0.0
                    for row in catalog
                ]
            )
            for formula in MODULE.FORMULAS
        },
        dict.fromkeys(MODULE.FORMULAS, 1.0),
        resonance_bonus=0.06,
        disagreement_penalty=0.05,
        metadata={"predictive_validation": "PREDICTIVE_PASS"},
    )
    metrics = {
        "rebalance_dates": 20,
        "median_cross_section": 250,
        "mean_ic": 0.05,
        "top_decile": {
            "5d": {"excess_return": 0.02},
            "10d": {"excess_return": 0.03},
        },
        "selected_rows": [],
        "date_metrics": [],
    }
    equal_metrics = {
        "mean_ic": 0.01,
        "top_decile": {
            "5d": {"excess_return": 0.005},
            "10d": {"excess_return": 0.006},
        },
    }

    gates = MODULE.validation_gates(
        250,
        MODULE.pd.DataFrame(index=range(10000)),
        metrics,
        equal_metrics,
        model,
    )

    assert gates["status"] == "BLOCKED"
    assert "independent_oos_rows_nonempty" in gates["failed"]
    assert "independent_oos_dates_nonempty" in gates["failed"]
    assert "point_in_time_universe_available" in gates["failed"]
    assert "tradability_constraints_complete" in gates["failed"]


def test_dealer_history_uses_fixed_tq_call_chain_and_aligns_day_dates():
    class FakeTq:
        def __init__(self):
            self.calls = []

        def formula_set_data_info(self, symbol, count, dividend_type):
            self.calls.append(("set", symbol, count, dividend_type))
            return {"ErrorId": "0"}

        def formula_zb(self, formula, code, xsflag):
            self.calls.append(("zb", formula, code, xsflag))
            return {
                "ErrorId": "0",
                "Value": {
                    "OUTPUT3": ["1", "2", "3"],
                    "OUTPUT4": ["0", "0", "0"],
                    "控盘程度": ["1", "2", "3"],
                    "控盘度": ["100", "100", "100"],
                },
            }

    tq = FakeTq()
    bars = {
        "600522.SH": [
            {"date": "20260808"},
            {"date": "20260809"},
            {"date": "20260810"},
            {"date": "20260811"},
            {"date": "20260812"},
        ]
    }

    maps, errors = MODULE.fetch_dealer_history_official(
        tq,
        ["600522.SH"],
        bars,
        ("OUTPUT3", "OUTPUT4", "控盘程度", "控盘度"),
        count=3,
    )

    assert errors == []
    assert tq.calls == [
        ("set", "600522.SH", 3, 1),
        ("zb", "庄家资金监控", "600522", 2),
    ]
    assert maps["600522.SH"]["20260810"]["控盘程度"] == 1.0
    assert maps["600522.SH"]["20260812"]["控盘程度"] == 3.0


def test_noninformative_feature_is_forced_to_zero_before_optimization():
    catalog = MODULE.subsystem_catalog()
    keys = [row["key"] for row in catalog]
    rows = []
    for date in ("20260101", "20260102", "20260103", "20260104", "20260105"):
        for index in range(30):
            row = {"date": date, "symbol": f"S{index:03d}"}
            row.update({key: float(index) for key in keys})
            row["zj_control_degree"] = 0.5
            rows.append(row)
    frame = MODULE.pd.DataFrame(rows)

    audited, diagnostics = MODULE.apply_information_constraints(frame, catalog)
    control = next(row for row in audited if row["key"] == "zj_control_degree")

    assert "无横截面区分度" in control["forced_zero_reason"]
    assert diagnostics["zj_control_degree"]["informative_dates"] == 0


def test_formal_weights_require_current_methodology_version(tmp_path):
    backtest = tmp_path / "backtest.json"
    backtest.write_text('{"status":"CLEAN_PASS"}', encoding="utf-8")
    weights_path = tmp_path / "weights.json"
    catalog = MODULE.subsystem_catalog()
    model = MODULE.build_hierarchical_model(
        catalog,
        {
            formula: np.array(
                [
                    1.0 if row["formula"] == formula and not row["forced_zero_reason"] else 0.0
                    for row in catalog
                ]
            )
            for formula in MODULE.FORMULAS
        },
        dict.fromkeys(MODULE.FORMULAS, 1.0),
        resonance_bonus=0.06,
        disagreement_penalty=0.05,
    )
    weights_path.write_text(
        json.dumps(
            {
                "status": "CLEAN_PASS",
                "source_backtest": str(backtest),
                "source_backtest_sha256": hashlib.sha256(
                    backtest.read_bytes()
                ).hexdigest(),
                "model": model,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="方法版本"):
        MODULE.load_formal_weights(weights_path)


def test_blocked_weights_payload_records_reason_and_source_hash(tmp_path):
    evidence = tmp_path / "evidence.json"
    evidence.write_text('{"status":"BLOCKED"}', encoding="utf-8")

    payload = MODULE.build_blocked_weights_payload(
        evidence,
        generated_at="2026-08-12T20:00:00+08:00",
        reason="验证期没有科学优于等权基准的权重候选",
        optimization_evidence={"candidate_count": 80},
    )

    assert payload["status"] == "BLOCKED"
    assert payload["methodology_version"] == MODULE.METHODOLOGY_VERSION
    assert payload["source_backtest"] == str(evidence)
    assert payload["source_backtest_sha256"] == hashlib.sha256(
        evidence.read_bytes()
    ).hexdigest()
    assert payload["model"] is None


def test_formal_payload_never_exposes_rejected_predictive_model(tmp_path):
    evidence = tmp_path / "evidence.json"
    evidence.write_text('{"status":"PREDICTIVE_REJECTED"}', encoding="utf-8")
    model = {"model_type": "candidate_only"}

    payload = MODULE.build_formal_weights_payload(
        evidence,
        generated_at="2026-08-17T12:00:00+08:00",
        predictive_status="PREDICTIVE_REJECTED",
        model=model,
        validation_gates={"status": "BLOCKED", "failed": ["test_ic_ci_lower_positive"]},
        oos_row_count=100,
        oos_date_count=20,
    )

    assert payload["status"] == "PREDICTIVE_REJECTED"
    assert payload["predictive_validation"]["status"] == "PREDICTIVE_REJECTED"
    assert payload["model"] is None


def test_sync_formal_model_state_replaces_stale_pass_with_rejected_v5(tmp_path):
    evidence = tmp_path / "evidence.json"
    evidence.write_text(
        json.dumps(
            {
                "status": "PREDICTIVE_REJECTED",
                "methodology_version": MODULE.METHODOLOGY_VERSION,
                "predictive_validation": {"status": "PREDICTIVE_REJECTED"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    source = tmp_path / "source-state.json"
    source.write_text(
        json.dumps(
            {
                "schema": "THREE_FORMULA_COMPOSITE_MODEL_V1",
                "status": "PREDICTIVE_REJECTED",
                "methodology_version": MODULE.METHODOLOGY_VERSION,
                "source_backtest": str(evidence),
                "source_backtest_sha256": hashlib.sha256(
                    evidence.read_bytes()
                ).hexdigest(),
                "predictive_validation": {
                    "status": "PREDICTIVE_REJECTED",
                    "oos_row_count": 1352,
                    "oos_date_count": 52,
                    "failed_gates": ["validation_selection_passed"],
                },
                "model": None,
                "validation_gates": {
                    "status": "BLOCKED",
                    "failed": ["validation_selection_passed"],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    target = tmp_path / "formal-state.json"
    target.write_text(
        json.dumps(
            {
                "status": "CLEAN_PASS",
                "methodology_version": "THREE_FORMULA_COMPOSITE_V3_HIERARCHICAL_RESONANCE",
                "model": {"stale": True},
            }
        ),
        encoding="utf-8",
    )

    receipt = MODULE.sync_formal_model_state(source, target)
    installed = json.loads(target.read_text(encoding="utf-8"))

    assert installed["status"] == "PREDICTIVE_REJECTED"
    assert installed["methodology_version"] == MODULE.METHODOLOGY_VERSION
    assert installed["model"] is None
    assert receipt["model_usable"] is False
    assert receipt["target_sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()


def test_sync_rejects_predictive_rejection_that_retains_model(tmp_path):
    evidence = tmp_path / "evidence.json"
    evidence.write_text('{"status":"PREDICTIVE_REJECTED"}', encoding="utf-8")
    source = tmp_path / "source-state.json"
    source.write_text(
        json.dumps(
            {
                "schema": "THREE_FORMULA_COMPOSITE_MODEL_V1",
                "status": "PREDICTIVE_REJECTED",
                "methodology_version": MODULE.METHODOLOGY_VERSION,
                "source_backtest": str(evidence),
                "source_backtest_sha256": hashlib.sha256(
                    evidence.read_bytes()
                ).hexdigest(),
                "predictive_validation": {
                    "status": "PREDICTIVE_REJECTED",
                    "failed_gates": ["failed"],
                },
                "model": {"must_not": "survive"},
                "validation_gates": {"status": "BLOCKED", "failed": ["failed"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="预测拒绝状态不得携带模型"):
        MODULE.sync_formal_model_state(source, tmp_path / "formal-state.json")


def test_formal_predictive_pass_requires_nonempty_oos_evidence(tmp_path):
    evidence = tmp_path / "evidence.json"
    evidence.write_text('{"status":"PREDICTIVE_PASS"}', encoding="utf-8")

    with pytest.raises(ValueError, match="样本外证据为空"):
        MODULE.build_formal_weights_payload(
            evidence,
            generated_at="2026-08-17T12:00:00+08:00",
            predictive_status="PREDICTIVE_PASS",
            model={"model_type": "candidate"},
            validation_gates={"status": "PASS", "failed": []},
            oos_row_count=0,
            oos_date_count=0,
        )


def test_formal_model_rejects_legacy_flat_weight_payload(tmp_path):
    backtest = tmp_path / "backtest.json"
    backtest.write_text('{"status":"CLEAN_PASS"}', encoding="utf-8")
    weights_path = tmp_path / "weights.json"
    weights_path.write_text(
        json.dumps(
            {
                "status": "CLEAN_PASS",
                "methodology_version": MODULE.METHODOLOGY_VERSION,
                "predictive_validation": {"status": "PREDICTIVE_PASS"},
                "source_backtest": str(backtest),
                "source_backtest_sha256": hashlib.sha256(
                    backtest.read_bytes()
                ).hexdigest(),
                "weights": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="三体系分层融合模型"):
        MODULE.load_formal_weights(weights_path)
