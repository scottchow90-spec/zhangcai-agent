# -*- coding: utf-8 -*-
"""Parse local TDX .day file and recompute AAA/DDD/买方意向 for 游资资金监控.

Usage:
  python scripts/parse_day_recalc_youzi.py --day "C:\\new_tdx_mock\\vipdoc\\sz\\lday\\sz301372.day" --count 30
"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import argparse
import json
import os
import struct
import sys


def ema(values, n):
    alpha = 2 / (n + 1)
    out = []
    prev = None
    for value in values:
        prev = value if prev is None else alpha * value + (1 - alpha) * prev
        out.append(prev)
    return out


def read_day(path):
    rows = []
    with open(path, 'rb') as f:
        while True:
            b = f.read(32)
            if len(b) < 32:
                break
            date, op, hi, lo, cl, amount, vol, res = struct.unpack('<IIIIIfII', b)
            rows.append({
                'date': str(date),
                'open': op / 100,
                'high': hi / 100,
                'low': lo / 100,
                'close': cl / 100,
                'amount': float(amount),
                'volume': vol,
            })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--day', required=True)
    parser.add_argument('--count', type=int, default=30)
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    rows = read_day(args.day)
    closes = [r['close'] for r in rows]
    aaa = [a - b for a, b in zip(ema(closes, 5), ema(closes, 30))]
    ddd = ema(aaa, 5)
    buy = [(a - d) * 2 for a, d in zip(aaa, ddd)]
    output4 = [1.0 if x > 0 else 0.0 for x in buy]

    result = []
    for row, a, d, b, o4 in zip(rows, aaa, ddd, buy, output4):
        item = dict(row)
        item.update({'AAA': round(a, 4), 'DDD': round(d, 4), '买方意向': round(b, 4), 'OUTPUT4': o4})
        result.append(item)

    print(json.dumps({
        'path': args.day,
        'exists': os.path.exists(args.day),
        'bytes': os.path.getsize(args.day) if os.path.exists(args.day) else None,
        'records': len(rows),
        'tail': result[-args.count:],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == '__main__':
    main()
