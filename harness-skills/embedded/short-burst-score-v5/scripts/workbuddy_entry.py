#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, platform, subprocess, sys
from pathlib import Path, PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from lhbpost.core import analyze_snapshot, load_config, load_json

REQUIRED=[
 'SKILL.md','scripts/workbuddy_entry.py','scripts/build_history_model.py','scripts/lhbpost/core.py',
 'scripts/lhbpost/features.py','scripts/lhbpost/market_features.py','scripts/lhbpost/seat_quality.py',
 'scripts/lhbpost/candidate_pipeline.py','scripts/lhbpost/snapshot_pipeline.py','scripts/lhbpost/research.py',
 'scripts/lhbpost/data/normalized_store.py','scripts/lhbpost/data/tushare_postmarket.py','scripts/lhbpost/data_audit.py',
 'templates/default-config.json','templates/snapshot-example.json','templates/labeled-events-example.csv',
 'references/deep-audit-merge-report.md','references/data-contract.md','references/research-validation.md',
 'references/workbuddy-usage.md','references/package-index.json'
]

def _sha(p):
    h=hashlib.sha256();
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''):h.update(c)
    return h.hexdigest()

def verify():
    missing=[x for x in REQUIRED if not (ROOT/x).exists()]
    if missing:
        print('VERIFY_FAILED');[print('MISSING',x) for x in missing];return 2
    errs=[]; seen=set()
    try:
        idx=json.loads((ROOT/'references/package-index.json').read_text(encoding='utf-8'))
        items=idx.get('files')
        if not isinstance(items,list) or not items or idx.get('file_count')!=len(items):
            raise ValueError('清单为空或文件数不符')
        for it in items:
            rel=it['path']; path=PurePosixPath(rel)
            if path.is_absolute() or '..' in path.parts or ':' in rel or '\\' in rel or rel!=path.as_posix():
                raise ValueError('非法清单路径:'+rel)
            if rel in seen: raise ValueError('重复清单路径:'+rel)
            seen.add(rel); p=ROOT/rel
            if not p.resolve().is_relative_to(ROOT.resolve()): raise ValueError('清单路径越界:'+rel)
            if not p.is_file():errs.append('missing:'+rel);continue
            if p.stat().st_size!=it['size'] or _sha(p)!=it['sha256']:errs.append('hash/size:'+rel)
        expected={p.relative_to(ROOT).as_posix() for folder in ('scripts','references','templates','agents')
                  for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts and p.suffix!='.pyc'}
        expected.add('SKILL.md'); expected.discard('references/package-index.json')
        if seen!=expected: errs.append('manifest-set:'+','.join(sorted(seen^expected)))
        if not (set(REQUIRED)-{'references/package-index.json'})<=seen: errs.append('manifest-required-omitted')
    except (ValueError,KeyError,TypeError,OSError) as ex:
        errs.append('manifest:'+str(ex))
    if errs:
        print('VERIFY_FAILED');[print(x) for x in errs];return 3
    print('VERIFY_OK');return 0

def doctor():
    print('WorkBuddy A股盘后龙虎榜技能 V5.0 短线爆发力评分版诊断')
    print('Python:',sys.version.split()[0]);print('Platform:',platform.platform());print('Root:',ROOT)
    print('Daily snapshot engine: standard library only')
    missing=[]
    for m in ('pandas','numpy'):
        try:__import__(m)
        except Exception:missing.append(m)
    if missing:print('RAW_PIPELINE_WARN: 原始数据管线缺少可选依赖 '+','.join(missing))
    else:print('Raw pipeline dependencies: OK (pandas/numpy)')
    try:__import__('tushare');print('Tushare downloader: available')
    except Exception:print('Tushare downloader: optional/unavailable')
    print('DOCTOR_OK');return 0

def _fmt_pct(v):
    try:return f"{float(v):.2%}"
    except Exception:return "—"

def render_md(r):
    lines=[f"# {r['trade_date']} 盘后短线爆发力评分结果",'',
           f"- 数据截止：{r['as_of']}",f"- 数据管线：{r.get('pipeline','—')}",
           f"- 市场状态：**{r['market_state']}**",f"- 市场闸门：{r.get('market_gate_method','—')}",
           f"- 候选等级上限：**{r['candidate_level_cap']}**",
           f"- 历史模型：{r['history_model'].get('status')} — {r['history_model'].get('message','')}",
           f"- 未来数据检查：{r.get('lookahead_check','—')}",'']
    lines += ['## 一、工作流执行审计','', '| 环节 | 状态 | 说明 |','|---|---|---|']
    for x in r.get('workflow_trace') or []:
        lines.append(f"| {x.get('step','')} | {x.get('status','')} | {x.get('detail','')} |")
    audit=r.get('raw_data_audit') or {}
    lines += ['', '### 原始数据审计', '']
    if audit:
        lines.append(f"- 通过：{audit.get('passed')}")
        warns=audit.get('warnings') or []
        lines.append('- 警告：'+('；'.join(str(x) for x in warns) if warns else '无'))
    else:
        lines.append('- 未提供原始数据审计证据：本次结果已按降级输入处理。')
    cov=r.get('coverage') or {}
    lines += ['', '### 数据覆盖', '']
    if cov:
        for k,v in cov.items():lines.append(f"- {k}：{v}")
    else:lines.append('- 无完整覆盖元数据：已按降级快照处理。')
    lines += ['', '## 二、市场总闸门依据', '']
    for x in r.get('market_reasons') or []:lines.append(f"- {x}")
    lines += ['', '## 三、全候选排序', '',
              '| 排名 | 股票 | 爆发力评分 | 技术 | 结构 | 资金 | 弹性 | 强势阶段 | 地位 | 透支 | 结论 |',
              '|---:|---|---:|---:|---:|---:|---:|---|---|---|---|']
    for x in r['results']:
        comp=x.get('score_components') or {}
        lines.append(f"| {x['rank']} | {x['name']}({x['code']}) | **{x.get('short_burst_score','—')}** | {comp.get('技术动量','—')} | {comp.get('结构地位','—')} | {comp.get('资金质量','—')} | {comp.get('资金弹性','—')} | {x['stage']} | {x['position']} | {x['overheat']} | **{x['conclusion']}** |")
    lines += ['', '## 四、逐股完整证据链', '']
    for x in r['results']:
        lines += [f"### {x['rank']}. {x['name']}（{x['code']}）",'',
                  f"- 结论：**{x['conclusion']}**；证据等级：{x.get('evidence_grade','—')}",
                  f"- 短线爆发力评分：**{x.get('short_burst_score','—')} / 100**（风险前={x.get('score_before_risk','—')}，风险扣分={x.get('score_risk_penalty','—')}；不是未经校准的上涨概率）",
                  f"- 六维分项："+'；'.join(f"{k}={v}" for k,v in (x.get('score_components') or {}).items()),
                  f"- 阶段/地位：{x['stage']} / {x['position']}",
                  f"- 上下文：{x.get('context_basis','—')} {x.get('context_name','') or ''}；状态={x['sector_state']}",
                  f"- 龙虎榜：{x['lhb_role']}；价格透支={x['overheat']}；事件风险级别={x.get('event_risk_level',0)}"]
        pos=x.get('positive_evidence') or [];neg=x.get('negative_evidence') or [];hard=x.get('hard_reject_reasons') or []
        lines.append('- 正向证据：'+('；'.join(pos) if pos else '无可确认正向证据'))
        lines.append('- 负向/限制：'+('；'.join(neg) if neg else '无'))
        if hard:lines.append('- 硬否决：'+'；'.join(hard))
        au=x.get('audit') or {}
        for title,key in [('板块/题材依据','context_reasons'),('价格透支依据','overheat_reasons'),('龙虎榜依据','lhb_reasons'),('盘后事件依据','event_reasons')]:
            vals=au.get(key) or []
            lines.append(f"- {title}："+('；'.join(str(z) for z in vals) if vals else '无'))
        hm=x.get('history_stats') or {}
        if hm.get('available'):
            hparts=[f"样本={hm.get('sample_n')}",f"可信度={hm.get('confidence')}",f"桶强弱={hm.get('strength','—')}"]
            for k,n in [('t1_positive_rate','次日正收益率'),('t3_positive_rate','3日正收益率'),('t5_ge5_rate','5日最高涨幅≥5%概率'),('t5_ge5_wilson_lower90','5日爆发率90%下界'),('avg_return_t5','5日平均收益'),('benchmark_excess_t5','5日相对基准超额')]:
                if k in hm:hparts.append(f"{n}={_fmt_pct(hm[k])}")
            lines.append('- 历史样本外统计：'+'；'.join(hparts))
        else:lines.append('- 历史样本外统计：不可用/样本不足，不输出概率。')
        lines.append('')
    policy=str(r.get('ranking_policy','爆发力评分')).rstrip('。；; ')
    lines += ['## 五、输出边界','',
              f"> {policy}。评分用于同日候选相对比较，不等于上涨概率；没有通过滚动样本外生产验收时禁止编造胜率；缺失关键数据时必须显式降级。"]
    return '\n'.join(lines)

def analyze_cmd(a):
    data=load_json(a.input);cfg=load_config(a.config) if a.config else load_config();model=load_json(a.history_model) if a.history_model else None
    r=analyze_snapshot(data,cfg,model);txt=json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False) if a.format=='json' else render_md(r)
    if a.output:Path(a.output).write_text(txt,encoding='utf-8');print(a.output)
    else:print(txt)
    return 0

def prepare_cmd(a):
    from lhbpost.data import NormalizedStore
    from lhbpost.snapshot_pipeline import build_snapshot
    from lhbpost.data_audit import audit_raw_data
    audit_output=getattr(a,'audit_output',None)
    try:
        audit=audit_raw_data(a.data_root,require_end=a.trade_date)
    except Exception as exc:
        if audit_output:
            Path(audit_output).write_text(json.dumps({'passed':False,'errors':[type(exc).__name__+':'+str(exc)],'warnings':[],'stats':{}},ensure_ascii=False,indent=2),encoding='utf-8')
        raise
    if audit_output:
        Path(audit_output).write_text(json.dumps({'passed':audit.passed,'errors':list(audit.errors),'warnings':list(audit.warnings),'stats':audit.stats},ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    if not audit.passed:
        raise ValueError('原始数据审计失败，禁止跳过步骤生成快照: '+'; '.join(audit.errors))
    st=NormalizedStore(a.data_root,strict=True)
    top_list=st.top_list();selected_codes=getattr(a,'selected_codes',None);extra={}
    if selected_codes is not None:
        from lhbpost.selected_workflow import verify_billboard_day
        proof=verify_billboard_day(a.data_root,a.trade_date,top_list,output=getattr(a,'billboard_audit_output',None))
        top_list.attrs['verified_complete_dates']=proof['verified_complete_dates']
        extra['selected_codes']=selected_codes
    snap=build_snapshot(trade_date=a.trade_date,as_of=a.as_of,daily=st.daily(),daily_basic=st.daily_basic(),top_list=top_list,top_inst=st.top_inst(),
        sw_members=st.sw_members(),stock_basic=st.stock_basic(),st_status=st.st(),limits=st.limits(),index_daily=st.index_daily(),adj_factor=st.adj_factor(),
        historical_basic=st.historical_basic(),event_features=st.event_features(),theme_members=st.theme_members(),**extra)
    # “有事件源但T日无事件”与“根本没事件源”必须区分；覆盖状态以原始数据审计为准。
    if audit.stats.get('coverage_event_features'):
        snap.setdefault('coverage',{})['event_feed']=True
        for x in snap.get('workflow_trace') or []:
            if x.get('step')=='盘后事件' and x.get('status')=='数据源缺失':
                x['status']='完成（当日无事件）';x['detail']='事件源已审计；截至as_of无匹配事件，按中性事实处理，不等同于缺数据源'
    snap['raw_data_audit']={'passed':audit.passed,'warnings':list(audit.warnings),'stats':audit.stats}
    snap['pipeline']='raw-postmarket-v5.0-audited'
    trace=list(snap.get('workflow_trace') or [])
    trace.insert(0,{'step':'原始数据审计','status':'完成','detail':'逐日全文件表头/主键/日期/覆盖/错误痕迹已审计；空龙虎榜日要求空快照文件'})
    snap['workflow_trace']=trace
    from lhbpost.core import validate_snapshot
    errors=validate_snapshot(snap)
    if errors: raise ValueError('快照校验失败: '+'; '.join(errors))
    Path(a.output).write_text(json.dumps(snap,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8');print(a.output);return 0

def audit_cmd(a):
    from lhbpost.data_audit import audit_raw_data
    r=audit_raw_data(a.data_root,require_end=a.require_end)
    print(json.dumps({'passed':r.passed,'errors':r.errors,'warnings':r.warnings,'stats':r.stats},ensure_ascii=False,indent=2));return 0 if r.passed else 5

def selftest():
    cmd=[sys.executable,str(ROOT/'scripts/tests/run_tests.py')]
    return subprocess.call(cmd,cwd=ROOT)

def main():
    p=argparse.ArgumentParser(description='A股盘后短线爆发力评分系统 V5.0（纯盘后、完整工作流）');sp=p.add_subparsers(dest='cmd',required=True)
    sp.add_parser('verify');sp.add_parser('doctor');sp.add_parser('selftest')
    a=sp.add_parser('analyze');a.add_argument('--input',required=True);a.add_argument('--output');a.add_argument('--format',choices=['json','markdown'],default='markdown');a.add_argument('--config');a.add_argument('--history-model')
    q=sp.add_parser('prepare-snapshot');q.add_argument('--data-root',required=True);q.add_argument('--trade-date',required=True);q.add_argument('--as-of',required=True);q.add_argument('--output',required=True)
    d=sp.add_parser('audit-data');d.add_argument('--data-root',required=True);d.add_argument('--require-end')
    args=p.parse_args()
    return {'verify':lambda:verify(),'doctor':lambda:doctor(),'selftest':lambda:selftest(),'analyze':lambda:analyze_cmd(args),'prepare-snapshot':lambda:prepare_cmd(args),'audit-data':lambda:audit_cmd(args)}[args.cmd]()
if __name__=='__main__':raise SystemExit(main())
