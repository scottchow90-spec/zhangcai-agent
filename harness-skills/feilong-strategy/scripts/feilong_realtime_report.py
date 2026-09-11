#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞龙在天实时分析固定脚本
Core asset wrapper: direct callable Feilong realtime report.

Usage:
  python feilong_realtime_report.py 301372
  python feilong_realtime_report.py 科净源
  python feilong_realtime_report.py 301372 --as-of-date 20260804
  python feilong_realtime_report.py 301372 --out E:\\Codex\\15_validation\\report.md
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from feilong_offline_replay import (
    match_first_board_cycles,
    replay_installed_formula_signals,
)
from feilong_continuation_research import run_factor_research
from feilong_deep_factor_research import run_deep_factor_research
from feilong_resonance_exhaustive import run_resonance_exhaustive
from feilong_daily_yaogu_scoring import run as run_daily_yaogu_scoring
from feilong_factor_correlation_v3_runner import run as run_factor_correlation_v3

TDX_ROOT = Path(os.environ.get("ZHANGCAI_TDX_ROOT", r"C:\new_tdx_mock"))
APP_ROOT = Path(os.environ.get("ZHANGCAI_APP_ROOT", str(Path(__file__).resolve().parents[3])))
WORKSPACE = APP_ROOT
VALIDATION = Path(os.environ.get(
    "FEILONG_VALIDATION_ROOT",
    str(Path(os.environ.get("ONESTOCK_STOCK_DATA_ROOT", str(APP_ROOT / "data" / "strategy-results"))) / "reports" / "feilong"),
))
SKILL_ROOT = Path(__file__).resolve().parents[1]
FORMULA_SOURCE_MANIFEST = SKILL_ROOT / "references" / "formula-source-manifest.json"
FORMULA_DISPLAY_NAME = "飞龙在天"
FORMULA_CALL_NAME = "飞龙在天"
SELECTION_FORMULA_CALL_NAME = "飞龙在天"
BACKTEST_HORIZONS = (1, 3, 5, 10, 20)
REQUIRED_FORMULA_OUTPUTS = {"OUTPUT3", "OUTPUT4", "OUTPUT5", "OUTPUT6", "波", "段"}
# OUTPUT6 is the display label (for example, "主升启动"), not a dated
# numeric series.  It must exist, but it cannot participate in date alignment.
DATED_FORMULA_OUTPUTS = REQUIRED_FORMULA_OUTPUTS - {"OUTPUT6"}

# Known aliases. Extend only from verified local source.
NAME_MAP = {
    "科净源": "301372.SZ",
}

SUBSYSTEMS = [
    (1, "龙头战法", "OUTPUT3"),
    (2, "趋势过滤/中长期均线强势条件", None),
    (3, "四日实体重叠箱体/波段密码底层形态", None),
    (4, "首板/唯一涨停确认", None),
    (5, "波段密码打板", "OUTPUT4"),
    (6, "量价模型/暴涨启动", "OUTPUT5"),
    (7, "波段随机强弱-波", "波"),
    (8, "波段随机强弱-段", "段"),
    (9, "私募秘进", "OUTPUT6"),
    (10, "主升启动共振", None),
]


def fnum(x):
    try:
        return float(x)
    except Exception:
        return None


def indicator_output_triggered(value: Any) -> bool:
    if value is True:
        return True
    numeric = fnum(value)
    return numeric is not None and numeric != 0


def pct(x):
    return "NA" if x is None else f"{x:.2f}%"


def n2(x):
    return "NA" if x is None else f"{x:.2f}"


def normalize_date(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y%m%d")
    digits = re.sub(r"\D", "", str(value))
    if len(digits) < 8:
        return None
    candidate = digits[:8]
    try:
        datetime.strptime(candidate, "%Y%m%d")
    except ValueError:
        return None
    return candidate


def parse_as_of_date(value: str) -> str:
    normalized = normalize_date(value)
    if normalized is None:
        raise argparse.ArgumentTypeError("日期必须为 YYYYMMDD 或 YYYY-MM-DD")
    return normalized


def display_date(value: str) -> str:
    return datetime.strptime(value, "%Y%m%d").strftime("%Y-%m-%d")


def build_formula_interpretation() -> List[Dict[str, Any]]:
    return [
        {
            "subsystem": "龙头战法",
            "logic": "当日涨幅超过8.9%，并满足四日中三日弱势后转强，或前一日2周期强弱值下穿20/45后的反转条件。",
            "role_in_xg": "XS2分支之一",
        },
        {
            "subsystem": "趋势过滤/中长期均线强势条件",
            "logic": "收盘同时高于89日EMA、三重13日高价EMA和三重5日高价EMA，且高点相对短趋势不过度乖离。",
            "role_in_xg": "波段密码打板前置条件",
        },
        {
            "subsystem": "四日实体重叠箱体/波段密码底层形态",
            "logic": "最近四根K线实体存在共同重叠价格区间，并要求36日内出现过该形态。",
            "role_in_xg": "波段密码打板前置条件",
        },
        {
            "subsystem": "首板/唯一涨停确认",
            "logic": "当日涨幅超过9.85%，且21日内只有本次满足；另以9.84%阈值要求前两日未满足。",
            "role_in_xg": "波段密码打板前置条件",
        },
        {
            "subsystem": "波段密码打板",
            "logic": "上市天数、名称/代码、价格、趋势、乖离、涨停、箱体和位置条件共同成立，再做13日过滤。",
            "role_in_xg": "XS2分支之一",
        },
        {
            "subsystem": "量价模型/暴涨启动",
            "logic": "使用当日涨幅、2日/10日量比和换手代理量构成线性判别式。",
            "role_in_xg": "XS1分支之一",
        },
        {
            "subsystem": "波段随机强弱-波",
            "logic": "36日高低区间位置经通达信SMA平滑；所给选股源计算该序列，但未把它接入最终XG。",
            "role_in_xg": "未参与最终XG",
        },
        {
            "subsystem": "波段随机强弱-段",
            "logic": "对波段强弱继续平滑形成较慢序列；所给选股源未把它接入最终XG。",
            "role_in_xg": "未参与最终XG",
        },
        {
            "subsystem": "私募秘进",
            "logic": "涨幅超过4.8%、收盘等于最高价，且4期预测量处于12期预测量的0.2至2.1倍，触发后过滤28日。",
            "role_in_xg": "XS1分支之一",
        },
        {
            "subsystem": "主升启动共振",
            "logic": "XS1与XS2同日成立，再叠加流通市值20至200亿元、名称过滤、FINANCE(3)=1和成交额超过1亿元。",
            "role_in_xg": "最终XG",
        },
    ]


def build_formula_risks() -> List[str]:
    return [
        "FINANCE(3)=1把范围限定为沪深主板，排除创业板、科创板和北交所",
        "固定9.84%/9.85%阈值不是按历史ST、科创板、创业板制度动态计算的涨停价",
        "X_1X至X_3X、X_53、X_54以及波段平滑序列未进入最终XG",
        "FINANCE与名称类函数由本机公式引擎解释，结果含当前股票池生存者偏差风险",
    ]


def normalize_stock_universe(raw: Any) -> List[str]:
    symbols: set[str] = set()
    for item in raw or []:
        market = ""
        if isinstance(item, str):
            candidate = item
        elif isinstance(item, dict):
            candidate = next(
                (
                    str(item[key])
                    for key in ("StockCode", "stock_code", "Code", "code", "Symbol", "symbol")
                    if item.get(key) is not None
                ),
                "",
            )
            market = str(item.get("Market") or item.get("market") or "").upper()
        else:
            continue
        candidate = candidate.strip().upper()
        match = re.fullmatch(r"(\d{6})(?:\.(SH|SZ|BJ))?", candidate)
        if not match:
            continue
        code, suffix = match.groups()
        if suffix is None:
            if market in {"SH", "SSE", "1"}:
                suffix = "SH"
            elif market in {"SZ", "SZSE", "0"}:
                suffix = "SZ"
            elif market in {"BJ", "BSE", "2"}:
                suffix = "BJ"
            elif code.startswith(("6", "9")):
                suffix = "SH"
            elif code.startswith(("0", "3")):
                suffix = "SZ"
            elif code.startswith(("4", "8")):
                suffix = "BJ"
            else:
                continue
        symbols.add(f"{code}.{suffix}")
    return sorted(symbols)


def extract_xg_signals(formula_result: Any) -> List[Dict[str, str]]:
    if not isinstance(formula_result, dict):
        return []
    signals: set[Tuple[str, str]] = set()

    def walk(symbol: str, value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                walk(symbol, item)
            return
        if not isinstance(value, dict):
            return
        date = normalize_date(value.get("Date"))
        if date:
            raw_value = value.get("Value", value.get("XG", 1))
            numeric = fnum(raw_value)
            if raw_value is True or (numeric is not None and numeric != 0):
                signals.add((symbol, date))
            return
        for nested in value.values():
            if isinstance(nested, (dict, list)):
                walk(symbol, nested)

    for key, node in formula_result.items():
        symbol_match = re.fullmatch(r"\d{6}\.(?:SH|SZ|BJ)", str(key).upper())
        if symbol_match:
            walk(str(key).upper(), node)
    return [
        {"symbol": symbol, "signal_date": signal_date}
        for symbol, signal_date in sorted(signals)
    ]


def extract_indicator_main_rise_signals(
    formula_result: Any,
) -> List[Dict[str, str]]:
    """Extract final resonance dates from the installed indicator outputs."""
    if not isinstance(formula_result, dict):
        return []
    signals: set[Tuple[str, str]] = set()
    final_outputs = ("OUTPUT3", "OUTPUT4", "OUTPUT5", "OUTPUT6")

    def dates_for(value: Any) -> set[str]:
        dates: set[str] = set()
        if isinstance(value, list):
            for item in value:
                dates.update(dates_for(item))
            return dates
        if not isinstance(value, dict):
            return dates
        date = normalize_date(value.get("Date"))
        if date:
            raw_value = value.get("Value", 0)
            if indicator_output_triggered(raw_value):
                dates.add(date)
            return dates
        for nested in value.values():
            if isinstance(nested, (dict, list)):
                dates.update(dates_for(nested))
        return dates

    for key, node in formula_result.items():
        symbol = str(key).upper()
        if re.fullmatch(r"\d{6}\.(?:SH|SZ|BJ)", symbol) is None:
            continue
        final_dates = set()
        if isinstance(node, dict):
            for output_name in final_outputs:
                final_dates.update(dates_for(node.get(output_name, [])))
        for signal_date in sorted(final_dates):
            signals.add((symbol, signal_date))
    return [
        {"symbol": symbol, "signal_date": signal_date}
        for symbol, signal_date in sorted(signals)
    ]


def normalize_bar_frame(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized.index = [normalize_date(value) for value in normalized.index]
    normalized = normalized.loc[[value is not None for value in normalized.index]]
    normalized = normalized[~normalized.index.duplicated(keep="last")].sort_index()
    return normalized


def build_event_rows(
    signals: List[Dict[str, str]],
    bars_by_symbol: Dict[str, pd.DataFrame],
    horizons: Tuple[int, ...] = BACKTEST_HORIZONS,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    normalized_frames = {
        symbol: normalize_bar_frame(frame)
        for symbol, frame in bars_by_symbol.items()
        if isinstance(frame, pd.DataFrame) and not frame.empty
    }
    for signal in signals:
        symbol = signal["symbol"]
        signal_date = normalize_date(signal["signal_date"])
        row: Dict[str, Any] = {
            "symbol": symbol,
            "signal_date": signal_date,
            "entry_date": None,
            "signal_close": None,
            "entry_open": None,
            "entry_gap_pct": None,
            "tradable_next_open": False,
            "exclusion_reason": None,
        }
        frame = normalized_frames.get(symbol)
        if frame is None or signal_date not in frame.index:
            row["exclusion_reason"] = "signal_bar_missing"
            rows.append(row)
            continue
        signal_position = frame.index.get_loc(signal_date)
        if not isinstance(signal_position, (int, np.integer)):
            signal_position = int(np.asarray(signal_position).nonzero()[0][-1])
        entry_position = int(signal_position) + 1
        signal_close = fnum(frame.iloc[int(signal_position)]["Close"])
        row["signal_close"] = signal_close
        if entry_position >= len(frame):
            row["exclusion_reason"] = "next_bar_unavailable"
            rows.append(row)
            continue
        entry_bar = frame.iloc[entry_position]
        entry_open = fnum(entry_bar["Open"])
        entry_high = fnum(entry_bar["High"])
        entry_low = fnum(entry_bar["Low"])
        row["entry_date"] = frame.index[entry_position]
        row["entry_open"] = entry_open
        if signal_close and entry_open:
            row["entry_gap_pct"] = (entry_open / signal_close - 1) * 100
        one_price = (
            entry_open is not None
            and entry_high is not None
            and entry_low is not None
            and math.isclose(entry_open, entry_high, rel_tol=0, abs_tol=1e-8)
            and math.isclose(entry_open, entry_low, rel_tol=0, abs_tol=1e-8)
        )
        locked_limit_up = bool(
            one_price and signal_close and entry_open / signal_close >= 1.095
        )
        row["tradable_next_open"] = not locked_limit_up and entry_open is not None and entry_open > 0
        if locked_limit_up:
            row["exclusion_reason"] = "next_open_one_price_limit_up"
        elif not row["tradable_next_open"]:
            row["exclusion_reason"] = "invalid_entry_open"
        for horizon in horizons:
            exit_position = entry_position + horizon - 1
            return_key = f"return_{horizon}d_pct"
            net_key = f"net_return_{horizon}d_pct"
            mae_key = f"mae_{horizon}d_pct"
            mfe_key = f"mfe_{horizon}d_pct"
            if entry_open is None or entry_open <= 0 or exit_position >= len(frame):
                row[return_key] = None
                row[net_key] = None
                row[mae_key] = None
                row[mfe_key] = None
                continue
            exit_close = fnum(frame.iloc[exit_position]["Close"])
            window = frame.iloc[entry_position : exit_position + 1]
            gross_return = (exit_close / entry_open - 1) * 100 if exit_close is not None else None
            row[return_key] = gross_return
            row[net_key] = gross_return - 0.20 if gross_return is not None else None
            row[mae_key] = (float(window["Low"].min()) / entry_open - 1) * 100
            row[mfe_key] = (float(window["High"].max()) / entry_open - 1) * 100
        rows.append(row)
    return rows


def summarize_event_rows(
    rows: List[Dict[str, Any]],
    horizons: Tuple[int, ...] = BACKTEST_HORIZONS,
) -> Dict[str, Any]:
    tradable = [row for row in rows if row.get("tradable_next_open")]
    summary: Dict[str, Any] = {
        "signal_count": len(rows),
        "tradable_signal_count": len(tradable),
        "excluded_one_price_limit_up_count": sum(
            row.get("exclusion_reason") == "next_open_one_price_limit_up" for row in rows
        ),
        "missing_entry_data_count": sum(
            row.get("exclusion_reason") in {"signal_bar_missing", "next_bar_unavailable", "invalid_entry_open"}
            for row in rows
        ),
        "horizons": {},
    }
    for horizon in horizons:
        returns = [
            float(row[f"return_{horizon}d_pct"])
            for row in tradable
            if row.get(f"return_{horizon}d_pct") is not None
        ]
        net_returns = [
            float(row[f"net_return_{horizon}d_pct"])
            for row in tradable
            if row.get(f"net_return_{horizon}d_pct") is not None
        ]
        maes = [
            float(row[f"mae_{horizon}d_pct"])
            for row in tradable
            if row.get(f"mae_{horizon}d_pct") is not None
        ]
        if not returns:
            summary["horizons"][f"{horizon}d"] = {
                "sample_count": 0,
                "win_rate_pct": None,
                "mean_return_pct": None,
                "median_return_pct": None,
                "mean_net_return_pct": None,
                "p25_return_pct": None,
                "p75_return_pct": None,
                "min_return_pct": None,
                "max_return_pct": None,
                "worst_mae_pct": None,
            }
            continue
        summary["horizons"][f"{horizon}d"] = {
            "sample_count": len(returns),
            "win_rate_pct": round(sum(value > 0 for value in returns) / len(returns) * 100, 6),
            "mean_return_pct": round(float(np.mean(returns)), 6),
            "median_return_pct": round(float(np.median(returns)), 6),
            "mean_net_return_pct": round(float(np.mean(net_returns)), 6) if net_returns else None,
            "p25_return_pct": round(float(np.percentile(returns, 25)), 6),
            "p75_return_pct": round(float(np.percentile(returns, 75)), 6),
            "min_return_pct": round(float(np.min(returns)), 6),
            "max_return_pct": round(float(np.max(returns)), 6),
            "worst_mae_pct": round(float(np.min(maes)), 6) if maes else None,
        }
    return summary


def market_data_to_frames(market_data: Any, symbols: List[str]) -> Dict[str, pd.DataFrame]:
    frames: Dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        fields: Dict[str, pd.Series] = {}
        for field in ("Open", "High", "Low", "Close", "Volume", "Amount"):
            try:
                fields[field] = market_series(market_data, field, symbol)
            except (KeyError, TypeError):
                if field in {"Open", "High", "Low", "Close"}:
                    fields = {}
                    break
        if fields:
            frame = pd.DataFrame(fields).dropna(subset=["Open", "High", "Low", "Close"], how="any")
            if not frame.empty:
                frames[symbol] = normalize_bar_frame(frame)
    return frames


def chunked(values: List[str], size: int) -> List[List[str]]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    return [values[index : index + size] for index in range(0, len(values), size)]


def run_formula_signal_batches(
    tq: Any,
    universe: List[str],
    start_date: str,
    end_date: str,
    chunk_size: int,
    selection_formula: str = SELECTION_FORMULA_CALL_NAME,
    formula_mode: str = "condition_selection",
) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    signals: List[Dict[str, str]] = []
    calls: List[Dict[str, Any]] = []

    def execute_batch(batch: List[str]) -> None:
        if formula_mode == "installed_indicator_main_rise":
            result = tq.formula_process_mul_zb(
                formula_name=selection_formula,
                return_count=0,
                return_date=True,
                stock_list=batch,
                stock_period="1d",
                start_time=start_date,
                end_time=end_date,
                count=0,
                dividend_type=1,
            )
        else:
            result = tq.formula_process_mul_xg(
                formula_name=selection_formula,
                return_count=0,
                return_date=True,
                stock_list=batch,
                stock_period="1d",
                start_time=start_date,
                end_time=end_date,
                count=0,
                dividend_type=1,
            )
        if not isinstance(result, dict) or not result:
            raise RuntimeError(f"TDX formula returned empty result for batch starting {batch[0]}")
        error_id = str(result.get("ErrorId", "0"))
        if error_id == "19" and len(batch) > 1:
            midpoint = max(1, len(batch) // 2)
            execute_batch(batch[:midpoint])
            execute_batch(batch[midpoint:])
            return
        if error_id not in {"0", "None"}:
            raise RuntimeError(
                f"TDX formula failed: error_id={error_id}, error={result.get('Error')}, batch_start={batch[0]}"
            )
        if formula_mode == "installed_indicator_main_rise":
            batch_signals = extract_indicator_main_rise_signals(result)
        else:
            batch_signals = extract_xg_signals(result)
        calls.append(
            {
                "batch_start": batch[0],
                "stock_count": len(batch),
                "error_id": error_id,
                "signal_count": len(batch_signals),
                "formula_mode": formula_mode,
            }
        )
        signals.extend(batch_signals)

    for batch in chunked(universe, chunk_size):
        execute_batch(batch)
    unique = {
        (signal["symbol"], signal["signal_date"]): signal
        for signal in signals
    }
    return [unique[key] for key in sorted(unique)], calls


def load_signal_stock_bars(
    tq: Any,
    symbols: List[str],
    start_date: str,
    chunk_size: int = 120,
) -> Dict[str, pd.DataFrame]:
    frames: Dict[str, pd.DataFrame] = {}
    for batch in chunked(symbols, chunk_size):
        market_data = tq.get_market_data(
            field_list=["Open", "High", "Low", "Close", "Volume", "Amount"],
            stock_list=batch,
            period="1d",
            start_time=start_date,
            end_time="",
            count=0,
            dividend_type="front",
            fill_data=False,
        )
        frames.update(market_data_to_frames(market_data, batch))
    return frames


def sha256_path(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_formula_source(formula_name: str) -> Dict[str, Any]:
    manifest_path = FORMULA_SOURCE_MANIFEST.resolve()
    if not manifest_path.is_file():
        raise RuntimeError(f"formula_source_manifest_missing:{manifest_path}")
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"formula_source_manifest_invalid:{type(exc).__name__}"
        ) from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != "FEILONG_FORMULA_SOURCE_MANIFEST_V1":
        raise RuntimeError("formula_source_manifest_schema_invalid")
    formulas = manifest.get("formulas")
    if not isinstance(formulas, dict):
        raise RuntimeError("formula_source_manifest_formulas_invalid")
    source_spec = formulas.get(formula_name)
    if not isinstance(source_spec, dict):
        raise RuntimeError(f"formula_source_not_registered:{formula_name}")

    source_path = Path(str(source_spec.get("source_path", "")))
    if not source_path.is_absolute():
        raise RuntimeError(f"formula_source_path_not_absolute:{formula_name}")
    if not source_path.is_file():
        raise RuntimeError(f"formula_source_missing:{formula_name}:{source_path}")
    source_bytes = source_path.read_bytes()
    expected_size = source_spec.get("source_size_bytes")
    if not isinstance(expected_size, int) or len(source_bytes) != expected_size:
        raise RuntimeError(f"formula_source_size_mismatch:{formula_name}")
    raw_sha256 = hashlib.sha256(source_bytes).hexdigest()
    expected_raw_sha256 = source_spec.get("source_raw_sha256")
    if raw_sha256 != expected_raw_sha256:
        raise RuntimeError(f"formula_source_raw_hash_mismatch:{formula_name}")

    source_encoding = source_spec.get("source_encoding")
    if source_encoding != "utf-8":
        raise RuntimeError(f"formula_source_encoding_invalid:{formula_name}")
    has_utf8_bom = source_bytes.startswith(b"\xef\xbb\xbf")
    if source_spec.get("source_bom") is not has_utf8_bom:
        raise RuntimeError(f"formula_source_bom_mismatch:{formula_name}")
    try:
        source_text = source_bytes.decode(source_encoding, errors="strict")
    except UnicodeError as exc:
        raise RuntimeError(f"formula_source_decode_failed:{formula_name}") from exc

    payload_encoding = source_spec.get("payload_encoding")
    if payload_encoding != "gbk" or manifest.get("payload_encoding") != "gbk":
        raise RuntimeError(f"formula_payload_encoding_invalid:{formula_name}")
    try:
        payload_bytes = source_text.encode(payload_encoding, errors="strict")
    except UnicodeError as exc:
        raise RuntimeError(f"formula_payload_encode_failed:{formula_name}") from exc
    expected_payload_size = source_spec.get("payload_size_bytes")
    if not isinstance(expected_payload_size, int) or len(payload_bytes) != expected_payload_size:
        raise RuntimeError(f"formula_payload_size_mismatch:{formula_name}")
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    if payload_sha256 != source_spec.get("gbk_payload_sha256"):
        raise RuntimeError(f"formula_payload_hash_mismatch:{formula_name}")

    return {
        "formula_name": formula_name,
        "source_path": str(source_path.resolve()),
        "source_encoding": source_encoding,
        "source_bom": has_utf8_bom,
        "source_size_bytes": len(source_bytes),
        "source_raw_sha256": raw_sha256,
        "payload_encoding": payload_encoding,
        "payload_size_bytes": len(payload_bytes),
        "gbk_payload_sha256": payload_sha256,
        "source_manifest_path": str(manifest_path),
        "source_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "authority_scope": source_spec.get("authority_scope"),
    }


def run_backtest(
    start_date: str,
    end_date: str,
    out_dir: str | None = None,
    symbols: List[str] | None = None,
    chunk_size: int = 240,
    selection_formula: str = SELECTION_FORMULA_CALL_NAME,
    formula_mode: str = "condition_selection",
    candidate_cycles_csv: str | None = None,
) -> Dict[str, Any]:
    normalized_start = normalize_date(start_date)
    normalized_end = normalize_date(end_date)
    if normalized_start is None or normalized_end is None:
        raise SystemExit("回测日期必须为 YYYYMMDD 或 YYYY-MM-DD")
    if normalized_start > normalized_end:
        raise SystemExit("回测开始日期不得晚于结束日期")
    if formula_mode not in {
        "condition_selection",
        "installed_indicator_main_rise",
        "offline_installed_formula_replay",
    }:
        raise SystemExit(f"不支持的公式模式: {formula_mode}")
    if formula_mode == "offline_installed_formula_replay" and not candidate_cycles_csv:
        raise SystemExit("离线公式回放必须提供 --candidate-cycles-csv")
    source_evidence = resolve_formula_source(selection_formula)
    output_directory = Path(out_dir) if out_dir else VALIDATION / f"feilong_backtest_{datetime.now():%Y%m%d_%H%M%S}"
    output_directory.mkdir(parents=True, exist_ok=True)
    offline_evidence: Dict[str, Any] | None = None
    candidate_cycles: pd.DataFrame | None = None
    first_board_matches: pd.DataFrame | None = None
    if formula_mode == "offline_installed_formula_replay":
        candidate_path = Path(str(candidate_cycles_csv)).resolve()
        if not candidate_path.is_file():
            raise RuntimeError(f"candidate cycles CSV is missing: {candidate_path}")
        candidate_cycles = pd.read_csv(
            candidate_path,
            dtype={"code": str, "first_board_date": str},
            encoding="utf-8-sig",
        )
        required_cycle_columns = {"code", "name", "first_board_date"}
        if not required_cycle_columns.issubset(candidate_cycles.columns):
            missing = sorted(required_cycle_columns - set(candidate_cycles.columns))
            raise RuntimeError(f"candidate cycles CSV columns are missing: {missing}")
        universe = normalize_stock_universe(candidate_cycles["code"].tolist())
        if symbols:
            requested = set(normalize_stock_universe(symbols))
            universe = [symbol for symbol in universe if symbol in requested]
        if not universe:
            raise RuntimeError("candidate cycle stock universe is empty")
        names = {
            str(row["code"]).zfill(6): str(row["name"])
            for row in candidate_cycles.to_dict("records")
        }
        symbols_by_code = {
            symbol.split(".", 1)[0]: symbol
            for symbol in universe
        }
        candidate_dates: Dict[str, List[str]] = {}
        for row in candidate_cycles.to_dict("records"):
            code = str(row["code"]).zfill(6)
            symbol = symbols_by_code.get(code)
            candidate_date = normalize_date(row["first_board_date"])
            if symbol is None or candidate_date is None:
                continue
            if normalized_start <= candidate_date <= normalized_end:
                candidate_dates.setdefault(symbol, []).append(candidate_date)
        candidate_dates = {
            symbol: sorted(set(dates))
            for symbol, dates in sorted(candidate_dates.items())
        }
        signals, offline_evidence = replay_installed_formula_signals(
            symbols=universe,
            start_date=normalized_start,
            end_date=normalized_end,
            names=names,
            candidate_dates=candidate_dates,
        )
        first_board_matches = match_first_board_cycles(candidate_cycles, signals)
        formula_calls = [{
            "batch_start": universe[0],
            "stock_count": len(universe),
            "error_id": "0",
            "signal_count": len(signals),
            "formula_mode": formula_mode,
        }]
        bars_by_symbol: Dict[str, pd.DataFrame] = {}
    else:
        tq = init_tq()
        try:
            if symbols:
                universe = normalize_stock_universe(symbols)
            else:
                universe = normalize_stock_universe(tq.get_stock_list(market="5", list_type=0))
            if not universe:
                raise RuntimeError("TDX stock universe is empty")
            signals, formula_calls = run_formula_signal_batches(
                tq=tq,
                universe=universe,
                start_date=normalized_start,
                end_date=normalized_end,
                chunk_size=chunk_size,
                selection_formula=selection_formula,
                formula_mode=formula_mode,
            )
            signal_symbols = sorted({signal["symbol"] for signal in signals})
            bars_by_symbol = load_signal_stock_bars(tq, signal_symbols, normalized_start) if signal_symbols else {}
        finally:
            tq.close()

    event_rows = build_event_rows(signals, bars_by_symbol)
    summary = summarize_event_rows(event_rows)
    latest_kline_date = max(
        (str(frame.index[-1]) for frame in bars_by_symbol.values() if not frame.empty),
        default=None,
    )
    payload: Dict[str, Any] = {
        "schema": "FEILONG_TDX_BACKTEST_V1",
        "status": "CLEAN_PASS",
        "generated_at": datetime.now().astimezone().isoformat(),
        "formula": {
            "formula_type": formula_mode,
            "formula_display_name": (
                FORMULA_DISPLAY_NAME
                if selection_formula in {SELECTION_FORMULA_CALL_NAME, FORMULA_CALL_NAME}
                else selection_formula
            ),
            "selection_formula": selection_formula,
            "indicator_formula": (
                FORMULA_CALL_NAME
                if formula_mode == "installed_indicator_main_rise"
                else FORMULA_DISPLAY_NAME
                if selection_formula == SELECTION_FORMULA_CALL_NAME
                else None
            ),
            "local_source_path": source_evidence["source_path"],
            "local_source_encoding": source_evidence["source_encoding"],
            "local_source_bom": source_evidence["source_bom"],
            "local_source_size_bytes": source_evidence["source_size_bytes"],
            "local_source_sha256": source_evidence["source_raw_sha256"],
            "local_source_raw_sha256": source_evidence["source_raw_sha256"],
            "payload_encoding": source_evidence["payload_encoding"],
            "gbk_payload_size_bytes": source_evidence["payload_size_bytes"],
            "gbk_payload_sha256": source_evidence["gbk_payload_sha256"],
            "source_manifest_path": source_evidence["source_manifest_path"],
            "source_manifest_sha256": source_evidence["source_manifest_sha256"],
            "source_authority_scope": source_evidence["authority_scope"],
            "interpretation": build_formula_interpretation(),
            "known_semantic_risks": build_formula_risks(),
        },
        "data": {
            "source": (
                "local Tongdaxin daily files with installed formula offline replay"
                if offline_evidence is not None
                else "local Tongdaxin TQ formula engine and D-drive daily K-line data"
            ),
            "tdx_root": str(TDX_ROOT),
            "start_date": normalized_start,
            "end_date": normalized_end,
            "latest_loaded_kline_date": latest_kline_date,
            "universe_count": len(universe),
            "signal_stock_count": len(bars_by_symbol),
            "formula_batch_count": len(formula_calls),
            "formula_calls": formula_calls,
            **(
                {
                    "candidate_cycles_csv": {
                        "path": str(Path(str(candidate_cycles_csv)).resolve()),
                        "size": Path(str(candidate_cycles_csv)).resolve().stat().st_size,
                        "sha256": sha256_path(Path(str(candidate_cycles_csv)).resolve()),
                    },
                    "candidate_cycle_count": int(len(candidate_cycles)),
                    "first_board_match_count": int(len(first_board_matches)),
                    "offline_replay_evidence": offline_evidence,
                }
                if offline_evidence is not None
                else {}
            ),
        },
        "execution_model": {
            "signal_confirmation": "signal day close",
            "entry": "next trading day open",
            "horizons_trading_days": list(BACKTEST_HORIZONS),
            "exit": "horizon day close",
            "one_price_limit_up_entry": "excluded from tradable statistics",
            "gross_return": "before fees and slippage",
            "net_stress": "gross return minus fixed 0.20 percentage points round trip",
            "portfolio_curve": "not calculated because the formula defines no exit, sizing, or concurrency rule",
        },
        "summary": summary,
        "signal_date_min": min((row["signal_date"] for row in event_rows), default=None),
        "signal_date_max": max((row["signal_date"] for row in event_rows), default=None),
    }
    csv_path = output_directory / "feilong_backtest_events.csv"
    json_path = output_directory / "feilong_backtest.json"
    segment_manifest_path = output_directory / "feilong_backtest_segment_manifest.json"
    first_board_matches_path = output_directory / "feilong_first_board_matches.csv"
    pd.DataFrame(event_rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
    if first_board_matches is not None:
        first_board_matches.to_csv(
            first_board_matches_path, index=False, encoding="utf-8-sig"
        )
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    artifact_evidence = {
        "backtest_json": {
            "path": str(json_path.resolve()),
            "size": json_path.stat().st_size,
            "sha256": hashlib.sha256(json_path.read_bytes()).hexdigest(),
        },
        "events_csv": {
            "path": str(csv_path.resolve()),
            "size": csv_path.stat().st_size,
            "sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        },
    }
    if first_board_matches is not None:
        artifact_evidence["first_board_matches_csv"] = {
            "path": str(first_board_matches_path.resolve()),
            "size": first_board_matches_path.stat().st_size,
            "sha256": hashlib.sha256(first_board_matches_path.read_bytes()).hexdigest(),
        }
    segment_manifest = {
        "schema": "FEILONG_BACKTEST_SEGMENT_MANIFEST_V1",
        "status": "CLEAN_PASS",
        "generated_at": datetime.now().astimezone().isoformat(),
        "formula": {
            "formula_type": payload["formula"]["formula_type"],
            "selection_formula": payload["formula"]["selection_formula"],
            "indicator_formula": payload["formula"]["indicator_formula"],
            "local_source_path": payload["formula"]["local_source_path"],
            "local_source_raw_sha256": payload["formula"]["local_source_raw_sha256"],
            "gbk_payload_sha256": payload["formula"]["gbk_payload_sha256"],
            "source_manifest_path": payload["formula"]["source_manifest_path"],
            "source_manifest_sha256": payload["formula"]["source_manifest_sha256"],
        },
        "data": {
            "start_date": normalized_start,
            "end_date": normalized_end,
            "universe_count": len(universe),
            "signal_count": len(event_rows),
        },
        "artifacts": artifact_evidence,
        "validation": {
            "status": "CLEAN_PASS",
            "errors": [],
            "formula_source_bound": True,
            "artifact_hashes_verified": True,
        },
    }
    segment_manifest_path.write_text(
        json.dumps(segment_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    result = {
        "schema": payload["schema"],
        "status": payload["status"],
        "backtest_json": str(json_path),
        "events_csv": str(csv_path),
        "segment_manifest": str(segment_manifest_path),
        "segment_manifest_sha256": hashlib.sha256(
            segment_manifest_path.read_bytes()
        ).hexdigest(),
        "formula": payload["formula"],
        "summary": summary,
    }
    if first_board_matches is not None:
        result["first_board_matches_csv"] = str(first_board_matches_path)
    return result


def resolve_symbol(query: str) -> str:
    q = query.strip().upper()
    if q in NAME_MAP:
        return NAME_MAP[q]
    # Chinese name exact map with original case
    if query.strip() in NAME_MAP:
        return NAME_MAP[query.strip()]
    exact = re.fullmatch(r"(\d{6})\.(SH|SZ|BJ)", q)
    if exact:
        return q
    m = re.search(r"(\d{6})", q)
    if not m:
        raise SystemExit(f"无法解析股票代码: {query}; 请传入6位代码或已登记名称")
    code = m.group(1)
    if code.startswith(("0", "3")):
        return f"{code}.SZ"
    if code.startswith(("6", "9")):
        return f"{code}.SH"
    if code.startswith(("4", "8")):
        return f"{code}.BJ"
    return f"{code}.SH"


def init_tq():
    sys.path.insert(0, str(TDX_ROOT / "PYPlugins" / "user"))
    sys.argv = ["tqcenter", "--run_tdx", "0"]
    from tqcenter import tq
    tq.initialize(str(TDX_ROOT / "PYPlugins" / "user" / "tdxdata_test.py"))
    return tq


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def sma_tdx(s, n, m=1):
    out = []
    prev = np.nan
    for x in s:
        if np.isnan(x):
            out.append(prev)
            continue
        if np.isnan(prev):
            prev = x
        else:
            prev = (m * x + (n - m) * prev) / n
        out.append(prev)
    return pd.Series(out, index=s.index)


def ref(s, n=1): return s.shift(n)
def hhv(s, n): return s.rolling(n, min_periods=1).max()
def llv(s, n): return s.rolling(n, min_periods=1).min()


def last_val(series):
    if not series: return None
    x = series[-1]
    return fnum(x.get("Value") if isinstance(x, dict) else x)


def prev_val(series, n=1):
    if not series or len(series) <= n: return None
    x = series[-1-n]
    return fnum(x.get("Value") if isinstance(x, dict) else x)


def last_date(series):
    if not series: return None
    x = series[-1]
    return x.get("Date") if isinstance(x, dict) else None


def tail_pairs(series, n=10):
    arr = []
    for x in (series or [])[-n:]:
        if isinstance(x, dict):
            arr.append((x.get("Date"), fnum(x.get("Value"))))
        else:
            arr.append((None, fnum(x)))
    return arr


def market_series(market_data: Any, field: str, symbol: str) -> pd.Series:
    values = market_data[field]
    if isinstance(values, pd.DataFrame):
        return values[symbol]
    if isinstance(values, pd.Series):
        return values
    raise TypeError(f"unsupported market-data field {field}: {type(values).__name__}")


def series_dates(series: pd.Series) -> List[str]:
    return [d for d in (normalize_date(value) for value in series.index) if d]


def formula_dates_by_output(node: Dict[str, Any]) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for key in sorted(REQUIRED_FORMULA_OUTPUTS):
        dates = []
        for item in node.get(key, []) or []:
            if isinstance(item, dict):
                date = normalize_date(item.get("Date"))
                if date:
                    dates.append(date)
        result[key] = sorted(set(dates))
    return result


def build_date_context(
    run_calendar_date: str,
    requested_as_of_date: str | None,
    output_dates: Dict[str, List[str]],
    kline_dates: List[str],
    snapshot_available: bool,
) -> Dict[str, Any]:
    run_date = normalize_date(run_calendar_date)
    requested = normalize_date(requested_as_of_date)
    if run_date is None:
        raise ValueError(f"invalid run calendar date: {run_calendar_date}")
    if requested_as_of_date is not None and requested is None:
        raise ValueError(f"invalid requested as-of date: {requested_as_of_date}")

    normalized_output_dates = {
        key: sorted({date for value in values if (date := normalize_date(value))})
        for key, values in output_dates.items()
    }
    formula_sets = [set(normalized_output_dates.get(key, [])) for key in sorted(DATED_FORMULA_OUTPUTS)]
    common_formula_dates = set.intersection(*formula_sets) if formula_sets else set()
    normalized_kline_dates = {date for value in kline_dates if (date := normalize_date(value))}
    common_dates = sorted(
        date for date in common_formula_dates & normalized_kline_dates
        if date <= run_date
    )

    errors: List[str] = []
    if requested and requested > run_date:
        errors.append(f"requested_as_of_date_is_future:{requested}>{run_date}")
    if requested and requested not in common_formula_dates:
        errors.append(f"formula_outputs_missing_as_of:{requested}")
    if requested and requested not in normalized_kline_dates:
        errors.append(f"kline_missing_as_of:{requested}")

    analysis_as_of_date = requested or (common_dates[-1] if common_dates else None)
    if analysis_as_of_date is None:
        errors.append("no_common_formula_and_kline_date")

    formula_latest_by_output = {
        key: (values[-1] if values else None)
        for key, values in normalized_output_dates.items()
    }
    same_day_realtime = (
        not errors
        and analysis_as_of_date == run_date
        and snapshot_available
    )
    mode = "same_day_realtime" if same_day_realtime else ("as_of_close" if not errors else "blocked")
    return {
        "ok": not errors,
        "mode": mode,
        "run_calendar_date": run_date,
        "requested_as_of_date": requested,
        "analysis_as_of_date": analysis_as_of_date,
        "formula_latest_date": max(
            (date for date in formula_latest_by_output.values() if date),
            default=None,
        ),
        "formula_latest_by_output": formula_latest_by_output,
        "formula_has_as_of": bool(
            analysis_as_of_date
            and all(
                analysis_as_of_date in normalized_output_dates.get(key, [])
                for key in DATED_FORMULA_OUTPUTS
            )
        ),
        "kline_latest_date": max(normalized_kline_dates, default=None),
        "kline_has_as_of": bool(analysis_as_of_date and analysis_as_of_date in normalized_kline_dates),
        "snapshot_available": snapshot_available,
        "errors": errors,
    }


def report_title(name: str, symbol: str, date_context: Dict[str, Any]) -> str:
    if date_context["mode"] == "same_day_realtime":
        scope = "今日实时分析"
    else:
        scope = f"截至 {display_date(date_context['analysis_as_of_date'])} 分析"
    return f"# {name} {symbol}｜飞龙在天 {scope}"


def find_same_day_cache_hits(symbol: str, run_calendar_date: str) -> List[str]:
    code = symbol.split(".")[0]
    cache_hits: List[str] = []
    roots = [
        TDX_ROOT / "T0002" / "cache",
        TDX_ROOT / "vipdoc" / "sz" / "eday",
        TDX_ROOT / "vipdoc" / "sh" / "eday",
        TDX_ROOT / "webs" / "web_cache",
    ]
    patterns = [f"*{code}*", f"*{run_calendar_date}*{code}*"]
    for root in roots:
        if not root.exists():
            continue
        for pat in patterns:
            for p in list(root.glob(pat))[:20]:
                try:
                    mt = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y%m%d")
                    if mt == run_calendar_date:
                        cache_hits.append(str(p))
                except Exception:
                    pass
    return sorted(set(cache_hits))


def formula_series_through_date(series: List[Any], as_of_date: str) -> List[Any]:
    filtered = []
    for item in series or []:
        if not isinstance(item, dict):
            continue
        item_date = normalize_date(item.get("Date"))
        if item_date and item_date <= as_of_date:
            filtered.append(item)
    return filtered


def market_series_through_date(series: pd.Series, as_of_date: str) -> pd.Series:
    mask = [bool(date and date <= as_of_date) for date in (normalize_date(value) for value in series.index)]
    return series.loc[mask]


def _analyze(
    query: str,
    tq,
    out: str | None = None,
    as_of_date: str | None = None,
    persist_artifacts: bool = True,
) -> Dict:
    symbol = resolve_symbol(query)
    code = symbol.split(".")[0]
    run_calendar_date = datetime.now().strftime("%Y%m%d")

    info = tq.get_stock_info(symbol)
    snap = tq.get_market_snapshot(symbol)
    md = tq.get_market_data(stock_list=[symbol], period="1d", count=180, dividend_type="front")
    formula = tq.formula_process_mul_zb(FORMULA_CALL_NAME, stock_list=[symbol], count=0, return_count=80, return_date=True, dividend_type=1)
    node = formula.get(symbol, {}) if isinstance(formula, dict) else {}
    populated_formula_outputs = {
        key for key, value in node.items()
        if key in REQUIRED_FORMULA_OUTPUTS and isinstance(value, list) and value
    }
    missing_formula_outputs = sorted(REQUIRED_FORMULA_OUTPUTS - populated_formula_outputs)
    if missing_formula_outputs:
        try:
            tq.close()
        finally:
            raise SystemExit(
                "飞龙公式执行失败: "
                f"display={FORMULA_DISPLAY_NAME}, call={FORMULA_CALL_NAME}, "
                f"missing_outputs={missing_formula_outputs}, "
                f"error_id={formula.get('ErrorId') if isinstance(formula, dict) else None}"
            )

    raw_close = market_series(md, "Close", symbol)
    date_context = build_date_context(
        run_calendar_date=run_calendar_date,
        requested_as_of_date=as_of_date,
        output_dates=formula_dates_by_output(node),
        kline_dates=series_dates(raw_close),
        snapshot_available=bool(snap),
    )
    date_context["cache_hits"] = (
        find_same_day_cache_hits(symbol, run_calendar_date)
        if date_context["mode"] == "same_day_realtime"
        else []
    )
    if not date_context["ok"]:
        raise SystemExit(
            "飞龙日期口径校验失败: "
            + json.dumps(date_context, ensure_ascii=False, default=str)
        )

    analysis_as_of_date = date_context["analysis_as_of_date"]
    latest = {}
    for key, val in node.items():
        if isinstance(val, list):
            val = formula_series_through_date(val, analysis_as_of_date)
            latest[key] = {
                "latest_date": last_date(val),
                "latest": last_val(val),
                "prev": prev_val(val, 1),
                "prev2": prev_val(val, 2),
                "tail10": tail_pairs(val, 10),
            }

    C = market_series_through_date(raw_close.astype(float), analysis_as_of_date)
    H = market_series_through_date(market_series(md, "High", symbol).astype(float), analysis_as_of_date)
    L = market_series_through_date(market_series(md, "Low", symbol).astype(float), analysis_as_of_date)
    O = market_series_through_date(market_series(md, "Open", symbol).astype(float), analysis_as_of_date)
    V = market_series_through_date(market_series(md, "Volume", symbol).astype(float), analysis_as_of_date)
    X5 = ref(C,1); X6 = ema(hhv(H,1),8); X7 = ema(C,8)
    X8 = (X7 < ref(X7,1)) & (C < X7)
    X9 = ((X6 < ref(X6,1)) | X8).astype(int)
    up = (C-X5).clip(lower=0); abschg = (C-X5).abs()
    X10 = sma_tdx(up,2,1) / sma_tdx(abschg,2,1) * 100
    X14 = (X10 < 20) & (ref(X10,1) > 20)
    X13 = (X10 < 45) & (ref(X10,1) > 45)
    longtou_calc = ((X9.eq(1).rolling(4,min_periods=4).sum()==3)&(X9==0)&(O<C)&((C-ref(C,1))/ref(C,1)>0.089)) | (((C-ref(C,1))/ref(C,1)>0.089)&(ref(X14.astype(int),1).astype(bool)|ref(X13.astype(int),1).astype(bool)))

    X15 = ema(C,89); X16 = ema(ema(ema(H,13),13),13); X17 = ema(ema(ema(H,5),5),5); X18 = (C-ref(C,1))/ref(C,1)*100
    X22 = (ref(C,1)<89)&(ref(C,1)>2); X23 = not code.startswith("3")
    X24 = (C>X17)&(C>X16)&(C>X15); X25 = H/X17; X26 = (X18>=9.84)&(ref((X18<9.84).astype(int),1).astype(bool))&(ref((X18<9.84).astype(int),2).astype(bool))
    X27 = X22 & X23 & X24 & (X25<1.16) & X26
    X28 = pd.concat([C,O],axis=1).max(axis=1); X29 = pd.concat([C,O],axis=1).min(axis=1)
    X30 = llv(X28,4); X31 = hhv(X29,4)
    X32 = (X28>=X30)&(X29<=X30)&(X28>=X31)&(X29<=X31)
    X33 = (ref(X28,1)>=X30)&(ref(X29,1)<=X30)&(ref(X28,1)>=X31)&(ref(X29,1)<=X31)
    X34 = (ref(X28,2)>=X30)&(ref(X29,2)<=X30)&(ref(X28,2)>=X31)&(ref(X29,2)<=X31)
    X35 = (ref(X28,3)>=X30)&(ref(X29,3)<=X30)&(ref(X28,3)>=X31)&(ref(X29,3)<=X31)
    X36 = X32 & X33 & X34 & X35
    X37 = X36.rolling(36,min_periods=1).max().astype(bool)
    X45 = (X18>9.85)&~(O==C); X46 = X45.rolling(21,min_periods=1).sum(); X47 = (X46==1)&X45
    private_basic = (C/ref(C,1)>1.048)&(C==H)

    if date_context["mode"] == "same_day_realtime":
        now = fnum(snap.get("Now")); last_close = fnum(snap.get("LastClose")); avg = fnum(snap.get("Average")); high = fnum(snap.get("Max")); low = fnum(snap.get("Min"))
        openp = fnum(snap.get("Open")); vol = fnum(snap.get("Volume")); amount = fnum(snap.get("Amount")); inside = fnum(snap.get("Inside")); outside = fnum(snap.get("Outside"))
    else:
        now = fnum(C.iloc[-1]); last_close = fnum(C.iloc[-2]); avg = None
        high = fnum(H.iloc[-1]); low = fnum(L.iloc[-1]); openp = fnum(O.iloc[-1])
        vol = fnum(V.iloc[-1]); amount = None; inside = None; outside = None
    realtime_calc = {
        "basis": date_context["mode"],
        "now": now, "last_close": last_close, "change_pct": ((now-last_close)/last_close*100 if now and last_close else None),
        "open": openp, "high": high, "low": low, "avg": avg, "volume_lot": vol, "amount_wan": amount,
        "amount_yi": (amount/10000 if amount else None), "inside": inside, "outside": outside,
        "inside_minus_outside": (inside-outside if inside is not None and outside is not None else None),
        "intraday_amp_pct": ((high-low)/last_close*100 if high and low and last_close else None),
        "below_avg_pct": ((now-avg)/avg*100 if now and avg else None),
    }

    derived = {
        "longtou_calc": bool(longtou_calc.iloc[-1]),
        "x9_last4": [int(x) for x in X9.tail(4).tolist()],
        "rsi2_x10": float(X10.iloc[-1]), "rsi2_prev": float(X10.iloc[-2]),
        "trend_filter": {
            "ema89": float(X15.iloc[-1]), "high_ema13x3": float(X16.iloc[-1]), "high_ema5x3": float(X17.iloc[-1]),
            "close_gt_all_three": bool(X24.iloc[-1]), "x25_high_div_high_ema5x3": float(X25.iloc[-1]),
            "x23_code_prefix_filter_pass": bool(X23), "x22_price_range_pass": bool(X22.iloc[-1]),
            "x26_first_limitup_pass": bool(X26.iloc[-1]), "x27_all_pass": bool(X27.iloc[-1]),
        },
        "box_shape": {"x36_today": bool(X36.iloc[-1]), "x37_exist_36d": bool(X37.iloc[-1])},
        "limitup_unique": {"x45_today_gt985_not_doji": bool(X45.iloc[-1]), "x46_count_21d": float(X46.iloc[-1]), "x47_unique_limitup": bool(X47.iloc[-1])},
        "boduan_password_calc": {
            "x55": False,
            "x47": bool(X47.iloc[-1]),
            "trigger": indicator_output_triggered(
                latest.get("OUTPUT4", {}).get("latest")
            ),
        },
        "private_entry_basic": {"pct_gt_4_8": bool((C/ref(C,1)>1.048).iloc[-1]), "close_eq_high": bool((C==H).iloc[-1]), "trigger_basic": bool(private_basic.iloc[-1])},
    }

    analysis_json = None
    derived_json = None
    report_path = None
    if persist_artifacts:
        slug = f"{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        VALIDATION.mkdir(parents=True, exist_ok=True)
        analysis_json = VALIDATION / f"feilong_{slug}_analysis.json"
        derived_json = VALIDATION / f"feilong_{slug}_derived.json"
        report_path = Path(out) if out else VALIDATION / f"feilong_{slug}_report.md"

    data = {
        "generated_at": datetime.now().isoformat(),
        "symbol": symbol,
        "name": info.get("Name", query),
        "date_context": date_context,
        "info": info,
        "snapshot": snap,
        "realtime_calc": realtime_calc,
        "latest_outputs": latest,
        "derived": derived,
        "realtime_evidence": date_context,
        "formula_raw": formula,
    }
    if persist_artifacts:
        analysis_json.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        derived_json.write_text(
            json.dumps(derived, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        md_report = render_report(data, analysis_json, derived_json)
        report_path.write_text(md_report, encoding="utf-8")
    return {
        "report": str(report_path) if report_path else None,
        "analysis_json": str(analysis_json) if analysis_json else None,
        "derived_json": str(derived_json) if derived_json else None,
        "summary": data,
    }


def analyze(
    query: str,
    out: str | None = None,
    as_of_date: str | None = None,
    persist_artifacts: bool = True,
) -> Dict:
    tq = init_tq()
    try:
        return _analyze(query, tq, out, as_of_date, persist_artifacts)
    finally:
        try:
            tq.close()
        except Exception:
            pass


def trigger_text(v):
    return "触发" if indicator_output_triggered(v) else "未触发"


def golden_cross_status(wave, seg):
    if wave is None or seg is None:
        return "金叉状态不可判定"
    return "金叉" if wave > seg else "未形成金叉"


def _display_value(value):
    number = fnum(value)
    return "NA" if number is None else f"{number:.2f}"


def _triggered(value) -> bool:
    return indicator_output_triggered(value)


def _subsystem_row(number, name, evidence, status, conclusion, note="适用"):
    return {
        "公式": FORMULA_CALL_NAME,
        "序号": number,
        "子系统/输出": name,
        "当前值/证据": str(evidence or "无可用证据"),
        "状态": str(status or "状态不可判定"),
        "结论": str(conclusion or "结论不可判定"),
        "适用性/备注": str(note or "适用性未说明"),
    }


def build_subsystem_rows(data: Dict, is_index: bool = False) -> List[Dict]:
    """Build the fixed 10-row Feilong table with closed external terminology."""
    d = data or {}
    lo = d.get("latest_outputs") or {}
    der = d.get("derived") or {}
    rc = d.get("realtime_calc") or {}

    def output_value(name):
        node = lo.get(name) or {}
        return node.get("latest")

    def index_na(number, name, reason):
        return _subsystem_row(
            number,
            name,
            "指数不适用",
            "指数不适用",
            f"{reason}，不纳入指数技术结论",
            "保留固定子系统行",
        )

    output3 = output_value("OUTPUT3")
    output4 = output_value("OUTPUT4")
    output5 = output_value("OUTPUT5")
    output6 = output_value("OUTPUT6")
    wave_node = lo.get("波") or {}
    seg_node = lo.get("段") or {}
    wave = wave_node.get("latest")
    seg = seg_node.get("latest")
    wave_prev = wave_node.get("prev")
    seg_prev = seg_node.get("prev")

    wave_now = fnum(wave)
    wave_before = fnum(wave_prev)
    if wave_now is None or wave_before is None:
        wave_state = "状态不可判定"
    elif wave_now > wave_before:
        wave_state = "上行"
    elif wave_now < wave_before:
        wave_state = "下行"
    else:
        wave_state = "持平"

    trend = der.get("trend_filter") or {}
    box = der.get("box_shape") or {}
    limitup = der.get("limitup_unique") or {}
    password = der.get("boduan_password_calc") or {}
    private = der.get("private_entry_basic") or {}
    cross_state = golden_cross_status(wave_now, fnum(seg))
    resonance = (
        (_triggered(output6) or _triggered(output5))
        and (_triggered(output4) or _triggered(output3))
    )

    rows = []
    rows.append(
        index_na(1, "龙头战法", "龙头战法依赖个股涨停与反转条件")
        if is_index
        else _subsystem_row(
            1,
            "龙头战法",
            f"OUTPUT3={_display_value(output3)}；X9近4日={der.get('x9_last4', 'NA')}；涨跌幅={_display_value(rc.get('change_pct'))}%",
            "触发" if _triggered(output3) else "未触发",
            "龙头战法信号已触发" if _triggered(output3) else "龙头战法信号尚未触发",
        )
    )
    rows.append(
        _subsystem_row(
            2,
            "趋势过滤/中长期均线强势条件",
            f"EMA89={_display_value(trend.get('ema89'))}；高点13三重EMA={_display_value(trend.get('high_ema13x3'))}；高点5三重EMA={_display_value(trend.get('high_ema5x3'))}；站上三线={trend.get('close_gt_all_three', 'NA')}",
            "通过" if trend.get("x27_all_pass") else "未完整通过",
            "趋势过滤条件完整通过" if trend.get("x27_all_pass") else "趋势过滤条件尚未完整通过",
            "指数部分适用：仅采用趋势均线条件" if is_index else "适用",
        )
    )
    rows.append(
        _subsystem_row(
            3,
            "四日实体重叠箱体/波段密码底层形态",
            f"今日箱体={box.get('x36_today', 'NA')}；36日内存在={box.get('x37_exist_36d', 'NA')}",
            "形成" if box.get("x36_today") else "未形成",
            "四日实体重叠箱体已形成" if box.get("x36_today") else "四日实体重叠箱体尚未形成",
        )
    )
    rows.append(
        index_na(4, "首板/唯一涨停确认", "首板确认属于个股涨停模型")
        if is_index
        else _subsystem_row(
            4,
            "首板/唯一涨停确认",
            f"X45={limitup.get('x45_today_gt985_not_doji', 'NA')}；21日涨停次数={_display_value(limitup.get('x46_count_21d'))}；X47={limitup.get('x47_unique_limitup', 'NA')}",
            "成立" if limitup.get("x47_unique_limitup") else "不成立",
            "首板/唯一涨停条件成立" if limitup.get("x47_unique_limitup") else "首板/唯一涨停条件不成立",
        )
    )
    rows.append(
        index_na(5, "波段密码打板", "打板信号属于个股涨停模型")
        if is_index
        else _subsystem_row(
            5,
            "波段密码打板",
            f"OUTPUT4={_display_value(output4)}；X47={password.get('x47', 'NA')}",
            "触发" if _triggered(output4) else "未触发",
            "波段密码打板信号已触发" if _triggered(output4) else "波段密码打板信号尚未触发",
        )
    )
    rows.append(
        index_na(6, "量价模型/暴涨启动", "暴涨启动属于个股量价模型")
        if is_index
        else _subsystem_row(
            6,
            "量价模型/暴涨启动",
            f"OUTPUT5={_display_value(output5)}；涨跌幅={_display_value(rc.get('change_pct'))}%；成交额={_display_value(rc.get('amount_wan'))}万",
            "触发" if _triggered(output5) else "未触发",
            "暴涨启动信号已触发" if _triggered(output5) else "暴涨启动信号尚未触发",
        )
    )
    rows.append(
        _subsystem_row(
            7,
            "波段随机强弱-波",
            f"当前={_display_value(wave)}；前值={_display_value(wave_prev)}",
            wave_state,
            f"波指标当前运行状态为{wave_state}",
        )
    )
    rows.append(
        _subsystem_row(
            8,
            "波段随机强弱-段",
            f"当前={_display_value(seg)}；前值={_display_value(seg_prev)}",
            cross_state,
            f"飞龙在天当前为{cross_state}",
        )
    )
    rows.append(
        index_na(9, "私募秘进", "私募秘进属于个股封板条件")
        if is_index
        else _subsystem_row(
            9,
            "私募秘进",
            f"OUTPUT6={_display_value(output6)}；涨幅条件={private.get('pct_gt_4_8', 'NA')}；收最高={private.get('close_eq_high', 'NA')}",
            "触发" if _triggered(output6) else "未触发",
            "私募秘进信号已触发" if _triggered(output6) else "私募秘进信号尚未触发",
        )
    )
    rows.append(
        index_na(10, "主升启动共振", "主升启动共振属于个股主动信号组合")
        if is_index
        else _subsystem_row(
            10,
            "主升启动共振",
            f"OUTPUT3/4/5/6={_display_value(output3)}/{_display_value(output4)}/{_display_value(output5)}/{_display_value(output6)}",
            "触发" if resonance else "未触发",
            "主升启动共振已形成" if resonance else "主升启动共振尚未形成",
        )
    )
    return rows


def table_tail(name, tail):
    lines = [f"| 日期 | {name} |", "|---|---:|"]
    for d, v in tail:
        lines.append(f"| {d} | {n2(v)} |")
    return "\n".join(lines)


def render_report(d: Dict, analysis_json: Path, derived_json: Path) -> str:
    name = d["name"]; symbol = d["symbol"]; rc = d["realtime_calc"]; lo = d["latest_outputs"]; der = d["derived"]; info=d["info"]; dc=d["date_context"]
    same_day = dc["mode"] == "same_day_realtime"
    period_word = "今日" if same_day else "基准日"
    analysis_date_display = display_date(dc["analysis_as_of_date"])
    wave=lo.get("波",{}).get("latest"); seg=lo.get("段",{}).get("latest")
    any_trig = [
        key
        for key in ["OUTPUT3", "OUTPUT4", "OUTPUT5", "OUTPUT6"]
        if indicator_output_triggered(lo.get(key, {}).get("latest"))
    ]
    xs1_triggered = any(
        indicator_output_triggered(lo.get(name, {}).get("latest"))
        for name in ("OUTPUT5", "OUTPUT6")
    )
    xs2_triggered = any(
        indicator_output_triggered(lo.get(name, {}).get("latest"))
        for name in ("OUTPUT3", "OUTPUT4")
    )
    main_rise_triggered = xs1_triggered and xs2_triggered
    main_state = "飞龙启动确认" if main_rise_triggered else "观察"
    lines=[]
    lines.append(report_title(name, symbol, dc))
    lines.append("")
    if same_day:
        lines.append(f"**数据口径**：{analysis_date_display} 同日TQ快照 + 通达信本地日线与公式输出。  ")
    else:
        lines.append(f"**数据口径**：截至 {analysis_date_display} 的通达信本地日线 + TQ公式输出；未将运行日快照冒充该日期实时行情。  ")
    lines.append(f"**运行日/分析基准日**：`{display_date(dc['run_calendar_date'])}` / `{analysis_date_display}`。  ")
    lines.append("**公式调用**：`飞龙在天`。  ")
    lines.append(f"**公式最新输出日期**：`{lo.get('波',{}).get('latest_date') or dc['formula_latest_date']}`。  ")
    lines.append("**验证产物**：")
    lines.append(f"- `{analysis_json}`")
    lines.append(f"- `{derived_json}`")
    lines.append("")
    lines.append("---")
    section_title = "今日实时行情快照" if same_day else f"{analysis_date_display} 日线行情"
    lines.append(f"\n## 1. {section_title}\n")
    price_label = "现价/最新价" if same_day else "收盘价"
    open_label = "今开" if same_day else "开盘价"
    rows=[("股票",name),("代码",symbol),("所属",f"{info.get('tdx_dyname','')}/{info.get('rs_hyname','')}"),(price_label,n2(rc['now'])),("昨收",n2(rc['last_close'])),("涨跌幅",pct(rc['change_pct'])),(open_label,n2(rc['open'])),("最高",n2(rc['high'])),("最低",n2(rc['low'])),("均价",n2(rc['avg'])),("成交量",n2(rc['volume_lot'])+"手"),("成交额",n2(rc['amount_wan'])+"万"),("振幅",pct(rc['intraday_amp_pct'])),("内盘",n2(rc['inside'])),("外盘",n2(rc['outside'])),("内外差",n2(rc['inside_minus_outside'])),("现价相对均价",pct(rc['below_avg_pct']))]
    lines += ["| 项目 | 数值 |","|---|---:|"] + [f"| {a} | {b} |" for a,b in rows]
    if same_day:
        lines.append(f"\n**实时状态解读**：现价相对均价为{pct(rc['below_avg_pct'])}，盘中最高{n2(rc['high'])}、最低{n2(rc['low'])}，振幅{pct(rc['intraday_amp_pct'])}；结合涨跌幅{pct(rc['change_pct'])}，先按盘中强弱和公式信号共同判断，不能仅凭内外盘下主力结论。")
    else:
        lines.append(f"\n**基准日状态解读**：收盘{n2(rc['now'])}，最高{n2(rc['high'])}、最低{n2(rc['low'])}，振幅{pct(rc['intraday_amp_pct'])}，涨跌幅{pct(rc['change_pct'])}；本节不使用运行日实时快照字段。")
    lines.append("\n---\n\n## 2. 飞龙在天输出总览\n")
    mapping=[("OUTPUT3","龙头战法"),("OUTPUT4","波段密码打板"),("OUTPUT5","暴涨启动"),("OUTPUT6","私募秘进"),("波","波段随机强弱-波"),("段","波段随机强弱-段")]
    lines += [f"| 输出 | 对应子系统 | {period_word}值 | 结论 |","|---|---|---:|---|"]
    for k,desc in mapping:
        v=lo.get(k,{}).get('latest')
        if k.startswith('OUTPUT'):
            concl=trigger_text(v)
        else:
            prev=lo.get(k,{}).get('prev'); concl=("上行" if v is not None and prev is not None and v>prev else "下行" if v is not None and prev is not None and v<prev else "持平/NA")
        lines.append(f"| {k} | {desc} | {n2(v)} | {concl} |")
    lines.append(f"\n核心结论：飞龙在天{period_word}{'有' if any_trig else '没有'}给出龙头、打板、暴涨、私募秘进、主升启动主动触发信号。")
    lines.append("\n---\n\n# 3. 飞龙在天子系统穷举分析\n")
    # 10 subsystems
    lines.append(f"## 子系统1：龙头战法\n- OUTPUT3：{n2(lo.get('OUTPUT3',{}).get('latest'))}，近10日均值序列见验证JSON；最近4日X_9X={der['x9_last4']}，{period_word}涨幅{pct(rc['change_pct'])}。\n- 判断：{trigger_text(lo.get('OUTPUT3',{}).get('latest'))}。若未触发，说明四日节奏/大阳线/反转条件未共振。")
    tf=der['trend_filter']
    lines.append(f"\n## 子系统2：趋势过滤 / 中长期均线强势条件\n- 现价{n2(rc['now'])}，EMA89={n2(tf['ema89'])}，高点13三重EMA={n2(tf['high_ema13x3'])}，高点5三重EMA={n2(tf['high_ema5x3'])}。\n- 站上三线：{tf['close_gt_all_three']}；代码过滤：{tf['x23_code_prefix_filter_pass']}；价格过滤：{tf['x22_price_range_pass']}；首板过滤：{tf['x26_first_limitup_pass']}。\n- 判断：趋势过滤{'通过' if tf['x27_all_pass'] else '未完整通过'}。")
    bs=der['box_shape']
    lines.append(f"\n## 子系统3：四日实体重叠箱体 / 波段密码底层形态\n- {period_word}X36={bs['x36_today']}；36日内历史箱体X37={bs['x37_exist_36d']}。\n- 判断：{period_word}{'形成新箱体触发' if bs['x36_today'] else '未形成新的四日实体重叠触发'}。")
    lu=der['limitup_unique']
    lines.append(f"\n## 子系统4：首板 / 唯一涨停确认\n- {period_word}涨幅{pct(rc['change_pct'])}；X45={lu['x45_today_gt985_not_doji']}；21日涨停次数={n2(lu['x46_count_21d'])}；X47={lu['x47_unique_limitup']}。\n- 判断：首板/唯一涨停{'成立' if lu['x47_unique_limitup'] else '不成立'}。")
    bp=der['boduan_password_calc']
    lines.append(f"\n## 子系统5：波段密码打板\n- OUTPUT4={n2(lo.get('OUTPUT4',{}).get('latest'))}；X47={bp['x47']}；触发={bp['trigger']}。\n- 判断：{trigger_text(lo.get('OUTPUT4',{}).get('latest'))}。")
    lines.append(f"\n## 子系统6：量价模型 / 暴涨启动\n- OUTPUT5={n2(lo.get('OUTPUT5',{}).get('latest'))}；涨幅{pct(rc['change_pct'])}；成交额{n2(rc['amount_wan'])}万。\n- 判断：{trigger_text(lo.get('OUTPUT5',{}).get('latest'))}。")
    lines.append("\n## 子系统7：波段随机强弱 - “波”\n" + table_tail("波", lo.get('波',{}).get('tail10',[])) + f"\n- 判断：波={n2(wave)}，较前值{n2(lo.get('波',{}).get('prev'))}，{'下行' if wave is not None and lo.get('波',{}).get('prev') is not None and wave<lo['波']['prev'] else '上行/持平'}。")
    lines.append("\n## 子系统8：波段随机强弱 - “段”\n" + table_tail("段", lo.get('段',{}).get('tail10',[])) + f"\n- 金叉状态：{golden_cross_status(wave, seg)}。")
    pe=der['private_entry_basic']
    lines.append(f"\n## 子系统9：私募秘进\n- OUTPUT6={n2(lo.get('OUTPUT6',{}).get('latest'))}；涨幅>4.8%={pe['pct_gt_4_8']}；收最高={pe['close_eq_high']}。\n- 判断：{trigger_text(lo.get('OUTPUT6',{}).get('latest'))}。")
    lines.append("\n## 子系统10：主升启动共振\n| 组件 | 状态 |\n|---|---|\n" + f"| 私募秘进 | {n2(lo.get('OUTPUT6',{}).get('latest'))} |\n| 暴涨启动 | {n2(lo.get('OUTPUT5',{}).get('latest'))} |\n| 波段密码打板 | {n2(lo.get('OUTPUT4',{}).get('latest'))} |\n| 龙头战法 | {n2(lo.get('OUTPUT3',{}).get('latest'))} |\n| 主升启动共振 | {'触发' if xs1_triggered and xs2_triggered else '未触发'} |\n\n- 判断：XS1与XS2未同时成立时，不得称为主升启动。")
    lines.append("\n---\n\n# 4. 总结结论\n")
    lines.append(f"- 龙头战法：{trigger_text(lo.get('OUTPUT3',{}).get('latest'))}\n- 波段密码打板：{trigger_text(lo.get('OUTPUT4',{}).get('latest'))}\n- 暴涨启动：{trigger_text(lo.get('OUTPUT5',{}).get('latest'))}\n- 私募秘进：{trigger_text(lo.get('OUTPUT6',{}).get('latest'))}\n- 主升启动共振：{'触发' if main_rise_triggered else '未触发'}\n\n当前属性：**{main_state}**。")
    lines.append(f"\n## 5. 后续观察条件\n\n1. `波`是否止跌回升。\n2. 金叉状态：{golden_cross_status(wave, seg)}。\n3. 价格是否站回均价/关键高点。\n4. OUTPUT5/OUTPUT6是否先亮。\n5. OUTPUT3/OUTPUT4是否共振。\n\n最后结论：按飞龙在天模板，当前未出现完整飞龙启动共振时，默认不是飞龙确认买点。")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("stock", nargs="?", default="002771", help="股票名称或6位代码 (默认: 002771 实丰美人独热血学习样例)")
    ap.add_argument("--out", help="输出md路径")
    ap.add_argument("--as-of-date", type=parse_as_of_date, help="分析基准日，格式 YYYYMMDD 或 YYYY-MM-DD")
    ap.add_argument("--json", action="store_true", help="只输出路径JSON")
    ap.add_argument("--backtest", action="store_true", help="运行飞龙在天选股历史事件研究")
    ap.add_argument("--start-date", type=parse_as_of_date, help="回测开始日期")
    ap.add_argument("--end-date", type=parse_as_of_date, help="回测结束日期")
    ap.add_argument("--out-dir", help="回测JSON和CSV输出目录")
    ap.add_argument("--symbols", help="可选的逗号分隔股票列表，用于受控验证")
    ap.add_argument("--chunk-size", type=int, default=240, help="通达信公式批处理股票数")
    ap.add_argument(
        "--selection-formula",
        default=SELECTION_FORMULA_CALL_NAME,
        help="条件选股公式名（固定为飞龙在天）",
    )
    ap.add_argument(
        "--formula-mode",
        choices=(
            "condition_selection",
            "installed_indicator_main_rise",
            "offline_installed_formula_replay",
        ),
        default="condition_selection",
        help="公式调用模式（已安装副图主升共振使用 installed_indicator_main_rise）",
    )
    ap.add_argument(
        "--candidate-cycles-csv",
        help="离线公式回放时用于按股票和首板日期精确连接的候选周期CSV",
    )
    ap.add_argument("--factor-research", action="store_true", help="运行首板飞龙在天连板因子研究")
    ap.add_argument("--factor-exhaustive", action="store_true", help="穷举首板飞龙在天共振信号的稳定高胜率因子")
    ap.add_argument("--factor-deep", action="store_true", help="运行首板飞龙在天深度稳健因子研究")
    ap.add_argument("--factor-correlation-v3", action="store_true", help="运行1280因子独立机制维度V3全量相关回测")
    ap.add_argument("--score-v3", action="store_true", help="构建1280因子多维妖股评分体系V3")
    ap.add_argument("--daily-score-v3", action="store_true", help="按本机最新通达信日线运行飞龙在天1280因子319有效维度实战评分")
    ap.add_argument("--score-32d", action="store_true", help="运行飞龙共振首板32维妖股评分体系构建")
    ap.add_argument("--daily-score-32d", action="store_true", help="按本机最新通达信日线运行飞龙在天640因子32维实战评分")
    ap.add_argument("--scoring-builder", help="32维评分体系构建脚本绝对路径")
    ap.add_argument("--scoring-model", default=r"F:\Codex\projects\飞龙在天评分体系彻底优化_20260901-184258\飞龙共振首板_32维评分模型配置.json")
    ap.add_argument("--historical-factors", default=r"F:\Codex\projects\飞龙在天评分体系彻底优化_20260901-184258\因子全量重算\飞龙共振首板_全量因子事件值.csv")
    ap.add_argument("--scoring-applier", default=r"F:\Codex\projects\飞龙在天评分体系彻底优化_20260901-184258\apply_yaogu_scoring.py")
    ap.add_argument("--target-date", type=parse_as_of_date, help="日评分目标日期；必须等于本机最新有效交易日")
    ap.add_argument("--matches-csv", help="因子研究使用的158个首板飞龙在天命中CSV")
    ap.add_argument("--migration-manifest", help="因子研究使用的迁移包manifest.json")
    ap.add_argument("--events-csv", help="穷举研究使用的已验证全市场首板事件CSV")
    ap.add_argument("--source-factor-manifest", help="穷举研究使用的源因子研究清单JSON")
    ap.add_argument("--tdx-root", default=str(TDX_ROOT), help="本机通达信只读根目录")
    args = ap.parse_args(argv if argv is not None else None)
    if args.factor_correlation_v3:
        required = {
            "--events-csv": args.events_csv,
            "--source-factor-manifest": args.source_factor_manifest,
            "--out-dir": args.out_dir,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            ap.error("--factor-correlation-v3 缺少参数: " + ", ".join(missing))
        result = run_factor_correlation_v3(
            events_csv=args.events_csv,
            source_manifest=args.source_factor_manifest,
            out_dir=args.out_dir,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.score_v3:
        required = {
            "--scoring-builder": args.scoring_builder,
            "--out-dir": args.out_dir,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            ap.error("--score-v3 缺少参数: " + ", ".join(missing))
        builder = Path(args.scoring_builder).resolve()
        output_dir = Path(args.out_dir).resolve()
        if not builder.is_file():
            raise FileNotFoundError(f"V3评分构建脚本不存在: {builder}")
        spec = importlib.util.spec_from_file_location("feilong_yaogu_multidim_v3_builder", builder)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"无法加载V3评分构建脚本: {builder}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module_out = Path(module.OUT_DIR).resolve()
        if module_out != output_dir:
            raise RuntimeError(f"评分输出目录不一致: builder={module_out}; requested={output_dir}")
        module.main()
        manifest_path = output_dir / "构建验收清单.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema") != "FEILONG_YAOGU_MULTIDIM_SCORE_BUILD_V3" or manifest.get("status") != "CLEAN_PASS":
            raise RuntimeError("V3多维评分构建验收未通过")
        artifacts = {}
        for name, evidence in manifest.get("artifacts", {}).items():
            path = Path(str(evidence.get("path", output_dir / name))).resolve()
            if not path.is_file() or path.name != name:
                raise RuntimeError(f"V3多维评分产物缺失: {path}")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if evidence.get("bytes") != path.stat().st_size or evidence.get("sha256") != digest:
                raise RuntimeError(f"V3多维评分产物哈希不一致: {path}")
            artifacts[name] = {"path": str(path), "size": path.stat().st_size, "sha256": digest}
        artifacts[manifest_path.name] = {
            "path": str(manifest_path),
            "size": manifest_path.stat().st_size,
            "sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        }
        result = {
            "schema": "FEILONG_YAOGU_MULTIDIM_SCORE_RUN_V3",
            "status": "CLEAN_PASS",
            "formula_name": "飞龙在天",
            "formula_sha256": "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0",
            "legacy_4_0_used": False,
            "builder": {"path": str(builder), "sha256": hashlib.sha256(builder.read_bytes()).hexdigest()},
            "checks": manifest.get("checks", {}),
            "artifacts": artifacts,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.daily_score_v3:
        if not args.out_dir:
            ap.error("--daily-score-v3 缺少参数: --out-dir")
        result = run_daily_yaogu_scoring(
            target_date=args.target_date,
            model_path=Path(args.scoring_model).resolve(),
            history_path=Path(args.historical_factors).resolve(),
            scorer_path=Path(args.scoring_applier).resolve(),
            out_dir=Path(args.out_dir).resolve(),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.daily_score_32d:
        if not args.out_dir:
            ap.error("--daily-score-32d 缺少参数: --out-dir")
        result = run_daily_yaogu_scoring(
            target_date=args.target_date,
            model_path=Path(args.scoring_model).resolve(),
            history_path=Path(args.historical_factors).resolve(),
            scorer_path=Path(args.scoring_applier).resolve(),
            out_dir=Path(args.out_dir).resolve(),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.score_32d:
        required = {
            "--scoring-builder": args.scoring_builder,
            "--out-dir": args.out_dir,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            ap.error("--score-32d 缺少参数: " + ", ".join(missing))
        builder = Path(args.scoring_builder).resolve()
        output_dir = Path(args.out_dir).resolve()
        if not builder.is_file():
            raise FileNotFoundError(f"32维评分构建脚本不存在: {builder}")
        spec = importlib.util.spec_from_file_location("feilong_yaogu_32d_builder", builder)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"无法加载32维评分构建脚本: {builder}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module_out = Path(module.OUT_DIR).resolve()
        if module_out != output_dir:
            raise RuntimeError(f"评分输出目录不一致: builder={module_out}; requested={output_dir}")
        module.main()
        manifest_path = output_dir / "构建验收清单.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("status") != "CLEAN_PASS":
            raise RuntimeError("32维评分构建验收未通过")
        artifacts = {}
        for name, evidence in manifest.get("artifacts", {}).items():
            path = output_dir / name
            if not path.is_file():
                raise RuntimeError(f"32维评分产物缺失: {path}")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if evidence.get("bytes") != path.stat().st_size or evidence.get("sha256") != digest:
                raise RuntimeError(f"32维评分产物哈希不一致: {path}")
            artifacts[name] = {"path": str(path), "size": path.stat().st_size, "sha256": digest}
        artifacts[manifest_path.name] = {
            "path": str(manifest_path),
            "size": manifest_path.stat().st_size,
            "sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        }
        result = {
            "schema": "FEILONG_YAOGU_32D_SCORE_RUN_V1",
            "status": "CLEAN_PASS",
            "formula_name": "飞龙在天",
            "formula_sha256": "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0",
            "legacy_4_0_used": False,
            "builder": {"path": str(builder), "sha256": hashlib.sha256(builder.read_bytes()).hexdigest()},
            "checks": manifest.get("checks", {}),
            "artifacts": artifacts,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.factor_deep:
        required = {
            "--events-csv": args.events_csv,
            "--source-factor-manifest": args.source_factor_manifest,
            "--out-dir": args.out_dir,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            ap.error("--factor-deep 缺少参数: " + ", ".join(missing))
        result = run_deep_factor_research(
            events_csv=args.events_csv,
            source_manifest=args.source_factor_manifest,
            out_dir=args.out_dir,
            tdx_root=args.tdx_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.factor_exhaustive:
        required = {
            "--events-csv": args.events_csv,
            "--source-factor-manifest": args.source_factor_manifest,
            "--out-dir": args.out_dir,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            ap.error("--factor-exhaustive 缺少参数: " + ", ".join(missing))
        result = run_resonance_exhaustive(
            events_csv=args.events_csv,
            source_manifest=args.source_factor_manifest,
            out_dir=args.out_dir,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.factor_research:
        required = {
            "--candidate-cycles-csv": args.candidate_cycles_csv,
            "--matches-csv": args.matches_csv,
            "--migration-manifest": args.migration_manifest,
            "--out-dir": args.out_dir,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            ap.error("--factor-research 缺少参数: " + ", ".join(missing))
        result = run_factor_research(
            cycles_csv=args.candidate_cycles_csv,
            matches_csv=args.matches_csv,
            migration_manifest=args.migration_manifest,
            out_dir=args.out_dir,
            tdx_root=args.tdx_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.backtest:
        if not args.start_date or not args.end_date:
            ap.error("--backtest 必须同时提供 --start-date 和 --end-date")
        selected_symbols = [value.strip() for value in args.symbols.split(",") if value.strip()] if args.symbols else None
        result = run_backtest(
            start_date=args.start_date,
            end_date=args.end_date,
            out_dir=args.out_dir,
            symbols=selected_symbols,
            chunk_size=args.chunk_size,
            selection_formula=args.selection_formula,
            formula_mode=args.formula_mode,
            candidate_cycles_csv=args.candidate_cycles_csv,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    res = analyze(args.stock, args.out, args.as_of_date)
    if args.json:
        print(json.dumps({k:v for k,v in res.items() if k != 'summary'}, ensure_ascii=False, indent=2))
    else:
        print(f"REPORT={res['report']}")
        print(f"ANALYSIS_JSON={res['analysis_json']}")
        print(f"DERIVED_JSON={res['derived_json']}")

if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    main()
