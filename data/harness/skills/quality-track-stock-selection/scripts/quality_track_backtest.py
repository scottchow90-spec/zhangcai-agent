from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import quality_track_live as live


ENTRY_COST_RATE = 0.0013  # 0.10% slippage + 0.03% commission
EXIT_COST_RATE = 0.0018   # 0.10% slippage + 0.03% commission + 0.05% stamp duty
GROSS_EXPOSURE = 0.60
HOLDING_DAYS = 5


def index_rows(rows: list[dict[str, float | int]]) -> tuple[list[int], dict[int, int]]:
    dates = [int(row["date"]) for row in rows]
    return dates, {date_i: index for index, date_i in enumerate(dates)}


def feature_at(rows: list[dict[str, float | int]], index: int) -> dict[str, float] | None:
    if index < 120 or index >= len(rows) - HOLDING_DAYS - 1:
        return None
    closes = [float(row["close"]) for row in rows[index - 60 : index + 1]]
    amounts = [float(row["amount"]) for row in rows[index - 19 : index + 1]]
    volumes = [float(row["volume"]) for row in rows[index - 5 : index + 1]]
    close = closes[-1]
    previous_close = closes[-2]
    ma20 = statistics.fmean(closes[-20:])
    ma60 = statistics.fmean(closes[-60:])
    ma20_prev5 = statistics.fmean(closes[-25:-5])
    previous_volumes = [value for value in volumes[:-1] if value > 0]
    if close <= 0 or previous_close <= 0 or not previous_volumes:
        return None
    atr_value = live.atr(rows[max(0, index - 29) : index + 1])
    return {
        "close": close,
        "return_1d": close / previous_close - 1.0,
        "return_5d": close / closes[-6] - 1.0,
        "return_20d": close / closes[-21] - 1.0,
        "ma20": ma20,
        "ma60": ma60,
        "ma20_prev5": ma20_prev5,
        "volume_ratio": volumes[-1] / statistics.fmean(previous_volumes),
        "average_amount_20d": statistics.fmean(amounts),
        "atr": atr_value,
        "atr_pct": atr_value / close,
    }


def stock_score(feature: dict[str, float], sector_rank: int) -> float:
    pct5 = feature["return_5d"]
    momentum = 12.0 if 0.02 <= pct5 <= 0.15 else 8.0 if 0 <= pct5 <= 0.20 else 3.0
    trend = (
        (8.0 if feature["close"] > feature["ma20"] else 0.0)
        + (5.0 if feature["close"] > feature["ma60"] else 0.0)
        + (5.0 if feature["ma20"] > feature["ma20_prev5"] else 0.0)
    )
    volume = 7.0 if 1.0 <= feature["volume_ratio"] <= 2.5 else 4.0 if 0.8 <= feature["volume_ratio"] < 1.0 else 0.0
    volatility = 5.0 if feature["atr_pct"] <= 0.06 else 2.0 if feature["atr_pct"] <= 0.09 else 0.0
    liquidity = min(6.0, math.log10(max(1.0, feature["average_amount_20d"] / 10_000_000.0)))
    sector = max(0.0, 30.0 - 4.0 * (sector_rank - 1))
    return sector + trend + momentum + volume + volatility + liquidity


def max_drawdown(equity: list[float]) -> float:
    peak = equity[0]
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        worst = min(worst, value / peak - 1.0)
    return worst


def annualized_return(total_return: float, trading_days: int) -> float:
    if trading_days <= 0 or total_return <= -1:
        return -1.0
    return (1.0 + total_return) ** (252.0 / trading_days) - 1.0


def matched_benchmark_return(raw_return: float, filled_count: int) -> float:
    """Match benchmark exposure to periods in which the strategy is invested."""
    return GROSS_EXPOSURE * raw_return if filled_count > 0 else 0.0


def run(output_path: Path, lookback_sessions: int = 500, as_of_date: int | None = None) -> dict[str, Any]:
    concepts = [item for item in live.load_concepts() if live.map_track(str(item["name"]))]
    names = live.load_names()
    universe = sorted({code for concept in concepts for code in concept["codes"]})
    rows_by_code: dict[str, list[dict[str, float | int]]] = {}
    index_by_code: dict[str, dict[int, int]] = {}
    for code7 in universe:
        rows = live.read_day_rows(code7, lookback_sessions + 225)
        if as_of_date is not None:
            rows = [row for row in rows if int(row["date"]) <= as_of_date]
        if len(rows) < 180:
            continue
        rows_by_code[code7] = rows
        _dates, date_index = index_rows(rows)
        index_by_code[code7] = date_index

    benchmark_rows = live.read_day_rows("1000300")
    if as_of_date is not None:
        benchmark_rows = [row for row in benchmark_rows if int(row["date"]) <= as_of_date]
    if len(benchmark_rows) < 180:
        raise RuntimeError("CSI 300 local benchmark history unavailable")
    benchmark_dates, benchmark_index = index_rows(benchmark_rows)
    first_signal_index = max(120, len(benchmark_dates) - lookback_sessions)
    last_signal_exclusive = len(benchmark_dates) - HOLDING_DAYS - 1
    signal_indices = [
        index for index in range(first_signal_index, last_signal_exclusive)
        if index % HOLDING_DAYS == 0
    ]
    signal_dates = [benchmark_dates[index] for index in signal_indices]
    concept_by_name = {str(item["source_name"]): item for item in concepts}

    periods: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    strategy_equity = [1.0]
    benchmark_equity = [1.0]
    benchmark_equity_always_exposed = [1.0]
    leakage_violations: list[str] = []
    for signal_date in signal_dates:
        benchmark_signal_index = benchmark_index[signal_date]
        benchmark_feature = feature_at(benchmark_rows, benchmark_signal_index)
        market_regime_pass = bool(
            benchmark_feature is not None
            and benchmark_feature["close"] > benchmark_feature["ma20"]
            and benchmark_feature["ma20"] > benchmark_feature["ma20_prev5"]
        )
        features: dict[str, dict[str, float]] = {}
        for code7, rows in rows_by_code.items():
            row_index = index_by_code[code7].get(signal_date)
            if row_index is None:
                continue
            feature = feature_at(rows, row_index)
            if feature is not None:
                features[code7] = feature

        sector_rows: list[dict[str, Any]] = []
        for source_name, concept in concept_by_name.items():
            member_features = [features[code] for code in concept["codes"] if code in features]
            if len(member_features) < 5 or len(member_features) / len(concept["codes"]) < 0.50:
                continue
            mean1 = statistics.fmean(item["return_1d"] for item in member_features)
            mean5 = statistics.fmean(item["return_5d"] for item in member_features)
            breadth = sum(item["return_1d"] > 0 for item in member_features) / len(member_features)
            if not market_regime_pass or mean1 <= 0 or mean5 <= 0 or breadth < 0.55:
                continue
            sector_rows.append({
                "source_name": source_name,
                "name": concept["name"],
                "codes": concept["codes"],
                "score": mean1 * 100.0 + mean5 * 30.0 + breadth * 5.0,
                "mean_return_1d": mean1,
                "mean_return_5d": mean5,
                "up_ratio": breadth,
            })
        sector_rows.sort(key=lambda item: (-float(item["score"]), str(item["source_name"])))
        selected_sectors = sector_rows[:5]
        code_sector_rank: dict[str, int] = {}
        for sector_rank, sector in enumerate(selected_sectors, 1):
            for code7 in sector["codes"]:
                code_sector_rank[code7] = min(sector_rank, code_sector_rank.get(code7, sector_rank))

        candidates: list[tuple[float, str, dict[str, float]]] = []
        for code7, sector_rank in code_sector_rank.items():
            feature = features.get(code7)
            if feature is None:
                continue
            symbol = live.symbol_from_code7(code7)
            name = names.get(symbol, "")
            if not name or name.upper().startswith(("ST", "*ST")):
                continue
            if feature["close"] < 2.0 or feature["average_amount_20d"] < 50_000_000:
                continue
            if not (0.02 <= feature["return_5d"] <= 0.15):
                continue
            if feature["close"] <= feature["ma20"] or feature["ma20"] <= feature["ma20_prev5"]:
                continue
            if feature["close"] / feature["ma20"] > 1.25:
                continue
            if feature["return_1d"] >= live.limit_ratio(code7) * 0.95:
                continue
            if feature["return_1d"] > 0.07:
                continue
            candidates.append((stock_score(feature, sector_rank), code7, feature))
        candidates.sort(key=lambda item: (-item[0], item[1]))

        filled: list[dict[str, Any]] = []
        for score, code7, feature in candidates[:12]:
            rows = rows_by_code[code7]
            signal_index = index_by_code[code7][signal_date]
            entry_index = signal_index + 1
            exit_index = entry_index + HOLDING_DAYS - 1
            if exit_index >= len(rows):
                continue
            entry_row = rows[entry_index]
            if int(entry_row["date"]) <= signal_date:
                leakage_violations.append(f"entry_not_after_signal:{code7}:{signal_date}")
                continue
            raw_entry = float(entry_row["open"])
            if raw_entry <= 0 or raw_entry / feature["close"] - 1.0 > 0.03:
                continue
            if raw_entry / feature["close"] - 1.0 >= live.limit_ratio(code7) * 0.95:
                continue
            entry_price = raw_entry * (1.0 + ENTRY_COST_RATE)
            stop_distance = min(0.08, max(0.02, 2.0 * feature["atr"] / feature["close"]))
            stop_price = raw_entry * (1.0 - stop_distance)
            exit_price: float | None = None
            exit_date: int | None = None
            exit_reason = "time_exit"
            for current_index in range(entry_index, exit_index + 1):
                current = rows[current_index]
                if float(current["low"]) <= stop_price:
                    exit_price = stop_price * (1.0 - EXIT_COST_RATE)
                    exit_date = int(current["date"])
                    exit_reason = "stop"
                    break
            if exit_price is None:
                exit_row = rows[exit_index]
                exit_price = float(exit_row["close"]) * (1.0 - EXIT_COST_RATE)
                exit_date = int(exit_row["date"])
            net_return = exit_price / entry_price - 1.0
            trade = {
                "signal_date": signal_date,
                "symbol": live.symbol_from_code7(code7),
                "name": names.get(live.symbol_from_code7(code7)),
                "score": round(score, 6),
                "feature_data_end": signal_date,
                "entry_date": int(entry_row["date"]),
                "raw_entry_open": raw_entry,
                "entry_price_after_cost": round(entry_price, 6),
                "stop_price_before_exit_cost": round(stop_price, 6),
                "exit_date": exit_date,
                "exit_price_after_cost": round(exit_price, 6),
                "exit_reason": exit_reason,
                "net_return": round(net_return, 8),
                "entry_cost_rate": ENTRY_COST_RATE,
                "exit_cost_rate": EXIT_COST_RATE,
            }
            filled.append(trade)
            if len(filled) == 5:
                break

        stock_return = statistics.fmean(item["net_return"] for item in filled) if filled else 0.0
        portfolio_return = GROSS_EXPOSURE * stock_return
        benchmark_entry = benchmark_rows[benchmark_signal_index + 1]
        benchmark_exit = benchmark_rows[benchmark_signal_index + HOLDING_DAYS]
        benchmark_raw_return = float(benchmark_exit["close"]) / float(benchmark_entry["open"]) - 1.0
        benchmark_period_return = matched_benchmark_return(benchmark_raw_return, len(filled))
        benchmark_period_return_always_exposed = GROSS_EXPOSURE * benchmark_raw_return
        strategy_equity.append(strategy_equity[-1] * (1.0 + portfolio_return))
        benchmark_equity.append(benchmark_equity[-1] * (1.0 + benchmark_period_return))
        benchmark_equity_always_exposed.append(
            benchmark_equity_always_exposed[-1] * (1.0 + benchmark_period_return_always_exposed)
        )
        trades.extend(filled)
        periods.append({
            "signal_date": signal_date,
            "selected_sector_count": len(selected_sectors),
            "market_regime_pass": market_regime_pass,
            "candidate_count": len(candidates),
            "filled_count": len(filled),
            "portfolio_return": round(portfolio_return, 8),
            "benchmark_raw_return": round(benchmark_raw_return, 8),
            "benchmark_return": round(benchmark_period_return, 8),
            "benchmark_return_always_exposed_60pct": round(benchmark_period_return_always_exposed, 8),
            "strategy_equity": round(strategy_equity[-1], 8),
            "benchmark_equity": round(benchmark_equity[-1], 8),
            "benchmark_equity_always_exposed_60pct": round(benchmark_equity_always_exposed[-1], 8),
        })

    trading_days = len(periods) * HOLDING_DAYS
    strategy_total = strategy_equity[-1] - 1.0
    benchmark_total = benchmark_equity[-1] - 1.0
    benchmark_total_always_exposed = benchmark_equity_always_exposed[-1] - 1.0
    period_returns = [float(item["portfolio_return"]) for item in periods]
    positive_periods = sum(value > 0 for value in period_returns)
    active_periods = sum(int(item["filled_count"]) > 0 for item in periods)
    metrics = {
        "period_count": len(periods),
        "active_period_count": active_periods,
        "inactive_period_count": len(periods) - active_periods,
        "trade_count": len(trades),
        "trading_days_covered": trading_days,
        "strategy_total_return_pct": round(strategy_total * 100.0, 4),
        "benchmark_total_return_pct_at_same_60pct_exposure": round(benchmark_total * 100.0, 4),
        "benchmark_total_return_pct_always_exposed_60pct": round(benchmark_total_always_exposed * 100.0, 4),
        "excess_return_pct": round((strategy_total - benchmark_total) * 100.0, 4),
        "excess_return_pct_vs_always_exposed_60pct": round(
            (strategy_total - benchmark_total_always_exposed) * 100.0, 4
        ),
        "strategy_annualized_return_pct": round(annualized_return(strategy_total, trading_days) * 100.0, 4),
        "benchmark_annualized_return_pct": round(annualized_return(benchmark_total, trading_days) * 100.0, 4),
        "benchmark_annualized_return_pct_always_exposed_60pct": round(
            annualized_return(benchmark_total_always_exposed, trading_days) * 100.0, 4
        ),
        "max_drawdown_pct": round(max_drawdown(strategy_equity) * 100.0, 4),
        "benchmark_max_drawdown_pct": round(max_drawdown(benchmark_equity) * 100.0, 4),
        "benchmark_max_drawdown_pct_always_exposed_60pct": round(
            max_drawdown(benchmark_equity_always_exposed) * 100.0, 4
        ),
        "positive_period_ratio_pct": round(positive_periods / len(periods) * 100.0, 4) if periods else 0.0,
        "trade_win_rate_pct": round(sum(item["net_return"] > 0 for item in trades) / len(trades) * 100.0, 4) if trades else 0.0,
        "average_trade_return_pct": round(statistics.fmean(item["net_return"] for item in trades) * 100.0, 4) if trades else 0.0,
    }
    checks = {
        "at_least_50_non_overlapping_periods": metrics["period_count"] >= 50,
        "positive_average_trade_after_cost": metrics["average_trade_return_pct"] > 0,
        "positive_excess_return": metrics["excess_return_pct"] > 0,
        "max_drawdown_not_below_minus_25pct": metrics["max_drawdown_pct"] >= -25.0,
        "trade_win_rate_at_least_45pct": metrics["trade_win_rate_pct"] >= 45.0,
        "no_lookahead_violations": not leakage_violations,
        "every_trade_has_nonzero_cost": all(item["entry_cost_rate"] > 0 and item["exit_cost_rate"] > 0 for item in trades),
    }
    payload = {
        "workflow": "优质赛道 V2 execution-layer walk-forward backtest",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "scope": "price/sector execution layer only",
        "not_validated": [
            "historical event-to-track mapping: local cache only retains recent news",
            "historical company financial/announcement gates: point-in-time snapshots unavailable",
        ],
        "biases": {
            "current_concept_membership_snapshot": True,
            "survivorship_bias": True,
            "claim_boundary": "does not validate the complete live workflow or authorize real-money deployment",
        },
        "parameters": {
            "lookback_sessions": lookback_sessions,
            "signal_interval_sessions": HOLDING_DAYS,
            "holding_days": HOLDING_DAYS,
            "max_positions": 5,
            "gross_exposure": GROSS_EXPOSURE,
            "entry_cost_rate": ENTRY_COST_RATE,
            "exit_cost_rate": EXIT_COST_RATE,
            "entry_timing": "next trading day open",
            "exit_timing": "fifth holding-session close or earlier stop",
            "stop": "2 ATR, minimum 2%, maximum 8%",
            "sampling_anchor": "absolute CSI300 history index modulo holding_days equals zero",
            "benchmark_exposure_rule": "60% only when strategy has filled positions; otherwise 0%",
            "benchmark_always_exposed_diagnostic": "60% in every sampled period",
        },
        "data": {
            "source": "C:/new_tdx_mock/vipdoc local daily bars",
            "benchmark": "000300.SH",
            "universe_current_member_count": len(universe),
            "loaded_history_count": len(rows_by_code),
            "first_signal_date": signal_dates[0] if signal_dates else None,
            "last_signal_date": signal_dates[-1] if signal_dates else None,
            "as_of_date": as_of_date or benchmark_dates[-1],
        },
        "metrics": metrics,
        "readiness_checks": checks,
        "leakage_violations": leakage_violations,
        "periods": periods,
        "trades": trades,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        "QUALITY_TRACK_BACKTEST "
        f"status={payload['status']} periods={metrics['period_count']} trades={metrics['trade_count']} "
        f"total={metrics['strategy_total_return_pct']} excess={metrics['excess_return_pct']} "
        f"maxdd={metrics['max_drawdown_pct']}"
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="优质赛道 V2 执行层无未来数据回测")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lookback-sessions", type=int, default=500)
    parser.add_argument("--as-of-date", type=int)
    args = parser.parse_args()
    result = run(args.output, args.lookback_sessions, args.as_of_date)
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
