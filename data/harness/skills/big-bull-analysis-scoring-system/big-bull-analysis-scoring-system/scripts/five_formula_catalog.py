from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

from collections import Counter
from collections.abc import Iterable as IterableABC
from collections.abc import Sequence as SequenceABC
from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence


FORMULAS = (
    "大牛线撑压版",
    "飞龙在天",
    "游资资金监控",
    "庄家资金监控",
    "机构资金监控",
)

_FORMULA_COUNTS = {
    "大牛线撑压版": 16,
    "飞龙在天": 10,
    "游资资金监控": 5,
    "庄家资金监控": 4,
    "机构资金监控": 16,
}
_ALLOWED_ROLES = frozenset(
    {"predictive_candidate", "confirmation", "quality_gate", "prospective"}
)
_FORBIDDEN_FIELD_MARKERS = ("weight", "score")
_POINT_IN_TIME_POLICY = "exclude_without_point_in_time_evidence"
_PROSPECTIVE_POLICY = "block_until_point_in_time_history_available"
_NON_MODEL_POLICY = "not_a_model_input"
_TOP_STRING_FIELDS = frozenset(
    {
        "formula",
        "key",
        "name",
        "source_expression",
        "source_field",
        "role",
        "expected_direction",
        "lineage_group",
        "missing_policy",
    }
)
_NESTED_STRING_FIELDS = frozenset(
    {
        "formula",
        "variable",
        "key",
        "parent_key",
        "source_expression",
        "source_field",
        "role",
        "expected_direction",
        "lineage_group",
        "missing_policy",
        "contribution_key",
    }
)
_NESTED_BOOL_FIELDS = frozenset(
    {"model_eligible", "top_level_alias", "visible_contribution"}
)


class CatalogValidationError(ValueError):
    """Raised when a candidate catalog violates the authoritative structure."""


@dataclass(frozen=True, slots=True)
class _CatalogItem:
    formula: str
    number: int
    key: str
    name: str
    source_expression: str
    source_field: str
    role: str
    expected_direction: str
    model_eligible: bool
    lineage_group: str
    missing_policy: str


@dataclass(frozen=True, slots=True)
class _NestedVariable:
    formula: str
    variable: str
    key: str
    parent_key: str
    source_expression: str
    source_field: str
    role: str
    expected_direction: str
    model_eligible: bool
    lineage_group: str
    missing_policy: str
    top_level_alias: bool
    contribution_key: str
    visible_contribution: bool


@dataclass(frozen=True, slots=True)
class _NestedRollupExpectation:
    key: str
    parent_key: str
    top_level_alias: bool
    contribution_key: str
    visible_contribution: bool


def _predictive(
    formula: str,
    number: int,
    key: str,
    name: str,
    expression: str,
    source_field: str,
    *,
    direction: str = "higher_is_bullish",
    lineage_group: str | None = None,
) -> _CatalogItem:
    return _CatalogItem(
        formula=formula,
        number=number,
        key=key,
        name=name,
        source_expression=expression,
        source_field=source_field,
        role="predictive_candidate",
        expected_direction=direction,
        model_eligible=True,
        lineage_group=lineage_group or key,
        missing_policy=_POINT_IN_TIME_POLICY,
    )


def _non_model(
    formula: str,
    number: int,
    key: str,
    name: str,
    expression: str,
    source_field: str,
    *,
    role: str,
    direction: str,
    lineage_group: str,
    missing_policy: str = _NON_MODEL_POLICY,
) -> _CatalogItem:
    return _CatalogItem(
        formula=formula,
        number=number,
        key=key,
        name=name,
        source_expression=expression,
        source_field=source_field,
        role=role,
        expected_direction=direction,
        model_eligible=False,
        lineage_group=lineage_group,
        missing_policy=missing_policy,
    )


_SUBSYSTEMS = (
    _predictive(
        FORMULAS[0], 1, "dnx_main_trend", "主趋势线",
        "主趋势线:EMA(EMA(CLOSE,10),10)*SSX1", "主趋势线",
    ),
    _predictive(
        FORMULAS[0], 2, "dnx_ema_layers", "EMA均线分层",
        "SSX4:=EMA(CLOSE,5)>EMA(CLOSE,20)*SSX2; SSX5:=EMA(CLOSE,5)<EMA(CLOSE,20)*SSX2; SSX6:=EMA(CLOSE,5)>EMA(CLOSE,10)*SSX2; SSX7:=EMA(CLOSE,5)<EMA(CLOSE,10)*SSX1; EMA9:EMA(CLOSE,173); EMA10:EMA(CLOSE,193); EMA11:EMA(CLOSE,213)",
        "SSX4/SSX5/SSX6/SSX7/EMA9/EMA10/EMA11",
    ),
    _predictive(
        FORMULAS[0], 3, "dnx_k_color", "K线颜色信号",
        "SSX8:=CLOSE<OPEN; STICKLINE(SSX4,HIGH,LOW,0,0); STICKLINE(SSX5,HIGH,LOW,0,0); STICKLINE(SSX5 AND SSX6,HIGH,LOW,0,1); STICKLINE(SSX4 AND SSX7,HIGH,LOW,0,0)",
        "SSX4/SSX5/SSX6/SSX7/SSX8/STICKLINE",
    ),
    _predictive(
        FORMULAS[0], 4, "dnx_float_cap", "流通市值",
        "流通市值:(FINANCE(40)/100000000)", "流通市值",
    ),
    _predictive(
        FORMULAS[0], 5, "dnx_dx", "DX动量指标",
        "MTM:=C-REF(C,1); DX:=100*EMA(EMA(MTM,6),6)/EMA(EMA(ABS(MTM),6),6)",
        "DX",
    ),
    _predictive(
        FORMULAS[0], 6, "dnx_participation_exit", "参与与离场信号",
        "卖:=IF(HHV(DX,2)=HHV(DX,7) AND COUNT(DX>50,2) AND CROSS(MA(DX,2),DX),1,0); 买1:=IF(LLV(DX,2)=LLV(DX,7) AND COUNT(DX<0,2) AND CROSS(DX,MA(DX,2)),1,0)",
        "买1/卖", direction="signal_specific",
    ),
    _predictive(
        FORMULAS[0], 7, "dnx_control", "控盘程度",
        "VAW1:=EMA(EMA(CLOSE,13),13); 控盘:=(VAW1-REF(VAW1,1))/REF(VAW1,1)*1000",
        "控盘",
    ),
    _predictive(
        FORMULAS[0], 8, "dnx_caishen", "财神短线",
        "财:=(EMA(CLOSE,S)-EMA(CLOSE,P))*50; 神:=EMA(财,M1)", "财/神",
    ),
    _predictive(
        FORMULAS[0], 9, "dnx_dealer_in_out", "庄进与庄出",
        "STJ83:=STJ81 AND STJ82; 庄:=BTJ11 AND BTJ2 AND BTJ3; 有庄:=FILTER(庄,30)",
        "STJ83/有庄", direction="signal_specific",
    ),
    _predictive(
        FORMULAS[0], 10, "dnx_yaogu", "妖股识别",
        "妖股:=XDF AND C/REF(C,1)>1.095 AND FLIGA AND VARAA", "妖股",
    ),
    _predictive(
        FORMULAS[0], 11, "dnx_leader_zone", "龙头参与区",
        "龙头第一买点:=IF((AA AND (CB<1)),1,0); 龙头第二买点:=IF((((CLOSE/REF(CLOSE,1))>=1.07)AND (CB<1)),1,0)",
        "龙头第一买点/龙头第二买点",
    ),
    _predictive(
        FORMULAS[0], 12, "dnx_dragon_pullback", "龙回头",
        "龙回头:=IF((((A AND REF(PP1,1) AND HH) OR (A AND REF(PP33,1) AND HH))),1,0 )",
        "龙回头",
    ),
    _predictive(
        FORMULAS[0], 13, "dnx_ignition", "点火信号",
        "FF:=EMA(CLOSE,3); MA15:=EMA(CLOSE,21); CROSS(FF,MA15)",
        "CROSS(FF,MA15)",
    ),
    _predictive(
        FORMULAS[0], 14, "dnx_theme_resonance", "起爆与题材共振",
        "起爆1:=金叉 AND ABC0 AND ABC1 AND ABC2 AND ABC3 AND ABC4",
        "起爆1",
    ),
    _predictive(
        FORMULAS[0], 15, "dnx_boll_ma", "BOLL与多重均线",
        "MA5:=MA(CLOSE,5); MA10:=MA(CLOSE,10); MA20:=MA(CLOSE,20); MA30:=MA(CLOSE,30); MA60:=MA(CLOSE,60); BOLL:=MA(CLOSE,M); UB:=BOLL+2*STD(CLOSE,M); LB:=BOLL-2*STD(CLOSE,M)",
        "MA5/MA10/MA20/MA30/MA60/BOLL/UB/LB", direction="contextual",
    ),
    _predictive(
        FORMULAS[0], 16, "dnx_support_pressure", "核心黄金分割撑压",
        "主趋势线:EMA(EMA(CLOSE,10),10)*SSX1; EMA9:EMA(CLOSE,173); EMA10:EMA(CLOSE,193); EMA11:EMA(CLOSE,213); BOLL:=MA(CLOSE,M); UB:=BOLL+2*STD(CLOSE,M); LB:=BOLL-2*STD(CLOSE,M)",
        "主趋势线/EMA9/EMA10/EMA11/BOLL/UB/LB（源文件无同名单字段）",
        direction="contextual",
    ),
    _predictive(
        FORMULAS[1], 1, "fl_dragon", "龙头战法",
        "龙头战法:=IF((COUNT(X_9X=1,4)=3 AND X_9X=0 AND OPEN<CLOSE AND (CLOSE-REF(CLOSE,1))/REF(CLOSE,1)>0.089)*10>=10 OR ((CLOSE-REF(CLOSE,1))/REF(CLOSE,1)>0.089 AND (REF(X_14X,1) OR REF(X_13X,1))) AND X_4X=1,100,DRAWNULL)",
        "龙头战法",
    ),
    _predictive(
        FORMULAS[1], 2, "fl_trend_filter", "趋势过滤/中长期均线强势条件",
        "X_15X:=EMA(CLOSE,89); X_16X:=EMA(EMA(EMA(HIGH,13),13),13); X_17X:=EMA(EMA(EMA(HIGH,5),5),5); X_24:=CLOSE>X_17X AND CLOSE>X_16X AND CLOSE>X_15X; X_27:=X_19X AND X_20X AND X_21X AND X_22 AND X_23 AND X_24 AND X_25<1.16 AND X_26",
        "X_15X/X_16X/X_17X/X_24/X_27",
    ),
    _predictive(
        FORMULAS[1], 3, "fl_box", "四日实体重叠箱体/波段密码底层形态",
        "X_32:=X_28>=X_30 AND X_29<=X_30 AND X_28>=X_31 AND X_29<=X_31; X_33:=REF(X_28,1)>=X_30 AND REF(X_29,1)<=X_30 AND REF(X_28,1)>=X_31 AND REF(X_29,1)<=X_31; X_34:=REF(X_28,2)>=X_30 AND REF(X_29,2)<=X_30 AND REF(X_28,2)>=X_31 AND REF(X_29,2)<=X_31; X_35:=REF(X_28,3)>=X_30 AND REF(X_29,3)<=X_30 AND REF(X_28,3)>=X_31 AND REF(X_29,3)<=X_31; X_36:=X_32 AND X_33 AND X_34 AND X_35",
        "X_28/X_29/X_30/X_31/X_32/X_33/X_34/X_35/X_36/X_37",
    ),
    _predictive(
        FORMULAS[1], 4, "fl_unique_limit", "首板/唯一涨停确认",
        "X_45:=X_18X>9.85 AND NOT(OPEN=CLOSE); X_46:=COUNT(X_45,21); X_47:=X_46=1 AND X_45",
        "X_45/X_46/X_47",
    ),
    _predictive(
        FORMULAS[1], 5, "fl_board", "波段密码打板",
        "X_55:=X_27 AND X_52 AND X_37; 波段密码打板:=IF(FILTER(X_55,13) AND X_47,100,DRAWNULL)",
        "波段密码打板",
    ),
    _predictive(
        FORMULAS[1], 6, "fl_surge", "量价模型/暴涨启动",
        "X_10:=0.0068*X_7-0.0072*X_8-0.5676*X_9-0.0105; X_11:=0.0015*X_7-0.0124*X_8+1.7461*X_9-0.0074; 暴涨启动:=(0-12.2401*X_10-1*X_11+0.321<0)*100",
        "X_7/X_8/X_9/X_10/X_11/暴涨启动",
    ),
    _predictive(
        FORMULAS[1], 7, "fl_wave", "波段随机强弱-波",
        "X_13:=(CLOSE-LLV(LOW,36))/(HHV(HIGH,36)-LLV(LOW,36))*100; X_14:=SMA(X_13,3,1); X_15:=SMA(X_14,3,1); 波:X_15",
        "波",
    ),
    _predictive(
        FORMULAS[1], 8, "fl_segment", "波段随机强弱-段",
        "X_16:=SMA(X_15,3,1); 段:X_16", "段",
    ),
    _predictive(
        FORMULAS[1], 9, "fl_private", "私募秘进",
        "X_20:=CLOSE/REF(CLOSE,1)>1.048 AND CLOSE=HIGH AND BETWEEN(FORCAST(VOL,4),0.2*FORCAST(VOL,12),2.1*FORCAST(VOL,12)); 私募秘进:=FILTER(X_20,28)*100",
        "私募秘进",
    ),
    _predictive(
        FORMULAS[1], 10, "fl_main_rise", "主升启动共振",
        "XS1:=私募秘进 OR (0-12.2401*X_10-1*X_11+0.321<0); XS2:=(FILTER(X_55,13) AND X_47) OR ((COUNT(X_9X=1,4)=3 AND X_9X=0 AND OPEN<CLOSE AND (CLOSE-REF(CLOSE,1))/REF(CLOSE,1)>0.089)*10>=10 OR ((CLOSE-REF(CLOSE,1))/REF(CLOSE,1)>0.089 AND (REF(X_14X,1) OR REF(X_13X,1))) AND X_4X=1); XS1 AND XS2",
        "XS1/XS2",
    ),
    _predictive(
        FORMULAS[2], 1, "youzi_aaa_trend_diff", "AAA快慢EMA趋势差",
        "AAA:EMA(CLOSE,5)-EMA(CLOSE,30)", "AAA", lineage_group="youzi_buyer_intent",
    ),
    _predictive(
        FORMULAS[2], 2, "youzi_ddd_signal", "DDD买方意向信号线",
        "DDD:EMA(AAA,5)", "DDD", lineage_group="youzi_buyer_intent",
    ),
    _predictive(
        FORMULAS[2], 3, "youzi_buyer_intent", "买方意向主输出",
        "买方意向:(AAA-DDD)*2", "买方意向", lineage_group="youzi_buyer_intent",
    ),
    _non_model(
        FORMULAS[2], 4, "youzi_positive_buyer_bar", "正向买方意向柱/OUTPUT4",
        "STICKLINE(买方意向>0,买方意向,0,3,0)", "STICKLINE/OUTPUT4",
        role="confirmation", direction="confirms_positive_parent",
        lineage_group="youzi_buyer_intent",
    ),
    _non_model(
        FORMULAS[2], 5, "youzi_l2_tiers", "L2四档资金分层模块",
        "X_1:=L2_AMO(0,2)/10000; X_2:=L2_AMO(1,2)/10000; X_3:=L2_AMO(2,2)/10000; X_4:=L2_AMO(3,2)/10000; X_5:=L2_AMO(0,3)/10000; X_6:=L2_AMO(1,3)/10000; X_7:=L2_AMO(2,3)/10000; X_8:=L2_AMO(3,3)/10000; X_9:=X_1+X_2+X_3+X_4-(X_5+X_6+X_7+X_8); X_10:=X_1-X_5; X_11:=X_2-X_6; X_12:=X_3-X_7; X_13:=X_4-X_8",
        "X_1/X_2/X_3/X_4/X_5/X_6/X_7/X_8/X_9/X_10/X_11/X_12/X_13",
        role="prospective", direction="pending_point_in_time_evidence",
        lineage_group="youzi_l2_tiers", missing_policy=_PROSPECTIVE_POLICY,
    ),
    _non_model(
        FORMULAS[3], 1, "zj_output3", "OUTPUT3",
        "STICKLINE(控盘程度,0,控盘程度,3,0)", "STICKLINE/OUTPUT3",
        role="confirmation", direction="confirms_zj_control_degree",
        lineage_group="zj_control_degree",
    ),
    _non_model(
        FORMULAS[3], 2, "zj_output4", "OUTPUT4",
        "STICKLINE(控盘程度 AND 控盘程度>100,100,控盘程度,3,0)",
        "STICKLINE/OUTPUT4", role="confirmation",
        direction="confirms_zj_control_degree_above_100",
        lineage_group="zj_control_degree",
    ),
    _predictive(
        FORMULAS[3], 3, "zj_control_degree", "控盘程度",
        "控盘程度:(IF(B6>N1,B6-N1,0))*3.5", "控盘程度",
        lineage_group="zj_control_degree",
    ),
    _non_model(
        FORMULAS[3], 4, "zj_control_scale", "控盘度",
        "控盘度:100", "控盘度", role="quality_gate", direction="none",
        lineage_group="zj_control_scale",
    ),
    _predictive(
        FORMULAS[4], 1, "jigou_large_order_flow", "大单动向",
        "大单动向:(LARGEINTRDVOL-LARGEOUTTRDVOL)*10000/FINANCE(7)",
        "大单动向", lineage_group="jigou_large_order_flow",
    ),
    _predictive(
        FORMULAS[4], 2, "jigou_notext1", "NOTEXT1",
        "NOTEXT1:MA(大单动向,10)*3", "NOTEXT1",
        lineage_group="jigou_large_order_flow",
    ),
    _non_model(
        FORMULAS[4], 3, "jigou_output3", "OUTPUT3",
        "STICKLINE(大单动向>0,0,大单动向*(大单动向>0),3,0)",
        "STICKLINE/OUTPUT3", role="confirmation",
        direction="confirms_positive_large_order_flow",
        lineage_group="jigou_large_order_flow",
    ),
    _non_model(
        FORMULAS[4], 4, "jigou_output4", "OUTPUT4",
        "DRAWGBK(CLOSE>0,RGB(0,0,0),RGB(0,0,0),0,9,0)",
        "DRAWGBK/OUTPUT4", role="quality_gate", direction="none",
        lineage_group="jigou_background",
    ),
    _non_model(
        FORMULAS[4], 5, "jigou_x1", "X_1",
        "X_1:=(L2_VOL(0,0)-L2_VOL(0,1))*VOL/10000", "X_1",
        role="prospective", direction="pending_point_in_time_evidence",
        lineage_group="jigou_institutional_flow", missing_policy=_PROSPECTIVE_POLICY,
    ),
    _non_model(
        FORMULAS[4], 6, "jigou_x2", "X_2",
        "X_2:=(L2_VOL(1,0)-L2_VOL(1,1))*VOL/10000", "X_2",
        role="prospective", direction="pending_point_in_time_evidence",
        lineage_group="jigou_large_holder_flow", missing_policy=_PROSPECTIVE_POLICY,
    ),
    _non_model(
        FORMULAS[4], 7, "jigou_x3", "X_3",
        "X_3:=(L2_VOL(2,0)-L2_VOL(2,1))*VOL/10000", "X_3",
        role="prospective", direction="pending_point_in_time_evidence",
        lineage_group="jigou_medium_flow", missing_policy=_PROSPECTIVE_POLICY,
    ),
    _non_model(
        FORMULAS[4], 8, "jigou_x4", "X_4",
        "X_4:=(L2_VOL(3,0)-L2_VOL(3,1))*VOL/10000", "X_4",
        role="prospective", direction="pending_point_in_time_evidence",
        lineage_group="jigou_retail_flow", missing_policy=_PROSPECTIVE_POLICY,
    ),
    _predictive(
        FORMULAS[4], 9, "jigou_institutional_in", "机构大单进",
        "机构大单进:EMA(X_1,20)*60/CAPITAL", "机构大单进",
        lineage_group="jigou_institutional_flow",
    ),
    _non_model(
        FORMULAS[4], 10, "jigou_output6", "OUTPUT6",
        "STICKLINE(机构大单进>0,0,机构大单进*(机构大单进>0),3,0)",
        "STICKLINE/OUTPUT6", role="confirmation",
        direction="confirms_positive_institutional_flow",
        lineage_group="jigou_institutional_flow",
    ),
    _non_model(
        FORMULAS[4], 11, "jigou_institutional_out", "机构大单出",
        "机构大单出:机构大单进<0", "机构大单出", role="confirmation",
        direction="confirms_negative_institutional_flow",
        lineage_group="jigou_institutional_flow",
    ),
    _predictive(
        FORMULAS[4], 12, "jigou_large_holder_in", "大户大单进",
        "大户大单进:EMA(X_2,20)*60/CAPITAL", "大户大单进",
        lineage_group="jigou_large_holder_flow",
    ),
    _non_model(
        FORMULAS[4], 13, "jigou_x5", "X_5",
        "X_5:=EMA(X_3,20)*60/CAPITAL", "X_5", role="prospective",
        direction="pending_point_in_time_evidence", lineage_group="jigou_medium_flow",
        missing_policy=_PROSPECTIVE_POLICY,
    ),
    _predictive(
        FORMULAS[4], 14, "jigou_retail_in", "散户资金进",
        "散户资金进:EMA(X_4,20)*60/CAPITAL", "散户资金进",
        lineage_group="jigou_retail_flow",
    ),
    _non_model(
        FORMULAS[4], 15, "jigou_small_order_out", "小单资金出",
        "小单资金出:大户大单进<0", "小单资金出", role="confirmation",
        direction="confirms_negative_large_holder_flow",
        lineage_group="jigou_large_holder_flow",
    ),
    _non_model(
        FORMULAS[4], 16, "jigou_axis", "中轴线",
        "中轴线:0", "中轴线", role="quality_gate", direction="none",
        lineage_group="jigou_axis",
    ),
)


def _nested(
    formula: str,
    variable: str,
    key: str,
    parent_key: str,
    expression: str,
    *,
    role: str,
    model_eligible: bool,
    lineage_group: str,
    top_level_alias: bool = False,
    contribution_key: str | None = None,
    missing_policy: str | None = None,
) -> _NestedVariable:
    return _NestedVariable(
        formula=formula,
        variable=variable,
        key=key,
        parent_key=parent_key,
        source_expression=expression,
        source_field=variable,
        role=role,
        expected_direction=(
            "higher_is_bullish"
            if role == "predictive_candidate"
            else "pending_point_in_time_evidence"
            if role == "prospective"
            else "lineage_evidence"
            if role == "confirmation"
            else "none"
        ),
        model_eligible=model_eligible,
        lineage_group=lineage_group,
        missing_policy=missing_policy
        or (_POINT_IN_TIME_POLICY if model_eligible else _NON_MODEL_POLICY),
        top_level_alias=top_level_alias,
        contribution_key=contribution_key or parent_key,
        visible_contribution=False,
    )


_YOUZI_EXPRESSIONS = (
    "X_1:=L2_AMO(0,2)/10000",
    "X_2:=L2_AMO(1,2)/10000",
    "X_3:=L2_AMO(2,2)/10000",
    "X_4:=L2_AMO(3,2)/10000",
    "X_5:=L2_AMO(0,3)/10000",
    "X_6:=L2_AMO(1,3)/10000",
    "X_7:=L2_AMO(2,3)/10000",
    "X_8:=L2_AMO(3,3)/10000",
    "X_9:=X_1+X_2+X_3+X_4-(X_5+X_6+X_7+X_8)",
    "X_10:=X_1-X_5",
    "X_11:=X_2-X_6",
    "X_12:=X_3-X_7",
    "X_13:=X_4-X_8",
    "CONST(MAX(ABS(X_9),MAX(ABS(X_10),MAX(ABS(X_11),MAX(ABS(X_12),ABS(X_13))))))",
)

_JIGOU_EXPRESSIONS = (
    "X_1:=(L2_VOL(0,0)-L2_VOL(0,1))*VOL/10000",
    "X_2:=(L2_VOL(1,0)-L2_VOL(1,1))*VOL/10000",
    "X_3:=(L2_VOL(2,0)-L2_VOL(2,1))*VOL/10000",
    "X_4:=(L2_VOL(3,0)-L2_VOL(3,1))*VOL/10000",
    "X_5:=EMA(X_3,20)*60/CAPITAL",
)

_ZJ_EXPRESSIONS = (
    "B1:=(HHV(H,N)-C)/(HHV(H,N)-LLV(LOW,N))*100-M",
    "B2:=SMA(B1,N,1)+100",
    "B3:=(C-LLV(L,N))/(HHV(H,N)-LLV(L,N))*100",
    "B4:=SMA(B3,7,1)",
    "B5:=SMA(B4,5,1)+100",
    "B6:=B5-B2",
)

_NESTED_VARIABLES = (
    *tuple(
        _nested(
            FORMULAS[2], f"X_{number}", f"youzi_x{number}", "youzi_l2_tiers",
            expression,
            role="quality_gate" if number == 14 else "prospective",
            model_eligible=False,
            lineage_group="youzi_l2_tiers",
            missing_policy=(
                _NON_MODEL_POLICY if number == 14 else _PROSPECTIVE_POLICY
            ),
        )
        for number, expression in enumerate(_YOUZI_EXPRESSIONS, start=1)
    ),
    *tuple(
        _nested(
            FORMULAS[4], f"X_{number}", f"jigou_x{number}", f"jigou_x{number}",
            expression,
            role="prospective",
            model_eligible=False,
            lineage_group=(
                "jigou_institutional_flow" if number == 1
                else "jigou_large_holder_flow" if number == 2
                else "jigou_medium_flow" if number in (3, 5)
                else "jigou_retail_flow"
            ),
            top_level_alias=True,
            missing_policy=_PROSPECTIVE_POLICY,
        )
        for number, expression in enumerate(_JIGOU_EXPRESSIONS, start=1)
    ),
    *tuple(
        _nested(
            FORMULAS[3], f"B{number}", f"zj_b{number}", "zj_control_degree",
            expression,
            role="predictive_candidate" if number in (2, 5, 6) else "confirmation",
            model_eligible=number in (2, 5, 6),
            lineage_group="zj_control_degree",
            contribution_key="zj_control_degree",
        )
        for number, expression in enumerate(_ZJ_EXPRESSIONS, start=1)
    ),
)

LINEAGE_REGISTRY = (
    "dnx_main_trend",
    "dnx_ema_layers",
    "dnx_k_color",
    "dnx_float_cap",
    "dnx_dx",
    "dnx_participation_exit",
    "dnx_control",
    "dnx_caishen",
    "dnx_dealer_in_out",
    "dnx_yaogu",
    "dnx_leader_zone",
    "dnx_dragon_pullback",
    "dnx_ignition",
    "dnx_theme_resonance",
    "dnx_boll_ma",
    "dnx_support_pressure",
    "fl_dragon",
    "fl_trend_filter",
    "fl_box",
    "fl_unique_limit",
    "fl_board",
    "fl_surge",
    "fl_wave",
    "fl_segment",
    "fl_private",
    "fl_main_rise",
    "youzi_buyer_intent",
    "youzi_l2_tiers",
    "zj_control_degree",
    "zj_control_scale",
    "jigou_large_order_flow",
    "jigou_background",
    "jigou_institutional_flow",
    "jigou_large_holder_flow",
    "jigou_medium_flow",
    "jigou_retail_flow",
    "jigou_axis",
)
_TOP_LINEAGE_BY_KEY = MappingProxyType(
    {
        "dnx_main_trend": "dnx_main_trend",
        "dnx_ema_layers": "dnx_ema_layers",
        "dnx_k_color": "dnx_k_color",
        "dnx_float_cap": "dnx_float_cap",
        "dnx_dx": "dnx_dx",
        "dnx_participation_exit": "dnx_participation_exit",
        "dnx_control": "dnx_control",
        "dnx_caishen": "dnx_caishen",
        "dnx_dealer_in_out": "dnx_dealer_in_out",
        "dnx_yaogu": "dnx_yaogu",
        "dnx_leader_zone": "dnx_leader_zone",
        "dnx_dragon_pullback": "dnx_dragon_pullback",
        "dnx_ignition": "dnx_ignition",
        "dnx_theme_resonance": "dnx_theme_resonance",
        "dnx_boll_ma": "dnx_boll_ma",
        "dnx_support_pressure": "dnx_support_pressure",
        "fl_dragon": "fl_dragon",
        "fl_trend_filter": "fl_trend_filter",
        "fl_box": "fl_box",
        "fl_unique_limit": "fl_unique_limit",
        "fl_board": "fl_board",
        "fl_surge": "fl_surge",
        "fl_wave": "fl_wave",
        "fl_segment": "fl_segment",
        "fl_private": "fl_private",
        "fl_main_rise": "fl_main_rise",
        "youzi_aaa_trend_diff": "youzi_buyer_intent",
        "youzi_ddd_signal": "youzi_buyer_intent",
        "youzi_buyer_intent": "youzi_buyer_intent",
        "youzi_positive_buyer_bar": "youzi_buyer_intent",
        "youzi_l2_tiers": "youzi_l2_tiers",
        "zj_output3": "zj_control_degree",
        "zj_output4": "zj_control_degree",
        "zj_control_degree": "zj_control_degree",
        "zj_control_scale": "zj_control_scale",
        "jigou_large_order_flow": "jigou_large_order_flow",
        "jigou_notext1": "jigou_large_order_flow",
        "jigou_output3": "jigou_large_order_flow",
        "jigou_output4": "jigou_background",
        "jigou_x1": "jigou_institutional_flow",
        "jigou_x2": "jigou_large_holder_flow",
        "jigou_x3": "jigou_medium_flow",
        "jigou_x4": "jigou_retail_flow",
        "jigou_institutional_in": "jigou_institutional_flow",
        "jigou_output6": "jigou_institutional_flow",
        "jigou_institutional_out": "jigou_institutional_flow",
        "jigou_large_holder_in": "jigou_large_holder_flow",
        "jigou_x5": "jigou_medium_flow",
        "jigou_retail_in": "jigou_retail_flow",
        "jigou_small_order_out": "jigou_large_holder_flow",
        "jigou_axis": "jigou_axis",
    }
)
_NESTED_LINEAGE_BY_IDENTITY = MappingProxyType(
    {
        **{
            (FORMULAS[2], f"X_{number}"): "youzi_l2_tiers"
            for number in range(1, 15)
        },
        (FORMULAS[4], "X_1"): "jigou_institutional_flow",
        (FORMULAS[4], "X_2"): "jigou_large_holder_flow",
        (FORMULAS[4], "X_3"): "jigou_medium_flow",
        (FORMULAS[4], "X_4"): "jigou_retail_flow",
        (FORMULAS[4], "X_5"): "jigou_medium_flow",
        **{
            (FORMULAS[3], f"B{number}"): "zj_control_degree"
            for number in range(1, 7)
        },
    }
)

_TOP_LEVEL_SIGNATURE = tuple(
    (item.formula, item.number, item.key, item.name) for item in _SUBSYSTEMS
)
_NESTED_SIGNATURE = tuple(
    (item.formula, item.variable, item.key, item.parent_key)
    for item in _NESTED_VARIABLES
)
_NESTED_VARIABLES_BY_FORMULA = {
    FORMULAS[2]: frozenset(f"X_{number}" for number in range(1, 15)),
    FORMULAS[4]: frozenset(f"X_{number}" for number in range(1, 6)),
    FORMULAS[3]: frozenset(f"B{number}" for number in range(1, 7)),
}
_NESTED_ROLLUP_EXPECTATIONS = MappingProxyType(
    {
        **{
            (FORMULAS[2], f"X_{number}"): _NestedRollupExpectation(
                key=f"youzi_x{number}",
                parent_key="youzi_l2_tiers",
                top_level_alias=False,
                contribution_key="youzi_l2_tiers",
                visible_contribution=False,
            )
            for number in range(1, 15)
        },
        **{
            (FORMULAS[4], f"X_{number}"): _NestedRollupExpectation(
                key=f"jigou_x{number}",
                parent_key=f"jigou_x{number}",
                top_level_alias=True,
                contribution_key=f"jigou_x{number}",
                visible_contribution=False,
            )
            for number in range(1, 6)
        },
        **{
            (FORMULAS[3], f"B{number}"): _NestedRollupExpectation(
                key=f"zj_b{number}",
                parent_key="zj_control_degree",
                top_level_alias=False,
                contribution_key="zj_control_degree",
                visible_contribution=False,
            )
            for number in range(1, 7)
        },
    }
)
_FIXED_NON_MODEL_TOP = {
    item.key: item.role for item in _SUBSYSTEMS if not item.model_eligible
}


def subsystem_catalog() -> list[dict[str, object]]:
    """Return a defensive copy of the fixed 51-item top-level catalog."""

    return [asdict(item) for item in _SUBSYSTEMS]


def nested_variable_catalog() -> list[dict[str, object]]:
    """Return a defensive copy of the fixed 25-node nested lineage catalog."""

    return [asdict(item) for item in _NESTED_VARIABLES]


def _mapping_copy(row: Mapping[str, object], label: str) -> dict[str, object]:
    try:
        if not isinstance(row, Mapping):
            raise CatalogValidationError(f"{label} row must be a mapping")
        return dict(row)
    except CatalogValidationError:
        raise
    except Exception as exc:
        raise CatalogValidationError(f"{label} mapping copy failed") from exc


def _candidate_rows(
    candidate: object,
    default_rows: Sequence[Mapping[str, object]],
    label: str,
) -> list[dict[str, object]]:
    source = default_rows if candidate is None else candidate
    if (
        not isinstance(source, SequenceABC)
        or isinstance(source, (str, bytes, bytearray))
    ):
        raise CatalogValidationError(f"{label} catalog must be a row sequence")
    try:
        copied: list[dict[str, object]] = []
        for index, row in enumerate(source):
            copied.append(_mapping_copy(row, f"{label}[{index}]"))
        return copied
    except CatalogValidationError:
        raise
    except Exception as exc:
        raise CatalogValidationError(f"{label} catalog iteration failed") from exc


def _require_nonempty_strings(
    row: Mapping[str, object], fields: Iterable[str], label: str
) -> None:
    for field in fields:
        value = row[field]
        if type(value) is not str or not value.strip():
            raise CatalogValidationError(
                f"{label}.{field} must be a non-empty str"
            )


def _validate_top_field_types(row: Mapping[str, object], label: str) -> None:
    _require_nonempty_strings(row, _TOP_STRING_FIELDS, label)
    if type(row["number"]) is not int:
        raise CatalogValidationError(f"{label}.number must be an exact int")
    if type(row["model_eligible"]) is not bool:
        raise CatalogValidationError(
            f"{label}.model_eligible must be an exact bool"
        )


def _validate_nested_field_types(row: Mapping[str, object], label: str) -> None:
    _require_nonempty_strings(row, _NESTED_STRING_FIELDS, label)
    for field in _NESTED_BOOL_FIELDS:
        if type(row[field]) is not bool:
            raise CatalogValidationError(f"{label}.{field} must be an exact bool")


def _normalize_lineage_registry(registry: object) -> frozenset[str]:
    if (
        not isinstance(registry, IterableABC)
        or isinstance(registry, (str, bytes, bytearray, Mapping))
    ):
        raise CatalogValidationError("lineage_registry must be an iterable of strings")
    normalized: list[str] = []
    try:
        for index, value in enumerate(registry):
            if type(value) is not str or not value.strip():
                raise CatalogValidationError(
                    f"lineage_registry[{index}] must be a non-empty str"
                )
            normalized.append(value)
    except CatalogValidationError:
        raise
    except Exception as exc:
        raise CatalogValidationError("lineage_registry iteration failed") from exc
    return frozenset(normalized)


def _reject_forbidden_fields(row: Mapping[str, object], label: str) -> None:
    try:
        forbidden = sorted(
            field
            for field in row
            if any(
                marker in field.casefold()
                for marker in _FORBIDDEN_FIELD_MARKERS
            )
        )
        if forbidden:
            raise CatalogValidationError(
                f"forbidden field in {label} catalog: {forbidden}"
            )
    except CatalogValidationError:
        raise
    except Exception as exc:
        raise CatalogValidationError(
            f"{label} forbidden-field inspection failed"
        ) from exc


def _require_string_field_keys(
    row: Mapping[object, object], label: str
) -> None:
    try:
        for field in row:
            if type(field) is not str:
                raise CatalogValidationError(
                    f"{label} field names must be exact strings"
                )
    except CatalogValidationError:
        raise
    except Exception as exc:
        raise CatalogValidationError(f"{label} field-name inspection failed") from exc


def _require_exact_schema(
    row: Mapping[str, object], expected_fields: set[str], label: str
) -> None:
    try:
        actual_fields = set(row)
        if actual_fields != expected_fields:
            missing = sorted(expected_fields - actual_fields)
            extras = sorted(actual_fields - expected_fields)
            raise CatalogValidationError(
                f"{label} schema mismatch: missing={missing}, extras={extras}"
            )
    except CatalogValidationError:
        raise
    except Exception as exc:
        raise CatalogValidationError(f"{label} schema inspection failed") from exc


def validate_catalog(
    rows: Sequence[Mapping[str, object]] | None = None,
    nested: Sequence[Mapping[str, object]] | None = None,
    lineage_registry: Iterable[str] | None = None,
) -> None:
    """Reject structural, lineage, role, alias, and model-eligibility drift."""

    top_rows = _candidate_rows(rows, subsystem_catalog(), "top-level")
    nested_rows = _candidate_rows(
        nested, nested_variable_catalog(), "nested"
    )
    registered_lineages = _normalize_lineage_registry(
        LINEAGE_REGISTRY if lineage_registry is None else lineage_registry
    )
    authoritative_lineages = frozenset(LINEAGE_REGISTRY)
    unknown_lineages = registered_lineages - authoritative_lineages
    if unknown_lineages:
        raise CatalogValidationError(
            f"unknown lineage_registry entries: {sorted(unknown_lineages)}"
        )
    missing_lineages = authoritative_lineages - registered_lineages
    if missing_lineages:
        raise CatalogValidationError(
            "unregistered lineage_group entries in lineage_registry: "
            f"{sorted(missing_lineages)}"
        )

    if len(top_rows) != 51:
        raise CatalogValidationError(f"top-level count drift: {len(top_rows)} != 51")
    required_top_fields = set(_CatalogItem.__dataclass_fields__)
    for index, row in enumerate(top_rows):
        _require_string_field_keys(row, f"top-level[{index}]")
        _reject_forbidden_fields(row, "top-level")
        _require_exact_schema(row, required_top_fields, f"top-level[{index}]")
        _validate_top_field_types(row, f"top-level[{index}]")

    formula_counts = Counter(row.get("formula") for row in top_rows)
    if formula_counts != Counter(_FORMULA_COUNTS):
        raise CatalogValidationError(
            f"formula group counts drift: {dict(formula_counts)}"
        )

    keys = [row.get("key") for row in top_rows]
    if len(set(keys)) != len(keys):
        raise CatalogValidationError("duplicate key in top-level catalog")
    formula_numbers = [
        (row.get("formula"), row.get("number")) for row in top_rows
    ]
    if len(set(formula_numbers)) != len(formula_numbers):
        raise CatalogValidationError("duplicate formula/number in top-level catalog")

    for row in top_rows:
        if row["role"] not in _ALLOWED_ROLES:
            raise CatalogValidationError(f"invalid role: {row['role']}")
        if row["role"] != "predictive_candidate" and row["model_eligible"] is not False:
            raise CatalogValidationError(
                f"non-predictive role is model eligible: {row['key']}"
            )
        if row["lineage_group"] not in registered_lineages:
            raise CatalogValidationError(
                f"unregistered lineage_group: {row['lineage_group']}"
            )
        expected_lineage = _TOP_LINEAGE_BY_KEY.get(row["key"])
        if expected_lineage is None or row["lineage_group"] != expected_lineage:
            raise CatalogValidationError(
                "top-level lineage binding drift: "
                f"{row['key']} -> {row['lineage_group']}"
            )

    for row in top_rows:
        expected_role = _FIXED_NON_MODEL_TOP.get(str(row["key"]))
        if expected_role is not None and (
            row["role"] != expected_role or row["model_eligible"] is not False
        ):
            raise CatalogValidationError(
                f"fixed non-model semantic violated: {row['key']}"
            )

    signature = tuple(
        (row["formula"], row["number"], row["key"], row["name"])
        for row in top_rows
    )
    if signature != _TOP_LEVEL_SIGNATURE:
        raise CatalogValidationError("top-level order or identity drift")

    if len(nested_rows) != 25:
        raise CatalogValidationError(f"nested count drift: {len(nested_rows)} != 25")
    required_nested_fields = set(_NestedVariable.__dataclass_fields__)
    for index, row in enumerate(nested_rows):
        _require_string_field_keys(row, f"nested[{index}]")
        _reject_forbidden_fields(row, "nested")
        _require_exact_schema(row, required_nested_fields, f"nested[{index}]")
        _validate_nested_field_types(row, f"nested[{index}]")

    for row in nested_rows:
        formula = row["formula"]
        if formula not in _NESTED_VARIABLES_BY_FORMULA:
            raise CatalogValidationError(f"unknown nested formula: {formula}")
        if row["variable"] not in _NESTED_VARIABLES_BY_FORMULA[formula]:
            raise CatalogValidationError(
                f"unknown nested variable: {formula}/{row['variable']}"
            )

    nested_pairs = [(row["formula"], row["variable"]) for row in nested_rows]
    if len(set(nested_pairs)) != len(nested_pairs):
        raise CatalogValidationError("duplicate nested formula/variable")

    top_keys = set(keys)
    top_by_key = {str(row["key"]): row for row in top_rows}
    for row in nested_rows:
        if row["parent_key"] not in top_keys:
            raise CatalogValidationError(f"missing parent key: {row['parent_key']}")
        if row["role"] not in _ALLOWED_ROLES:
            raise CatalogValidationError(f"invalid role: {row['role']}")
        if row["role"] != "predictive_candidate" and row["model_eligible"] is not False:
            raise CatalogValidationError(
                f"non-predictive role is model eligible: {row['key']}"
            )
        if row["lineage_group"] not in registered_lineages:
            raise CatalogValidationError(
                f"unregistered lineage_group: {row['lineage_group']}"
            )
        identity = (row["formula"], row["variable"])
        expected_lineage = _NESTED_LINEAGE_BY_IDENTITY.get(identity)
        if expected_lineage is None or row["lineage_group"] != expected_lineage:
            alias_context = (
                "; institution alias metadata drift"
                if row["formula"] == FORMULAS[4]
                else ""
            )
            raise CatalogValidationError(
                "nested lineage binding drift"
                f"{alias_context}: {row['formula']}/{row['variable']} "
                f"-> {row['lineage_group']}"
            )

        if row["formula"] == FORMULAS[2]:
            if row["parent_key"] != "youzi_l2_tiers":
                raise CatalogValidationError(
                    f"youzi parent drift: {row['variable']}"
                )
            expected_role = (
                "quality_gate" if row["variable"] == "X_14" else "prospective"
            )
            if row["role"] != expected_role or row["model_eligible"] is not False:
                raise CatalogValidationError(
                    f"youzi nested semantic drift: {row['variable']}"
                )

        if row["formula"] == FORMULAS[4]:
            number = int(str(row["variable"]).split("_")[1])
            expected_key = f"jigou_x{number}"
            if (
                row["key"] != expected_key
                or row["parent_key"] != expected_key
                or row["top_level_alias"] is not True
            ):
                raise CatalogValidationError(
                    f"institution alias key/parent drift: {row['variable']}"
                )
            if row["role"] != "prospective" or row["model_eligible"] is not False:
                raise CatalogValidationError(
                    f"prospective alias model eligibility drift: {row['variable']}"
                )
            top_alias = top_by_key[expected_key]
            shared_fields = (
                "formula",
                "source_expression",
                "source_field",
                "role",
                "expected_direction",
                "model_eligible",
                "lineage_group",
                "missing_policy",
            )
            mismatches = [
                field
                for field in shared_fields
                if row[field] != top_alias[field]
            ]
            if row["variable"] != top_alias["name"]:
                mismatches.append("variable/name")
            if mismatches:
                raise CatalogValidationError(
                    "institution alias metadata drift: "
                    f"{row['variable']} mismatched {sorted(mismatches)}"
                )

        if row["formula"] == FORMULAS[3]:
            if row["parent_key"] != "zj_control_degree":
                raise CatalogValidationError(
                    f"dealer parent drift: {row['variable']}"
                )
            if (
                row["contribution_key"] != "zj_control_degree"
                or row["visible_contribution"] is not False
            ):
                raise CatalogValidationError(
                    f"dealer contribution roll-up drift: {row['variable']}"
                )
            raw_candidate = row["variable"] in {"B2", "B5", "B6"}
            expected_role = "predictive_candidate" if raw_candidate else "confirmation"
            if (
                row["role"] != expected_role
                or row["model_eligible"] is not raw_candidate
            ):
                raise CatalogValidationError(
                    f"dealer nested semantic drift: {row['variable']}"
                )

        rollup = _NESTED_ROLLUP_EXPECTATIONS[(row["formula"], row["variable"])]
        rollup_fields = (
            "key",
            "parent_key",
            "top_level_alias",
            "contribution_key",
            "visible_contribution",
        )
        rollup_mismatches = [
            field
            for field in rollup_fields
            if row[field] != getattr(rollup, field)
        ]
        if rollup_mismatches:
            raise CatalogValidationError(
                "nested roll-up metadata drift: "
                f"{row['formula']}/{row['variable']} mismatched "
                f"{sorted(rollup_mismatches)}"
            )

    nested_signature = tuple(
        (row["formula"], row["variable"], row["key"], row["parent_key"])
        for row in nested_rows
    )
    if nested_signature != _NESTED_SIGNATURE:
        raise CatalogValidationError("nested order or identity drift")
