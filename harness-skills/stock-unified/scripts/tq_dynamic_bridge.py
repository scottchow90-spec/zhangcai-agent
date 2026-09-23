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
from datetime import datetime
from pathlib import Path

_tdx_root_text = (
    os.environ.get("ZHANGCAI_TDX_ROOT")
    or os.environ.get("TDX_ROOT")
    or ""
).strip()
TDX_ROOT = Path(_tdx_root_text or os.environ.get("ZHANGCAI_DEV_TDX_ROOT", r"C:\new_tdx_mock")).expanduser().resolve()
USER_DIR = TDX_ROOT / 'PYPlugins' / 'user'
TQCENTER = USER_DIR / 'tqcenter.py'
DEFAULT_INIT = USER_DIR / 'openclaw_tq_test.py'
FALLBACK_INIT = USER_DIR / 'tdxdata_test.py'
NODE_TOOL = TDX_ROOT / 'NodeTool.exe'
PY_STRATEGY_CFG = USER_DIR.parent / 'py_strategy.cfg'
BRIDGE_SCRIPT = USER_DIR / 'openclaw_bridge_simple.py'
BRIDGE_STATUS = USER_DIR / '_openclaw_runtime' / 'bridge_status.json'

CORE_ZB_FORMULAS = [
    ('大牛线4.0', 20, 1),
    ('飞龙在天', 0, 0),
    ('游资资金监控', 5, 0),
    ('机构资金监控', 5, 0),
]
RESERVED_ZB_FORMULAS = [
    ('庄家资金监控', 5, 0),
]
OPTIONAL_XG_FORMULAS = [
    '飞龙在天选股',
]
FORMULA_CALL_NAMES = {
    '大牛线4.0': '大牛线撑压版',
}

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def json_out(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _iso_mtime(path: Path | None):
    if not path or not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec='seconds')


def _file_meta(path: Path):
    if not path.exists():
        return {'path': str(path), 'exists': False}
    stat = path.stat()
    return {
        'path': str(path),
        'exists': True,
        'size': stat.st_size,
        'updated_at': datetime.fromtimestamp(stat.st_mtime).isoformat(timespec='seconds'),
    }


def _parse_simple_cfg(path: Path):
    payload = _file_meta(path)
    if not path.exists():
        return payload
    text = path.read_text(encoding='utf-8', errors='replace')
    payload['raw'] = text
    parsed = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('[') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        parsed[key.strip()] = value.strip()
    payload['parsed'] = parsed
    return payload


def _load_bridge_status(path: Path):
    payload = _file_meta(path)
    if not path.exists():
        return payload
    try:
        payload['json'] = json.loads(path.read_text(encoding='utf-8', errors='replace'))
    except Exception as exc:
        payload['json_error'] = str(exc)
    return payload


def _get_tdx_process_info():
    command = [
        'powershell',
        '-NoProfile',
        '-Command',
        "Get-Process TdxW -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,StartTime | ConvertTo-Json -Compress",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', check=False)
        text = (result.stdout or '').strip()
        if result.returncode != 0 or not text:
            return {'running': False}
        data = json.loads(text)
        if isinstance(data, list):
            data = data[0] if data else {}
        return {
            'running': bool(data),
            'id': data.get('Id'),
            'name': data.get('ProcessName'),
            'start_time': data.get('StartTime'),
        }
    except Exception as exc:
        return {'running': False, 'error': str(exc)}


def _needs_restart(process_info, cfg_meta, bridge_meta):
    start_time = process_info.get('start_time')
    if not start_time:
        return None
    try:
        start_text = str(start_time)
        if start_text.startswith('/Date(') and start_text.endswith(')/'):
            millis = int(start_text[6:-2])
            started = datetime.fromtimestamp(millis / 1000.0)
        else:
            started = datetime.fromisoformat(start_text)
    except Exception:
        return None
    latest_required = None
    for candidate in [cfg_meta.get('updated_at'), bridge_meta.get('updated_at')]:
        if not candidate:
            continue
        try:
            parsed = datetime.fromisoformat(str(candidate))
        except Exception:
            continue
        latest_required = parsed if latest_required is None else max(latest_required, parsed)
    if latest_required is None:
        return None
    return started < latest_required


def create_runtime_init():
    source = DEFAULT_INIT if DEFAULT_INIT.exists() else FALLBACK_INIT if FALLBACK_INIT.exists() else None
    if source is None:
        raise FileNotFoundError(f'missing init script: {DEFAULT_INIT} and {FALLBACK_INIT}')
    return source, source


def cleanup_runtime_init(runtime_path: Path | None) -> None:
    return


def _as_float_list(values):
    result = []
    for item in values or []:
        result.append(float(item))
    return result


def _extract_field_series(payload, field_name: str, symbol: str):
    field_value = (payload or {}).get(field_name)
    if field_value is None:
        return []

    if isinstance(field_value, dict):
        if symbol in field_value:
            return _extract_field_series({field_name: field_value[symbol]}, field_name, symbol)
        if len(field_value) == 1:
            return _extract_field_series({field_name: next(iter(field_value.values()))}, field_name, symbol)

    columns = getattr(field_value, 'columns', None)
    if columns is not None:
        try:
            if symbol in columns:
                return _as_float_list(field_value[symbol].tolist())
            if len(columns) == 1:
                return _as_float_list(field_value[columns[0]].tolist())
        except Exception:
            pass

    tolist = getattr(field_value, 'tolist', None)
    if callable(tolist):
        values = tolist()
        if isinstance(values, list):
            try:
                return _as_float_list(values)
            except Exception:
                return values

    if isinstance(field_value, (list, tuple)):
        try:
            return _as_float_list(field_value)
        except Exception:
            return list(field_value)

    return []


def _tdx_sma(values, period: int, weight: int = 1):
    result = []
    for index, value in enumerate(values):
        if index == 0:
            result.append(float(value))
        else:
            result.append((float(value) * weight + result[-1] * (period - weight)) / period)
    return result


def compute_zhuang_control(tq, symbol: str, days: int = 60):
    market_data = tq.get_market_data(stock_list=[symbol], period='1d', count=max(days, 60))
    highs = _extract_field_series(market_data, 'High', symbol)
    lows = _extract_field_series(market_data, 'Low', symbol)
    closes = _extract_field_series(market_data, 'Close', symbol)

    size = min(len(highs), len(lows), len(closes))
    if size <= 0:
        return None
    highs = highs[-size:]
    lows = lows[-size:]
    closes = closes[-size:]

    n_param = 35
    m_param = 0
    n1_param = 3

    b1 = []
    b3 = []
    for index in range(size):
        start = max(0, index - n_param + 1)
        hhv = max(highs[start : index + 1])
        llv = min(lows[start : index + 1])
        denom = hhv - llv
        if denom > 0:
            b1.append((hhv - closes[index]) / denom * 100 - m_param)
            b3.append((closes[index] - llv) / denom * 100)
        else:
            b1.append(0.0)
            b3.append(50.0)

    b2 = [value + 100.0 for value in _tdx_sma(b1, n_param, 1)]
    b4 = _tdx_sma(b3, 7, 1)
    b5 = [value + 100.0 for value in _tdx_sma(b4, 5, 1)]
    b6 = [b5[index] - b2[index] for index in range(len(b5))]
    last_value = b6[-1]
    return round(max(last_value - n1_param, 0.0) * 3.5, 2) if last_value > n1_param else 0.0


def patch_zhuang_result(tq, formula_name: str, symbol: str, result, count: int):
    if formula_name != '庄家资金监控':
        return result
    if not isinstance(result, dict):
        return result
    row = result.get(symbol)
    if not isinstance(row, dict):
        computed = compute_zhuang_control(tq, symbol, days=max(count, 60))
        if computed is None:
            return result
        return {
            symbol: {
                '控盘程度': [f'{computed:.2f}'],
                '控盘度': ['100.00'],
                'OUTPUT3': [f'{computed:.2f}'],
                'OUTPUT4': [f'{computed:.2f}' if computed > 100 else '0.00'],
            },
            'ErrorId': '0',
        }

    current = row.get('控盘程度', [None])
    current_value = current[0] if isinstance(current, list) and current else current
    if current_value not in (None, '', 'None'):
        return result

    computed = compute_zhuang_control(tq, symbol, days=max(count, 60))
    if computed is None:
        return result

    row['控盘程度'] = [f'{computed:.2f}']
    result[symbol] = row
    return result


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


def detect_formula_result_ok(res):
    return bool(res) and isinstance(res, dict) and str(res.get('ErrorId', '0')) == '0'


def runtime_formula_name(formula_name: str) -> str:
    return FORMULA_CALL_NAMES.get(formula_name, formula_name)


def command_status(args):
    cfg_meta = _parse_simple_cfg(PY_STRATEGY_CFG)
    bridge_meta = _file_meta(BRIDGE_SCRIPT)
    bridge_status_meta = _load_bridge_status(BRIDGE_STATUS)
    process_info = _get_tdx_process_info()
    payload = {
        'user_dir': str(USER_DIR),
        'tqcenter_exists': TQCENTER.exists(),
        'default_init_exists': DEFAULT_INIT.exists(),
        'fallback_init_exists': FALLBACK_INIT.exists(),
        'py_strategy_cfg': cfg_meta,
        'bridge_script': bridge_meta,
        'bridge_status': bridge_status_meta,
        'tdx_process': process_info,
    }
    payload['restart_required'] = _needs_restart(process_info, cfg_meta, bridge_meta)
    reasons = []
    parsed_cfg = cfg_meta.get('parsed') or {}
    if parsed_cfg.get('Num') != '1':
        reasons.append('py_strategy.cfg does not enable a Python bridge strategy')
    if parsed_cfg.get('FileName01') != r'user\openclaw_bridge_simple.py':
        reasons.append('py_strategy.cfg does not point to user\\openclaw_bridge_simple.py')
    if not bridge_meta.get('exists'):
        reasons.append('bridge script missing from live PYPlugins\\user')
    if process_info.get('running') and payload['restart_required']:
        reasons.append('TdxW.exe started before the current bridge config/script was deployed')
    if process_info.get('running') and not bridge_status_meta.get('exists'):
        reasons.append('no bridge_status.json was produced by the in-process bridge yet')

    if not TQCENTER.exists():
        payload['ok'] = False
        payload['reasons'] = reasons
        json_out(payload)
        return 2
    try:
        tq = load_tq()
        payload['tq_class'] = str(tq)
        runtime_init, init_source = create_runtime_init()
        payload['init_source'] = str(init_source)
        payload['init_path'] = str(runtime_init)
        try:
            tq.initialize(str(runtime_init))
            payload['init_ok'] = True
            payload['ok'] = True
        except Exception as exc:
            payload['init_ok'] = False
            payload['ok'] = False
            payload['error'] = str(exc)
            reasons.append(str(exc))
    except Exception as exc:
        payload['ok'] = False
        payload['error'] = str(exc)
        reasons.append(str(exc))
        json_out(payload)
        return 1
    payload['reasons'] = reasons
    json_out(payload)
    return 0


def command_formula_zb(args):
    payload = {
        'formula_name': args.formula_name,
        'symbol': args.symbol,
        'count': args.count,
        'default_init_exists': DEFAULT_INIT.exists(),
    }
    runtime_init = None
    try:
        tq = load_tq()
        runtime_init, init_source = create_runtime_init()
        payload['init_source'] = str(init_source)
        payload['init_path'] = str(runtime_init)
        call_name = runtime_formula_name(args.formula_name)
        payload['tq_formula'] = call_name
        try:
            tq.initialize(str(runtime_init))
        except Exception:
            ensure_runtime_helper()
            tq.initialize(str(runtime_init))
        res = tq.formula_process_mul_zb(
            call_name,
            stock_list=[args.symbol],
            count=args.count,
            return_date=args.return_date,
            dividend_type=args.dividend_type,
        )
        res = patch_zhuang_result(tq, args.formula_name, args.symbol, res, args.count)
        payload['ok'] = detect_formula_result_ok(res)
        payload['result'] = res
        if not payload['ok']:
            payload['error'] = 'empty result'
    except Exception as exc:
        payload['ok'] = False
        payload['error'] = str(exc)
        json_out(payload)
        return 1
    finally:
        cleanup_runtime_init(runtime_init)
    json_out(payload)
    return 0


def command_formula_xg(args):
    payload = {
        'formula_name': args.formula_name,
        'symbol': args.symbol,
        'default_init_exists': DEFAULT_INIT.exists(),
    }
    runtime_init = None
    try:
        tq = load_tq()
        runtime_init, init_source = create_runtime_init()
        payload['init_source'] = str(init_source)
        payload['init_path'] = str(runtime_init)
        try:
            tq.initialize(str(runtime_init))
        except Exception:
            ensure_runtime_helper()
            tq.initialize(str(runtime_init))
        res = tq.formula_process_mul_xg(
            args.formula_name,
            stock_list=[args.symbol],
            count=0,
            dividend_type=args.dividend_type,
        )
        payload['ok'] = detect_formula_result_ok(res)
        payload['result'] = res
        if not payload['ok']:
            payload['error'] = 'empty result'
    except Exception as exc:
        payload['ok'] = False
        payload['error'] = str(exc)
        json_out(payload)
        return 1
    finally:
        cleanup_runtime_init(runtime_init)
    json_out(payload)
    return 0


def command_five(args):
    formulas = [(name, 'zb', count, dividend_type, True, False) for name, count, dividend_type in CORE_ZB_FORMULAS]
    formulas.extend((name, 'zb', count, dividend_type, False, True) for name, count, dividend_type in RESERVED_ZB_FORMULAS)
    if args.include_xg:
        formulas.extend((name, 'xg', 0, 0, False, False) for name in OPTIONAL_XG_FORMULAS)
    result = {'symbol': args.symbol, 'default_init_exists': DEFAULT_INIT.exists(), 'items': []}
    runtime_init = None
    try:
        tq = load_tq()
        runtime_init, init_source = create_runtime_init()
        result['init_source'] = str(init_source)
        result['init_path'] = str(runtime_init)
        try:
            tq.initialize(str(runtime_init))
        except Exception:
            ensure_runtime_helper()
            tq.initialize(str(runtime_init))
        for name, kind, count, dividend_type, required, reserved in formulas:
            try:
                if kind == 'zb':
                    call_name = runtime_formula_name(name)
                    res = tq.formula_process_mul_zb(call_name, stock_list=[args.symbol], count=count, return_date=False, dividend_type=dividend_type)
                    res = patch_zhuang_result(tq, name, args.symbol, res, count)
                else:
                    call_name = name
                    res = tq.formula_process_mul_xg(name, stock_list=[args.symbol], count=0, dividend_type=dividend_type)
                ok = detect_formula_result_ok(res)
                item = {'formula': name, 'tq_formula': call_name, 'kind': kind, 'ok': ok, 'required': required, 'reserved': reserved, 'result': res}
                if not ok:
                    item['error'] = 'empty result'
                result['items'].append(item)
            except Exception as exc:
                result['items'].append({'formula': name, 'kind': kind, 'ok': False, 'required': required, 'reserved': reserved, 'error': str(exc)})
    except Exception as exc:
        result['ok'] = False
        result['error'] = str(exc)
        json_out(result)
        return 1
    finally:
        cleanup_runtime_init(runtime_init)
    result['failed_formulas'] = [item.get('formula') for item in result['items'] if item.get('required') and not item.get('ok')]
    result['reserved_failed_formulas'] = [item.get('formula') for item in result['items'] if item.get('reserved') and not item.get('ok')]
    result['ok'] = not result['failed_formulas']
    json_out(result)
    return 0 if result['ok'] else 2


def build_parser():
    parser = argparse.ArgumentParser(description='Minimal TQ bridge for stock workflow validation.')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('status').set_defaults(func=command_status)

    fz = sub.add_parser('formula-zb')
    fz.add_argument('formula_name')
    fz.add_argument('symbol')
    fz.add_argument('--count', type=int, default=5)
    fz.add_argument('--return-date', action='store_true')
    fz.add_argument('--dividend-type', type=int, default=0)
    fz.set_defaults(func=command_formula_zb)

    fx = sub.add_parser('formula-xg')
    fx.add_argument('formula_name')
    fx.add_argument('symbol')
    fx.add_argument('--dividend-type', type=int, default=0)
    fx.set_defaults(func=command_formula_xg)

    fv = sub.add_parser('five')
    fv.add_argument('symbol')
    fv.add_argument('--include-xg', action='store_true')
    fv.set_defaults(func=command_five)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == '__main__':
    raise SystemExit(main())
