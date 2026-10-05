#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import csv
import hashlib
import json
import math
import os
import struct
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_tdx_root

import numpy as np
import pandas as pd

from scipy.stats import spearmanr
from sklearn.linear_model import ElasticNet, LinearRegression, Ridge

from scoring_mode_gate import (
    CANONICAL_SCORING_MODE,
    COMPONENT_ITEM_COUNTS,
    SCORING_CONTRACT_ID,
    SCORING_UNIVERSE_POLICY,
    TOP_LEVEL_WEIGHTS,
    validate_composite_ranking_identity,
)


TDX_ROOT = resolve_tdx_root()
TQ_USER_DIR = TDX_ROOT / "PYPlugins" / "user"
TQ_INIT_PATH = TQ_USER_DIR / "tdxdata_test.py"
DEFAULT_BLOCK_DIR = TDX_ROOT / "T0002" / "blocknew"
STOCK_NAME_INDEX = TDX_ROOT / "T0002" / "hq_cache" / "infoharbor_ex.code"
BIG_BULL_FORMULA = "大牛线撑压版"
FEILONG_FORMULA = "飞龙在天"
DEALER_FORMULA = "庄家资金监控"
FORMULAS = (BIG_BULL_FORMULA, FEILONG_FORMULA, DEALER_FORMULA)
FORMULA_SOURCES = (
    TDX_ROOT / "T0002" / "gs_bak" / "大牛线.txt",
    TDX_ROOT / "T0002" / "gs_bak" / "飞龙在天.txt",
    TDX_ROOT / "T0002" / "gs_bak" / "庄家资金监控.txt",
)
METHODOLOGY_VERSION = "THREE_FORMULA_COMPOSITE_V6_FULL_30_STRUCTURAL_FORECAST"
SHANGHAI_TIMEZONE = "Asia/Shanghai"
SHANGHAI = ZoneInfo(SHANGHAI_TIMEZONE)
CURRENT_SCORE_ARTIFACTS = (
    "三公式综合评分最新排名.json",
    "三公式综合评分最新排名.csv",
    "三公式综合评分30项贡献明细.csv",
    "三公式综合评分最新排名报告.md",
)
MIN_OOS_DATES = 40
MIN_MEAN_IC = 0.01
MIN_5D_EXCESS_RETURN = 0.001
MIN_10D_EXCESS_RETURN = 0.0015


class OptimizationBlocked(RuntimeError):
    def __init__(self, message: str, evidence: dict[str, Any]):
        super().__init__(message)
        self.evidence = evidence


class ScoringDateBlocked(RuntimeError):
    def __init__(self, message: str, evidence: dict[str, Any]):
        super().__init__(message)
        self.evidence = evidence


class FormalModelUnavailable(ValueError):
    pass


def shanghai_now(now: datetime | None = None) -> datetime:
    if now is None:
        return datetime.now(SHANGHAI)
    if now.tzinfo is None:
        return now.replace(tzinfo=SHANGHAI)
    return now.astimezone(SHANGHAI)


def enforce_current_scoring_date(
    score_date: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    moment = shanghai_now(now)
    beijing_date = moment.strftime("%Y%m%d")
    actual_score_date = str(score_date).replace("-", "").strip()
    preopen_latest_complete = (
        moment.weekday() < 5
        and (moment.hour, moment.minute) < (9, 30)
        and actual_score_date < beijing_date
    )
    required_score_date = actual_score_date if preopen_latest_complete else beijing_date
    evidence = {
        "status": "PASS",
        "timezone": SHANGHAI_TIMEZONE,
        "beijing_date": beijing_date,
        "beijing_weekday": moment.weekday(),
        "score_date": actual_score_date,
        "required_score_date": required_score_date,
        "rule": (
            "SHANGHAI_PREOPEN_LATEST_COMPLETE_TRADING_DAY"
            if preopen_latest_complete
            else "SHANGHAI_WEEKDAY_SCORE_DATE_MUST_EQUAL_TODAY"
        ),
        "reason": "开盘前使用本机最近完整交易日" if preopen_latest_complete else "",
    }
    if (
        moment.weekday() < 5
        and not preopen_latest_complete
        and actual_score_date != required_score_date
    ):
        evidence["status"] = "BLOCKED"
        evidence["reason"] = (
            "本机行情未更新到北京时间当天，禁止生成或交付评分榜单"
        )
        raise ScoringDateBlocked(
            "评分交易日硬闸阻断："
            f"北京时间当前日期{beijing_date}，实际评分日{actual_score_date}；"
            "本机行情未更新到当天",
            evidence,
        )
    return evidence


def subsystem_catalog() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(
        formula: str,
        number: int,
        key: str,
        name: str,
        source: str,
        forced_zero_reason: str = "",
    ) -> None:
        rows.append(
            {
                "formula": formula,
                "number": number,
                "key": key,
                "name": name,
                "source": source,
                "forced_zero_reason": forced_zero_reason,
            }
        )

    add(BIG_BULL_FORMULA, 1, "dnx_main_trend", "主趋势线", "TQ主趋势线历史序列")
    add(BIG_BULL_FORMULA, 2, "dnx_ema_layers", "EMA均线分层", "公式原文因果推导")
    add(BIG_BULL_FORMULA, 3, "dnx_k_color", "K线颜色信号", "公式原文因果推导")
    add(
        BIG_BULL_FORMULA,
        4,
        "dnx_float_cap",
        "流通市值",
        "TQ流通市值输出",
    )
    add(BIG_BULL_FORMULA, 5, "dnx_dx", "DX动量指标", "公式原文因果推导")
    add(BIG_BULL_FORMULA, 6, "dnx_participation_exit", "参与与离场信号", "公式原文因果推导")
    add(BIG_BULL_FORMULA, 7, "dnx_control", "控盘程度", "公式原文因果推导")
    add(BIG_BULL_FORMULA, 8, "dnx_caishen", "财神短线", "公式原文因果推导")
    add(BIG_BULL_FORMULA, 9, "dnx_dealer_in_out", "庄进/庄出", "TQ OUTPUT4/OUTPUT6历史序列")
    add(
        BIG_BULL_FORMULA,
        10,
        "dnx_yaogu",
        "妖股识别",
        "公式原文按日线收盘时点因果推导",
    )
    add(BIG_BULL_FORMULA, 11, "dnx_leader_zone", "龙头参与区", "公式原文因果推导")
    add(BIG_BULL_FORMULA, 12, "dnx_dragon_pullback", "龙回头", "公式原文因果推导")
    add(BIG_BULL_FORMULA, 13, "dnx_ignition", "点火信号", "TQ OUTPUT9与公式原文交叉核对")
    add(BIG_BULL_FORMULA, 14, "dnx_theme_resonance", "起爆/题材共振", "公式原文因果推导")
    add(BIG_BULL_FORMULA, 15, "dnx_boll_ma", "BOLL+多重均线", "公式原文因果推导")
    add(BIG_BULL_FORMULA, 16, "dnx_support_pressure", "核心黄金分割撑压", "TQ支撑压力历史序列")

    add(FEILONG_FORMULA, 1, "fl_dragon", "龙头战法", "TQ OUTPUT3历史序列")
    add(FEILONG_FORMULA, 2, "fl_trend_filter", "趋势过滤/中长期均线强势条件", "公式原文因果推导")
    add(FEILONG_FORMULA, 3, "fl_box", "四日实体重叠箱体/波段密码底层形态", "公式原文因果推导")
    add(FEILONG_FORMULA, 4, "fl_unique_limit", "首板/唯一涨停确认", "公式原文因果推导")
    add(FEILONG_FORMULA, 5, "fl_board", "波段密码打板", "TQ OUTPUT4历史序列")
    add(FEILONG_FORMULA, 6, "fl_surge", "量价模型/暴涨启动", "TQ OUTPUT5历史序列")
    add(FEILONG_FORMULA, 7, "fl_wave", "波段随机强弱-波", "TQ波历史序列")
    add(FEILONG_FORMULA, 8, "fl_segment", "波段随机强弱-段", "TQ段历史序列")
    add(FEILONG_FORMULA, 9, "fl_private", "私募秘进", "TQ OUTPUT6历史序列")
    add(FEILONG_FORMULA, 10, "fl_main_rise", "主升启动共振", "TQ输出组合因果推导")

    add(DEALER_FORMULA, 1, "zj_cost_pressure", "成本压力B2", "公式原文B1经35日SMA后加100")
    add(DEALER_FORMULA, 2, "zj_fund_strength", "资金强度B5", "公式原文B3经7日、5日SMA后加100")
    add(DEALER_FORMULA, 3, "zj_control_spread", "控盘差值B6", "公式原文B5减B2")
    add(DEALER_FORMULA, 4, "zj_control_degree", "控盘程度", "公式原文MAX(B6-3,0)乘3.5")
    return rows


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tdx_stock_names(
    path: Path = STOCK_NAME_INDEX,
) -> dict[str, str]:
    if not path.is_file():
        raise FileNotFoundError(f"通达信股票名称索引不存在：{path}")
    text = path.read_bytes().decode("gbk", errors="ignore")
    names: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.strip().split("|")
        if len(parts) < 2:
            continue
        code = parts[0].strip()
        name = parts[1].strip()
        if len(code) == 6 and code.isdigit() and name:
            names[code] = name
    if not names:
        raise RuntimeError(f"通达信股票名称索引为空：{path}")
    return names


def safe_float(value: Any) -> float:
    if isinstance(value, dict):
        value = value.get("Value")
    try:
        number = float(value)
    except (TypeError, ValueError):
        return math.nan
    return number if math.isfinite(number) else math.nan


def load_board_symbols(
    board_code: str,
    board_file: str,
) -> tuple[list[str], Path] | tuple[None, None]:
    if not board_code and not board_file:
        return None, None
    path = (
        Path(board_file).expanduser().resolve()
        if board_file
        else DEFAULT_BLOCK_DIR / f"{board_code}.blk"
    )
    if not path.is_file():
        raise FileNotFoundError(f"通达信自定义板块文件不存在：{path}")
    symbols: list[str] = []
    seen: set[str] = set()
    for raw in path.read_text(encoding="ascii", errors="ignore").splitlines():
        value = raw.strip()
        if len(value) != 7 or not value.isdigit():
            continue
        symbol = f"{value[1:]}.{'SH' if value[0] == '1' else 'SZ'}"
        if symbol not in seen:
            seen.add(symbol)
            symbols.append(symbol)
    if not symbols:
        raise ValueError(f"通达信自定义板块为空：{path}")
    return symbols, path


def merge_scoring_universe(
    benchmark_symbols: list[str],
    board_symbols: list[str] | None,
    max_stocks: int,
) -> list[str]:
    del board_symbols
    selected = sorted(set(benchmark_symbols))
    return selected[:max_stocks] if max_stocks else selected


def merge_fetch_symbols(
    reference_symbols: list[str],
    board_symbols: list[str] | None,
) -> list[str]:
    return sorted(set(reference_symbols) | set(board_symbols or []))


def canonical_payload_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_scoring_identity(
    symbols: list[str],
    score_date: str,
    model: dict[str, Any],
) -> dict[str, Any]:
    formula_material = {
        "catalog": subsystem_catalog(),
        "sources": [
            {
                "path": str(path),
                "sha256": sha256_file(path) if path.is_file() else None,
            }
            for path in FORMULA_SOURCES
        ],
    }
    canonical_symbols = sorted(set(symbols))
    return {
        "contract_id": SCORING_CONTRACT_ID,
        "canonical_mode": CANONICAL_SCORING_MODE,
        "score_date": str(score_date),
        "universe_policy": SCORING_UNIVERSE_POLICY,
        "tdx_market": "23",
        "universe_count": len(canonical_symbols),
        "universe_sha256": canonical_payload_sha256(canonical_symbols),
        "model_sha256": canonical_payload_sha256(model),
        "formula_catalog_sha256": canonical_payload_sha256(formula_material),
        "component_item_counts": list(COMPONENT_ITEM_COUNTS),
        "top_level_weights": list(TOP_LEVEL_WEIGHTS),
    }


def validate_cross_board_score_consistency(
    payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    if len(payloads) < 2:
        raise ValueError("cross_board_payload_count_invalid")
    identities = []
    rows_by_symbol: list[dict[str, dict[str, Any]]] = []
    for payload in payloads:
        validate_composite_ranking_identity(payload)
        identities.append(payload["scoring_identity"])
        ranking = payload.get("ranking")
        if not isinstance(ranking, list):
            raise ValueError("cross_board_ranking_invalid")
        rows_by_symbol.append({str(row.get("symbol", "")): row for row in ranking})
    identity_materials = [
        canonical_payload_sha256(identity)
        for identity in identities
    ]
    if len(set(identity_materials)) != 1:
        raise ValueError("cross_board_identity_drift")

    common_symbols = set(rows_by_symbol[0])
    for rows in rows_by_symbol[1:]:
        common_symbols &= set(rows)
    score_fields = (
        "score",
        "formula_scores",
        "top_level_items",
        "fusion",
        "contributions",
    )
    for symbol in sorted(common_symbols):
        signatures = [
            canonical_payload_sha256(
                {field: rows[symbol].get(field) for field in score_fields}
            )
            for rows in rows_by_symbol
        ]
        if len(set(signatures)) != 1:
            raise ValueError(f"cross_board_score_drift:{symbol}")
    return {
        "status": "PASS",
        "payload_count": len(payloads),
        "universe_sha256": identities[0]["universe_sha256"],
        "common_stock_count": len(common_symbols),
        "common_symbols": sorted(common_symbols),
    }


def percentile_scores(values: np.ndarray) -> np.ndarray:
    series = pd.Series(np.asarray(values, dtype=float))
    finite_count = int(series.notna().sum())
    if finite_count <= 0:
        return np.full(len(series), 50.0, dtype=float)
    ranks = series.rank(method="average", na_option="keep")
    result = ranks.sub(0.5).div(finite_count).mul(100.0).to_numpy(dtype=float)
    return np.where(np.isfinite(result), result, 50.0)


def _normalize_positive(values: np.ndarray) -> np.ndarray:
    result = np.maximum(np.asarray(values, dtype=float), 0.0)
    if result.sum() <= 0:
        raise ValueError("模型没有产生有效非零系数")
    return result / result.sum()


def build_hierarchical_model(
    catalog: list[dict[str, Any]],
    subsystem_coefficients: dict[str, np.ndarray],
    system_weights: dict[str, float],
    *,
    resonance_bonus: float,
    disagreement_penalty: float,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if set(subsystem_coefficients) != set(FORMULAS):
        raise ValueError("体系内系数必须完整覆盖三套公式")
    if set(system_weights) != set(FORMULAS):
        raise ValueError("体系级权重必须完整覆盖三套公式")
    normalized_system = _normalize_positive(
        np.array([system_weights[formula] for formula in FORMULAS], dtype=float)
    )
    if np.any(normalized_system < 0.10 - 1e-12):
        raise ValueError("三套体系的正式权重均不得低于10%")

    subsystem_rows: list[dict[str, Any]] = []
    for formula in FORMULAS:
        coefficients = np.asarray(subsystem_coefficients[formula], dtype=float)
        if len(coefficients) != len(catalog):
            raise ValueError(f"{formula}体系内系数数量与固定30项不一致")
        active = np.array(
            [
                row["formula"] == formula and not row["forced_zero_reason"]
                for row in catalog
            ],
            dtype=bool,
        )
        local = np.zeros(len(catalog), dtype=float)
        importance = np.abs(coefficients[active])
        if importance.sum() <= 0:
            reliability = safe_float(
                (metadata or {}).get("system_reliability", {}).get(formula, 1.0)
            )
            if reliability != 0.0:
                raise ValueError(f"{formula}体系内模型没有有效系数")
        else:
            local[active] = importance / importance.sum() * 100.0
        for index, row in enumerate(catalog):
            if row["formula"] != formula:
                continue
            subsystem_rows.append(
                {
                    **row,
                    "coefficient": round(float(coefficients[index]), 10),
                    "direction": -1 if coefficients[index] < 0 else 1,
                    "local_weight": round(float(local[index]), 8),
                }
            )

    return {
        "schema": "THREE_FORMULA_HIERARCHICAL_MODEL_V1",
        "model_type": "hierarchical_three_system_resonance",
        "methodology_version": METHODOLOGY_VERSION,
        "system_weights": {
            formula: round(float(weight * 100.0), 8)
            for formula, weight in zip(FORMULAS, normalized_system, strict=True)
        },
        "subsystem_weights": subsystem_rows,
        "fusion": {
            "resonance_bonus": round(float(resonance_bonus), 8),
            "disagreement_penalty": round(float(disagreement_penalty), 8),
            "formula": (
                "总分=体系加权基础分+三体系共振加分-体系分歧扣分，"
                "并限制在0至100分"
            ),
        },
        "metadata": metadata or {},
    }


def build_structural_fallback_model(
    catalog: list[dict[str, Any]],
    diagnostics: dict[str, dict[str, Any]],
    *,
    reason: str,
) -> dict[str, Any]:
    priors = {
        BIG_BULL_FORMULA: 0.40,
        FEILONG_FORMULA: 0.35,
        DEALER_FORMULA: 0.25,
    }
    coefficients: dict[str, np.ndarray] = {}
    reliability: dict[str, float] = {}
    for formula in FORMULAS:
        values = np.zeros(len(catalog), dtype=float)
        active_values: list[float] = []
        for index, row in enumerate(catalog):
            if row["formula"] != formula or row["forced_zero_reason"]:
                continue
            item = diagnostics.get(row["key"], {})
            coverage = max(0.0, min(1.0, safe_float(item.get("coverage"))))
            total_dates = max(1.0, safe_float(item.get("total_dates")))
            informative = max(
                0.0,
                min(
                    1.0,
                    safe_float(item.get("informative_dates")) / total_dates,
                ),
            )
            value = max(0.01, math.sqrt(coverage * informative))
            values[index] = value
            active_values.append(value)
        if not active_values:
            raise ValueError(f"{formula}没有可用于结构模型的审计项")
        coefficients[formula] = values
        reliability[formula] = float(np.mean(active_values))
    system_weights = {
        formula: priors[formula] * reliability[formula]
        for formula in FORMULAS
    }
    return build_hierarchical_model(
        catalog,
        coefficients,
        system_weights,
        resonance_bonus=0.08,
        disagreement_penalty=0.08,
        metadata={
            "model_origin": "audited_structural_fallback",
            "predictive_validation": "BLOCKED_NO_PREDICTIVE_CANDIDATE",
            "predictive_validation_reason": reason,
            "system_role_priors": priors,
            "system_reliability": reliability,
            "weight_basis": "历史覆盖率与横截面区分度审计",
        },
    )


def build_fixed_research_model_payload() -> tuple[dict[str, Any], dict[str, Any]]:
    catalog = subsystem_catalog()
    priors = {
        BIG_BULL_FORMULA: 0.40,
        FEILONG_FORMULA: 0.35,
        DEALER_FORMULA: 0.25,
    }
    coefficients: dict[str, np.ndarray] = {}
    for formula in FORMULAS:
        values = np.zeros(len(catalog), dtype=float)
        for index, row in enumerate(catalog):
            if row["formula"] == formula and not row["forced_zero_reason"]:
                values[index] = 1.0
        coefficients[formula] = values
    model = build_hierarchical_model(
        catalog,
        coefficients,
        priors,
        resonance_bonus=0.08,
        disagreement_penalty=0.08,
        metadata={
            "model_origin": "fixed_research_structural",
            "predictive_validation": "NOT_APPLICABLE_RESEARCH_ONLY",
            "system_role_priors": priors,
            "weight_basis": "固定研究结构先验，体系内有效项目等权",
            "prediction_authorized": False,
        },
    )
    payload = {
        "schema": "THREE_FORMULA_RESEARCH_STRUCTURAL_MODEL_V1",
        "status": "RESEARCH_ONLY",
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": shanghai_now().isoformat(timespec="seconds"),
        "predictive_validation": {
            "status": "NOT_APPLICABLE",
            "reason": "研究型结构评分不使用回测或训练权重",
        },
        "model": model,
    }
    return payload, model


def build_research_model_for_frame(
    frame: pd.DataFrame,
    reference_symbols: list[str],
    *,
    minimum_coverage: float = 0.95,
) -> tuple[dict[str, Any], dict[str, Any]]:
    catalog = [dict(row) for row in subsystem_catalog()]
    reference_set = set(reference_symbols)
    reference = frame[frame["symbol"].isin(reference_set)].copy()
    if reference.empty:
        raise ValueError("scoring_reference_universe_empty")
    diagnostics: dict[str, dict[str, Any]] = {}
    for row in catalog:
        key = str(row["key"])
        if key not in reference:
            raise ValueError(f"thirty_item_data_incomplete:{key}:missing_column")
        values = pd.to_numeric(reference[key], errors="coerce")
        finite = values[np.isfinite(values.to_numpy(dtype=float))]
        coverage = float(len(finite) / len(reference))
        unique_count = int(finite.nunique(dropna=True))
        if coverage < 1.0:
            raise ValueError(
                f"thirty_item_data_incomplete:{key}:coverage={coverage:.8f}"
            )
        informative = unique_count > 1
        diagnostics[key] = {
            "coverage": round(coverage, 8),
            "unique_count": unique_count,
            "informative": informative,
            "neutral_observation": not informative,
            "forced_zero_reason": "",
        }

    coefficients: dict[str, np.ndarray] = {}
    system_reliability: dict[str, float] = {}
    for formula in FORMULAS:
        values = np.zeros(len(catalog), dtype=float)
        active = [
            index
            for index, row in enumerate(catalog)
            if row["formula"] == formula
        ]
        values[active] = 1.0
        coefficients[formula] = values
        system_reliability[formula] = 1.0

    priors = {
        BIG_BULL_FORMULA: 0.40,
        FEILONG_FORMULA: 0.35,
        DEALER_FORMULA: 0.25,
    }
    model = build_hierarchical_model(
        catalog,
        coefficients,
        priors,
        resonance_bonus=0.08,
        disagreement_penalty=0.08,
        metadata={
            "model_origin": "current_reference_information_aware_research",
            "predictive_validation": "NOT_APPLICABLE_RESEARCH_ONLY",
            "prediction_authorized": False,
            "weight_basis": "固定30项全部参与，体系内等权；常量观测按中点秩50分保留正权重",
            "minimum_coverage": minimum_coverage,
            "system_reliability": system_reliability,
            "neutralized_systems": [],
            "active_subsystem_count": len(catalog),
            "all_subsystems_participate": True,
            "research_information_diagnostics": diagnostics,
        },
    )
    payload = {
        "schema": "THREE_FORMULA_RESEARCH_STRUCTURAL_MODEL_V1",
        "status": "RESEARCH_ONLY",
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": shanghai_now().isoformat(timespec="seconds"),
        "predictive_validation": {
            "status": "NOT_APPLICABLE",
            "reason": "研究型结构评分不使用回测或训练权重",
        },
        "model": model,
    }
    return payload, model


def validate_hierarchical_model(model: dict[str, Any]) -> None:
    catalog = subsystem_catalog()
    expected_keys = [row["key"] for row in catalog]
    if model.get("model_type") != "hierarchical_three_system_resonance":
        raise ValueError("正式模型不是三体系分层共振模型")
    rows = model.get("subsystem_weights")
    if not isinstance(rows, list):
        raise ValueError("正式模型缺少体系内权重")
    actual_keys = [str(row.get("key", "")) for row in rows]
    if actual_keys != expected_keys:
        raise ValueError("正式模型未按固定顺序覆盖30个子系统")
    system_weights = model.get("system_weights")
    if not isinstance(system_weights, dict) or set(system_weights) != set(FORMULAS):
        raise ValueError("正式模型缺少完整三体系权重")
    if abs(sum(float(system_weights[name]) for name in FORMULAS) - 100.0) > 1e-6:
        raise ValueError("正式模型的三体系权重总和不是100")
    if min(float(system_weights[name]) for name in FORMULAS) < 10.0 - 1e-6:
        raise ValueError("正式模型存在低于10%的体系权重")
    reliability = model.get("metadata", {}).get("system_reliability", {})
    if reliability:
        if set(reliability) != set(FORMULAS) or any(
            not math.isfinite(safe_float(reliability[name]))
            or safe_float(reliability[name]) < 0
            or safe_float(reliability[name]) > 1
            for name in FORMULAS
        ):
            raise ValueError("三体系信息可靠性无效")
    for formula in FORMULAS:
        local_sum = sum(
            float(row["local_weight"])
            for row in rows
            if row["formula"] == formula
        )
        expected_sum = 0.0 if safe_float(reliability.get(formula, 1.0)) == 0 else 100.0
        if abs(local_sum - expected_sum) > 1e-6:
            raise ValueError(f"{formula}体系内权重总和无效")
    if any(
        int(row.get("direction", 0)) not in {-1, 1}
        for row in rows
    ):
        raise ValueError("正式模型的体系内方向必须为正向或反向")
    fusion = model.get("fusion")
    if not isinstance(fusion, dict):
        raise ValueError("正式模型缺少共振融合参数")
    for key in ("resonance_bonus", "disagreement_penalty"):
        value = safe_float(fusion.get(key))
        if not math.isfinite(value) or value < 0 or value > 0.5:
            raise ValueError(f"正式模型融合参数无效：{key}")


def fuse_system_scores(
    system_scores: dict[str, float],
    system_weights: dict[str, float],
    *,
    resonance_bonus: float,
    disagreement_penalty: float,
) -> dict[str, float]:
    scores = np.array([safe_float(system_scores[name]) for name in FORMULAS])
    weights = np.array([safe_float(system_weights[name]) for name in FORMULAS])
    if not np.isfinite(scores).all() or not np.isfinite(weights).all():
        raise ValueError("三体系分数或权重包含无效值")
    weights = _normalize_positive(weights)
    base_score = float(scores @ weights)
    spread = float(scores.max() - scores.min())
    agreement = max(0.0, 1.0 - spread / 100.0)
    resonance = float(resonance_bonus) * float(scores.min()) * agreement
    penalty = float(disagreement_penalty) * spread
    total = min(100.0, max(0.0, base_score + resonance - penalty))
    return {
        "base_score": round(base_score, 8),
        "resonance_bonus": round(resonance, 8),
        "disagreement_penalty": round(penalty, 8),
        "agreement": round(agreement, 8),
        "spread": round(spread, 8),
        "total_score": round(total, 8),
    }


def score_feature_frame(
    frame: pd.DataFrame,
    model: dict[str, Any],
    *,
    reference_symbols: list[str] | None = None,
) -> pd.DataFrame:
    validate_hierarchical_model(model)
    catalog = subsystem_catalog()
    expected_keys = [row["key"] for row in catalog]
    weight_by_key = {
        str(row["key"]): row for row in model["subsystem_weights"]
    }
    system_reliability = {
        formula: safe_float(
            model.get("metadata", {})
            .get("system_reliability", {})
            .get(formula, 1.0)
        )
        for formula in FORMULAS
    }

    ranked = frame[["date", "symbol", *expected_keys]].copy()
    ranked["_source_index"] = frame.index
    reference_set = set(reference_symbols or [])
    for _, indexes in ranked.groupby("date").groups.items():
        group_indexes = list(indexes)
        group = ranked.loc[group_indexes]
        if reference_symbols is None:
            reference_mask = np.ones(len(group), dtype=bool)
        else:
            reference_mask = group["symbol"].isin(reference_set).to_numpy()
            if not reference_mask.any():
                raise ValueError("scoring_reference_universe_empty")
        for key in expected_keys:
            direction = int(weight_by_key[key]["direction"])
            values = group[key].to_numpy(dtype=float) * direction
            if reference_symbols is None:
                ranked.loc[group_indexes, key] = percentile_scores(values)
                continue
            reference_values = values[reference_mask]
            finite_reference = reference_values[np.isfinite(reference_values)]
            if not len(finite_reference):
                ranked.loc[group_indexes, key] = 50.0
                continue
            reference_ranks = percentile_scores(reference_values)
            percentiles = np.full(len(values), 50.0, dtype=float)
            percentiles[reference_mask] = reference_ranks
            for position, value in enumerate(values):
                if reference_mask[position] or not math.isfinite(value):
                    continue
                less = int(np.sum(finite_reference < value))
                equal = int(np.sum(finite_reference == value))
                percentiles[position] = (
                    (less + 0.5 * equal) / len(finite_reference) * 100.0
                )
            ranked.loc[group_indexes, key] = percentiles

    rows: list[dict[str, Any]] = []
    for record in ranked.to_dict("records"):
        contributions = []
        formula_scores = {formula: 0.0 for formula in FORMULAS}
        for catalog_row in catalog:
            key = catalog_row["key"]
            local_weight = float(weight_by_key[key]["local_weight"])
            percentile = float(record[key])
            reliability = system_reliability[catalog_row["formula"]]
            effective_percentile = 50.0 + reliability * (percentile - 50.0)
            local_contribution = effective_percentile * local_weight / 100.0
            formula_scores[catalog_row["formula"]] += local_contribution
            contributions.append(
                {
                    "formula": catalog_row["formula"],
                    "number": catalog_row["number"],
                    "key": key,
                    "name": catalog_row["name"],
                    "raw_value": round(
                        safe_float(frame.loc[record["_source_index"], key]),
                        8,
                    ),
                    "percentile": round(percentile, 8),
                    "effective_percentile": round(effective_percentile, 8),
                    "system_reliability": round(reliability, 8),
                    "direction": int(weight_by_key[key]["direction"]),
                    "local_weight": round(local_weight, 8),
                    "local_contribution": round(local_contribution, 8),
                    "system_weight": round(
                        float(model["system_weights"][catalog_row["formula"]]),
                        8,
                    ),
                    "base_contribution": round(
                        local_contribution
                        * float(model["system_weights"][catalog_row["formula"]])
                        / 100.0,
                        8,
                    ),
                    "forced_zero_reason": str(
                        weight_by_key[key].get("forced_zero_reason", "")
                    ),
                }
            )
        formula_scores = {
            formula: (
                50.0
                if system_reliability[formula] == 0.0
                else round(score, 8)
            )
            for formula, score in formula_scores.items()
        }
        top_level_items = dict(formula_scores)
        fusion = fuse_system_scores(
            formula_scores,
            model["system_weights"],
            resonance_bonus=float(model["fusion"]["resonance_bonus"]),
            disagreement_penalty=float(
                model["fusion"]["disagreement_penalty"]
            ),
        )
        fusion["top_level_scores"] = top_level_items
        fusion["top_level_weights"] = {
            formula: round(float(model["system_weights"][formula]), 8)
            for formula in FORMULAS
        }
        fusion["top_level_item_count"] = len(FORMULAS)
        rows.append(
            {
                "date": str(record["date"]),
                "symbol": str(record["symbol"]),
                "score": fusion["total_score"],
                "formula_scores": formula_scores,
                "top_level_items": top_level_items,
                "fusion": fusion,
                "contributions": contributions,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["score", "symbol"],
        ascending=[False, True],
        ignore_index=True,
    )


def latest_broad_feature_frame(
    frame: pd.DataFrame,
    stock_count: int,
    minimum_fraction: float = 0.7,
) -> tuple[pd.DataFrame, str]:
    if frame.empty:
        raise RuntimeError("没有可用于当前评分的特征")
    minimum_count = max(5, int(math.ceil(stock_count * minimum_fraction)))
    counts = frame.groupby("date")["symbol"].nunique().sort_index()
    eligible = [
        str(date)
        for date, count in counts.items()
        if int(count) >= minimum_count
    ]
    if not eligible:
        raise RuntimeError("没有覆盖足够股票的统一评分日")
    score_date = eligible[-1]
    selected = (
        frame[frame["date"].astype(str) == score_date]
        .drop_duplicates("symbol", keep="last")
        .reset_index(drop=True)
    )
    return selected, score_date


def chronological_split(
    dates: np.ndarray,
    train_ratio: float = 0.6,
    validation_ratio: float = 0.2,
    purge_dates: int = 2,
) -> dict[str, np.ndarray]:
    values = np.asarray(dates).astype(str)
    unique = np.array(sorted(set(values)))
    if len(unique) < 5:
        raise ValueError("可用回测日期不足")
    if purge_dates < 0:
        raise ValueError("净化日期数不能为负数")
    train_end = max(1, int(len(unique) * train_ratio))
    validation_end = max(train_end + 1, int(len(unique) * (train_ratio + validation_ratio)))
    validation_end = min(validation_end, len(unique) - 1)
    train_keep_end = train_end - purge_dates
    validation_keep_end = validation_end - purge_dates
    if train_keep_end < 1 or validation_keep_end <= train_end:
        raise ValueError("净化区后训练或验证日期不足")
    train_dates = unique[:train_keep_end]
    purged_train_dates = unique[train_keep_end:train_end]
    validation_dates = unique[train_end:validation_keep_end]
    purged_validation_dates = unique[validation_keep_end:validation_end]
    test_dates = unique[validation_end:]
    return {
        "train": np.isin(values, train_dates),
        "validation": np.isin(values, validation_dates),
        "test": np.isin(values, test_dates),
        "train_dates": train_dates,
        "validation_dates": validation_dates,
        "test_dates": test_dates,
        "purged_train_dates": purged_train_dates,
        "purged_validation_dates": purged_validation_dates,
        "purge_dates": purge_dates,
    }


def _cap_weights(weights: np.ndarray, cap: float = 0.12) -> np.ndarray:
    result = np.maximum(np.asarray(weights, dtype=float), 0.0)
    if result.sum() <= 0:
        return result
    result /= result.sum()
    for _ in range(100):
        over = result > cap + 1e-12
        if not over.any():
            break
        excess = float((result[over] - cap).sum())
        result[over] = cap
        under = ~over
        room = np.maximum(cap - result[under], 0.0)
        if room.sum() <= 0:
            break
        result[under] += excess * room / room.sum()
    return result / result.sum() if result.sum() else result


def build_weight_table(
    catalog: list[dict[str, Any]], coefficients: np.ndarray
) -> list[dict[str, Any]]:
    raw = np.asarray(coefficients, dtype=float).copy()
    if len(raw) != len(catalog):
        raise ValueError("权重系数数量与30个子系统不一致")
    for index, row in enumerate(catalog):
        if row["forced_zero_reason"]:
            raw[index] = 0.0
    raw = np.maximum(raw, 0.0)
    active = np.array([not row["forced_zero_reason"] for row in catalog], dtype=bool)
    if raw[active].sum() <= 0:
        raise ValueError("优化器没有产生有效非零系数")
    normalized = np.zeros_like(raw)
    normalized[active] = _cap_weights(raw[active]) * 100.0
    table = []
    for row, coefficient, weight in zip(catalog, raw, normalized, strict=True):
        table.append(
            {
                **row,
                "coefficient": round(float(coefficient), 10),
                "weight": round(float(weight), 8),
            }
        )
    drift = 100.0 - sum(row["weight"] for row in table)
    if abs(drift) > 1e-8:
        target = max(
            (row for row in table if not row["forced_zero_reason"]),
            key=lambda row: row["weight"],
        )
        target["weight"] = round(target["weight"] + drift, 8)
    return table


def ema(values: np.ndarray, period: int) -> np.ndarray:
    return pd.Series(values, dtype=float).ewm(
        span=period, adjust=False, min_periods=1
    ).mean().to_numpy()


def tdx_sma(values: np.ndarray, period: int, weight: int = 1) -> np.ndarray:
    result = np.empty(len(values), dtype=float)
    if not len(values):
        return result
    result[0] = float(values[0])
    for index in range(1, len(values)):
        result[index] = (
            weight * float(values[index]) + (period - weight) * result[index - 1]
        ) / period
    return result


def rolling(values: np.ndarray, period: int, kind: str) -> np.ndarray:
    series = pd.Series(values, dtype=float)
    if kind == "mean":
        return series.rolling(period, min_periods=1).mean().to_numpy()
    if kind == "max":
        return series.rolling(period, min_periods=1).max().to_numpy()
    if kind == "min":
        return series.rolling(period, min_periods=1).min().to_numpy()
    if kind == "std":
        return series.rolling(period, min_periods=2).std(ddof=0).fillna(0).to_numpy()
    if kind == "sum":
        return series.rolling(period, min_periods=1).sum().to_numpy()
    raise ValueError(kind)


def crosses_up(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    result = np.zeros(len(left), dtype=bool)
    result[1:] = (left[1:] > right[1:]) & (left[:-1] <= right[:-1])
    return result


def crosses_down(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    result = np.zeros(len(left), dtype=bool)
    result[1:] = (left[1:] < right[1:]) & (left[:-1] >= right[:-1])
    return result


def read_day_file(path: Path) -> list[dict[str, Any]]:
    data = path.read_bytes()
    rows: list[dict[str, Any]] = []
    for offset in range(0, len(data), 32):
        block = data[offset : offset + 32]
        if len(block) != 32:
            break
        date_i, open_i, high_i, low_i, close_i, amount, volume, _ = struct.unpack(
            "<IIIIIfII", block
        )
        if date_i <= 0 or min(open_i, high_i, low_i, close_i) <= 0:
            continue
        rows.append(
            {
                "date": str(date_i),
                "open": open_i / 100.0,
                "high": high_i / 100.0,
                "low": low_i / 100.0,
                "close": close_i / 100.0,
                "amount": float(amount),
                "volume": float(volume),
            }
        )
    return rows


def day_path(symbol: str) -> Path:
    code, market = symbol.split(".")
    prefix = market.lower()
    return TDX_ROOT / "vipdoc" / prefix / "lday" / f"{prefix}{code}.day"


def initialize_tq():
    sys.path.insert(0, str(TQ_USER_DIR))
    sys.argv = ["tqcenter", "--run_tdx", "0"]
    from tqcenter import tq

    tq.initialize(str(TQ_INIT_PATH))
    return tq


def market_data_to_bars(
    market_data: dict[str, Any],
    symbols: list[str],
) -> dict[str, list[dict[str, Any]]]:
    fields = {
        "open": market_data.get("Open"),
        "high": market_data.get("High"),
        "low": market_data.get("Low"),
        "close": market_data.get("Close"),
        "volume": market_data.get("Volume"),
        "amount": market_data.get("Amount"),
    }
    if not all(isinstance(value, pd.DataFrame) for value in fields.values()):
        raise ValueError("通达信前复权K线返回字段不完整")
    close_frame = fields["close"]
    result: dict[str, list[dict[str, Any]]] = {}
    for symbol in symbols:
        if any(symbol not in frame.columns for frame in fields.values()):
            continue
        rows: list[dict[str, Any]] = []
        for timestamp in close_frame.index:
            values = {
                name: float(frame.at[timestamp, symbol])
                for name, frame in fields.items()
            }
            # TQ Amount is expressed in 10,000 CNY while .day amount is CNY.
            # Normalize both paths to CNY before applying liquidity constraints.
            values["amount"] *= 10_000.0
            if not all(math.isfinite(value) for value in values.values()):
                continue
            if min(values[name] for name in ("open", "high", "low", "close")) <= 0:
                continue
            rows.append(
                {
                    "date": pd.Timestamp(timestamp).strftime("%Y%m%d"),
                    **values,
                }
            )
        if rows:
            result[symbol] = rows
    return result


def fetch_adjusted_market_history(
    tq,
    symbols: list[str],
    *,
    count: int,
    batch_size: int = 30,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, str]]]:
    bars: dict[str, list[dict[str, Any]]] = {}
    errors: list[dict[str, str]] = []
    for offset in range(0, len(symbols), batch_size):
        batch = symbols[offset : offset + batch_size]
        try:
            payload = tq.get_market_data(
                field_list=["Open", "High", "Low", "Close", "Volume", "Amount"],
                stock_list=batch,
                period="1d",
                count=count,
                dividend_type="front",
                fill_data=True,
            )
            parsed = market_data_to_bars(payload, batch)
            minimum_records = max(1, int(math.ceil(count * 0.98)))
            for symbol in batch:
                if len(parsed.get(symbol, [])) >= minimum_records:
                    continue
                try:
                    retry_payload = tq.get_market_data(
                        field_list=["Open", "High", "Low", "Close", "Volume", "Amount"],
                        stock_list=[symbol],
                        period="1d",
                        count=count,
                        dividend_type="front",
                        fill_data=True,
                    )
                    retry_parsed = market_data_to_bars(retry_payload, [symbol])
                    if len(retry_parsed.get(symbol, [])) < minimum_records:
                        raise RuntimeError(
                            f"adjusted_history_short:{len(retry_parsed.get(symbol, []))}"
                        )
                    parsed[symbol] = retry_parsed[symbol]
                except Exception as exc:
                    errors.append(
                        {
                            "symbol": symbol,
                            "error": f"front_adjusted_individual_retry:{type(exc).__name__}:{exc}",
                        }
                    )
            bars.update(parsed)
            for symbol in batch:
                if symbol not in parsed and not any(
                    row.get("symbol") == symbol for row in errors
                ):
                    errors.append(
                        {
                            "symbol": symbol,
                            "error": "front_adjusted_market_data_missing",
                        }
                    )
        except Exception as exc:
            for symbol in batch:
                errors.append(
                    {
                        "symbol": symbol,
                        "error": f"front_adjusted_market_data:{type(exc).__name__}:{exc}",
                    }
                )
        print(
            json.dumps(
                {
                    "前复权K线": min(offset + len(batch), len(symbols)),
                    "总数": len(symbols),
                    "错误": len(errors),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
            flush=True,
        )
    return bars, errors


def formula_dates(node: dict[str, Any], fields: tuple[str, ...]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for field in fields:
        items = node.get(field)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            date = "".join(ch for ch in str(item.get("Date") or "") if ch.isdigit())[:8]
            if len(date) != 8:
                continue
            result.setdefault(date, {})[field] = safe_float(item.get("Value"))
    return result


def fetch_formula_history(
    tq,
    formula: str,
    symbols: list[str],
    fields: tuple[str, ...],
    count: int,
    dividend_type: int,
    batch_size: int,
) -> tuple[dict[str, dict[str, dict[str, float]]], list[dict[str, str]]]:
    maps: dict[str, dict[str, dict[str, float]]] = {}
    errors: list[dict[str, str]] = []
    for offset in range(0, len(symbols), batch_size):
        batch = symbols[offset : offset + batch_size]
        try:
            payload = tq.formula_process_mul_zb(
                formula,
                stock_list=batch,
                count=0,
                return_count=count,
                return_date=True,
                dividend_type=dividend_type,
            )
            if not isinstance(payload, dict) or str(payload.get("ErrorId")) not in {"0", "19"}:
                raise RuntimeError(str(payload)[:500])
            for symbol in batch:
                node = payload.get(symbol)
                if not isinstance(node, dict):
                    try:
                        retry_payload = tq.formula_process_mul_zb(
                            formula,
                            stock_list=[symbol],
                            count=0,
                            return_count=count,
                            return_date=True,
                            dividend_type=dividend_type,
                        )
                        retry_node = (
                            retry_payload.get(symbol)
                            if isinstance(retry_payload, dict)
                            and str(retry_payload.get("ErrorId")) in {"0", "19"}
                            else None
                        )
                        if not isinstance(retry_node, dict):
                            raise RuntimeError("missing_node_after_individual_retry")
                        maps[symbol] = formula_dates(retry_node, fields)
                    except Exception as exc:
                        errors.append(
                            {
                                "formula": formula,
                                "symbol": symbol,
                                "error": f"individual_retry:{type(exc).__name__}:{exc}",
                            }
                        )
                    continue
                maps[symbol] = formula_dates(node, fields)
        except Exception as exc:
            for symbol in batch:
                errors.append(
                    {
                        "formula": formula,
                        "symbol": symbol,
                        "error": f"{type(exc).__name__}:{exc}",
                    }
                )
        print(
            json.dumps(
                {
                    "公式": formula,
                    "已处理": min(offset + len(batch), len(symbols)),
                    "总数": len(symbols),
                    "错误": len(errors),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
            flush=True,
        )
    return maps, errors


def fetch_dealer_history_official(
    tq,
    symbols: list[str],
    bars: dict[str, list[dict[str, Any]]],
    fields: tuple[str, ...],
    count: int,
) -> tuple[dict[str, dict[str, dict[str, float]]], list[dict[str, str]]]:
    maps: dict[str, dict[str, dict[str, float]]] = {}
    errors: list[dict[str, str]] = []
    for index, symbol in enumerate(symbols, start=1):
        try:
            setup = tq.formula_set_data_info(
                symbol,
                count=count,
                dividend_type=1,
            )
            if not isinstance(setup, dict) or str(setup.get("ErrorId")) != "0":
                raise RuntimeError(f"formula_set_data_info:{setup}")
            result = tq.formula_zb(
                DEALER_FORMULA,
                symbol.split(".", 1)[0],
                xsflag=2,
            )
            if not isinstance(result, dict) or str(result.get("ErrorId")) != "0":
                raise RuntimeError(f"formula_zb:{result}")
            values = result.get("Value")
            if not isinstance(values, dict):
                raise RuntimeError("formula_value_empty")
            dates = [row["date"] for row in bars[symbol]][-count:]
            field_values: dict[str, list[Any]] = {}
            for field in fields:
                series = values.get(field)
                if not isinstance(series, list) or len(series) != len(dates):
                    raise RuntimeError(
                        f"field_length_mismatch:{field}:"
                        f"{len(series) if isinstance(series, list) else -1}:"
                        f"{len(dates)}"
                    )
                field_values[field] = series
            maps[symbol] = {
                date: {
                    field: safe_float(field_values[field][offset])
                    for field in fields
                }
                for offset, date in enumerate(dates)
            }
        except Exception as exc:
            errors.append(
                {
                    "formula": DEALER_FORMULA,
                    "symbol": symbol,
                    "error": f"{type(exc).__name__}:{exc}",
                }
            )
        if index % 10 == 0 or index == len(symbols):
            print(
                json.dumps(
                    {
                        "公式": DEALER_FORMULA,
                        "已处理": index,
                        "总数": len(symbols),
                        "错误": len(errors),
                        "接口": "formula_set_data_info+formula_zb",
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
                flush=True,
            )
    return maps, errors


def formula_feature_arrays(
    symbol: str,
    records: list[dict[str, Any]],
    big_map: dict[str, dict[str, float]],
    feilong_map: dict[str, dict[str, float]],
    dealer_map: dict[str, dict[str, float]],
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    dates = np.array([row["date"] for row in records])
    open_ = np.array([row["open"] for row in records], dtype=float)
    high = np.array([row["high"] for row in records], dtype=float)
    low = np.array([row["low"] for row in records], dtype=float)
    close = np.array([row["close"] for row in records], dtype=float)
    volume = np.array([row["volume"] for row in records], dtype=float)
    amount = np.array([row["amount"] for row in records], dtype=float)
    size = len(records)

    def mapped(source: dict[str, dict[str, float]], field: str) -> np.ndarray:
        return np.array(
            [safe_float(source.get(date, {}).get(field)) for date in dates],
            dtype=float,
        )

    main_trend_tq = mapped(big_map, "主趋势线")
    main_trend = np.where(
        np.isfinite(main_trend_tq), main_trend_tq, ema(ema(close, 10), 10)
    )
    ema5 = ema(close, 5)
    ema10 = ema(close, 10)
    ema20 = ema(close, 20)
    ema173 = ema(close, 173)
    ema193 = ema(close, 193)
    ema213 = ema(close, 213)
    mtm = np.r_[0.0, np.diff(close)]
    dx_num = ema(ema(mtm, 6), 6)
    dx_den = ema(ema(np.abs(mtm), 6), 6)
    dx = np.divide(100.0 * dx_num, dx_den, out=np.zeros(size), where=dx_den != 0)
    dx_ma2 = rolling(dx, 2, "mean")
    buy = (
        (dx <= rolling(dx, 7, "min") + 1e-9)
        & (rolling((dx < 0).astype(float), 2, "sum") >= 1)
        & crosses_up(dx, dx_ma2)
    )
    sell = (
        (dx >= rolling(dx, 7, "max") - 1e-9)
        & (rolling((dx > 50).astype(float), 2, "sum") >= 1)
        & crosses_down(dx, dx_ma2)
    )
    vaw1 = ema(ema(close, 13), 13)
    previous_vaw1 = np.r_[np.nan, vaw1[:-1]]
    control = np.divide(
        (vaw1 - previous_vaw1) * 1000.0,
        previous_vaw1,
        out=np.zeros(size),
        where=np.isfinite(previous_vaw1) & (previous_vaw1 != 0),
    )
    cai = (ema(close, 8) - ema(close, 21)) * 50.0
    shen = ema(cai, 3)
    change = np.divide(
        close,
        np.r_[np.nan, close[:-1]],
        out=np.ones(size),
        where=np.r_[False, close[:-1] != 0],
    ) - 1.0
    volume_ratio = np.divide(
        volume,
        np.r_[np.nan, volume[:-1]],
        out=np.ones(size),
        where=np.r_[False, volume[:-1] != 0],
    )
    limit_threshold = 0.195 if symbol.startswith(("300", "301", "688")) else 0.095
    is_limit = change >= limit_threshold
    leader_zone = np.where(
        (change >= 0.099) & (volume_ratio < 1.0),
        1.0,
        np.where((change >= 0.07) & (volume_ratio < 1.0), 0.7, 0.0),
    )

    gains = np.maximum(np.r_[0.0, np.diff(close)], 0.0)
    moves = np.abs(np.r_[0.0, np.diff(close)])
    operation = np.divide(
        tdx_sma(gains, 2),
        tdx_sma(moves, 2),
        out=np.zeros(size),
        where=tdx_sma(moves, 2) != 0,
    ) * 100.0
    pp45 = crosses_down(operation, np.full(size, 45.0))
    pp20 = crosses_down(operation, np.full(size, 20.0))
    recent_limit13 = rolling(is_limit.astype(float), 13, "sum") >= 1
    smooth_low = tdx_sma(low, 4, 3)
    dragon = np.zeros(size, dtype=bool)
    dragon[1:] = (
        np.isfinite(smooth_low[1:])
        & (pp45[:-1] | pp20[:-1])
        & recent_limit13[1:]
    )
    ema3 = ema(close, 3)
    ema21 = ema(close, 21)
    ignition = crosses_up(ema3, ema21)

    lowest150 = rolling(low, 150, "min")
    highest150 = rolling(high, 150, "max")
    rsv_den = highest150 - lowest150
    rsv = np.divide(
        close - lowest150,
        rsv_den,
        out=np.zeros(size),
        where=rsv_den != 0,
    ) * 100.0
    kdj_k = tdx_sma(rsv, 3)
    kdj_d = tdx_sma(kdj_k, 3)
    kdj_j = 3 * kdj_k - 2 * kdj_d
    kdj_cross = (kdj_k > kdj_d) & (kdj_j > kdj_d) & (kdj_j > kdj_k)
    theme_resonance = kdj_cross & is_limit & (close >= high - 1e-9)

    three_day_drop = np.zeros(size, dtype=bool)
    three_day_drop[3:] = (close[:-3] - close[3:]) / close[:-3] > 0.05
    bars_since_drop = np.full(size, 10_000, dtype=int)
    latest_drop = -10_000
    for index, flag in enumerate(three_day_drop):
        if flag:
            latest_drop = index
        bars_since_drop[index] = index - latest_drop
    drop_high = np.full(size, np.nan)
    for index, elapsed in enumerate(bars_since_drop):
        anchor = index - elapsed
        if anchor >= 0:
            candidates = high[max(0, anchor - 2) : anchor + 1]
            if len(candidates):
                drop_high[index] = float(np.max(candidates))
    recent_low = rolling(low, 150, "min")
    violent_profit = (
        (change > 0.05)
        & (bars_since_drop < 150)
        & np.isfinite(drop_high)
        & ((open_ - drop_high) / np.maximum(drop_high, 0.01) < 0.30)
        & ((close - recent_low) / np.maximum(recent_low, 0.01) < 0.50)
        & (volume / np.maximum(rolling(volume, 5, "mean"), 1.0) < 3.5)
    )
    boll = rolling(close, 20, "mean")
    boll_std = rolling(close, 20, "std")
    boll_z = np.divide(
        close - boll,
        2.0 * boll_std,
        out=np.zeros(size),
        where=boll_std != 0,
    )
    ma30 = rolling(close, 30, "mean")
    ma54 = rolling(close, 54, "mean")
    ma60 = rolling(close, 60, "mean")
    ma120 = rolling(close, 120, "mean")
    deviation = ((close - ma54) / np.maximum(ma54, 0.01) < 0.1) & (
        (close - ema10) / np.maximum(ema10, 0.01) < 0.3
    )
    platform_break = np.zeros(size, dtype=bool)
    if size > 10:
        prior_ten = rolling(deviation.astype(float), 10, "sum")
        platform_break[1:] = (~deviation[1:]) & deviation[:-1] & (prior_ten[:-1] >= 10)
    fliga = (
        ((volume_ratio > 1.2) & (close > open_))
        | ((low > np.r_[np.nan, high[:-1]]) & (open_ > close) & (volume_ratio > 1.2))
    )
    yaogu = (
        (violent_profit | platform_break)
        & (change > 0.095)
        & fliga
        & (change > 0.05)
        & (close / np.maximum(open_, 0.01) > 1.05)
    )
    ma_strength = np.mean(
        np.vstack(
            [
                close > ema5,
                close > ema10,
                close > ema20,
                close > ma30,
                close > ma54,
                close > ma60,
                close > ma120,
            ]
        ),
        axis=0,
    )

    supports = np.vstack([mapped(big_map, "支撑一"), mapped(big_map, "支撑二")])
    pressures = np.vstack([mapped(big_map, "压力一"), mapped(big_map, "压力二")])
    support_distance = np.full(size, np.nan)
    pressure_distance = np.full(size, np.nan)
    for index in range(size):
        valid_supports = supports[:, index]
        valid_supports = valid_supports[
            np.isfinite(valid_supports) & (valid_supports > 0) & (valid_supports < close[index])
        ]
        valid_pressures = pressures[:, index]
        valid_pressures = valid_pressures[
            np.isfinite(valid_pressures) & (valid_pressures > close[index])
        ]
        if len(valid_supports):
            support_distance[index] = (close[index] - valid_supports.max()) / close[index]
        if len(valid_pressures):
            pressure_distance[index] = (valid_pressures.min() - close[index]) / close[index]
    support_pressure = np.log1p(
        np.divide(
            pressure_distance,
            support_distance + 0.005,
            out=np.zeros(size),
            where=np.isfinite(pressure_distance) & np.isfinite(support_distance),
        )
    )

    dnx_o4 = mapped(big_map, "OUTPUT4")
    dnx_o6 = mapped(big_map, "OUTPUT6")
    dnx_o9 = mapped(big_map, "OUTPUT9")
    fl_o3 = mapped(feilong_map, "OUTPUT3")
    fl_o4 = mapped(feilong_map, "OUTPUT4")
    fl_o5 = mapped(feilong_map, "OUTPUT5")
    fl_o6 = mapped(feilong_map, "OUTPUT6")
    wave = mapped(feilong_map, "波")
    segment = mapped(feilong_map, "段")

    high_ema13x3 = ema(ema(ema(high, 13), 13), 13)
    high_ema5x3 = ema(ema(ema(high, 5), 5), 5)
    ema89 = ema(close, 89)
    first_limit = is_limit & ~np.r_[False, is_limit[:-1]] & ~np.r_[False, False, is_limit[:-2]]
    trend_filter = (
        (np.arange(size) >= 120)
        & (not symbol.startswith("3"))
        & (close > ema89)
        & (close > high_ema13x3)
        & (close > high_ema5x3)
        & (high / np.maximum(high_ema5x3, 0.01) < 1.16)
        & first_limit
    )
    body_high = np.maximum(open_, close)
    body_low = np.minimum(open_, close)
    four_low_high = rolling(body_high, 4, "min")
    four_high_low = rolling(body_low, 4, "max")
    box_today = four_high_low <= four_low_high
    box_recent = rolling(box_today.astype(float), 36, "max") > 0
    unique_limit = is_limit & (rolling(is_limit.astype(float), 21, "sum") == 1)
    fl_main_rise = (
        ((fl_o5 >= 99) | (fl_o6 >= 99))
        & ((fl_o3 >= 99) | (fl_o4 >= 99))
    )
    dealer_high35 = rolling(high, 35, "max")
    dealer_low35 = rolling(low, 35, "min")
    dealer_range35 = dealer_high35 - dealer_low35
    dealer_b1 = np.divide(
        dealer_high35 - close,
        dealer_range35,
        out=np.zeros(size),
        where=dealer_range35 != 0,
    ) * 100.0
    dealer_b2 = tdx_sma(dealer_b1, 35) + 100.0
    dealer_b3 = np.divide(
        close - dealer_low35,
        dealer_range35,
        out=np.zeros(size),
        where=dealer_range35 != 0,
    ) * 100.0
    dealer_b4 = tdx_sma(dealer_b3, 7)
    dealer_b5 = tdx_sma(dealer_b4, 5) + 100.0
    dealer_b6 = dealer_b5 - dealer_b2

    features = {
        "dnx_main_trend": np.divide(close, main_trend, out=np.ones(size), where=main_trend != 0)
        - 1.0
        + np.r_[0.0, np.diff(main_trend)] / np.maximum(main_trend, 0.01),
        "dnx_ema_layers": (
            (ema5 > ema10).astype(float)
            + (ema10 > ema20).astype(float)
            + (close > ema173).astype(float)
            + (ema173 > ema193).astype(float)
            + (ema193 > ema213).astype(float)
        )
        / 5.0,
        "dnx_k_color": (ema5 > ema20).astype(float),
        "dnx_float_cap": mapped(big_map, "流通市值"),
        "dnx_dx": dx + np.r_[0.0, np.diff(dx)],
        "dnx_participation_exit": buy.astype(float) - sell.astype(float),
        "dnx_control": control,
        "dnx_caishen": cai - shen,
        "dnx_dealer_in_out": (dnx_o4 > 0).astype(float) - (dnx_o6 > 0).astype(float),
        "dnx_yaogu": yaogu.astype(float),
        "dnx_leader_zone": leader_zone,
        "dnx_dragon_pullback": dragon.astype(float),
        "dnx_ignition": np.maximum(ignition.astype(float), (dnx_o9 > 0).astype(float)),
        "dnx_theme_resonance": theme_resonance.astype(float),
        "dnx_boll_ma": np.clip(boll_z, -2, 2) + ma_strength,
        "dnx_support_pressure": support_pressure,
        "fl_dragon": (fl_o3 >= 99).astype(float),
        "fl_trend_filter": trend_filter.astype(float),
        "fl_box": (box_today | box_recent).astype(float),
        "fl_unique_limit": unique_limit.astype(float),
        "fl_board": (fl_o4 >= 99).astype(float),
        "fl_surge": (fl_o5 >= 99).astype(float),
        "fl_wave": wave + np.r_[0.0, np.diff(np.nan_to_num(wave, nan=0.0))],
        "fl_segment": segment + np.r_[0.0, np.diff(np.nan_to_num(segment, nan=0.0))],
        "fl_private": (fl_o6 >= 99).astype(float),
        "fl_main_rise": fl_main_rise.astype(float),
        "zj_cost_pressure": dealer_b2,
        "zj_fund_strength": dealer_b5,
        "zj_control_spread": dealer_b6,
        "zj_control_degree": np.maximum(dealer_b6 - 3.0, 0.0) * 3.5,
    }
    market = {
        "date": dates,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "amount": amount,
    }
    return features, market


def assess_entry_tradability(
    symbol: str,
    records: list[dict[str, Any]],
    *,
    signal_date: str,
    market_calendar: list[str],
    minimum_amount: float,
) -> dict[str, Any]:
    """Resolve a signal to the exact next market session and audit entry feasibility."""
    calendar = [str(value) for value in market_calendar]
    try:
        signal_calendar_index = calendar.index(str(signal_date))
    except ValueError:
        return {"tradable": False, "reason": "signal_date_not_in_market_calendar"}
    if signal_calendar_index + 1 >= len(calendar):
        return {"tradable": False, "reason": "entry_session_not_available"}

    record_index = {str(row.get("date", "")): index for index, row in enumerate(records)}
    signal_index = record_index.get(str(signal_date))
    entry_date = calendar[signal_calendar_index + 1]
    entry_index = record_index.get(entry_date)
    if signal_index is None:
        return {"tradable": False, "reason": "signal_session_bar_missing"}
    if entry_index is None:
        return {
            "tradable": False,
            "reason": "entry_session_bar_missing",
            "entry_date": entry_date,
        }

    signal_bar = records[signal_index]
    entry_bar = records[entry_index]
    volume = safe_float(entry_bar.get("volume"))
    amount = safe_float(entry_bar.get("amount"))
    if volume <= 0 or amount < max(0.0, float(minimum_amount)):
        return {
            "tradable": False,
            "reason": "entry_session_insufficient_liquidity",
            "entry_date": entry_date,
            "entry_index": entry_index,
        }

    prior_close = safe_float(signal_bar.get("close"))
    entry_open = safe_float(entry_bar.get("open"))
    entry_high = safe_float(entry_bar.get("high"))
    entry_low = safe_float(entry_bar.get("low"))
    entry_close = safe_float(entry_bar.get("close"))
    if min(prior_close, entry_open, entry_high, entry_low, entry_close) <= 0:
        return {
            "tradable": False,
            "reason": "entry_session_price_invalid",
            "entry_date": entry_date,
            "entry_index": entry_index,
        }
    price_tolerance = max(1e-8, abs(entry_close) * 1e-6)
    one_price = abs(entry_high - entry_low) <= price_tolerance
    open_change = entry_open / prior_close - 1.0
    # A 4.8% conservative floor catches historical ST 5% limits as well as
    # ordinary 10% and registration-board 20% one-price limit-ups.
    if one_price and open_change >= 0.048:
        return {
            "tradable": False,
            "reason": "entry_session_one_price_limit_up",
            "entry_date": entry_date,
            "entry_index": entry_index,
        }
    return {
        "tradable": True,
        "reason": "tradable",
        "entry_date": entry_date,
        "entry_index": entry_index,
    }


def build_observations(
    symbols: list[str],
    bars: dict[str, list[dict[str, Any]]],
    big_maps: dict[str, dict[str, dict[str, float]]],
    feilong_maps: dict[str, dict[str, dict[str, float]]],
    dealer_maps: dict[str, dict[str, dict[str, float]]],
    count: int,
    rebalance_days: int,
    cost_bps: float,
    minimum_entry_amount: float = 10_000_000.0,
) -> tuple[pd.DataFrame, list[dict[str, str]], dict[str, Any]]:
    catalog = subsystem_catalog()
    feature_keys = [row["key"] for row in catalog]
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    market_calendar = sorted(
        {
            str(record.get("date", ""))
            for records in bars.values()
            for record in records
            if record.get("date")
        }
    )
    excluded_by_reason: dict[str, int] = {}
    evaluated_entries = 0
    for symbol in symbols:
        try:
            records = bars[symbol]
            features, market = formula_feature_arrays(
                symbol,
                records,
                big_maps[symbol],
                feilong_maps[symbol],
                dealer_maps[symbol],
            )
            allowed_dates = set(sorted(big_maps[symbol])[-count:])
            date_index = {date: index for index, date in enumerate(market["date"])}
            common_dates = sorted(
                allowed_dates
                & set(feilong_maps[symbol])
                & set(dealer_maps[symbol])
                & set(date_index)
            )
            for date in common_dates:
                index = date_index[date]
                if index < 220:
                    continue
                evaluated_entries += 1
                entry_audit = assess_entry_tradability(
                    symbol,
                    records,
                    signal_date=date,
                    market_calendar=market_calendar,
                    minimum_amount=minimum_entry_amount,
                )
                if not entry_audit["tradable"]:
                    reason = str(entry_audit["reason"])
                    excluded_by_reason[reason] = excluded_by_reason.get(reason, 0) + 1
                    continue
                entry_index = int(entry_audit["entry_index"])
                if entry_index + 9 >= len(records):
                    excluded_by_reason["forward_horizon_incomplete"] = (
                        excluded_by_reason.get("forward_horizon_incomplete", 0) + 1
                    )
                    continue
                entry = market["open"][entry_index]
                if not math.isfinite(entry) or entry <= 0:
                    excluded_by_reason["entry_session_price_invalid"] = (
                        excluded_by_reason.get("entry_session_price_invalid", 0) + 1
                    )
                    continue
                result: dict[str, Any] = {"symbol": symbol, "date": date}
                for key in feature_keys:
                    result[key] = safe_float(features[key][index])
                future_returns = {}
                for horizon in (3, 5, 10):
                    exit_close = market["close"][entry_index + horizon - 1]
                    future_returns[horizon] = exit_close / entry - 1.0 - cost_bps / 10000.0
                    result[f"return_{horizon}d"] = future_returns[horizon]
                next_five = slice(entry_index, entry_index + 5)
                result["mfe_5d"] = (
                    float(np.max(market["high"][next_five])) / entry - 1.0
                )
                result["mae_5d"] = (
                    float(np.min(market["low"][next_five])) / entry - 1.0
                )
                result["target"] = (
                    0.25 * future_returns[3]
                    + 0.35 * future_returns[5]
                    + 0.40 * future_returns[10]
                    + 0.10 * result["mfe_5d"]
                    - 0.20 * abs(min(result["mae_5d"], 0.0))
                )
                rows.append(result)
        except Exception as exc:
            errors.append(
                {"symbol": symbol, "error": f"{type(exc).__name__}:{exc}"}
            )
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("没有构建出可回测样本")
    selected_dates = global_rebalance_dates(
        frame,
        stock_count=len(symbols),
        rebalance_days=rebalance_days,
        minimum_fraction=0.7,
    )
    frame = frame[frame["date"].isin(selected_dates)].reset_index(drop=True)
    if frame.empty:
        raise RuntimeError("统一再平衡日期后没有可回测样本")
    audit = {
        "policy": "exact_next_market_session_positive_liquidity_and_no_one_price_limit_up",
        "minimum_entry_amount": float(minimum_entry_amount),
        "evaluated_entries": evaluated_entries,
        "included_entries_before_rebalance_filter": len(rows),
        "excluded_by_reason": excluded_by_reason,
        "checks": {
            "exact_next_market_session_entry": True,
            "positive_volume_and_amount": True,
            "one_price_limit_up_excluded": True,
            "historical_st_status_available": False,
        },
        "complete": False,
        "incomplete_reason": "本机数据未提供逐日历史ST身份快照，完整可交易性保持失败关闭",
    }
    return frame, errors, audit


def apply_information_constraints(
    frame: pd.DataFrame,
    catalog: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    audited = [dict(row) for row in catalog]
    total_dates = int(frame["date"].nunique())
    required_dates = max(5, int(math.ceil(total_dates * 0.6)))
    diagnostics: dict[str, dict[str, Any]] = {}
    for row in audited:
        key = row["key"]
        numeric = pd.to_numeric(frame[key], errors="coerce")
        finite = np.isfinite(numeric.to_numpy(dtype=float))
        coverage = float(finite.mean()) if len(finite) else 0.0
        informative_dates = 0
        for _, indexes in frame.groupby("date").groups.items():
            values = numeric.loc[indexes]
            values = values[np.isfinite(values.to_numpy(dtype=float))]
            if len(values) >= 20 and values.nunique(dropna=True) > 1:
                informative_dates += 1
        diagnostics[key] = {
            "coverage": round(coverage, 8),
            "informative_dates": informative_dates,
            "total_dates": total_dates,
            "required_informative_dates": required_dates,
        }
        if row["forced_zero_reason"]:
            continue
        if coverage < 0.8:
            row["forced_zero_reason"] = (
                f"历史有效值覆盖率不足（{coverage:.2%}）"
            )
        elif informative_dates < required_dates:
            row["forced_zero_reason"] = (
                f"历史样本无横截面区分度（"
                f"{informative_dates}/{total_dates}个有效日期）"
            )
    return audited, diagnostics


def normalize_backtest_features(
    frame: pd.DataFrame,
    catalog: list[dict[str, Any]],
) -> pd.DataFrame:
    normalized = frame.copy()
    for row in catalog:
        key = row["key"]
        normalized[key] = normalized.groupby("date")[key].transform(
            lambda series: pd.Series(
                percentile_scores(series.to_numpy(dtype=float)) / 100.0,
                index=series.index,
            )
        )
    return normalized


def prepare_backtest_frame(
    raw_frame: pd.DataFrame,
    catalog: list[dict[str, Any]],
    *,
    purge_dates: int = 2,
) -> tuple[
    pd.DataFrame,
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, np.ndarray],
]:
    split = chronological_split(
        raw_frame["date"].to_numpy(),
        purge_dates=purge_dates,
    )
    audited, diagnostics = apply_information_constraints(
        raw_frame.loc[split["train"]].reset_index(drop=True),
        catalog,
    )
    return normalize_backtest_features(raw_frame, audited), audited, diagnostics, split


def build_current_feature_frame(
    symbols: list[str],
    bars: dict[str, list[dict[str, Any]]],
    big_maps: dict[str, dict[str, dict[str, float]]],
    feilong_maps: dict[str, dict[str, dict[str, float]]],
    dealer_maps: dict[str, dict[str, dict[str, float]]],
    count: int,
) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    feature_keys = [row["key"] for row in subsystem_catalog()]
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for symbol in symbols:
        try:
            features, market = formula_feature_arrays(
                symbol,
                bars[symbol],
                big_maps[symbol],
                feilong_maps[symbol],
                dealer_maps[symbol],
            )
            allowed_dates = set(sorted(big_maps[symbol])[-count:])
            date_index = {date: index for index, date in enumerate(market["date"])}
            common_dates = sorted(
                allowed_dates
                & set(feilong_maps[symbol])
                & set(dealer_maps[symbol])
                & set(date_index)
            )
            for date in common_dates:
                index = date_index[date]
                if index < 220:
                    continue
                result: dict[str, Any] = {"symbol": symbol, "date": date}
                for key in feature_keys:
                    result[key] = safe_float(features[key][index])
                rows.append(result)
        except Exception as exc:
            errors.append(
                {"symbol": symbol, "error": f"{type(exc).__name__}:{exc}"}
            )
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("没有构建出当前评分特征")
    return frame, errors


def global_rebalance_dates(
    frame: pd.DataFrame,
    stock_count: int,
    rebalance_days: int,
    minimum_fraction: float = 0.7,
) -> list[str]:
    minimum_count = max(50, int(math.ceil(stock_count * minimum_fraction)))
    counts = frame.groupby("date")["symbol"].nunique().sort_index()
    eligible = [
        str(date)
        for date, count in counts.items()
        if int(count) >= minimum_count
    ]
    return eligible[::rebalance_days]


def _mean_ic(frame: pd.DataFrame, prediction: np.ndarray) -> float:
    work = frame[["date", "target"]].copy()
    work["prediction"] = prediction
    values = []
    for _, group in work.groupby("date"):
        if len(group) < 20 or group["prediction"].nunique() < 2:
            continue
        value = spearmanr(group["prediction"], group["target"]).statistic
        if math.isfinite(value):
            values.append(float(value))
    return float(np.mean(values)) if values else 0.0


def _max_drawdown(returns: list[float]) -> float:
    if not returns:
        return 0.0
    equity = np.cumprod(1.0 + np.asarray(returns, dtype=float))
    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1.0
    return float(drawdown.min())


def newey_west_mean_statistics(
    values: list[float] | np.ndarray,
    max_lag: int | None = None,
) -> dict[str, Any]:
    sample = np.asarray(values, dtype=float)
    sample = sample[np.isfinite(sample)]
    count = len(sample)
    if count == 0:
        return {
            "count": 0,
            "mean": 0.0,
            "standard_error": None,
            "t_stat": None,
            "ci95_lower": None,
            "ci95_upper": None,
            "max_lag": 0,
        }
    mean = float(sample.mean())
    centered = sample - mean
    lag = (
        max(0, int(4 * (count / 100.0) ** (2.0 / 9.0)))
        if max_lag is None
        else max(0, min(int(max_lag), count - 1))
    )
    long_run_variance = float(np.dot(centered, centered) / count)
    for step in range(1, lag + 1):
        covariance = float(np.dot(centered[step:], centered[:-step]) / count)
        long_run_variance += 2.0 * (1.0 - step / (lag + 1.0)) * covariance
    standard_error = math.sqrt(max(long_run_variance, 0.0) / count)
    if standard_error <= 1e-15:
        t_stat = None if abs(mean) <= 1e-15 else math.copysign(math.inf, mean)
        lower = upper = mean
    else:
        t_stat = mean / standard_error
        lower = mean - 1.96 * standard_error
        upper = mean + 1.96 * standard_error
    return {
        "count": count,
        "mean": round(mean, 10),
        "standard_error": round(standard_error, 10),
        "t_stat": None if t_stat is None else round(float(t_stat), 8),
        "ci95_lower": round(lower, 10),
        "ci95_upper": round(upper, 10),
        "max_lag": lag,
    }


def evaluate_predictions(frame: pd.DataFrame, prediction: np.ndarray) -> dict[str, Any]:
    work = frame[["date", "symbol", "target", "return_3d", "return_5d", "return_10d"]].copy()
    work["score"] = prediction
    selected_rows = []
    date_metrics = []
    for date, group in work.groupby("date"):
        group = group.sort_values(["score", "symbol"], ascending=[False, True])
        take = max(5, int(math.ceil(len(group) * 0.10)))
        selected = group.head(take)
        selected_rows.append(selected)
        date_ic = 0.0
        if len(group) >= 20 and group["score"].nunique() > 1:
            statistic = spearmanr(group["score"], group["target"]).statistic
            if math.isfinite(statistic):
                date_ic = float(statistic)
        date_metrics.append(
            {
                "date": date,
                "universe_count": len(group),
                "selected_count": len(selected),
                "selected_3d": float(selected["return_3d"].mean()),
                "selected_5d": float(selected["return_5d"].mean()),
                "selected_10d": float(selected["return_10d"].mean()),
                "universe_3d": float(group["return_3d"].mean()),
                "universe_5d": float(group["return_5d"].mean()),
                "universe_10d": float(group["return_10d"].mean()),
                "date_ic": date_ic,
                "excess_5d": float(
                    selected["return_5d"].mean() - group["return_5d"].mean()
                ),
                "excess_10d": float(
                    selected["return_10d"].mean() - group["return_10d"].mean()
                ),
            }
        )
    selected = pd.concat(selected_rows, ignore_index=True) if selected_rows else pd.DataFrame()
    metrics = pd.DataFrame(date_metrics)
    if metrics.empty:
        raise RuntimeError("没有可评估的横截面日期")
    return {
        "observations": int(len(work)),
        "rebalance_dates": int(len(metrics)),
        "median_cross_section": int(metrics["universe_count"].median()),
        "minimum_cross_section": int(metrics["universe_count"].min()),
        "mean_ic": round(_mean_ic(frame, prediction), 8),
        "top_decile": {
            horizon: {
                "mean_return": round(float(metrics[f"selected_{horizon}"].mean()), 8),
                "universe_return": round(float(metrics[f"universe_{horizon}"].mean()), 8),
                "excess_return": round(
                    float(
                        (
                            metrics[f"selected_{horizon}"]
                            - metrics[f"universe_{horizon}"]
                        ).mean()
                    ),
                    8,
                ),
                "hit_rate": round(
                    float((metrics[f"selected_{horizon}"] > 0).mean()), 8
                ),
            }
            for horizon in ("3d", "5d", "10d")
        },
        "max_drawdown_5d_sequence": round(
            _max_drawdown(metrics["selected_5d"].tolist()), 8
        ),
        "statistical_tests": {
            "mean_ic": newey_west_mean_statistics(metrics["date_ic"].tolist()),
            "excess_5d": newey_west_mean_statistics(metrics["excess_5d"].tolist()),
            "excess_10d": newey_west_mean_statistics(metrics["excess_10d"].tolist()),
        },
        "selected_rows": selected.to_dict("records"),
        "date_metrics": date_metrics,
    }


def _prediction_objective(metrics: dict[str, Any]) -> float:
    return float(
        metrics["mean_ic"]
        + 3.0 * metrics["top_decile"]["5d"]["excess_return"]
        + 2.0 * metrics["top_decile"]["10d"]["excess_return"]
    )


def temporal_validation_robustness(
    frame: pd.DataFrame,
    prediction: np.ndarray,
    benchmark_prediction: np.ndarray,
    *,
    segments: int = 3,
) -> dict[str, Any]:
    """Require candidate superiority and positive economics in every time segment."""
    candidate_values = np.asarray(prediction, dtype=float)
    benchmark_values = np.asarray(benchmark_prediction, dtype=float)
    if len(frame) != len(candidate_values) or len(frame) != len(benchmark_values):
        raise ValueError("验证框架与候选/基准预测长度不一致")
    if segments < 2:
        raise ValueError("时间稳定性分段数必须不少于2")
    unique_dates = np.array(sorted(frame["date"].astype(str).unique()))
    date_segments = [part for part in np.array_split(unique_dates, segments) if len(part)]
    rows: list[dict[str, Any]] = []
    for index, dates in enumerate(date_segments, start=1):
        mask = frame["date"].astype(str).isin(dates).to_numpy()
        segment_frame = frame.loc[mask].reset_index(drop=True)
        candidate_metrics = evaluate_predictions(segment_frame, candidate_values[mask])
        benchmark_metrics = evaluate_predictions(segment_frame, benchmark_values[mask])
        candidate_objective = _prediction_objective(candidate_metrics)
        benchmark_objective = _prediction_objective(benchmark_metrics)
        passed = (
            candidate_metrics["mean_ic"] > 0
            and candidate_metrics["top_decile"]["5d"]["excess_return"] > 0
            and candidate_metrics["top_decile"]["10d"]["excess_return"] > 0
            and candidate_objective > benchmark_objective + 1e-6
        )
        rows.append(
            {
                "segment": index,
                "start": str(dates[0]),
                "end": str(dates[-1]),
                "dates": len(dates),
                "candidate_mean_ic": candidate_metrics["mean_ic"],
                "candidate_5d_excess": candidate_metrics["top_decile"]["5d"]["excess_return"],
                "candidate_10d_excess": candidate_metrics["top_decile"]["10d"]["excess_return"],
                "candidate_objective": round(candidate_objective, 10),
                "benchmark_objective": round(benchmark_objective, 10),
                "objective_advantage": round(
                    candidate_objective - benchmark_objective,
                    10,
                ),
                "passed": passed,
            }
        )
    return {
        "status": "PASS" if rows and all(row["passed"] for row in rows) else "REJECTED",
        "segment_count": len(rows),
        "segments": rows,
    }


def select_fusion_candidate(
    candidates: list[dict[str, Any]],
    *,
    equal_weight_objective: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not candidates:
        raise OptimizationBlocked(
            "没有产生有效三体系融合候选",
            {
                "candidate_count": 0,
                "eligible_candidate_count": 0,
                "reason": "没有产生有效三体系融合候选",
            },
        )
    eligible = [
        row
        for row in candidates
        if row["objective"] > equal_weight_objective + 1e-6
        and row.get("temporal_robustness", {}).get("status") == "PASS"
        and row["metrics"]["mean_ic"] > 0
        and row["metrics"]["top_decile"]["5d"]["excess_return"] > 0
        and row["metrics"]["top_decile"]["10d"]["excess_return"] > 0
    ]
    selected = max(eligible or candidates, key=lambda row: row["objective"])
    return selected, {
        "status": "VALIDATION_PASS" if eligible else "VALIDATION_REJECTED",
        "candidate_count": len(candidates),
        "eligible_candidate_count": len(eligible),
        "equal_weight_objective": round(equal_weight_objective, 10),
        "selected_objective": round(float(selected["objective"]), 10),
    }


def _linear_model(
    kind: str,
    params: dict[str, float],
    *,
    positive: bool,
):
    if kind == "positive_linear":
        return LinearRegression(positive=positive)
    if kind == "positive_ridge":
        return Ridge(
            positive=positive,
            solver="lbfgs" if positive else "auto",
            **params,
        )
    return ElasticNet(
        positive=positive,
        max_iter=10000,
        random_state=20260813,
        selection="cyclic",
        **params,
    )


def _model_specs() -> list[tuple[str, dict[str, float]]]:
    return [
        ("positive_linear", {}),
        *[
            ("positive_ridge", {"alpha": alpha})
            for alpha in (0.001, 0.01, 0.1, 1.0, 10.0)
        ],
        *[
            ("elastic_net", {"alpha": alpha, "l1_ratio": ratio})
            for alpha in (0.00003, 0.0001, 0.0003)
            for ratio in (0.1, 0.5)
        ],
    ]


def _fit_local_coefficients(
    x: np.ndarray,
    y: np.ndarray,
    fit_mask: np.ndarray,
    active_indexes: list[int],
    *,
    kind: str,
    params: dict[str, float],
    shrinkage: float,
) -> np.ndarray:
    model = _linear_model(kind, params, positive=False)
    model.fit(x[fit_mask][:, active_indexes], y[fit_mask])
    coefficients = np.asarray(model.coef_, dtype=float)
    if np.abs(coefficients).sum() <= 0:
        raise ValueError("体系内模型没有产生有效非零系数")
    learned = coefficients / np.abs(coefficients).sum()
    equal = np.full(len(active_indexes), 1.0 / len(active_indexes))
    directions = np.sign(coefficients)
    directions[directions == 0] = 1.0
    equal_signed = equal * directions
    local = shrinkage * learned + (1.0 - shrinkage) * equal_signed
    if np.abs(local).sum() <= 0:
        raise ValueError("体系内方向收缩后没有有效系数")
    local /= np.abs(local).sum()
    result = np.zeros(x.shape[1], dtype=float)
    result[active_indexes] = local
    return result


def directed_system_score(
    features: np.ndarray,
    coefficients: np.ndarray,
) -> np.ndarray:
    values = np.asarray(features, dtype=float)
    directions = np.asarray(coefficients, dtype=float)
    if values.ndim != 2 or values.shape[1] != len(directions):
        raise ValueError("体系特征与方向系数数量不一致")
    importance = np.abs(directions)
    if importance.sum() <= 0:
        raise ValueError("体系内系数没有有效重要性")
    importance /= importance.sum()
    directed = np.where(directions >= 0, values, 1.0 - values)
    return directed @ importance


def _system_score_matrix(
    x: np.ndarray,
    catalog: list[dict[str, Any]],
    local_coefficients: dict[str, np.ndarray],
) -> np.ndarray:
    columns = []
    for formula in FORMULAS:
        coefficients = np.asarray(local_coefficients[formula], dtype=float)
        if len(coefficients) != len(catalog):
            raise ValueError(f"{formula}体系内系数数量不正确")
        columns.append(directed_system_score(x, coefficients))
    return np.column_stack(columns)


def _floor_system_weights(
    values: np.ndarray,
    floor: float = 0.10,
) -> np.ndarray:
    normalized = _normalize_positive(values)
    if floor * len(normalized) >= 1.0:
        raise ValueError("体系权重下限无效")
    return floor + (1.0 - floor * len(normalized)) * normalized


def _fused_prediction(
    system_scores: np.ndarray,
    system_weights: np.ndarray,
    *,
    resonance_bonus: float,
    disagreement_penalty: float,
) -> np.ndarray:
    scores = np.asarray(system_scores, dtype=float) * 100.0
    weights = _normalize_positive(system_weights)
    base = scores @ weights
    spread = scores.max(axis=1) - scores.min(axis=1)
    agreement = np.maximum(0.0, 1.0 - spread / 100.0)
    resonance = resonance_bonus * scores.min(axis=1) * agreement
    penalty = disagreement_penalty * spread
    return np.clip(base + resonance - penalty, 0.0, 100.0) / 100.0


def _equal_hierarchical_prediction(
    x: np.ndarray,
    catalog: list[dict[str, Any]],
) -> np.ndarray:
    local: dict[str, np.ndarray] = {}
    for formula in FORMULAS:
        active = [
            index
            for index, row in enumerate(catalog)
            if row["formula"] == formula and not row["forced_zero_reason"]
        ]
        coefficients = np.zeros(len(catalog), dtype=float)
        coefficients[active] = 1.0 / len(active)
        local[formula] = coefficients
    system_scores = _system_score_matrix(x, catalog, local)
    return system_scores.mean(axis=1)


def fit_weights(
    frame: pd.DataFrame, catalog: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any], np.ndarray]:
    keys = [row["key"] for row in catalog]
    split = chronological_split(frame["date"].to_numpy())
    x = frame[keys].to_numpy(dtype=float)
    ranked_target = frame.groupby("date")["target"].rank(
        method="average", pct=True
    )
    y = ranked_target.to_numpy(dtype=float) - 0.5
    validation_frame = frame.loc[split["validation"]].reset_index(drop=True)
    selected_local: dict[str, dict[str, Any]] = {}
    train_local_coefficients: dict[str, np.ndarray] = {}
    local_candidate_count = 0
    for formula in FORMULAS:
        active_indexes = [
            index
            for index, row in enumerate(catalog)
            if row["formula"] == formula and not row["forced_zero_reason"]
        ]
        best: dict[str, Any] | None = None
        for kind, params in _model_specs():
            for shrinkage in (0.25, 0.5, 0.75, 1.0):
                try:
                    coefficients = _fit_local_coefficients(
                        x,
                        y,
                        split["train"],
                        active_indexes,
                        kind=kind,
                        params=params,
                        shrinkage=shrinkage,
                    )
                except ValueError:
                    continue
                local_candidate_count += 1
                metrics = evaluate_predictions(
                    validation_frame,
                    directed_system_score(
                        x[split["validation"]],
                        coefficients,
                    ),
                )
                candidate = {
                    "kind": kind,
                    "params": params,
                    "shrinkage": shrinkage,
                    "objective": _prediction_objective(metrics),
                    "metrics": {
                        key: value
                        for key, value in metrics.items()
                        if key not in {"selected_rows", "date_metrics"}
                    },
                    "coefficients": coefficients,
                }
                if best is None or candidate["objective"] > best["objective"]:
                    best = candidate
        if best is None:
            raise OptimizationBlocked(
                f"{formula}没有产生有效体系内模型",
                {
                    "candidate_count": local_candidate_count,
                    "eligible_candidate_count": 0,
                    "reason": f"{formula}没有产生有效体系内模型",
                },
            )
        selected_local[formula] = {
            key: value for key, value in best.items() if key != "coefficients"
        }
        train_local_coefficients[formula] = best["coefficients"]

    train_system_scores = _system_score_matrix(
        x,
        catalog,
        train_local_coefficients,
    )
    fusion_candidates: list[dict[str, Any]] = []
    for kind, params in _model_specs():
        system_model = _linear_model(kind, params, positive=True)
        system_model.fit(train_system_scores[split["train"]], y[split["train"]])
        learned = np.maximum(np.asarray(system_model.coef_, dtype=float), 0.0)
        if learned.sum() <= 0:
            continue
        learned = _floor_system_weights(learned)
        equal = np.full(len(FORMULAS), 1.0 / len(FORMULAS))
        for shrinkage in (0.25, 0.5, 0.75, 1.0):
            system_weights = _floor_system_weights(
                shrinkage * learned + (1.0 - shrinkage) * equal
            )
            for resonance_bonus in (0.03, 0.06, 0.09, 0.12):
                for disagreement_penalty in (0.02, 0.05, 0.08, 0.12):
                    validation_prediction = _fused_prediction(
                        train_system_scores[split["validation"]],
                        system_weights,
                        resonance_bonus=resonance_bonus,
                        disagreement_penalty=disagreement_penalty,
                    )
                    metrics = evaluate_predictions(
                        validation_frame,
                        validation_prediction,
                    )
                    fusion_candidates.append(
                        {
                            "kind": kind,
                            "params": params,
                            "shrinkage": shrinkage,
                            "resonance_bonus": resonance_bonus,
                            "disagreement_penalty": disagreement_penalty,
                            "objective": round(
                                _prediction_objective(metrics),
                                10,
                            ),
                            "metrics": {
                                key: value
                                for key, value in metrics.items()
                                if key not in {"selected_rows", "date_metrics"}
                            },
                            "_validation_prediction": validation_prediction,
                        }
                    )
    if not fusion_candidates:
        raise OptimizationBlocked(
            "没有产生有效三体系融合候选",
            {
                "candidate_count": 0,
                "eligible_candidate_count": 0,
                "reason": "没有产生有效三体系融合候选",
            },
        )

    equal_validation_prediction = _equal_hierarchical_prediction(
        x[split["validation"]],
        catalog,
    )
    equal_validation_metrics = evaluate_predictions(
        validation_frame,
        equal_validation_prediction,
    )
    equal_validation_objective = _prediction_objective(equal_validation_metrics)
    for candidate in fusion_candidates:
        candidate["temporal_robustness"] = temporal_validation_robustness(
            validation_frame,
            np.asarray(candidate.pop("_validation_prediction"), dtype=float),
            equal_validation_prediction,
            segments=3,
        )
    selected, validation_selection = select_fusion_candidate(
        fusion_candidates,
        equal_weight_objective=equal_validation_objective,
    )
    fit_mask = split["train"] | split["validation"]
    final_local_coefficients: dict[str, np.ndarray] = {}
    for formula in FORMULAS:
        active_indexes = [
            index
            for index, row in enumerate(catalog)
            if row["formula"] == formula and not row["forced_zero_reason"]
        ]
        local_spec = selected_local[formula]
        final_local_coefficients[formula] = _fit_local_coefficients(
            x,
            y,
            fit_mask,
            active_indexes,
            kind=local_spec["kind"],
            params=local_spec["params"],
            shrinkage=float(local_spec["shrinkage"]),
        )
    final_system_scores = _system_score_matrix(
        x,
        catalog,
        final_local_coefficients,
    )
    final_system_model = _linear_model(
        selected["kind"],
        selected["params"],
        positive=True,
    )
    final_system_model.fit(final_system_scores[fit_mask], y[fit_mask])
    learned_system = _floor_system_weights(
        np.maximum(np.asarray(final_system_model.coef_, dtype=float), 0.0)
    )
    equal_system = np.full(len(FORMULAS), 1.0 / len(FORMULAS))
    final_system_weights = _floor_system_weights(
        selected["shrinkage"] * learned_system
        + (1.0 - selected["shrinkage"]) * equal_system
    )
    model = build_hierarchical_model(
        catalog,
        final_local_coefficients,
        {
            formula: float(weight * 100.0)
            for formula, weight in zip(
                FORMULAS,
                final_system_weights,
                strict=True,
            )
        },
        resonance_bonus=float(selected["resonance_bonus"]),
        disagreement_penalty=float(selected["disagreement_penalty"]),
        metadata={
            "predictive_validation_selection": validation_selection["status"],
            "selected_local_models": selected_local,
            "selected_fusion_model": {
                key: value
                for key, value in selected.items()
                if key != "metrics"
            },
        },
    )
    predictions = _fused_prediction(
        final_system_scores,
        final_system_weights,
        resonance_bonus=float(selected["resonance_bonus"]),
        disagreement_penalty=float(selected["disagreement_penalty"]),
    )
    evidence = {
        "selected_model": {
            "model_type": model["model_type"],
            "local_models": selected_local,
            "fusion_model": {
                key: value
                for key, value in selected.items()
                if key != "metrics"
            },
            "validation_objective": selected["objective"],
            "equal_weight_validation_objective": round(
                equal_validation_objective,
                10,
            ),
        },
        "candidate_count": len(fusion_candidates),
        "local_candidate_count": local_candidate_count,
        "validation_selection": validation_selection,
        "top_candidates": sorted(
            fusion_candidates,
            key=lambda row: row["objective"],
            reverse=True,
        )[:5],
        "date_split": {
            "purge": {
                "rebalance_dates_per_boundary": int(split["purge_dates"]),
                "label_horizon_trading_days": 10,
                "train_validation_purged_dates": split[
                    "purged_train_dates"
                ].astype(str).tolist(),
                "validation_test_purged_dates": split[
                    "purged_validation_dates"
                ].astype(str).tolist(),
            },
            "train": {
                "start": str(split["train_dates"][0]),
                "end": str(split["train_dates"][-1]),
                "dates": len(split["train_dates"]),
                "observations": int(split["train"].sum()),
            },
            "validation": {
                "start": str(split["validation_dates"][0]),
                "end": str(split["validation_dates"][-1]),
                "dates": len(split["validation_dates"]),
                "observations": int(split["validation"].sum()),
            },
            "test": {
                "start": str(split["test_dates"][0]),
                "end": str(split["test_dates"][-1]),
                "dates": len(split["test_dates"]),
                "observations": int(split["test"].sum()),
            },
        },
        "train_validation_metrics": {
            key: value
            for key, value in evaluate_predictions(
                frame.loc[fit_mask].reset_index(drop=True),
                predictions[fit_mask],
            ).items()
            if key not in {"selected_rows", "date_metrics"}
        },
        "test_metrics": evaluate_predictions(
            frame.loc[split["test"]].reset_index(drop=True),
            predictions[split["test"]],
        ),
        "equal_weight_validation_metrics": {
            key: value
            for key, value in equal_validation_metrics.items()
            if key not in {"selected_rows", "date_metrics"}
        },
        "split_masks": split,
    }
    return model, evidence, predictions


def equal_weight_metrics(
    frame: pd.DataFrame,
    catalog: list[dict[str, Any]],
    test_mask: np.ndarray,
) -> dict[str, Any]:
    keys = [row["key"] for row in catalog]
    prediction = _equal_hierarchical_prediction(
        frame.loc[test_mask, keys].to_numpy(dtype=float),
        catalog,
    )
    metrics = evaluate_predictions(
        frame.loc[test_mask].reset_index(drop=True), prediction
    )
    return {
        key: value
        for key, value in metrics.items()
        if key not in {"selected_rows", "date_metrics"}
    }


def validation_gates(
    stock_count: int,
    frame: pd.DataFrame,
    metrics: dict[str, Any],
    equal_metrics: dict[str, Any],
    model: dict[str, Any],
    *,
    point_in_time_universe_available: bool = False,
    tradability_constraints_complete: bool = False,
) -> dict[str, Any]:
    validate_hierarchical_model(model)
    statistical = metrics.get("statistical_tests", {})
    ic_statistics = statistical.get("mean_ic", {})
    excess_5d_statistics = statistical.get("excess_5d", {})
    excess_10d_statistics = statistical.get("excess_10d", {})
    def ci_lower_positive(node: dict[str, Any]) -> bool:
        value = node.get("ci95_lower")
        return isinstance(value, (int, float)) and math.isfinite(value) and value > 0
    active_local = [
        row["local_weight"]
        for row in model["subsystem_weights"]
        if row["local_weight"] > 0
    ]
    checks = {
        "stocks_at_least_250": stock_count >= 250,
        "observations_at_least_10000": len(frame) >= 10000,
        "test_dates_at_least_40": metrics["rebalance_dates"] >= MIN_OOS_DATES,
        "test_median_cross_section_at_least_200": (
            metrics["median_cross_section"] >= 200
        ),
        "independent_oos_rows_nonempty": bool(metrics.get("selected_rows")),
        "independent_oos_dates_nonempty": bool(metrics.get("date_metrics")),
        "test_ic_economic_floor": metrics["mean_ic"] >= MIN_MEAN_IC,
        "test_5d_excess_economic_floor": (
            metrics["top_decile"]["5d"]["excess_return"] >= MIN_5D_EXCESS_RETURN
        ),
        "test_10d_excess_economic_floor": (
            metrics["top_decile"]["10d"]["excess_return"] >= MIN_10D_EXCESS_RETURN
        ),
        "test_ic_newey_west_ci_lower_positive": ci_lower_positive(ic_statistics),
        "test_5d_newey_west_ci_lower_positive": ci_lower_positive(
            excess_5d_statistics
        ),
        "test_10d_newey_west_ci_lower_positive": ci_lower_positive(
            excess_10d_statistics
        ),
        "validation_selection_passed": (
            model.get("metadata", {}).get("predictive_validation_selection")
            == "VALIDATION_PASS"
        ),
        "strictly_better_than_equal_weight_5d": (
            metrics["top_decile"]["5d"]["excess_return"]
            > equal_metrics["top_decile"]["5d"]["excess_return"] + 1e-6
        ),
        "strictly_better_than_equal_weight_ic": (
            metrics["mean_ic"] > equal_metrics["mean_ic"] + 1e-6
        ),
        "point_in_time_universe_available": point_in_time_universe_available,
        "tradability_constraints_complete": tradability_constraints_complete,
        "hierarchical_model_required": (
            model["model_type"] == "hierarchical_three_system_resonance"
        ),
        "three_system_weights_sum_100": abs(
            sum(model["system_weights"].values()) - 100.0
        )
        < 1e-6,
        "each_system_weight_at_least_10": min(
            model["system_weights"].values()
        )
        >= 10.0 - 1e-6,
        "each_system_local_weights_sum_100": all(
            abs(
                sum(
                    row["local_weight"]
                    for row in model["subsystem_weights"]
                    if row["formula"] == formula
                )
                - 100.0
            )
            < 1e-6
            for formula in FORMULAS
        ),
        "resonance_and_disagreement_terms_present": (
            model["fusion"]["resonance_bonus"] > 0
            and model["fusion"]["disagreement_penalty"] > 0
        ),
        "at_least_8_active_subsystems": len(active_local) >= 8,
    }
    return {
        "status": "PASS" if all(checks.values()) else "BLOCKED",
        "checks": checks,
        "failed": [key for key, value in checks.items() if not value],
    }


def send_official_tq_backtest(
    tq,
    selected_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if not selected_rows:
        return {"status": "BLOCKED", "error": "no_selected_rows"}
    counts: dict[str, int] = {}
    for row in selected_rows:
        symbol = str(row["symbol"])
        counts[symbol] = counts.get(symbol, 0) + 1
    symbol = max(counts, key=counts.get)
    trades = [row for row in selected_rows if row["symbol"] == symbol][:20]
    records = read_day_file(day_path(symbol))
    by_date = {row["date"]: index for index, row in enumerate(records)}
    time_list: list[str] = []
    data_list: list[list[str]] = []
    for row in trades:
        index = by_date.get(str(row["date"]))
        if index is None or index + 5 >= len(records):
            continue
        entry = records[index + 1]
        exit_row = records[index + 5]
        time_list.extend([entry["date"] + "093000", exit_row["date"] + "150000"])
        data_list.extend(
            [
                ["1", f"{entry['open']:.2f}", "100", "0", "0", "0"],
                ["0", "0", "0", "1", f"{exit_row['close']:.2f}", "100"],
            ]
        )
    if not time_list:
        return {"status": "BLOCKED", "error": "no_transferable_trades"}
    response = tq.send_bt_data(
        stock_code=symbol,
        time_list=time_list,
        data_list=data_list,
        count=len(time_list),
    )
    ok = isinstance(response, dict) and str(response.get("ErrorId")) == "0"
    return {
        "status": "PASS" if ok else "BLOCKED",
        "stock_code": symbol,
        "trade_count": len(time_list) // 2,
        "point_count": len(time_list),
        "response": response,
        "interface": "TdxQuant TQ send_bt_data",
    }


def render_report(payload: dict[str, Any]) -> str:
    gates = payload["validation_gates"]
    test = payload["backtest"]["test_metrics"]
    equal = payload["backtest"]["equal_weight_test_metrics"]
    statistics = test["statistical_tests"]
    lines = [
        "# 三公式综合评分系统历史回测与权重优化证据",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 状态：{payload['status']}",
        f"- 本机通达信截止日：{payload['data']['latest_date']}",
        f"- 股票样本：{payload['data']['stock_count']}只",
        f"- 可用观察值：{payload['data']['observation_count']}条",
        f"- 公式子系统：固定30项（大牛线撑压版16项、飞龙在天10项、庄家资金监控4项）",
        f"- 交易口径：统一前复权序列中信号日后精确下一市场交易日开盘成交，入场日成交额不少于{payload['method']['minimum_entry_amount'] / 10000:.0f}万元，排除零流动性及一字涨停，双边成本{payload['method']['cost_bps']:.0f}基点",
        "",
        "## 科学性约束",
        "",
        "1. 所有公式信号来自本机通达信TQ历史公式输出或对应公式原文的因果推导。",
        "2. 训练、验证、测试按时间先后切分；10日标签在两条边界各净化2个五日再平衡点，测试集不参与权重选择。",
        "3. 特征覆盖率和横截面区分度只在训练期拟合，固定后应用于验证与独立测试。",
        "4. 三套公式特征与收益标签全部使用本机通达信front前复权K线，避免公司行动口径错配。",
        "5. 先在三套体系内部独立建模并各自归一为100分，再由体系级模型融合；30项不得越级直接相加。",
        "6. 目标同时覆盖3日、5日、10日收益与5日有利/不利波动，不针对单一持有期调参。",
        "7. 独立样本外同时要求经济门槛、等权基准优势和Newey-West 95%区间下界大于0；任一失败即PREDICTIVE_REJECTED。",
        "8. 历史时点股票池以及涨跌停、停牌、ST和流动性可交易约束均为预测通过硬条件；当前任一缺失即拒绝预测模型。",
        "9. 融合候选除全验证期优于等权外，还必须在按时间切分的三个验证子区间逐段保持正IC、正5日/10日超额并优于等权目标。",
        "",
        "## 数据完整性审计",
        "",
        f"- 历史时点股票池完整：{payload['data']['point_in_time_universe_audit']['complete']}",
        f"- 可交易性约束完整：{payload['data']['tradability_audit']['complete']}",
        f"- 可交易性排除统计：{json.dumps(payload['data']['tradability_audit']['excluded_by_reason'], ensure_ascii=False, sort_keys=True)}",
        f"- 仍缺字段：{payload['data']['point_in_time_universe_audit']['incomplete_reason']}；{payload['data']['tradability_audit']['incomplete_reason']}",
        "",
        "## 样本外结果",
        "",
        "| 指标 | 优化权重 | 等权基准 |",
        "|---|---:|---:|",
        f"| 平均秩相关IC | {test['mean_ic']:.4f} | {equal['mean_ic']:.4f} |",
        f"| 5日Top10%超额 | {test['top_decile']['5d']['excess_return']:.2%} | {equal['top_decile']['5d']['excess_return']:.2%} |",
        f"| 10日Top10%超额 | {test['top_decile']['10d']['excess_return']:.2%} | {equal['top_decile']['10d']['excess_return']:.2%} |",
        f"| 5日Top10%胜率 | {test['top_decile']['5d']['hit_rate']:.2%} | {equal['top_decile']['5d']['hit_rate']:.2%} |",
        f"| 5日序列最大回撤 | {test['max_drawdown_5d_sequence']:.2%} | {equal['max_drawdown_5d_sequence']:.2%} |",
        "",
        "## 独立样本外统计区间",
        "",
        "| 序列 | 均值 | Newey-West标准误 | 95%下界 | 95%上界 |",
        "|---|---:|---:|---:|---:|",
        f"| 日度横截面IC | {statistics['mean_ic']['mean']:.4f} | {statistics['mean_ic']['standard_error']:.4f} | {statistics['mean_ic']['ci95_lower']:.4f} | {statistics['mean_ic']['ci95_upper']:.4f} |",
        f"| 5日Top10%超额 | {statistics['excess_5d']['mean']:.2%} | {statistics['excess_5d']['standard_error']:.2%} | {statistics['excess_5d']['ci95_lower']:.2%} | {statistics['excess_5d']['ci95_upper']:.2%} |",
        f"| 10日Top10%超额 | {statistics['excess_10d']['mean']:.2%} | {statistics['excess_10d']['standard_error']:.2%} | {statistics['excess_10d']['ci95_lower']:.2%} | {statistics['excess_10d']['ci95_upper']:.2%} |",
        "",
        f"预声明经济门槛：平均IC≥{MIN_MEAN_IC:.3f}，5日超额≥{MIN_5D_EXCESS_RETURN:.2%}，10日超额≥{MIN_10D_EXCESS_RETURN:.2%}，独立样本外日期≥{MIN_OOS_DATES}。",
        "",
        "## 体系级融合",
        "",
        "| 体系 | 权重 |",
        "|---|---:|",
    ]
    for formula in FORMULAS:
        lines.append(
            f"| {formula} | {payload['model']['system_weights'][formula]:.2f} |"
        )
    lines.extend(
        [
            "",
            f"- 三体系共振系数：{payload['model']['fusion']['resonance_bonus']:.4f}",
            f"- 体系分歧系数：{payload['model']['fusion']['disagreement_penalty']:.4f}",
            "",
            "## 体系内权重",
            "",
            "| 公式 | 序号 | 子系统 | 体系内权重 | 处理说明 |",
            "|---|---:|---|---:|---|",
        ]
    )
    for row in payload["model"]["subsystem_weights"]:
        lines.append(
            f"| {row['formula']} | {row['number']} | {row['name']} | "
            f"{row['local_weight']:.2f} | {row['forced_zero_reason'] or row['source']} |"
        )
    lines.extend(
        [
            "",
            "## 验收门槛",
            "",
        ]
    )
    for name, passed in gates["checks"].items():
        lines.append(f"- {'通过' if passed else '失败'}：{name}")
    lines.extend(
        [
            "",
            "## 通达信官方接口证据",
            "",
            f"- 公式注册与历史执行：{payload['official_tdx']['formula_execution_status']}",
            f"- TQ回测结果回传：{payload['official_tdx']['backtest_transfer']['status']}",
            f"- 接口：{payload['official_tdx']['backtest_transfer'].get('interface', 'TdxQuant TQ')}",
            "",
            "本报告是历史统计研究证据，不构成收益承诺。当前成分股样本仍存在退市样本缺失等幸存者偏差边界。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_blocked_report(payload: dict[str, Any]) -> str:
    optimization = payload["optimization_evidence"]
    best = optimization.get("best_candidate") or {}
    lines = [
        "# 三公式综合评分系统历史回测阻断证据",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 状态：{payload['status']}",
        f"- 阻断原因：{payload['reason']}",
        f"- 方法版本：{payload['methodology_version']}",
        f"- 本机通达信截止日：{payload['data']['latest_date']}",
        f"- 股票样本：{payload['data']['stock_count']}只",
        f"- 可用观察值：{payload['data']['observation_count']}条",
        f"- 权重候选：{optimization.get('candidate_count', 0)}组",
        f"- 合格候选：{optimization.get('eligible_candidate_count', 0)}组",
        "",
        "## 科学结论",
        "",
        "庄家资金监控已按固定官方调用链逐股执行：formula_set_data_info → formula_zb。",
        "30项原始特征先做历史覆盖率和横截面区分度审计，再进入时间切分和权重优化。",
        "当前验证期没有任何分层融合候选严格优于三体系等权基准，因此未安装正式可用模型，旧模型已失效。",
    ]
    if best:
        lines.extend(
            [
                "",
                "## 最优但不合格候选",
                "",
                f"- 模型：{best.get('kind')}",
                f"- 参数：{json.dumps(best.get('params', {}), ensure_ascii=False)}",
                f"- 收缩比例：{best.get('shrinkage')}",
                f"- 候选目标值：{best.get('objective')}",
                f"- 等权目标值：{optimization.get('equal_weight_validation_objective')}",
            ]
        )
    lines.extend(
        [
            "",
            "该结果表示当前样本与约束下无法科学固化差异化综合评分权重，不构成收益承诺或交易指令。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_structural_report(payload: dict[str, Any]) -> str:
    model = payload["model"]
    lines = [
        "# 三公式综合评分系统正式固化证据",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 系统状态：{payload['status']}",
        f"- 模型类型：{model['model_type']}",
        f"- 模型来源：{model['metadata']['model_origin']}",
        f"- 预测验证：{model['metadata']['predictive_validation']}",
        f"- 预测验证说明：{model['metadata']['predictive_validation_reason']}",
        f"- 本机通达信截止日：{payload['data']['latest_date']}",
        f"- 股票样本：{payload['data']['stock_count']}只",
        f"- 可用观察值：{payload['data']['observation_count']}条",
        "",
        "## 固化结构",
        "",
        "1. 大牛线撑压版16项、飞龙在天10项、庄家资金监控4项仅在各自体系内部形成0至100分子分。",
        "2. 体系内权重依据历史覆盖率与横截面区分度审计，重复、常量、不可回溯和无区分度项保留审计行并置零。",
        "3. 融合层只接收三套体系子分，计算体系加权基础分、三体系共振加分和体系分歧扣分。",
        "4. 唯一总分限制在0至100分，固定公式可逐项复算，不是30项直接拼接。",
        "",
        "## 体系级权重",
        "",
    ]
    for formula in FORMULAS:
        lines.append(
            f"- {formula}：{model['system_weights'][formula]:.4f}"
        )
    lines.extend(
        [
            f"- 共振系数：{model['fusion']['resonance_bonus']:.4f}",
            f"- 分歧系数：{model['fusion']['disagreement_penalty']:.4f}",
            "",
            "## 验证边界",
            "",
            "结构完整性、权重归一、三体系共同参与、总分复算和本机通达信取数均已纳入固定校验。",
            "当前训练和验证样本未建立优于三体系等权基准的预测优势，因此本模型用于一致化综合评分和候选比较，不声称已证明超额收益。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_blocked_weights_payload(
    source_backtest: Path,
    *,
    generated_at: str,
    reason: str,
    optimization_evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": "THREE_FORMULA_COMPOSITE_MODEL_V1",
        "status": "BLOCKED",
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": generated_at,
        "source_backtest": str(source_backtest),
        "source_backtest_sha256": sha256_file(source_backtest),
        "reason": reason,
        "optimization_evidence": optimization_evidence,
        "predictive_validation": {
            "status": "BLOCKED",
            "oos_row_count": 0,
            "oos_date_count": 0,
            "failed_gates": ["scientific_weight_candidate_not_found"],
        },
        "model": None,
        "validation_gates": {
            "status": "BLOCKED",
            "checks": {},
            "failed": ["scientific_weight_candidate_not_found"],
        },
    }


def build_formal_weights_payload(
    source_backtest: Path,
    *,
    generated_at: str,
    predictive_status: str,
    model: dict[str, Any],
    validation_gates: dict[str, Any],
    oos_row_count: int,
    oos_date_count: int,
) -> dict[str, Any]:
    if predictive_status not in {"PREDICTIVE_PASS", "PREDICTIVE_REJECTED"}:
        raise ValueError(f"未知预测状态：{predictive_status}")
    if predictive_status == "PREDICTIVE_PASS" and (
        oos_row_count <= 0 or oos_date_count <= 0
    ):
        raise ValueError("预测通过所需的独立样本外证据为空")
    passed = (
        predictive_status == "PREDICTIVE_PASS"
        and validation_gates.get("status") == "PASS"
    )
    return {
        "schema": "THREE_FORMULA_COMPOSITE_MODEL_V1",
        "status": "CLEAN_PASS" if passed else "PREDICTIVE_REJECTED",
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": generated_at,
        "source_backtest": str(source_backtest),
        "source_backtest_sha256": sha256_file(source_backtest),
        "predictive_validation": {
            "status": "PREDICTIVE_PASS" if passed else "PREDICTIVE_REJECTED",
            "oos_row_count": int(oos_row_count),
            "oos_date_count": int(oos_date_count),
            "failed_gates": list(validation_gates.get("failed", [])),
        },
        "model": model if passed else None,
        "validation_gates": validation_gates,
    }


def sync_formal_model_state(source: Path, target: Path) -> dict[str, Any]:
    source = source.resolve()
    target = target.resolve()
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("正式模型状态根节点不是对象")
    if payload.get("schema") != "THREE_FORMULA_COMPOSITE_MODEL_V1":
        raise ValueError("正式模型状态结构版本无效")
    if payload.get("methodology_version") != METHODOLOGY_VERSION:
        raise ValueError("正式模型状态方法版本不是当前V5版本")

    status = payload.get("status")
    predictive = payload.get("predictive_validation")
    predictive_status = (
        predictive.get("status") if isinstance(predictive, dict) else None
    )
    model = payload.get("model")
    validation = payload.get("validation_gates")
    if status == "PREDICTIVE_REJECTED":
        if predictive_status != "PREDICTIVE_REJECTED":
            raise ValueError("预测拒绝状态与预测验证终态不一致")
        if model is not None:
            raise ValueError("预测拒绝状态不得携带模型")
        if (
            not isinstance(validation, dict)
            or validation.get("status") == "PASS"
            or not list(validation.get("failed", []))
        ):
            raise ValueError("预测拒绝状态缺少失败门禁证据")
    elif status == "CLEAN_PASS":
        if predictive_status != "PREDICTIVE_PASS":
            raise ValueError("正式通过状态缺少预测通过终态")
        if not isinstance(model, dict):
            raise ValueError("正式通过状态缺少可用模型")
        if (
            not isinstance(validation, dict)
            or validation.get("status") != "PASS"
            or int(predictive.get("oos_row_count", 0)) <= 0
            or int(predictive.get("oos_date_count", 0)) <= 0
        ):
            raise ValueError("正式通过状态缺少独立样本外通过证据")
        validate_hierarchical_model(model)
    elif status == "BLOCKED":
        if predictive_status != "BLOCKED":
            raise ValueError("阻塞状态与预测验证终态不一致")
        if model is not None:
            raise ValueError("阻塞状态不得携带模型")
        if not isinstance(validation, dict) or validation.get("status") != "BLOCKED":
            raise ValueError("阻塞状态缺少阻塞门禁证据")
    else:
        raise ValueError(f"禁止同步未验收的正式模型状态：{status!r}")

    evidence_path = Path(str(payload.get("source_backtest", "")))
    expected_evidence_hash = str(payload.get("source_backtest_sha256", ""))
    if not evidence_path.is_file():
        raise ValueError("正式模型状态绑定的回测证据不存在")
    if sha256_file(evidence_path) != expected_evidence_hash:
        raise ValueError("正式模型状态绑定的回测证据哈希不匹配")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise ValueError("回测证据根节点不是对象")
    if evidence.get("status") != predictive_status:
        raise ValueError("正式模型状态与回测证据预测终态不一致")
    if evidence.get("methodology_version") != METHODOLOGY_VERSION:
        raise ValueError("回测证据方法版本不是当前V5版本")

    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        temp_path.replace(target)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    return {
        "schema": "THREE_FORMULA_COMPOSITE_STATE_SYNC_V1",
        "status": status,
        "methodology_version": METHODOLOGY_VERSION,
        "model_usable": status == "CLEAN_PASS",
        "source": str(source),
        "source_sha256": sha256_file(source),
        "source_backtest": str(evidence_path),
        "source_backtest_sha256": expected_evidence_hash,
        "target": str(target),
        "target_sha256": sha256_file(target),
        "oos_row_count": int(predictive.get("oos_row_count", 0)),
        "oos_date_count": int(predictive.get("oos_date_count", 0)),
        "failed_gates": list(predictive.get("failed_gates", [])),
        "atomic_replace": True,
    }


def run_formal_model_state_sync(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    source = Path(args.sync_model_state_from).resolve()
    target = Path(args.sync_model_state_to or args.weights_file).resolve()
    receipt = sync_formal_model_state(source, target)
    snapshot = output_dir / "三公式综合评分同步后模型状态.json"
    snapshot.write_bytes(target.read_bytes())
    receipt_path = output_dir / "三公式综合评分状态同步收据.json"
    receipt["artifacts"] = {
        "synced_state": {
            "path": str(snapshot),
            "sha256": sha256_file(snapshot),
        },
        "sync_receipt": {
            "path": str(receipt_path),
        },
    }
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    receipt["artifacts"]["sync_receipt"]["sha256"] = sha256_file(receipt_path)
    print(json.dumps(receipt, ensure_ascii=False))
    return receipt


def load_formal_weights(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "CLEAN_PASS":
        raise FormalModelUnavailable("正式模型文件未通过回测验收")
    if payload.get("methodology_version") != METHODOLOGY_VERSION:
        raise FormalModelUnavailable("正式模型方法版本不是当前科学取数版本")
    predictive = payload.get("predictive_validation")
    if not isinstance(predictive, dict) or predictive.get("status") != "PREDICTIVE_PASS":
        raise FormalModelUnavailable("正式模型预测验证未通过")
    model = payload.get("model")
    if not isinstance(model, dict):
        raise FormalModelUnavailable("正式文件缺少三体系分层融合模型")
    validate_hierarchical_model(model)
    source_backtest = Path(str(payload.get("source_backtest", "")))
    expected_hash = str(payload.get("source_backtest_sha256", ""))
    if not source_backtest.is_file():
        raise FormalModelUnavailable("正式权重来源回测证据不存在")
    if sha256_file(source_backtest) != expected_hash:
        raise FormalModelUnavailable("正式权重来源回测证据哈希不匹配")
    return payload, model


def market_percentile_from_rank(rank: int, universe_count: int) -> float:
    if universe_count <= 0 or rank < 1 or rank > universe_count:
        raise ValueError("全市场排名或母体数量无效")
    return round((universe_count - rank + 0.5) / universe_count * 100.0, 8)


def current_score_conclusion(row: dict[str, Any]) -> str:
    scoring_items = row.get("top_level_items", row["formula_scores"])
    strongest = max(scoring_items, key=scoring_items.get)
    weakest = min(scoring_items, key=scoring_items.get)
    percentile = float(row["market_percentile"])
    if percentile >= 90:
        level = "固定母体前10%"
    elif percentile >= 70:
        level = "固定母体前30%"
    elif percentile >= 30:
        level = "固定母体中间40%"
    else:
        level = "固定母体后30%"
    score_values = [float(value) for value in scoring_items.values()]
    spread = max(score_values) - min(score_values)
    if percentile >= 90 and min(score_values) >= 50:
        forecast = "未来5至10个交易日结构偏强，倾向延续上行或强势整理"
    elif percentile >= 70:
        forecast = "未来5至10个交易日偏强震荡，倾向保持相对强势"
    elif percentile >= 30:
        forecast = "未来5至10个交易日震荡分化，方向优势尚不突出"
    else:
        forecast = "未来5至10个交易日结构偏弱，倾向先修复再确认"
    invalidation = (
        "三体系分歧继续扩大则预测失效"
        if spread >= 20
        else "任一主导体系跌破当日固定母体中位且共振转负则预测失效"
    )
    return (
        f"{forecast}；{level}；最强体系为{strongest}"
        f"（{float(scoring_items[strongest]):.2f}分），"
        f"最弱体系为{weakest}"
        f"（{float(scoring_items[weakest]):.2f}分）；{invalidation}。"
    )


def validate_current_score_delivery(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("status") != "CLEAN_PASS":
        raise ValueError("评分结果状态不是CLEAN_PASS")
    if payload.get("score_is_probability") is not False:
        raise ValueError("综合结构分不得解释为上涨概率")
    if "不是上涨概率" not in str(payload.get("score_interpretation", "")):
        raise ValueError("综合结构分缺少非概率解释")
    if payload.get("forecast_mode") != "RULE_BASED_STRUCTURAL_FORECAST":
        raise ValueError("结构预测模式未启用")
    if payload.get("forecast_horizon") != "未来5至10个交易日":
        raise ValueError("结构预测期限缺失")
    if payload.get("forecast_is_probability") is not False:
        raise ValueError("结构预测不得伪装成概率")
    if payload.get("date_gate", {}).get("status") != "PASS":
        raise ValueError("评分日期硬闸未通过")
    identity_validation = validate_composite_ranking_identity(payload)
    ranking = payload.get("ranking")
    if not isinstance(ranking, list) or not ranking:
        raise ValueError("评分排名为空")
    if len(ranking) != int(payload.get("stock_count", 0)):
        raise ValueError("评分排名数量与股票数量不一致")
    board = payload.get("board")
    if board and len(ranking) != int(board.get("constituent_count", 0)):
        raise ValueError("评分排名未覆盖全部板块成分")
    expected_formula_counts = {
        BIG_BULL_FORMULA: 16,
        FEILONG_FORMULA: 10,
        DEALER_FORMULA: 4,
    }
    contribution_row_count = 0
    for row in ranking:
        symbol = str(row.get("symbol", ""))
        if not str(row.get("name", "")).strip():
            raise ValueError(f"股票名称缺失：{symbol}")
        formula_scores = row.get("formula_scores")
        if not isinstance(formula_scores, dict) or set(formula_scores) != set(FORMULAS):
            raise ValueError(f"三体系子分不完整：{symbol}")
        top_level_items = row.get("top_level_items")
        expected_top_level = set(FORMULAS)
        if not isinstance(top_level_items, dict) or set(top_level_items) != expected_top_level:
            raise ValueError(f"三个顶层评分体系不完整：{symbol}")
        fusion = row.get("fusion")
        required_fusion = {
            "base_score",
            "resonance_bonus",
            "disagreement_penalty",
            "total_score",
        }
        if not isinstance(fusion, dict) or not required_fusion.issubset(fusion):
            raise ValueError(f"总分拆解不完整：{symbol}")
        top_level_weights = fusion.get("top_level_weights")
        if (
            fusion.get("top_level_item_count") != 3
            or not isinstance(top_level_weights, dict)
            or set(top_level_weights) != expected_top_level
            or not math.isclose(sum(top_level_weights.values()), 100.0, abs_tol=1e-7)
        ):
            raise ValueError(f"三体系权重结构无效：{symbol}")
        recomputed = max(
            0.0,
            min(
                100.0,
                float(fusion["base_score"])
                + float(fusion["resonance_bonus"])
                - float(fusion["disagreement_penalty"]),
            ),
        )
        if not math.isclose(float(row["score"]), recomputed, abs_tol=1e-7):
            raise ValueError(f"总分不可复算：{symbol}")
        contributions = row.get("contributions")
        if not isinstance(contributions, list) or len(contributions) != 30:
            raise ValueError(f"30项贡献不完整：{symbol}")
        item_keys = {
            (item.get("formula"), item.get("number"), item.get("key"))
            for item in contributions
        }
        if len(item_keys) != 30:
            raise ValueError(f"30项贡献存在重复：{symbol}")
        formula_counts = {
            formula: sum(
                1 for item in contributions if item.get("formula") == formula
            )
            for formula in FORMULAS
        }
        if formula_counts != expected_formula_counts:
            raise ValueError(f"16+10+4评分明细不完整：{symbol}")
        for item in contributions:
            raw_value = safe_float(item.get("raw_value"))
            percentile = safe_float(item.get("percentile"))
            effective_percentile = safe_float(item.get("effective_percentile"))
            reliability = safe_float(item.get("system_reliability"))
            local_weight = safe_float(item.get("local_weight"))
            base_contribution = safe_float(item.get("base_contribution"))
            if not math.isfinite(raw_value):
                raise ValueError(f"30项存在非有限真实值：{symbol}:{item.get('key')}")
            if not math.isfinite(local_weight) or local_weight <= 0:
                raise ValueError(f"30项存在零业务权重：{symbol}:{item.get('key')}")
            if not math.isfinite(base_contribution):
                raise ValueError(f"30项贡献不可复算：{symbol}:{item.get('key')}")
            if str(item.get("forced_zero_reason", "")).strip():
                raise ValueError(f"30项仍含强制零权重原因：{symbol}:{item.get('key')}")
            if (
                not math.isfinite(effective_percentile)
                or not 0 <= effective_percentile <= 100
            ):
                raise ValueError(f"可靠性调整后百分位缺失或无效：{symbol}")
            if not math.isfinite(reliability) or not 0 <= reliability <= 1:
                raise ValueError(f"体系信息可靠性缺失或无效：{symbol}")
            expected_effective = 50.0 + reliability * (percentile - 50.0)
            if not math.isclose(
                effective_percentile,
                expected_effective,
                rel_tol=0.0,
                abs_tol=1e-6,
            ):
                raise ValueError(f"可靠性调整后百分位与公式不一致：{symbol}")
        if not str(row.get("conclusion", "")).strip():
            raise ValueError(f"综合结论缺失：{symbol}")
        if "未来5至10个交易日" not in str(row.get("conclusion", "")) or "预测失效" not in str(row.get("conclusion", "")):
            raise ValueError(f"预测结论或失效条件缺失：{symbol}")
        market_percentile = safe_float(row.get("market_percentile"))
        if not math.isfinite(market_percentile) or not 0 <= market_percentile <= 100:
            raise ValueError(f"全市场分位无效：{symbol}")
        contribution_row_count += len(contributions)
    return {
        "status": "PASS",
        "scoring_identity": identity_validation,
        "stock_count": len(ranking),
        "contribution_row_count": contribution_row_count,
        "required_fields": [
            "股票名称",
            "股票代码",
            "板块排名",
            "全市场排名",
            "全市场分位",
            "综合总分",
            "体系加权基础分",
            "三体系共振加分",
            "体系分歧扣分",
            *FORMULAS,
            "综合结论",
            "未来5至10个交易日结构预测",
            "预测失效条件",
            "固定30项完整明细",
        ],
    }


def _display_number(value: Any, digits: int = 4) -> str:
    number = safe_float(value)
    if math.isnan(number):
        return "不可回溯"
    return f"{number:.{digits}f}"


def render_current_score_report(payload: dict[str, Any]) -> str:
    delivery = validate_current_score_delivery(payload)
    date_gate = payload["date_gate"]
    lines = [
        "# 大牛线撑压版＋飞龙在天＋庄家资金监控综合评分完整报告",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 评分交易日：{payload['score_date']}",
        f"- 日期硬闸：{date_gate['status']}",
        f"- 日期硬闸时区：{date_gate['timezone']}",
        f"- 北京时间当天：{date_gate['beijing_date']}",
        f"- 评分板块：{payload['board']['name']}（{payload['board']['code']}）",
        f"- 股票数量：{payload['stock_count']}只",
        f"- 分数解释：{payload['score_interpretation']}",
        f"- 预测模式：{payload['forecast_mode']}",
        f"- 预测期限：{payload['forecast_horizon']}",
        f"- 报告完整性：{delivery['status']}",
        f"- 固定明细：{delivery['contribution_row_count']}条"
        f"（每只30条，16＋10＋4）",
        f"- 股票名称来源：{payload['data']['stock_name_source']}",
        f"- 预测优势验证："
        f"{payload['model'].get('metadata', {}).get('predictive_validation', 'UNKNOWN')}",
        f"- 正式模型文件：{payload['model_file']['path']}",
        f"- 正式模型文件SHA-256：{payload['model_file']['sha256']}",
        f"- 模型来源回测SHA-256：{payload['model_file']['source_backtest_sha256']}",
        "",
        "## 三体系融合参数",
        "",
        "| 评分体系 | 权重 |",
        "|---|---:|",
    ]
    top_level_weights = payload["ranking"][0]["fusion"]["top_level_weights"]
    for item_name, weight in top_level_weights.items():
        lines.append(
            f"| {item_name} | {float(weight):.4f}% |"
        )
    lines.extend(
        [
            "",
            "## 完整排名与总分拆解",
            "",
            "| 板块排名 | 全市场排名 | 全市场分位 | 股票名称 | 股票代码 | 综合总分 | "
            "三体系加权基础分 | 三体系共振加分 | 三体系分歧扣分 | "
            "大牛线撑压版 | 飞龙在天 | 庄家资金监控 | 综合结论 |",
            "|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["ranking"]:
        formula_scores = row["formula_scores"]
        fusion = row["fusion"]
        lines.append(
            f"| {row['rank']} | {row['market_rank']} | "
            f"{float(row['market_percentile']):.2f}% | {row['name']} | "
            f"{row['symbol']} | {row['score']:.4f} | "
            f"{float(fusion['base_score']):.4f} | "
            f"{float(fusion['resonance_bonus']):.4f} | "
            f"{float(fusion['disagreement_penalty']):.4f} | "
            f"{float(formula_scores[BIG_BULL_FORMULA]):.4f} | "
            f"{float(formula_scores[FEILONG_FORMULA]):.4f} | "
            f"{float(formula_scores[DEALER_FORMULA]):.4f} | "
            f"{row['conclusion']} |"
        )
    lines.extend(
        [
            "",
            "## 固定30项完整明细",
            "",
            "以下逐股完整展示大牛线撑压版16项、飞龙在天10项、"
            "庄家资金监控4项；不增加其他评分项目。",
        ]
    )
    for row in payload["ranking"]:
        formula_scores = row["formula_scores"]
        fusion = row["fusion"]
        lines.extend(
            [
                "",
                f"### {row['rank']}. {row['name']}（{row['symbol']}）",
                "",
                f"- 板块排名：{row['rank']}；全市场排名：{row['market_rank']}；"
                f"全市场分位：{float(row['market_percentile']):.2f}%",
                f"- 综合总分：{row['score']:.4f}",
                f"- 三体系加权基础分：{float(fusion['base_score']):.4f}",
                f"- 三体系共振加分：{float(fusion['resonance_bonus']):.4f}",
                f"- 三体系分歧扣分：{float(fusion['disagreement_penalty']):.4f}",
                f"- 大牛线撑压版：{float(formula_scores[BIG_BULL_FORMULA]):.4f}",
                f"- 飞龙在天：{float(formula_scores[FEILONG_FORMULA]):.4f}",
                f"- 庄家资金监控：{float(formula_scores[DEALER_FORMULA]):.4f}",
                f"- 综合结论：{row['conclusion']}",
                "",
                "| 体系 | 序号 | 子系统/输出 | 原始值 | 横截面百分位 | "
                "可靠性调整后百分位 | 体系信息可靠性 | 体系内权重 | 体系内贡献 | 体系权重 | 逐项基础贡献 | "
                "零权重/审计原因 |",
                "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
            ]
        )
        for item in row["contributions"]:
            lines.append(
                f"| {item['formula']} | {item['number']} | {item['name']} | "
                f"{_display_number(item.get('raw_value'))} | "
                f"{_display_number(item.get('percentile'))} | "
                f"{_display_number(item.get('effective_percentile'))} | "
                f"{_display_number(item.get('system_reliability'))} | "
                f"{_display_number(item.get('local_weight'))} | "
                f"{_display_number(item.get('local_contribution'))} | "
                f"{_display_number(item.get('system_weight'))} | "
                f"{_display_number(item.get('base_contribution'))} | "
                f"{item.get('forced_zero_reason') or '有效参与评分'} |"
            )
    lines.extend(
        [
            "",
            "## 使用边界",
            "",
            "总分＝三体系加权基础分＋三体系共振加分－三体系分歧扣分，"
            "并限制在0至100分。固定30项只在所属体系内部形成三套子分，"
            "再按三体系权重融合，不引入其他评分项目。",
            (
            "本结果的综合分不是上涨概率；"
            if payload.get("research_only")
            else "本结果仅在正式模型预测状态为PREDICTIVE_PASS时生成；"
        )
            + "其中方向结论是固定30项的规则型结构预测，不构成收益承诺或交易指令。",
        ]
    )
    return "\n".join(lines) + "\n"


def eligible_current_symbols(
    symbols: list[str],
    bars: dict[str, list[dict[str, Any]]],
) -> list[str]:
    """Keep stocks with enough history for the longest 213-day current feature."""
    return [symbol for symbol in symbols if len(bars[symbol]) >= 260]


def run_current_scoring(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in CURRENT_SCORE_ARTIFACTS:
        (output_dir / name).unlink(missing_ok=True)
    weights_path = Path(args.weights_file).resolve()
    research_structural = bool(getattr(args, "research_structural", False))
    if research_structural:
        model_payload = None
        model = None
        model_source_path = Path(__file__).resolve()
    else:
        model_payload, model = load_formal_weights(weights_path)
        model_source_path = weights_path
    stock_names = load_tdx_stock_names()
    board_symbols, board_path = load_board_symbols(
        args.board_code,
        args.board_file,
    )
    tq = initialize_tq()
    try:
        universe = tq.get_stock_list(market="23")
        benchmark_symbols = sorted({
            symbol
            for symbol in universe
            if isinstance(symbol, str)
            and symbol.endswith((".SH", ".SZ"))
            and day_path(symbol).is_file()
        })
        reference_symbols = merge_scoring_universe(
            benchmark_symbols,
            board_symbols,
            args.max_stocks,
        )
        symbols = merge_fetch_symbols(reference_symbols, board_symbols)
        bars = {symbol: read_day_file(day_path(symbol)) for symbol in symbols}
        symbols = eligible_current_symbols(symbols, bars)
        bars = {symbol: bars[symbol] for symbol in symbols}
        big_maps, big_errors = fetch_formula_history(
            tq,
            BIG_BULL_FORMULA,
            symbols,
            (
                "主趋势线",
                "流通市值",
                "OUTPUT4",
                "OUTPUT6",
                "OUTPUT9",
                "支撑一",
                "支撑二",
                "压力一",
                "压力二",
            ),
            args.count,
            1,
            args.batch_size,
        )
        feilong_maps, feilong_errors = fetch_formula_history(
            tq,
            FEILONG_FORMULA,
            symbols,
            ("OUTPUT3", "OUTPUT4", "OUTPUT5", "OUTPUT6", "波", "段"),
            args.count,
            1,
            args.batch_size,
        )
        dealer_maps, dealer_errors = fetch_formula_history(
            tq,
            DEALER_FORMULA,
            symbols,
            ("OUTPUT3", "OUTPUT4", "控盘程度", "控盘度"),
            args.count,
            1,
            args.batch_size,
        )
        complete_symbols = sorted(
            symbol
            for symbol in symbols
            if symbol in big_maps
            and symbol in feilong_maps
            and symbol in dealer_maps
            and big_maps[symbol]
            and feilong_maps[symbol]
            and dealer_maps[symbol]
        )
        feature_frame, observation_errors = build_current_feature_frame(
            complete_symbols,
            bars,
            big_maps,
            feilong_maps,
            dealer_maps,
            args.count,
        )
        reference_complete = sorted(set(reference_symbols) & set(complete_symbols))
        if len(reference_complete) < max(250, int(len(reference_symbols) * 0.7)):
            raise RuntimeError("固定评分母体有效股票不足")
        latest_frame, score_date = latest_broad_feature_frame(
            feature_frame,
            stock_count=len(reference_complete),
            minimum_fraction=0.7,
        )
        date_gate = enforce_current_scoring_date(score_date)
        if research_structural:
            model_payload, model = build_research_model_for_frame(
                latest_frame,
                reference_complete,
            )
        if not isinstance(model_payload, dict) or not isinstance(model, dict):
            raise RuntimeError("综合评分模型未完成构建")
        scored = score_feature_frame(
            latest_frame,
            model,
            reference_symbols=reference_complete,
        )
        reference_scores = scored[
            scored["symbol"].isin(reference_complete)
        ]["score"].to_numpy(dtype=float)
        scored["market_rank"] = scored["score"].map(
            lambda value: int(1 + np.sum(reference_scores > float(value)))
        )
        scored["market_percentile"] = scored["market_rank"].map(
            lambda rank: market_percentile_from_rank(
                int(rank),
                len(reference_scores),
            )
        )
        if board_symbols is not None:
            scored = scored[scored["symbol"].isin(board_symbols)].copy()
            missing = sorted(set(board_symbols) - set(scored["symbol"]))
            if missing:
                raise RuntimeError(
                    "板块成分未全部进入统一评分日：" + ",".join(missing)
                )
        scored["rank"] = (
            scored["score"].rank(method="min", ascending=False).astype(int)
        )
        scored = scored.sort_values(
            ["rank", "symbol"],
            ascending=[True, True],
            ignore_index=True,
        )
        ranking: list[dict[str, Any]] = []
        contribution_rows: list[dict[str, Any]] = []
        for row in scored.to_dict("records"):
            symbol = str(row["symbol"])
            stock_name = stock_names.get(symbol.split(".", 1)[0], "").strip()
            if not stock_name:
                raise RuntimeError(f"股票名称缺失：{symbol}")
            ranking_row = {
                "rank": int(row["rank"]),
                "market_rank": int(row["market_rank"]),
                "market_percentile": round(float(row["market_percentile"]), 8),
                "date": row["date"],
                "symbol": symbol,
                "name": stock_name,
                "score": round(float(row["score"]), 8),
                "formula_scores": row["formula_scores"],
                "top_level_items": row["top_level_items"],
                "fusion": row["fusion"],
                "contributions": row["contributions"],
            }
            ranking_row["conclusion"] = current_score_conclusion(ranking_row)
            ranking.append(ranking_row)
            for item in row["contributions"]:
                contribution_rows.append(
                    {
                        "rank": ranking_row["rank"],
                        "date": ranking_row["date"],
                        "symbol": ranking_row["symbol"],
                        "stock_name": ranking_row["name"],
                        "total_score": ranking_row["score"],
                        "base_score": row["fusion"]["base_score"],
                        "resonance_bonus": row["fusion"]["resonance_bonus"],
                        "disagreement_penalty": row["fusion"][
                            "disagreement_penalty"
                        ],
                        **item,
                    }
                )
        weights_source = str(model_payload.get("source_backtest", ""))
        payload = {
            "schema": "THREE_FORMULA_COMPOSITE_CURRENT_SCORE_V1",
            "status": "CLEAN_PASS",
            "scoring_mode": (
                "RESEARCH_STRUCTURAL" if research_structural else "PREDICTIVE_MODEL"
            ),
            "research_only": research_structural,
            "prediction_authorized": not research_structural,
            "directional_forecast_authorized": True,
            "score_is_probability": False,
            "forecast_mode": "RULE_BASED_STRUCTURAL_FORECAST",
            "forecast_horizon": "未来5至10个交易日",
            "forecast_is_probability": False,
            "score_interpretation": (
                "固定参考母体横截面结构分位，不是上涨概率"
            ),
            "generated_at": shanghai_now().isoformat(timespec="seconds"),
            "score_date": score_date,
            "scoring_identity": build_scoring_identity(
                reference_complete,
                score_date,
                model,
            ),
            "date_gate": date_gate,
            "stock_count": len(ranking),
            "board": (
                {
                    "name": args.board_name,
                    "code": args.board_code,
                    "path": str(board_path),
                    "sha256": sha256_file(board_path),
                    "constituent_count": len(board_symbols),
                }
                if board_symbols is not None and board_path is not None
                else None
            ),
            "model_file": {
                "path": str(model_source_path),
                "sha256": sha256_file(model_source_path),
                "source_backtest": weights_source,
                "source_backtest_sha256": model_payload.get(
                    "source_backtest_sha256"
                ),
                "source_backtest_hash_verified": (
                    bool(weights_source)
                    and Path(weights_source).is_file()
                    and sha256_file(Path(weights_source))
                    == model_payload.get("source_backtest_sha256")
                ),
            },
            "model": model,
            "data": {
                "universe_count": len(reference_complete),
                "fetched_symbol_count": len(complete_symbols),
                "stock_name_source": str(STOCK_NAME_INDEX),
                "formula_errors": big_errors + feilong_errors + dealer_errors,
                "observation_errors": observation_errors,
            },
            "ranking": ranking,
            "runtime_seconds": round(time.time() - started, 2),
        }
        payload["delivery_validation"] = validate_current_score_delivery(payload)
        ranking_json = output_dir / "三公式综合评分最新排名.json"
        ranking_csv = output_dir / "三公式综合评分最新排名.csv"
        contribution_csv = output_dir / "三公式综合评分30项贡献明细.csv"
        report_path = output_dir / "三公式综合评分最新排名报告.md"
        ranking_json.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        write_csv(
            ranking_csv,
            [
                {
                    "rank": row["rank"],
                    "market_rank": row["market_rank"],
                    "market_percentile": row["market_percentile"],
                    "date": row["date"],
                    "name": row["name"],
                    "symbol": row["symbol"],
                    "score": row["score"],
                    "base_score": row["fusion"]["base_score"],
                    "resonance_bonus": row["fusion"]["resonance_bonus"],
                    "disagreement_penalty": row["fusion"][
                        "disagreement_penalty"
                    ],
                    BIG_BULL_FORMULA: row["formula_scores"][BIG_BULL_FORMULA],
                    FEILONG_FORMULA: row["formula_scores"][FEILONG_FORMULA],
                    DEALER_FORMULA: row["formula_scores"][DEALER_FORMULA],
                    "conclusion": row["conclusion"],
                }
                for row in ranking
            ],
        )
        write_csv(contribution_csv, contribution_rows)
        report_path.write_text(render_current_score_report(payload), encoding="utf-8")
        payload["artifacts"] = {
            "ranking_json": str(ranking_json),
            "ranking_csv": str(ranking_csv),
            "contributions_csv": str(contribution_csv),
            "report": str(report_path),
        }
        print(json.dumps(payload, ensure_ascii=False))
        return payload
    finally:
        try:
            tq.close()
        except Exception:
            pass


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    for path in (*FORMULA_SOURCES, TQ_INIT_PATH):
        if not path.is_file():
            raise FileNotFoundError(path)
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    tq = initialize_tq()
    official_transfer: dict[str, Any] = {"status": "BLOCKED", "error": "not_run"}
    try:
        universe = tq.get_stock_list(market="23")
        symbols = [
            symbol
            for symbol in universe
            if isinstance(symbol, str)
            and symbol.endswith((".SH", ".SZ"))
            and day_path(symbol).is_file()
        ]
        if args.max_stocks:
            symbols = symbols[: args.max_stocks]
        local_day_bars = {symbol: read_day_file(day_path(symbol)) for symbol in symbols}
        symbols = [
            symbol
            for symbol in symbols
            if len(local_day_bars[symbol]) >= args.count + 240
        ]
        bars, adjusted_bar_errors = fetch_adjusted_market_history(
            tq,
            symbols,
            count=args.count + 260,
            batch_size=max(12, args.batch_size * 4),
        )
        symbols = [
            symbol
            for symbol in symbols
            if symbol in bars and len(bars[symbol]) >= args.count + 240
        ]
        bars = {symbol: bars[symbol] for symbol in symbols}
        big_maps, big_errors = fetch_formula_history(
            tq,
            BIG_BULL_FORMULA,
            symbols,
            (
                "主趋势线",
                "流通市值",
                "OUTPUT4",
                "OUTPUT6",
                "OUTPUT9",
                "支撑一",
                "支撑二",
                "压力一",
                "压力二",
            ),
            args.count,
            1,
            args.batch_size,
        )
        feilong_maps, feilong_errors = fetch_formula_history(
            tq,
            FEILONG_FORMULA,
            symbols,
            ("OUTPUT3", "OUTPUT4", "OUTPUT5", "OUTPUT6", "波", "段"),
            args.count,
            1,
            args.batch_size,
        )
        dealer_maps, dealer_errors = fetch_dealer_history_official(
            tq,
            symbols,
            bars,
            ("OUTPUT3", "OUTPUT4", "控盘程度", "控盘度"),
            args.count,
        )
        complete_symbols = [
            symbol
            for symbol in symbols
            if symbol in big_maps
            and symbol in feilong_maps
            and symbol in dealer_maps
            and len(big_maps[symbol]) >= args.count * 0.8
            and len(feilong_maps[symbol]) >= args.count * 0.8
            and len(dealer_maps[symbol]) >= args.count * 0.8
        ]
        raw_frame, observation_errors, tradability_audit = build_observations(
            complete_symbols,
            bars,
            big_maps,
            feilong_maps,
            dealer_maps,
            args.count,
            args.rebalance_days,
            args.cost_bps,
            args.minimum_entry_amount,
        )
        point_in_time_universe_audit = {
            "source": "current_tdx_market_23_with_signal_date_bar_availability",
            "checks": {
                "signal_date_bar_availability_applied": True,
                "historical_constituent_snapshots_available": False,
                "historical_delisting_membership_available": False,
            },
            "complete": False,
            "incomplete_reason": "当前通达信接口返回现时成分，缺少逐日历史成分与退市成员快照",
        }
        frame, catalog, information_diagnostics, _ = prepare_backtest_frame(
            raw_frame,
            subsystem_catalog(),
        )
        try:
            model, evidence, predictions = fit_weights(frame, catalog)
        except OptimizationBlocked as exc:
            generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
            latest_date = max(
                (records[-1]["date"] for records in bars.values() if records),
                default="",
            )
            summary_path = output_dir / "三公式综合评分回测证据.json"
            report_path = output_dir / "三公式综合评分回测报告.md"
            trades_path = output_dir / "三公式综合评分样本外明细.csv"
            dates_path = output_dir / "三公式综合评分样本外分期.csv"
            weights_path = output_dir / "三公式综合评分正式模型.json"
            model = build_structural_fallback_model(
                catalog,
                information_diagnostics,
                reason=str(exc),
            )
            structural_checks = {
                "fixed_30_subsystems": len(model["subsystem_weights"]) == 30,
                "three_systems_present": set(model["system_weights"])
                == set(FORMULAS),
                "system_weights_sum_100": abs(
                    sum(model["system_weights"].values()) - 100.0
                )
                < 1e-6,
                "fusion_terms_present": (
                    model["fusion"]["resonance_bonus"] > 0
                    and model["fusion"]["disagreement_penalty"] > 0
                ),
            }
            validate_hierarchical_model(model)
            payload = {
                "schema": "THREE_FORMULA_COMPOSITE_SCORING_BACKTEST_V1",
                "status": "BLOCKED",
                "methodology_version": METHODOLOGY_VERSION,
                "generated_at": generated_at,
                "model_mode": "AUDITED_STRUCTURAL",
                "predictive_validation": {
                    "status": "BLOCKED",
                    "reason": str(exc),
                    "optimization_evidence": exc.evidence,
                },
                "method": {
                    "universe": "本机通达信沪深300成分股",
                    "history_count": args.count,
                    "rebalance_days": args.rebalance_days,
                    "entry": "统一前复权序列中信号日后下一交易日开盘",
                    "price_adjustment": "front（特征与收益标签统一前复权）",
                    "horizons": [3, 5, 10],
                    "cost_bps": args.cost_bps,
                    "minimum_entry_amount": args.minimum_entry_amount,
                    "optimization": "体系内模型、体系级融合与共振参数分层训练；验证期三段稳定性选型；独立测试",
                    "model_constraints": "三体系分别归一为100分，体系权重总和100且单体系不低于10%，无信息项强制0",
                },
                "data": {
                    "stock_count": len(complete_symbols),
                    "observation_count": len(frame),
                    "latest_date": latest_date,
                    "formula_errors": big_errors + feilong_errors + dealer_errors,
                    "observation_errors": adjusted_bar_errors + observation_errors,
                    "information_diagnostics": information_diagnostics,
                    "point_in_time_universe_audit": point_in_time_universe_audit,
                    "tradability_audit": tradability_audit,
                    "formula_sources": [
                        {
                            "path": str(path),
                            "sha256": sha256_file(path),
                            "size": path.stat().st_size,
                        }
                        for path in FORMULA_SOURCES
                    ],
                },
                "subsystem_audit": catalog,
                "model": model,
                "validation_gates": {
                    "status": "BLOCKED",
                    "checks": structural_checks,
                    "failed": [
                        "scientific_weight_candidate_not_found",
                        *[
                            key
                            for key, value in structural_checks.items()
                            if not value
                        ],
                    ],
                },
                "official_tdx": {
                    "formula_execution_status": "PASS",
                    "dealer_formula_interface": (
                        "formula_set_data_info+formula_zb"
                    ),
                    "dealer_formula_error_count": len(dealer_errors),
                    "backtest_transfer": {
                        "status": "NOT_APPLICABLE",
                        "reason": "审计型结构模型不声明预测交易策略",
                    },
                },
                "runtime_seconds": round(time.time() - started, 2),
            }
            summary_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report_path.write_text(
                render_structural_report(payload),
                encoding="utf-8",
            )
            write_csv(trades_path, [])
            write_csv(dates_path, [])
            formal_model = build_blocked_weights_payload(
                summary_path,
                generated_at=generated_at,
                reason=str(exc),
                optimization_evidence=exc.evidence,
            )
            weights_path.write_text(
                json.dumps(formal_model, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            synced_model_state = None
            if args.sync_model_state_to:
                synced_model_state = sync_formal_model_state(
                    weights_path,
                    Path(args.sync_model_state_to),
                )
            installed_path = None
            payload["artifacts"] = {
                "summary": str(summary_path),
                "report": str(report_path),
                "test_rows": str(trades_path),
                "test_dates": str(dates_path),
                "model": str(weights_path),
                "installed_model": (
                    str(installed_path) if installed_path else None
                ),
                "synced_model_state": synced_model_state,
            }
            print(json.dumps(payload, ensure_ascii=False))
            return payload
        split = evidence.pop("split_masks")
        test_metrics_full = evidence["test_metrics"]
        equal_metrics = equal_weight_metrics(frame, catalog, split["test"])
        gates = validation_gates(
            len(complete_symbols),
            frame,
            test_metrics_full,
            equal_metrics,
            model,
            point_in_time_universe_available=bool(
                point_in_time_universe_audit["complete"]
            ),
            tradability_constraints_complete=bool(tradability_audit["complete"]),
        )
        if args.send_tdx:
            official_transfer = send_official_tq_backtest(
                tq, test_metrics_full["selected_rows"]
            )
        test_rows = test_metrics_full.pop("selected_rows")
        test_date_metrics = test_metrics_full.pop("date_metrics")
        predictive_status = (
            "PREDICTIVE_PASS"
            if gates["status"] == "PASS"
            and (not args.send_tdx or official_transfer["status"] == "PASS")
            else "PREDICTIVE_REJECTED"
        )
        latest_date = max(
            (records[-1]["date"] for records in bars.values() if records),
            default="",
        )
        payload = {
            "schema": "THREE_FORMULA_COMPOSITE_SCORING_BACKTEST_V1",
            "status": predictive_status,
            "methodology_version": METHODOLOGY_VERSION,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "predictive_validation": {
                "status": predictive_status,
                "decision_rule": "全部预声明验证闸通过才允许PREDICTIVE_PASS，否则PREDICTIVE_REJECTED",
                "failed_gates": gates["failed"],
            },
            "method": {
                "universe": "本机通达信沪深300成分股",
                "history_count": args.count,
                "rebalance_days": args.rebalance_days,
                "entry": "统一前复权序列中信号日后下一交易日开盘",
                "price_adjustment": "front（特征与收益标签统一前复权）",
                "horizons": [3, 5, 10],
                "cost_bps": args.cost_bps,
                "minimum_entry_amount": args.minimum_entry_amount,
                "target": "0.25*3日收益+0.35*5日收益+0.40*10日收益+0.10*5日MFE-0.20*5日MAE绝对值",
                "optimization": "三套体系分别训练体系内模型；融合层只接收三套子分并选择体系权重、共振系数和分歧系数；验证期三段稳定性选型，训练+验证重拟合，独立测试",
                "model_constraints": "30项仅在所属体系内部归一；三体系权重总和100且单体系不低于10%；重复、常量、不可回溯和无区分度项强制0",
            },
            "data": {
                "stock_count": len(complete_symbols),
                "observation_count": len(frame),
                "latest_date": latest_date,
                "symbols": complete_symbols,
                "formula_errors": big_errors + feilong_errors + dealer_errors,
                "observation_errors": adjusted_bar_errors + observation_errors,
                "information_diagnostics": information_diagnostics,
                "point_in_time_universe_audit": point_in_time_universe_audit,
                "tradability_audit": tradability_audit,
                "formula_sources": [
                    {
                        "path": str(path),
                        "sha256": sha256_file(path),
                        "size": path.stat().st_size,
                    }
                    for path in FORMULA_SOURCES
                ],
            },
            "model": model,
            "backtest": {
                **evidence,
                "equal_weight_test_metrics": equal_metrics,
                "test_date_metrics": test_date_metrics,
            },
            "validation_gates": gates,
            "official_tdx": {
                "formula_execution_status": "PASS",
                "tq_init_path": str(TQ_INIT_PATH),
                "backtest_transfer": official_transfer,
            },
            "runtime_seconds": round(time.time() - started, 2),
        }
        summary_path = output_dir / "三公式综合评分回测证据.json"
        report_path = output_dir / "三公式综合评分回测报告.md"
        trades_path = output_dir / "三公式综合评分样本外明细.csv"
        dates_path = output_dir / "三公式综合评分样本外分期.csv"
        weights_path = output_dir / "三公式综合评分正式模型.json"
        summary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        report_path.write_text(render_report(payload), encoding="utf-8")
        write_csv(trades_path, test_rows)
        write_csv(dates_path, test_date_metrics)
        model_payload = build_formal_weights_payload(
            summary_path,
            generated_at=payload["generated_at"],
            predictive_status=predictive_status,
            model=model,
            validation_gates=gates,
            oos_row_count=len(test_rows),
            oos_date_count=len(test_date_metrics),
        )
        weights_path.write_text(
            json.dumps(model_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        synced_model_state = None
        if args.sync_model_state_to:
            synced_model_state = sync_formal_model_state(
                weights_path,
                Path(args.sync_model_state_to),
            )
        installed_path = None
        if predictive_status == "PREDICTIVE_PASS" and args.install_weights:
            installed_path = Path(args.install_weights).resolve()
            installed_path.parent.mkdir(parents=True, exist_ok=True)
            installed_path.write_text(
                json.dumps(model_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        payload["artifacts"] = {
            "summary": str(summary_path),
            "report": str(report_path),
            "test_rows": str(trades_path),
            "test_dates": str(dates_path),
            "model": str(weights_path),
            "installed_model": str(installed_path) if installed_path else None,
            "synced_model_state": synced_model_state,
        }
        print(json.dumps(payload, ensure_ascii=False))
        return payload
    finally:
        try:
            tq.close()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="三公式综合评分系统真实历史回测与权重优化")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--count", type=int, default=None)
    parser.add_argument("--max-stocks", type=int, default=300)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--rebalance-days", type=int, default=5)
    parser.add_argument("--cost-bps", type=float, default=30.0)
    parser.add_argument("--minimum-entry-amount", type=float, default=10_000_000.0)
    parser.add_argument("--send-tdx", action="store_true")
    parser.add_argument("--install-weights", default="")
    parser.add_argument("--sync-model-state-from", default="")
    parser.add_argument("--sync-model-state-to", default="")
    parser.add_argument("--score-only", action="store_true")
    parser.add_argument("--research-structural", action="store_true")
    parser.add_argument("--board-name", default="")
    parser.add_argument("--board-code", default="")
    parser.add_argument("--board-file", default="")
    parser.add_argument(
        "--weights-file",
        default=str(
            Path(__file__).resolve().parents[1]
            / "assets"
            / "three_formula_composite_weights.json"
        ),
    )
    args = parser.parse_args()
    if args.count is None:
        args.count = 260 if args.score_only else 520
    if args.sync_model_state_from:
        payload = run_formal_model_state_sync(args)
        return 0 if payload["status"] in {
            "CLEAN_PASS",
            "PREDICTIVE_REJECTED",
        } else 2
    if not args.score_only and args.count < 360:
        raise SystemExit("--count不能少于360")
    if args.score_only and args.count < 220:
        raise SystemExit("--count不能少于220")
    if args.max_stocks and args.max_stocks < 250:
        raise SystemExit("--max-stocks不能少于250")
    try:
        payload = run_current_scoring(args) if args.score_only else run(args)
    except FormalModelUnavailable as exc:
        weights_path = Path(args.weights_file).resolve()
        model_state: dict[str, Any] = {}
        try:
            candidate = json.loads(weights_path.read_text(encoding="utf-8"))
            if isinstance(candidate, dict):
                predictive = candidate.get("predictive_validation")
                model_state = {
                    "status": candidate.get("status"),
                    "methodology_version": candidate.get("methodology_version"),
                    "predictive_status": (
                        predictive.get("status")
                        if isinstance(predictive, dict)
                        else None
                    ),
                    "model_is_null": candidate.get("model") is None,
                    "sha256": sha256_file(weights_path),
                }
        except (OSError, UnicodeError, json.JSONDecodeError):
            model_state = {}
        payload = {
            "schema": "THREE_FORMULA_COMPOSITE_CURRENT_SCORE_V1",
            "status": "BLOCKED",
            "error_code": "FORMAL_MODEL_UNAVAILABLE",
            "error": str(exc),
            "model_state_path": str(weights_path),
            "model_state": model_state,
            "artifacts": {},
        }
        print(json.dumps(payload, ensure_ascii=False))
    except ScoringDateBlocked as exc:
        payload = {
            "schema": "THREE_FORMULA_COMPOSITE_CURRENT_SCORE_V1",
            "status": "BLOCKED",
            "generated_at": shanghai_now().isoformat(timespec="seconds"),
            "error": str(exc),
            "date_gate": exc.evidence,
            "artifacts": {},
        }
        print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["status"] in {
        "CLEAN_PASS",
        "PREDICTIVE_PASS",
        "PREDICTIVE_REJECTED",
    } else 2


if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
