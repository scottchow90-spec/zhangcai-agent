#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

import requests

from _request_guard import call_with_retries


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.parts.append(data)

    @property
    def title(self) -> str:
        return re.sub(r"\s+", " ", "".join(self.parts)).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def market_prefix(code: str) -> str:
    if code.startswith("92") or code.startswith(("4", "8")):
        return "bj"
    return "sh" if code.startswith(("5", "6", "9")) else "sz"


def fetch_page(code: str, name: str) -> dict:
    url = f"https://quote.eastmoney.com/{market_prefix(code)}{code}.html"

    def request_page():
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://quote.eastmoney.com/",
                "Cache-Control": "no-cache",
            },
            timeout=12,
        )
        response.raise_for_status()
        return response

    response = call_with_retries(request_page, attempts=2, timeout_seconds=12)
    response.encoding = response.apparent_encoding or response.encoding or "utf-8"
    text = response.text
    parser = TitleParser()
    parser.feed(text)
    title = parser.title
    if code not in title or name not in title:
        raise RuntimeError(f"page_identity_mismatch:{code}:{name}:{title}")
    return {
        "code": code,
        "name": name,
        "url": url,
        "title": title,
        "verified_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "response_sha256": hashlib.sha256(response.content).hexdigest(),
        "response_bytes": len(response.content),
        "http_status": response.status_code,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="生成候选股票当前网页来源回执")
    parser.add_argument("--date", required=True)
    parser.add_argument("--analyzed", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"20\d{6}", args.date):
        raise SystemExit("--date must be YYYYMMDD")
    analyzed_path = Path(args.analyzed).resolve()
    out_path = Path(args.out).resolve()
    analyzed = json.loads(analyzed_path.read_text(encoding="utf-8"))
    picks = analyzed.get("picks") or []
    if not picks:
        raise SystemExit("source evidence blocked: analyzed picks are empty")
    entries = [fetch_page(str(item["code"]), str(item["name"])) for item in picks]
    payload = {
        "status": "PASS",
        "browser_surface": "web_api",
        "source_method": "HTTPS GET with bounded retries",
        "provider": "东方财富行情页",
        "trade_date": args.date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "analyzed_path": str(analyzed_path),
        "analyzed_sha256": sha256_file(analyzed_path),
        "entries": entries,
        "errors": [],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
