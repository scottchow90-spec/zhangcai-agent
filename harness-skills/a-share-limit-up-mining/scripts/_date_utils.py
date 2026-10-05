"""Shared date resolver for 连板挖掘 scripts.

Single source of truth for "what is the latest trading day?".

NO hardcoded dates anywhere. Reads the last 32-byte record from TDX local
.day files (header 32 bytes, records 32 bytes each in v5; v6 40-byte
records are auto-detected from header count vs file size).

We pick the freshest mtime among valid candidates and validate that the
last record's date_int is sensible and monotonic (prev <= last).
"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
from pathlib import Path
import sys
import struct

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_tdx_root

_TDX_ROOT = resolve_tdx_root()
_CANDIDATES = [
    _TDX_ROOT / "vipdoc" / "xinzeng" / "sh" / "lday" / "sh000001.day",
    _TDX_ROOT / "vipdoc" / "sh" / "lday" / "sh000001.day",
    _TDX_ROOT / "vipdoc" / "sz" / "lday" / "sz399001.day",
]


def _tdx_last_record(p: Path):
    """Return (date_int, prev_date_int, rec_size) for the last record of p."""
    if not p.exists():
        return None
    size = p.stat().st_size
    if size < 64:
        return None
    with open(p, "rb") as f:
        f.seek(0, 2)
        fsize = f.tell()
        f.seek(0)
        header = f.read(32)
        n = struct.unpack("<I", header[4:8])[0]
        rec_size = 32
        if n > 0 and (fsize - 32) % n == 0:
            rec_size = (fsize - 32) // n
        if rec_size not in (32, 40):
            rec_size = 32
        records = (fsize - 32) // rec_size
        if records <= 0:
            return None
        f.seek(32 + (records - 1) * rec_size)
        last = f.read(rec_size)
        prev = b""
        if records >= 2:
            f.seek(32 + (records - 2) * rec_size)
            prev = f.read(rec_size)
    date_int = struct.unpack("<I", last[0:4])[0]
    prev_date = struct.unpack("<I", prev[0:4])[0] if prev else 0
    return date_int, prev_date, rec_size


def resolve_latest_trade_date() -> str:
    """Return the latest trading day as 'YYYYMMDD' (string)."""
    found = []
    for p in _CANDIDATES:
        try:
            r = _tdx_last_record(p)
            if not r:
                continue
            date_int, prev_date, rec_size = r
            if not (20000101 <= date_int <= 20991231):
                continue
            if prev_date and prev_date > date_int:
                continue
            found.append((p.stat().st_mtime, p, date_int))
        except Exception:
            continue
    if not found:
        raise RuntimeError(
            "无法从 TDX 本地 K 线文件读取最近交易日（已尝试 xinzeng/sh/lday/sh000001.day, "
            "sh/lday/sh000001.day, sz/lday/sz399001.day）。请先确认通达信本地数据已下载并落盘。"
        )
    found.sort(key=lambda x: x[0], reverse=True)
    return str(found[0][2])


if __name__ == "__main__":
    print(resolve_latest_trade_date())
