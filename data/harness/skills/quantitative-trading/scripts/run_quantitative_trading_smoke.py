#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import importlib.util
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
REPORTS = WORKSPACE / 'skills' / 'quantitative-trading' / 'reports'


def load_tdx_live_candidates(workspace: Path):
    hub_path = workspace / 'skills' / 'tdx-local-hub' / 'scripts' / 'tdx_hub.py'
    spec = importlib.util.spec_from_file_location('quantitative_trading_tdx_hub', hub_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot load TDX hub: {hub_path}')
    hub = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hub)
    block_root = Path(r'C:\new_tdx_mock\T0002\blocknew')
    raw_symbols = []
    block_paths = []
    for name in ('ZTC.blk', 'FLZT.blk'):
        block_path = block_root / name
        block_paths.append(str(block_path))
        raw_symbols.extend(hub.read_block_file(block_path))
    normalized_symbols = []
    seen = set()
    for raw in raw_symbols:
        normalized = hub.normalize_symbol(raw)
        if normalized not in seen:
            seen.add(normalized)
            normalized_symbols.append(normalized)
    candidates = []
    latest_dates = []
    for normalized in normalized_symbols:
        path = hub.day_path(normalized)
        rows = hub.read_records(path, hub.DAY_RECORD, hub.parse_day_record, 60)
        if len(rows) < 21:
            continue
        closes = [float(item['close']) for item in rows]
        momentum20 = closes[-1] / closes[-21] - 1 if closes[-21] else 0.0
        score = round(max(0.0, min(100.0, 50.0 + momentum20 * 200.0)), 3)
        market = normalized[:2].upper()
        code = normalized[-6:]
        candidates.append({
            'code': code,
            'symbol': f'{code}.{market}',
            'score': score,
            'momentum20': round(momentum20, 6),
            'latest_close': closes[-1],
            'latest_date': str(rows[-1]['date']),
            'kline_path': str(path),
            'source': 'tdx_live_blocknew',
        })
        latest_dates.append(str(rows[-1]['date']))
    return {
        'candidates': candidates,
        'data_source': 'tdx_live_blocknew',
        'fallback_used': False,
        'block_paths': block_paths,
        'latest_date': max(latest_dates) if latest_dates else None,
    }




def load_support_data_v2(workspace: Path):
    """2026-06-22 加固 v2: 优先读 support_pressure_scan_20260525.json (历史固定数据),
    缺失则 fallback 到 reports/sr_*/support-pressure-analysis-workflow/workflow_report.json (最新 multi-candidate 扫描),
    最后再 fallback 到 manual_run (single candidate).
    返回 {'candidates': [...]} 结构 (多 candidate).
    """
    import glob as _glob
    primary = workspace / 'support_pressure_scan_20260525.json'
    if primary.exists():
        return json.loads(primary.read_text(encoding='utf-8'))
    # 优先级 1: 最新 sr_* 多候选扫描报告
    sr_reports = sorted(_glob.glob(str(workspace / 'reports' / 'sr_*' / 'support-pressure-analysis-workflow' / 'workflow_report.json')),
                       key=lambda p: Path(p).stat().st_mtime, reverse=True)
    for sr in sr_reports:
        try:
            d = json.loads(Path(sr).read_text(encoding='utf-8'))
            trans = d.get('transmission', {}).get('transmissions', [])
            if len(trans) >= 4:
                cands = []
                for t in trans:
                    sym = t.get('symbol', '')
                    code = sym.split('.')[0] if sym else ''
                    cands.append({
                        'code': code,
                        'name': t.get('name', ''),
                        'buy_low': 0,
                        'invalid': '',
                        'pos60': 0.5 if t.get('alignment') == 'neutral' else (0.3 if t.get('alignment') == 'bullish' else 0.8),
                        'score': 50 if t.get('alignment') == 'neutral' else (70 if t.get('alignment') == 'bullish' else 30),
                        'source': 'fallback_sr_workflow_report',
                    })
                return {'candidates': cands, 'data_source': 'fallback_sr', 'fallback_used': True, 'sr_report': sr}
        except Exception:
            continue
    # 优先级 2: manual_run single candidate
    fallback = workspace / 'reports' / 'manual_run' / 'support-resistance-analysis' / 'support_resistance_report.json'
    if fallback.exists():
        d = json.loads(fallback.read_text(encoding='utf-8'))
        return {
            'candidates': [{
                'code': d.get('symbol', '000001.SH'),
                'name': d.get('name', '上证指数'),
                'buy_low': d.get('support_zones', [{}])[0].get('level', 0) if d.get('support_zones') else 0,
                'invalid': d.get('invalidation_line', ''),
                'pos60': 0.5, 'score': 50,
                'source': 'fallback_support_resistance_report',
            }],
            'data_source': 'fallback_manual', 'fallback_used': True,
        }
    raise FileNotFoundError(f'no support pressure data: tried {primary}, sr_*, and {fallback}')




def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    support = load_tdx_live_candidates(WORKSPACE)
    candidates = support.get('candidates', [])[:30]
    avg_score = round(sum(item.get('score', 0) for item in candidates) / len(candidates), 3) if candidates else 0
    ok = len(candidates) >= 20
    fallback_used = bool(support.get('fallback_used'))
    final_ok = ok and not fallback_used and bool(support.get('latest_date'))
    out = REPORTS / f'quantitative-trading-smoke-{datetime.now().strftime("%Y%m%d")}.json'
    status = 'CLEAN_PASS' if final_ok else 'BUSINESS_INSUFFICIENT'
    report = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'ok': final_ok,
        'status': status,
        'universe_size': len(candidates),
        'avg_score': avg_score,
        'fallback_used': fallback_used,
        'data_source': support.get('data_source'),
        'latest_date': support.get('latest_date'),
        'block_paths': support.get('block_paths', []),
        'candidates': candidates,
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': final_ok, 'status': status, 'report': str(out), 'universe_size': len(candidates), 'data_source': support.get('data_source'), 'latest_date': support.get('latest_date')}, ensure_ascii=False, indent=2))
    return 0 if final_ok else 1


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == '__main__':
    raise SystemExit(main())
