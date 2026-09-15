#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用黄金点火分析器：本机通达信数据 + 大牛线点火字段。"""

from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import contextlib
import csv
import dataclasses
import hashlib
import importlib.util
import io
import json
import math
import os
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = Path(os.environ.get("ZHANGCAI_APP_ROOT", str(SKILL_ROOT.parent.parent))).resolve()
TDX_ROOT = Path(os.environ.get("ZHANGCAI_TDX_ROOT", r"C:\new_tdx_mock")).resolve()
TDX_HUB_PATH = Path(os.environ.get(
    "TDX_HUB_PATH",
    str(APP_ROOT / "harness-skills" / "tdx-local-hub" / "scripts" / "tdx_hub.py"),
)).resolve()
BACKTEST_RUNTIME_PATH = Path(os.environ.get(
    "STOCK_BACKTEST_RUNTIME_PATH",
    str(APP_ROOT / "harness-skills" / "stock-unified" / "scripts" / "stock_strategy_backtest.py"),
)).resolve()
BOND_MAP_PATH = Path(os.environ.get(
    "TDX_BOND_MAP_PATH",
    str(TDX_ROOT / "T0002" / "hq_cache" / "speckzzdata.txt"),
)).resolve()
FORMULA_STORE_PATH = Path(os.environ.get(
    "TDX_FORMULA_STORE_PATH",
    str(TDX_ROOT / "T0002" / "PriGS.dat"),
)).resolve()
RESULTS_DIR = Path(os.environ.get(
    "ZHANGCAI_STRATEGY_RESULTS_DIR",
    os.environ.get("ONESTOCK_STOCK_DATA_ROOT", str(APP_ROOT / "app-data" / "strategy-results")),
)).resolve() / "golden-ignition"
FORMULA_NAME = "大牛线4.0"
FORMULA_CALL_NAME = "大牛线撑压版"
AI_FORMULA_NAME = "黄金点火AI"
IGNITION_FIELDS = ("OUTPUT59", "OUTPUT60", "OUTPUT61")
BOND_PREFIXES = ("110", "111", "113", "118", "123", "127", "128", "132")


def file_binding(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": str(path),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "updated_at": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(),
    }


def load_tdx_hub():
    spec = importlib.util.spec_from_file_location("golden_ignition_tdx_hub", TDX_HUB_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载通达信入口：{TDX_HUB_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_backtest_runtime():
    spec = importlib.util.spec_from_file_location(
        "golden_ignition_stock_backtest",
        BACKTEST_RUNTIME_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载统一回测运行时：{BACKTEST_RUNTIME_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def six_digit_code(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) < 6:
        raise ValueError(f"无效证券代码：{value}")
    return digits[-6:]


def bond_underlying(code: str) -> str | None:
    if not code.startswith(BOND_PREFIXES) or not BOND_MAP_PATH.is_file():
        return None
    with BOND_MAP_PATH.open("r", encoding="gbk", errors="replace", newline="") as handle:
        for fields in csv.reader(handle):
            if len(fields) >= 3 and fields[1].strip() == code:
                underlying = fields[2].strip()
                return underlying if len(underlying) == 6 and underlying.isdigit() else None
    return None


def ema(values: list[float], period: int) -> list[float]:
    alpha = 2.0 / (period + 1.0)
    result: list[float] = []
    for value in values:
        result.append(value if not result else alpha * value + (1.0 - alpha) * result[-1])
    return result


def number(value: Any) -> float | None:
    if isinstance(value, list):
        value = value[0] if value else None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def align_formula_series(
    dates: list[str],
    values: list[Any],
) -> dict[str, float]:
    usable = min(len(dates), len(values))
    if usable <= 0:
        return {}
    aligned: dict[str, float] = {}
    for date, raw in zip(dates[-usable:], values[-usable:]):
        value = number(raw)
        if value is not None and math.isfinite(value):
            aligned[str(date)] = value
    return aligned


def select_signal_field(
    fields: dict[str, Any],
    *,
    expected_length: int,
) -> str | None:
    candidates: list[tuple[float, int, str]] = []
    for name, raw in fields.items():
        if not isinstance(raw, list) or not raw:
            continue
        values = [number(item) for item in raw[-expected_length:]]
        finite = [value for value in values if value is not None and math.isfinite(value)]
        if len(finite) < min(expected_length, len(raw)):
            continue
        positives = [value for value in finite if value > 0]
        zeros = [value for value in finite if abs(value) <= 1e-12]
        if not positives or not zeros:
            continue
        density = len(positives) / len(finite)
        if density > 0.50:
            continue
        positive_levels = len({round(value, 8) for value in positives})
        candidates.append((density, positive_levels, str(name)))
    return min(candidates)[2] if candidates else None


def formula_failure_diagnostics(payload: dict[str, Any]) -> str:
    evidence = {
        key: payload.get(key)
        for key in ("error", "attempts", "result", "tq_stdout", "tq_stderr")
        if payload.get(key) not in (None, "")
    }
    return json.dumps(evidence, ensure_ascii=False, sort_keys=True)


def extract_xg_signal_dates(
    records: list[Any],
    *,
    fallback_dates: list[str],
) -> list[str]:
    if records and all(isinstance(item, dict) for item in records):
        dates: list[str] = []
        for item in records:
            value = number(item.get("Value", item.get("value")))
            date = item.get("Date", item.get("date"))
            if value is not None and value > 0 and date is not None:
                dates.append(str(date))
        return dates
    aligned = align_formula_series(fallback_dates, records)
    return [date for date, value in aligned.items() if value > 0]


def build_ai_signals(
    bars: list[Any],
    signal_dates: set[str],
    params: dict[str, Any],
) -> list[bool]:
    closes = [float(bar.close) for bar in bars]
    amounts = [float(bar.amount) for bar in bars]
    trend_filter = str(params.get("trend_filter", "none"))
    volume_ratio = float(params.get("volume_ratio", 0.0))
    signals = [False] * len(bars)
    for index, bar in enumerate(bars):
        if str(bar.date) not in signal_dates:
            continue
        trend_ok = True
        if trend_filter in {"above_ma20", "ma20_rising"}:
            if index < 19:
                trend_ok = False
            else:
                current_ma20 = statistics.fmean(closes[index - 19 : index + 1])
                trend_ok = closes[index] > current_ma20
                if trend_ok and trend_filter == "ma20_rising":
                    if index < 24:
                        trend_ok = False
                    else:
                        prior_ma20 = statistics.fmean(closes[index - 24 : index - 4])
                        trend_ok = current_ma20 > prior_ma20
        volume_ok = True
        if volume_ratio > 0:
            if index < 20:
                volume_ok = False
            else:
                prior_amount = statistics.fmean(amounts[index - 20 : index])
                volume_ok = prior_amount > 0 and amounts[index] >= prior_amount * volume_ratio
        signals[index] = trend_ok and volume_ok
    return signals


def ai_trade_metrics(trades: list[Any]) -> dict[str, Any]:
    if not trades:
        return {
            "trade_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": None,
            "average_win": None,
            "average_loss": None,
            "payoff_ratio": None,
            "profit_factor": None,
            "average_net_return": None,
            "median_net_return": None,
            "compounded_trade_return": None,
            "max_drawdown": None,
        }
    returns = [float(trade.net_return) for trade in trades]
    wins = [value for value in returns if value > 0]
    losses = [-value for value in returns if value < 0]
    average_win = statistics.fmean(wins) if wins else None
    average_loss = statistics.fmean(losses) if losses else None
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in returns:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - 1.0)
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    return {
        "trade_count": len(returns),
        "win_count": len(wins),
        "loss_count": len(losses),
        "win_rate": len(wins) / len(returns),
        "average_win": average_win,
        "average_loss": average_loss,
        "payoff_ratio": (
            average_win / average_loss
            if average_win is not None and average_loss not in (None, 0)
            else None
        ),
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else None,
        "average_net_return": statistics.fmean(returns),
        "median_net_return": statistics.median(returns),
        "compounded_trade_return": equity - 1.0,
        "max_drawdown": max_drawdown,
    }


def dual_objective(metrics: dict[str, Any], *, minimum_trades: int) -> float:
    count = int(metrics.get("trade_count") or 0)
    if count <= 0:
        return -1_000_000.0
    win_rate = float(metrics.get("win_rate") or 0.0)
    payoff = max(0.05, min(10.0, float(metrics.get("payoff_ratio") or 0.05)))
    profit_factor = max(0.05, min(10.0, float(metrics.get("profit_factor") or 0.05)))
    drawdown = float(metrics.get("max_drawdown") or 0.0)
    base = win_rate + 0.35 * math.log(payoff) + 0.25 * math.log(profit_factor) + 0.50 * drawdown
    sample_weight = min(1.0, count / max(1, minimum_trades))
    return base * sample_weight - (1.0 - sample_weight)


def ai_parameter_grid() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    baseline = {
        "hold_days": 5,
        "stop_loss_pct": 0.08,
        "trend_filter": "none",
        "volume_ratio": 0.0,
    }
    rows: list[dict[str, Any]] = []
    for hold_days in (3, 5, 8, 10):
        for stop_loss_pct in (0.04, 0.06, 0.08, None):
            rows.append(
                {
                    "hold_days": hold_days,
                    "stop_loss_pct": stop_loss_pct,
                    "trend_filter": "none",
                    "volume_ratio": 0.0,
                }
            )
    for hold_days in (5, 8):
        for stop_loss_pct in (0.06, 0.08):
            for trend_filter in ("above_ma20", "ma20_rising"):
                for volume_ratio in (0.0, 1.0, 1.2):
                    rows.append(
                        {
                            "hold_days": hold_days,
                            "stop_loss_pct": stop_loss_pct,
                            "trend_filter": trend_filter,
                            "volume_ratio": volume_ratio,
                        }
                    )
    unique: dict[str, dict[str, Any]] = {}
    for row in [baseline, *rows]:
        unique[json.dumps(row, ensure_ascii=False, sort_keys=True)] = row
    return baseline, list(unique.values())


def select_validation_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("candidate rows must not be empty")
    train_ranked = sorted(
        rows,
        key=lambda row: (
            float(row["train_objective"]),
            int((row.get("train_metrics") or {}).get("trade_count") or 0),
        ),
        reverse=True,
    )
    shortlist_count = max(1, (len(train_ranked) + 1) // 2)
    return max(
        train_ranked[:shortlist_count],
        key=lambda row: (
            float(row["validation_objective"]),
            int((row.get("validation_metrics") or {}).get("trade_count") or 0),
        ),
    )


def select_dual_goal_candidate(
    rows: list[dict[str, Any]],
    *,
    baseline_parameters: dict[str, Any],
    minimum_trades: int,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("candidate rows must not be empty")
    baseline_row = next(
        (row for row in rows if row["parameters"] == baseline_parameters),
        None,
    )
    if baseline_row is None:
        raise ValueError("baseline parameters must be present in candidate rows")
    baseline_metrics = baseline_row.get("validation_metrics") or {}
    baseline_win_rate = baseline_metrics.get("win_rate")
    baseline_payoff_ratio = baseline_metrics.get("payoff_ratio")
    if baseline_win_rate is None or baseline_payoff_ratio is None:
        raise ValueError("baseline validation metrics must include win_rate and payoff_ratio")

    train_ranked = sorted(
        rows,
        key=lambda row: (
            float(row["train_objective"]),
            int((row.get("train_metrics") or {}).get("trade_count") or 0),
        ),
        reverse=True,
    )
    shortlist_count = max(1, (len(train_ranked) + 1) // 2)
    shortlist = train_ranked[:shortlist_count]
    eligible: list[dict[str, Any]] = []
    rejected_single_goal: list[dict[str, Any]] = []
    for row in shortlist:
        if row is baseline_row:
            continue
        metrics = row.get("validation_metrics") or {}
        trade_count = int(metrics.get("trade_count") or 0)
        win_rate = metrics.get("win_rate")
        payoff_ratio = metrics.get("payoff_ratio")
        win_improved = win_rate is not None and float(win_rate) > float(baseline_win_rate)
        payoff_improved = (
            payoff_ratio is not None
            and float(payoff_ratio) > float(baseline_payoff_ratio)
        )
        sample_ok = trade_count >= minimum_trades
        if sample_ok and win_improved and payoff_improved:
            eligible.append(row)
            continue
        if sample_ok and win_improved != payoff_improved:
            reasons = []
            if not win_improved:
                reasons.append("validation_win_rate_not_improved")
            if not payoff_improved:
                reasons.append("validation_payoff_ratio_not_improved")
            rejected_single_goal.append(
                {
                    "parameters": row["parameters"],
                    "validation_metrics": metrics,
                    "validation_objective": row["validation_objective"],
                    "reasons": reasons,
                }
            )

    if eligible:
        selected = max(
            eligible,
            key=lambda row: (
                float(row["validation_objective"]),
                int((row.get("validation_metrics") or {}).get("trade_count") or 0),
            ),
        )
        status = "dual_goal_validation_improved"
    else:
        selected = baseline_row
        status = "baseline_fallback_no_dual_improvement"
    rejected_single_goal.sort(
        key=lambda row: float(row["validation_objective"]),
        reverse=True,
    )
    return {
        "status": status,
        "selected": selected,
        "shortlist_count": shortlist_count,
        "eligible_count": len(eligible),
        "baseline_validation_metrics": baseline_metrics,
        "rejected_single_goal_candidates": rejected_single_goal,
    }


def format_percent(value: Any) -> str:
    return "N/A" if value is None else f"{float(value) * 100:.2f}%"


def build_ai_recommendations(
    *,
    selection_status: str,
    baseline: dict[str, Any],
    selected: dict[str, Any],
    rejected_single_goal_candidates: list[dict[str, Any]],
    test_both_improved: bool = False,
) -> list[str]:
    if selection_status == "dual_goal_validation_improved" and test_both_improved:
        opening = (
            "验证集与测试集均显示胜率和盈亏比同时提高，可将选定参数用于纸面跟踪；"
            "在新的滚动样本再次验证前，不直接改写原公式。"
        )
        parameter_line = (
            f"纸面参数：持有 {selected['hold_days']} 个交易日；止损："
            f"{format_percent(selected['stop_loss_pct']) if selected['stop_loss_pct'] is not None else '不设固定止损'}；"
            f"趋势过滤：{selected['trend_filter']}；量能阈值：{selected['volume_ratio']:.1f} 倍。"
        )
    else:
        opening = (
            "没有候选参数在独立验证规则下同时提高胜率和盈亏比，双目标硬闸已回退并保留基线；"
            "被拒绝的单目标参数不得写成优化建议。"
        )
        parameter_line = (
            f"保留基线执行层参数：持有 {baseline['hold_days']} 个交易日；止损："
            f"{format_percent(baseline['stop_loss_pct']) if baseline['stop_loss_pct'] is not None else '不设固定止损'}；"
            f"趋势过滤：{baseline['trend_filter']}；量能阈值：{baseline['volume_ratio']:.1f} 倍。"
        )
    rejected_line = (
        f"验证短名单中有 {len(rejected_single_goal_candidates)} 组参数只改善一个目标，均已拒绝。"
        if rejected_single_goal_candidates
        else "验证短名单中没有需要列示的单目标改善参数。"
    )
    return [
        opening,
        parameter_line,
        rejected_line,
        "信号必须在收盘后确认，下一交易日开盘执行，避免同日收盘价成交造成未来函数偏差。",
        "建议每月滚动追加新K线，只在连续两个样本外窗口同时改善胜率和盈亏比时，才考虑升级纸面参数。",
    ]


def metrics_with_objective(
    trades: list[Any],
    *,
    minimum_trades: int,
) -> dict[str, Any]:
    result = ai_trade_metrics(trades)
    result["dual_objective"] = dual_objective(
        result,
        minimum_trades=minimum_trades,
    )
    return result


def run_parameter_set(
    runtime: Any,
    universe: dict[str, list[Any]],
    signal_dates: dict[str, set[str]],
    params: dict[str, Any],
) -> list[Any]:
    config = runtime.ExecutionConfig(
        hold_days=int(params["hold_days"]),
        stop_loss_pct=(
            float(params["stop_loss_pct"])
            if params.get("stop_loss_pct") is not None
            else None
        ),
    )
    trades: list[Any] = []
    for symbol, bars in universe.items():
        signals = build_ai_signals(
            bars,
            signal_dates.get(symbol, set()),
            params,
        )
        trades.extend(runtime.execute_signals(symbol, bars, signals, config))
    return sorted(
        trades,
        key=lambda trade: (trade.exit_date, trade.symbol, trade.entry_date),
    )


def partition_trades(
    runtime: Any,
    trades: list[Any],
    split: Any,
    partition: str,
) -> list[Any]:
    return runtime.partition_trades(trades, split, partition)


def yearly_metrics(trades: list[Any]) -> dict[str, Any]:
    years = sorted({str(trade.signal_date)[:4] for trade in trades})
    return {
        year: ai_trade_metrics(
            [trade for trade in trades if str(trade.signal_date).startswith(year)]
        )
        for year in years
    }


def render_ai_backtest_markdown(payload: dict[str, Any]) -> str:
    comparison = payload["test_comparison"]
    baseline = comparison["baseline"]
    optimized = comparison["optimized"]
    deltas = comparison["deltas"]
    params = payload["optimization"]
    lines = [
        "# 黄金点火AI真实K线回测与优化报告",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 通达信公式：`{payload['formula']['name']}`（条件选股公式，字段 `XG`）",
        f"- K线区间：`{payload['data']['start_date']}` 至 `{payload['data']['end_date']}`",
        f"- 样本股票：`{payload['data']['universe_size']}` 只",
        f"- 原始信号：`{payload['data']['signal_count']}` 个",
        f"- 真实成交模型：信号后下一交易日开盘买入，含佣金、最低佣金、印花税和双边滑点",
        "",
        "## 测试集结果",
        "",
        "| 指标 | 原始执行参数 | 双目标闸门选定参数 | 变化 |",
        "|---|---:|---:|---:|",
        f"| 交易数 | {baseline['trade_count']} | {optimized['trade_count']} | {optimized['trade_count'] - baseline['trade_count']} |",
        f"| 胜率 | {format_percent(baseline['win_rate'])} | {format_percent(optimized['win_rate'])} | {format_percent(deltas['win_rate'])} |",
        f"| 平均盈利 | {format_percent(baseline['average_win'])} | {format_percent(optimized['average_win'])} | {format_percent(deltas['average_win'])} |",
        f"| 平均亏损 | {format_percent(baseline['average_loss'])} | {format_percent(optimized['average_loss'])} | {format_percent(deltas['average_loss'])} |",
        f"| 盈亏比 | {baseline['payoff_ratio'] if baseline['payoff_ratio'] is not None else 'N/A'} | {optimized['payoff_ratio'] if optimized['payoff_ratio'] is not None else 'N/A'} | {deltas['payoff_ratio'] if deltas['payoff_ratio'] is not None else 'N/A'} |",
        f"| 利润因子 | {baseline['profit_factor'] if baseline['profit_factor'] is not None else 'N/A'} | {optimized['profit_factor'] if optimized['profit_factor'] is not None else 'N/A'} | {deltas['profit_factor'] if deltas['profit_factor'] is not None else 'N/A'} |",
        f"| 最大交易序列回撤 | {format_percent(baseline['max_drawdown'])} | {format_percent(optimized['max_drawdown'])} | {format_percent(deltas['max_drawdown'])} |",
        "",
        "## 参数",
        "",
        f"- 基线：`{json.dumps(params['baseline_parameters'], ensure_ascii=False, sort_keys=True)}`",
        f"- 双目标硬闸最终采用：`{json.dumps(params['optimized_parameters'], ensure_ascii=False, sort_keys=True)}`",
        f"- 选择状态：`{params['selection_status']}`",
        f"- 固定候选网格：`{params['grid_size']}` 组；测试集在定参后只读取一次。",
        "",
    ]
    rejected = params.get("rejected_single_goal_candidates") or []
    if rejected:
        reason_labels = {
            "validation_win_rate_not_improved": "验证胜率未提高",
            "validation_payoff_ratio_not_improved": "验证盈亏比未提高",
        }
        lines.extend(
            [
                "## 被拒绝的单目标参数",
                "",
                "| 参数 | 拒绝原因 | 验证胜率 | 验证盈亏比 |",
                "|---|---|---:|---:|",
            ]
        )
        for row in rejected:
            metrics = row.get("validation_metrics") or {}
            reasons = "；".join(
                reason_labels.get(reason, reason)
                for reason in row.get("reasons", [])
            )
            lines.append(
                f"| `{json.dumps(row['parameters'], ensure_ascii=False, sort_keys=True)}` | {reasons} | "
                f"{format_percent(metrics.get('win_rate'))} | "
                f"{metrics.get('payoff_ratio') if metrics.get('payoff_ratio') is not None else 'N/A'} |"
            )
        lines.append("")
    lines.extend(["## 结论与建议", ""])
    for item in payload["recommendations"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 验证边界",
            "",
            "- 公式信号由本机通达信TQ引擎直接计算，没有按名称猜测或用EMA代理。",
            "- 回测没有改写通达信中的原公式；优化只作用于纸面交易执行层。",
            "- 当前名称与当前流动性排序会引入幸存者偏差；结果不构成收益保证或自动交易指令。",
            "- 多证券交易按退出时间组成交易序列，未建模组合同时持仓上限与资金占用冲突。",
            "",
            "## 数据完整性",
            "",
            f"- 公式库SHA256：`{payload['formula']['store_sha256']}`",
            f"- 信号集SHA256：`{payload['data']['signal_set_sha256']}`",
            f"- K线清单SHA256：`{payload['data']['daily_manifest_sha256']}`",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ai_backtest(
    *,
    formula_name: str,
    start_date: int,
    end_date: int,
    max_symbols: int,
    batch_size: int,
    output_json: Path,
    output_markdown: Path,
) -> dict[str, Any]:
    hub = load_tdx_hub()
    runtime = load_backtest_runtime()
    names = runtime.load_names()
    universe = runtime.load_universe(
        "equity",
        start_date,
        end_date,
        max_symbols,
        names,
    )
    if not universe:
        raise RuntimeError("没有从本机通达信加载到合格A股历史日线")
    all_dates = sorted(
        {
            bar.date
            for bars in universe.values()
            for bar in bars
            if start_date <= bar.date <= end_date
        }
    )
    split = runtime.chronological_split(all_dates)
    count = max(len(bars) for bars in universe.values())
    symbols = list(universe)
    signal_dates: dict[str, set[str]] = {symbol: set() for symbol in symbols}
    batch_evidence: list[dict[str, Any]] = []
    for offset in range(0, len(symbols), batch_size):
        batch = symbols[offset : offset + batch_size]
        result = tq_xg_history(
            hub,
            formula_name,
            batch,
            count=count,
            dividend_type=1,
        )
        if result.get("ok") is not True:
            raise RuntimeError(
                f"黄金点火AI批次执行失败 offset={offset}："
                + formula_failure_diagnostics(result)
            )
        nodes = result.get("result") or {}
        returned_symbols = 0
        batch_signal_count = 0
        for symbol in batch:
            node = nodes.get(symbol, {}) if isinstance(nodes, dict) else {}
            records = node.get("XG", []) if isinstance(node, dict) else []
            dates = {
                date
                for date in extract_xg_signal_dates(records, fallback_dates=[])
                if start_date <= int(date[:8]) <= end_date
            }
            if isinstance(node, dict) and "XG" in node:
                returned_symbols += 1
            signal_dates[symbol] = dates
            batch_signal_count += len(dates)
        batch_evidence.append(
            {
                "offset": offset,
                "requested_symbols": len(batch),
                "returned_symbols": returned_symbols,
                "signal_count": batch_signal_count,
                "error_id": str(nodes.get("ErrorId", "0")) if isinstance(nodes, dict) else None,
                "init_path": result.get("init_path"),
                "lock_waited_ms": result.get("lock_waited_ms"),
            }
        )
    signal_count = sum(len(dates) for dates in signal_dates.values())
    if signal_count <= 0:
        raise RuntimeError("黄金点火AI在所选真实K线样本中没有历史点火信号")

    baseline, grid = ai_parameter_grid()
    cache: dict[str, list[Any]] = {}

    def trades_for(params: dict[str, Any]) -> list[Any]:
        key = json.dumps(params, ensure_ascii=False, sort_keys=True)
        if key not in cache:
            cache[key] = run_parameter_set(runtime, universe, signal_dates, params)
        return cache[key]

    minimum_trades = 20
    candidates: list[dict[str, Any]] = []
    for params in grid:
        trades = trades_for(params)
        train_metrics = metrics_with_objective(
            partition_trades(runtime, trades, split, "train"),
            minimum_trades=minimum_trades,
        )
        validation_metrics = metrics_with_objective(
            partition_trades(runtime, trades, split, "validation"),
            minimum_trades=minimum_trades,
        )
        candidates.append(
            {
                "parameters": params,
                "train_objective": train_metrics["dual_objective"],
                "validation_objective": validation_metrics["dual_objective"],
                "train_metrics": train_metrics,
                "validation_metrics": validation_metrics,
            }
        )
    selection = select_dual_goal_candidate(
        candidates,
        baseline_parameters=baseline,
        minimum_trades=minimum_trades,
    )
    selected = selection["selected"]
    optimized = selected["parameters"]
    baseline_trades = trades_for(baseline)
    optimized_trades = trades_for(optimized)
    baseline_test = metrics_with_objective(
        partition_trades(runtime, baseline_trades, split, "test"),
        minimum_trades=minimum_trades,
    )
    optimized_test = metrics_with_objective(
        partition_trades(runtime, optimized_trades, split, "test"),
        minimum_trades=minimum_trades,
    )

    def delta(key: str) -> float | None:
        before = baseline_test.get(key)
        after = optimized_test.get(key)
        return None if before is None or after is None else float(after) - float(before)

    deltas = {
        key: delta(key)
        for key in (
            "win_rate",
            "average_win",
            "average_loss",
            "payoff_ratio",
            "profit_factor",
            "max_drawdown",
            "dual_objective",
        )
    }
    both_improved = (
        deltas["win_rate"] is not None
        and deltas["payoff_ratio"] is not None
        and deltas["win_rate"] > 0
        and deltas["payoff_ratio"] > 0
    )
    recommendations = build_ai_recommendations(
        selection_status=selection["status"],
        baseline=baseline,
        selected=optimized,
        rejected_single_goal_candidates=selection["rejected_single_goal_candidates"],
        test_both_improved=both_improved,
    )

    daily_manifest = [
        {
            "symbol": symbol,
            **file_binding(hub.day_path(symbol)),
        }
        for symbol in symbols
    ]
    daily_manifest_hash = hashlib.sha256(
        json.dumps(daily_manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    serializable_signals = {
        symbol: sorted(dates)
        for symbol, dates in signal_dates.items()
        if dates
    }
    signal_set_hash = hashlib.sha256(
        json.dumps(serializable_signals, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    payload = {
        "schema": "GOLDEN_IGNITION_AI_BACKTEST_V1",
        "status": "PASS",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "formula": {
            "name": formula_name,
            "kind": "xg",
            "field": "XG",
            "dividend_type": 1,
            "store": str(FORMULA_STORE_PATH),
            "store_sha256": file_binding(FORMULA_STORE_PATH)["sha256"],
            "source_code_exported": False,
        },
        "data": {
            "source": "C:/new_tdx_mock local daily bars + local TQ formula engine",
            "start_date": start_date,
            "end_date": end_date,
            "universe_size": len(universe),
            "selection": "当前非ST非退市A股按最近20日通达信本地成交额排序，取流动性前列",
            "signal_count": signal_count,
            "symbols_with_signals": len(serializable_signals),
            "bar_count_requested": count,
            "daily_manifest_sha256": daily_manifest_hash,
            "signal_set_sha256": signal_set_hash,
            "batch_evidence": batch_evidence,
        },
        "time_split": dataclasses.asdict(split),
        "execution_assumptions": dataclasses.asdict(runtime.ExecutionConfig()),
        "optimization": {
            "goal": "simultaneously improve win_rate and payoff_ratio",
            "baseline_parameters": baseline,
            "optimized_parameters": optimized,
            "grid_size": len(grid),
            "minimum_partition_trades": minimum_trades,
            "selection_status": selection["status"],
            "selection_rule": "train top half shortlist; validation requires both win_rate and payoff_ratio above baseline with at least 20 trades; otherwise baseline fallback; test read once",
            "shortlist_count": selection["shortlist_count"],
            "eligible_count": selection["eligible_count"],
            "baseline_validation_metrics": selection["baseline_validation_metrics"],
            "selected_train_metrics": selected["train_metrics"],
            "selected_validation_metrics": selected["validation_metrics"],
            "rejected_single_goal_candidates": selection["rejected_single_goal_candidates"],
            "candidate_results": sorted(
                candidates,
                key=lambda item: item["validation_objective"],
                reverse=True,
            ),
        },
        "test_comparison": {
            "baseline": baseline_test,
            "optimized": optimized_test,
            "deltas": deltas,
            "both_win_rate_and_payoff_improved": both_improved,
        },
        "full_period_reference": {
            "baseline": ai_trade_metrics(baseline_trades),
            "optimized": ai_trade_metrics(optimized_trades),
            "baseline_by_year": yearly_metrics(baseline_trades),
            "optimized_by_year": yearly_metrics(optimized_trades),
        },
        "recommendations": recommendations,
        "daily_manifest": daily_manifest,
        "signal_dates": serializable_signals,
        "risk_boundary": [
            "历史研究与决策支持，不构成收益承诺或自动交易指令。",
            "当前名称和当前流动性排序存在幸存者偏差。",
            "未建模组合资金占用和同时持仓上限。",
        ],
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    output_markdown.write_text(
        render_ai_backtest_markdown(payload),
        encoding="utf-8",
    )
    payload["artifacts"] = {
        "json": file_binding(output_json),
        "markdown": file_binding(output_markdown),
    }
    return payload


def backtest_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="黄金点火AI真实K线回测")
    parser.add_argument("--formula", default=AI_FORMULA_NAME)
    parser.add_argument("--start-date", type=int, default=20210101)
    parser.add_argument("--end-date", type=int, default=20260814)
    parser.add_argument("--max-symbols", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--output-json")
    parser.add_argument("--output-markdown")
    args = parser.parse_args(argv)
    if args.start_date >= args.end_date:
        parser.error("--start-date 必须早于 --end-date")
    if args.max_symbols < 50 or args.max_symbols > 2000:
        parser.error("--max-symbols 必须在50到2000之间")
    if args.batch_size < 1 or args.batch_size > 100:
        parser.error("--batch-size 必须在1到100之间")
    output_json = Path(args.output_json).resolve() if args.output_json else (
        RESULTS_DIR / f"golden_ignition_ai_backtest_{datetime.now():%Y%m%d_%H%M%S}.json"
    )
    output_markdown = Path(args.output_markdown).resolve() if args.output_markdown else (
        RESULTS_DIR / f"golden_ignition_ai_backtest_{datetime.now():%Y%m%d_%H%M%S}.md"
    )
    try:
        payload = run_ai_backtest(
            formula_name=args.formula,
            start_date=args.start_date,
            end_date=args.end_date,
            max_symbols=args.max_symbols,
            batch_size=args.batch_size,
            output_json=output_json,
            output_markdown=output_markdown,
        )
    except Exception as error:
        print(json.dumps({
            "status": "BLOCKED",
            "skill": "golden-ignition",
            "operation": "backtest",
            "formula_name": args.formula,
            "error": f"{type(error).__name__}: {error}",
        }, ensure_ascii=False))
        return 2
    comparison = payload["test_comparison"]
    print(json.dumps({
        "status": payload["status"],
        "skill": "golden-ignition",
        "operation": "backtest",
        "formula_name": args.formula,
        "data": payload["data"],
        "optimized_parameters": payload["optimization"]["optimized_parameters"],
        "test_comparison": comparison,
        "artifacts": payload["artifacts"],
    }, ensure_ascii=False))
    return 0


def tq_xg_history(
    hub: Any,
    formula_name: str,
    symbols: list[str],
    *,
    count: int,
    dividend_type: int,
) -> dict[str, Any]:
    stdout_log = io.StringIO()
    stderr_log = io.StringIO()
    tq = None
    init_path = None
    try:
        with hub.TQLock() as lock:
            with contextlib.redirect_stdout(stdout_log), contextlib.redirect_stderr(stderr_log):
                tq, init_path = hub.load_tq()
                result = tq.formula_process_mul_xg(
                    formula_name=formula_name,
                    return_count=0,
                    return_date=True,
                    stock_list=symbols,
                    stock_period="1d",
                    count=count,
                    dividend_type=dividend_type,
                )
            waited_ms = lock.waited_ms
    except Exception as exc:
        result = {}
        waited_ms = None
        error = f"{type(exc).__name__}: {exc}"
    else:
        error = None
    finally:
        if tq is not None:
            if hasattr(tq, "_release"):
                tq._release()
            else:
                tq.close()
    ok = bool(result) and isinstance(result, dict) and str(result.get("ErrorId", "0")) in {"0", "19"}
    payload = {
        "ok": ok,
        "formula": formula_name,
        "kind": "xg",
        "symbols": symbols,
        "count": count,
        "dividend_type": dividend_type,
        "return_date": True,
        "result": result,
        "init_path": str(init_path) if init_path else None,
        "lock_waited_ms": waited_ms,
    }
    if error:
        payload["error"] = error
    if stdout_log.getvalue().strip():
        payload["tq_stdout"] = stdout_log.getvalue().strip()
    if stderr_log.getvalue().strip():
        payload["tq_stderr"] = stderr_log.getvalue().strip()
    return payload


def probe_ai_formula(
    symbol_input: str,
    count: int,
    formula_name: str = AI_FORMULA_NAME,
) -> dict[str, Any]:
    hub = load_tdx_hub()
    symbol = hub.symbol_suffix(symbol_input)
    rows = hub.read_day_records(symbol, count)
    if not rows:
        raise RuntimeError(f"本地通达信日线为空：{symbol}")
    probe_count = min(count, 120)
    formula_attempts: list[dict[str, Any]] = []
    formula: dict[str, Any] | None = None
    working_kind: str | None = None
    working_dividend: int | None = None
    for kind, dividend_type in (("zb", 1), ("zb", 0), ("xg", 1), ("xg", 0)):
        candidate = hub.tq_formula(
            formula_name,
            symbol,
            probe_count,
            kind,
            dividend_type,
        )
        formula_attempts.append(
            {
                "kind": kind,
                "dividend_type": dividend_type,
                "count": probe_count,
                "payload": candidate,
            }
        )
        if candidate.get("ok") is True:
            formula = candidate
            working_kind = kind
            working_dividend = dividend_type
            break
    if formula is None:
        diagnostics = [
            {
                "kind": item["kind"],
                "dividend_type": item["dividend_type"],
                "count": item["count"],
                "diagnostics": formula_failure_diagnostics(item["payload"]),
            }
            for item in formula_attempts
        ]
        raise RuntimeError(
            "通达信公式四组合执行均失败："
            + json.dumps(diagnostics, ensure_ascii=False)
        )
    if working_kind == "xg":
        history_formula = tq_xg_history(
            hub,
            formula_name,
            [symbol],
            count=count,
            dividend_type=int(working_dividend or 0),
        )
        if history_formula.get("ok") is not True:
            raise RuntimeError(
                "通达信历史选股公式执行失败："
                + formula_failure_diagnostics(history_formula)
            )
        formula = history_formula
    elif count != probe_count:
        full_formula = hub.tq_formula(
            formula_name,
            symbol,
            count,
            working_kind,
            working_dividend,
        )
        if full_formula.get("ok") is not True:
            raise RuntimeError(
                "通达信公式短窗口成功但完整窗口失败："
                + formula_failure_diagnostics(full_formula)
            )
        formula = full_formula
    node = (formula.get("result") or {}).get(symbol, {})
    if not isinstance(node, dict):
        raise RuntimeError(f"通达信公式没有返回字段对象：{symbol}")
    series = {name: value for name, value in node.items() if isinstance(value, list)}
    raw_xg = series.get("XG", [])
    selected = (
        "XG"
        if raw_xg and all(isinstance(item, dict) for item in raw_xg)
        else select_signal_field(series, expected_length=min(count, len(rows)))
    )
    dates = [str(row["date"]) for row in rows]
    signal_dates = (
        extract_xg_signal_dates(series.get(selected, []), fallback_dates=dates)
        if selected
        else []
    )
    summaries: dict[str, Any] = {}
    for name, raw in sorted(series.items()):
        values = [
            number(item.get("Value", item.get("value")))
            if isinstance(item, dict)
            else number(item)
            for item in raw
        ]
        finite = [value for value in values if value is not None and math.isfinite(value)]
        summaries[name] = {
            "count": len(raw),
            "finite_count": len(finite),
            "positive_count": sum(value > 0 for value in finite),
            "zero_count": sum(abs(value) <= 1e-12 for value in finite),
            "min": min(finite) if finite else None,
            "max": max(finite) if finite else None,
            "tail": raw[-10:],
        }
    return {
        "status": "PASS",
        "skill": "golden-ignition",
        "operation": "probe-ai",
        "formula_name": formula_name,
        "formula_installed": True,
        "formula_registered_in_text_registry": formula.get("registered") is True,
        "working_kind": working_kind,
        "working_dividend_type": working_dividend,
        "probe_attempts": formula_attempts,
        "symbol": symbol,
        "daily_count": len(rows),
        "daily_start": dates[0],
        "daily_end": dates[-1],
        "signal_field_candidate": selected,
        "signal_dates": signal_dates,
        "field_summaries": summaries,
        "formula_result": formula,
        "data_source": file_binding(hub.day_path(symbol)),
    }


def probe_ai_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="探测黄金点火AI真实历史输出字段")
    parser.add_argument("symbol")
    parser.add_argument("--count", type=int, default=600)
    parser.add_argument("--formula", default=AI_FORMULA_NAME)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    if args.count < 30 or args.count > 5000:
        parser.error("--count 必须在30到5000之间")
    try:
        payload = probe_ai_formula(args.symbol, args.count, args.formula)
    except Exception as error:
        payload = {
            "status": "BLOCKED",
            "skill": "golden-ignition",
            "operation": "probe-ai",
            "formula_name": args.formula,
            "input": args.symbol,
            "error": f"{type(error).__name__}: {error}",
        }
    output = Path(args.output).resolve() if args.output else (
        RESULTS_DIR / f"golden_ignition_ai_probe_{six_digit_code(args.symbol)}_{datetime.now():%Y%m%d_%H%M%S}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "skill": "golden-ignition",
        "operation": "probe-ai",
        "formula_name": args.formula,
        "symbol": payload.get("symbol"),
        "signal_field_candidate": payload.get("signal_field_candidate"),
        "result_path": str(output),
    }, ensure_ascii=False))
    return 0 if payload["status"] == "PASS" else 2


def analyze(symbol_input: str, lookback: int, target_name: str | None) -> dict[str, Any]:
    hub = load_tdx_hub()
    input_code = six_digit_code(symbol_input)
    underlying = bond_underlying(input_code)
    target_type = "convertible_bond" if underlying else "stock"
    analysis_input = underlying or input_code
    analysis_symbol = hub.symbol_suffix(analysis_input)
    input_symbol = hub.symbol_suffix(symbol_input)

    rows = hub.read_day_records(analysis_symbol, 240)
    if len(rows) < 30:
        raise RuntimeError(f"本地通达信日线不足30条：{analysis_symbol}")
    closes = [float(row["close"]) for row in rows]
    ema3 = ema(closes, 3)
    ema21 = ema(closes, 21)
    crosses: list[dict[str, Any]] = []
    for index in range(1, len(rows)):
        triggered = ema3[index] > ema21[index] and ema3[index - 1] <= ema21[index - 1]
        if triggered:
            crosses.append(
                {
                    "date": rows[index]["date"],
                    "ema3": round(ema3[index], 4),
                    "ema21": round(ema21[index], 4),
                    "close": rows[index]["close"],
                }
            )
    recent_dates = {row["date"] for row in rows[-lookback:]}
    recent_crosses = [item for item in crosses if item["date"] in recent_dates]

    formula = hub.tq_formula(FORMULA_NAME, analysis_symbol, max(lookback, 5), "zb", 1)
    node = (formula.get("result") or {}).get(analysis_symbol, {}) if formula.get("ok") else {}
    formula_values = {field: number(node.get(field)) for field in IGNITION_FIELDS}
    formula_triggered = any(value is not None and value > 0 for value in formula_values.values())
    triggered = formula_triggered or bool(recent_crosses)

    return {
        "status": "PASS",
        "skill": "golden-ignition",
        "name_cn": "黄金点火",
        "scope": "通用证券点火分析；股票直接分析，可转债自动映射正股",
        "generated_at": datetime.now().astimezone().isoformat(),
        "input_symbol": input_symbol,
        "target_name": target_name or input_symbol,
        "target_type": target_type,
        "analysis_symbol": analysis_symbol,
        "underlying_symbol": analysis_symbol if underlying else None,
        "latest_trading_date": datetime.strptime(rows[-1]["date"], "%Y%m%d").date().isoformat(),
        "lookback_trading_days": lookback,
        "signal_definition": "CROSS(EMA(CLOSE,3),EMA(CLOSE,21))",
        "signal_status": "HIT" if triggered else "NO_SIGNAL",
        "ignition_signal": triggered,
        "local_daily": {
            "latest_close": rows[-1]["close"],
            "latest_ema3": round(ema3[-1], 4),
            "latest_ema21": round(ema21[-1], 4),
            "recent_crosses": recent_crosses,
        },
        "tdx_formula": {
            "ok": formula.get("ok") is True,
            "public_name": FORMULA_NAME,
            "runtime_name": formula.get("tq_formula") or FORMULA_CALL_NAME,
            "symbol": analysis_symbol,
            "fields": formula_values,
            "current_triggered": formula_triggered,
            "generated_at": formula.get("generated_at"),
        },
        "data_sources": {
            "tdx_hub": file_binding(TDX_HUB_PATH),
            "daily_file": file_binding(hub.day_path(analysis_symbol)),
            "bond_mapping": file_binding(BOND_MAP_PATH) if underlying else None,
        },
        "risk_boundary": [
            "点火信号是技术条件，不代表必然上涨。",
            "可转债输入仅以正股判断点火，仍需另行检查溢价率、余额、强赎与流动性。",
            "本地日线日期与盘中公式快照不一致时，必须分别标注，不能冒充同日收盘结论。",
        ],
    }


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "backtest":
        return backtest_main(sys.argv[2:])
    if len(sys.argv) > 1 and sys.argv[1] == "probe-ai":
        return probe_ai_main(sys.argv[2:])
    parser = argparse.ArgumentParser(description="通用黄金点火分析：股票或可转债代码")
    parser.add_argument("symbol", help="股票或可转债代码，例如 600577.SH、110074.SH")
    parser.add_argument("--lookback", type=int, default=5, help="近期窗口，默认5个交易日")
    parser.add_argument("--name", help="可选目标名称")
    parser.add_argument("--output", help="可选JSON输出路径")
    args = parser.parse_args()
    if args.lookback < 1 or args.lookback > 30:
        parser.error("--lookback 必须在1到30之间")

    try:
        payload = analyze(args.symbol, args.lookback, args.name)
    except Exception as error:
        payload = {
            "status": "BLOCKED",
            "skill": "golden-ignition",
            "generated_at": datetime.now().astimezone().isoformat(),
            "input": args.symbol,
            "error": f"{type(error).__name__}: {error}",
        }

    output = Path(args.output).resolve() if args.output else (
        RESULTS_DIR / f"golden_ignition_{six_digit_code(args.symbol)}_{datetime.now():%Y%m%d_%H%M%S}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "status": payload["status"],
        "skill": "golden-ignition",
        "input_symbol": payload.get("input_symbol", args.symbol),
        "analysis_symbol": payload.get("analysis_symbol"),
        "latest_trading_date": payload.get("latest_trading_date"),
        "signal_status": payload.get("signal_status"),
        "result_path": str(output),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
