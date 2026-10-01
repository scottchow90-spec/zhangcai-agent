#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import json
import re
from datetime import datetime, time as clock_time, timezone, timedelta
from typing import Any
from urllib.request import Request, urlopen


CHINA_TZ = timezone(timedelta(hours=8))
HTTP_TIMEOUT_SECONDS = 10
REQUIRED_QUOTE_FIELDS = ("open", "high", "low", "close", "amount", "volume", "preclose")


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _fetch_tencent_trade_date() -> tuple[str, dict[str, Any]]:
    request = Request(
        "https://qt.gtimg.cn/q=sh000001,sz399001",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        text = response.read().decode("gb18030", errors="strict")
    stamps = re.findall(r"~(20\d{12})~", text)
    dates = {stamp[:8] for stamp in stamps}
    if len(dates) != 1:
        raise RuntimeError(f"tencent_trade_date_ambiguous:{sorted(dates)}")
    trade_date = dates.pop()
    return trade_date, {
        "source_id": "tencent",
        "trade_date": trade_date,
        "index_count": len(stamps),
    }


def _fetch_sina_trade_date() -> tuple[str, dict[str, Any]]:
    request = Request(
        "https://hq.sinajs.cn/list=sh000001,sz399001",
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://finance.sina.com.cn",
        },
    )
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        text = response.read().decode("gb18030", errors="strict")
    dates = {value.replace("-", "") for value in re.findall(r",(20\d{2}-\d{2}-\d{2}),\d{2}:\d{2}:\d{2}", text)}
    if len(dates) != 1:
        raise RuntimeError(f"sina_trade_date_ambiguous:{sorted(dates)}")
    trade_date = dates.pop()
    return trade_date, {
        "source_id": "sina",
        "trade_date": trade_date,
        "index_count": text.count("var hq_str_"),
    }


def _market_phase(checked_at: datetime, trade_date: str) -> str:
    if checked_at.strftime("%Y%m%d") != trade_date:
        return "off_session"
    current = checked_at.timetz().replace(tzinfo=None)
    if clock_time(9, 15) <= current < clock_time(9, 30):
        return "preopen_with_current_data"
    if clock_time(9, 30) <= current <= clock_time(11, 30):
        return "active"
    if clock_time(11, 30) < current < clock_time(13, 0):
        return "midday_pause"
    if clock_time(13, 0) <= current < clock_time(15, 0):
        return "active"
    if current >= clock_time(15, 0):
        return "postclose"
    return "off_session"


def resolve_market_snapshot() -> dict[str, Any]:
    checked_at = datetime.now(CHINA_TZ)
    sources: list[dict[str, Any]] = []
    errors: list[str] = []
    for source_id, fetcher in (
        ("tencent", _fetch_tencent_trade_date),
        ("sina", _fetch_sina_trade_date),
    ):
        try:
            _trade_date, source = fetcher()
            sources.append(source)
        except Exception as exc:
            errors.append(f"{source_id}:{type(exc).__name__}:{exc}")
    dates = [str(item.get("trade_date") or "") for item in sources]
    latest = max(dates) if dates else ""
    matching = {str(item.get("source_id") or "") for item in sources if item.get("trade_date") == latest}
    if len(matching) < 2:
        errors.append(f"independent_market_sources_insufficient:{len(matching)}<2")
    return {
        "status": "PASS" if not errors else "BLOCKED",
        "checked_at": checked_at.isoformat(),
        "latest_available_trade_date": latest,
        "market_phase": _market_phase(checked_at, latest) if latest else "unknown",
        "sources": sources,
        "errors": errors,
    }


def validate_data_evidence(
    quote_payload: dict[str, Any], snapshot: dict[str, Any]
) -> dict[str, Any]:
    errors: list[str] = []
    trade_date = re.sub(r"\D", "", str(quote_payload.get("trade_date") or ""))
    live_date = re.sub(
        r"\D", "", str(snapshot.get("latest_available_trade_date") or "")
    )
    if trade_date != live_date:
        errors.append(f"quote_trade_date_mismatch:{trade_date}!={live_date}")
    quotes = quote_payload.get("quotes")
    if not isinstance(quotes, dict):
        quotes = {}
        errors.append("quote_map_missing_or_invalid")
    declared = str(quote_payload.get("quotes_sha256") or "")
    actual = _canonical_sha256(quotes)
    if declared != actual:
        errors.append("quotes_sha256_mismatch")
    valid_records = 0
    invalid_price_volume_records = 0
    for quote in quotes.values():
        if not isinstance(quote, dict) or not all(
            quote.get(field) is not None for field in REQUIRED_QUOTE_FIELDS
        ):
            continue
        try:
            open_price = float(quote["open"])
            high = float(quote["high"])
            low = float(quote["low"])
            close = float(quote["close"])
            preclose = float(quote["preclose"])
            amount = float(quote["amount"])
            volume = float(quote["volume"])
            average_price = amount / volume
            coherent = (
                min(open_price, high, low, close, preclose, amount, volume) > 0
                and high >= max(open_price, close)
                and low <= min(open_price, close)
                and low * 0.995 <= average_price <= high * 1.005
            )
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            coherent = False
        if coherent:
            valid_records += 1
        else:
            invalid_price_volume_records += 1
    if valid_records != len(quotes):
        errors.append(f"quote_records_invalid:{len(quotes) - valid_records}")
    if invalid_price_volume_records:
        errors.append(
            f"quote_price_volume_unit_invalid:{invalid_price_volume_records}"
        )
    fetched_at_raw = str(quote_payload.get("fetched_at") or "")
    try:
        fetched_at = datetime.fromisoformat(fetched_at_raw.replace("Z", "+00:00"))
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=CHINA_TZ)
        checked_at = datetime.fromisoformat(str(snapshot.get("checked_at") or ""))
        age_seconds = (checked_at - fetched_at.astimezone(checked_at.tzinfo)).total_seconds()
        max_age = 600 if snapshot.get("market_phase") in {"active", "preopen_with_current_data"} else 7200
        if age_seconds < -120 or age_seconds > max_age:
            errors.append(f"quote_evidence_age_invalid:{age_seconds:.0f}s")
    except (TypeError, ValueError) as exc:
        errors.append(f"quote_fetched_at_invalid:{type(exc).__name__}:{exc}")
    if not str(quote_payload.get("source") or "").strip():
        errors.append("quote_source_missing")
    return {
        "status": "PASS" if not errors else "BLOCKED",
        "trade_date": trade_date,
        "quote_record_count": len(quotes),
        "valid_quote_record_count": valid_records,
        "invalid_price_volume_record_count": invalid_price_volume_records,
        "errors": errors,
    }
