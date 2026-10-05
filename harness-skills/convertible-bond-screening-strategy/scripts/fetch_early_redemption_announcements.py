#!/usr/bin/env python3
"""Build a fail-closed CNINFO early-redemption snapshot for convertible bonds."""

from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import concurrent.futures
import datetime as dt
import email.utils
import hashlib
import http.cookiejar
import importlib.util
import io
import json
import math
import os
import random
import re
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from runtime_utils import canonicalize_business_payload


SCHEMA = "CONVERTIBLE-BOND-EARLY-REDEMPTION-SNAPSHOT-1"
CNINFO_STOCK_URL = "https://www.cninfo.com.cn/new/data/szse_stock.json"
CNINFO_QUERY_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_SEARCH_URL = "https://www.cninfo.com.cn/new/fulltextSearch?keyWord=%E8%B5%8E%E5%9B%9E"
CATEGORY = "category_kzzq_szsh"
KEYWORD = "赎回"
SHANGHAI = ZoneInfo("Asia/Shanghai")
SCRIPT_DIR = Path(__file__).resolve().parent
PUBLIC_READONLY_SNAPSHOT_DIR_ENV = "CODEX_PUBLIC_READONLY_SNAPSHOT_DIR"
SHARED_SNAPSHOT_RELATIVE_PATH = (
    Path("convertible-bond-screening-strategy")
    / "early_redemption_announcements.json"
)

MIN_REQUEST_INTERVAL_SECONDS = 0.8
REQUEST_INTERVAL_JITTER_SECONDS = 0.4
HTTP_403_COOLDOWN_SECONDS = 30.0
HTTP_429_COOLDOWN_SECONDS = 10.0
MAX_SERVER_COOLDOWN_SECONDS = 120.0
CONSECUTIVE_403_CIRCUIT_THRESHOLD = 2
HTTP_ERROR_BODY_SAMPLE_BYTES = 512
HTTP_ERROR_BODY_PREVIEW_CHARS = 240
DIAGNOSTIC_RESPONSE_HEADERS = (
    "Content-Type",
    "Date",
    "Retry-After",
    "Server",
    "Via",
    "X-Cache",
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset",
)

NON_EXCLUSION_PHRASES = ("预计", "可能", "是否满足", "即将触发", "不提前", "不行使", "暂不")
EXCLUSION_PHRASES = (
    "决定行使",
    "提前赎回",
    "实施赎回",
    "赎回暨摘牌",
    "停止交易",
    "停止转股",
    "最后交易日",
    "赎回登记日",
    "赎回结果",
    "摘牌",
)
HARD_CONFLICT_PHRASES = tuple(item for item in EXCLUSION_PHRASES if item != "提前赎回")
QUOTE_AND_SPACE_RE = re.compile(r"[\s\"'`‘’“”《》「」『』]+", re.UNICODE)


class SnapshotError(RuntimeError):
    def __init__(self, message: str, diagnostics: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics or []


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        canonicalize_business_payload(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_meta(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "size": len(raw), "sha256": _sha256_bytes(raw)}


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonicalize_business_payload(payload)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _parse_cutoff(value: str) -> tuple[str, dt.date, dt.datetime]:
    text = value.strip()
    parsed = None
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            parsed = dt.datetime.strptime(text, fmt).date()
            break
        except ValueError:
            continue
    if parsed is None:
        raise SnapshotError("cutoff must be YYYYMMDD or YYYY-MM-DD")
    as_of = dt.datetime.combine(parsed, dt.time(23, 59, 59), tzinfo=SHANGHAI)
    return parsed.strftime("%Y%m%d"), parsed, as_of


def _normalize_title(value: Any) -> str:
    return QUOTE_AND_SPACE_RE.sub("", str(value or ""))


def _classify_title(title: str) -> tuple[str, list[str]]:
    normalized = _normalize_title(title)
    non_exclusion = [item for item in NON_EXCLUSION_PHRASES if item in normalized]
    exclusions = [item for item in EXCLUSION_PHRASES if item in normalized]
    hard_conflicts = [item for item in HARD_CONFLICT_PHRASES if item in normalized]
    if non_exclusion and hard_conflicts:
        return "CONFLICT", sorted(set(non_exclusion + hard_conflicts))
    if non_exclusion:
        return "NON_EXCLUSION", non_exclusion
    if exclusions:
        return "EXCLUSION", exclusions
    return "AMBIGUOUS", []


def _derive_market(code: str, *, underlying: bool) -> str:
    if underlying:
        if code.startswith(("5", "6", "9")):
            return "SH"
        if code.startswith(("4", "8")):
            return "BJ"
        return "SZ"
    return "SH" if code.startswith("11") else "SZ"


def _alias_value(row: dict[str, Any], aliases: tuple[str, ...]) -> tuple[str, list[str]]:
    values = sorted({str(row.get(key, "")).strip() for key in aliases if str(row.get(key, "")).strip()})
    if not values:
        return "", []
    if len(values) > 1:
        return values[0], [f"ambiguous_alias:{'/'.join(aliases)}:{'|'.join(values)}"]
    return values[0], []


def _normalize_bond(row: dict[str, Any], index: int) -> dict[str, Any]:
    symbol, errors = _alias_value(row, ("symbol",))
    bond_code, more = _alias_value(row, ("bond_code", "code"))
    errors.extend(more)
    if not bond_code and re.fullmatch(r"\d{6}\.(?:SH|SZ)", symbol.upper()):
        bond_code = symbol[:6]
    if not symbol and re.fullmatch(r"\d{6}", bond_code):
        symbol = f"{bond_code}.{_derive_market(bond_code, underlying=False)}"
    symbol = symbol.upper()
    if not re.fullmatch(r"\d{6}\.(?:SH|SZ)", symbol):
        errors.append("invalid_or_missing_symbol")
    elif bond_code and symbol[:6] != bond_code:
        errors.append("symbol_bond_code_conflict")
    if not re.fullmatch(r"\d{6}", bond_code):
        errors.append("invalid_or_missing_bond_code")

    bond_name, more = _alias_value(row, ("bond_name", "name"))
    errors.extend(more)
    if not bond_name or bond_name == bond_code:
        errors.append("invalid_or_missing_bond_name")

    underlying_code, more = _alias_value(row, ("underlying_code", "underlying"))
    errors.extend(more)
    underlying_symbol, more = _alias_value(row, ("underlying_symbol",))
    errors.extend(more)
    if not underlying_code and re.fullmatch(r"\d{6}\.(?:SH|SZ|BJ)", underlying_symbol.upper()):
        underlying_code = underlying_symbol[:6]
    if not underlying_symbol and re.fullmatch(r"\d{6}", underlying_code):
        underlying_symbol = f"{underlying_code}.{_derive_market(underlying_code, underlying=True)}"
    underlying_symbol = underlying_symbol.upper()
    if not re.fullmatch(r"\d{6}", underlying_code):
        errors.append("invalid_or_missing_underlying_code")
    if not re.fullmatch(r"\d{6}\.(?:SH|SZ|BJ)", underlying_symbol):
        errors.append("invalid_or_missing_underlying_symbol")
    elif underlying_code and underlying_symbol[:6] != underlying_code:
        errors.append("underlying_symbol_code_conflict")

    listing_raw, more = _alias_value(
        row,
        ("listing_date", "list_date", "listed_date", "bond_listing_date", "listingDate"),
    )
    errors.extend(more)
    listing_date = "1990-01-01"
    listing_source = "fallback_1990-01-01"
    if listing_raw:
        for fmt in ("%Y%m%d", "%Y-%m-%d"):
            try:
                listing_date = dt.datetime.strptime(listing_raw, fmt).date().isoformat()
                listing_source = "universe"
                break
            except ValueError:
                continue
        else:
            errors.append("invalid_listing_date")

    return {
        "_index": index,
        "symbol": symbol or f"INVALID-{index:06d}",
        "bond_code": bond_code,
        "bond_name": bond_name,
        "underlying_code": underlying_code,
        "underlying_symbol": underlying_symbol,
        "listing_date": listing_date,
        "listing_date_source": listing_source,
        "load_errors": sorted(set(errors)),
    }


def _load_module_universe(cutoff: str) -> tuple[list[dict[str, Any]], dict[str, Any], bool]:
    module_path = SCRIPT_DIR / "run_convertible_bond_screening.py"
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        spec = importlib.util.spec_from_file_location("_cb_screening_universe", module_path)
        if spec is None or spec.loader is None:
            raise SnapshotError(f"cannot load universe module: {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        bonds, _tnf, diagnostics = module.parse_bonds(cutoff)
    finally:
        if sys.path and sys.path[0] == str(SCRIPT_DIR):
            sys.path.pop(0)
    source_meta = _file_meta(module.BOND_SOURCE)
    source_meta.update({
        "mode": "local_parse_bonds",
        "parser": str(module_path.resolve()),
        "diagnostics": diagnostics,
    })
    complete = (
        not diagnostics.get("duplicate_symbols")
        and not diagnostics.get("source_current_candidate_missing_tnf")
        and int(diagnostics.get("invalid_or_unresolved_source_rows") or 0) == 0
    )
    return bonds, source_meta, bool(complete)


def _records_from_json(payload: Any) -> tuple[list[dict[str, Any]], int | None]:
    if isinstance(payload, list):
        return payload, None
    if not isinstance(payload, dict):
        raise SnapshotError("universe JSON root must be an object or array")
    if isinstance(payload.get("all_results"), list):
        records = list(payload["all_results"])
        excluded = payload.get("hard_excluded_results", [])
        if excluded is not None and not isinstance(excluded, list):
            raise SnapshotError("hard_excluded_results must be an array")
        records.extend(excluded or [])
        declared = payload.get("universe_count")
        return records, int(declared) if isinstance(declared, int) else None
    pools = [key for key in ("master_records", "bonds", "records") if isinstance(payload.get(key), list)]
    if len(pools) != 1:
        raise SnapshotError("universe JSON must contain exactly one recognized record array")
    declared = payload.get("universe_count")
    return list(payload[pools[0]]), int(declared) if isinstance(declared, int) else None


def _load_universe(path: Path | None, cutoff: str) -> tuple[list[dict[str, Any]], dict[str, Any], bool]:
    if path is None:
        raw, source, complete = _load_module_universe(cutoff)
    else:
        raw_bytes = path.resolve().read_bytes()
        try:
            payload = json.loads(raw_bytes.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SnapshotError(f"universe JSON decode failed: {exc}") from exc
        raw, declared = _records_from_json(payload)
        source = {
            "mode": "json_snapshot",
            "path": str(path.resolve()),
            "size": len(raw_bytes),
            "sha256": _sha256_bytes(raw_bytes),
            "declared_universe_count": declared,
        }
        complete = declared is None or declared == len(raw)
    if not raw:
        raise SnapshotError("universe is empty")
    if not all(isinstance(item, dict) for item in raw):
        raise SnapshotError("every universe record must be an object")
    bonds = [_normalize_bond(item, index) for index, item in enumerate(raw)]
    symbols = [item["symbol"] for item in bonds]
    duplicates = sorted({item for item in symbols if symbols.count(item) > 1})
    if duplicates:
        for item in bonds:
            if item["symbol"] in duplicates:
                item["load_errors"] = sorted(set(item["load_errors"] + ["duplicate_symbol_in_universe"]))
        complete = False
    source["record_count"] = len(bonds)
    source["normalized_records_sha256"] = _sha256_bytes(_canonical_bytes(bonds))
    return sorted(bonds, key=lambda item: (item["symbol"], item["_index"])), source, bool(complete)


def _load_shared_readonly_snapshot(
    path: Path,
    *,
    bonds: list[dict[str, Any]],
    run_id: str,
    cutoff: str,
    as_of: dt.datetime,
) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        source_bytes = resolved.read_bytes()
        payload = json.loads(source_bytes.decode("utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SnapshotError(
            f"shared readonly snapshot cannot be read: {type(exc).__name__}:{exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise SnapshotError("shared readonly snapshot root must be an object")

    records = payload.get("records")
    coverage = payload.get("coverage")
    source = payload.get("source")
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise SnapshotError("shared readonly snapshot records are invalid")
    if not isinstance(coverage, dict) or not isinstance(source, dict):
        raise SnapshotError("shared readonly snapshot metadata is invalid")

    statuses = [str(item.get("early_redemption_status") or "") for item in records]
    expected_identity_fields = (
        "symbol",
        "bond_code",
        "bond_name",
        "underlying_code",
        "underlying_symbol",
        "listing_date",
        "listing_date_source",
    )
    expected_identities = sorted(
        tuple(str(bond.get(field) or "") for field in expected_identity_fields)
        for bond in bonds
    )
    actual_identities = sorted(
        tuple(str(record.get(field) or "") for field in expected_identity_fields)
        for record in records
    )
    calculated_records_sha256 = _sha256_bytes(_canonical_bytes(records))
    errors: list[str] = []
    if payload.get("schema") != SCHEMA:
        errors.append("schema_mismatch")
    if payload.get("status") != "PASS":
        errors.append("status_not_pass")
    if payload.get("cutoff") != cutoff or payload.get("as_of") != as_of.isoformat():
        errors.append("cutoff_mismatch")
    if source.get("provider") != "CNINFO":
        errors.append("provider_mismatch")
    if payload.get("current_universe_complete") is not True:
        errors.append("universe_not_complete")
    if payload.get("universe_count") != len(bonds) or payload.get("record_count") != len(records):
        errors.append("record_count_mismatch")
    if len(records) != len(bonds) or actual_identities != expected_identities:
        errors.append("universe_identity_mismatch")
    if payload.get("records_sha256") != calculated_records_sha256:
        errors.append("records_sha256_mismatch")
    if any(
        status
        not in {"ANNOUNCED_EARLY_REDEMPTION", "NO_MATCH_AS_OF_CUTOFF"}
        for status in statuses
    ):
        errors.append("record_status_invalid")
    if payload.get("announced_count") != statuses.count("ANNOUNCED_EARLY_REDEMPTION"):
        errors.append("announced_count_mismatch")
    if payload.get("no_match_count") != statuses.count("NO_MATCH_AS_OF_CUTOFF"):
        errors.append("no_match_count_mismatch")
    if payload.get("unverified_count") != statuses.count("UNVERIFIED") or "UNVERIFIED" in statuses:
        errors.append("unverified_records_present")
    if payload.get("errors") != []:
        errors.append("snapshot_errors_present")
    if (
        coverage.get("complete") is not True
        or coverage.get("requested_count") != len(bonds)
        or coverage.get("completed_count") != len(bonds)
        or any(record.get("query_complete") is not True for record in records)
    ):
        errors.append("coverage_incomplete")
    try:
        stable = resolved.read_bytes() == source_bytes
    except OSError as exc:
        raise SnapshotError(
            f"shared readonly snapshot stability read failed: {type(exc).__name__}:{exc}"
        ) from exc
    if not stable:
        errors.append("snapshot_changed_during_read")
    if errors:
        raise SnapshotError("shared readonly snapshot invalid: " + ",".join(errors))

    rebound = dict(payload)
    rebound["run_id"] = run_id
    rebound["source"] = {
        **source,
        "input_mode": "shared_readonly_snapshot",
        "input_snapshot": {
            "path": str(resolved),
            "size": len(source_bytes),
            "sha256": _sha256_bytes(source_bytes),
            "source_run_id": str(payload.get("run_id") or ""),
        },
    }
    return rebound


def _shared_readonly_snapshot_path() -> Path | None:
    raw_root = str(os.environ.get(PUBLIC_READONLY_SNAPSHOT_DIR_ENV) or "").strip()
    if not raw_root:
        return None
    root = Path(raw_root).resolve()
    candidate = (root / SHARED_SNAPSHOT_RELATIVE_PATH).resolve()
    if not candidate.is_relative_to(root):
        raise SnapshotError("shared readonly snapshot escapes configured root")
    if candidate.exists() and not candidate.is_file():
        raise SnapshotError("shared readonly snapshot path is not a file")
    return candidate if candidate.is_file() else None


def _retry_after_seconds(headers: Any) -> float | None:
    if headers is None:
        return None
    value = headers.get("Retry-After")
    if value is None:
        return None
    text = str(value).strip()
    try:
        return max(0.0, float(text))
    except ValueError:
        pass
    try:
        parsed = email.utils.parsedate_to_datetime(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return max(0.0, (parsed - dt.datetime.now(dt.timezone.utc)).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None


def _http_error_diagnostic(exc: urllib.error.HTTPError, attempt: int) -> dict[str, Any]:
    try:
        captured = exc.read(HTTP_ERROR_BODY_SAMPLE_BYTES + 1)
    except (OSError, ValueError):
        captured = b""
    truncated = len(captured) > HTTP_ERROR_BODY_SAMPLE_BYTES
    sample = captured[:HTTP_ERROR_BODY_SAMPLE_BYTES]
    try:
        preview = sample.decode("utf-8-sig")
    except UnicodeDecodeError:
        preview = sample.decode("utf-8", errors="replace")
    preview = re.sub(r"\s+", " ", preview).strip()[:HTTP_ERROR_BODY_PREVIEW_CHARS]
    response_headers: dict[str, str] = {}
    for name in DIAGNOSTIC_RESPONSE_HEADERS:
        if exc.headers is not None and exc.headers.get(name) is not None:
            response_headers[name] = str(exc.headers.get(name))[:240]
    diagnostic: dict[str, Any] = {
        "attempt": attempt,
        "http_status": int(exc.code),
        "reason": str(exc.reason)[:160],
        "response_headers": response_headers,
        "body_sample_size": len(sample),
        "body_sample_sha256": _sha256_bytes(sample),
        "body_sample_truncated": truncated,
    }
    retry_after = _retry_after_seconds(exc.headers)
    if retry_after is not None:
        diagnostic["retry_after_seconds"] = round(retry_after, 3)
    if preview:
        diagnostic["body_preview"] = preview
    return diagnostic


class JsonHttpClient:
    def __init__(
        self,
        timeout_seconds: float,
        retries: int,
        *,
        opener: Any | None = None,
        monotonic_fn: Callable[[], float] = time.monotonic,
        sleep_fn: Callable[[float], None] = time.sleep,
        uniform_fn: Callable[[float, float], float] = random.uniform,
        min_interval_seconds: float = MIN_REQUEST_INTERVAL_SECONDS,
        interval_jitter_seconds: float = REQUEST_INTERVAL_JITTER_SECONDS,
        forbidden_cooldown_seconds: float = HTTP_403_COOLDOWN_SECONDS,
        rate_limit_cooldown_seconds: float = HTTP_429_COOLDOWN_SECONDS,
        max_server_cooldown_seconds: float = MAX_SERVER_COOLDOWN_SECONDS,
        circuit_threshold: int = CONSECUTIVE_403_CIRCUIT_THRESHOLD,
    ) -> None:
        if retries < 0:
            raise ValueError("retries must be non-negative")
        if min_interval_seconds < 0 or interval_jitter_seconds < 0:
            raise ValueError("request intervals must be non-negative")
        if forbidden_cooldown_seconds < 0 or rate_limit_cooldown_seconds < 0:
            raise ValueError("cooldowns must be non-negative")
        if max_server_cooldown_seconds <= 0:
            raise ValueError("max_server_cooldown_seconds must be positive")
        if circuit_threshold < 2:
            raise ValueError("circuit_threshold must be at least 2")
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener = opener or urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._cookie_jar),
        )
        self._monotonic = monotonic_fn
        self._sleep = sleep_fn
        self._uniform = uniform_fn
        self._min_interval_seconds = min_interval_seconds
        self._interval_jitter_seconds = interval_jitter_seconds
        self._forbidden_cooldown_seconds = forbidden_cooldown_seconds
        self._rate_limit_cooldown_seconds = rate_limit_cooldown_seconds
        self._max_server_cooldown_seconds = max_server_cooldown_seconds
        self._circuit_threshold = circuit_threshold
        self._state_lock = threading.Lock()
        self._thread_state = threading.local()
        self._global_cooldown_until = 0.0
        self._consecutive_403 = 0
        self._circuit_open = False

    def _wait_for_request_slot(self) -> None:
        while True:
            now = self._monotonic()
            with self._state_lock:
                circuit_open = self._circuit_open
                consecutive_403 = self._consecutive_403
                global_cooldown_until = self._global_cooldown_until
            if circuit_open:
                raise self._circuit_error(consecutive_403)
            global_remaining = global_cooldown_until - now
            if global_remaining > 0:
                self._sleep(global_remaining)
                continue

            next_request_at = float(
                getattr(self._thread_state, "next_request_at", 0.0)
            )
            local_remaining = next_request_at - now
            if local_remaining > 0:
                self._sleep(local_remaining)
                continue

            started_at = self._monotonic()
            interval = self._min_interval_seconds + self._uniform(
                0.0,
                self._interval_jitter_seconds,
            )
            self._thread_state.next_request_at = started_at + interval

            with self._state_lock:
                circuit_open = self._circuit_open
                consecutive_403 = self._consecutive_403
                global_cooldown_until = self._global_cooldown_until
            if circuit_open:
                raise self._circuit_error(consecutive_403)
            global_remaining = global_cooldown_until - self._monotonic()
            if global_remaining > 0:
                self._sleep(global_remaining)
                continue
            return

    def _schedule_global_cooldown(self, seconds: float) -> float:
        bounded = min(max(0.0, seconds), self._max_server_cooldown_seconds)
        with self._state_lock:
            self._global_cooldown_until = max(
                self._global_cooldown_until,
                self._monotonic() + bounded,
            )
        return bounded

    def _circuit_error(self, consecutive_403: int | None = None) -> SnapshotError:
        if consecutive_403 is None:
            with self._state_lock:
                consecutive_403 = self._consecutive_403
        diagnostic = {
            "event": "circuit_open",
            "reason": "consecutive_HTTP_403",
            "consecutive_403": consecutive_403,
            "threshold": self._circuit_threshold,
        }
        return SnapshotError(
            f"circuit_open:consecutive_HTTP_403:{consecutive_403}",
            [diagnostic],
        )

    def _reset_consecutive_403_if_closed(self) -> None:
        with self._state_lock:
            if not self._circuit_open:
                self._consecutive_403 = 0

    def _record_forbidden(self, diagnostic: dict[str, Any]) -> bool:
        with self._state_lock:
            self._consecutive_403 += 1
            diagnostic["consecutive_403"] = self._consecutive_403
            if self._consecutive_403 >= self._circuit_threshold:
                self._circuit_open = True
                diagnostic["circuit_opened"] = True
            return self._circuit_open

    def _circuit_state(self) -> tuple[bool, int]:
        with self._state_lock:
            return self._circuit_open, self._consecutive_403

    def request_json(
        self,
        method: str,
        url: str,
        form: dict[str, str] | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        body = urllib.parse.urlencode(form).encode("utf-8") if form is not None else None
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": CNINFO_SEARCH_URL,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
            ),
        }
        if body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
            headers["Origin"] = "https://www.cninfo.com.cn"
            headers["X-Requested-With"] = "XMLHttpRequest"
        errors: list[str] = []
        diagnostics: list[dict[str, Any]] = []
        circuit_open, consecutive_403 = self._circuit_state()
        if circuit_open:
            raise self._circuit_error(consecutive_403)
        for attempt in range(1, self.retries + 2):
            try:
                self._wait_for_request_slot()
            except SnapshotError as exc:
                errors.append(
                    f"attempt_{attempt}:{type(exc).__name__}:{str(exc)[:240]}"
                )
                diagnostics.extend(exc.diagnostics)
                break

            request = urllib.request.Request(
                url,
                data=body,
                headers=headers,
                method=method,
            )
            try:
                with self._opener.open(
                    request,
                    timeout=self.timeout_seconds,
                ) as response:
                    raw = response.read()
                    status = int(getattr(response, "status", 200))
                self._reset_consecutive_403_if_closed()
                try:
                    payload = json.loads(raw.decode("utf-8-sig"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise SnapshotError(f"invalid JSON response: {exc}") from exc
                return payload, {
                    "attempts": attempt,
                    "http_status": status,
                    "response_size": len(raw),
                    "response_sha256": _sha256_bytes(raw),
                    "errors": errors,
                    "diagnostics": diagnostics,
                }
            except urllib.error.HTTPError as exc:
                code = int(exc.code)
                errors.append(f"attempt_{attempt}:HTTP_{code}")
                diagnostic = _http_error_diagnostic(exc, attempt)
                diagnostics.append(diagnostic)
                circuit_open = (
                    self._record_forbidden(diagnostic)
                    if code == 403
                    else False
                )
                if code != 403:
                    self._reset_consecutive_403_if_closed()
                retry_after = float(
                    diagnostic.get("retry_after_seconds", 0.0)
                )
                if code == 403:
                    cooldown = max(
                        self._forbidden_cooldown_seconds,
                        retry_after,
                    )
                    diagnostic["cooldown_seconds"] = (
                        self._schedule_global_cooldown(cooldown)
                    )
                elif code == 429:
                    cooldown = max(
                        self._rate_limit_cooldown_seconds,
                        retry_after,
                    )
                    diagnostic["cooldown_seconds"] = (
                        self._schedule_global_cooldown(cooldown)
                    )
                else:
                    cooldown = min(0.4 * (2 ** (attempt - 1)), 3.0)
                    diagnostic["cooldown_seconds"] = cooldown
                retryable = (
                    code in (403, 408, 429)
                    or 500 <= code <= 599
                )
                if circuit_open or not retryable or attempt > self.retries:
                    break
                if code not in (403, 429) and cooldown > 0:
                    self._sleep(cooldown)
            except (
                urllib.error.URLError,
                TimeoutError,
                OSError,
                SnapshotError,
            ) as exc:
                self._reset_consecutive_403_if_closed()
                errors.append(
                    f"attempt_{attempt}:{type(exc).__name__}:{str(exc)[:240]}"
                )
                if isinstance(exc, SnapshotError):
                    diagnostics.extend(exc.diagnostics)
                cooldown = min(0.4 * (2 ** (attempt - 1)), 3.0)
                if attempt > self.retries:
                    break
                if cooldown > 0:
                    self._sleep(cooldown)
        circuit_open, consecutive_403 = self._circuit_state()
        if circuit_open:
            diagnostics.append({
                "event": "circuit_open",
                "reason": "consecutive_HTTP_403",
                "consecutive_403": consecutive_403,
                "threshold": self._circuit_threshold,
            })
        raise SnapshotError("request failed: " + ";".join(errors), diagnostics)


def _stock_map(payload: Any) -> tuple[dict[str, str], list[str]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("stockList"), list):
        rows = payload["stockList"]
    else:
        raise SnapshotError("CNINFO stock map has an unsupported schema")
    mapping: dict[str, str] = {}
    conflicts: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        code = str(row.get("code") or row.get("secCode") or "").strip()
        org_id = str(row.get("orgId") or "").strip()
        if not re.fullmatch(r"\d{6}", code) or not org_id:
            continue
        if code in mapping and mapping[code] != org_id:
            conflicts.add(code)
        else:
            mapping[code] = org_id
    for code in conflicts:
        mapping.pop(code, None)
    if not mapping:
        raise SnapshotError("CNINFO stock map contains no usable code/orgId pairs")
    return mapping, sorted(conflicts)


def _bool_value(value: Any, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.lower() in ("true", "false"):
        return value.lower() == "true"
    raise SnapshotError(f"invalid {field} value")


def _announcement_time(value: Any) -> dt.datetime:
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        number = float(value)
        if number > 10_000_000_000:
            number /= 1000.0
        return dt.datetime.fromtimestamp(number, tz=dt.timezone.utc).astimezone(SHANGHAI)
    text = str(value or "").strip()
    if not text:
        raise SnapshotError("missing announcementTime")
    iso = text.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(iso)
    except ValueError:
        parsed = None
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y%m%d"):
            try:
                parsed = dt.datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            raise SnapshotError(f"invalid announcementTime:{text[:80]}")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=SHANGHAI)
    return parsed.astimezone(SHANGHAI)


def _announcement_url(item: dict[str, Any]) -> str:
    adjunct = str(item.get("adjunctUrl") or "").strip()
    if adjunct.startswith(("https://", "http://")):
        return adjunct
    if adjunct:
        return "https://static.cninfo.com.cn/" + adjunct.lstrip("/")
    return ""


def _detail_url(item: dict[str, Any], underlying_code: str, org_id: str) -> str:
    params = {
        "stockCode": underlying_code,
        "announcementId": str(item.get("announcementId") or ""),
        "orgId": org_id,
        "announcementTime": str(item.get("announcementTime") or ""),
    }
    return "https://www.cninfo.com.cn/new/disclosure/detail?" + urllib.parse.urlencode(params)


def _query_one(
    bond: dict[str, Any],
    org_id: str | None,
    cutoff_date: dt.date,
    as_of: dt.datetime,
    page_size: int,
    max_pages: int,
    client: Any,
) -> dict[str, Any]:
    base = {key: value for key, value in bond.items() if not key.startswith("_") and key != "load_errors"}
    errors = list(bond["load_errors"])
    request_diagnostics: list[dict[str, Any]] = []
    page_records: list[dict[str, Any]] = []
    announcements: list[dict[str, Any]] = []
    if not org_id:
        errors.append("missing_or_ambiguous_cninfo_org_id")
    if errors:
        return {
            **base,
            "org_id": org_id,
            "early_redemption_status": "UNVERIFIED",
            "query_complete": False,
            "pages_fetched": 0,
            "total_announcements": None,
            "announcements_fetched": 0,
            "exact_name_match_count": 0,
            "exclusion_match_count": 0,
            "non_exclusion_match_count": 0,
            "request_coverage": {"complete": False, "pages": []},
            "request_diagnostics": request_diagnostics,
            "announcements": [],
            "errors": sorted(set(errors)),
        }

    total_expected: int | None = None
    seen_ids: set[str] = set()
    seen_page_hashes: set[str] = set()
    page_num = 1
    complete = False
    while page_num <= max_pages:
        form = {
            "pageNum": str(page_num),
            "pageSize": str(page_size),
            "column": "szse",
            "tabName": "fulltext",
            "plate": "",
            "stock": f"{bond['underlying_code']},{org_id}",
            "searchkey": KEYWORD,
            "secid": "",
            "category": CATEGORY,
            "trade": "",
            "seDate": f"{bond['listing_date']}~{cutoff_date.isoformat()}",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "false",
        }
        try:
            payload, meta = client.request_json("POST", CNINFO_QUERY_URL, form)
            if not isinstance(payload, dict):
                raise SnapshotError("announcement response root is not an object")
            raw_total = payload.get("totalAnnouncement", payload.get("totalRecordNum"))
            if isinstance(raw_total, bool) or not isinstance(raw_total, (int, float, str)):
                raise SnapshotError("missing totalAnnouncement")
            try:
                current_total = int(raw_total)
            except (TypeError, ValueError) as exc:
                raise SnapshotError("invalid totalAnnouncement") from exc
            if current_total < 0:
                raise SnapshotError("negative totalAnnouncement")
            if total_expected is None:
                total_expected = current_total
            elif total_expected != current_total:
                raise SnapshotError("totalAnnouncement changed across pages")
            rows = payload.get("announcements")
            if rows is None and current_total == 0:
                rows = []
            if not isinstance(rows, list) or not all(isinstance(item, dict) for item in rows):
                raise SnapshotError("announcements is not an object array")
            has_more_source = "response"
            if "hasMore" in payload:
                has_more = _bool_value(payload["hasMore"], "hasMore")
            else:
                has_more = page_num * page_size < current_total
                has_more_source = "derived_from_total"
            page_hash = str(meta.get("response_sha256") or "")
            if not re.fullmatch(r"[0-9a-f]{64}", page_hash):
                raise SnapshotError("missing response SHA-256")
            if page_hash in seen_page_hashes:
                raise SnapshotError("repeated page response detected")
            seen_page_hashes.add(page_hash)

            page_ids: list[str] = []
            for raw_item in rows:
                announcement_id = str(raw_item.get("announcementId") or "").strip()
                title = str(raw_item.get("announcementTitle") or "").strip()
                sec_code = str(raw_item.get("secCode") or "").strip()
                if not announcement_id or not title or not re.fullmatch(r"\d{6}", sec_code):
                    raise SnapshotError("announcement missing id/title/exact secCode")
                if announcement_id in seen_ids:
                    raise SnapshotError(f"duplicate announcementId across pages:{announcement_id}")
                seen_ids.add(announcement_id)
                event_time = _announcement_time(raw_item.get("announcementTime"))
                if event_time > as_of:
                    raise SnapshotError(f"future announcement beyond cutoff:{announcement_id}")
                exact_name = _normalize_title(bond["bond_name"]) in _normalize_title(title)
                underlying_exact = sec_code == bond["underlying_code"]
                classification = "NOT_TARGET_BOND"
                markers: list[str] = []
                if exact_name and not underlying_exact:
                    classification = "MAPPING_CONFLICT"
                    errors.append(f"title_mapping_conflict:{announcement_id}")
                elif exact_name and underlying_exact:
                    classification, markers = _classify_title(title)
                    if classification == "AMBIGUOUS":
                        errors.append(f"ambiguous_redemption_title:{announcement_id}")
                    elif classification == "CONFLICT":
                        errors.append(f"conflicting_redemption_title:{announcement_id}")
                detail_url = _detail_url(raw_item, bond["underlying_code"], org_id)
                normalized = {
                    "announcement_id": announcement_id,
                    "announcement_time": event_time.isoformat(),
                    "title": title,
                    "sec_code": sec_code,
                    "url": _announcement_url(raw_item) or detail_url,
                    "source_url": detail_url,
                    "bond_name_exact": exact_name,
                    "underlying_code_exact": underlying_exact,
                    "classification": classification,
                    "matched_phrases": markers,
                }
                announcements.append(normalized)
                page_ids.append(announcement_id)
            page_records.append({
                "page_num": page_num,
                "page_size": page_size,
                "returned_count": len(rows),
                "total_announcements": current_total,
                "has_more": has_more,
                "has_more_source": has_more_source,
                "announcement_ids": sorted(page_ids),
                "request": {
                    "url": CNINFO_QUERY_URL,
                    "stock": form["stock"],
                    "category": CATEGORY,
                    "keyword": KEYWORD,
                    "date_range": form["seDate"],
                },
                **meta,
            })
            if not has_more:
                complete = True
                break
            page_num += 1
        except SnapshotError as exc:
            request_diagnostics.extend(exc.diagnostics)
            errors.append(f"page_{page_num}:{exc}")
            break

    if page_num > max_pages and not complete:
        errors.append("max_pages_exceeded")
    if total_expected is None:
        complete = False
        errors.append("total_announcement_unverified")
    elif complete:
        expected_pages = max(1, math.ceil(total_expected / page_size))
        if len(page_records) != expected_pages:
            complete = False
            errors.append(f"page_coverage_mismatch:{len(page_records)}!={expected_pages}")
        if len(announcements) != total_expected:
            complete = False
            errors.append(f"announcement_count_mismatch:{len(announcements)}!={total_expected}")

    announcements.sort(key=lambda item: (item["announcement_time"], item["announcement_id"], item["title"]))
    exact = [item for item in announcements if item["bond_name_exact"] and item["underlying_code_exact"]]
    exclusions = [item for item in exact if item["classification"] == "EXCLUSION"]
    non_exclusions = [item for item in exact if item["classification"] == "NON_EXCLUSION"]
    if errors or not complete:
        status = "UNVERIFIED"
    elif exclusions:
        status = "ANNOUNCED_EARLY_REDEMPTION"
    else:
        status = "NO_MATCH_AS_OF_CUTOFF"
    return {
        **base,
        "org_id": org_id,
        "early_redemption_status": status,
        "query_complete": bool(complete and not errors),
        "pages_fetched": len(page_records),
        "total_announcements": total_expected,
        "announcements_fetched": len(announcements),
        "exact_name_match_count": len(exact),
        "exclusion_match_count": len(exclusions),
        "non_exclusion_match_count": len(non_exclusions),
        "request_coverage": {"complete": bool(complete and not errors), "pages": page_records},
        "request_diagnostics": request_diagnostics,
        "announcements": announcements,
        "errors": sorted(set(errors)),
    }


def _unverified_record(bond: dict[str, Any], reason: str) -> dict[str, Any]:
    copy = dict(bond)
    copy["load_errors"] = sorted(set(copy.get("load_errors", []) + [reason]))
    return _query_one(copy, None, dt.date(1990, 1, 1), dt.datetime(1990, 1, 1, tzinfo=SHANGHAI), 30, 1, None)


def _build_snapshot(
    bonds: list[dict[str, Any]],
    universe_source: dict[str, Any],
    universe_complete: bool,
    run_id: str,
    cutoff: str,
    cutoff_date: dt.date,
    as_of: dt.datetime,
    client: Any,
    workers: int,
    page_size: int,
    max_pages: int,
) -> dict[str, Any]:
    top_errors: list[str] = []
    stock_meta: dict[str, Any] = {}
    try:
        stock_payload, stock_meta = client.request_json("GET", CNINFO_STOCK_URL)
        mapping, conflicts = _stock_map(stock_payload)
        if conflicts:
            top_errors.append("ambiguous_org_id_codes:" + ",".join(conflicts))
    except Exception as exc:
        mapping = {}
        conflicts = []
        if isinstance(exc, SnapshotError):
            stock_meta = {"errors": [str(exc)], "diagnostics": exc.diagnostics}
        top_errors.append(f"cninfo_stock_map_failed:{type(exc).__name__}:{str(exc)[:300]}")

    def work(bond: dict[str, Any]) -> dict[str, Any]:
        code = bond["underlying_code"]
        if not mapping:
            return _unverified_record(bond, "cninfo_stock_map_unavailable")
        reason = "ambiguous_cninfo_org_id" if code in conflicts else "missing_cninfo_org_id"
        org_id = mapping.get(code)
        if not org_id:
            copy = dict(bond)
            copy["load_errors"] = sorted(set(copy.get("load_errors", []) + [reason]))
            return _query_one(copy, None, cutoff_date, as_of, page_size, max_pages, client)
        return _query_one(bond, org_id, cutoff_date, as_of, page_size, max_pages, client)

    records: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(work, bond) for bond in bonds]
        for future in futures:
            try:
                records.append(future.result())
            except Exception as exc:
                index = len(records)
                records.append(_unverified_record(bonds[index], f"worker_failure:{type(exc).__name__}:{str(exc)[:240]}"))
    records.sort(key=lambda item: item["symbol"])
    for record in records:
        if record["early_redemption_status"] == "UNVERIFIED":
            top_errors.extend(f"{record['symbol']}:{error}" for error in record["errors"])
    statuses = [record["early_redemption_status"] for record in records]
    all_covered = len(records) == len(bonds) and all(record["query_complete"] for record in records)
    current_complete = bool(universe_complete and all_covered)
    status = "PASS" if current_complete and "UNVERIFIED" not in statuses else "BLOCKED"
    pages_fetched = sum(record["pages_fetched"] for record in records)
    announcements_fetched = sum(record["announcements_fetched"] for record in records)
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": status,
        "run_id": run_id,
        "cutoff": cutoff,
        "as_of": as_of.isoformat(),
        "generated_at": dt.datetime.now(SHANGHAI).isoformat(),
        "source": {
            "provider": "CNINFO",
            "org_id_endpoint": CNINFO_STOCK_URL,
            "announcement_endpoint": CNINFO_QUERY_URL,
            "category": CATEGORY,
            "keyword": KEYWORD,
            "stock_map_count": len(mapping),
            "stock_map_fetch": stock_meta,
        },
        "universe_source": universe_source,
        "universe_count": len(bonds),
        "record_count": len(records),
        "announced_count": statuses.count("ANNOUNCED_EARLY_REDEMPTION"),
        "no_match_count": statuses.count("NO_MATCH_AS_OF_CUTOFF"),
        "unverified_count": statuses.count("UNVERIFIED"),
        "current_universe_complete": current_complete,
        "coverage": {
            "requested_count": len(bonds),
            "completed_count": sum(record["query_complete"] for record in records),
            "pages_fetched": pages_fetched,
            "announcements_fetched": announcements_fetched,
            "complete": current_complete,
        },
        "records": records,
        "errors": sorted(set(top_errors)),
    }
    payload["records_sha256"] = _sha256_bytes(_canonical_bytes(records))
    return payload


class _FixtureClient:
    def __init__(self, stock_rows: list[dict[str, Any]], pages: dict[tuple[str, int], dict[str, Any]]) -> None:
        self.stock_rows = stock_rows
        self.pages = pages

    def request_json(self, method: str, url: str, form: dict[str, str] | None = None) -> tuple[Any, dict[str, Any]]:
        if method == "GET" and url == CNINFO_STOCK_URL:
            payload: Any = {"stockList": self.stock_rows}
        elif method == "POST" and url == CNINFO_QUERY_URL and form is not None:
            code = form["stock"].split(",", 1)[0]
            payload = self.pages[(code, int(form["pageNum"]))]
        else:
            raise SnapshotError("unexpected fixture request")
        raw = _canonical_bytes(payload)
        return payload, {
            "attempts": 1,
            "http_status": 200,
            "response_size": len(raw),
            "response_sha256": _sha256_bytes(raw),
            "errors": [],
            "diagnostics": [],
        }


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        if seconds < 0:
            raise AssertionError("fixture clock cannot sleep backwards")
        self.sleeps.append(seconds)
        self.now += seconds


class _SequenceResponse:
    def __init__(self, raw: bytes, status: int) -> None:
        self.raw = raw
        self.status = status

    def read(self) -> bytes:
        return self.raw

    def __enter__(self) -> "_SequenceResponse":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        return None


class _SequenceOpener:
    def __init__(self, events: list[dict[str, Any]], clock: _FakeClock) -> None:
        self.events = list(events)
        self.clock = clock
        self.call_times: list[float] = []

    def open(self, request: urllib.request.Request, timeout: float) -> _SequenceResponse:
        del timeout
        self.call_times.append(self.clock.monotonic())
        if not self.events:
            raise AssertionError("unexpected fixture HTTP request")
        event = self.events.pop(0)
        status = int(event.get("status", 200))
        raw_value = event.get("raw")
        raw = bytes(raw_value) if isinstance(raw_value, (bytes, bytearray)) else _canonical_bytes(event.get("payload"))
        headers = event.get("headers") or {}
        if status >= 400:
            raise urllib.error.HTTPError(
                request.full_url,
                status,
                str(event.get("reason") or "fixture HTTP error"),
                headers,
                io.BytesIO(raw),
            )
        return _SequenceResponse(raw, status)


class _ConcurrentSnapshotOpener:
    def __init__(self, stock_rows: list[dict[str, str]], *, release_after: int = 2) -> None:
        self.stock_rows = stock_rows
        self.release_after = release_after
        self._lock = threading.Lock()
        self._release = threading.Event()
        self.active = 0
        self.max_active = 0
        self.post_calls = 0

    def open(self, request: urllib.request.Request, timeout: float) -> _SequenceResponse:
        del timeout
        if request.full_url == CNINFO_STOCK_URL:
            return _SequenceResponse(_canonical_bytes({"stockList": self.stock_rows}), 200)
        if request.full_url != CNINFO_QUERY_URL:
            raise AssertionError(f"unexpected fixture URL: {request.full_url}")
        with self._lock:
            self.active += 1
            self.post_calls += 1
            self.max_active = max(self.max_active, self.active)
            if self.post_calls >= self.release_after:
                self._release.set()
        try:
            self._release.wait(timeout=0.5)
            time.sleep(0.02)
            return _SequenceResponse(
                _canonical_bytes({
                    "totalAnnouncement": 0,
                    "hasMore": False,
                    "announcements": [],
                }),
                200,
            )
        finally:
            with self._lock:
                self.active -= 1


class _ThreadTimingOpener:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.call_times: dict[int, list[float]] = {}

    def open(self, request: urllib.request.Request, timeout: float) -> _SequenceResponse:
        del request, timeout
        thread_id = threading.get_ident()
        with self._lock:
            self.call_times.setdefault(thread_id, []).append(time.monotonic())
        return _SequenceResponse(_canonical_bytes({"ok": True}), 200)


class _CircuitRaceOpener:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._forbidden_release = threading.Event()
        self.success_entered = threading.Event()
        self.release_success = threading.Event()
        self.active = 0
        self.max_active = 0
        self.forbidden_calls = 0
        self.total_calls = 0

    def open(self, request: urllib.request.Request, timeout: float) -> _SequenceResponse:
        del timeout
        with self._lock:
            self.active += 1
            self.total_calls += 1
            self.max_active = max(self.max_active, self.active)
        try:
            if request.full_url.endswith("/success"):
                self.success_entered.set()
                self.release_success.wait(timeout=1.0)
                return _SequenceResponse(_canonical_bytes({"success": True}), 200)
            if request.full_url.endswith("/forbidden"):
                with self._lock:
                    self.forbidden_calls += 1
                    if self.forbidden_calls >= 2:
                        self._forbidden_release.set()
                self._forbidden_release.wait(timeout=1.0)
                raise urllib.error.HTTPError(
                    request.full_url,
                    403,
                    "fixture forbidden",
                    {},
                    io.BytesIO(b"forbidden"),
                )
            raise AssertionError(f"unexpected fixture URL: {request.full_url}")
        finally:
            with self._lock:
                self.active -= 1


class _CooldownOpener:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.calls: list[tuple[str, float, int]] = []

    def open(self, request: urllib.request.Request, timeout: float) -> _SequenceResponse:
        del timeout
        with self._lock:
            self.calls.append((request.full_url, time.monotonic(), threading.get_ident()))
        if request.full_url.endswith("/rate-limit"):
            raise urllib.error.HTTPError(
                request.full_url,
                429,
                "fixture rate limit",
                {},
                io.BytesIO(b"rate limited"),
            )
        return _SequenceResponse(_canonical_bytes({"recovered": True}), 200)


class _FailingQueryClient:
    def __init__(self, stock_rows: list[dict[str, str]]) -> None:
        self.stock_rows = stock_rows

    def request_json(
        self,
        method: str,
        url: str,
        form: dict[str, str] | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        del form
        if method == "GET" and url == CNINFO_STOCK_URL:
            payload: Any = {"stockList": self.stock_rows}
            raw = _canonical_bytes(payload)
            return payload, {
                "attempts": 1,
                "http_status": 200,
                "response_size": len(raw),
                "response_sha256": _sha256_bytes(raw),
                "errors": [],
                "diagnostics": [],
            }
        raise SnapshotError("fixture_query_failure", [{"event": "fixture_query_failure"}])


def _epoch_ms(value: str) -> int:
    parsed = dt.datetime.fromisoformat(value).replace(tzinfo=SHANGHAI)
    return int(parsed.timestamp() * 1000)


def _selftest() -> int:
    bonds = [
        _normalize_bond({"symbol": "123001.SZ", "name": "测试转债", "underlying": "000001"}, 0),
        _normalize_bond({"symbol": "110001.SH", "name": "空白转债", "underlying": "600000"}, 1),
    ]
    pages = {
        ("000001", 1): {
            "totalAnnouncement": 2,
            "hasMore": True,
            "announcements": [{
                "announcementId": "A1",
                "announcementTitle": "关于“测试转债”预计触发赎回条款的提示性公告",
                "announcementTime": _epoch_ms("2026-07-01 09:00:00"),
                "secCode": "000001",
                "adjunctUrl": "/finalpage/fixture-a1.pdf",
            }],
        },
        ("000001", 2): {
            "totalAnnouncement": 2,
            "hasMore": False,
            "announcements": [{
                "announcementId": "A2",
                "announcementTitle": "关于提前赎回“测试转债”暨摘牌的公告",
                "announcementTime": _epoch_ms("2026-07-02 09:00:00"),
                "secCode": "000001",
                "adjunctUrl": "/finalpage/fixture-a2.pdf",
            }],
        },
        ("600000", 1): {"totalAnnouncement": 0, "hasMore": False, "announcements": []},
    }
    client = _FixtureClient(
        [{"code": "000001", "orgId": "gssz0000001"}, {"code": "600000", "orgId": "gssh0600000"}],
        pages,
    )
    cutoff, cutoff_date, as_of = _parse_cutoff("20260727")
    snapshot = _build_snapshot(
        bonds,
        {"mode": "fixture", "record_count": 2},
        True,
        "fixture-pass",
        cutoff,
        cutoff_date,
        as_of,
        client,
        2,
        1,
        10,
    )
    by_symbol = {item["symbol"]: item for item in snapshot["records"]}
    checks = {
        "schema": snapshot["schema"] == SCHEMA,
        "pass_status": snapshot["status"] == "PASS",
        "full_pagination": by_symbol["123001.SZ"]["pages_fetched"] == 2,
        "announced": by_symbol["123001.SZ"]["early_redemption_status"] == "ANNOUNCED_EARLY_REDEMPTION",
        "empty_query_safe_when_complete": by_symbol["110001.SH"]["early_redemption_status"] == "NO_MATCH_AS_OF_CUTOFF",
        "non_exclusion_first": _classify_title("关于不提前赎回测试转债的公告")[0] == "NON_EXCLUSION",
        "conditional_recalculation_is_non_exclusion": _classify_title(
            "关于测试转债重新计算是否满足赎回条件的提示性公告"
        )[0] == "NON_EXCLUSION",
        "conflict_closed": _classify_title("关于不提前赎回测试转债暨摘牌的公告")[0] == "CONFLICT",
        "normalized_exact_name": _normalize_title("“ 测试 转债 ”") == _normalize_title("测试转债"),
    }

    session_client = JsonHttpClient(1.0, 0)
    cookie_handlers = [
        handler
        for handler in session_client._opener.handlers
        if isinstance(handler, urllib.request.HTTPCookieProcessor)
    ]
    checks["single_cookie_session"] = (
        isinstance(session_client._cookie_jar, http.cookiejar.CookieJar)
        and len(cookie_handlers) == 1
        and cookie_handlers[0].cookiejar is session_client._cookie_jar
    )

    throttle_clock = _FakeClock()
    throttle_opener = _SequenceOpener(
        [{"payload": {"request": 1}}, {"payload": {"request": 2}}],
        throttle_clock,
    )
    throttle_client = JsonHttpClient(
        1.0,
        0,
        opener=throttle_opener,
        monotonic_fn=throttle_clock.monotonic,
        sleep_fn=throttle_clock.sleep,
        uniform_fn=lambda _low, _high: 0.0,
        min_interval_seconds=1.0,
        interval_jitter_seconds=0.0,
    )
    throttle_client.request_json("GET", "https://fixture.invalid/one")
    throttle_client.request_json("GET", "https://fixture.invalid/two")
    checks["global_throttle"] = (
        throttle_opener.call_times == [0.0, 1.0]
        and throttle_clock.sleeps == [1.0]
    )

    retry_clock = _FakeClock()
    blocked_body = b"<html>temporary access denied</html>"
    retry_opener = _SequenceOpener(
        [
            {
                "status": 403,
                "raw": blocked_body,
                "headers": {"Content-Type": "text/html", "Retry-After": "2"},
            },
            {"payload": {"recovered": True}},
        ],
        retry_clock,
    )
    retry_client = JsonHttpClient(
        1.0,
        2,
        opener=retry_opener,
        monotonic_fn=retry_clock.monotonic,
        sleep_fn=retry_clock.sleep,
        uniform_fn=lambda _low, _high: 0.0,
        min_interval_seconds=1.0,
        interval_jitter_seconds=0.0,
        forbidden_cooldown_seconds=2.0,
        max_server_cooldown_seconds=10.0,
        circuit_threshold=2,
    )
    retry_payload, retry_meta = retry_client.request_json("POST", "https://fixture.invalid/query", {"q": "1"})
    retry_diagnostic = retry_meta["diagnostics"][0]
    checks["http_403_then_success"] = (
        retry_payload == {"recovered": True}
        and retry_meta["attempts"] == 2
        and retry_meta["errors"] == ["attempt_1:HTTP_403"]
        and retry_opener.call_times == [0.0, 2.0]
        and retry_client._consecutive_403 == 0
    )
    checks["http_error_diagnostics"] = (
        retry_diagnostic["http_status"] == 403
        and retry_diagnostic["response_headers"]["Retry-After"] == "2"
        and retry_diagnostic["body_sample_sha256"] == _sha256_bytes(blocked_body)
        and retry_diagnostic["cooldown_seconds"] == 2.0
    )

    rate_clock = _FakeClock()
    rate_opener = _SequenceOpener(
        [
            {"status": 429, "raw": b"slow down", "headers": {"Retry-After": "3"}},
            {"payload": {"rate_recovered": True}},
        ],
        rate_clock,
    )
    rate_client = JsonHttpClient(
        1.0,
        1,
        opener=rate_opener,
        monotonic_fn=rate_clock.monotonic,
        sleep_fn=rate_clock.sleep,
        uniform_fn=lambda _low, _high: 0.0,
        min_interval_seconds=1.0,
        interval_jitter_seconds=0.0,
        rate_limit_cooldown_seconds=1.0,
        max_server_cooldown_seconds=10.0,
    )
    rate_payload, rate_meta = rate_client.request_json("GET", "https://fixture.invalid/rate")
    checks["http_429_retry_after"] = (
        rate_payload == {"rate_recovered": True}
        and rate_meta["attempts"] == 2
        and rate_opener.call_times == [0.0, 3.0]
    )

    blocked_bond = [_normalize_bond({"symbol": "123002.SZ", "name": "未来转债", "underlying": "000002"}, 0)]

    circuit_clock = _FakeClock()
    circuit_opener = _SequenceOpener(
        [
            {"status": 403, "raw": b"blocked-1"},
            {"status": 403, "raw": b"blocked-2"},
            {"payload": {"must_not_be_called": True}},
        ],
        circuit_clock,
    )
    circuit_client = JsonHttpClient(
        1.0,
        3,
        opener=circuit_opener,
        monotonic_fn=circuit_clock.monotonic,
        sleep_fn=circuit_clock.sleep,
        uniform_fn=lambda _low, _high: 0.0,
        min_interval_seconds=0.5,
        interval_jitter_seconds=0.0,
        forbidden_cooldown_seconds=1.0,
        max_server_cooldown_seconds=10.0,
        circuit_threshold=2,
    )
    circuit_record = _query_one(
        blocked_bond[0],
        "gssz0000002",
        cutoff_date,
        as_of,
        30,
        10,
        circuit_client,
    )
    calls_before_open_check = len(circuit_opener.call_times)
    try:
        circuit_client.request_json("GET", "https://fixture.invalid/after-open")
        circuit_open_error: SnapshotError | None = None
    except SnapshotError as exc:
        circuit_open_error = exc
    checks["consecutive_403_circuit_breaker"] = (
        circuit_record["early_redemption_status"] == "UNVERIFIED"
        and circuit_client._circuit_open
        and calls_before_open_check == 2
        and len(circuit_opener.call_times) == 2
        and circuit_open_error is not None
        and "circuit_open:consecutive_HTTP_403:2" in str(circuit_open_error)
    )
    checks["failure_diagnostics_persisted"] = (
        len(circuit_record["request_diagnostics"]) == 3
        and circuit_record["request_diagnostics"][1].get("circuit_opened") is True
        and circuit_record["request_diagnostics"][2].get("event") == "circuit_open"
    )

    concurrent_bonds = [
        _normalize_bond(
            {
                "symbol": f"12310{index}.SZ",
                "name": f"并发{index}转债",
                "underlying": f"00010{index}",
            },
            index,
        )
        for index in range(6)
    ]
    concurrent_rows = [
        {"code": bond["underlying_code"], "orgId": f"gssz{bond['underlying_code']}"}
        for bond in concurrent_bonds
    ]
    concurrent_opener = _ConcurrentSnapshotOpener(concurrent_rows)
    concurrent_client = JsonHttpClient(
        1.0,
        0,
        opener=concurrent_opener,
        min_interval_seconds=0.0,
        interval_jitter_seconds=0.0,
    )
    concurrent_snapshot = _build_snapshot(
        concurrent_bonds,
        {"mode": "fixture", "record_count": len(concurrent_bonds)},
        True,
        "fixture-concurrency",
        cutoff,
        cutoff_date,
        as_of,
        concurrent_client,
        4,
        30,
        10,
    )
    checks["bounded_workers_overlap_real_http_open"] = bool(
        concurrent_snapshot["status"] == "PASS"
        and concurrent_snapshot["record_count"] == len(concurrent_bonds)
        and 1 < concurrent_opener.max_active <= 4
    )

    timing_opener = _ThreadTimingOpener()
    timing_client = JsonHttpClient(
        1.0,
        0,
        opener=timing_opener,
        min_interval_seconds=0.05,
        interval_jitter_seconds=0.0,
    )
    timing_start = threading.Event()

    def _timed_pair(worker: int) -> None:
        timing_start.wait(timeout=1.0)
        timing_client.request_json("GET", f"https://fixture.invalid/timing/{worker}/1")
        timing_client.request_json("GET", f"https://fixture.invalid/timing/{worker}/2")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        timing_futures = [executor.submit(_timed_pair, worker) for worker in range(2)]
        timing_start.set()
        for future in timing_futures:
            future.result(timeout=2.0)
    timing_deltas = [
        call_times[1] - call_times[0]
        for call_times in timing_opener.call_times.values()
        if len(call_times) == 2
    ]
    checks["per_thread_minimum_interval"] = bool(
        len(timing_deltas) == 2
        and all(delta >= 0.04 for delta in timing_deltas)
    )

    circuit_race_opener = _CircuitRaceOpener()
    circuit_race_client = JsonHttpClient(
        1.0,
        0,
        opener=circuit_race_opener,
        min_interval_seconds=0.0,
        interval_jitter_seconds=0.0,
        forbidden_cooldown_seconds=0.0,
        circuit_threshold=2,
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        success_future = executor.submit(
            circuit_race_client.request_json,
            "GET",
            "https://fixture.invalid/success",
        )
        success_started = circuit_race_opener.success_entered.wait(timeout=1.0)
        forbidden_futures = [
            executor.submit(
                circuit_race_client.request_json,
                "GET",
                "https://fixture.invalid/forbidden",
            )
            for _ in range(2)
        ]
        forbidden_errors: list[SnapshotError] = []
        for future in forbidden_futures:
            try:
                future.result(timeout=2.0)
            except SnapshotError as exc:
                forbidden_errors.append(exc)
        circuit_open_before_success = circuit_race_client._circuit_open
        circuit_race_opener.release_success.set()
        success_payload, _success_meta = success_future.result(timeout=2.0)
    calls_before_rejected_request = circuit_race_opener.total_calls
    try:
        circuit_race_client.request_json("GET", "https://fixture.invalid/after-circuit")
        rejected_after_circuit = False
    except SnapshotError:
        rejected_after_circuit = True
    checks["concurrent_403_shared_circuit_and_success_cannot_reopen"] = bool(
        success_started
        and len(forbidden_errors) == 2
        and circuit_race_opener.max_active > 1
        and circuit_race_opener.forbidden_calls == 2
        and circuit_open_before_success
        and circuit_race_client._circuit_open
        and circuit_race_client._consecutive_403 == 2
        and success_payload == {"success": True}
        and rejected_after_circuit
        and circuit_race_opener.total_calls == calls_before_rejected_request
    )

    cooldown_opener = _CooldownOpener()
    cooldown_client = JsonHttpClient(
        1.0,
        0,
        opener=cooldown_opener,
        min_interval_seconds=0.0,
        interval_jitter_seconds=0.0,
        rate_limit_cooldown_seconds=0.1,
        max_server_cooldown_seconds=1.0,
    )

    def _rate_limited_request() -> None:
        try:
            cooldown_client.request_json("GET", "https://fixture.invalid/rate-limit")
        except SnapshotError:
            return
        raise AssertionError("fixture rate-limit request unexpectedly succeeded")

    rate_thread = threading.Thread(target=_rate_limited_request)
    rate_thread.start()
    rate_thread.join(timeout=2.0)
    cooldown_followup_started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        cooldown_payload, _cooldown_meta = executor.submit(
            cooldown_client.request_json,
            "GET",
            "https://fixture.invalid/after-rate-limit",
        ).result(timeout=2.0)
    cooldown_followup_call = cooldown_opener.calls[-1]
    checks["http_429_cooldown_is_global_across_threads"] = bool(
        not rate_thread.is_alive()
        and cooldown_payload == {"recovered": True}
        and cooldown_followup_call[0].endswith("/after-rate-limit")
        and cooldown_followup_call[1] - cooldown_followup_started >= 0.08
    )

    failing_snapshot = _build_snapshot(
        blocked_bond,
        {"mode": "fixture", "record_count": 1},
        True,
        "fixture-query-failure",
        cutoff,
        cutoff_date,
        as_of,
        _FailingQueryClient([{"code": "000002", "orgId": "gssz0000002"}]),
        4,
        30,
        10,
    )
    checks["query_failure_remains_unverified_and_snapshot_blocked"] = bool(
        failing_snapshot["status"] == "BLOCKED"
        and failing_snapshot["unverified_count"] == 1
        and failing_snapshot["records"][0]["early_redemption_status"] == "UNVERIFIED"
    )

    future_client = _FixtureClient(
        [{"code": "000002", "orgId": "gssz0000002"}],
        {("000002", 1): {
            "totalAnnouncement": 1,
            "hasMore": False,
            "announcements": [{
                "announcementId": "FUTURE-1",
                "announcementTitle": "关于提前赎回未来转债的公告",
                "announcementTime": _epoch_ms("2026-07-28 09:00:00"),
                "secCode": "000002",
                "adjunctUrl": "/finalpage/fixture-future.pdf",
            }],
        }},
    )
    future_snapshot = _build_snapshot(
        blocked_bond,
        {"mode": "fixture", "record_count": 1},
        True,
        "fixture-future",
        cutoff,
        cutoff_date,
        as_of,
        future_client,
        1,
        30,
        10,
    )
    checks["future_is_blocked"] = (
        future_snapshot["status"] == "BLOCKED"
        and future_snapshot["records"][0]["early_redemption_status"] == "UNVERIFIED"
    )
    incomplete_client = _FixtureClient(
        [{"code": "000002", "orgId": "gssz0000002"}],
        {("000002", 1): {
            "totalAnnouncement": 2,
            "hasMore": False,
            "announcements": [{
                "announcementId": "ONLY-1",
                "announcementTitle": "关于未来转债预计触发赎回条款的公告",
                "announcementTime": _epoch_ms("2026-07-01 09:00:00"),
                "secCode": "000002",
                "adjunctUrl": "/finalpage/fixture-only.pdf",
            }],
        }},
    )
    incomplete_snapshot = _build_snapshot(
        blocked_bond,
        {"mode": "fixture", "record_count": 1},
        True,
        "fixture-incomplete",
        cutoff,
        cutoff_date,
        as_of,
        incomplete_client,
        1,
        30,
        10,
    )
    checks["incomplete_pagination_is_blocked"] = (
        incomplete_snapshot["status"] == "BLOCKED"
        and incomplete_snapshot["records"][0]["early_redemption_status"] == "UNVERIFIED"
    )
    with tempfile.TemporaryDirectory(prefix="cb-redemption-selftest-") as directory:
        target = Path(directory) / "snapshot.json"
        _atomic_write_json(target, snapshot)
        persisted = json.loads(target.read_text(encoding="utf-8"))
        checks["atomic_persisted_readback"] = persisted["records_sha256"] == snapshot["records_sha256"]
    passed = all(checks.values())
    print(json.dumps({"status": "PASS" if passed else "FAIL", "checks": checks}, ensure_ascii=False, sort_keys=True))
    return 0 if passed else 1


def _blocked_snapshot(run_id: str, cutoff: str, as_of: dt.datetime, error: str) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    return {
        "schema": SCHEMA,
        "status": "BLOCKED",
        "run_id": run_id,
        "cutoff": cutoff,
        "as_of": as_of.isoformat(),
        "generated_at": dt.datetime.now(SHANGHAI).isoformat(),
        "source": {
            "provider": "CNINFO",
            "org_id_endpoint": CNINFO_STOCK_URL,
            "announcement_endpoint": CNINFO_QUERY_URL,
            "category": CATEGORY,
            "keyword": KEYWORD,
        },
        "universe_source": {},
        "universe_count": 0,
        "record_count": 0,
        "announced_count": 0,
        "no_match_count": 0,
        "unverified_count": 0,
        "current_universe_complete": False,
        "coverage": {
            "requested_count": 0,
            "completed_count": 0,
            "pages_fetched": 0,
            "announcements_fetched": 0,
            "complete": False,
        },
        "records": records,
        "errors": [error],
        "records_sha256": _sha256_bytes(_canonical_bytes(records)),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch official CNINFO early-redemption announcements for the current convertible-bond universe.",
    )
    parser.add_argument("--output", type=Path, help="Atomic JSON output path (required unless --selftest).")
    parser.add_argument("--run-id", help="Run identifier bound into the snapshot (required unless --selftest).")
    parser.add_argument("--cutoff", help="Asia/Shanghai cutoff date, YYYYMMDD or YYYY-MM-DD (required unless --selftest).")
    parser.add_argument(
        "--universe",
        type=Path,
        help="Optional fixed universe JSON. Omit to call the sibling parse_bonds() over current speckzzdata.txt + TNF.",
    )
    parser.add_argument("--workers", type=int, default=4, help="Concurrent per-bond requests (default: 4; range: 1-8).")
    parser.add_argument("--timeout-seconds", type=float, default=15.0, help="Per-request timeout (default: 15).")
    parser.add_argument("--retries", type=int, default=3, help="Retries after the first request (default: 3; range: 0-6).")
    parser.add_argument("--page-size", type=int, default=30, help="CNINFO page size (default: 30; range: 1-100).")
    parser.add_argument("--max-pages", type=int, default=1000, help="Fail-closed pagination ceiling (default: 1000).")
    parser.add_argument("--selftest", action="store_true", help="Run the offline fixture selftest; no network access.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.selftest:
        return _selftest()
    missing = [name for name in ("output", "run_id", "cutoff") if getattr(args, name) in (None, "")]
    if missing:
        _parser().error("required unless --selftest: " + ", ".join(f"--{name.replace('_', '-')}" for name in missing))
    if not 1 <= args.workers <= 8:
        _parser().error("--workers must be between 1 and 8")
    if not 0 <= args.retries <= 6:
        _parser().error("--retries must be between 0 and 6")
    if not 1 <= args.page_size <= 100:
        _parser().error("--page-size must be between 1 and 100")
    if not 1 <= args.max_pages <= 10000:
        _parser().error("--max-pages must be between 1 and 10000")
    if not 1.0 <= args.timeout_seconds <= 120.0:
        _parser().error("--timeout-seconds must be between 1 and 120")

    cutoff, cutoff_date, as_of = _parse_cutoff(args.cutoff)
    try:
        bonds, universe_source, universe_complete = _load_universe(args.universe, cutoff)
        shared_snapshot = _shared_readonly_snapshot_path()
        if shared_snapshot is not None:
            snapshot = _load_shared_readonly_snapshot(
                shared_snapshot,
                bonds=bonds,
                run_id=args.run_id,
                cutoff=cutoff,
                as_of=as_of,
            )
        else:
            snapshot = _build_snapshot(
                bonds,
                universe_source,
                universe_complete,
                args.run_id,
                cutoff,
                cutoff_date,
                as_of,
                JsonHttpClient(args.timeout_seconds, args.retries),
                args.workers,
                args.page_size,
                args.max_pages,
            )
    except Exception as exc:
        snapshot = _blocked_snapshot(args.run_id, cutoff, as_of, f"fatal:{type(exc).__name__}:{str(exc)[:500]}")
    _atomic_write_json(args.output, snapshot)
    print(json.dumps({
        "schema": snapshot["schema"],
        "status": snapshot["status"],
        "output": str(args.output.resolve()),
        "record_count": snapshot["record_count"],
        "announced_count": snapshot["announced_count"],
        "no_match_count": snapshot["no_match_count"],
        "unverified_count": snapshot["unverified_count"],
        "records_sha256": snapshot["records_sha256"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if snapshot["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
