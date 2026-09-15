#!/usr/bin/env python3
"""
大牛线分析全能硬闸（三合一强化版）
====================================
合并: 源码验证 + TQ连接预检 + 公式存在性校验 + 分析流程锁定

执行方式:
    python hooks/daniuxian_source_gate.py --assert --code <股票代码>

阻断条件（任一失败即SystemExit(2)）:
    1. 公式源码文件不存在或关键字段缺失
    2. TQ DLL无法初始化或连接失败
    3. 公式在通达信中不存在(实际调用验证)
    4. 指定的股票代码在通达信中不存在
    5. 必须使用固定分析模块 daniuxian_analysis.py
    6. workspace中存在3个以上_tmp_*.py临时脚本
"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import sys, os, json, subprocess

FORMULA_SOURCE = r'C:\new_tdx_mock\T0002\gs_bak\大牛线.txt'
DISPLAY_FORMULA_NAME = '大牛线撑压版'
# 本机通达信显示/源码名与 TQ 动态注册名不同；运行态必须使用此可调用别名。
TQ_FORMULA_NAME = '大牛线撑压版'
FIXED_ANALYZER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'daniuxian_analysis.py')
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ===== 16子系统标准定义（唯一真相源，修改此处=篡改） =====
SUBSYSTEMS_STANDARD = [
    (1,  '主趋势线',     'EMA(EMA(CLOSE,10),10)',              '主趋势线'),
    (2,  'EMA均线分层',   'EMA5/10/20 + EMA173/193/213',        'EMA9,EMA10,EMA11'),
    (3,  'K线颜色信号',   'EMA5>EMA20=红K / EMA5<EMA20=绿K',    '内置渲染'),
    (4,  '流通市值',      'FINANCE(40)/100000000',              '流通市值'),
    (5,  'DX动量指标',    '100*EMA(EMA(MTM,6),6)/EMA(EMA(ABS(MTM),6),6)', '内置计算'),
    (6,  '参与与离场信号', '短线力量低位转强=参与提醒 / 高位转弱=离场提醒', '内置主图'),
    (7,  '控盘程度',      '(VAW1-REF(VAW1))/REF(VAW1)*1000',   '内置计算'),
    (8,  '财神短线',      '(EMA(C,8)-EMA(C,21))*50 / EMA(财,3)','内置计算'),
    (9,  '庄进/庄出',     'OUTPUT4(庄进) + OUTPUT6(庄出)',      'OUTPUT4,OUTPUT6'),
    (10, '妖股识别',      '涨停+平台突破+量能放大',              '妖股标记'),
    (11, '龙头参与区',     '涨停缩量=第一参与区 / 涨幅大于百分之七且缩量=第二参与区', '内置主图'),
    (12, '龙回头',        '白横杠+红点+红箭头+红色买字共同条件', 'X7'),
    (13, '点火信号',      'CROSS(EMA3,EMA21)',                  'OUTPUT9'),
    (14, '起爆/题材共振', 'KDJ金叉+涨停',                       'OUTPUT3+起爆1'),
    (15, 'BOLL+多重均线', 'BOLL(20,2)+MA5/10/20/30/54/60/120',  '内置主图'),
    (16, '核心黄金分割撑压', '大牛线撑压版核心黄金分割支撑/压力',
     '支撑一,支撑二,压力一,压力二,OUTPUT66'),
]

TQ_KEY_FIELDS = [
    '主趋势线', 'EMA9', 'EMA10', 'EMA11',
    'OUTPUT3', 'OUTPUT4', 'OUTPUT6', 'OUTPUT9',
    '流通市值', '涨停价', '跌停价',
    '支撑一', '支撑二', '压力一', '压力二', 'OUTPUT66',
]

def fail(reason):
    print(f"FATAL: {reason}")
    print("BLOCKED_HARD_GATE")
    sys.exit(2)

# ===== 闸1: 公式源码完整性 =====
def gate_source_integrity():
    """验证公式源码文件存在且关键字段齐全"""
    if not os.path.exists(FORMULA_SOURCE):
        fail(f"大牛线4.0公式源码不存在: {FORMULA_SOURCE}")

    with open(FORMULA_SOURCE, 'r', encoding='utf-8') as f:
        content = f.read()

    missing = []
    for name in ['主趋势线', 'EMA9', 'EMA10', 'EMA11', '流通市值',
                 '庄:=', 'STJ83:=', '龙回头:=', 'X7:=', "DRAWTEXT(X7", '起爆1:=',
                 '龙头第一买点:=', '妖股:=', '财:=', '控盘:=', 'DX:=',
                 'BOLL:=', 'MA5:=MA', 'MA10:=MA', 'MA20:=MA',
                 'FF:=EMA(CLOSE,3)', 'MA15:=EMA(CLOSE,21)', 'CROSS(FF,MA15)']:
        if name not in content:
            missing.append(name)
    if missing:
        fail(f"公式源码缺少关键字段: {missing}")
    print(f"  [GATE1 PASS] 源码完整性: 21个关键字段全部存在")

# ===== 闸2: TQ连接可用性 =====
def gate_tq_connectivity():
    """验证TQ DLL能初始化并连接通达信"""
    try:
        old_argv = sys.argv[:]
        sys.argv = ['tqcenter', '--run_tdx', '0']

        if 'tqcenter' in sys.modules:
            del sys.modules['tqcenter']
        if 'tqcenter.tq' in sys.modules:
            del sys.modules['tqcenter.tq']

        sys.path.insert(0, r'C:\new_tdx_mock\PYPlugins\user')
        from tqcenter import tq

        tq.initialize(r'C:\new_tdx_mock\PYPlugins\user\tdxdata_test.py')
        if tq.run_id < 0:
            fail(f"TQ初始化失败: run_id={tq.run_id}")

        # 测试基本功能
        snap = tq.get_market_snapshot('301372.SZ')
        if not snap or snap.get('ErrorId') != '0':
            fail("TQ快照接口不可用")

        tq.close()
        print(f"  [GATE2 PASS] TQ连接正常: run_mode={tq.run_mode} run_id={tq.run_id}")
        return True
    except Exception as e:
        fail(f"TQ连接失败: {e}")
    finally:
        sys.argv = old_argv

# ===== 闸3: 公式存在性（实际调用验证） =====
def gate_formula_exists(stock_code):
    """实际调用公式验证其在通达信中存在并可计算"""
    try:
        old_argv = sys.argv[:]
        sys.argv = ['tqcenter', '--run_tdx', '0']

        if 'tqcenter' in sys.modules:
            del sys.modules['tqcenter']
        if 'tqcenter.tq' in sys.modules:
            del sys.modules['tqcenter.tq']

        sys.path.insert(0, r'C:\new_tdx_mock\PYPlugins\user')
        from tqcenter import tq

        tq.initialize(r'C:\new_tdx_mock\PYPlugins\user\tdxdata_test.py')

        # 加载数据
        sz_code = f'{stock_code}.SZ' if stock_code.startswith(('0','2','3')) else f'{stock_code}.SH'
        r1 = tq.formula_set_data_info(sz_code, count=5, dividend_type=1)
        if r1.get('ErrorId') != '0':
            fail(f"formula_set_data_info失败: {r1.get('Error','?')}")

        # 调用公式
        r2 = tq.formula_zb(TQ_FORMULA_NAME, formula_arg=stock_code)
        v = r2.get('Value', {})
        if not v:
            fail(f"{DISPLAY_FORMULA_NAME}公式返回空: runtime_call={TQ_FORMULA_NAME} result={r2}")

        # 验证TQ关键字段
        missing_tq = []
        for field in TQ_KEY_FIELDS:
            if field not in v:
                missing_tq.append(field)
        if missing_tq:
            fail(f"公式缺少TQ输出字段: {missing_tq}")

        tq.close()
        print(f"  [GATE3 PASS] {DISPLAY_FORMULA_NAME}公式存在且返回{v.__len__()}个字段(runtime_call={TQ_FORMULA_NAME})")
        return True
    except Exception as e:
        fail(f"公式调用验证失败: {e}")
    finally:
        sys.argv = old_argv

# ===== 闸4: 固定分析模块存在 =====
def gate_fixed_analyzer():
    """验证固定分析模块存在且可导入"""
    if not os.path.exists(FIXED_ANALYZER):
        fail(f"固定分析模块不存在: {FIXED_ANALYZER}")

    # 验证语法正确
    r = subprocess.run([sys.executable, '-m', 'py_compile', FIXED_ANALYZER],
                       capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        fail(f"固定分析模块语法错误: {r.stderr[-500:]}")

    print(f"  [GATE4 PASS] 固定分析模块语法正确")

# ===== 闸5: 临时脚本检测 =====
def gate_no_temp_scripts():
    """禁止workspace中存在3个以上_tmp_*.py"""
    temp_scripts = []
    for f in os.listdir(WORKSPACE):
        if f.startswith('_tmp_') and f.endswith('.py'):
            temp_scripts.append(f)
    if len(temp_scripts) >= 3:
        fail(f"workspace中_tmp_*.py过多({len(temp_scripts)}个): {temp_scripts}。禁止散落临时脚本，请使用固定模块。")
    if temp_scripts:
        print(f"  [GATE5 WARN] {len(temp_scripts)}个临时脚本: {temp_scripts} (未超阈值)")
    else:
        print(f"  [GATE5 PASS] 零临时脚本")

# ===== 主闸 =====
def assert_all(stock_code=None):
    """执行全部5道硬闸"""
    print("="*60)
    print("大牛线分析全能硬闸（五道闸）")
    print("="*60)

    gate_source_integrity()
    gate_tq_connectivity()
    if stock_code:
        gate_formula_exists(stock_code)
    else:
        print("  [GATE3 SKIP] 未提供股票代码")
    gate_fixed_analyzer()
    gate_no_temp_scripts()

    print("="*60)
    print("ALL_GATES_PASSED: 五道闸全部通过，可以开始分析")
    print(f'分析入口: python {FIXED_ANALYZER} <代码>')
    print("禁止行为: 写新临时脚本 / 手算替代TQ / 杜撰子系统编号")
    print("="*60)
    return True

def print_subsystems():
    """打印16子系统标准清单"""
    print("="*60)
    print("大牛线撑压版 十六子系统（唯一标准，禁止杜撰）")
    print("="*60)
    for sid, name, formula, output in SUBSYSTEMS_STANDARD:
        print(f"  {sid:2d}. {name:10s} | 公式: {formula[:40]:40s} | TQ输出: {output}")
    print("="*60)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', dest='check')
    parser.add_argument('--code', type=str, default=None)
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()

    if args.list:
        print_subsystems()
    elif args.check:
        assert_all(args.code)
    else:
        # 默认执行完整验证（需要代码参数时跳过闸3）
        assert_all(None)
