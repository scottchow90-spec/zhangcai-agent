"""Fail-closed point-in-time universe and forward-label construction."""

from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import json
import math
import re
from datetime import date
from pathlib import Path
from typing import Any, Sequence

import pandas as pd


class DataCapabilityBlocked(RuntimeError):
    """Raised when required historical data capability cannot be proven."""


_CAPABILITY_KEYS = (
    "historical_st_status_available",
    "delisted_symbols_included",
    "suspension_history_available",
    "limit_state_reconstructable",
    "listing_age_reconstructable",
    "liquidity_history_available",
    "point_in_time_universe_available",
    "tradability_constraints_complete",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(
            path,
            dtype={
                "date": "string",
                "listing_date": "string",
                "delisting_date": "string",
            },
        )
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if suffix in {".jsonl", ".ndjson"}:
        return pd.read_json(path, lines=True)
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return pd.DataFrame(payload)
        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            return pd.DataFrame(payload["records"])
        raise ValueError("JSON must be a record list or contain a records list")
    raise ValueError(f"unsupported table format: {suffix or '<none>'}")


def _truth_value(value: object) -> bool | None:
    if value is None or value is pd.NA:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value == 1:
        return True
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value == 0:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    return None


def _has_true_evidence(frame: pd.DataFrame, names: Sequence[str]) -> bool:
    for name in names:
        if _truth_value(frame.attrs.get(name)) is True:
            return True
        if name in frame.columns and not frame.empty:
            values = [_truth_value(value) for value in frame[name].tolist()]
            if values and all(value is True for value in values):
                return True
    return False


def _has_columns(frame: pd.DataFrame | None, columns: set[str]) -> bool:
    return frame is not None and not frame.empty and columns <= set(frame.columns)


def _audit_symbol_date_keys(frame: pd.DataFrame | None) -> set[tuple[str, str]] | None:
    if not _has_columns(frame, {"symbol", "date"}):
        return None
    assert frame is not None
    try:
        keys = [
            (
                _normalize_symbol(symbol),
                _validate_iso_date(day, field="audit.date"),
            )
            for symbol, day in zip(frame["symbol"], frame["date"], strict=True)
        ]
    except (TypeError, ValueError):
        return None
    return set(keys) if len(keys) == len(set(keys)) else None


def _audit_strict_bool_column(frame: pd.DataFrame | None, column: str) -> bool:
    if frame is None or frame.empty or column not in frame.columns:
        return False
    return all(type(value) is bool for value in frame[column].tolist())


def _audit_finite_nonnegative_column(
    frame: pd.DataFrame | None,
    column: str,
    *,
    integer: bool = False,
) -> bool:
    if frame is None or frame.empty or column not in frame.columns:
        return False
    try:
        values = pd.to_numeric(frame[column], errors="raise").astype(float)
    except (TypeError, ValueError):
        return False
    if values.isna().any():
        return False
    numbers = values.tolist()
    if any(not math.isfinite(value) or value < 0 for value in numbers):
        return False
    return not integer or all(value.is_integer() for value in numbers)


def _audit_date_column(
    frame: pd.DataFrame | None,
    column: str,
    *,
    nullable: bool,
) -> bool:
    if frame is None or frame.empty or column not in frame.columns:
        return False
    try:
        for value in frame[column].tolist():
            if nullable and (value is None or pd.isna(value)):
                continue
            _validate_iso_date(value, field=f"audit.{column}")
    except (TypeError, ValueError):
        return False
    return True


def _audit_unique_symbols(frame: pd.DataFrame | None) -> bool:
    if not _has_columns(frame, {"symbol"}):
        return False
    assert frame is not None
    try:
        symbols = [_normalize_symbol(value) for value in frame["symbol"].tolist()]
    except ValueError:
        return False
    return len(symbols) == len(set(symbols))


def _audit_delisted_evidence_matches(
    master: pd.DataFrame | None,
    delisted: pd.DataFrame | None,
) -> bool:
    required = {"symbol", "listing_date", "delisting_date"}
    if not _has_columns(master, required) or not _has_columns(delisted, required):
        return False
    assert master is not None and delisted is not None
    try:
        master_rows: dict[str, list[tuple[str, str | None]]] = {}
        for record in master[list(required)].to_dict("records"):
            symbol = _normalize_symbol(record["symbol"])
            listing_date = _validate_iso_date(
                record["listing_date"], field="audit.master.listing_date"
            )
            raw_delisting_date = record["delisting_date"]
            delisting_date = (
                None
                if raw_delisting_date is None or pd.isna(raw_delisting_date)
                else _validate_iso_date(
                    raw_delisting_date, field="audit.master.delisting_date"
                )
            )
            master_rows.setdefault(symbol, []).append((listing_date, delisting_date))

        delisted_rows: dict[str, tuple[str, str]] = {}
        for record in delisted[list(required)].to_dict("records"):
            symbol = _normalize_symbol(record["symbol"])
            if symbol in delisted_rows:
                return False
            delisted_rows[symbol] = (
                _validate_iso_date(
                    record["listing_date"], field="audit.delisted.listing_date"
                ),
                _validate_iso_date(
                    record["delisting_date"], field="audit.delisted.delisting_date"
                ),
            )

        master_delisted_symbols = {
            symbol
            for symbol, history in master_rows.items()
            if any(delisting is not None for _, delisting in history)
        }
        if set(delisted_rows) != master_delisted_symbols:
            return False
        for symbol, (expected_listing, expected_delisting) in delisted_rows.items():
            history = master_rows.get(symbol)
            if not history:
                return False
            listing_dates = {listing for listing, _ in history}
            nonempty_delisting_dates = {
                delisting for _, delisting in history if delisting is not None
            }
            if listing_dates != {expected_listing}:
                return False
            if nonempty_delisting_dates != {expected_delisting}:
                return False
    except (TypeError, ValueError):
        return False
    return True


def audit_point_in_time_capabilities(
    *,
    stock_master_path: Path,
    st_history_path: Path | None,
    suspension_history_path: Path | None,
    delisted_master_path: Path | None,
) -> dict[str, Any]:
    """Audit source files without upgrading incomplete data into historical proof."""

    supplied = {
        "stock_master": stock_master_path,
        "st_history": st_history_path,
        "suspension_history": suspension_history_path,
        "delisted_master": delisted_master_path,
    }
    source_paths: dict[str, str | None] = {}
    source_sha256: dict[str, str | None] = {}
    frames: dict[str, pd.DataFrame | None] = {name: None for name in supplied}
    errors: list[str] = []

    for name, raw_path in supplied.items():
        if raw_path is None:
            source_paths[name] = None
            source_sha256[name] = None
            continue
        if not isinstance(raw_path, Path):
            source_paths[name] = None
            source_sha256[name] = None
            errors.append(f"{name}_path_must_be_path")
            continue
        path = raw_path.resolve()
        source_paths[name] = str(path)
        if not path.is_file():
            source_sha256[name] = None
            errors.append(f"{name}_file_missing")
            continue
        source_sha256[name] = _sha256(path)
        if path.stat().st_size == 0:
            errors.append(f"{name}_file_empty")
            continue
        try:
            frame = _read_table(path)
        except Exception as exc:  # The audit must remain structured on bad input.
            errors.append(f"{name}_unreadable:{type(exc).__name__}")
            continue
        if frame.empty:
            errors.append(f"{name}_table_empty")
            continue
        frames[name] = frame

    master = frames["stock_master"]
    st_history = frames["st_history"]
    suspension = frames["suspension_history"]
    delisted = frames["delisted_master"]

    master_keys = _audit_symbol_date_keys(master)
    st_keys = _audit_symbol_date_keys(st_history)
    suspension_keys = _audit_symbol_date_keys(suspension)
    point_in_time = master_keys is not None and _has_true_evidence(
        master,
        ("point_in_time_universe_available", "historical_point_in_time"),
    )
    historical_st = (
        master_keys is not None
        and st_keys is not None
        and master_keys <= st_keys
        and _audit_strict_bool_column(st_history, "is_st")
        and (
        _has_true_evidence(
            st_history,
            ("historical_st_status_available", "historical_point_in_time"),
        )
        )
    )
    suspension_history = (
        master_keys is not None
        and suspension_keys is not None
        and master_keys <= suspension_keys
        and _audit_strict_bool_column(suspension, "is_suspended")
        and _has_true_evidence(
            suspension,
            ("suspension_history_available", "historical_point_in_time"),
        )
    )
    master_claims_delisted = _has_columns(
        master, {"symbol", "listing_date", "delisting_date"}
    ) and _audit_date_column(
        master, "listing_date", nullable=False
    ) and _audit_date_column(
        master, "delisting_date", nullable=True
    ) and _has_true_evidence(
        master,
        ("delisted_symbols_included",),
    )
    separate_delisted_history = _has_columns(
        delisted, {"symbol", "listing_date", "delisting_date"}
    ) and _audit_unique_symbols(
        delisted
    ) and _audit_date_column(
        delisted, "listing_date", nullable=False
    ) and _audit_date_column(
        delisted, "delisting_date", nullable=False
    ) and _has_true_evidence(delisted, ("historical_point_in_time",))
    delisted_included = bool(
        master_claims_delisted
        and separate_delisted_history
        and _audit_delisted_evidence_matches(master, delisted)
    )
    limit_reconstructable = bool(
        master_keys is not None
        and _audit_strict_bool_column(master, "is_limit_locked")
    )
    listing_age = bool(
        master_keys is not None
        and _audit_date_column(master, "listing_date", nullable=False)
        and _audit_finite_nonnegative_column(
            master, "listing_trading_days", integer=True
        )
    )
    liquidity = bool(
        master_keys is not None
        and _audit_finite_nonnegative_column(master, "amount")
        and _audit_finite_nonnegative_column(
            master, "trailing_20d_median_turnover_cny"
        )
    )
    tradability_complete = all(
        (
            historical_st,
            delisted_included,
            suspension_history,
            limit_reconstructable,
            listing_age,
            liquidity,
            point_in_time,
        )
    )

    capabilities = {
        "historical_st_status_available": bool(historical_st),
        "delisted_symbols_included": bool(delisted_included),
        "suspension_history_available": bool(suspension_history),
        "limit_state_reconstructable": bool(limit_reconstructable),
        "listing_age_reconstructable": bool(listing_age),
        "liquidity_history_available": bool(liquidity),
        "point_in_time_universe_available": bool(point_in_time),
        "tradability_constraints_complete": bool(tradability_complete),
    }
    capability_errors = {
        "historical_st_status_available": "historical_st_status_missing",
        "delisted_symbols_included": "delisted_history_missing_survivorship_risk",
        "suspension_history_available": "suspension_history_missing",
        "limit_state_reconstructable": "limit_state_reconstruction_missing",
        "listing_age_reconstructable": "listing_age_reconstruction_missing",
        "liquidity_history_available": "liquidity_history_missing",
        "point_in_time_universe_available": "point_in_time_universe_missing",
        "tradability_constraints_complete": "tradability_constraints_incomplete",
    }
    for key in _CAPABILITY_KEYS:
        if not capabilities[key] and capability_errors[key] not in errors:
            errors.append(capability_errors[key])

    return {
        **capabilities,
        "status": "PASS" if tradability_complete else "BLOCKED",
        "errors": errors,
        "source_paths": source_paths,
        "source_sha256": source_sha256,
    }


_DATE8 = re.compile(r"\d{8}\Z")
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_SYMBOL_SUFFIX = re.compile(r"^(\d{6})\.(SH|SZ|BJ)$")
_SYMBOL_PREFIX = re.compile(r"^(SH|SZ|BJ)(\d{6})$")
_SH_CODE_PREFIXES = frozenset(("600", "601", "603", "605", "688", "689"))
_SZ_CODE_PREFIXES = frozenset(("000", "001", "002", "003", "300", "301"))
_BJ_CODE_PREFIXES = frozenset(("43", "83", "87", "88", "92"))


def _validate_iso_date(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f"{field} must be an unambiguous YYYYMMDD or YYYY-MM-DD string"
        )
    if _DATE8.fullmatch(value) is None and _ISO_DATE.fullmatch(value) is None:
        raise ValueError(
            f"{field} must be an unambiguous YYYYMMDD or YYYY-MM-DD string"
        )
    try:
        if _DATE8.fullmatch(value) is not None:
            parsed = date(int(value[:4]), int(value[4:6]), int(value[6:8]))
        else:
            parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} is not a valid calendar date: {value}") from exc
    return parsed.strftime("%Y%m%d")


def _validate_date_sequence(values: Sequence[str], *, field: str) -> list[str]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{field} must be a sequence, not a scalar or unordered container")
    normalized = [_validate_iso_date(value, field=field) for value in values]
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field} contains duplicate dates")
    return normalized


def _normalize_symbol(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("symbol must be a string")
    compact = value.strip().upper()
    suffix_match = _SYMBOL_SUFFIX.fullmatch(compact)
    if suffix_match:
        code = suffix_match.group(1)
        return f"{code}.{_market_for_code(code)}"
    prefix_match = _SYMBOL_PREFIX.fullmatch(compact)
    if prefix_match:
        code = prefix_match.group(2)
        return f"{code}.{_market_for_code(code)}"
    if re.fullmatch(r"\d{6}", compact):
        return f"{compact}.{_market_for_code(compact)}"
    raise ValueError(f"invalid A-share symbol: {value!r}")


def _market_for_code(code: str) -> str:
    if code[:2] in _BJ_CODE_PREFIXES:
        return "BJ"
    if code[:3] in _SH_CODE_PREFIXES:
        return "SH"
    if code[:3] in _SZ_CODE_PREFIXES:
        return "SZ"
    raise ValueError(f"unsupported A-share code: {code}")


def _require_dataframe(value: object, *, name: str, allow_empty: bool = False) -> pd.DataFrame:
    if not isinstance(value, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame")
    if value.empty and not allow_empty:
        raise DataCapabilityBlocked(f"{name} is empty; historical capability cannot be proven")
    return value.copy(deep=True)


def _require_columns(frame: pd.DataFrame, columns: set[str], *, name: str) -> None:
    missing = sorted(columns - set(frame.columns))
    if missing:
        raise DataCapabilityBlocked(f"{name} missing required columns: {', '.join(missing)}")


def _prepare_symbol_dates(frame: pd.DataFrame, *, name: str, date_column: str = "date") -> pd.DataFrame:
    prepared = frame.copy(deep=True)
    prepared["symbol"] = prepared["symbol"].map(_normalize_symbol)
    prepared[date_column] = [
        _validate_iso_date(value, field=f"{name}.{date_column}")
        for value in prepared[date_column].tolist()
    ]
    if prepared.duplicated(["symbol", date_column]).any():
        raise ValueError(f"{name} contains normalized duplicate symbol/date pairs")
    return prepared


def _require_true_evidence(
    frame: pd.DataFrame,
    aliases: Sequence[str],
    *,
    message: str,
) -> None:
    if not _has_true_evidence(frame, aliases):
        raise DataCapabilityBlocked(message)


def _strict_boolean_series(frame: pd.DataFrame, column: str, *, name: str) -> pd.Series:
    values = [_truth_value(value) for value in frame[column].tolist()]
    if any(value is None for value in values):
        raise ValueError(f"{name}.{column} must contain explicit booleans without missing values")
    return pd.Series(values, index=frame.index, dtype=bool)


def _finite_numeric_series(
    frame: pd.DataFrame,
    column: str,
    *,
    name: str,
    nonnegative: bool = False,
) -> pd.Series:
    try:
        values = pd.to_numeric(frame[column], errors="raise").astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}.{column} must be numeric") from exc
    if values.isna().any() or not all(math.isfinite(value) for value in values.tolist()):
        raise ValueError(f"{name}.{column} must contain finite values")
    if nonnegative and (values < 0).any():
        raise ValueError(f"{name}.{column} must be nonnegative")
    return values


def _validate_thresholds(
    minimum_listing_days: int,
    minimum_median_turnover_cny: float,
) -> tuple[int, float]:
    if isinstance(minimum_listing_days, bool) or not isinstance(minimum_listing_days, int):
        raise TypeError("minimum_listing_days must be an integer")
    if minimum_listing_days < 1:
        raise ValueError("minimum_listing_days must be at least 1")
    if isinstance(minimum_median_turnover_cny, bool) or not isinstance(
        minimum_median_turnover_cny, (int, float)
    ):
        raise TypeError("minimum_median_turnover_cny must be numeric")
    turnover = float(minimum_median_turnover_cny)
    if not math.isfinite(turnover) or turnover < 0:
        raise ValueError("minimum_median_turnover_cny must be finite and nonnegative")
    return minimum_listing_days, turnover


def build_point_in_time_universe(
    *,
    signal_dates: Sequence[str],
    stock_master: pd.DataFrame,
    st_history: pd.DataFrame,
    suspension_history: pd.DataFrame,
    minimum_listing_days: int = 120,
    minimum_median_turnover_cny: float = 20_000_000.0,
) -> pd.DataFrame:
    """Build an auditable historical universe without current-list substitution."""

    dates = _validate_date_sequence(signal_dates, field="signal_dates")
    minimum_days, minimum_turnover = _validate_thresholds(
        minimum_listing_days,
        minimum_median_turnover_cny,
    )
    master = _require_dataframe(stock_master, name="stock_master")
    st = _require_dataframe(st_history, name="st_history")
    suspension = _require_dataframe(suspension_history, name="suspension_history")

    if "listing_trading_days" not in master.columns:
        raise DataCapabilityBlocked(
            "stock_master lacks mechanical trading-day listing age evidence"
        )
    if "trailing_20d_median_turnover_cny" not in master.columns:
        raise DataCapabilityBlocked(
            "stock_master lacks close-available trailing-20-day median turnover evidence"
        )
    _require_columns(
        master,
        {
            "symbol",
            "date",
            "listing_date",
            "delisting_date",
            "listing_trading_days",
            "trailing_20d_median_turnover_cny",
        },
        name="stock_master",
    )
    _require_true_evidence(
        master,
        ("point_in_time_universe_available", "historical_point_in_time"),
        message="stock_master lacks explicit historical point-in-time universe evidence",
    )
    _require_true_evidence(
        master,
        ("delisted_symbols_included",),
        message="stock_master lacks delisted history; full-A claim has survivorship risk",
    )
    _require_columns(st, {"symbol", "date", "is_st"}, name="st_history")
    _require_true_evidence(
        st,
        ("historical_st_status_available", "historical_point_in_time"),
        message="historical ST status evidence is missing",
    )
    _require_columns(
        suspension,
        {"symbol", "date", "is_suspended"},
        name="suspension_history",
    )
    _require_true_evidence(
        suspension,
        ("suspension_history_available", "historical_point_in_time"),
        message="historical suspension history evidence is missing",
    )

    master = _prepare_symbol_dates(master, name="stock_master")
    st = _prepare_symbol_dates(st, name="st_history")
    suspension = _prepare_symbol_dates(suspension, name="suspension_history")
    master["listing_date"] = [
        _validate_iso_date(value, field="stock_master.listing_date")
        for value in master["listing_date"].tolist()
    ]
    delisting_dates: list[str | None] = []
    for value in master["delisting_date"].tolist():
        if value is None or (isinstance(value, float) and math.isnan(value)) or pd.isna(value):
            delisting_dates.append(None)
        else:
            delisting_dates.append(
                _validate_iso_date(value, field="stock_master.delisting_date")
            )
    master["delisting_date"] = delisting_dates
    listing_days = _finite_numeric_series(
        master,
        "listing_trading_days",
        name="stock_master",
        nonnegative=True,
    )
    if any(not value.is_integer() for value in listing_days.tolist()):
        raise ValueError("stock_master.listing_trading_days must contain whole trading days")
    master["listing_trading_days"] = listing_days.astype(int)
    master["trailing_20d_median_turnover_cny"] = _finite_numeric_series(
        master,
        "trailing_20d_median_turnover_cny",
        name="stock_master",
        nonnegative=True,
    )
    st["is_st"] = _strict_boolean_series(st, "is_st", name="st_history")
    suspension["is_suspended"] = _strict_boolean_series(
        suspension,
        "is_suspended",
        name="suspension_history",
    )

    requested_master = master[master["date"].isin(dates)].copy()
    missing_dates = sorted(set(dates) - set(requested_master["date"]))
    if missing_dates:
        raise DataCapabilityBlocked(
            "stock_master request coverage missing for dates: " + ", ".join(missing_dates)
        )
    requested_pairs = set(zip(requested_master["symbol"], requested_master["date"], strict=False))
    for status_frame, name in ((st, "st_history"), (suspension, "suspension_history")):
        available_pairs = set(zip(status_frame["symbol"], status_frame["date"], strict=False))
        missing_pairs = requested_pairs - available_pairs
        if missing_pairs:
            sample = sorted(f"{symbol}@{day}" for symbol, day in missing_pairs)[:5]
            raise DataCapabilityBlocked(
                f"{name} request coverage missing: {', '.join(sample)}"
            )

    merged = requested_master.merge(
        st[["symbol", "date", "is_st"]],
        on=["symbol", "date"],
        how="left",
        validate="one_to_one",
    ).merge(
        suspension[["symbol", "date", "is_suspended"]],
        on=["symbol", "date"],
        how="left",
        validate="one_to_one",
    )
    rows: list[dict[str, Any]] = []
    for record in merged.to_dict("records"):
        signal_date = record["date"]
        raw_delisting_date = record["delisting_date"]
        delisting_date = (
            None if raw_delisting_date is None or pd.isna(raw_delisting_date) else raw_delisting_date
        )
        reason = "eligible"
        if bool(record["is_st"]):
            reason = "historical_st"
        elif bool(record["is_suspended"]):
            reason = "suspended"
        elif record["listing_date"] > signal_date:
            reason = "not_yet_listed"
        elif delisting_date is not None and signal_date > delisting_date:
            reason = "delisted"
        elif int(record["listing_trading_days"]) < minimum_days:
            reason = "insufficient_listing_age"
        elif float(record["trailing_20d_median_turnover_cny"]) < minimum_turnover:
            reason = "insufficient_liquidity"
        rows.append(
            {
                "symbol": record["symbol"],
                "signal_date": signal_date,
                "listing_date": record["listing_date"],
                "delisting_date": delisting_date,
                "listing_trading_days": int(record["listing_trading_days"]),
                "trailing_20d_median_turnover_cny": float(
                    record["trailing_20d_median_turnover_cny"]
                ),
                "is_st": bool(record["is_st"]),
                "is_suspended": bool(record["is_suspended"]),
                "eligible": reason == "eligible",
                "exclusion_reason": reason,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["signal_date", "symbol"], kind="mergesort"
    ).reset_index(drop=True)


def _validate_horizons_and_cost(
    horizons: tuple[int, int], cost_bps: float
) -> tuple[tuple[int, int], float]:
    if not isinstance(horizons, tuple) or len(horizons) != 2:
        raise TypeError("horizons must be a two-item tuple")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in horizons):
        raise TypeError("horizons must contain integers")
    if any(value < 1 for value in horizons):
        raise ValueError("horizons must be positive")
    if horizons[0] >= horizons[1]:
        raise ValueError("horizons must be unique and strictly increasing")
    if isinstance(cost_bps, bool) or not isinstance(cost_bps, (int, float)):
        raise TypeError("cost_bps must be numeric")
    cost = float(cost_bps)
    if not math.isfinite(cost) or not 0 <= cost <= 10_000:
        raise ValueError("cost_bps must be finite and between 0 and 10000")
    return horizons, cost


def _numeric_allow_missing(
    frame: pd.DataFrame,
    column: str,
    *,
    name: str,
    nonnegative: bool = False,
    allow_non_finite: bool = False,
) -> pd.Series:
    try:
        values = pd.to_numeric(frame[column], errors="raise").astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}.{column} must be numeric") from exc
    present = values.dropna()
    if not allow_non_finite and not all(
        math.isfinite(value) for value in present.tolist()
    ):
        raise ValueError(f"{name}.{column} must contain finite values when present")
    finite_present = present[present.map(math.isfinite)]
    if nonnegative and (finite_present < 0).any():
        raise ValueError(f"{name}.{column} must be nonnegative")
    return values


def _forward_adjustment_proven(frame: pd.DataFrame) -> bool:
    attr_value = frame.attrs.get("price_adjustment")
    if isinstance(attr_value, str) and attr_value.strip().lower() in {
        "qfq",
        "forward_adjusted",
        "前复权",
    }:
        return True
    for column in ("adjustment", "adjustment_mode", "price_adjustment"):
        if column not in frame.columns or frame.empty:
            continue
        values = frame[column].tolist()
        if all(
            isinstance(value, str)
            and value.strip().lower() in {"qfq", "forward_adjusted", "前复权"}
            for value in values
        ):
            return True
    if "is_forward_adjusted" in frame.columns:
        values = [_truth_value(value) for value in frame["is_forward_adjusted"].tolist()]
        return bool(values) and all(value is True for value in values)
    return False


def _limit_lock_series(frame: pd.DataFrame) -> pd.Series:
    for column in ("is_limit_locked", "locked_limit"):
        if column in frame.columns:
            return _strict_boolean_series(frame, column, name="bars")
    for column in ("limit_state", "limit_status"):
        if column not in frame.columns:
            continue
        unlocked = {"none", "not_locked", "unlocked", "normal"}
        locked = {
            "limit_up_locked",
            "limit_down_locked",
            "up_locked",
            "down_locked",
            "locked_up",
            "locked_down",
        }
        result: list[bool] = []
        for value in frame[column].tolist():
            if not isinstance(value, str):
                raise ValueError(f"bars.{column} must contain explicit limit-lock states")
            normalized = value.strip().lower()
            if normalized in unlocked:
                result.append(False)
            elif normalized in locked:
                result.append(True)
            else:
                raise ValueError(f"bars.{column} has unknown limit-lock state: {value!r}")
        return pd.Series(result, index=frame.index, dtype=bool)
    raise DataCapabilityBlocked(
        "bars lack explicit daily limit-lock evidence; limit state cannot be guessed"
    )


def build_forward_labels(
    *,
    bars: pd.DataFrame,
    universe: pd.DataFrame,
    horizons: tuple[int, int] = (5, 10),
    cost_bps: float = 30.0,
) -> pd.DataFrame:
    """Construct next-open, forward-adjusted, benchmark-relative labels."""

    validated_horizons, validated_cost = _validate_horizons_and_cost(horizons, cost_bps)
    daily = _require_dataframe(bars, name="bars")
    scope = _require_dataframe(universe, name="universe")
    _require_columns(scope, {"symbol", "signal_date", "eligible"}, name="universe")
    prepared_scope = scope.copy(deep=True)
    prepared_scope["symbol"] = prepared_scope["symbol"].map(_normalize_symbol)
    prepared_scope["signal_date"] = [
        _validate_iso_date(value, field="universe.signal_date")
        for value in prepared_scope["signal_date"].tolist()
    ]
    if prepared_scope.duplicated(["symbol", "signal_date"]).any():
        raise ValueError("universe contains normalized duplicate symbol/date pairs")
    prepared_scope["eligible"] = _strict_boolean_series(
        prepared_scope,
        "eligible",
        name="universe",
    )
    eligible = prepared_scope[prepared_scope["eligible"]].copy()
    if eligible.empty:
        raise DataCapabilityBlocked("eligible universe is empty")
    eligible_symbols = set(eligible["symbol"])

    _require_columns(
        daily,
        {"symbol", "date", "open", "high", "low", "close", "volume", "amount", "is_suspended"},
        name="bars",
    )
    normalized_bar_symbols: list[str | None] = []
    for value in daily["symbol"].tolist():
        try:
            normalized_bar_symbols.append(_normalize_symbol(value))
        except ValueError:
            normalized_bar_symbols.append(None)
    daily["symbol"] = normalized_bar_symbols
    daily = daily[daily["symbol"].isin(eligible_symbols)].copy()
    missing_symbols = sorted(eligible_symbols - set(daily["symbol"]))
    if missing_symbols:
        raise DataCapabilityBlocked(
            "bars coverage missing for eligible symbols: " + ", ".join(missing_symbols)
        )
    _require_true_evidence(
        daily,
        ("historical_daily_available", "historical_point_in_time"),
        message="bars lack explicit historical daily evidence",
    )
    limit_locked = _limit_lock_series(daily)
    if not _forward_adjustment_proven(daily):
        raise DataCapabilityBlocked(
            "bars lack explicit forward-adjusted (qfq) price evidence"
        )
    daily = _prepare_symbol_dates(daily, name="bars")
    daily["is_suspended"] = _strict_boolean_series(
        daily, "is_suspended", name="bars"
    )
    daily["is_limit_locked"] = pd.Series(
        limit_locked.tolist(), index=daily.index, dtype=bool
    )
    for column in ("high", "low"):
        daily[column] = _numeric_allow_missing(daily, column, name="bars")
    for column in ("open", "close"):
        daily[column] = _numeric_allow_missing(
            daily,
            column,
            name="bars",
            allow_non_finite=True,
        )
    for column in ("volume", "amount"):
        daily[column] = _numeric_allow_missing(
            daily,
            column,
            name="bars",
            nonnegative=True,
            allow_non_finite=True,
        )

    available_pairs = set(zip(daily["symbol"], daily["date"], strict=False))
    required_pairs = set(zip(eligible["symbol"], eligible["signal_date"], strict=False))
    missing_pairs = sorted(required_pairs - available_pairs)
    if missing_pairs:
        raise DataCapabilityBlocked(
            "bars coverage missing for eligible signal pairs: "
            + ", ".join(f"{symbol}@{day}" for symbol, day in missing_pairs)
        )

    calendar = sorted(daily["date"].unique().tolist())
    calendar_index = {day: index for index, day in enumerate(calendar)}
    missing_signal_dates = sorted(set(eligible["signal_date"]) - set(calendar))
    if missing_signal_dates:
        raise DataCapabilityBlocked(
            "signal dates are absent from historical trading calendar: "
            + ", ".join(missing_signal_dates)
        )
    records = {
        (record["symbol"], record["date"]): record
        for record in daily.to_dict("records")
    }
    rows: list[dict[str, Any]] = []
    for item in eligible.sort_values(
        ["signal_date", "symbol"], kind="mergesort"
    ).to_dict("records"):
        symbol = item["symbol"]
        signal_date = item["signal_date"]
        signal_index = calendar_index[signal_date]
        entry_date = calendar[signal_index + 1] if signal_index + 1 < len(calendar) else None
        signal_bar = records.get((symbol, signal_date))
        entry_bar = records.get((symbol, entry_date)) if entry_date is not None else None
        tradable = False
        reason = "entry_session_unavailable"
        entry_open = math.nan
        if signal_bar is None:
            reason = "signal_bar_missing"
        elif entry_date is None:
            reason = "entry_session_unavailable"
        elif entry_bar is None:
            reason = "entry_bar_missing"
        elif bool(entry_bar["is_suspended"]):
            reason = "entry_suspended"
        elif pd.isna(entry_bar["volume"]):
            reason = "entry_volume_missing"
        elif not math.isfinite(float(entry_bar["volume"])):
            reason = "entry_volume_non_finite"
        elif float(entry_bar["volume"]) <= 0:
            reason = "entry_zero_volume"
        elif pd.isna(entry_bar["amount"]):
            reason = "entry_amount_missing"
        elif not math.isfinite(float(entry_bar["amount"])):
            reason = "entry_amount_non_finite"
        elif float(entry_bar["amount"]) <= 0:
            reason = "entry_zero_amount"
        elif pd.isna(entry_bar["open"]):
            reason = "entry_open_missing"
        elif not math.isfinite(float(entry_bar["open"])):
            reason = "entry_open_non_finite"
        elif float(entry_bar["open"]) <= 0:
            reason = "entry_open_invalid"
        elif bool(entry_bar["is_limit_locked"]):
            reason = "entry_limit_locked"
        else:
            tradable = True
            reason = "tradable"
            entry_open = float(entry_bar["open"])

        output: dict[str, Any] = {
            "symbol": symbol,
            "signal_date": signal_date,
            "eligible": True,
            "universe_exclusion_reason": item.get("exclusion_reason", "eligible"),
            "entry_date": entry_date,
            "entry_open": entry_open,
            "tradable": tradable,
            "untradable_reason": reason,
            "adjustment_basis": "qfq",
            "cost_bps": validated_cost,
        }
        for horizon in validated_horizons:
            suffix = f"{horizon}d"
            target_index = signal_index + horizon
            exit_date = calendar[target_index] if target_index < len(calendar) else None
            complete = False
            status = "entry_not_tradable"
            gross_return = math.nan
            if tradable:
                if exit_date is None:
                    status = "horizon_session_unavailable"
                else:
                    exit_bar = records.get((symbol, exit_date))
                    if exit_bar is None:
                        status = "horizon_bar_missing"
                    elif pd.isna(exit_bar["close"]):
                        status = "horizon_close_missing"
                    elif not math.isfinite(float(exit_bar["close"])):
                        status = "horizon_close_non_finite"
                    elif float(exit_bar["close"]) <= 0:
                        status = "horizon_close_invalid"
                    else:
                        complete = True
                        status = "complete"
                        gross_return = float(exit_bar["close"]) / entry_open - 1.0
            output[f"exit_date_{suffix}"] = exit_date
            output[f"horizon_{suffix}_complete"] = complete
            output[f"label_status_{suffix}"] = status
            output[f"gross_return_{suffix}"] = gross_return
        rows.append(output)

    result = pd.DataFrame(rows).sort_values(
        ["signal_date", "symbol"], kind="mergesort"
    ).reset_index(drop=True)
    round_trip_cost = validated_cost / 10_000.0
    for horizon in validated_horizons:
        suffix = f"{horizon}d"
        result[f"benchmark_gross_return_{suffix}"] = math.nan
        result[f"benchmark_constituent_count_{suffix}"] = 0
        result[f"excess_return_{suffix}"] = math.nan
        for signal_date, indices in result.groupby("signal_date", sort=True).groups.items():
            group = result.loc[indices]
            benchmark_members = group[
                group["tradable"] & group[f"horizon_{suffix}_complete"]
            ]
            if benchmark_members.empty:
                raise DataCapabilityBlocked(
                    f"benchmark is empty for {signal_date} at {horizon}-day horizon"
                )
            benchmark = float(benchmark_members[f"gross_return_{suffix}"].mean())
            result.loc[indices, f"benchmark_gross_return_{suffix}"] = benchmark
            result.loc[indices, f"benchmark_constituent_count_{suffix}"] = len(
                benchmark_members
            )
            complete_indices = benchmark_members.index
            result.loc[complete_indices, f"excess_return_{suffix}"] = (
                result.loc[complete_indices, f"gross_return_{suffix}"]
                - benchmark
                - round_trip_cost
            )
    return result


def build_rebalance_frame(
    *,
    observations: pd.DataFrame,
    trading_dates: Sequence[str],
    rebalance_days: int = 5,
) -> pd.DataFrame:
    """Select fixed, non-overlapping rebalance cross-sections from a calendar."""

    if isinstance(rebalance_days, bool) or not isinstance(rebalance_days, int):
        raise TypeError("rebalance_days must be an integer")
    if rebalance_days < 1:
        raise ValueError("rebalance_days must be at least 1")
    calendar = _validate_date_sequence(trading_dates, field="trading_dates")
    if calendar != sorted(calendar):
        raise ValueError("trading_dates must be in strictly increasing order")
    frame = _require_dataframe(observations, name="observations")
    if "signal_date" not in frame.columns:
        if "date" not in frame.columns:
            raise DataCapabilityBlocked(
                "observations missing required signal_date column"
            )
        frame = frame.rename(columns={"date": "signal_date"})
    _require_columns(frame, {"symbol", "signal_date"}, name="observations")
    reserved = {
        "rebalance_index",
        "rebalance_date",
        "holding_period_start_date",
        "holding_period_end_date",
    }
    conflicts = sorted(reserved & set(frame.columns))
    if conflicts:
        raise ValueError(
            "observations contain reserved rebalance columns: " + ", ".join(conflicts)
        )
    frame["symbol"] = frame["symbol"].map(_normalize_symbol)
    frame["signal_date"] = [
        _validate_iso_date(value, field="observations.signal_date")
        for value in frame["signal_date"].tolist()
    ]
    if frame.duplicated(["symbol", "signal_date"]).any():
        raise ValueError("observations contain normalized duplicate symbol/date pairs")
    unknown = sorted(set(frame["signal_date"]) - set(calendar))
    if unknown:
        raise ValueError(
            "observations contain dates absent from trading_dates: " + ", ".join(unknown)
        )

    anchor_metadata: dict[str, tuple[int, str]] = {}
    for index, start in enumerate(range(0, len(calendar), rebalance_days)):
        end = min(start + rebalance_days - 1, len(calendar) - 1)
        anchor_metadata[calendar[start]] = (index, calendar[end])
    result = frame[frame["signal_date"].isin(anchor_metadata)].copy()
    if result.empty:
        raise DataCapabilityBlocked("no observations exist on fixed rebalance dates")
    result["rebalance_index"] = result["signal_date"].map(
        lambda day: anchor_metadata[day][0]
    )
    result["rebalance_date"] = result["signal_date"]
    result["holding_period_start_date"] = result["signal_date"]
    result["holding_period_end_date"] = result["signal_date"].map(
        lambda day: anchor_metadata[day][1]
    )
    return result.sort_values(
        ["signal_date", "symbol"], kind="mergesort"
    ).reset_index(drop=True)
