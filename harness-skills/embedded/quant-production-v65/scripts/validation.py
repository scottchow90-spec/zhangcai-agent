from __future__ import annotations
import json, math, statistics, hashlib
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

MODELS=['平台主升','弱转强','龙回头','黄金点火']
KEY={'平台主升':'platform','弱转强':'weak','龙回头':'comeback','黄金点火':'fire'}

def _read_jsonl(path:Path)->List[dict]:
    if not path.exists(): return []
    out=[]
    for line in path.read_text('utf-8').splitlines():
        if line.strip():
            try: out.append(json.loads(line))
            except Exception: pass
    return out

def _append_jsonl(path:Path, rows:List[dict]):
    if not rows: return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as f:
        for x in rows: f.write(json.dumps(x,ensure_ascii=False,default=str)+'\n')

def archive_after_market(results, trade_date:str, state_dir:Path, production_eligible:bool, source_match:Optional[float], baseline_n:int=150):
    path=state_dir/'event_archive.jsonl'; existing={(x.get('date'),x.get('code'),x.get('kind')) for x in _read_jsonl(path)}
    core=[r for r in results if r.core_base_hit]
    pool=[r for r in results if r.metrics.get('pool') and not r.core_base_hit]
    pool=sorted(pool,key=lambda r: hashlib.sha256((trade_date+r.code).encode()).hexdigest())[:baseline_n]
    rows=[]
    for r,kind in [(x,'core') for x in core]+[(x,'baseline') for x in pool]:
        key=(trade_date,r.code,kind)
        if key in existing: continue
        rows.append({'date':trade_date,'year':int(trade_date[:4]),'code':r.code,'name':r.name,'kind':kind,'production_eligible':bool(production_eligible),
            'bases':r.bases,'scores':r.model_scores,'components':r.components,'fire_age':r.metrics.get('fire_age',99),'labels':r.model_labels,
            'source_match':source_match,'outcomes':None})
    _append_jsonl(path,rows); return len(rows)

def mature_archive_outcomes(state_dir:Path, histories:Dict[str,List[dict]], market_dates:List[str], asof_date:str):
    """把既有AUTHORIZED盘后事件在未来5/10个市场交易日成熟后补齐结果标签。

    参考价为信号日收盘；未来窗口按市场交易日而不是股票自身有成交的K线数量，
    停牌日沿用最近收盘作为5日收盘估值，MFE/MAE只使用窗口内真实高低价并包含0基线。
    """
    path=state_dir/'event_archive.jsonl'; rows=_read_jsonl(path)
    if not rows or len(market_dates)<11: return {'matured':0,'pending':sum(1 for x in rows if x.get('production_eligible') and not _outcome_mature(x)),'unavailable':0}
    cal=[str(x) for x in market_dates]; pos={d:i for i,d in enumerate(cal)}; matured=0; unavailable=0; changed=False
    for x in rows:
        if not x.get('production_eligible') or _outcome_mature(x): continue
        d=str(x.get('date') or ''); code=str(x.get('code') or '')
        if d not in pos or pos[d]+10>=len(cal): continue
        bars=histories.get(code) or []; bmap={str(b.get('date')):b for b in bars if b.get('date')}
        b0=bmap.get(d)
        if not b0 or b0.get('close') is None:
            unavailable+=1; continue
        ref=float(b0['close']); future=cal[pos[d]+1:pos[d]+11]; target5=future[4]
        # 第5个市场交易日若停牌，则使用截至该日最后可见收盘；绝不使用之后复牌价格回填。
        close5=ref
        for dd in cal[pos[d]+1:pos[d]+6]:
            b=bmap.get(dd)
            if b and b.get('close') is not None: close5=float(b['close'])
        highs=[ref]; lows=[ref]
        for dd in future:
            b=bmap.get(dd)
            if not b: continue
            if b.get('high') is not None: highs.append(float(b['high']))
            if b.get('low') is not None: lows.append(float(b['low']))
        if ref<=0:
            unavailable+=1; continue
        mfe=max(highs)/ref-1; mae=min(lows)/ref-1
        x['outcomes']={'ret_close_5':close5/ref-1,'hit10_10d':bool(mfe>=.10),'mfe_10':mfe,'mae_10':mae,'reference_close':ref,'matured_asof':asof_date,'horizon':'5/10个市场交易日'}
        matured+=1; changed=True
    if changed: path.write_text('\n'.join(json.dumps(x,ensure_ascii=False,default=str) for x in rows)+'\n','utf-8')
    pending=sum(1 for x in rows if x.get('production_eligible') and not _outcome_mature(x))
    return {'matured':matured,'pending':pending,'unavailable':unavailable}

def archive_realtime(results, trade_date:str, state_dir:Path, ts:Optional[str]=None):
    ts=ts or datetime.now().isoformat(timespec='minutes'); rows=[]
    for r in results:
        if r.model_labels: rows.append({'date':trade_date,'timestamp':ts,'code':r.code,'labels':r.model_labels})
    _append_jsonl(state_dir/'realtime_alerts.jsonl',rows); return len(rows)

def update_realtime_close_confirmation(state_dir:Path, trade_date:str, close_candidates:set[str]):
    p=state_dir/'realtime_alerts.jsonl'; rows=_read_jsonl(p); changed=False
    for x in rows:
        if x.get('date')==trade_date and 'close_confirmed' not in x:
            x['close_confirmed']=x.get('code') in close_candidates; changed=True
    if changed: p.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows)+'\n','utf-8')

def archive_industry_states(results, trade_date:str, state_dir:Path):
    """每日每行业只归档一次完整六维状态，供次日的扩散/资金变化和生命周期连续性使用。"""
    path=state_dir/'industry_archive.jsonl'; rows=[]; seen=set()
    existing={(x.get('date'),x.get('industry')) for x in _read_jsonl(path)}
    for r in results:
        m=getattr(r,'metrics',{}) or {}; ind=getattr(r,'industry',None)
        if not ind or not m.get('industry_complete') or (trade_date,ind) in existing or ind in seen: continue
        seen.add(ind); dims=m.get('industry_dimensions') or {}
        rows.append({'date':trade_date,'industry':ind,'score_100':m.get('industry_score'),'phase':m.get('industry_phase'),
                     'dimensions':dims,'breadth_up_ratio':m.get('industry_breadth_up_ratio'),'amount_share':m.get('industry_amount_share')})
    _append_jsonl(path,rows); return len(rows)


def load_industry_history(state_dir:Path, industry:str, limit:int=10)->List[dict]:
    rows=[x for x in _read_jsonl(state_dir/'industry_archive.jsonl') if x.get('industry')==industry]
    rows.sort(key=lambda x:x.get('date',''))
    return rows[-limit:]


def _source_match_rate(rows:List[dict])->float:
    bydate={}
    for x in rows:
        v=x.get('source_match')
        if v is None: continue
        try:
            fv=float(v)
            if math.isfinite(fv): bydate[x.get('date')]=max(0.0,min(1.0,fv))
        except Exception: pass
    return sum(bydate.values())/len(bydate) if bydate else 0.0

def _median(xs):
    xs=[x for x in xs if x is not None and math.isfinite(float(x))]
    return statistics.median(xs) if xs else None

def _outcome_mature(x: dict) -> bool:
    o=x.get('outcomes')
    if not isinstance(o,dict): return False
    return all(o.get(k) is not None for k in ('ret_close_5','hit10_10d','mfe_10','mae_10'))

def _baseline_hit(rows: List[dict], years: Optional[set[int]]=None) -> float:
    xs=[x for x in rows if x.get('kind')=='baseline' and _outcome_mature(x) and (years is None or int(x.get('year')) in years)]
    if not xs: return 0.0
    return sum(bool((x.get('outcomes') or {}).get('hit10_10d')) for x in xs)/len(xs)

def _metrics(rows, baseline_hit):
    n=len(rows)
    if not n: return {'n':0}
    r5=[x['outcomes'].get('ret_close_5') for x in rows if x.get('outcomes')]
    r5=[float(x) for x in r5 if x is not None]
    hit=[bool(x['outcomes'].get('hit10_10d')) for x in rows if x.get('outcomes') and x['outcomes'].get('hit10_10d') is not None]
    mfe=[float(x['outcomes'].get('mfe_10')) for x in rows if x.get('outcomes') and x['outcomes'].get('mfe_10') is not None]
    mae=[abs(float(x['outcomes'].get('mae_10'))) for x in rows if x.get('outcomes') and x['outcomes'].get('mae_10') is not None]
    years=defaultdict(list)
    for x in rows:
        o=x.get('outcomes') or {}; rr=o.get('ret_close_5')
        if rr is not None: years[x['year']].append(float(rr))
    profitable=sum(1 for ys in years.values() if _median(ys) is not None and _median(ys)>0)
    return {'n':n,'ret5_winrate':sum(v>0 for v in r5)/len(r5) if r5 else 0.0,'ret5_median':_median(r5),
        'hit10_rate':sum(hit)/len(hit) if hit else 0.0,'hit10_lift_vs_baseline':((sum(hit)/len(hit))/baseline_hit if hit and baseline_hit>0 else 0.0),
        'mfe_mae_ratio':((_median(mfe) or 0)/(_median(mae) or 1e-9)) if mfe and mae else 0.0,
        'profitable_year_fraction':profitable/len(years) if years else 0.0}

def _objective(m):
    # 没有真实样本时目标函数必须为0，禁止把默认中心值0.5误当成模型质量。
    if int(m.get('n',0) or 0) <= 0:
        return 0.0
    med=m.get('ret5_median')
    med=0.0 if med is None else float(med)
    return .35*min(m.get('hit10_lift_vs_baseline',0),2)/2 + .20*max(min(med*10+.5,1),0)+.20*m.get('ret5_winrate',0)+.15*min(m.get('mfe_mae_ratio',0),2)/2+.10*m.get('profitable_year_fraction',0)

def _select(rows, model, threshold, fire_window=3):
    out=[]
    for x in rows:
        if not x.get('bases',{}).get(model): continue
        if model=='黄金点火' and int(x.get('fire_age',99))>=fire_window: continue
        if float(x.get('scores',{}).get(model,0))>=threshold: out.append(x)
    return out

def validate_production(state_dir:Path, cfg:dict, dataset:Optional[str]=None):
    rows=_read_jsonl(Path(dataset)) if dataset else _read_jsonl(state_dir/'event_archive.jsonl')
    authorized=[x for x in rows if x.get('production_eligible')]
    eligible=[x for x in authorized if _outcome_mature(x)]
    baseline=[x for x in eligible if x.get('kind')=='baseline']
    baseline_hit=_baseline_hit(eligible)
    core=[x for x in eligible if x.get('kind')=='core']
    years=sorted({int(x['year']) for x in eligible})
    gates=[]
    def gate(name, ok, value, threshold): gates.append({'name':name,'pass':bool(ok),'value':value,'threshold':threshold})
    g=cfg['production_gates']; opt=cfg['optimization']; frozen={}; oos_all=[]; selected_history=defaultdict(list)
    holdout=max(years) if years else None; devyears=[y for y in years if y!=holdout]
    for testy in devyears:
        train=[y for y in devyears if testy-4<=y<=testy-2]; valy=testy-1
        if len(train)<2 or valy not in devyears: continue
        train_rows=[x for x in core if x['year'] in train]
        if len(train_rows)<int(opt.get('min_train_samples',0)): continue
        val=[x for x in core if x['year']==valy]; test=[x for x in core if x['year']==testy]
        val_baseline_hit=_baseline_hit(eligible,{valy})
        if len(val)<opt['min_validation_samples'] or not test: continue
        for model in MODELS:
            best=None
            windows=cfg['optimization']['fire_cross_window_grid'] if model=='黄金点火' else [3]
            for w in windows:
                for th in opt['score_grid']:
                    m=_metrics(_select(val,model,th,w),val_baseline_hit)
                    if m.get('n',0)<10: continue
                    cand=(_objective(m),th,w,m)
                    if best is None or cand[0]>best[0]: best=cand
            if best:
                _,th,w,_=best; selected_history[model].append((th,w)); sel=_select(test,model,th,w)
                for x in sel:
                    y=dict(x); y['model']=model; oos_all.append(y)
    for model in MODELS:
        hist=selected_history.get(model,[])
        if hist:
            th=Counter(a for a,b in hist).most_common(1)[0][0]; w=Counter(b for a,b in hist).most_common(1)[0][0]
        else:
            th=cfg['model'][KEY[model]+'_score_min']; w=cfg['model']['fire_cross_window']
        frozen[model]={'score_min':th,'fire_cross_window':w if model=='黄金点火' else None}
    dev_year_set=set(devyears)
    dev_baseline_hit=_baseline_hit(eligible,dev_year_set) if dev_year_set else 0.0
    model_oos={m:_metrics([x for x in oos_all if x.get('model')==m],dev_baseline_hit) for m in MODELS}
    hold=[x for x in core if holdout is not None and x['year']==holdout]
    hold_baseline_hit=_baseline_hit(eligible,{holdout}) if holdout is not None else 0.0
    hold_models={m:_metrics(_select(hold,m,frozen[m]['score_min'],frozen[m]['fire_cross_window'] or 3),hold_baseline_hit) for m in MODELS}
    total_hold=sum(v.get('n',0) for v in hold_models.values())
    gate('生产级PIT事件样本存在',len(eligible)>0,len(eligible),'>0')
    gate('滚动样本外总样本量',len(oos_all)>=g['min_oos_samples_total'],len(oos_all),g['min_oos_samples_total'])
    for m,mt in model_oos.items():
        gate(f'{m}:样本量',mt.get('n',0)>=g['min_oos_samples_per_model'],mt.get('n',0),g['min_oos_samples_per_model'])
        gate(f'{m}:5日胜率',mt.get('ret5_winrate',0)>=g['min_ret5_winrate'],mt.get('ret5_winrate'),g['min_ret5_winrate'])
        med5=mt.get('ret5_median'); gate(f'{m}:5日中位收益',med5 is not None and med5>=g['min_ret5_median'],med5,g['min_ret5_median'])
        gate(f'{m}:10日10%提升',mt.get('hit10_lift_vs_baseline',0)>=g['min_hit10_lift_vs_baseline'],mt.get('hit10_lift_vs_baseline'),g['min_hit10_lift_vs_baseline'])
        gate(f'{m}:MFE/MAE',mt.get('mfe_mae_ratio',0)>=g['min_mfe_mae_ratio'],mt.get('mfe_mae_ratio'),g['min_mfe_mae_ratio'])
        gate(f'{m}:年度一致性',mt.get('profitable_year_fraction',0)>=g['min_profitable_year_fraction'],mt.get('profitable_year_fraction'),g['min_profitable_year_fraction'])
    gate('最终封存样本总量',total_hold>=g['min_final_holdout_samples_total'],total_hold,g['min_final_holdout_samples_total'])
    for m,mt in hold_models.items():
        gate(f'封存:{m}:样本量',mt.get('n',0)>=g['min_final_holdout_samples_per_model'],mt.get('n',0),g['min_final_holdout_samples_per_model'])
        gate(f'封存:{m}:5日胜率',mt.get('ret5_winrate',0)>=g['min_final_holdout_ret5_winrate'],mt.get('ret5_winrate'),g['min_final_holdout_ret5_winrate'])
        med5=mt.get('ret5_median'); gate(f'封存:{m}:5日中位收益',med5 is not None and med5>=g['min_final_holdout_ret5_median'],med5,g['min_final_holdout_ret5_median'])
        gate(f'封存:{m}:10日10%提升',mt.get('hit10_lift_vs_baseline',0)>=g['min_final_holdout_hit10_lift'],mt.get('hit10_lift_vs_baseline'),g['min_final_holdout_hit10_lift'])
    # Resonance under frozen thresholds: labels are independent; no display-priority pollution.
    resonance=defaultdict(list)
    for x in core:
        labs=[m for m in MODELS if x.get('bases',{}).get(m) and float(x.get('scores',{}).get(m,0))>=frozen[m]['score_min'] and (m!='黄金点火' or int(x.get('fire_age',99))<frozen[m]['fire_cross_window'])]
        if labs and x.get('outcomes'): resonance['+'.join(labs)].append(x)
    resonance_report={k:_metrics(v,baseline_hit) for k,v in resonance.items()}
    # 参数邻域稳定性：冻结阈值附近的相邻参数不得让目标函数塌陷。
    neighbor_stability={}
    devcore=[x for x in core if holdout is None or x.get('year')!=holdout]
    for m in MODELS:
        base_th=frozen[m]['score_min']; base_w=frozen[m]['fire_cross_window'] or 3
        bm=_metrics(_select(devcore,m,base_th,base_w),dev_baseline_hit); bo=_objective(bm)
        min_neighbor_samples=max(10,int(opt.get('min_validation_samples',20))//2)
        candidates=[]
        grid=sorted(opt['score_grid'])
        if base_th in grid:
            i=grid.index(base_th)
            if i>0:candidates.append((grid[i-1],base_w,'score-'))
            if i+1<len(grid):candidates.append((grid[i+1],base_w,'score+'))
        if m=='黄金点火':
            wgrid=sorted(opt['fire_cross_window_grid'])
            if base_w in wgrid:
                j=wgrid.index(base_w)
                if j>0:candidates.append((base_th,wgrid[j-1],'window-'))
                if j+1<len(wgrid):candidates.append((base_th,wgrid[j+1],'window+'))
        ratios=[]; details=[]
        for th,w,label in candidates:
            mm=_metrics(_select(devcore,m,th,w),dev_baseline_hit); obj=_objective(mm)
            # 冻结点或邻域没有足够样本时不能伪造“稳定”。
            enough=(bm.get('n',0)>=min_neighbor_samples and mm.get('n',0)>=min_neighbor_samples)
            ratio=(obj/bo) if enough and bo>1e-12 else 0.0
            ratios.append(ratio); details.append({'neighbor':label,'score_min':th,'fire_cross_window':w,'objective_ratio_vs_frozen':ratio,'enough_samples':enough,'metrics':mm})
        stability=min(ratios) if ratios and bm.get('n',0)>=min_neighbor_samples else 0.0
        neighbor_stability[m]={'ratio':stability,'base_objective':bo,'details':details}
        gate(f'{m}:参数邻域稳定率',stability>=g['min_neighbor_stability_ratio'],stability,g['min_neighbor_stability_ratio'])
    # Factor ablation on frozen thresholds, using component point removal.
    ablation={}
    for m in MODELS:
        full=_select(devcore,m,frozen[m]['score_min'],frozen[m]['fire_cross_window'] or 3); fm=_metrics(full,dev_baseline_hit); block=[]
        components=sorted({c for x in core for c in (x.get('components',{}).get(m,{}) or {}).keys()})
        for comp in components:
            wo=[]
            for x in devcore:
                if not x.get('bases',{}).get(m): continue
                sc=float(x.get('scores',{}).get(m,0))-float((x.get('components',{}).get(m,{}) or {}).get(comp,0))
                if m=='黄金点火' and int(x.get('fire_age',99))>=frozen[m]['fire_cross_window']: continue
                if sc>=frozen[m]['score_min']: wo.append(x)
            wm=_metrics(wo,dev_baseline_hit); delta=_objective(fm)-_objective(wm)
            block.append({'component':comp,'delta_full_minus_without':delta,'full_n':fm.get('n',0),'without_n':wm.get('n',0)})
            gate(f'{m}:因子贡献:{comp}',delta>=g['min_component_contribution_delta'],delta,g['min_component_contribution_delta'])
        ablation[m]={'full':fm,'components':block}
    # Intraday stability from archived alerts.
    alerts=_read_jsonl(state_dir/'realtime_alerts.jsonl'); alert_groups=defaultdict(list)
    for a in alerts: alert_groups[(a.get('date'),a.get('code'))].append(a)
    first=[]; survive30=[]; closec=[]
    for key,arr in alert_groups.items():
        arr=sorted(arr,key=lambda x:x.get('timestamp','')); first.append(arr[0]);
        try: t0=datetime.fromisoformat(arr[0]['timestamp'])
        except Exception: t0=None
        ok30=False
        if t0:
            for a in arr[1:]:
                try:
                    if (datetime.fromisoformat(a['timestamp'])-t0).total_seconds()>=1800: ok30=True; break
                except Exception: pass
        survive30.append(ok30); closec.append(any(a.get('close_confirmed') is True for a in arr))
    intra={'alerts':len(first),'survive_30m':sum(survive30)/len(survive30) if survive30 else 0.0,'survive_close':sum(closec)/len(closec) if closec else 0.0}
    gate('盘中预警样本量',intra['alerts']>=g['min_intraday_alerts'],intra['alerts'],g['min_intraday_alerts'])
    gate('盘中30分钟存活率',intra['survive_30m']>=g['min_intraday_survive_30m'],intra['survive_30m'],g['min_intraday_survive_30m'])
    gate('盘中收盘确认率',intra['survive_close']>=g['min_intraday_survive_close'],intra['survive_close'],g['min_intraday_survive_close'])
    smr=_source_match_rate(authorized)
    gate('双源价格一致率',smr>=g['min_source_match_rate'],smr,g['min_source_match_rate'])
    passed=all(x['pass'] for x in gates)
    return {'status':'PRODUCTION_READY' if passed else 'NOT_READY','pass':passed,'eligible_events':len(eligible),'authorized_events':len(authorized),'immature_events':len(authorized)-len(eligible),'baseline_hit10':baseline_hit,'dev_baseline_hit10':dev_baseline_hit,'holdout_baseline_hit10':hold_baseline_hit,'holdout_year':holdout,'frozen_params':frozen,'oos_models':model_oos,'final_holdout':hold_models,'resonance':resonance_report,'neighbor_stability':neighbor_stability,'ablation':ablation,'intraday':intra,'source_match_rate':smr,'gates':gates}
