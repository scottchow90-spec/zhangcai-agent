#!/usr/bin/env python3
"""统一落盘个股研究所需的补充数据。

数据契约只使用公开/本地来源，所有输出都写入 ZHANGCAI_DATA_DIR：
* Sina 财务三表（按目标股票按需读取）
* 腾讯报价中的总股本/流通股本/估值快照
* 本地 TDX 归档中的主要指数日线
* 东方财富/已有 public 快照中的全市场龙虎榜
* 东方财富 datacenter 的融资融券日明细

没有数据时保留 status=missing/unavailable 与 error，不用 0 或空数组伪装成真实数据。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import urllib.parse
import struct
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


APP_ROOT = Path(os.environ.get("ZHANGCAI_APP_ROOT", Path(__file__).resolve().parents[1]))
DATA_ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR", APP_ROOT / "app-data"))
SUPPLEMENTAL_ROOT = DATA_ROOT / "evidence" / "supplemental"
DAILY_ROOT = DATA_ROOT / "market" / "daily"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ZhangcaiAgent/1.0"


def compact_date(value: str) -> str:
    raw = re.sub(r"\D", "", str(value or ""))
    if len(raw) != 8:
        raise ValueError("--date 必须是 YYYY-MM-DD 或 YYYYMMDD")
    return raw


def date_text(value: str) -> str:
    raw = compact_date(value)
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"


def normalize_code(value: str) -> str:
    raw = str(value or "").strip().upper()
    match = re.search(r"(\d{6})", raw)
    if not match:
        raise ValueError("--code 必须包含六位股票代码")
    return match.group(1)


def market_prefix(code: str) -> str:
    # Tencent/TDX use the BJ namespace for the newer 920xxx listings.
    # Keep 900xxx Shanghai B-shares/other 9-prefix instruments on SH.
    if code.startswith("92"):
        return "bj"
    return "sh" if code.startswith(("5", "6", "9")) else "sz"


def number(value: Any) -> float | None:
    if value in (None, "", "-", "--"):
        return None
    try:
        result = float(str(value).replace(",", "").replace("%", ""))
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if hasattr(value, "item"):
        try:
            return json_safe(value.item())
        except Exception:
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)


def fetch_json(url: str, *, referer: str = "https://quote.eastmoney.com/", timeout: int = 25) -> tuple[Any, dict[str, Any]]:
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer, "Accept": "application/json,text/plain,*/*"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        return json.loads(raw.decode("utf-8-sig")), {
            "url": url,
            "http_status": int(getattr(response, "status", 200) or 200),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }


def fetch_text(url: str, *, referer: str = "https://finance.sina.com.cn/", timeout: int = 25) -> tuple[str, dict[str, Any]]:
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        return raw.decode("utf-8-sig", "replace"), {
            "url": url,
            "http_status": int(getattr(response, "status", 200) or 200),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }


def as_status(name: str, status: str, source: str, *, meta: dict[str, Any] | None = None, data: Any = None, error: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"name": name, "status": status, "source": source}
    if meta:
        result.update(meta)
    if data is not None:
        result["data"] = json_safe(data)
    if error:
        result["error"] = error[:1000]
    return result


def parse_tencent_quote(code: str) -> dict[str, Any]:
    prefixed = f"{market_prefix(code)}{code}"
    text, meta = fetch_text(f"https://qt.gtimg.cn/q={prefixed}", referer="https://gu.qq.com/")
    match = re.search(r"=\"(.*?)\"", text, re.S)
    if not match:
        raise ValueError("腾讯行情返回为空")
    values = match.group(1).split("~")
    if len(values) < 74 or values[2] != code:
        raise ValueError("腾讯行情代码校验失败")

    def v(index: int) -> float | None:
        return number(values[index]) if index < len(values) else None

    price = v(3)
    float_mcap_yi = v(44)
    total_mcap_yi = v(45)
    # 腾讯 v_* 的 72/73 是流通股本/总股本（股）；这两个字段是数据技能包
    # 中东财 f85/f84 的独立低风控备胎，不能用市值反推覆盖真实值。
    float_shares = v(72)
    total_shares = v(73)
    quote = {
        "code": code,
        "name": values[1],
        "price": price,
        "last_close": v(4),
        "change_pct": v(32),
        "amount_wan": v(37),
        "turnover_pct": v(38),
        "pe_ttm": v(39),
        "float_market_cap_yuan": float_mcap_yi * 100_000_000 if float_mcap_yi is not None else None,
        "total_market_cap_yuan": total_mcap_yi * 100_000_000 if total_mcap_yi is not None else None,
        "pb": v(46),
        "limit_up": v(47),
        "limit_down": v(48),
        "float_shares": int(float_shares) if float_shares is not None and float_shares > 0 else None,
        "total_shares": int(total_shares) if total_shares is not None and total_shares > 0 else None,
        "quote_time": values[30] if len(values) > 30 else "",
        "is_stale": bool(v(37) == 0 and price and v(4) == price),
    }
    if quote["float_shares"] is None:
        raise ValueError("腾讯行情未提供有效流通股本")
    return {"status": "available", "provider": "tencent", "method": "qt.gtimg.cn", "meta": meta, "data": quote}


def parse_sina_statement(code: str, report_type: str, limit: int = 8) -> dict[str, Any]:
    prefix = market_prefix(code)
    params = urllib.parse.urlencode({
        "paperCode": f"{prefix}{code}", "source": report_type, "type": "0", "page": "1", "num": str(limit),
    })
    url = "https://quotes.sina.cn/cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022?" + params
    payload, meta = fetch_json(url, referer="https://finance.sina.com.cn/")
    report_list = (((payload or {}).get("result") or {}).get("data") or {}).get("report_list") or {}
    rows = []
    for period in sorted(report_list.keys(), reverse=True)[:limit]:
        period_obj = report_list.get(period) or {}
        row: dict[str, Any] = {"report_date": f"{period[:4]}-{period[4:6]}-{period[6:8]}"}
        for item in period_obj.get("data", []) or []:
            title = str(item.get("item_title") or "").strip()
            if not title or item.get("item_value") is None:
                continue
            row[title] = item.get("item_value")
            tongbi = item.get("item_tongbi")
            if tongbi not in (None, ""):
                row[title + "_yoy"] = tongbi
        rows.append(row)
    return {"status": "available" if rows else "missing", "provider": "sina", "method": f"CompanyFinanceService.getFinanceReport2022:{report_type}", "meta": meta, "data": {"records": rows, "record_count": len(rows)}}


def financial_snapshot(code: str) -> dict[str, Any]:
    statements: dict[str, Any] = {}
    errors = []
    for report_type in ("fzb", "lrb", "llb"):
        try:
            statements[report_type] = parse_sina_statement(code, report_type)
        except Exception as exc:
            statements[report_type] = {"status": "unavailable", "provider": "sina", "method": report_type, "error": f"{type(exc).__name__}: {exc}"}
            errors.append(f"{report_type}: {type(exc).__name__}: {exc}")
    records = {k: ((v.get("data") or {}).get("records") or []) for k, v in statements.items()}
    latest = max((row.get("report_date", "") for rows in records.values() for row in rows), default="")
    status = "available" if any(records.values()) else "unavailable"
    result: dict[str, Any] = {"status": status, "provider": "sina", "method": "CompanyFinanceService.getFinanceReport2022", "latest_report_date": latest, "statements": statements}
    if errors:
        result["errors"] = errors
    return result


def read_public_lhb(requested_date: str, code: str | None = None) -> dict[str, Any]:
    compact = compact_date(requested_date)
    text_date = date_text(compact)
    candidates = [
        DATA_ROOT / "public" / "latest.json",
        DATA_ROOT / "public" / "lhb" / f"{text_date}.json",
        DATA_ROOT / "public" / compact / "market-latest.json",
    ]
    payload = None
    source_path = None
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            value = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:
            continue
        if str(value.get("date") or value.get("source_date") or "").replace("-", "") == compact:
            payload, source_path = value, candidate
            break
    if payload is None:
        return as_status("longhubang", "missing", "local-public", data={"requested_date": text_date, "snapshot_exists": False, "records": [], "record_count": 0}, error="没有同日龙虎榜快照")

    sources = payload.get("sources") or {}
    all_rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for source_name in ("eastmoneyLhb", "akshareLhb"):
        source = sources.get(source_name) or {}
        data = source.get("data") or {}
        raw_rows = ((data.get("result") or {}).get("data") if source_name == "eastmoneyLhb" else data.get("records")) or []
        for row in raw_rows:
            item = {
                "code": str(row.get("SECURITY_CODE") or row.get("代码") or "").zfill(6),
                "name": row.get("SECURITY_NAME_ABBR") or row.get("名称") or "",
                "date": str(row.get("TRADE_DATE") or row.get("上榜日") or "")[:10],
                "net_buy_yuan": number(row.get("BILLBOARD_NET_AMT") if "BILLBOARD_NET_AMT" in row else row.get("龙虎榜净买额")),
                "buy_yuan": number(row.get("BILLBOARD_BUY_AMT") if "BILLBOARD_BUY_AMT" in row else row.get("龙虎榜买入额")),
                "sell_yuan": number(row.get("BILLBOARD_SELL_AMT") if "BILLBOARD_SELL_AMT" in row else row.get("龙虎榜卖出额")),
                "turnover_pct": number(row.get("换手率") or row.get("TURNOVERRATE")),
                "reason": row.get("EXPLAIN") or row.get("解读") or row.get("上榜原因") or "",
                "source": source_name,
            }
            if item["code"] and item["date"].replace("-", "") == compact:
                all_rows.append(item)
    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for row in all_rows:
        dedup.setdefault((row["code"], row["date"]), row)
    normalized = list(dedup.values())
    if code:
        normalized = [row for row in normalized if row["code"] == code]
    detail_source = sources.get("akshareLhbStockDetail") or {}
    detail_rows = ((detail_source.get("data") or {}).get("records") or [])
    if code:
        details = [row for row in detail_rows if str(row.get("代码") or "").zfill(6) == code]
    else:
        details = detail_rows
    return as_status("longhubang", "available", "local-public", meta={"snapshot_path": str(source_path), "source_date": text_date}, data={
        "requested_date": text_date,
        "snapshot_exists": True,
        "records": normalized,
        "record_count": len(normalized),
        "market_record_count": len(list(dedup.values())),
        "seat_details": details,
        "seat_detail_count": len(details),
        "target_has_record": bool(normalized),
    })


def fetch_margin(requested_date: str, code: str | None = None) -> dict[str, Any]:
    compact = compact_date(requested_date)
    text_date = date_text(compact)
    # datacenter 的日期过滤器使用单引号；双引号对 SCODE 也能兼容，
    # 但 DATE 双引号会返回空结果，容易把“当天无融资融券”误判为真。
    condition = f"(SCODE=\"{code}\")" if code else f"(DATE='{text_date}')"
    params = urllib.parse.urlencode({
        "sortColumns": "DATE,SCODE", "sortTypes": "-1,1", "pageSize": "5000", "pageNumber": "1",
        "reportName": "RPTA_WEB_RZRQ_GGMX", "columns": "ALL", "source": "WEB", "client": "WEB", "filter": condition,
    })
    first_url = "https://datacenter-web.eastmoney.com/api/data/v1/get?" + params
    try:
        first, meta = fetch_json(first_url, referer="https://data.eastmoney.com/rzrq/", timeout=25)
        result = (first or {}).get("result") or {}
        pages = max(1, min(int(result.get("pages") or 1), 20))
        raw_rows = list(result.get("data") or [])
        for page in range(2, pages + 1):
            page_params = dict(urllib.parse.parse_qsl(params))
            page_params["pageNumber"] = str(page)
            value, _ = fetch_json("https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(page_params), referer="https://data.eastmoney.com/rzrq/", timeout=25)
            raw_rows.extend(((value or {}).get("result") or {}).get("data") or [])
        records = []
        for row in raw_rows:
            item = {
                "date": str(row.get("DATE") or "")[:10],
                "code": str(row.get("SCODE") or "").zfill(6),
                "name": row.get("SECNAME") or "",
                "market": row.get("MARKET") or "",
                "rzye": number(row.get("RZYE")), "rzmre": number(row.get("RZMRE")), "rzche": number(row.get("RZCHE")),
                "rqye": number(row.get("RQYE")), "rqmcl": number(row.get("RQMCL")), "rqchl": number(row.get("RQCHL")),
                "rzrqye": number(row.get("RZRQYE")), "rzjme": number(row.get("RZJME")), "fin_balance_gr": number(row.get("FIN_BALANCE_GR")),
                "close": number(row.get("SPJ")), "change_pct": number(row.get("ZDF")), "source": "eastmoney-datacenter",
            }
            if item["code"]:
                records.append(item)
        records.sort(key=lambda row: row.get("date", ""), reverse=True)
        exact = [row for row in records if row.get("date", "").replace("-", "") == compact]
        return as_status("margin", "available" if records else "missing", "eastmoney-datacenter", meta={"source_date": text_date, "requested_date": text_date, "exact_date": bool(exact), "latest_available_date": records[0].get("date") if records else "", "pages": pages, **meta}, data={"records": records, "record_count": len(records), "exact_record_count": len(exact), "snapshot_exists": bool(records)})
    except Exception as exc:
        return as_status("margin", "unavailable", "eastmoney-datacenter", data={"records": [], "record_count": 0, "snapshot_exists": False, "requested_date": text_date}, error=f"{type(exc).__name__}: {exc}")


def read_index_daily(requested_date: str) -> dict[str, Any]:
    compact = compact_date(requested_date)
    wanted = {"sh000001", "sz399001", "sz399006", "sh000300", "sh000016", "sh000688", "sz399005", "sh000905", "sh000852"}
    # 指数先读 TDX 原始 .day 文件，只打开 9 个小文件，不能为了找指数扫描
    # 15,722,263 行、约 2.5GB 的全市场 JSONL 归档。
    _tdx_root_text = os.environ.get("ZHANGCAI_TDX_ROOT", "").strip()
    _packaged_runtime = os.environ.get("ZHANGCAI_PACKAGED") == "1"
    tdx_root = Path(_tdx_root_text) if _tdx_root_text else (
        Path(r"C:\new_tdx_mock") if not _packaged_runtime else Path(r"C:\__zhangcai_tdx_root_not_configured__")
    )
    rows: dict[str, list[dict[str, Any]]] = {key: [] for key in wanted}
    for symbol in wanted:
        market, code = symbol[:2], symbol[2:]
        file = tdx_root / "vipdoc" / market / "lday" / f"{symbol}.day"
        if not file.exists():
            continue
        try:
            raw = file.read_bytes()
            for offset in range(0, len(raw) - (len(raw) % 32), 32):
                day, open_i, high_i, low_i, close_i, amount, volume = struct.unpack_from("<IIIII f I", raw, offset)
                day_text = str(day)
                if not re.fullmatch(r"\d{8}", day_text):
                    continue
                rows[symbol].append({
                    "date": f"{day_text[:4]}-{day_text[4:6]}-{day_text[6:]}", "open": round(open_i / 100, 2),
                    "high": round(high_i / 100, 2), "low": round(low_i / 100, 2), "close": round(close_i / 100, 2),
                    "amount": round(float(amount), 2), "volume": int(volume),
                })
        except (OSError, struct.error):
            continue
    fallback_file = DAILY_ROOT / compact / "tdx-bars.jsonl"
    if not any(rows.values()) and fallback_file.exists():
        # 仅在 TDX 原始文件不存在时提供兼容回退；该路径用于移植后的 EXE
        # 小型归档，正常开发环境不会走这里。
        with fallback_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                symbol = str(row.get("symbol") or "").lower()
                if symbol not in rows:
                    continue
                rows[symbol].append({
                    "date": str(row.get("date") or ""), "open": number(row.get("open")), "high": number(row.get("high")),
                    "low": number(row.get("low")), "close": number(row.get("close")), "amount": number(row.get("amount")), "volume": number(row.get("volume")),
                })
    result = {}
    for symbol, values in rows.items():
        if not values:
            continue
        values.sort(key=lambda row: row.get("date", ""))
        result[symbol] = {"symbol": symbol, "records": values, "record_count": len(values), "first_date": values[0]["date"], "last_date": values[-1]["date"], "full_history_verified": True}
    return as_status("index_daily", "available" if result else "missing", "tdx-local", meta={"source_file": str(tdx_root / "vipdoc"), "source_date": date_text(compact)}, data={"requested_date": date_text(compact), "symbols": result, "symbol_count": len(result)})


def sync_many(args: argparse.Namespace, codes: list[str]) -> dict[str, Any]:
    """Batch code-level supplements without duplicating the market snapshot.

    The package's public-data policy allows bounded batches.  Market-level
    index/LHB/margin data is written once; each code file keeps only a stable
    reference to that file plus its own Tencent/Sina evidence.  This avoids
    creating dozens of 10+ MB copies of the same market payload.
    """
    compact = compact_date(args.date)
    text_date = date_text(compact)
    target_dir = SUPPLEMENTAL_ROOT / compact
    target_dir.mkdir(parents=True, exist_ok=True)
    index = read_index_daily(text_date)
    lhb = read_public_lhb(text_date)
    margin = fetch_margin(text_date)
    market_payload: dict[str, Any] = {
        "schema": "ZHANGCAI_SUPPLEMENTAL_DATA_V1",
        "status": "completed",
        "requested_date": text_date,
        "trade_date": text_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_policy": "a-stock-data v3.7.2: TDX local index, Tencent quote, Sina statements, Eastmoney datacenter, local public LHB archive",
        "market": {"index_daily": index, "longhubang": lhb, "margin": margin},
        "stock": None,
        "coverage": {
            "financial": None,
            "share_capital": None,
            "index_daily": index.get("status") == "available",
            "longhubang_snapshot": lhb.get("data", {}).get("snapshot_exists") is True,
            "margin_snapshot": margin.get("data", {}).get("snapshot_exists") is True,
        },
        "stock_summary": {"requested_count": len(codes), "financial_available": 0, "share_capital_available": 0, "files": []},
    }
    market_file = target_dir / "market.json"
    market_file.write_text(json.dumps(market_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lhb_records = (lhb.get("data") or {}).get("records") or []
    lhb_details = (lhb.get("data") or {}).get("seat_details") or []
    margin_records = (margin.get("data") or {}).get("records") or []
    results: list[dict[str, Any]] = []
    for code in codes:
        try:
            quote = parse_tencent_quote(code)
        except Exception as exc:
            quote = {"status": "unavailable", "provider": "tencent", "method": "qt.gtimg.cn", "error": f"{type(exc).__name__}: {exc}"}
        financial = financial_snapshot(code)
        stock = {"code": code, "financial": financial, "share_capital": quote}
        code_lhb = [row for row in lhb_records if str(row.get("code") or "").zfill(6) == code]
        code_details = [row for row in lhb_details if str(row.get("代码") or "").zfill(6) == code]
        code_margin = [row for row in margin_records if str(row.get("code") or "").zfill(6) == code]
        payload = {
            **market_payload,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "market": {
                "ref": f"evidence/supplemental/{compact}/market.json",
                "trade_date": text_date,
                "index_daily": {"status": index.get("status"), "symbol_count": index.get("data", {}).get("symbol_count", 0)},
                "longhubang": {"status": lhb.get("status"), "target_records": len(code_lhb), "seat_details": code_details},
                "margin": {"status": margin.get("status"), "target_records": len(code_margin), "records": code_margin},
            },
            "stock": stock,
            "coverage": {
                "financial": financial.get("status") == "available",
                "share_capital": quote.get("status") == "available",
                "index_daily": index.get("status") == "available",
                "longhubang_snapshot": lhb.get("data", {}).get("snapshot_exists") is True,
                "margin_snapshot": margin.get("data", {}).get("snapshot_exists") is True,
            },
        }
        target = target_dir / f"{code}.{market_prefix(code).upper()}.json"
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        market_payload["stock_summary"]["files"].append(str(target.relative_to(DATA_ROOT)).replace("\\", "/"))
        if payload["coverage"]["financial"]:
            market_payload["stock_summary"]["financial_available"] += 1
        if payload["coverage"]["share_capital"]:
            market_payload["stock_summary"]["share_capital_available"] += 1
        results.append({"code": code, "file": str(target), "coverage": payload["coverage"], "financial_report_date": financial.get("latest_report_date", ""), "quote_time": (quote.get("data") or {}).get("quote_time", "")})
    # Rebuild the batch summary from all dated code files.  A later retry for
    # two BJ symbols must not erase the 30 earlier files from the market
    # index, which is what Harness and a future EXE read first.
    all_files = sorted(target_dir.glob("[0-9][0-9][0-9][0-9][0-9][0-9].*.json"))
    financial_count = 0
    share_count = 0
    relative_files: list[str] = []
    for path in all_files:
        value = json.loads(path.read_text(encoding="utf-8"))
        coverage = value.get("coverage", {}) if isinstance(value, dict) else {}
        financial_count += int(coverage.get("financial") is True)
        share_count += int(coverage.get("share_capital") is True)
        relative_files.append(str(path.relative_to(DATA_ROOT)).replace("\\", "/"))
    market_payload["stock"] = None
    market_payload["stock_summary"] = {
        "requested_count": len(all_files),
        "financial_available": financial_count,
        "share_capital_available": share_count,
        "files": relative_files,
    }
    market_payload["coverage"]["financial"] = financial_count == len(all_files) if all_files else False
    market_payload["coverage"]["share_capital"] = share_count == len(all_files) if all_files else False
    market_file.write_text(json.dumps(market_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (SUPPLEMENTAL_ROOT / "latest.json").write_text(json.dumps(market_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "completed", "date": text_date, "codes": len(codes), "output": str(market_file), "coverage": market_payload["coverage"], "stock_summary": market_payload["stock_summary"], "results": results}


def sync(args: argparse.Namespace) -> dict[str, Any]:
    compact = compact_date(args.date)
    text_date = date_text(compact)
    code = normalize_code(args.code) if args.code else None
    target_dir = SUPPLEMENTAL_ROOT / compact
    target_dir.mkdir(parents=True, exist_ok=True)

    index = read_index_daily(text_date)
    lhb = read_public_lhb(text_date, code)
    margin = fetch_margin(text_date, code)
    stock: dict[str, Any] | None = None
    if code:
        try:
            quote = parse_tencent_quote(code)
        except Exception as exc:
            quote = {"status": "unavailable", "provider": "tencent", "method": "qt.gtimg.cn", "error": f"{type(exc).__name__}: {exc}"}
        stock = {
            "code": code,
            "financial": financial_snapshot(code),
            "share_capital": quote,
        }

    payload: dict[str, Any] = {
        "schema": "ZHANGCAI_SUPPLEMENTAL_DATA_V1",
        "status": "completed",
        "requested_date": text_date,
        "trade_date": text_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_policy": "a-stock-data v3.7.2: TDX local index, Tencent quote, Sina statements, Eastmoney datacenter, local public LHB archive",
        "market": {"index_daily": index, "longhubang": lhb, "margin": margin},
        "stock": stock,
        "coverage": {
            "financial": stock and stock["financial"].get("status") == "available",
            "share_capital": stock and stock["share_capital"].get("status") == "available",
            "index_daily": index.get("status") == "available",
            "longhubang_snapshot": lhb.get("data", {}).get("snapshot_exists") is True,
            "margin_snapshot": margin.get("data", {}).get("snapshot_exists") is True,
        },
    }
    # 市场级快照和个股按需快照必须分离。个股请求不能覆盖当天的
    # market.json，否则全市场龙虎榜/融资融券会被误读成目标股票数据。
    day_file = target_dir / "market.json"
    if not code:
        day_file.write_text(json.dumps({k: v for k, v in payload.items() if k != "stock"}, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        (target_dir / f"{code}.{market_prefix(code).upper()}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (SUPPLEMENTAL_ROOT / "latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "completed", "date": text_date, "code": code, "output": str(target_dir / (f"{code}.{market_prefix(code).upper()}.json" if code else "market.json")), "coverage": payload["coverage"], "counts": {"index_symbols": index.get("data", {}).get("symbol_count", 0), "lhb": lhb.get("data", {}).get("market_record_count", lhb.get("data", {}).get("record_count", 0)), "lhb_target": lhb.get("data", {}).get("record_count", 0), "margin": margin.get("data", {}).get("record_count", 0)}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--code")
    parser.add_argument("--codes", help="逗号/空格分隔的多只股票代码；一次只抓取目标股票的财务和股本，市场数据只写一份")
    parser.add_argument("--mode", choices=("daily", "stock"), default="daily")
    args = parser.parse_args()
    if args.codes:
        values = []
        for raw in str(args.codes).replace(",", " ").split():
            try:
                values.append(normalize_code(raw))
            except ValueError:
                continue
        values = list(dict.fromkeys(values))
        result = sync_many(args, values) if values else {"status": "missing", "error": "--codes 未解析出有效股票代码"}
    else:
        result = sync(args)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
