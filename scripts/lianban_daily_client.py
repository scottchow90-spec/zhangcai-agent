#!/usr/bin/env python3
"""Fetch and normalize one Lianban.net A-share daily review snapshot."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import html
import json
import os
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests


SCHEMA = "LIANBAN_DAILY_SNAPSHOT_V1"
BASE_URL = "https://lianban.net"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Zhangcai3003DataClient/1.0)",
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
    "Referer": f"{BASE_URL}/opendata.html",
}


def validate_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid_date:{value}") from exc


def build_urls(target_date: str, *, latest: bool) -> dict[str, str]:
    target_date = validate_date(target_date)
    return {
        "page": f"{BASE_URL}/days/{target_date}.html",
        "open_data": (
            f"{BASE_URL}/opendata/latest.json"
            if latest
            else f"{BASE_URL}/opendata/{target_date}.json"
        ),
    }


def first(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if mapping.get(key) is not None:
            return mapping[key]
    return None


def normalize_open_data(payload: dict[str, Any]) -> dict[str, Any]:
    kpi = payload.get("kpi") if isinstance(payload.get("kpi"), dict) else payload
    themes = first(payload, "themes", "plates", "topics")
    topics = []
    if isinstance(themes, list):
        for row in themes:
            if not isinstance(row, dict):
                continue
            name = first(row, "name", "theme", "plate")
            if isinstance(name, str) and name.strip():
                topics.append({
                    "name": name.strip(),
                    "count": first(row, "limit_up", "count", "zt"),
                })
    return {
        "target_date": first(kpi, "date", "trading_date"),
        "source": payload.get("source"),
        "license": payload.get("license"),
        "note": payload.get("note"),
        "market": {
            "limit_up": first(kpi, "limit_up", "zt"),
            "limit_down": first(kpi, "limit_down", "dt"),
            "consecutive": first(kpi, "lianban", "consecutive", "lb"),
            "max_board": first(kpi, "max_board", "height"),
            "seal_rate": first(kpi, "seal_rate_pct", "seal_rate", "rate"),
            "broken_board": first(kpi, "zhaban", "broken_board", "zb"),
            "advancers": first(kpi, "adv", "advancers", "up"),
            "decliners": first(kpi, "dec", "decliners", "down"),
            "emotion_stage": first(
                kpi,
                "emotion_phase",
                "emotion_stage",
                "emotion",
            ),
        },
        "topics": topics,
        "raw": payload,
    }


def balanced_object(text: str, start: int) -> str | None:
    depth = 0
    quote = None
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in {'"', "'"}:
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    return None


def stock_map(page_html: str) -> dict[str, Any]:
    match = re.search(r"\bvar\s+S\s*=\s*\{", page_html)
    if not match:
        return {}
    start = page_html.find("{", match.start())
    encoded = balanced_object(page_html, start)
    if not encoded:
        return {}
    try:
        payload = json.loads(encoded)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def strip_html(value: str) -> str:
    value = re.sub(
        r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>",
        " ",
        value,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def parse_html_details(page_html: str) -> dict[str, Any]:
    title_match = re.search(
        r"<title\b[^>]*>(.*?)</title>",
        page_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    title = strip_html(title_match.group(1)) if title_match else None
    rows = stock_map(page_html)
    stock_items = []
    stock_codes = set(re.findall(r"/(?:gu|stock)/([0368]\d{5})\.html", page_html))
    event_texts = []
    for code, row in rows.items():
        if not isinstance(row, dict):
            continue
        code = str(code)
        if re.fullmatch(r"[0368]\d{5}", code):
            stock_codes.add(code)
        reason = first(row, "rs", "reason")
        stock_items.append({
            "code": code,
            "name": first(row, "n", "name"),
            "board_count": first(row, "lb", "board_count"),
            "board_label": first(row, "lbs", "board_label"),
            "limit_up_time": first(row, "t", "limit_up_time"),
            "theme": first(row, "th", "theme"),
            "board": row.get("board"),
            "reason": reason,
            "price": first(row, "p", "price"),
            "pct": row.get("pct"),
        })
        if isinstance(reason, str) and reason.strip():
            event_texts.append(reason.strip())

    # Also support small embedded objects used by tests and lightweight pages.
    for match in re.finditer(
        r"\{[^{}]*\"code\"\s*:\s*\"([0368]\d{5})\"[^{}]*\}",
        page_html,
    ):
        try:
            item = json.loads(match.group(0))
        except json.JSONDecodeError:
            continue
        stock_codes.add(item["code"])
        stock_items.append(item)
        reason = item.get("reason")
        if isinstance(reason, str) and reason.strip():
            event_texts.append(reason.strip())

    text = strip_html(page_html)
    event_texts.extend(
        sentence.strip()
        for sentence in re.split(r"(?<=[。！？])", text)
        if any(token in sentence for token in ("事件", "政策", "异动", "催化", "主线"))
    )
    return {
        "title": title,
        "stock_count": len(stock_items),
        "stock_codes": sorted(stock_codes),
        "stock_items": stock_items,
        "event_texts": list(dict.fromkeys(event_texts))[:200],
    }


def _retry_delay(response: requests.Response | None, attempt: int) -> float:
    if response is not None:
        raw = response.headers.get("Retry-After")
        try:
            return min(45.0, max(0.0, float(raw)))
        except (TypeError, ValueError):
            pass
    return (5.0, 15.0, 45.0)[min(attempt, 2)]


def fetch(url: str, timeout: int, *, max_attempts: int = 4) -> requests.Response:
    attempts = max(1, max_attempts)
    for attempt in range(attempts):
        response = None
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException:
            status = response.status_code if response is not None else None
            retryable = status is None or status == 429 or status in {500, 502, 503, 504}
            if not retryable or attempt + 1 >= attempts:
                raise
            time.sleep(_retry_delay(response, attempt))
    raise RuntimeError("unreachable_fetch_retry_state")


def source_record(url: str, response: requests.Response | None, error: str | None) -> dict:
    content = response.content if response is not None else b""
    return {
        "url": url,
        "status_code": response.status_code if response is not None else None,
        "content_type": response.headers.get("content-type") if response is not None else None,
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest() if content else None,
        "error": error,
    }


def inherited_current_task_snapshot(requested_date: str) -> dict[str, Any] | None:
    if (
        os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1"
        or os.environ.get("CODEX_LIANBAN_STATUS") != "CLEAN_PASS"
        or os.environ.get("CODEX_LIANBAN_ATTRIBUTION") != "连板网"
    ):
        return None
    source_path = Path(os.environ.get("CODEX_LIANBAN_SNAPSHOT", "")).resolve()
    if not source_path.is_file():
        return None
    try:
        source_bytes = source_path.read_bytes()
        payload = json.loads(source_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    sources = payload.get("sources")
    page = sources.get("page") if isinstance(sources, dict) else None
    open_data = sources.get("open_data") if isinstance(sources, dict) else None
    details = payload.get("page_details")
    stock_items = details.get("stock_items") if isinstance(details, dict) else None
    if (
        payload.get("schema") != SCHEMA
        or payload.get("status") != "CLEAN_PASS"
        or (
            payload.get("target_date") != requested_date
            and payload.get("requested_date") != requested_date
        )
        or payload.get("errors")
        or not isinstance(page, dict)
        or page.get("status_code") != 200
        or page.get("url") != os.environ.get("CODEX_LIANBAN_SOURCE_URL")
        or not isinstance(open_data, dict)
        or open_data.get("status_code") != 200
        or open_data.get("url") != os.environ.get("CODEX_LIANBAN_OPEN_DATA_URL")
        or not isinstance(stock_items, list)
        or not stock_items
    ):
        return None
    payload["reuse"] = {
        "mode": "current_task_inherited_snapshot",
        "source_path": str(source_path),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
    }
    return payload


def collect_snapshot(
    requested_date: str,
    *,
    latest: bool = False,
    timeout: int = 25,
) -> dict[str, Any]:
    requested_date = validate_date(requested_date)
    inherited = inherited_current_task_snapshot(requested_date)
    if inherited is not None:
        inherited["current_invocation"] = {
            "requested_date": requested_date,
            "latest_requested": latest,
        }
        return inherited
    urls = build_urls(requested_date, latest=latest)
    errors = []
    open_response = page_response = None
    open_error = page_error = None
    normalized = {"target_date": None, "market": {}, "topics": []}
    details = {
        "title": None,
        "stock_count": 0,
        "stock_codes": [],
        "stock_items": [],
        "event_texts": [],
    }
    try:
        open_response = fetch(urls["open_data"], timeout)
        normalized = normalize_open_data(open_response.json())
    except Exception as exc:
        open_error = f"{type(exc).__name__}:{exc}"
        errors.append(f"open_data_fetch_failed:{open_error}")

    resolved_date = normalized.get("target_date") or requested_date
    try:
        resolved_date = validate_date(str(resolved_date))
    except argparse.ArgumentTypeError:
        resolved_date = requested_date
        errors.append("open_data_target_date_invalid")
    page_url = build_urls(resolved_date, latest=False)["page"]
    try:
        page_response = fetch(page_url, timeout)
        page_response.encoding = page_response.apparent_encoding or "utf-8"
        details = parse_html_details(page_response.text)
        if not details["stock_items"]:
            errors.append("page_stock_details_missing")
    except Exception as exc:
        page_error = f"{type(exc).__name__}:{exc}"
        errors.append(f"page_fetch_failed:{page_error}")

    clean = open_response is not None and page_response is not None and not errors
    return {
        "schema": SCHEMA,
        "status": "CLEAN_PASS" if clean else "DEGRADED",
        "requested_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "requested_date": requested_date,
        "target_date": resolved_date,
        "latest_requested": latest,
        "source_name": "连板网",
        "license": normalized.get("license") or "CC BY 4.0",
        "attribution_required": True,
        "source_role": "supplemental_event_theme_sentiment_cross_validation",
        "sources": {
            "open_data": source_record(urls["open_data"], open_response, open_error),
            "page": source_record(page_url, page_response, page_error),
        },
        "market": normalized.get("market", {}),
        "topics": normalized.get("topics", []),
        "note": normalized.get("note"),
        "page_details": details,
        "errors": errors,
    }


def write_snapshot(path: Path, payload: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if json.loads(temporary.read_text(encoding="utf-8")).get("schema") != SCHEMA:
        raise RuntimeError("snapshot_readback_failed")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--date", type=validate_date)
    target.add_argument("--latest", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=25)
    args = parser.parse_args()
    payload = collect_snapshot(
        args.date or date.today().isoformat(),
        latest=args.latest,
        timeout=max(1, args.timeout),
    )
    if args.output:
        write_snapshot(args.output, payload)
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
