#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preflight.py — 连板挖掘前置条件检查

检查项:
  1. SKILL.md 存在 + 含 NO_REDISCOVERY
  2. references/workflow.md 存在 + >= 600 bytes
  3. references/full_workflow.md 存在
  4. references/long_run_checklist.md 存在
  5. 本地 TDX 数据可访问 (任一候选路径存在)
  6. akshare 可导入 (可选, 不阻塞)
  7. 长期运行配套脚本路径存在 (本 skill 本地 scripts)
  8. 输出目录可写

用法:
  python preflight.py           # 完整检查
  python preflight.py --strict  # 严格模式, 任何 WARN 都视为 FAIL
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import argparse
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

SKILL_DIR = Path(__file__).resolve().parents[1]
WORKFLOW_MD_MIN_SIZE = 600
TDX_CANDIDATES = [
    Path(r'C:\new_tdx_mock\T0002\blocknew\ZTC.blk'),
    Path(r'C:\new_tdx_mock\vipdoc\sh\lday'),
    Path(r'C:\new_tdx\vipdoc\sh\lday'),
    Path(r'C:\zd_tdx\vipdoc\sh\lday'),
]
INFRA_SCRIPTS = SKILL_DIR / 'scripts'
REPORTS_DIR = Path(r'D:\C盘转移\日志\codex\reports')


def check(label: str, ok: bool, detail: str = '', level: str = 'INFO') -> tuple[bool, str]:
    marker = 'OK' if ok else 'FAIL'
    color = '\033[92m' if ok else '\033[91m'
    reset = '\033[0m'
    line = f'  [{color}{marker}{reset}] {label}'
    if detail:
        line += f' — {detail}'
    print(line)
    return ok, level


def main() -> int:
    ap = argparse.ArgumentParser(description='连板挖掘前置检查')
    ap.add_argument('--strict', action='store_true', help='严格模式, WARN 也算 FAIL')
    args = ap.parse_args()

    print('=== 连板挖掘前置检查 ===\n')
    fails = 0
    warns = 0

    # 1. SKILL.md + NO_REDISCOVERY
    skill_md = SKILL_DIR / 'SKILL.md'
    if skill_md.exists():
        content = skill_md.read_text(encoding='utf-8')
        has_no_rediscovery = 'NO_REDISCOVERY' in content
        ok, _ = check('SKILL.md 存在', True, str(skill_md))
        ok2, _ = check('SKILL.md 含 NO_REDISCOVERY 标记', has_no_rediscovery)
        if not has_no_rediscovery:
            fails += 1
    else:
        check('SKILL.md 存在', False, str(skill_md))
        fails += 1

    # 2. workflow.md >= 600 bytes
    workflow_md = SKILL_DIR / 'references' / 'workflow.md'
    if workflow_md.exists():
        size = workflow_md.stat().st_size
        ok, _ = check('references/workflow.md >= 600 bytes', size >= WORKFLOW_MD_MIN_SIZE,
                      f'{size} bytes')
        if not ok:
            fails += 1
    else:
        check('references/workflow.md 存在', False, str(workflow_md))
        fails += 1

    # 3. full_workflow.md
    full_md = SKILL_DIR / 'references' / 'full_workflow.md'
    if full_md.exists():
        check('references/full_workflow.md 存在', True, f'{full_md.stat().st_size} bytes')
    else:
        check('references/full_workflow.md 存在', False, str(full_md))
        fails += 1

    # 4. long_run_checklist.md
    lr_md = SKILL_DIR / 'references' / 'long_run_checklist.md'
    if lr_md.exists():
        check('references/long_run_checklist.md 存在', True, f'{lr_md.stat().st_size} bytes')
    else:
        check('references/long_run_checklist.md 存在', False, str(lr_md))
        warns += 1

    # 5. TDX 本地数据
    tdx_ok = False
    for p in TDX_CANDIDATES:
        if p.exists():
            tdx_ok = True
            check('TDX 本地数据可访问', True, str(p))
            break
    if not tdx_ok:
        check('TDX 本地数据可访问', False,
              f'未找到任何候选路径 (尝试: {[str(p) for p in TDX_CANDIDATES]})')
        fails += 1

    # 6. akshare (可选)
    try:
        import akshare  # noqa: F401
        check('akshare 可导入', True)
    except ImportError:
        check('akshare 可导入', False, '未安装, 部分数据源会降级')
        warns += 1

    # 7. 长期运行配套脚本
    if INFRA_SCRIPTS.exists():
        check('长期运行配套脚本路径存在', True, str(INFRA_SCRIPTS))
    else:
        check('长期运行配套脚本路径存在', False, str(INFRA_SCRIPTS),
              '本地长期运行支持会失效, 但本 skill 仍可单独运行')
        warns += 1

    # 8. 输出目录
    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        test_file = REPORTS_DIR / '.lianban_mining_preflight_test'
        test_file.write_text('test', encoding='utf-8')
        test_file.unlink()
        check('输出目录可写', True, str(REPORTS_DIR))
    except Exception as e:
        check('输出目录可写', False, f'{REPORTS_DIR}: {e}')
        fails += 1

    print()
    print(f'=== 结果: {fails} FAIL, {warns} WARN ===')
    if fails > 0:
        print('⛔ 前置检查未通过, 请先解决 FAIL 项')
        return 1
    if args.strict and warns > 0:
        print('⛔ 严格模式下 WARN 也算 FAIL')
        return 1
    print('✅ 前置检查通过, 可以通过 codex_entry.py 选择执行模式')
    return 0


if __name__ == '__main__':
    sys.exit(main())
