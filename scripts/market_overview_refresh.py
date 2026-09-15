#!/usr/bin/env python3
"""Read only the real time fields needed by the overview cards."""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import argparse
import struct
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TDX_ROOT = Path(os.environ.get("ZHANGCAI_TDX_ROOT", r"C:\new_tdx_mock"))
USER_DIR = TDX_ROOT / "PYPlugins" / "user"
MARKET_FILE = Path(__file__).resolve().parents[1] / "lib" / "market.json"
DAY_RECORD = struct.Struct("<IIIIIfII")
CONNECTION_TEMPLATE = USER_DIR / "tdxdata_test.py"
DATA_ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR", Path(__file__).resolve().parents[1] / "app-data"))
PUBLIC_FALLBACK_FILE = DATA_ROOT / "runtime" / "market-public-fallback.json"
SHANGHAI_TZ = timezone(timedelta(hours=8))
PUBLIC_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",
    "Referer": "https://quote.eastmoney.com/",
    "Accept": "application/json,text/plain,*/*",
    "Connection": "close",
}
PUBLIC_INDEX_SECIDS = {
    "sh000001": "1.000001",
    "sz399001": "0.399001",
    "sz399006": "0.399006",
    "sh000688": "1.000688",
    "sh000016": "1.000016",
    "bj899050": "0.899050",
}


def tdx_is_running() -> bool:
    """检测通达信主进程，避免把 TQ 初始化异常直接显示给网页。"""
    if os.name != "nt":
        return True
    names = {"tdxw.exe", "tdx.exe", "new_tdx.exe", "通达信.exe"}
    try:
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        output = result.stdout.decode("mbcs", errors="ignore").lower()
        return any(f'"{name}"' in output for name in names)
    except OSError:
        # 无法读取进程列表时继续尝试 TQ；真正的初始化错误会被友好化。
        return True


def connection_script(scope: str) -> Path:
    """为每次 TQ 会话生成唯一脚本名，避免并发刷新触发同名策略锁。"""
    session_dir = MARKET_FILE.resolve().parents[1] / "data" / "runtime" / "tq-sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    target = session_dir / f"tdxdata_{scope}_{os.getpid()}_{time.time_ns()}.py"
    shutil.copyfile(CONNECTION_TEMPLATE, target)
    return target


def print_tq_error(scope: str, tdx_running: bool, error: Exception) -> int:
    if not tdx_running:
        message = "通达信客户端未启动，无法读取实时指数。请先打开通达信并登录后再刷新。"
        code = "TDX_NOT_RUNNING"
    else:
        message = "通达信已打开，但 TQ 数据接口初始化失败，可能有其他刷新任务正在占用连接。请稍后重试。"
        code = "TQ_INIT_FAILED"
    print(json.dumps({
        "status": "error",
        "error": message,
        "errorCode": code,
        "scope": scope,
        "tdxRunning": tdx_running,
    }, ensure_ascii=False))
    return 0


def public_json(url: str, params: dict[str, str], timeout: int = 20) -> dict:
    # Eastmoney 的旧式行情网关对逗号被百分号编码的 fields/secids
    # 偶发直接断连接；保留查询参数中的逗号与点号，其他字符仍编码。
    target = f"{url}?{urlencode(params, safe=',.')}"
    # 当前 Windows 环境的公开行情访问经过系统代理；urllib/requests
    # 会被代理端主动断开，而 PowerShell 的系统网络栈可以正常完成同一
    # 个只读请求。优先使用 PowerShell，失败后仍保留 urllib 作为 EXE
    # 打包环境的备用路径。
    ps_url = target.replace("'", "''")
    ps_script = (
        "$ErrorActionPreference='Stop';"
        "$ProgressPreference='SilentlyContinue';"
        f"$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec {int(timeout)} "
        f"-Uri '{ps_url}' -Headers @{{'User-Agent'='Mozilla/5.0';'Referer'='https://quote.eastmoney.com/';'Accept'='application/json,text/plain,*/*'}};"
        "[Console]::Out.Write($r.Content)"
    )
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True,
            check=True,
            timeout=timeout + 5,
        )
        return json.loads(completed.stdout.decode("utf-8-sig", errors="replace"))
    except Exception as powershell_error:
        ps_stderr = getattr(powershell_error, "stderr", b"")
        if isinstance(ps_stderr, bytes):
            ps_stderr = ps_stderr.decode("utf-8", errors="replace")
        request = Request(target, headers=PUBLIC_HEADERS)
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8-sig", errors="replace"))
        except Exception as urllib_error:
            raise RuntimeError(f"PowerShell={powershell_error}; stderr={str(ps_stderr).strip()[:300]}; urllib={urllib_error}") from urllib_error


def public_trade_date() -> str:
    """Use the latest weekday visible to the public quote endpoint.

    The public list endpoint has no reliable per-row trade date. Before the
    normal A-share open, use the previous weekday; after open use today. The
    payload is still marked degraded so callers do not mistake it for TDX.
    """
    current = datetime.now(SHANGHAI_TZ)
    if current.weekday() >= 5 or (current.hour, current.minute) < (9, 30):
        current -= timedelta(days=1)
        while current.weekday() >= 5:
            current -= timedelta(days=1)
    return current.strftime("%Y%m%d")


def public_market_name(code: str) -> str:
    if code.startswith("6"):
        return "sh"
    if code.startswith(("4", "8", "92")):
        return "bj"
    return "sz"


def public_limit_pct(code: str) -> float:
    if code.startswith(("30", "68")):
        return 20.0
    if code.startswith(("4", "8", "92")):
        return 30.0
    return 10.0


def public_float(value: object, default: float = 0.0) -> float:
    """Parse Eastmoney's numeric fields, including '-' and comma values."""
    try:
        text = str(value).strip().replace(",", "")
        if not text or text in {"-", "--", "None", "null"}:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def append_history(old: dict, latest: dict) -> list[dict]:
    history = [row for row in (old.get("history") or []) if row.get("date") != latest.get("date")]
    history.append({key: latest.get(key) for key in ("date", "open", "high", "low", "close", "amount", "volume")})
    return history[-60:]


def public_indices(market: dict, trade_date: str) -> list[dict]:
    params = {
        "fltt": "2",
        "fields": "f2,f3,f4,f5,f6,f12,f14,f15,f16,f17,f18",
        "secids": ",".join(PUBLIC_INDEX_SECIDS.values()),
    }
    body = public_json("https://push2delay.eastmoney.com/api/qt/ulist.np/get", params)
    if body.get("rc") != 0 or not isinstance(body.get("data", {}).get("diff"), list):
        raise ValueError("东方财富指数公开快照为空")
    old_by_code = {str(row.get("code")): row for row in market.get("indices", [])}
    rows = []
    for item in body["data"]["diff"]:
        raw_code = str(item.get("f12") or "")
        code = next((key for key in PUBLIC_INDEX_SECIDS if key.endswith(raw_code)), "")
        if not code:
            continue
        close = public_float(item.get("f2"))
        previous = public_float(item.get("f18"))
        old = old_by_code.get(code, {})
        if close <= 0:
            continue
        if previous <= 0:
            previous = float(old.get("previousClose") or old.get("close") or close)
        latest = {
            **old,
            "code": code,
            "name": str(item.get("f14") or old.get("name") or code),
            "market": code[:2],
            "date": trade_date,
            "open": public_float(item.get("f17"), public_float(old.get("open"), close)),
            "high": public_float(item.get("f15"), public_float(old.get("high"), close)),
            "low": public_float(item.get("f16"), public_float(old.get("low"), close)),
            "close": close,
            "previousClose": previous,
            "amount": public_float(item.get("f6"), public_float(old.get("amount"))),
            "volume": public_float(item.get("f5"), public_float(old.get("volume"))),
            "pct": round(public_float(item.get("f3"), (close / previous - 1) * 100 if previous else 0), 2),
            "realtime": False,
            "source": "Eastmoney public delayed snapshot",
            "historySource": "public quote + local page history",
        }
        latest["history"] = append_history(old, latest)
        rows.append(latest)
    if len(rows) < 3:
        raise ValueError("东方财富指数公开快照有效数量不足")
    return rows


def public_market_rows(market: dict, trade_date: str) -> list[dict]:
    params = {
        "pn": "1",
        # Eastmoney currently caps this endpoint at 100 rows per response,
        # even when pz is larger.  Keep the page size explicit and combine
        # the pages only inside the fallback worker; the browser receives a
        # compact homepage payload, never the full public universe.
        "pz": "100",
        "po": "1",
        "np": "1",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "fields": "f2,f3,f4,f5,f6,f12,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26",
    }
    endpoint = "https://push2delay.eastmoney.com/api/qt/clist/get"
    body = public_json(endpoint, params, timeout=30)
    data = body.get("data") if isinstance(body, dict) else None
    first_items = data.get("diff") if isinstance(data, dict) else None
    total = int(data.get("total") or 0) if isinstance(data, dict) else 0
    if body.get("rc") != 0 or not isinstance(first_items, list) or not first_items or total <= 0:
        raise ValueError("东方财富全市场公开快照为空")
    page_size = 100
    page_count = max(1, (total + page_size - 1) // page_size)
    items = list(first_items)

    def fetch_page(page: int) -> list[dict]:
        page_params = {**params, "pn": str(page), "pz": str(page_size)}
        page_body = public_json(endpoint, page_params, timeout=30)
        page_data = page_body.get("data") if isinstance(page_body, dict) else None
        page_items = page_data.get("diff") if isinstance(page_data, dict) else None
        if page_body.get("rc") != 0 or not isinstance(page_items, list):
            raise ValueError(f"公开行情第 {page}/{page_count} 页为空")
        return page_items

    # A small amount of concurrency keeps the fallback responsive while
    # avoiding a burst large enough to trigger the public endpoint's guard.
    if page_count > 1:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(fetch_page, page): page for page in range(2, page_count + 1)}
            for future in as_completed(futures):
                items.extend(future.result())
    existing = market.get("allStocks") or market.get("stocks") or []
    old_by_code = {str(row.get("code")): row for row in existing if row.get("code")}
    rows = []
    for item in items:
        code = str(item.get("f12") or "").zfill(6)
        close = public_float(item.get("f2"))
        if len(code) != 6 or close <= 0:
            continue
        old = old_by_code.get(code, {})
        previous = public_float(item.get("f18"), public_float(old.get("previousClose"), close))
        row = {
            **old,
            "code": code,
            "name": str(item.get("f14") or old.get("name") or code).replace(" ", ""),
            "market": public_market_name(code),
            "date": trade_date,
            "open": public_float(item.get("f17"), public_float(old.get("open"), close)),
            "high": public_float(item.get("f15"), public_float(old.get("high"), close)),
            "low": public_float(item.get("f16"), public_float(old.get("low"), close)),
            "close": close,
            "previousClose": previous,
            "amount": public_float(item.get("f6")),
            "volume": public_float(item.get("f5")),
            "pct": round(public_float(item.get("f3"), (close / previous - 1) * 100 if previous else 0), 2),
            "limitPct": public_limit_pct(code),
            "realtime": False,
            "source": "Eastmoney public delayed snapshot",
            "historySource": "public quote + local page history",
        }
        row["history"] = append_history(old, row)
        rows.append(row)
    if len(rows) < min(3000, max(100, total // 2)):
        raise ValueError(f"东方财富公开快照仅返回 {len(rows)}/{total} 只有效股票")
    return rows


def public_fallback(scope: str, market: dict, reason: str) -> dict:
    trade_date = public_trade_date()
    try:
        indices = public_indices(market, trade_date)
        stocks = public_market_rows(market, trade_date) if scope in {"market", "watchlist"} else []
        if scope == "watchlist":
            requested = {value.strip() for value in str(os.environ.get("ZHANGCAI_PUBLIC_WATCHLIST_CODES", "")).split(",") if value.strip()}
            if requested:
                stocks = [row for row in stocks if row["code"] in requested]
        summary_stocks = [row for row in stocks if row.get("name") not in {"上证指数", "深证成指", "创业板指", "科创50", "上证50", "北证50"}]
        up = sum(float(row.get("pct", 0)) > 0 for row in summary_stocks)
        down = sum(float(row.get("pct", 0)) < 0 for row in summary_stocks)
        flat = len(summary_stocks) - up - down
        bins = [
            sum(row.get("pct", 0) < -7 for row in summary_stocks),
            sum(-7 <= row.get("pct", 0) < -3 for row in summary_stocks),
            sum(-3 <= row.get("pct", 0) < 0 for row in summary_stocks),
            sum(row.get("pct", 0) == 0 for row in summary_stocks),
            sum(0 < row.get("pct", 0) <= 3 for row in summary_stocks),
            sum(3 < row.get("pct", 0) <= 7 for row in summary_stocks),
            sum(row.get("pct", 0) > 7 for row in summary_stocks),
        ]
        gain_rows = sorted(stocks, key=lambda row: (row.get("pct", 0), row.get("amount", 0)), reverse=True)
        amount_rows = sorted(stocks, key=lambda row: (row.get("amount", 0), row.get("pct", 0)), reverse=True)
        overview_rows = {row["code"]: row for row in gain_rows[:100] + amount_rows[:100]}

        def homepage_stock(row: dict) -> dict:
            # Leaderboards need no historical bars, industry payload, or
            # derived research fields.  Keeping this projection small makes
            # the public fallback fast and prevents stale detail data from
            # being mistaken for a complete local universe.
            return {
                key: row.get(key)
                for key in ("code", "name", "market", "date", "open", "high", "low", "close", "previousClose", "pct", "amount", "volume", "limitPct", "source")
            }

        # The public fallback is intentionally shaped for the homepage only:
        # six indexes, market breadth, and two compact leaderboards.  The
        # complete public universe above is used transiently to calculate the
        # breadth, then discarded instead of being returned or archived.
        payload = {
            "status": "ok",
            "source": "Eastmoney public delayed market snapshot (fallback)",
            "provider": "eastmoney",
            "quality": "degraded",
            "fallback": True,
            "fallbackReason": reason[:500],
            "fetchedAt": datetime.now(SHANGHAI_TZ).isoformat(timespec="seconds"),
            "tradeDate": trade_date,
            "dataScope": scope,
            "indices": indices,
            "stocks": [homepage_stock(row) for row in overview_rows.values()] if scope in {"market", "watchlist"} else [],
            "allStocks": [],
            "marketSummary": {
                "currentCount": len(summary_stocks) if scope == "market" else market.get("currentCount"),
                "up": up if scope == "market" else market.get("up"),
                "down": down if scope == "market" else market.get("down"),
                "flat": flat if scope == "market" else market.get("flat"),
                "amount": round(sum(float(row.get("amount", 0)) for row in summary_stocks)) if scope == "market" else market.get("amount"),
                "bins": bins if scope == "market" else market.get("bins", []),
            },
            "replaceLeaderboard": scope in {"market", "watchlist"},
            "scope": f"通达信/TQ 不可用，已切换东方财富公开行情降级；首页已更新指数、市场宽度、涨幅榜和成交额榜，日期 {trade_date}",
            "dataSources": {
                "primary": "TongdaXin/TQ",
                "fallback": "Eastmoney push2 public delayed snapshot",
                "fallbackQuality": "DEGRADED",
                "fallbackReason": reason[:500],
            },
        }
        PUBLIC_FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        PUBLIC_FALLBACK_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
    except Exception as error:
        return {
            "status": "error",
            "error": f"通达信/TQ 不可用，公开行情降级也失败：{error}",
            "errorCode": "PUBLIC_FALLBACK_FAILED",
            "fallback": True,
            "fallbackReason": reason[:500],
            "tradeDate": trade_date,
        }

INDEXES = [
    ("sh000001", "上证指数", "000001.SH"),
    ("sz399001", "深证成指", "399001.SZ"),
    ("sz399006", "创业板指", "399006.SZ"),
    ("sh000688", "科创50", "000688.SH"),
    ("sh000016", "上证50", "000016.SH"),
    ("bj899050", "北证50", "899050.BJ"),
]


def symbol_for(stock: dict) -> str:
    return f"{stock.get('code', '')}.{str(stock.get('market', 'sz')).upper()}"


def day_path(stock: dict) -> Path:
    market = str(stock.get("market", "sz")).lower()
    code = str(stock.get("code", ""))[-6:]
    return TDX_ROOT / "vipdoc" / market / "lday" / f"{market}{code}.day"


def parse_day(chunk: bytes) -> dict | None:
    try:
        date_i, open_i, high_i, low_i, close_i, amount, volume, _unused = DAY_RECORD.unpack(chunk)
        return {"date": str(date_i), "open": open_i / 100.0, "high": high_i / 100.0, "low": low_i / 100.0, "close": close_i / 100.0, "amount": float(amount), "volume": int(volume)}
    except (struct.error, ValueError):
        return None


def latest_day(stock: dict) -> tuple[dict | None, dict | None]:
    path = day_path(stock)
    try:
        count = path.stat().st_size // DAY_RECORD.size
        if count < 1:
            return None, None
        with path.open("rb") as handle:
            handle.seek((count - 1) * DAY_RECORD.size)
            latest = parse_day(handle.read(DAY_RECORD.size))
            previous = None
            if count > 1:
                handle.seek((count - 2) * DAY_RECORD.size)
                previous = parse_day(handle.read(DAY_RECORD.size))
            return latest, previous
    except OSError:
        return None, None


def tdx_trade_date(source: list[dict]) -> str:
    counts: Counter[str] = Counter()
    for stock in source:
        latest, _ = latest_day(stock)
        if latest and latest.get("date"):
            counts[str(latest["date"])] += 1
    return max((date for date, count in counts.items() if count >= 3000), default="")


def dayline_stock(stock: dict, target_date: str) -> dict | None:
    latest, previous = latest_day(stock)
    if not latest or latest.get("date") != target_date:
        return None
    close = float(latest.get("close") or 0)
    previous_close = float((previous or {}).get("close") or stock.get("previousClose") or close)
    history = list(stock.get("history") or [])
    history = [row for row in history if row.get("date") != latest.get("date")]
    history.append(latest)
    return {**stock, **latest, "previousClose": previous_close, "pct": round((close / previous_close - 1) * 100, 2) if previous_close else 0, "history": history[-60:], "realtime": False}


def realtime_stock(tq, stock: dict) -> dict | None:
    try:
        value = tq.get_market_snapshot(
            stock_code=symbol_for(stock),
            field_list=["Now", "LastClose", "Open", "Max", "Min", "Amount", "Volume"],
        ) or {}
        now = float(value.get("Now") or stock.get("close") or 0)
        last = float(value.get("LastClose") or stock.get("previousClose") or stock.get("close") or 0)
        if not now or not last:
            return None
        amount = float(value.get("Amount") or 0)
        # TQ snapshot Amount is in ten-thousand yuan; the web model stores yuan.
        if amount and amount < 1e8:
            amount *= 10000
        return {
            **stock,
            "open": float(value.get("Open") or stock.get("open") or 0),
            "high": float(value.get("Max") or stock.get("high") or 0),
            "low": float(value.get("Min") or stock.get("low") or 0),
            "close": now,
            "previousClose": last,
            "amount": round(amount or float(stock.get("amount") or 0)),
            "volume": float(value.get("Volume") or stock.get("volume") or 0),
            "pct": round((now / last - 1) * 100, 2),
            "realtime": True,
        }
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["indices", "market", "watchlist"], default="indices")
    parser.add_argument("--codes", default="")
    args = parser.parse_args()
    scope = args.scope
    market = json.loads(MARKET_FILE.read_text(encoding="utf-8"))
    needs_tq = scope in {"indices", "watchlist"}
    tq = None
    connection_path = None
    if needs_tq:
        running = tdx_is_running()
        if not running:
            payload = public_fallback(scope, market, "TDX_NOT_RUNNING")
            print(json.dumps(payload, ensure_ascii=False))
            return 0
        try:
            sys.path.insert(0, str(USER_DIR))
            os.chdir(TDX_ROOT)
            from tqcenter import tq as tq_api  # type: ignore
            tq = tq_api
            connection_path = connection_script(scope)
        except Exception as error:
            return_code = public_fallback(scope, market, f"TQ_IMPORT_FAILED: {error}")
            print(json.dumps(return_code, ensure_ascii=False))
            return 0

    rows = []
    stock_rows = []
    source_universe = list(market.get("allStocks", [])) or list(market.get("stocks", []))
    trade_date = tdx_trade_date(source_universe) or str(market.get("date") or "")
    quiet = io.StringIO()
    if tq is not None and connection_path is not None:
        try:
            with contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
                tq.initialize(str(connection_path))
        except Exception as error:
            try:
                tq.close()
            except Exception:
                pass
            try:
                connection_path.unlink(missing_ok=True)
            except OSError:
                pass
            payload = public_fallback(scope, market, f"TQ_INIT_FAILED: {error}")
            print(json.dumps(payload, ensure_ascii=False))
            return 0
    try:
        with contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            for code, name, symbol in INDEXES if scope == "indices" else []:
                old = next((x for x in market.get("indices", []) if x.get("code") == code), {})
                try:
                    value = tq.get_market_snapshot(
                        stock_code=symbol,
                        field_list=["Now", "LastClose", "Open", "Max", "Min", "Amount", "Volume"],
                    ) or {}
                    now = float(value.get("Now") or old.get("close") or 0)
                    last = float(value.get("LastClose") or old.get("close") or 0)
                    change = round((now / last - 1) * 100, 2) if last else float(old.get("pct") or 0)
                    rows.append({
                        "code": code,
                        "name": name,
                        "date": trade_date or old.get("date") or market.get("date"),
                        "open": float(value.get("Open") or old.get("open") or 0),
                        "high": float(value.get("Max") or old.get("high") or 0),
                        "low": float(value.get("Min") or old.get("low") or 0),
                        "close": now,
                        "previousClose": last,
                        "amount": float(value.get("Amount") or old.get("amount") or 0),
                        "volume": float(value.get("Volume") or old.get("volume") or 0),
                        "pct": change,
                        "realtime": True,
                    })
                except Exception:
                    if old:
                        rows.append({**old, "realtime": False})
            if scope in {"market", "watchlist"}:
                # Refresh the same current-day universe used by the overview.
                requested = {x.strip() for x in args.codes.split(",") if x.strip()} if scope == "watchlist" else set()
                source = source_universe
                if requested:
                    source = [x for x in source if x.get("code") in requested]
                for stock in source:
                    # 首页与复盘使用最新完整 TDX 日线，避免继续锁定旧的
                    # lib/market.json 日期；自选股仍优先读取 TQ 实时快照。
                    live = dayline_stock(stock, trade_date) if scope == "market" else realtime_stock(tq, stock)
                    if live:
                        stock_rows.append(live)
    finally:
        with contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            try:
                if tq is not None:
                    tq.close()
            except Exception:
                pass
    if connection_path is not None:
        try:
            connection_path.unlink(missing_ok=True)
        except OSError:
            pass

    if scope == "indices" and len([row for row in rows if row.get("realtime")]) < len(INDEXES):
        payload = public_fallback(scope, market, "TQ 指数快照为空或仅返回部分指数")
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    if scope == "watchlist" and not stock_rows:
        payload = public_fallback(scope, market, "TQ 自选股快照为空")
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    if scope == "market" and not stock_rows:
        payload = public_fallback(scope, market, f"通达信未返回 {trade_date or '最新'} 日线样本")
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    latest_indices = []
    if scope == "market":
        # The full-market request is also the browser boot snapshot.  Refresh
        # index cards from the same TDX date so the page cannot show 0908
        # indices beside a 20260911 stock universe.
        for index in market.get("indices", []):
            code = str(index.get("code") or "")
            index_market = str(index.get("market") or code[:2] or "sh").lower()
            # Preserve the web index key (for example ``sh000001``) so the
            # server-side merge replaces the 0908 baseline card instead of
            # appending a duplicate ``000001`` card.
            index_seed = {**index, "market": index_market, "code": code}
            latest_index = dayline_stock(index_seed, trade_date)
            if latest_index:
                latest_indices.append(latest_index)
    else:
        latest_indices = rows
    gain_rows = sorted(stock_rows, key=lambda x: (x.get("pct", 0), x.get("amount", 0)), reverse=True)
    amount_rows = sorted(stock_rows, key=lambda x: (x.get("amount", 0), x.get("pct", 0)), reverse=True)
    summary_stocks = [x for x in stock_rows if x.get("name") not in {"上证指数", "深证成指", "创业板指", "科创50", "上证50", "北证50"}]
    if scope == "market":
        up = sum(float(x.get("pct", 0)) > 0 for x in summary_stocks)
        down = sum(float(x.get("pct", 0)) < 0 for x in summary_stocks)
        flat = len(summary_stocks) - up - down
        bins = [
            sum(x.get("pct", 0) < -7 for x in summary_stocks),
            sum(-7 <= x.get("pct", 0) < -3 for x in summary_stocks),
            sum(-3 <= x.get("pct", 0) < 0 for x in summary_stocks),
            sum(x.get("pct", 0) == 0 for x in summary_stocks),
            sum(0 < x.get("pct", 0) <= 3 for x in summary_stocks),
            sum(3 < x.get("pct", 0) <= 7 for x in summary_stocks),
            sum(x.get("pct", 0) > 7 for x in summary_stocks),
        ]
    else:
        up, down, flat, bins = (market.get("up"), market.get("down"), market.get("flat"), market.get("bins", []))
    overview_rows = {x.get("code"): x for x in gain_rows[:100] + amount_rows[:100]}
    # The overview only needs a compact leaderboard, but the browser and the
    # Harness data page need the complete same-day universe.  Keep both shapes
    # explicit so callers never mistake the top-200 view for a full archive.
    all_stocks = stock_rows if scope == "market" else []
    print(json.dumps({
        "status": "ok",
        "source": "Tongdaxin TQ realtime snapshot",
        "fetchedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "tradeDate": trade_date,
        "indices": rows if scope == "indices" else latest_indices if scope == "market" else [],
        "stocks": list(overview_rows.values()) if scope in {"market", "watchlist"} else [],
        "allStocks": all_stocks,
        "marketSummary": {
            "currentCount": (len(summary_stocks) if scope == "market" else market.get("currentCount")),
            "up": up,
            "down": down,
            "flat": flat,
            "amount": (round(sum(float(x.get("amount", 0)) for x in summary_stocks)) or market.get("amount")) if scope == "market" else market.get("amount"),
            "bins": bins,
        },
        "replaceLeaderboard": scope == "market",
        "scope": "已刷新主要指数实时字段" if scope == "indices" else (f"已刷新 {len(stock_rows)} 只自选股实时字段" if scope == "watchlist" else f"已刷新 {len(stock_rows)} 只最新完整日线的价格、涨跌幅、成交额和量能；日期 {trade_date}"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
