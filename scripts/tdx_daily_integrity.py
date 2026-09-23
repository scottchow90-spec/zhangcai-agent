#!/usr/bin/env python3
"""全量检查并补齐通达信 A 股日线文件。

检查以通达信 TQ 返回的股票列表为准，文件内容以 .day 实际最后一条记录为准。
TQ 的 refresh_kline 在部分终端只返回“已提交”而不会立即改写文件，因此对缺口
再读取一次 TQ 1d 数据，并把当天 K 线按通达信 32 字节格式追加到本地文件。
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import urllib.parse
import urllib.request
import shutil
import time
from collections import Counter
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python 3.8 fallback
    ZoneInfo = None  # type: ignore
from pathlib import Path
from typing import Any

_tdx_root_text = os.environ.get("ZHANGCAI_TDX_ROOT", "").strip()
_packaged_runtime = os.environ.get("ZHANGCAI_PACKAGED") == "1"
TDX_ROOT = Path(_tdx_root_text) if _tdx_root_text else (
    Path(r"C:\new_tdx_mock") if not _packaged_runtime else Path(r"C:\__zhangcai_tdx_root_not_configured__")
)
DATA_ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
DAY = struct.Struct("<IIIIIfII")
MARKETS = ("SH", "SZ", "BJ")


def connection_script(tag: str) -> Path:
    """每个 TQ 会话使用独立脚本名，避免并发任务被 TQ 判定为同名策略。"""
    user = TDX_ROOT / "PYPlugins" / "user"
    template = user / "tdxdata_test.py"
    session_dir = DATA_ROOT / "runtime" / "tq-sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    target = session_dir / f"tdxdata_integrity_{tag}_{os.getpid()}_{time.time_ns()}.py"
    shutil.copyfile(template, target)
    return target


def date_from_file(path: Path) -> tuple[str | None, int, bool]:
    try:
        size = path.stat().st_size
        if size < DAY.size or size % DAY.size:
            return None, size // DAY.size, True
        value = DAY.unpack(path.read_bytes()[-DAY.size:])[0]
        text = str(value)
        return (text if len(text) == 8 else None), size // DAY.size, False
    except (OSError, struct.error):
        return None, 0, True


def code_path(code: str) -> Path:
    number, market = code.split(".", 1)
    return TDX_ROOT / "vipdoc" / market.lower() / "lday" / f"{market.lower()}{number}.day"


def find_existing_path(code: str) -> Path | None:
    direct = code_path(code)
    if direct.exists():
        return direct
    number = code.split(".", 1)[0]
    for market in MARKETS:
        candidate = TDX_ROOT / "vipdoc" / market.lower() / "lday" / f"{market.lower()}{number}.day"
        if candidate.exists():
            return candidate
    return None


def existing_stock_codes() -> list[str]:
    """在 TDX/TQ 未连接时恢复可审计的 A 股证券清单。"""
    # 优先使用本地市场快照中的 allStocks（通常 5559 只），它已排除
    # 指数、基金和可转债；只有快照不存在时才回退扫描 .day 文件。
    market_file = DATA_ROOT.parent / "lib" / "market.json"
    try:
        payload = json.loads(market_file.read_text(encoding="utf-8"))
        values = payload.get("allStocks") if isinstance(payload, dict) else None
        if isinstance(values, list):
            codes = []
            for item in values:
                if not isinstance(item, dict):
                    continue
                code = str(item.get("code") or "").strip()
                market = str(item.get("market") or "").strip().upper()
                if len(code) == 6 and code.isdigit() and market in MARKETS:
                    codes.append(f"{code}.{market}")
            if codes:
                return sorted(set(codes))
    except Exception:
        pass
    """使用本地 .day 文件作为最后的审计回退。"""
    codes: list[str] = []
    for market in MARKETS:
        folder = TDX_ROOT / "vipdoc" / market.lower() / "lday"
        if not folder.exists():
            continue
        for path in folder.glob(f"{market.lower()}*.day"):
            number = path.stem[len(market):]
            if number.isdigit() and len(number) == 6:
                codes.append(f"{number}.{market}")
    return sorted(set(codes))


def read_tq_stock_list() -> list[str]:
    user = TDX_ROOT / "PYPlugins" / "user"
    init = user / "tdxdata_test.py"
    if not init.is_file():
        raise RuntimeError(f"缺少 TQ 初始化文件：{init}")
    sys.path.insert(0, str(user))
    os.chdir(TDX_ROOT)
    from tqcenter import tq  # type: ignore

    session = connection_script("list")
    try:
        tq.initialize(str(session))
        raw = tq.get_stock_list(market="5", list_type=0)
        return sorted({str(item).strip().upper() for item in raw if isinstance(item, str) and "." in item})
    finally:
        tq.close()
        session.unlink(missing_ok=True)


def scan(codes: list[str], target: str | None = None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    dates = Counter[str]()
    for code in codes:
        path = find_existing_path(code)
        if path is None:
            row = {"code": code, "market": code.split(".", 1)[1], "path": str(code_path(code)), "status": "missing_file", "latestDate": None, "recordCount": 0, "aligned": False}
        else:
            latest, records, corrupt = date_from_file(path)
            if latest:
                dates[latest] += 1
            row = {"code": code, "market": code.split(".", 1)[1], "path": str(path), "status": "corrupt" if corrupt else "unknown", "latestDate": latest, "recordCount": records, "aligned": not corrupt}
        rows.append(row)
    resolved_target = target or (dates.most_common(1)[0][0] if dates else None)
    for row in rows:
        if row["status"] == "missing_file":
            row["status"] = "missing_file"
        elif not row["aligned"]:
            row["status"] = "corrupt"
        elif row["latestDate"] == resolved_target:
            row["status"] = "complete"
        else:
            row["status"] = "stale"
    return {
        "targetDate": resolved_target,
        "stockCount": len(codes),
        "completeCount": sum(row["status"] == "complete" for row in rows),
        "nonTradingCount": sum(row["status"] == "non_trading" for row in rows),
        "effectiveCompleteCount": sum(row["status"] in {"complete", "non_trading"} for row in rows),
        "staleCount": sum(row["status"] == "stale" for row in rows),
        "missingFileCount": sum(row["status"] == "missing_file" for row in rows),
        "corruptCount": sum(row["status"] == "corrupt" for row in rows),
        "effectiveMissingCount": sum(row["status"] not in {"complete", "non_trading"} for row in rows),
        "dateDistribution": dict(dates),
        "byMarket": {market: {"stockCount": sum(row["market"] == market for row in rows), "completeCount": sum(row["market"] == market and row["status"] == "complete" for row in rows), "nonTradingCount": sum(row["market"] == market and row["status"] == "non_trading" for row in rows), "effectiveCompleteCount": sum(row["market"] == market and row["status"] in {"complete", "non_trading"} for row in rows), "staleCount": sum(row["market"] == market and row["status"] == "stale" for row in rows), "missingFileCount": sum(row["market"] == market and row["status"] == "missing_file" for row in rows), "corruptCount": sum(row["market"] == market and row["status"] == "corrupt" for row in rows)} for market in MARKETS},
        "rows": rows,
    }


def frame_value(data: Any, key: str, symbol: str) -> Any:
    value = data.get(key)
    if value is None:
        return None
    try:
        series = value[symbol]
        return series.iloc[-1] if hasattr(series, "iloc") else None
    except Exception:
        return None


def frame_date(data: Any, symbol: str) -> str | None:
    value = data.get("Close")
    try:
        series = value[symbol]
        stamp = series.index[-1]
        return getattr(stamp, "strftime", lambda _fmt: str(stamp))("%Y%m%d")
    except Exception:
        return None


def public_kline(code: str, target: str) -> dict[str, Any] | None:
    """用带 Referer 的东方财富历史 K 线接口兜底。

    只接受明确返回 target 日期的记录；接口无记录、跨日记录或字段不完整时
    均返回 None，避免为了让完整率变高而写入猜测值。
    """
    number, market = code.split('.', 1)
    secid_market = 1 if market == 'SH' else 0
    query = urllib.parse.urlencode({
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f116',
        'ut': '7eea3edcaed734bea9cbfc24409ed989',
        'klt': '101', 'fqt': '0', 'secid': f'{secid_market}.{number}',
        'beg': target, 'end': target, 'lmt': '5',
    })
    url = f'https://push2his.eastmoney.com/api/qt/stock/kline/get?{query}'
    request = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (ZhangcaiAgent/1.0)',
        'Referer': 'https://quote.eastmoney.com/',
    })
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode('utf-8-sig'))
        rows = ((payload.get('data') or {}).get('klines') or [])
        for raw in rows:
            values = str(raw).split(',')
            if len(values) < 7 or values[0].replace('-', '') != target:
                continue
            numbers = [float(values[index]) for index in range(1, 7)]
            return {
                'date': values[0].replace('-', ''), 'open': numbers[0], 'close': numbers[1],
                'high': numbers[2], 'low': numbers[3], 'volume': numbers[4], 'amount': numbers[5],
                'url': url,
            }
    except Exception:
        return None
    return None


def quote_status(code: str) -> dict[str, Any] | None:
    """读取证券基础行情状态，用于区分无交易记录与未上市/停牌。"""
    number, market = code.split('.', 1)
    secid_market = 1 if market == 'SH' else 0
    query = urllib.parse.urlencode({
        'secid': f'{secid_market}.{number}',
        'fields': 'f43,f57,f58,f59,f60,f116,f117,f169,f170',
        'ut': '7eea3edcaed734bea9cbfc24409ed989',
    })
    url = f'https://push2.eastmoney.com/api/qt/stock/get?{query}'
    request = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (ZhangcaiAgent/1.0)',
        'Referer': 'https://quote.eastmoney.com/',
    })
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode('utf-8-sig'))
        data = payload.get('data')
        if not isinstance(data, dict) or not data.get('f57'):
            return None
        return {
            'url': url,
            'code': str(data.get('f57')),
            'name': data.get('f58'),
            'price': float(data.get('f43') or 0),
            'totalMarketCap': float(data.get('f116') or 0),
            'floatMarketCap': float(data.get('f117') or 0),
        }
    except Exception:
        return None


def local_security_metadata(code: str) -> dict[str, Any] | None:
    """读取通达信 base.dbf 的证券档案，作为行情接口受限时的本地状态依据。"""
    number, _market = code.split('.', 1)
    dbf = TDX_ROOT / 'T0002' / 'hq_cache' / 'base.dbf'
    try:
        raw = dbf.read_bytes()
        header_size = int.from_bytes(raw[8:10], 'little')
        record_size = int.from_bytes(raw[10:12], 'little')
        record_count = int.from_bytes(raw[4:8], 'little')
        for index in range(record_count):
            record = raw[header_size + index * record_size:header_size + (index + 1) * record_size]
            if len(record) < 16 or record[2:8].decode('latin1', 'ignore') != number:
                continue
            return {'provider': 'Tongdaxin base.dbf', 'path': str(dbf), 'listingDate': record[8:16].decode('latin1', 'ignore').strip()}
    except Exception:
        return None
    return None


def classify_non_trading(rows: list[dict[str, Any]], target: str) -> list[dict[str, Any]]:
    """把确认未上市/停牌的缺口纳入有效完整率，不生成虚假 K 线。"""
    accepted: list[dict[str, Any]] = []
    for row in rows:
        # stale 表示已有日线文件但尚未切到目标交易日。它们应由上面的
        # refresh_kline 批量下载，不能逐只走公开接口判成“停牌”。此前
        # 5559 只股票中约 5000 条 stale 会触发 5000 次串行请求，造成网页
        # 长时间停在“等待 DeepSeek 校验”。只有真正缺文件/损坏文件才做
        # 状态核验；未能核实的项目继续保留为 unresolved。
        if row.get('status') not in {'missing_file', 'corrupt'}:
            continue
        quote = quote_status(str(row['code']))
        metadata = local_security_metadata(str(row['code']))
        evidence = quote or metadata
        kind = ''
        reason = ''
        if quote and quote.get('price', 0) == 0:
            cap = float(quote.get('totalMarketCap') or 0)
            kind = 'suspended' if cap > 0 else 'unlisted'
            reason = '停牌（证券存在且总市值大于0，目标日无成交价）' if kind == 'suspended' else '未上市或暂无上市行情（证券元数据存在但总市值为0）'
        elif metadata:
            listing_date = str(metadata.get('listingDate') or '')
            if listing_date == '0' or (listing_date.isdigit() and listing_date > target):
                kind, reason = 'unlisted', '未上市（通达信证券档案显示上市日期晚于目标交易日或为0）'
            elif listing_date.isdigit() and listing_date <= target:
                kind, reason = 'suspended', '停牌或目标日无交易（证券档案已登记，但无目标日 K 线）'
        if not kind:
            continue
        row['status'] = 'non_trading'
        row['nonTradingType'] = kind
        row['nonTradingReason'] = reason
        row['quoteEvidence'] = evidence
        row['targetDate'] = target
        accepted.append({'code': row['code'], 'status': 'non_trading', 'type': kind, 'reason': reason, 'quoteEvidence': evidence})
    return accepted


def after_close_target_date() -> tuple[str | None, str]:
    """收盘切点统一为上海时间 16:30。

    16:30 之后的工作日必须以当天为目标，不能继续沿用上一份完整性报告的日期。
    周末不强行制造交易日，仍由文件日期分布决定目标日。
    """
    now = datetime.now(ZoneInfo("Asia/Shanghai")) if ZoneInfo else datetime.now().astimezone()
    after_cutoff = (now.hour, now.minute) >= (16, 30)
    if after_cutoff and now.weekday() < 5:
        return now.strftime("%Y%m%d"), now.isoformat(timespec="seconds")
    return None, now.isoformat(timespec="seconds")


def replenish(rows: list[dict[str, Any]], target: str, refresh: bool = False) -> list[dict[str, Any]]:
    user = TDX_ROOT / "PYPlugins" / "user"
    init = user / "tdxdata_test.py"
    sys.path.insert(0, str(user))
    os.chdir(TDX_ROOT)
    from tqcenter import tq  # type: ignore

    candidates = [row for row in rows if row["status"] in {"stale", "missing_file", "corrupt"}]
    result: list[dict[str, Any]] = []
    session = connection_script("repair")
    try:
        try:
            tq.initialize(str(session))
        except Exception:
            # TQ 初始化失败时仍生成完整性报告，避免网页只收到原始 Traceback。
            return [{"status": "blocked", "reason": "通达信 TQ 未连接；请确认 TdxW 已登录并启用 TQ 插件后重试", "candidateCount": len(candidates), "sourcesTried": ["Tongdaxin TQ"]}]
        if refresh and candidates:
            # refresh_kline 是通达信官方的批量下载入口。一次把 5570 只
            # 送入 get_market_data 会阻塞 TQ 分页数分钟，因此这里只提交
            # 分批刷新；文件是否真正写入由后续 scan 验收。
            candidate_codes = [row["code"] for row in candidates]
            for offset in range(0, len(candidate_codes), 200):
                try:
                    tq.refresh_kline(stock_list=candidate_codes[offset:offset + 200], period="1d")
                except Exception:
                    # 单批失败不影响后续批次，最终在 unresolved 中保留。
                    pass
        # 旧日期 stale 文件通常只提交批量刷新；残留数量较少时，下面会
        # 额外做一次批量读取并写入，实际缺失/损坏文件继续走公开源兜底。
        # 少量 stale 项可以直接批量读取最新一根日线并写入本地；当缺口
        # 很大时仍只提交 refresh_kline，避免一次 get_market_data 分页数千
        # 只而再次阻塞。这样 10~20 只残留缺口可以在一次点击中真正闭环。
        read_limit = max(0, int(os.environ.get("ZHANGCAI_TQ_REPAIR_READ_LIMIT", "200")))
        stale_rows = [row for row in candidates if row["status"] == "stale"]
        readable_stale_codes = {row["code"] for row in stale_rows} if len(stale_rows) <= read_limit else set()
        stale_repairs = [
            {"code": row["code"], "before": row["status"], "path": row["path"],
             "status": "refresh_submitted", "fetchedDate": None,
             "source": "Tongdaxin TQ refresh_kline(batch)"}
            for row in stale_rows if row["code"] not in readable_stale_codes
        ]
        result.extend(stale_repairs)
        candidates = [row for row in candidates if row["status"] in {"missing_file", "corrupt"} or row["code"] in readable_stale_codes]
        # TQ 支持一次请求一批证券；逐只请求在收盘后全量切换到新日期时会
        # 产生数千次 IPC，容易把刷新拖到超时。一次批量读取后逐行写入本地
        # .day 文件，缺失文件再走有限的公开历史 K 线兜底。
        data_batches: dict[str, Any] = {}
        candidate_codes = [item["code"] for item in candidates]
        try:
            batch = tq.get_market_data(stock_list=candidate_codes, period="1d", count=1)
            for code in candidate_codes:
                data_batches[code] = batch
        except Exception:
            for code in candidate_codes:
                data_batches[code] = {}
        public_budget = max(0, int(os.environ.get("ZHANGCAI_PUBLIC_KLINE_FALLBACK_LIMIT", "200")))
        public_attempts = 0
        for row in candidates:
            code = row["code"]
            item: dict[str, Any] = {"code": code, "before": row["status"], "path": row["path"], "status": "unresolved", "sourcesTried": []}
            try:
                item["sourcesTried"].append("Tongdaxin TQ get_market_data")
                data = data_batches.get(code, {})
                fetched_date = frame_date(data, code)
                source = "Tongdaxin TQ get_market_data"
                public = None
                # 新目标日切换时，所有旧日期文件都会进入 candidates；对这类
                # stale 项不逐只访问公开接口，避免收盘刷新触发数千次网络请求。
                # 公开源仅用于实际缺失/损坏文件，并受预算保护。
                if fetched_date != target and row["before"] in {"missing_file", "corrupt"} and public_attempts < public_budget:
                    item["sourcesTried"].append("东方财富历史K线(push2his)")
                    public_attempts += 1
                    public = public_kline(code, target)
                    if public:
                        fetched_date = public["date"]
                        source = "东方财富历史K线(push2his)"
                if fetched_date != target:
                    item.update({"fetchedDate": fetched_date, "reason": "TQ 与公开历史 K 线均未返回目标交易日数据"})
                    result.append(item)
                    continue
                def number(key: str, scale: float = 1.0, default: float = 0.0) -> float:
                    if public is not None:
                        mapping = {'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume', 'Amount': 'amount'}
                        value = public.get(mapping.get(key, key))
                    else:
                        value = frame_value(data, key, code)
                    try:
                        return float(value) * scale if value is not None else default
                    except (TypeError, ValueError):
                        return default
                path = Path(row["path"])
                path.parent.mkdir(parents=True, exist_ok=True)
                reserved = 0
                if path.exists() and path.stat().st_size >= DAY.size:
                    try:
                        reserved = DAY.unpack(path.read_bytes()[-DAY.size:])[-1]
                    except (OSError, struct.error):
                        reserved = 0
                packed = DAY.pack(int(target), round(number("Open", 100)), round(number("High", 100)), round(number("Low", 100)), round(number("Close", 100)), number("Amount", 10000), round(number("Volume")), reserved)
                with path.open("ab") as handle:
                    handle.write(packed)
                item.update({"status": "written", "fetchedDate": fetched_date, "recordAppended": 1, "source": source})
            except Exception as exc:
                item["reason"] = f"{type(exc).__name__}: {exc}"
            result.append(item)
    finally:
        tq.close()
        session.unlink(missing_ok=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-date", default="", help="YYYYMMDD；默认按上海时间 16:30 收盘切点选择目标日")
    parser.add_argument("--refresh", action="store_true", help="先通过 TQ 提交缺口刷新，再读取并写入 .day 文件")
    args = parser.parse_args()
    started = datetime.now().astimezone().isoformat(timespec="seconds")
    tdx_error = ""
    try:
        codes = read_tq_stock_list()
    except Exception as exc:
        tdx_error = "通达信 TQ 未连接；已使用本地日线文件生成审计结果，请登录 TdxW 并启用 TQ 后重试"
        codes = existing_stock_codes()
        if not codes:
            print(json.dumps({"status": "BLOCKED", "reason": tdx_error}, ensure_ascii=False))
            return 2
    cutoff_target, shanghai_now = after_close_target_date()
    requested_target = args.target_date or cutoff_target
    before = scan(codes, requested_target or None)
    target = before["targetDate"]
    repairs = replenish(before["rows"], target, refresh=args.refresh) if target else []
    after = scan(codes, target)
    # TQ 未连接时不能通过报价接口判定停牌/未上市；保留 stale/missing 为
    # 未解决项，避免把整批旧日线误计入“有效完整”。
    non_trading = classify_non_trading(after["rows"], target) if target and not tdx_error else []
    # 物理文件统计与业务有效完整率分开保留：未上市/停牌没有日线是正常状态，
    # 但仍在报告中记录其缺失文件数量，便于审计实际落盘情况。
    after["nonTradingCount"] = sum(row["status"] == "non_trading" for row in after["rows"])
    after["effectiveCompleteCount"] = sum(row["status"] in {"complete", "non_trading"} for row in after["rows"])
    after["effectiveMissingCount"] = sum(row["status"] not in {"complete", "non_trading"} for row in after["rows"])
    for market in MARKETS:
        bucket = after["byMarket"][market]
        bucket["nonTradingCount"] = sum(row["market"] == market and row["status"] == "non_trading" for row in after["rows"])
        bucket["effectiveCompleteCount"] = sum(row["market"] == market and row["status"] in {"complete", "non_trading"} for row in after["rows"])
    report = {
        "schema": "ZHANGCAI_TDX_DAILY_INTEGRITY_V1",
        "startedAt": started,
        "finishedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "tdxRoot": str(TDX_ROOT),
        "stockListSource": "Tongdaxin TQ get_stock_list(market=5)",
        "timezone": "Asia/Shanghai",
        "closeRefreshCutoff": "16:30",
        "checkedAtShanghai": shanghai_now,
        "targetSelection": "explicit --target-date" if args.target_date else ("after-close current weekday" if cutoff_target else "latest file date distribution"),
        "tdxConnection": "connected" if not tdx_error else "unavailable",
        "tdxConnectionMessage": tdx_error,
        "targetDate": target,
        "before": {key: value for key, value in before.items() if key != "rows"},
        "repairs": repairs,
        "after": {key: value for key, value in after.items() if key != "rows"},
        "nonTrading": non_trading,
        "unresolved": [item for item in after["rows"] if item["status"] not in {"complete", "non_trading"}],
        "complete": after["effectiveCompleteCount"] == after["stockCount"],
    }
    submitted = sum(1 for item in repairs if item.get("status") == "refresh_submitted")
    written = sum(1 for item in repairs if item.get("status") == "written")
    report["refreshSubmissionCount"] = submitted
    report["writtenCount"] = written
    # refresh_kline 只向通达信提交下载请求；在客户端尚未完成“盘后数据下载”
    # 时，TQ 可能返回成功但 .day 文件仍停在上一交易日。把这个事实写进报告，
    # 网页和 Harness 可以明确提示用户完成一次客户端操作，而不是误报为已补齐。
    if report["unresolved"] and submitted:
        report["manualActionRequired"] = True
        report["manualAction"] = "请在通达信客户端登录后执行一次“盘后数据下载/日线数据下载”，等待完成后再点击补齐；TQ refresh_kline 仅提交请求，不保证立即写入 .day 文件。"
    else:
        report["manualActionRequired"] = False
        report["manualAction"] = ""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = DATA_ROOT / "runtime" / f"tdx-daily-integrity-{stamp}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    report["output"] = str(output)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    markdown = output.with_suffix('.md')
    unresolved_lines = '\n'.join(
        f"| {item['code']} | {item['market']} | {item['status']} | {item.get('latestDate') or '—'} |"
        for item in report['unresolved']
    ) or '| — | — | complete | — |'
    markdown_text = (
        f"# 通达信个股日线完整性报告\n\n"
        f"- 目标交易日：**{target or '—'}**\n"
        f"- 股票清单：**{after['stockCount']}** 只（来源：TQ get_stock_list(market=5)）\n"
        f"- 文件已对齐：**{after['completeCount']}** 只；未上市/停牌按规则计入有效完整：**{after['nonTradingCount']}** 只\n"
        f"- 有效完整率：**{after['effectiveCompleteCount']}/{after['stockCount']}**；stale：**{after['staleCount']}** 只；物理缺失文件：**{after['missingFileCount']}** 只；损坏：**{after['corruptCount']}** 只\n"
        f"- 本轮写入：**{written}** 条；仍需补齐：**{len(report['unresolved'])}** 只\n\n"
        + (f"- **需要人工完成通达信盘后数据下载**：TQ 已提交 {submitted} 批，但仍有 {len(report['unresolved'])} 只文件未切到目标日。\n\n" if report["manualActionRequired"] else "")
        + f"## 未补齐清单\n\n| 代码 | 市场 | 状态 | 文件最后日期 |\n|---|---|---|---|\n{unresolved_lines}\n\n"
        + "## 未上市/停牌豁免清单\n\n"
        + ('\n'.join(f"- **{item['code']}**：{item['type']}，{item['reason']}" for item in report['nonTrading']) or '- 无')
        + "\n\n## 补齐来源与结果\n\n"
        + "每个缺口依次尝试通达信 TQ `get_market_data(period=1d)` 与带 Referer 的东方财富 `push2his` 历史 K 线。只有明确返回目标日期时才会写入 `.day`；没有返回的数据保持缺口，不用估算值。\n\n"
        + (f"人工动作：{report['manualAction']}\n\n" if report["manualActionRequired"] else "")
        + f"JSON 明细：`{output}`\n"
    )
    markdown.write_text(markdown_text, encoding='utf-8')
    report["markdown"] = str(markdown)
    # 将 markdown 路径同步回 JSON，方便网页和 Harness 直接定位人类可读版本。
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"status": "COMPLETE" if report["complete"] else "PARTIAL", "targetDate": target, "before": report["before"], "repairs": repairs, "after": report["after"], "unresolved": report["unresolved"], "output": str(output), "markdown": str(markdown)}, ensure_ascii=False, indent=2, default=str))
    return 0 if report["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
