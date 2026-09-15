from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENGINE = load_module("a_share_15d_scoring_test", SCRIPTS / "run_a_share_15d.py")
AUDIT = load_module("a_share_15d_audit_scoring_test", SCRIPTS / "audit_engine.py")


def rows(last_close: float = 11.0) -> list[dict]:
    values = []
    for index in range(89):
        close = 10.0 + index * 0.002
        values.append({
            "date": f"20260{index // 28 + 1}{index % 28 + 1:02d}",
            "open": close,
            "high": close + 0.2,
            "low": close - 0.2,
            "close": close,
            "amount": 200_000_000.0,
            "volume": 100_000.0,
        })
    values.append({
        "date": "20260401",
        "open": 10.3,
        "high": last_close,
        "low": 10.2,
        "close": last_close,
        "amount": 600_000_000.0,
        "volume": 180_000.0,
    })
    return values


def candidate_item() -> dict:
    return {
        "rows": rows(),
        "formula_fields": {
            "大牛线4.0": {
                "主趋势线": 10.0,
                "EMA9": 10.2,
                "EMA10": 10.1,
                "EMA11": 10.0,
                "OUTPUT6": 0,
            },
            "飞龙在天": {"波": 50.0, "段": 45.0, "OUTPUT3": 0, "OUTPUT4": 0, "OUTPUT5": 0, "OUTPUT6": 0},
            "游资资金监控": {"买方意向": 0.0, "AAA": 0.0, "DDD": 0.0},
            "机构资金监控": {
                "机构大单进": 0.0,
                "机构大单出": 0.0,
                "大单动向": 0.0,
                "大户大单进": 0.0,
                "散户资金进": 0.0,
            },
            "庄家资金监控": {},
        },
        "wave": 50.0,
        "segment": 45.0,
        "ignition": False,
        "risk_hits": [],
        "major_risk_hits": [],
        "reduction_hits": [],
        "catalyst_hits": [],
        "fundamental_hits": [],
        "financial_safety_hits": [],
        "lhb_hits": [],
        "concepts": [],
        "candidate_text_source_count": 0,
        "local_text_source_count": 0,
        "limit_price": 11.0,
        "pct": 10.0,
        "is_one_price": False,
        "one_price_streak": 0,
        "recent_gain_3d_pct": 10.0,
        "recent_gain_5d_pct": 12.0,
        "recent_gain_10d_pct": 15.0,
    }


def dimension(result: dict, name: str) -> dict:
    return next(row for row in result["positive_dimensions"] if row["name"] == name)


def risk(result: dict, name: str) -> dict:
    return next(row for row in result["risks"] if row["name"] == name)


def test_required_formula_success_requires_complete_numeric_fields():
    for formula in ENGINE.REQUIRED_FORMULA_FIELDS:
        assert not ENGINE.required_formula_result_ok(formula, {})
    for formula, fields in ENGINE.REQUIRED_FORMULA_FIELDS.items():
        payload = {field: 1.0 for field in fields}
        assert ENGINE.required_formula_result_ok(formula, payload)
        payload[fields[0]] = None
        assert not ENGINE.required_formula_result_ok(formula, payload)


def test_missing_evidence_does_not_receive_default_positive_points():
    item = candidate_item()
    item["formula_fields"]["大牛线4.0"] = {}
    item["formula_fields"]["游资资金监控"] = {}
    item["formula_fields"]["机构资金监控"] = {}
    result = ENGINE.score_candidate(item, Counter())

    zero_dimensions = (
        "大牛线攻击信号",
        "飞龙启动信号",
        "游资点火强度",
        "机构净流入强度",
        "资金合力持续性",
        "催化延续证据",
        "市场广度",
        "涨停生态",
        "主线题材共振",
        "全市场相对强度",
    )
    for name in zero_dimensions:
        assert dimension(result, name)["score"] == 0.0


def test_dealer_exit_and_trend_break_are_independent_risks():
    item = candidate_item()
    item["formula_fields"]["大牛线4.0"]["OUTPUT6"] = 1
    result = ENGINE.score_candidate(item, Counter())
    assert risk(result, "大牛线庄出")["deduction"] == 2
    assert risk(result, "跌破主趋势线")["deduction"] == 0

    item = candidate_item()
    item["formula_fields"]["大牛线4.0"]["主趋势线"] = 12.0
    result = ENGINE.score_candidate(item, Counter())
    assert risk(result, "大牛线庄出")["deduction"] == 0
    assert risk(result, "跌破主趋势线")["deduction"] == 3


def test_soft_announcement_and_high_wave_risks_remain_reachable_after_hard_gate():
    item = candidate_item()
    item["wave"] = 85.0
    item["formula_fields"]["飞龙在天"]["波"] = 85.0
    item["major_risk_hits"] = [{"keywords": "诉讼"}]
    result = ENGINE.score_candidate(item, Counter())
    assert risk(result, "重大公告或财务风险")["deduction"] == 3
    assert risk(result, "波段过高且无资金承接")["deduction"] == 3


def test_concept_strength_uses_other_candidates_and_filters_generic_regions():
    assert ENGINE.concept_tokens("浙江板块 人工智能 人工智能 综合类") == ["人工智能"]
    item = candidate_item()
    item["concepts"] = ["人工智能"]
    own_only = ENGINE.score_candidate(item, Counter({"人工智能": 1}))
    shared = ENGINE.score_candidate(item, Counter({"人工智能": 4}))
    assert dimension(own_only, "主线题材共振")["score"] == 0.0
    assert dimension(shared, "主线题材共振")["score"] == 7.0


def test_cross_sectional_scores_limit_full_marks_to_the_strongest_cohort():
    cohort = [float(value) for value in range(1, 11)]
    assert ENGINE.cross_sectional_stars(10.0, cohort) == 5.0
    assert ENGINE.cross_sectional_stars(8.0, cohort) == 4.0
    assert ENGINE.cross_sectional_stars(5.0, cohort) == 3.0
    assert ENGINE.cross_sectional_stars(1.0, cohort) == 1.5
    assert ENGINE.cross_sectional_stars(0.0, cohort) == 0.0


def test_fundamental_and_financial_hits_never_create_positive_factors():
    item = candidate_item()
    item["fundamental_hits"] = [{"keywords": "营收增长"}]
    item["financial_safety_hits"] = [{"keywords": "现金流改善"}]
    result = ENGINE.score_candidate(item, Counter())
    names = {row["name"] for row in result["positive_dimensions"]}
    assert not any("基本面" in name or "财务" in name or "估值" in name for name in names)
    assert result["score_contract"]["fundamental_positive_weight"] == 0


def test_liquidity_execution_is_not_a_duplicate_of_trend_distance():
    item = candidate_item()
    item["formula_fields"]["大牛线4.0"]["主趋势线"] = 12.0
    result = ENGINE.score_candidate(item, Counter())
    assert dimension(result, "流动性分位")["score"] > 0.0
    assert risk(result, "跌破主趋势线")["deduction"] == 3


def test_current_breakout_high_is_not_treated_as_preexisting_pressure():
    result = ENGINE.score_candidate(candidate_item(), Counter())
    assert risk(result, "强压力位压制")["deduction"] == 0


def test_audit_recomputes_candidate_score_math():
    result = ENGINE.score_candidate(candidate_item(), Counter())
    assert AUDIT.validate_candidate_score(result, 1) == []
    result["final_score"] += 1
    assert "candidate_1_final_score_mismatch" in AUDIT.validate_candidate_score(result, 1)


def test_audit_recomputes_full_cross_sectional_26_factor_cohort():
    items = []
    for index in range(10):
        item = candidate_item()
        item.update({"market": "SZ", "code": f"0000{index:02d}", "name": f"测试{index}", "is_limit_up": True})
        item["rows"][-1]["amount"] = 150_000_000.0 + index * 80_000_000.0
        item["rows"][-1]["volume"] = 110_000.0 + index * 18_000.0
        item["recent_gain_3d_pct"] = 8.0 + index
        item["recent_gain_5d_pct"] = 10.0 + index * 1.4
        item["recent_gain_10d_pct"] = 12.0 + index * 1.8
        item["formula_fields"]["游资资金监控"].update({"买方意向": index / 10, "AAA": 2.0, "DDD": 1.0})
        item["formula_fields"]["机构资金监控"].update({"机构大单进": index + 1.0, "机构大单出": 1.0})
        item["concepts"] = ["人工智能"] if index >= 4 else ["机器人"]
        items.append(item)
    concepts = Counter(token for item in items for token in item["concepts"])
    macro = {
        "market_count": 5000,
        "advancers": 2900,
        "decliners": 1900,
        "flat": 200,
        "limit_up_count": 65,
        "market_return_cohorts": {
            "1d": [value / 10 for value in range(-100, 101)],
            "3d": [value / 5 for value in range(-100, 101)],
            "5d": [value / 4 for value in range(-100, 101)],
            "10d": [value / 3 for value in range(-100, 101)],
        },
    }
    context = ENGINE.build_scoring_context(items, concepts, macro)
    scored = [ENGINE.score_candidate(item, concepts, len(items), context) for item in items]
    audit_context = AUDIT._build_scoring_context(scored, concepts, macro)

    for index, result in enumerate(scored, 1):
        assert AUDIT.validate_candidate_score(result, index, concepts, audit_context) == []

    scored[0]["axis_scores"]["爆发力"]["normalized"] += 1
    assert "candidate_1_axis_爆发力_mismatch" in AUDIT.validate_candidate_score(scored[0], 1, concepts, audit_context)


def test_audit_rejects_semantic_score_tampering_even_when_totals_are_updated():
    result = ENGINE.score_candidate(candidate_item(), Counter())
    target = dimension(result, "催化延续证据")
    delta = target["weight"] - target["score"]
    target["stars"] = 5.0
    target["score"] = target["weight"]
    result["positive_score"] = round(result["positive_score"] + delta, 2)
    result["final_score"] = round(result["final_score"] + delta, 2)

    errors = AUDIT.validate_candidate_score(result, 1)

    assert "candidate_1_dimension_18_semantic_mismatch" in errors


def test_positive_and_exit_signal_polarity_are_separate():
    assert ENGINE.positive_signal_active("点火") is True
    assert ENGINE.positive_signal_active("庄出") is False
    assert ENGINE.exit_signal_active("庄出") is True
    assert ENGINE.exit_signal_active("点火") is False


def test_bse_identity_and_price_limit_are_supported():
    assert ENGINE.valid_a_code("BJ", "920001") is True
    assert ENGINE.valid_a_code("BJ", "899050") is False
    assert ENGINE.limit_rate("BJ", "920001") == 0.30
    assert ENGINE.limit_rate("SH", "688001") == 0.20


def test_expected_trade_date_uses_official_holiday_calendar():
    moment = datetime(2026, 5, 4, 18, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert ENGINE.expected_completed_trade_date(moment) == "20260430"


def test_negative_macd_histogram_cannot_create_bearish_divergence():
    closes = [10.0] * 9 + [11.0]
    hist = [-0.5, -0.4, -0.3, -0.2, -0.1, -0.2, -0.15, -0.1, -0.08, -0.09]
    assert ENGINE.macd_bearish_divergence(closes, hist) is False


def test_text_hard_gate_fails_closed_without_candidate_coverage():
    item = candidate_item()
    item.update({"code": "000001", "name": "测试股份", "market": "SZ", "symbol": "000001.SZ"})
    item["rows"] = rows()
    ENGINE.run_hub = lambda *args, **kwargs: {
        "items": [
            {"formula": name, "ok": True, "result": {"000001.SZ": fields}}
            for name, fields in item["formula_fields"].items()
            if name != "庄家资金监控"
        ]
    }
    enriched = ENGINE.enrich_candidate(item, [])
    risk_gate = next(row for row in enriched["hard_exclusions"] if row["name"] == "立案调查或财务造假")
    assert risk_gate["passed"] is False
    assert enriched["passed_hard_gate"] is False


def test_score_contract_is_26_factor_short_term_four_axis_model():
    item = candidate_item()
    item["formula_fields"]["大牛线4.0"].update({
        "主趋势线": 10.5,
        "OUTPUT3": 1,
    })
    item["formula_fields"]["飞龙在天"]["OUTPUT3"] = 1
    item["formula_fields"]["游资资金监控"].update({
        "买方意向": 1.0,
        "AAA": 2.0,
        "DDD": 1.0,
        "OUTPUT4": 1,
    })
    item["formula_fields"]["机构资金监控"].update({
        "机构大单进": 2.0,
        "机构大单出": 1.0,
        "大单动向": 1.0,
        "大户大单进": 1.0,
        "散户资金进": -1.0,
    })
    item["formula_fields"]["庄家资金监控"]["控盘度"] = 80.0
    item["ignition"] = True
    item["catalyst_hits"] = [{"keywords": "中标"}]
    item["lhb_hits"] = [{"keywords": "机构专用买入"}]
    item["concepts"] = ["人工智能"]

    result = ENGINE.score_candidate(item, Counter({"人工智能": 4}), universe_size=4)

    assert len(result["positive_dimensions"]) == 26
    assert sum(row["weight"] for row in result["positive_dimensions"]) == 100.0
    assert result["score_contract"]["version"] == "A-SHARE-STRONG-26F-100-V6.1"
    assert result["score_contract"]["factor_role_policy"] == "pool_and_regime_factors_calibrate_absolute_context_but_do_not_claim_cross_sectional_ranking_power"
    assert result["score_contract"]["axis_weights"] == {
        "爆发力": 35.0,
        "持续性": 35.0,
        "市场协同": 20.0,
        "可交易性": 10.0,
    }
    assert set(result["axis_scores"]) == {"爆发力", "持续性", "市场协同", "可交易性"}


def test_factor_roles_separate_ranking_from_pool_and_market_context():
    result = ENGINE.score_candidate(candidate_item(), Counter())
    roles = {row["name"]: row["role"] for row in result["positive_dimensions"]}
    assert roles["强势收盘强度"] == "pool_confirmation"
    assert roles["市场广度"] == roles["涨停生态"] == "market_regime"
    assert roles["催化延续证据"] == "candidate_evidence"
    assert sum(row["ranking_relevant"] for row in result["positive_dimensions"]) == 23


def test_volatility_quality_uses_cross_sectional_ranking_instead_of_wide_full_mark_band():
    items = []
    for index in range(10):
        item = candidate_item()
        item["rows"][-1]["high"] += index * 0.35
        item["rows"][-1]["low"] -= index * 0.15
        items.append(item)
    concepts = Counter()
    context = ENGINE.build_scoring_context(items, concepts)
    results = [ENGINE.score_candidate(item, concepts, len(items), context) for item in items]
    volatility_stars = [dimension(result, "波动可控性")["stars"] for result in results]
    assert len(set(volatility_stars)) > 1
    assert sum(value == 5.0 for value in volatility_stars) / len(volatility_stars) < 0.8


def test_supported_high_momentum_is_not_blanket_excluded():
    item = candidate_item()
    item.update({"code": "000001", "name": "测试股份", "market": "SZ", "symbol": "000001.SZ"})
    item["recent_gain_3d_pct"] = 45.0
    item["recent_gain_5d_pct"] = 70.0
    item["recent_gain_10d_pct"] = 95.0
    item["formula_fields"]["游资资金监控"].update({"买方意向": 1.0, "AAA": 2.0, "DDD": 1.0})
    item["formula_fields"]["机构资金监控"].update({"机构大单进": 2.0, "机构大单出": 1.0})
    ENGINE.run_hub = lambda *args, **kwargs: {
        "items": [
            {"formula": name, "ok": True, "result": {"000001.SZ": fields}}
            for name, fields in item["formula_fields"].items()
            if name != "庄家资金监控"
        ]
    }
    enriched = ENGINE.enrich_candidate(item, [("local.txt", "000001 测试股份发布正常公告。")])
    assert next(row for row in enriched["hard_exclusions"] if row["name"] == "近3日极端加速且无启动承接")["passed"] is True
    assert next(row for row in enriched["hard_exclusions"] if row["name"] == "近5日或10日极端加速且无资金承接")["passed"] is True


def test_unsupported_extreme_momentum_is_excluded():
    item = candidate_item()
    item.update({"code": "000001", "name": "测试股份", "market": "SZ", "symbol": "000001.SZ"})
    item["recent_gain_3d_pct"] = 45.0
    item["recent_gain_5d_pct"] = 70.0
    item["recent_gain_10d_pct"] = 95.0
    ENGINE.run_hub = lambda *args, **kwargs: {
        "items": [
            {"formula": name, "ok": True, "result": {"000001.SZ": fields}}
            for name, fields in item["formula_fields"].items()
            if name != "庄家资金监控"
        ]
    }
    enriched = ENGINE.enrich_candidate(item, [("local.txt", "000001 测试股份发布正常公告。")])
    assert enriched["passed_hard_gate"] is False
    assert {row["name"] for row in enriched["hard_exclusions"] if not row["passed"]} == {
        "近3日极端加速且无启动承接",
        "近5日或10日极端加速且无资金承接",
    }


def test_negated_risk_sentence_is_not_a_positive_hit():
    corpus = [("local.txt", "测试股份公告：公司不存在财务造假。")]
    assert ENGINE.text_hits(corpus, "000001", "测试股份", ["财务造假"]) == []
