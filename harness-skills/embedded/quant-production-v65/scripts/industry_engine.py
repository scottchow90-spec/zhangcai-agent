from __future__ import annotations

import math
import re
from datetime import datetime
from statistics import median
from typing import Any, Dict, List, Optional, Sequence, Tuple

EPS=1e-9

POSITIVE_WORDS=(
    '支持','促进','加快','鼓励','补贴','规划','行动计划','指导意见','试点','获批','批准','落地','突破',
    '扩产','涨价','提价','订单','中标','需求增长','景气','上调','创新高','增长','复苏','利好','投资','建设','国产替代'
)
NEGATIVE_WORDS=(
    '处罚','调查','限制','禁令','风险','事故','停产','亏损','下调','取消','终止','召回','过剩','降价','减产',
    '退市','违约','暴雷','整改','警示','禁止','制裁','下滑','萎缩','亏损扩大'
)
MAJOR_POLICY_WORDS=('国务院','部委','发改委','工信部','财政部','商务部','人民银行','证监会','交易所','政策','规划','指导意见','行动计划','通知','办法','条例','方案')
OFFICIAL_SOURCE_WORDS=('中国政府网','国务院','新华社','人民日报','国家发展改革委','发改委','工信部','财政部','商务部','人民银行','证监会','上交所','深交所','北交所','国家统计局')
AUTHORITATIVE_MEDIA_WORDS=('证券时报','上海证券报','中国证券报','第一财经','财联社','经济日报','央视','人民网','新华财经')


def _mean(xs: Sequence[float]) -> float:
    vals=[float(x) for x in xs if x is not None and math.isfinite(float(x))]
    return sum(vals)/len(vals) if vals else 0.0


def _median(xs: Sequence[float]) -> Optional[float]:
    vals=[float(x) for x in xs if x is not None and math.isfinite(float(x))]
    return float(median(vals)) if vals else None


def _ma(vals: Sequence[float], end: int, n: int) -> float:
    return _mean(vals[max(0,end-n+1):end+1])


def _ret(vals: Sequence[float], end: int, n: int) -> Optional[float]:
    if end-n < 0 or float(vals[end-n]) == 0: return None
    return float(vals[end])/float(vals[end-n])-1.0


def _index_map(index_bars: Sequence[Dict[str,Any]]) -> Dict[str,float]:
    return {str(x.get('date')):float(x.get('close')) for x in index_bars if x.get('date') is not None and x.get('close') is not None}


def _aligned_index_returns(board_bars: Sequence[Dict[str,Any]], index_bars: Sequence[Dict[str,Any]], n: int) -> Optional[float]:
    if len(board_bars) < n+1: return None
    im=_index_map(index_bars)
    d0=str(board_bars[-1].get('date')); d1=str(board_bars[-1-n].get('date'))
    if d0 not in im or d1 not in im or im[d1] == 0: return None
    return im[d0]/im[d1]-1.0


def _score_threshold(v: Optional[float], levels: Sequence[Tuple[float,int]]) -> int:
    if v is None: return 0
    for threshold,score in levels:
        if v >= threshold: return int(score)
    return 0


def _parse_dt(v: Any) -> Optional[datetime]:
    if not v: return None
    s=str(v).strip().replace('T',' ')
    s=re.sub(r'Z$','',s)
    for fmt in ('%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M','%Y-%m-%d','%Y/%m/%d %H:%M:%S','%Y/%m/%d %H:%M','%Y/%m/%d'):
        try: return datetime.strptime(s[:19],fmt)
        except Exception: pass
    return None


def _source_quality(source: str) -> float:
    s=source or ''
    if any(k in s for k in OFFICIAL_SOURCE_WORDS): return 1.0
    if any(k in s for k in AUTHORITATIVE_MEDIA_WORDS): return 0.8
    return 0.55 if s else 0.4


def _polarity(text: str) -> int:
    p=sum(text.count(k) for k in POSITIVE_WORDS)
    n=sum(text.count(k) for k in NEGATIVE_WORDS)
    if p>n and p>0: return 1
    if n>p and n>0: return -1
    return 0


def _trading_age(event_dt: Optional[datetime], board_bars: Sequence[Dict[str,Any]]) -> int:
    if event_dt is None: return 99
    ds=[str(x.get('date')) for x in board_bars]
    ed=event_dt.strftime('%Y-%m-%d')
    return sum(1 for d in ds if d>ed)


def _decay(event_type: str, age: int) -> float:
    if event_type == '重大政策':
        if age<=1:return 1.0
        if age<=3:return .8
        if age<=5:return .6
        if age<=10:return .3
        return 0.0
    if age<=0:return 1.0
    if age==1:return .7
    if age==2:return .4
    return 0.0


def _event_metrics(articles: Sequence[Dict[str,Any]], industry_name: Optional[str], board_bars: Sequence[Dict[str,Any]], price_confirmed: bool, asof: Optional[datetime], covered: bool) -> Dict[str,Any]:
    if not covered:
        return {'covered':False,'driver_score':0.0,'risk_penalty':0.0,'top_events':[],'positive_confirmed':False,'fresh_event_count':0}
    seen=set(); pos=[]; neg=[]; top=[]
    for a in articles or []:
        title=re.sub(r'<[^>]+>','',str(a.get('title') or '')).strip()
        content=re.sub(r'<[^>]+>','',str(a.get('content') or '')).strip()
        if not title: continue
        key=re.sub(r'\s+','',title)[:60]
        if key in seen: continue
        seen.add(key)
        dt=_parse_dt(a.get('time') or a.get('date') or a.get('published_at'))
        if asof and dt and dt>asof.replace(tzinfo=None):
            continue
        txt=title+' '+content
        pol=_polarity(txt)
        if pol==0: continue
        etype='重大政策' if any(k in txt for k in MAJOR_POLICY_WORDS) else '产业事件'
        age=_trading_age(dt,board_bars); decay=_decay(etype,age)
        if decay<=0: continue
        q=_source_quality(str(a.get('source') or a.get('mediaName') or ''))
        # 搜索词命中行业名才视为真正行业范围；否则只给较弱范围系数。
        scope=1.0 if industry_name and industry_name in txt else .65
        raw=q*scope*decay
        row={'title':title,'time':dt.isoformat(timespec='minutes') if dt else str(a.get('time') or ''),'source':str(a.get('source') or a.get('mediaName') or ''),'direction':'正面' if pol>0 else '负面','event_type':etype,'trading_age':age,'raw_strength':round(raw,4),'price_confirmed':bool(price_confirmed) if pol>0 else None}
        top.append(row)
        (pos if pol>0 else neg).append(raw)
    # 正面驱动必须经过价格确认；不确认不加分。最多取3条独立事件，防止转载堆分。
    pos_raw=sum(sorted(pos,reverse=True)[:3]) if price_confirmed else 0.0
    neg_raw=sum(sorted(neg,reverse=True)[:3])
    driver=min(15.0,15.0*(1-math.exp(-pos_raw/1.5))) if pos_raw>0 else 0.0
    risk=min(15.0,15.0*(1-math.exp(-neg_raw/1.3))) if neg_raw>0 else 0.0
    top=sorted(top,key=lambda x:(x['direction']!='负面',-x['raw_strength'],x['trading_age']))[:8]
    return {'covered':True,'driver_score':round(driver,2),'risk_penalty':round(risk,2),'top_events':top,'positive_confirmed':bool(pos and price_confirmed),'fresh_event_count':sum(1 for x in top if x['trading_age']<=2)}


def _breadth_metrics(members: Sequence[Dict[str,Any]], prev: Optional[Dict[str,Any]]) -> Dict[str,Any]:
    pcts=[]; amounts=[]
    for x in members or []:
        try:
            pct=float(x.get('pct'))
            if math.isfinite(pct): pcts.append(pct/100.0)
        except Exception: pass
        try:
            amt=float(x.get('amount'))
            if math.isfinite(amt) and amt>=0: amounts.append(amt)
        except Exception: pass
    if not pcts:
        return {'covered':False,'score':0,'up_ratio':None,'median_return':None,'pct3_ratio':None,'pct5_ratio':None,'limitup_count':0,'amount_sum':sum(amounts),'breadth_improved':False}
    n=len(pcts); up=sum(x>0 for x in pcts)/n; med=_median(pcts) or 0.0; p3=sum(x>=.03 for x in pcts)/n; p5=sum(x>=.05 for x in pcts)/n; lu=sum(x>=.095 for x in pcts)
    score=0
    score += _score_threshold(up,((.65,5),(.55,3),(.50,2)))
    score += _score_threshold(med,((.01,4),(0,2)))
    score += _score_threshold(p3,((.20,4),(.10,3),(.05,1)))
    score += _score_threshold(p5,((.10,3),(.05,2),(.02,1)))
    score += 2 if lu>=2 or lu/max(n,1)>=.03 else (1 if lu>=1 else 0)
    prev_up=(prev or {}).get('breadth_up_ratio')
    improved=prev_up is not None and up>=float(prev_up)+.05
    score += 2 if improved else 0
    return {'covered':True,'score':min(score,20),'up_ratio':up,'median_return':med,'pct3_ratio':p3,'pct5_ratio':p5,'limitup_count':lu,'amount_sum':sum(amounts),'breadth_improved':improved}


def _funds_metrics(board_bars: Sequence[Dict[str,Any]], members: Sequence[Dict[str,Any]], market_amount_total: Optional[float], prev: Optional[Dict[str,Any]]) -> Dict[str,Any]:
    if len(board_bars)<21:
        return {'covered':False,'score':0,'amount_ratio_5':None,'amount_ratio_20':None,'amount_share':None,'top3_amount_share':None}
    am=[float(x.get('amount') or 0) for x in board_bars]; cur=am[-1]
    r5=cur/max(_mean(am[-6:-1]),EPS); r20=cur/max(_mean(am[-21:-1]),EPS)
    member_amounts=sorted([float(x.get('amount') or 0) for x in members or [] if x.get('amount') not in (None,'-','')],reverse=True)
    msum=sum(member_amounts); top3=(sum(member_amounts[:3])/msum) if msum>0 else None
    share=(msum/float(market_amount_total)) if msum>0 and market_amount_total and market_amount_total>0 else None
    score=0
    score += _score_threshold(r20,((1.2,4),(1.0,3),(.8,1)))
    score += _score_threshold(r5,((1.1,3),(.9,1)))
    prev_share=(prev or {}).get('amount_share')
    if share is not None and prev_share is not None and float(prev_share)>0:
        score += 3 if share>=float(prev_share)*1.10 else (2 if share>float(prev_share) else 0)
    if top3 is not None:
        score += 3 if top3<=.45 else (2 if top3<=.60 else (1 if top3<=.75 else 0))
    # 健康放量而非极端爆量；极端爆量由过热惩罚处理。
    if 1.0<=r20<=2.0: score+=2
    return {'covered':True,'score':min(score,15),'amount_ratio_5':r5,'amount_ratio_20':r20,'amount_share':share,'top3_amount_share':top3}


def industry_metrics(industry_data: Any, index_bars: Any, params: Optional[Dict[str,Any]]=None) -> Dict[str,Any]:
    """六维行业强度与驱动引擎。

    industry_data 推荐结构：
    {name,bars,constituents,events,events_covered,history_state,market_amount_total,asof}
    兼容旧版直接传行业K线列表，但此时行业内部宽度和消息覆盖不完整，complete=False。
    """
    p=params or {}
    if isinstance(industry_data,list):
        data={'name':None,'bars':industry_data,'constituents':[],'events':[],'events_covered':False,'history_state':[],'market_amount_total':None,'asof':None}
    elif isinstance(industry_data,dict): data=industry_data
    else: data={}
    bars=list(data.get('bars') or [])
    if len(bars)<21:
        return {'valid':False,'complete':False,'score':0,'score_100':0,'strong':False,'super':False,'phase':'未知','tier':'未知','return':None,'excess':None,
                'dimensions':{'相对价格强度':0,'行业内部扩散':0,'时间持续性':0,'资金与成交确认':0,'消息政策事件驱动':0,'龙头与梯队':0},'coverage':0.0,'overheat_penalty':0,'event_risk_penalty':0,'events':[]}
    c=[float(x['close']) for x in bars]; h=[float(x.get('high',x['close'])) for x in bars]; t=len(c)-1
    if c[t-1]<=0:
        return {'valid':False,'complete':False,'score':0,'score_100':0,'strong':False,'super':False,'phase':'未知','tier':'未知','return':None,'excess':None,'dimensions':{},'coverage':0.0,'overheat_penalty':0,'event_risk_penalty':0,'events':[]}
    if isinstance(index_bars,(int,float)):
        idx1=float(index_bars); idxrets={1:idx1,3:None,5:None,10:None}; idx_daily=[]
    else:
        idxrets={n:_aligned_index_returns(bars,index_bars or [],n) for n in (1,3,5,10)}
        im=_index_map(index_bars or []); idx_daily=[]
        for i in range(max(1,t-4),t+1):
            d0=str(bars[i].get('date')); d1=str(bars[i-1].get('date'))
            idx_daily.append((im[d0]/im[d1]-1) if d0 in im and d1 in im and im[d1] else None)
    rets={n:_ret(c,t,n) for n in (1,3,5,10)}; excess={n:(rets[n]-idxrets[n] if rets[n] is not None and idxrets[n] is not None else None) for n in (1,3,5,10)}
    price=0
    price += _score_threshold(excess[1],((.01,4),(0,2)))
    price += _score_threshold(excess[3],((.02,5),(.005,3),(0,1)))
    price += _score_threshold(excess[5],((.03,6),(.01,4),(0,2)))
    price += _score_threshold(excess[10],((.05,4),(.02,3),(0,1)))
    price += int(c[t]>_ma(c,t,10))+int(_ma(c,t,5)>=_ma(c,t,10))+int(c[t]>_ma(c,t,20))
    price += 3 if c[t]>max(h[max(0,t-20):t]) else 0
    price=min(price,25)

    hist=list(data.get('history_state') or []); prev=hist[-1] if hist else None
    breadth=_breadth_metrics(data.get('constituents') or [],prev)

    # 时间持续性：不只看当日，统计1/3/5/10日超额和近5日逐日超额胜率。
    board_daily=[]
    for i in range(max(1,t-4),t+1): board_daily.append(c[i]/c[i-1]-1 if c[i-1] else 0)
    pos_ex_days=0
    for br,ir in zip(board_daily,idx_daily[-len(board_daily):] if idx_daily else []):
        if ir is not None and br-ir>0: pos_ex_days+=1
    pos_days=sum(x>0 for x in board_daily)
    time_score=0
    time_score += 6 if pos_ex_days>=5 else (5 if pos_ex_days>=4 else (3 if pos_ex_days>=3 else 0))
    time_score += 4 if pos_days>=4 else (2 if pos_days>=3 else 0)
    time_score += 2 if excess[3] is not None and excess[3]>0 else 0
    time_score += 2 if excess[5] is not None and excess[5]>0 else 0
    time_score += 2 if excess[10] is not None and excess[10]>0 else 0
    if prev and prev.get('score_100') is not None:
        time_score += 4 if float(prev['score_100'])>=60 else (2 if float(prev['score_100'])>=45 else 0)
    time_score=min(time_score,20)

    funds=_funds_metrics(bars,data.get('constituents') or [],data.get('market_amount_total'),prev)

    # 龙头与梯队：既要有领涨核心，又不能只有一只股票独舞。
    pcts=sorted([float(x.get('pct'))/100.0 for x in data.get('constituents') or [] if x.get('pct') not in (None,'-','')],reverse=True)
    leader=0
    if pcts:
        up=breadth.get('up_ratio') or 0; med=breadth.get('median_return') or 0; top3=_mean(pcts[:3])
        leader += 2 if pcts[0]>=.08 and up>=.55 else (1 if pcts[0]>=.05 else 0)
        leader += 2 if top3>=.03 and med>=0 else (1 if top3>=.02 else 0)
        leader += 1 if up>=.55 else 0
    leader=min(leader,5)

    price_confirmed=(excess[1] is not None and excess[1]>0 and (breadth.get('up_ratio') or 0)>=.50) or (excess[3] is not None and excess[3]>0 and (breadth.get('up_ratio') or 0)>=.55)
    asof=_parse_dt(data.get('asof')) if data.get('asof') else None
    ev=_event_metrics(data.get('events') or [],data.get('name'),bars,price_confirmed,asof,bool(data.get('events_covered')))
    driver=float(ev['driver_score'])

    # 过热/退潮惩罚，避免“越涨越高分”。
    overheat=0
    if rets[1] is not None and rets[1]>=.04: overheat+=5
    if funds.get('amount_ratio_20') is not None and funds['amount_ratio_20']>=2: overheat+=4
    if (breadth.get('up_ratio') or 0)>=.80: overheat+=3
    if excess[5] is not None and excess[5]>=.08: overheat+=4
    if breadth.get('limitup_count',0)>=3 and (breadth.get('median_return') or 0)>=.02: overheat+=2
    if pcts and _mean(pcts[:3])>=.08: overheat+=2
    overheat=min(overheat,20)
    retreat=0
    if rets[1] is not None and rets[1]<0 and (excess[1] is not None and excess[1]<0): retreat+=4
    if excess[3] is not None and excess[3]<0: retreat+=4
    if excess[5] is not None and excess[5]<0: retreat+=4
    if breadth.get('covered') and (breadth.get('up_ratio') or 0)<.40: retreat+=4
    if breadth.get('covered') and (breadth.get('median_return') or 0)<0: retreat+=4
    structure_penalty=min(max(overheat,retreat),20)

    dims={'相对价格强度':price,'行业内部扩散':breadth['score'],'时间持续性':time_score,'资金与成交确认':funds['score'],'消息政策事件驱动':driver,'龙头与梯队':leader}
    base=sum(float(x) for x in dims.values())
    final=max(0.0,min(100.0,base-structure_penalty-float(ev['risk_penalty'])))

    if retreat>=12 or ((excess[3] is not None and excess[3]<0) and (excess[5] is not None and excess[5]<0) and breadth.get('covered') and (breadth.get('up_ratio') or 0)<.45): phase='退潮'
    elif overheat>=10: phase='高潮'
    elif excess[5] is not None and excess[5]>0 and breadth.get('covered') and ((breadth.get('up_ratio') or 0)<.50 or (breadth.get('median_return') or 0)<0): phase='分歧'
    elif excess[3] is not None and excess[3]>0 and ((excess[5] is None or excess[5]<=0) or pos_ex_days<=3): phase='启动'
    elif excess[3] is not None and excess[3]>0 and excess[5] is not None and excess[5]>0 and pos_ex_days>=3 and (not breadth.get('covered') or (breadth.get('up_ratio') or 0)>=.55): phase='主升'
    else: phase='轮动/中性'

    core_min=float(p.get('industry_core_score_min',80)); strong_min=float(p.get('industry_strong_score_min',70)); tradable_min=float(p.get('industry_tradable_score_min',60))
    if final>=core_min:tier='核心强势行业'
    elif final>=strong_min:tier='强势行业'
    elif final>=tradable_min:tier='可交易行业'
    elif final>=45:tier='轮动/中性'
    elif final>=30:tier='偏弱'
    else:tier='弱势/退潮'

    coverage_weights={'price':25,'breadth':20,'time':20,'funds':15,'events':15,'leader':5}
    coverage=coverage_weights['price']+coverage_weights['time']
    if breadth.get('covered'): coverage+=coverage_weights['breadth']+coverage_weights['leader']
    if funds.get('covered'): coverage+=coverage_weights['funds']
    if ev.get('covered'): coverage+=coverage_weights['events']
    complete=coverage>=100
    return {
        'valid':True,'complete':complete,'coverage':coverage/100.0,'score':final,'score_100':final,'strong':final>=70 and phase in ('启动','主升'),
        'super':final>=80 and phase in ('启动','主升'),'phase':phase,'tier':tier,
        'return':rets[1],'excess':excess[1],'returns':rets,'excess_returns':excess,'dimensions':dims,'base_score':base,
        'overheat_penalty':structure_penalty,'event_risk_penalty':float(ev['risk_penalty']),'events':ev['top_events'],'event_covered':ev['covered'],
        'event_positive_confirmed':ev['positive_confirmed'],'fresh_event_count':ev['fresh_event_count'],'price_confirmed':price_confirmed,
        'breadth':breadth,'funds':funds,'positive_excess_days_5':pos_ex_days,'positive_days_5':pos_days,
        'gate_strong_market':float(p.get('industry_strong_market_min',60)),'gate_normal_market':float(p.get('industry_normal_market_min',70)),'gate_weak_market':float(p.get('industry_weak_market_min',80)),'gate_extreme_platform':float(p.get('industry_extreme_platform_min',85)),
    }


def industry_environment_state(model: str, market_level: int, ind: Dict[str,Any], lock: bool=False) -> Optional[bool]:
    """返回 True/False/None；None 表示行业数据未闭合，必须按UNKNOWN传播而不是当失败。"""
    if not ind.get('valid') or not ind.get('complete'): return None
    score=float(ind.get('score_100') or 0); phase=str(ind.get('phase') or '未知')
    if phase=='退潮': return False
    if market_level>=3: return score>=float(ind.get('gate_strong_market',60))
    if market_level==2: return score>=float(ind.get('gate_normal_market',70)) and phase in ('启动','主升')
    if market_level==1: return score>=float(ind.get('gate_weak_market',80)) and phase in ('启动','主升')
    if market_level==0: return model=='平台主升' and score>=float(ind.get('gate_extreme_platform',85)) and phase in ('启动','主升') and bool(lock)
    return False


def industry_increment_bonus(market_level: int, ind: Dict[str,Any]) -> int:
    """只奖励超过行业硬门的额外强度，避免“行业硬门通过”本身再次重复计分。

    基础门：强市60、常市70、弱市80、极弱平台85。
    每高出门槛4分增加1分，最多5分；高潮/分歧/退潮不享受额外奖励。
    """
    if not ind.get('valid') or not ind.get('complete'):
        return 0
    phase=str(ind.get('phase') or '未知')
    if phase not in ('启动','主升'):
        return 0
    score=float(ind.get('score_100') or 0)
    if market_level>=3: gate=float(ind.get('gate_strong_market',60))
    elif market_level==2: gate=float(ind.get('gate_normal_market',70))
    elif market_level==1: gate=float(ind.get('gate_weak_market',80))
    else: gate=float(ind.get('gate_extreme_platform',85))
    return max(0,min(5,int((score-gate)//4)))
