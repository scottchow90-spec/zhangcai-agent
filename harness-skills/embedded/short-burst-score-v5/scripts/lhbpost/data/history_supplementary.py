"""Reuse completed locally acquired historical observations through their hashes."""
from pathlib import Path
import json
from datetime import datetime

SOURCE_RUNS=Path(r'F:\Codex\Home\business_data\a-share-market-environment\executions\runs')

def select_source(start,end,root=SOURCE_RUNS):
    lo=datetime.strptime(start,'%Y%m%d').strftime('%Y-%m-%d')
    hi=datetime.strptime(end,'%Y%m%d').strftime('%Y-%m-%d')
    for path in sorted(Path(root).glob('*/market_history_source/acquisition_manifest.json'),reverse=True):
        try:
            value=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(value,dict):continue
            if value.get('schema')!='BAOSTOCK_MARKET_HISTORY_SOURCE_V1':continue
            if value.get('status') not in ('ACQUIRED_PROVIDER_SCOPE','ACQUIRED_WITH_COVERAGE_GAPS'):continue
            if value.get('start_date','9999')<=lo<=hi<=value.get('target_date',''):
                return path.parent
        except (OSError,ValueError,TypeError):continue
    raise ValueError('no_completed_hash_bound_history_source_covering_request')

def acquire_history_supplementary(adapter,start,end):
    from .history_state_import import import_history_states
    try:source=select_source(start,end)
    except ValueError:source=None
    from .local_history_acquisition import acquire_or_reuse
    source=acquire_or_reuse(adapter,start,end,source)
    result=import_history_states(source,adapter.out,
        datetime.strptime(start,'%Y%m%d').strftime('%Y-%m-%d'),
        datetime.strptime(end,'%Y%m%d').strftime('%Y-%m-%d'))
    for table in ('bak_basic','stock_st'):
        files=sorted((adapter.out/table).glob('*.csv'))
        if files:
            adapter.manifest['tables'][table]={'source_root':str(source),
                'dates':result.get('state_written_complete_dates',[]) if table=='stock_st' else result['written_complete_dates'],
                'complete_requested_daily_universe':result.get('historical_state_complete',False) if table=='stock_st' else result['complete'],
                'historical_name_verified':False,'files':[str(p.relative_to(adapter.out)) for p in files]}
    adapter.manifest['historical_state_coverage']={k:v for k,v in result.items() if k not in ('source_bindings','missing_rows','source_failures')}
    if not result['complete']:
        adapter.manifest['failures'].append({'source':'historical_state','error':'incomplete_verified_source_coverage',
            'missing_rows':len(result['missing_rows']),'failed_source_files':len(result['source_failures'])})
    return result
