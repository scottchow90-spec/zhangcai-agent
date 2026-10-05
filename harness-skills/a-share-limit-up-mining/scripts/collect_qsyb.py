#!/usr/bin/env python3
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
# -*- coding: utf-8 -*-
import sys, os, json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
import warnings

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_data_root

DATA_DIR = resolve_data_root() / 'strategy-data' / 'a-share-limit-up-mining'
DATA_DIR.mkdir(parents=True, exist_ok=True)

warnings.filterwarnings('ignore')
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

try:
    from _date_utils import resolve_latest_trade_date
    _RESOLVED = resolve_latest_trade_date()
except Exception:
    _RESOLVED = None
DATE = sys.argv[1] if len(sys.argv) > 1 and str(sys.argv[1]).isdigit() else _RESOLVED
if not DATE:
    raise SystemExit("collect_qsyb: cannot determine trading date (no --date and TDX lookup failed)")


def confirm_no_research_rows(code):
    import requests
    response = requests.get(
        "https://reportapi.eastmoney.com/report/list",
        params={
            "industryCode": "*", "pageSize": "1", "industry": "*", "rating": "*",
            "ratingChange": "*", "beginTime": "2000-01-01",
            "endTime": f"{datetime.now().year + 1}-01-01", "pageNo": "1",
            "qType": "0", "orgCode": "", "code": code, "rcode": "",
        },
        timeout=20,
    )
    response.raise_for_status()
    return int(response.json().get("TotalPage", -1)) == 0

def main():
    import akshare as ak
    raw_path = DATA_DIR / f"raw_{DATE}.json"
    out = json.loads(raw_path.read_text(encoding='utf-8'))
    name_map = {r['code']: r['name'] for r in out['zt_pool']}
    # The downstream Word report only binds QSYB rows to the涨停池/pick codes.
    # Scanning full LHB-only symbols doubles runtime and caused the locked
    # orchestrator to timeout before a real report could be produced.
    codes = list(dict.fromkeys([r['code'] for r in out['zt_pool']]))
    print(f'codes to probe: {len(codes)}')

    C_RES_CODE = '\u80a1\u7968\u4ee3\u7801'
    C_RES_NAME = '\u80a1\u7968\u7b80\u79f0'
    C_RES_TITLE = '\u62a5\u544a\u540d\u79f0'
    C_RES_RAT = '\u4e1c\u8d22\u8bc4\u7ea7'
    C_RES_ORG = '\u673a\u6784'
    C_RES_IND = '\u884c\u4e1a'
    C_RES_DT = '\u65e5\u671f'

    trade_day = datetime.strptime(DATE, '%Y%m%d')
    earliest = trade_day - timedelta(days=180)
    def probe_code(code):
        rows = []
        try:
            df = ak.stock_research_report_em(symbol=code)
        except KeyError as exc:
            if str(exc).strip("'\"") == "infoCode":
                try:
                    if confirm_no_research_rows(code):
                        return rows, None, True
                except Exception as confirm_exc:
                    return rows, {
                        'code': code,
                        'error': f'{type(confirm_exc).__name__}: {confirm_exc}',
                    }, False
            return rows, {'code': code, 'error': f'{type(exc).__name__}: {exc}'}, False
        except Exception as exc:
            return rows, {'code': code, 'error': f'{type(exc).__name__}: {exc}'}, False
        if df is None or df.empty:
            return rows, None, False
        for _, r in df.head(3).iterrows():
            try:
                d_raw = r.get(C_RES_DT, None)
                d_str = ''
                if d_raw is not None and str(d_raw) != 'nan':
                    if hasattr(d_raw, 'strftime'):
                        d_str = d_raw.strftime('%Y-%m-%d')
                    else:
                        d_str = str(d_raw)[:10]
                row_code = str(r.get(C_RES_CODE, code)).strip()
                row_name = str(r.get(C_RES_NAME, '')).strip()
                if row_code != code or not row_name or not d_str:
                    continue
                report_day = datetime.strptime(d_str[:10], '%Y-%m-%d')
                if report_day < earliest or report_day > trade_day:
                    continue
                rows.append({
                    'code': row_code,
                    'name': row_name,
                    'report': str(r.get(C_RES_TITLE, '')).strip()[:50],
                    'rating': str(r.get(C_RES_RAT, '')).strip(),
                    'org': str(r.get(C_RES_ORG, '')).strip(),
                    'industry': str(r.get(C_RES_IND, '')).strip(),
                    'date': d_str,
                    'evidence_id': f'QSYB:{code}:{d_str}:{str(r.get(C_RES_ORG, "")).strip()}',
                })
            except Exception:
                continue
        return rows, None, False

    research = []
    errors = []
    confirmed_empty_codes = []
    # Bounded concurrency keeps the complete per-stock review inside the
    # orchestrator's fixed 240-second collection window.
    with ThreadPoolExecutor(max_workers=min(8, len(codes))) as pool:
        for code, (rows, error, confirmed_empty) in zip(codes, pool.map(probe_code, codes)):
            research.extend(rows)
            if error:
                errors.append(error)
            if confirmed_empty:
                confirmed_empty_codes.append(code)
    research.sort(key=lambda x: x['date'], reverse=True)
    out['qsyb'] = research
    out['qsyb_collection'] = {
        'window_days': 180,
        'codes_probed': len(codes),
        'rows': len(research),
        'confirmed_empty_codes': confirmed_empty_codes,
        'review_complete_codes': len(codes) - len(errors),
        'errors': errors,
    }
    if errors:
        print(f"ERROR: research review incomplete for {len(errors)} codes", file=sys.stderr)
        return 2
    if not research:
        print('ERROR: no stock-bound research rows in the 180-day window', file=sys.stderr)
        return 2
    print(f'qsyb: {len(research)}')

    p = DATA_DIR / f"raw2_{DATE}.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    print(f'saved: {p}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
