from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PROJECT = Path(r"F:\Codex\projects\飞龙在天评分体系彻底优化_20260901-184258")
MODEL_PATH = PROJECT / "飞龙共振首板_32维评分模型配置.json"
SCORER_PATH = PROJECT / "apply_yaogu_scoring.py"
HISTORY_PATH = PROJECT / "因子全量重算" / "飞龙共振首板_全量因子事件值.csv"
REFERENCE_PATH = PROJECT / "飞龙共振首板_样本逐股32维评分.csv"


def load_scorer():
    spec = importlib.util.spec_from_file_location("optimized_feilong_scorer_test", SCORER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_fixture() -> tuple[dict, pd.DataFrame]:
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    factor_names = [str(item["factor"]) for item in model["factors"]]
    columns = ["symbol", "first_board_date", *factor_names]
    history = pd.read_csv(HISTORY_PATH, usecols=columns, nrows=800, low_memory=False)
    numeric = history[factor_names].apply(pd.to_numeric, errors="coerce")
    complete = history.loc[np.isfinite(numeric.to_numpy(dtype=float)).all(axis=1)].head(32).copy()
    assert len(complete) == 32
    complete.loc[:, factor_names] = numeric.loc[complete.index, factor_names]
    return model, complete.reset_index(drop=True)


def test_v2_model_contract_is_clean() -> None:
    model, _frame = load_fixture()
    validation = model["production_validation"]
    assert model["schema"] == "FEILONG_YAOGU_32D_SCORE_V2"
    assert model["registered_factor_count"] == 640
    assert model["rankable_factor_count"] == 634
    assert model["dimension_count"] == 32
    assert model["imputed_training_cells"] == 0
    assert validation["status"] == "CLEAN_PASS"
    assert validation["development_grade_monotonic"] is True
    assert validation["sealed_holdout_top_grade_positive_lift"] is True


def test_real_history_score_is_exactly_repeatable_and_matches_build_output() -> None:
    scorer = load_scorer()
    model, frame = load_fixture()
    first = scorer.score_frame(frame, model)
    second = scorer.score_frame(frame.copy(deep=True), model)
    pd.testing.assert_frame_equal(first, second, check_exact=True)

    score_columns = [
        "连板启动分",
        "妖股深化分",
        "妖股综合评分",
        *[f"维度{index:02d}_{family}" for index, family in enumerate(model["dimensions"], start=1)],
    ]
    reference = pd.read_csv(
        REFERENCE_PATH,
        usecols=["symbol", "first_board_date", *score_columns],
        low_memory=False,
    )
    expected = frame[["symbol", "first_board_date"]].merge(
        reference,
        on=["symbol", "first_board_date"],
        how="left",
        validate="one_to_one",
    )
    assert expected[score_columns].notna().all().all()
    np.testing.assert_allclose(
        first[score_columns].to_numpy(dtype=float),
        expected[score_columns].to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-12,
    )


def test_real_model_rejects_single_nonfinite_cell() -> None:
    scorer = load_scorer()
    model, frame = load_fixture()
    frame.loc[0, model["factors"][0]["factor"]] = np.nan
    with pytest.raises(ValueError, match="production_factor_matrix_nonfinite"):
        scorer.score_frame(frame, model)
