#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPORTS = SKILL_ROOT / "reports"
DRAGON_SCRIPT = Path(r"D:\C盘转移\日志\codex\skills\dragon-pullback\scripts\run_strong_leader_first_yin.py")
TDX_HUB_PATH = Path(r"D:\C盘转移\日志\codex\skills\tdx-local-hub\scripts\tdx_hub.py")
SCHEMA_VERSION = 1


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def quantile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def wilson_interval(wins: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 0.0
    probability = wins / total
    denominator = 1.0 + z * z / total
    center = (probability + z * z / (2.0 * total)) / denominator
    margin = z * math.sqrt(probability * (1.0 - probability) / total + z * z / (4.0 * total * total)) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def binding(path: Path) -> dict[str, Any]:
    return {"path": str(path), "size": path.stat().st_size, "sha256": file_sha256(path)}


def build_universe(scanner) -> tuple[list[dict[str, Any]], int]:
    names = scanner.load_names()
    industries = scanner.load_industries()
    base_rows = scanner.parse_dbf(scanner.BASE_DBF, {"GPDM", "LTAG", "SSDATE", "HY"})
    universe = []
    for item in base_rows:
        code = item.get("GPDM", "")
        market = scanner.market_for_code(code)
        if market is None:
            continue
        name = names.get((market, code), "")
        if not name or "ST" in name.upper() or "退" in name:
            continue
        float_shares = scanner.number(item.get("LTAG", "")) * 10_000.0
        if float_shares <= 0:
            continue
        universe.append(
            {
                "code": code,
                "market": market,
                "symbol": f"{code}.{market}",
                "name": name,
                "float_shares": float_shares,
                "listing_date": item.get("SSDATE", ""),
                "industry": industries.get((market, code)) or f"HY:{item.get('HY', '')}",
            }
        )
    return universe, len(base_rows)


def one_price_limit_up(scanner, previous: dict[str, Any], current: dict[str, Any], code: str) -> bool:
    target = scanner.limit_price(float(previous["close"]), scanner.limit_percent(code), 1)
    return float(current["low"]) >= target - 0.011 and float(current["close"]) >= target - 0.011


def one_price_limit_down(scanner, previous: dict[str, Any], current: dict[str, Any], code: str) -> bool:
    target = scanner.limit_price(float(previous["close"]), scanner.limit_percent(code), -1)
    return float(current["high"]) <= target + 0.011 and float(current["close"]) <= target + 0.011


def corporate_action_anomaly(scanner, rows: list[dict[str, Any]], start: int, end: int, code: str) -> bool:
    threshold = scanner.limit_percent(code) + 0.035
    for index in range(max(1, start), min(end + 1, len(rows))):
        previous_close = float(rows[index - 1]["close"])
        if previous_close <= 0:
            return True
        change = abs(float(rows[index]["close"]) / previous_close - 1.0)
        if change > threshold:
            return True
    return False


def resolved_exit(
    scanner,
    rows: list[dict[str, Any]],
    code: str,
    intended_index: int,
    price_field: str,
    max_defer: int,
) -> tuple[int, float, int] | None:
    if intended_index >= len(rows):
        return None
    if not one_price_limit_down(scanner, rows[intended_index - 1], rows[intended_index], code):
        return intended_index, float(rows[intended_index][price_field]), 0
    for defer in range(1, max_defer + 1):
        candidate = intended_index + defer
        if candidate >= len(rows):
            return None
        if not one_price_limit_down(scanner, rows[candidate - 1], rows[candidate], code):
            return candidate, float(rows[candidate]["open"]), defer
    return None


def net_return(entry_price: float, exit_price: float, commission: float, stamp: float, slippage: float) -> float:
    effective_buy = entry_price * (1.0 + commission + slippage)
    effective_sell = exit_price * (1.0 - commission - stamp - slippage)
    return effective_sell / effective_buy - 1.0


def make_outcome(
    entry_row: dict[str, Any],
    exit_row: dict[str, Any],
    entry_price: float,
    exit_price: float,
    commission: float,
    stamp: float,
    slippage: float,
    deferred_sessions: int,
    benchmark_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    gross = exit_price / entry_price - 1.0
    net = net_return(entry_price, exit_price, commission, stamp, slippage)
    benchmark_entry = benchmark_rows.get(str(entry_row["date"]))
    benchmark_exit = benchmark_rows.get(str(exit_row["date"]))
    benchmark_return = None
    excess_return = None
    if benchmark_entry and benchmark_exit and float(benchmark_entry["open"]) > 0:
        benchmark_return = float(benchmark_exit["close"]) / float(benchmark_entry["open"]) - 1.0
        excess_return = net - benchmark_return
    return {
        "entry_date": str(entry_row["date"]),
        "entry_price": round(entry_price, 4),
        "exit_date": str(exit_row["date"]),
        "exit_price": round(exit_price, 4),
        "gross_return": round(gross, 8),
        "net_return": round(net, 8),
        "benchmark_return": round(benchmark_return, 8) if benchmark_return is not None else None,
        "excess_return": round(excess_return, 8) if excess_return is not None else None,
        "exit_deferred_sessions": deferred_sessions,
    }


def calculate_trade_outcomes(
    scanner,
    rows: list[dict[str, Any]],
    signal_index: int,
    code: str,
    horizons: list[int],
    commission: float,
    stamp: float,
    slippage: float,
    max_defer: int,
    benchmark_rows: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    entry_index = signal_index + 1
    if entry_index >= len(rows):
        return None, "no_next_session"
    entry = rows[entry_index]
    if float(entry["volume"]) <= 0 or float(entry["amount"]) <= 0:
        return None, "next_session_no_liquidity"
    if one_price_limit_up(scanner, rows[signal_index], entry, code):
        return None, "next_session_one_price_limit_up"
    entry_price = float(entry["open"])
    if entry_price <= 0:
        return None, "invalid_entry_price"

    fixed: dict[str, Any] = {}
    for horizon in horizons:
        intended = entry_index + horizon - 1
        resolved = resolved_exit(scanner, rows, code, intended, "close", max_defer)
        if resolved is None:
            continue
        exit_index, exit_price, deferred = resolved
        fixed[str(horizon)] = make_outcome(
            entry,
            rows[exit_index],
            entry_price,
            exit_price,
            commission,
            stamp,
            slippage,
            deferred,
            benchmark_rows,
        )

    adaptive = None
    signal_low = float(rows[signal_index]["low"])
    signal_high = float(rows[signal_index]["high"])
    max_hold = 5
    trigger_reason = None
    intended_exit = None
    price_field = "close"
    for offset in range(max_hold):
        observation_index = entry_index + offset
        if observation_index >= len(rows):
            break
        closes = [float(item["close"]) for item in rows[max(0, observation_index - 4) : observation_index + 1]]
        close = float(rows[observation_index]["close"])
        if close < signal_low:
            trigger_reason = "close_below_first_yin_low"
            intended_exit = observation_index + 1
            price_field = "open"
            break
        no_new_high = max(float(item["high"]) for item in rows[entry_index : observation_index + 1]) <= signal_high
        if offset >= 2 and no_new_high and close < mean(closes):
            trigger_reason = "three_sessions_no_new_high_and_close_below_ma5"
            intended_exit = observation_index + 1
            price_field = "open"
            break
    if intended_exit is None:
        intended_exit = entry_index + max_hold - 1
        trigger_reason = "scheduled_five_session_exit"
        price_field = "close"
    resolved = resolved_exit(scanner, rows, code, intended_exit, price_field, max_defer)
    if resolved is not None:
        exit_index, exit_price, deferred = resolved
        adaptive = make_outcome(
            entry,
            rows[exit_index],
            entry_price,
            exit_price,
            commission,
            stamp,
            slippage,
            deferred,
            benchmark_rows,
        )
        adaptive["exit_reason"] = trigger_reason

    return {"fixed_horizons": fixed, "adaptive": adaptive}, None


def summarize_outcomes(signals: list[dict[str, Any]], outcome_key: str, horizon: str | None = None) -> dict[str, Any]:
    outcomes = []
    for signal in signals:
        value = signal["outcomes"].get(outcome_key)
        if horizon is not None:
            value = (value or {}).get(horizon)
        if value:
            outcomes.append(value)
    returns = [float(item["net_return"]) for item in outcomes]
    excess = [float(item["excess_return"]) for item in outcomes if item.get("excess_return") is not None]
    wins = sum(1 for value in returns if value > 0)
    losses = [value for value in returns if value < 0]
    gains = [value for value in returns if value > 0]
    low, high = wilson_interval(wins, len(returns))
    loss_sum = abs(sum(losses))
    return {
        "trades": len(returns),
        "mean_net_return_pct": round(mean(returns) * 100.0, 4),
        "median_net_return_pct": round(median(returns) * 100.0, 4),
        "win_rate_pct": round((wins / len(returns) * 100.0) if returns else 0.0, 3),
        "win_rate_95pct_wilson": [round(low * 100.0, 3), round(high * 100.0, 3)],
        "profit_factor": round(sum(gains) / loss_sum, 4) if loss_sum else None,
        "average_gain_pct": round(mean(gains) * 100.0, 4),
        "average_loss_pct": round(mean(losses) * 100.0, 4),
        "p10_pct": round(quantile(returns, 0.10) * 100.0, 4),
        "p90_pct": round(quantile(returns, 0.90) * 100.0, 4),
        "worst_pct": round(min(returns) * 100.0, 4) if returns else 0.0,
        "best_pct": round(max(returns) * 100.0, 4) if returns else 0.0,
        "mean_excess_vs_shanghai_pct": round(mean(excess) * 100.0, 4),
    }


def time_split(signals: list[dict[str, Any]], ready_only: bool) -> dict[str, Any]:
    eligible = [
        item
        for item in signals
        if item["grade"] in {"S", "T"}
        and item["outcomes"].get("adaptive")
        and (item.get("technical_trade_ready") if ready_only else True)
    ]
    eligible.sort(key=lambda item: (item["signal_date"], item["symbol"]))
    first = int(len(eligible) * 0.60)
    second = int(len(eligible) * 0.80)
    segments = {"first_60pct": eligible[:first], "middle_20pct": eligible[first:second], "last_20pct": eligible[second:]}
    return {
        key: {
            "start": values[0]["signal_date"] if values else None,
            "end": values[-1]["signal_date"] if values else None,
            **summarize_outcomes(values, "adaptive"),
        }
        for key, values in segments.items()
    }


def simulate_ten_slot_portfolio(signals: list[dict[str, Any]], ready_only: bool) -> dict[str, Any]:
    candidates = [
        item
        for item in signals
        if item["grade"] in {"S", "T"}
        and item["outcomes"].get("adaptive")
        and (item.get("technical_trade_ready") if ready_only else True)
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        grouped[item["outcomes"]["adaptive"]["entry_date"]].append(item)
    slots = [{"available_after": "", "multiplier": 1.0, "trades": 0} for _ in range(10)]
    scheduled = []
    skipped_capacity = 0
    grade_rank = {"S": 0, "T": 1}
    for entry_date in sorted(grouped):
        daily = sorted(grouped[entry_date], key=lambda item: (grade_rank[item["grade"]], -item["score"], item["symbol"]))[:3]
        for trade in daily:
            available = [index for index, slot in enumerate(slots) if slot["available_after"] < entry_date]
            if not available:
                skipped_capacity += 1
                continue
            slot_index = min(available, key=lambda index: slots[index]["available_after"])
            outcome = trade["outcomes"]["adaptive"]
            slots[slot_index]["available_after"] = outcome["exit_date"]
            slots[slot_index]["trades"] += 1
            scheduled.append(
                {
                    "slot": slot_index,
                    "symbol": trade["symbol"],
                    "grade": trade["grade"],
                    "score": trade["score"],
                    "entry_date": entry_date,
                    "exit_date": outcome["exit_date"],
                    "net_return": outcome["net_return"],
                }
            )
    equity = [0.1] * 10
    curve = [{"date": None, "equity": 1.0}]
    peak = 1.0
    max_drawdown = 0.0
    for event in sorted(scheduled, key=lambda item: (item["exit_date"], item["slot"])):
        equity[event["slot"]] *= 1.0 + float(event["net_return"])
        total = sum(equity)
        peak = max(peak, total)
        max_drawdown = min(max_drawdown, total / peak - 1.0)
        curve.append({"date": event["exit_date"], "equity": round(total, 8)})
    total_return = sum(equity) - 1.0
    start = min((item["entry_date"] for item in scheduled), default=None)
    end = max((item["exit_date"] for item in scheduled), default=None)
    cagr = None
    if start and end:
        days = max((dt.datetime.strptime(end, "%Y%m%d") - dt.datetime.strptime(start, "%Y%m%d")).days, 1)
        if 1.0 + total_return > 0:
            cagr = (1.0 + total_return) ** (365.0 / days) - 1.0
    return {
        "rules": {"slots": 10, "max_new_positions_per_day": 3, "position_fraction_per_slot": 0.10},
        "candidate_trades": len(candidates),
        "executed_trades": len(scheduled),
        "skipped_for_capacity": skipped_capacity,
        "start": start,
        "end": end,
        "total_return_pct": round(total_return * 100.0, 4),
        "cagr_pct": round(cagr * 100.0, 4) if cagr is not None else None,
        "max_drawdown_pct": round(max_drawdown * 100.0, 4),
        "final_equity": round(1.0 + total_return, 8),
        "equity_curve_tail": curve[-20:],
        "samples": scheduled[-20:],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="No-lookahead local TDX backtest for strong-leader first-yin signals")
    parser.add_argument("--lookback-sessions", type=int, default=750)
    parser.add_argument("--horizons", default="1,3,5,10")
    parser.add_argument("--commission-bps", type=float, default=3.0)
    parser.add_argument("--stamp-duty-bps", type=float, default=5.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--max-limit-down-defer", type=int, default=3)
    parser.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    started = dt.datetime.now().astimezone()
    horizons = sorted({int(value) for value in args.horizons.split(",") if int(value) > 0})
    if not horizons:
        raise SystemExit("at least one horizon is required")
    scanner = load_module("strong_leader_selector", DRAGON_SCRIPT)
    hub = load_module("tdx_local_hub", TDX_HUB_PATH)
    universe, base_records = build_universe(scanner)
    index_path = hub.day_path("999999.SH")
    index_rows = hub.read_records(index_path, hub.DAY_RECORD, hub.parse_day_record, 0)
    future_padding = max(horizons) + args.max_limit_down_defer + 2
    if len(index_rows) < args.lookback_sessions + future_padding + 30:
        start_position = 30
    else:
        start_position = len(index_rows) - args.lookback_sessions - future_padding
    signal_start_date = str(index_rows[start_position]["date"])
    signal_end_date = str(index_rows[-future_padding]["date"])
    benchmark_rows = {str(item["date"]): item for item in index_rows}
    read_limit = args.lookback_sessions + future_padding + 80
    commission = args.commission_bps / 10_000.0
    stamp = args.stamp_duty_bps / 10_000.0
    slippage = args.slippage_bps / 10_000.0

    signals: list[dict[str, Any]] = []
    skips: dict[str, int] = defaultdict(int)
    scan_stats: dict[str, int] = defaultdict(int)
    source_rows = []
    for meta in universe:
        path = hub.day_path(meta["symbol"])
        if not path.exists():
            scan_stats["missing_day_file"] += 1
            continue
        stat = path.stat()
        source_rows.append(f"{path}|{stat.st_size}|{stat.st_mtime_ns}")
        rows = hub.read_records(path, hub.DAY_RECORD, hub.parse_day_record, read_limit)
        if len(rows) < 60:
            scan_stats["insufficient_history"] += 1
            continue
        scan_stats["loaded"] += 1
        flags = scanner.build_limit_up_flags(rows, meta["code"])
        last_signal_index = len(rows) - future_padding
        for index in range(20, max(20, last_signal_index + 1)):
            date = str(rows[index]["date"])
            if date < signal_start_date or date > signal_end_date:
                continue
            # Exact necessary conditions for every supported grade.  Applying
            # them before evaluate_at avoids rebuilding the full close series
            # for bars that cannot possibly be a first-yin setup.
            if float(rows[index]["close"]) >= float(rows[index]["open"]):
                continue
            if not any(flags[max(1, index - 8) : index]):
                continue
            evaluated = scanner.evaluate_at(rows, index, meta, flags)
            if not evaluated:
                continue
            scan_stats[f"signal_{evaluated['grade']}"] += 1
            if corporate_action_anomaly(scanner, rows, index - 30, index + future_padding, meta["code"]):
                skips["corporate_action_or_price_anomaly"] += 1
                continue
            outcomes, reason = calculate_trade_outcomes(
                scanner,
                rows,
                index,
                meta["code"],
                horizons,
                commission,
                stamp,
                slippage,
                args.max_limit_down_defer,
                benchmark_rows,
            )
            if outcomes is None:
                skips[reason or "unknown"] += 1
                continue
            signal = {
                "signal_date": date,
                "symbol": meta["symbol"],
                "name": meta["name"],
                "industry": meta["industry"],
                "grade": evaluated["grade"],
                "metrics": evaluated["metrics"],
                "evaluation": evaluated,
                "outcomes": outcomes,
                "source_path": str(path),
            }
            signals.append(signal)

    signal_dates = {item["signal_date"] for item in signals}
    market_rows: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    sector_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for meta in universe:
        path = hub.day_path(meta["symbol"])
        if not path.exists():
            continue
        rows = hub.read_records(path, hub.DAY_RECORD, hub.parse_day_record, read_limit)
        if len(rows) < 6:
            continue
        flags = scanner.build_limit_up_flags(rows, meta["code"])
        for index in range(5, len(rows)):
            date = str(rows[index]["date"])
            if date not in signal_dates:
                continue
            previous = rows[index - 1]
            current = rows[index]
            change = float(current["close"]) / float(previous["close"]) - 1.0 if float(previous["close"]) else 0.0
            bucket = market_rows[date]
            bucket["total"] += 1
            bucket["advances" if change > 0.0001 else "declines" if change < -0.0001 else "flats"] += 1
            bucket["limit_ups"] += int(flags[index])
            bucket["limit_downs"] += int(scanner.is_limit_down(previous, current, meta["code"]))
            previous_five = float(rows[index - 5]["close"])
            if previous_five > 0:
                sector_values[(date, meta["industry"])].append(float(current["close"]) / previous_five - 1.0)

    sector_medians = {key: median(values) for key, values in sector_values.items() if values}
    ranked_by_date: dict[str, list[float]] = defaultdict(list)
    for (date, _industry), value in sector_medians.items():
        ranked_by_date[date].append(value)
    for values in ranked_by_date.values():
        values.sort()

    for signal in signals:
        date = signal["signal_date"]
        bucket = market_rows[date]
        market = {
            "advance_ratio": bucket["advances"] / max(bucket["total"], 1),
            "limit_up_down_ratio": bucket["limit_ups"] / max(bucket["limit_downs"], 1),
            "veto": bucket["limit_downs"] > bucket["limit_ups"],
        }
        sector_value = sector_medians.get((date, signal["industry"]))
        ranking = ranked_by_date.get(date, [])
        percentile = 0.0
        if sector_value is not None and ranking:
            percentile = sum(1 for value in ranking if value <= sector_value) / len(ranking)
        score, score_parts = scanner.score_candidate(signal["evaluation"], market, percentile)
        signal["score"] = score
        signal["score_parts"] = score_parts
        signal["market"] = {
            "advance_ratio": round(market["advance_ratio"], 4),
            "limit_up_down_ratio": round(market["limit_up_down_ratio"], 4),
            "veto": market["veto"],
        }
        signal["sector_strength_percentile"] = round(percentile, 4)
        signal["technical_trade_ready"] = bool(
            signal["grade"] in {"S", "T"} and score >= 70 and not market["veto"] and percentile >= 0.45
        )
        signal.pop("evaluation", None)

    grades = {
        "S": [item for item in signals if item["grade"] == "S"],
        "T": [item for item in signals if item["grade"] == "T"],
        "A": [item for item in signals if item["grade"] == "A"],
        "S_plus_T": [item for item in signals if item["grade"] in {"S", "T"}],
        "trade_ready_S_plus_T": [item for item in signals if item.get("technical_trade_ready")],
    }
    event_study = {}
    for group, items in grades.items():
        event_study[group] = {
            "fixed_horizons": {str(horizon): summarize_outcomes(items, "fixed_horizons", str(horizon)) for horizon in horizons},
            "adaptive_five_session": summarize_outcomes(items, "adaptive"),
        }

    raw_portfolio = simulate_ten_slot_portfolio(signals, ready_only=False)
    ready_portfolio = simulate_ten_slot_portfolio(signals, ready_only=True)
    raw_split = time_split(signals, ready_only=False)
    ready_split = time_split(signals, ready_only=True)
    ready_summary = event_study["trade_ready_S_plus_T"]["adaptive_five_session"]
    ready_last = ready_split["last_20pct"]
    if ready_summary["trades"] < 30:
        verdict = "INSUFFICIENT_EVIDENCE"
    elif (
        ready_summary["mean_net_return_pct"] > 0
        and (ready_summary["profit_factor"] or 0) >= 1.10
        and ready_last["mean_net_return_pct"] > 0
        and ready_portfolio["max_drawdown_pct"] >= -20.0
    ):
        verdict = "CONDITIONAL_PASS"
    else:
        verdict = "FAIL"

    current_selector_path = Path(r"D:\C盘转移\日志\codex\skills\dragon-pullback\reports\strong-leader-first-yin-latest.json")
    current_selector = json.loads(current_selector_path.read_text(encoding="utf-8-sig")) if current_selector_path.exists() else {}
    source_snapshot = hashlib.sha256("\n".join(sorted(source_rows)).encode("utf-8")).hexdigest()
    samples = sorted(signals, key=lambda item: (item["signal_date"], item["symbol"]), reverse=True)[:100]
    research_signals = sorted(
        (item for item in signals if item["grade"] in {"S", "T"}),
        key=lambda item: (item["signal_date"], item["symbol"]),
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "strategy_id": "strong-leader-first-yin-v1",
        "generated_at": started.isoformat(timespec="seconds"),
        "status": "CLEAN_PASS",
        "strategy_verdict": verdict,
        "backtest_completed": True,
        "data": {
            "source": "local_tdx_raw_daily",
            "tdx_root": str(scanner.TDX_ROOT),
            "signal_period": {"start": signal_start_date, "end": signal_end_date},
            "latest_market_date": str(index_rows[-1]["date"]),
            "lookback_sessions_requested": args.lookback_sessions,
            "base_dbf_records": base_records,
            "eligible_current_universe": len(universe),
            "scan_stats": dict(scan_stats),
            "source_snapshot_sha256": source_snapshot,
            "index_binding": binding(index_path),
        },
        "execution_assumptions": {
            "signal_timing": "signal known after close; entry only at next available session open",
            "entry_unavailable": "skip next-session one-price limit-up or zero-liquidity session",
            "exit_unavailable": f"defer one-price limit-down exit for at most {args.max_limit_down_defer} sessions",
            "fixed_horizons_sessions": horizons,
            "adaptive_exit": "after close invalidation, exit next session open; otherwise exit fifth session close",
            "commission_bps_each_side": args.commission_bps,
            "stamp_duty_bps_sell": args.stamp_duty_bps,
            "slippage_bps_each_side": args.slippage_bps,
            "minimum_commission": "not modeled",
        },
        "signal_counts": {
            "generated": {key: scan_stats.get(f"signal_{key}", 0) for key in ("S", "T", "A")},
            "executable_after_filters": {key: len(grades[key]) for key in ("S", "T", "A")},
            "trade_ready_S_plus_T": len(grades["trade_ready_S_plus_T"]),
            "skipped": dict(skips),
            "signal_dates": len(signal_dates),
        },
        "event_study": event_study,
        "time_robustness_split": {"raw_S_plus_T": raw_split, "trade_ready_S_plus_T": ready_split},
        "portfolio_simulation": {"raw_S_plus_T": raw_portfolio, "trade_ready_S_plus_T": ready_portfolio},
        "current_selector": {
            "binding": binding(current_selector_path) if current_selector_path.exists() else None,
            "latest_trade_date": current_selector.get("latest_trade_date"),
            "strict_count": current_selector.get("selection", {}).get("strict_count"),
            "turnover_divergence_count": current_selector.get("selection", {}).get("turnover_divergence_count"),
            "practical_count": current_selector.get("selection", {}).get("practical_count"),
            "technical_trade_ready_count": current_selector.get("selection", {}).get("technical_trade_ready_count"),
        },
        "known_biases": {
            "survivorship_bias": "current listed-stock universe is projected backward",
            "float_share_point_in_time_bias": "current float shares are used for historical turnover filters",
            "industry_point_in_time_bias": "current industry classification is projected backward",
            "price_adjustment": "raw unadjusted TDX prices; windows with moves beyond board limit plus 3.5pct are excluded",
            "historical_ST_status": "not available point in time; current ST names are excluded",
            "intraday_queue_and_impact": "not modeled beyond one-price limit checks and configured slippage",
            "true_out_of_sample": "not verified; chronological split is robustness evidence only",
        },
        "validation": {
            "no_same_bar_entry": all(
                item["outcomes"]["adaptive"] is None
                or item["outcomes"]["adaptive"]["entry_date"] > item["signal_date"]
                for item in signals
            ),
            "fees_and_slippage_included": True,
            "one_price_limit_checks_included": True,
            "corporate_action_anomaly_filter_included": True,
            "time_split_present": True,
            "selector_can_generate_signals": bool(signals),
        },
        "samples": samples,
        "research_signals_S_plus_T": research_signals,
        "risk_boundary": {
            "guaranteed_profit": False,
            "announcement_and_news_point_in_time_filter": "not verified",
            "real_broker_fill": "not verified",
            "live_forward_test": "not verified",
        },
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    output = Path(args.output) if args.output else REPORTS / f"strong-leader-first-yin-backtest-{started.strftime('%Y%m%d-%H%M%S')}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = REPORTS / "strong-leader-first-yin-backtest-latest.json"
    latest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "status": payload["status"],
        "strategy_verdict": verdict,
        "signal_period": payload["data"]["signal_period"],
        "executable_signals": len(signals),
        "trade_ready_signals": len(grades["trade_ready_S_plus_T"]),
        "raw_adaptive": event_study["S_plus_T"]["adaptive_five_session"],
        "trade_ready_adaptive": ready_summary,
        "trade_ready_portfolio": ready_portfolio,
        "report": str(output),
        "latest_report": str(latest),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
