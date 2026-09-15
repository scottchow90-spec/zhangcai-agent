"""Independent receipt-time replay of the explicitly requested annual-reference workflow.

The producer cannot certify completion. This checker rebuilds from bound raw
inputs and compares every snapshot/output field; no business status grants PASS.
Other actions and the original causal-market mode remain contract-only.
"""
from __future__ import annotations

import contextlib
from datetime import datetime, time, timedelta
import hashlib
import io
import json
import math
from pathlib import Path
import tempfile

SKILL_ID = 'a-share-short-burst-score'
MODE = 'yearly-limit-close-premium'
CONFIG_SHA256 = 'a46728f4db815605b9be76b360d17dee346e4a18ae944e2e1eec4e9534016190'
FILES = {
    'full_selected_request': 'full_selected_request.json',
    'raw_input_bindings': 'raw_input_bindings.json',
    'historical_reference': 'historical_limit_followthrough_reference.json',
    'historical_reference_replay': 'historical_reference_replay.json',
    'current_streaks': 'current_streaks.csv',
    'current_streaks_source_check': 'current_streaks_source_check.json',
    'event_source_audit': 'event_source_audit.json',
    'raw_data_audit': 'raw_data_audit.json',
    'billboard_source_audit': 'billboard_source_audit.json',
    'prepared_snapshot': 'prepared_snapshot.json',
    'history_model_validation': 'history_model_validation.json',
    'analysis': 'analysis.json',
    'report': 'analysis.md',
    'input_binding': 'input_binding.json',
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError('duplicate_json_key:' + key)
            out[key] = value
        return out
    def constant(value):
        raise ValueError('nonfinite_json:' + value)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),
                      object_pairs_hook=unique, parse_constant=constant)


def exact(actual, expected, label):
    # JSON encoding preserves the distinction between booleans and numbers.
    encode = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True,
                                 separators=(',', ':'), allow_nan=False)
    if encode(actual) != encode(expected):
        raise ValueError('semantic_replay_mismatch:' + label)


def relocate(value, old, new):
    """Only replace a replay-created file's absolute directory, never fields."""
    if isinstance(value, dict):
        return {relocate(k, old, new): relocate(v, old, new) for k, v in value.items()}
    if isinstance(value, list):
        return [relocate(v, old, new) for v in value]
    if isinstance(value, str) and (value == str(old) or value.startswith(str(old) + '\\') or value.startswith(str(old) + '/')):
        return str(new) + value[len(str(old)):]
    return value


def artifact_paths(business, run):
    artifacts = business.get('artifacts')
    if not isinstance(artifacts, dict):
        raise ValueError('replay_artifacts_missing')
    out = {}
    for key, filename in FILES.items():
        value = artifacts.get(key)
        if not isinstance(value, str):
            raise ValueError('replay_artifact_missing:' + key)
        path = Path(value).resolve()
        if path != (run / filename).resolve() or not path.is_file():
            raise ValueError('replay_artifact_not_current_run:' + key)
        out[key] = path
    return out


def request_identity(args, paths):
    if len(args) != 4 or args[0:3] != ['--action', 'analyze', '--input']:
        raise ValueError('replay_action_arguments_not_exact')
    source = Path(args[3]).resolve()
    if not source.is_file() or digest(source) != digest(paths['full_selected_request']):
        raise ValueError('replay_original_input_mismatch')
    request = read_json(paths['full_selected_request'])
    if request.get('schema') != 'SHORT_BURST_FULL_SELECTED_REQUEST_V1':
        raise ValueError('replay_request_schema')
    if request.get('market_reference', {}).get('mode') != MODE:
        raise ValueError('replay_mode_not_registered')
    if request.get('history_model') is not None:
        raise ValueError('replay_external_history_model_not_registered')
    at = datetime.fromisoformat(request['as_of'])
    if at.utcoffset() != timedelta(hours=8) or at.date().isoformat() != request['trade_date'] or at.time() < time(15):
        raise ValueError('replay_postmarket_cutoff_invalid')
    return request, source


def verify_bindings(bindings):
    if not isinstance(bindings, dict) or not bindings:
        raise ValueError('replay_raw_bindings_empty')
    for filename, expected in bindings.items():
        path = Path(filename)
        if not path.is_absolute() or not path.is_file() or digest(path) != expected:
            raise ValueError('replay_raw_binding_changed:' + filename)


def verify_score_arithmetic(analysis, snapshot, config):
    """Independent arithmetic check; full precision equality is replayed separately.

    Exported components are rounded to two decimals. Their weighted average can
    differ from the unrounded engine base by at most one cent. No field is
    excluded or rounded for the full-output comparison performed by check().
    """
    mapping = {'技术动量': 'technical', '结构地位': 'structure', '资金质量': 'capital',
               '资金弹性': 'elasticity', '事件驱动': 'catalyst', '历史验证': 'history'}
    weights = config['scoring']['component_weights']
    wanted = {row['code'] for row in snapshot['stocks']}
    rows = analysis['results']
    if len(rows) != len(wanted) or {r['code'] for r in rows} != wanted:
        raise ValueError('replay_result_candidate_scope')
    denominator = sum(weights[k] for k in mapping.values())
    for row in rows:
        components = row['score_components']
        if set(components) != set(mapping):
            raise ValueError('replay_six_components_missing')
        for n in [*components.values(), row['score_before_risk'], row['score_risk_penalty'], row['short_burst_score']]:
            if isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n):
                raise ValueError('replay_invalid_numeric_score')
        base = sum(components[k] * weights[mapping[k]] for k in mapping) / denominator
        if abs(base - row['score_before_risk']) > .01000001:
            raise ValueError('replay_component_weighted_sum')
        penalty = sum(row['score_risk_details'].values())
        if round(penalty, 2) != row['score_risk_penalty']:
            raise ValueError('replay_risk_sum')
        if round(max(0., min(100., row['score_before_risk'] - penalty)), 2) != row['short_burst_score']:
            raise ValueError('replay_final_score_arithmetic')
        if components['历史验证'] != 50.0 or row['history_stats'].get('available') is not False:
            raise ValueError('replay_annual_reference_used_as_score')
        if row.get('conclusion') == '核心候选':
            raise ValueError('replay_unqualified_production_claim')
    if [r['code'] for r in rows] != [r['code'] for r in sorted(rows, key=lambda r: (-r['short_burst_score'], r['code']))]:
        raise ValueError('replay_ranking_policy')
    if [r['rank'] for r in rows] != list(range(1, len(rows) + 1)):
        raise ValueError('replay_ranking_numbers')


def verify_reference_separation(snapshot):
    exact(snapshot.get('market', {}).get('historical_reference_policy'),
          {'mode': MODE, 'use': 'reference_only', 'affects_scoring_formula': False},
          'reference_only_policy')
    forbidden = {'next_close_premium_count', 'next_close_premium_rate',
                 'next_close_return', 'next_close_premium', 'next_market_session',
                 'return_t1', 'return_t3', 'return_t5', 'event_labels'}
    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in forbidden:
                    raise ValueError('replay_future_label_in_daily_snapshot:' + key)
                visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
    visit(snapshot)


def verify_annual_window(reference, trade_date):
    end = datetime.strptime(trade_date, '%Y-%m-%d').date()
    try:
        previous_anniversary = end.replace(year=end.year - 1)
    except ValueError:  # February 29 maps to February 28 in the previous year.
        previous_anniversary = end.replace(year=end.year - 1, day=28)
    start = previous_anniversary + timedelta(days=1)
    if (reference.get('start_date'), reference.get('end_date'), reference.get('as_of_date')) != (start.isoformat(), trade_date, trade_date):
        raise ValueError('replay_reference_not_exact_one_calendar_year')


def check(root, business, extra_args, run_dir):
    out = {'status': 'BLOCKED', 'scope': 'contract_execution',
           'full_workflow_completed': False, 'errors': [], 'verified_steps': [],
           'limitations': ['workflow_completion_is_not_return_validation_or_trading_permission']}
    args = list(extra_args)
    if len(args) != 4 or args[:3] != ['--action', 'analyze', '--input']:
        return {**out, 'status': 'NOT_APPLICABLE', 'limitations': ['requested_action_semantics_not_registered']}
    try:
        incoming = read_json(args[3])
        if incoming.get('schema') != 'SHORT_BURST_FULL_SELECTED_REQUEST_V1' or incoming.get('market_reference', {}).get('mode') != MODE:
            return {**out, 'status': 'NOT_APPLICABLE', 'limitations': ['requested_mode_semantics_not_registered']}
        root, run = Path(root).resolve(), Path(run_dir).resolve()
        if business.get('skill_id') != SKILL_ID or business.get('schema') != 'STOCK_CANONICAL_BUSINESS_RESULT_V1':
            raise ValueError('replay_business_identity')
        if business.get('execution_purpose') != 'CONTRACT_EXECUTION_ONLY':
            raise ValueError('replay_producer_purpose')
        paths = artifact_paths(business, run)
        before = {key: digest(path) for key, path in paths.items()}
        request, source = request_identity(args, paths)
        out['data_date'] = request['trade_date']
        if request.get('screenshot') is not None:
            screenshot = request['screenshot']
            copy_path = Path(business.get('artifacts', {}).get('request_screenshot', '')).resolve()
            if copy_path != (run / 'request_screenshot.png').resolve() or not copy_path.is_file():
                raise ValueError('replay_screenshot_copy_missing_or_outside_run')
            if digest(copy_path) != screenshot.get('sha256') or digest(screenshot['path']) != screenshot.get('sha256'):
                raise ValueError('replay_screenshot_identity_changed')
            paths['request_screenshot'] = copy_path
            before['request_screenshot'] = digest(copy_path)
        bindings = read_json(paths['raw_input_bindings'])
        verify_bindings(bindings)
        verify_annual_window(read_json(paths['historical_reference']), request['trade_date'])
        cfg_path = root / 'templates/default-config.json'
        if digest(cfg_path) != CONFIG_SHA256:
            raise ValueError('replay_original_formula_configuration_changed')
        config = read_json(cfg_path)
        snapshot = read_json(paths['prepared_snapshot'])
        analysis = read_json(paths['analysis'])
        input_binding = read_json(paths['input_binding'])
        exact(input_binding, {'path': str(paths['prepared_snapshot']), 'sha256': before['prepared_snapshot']}, 'input_binding')
        from lhbpost.event_source_replay import check_event_sources
        events_check = check_event_sources(request, read_json(paths['event_source_audit']))
        if events_check.get('status') != 'PASS':
            raise ValueError('replay_event_source_failed:' + str(events_check.get('errors')))
        from lhbpost.selected_workflow import prepare_selected
        from lhbpost.core import analyze_snapshot
        from workbuddy_entry import render_md
        # No production data is written and no provider is contacted by replay.
        with tempfile.TemporaryDirectory(prefix='short-burst-semantic-') as scratch_name:
            scratch = Path(scratch_name).resolve()
            replay_artifacts = {}
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                prepared, model = prepare_selected(request, source, scratch, replay_artifacts)
            if model is not None:
                raise ValueError('replay_model_unexpected')
            replay_snapshot = read_json(prepared)
            # Re-enumeration catches omitted bindings as well as changed files.
            for key in ['raw_input_bindings', 'raw_data_audit', 'billboard_source_audit',
                        'historical_reference', 'historical_reference_replay',
                        'current_streaks_source_check', 'event_source_audit',
                        'history_model_validation', 'prepared_snapshot']:
                value = read_json(replay_artifacts[key])
                exact(read_json(paths[key]), relocate(value, scratch, run), key)
            if Path(replay_artifacts['current_streaks']).read_bytes() != paths['current_streaks'].read_bytes():
                raise ValueError('replay_streak_file_mismatch')
            expected = analyze_snapshot(replay_snapshot, config, None)
            exact(analysis, expected, 'all_analysis_fields')
            if paths['report'].read_text(encoding='utf-8') != render_md(expected) + '\n':
                raise ValueError('replay_report_mismatch')
        verify_reference_separation(snapshot)
        verify_score_arithmetic(analysis, snapshot, config)
        verify_bindings(bindings)
        for key, path in paths.items():
            if digest(path) != before[key]:
                raise ValueError('replay_artifact_changed_during_check:' + key)
        out.update(status='PASS', scope='workflow_decision', full_workflow_completed=True,
                   verified_steps=['original_request_and_exact_selected_securities_bound',
                     'raw_input_set_reenumerated_and_all_hashes_rechecked',
                     'audit_time_cutoff_PIT_market_sector_positions_and_snapshot_rebuilt',
                     'annual_limit_ST_exright_next_close_samples_replayed_outside_score',
                     'current_streaks_and_complete_billboard_source_pages_replayed',
                     'official_announcement_query_pages_documents_and_event_rows_replayed',
                     'all_analysis_fields_report_six_components_risks_ranking_exactly_replayed',
                     'original_weights_and_unqualified_history_neutrality_preserved'],
                   workflow_variant='explicit_selected_annual_reference_original_scoring',
                   selected_count=len(request['stocks']), event_source_check=events_check)
    except Exception as exc:
        out['errors'] = [type(exc).__name__ + ':' + str(exc)]
    return out
