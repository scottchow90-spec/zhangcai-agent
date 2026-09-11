#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import contextlib
import datetime as dt
import hashlib
import io
import json
import os
import re
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    import msvcrt
except ImportError:  # pragma: no cover - this skill is deployed on Windows.
    msvcrt = None

TDX_ROOT = Path(os.environ.get("TDX_ROOT", r"C:\new_tdx_mock"))
TQ_USER_DIR = TDX_ROOT / "PYPlugins" / "user"
TQCENTER = TQ_USER_DIR / "tqcenter.py"
TQ_INIT_PRIMARY = TQ_USER_DIR / "openclaw_tq_test.py"
TQ_INIT_FALLBACK = TQ_USER_DIR / "tdxdata_test.py"
VIPDOC = TDX_ROOT / "vipdoc"
GS_BAK = TDX_ROOT / "T0002" / "gs_bak"
BLOCKNEW = TDX_ROOT / "T0002" / "blocknew"
NEWS_DIRS = [
    TDX_ROOT / "T0002" / "msg_zx",
    TDX_ROOT / "T0002" / "msg_web",
    TDX_ROOT / "T0002" / "hq_cache",
    TDX_ROOT / "T0002" / "info_cache",
    TDX_ROOT / "T0002" / "cache",
]
_DATA_ROOT = os.environ.get("ONESTOCK_STOCK_DATA_ROOT", "").strip()
TQ_LOCK_PATH = (
    Path(_DATA_ROOT).expanduser().resolve() / "runtime" / "skills" / "tdx-local-hub" / "tq.lock"
    if _DATA_ROOT
    else Path(__file__).resolve().parents[1] / ".runtime" / "tq.lock"
)

DAY_RECORD = struct.Struct("<IIIIIfII")
LC5_RECORD = struct.Struct("<HHfffffII")
BOND_CODE_PREFIXES = ("110", "111", "113", "118", "123", "127", "128", "132")

CORE_FORMULAS: dict[str, dict[str, Any]] = {
    # Public workflow and runtime both use the installed current formula name.
    "大牛线4.0": {"kind": "zb", "count": 20, "dividend_type": 1, "call_name": "大牛线撑压版"},
    "大牛线撑压版": {"kind": "zb", "count": 20, "dividend_type": 1},
    "飞龙在天": {"kind": "zb", "count": 0, "dividend_type": 0},
    "游资资金监控": {"kind": "zb", "count": 5, "dividend_type": 0},
    "机构资金监控": {"kind": "zb", "count": 5, "dividend_type": 0},
    "庄家资金监控": {"kind": "zb", "count": 5, "dividend_type": 0},
    "飞龙在天选股": {"kind": "xg", "count": 0, "dividend_type": 0},
}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="milliseconds")


def emit(payload: dict[str, Any], code: int = 0) -> None:
    payload.setdefault("generated_at", now())
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    raise SystemExit(code)


def file_meta(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False}
    stat = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "size": stat.st_size,
        "updated_at": dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def normalize_symbol(symbol: str) -> str:
    raw = symbol.strip().lower().replace("_", "")
    suffix_match = re.fullmatch(r"(\d{6})\.?(sh|sz|bj)", raw)
    if suffix_match:
        return suffix_match.group(2) + suffix_match.group(1)
    prefix_match = re.fullmatch(r"(sh|sz|bj)\.?(\d{6})", raw)
    if prefix_match:
        return prefix_match.group(1) + prefix_match.group(2)
    raw = raw.replace(".", "")
    if raw.startswith(("sh", "sz", "bj")) and len(raw) >= 8:
        return raw[:2] + raw[-6:]
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) < 6:
        raise ValueError(f"invalid symbol: {symbol}")
    code = digits[-6:]
    # 北交所新股使用 920xxx，不能按普通 9xxxxx 上海代码处理。
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
        return "bj"
    return value[:2]


def day_path(symbol: str) -> Path:
    value = normalize_symbol(symbol)
    market = market_dir(value)
    candidates = [
        VIPDOC / market / "lday" / f"{value}.day",
        VIPDOC / "xinzeng" / market / "lday" / f"{value}.day",
        VIPDOC / "xinzeng" / f"{value}.day",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def lc5_path(symbol: str) -> Path:
    value = normalize_symbol(symbol)
    market = market_dir(value)
    candidates = [
        VIPDOC / market / "fzline" / f"{value}.lc5",
        VIPDOC / "xinzeng" / market / "fzline" / f"{value}.lc5",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def parse_day_record(chunk: bytes, price_divisor: float = 100.0) -> dict[str, Any]:
    date_i, open_i, high_i, low_i, close_i, amount, volume, _unused = DAY_RECORD.unpack(chunk)
    return {
        "date": str(date_i),
        "open": open_i / price_divisor,
        "high": high_i / price_divisor,
        "low": low_i / price_divisor,
        "close": close_i / price_divisor,
        "amount": float(amount),
        "volume": int(volume),
    }


def parse_lc5_record(chunk: bytes) -> dict[str, Any]:
    date_w, minute_w, open_p, high_p, low_p, close_p, amount, volume, _unused = LC5_RECORD.unpack(chunk)
    year = (date_w // 2048) + 2004
    month = (date_w % 2048) // 100
    day = (date_w % 2048) % 100
    hour = minute_w // 60
    minute = minute_w % 60
    try:
        date_s = dt.date(year, month, day).isoformat()
        time_s = f"{hour:02d}:{minute:02d}:00"
    except ValueError:
        date_s = str(date_w)
        time_s = str(minute_w)
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


def read_records(path: Path, record_struct: struct.Struct, parser, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    count = path.stat().st_size // record_struct.size
    if count <= 0:
        return []
    read_count = min(count, limit) if limit > 0 else count
    rows = []
    with path.open("rb") as handle:
        handle.seek((count - read_count) * record_struct.size)
        for _ in range(read_count):
            chunk = handle.read(record_struct.size)
            if len(chunk) != record_struct.size:
                break
            rows.append(parser(chunk))
    return rows


def day_price_divisor(symbol: str) -> float:
    code = normalize_symbol(symbol)[2:]
    return 10000.0 if code.startswith(BOND_CODE_PREFIXES) else 100.0


def read_day_records(symbol: str, limit: int) -> list[dict[str, Any]]:
    divisor = day_price_divisor(symbol)
    return read_records(
        day_path(symbol),
        DAY_RECORD,
        lambda chunk: parse_day_record(chunk, divisor),
        limit,
    )


def read_text(path: Path, max_chars: int = 2000) -> tuple[str, str]:
    raw = path.read_bytes()[: max_chars * 4]
    for enc in ("utf-8-sig", "gb18030", "gbk", "utf-16", "latin1"):
        try:
            return raw.decode(enc, errors="replace")[:max_chars], enc
        except Exception:
            continue
    return "", "unreadable"


def read_block_file(path: Path) -> list[str]:
    if not path.exists() or path.stat().st_size <= 0:
        return []
    text, _enc = read_text(path, max_chars=200000)
    symbols = []
    for token in text.replace("\r", "\n").replace(",", "\n").splitlines():
        token = token.strip().lstrip("\ufeff")
        if token:
            symbols.append(token)
    return symbols


def load_tq():
    if not TDX_ROOT.exists():
        raise FileNotFoundError(str(TDX_ROOT))
    if not TQCENTER.exists():
        raise FileNotFoundError(str(TQCENTER))
    os.chdir(str(TDX_ROOT))
    sys.path.insert(0, str(TQ_USER_DIR))
    from tqcenter import tq  # type: ignore
    init_path = TQ_INIT_PRIMARY if TQ_INIT_PRIMARY.exists() else TQ_INIT_FALLBACK
    if not init_path.exists():
        raise FileNotFoundError(f"missing TQ init: {TQ_INIT_PRIMARY} / {TQ_INIT_FALLBACK}")
    tq.initialize(str(init_path))
    return tq, init_path


class TQLock:
    def __init__(self, timeout_seconds: float = 30.0, poll_seconds: float = 0.05) -> None:
        self.timeout_seconds = timeout_seconds
        self.poll_seconds = poll_seconds
        self.handle = None
        self.waited_ms = 0.0

    def __enter__(self) -> "TQLock":
        if msvcrt is None:
            return self
        TQ_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.handle = TQ_LOCK_PATH.open("a+b")
        self.handle.seek(0, os.SEEK_END)
        if self.handle.tell() == 0:
            self.handle.write(b"0")
            self.handle.flush()
        start = time.perf_counter()
        while True:
            try:
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
                self.waited_ms = round((time.perf_counter() - start) * 1000, 3)
                return self
            except OSError:
                if time.perf_counter() - start > self.timeout_seconds:
                    raise TimeoutError(f"TQ lock timeout: {TQ_LOCK_PATH}")
                time.sleep(self.poll_seconds)

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        if self.handle is None or msvcrt is None:
            return
        try:
            self.handle.seek(0)
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            self.handle.close()


def formula_registry() -> dict[str, Any]:
    formulas = {}
    for name, meta in CORE_FORMULAS.items():
        formulas[name] = {"name": name, "core": True, **meta}
    if GS_BAK.exists():
        for path in sorted(GS_BAK.glob("*.txt")):
            name = path.stem
            meta = formulas.get(name, {"name": name, "core": False})
            meta.update(file_meta(path))
            if "kind" not in meta:
                meta["kind"] = "xg" if "选股" in name else "zb"
            formulas[name] = meta
    return {
        "ok": True,
        "root": str(TDX_ROOT),
        "source": str(GS_BAK),
        "count": len(formulas),
        "formulas": sorted(formulas.values(), key=lambda item: item["name"]),
    }


def detect_tdx_process() -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Process TdxW -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,StartTime | ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
        text = (result.stdout or "").strip()
        if not text:
            return {"running": False}
        data = json.loads(text)
        if isinstance(data, list):
            data = data[0] if data else {}
        return {"running": bool(data), "id": data.get("Id"), "name": data.get("ProcessName"), "start_time": data.get("StartTime")}
    except Exception as exc:
        return {"running": False, "error": str(exc)}


def cmd_status(_args: argparse.Namespace) -> None:
    start = time.perf_counter()
    registry = formula_registry()
    payload = {
        "ok": TDX_ROOT.exists(),
        "root": file_meta(TDX_ROOT),
        "vipdoc": file_meta(VIPDOC),
        "tq_user_dir": file_meta(TQ_USER_DIR),
        "tqcenter": file_meta(TQCENTER),
        "tq_init_primary": file_meta(TQ_INIT_PRIMARY),
        "tq_init_fallback": file_meta(TQ_INIT_FALLBACK),
        "gs_bak": file_meta(GS_BAK),
        "blocknew": file_meta(BLOCKNEW),
        "tdx_process": detect_tdx_process(),
        "formula_count": registry["count"],
        "news_dirs": [file_meta(path) for path in NEWS_DIRS],
        "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
    }
    emit(payload, 0 if payload["ok"] else 2)


def cmd_registry(_args: argparse.Namespace) -> None:
    start = time.perf_counter()
    payload = formula_registry()
    payload["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 3)
    emit(payload)


def cmd_kline(args: argparse.Namespace) -> None:
    start = time.perf_counter()
    path = day_path(args.symbol) if args.period == "day" else lc5_path(args.symbol)
    rows = read_day_records(args.symbol, args.limit) if args.period == "day" else read_records(path, LC5_RECORD, parse_lc5_record, args.limit)
    payload = {
        "ok": bool(rows),
        "symbol": symbol_suffix(args.symbol),
        "period": args.period,
        "path": str(path),
        "meta": file_meta(path),
        "count": len(rows),
        "records": rows,
        "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
    }
    emit(payload, 0 if rows else 2)


def _latest_disk_day(symbol: str) -> str:
    rows = read_day_records(symbol, 1)
    return str(rows[-1].get("date") or "") if rows else ""


def cmd_refresh_kline(args: argparse.Namespace) -> None:
    """Refresh through the existing TQ session without launching helper processes."""
    start = time.perf_counter()
    before = _latest_disk_day(args.symbol)
    stdout_log = io.StringIO()
    stderr_log = io.StringIO()
    items: list[dict[str, Any]] = []
    init_path: Path | None = None
    lock_waited_ms = 0.0
    error = ""
    tq = None
    try:
        with TQLock() as lock:
            lock_waited_ms = lock.waited_ms
            with contextlib.redirect_stdout(stdout_log), contextlib.redirect_stderr(stderr_log):
                tq, init_path = load_tq()
                for period in args.periods:
                    try:
                        result = tq.refresh_kline(
                            stock_list=[symbol_suffix(args.symbol)],
                            period=period,
                        )
                        items.append({
                            "period": period,
                            "call_ok": bool(result),
                            "result_type": type(result).__name__,
                            "result_preview": str(result)[:500],
                        })
                    except Exception as exc:
                        items.append({
                            "period": period,
                            "call_ok": False,
                            "error": f"{type(exc).__name__}: {exc}",
                        })
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        if tq is not None:
            try:
                tq.close()
            except Exception:
                pass

    after = _latest_disk_day(args.symbol)
    try:
        disk_updated = bool(after) and (not before or int(after) > int(before))
    except ValueError:
        disk_updated = bool(after) and after != before
    payload = {
        "ok": disk_updated,
        "status": "CLEAN_PASS" if disk_updated else "DATA_STALE",
        "symbol": symbol_suffix(args.symbol),
        "periods": args.periods,
        "disk_path": str(day_path(args.symbol)),
        "disk_latest_before": before,
        "disk_latest_after": after,
        "disk_updated": disk_updated,
        "items": items,
        "init_path": str(init_path) if init_path else "",
        "lock_waited_ms": lock_waited_ms,
        "error": error or ("" if disk_updated else "disk_refresh_not_observed"),
        "captured_stdout_tail": stdout_log.getvalue()[-1000:],
        "captured_stderr_tail": stderr_log.getvalue()[-1000:],
        "helper_process_launch_allowed": False,
        "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
    }
    emit(payload, 0 if disk_updated else 2)


def cmd_blocks(_args: argparse.Namespace) -> None:
    start = time.perf_counter()
    items = []
    if BLOCKNEW.exists():
        for path in sorted(BLOCKNEW.glob("*.blk")):
            symbols = read_block_file(path)
            items.append({"name": path.stem, "path": str(path), "count": len(symbols), "meta": file_meta(path), "sample": symbols[:10]})
    emit({"ok": True, "root": str(BLOCKNEW), "count": len(items), "blocks": items, "elapsed_ms": round((time.perf_counter() - start) * 1000, 3)})


def cmd_block(args: argparse.Namespace) -> None:
    start = time.perf_counter()
    name = args.name if args.name.lower().endswith(".blk") else args.name + ".blk"
    path = BLOCKNEW / name
    symbols = read_block_file(path)
    normalized = []
    for item in symbols:
        try:
            normalized.append(symbol_suffix(item))
        except Exception:
            normalized.append(item)
    emit(
        {
            "ok": bool(symbols),
            "name": path.stem,
            "path": str(path),
            "count": len(normalized),
            "symbols": normalized,
            "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
        },
        0 if symbols else 2,
    )


def tq_formula(formula: str, symbol: str, count: int, kind: str | None = None, dividend_type: int | None = None) -> dict[str, Any]:
    start = time.perf_counter()
    stdout_log = io.StringIO()
    stderr_log = io.StringIO()
    init_path: Path | None = None
    result: Any = {}
    error: str | None = None
    lock_waited_ms = 0.0
    attempts: list[dict[str, Any]] = []
    registry = formula_registry()["formulas"]
    known = next((item for item in registry if item["name"] == formula), {})
    resolved_kind = kind or known.get("kind") or ("xg" if "选股" in formula else "zb")
    resolved_dividend = dividend_type if dividend_type is not None else int(known.get("dividend_type", 0) or 0)
    runtime_formula = str(known.get("call_name") or formula)
    try:
        with TQLock() as lock:
            lock_waited_ms = lock.waited_ms
            with contextlib.redirect_stdout(stdout_log), contextlib.redirect_stderr(stderr_log):
                # The desktop client can report its process before the TQ DLL
                # endpoint is ready (especially immediately after launch).
                # Give initialization a third, low-frequency attempt so a
                # transient startup race is not surfaced as “公式缺失”.
                for attempt_index in range(3):
                    tq, init_path = load_tq()
                    try:
                        if resolved_kind == "xg":
                            result = tq.formula_process_mul_xg(runtime_formula, stock_list=[symbol_suffix(symbol)], count=0, dividend_type=resolved_dividend)
                        elif runtime_formula == "庄家资金监控":
                            setup = tq.formula_set_data_info(
                                symbol_suffix(symbol),
                                count=count,
                                dividend_type=resolved_dividend,
                            )
                            if str(setup.get("ErrorId")) != "0":
                                result = {
                                    "ErrorId": str(setup.get("ErrorId", "1")),
                                    "Error": f"formula_set_data_info failed: {setup}",
                                }
                            else:
                                direct = tq.formula_zb(
                                    runtime_formula,
                                    symbol_suffix(symbol).split(".", 1)[0],
                                    xsflag=2,
                                )
                                if (
                                    isinstance(direct, dict)
                                    and str(direct.get("ErrorId")) == "0"
                                    and isinstance(direct.get("Value"), dict)
                                    and direct.get("Value")
                                ):
                                    result = {
                                        symbol_suffix(symbol): direct["Value"],
                                        "ErrorId": "0",
                                    }
                                else:
                                    result = direct
                        else:
                            result = tq.formula_process_mul_zb(runtime_formula, stock_list=[symbol_suffix(symbol)], count=count, return_date=False, dividend_type=resolved_dividend)
                    finally:
                        if hasattr(tq, "_release"):
                            tq._release()
                        else:
                            tq.close()
                    attempt_ok = bool(result) and isinstance(result, dict) and str(result.get("ErrorId", "0")) == "0"
                    attempts.append({"attempt": attempt_index + 1, "ok": attempt_ok, "empty": not bool(result)})
                    if attempt_ok or attempt_index == 2:
                        break
                    time.sleep(0.8)
    except Exception as exc:
        error = str(exc)
    ok = bool(result) and isinstance(result, dict) and str(result.get("ErrorId", "0")) == "0"
    payload = {
        "ok": ok,
        "formula": formula,
        "tq_formula": runtime_formula,
        "kind": resolved_kind,
        "symbol": symbol_suffix(symbol),
        "count": count,
        "init_path": str(init_path) if init_path else None,
        "registered": bool(known),
        "registry_path": known.get("path"),
        "result": result,
        "attempts": attempts,
        "lock_waited_ms": lock_waited_ms,
        "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
    }
    if error:
        payload["error"] = error
    stdout_text = stdout_log.getvalue().strip()
    stderr_text = stderr_log.getvalue().strip()
    if stdout_text:
        payload["tq_stdout"] = stdout_text
    if stderr_text:
        payload["tq_stderr"] = stderr_text
    return payload


def cmd_formula(args: argparse.Namespace) -> None:
    try:
        payload = tq_formula(args.formula, args.symbol, args.count, args.kind, args.dividend_type)
        emit(payload, 0 if payload["ok"] else 2)
    except Exception as exc:
        emit({"ok": False, "formula": args.formula, "symbol": args.symbol, "error": str(exc)}, 1)


def cmd_five(args: argparse.Namespace) -> None:
    start = time.perf_counter()
    items = []
    for formula in ["大牛线4.0", "飞龙在天", "游资资金监控", "机构资金监控", "庄家资金监控"]:
        meta = CORE_FORMULAS[formula]
        try:
            item = tq_formula(formula, args.symbol, int(meta["count"]), "zb", int(meta["dividend_type"]))
            item["required"] = bool(meta.get("required", True))
            item["reserved"] = bool(meta.get("reserved", False))
            items.append(item)
        except Exception as exc:
            items.append({
                "ok": False,
                "formula": formula,
                "error": str(exc),
                "required": bool(meta.get("required", True)),
                "reserved": bool(meta.get("reserved", False)),
            })
    failed = [item.get("formula") for item in items if not item.get("ok") and item.get("required", True)]
    ok = not failed
    emit(
        {
            "ok": ok,
            "symbol": symbol_suffix(args.symbol),
            "items": items,
            "failed_formulas": failed,
            "reserved_failed_formulas": [],
            "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
        },
        0 if ok else 2,
    )


def cmd_news(args: argparse.Namespace) -> None:
    start = time.perf_counter()
    files: list[Path] = []
    for root in NEWS_DIRS:
        if root.exists():
            files.extend([p for p in root.rglob("*") if p.is_file()])
    files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[: args.limit]
    items = []
    for path in files:
        item = file_meta(path)
        if path.suffix.lower() in {".txt", ".html", ".htm", ".json", ".ini", ".cfg", ".xml"} and path.stat().st_size <= args.max_bytes:
            text, enc = read_text(path, max_chars=args.preview_chars)
            item["encoding"] = enc
            item["preview"] = text
            item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        items.append(item)
    emit({"ok": True, "roots": [str(path) for path in NEWS_DIRS], "count": len(items), "items": items, "elapsed_ms": round((time.perf_counter() - start) * 1000, 3)})


def cmd_probe(args: argparse.Namespace) -> None:
    start = time.perf_counter()
    result: dict[str, Any] = {"ok": True, "symbol": symbol_suffix(args.symbol), "steps": {}}
    try:
        result["steps"]["status"] = {
            "root_exists": TDX_ROOT.exists(),
            "tqcenter_exists": TQCENTER.exists(),
            "formula_count": formula_registry()["count"],
        }
        day = read_day_records(args.symbol, 3)
        result["steps"]["kline_day"] = {"ok": bool(day), "path": str(day_path(args.symbol)), "count": len(day), "tail": day[-1:] if day else []}
        result["steps"]["news"] = {"roots_found": sum(1 for path in NEWS_DIRS if path.exists())}
        try:
            result["steps"]["formula"] = tq_formula(args.formula, args.symbol, args.count, args.kind, args.dividend_type)
        except Exception as exc:
            result["steps"]["formula"] = {"ok": False, "error": str(exc)}
        result["ok"] = bool(result["steps"]["kline_day"]["ok"])
    finally:
        result["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 3)
    emit(result, 0 if result["ok"] else 2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fixed Codex local Tongdaxin/TQ hub for C:\\new_tdx_mock.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("registry").set_defaults(func=cmd_registry)

    kline = sub.add_parser("kline")
    kline.add_argument("symbol")
    kline.add_argument("--period", choices=["day", "lc5"], default="day")
    kline.add_argument("--limit", type=int, default=20)
    kline.set_defaults(func=cmd_kline)

    refresh = sub.add_parser("refresh-kline")
    refresh.add_argument("symbol")
    refresh.add_argument("--periods", nargs="+", default=["1d"])
    refresh.set_defaults(func=cmd_refresh_kline)

    sub.add_parser("blocks").set_defaults(func=cmd_blocks)
    block = sub.add_parser("block")
    block.add_argument("name")
    block.set_defaults(func=cmd_block)

    formula = sub.add_parser("formula")
    formula.add_argument("formula")
    formula.add_argument("symbol")
    formula.add_argument("--count", type=int, default=5)
    formula.add_argument("--kind", choices=["zb", "xg"], default=None)
    formula.add_argument("--dividend-type", type=int, default=None)
    formula.set_defaults(func=cmd_formula)

    five = sub.add_parser("five")
    five.add_argument("symbol")
    five.set_defaults(func=cmd_five)

    news = sub.add_parser("news")
    news.add_argument("--limit", type=int, default=20)
    news.add_argument("--max-bytes", type=int, default=256000)
    news.add_argument("--preview-chars", type=int, default=1200)
    news.set_defaults(func=cmd_news)

    probe = sub.add_parser("probe")
    probe.add_argument("symbol")
    probe.add_argument("--formula", default="大牛线4.0")
    probe.add_argument("--count", type=int, default=3)
    probe.add_argument("--kind", choices=["zb", "xg"], default=None)
    probe.add_argument("--dividend-type", type=int, default=None)
    probe.set_defaults(func=cmd_probe)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    # 2026-06-30 加固: 无参数时默认走 status, 让 entry auto / 无参调链不断
    if not argv and len(sys.argv) == 1:
        argv = ["status"]
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
