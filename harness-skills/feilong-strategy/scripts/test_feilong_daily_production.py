from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import feilong_daily_yaogu_scoring as daily
import feilong_factor_correlation_research as factor_research
import feilong_yaogu_factor_library as yaogu


SCORER_PATH = Path(r"F:\Codex\projects\飞龙在天评分体系彻底优化_20260901-184258\apply_yaogu_scoring.py")


def load_scorer():
    spec = importlib.util.spec_from_file_location("production_scorer_test", SCORER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def minimal_config() -> dict:
    quantiles = [index / 100 for index in range(101)]
    dimensions = [f"dimension_{index:02d}" for index in range(1, 33)]
    factor = {
        "factor": "factor_a",
        "family": dimensions[0],
        "value_quantiles": quantiles,
        "reach2": {"coefficient": 1.0},
        "reach3": {"coefficient": 1.0},
    }
    return {
        "schema": "FEILONG_YAOGU_32D_SCORE_V2",
        "rankable_factor_count": 1,
        "dimensions": dimensions,
        "factors": [factor],
        "target_models": {
            target: {"intercept": 0.0, "probability_quantiles": quantiles}
            for target in ("reach2", "reach3")
        },
        "dimension_contribution_quantiles": {
            target: {dimension: quantiles for dimension in dimensions}
            for target in ("reach2", "reach3")
        },
        "target_blend": {"reach2": 0.6, "reach3": 0.4},
        "composite_pre_quantiles": quantiles,
        "grade_thresholds": {"E": 0.0, "D": 20.0, "C": 40.0, "B": 60.0, "A": 80.0, "S": 90.0},
    }


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_production_scorer_rejects_nonfinite(value: float) -> None:
    scorer = load_scorer()
    with pytest.raises(ValueError, match="production_factor_matrix_nonfinite"):
        scorer.score_frame(pd.DataFrame({"factor_a": [value]}), minimal_config())


def test_production_scorer_same_input_same_output() -> None:
    scorer = load_scorer()
    frame = pd.DataFrame({"factor_a": [10.0, 20.0, 30.0]})
    first = scorer.score_frame(frame, minimal_config())
    second = scorer.score_frame(frame.copy(deep=True), minimal_config())
    pd.testing.assert_frame_equal(first, second, check_exact=True)


def test_rule_asset_hash_drift_fails_closed(tmp_path: Path) -> None:
    asset = tmp_path / "asset.txt"
    asset.write_text("locked", encoding="utf-8")
    lock = tmp_path / "lock.json"
    lock.write_text(
        json.dumps(
            {
                "schema": "FEILONG_DAILY_SCORE_PRODUCTION_LOCK_V2",
                "status": "LOCKED",
                "formula_name": "飞龙在天",
                "factor_count": 640,
                "rankable_factor_count": 634,
                "dimension_count": 32,
                "model_schema": "FEILONG_YAOGU_32D_SCORE_V2",
                "decision_rule_version": "FEILONG_32D_DECISION_V2",
                "minimum_prior_trading_bars": 251,
                "assets": [
                    {**daily.file_evidence(asset), "role": role}
                    for role in ("score_model", "training_history", "score_engine")
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    daily.validate_production_lock(lock)
    asset.write_text("drifted", encoding="utf-8")
    with pytest.raises(RuntimeError, match="生产规则资产漂移"):
        daily.validate_production_lock(lock)


def test_local_risk_corpus_excludes_dynamic_binary_market_cache(tmp_path: Path) -> None:
    message_dir = tmp_path / "T0002" / "msg_zx"
    cache_dir = tmp_path / "T0002" / "cache"
    info_dir = tmp_path / "T0002" / "info_cache"
    message_dir.mkdir(parents=True)
    cache_dir.mkdir(parents=True)
    info_dir.mkdir(parents=True)
    announcement = message_dir / "realinfo.html"
    cached_day = cache_dir / "sh600000.~~~day"
    index = message_dir / "msg_zx.idx"
    info = info_dir / "announcement.json"
    announcement.write_text("公告", encoding="utf-8")
    cached_day.write_bytes(b"binary market cache")
    index.write_bytes(b"binary index")
    info.write_text('{"event":"公告"}', encoding="utf-8")

    target_date = pd.Timestamp.now().strftime("%Y%m%d")
    assert daily.local_risk_corpus_paths(tmp_path, target_date) == [
        info.resolve(),
        announcement.resolve(),
    ]


def no_prior_event_bars(periods: int = 261, *, descending: bool = False) -> pd.DataFrame:
    dates = pd.date_range("2025-08-01", periods=periods, freq="B").strftime("%Y%m%d")
    direction = -1.0 if descending else 1.0
    close = 10.0 + direction * np.arange(periods, dtype=float) * 0.001
    return pd.DataFrame(
        {
            "date": dates,
            "open": close * 0.999,
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "amount": np.full(periods, 10_000_000.0),
            "volume": np.full(periods, 1_000_000.0),
        }
    )


def test_zero_prior_event_state_is_finite_and_explicit() -> None:
    bars = no_prior_event_bars()
    factors = yaogu.calculate_yaogu_daily_factors(bars, len(bars) - 1)
    zero_state_factors = [
        *(f"prior_touch_fail_ratio_{window}d" for window in (60, 120, 250)),
        *(f"prior_isolated_limit_share_{window}d" for window in (60, 120, 250)),
        *(f"prior_limit_interarrival_cv_{window}d" for window in (60, 120, 250)),
        "prior_limit_nextday_continuation_rate_250d",
        "prior_limit_nextday_return_mean_250d",
        "prior_limit_nextday_gap_mean_250d",
        "prior_limit_post3d_return_mean_250d",
        "prior_limit_post3d_drawdown_mean_250d",
        "prior_touch_fail_nextday_recovery_rate_250d",
    ]
    actual = {factor: factors[factor] for factor in zero_state_factors}
    assert all(np.isfinite(value) for value in actual.values()), actual
    assert all(value == 0.0 for value in actual.values()), actual


def test_flat_post_trough_path_has_zero_recovery_efficiency() -> None:
    bars = no_prior_event_bars(descending=True)
    factors = yaogu.calculate_yaogu_daily_factors(bars, len(bars) - 1)
    assert factors["prior_post_trough_recovery_efficiency_20d"] == 0.0


def test_last_two_limitup_gap_uses_window_outside_sentinel() -> None:
    no_event = np.zeros(120, dtype=bool)
    one_event = no_event.copy()
    one_event[30] = True
    two_events = no_event.copy()
    two_events[[10, 50]] = True
    assert factor_research.last_two_limitup_gap_or_sentinel(no_event, 120) == 121.0
    assert factor_research.last_two_limitup_gap_or_sentinel(one_event, 120) == 121.0
    assert factor_research.last_two_limitup_gap_or_sentinel(two_events, 120) == 40.0
