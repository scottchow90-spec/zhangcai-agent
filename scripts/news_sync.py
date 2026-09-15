#!/usr/bin/env python3
"""Persist a daily, traceable public A-share news snapshot for the local runtime."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request
from collections import OrderedDict
from datetime import datetime
from typing import Any
from pathlib import Path

APP_ROOT = Path(os.environ.get("ZHANGCAI_APP_ROOT", Path(__file__).resolve().parents[1]))
DATA_ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR", APP_ROOT / "app-data"))
ROOT = DATA_ROOT / "news"
UA = {
    "User-Agent": "Mozilla/5.0 (ZhangcaiAgent/1.0)",
    "Accept": "application/json,text/plain,*/*",
}


def _iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _clean(value: Any) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return re.sub(r"\s+", " ", text).strip()


def _source_time(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)) or str(value).isdigit():
        try:
            number = float(value)
            if number > 10_000_000_000:
                number /= 1000
            return datetime.fromtimestamp(number).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        except (OverflowError, OSError, ValueError):
            return ""
    text = str(value).strip().replace("T", " ")
    match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})(?:[ T]+(\d{1,2}:\d{2}:\d{2}))?", text)
    return (match.group(1).replace("/", "-") + (f" {match.group(2)}" if match.group(2) else "")) if match else text


def _fetch_json(url: str, *, referer: str, timeout: int = 15) -> tuple[Any, dict[str, Any]]:
    request = urllib.request.Request(url, headers={**UA, "Referer": referer})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        return json.loads(raw.decode("utf-8-sig", "replace")), {
            "url": url,
            "http_status": int(response.status),
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }


def _provider_request(provider: str, limit: int) -> tuple[Any, dict[str, Any]]:
    if provider == "eastmoney":
        params = {"client": "web", "biz": "web_724", "fastColumn": "102", "sortEnd": "", "pageSize": str(limit), "req_trace": str(int(time.time() * 1000))}
        url = "https://np-weblist.eastmoney.com/comm/web/getFastNewsList?" + urllib.parse.urlencode(params)
        return _fetch_json(url, referer="https://kuaixun.eastmoney.com/7_24.html")
    if provider == "sina":
        params = {"pageid": "153", "lid": "2516", "num": str(limit), "page": "1"}
        url = "https://feed.mix.sina.com.cn/api/roll/get?" + urllib.parse.urlencode(params)
        return _fetch_json(url, referer="https://finance.sina.com.cn/")
    if provider == "cls":
        # The skill package documents this signed v1 endpoint as the current
        # route; the retired /api/cache route must not be counted as success.
        # CLS currently returns an empty body for rn=100; its public page
        # accepts 50 reliably, so keep the provider-specific bound explicit.
        params = {"appName": "CailianpressWeb", "os": "web", "sv": "7.7.5", "last_time": "", "refresh_type": "1", "rn": str(min(limit, 50))}
        query = "&".join(f"{key}={params[key]}" for key in sorted(params))
        sign = hashlib.md5(hashlib.sha1(query.encode("utf-8")).hexdigest().encode("ascii")).hexdigest()
        url = f"https://www.cls.cn/v1/roll/get_roll_list?{query}&sign={sign}"
        return _fetch_json(url, referer="https://www.cls.cn/")
    if provider == "ths":
        url = "https://news.10jqka.com.cn/tapp/news/push/stock?" + urllib.parse.urlencode({"page": "1", "tag": "", "track": "website"})
        return _fetch_json(url, referer="https://news.10jqka.com.cn/")
    raise ValueError(f"unsupported_provider:{provider}")


def _provider_rows(provider: str, body: Any) -> list[dict[str, Any]]:
    if not isinstance(body, dict):
        raise ValueError("payload_not_object")
    if provider == "eastmoney":
        if body.get("code") not in (0, "0", 1, "1"):
            raise ValueError(f"eastmoney_code:{body.get('code')}")
        data = body.get("data") if isinstance(body.get("data"), dict) else {}
        rows = data.get("fastNewsList", [])
    elif provider == "sina":
        result = body.get("result")
        if not isinstance(result, dict):
            raise ValueError("sina_result_missing")
        state = result.get("status")
        if isinstance(state, dict) and state.get("code") not in (0, "0"):
            raise ValueError(f"sina_code:{state.get('code')}")
        rows = result.get("data", [])
    elif provider == "cls":
        if body.get("errno") not in (0, "0"):
            raise ValueError(f"cls_errno:{body.get('errno')}")
        data = body.get("data") if isinstance(body.get("data"), dict) else {}
        rows = data.get("roll_data", [])
    else:
        data = body.get("data")
        rows = (data.get("list") or data.get("data") or []) if isinstance(data, dict) else data if isinstance(data, list) else body.get("list", [])
    if not isinstance(rows, list):
        raise ValueError(f"{provider}_rows_missing")
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        title = _clean(row.get("title") or row.get("name") or row.get("brief") or row.get("content"))
        content = _clean(row.get("summary") or row.get("brief") or row.get("intro") or row.get("content"))
        published = _source_time(row.get("showTime") or row.get("ctime") or row.get("time") or row.get("intime") or row.get("publish_time"))
        if not title and not content:
            continue
        item: dict[str, Any] = {"provider": provider, "title": title or content[:120], "content": content, "source_timestamp": published}
        url = row.get("url") or row.get("wapurl") or row.get("link")
        if url:
            item["url"] = str(url).replace("\\/", "/")
        if isinstance(row.get("stockList"), list):
            item["stock_list"] = row["stockList"]
        normalized.append(item)
    return normalized


def _fetch_provider(provider: str, limit: int) -> dict[str, Any]:
    started = _iso_now()
    try:
        body, meta = _provider_request(provider, limit)
        records = _provider_rows(provider, body)
        return {"provider": provider, "status": "available" if records else "empty", "started_at": started, "finished_at": _iso_now(), "records": records, "record_count": len(records), **meta}
    except Exception as exc:
        return {"provider": provider, "status": "unavailable", "started_at": started, "finished_at": _iso_now(), "records": [], "record_count": 0, "error": f"{type(exc).__name__}: {exc}"}


def _merge_records(providers: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    merged: OrderedDict[tuple[str, str], dict[str, Any]] = OrderedDict()
    for provider, result in providers.items():
        for item in result.get("records", []):
            key = (_clean(item.get("title")), _source_time(item.get("source_timestamp")))
            if key not in merged:
                merged[key] = {**item, "providers": [provider]}
            elif provider not in merged[key]["providers"]:
                merged[key]["providers"].append(provider)
    return sorted(merged.values(), key=lambda item: str(item.get("source_timestamp") or ""), reverse=True)


def fetch_fast_news(limit: int) -> dict:
    params = {
        "client": "web",
        "biz": "web_news_col",
        "fastColumn": "102",
        "pageSize": str(limit),
        "page": "1",
        "sortEnd": "",
        "req_trace": str(int(time.time() * 1000)),
    }
    url = "https://np-weblist.eastmoney.com/comm/web/getFastNewsList?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=25) as response:
        raw = response.read()
        data = json.loads(raw.decode("utf-8-sig"))
        rows = data.get("data", {}).get("fastNewsList", []) if isinstance(data, dict) else []
        if not isinstance(rows, list):
            rows = []
        return {
            "url": url,
            "httpStatus": response.status,
            "contentType": response.headers.get("content-type"),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "providerCode": data.get("code") if isinstance(data, dict) else None,
            "providerMessage": data.get("message") if isinstance(data, dict) else None,
            "records": [
                {
                    "id": item.get("code"),
                    "publishedAt": item.get("showTime"),
                    "title": item.get("title"),
                    "summary": item.get("summary"),
                    "stockList": item.get("stockList") if isinstance(item.get("stockList"), list) else [],
                    "source": "东方财富7x24快讯",
                }
                for item in rows
                if isinstance(item, dict)
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYY-MM-DD 或 YYYYMMDD")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    compact = args.date.replace("-", "")
    if len(compact) != 8 or not compact.isdigit():
        raise SystemExit("--date 必须是 YYYY-MM-DD 或 YYYYMMDD")
    if args.limit < 1 or args.limit > 200:
        raise SystemExit("--limit 必须在 1 到 200 之间")
    date_text = f"{compact[:4]}-{compact[4:6]}-{compact[6:]}"
    providers = {provider: _fetch_provider(provider, args.limit) for provider in ("eastmoney", "sina", "cls", "ths")}
    records = _merge_records(providers)
    same_day = [row for row in records if str(row.get("source_timestamp") or "").startswith(date_text)]
    succeeded = [provider for provider, value in providers.items() if value.get("record_count", 0) > 0]
    failed = {provider: value.get("error", "empty") for provider, value in providers.items() if provider not in succeeded}
    provider_hashes = "|".join(str(value.get("sha256") or "") for value in providers.values())
    payload = {
        "schema": "ZHANGCAI_MULTI_SOURCE_NEWS_SNAPSHOT_V2",
        "date": date_text,
        "requested_date": date_text,
        "source_date": date_text,
        "source": providers.get("eastmoney", {}),
        "source_name": "eastmoney,sina,cls,ths",
        "source_url_or_local_root": "news/" + compact,
        "source_sha256": hashlib.sha256(provider_hashes.encode("utf-8")).hexdigest(),
        "retrieved_at": _iso_now(),
        "fetched_date": datetime.now().astimezone().strftime("%Y-%m-%d"),
        "fetchedAt": _iso_now(),
        "status": "available" if succeeded else "missing",
        "quality": "multi_source" if len(succeeded) >= 2 else "degraded",
        "providers": providers,
        "providers_succeeded": succeeded,
        "provider_records": {name: int(value.get("record_count", 0) or 0) for name, value in providers.items()},
        "records": records,
        "sameDayRecordCount": len(same_day),
        "sameDayProviderRecordCount": {
            name: sum(1 for row in value.get("records", []) if str(row.get("source_timestamp") or "").startswith(date_text))
            for name, value in providers.items()
        },
        "errors": failed,
        "source_policy": "package market_news_providers: eastmoney,sina,cls,ths; source timestamps remain authoritative",
        "error_or_reason": failed,
    }
    day_dir = ROOT / compact
    day_dir.mkdir(parents=True, exist_ok=True)
    output = day_dir / f"multi-source-news-{datetime.now().strftime('%H%M%S')}.json"
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    output.write_text(encoded, encoding="utf-8")
    (ROOT / "latest.json").write_text(encoded, encoding="utf-8")
    print(json.dumps({
        "output": str(output), "status": payload["status"], "quality": payload["quality"],
        "providers_succeeded": succeeded, "provider_records": payload["provider_records"],
        "sameDayRecordCount": payload["sameDayRecordCount"], "errors": failed,
    }, ensure_ascii=False))
    return 0 if payload["status"] == "available" else 2


if __name__ == "__main__":
    raise SystemExit(main())
