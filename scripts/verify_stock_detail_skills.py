#!/usr/bin/env python3
"""Run the ten existing canonical selftests and the actual Harness provider check."""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from release_verification import app_root, emit, stock_skill_ids


def run_json(command, root, env, timeout=120):
    result = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=timeout)
    import json
    value = json.loads(result.stdout.decode('utf-8-sig'))
    if result.returncode or value.get('status') != 'CLEAN_PASS':
        raise ValueError(f"exit={result.returncode}; status={value.get('status')}; errors={value.get('errors', [])}")
    return value


def verify(root, static_only=False):
    ids = stock_skill_ids(root)
    errors, passed, discovered = [], [], 0
    frontend = root / 'app/home-client.tsx'
    if frontend.is_file():
        match = re.search(r'const stockDetailSkills=\[(.*?)\];', frontend.read_text(encoding='utf-8'), re.S)
        found = re.findall(r"id:'([^']+)'", match.group(1)) if match else []
        if found != ids:
            errors.append('Stock-detail release IDs differ from the actual frontend entry list')
    with tempfile.TemporaryDirectory(prefix='zhangcai-stock-check-') as temp:
        env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8',
               'STOCK_SKILLS_ROOT': str(root / 'harness-skills'),
               'STOCK_CANONICAL_RUNTIME': str(root / 'scripts/stock_canonical_runtime.py'),
               'ZHANGCAI_APP_ROOT': str(root), 'ZHANGCAI_DATA_DIR': temp,
               'ONESTOCK_STOCK_DATA_ROOT': temp, 'ZHANGCAI_PACKAGED': '1',
               'ZHANGCAI_TDX_ROOT': str(Path(temp) / '__tdx_not_configured__')}
        for skill in ids:
            entry = root / 'harness-skills' / skill / 'scripts/codex_entry.py'
            try:
                value = run_json([sys.executable, '-B', str(entry), 'selftest'], root, env)
                if value.get('skill_id') != skill or value.get('errors'):
                    raise ValueError('Selftest identity mismatch or nonempty errors')
                passed.append(skill)
            except Exception as error:
                errors.append(f'{skill}: {type(error).__name__}: {error}')
        if not static_only:
            node = os.environ.get('ZHANGCAI_RELEASE_NODE')
            if not node:
                private = root / '.runtime/node/node.exe'
                node = str(private) if private.is_file() else shutil.which('node')
            try:
                if not node:
                    raise ValueError('Node runtime unavailable')
                env['ZHANGCAI_RELEASE_APP_ROOT'] = str(root)
                value = run_json([node, str(root / 'scripts/tests/verify_stock_detail_skill_discovery.mjs')], root, env)
                discovered = value['dsh_discovered']
                if discovered != 10:
                    raise ValueError('Harness did not discover all ten skills')
            except Exception as error:
                errors.append(f'DSH discovery: {type(error).__name__}: {error}')
    return {'schema': 'ZHANGCAI_STOCK_DETAIL_VERIFICATION_V1',
            'status': 'BLOCKED' if errors else 'STATIC_PASS' if static_only else 'CLEAN_PASS',
            'expected_skills': 10, 'selftests_passed': len(passed), 'dsh_discovered': discovered,
            'business_execution_tested': False, 'passed': passed, 'errors': errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--static-only', action='store_true', help='Selftests only; never reports CLEAN_PASS')
    args = parser.parse_args()
    try:
        result = verify(app_root(), args.static_only)
    except Exception as error:
        result = {'status': 'BLOCKED', 'expected_skills': 10, 'selftests_passed': 0,
                  'dsh_discovered': 0, 'errors': [f'{type(error).__name__}: {error}']}
    return emit(result)


if __name__ == '__main__':
    raise SystemExit(main())
