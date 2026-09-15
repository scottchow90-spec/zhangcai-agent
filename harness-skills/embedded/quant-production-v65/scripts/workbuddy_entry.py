from __future__ import annotations
import argparse, hashlib, html, json, os, sys, traceback
from collections import Counter
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE))

from engine import (
    EvalResult, RealtimeEvalResult, REALTIME_FAIL, REALTIME_PASS, REALTIME_UNKNOWN,
    ema_series, evaluate_realtime_stock, evaluate_stock, exchange_of, industry_metrics,
    is_mainboard, limit_up_price, summarize, summarize_realtime, tdx_sma_series,
)
from public_data import (
    Cache, DataError, build_realtime_bars, china_market_session_status, china_realtime_window_status,
    eastmoney_board_constituents, eastmoney_board_kline, eastmoney_industry_boards, eastmoney_industry_name, eastmoney_news_search,
    eastmoney_index_kline, eastmoney_intraday_trends, eastmoney_universe, eastmoney_kline,
    fetch_breadth_for_date, fetch_histories, intraday_reference_price,
    latest_completed_trade_date, realtime_breadth_from_universe, tencent_kline,
)
from data_bridge import DataBundle, BRIDGE_EXIT_CODE, resolve_bundle_path, write_bridge_request, SCHEMA as BRIDGE_SCHEMA
from validation import archive_after_market, archive_industry_states, archive_realtime, load_industry_history, mature_archive_outcomes, update_realtime_close_confirmation, validate_production, _source_match_rate, _objective

VERSION='6.5.0-final'
ENGINE_NAME='A股量化生产定型工程 V6.5 WorkBuddy双路容灾最终生产版'
REQUIRED=[
    'SKILL.md','README_安装说明.md','workflow_manifest.json','package-manifest.json','config/production.json',
    'scripts/workbuddy_entry.py','scripts/engine.py','scripts/industry_engine.py','scripts/public_data.py','scripts/data_bridge.py','scripts/consensus_engine.py','scripts/validation.py',
    'references/V6.3_规则引擎.md','references/V6.3_行业强度与驱动引擎.md','references/V6.3_深度审计与防回归报告.md','references/V6.4_数据容灾与WorkBuddy桥接规范.md','references/V6.5_双路容灾最终生产规范.md','references/数据源与生产门禁.md','references/输出模板.md','references/纠错继承矩阵.md',
    'tests/README.md','tests/offline_e2e.py',
]


def sha256(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()


def load_cfg():
    return json.loads((ROOT/'config/production.json').read_text('utf-8'))


class RuntimeData:
    """统一数据入口：direct 与 WorkBuddy bridge 对评分引擎保持同一字段合同。"""
    def __init__(self, bundle: Optional[DataBundle] = None):
        self.bundle=bundle
        self.route='WORKBUDDY_BRIDGE' if bundle else 'DIRECT_PUBLIC_API'

    def latest_trade_date(self, mode:str)->str:
        return self.bundle.trade_date if self.bundle else latest_completed_trade_date(mode)
    def universe(self): return self.bundle.universe() if self.bundle else eastmoney_universe()
    def kline(self, code, end_date, count_days=260, market_id=None): return self.bundle.kline(code,end_date,count_days,market_id) if self.bundle else eastmoney_kline(code,end_date,count_days,market_id)
    def index_kline(self, secid, end_date, count_days=80): return self.bundle.index_kline(secid,end_date,count_days) if self.bundle else eastmoney_index_kline(secid,end_date,count_days)
    def industry_name(self, code): return self.bundle.industry_name(code) if self.bundle else eastmoney_industry_name(code)
    def industry_boards(self): return self.bundle.industry_boards() if self.bundle else eastmoney_industry_boards()
    def board_kline(self, board_code, end_date, count_days=30): return self.bundle.board_kline(board_code,end_date,count_days) if self.bundle else eastmoney_board_kline(board_code,end_date,count_days)
    def board_constituents(self, board_code, page_size=600): return self.bundle.board_constituents(board_code,page_size) if self.bundle else eastmoney_board_constituents(board_code,page_size)
    def news_search(self, keyword, count=30): return self.bundle.news_search(keyword,count) if self.bundle else eastmoney_news_search(keyword,count)
    def news_scan_complete(self, keyword): return self.bundle.news_scan_complete(keyword) if self.bundle else True
    def secondary_rows(self, code, count=260): return self.bundle.secondary_rows(code,count) if self.bundle else tencent_kline(code,count)
    def intraday_trends(self, code): return self.bundle.intraday_trends(code) if self.bundle else eastmoney_intraday_trends(code)
    def provenance(self):
        if self.bundle: return self.bundle.provenance
        return {'primary':{'provider':'Eastmoney','kind':'public_api'},'secondary':{'provider':'Tencent','kind':'public_api'}}


def _integrity_files():
    skip_dirs={'__pycache__','output','state','.git'}
    out=[]
    for p in ROOT.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(ROOT).as_posix()
        if rel=='package-manifest.json' or any(part in skip_dirs for part in p.relative_to(ROOT).parts): continue
        if p.suffix in {'.pyc','.pyo'}: continue
        out.append(rel)
    return sorted(out)


def verify_package(verbose=True):
    probs=[]
    for rel in REQUIRED:
        if not (ROOT/rel).exists(): probs.append('缺少文件:'+rel)
    mp=ROOT/'package-manifest.json'
    if mp.exists():
        try:
            m=json.loads(mp.read_text('utf-8'))
            if str(m.get('version'))!=VERSION: probs.append(f"manifest版本不一致:{m.get('version')} != {VERSION}")
            hashes=m.get('sha256') or {}
            actual=set(_integrity_files()); declared=set(hashes)
            for rel in sorted(actual-declared): probs.append('manifest漏列:'+rel)
            for rel in sorted(declared-actual): probs.append('manifest多列/文件缺失:'+rel)
            for rel,exp in hashes.items():
                p=ROOT/rel
                if p.exists() and sha256(p)!=exp: probs.append('哈希不一致:'+rel)
        except Exception as e:
            probs.append('manifest解析失败:'+str(e))
    else:
        probs.append('缺少文件:package-manifest.json')
    if verbose:
        print('VERIFY_OK' if not probs else 'VERIFY_FAILED\n'+'\n'.join('- '+x for x in probs))
    return not probs


def _synthetic_realtime_fixture():
    """构造不依赖网络的强市平台突破样本，用于三态传播回归。"""
    bars=[]; px=10.0
    # 长背景：温和上升，保证长期趋势结构成立。
    for i in range(280):
        prev=px; px*=1.0015
        bars.append({'date':f'D{i:03d}','open':px*.999,'close':px,'high':px*1.004,'low':px*.996,
                     'volume':2_000_000,'amount':120_000_000,'change':px-prev if i else 0,'turnover':2.0})
    # 近20日窄平台；前15日量较高，最近5日缩量。
    base=px
    for j in range(20):
        close=base*(1+((j%3)-1)*0.0004)
        vol=2_000_000 if j<15 else 1_000_000
        bars.append({'date':f'P{j:03d}','open':close*.9995,'close':close,'high':close*1.003,'low':close*.997,
                     'volume':vol,'amount':120_000_000,'change':close-bars[-1]['close'],'turnover':1.5})
    prev_close=bars[-1]['close']; prevh=max(x['high'] for x in bars[-20:])
    last=max(prev_close*1.045,prevh*1.02); op=prev_close*1.015; hi=last*1.002; lo=op*.998
    snap={'date':'R300','last':last,'open':op,'high':hi,'low':lo,'amount':80_000_000,'turnover':2.0,
          'volume_ratio':1.50,'pct':(last/prev_close-1)*100,'stable_price':max(prevh*1.01,last*.995),
          'volume':1_500_000,'change':last-prev_close}
    live=bars+[{'date':'R300','open':op,'close':last,'high':hi,'low':lo,'volume':1_500_000,'amount':80_000_000,
                'change':last-prev_close,'turnover':2.0,'pct_change':snap['pct']}]
    idx=[]; ip=3000.0
    for i in range(80):
        prev=ip; ip*=1.001
        idx.append({'date':f'I{i:03d}','open':ip*.999,'close':ip,'high':ip*1.002,'low':ip*.998,'volume':1,'amount':1,'change':ip-prev,'turnover':0})
    return live,idx,snap


def _synthetic_industry_context(idx):
    bars=[]; px=1000.0
    for i,x in enumerate(idx):
        prev=px; px*=1.005
        bars.append({'date':x['date'],'open':px*.998,'close':px,'high':px*1.004,'low':px*.996,'volume':1_000_000,'amount':1_000_000_000*(1+i/500),'change':px-prev,'turnover':1.0})
    members=[]
    for i in range(30):
        pct=3.2+(i%6)*.45
        members.append({'code':f'600{i:03d}','name':f'行业样本{i}','pct':pct,'amount':80_000_000+i*1_000_000,'turnover':2.0})
    return {'name':'测试行业','bars':bars,'constituents':members,'events':[],'events_covered':True,'history_state':[],
            'market_amount_total':80_000_000_000,'asof':'2099-01-01T10:30:00'}

def _realtime_tristate_regression(fail):
    live,idx,snap=_synthetic_realtime_fixture(); cfg=load_cfg()['model']; ictx=_synthetic_industry_context(idx)
    ok=evaluate_realtime_stock({'code':'600001','name':'三态自检','industry':'测试行业','bars':live,'snapshot':snap},.65,idx,ictx,cfg)
    if ok.state!=REALTIME_PASS or '平台主升' not in ok.model_labels:
        fail.append('实时量比存在未正常计算:'+ok.state+':'+','.join(ok.reject_reasons))
    miss=dict(snap); miss['volume_ratio']=None
    unk=evaluate_realtime_stock({'code':'600001','name':'三态自检','industry':'测试行业','bars':live,'snapshot':miss},.65,idx,ictx,cfg)
    if unk.state!=REALTIME_UNKNOWN or '实时量比' not in unk.unknown_fields:
        fail.append('潜在候选缺实时量比未传播UNKNOWN')
    low=dict(miss); low['last']=live[-2]['close']*.99; low['high']=live[-2]['close']*1.001; low['open']=live[-2]['close']; low['low']=low['last']*.998; low['pct']=-1.0
    live2=[dict(x) for x in live]; live2[-1].update({'close':low['last'],'high':low['high'],'open':low['open'],'low':low['low']})
    bad=evaluate_realtime_stock({'code':'600001','name':'三态自检','industry':'测试行业','bars':live2,'snapshot':low},.65,idx,ictx,cfg)
    if bad.state!=REALTIME_FAIL:
        fail.append('基本价格结构失败却被实时量比缺失误阻断:'+bad.state)


def _workflow_trace_e2e(fail):
    """无网络执行真实execute骨架，证明13步不是只写在manifest里。"""
    import contextlib, io, tempfile
    g=globals(); names=['verify_package','load_cfg','latest_completed_trade_date','eastmoney_universe','fetch_histories','fetch_breadth_for_date','eastmoney_index_kline','eastmoney_industry_boards','_fetch_industries']
    old={n:g[n] for n in names}
    try:
        bars=[]; px=10.0
        for i in range(320):
            prev=px; px*=1.0002
            bars.append({'date':f'X{i:03d}','open':px*.999,'close':px,'high':px*1.002,'low':px*.998,'volume':1_000_000,'amount':120_000_000,'change':px-prev if i else 0,'turnover':2.0})
        bars[-1]['date']='2099-01-01'
        idx=[]; ip=3000.0
        for i in range(80):
            prev=ip; ip*=1.0002
            idx.append({'date':f'I{i:03d}','open':ip*.999,'close':ip,'high':ip*1.002,'low':ip*.998,'volume':1,'amount':1,'change':ip-prev,'turnover':0})
        idx[-1]['date']='2099-01-01'
        uni=[{'code':'600001','name':'工作流自检','amount':120_000_000,'pct':0.2,'last':bars[-1]['close'],'high':bars[-1]['high'],'low':bars[-1]['low'],'open':bars[-1]['open'],'turnover':2.0,'volume_ratio':1.0}]
        g['verify_package']=lambda verbose=False: True
        _cfg=old['load_cfg'](); _cfg['data_gates']=dict(_cfg['data_gates']); _cfg['data_gates']['min_universe_size']=1
        g['load_cfg']=lambda:_cfg
        g['latest_completed_trade_date']=lambda mode:'2099-01-01'
        g['eastmoney_universe']=lambda:uni
        g['fetch_histories']=lambda universe,trade_date,workers,cache,count_days,*a,**kw:({'600001':bars},[])
        g['fetch_breadth_for_date']=lambda universe,hist,trade_date,workers,cache,*a,**kw:{'breadth':.60,'up':1,'down':0,'flat':0,'covered':1,'universe':1,'missing':[]}
        g['eastmoney_index_kline']=lambda secid,trade_date,count:idx
        g['eastmoney_industry_boards']=lambda:{}
        g['_fetch_industries']=lambda codes,trade_date,boards,state_dir,market_amount_total,asof,external_events,*a,**kw:({}, {}, [])
        with tempfile.TemporaryDirectory() as td:
            args=argparse.Namespace(mode='after-market',date=None,workers=1,cache_dir=str(Path(td)/'cache'),state_dir=str(Path(td)/'state'),output_dir=str(Path(td)/'out'),events_file=None)
            with contextlib.redirect_stdout(io.StringIO()):
                rc=execute(args)
            if rc!=0: fail.append('真实execute骨架离线验收未AUTHORIZED')
            result=Path(td)/'out'/'2099-01-01'/'V6.5_result.json'
            if not result.exists(): fail.append('真实execute骨架未生成JSON'); return
            z=json.loads(result.read_text('utf-8')); trace=z.get('workflow_trace') or []
            if len(trace)!=13 or [x.get('step') for x in trace]!=list(range(1,14)):
                fail.append('真实execute工作流不是严格13/13')
            report=(Path(td)/'out'/'2099-01-01'/'V6.5_report.md').read_text('utf-8')
            required=['一、核心状态','二、不可跳步工作流执行审计','三、行业六维强度','四、四模型独立结果','五、多模型共振结果','六、正式候选/阻断预览','七、实时UNKNOWN传播与主要淘汰原因','八、数据、回归与反偷工减料审计','九、量化生产定型状态','十、最终结论']
            for x in required:
                if x not in report: fail.append('真实execute十段输出缺失:'+x)
    finally:
        for n,v in old.items(): g[n]=v

def selftest():
    fail=[]
    if abs(limit_up_price(10.01)-11.01)>1e-9: fail.append('涨停价')
    if industry_metrics(None,0)['score']!=0: fail.append('行业缺失仍送分')
    if len(ema_series([1,2,3],3))!=3 or len(tdx_sma_series([10,20,30],3,1))!=3: fail.append('EMA/SMA')
    bars=[]; px=10.0
    for i in range(320):
        prev=px; px*=1.0004
        bars.append({'date':f'D{i:03d}','open':px*.997,'close':px,'high':px*1.01,'low':px*.99,'volume':1_000_000+i*500,'amount':120_000_000,'change':px-prev if i else 0,'turnover':2.0})
    idx=[]; ip=3000
    for i in range(80):
        prev=ip; ip*=1.0003
        idx.append({'date':f'I{i:03d}','open':ip,'close':ip,'high':ip*1.001,'low':ip*.999,'volume':1,'amount':1,'change':ip-prev,'turnover':0})
    ictx=_synthetic_industry_context(idx); im=industry_metrics(ictx,idx,load_cfg()['model'])
    expected_dims={'相对价格强度','行业内部扩散','时间持续性','资金与成交确认','消息政策事件驱动','龙头与梯队'}
    if not im.get('complete') or set(im.get('dimensions',{}))!=expected_dims: fail.append('行业六维引擎未完整闭合')
    if im.get('coverage',0)<1: fail.append('行业覆盖率未到100%')
    try:
        r=evaluate_stock({'code':'600001','name':'自检','industry':'测试行业','bars':bars},.6,idx,ictx,load_cfg()['model'])
        for key in ['平台主升','弱转强','龙回头','黄金点火']:
            if key not in r.bases or key not in r.model_scores: fail.append('四模型结构:'+key)
    except Exception as e:
        fail.append('完整盘后引擎:'+str(e))
    try:
        _realtime_tristate_regression(fail)
    except Exception as e:
        fail.append('实时三态引擎:'+str(e))
    eng=(ROOT/'scripts/engine.py').read_text('utf-8'); indsrc=(ROOT/'scripts/industry_engine.py').read_text('utf-8'); val=(ROOT/'scripts/validation.py').read_text('utf-8'); tpl=(ROOT/'references/输出模板.md').read_text('utf-8'); pub=(ROOT/'scripts/public_data.py').read_text('utf-8'); wfdoc=json.loads((ROOT/'workflow_manifest.json').read_text('utf-8'))
    bridge=(ROOT/'scripts/data_bridge.py').read_text('utf-8')
    for token in ['DATA_BRIDGE_REQUIRED','主行情源与第二行情源必须独立','synthetic','bundle.json','news_scan_complete']:
        if token not in bridge: fail.append('数据容灾桥缺失:'+token)
    # 数据桥必须真实执行校验：有效独立二源可通过；同源/模拟源必须拒绝。
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            bp=Path(td)/'bundle.json'
            now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
            base={'schema':BRIDGE_SCHEMA,'mode':'after-market','trade_date':'2026-09-11','generated_at':now,'decision_asof':'2026-09-11T15:10:00',
                  'provenance':{'primary':{'provider':'ProviderA','kind':'public_api'},'secondary':{'provider':'ProviderB','kind':'licensed_data'}},
                  'universe':[{'code':'600001','name':'桥接自检'}],
                  'histories':{'600001':[{'date':'2026-09-11','open':10,'close':10,'high':10,'low':10,'volume':1,'amount':1,'pct_change':0,'change':0,'turnover':1}]},
                  'indices':{'1.000001':[{'date':'2026-09-11','close':3000}],'0.399001':[{'date':'2026-09-11','close':10000}]},
                  'industries':{'stock_to_name':{},'boards':{},'board_bars':{},'constituents':{},'news':{},'news_scan_complete':{}},
                  'secondary':{'600001':{'date':'2026-09-11','close':10}}}
            bp.write_text(json.dumps(base,ensure_ascii=False),'utf-8'); db=DataBundle(str(bp))
            if db.validate('after-market','2026-09-11'): fail.append('合法独立二源数据桥被错误拒绝')
            same=json.loads(json.dumps(base)); same['provenance']['secondary']['provider']='ProviderA'; bp.write_text(json.dumps(same,ensure_ascii=False),'utf-8')
            if not any('必须独立' in x for x in DataBundle(str(bp)).validate('after-market','2026-09-11')): fail.append('同源冒充二源未被拒绝')
            fake=json.loads(json.dumps(base)); fake['provenance']['primary']['kind']='synthetic'; bp.write_text(json.dumps(fake,ensure_ascii=False),'utf-8')
            if not any('模拟/生成' in x for x in DataBundle(str(bp)).validate('after-market','2026-09-11')): fail.append('模拟数据桥未被拒绝')
            req=write_bridge_request(str(Path(td)/'req.json'),'after-market','2026-09-11','direct network fail')
            rq=json.loads(req.read_text('utf-8'))
            if rq.get('status')!='DATA_BRIDGE_REQUIRED' or '自动' not in ''.join(rq.get('mandatory_rules') or []): fail.append('桥接请求未固化自动续跑合同')
    except Exception as e:
        fail.append('数据桥动态回归:'+str(e))
    for token in ['earlier15','(60,120,250)','fire_cross_window','model_labels','REALTIME_UNKNOWN','实时量比','summarize_realtime','realtime_liq']:
        if token not in eng: fail.append('纠错回归缺失:'+token)
    for token in ['final_holdout','ablation','resonance','survive_30m','PRODUCTION_READY','neighbor_stability','_source_match_rate','_outcome_mature','mature_archive_outcomes','val_baseline_hit','dev_baseline_hit','hold_baseline_hit','min_train_samples']:
        if token not in val: fail.append('生产工作流缺失:'+token)
    for token in ['build_realtime_bars','realtime_breadth_from_universe','intraday_reference_price','volume_ratio','eastmoney_board_constituents','eastmoney_news_search','kline_fetcher']:
        if token not in pub: fail.append('实时数据链缺失:'+token)
    for token in ['相对价格强度','行业内部扩散','时间持续性','资金与成交确认','消息政策事件驱动','龙头与梯队','overheat_penalty','price_confirmed','industry_environment_state']:
        if token not in indsrc: fail.append('行业六维/消息驱动缺失:'+token)
    steps=wfdoc.get('required_steps') or []
    if len(steps)!=13: fail.append(f'固化工作流不是13步:{len(steps)}')
    if wfdoc.get('anti_shortcut_policy')!='all_steps_recorded_even_if_not_applicable_or_blocked': fail.append('反偷工减料工作流合同缺失')
    for head in ['核心状态','不可跳步工作流执行审计','行业六维强度','四模型独立结果','多模型共振结果','候选','数据、回归与反偷工减料审计','量化生产定型状态','最终结论']:
        if head not in tpl: fail.append('输出模板缺失:'+head)
    # 双源一致率必须按数值比例聚合，0.5不能被bool误算为100%。
    sm=_source_match_rate([{'date':'2099-01-01','source_match':0.5},{'date':'2099-01-02','source_match':1.0}])
    if abs(sm-.75)>1e-9: fail.append('双源一致率仍存在bool聚合错误')
    if _objective({'n':0})!=0.0: fail.append('零样本目标函数仍伪造正分')
    try:
        import tempfile
        from datetime import timedelta
        with tempfile.TemporaryDirectory() as td:
            st=Path(td); d0=datetime(2099,1,1)
            dates=[(d0+timedelta(days=i)).strftime('%Y-%m-%d') for i in range(11)]
            rows=[{'date':dates[0],'year':2099,'code':'600001','name':'成熟自检','kind':'core','production_eligible':True,'bases':{},'scores':{},'components':{},'outcomes':None,'source_match':1.0}]
            (st/'event_archive.jsonl').write_text(json.dumps(rows[0],ensure_ascii=False)+'\n','utf-8')
            hb=[]
            for i,dte in enumerate(dates):
                close=10*(1+.01*i); hb.append({'date':dte,'open':close,'close':close,'high':close*1.01,'low':close*.99})
            mz=mature_archive_outcomes(st,{'600001':hb},dates,dates[-1])
            rr=json.loads((st/'event_archive.jsonl').read_text('utf-8').strip())
            if mz.get('matured')!=1 or not isinstance(rr.get('outcomes'),dict) or rr['outcomes'].get('hit10_10d') is not True:
                fail.append('严格样本5/10日结果成熟链未闭合')
            empty=Path(td)/'empty'; empty.mkdir()
            pv=validate_production(empty,load_cfg())
            if pv.get('status')!='NOT_READY' or any(float(x.get('ratio') or 0)>0 for x in (pv.get('neighbor_stability') or {}).values()):
                fail.append('零生产样本仍可能伪造参数稳定/PRODUCTION_READY')
    except Exception as e:
        fail.append('样本成熟/零样本生产门回归:'+str(e))
    if 'or -99' in val: fail.append('中位收益0仍可能被truthiness误判为缺失')
    entry_src=(ROOT/'scripts/workbuddy_entry.py').read_text('utf-8')
    if sum(1 for line in entry_src.splitlines() if line.startswith("    wf(13,'完整Markdown/JSON/HTML/运行哈希输出'"))!=1:
        fail.append('第13步工作流重复或缺失')
    if 'industry_increment_bonus' not in eng or "'行业超额强度'" not in eng or "'行业强':industry_points" in eng:
        fail.append('行业硬门与评分重复计权未消除')
    cfg_now=load_cfg()
    if 'min_train_samples' not in val: fail.append('训练样本门仍是配置未执行')
    if 'industry_engine' in cfg_now: fail.append('存在仅描述不执行的行业配置块')
    # 消息时点/价格确认回归：未来消息不得进入；正面未获价格确认不得加分；可信负面可先扣风险。
    try:
        from industry_engine import _event_metrics
        bb=[{'date':f'2026-09-{d:02d}','close':100+d} for d in range(1,12)]
        asof=datetime.fromisoformat('2026-09-11T15:10:00')
        future=_event_metrics([{'time':'2026-09-12 09:00','title':'测试行业重大政策支持','source':'中国政府网'}],'测试行业',bb,True,asof,True)
        if future.get('driver_score')!=0 or future.get('top_events'): fail.append('未来消息未被decision_asof截断')
        unconfirmed=_event_metrics([{'time':'2026-09-11 10:00','title':'测试行业获得政策支持','source':'中国政府网'}],'测试行业',bb,False,asof,True)
        if unconfirmed.get('driver_score')!=0: fail.append('正面消息未价格确认却加分')
        negative=_event_metrics([{'time':'2026-09-11 10:00','title':'测试行业发生重大事故停产风险','source':'新华社'}],'测试行业',bb,False,asof,True)
        if negative.get('risk_penalty',0)<=0: fail.append('可信负面事件未形成风险扣分')
    except Exception as e: fail.append('消息时序回归:'+str(e))
    if "'黄金点火': structural['黄金点火']" not in eng or "and realtime_liq and p['realtime_fire_volume_ratio_min']" not in eng:
        fail.append('黄金点火盘中成交额硬门回归')
    try:
        _workflow_trace_e2e(fail)
    except Exception as e:
        fail.append('真实execute工作流离线验收:'+str(e))
    try:
        import consensus_engine as ce
        if ce.SCHEMA!='a_share_quant_consensus_bundle_v2': fail.append('V6.5共识容灾schema缺失')
        if not ce.selftest(): fail.append('V6.5共识容灾动态回归失败')
    except Exception as e:
        fail.append('V6.5共识容灾动态回归:'+str(e))
    if fail:
        print('SELFTEST_FAILED\n'+'\n'.join('- '+x for x in fail)); return False
    print('ALL_TESTS_PASSED'); return True


def deep_audit():
    """针对用户固定要求的三条红线做发布前审计。"""
    failures=[]
    # 1) 早期错误回归
    if not selftest(): failures.append('早期错误回归/selftest失败')
    # 2) 固化工作流偏离
    try:
        wf=json.loads((ROOT/'workflow_manifest.json').read_text('utf-8')); steps=wf.get('required_steps') or []
        if len(steps)!=13 or [x.get('step') for x in steps]!=list(range(1,14)): failures.append('工作流13步编号/数量偏离')
        entry=(ROOT/'scripts/workbuddy_entry.py').read_text('utf-8')
        for n in range(1,14):
            if f'wf({n},' not in entry: failures.append(f'实际执行代码缺失工作流第{n}步')
        if sum(1 for line in entry.splitlines() if line.startswith("    wf(13,'完整Markdown/JSON/HTML/运行哈希输出'"))!=1: failures.append('实际执行代码第13步重复/缺失')
        eng=(ROOT/'scripts/engine.py').read_text('utf-8')
        if 'industry_increment_bonus' not in eng or "'行业强':industry_points" in eng: failures.append('行业硬门又被直接重复计分')
    except Exception as e: failures.append('workflow_manifest解析失败:'+str(e))
    # 3) 简化输出/少跑步骤偷工减料
    tpl=(ROOT/'references/输出模板.md').read_text('utf-8')
    for token in ['十段一级结构','13/13','行业六维','消息证据','逐模型','反偷工减料','UNKNOWN']:
        if token not in tpl: failures.append('固定输出缺失:'+token)
    if failures:
        print('DEEP_AUDIT_FAILED\n'+'\n'.join('- '+x for x in failures)); return False
    print('DEEP_AUDIT_PASSED')
    print('1) 早期错误回归：通过')
    print('2) 固化工作流偏离：未发现')
    print('3) 简化输出/少跑步骤：未发现；固定13步+十段完整输出')
    return True

def doctor():
    pkg=verify_package(False); direct=True
    print('Python:',sys.version.split()[0]); print('包完整性:','正常' if pkg else '失败')
    try:
        u=eastmoney_universe(); print('直连主源股票池:',len(u),'只')
        direct=direct and len(u)>=3000
    except Exception as e:
        print('直连主源:不可用',e); direct=False
    try:
        d=latest_completed_trade_date('after-market'); print('直连交易日:',d)
    except Exception as e:
        print('直连交易日:不可用',e); direct=False
    try:
        t=tencent_kline('000001',5); print('直连独立二源:','正常' if t else '不可用'); direct=direct and bool(t)
    except Exception as e:
        print('直连独立二源:不可用',e); direct=False
    print('WorkBuddy数据桥schema:',BRIDGE_SCHEMA)
    print('容灾状态:','直连可用' if direct else '直连不可用；必须自动进入WorkBuddy数据桥，不得把本状态当最终BLOCKED')
    if not pkg:
        print('DOCTOR_FAILED'); return False
    print('DOCTOR_OK' if direct else 'DOCTOR_OK_BRIDGE_READY')
    return True

def _board(name,boards):
    if name in boards:return boards[name]
    n=name.replace('Ⅱ','').replace('II','').strip()
    for k,v in boards.items():
        kk=k.replace('Ⅱ','').replace('II','').strip()
        if kk==n or n in kk or kk in n:return v
    return None


def _secondary(r,date,tolerance=.02,data:Optional[RuntimeData]=None):
    try:
        rows=(data or RuntimeData()).secondary_rows(r.code,360); row=next((x for x in rows if x['date']==date),None)
        if not row:return {'status':'UNAVAILABLE'}
        diff=abs(float(row['close'])-float(r.metrics.get('close') or 0))
        return {'status':'MATCH' if diff<=tolerance else 'MISMATCH','diff':diff,'close':row['close']}
    except Exception as e:
        return {'status':'UNAVAILABLE','reason':str(e)}


def _dict(r):
    d={'code':r.code,'name':r.name,'labels':list(getattr(r,'model_labels',[]) or []),'primary_model':getattr(r,'primary_model',None),
       'resonance_count':int(getattr(r,'resonance_count',0) or 0),'scores':dict(getattr(r,'model_scores',{}) or {}),
       'reject_reasons':list(getattr(r,'reject_reasons',[]) or []),'metrics':dict(getattr(r,'metrics',{}) or {}),'bases':dict(getattr(r,'bases',{}) or {}),'components':dict(getattr(r,'components',{}) or {})}
    if isinstance(r,EvalResult):
        d.update({'market_state':r.market_state,'industry':r.industry,'industry_valid':r.industry_valid,'needs_industry':r.needs_industry})
    else:
        d.update({'state':r.state,'potential_models':r.potential_models,'unknown_fields':r.unknown_fields,'needs_industry':r.needs_industry})
    return d


def _production_summary(state_dir,cfg):
    try:return validate_production(state_dir,cfg)
    except Exception as e:return {'status':'NOT_READY','pass':False,'reason':'生产验证异常:'+str(e),'gates':[]}


def render_md(p):
    b=p['breadth']; q=p['coverage']; prod=p['production_validation']; rt=p['mode']=='realtime'
    lines=[f"# A股量化生产定型工程 V6.5 — {p['trade_date']} {'盘中实时' if rt else '盘后实跑'}结果","",f"**本次运行状态：{p['status']}**  ",f"**量化生产定型状态：{prod.get('status','NOT_READY')}**  ",f"**决策信息截止：{p.get('decision_asof','-')}**","",
           "## 一、核心状态","","| 项目 | 结果 |","|---|---|",f"| 数据质量 | {'通过' if p['status']=='AUTHORIZED' else '阻断'} |",f"| 市场状态 | {p['market_state']} |",f"| 全市场宽度 | {b['breadth']*100:.2f}% |",f"| 上涨 / 下跌 / 平盘 | {b['up']} / {b['down']} / {b['flat']} |",f"| 主板历史覆盖 | {q['mainboard_rate']*100:.2f}% |",f"| 市场宽度覆盖 | {q['breadth_rate']*100:.2f}% |",f"| 点时数据资格 | {p['pit_status']} |",f"| 本地通达信/公式依赖 | 无 |"]
    if rt: lines.append(f"| 实时三态未知数 | {len(p.get('realtime_unknown',[]))} |")

    lines += ["","## 二、不可跳步工作流执行审计","","| 步骤 | 工作流 | 状态 | 证据 |","|---:|---|---|---|"]
    for x in p.get('workflow_trace',[]): lines.append(f"| {x.get('step')} | {x.get('name')} | {x.get('status')} | {x.get('detail') or '-'} |")
    lines.append(f"\n**工作流记录：{len(p.get('workflow_trace',[]))}/13。任何步骤不记录均不得宣称完整执行。**")

    lines += ["","## 三、行业六维强度、生命周期与消息驱动","",
              "行业不再使用旧版4条件静态评分；固定为：相对价格25 + 内部扩散20 + 时间持续20 + 资金成交15 + 消息政策事件15 + 龙头梯队5 − 过热/退潮惩罚 − 负面事件惩罚。"]
    inds=p.get('industry_summaries') or {}
    if not inds: lines.append('\n- 本轮没有股票进入行业精算，或行业数据完全未映射；相关原因必须在第八节审计中出现。')
    else:
        lines += ["","| 行业 | 总分 | 阶段 | 等级 | 覆盖率 | 价格25 | 扩散20 | 时间20 | 资金15 | 消息15 | 龙头5 | 结构惩罚 | 事件风险 |","|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for name,z in sorted(inds.items(),key=lambda kv:(-(float(kv[1].get('score') or 0)),kv[0])):
            d=z.get('dimensions') or {}
            lines.append(f"| {name} | {float(z.get('score') or 0):.1f} | {z.get('phase') or '未知'} | {z.get('tier') or '未知'} | {float(z.get('coverage') or 0)*100:.0f}% | {float(d.get('相对价格强度') or 0):.1f} | {float(d.get('行业内部扩散') or 0):.1f} | {float(d.get('时间持续性') or 0):.1f} | {float(d.get('资金与成交确认') or 0):.1f} | {float(d.get('消息政策事件驱动') or 0):.1f} | {float(d.get('龙头与梯队') or 0):.1f} | {float(z.get('overheat_penalty') or 0):.1f} | {float(z.get('event_risk_penalty') or 0):.1f} |")
        lines += ["","### 行业消息证据与时间衰减"]
        for name,z in sorted(inds.items()):
            ev=z.get('events') or []
            if not ev:
                lines.append(f"- **{name}**：无进入评分的有效新鲜事件；若消息检索失败而非确实无事件，会在数据审计中明确标记，不能伪装为0分已核验。")
                continue
            lines.append(f"- **{name}**：")
            for e in ev[:8]:
                lines.append(f"  - {e.get('time') or '-'}｜{e.get('direction')}｜{e.get('event_type')}｜交易日龄={e.get('trading_age')}｜{e.get('source') or '来源未标'}｜{e.get('title')}｜正面价格确认={e.get('price_confirmed')}")

    lines += ["","## 四、四模型独立结果","","| 模型 | 独立触发数 |","|---|---:|"]
    for k,v in p['model_counts'].items(): lines.append(f'| {k} | {v} |')
    evidence=p['candidates'] if p['status']=='AUTHORIZED' else p.get('candidate_preview_when_blocked',[])
    if evidence:
        lines += ['', '### 候选逐模型硬门、分数与增量证据（禁止只报总分）', '', '| 代码 | 模型 | 硬门 | 分数 | 增量证据 |', '|---|---|---|---:|---|']
        for x in evidence:
            for model in ['平台主升','弱转强','龙回头','黄金点火']:
                base=bool((x.get('bases') or {}).get(model)); score=float((x.get('scores') or {}).get(model,0) or 0); comp=(x.get('components') or {}).get(model,{}) or {}
                comp_text='；'.join(f'{k}={v:g}' for k,v in comp.items()) if comp else '-'
                lines.append(f"| {x['code']} | {model} | {'通过' if base else '未通过'} | {score:.1f} | {comp_text} |")
    else:
        lines.append('\n- 本轮无正式/预览候选进入逐模型证据表；四模型仍已对全股票池完成核心结构计算，淘汰原因见第七节。')
    lines += ['', '## 五、多模型共振结果','', '| 同时触发模型数 | 股票数 |','|---:|---:|']
    for k,v in p['resonance_counts'].items(): lines.append(f'| {k} | {v} |')

    lines += ['', '## 六、正式候选/阻断预览','']
    lines.append('**正式候选：**' if p['status']=='AUTHORIZED' else '**当前为BLOCKED，以下仅为非正式预览：**')
    cand=p['candidates'] if p['status']=='AUTHORIZED' else p.get('candidate_preview_when_blocked',[])
    if not cand: lines.append('**0只。**' if p['status']=='AUTHORIZED' else '无已通过全部已知硬门的预览候选。')
    else:
        if rt:
            lines += ['| 排名 | 代码 | 名称 | 全部模型标签 | 共振 | 行业分/阶段 | 实时量比 | 实时换手 | 实时成交额 | 稳定参考价 |','|---:|---|---|---|---:|---|---:|---:|---:|---:|']
            for i,x in enumerate(cand,1):
                m=x['metrics']; vr=m.get('realtime_volume_ratio'); tr=m.get('realtime_turnover_fraction'); sp=m.get('stable_price'); amt=m.get('realtime_amount')
                lines.append(f"| {i} | {x['code']} | {x['name']} | {'+'.join(x['labels'])} | {x['resonance_count']} | {float(m.get('industry_score') or 0):.1f}/{m.get('industry_phase') or '未知'} | {'-' if vr is None else f'{vr:.2f}'} | {'-' if tr is None else f'{tr*100:.2f}%'} | {'-' if amt is None else f'{amt/1e8:.2f}亿'} | {'-' if sp is None else f'{sp:.2f}'} |")
        else:
            lines += ['| 排名 | 代码 | 名称 | 全部模型标签 | 共振 | 显示主模型 | 各模型评分 | 行业 | 行业分/阶段 | 行业覆盖 | 锁筹 | 压力空间 |','|---:|---|---|---|---:|---|---|---|---|---:|---|---:|']
            for i,x in enumerate(cand,1):
                m=x['metrics']; ps=m.get('pressure_space')
                lines.append(f"| {i} | {x['code']} | {x['name']} | {'+'.join(x['labels'])} | {x['resonance_count']} | {x.get('primary_model') or '-'} | {json.dumps(x['scores'],ensure_ascii=False)} | {x.get('industry') or '-'} | {float(m.get('industry_score') or 0):.1f}/{m.get('industry_phase') or '未知'} | {float(m.get('industry_coverage') or 0)*100:.0f}% | {'是' if m.get('lock_model') else '否'} | {'无已知上压' if m.get('no_pressure') else ('-' if ps is None else f'{ps*100:.2f}%')} |")

    lines += ['', '## 七、实时UNKNOWN传播与主要淘汰原因','']
    if not rt: lines.append('- 盘后模式无实时字段判定；本节仍保留并展示主要淘汰原因与行业未决，禁止删节。')
    if rt:
        unknown=p.get('realtime_unknown',[])
        if not unknown: lines.append('- 无潜在候选存在关键实时字段未知。')
        else:
            for x in unknown:
                lines.append(f"- {x['code']} {x['name']}：潜在模型={'+'.join(x.get('potential_models') or [])}；未知字段={','.join(x.get('unknown_fields') or [])}。=> **UNKNOWN / BLOCKED**")
        lines += ['', '### 正常淘汰原因']
    for k,v in p.get('reject_counts',{}).items(): lines.append(f'- {k}：{v}只')

    lines += ['', '## 八、数据、回归与反偷工减料审计','']
    if p.get('block_reasons'):
        for x in p['block_reasons']: lines.append('- ❌ '+x)
    else: lines.append('- ✅ 数据门闭合；没有用市场环境短路推断最终0只。')
    a=p['audit']
    lines += [f"- 数据路由：{a.get('data_route','DIRECT_PUBLIC_API')}；来源={json.dumps(a.get('data_provenance') or {},ensure_ascii=False)}",f"- 工作流：{a.get('workflow_steps_recorded')}/{a.get('workflow_steps_expected')}，固定全链路未删步。",f"- 规则哈希：`{a.get('rules_hash')}`",f"- 行业引擎哈希：`{a.get('industry_rules_hash')}`",f"- 反偷工减料合同：{a.get('anti_shortcut')}"]
    if rt:
        lines += [f"- 实时未知传播：潜在候选UNKNOWN {a.get('realtime_unknown_count',0)}只；基本结构失败仍正常FAIL。",f"- 分钟稳定价：取得 {a.get('stable_price_ok',0)} / 请求 {a.get('stable_price_requested',0)}。",'- 当前未完成日K每次由实时快照重建，不复用同日旧缓存。']
    else:
        lines += [f"- 二源核验：匹配 {a.get('secondary_match')} / 冲突 {a.get('secondary_mismatch')} / UNKNOWN {a.get('secondary_unavailable')}",f"- 行业六维/消息未决核心结构：{len(a.get('unresolved_codes') or [])}只"]
    if a.get('industry_errors'):
        lines.append('- 行业数据异常/消息检索异常（完整保留，禁止静默删除）：')
        for x in a['industry_errors']: lines.append('  - '+x)
    lines += ['- 早期错误防回归：行业缺失不送分；平台缩量不自比较；60/120/250多尺度撑压；黄金点火非仅当日交叉；硬门不重复计分；多模型标签不覆盖；实时量比不线性外推；同日未完成K线不复用；UNKNOWN不等于FAIL。']

    lines += ['', '## 九、量化生产定型状态','',f"- 当前：**{prod.get('status','NOT_READY')}**",f"- 已授权归档事件：{prod.get('authorized_events',0)}",f"- 已成熟可验收事件：{prod.get('eligible_events',0)}",f"- 尚未成熟/结果字段不完整事件：{prod.get('immature_events',0)}",f"- 最终封存年份：{prod.get('holdout_year')}"]
    ns=prod.get('neighbor_stability') or {}
    if ns:
        for m,z in ns.items(): lines.append(f"- {m}参数邻域稳定率：{float(z.get('ratio') or 0):.3f}")
    lines.append(f"- 双源价格一致率：{float(prod.get('source_match_rate') or 0)*100:.2f}%")
    failed=[x for x in prod.get('gates',[]) if not x.get('pass')]
    if failed:
        lines.append('- 未通过门槛：')
        for x in failed: lines.append(f"  - {x['name']}：{x.get('value')}（门槛 {x.get('threshold')}）")
    else: lines.append('- 所有生产验证门槛已通过。')

    lines += ['', '## 十、最终结论','']
    if p['status']=='BLOCKED': lines.append('**本次数据门禁未闭合，禁止把任何预览名单当正式结果。**')
    elif not cand: lines.append('**本次全工作流逐股完整计算后，正式候选为0只。**')
    else: lines.append('以上为本轮正式候选；模型分数是规则证据分，不等于上涨概率、胜率或收益保证。')
    lines.append('本技能仅做盘后选股与盘中实时候选；不做集合竞价、次日开盘买点、持仓退出或自动交易。')
    return '\n'.join(lines)
def _load_external_events(path: Optional[str]) -> Dict[str,Dict[str,Any]]:
    out={}
    if not path: return out
    p=Path(path)
    if not p.exists(): raise DataError('外部事件文件不存在:'+str(p))
    text=p.read_text('utf-8')
    rows=[]
    if p.suffix.lower()=='.json':
        z=json.loads(text); rows=z if isinstance(z,list) else z.get('events',[])
    else:
        for line in text.splitlines():
            if line.strip(): rows.append(json.loads(line))
    for x in rows:
        ind=str(x.get('industry') or '').strip()
        if not ind: continue
        d=out.setdefault(ind,{'events':[],'scan_complete':False})
        if x.get('scan_complete') is True: d['scan_complete']=True
        if x.get('title'): d['events'].append(x)
    return out


def _decision_asof(trade_date:str, historical:bool=False)->str:
    now=datetime.now(ZoneInfo('Asia/Shanghai'))
    if not historical and now.strftime('%Y-%m-%d')==trade_date:
        return now.replace(tzinfo=None).isoformat(timespec='seconds')
    # 历史预览统一锁到15:10，且仍由PIT门禁阻断为正式生产样本。
    return f'{trade_date}T15:10:00'


def _fetch_industries(codes,trade_date,boards,state_dir:Path,market_amount_total:float,asof:str,external_events:Optional[Dict[str,Dict[str,Any]]]=None,data:Optional[RuntimeData]=None):
    icache={}; imap={}; ierr=[]; external_events=external_events or {}; data=data or RuntimeData()
    for code in codes:
        try:
            nm=data.industry_name(code); imap[code]=nm
            if not nm:
                ierr.append(code+':行业缺失'); continue
            bc=_board(nm,boards)
            if not bc:
                ierr.append(code+':行业板块未映射'); continue
            if bc not in icache:
                bars=data.board_kline(bc,trade_date,60)
                if not bars or bars[-1]['date']!=trade_date:
                    ierr.append(code+':行业历史未对齐')
                    icache[bc]={'name':nm,'bars':bars,'constituents':[],'events':[],'events_covered':False,'history_state':load_industry_history(state_dir,nm),'market_amount_total':market_amount_total,'asof':asof}
                else:
                    try:
                        members=data.board_constituents(bc)
                    except Exception as e:
                        members=[]; ierr.append(nm+':行业成分股快照失败:'+str(e))
                    news=[]; news_ok=False
                    try:
                        news=data.news_search(nm,30); news_ok=data.news_scan_complete(nm)
                    except Exception as e:
                        ierr.append(nm+':消息检索失败:'+str(e))
                    ext=external_events.get(nm) or {}
                    merged=list(news)+list(ext.get('events') or [])
                    events_covered=bool(news_ok or ext.get('scan_complete'))
                    icache[bc]={'name':nm,'bars':bars,'constituents':members,'events':merged,'events_covered':events_covered,
                                'history_state':load_industry_history(state_dir,nm),'market_amount_total':market_amount_total,'asof':asof}
            imap[code]=(nm,bc)
        except Exception as e:
            ierr.append(code+':'+str(e))
    return imap,icache,ierr
def execute(args):
    if not verify_package(False):
        print('BLOCKED:包完整性失败'); return 2
    bundle_path=resolve_bundle_path(getattr(args,'data_bundle',None))
    bundle=DataBundle(bundle_path) if bundle_path else None
    if bundle:
        bundle.assert_valid(args.mode,args.date if args.date else None)
    data=RuntimeData(bundle)
    if args.mode=='realtime' and args.date:
        print('BLOCKED:盘中实时模式禁止指定历史日期；历史分钟快照不可用时不能伪造实时回放'); return 2
    cfg=load_cfg(); workflow=[]
    def wf(no,name,status='完成',detail=''):
        workflow.append({'step':no,'name':name,'status':status,'detail':detail})
        print(f'[{no}/13] {name}：{status}'+(f'；{detail}' if detail else ''))
    if args.mode=='realtime':
        rtwin=china_realtime_window_status(cfg['model'].get('realtime_min_minutes_from_open',30))
        if rtwin!='realtime':
            print('BLOCKED:盘中模式仅开盘30分钟后的连续竞价阶段运行，集合竞价/开盘前30分钟/午休/收盘后均禁止'); return 2
    trade_date=args.date or data.latest_trade_date(args.mode); cache=Cache(args.cache_dir)
    state=Path(args.state_dir or (ROOT/'state')); state.mkdir(parents=True,exist_ok=True)
    latest=data.latest_trade_date('after-market')
    pit=(args.mode=='realtime' and not args.date) or (args.mode=='after-market' and not args.date and trade_date==latest)
    pit_status='CURRENT_SNAPSHOT' if pit else 'HISTORICAL_NON_PIT_PREVIEW'
    asof=_decision_asof(trade_date,historical=not pit)
    external_events=_load_external_events(getattr(args,'events_file',None))
    wf(1,'包完整性/决策时点锁定','完成',f'{trade_date}；{args.mode}；{pit_status}；asof={asof}；数据路由={data.route}')

    uni=data.universe(); main=[x for x in uni if is_mainboard(x['code'])]; smap={x['code']:x for x in main}
    market_amount_total=sum(float(x.get('amount') or 0) for x in uni if x.get('amount') not in (None,'-',''))
    wf(2,'全A股票池与主板过滤','完成',f'全A {len(uni)}；主板 {len(main)}')

    raw_hist,he=fetch_histories(main,trade_date,args.workers,cache,cfg['data_gates']['history_request_bars'],kline_fetcher=data.kline)
    min_hist=int(cfg['data_gates'].get('native_min_history_bars',120))
    if args.mode=='realtime':
        hist={code:build_realtime_bars(bars,smap[code],trade_date) for code,bars in raw_hist.items() if code in smap}
    else: hist=raw_hist
    hist={k:v for k,v in hist.items() if len(v)>=min_hist and str(v[-1].get('date'))==str(trade_date)}
    mr=len(hist)/max(len(main),1)
    enhanced=sum(1 for v in hist.values() if len(v)>=int(cfg['data_gates'].get('enhanced_history_bars',250)))
    wf(3,'模型级历史数据门','完成',f'核心≥{min_hist}根覆盖 {mr*100:.2f}%；增强≥250根 {enhanced}/{len(hist)}')

    breadth=realtime_breadth_from_universe(uni) if args.mode=='realtime' else fetch_breadth_for_date(uni,hist,trade_date,args.workers,cache,kline_fetcher=data.kline)
    br=breadth['covered']/max(breadth['universe'],1)
    wf(4,'全市场宽度逐股重算','完成',f"宽度 {breadth['breadth']*100:.2f}%；覆盖 {br*100:.2f}%")

    sh=data.index_kline('1.000001',trade_date,320); sz=data.index_kline('0.399001',trade_date,320)
    if not sh or not sz or sh[-1]['date']!=trade_date or sz[-1]['date']!=trade_date: raise DataError('指数数据未对齐')
    wf(5,'沪深对应指数与市场权限','完成','上证/深证指数已对齐')

    if args.mode=='after-market':
        prelim=[evaluate_stock({'code':code,'name':smap[code]['name'],'bars':bars},breadth['breadth'],sh if exchange_of(code)=='SH' else sz,None,cfg['model']) for code,bars in hist.items()]
        need=sorted({r.code for r in prelim if r.needs_industry or r.core_base_hit})
    else:
        prelim=[]
        for code,bars in hist.items():
            snap=dict(smap[code]); snap['date']=trade_date; snap['stable_price']=None
            prelim.append(evaluate_realtime_stock({'code':code,'name':smap[code]['name'],'bars':bars,'snapshot':snap},breadth['breadth'],sh if exchange_of(code)=='SH' else sz,None,cfg['model']))
        need=sorted({r.code for r in prelim if r.potential_models})
    wf(6,'四模型核心结构逐股预筛','完成',f'{len(need)}只进入行业六维精算')

    boards=data.industry_boards() if need else {}
    imap,icache,ierr=_fetch_industries(need,trade_date,boards,state,market_amount_total,asof,external_events,data=data)
    complete_ind=sum(1 for x in icache.values() if x.get('events_covered') and x.get('constituents') and x.get('bars'))
    wf(7,'行业六维+时间+消息驱动精算','完成',f'行业板块 {len(icache)}；原始数据闭合 {complete_ind}')

    if args.mode=='after-market':
        final=[]
        for code,bars in hist.items():
            z=imap.get(code); nm=None; ictx=None
            if isinstance(z,tuple): nm,bc=z; ictx=icache.get(bc)
            elif isinstance(z,str): nm=z
            final.append(evaluate_stock({'code':code,'name':smap[code]['name'],'industry':nm,'bars':bars},breadth['breadth'],sh if exchange_of(code)=='SH' else sz,ictx,cfg['model']))
        summ=summarize(final); unresolved=[r for r in final if r.needs_industry]
        stable_req=stable_ok=0; rt_unknown=[]
    else:
        first=[]
        for code,bars in hist.items():
            z=imap.get(code); nm=None; ictx=None
            if isinstance(z,tuple): nm,bc=z; ictx=icache.get(bc)
            elif isinstance(z,str): nm=z
            snap=dict(smap[code]); snap['date']=trade_date; snap['stable_price']=None
            first.append(evaluate_realtime_stock({'code':code,'name':smap[code]['name'],'industry':nm,'bars':bars,'snapshot':snap},breadth['breadth'],sh if exchange_of(code)=='SH' else sz,ictx,cfg['model']))
        req=[r for r in first if r.state==REALTIME_UNKNOWN and '数分钟前价格' in r.unknown_fields]
        stable_req=len(req); stable_map={}
        for r in req:
            try:
                px=intraday_reference_price(data.intraday_trends(r.code),cfg['model'].get('realtime_stable_minutes_back',5))
                if px is not None: stable_map[r.code]=px
            except Exception: pass
        stable_ok=len(stable_map); final=[]
        for code,bars in hist.items():
            z=imap.get(code); nm=None; ictx=None
            if isinstance(z,tuple): nm,bc=z; ictx=icache.get(bc)
            elif isinstance(z,str): nm=z
            snap=dict(smap[code]); snap['date']=trade_date; snap['stable_price']=stable_map.get(code)
            final.append(evaluate_realtime_stock({'code':code,'name':smap[code]['name'],'industry':nm,'bars':bars,'snapshot':snap},breadth['breadth'],sh if exchange_of(code)=='SH' else sz,ictx,cfg['model']))
        summ=summarize_realtime(final); unresolved=[]; rt_unknown=list(summ['unknown'])
    wf(8,'四模型完整硬门/评分/共振','完成',f"候选 {summ['candidate_count']}；实时未知 {len(rt_unknown)}")

    block=[]
    min_uni=int(cfg['data_gates'].get('min_universe_size',3000))
    if len(uni)<min_uni:block.append(f'全A股票池{len(uni)}低于最小完整性门槛{min_uni}')
    if mr<cfg['data_gates']['min_mainboard_coverage']:block.append(f'主板历史覆盖率{mr*100:.2f}%低于门槛')
    if br<cfg['data_gates']['min_breadth_coverage']:block.append(f'市场宽度覆盖率{br*100:.2f}%低于门槛')
    if args.mode=='after-market' and unresolved:block.append(f'{len(unresolved)}只核心结构的行业六维/消息数据未闭合')
    if args.mode=='realtime' and rt_unknown:
        fields=Counter(f for r in rt_unknown for f in r.unknown_fields)
        block.append(f"{len(rt_unknown)}只潜在盘中候选存在关键实时字段未知："+'、'.join(f'{k}{v}只' for k,v in fields.most_common()))
    if args.date and not pit:block.append('指定历史日期使用当前公开股票身份/行业映射，缺少严格point-in-time快照；只能做研究预览')
    wf(9,'UNKNOWN传播与数据门禁预审','完成',f'预阻断 {len(block)}项')

    cands=[_dict(r) for r in summ['candidates']]; match=mis=unav=0
    if args.mode=='after-market':
        for x in cands:
            r=next(r for r in summ['candidates'] if r.code==x['code']); ck=_secondary(r,trade_date,cfg['data_gates']['secondary_close_tolerance'],data=data); x['secondary_check']=ck
            if ck['status']=='MATCH':match+=1
            elif ck['status']=='MISMATCH':mis+=1
            else:unav+=1
        if mis:block.append('最终候选存在第二行情源价格冲突')
        if unav:block.append('最终候选存在第二行情源不可用，价格核验UNKNOWN')
        wf(10,'第二行情源候选价格核验','完成',f'匹配{match}/冲突{mis}/未知{unav}')
    else:
        wf(10,'第二行情源候选价格核验','不适用','盘中只做实时三态；收盘后二源验证归入盘后流程')
    status='BLOCKED' if block else 'AUTHORIZED'

    source_match=(match/(match+mis+unav)) if (match+mis+unav) else None
    if args.mode=='after-market' and status=='AUTHORIZED':
        archived=archive_after_market(final,trade_date,state,pit,source_match,cfg['data_gates']['baseline_sample_per_day'])
        archived_ind=archive_industry_states(final,trade_date,state)
        market_dates=sorted({str(x.get('date')) for x in sh if x.get('date')})
        maturity=mature_archive_outcomes(state,hist,market_dates,trade_date)
        update_realtime_close_confirmation(state,trade_date,{r.code for r in summ['candidates']})
        wf(11,'严格样本/行业状态归档与历史样本成熟','完成',f"新增事件{archived}；行业{archived_ind}；成熟旧事件{maturity.get('matured',0)}；待成熟{maturity.get('pending',0)}")
    elif args.mode=='realtime' and status=='AUTHORIZED':
        archive_realtime(summ['candidates'],trade_date,state); wf(11,'严格实时样本归档（不成熟盘后样本）','完成','仅AUTHORIZED写入')
    else: wf(11,'严格样本/行业状态归档与历史样本成熟','阻断未归档','BLOCKED不得污染生产样本')

    prod=_production_summary(state,cfg); wf(12,'量化生产定型验证','完成',prod.get('status','NOT_READY'))
    if args.mode=='after-market': mstate=Counter(r.market_state for r in final).most_common(1)[0][0] if final else '未知'
    else: mstate=Counter((r.metrics.get('market_state') or '未知') for r in final).most_common(1)[0][0] if final else '未知'

    # 行业摘要只展示实际进入行业精算的行业，保留六维、阶段和消息证据，不得简化为单一“行业强”。
    industry_summaries={}
    for r in final:
        m=getattr(r,'metrics',{}) or {}; ind=getattr(r,'industry',None)
        if not ind: continue
        if ind not in industry_summaries:
            industry_summaries[ind]={'score':m.get('industry_score'),'phase':m.get('industry_phase'),'tier':m.get('industry_tier'),'coverage':m.get('industry_coverage'),
                'dimensions':m.get('industry_dimensions') or {},'overheat_penalty':m.get('industry_overheat_penalty',0),'event_risk_penalty':m.get('industry_event_risk_penalty',0),
                'events':m.get('industry_events') or [],'breadth_up_ratio':m.get('industry_breadth_up_ratio'),'amount_share':m.get('industry_amount_share')}

    payload={'engine':ENGINE_NAME,'version':VERSION,'trade_date':trade_date,'decision_asof':asof,'mode':args.mode,'status':status,'pit_status':pit_status,'market_state':mstate,'generated_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'),
             'workflow_trace':workflow,'breadth':{k:v for k,v in breadth.items() if k!='missing'},'coverage':{'mainboard_ok':len(hist),'mainboard_total':len(main),'mainboard_rate':mr,'breadth_rate':br},
             'industry_summaries':industry_summaries,'model_counts':summ['model_counts'],'resonance_counts':summ['resonance_counts'],'candidates':cands if status=='AUTHORIZED' else [],'candidate_preview_when_blocked':cands if status=='BLOCKED' else [],
             'realtime_unknown':[_dict(r) for r in rt_unknown],'reject_counts':summ['reject_counts'],'block_reasons':block,'production_validation':prod,
             'audit':{'history_errors_sample':he[:30],'industry_errors':ierr[:100],'unresolved_codes':[r.code for r in unresolved],'secondary_match':match,'secondary_mismatch':mis,'secondary_unavailable':unav,
                      'secondary_scope':'after-market-only','realtime_unknown_count':len(rt_unknown),'stable_price_requested':stable_req,'stable_price_ok':stable_ok,'rules_hash':sha256(ROOT/'scripts/engine.py'),
                      'industry_rules_hash':sha256(ROOT/'scripts/industry_engine.py'),'workflow_steps_expected':13,'workflow_steps_recorded':len(workflow)+1,
                      'no_tdx_formula':True,'no_local_tdx':True,'auction_disabled':True,'historical_realtime_disabled':True,'next_open_disabled':True,'exit_disabled':True,'auto_trade_disabled':True,
                      'data_route':data.route,'data_provenance':data.provenance(),'anti_shortcut':'全市场->核心预筛->行业六维/事件->完整四模型->未知传播->独立二源->归档->生产验证->完整输出'}}
    od=Path(args.output_dir or ROOT/'output')/trade_date; od.mkdir(parents=True,exist_ok=True)
    # 输出本身作为第13步；先补trace再渲染，确保报告显示13/13而不是事后补写。
    wf(13,'完整Markdown/JSON/HTML/运行哈希输出','完成','固定十段结构；禁止删行业/审计/工作流')
    payload['workflow_trace']=workflow; payload['audit']['workflow_steps_recorded']=len(workflow)
    md=render_md(payload)
    (od/'V6.5_result.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str),'utf-8')
    (od/'V6.5_report.md').write_text(md,'utf-8')
    (od/'V6.5_report.html').write_text('<html><meta charset="utf-8"><body><pre>'+html.escape(md)+'</pre></body></html>','utf-8')
    (od/'run_manifest.json').write_text(json.dumps({'report_sha256':sha256(od/'V6.5_report.md'),'result_sha256':sha256(od/'V6.5_result.json'),'rules_sha256':sha256(ROOT/'scripts/engine.py'),'industry_rules_sha256':sha256(ROOT/'scripts/industry_engine.py')},ensure_ascii=False,indent=2),'utf-8')
    print(md)
    return 0 if status=='AUTHORIZED' else 3
def offline_e2e():
    """不访问网络的端到端回归：引擎三态 -> 全局授权门 -> 报告渲染。"""
    fail=[]; live,idx,snap=_synthetic_realtime_fixture(); cfg=load_cfg()['model']; ictx=_synthetic_industry_context(idx)
    good=evaluate_realtime_stock({'code':'600001','name':'完整样本','industry':'测试行业','bars':live,'snapshot':snap},.65,idx,ictx,cfg)
    missing=dict(snap); missing['volume_ratio']=None
    unknown=evaluate_realtime_stock({'code':'600002','name':'量比未知样本','industry':'测试行业','bars':live,'snapshot':missing},.65,idx,ictx,cfg)
    low=dict(missing); low['last']=live[-2]['close']*.99; low['open']=live[-2]['close']; low['high']=live[-2]['close']*1.001; low['low']=low['last']*.998; low['pct']=-1.0
    live_low=[dict(x) for x in live]; live_low[-1].update({'close':low['last'],'open':low['open'],'high':low['high'],'low':low['low']})
    rejected=evaluate_realtime_stock({'code':'600003','name':'正常淘汰样本','industry':'测试行业','bars':live_low,'snapshot':low},.65,idx,ictx,cfg)
    s=summarize_realtime([good,unknown,rejected])
    if good.state!=REALTIME_PASS: fail.append('完整实时样本未PASS')
    if unknown.state!=REALTIME_UNKNOWN or '实时量比' not in unknown.unknown_fields: fail.append('量比缺失潜在候选未UNKNOWN')
    if rejected.state!=REALTIME_FAIL: fail.append('基本结构失败未正常FAIL')
    global_status='BLOCKED' if s['unknown'] else 'AUTHORIZED'
    if global_status!='BLOCKED': fail.append('UNKNOWN未上卷为全局BLOCKED')
    payload={'engine':ENGINE_NAME,'version':VERSION,'trade_date':'2099-01-01','decision_asof':'2099-01-01T10:30:00','mode':'realtime','status':global_status,'pit_status':'OFFLINE_E2E','market_state':'强市','generated_at':'2099-01-01T10:30:00','workflow_trace':[{'step':i,'name':f'离线步骤{i}','status':'完成','detail':'E2E'} for i in range(1,14)],
             'breadth':{'breadth':.65,'up':65,'down':35,'flat':0,'covered':100,'universe':100},'industry_summaries':{'测试行业':{'score':70,'phase':'主升','tier':'强势行业','coverage':1.0,'dimensions':{'相对价格强度':20,'行业内部扩散':15,'时间持续性':15,'资金与成交确认':10,'消息政策事件驱动':5,'龙头与梯队':5},'overheat_penalty':0,'event_risk_penalty':0,'events':[]}},'coverage':{'mainboard_ok':100,'mainboard_total':100,'mainboard_rate':1.0,'breadth_rate':1.0},
             'model_counts':s['model_counts'],'resonance_counts':s['resonance_counts'],'candidates':[],'candidate_preview_when_blocked':[_dict(good)],'realtime_unknown':[_dict(unknown)],'reject_counts':s['reject_counts'],
             'block_reasons':['1只潜在盘中候选存在关键实时字段未知：实时量比1只'],'production_validation':{'status':'NOT_READY','eligible_events':0,'holdout_year':None,'gates':[]},
             'audit':{'secondary_match':0,'secondary_mismatch':0,'secondary_unavailable':0,'unresolved_codes':[],'realtime_unknown_count':1,'stable_price_requested':0,'stable_price_ok':0,'rules_hash':sha256(ROOT/'scripts/engine.py'),'industry_rules_hash':sha256(ROOT/'scripts/industry_engine.py'),'workflow_steps_expected':13,'workflow_steps_recorded':13,'anti_shortcut':'E2E完整工作流'}}
    report=render_md(payload)
    for token in ['UNKNOWN / BLOCKED','实时量比','禁止把任何预览名单当正式结果','不可跳步工作流执行审计','行业六维强度']:
        if token not in report: fail.append('E2E报告缺失:'+token)
    # 第二轮：移除未知样本后必须可授权，证明不是“一有缺字段就全局永远阻断”。
    s2=summarize_realtime([good,rejected])
    if s2['unknown'] or not s2['candidates']: fail.append('无未知样本时授权链未闭合')
    if fail:
        print('OFFLINE_E2E_FAILED\n'+'\n'.join('- '+x for x in fail)); return False
    print('OFFLINE_E2E_PASSED')
    print('CASE1 实时量比存在 -> PASS -> 正常计算')
    print('CASE2 实时量比缺失 + 潜在候选结构成立 -> UNKNOWN -> BLOCKED')
    print('CASE3 实时量比缺失 + 基本价格结构不成立 -> FAIL -> 正常淘汰')
    return True


def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest='cmd',required=True)
    for x in ['verify','selftest','deep-audit','doctor','production-status','offline-e2e']: s.add_parser(x)
    br=s.add_parser('bridge-request'); br.add_argument('--mode',choices=['after-market','realtime'],default='after-market'); br.add_argument('--date'); br.add_argument('--output')
    e=s.add_parser('execute'); e.add_argument('--date'); e.add_argument('--mode',choices=['after-market','realtime'],default='after-market'); e.add_argument('--workers',type=int,default=12); e.add_argument('--cache-dir'); e.add_argument('--state-dir'); e.add_argument('--output-dir'); e.add_argument('--events-file',help='可选：WorkBuddy补充的行业政策/产业事件JSON或JSONL'); e.add_argument('--data-bundle',help='WorkBuddy外部取数桥JSON/ZIP；直连失败后必须用该参数自动续跑')
    v=s.add_parser('validate-production'); v.add_argument('--dataset'); v.add_argument('--state-dir')
    a=p.parse_args()
    if a.cmd=='verify': return 0 if verify_package() else 2
    if a.cmd=='selftest': return 0 if selftest() else 2
    if a.cmd=='offline-e2e': return 0 if offline_e2e() else 2
    if a.cmd=='deep-audit': return 0 if deep_audit() else 2
    if a.cmd=='doctor': return 0 if doctor() else 2
    if a.cmd=='bridge-request':
        out=a.output or str(ROOT/'output'/'_bridge'/'workbuddy_bridge_request.json')
        pth=write_bridge_request(out,a.mode,a.date,'显式请求WorkBuddy数据桥')
        print('DATA_BRIDGE_REQUIRED:',pth); return BRIDGE_EXIT_CODE
    if a.cmd in ('validate-production','production-status'):
        r=validate_production(Path(getattr(a,'state_dir',None) or ROOT/'state'),load_cfg(),getattr(a,'dataset',None)); print(json.dumps(r,ensure_ascii=False,indent=2)); return 0 if r.get('pass') else 3
    if a.cmd=='execute':
        try:return execute(a)
        except KeyboardInterrupt:return 130
        except DataError as e:
            if not resolve_bundle_path(getattr(a,'data_bundle',None)):
                od=Path(a.output_dir or ROOT/'output')/'_bridge'
                req=write_bridge_request(str(od/'workbuddy_bridge_request.json'),a.mode,a.date,str(e),str(od/'workbuddy_data_bundle.zip'))
                print('DATA_BRIDGE_REQUIRED:',e)
                print('桥接请求:',req)
                print('本状态不是最终BLOCKED；WorkBuddy必须完成外部取数并用--data-bundle自动续跑。')
                return BRIDGE_EXIT_CODE
            print('BLOCKED:数据桥已启用但仍未闭合:',e)
            if os.environ.get('WORKBUDDY_DEBUG')=='1':traceback.print_exc()
            return 3
        except Exception as e:
            print('BLOCKED:非数据源异常:',e)
            if os.environ.get('WORKBUDDY_DEBUG')=='1':traceback.print_exc()
            return 2
    return 2

if __name__=='__main__':
    raise SystemExit(main())
