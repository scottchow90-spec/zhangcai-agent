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
from collections import Counter
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TDX_ROOT = Path(os.environ.get("ZHANGCAI_TDX_ROOT", r"C:\new_tdx_mock"))
USER_DIR = TDX_ROOT / "PYPlugins" / "user"
MARKET_FILE = Path(__file__).resolve().parents[1] / "lib" / "market.json"
DAY_RECORD = struct.Struct("<IIIIIfII")
CONNECTION_TEMPLATE = USER_DIR / "tdxdata_test.py"


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
            return print_tq_error(scope, False, RuntimeError("TDX_NOT_RUNNING"))
        sys.path.insert(0, str(USER_DIR))
        os.chdir(TDX_ROOT)
        try:
            from tqcenter import tq as tq_api  # type: ignore
            tq = tq_api
            connection_path = connection_script(scope)
        except Exception as error:
            return print_tq_error(scope, True, error)

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
            return print_tq_error(scope, tdx_is_running(), error)
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

    if scope == "indices" and not rows:
        print(json.dumps({"status": "error", "error": "通达信未返回指数实时快照"}, ensure_ascii=False))
        return 2
    if scope == "watchlist" and not stock_rows:
        stock_rows = list(market.get("stocks", []))
    if scope == "market" and not stock_rows:
        print(json.dumps({"status": "error", "error": f"通达信未返回 {trade_date or '最新'} 日线样本"}, ensure_ascii=False))
        return 2
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
    print(json.dumps({
        "status": "ok",
        "source": "Tongdaxin TQ realtime snapshot",
        "fetchedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "tradeDate": trade_date,
        "indices": rows if scope == "indices" else [],
        "stocks": list(overview_rows.values()) if scope in {"market", "watchlist"} else [],
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
