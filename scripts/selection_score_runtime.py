#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""3003 本地策略评分运行时。

这个入口只读取 app-data 中已经落盘的通达信日线和网页候选，不访问未来数据，
并调用三套原始技能包中的真实评分函数：

* 黄金点火 V8: embedded/golden-ignition-v8/scripts/run_v8.py
* 短线爆发力 V5: embedded/short-burst-score-v5/scripts/lhbpost/core.py
* 量化生产 V6.5: embedded/quant-production-v65/scripts/engine.py

它不是把涨幅/成交额重新命名为评分。辅助数据缺失时仍返回原始引擎算出的数值，
同时把缺失项和降级状态写入回执，禁止把研究适配结果冒充生产授权结果。
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import struct
import sys
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# The bridge reads child-process stdout as UTF-8. Windows Python may otherwise
# choose the active Chinese code page, which turns strategy fields into
# mojibake in persisted receipts and browser tables.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


APP_ROOT = Path(os.environ.get("ZHANGCAI_APP_ROOT") or Path(__file__).resolve().parents[1])
DATA_ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR") or APP_ROOT / "app-data")
EMBEDDED_ROOT = APP_ROOT / "harness-skills" / "embedded"


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def load_exact_date_market_fields(target_date: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """读取已经落盘且日期严格匹配的公开行情补充字段。

    TDX .day 文件没有换手率和流通市值。量化 V6.5 的量能门控又明确要求
    turnover，因此这里仅从同一交易日的本地公开快照补齐，不调用实时接口，
    也不把成交额/价格推算成换手率，避免历史评分发生未来数据泄漏。
    """
    compact = "".join(ch for ch in str(target_date or "") if ch.isdigit())[:8]
    if len(compact) != 8:
        return {}, {"status": "missing", "reason": "invalid_date", "records": 0}
    iso = f"{compact[:4]}-{compact[4:6]}-{compact[6:]}"
    public_root = DATA_ROOT / "public"
    paths: List[Path] = []
    dated_dir = public_root / compact
    if dated_dir.exists():
        paths.extend(sorted(dated_dir.glob("market-*.json")))
    limit_up = public_root / "limit-up" / f"{iso}.json"
    if limit_up.exists():
        paths.append(limit_up)
    latest = public_root / "latest.json"
    if latest.exists():
        paths.append(latest)

    fields: Dict[str, Dict[str, Any]] = {}
    used: List[str] = []

    def add(item: Any, source: Path, provider: str) -> None:
        if not isinstance(item, dict):
            return
        code = code_only(item.get("c") or item.get("代码") or item.get("code"))
        if not code or code == "000000":
            return
        turnover = number(item.get("hs") if item.get("hs") is not None else item.get("换手率"))
        if turnover is None:
            turnover = number(item.get("turnover_pct") if item.get("turnover_pct") is not None else item.get("turnover"))
        if turnover is None:
            return
        fields[code] = {
            "turnover_pct": float(turnover),
            "float_market_cap": number(item.get("ltsz") if item.get("ltsz") is not None else item.get("流通市值")),
            "total_market_cap": number(item.get("tshare") if item.get("tshare") is not None else item.get("总市值")),
            "source": str(source),
            "provider": provider,
            "source_date": iso,
        }

    for path in paths:
        payload = load_json(path, {}) or {}
        if not isinstance(payload, dict):
            continue
        payload_date = str(payload.get("date") or payload.get("source_date") or "")[:10]
        if payload_date and payload_date != iso:
            continue
        sources = payload.get("sources") if isinstance(payload.get("sources"), dict) else {}
        east = sources.get("eastmoneyLimitUp") if isinstance(sources, dict) else None
        east_data = east.get("data") if isinstance(east, dict) else None
        east_rows = east_data.get("data", {}).get("pool", []) if isinstance(east_data, dict) and isinstance(east_data.get("data"), dict) else []
        for item in east_rows if isinstance(east_rows, list) else []:
            add(item, path, "eastmoney_limit_up_same_day")
        ak = sources.get("akshareLimitUpPool") if isinstance(sources, dict) else None
        ak_data = ak.get("data") if isinstance(ak, dict) else None
        ak_rows = ak_data.get("records", []) if isinstance(ak_data, dict) else []
        for item in ak_rows if isinstance(ak_rows, list) else []:
            add(item, path, "akshare_limit_up_same_day")

        # limit-up/<date>.json is an archive with the same sources shape, but
        # accept a flat records/pool shape too for future fallback archives.
        for key in ("records", "pool"):
            rows = payload.get(key)
            for item in rows if isinstance(rows, list) else []:
                add(item, path, "public_same_day_archive")
        if fields:
            used.append(str(path))

    return fields, {
        "status": "available" if fields else "missing",
        "date": iso,
        "records": len(fields),
        "paths": used,
        "kind": "same-day-public-snapshot",
    }


def number(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except Exception:
        return default


def finite(value: Any, default: float = 0.0) -> float:
    result = number(value)
    return default if result is None else result


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def code_only(value: Any) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits[-6:].zfill(6)


def iso_date(value: Any) -> str:
    raw = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(raw) == 8:
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return str(value or "")[:10]


def tdx_symbol(code: str, market: str = "") -> str:
    venue = str(market or "").lower()
    if venue not in {"sh", "sz", "bj"}:
        venue = "sh" if code.startswith(("5", "6", "9")) else "sz"
    return venue + code


def load_tdx_history(target_date: str, codes: Iterable[str]) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Any]]:
    """按日期加载本地 TDX JSONL。只保留请求标的和上证/深证指数。"""
    requested = "".join(ch for ch in str(target_date or "") if ch.isdigit())[:8]
    wanted = {code_only(x) for x in codes}
    wanted.update({"000001", "399001", "399006"})
    wanted_symbols = set()
    for code in wanted:
        if code == "000001":
            wanted_symbols.add("sh000001")
        elif code in {"399001", "399006"}:
            wanted_symbols.add("sz" + code)
        else:
            wanted_symbols.add(tdx_symbol(code))

    # 优先读取 TDX 原生 .day。tdx-bars.jsonl 是完整归档文件，当前约数 GB，
    # 不应为一次 30 只候选评分把整份归档从头扫描；.day 读取只 seek 最近 260 根。
    tdx_root = Path(os.environ.get("ZHANGCAI_TDX_ROOT") or os.environ.get("TDX_ROOT") or r"C:\new_tdx_mock")
    day_record = struct.Struct("<IIIIIfII")
    binary_grouped: Dict[str, List[Dict[str, Any]]] = {}
    binary_paths: List[str] = []
    binary_records = 0

    def binary_path(symbol: str) -> Path:
        market = symbol[:2]
        candidates = [
            tdx_root / "vipdoc" / market / "lday" / f"{symbol}.day",
            tdx_root / "vipdoc" / "xinzeng" / market / "lday" / f"{symbol}.day",
            tdx_root / "vipdoc" / "xinzeng" / f"{symbol}.day",
        ]
        return next((item for item in candidates if item.exists()), candidates[0])

    def read_binary(symbol: str) -> List[Dict[str, Any]]:
        file = binary_path(symbol)
        if not file.exists():
            return []
        count = file.stat().st_size // day_record.size
        if count <= 0:
            return []
        rows: List[Dict[str, Any]] = []
        with file.open("rb") as handle:
            handle.seek(max(0, count - 320) * day_record.size)
            for _ in range(min(count, 320)):
                chunk = handle.read(day_record.size)
                if len(chunk) != day_record.size:
                    break
                date_i, open_i, high_i, low_i, close_i, amount, volume, _unused = day_record.unpack(chunk)
                date_value = str(date_i)
                if not date_value.isdigit() or len(date_value) != 8 or (requested and date_value > requested):
                    continue
                rows.append({
                    "date": iso_date(date_value),
                    "open": open_i / 100.0,
                    "high": high_i / 100.0,
                    "low": low_i / 100.0,
                    "close": close_i / 100.0,
                    "volume": float(volume),
                    "amount": float(amount),
                })
        rows.sort(key=lambda item: str(item.get("date") or ""))
        return rows

    for symbol in sorted(wanted_symbols):
        rows = read_binary(symbol)
        if rows:
            binary_grouped[symbol] = rows
            binary_paths.append(str(binary_path(symbol)))
            binary_records += len(rows)
    if binary_grouped:
        return binary_grouped, {
            "status": "available",
            "kind": "tdx-native-day",
            "root": str(tdx_root),
            "paths": binary_paths,
            "records": binary_records,
        }

    daily_root = DATA_ROOT / "market" / "daily"
    candidate_dirs = []
    if requested and (daily_root / requested / "tdx-bars.jsonl").exists():
        candidate_dirs.append((requested, daily_root / requested / "tdx-bars.jsonl"))
    try:
        for directory in sorted(daily_root.iterdir(), reverse=True):
            if not directory.is_dir() or not directory.name.isdigit() or directory.name > requested:
                continue
            file = directory / "tdx-bars.jsonl"
            if file.exists() and not any(x[0] == directory.name for x in candidate_dirs):
                candidate_dirs.append((directory.name, file))
    except Exception:
        pass
    if not candidate_dirs:
        return {}, {"status": "missing", "path": str(daily_root), "records": 0}

    chosen_date, source = candidate_dirs[0]
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    records = 0
    try:
        with source.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                try:
                    raw = json.loads(line)
                except Exception:
                    continue
                symbol = str(raw.get("symbol") or "").strip().lower()
                if symbol not in wanted_symbols:
                    continue
                date_value = "".join(ch for ch in str(raw.get("date") or "") if ch.isdigit())[:8]
                if not date_value or (requested and date_value > requested):
                    continue
                row = {
                    "date": iso_date(date_value),
                    "open": finite(raw.get("open")),
                    "high": finite(raw.get("high")),
                    "low": finite(raw.get("low")),
                    "close": finite(raw.get("close")),
                    "volume": finite(raw.get("volume")),
                    "amount": finite(raw.get("amount")),
                }
                grouped[symbol].append(row)
                records += 1
    except Exception as exc:
        return {}, {"status": "error", "path": str(source), "records": records, "error": str(exc)}
    for rows in grouped.values():
        rows.sort(key=lambda item: str(item.get("date") or ""))
    return dict(grouped), {"status": "available", "path": str(source), "date": chosen_date, "records": records}


def load_modules() -> Dict[str, Any]:
    modules: Dict[str, Any] = {}

    def load(name: str, file: Path, extra_path: Optional[Path] = None) -> Any:
        if extra_path and str(extra_path) not in sys.path:
            sys.path.insert(0, str(extra_path))
        spec = importlib.util.spec_from_file_location(name, str(file))
        if not spec or not spec.loader:
            raise RuntimeError(f"无法加载原始策略模块: {file}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    golden_file = EMBEDDED_ROOT / "golden-ignition-v8" / "scripts" / "run_v8.py"
    burst_root = EMBEDDED_ROOT / "short-burst-score-v5"
    quant_root = EMBEDDED_ROOT / "quant-production-v65"
    modules["golden"] = load("embedded_golden_v8", golden_file)
    modules["burst"] = load("embedded_short_burst_core", burst_root / "scripts" / "lhbpost" / "core.py")
    modules["quant"] = load("embedded_quant_engine", quant_root / "scripts" / "engine.py", quant_root / "scripts")
    return modules


def bars_for(grouped: Dict[str, List[Dict[str, Any]]], code: str, market: str) -> List[Dict[str, Any]]:
    rows = grouped.get(tdx_symbol(code, market)) or []
    out: List[Dict[str, Any]] = []
    previous: Optional[float] = None
    for row in rows:
        item = dict(row)
        close = number(item.get("close"))
        if previous is not None and close is not None:
            item["change"] = close - previous
            item["pct_change"] = (close / previous - 1.0) * 100.0 if previous else 0.0
        out.append(item)
        if close is not None and close > 0:
            previous = close
    return out


def industry_identity(stock: Dict[str, Any]) -> str:
    """Return the stable TDX industry key used by the local adapter.

    The web snapshot carries both the TDX code and the display name.  The
    code is preferred because names can be changed by a vendor, while a
    name-only fallback keeps older snapshots usable.
    """
    code = str(stock.get("industryCode") or stock.get("industry_code") or "").strip()
    name = str(stock.get("industryName") or stock.get("industry") or stock.get("sectorName") or "").strip()
    if code and code.upper() not in {"UNKNOWN", "N/A", "NONE"}:
        return code
    return f"name:{name}" if name else "name:未知行业"


def _compact_industry_member(stock: Dict[str, Any], target_date: str) -> Dict[str, Any]:
    """Keep only same-day member fields consumed by the V6.3 industry engine."""
    return {
        "code": code_only(stock.get("code")),
        "name": str(stock.get("name") or stock.get("code") or ""),
        "market": str(stock.get("market") or ""),
        "date": str(stock.get("date") or target_date),
        "pct": number(stock.get("pct")),
        "amount": number(stock.get("amount"), 0.0),
        "limitPct": number(stock.get("limitPct"), 10.0),
        "limitStreak": number(stock.get("limitStreak"), 0.0),
    }


def aggregate_industry_bars(
    members: List[Dict[str, Any]],
    grouped: Dict[str, List[Dict[str, Any]]],
    target_date: str,
) -> Tuple[List[Dict[str, Any]], int]:
    """Build a deterministic equal-weight TDX industry index from local bars.

    No price or amount is invented here.  Each constituent contributes its
    actual TDX bars, normalized to 100 at the beginning of the retained
    window so high-priced shares cannot dominate the industry index.  The
    original V6.3 industry engine remains unchanged and receives ordinary
    OHLC/amount bars.
    """
    by_date: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: {"close": [], "high": [], "low": [], "open": [], "amount": []})
    usable_members = 0
    for member in members:
        code = code_only(member.get("code"))
        if not code:
            continue
        bars = bars_for(grouped, code, str(member.get("market") or ""))
        usable = [x for x in bars if number(x.get("close")) is not None and number(x.get("close")) > 0]
        if len(usable) < 21:
            continue
        base = number(usable[0].get("close"))
        if base is None or base <= 0:
            continue
        usable_members += 1
        for bar in usable:
            day = str(bar.get("date") or "")
            close = number(bar.get("close"))
            if not day or close is None or close <= 0:
                continue
            bucket = by_date[day]
            scale = 100.0 / base
            bucket["close"].append(close * scale)
            bucket["high"].append((number(bar.get("high"), close) or close) * scale)
            bucket["low"].append((number(bar.get("low"), close) or close) * scale)
            bucket["open"].append((number(bar.get("open"), close) or close) * scale)
            bucket["amount"].append(number(bar.get("amount"), 0.0) or 0.0)

    result: List[Dict[str, Any]] = []
    for day in sorted(by_date):
        bucket = by_date[day]
        if not bucket["close"]:
            continue
        result.append({
            "date": day,
            "open": sum(bucket["open"]) / len(bucket["open"]),
            "high": sum(bucket["high"]) / len(bucket["high"]),
            "low": sum(bucket["low"]) / len(bucket["low"]),
            "close": sum(bucket["close"]) / len(bucket["close"]),
            "amount": sum(bucket["amount"]),
            "volume": 0.0,
            "constituent_count": len(bucket["close"]),
        })
    return result, usable_members


def load_same_day_industry_events(target_date: str) -> Tuple[List[Dict[str, Any]], bool, List[str]]:
    """Read only event records whose timestamp is the requested trade date.

    Some older archives were stored under a stale date directory while their
    records were actually from a later day.  A directory name or archive
    ``date`` alone is therefore not sufficient evidence for V6.5.
    """
    iso = iso_date(target_date)
    paths: List[Path] = []
    dated = DATA_ROOT / "news" / str(target_date)
    if dated.exists():
        paths.extend(sorted(dated.glob("*.json")))
    evidence = DATA_ROOT / "evidence" / "public" / f"news-{iso}.json"
    if evidence.exists():
        paths.append(evidence)
    events: List[Dict[str, Any]] = []
    seen = set()
    covered = False

    def records_from(payload: Any) -> List[Any]:
        if not isinstance(payload, dict):
            return []
        candidates: List[Any] = [payload.get("records")]
        source = payload.get("source")
        if isinstance(source, dict):
            candidates.append(source.get("records"))
        snapshot = payload.get("snapshot")
        if isinstance(snapshot, dict):
            candidates.append(snapshot.get("records"))
            snap_source = snapshot.get("source")
            if isinstance(snap_source, dict):
                candidates.append(snap_source.get("records"))
        for value in candidates:
            if isinstance(value, list):
                return value
        return []

    for path in paths:
        payload = load_json(path, {}) or {}
        if not isinstance(payload, dict):
            continue
        metadata_date = str(payload.get("source_date") or payload.get("date") or "")[:10]
        if metadata_date and metadata_date != iso:
            continue
        records = records_from(payload)
        for item in records:
            if not isinstance(item, dict):
                continue
            timestamp = str(
                item.get("source_timestamp")
                or item.get("publishedAt")
                or item.get("published_at")
                or item.get("time")
                or item.get("date")
                or ""
            )
            if not timestamp.startswith(iso):
                continue
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            key = (title, timestamp)
            if key in seen:
                continue
            seen.add(key)
            events.append({
                "title": title,
                "content": str(item.get("content") or item.get("summary") or ""),
                "time": timestamp,
                "source": str(item.get("source") or item.get("provider") or ""),
            })
        if records and (int(finite(payload.get("sameDayRecordCount"), 0)) > 0 or any(
            str(item.get("source_timestamp") or item.get("publishedAt") or item.get("published_at") or item.get("time") or item.get("date") or "").startswith(iso)
            for item in records if isinstance(item, dict)
        )):
            covered = True
    return events, covered, [str(x) for x in paths]


def prepare_quant_industry_codes(rows: List[Dict[str, Any]], market: Dict[str, Any]) -> List[str]:
    """Expand a quant request with all local members of candidate industries."""
    wanted_keys = {industry_identity(row) for row in rows}
    all_stocks = market.get("allStocks") if isinstance(market.get("allStocks"), list) else []
    codes: List[str] = []
    seen = set()
    for item in all_stocks:
        if not isinstance(item, dict) or industry_identity(item) not in wanted_keys:
            continue
        code = code_only(item.get("code"))
        if len(code) != 6 or code in seen:
            continue
        seen.add(code)
        codes.append(code)
    return codes


def build_quant_industry_contexts(
    rows: List[Dict[str, Any]],
    market: Dict[str, Any],
    grouped: Dict[str, List[Dict[str, Any]]],
    target_date: str,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """Materialize V6.5 industry inputs from the local market/data archive."""
    all_stocks = market.get("allStocks") if isinstance(market.get("allStocks"), list) else []
    row_keys = {industry_identity(row) for row in rows}
    members_by_key: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in all_stocks:
        if not isinstance(item, dict):
            continue
        key = industry_identity(item)
        if key not in row_keys:
            continue
        if item.get("date") and str(item.get("date")) != str(target_date):
            continue
        members_by_key[key].append(_compact_industry_member(item, target_date))
    # Keep a candidate in its own group even if the snapshot has no full
    # universe member mapping; this preserves an explicit missing-data audit.
    for row in rows:
        key = industry_identity(row)
        if not any(x.get("code") == code_only(row.get("code")) for x in members_by_key.get(key, [])):
            members_by_key[key].append(_compact_industry_member(row, target_date))

    events, events_covered, event_paths = load_same_day_industry_events(target_date)
    contexts: Dict[str, Dict[str, Any]] = {}
    usable_contexts = 0
    loaded_members = 0
    for key, members in members_by_key.items():
        name = str(next((x.get("industryName") for x in all_stocks if isinstance(x, dict) and industry_identity(x) == key and x.get("industryName")), ""))
        if not name:
            name = str(next((x.get("industry") for x in rows if industry_identity(x) == key), "未知行业"))
        bars, usable_members = aggregate_industry_bars(members, grouped, target_date)
        loaded_members += usable_members
        if len(bars) >= 21:
            usable_contexts += 1
        contexts[key] = {
            "name": name,
            "bars": bars,
            "constituents": members,
            "events": events,
            "events_covered": events_covered,
            "history_state": [],
            "market_amount_total": number(market.get("amount")),
            "asof": f"{iso_date(target_date)}T18:00:00+08:00",
            "adapter": {
                "source": "local TDX member bars -> equal-weight industry index",
                "target_date": iso_date(target_date),
                "member_count": len(members),
                "member_history_count": usable_members,
                "bar_count": len(bars),
                "event_paths": event_paths,
                "events_covered": events_covered,
            },
        }
    return contexts, {
        "status": "available" if contexts else "missing",
        "context_count": len(contexts),
        "usable_context_count": usable_contexts,
        "member_count": sum(len(x) for x in members_by_key.values()),
        "member_history_count": loaded_members,
        "events_count": len(events),
        "events_covered": events_covered,
        "event_paths": event_paths,
        "kind": "tdx-member-derived-industry-context",
    }


def returns(bars: List[Dict[str, Any]], periods: Iterable[int]) -> Dict[str, Optional[float]]:
    closes = [number(x.get("close")) for x in bars]
    clean = [x for x in closes if x is not None and x > 0]
    result: Dict[str, Optional[float]] = {}
    for period in periods:
        if len(clean) <= period or not clean[-period - 1]:
            result[str(period)] = None
        else:
            result[str(period)] = (clean[-1] / clean[-period - 1] - 1.0) * 100.0
    return result


def mean(values: Iterable[Any]) -> Optional[float]:
    vals = [number(x) for x in values]
    vals = [x for x in vals if x is not None]
    return sum(vals) / len(vals) if vals else None


def percentile(value: Optional[float], values: List[Optional[float]]) -> float:
    usable = sorted(x for x in values if x is not None)
    if value is None or not usable:
        return 0.5
    if len(usable) == 1:
        return 0.5
    return clamp(sum(1 for x in usable if x <= value) / len(usable))


def limit_ratio(code: str, limit_pct: Any) -> float:
    if code.startswith(("300", "301", "688", "689")):
        return 0.20
    return finite(limit_pct, 10.0) / 100.0


def is_limit_up(code: str, bars: List[Dict[str, Any]], index: int, limit_pct: Any) -> bool:
    if index <= 0 or index >= len(bars):
        return False
    prev = number(bars[index - 1].get("close"))
    close = number(bars[index].get("close"))
    high = number(bars[index].get("high"))
    return bool(prev and close and high and close / prev - 1.0 >= limit_ratio(code, limit_pct) * 0.95 and abs(close - high) <= 0.01)


def streak(code: str, bars: List[Dict[str, Any]], limit_pct: Any) -> int:
    result = 0
    for index in range(len(bars) - 1, 0, -1):
        if is_limit_up(code, bars, index, limit_pct):
            result += 1
        else:
            break
    return result


def board_name(code: str) -> str:
    if code.startswith(("300", "301")):
        return "创业板"
    if code.startswith(("688", "689")):
        return "科创板"
    if code.startswith(("4", "8", "920")):
        return "北交所"
    return "主板"


def market_summary(market: Dict[str, Any], grouped: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    indices = {}
    for row in market.get("indices") or []:
        code = code_only(row.get("code"))
        if code:
            indices[code] = finite(row.get("pct"))
    return {
        "up_count": int(finite(market.get("up"))),
        "down_count": int(finite(market.get("down"))),
        "flat_count": int(finite(market.get("flat"))),
        "limit_up_count": len(market.get("tdxLimitUpCodes") or []),
        "limit_down_count": len(market.get("tdxLimitDownCodes") or []),
        "broken_limit_up_count": 0,
        "turnover_total": finite(market.get("amount")),
        "turnover_change_pct": 0.0,
        "index_changes": {
            "000001.SH": indices.get("000001", 0.0),
            "399001.SZ": indices.get("399001", 0.0),
            "399006.SZ": indices.get("399006", 0.0),
        },
    }


def base_metrics(stock: Dict[str, Any], bars: List[Dict[str, Any]], all_features: Dict[str, Dict[str, Optional[float]]]) -> Dict[str, Any]:
    code = code_only(stock.get("code"))
    close = number(bars[-1].get("close")) if bars else number(stock.get("close"), 0.0)
    close = close or 0.0
    high = number(bars[-1].get("high"), close) if bars else close
    low = number(bars[-1].get("low"), close) if bars else close
    opens = [number(x.get("open")) for x in bars]
    closes = [number(x.get("close")) for x in bars]
    volumes = [number(x.get("volume"), 0.0) or 0.0 for x in bars]
    amounts = [number(x.get("amount"), 0.0) or 0.0 for x in bars]
    clean_closes = [x for x in closes if x is not None and x > 0]
    r = returns(bars, (3, 5, 10, 20))
    ma20 = mean(clean_closes[-20:])
    ma60 = mean(clean_closes[-60:])
    ma5 = mean(clean_closes[-5:])
    ma10 = mean(clean_closes[-10:])
    old_ma20 = mean(clean_closes[-25:-5]) if len(clean_closes) >= 25 else None
    ret20 = r.get("20")
    slope = ((ma20 / old_ma20 - 1.0) * 100.0) if ma20 and old_ma20 else None
    prior20 = [x for x in (number(v) for v in [b.get("high") for b in bars[-21:-1]]) if x is not None]
    prev20_high = max(prior20) if prior20 else None
    breakout = clamp(0.5 + ((close / prev20_high - 1.0) * 5.0 if prev20_high else 0.0))
    close_location = clamp((close - (low or close)) / max((high or close) - (low or close), 0.01))
    avg_volume20 = mean(volumes[-21:-1]) if len(volumes) > 1 else None
    vol_ratio = close and ((volumes[-1] / avg_volume20) if avg_volume20 else None)
    volume_health = clamp(1.0 - abs((vol_ratio or 1.0) - 1.5) / 3.0)
    pct = number(stock.get("pct"))
    if pct is None and len(clean_closes) >= 2 and clean_closes[-2]:
        pct = (clean_closes[-1] / clean_closes[-2] - 1.0) * 100.0
    limit_pct = finite(stock.get("limitPct"), 20.0 if code.startswith(("300", "301", "688")) else 10.0)
    current_streak = max(int(finite(stock.get("limitStreak"))), streak(code, bars, limit_pct))
    industry = str(stock.get("industryName") or stock.get("sectorName") or "未知行业")
    return {
        "code": code,
        "name": str(stock.get("name") or code),
        "board": board_name(code),
        "exchange": str(stock.get("market") or "sz").upper(),
        "industry": industry,
        "industry_code": str(stock.get("industryCode") or stock.get("industry_code") or ""),
        "sector_code": str(stock.get("sectorCode") or stock.get("sector_code") or ""),
        "sector": industry,
        "risk_warning": bool("ST" in str(stock.get("name") or "").upper()),
        "is_st": bool("ST" in str(stock.get("name") or "").upper()),
        "delisting_risk": bool("退" in str(stock.get("name") or "")),
        "is_delisting_arrangement": False,
        "change_pct": float(pct or 0.0),
        "turnover": finite(stock.get("amount")),
        "turnover_rate": 0.0,
        "days_return": r,
        "board_streak": current_streak,
        "close_location": close_location,
        "volume_ratio20": float(vol_ratio or 1.0),
        "distance_to_prev20_high_pct": ((close / prev20_high - 1.0) * 100.0) if prev20_high else None,
        "breakout_20d_strength": breakout,
        "rs_20d_pctile": percentile(ret20, [x.get("ret20") for x in all_features.values()]),
        "ma20_slope_pctile": percentile(slope, [x.get("slope") for x in all_features.values()]),
        "close_above_ma20": bool(ma20 and close > ma20),
        "ma5_gt_ma10_gt_ma20": bool(ma5 and ma10 and ma20 and ma5 > ma10 > ma20),
        "ma20_gt_ma60": bool(ma20 and ma60 and ma20 > ma60),
        "volume_health": volume_health,
        "startup_location_health": close_location,
        "sector_rs_5d_pctile": 0.5,
        "sector_activity_pctile": 0.5,
        "risk_penalty": 0.0,
        "market_climax": False,
        "severe_negative_event": False,
        "downward_anomaly_without_reversal": False,
        "three_day_surge_high_climax": False,
        "extreme_volume_inst_sell_weak_relay": False,
        "broken_limit_weak_close": False,
        "recent_ipo_immature": False,
        "new_unlimited": False,
        "independent_catalyst": False,
        "catalyst_public_before_cutoff": False,
        "catalyst_quality": None,
        "lhb": {"listed": False, "absence_verified_in_complete_saved_billboard": False},
        "post_close_events": [],
        "data_quality": "normal",
        "feature_provenance": {
            "source": "app-data/market/daily/<trade_date>/tdx-bars.jsonl",
            "derived_fields": ["change_pct", "days_return", "close_location", "volume_ratio20", "breakout_20d_strength", "board_streak"],
            "not_available": ["turnover_rate", "free_float_mcap", "lhb", "event_feed", "industry_pit", "history_model"],
        },
        "_bars": bars,
        "_opens": opens,
        "_amounts": amounts,
    }


def attach_same_day_market_fields(row: Dict[str, Any], fields: Dict[str, Any]) -> None:
    """把同日公开快照字段接到 V6.5 所消费的最后一根日线上。"""
    if not fields:
        return
    turnover_pct = number(fields.get("turnover_pct"))
    if turnover_pct is None:
        return
    row["turnover_rate"] = float(turnover_pct)
    if fields.get("float_market_cap") is not None:
        row["free_float_mcap"] = fields.get("float_market_cap")
    if fields.get("total_market_cap") is not None:
        row["total_market_cap"] = fields.get("total_market_cap")
    provenance = row.setdefault("feature_provenance", {})
    provenance.setdefault("available", []).extend([
        "turnover_rate",
        "float_market_cap" if fields.get("float_market_cap") is not None else "",
    ])
    provenance["available"] = [x for x in provenance.get("available", []) if x]
    unavailable = provenance.get("not_available") or []
    provenance["not_available"] = [
        x for x in unavailable
        if x not in {"turnover_rate", "free_float_mcap"} or (x == "free_float_mcap" and fields.get("float_market_cap") is None)
    ]
    provenance["turnover_rate_source"] = {
        "provider": fields.get("provider"),
        "path": fields.get("source"),
        "date": fields.get("source_date"),
        "unit": "percent",
    }
    bars = row.get("_bars") or []
    if bars:
        bars[-1]["turnover"] = float(turnover_pct)
        bars[-1]["turnover_source"] = fields.get("source")


def add_sector_features(rows: List[Dict[str, Any]]) -> None:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("sector") or "未知行业")].append(row)
    for members in groups.values():
        members.sort(key=lambda x: (finite(x.get("change_pct")), finite(x.get("turnover"))), reverse=True)
        for index, row in enumerate(members, 1):
            row["sector_core_rank"] = index
            row["sector_leader"] = index == 1
            pcts = [finite(x.get("change_pct")) for x in members]
            row["sector_rs_5d_pctile"] = percentile(finite(row.get("days_return", {}).get("5")), [finite(x.get("days_return", {}).get("5")) for x in members])
            row["sector_activity_pctile"] = percentile(finite(row.get("turnover")), [finite(x.get("turnover")) for x in members])
            row["industry_metrics"] = {
                "day_change_pct": sum(pcts) / len(pcts) if pcts else 0.0,
                "up_ratio": sum(1 for x in pcts if x > 0) / max(len(pcts), 1),
                "limit_up_count": sum(1 for x in pcts if x >= finite(row.get("limitPct"), 10.0) - 0.5),
                "two_plus_board_count": sum(1 for x in members if finite(x.get("board_streak")) >= 2),
                "rel_strength_3d": finite(row.get("days_return", {}).get("3")),
                "rel_strength_5d": finite(row.get("days_return", {}).get("5")),
                "leader_advanced": index == 1,
            }


def cleanup_internal(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): cleanup_internal(v) for k, v in value.items() if not str(k).startswith("_")}
    if isinstance(value, list):
        return [cleanup_internal(v) for v in value]
    if is_dataclass(value):
        return cleanup_internal(asdict(value))
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, float) and (not math.isfinite(value)):
        return None
    return value


def run_golden(mod: Any, rows: List[Dict[str, Any]], date_value: str) -> Tuple[List[Dict[str, Any]], List[str], str]:
    computed: List[Dict[str, Any]] = []
    missing: List[str] = ["通达信 TQ 现场公式证据（V8 数值评分已由原始 run_v8.py 完成；现场回执未接入）"]
    for row in rows:
        golden_rows = []
        for bar in row.get("_bars") or []:
            golden_rows.append({
                "date": datetime.strptime(str(bar["date"]), "%Y-%m-%d").date(),
                "code": row["code"], "name": row["name"], "board": row["board"],
                "open": finite(bar.get("open")), "high": finite(bar.get("high")),
                "low": finite(bar.get("low")), "close": finite(bar.get("close")),
                "volume": finite(bar.get("volume")), "amount": finite(bar.get("amount")),
                "is_st": row.get("is_st", False), "is_delist": row.get("delisting_risk", False),
            })
        if not golden_rows:
            missing.append(f"{row['code']}:无本地日线")
            continue
        values = mod.compute(golden_rows)
        target = [x for x in values if x.get("date").isoformat() == iso_date(date_value)]
        if target:
            item = cleanup_internal(target[-1])
            model_scores = {"A平台": finite(item.get("model_a_score")), "B弱转强": finite(item.get("model_b_score")), "C黄金点火": finite(item.get("model_c_score"))}
            item.update({
                "score": max(model_scores.values()),
                "final_score": max(model_scores.values()),
                "model_scores": model_scores,
                "score_status": "LOCAL_SCORED_DEGRADED",
                "score_source": "原始黄金点火 V8 run_v8.py · 本地通达信日线",
                "missing": ["tdx_tq_formula（V8数值评分不依赖现场TQ；现场公式证据未接入）"],
            })
            computed.append(item)
    computed.sort(key=lambda x: (bool(x.get("final_pass")), finite(x.get("model_c_score")), finite(x.get("model_a_score")), finite(x.get("model_b_score"))), reverse=True)
    return computed, missing, "DEGRADED"


def run_burst(mod: Any, rows: List[Dict[str, Any]], market: Dict[str, Any], grouped: Dict[str, List[Dict[str, Any]]], date_value: str) -> Tuple[List[Dict[str, Any]], List[str], str]:
    snapshot = {
        "trade_date": iso_date(date_value),
        "as_of": iso_date(date_value) + "T18:00:00+08:00",
        "market": market_summary(market, grouped),
        "stocks": [],
        "pipeline": "local-tdx-daily-adapter-v5.0",
        "coverage": {
            "market_full_features": False, "index_daily": True, "industry_pit": False,
            "theme_pit": False, "event_feed": False, "seat_detail": False, "history_model": False,
        },
        "workflow_trace": [
            {"step": "时间截断", "status": "完成", "detail": "本地日线已物理截断至T日"},
            {"step": "历史时点状态", "status": "完成", "detail": "证券名称和板块字段来自本地快照"},
            {"step": "板块与题材", "status": "降级", "detail": "仅使用网页候选中的TDX行业映射，未取得历史时点完整行业/题材成员"},
            {"step": "龙虎榜", "status": "缺失", "detail": "本次未取得完整龙虎榜席位与生命周期数据"},
            {"step": "历史样本", "status": "缺失", "detail": "本次未取得V5样本外历史模型"},
            {"step": "爆发力评分", "status": "执行", "detail": "调用原始core.py六维评分和独立风险扣分"},
        ],
    }
    for row in rows:
        missing = [
            "turnover_rate_pctile", "free_mcap_pctile", "lhb_net_free_float_pctile",
            "lhb_net_impact_pctile", "lhb_participation_pctile", "inst_net_impact_pctile",
            "broker_net_impact_pctile", "buy_sell_balance", "history_model", "industry_pit", "event_feed",
        ]
        item = {k: v for k, v in row.items() if not str(k).startswith("_")}
        item["missing_score_features"] = missing
        snapshot["stocks"].append(item)
    try:
        result = mod.analyze_snapshot(snapshot, config=None, history_model=None)
    except Exception as exc:
        return [], [f"原始V5评分引擎执行失败: {exc}"], "BLOCKED"
    result_rows: List[Dict[str, Any]] = []
    global_missing = [
        "完整V5.0生产快照（market_full_features、industry_pit、event_feed、seat_detail）",
        "龙虎榜席位/机构/营业部资金分项与生命周期",
        "V5历史样本外模型（history_model）",
        "全市场策略扫描（当前按网页条件候选评分）",
    ]
    for item in result.get("results") or []:
        output = cleanup_internal(item)
        output["score"] = output.get("short_burst_score")
        output["final_score"] = output.get("short_burst_score")
        output["model_scores"] = {"short_burst_score": output.get("short_burst_score")}
        output["score_status"] = "LOCAL_SCORED_DEGRADED"
        output["score_source"] = "原始短线爆发力 V5 core.py · 本地通达信日线适配"
        output["missing"] = global_missing + list(output.get("audit", {}).get("raw_stock_feature_provenance", {}).get("not_available", []))
        result_rows.append(output)
    result_rows.sort(key=lambda x: (finite(x.get("short_burst_score")), -len(x.get("hard_reject_reasons") or [])), reverse=True)
    return result_rows, global_missing, "DEGRADED"


def run_quant(
    mod: Any,
    rows: List[Dict[str, Any]],
    market: Dict[str, Any],
    grouped: Dict[str, List[Dict[str, Any]]],
    date_value: str,
    industry_contexts: Optional[Dict[str, Dict[str, Any]]] = None,
    industry_status: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[str], str]:
    quant_root = EMBEDDED_ROOT / "quant-production-v65"
    config = load_json(quant_root / "config" / "production.json", {}) or {}
    params = dict(config.get("model") or {})
    params["native_min_history_bars"] = finite((config.get("data_gates") or {}).get("native_min_history_bars"), 120)
    index_bars = (grouped.get("sh000001") or [])
    if len(index_bars) < 21:
        index_bars = grouped.get("sz399001") or index_bars
    total = max(1, int(finite(market.get("total"), len(rows))))
    breadth = int(finite(market.get("up"))) / max(1, int(finite(market.get("up")) + finite(market.get("down")) + finite(market.get("flat"))))
    industry_contexts = industry_contexts or {}
    industry_status = industry_status or {}
    missing = [
        "V6.5独立第二行情源收盘核验（secondary）",
        "未进入同日公开快照的候选缺少换手率/流通市值精确字段",
        "生产授权门槛与全市场双路共识（当前仅执行原始engine逐股研究评分）",
        "全市场策略扫描（当前按网页条件候选评分）",
    ]
    if not industry_status.get("usable_context_count"):
        missing.append("行业六维历史时点数据（industry bars/constituents/events）")
    elif not industry_status.get("events_covered"):
        missing.append("同日行业消息/事件覆盖（行业硬门保持 UNKNOWN，不用空事件放行）")
    if not any(finite(row.get("turnover_rate")) <= 0 for row in rows):
        missing = [item for item in missing if not item.startswith("未进入同日公开快照")]
    result_rows: List[Dict[str, Any]] = []
    for row in rows:
        stock = {
            "code": row["code"], "name": row["name"], "industry": row.get("industry"),
            "bars": row.get("_bars") or [],
        }
        context = industry_contexts.get(industry_identity(row))
        try:
            # The original engine is intentionally unchanged.  The adapter
            # now supplies a real local industry context when available;
            # missing event coverage continues to propagate UNKNOWN through
            # the engine's existing hard gate.
            evaluated = mod.evaluate_stock(stock, breadth, index_bars, context or [], params)
            output = cleanup_internal(evaluated)
        except Exception as exc:
            output = {
                "code": row["code"], "name": row["name"], "trade_date": iso_date(date_value),
                "model_labels": [], "model_scores": {}, "reject_reasons": [str(exc)],
            }
        scores = output.get("model_scores") or {}
        numeric_scores = [finite(x) for x in scores.values() if number(x) is not None]
        output["score"] = max(numeric_scores) if numeric_scores else None
        output["final_score"] = output.get("score")
        output["primary_score"] = output.get("score")
        output["score_status"] = "LOCAL_SCORED_DEGRADED" if numeric_scores else "INSUFFICIENT_HISTORY"
        output["score_source"] = "原始量化生产 V6.5 engine.py · 本地通达信日线 + 同日公开快照补充"
        states = output.get("model_states") if isinstance(output.get("model_states"), dict) else {}
        triggered = [name for name, state in states.items() if isinstance(state, dict) and state.get("status") == "TRIGGERED"]
        core_candidates = [
            (name, finite(state.get("score")))
            for name, state in states.items()
            if isinstance(state, dict) and state.get("core") is True
        ]
        core_candidates.sort(key=lambda item: item[1], reverse=True)
        output["model_triggered"] = triggered
        output["model_triggered_count"] = len(triggered)
        output["primary_model_candidate"] = core_candidates[0][0] if core_candidates else None
        output["primary_model_status"] = (
            "TRIGGERED" if output.get("primary_model") else
            "PENDING_DATA" if core_candidates else
            "NOT_TRIGGERED"
        )
        output["model_score_basis"] = "四模型分量分数；只有 model_labels 才表示通过全部硬门并触发"
        output["industry_data_status"] = {
            "key": industry_identity(row),
            "context_available": bool(context),
            "bars": len((context or {}).get("bars") or []),
            "constituents": len((context or {}).get("constituents") or []),
            "events_covered": bool((context or {}).get("events_covered")),
            "adapter": (context or {}).get("adapter") or {},
        }
        row_missing = list(missing)
        if finite(row.get("turnover_rate")) > 0:
            row_missing = [item for item in row_missing if not item.startswith("未进入同日公开快照")]
        output["missing"] = row_missing if numeric_scores else row_missing + ["原始引擎要求至少120根历史日线"]
        result_rows.append(output)
    result_rows.sort(key=lambda x: (finite(x.get("score")), finite(x.get("resonance_count"))), reverse=True)
    return result_rows, missing, "DEGRADED"


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "error": "需要评分请求 JSON 路径"}, ensure_ascii=False))
        return 2
    request_path = Path(sys.argv[1])
    request = load_json(request_path, {}) or {}
    strategy_id = str(request.get("strategyId") or request.get("strategy_id") or "")
    date_value = "".join(ch for ch in str(request.get("date") or "") if ch.isdigit())[:8]
    market = load_json(DATA_ROOT / "runtime" / "market-latest.json", {}) or {}
    candidates = request.get("candidates") if isinstance(request.get("candidates"), list) else []
    if not strategy_id or not date_value or not candidates:
        print(json.dumps({"status": "error", "error": "strategyId、date、candidates 均为必填"}, ensure_ascii=False))
        return 2
    codes = [code_only(x.get("code")) for x in candidates if isinstance(x, dict)]
    # V6.5's industry gate is evaluated against the whole candidate
    # industry's local membership, not only the 30 web candidates.  Expand
    # the TDX read set before loading bars so the engine does not receive an
    # empty industry argument by construction.
    industry_codes = prepare_quant_industry_codes(candidates, market) if strategy_id == "quant-production-v65" else []
    grouped, tdx_status = load_tdx_history(date_value, list(dict.fromkeys(codes + industry_codes)))
    same_day_fields, same_day_status = load_exact_date_market_fields(date_value)
    all_features: Dict[str, Dict[str, Optional[float]]] = {}
    base_rows: List[Dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        code = code_only(candidate.get("code"))
        bars = bars_for(grouped, code, str(candidate.get("market") or ""))
        row = base_metrics(candidate, bars, all_features)
        attach_same_day_market_fields(row, same_day_fields.get(code) or {})
        base_rows.append(row)
        rr = row.get("days_return") or {}
        all_features[code] = {
            "ret20": number(rr.get("20")),
            "slope": None,
        }
    # 第二遍补齐斜率百分位，避免用当前候选顺序作为评分。
    for row in base_rows:
        bars = row.get("_bars") or []
        closes = [number(x.get("close")) for x in bars]
        closes = [x for x in closes if x is not None and x > 0]
        ma20 = mean(closes[-20:])
        old = mean(closes[-25:-5]) if len(closes) >= 25 else None
        slope = ((ma20 / old - 1.0) * 100.0) if ma20 and old else None
        all_features[row["code"]]["slope"] = slope
    ret20_values = [x.get("ret20") for x in all_features.values()]
    slope_values = [x.get("slope") for x in all_features.values()]
    for row in base_rows:
        row["rs_20d_pctile"] = percentile(all_features[row["code"]].get("ret20"), ret20_values)
        row["ma20_slope_pctile"] = percentile(all_features[row["code"]].get("slope"), slope_values)
    add_sector_features(base_rows)
    try:
        modules = load_modules()
    except Exception as exc:
        print(json.dumps({"status": "error", "error": f"原始策略模块加载失败: {exc}"}, ensure_ascii=False))
        return 1

    industry_contexts: Dict[str, Dict[str, Any]] = {}
    industry_status: Dict[str, Any] = {}
    if strategy_id == "quant-production-v65":
        industry_contexts, industry_status = build_quant_industry_contexts(base_rows, market, grouped, date_value)

    if strategy_id == "golden-ignition-v8":
        result_rows, missing, score_status = run_golden(modules["golden"], base_rows, date_value)
    elif strategy_id == "short-burst-score-v5":
        result_rows, missing, score_status = run_burst(modules["burst"], base_rows, market, grouped, date_value)
    elif strategy_id == "quant-production-v65":
        result_rows, missing, score_status = run_quant(
            modules["quant"],
            base_rows,
            market,
            grouped,
            date_value,
            industry_contexts,
            industry_status,
        )
    else:
        print(json.dumps({"status": "error", "error": f"未支持的策略评分入口: {strategy_id}"}, ensure_ascii=False))
        return 2

    by_code = {str(x.get("code")): x for x in result_rows}
    ordered = [by_code[code] for code in codes if code in by_code]
    output = {
        "status": "ok",
        "strategy_id": strategy_id,
        "trade_date": date_value,
        "score_status": score_status,
        "score_source": {
            "kind": "embedded_original_engine",
            "root": str(EMBEDDED_ROOT),
            "tdx_daily": tdx_status,
            "candidate_scope": len(candidates),
            "industry_context": industry_status if strategy_id == "quant-production-v65" else None,
        },
        "candidate_count": len(ordered),
        "missing": list(dict.fromkeys(missing)),
        "results": ordered,
        "audit": {
            "no_future_data": True,
            "data_date": date_value,
            "tdx_daily": tdx_status,
            "same_day_market_fields": same_day_status,
            "full_market_scan": False,
            "note": "数值字段来自原始策略评分函数；缺失辅助数据只影响生产授权/候选等级，不用涨幅或成交额替代策略分。",
        },
    }
    print(json.dumps(cleanup_internal(output), ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
