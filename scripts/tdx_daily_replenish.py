#!/usr/bin/env python3
"""补齐已打开通达信终端中的当日 A 股日线缓存。"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import time
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

TDX_ROOT = Path(os.environ.get("ZHANGCAI_TDX_ROOT", r"C:\new_tdx_mock"))
USER_DIR = TDX_ROOT / "PYPlugins" / "user"
INIT_FILE = USER_DIR / "tdxdata_test.py"
DAY_RECORD = struct.Struct("<IIIIIfII")
DAY_DIRS = {
    "SH": TDX_ROOT / "vipdoc" / "sh" / "lday",
    "SZ": TDX_ROOT / "vipdoc" / "sz" / "lday",
    "BJ": TDX_ROOT / "vipdoc" / "bj" / "lday",
}


def connection_script(tag: str) -> Path:
    """每次补齐使用唯一 TQ 脚本名，避免与其他后台刷新任务冲突。"""
    session_dir = Path(os.environ.get("ZHANGCAI_DATA_DIR", Path(__file__).resolve().parents[1] / "data")) / "runtime" / "tq-sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    target = session_dir / f"tdxdata_replenish_{tag}_{os.getpid()}_{time.time_ns()}.py"
    shutil.copyfile(INIT_FILE, target)
    return target


def latest_date(path: Path) -> str | None:
    try:
        with path.open("rb") as handle:
            if path.stat().st_size < DAY_RECORD.size:
                return None
            handle.seek(-DAY_RECORD.size, 2)
            return str(DAY_RECORD.unpack(handle.read(DAY_RECORD.size))[0])
    except (OSError, struct.error):
        return None


def code_from_path(market: str, path: Path) -> str:
    return f"{path.stem[-6:]}.{market}"


def local_dates() -> tuple[str | None, dict[str, str | None], Counter[str]]:
    rows: dict[str, str | None] = {}
    counts: Counter[str] = Counter()
    for market, directory in DAY_DIRS.items():
        for path in directory.glob(f"{market.lower()}*.day"):
            code = code_from_path(market, path)
            date = latest_date(path)
            rows[code] = date
            if date:
                counts[date] += 1
    target = max((date for date, count in counts.items() if count >= 3000), default=None)
    return target, rows, counts


def normalize_codes(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        code = str(item).strip().upper()
        if code and "." in code:
            result.append(code)
    return sorted(set(result))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--pause", type=float, default=0.2)
    parser.add_argument("--all", action="store_true", help="刷新终端返回的全部股票，而不只补缺失日期")
    args = parser.parse_args()
    if args.batch_size < 1 or args.batch_size > 100:
        parser.error("--batch-size 必须在 1 到 100 之间")
    if not INIT_FILE.is_file():
        print(json.dumps({"status": "BLOCKED", "error": f"缺少 TQ 初始化文件：{INIT_FILE}"}, ensure_ascii=False))
        return 2

    target, before_rows, before_counts = local_dates()
    sys.path.insert(0, str(USER_DIR))
    os.chdir(TDX_ROOT)
    from tqcenter import tq  # type: ignore

    payload: dict[str, object] = {
        "schema": "ZHANGCAI_TDX_DAILY_REPLENISH_V1",
        "startedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "tdxRoot": str(TDX_ROOT),
        "targetDateBefore": target,
        "beforeDateCounts": dict(before_counts),
        "batchSize": args.batch_size,
        "batches": [],
    }
    session = connection_script("daily")
    try:
        tq.initialize(str(session))
        stock_list = normalize_codes(tq.get_stock_list(market="5", list_type=0))
        missing = [code for code in stock_list if before_rows.get(code) != target] if target and not args.all else stock_list
        payload["stockListCount"] = len(stock_list)
        payload["requestedCount"] = len(missing)
        payload["missingCodesBefore"] = missing if target and not args.all else []
        payload["mode"] = "all" if args.all else "missing-date"
        if not missing:
            payload["status"] = "NOOP"
        else:
            for offset in range(0, len(missing), args.batch_size):
                batch = missing[offset : offset + args.batch_size]
                try:
                    result = tq.refresh_kline(stock_list=batch, period="1d")
                    item = {"offset": offset, "count": len(batch), "ok": bool(result), "result": result if isinstance(result, (dict, list, str, int, float, bool)) else str(result)}
                except Exception as exc:  # keep later batches running and report the failed batch
                    item = {"offset": offset, "count": len(batch), "ok": False, "error": f"{type(exc).__name__}: {exc}"}
                payload["batches"].append(item)  # type: ignore[union-attr]
                print(json.dumps({"progress": min(offset + len(batch), len(missing)), "total": len(missing), "ok": item["ok"]}, ensure_ascii=False), flush=True)
                if args.pause > 0:
                    time.sleep(args.pause)
            payload["status"] = "DONE"
    except Exception as exc:
        payload["status"] = "ERROR"
        payload["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            tq.close()
        except Exception:
            pass
        session.unlink(missing_ok=True)

    target_after, after_rows, after_counts = local_dates()
    payload["finishedAt"] = datetime.now().astimezone().isoformat(timespec="seconds")
    payload["targetDateAfter"] = target_after
    payload["afterDateCounts"] = dict(after_counts)
    payload["targetDateRowsAfter"] = sum(1 for date in after_rows.values() if date == target_after)
    payload["missingCodesAfter"] = [
        code for code in (stock_list if 'stock_list' in locals() else [])
        if target_after and after_rows.get(code) != target_after
    ]
    payload["failedBatches"] = sum(1 for item in payload["batches"] if not item.get("ok"))  # type: ignore[index]
    output = Path(os.environ.get("ZHANGCAI_DATA_DIR", Path(__file__).resolve().parents[1] / "data")) / "runtime" / f"tdx-daily-replenish-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    payload["output"] = str(output)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("status") in {"DONE", "NOOP"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
