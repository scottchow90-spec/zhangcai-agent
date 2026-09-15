from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from .utils import clip

@dataclass(frozen=True)
class MarketEnvResult:
    state: str
    permission: str
    composite: float
    climax: bool
    data_quality: str
    reasons: tuple[str,...]


def _median(values):
    z=sorted(float(x) for x in values);n=len(z)
    if not n:return 0.0
    return z[n//2] if n%2 else (z[n//2-1]+z[n//2])/2

# 所有输入均为截至当日、基于过去120交易日的滚动百分位，0最弱/低，1最强/高。
# V5.0取消旧版硬编码加权“市场综合分”作为状态决定器，改用透明规则和等权中位健康值做审计辅助。
def classify_market(m: Mapping[str,float|bool|str]) -> MarketEnvResult:
    required=['breadth_pctile','sentiment_pctile','trend_pctile','liquidity_pctile','smallcap_relative_pctile','risk_pctile','divergence_pctile','improvement']
    missing=[k for k in required if k not in m or m[k] is None]
    if missing:
        return MarketEnvResult('震荡可做','暂停',0.0,False,'insufficient',(f"缺失市场字段:{','.join(missing)}",))
    breadth=clip(float(m['breadth_pctile']));sentiment=clip(float(m['sentiment_pctile']));trend=clip(float(m['trend_pctile']))
    liq=clip(float(m['liquidity_pctile']));small=clip(float(m['smallcap_relative_pctile']));risk=clip(float(m['risk_pctile']));div=clip(float(m['divergence_pctile']))
    imp=max(-1.0,min(1.0,float(m['improvement'])))
    health=clip(_median([breadth,sentiment,trend,liq,small,1-risk,1-div]))

    panic=(risk>=0.90 and breadth<=0.20) or (breadth<=0.10 and sentiment<=0.15)
    ebb=((breadth<0.28 and sentiment<0.32 and risk>=0.65) or (risk>=0.85 and sentiment<0.40) or (health<0.30 and imp<=0))
    severe_div=div>=0.75 and breadth<0.45
    repair=imp>=0.20 and breadth<0.58 and sentiment<0.58 and not panic and not ebb
    broad_bull=(breadth>=0.65 and sentiment>=0.60 and trend>=0.55 and risk<=0.45 and div<=0.55)
    positive_votes=sum([breadth>=0.50,sentiment>=0.50,trend>=0.50,liq>=0.45,small>=0.45])
    structural_bull=(positive_votes>=3 and sentiment>=0.48 and risk<0.70 and div<0.70 and imp>-0.35)

    if panic:
        state,perm='恐慌','暂停'
    elif ebb:
        state,perm='退潮','暂停'
    elif severe_div:
        state,perm='结构严重分化','暂停' if imp < -0.20 else '精选'
    elif repair:
        state,perm='修复','小仓试错'
    elif broad_bull:
        state,perm='全面主升','正常'
    elif structural_bull:
        state,perm='结构性主升','正常'
    else:
        state,perm='震荡可做','精选'

    climax=bool(m.get('index_extreme_up',False) and m.get('turnover_extreme',False)
                and m.get('sector_broad_surge',False) and m.get('individual_accelerating',False))
    reasons=(f"健康中位值={health:.3f}",f"宽度={breadth:.2f}",f"情绪={sentiment:.2f}",f"趋势={trend:.2f}",
             f"流动性={liq:.2f}",f"风险={risk:.2f}",f"背离={div:.2f}",f"改善速度={imp:.2f}",f"正向条件数={positive_votes}/5")
    return MarketEnvResult(state,perm,health,climax,'normal',reasons)
