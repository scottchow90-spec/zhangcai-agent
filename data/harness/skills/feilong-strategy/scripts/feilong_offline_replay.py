#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import math
import struct
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DAY_RECORD = struct.Struct("<IIIIIfII")
PRICE_COLUMNS = ("open", "high", "low", "close")


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_date(value: Any) -> str:
    digits = "".join(character for character in str(value) if character.isdigit())
    if len(digits) < 8:
        raise ValueError(f"invalid date: {value}")
    result = digits[:8]
    datetime.strptime(result, "%Y%m%d")
    return result


def day_path_for_symbol(tdx_root: Path, symbol: str) -> Path:
    code, _, market = symbol.upper().partition(".")
    if len(code) != 6 or market not in {"SH", "SZ", "BJ"}:
        raise ValueError(f"invalid stock symbol: {symbol}")
    return tdx_root / "vipdoc" / market.lower() / "lday" / f"{market.lower()}{code}.day"


def cw_path_for_symbol(tdx_root: Path, symbol: str) -> Path:
    code, _, market = symbol.upper().partition(".")
    if len(code) != 6 or market not in {"SH", "SZ", "BJ"}:
        raise ValueError(f"invalid stock symbol: {symbol}")
    return tdx_root / "vipdoc" / "cw" / f"gp{market.lower()}{code}.dat"


def read_tdx_day(path: Path) -> pd.DataFrame:
    content = path.read_bytes()
    if not content or len(content) % DAY_RECORD.size:
        raise RuntimeError(f"invalid Tongdaxin daily file: {path}")
    rows = [
        {
            "date": normalize_date(date),
            "open": open_ / 100.0,
            "high": high / 100.0,
            "low": low / 100.0,
            "close": close / 100.0,
            "amount": float(amount),
            "volume": float(volume),
        }
        for date, open_, high, low, close, amount, volume, _reserved
        in DAY_RECORD.iter_unpack(content)
    ]
    frame = pd.DataFrame(rows).set_index("date").sort_index(kind="mergesort")
    if frame.index.has_duplicates:
        raise RuntimeError(f"duplicate Tongdaxin daily dates: {path}")
    return frame


def read_base_finance(path: Path) -> dict[str, dict[str, Any]]:
    content = path.read_bytes()
    if len(content) < 32:
        raise RuntimeError(f"invalid DBF file: {path}")
    record_count = struct.unpack_from("<I", content, 4)[0]
    header_length = struct.unpack_from("<H", content, 8)[0]
    record_length = struct.unpack_from("<H", content, 10)[0]
    fields: list[tuple[str, str, int, int]] = []
    offset = 32
    position = 1
    while offset + 32 <= header_length and content[offset] != 0x0D:
        descriptor = content[offset : offset + 32]
        name = descriptor[:11].split(b"\0", 1)[0].decode("ascii", errors="strict")
        field_type = chr(descriptor[11])
        length = int(descriptor[16])
        fields.append((name, field_type, length, position))
        position += length
        offset += 32
    wanted = {"GPDM", "LTAG", "SSDATE", "GXRQ"}
    selected = [field for field in fields if field[0] in wanted]
    if {field[0] for field in selected} != wanted:
        raise RuntimeError("base.dbf required fields are missing")
    result: dict[str, dict[str, Any]] = {}
    for index in range(record_count):
        start = header_length + index * record_length
        record = content[start : start + record_length]
        if len(record) != record_length or record[:1] == b"*":
            continue
        row: dict[str, Any] = {}
        for name, field_type, length, field_offset in selected:
            raw = record[field_offset : field_offset + length].strip()
            text = raw.decode("ascii", errors="ignore").strip()
            if field_type in {"N", "F"}:
                row[name] = float(text) if text else 0.0
            else:
                row[name] = text
        code = str(row.get("GPDM", ""))
        if len(code) == 6 and code.isdigit():
            result[code] = row
    return result


def read_gbbq(path: Path, reader_path: Path) -> pd.DataFrame:
    if not path.is_file() or not reader_path.is_file():
        raise RuntimeError("Tongdaxin gbbq data or its vendored reader is missing")
    spec = importlib.util.spec_from_file_location("feilong_gbbq_reader", reader_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load vendored gbbq reader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    raw = module.GbbqReader().get_df(str(path))
    actions = raw.loc[pd.to_numeric(raw["category"]).eq(1)].copy()
    actions["symbol"] = (
        actions["code"].astype(str).str.zfill(6)
        + pd.to_numeric(actions["market"]).map({0: ".SZ", 1: ".SH", 2: ".BJ"})
    )
    actions["date"] = actions["datetime"].map(normalize_date)
    return actions.rename(
        columns={
            "hongli_panqianliutong": "cash_dividend_per_10",
            "peigujia_qianzongguben": "rights_price",
            "songgu_qianzongguben": "bonus_shares_per_10",
            "peigu_houzongguben": "rights_shares_per_10",
        }
    )[
        [
            "symbol",
            "date",
            "cash_dividend_per_10",
            "rights_price",
            "bonus_shares_per_10",
            "rights_shares_per_10",
        ]
    ].sort_values(["symbol", "date"], kind="mergesort")


def front_adjust_like_tq(raw_bars: pd.DataFrame, actions: pd.DataFrame) -> pd.DataFrame:
    bars = raw_bars.copy()
    if bars.empty or actions.empty:
        return bars
    dates = bars.index.to_numpy(dtype=str)
    multipliers = np.ones(len(bars), dtype=float)
    for action in actions.to_dict("records"):
        date = str(action["date"])
        position = int(np.searchsorted(dates, date, side="left"))
        if position <= 0 or position >= len(bars) or dates[position] != date:
            continue
        previous_close = float(bars.iloc[position - 1]["close"])
        cash_per_share = float(action["cash_dividend_per_10"]) / 10.0
        share_bonus_ratio = float(action["bonus_shares_per_10"]) / 10.0
        allotment_ratio = float(action["rights_shares_per_10"]) / 10.0
        denominator = 1.0 + share_bonus_ratio + allotment_ratio
        if previous_close <= 0 or denominator <= 0:
            raise RuntimeError(f"invalid corporate action for {date}")
        rights_price = float(action["rights_price"])
        theoretical_price = (
            previous_close
            - cash_per_share
            + allotment_ratio * rights_price
        ) / denominator
        ratio = theoretical_price / previous_close
        if not math.isfinite(ratio) or ratio <= 0:
            raise RuntimeError(f"invalid forward adjustment ratio for {date}")
        multipliers[:position] *= ratio
    bars.loc[:, PRICE_COLUMNS] = (
        bars.loc[:, PRICE_COLUMNS].to_numpy(dtype=float) * multipliers[:, None]
    )
    return bars


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def sma_tdx(series: pd.Series, period: int, weight: int = 1) -> pd.Series:
    values: list[float] = []
    previous = math.nan
    for raw in series.to_numpy(dtype=float):
        if not math.isfinite(raw):
            values.append(previous)
            continue
        previous = raw if not math.isfinite(previous) else (
            weight * raw + (period - weight) * previous
        ) / period
        values.append(previous)
    return pd.Series(values, index=series.index, dtype=float)


def filter_tdx(condition: pd.Series, bars: int) -> pd.Series:
    result: list[bool] = []
    remaining = 0
    for value in condition.fillna(False).astype(bool):
        if remaining == 0 and value:
            result.append(True)
            remaining = bars
        else:
            result.append(False)
            if remaining > 0:
                remaining -= 1
    return pd.Series(result, index=condition.index, dtype=bool)


def barslast(condition: pd.Series) -> pd.Series:
    values: list[float] = []
    last_true: int | None = None
    for index, value in enumerate(condition.fillna(False).astype(bool)):
        if value:
            last_true = index
        values.append(math.nan if last_true is None else float(index - last_true))
    return pd.Series(values, index=condition.index, dtype=float)


def dynamic_ref(series: pd.Series, offsets: pd.Series) -> pd.Series:
    source = series.to_numpy(dtype=float)
    result = np.full(len(series), np.nan, dtype=float)
    for index, raw_offset in enumerate(offsets.to_numpy(dtype=float)):
        if math.isfinite(raw_offset):
            source_index = index - int(raw_offset)
            if source_index >= 0:
                result[index] = source[source_index]
    return pd.Series(result, index=series.index, dtype=float)


def forcast_tdx(series: pd.Series, period: int) -> pd.Series:
    source = series.to_numpy(dtype=float)
    result = np.full(len(source), np.nan, dtype=float)
    x = np.arange(period, dtype=float)
    x_mean = float(x.mean())
    denominator = float(np.square(x - x_mean).sum())
    for index in range(period - 1, len(source)):
        window = source[index - period + 1 : index + 1]
        if not np.isfinite(window).all():
            continue
        y_mean = float(window.mean())
        slope = float(((x - x_mean) * (window - y_mean)).sum() / denominator)
        result[index] = y_mean + slope * ((period - 1) - x_mean)
    return pd.Series(result, index=series.index, dtype=float)


def evaluate_installed_formula(
    bars: pd.DataFrame,
    *,
    active_capital_10k_shares: float | None,
    listing_date: str,
    code: str,
    name: str = "",
) -> pd.DataFrame:
    close = bars["close"].astype(float)
    high = bars["high"].astype(float)
    low = bars["low"].astype(float)
    open_ = bars["open"].astype(float)
    volume_shares = bars["volume"].astype(float)
    previous_close = close.shift(1)

    high_ema_8 = ema(high, 8)
    close_ema_8 = ema(close, 8)
    weak = ((high_ema_8 < high_ema_8.shift(1)) | ((close_ema_8 < close_ema_8.shift(1)) & (close < close_ema_8))).astype(int)
    rise = (close - previous_close).clip(lower=0)
    absolute_change = (close - previous_close).abs()
    rsi_2 = sma_tdx(rise, 2, 1) / sma_tdx(absolute_change, 2, 1) * 100.0
    dif = ema(close, 12) - ema(close, 26)
    cross_45_down = (rsi_2 < 45) & (rsi_2.shift(1) > 45) & dif.ne(0)
    cross_20_down = (rsi_2 < 20) & (rsi_2.shift(1) > 20)
    pct_change = (close - previous_close) / previous_close
    longtou = (
        (weak.eq(1).rolling(4, min_periods=1).sum().eq(3))
        & weak.eq(0)
        & open_.lt(close)
        & pct_change.gt(0.089)
    ) | (
        pct_change.gt(0.089)
        & (cross_20_down.shift(1).fillna(False) | cross_45_down.shift(1).fillna(False))
    )

    ema_89 = ema(close, 89)
    high_ema_13 = ema(ema(ema(high, 13), 13), 13)
    high_ema_5 = ema(ema(ema(high, 5), 5), 5)
    pct_100 = pct_change * 100.0
    listing = datetime.strptime(normalize_date(listing_date), "%Y%m%d")
    listed_over_120 = pd.Series(
        [
            (datetime.strptime(str(date), "%Y%m%d") - listing).days > 120
            for date in bars.index
        ],
        index=bars.index,
        dtype=bool,
    )
    name_filter = not ("ST" in name.upper())
    code_filter = not code.startswith("3")
    price_filter = close.shift(1).lt(89) & close.shift(1).gt(2)
    trend_filter = close.gt(high_ema_5) & close.gt(high_ema_13) & close.gt(ema_89)
    first_limit_up = pct_100.ge(9.84) & pct_100.shift(1).lt(9.84) & pct_100.shift(2).lt(9.84)
    x27 = (
        listed_over_120
        & name_filter
        & price_filter
        & code_filter
        & trend_filter
        & (high / high_ema_5).lt(1.16)
        & first_limit_up
    )

    body_high = pd.concat([close, open_], axis=1).max(axis=1)
    body_low = pd.concat([close, open_], axis=1).min(axis=1)
    overlap_low = body_high.rolling(4, min_periods=1).min()
    overlap_high = body_low.rolling(4, min_periods=1).max()
    overlap = pd.Series(True, index=bars.index)
    for offset in range(4):
        overlap &= (
            body_high.shift(offset).ge(overlap_low)
            & body_low.shift(offset).le(overlap_low)
            & body_high.shift(offset).ge(overlap_high)
            & body_low.shift(offset).le(overlap_high)
        )
    overlap_exists = overlap.rolling(36, min_periods=1).max().fillna(False).astype(bool)

    middle_five_ago = (open_.shift(5) + close.shift(5)) / 2.0
    average_price = (high + low + close + open_) / 4.0
    x40 = pd.concat([middle_five_ago, average_price, high.rolling(5, min_periods=1).max()], axis=1).max(axis=1)
    x41 = pd.concat([middle_five_ago, average_price, low.rolling(5, min_periods=1).min()], axis=1).min(axis=1)
    x43 = x40.eq(middle_five_ago)
    unique_limit_up_base = pct_100.gt(9.85) & open_.ne(close)
    unique_limit_up = unique_limit_up_base.rolling(21, min_periods=1).sum().eq(1) & unique_limit_up_base
    x48 = dynamic_ref(overlap_high, barslast(overlap))
    x49 = dynamic_ref(x40, barslast(x43))
    x52 = (x41 / x49).lt(1.3) & (x41 / x48).lt(1.3) & unique_limit_up_base
    x55 = x27 & x52 & overlap_exists
    waveband_password = filter_tdx(x55, 13) & unique_limit_up

    volume_lots = volume_shares / 100.0
    forecast_4 = forcast_tdx(volume_lots, 4)
    forecast_12 = forcast_tdx(volume_lots, 12)
    private_base = (
        (close / previous_close).gt(1.048)
        & close.eq(high)
        & forecast_4.ge(0.2 * forecast_12)
        & forecast_4.le(2.1 * forecast_12)
    )
    private_entry = filter_tdx(private_base, 28)
    xs2 = waveband_password | longtou
    if active_capital_10k_shares is None:
        return pd.DataFrame(
            {
                "longtou": longtou.fillna(False).astype(bool),
                "waveband_password": waveband_password.fillna(False).astype(bool),
                "private_entry": private_entry.fillna(False).astype(bool),
                "xs2": xs2.fillna(False).astype(bool),
            },
            index=bars.index,
        )

    capital_lots = float(active_capital_10k_shares) * 100.0
    if capital_lots <= 0:
        raise RuntimeError(f"invalid active capital for {code}")
    volume_ratio = volume_lots / capital_lots
    volume_ma_ratio = volume_lots.rolling(2, min_periods=1).mean() / volume_lots.rolling(10, min_periods=1).mean()
    x10 = 0.0068 * pct_100 - 0.0072 * volume_ma_ratio - 0.5676 * volume_ratio - 0.0105
    x11 = 0.0015 * pct_100 - 0.0124 * volume_ma_ratio + 1.7461 * volume_ratio - 0.0074
    rapid_rise = (0.0 - 12.2401 * x10 - x11 + 0.321).lt(0)
    xs1 = private_entry | rapid_rise
    return pd.DataFrame(
        {
            "longtou": longtou.fillna(False).astype(bool),
            "waveband_password": waveband_password.fillna(False).astype(bool),
            "rapid_rise": rapid_rise.fillna(False).astype(bool),
            "private_entry": private_entry.fillna(False).astype(bool),
            "xs1": xs1.fillna(False).astype(bool),
            "xs2": xs2.fillna(False).astype(bool),
            "signal": (xs1 & xs2).fillna(False).astype(bool),
        },
        index=bars.index,
    )


def resolve_missing_finance_candidates(
    capital_independent: pd.DataFrame,
    *,
    candidate_dates: list[str],
    symbol: str,
) -> tuple[list[str], list[dict[str, Any]]]:
    required = {"xs2", "private_entry"}
    if not required.issubset(capital_independent.columns):
        missing = sorted(required - set(capital_independent.columns))
        raise RuntimeError(f"capital-independent formula columns are missing: {missing}")
    signal_dates: list[str] = []
    proofs: list[dict[str, Any]] = []
    for candidate_date in sorted({normalize_date(value) for value in candidate_dates}):
        if candidate_date not in capital_independent.index:
            raise RuntimeError(f"candidate date is missing from local daily data: {symbol} {candidate_date}")
        row = capital_independent.loc[candidate_date]
        xs2 = bool(row["xs2"])
        private_entry = bool(row["private_entry"])
        if not xs2:
            signal = False
            reason = "xs2_false"
        elif private_entry:
            signal = True
            reason = "private_entry_true"
            signal_dates.append(candidate_date)
        else:
            raise RuntimeError(f"active capital is required: {symbol} {candidate_date}")
        proofs.append(
            {
                "candidate_date": candidate_date,
                "xs2": xs2,
                "private_entry": private_entry,
                "signal": signal,
                "reason": reason,
            }
        )
    return signal_dates, proofs


def replay_installed_formula_signals(
    symbols: list[str],
    start_date: str,
    end_date: str,
    *,
    tdx_root: Path = Path(r"C:\new_tdx_mock"),
    vendor_reader: Path | None = None,
    names: dict[str, str] | None = None,
    candidate_dates: dict[str, list[str]] | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    start = normalize_date(start_date)
    end = normalize_date(end_date)
    if start > end:
        raise ValueError("start date is later than end date")
    base_path = tdx_root / "T0002" / "hq_cache" / "base.dbf"
    gbbq_path = tdx_root / "T0002" / "hq_cache" / "gbbq"
    reader_path = vendor_reader or (
        Path(__file__).resolve().parents[1]
        / "vendor"
        / "pytdx-1.72"
        / "pytdx"
        / "reader"
        / "gbbq_reader.py"
    )
    finance = read_base_finance(base_path)
    actions = read_gbbq(gbbq_path, reader_path)
    action_groups = {
        symbol: group.drop(columns=["symbol"]).copy()
        for symbol, group in actions.groupby("symbol", sort=False)
    }
    signals: list[dict[str, str]] = []
    day_sources: list[dict[str, Any]] = []
    missing_finance_resolutions: list[dict[str, Any]] = []
    for symbol in sorted(set(value.upper() for value in symbols)):
        code = symbol.split(".", 1)[0]
        row = finance.get(code)
        day_path = day_path_for_symbol(tdx_root, symbol)
        bars = read_tdx_day(day_path)
        adjusted = front_adjust_like_tq(
            bars,
            action_groups.get(symbol, pd.DataFrame()),
        )
        day_source = {
            "symbol": symbol,
            "path": str(day_path.resolve()),
            "size": day_path.stat().st_size,
            "sha256": sha256_path(day_path),
        }
        if row is None:
            dates = (candidate_dates or {}).get(symbol, [])
            if not dates:
                raise RuntimeError(f"base.dbf stock is missing without candidate dates: {symbol}")
            normalized_candidates = sorted(
                {
                    normalize_date(value)
                    for value in dates
                    if start <= normalize_date(value) <= end
                }
            )
            if not normalized_candidates:
                raise RuntimeError(f"base.dbf stock has no in-range candidate dates: {symbol}")
            first_local_date = normalize_date(adjusted.index[0])
            first_local_day = datetime.strptime(first_local_date, "%Y%m%d")
            for candidate_date in normalized_candidates:
                candidate_day = datetime.strptime(candidate_date, "%Y%m%d")
                if (candidate_day - first_local_day).days <= 120:
                    raise RuntimeError(
                        f"listing age cannot be proven from local daily data: {symbol} {candidate_date}"
                    )
            capital_independent = evaluate_installed_formula(
                adjusted,
                active_capital_10k_shares=None,
                listing_date=first_local_date,
                code=code,
                name=(names or {}).get(code, ""),
            )
            resolved_dates, proofs = resolve_missing_finance_candidates(
                capital_independent,
                candidate_dates=normalized_candidates,
                symbol=symbol,
            )
            signals.extend(
                {"symbol": symbol, "signal_date": signal_date}
                for signal_date in resolved_dates
            )
            cw_path = cw_path_for_symbol(tdx_root, symbol)
            if not cw_path.is_file():
                raise RuntimeError(f"local Tongdaxin cw file is missing: {symbol}")
            missing_finance_resolutions.append(
                {
                    "symbol": symbol,
                    "resolution": "candidate-date-capital-dependency-short-circuit",
                    "listing_date_upper_bound": first_local_date,
                    "candidate_proofs": proofs,
                    "day_source": day_source,
                    "cw_source": {
                        "path": str(cw_path.resolve()),
                        "size": cw_path.stat().st_size,
                        "sha256": sha256_path(cw_path),
                    },
                }
            )
            day_sources.append(day_source)
            continue
        evaluated = evaluate_installed_formula(
            adjusted,
            active_capital_10k_shares=float(row["LTAG"]),
            listing_date=str(row["SSDATE"]),
            code=code,
            name=(names or {}).get(code, ""),
        )
        selected = evaluated.loc[
            evaluated.index.to_series().between(start, end) & evaluated["signal"]
        ]
        signals.extend(
            {"symbol": symbol, "signal_date": str(date)} for date in selected.index
        )
        day_sources.append(day_source)
    return sorted(signals, key=lambda row: (row["symbol"], row["signal_date"])), {
        "mode": "offline-installed-formula-replay",
        "start_date": start,
        "end_date": end,
        "symbol_count": len(set(symbols)),
        "signal_count": len(signals),
        "base_dbf": {"path": str(base_path), "sha256": sha256_path(base_path)},
        "gbbq": {"path": str(gbbq_path), "sha256": sha256_path(gbbq_path)},
        "gbbq_reader": {"path": str(reader_path), "sha256": sha256_path(reader_path)},
        "day_sources": day_sources,
        "missing_finance_resolutions": missing_finance_resolutions,
    }


def match_first_board_cycles(
    cycles: pd.DataFrame, signals: list[dict[str, str]]
) -> pd.DataFrame:
    required = {"code", "first_board_date"}
    if not required.issubset(cycles.columns):
        raise ValueError(f"cycles missing columns: {sorted(required - set(cycles.columns))}")
    source = cycles.copy()
    source["code"] = source["code"].astype(str).str.zfill(6)
    source["first_board_date"] = source["first_board_date"].map(normalize_date)
    signal_frame = pd.DataFrame(signals, columns=["symbol", "signal_date"])
    if signal_frame.empty:
        result = source.iloc[0:0].copy()
        result["signal_date"] = pd.Series(dtype="object")
        return result
    signal_frame["code"] = signal_frame["symbol"].str.slice(0, 6)
    signal_frame["signal_date"] = signal_frame["signal_date"].map(normalize_date)
    result = source.merge(
        signal_frame,
        left_on=["code", "first_board_date"],
        right_on=["code", "signal_date"],
        how="inner",
        validate="many_to_one",
    )
    return result.sort_values(["first_board_date", "code"], kind="mergesort").reset_index(drop=True)
