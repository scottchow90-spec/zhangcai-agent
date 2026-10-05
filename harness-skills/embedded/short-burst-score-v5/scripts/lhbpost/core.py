#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A股盘后短线爆发力评分引擎 v5.0。

只处理 T 日收盘后已知信息；拒绝盘中、集合竞价、T+1 及之后字段。
输出透明、可审计的短线爆发力相对评分；未经历史样本外校准时，评分绝不冒充预测概率。
"""
from __future__ import annotations

import json
import math
import re
import hashlib
import copy
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "templates" / "default-config.json"

FORBIDDEN_KEYS = {
    "next_day_return", "t_plus_1", "t_plus_3", "t_plus_5", "future_return",
    "next_open", "next_close", "next_high", "next_low", "next_auction",
    "next_day_high", "next_day_low", "future_price", "future_label",
    "auction_gap", "auction_price", "call_auction", "竞价涨幅", "竞价成交额",
    "minute_bars", "intraday_signal", "five_minute_confirm", "分时信号", "盘中确认"
}
FORBIDDEN_KEY_PATTERNS = [
    re.compile(r"(^|_)(next|future|t\+?1|t\+?2|t\+?3|t\+?4|t\+?5)(_|$)", re.I),
    re.compile(r"auction|竞价|minute|intraday|分时|盘中", re.I),
]
TIME_FIELDS = {"source_time","public_time","published_at","evidence_time","as_of_time"}
DATE_FIELDS = {"trade_date","event_date","reference_date","asof_date","mature_date"}


POSITION_RANK = {
    "主线核心": 7,
    "板块最高板": 7,
    "板块前排": 6,
    "容量核心": 5,
    "独立强势": 4,
    "弱板块孤立强股": 3,
    "后排跟风": 1,
    "板块退潮": 0,
    "未知": 0,
}
SECTOR_RANK = {"强势持续": 3, "中性/轮动": 2, "弱势": 1, "退潮": 0, "未知": 0}
LHB_RANK = {"确认": 2, "弱确认": 1, "中性": 0, "集中风险": -1, "负面": -2, "无龙虎榜": -3}
OVERHEAT_RISK = {"低位/未见明显透支": 0, "正常加速": 1, "高位拥挤": 2, "末端透支": 3}
CONCLUSION_RANK = {
    "核心候选": 7,
    "重点候选A": 6,
    "重点候选B": 5,
    "重点观察": 4,
    "次级观察": 3,
    "风险观察": 2,
    "特殊观察池": 1,
    "剔除": 0,
}
MARKET_CAP = {
    "强进攻": "核心候选",
    "正常轮动": "核心候选",
    "强分歧": "重点候选A",
    "退潮": "重点观察",
    "极端风险": "风险观察",
}
CAUSAL_MARKET_MAP = {
    "全面主升": "强进攻",
    "结构性主升": "正常轮动",
    "震荡可做": "正常轮动",
    "修复": "强分歧",
    "结构严重分化": "强分歧",
    "退潮": "退潮",
    "恐慌": "极端风险",
}
PERMISSION_CAP = {"正常":"核心候选","精选":"重点候选A","小仓试错":"重点观察","暂停":"风险观察"}
STATE_SEVERITY = {"强进攻":0,"正常轮动":1,"强分歧":2,"退潮":3,"极端风险":4}

REQUIRED_PREANALYSIS_STEPS = [
    "原始数据审计", "时间截断", "历史时点状态", "市场环境", "强势阶段",
    "板块与题材", "市场/板块地位", "价格透支", "龙虎榜", "盘后事件", "历史样本", "爆发力评分",
]
REQUIRED_COVERAGE_KEYS = {"market_full_features","index_daily","industry_pit","theme_pit","event_feed","seat_detail","history_model"}
SCORING_FEATURES = {
    'rs_20d_pctile', 'ma20_slope_pctile', 'breakout_20d_strength', 'close_location',
    'volume_health', 'startup_location_health', 'close_above_ma20', 'ma5_gt_ma10_gt_ma20',
    'ma20_gt_ma60', 'sector_rs_5d_pctile', 'sector_activity_pctile', 'turnover_rate_pctile',
    'free_mcap_pctile', 'lhb_net_free_float_pctile', 'lhb_net_impact_pctile',
    'lhb_participation_pctile', 'inst_net_impact_pctile', 'broker_net_impact_pctile', 'buy_sell_balance',
}
BOOL_FIELDS = {
    'risk_warning','is_st','delisting_risk','is_delisting_arrangement','new_unlimited',
    'recent_ipo_immature','sector_leader','capacity_core','industry_capacity_core','theme_capacity_core',
    'theme_verified','leader_advanced','close_above_ma20','ma5_gt_ma10_gt_ma20','ma20_gt_ma60',
    'independent_catalyst','catalyst_public_before_cutoff','market_climax','severe_negative_event',
    'downward_anomaly_without_reversal','three_day_surge_high_climax','extreme_volume_inst_sell_weak_relay',
    'broken_limit_weak_close','listed','lifecycle_net_improving','concept_denial',
}


def validate_config(cfg: Dict[str, Any]) -> None:
    """Reject misspelled/invalid weights and risk bonuses before any scoring."""
    reference = json.loads(DEFAULT_CONFIG.read_text(encoding='utf-8-sig'))
    errors = []
    def check(actual, expected, path='config'):
        if isinstance(expected, dict):
            if not isinstance(actual, dict) or set(actual) != set(expected):
                errors.append(path + ' 配置字段缺失或含未知字段'); return
            for key, value in expected.items(): check(actual[key], value, path+'.'+key)
        elif isinstance(expected, (int, float)):
            if isinstance(actual, bool) or not isinstance(actual, (int, float)) or not math.isfinite(actual):
                errors.append(path+' 必须是有限数值')
        elif not isinstance(actual, type(expected)):
            errors.append(path+' 类型错误')
    check(cfg, reference)
    if errors: raise ValueError('; '.join(errors))
    scoring = cfg['scoring']
    for key, values in scoring.items():
        if key.endswith('_weights'):
            if any(v < 0 for v in values.values()) or not math.isclose(sum(values.values()), 1.0, abs_tol=1e-8):
                errors.append(key+' 权重必须非负且合计为1')
    if any(v < 0 for v in scoring['risk_penalty'].values()): errors.append('风险扣分不得为负数')
    th = scoring['conclusion_thresholds']
    ordered = [th[k] for k in ('core','candidate_a','candidate_b','watch','secondary')]
    if not (100 >= ordered[0] and ordered[-1] >= 0 and all(a>b for a,b in zip(ordered,ordered[1:]))):
        errors.append('候选阈值必须在0到100之间严格递减')
    h=cfg['history']
    if not (1 <= h['min_sample'] <= h['medium_sample'] <= h['high_sample']): errors.append('历史样本阈值顺序错误')
    if errors: raise ValueError('; '.join(errors))


def load_config(path: str | Path | None = None) -> Dict[str, Any]:
    p = Path(path) if path else DEFAULT_CONFIG
    cfg = json.loads(p.read_text(encoding="utf-8-sig"))
    validate_config(cfg)
    return cfg


def parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(str(value))
    if dt.tzinfo is None:
        raise ValueError(f"时间必须带时区: {value}")
    return dt


def iter_keys(obj: Any) -> Iterable[str]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from iter_keys(v)
    elif isinstance(obj, list):
        for x in obj:
            yield from iter_keys(x)


def _f(v: Any, default: float = 0.0) -> float:
    try:
        x = float(v)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def _forbidden_key(k: str) -> bool:
    if k in FORBIDDEN_KEYS:
        return True
    return any(p.search(k) for p in FORBIDDEN_KEY_PATTERNS)

def _walk(obj: Any, path: str = ""):
    if isinstance(obj, dict):
        for k,v in obj.items():
            pp=f"{path}.{k}" if path else str(k)
            yield pp,str(k),v
            yield from _walk(v,pp)
    elif isinstance(obj,list):
        for i,v in enumerate(obj):
            yield from _walk(v,f"{path}[{i}]")


def _validate_production_workflow(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    pipeline=str(data.get("pipeline") or "")
    if pipeline != "raw-postmarket-v5.0-audited":
        return errors
    audit=data.get("raw_data_audit")
    if not isinstance(audit,dict) or audit.get("passed") is not True:
        errors.append("生产管线缺少通过的raw_data_audit，禁止把未审计快照冒充完整生产结果")
    cov=data.get("coverage")
    if not isinstance(cov,dict):
        errors.append("生产管线缺少coverage元数据")
    else:
        miss=sorted(REQUIRED_COVERAGE_KEYS-set(cov))
        if miss: errors.append("生产管线coverage缺键:"+",".join(miss))
    wf=data.get("workflow_trace")
    if not isinstance(wf,list):
        errors.append("生产管线缺少workflow_trace")
        return errors
    steps=[str(x.get("step")) for x in wf if isinstance(x,dict)]
    pos=-1
    for req in REQUIRED_PREANALYSIS_STEPS:
        try:i=steps.index(req,pos+1)
        except ValueError:
            errors.append(f"完整工作流缺少步骤:{req}")
            continue
        pos=i
    return errors

def validate_snapshot(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(data, dict): return ['快照必须是对象']
    for field in ("trade_date", "as_of", "market", "stocks"):
        if field not in data: errors.append(f"缺少顶层字段: {field}")
    bad=[]
    for path,k,v in _walk(data):
        if _forbidden_key(k): bad.append(path)
        if isinstance(v, float) and not math.isfinite(v): errors.append('非有限数值: '+path)
        if isinstance(v, str) and v.strip().lower() in {'nan','inf','-inf','+inf','infinity','-infinity'}:
            errors.append('非有限数值: '+path)
        if k in BOOL_FIELDS and v is not None and type(v) is not bool: errors.append('布尔字段类型错误: '+path)
    if bad: errors.append("检测到禁用字段（未来/盘中/集合竞价）: " + ", ".join(sorted(set(bad))[:20]))
    as_of=None
    if "as_of" in data:
        try: as_of=parse_dt(data["as_of"])
        except Exception as ex: errors.append(str(ex))
    trade_date=str(data.get("trade_date", ""))
    try: td=date.fromisoformat(trade_date)
    except (ValueError, TypeError): errors.append('trade_date 日期格式错误'); td=None
    local_asof=as_of.astimezone(timezone(timedelta(hours=8))) if as_of else None
    if local_asof and local_asof.hour < 15: errors.append('只接受中国交易日收盘后（15:00及以后）的as_of')
    if local_asof and trade_date and local_asof.date().isoformat()!=trade_date:
        errors.append("as_of 日期与 trade_date 不一致")
    if as_of and td:
        for path,k,v in _walk(data):
            if k in TIME_FIELDS and v:
                try:
                    if parse_dt(v)>as_of: errors.append(f"证据时间晚于 as_of: {path}={v}")
                except Exception as ex: errors.append(f"证据时间错误 {path}: {ex}")
            elif k in DATE_FIELDS and v and path != "trade_date":
                # 日常快照不允许把T+1/T+N日期藏在普通日期字段中。
                try:
                    dv=date.fromisoformat(str(v)[:10])
                    if dv>td: errors.append(f"日期字段晚于分析交易日: {path}={v}")
                except Exception as ex:
                    errors.append(f"日期字段错误 {path}: {ex}")
    if not isinstance(data.get('market'), dict): errors.append('market 必须为对象')
    cov=data.get('coverage')
    if cov is not None:
        if not isinstance(cov,dict): errors.append('coverage 必须为对象')
        else:
            for key in REQUIRED_COVERAGE_KEYS-{'history_model'}:
                if key in cov and type(cov[key]) is not bool: errors.append('coverage 布尔字段类型错误: '+key)
    if 'workflow_trace' in data and (not isinstance(data['workflow_trace'],list) or any(not isinstance(x,dict) for x in data['workflow_trace'])):
        errors.append('workflow_trace 必须为对象数组')
    stocks=data.get("stocks")
    if not isinstance(stocks,list): errors.append("stocks 必须为数组"); return errors
    seen=set()
    for i,s in enumerate(stocks):
        if not isinstance(s,dict): errors.append(f"stocks[{i}] 不是对象"); continue
        for field in ("code","name"):
            if not s.get(field): errors.append(f"stocks[{i}] 缺少 {field}")
        key=(s.get("code"),trade_date)
        if key in seen: errors.append(f"重复候选事件: {key[0]} {trade_date}")
        seen.add(key)
        if s.get("data_quality") == "insufficient": errors.append(f"{s.get('code','?')} 数据质量不足")
        missing=s.get('missing_score_features',[])
        if not isinstance(missing,list) or any(not isinstance(k,str) for k in missing): errors.append('missing_score_features必须为字段名数组')
        for key in SCORING_FEATURES-BOOL_FIELDS:
            if s.get(key) is not None and (isinstance(s[key],bool) or not isinstance(s[key],(int,float))):
                errors.append(f"{s.get('code')} 数值字段类型错误: {key}")
        for ev in s.get('post_close_events') or []:
            if not isinstance(ev,dict) or not ev.get('public_time'): errors.append('盘后事件必须带public_time')
    errors.extend(_validate_production_workflow(data))
    return errors

def market_state(m: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[str, List[str]]:
    c = cfg["market_gate"]
    up, down = _f(m.get("up_count")), _f(m.get("down_count"))
    flat = _f(m.get("flat_count"))
    lu, ld = _f(m.get("limit_up_count")), _f(m.get("limit_down_count"))
    total = max(up + down + flat, 1.0)
    up_ratio = up / total
    limit_ratio = lu / max(ld, 1.0)
    idx_vals = [_f(v) for v in (m.get("index_changes") or {}).values() if isinstance(v, (int, float))]
    idx_avg = sum(idx_vals) / len(idx_vals) if idx_vals else 0.0
    turnover_change = _f(m.get("turnover_change_pct"))
    broken = _f(m.get("broken_limit_up_count"), -1)
    seal_rate = lu / max(lu + broken, 1.0) if broken >= 0 else None
    prev_lu_ret = m.get("prev_limit_up_avg_return")

    reasons = [
        f"上涨家数比例 {up_ratio:.1%}", f"涨停/跌停比 {limit_ratio:.2f}",
        f"主要指数平均涨跌 {idx_avg:.2f}%", f"成交额变化 {turnover_change:.2f}%"
    ]
    if seal_rate is not None:
        reasons.append(f"封板率 {seal_rate:.1%}")
    if prev_lu_ret is not None:
        reasons.append(f"昨日涨停股今日平均表现 {_f(prev_lu_ret):.2f}%")

    if up_ratio >= c["attack_up_ratio"] and limit_ratio >= c["attack_limit_ratio"] and idx_avg >= 0:
        return "强进攻", reasons
    if up_ratio >= c["normal_up_ratio"] and limit_ratio >= c["normal_limit_ratio"] and idx_avg >= -0.5:
        return "正常轮动", reasons
    if up_ratio < c["extreme_up_ratio"] or (ld >= lu and idx_avg <= c["extreme_index_avg_pct"]):
        return "极端风险", reasons
    if up_ratio < c["retreat_up_ratio"]:
        # 宽度极差但涨停/跌停比仍明显偏多，视为强分歧而不是直接把逆势股奖励为“强”。
        if limit_ratio >= c["normal_limit_ratio"]:
            return "强分歧", reasons
        return "退潮", reasons
    if idx_avg <= c["retreat_index_avg_pct"] and turnover_change < 0:
        return "退潮", reasons
    return "强分歧", reasons


def _more_conservative_state(a: str, b: str) -> str:
    return a if STATE_SEVERITY.get(a,9) >= STATE_SEVERITY.get(b,9) else b


def _cap_more_conservative(a: str, b: str) -> str:
    return a if CONCLUSION_RANK.get(a,-9) <= CONCLUSION_RANK.get(b,-9) else b


def resolve_market_gate(m: Dict[str, Any], cfg: Dict[str, Any], coverage: Dict[str, Any] | None = None) -> Tuple[str, str, List[str], str]:
    """双轨市场总闸门：原始宽度/涨跌停口径 + 120日因果百分位口径，取更保守结果。

    这样既不退回V3/V4.1的简化市场判断，也不让旧技能中的手工加权市场综合分单独支配结果。
    """
    raw_state, reasons = market_state(m, cfg)
    state=raw_state
    method="原始宽度闸门"
    cap=MARKET_CAP[raw_state]
    cm=m.get("causal_market") or {}
    if cm and str(cm.get("data_quality"))=="normal":
        causal_state=CAUSAL_MARKET_MAP.get(str(cm.get("state")), "强分歧")
        state=_more_conservative_state(raw_state, causal_state)
        perm=str(cm.get("permission") or "暂停")
        cap=_cap_more_conservative(MARKET_CAP[state], PERMISSION_CAP.get(perm,"风险观察"))
        reasons=reasons+[
            f"因果市场状态 {cm.get('state')}→{causal_state}",
            f"市场权限 {perm}",
            f"120日宽度分位 {cm.get('breadth_pctile')}",
            f"120日情绪分位 {cm.get('sentiment_pctile')}",
            f"120日风险分位 {cm.get('risk_pctile')}",
        ]
        method="双轨保守融合"
    else:
        # 缺完整市场因果特征时，不允许静默按简化模型给出高等级候选。
        cap=_cap_more_conservative(cap,"重点观察")
        reference=m.get("historical_reference_policy") or {}
        if reference.get("mode")=="yearly-limit-close-premium" and reference.get("use")=="reference_only" and reference.get("affects_scoring_formula") is False:
            reasons.append("按用户要求：历史市场参考改为近一年涨停及次日收盘溢价；仅供参考，不改变原计分公式，保留原候选等级上限")
            method="原始宽度闸门；用户指定年度历史参考"
        else:
            reasons.append("完整120日因果市场特征缺失：按降级模式限制候选等级")
            method="降级：仅原始宽度闸门"
    cov=coverage or {}
    if not cov:
        cap=_cap_more_conservative(cap,"重点观察")
        reasons.append("工作流覆盖元数据缺失：视为手工/降级快照，候选等级限制为重点观察")
    if cov:
        if not cov.get("market_full_features",False) and not cov.get("historical_market_reference_replaced_by_user",False):
            cap=_cap_more_conservative(cap,"重点观察")
            reasons.append("完整市场因果层/指数日线覆盖不足：降级")
        if not cov.get("industry_pit",False):
            cap=_cap_more_conservative(cap,"重点观察")
            reasons.append("历史时点行业映射缺失：降级")
        if not cov.get("event_feed",False):
            cap=_cap_more_conservative(cap,"重点候选B")
            reasons.append("盘后事件数据源缺失：禁止升级为A/核心")
    return state, cap, reasons, method

def classify_stage(s: Dict[str, Any]) -> str:
    if s.get("new_unlimited"):
        return "特殊观察"
    streak = int(_f(s.get("board_streak")))
    if streak >= 3:
        return "3板及以上"
    if streak == 2:
        return "2板"
    if streak == 1:
        return "首板"
    r20 = _f((s.get("days_return") or {}).get("20"))
    if _f(s.get("change_pct")) > 3 and r20 > 12:
        return "趋势强势"
    return "普通"


def sector_state(s: Dict[str, Any], cfg: Dict[str, Any], metrics: Dict[str, Any] | None = None) -> Tuple[str, List[str]]:
    sm = metrics if metrics is not None else (s.get("sector_metrics") or {})
    c = cfg["sector"]
    day = _f(sm.get("day_change_pct"))
    up_ratio = _f(sm.get("up_ratio"))
    lu = int(_f(sm.get("limit_up_count")))
    two = int(_f(sm.get("two_plus_board_count")))
    r3, r5 = _f(sm.get("rel_strength_3d")), _f(sm.get("rel_strength_5d"))
    advanced = bool(sm.get("leader_advanced"))
    reasons = [f"板块当日 {day:.2f}%", f"上涨占比 {up_ratio:.1%}", f"板块涨停 {lu} 家", f"2板及以上 {two} 家", f"3日相对强度 {r3:.2f}", f"5日相对强度 {r5:.2f}"]

    if day > c["strong_day_change_pct"] and up_ratio >= c["strong_up_ratio"] and lu >= c["strong_limit_up_count"] and (r3 > 0 or r5 > 0 or two > 0 or advanced):
        return "强势持续", reasons
    if day < 0 and up_ratio < 0.30 and lu == 0:
        return "退潮", reasons
    if day < c["weak_day_change_pct"] and up_ratio < c["weak_up_ratio"] and r3 <= 0 and r5 <= 0:
        return "弱势", reasons
    return "中性/轮动", reasons


def resolve_context(s: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """行业层必跑；历史时点题材存在时，只有题材状态客观强于行业时才采用题材上下文。"""
    im=s.get("industry_metrics") or s.get("sector_metrics") or {}
    tm=s.get("theme_metrics") or {}
    ist,ir=sector_state(s,cfg,im)
    tst,tr=("未知",[]) if not tm or not s.get("theme_verified") else sector_state(s,cfg,tm)
    use_theme=False
    if tm and s.get("theme_verified"):
        if tst=="强势持续" and ist!="强势持续": use_theme=True
        elif SECTOR_RANK.get(tst,0)>SECTOR_RANK.get(ist,0): use_theme=True
    if use_theme:
        return {"state":tst,"reasons":["采用历史时点题材上下文"]+tr,"basis":"题材","name":s.get("theme") or s.get("theme_code"),
                "core_rank":int(_f(s.get("theme_core_rank"),99)),"leader":int(_f(s.get("theme_core_rank"),99))==1,
                "capacity_core":bool(s.get("theme_capacity_core"))}
    return {"state":ist,"reasons":["采用历史时点行业上下文"]+ir,"basis":"行业","name":s.get("sector"),
            "core_rank":int(_f(s.get("industry_core_rank",s.get("sector_core_rank")),99)),
            "leader":int(_f(s.get("industry_core_rank",s.get("sector_core_rank")),99))==1 or bool(s.get("sector_leader")),
            "capacity_core":bool(s.get("industry_capacity_core",s.get("capacity_core")))}


def derive_position(s: Dict[str, Any], sec_state: str, *, core_rank: int | None = None,
                    leader: bool | None = None, capacity_core: bool | None = None) -> str:
    # 禁止把人工 market_position 当作排序事实；核心地位必须由全市场同板块可复现排序派生。
    core_rank=int(_f(core_rank if core_rank is not None else s.get("sector_core_rank"),99))
    market_rank=int(_f(s.get("market_height_rank"),99))
    streak=int(_f(s.get("board_streak")))
    is_leader=bool(leader if leader is not None else s.get("sector_leader"))
    cap_core=bool(capacity_core if capacity_core is not None else s.get("capacity_core"))
    if is_leader and sec_state=="强势持续" and core_rank<=2:
        return "主线核心"
    if streak>=2 and core_rank==1:
        return "板块最高板"
    if core_rank<=2 and sec_state not in {"弱势","退潮"}:
        return "板块前排"
    if market_rank<=3 and streak>=2:
        return "独立强势"
    if cap_core and sec_state not in {"弱势","退潮"}:
        return "容量核心"
    if sec_state in {"弱势","退潮"} and _f(s.get("change_pct"))>=7:
        return "弱板块孤立强股"
    if core_rank<=5 and _f(s.get("change_pct"))>=5:
        return "板块前排"
    if _f(s.get("change_pct"))>=7:
        return "独立强势"
    return "未知"

def overheat(s: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[str, List[str]]:
    c = cfg["overheat"]
    d = s.get("days_return") or {}
    r5, r10, r20 = _f(d.get("5")), _f(d.get("10")), _f(d.get("20"))
    tr = _f(s.get("turnover_rate"))
    vr = _f(s.get("volume_ratio20"))
    ext20 = s.get("distance_to_prev20_high_pct")
    ext20 = _f(ext20) if ext20 is not None else None
    ext20_atr = s.get("distance_to_prev20_high_atr")
    ext20_atr = _f(ext20_atr) if ext20_atr is not None else None
    streak = int(_f(s.get("board_streak")))
    tags: List[str] = []
    severe = 0
    moderate = 0
    if r20 >= c["r20_extreme"]:
        severe += 2; tags.append(f"20日涨幅{r20:.1f}%>=极端阈值")
    elif r20 >= c["r20_high"]:
        moderate += 2; tags.append(f"20日涨幅{r20:.1f}%偏高")
    if r10 >= c["r10_high"]:
        moderate += 1; tags.append(f"10日涨幅{r10:.1f}%偏高")
    if r5 >= c["r5_high"]:
        moderate += 1; tags.append(f"5日涨幅{r5:.1f}%偏高")
    if tr >= c["turnover_extreme"]:
        severe += 1; tags.append(f"换手率{tr:.1f}%极高")
    elif tr >= c["turnover_high"]:
        moderate += 1; tags.append(f"换手率{tr:.1f}%偏高")
    if vr >= c.get("volume_ratio_extreme", 5.0):
        severe += 1; tags.append(f"成交额/过去20日中位数 {vr:.2f} 倍，极端放量")
    elif vr >= c.get("volume_ratio_high", 3.5):
        moderate += 1; tags.append(f"成交额/过去20日中位数 {vr:.2f} 倍，明显放量")
    if ext20 is not None:
        if ext20 >= c.get("prev20_extension_extreme_pct",15.0):
            severe += 1; tags.append(f"收盘高于此前20日高点 {ext20:.1f}%，扩张过快")
        elif ext20 >= c.get("prev20_extension_high_pct",8.0):
            moderate += 1; tags.append(f"收盘高于此前20日高点 {ext20:.1f}%，存在透支")
    # 用ATR再做一次波动率标准化，避免主板10%与20%涨跌幅板块只靠绝对涨幅阈值硬比较。
    if ext20_atr is not None:
        if ext20_atr >= c.get("atr_extension_extreme",3.5):
            severe += 1; tags.append(f"突破前20日高点后扩张 {ext20_atr:.2f}ATR，波动率标准化后极端")
        elif ext20_atr >= c.get("atr_extension_high",2.0):
            moderate += 1; tags.append(f"突破前20日高点后扩张 {ext20_atr:.2f}ATR，存在标准化透支")
    if streak >= c["streak_extreme"]:
        severe += 1; tags.append(f"连板高度{streak}偏极端")
    elif streak >= c["streak_high"]:
        moderate += 1; tags.append(f"连板高度{streak}较高")
    close_loc = s.get("close_location")
    if close_loc is not None and _f(close_loc) < 0.35 and _f(s.get("change_pct")) > 3:
        moderate += 1; tags.append("收盘位置偏低，存在冲高回落")
    if s.get("broken_limit_weak_close"):
        moderate += 2; tags.append("炸板后弱收")
    if severe >= 2 or severe + moderate >= 5:
        return "末端透支", tags
    if severe >= 1 or moderate >= 3:
        return "高位拥挤", tags
    if moderate >= 1:
        return "正常加速", tags
    return "低位/未见明显透支", tags


def lhb_evidence(s: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[str, Dict[str, float], List[str]]:
    l = s.get("lhb") or {}
    if not l.get("listed"):
        if l.get('absence_verified_in_complete_saved_billboard') is True:
            return "无龙虎榜", {}, ["完整当日榜单已核验，确实未上榜；当前资金、席位和生命周期不适用，按原规则中性"]
        return "无龙虎榜", {}, ["未提供龙虎榜明细"]
    c = cfg["lhb"]
    turnover = _f(s.get("turnover"))
    impact_denominator = _f(l.get("impact_denominator"), turnover)
    if impact_denominator <= 0:
        impact_denominator = turnover
    buy5, sell5 = _f(l.get("buy5")), _f(l.get("sell5"))
    net = _f(l.get("net_buy"), buy5 - sell5)
    buy1 = _f(l.get("buy1"))
    inst = _f(l.get("institution_net"))
    connect = _f(l.get("connect_net"))
    broker = _f(l.get("broker_net"))
    net_ratio = net / impact_denominator if impact_denominator > 0 else 0.0
    buy_sell = buy5 / sell5 if sell5 > 0 else (999.0 if buy5 > 0 else 0.0)
    concentration = buy1 / buy5 if buy5 > 0 else 0.0
    inst_ratio = inst / impact_denominator if impact_denominator > 0 else 0.0
    broker_ratio = broker / impact_denominator if impact_denominator > 0 else 0.0
    free_float = _f(s.get("free_float_mcap"))
    net_ff = net / free_float if free_float > 0 else float("nan")
    trigger=str(l.get("trigger_reason") or "").strip()
    all_reasons=str(l.get("all_reasons") or trigger).strip()
    window_type=str(l.get("window_type") or "daily")
    reasons = [
        f"主披露窗口 {window_type}",
        f"上榜原因 {trigger or '未提供'}",
        f"龙虎榜净买/匹配披露窗口成交额 {net_ratio:.2%}", f"前五买/卖比 {buy_sell:.2f}",
        f"买一集中度 {concentration:.1%}", f"机构专用净额 {inst:.0f}",
        f"股通专用净额 {connect:.0f}", f"普通营业部净额 {broker:.0f}"
    ]
    disclosed=s.get('capital_observation_protocol')=='DISCLOSED_RANKED_SIDE_CONTRIBUTIONS_V1'
    if disclosed:
        sides=l.get('disclosed_sides') or {}
        reasons=reasons[:5]+[
            '本次机构/营业部分项按公开买榜与卖榜贡献评分；差额不代表席位实际净买，未披露对侧未填零']
        for category,label in [('institution','机构'),('connect','股通'),('broker','营业部')]:
            reasons.append(f"{label}买榜贡献 {_f(sides.get(category+'_disclosed_buy')):.0f}，卖榜贡献 {_f(sides.get(category+'_disclosed_sell')):.0f}")
    dnr=l.get("daily_net_buy_ratio"); tnr=l.get("three_day_net_buy_ratio")
    if dnr is not None: reasons.append(f"单日窗口净买强度 {_f(dnr):.2%}")
    if tnr is not None: reasons.append(f"三日累计窗口净买强度 {_f(tnr):.2%}")
    if all_reasons and all_reasons!=trigger: reasons.append(f"全部上榜原因 {all_reasons}")
    if math.isfinite(net_ff):
        reasons.append(f"龙虎榜净买/自由流通市值 {net_ff:.2%}")
    trend = str(l.get("flow_trend") or "").strip()
    lifecycle_no=int(_f(l.get("lifecycle_event_no"),1))
    lifecycle_improving=bool(l.get("lifecycle_net_improving"))
    seat_q=l.get("seat_quality_pctile"); seat_n=int(_f(l.get("seat_quality_samples"),0))
    if trend: reasons.append(f"连续上榜资金趋势 {trend}")
    if lifecycle_no>1: reasons.append(f"3交易日生命周期内第{lifecycle_no}次上榜，净买改善={lifecycle_improving}")
    if seat_q is not None and seat_n>=20: reasons.append(f"成熟席位质量百分位 {_f(seat_q):.1%}，最小成熟样本 {seat_n}")

    if net_ratio <= c["negative_net_ratio"] or (not disclosed and inst_ratio <= c["extreme_institution_sell_ratio"]) or trend in {"兑现", "反手"}:
        role = "负面"
    elif concentration >= c["concentration_risk"] and net > 0:
        role = "集中风险"
    elif net_ratio >= c["confirm_net_ratio"] and buy_sell >= c["confirm_buy_sell_ratio"]:
        role = "确认"
    elif net > 0:
        role = "弱确认"
    else:
        role = "中性"
    return role, {
        "net_buy_ratio": net_ratio,
        "buy_sell_ratio": buy_sell,
        "buy1_concentration": concentration,
        "institution_net_ratio": None if disclosed else inst_ratio,
        "broker_net_ratio": None if disclosed else broker_ratio,
        "net_buy_free_float_ratio": net_ff if math.isfinite(net_ff) else None,
        "net_impact_pctile": _f(s.get("lhb_net_impact_pctile"), 0.5),
        "participation_pctile": _f(s.get("lhb_participation_pctile"), 0.5),
        "institution_impact_pctile": _f(s.get("institution_disclosed_impact_pctile" if disclosed else "inst_net_impact_pctile"), 0.5),
        "broker_impact_pctile": _f(s.get("broker_disclosed_impact_pctile" if disclosed else "broker_net_impact_pctile"), 0.5),
        "buy_sell_balance": _f(s.get("disclosed_buy_sell_balance" if disclosed else "buy_sell_balance"), 0.0),
        "capital_observation_protocol": 'DISCLOSED_RANKED_SIDE_CONTRIBUTIONS_V1' if disclosed else 'ACTUAL_DISCLOSED_SEAT_NET',
        "disclosed_side_contributions": l.get('disclosed_sides') if disclosed else None,
        "net_free_float_pctile": _f(s.get("lhb_net_free_float_pctile"), 0.5),
        "lifecycle_event_no": lifecycle_no,
        "lifecycle_net_improving": 1.0 if lifecycle_improving else 0.0,
        "seat_quality_pctile": _f(seat_q) if seat_q is not None else None,
        "seat_quality_samples": seat_n,
        "seat_quality_pctile_effective": (_f(seat_q) if seat_q is not None and seat_n>=20 else None),
        "daily_net_buy_ratio": (_f(dnr) if dnr is not None else None),
        "three_day_net_buy_ratio": (_f(tnr) if tnr is not None else None),
    }, reasons


def hard_vetoes(s: Dict[str, Any], position: str, sec_state: str, oh: str, lhb_role: str) -> List[str]:
    v: List[str] = []
    board = str(s.get("board") or s.get("exchange") or "")
    if "北交" in board or board.upper() in {"BSE", "BJ"} or str(s.get("code", "")).endswith(".BJ"):
        v.append("默认排除北交所")
    if s.get("risk_warning") or s.get("is_st"):
        v.append("风险警示/ST")
    if s.get("delisting_risk") or s.get("is_delisting_arrangement"):
        v.append("退市/重大退市风险")
    if _f(s.get("change_pct")) <= 0:
        v.append("非短线强势上涨样本")
    if s.get("data_conflicts"):
        v.append("关键数据存在未解决冲突")
    if s.get("data_quality") == "insufficient":
        v.append("关键数据质量不足")
    if s.get("severe_negative_event"):
        v.append("盘后重大负面事件")
    if sec_state == "退潮" and int(_f(s.get("board_streak"))) <= 1:
        v.append("板块退潮且自身仅低阶段强势")
    if oh == "末端透支" and lhb_role == "负面":
        v.append("末端透支叠加龙虎榜负面")
    if oh in {"高位拥挤", "末端透支"} and _f((s.get("lhb") or {}).get("institution_net")) < 0 and lhb_role == "负面":
        v.append("高位机构明显兑现")
    for e in s.get("post_close_events") or []:
        if isinstance(e, dict) and str(e.get("risk_level") or "").lower() in {"hard", "重大", "severe"}:
            v.append("盘后重大风险事件: " + str(e.get("title") or e.get("type") or "未命名"))
        if isinstance(e, dict) and e.get("concept_denial") is True:
            v.append("盘后重要概念澄清/证伪")
    return list(dict.fromkeys(v))


def _apply_cap(base: str, cap: str) -> str:
    return cap if CONCLUSION_RANK.get(base, -9) > CONCLUSION_RANK.get(cap, -9) else base

def _downgrade(base: str, steps: int = 1) -> str:
    ordered = ["剔除","特殊观察池","风险观察","次级观察","重点观察","重点候选B","重点候选A","核心候选"]
    try:
        i = ordered.index(base)
    except ValueError:
        return base
    return ordered[max(0, i-max(0, int(steps)))]

def event_risk_evidence(s: Dict[str, Any]) -> Tuple[int, List[str]]:
    """盘后事件先抽取风险与已核验催化事实；风险独立扣分，已核验催化仅进入小权重事件分。"""
    level = 0
    reasons: List[str] = []
    for e in s.get("post_close_events") or []:
        if not isinstance(e, dict):
            continue
        title = str(e.get("title") or e.get("type") or "盘后事件")
        risk = _f(e.get("risk_penalty"))
        rl = str(e.get("risk_level") or "").lower()
        if e.get("concept_denial") is True or rl in {"hard","重大","severe"}:
            level = max(level, 3); reasons.append(f"重大风险/证伪: {title}")
        elif rl in {"high","高"} or risk >= 0.75:
            level = max(level, 2); reasons.append(f"高风险盘后事件: {title}")
        elif rl in {"medium","中"} or risk >= 0.50:
            level = max(level, 1); reasons.append(f"中等风险盘后事件: {title}")
        elif risk > 0:
            reasons.append(f"低风险盘后事件: {title}")
        elif e.get("independent_catalyst") is True:
            reasons.append(f"已核验独立催化（仅进入小权重事件驱动分）: {title}")
    return level, reasons


def model_bucket(market: str, stage: str, position: str, sec_state: str, oh: str, lhb_role: str) -> str:
    pos_group = "核心前排" if POSITION_RANK.get(position, 0) >= 5 else "独立/后排"
    oh_group = "低中位" if OVERHEAT_RISK.get(oh, 9) <= 1 else "高位"
    lhb_group = "正向" if LHB_RANK.get(lhb_role, -9) >= 1 else "非正向"
    return "|".join([market, stage, pos_group, sec_state, oh_group, lhb_group])


def validate_history_model(model: Dict[str, Any] | None, trade_date: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    if not model:
        return {"status": "未启用", "message": "历史模型未启用；历史验证分项保持中性，不输出胜率。", "production_qualified": False}
    errors: List[str] = []
    cutoff = model.get("model_cutoff")
    if not cutoff:
        errors.append("缺少 model_cutoff")
    else:
        try:
            if date.fromisoformat(str(cutoff)) >= date.fromisoformat(trade_date):
                errors.append("model_cutoff 必须早于分析交易日")
        except Exception:
            errors.append("model_cutoff 日期格式错误")
    scheme = str(model.get("validation_scheme") or "")
    allowed = set(cfg["history"]["allowed_validation_schemes"])
    if scheme not in allowed:
        errors.append("历史模型缺少合格的时间序列样本外验证方案")
    if not isinstance(model.get("buckets"), dict):
        errors.append("历史模型缺少 buckets")
    from .research import REQUIRED_ACCEPTANCE_CHECKS
    acceptance = model.get("acceptance")
    if not isinstance(acceptance, dict):
        errors.append("缺少合法验收记录"); acceptance={}
    checks=acceptance.get("checks")
    if not isinstance(checks,dict) or set(checks)!=REQUIRED_ACCEPTANCE_CHECKS or any(type(v) is not bool for v in checks.values()):
        errors.append("验收明细字段或布尔类型错误")
    else:
        if type(acceptance.get('passed')) is not bool or acceptance['passed'] != all(checks.values()):
            errors.append("acceptance.passed 与明细检查不一致")
    # 本入口没有原始行情/冻结规则/逐折运行证据，不能通过JSON自报升级为生产模型。
    if model.get('production_qualified') is not False or model.get('rule_replay_verified') is not False:
        errors.append("本版未实现独立规则重放验收，禁止自报生产资格")
    if model.get('evidence_scope') != 'research_only':
        errors.append("历史CSV只能标记为research_only")
    provenance=model.get('provenance_hash')
    if not isinstance(provenance,str) or not re.fullmatch(r'[0-9a-f]{64}',provenance):
        errors.append("历史来源摘要格式无效")
    for path,key,value in _walk(model):
        if isinstance(value,float) and not math.isfinite(value): errors.append('历史非有限数值:'+path)
    if errors:
        return {"status":"拒绝","message":"; ".join(errors),"production_qualified":False}
    return {
        "status":"研究参考",
        "message":"按年份分期的标签描述统计；尚无独立规则重放证据。历史分项保持中性，不作为样本外胜率或核心候选升级依据。",
        "model_cutoff":cutoff, "validation_scheme":scheme,
        "production_qualified":False, "evidence_scope":"research_only",
        "acceptance":acceptance, "provenance_hash":provenance,
    }


def _history_strength(stat: Dict[str, Any], n: int, cfg: Dict[str, Any]) -> Tuple[str, float, List[str]]:
    """评价当前历史桶本身是否真正有效，而不是把“样本多”误当成“表现好”。"""
    h = cfg["history"]
    t5 = stat.get("t5_ge5_rate")
    t5_lb = stat.get("t5_ge5_wilson_lower90")
    avg = stat.get("avg_return_t5")
    avg_lb = stat.get("avg_return_t5_bootstrap_lower90")
    excess = stat.get("benchmark_excess_t5")
    excess_lb = stat.get("benchmark_excess_t5_bootstrap_lower90")
    mae = stat.get("avg_mae_5d")
    reasons: List[str] = []
    medium = n >= int(h["medium_sample"])

    strong = (
        medium and t5_lb is not None and _f(t5_lb, -9) >= _f(h.get("strong_min_t5_burst_lower90"), .30)
        and avg_lb is not None and _f(avg_lb, -9) > 0
        and excess_lb is not None and _f(excess_lb, -9) > 0
        and (mae is None or _f(mae) >= _f(h.get("max_acceptable_avg_mae_5d"), -.10))
    )
    if strong:
        reasons.append("当前桶的5日爆发率下界、5日收益下界和相对基准超额下界均为正")
        return "强正向", .95, reasons

    neg_flags = []
    if avg is not None and _f(avg) < 0: neg_flags.append("5日平均收益为负")
    if excess is not None and _f(excess) < 0: neg_flags.append("5日相对基准超额为负")
    if t5 is not None and _f(t5) < _f(h.get("negative_max_t5_burst_rate"), .25): neg_flags.append("5日达到5%爆发率过低")
    if mae is not None and _f(mae) < _f(h.get("max_acceptable_avg_mae_5d"), -.10): neg_flags.append("平均5日最大回撤过大")
    if medium and len(neg_flags) >= 2:
        return "强负向", .08, neg_flags
    if medium and len(neg_flags) == 1:
        return "负向", .25, neg_flags

    positive = (
        t5 is not None and _f(t5) >= _f(h.get("positive_min_t5_burst_rate"), .40)
        and avg is not None and _f(avg) > 0
        and (excess is None or _f(excess) >= 0)
    )
    if positive:
        reasons.append("当前桶点估计为正，但统计下界尚未达到强正向标准")
        return "正向", .72, reasons
    return "中性", .50, ["当前桶未达到可确认正向或负向标准"]


def history_for_bucket(model: Dict[str, Any] | None, bucket: str, cfg: Dict[str, Any], model_status: Dict[str, Any]) -> Dict[str, Any]:
    if not model or model_status.get("status") != "可用":
        return {"available": False, "strength": "不可用", "history_score": .50}
    stat = (model.get("buckets") or {}).get(bucket)
    if not isinstance(stat, dict):
        return {"available": False, "strength": "无匹配桶", "history_score": .50}
    n = int(_f(stat.get("sample_n")))
    if n < cfg["history"]["min_sample"]:
        return {"available": False, "sample_n": n, "reason": "相似样本不足50，不输出概率", "strength":"样本不足", "history_score":.50}
    conf = "高" if n >= cfg["history"]["high_sample"] else "中" if n >= cfg["history"]["medium_sample"] else "低"
    strength, hscore, reasons = _history_strength(stat, n, cfg)
    out = {"available": True, "sample_n": n, "confidence": conf, "strength": strength,
           "history_score": hscore, "strength_reasons": reasons}
    for key in (
        "t1_positive_rate", "t3_positive_rate", "t5_ge5_rate", "t5_ge5_wilson_lower90",
        "avg_mae_5d", "avg_return_t5", "avg_return_t5_bootstrap_lower90",
        "benchmark_excess_t5", "benchmark_excess_t5_bootstrap_lower90"
    ):
        if key in stat and stat[key] is not None:
            out[key] = stat[key]
    return out


def _clip01(v: Any, default: float = .5) -> float:
    x = _f(v, default)
    return max(0.0, min(1.0, x))


def _weighted(values: Dict[str, float], weights: Dict[str, Any]) -> float:
    total = sum(max(0.0, _f(weights.get(k))) for k in values)
    if total <= 0:
        return 50.0
    return 100.0 * sum(_clip01(values[k]) * max(0.0, _f(weights.get(k))) for k in values) / total


def stage_market_fit(stage: str, market: str) -> float:
    """阶段不是绝对等级，而是市场状态条件变量。"""
    matrix = {
        "强进攻": {"首板":.76, "2板":.94, "3板及以上":1.00, "趋势强势":.90, "普通":.25, "特殊观察":.10},
        "正常轮动": {"首板":.82, "2板":1.00, "3板及以上":.78, "趋势强势":.92, "普通":.25, "特殊观察":.10},
        "强分歧": {"首板":.78, "2板":.76, "3板及以上":.55, "趋势强势":.90, "普通":.20, "特殊观察":.10},
        "退潮": {"首板":.50, "2板":.38, "3板及以上":.22, "趋势强势":.72, "普通":.12, "特殊观察":.05},
        "极端风险": {"首板":.20, "2板":.15, "3板及以上":.10, "趋势强势":.25, "普通":.05, "特殊观察":.02},
    }
    return matrix.get(market, matrix["强分歧"]).get(stage, .20)


def _position_score(position: str) -> float:
    return {
        "主线核心":1.00, "板块最高板":.96, "板块前排":.84, "容量核心":.80,
        "独立强势":.70, "弱板块孤立强股":.46, "后排跟风":.22, "板块退潮":.05, "未知":.30,
    }.get(position, .30)


def _sector_score(sec_state: str) -> float:
    return {"强势持续":1.00, "中性/轮动":.62, "弱势":.28, "退潮":.08, "未知":.35}.get(sec_state, .35)


def _free_mcap_fit(p: float) -> float:
    p=_clip01(p)
    # 小中盘更具资金推动弹性，但最小盘不直接给满分，避免把微盘风险当成爆发力。
    if p <= .30:
        return .58 + .42*(p/.30)
    return max(.20, 1.0 - .80*((p-.30)/.70))


def _turnover_fit(p: float) -> float:
    p=_clip01(p)
    if p <= .75:
        return .35 + .65*(p/.75)
    return max(.70, 1.0 - .30*((p-.75)/.25))


def short_burst_score(s: Dict[str, Any], stage: str, position: str, sec_state: str, market: str,
                      oh: str, lhb_role: str, lhb_metrics: Dict[str, Any], event_level: int,
                      hist: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    sc = cfg["scoring"]
    ma_bundle = sum(.5 if s.get(k) is None else float(s[k]) for k in ('close_above_ma20','ma5_gt_ma10_gt_ma20','ma20_gt_ma60')) / 3.0
    technical_vals = {
        "rs20": _clip01(s.get("rs_20d_pctile")),
        "ma20_slope": _clip01(s.get("ma20_slope_pctile")),
        "breakout20": _clip01(s.get("breakout_20d_strength"), .5),
        "close_location": _clip01(s.get("close_location")),
        "volume_health": _clip01(s.get("volume_health")),
        "startup_location": _clip01(s.get("startup_location_health")),
        "ma_structure": ma_bundle,
    }
    structure_vals = {
        "position": _position_score(position),
        "stage_market_fit": stage_market_fit(stage, market),
        "sector_state": _sector_score(sec_state),
        "sector_rs": _clip01(s.get("sector_rs_5d_pctile")),
        "sector_activity": _clip01(s.get("sector_activity_pctile")),
    }
    net_ratio = _f(lhb_metrics.get("net_buy_ratio"))
    net_ratio_score = _clip01(.5 + max(-.06, min(.06, net_ratio))/.12)
    seat_n = int(_f(lhb_metrics.get("seat_quality_samples")))
    seat_q = lhb_metrics.get("seat_quality_pctile_effective")
    if seat_q is None or not math.isfinite(_f(seat_q, float("nan"))):
        seat_score=.50
    else:
        shrink=seat_n/(seat_n+40.0)
        seat_score=.50+(_clip01(seat_q)-.50)*shrink
    lifecycle_no=int(_f(lhb_metrics.get("lifecycle_event_no"),1))
    lifecycle_improving=bool(_f(lhb_metrics.get("lifecycle_net_improving")))
    lifecycle_score=.70 if lifecycle_no>1 and lifecycle_improving else (.42 if lifecycle_no>1 else .50)
    capital_vals = {
        "net_impact": _clip01(lhb_metrics.get("net_impact_pctile")),
        "participation": _clip01(lhb_metrics.get("participation_pctile")),
        "institution": _clip01(lhb_metrics.get("institution_impact_pctile")),
        "broker": _clip01(lhb_metrics.get("broker_impact_pctile")),
        "buy_sell_balance": _clip01((_f(lhb_metrics.get("buy_sell_balance"))+1.0)/2.0),
        "net_ratio": net_ratio_score,
        "seat_quality": seat_score,
        "lifecycle": lifecycle_score,
    }
    elasticity_vals = {
        "free_mcap_fit": _free_mcap_fit(s.get("free_mcap_pctile", .5)),
        "turnover_fit": _turnover_fit(s.get("turnover_rate_pctile", .5)),
        "net_to_free_mcap": _clip01(lhb_metrics.get("net_free_float_pctile", s.get("lhb_net_free_float_pctile", .5))),
    }
    catalyst=.50
    if bool(s.get("independent_catalyst")) and bool(s.get("catalyst_public_before_cutoff")):
        q=_clip01(s.get("catalyst_quality"), .5)
        catalyst=.55+.45*q
    history_score=_clip01(hist.get("history_score"), .50)
    components = {
        "技术动量": _weighted(technical_vals, sc["technical_weights"]),
        "结构地位": _weighted(structure_vals, sc["structure_weights"]),
        "资金质量": _weighted(capital_vals, sc["capital_weights"]),
        "资金弹性": _weighted(elasticity_vals, sc["elasticity_weights"]),
        "事件驱动": 100.0*catalyst,
        "历史验证": 100.0*history_score,
    }
    cw=sc["component_weights"]
    mapping={"技术动量":"technical","结构地位":"structure","资金质量":"capital","资金弹性":"elasticity","事件驱动":"catalyst","历史验证":"history"}
    denom=sum(max(0.0,_f(cw.get(mapping[k]))) for k in components)
    base=sum(components[k]*max(0.0,_f(cw.get(mapping[k]))) for k in components)/denom if denom>0 else 50.0

    rp=sc["risk_penalty"]
    penalties: Dict[str,float]={}
    oh_pen={
        "正常加速":_f(rp.get("normal_acceleration"),2),
        "高位拥挤":_f(rp.get("crowded"),9),
        "末端透支":_f(rp.get("terminal"),18),
    }.get(oh,0.0)
    if oh_pen: penalties["价格透支"]=oh_pen
    event_discrete = 0.0
    if event_level>=3:event_discrete=_f(rp.get("event_severe"),35)
    elif event_level==2:event_discrete=_f(rp.get("event_high"),18)
    elif event_level==1:event_discrete=_f(rp.get("event_medium"),8)
    continuous=_clip01(s.get("risk_penalty"),0.0)*_f(rp.get("continuous_event_risk_max"),12)
    event_pen=max(event_discrete,continuous)
    if event_pen: penalties["盘后事件风险"]=event_pen
    if lhb_role=="负面": penalties["龙虎榜负面"]=_f(rp.get("lhb_negative"),8)
    if lhb_role=="集中风险": penalties["买一集中风险"]=_f(rp.get("lhb_concentration"),4)
    if bool(s.get("market_climax")): penalties["市场/板块高潮"]=_f(rp.get("market_climax"),5)
    if bool(s.get("downward_anomaly_without_reversal")): penalties["下跌异常未反转"]=_f(rp.get("downward_anomaly"),8)
    if bool(s.get("three_day_surge_high_climax")): penalties["三日急涨高潮"]=_f(rp.get("surge_climax"),6)
    if bool(s.get("extreme_volume_inst_sell_weak_relay")): penalties["极量机构兑现弱承接"]=_f(rp.get("weak_relay"),8)
    risk_total=sum(penalties.values())
    final=max(0.0,min(100.0,base-risk_total))
    weighted_contrib={k:components[k]*_f(cw.get(mapping[k])) for k in components}
    top_positive=[k for k,_ in sorted(weighted_contrib.items(),key=lambda kv:kv[1],reverse=True)[:3]]
    weak=[k for k,v in components.items() if v<45]
    return {
        "base_score":round(base,2), "risk_penalty":round(risk_total,2), "final_score":round(final,2),
        "components":{k:round(v,2) for k,v in components.items()},
        "risk_details":{k:round(v,2) for k,v in penalties.items()},
        "top_positive_components":top_positive, "weak_components":weak,
        "factor_details":{
            "technical":{k:round(v,4) for k,v in technical_vals.items()},
            "structure":{k:round(v,4) for k,v in structure_vals.items()},
            "capital":{k:round(v,4) for k,v in capital_vals.items()},
            "elasticity":{k:round(v,4) for k,v in elasticity_vals.items()},
        },
        "meaning":"0-100短线爆发力相对评分；不是未经校准的上涨概率",
    }


def evidence_conclusion(score: float, hard: List[str], market: str, candidate_cap: str, new_unlimited: bool,
                        recent_ipo_immature: bool, history: Dict[str, Any], model_status: Dict[str, Any],
                        cfg: Dict[str, Any]) -> Tuple[str, str]:
    if hard:
        return "剔除", "D"
    if new_unlimited:
        return "特殊观察池", "C"
    if market == "极端风险":
        return "风险观察", "C"
    th=cfg["scoring"]["conclusion_thresholds"]
    if score >= _f(th["candidate_a"]):
        base,grade="重点候选A","A"
    elif score >= _f(th["candidate_b"]):
        base,grade="重点候选B","B+"
    elif score >= _f(th["watch"]):
        base,grade="重点观察","B"
    elif score >= _f(th["secondary"]):
        base,grade="次级观察","B-"
    else:
        base,grade="风险观察","C"

    # 核心候选必须同时满足高分 + 整体生产模型通过 + 当前桶本身“强正向”。
    if score >= _f(th["core"]) and base=="重点候选A" and market in {"强进攻","正常轮动"}        and model_status.get("production_qualified") and history.get("available") and history.get("strength")=="强正向":
        base,grade="核心候选","A+"

    # 历史表现差不能因为样本多而升级；相反必须对候选上限形成约束。
    if history.get("available") and history.get("confidence") in {"中","高"}:
        if history.get("strength")=="强负向":
            base=_apply_cap(base,"重点观察")
        elif history.get("strength")=="负向":
            base=_apply_cap(base,"重点候选B")
    base=_apply_cap(base,candidate_cap)
    grade={'核心候选':'A+','重点候选A':'A','重点候选B':'B+','重点观察':'B','次级观察':'B-','风险观察':'C','特殊观察池':'C','剔除':'D'}[base]
    if recent_ipo_immature:
        base=_apply_cap(base,"重点观察")
        if grade in {"A+","A","B+"}: grade="C+"
    return base,grade


def analyze_stock(s: Dict[str, Any], market: str, candidate_cap: str, cfg: Dict[str, Any],
                  model: Dict[str, Any] | None, model_status: Dict[str, Any]) -> Dict[str, Any]:
    required_scoring=set(SCORING_FEATURES)
    if s.get('capital_observation_protocol')=='DISCLOSED_RANKED_SIDE_CONTRIBUTIONS_V1':
        required_scoring-=set(['inst_net_impact_pctile','broker_net_impact_pctile','buy_sell_balance'])
        required_scoring.update(['institution_disclosed_impact_pctile','broker_disclosed_impact_pctile','disclosed_buy_sell_balance'])
    missing_features=sorted({k for k in required_scoring if s.get(k) is None}|set(s.get('missing_score_features') or []))
    if missing_features: candidate_cap=_cap_more_conservative(candidate_cap,'重点观察')
    s=dict(s)
    for k in missing_features:
        if k in SCORING_FEATURES: s[k]=None
    stage = classify_stage(s)
    ctx = resolve_context(s, cfg)
    sec_state, sec_reasons = ctx["state"], ctx["reasons"]
    position = derive_position(s, sec_state, core_rank=ctx.get("core_rank"), leader=ctx.get("leader"), capacity_core=ctx.get("capacity_core"))
    oh, oh_reasons = overheat(s, cfg)
    lhb_role, lhb_metrics, lhb_reasons = lhb_evidence(s, cfg)
    event_level, event_reasons = event_risk_evidence(s)
    hard = hard_vetoes(s, position, sec_state, oh, lhb_role)
    bucket = model_bucket(market, stage, position, sec_state, oh, lhb_role)
    hist = history_for_bucket(model, bucket, cfg, model_status)
    score = short_burst_score(s, stage, position, sec_state, market, oh, lhb_role, lhb_metrics, event_level, hist, cfg)
    conclusion, grade = evidence_conclusion(
        score["final_score"], hard, market, candidate_cap, bool(s.get("new_unlimited")),
        bool(s.get("recent_ipo_immature")), hist, model_status, cfg
    )

    positive: List[str] = []
    negative: List[str] = []
    if missing_features:
        verified_absence=(s.get('lhb') or {}).get('absence_verified_in_complete_saved_billboard') is True and not (s.get('lhb') or {}).get('listed')
        not_applicable={'broker_net_impact_pctile','buy_sell_balance','inst_net_impact_pctile','lhb_net_free_float_pctile','lhb_net_impact_pctile','lhb_participation_pctile'} if verified_absence else set()
        unavailable=[k for k in missing_features if k not in not_applicable]
        if set(missing_features)&not_applicable:negative.append('完整榜单核验为未上榜：龙虎榜资金分项不适用，按原规则中性；不表示实际净买为零')
        if unavailable:negative.append('评分特征缺失，使用中性占位且降级：'+','.join(unavailable))
    if score["components"]["技术动量"] >= 70: positive.append(f"技术动量强 {score['components']['技术动量']:.1f}")
    if score["components"]["结构地位"] >= 70: positive.append(f"结构地位强 {score['components']['结构地位']:.1f}")
    if score["components"]["资金质量"] >= 70: positive.append(f"资金质量强 {score['components']['资金质量']:.1f}")
    if score["components"]["资金弹性"] >= 70: positive.append(f"资金推动弹性较好 {score['components']['资金弹性']:.1f}")
    if score["components"]["事件驱动"] >= 70: positive.append("存在截止时点前已核验独立催化")
    if hist.get("strength") in {"正向","强正向"}: positive.append(f"历史样本外证据: {hist.get('strength')}")
    if POSITION_RANK.get(position,0)>=5: positive.append(f"市场/板块地位: {position}")
    if sec_state=="强势持续": positive.append(f"{ctx.get('basis','行业')}存在持续性证据")
    if LHB_RANK.get(lhb_role,-9)>=1: positive.append(f"龙虎榜资金证据: {lhb_role}")

    for name,val in score["components"].items():
        if val<40: negative.append(f"{name}偏弱 {val:.1f}")
    for name,val in score["risk_details"].items(): negative.append(f"{name}扣分 {val:.1f}")
    if hist.get("strength") in {"负向","强负向"}: negative.append("历史样本外证据: "+str(hist.get("strength")))
    if s.get("recent_ipo_immature"): negative.append("上市第6-19个交易日：筹码尚未充分成熟，限制候选等级")
    negative.extend(hard)

    sort_tuple=(-CONCLUSION_RANK.get(conclusion,-9), -score["final_score"], str(s.get("code") or ""))
    return {
        "code": s.get("code"), "name": s.get("name"), "stage": stage,
        "sector": s.get("sector"), "context_basis": ctx.get("basis"), "context_name": ctx.get("name"),
        "sector_state": sec_state, "position": position,
        "lhb_role": lhb_role, "overheat": oh, "event_risk_level": event_level, "model_bucket": bucket,
        "short_burst_score": score["final_score"], "score_before_risk": score["base_score"],
        "score_risk_penalty": score["risk_penalty"], "score_components": score["components"],
        "score_risk_details": score["risk_details"], "score_meaning": score["meaning"],
        "evidence_grade": grade, "conclusion": conclusion,
        "positive_evidence": positive, "negative_evidence": negative,
        "hard_reject_reasons": hard, "history_stats": hist,
        "audit": {
            "context_reasons": sec_reasons, "overheat_reasons": oh_reasons, "lhb_reasons": lhb_reasons,
            "event_reasons": event_reasons, "lhb_metrics": lhb_metrics,
            "context": ctx, "score_factor_details": score["factor_details"],
            "score_top_positive_components": score["top_positive_components"], "score_weak_components": score["weak_components"],
            "raw_stock_feature_provenance": s.get("feature_provenance") or {},
        },
        "_sort_tuple": sort_tuple,
    }

def analyze_snapshot(data: Dict[str, Any], config: Dict[str, Any] | None = None, history_model: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = load_config() if config is None else config
    validate_config(cfg)
    errors = validate_snapshot(data)
    if errors:
        raise ValueError("; ".join(errors))
    coverage = data.get("coverage") or {}
    state, candidate_cap, reasons, gate_method = resolve_market_gate(data["market"], cfg, coverage)
    pipeline=str(data.get("pipeline") or "manual/degraded")
    if pipeline != "raw-postmarket-v5.0-audited":
        candidate_cap=_cap_more_conservative(candidate_cap,"重点观察")
        reasons.append("输入不是V5.0已审计生产快照：禁止冒充完整管线，候选等级降至重点观察上限")
    model_status = validate_history_model(history_model, str(data["trade_date"]), cfg)
    rows = [analyze_stock(s, state, candidate_cap, cfg, history_model, model_status) for s in data["stocks"]]
    rows.sort(key=lambda x: x["_sort_tuple"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        r.pop("_sort_tuple", None)
    workflow = copy.deepcopy(data.get("workflow_trace") or [])
    for item in workflow:
        if item.get('step')=='市场环境': item['step']='市场总闸门'
        if item.get('step')=='风险否决与排序': item['step']='风险否决与最终排序'
    def _upsert_workflow(step: str, detail: str) -> None:
        for item in workflow:
            if isinstance(item, dict) and item.get("step") == step:
                item.update({"status":"完成", "detail":detail})
                return
        workflow.append({"step":step, "status":"完成", "detail":detail})
    _upsert_workflow("市场总闸门", f"{gate_method}；最终状态={state}；候选上限={candidate_cap}")
    _upsert_workflow('历史样本', model_status['message'])
    for item in workflow:
        if item.get('step')=='历史样本': item['status']=model_status['status']
    _upsert_workflow("爆发力评分", "逐股完成技术动量/结构地位/资金质量/资金弹性/事件驱动/历史验证六维评分，并独立计算风险扣分")
    _upsert_workflow("风险否决与最终排序", "硬否决先行；候选按短线爆发力得分排序；同分按股票代码稳定排序，禁止输入顺序影响结果")
    pipeline = data.get("pipeline", "manual/degraded")
    if str(pipeline)=="raw-postmarket-v5.0-audited" and bool((data.get("raw_data_audit") or {}).get("passed")):
        lookahead = "通过：原始数据审计已通过；输入字段、嵌套日期/时间通过T日截止校验；特征计算前已物理截断到T日。"
    else:
        lookahead = "仅通过输入快照字段/日期/时间检查；上游原始数据审计或生产标识不完整，已强制降级，禁止声明完整无泄漏生产链路。"
    return {
        "trade_date": data["trade_date"], "as_of": data["as_of"],
        "mode": "仅盘后；不使用盘中和集合竞价",
        "lookahead_check": lookahead,
        "pipeline": pipeline,
        "raw_data_audit": data.get("raw_data_audit") or {},
        "coverage": coverage,
        "workflow_trace": workflow,
        "market_state": state, "market_gate_method": gate_method, "market_reasons": reasons,
        "candidate_level_cap": candidate_cap,
        "history_model": model_status,
        "ranking_policy": "风险闸门先行；技术动量、结构地位、资金质量、资金弹性、事件驱动、历史验证形成透明短线爆发力相对评分；透支/事件/龙虎榜异常独立扣分。评分不是未经校准的上涨概率。核心候选必须同时满足高分、整体滚动样本外生产验收和当前历史桶强正向。",
        "results": rows,
    }


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save_json(obj: Dict[str, Any], path: str | Path) -> None:
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
