#!/usr/bin/env python3
from __future__ import annotations
import csv,json,os,sys,tempfile
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))

from lhbpost.core import analyze_snapshot, model_bucket, validate_history_model, load_config, market_state, stage_market_fit

PASS=0;FAIL=0

def check(name,fn):
    global PASS,FAIL
    try:fn();PASS+=1;print('PASS',name)
    except Exception as e:FAIL+=1;print('FAIL',name,repr(e))

def market(normal=False):
    if normal:return {'up_count':3000,'down_count':2000,'limit_up_count':60,'limit_down_count':15,'broken_limit_up_count':20,'turnover_change_pct':3,'index_changes':{'a':.6,'b':.4},'source_time':'2026-09-10T18:00:00+08:00'}
    return {'up_count':955,'down_count':4512,'limit_up_count':40,'limit_down_count':14,'broken_limit_up_count':26,'turnover_change_pct':-8.2,'index_changes':{'a':-.43,'b':-.77,'c':-.49},'source_time':'2026-09-10T18:00:00+08:00'}

def stk(code='000993.SZ',name='闽东电力',streak=2,core=1,secstrong=True,r20=28,net=.03,inst=0,mheight=2):
    sm={'day_change_pct':2 if secstrong else -1,'up_ratio':.7 if secstrong else .25,'limit_up_count':5 if secstrong else 0,'two_plus_board_count':1 if streak>=2 else 0,'rel_strength_3d':3 if secstrong else -1,'rel_strength_5d':4 if secstrong else -1,'leader_advanced':streak>=2 and secstrong}
    turnover=1_000_000_000
    return {'code':code,'name':name,'board':'主板','risk_warning':False,'delisting_risk':False,'data_quality':'normal','change_pct':10,'turnover':turnover,'turnover_rate':16,'free_float_mcap':8_000_000_000,'days_return':{'3':15,'5':18,'10':20,'20':r20},'board_streak':streak,'market_height_rank':mheight,'sector':'测试','sector_core_rank':core,'sector_leader':core==1,'capacity_core':False,'sector_metrics':sm,'close_location':1.0,
            'rs_20d_pctile':.88,'ma20_slope_pctile':.84,'breakout_20d_strength':.90,'close_above_ma20':True,'ma5_gt_ma10_gt_ma20':True,'ma20_gt_ma60':True,'volume_health':.90,'startup_location_health':.82,
            'turnover_rate_pctile':.75,'free_mcap_pctile':.30,'lhb_net_free_float_pctile':.82,'sector_rs_5d_pctile':.86,'sector_activity_pctile':.78,
            'lhb_net_impact_pctile':.82,'lhb_participation_pctile':.72,'inst_net_impact_pctile':.65,'broker_net_impact_pctile':.78,'buy_sell_balance':.35,
            'lhb':{'listed':True,'buy5':150_000_000,'sell5':100_000_000,'net_buy':turnover*net,'buy1':40_000_000,'institution_net':inst,'connect_net':0,'broker_net':turnover*net-inst,'lifecycle_event_no':2,'lifecycle_net_improving':True,'seat_quality_pctile':.75,'seat_quality_samples':30},'post_close_events':[],'source_time':'2026-09-10T20:00:00+08:00','feature_provenance':{'source_time':'2026-09-10T20:00:00+08:00'}}

def snap(stocks=None,normal=False):return {'trade_date':'2026-09-10','as_of':'2026-09-10T21:00:00+08:00','market':market(normal),'stocks':stocks or [stk()]}

def audited(z):
    z=dict(z)
    z['pipeline']='raw-postmarket-v5.0-audited'
    z['raw_data_audit']={'passed':True,'warnings':[],'stats':{}}
    z['coverage']={
        'industry_pit':True,'event_feed':True,'market_full_features':True,'index_daily':True,
        'theme_pit':True,'seat_detail':True,'history_model':'external_at_analyze'
    }
    z['workflow_trace']=[{'step':s,'status':'完成','detail':'test'} for s in [
        '原始数据审计','时间截断','历史时点状态','市场环境','强势阶段','板块与题材',
        '市场/板块地位','价格透支','龙虎榜','盘后事件','历史样本','爆发力评分']]
    return z

def expect_value_error(obj):
    try:analyze_snapshot(obj)
    except ValueError:return
    raise AssertionError('expected ValueError')

check('future-pattern-rejected',lambda:expect_value_error({**snap(),'stocks':[{**stk(),'t1_return':.1}]}))
check('auction-nested-rejected',lambda:expect_value_error({**snap(),'stocks':[{**stk(),'extra':{'auction_volume':1}}]}))
check('future-evidence-time-rejected',lambda:expect_value_error({**snap(),'stocks':[{**stk(),'lhb':{**stk()['lhb'],'source_time':'2026-09-11T09:00:00+08:00'}}]}))
check('duplicate-event-rejected',lambda:expect_value_error(snap([stk(),stk()])))

def manual_position_not_trusted():
    s=stk(core=99,streak=1,mheight=99);s['market_position']='主线核心';r=analyze_snapshot(snap([s]))['results'][0];assert r['position']!='主线核心'
check('manual-position-not-trusted',manual_position_not_trusted)
check('market-in-history-bucket',lambda:(_ for _ in ()).throw(AssertionError()) if not model_bucket('强分歧','2板','主线核心','强势持续','低位/未见明显透支','确认').startswith('强分歧|') else None)

def seat_evidence_present():
    r=analyze_snapshot(snap())['results'][0];txt='|'.join(r['audit']['lhb_reasons']);assert '成熟席位质量百分位' in txt and r['audit']['lhb_metrics']['seat_quality_samples']==30
check('seat-quality-integrated',seat_evidence_present)

def manual_production_flag_rejected():
    m={'model_cutoff':'2026-09-09','validation_scheme':'walk_forward_oos','production_qualified':True,'buckets':{},'provenance_hash':'x','walk_forward_folds':[{'fold':'x'}],'acceptance':{'passed':False,'checks':{'a':False}}}
    assert validate_history_model(m,'2026-09-10',load_config())['status']=='拒绝'
check('manual-production-flag-rejected',manual_production_flag_rejected)

def qualified_model_can_upgrade():
    s=stk();b=model_bucket('强进攻','2板','主线核心','强势持续','低位/未见明显透支','确认')
    checks={'oos_sample_n_ge_300':True,'benchmark_coverage_ge_90pct':True,'t1_excess_bootstrap_5pct_gt_0':True,'t5_excess_bootstrap_5pct_gt_0':True,'at_least_3_oos_years':True,'positive_excess_year_ratio_ge_60pct':True,'single_year_positive_excess_le_60pct':True}
    m={'model_cutoff':'2026-09-09','validation_scheme':'walk_forward_oos','production_qualified':True,'provenance_hash':'abc','acceptance':{'passed':True,'checks':checks},'walk_forward_folds':[{'fold':'year_2025'}],'buckets':{b:{'sample_n':150,'t1_positive_rate':.65,'t3_positive_rate':.68,'t5_ge5_rate':.62,'t5_ge5_wilson_lower90':.50,'avg_return_t5':.055,'avg_return_t5_bootstrap_lower90':.025,'benchmark_excess_t5':.035,'benchmark_excess_t5_bootstrap_lower90':.012,'avg_mae_5d':-.035}}}
    z=audited(snap([s],normal=True));z['market']['causal_market']={'data_quality':'normal','state':'全面主升','permission':'正常','breadth_pctile':.8,'sentiment_pctile':.8,'risk_pctile':.2}
    r=analyze_snapshot(z,history_model=m);assert r['history_model']['status']=='拒绝' and r['results'][0]['conclusion']!='核心候选'
check('self-reported-qualified-model-rejected',qualified_model_can_upgrade)

def regression_structure():
    a=stk('000993.SZ','闽东电力',2,1,True,28,.008,-20_000_000,2)
    b=stk('002636.SZ','金安国纪',1,2,True,55,.115,200_000_000,8)
    r=analyze_snapshot(snap([b,a]));names=[x['name'] for x in r['results']];assert names.index('闽东电力')<names.index('金安国纪')
check('sep10-structure-regression',regression_structure)

def future_plain_date_rejected():
    z=snap();z['stocks'][0]['extra']={'event_date':'2026-09-11'};expect_value_error(z)
check('future-plain-date-rejected',future_plain_date_rejected)

def malformed_plain_date_rejected():
    z=snap();z['stocks'][0]['extra']={'event_date':'not-a-date'};expect_value_error(z)
check('malformed-date-not-silently-ignored',malformed_plain_date_rejected)

def market_flat_count_must_be_in_breadth():
    m={'up_count':52,'down_count':33,'flat_count':15,'limit_up_count':30,'limit_down_count':10,'turnover_change_pct':1,'index_changes':{'a':.2}}
    st,_=market_state(m,load_config());assert st=='正常轮动',st
check('market-breadth-includes-flat-count',market_flat_count_must_be_in_breadth)

def missing_coverage_degrades():
    r=analyze_snapshot(snap([stk()],normal=True));assert CONCLUSION_RANK_TEST(r['candidate_level_cap'])<=CONCLUSION_RANK_TEST('重点观察')
def CONCLUSION_RANK_TEST(x):
    return {'核心候选':7,'重点候选A':6,'重点候选B':5,'重点观察':4,'次级观察':3,'风险观察':2,'特殊观察池':1,'剔除':0}.get(x,-1)
check('missing-coverage-degrades',missing_coverage_degrades)

def causal_market_more_conservative():
    z=snap([stk()],normal=True);z['coverage']={'industry_pit':True,'event_feed':True,'market_full_features':True};z['market']['causal_market']={'data_quality':'normal','state':'退潮','permission':'暂停','breadth_pctile':.2,'sentiment_pctile':.2,'risk_pctile':.9}
    r=analyze_snapshot(z);assert r['market_state']=='退潮' and CONCLUSION_RANK_TEST(r['candidate_level_cap'])<=CONCLUSION_RANK_TEST('风险观察')
check('causal-market-gate-used',causal_market_more_conservative)

def medium_event_must_downgrade():
    a=stk();b=stk('000992.SZ','对照股');a['post_close_events']=[{'title':'中等风险','risk_level':'medium','risk_penalty':.6,'public_time':'2026-09-10T20:30:00+08:00'}]
    a['risk_penalty']=.6
    z=snap([a,b]);r=analyze_snapshot(z);d={x['name']:x for x in r['results']}
    assert d['闽东电力']['short_burst_score']<d['对照股']['short_burst_score'] and d['闽东电力']['score_risk_penalty']>=8
check('medium-event-risk-downgrades',medium_event_must_downgrade)

def recent_ipo_cap():
    s=stk();s['recent_ipo_immature']=True;z=snap([s]);r=analyze_snapshot(z)['results'][0];assert CONCLUSION_RANK_TEST(r['conclusion'])<=CONCLUSION_RANK_TEST('重点观察')
check('recent-ipo-6-19d-cap',recent_ipo_cap)

def full_markdown_not_simplified():
    from workbuddy_entry import render_md
    r=analyze_snapshot(snap([stk()]));md=render_md(r)
    assert '工作流执行审计' in md and '全候选排序' in md and '逐股完整证据链' in md and '数据覆盖' in md and '原始数据审计' in md
check('full-markdown-exposes-workflow',full_markdown_not_simplified)

def prepare_snapshot_cannot_skip_audit():
    from types import SimpleNamespace
    from workbuddy_entry import prepare_cmd
    with tempfile.TemporaryDirectory() as td:
        a=SimpleNamespace(data_root=td,trade_date='2026-09-10',as_of='2026-09-10T21:00:00+08:00',output=str(Path(td)/'x.json'))
        try:prepare_cmd(a)
        except ValueError as ex:
            assert '原始数据审计失败' in str(ex);return
        raise AssertionError('prepare-snapshot must run audit first')
check('prepare-snapshot-forces-audit',prepare_snapshot_cannot_skip_audit)

def audited_pipeline_requires_audit_proof():
    z=snap();z['pipeline']='raw-postmarket-v5.0-audited';z['coverage']={'industry_pit':True,'event_feed':True,'market_full_features':True,'index_daily':True,'theme_pit':True,'seat_detail':True,'history_model':'x'};z['workflow_trace']=[{'step':s} for s in ['原始数据审计','时间截断','历史时点状态','市场环境','强势阶段','板块与题材','市场/板块地位','价格透支','龙虎榜','盘后事件','历史样本','爆发力评分']]
    expect_value_error(z)
check('audited-pipeline-requires-audit-proof',audited_pipeline_requires_audit_proof)

def audited_pipeline_rejects_missing_step():
    z=audited(snap());z['workflow_trace']=[x for x in z['workflow_trace'] if x['step']!='价格透支'];expect_value_error(z)
check('audited-pipeline-rejects-missing-workflow-step',audited_pipeline_rejects_missing_step)

def unverified_pipeline_is_forced_degraded():
    z=snap();z['pipeline']='raw-postmarket-v5.0-unverified';z['coverage']={'industry_pit':True,'event_feed':True,'market_full_features':True,'index_daily':True,'theme_pit':True,'seat_detail':True,'history_model':'x'};z['market']['causal_market']={'data_quality':'normal','state':'全面主升','permission':'正常','breadth_pctile':.8,'sentiment_pctile':.8,'risk_pctile':.2}
    r=analyze_snapshot(z);assert CONCLUSION_RANK_TEST(r['candidate_level_cap'])<=CONCLUSION_RANK_TEST('重点观察') and '禁止冒充完整管线' in '|'.join(r['market_reasons'])
check('unverified-pipeline-cannot-claim-production',unverified_pipeline_is_forced_degraded)

def audited_pipeline_requires_coverage_keys():
    z=audited(snap());del z['coverage']['seat_detail'];expect_value_error(z)
check('audited-pipeline-requires-complete-coverage-metadata',audited_pipeline_requires_coverage_keys)



def technical_features_must_change_score_and_rank():
    strong=stk('000001.SZ','强技术')
    weak=stk('000002.SZ','弱技术')
    for k,v in {'rs_20d_pctile':.05,'ma20_slope_pctile':.05,'breakout_20d_strength':0.0,'close_location':.25,'volume_health':.15,'startup_location_health':.20}.items():weak[k]=v
    weak['close_above_ma20']=False;weak['ma5_gt_ma10_gt_ma20']=False;weak['ma20_gt_ma60']=False
    r=analyze_snapshot(snap([weak,strong]))['results'];d={x['name']:x for x in r}
    assert d['强技术']['short_burst_score']>d['弱技术']['short_burst_score']+10
    assert r[0]['name']=='强技术'
check('technical-factors-have-real-sensitivity',technical_features_must_change_score_and_rank)


def deterministic_tie_not_input_order():
    a=stk('000001.SZ','A');b=stk('000002.SZ','B')
    r1=analyze_snapshot(snap([b,a]))['results'];r2=analyze_snapshot(snap([a,b]))['results']
    assert [x['code'] for x in r1]==[x['code'] for x in r2]
    assert r1[0]['code']=='000001.SZ'
check('tie-break-independent-of-input-order',deterministic_tie_not_input_order)


def stage_fit_changes_with_market_cycle():
    assert stage_market_fit('3板及以上','强进攻')>stage_market_fit('2板','强进攻')
    assert stage_market_fit('2板','正常轮动')>stage_market_fit('3板及以上','正常轮动')
    assert stage_market_fit('趋势强势','退潮')>stage_market_fit('3板及以上','退潮')
check('stage-is-market-conditioned-not-fixed-rank',stage_fit_changes_with_market_cycle)


def bad_history_bucket_cannot_upgrade():
    s=stk();b=model_bucket('强进攻','2板','主线核心','强势持续','低位/未见明显透支','确认')
    checks={'oos_sample_n_ge_300':True,'benchmark_coverage_ge_90pct':True,'t1_excess_bootstrap_5pct_gt_0':True,'t5_excess_bootstrap_5pct_gt_0':True,'at_least_3_oos_years':True,'positive_excess_year_ratio_ge_60pct':True,'single_year_positive_excess_le_60pct':True}
    m={'model_cutoff':'2026-09-09','validation_scheme':'walk_forward_oos','production_qualified':True,'provenance_hash':'bad','acceptance':{'passed':True,'checks':checks},'walk_forward_folds':[{'fold':'year_2025'}],
       'buckets':{b:{'sample_n':150,'t1_positive_rate':.2,'t3_positive_rate':.2,'t5_ge5_rate':.10,'t5_ge5_wilson_lower90':.06,'avg_return_t5':-.08,'avg_return_t5_bootstrap_lower90':-.10,'benchmark_excess_t5':-.10,'benchmark_excess_t5_bootstrap_lower90':-.12,'avg_mae_5d':-.15}}}
    z=audited(snap([s],normal=True));z['market']['causal_market']={'data_quality':'normal','state':'全面主升','permission':'正常','breadth_pctile':.8,'sentiment_pctile':.8,'risk_pctile':.2}
    x=analyze_snapshot(z,history_model=m)['results'][0]
    assert x['conclusion']!='核心候选' and not x['history_stats']['available']
    from lhbpost.core import _history_strength, evidence_conclusion
    strength,_,_= _history_strength(m['buckets'][b],150,load_config())
    assert strength=='强负向'
    final,_=evidence_conclusion(95,[],'强进攻','核心候选',False,False,{'available':True,'confidence':'中','strength':strength},{'production_qualified':True},load_config())
    assert CONCLUSION_RANK_TEST(final)<=CONCLUSION_RANK_TEST('重点观察')
check('bad-history-never-upgrades-by-sample-size',bad_history_bucket_cannot_upgrade)


def score_components_are_complete_and_auditable():
    x=analyze_snapshot(snap([stk()]))['results'][0]
    assert set(x['score_components'])=={'技术动量','结构地位','资金质量','资金弹性','事件驱动','历史验证'}
    assert isinstance(x['audit']['score_factor_details'],dict) and x['score_meaning'].startswith('0-100')
check('score-components-complete',score_components_are_complete_and_auditable)

def workflow_steps_are_upserted_not_duplicated():
    z=audited(snap([stk()]))
    r=analyze_snapshot(z)
    steps=[x.get('step') for x in r['workflow_trace'] if isinstance(x,dict)]
    assert steps.count('爆发力评分')==1
    assert steps.count('风险否决与最终排序')==1
check('workflow-no-fake-duplicate-execution',workflow_steps_are_upserted_not_duplicated)

# pandas-based engineering tests
try:
 import pandas as pd, numpy as np
 from lhbpost.features import aggregate_lhb,assign_lifecycle,map_industry_point_in_time
 from lhbpost.seat_quality import build_mature_seat_quality,_dedupe_seat_events
 from lhbpost.snapshot_pipeline import _short_term_core_rank,_cut
 from lhbpost.data.normalized_store import NormalizedStore
 from lhbpost.data_audit import audit_raw_data
 from lhbpost.research import build_model
 from lhbpost.market_features import build_market_features

 def agg_3d_denominator():
    dates=pd.to_datetime(['2026-09-08','2026-09-09','2026-09-10']);daily=pd.DataFrame({'trade_date':dates,'ts_code':['A']*3,'amount':[100.,100.,100.]})
    tl=pd.DataFrame({'trade_date':[dates[-1]],'ts_code':['A'],'l_buy':[60.],'l_sell':[30.],'reason':['连续三个交易日涨幅偏离']})
    ti=pd.DataFrame();r=aggregate_lhb(tl,ti,daily).iloc[0];assert abs(r['lhb_net_buy_ratio']-.1)<1e-9
 check('lhb-3d-denominator',agg_3d_denominator)

 def dual_window_preserved():
    dt=pd.Timestamp('2026-09-10');dates=pd.to_datetime(['2026-09-08','2026-09-09','2026-09-10'])
    daily=pd.DataFrame({'trade_date':dates,'ts_code':['A']*3,'amount':[100.,100.,100.]})
    tl=pd.DataFrame({'trade_date':[dt,dt],'ts_code':['A','A'],'l_buy':[30.,60.],'l_sell':[10.,30.],'reason':['日涨幅偏离','连续三个交易日涨幅偏离']})
    r=aggregate_lhb(tl,pd.DataFrame(),daily).iloc[0]
    assert r['window_type']=='daily' and abs(r['daily_lhb_net_buy_ratio']-.2)<1e-9 and abs(r['three_day_lhb_net_buy_ratio']-.1)<1e-9 and r['has_daily_window'] and r['has_three_day_window']
 check('lhb-dual-window-preserved',dual_window_preserved)

 def core_uses_matched_window_denominator():
    s=stk();s['turnover']=1_000_000_000;s['lhb']={**s['lhb'],'net_buy':300_000_000,'buy5':600_000_000,'sell5':300_000_000,'impact_denominator':3_000_000_000}
    r=analyze_snapshot(snap([s]))['results'][0];assert abs(r['audit']['lhb_metrics']['net_buy_ratio']-.1)<1e-12
 check('core-uses-matched-window-denominator',core_uses_matched_window_denominator)

 def connect_not_broker():
    dt=pd.Timestamp('2026-09-10');daily=pd.DataFrame({'trade_date':[dt],'ts_code':['A'],'amount':[100.]});tl=pd.DataFrame({'trade_date':[dt],'ts_code':['A'],'l_buy':[30.],'l_sell':[10.],'reason':['日涨幅偏离']})
    ti=pd.DataFrame({'trade_date':[dt,dt],'ts_code':['A','A'],'exalter':['深股通专用','某营业部'],'buy':[10.,5.],'sell':[1.,2.],'net_buy':[9.,3.],'reason':['日涨幅偏离']*2})
    r=aggregate_lhb(tl,ti,daily).iloc[0];assert r['connect_net']==9 and r['broker_net']==3
 check('connect-not-broker',connect_not_broker)

 def lifecycle_trade_days():
    e=pd.DataFrame({'trade_date':pd.to_datetime(['2026-09-07','2026-09-10']),'ts_code':['A','A'],'lhb_net_buy_ratio':[.01,.02]});cal=pd.to_datetime(['2026-09-07','2026-09-08','2026-09-09','2026-09-10'])
    r=assign_lifecycle(e,cal);assert list(r['lifecycle_event_no'])==[1,2] and bool(r.iloc[1]['lifecycle_net_improving'])
 check('lifecycle-by-market-days',lifecycle_trade_days)

 def pit_industry():
    s=pd.DataFrame({'trade_date':pd.to_datetime(['2020-01-02','2022-01-02']),'ts_code':['A','A']});m=pd.DataFrame({'ts_code':['A','A'],'l1_code':['OLD','NEW'],'l1_name':['旧','新'],'in_date':pd.to_datetime(['2019-01-01','2021-01-01']),'out_date':pd.to_datetime(['2020-12-31','2025-12-31'])})
    r=map_industry_point_in_time(s,m).sort_values('trade_date');assert list(r['l1_code'])==['OLD','NEW']
 check('pit-industry-mapping',pit_industry)

 def mature_seat_no_future():
    cal=pd.bdate_range('2026-01-01',periods=30);daily=pd.DataFrame({'trade_date':list(cal)*1,'ts_code':['A']*30,'close':np.arange(30)+10,'high':np.arange(30)+10.5,'low':np.arange(30)+9.5})
    st=pd.DataFrame({'trade_date':[cal[2]],'ts_code':['A'],'exalter':['席位X'],'buy':[10.],'sell':[0.],'net_buy':[10.]})
    q=build_mature_seat_quality(st,daily,trade_dates=cal);assert len(q)>0 and q['asof_date'].min()>cal[12]
 check('seat-label-maturity',mature_seat_no_future)

 def normalized_units():
    with tempfile.TemporaryDirectory() as td:
      p=Path(td);(p/'daily').mkdir();pd.DataFrame([{'ts_code':'A','trade_date':'20260910','open':1,'high':1,'low':1,'close':1,'vol':2,'amount':3,'pct_chg':.5}]).to_csv(p/'daily/20260910.csv',index=False)
      r=NormalizedStore(p).daily().iloc[0];assert r['vol']==200 and r['amount']==3000 and abs(r['pct_chg']-.005)<1e-12
 check('normalized-store-units',normalized_units)

 def market_features_no_hidden_hand_weights():
    dates=pd.bdate_range('2025-01-01',periods=150);rows=[];lims=[];ix=[]
    for j in range(30):
      code=f'{j:06d}.SZ'
      for i,dt in enumerate(dates):
       base=10+j*.05+i*.002;chg=((j+i)%9-4)/1000;close=base*(1+chg)
       rows.append({'ts_code':code,'trade_date':dt,'open':base,'high':max(base,close)*1.01,'low':min(base,close)*.99,'close':close,'amount':1e7*(1+(i%7)/10),'vol':1e6,'pct_chg':chg})
       lims.append({'ts_code':code,'trade_date':dt,'up_limit':base*1.1,'down_limit':base*.9})
    for dt in dates:ix.append({'ts_code':'000001.SH','trade_date':dt,'close':3000+len(ix)*.3,'pct_chg':.0001,'amount':1e11})
    from lhbpost.features import build_stock_daily_features
    sf=build_stock_daily_features(pd.DataFrame(rows));mf=build_market_features(sf,pd.DataFrame(lims),pd.DataFrame(ix));r=mf.iloc[-1]
    exp=float(pd.Series([r['limit_up_count_p'],r['prev_limit_median_return_p'],r['prev_limit_red_rate_p']]).median())
    assert abs(float(r['sentiment_pctile'])-exp)<1e-12
    exptrend=float(pd.Series([r['pct_above_ma20_p'],r['pct_above_ma60_p'],r['index_above20_pctile']]).median())
    assert abs(float(r['trend_pctile'])-exptrend)<1e-12
 check('market-features-no-hidden-hand-weights',market_features_no_hidden_hand_weights)

 def physical_cut_removes_future_rows():
    d=pd.DataFrame({'trade_date':pd.to_datetime(['2026-09-10','2026-09-11']),'ts_code':['A','A'],'close':[1,999]})
    r=_cut(d,pd.Timestamp('2026-09-10'));assert len(r)==1 and r.iloc[0]['close']==1
 check('physical-time-cut-before-features',physical_cut_removes_future_rows)

 def short_term_core_rank_prioritizes_stage():
    dt=pd.Timestamp('2026-09-10')
    sf=pd.DataFrame({'trade_date':[dt,dt],'ts_code':['A','B'],'g':['X','X'],'pct_chg':[.05,.10],'ret5':[.05,.50],'amount':[10.,100.]})
    st=pd.DataFrame({'trade_date':[dt,dt],'ts_code':['A','B'],'board_streak':[2,1],'is_limit_up':[True,True]})
    r=_short_term_core_rank(sf,st,'g','z');rank=dict(zip(r.ts_code,r.z_core_rank));assert rank['A']==1 and rank['B']==2
 check('short-term-sector-core-stage-first',short_term_core_rank_prioritizes_stage)

 def seat_multi_reason_deduped():
    dt=pd.Timestamp('2026-09-10');st=pd.DataFrame({'trade_date':[dt,dt],'ts_code':['A','A'],'exalter':['S','S'],'buy':[10.,30.],'sell':[1.,2.],'reason':['日涨幅偏离','连续三个交易日涨幅偏离']})
    r=_dedupe_seat_events(st);assert len(r)==1 and r.iloc[0]['reason']=='日涨幅偏离'
 check('seat-multi-reason-not-double-counted',seat_multi_reason_deduped)

 def audit_forbidden_even_when_core_complete():
    with tempfile.TemporaryDirectory() as td:
      p=Path(td)
      for d in ['daily','daily_basic','adj_factor','bak_basic','stock_st','stk_limit','top_list','top_inst']:(p/d).mkdir()
      pd.DataFrame(columns=['cal_date']).to_csv(p/'trade_cal.csv',index=False);pd.DataFrame(columns=['ts_code','name']).to_csv(p/'stock_basic.csv',index=False);pd.DataFrame(columns=['ts_code','l1_code','in_date']).to_csv(p/'sw_members.csv',index=False)
      schemas={'daily':['ts_code','trade_date','open','high','low','close','vol','amount'],'daily_basic':['ts_code','trade_date'],'adj_factor':['ts_code','trade_date','adj_factor'],'stk_limit':['ts_code','trade_date','up_limit','down_limit'],'top_list':['ts_code','trade_date'],'top_inst':['ts_code','trade_date']}
      for d,cols in schemas.items():pd.DataFrame(columns=cols).to_csv(p/d/'20260910.csv',index=False)
      (p/'mins_5m').mkdir();r=audit_raw_data(p);assert not r.passed and any('禁止的盘中/竞价目录' in e for e in r.errors)
 check('forbidden-dir-fails-even-core-complete',audit_forbidden_even_when_core_complete)

 def audit_forbidden_dirs_fail():
    with tempfile.TemporaryDirectory() as td:
      p=Path(td);(p/'mins_5m').mkdir();r=audit_raw_data(p);assert any('禁止的盘中/竞价目录' in e for e in r.errors) and not r.passed
 check('data-audit-forbidden-dir-hard-fail',audit_forbidden_dirs_fail)

 def _make_audit_fixture(p,dates=('20260907','20260908','20260909','20260910')):
    for d in ['daily','daily_basic','adj_factor','bak_basic','stock_st','stk_limit','top_list','top_inst']:(p/d).mkdir(parents=True,exist_ok=True)
    pd.DataFrame({'cal_date':list(dates),'is_open':['1']*len(dates)}).to_csv(p/'trade_cal.csv',index=False)
    pd.DataFrame([{'ts_code':'000001.SZ','name':'A','list_date':'20000101'}]).to_csv(p/'stock_basic.csv',index=False)
    pd.DataFrame([{'ts_code':'000001.SZ','l1_code':'801010.SI','in_date':'20000101','out_date':''}]).to_csv(p/'sw_members.csv',index=False)
    for dt in dates:
      pd.DataFrame([{'ts_code':'000001.SZ','trade_date':dt,'open':1,'high':1,'low':1,'close':1,'vol':1,'amount':1}]).to_csv(p/'daily'/f'{dt}.csv',index=False)
      pd.DataFrame([{'ts_code':'000001.SZ','trade_date':dt}]).to_csv(p/'daily_basic'/f'{dt}.csv',index=False)
      pd.DataFrame([{'ts_code':'000001.SZ','trade_date':dt,'adj_factor':1}]).to_csv(p/'adj_factor'/f'{dt}.csv',index=False)
      pd.DataFrame([{'ts_code':'000001.SZ','trade_date':dt}]).to_csv(p/'bak_basic'/f'{dt}.csv',index=False)
      pd.DataFrame(columns=['ts_code','trade_date']).to_csv(p/'stock_st'/f'{dt}.csv',index=False)
      pd.DataFrame([{'ts_code':'000001.SZ','trade_date':dt,'up_limit':1.1,'down_limit':.9}]).to_csv(p/'stk_limit'/f'{dt}.csv',index=False)
      pd.DataFrame(columns=['ts_code','trade_date']).to_csv(p/'top_list'/f'{dt}.csv',index=False)
      pd.DataFrame(columns=['ts_code','trade_date']).to_csv(p/'top_inst'/f'{dt}.csv',index=False)

 def audit_checks_every_file_not_first_three_only():
    with tempfile.TemporaryDirectory() as td:
      p=Path(td);_make_audit_fixture(p);pd.DataFrame([{'ts_code':'000001.SZ','trade_date':'20260910'}]).to_csv(p/'daily_basic/20260910.csv',index=False)
      # 第4个文件故意缺字段不是好测试，因为daily_basic最低字段仍齐；改成错误日期字段名。
      pd.DataFrame([{'ts_code':'000001.SZ','bad_date':'20260910'}]).to_csv(p/'daily_basic/20260910.csv',index=False)
      r=audit_raw_data(p,require_end='2026-09-10');assert not r.passed and any('daily_basic/20260910.csv缺字段' in x for x in r.errors)
 check('audit-checks-all-file-headers',audit_checks_every_file_not_first_three_only)

 def audit_requires_sparse_daily_snapshots_too():
    with tempfile.TemporaryDirectory() as td:
      p=Path(td);_make_audit_fixture(p);(p/'top_list/20260909.csv').unlink()
      r=audit_raw_data(p,require_end='2026-09-10');assert not r.passed and any('top_list缺少1个交易日快照' in x for x in r.errors)
 check('audit-no-silent-missing-lhb-day',audit_requires_sparse_daily_snapshots_too)

 def audit_event_schema_requires_public_time():
    with tempfile.TemporaryDirectory() as td:
      p=Path(td);_make_audit_fixture(p);pd.DataFrame(columns=['trade_date','ts_code']).to_csv(p/'event_features.csv',index=False)
      r=audit_raw_data(p,require_end='2026-09-10');assert not r.passed and any('event_features.csv缺字段' in x for x in r.errors)
 check('audit-event-time-required',audit_event_schema_requires_public_time)

 def model_no_benchmark_no_production():
    with tempfile.TemporaryDirectory() as td:
      f=Path(td)/'e.csv';o=Path(td)/'m.json';cols=['event_date','model_bucket','return_t1','return_t3','return_t5','max_return_t5','max_drawdown_t5']
      with f.open('w',newline='',encoding='utf-8') as fh:
       w=csv.DictWriter(fh,fieldnames=cols);w.writeheader()
       for i in range(320):
        y=2023+(i%3);w.writerow({'event_date':f'{y}-01-{1+i%20:02d}','model_bucket':'X','return_t1':.01,'return_t3':.02,'return_t5':.03,'max_return_t5':.05,'max_drawdown_t5':-.02})
      m=build_model(f,'2026-09-10',o);assert not m['production_qualified'] and m['provenance_hash']
 check('model-requires-benchmark',model_no_benchmark_no_production)

 def model_walk_forward_dynamic():
    with tempfile.TemporaryDirectory() as td:
      f=Path(td)/'e.csv';o=Path(td)/'m.json';cols=['event_date','model_bucket','return_t1','return_t3','return_t5','max_return_t5','max_drawdown_t5','benchmark_return_t1','benchmark_return_t5','benchmark_max_return_t5','benchmark_max_drawdown_t5']
      with f.open('w',newline='',encoding='utf-8') as fh:
       w=csv.DictWriter(fh,fieldnames=cols);w.writeheader()
       for y in range(2019,2027):
        for i in range(70):
         m=1+(i//20);d=1+(i%20);w.writerow({'event_date':f'{y}-{m:02d}-{d:02d}','model_bucket':'X','return_t1':.02,'return_t3':.03,'return_t5':.04,'max_return_t5':.06,'max_drawdown_t5':-.01,'benchmark_return_t1':0,'benchmark_return_t5':0,'benchmark_max_return_t5':.01,'benchmark_max_drawdown_t5':-.02})
       for d in range(1,21):
        w.writerow({'event_date':f'2026-08-{d:02d}','model_bucket':'X','return_t1':.02,'return_t3':.03,'return_t5':.04,'max_return_t5':.06,'max_drawdown_t5':-.01,'benchmark_return_t1':0,'benchmark_return_t5':0,'benchmark_max_return_t5':.01,'benchmark_max_drawdown_t5':-.02})
      m=build_model(f,'2026-09-10',o);assert m['validation_scheme']=='walk_forward_oos' and len(m['walk_forward_folds'])>=3 and m['split_counts'].get('observation',0)>0
 check('model-dynamic-walk-forward',model_walk_forward_dynamic)
except Exception as e:
 print('PANDAS_TEST_SETUP_FAILED',repr(e));FAIL+=1

print(f'CORE_TEST_SUMMARY passed={PASS} failed={FAIL}')
if FAIL:sys.exit(1)
# 继承自第二技能且仍属于纯盘后范围的pytest回归。
try:
 import subprocess
 inherited=[str(p) for p in sorted(Path(__file__).parent.glob('test_*.py'))]
 env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'scripts')+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '');rc=subprocess.call([sys.executable,'-m','pytest','-q','-p','no:cacheprovider',*inherited],env=env)
 if rc!=0:sys.exit(rc)
 print('ALL_DISCOVERED_PYTEST_MODULES_PASSED')
except Exception as ex:
 print('TEST_EXECUTION_FAILED',repr(ex));sys.exit(1)
print('ALL_TESTS_PASSED')
