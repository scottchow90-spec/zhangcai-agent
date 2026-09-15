from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote as url_quote
from urllib.request import Request, urlopen


CHINA_TZ = timezone(timedelta(hours=8))
TDX_ROOT = Path(r"C:\new_tdx_mock\vipdoc")


def canonical_sha256(payload: object) -> str:
    raw = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def discover_symbols() -> list[str]:
    prefixes = {
        "sh": ("600", "601", "603", "605", "688", "689"),
        "sz": ("000", "001", "002", "003", "300", "301"),
        "bj": ("4", "8", "9"),
    }
    symbols: list[str] = []
    for market, allowed in prefixes.items():
        folder = TDX_ROOT / market / "lday"
        for path in folder.glob(f"{market}*.day"):
            code = path.stem[-6:]
            if re.fullmatch(r"\d{6}", code) and code.startswith(allowed):
                symbols.append(f"{code}.{market.upper()}")
    return sorted(set(symbols))


def normalize_volume_to_shares(
    *, amount: float, raw_volume: float, low: float, high: float
) -> tuple[int, int, float]:
    """Tencent reports normal A shares in lots but some boards in shares."""
    candidates: list[tuple[int, int, float]] = []
    for scale in (1, 100):
        shares = int(round(raw_volume * scale))
        if shares <= 0:
            continue
        average_price = amount / shares
        if low * 0.995 <= average_price <= high * 1.005:
            candidates.append((shares, scale, average_price))
    if len(candidates) != 1:
        raise ValueError(
            f"volume_unit_ambiguous:raw={raw_volume}:amount={amount}:"
            f"low={low}:high={high}:candidates={len(candidates)}"
        )
    return candidates[0]


def fetch_batch(symbols: list[str], trade_date: str) -> tuple[dict[str, dict], str]:
    query_symbols = ",".join(
        f"{symbol.split('.')[1].lower()}{symbol.split('.')[0]}" for symbol in symbols
    )
    request = Request(
        "https://qt.gtimg.cn/q=" + url_quote(query_symbols, safe=","),
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urlopen(request, timeout=20) as response:
        raw = response.read()
    text = raw.decode("gb18030", errors="strict")
    found: dict[str, dict] = {}
    for match in re.finditer(r'v_(sh|sz|bj)(\d{6})="([^"]*)";', text):
        market, code, body = match.groups()
        fields = body.split("~")
        if len(fields) < 39 or fields[2] != code:
            continue
        stamp = fields[30]
        if not stamp.startswith(trade_date):
            continue
        try:
            close = float(fields[3])
            preclose = float(fields[4])
            open_price = float(fields[5])
            high = float(fields[33])
            low = float(fields[34])
            detail = fields[35].split("/")
            amount = float(detail[2])
            raw_volume = float(fields[36])
            volume, volume_scale, average_price = normalize_volume_to_shares(
                amount=amount, raw_volume=raw_volume, low=low, high=high
            )
        except (IndexError, ValueError):
            continue
        if min(close, preclose, open_price, high, low, amount, volume) <= 0:
            continue
        if high < max(open_price, close) or low > min(open_price, close):
            continue
        symbol = f"{code}.{market.upper()}"
        found[symbol] = {
            "code": code,
            "market": market.upper(),
            "symbol": symbol,
            "name": fields[1],
            "trade_date": trade_date,
            "quote_time": stamp,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "preclose": preclose,
            "amount": amount,
            "volume": volume,
            "volume_source_scale": volume_scale,
            "average_price": round(average_price, 6),
        }
    return found, hashlib.sha256(raw).hexdigest()


def fetch_quotes(trade_date: str) -> dict:
    symbols = discover_symbols()
    quotes: dict[str, dict] = {}
    source_hashes: list[str] = []
    failed_batches: list[str] = []
    for start in range(0, len(symbols), 80):
        batch = symbols[start : start + 80]
        last_error = ""
        for attempt in range(3):
            try:
                batch_quotes, raw_hash = fetch_batch(batch, trade_date)
                quotes.update(batch_quotes)
                source_hashes.append(raw_hash)
                last_error = ""
                break
            except Exception as exc:
                last_error = f"{type(exc).__name__}:{exc}"
                time.sleep(0.15 * (attempt + 1))
        if last_error:
            failed_batches.append(f"batch_{start}:{last_error}")
        time.sleep(0.03)
    return {
        "schema": "nana-current-quotes/v2",
        "trade_date": trade_date,
        "fetched_at": datetime.now(CHINA_TZ).isoformat(timespec="seconds"),
        "source": "Tencent qt.gtimg.cn",
        "symbols_discovered": len(symbols),
        "failed_batches": failed_batches,
        "source_hashes": source_hashes,
        "quotes_sha256": canonical_sha256(quotes),
        "quotes": quotes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trade-date", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"20\d{6}", args.trade_date):
        raise SystemExit("invalid --trade-date")
    payload = fetch_quotes(args.trade_date)
    quote_count = len(payload["quotes"])
    if quote_count < 4000:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "trade_date": args.trade_date,
                    "quotes_fetched": quote_count,
                    "failed_batches": payload["failed_batches"],
                },
                ensure_ascii=False,
            )
        )
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "trade_date": args.trade_date,
                "quotes_fetched": quote_count,
                "failed_batches": payload["failed_batches"],
                "quotes_sha256": payload["quotes_sha256"],
                "output": str(args.output.resolve()),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
