# -*- coding: utf-8 -*-
"""Call local TQ formula_process_mul_zb for 游资资金监控.

Usage:
  python scripts/call_youzi_tq.py --code 301372.SZ --count 30 --tdx "C:\\new_tdx_mock"
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
import sys
_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_tdx_root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--code', required=True, help='Stock code, e.g. 301372.SZ')
    parser.add_argument('--count', type=int, default=30)
    parser.add_argument('--tdx', default=str(resolve_tdx_root()))
    parser.add_argument('--formula', default='游资资金监控')
    parser.add_argument('--dividend-type', type=int, default=1)
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    user_dir = os.path.join(args.tdx, 'PYPlugins', 'user')
    sys.path.insert(0, user_dir)
    sys.argv = ['tqcenter', '--run_tdx', '0']

    # Auto-suffix: 600→SH, others→SZ
    code = args.code
    if '.' not in code:
        code = code + ('.SH' if code.startswith('6') else '.SZ')

    from tqcenter import tq

    tq.initialize(args.tdx)
    try:
        setup = tq.formula_set_data_info(code, count=args.count, dividend_type=args.dividend_type)
        result = tq.formula_process_mul_zb(
            args.formula,
            stock_list=[args.code],
            return_count=args.count,
            return_date=True,
            dividend_type=args.dividend_type,
        )
        print(json.dumps({'setup': setup, 'result': result}, ensure_ascii=False, indent=2, default=str))
    finally:
        try:
            tq.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()
