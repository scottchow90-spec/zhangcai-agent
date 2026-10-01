from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import inspect
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "three_formula_composite_backtest.py"
SPEC = importlib.util.spec_from_file_location("exact_thirty_item_runtime", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_current_scoring_runtime_exposes_only_the_original_thirty_items() -> None:
    catalog = MODULE.subsystem_catalog()
    counts = {
        formula: sum(row["formula"] == formula for row in catalog)
        for formula in MODULE.FORMULAS
    }
    assert counts == {
        "大牛线撑压版": 16,
        "飞龙在天": 10,
        "庄家资金监控": 4,
    }
    assert len(catalog) == 30
    assert "core_mainline_context" not in inspect.signature(
        MODULE.score_feature_frame
    ).parameters

    model = MODULE.build_hierarchical_model(
        catalog,
        {
            formula: np.array(
                [
                    1.0
                    if row["formula"] == formula and not row["forced_zero_reason"]
                    else 0.0
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
        resonance_bonus=0.08,
        disagreement_penalty=0.08,
    )
    frame = MODULE.pd.DataFrame(
        [
            {
                "date": "20260817",
                "symbol": "000001.SZ",
                **{row["key"]: 1.0 for row in catalog},
            }
        ]
    )

    row = MODULE.score_feature_frame(frame, model).iloc[0]
    assert len(row["contributions"]) == 30
    assert set(row["top_level_items"]) == set(MODULE.FORMULAS)
    assert "core_mainline_item" not in row
    assert MODULE.CURRENT_SCORE_ARTIFACTS == (
        "三公式综合评分最新排名.json",
        "三公式综合评分最新排名.csv",
        "三公式综合评分30项贡献明细.csv",
        "三公式综合评分最新排名报告.md",
    )


def test_active_skill_surfaces_and_execution_contract_remove_added_projects() -> None:
    active_files = (
        ROOT / "SKILL.md",
        ROOT / "references" / "workflow.md",
        ROOT / "references" / "three_formula_composite_scoring.md",
        ROOT / "scripts" / "analysis_scoring.py",
        ROOT / "scripts" / "canonical_business_adapter.py",
        ROOT / "scripts" / "poster_builder.py",
        ROOT / "scripts" / "three_formula_composite_backtest.py",
    )
    forbidden = (
        "核心主线评分系统",
        "短线市场情绪适配",
        "31项",
        "第31项",
        "core_mainline",
        "sentiment_gate",
        "short-term-sentiment",
        "short_term_market_sentiment",
    )
    combined = "\n".join(path.read_text(encoding="utf-8") for path in active_files)
    for marker in forbidden:
        assert marker not in combined
    for marker in ("大牛线40%", "飞龙在天35%", "庄家资金监控25%", "固定30项"):
        assert marker in combined

    contract_catalog = json.loads(
        Path(
            r"D:\C盘转移\日志\codex\skills\stock-unified\references\stock_execution_contracts.json"
        ).read_text(encoding="utf-8")
    )
    contract = next(
        row
        for row in contract_catalog["contracts"]
        if row["skill_id"] == "big-bull-analysis-scoring-system"
    )
    binding_paths = "\n".join(
        str(binding["path"]) for binding in contract["business_bindings"]
    ).lower()
    required_bindings = "\n".join(
        contract["workflow_guard"]["required_bindings"]
    ).lower()
    assert "core_mainline" not in binding_paths + required_bindings
    assert "sentiment" not in binding_paths + required_bindings
    lianban = contract.get("supplemental_sources", {}).get("lianban_daily", {})
    assert lianban.get("enabled") is True
    assert lianban.get("required") is False
    assert "lianban" not in binding_paths + required_bindings


def test_full_thirty_item_scoring_semantics_are_documented_on_all_active_surfaces() -> None:
    documentation = (
        ROOT / "SKILL.md",
        ROOT / "references" / "workflow.md",
        ROOT / "references" / "three_formula_composite_scoring.md",
    )
    required_markers = (
        "中点秩",
        "真实",
        "正业务权重",
        "缺一项",
        "固定母体分位",
        "不是上涨概率",
    )

    for path in documentation:
        content = path.read_text(encoding="utf-8")
        for marker in required_markers:
            assert marker in content, f"{path.name}缺少评分语义：{marker}"
