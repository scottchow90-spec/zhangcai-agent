#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import datetime as dt
import json
import os
import struct
import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# K线数据源硬闸（2026-05-28）：只允许 C:\new_tdx_mock
# ═══════════════════════════════════════════════════════════════
DEFAULT_ROOT = Path(r"C:\new_tdx_mock")
_REQUIRED_ROOT = Path(r"C:\new_tdx_mock")
if not _REQUIRED_ROOT.exists():
    print(json.dumps({"ok": False, "error": "KLINE_DATA_SOURCE_BLOCKED: C:\\new_tdx_mock does not exist", "gate": "tdx_local_data.py::D-drive-check"}, ensure_ascii=False), file=sys.stderr)
    sys.exit(73)
DEFAULT_ROOTS = [("tdxmoni_raw", DEFAULT_ROOT)]
DAY_RECORD = struct.Struct("<IIIIIfII")
LC5_RECORD = struct.Struct("<HHfffffII")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def json_out(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def parse_roots(root_arg: str | None) -> list[tuple[str, Path]]:
    _REQUIRED_ROOT = Path(r"C:\new_tdx_mock")
    if not root_arg or root_arg == "auto":
        return DEFAULT_ROOTS
    items: list[tuple[str, Path]] = []
    for index, raw_item in enumerate(root_arg.split(";")):
        raw_item = raw_item.strip()
        if not raw_item:
            continue
        if "=" in raw_item:
            label, path_str = raw_item.split("=", 1)
        else:
            label, path_str = f"root{index + 1}", raw_item
        p = Path(path_str.strip())
        if p.resolve() != _REQUIRED_ROOT.resolve():
            json_out({"ok": False, "error": f"KLINE_DATA_SOURCE_BLOCKED: --root must be {_REQUIRED_ROOT}, got {p}", "gate": "tdx_local_data.py::parse_roots"})
            sys.exit(73)
        items.append((label.strip() or f"root{index + 1}", p))
    return items or DEFAULT_ROOTS


def normalize_symbol(symbol: str) -> str:
    raw = symbol.strip().lower().replace(".", "").replace("_", "")
    if raw.startswith(("sh", "sz", "bj")) and len(raw) >= 8:
        return raw[:2] + raw[-6:]
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) < 6:
        raise ValueError(f"invalid symbol: {symbol}")
    code = digits[-6:]
    if code.startswith("920") or code.startswith(("4", "8")):
        market = "bj"
    elif code.startswith(("5", "6", "9")):
        market = "sh"
    else:
        market = "sz"
    return market + code


def symbol_suffix(symbol: str) -> str:
    value = normalize_symbol(symbol)
    return value[2:] + "." + value[:2].upper()


def market_dir(symbol: str) -> str:
    value = normalize_symbol(symbol)
    if value.startswith("bj"):
        return "sz"
    return value[:2]


def file_meta(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"exists": False, "size": 0, "updated_at": None}
    stat = path.stat()
    return {
        "exists": True,
        "size": stat.st_size,
        "updated_at": dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def day_path(root: Path, symbol: str) -> Path:
    value = normalize_symbol(symbol)
    market = market_dir(value)
    candidates = [
        root / "vipdoc" / market / "lday" / f"{value}.day",
        root / "vipdoc" / "xinzeng" / market / "lday" / f"{value}.day",
        root / "vipdoc" / "xinzeng" / f"{value}.day",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def lc5_path(root: Path, symbol: str) -> Path:
    value = normalize_symbol(symbol)
    market = market_dir(value)
    candidates = [
        root / "vipdoc" / market / "fzline" / f"{value}.lc5",
        root / "vipdoc" / "xinzeng" / market / "fzline" / f"{value}.lc5",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def parse_day_record(chunk: bytes) -> dict[str, object]:
    date_i, open_i, high_i, low_i, close_i, amount, volume, _unused = DAY_RECORD.unpack(chunk)
    return {
        "date": str(date_i),
        "open": open_i / 100.0,
        "high": high_i / 100.0,
        "low": low_i / 100.0,
        "close": close_i / 100.0,
        "amount": float(amount),
        "volume": int(volume),
    }


def parse_lc5_date(date_word: int, minute_word: int) -> tuple[str, str]:
    year = (date_word // 2048) + 2004
    month = (date_word % 2048) // 100
    day = (date_word % 2048) % 100
    hour = minute_word // 60
    minute = minute_word % 60
    try:
        date_s = dt.date(year, month, day).isoformat()
        time_s = f"{hour:02d}:{minute:02d}:00"
    except ValueError:
        date_s = str(date_word)
        time_s = str(minute_word)
    return date_s, time_s


def parse_lc5_record(chunk: bytes) -> dict[str, object]:
    date_w, minute_w, open_p, high_p, low_p, close_p, amount, volume, _unused = LC5_RECORD.unpack(chunk)
    date_s, time_s = parse_lc5_date(date_w, minute_w)
    return {
        "date": date_s,
        "time": time_s,
        "open": round(float(open_p), 4),
        "high": round(float(high_p), 4),
        "low": round(float(low_p), 4),
        "close": round(float(close_p), 4),
        "amount": float(amount),
        "volume": int(volume),
    }


def read_fixed_records(path: Path, record_struct: struct.Struct, parser, limit: int | None = None) -> list[dict[str, object]]:
    if not path.exists():
        return []
    count = path.stat().st_size // record_struct.size
    if count <= 0:
        return []
    read_count = count if not limit or limit <= 0 or limit >= count else limit
    start = (count - read_count) * record_struct.size
    rows: list[dict[str, object]] = []
    with path.open("rb") as fh:
        fh.seek(start)
        for _ in range(read_count):
            chunk = fh.read(record_struct.size)
            if len(chunk) != record_struct.size:
                break
            rows.append(parser(chunk))
    return rows


def read_block_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="gbk", errors="ignore")
    return [line.strip().lstrip("\ufeff") for line in text.splitlines() if line.strip()]


def block_files(root: Path) -> list[Path]:
    block_dir = root / "T0002" / "blocknew"
    if not block_dir.exists():
        return []
    return sorted(block_dir.glob("*.blk"))


def read_best_kline(roots: list[tuple[str, Path]], symbol: str, period: str, limit: int) -> dict[str, object]:
    for label, root in roots:
        path = day_path(root, symbol) if period == "day" else lc5_path(root, symbol)
        records = (
            read_fixed_records(path, DAY_RECORD, parse_day_record, limit)
            if period == "day"
            else read_fixed_records(path, LC5_RECORD, parse_lc5_record, limit)
        )
        if records:
            return {
                "ok": True,
                "source_path": label,
                "period": period,
                "path": str(path),
                "meta": file_meta(path),
                "records": records,
            }
    return {"ok": False, "period": period, "records": []}


def command_summary(args: argparse.Namespace) -> int:
    roots = parse_roots(args.root)
    payload = []
    for label, root in roots:
        payload.append(
            {
                "source_path": label,
                "root": str(root),
                "exists": root.exists(),
                "block_count": len(block_files(root)),
                "sample_block_dir": str(root / "T0002" / "blocknew"),
                "sample_day_path": str(day_path(root, "600000")),
                "sample_lc5_path": str(lc5_path(root, "600000")),
            }
        )
    json_out({"sources": payload})
    return 0


def command_kline(args: argparse.Namespace) -> int:
    roots = parse_roots(args.root)
    payload = read_best_kline(roots, args.symbol, args.period, args.limit)
    payload.update({"symbol": symbol_suffix(args.symbol)})
    json_out(payload)
    return 0 if payload.get("ok") else 2


def command_blocks(args: argparse.Namespace) -> int:
    items = []
    for label, root in parse_roots(args.root):
        for path in block_files(root):
            symbols = read_block_file(path)
            sample_symbols = []
            for item in symbols[:10]:
                try:
                    sample_symbols.append(symbol_suffix(item))
                except Exception:
                    continue
            items.append(
                {
                    "source_path": label,
                    "name": path.stem,
                    "path": str(path),
                    "symbols": len(symbols),
                    "sample": sample_symbols,
                    "updated_at": dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                }
            )
    json_out({"blocks": items})
    return 0


def command_block(args: argparse.Namespace) -> int:
    errors: list[dict[str, object]] = []
    roots = parse_roots(args.root)
    for idx, (label, root) in enumerate(roots):
        name = args.name
        path = root / "T0002" / "blocknew" / (name if name.lower().endswith(".blk") else name + ".blk")
        symbols = read_block_file(path)
        if symbols:
            json_out(
                {
                    "ok": True,
                    "source_path": label,
                    "name": path.stem,
                    "path": str(path),
                    "exists": path.exists(),
                    "fallback_used": idx > 0,
                    "count": len(symbols),
                    "symbols": [symbol_suffix(symbol) for symbol in symbols],
                }
            )
            return 0
        errors.append({"source_path": label, "path": str(path), "exists": path.exists(), "error": "empty or missing"})
    json_out({"ok": False, "name": args.name, "count": 0, "symbols": [], "errors": errors})
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read local TongDaXin data from configured local roots.")
    parser.add_argument("--root", default=os.environ.get("TDX_ROOTS", "auto"))
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("summary", help="summarize available local TDX data").set_defaults(func=command_summary)

    kline = sub.add_parser("kline", help="read one symbol kline records")
    kline.add_argument("symbol")
    kline.add_argument("--period", choices=["day", "lc5"], default="day")
    kline.add_argument("--limit", type=int, default=20)
    kline.set_defaults(func=command_kline)

    sub.add_parser("blocks", help="list blocknew stock pools").set_defaults(func=command_blocks)

    block = sub.add_parser("block", help="read one blocknew stock pool")
    block.add_argument("name")
    block.set_defaults(func=command_block)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"tdx_local_data error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
