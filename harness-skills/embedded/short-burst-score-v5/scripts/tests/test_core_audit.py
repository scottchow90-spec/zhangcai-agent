import copy
import json
from pathlib import Path
import pytest
from lhbpost.core import analyze_snapshot, load_config, sector_state, evidence_conclusion
import workbuddy_entry as entry

ROOT = Path(__file__).resolve().parents[2]

def snapshot():
    return json.loads((ROOT / 'templates/snapshot-example.json').read_text(encoding='utf-8'))

@pytest.mark.parametrize('asof', ['2026-09-10T10:00:00+08:00', '2026-09-10T01:00:00+00:00'])
def test_intraday_rejected(asof):
    z = snapshot(); z['as_of'] = asof
    # Remove later source timestamps so rejection must be the market-close gate.
    def clean(x):
        if isinstance(x, dict):
            for k in list(x):
                if k in {'source_time', 'public_time'}: del x[k]
                else: clean(x[k])
        elif isinstance(x, list):
            for v in x: clean(v)
    clean(z)
    with pytest.raises(ValueError, match='收盘'): analyze_snapshot(z)

def test_utc_cutoff_uses_china_trade_date():
    z = snapshot(); z['as_of'] = '2026-09-10T13:00:00+00:00'
    assert analyze_snapshot(z)['trade_date'] == '2026-09-10'

@pytest.mark.parametrize('value', [float('nan'), float('inf'), 'NaN'])
def test_nonfinite_scoring_rejected(value):
    z = snapshot(); z['stocks'][0]['change_pct'] = value
    with pytest.raises(ValueError): analyze_snapshot(z)

def test_false_string_coverage_rejected():
    z = snapshot(); z['coverage']['industry_pit'] = 'false'
    with pytest.raises(ValueError): analyze_snapshot(z)

def test_missing_technical_features_cannot_claim_complete():
    z = snapshot(); del z['stocks'][0]['rs_20d_pctile']
    r = analyze_snapshot(z)
    assert any('rs_20d_pctile' in v for v in r['results'][0]['negative_evidence'])

def test_hard_veto_precedes_new_listing_pool():
    z = snapshot(); z['stocks'][0].update(new_unlimited=True, severe_negative_event=True)
    assert analyze_snapshot(z)['results'][0]['conclusion'] == '剔除'

def test_sector_ebb_is_not_swallowed_by_weak():
    metrics = dict(day_change_pct=-3, up_ratio=.1, limit_up_count=0, rel_strength_3d=-1, rel_strength_5d=-1)
    assert sector_state({}, load_config(), metrics)[0] == '退潮'

def test_grade_follows_final_cap():
    conclusion, grade = evidence_conclusion(95, [], '强进攻', '重点观察', False, False, {}, {}, load_config())
    assert (conclusion, grade) == ('重点观察', 'B')

@pytest.mark.parametrize('mutation', ['negative_penalty', 'zero_weights', 'inverted_thresholds', 'unknown_weight'])
def test_invalid_config_rejected(mutation):
    cfg = load_config()
    if mutation == 'negative_penalty': cfg['scoring']['risk_penalty']['event_severe'] = -100
    elif mutation == 'zero_weights': cfg['scoring']['component_weights'] = {k:0 for k in cfg['scoring']['component_weights']}
    elif mutation == 'inverted_thresholds': cfg['scoring']['conclusion_thresholds']['core'] = 0
    else: cfg['scoring']['component_weights']['typo'] = 1
    with pytest.raises(ValueError): analyze_snapshot(snapshot(), cfg)

def test_analysis_does_not_mutate_input_workflow():
    z = snapshot(); before = copy.deepcopy(z)
    analyze_snapshot(z)
    assert z == before

def test_declared_missing_source_is_not_erased_by_placeholder():
    z=snapshot(); z['stocks'][0]['missing_score_features']=['rs_20d_pctile']
    result=analyze_snapshot(z)['results'][0]
    assert result['audit']['score_factor_details']['technical']['rs20']==.5
    assert any('rs_20d_pctile' in x for x in result['negative_evidence'])

def test_model_self_attestation_cannot_unlock_production():
    from lhbpost.core import validate_history_model
    from lhbpost.research import REQUIRED_ACCEPTANCE_CHECKS
    model={'model_cutoff':'2026-09-09','validation_scheme':'walk_forward_oos',
           'production_qualified':True,'rule_replay_verified':True,'evidence_scope':'production',
           'provenance_hash':'a'*64,'buckets':{},'walk_forward_folds':[{'fold':'fake'}],
           'acceptance':{'passed':True,'checks':{k:True for k in REQUIRED_ACCEPTANCE_CHECKS}}}
    assert validate_history_model(model,'2026-09-10',load_config())['status']=='拒绝'

@pytest.mark.parametrize('mode', ['empty', 'omitted', 'traversal', 'extra'])
def test_manifest_cannot_skip_integrity_checks(tmp_path, monkeypatch, mode):
    import shutil
    for rel in entry.REQUIRED:
        p = tmp_path / rel; p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, p)
    idx = json.loads((ROOT / 'references/package-index.json').read_text(encoding='utf-8'))
    # This fixture deliberately includes all files actually present, so omission alone is tested.
    idx['files'] = [{'path':p.relative_to(tmp_path).as_posix(), 'size':p.stat().st_size, 'sha256':entry._sha(p)}
                    for p in tmp_path.rglob('*') if p.is_file() and p.name != 'package-index.json']
    idx['file_count'] = len(idx['files'])
    if mode == 'empty': idx['files'] = []
    elif mode == 'omitted': idx['files'] = [x for x in idx['files'] if x['path'] != 'SKILL.md']
    elif mode == 'traversal': idx['files'][0]['path'] = '../outside'
    elif mode == 'extra': (tmp_path / 'scripts/unlisted.py').write_text('pass')
    (tmp_path / 'references/package-index.json').write_text(json.dumps(idx), encoding='utf-8')
    monkeypatch.setattr(entry, 'ROOT', tmp_path)
    assert entry.verify() != 0
