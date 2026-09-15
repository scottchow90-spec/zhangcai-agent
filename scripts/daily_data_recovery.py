#!/usr/bin/env python3
"""把缺失的交易日日线写入应用可写的降级层。

TDX .day 是主真值，但它属于外部安装目录，未来 EXE 可能无法连接或写入。
本脚本不修改 TDX 源目录：只把通过公开接口明确返回的目标交易日 OHLCV 写入
app-data/market/daily/fallback/<YYYYMMDD>/，并维护一个按股票/日期索引的
daily-data-index.json。这样查询和 Harness 可以在 TDX 不可用时继续使用已核验
的降级记录，同时不会把降级数据伪装成 TDX 全量历史。

公开源顺序：
1. 东方财富 push2his（若网络可达，提供成交额）；
2. 腾讯公开 fqkline（提供未复权 OHLCV，成交额可能为空）。
只有日期完全匹配的记录才会落盘；缺字段、跨日或网络失败均保留为缺口。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APP_ROOT = Path(os.environ.get("ZHANGCAI_APP_ROOT", Path(__file__).resolve().parents[1]))
DATA_ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR", APP_ROOT / "app-data"))
TDX_ROOT = Path(os.environ.get("ZHANGCAI_TDX_ROOT", r"C:\new_tdx_mock"))
TDX_INDEX_FILE = DATA_ROOT / "market" / "daily" / "index" / "tdx-symbol-index.json"
DAILY_INDEX_FILE = DATA_ROOT / "market" / "daily" / "index" / "daily-data-index.json"
FALLBACK_ROOT = DATA_ROOT / "market" / "daily" / "fallback"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalize_code(raw: str) -> tuple[str, str] | None:
    text = str(raw or "").strip().upper()
    market = ""
    number = ""
    if "." in text:
        number, market = text.split(".", 1)
    elif text[:2] in {"SH", "SZ", "BJ"}:
        market, number = text[:2], text[2:]
    else:
        number = text
        if number.startswith("92"):
            market = "BJ"
        elif number.startswith(("6", "68")):
            market = "SH"
        elif number.startswith(("4", "8")):
            market = "BJ"
        else:
            market = "SZ"
    if len(number) != 6 or not number.isdigit() or market not in {"SH", "SZ", "BJ"}:
        return None
    return number, market


def symbol_key(code: str, market: str) -> str:
    return f"{market.lower()}{code}"


def tdx_path(code: str, market: str) -> Path:
    return TDX_ROOT / "vipdoc" / market.lower() / "lday" / f"{market.lower()}{code}.day"


def latest_tdx_date(path: Path) -> str | None:
    try:
        with path.open("rb") as stream:
            stream.seek(0, os.SEEK_END)
            if stream.tell() < 32:
                return None
            stream.seek(-32, os.SEEK_END)
            value = int.from_bytes(stream.read(4), "little")
            text = str(value)
            return text if len(text) == 8 and text.isdigit() else None
    except OSError:
        return None


def load_symbols(codes: list[str]) -> list[dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for raw in codes:
        normalized = normalize_code(raw)
        if normalized:
            code, market = normalized
            result[symbol_key(code, market)] = {"code": code, "market": market, "symbol": f"{code}.{market}"}
    if not codes:
        cached = read_json(TDX_INDEX_FILE, {})
        for key, item in (cached.get("symbols", {}) if isinstance(cached, dict) else {}).items():
            if not isinstance(item, dict):
                continue
            normalized = normalize_code(item.get("symbol") or key)
            if not normalized:
                continue
            code, market = normalized
            result.setdefault(symbol_key(code, market), {"code": code, "market": market, "symbol": f"{code}.{market}"})
    return sorted(result.values(), key=lambda row: row["symbol"])


def public_request(url: str) -> tuple[dict[str, Any] | list[Any] | None, str, str]:
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (ZhangcaiAgent/1.0)",
        "Referer": "https://quote.eastmoney.com/",
        "Accept": "application/json,text/plain,*/*",
        "Connection": "close",
    })
    with urllib.request.urlopen(request, timeout=15) as response:
        raw = response.read()
    payload = json.loads(raw.decode("utf-8-sig"))
    return payload, url, sha256_bytes(raw)


def eastmoney_kline(item: dict[str, str], target: str) -> dict[str, Any] | None:
    code, market = item["code"], item["market"]
    secid_market = 1 if market == "SH" else 0
    query = urllib.parse.urlencode({
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f116",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": "101", "fqt": "0", "secid": f"{secid_market}.{code}",
        "beg": target, "end": target, "lmt": "5",
    })
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?{query}"
    try:
        payload, source_url, digest = public_request(url)
        rows = ((payload.get("data") or {}).get("klines") or []) if isinstance(payload, dict) else []
        for raw in rows:
            values = str(raw).split(",")
            if len(values) < 7 or values[0].replace("-", "") != target:
                continue
            numbers = [float(values[index]) for index in range(1, 7)]
            return {
                "date": target, "open": numbers[0], "close": numbers[1],
                "high": numbers[2], "low": numbers[3], "volume": numbers[4],
                "amount": numbers[5], "source": "Eastmoney push2his historical daily kline",
                "source_url": source_url, "source_sha256": digest,
            }
    except Exception:
        return None
    return None


def tencent_kline(item: dict[str, str], target: str) -> dict[str, Any] | None:
    code, market = item["code"], item["market"]
    prefix = market.lower()
    # bfq = 不复权，和 TDX .day 的原始 OHLC 口径更接近；腾讯接口只返回量，
    # 因此 amount 保持 null，并明确记录字段缺失，不用价格乘成交量伪造成交额。
    query = urllib.parse.urlencode({
        "param": f"{prefix}{code},day,{target[:4]}-{target[4:6]}-{target[6:]},{target[:4]}-{target[4:6]}-{target[6:]},5,bfq",
    })
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?{query}"
    try:
        payload, source_url, digest = public_request(url)
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        rows = data.get(f"{prefix}{code}", {}).get("day", [])
        for values in rows if isinstance(rows, list) else []:
            if not isinstance(values, list) or len(values) < 6:
                continue
            if str(values[0]).replace("-", "") != target:
                continue
            numbers = [float(values[index]) for index in range(1, 6)]
            return {
                "date": target, "open": numbers[0], "close": numbers[1],
                "high": numbers[2], "low": numbers[3], "volume": numbers[4],
                "amount": None, "source": "Tencent public fqkline daily (bfq)",
                "source_url": source_url, "source_sha256": digest,
                "missing_fields": ["amount"],
            }
    except Exception:
        return None
    return None


def existing_fallback_rows(item: dict[str, str], target: str) -> list[dict[str, Any]]:
    file = FALLBACK_ROOT / target / f"{symbol_key(item['code'], item['market'])}.jsonl"
    rows: list[dict[str, Any]] = []
    try:
        for line in file.read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            if isinstance(value, dict) and value.get("date") == target:
                rows.append(value)
    except (OSError, ValueError):
        pass
    return rows


def append_fallback(item: dict[str, str], target: str, bar: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    folder = FALLBACK_ROOT / target
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / f"{symbol_key(item['code'], item['market'])}.jsonl"
    row = {
        "schema": "ZHANGCAI_PUBLIC_DAILY_BAR_V1",
        "symbol": symbol_key(item["code"], item["market"]),
        "code": item["code"], "market": item["market"], "date": bar["date"],
        "open": bar["open"], "high": bar["high"], "low": bar["low"],
        "close": bar["close"], "volume": bar["volume"], "amount": bar.get("amount"),
        "source": bar["source"], "source_url": bar["source_url"],
        "source_date": bar["date"], "retrieved_at": now_iso(),
        "source_sha256": bar.get("source_sha256", ""),
        "status": "degraded", "missing_fields": bar.get("missing_fields", []),
        "degradation": "public_daily_fallback; amount unavailable" if bar.get("amount") is None else "public_daily_fallback",
    }
    lines = []
    try:
        lines = file.read_text(encoding="utf-8").splitlines()
    except OSError:
        pass
    old_rows = []
    for line in lines:
        try:
            value = json.loads(line)
            if isinstance(value, dict) and value.get("date") != row["date"]:
                old_rows.append(value)
        except ValueError:
            continue
    old_rows.append(row)
    old_rows.sort(key=lambda value: str(value.get("date") or ""))
    temp = file.with_suffix(file.suffix + ".tmp")
    temp.write_text("".join(json.dumps(value, ensure_ascii=False) + "\n" for value in old_rows), encoding="utf-8")
    temp.replace(file)
    return file, row


def load_index() -> dict[str, Any]:
    value = read_json(DAILY_INDEX_FILE, {})
    if not isinstance(value, dict) or value.get("schema") != "ZHANGCAI_DAILY_DATA_INDEX_V1":
        return {"schema": "ZHANGCAI_DAILY_DATA_INDEX_V1", "generated_at": now_iso(), "source_precedence": ["tdx_local_day", "tdx_archive", "public_daily_fallback"], "dates": {}, "symbols": {}}
    value.setdefault("dates", {})
    value.setdefault("symbols", {})
    return value


def rebuild_index(index: dict[str, Any], target: str, requested: int, fetched: int, failed: int, tdx_available: bool) -> None:
    date_info = index["dates"].setdefault(target, {})
    # A no-op recovery pass (all TDX rows already cover the target date) must
    # not erase the previous public fallback audit counts.
    if requested == 0 and fetched == 0 and failed == 0 and date_info:
        requested = int(date_info.get("requested_count") or 0)
        fetched = int(date_info.get("fetched_count") or 0)
        failed = int(date_info.get("failed_count") or 0)
    fallback_status = "available" if failed == 0 else ("degraded" if fetched else "blocked")
    date_info.update({
        "trade_date": target, "updated_at": now_iso(), "requested_count": requested,
        "fetched_count": fetched, "failed_count": failed,
        "tdx_available": tdx_available, "fallback_root": f"market/daily/fallback/{target}/",
        "fallback_status": fallback_status,
    })
    tdx_cached = read_json(TDX_INDEX_FILE, {})
    tdx_symbols = tdx_cached.get("symbols", {}) if isinstance(tdx_cached, dict) else {}
    daily_manifest = read_json(DATA_ROOT / "status" / "tdx-daily-history.json", {})
    tdx_archive_file = daily_manifest.get("file", "") if isinstance(daily_manifest, dict) else ""
    tdx_archive_date = str(daily_manifest.get("trade_date") or "") if isinstance(daily_manifest, dict) else ""
    tdx_archive_path = DATA_ROOT / str(tdx_archive_file) if tdx_archive_file else DATA_ROOT / "__missing__"
    tdx_day_manifest = read_json(DATA_ROOT / "market" / "daily" / target / "manifest.json", {})
    tdx_archive_target_available = bool(
        isinstance(daily_manifest, dict)
        and daily_manifest.get("schema") == "ZHANGCAI_TDX_DAILY_ARCHIVE_V1"
        and daily_manifest.get("status") == "available"
        and tdx_archive_date == target
        and tdx_archive_path.is_file()
        and isinstance(tdx_day_manifest, dict)
        and tdx_day_manifest.get("schema") == "ZHANGCAI_TDX_DAILY_ARCHIVE_V1"
        and tdx_day_manifest.get("trade_date") == target
    )
    date_info.update({
        "tdx_archive_status": "available" if tdx_archive_target_available else ("stale" if tdx_archive_date else "missing"),
        "tdx_archive_trade_date": tdx_archive_date,
        "tdx_archive_path": tdx_archive_file,
        "tdx_archive_symbols": int(daily_manifest.get("current_trade_date_symbols") or 0) if isinstance(daily_manifest, dict) else 0,
        "tdx_archive_bar_records": int(daily_manifest.get("bar_records") or 0) if isinstance(daily_manifest, dict) else 0,
    })
    # Remove stale TDX-only fields for securities that disappeared from the
    # current source index, while retaining their public fallback history.
    for key, entry in (index.get("symbols", {}) if isinstance(index.get("symbols"), dict) else {}).items():
        if key in tdx_symbols or not isinstance(entry, dict):
            continue
        for field in ("tdx_source_root", "tdx_source_file", "tdx_record_count", "tdx_first_date", "tdx_last_date", "tdx_status", "tdx_archive_path"):
            entry.pop(field, None)
    for key, item in tdx_symbols.items():
        if not isinstance(item, dict):
            continue
        entry = index["symbols"].setdefault(key, {
            "symbol": item.get("symbol", key), "code": item.get("code", key[-6:]),
            "market": item.get("market", key[:2].upper()),
        })
        source_file = str(item.get("file") or "")
        entry.update({
            "tdx_source_root": tdx_cached.get("source_root", str(TDX_ROOT)) if isinstance(tdx_cached, dict) else str(TDX_ROOT),
            "tdx_source_file": source_file,
            "tdx_record_count": int(item.get("record_count") or 0),
            "tdx_first_date": item.get("first_date", ""), "tdx_last_date": item.get("last_date", ""),
            "tdx_status": "available" if tdx_available else "unavailable",
            "tdx_archive_path": tdx_archive_file,
        })
    # Re-scan small fallback files only. This keeps the index authoritative even
    # if a previous run was interrupted after writing a bar but before its index.
    target_fallback_symbols = 0
    target_fallback_records = 0
    for date_dir in FALLBACK_ROOT.iterdir() if FALLBACK_ROOT.is_dir() else []:
        if not date_dir.is_dir() or not date_dir.name.isdigit():
            continue
        for file in date_dir.glob("*.jsonl"):
            try:
                rows = [json.loads(line) for line in file.read_text(encoding="utf-8").splitlines() if line.strip()]
            except (OSError, ValueError):
                continue
            if not rows:
                continue
            if date_dir.name == target:
                target_fallback_symbols += 1
                target_fallback_records += len(rows)
            last = rows[-1]
            symbol = str(last.get("symbol") or file.stem)
            entry = index["symbols"].setdefault(symbol, {"symbol": symbol, "code": last.get("code", symbol[-6:]), "market": last.get("market", symbol[:2].upper())})
            dates = [str(row.get("date")) for row in rows if row.get("date")]
            entry.update({
                "fallback_records": len(rows), "fallback_first_date": min(dates) if dates else "",
                "fallback_last_date": max(dates) if dates else "", "fallback_path": f"market/daily/fallback/{date_dir.name}/{file.name}",
                "fallback_status": "degraded", "fallback_missing_fields": sorted({field for row in rows for field in (row.get("missing_fields") or [])}),
            })
    date_info.update({"available_fallback_symbols": target_fallback_symbols, "available_fallback_records": target_fallback_records})
    # The date-level status describes whether the date is usable overall.
    # A complete TDX archive must not be downgraded merely because an
    # optional public fallback request missed one symbol.  Keep that separate
    # in fallback_status for Harness diagnostics.
    date_info["status"] = "available" if tdx_archive_target_available else fallback_status
    index["generated_at"] = now_iso()
    summary = {
        "symbol_count": len(index["symbols"]),
        "tdx_symbol_count": sum(1 for row in index["symbols"].values() if row.get("tdx_record_count")),
        "tdx_record_count": sum(int(row.get("tdx_record_count") or 0) for row in index["symbols"].values()),
        "fallback_symbol_count": sum(1 for row in index["symbols"].values() if row.get("fallback_records")),
        "fallback_record_count": sum(int(row.get("fallback_records") or 0) for row in index["symbols"].values()),
        "date_count": len(index["dates"]),
    }
    index["summary"] = summary
    write_json(DAILY_INDEX_FILE, index)
    date_index = DATA_ROOT / "market" / "daily" / target / "daily-data-index.json"
    write_json(date_index, {"schema": "ZHANGCAI_DAILY_DATA_INDEX_DATE_V1", "trade_date": target, "generated_at": index["generated_at"], "summary": summary, "date": index["dates"].get(target, {}), "source_precedence": index["source_precedence"], "index_path": "market/daily/index/daily-data-index.json"})
    day_manifest_path = DATA_ROOT / "market" / "daily" / target / "manifest.json"
    day_manifest = read_json(day_manifest_path, {})
    if isinstance(day_manifest, dict) and day_manifest:
        day_manifest.update({
            "daily_data_index": "market/daily/index/daily-data-index.json",
            "daily_date_index": f"market/daily/{target}/daily-data-index.json",
            "fallback_root": f"market/daily/fallback/{target}/",
            "fallback_records": summary.get("fallback_record_count", 0),
            "fallback_symbols": summary.get("fallback_symbol_count", 0),
        })
        write_json(day_manifest_path, day_manifest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", "--target-date", dest="date", required=True, help="目标交易日 YYYYMMDD")
    parser.add_argument("--codes", default="", help="逗号/空格分隔的代码；不传则读取缓存股票索引")
    parser.add_argument("--max-symbols", type=int, default=0, help="断开 TDX 时限制公开源请求数量；0 表示默认上限 200")
    parser.add_argument("--force", action="store_true", help="即使 TDX 已有目标日，也强制检查/写入公开层")
    parser.add_argument("--sleep-ms", type=int, default=80, help="公开接口请求间隔，避免连续请求过快")
    args = parser.parse_args()
    target = str(args.date).replace("-", "")
    if len(target) != 8 or not target.isdigit():
        raise SystemExit("--date 必须是 YYYYMMDD")
    explicit_codes = [part for part in str(args.codes).replace(",", " ").split() if part]
    symbols = load_symbols(explicit_codes)
    tdx_available = TDX_ROOT.is_dir() and any((TDX_ROOT / "vipdoc" / market / "lday").is_dir() for market in ("sh", "sz", "bj"))
    max_symbols = int(args.max_symbols or 0)
    if not tdx_available and not explicit_codes:
        max_symbols = max_symbols or int(os.environ.get("ZHANGCAI_PUBLIC_FALLBACK_MAX_SYMBOLS", "200"))
    if not explicit_codes and not max_symbols:
        # A present but stale TDX directory can mean the client is closed or
        # its download did not complete. Do not issue thousands of public
        # requests in one scheduler tick; callers can continue in batches.
        candidates = [item for item in symbols if args.force or latest_tdx_date(tdx_path(item["code"], item["market"])) != target]
        if len(candidates) > 200:
            symbols = candidates
            max_symbols = int(os.environ.get("ZHANGCAI_PUBLIC_FALLBACK_MAX_SYMBOLS", "200"))
    if max_symbols > 0:
        symbols = symbols[:max_symbols]
    requested = 0
    fetched = 0
    failed = 0
    results: list[dict[str, Any]] = []
    for item in symbols:
        path = tdx_path(item["code"], item["market"])
        if not args.force and latest_tdx_date(path) == target:
            continue
        requested += 1
        if existing_fallback_rows(item, target):
            results.append({"symbol": item["symbol"], "status": "already_available", "source": "public_daily_fallback"})
            fetched += 1
            continue
        bar = eastmoney_kline(item, target) or tencent_kline(item, target)
        if bar is None:
            failed += 1
            results.append({"symbol": item["symbol"], "status": "missing", "reason": "公开源未返回目标交易日或请求失败"})
            continue
        file, row = append_fallback(item, target, bar)
        fetched += 1
        results.append({"symbol": item["symbol"], "status": "written", "path": str(file), "source": row["source"], "missing_fields": row["missing_fields"]})
        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000)
    index = load_index()
    rebuild_index(index, target, requested, fetched, failed, tdx_available)
    report = {
        "schema": "ZHANGCAI_PUBLIC_DAILY_RECOVERY_V1", "status": "available" if failed == 0 else ("degraded" if fetched else "blocked"),
        "trade_date": target, "tdx_available": tdx_available, "requested_count": requested,
        "fetched_count": fetched, "failed_count": failed, "source_precedence": index["source_precedence"],
        "daily_index": str(DAILY_INDEX_FILE), "fallback_root": str(FALLBACK_ROOT / target),
        "requested_scope": "explicit_codes" if explicit_codes else "cached_tdx_symbol_index",
        "cap_applied": max_symbols if max_symbols else None, "results": results,
        "retrieved_at": now_iso(),
    }
    report_file = DATA_ROOT / "runtime" / f"daily-recovery-{target}-{datetime.now().strftime('%H%M%S')}.json"
    report["report"] = str(report_file)
    write_json(report_file, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
