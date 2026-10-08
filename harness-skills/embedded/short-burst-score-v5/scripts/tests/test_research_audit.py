import csv
from datetime import date, timedelta
import pytest
from lhbpost.research import (load_labeled, acceptance, build_model,
                             validate_acceptance_checks, _bootstrap_lower_diff)


def _write(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def _row():
    return dict(event_date='2021-01-04', code='000001',model_bucket='a',
                return_t1=.01, return_t3=.02, return_t5=.03,
                max_return_t5=.05,max_drawdown_t5=-.01,
                label_end_date='2021-01-11')


def test_duplicate_event_cannot_inflate_sample_count(tmp_path):
    p=tmp_path/'a.csv';row=_row();_write(p,[row,row])
    with pytest.raises(ValueError,match='重复历史事件'):
        load_labeled(p,date(2026,1,1))


def test_unmatured_labels_are_excluded(tmp_path):
    p=tmp_path/'a.csv';_write(p,[_row()])
    assert load_labeled(p,date(2021,1,8))==[]


@pytest.mark.parametrize('field,value', [('return_t5','NaN'),('return_t1',-2),('max_drawdown_t5',.1)])
def test_invalid_labels_fail_closed(tmp_path,field,value):
    p=tmp_path/'a.csv';row=_row();row[field]=value;_write(p,[row])
    with pytest.raises(ValueError):load_labeled(p,date(2026,1,1))


def test_repeated_days_and_self_report_cannot_qualify():
    rows=[]
    for year in [2021,2022,2023]:
        for i in range(100):
            r=_row();r.update(_date=date(year,1,4),_split='oos',
                _label_end=date(year,1,11), rule_replay_verified=True,
                benchmark_return_t1=0.,benchmark_return_t5=0.,
                benchmark_max_return_t5=0.,benchmark_max_drawdown_t5=0.)
            rows.append(r)
    result=acceptance(rows)
    assert not result['passed']
    assert not result['checks']['unique_events']
    assert not result['checks']['at_least_60_oos_dates']
    assert not result['checks']['independent_rule_replay_verified']


def test_acceptance_rejects_arbitrary_truthy_checks():
    assert not validate_acceptance_checks({'passed':True,'checks':{'anything':'false'}})


def test_build_model_labels_research_scope(tmp_path):
    p=tmp_path/'a.csv';_write(p,[_row()])
    m=build_model(p,'2026-01-01',tmp_path/'model.json')
    assert m['evidence_scope']=='research_only'
    assert m['production_qualified'] is False
    assert m['rule_replay_verified'] is False


def test_bootstrap_needs_independent_dates():
    rows=[dict(_date=date(2021,1,1),a=.1,b=0.) for _ in range(1000)]
    assert _bootstrap_lower_diff(rows,'a','b') is None
