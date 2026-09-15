from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from statistics import mean
from typing import Any, Dict, List, Optional, Sequence, Tuple

from industry_engine import industry_metrics as industry_metrics_v63, industry_environment_state, industry_increment_bonus

EPS=1e-9
MODEL_ORDER=["平台主升","弱转强","龙回头","黄金点火"]

def _mean(xs): return float(mean(xs)) if xs else 0.0

def ema_series(values: Sequence[float], n:int)->List[float]:
    if not values: return []
    a=2.0/(n+1.0); out=[float(values[0])]
    for x in values[1:]: out.append(a*float(x)+(1-a)*out[-1])
    return out

def tdx_sma_series(values: Sequence[float], n:int, m:int=1)->List[float]:
    if not values: return []
    out=[float(values[0])]
    for x in values[1:]: out.append((m*float(x)+(n-m)*out[-1])/n)
    return out

def rolling_max(values,end,n):
    return max(values[max(0,end-n+1):end+1])

def rolling_min(values,end,n):
    return min(values[max(0,end-n+1):end+1])

def ma_at(values,end,n):
    return _mean(values[max(0,end-n+1):end+1])

def limit_up_price(reference_close:float, ratio:float=.10)->float:
    q=Decimal(str(reference_close))*(Decimal('1')+Decimal(str(ratio)))
    return float(q.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def is_mainboard(code:str)->bool:
    return code.startswith(("600","601","603","605","000","001","002","003"))

def exchange_of(code:str)->str: return 'SH' if code.startswith('6') else 'SZ'

def board_series(bars):
    out=[]
    for i,b in enumerate(bars):
        if i==0: out.append(False); continue
        c=float(b['close']); h=float(b['high']); ch=b.get('change')
        ref=c-float(ch) if ch is not None else float(bars[i-1]['close'])
        if ref<=0: ref=float(bars[i-1]['close'])
        z=limit_up_price(ref,.10)
        out.append(c>=z-.005 and abs(c-h)<=.005)
    return out

def market_state(breadth,index_bars):
    if len(index_bars)<21: raise ValueError('指数历史不足21根')
    c=[float(x['close']) for x in index_bars]; t=len(c)-1
    r=c[t]/c[t-1]-1 if c[t-1] else 0
    score=int(c[t]>ma_at(c,t,20))+int(ma_at(c,t,5)>=ma_at(c,t,10))+int(r>=-.01)
    if breadth>=.55 and score>=2: return '强市',3,score,r
    if breadth>=.35 and score>=2: return '常市',2,score,r
    if .20<=breadth<.35 and score>=1: return '弱市',1,score,r
    return '极弱市',0,score,r

def industry_metrics(industry_data,index_bars,params:Optional[Dict[str,Any]]=None):
    return industry_metrics_v63(industry_data,index_bars,params)

def _fib_context(highs,lows,t,close):
    pressures=[]; supports=[]
    for n in (60,120,250):
        if t<n: continue
        hi=rolling_max(highs,t-1,n); lo=rolling_min(lows,t-1,n); width=max(.01,hi-lo)
        levels=[lo+width*x for x in (.236,.382,.5,.618,.786)]
        pressures += [x for x in levels+[hi] if x>close]
        supports += [x for x in [lo]+levels if 0<x<close]
    p=min(pressures) if pressures else None
    s=max(supports) if supports else None
    return {
        'pressure':p,'support':s,'no_pressure':p is None,
        'pressure_space':(p/close-1) if p else None,
        'support_valid':s is not None,'support_distance':(close/s-1) if s else None,
    }

@dataclass
class EvalResult:
    code:str; name:str; trade_date:str; market_state:str; market_level:int; industry:Optional[str]
    industry_valid:bool; model_labels:List[str]; model_scores:Dict[str,float]; primary_model:Optional[str]
    resonance_count:int; authorized_candidate:bool; needs_industry:bool; core_base_hit:bool
    reject_reasons:List[str]=field(default_factory=list); metrics:Dict[str,Any]=field(default_factory=dict)
    bases:Dict[str,bool]=field(default_factory=dict); components:Dict[str,Dict[str,float]]=field(default_factory=dict)
    model_states:Dict[str,Dict[str,Any]]=field(default_factory=dict)


def evaluate_stock(stock:Dict[str,Any], breadth:float, index_bars, industry_bars=None, params:Optional[Dict[str,Any]]=None)->EvalResult:
    p={'platform_score_min':10,'weak_score_min':10,'comeback_score_min':10,'fire_score_min':10,'fire_cross_window':3,'platform_volume_ratio':.95,'pressure_space_good':.08,'support_near':.08}
    if params: p.update(params)
    code=str(stock['code']); name=str(stock.get('name') or code); industry=stock.get('industry'); bars=list(stock.get('bars') or [])
    min_bars=int(p.get('native_min_history_bars',120))
    if len(bars)<min_bars:
        return EvalResult(code,name,bars[-1]['date'] if bars else '','未知',-1,industry,False,[],{},None,0,False,False,False,[f'历史数据不足{min_bars}根'],{'history_count':len(bars),'history_tier':'INSUFFICIENT'}, {}, {})
    t=len(bars)-1; trade_date=str(bars[t]['date'])
    o=[float(x['open']) for x in bars]; c=[float(x['close']) for x in bars]; h=[float(x['high']) for x in bars]; l=[float(x['low']) for x in bars]
    v=[float(x.get('volume',0) or 0) for x in bars]; a=[float(x.get('amount',0) or 0) for x in bars]; turnp=[float(x.get('turnover',0) or 0) for x in bars]
    try: mstate,mlevel,mscore,idxret=market_state(breadth,index_bars)
    except Exception as e:
        return EvalResult(code,name,trade_date,'未知',-1,industry,False,[],{},None,0,False,False,False,[f'市场指数数据不足:{e}'],{}, {}, {})
    ind=industry_metrics(industry_bars,index_bars,p)
    nonst='ST' not in name.upper() and '退' not in name
    pool=is_mainboard(code) and nonst and len(bars)>120 and ma_at(a,t-1,20)>=50_000_000 and a[t]>=100_000_000
    bs=board_series(bars); sealed=bs[t]; first_board=sealed and not any(bs[max(0,t-20):t]) and h[t]>l[t]+EPS
    e3=ema_series(c,3); e5=ema_series(c,5); e8=ema_series(c,8); e10=ema_series(c,10); e20=ema_series(c,20); e21=ema_series(c,21); e89=ema_series(c,89); mt=ema_series(ema_series(c,10),10); eh8=ema_series(h,8)
    # 昨日以前背景，避免当前大阳线自我确认。
    y=t-1
    trend_y=int(c[y]>e20[y])+int(e5[y]>e10[y])+int(e10[y]>e20[y])+int(e20[y]>=e20[t-6])+int(c[y]>e89[y])
    mt_up_y=mt[y]>=mt[t-2]; trend_strong_y=trend_y>=4 and mt_up_y; trend_repair_y=trend_y>=2 and e20[y]>=e20[t-6]*.98
    prev_low20=rolling_min(l,t-1,20); pos_y=c[t-1]/prev_low20 if prev_low20>0 else 1; pos_ok_y=pos_y<=1.28 and c[t-1]/e20[t-1]<=1.18
    eu=[max(x,y) for x,y in zip(o,c)]; el=[min(x,y) for x,y in zip(o,c)]
    overlap=rolling_max(el,t-1,4)<=rolling_min(eu,t-1,4); pr8=rolling_max(h,t-1,8)/max(rolling_min(l,t-1,8),EPS); pr15=rolling_max(h,t-1,15)/max(rolling_min(l,t-1,15),EPS)
    recent5=ma_at(v,t-1,5); earlier15=_mean(v[t-20:t-5]); shrink=earlier15>0 and recent5<=earlier15*p['platform_volume_ratio']
    platform_points=sum(map(int,(overlap,pr8<=1.12,pr15<=1.20,shrink))); platform_ok=platform_points>=3
    break20=c[t]>rolling_max(h,t-1,20); break10=c[t]>rolling_max(h,t-1,10); break5=c[t]>rolling_max(h,t-1,5); break3=c[t]>rolling_max(h,t-1,3)
    # Momentum and control.
    rsv=[]
    for i in range(len(bars)):
        hh=rolling_max(h,i,9); ll=rolling_min(l,i,9); rsv.append((c[i]-ll)/(hh-ll)*100 if hh>ll else 50)
    k=tdx_sma_series(rsv,3,1); d=tdx_sma_series(k,3,1); j=[3*x-2*y for x,y in zip(k,d)]; momentum=k[t]>d[t] and j[t]>k[t] and k[t]>=k[t-1]
    dealer=ema_series(ema_series(c,13),13); ctrl=[0.0]
    for i in range(1,len(dealer)): ctrl.append((dealer[i]/dealer[i-1]-1)*1000 if dealer[i-1] else 0)
    control_up=ctrl[t]>0 and ctrl[t]>ctrl[t-1]
    weak=[False]
    for i in range(1,len(bars)): weak.append(eh8[i]<eh8[i-1] or (e8[i]<e8[i-1] and c[i]<e8[i]))
    weak_prev3=len(weak[t-3:t])==3 and all(weak[t-3:t])
    absd=[0.0]; posd=[0.0]
    for i in range(1,len(c)):
        dd=c[i]-c[i-1]; absd.append(abs(dd)); posd.append(max(dd,0))
    den=tdx_sma_series(absd,2,1); num=tdx_sma_series(posd,2,1); rsi=[(nn/dd*100 if dd>EPS else 50) for nn,dd in zip(num,den)]; oversold_y=rsi[t-1]<20
    ref=c[t]-float(bars[t].get('change',c[t]-c[t-1]) or 0); ref=ref if ref>0 else c[t-1]
    pct=(c[t]/ref-1) if ref else 0; volratio=ma_at(v,t,2)/max(ma_at(v,t,10),EPS); turnover=turnp[t]/100; volstart=v[t]/max(ma_at(v,t-1,5),EPS)
    amp=(h[t]-l[t])/ref if ref else 0; closepos=(c[t]-l[t])/(h[t]-l[t]) if h[t]>l[t] else .5; lock=pct*100>5.3925+1.1864*volratio+61.3858*turnover
    strongk=c[t]>o[t] and closepos>=.75 and amp<=.12; volume_ok=.90<=volstart<=4 and .005<=turnover<=.18 and a[t]>=ma_at(a,t,5)
    fib=_fib_context(h,l,t,c[t]); pressure_good=fib['no_pressure'] or (fib['pressure_space'] is not None and fib['pressure_space']>=p['pressure_space_good']); support_near=fib['support_valid'] and fib['support_distance']<=p['support_near']
    # V6.3行业层：六维100分 + 生命周期 + 消息时效。行业数据未闭合不再中性放行。
    platform_env_state=industry_environment_state('平台主升',mlevel,ind,lock)
    platform_env=platform_env_state is True
    industry_points=industry_increment_bonus(mlevel,ind)
    platform_core=pool and first_board and trend_strong_y and pos_ok_y and platform_ok and break20 and strongk and volume_ok and h[t]/e5[t]<=1.16
    platform_base=platform_core and platform_env
    pc={'行业超额强度':industry_points,'锁筹':5 if (lock and mlevel!=0) else 0,'压力空间':5 if pressure_good else 0,'动量':3 if momentum else 0,'控盘':2 if control_up else 0,'换手甜蜜区':3 if .01<=turnover<=.08 else 0}
    ps=sum(pc.values()); sig_platform=platform_base and ps>=p['platform_score_min']
    weak_env_state=industry_environment_state('弱转强',mlevel,ind,lock); weak_env=weak_env_state is True
    weak_core=pool and first_board and trend_repair_y and (weak_prev3 or oversold_y) and break10 and c[t]>e20[t] and strongk and volume_ok and h[t]/e5[t]<=1.16
    weak_base=weak_core and weak_env
    wc={'弱势+超卖双确认':5 if weak_prev3 and oversold_y else 0,'行业超额强度':industry_points,'锁筹':5 if lock else 0,'压力空间':4 if pressure_good else 0,'动量':3 if momentum else 0,'控盘':2 if control_up else 0}
    ws=sum(wc.values()); sig_weak=weak_base and ws>=p['weak_score_min']
    # Dragon pullback excludes current day to remove lookahead/self-confirmation.
    prevdist=None
    for dist in range(2,14):
        if t-dist>=0 and bs[t-dist]: prevdist=dist; break
    if prevdist:
        bp=c[t-prevdist]; prior_lows=l[t-prevdist+1:t]; pb=(min(prior_lows)/bp-1) if prior_lows else None
    else: bp=0; pb=None
    validpb=pb is not None and -.18<=pb<=-.04
    comeback_trigger=c[t]>o[t] and break3 and c[t]>e10[t] and e10[t]>=e20[t] and mt[t]>=mt[t-1] and v[t]>=v[t-1]*1.05 and v[t]<=ma_at(v,t,5)*1.8 and c[t]/e20[t]<=1.12
    comeback_env_state=industry_environment_state('龙回头',mlevel,ind,lock); comeback_env=comeback_env_state is True
    comeback_core=pool and not sealed and validpb and comeback_trigger
    comeback_base=comeback_core and comeback_env
    cc={'健康回撤':5 if pb is not None and .06<=abs(pb)<=.12 else 0,'行业超额强度':industry_points,'支撑邻近':4 if support_near else 0,'压力空间':4 if pressure_good else 0,'动量':3 if momentum else 0,'控盘':2 if control_up else 0}
    cs=sum(cc.values()); sig_comeback=comeback_base and cs>=p['comeback_score_min']
    # Golden fire: recent-cross state machine, not only current-day CROSS.
    crosses=[False]*len(c)
    for i in range(1,len(c)): crosses[i]=e3[i]>e21[i] and e3[i-1]<=e21[i-1]
    lastcross=None
    for age in range(0,p['fire_cross_window']):
        if t-age>=0 and crosses[t-age]: lastcross=age; break
    firegap=e3[t]/e21[t]-1 if e21[t] else 0; prevgap=e3[t-1]/e21[t-1]-1 if e21[t-1] else 0
    fire_fresh=lastcross is not None and e3[t]>e21[t] and firegap>prevgap
    fire_compress=pr8<=1.12 and (pr8<=1.08 or shrink)
    fire_bg=c[t-1]>e20[t-1] and e5[t-1]>=e10[t-1] and e21[t-1]>=e21[t-4]*.997 and e20[t-1]>=e20[t-4]*.995 and mt_up_y
    fire_k=c[t]>o[t] and closepos>=.75 and .015<=pct<=.065 and amp<=.10
    fire_vol=1.15<=volstart<=2.8 and .008<=turnover<=.15
    fire_early=c[t]/e21[t]<=1.06 and c[t]/e20[t]<=1.10 and pos_y<=1.22
    fire_no_exhaust=not any(bs[max(0,t-10):t]) and not sealed
    fire_env_state=industry_environment_state('黄金点火',mlevel,ind,lock); fire_env=fire_env_state is True
    fire_core=pool and fire_compress and fire_bg and break5 and fire_k and fire_vol and fire_early and fire_no_exhaust and e3[t]>e21[t] and firegap>prevgap
    fire_base_core=fire_core and fire_env
    fire_base=fire_base_core and fire_fresh
    fc={'金叉新鲜':3 if lastcross is not None and 1<=lastcross<p['fire_cross_window'] else 0,'均线差扩大':4 if firegap>=.005 else 0,'行业超额强度':industry_points,'支撑邻近':3 if support_near else 0,'压力空间':5 if pressure_good else 0,'动量':3 if momentum else 0,'控盘':2 if control_up else 0}
    fs=sum(fc.values()); sig_fire=fire_base and fs>=p['fire_score_min']
    labels=[]; scores={}
    for nm,ok,sc in [('平台主升',sig_platform,ps),('弱转强',sig_weak,ws),('龙回头',sig_comeback,cs),('黄金点火',sig_fire,fs)]:
        if ok: labels.append(nm); scores[nm]=float(sc)
    primary=next((m for m in MODEL_ORDER if m in labels),None)  # display only; labels remain independent.
    needs_ind=False
    env_states={'平台主升':platform_env_state,'弱转强':weak_env_state,'龙回头':comeback_env_state,'黄金点火':fire_env_state}
    core_states={'平台主升':platform_core,'弱转强':weak_core,'龙回头':comeback_core,'黄金点火':fire_core}
    if any(core_states[m] and env_states[m] is None for m in MODEL_ORDER): needs_ind=True
    reasons=[]
    if not pool:
        if not is_mainboard(code): reasons.append('非沪深主板')
        if not nonst: reasons.append('ST/退市风险名称')
        if len(bars)<=120: reasons.append('上市不足120日')
        if not (ma_at(a,t-1,20)>=50_000_000 and a[t]>=100_000_000): reasons.append('流动性不足')
    elif not any((platform_core,weak_core,comeback_core,fire_core)):
        if sealed and not first_board: reasons.append('非20日首板')
        if not trend_strong_y and not trend_repair_y: reasons.append('昨日背景趋势不足')
        if not reasons: reasons.append('四模型核心结构均未触发')
    elif not labels:
        reasons.append('需要行业数据完成硬门判定' if needs_ind else '增量评分/环境门槛未通过')
    history_tier='ENHANCED_250' if len(bars)>=250 else 'CORE_120'
    metrics={
        'history_count':len(bars),'history_tier':history_tier,'close':c[t],'market_breadth':breadth,'market_score':mscore,'index_return':idxret,'industry_score':ind.get('score_100',0),'industry_return':ind.get('return'),'industry_excess':ind.get('excess'),'industry_phase':ind.get('phase'),'industry_tier':ind.get('tier'),'industry_coverage':ind.get('coverage',0),'industry_complete':ind.get('complete',False),'industry_dimensions':ind.get('dimensions',{}),'industry_overheat_penalty':ind.get('overheat_penalty',0),'industry_event_risk_penalty':ind.get('event_risk_penalty',0),'industry_events':ind.get('events',[]),'industry_increment_points':industry_points,'industry_breadth_up_ratio':(ind.get('breadth') or {}).get('up_ratio'),'industry_amount_share':(ind.get('funds') or {}).get('amount_share'),

        'trend_score_y':trend_y,'platform_score':platform_points,'lock_model':lock,'volume_ratio_2_10':volratio,'turnover_fraction':turnover,'vol_start':volstart,
        'pressure_space':fib['pressure_space'],'support_distance':fib['support_distance'],'no_pressure':fib['no_pressure'],'support_valid':fib['support_valid'],'first_board':first_board,'sealed':sealed,
        'fire_age':lastcross if lastcross is not None else 99,'fire_gap':firegap,'weak_prev3':weak_prev3,'oversold_y':oversold_y,'pullback_prev':pb,
        'pool':pool
    }
    bases={'平台主升':platform_base,'弱转强':weak_base,'龙回头':comeback_base,'黄金点火':fire_base_core}
    comps={'平台主升':pc,'弱转强':wc,'龙回头':cc,'黄金点火':fc}
    allscores={'平台主升':float(ps),'弱转强':float(ws),'龙回头':float(cs),'黄金点火':float(fs)}
    thresholds={'平台主升':float(p['platform_score_min']),'弱转强':float(p['weak_score_min']),'龙回头':float(p['comeback_score_min']),'黄金点火':float(p['fire_score_min'])}
    model_states={}
    for model in MODEL_ORDER:
        core=bool(core_states[model]); environment=env_states[model]; score=allscores[model]
        score_pass=score>=thresholds[model]
        if model in labels:
            status='TRIGGERED'
        elif not core:
            status='CORE_NOT_TRIGGERED'
        elif environment is None:
            status='UNKNOWN_ENVIRONMENT'
        elif environment is False:
            status='ENVIRONMENT_REJECTED'
        elif not score_pass:
            status='SCORE_NOT_REACHED'
        else:
            status='NOT_TRIGGERED'
        model_states[model]={
            'status':status,
            'core':core,
            'environment':environment,
            'score':score,
            'threshold':thresholds[model],
            'score_pass':score_pass,
            'base':bool(bases[model]),
            'triggered':model in labels,
        }
    core_hit=any((platform_core,weak_core,comeback_core,fire_core))
    return EvalResult(code,name,trade_date,mstate,mlevel,industry,bool(ind['valid']),labels,allscores,primary,len(labels),bool(labels) and not needs_ind,needs_ind,core_hit,reasons,metrics,bases,comps,model_states)

def summarize(results):
    counts={m:0 for m in MODEL_ORDER}; resonance={str(i):0 for i in range(1,5)}; cands=[]; rej={}
    for r in results:
        for m in r.model_labels: counts[m]+=1
        if r.model_labels:
            resonance[str(r.resonance_count)]=resonance.get(str(r.resonance_count),0)+1; cands.append(r)
        for x in r.reject_reasons[:1]: rej[x]=rej.get(x,0)+1
    cands.sort(key=lambda r:(-r.resonance_count,-max(r.model_scores.get(m,0) for m in r.model_labels),r.code))
    return {'model_counts':counts,'resonance_counts':resonance,'candidate_count':len(cands),'candidates':cands,'reject_counts':dict(sorted(rej.items(),key=lambda kv:(-kv[1],kv[0]))),'needs_industry_count':sum(r.needs_industry for r in results)}

# ==================== V6.3 盘中实时三态引擎 ====================
# 设计原则：关键实时字段缺失时，只有在“其余结构已经足以成为潜在候选”时才传播 UNKNOWN；
# 如果价格/趋势/突破等基本结构本身就不成立，则正常 FAIL，不用缺失数据制造无意义阻断。

REALTIME_PASS='PASS'
REALTIME_FAIL='FAIL'
REALTIME_UNKNOWN='UNKNOWN'

@dataclass
class RealtimeEvalResult:
    code:str
    name:str
    trade_date:str
    state:str
    model_labels:List[str]=field(default_factory=list)
    potential_models:List[str]=field(default_factory=list)
    model_scores:Dict[str,float]=field(default_factory=dict)
    primary_model:Optional[str]=None
    resonance_count:int=0
    unknown_fields:List[str]=field(default_factory=list)
    needs_industry:bool=False
    reject_reasons:List[str]=field(default_factory=list)
    metrics:Dict[str,Any]=field(default_factory=dict)
    bases:Dict[str,bool]=field(default_factory=dict)
    components:Dict[str,Dict[str,float]]=field(default_factory=dict)


def _num_or_none(v):
    if v is None or isinstance(v,bool):
        return None
    if isinstance(v,str):
        s=v.strip()
        if s in ('','-','--','None','null','nan','NaN'):
            return None
        v=s
    try:
        x=float(v)
        if x!=x or x in (float('inf'),float('-inf')):
            return None
        return x
    except Exception:
        return None


def _realtime_env_state(model:str, mlevel:int, ind:Dict[str,Any], lock:bool=False)->str:
    """V6.3行业门三态：行业六维未闭合=>UNKNOWN，不再把缺失当中性通过。"""
    # 极弱市盘中先判断行业资格，实时锁筹在关键字段闭合后由model_ok再次硬检。
    z=industry_environment_state(model,mlevel,ind,True if (mlevel==0 and model=='平台主升') else lock)
    if z is None: return REALTIME_UNKNOWN
    return REALTIME_PASS if z else REALTIME_FAIL

def evaluate_realtime_stock(stock:Dict[str,Any], breadth:float, index_bars, industry_bars=None, params:Optional[Dict[str,Any]]=None)->RealtimeEvalResult:
    """V6.3独立盘中实时引擎。

    `stock['bars']` 最后一根必须是由当前公开快照构造的当日未完成日线；
    `stock['snapshot']` 保存真正的即时字段。函数不把缺失实时量比默认为0/失败。
    """
    p={'platform_score_min':10,'weak_score_min':10,'comeback_score_min':10,'fire_score_min':10,'fire_cross_window':3,'platform_volume_ratio':.95,'pressure_space_good':.08,'support_near':.08,
       'realtime_common_volume_ratio_min':1.05,'realtime_common_volume_ratio_max':3.50,'realtime_common_turnover_min':.003,'realtime_common_turnover_max':.18,'realtime_amount_min':30_000_000,
       'realtime_fire_volume_ratio_min':1.15,'realtime_fire_volume_ratio_max':2.80,'realtime_fire_turnover_min':.005,'realtime_fire_turnover_max':.15,
       'realtime_break_current_buffer':.003,'realtime_break_stable_buffer':.001}
    if params: p.update(params)
    code=str(stock['code']); name=str(stock.get('name') or code); industry=stock.get('industry')
    bars=list(stock.get('bars') or []); snap=dict(stock.get('snapshot') or {})
    trade_date=str(snap.get('date') or (bars[-1].get('date') if bars else ''))
    min_bars=int(p.get('native_min_history_bars',120))
    if len(bars)<min_bars:
        return RealtimeEvalResult(code,name,trade_date,REALTIME_FAIL,reject_reasons=[f'历史数据不足{min_bars}根'])
    t=len(bars)-1; y=t-1
    try: mstate,mlevel,mscore,idxret=market_state(breadth,index_bars)
    except Exception as e:
        return RealtimeEvalResult(code,name,trade_date,REALTIME_UNKNOWN,unknown_fields=['市场指数'],reject_reasons=[f'市场指数数据不足:{e}'])
    ind=industry_metrics(industry_bars,index_bars,p)

    # 实时字段只认当前快照，不从缓存日K静默补空。
    last=_num_or_none(snap.get('last')); op=_num_or_none(snap.get('open')); hi=_num_or_none(snap.get('high')); lo=_num_or_none(snap.get('low'))
    amount=_num_or_none(snap.get('amount')); turnover_pct=_num_or_none(snap.get('turnover')); volume_ratio=_num_or_none(snap.get('volume_ratio'))
    pct_live=_num_or_none(snap.get('pct')); stable_price=_num_or_none(snap.get('stable_price'))

    # 背景可以先算；如果当前价格四要素缺失且背景具备潜力，后面会传播UNKNOWN。
    c=[float(x['close']) for x in bars]; h=[float(x['high']) for x in bars]; l=[float(x['low']) for x in bars]; o=[float(x['open']) for x in bars]
    v=[float(x.get('volume',0) or 0) for x in bars]; a=[float(x.get('amount',0) or 0) for x in bars]
    e3=ema_series(c,3); e5=ema_series(c,5); e8=ema_series(c,8); e10=ema_series(c,10); e20=ema_series(c,20); e21=ema_series(c,21); e89=ema_series(c,89); mt=ema_series(ema_series(c,10),10); eh8=ema_series(h,8)
    trend_y=int(c[y]>e20[y])+int(e5[y]>e10[y])+int(e10[y]>e20[y])+int(e20[y]>=e20[t-6])+int(c[y]>e89[y])
    mt_up_y=mt[y]>=mt[t-2]; trend_strong_y=trend_y>=4 and mt_up_y; trend_repair_y=trend_y>=2 and e20[y]>=e20[t-6]*.98
    prev_low20=rolling_min(l,y,20); pos_y=c[y]/prev_low20 if prev_low20>0 else 1; pos_ok_y=pos_y<=1.28 and c[y]/e20[y]<=1.18
    eu=[max(x,z) for x,z in zip(o,c)]; el=[min(x,z) for x,z in zip(o,c)]
    overlap=rolling_max(el,y,4)<=rolling_min(eu,y,4); pr8=rolling_max(h,y,8)/max(rolling_min(l,y,8),EPS); pr15=rolling_max(h,y,15)/max(rolling_min(l,y,15),EPS)
    recent5=ma_at(v,y,5); earlier15=_mean(v[t-20:t-5]); shrink=earlier15>0 and recent5<=earlier15*p['platform_volume_ratio']
    platform_points=sum(map(int,(overlap,pr8<=1.12,pr15<=1.20,shrink))); platform_ok=platform_points>=3
    absd=[0.0]; posd=[0.0]
    for i in range(1,len(c)):
        dd=c[i]-c[i-1]; absd.append(abs(dd)); posd.append(max(dd,0))
    den=tdx_sma_series(absd,2,1); num=tdx_sma_series(posd,2,1); rsi=[(nn/dd*100 if dd>EPS else 50) for nn,dd in zip(num,den)]
    weak=[False]
    for i in range(1,len(bars)): weak.append(eh8[i]<eh8[i-1] or (e8[i]<e8[i-1] and c[i]<e8[i]))
    weak_prev3=len(weak[t-3:t])==3 and all(weak[t-3:t]); oversold_y=rsi[y]<20
    nonst='ST' not in name.upper() and '退' not in name
    pool=is_mainboard(code) and nonst and len(bars)>120 and ma_at(a,y,20)>=50_000_000
    bs=board_series(bars[:t])  # 只到昨日，当前未完成K线不得反向污染历史封板序列。
    prevdist=None
    for dist in range(1,14):
        i=y-dist+1
        if i>=0 and i<len(bs) and bs[i]: prevdist=t-i; break
    if prevdist:
        bi=t-prevdist; bp=c[bi]; prior_lows=l[bi+1:t]; pb=(min(prior_lows)/bp-1) if prior_lows else None
    else: bp=0; pb=None
    validpb=pb is not None and -.18<=pb<=-.04

    # 背景级潜力：用来决定“当前字段缺失”是否可能改变候选，不以缺字段直接判失败。
    background_possible={
        '平台主升': pool and trend_strong_y and pos_ok_y and platform_ok,
        '弱转强': pool and trend_repair_y and (weak_prev3 or oversold_y),
        '龙回头': pool and validpb,
        '黄金点火': pool and (pr8<=1.12 and (pr8<=1.08 or shrink)) and c[y]>e20[y] and e5[y]>=e10[y] and e21[y]>=e21[t-4]*.997 and e20[y]>=e20[t-4]*.995 and mt_up_y,
    }
    if not any(background_possible.values()):
        reason='股票池/昨日背景结构不成立'
        return RealtimeEvalResult(code,name,trade_date,REALTIME_FAIL,reject_reasons=[reason],metrics={'market_state':mstate,'market_level':mlevel,'industry_valid':ind.get('valid',False),'industry_complete':ind.get('complete',False),'industry_score':ind.get('score_100',0),'industry_phase':ind.get('phase'),'industry_coverage':ind.get('coverage',0),'background_possible':background_possible,'pool':pool})

    missing_price=[k for k,val in [('实时现价',last),('实时开盘',op),('实时最高',hi),('实时最低',lo)] if val is None]
    if missing_price:
        return RealtimeEvalResult(code,name,trade_date,REALTIME_UNKNOWN,potential_models=[m for m,x in background_possible.items() if x],unknown_fields=missing_price,reject_reasons=['背景结构具备潜力但关键实时价格字段缺失'],metrics={'market_state':mstate,'market_level':mlevel,'industry_valid':ind.get('valid',False),'industry_complete':ind.get('complete',False),'industry_score':ind.get('score_100',0),'industry_phase':ind.get('phase'),'industry_coverage':ind.get('coverage',0),'background_possible':background_possible,'pool':pool})

    # 以快照重算当前K线相关状态。
    if pct_live is None:
        pre=c[y]
        pct_live=(last/pre-1)*100 if pre else None
    amp=(hi-lo)/c[y] if c[y] else None
    closepos=(last-lo)/(hi-lo) if hi>lo else .5
    strongk=last>op and closepos>=.70 and amp is not None and amp<=.10
    prevh20=rolling_max(h,y,20); prevh10=rolling_max(h,y,10); prevh5=rolling_max(h,y,5); prevh3=rolling_max(h,y,3)
    now_break={'平台主升':last>=prevh20*(1+p['realtime_break_current_buffer']),'弱转强':last>=prevh10*(1+p['realtime_break_current_buffer']),'龙回头':last>=prevh3*(1+p['realtime_break_current_buffer']),'黄金点火':last>=prevh5*(1+p['realtime_break_current_buffer'])}

    # 盘中EMA按当前快照收盘近似最后一根，build_realtime_bars已保证c[t]=last。
    # 通用的“除量比/数分前价外”结构。只有走到这里才有资格触发UNKNOWN传播。
    structural={
        '平台主升': background_possible['平台主升'] and now_break['平台主升'] and strongk and pct_live is not None and 3.50<=pct_live<=10.10,
        '弱转强': background_possible['弱转强'] and now_break['弱转强'] and last>e20[t] and strongk and pct_live is not None and 3.00<=pct_live<=10.10,
        '龙回头': background_possible['龙回头'] and now_break['龙回头'] and last>op and last>e10[t] and e10[t]>=e20[t] and pct_live is not None and 1.50<=pct_live<=8.00,
        '黄金点火': False,
    }
    crosses=[False]*len(c)
    for i in range(1,len(c)): crosses[i]=e3[i]>e21[i] and e3[i-1]<=e21[i-1]
    firegap=e3[t]/e21[t]-1 if e21[t] else 0; prevgap=e3[y]/e21[y]-1 if e21[y] else 0
    firefresh=any(crosses[max(1,t-p['fire_cross_window']+1):t+1]) and e3[t]>e21[t] and firegap>prevgap
    fire_early=last/e21[t]<=1.06 and last/e20[t]<=1.10 and pos_y<=1.22
    structural['黄金点火']=background_possible['黄金点火'] and firefresh and now_break['黄金点火'] and last>op and closepos>=.75 and pct_live is not None and 1.50<=pct_live<=6.50 and amp is not None and amp<=.10 and fire_early

    # 环境先做三态。环境明确FAIL的结构不是“未知”；环境未知则只有结构已到位才传播。
    env={m:_realtime_env_state(m,mlevel,ind) for m in MODEL_ORDER}
    potential=[m for m in MODEL_ORDER if structural.get(m) and env[m]!=REALTIME_FAIL]
    if not potential:
        return RealtimeEvalResult(code,name,trade_date,REALTIME_FAIL,reject_reasons=['实时价格/趋势/突破或市场环境未形成潜在候选'],metrics={'market_state':mstate,'market_level':mlevel,'industry_valid':ind.get('valid',False),'industry_complete':ind.get('complete',False),'industry_score':ind.get('score_100',0),'industry_phase':ind.get('phase'),'industry_coverage':ind.get('coverage',0),'structural':structural,'environment_state':env,'pool':pool,'pct_live':pct_live})

    unknown=[]; needs_ind=any(env[m]==REALTIME_UNKNOWN for m in potential)
    if needs_ind: unknown.append('行业强度/超额')
    # 稳定突破必须用数分钟前价格；不允许拿当前现价代替。
    if stable_price is None: unknown.append('数分钟前价格')
    # 实时量比是硬输入：存在才计算；潜在候选缺失=>UNKNOWN=>BLOCKED。
    if volume_ratio is None: unknown.append('实时量比')
    if turnover_pct is None: unknown.append('实时换手')
    if amount is None: unknown.append('实时成交额')
    if unknown:
        return RealtimeEvalResult(code,name,trade_date,REALTIME_UNKNOWN,potential_models=potential,unknown_fields=sorted(set(unknown)),needs_industry=needs_ind,reject_reasons=['关键实时字段缺失，未知≠不通过'],metrics={'market_state':mstate,'market_level':mlevel,'industry_valid':ind.get('valid',False),'industry_complete':ind.get('complete',False),'industry_score':ind.get('score_100',0),'industry_phase':ind.get('phase'),'industry_coverage':ind.get('coverage',0),'structural':structural,'environment_state':env,'pool':pool,'pct_live':pct_live,'realtime_volume_ratio':volume_ratio})

    turnover=turnover_pct/100.0
    realtime_liq=amount>=p['realtime_amount_min']
    common_vol=p['realtime_common_volume_ratio_min']<=volume_ratio<=p['realtime_common_volume_ratio_max'] and p['realtime_common_turnover_min']<=turnover<=p['realtime_common_turnover_max'] and realtime_liq
    sb=1+p['realtime_break_stable_buffer']
    stable={'平台主升':stable_price>=prevh20*sb,'弱转强':stable_price>=prevh10*sb,'龙回头':stable_price>=prevh3*sb,'黄金点火':stable_price>=prevh5*sb}
    # 黄金点火还要求数分钟前EMA状态稳定。
    stable_e3=stable_price*.5+e3[y]*.5
    stable_e21=stable_price*(2/22)+e21[y]*(20/22)
    fire_stable=stable_e3>=stable_e21*1.001
    # 盘中锁筹只在实时量比/换手均已知后计算；极弱市平台主升必须再次通过锁筹硬门。
    lock=pct_live>5.3925+1.1864*volume_ratio+61.3858*turnover
    model_ok={
        '平台主升': structural['平台主升'] and env['平台主升']==REALTIME_PASS and stable['平台主升'] and common_vol and (mlevel!=0 or lock),
        '弱转强': structural['弱转强'] and env['弱转强']==REALTIME_PASS and stable['弱转强'] and common_vol,
        '龙回头': structural['龙回头'] and env['龙回头']==REALTIME_PASS and stable['龙回头'] and common_vol,
        '黄金点火': structural['黄金点火'] and env['黄金点火']==REALTIME_PASS and stable['黄金点火'] and fire_stable and realtime_liq and p['realtime_fire_volume_ratio_min']<=volume_ratio<=p['realtime_fire_volume_ratio_max'] and p['realtime_fire_turnover_min']<=turnover<=p['realtime_fire_turnover_max'],
    }

    # 继续沿用V6.1的增量证据评分；实时硬门本身不重复计分。
    fib=_fib_context(h,l,t,last); pressure_good=fib['no_pressure'] or (fib['pressure_space'] is not None and fib['pressure_space']>=p['pressure_space_good']); support_near=fib['support_valid'] and fib['support_distance']<=p['support_near']
    rsv=[]
    for i in range(len(bars)):
        hh=rolling_max(h,i,9); ll=rolling_min(l,i,9); rsv.append((c[i]-ll)/(hh-ll)*100 if hh>ll else 50)
    k=tdx_sma_series(rsv,3,1); d=tdx_sma_series(k,3,1); j=[3*x-2*y for x,y in zip(k,d)]; momentum=k[t]>d[t] and j[t]>k[t] and k[t]>=k[t-1]
    dealer=ema_series(ema_series(c,13),13); ctrl=[0.0]
    for i in range(1,len(dealer)): ctrl.append((dealer[i]/dealer[i-1]-1)*1000 if dealer[i-1] else 0)
    control_up=ctrl[t]>0 and ctrl[t]>ctrl[t-1]
    # 实时行业分来自六维行业引擎；硬门本身不重复计分。
    industry_points=industry_increment_bonus(mlevel,ind)
    pc={'行业超额强度':industry_points,'锁筹':5 if (lock and mlevel!=0) else 0,'压力空间':5 if pressure_good else 0,'动量':3 if momentum else 0,'控盘':2 if control_up else 0,'换手甜蜜区':3 if .01<=turnover<=.08 else 0}
    wc={'弱势+超卖双确认':5 if weak_prev3 and oversold_y else 0,'行业超额强度':industry_points,'锁筹':5 if lock else 0,'压力空间':4 if pressure_good else 0,'动量':3 if momentum else 0,'控盘':2 if control_up else 0}
    cc={'健康回撤':5 if pb is not None and .06<=abs(pb)<=.12 else 0,'行业超额强度':industry_points,'支撑邻近':4 if support_near else 0,'压力空间':4 if pressure_good else 0,'动量':3 if momentum else 0,'控盘':2 if control_up else 0}
    fc={'金叉新鲜':3 if any(crosses[max(1,t-p['fire_cross_window']+1):t]) else 0,'均线差扩大':4 if firegap>=.005 else 0,'行业超额强度':industry_points,'支撑邻近':3 if support_near else 0,'压力空间':5 if pressure_good else 0,'动量':3 if momentum else 0,'控盘':2 if control_up else 0}
    comps={'平台主升':pc,'弱转强':wc,'龙回头':cc,'黄金点火':fc}; scores={m:float(sum(comps[m].values())) for m in MODEL_ORDER}
    thresholds={'平台主升':p['platform_score_min'],'弱转强':p['weak_score_min'],'龙回头':p['comeback_score_min'],'黄金点火':p['fire_score_min']}
    labels=[m for m in MODEL_ORDER if model_ok[m] and scores[m]>=thresholds[m]]
    bases={m:bool(model_ok[m]) for m in MODEL_ORDER}
    if not labels:
        return RealtimeEvalResult(code,name,trade_date,REALTIME_FAIL,potential_models=potential,model_scores=scores,reject_reasons=['实时量价/稳定突破/增量评分未通过'],metrics={'market_state':mstate,'market_level':mlevel,'industry_valid':ind.get('valid',False),'industry_complete':ind.get('complete',False),'industry_score':ind.get('score_100',0),'industry_phase':ind.get('phase'),'industry_coverage':ind.get('coverage',0),'structural':structural,'environment_state':env,'stable_break':stable,'pool':pool,'pct_live':pct_live,'realtime_volume_ratio':volume_ratio,'realtime_turnover_fraction':turnover,'realtime_amount':amount},bases=bases,components=comps)
    primary=next((m for m in MODEL_ORDER if m in labels),None)
    return RealtimeEvalResult(code,name,trade_date,REALTIME_PASS,labels,potential,scores,primary,len(labels),[],False,[],{'market_state':mstate,'market_level':mlevel,'industry_valid':ind.get('valid',False),'industry_complete':ind.get('complete',False),'industry_score':ind.get('score_100',0),'industry_phase':ind.get('phase'),'industry_coverage':ind.get('coverage',0),'industry_score':ind.get('score_100',0),'industry_excess':ind.get('excess'),'industry_phase':ind.get('phase'),'industry_tier':ind.get('tier'),'industry_dimensions':ind.get('dimensions',{}),'industry_events':ind.get('events',[]),'industry_increment_points':industry_points,'industry_breadth_up_ratio':(ind.get('breadth') or {}).get('up_ratio'),'industry_amount_share':(ind.get('funds') or {}).get('amount_share'),'structural':structural,'environment_state':env,'stable_break':stable,'pool':pool,'pct_live':pct_live,'realtime_volume_ratio':volume_ratio,'realtime_turnover_fraction':turnover,'realtime_amount':amount,'stable_price':stable_price,'pressure_space':fib['pressure_space'],'support_distance':fib['support_distance'],'no_pressure':fib['no_pressure']},bases,comps)


def summarize_realtime(results:Sequence[RealtimeEvalResult])->Dict[str,Any]:
    counts={m:0 for m in MODEL_ORDER}; resonance={str(i):0 for i in range(1,5)}; cands=[]; unknown=[]; rej={}
    for r in results:
        if r.state==REALTIME_PASS:
            for m in r.model_labels: counts[m]+=1
            resonance[str(r.resonance_count)]=resonance.get(str(r.resonance_count),0)+1; cands.append(r)
        elif r.state==REALTIME_UNKNOWN:
            unknown.append(r)
        else:
            for x in r.reject_reasons[:1]: rej[x]=rej.get(x,0)+1
    cands.sort(key=lambda r:(-r.resonance_count,-max((r.model_scores.get(m,0) for m in r.model_labels),default=0),r.code))
    unknown.sort(key=lambda r:(-len(r.potential_models),r.code))
    return {'model_counts':counts,'resonance_counts':resonance,'candidate_count':len(cands),'candidates':cands,'unknown_count':len(unknown),'unknown':unknown,'reject_counts':dict(sorted(rej.items(),key=lambda kv:(-kv[1],kv[0])))}
