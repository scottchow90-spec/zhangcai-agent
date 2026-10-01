from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import importlib.util
import json
import math
import re
import struct
from collections import Counter
from datetime import datetime, time as clock_time
from pathlib import Path
from typing import Any, Iterable


FRESHNESS_GATE = Path(__file__).resolve().with_name("nana_market_data.py")
DAY_RECORD = struct.Struct("<IIIIIfII")
MIN_TARGET_FILES = 4000
MIN_TARGET_COVERAGE_RATIO = 0.80
FUTURE_TOLERANCE_SECONDS = 120
ACTIVE_MAX_AGE_SECONDS = 600
MIDDAY_MAX_AGE_SECONDS = 7200


def normalize_trade_date(value: object) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits if re.fullmatch(r"20\d{6}", digits) else ""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def bind_quote_json_file(
    path: Path, caller_payload: dict[str, Any] | None = None
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    resolved = path.resolve()
    errors: list[str] = []
    binding: dict[str, Any] = {
        "schema": "nana-quote-file-binding/v1",
        "status": "BLOCKED",
        "path": str(resolved),
        "size_bytes": None,
        "file_sha256": None,
        "payload_sha256": None,
        "quotes_declared_sha256": None,
        "quotes_actual_sha256": None,
        "payload_matches_caller": False,
        "trade_date": "",
        "quote_record_count": 0,
        "errors": errors,
    }
    try:
        raw = resolved.read_bytes()
    except OSError as exc:
        errors.append(f"quote_file_unreadable:{type(exc).__name__}:{exc}")
        return None, binding
    binding["size_bytes"] = len(raw)
    binding["file_sha256"] = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8-sig", errors="strict")
        payload = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"quote_file_parse_failed:{type(exc).__name__}:{exc}")
        return None, binding
    if not isinstance(payload, dict):
        errors.append("quote_file_root_not_object")
        return None, binding
    payload_sha = canonical_sha256(payload)
    binding["payload_sha256"] = payload_sha
    if caller_payload is None:
        binding["payload_matches_caller"] = True
    elif not isinstance(caller_payload, dict):
        errors.append("quote_caller_payload_not_object")
    elif canonical_sha256(caller_payload) != payload_sha:
        errors.append("quote_caller_payload_disk_mismatch")
    else:
        binding["payload_matches_caller"] = True
    trade_date = normalize_trade_date(payload.get("trade_date"))
    binding["trade_date"] = trade_date
    if not trade_date:
        errors.append("quote_file_trade_date_missing_or_invalid")
    quotes = payload.get("quotes")
    if not isinstance(quotes, dict):
        errors.append("quote_file_quote_map_missing_or_invalid")
        quotes = {}
    binding["quote_record_count"] = len(quotes)
    declared = payload.get("quotes_sha256")
    binding["quotes_declared_sha256"] = declared
    actual = canonical_sha256(quotes)
    binding["quotes_actual_sha256"] = actual
    if not isinstance(declared, str) or not re.fullmatch(r"[0-9a-f]{64}", declared):
        errors.append("quotes_sha256_missing_or_invalid")
    elif declared != actual:
        errors.append(f"quotes_sha256_mismatch:{declared}!={actual}")
    binding["status"] = "PASS" if not errors else "BLOCKED"
    return payload, binding


def _load_freshness_gate() -> Any:
    if not FRESHNESS_GATE.is_file():
        raise RuntimeError(f"freshness_gate_missing:{FRESHNESS_GATE}")
    spec = importlib.util.spec_from_file_location("nana_stock_freshness_gate", FRESHNESS_GATE)
    if spec is None or spec.loader is None:
        raise RuntimeError("freshness_gate_loader_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inspect_local_universe(
    universe: Iterable[tuple[str, str, str, Path]],
) -> dict[str, Any]:
    rows = sorted(universe, key=lambda item: (item[0], item[1], str(item[3])))
    counts: Counter[str] = Counter()
    entries: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    read_errors = 0
    for market, code, _name, path in rows:
        try:
            stat = path.stat()
            if stat.st_size < DAY_RECORD.size or stat.st_size % DAY_RECORD.size:
                read_errors += 1
                continue
            with path.open("rb") as handle:
                handle.seek(-DAY_RECORD.size, 2)
                raw = handle.read(DAY_RECORD.size)
            trade_date = normalize_trade_date(DAY_RECORD.unpack(raw)[0])
            if not trade_date:
                read_errors += 1
                continue
            counts[trade_date] += 1
            entry = {
                "symbol": f"{code}.{market}",
                "trade_date": trade_date,
                "mtime_ns": stat.st_mtime_ns,
                "size_bytes": stat.st_size,
                "last_record_sha256": hashlib.sha256(raw).hexdigest(),
            }
            entries.append(entry)
            digest.update(
                (
                    f"{entry['symbol']}\0{trade_date}\0{stat.st_size}\0"
                    f"{stat.st_mtime_ns}\0{entry['last_record_sha256']}\n"
                ).encode("utf-8")
            )
        except (OSError, struct.error):
            read_errors += 1
    universe_count = len(rows)
    coverage_floor = max(
        MIN_TARGET_FILES, math.ceil(universe_count * MIN_TARGET_COVERAGE_RATIO)
    )
    sufficiently_covered = [
        value for value, count in counts.items() if count >= coverage_floor
    ]
    latest = max(sufficiently_covered) if sufficiently_covered else ""
    return {
        "universe_files": universe_count,
        "readable_last_records": len(entries),
        "read_errors": read_errors,
        "required_target_coverage": coverage_floor,
        "latest_sufficiently_covered_trade_date": latest,
        "date_distribution_top10": counts.most_common(10),
        "last_record_manifest_sha256": digest.hexdigest(),
        "_entries": entries,
    }


def _parse_checked_at(snapshot: dict[str, Any]) -> datetime:
    value = str(snapshot.get("checked_at") or "")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed


def _local_route_evidence(
    local_profile: dict[str, Any], snapshot: dict[str, Any], live_date: str
) -> dict[str, Any]:
    entries = local_profile.get("_entries") or []
    required = int(local_profile.get("required_target_coverage") or MIN_TARGET_FILES)
    target_entries = [item for item in entries if item.get("trade_date") == live_date]
    result = {
        "status": "BLOCKED",
        "target_record_count": len(target_entries),
        "required_target_coverage": required,
        "recency_qualified_count": 0,
        "recency_requirement": "not_evaluated",
        "errors": [],
    }
    errors = result["errors"]
    if local_profile.get("latest_sufficiently_covered_trade_date") != live_date:
        errors.append(
            "stale_local_trade_date:"
            f"{local_profile.get('latest_sufficiently_covered_trade_date')}!={live_date}"
        )
    if len(target_entries) < required:
        errors.append(f"local_target_coverage_insufficient:{len(target_entries)}<{required}")
    try:
        checked_at = _parse_checked_at(snapshot)
    except (TypeError, ValueError) as exc:
        errors.append(f"market_checked_at_invalid:{type(exc).__name__}:{exc}")
        return result
    phase = str(snapshot.get("market_phase") or "")
    qualified = len(target_entries)
    if phase in {"active", "preopen_with_current_data"}:
        result["recency_requirement"] = f"mtime_age<={ACTIVE_MAX_AGE_SECONDS}s"
        qualified = sum(
            -FUTURE_TOLERANCE_SECONDS
            <= (checked_at - datetime.fromtimestamp(item["mtime_ns"] / 1_000_000_000, tz=checked_at.tzinfo)).total_seconds()
            <= ACTIVE_MAX_AGE_SECONDS
            for item in target_entries
        )
    elif phase == "midday_pause":
        result["recency_requirement"] = f"mtime_age<={MIDDAY_MAX_AGE_SECONDS}s"
        qualified = sum(
            -FUTURE_TOLERANCE_SECONDS
            <= (checked_at - datetime.fromtimestamp(item["mtime_ns"] / 1_000_000_000, tz=checked_at.tzinfo)).total_seconds()
            <= MIDDAY_MAX_AGE_SECONDS
            for item in target_entries
        )
    elif phase == "postclose":
        result["recency_requirement"] = "mtime_at_or_after_market_close"
        close_boundary = datetime.combine(
            checked_at.date(), clock_time(15, 0), tzinfo=checked_at.tzinfo
        )
        qualified = sum(
            datetime.fromtimestamp(item["mtime_ns"] / 1_000_000_000, tz=checked_at.tzinfo)
            >= close_boundary
            for item in target_entries
        )
    elif phase == "off_session":
        result["recency_requirement"] = "latest_trade_date_record"
    else:
        errors.append(f"market_phase_unsupported:{phase}")
        qualified = 0
    result["recency_qualified_count"] = qualified
    if qualified < required:
        errors.append(f"local_recency_coverage_insufficient:{qualified}<{required}")
    result["status"] = "PASS" if not errors else "BLOCKED"
    return result


def _quote_route_evidence(
    quote_payload: dict[str, Any],
    quote_validation: dict[str, Any] | None,
    quote_file_binding: dict[str, Any] | None,
    universe_symbols: set[str],
    required: int,
) -> dict[str, Any]:
    errors: list[str] = []
    validation = quote_validation or {
        "status": "BLOCKED",
        "errors": ["quote_evidence_not_validated"],
    }
    if validation.get("status") != "PASS":
        errors.extend(str(item) for item in validation.get("errors") or [])
        if not validation.get("errors"):
            errors.append("quote_evidence_validation_failed")
    binding = quote_file_binding or {
        "status": "BLOCKED",
        "errors": ["quote_file_binding_missing"],
    }
    if binding.get("status") != "PASS":
        errors.extend(str(item) for item in binding.get("errors") or [])
        if not binding.get("errors"):
            errors.append("quote_file_binding_failed")
    quotes = quote_payload.get("quotes") if isinstance(quote_payload, dict) else None
    if not isinstance(quotes, dict):
        quotes = {}
        errors.append("quote_map_missing_or_invalid")
    required_fields = ("open", "high", "low", "close", "amount", "volume", "preclose")
    valid_symbols = 0
    for symbol, quote in quotes.items():
        if symbol not in universe_symbols or not isinstance(quote, dict):
            continue
        if all(quote.get(field) is not None for field in required_fields):
            valid_symbols += 1
    if valid_symbols < required:
        errors.append(f"quote_target_coverage_insufficient:{valid_symbols}<{required}")
    return {
        "status": "PASS" if not errors else "BLOCKED",
        "valid_quote_symbols": valid_symbols,
        "required_target_coverage": required,
        "evidence_validation": validation,
        "quote_file": binding,
        "errors": errors,
    }


def evaluate_freshness_inputs(
    *,
    requested_trade_date: str,
    local_profile: dict[str, Any],
    snapshot: dict[str, Any],
    quote_payload: dict[str, Any] | None = None,
    quote_validation: dict[str, Any] | None = None,
    quote_file_binding: dict[str, Any] | None = None,
    forced_errors: list[str] | None = None,
) -> dict[str, Any]:
    target_date = normalize_trade_date(requested_trade_date)
    live_date = normalize_trade_date(snapshot.get("latest_available_trade_date"))
    errors = list(forced_errors or [])
    if not target_date:
        errors.append("requested_trade_date_missing_or_invalid")
    if not live_date:
        errors.append("latest_market_trade_date_missing_or_invalid")
    if target_date and live_date and target_date != live_date:
        errors.append(f"stale_requested_trade_date:{target_date}!={live_date}")
    source_ids = {
        str(item.get("source_id") or "")
        for item in snapshot.get("sources") or []
        if isinstance(item, dict)
        and normalize_trade_date(item.get("trade_date")) == live_date
    }
    source_ids.discard("")
    if len(source_ids) < 2:
        errors.append(f"independent_market_sources_insufficient:{len(source_ids)}<2")

    local_route = _local_route_evidence(local_profile, snapshot, live_date)
    quote_route: dict[str, Any] | None = None
    selected_route = ""
    if quote_payload is not None:
        quote_date = normalize_trade_date(quote_payload.get("trade_date"))
        if quote_date != live_date:
            errors.append(f"stale_quote_trade_date:{quote_date}!={live_date}")
        universe_symbols = {
            str(item.get("symbol")) for item in local_profile.get("_entries") or []
        }
        quote_route = _quote_route_evidence(
            quote_payload,
            quote_validation,
            quote_file_binding,
            universe_symbols,
            int(local_profile.get("required_target_coverage") or MIN_TARGET_FILES),
        )
        if quote_route["status"] != "PASS":
            errors.extend(quote_route["errors"])
        elif not errors:
            selected_route = "validated_quote_append"
    elif local_route["status"] == "PASS" and not errors:
        selected_route = "local_day"
    if not selected_route:
        errors.append("no_fresh_full_market_data_route")

    public_local = {key: value for key, value in local_profile.items() if key != "_entries"}
    result = {
        "schema": "nana-selector-freshness-gate/v3",
        "status": "PASS" if not errors else "BLOCKED",
        "reason": None if not errors else "FRESHNESS_GATE_BLOCKED",
        "checked_at": snapshot.get("checked_at"),
        "requested_trade_date": target_date,
        "latest_market_trade_date": live_date,
        "market_phase": snapshot.get("market_phase"),
        "independent_market_sources": sorted(source_ids),
        "selected_data_route": selected_route or None,
        "local_data": public_local,
        "local_route": local_route,
        "quote_route": quote_route,
        "quote_file": quote_file_binding if quote_payload is not None else None,
        "quote_json_sha256": (
            quote_file_binding.get("file_sha256")
            if isinstance(quote_file_binding, dict)
            else None
        ),
        "market_snapshot_sha256": canonical_sha256(snapshot),
        "market_snapshot": snapshot,
        "errors": list(dict.fromkeys(errors)),
    }
    return result


def build_freshness_guard(
    *,
    universe: list[tuple[str, str, str, Path]],
    requested_trade_date: str,
    quote_payload: dict[str, Any] | None = None,
    quote_json_path: Path | None = None,
    forced_errors: list[str] | None = None,
) -> dict[str, Any]:
    local_profile = inspect_local_universe(universe)
    target_date = normalize_trade_date(requested_trade_date)
    if not target_date:
        target_date = str(local_profile.get("latest_sufficiently_covered_trade_date") or "")
    quote_file_binding: dict[str, Any] | None = None
    if quote_payload is not None or quote_json_path is not None:
        if quote_json_path is None:
            quote_file_binding = {
                "schema": "nana-quote-file-binding/v1",
                "status": "BLOCKED",
                "path": None,
                "errors": ["quote_json_path_missing"],
            }
        else:
            _disk_payload, quote_file_binding = bind_quote_json_file(
                quote_json_path, quote_payload
            )
    try:
        module = _load_freshness_gate()
        snapshot = module.resolve_market_snapshot()
        quote_validation = (
            module.validate_data_evidence(quote_payload, snapshot)
            if quote_payload is not None
            else None
        )
        return evaluate_freshness_inputs(
            requested_trade_date=target_date,
            local_profile=local_profile,
            snapshot=snapshot,
            quote_payload=quote_payload,
            quote_validation=quote_validation,
            quote_file_binding=quote_file_binding,
            forced_errors=forced_errors,
        )
    except Exception as exc:
        public_local = {
            key: value for key, value in local_profile.items() if key != "_entries"
        }
        return {
            "schema": "nana-selector-freshness-gate/v3",
            "status": "BLOCKED",
            "reason": "MARKET_FRESHNESS_UNVERIFIED",
            "requested_trade_date": target_date,
            "local_data": public_local,
            "quote_file": quote_file_binding,
            "quote_json_sha256": (
                quote_file_binding.get("file_sha256")
                if isinstance(quote_file_binding, dict)
                else None
            ),
            "errors": [
                *(forced_errors or []),
                f"market_freshness_unavailable:{type(exc).__name__}:{exc}",
            ],
        }


def selftest() -> dict[str, Any]:
    snapshot = {
        "status": "PASS",
        "checked_at": "2026-07-27T16:00:00+08:00",
        "latest_available_trade_date": "2026-07-27",
        "market_phase": "off_session",
        "sources": [
            {"source_id": "tencent", "trade_date": "2026-07-27"},
            {"source_id": "sina", "trade_date": "2026-07-27"},
        ],
    }
    entries = [
        {
            "symbol": f"{index:06d}.SH",
            "trade_date": "20260727",
            "mtime_ns": 0,
            "size_bytes": DAY_RECORD.size,
            "last_record_sha256": "0" * 64,
        }
        for index in range(4000)
    ]
    current_profile = {
        "universe_files": 4000,
        "readable_last_records": 4000,
        "read_errors": 0,
        "required_target_coverage": 4000,
        "latest_sufficiently_covered_trade_date": "20260727",
        "date_distribution_top10": [["20260727", 4000]],
        "last_record_manifest_sha256": "0" * 64,
        "_entries": entries,
    }
    current = evaluate_freshness_inputs(
        requested_trade_date="20260727",
        local_profile=current_profile,
        snapshot=snapshot,
    )
    stale_request = evaluate_freshness_inputs(
        requested_trade_date="20260724",
        local_profile=current_profile,
        snapshot=snapshot,
    )
    stale_profile = dict(current_profile)
    stale_profile["latest_sufficiently_covered_trade_date"] = "20260724"
    stale_profile["_entries"] = [dict(item, trade_date="20260724") for item in entries]
    stale_local = evaluate_freshness_inputs(
        requested_trade_date="20260727",
        local_profile=stale_profile,
        snapshot=snapshot,
    )
    passed = (
        current["status"] == "PASS"
        and stale_request["status"] == "BLOCKED"
        and stale_local["status"] == "BLOCKED"
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "current_case": current["status"],
        "stale_request_case": stale_request["status"],
        "stale_local_case": stale_local["status"],
    }
