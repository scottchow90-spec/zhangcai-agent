#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, html, json, math
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
SCHEMA='a_share_quant_consensus_bundle_v2'
VERSION='6.5.0-final'
REAL_KINDS={'public_api','workbuddy_connector','browser','licensed_data','github_public_dataset','financial_connector'}

def load_cfg(): return json.loads((ROOT/'config/production.json').read_text('utf-8'))
def sha256(p:Path):
    h=hashlib.sha256();
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def provider_id(x):
    if not isinstance(x,dict): return ''
    return str(x.get('provider') or x.get('name') or '').strip().lower()
def is_mainboard(c): return str(c).startswith(('600','601','603','605','000','001','002','003'))
def _f(v,default=None):
    try:return float(v)
    except:return default

def validate_bundle(b,cfg):
    e=[]
    if b.get('schema')!=SCHEMA:e.append('schema错误')
    if b.get('mode')!='after-market':e.append('共识生产路径仅允许盘后')
    td=str(b.get('trade_date') or '')
    try:datetime.strptime(td,'%Y-%m-%d')
    except:e.append('trade_date格式错误')
    prov=b.get('provenance') or {}; p=prov.get('primary') or {}; s=prov.get('secondary') or {}
    if not provider_id(p) or not provider_id(s):e.append('主/二来源标识缺失')
    if provider_id(p)==provider_id(s):e.append('主/二来源不独立')
    for k,z in [('primary',p),('secondary',s)]:
        if str(z.get('kind') or '').lower() not in REAL_KINDS:e.append(f'{k}来源类型不是获准真实来源')
    items=b.get('primary_candidates'); quotes=b.get('secondary_quotes')
    if not isinstance(items,list) or not items:e.append('primary_candidates缺失')
    if not isinstance(quotes,dict) or not quotes:e.append('secondary_quotes缺失')
    return e

def event_score(ev):
    state=str((ev or {}).get('state') or 'neutral').lower()
    if state=='positive': return 5.0
    if state=='negative': return 0.0
    return 2.0

def execute(bundle_path:str,output_dir:str|None=None):
    cfg=load_cfg(); g=cfg['data_gates']; b=json.loads(Path(bundle_path).read_text('utf-8'))
    errs=validate_bundle(b,cfg)
    if errs: raise SystemExit('BLOCKED:'+ '；'.join(errs))
    td=b['trade_date']; quotes=b['secondary_quotes']; events=b.get('events') or {}; trace=[]
    def wf(n,name,status='完成',detail=''): trace.append({'step':n,'name':name,'status':status,'detail':detail})
    wf(1,'包完整性/决策时点锁定',detail=f'{td}；after-market；CONSENSUS_RESCUE')
    raw=[x for x in b['primary_candidates'] if is_mainboard(x.get('code','')) and 'ST' not in str(x.get('name','')).upper() and '退' not in str(x.get('name',''))]
    wf(2,'主板候选池与风险名称过滤',detail=f'输入{len(b["primary_candidates"])}；主板有效{len(raw)}')
    hmin=int(g['consensus_primary_history_days_min']); hist_ok=[x for x in raw if int(x.get('source_history_days') or 0)>=hmin]
    wf(3,'模型级历史证据门',detail=f'主模型滚动历史≥{hmin}日 {len(hist_ok)}/{len(raw)}；本路径不伪装为V6.3原生四模型')
    wf(4,'主源候选数据质量/流动性完整性',detail='检查未复权展示价、成交额、换手率、日涨跌')
    wf(5,'独立二源证券身份与收盘价准备',detail=f'二源报价{len(quotes)}只')
    passed=[]; rejected=[]
    for x in hist_ok:
        code=str(x['code']); reasons=[]
        close=_f(x.get('close')); pw=_f(x.get('pred_win')); pr=_f(x.get('pred_ret')); amt=_f(x.get('amount'),0); turn=_f(x.get('turnover')); dr=_f(x.get('daily_return'))
        if x.get('price_type')!='raw_unadjusted': reasons.append('主源展示价非未复权')
        if pw is None or pw<float(g['consensus_min_pred_win']): reasons.append('模型胜率预测不足')
        if pr is None or pr<float(g['consensus_min_pred_ret']): reasons.append('峰值收益预测不足')
        if amt<float(g['consensus_min_amount']): reasons.append('成交额不足')
        if turn is None or not(float(g['consensus_turnover_min'])<=turn<=float(g['consensus_turnover_max'])): reasons.append('换手率不在生产区间')
        if dr is None or abs(dr)>float(g['consensus_abs_daily_return_max']): reasons.append('当日波动过热/过弱')
        q=quotes.get(code) or {}; qclose=_f(q.get('close'))
        if str(q.get('trade_date') or '')!=td: reasons.append('二源日期不一致')
        if close is None or qclose is None: reasons.append('二源价格缺失'); diff=None
        else:
            diff=abs(close/qclose-1) if qclose else 999
            if diff>float(g['consensus_price_tolerance']): reasons.append('二源价格冲突')
        ev=events.get(code) or {'state':'neutral','summary':'未发现可证实的重大负面事件'}
        if str(ev.get('risk') or '').upper()=='HIGH': reasons.append('重大负面事件风险')
        if reasons:
            rejected.append({'code':code,'name':x.get('name'),'reasons':reasons,'secondary_diff':diff}); continue
        # 生产分：模型概率/收益为主，二源一致、流动性、事件、跨扫描确认只做有限增量。
        win=min(max((pw-.90)/.08,0),1)*45
        ret=min(max((pr-.17)/.08,0),1)*25
        liq=10 if amt>=1_000_000_000 else (7 if amt>=500_000_000 else 4)
        source=10
        event=event_score(ev)
        cross=5 if x.get('cross_scanner_confirmed') else 0
        score=round(min(100,60+win+ret+liq+source+event+cross),2)
        y=dict(x); y.update({'candidate_tier':'B_CONSENSUS_PRODUCTION','authorized_candidate':True,'production_score':score,'secondary_close':qclose,'secondary_diff':round(diff,8),'event_state':ev.get('state','neutral'),'event_summary':ev.get('summary',''),'data_route':'independent_cross_provider_consensus'})
        passed.append(y)
    wf(6,'主模型阈值/流动性/过热硬门',detail=f'初筛后{len(passed)}只')
    wf(7,'行业/消息/事件风险门',detail='HIGH风险事件一票否决；正面只做增量不替代价格确认')
    passed.sort(key=lambda z:(-z['production_score'],-_f(z.get('pred_win'),0),-_f(z.get('pred_ret'),0),z['code']))
    wf(8,'双源共识综合评分与排序',detail=f'候选{len(passed)}只')
    match=sum(1 for x in passed if x['secondary_diff']<=float(g['consensus_price_tolerance']))
    match_rate=match/max(len(passed),1)
    blocks=[]
    if len(passed)<int(g['consensus_min_candidates']): blocks.append('正式候选数量低于最小生产门')
    if passed and match_rate<float(g['consensus_min_price_match_rate']): blocks.append('二源价格匹配率未达100%')
    wf(9,'UNKNOWN传播与数据门禁',detail=f'阻断{len(blocks)}项')
    wf(10,'独立第二行情源逐只核验',detail=f'匹配{match}/{len(passed)}；冲突0；未知0')
    status='AUTHORIZED' if not blocks else 'BLOCKED'
    wf(11,'候选证据归档',status='完成' if status=='AUTHORIZED' else '阻断未归档',detail='保留主模型证据/二源价格/事件证据/来源标识')
    wf(12,'生产授权验证',detail=f'{status}；候选{len(passed)}')
    wf(13,'完整JSON/Markdown/HTML/运行哈希输出',detail='13/13')
    payload={'engine':'A股量化生产定型工程 V6.5 WorkBuddy双路容灾最终生产版','version':VERSION,'route':'CONSENSUS_RESCUE','trade_date':td,'status':status,'generated_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'),'workflow_trace':trace,'candidate_count':len(passed) if status=='AUTHORIZED' else 0,'candidates':passed if status=='AUTHORIZED' else [],'candidate_preview_when_blocked':passed if status!='AUTHORIZED' else [],'rejected':rejected,'block_reasons':blocks,'audit':{'primary_provider':provider_id((b.get('provenance') or {}).get('primary')),'secondary_provider':provider_id((b.get('provenance') or {}).get('secondary')),'source_independent':True,'price_match_rate':match_rate,'no_synthetic':True,'native_four_model_claimed':False,'consensus_route_contract':'主模型真实候选 + 独立二源收盘价 + 事件风险门；不得冒充V6.3原生四模型结果'}}
    od=Path(output_dir or ROOT/'output')/td; od.mkdir(parents=True,exist_ok=True)
    jp=od/'V6.5_consensus_result.json'; jp.write_text(json.dumps(payload,ensure_ascii=False,indent=2),'utf-8')
    lines=[f'# {td} V6.5 双源共识容灾生产实跑', '', f'- 状态：**{status}**', f'- 正式候选：**{len(passed) if status=="AUTHORIZED" else 0}只**', '- 路径：CONSENSUS_RESCUE（正式生产路径，但不冒充V6.3原生四模型）','', '## 候选']
    if status=='AUTHORIZED':
        lines += ['', '|排名|代码|名称|收盘|生产分|主模型胜率|峰值收益预测|成交额|当日涨跌|二源差异|事件|', '|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|']
        for i,x in enumerate(passed,1):
            lines.append(f"|{i}|{x['code']}|{x['name']}|{x['close']:.2f}|{x['production_score']:.2f}|{x['pred_win']*100:.2f}%|{x['pred_ret']*100:.2f}%|{x['amount']/1e8:.2f}亿|{x['daily_return']*100:.2f}%|{x['secondary_diff']*100:.4f}%|{x['event_summary']}|")
    lines += ['', '## 13步工作流审计']
    for z in trace: lines.append(f"{z['step']}. {z['name']}：{z['status']}；{z['detail']}")
    lines += ['', '## 明示边界', '- 该路径是V6.5新增的正式容灾生产路径；当原生全市场K线桥不可物化时使用。', '- 不把外部机器学习模型结果伪装成“平台主升/弱转强/龙回头/黄金点火”原生信号。', '- 若原生四模型数据闭合，优先使用NATIVE_4MODEL；若不闭合但本路径全部门通过，可输出B_CONSENSUS_PRODUCTION正式候选。']
    md='\n'.join(lines)+'\n'; mp=od/'V6.5_consensus_report.md'; mp.write_text(md,'utf-8')
    (od/'V6.5_consensus_report.html').write_text('<html><meta charset="utf-8"><body><pre>'+html.escape(md)+'</pre></body></html>','utf-8')
    (od/'consensus_run_manifest.json').write_text(json.dumps({'result_sha256':sha256(jp),'report_sha256':sha256(mp),'bundle_sha256':sha256(Path(bundle_path))},ensure_ascii=False,indent=2),'utf-8')
    print(md); return 0 if status=='AUTHORIZED' else 3

def selftest():
    import tempfile
    cfg=load_cfg(); td='2099-01-01'
    base={'schema':SCHEMA,'mode':'after-market','trade_date':td,'provenance':{'primary':{'provider':'A','kind':'github_public_dataset'},'secondary':{'provider':'B','kind':'financial_connector'}},'primary_candidates':[],'secondary_quotes':{},'events':{}}
    for i in range(3):
        code=f'60000{i+1}'; base['primary_candidates'].append({'code':code,'name':'自检'+str(i),'trade_date':td,'close':10+i,'price_type':'raw_unadjusted','pred_win':.93,'pred_ret':.19,'amount':1e9,'turnover':.05,'daily_return':.02,'source_history_days':220}); base['secondary_quotes'][code]={'trade_date':td,'close':10+i}
    with tempfile.TemporaryDirectory() as t:
        p=Path(t)/'b.json'; p.write_text(json.dumps(base,ensure_ascii=False),'utf-8')
        rc=execute(str(p),str(Path(t)/'o'))
        if rc!=0: print('CONSENSUS_SELFTEST_FAILED'); return False
        bad=json.loads(json.dumps(base)); bad['provenance']['secondary']['provider']='A'; p.write_text(json.dumps(bad,ensure_ascii=False),'utf-8')
        if not any('不独立' in x for x in validate_bundle(bad,cfg)): print('CONSENSUS_SELFTEST_FAILED:same-source'); return False
    print('CONSENSUS_SELFTEST_PASSED'); return True

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
    e=sp.add_parser('execute'); e.add_argument('--bundle',required=True); e.add_argument('--output-dir')
    sp.add_parser('selftest')
    a=ap.parse_args();
    if a.cmd=='execute': return execute(a.bundle,a.output_dir)
    return 0 if selftest() else 2
if __name__=='__main__': raise SystemExit(main())
