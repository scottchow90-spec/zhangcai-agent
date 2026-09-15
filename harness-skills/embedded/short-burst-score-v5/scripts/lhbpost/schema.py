from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

MARKET_STATES = ("全面主升","结构性主升","震荡可做","结构严重分化","修复","退潮","恐慌")
PERMISSIONS = ("正常","精选","小仓试错","暂停")

@dataclass(frozen=True)
class CandidateFeatures:
    trade_date: str
    ts_code: str
    name: str = ""
    exchange: str = ""
    board: str = ""
    list_days: int = 9999
    is_st: bool = False
    is_delisting_arrangement: bool = False
    data_quality: str = "normal"  # normal / warning / insufficient

    market_state: str = "震荡可做"
    market_permission: str = "精选"
    market_climax: bool = False

    sector_code: str = ""
    theme_code: str = "__UNKNOWN_THEME__"
    theme_verified: bool = False
    sector_rs_5d_pctile: float = 0.5
    sector_activity_pctile: float = 0.5
    sector_core_rank: int = 99
    sector_is_ebb: bool = False
    independent_catalyst: bool = False
    catalyst_quality: Optional[float] = None
    catalyst_public_before_cutoff: bool = False

    rs_20d_pctile: float = 0.5
    ma20_slope_pctile: float = 0.5
    close_above_ma20: bool = False
    ma5_gt_ma10_gt_ma20: bool = False
    ma20_gt_ma60: bool = False

    breakout_20d_strength: float = 0.0     # 0..1, 1=确认突破
    close_location_day: float = 0.5        # (C-L)/(H-L)
    volume_health: float = 0.5             # 0..1
    startup_location_health: float = 0.5   # 0..1
    turnover_rate_pctile: float = 0.5      # 同日全市场换手率百分位
    free_mcap_pctile: float = 0.5          # 同日全市场自由流通市值百分位，小=更小盘
    lhb_net_free_float_pctile: float = 0.5 # 同日龙虎榜净买/自由流通市值百分位

    lhb_net_buy_ratio: float = 0.0
    lhb_net_impact_pctile: float = 0.5
    lhb_participation_pctile: float = 0.5

    inst_net_buy_ratio: float = 0.0
    inst_net_impact_pctile: float = 0.5
    broker_net_buy_ratio: float = 0.0
    broker_net_impact_pctile: float = 0.5
    buy_sell_balance: float = 0.0          # -1..1

    lifecycle_event_no: int = 1
    lifecycle_net_improving: bool = False

    seat_quality_pctile: Optional[float] = None
    seat_quality_samples: int = 0

    risk_penalty: float = 0.0              # 0..1; severe risk belongs in veto

    # hard-veto evidence
    downward_anomaly_without_reversal: bool = False
    three_day_surge_high_climax: bool = False
    extreme_volume_inst_sell_weak_relay: bool = False
    severe_negative_event: bool = False

    extra: Dict[str, Any] = field(default_factory=dict, compare=False)
