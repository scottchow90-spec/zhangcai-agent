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


WORKFLOW_NAME = "每日涨停板龙头分类"
SCHEMA_VERSION = "1.0"
BANNED_CONCEPTS = {"其他", "其它", "综合", "综合概念", "未分类", "待定", "未知"}
BANNED_CLAIM_PHRASES = {
    "沿用上期",
    "维持原判断",
    "默认结论",
    "固定结论",
    "兜底判断",
    "通常如此",
    "一般都会",
    "一般来说",
    "有望",
    "预计",
    "大概率",
    "建议关注",
    "后市可期",
    "值得关注",
}
MORNING_END = time(11, 30, 0)
LHB_THRESHOLD = 100_000_000.0


class PayloadAuditError(ValueError):
    pass


def _need(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _parse_date(value: Any, field: str, errors: list[str]) -> str:
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date().isoformat()
    except Exception:
        errors.append(f"{field} 必须是 YYYY-MM-DD")
        return ""


def _parse_iso(value: Any, field: str, errors: list[str]) -> None:
    try:
        text = str(value)
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("missing timezone")
    except Exception:
        errors.append(f"{field} 必须是带时区时间")


def _parse_clock(value: Any, field: str, errors: list[str]) -> time | None:
    try:
        return datetime.strptime(str(value), "%H:%M:%S").time()
    except Exception:
        errors.append(f"{field} 必须是 HH:MM:SS")
        return None


def _money(value: Any, field: str, errors: list[str]) -> float | None:
    try:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("not finite")
        return number
    except Exception:
        errors.append(f"{field} 必须是有限金额数字")
        return None


def _seq_ranks(items: list[dict[str, Any]], field: str, errors: list[str]) -> None:
    ranks = [item.get("rank") for item in items]
    _need(ranks == list(range(1, len(items) + 1)), f"{field} 排名必须从1连续排列", errors)


def audit_payload(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    _need(payload.get("workflow_name") == WORKFLOW_NAME, "workflow_name 不正确", errors)
    _need(str(payload.get("schema_version")) == SCHEMA_VERSION, "schema_version 不正确", errors)

    trade_date = _parse_date(payload.get("trade_date"), "trade_date", errors)
    latest_date = _parse_date(payload.get("latest_completed_trade_date"), "latest_completed_trade_date", errors)
    _need(bool(trade_date) and trade_date == latest_date, "报告交易日必须等于最新完整交易日", errors)
    _parse_iso(payload.get("generated_at"), "generated_at", errors)
    _parse_iso(payload.get("data_cutoff"), "data_cutoff", errors)

    sources = payload.get("sources")
    _need(isinstance(sources, list), "sources 必须是列表", errors)
    sources = sources if isinstance(sources, list) else []
    source_by_id: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"sources[{index}] 必须是对象")
            continue
        source_id = str(source.get("source_id", "")).strip()
        _need(bool(source_id), f"sources[{index}] 缺少 source_id", errors)
        _need(source_id not in source_by_id, f"来源编号重复: {source_id}", errors)
        if source_id:
            source_by_id[source_id] = source
        for key in ("source_name", "provider_group", "source_type", "fetched_at", "locator", "sha256"):
            _need(bool(str(source.get(key, "")).strip()), f"来源 {source_id or index} 缺少 {key}", errors)
        _parse_iso(source.get("fetched_at"), f"来源 {source_id or index} fetched_at", errors)
        source_trade_date = _parse_date(source.get("trade_date"), f"来源 {source_id or index} trade_date", errors)
        _need(not trade_date or source_trade_date == trade_date, f"来源 {source_id or index} 交易日不一致", errors)
        sha = str(source.get("sha256", ""))
        _need(bool(re.fullmatch(r"[0-9a-fA-F]{64}", sha)), f"来源 {source_id or index} sha256 无效", errors)

    evidence = payload.get("evidence")
    _need(isinstance(evidence, list), "evidence 必须是列表", errors)
    evidence = evidence if isinstance(evidence, list) else []
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            errors.append(f"evidence[{index}] 必须是对象")
            continue
        evidence_id = str(item.get("evidence_id", "")).strip()
        source_id = str(item.get("source_id", "")).strip()
        _need(bool(evidence_id), f"evidence[{index}] 缺少 evidence_id", errors)
        _need(evidence_id not in evidence_by_id, f"证据编号重复: {evidence_id}", errors)
        _need(source_id in source_by_id, f"证据 {evidence_id or index} 引用了未知来源", errors)
        if evidence_id:
            evidence_by_id[evidence_id] = item
        for key in ("stock_code", "field", "value", "captured_at", "locator"):
            _need(item.get(key) not in (None, ""), f"证据 {evidence_id or index} 缺少 {key}", errors)
        _parse_iso(item.get("captured_at"), f"证据 {evidence_id or index} captured_at", errors)
        ev_date = _parse_date(item.get("trade_date"), f"证据 {evidence_id or index} trade_date", errors)
        _need(not trade_date or ev_date == trade_date, f"证据 {evidence_id or index} 交易日不一致", errors)

    def groups_for(evidence_ids: Any, field: str, minimum: int = 2) -> set[str]:
        if not isinstance(evidence_ids, list):
            errors.append(f"{field} 必须是证据编号列表")
            return set()
        groups: set[str] = set()
        for evidence_id in evidence_ids:
            item = evidence_by_id.get(str(evidence_id))
            if not item:
                errors.append(f"{field} 引用了未知证据 {evidence_id}")
                continue
            source = source_by_id.get(str(item.get("source_id")), {})
            group = str(source.get("provider_group", "")).strip()
            if group:
                groups.add(group)
        _need(len(groups) >= minimum, f"{field} 至少需要 {minimum} 个独立来源组", errors)
        return groups

    stocks = payload.get("stocks")
    _need(isinstance(stocks, list), "stocks 必须是列表", errors)
    stocks = stocks if isinstance(stocks, list) else []
    stock_by_code: dict[str, dict[str, Any]] = {}
    time_by_code: dict[str, tuple[time, time]] = {}
    for index, stock in enumerate(stocks):
        if not isinstance(stock, dict):
            errors.append(f"stocks[{index}] 必须是对象")
            continue
        code = str(stock.get("stock_code", "")).strip()
        _need(bool(re.fullmatch(r"\d{6}", code)), f"股票代码无效: {code or index}", errors)
        _need(code not in stock_by_code, f"股票重复: {code}", errors)
        if code:
            stock_by_code[code] = stock
        for key in ("stock_name", "exchange", "primary_concept"):
            _need(bool(str(stock.get(key, "")).strip()), f"股票 {code or index} 缺少 {key}", errors)
        concept = str(stock.get("primary_concept", "")).strip()
        _need(concept not in BANNED_CONCEPTS, f"股票 {code} 使用了含糊主概念: {concept}", errors)
        _need(stock.get("close_at_limit") is True, f"股票 {code} 收盘未核实封在涨停价", errors)
        _money(stock.get("close_price"), f"股票 {code} close_price", errors)
        _money(stock.get("limit_up_price"), f"股票 {code} limit_up_price", errors)
        first_time = _parse_clock(stock.get("first_limit_time"), f"股票 {code} first_limit_time", errors)
        final_time = _parse_clock(stock.get("final_limit_time"), f"股票 {code} final_limit_time", errors)
        if first_time and final_time:
            _need(first_time <= final_time, f"股票 {code} 首次封板时间晚于最终封板时间", errors)
            time_by_code[code] = (first_time, final_time)
        field_evidence = stock.get("field_evidence")
        _need(isinstance(field_evidence, dict), f"股票 {code} 缺少 field_evidence", errors)
        field_evidence = field_evidence if isinstance(field_evidence, dict) else {}
        groups_for(field_evidence.get("pool"), f"股票 {code} 涨停池证据")
        groups_for(field_evidence.get("concept"), f"股票 {code} 主概念证据")
        groups_for(field_evidence.get("times"), f"股票 {code} 封板时间证据")

        roles = stock.get("leader_roles", [])
        _need(isinstance(roles, list), f"股票 {code} leader_roles 必须是列表", errors)
        for role_index, role in enumerate(roles if isinstance(roles, list) else []):
            if not isinstance(role, dict):
                errors.append(f"股票 {code} 性质[{role_index}] 必须是对象")
                continue
            _need(bool(str(role.get("name", "")).strip()), f"股票 {code} 性质缺少名称", errors)
            _need(bool(str(role.get("reason", "")).strip()), f"股票 {code} 性质缺少白话理由", errors)
            groups_for(role.get("evidence_ids"), f"股票 {code} 性质 {role.get('name', role_index)} 证据")

        lhb = stock.get("lhb")
        _need(isinstance(lhb, dict), f"股票 {code} 缺少 lhb", errors)
        lhb = lhb if isinstance(lhb, dict) else {}
        if lhb.get("is_listed") is True:
            buy = _money(lhb.get("buy_amount"), f"股票 {code} 龙虎榜买入额", errors)
            sell = _money(lhb.get("sell_amount"), f"股票 {code} 龙虎榜卖出额", errors)
            net = _money(lhb.get("net_amount"), f"股票 {code} 龙虎榜净买入额", errors)
            if buy is not None and sell is not None and net is not None:
                _need(abs((buy - sell) - net) <= 1.0, f"股票 {code} 龙虎榜净买入额计算不一致", errors)
            lhb_groups = groups_for(lhb.get("evidence_ids"), f"股票 {code} 龙虎榜证据")
            official = False
            for evidence_id in lhb.get("evidence_ids", []) if isinstance(lhb.get("evidence_ids"), list) else []:
                item = evidence_by_id.get(str(evidence_id), {})
                source = source_by_id.get(str(item.get("source_id")), {})
                if source.get("source_type") == "交易所公开信息":
                    official = True
            _need(official and len(lhb_groups) >= 2, f"股票 {code} 龙虎榜必须含交易所披露和独立复核", errors)
        else:
            _need(lhb.get("is_listed") is False, f"股票 {code} lhb.is_listed 必须明确真假", errors)
            for key in ("buy_amount", "sell_amount", "net_amount"):
                _need(lhb.get(key) is None, f"股票 {code} 未上龙虎榜时 {key} 必须为空", errors)

    concept_summary = payload.get("concept_summary")
    _need(isinstance(concept_summary, list), "concept_summary 必须是列表", errors)
    concept_summary = concept_summary if isinstance(concept_summary, list) else []
    actual_concepts: dict[str, list[str]] = {}
    for code, stock in stock_by_code.items():
        actual_concepts.setdefault(str(stock.get("primary_concept", "")).strip(), []).append(code)
    seen_concepts: set[str] = set()
    for index, concept_item in enumerate(concept_summary):
        if not isinstance(concept_item, dict):
            errors.append(f"concept_summary[{index}] 必须是对象")
            continue
        concept = str(concept_item.get("concept", "")).strip()
        _need(concept in actual_concepts, f"概念汇总出现未知概念: {concept}", errors)
        _need(concept not in seen_concepts, f"概念汇总重复: {concept}", errors)
        seen_concepts.add(concept)
        codes = actual_concepts.get(concept, [])
        _need(concept_item.get("verified_limit_up_count") == len(codes), f"概念 {concept} 涨停家数不一致", errors)

        nature_top = concept_item.get("nature_top", [])
        _need(isinstance(nature_top, list), f"概念 {concept} nature_top 必须是列表", errors)
        nature_top = nature_top if isinstance(nature_top, list) else []
        _need(len(nature_top) <= 10, f"概念 {concept} 性质榜超过10只", errors)
        _seq_ranks(nature_top, f"概念 {concept} 性质榜", errors)
        nature_codes: set[str] = set()
        for item in nature_top:
            code = str(item.get("stock_code", ""))
            _need(code in codes, f"概念 {concept} 性质榜股票不属于本概念: {code}", errors)
            _need(code not in nature_codes, f"概念 {concept} 性质榜股票重复: {code}", errors)
            nature_codes.add(code)
            nature_names = item.get("nature_names")
            _need(isinstance(nature_names, list) and len(nature_names) > 0, f"概念 {concept} 性质榜 {code} 缺少性质名称", errors)
            stock_roles = {
                str(role.get("name", "")).strip()
                for role in stock_by_code.get(code, {}).get("leader_roles", [])
                if isinstance(role, dict)
            }
            if isinstance(nature_names, list):
                _need(set(map(str, nature_names)).issubset(stock_roles), f"概念 {concept} 性质榜 {code} 出现未核实性质", errors)
            _need(bool(str(item.get("reason", "")).strip()), f"概念 {concept} 性质榜 {code} 缺少理由", errors)
            groups_for(item.get("evidence_ids"), f"概念 {concept} 性质榜 {code} 证据")
        role_stock_count = sum(1 for code in codes if stock_by_code.get(code, {}).get("leader_roles"))
        _need(len(nature_top) == min(role_stock_count, 10), f"概念 {concept} 性质榜存在漏项或补位", errors)

        position_top = concept_item.get("position_top", [])
        _need(isinstance(position_top, list), f"概念 {concept} position_top 必须是列表", errors)
        position_top = position_top if isinstance(position_top, list) else []
        _need(len(position_top) <= 10, f"概念 {concept} 地位榜超过10只", errors)
        _seq_ranks(position_top, f"概念 {concept} 地位榜", errors)
        position_codes: set[str] = set()
        for item in position_top:
            code = str(item.get("stock_code", ""))
            _need(code in codes, f"概念 {concept} 地位榜股票不属于本概念: {code}", errors)
            _need(code not in position_codes, f"概念 {concept} 地位榜股票重复: {code}", errors)
            position_codes.add(code)
            _need(bool(str(item.get("reason", "")).strip()), f"概念 {concept} 地位榜 {code} 缺少理由", errors)
            groups_for(item.get("evidence_ids"), f"概念 {concept} 地位榜 {code} 证据")
    _need(seen_concepts == set(actual_concepts), "概念汇总未与涨停池完整对账", errors)
    _need(sum(len(codes) for codes in actual_concepts.values()) == len(stock_by_code), "主概念统计存在重复或遗漏", errors)

    morning = payload.get("morning_limit_ups")
    _need(isinstance(morning, list), "morning_limit_ups 必须是列表", errors)
    morning = morning if isinstance(morning, list) else []
    expected_morning = [
        code
        for code, (first, final) in sorted(time_by_code.items(), key=lambda pair: (pair[1][0], pair[1][1], pair[0]))
        if final <= MORNING_END
    ]
    actual_morning = [str(item.get("stock_code", "")) for item in morning if isinstance(item, dict)]
    _need(actual_morning == expected_morning, "上午封板名单必须完整且按首次封板时间升序", errors)

    lhb_top = payload.get("lhb_net_buy_ge_100m")
    _need(isinstance(lhb_top, list), "lhb_net_buy_ge_100m 必须是列表", errors)
    lhb_top = lhb_top if isinstance(lhb_top, list) else []
    expected_lhb_pairs: list[tuple[str, float]] = []
    for code, stock in stock_by_code.items():
        lhb = stock.get("lhb", {}) if isinstance(stock.get("lhb"), dict) else {}
        if lhb.get("is_listed") is True:
            try:
                net = float(lhb.get("net_amount"))
            except Exception:
                continue
            if math.isfinite(net) and net >= LHB_THRESHOLD:
                expected_lhb_pairs.append((code, net))
    expected_lhb_pairs.sort(key=lambda pair: (-pair[1], time_by_code.get(pair[0], (time.max, time.max))[0], pair[0]))
    actual_lhb = [str(item.get("stock_code", "")) for item in lhb_top if isinstance(item, dict)]
    _need(actual_lhb == [code for code, _ in expected_lhb_pairs], "龙虎榜一亿元名单必须完整且按净买入额降序", errors)

    claims = payload.get("report_claims")
    _need(isinstance(claims, list), "report_claims 必须是列表", errors)
    claims = claims if isinstance(claims, list) else []
    claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            errors.append(f"report_claims[{index}] 必须是对象")
            continue
        claim_id = str(claim.get("claim_id", "")).strip()
        text = str(claim.get("text", "")).strip()
        _need(bool(claim_id), f"report_claims[{index}] 缺少 claim_id", errors)
        _need(claim_id not in claim_ids, f"结论编号重复: {claim_id}", errors)
        claim_ids.add(claim_id)
        _need(bool(text), f"结论 {claim_id or index} 缺少文字", errors)
        for phrase in BANNED_CLAIM_PHRASES:
            _need(phrase not in text, f"结论 {claim_id or index} 含模板式措辞: {phrase}", errors)
        groups_for(claim.get("evidence_ids"), f"结论 {claim_id or index} 证据")

    conflicts = payload.get("unresolved_critical_conflicts")
    _need(isinstance(conflicts, list), "unresolved_critical_conflicts 必须是列表", errors)
    _need(isinstance(conflicts, list) and len(conflicts) == 0, "仍有未解决关键冲突，禁止正式报告", errors)

    if errors:
        raise PayloadAuditError("\n".join(errors))
    return {
        "status": "PASS",
        "workflow_name": WORKFLOW_NAME,
        "trade_date": trade_date,
        "stock_count": len(stock_by_code),
        "concept_count": len(actual_concepts),
        "morning_count": len(expected_morning),
        "lhb_ge_100m_count": len(expected_lhb_pairs),
        "claim_count": len(claims),
    }


def load_and_audit(path: str | Path) -> dict[str, Any]:
    payload_path = Path(path)
    with payload_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise PayloadAuditError("结构化结果顶层必须是对象")
    return audit_payload(payload)
