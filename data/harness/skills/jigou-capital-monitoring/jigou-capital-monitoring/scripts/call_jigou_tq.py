# -*- coding: utf-8 -*-
"""机构资金监控 TQ 正确调用脚本

⚠️ 关键：本公式必须用 formula_zb 直接调用，禁止用 formula_process_mul_zb。
⚠️ count 必须 >= 40 才能让 EMA(20) 充分收敛，得到稳定值。
"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import sys, json, argparse, os

# ---- 正确的 TQ 调用 ----
def _auto_suffix(code):
    """自动补全市场后缀：600→SH, 000/001/002/300/301→SZ, 688→SH"""
    if '.' in code:
        return code
    if code.startswith('6'):
        return code + '.SH'
    return code + '.SZ'

def call_jigou_formula(code, tdx_root=r'C:\new_tdx_mock', count=60, dividend_type=0):
    """
    正确调用机构资金监控公式。
    返回：最新一条记录的 dict，字段与通达信公式界面一致。
    """
    code = _auto_suffix(code)
    root = os.path.abspath(tdx_root)
    user_dir = os.path.join(root, 'PYPlugins', 'user')
    if user_dir not in sys.path:
        sys.path.insert(0, user_dir)
    sys.argv = ['tqcenter', '--run_tdx', '0']

    from tqcenter import tq

    init_path = os.path.join(user_dir, 'tdxdata_test.py')
    tq.initialize(init_path)

    try:
        # Step 1: 设定K线加载参数 — count>=40 是关键
        setup = tq.formula_set_data_info(code, count=count, dividend_type=dividend_type)
        if setup.get('ErrorId') != '0':
            return {'error': f'set_data_info failed: {setup}', 'step': 'set_data_info'}

        # Step 2: 直接调用 formula_zb — 这是唯一正确口径
        stock_code_short = code.split('.')[0] if '.' in code else code
        result = tq.formula_zb('机构资金监控', stock_code_short, xsflag=2)

        if result.get('ErrorId') != '0':
            return {'error': f'formula_zb failed: {result}', 'step': 'formula_zb'}

        # Step 3: 取最新一条
        values = result.get('Value', {})
        latest = {}
        for k, v in values.items():
            if isinstance(v, list) and v:
                latest[k] = v[-1]
            else:
                latest[k] = v
        latest['_count'] = count
        latest['_div'] = dividend_type
        latest['_code'] = code
        latest['_raw_count'] = len(values.get('大单动向', [])) if isinstance(values.get('大单动向'), list) else 0
        return latest

    finally:
        try:
            tq.close()
        except Exception:
            pass


# ---- 校验：必须与通达信界面一致 ----
EXPECTED_BASELINE = {
    '大单动向': '0.36',
    '机构大单进': '-0.34',
    '机构大单出': '1.00',
    '大户大单进': '-0.03',
    '散户资金进': '0.23',
    '小单资金出': '1.00',
    '中轴线': '0.00',
}


def verify_against_baseline(latest, tolerance=0.01):
    """校验结果是否与已知正确基准值一致。"""
    errors = []
    for key, expected_str in EXPECTED_BASELINE.items():
        actual = latest.get(key)
        if actual is None:
            errors.append(f'{key}: MISSING (expected {expected_str})')
            continue
        try:
            expected = float(expected_str)
            if abs(expected) < 0.001:
                if float(actual) != 0.0:
                    errors.append(f'{key}: {actual} (expected ~{expected_str})')
            elif abs(float(actual) - expected) > tolerance:
                errors.append(f'{key}: {actual} (expected ~{expected_str}, diff {abs(float(actual)-expected):.4f})')
        except (ValueError, TypeError):
            if str(actual) != expected_str:
                errors.append(f'{key}: {actual} (expected {expected_str})')
    return errors


def main():
    parser = argparse.ArgumentParser(description='机构资金监控 TQ 正确调用器')
    parser.add_argument('--code', default='301372.SZ', help='股票代码')
    parser.add_argument('--tdx', default=r'C:\new_tdx_mock', help='通达信安装目录')
    parser.add_argument('--count', type=int, default=60, help='K线加载数量(>=40)')
    parser.add_argument('--div', type=int, default=0, help='复权类型 0=不复权 1=前复权 2=后复权')
    parser.add_argument('--verify', action='store_true', default=False, help='可选：校验与固定基准值的一致性；默认关闭，避免盘后数据变化导致实跑误判')
    parser.add_argument('--json', action='store_true', help='JSON格式输出')

    args = parser.parse_args()
    result = call_jigou_formula(code=args.code, tdx_root=args.tdx, count=args.count, dividend_type=args.div)

    if not args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        print(json.dumps(result, ensure_ascii=False, default=str))

    if args.verify and 'error' not in result:
        errors = verify_against_baseline(result)
        if errors:
            print(f'\n[WARN] 基准值校验失败 ({len(errors)}项):')
            for e in errors:
                print(f'  - {e}')
            sys.exit(1)
        else:
            print(f'\n[PASS] 基准值校验通过 — 与通达信公式界面显示一致')
    elif 'error' in result:
        print(f'\n[FAIL] 调用失败: {result["error"]}')
        sys.exit(2)


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == '__main__':
    main()
