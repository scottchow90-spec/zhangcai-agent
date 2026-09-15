#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import re
from datetime import datetime, time as clock_time, timedelta, timezone
from typing import Any
from urllib.request import Request, urlopen


CHINA_TZ = timezone(timedelta(hours=8))
HTTP_TIMEOUT_SECONDS = 10


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
    return trade_date, {"source_id": "tencent", "trade_date": trade_date, "index_count": len(stamps)}


def _fetch_sina_trade_date() -> tuple[str, dict[str, Any]]:
    request = Request(
        "https://hq.sinajs.cn/list=sh000001,sz399001",
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"},
    )
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        text = response.read().decode("gb18030", errors="strict")
    dates = {
        value.replace("-", "")
        for value in re.findall(r",(20\d{2}-\d{2}-\d{2}),\d{2}:\d{2}:\d{2}", text)
    }
    if len(dates) != 1:
        raise RuntimeError(f"sina_trade_date_ambiguous:{sorted(dates)}")
    trade_date = dates.pop()
    return trade_date, {"source_id": "sina", "trade_date": trade_date, "index_count": text.count("var hq_str_")}


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
    for source_id, fetcher in (("tencent", _fetch_tencent_trade_date), ("sina", _fetch_sina_trade_date)):
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


def _parse_datetime(value: object) -> datetime:
    parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=CHINA_TZ)


def validate_data_evidence(
    payload: dict[str, Any], snapshot: dict[str, Any], config: dict[str, Any] | None = None
) -> dict[str, Any]:
    config = config or {}
    errors: list[str] = []
    trade_date = re.sub(r"\D", "", str(payload.get("trade_date") or ""))
    live_date = re.sub(r"\D", "", str(snapshot.get("latest_available_trade_date") or ""))
    if snapshot.get("status") != "PASS":
        errors.append("market_snapshot_blocked")
    if not trade_date or trade_date != live_date:
        errors.append(f"payload_trade_date_mismatch:{trade_date}!={live_date}")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        sources = []
        errors.append("sources_missing_or_invalid")
    provider_groups: set[str] = set()
    checked_at: datetime | None
    try:
        checked_at = _parse_datetime(snapshot.get("checked_at"))
    except (TypeError, ValueError):
        checked_at = None
        errors.append("snapshot_checked_at_invalid")
    phase = str(snapshot.get("market_phase") or "")
    default_age = 900 if phase in {"active", "midday_pause", "preopen_with_current_data"} else 7200
    max_age = float(config.get("max_source_age_seconds") or default_age)
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"source_invalid:{index}")
            continue
        group = str(source.get("provider_group") or source.get("source_id") or "").strip()
        if group:
            provider_groups.add(group)
        else:
            errors.append(f"source_provider_missing:{index}")
        source_date = re.sub(r"\D", "", str(source.get("trade_date") or ""))
        if source_date != trade_date:
            errors.append(f"source_trade_date_mismatch:{index}:{source_date}!={trade_date}")
        if not str(source.get("locator") or "").strip():
            errors.append(f"source_locator_missing:{index}")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", str(source.get("sha256") or "")):
            errors.append(f"source_sha256_invalid:{index}")
        try:
            fetched_at = _parse_datetime(source.get("fetched_at"))
            if checked_at is not None:
                age = (checked_at - fetched_at.astimezone(checked_at.tzinfo)).total_seconds()
                if age < -120 or age > max_age:
                    errors.append(f"source_age_invalid:{index}:{age:.0f}s")
        except (TypeError, ValueError):
            errors.append(f"source_fetched_at_invalid:{index}")
    if len(provider_groups) < 2:
        errors.append(f"independent_provider_groups_insufficient:{len(provider_groups)}<2")
    return {
        "status": "PASS" if not errors else "BLOCKED",
        "trade_date": trade_date,
        "source_count": len(sources),
        "provider_group_count": len(provider_groups),
        "errors": errors,
    }


def run_selftests() -> dict[str, Any]:
    checked_at = "2099-01-05T15:15:00+08:00"
    snapshot = {
        "status": "PASS",
        "checked_at": checked_at,
        "latest_available_trade_date": "20990105",
        "market_phase": "postclose",
        "sources": [],
        "errors": [],
    }
    payload = {
        "trade_date": "2099-01-05",
        "sources": [
            {"source_id": "S1", "provider_group": "A", "trade_date": "2099-01-05", "fetched_at": "2099-01-05T15:00:00+08:00", "locator": "synthetic://s1", "sha256": "a" * 64},
            {"source_id": "S2", "provider_group": "B", "trade_date": "2099-01-05", "fetched_at": "2099-01-05T15:00:00+08:00", "locator": "synthetic://s2", "sha256": "b" * 64},
        ],
    }
    checks: list[dict[str, Any]] = []

    def check(name: str, candidate: dict[str, Any], market: dict[str, Any], expected: str) -> None:
        actual = validate_data_evidence(candidate, market)["status"]
        checks.append({"name": name, "status": "PASS" if actual == expected else "FAIL", "actual": actual, "expected": expected})

    import copy
    check("valid_fixture", copy.deepcopy(payload), copy.deepcopy(snapshot), "PASS")
    candidate = copy.deepcopy(payload); candidate["trade_date"] = "2099-01-04"
    check("trade_date_mismatch", candidate, copy.deepcopy(snapshot), "BLOCKED")
    candidate = copy.deepcopy(payload); candidate["sources"] = []
    check("sources_required", candidate, copy.deepcopy(snapshot), "BLOCKED")
    candidate = copy.deepcopy(payload); candidate["sources"][0]["trade_date"] = "2099-01-04"
    check("source_trade_date", candidate, copy.deepcopy(snapshot), "BLOCKED")
    candidate = copy.deepcopy(payload); candidate["sources"][0]["fetched_at"] = "invalid"
    check("source_timestamp", candidate, copy.deepcopy(snapshot), "BLOCKED")
    candidate = copy.deepcopy(payload); candidate["sources"][0]["fetched_at"] = "2099-01-05T10:00:00+08:00"
    check("source_age", candidate, copy.deepcopy(snapshot), "BLOCKED")
    candidate = copy.deepcopy(payload); candidate["sources"][1]["provider_group"] = "A"
    check("independent_sources", candidate, copy.deepcopy(snapshot), "BLOCKED")
    candidate = copy.deepcopy(payload); candidate["sources"][0]["sha256"] = "bad"
    check("source_digest", candidate, copy.deepcopy(snapshot), "BLOCKED")
    market = copy.deepcopy(snapshot); market["status"] = "BLOCKED"
    check("market_snapshot_status", copy.deepcopy(payload), market, "BLOCKED")
    return {"status": "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL", "checks": checks}
