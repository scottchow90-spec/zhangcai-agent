#!/usr/bin/env python3
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
# -*- coding: utf-8 -*-
import sys, os, json
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


def prepare_pandas_for_akshare_news():
    try:
        import pandas as pd

        pd.options.mode.string_storage = "python"
        pd.set_option("future.infer_string", False)
    except Exception:
        pass

try:
    from _date_utils import resolve_latest_trade_date
    _RESOLVED = resolve_latest_trade_date()
except Exception:
    _RESOLVED = None
DATE = sys.argv[1] if len(sys.argv) > 1 and str(sys.argv[1]).isdigit() else _RESOLVED
if not DATE:
    raise SystemExit("collect_rdxz: cannot determine trading date (no --date and TDX lookup failed)")

def main():
    prepare_pandas_for_akshare_news()
    import akshare as ak
    raw_path = Path(fr"D:\C盘转移\日志\codex\tmp_lb\data\raw2_{DATE}.json")
    out = json.loads(raw_path.read_text(encoding='utf-8'))
    name_map = {r['code']: r['name'] for r in out['zt_pool']}
    # The report's RDXZ table is filtered to涨停池/pick codes. Avoid scanning
    # unrelated LHB-only symbols so the single execution path finishes inside
    # the full-skill audit budget.
    codes = list(dict.fromkeys([r['code'] for r in out['zt_pool']]))
    print(f'codes: {len(codes)}')

    C_NW_TT = '\u65b0\u95fb\u6807\u9898'
    C_NW_CT = '\u65b0\u95fb\u5185\u5bb9'
    C_NW_PT = '\u53d1\u5e03\u65f6\u95f4'
    C_NW_SR = '\u6587\u7ae0\u6765\u6e90'

    trade_end = datetime.strptime(DATE, '%Y%m%d').replace(hour=23, minute=59, second=59)
    earliest = trade_end - timedelta(hours=72)
    news = []
    errors = []
    for code in codes:
        name = name_map.get(code, '')
        try:
            df = ak.stock_news_em(symbol=code)
        except Exception as exc:
            errors.append({'code': code, 'error': f'{type(exc).__name__}: {exc}'})
            continue
        if df is None or df.empty:
            continue
        for _, r in df.head(8).iterrows():
            try:
                title = str(r.get(C_NW_TT, '')).strip()
                content = str(r.get(C_NW_CT, '')).strip()
                published = str(r.get(C_NW_PT, '')).strip()
                source = str(r.get(C_NW_SR, '')).strip()
                if not title or not content or not published or not source:
                    continue
                if code not in title+content and name not in title+content:
                    continue
                try:
                    published_dt = datetime.fromisoformat(published[:19].replace('/', '-'))
                except ValueError:
                    continue
                if published_dt < earliest or published_dt > trade_end:
                    continue
                news.append({
                    'code': code,
                    'name': name,
                    'title': title[:60],
                    'content': content[:80],
                    'published': published[:19],
                    'source': source[:30],
                    'evidence_id': f'RDXZ:{code}:{published[:19]}:{source[:30]}',
                })
            except Exception:
                continue
    news.sort(key=lambda x: x['published'], reverse=True)
    out['rdxz'] = news
    out['rdxz_collection'] = {
        'window_hours': 72,
        'codes_probed': len(codes),
        'rows': len(news),
        'errors': errors,
    }
    if not news:
        print('ERROR: no stock-bound news rows in the 72-hour window', file=sys.stderr)
        return 2
    print(f'rdxz: {len(news)}')

    p = Path(fr"D:\C盘转移\日志\codex\tmp_lb\data\raw3_{DATE}.json")
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    print(f'saved: {p}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
