#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
_DATA_ROOT = os.environ.get("ONESTOCK_STOCK_DATA_ROOT", "").strip()
REPORTS = (
    Path(_DATA_ROOT).expanduser().resolve() / "runtime" / "skills" / "dragon-pullback" / "reports"
    if _DATA_ROOT
    else WORKSPACE / "skills" / "dragon-pullback" / "reports"
)
PYTHON = sys.executable
sys.path.insert(0, str(WORKSPACE / 'scripts'))

from stock_support_pressure_adapter import run_current_support_pressure


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def run_probe(formula_name: str, symbol: str, count: int, dividend_type: int = 0) -> dict:
    """Run via tdx-local-hub, not tq_dynamic_bridge, so stock guard stays clean."""
    script = WORKSPACE / 'skills' / 'tdx-local-hub' / 'scripts' / 'tdx_hub.py'
    completed = subprocess.run(
        [PYTHON, str(script), 'five', symbol],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=180,
    )
    parsed = None
    try:
        start = completed.stdout.find('{')
        end = completed.stdout.rfind('}')
        if start >= 0 and end >= start:
            all_data = json.loads(completed.stdout[start:end + 1])
            if formula_name == '大牛线4.0':
                item = next((x for x in all_data.get('items', []) if x.get('formula') == '大牛线4.0'), None)
            elif formula_name == '飞龙在天':
                item = next((x for x in all_data.get('items', []) if x.get('formula') == '飞龙在天'), None)
            else:
                item = None
            parsed = {'ok': bool(item and item.get('ok')), 'item': item, 'all_ok': all_data.get('ok')}
    except Exception:
        parsed = None
    return {'returncode': completed.returncode, 'parsed': parsed, 'stdout': completed.stdout[-8000:], 'stderr': completed.stderr[-8000:]}




def load_support_data_v2(workspace: Path):
    run_dir = REPORTS / 'support-pressure-input' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    return run_current_support_pressure(workspace, run_dir, timeout=600)




def main() -> int:
    # 2026-06-22 加固: 支持 --help / --dry-run 快速响应 (跳过 tdx_hub five 公式调用, 避免 30s+ 超时)
    import argparse
    p = argparse.ArgumentParser(description="龙回头 smoke (run 大牛线4.0 + 飞龙在天)")
    p.add_argument("--dry-run", action="store_true", help="跳过 tdx_hub five 公式调用")
    ns, _unknown = p.parse_known_args()

    REPORTS.mkdir(parents=True, exist_ok=True)
    support = load_support_data_v2(WORKSPACE)
    candidate = support['candidates'][0]
    symbol = candidate['code']

    if ns.dry_run:
        payload = {
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'ok': True,
            'status': 'DRY_RUN_OK',
            'symbol': symbol,
            'support_candidate': candidate,
            'notes': 'dry-run 跳过 tdx_hub five 调用 (避免超时)',
            'fallback_used': bool(support.get('fallback_used')),
        }
        out = REPORTS / f'dragon-pullback-smoke-{datetime.now().strftime("%Y%m%d")}.json'
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'ok': True, 'status': 'DRY_RUN_OK', 'report': str(out), 'symbol': symbol}, ensure_ascii=False, indent=2))
        return 0
    big_bull = run_probe('大牛线4.0', symbol, 20, dividend_type=1)
    feilong = run_probe('飞龙在天', symbol, 0)
    ok = bool((big_bull['parsed'] or {}).get('ok')) and bool((feilong['parsed'] or {}).get('ok'))
    payload = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'ok': ok,
        'symbol': symbol,
        'support_candidate': candidate,
        'big_bull': big_bull['parsed'],
        'feilong': feilong['parsed'],
        'notes': 'Rebuilt smoke uses support/resistance candidate plus live 大牛线4.0 and 飞龙在天.',
    }
    out = REPORTS / f'dragon-pullback-smoke-{datetime.now().strftime("%Y%m%d")}.json'
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': ok, 'report': str(out), 'symbol': symbol}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == '__main__':
    raise SystemExit(main())
