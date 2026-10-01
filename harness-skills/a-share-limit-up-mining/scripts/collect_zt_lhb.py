#!/usr/bin/env python3
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
# -*- coding: utf-8 -*-
import sys, os, json
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_data_root, resolve_tdx_root

DATA_DIR = resolve_data_root() / 'strategy-data' / 'a-share-limit-up-mining'
DATA_DIR.mkdir(parents=True, exist_ok=True)
ZTC = resolve_tdx_root() / "T0002" / "blocknew" / "ZTC.blk"
try:
    from _date_utils import resolve_latest_trade_date
    _RESOLVED = resolve_latest_trade_date()
except Exception:
    _RESOLVED = None
DATE = sys.argv[1] if len(sys.argv) > 1 and str(sys.argv[1]).isdigit() else _RESOLVED
if not DATE:
    raise SystemExit("collect_zt_lhb: cannot determine trading date (no --date and TDX lookup failed)")

def time_fmt(s):
    s = str(s).strip()
    if not s or s == 'nan':
        return '-'
    if len(s) == 6 and s.isdigit():
        return f"{s[:2]}:{s[2:4]}:{s[4:6]}"
    return s

def read_ztc():
    text = ZTC.read_text(encoding='gbk', errors='ignore')
    codes = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        c = s[-6:] if len(s) >= 6 else s
        if c.isdigit() and len(c) == 6:
            codes.append(c)
    return list(dict.fromkeys(codes))


def fetch_stable_limit_up_pool(fetcher, date, code_column, max_attempts=5):
    """Require two matching, duplicate-free snapshots for the fixed trade date."""
    diagnostics = []
    previous_codes = None
    previous_df = None
    for attempt in range(1, max_attempts + 1):
        try:
            df = fetcher(date=date)
        except Exception as exc:
            diagnostics.append({
                'attempt': attempt,
                'status': 'ERROR',
                'error': f'{type(exc).__name__}: {exc}',
            })
            continue

        raw_codes = [str(value).strip() for value in df[code_column].tolist()]
        invalid_codes = sorted({
            code for code in raw_codes
            if len(code) != 6 or not code.isdigit()
        })
        duplicate_codes = sorted({
            code for code in raw_codes
            if raw_codes.count(code) > 1
        })
        diagnostics.append({
            'attempt': attempt,
            'status': 'CLEAN' if raw_codes and not invalid_codes and not duplicate_codes else 'INCOMPLETE',
            'rows': len(raw_codes),
            'unique_codes': len(set(raw_codes)),
            'invalid_codes': invalid_codes,
            'duplicate_codes': duplicate_codes,
        })
        if not raw_codes or invalid_codes or duplicate_codes:
            continue

        codes = tuple(sorted(raw_codes))
        if previous_codes == codes:
            return df, diagnostics
        previous_codes = codes
        previous_df = df

    clean_observations = sum(1 for item in diagnostics if item.get('status') == 'CLEAN')
    raise RuntimeError(
        'limit-up pool did not produce two matching duplicate-free snapshots; '
        f'clean_observations={clean_observations}; diagnostics={diagnostics}'
    )

def main():
    import akshare as ak
    out = {'date': DATE, 'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    out['ztc_local'] = read_ztc()

    C_CODE = '\u4ee3\u7801'
    C_NAME = '\u540d\u79f0'
    C_PCT = '\u6da8\u8dcc\u5e45'
    C_PRICE = '\u6700\u65b0\u4ef7'
    C_AMOUNT = '\u6210\u4ea4\u989d'
    C_FLOAT_CAP = '\u6d41\u901a\u5e02\u503c'
    C_TOTAL_CAP = '\u603b\u5e02\u503c'
    C_IND = '\u6240\u5c5e\u884c\u4e1a'
    C_LB = '\u8fde\u677f\u6570'
    C_TJ = '\u6da8\u505c\u7edf\u8ba1'
    C_FS = '\u9996\u6b21\u5c01\u677f\u65f6\u95f4'
    C_LS = '\u6700\u540e\u5c01\u677f\u65f6\u95f4'
    C_BR = '\u70b8\u677f\u6b21\u6570'
    C_SF = '\u5c01\u677f\u8d44\u91d1'
    C_TN = '\u6362\u624b\u7387'

    df, zt_collection = fetch_stable_limit_up_pool(
        ak.stock_zt_pool_em,
        DATE,
        C_CODE,
    )
    out['zt_collection'] = {
        'status': 'STABLE_CLEAN',
        'attempts': zt_collection,
    }
    zt_rows = []
    for _, r in df.iterrows():
        zt_rows.append({
            'code': str(r[C_CODE]).strip(),
            'name': str(r[C_NAME]).strip(),
            'pct_change': float(r.get(C_PCT, 0) or 0),
            'price': float(r.get(C_PRICE, 0) or 0),
            'amount': float(r.get(C_AMOUNT, 0) or 0),
            'float_cap': float(r.get(C_FLOAT_CAP, 0) or 0),
            'total_cap': float(r.get(C_TOTAL_CAP, 0) or 0),
            'industry': str(r.get(C_IND, '-')).strip(),
            'lb': int(r.get(C_LB, 1) or 1),
            'lb_tj': str(r.get(C_TJ, '-')).strip(),
            'first_seal': time_fmt(r.get(C_FS, '')),
            'last_seal': time_fmt(r.get(C_LS, '')),
            'break_count': int(r.get(C_BR, 0) or 0),
            'seal_funds': float(r.get(C_SF, 0) or 0),
            'turnover': float(r.get(C_TN, 0) or 0),
        })
    out['zt_pool'] = zt_rows

    C_NET = '\u9f99\u864e\u699c\u51c0\u4e70\u989d'
    C_BUY = '\u9f99\u864e\u699c\u4e70\u5165\u989d'
    C_SELL = '\u9f99\u864e\u699c\u5356\u51fa\u989d'
    C_REA = '\u4e0a\u699c\u539f\u56e0'

    try:
        df2 = ak.stock_lhb_detail_em(start_date=DATE, end_date=DATE)
    except Exception as e:
        print(f'  lhb_api_failed: {type(e).__name__}: {e}', file=sys.stderr)
        df2 = None
    history_df = None
    history_date = None
    if df2 is None or getattr(df2, 'empty', True):
        for delta in range(1, 11):
            try:
                cand = (datetime.strptime(DATE, "%Y%m%d") - timedelta(days=delta)).strftime("%Y%m%d")
            except Exception:
                break
            try:
                candidate_df = ak.stock_lhb_detail_em(start_date=cand, end_date=cand)
            except Exception:
                candidate_df = None
            if candidate_df is not None and not getattr(candidate_df, 'empty', True):
                history_df = candidate_df
                history_date = cand
                print(f'  lhb_history_context: found {cand}; excluded from {DATE} scoring', file=sys.stderr)
                break
    lhb_rows = []
    if df2 is None or getattr(df2, 'empty', True):
        df2 = type("E", (), {"iterrows": lambda self: iter([])})()
    for _, r in df2.iterrows():
        lhb_rows.append({
            'code': str(r[C_CODE]).strip(),
            'name': str(r[C_NAME]).strip(),
            'source_date': DATE,
            'net_buy': float(r.get(C_NET, 0) or 0),
            'buy': float(r.get(C_BUY, 0) or 0),
            'sell': float(r.get(C_SELL, 0) or 0),
            'reason': str(r.get(C_REA, '')).strip()[:50],
        })
    out['lhb'] = lhb_rows
    history_rows = []
    if history_df is not None:
        for _, r in history_df.iterrows():
            history_rows.append({
                'code': str(r[C_CODE]).strip(),
                'name': str(r[C_NAME]).strip(),
                'source_date': history_date,
                'net_buy': float(r.get(C_NET, 0) or 0),
                'buy': float(r.get(C_BUY, 0) or 0),
                'sell': float(r.get(C_SELL, 0) or 0),
                'reason': str(r.get(C_REA, '')).strip()[:50],
                'usage': 'historical_context_only',
            })
    out['lhb_history'] = history_rows
    if not lhb_rows:
        print(f'ERROR: no exact-date LHB rows for {DATE}; historical context cannot be scored', file=sys.stderr)
        return 2

    p = DATA_DIR / f"raw_{DATE}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    print(f'zt={len(zt_rows)} lhb={len(lhb_rows)} saved={p}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
