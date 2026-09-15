"""Negative controls for receipt-time scoring replay; no market data required."""
import copy
import json
from pathlib import Path

import pytest
import workflow_replay as replay


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    return path


@pytest.mark.parametrize('changed', [{'score': True}, {'score': 2}, {'score': 1, 'hidden': 9}, {'score': 1.0}])
def test_exact_comparison_has_no_ignored_fields(changed):
    with pytest.raises(ValueError, match='semantic_replay_mismatch'):
        replay.exact(changed, {'score': 1}, 'score')


@pytest.mark.parametrize('text', ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'])
def test_ambiguous_json_cannot_be_authorized(tmp_path, text):
    path = tmp_path / 'bad.json'; path.write_text(text, encoding='utf-8')
    with pytest.raises(ValueError): replay.read_json(path)


def test_artifact_cannot_be_borrowed_from_other_run(tmp_path):
    run = tmp_path / 'run'; run.mkdir()
    business = {'artifacts': {k: str(write(run / name, {})) for k, name in replay.FILES.items()}}
    business['artifacts']['analysis'] = str(write(tmp_path / 'other/analysis.json', {}))
    with pytest.raises(ValueError, match='not_current_run:analysis'):
        replay.artifact_paths(business, run)


def test_request_source_changed_after_copy_is_rejected(tmp_path):
    source = write(tmp_path / 'source.json', {'trade_date': '2026-09-10'})
    copied = write(tmp_path / 'run/request.json', {'trade_date': '2026-09-11'})
    with pytest.raises(ValueError, match='original_input_mismatch'):
        replay.request_identity(['--action', 'analyze', '--input', str(source)], {'full_selected_request': copied})


@pytest.mark.parametrize('as_of', ['2026-09-11T14:59:59+08:00', '2026-09-12T00:00:00+08:00', '2026-09-11T23:00:00'])
def test_bad_asof_cannot_claim_postmarket_completion(tmp_path, as_of):
    value = {'schema': 'SHORT_BURST_FULL_SELECTED_REQUEST_V1', 'market_reference': {'mode': replay.MODE},
             'trade_date': '2026-09-11', 'as_of': as_of}
    source = write(tmp_path / 'source.json', value)
    with pytest.raises(ValueError, match='cutoff_invalid'):
        replay.request_identity(['--action', 'analyze', '--input', str(source)], {'full_selected_request': source})


def test_deleted_or_modified_raw_source_is_not_accepted(tmp_path):
    source = write(tmp_path / 'raw.json', {'price': 10})
    binding = {str(source): replay.digest(source)}
    write(source, {'price': 11})
    with pytest.raises(ValueError, match='raw_binding_changed'): replay.verify_bindings(binding)
    with pytest.raises(ValueError, match='bindings_empty'): replay.verify_bindings({})


def arithmetic_fixture():
    labels = ['技术动量', '结构地位', '资金质量', '资金弹性', '事件驱动', '历史验证']
    row = {'code': '600000.SH', 'rank': 1, 'score_components': dict.fromkeys(labels, 50.0),
           'score_before_risk': 50.0, 'score_risk_penalty': 2.0, 'short_burst_score': 48.0,
           'score_risk_details': {'价格透支': 2.0}, 'history_stats': {'available': False}, 'conclusion': '重点观察'}
    config = {'scoring': {'component_weights': dict(zip(['technical', 'structure', 'capital', 'elasticity', 'catalyst', 'history'], [.28, .25, .22, .1, .05, .1]))}}
    return {'results': [row]}, {'stocks': [{'code': '600000.SH'}]}, config


def test_independent_arithmetic_positive_control():
    replay.verify_score_arithmetic(*arithmetic_fixture())


def test_current_market_limit_count_is_not_a_future_label():
    snapshot = {'market': {'limit_up_count': 40, 'historical_reference_policy':
        {'mode': replay.MODE, 'use': 'reference_only', 'affects_scoring_formula': False}},
        'stocks': [{'industry_metrics': {'limit_up_count': 2}}]}
    replay.verify_reference_separation(snapshot)
    snapshot['stocks'][0]['next_close_return'] = .1
    with pytest.raises(ValueError, match='future_label'):
        replay.verify_reference_separation(snapshot)


def test_reference_policy_cannot_enable_scoring():
    with pytest.raises(ValueError, match='reference_only_policy'):
        replay.verify_reference_separation({'market': {'historical_reference_policy':
            {'mode': replay.MODE, 'use': 'reference_only', 'affects_scoring_formula': True}}})


@pytest.mark.parametrize('start', ['2026-09-10', '2024-09-12', '2025-09-11'])
def test_reference_cannot_substitute_a_different_window(start):
    with pytest.raises(ValueError, match='one_calendar_year'):
        replay.verify_annual_window({'start_date': start, 'end_date': '2026-09-11', 'as_of_date': '2026-09-11'}, '2026-09-11')


def test_exact_year_and_leap_day_are_explicit():
    replay.verify_annual_window({'start_date': '2025-09-12', 'end_date': '2026-09-11', 'as_of_date': '2026-09-11'}, '2026-09-11')
    replay.verify_annual_window({'start_date': '2023-03-01', 'end_date': '2024-02-29', 'as_of_date': '2024-02-29'}, '2024-02-29')


@pytest.mark.parametrize('fault', ['missing_stock', 'base', 'penalty', 'final', 'history', 'rank', 'probability', 'bool_score'])
def test_independent_arithmetic_rejects_result_changes(fault):
    data, snapshot, config = arithmetic_fixture(); row = data['results'][0]
    if fault == 'missing_stock': data['results'] = []
    elif fault == 'base': row['score_before_risk'] = 60.
    elif fault == 'penalty': row['score_risk_penalty'] = 0.
    elif fault == 'final': row['short_burst_score'] = 50.
    elif fault == 'history': row['history_stats']['available'] = True
    elif fault == 'rank': row['rank'] = 2
    elif fault == 'probability': row['conclusion'] = '核心候选'
    else: row['score_components']['技术动量'] = True
    with pytest.raises(ValueError): replay.verify_score_arithmetic(data, snapshot, config)


@pytest.mark.parametrize('args', [[], ['--action', 'diagnose'], ['--action', 'analyze', '--input', 'x', '--skip-audit']])
def test_other_actions_cannot_be_promoted(tmp_path, args):
    result = replay.check(tmp_path, {'status': 'CLEAN_PASS', 'full_workflow_completed': True}, args, tmp_path)
    assert result['status'] == 'NOT_APPLICABLE'
    assert result['full_workflow_completed'] is False


def test_original_mode_remains_unregistered(tmp_path):
    source = write(tmp_path / 'request.json', {'schema': 'SHORT_BURST_FULL_SELECTED_REQUEST_V1'})
    result = replay.check(tmp_path, {}, ['--action', 'analyze', '--input', str(source)], tmp_path)
    assert result['status'] == 'NOT_APPLICABLE'
    assert result['full_workflow_completed'] is False


def test_producer_true_cannot_replace_missing_artifacts(tmp_path):
    source = write(tmp_path / 'request.json', {'schema': 'SHORT_BURST_FULL_SELECTED_REQUEST_V1', 'market_reference': {'mode': replay.MODE}})
    business = {'schema': 'STOCK_CANONICAL_BUSINESS_RESULT_V1', 'skill_id': replay.SKILL_ID,
                'execution_purpose': 'CONTRACT_EXECUTION_ONLY', 'full_workflow_completed': True, 'status': 'CLEAN_PASS'}
    result = replay.check(tmp_path, business, ['--action', 'analyze', '--input', str(source)], tmp_path)
    assert result['status'] == 'BLOCKED'
    assert result['full_workflow_completed'] is False
