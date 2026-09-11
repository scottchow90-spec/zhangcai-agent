#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

USER_DIR = Path(r'C:\new_tdx_mock\PYPlugins\user')
FALLBACK_INIT = USER_DIR / 'tdxdata_test.py'
TDX_ROOT = USER_DIR.parents[1]
NODE_TOOL = TDX_ROOT / 'NodeTool.exe'

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def json_out(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def load_tq():
    os.chdir(str(TDX_ROOT))
    sys.path.insert(0, str(USER_DIR))
    from tqcenter import tq  # type: ignore
    return tq


def ensure_runtime_helper():
    if not NODE_TOOL.exists():
        return
    try:
        subprocess.Popen([str(NODE_TOOL)], cwd=str(TDX_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return


def command_snapshot(args):
    payload = {'symbol': args.symbol, 'init_exists': FALLBACK_INIT.exists()}
    try:
        tq = load_tq()
        if not FALLBACK_INIT.exists():
            raise FileNotFoundError(str(FALLBACK_INIT))
        try:
            tq.initialize(str(FALLBACK_INIT))
        except Exception:
            ensure_runtime_helper()
            tq.initialize(str(FALLBACK_INIT))
        res = tq.get_market_snapshot(stock_code=args.symbol, field_list=[])
        payload['ok'] = bool(res)
        payload['result'] = res
        if not res:
            payload['error'] = 'empty result'
        tq.close()
    except Exception as exc:
        payload['ok'] = False
        payload['error'] = str(exc)
        json_out(payload)
        return 1
    json_out(payload)
    return 0 if payload['ok'] else 2


def command_refresh_kline(args):
    payload = {'symbol': args.symbol, 'periods': args.periods, 'init_exists': FALLBACK_INIT.exists(), 'items': []}
    try:
        tq = load_tq()
        if not FALLBACK_INIT.exists():
            raise FileNotFoundError(str(FALLBACK_INIT))
        try:
            tq.initialize(str(FALLBACK_INIT))
        except Exception:
            ensure_runtime_helper()
            tq.initialize(str(FALLBACK_INIT))
        for period in args.periods:
            try:
                res = tq.refresh_kline(stock_list=[args.symbol], period=period)
                payload['items'].append({'period': period, 'ok': bool(res), 'result': res if isinstance(res, (dict, list, str, int, float, bool)) else str(res)})
            except Exception as exc:
                payload['items'].append({'period': period, 'ok': False, 'error': str(exc)})
        tq.close()
        payload['ok'] = any(item.get('ok') for item in payload['items'])
    except Exception as exc:
        payload['ok'] = False
        payload['error'] = str(exc)
        json_out(payload)
        return 1
    json_out(payload)
    return 0 if payload['ok'] else 2


def build_parser():
    parser = argparse.ArgumentParser(description='Minimal realtime refresh bridge for stock workflow validation.')
    sub = parser.add_subparsers(dest='command', required=True)

    snapshot = sub.add_parser('snapshot')
    snapshot.add_argument('symbol')
    snapshot.set_defaults(func=command_snapshot)

    rk = sub.add_parser('refresh-kline')
    rk.add_argument('symbol')
    rk.add_argument('--periods', nargs='+', default=['1m','5m','1d'])
    rk.set_defaults(func=command_refresh_kline)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == '__main__':
    raise SystemExit(main())
