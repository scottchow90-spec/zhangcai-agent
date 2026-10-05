from __future__ import annotations
import csv, hashlib, json, math, random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean, median

LABEL_COLS=('return_t1','return_t3','return_t5','max_return_t5','max_drawdown_t5')
BENCH_COLS=('benchmark_return_t1','benchmark_return_t5','benchmark_max_return_t5','benchmark_max_drawdown_t5')
REQUIRED_ACCEPTANCE_CHECKS = frozenset({
    'oos_sample_n_ge_300', 'benchmark_coverage_ge_90pct',
    't1_excess_bootstrap_5pct_gt_0', 't5_excess_bootstrap_5pct_gt_0',
    'at_least_3_oos_years', 'positive_excess_year_ratio_ge_60pct',
    'single_year_positive_excess_le_60pct', 'unique_events',
    'at_least_60_oos_dates', 'label_maturity_verified',
    'independent_rule_replay_verified',
})


def validate_acceptance_checks(acceptance):
    if not isinstance(acceptance, dict):
        return False
    checks = acceptance.get('checks')
    return (isinstance(checks, dict) and set(checks) == REQUIRED_ACCEPTANCE_CHECKS
            and all(v is True for v in checks.values())
            and acceptance.get('passed') is True)


def _f(x):
    try:
        y=float(x);return y if math.isfinite(y) else None
    except Exception:return None

def load_labeled(path:str|Path, cutoff:date):
    rows=[];seen=set()
    with open(path,'r',encoding='utf-8-sig',newline='') as fh:
        rd=csv.DictReader(fh)
        required={'event_date','model_bucket',*LABEL_COLS}
        miss=required-set(rd.fieldnames or [])
        if miss:raise ValueError('历史标签CSV缺字段:'+','.join(sorted(miss)))
        for r in rd:
            try:d=date.fromisoformat(str(r['event_date'])[:10])
            except Exception:continue
            if d>=cutoff:continue
            code=str(r.get('code') or '').strip()
            event_key=(code,d)
            if code and event_key in seen:
                raise ValueError(f'重复历史事件: {code} {d}')
            if code:seen.add(event_key)
            label_end=None
            if r.get('label_end_date'):
                try:label_end=date.fromisoformat(r['label_end_date'])
                except ValueError:raise ValueError('label_end_date 日期无效')
                if label_end<=d:raise ValueError('标签成熟日必须晚于事件日')
                if label_end>=cutoff:continue
            r['_label_end']=label_end
            vals={k:_f(r.get(k)) for k in (*LABEL_COLS,*BENCH_COLS)}
            if any(vals[k] is None for k in LABEL_COLS):
                raise ValueError(f'历史标签包含缺失或非有限数值: {d}')
            if any(vals[k]<-1 for k in LABEL_COLS):
                raise ValueError(f'历史收益率低于-100%: {d}')
            if vals['max_drawdown_t5']>0 or vals['max_return_t5']<vals['return_t5']:
                raise ValueError(f'历史标签收益/回撤关系不一致: {d}')
            r.update(vals);r['_date']=d;rows.append(r)
    return sorted(rows,key=lambda r:r['_date'])

def assign_walk_forward(rows, cutoff:date, min_train_years:int=2, observation_days:int=90):
    """动态滚动样本外切分。

    - 最近 observation_days 天永久作为观察区，不进入验收/桶统计；
    - 最早 min_train_years 个自然年仅作开发；
    - 之后每一个完整/截至观察区前的自然年作为一个样本外折叠，训练期仅使用该年之前数据。
    规则完全由数据时间与cutoff派生，不写死2022/2024/2026等日期。
    """
    if not rows:return [],[]
    obs_start=cutoff-timedelta(days=max(30,int(observation_days)))
    eligible=[r for r in rows if r['_date']<obs_start]
    years=sorted({r['_date'].year for r in eligible})
    train_years=set(years[:max(1,int(min_train_years))])
    oos_years=years[max(1,int(min_train_years)):]
    folds=[]
    for y in oos_years:
        test=[r for r in eligible if r['_date'].year==y]
        train=[r for r in eligible if r['_date'].year<y and r.get('_label_end') is not None and r['_label_end'] < min(t['_date'] for t in test)]
        if not train:
            # 旧CSV可用于描述统计，但不伪造已隔离成熟标签的训练证据。
            train=[r for r in eligible if r['_date'].year<y]
        if not test or not train:continue
        folds.append({'fold':f'year_{y}','train_start':min(r['_date'] for r in train).isoformat(),
                      'train_end':max(r['_date'] for r in train).isoformat(),
                      'test_start':min(r['_date'] for r in test).isoformat(),
                      'test_end':max(r['_date'] for r in test).isoformat(),
                      'train_n':len(train),'test_n':len(test),'test_year':y,
                      'label_maturity_verified':all(r.get('_label_end') is not None and r['_label_end']<min(t['_date'] for t in test) for r in train)})
    oos_year_set={f['test_year'] for f in folds}
    for r in rows:
        if r['_date']>=obs_start:r['_split']='observation';r['_fold']='observation'
        elif r['_date'].year in train_years:r['_split']='development';r['_fold']='development'
        elif r['_date'].year in oos_year_set:r['_split']='oos';r['_fold']=f"year_{r['_date'].year}"
        else:r['_split']='development';r['_fold']='development'
    return rows,folds


def _wilson_lower(successes:int, n:int, z:float=1.6448536269514722):
    """90% Wilson下界；用于桶级爆发率，避免只看点估计把小样本误判为强。"""
    if n<=0:return None
    phat=successes/n
    den=1+z*z/n
    center=phat+z*z/(2*n)
    adj=z*math.sqrt((phat*(1-phat)+z*z/(4*n))/n)
    return (center-adj)/den

def _bootstrap_lower_mean(values, reps:int=600, seed:int=20260911, q:float=.10):
    vals=[float(x) for x in values if x is not None and math.isfinite(float(x))]
    if len(vals)<50:return None
    rng=random.Random(seed+len(vals));n=len(vals);means=[]
    for _ in range(reps):
        means.append(mean(vals[rng.randrange(n)] for __ in range(n)))
    means.sort();return means[max(0,min(len(means)-1,int(q*(len(means)-1))))]

def _metrics(rows):
    if not rows:return {'sample_n':0}
    t1=[r['return_t1'] for r in rows];t3=[r['return_t3'] for r in rows];t5=[r['return_t5'] for r in rows]
    mfe=[r['max_return_t5'] for r in rows];mae=[r['max_drawdown_t5'] for r in rows]
    burst_n=sum(x>=.05 for x in mfe);n=len(rows)
    out={'sample_n':n,'t1_positive_rate':sum(x>0 for x in t1)/n,'t3_positive_rate':sum(x>0 for x in t3)/n,
         't5_ge5_rate':burst_n/n,'t5_ge5_wilson_lower90':_wilson_lower(burst_n,n),
         'avg_return_t5':mean(t5),'avg_return_t5_bootstrap_lower90':_bootstrap_lower_diff([dict(r,_zero=0.) for r in rows],'return_t5','_zero',seed=20260912),
         'median_return_t5':median(t5),'avg_mae_5d':mean(mae)}
    b=[r for r in rows if r.get('benchmark_return_t5') is not None]
    excess=[r['return_t5']-r['benchmark_return_t5'] for r in b]
    out['benchmark_excess_t5']=mean(excess) if excess else None
    out['benchmark_excess_t5_bootstrap_lower90']=_bootstrap_lower_diff(b,'return_t5','benchmark_return_t5',seed=20260913) if excess else None
    return out

def _bootstrap_lower_diff(rows, metric, bench_metric, reps=1000, seed=20260911):
    # 同日股票和重叠持有期高度相关：按连续5个观察日成块重采样。
    groups=defaultdict(list)
    for r in rows:
        a,b=_f(r.get(metric)),_f(r.get(bench_metric))
        if a is not None and b is not None:groups[r['_date']].append(a-b)
    days=[groups[d] for d in sorted(groups)]
    if sum(map(len,days))<100 or len(days)<20:return None
    rng=random.Random(seed);vals=[];n=len(days)
    for _ in range(reps):
        sampled=[]
        while len(sampled)<n:
            start=rng.randrange(n)
            sampled.extend(days[(start+j)%n] for j in range(5))
        values=[x for day in sampled[:n] for x in day]
        vals.append(mean(values))
    vals.sort();return vals[int(.05*(len(vals)-1))]


def acceptance(rows):
    oos=[r for r in rows if r.get('_split')=='oos']
    years=defaultdict(list)
    for r in oos:years[r['_date'].year].append(r)
    complete_bench=[r for r in oos if all(r.get(k) is not None for k in BENCH_COLS)]
    t1_lb=_bootstrap_lower_diff(complete_bench,'return_t1','benchmark_return_t1') if complete_bench else None
    t5_lb=_bootstrap_lower_diff(complete_bench,'return_t5','benchmark_return_t5') if complete_bench else None
    checks={
        'oos_sample_n_ge_300':len(oos)>=300,
        'benchmark_coverage_ge_90pct':bool(oos) and len(complete_bench)/len(oos)>=.90,
        't1_excess_bootstrap_5pct_gt_0':t1_lb is not None and t1_lb>0,
        't5_excess_bootstrap_5pct_gt_0':t5_lb is not None and t5_lb>0,
        'at_least_3_oos_years':len(years)>=3,
        'unique_events':bool(oos) and all(str(r.get('code') or '').strip() for r in oos) and len({(r.get('code'),r['_date']) for r in oos})==len(oos),
        'at_least_60_oos_dates':len({r['_date'] for r in oos})>=60,
        'label_maturity_verified':bool(oos) and all(r.get('_label_end') is not None and r['_label_end']>r['_date'] for r in oos),
        # 此入口只接收标签CSV，不执行/证明规则冻结及逐折独立重放。
        # 禁止由CSV中的自报字段解锁生产资格。
        'independent_rule_replay_verified':False,
    }
    year_ex=[]
    for y,rs in sorted(years.items()):
        q=[r['return_t5']-r['benchmark_return_t5'] for r in rs if r.get('benchmark_return_t5') is not None]
        if q:year_ex.append((y,mean(q),sum(max(x,0) for x in q)))
    checks['positive_excess_year_ratio_ge_60pct']=bool(year_ex) and sum(v>0 for _,v,_ in year_ex)/len(year_ex)>=.60
    pos=sum(z for _,_,z in year_ex)
    checks['single_year_positive_excess_le_60pct']=bool(year_ex) and (pos<=0 or max(z for _,_,z in year_ex)/pos<=.60)
    return {'passed':all(checks.values()),'checks':checks,'oos_sample_n':len(oos),'benchmark_complete_n':len(complete_bench),
            'bootstrap_lower_excess_t1':t1_lb,'bootstrap_lower_excess_t5':t5_lb,
            'year_stats':[{'year':y,'avg_excess_t5':v,'positive_excess_sum':z} for y,v,z in year_ex]}

def build_model(events_path:str|Path, cutoff:str, output:str|Path):
    cut=date.fromisoformat(cutoff);rows=load_labeled(events_path,cut);rows,folds=assign_walk_forward(rows,cut)
    groups=defaultdict(list);split_counts=defaultdict(int)
    for r in rows:
        split_counts[r['_split']]+=1
        if r['_split']=='oos':groups[r['model_bucket']].append(r)
    raw=Path(events_path).read_bytes();prov=hashlib.sha256(raw+b'|'+cutoff.encode()+b'|v5.0-short-burst-walk-forward-oos').hexdigest()
    acc=acceptance(rows)
    model={'model_cutoff':cutoff,'validation_scheme':'walk_forward_oos','production_qualified':False,
           'evidence_scope':'research_only', 'rule_replay_verified':False,
           'acceptance':acc,'provenance_hash':prov,'split_counts':dict(split_counts),'walk_forward_folds':folds,
           'buckets':{k:_metrics(v) for k,v in sorted(groups.items())},
           'notes':'仅历史分期描述研究；本入口不训练模型、不证明规则冻结或独立重放，不具备生产资格。动态时间分期：最早2个自然年仅开发，后续逐年向前验证；cutoff前最近90天永久观察，不参与验收/桶统计。统计检查不能替代真实样本外规则重放；当前桶另外计算5日爆发率Wilson下界、5日收益及相对基准超额的bootstrap下界，禁止仅凭样本数量升级。'}
    Path(output).write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8');return model
