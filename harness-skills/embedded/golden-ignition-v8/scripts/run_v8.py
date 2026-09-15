#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WorkBuddy V8 deterministic daily screener (stdlib only).

Input CSV: date/code/open/high/low/close/volume; optional name/amount/board/is_st/is_delist.
Output: results.csv, golden_ignition_audit.csv, summary.json.
No third-party Python packages are required.
"""
from __future__ import annotations
import argparse, csv, json, math
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

NAN = None
ALIASES = {
    'date':['date','time','trade_date'], 'code':['code','symbol','ticker'], 'name':['name','stock_name'],
    'open':['open','raw_open'], 'high':['high','raw_high'], 'low':['low','raw_low'], 'close':['close','raw_close'],
    'volume':['volume','vol'], 'amount':['amount','turnover_amount'], 'board':['board','market_board'],
    'is_st':['is_st','st'], 'is_delist':['is_delist','delist']
}

def isnum(x):
    return isinstance(x,(int,float)) and math.isfinite(x)

def fnum(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None

def truthy(v):
    if v is None: return False
    s=str(v).strip().lower()
    return s in {'1','true','yes','y','是','st'}

def parse_date(s):
    s=str(s).strip()
    for fmt in ('%Y-%m-%d','%Y/%m/%d','%Y%m%d'):
        try: return datetime.strptime(s,fmt).date()
        except ValueError: pass
    raise ValueError(f'无法解析日期: {s}')

def safe_div(a,b,default=None):
    if not isnum(a) or not isnum(b) or b == 0: return default
    return a/b

def vmax(a,b):
    if not isnum(a): return b
    if not isnum(b): return a
    return max(a,b)

def ema(vals,n):
    alpha=2.0/(n+1.0); out=[]; prev=None
    for x in vals:
        if not isnum(x): out.append(prev); continue
        prev=x if prev is None else alpha*x+(1-alpha)*prev
        out.append(prev)
    return out

def tdx_sma(vals,n,m):
    out=[]; prev=None
    for x in vals:
        if not isnum(x): out.append(prev); continue
        prev=x if prev is None else (m*x+(n-m)*prev)/n
        out.append(prev)
    return out

def shift(vals,n=1,fill=None):
    if n<=0: return list(vals)
    return [fill]*n + list(vals[:-n]) if len(vals)>=n else [fill]*len(vals)

def roll(vals,n,kind='sum'):
    out=[]
    for i in range(len(vals)):
        start=max(0,i-n+1); w=vals[start:i+1]
        if kind=='sum':
            out.append(sum(1 if bool(x) else 0 for x in w))
        else:
            nums=[x for x in w if isnum(x)]
            if not nums: out.append(None)
            elif kind=='max': out.append(max(nums))
            elif kind=='min': out.append(min(nums))
            elif kind=='mean': out.append(sum(nums)/len(nums))
            else: raise ValueError(kind)
    return out

def ref_roll(vals,n,kind):
    # rolling window over prior n bars, excluding current
    return shift(roll(vals,n,kind),1,None)

def cross(a,b):
    # a/b can be list or scalar
    n=len(a) if isinstance(a,list) else len(b)
    aa=a if isinstance(a,list) else [float(a)]*n
    bb=b if isinstance(b,list) else [float(b)]*n
    out=[False]*n
    for i in range(1,n):
        if all(isnum(x) for x in (aa[i],bb[i],aa[i-1],bb[i-1])):
            out[i]=aa[i]>bb[i] and aa[i-1]<=bb[i-1]
    return out

def barlast(flags):
    out=[]; last=None
    for i,v in enumerate(flags):
        if bool(v): last=i; out.append(0)
        else: out.append(math.inf if last is None else i-last)
    return out

def bool_and(*seqs):
    return [all(bool(s[i]) for s in seqs) for i in range(len(seqs[0]))]

def bool_or(*seqs):
    return [any(bool(s[i]) for s in seqs) for i in range(len(seqs[0]))]

def ge(a,b): return [isnum(x) and x>=b for x in a]
def gt(a,b): return [isnum(x) and x>b for x in a]
def le(a,b): return [isnum(x) and x<=b for x in a]
def lt(a,b): return [isnum(x) and x<b for x in a]

def board_limit(code, board, d):
    code=str(code).zfill(6); board=str(board or '')
    if '科创' in board or code.startswith(('688','689')): return .20
    if '创业' in board or code.startswith(('300','301')): return .20 if d>=date(2020,8,24) else .10
    return .10

def normalize_header(fieldnames):
    lower={x.lower():x for x in fieldnames}; mapping={}
    for dst,opts in ALIASES.items():
        if dst in fieldnames: mapping[dst]=dst; continue
        for x in opts:
            if x.lower() in lower: mapping[dst]=lower[x.lower()]; break
    return mapping

def load_csv(path):
    groups=defaultdict(list)
    with open(path,'r',encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f); mapping=normalize_header(r.fieldnames or [])
        need=['date','code','open','high','low','close','volume']; miss=[x for x in need if x not in mapping]
        if miss: raise SystemExit('缺少必需字段: '+','.join(miss))
        for raw in r:
            row={}
            for dst,src in mapping.items(): row[dst]=raw.get(src,'')
            row['date']=parse_date(row['date']); row['code']=str(row['code']).split('.')[0].zfill(6)
            for c in ('open','high','low','close','volume','amount'): row[c]=fnum(row.get(c))
            # invalid historical OHLCV rows are not valid bars
            if any(row.get(c) is None for c in ('open','high','low','close','volume')): continue
            row.setdefault('name',''); row.setdefault('board',''); row.setdefault('is_st',''); row.setdefault('is_delist','')
            groups[row['code']].append(row)
    for code in groups: groups[code].sort(key=lambda x:x['date'])
    return groups

def score_if(cond,yes,no=0): return yes if bool(cond) else no

def compute(rows):
    n=len(rows); code=rows[-1]['code']
    O=[r['open'] for r in rows]; H=[r['high'] for r in rows]; L=[r['low'] for r in rows]; C=[r['close'] for r in rows]; V=[r['volume'] for r in rows]; A=[r.get('amount') for r in rows]
    lim=[board_limit(code,r.get('board',''),r['date']) for r in rows]
    prev=shift(C,1)
    ns=[safe_div((C[i]/prev[i]-1) if isnum(prev[i]) else None,lim[i]) for i in range(n)]
    cpos=[safe_div(C[i]-L[i],max(H[i]-L[i],.01)) for i in range(n)]
    hstr=[isnum(ns[i]) and ns[i]>=.70 and C[i]>O[i] and cpos[i]>=.70 for i in range(n)]
    hzt=[isnum(ns[i]) and ns[i]>=.985 and C[i]==H[i] for i in range(n)]
    a5=ref_roll(A,5,'mean'); liq=[isnum(x) and x>=50_000_000 for x in a5]

    tr10=ema(ema(C,10),10); e5=ema(C,5); e20=ema(C,20); e89=ema(C,89)
    T1=[i>0 and isnum(tr10[i]) and isnum(tr10[i-1]) and tr10[i]>tr10[i-1] for i in range(n)]
    T2=[isnum(e5[i]) and isnum(e20[i]) and e5[i]>e20[i] for i in range(n)]
    T3=[i>0 and isnum(e20[i]) and isnum(e20[i-1]) and e20[i]>=e20[i-1] for i in range(n)]
    T4=[isnum(e89[i]) and C[i]>e89[i] for i in range(n)]
    r5,r10,r20,r60,r120=[ref_roll(H,k,'max') for k in (5,10,20,60,120)]
    brk5=[isnum(r5[i]) and C[i]>r5[i] for i in range(n)]; brk10=[isnum(r10[i]) and C[i]>r10[i] for i in range(n)]; brk20=[isnum(r20[i]) and C[i]>r20[i] for i in range(n)]; brk60=[isnum(r60[i]) and C[i]>r60[i] for i in range(n)]
    v5=ref_roll(V,5,'mean'); vr=[safe_div(V[i],max(v5[i],1)) if isnum(v5[i]) else None for i in range(n)]
    extn=[safe_div(C[i]/e20[i]-1,lim[i]) if isnum(e20[i]) else None for i in range(n)]; extok=[isnum(x) and x<=2.50 for x in extn]
    space60=[isnum(r60[i]) and (C[i]>=r60[i] or safe_div(r60[i]-C[i],max(C[i],.01),-999)>=lim[i]*.35) for i in range(n)]
    space120=[isnum(r120[i]) and (C[i]>=r120[i] or safe_div(r120[i]-C[i],max(C[i],.01),-999)>=lim[i]*.50) for i in range(n)]

    # Model A
    bt=[max(O[i],C[i]) for i in range(n)]; bb=[min(O[i],C[i]) for i in range(n)]
    min_bt=ref_roll(bt,4,'min'); max_bb=ref_roll(bb,4,'max'); ov4=[isnum(min_bt[i]) and isnum(max_bb[i]) and min_bt[i]>=max_bb[i] for i in range(n)]
    p5h=ref_roll(H,5,'max'); p5l=ref_roll(L,5,'min'); p20h=ref_roll(H,20,'max'); p20l=ref_roll(L,20,'min')
    w5=[safe_div(p5h[i]-p5l[i],max(p5l[i],.01)) if isnum(p5h[i]) and isnum(p5l[i]) else None for i in range(n)]
    w20=[safe_div(p20h[i]-p20l[i],max(p20l[i],.01)) if isnum(p20h[i]) and isnum(p20l[i]) else None for i in range(n)]
    comp=[isnum(w5[i]) and isnum(w20[i]) and w5[i]<=w20[i]*.75 for i in range(n)]
    v3=ref_roll(V,3,'mean'); v10=ref_roll(V,10,'mean'); vcon=[isnum(v3[i]) and isnum(v10[i]) and v3[i]<=v10[i]*1.05 for i in range(n)]
    d20=[safe_div(r20[i]-prev[i],max(prev[i],.01)) if isnum(r20[i]) and isnum(prev[i]) else None for i in range(n)]
    near20=[isnum(d20[i]) and d20[i]>=0 and d20[i]<=lim[i]*1.20 for i in range(n)]
    brk20_count=roll(brk20,5,'sum'); first20=[i>0 and brk20_count[i-1]==0 for i in range(n)]

    # Model B
    lc=prev; diff=[C[i]-lc[i] if isnum(lc[i]) else None for i in range(n)]
    rsden=tdx_sma([abs(x) if isnum(x) else None for x in diff],2,1); rsnum=tdx_sma([max(x,0) if isnum(x) else None for x in diff],2,1)
    rs2=[safe_div(rsnum[i],max(rsden[i],.0001))*100 if isnum(rsnum[i]) and isnum(rsden[i]) else None for i in range(n)]
    w45=cross(45,rs2); w20d=cross(20,rs2); wash=bool_or(w45,w20d)
    bw=barlast(shift(wash,1,False)); bs=barlast(shift(hstr,1,False)); seqb=[bw[i]<=7 and bs[i]>bw[i] and bs[i]<=30 for i in range(n)]; deepw=[x<=7 for x in barlast(shift(w20d,1,False))]
    rec1=[i>0 and isnum(rs2[i]) and isnum(rs2[i-1]) and rs2[i]>rs2[i-1] for i in range(n)]; rec2=[isnum(x) and x>=35 for x in rs2]
    rec3=[isnum(prev[i]) and C[i]>prev[i] and C[i]>O[i] for i in range(n)]; rec4=[i>0 and C[i]>H[i-1] for i in range(n)]
    ddb=[safe_div(r20[i]-C[i],max(r20[i],.01)) if isnum(r20[i]) else None for i in range(n)]

    # Model C
    e3=ema(C,3); e21=ema(C,21); edif=[e3[i]-e21[i] if isnum(e3[i]) and isnum(e21[i]) else None for i in range(n)]; f0=cross(e3,e21); deadf=cross(e21,e3)
    bodyr=[safe_div(C[i]-O[i],max(H[i]-L[i],.01)) for i in range(n)]; gapn=[safe_div((O[i]/prev[i]-1) if isnum(prev[i]) else None,lim[i]) for i in range(n)]
    pconf=[C[i]>O[i] and isnum(bodyr[i]) and bodyr[i]>=.25 and cpos[i]>=.72 and isnum(ns[i]) and ns[i]>=.25 and (brk5[i] or ns[i]>=.50) and isnum(vr[i]) and vr[i]>=.75 and vr[i]<=3.50 for i in range(n)]
    f1=[i>=1 and f0[i-1] and not pconf[i-1] for i in range(n)]
    pconf2=roll(pconf,2,'sum'); f2=[i>=2 and f0[i-2] and isnum(e3[i-1]) and isnum(e21[i-1]) and e3[i-1]>e21[i-1] and pconf2[i-1]==0 for i in range(n)]
    fresh=bool_or(f0,f1,f2)
    preext=[]; slope=[]
    for i in range(n):
        pe=sl=None
        if f0[i] and i>=4 and isnum(e21[i-1]) and isnum(e21[i-4]):
            pe=safe_div(C[i-1]/e21[i-1]-1,lim[i]); sl=safe_div(e21[i-1]/e21[i-4]-1,lim[i])
        elif f1[i] and i>=5 and isnum(e21[i-2]) and isnum(e21[i-5]):
            pe=safe_div(C[i-2]/e21[i-2]-1,lim[i]); sl=safe_div(e21[i-2]/e21[i-5]-1,lim[i])
        elif f2[i] and i>=6 and isnum(e21[i-3]) and isnum(e21[i-6]):
            pe=safe_div(C[i-3]/e21[i-3]-1,lim[i]); sl=safe_div(e21[i-3]/e21[i-6]-1,lim[i])
        preext.append(pe); slope.append(sl)
    prepos=[isnum(x) and -.50<=x<=.40 for x in preext]; slowok=[isnum(x) and x>=-.15 for x in slope]
    spup=[i>0 and isnum(e3[i]) and isnum(e3[i-1]) and isnum(edif[i]) and isnum(edif[i-1]) and e3[i]>e3[i-1] and edif[i]>edif[i-1] for i in range(n)]
    fgap=[safe_div(e3[i]/e21[i]-1,lim[i]) if isnum(e3[i]) and isnum(e21[i]) else None for i in range(n)]; fgapok=[isnum(x) and x<=.60 for x in fgap]
    ns70=[isnum(x) and x>=.70 for x in ns]; c3=roll(ns70,3,'sum'); c5=roll(ns70,5,'sum'); hot3=[i>0 and c3[i-1]==0 for i in range(n)]; hot5=[i>0 and c5[i-1]==0 for i in range(n)]
    run10=[safe_div(C[i-1]/C[i-11]-1,lim[i]) if i>=11 else None for i in range(n)]; runok=[isnum(x) and x<=1.80 for x in run10]
    dead5=roll(deadf,5,'sum'); stable5=[i>0 and dead5[i-1]==0 for i in range(n)]; tradeok=[H[i]>L[i] for i in range(n)]

    out=[]; sigc0_hist=[]
    for i,r in enumerate(rows):
        base=(i+1)>=130 and C[i]>2 and V[i]>0
        name=str(r.get('name','')); board=str(r.get('board',''))
        if truthy(r.get('is_st')) or 'ST' in name.upper(): base=False
        if truthy(r.get('is_delist')) or '退' in name: base=False
        if '北交所' in board or code.startswith(('4','8','92')): base=False

        ahard=base and (T1[i] or T2[i]) and isnum(e20[i]) and C[i]>e20[i] and (brk10[i] or brk20[i]) and C[i]>O[i] and cpos[i]>=.70 and isnum(ns[i]) and ns[i]>=.35 and isnum(vr[i]) and .80<=vr[i]<=4 and extok[i]
        ascore=(score_if(T1[i],6)+score_if(T2[i],6)+score_if(T3[i],4)+score_if(T4[i],4)+score_if(ov4[i],7)+score_if(comp[i],7)+score_if(vcon[i],5)+score_if(near20[i],4)+score_if(first20[i],1)+score_if(brk10[i],6)+score_if(brk20[i],8)+score_if(brk60[i],3)+
                (10 if isnum(ns[i]) and ns[i]>=.80 else 7 if isnum(ns[i]) and ns[i]>=.55 else 4 if isnum(ns[i]) and ns[i]>=.35 else 0)+
                (6 if cpos[i]>=.90 else 4 if cpos[i]>=.80 else 2 if cpos[i]>=.70 else 0)+
                (8 if isnum(vr[i]) and 1.10<=vr[i]<=2.80 else 5 if isnum(vr[i]) and .80<=vr[i]<=4 else 0)+score_if(liq[i],3)+
                (4 if isnum(extn[i]) and extn[i]<=1.60 else 2 if extok[i] else 0)+score_if(space60[i],4)+score_if(space120[i],4))
        siga=ahard and ascore>=70

        bhard=base and seqb[i] and (T1[i] or T2[i]) and isnum(e20[i]) and C[i]>=e20[i]*.98 and rec1[i] and rec2[i] and rec3[i] and cpos[i]>=.65 and isnum(ns[i]) and ns[i]>=.20 and isnum(vr[i]) and .70<=vr[i]<=3.20 and isnum(ddb[i]) and ddb[i]<=.25 and extok[i]
        bscore=((8 if hzt[i] else 5 if hstr[i] else 0)+score_if(seqb[i],10)+(7 if deepw[i] else 3)+score_if(T1[i],6)+score_if(T2[i],6)+score_if(T3[i],4)+score_if(T4[i],4)+
                (7 if isnum(rs2[i]) and rs2[i]>=45 else 4 if isnum(rs2[i]) and rs2[i]>=35 else 0)+score_if(rec4[i],8)+
                (7 if cpos[i]>=.90 else 5 if cpos[i]>=.75 else 3 if cpos[i]>=.65 else 0)+
                (8 if isnum(ns[i]) and ns[i]>=.50 else 5 if isnum(ns[i]) and ns[i]>=.30 else 3 if isnum(ns[i]) and ns[i]>=.20 else 0)+
                (10 if isnum(vr[i]) and .90<=vr[i]<=2.30 else 6 if isnum(vr[i]) and .70<=vr[i]<=3.20 else 0)+score_if(liq[i],4)+
                (5 if isnum(ddb[i]) and ddb[i]<=.12 else 3 if isnum(ddb[i]) and ddb[i]<=.25 else 0)+score_if(space60[i],3)+score_if(space120[i],3))
        sigb=bhard and bscore>=70

        chard=base and fresh[i] and slowok[i] and prepos[i] and isnum(e3[i]) and isnum(e21[i]) and e3[i]>e21[i] and spup[i] and fgapok[i] and C[i]>e21[i] and C[i]>O[i] and isnum(bodyr[i]) and bodyr[i]>=.25 and cpos[i]>=.72 and isnum(ns[i]) and ns[i]>=.25 and (brk5[i] or ns[i]>=.50) and isnum(vr[i]) and .75<=vr[i]<=3.50 and hot3[i] and runok[i] and tradeok[i] and isnum(extn[i]) and extn[i]<=1.60 and isnum(gapn[i]) and -.50<=gapn[i]<=.75
        cscore=((10 if f0[i] else 8 if f1[i] else 6)+
                (6 if isnum(slope[i]) and slope[i]>=0 else 4 if isnum(slope[i]) and slope[i]>=-.08 else 2)+
                (6 if isnum(preext[i]) and abs(preext[i])<=.15 else 4 if isnum(preext[i]) and abs(preext[i])<=.30 else 2)+
                (4 if isnum(fgap[i]) and fgap[i]<=.12 else 3 if isnum(fgap[i]) and fgap[i]<=.30 else 1)+score_if(spup[i],2)+score_if(stable5[i],2)+
                (12 if brk20[i] else 9 if brk10[i] else 6 if brk5[i] else 4 if isnum(ns[i]) and ns[i]>=.50 else 0)+
                (8 if isnum(ns[i]) and ns[i]>=.85 else 6 if isnum(ns[i]) and ns[i]>=.65 else 4 if isnum(ns[i]) and ns[i]>=.45 else 2 if isnum(ns[i]) and ns[i]>=.25 else 0)+
                (5 if cpos[i]>=.95 else 4 if cpos[i]>=.85 else 2 if cpos[i]>=.72 else 0)+
                (5 if isnum(bodyr[i]) and bodyr[i]>=.70 else 4 if isnum(bodyr[i]) and bodyr[i]>=.50 else 2 if isnum(bodyr[i]) and bodyr[i]>=.25 else 0)+
                (8 if isnum(vr[i]) and 1.05<=vr[i]<=2.80 else 5 if isnum(vr[i]) and .75<=vr[i]<=3.50 else 0)+score_if(liq[i],4)+
                (3 if isnum(gapn[i]) and abs(gapn[i])<=.20 else 2 if isnum(gapn[i]) and abs(gapn[i])<=.45 else 0)+
                (5 if hot5[i] else 3 if hot3[i] else 0)+
                (5 if isnum(run10[i]) and run10[i]<=.70 else 3 if isnum(run10[i]) and run10[i]<=1.20 else 1 if isnum(run10[i]) and run10[i]<=1.80 else 0)+
                (5 if isnum(extn[i]) and extn[i]<=.70 else 3 if isnum(extn[i]) and extn[i]<=1.10 else 1 if isnum(extn[i]) and extn[i]<=1.60 else 0)+score_if(space60[i],5)+score_if(space120[i],5))
        sigc0=chard and cscore>=70
        prev5=sum(1 for x in sigc0_hist[max(0,len(sigc0_hist)-5):] if x)
        sigc=sigc0 and prev5==0
        sigc0_hist.append(sigc0)

        golden_stage='当日金叉' if f0[i] else '次日首次确认' if f1[i] else '第二日首次确认' if f2[i] else ''
        checks=[('无新鲜金叉',fresh[i]),('慢线状态失败',slowok[i]),('点火前位置失败',prepos[i]),('金叉未保持',isnum(e3[i]) and isnum(e21[i]) and e3[i]>e21[i]),('金叉未继续扩张',spup[i]),('均线张口过大',fgapok[i]),('收盘未站EMA21',isnum(e21[i]) and C[i]>e21[i]),('非阳线',C[i]>O[i]),('实体过弱',isnum(bodyr[i]) and bodyr[i]>=.25),('收盘位置过低',cpos[i]>=.72),('强度不足',isnum(ns[i]) and ns[i]>=.25),('无突破/强涨确认',brk5[i] or (isnum(ns[i]) and ns[i]>=.50)),('量比过低',isnum(vr[i]) and vr[i]>=.75),('量比过高',isnum(vr[i]) and vr[i]<=3.50),('近3日已高热',hot3[i]),('10日过热',runok[i]),('一字板',tradeok[i]),('EMA20乖离过热',isnum(extn[i]) and extn[i]<=1.60),('低开过大',isnum(gapn[i]) and gapn[i]>=-.50),('高开过大',isnum(gapn[i]) and gapn[i]<=.75)]
        reasons='；'.join(label for label,ok in checks if not ok)
        out.append({**r,'model_a_score':ascore,'model_a_pass':siga,'model_b_score':bscore,'model_b_pass':sigb,'model_c_score':cscore,'model_c_pass':sigc,'golden_stage':golden_stage,'final_pass':siga or sigb or sigc,'VR':vr[i],'NS':ns[i],'CPOS':cpos[i],'BODYR':bodyr[i],'PREEXTF':preext[i],'SLOPEF':slope[i],'FGAP':fgap[i],'EXTN':extn[i],'golden_fail_reasons':reasons})
    return out

def fmt(v):
    if v is None: return ''
    if isinstance(v,bool): return '1' if v else '0'
    if isinstance(v,date): return v.isoformat()
    if isinstance(v,float): return '' if not math.isfinite(v) else f'{v:.10g}'
    return str(v)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--date'); ap.add_argument('--output-dir',default='.'); ap.add_argument('--top',type=int,default=50)
    args=ap.parse_args(); groups=load_csv(args.csv); allrows=[]
    for _,rows in groups.items(): allrows.extend(compute(rows))
    if not allrows: raise SystemExit('无有效数据')
    target=parse_date(args.date) if args.date else max(r['date'] for r in allrows)
    cur=[r for r in allrows if r['date']==target]
    if not cur: raise SystemExit(f'目标日无数据: {target}')
    cur.sort(key=lambda r:(bool(r['final_pass']),bool(r['model_c_pass']),r['model_c_score'],r['model_a_score'],r['model_b_score']),reverse=True)
    outdir=Path(args.output_dir); outdir.mkdir(parents=True,exist_ok=True)
    fields=['date','code','name','model_a_score','model_a_pass','model_b_score','model_b_pass','model_c_score','model_c_pass','golden_stage','final_pass','VR','NS','CPOS','BODYR','PREEXTF','SLOPEF','FGAP','EXTN','golden_fail_reasons']
    for fname,data in [('results.csv',cur[:args.top]),('golden_ignition_audit.csv',sorted(cur,key=lambda r:(bool(r['model_c_pass']),r['model_c_score']),reverse=True)[:args.top])]:
        with open(outdir/fname,'w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader();
            for r in data: w.writerow({k:fmt(r.get(k)) for k in fields})
    summary={'date':target.isoformat(),'stocks_on_date':len(cur),'final_pass':sum(bool(r['final_pass']) for r in cur),'model_a_pass':sum(bool(r['model_a_pass']) for r in cur),'model_b_pass':sum(bool(r['model_b_pass']) for r in cur),'model_c_pass':sum(bool(r['model_c_pass']) for r in cur),'confirmed_codes':[r['code'] for r in cur if r['final_pass']],'golden_codes':[r['code'] for r in cur if r['model_c_pass']]}
    (outdir/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
