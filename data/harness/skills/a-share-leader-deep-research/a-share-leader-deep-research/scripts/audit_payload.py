from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import math
import re
from datetime import datetime, time
from pathlib import Path
from typing import Any

from logic_analysis import clock_seconds, stock_theme_clusters


WORKFLOW_NAME = "龙头深度研究"
SCHEMA_VERSION = "3.2"
MORNING_END = time(11, 30)
LHB_THRESHOLD = 100_000_000.0
BANNED_CONCEPTS = {"其他", "其它", "综合", "综合概念", "未分类", "待定", "未知"}
ALLOWED_INVESTMENT_BOARDS = {
    "大消费", "医药生物", "大科技", "高端制造", "新能源",
    "基建公用", "金融地产", "周期资源",
}
BANNED_CLAIMS = {
    "沿用上期", "维持原判断", "默认结论", "固定结论", "兜底判断",
    "按本投资板块内带动、连板高度和封板质量比较列龙",
    "有望", "预计", "大概率", "建议关注", "后市可期", "值得关注",
    "反证", "停止生成", "代码差集", "逐只同池", "逐只对账",
    "双源逐只", "东方财富与短线侠", "差异处理",
    "本轮抓取", "来源组", "本地旁证", "本地通达信状态",
    "未达到1亿元", "缺少席位明细", "若任一来源", "若任一股票",
    "主催化", "共同催化", "催化结构由",
    "证据完整度", "逻辑证据完整度",
    "扩散节点", "盘中扩散", "扩散先锋", "主线锚",
}
LOGIC_CONNECTORS = {
    "共同机制", "覆盖", "机制锚", "高度锚", "时序", "共振", "因果",
}
STATISTICS_ONLY_LOGIC = re.compile(
    r"^.+共有\d+只涨停[，,；;].*连板\d+只.*10:00前.*零开板\d+只.*最高"
)


class PayloadAuditError(ValueError):
    pass


def need(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def parse_date(value: Any, field: str, errors: list[str]) -> str:
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date().isoformat()
    except Exception:
        errors.append(f"{field} 必须是 YYYY-MM-DD")
        return ""


def parse_iso(value: Any, field: str, errors: list[str]) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("missing timezone")
        return parsed
    except Exception:
        errors.append(f"{field} 必须是带时区时间")
        return None


def parse_clock(value: Any, field: str, errors: list[str]) -> time | None:
    try:
        return datetime.strptime(str(value), "%H:%M:%S").time()
    except Exception:
        errors.append(f"{field} 必须是 HH:MM:SS")
        return None


def finite_number(value: Any, field: str, errors: list[str]) -> float | None:
    try:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("not finite")
        return result
    except Exception:
        errors.append(f"{field} 必须是有限数字")
        return None


def sequential_ranks(items: list[dict[str, Any]], field: str, errors: list[str]) -> None:
    need([item.get("rank") for item in items] == list(range(1, len(items) + 1)), f"{field} 排名必须从1连续排列", errors)


def audit_payload(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    need(payload.get("workflow_name") == WORKFLOW_NAME, "workflow_name 不正确", errors)
    need(str(payload.get("schema_version")) == SCHEMA_VERSION, "schema_version 不正确", errors)
    trade_date = parse_date(payload.get("trade_date"), "trade_date", errors)
    data_mode = str(payload.get("data_mode") or "")
    need(data_mode in {"intraday", "close"}, "data_mode 必须是 intraday 或 close", errors)
    parse_iso(payload.get("generated_at"), "generated_at", errors)
    parse_iso(payload.get("data_cutoff"), "data_cutoff", errors)

    sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
    need(bool(sources), "sources 必须是非空列表", errors)
    source_by_id: dict[str, dict[str, Any]] = {}
    provider_groups: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"sources[{index}] 必须是对象")
            continue
        source_id = str(source.get("source_id") or "").strip()
        need(bool(source_id) and source_id not in source_by_id, f"来源编号缺失或重复: {source_id or index}", errors)
        if source_id:
            source_by_id[source_id] = source
        for field in ("source_name", "provider_group", "source_type", "fetched_at", "locator", "sha256"):
            need(bool(str(source.get(field) or "").strip()), f"来源 {source_id or index} 缺少 {field}", errors)
        provider_groups.add(str(source.get("provider_group") or "").strip())
        parse_iso(source.get("fetched_at"), f"来源 {source_id or index} fetched_at", errors)
        need(parse_date(source.get("trade_date"), f"来源 {source_id or index} trade_date", errors) == trade_date, f"来源 {source_id or index} 交易日不一致", errors)
        need(bool(re.fullmatch(r"[0-9a-fA-F]{64}", str(source.get("sha256") or ""))), f"来源 {source_id or index} sha256 无效", errors)
    provider_groups.discard("")
    need(len(provider_groups) >= 2, "至少需要两个独立来源组", errors)

    evidence = payload.get("evidence") if isinstance(payload.get("evidence"), list) else []
    need(bool(evidence), "evidence 必须是非空列表", errors)
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            errors.append(f"evidence[{index}] 必须是对象")
            continue
        evidence_id = str(item.get("evidence_id") or "").strip()
        source_id = str(item.get("source_id") or "").strip()
        need(bool(evidence_id) and evidence_id not in evidence_by_id, f"证据编号缺失或重复: {evidence_id or index}", errors)
        if evidence_id:
            evidence_by_id[evidence_id] = item
        need(source_id in source_by_id, f"证据 {evidence_id or index} 引用了未知来源", errors)
        need(parse_date(item.get("trade_date"), f"证据 {evidence_id or index} trade_date", errors) == trade_date, f"证据 {evidence_id or index} 交易日不一致", errors)
        parse_iso(item.get("captured_at"), f"证据 {evidence_id or index} captured_at", errors)
        for field in ("stock_code", "field", "value", "locator"):
            need(item.get(field) not in (None, ""), f"证据 {evidence_id or index} 缺少 {field}", errors)

    def groups_for(ids: Any, field: str, minimum: int = 2) -> set[str]:
        if not isinstance(ids, list):
            errors.append(f"{field} 必须是证据编号列表")
            return set()
        groups: set[str] = set()
        for evidence_id in ids:
            item = evidence_by_id.get(str(evidence_id))
            if not item:
                errors.append(f"{field} 引用了未知证据 {evidence_id}")
                continue
            source = source_by_id.get(str(item.get("source_id")), {})
            group = str(source.get("provider_group") or "").strip()
            if group:
                groups.add(group)
        need(len(groups) >= minimum, f"{field} 至少需要 {minimum} 个独立来源组", errors)
        return groups

    stocks = payload.get("stocks") if isinstance(payload.get("stocks"), list) else []
    need(bool(stocks), "stocks 必须是非空列表", errors)
    stock_by_code: dict[str, dict[str, Any]] = {}
    times: dict[str, tuple[time, time]] = {}
    for index, stock in enumerate(stocks):
        if not isinstance(stock, dict):
            errors.append(f"stocks[{index}] 必须是对象")
            continue
        code = str(stock.get("stock_code") or "")
        need(bool(re.fullmatch(r"\d{6}", code)) and code not in stock_by_code, f"股票代码无效或重复: {code or index}", errors)
        if code:
            stock_by_code[code] = stock
        for field in ("stock_name", "exchange", "primary_concept"):
            need(bool(str(stock.get(field) or "").strip()), f"股票 {code or index} 缺少 {field}", errors)
        concept = str(stock.get("primary_concept") or "").strip()
        need(concept not in BANNED_CONCEPTS, f"股票 {code} 使用含糊投资板块: {concept}", errors)
        need(concept in ALLOWED_INVESTMENT_BOARDS, f"股票 {code} 投资板块不在八类允许集合: {concept}", errors)
        secondary = stock.get("secondary_concepts") if isinstance(stock.get("secondary_concepts"), list) else []
        drivers = stock.get("event_drivers") if isinstance(stock.get("event_drivers"), list) else []
        need(bool(secondary) and all(bool(str(item).strip()) for item in secondary), f"股票 {code} 细分方向必须是非空字符串列表", errors)
        need(bool(drivers) and all(bool(str(item).strip()) for item in drivers), f"股票 {code} 当日推动因素必须是非空字符串列表", errors)
        basis = str(stock.get("classification_basis") or "").strip()
        need(bool(basis), f"股票 {code} 缺少投资板块分类依据", errors)
        need(concept not in {str(item).strip() for item in secondary}, f"股票 {code} 投资板块与细分方向重复", errors)
        need(concept not in {str(item).strip() for item in drivers}, f"股票 {code} 投资板块与当日推动因素重复", errors)
        need(stock.get("at_limit_at_cutoff") is True, f"股票 {code} 截至时点未核实封在涨停价", errors)
        if data_mode == "close":
            need(stock.get("close_at_limit") is True, f"股票 {code} 收盘未封在涨停价", errors)
        finite_number(stock.get("limit_up_price"), f"股票 {code} limit_up_price", errors)
        first = parse_clock(stock.get("first_limit_time"), f"股票 {code} first_limit_time", errors)
        last_value = stock.get("latest_seal_time_at_cutoff", stock.get("final_limit_time"))
        last = parse_clock(last_value, f"股票 {code} latest_seal_time_at_cutoff", errors)
        if first and last:
            need(first <= last, f"股票 {code} 首次封板晚于截至时点最后封板", errors)
            times[code] = (first, last)
        field_evidence = stock.get("field_evidence") if isinstance(stock.get("field_evidence"), dict) else {}
        groups_for(field_evidence.get("pool"), f"股票 {code} 涨停池证据")
        groups_for(field_evidence.get("concept"), f"股票 {code} 投资板块证据")
        groups_for(field_evidence.get("times"), f"股票 {code} 封板时间证据")
        roles = stock.get("leader_roles") if isinstance(stock.get("leader_roles"), list) else []
        for role_index, role in enumerate(roles):
            if not isinstance(role, dict):
                errors.append(f"股票 {code} 性质[{role_index}] 必须是对象")
                continue
            need(bool(str(role.get("name") or "").strip()), f"股票 {code} 性质缺少名称", errors)
            need(bool(str(role.get("reason") or "").strip()), f"股票 {code} 性质缺少理由", errors)
            groups_for(role.get("evidence_ids"), f"股票 {code} 性质证据")

    concepts: dict[str, list[str]] = {}
    for code, stock in stock_by_code.items():
        concepts.setdefault(str(stock.get("primary_concept") or "").strip(), []).append(code)
    concept_summary = payload.get("concept_summary") if isinstance(payload.get("concept_summary"), list) else []
    seen_concepts: set[str] = set()
    for index, item in enumerate(concept_summary):
        if not isinstance(item, dict):
            errors.append(f"concept_summary[{index}] 必须是对象")
            continue
        concept = str(item.get("concept") or "").strip()
        need(concept in concepts and concept not in seen_concepts, f"投资板块汇总未知或重复: {concept}", errors)
        seen_concepts.add(concept)
        need(item.get("verified_limit_up_count") == len(concepts.get(concept, [])), f"投资板块 {concept} 家数不一致", errors)
        deep_fields = (
            "logic_summary",
            "mechanism_evidence",
            "validation_constraints",
        )
        if index < 3:
            members = [
                stock_by_code[code]
                for code in concepts.get(concept, [])
            ]
            member_codes = {str(stock["stock_code"]) for stock in members}
            member_names = {str(stock["stock_name"]) for stock in members}
            logic_model = (
                item.get("logic_model")
                if isinstance(item.get("logic_model"), dict)
                else {}
            )
            need(bool(logic_model), f"前三板块 {concept} 缺少结构化逻辑模型", errors)
            need(
                str(logic_model.get("logic_type") or "") in {
                    "双机制共振型",
                    "主机制集中型",
                    "高度抱团、多分支并行型",
                    "多分支轮动型",
                },
                f"前三板块 {concept} 逻辑类型无效",
                errors,
            )
            mechanisms = (
                logic_model.get("shared_mechanisms")
                if isinstance(logic_model.get("shared_mechanisms"), list)
                else []
            )
            need(bool(mechanisms), f"前三板块 {concept} 缺少共同机制覆盖", errors)
            for mechanism in mechanisms:
                codes = {
                    str(code) for code in mechanism.get("stock_codes") or []
                } if isinstance(mechanism, dict) else set()
                need(
                    bool(str(mechanism.get("name") or "").strip())
                    and int(mechanism.get("stock_count") or 0) == len(codes)
                    and codes <= member_codes,
                    f"前三板块 {concept} 共同机制覆盖无效",
                    errors,
                )
            common_events = (
                logic_model.get("common_event_evidence")
                if isinstance(logic_model.get("common_event_evidence"), list)
                else []
            )
            for event in common_events:
                codes = {
                    str(code) for code in event.get("stock_codes") or []
                } if isinstance(event, dict) else set()
                need(
                    bool(str(event.get("event") or "").strip())
                    and len(codes) >= 2
                    and int(event.get("stock_count") or 0) == len(codes)
                    and codes <= member_codes,
                    f"前三板块 {concept} 共同事件证据无效",
                    errors,
                )
            causal_boundary = str(
                logic_model.get("causal_boundary") or ""
            ).strip()
            need(
                bool(causal_boundary)
                and "因果" in causal_boundary
                and (
                    "不把题材共现等同于外生事件因果" in causal_boundary
                    or "不单凭共现断言事件已经造成涨停" in causal_boundary
                ),
                f"前三板块 {concept} 缺少因果边界",
                errors,
            )
            temporal_sequence = (
                logic_model.get("temporal_sequence")
                if isinstance(logic_model.get("temporal_sequence"), dict)
                else {}
            )
            for field in (
                "height_anchor",
                "mechanism_anchor",
                "temporal_lead_anchor",
                "capacity_anchor",
            ):
                need(
                    str(temporal_sequence.get(field) or "") in member_codes,
                    f"前三板块 {concept} 时序结构字段 {field} 无效",
                    errors,
                )
            need(
                isinstance(
                    temporal_sequence.get("subsequent_peer_count_90m"),
                    int,
                )
                and 0
                <= temporal_sequence["subsequent_peer_count_90m"]
                < len(members),
                f"前三板块 {concept} 90分钟后续同题材数量无效",
                errors,
            )
            need(
                "transmission" not in logic_model,
                f"前三板块 {concept} 禁止使用含因果暗示的传导字段",
                errors,
            )
            validation = (
                logic_model.get("validation")
                if isinstance(logic_model.get("validation"), dict)
                else {}
            )
            expected_validation = {
                "member_count": len(members),
                "linked_count": sum(
                    int(stock.get("consecutive_limit_count") or 1) >= 2
                    for stock in members
                ),
                "early_count": sum(
                    clock_seconds(stock.get("first_limit_time")) <= 10 * 3600
                    for stock in members
                ),
                "zero_open_count": sum(
                    int(stock.get("open_count") or 0) == 0 for stock in members
                ),
                "high_reopen_count": sum(
                    int(stock.get("open_count") or 0) >= 3 for stock in members
                ),
                "late_seal_count": sum(
                    clock_seconds(
                        stock.get("final_limit_time")
                        or stock.get("latest_seal_time_at_cutoff")
                    )
                    >= 14 * 3600
                    for stock in members
                ),
            }
            for field, expected in expected_validation.items():
                need(
                    validation.get(field) == expected,
                    f"前三板块 {concept} 逻辑验证字段 {field} 不可复算",
                    errors,
                )
            expected_clusters = {
                cluster
                for stock in members
                for cluster in stock_theme_clusters(stock)
            }
            need(
                all(
                    str(mechanism.get("name") or "") in expected_clusters
                    for mechanism in mechanisms
                    if isinstance(mechanism, dict)
                ),
                f"前三板块 {concept} 共同机制不来自成员事实",
                errors,
            )
            constraints = (
                logic_model.get("constraints")
                if isinstance(logic_model.get("constraints"), list)
                else []
            )
            need(
                bool(constraints)
                and all(bool(str(value).strip()) for value in constraints),
                f"前三板块 {concept} 缺少结构约束",
                errors,
            )
            need(
                str(logic_model.get("structural_evidence_strength") or "")
                in {"高", "中", "低"},
                f"前三板块 {concept} 盘面结构证据强度无效",
                errors,
            )
            structural_score = logic_model.get("structural_evidence_score")
            need(
                isinstance(structural_score, int)
                and -2 <= structural_score <= 5,
                f"前三板块 {concept} 盘面结构证据评分无效",
                errors,
            )
            need(
                "confidence" not in logic_model
                and "confidence_score" not in logic_model,
                f"前三板块 {concept} 禁止使用含混的证据完整度字段",
                errors,
            )
            position_conclusion = str(
                logic_model.get("position_conclusion") or ""
            ).strip()
            need(
                bool(position_conclusion) and "龙1" in position_conclusion,
                f"前三板块 {concept} 缺少板块内部龙头地位结论",
                errors,
            )
            if len(members) >= 3:
                need(
                    "高于龙2" in position_conclusion
                    and "龙3" in position_conclusion
                    and "但" in position_conclusion,
                    f"前三板块 {concept} 地位结论缺少龙1胜出、龙2压制或龙3边界",
                    errors,
                )
                need(
                    sum(name in position_conclusion for name in member_names) >= 3,
                    f"前三板块 {concept} 地位结论缺少前三席位具体股票",
                    errors,
                )
            for field in deep_fields:
                value = str(item.get(field) or "").strip()
                need(bool(value) and bool(re.search(r"\d", value)), f"前三板块 {concept} {field} 必须含本轮数字事实", errors)
                need(
                    not STATISTICS_ONLY_LOGIC.search(value),
                    f"前三板块 {concept} {field} 不能仅罗列统计数据",
                    errors,
                )
                for phrase in BANNED_CLAIMS:
                    need(phrase not in value, f"前三板块 {concept} {field} 含模板措辞: {phrase}", errors)
            logic_summary = str(item.get("logic_summary") or "")
            need(
                sum(term in logic_summary for term in LOGIC_CONNECTORS) >= 4,
                f"前三板块 {concept} 核心逻辑缺少机制、时序和因果边界",
                errors,
            )
            need(
                sum(name in logic_summary for name in member_names) >= 2
                or len(member_names) == 1,
                f"前三板块 {concept} 核心逻辑缺少具体股票锚点",
                errors,
            )
            need(
                item.get("logic_summary") == logic_model.get("logic_statement")
                and item.get("mechanism_evidence")
                == logic_model.get("mechanism_statement")
                and item.get("validation_constraints")
                == logic_model.get("validation_statement"),
                f"前三板块 {concept} 可见结论与结构化逻辑模型不一致",
                errors,
            )
        else:
            need(not item.get("logic_model"), f"非前三板块 {concept} 禁止生成逻辑模型", errors)
            for field in deep_fields:
                need(not str(item.get(field) or "").strip(), f"非前三板块 {concept} 禁止深析字段 {field}", errors)
            need(not item.get("nature_top") and not item.get("position_top"), f"非前三板块 {concept} 禁止生成榜单", errors)
        for list_name in ("nature_top", "position_top"):
            rows = item.get(list_name) if isinstance(item.get(list_name), list) else []
            need(len(rows) <= 10, f"投资板块 {concept} {list_name} 超过10只", errors)
            sequential_ranks(rows, f"投资板块 {concept} {list_name}", errors)
            listed: set[str] = set()
            reason_signatures: set[tuple[str, ...]] = set()
            for row in rows:
                code = str(row.get("stock_code") or "")
                need(code in concepts.get(concept, []) and code not in listed, f"投资板块 {concept} {list_name} 股票错误或重复: {code}", errors)
                listed.add(code)
                reason = str(row.get("reason") or "").strip()
                need(bool(reason), f"投资板块 {concept} {list_name} {code} 缺少理由", errors)
                for phrase in BANNED_CLAIMS:
                    need(phrase not in reason, f"投资板块 {concept} {list_name} {code} 含模板措辞: {phrase}", errors)
                if list_name == "position_top":
                    required_reason_fields = (
                        ("rank_driver", "缺少胜出依据"),
                        ("relative_comparison", "缺少相对比较"),
                        ("weakness", "缺少主要短板"),
                        ("invalidation", "缺少失效条件"),
                    )
                    for field, label in required_reason_fields:
                        need(
                            bool(str(row.get(field) or "").strip()),
                            f"投资板块 {concept} 地位榜 {code} {label}",
                            errors,
                        )
                    for label in (
                        "胜出依据：",
                        "相对位置：",
                        "主要短板：",
                        "失效条件：",
                    ):
                        need(
                            label in reason,
                            f"投资板块 {concept} 地位榜 {code} 理由缺少模块 {label}",
                            errors,
                        )
                    need(
                        "仅表示时序共振" not in reason,
                        f"投资板块 {concept} 地位榜 {code} 禁止用时序共振替代地位推理",
                        errors,
                    )
                    vector = (
                        row.get("decision_vector")
                        if isinstance(row.get("decision_vector"), dict)
                        else {}
                    )
                    stock = stock_by_code.get(code, {})
                    expected_vector = {
                        "consecutive_limit_count": int(
                            stock.get("consecutive_limit_count") or 1
                        ),
                        "recent_limit_count": int(stock.get("recent_limit_count") or 1),
                        "open_count": int(stock.get("open_count") or 0),
                        "final_limit_time": str(stock.get("final_limit_time") or ""),
                        "amount": float(stock.get("amount") or 0),
                        "first_limit_time": str(stock.get("first_limit_time") or ""),
                    }
                    for field, expected in expected_vector.items():
                        need(
                            vector.get(field) == expected,
                            f"投资板块 {concept} 地位榜 {code} 决策字段 {field} 不可复算",
                            errors,
                        )
                    signature = tuple(
                        re.sub(r"\s+", "", str(row.get(field) or ""))
                        for field, _label in required_reason_fields
                    )
                    need(
                        signature not in reason_signatures,
                        f"投资板块 {concept} 地位依据重复: {code}",
                        errors,
                    )
                    reason_signatures.add(signature)
                groups_for(row.get("evidence_ids"), f"投资板块 {concept} {list_name} {code} 证据")
    need(seen_concepts == set(concepts), "投资板块汇总未与涨停池完整对账", errors)

    expected_morning = [
        code for code, pair in sorted(times.items(), key=lambda item: (item[1][0], item[1][1], item[0]))
        if pair[1] <= MORNING_END
    ]
    morning = payload.get("morning_limit_ups") if isinstance(payload.get("morning_limit_ups"), list) else []
    actual_morning = [str(item.get("stock_code") or "") for item in morning if isinstance(item, dict)]
    need(actual_morning == expected_morning, "上午封板名单不完整或排序错误", errors)

    lhb_status = str(payload.get("lhb_status") or "")
    need(lhb_status in {"published", "not_published"}, "lhb_status 无效", errors)
    lhb_rows = payload.get("lhb_net_buy_ge_100m") if isinstance(payload.get("lhb_net_buy_ge_100m"), list) else []
    if lhb_status == "not_published":
        need(not lhb_rows, "龙虎榜未发布时亿元名单必须为空", errors)
    else:
        previous = math.inf
        for row in lhb_rows:
            code = str(row.get("stock_code") or "")
            need(code in stock_by_code, f"龙虎榜出现未知股票: {code}", errors)
            amount = finite_number(row.get("net_amount"), f"龙虎榜 {code} net_amount", errors)
            if amount is not None:
                need(amount >= LHB_THRESHOLD, f"龙虎榜 {code} 净买入不足1亿元", errors)
                need(amount <= previous, "龙虎榜亿元名单未按净买入降序", errors)
                previous = amount
            seats = row.get("seats") if isinstance(row.get("seats"), list) else []
            need(bool(seats), f"龙虎榜 {code} 缺少正式披露席位", errors)
            seen_seats: set[tuple] = set()
            for seat in seats:
                name = str(seat.get("seat_name") or "").strip()
                identity = str(seat.get("seat_identity") or "").strip()
                buy = finite_number(seat.get("buy_amount"), f"龙虎榜 {code} 席位买入", errors)
                sell = finite_number(seat.get("sell_amount"), f"龙虎榜 {code} 席位卖出", errors)
                net = finite_number(seat.get("net_amount"), f"龙虎榜 {code} 席位净额", errors)
                key = (name, buy, sell)
                need(bool(name) and key not in seen_seats, f"龙虎榜 {code} 席位缺名或重复", errors)
                seen_seats.add(key)
                need(identity in {"深股通专用席位", "机构专用席位", "营业部席位"}, f"龙虎榜 {code} 席位身份无依据", errors)
                if buy is not None and sell is not None and net is not None:
                    need(abs(net - (buy - sell)) < 1, f"龙虎榜 {code} 席位净额复算不一致", errors)

    claims = payload.get("report_claims") if isinstance(payload.get("report_claims"), list) else []
    claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            errors.append(f"report_claims[{index}] 必须是对象")
            continue
        claim_id = str(claim.get("claim_id") or "").strip()
        text = str(claim.get("text") or "").strip()
        need(bool(claim_id) and claim_id not in claim_ids, f"结论编号缺失或重复: {claim_id or index}", errors)
        claim_ids.add(claim_id)
        need(bool(text) and bool(re.search(r"\d", text)), f"结论 {claim_id or index} 必须含数字事实", errors)
        need(
            not str(claim.get("basis_text") or "").strip()
            and not str(claim.get("counterevidence_text") or "").strip(),
            f"结论 {claim_id or index} 禁止携带依据/反证过程字段",
            errors,
        )
        for phrase in BANNED_CLAIMS:
            need(phrase not in text, f"结论 {claim_id or index} 含模板措辞: {phrase}", errors)
        groups_for(claim.get("evidence_ids"), f"结论 {claim_id or index} 证据")

    conflicts = payload.get("unresolved_critical_conflicts")
    need(isinstance(conflicts, list) and not conflicts, "存在未解决关键冲突", errors)
    if errors:
        raise PayloadAuditError("\n".join(errors))
    return {
        "status": "PASS",
        "workflow_name": WORKFLOW_NAME,
        "schema_version": SCHEMA_VERSION,
        "trade_date": trade_date,
        "data_mode": data_mode,
        "stock_count": len(stock_by_code),
        "concept_count": len(concepts),
        "morning_count": len(expected_morning),
        "lhb_count": len(lhb_rows),
        "claim_count": len(claims),
    }


def load_and_audit(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise PayloadAuditError("结构化结果顶层必须是对象")
    return audit_payload(payload)
