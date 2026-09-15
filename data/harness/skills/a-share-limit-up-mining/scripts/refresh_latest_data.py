#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests


DAY_RECORD = struct.Struct("<5If2I")
DEFAULT_ROOT = Path(r"C:\new_tdx_mock")
EASTMONEY_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latest_day(path: Path) -> str:
    if not path.is_file() or path.stat().st_size < DAY_RECORD.size:
        return ""
    with path.open("rb") as handle:
        handle.seek(-DAY_RECORD.size, os.SEEK_END)
        raw = handle.read(DAY_RECORD.size)
    value = DAY_RECORD.unpack(raw)[0]
    return str(value) if 19900101 <= value <= 20991231 else ""


def market_for_code(code: str) -> str:
    if code.startswith(("4", "8", "92")):
        return "bj"
    if code.startswith(("5", "6", "9")):
        return "sh"
    return "sz"


def day_path(root: Path, code: str) -> Path:
    market = market_for_code(code)
    return root / "vipdoc" / market / "lday" / f"{market}{code}.day"


def backup_once(path: Path, backup_dir: Path) -> str:
    if not path.exists():
        return ""
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"{path.name}.{sha256_file(path)[:16]}.bak"
    if not target.exists():
        shutil.copy2(path, target)
    return str(target)


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".codex-refresh.tmp")
    tmp.write_bytes(payload)
    os.replace(tmp, path)


def fetch_limit_pool(date_yyyymmdd: str) -> list[dict]:
    import akshare as ak

    frame = ak.stock_zt_pool_em(date=date_yyyymmdd)
    if frame is None or frame.empty:
        raise RuntimeError(f"limit-up pool is empty for {date_yyyymmdd}")
    rows = []
    for _, row in frame.iterrows():
        code = str(row.get("代码", "")).strip().zfill(6)
        if len(code) != 6 or not code.isdigit():
            continue
        rows.append({
            "code": code,
            "name": str(row.get("名称", "")).strip(),
            "close": float(row.get("最新价", 0) or 0),
            "change_pct": float(row.get("涨跌幅", 0) or 0),
            "boards": int(row.get("连板数", 0) or 0),
        })
    if not rows:
        raise RuntimeError(f"limit-up pool has no valid codes for {date_yyyymmdd}")
    return rows


def fetch_bars(session: requests.Session, code: str, begin: str, end: str) -> list[dict]:
    market = market_for_code(code)
    secid_market = 1 if market == "sh" else 0
    params = {
        "secid": f"{secid_market}.{code}",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "0",
        "beg": begin,
        "end": end,
        "lmt": "100",
    }
    last_error = ""
    for attempt in range(4):
        try:
            response = session.get(EASTMONEY_URL, params=params, timeout=20)
            response.raise_for_status()
            payload = response.json()
            lines = (payload.get("data") or {}).get("klines") or []
            bars = []
            for line in lines:
                parts = str(line).split(",")
                if len(parts) < 7:
                    continue
                bars.append({
                    "date": parts[0].replace("-", ""),
                    "open": float(parts[1]),
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                    "volume_lots": int(float(parts[5])),
                    "amount": float(parts[6]),
                })
            if bars:
                return bars
            last_error = "empty klines"
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {code}: {last_error}")


def pack_bar(bar: dict) -> bytes:
    return DAY_RECORD.pack(
        int(bar["date"]),
        int(round(float(bar["open"]) * 100)),
        int(round(float(bar["high"]) * 100)),
        int(round(float(bar["low"]) * 100)),
        int(round(float(bar["close"]) * 100)),
        float(bar["amount"]),
        int(round(float(bar["volume_lots"]) * 100)),
        0,
    )


def merge_day_file(path: Path, bars: list[dict], backup_dir: Path) -> dict:
    existing = path.read_bytes() if path.exists() else b""
    if len(existing) % DAY_RECORD.size:
        raise RuntimeError(f"invalid .day byte length: {path} ({len(existing)})")
    records = {}
    for offset in range(0, len(existing), DAY_RECORD.size):
        chunk = existing[offset:offset + DAY_RECORD.size]
        records[DAY_RECORD.unpack(chunk)[0]] = chunk
    before = max(records) if records else 0
    changed = False
    for bar in bars:
        key = int(bar["date"])
        packed = pack_bar(bar)
        if records.get(key) != packed:
            records[key] = packed
            changed = True
    if changed:
        backup = backup_once(path, backup_dir)
        atomic_write(path, b"".join(records[key] for key in sorted(records)))
    else:
        backup = ""
    return {
        "path": str(path),
        "before": str(before) if before else "",
        "after": latest_day(path),
        "changed": changed,
        "backup": backup,
        "sha256": sha256_file(path),
    }


def sync_ztc(root: Path, pool: list[dict], backup_dir: Path) -> dict:
    path = root / "T0002" / "blocknew" / "ZTC.blk"
    lines = []
    for row in pool:
        code = row["code"]
        market = market_for_code(code)
        prefix = "1" if market == "sh" else ("2" if market == "bj" else "0")
        lines.append(prefix + code)
    payload = ("\r\n".join(dict.fromkeys(lines)) + "\r\n").encode("gbk")
    current = path.read_bytes() if path.exists() else b""
    changed = current != payload
    backup = backup_once(path, backup_dir) if changed else ""
    if changed:
        atomic_write(path, payload)
    return {
        "path": str(path),
        "changed": changed,
        "codes": len(lines),
        "backup": backup,
        "sha256": sha256_file(path),
    }


def probe_latest(root: Path) -> str:
    probes = [
        root / "vipdoc" / "sh" / "lday" / "sh000001.day",
        root / "vipdoc" / "sz" / "lday" / "sz399001.day",
    ]
    dates = [latest_day(path) for path in probes]
    dates = [value for value in dates if value]
    return max(dates) if dates else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair latest TDX daily bars needed by 连板挖掘")
    parser.add_argument("--date", required=True, help="YYYYMMDD")
    parser.add_argument("--tdx-root", default=str(DEFAULT_ROOT))
    parser.add_argument("--poll-seconds", type=int, default=30)
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()

    if len(args.date) != 8 or not args.date.isdigit():
        raise SystemExit("--date must be YYYYMMDD")
    root = Path(args.tdx_root).resolve()
    if root != DEFAULT_ROOT.resolve():
        raise SystemExit(f"unexpected TDX root: {root}")
    evidence_path = Path(args.evidence).resolve()
    backup_dir = evidence_path.parent / f"tdx-refresh-backup-{args.date}"
    started = datetime.now().astimezone().isoformat()
    before = probe_latest(root)

    deadline = time.time() + max(0, args.poll_seconds)
    while before < args.date and time.time() < deadline:
        time.sleep(2)
        before = probe_latest(root)

    pool = fetch_limit_pool(args.date)
    ztc = sync_ztc(root, pool, backup_dir)
    required = [row for row in pool if market_for_code(row["code"]) in {"sh", "sz"}]
    missing = [row for row in required if latest_day(day_path(root, row["code"])) < args.date]
    touched = []
    errors = []
    if missing:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
        begin = (datetime.strptime(args.date, "%Y%m%d") - timedelta(days=10)).strftime("%Y%m%d")
        for row in missing:
            try:
                bars = fetch_bars(session, row["code"], begin, args.date)
                touched.append(merge_day_file(day_path(root, row["code"]), bars, backup_dir))
            except Exception as exc:
                errors.append(f"{row['code']}:{type(exc).__name__}:{exc}")

    stale_codes = [row["code"] for row in required if latest_day(day_path(root, row["code"])) != args.date]
    close_mismatches = []
    for row in required:
        path = day_path(root, row["code"])
        if latest_day(path) != args.date:
            continue
        raw = path.read_bytes()[-DAY_RECORD.size:]
        unpacked = DAY_RECORD.unpack(raw)
        close = unpacked[4] / 100.0
        high = unpacked[2] / 100.0
        if abs(close - row["close"]) > 0.011 or abs(high - close) > 0.011:
            close_mismatches.append({"code": row["code"], "pool_close": row["close"], "day_close": close, "day_high": high})

    after = probe_latest(root)
    status = "PASS" if not errors and not stale_codes and not close_mismatches and after == args.date else "BLOCKED"
    result = {
        "status": status,
        "trade_date": args.date,
        "started_at": started,
        "verified_at": datetime.now().astimezone().isoformat(),
        "tdx_root": str(root),
        "source": "Eastmoney limit-up pool and kline API; TDX local .day verification",
        "latest_before": before,
        "latest_after": after,
        "limit_pool_count": len(pool),
        "required_candidate_count": len(required),
        "candidate_files_repaired": len(touched),
        "touched_files": touched,
        "ztc": ztc,
        "stale_codes": stale_codes,
        "close_mismatches": close_mismatches,
        "errors": errors,
    }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
