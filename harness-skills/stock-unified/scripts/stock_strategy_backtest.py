#!/usr/bin/env python3
"""Unified, deterministic A-share strategy backtest and bounded optimizer."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import json
import math
import os
import statistics
import struct
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_tdx_root


_tdx_root_text = (
    os.environ.get("ZHANGCAI_TDX_ROOT")
    or os.environ.get("TDX_ROOT")
    or os.environ.get("TDX_ROOTS")
    or ""
).strip()
TDX_ROOT = resolve_tdx_root()
DAY_RECORD = struct.Struct("<IIIIIfII")
DAY_DIRS = {
    "SH": TDX_ROOT / "vipdoc" / "sh" / "lday",
    "SZ": TDX_ROOT / "vipdoc" / "sz" / "lday",
    "BJ": TDX_ROOT / "vipdoc" / "bj" / "lday",
}
TNF_FILES = {
    "SH": TDX_ROOT / "T0002" / "hq_cache" / "shs.tnf",
    "SZ": TDX_ROOT / "T0002" / "hq_cache" / "szs.tnf",
    "BJ": TDX_ROOT / "T0002" / "hq_cache" / "bjs.tnf",
}
EQUITY_PREFIXES = (
    "000", "001", "002", "003", "300", "301", "600", "601", "603", "605",
    "688", "689", "830", "831", "832", "833", "834", "835", "836", "837",
    "838", "839", "870", "871", "872", "873",
)
BOND_PREFIXES = ("110", "111", "113", "118", "123", "127", "128")
EXPECTED_STRATEGY_SKILLS = (
    "golden-ignition",
    "feilong-strategy",
    "a-share-bottom-fishing",
    "a-share-limit-up-mining",
    "convertible-bond-screening-strategy",
    "quality-track-stock-selection",
)


@dataclass(frozen=True)
class Bar:
    date: int
    open: float
    high: float
    low: float
    close: float
    amount: float
    volume: int


@dataclass(frozen=True)
class ExecutionConfig:
    hold_days: int = 5
    capital_per_trade: float = 100_000.0
    commission_rate: float = 0.00025
    minimum_commission: float = 5.0
    stamp_tax_rate: float = 0.0005
    slippage_bps: float = 5.0
    stop_loss_pct: float | None = None
    lot_size: int = 100
    asset_type: str = "equity"


@dataclass(frozen=True)
class Trade:
    symbol: str
    signal_date: int
    entry_date: int
    exit_date: int
    entry_price: float
    exit_price: float
    shares: int
    entry_commission: float
    exit_commission: float
    stamp_tax: float
    gross_return: float
    net_return: float
    exit_reason: str
    exit_delay_days: int


@dataclass(frozen=True)
class TimeSplit:
    train_start: int
    train_end: int
    validation_start: int
    validation_end: int
    test_start: int
    test_end: int

    def contains(self, partition: str, date: int) -> bool:
        if partition == "train":
            return self.train_start <= date <= self.train_end
        if partition == "validation":
            return self.validation_start <= date <= self.validation_end
        if partition == "test":
            return self.test_start <= date <= self.test_end
        raise ValueError(f"unknown partition: {partition}")


SignalBuilder = Callable[[list[Bar], dict[str, Any], str], list[bool]]


@dataclass(frozen=True)
class StrategySpec:
    skill: str
    asset_type: str
    fidelity: str
    baseline: dict[str, Any]
    parameter_grid: tuple[dict[str, Any], ...]
    signal_builder: SignalBuilder
    limitations: tuple[str, ...]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_zero(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("gb18030", errors="ignore").strip()


def load_names() -> dict[str, str]:
    names: dict[str, str] = {}
    for market, path in TNF_FILES.items():
        if not path.is_file():
            continue
        data = path.read_bytes()
        if len(data) < 50 or (len(data) - 50) % 360:
            continue
        for offset in range(50, len(data), 360):
            record = data[offset : offset + 360]
            code = decode_zero(record[:6])
            name = decode_zero(record[31:49])
            if len(code) == 6 and name:
                names[f"{code}.{market}"] = name
    return names


def symbol_from_path(path: Path, market: str) -> str:
    return f"{path.stem[2:]}.{market}"


def read_day_file(path: Path, start_date: int, end_date: int) -> list[Bar]:
    if not path.is_file() or path.stat().st_size % DAY_RECORD.size:
        return []
    rows: list[Bar] = []
    with path.open("rb") as handle:
        while raw := handle.read(DAY_RECORD.size):
            date_i, open_i, high_i, low_i, close_i, amount, volume, _unused = DAY_RECORD.unpack(raw)
            if date_i < start_date or date_i > end_date or close_i <= 0:
                continue
            rows.append(
                Bar(
                    date=int(date_i),
                    open=float(open_i) / 100.0,
                    high=float(high_i) / 100.0,
                    low=float(low_i) / 100.0,
                    close=float(close_i) / 100.0,
                    amount=float(amount),
                    volume=int(volume),
                )
            )
    return rows


def limit_ratio(symbol: str, asset_type: str = "equity") -> float:
    code, market = symbol.split(".", 1)
    if asset_type == "convertible_bond":
        return 0.20
    if market == "BJ":
        return 0.30
    if code.startswith(("300", "301", "688", "689")):
        return 0.20
    return 0.10


def is_suspended(bar: Bar) -> bool:
    return bar.volume <= 0 or bar.open <= 0 or bar.close <= 0


def is_one_price(bar: Bar) -> bool:
    return max(bar.open, bar.high, bar.low, bar.close) - min(bar.open, bar.high, bar.low, bar.close) < 1e-9


def is_limit_locked(bar: Bar, previous_close: float, ratio: float, direction: str) -> bool:
    if not is_one_price(bar) or previous_close <= 0:
        return False
    change = bar.close / previous_close - 1.0
    return change >= ratio * 0.98 if direction == "up" else change <= -ratio * 0.98


def execute_signals(
    symbol: str,
    bars: list[Bar],
    signals: list[bool],
    config: ExecutionConfig,
) -> list[Trade]:
    if len(bars) != len(signals):
        raise ValueError("bars and signals must have identical lengths")
    trades: list[Trade] = []
    next_free_index = 0
    ratio = limit_ratio(symbol, config.asset_type)
    slip = config.slippage_bps / 10_000.0
    for signal_index, active in enumerate(signals):
        if not active or signal_index < next_free_index or signal_index + 1 >= len(bars):
            continue
        entry_index = signal_index + 1
        entry_bar = bars[entry_index]
        if is_suspended(entry_bar) or is_limit_locked(entry_bar, bars[signal_index].close, ratio, "up"):
            continue
        entry_price = entry_bar.open * (1.0 + slip)
        lots = int(config.capital_per_trade / max(entry_bar.open * config.lot_size, 0.01))
        if lots <= 0:
            continue
        shares = lots * config.lot_size
        entry_value = shares * entry_price
        entry_commission = max(config.minimum_commission, entry_value * config.commission_rate)

        planned_exit = entry_index + max(1, config.hold_days)
        if planned_exit >= len(bars):
            continue
        exit_index = planned_exit
        exit_reason = "holding_period"
        if config.stop_loss_pct is not None:
            stop_price = entry_price * (1.0 - config.stop_loss_pct)
            for index in range(entry_index + 1, min(planned_exit, len(bars) - 1) + 1):
                current = bars[index]
                if current.low <= stop_price:
                    exit_index = index
                    exit_reason = "stop_loss"
                    break

        desired_exit_index = exit_index
        while exit_index < len(bars):
            current = bars[exit_index]
            previous = bars[exit_index - 1]
            if not is_suspended(current) and not is_limit_locked(current, previous.close, ratio, "down"):
                break
            exit_index += 1
        if exit_index >= len(bars):
            continue

        exit_bar = bars[exit_index]
        if exit_reason == "stop_loss":
            stop_price = entry_price * (1.0 - float(config.stop_loss_pct))
            raw_exit = min(exit_bar.open, stop_price) if exit_bar.open <= stop_price else stop_price
        else:
            raw_exit = exit_bar.open
        exit_price = raw_exit * (1.0 - slip)
        exit_value = shares * exit_price
        exit_commission = max(config.minimum_commission, exit_value * config.commission_rate)
        stamp_tax = 0.0 if config.asset_type == "convertible_bond" else exit_value * config.stamp_tax_rate
        gross_return = exit_price / entry_price - 1.0
        net_profit = exit_value - entry_value - entry_commission - exit_commission - stamp_tax
        net_return = net_profit / (entry_value + entry_commission)
        trades.append(
            Trade(
                symbol=symbol,
                signal_date=bars[signal_index].date,
                entry_date=entry_bar.date,
                exit_date=exit_bar.date,
                entry_price=entry_price,
                exit_price=exit_price,
                shares=shares,
                entry_commission=entry_commission,
                exit_commission=exit_commission,
                stamp_tax=stamp_tax,
                gross_return=gross_return,
                net_return=net_return,
                exit_reason=exit_reason,
                exit_delay_days=exit_index - desired_exit_index,
            )
        )
        next_free_index = exit_index + 1
    return trades


def chronological_split(
    dates: Iterable[int],
    train_ratio: float = 0.60,
    validation_ratio: float = 0.20,
) -> TimeSplit:
    ordered = sorted(set(dates))
    if len(ordered) < 15:
        raise ValueError("at least 15 distinct dates are required")
    train_count = max(1, min(len(ordered) - 2, int(len(ordered) * train_ratio)))
    validation_count = max(1, min(len(ordered) - train_count - 1, int(len(ordered) * validation_ratio)))
    return TimeSplit(
        train_start=ordered[0],
        train_end=ordered[train_count - 1],
        validation_start=ordered[train_count],
        validation_end=ordered[train_count + validation_count - 1],
        test_start=ordered[train_count + validation_count],
        test_end=ordered[-1],
    )


def ema(values: list[float], period: int) -> list[float]:
    if period <= 0:
        raise ValueError("EMA period must be positive")
    alpha = 2.0 / (period + 1.0)
    output: list[float] = []
    current = values[0] if values else 0.0
    for value in values:
        current = alpha * value + (1.0 - alpha) * current
        output.append(current)
    return output


def rolling_mean(values: list[float], period: int) -> list[float]:
    output = [math.nan] * len(values)
    total = 0.0
    for index, value in enumerate(values):
        total += value
        if index >= period:
            total -= values[index - period]
        if index >= period - 1:
            output[index] = total / period
    return output


def rolling_max(values: list[float], period: int) -> list[float]:
    return [math.nan if i < period - 1 else max(values[i - period + 1 : i + 1]) for i in range(len(values))]


def rolling_min(values: list[float], period: int) -> list[float]:
    return [math.nan if i < period - 1 else min(values[i - period + 1 : i + 1]) for i in range(len(values))]


def wave_position(bars: list[Bar], period: int) -> list[float]:
    highs = rolling_max([bar.high for bar in bars], period)
    lows = rolling_min([bar.low for bar in bars], period)
    output: list[float] = []
    for index, bar in enumerate(bars):
        spread = highs[index] - lows[index]
        output.append(50.0 if math.isnan(spread) or spread <= 0 else 100.0 * (bar.close - lows[index]) / spread)
    return output


def golden_signals(bars: list[Bar], params: dict[str, Any], _symbol: str) -> list[bool]:
    closes = [bar.close for bar in bars]
    fast = ema(closes, int(params["fast"]))
    slow = ema(closes, int(params["slow"]))
    return [index > 0 and fast[index - 1] <= slow[index - 1] and fast[index] > slow[index] for index in range(len(bars))]


def feilong_proxy_signals(bars: list[Bar], params: dict[str, Any], _symbol: str) -> list[bool]:
    closes = [bar.close for bar in bars]
    fast = ema(closes, int(params["fast"]))
    slow = ema(closes, int(params["slow"]))
    wave = wave_position(bars, int(params["wave_period"]))
    return [
        index > 0
        and wave[index] < float(params["wave_threshold"])
        and fast[index] >= slow[index]
        and closes[index] > closes[index - 1]
        for index in range(len(bars))
    ]


def bottom_fishing_signals(bars: list[Bar], params: dict[str, Any], _symbol: str) -> list[bool]:
    closes = [bar.close for bar in bars]
    lows = [bar.low for bar in bars]
    wave = wave_position(bars, int(params["wave_period"]))
    ma5 = rolling_mean(closes, 5)
    return [
        index >= 6
        and wave[index - 1] < float(params["wave_threshold"])
        and closes[index] > closes[index - 1]
        and lows[index - 1] <= min(lows[index - 5 : index])
        and not math.isnan(ma5[index])
        and closes[index] >= ma5[index]
        for index in range(len(bars))
    ]


def limit_up_signals(bars: list[Bar], params: dict[str, Any], symbol: str) -> list[bool]:
    consecutive = int(params["boards"])
    ratio = limit_ratio(symbol)
    locked = [False]
    for index in range(1, len(bars)):
        change = bars[index].close / bars[index - 1].close - 1.0
        locked.append(change >= ratio * 0.98 and abs(bars[index].high - bars[index].close) < 1e-9)
    return [
        index >= consecutive and all(locked[index - consecutive + 1 : index + 1])
        for index in range(len(bars))
    ]


def convertible_bond_signals(bars: list[Bar], params: dict[str, Any], _symbol: str) -> list[bool]:
    closes = [bar.close for bar in bars]
    amounts = [bar.amount for bar in bars]
    ma5 = rolling_mean(closes, 5)
    ma20 = rolling_mean(closes, 20)
    amount5 = rolling_mean(amounts, 5)
    high20 = rolling_max([bar.high for bar in bars], 20)
    low20 = rolling_min([bar.low for bar in bars], 20)
    signals = [False] * len(bars)
    for index in range(21, len(bars)):
        returns = [closes[i] / closes[i - 1] - 1.0 for i in range(index - 9, index + 1)]
        volatility = statistics.pstdev(returns)
        score = 0
        score += 10 if closes[index] > ma20[index] else 0
        score += 10 if ma5[index] > ma20[index] else 0
        score += 10 if closes[index] > closes[index - 5] else 0
        score += 10 if closes[index] > closes[index - 20] else 0
        score += 10 if amounts[index] > amount5[index] * float(params["volume_ratio"]) else 0
        score += 10 if amount5[index] >= float(params["min_amount"]) else 0
        score += 10 if volatility <= float(params["max_volatility"]) else 0
        score += 10 if closes[index] / high20[index] >= 0.90 else 0
        score += 10 if closes[index] / low20[index] >= 1.05 else 0
        score += 10 if bars[index].close > bars[index].open else 0
        signals[index] = score >= int(params["score_threshold"])
    return signals


def quality_track_signals(bars: list[Bar], params: dict[str, Any], _symbol: str) -> list[bool]:
    closes = [bar.close for bar in bars]
    amounts = [bar.amount for bar in bars]
    ma20 = rolling_mean(closes, 20)
    ma60 = rolling_mean(closes, 60)
    amount5 = rolling_mean(amounts, 5)
    high20 = rolling_max([bar.high for bar in bars], 20)
    signals = [False] * len(bars)
    for index in range(60, len(bars)):
        trend = closes[index] > ma20[index] > ma60[index] and ma20[index] > ma20[index - 5]
        momentum = float(params["min_momentum"]) <= closes[index] / closes[index - 20] - 1.0 <= float(params["max_momentum"])
        volume = amounts[index] >= amount5[index] * float(params["volume_ratio"])
        near_high = closes[index] / high20[index] >= float(params["near_high"])
        signals[index] = trend and momentum and volume and near_high
    return signals


def strategy_specs() -> tuple[StrategySpec, ...]:
    return (
        StrategySpec(
            "golden-ignition",
            "equity",
            "EXACT_PRICE_RULE",
            {"fast": 3, "slow": 21, "hold_days": 5, "stop_loss_pct": 0.08},
            (
                {"fast": 3, "slow": 18, "hold_days": 5, "stop_loss_pct": 0.08},
                {"fast": 3, "slow": 21, "hold_days": 5, "stop_loss_pct": 0.08},
                {"fast": 5, "slow": 21, "hold_days": 8, "stop_loss_pct": 0.08},
                {"fast": 5, "slow": 34, "hold_days": 8, "stop_loss_pct": 0.10},
            ),
            golden_signals,
            (),
        ),
        StrategySpec(
            "feilong-strategy",
            "equity",
            "HISTORICAL_PRICE_PROXY",
            {"fast": 3, "slow": 8, "wave_period": 21, "wave_threshold": 25, "hold_days": 5, "stop_loss_pct": 0.08},
            tuple(
                {"fast": fast, "slow": slow, "wave_period": 21, "wave_threshold": threshold, "hold_days": hold, "stop_loss_pct": 0.08}
                for fast, slow, threshold, hold in ((3, 8, 20, 5), (3, 8, 25, 5), (3, 13, 30, 8), (5, 13, 35, 8))
            ),
            feilong_proxy_signals,
            ("OUTPUT3/4/5/6 historical series are not available in batch form; the test uses an explicitly labelled price proxy.",),
        ),
        StrategySpec(
            "a-share-bottom-fishing",
            "equity",
            "HISTORICAL_PRICE_PROXY",
            {"wave_period": 21, "wave_threshold": 20, "hold_days": 8, "stop_loss_pct": 0.08},
            tuple(
                {"wave_period": period, "wave_threshold": threshold, "hold_days": hold, "stop_loss_pct": stop}
                for period, threshold, hold, stop in ((13, 15, 5, 0.06), (21, 20, 8, 0.08), (21, 25, 10, 0.08), (34, 25, 10, 0.10))
            ),
            bottom_fishing_signals,
            (
                "The structural buy point is reconstructed from OHLCV only.",
                "Historical ST, delisting-risk and bank classifications are unavailable; current-name exclusions are used and disclosed.",
            ),
        ),
        StrategySpec(
            "a-share-limit-up-mining",
            "equity",
            "EXACT_PRICE_RULE_WITH_LIMITATIONS",
            {"boards": 2, "hold_days": 3, "stop_loss_pct": 0.08},
            (
                {"boards": 2, "hold_days": 2, "stop_loss_pct": 0.06},
                {"boards": 2, "hold_days": 3, "stop_loss_pct": 0.08},
                {"boards": 2, "hold_days": 5, "stop_loss_pct": 0.10},
                {"boards": 3, "hold_days": 3, "stop_loss_pct": 0.08},
            ),
            limit_up_signals,
            ("Historical auction order-book accessibility and board-opening details are unavailable in daily bars.",),
        ),
        StrategySpec(
            "convertible-bond-screening-strategy",
            "convertible_bond",
            "POINT_IN_TIME_PRICE_PROXY",
            {"score_threshold": 60, "volume_ratio": 1.0, "min_amount": 50_000_000, "max_volatility": 0.04, "hold_days": 5, "stop_loss_pct": 0.06},
            (
                {"score_threshold": 50, "volume_ratio": 0.9, "min_amount": 30_000_000, "max_volatility": 0.05, "hold_days": 3, "stop_loss_pct": 0.05},
                {"score_threshold": 60, "volume_ratio": 1.0, "min_amount": 50_000_000, "max_volatility": 0.04, "hold_days": 5, "stop_loss_pct": 0.06},
                {"score_threshold": 70, "volume_ratio": 1.1, "min_amount": 80_000_000, "max_volatility": 0.035, "hold_days": 5, "stop_loss_pct": 0.06},
                {"score_threshold": 70, "volume_ratio": 1.2, "min_amount": 100_000_000, "max_volatility": 0.03, "hold_days": 8, "stop_loss_pct": 0.08},
            ),
            convertible_bond_signals,
            (
                "Historical forced-redemption announcement snapshots are unavailable and are not fabricated.",
                "The current convertible-bond universe introduces survivorship bias.",
            ),
        ),
        StrategySpec(
            "quality-track-stock-selection",
            "equity",
            "POINT_IN_TIME_PRICE_PROXY",
            {"min_momentum": 0.0, "max_momentum": 0.30, "volume_ratio": 1.0, "near_high": 0.92, "hold_days": 5, "stop_loss_pct": 0.08},
            (
                {"min_momentum": 0.0, "max_momentum": 0.20, "volume_ratio": 0.9, "near_high": 0.90, "hold_days": 5, "stop_loss_pct": 0.08},
                {"min_momentum": 0.0, "max_momentum": 0.30, "volume_ratio": 1.0, "near_high": 0.92, "hold_days": 5, "stop_loss_pct": 0.08},
                {"min_momentum": 0.02, "max_momentum": 0.35, "volume_ratio": 1.1, "near_high": 0.95, "hold_days": 8, "stop_loss_pct": 0.08},
                {"min_momentum": 0.05, "max_momentum": 0.40, "volume_ratio": 1.2, "near_high": 0.97, "hold_days": 10, "stop_loss_pct": 0.10},
            ),
            quality_track_signals,
            ("Current concept membership is not a historical constituent snapshot and introduces survivorship bias.",),
        ),
    )


def universe_candidates(asset_type: str) -> list[tuple[str, Path]]:
    prefixes = BOND_PREFIXES if asset_type == "convertible_bond" else EQUITY_PREFIXES
    candidates: list[tuple[str, Path]] = []
    for market, directory in DAY_DIRS.items():
        if not directory.is_dir():
            continue
        for path in directory.glob(f"{market.lower()}*.day"):
            code = path.stem[2:]
            if len(code) == 6 and code.startswith(prefixes):
                candidates.append((f"{code}.{market}", path))
    return candidates


def load_universe(
    asset_type: str,
    start_date: int,
    end_date: int,
    max_symbols: int,
    names: dict[str, str],
) -> dict[str, list[Bar]]:
    warmup_start = max(19900101, start_date - 20000)
    ranked: list[tuple[float, str, list[Bar]]] = []
    for symbol, path in universe_candidates(asset_type):
        name = names.get(symbol, "")
        if asset_type == "equity":
            upper = name.upper()
            if not name or "ST" in upper or "退" in name:
                continue
        rows = read_day_file(path, warmup_start, end_date)
        in_range = [row for row in rows if row.date >= start_date]
        if len(in_range) < 120:
            continue
        recent_amounts = [row.amount for row in in_range[-20:] if row.amount > 0]
        liquidity = statistics.fmean(recent_amounts) if recent_amounts else 0.0
        ranked.append((liquidity, symbol, rows))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return {symbol: rows for _liquidity, symbol, rows in ranked[:max_symbols]}


def execution_config(params: dict[str, Any], asset_type: str) -> ExecutionConfig:
    return ExecutionConfig(
        hold_days=int(params["hold_days"]),
        stop_loss_pct=float(params["stop_loss_pct"]) if params.get("stop_loss_pct") is not None else None,
        asset_type=asset_type,
        lot_size=10 if asset_type == "convertible_bond" else 100,
    )


def backtest_parameter_set(
    spec: StrategySpec,
    params: dict[str, Any],
    universe: dict[str, list[Bar]],
) -> list[Trade]:
    trades: list[Trade] = []
    config = execution_config(params, spec.asset_type)
    for symbol, bars in universe.items():
        signals = spec.signal_builder(bars, params, symbol)
        trades.extend(execute_signals(symbol, bars, signals, config))
    return sorted(trades, key=lambda trade: (trade.exit_date, trade.symbol, trade.entry_date))


def partition_trades(trades: list[Trade], split: TimeSplit, partition: str) -> list[Trade]:
    return [
        trade
        for trade in trades
        if split.contains(partition, trade.signal_date)
        and split.contains(partition, trade.entry_date)
        and split.contains(partition, trade.exit_date)
    ]


def metrics(trades: list[Trade]) -> dict[str, Any]:
    if not trades:
        return {
            "trade_count": 0,
            "win_rate": None,
            "average_net_return": None,
            "median_net_return": None,
            "compounded_trade_return": None,
            "max_trade_sequence_drawdown": None,
            "profit_factor": None,
            "objective": -1_000_000.0,
        }
    returns = [trade.net_return for trade in trades]
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in returns:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - 1.0)
    gains = sum(value for value in returns if value > 0)
    losses = -sum(value for value in returns if value < 0)
    average = statistics.fmean(returns)
    objective = average * math.sqrt(len(returns)) + max_drawdown * 0.15
    return {
        "trade_count": len(trades),
        "win_rate": sum(value > 0 for value in returns) / len(returns),
        "average_net_return": average,
        "median_net_return": statistics.median(returns),
        "compounded_trade_return": equity - 1.0,
        "max_trade_sequence_drawdown": max_drawdown,
        "profit_factor": gains / losses if losses > 0 else None,
        "objective": objective,
    }


def compact_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: params[key] for key in sorted(params)}


def build_deployment_decision(result: dict[str, Any]) -> dict[str, Any]:
    improved = result["test_comparison"]["out_of_sample_improved"] is True
    active_parameters = (
        result["optimized_parameters"]
        if improved
        else result["baseline_parameters"]
    )
    return {
        "mode": "PAPER_DEBUG_ONLY" if improved else "BASELINE_RETAINED",
        "active_parameters": compact_params(dict(active_parameters)),
        "production_skill_modified": False,
        "automatic_order": False,
        "reason": (
            "测试集目标值严格改善，仅在 stock-unified 纸面调试层启用优化参数；正式业务技能合同保持不变。"
            if improved
            else "测试集目标值未严格改善，纸面调试维持基线参数；正式业务技能合同保持不变。"
        ),
    }


def validate_deployment_decisions(results: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    mode_counts = {"PAPER_DEBUG_ONLY": 0, "BASELINE_RETAINED": 0}
    seen_skills: set[str] = set()
    validated_count = 0

    for result in results:
        skill = str(result.get("skill", "<unknown>"))
        if skill in seen_skills:
            errors.append(f"{skill}: duplicate strategy result")
        seen_skills.add(skill)
        if result.get("status") != "PASS":
            errors.append(f"{skill}: strategy status is not PASS")
            continue
        decision = result.get("deployment_decision")
        if not isinstance(decision, dict):
            errors.append(f"{skill}: deployment_decision is missing")
            continue

        improved = result["test_comparison"]["out_of_sample_improved"] is True
        expected_mode = "PAPER_DEBUG_ONLY" if improved else "BASELINE_RETAINED"
        expected_parameters = (
            result["optimized_parameters"]
            if improved
            else result["baseline_parameters"]
        )
        actual_mode = decision.get("mode")
        if actual_mode != expected_mode:
            errors.append(f"{skill}: mode must be {expected_mode}, got {actual_mode}")
        elif actual_mode in mode_counts:
            mode_counts[actual_mode] += 1
        if decision.get("active_parameters") != compact_params(dict(expected_parameters)):
            errors.append(f"{skill}: active_parameters do not match {expected_mode}")
        if decision.get("production_skill_modified") is not False:
            errors.append(f"{skill}: production_skill_modified must be false")
        if decision.get("automatic_order") is not False:
            errors.append(f"{skill}: automatic_order must be false")
        validated_count += 1

    expected_skills = set(EXPECTED_STRATEGY_SKILLS)
    missing_skills = sorted(expected_skills - seen_skills)
    unexpected_skills = sorted(seen_skills - expected_skills)
    if missing_skills:
        errors.append(f"missing strategies: {', '.join(missing_skills)}")
    if unexpected_skills:
        errors.append(f"unexpected strategies: {', '.join(unexpected_skills)}")
    expected_counts = {"PAPER_DEBUG_ONLY": 3, "BASELINE_RETAINED": 3}
    if mode_counts != expected_counts:
        errors.append(f"deployment split must be 3/3, got {mode_counts}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "expected_strategy_count": len(EXPECTED_STRATEGY_SKILLS),
        "validated_strategy_count": validated_count,
        "mode_counts": mode_counts,
        "production_skill_modified_count": sum(
            result.get("deployment_decision", {}).get("production_skill_modified") is True
            for result in results
        ),
        "automatic_order_enabled_count": sum(
            result.get("deployment_decision", {}).get("automatic_order") is True
            for result in results
        ),
        "errors": errors,
    }


def optimize_strategy(
    spec: StrategySpec,
    universe: dict[str, list[Bar]],
    split: TimeSplit,
) -> dict[str, Any]:
    cache: dict[str, list[Trade]] = {}

    def cached(params: dict[str, Any]) -> list[Trade]:
        key = json.dumps(compact_params(params), ensure_ascii=False, sort_keys=True)
        if key not in cache:
            cache[key] = backtest_parameter_set(spec, params, universe)
        return cache[key]

    train_rows: list[dict[str, Any]] = []
    for params in spec.parameter_grid:
        train_metrics = metrics(partition_trades(cached(params), split, "train"))
        train_rows.append({"parameters": compact_params(params), "metrics": train_metrics})
    train_rows.sort(key=lambda row: (row["metrics"]["objective"], row["metrics"]["trade_count"]), reverse=True)
    candidate_count = max(1, math.ceil(len(train_rows) / 2))
    train_candidates = train_rows[:candidate_count]

    validation_rows: list[dict[str, Any]] = []
    for candidate in train_candidates:
        params = candidate["parameters"]
        validation_metrics = metrics(partition_trades(cached(params), split, "validation"))
        validation_rows.append(
            {
                "parameters": params,
                "train_metrics": candidate["metrics"],
                "validation_metrics": validation_metrics,
            }
        )
    validation_rows.sort(
        key=lambda row: (row["validation_metrics"]["objective"], row["validation_metrics"]["trade_count"]),
        reverse=True,
    )
    selected = validation_rows[0]
    optimized_params = selected["parameters"]

    baseline_trades = cached(spec.baseline)
    optimized_trades = cached(optimized_params)
    baseline_test = metrics(partition_trades(baseline_trades, split, "test"))
    optimized_test = metrics(partition_trades(optimized_trades, split, "test"))
    return {
        "skill": spec.skill,
        "asset_type": spec.asset_type,
        "fidelity": spec.fidelity,
        "universe_size": len(universe),
        "baseline_parameters": compact_params(spec.baseline),
        "optimized_parameters": optimized_params,
        "selection_protocol": {
            "parameter_grid_size": len(spec.parameter_grid),
            "train_candidates_forwarded": candidate_count,
            "rule": "Rank bounded grid on train, select among top half on validation, read test once after selection.",
        },
        "selected_train_metrics": selected["train_metrics"],
        "selected_validation_metrics": selected["validation_metrics"],
        "test_comparison": {
            "baseline": baseline_test,
            "optimized": optimized_test,
            "average_net_return_delta": (
                None
                if baseline_test["average_net_return"] is None or optimized_test["average_net_return"] is None
                else optimized_test["average_net_return"] - baseline_test["average_net_return"]
            ),
            "objective_delta": optimized_test["objective"] - baseline_test["objective"],
            "out_of_sample_improved": optimized_test["objective"] > baseline_test["objective"],
        },
        "full_period_reference": {
            "baseline": metrics(baseline_trades),
            "optimized": metrics(optimized_trades),
        },
        "limitations": list(spec.limitations),
    }


def format_pct(value: Any) -> str:
    return "N/A" if value is None else f"{float(value) * 100:.2f}%"


def markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# 股票策略统一回测与有边界优化报告",
        "",
        f"- 状态：`{payload['status']}`",
        f"- 纸面调试验证：`{payload['paper_debug_validation']['status']}`",
        f"- 数据截止日：`{payload['data']['end_date']}`",
        f"- 股票样本：`{payload['data']['equity_universe_size']}`",
        f"- 可转债样本：`{payload['data']['convertible_bond_universe_size']}`",
        f"- 时间切分：训练 `{payload['time_split']['train_start']}-{payload['time_split']['train_end']}`，"
        f"验证 `{payload['time_split']['validation_start']}-{payload['time_split']['validation_end']}`，"
        f"测试 `{payload['time_split']['test_start']}-{payload['time_split']['test_end']}`",
        "",
        "## 测试集优化前后",
        "",
        "| 技能 | 复现等级 | 基线交易数 | 优化交易数 | 基线平均净收益 | 优化平均净收益 | 目标值变化 | 测试集改善 | 纸面调试决策 |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for result in payload["strategies"]:
        comparison = result["test_comparison"]
        baseline = comparison["baseline"]
        optimized = comparison["optimized"]
        deployment = result["deployment_decision"]
        lines.append(
            f"| `{result['skill']}` | `{result['fidelity']}` | {baseline['trade_count']} | "
            f"{optimized['trade_count']} | {format_pct(baseline['average_net_return'])} | "
            f"{format_pct(optimized['average_net_return'])} | {comparison['objective_delta']:.6f} | "
            f"{'是' if comparison['out_of_sample_improved'] else '否'} | `{deployment['mode']}` |"
        )
    lines.extend(
        [
            "",
            "## 纸面调试部署",
            "",
            f"- 启用优化参数：`{payload['paper_debug_validation']['mode_counts']['PAPER_DEBUG_ONLY']}` 套。",
            f"- 保留基线参数：`{payload['paper_debug_validation']['mode_counts']['BASELINE_RETAINED']}` 套。",
            f"- 修改正式业务技能：`{payload['paper_debug_validation']['production_skill_modified_count']}` 套。",
            f"- 启用自动下单：`{payload['paper_debug_validation']['automatic_order_enabled_count']}` 套。",
            "- 优化参数仅作为 `stock-unified` 纸面调试活动参数，不写回正式业务技能固定核心定义。",
            "",
            "## 执行模型",
            "",
            "- 信号只允许在下一实际交易日开盘成交，禁止同日成交。",
            "- 停牌或一字涨停拒绝买入；计划卖出日停牌或一字跌停时顺延到首个可卖交易日。",
            "- 股票佣金 0.025%，单边最低 5 元；卖出印花税 0.05%；默认双边滑点 5bp。",
            "- 可转债按 10 张一手建模，不收股票卖出印花税；其他费用参数保持可配置。",
            "- 同一证券持仓期间不叠加新仓，止损最早从买入后的下一交易日生效。",
            "",
            "## 优化约束",
            "",
            "- 参数候选是代码内固定的小型网格，不做无限搜索。",
            "- 训练集只用于候选排序，验证集决定最终参数，测试集在参数确定后才读取。",
            "- 测试集未改善的策略如实保留，不用测试结果反向调参。",
            "",
            "## 重要边界",
            "",
            "- 本报告是历史研究和决策支持，不构成收益承诺或自动交易指令。",
            "- 多证券交易按退出日期顺序形成“交易序列复利”和回撤，不等同于资金容量受限的组合净值。",
            "- 当前证券名称、当前股票/转债存续池和当前概念成员会引入幸存者偏差。",
            "- `HISTORICAL_PRICE_PROXY` 和 `POINT_IN_TIME_PRICE_PROXY` 均为明确标注的代理回测，不是对专有历史输出或缺失历史快照的伪造。",
            "",
            "## 策略明细",
            "",
        ]
    )
    for result in payload["strategies"]:
        lines.extend(
            [
                f"### {result['skill']}",
                "",
                f"- 基线参数：`{json.dumps(result['baseline_parameters'], ensure_ascii=False, sort_keys=True)}`",
                f"- 优化参数：`{json.dumps(result['optimized_parameters'], ensure_ascii=False, sort_keys=True)}`",
                f"- 纸面调试模式：`{result['deployment_decision']['mode']}`",
                f"- 活动参数：`{json.dumps(result['deployment_decision']['active_parameters'], ensure_ascii=False, sort_keys=True)}`",
                f"- 决策说明：{result['deployment_decision']['reason']}",
                f"- 训练交易数：`{result['selected_train_metrics']['trade_count']}`",
                f"- 验证交易数：`{result['selected_validation_metrics']['trade_count']}`",
            ]
        )
        for limitation in result["limitations"]:
            lines.append(f"- 限制：{limitation}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def run(
    output_json: Path,
    output_markdown: Path,
    start_date: int,
    end_date: int,
    max_equities: int,
    max_bonds: int,
) -> dict[str, Any]:
    names = load_names()
    equities = load_universe("equity", start_date, end_date, max_equities, names)
    bonds = load_universe("convertible_bond", start_date, end_date, max_bonds, names)
    if not equities:
        raise RuntimeError(f"no eligible equity history was loaded from {TDX_ROOT}")
    all_dates = sorted({bar.date for bars in equities.values() for bar in bars if start_date <= bar.date <= end_date})
    split = chronological_split(all_dates)
    results = []
    for spec in strategy_specs():
        universe = bonds if spec.asset_type == "convertible_bond" else equities
        if not universe:
            results.append(
                {
                    "skill": spec.skill,
                    "asset_type": spec.asset_type,
                    "fidelity": spec.fidelity,
                    "status": "NO_LOCAL_UNIVERSE",
                    "limitations": [*spec.limitations, "No eligible local history was available."],
                }
            )
            continue
        result = optimize_strategy(spec, universe, split)
        result["status"] = "PASS"
        result["deployment_decision"] = build_deployment_decision(result)
        results.append(result)
    failed = [item["skill"] for item in results if item.get("status") != "PASS"]
    paper_debug_validation = validate_deployment_decisions(results)
    payload = {
        "schema": "STOCK_STRATEGY_BACKTEST_V2",
        "status": "PASS" if not failed and paper_debug_validation["status"] == "PASS" else "FAIL",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "data": {
            "source": f"{TDX_ROOT} local daily bars",
            "start_date": start_date,
            "end_date": end_date,
            "equity_universe_size": len(equities),
            "convertible_bond_universe_size": len(bonds),
            "selection": "Current-name eligible securities ranked by recent 20-day local turnover.",
            "failed_strategies": failed,
        },
        "time_split": asdict(split),
        "execution_assumptions": asdict(ExecutionConfig()),
        "strategies": results,
        "paper_debug_validation": paper_debug_validation,
        "risk_boundary": (
            "Historical research and decision support only; paper-debug parameters do not modify production skills, "
            "automatic ordering is disabled, and no return is guaranteed."
        ),
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    output_markdown.write_text(markdown_report(payload), encoding="utf-8")
    payload["artifacts"] = {
        "json": {"path": str(output_json.resolve()), "sha256": file_sha256(output_json), "size": output_json.stat().st_size},
        "markdown": {"path": str(output_markdown.resolve()), "sha256": file_sha256(output_markdown), "size": output_markdown.stat().st_size},
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified A-share and convertible-bond backtest")
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    parser.add_argument("--start-date", type=int, default=20210101)
    parser.add_argument("--end-date", type=int, default=20260731)
    parser.add_argument("--max-equities", type=int, default=180)
    parser.add_argument("--max-bonds", type=int, default=120)
    args = parser.parse_args()
    result = run(
        args.output_json,
        args.output_markdown,
        args.start_date,
        args.end_date,
        args.max_equities,
        args.max_bonds,
    )
    print(json.dumps({"status": result["status"], "data": result["data"], "artifacts": result["artifacts"]}, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
