#!/usr/bin/env python3
"""PDF-strict multi-cycle A-share short-term sentiment evidence engine."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_MARKET = (
    "index_change_pct", "advancers", "decliners", "total_amount_billion",
    "amount_change_pct", "limit_up", "limit_down", "consecutive",
    "max_board", "seal_rate", "broken_board",
    "topic_top_count", "topic_count_ge3",
)
REQUIRED_SOURCES = ("tongdaxin", "duanxianxia", "lianban")
REQUIRED_PREVIOUS = ("limit_up", "limit_down", "consecutive", "seal_rate", "broken_board")
MARKET_STAGES = (
    "赚钱效应回暖",
    "赚钱效应低迷",
    "赚钱效应高潮",
    "亏钱效应出现",
    "亏钱效应炸裂",
)
SHORT_TERM_STAGES = (
    "启动期",
    "确认期",
    "发酵期",
    "加速期",
    "高潮期",
    "分歧期",
    "退潮期",
)


class SnapshotValidationError(ValueError):
    pass


def _format_metric(value: Any, precision: int = 0) -> str:
    return f"{float(value):.{precision}f}" if precision else str(int(value))


def _transition(
    label: str,
    previous: Any,
    current: Any,
    unit: str,
    *,
    precision: int = 0,
) -> str:
    previous_number = float(previous)
    current_number = float(current)
    direction = "升至" if current_number > previous_number else "降至" if current_number < previous_number else "持平于"
    return (
        f"{label}由{_format_metric(previous, precision)}{unit}{direction}"
        f"{_format_metric(current, precision)}{unit}"
    )


def _dynamic_conclusion(
    stage: str,
    market: dict[str, Any],
    previous: dict[str, Any],
    *,
    short_term: bool,
) -> str:
    transition_facts = "、".join(
        (
            _transition("涨停", previous["limit_up"], market["limit_up"], "家"),
            _transition("封板率", previous["seal_rate"], market["seal_rate"], "%", precision=1),
            _transition("炸板", previous["broken_board"], market["broken_board"], "家"),
            _transition("跌停", previous["limit_down"], market["limit_down"], "家"),
        )
    )
    ladder_fact = _transition("连板", previous["consecutive"], market["consecutive"], "只")
    prefix = f"当前短线市场情绪处于{stage}" if short_term else f"当前中级周期处于{stage}阶段"
    conclusion = f"{prefix}。{transition_facts}；{ladder_fact}。"
    return conclusion


def _reported_stage_to_pdf_stage(value: Any) -> str | None:
    label = str(value or "").strip()
    mappings = (
        (("高潮", "加速", "发酵"), "赚钱效应高潮"),
        (("分歧", "退潮初期"), "亏钱效应出现"),
        (("退潮", "冰点"), "亏钱效应炸裂"),
        (("回暖", "修复", "启动"), "赚钱效应回暖"),
        (("低迷", "混沌", "轮动"), "赚钱效应低迷"),
    )
    for tokens, stage in mappings:
        if any(token in label for token in tokens):
            return stage
    return None


def _reported_short_term_stage(value: Any) -> str | None:
    label = str(value or "").strip()
    for stage in SHORT_TERM_STAGES:
        if stage.removesuffix("期") in label:
            return stage
    return None


def determine_market_stage(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Choose one PDF five-stage conclusion without creating a sentiment score."""
    m = snapshot["market"]
    previous = snapshot["comparisons"]["previous_trading_day"]
    broad_profit = m["advancers"] > m["decliners"]
    broad_loss = m["decliners"] > m["advancers"]

    if previous:
        limit_up_rising = m["limit_up"] > previous["limit_up"]
        limit_down_rising = m["limit_down"] > previous["limit_down"]
        leader_rising = m["consecutive"] >= previous["consecutive"]
        seal_improving = m["seal_rate"] >= previous["seal_rate"]
        broken_rising = m["broken_board"] > previous["broken_board"]
        limit_down_cascade = (
            m["limit_down"] > m["limit_up"]
            and m["limit_down"] >= previous["limit_down"] * 3
        )
        severe_loss = (
            broad_loss
            and limit_down_rising
            and not leader_rising
            and not seal_improving
            and (broken_rising or limit_down_cascade)
        )
        emerging_loss = (
            leader_rising
            and (limit_down_rising or not seal_improving or broken_rising)
            and (not limit_up_rising or broad_loss)
        )
        climax = (
            broad_profit
            and limit_up_rising
            and leader_rising
            and seal_improving
            and m["limit_down"] <= previous["limit_down"]
            and m["topic_count_ge3"] >= 3
        )
        recovery = (
            (limit_up_rising or seal_improving or broad_profit)
            and not limit_down_rising
            and not broken_rising
        )
        if severe_loss:
            stage = "亏钱效应炸裂"
        elif emerging_loss:
            stage = "亏钱效应出现"
        elif climax:
            stage = "赚钱效应高潮"
        elif recovery:
            stage = "赚钱效应回暖"
        else:
            stage = "赚钱效应低迷"
        confidence = "MEDIUM"

    evidence = [
        f"上涨{m['advancers']}家、下跌{m['decliners']}家，上证日线{m['index_change_pct']:+.3f}%",
        f"涨停{m['limit_up']}家、跌停{m['limit_down']}家、连板{m['consecutive']}只、最高{m['max_board']}板",
        f"封板率{m['seal_rate']:.1f}%、炸板{m['broken_board']}家、成交额较前日{m['amount_change_pct']:+.2f}%",
        f"最强题材{m['topic_top_count']}家涨停，至少3家涨停的题材{m['topic_count_ge3']}个",
    ]
    evidence.append(
        f"前一交易日涨停{previous['limit_up']}家、跌停{previous['limit_down']}家、"
        f"连板{previous['consecutive']}只、封板率{previous['seal_rate']}%、炸板{previous['broken_board']}家"
    )
    reported = snapshot["sources"]["lianban"].get("reported_stage")
    reported_stage = _reported_stage_to_pdf_stage(reported)
    if reported:
        evidence.append(f"连板网补充标签={reported}")
    if reported_stage == stage:
        confidence = "HIGH"
    if snapshot["cross_validation"]["limit_up_difference"] != 0:
        confidence = "LOW"

    return {
        "status": "DETERMINED",
        "stage": stage,
        "confidence": confidence,
        "conclusion": _dynamic_conclusion(stage, m, previous, short_term=False),
        "evidence": evidence,
        "method": "PDF五阶段证据主导判定；不生成情绪分值或权重",
    }


def determine_short_term_stage(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Determine the current topic-led short-cycle phase from PDF evidence."""
    m = snapshot["market"]
    previous = snapshot["comparisons"]["previous_trading_day"]
    broad_profit = m["advancers"] > m["decliners"]
    broad_loss = m["decliners"] > m["advancers"]
    reported = snapshot["sources"]["lianban"].get("reported_stage")
    reported_stage = _reported_short_term_stage(reported)

    if previous:
        prior_limit_up = previous["limit_up"]
        prior_limit_down = previous["limit_down"]
        prior_consecutive = previous["consecutive"]
        prior_seal_rate = previous["seal_rate"]
        prior_broken = previous["broken_board"]
        limit_up_rising = m["limit_up"] > prior_limit_up
        limit_down_rising = m["limit_down"] > prior_limit_down
        leader_rising = m["consecutive"] >= prior_consecutive
        seal_improving = m["seal_rate"] >= prior_seal_rate
        broken_rising = m["broken_board"] > prior_broken

        if (
            broad_loss
            and (limit_down_rising or broken_rising)
            and not leader_rising
            and not seal_improving
        ):
            stage = "退潮期"
        elif (limit_down_rising or broken_rising or not seal_improving) and (
            not limit_up_rising or broad_loss
        ):
            stage = "分歧期"
        elif (
            broad_profit
            and limit_up_rising
            and leader_rising
            and seal_improving
            and m["topic_count_ge3"] >= 5
            and m["limit_up"] >= 80
            and m["seal_rate"] >= 85
        ):
            stage = "高潮期"
        elif (
            broad_profit
            and leader_rising
            and seal_improving
            and m["amount_change_pct"] > 0
            and not broken_rising
        ):
            stage = "加速期"
        elif broad_profit and limit_up_rising and m["topic_count_ge3"] >= 3:
            stage = "发酵期"
        elif (
            leader_rising
            and m["topic_count_ge3"] >= 2
            and not limit_down_rising
            and seal_improving
            and not broken_rising
        ):
            stage = "确认期"
        else:
            stage = "启动期"
        confidence = "MEDIUM"

    evidence = [
        f"上涨{m['advancers']}家、下跌{m['decliners']}家，上证日线{m['index_change_pct']:+.3f}%",
        f"涨停{m['limit_up']}家、跌停{m['limit_down']}家、连板{m['consecutive']}只、最高{m['max_board']}板",
        f"封板率{m['seal_rate']:.1f}%、炸板{m['broken_board']}家、成交额较前日{m['amount_change_pct']:+.2f}%",
        f"最强题材{m['topic_top_count']}家涨停，至少3家涨停的题材{m['topic_count_ge3']}个",
    ]
    evidence.append(
        f"前一交易日涨停{previous['limit_up']}家、跌停{previous['limit_down']}家、"
        f"连板{previous['consecutive']}只、封板率{previous['seal_rate']}%、炸板{previous['broken_board']}家"
    )
    if reported:
        evidence.append(f"连板网补充标签={reported}")
    if reported_stage == stage:
        confidence = "HIGH"
    if snapshot["cross_validation"]["limit_up_difference"] != 0:
        confidence = "LOW"
    return {
        "status": "DETERMINED",
        "stage": stage,
        "confidence": confidence,
        "conclusion": _dynamic_conclusion(stage, m, previous, short_term=True),
        "evidence": evidence,
        "method": "PDF题材情绪小周期证据主导判定；不生成情绪分值或权重",
    }


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    if not isinstance(snapshot, dict) or not snapshot.get("trading_date"):
        raise SnapshotValidationError("missing:trading_date")
    market = snapshot.get("market")
    if not isinstance(market, dict):
        raise SnapshotValidationError("missing:market")
    missing = [key for key in REQUIRED_MARKET if key not in market or market[key] is None]
    if missing:
        raise SnapshotValidationError("missing_market_fields:" + ",".join(missing))
    comparisons = snapshot.get("comparisons")
    if not isinstance(comparisons, dict):
        raise SnapshotValidationError("missing:comparisons")
    previous = comparisons.get("previous_trading_day")
    if not isinstance(previous, dict):
        raise SnapshotValidationError("missing:previous_trading_day")
    previous_missing = [key for key in REQUIRED_PREVIOUS if previous.get(key) is None]
    if previous_missing:
        raise SnapshotValidationError("missing_previous_metrics:" + ",".join(previous_missing))
    cross_validation = snapshot.get("cross_validation")
    if not isinstance(cross_validation, dict) or cross_validation.get("limit_up_difference") is None:
        raise SnapshotValidationError("missing_cross_validation:limit_up_difference")
    sources = snapshot.get("sources")
    if not isinstance(sources, dict):
        raise SnapshotValidationError("missing:sources")
    source_missing = [name for name in REQUIRED_SOURCES if name not in sources]
    if source_missing:
        raise SnapshotValidationError("missing_sources:" + ",".join(source_missing))
    dates = set()
    for name in REQUIRED_SOURCES:
        source = sources[name]
        if not isinstance(source, dict) or source.get("verified") is not True:
            raise SnapshotValidationError(f"source_not_verified:{name}")
        dates.add(str(source.get("trading_date", "")))
    if dates != {str(snapshot["trading_date"])}:
        raise SnapshotValidationError("source_date_mismatch:" + ",".join(sorted(dates)))


def analyze_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    validate_snapshot(snapshot)
    m = snapshot["market"]
    stage_conclusion = determine_market_stage(snapshot)
    short_stage_conclusion = determine_short_term_stage(snapshot)
    previous = snapshot["comparisons"]["previous_trading_day"]
    topics = snapshot.get("topics", [])
    topic_names = [str(row.get("name", "")) for row in topics[:4] if isinstance(row, dict)]
    topic_text = "、".join(name for name in topic_names if name) or "无可用题材名称"
    leader_relation = "仅有当日截面，禁止判定龙头周期阶段"
    profit_loss_relation = "仅有当日截面，禁止判定中级赚钱/亏钱周期阶段"
    relation_status = "OBSERVATION_ONLY"
    if previous:
        relation_status = "RELATION_DETERMINED"
        leader_relation = (
            f"连板由{previous['consecutive']}只变为{m['consecutive']}只；"
            f"当日最高{m['max_board']}板。只确认梯队变化，不据此强制命名周期阶段"
        )
        profit_loss_relation = (
            f"涨停由{previous['limit_up']}家变为{m['limit_up']}家，"
            f"跌停由{previous['limit_down']}家变为{m['limit_down']}家，"
            f"连板由{previous['consecutive']}家变为{m['consecutive']}家，"
            f"封板率由{previous['seal_rate']}%变为{m['seal_rate']:.1f}%。"
            "这些事实说明赚钱与亏钱效应并存，不能压缩为单一强弱分数"
        )

    cycles = {
        "index_cycle": {
            "stage_status": "INSUFFICIENT_EVIDENCE",
            "judgement": "只确认上证日线与市场宽度，禁止判定指数周期阶段",
            "observations": [
                f"上证日线{m['index_change_pct']:+.3f}%",
                f"上涨{m['advancers']}家、下跌{m['decliners']}家",
            ],
            "evidence_limit": "缺少PDF要求的上证加权、上证非加权、创业板加权、创业板非加权、上证50五类指数分时及其背离/共振",
        },
        "theme_cycle": {
            "stage_status": "DETERMINED",
            "judgement": short_stage_conclusion["conclusion"],
            "observations": short_stage_conclusion["evidence"],
            "evidence_limit": "明确短线阶段是当次市场生态结论；具体题材内部的启动、确认和龙头关系仍受连续序列完整度限制",
        },
        "leader_cycle": {
            "stage_status": relation_status,
            "judgement": leader_relation,
            "observations": [f"最高{m['max_board']}板", f"连板{m['consecutive']}只"],
            "evidence_limit": "缺少核心龙头逐日结构、辨识度、换手、分歧、反包和补涨接力完整序列",
        },
        "profit_loss_cycle": {
            "stage_status": relation_status,
            "judgement": profit_loss_relation,
            "observations": [
                f"涨停{m['limit_up']}家、跌停{m['limit_down']}家",
                f"封板率{m['seal_rate']:.1f}%、炸板{m['broken_board']}家",
                f"成交额{m['total_amount_billion']:.1f}亿元，较前日{m['amount_change_pct']:+.2f}%",
            ],
            "evidence_limit": "可确认相邻交易日方向变化；不足以替代完整中级周期序列",
        },
        "intermediate_cycle": {
            "stage_status": "DETERMINED",
            "judgement": stage_conclusion["conclusion"],
            "observations": stage_conclusion["evidence"],
            "evidence_limit": "明确阶段是当次证据主导结论；子周期错位和反证仍须保留，不能据此生成情绪分值",
        },
    }

    short_stage_conflicts: list[str] = []
    intermediate_stage_conflicts: list[str] = []
    lianban_stage = snapshot["sources"]["lianban"].get("reported_stage")
    mapped_short_stage = _reported_short_term_stage(lianban_stage)
    if (
        lianban_stage
        and mapped_short_stage is not None
        and mapped_short_stage != short_stage_conclusion["stage"]
    ):
        short_stage_conflicts.append(
            f"连板网标签={lianban_stage}，与内部短线阶段={short_stage_conclusion['stage']}不一致；"
            "仅作补充观察"
        )
    mapped_intermediate_stage = _reported_stage_to_pdf_stage(lianban_stage)
    if (
        lianban_stage
        and mapped_intermediate_stage is not None
        and mapped_intermediate_stage != stage_conclusion["stage"]
    ):
        intermediate_stage_conflicts.append(
            f"连板网标签={lianban_stage}，映射后与内部中级周期阶段={stage_conclusion['stage']}不一致；"
            "仅作补充观察"
        )
    cross = snapshot.get("cross_validation", {})
    if cross["limit_up_difference"] != 0:
        source_conflict = f"短线侠与连板网涨停数差异={cross['limit_up_difference']}"
        short_stage_conflicts.append(source_conflict)
        intermediate_stage_conflicts.append(source_conflict)

    short_stage_conclusion["conflicts"] = short_stage_conflicts
    short_stage_conclusion["conflict_statement"] = (
        "；".join(short_stage_conflicts)
        if short_stage_conflicts
        else "未发现足以改变短线情绪阶段判定的直接冲突。"
    )
    stage_conclusion["conflicts"] = intermediate_stage_conflicts
    stage_conclusion["conflict_statement"] = (
        "；".join(intermediate_stage_conflicts)
        if intermediate_stage_conflicts
        else "未发现足以改变中级周期阶段判定的直接冲突。"
    )
    conflicts = list(dict.fromkeys(short_stage_conflicts + intermediate_stage_conflicts))

    return {
        "schema": "SHORT_TERM_MARKET_SENTIMENT_PDF_STRICT_V1",
        "status": "CLEAN_PASS",
        "trading_date": snapshot["trading_date"],
        "analysis_mode": "pdf_strict_multi_cycle",
        "single_stage_conclusion": stage_conclusion,
        "short_term_stage_conclusion": short_stage_conclusion,
        "cycles": cycles,
        "observed_relationship": (
            f"当日题材聚集（{topic_text}）与上涨/下跌{m['advancers']}/{m['decliners']}、"
            f"成交额环比{m['amount_change_pct']:+.2f}%及连板{m['consecutive']}只同时存在；"
            f"短线情绪阶段为{short_stage_conclusion['stage']}，中级周期阶段为"
            f"{stage_conclusion['stage']}，同时保留各周期错位和反证"
        ),
        "conflicts": conflicts,
        "evidence_limits": [row["evidence_limit"] for row in cycles.values()],
        "risk_boundary": [
            f"当日炸板{m['broken_board']}家、跌停{m['limit_down']}家",
            f"成交额较前日{m['amount_change_pct']:+.2f}%",
            "缺少五类指数分时和完整多日周期序列时，不得把局部题材聚集外推为全市场发酵或偏强",
            "市场结构研判不构成个股推荐、收益保证或自动交易指令",
        ],
        "sources": snapshot["sources"],
    }


def example_snapshot(name: str) -> dict[str, Any]:
    rows = {
        "strong": dict(index_change_pct=1.8, advancers=4200, decliners=900, total_amount_billion=23000, amount_change_pct=18, limit_up=115, limit_down=2, consecutive=32, max_board=8, seal_rate=91, broken_board=8, topic_top_count=18, topic_count_ge3=9),
        "mixed": dict(index_change_pct=0.0, advancers=2550, decliners=2550, total_amount_billion=12000, amount_change_pct=0, limit_up=45, limit_down=12, consecutive=10, max_board=4, seal_rate=68, broken_board=20, topic_top_count=7, topic_count_ge3=3),
        "retreat": dict(index_change_pct=-2.0, advancers=650, decliners=4450, total_amount_billion=8000, amount_change_pct=-18, limit_up=22, limit_down=24, consecutive=3, max_board=2, seal_rate=42, broken_board=36, topic_top_count=3, topic_count_ge3=1),
    }
    market = rows[name]
    previous_rows = {
        "strong": dict(limit_up=80, limit_down=4, consecutive=20, seal_rate=80, broken_board=15),
        "mixed": dict(limit_up=50, limit_down=12, consecutive=12, seal_rate=70, broken_board=20),
        "retreat": dict(limit_up=30, limit_down=10, consecutive=8, seal_rate=60, broken_board=20),
    }
    date = "2026-08-14"
    return {
        "trading_date": date,
        "market": market,
        "topics": [],
        "sources": {
            key: {"verified": True, "trading_date": date}
            for key in REQUIRED_SOURCES
        },
        "cross_validation": {"limit_up_difference": 0},
        "comparisons": {"previous_trading_day": previous_rows[name]},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", nargs="?")
    parser.add_argument("--example", choices=("strong", "mixed", "retreat"))
    args = parser.parse_args()
    snapshot = example_snapshot(args.example) if args.example else json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    print(json.dumps(analyze_snapshot(snapshot), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
