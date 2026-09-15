#!/usr/bin/env python3
"""Build and persist the mandatory six-part five-theory delivery conclusion.

This module formats already-computed scientific-engine evidence.  It does not
recalculate theory signals and it never upgrades structural observations into
an empirical predictive-edge claim.
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any


SCHEMA = "UNIFIED_FIVE_THEORY_CONCLUSION_V1"
DELIVERY_SECTIONS = ["波浪理论", "缠论", "斐波那契", "江恩理论", "威科夫", "综合结论"]
REQUIRED_SUBSYSTEMS = ("elliott_wave", "chan_structure", "fibonacci", "gann", "wyckoff")


class UnifiedConclusionError(RuntimeError):
    """Raised when a report cannot satisfy the mandatory delivery contract."""


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _display_number(value: Any) -> str:
    number = _finite_number(value)
    if number is None:
        return "无可靠数值"
    return f"{number:.4f}".rstrip("0").rstrip(".")


def _zone_text(zone: Any) -> str:
    if not isinstance(zone, dict):
        return "未形成合格区间"
    lower = _display_number(zone.get("lower"))
    upper = _display_number(zone.get("upper"))
    center = _display_number(zone.get("center"))
    return f"{lower}—{upper}（中心{center}）"


def _price_text(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("price")
    return _display_number(value)


def _required_subsystems(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if report.get("status") != "PASS":
        raise UnifiedConclusionError(f"report_status_not_pass:{report.get('status')}")
    raw = report.get("theory_subsystems")
    if not isinstance(raw, dict):
        raise UnifiedConclusionError("theory_subsystems_missing")
    validated: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_SUBSYSTEMS:
        subsystem = raw.get(name)
        if not isinstance(subsystem, dict):
            raise UnifiedConclusionError(f"subsystem_missing:{name}")
        if subsystem.get("status") != "PASS":
            raise UnifiedConclusionError(f"subsystem_status_not_pass:{name}:{subsystem.get('status')}")
        if subsystem.get("active_in_main_chain") is not True:
            raise UnifiedConclusionError(f"subsystem_not_active_in_main_chain:{name}")
        for field in ("candidate_levels", "limitations"):
            if not isinstance(subsystem.get(field), list):
                raise UnifiedConclusionError(f"subsystem_field_missing:{name}:{field}")
        validated[name] = subsystem
    return validated


def _require_full_tdx_history(report: dict[str, Any], subsystems: dict[str, dict[str, Any]]) -> None:
    source = report.get("data_provenance")
    if not isinstance(source, dict) or source.get("source_type") != "tdx_local_hub":
        return
    returned = source.get("records_returned")
    available = source.get("source_records_available")
    if (
        source.get("history_scope") != "FULL_LOCAL_TDX_FILE"
        or source.get("full_history_required") is not True
        or source.get("full_history_verified") is not True
        or not isinstance(returned, int)
        or not isinstance(available, int)
        or returned != available
    ):
        raise UnifiedConclusionError(
            f"tdx_full_history_not_verified:returned={returned}:available={available}"
        )
    elliott = subsystems["elliott_wave"]
    if (
        elliott.get("input_bar_count") != returned
        or elliott.get("search_scope") != "ALL_CONFIRMED_ALTERNATING_PIVOTS"
    ):
        raise UnifiedConclusionError(
            "elliott_full_history_not_verified:"
            f"elliott_bars={elliott.get('input_bar_count')}:source_bars={returned}:"
            f"scope={elliott.get('search_scope')}"
        )


def _elliott_section(subsystem: dict[str, Any]) -> dict[str, Any]:
    direction = str(subsystem.get("direction", "unclear")).lower()
    trend = {"up": "UP_STRUCTURE", "down": "DOWN_STRUCTURE"}.get(direction, "UNCLEAR_STRUCTURE")
    state = subsystem.get("structure_state")
    rules = subsystem.get("rule_validation")
    wave_points = subsystem.get("wave_points")
    complete = (
        state == "complete_impulse"
        and isinstance(rules, dict)
        and len(rules) >= 5
        and all(value is True for value in rules.values())
        and isinstance(wave_points, list)
        and len(wave_points) >= 6
        and all(isinstance(point, dict) and point.get("confirmed") is True for point in wave_points[-6:])
    )
    if complete:
        wave_number = 5
        confirmed = "CONFIRMED_IMPULSE_WAVE_5_COMPLETE"
        explanation = "已确认一组完整推动浪并完成第5浪；后续发展浪尚无右侧确认，不能预先编号。"
    else:
        wave_number = None
        confirmed = "UNRESOLVED_NO_COMPLETE_IMPULSE"
        explanation = "尚未形成全部规则通过的完整推动浪，当前不能可靠标注为第1至第5浪。"
    return {
        "status": "PASS",
        "wave_number": wave_number,
        "confirmed_wave_position": confirmed,
        "developing_wave_position": "UNRESOLVED_REQUIRES_RIGHT_CONFIRMATION",
        "trend": trend,
        "structure_state": state,
        "direction": direction,
        "rule_validation": rules if isinstance(rules, dict) else {},
        "input_bar_count": subsystem.get("input_bar_count"),
        "search_scope": subsystem.get("search_scope"),
        "confirmed_pivot_count": subsystem.get("confirmed_pivot_count"),
        "candidate_window_count": subsystem.get("candidate_window_count"),
        "conclusion_cn": f"{explanation} 已确认枢轴结构趋势为{ {'UP_STRUCTURE': '上行', 'DOWN_STRUCTURE': '下行'}.get(trend, '不明') }。",
    }


def _chan_section(subsystem: dict[str, Any], close: float) -> dict[str, Any]:
    zones = subsystem.get("central_zones")
    strokes = subsystem.get("strokes")
    latest_zone = zones[-1] if isinstance(zones, list) and zones else None
    latest_stroke = strokes[-1] if isinstance(strokes, list) and strokes else None
    direction = latest_stroke.get("direction") if isinstance(latest_stroke, dict) else None
    if isinstance(latest_zone, dict):
        lower = _finite_number(latest_zone.get("lower"))
        upper = _finite_number(latest_zone.get("upper"))
        if lower is None or upper is None or upper <= lower:
            raise UnifiedConclusionError("chan_latest_central_zone_invalid")
        if lower <= close <= upper:
            trend = "IN_CENTRAL_ZONE"
        elif close > upper and direction == "up":
            trend = "UP_STROKE_ABOVE_CENTRAL_ZONE"
        elif close < lower and direction == "down":
            trend = "DOWN_STROKE_BELOW_CENTRAL_ZONE"
        elif close > upper:
            trend = "ABOVE_CENTRAL_ZONE_WITHOUT_UP_STROKE_CONFIRMATION"
        else:
            trend = "BELOW_CENTRAL_ZONE_WITHOUT_DOWN_STROKE_CONFIRMATION"
        zone_state = "CONFIRMED_CENTRAL_ZONE_PRESENT"
        zone_cn = _zone_text({"lower": lower, "upper": upper, "center": (lower + upper) / 2.0})
    else:
        trend = {
            "up": "UP_STROKE_NO_CONFIRMED_CENTRAL_ZONE",
            "down": "DOWN_STROKE_NO_CONFIRMED_CENTRAL_ZONE",
        }.get(direction, "NO_CONFIRMED_STROKE_OR_CENTRAL_ZONE")
        zone_state = "NO_CONFIRMED_CENTRAL_ZONE"
        zone_cn = "尚无确认中枢"
    return {
        "status": "PASS",
        "central_zone_state": zone_state,
        "latest_central_zone": latest_zone,
        "last_stroke_direction": direction,
        "trend": trend,
        "buy_sell_state": subsystem.get("buy_sell_state"),
        "conclusion_cn": f"最新中枢为{zone_cn}；最后一笔方向为{direction or '未确认'}，结构趋势状态为{trend}。",
    }


def _fibonacci_levels(subsystem: dict[str, Any]) -> list[float]:
    clusters = subsystem.get("confluence_clusters")
    levels = [
        number
        for cluster in clusters if isinstance(cluster, dict)
        if (number := _finite_number(cluster.get("center"))) is not None
    ] if isinstance(clusters, list) else []
    if not levels:
        candidates = subsystem.get("candidate_levels")
        levels = [
            number
            for item in candidates if isinstance(item, dict)
            if (number := _finite_number(item.get("level"))) is not None
        ] if isinstance(candidates, list) else []
    return sorted(set(levels))


def _fibonacci_section(subsystem: dict[str, Any], close: float) -> dict[str, Any]:
    levels = _fibonacci_levels(subsystem)
    supports = sorted((level for level in levels if level < close), reverse=True)[:3]
    resistances = sorted(level for level in levels if level > close)[:3]
    at_price = [level for level in levels if level == close]
    active_swing = subsystem.get("active_swing") if isinstance(subsystem.get("active_swing"), dict) else None
    return {
        "status": "PASS",
        "active_swing": active_swing,
        "nearest_support_positions": supports,
        "nearest_resistance_positions": resistances,
        "at_current_price_positions": at_price,
        "level_source": "confluence_clusters" if subsystem.get("confluence_clusters") else "candidate_levels",
        "conclusion_cn": (
            f"活动摆动方向为{(active_swing or {}).get('direction', '未确认')}；"
            f"最近支撑参考为{', '.join(_display_number(value) for value in supports) or '未形成'}；"
            f"最近压力参考为{', '.join(_display_number(value) for value in resistances) or '未形成'}。"
        ),
    }


def _gann_section(subsystem: dict[str, Any]) -> dict[str, Any]:
    cycles = subsystem.get("time_cycles")
    if not isinstance(cycles, list):
        raise UnifiedConclusionError("gann_time_cycles_missing")
    near = sorted({
        int(cycle["length"])
        for cycle in cycles
        if isinstance(cycle, dict) and cycle.get("near_turn_window") is True and _finite_number(cycle.get("length")) is not None
    })
    upcoming = [
        int(number)
        for cycle in cycles if isinstance(cycle, dict)
        if (number := _finite_number(cycle.get("bars_to_next"))) is not None and number >= 0
    ]
    next_bars = min(upcoming) if upcoming else None
    state = "NEAR_TIME_WINDOW" if near else "NO_NEAR_TIME_WINDOW"
    if near:
        detail = f"正处于{', '.join(str(value) for value in near)}交易日周期的±2交易日接近窗口"
    else:
        detail = f"未处于预设周期接近窗口，最近窗口约{next_bars}个交易日后" if next_bars is not None else "没有可计算的近期窗口"
    return {
        "status": "PASS",
        "time_window_state": state,
        "near_cycle_lengths": near,
        "next_window_bars": next_bars,
        "anchor": subsystem.get("anchor"),
        "trend_slope_atr_per_bar": subsystem.get("trend_slope_atr_per_bar"),
        "turning_point_claimed": False,
        "conclusion_cn": f"{detail}；这只是时间接近度，不等于已确认转折点。",
    }


def _wyckoff_section(subsystem: dict[str, Any], close: float) -> dict[str, Any]:
    trading_range = subsystem.get("trading_range")
    if not isinstance(trading_range, dict):
        raise UnifiedConclusionError("wyckoff_trading_range_missing")
    lower = _finite_number(trading_range.get("lower"))
    upper = _finite_number(trading_range.get("upper"))
    midpoint = _finite_number(trading_range.get("midpoint"))
    if lower is None or upper is None or midpoint is None or not lower < upper:
        raise UnifiedConclusionError("wyckoff_trading_range_invalid")
    if close < lower:
        position = "BELOW_TRADING_RANGE"
    elif close > upper:
        position = "ABOVE_TRADING_RANGE"
    elif close >= midpoint:
        position = "ABOVE_RANGE_MIDPOINT"
    else:
        position = "BELOW_RANGE_MIDPOINT"
    events = subsystem.get("events")
    latest_accepted = next(
        (event for event in reversed(events) if isinstance(event, dict) and event.get("accepted") is True),
        None,
    ) if isinstance(events, list) else None
    phase = str(subsystem.get("phase") or "undetermined_range")
    event_cn = "无已确认事件" if latest_accepted is None else (
        f"最近确认事件为{latest_accepted.get('type')}（{latest_accepted.get('date', '日期未知')}）"
    )
    return {
        "status": "PASS",
        "phase": phase,
        "trading_range": trading_range,
        "range_position": position,
        "latest_accepted_event": latest_accepted,
        "conditions": subsystem.get("conditions") if isinstance(subsystem.get("conditions"), dict) else {},
        "conclusion_cn": f"当前运行阶段为{phase}，价格位于{position}；{event_cn}。",
    }


def _integrated_section(
    report: dict[str, Any],
    elliott: dict[str, Any],
    chan: dict[str, Any],
    fibonacci: dict[str, Any],
    gann: dict[str, Any],
    wyckoff: dict[str, Any],
) -> dict[str, Any]:
    technical = report.get("technical_context")
    conclusion = report.get("conclusion")
    validation = report.get("walk_forward_validation")
    if not isinstance(technical, dict) or not isinstance(conclusion, dict) or not isinstance(validation, dict):
        raise UnifiedConclusionError("technical_conclusion_or_validation_missing")
    close = _finite_number(technical.get("close"))
    ema20 = _finite_number(technical.get("ema20"))
    macd_histogram = _finite_number(technical.get("macd_histogram"))
    bullish = (
        close is not None and ema20 is not None and close > ema20
        and macd_histogram is not None and macd_histogram > 0
        and str(chan.get("trend", "")).startswith("UP_STROKE")
        and wyckoff.get("range_position") in {"ABOVE_RANGE_MIDPOINT", "ABOVE_TRADING_RANGE"}
    )
    bearish = (
        close is not None and ema20 is not None and close < ema20
        and macd_histogram is not None and macd_histogram < 0
        and str(chan.get("trend", "")).startswith("DOWN_STROKE")
        and wyckoff.get("range_position") in {"BELOW_RANGE_MIDPOINT", "BELOW_TRADING_RANGE"}
    )
    if bullish:
        structural_bias = "STRUCTURAL_RECOVERY_NOT_TREND_CONFIRMED"
        bias_cn = "结构性修复占优，但尚未确认趋势性上行"
    elif bearish:
        structural_bias = "STRUCTURAL_WEAKNESS_NOT_TREND_CONFIRMED"
        bias_cn = "结构性走弱占优，但尚未确认趋势性下行"
    else:
        structural_bias = "MIXED_RANGE_STRUCTURE_NO_DIRECTIONAL_CONFIRMATION"
        bias_cn = "多方法结构信号混合，维持区间或过渡判断，方向未确认"
    gate = validation.get("global_cross_sectional_gate")
    predictive_allowed = bool(gate.get("predictive_claim_allowed")) if isinstance(gate, dict) else False
    support = conclusion.get("primary_support_zone")
    resistance = conclusion.get("primary_resistance_zone")
    breakout = conclusion.get("breakout_trigger")
    breakdown = conclusion.get("breakdown_trigger")
    invalidation = conclusion.get("support_scenario_invalidation")
    conflicts: list[str] = []
    if elliott.get("trend") == "DOWN_STRUCTURE" and str(chan.get("trend", "")).startswith("UP"):
        conflicts.append("ELLIOTT_DOWN_VS_CHAN_UP")
    if elliott.get("trend") == "UP_STRUCTURE" and str(chan.get("trend", "")).startswith("DOWN"):
        conflicts.append("ELLIOTT_UP_VS_CHAN_DOWN")
    clear = (
        f"五套子系统已全部运行并逐项通过。综合判断：{bias_cn}。"
        f"主支撑候选区{_zone_text(support)}，主压力候选区{_zone_text(resistance)}；"
        f"向上需日线确认突破{_price_text(breakout)}，向下风险线为{_price_text(breakdown)}，"
        f"支撑情景失效线为{_price_text(invalidation)}。"
        f"当前结论仍为{conclusion.get('state', 'UNKNOWN')}，方向预测为{conclusion.get('directional_prediction', 'NOT_CLAIMED')}；"
        "五法共享同一形式化理论证据家族，不作五票独立共振计数。"
    )
    return {
        "status": "PASS",
        "structural_bias": structural_bias,
        "trend_confirmation": "NOT_CONFIRMED" if not predictive_allowed else "STRUCTURAL_ONLY_PREDICTIVE_GATE_SEPARATELY_ALLOWED",
        "primary_support_zone": support,
        "primary_resistance_zone": resistance,
        "breakout_trigger": breakout,
        "breakdown_trigger": breakdown,
        "support_scenario_invalidation": invalidation,
        "predictive_claim_allowed": predictive_allowed,
        "output_state": conclusion.get("state"),
        "directional_prediction": conclusion.get("directional_prediction"),
        "confidence_cap": conclusion.get("confidence_cap"),
        "cross_theory_conflicts": conflicts,
        "evidence_family_policy": "FIVE_THEORIES_ARE_ONE_FORMALIZED_THEORY_EVIDENCE_FAMILY_NOT_FIVE_INDEPENDENT_VOTES",
        "clear_conclusion_cn": clear,
    }


def build_unified_conclusion(report: dict[str, Any]) -> dict[str, Any]:
    """Return a fail-closed, six-part conclusion built from all five subsystems."""
    if not isinstance(report, dict):
        raise UnifiedConclusionError("report_not_object")
    subsystems = _required_subsystems(report)
    _require_full_tdx_history(report, subsystems)
    technical = report.get("technical_context")
    close = _finite_number(technical.get("close")) if isinstance(technical, dict) else None
    if close is None or close <= 0:
        raise UnifiedConclusionError("technical_close_invalid")
    elliott = _elliott_section(subsystems["elliott_wave"])
    chan = _chan_section(subsystems["chan_structure"], close)
    fibonacci = _fibonacci_section(subsystems["fibonacci"], close)
    gann = _gann_section(subsystems["gann"])
    wyckoff = _wyckoff_section(subsystems["wyckoff"], close)
    integrated = _integrated_section(report, elliott, chan, fibonacci, gann, wyckoff)
    formatted = "\n".join(
        (
            f"1. 波浪理论：{elliott['conclusion_cn']}",
            f"2. 缠论：{chan['conclusion_cn']}",
            f"3. 斐波那契：{fibonacci['conclusion_cn']}",
            f"4. 江恩理论：{gann['conclusion_cn']}",
            f"5. 威科夫：{wyckoff['conclusion_cn']}",
            f"6. 综合结论：{integrated['clear_conclusion_cn']}",
        )
    )
    result = {
        "schema": SCHEMA,
        "status": "PASS",
        "all_subsystems_used": True,
        "delivery_sections": DELIVERY_SECTIONS,
        "subsystem_statuses": {name: "PASS" for name in REQUIRED_SUBSYSTEMS},
        "elliott_wave": elliott,
        "chan_structure": chan,
        "fibonacci": fibonacci,
        "gann": gann,
        "wyckoff": wyckoff,
        "integrated_conclusion": integrated,
        "formatted_conclusion_cn": formatted,
    }
    cursor = -1
    for index, heading in enumerate(("1. 波浪理论：", "2. 缠论：", "3. 斐波那契：", "4. 江恩理论：", "5. 威科夫：", "6. 综合结论："), start=1):
        found = formatted.find(heading)
        if found <= cursor:
            raise UnifiedConclusionError(f"delivery_heading_missing_or_out_of_order:{index}")
        cursor = found
    return result


def _temporary_json_path(path: Path) -> Path:
    token = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:8]
    return path.with_name(f".{token}.tmp")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_json_path(path)
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def enrich_analysis_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Enrich every PASS target report and refresh its artifact binding."""
    if not isinstance(summary, dict) or summary.get("status") != "PASS":
        raise UnifiedConclusionError(f"analysis_summary_not_pass:{getattr(summary, 'get', lambda *_: None)('status')}")
    items = summary.get("items")
    if not isinstance(items, list) or not items:
        raise UnifiedConclusionError("analysis_summary_items_missing")
    enriched = copy.deepcopy(summary)
    for item in enriched["items"]:
        if not isinstance(item, dict) or item.get("status") != "PASS":
            raise UnifiedConclusionError("analysis_item_not_pass")
        artifact = item.get("artifact")
        if not isinstance(artifact, dict) or not artifact.get("path"):
            raise UnifiedConclusionError("analysis_item_artifact_missing")
        report_path = Path(str(artifact["path"]))
        if not report_path.is_file():
            raise UnifiedConclusionError(f"analysis_report_missing:{report_path}")
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise UnifiedConclusionError(f"analysis_report_read_error:{type(exc).__name__}:{exc}") from exc
        if report.get("symbol") != item.get("symbol"):
            raise UnifiedConclusionError(f"analysis_report_symbol_mismatch:{item.get('symbol')}:{report.get('symbol')}")
        unified = build_unified_conclusion(report)
        report["unified_five_theory_conclusion"] = unified
        _write_json(report_path, report)
        readback = json.loads(report_path.read_text(encoding="utf-8"))
        readback_unified = readback.get("unified_five_theory_conclusion")
        if not isinstance(readback_unified, dict) or readback_unified.get("schema") != SCHEMA or readback_unified.get("status") != "PASS":
            raise UnifiedConclusionError(f"unified_report_readback_failed:{report_path}")
        artifact.update(
            {
                "size": report_path.stat().st_size,
                "sha256": _sha256(report_path),
                "readback_status": readback.get("status"),
            }
        )
        item["unified_five_theory_conclusion_status"] = "PASS"
        item["unified_five_theory_conclusion_schema"] = SCHEMA
        item["unified_five_theory_conclusion"] = {
            "elliott_wave_position": unified["elliott_wave"]["confirmed_wave_position"],
            "elliott_wave_number": unified["elliott_wave"]["wave_number"],
            "elliott_trend": unified["elliott_wave"]["trend"],
            "chan_trend": unified["chan_structure"]["trend"],
            "fibonacci_support_positions": unified["fibonacci"]["nearest_support_positions"],
            "fibonacci_resistance_positions": unified["fibonacci"]["nearest_resistance_positions"],
            "gann_time_window_state": unified["gann"]["time_window_state"],
            "wyckoff_phase": unified["wyckoff"]["phase"],
            "structural_bias": unified["integrated_conclusion"]["structural_bias"],
            "formatted_conclusion_cn": unified["formatted_conclusion_cn"],
        }
    enriched["unified_delivery_schema"] = SCHEMA
    enriched["unified_delivery_status"] = "PASS"
    enriched["unified_delivery_item_count"] = len(enriched["items"])
    return enriched


def persist_enriched_summary(summary: dict[str, Any], summary_path: str | Path) -> dict[str, Any]:
    """Persist the enriched summary and return a non-self-referential artifact receipt."""
    path = Path(summary_path)
    disk_payload = copy.deepcopy(summary)
    disk_payload.pop("summary_artifact", None)
    _write_json(path, disk_payload)
    readback = json.loads(path.read_text(encoding="utf-8"))
    if readback.get("status") != "PASS" or readback.get("unified_delivery_status") != "PASS":
        raise UnifiedConclusionError(f"enriched_summary_readback_failed:{path}")
    final = copy.deepcopy(disk_payload)
    final["summary_artifact"] = {
        "path": str(path),
        "size": path.stat().st_size,
        "sha256": _sha256(path),
        "readback_status": readback.get("status"),
    }
    return final
