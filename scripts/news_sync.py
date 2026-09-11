#!/usr/bin/env python3
"""Persist a daily, traceable public A-share news snapshot for the local runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR", Path(__file__).resolve().parents[1] / "data")) / "news"
UA = {
    "User-Agent": "Mozilla/5.0 (ZhangcaiAgent/1.0)",
    "Accept": "application/json,text/plain,*/*",
}


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
    try:
        source = fetch_fast_news(args.limit)
        same_day = [x for x in source["records"] if str(x.get("publishedAt") or "").startswith(date_text)]
        payload = {
            "schema": "ZHANGCAI_NEWS_SNAPSHOT_V1",
            "date": date_text,
            "fetchedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "available" if source["providerCode"] in {0, "0", 1, "1"} and source["records"] else "missing",
            "source": source,
            "sameDayRecordCount": len(same_day),
        }
    except Exception as exc:
        payload = {
            "schema": "ZHANGCAI_NEWS_SNAPSHOT_V1",
            "date": date_text,
            "fetchedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "missing",
            "source": {"name": "东方财富7x24快讯", "error": f"{type(exc).__name__}: {exc}"},
            "sameDayRecordCount": 0,
        }
    day_dir = ROOT / compact
    day_dir.mkdir(parents=True, exist_ok=True)
    output = day_dir / f"eastmoney-fast-news-{datetime.now().strftime('%H%M%S')}.json"
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    output.write_text(encoded, encoding="utf-8")
    (ROOT / "latest.json").write_text(encoded, encoding="utf-8")
    print(json.dumps({"output": str(output), "status": payload["status"], "sameDayRecordCount": payload["sameDayRecordCount"]}, ensure_ascii=False))
    return 0 if payload["status"] == "available" else 2


if __name__ == "__main__":
    raise SystemExit(main())
