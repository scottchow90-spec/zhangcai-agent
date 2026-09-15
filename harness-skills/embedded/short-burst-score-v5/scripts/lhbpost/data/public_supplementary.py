"""Add verified public evidence without changing its coverage meaning."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd


def acquire_public_supplementary(adapter, start, end):
    from .public_gap_sources import fetch_csi2000, fetch_candidate_announcements
    out = adapter.out
    manifest = adapter.manifest
    def fail(source, exc):
        manifest['failures'].append({'source':source,'error':f'{type(exc).__name__}:{exc}'})
    try:
        from .sz_historical_names import acquire_sz_historical_names
        names=acquire_sz_historical_names(out/'source_evidence/sz_historical_names')
        manifest['historical_short_name_source']=names
        if names['status']!='ACQUIRED_DATED_SHORT_NAME_CHANGES':
            fail('sz_historical_names',ValueError(names.get('error','source_incomplete')))
    except Exception as exc:
        fail('sz_historical_names',exc)
    try:
        calendar = pd.read_csv(out/'trade_cal.csv', dtype={'cal_date':str})
        dates = calendar.loc[calendar.is_open.eq(1), 'cal_date'].tolist()
        new = fetch_csi2000(start, end, evidence_dir=out/'source_evidence/csi2000', expected_dates=dates)
        originals = [pd.read_csv(p, dtype={'trade_date':str,'ts_code':str}) for p in sorted((out/'index_daily').glob('*.csv'))]
        old = pd.concat(originals, ignore_index=True) if originals else pd.DataFrame(columns=new.columns)
        # Never overwrite the existing seven index series with only the new one.
        old = old.loc[~old.ts_code.isin(['932000.SH','932000.CSI'])]
        merged = pd.concat([old, new], ignore_index=True)
        if merged.duplicated(['ts_code','trade_date']).any():
            raise ValueError('duplicate_index_date_after_merge')
        adapter._save('index_daily', merged.to_dict('records'))
        manifest['failures'] = [x for x in manifest['failures'] if not (
            x.get('source')=='sh932000' and x.get('error')=='no_index_bars_in_requested_range')]
        manifest['tables']['index_daily']['official_csi2000_dates'] = len(new)
    except Exception as exc:
        fail('official_csi2000', exc)
    try:
        path = out/'top_list'/f'{end}.csv'
        if not path.is_file():
            raise ValueError('candidate_list_for_end_date_unavailable')
        codes = sorted(set(pd.read_csv(path, dtype={'ts_code':str}).ts_code))
        cutoff = datetime.now(timezone(timedelta(hours=8))).isoformat()
        events, coverage = fetch_candidate_announcements(codes, end, cutoff,
            evidence_dir=out/'source_evidence/announcements')
        # Source pagination completeness does not establish semantic review.
        adapter._json('source_evidence/announcement_coverage.json', coverage)
        events.to_csv(out/'source_evidence/candidate_announcements.csv', index=False, encoding='utf-8-sig')
        manifest['announcement_evidence'] = coverage
    except Exception as exc:
        fail('candidate_announcement_evidence', exc)
