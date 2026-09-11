from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import math
import numbers
import re
from collections.abc import Sequence as SequenceABC
from datetime import date, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from five_formula_catalog import (
    nested_variable_catalog,
    subsystem_catalog,
    validate_catalog,
)
from three_formula_composite_backtest import ema, formula_feature_arrays


YOUZI_FORMULA = "游资资金监控"
INSTITUTION_FORMULA = "机构资金监控"
BIG_BULL_FORMULA = "大牛线撑压版"
FEILONG_FORMULA = "飞龙在天"
DEALER_FORMULA = "庄家资金监控"

_FORMULA_SOURCES: tuple[tuple[Path, str], ...] = (
    (
        Path(r"C:\new_tdx_mock\T0002\gs_bak\大牛线.txt"),
        "0FD94557892AAC0FF1BA2D99229F094900D73F11F48DC510B3EFDA326EE0AB00",
    ),
    (
        Path(r"C:\new_tdx_mock\T0002\gs_bak\飞龙在天.txt"),
        "AABCEC3D83B2B37D01D53BA4D9C281A745E29F53D941F3704DA95DCEA114E1E0",
    ),
    (
        Path(r"C:\new_tdx_mock\T0002\gs_bak\游资资金.txt"),
        "95576CF5BEFD882A64056640A343A69CB64B278AE10203A5CA2AD375936DD896",
    ),
    (
        Path(r"C:\new_tdx_mock\T0002\gs_bak\庄家资金监控.txt"),
        "7A14C0B6C667169231B119FA0A89F60CDF6D009C45AF74AFFAD7F34B3F8AB668",
    ),
    (
        Path(r"C:\new_tdx_mock\T0002\gs_bak\机构资金.txt"),
        "D631B1B32333108E7C92A5A6D2AA6C235CF5B68B6741A21D6B8FA45A5B5423C4",
    ),
)

_BAR_COLUMNS = ("date", "open", "high", "low", "close", "volume", "amount")
_SHANGHAI = ZoneInfo("Asia/Shanghai")
_DATE8_PATTERN = re.compile(r"\d{8}")
_ISO_DATE_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}"
    r"(?:[T ]\d{2}:\d{2}"
    r"(?::\d{2}(?:\.\d{1,9})?)?"
    r"(?:Z|[+-]\d{2}:\d{2})?"
    r")?"
)
_FORMULA_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "dnx_float_cap": ("流通市值",),
    "dnx_dealer_in_out": ("OUTPUT4", "OUTPUT6"),
    "dnx_support_pressure": ("支撑一", "支撑二", "压力一", "压力二"),
    "fl_dragon": ("OUTPUT3",),
    "fl_board": ("OUTPUT4",),
    "fl_surge": ("OUTPUT5",),
    "fl_wave": ("波",),
    "fl_segment": ("段",),
    "fl_private": ("OUTPUT6",),
    "fl_main_rise": ("OUTPUT3", "OUTPUT4", "OUTPUT5", "OUTPUT6"),
}
_MARKET_BY_PREFIX = MappingProxyType({
    **{prefix: "SH" for prefix in ("600", "601", "603", "605", "688", "689")},
    **{prefix: "SZ" for prefix in ("000", "001", "002", "003", "300", "301")},
})
_BJ_MARKET_PREFIXES = frozenset(("43", "83", "87", "88", "92"))


class FeatureInputError(ValueError):
    pass


class ProvenanceError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _verified_provenance() -> dict[str, Any]:
    source_rows: list[dict[str, str]] = []
    for path, expected in _FORMULA_SOURCES:
        if not path.is_file():
            raise ProvenanceError(f"formula_source_missing:{path}")
        actual = _sha256(path)
        if actual != expected:
            raise ProvenanceError(
                f"formula_source_sha256_mismatch:{path}:expected={expected}:actual={actual}"
            )
        source_rows.append(
            {
                "path": str(path),
                "sha256": actual,
                "expected_sha256": expected,
                "status": "verified",
                "access": "read_only",
            }
        )
    adapter = Path(__file__).resolve()
    return {
        "formula_sources": source_rows,
        "adapter": {
            "path": str(adapter),
            "sha256": _sha256(adapter),
            "access": "read_only_self_digest",
        },
    }


def _require_front_adjusted(dividend_type: int) -> None:
    if type(dividend_type) is not int or dividend_type != 1:
        raise ValueError("dividend_type_must_equal_1")


def _market_for_code(code: str) -> str:
    if code[:2] in _BJ_MARKET_PREFIXES:
        return "BJ"
    market = _MARKET_BY_PREFIX.get(code[:3])
    if market is None:
        raise ValueError(f"unsupported_a_share_code:{code}")
    return market


def _normalize_symbol(value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"invalid_stock_code:{value}")
    raw = value.strip().upper()
    match = re.fullmatch(r"(\d{6})(?:\.(SH|SZ|BJ))?", raw)
    if not match:
        raise ValueError(f"invalid_stock_code:{value}")
    code, _ = match.groups()
    return f"{code}.{_market_for_code(code)}"


def _sequence_values(value: Any, label: str) -> list[Any]:
    if isinstance(value, np.ndarray):
        if value.ndim != 1:
            raise FeatureInputError(f"{label}_must_be_sequence")
        return value.tolist()
    if isinstance(value, (str, bytes, bytearray, Mapping)) or not isinstance(
        value, SequenceABC
    ):
        raise FeatureInputError(f"{label}_must_be_sequence")
    try:
        return list(value)
    except Exception as exc:
        raise FeatureInputError(f"{label}_sequence_iteration_failed") from exc


def _mapping_copy(value: Any, label: str) -> dict[Any, Any]:
    if not isinstance(value, Mapping):
        raise FeatureInputError(f"{label}_must_be_mapping")
    try:
        return dict(value)
    except Exception as exc:
        raise FeatureInputError(f"{label}_mapping_copy_failed") from exc


def _symbol_entries(
    symbols: Sequence[str],
) -> tuple[tuple[Any, str | None, Exception | None], ...]:
    entries: list[tuple[Any, str | None, Exception | None]] = []
    seen: set[str] = set()
    for raw_symbol in _sequence_values(symbols, "symbols"):
        try:
            symbol = _normalize_symbol(raw_symbol)
        except Exception as exc:
            entries.append((raw_symbol, None, exc))
            continue
        if symbol in seen:
            raise FeatureInputError(f"duplicate_normalized_symbol:{symbol}")
        seen.add(symbol)
        entries.append((raw_symbol, symbol, None))
    if not entries:
        raise FeatureInputError("symbols_must_not_be_empty")
    return tuple(entries)


def _error(
    *,
    symbol: str,
    formula: str,
    stage: str,
    status: str,
    error_type: str,
    message: str,
) -> dict[str, str]:
    return {
        "symbol": symbol,
        "formula": formula,
        "stage": stage,
        "status": status,
        "error_type": error_type,
        "message": message,
    }


def compute_youzi_price_features(close: np.ndarray) -> dict[str, np.ndarray]:
    try:
        values = np.asarray(close, dtype=float)
    except (TypeError, ValueError) as exc:
        raise FeatureInputError("close_must_be_nonempty_1d_finite") from exc
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise FeatureInputError("close_must_be_nonempty_1d_finite")
    aaa = ema(values, 5) - ema(values, 30)
    ddd = ema(aaa, 5)
    buyer_intent = (aaa - ddd) * 2.0
    return {
        "youzi_aaa_trend_diff": aaa,
        "youzi_ddd_signal": ddd,
        "youzi_buyer_intent": buyer_intent,
        "youzi_positive_buyer_bar": buyer_intent > 0,
    }


def fetch_youzi_history(
    tq: Any,
    symbols: Sequence[str],
    count: int,
    dividend_type: int = 1,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    _require_front_adjusted(dividend_type)
    if type(count) is not int or count <= 0:
        raise ValueError("count_must_be_positive_int")
    return _fetch_youzi_history_entries(tq, _symbol_entries(symbols), count)


def _fetch_youzi_history_entries(
    tq: Any,
    symbol_entries: tuple[tuple[Any, str | None, Exception | None], ...],
    count: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payloads: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    for raw_symbol, symbol, symbol_error in symbol_entries:
        if symbol_error is not None:
            errors.append(
                _error(
                    symbol=str(raw_symbol),
                    formula=YOUZI_FORMULA,
                    stage="symbol_validation",
                    status="invalid",
                    error_type=type(symbol_error).__name__,
                    message=str(symbol_error),
                )
            )
            continue
        assert symbol is not None
        try:
            payload = tq.formula_process_mul_zb(
                YOUZI_FORMULA,
                stock_list=[symbol],
                count=0,
                return_count=count,
                return_date=True,
                dividend_type=1,
            )
        except Exception as exc:
            errors.append(
                _error(
                    symbol=symbol,
                    formula=YOUZI_FORMULA,
                    stage="formula_process_mul_zb",
                    status="failed",
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )
            continue
        if not isinstance(payload, Mapping):
            errors.append(
                _error(
                    symbol=symbol,
                    formula=YOUZI_FORMULA,
                    stage="formula_payload",
                    status="unavailable",
                    error_type="InvalidPayload",
                    message="formula_payload_not_mapping",
                )
            )
            continue
        error_id = str(payload.get("ErrorId"))
        if error_id not in {"0", "19"}:
            errors.append(
                _error(
                    symbol=symbol,
                    formula=YOUZI_FORMULA,
                    stage="formula_payload",
                    status="failed",
                    error_type="FormulaError",
                    message=f"formula_error_id:{error_id}",
                )
            )
            continue
        payloads[symbol] = payload
        code = symbol.split(".", 1)[0]
        node = payload.get(symbol)
        if not isinstance(node, Mapping):
            node = payload.get(code)
        if not isinstance(node, Mapping):
            errors.append(
                _error(
                    symbol=symbol,
                    formula=YOUZI_FORMULA,
                    stage="formula_payload",
                    status="unavailable",
                    error_type="MissingPointInTimeNode",
                    message="point_in_time_formula_node_missing",
                )
            )
    return payloads, errors


def fetch_institution_current(
    tq: Any,
    symbols: Sequence[str],
    count: int = 60,
    dividend_type: int = 1,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    _require_front_adjusted(dividend_type)
    if type(count) is not int or count != 60:
        raise ValueError("institution_count_must_equal_60")
    return _fetch_institution_current_entries(tq, _symbol_entries(symbols))


def _fetch_institution_current_entries(
    tq: Any,
    symbol_entries: tuple[tuple[Any, str | None, Exception | None], ...],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payloads: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    for raw_symbol, symbol, symbol_error in symbol_entries:
        if symbol_error is not None:
            errors.append(
                _error(
                    symbol=str(raw_symbol),
                    formula=INSTITUTION_FORMULA,
                    stage="symbol_validation",
                    status="invalid",
                    error_type=type(symbol_error).__name__,
                    message=str(symbol_error),
                )
            )
            continue
        assert symbol is not None
        try:
            setup = tq.formula_set_data_info(
                symbol,
                count=60,
                dividend_type=1,
            )
        except Exception as exc:
            errors.append(
                _error(
                    symbol=symbol,
                    formula=INSTITUTION_FORMULA,
                    stage="formula_set_data_info",
                    status="failed",
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )
            continue
        if not isinstance(setup, Mapping) or str(setup.get("ErrorId")) != "0":
            errors.append(
                _error(
                    symbol=symbol,
                    formula=INSTITUTION_FORMULA,
                    stage="formula_set_data_info",
                    status="failed",
                    error_type="FormulaSetupError",
                    message=f"formula_set_data_info_failed:{setup}",
                )
            )
            continue
        try:
            result = tq.formula_zb(
                INSTITUTION_FORMULA,
                symbol.split(".", 1)[0],
                xsflag=2,
            )
        except Exception as exc:
            errors.append(
                _error(
                    symbol=symbol,
                    formula=INSTITUTION_FORMULA,
                    stage="formula_zb",
                    status="failed",
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )
            continue
        if not isinstance(result, Mapping) or str(result.get("ErrorId")) != "0":
            errors.append(
                _error(
                    symbol=symbol,
                    formula=INSTITUTION_FORMULA,
                    stage="formula_zb",
                    status="failed",
                    error_type="FormulaError",
                    message=f"formula_zb_failed:{result}",
                )
            )
            continue
        payloads[symbol] = result
    return payloads, errors


def _date_string(value: Any) -> str:
    try:
        if isinstance(value, (pd.Timestamp, datetime, date, np.datetime64)):
            timestamp = pd.Timestamp(value)
        elif type(value) is str:
            raw = value.strip()
            if _DATE8_PATTERN.fullmatch(raw):
                timestamp = pd.Timestamp(datetime.strptime(raw, "%Y%m%d"))
            elif _ISO_DATE_PATTERN.fullmatch(raw):
                timestamp = pd.Timestamp(raw)
            else:
                raise FeatureInputError(f"invalid_date:{value}")
        else:
            raise FeatureInputError(f"invalid_date:{value}")
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize(_SHANGHAI)
        else:
            timestamp = timestamp.tz_convert(_SHANGHAI)
        return timestamp.strftime("%Y%m%d")
    except FeatureInputError:
        raise
    except Exception as exc:
        raise FeatureInputError(f"invalid_date:{value}") from exc


def _looks_like_date(value: Any) -> bool:
    if isinstance(value, (pd.Timestamp, datetime, date, np.datetime64)):
        return True
    if type(value) is not str:
        return False
    raw = value.strip()
    return bool(
        _DATE8_PATTERN.fullmatch(raw)
        or re.match(r"^\d{4}-\d{2}-\d{2}", raw)
    )


def _mapping_value_for_symbol(
    values: Mapping[str, Any], raw_symbol: Any, symbol: str
) -> Any:
    missing = object()
    for key in (str(raw_symbol), symbol, symbol.split(".", 1)[0]):
        candidate = values.get(key, missing)
        if candidate is not missing:
            return candidate
    return missing


def _validated_requested_bars(
    bars_by_symbol: Any,
    symbol_entries: tuple[tuple[Any, str | None, Exception | None], ...],
) -> dict[str, pd.DataFrame]:
    bars_mapping = _mapping_copy(bars_by_symbol, "bars_by_symbol")
    validated: dict[str, pd.DataFrame] = {}
    for raw_symbol, symbol, symbol_error in symbol_entries:
        if symbol_error is not None:
            continue
        assert symbol is not None
        frame = _mapping_value_for_symbol(bars_mapping, raw_symbol, symbol)
        if not isinstance(frame, pd.DataFrame):
            raise FeatureInputError(f"bars_must_be_dataframe:{symbol}")
        missing = [column for column in _BAR_COLUMNS if column not in frame.columns]
        if missing:
            raise FeatureInputError(
                f"bars_missing_columns:{symbol}:{','.join(missing)}"
            )
        try:
            date_values = frame["date"].tolist()
        except Exception as exc:
            raise FeatureInputError(f"bars_date_read_failed:{symbol}") from exc
        for date_value in date_values:
            _date_string(date_value)
        validated[symbol] = frame
    return validated


def _is_formula_sequence(value: Any) -> bool:
    return isinstance(value, np.ndarray) or (
        isinstance(value, SequenceABC)
        and not isinstance(value, (str, bytes, bytearray, Mapping))
    )


def _validated_formula_sequence(value: Any, label: str) -> list[dict[Any, Any]]:
    items = _sequence_values(value, label)
    validated: list[dict[Any, Any]] = []
    for index, item in enumerate(items):
        copied = _mapping_copy(item, f"{label}_item_{index}")
        if "Date" not in copied or "Value" not in copied:
            raise FeatureInputError(f"{label}_item_fields_invalid:{index}")
        _date_string(copied["Date"])
        validated.append(copied)
    return validated


def _validated_nested_formula_mapping(value: Any, label: str) -> dict[Any, Any]:
    copied = _mapping_copy(value, label)
    validated: dict[Any, Any] = {}
    for key, nested in copied.items():
        if _looks_like_date(key):
            _date_string(key)
        if isinstance(nested, Mapping):
            validated[key] = _validated_nested_formula_mapping(
                nested, f"{label}_{key}"
            )
        elif _is_formula_sequence(nested):
            validated[key] = _validated_formula_sequence(
                nested, f"{label}_{key}"
            )
        else:
            validated[key] = nested
    return validated


def _validated_formula_history(value: Any) -> dict[str, dict[str, Any]]:
    history = _mapping_copy(value, "formula_history_by_symbol")
    validated: dict[str, dict[str, Any]] = {}
    for symbol_key, symbol_value in history.items():
        if type(symbol_key) is not str:
            raise FeatureInputError("formula_history_symbol_key_must_be_string")
        symbol_mapping = _mapping_copy(
            symbol_value, f"formula_history_symbol_{symbol_key}"
        )
        validated_symbol: dict[str, Any] = {}
        for formula, formula_value in symbol_mapping.items():
            if type(formula) is not str:
                raise FeatureInputError("formula_history_formula_key_must_be_string")
            formula_mapping = _mapping_copy(
                formula_value, f"formula_history_formula_{formula}"
            )
            validated_formula: dict[Any, Any] = {}
            for field, field_value in formula_mapping.items():
                if type(field) is not str:
                    raise FeatureInputError(
                        f"formula_history_field_key_must_be_string:{formula}"
                    )
                if isinstance(field_value, Mapping):
                    validated_formula[field] = _validated_nested_formula_mapping(
                        field_value, f"formula_history_field_{formula}_{field}"
                    )
                elif _is_formula_sequence(field_value):
                    validated_formula[field] = _validated_formula_sequence(
                        field_value, f"formula_history_field_{formula}_{field}"
                    )
                else:
                    raise FeatureInputError(
                        f"formula_history_field_must_be_mapping_or_sequence:"
                        f"{formula}:{field}"
                    )
            validated_symbol[formula] = validated_formula
        validated[symbol_key] = validated_symbol
    return validated


def _normalized_signal_dates(signal_dates: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in _sequence_values(signal_dates, "signal_dates"):
        date = _date_string(value)
        if date in seen:
            raise FeatureInputError(f"duplicate_normalized_signal_date:{date}")
        seen.add(date)
        normalized.append(date)
    if not normalized:
        raise FeatureInputError("signal_dates_must_not_be_empty")
    return tuple(normalized)


def _finite_number(value: Any) -> float | None:
    if isinstance(value, (bool, np.bool_)):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _dated_formula_map(node: Any) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    seen: set[tuple[str, str]] = set()

    def add(date_value: Any, field: Any, value: Any) -> None:
        date = _date_string(date_value)
        if type(field) is not str:
            return
        identity = (field, date)
        if identity in seen:
            raise FeatureInputError(f"duplicate_formula_field_date:{field}:{date}")
        seen.add(identity)
        number = _finite_number(value)
        if number is not None:
            result.setdefault(date, {})[field] = number

    def visit(candidate: Any) -> None:
        if not isinstance(candidate, Mapping):
            return
        for field, value in candidate.items():
            date = _date_string(field) if _looks_like_date(field) else ""
            if date and isinstance(value, Mapping):
                for nested_field, nested_value in value.items():
                    add(date, nested_field, nested_value)
                continue
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, Mapping) and "Date" in item and "Value" in item:
                        add(item["Date"], field, item["Value"])
                continue
            if isinstance(value, Mapping):
                visit(value)

    visit(node)
    return result


def _symbol_mapping(
    values: Mapping[str, Any], raw_symbol: str, symbol: str
) -> Mapping[str, Any]:
    for key in (symbol, raw_symbol, symbol.split(".", 1)[0]):
        node = values.get(key)
        if isinstance(node, Mapping):
            return node
    return {}


def _formula_map(
    symbol_history: Mapping[str, Any], formula: str, signal_date: str
) -> dict[str, dict[str, float]]:
    dated = _dated_formula_map(symbol_history.get(formula, {}))
    return {date: fields for date, fields in dated.items() if date <= signal_date}


def _prepare_records(frame: Any, signal_date: str) -> list[dict[str, Any]]:
    if not isinstance(frame, pd.DataFrame):
        raise ValueError("bars_must_be_dataframe")
    missing = [column for column in _BAR_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"bars_missing_columns:{','.join(missing)}")
    prepared = frame.loc[:, _BAR_COLUMNS].copy()
    prepared["date"] = prepared["date"].map(_date_string)
    prepared = prepared.loc[prepared["date"] <= signal_date].copy()
    if prepared.empty or signal_date not in set(prepared["date"]):
        raise ValueError(f"signal_date_bar_missing:{signal_date}")
    for column in _BAR_COLUMNS[1:]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    prepared = prepared.sort_values("date", kind="stable")
    duplicate_dates = prepared["date"].duplicated(keep=False)
    if duplicate_dates.any():
        raise ValueError("bars_duplicate_dates")
    numeric = prepared.loc[:, _BAR_COLUMNS[1:]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("bars_must_be_finite")
    return prepared.to_dict(orient="records")


def _required_formula_available(
    key: str, dated: Mapping[str, Mapping[str, float]], signal_date: str
) -> bool:
    required = _FORMULA_REQUIRED_FIELDS.get(key)
    if not required:
        return True
    actual = dated.get(signal_date, {})
    if key == "dnx_support_pressure":
        return any(field in actual for field in required[:2]) and any(
            field in actual for field in required[2:]
        )
    if key == "fl_main_rise":
        return any(field in actual for field in ("OUTPUT5", "OUTPUT6")) and any(
            field in actual for field in ("OUTPUT3", "OUTPUT4")
        )
    return all(field in actual for field in required)


def _causal_formula_values(
    *,
    symbol: str,
    signal_date: str,
    records: list[dict[str, Any]],
    symbol_history: Mapping[str, Any],
) -> tuple[dict[str, float], dict[str, str], dict[str, float]]:
    big_map = _formula_map(symbol_history, BIG_BULL_FORMULA, signal_date)
    feilong_map = _formula_map(symbol_history, FEILONG_FORMULA, signal_date)
    dealer_map = _formula_map(symbol_history, DEALER_FORMULA, signal_date)
    arrays, _ = formula_feature_arrays(
        symbol,
        records,
        big_map,
        feilong_map,
        dealer_map,
    )
    values: dict[str, float] = {}
    statuses: dict[str, str] = {}
    for row in subsystem_catalog():
        key = str(row["key"])
        formula = str(row["formula"])
        if formula not in {BIG_BULL_FORMULA, FEILONG_FORMULA}:
            continue
        dated = big_map if formula == BIG_BULL_FORMULA else feilong_map
        if not _required_formula_available(key, dated, signal_date):
            values[key] = math.nan
            statuses[key] = "missing_point_in_time_formula_field"
            continue
        candidate = arrays.get(key)
        number = (
            _finite_number(candidate[-1])
            if isinstance(candidate, np.ndarray) and candidate.size
            else None
        )
        values[key] = number if number is not None else math.nan
        statuses[key] = (
            "available_causal_formula"
            if key in _FORMULA_REQUIRED_FIELDS
            else "computed_causal_price"
        )

    control_degree = _finite_number(arrays["zj_control_degree"][-1])
    dealer_values = {
        "zj_output3": control_degree if control_degree is not None else math.nan,
        "zj_output4": (
            float(control_degree > 100.0)
            if control_degree is not None
            else math.nan
        ),
        "zj_control_degree": (
            control_degree if control_degree is not None else math.nan
        ),
        "zj_control_scale": 100.0,
    }
    values.update(dealer_values)
    statuses.update({key: "computed_causal_price" for key in dealer_values})
    nested_dealer = {
        "zj_b2": float(arrays["zj_cost_pressure"][-1]),
        "zj_b5": float(arrays["zj_fund_strength"][-1]),
        "zj_b6": float(arrays["zj_control_spread"][-1]),
    }
    return values, statuses, nested_dealer


def _field_evidence(
    *,
    symbol: str,
    date: str,
    key: str,
    formula: str,
    role: str,
    source: str,
    status: str,
    value: Any,
    node_type: str = "top_level",
) -> dict[str, Any]:
    number = _finite_number(value)
    return {
        "symbol": symbol,
        "date": date,
        "key": key,
        "formula": formula,
        "role": role,
        "source": source,
        "status": status,
        "value": number,
        "node_type": node_type,
    }


def _build_feature_row(
    *,
    raw_symbol: str,
    symbol: str,
    signal_date: str,
    frame: pd.DataFrame,
    symbol_history: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records = _prepare_records(frame, signal_date)
    values, statuses, nested_dealer = _causal_formula_values(
        symbol=symbol,
        signal_date=signal_date,
        records=records,
        symbol_history=symbol_history,
    )
    close = np.array([record["close"] for record in records], dtype=float)
    values.update(
        {
            key: float(array[-1])
            for key, array in compute_youzi_price_features(close).items()
        }
    )
    for key in (
        "youzi_aaa_trend_diff",
        "youzi_ddd_signal",
        "youzi_buyer_intent",
        "youzi_positive_buyer_bar",
    ):
        statuses[key] = "computed_causal_price"
    values["youzi_l2_tiers"] = math.nan
    statuses["youzi_l2_tiers"] = "missing_point_in_time"

    institution_map = _formula_map(
        symbol_history, INSTITUTION_FORMULA, signal_date
    )
    institution_fields = institution_map.get(signal_date, {})
    catalog = subsystem_catalog()
    evidence_rows: list[dict[str, Any]] = []
    for catalog_row in catalog:
        key = str(catalog_row["key"])
        formula = str(catalog_row["formula"])
        if formula == INSTITUTION_FORMULA:
            source_field = str(catalog_row["name"])
            number = _finite_number(institution_fields.get(source_field))
            values[key] = number if number is not None else math.nan
            statuses[key] = (
                "available_point_in_time"
                if number is not None
                else "missing_point_in_time"
            )
        evidence_rows.append(
            _field_evidence(
                symbol=symbol,
                date=signal_date,
                key=key,
                formula=formula,
                role=str(catalog_row["role"]),
                source=formula,
                status=statuses.get(key, "unavailable"),
                value=values.get(key),
            )
        )

    youzi_fields = _formula_map(
        symbol_history, YOUZI_FORMULA, signal_date
    ).get(signal_date, {})
    for nested in nested_variable_catalog():
        if nested["top_level_alias"] is True:
            continue
        formula = str(nested["formula"])
        key = str(nested["key"])
        if formula == YOUZI_FORMULA:
            number = _finite_number(youzi_fields.get(str(nested["variable"])))
            status = (
                "available_point_in_time"
                if number is not None
                else "missing_point_in_time"
            )
        elif formula == INSTITUTION_FORMULA:
            number = _finite_number(
                institution_fields.get(str(nested["variable"]))
            )
            status = (
                "available_point_in_time"
                if number is not None
                else "missing_point_in_time"
            )
        else:
            number = nested_dealer.get(key)
            status = (
                "computed_causal_price"
                if number is not None
                else "unavailable_confirmation_node"
            )
        if nested["top_level_alias"] is not True:
            values[key] = number if number is not None else math.nan
        evidence_rows.append(
            _field_evidence(
                symbol=symbol,
                date=signal_date,
                key=key,
                formula=formula,
                role=str(nested["role"]),
                source=formula,
                status=status,
                value=number,
                node_type="nested",
            )
        )
    raw_node_keys = [
        str(row["key"])
        for row in nested_variable_catalog()
        if row["top_level_alias"] is not True
    ]
    return {
        "symbol": symbol,
        "date": signal_date,
        **{str(row["key"]): values.get(str(row["key"]), math.nan) for row in catalog},
        **{key: values.get(key, math.nan) for key in raw_node_keys},
    }, evidence_rows


def build_historical_features(
    *,
    symbols: Sequence[str],
    signal_dates: Sequence[str],
    bars_by_symbol: Mapping[str, pd.DataFrame],
    formula_history_by_symbol: Mapping[str, Mapping[str, Any]],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    symbol_entries = _symbol_entries(symbols)
    normalized_dates = _normalized_signal_dates(signal_dates)
    bars_mapping = _validated_requested_bars(bars_by_symbol, symbol_entries)
    history_mapping = _validated_formula_history(formula_history_by_symbol)
    provenance = _verified_provenance()
    catalog = subsystem_catalog()
    validate_catalog(catalog)
    raw_node_keys = [
        str(row["key"])
        for row in nested_variable_catalog()
        if row["top_level_alias"] is not True
    ]
    columns = [
        "symbol",
        "date",
        *[str(row["key"]) for row in catalog],
        *raw_node_keys,
    ]
    rows: list[dict[str, Any]] = []
    field_evidence: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for raw_symbol, symbol, symbol_error in symbol_entries:
        if symbol_error is not None:
            errors.append(
                _error(
                    symbol=str(raw_symbol),
                    formula="five_formula_features",
                    stage="symbol_validation",
                    status="invalid",
                    error_type=type(symbol_error).__name__,
                    message=str(symbol_error),
                )
            )
            continue
        assert symbol is not None
        frame = bars_mapping[symbol]
        history = _symbol_mapping(
            history_mapping, str(raw_symbol), symbol
        )
        for signal_date in normalized_dates:
            try:
                row, row_evidence = _build_feature_row(
                    raw_symbol=str(raw_symbol),
                    symbol=symbol,
                    signal_date=signal_date,
                    frame=frame,
                    symbol_history=history,
                )
                rows.append(row)
                field_evidence.extend(row_evidence)
            except FeatureInputError:
                raise
            except Exception as exc:
                errors.append(
                    _error(
                        symbol=symbol,
                        formula="five_formula_features",
                        stage="historical_feature_build",
                        status="failed",
                        error_type=type(exc).__name__,
                        message=str(exc),
                    )
                )
    result = pd.DataFrame(rows, columns=columns)
    missing = any(
        str(row["status"]).startswith(("missing", "unavailable"))
        for row in field_evidence
    )
    return result, {
        "schema": "FIVE_FORMULA_HISTORICAL_FEATURE_EVIDENCE_V1",
        "status": "PARTIAL" if missing or errors else "PASS",
        "provenance": provenance,
        "fields": field_evidence,
        "errors": errors,
    }


def _latest_formula_number(value: Any) -> float | None:
    candidate = value
    if isinstance(candidate, list):
        if not candidate:
            return None
        candidate = candidate[-1]
    if isinstance(candidate, Mapping):
        candidate = candidate.get("Value")
    return _finite_number(candidate)


def _point_in_time_formula_number(
    value: Any, signal_date: str
) -> tuple[float | None, str | None]:
    if not isinstance(value, list) or not value:
        return None, "point_in_time_series_malformed_or_empty"
    matches: list[float] = []
    for item in value:
        if not isinstance(item, Mapping) or "Date" not in item or "Value" not in item:
            return None, "point_in_time_item_malformed"
        try:
            item_date = _date_string(item["Date"])
        except ValueError:
            return None, "point_in_time_item_date_invalid"
        number = _finite_number(item["Value"])
        if number is None:
            return None, "point_in_time_item_value_non_finite"
        if item_date == signal_date:
            matches.append(number)
    if not matches:
        return None, "point_in_time_exact_date_missing"
    if len(matches) != 1:
        return None, "point_in_time_exact_date_duplicate"
    return matches[0], None


def _youzi_current_node(payload: Any, symbol: str) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    for key in (symbol, symbol.split(".", 1)[0]):
        node = payload.get(key)
        if isinstance(node, Mapping):
            return node
    return {}


def build_current_features(
    *,
    tq: Any,
    symbols: Sequence[str],
    bars_by_symbol: Mapping[str, pd.DataFrame],
    signal_date: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    symbol_entries = _symbol_entries(symbols)
    actual_date = _date_string(signal_date)
    bars_mapping = _validated_requested_bars(bars_by_symbol, symbol_entries)
    provenance = _verified_provenance()
    catalog = subsystem_catalog()
    validate_catalog(catalog)
    youzi_payloads, youzi_errors = _fetch_youzi_history_entries(
        tq, symbol_entries, count=60
    )
    institution_payloads, institution_errors = _fetch_institution_current_entries(
        tq, symbol_entries
    )
    errors: list[dict[str, Any]] = [*youzi_errors, *institution_errors]
    rows: list[dict[str, Any]] = []
    field_evidence: list[dict[str, Any]] = []
    for raw_symbol, symbol, symbol_error in symbol_entries:
        if symbol_error is not None:
            continue
        assert symbol is not None
        frame = bars_mapping[symbol]
        try:
            row, row_evidence = _build_feature_row(
                raw_symbol=str(raw_symbol),
                symbol=symbol,
                signal_date=actual_date,
                frame=frame,
                symbol_history={},
            )
        except FeatureInputError:
            raise
        except Exception as exc:
            errors.append(
                _error(
                    symbol=symbol,
                    formula="five_formula_features",
                    stage="current_feature_build",
                    status="failed",
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )
            continue

        institution_payload = institution_payloads.get(symbol, {})
        institution_values = (
            institution_payload.get("Value", {})
            if isinstance(institution_payload, Mapping)
            else {}
        )
        if not isinstance(institution_values, Mapping):
            institution_values = {}
        for catalog_row in catalog:
            if catalog_row["formula"] != INSTITUTION_FORMULA:
                continue
            key = str(catalog_row["key"])
            number = _latest_formula_number(
                institution_values.get(str(catalog_row["name"]))
            )
            row[key] = number if number is not None else math.nan
            for evidence_row in row_evidence:
                if (
                    evidence_row["node_type"] == "top_level"
                    and evidence_row["key"] == key
                ):
                    evidence_row["value"] = number
                    evidence_row["status"] = (
                        "available_current_formula"
                        if number is not None
                        else "unavailable"
                    )
                    break

        for nested in nested_variable_catalog():
            if nested["formula"] != INSTITUTION_FORMULA:
                continue
            number = _latest_formula_number(
                institution_values.get(str(nested["variable"]))
            )
            for evidence_row in row_evidence:
                if (
                    evidence_row["node_type"] == "nested"
                    and evidence_row["formula"] == INSTITUTION_FORMULA
                    and evidence_row["key"] == nested["key"]
                ):
                    evidence_row["value"] = number
                    evidence_row["status"] = (
                        "available_current_formula"
                        if number is not None
                        else "unavailable"
                    )
                    break

        youzi_node = _youzi_current_node(youzi_payloads.get(symbol), symbol)
        for nested in nested_variable_catalog():
            if nested["formula"] != YOUZI_FORMULA:
                continue
            variable = str(nested["variable"])
            if variable in youzi_node:
                number, issue = _point_in_time_formula_number(
                    youzi_node[variable], actual_date
                )
                if issue is not None:
                    errors.append(
                        _error(
                            symbol=symbol,
                            formula=YOUZI_FORMULA,
                            stage="point_in_time_field_validation",
                            status="unavailable",
                            error_type="PointInTimeFormulaError",
                            message=f"{variable}:{issue}",
                        )
                    )
            else:
                number, issue = None, None
            for evidence_row in row_evidence:
                if (
                    evidence_row["node_type"] == "nested"
                    and evidence_row["formula"] == YOUZI_FORMULA
                    and evidence_row["key"] == nested["key"]
                ):
                    evidence_row["value"] = number
                    evidence_row["status"] = (
                        "available_current_formula"
                        if number is not None
                        else "unavailable"
                    )
                    break
            if nested["top_level_alias"] is not True:
                row[str(nested["key"])] = (
                    number if number is not None else math.nan
                )
        rows.append(row)
        field_evidence.extend(row_evidence)

    raw_node_keys = [
        str(row["key"])
        for row in nested_variable_catalog()
        if row["top_level_alias"] is not True
    ]
    columns = [
        "symbol",
        "date",
        *[str(row["key"]) for row in catalog],
        *raw_node_keys,
    ]
    result = pd.DataFrame(rows, columns=columns)
    missing = any(
        str(row["status"]).startswith(("missing", "unavailable"))
        for row in field_evidence
    )
    return result, {
        "schema": "FIVE_FORMULA_CURRENT_FEATURE_EVIDENCE_V1",
        "status": "PARTIAL" if missing or errors else "PASS",
        "provenance": provenance,
        "fields": field_evidence,
        "errors": errors,
        "requested_symbols": [str(raw_symbol) for raw_symbol, _, _ in symbol_entries],
        "returned_symbols": result["symbol"].tolist(),
    }


def roll_up_node_contributions(
    node_rows: Sequence[Mapping[str, Any]],
    catalog: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    node_values = _sequence_values(node_rows, "node_rows")
    catalog_values = _sequence_values(catalog, "catalog")
    candidate_catalog = [
        _mapping_copy(row, f"catalog_row_{index}")
        for index, row in enumerate(catalog_values)
    ]
    try:
        validate_catalog(candidate_catalog)
        authoritative_catalog = subsystem_catalog()
        if candidate_catalog != authoritative_catalog:
            raise ValueError("catalog content differs from authority")
    except Exception as exc:
        raise ValueError(f"catalog_not_authoritative:{exc}") from exc

    parent_by_node = {
        str(row["key"]): str(row["key"]) for row in authoritative_catalog
    }
    for nested in nested_variable_catalog():
        key = str(nested["key"])
        parent = str(nested["parent_key"])
        existing = parent_by_node.get(key)
        if existing is not None and existing != parent:
            raise ValueError(f"authoritative_node_binding_conflict:{key}")
        parent_by_node[key] = parent

    top_keys = [str(row["key"]) for row in authoritative_catalog]
    contributions: dict[str, list[float]] = {key: [] for key in top_keys}
    seen: set[str] = set()
    raw_values: list[float] = []
    for index, node_value in enumerate(node_values):
        try:
            node = _mapping_copy(node_value, f"node_row_{index}")
        except FeatureInputError as exc:
            raise FeatureInputError(f"node_row_must_be_mapping:{index}") from exc
        for field in ("key", "parent_key", "latent_contribution"):
            if field not in node:
                raise ValueError(f"missing_node_field:{index}:{field}")
        key = node["key"]
        parent = node["parent_key"]
        if type(key) is not str or key not in parent_by_node:
            raise ValueError(f"unknown_node_key:{key}")
        if key in seen:
            raise ValueError(f"duplicate_node_key:{key}")
        seen.add(key)
        expected_parent = parent_by_node[key]
        if type(parent) is not str or parent != expected_parent:
            raise ValueError(
                f"node_parent_binding_mismatch:{key}:"
                f"expected={expected_parent}:actual={parent}"
            )
        value = node["latent_contribution"]
        if isinstance(value, (bool, np.bool_)):
            raise ValueError(f"contribution_must_be_numeric_not_bool:{key}")
        if not isinstance(value, numbers.Real):
            raise ValueError(f"contribution_must_be_numeric_not_bool:{key}")
        contribution = float(value)
        if not math.isfinite(contribution):
            raise ValueError(f"contribution_must_be_finite:{key}")
        contributions[parent].append(contribution)
        raw_values.append(contribution)

    rolled: list[dict[str, Any]] = []
    for row in authoritative_catalog:
        key = str(row["key"])
        rolled.append(
            {
                **row,
                "latent_contribution": math.fsum(contributions[key]),
            }
        )
    if len(rolled) != 51:
        raise ValueError(f"rollup_output_count_invalid:{len(rolled)}")
    raw_total = math.fsum(raw_values)
    rolled_total = math.fsum(
        float(row["latent_contribution"]) for row in rolled
    )
    if not math.isclose(raw_total, rolled_total, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(
            f"rollup_conservation_failed:raw={raw_total}:rolled={rolled_total}"
        )
    return rolled
