# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("daniuxian_analysis.py")
SPEC = importlib.util.spec_from_file_location("daniuxian_analysis", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def shanghai_index_fixture():
    return {
        "is_index": True,
        "close": 3926.96,
        "open": 3957.15,
        "high": 3968.47,
        "low": 3924.63,
        "last_close": 3946.67,
        "change_pct": -0.50,
        "main_trend": 3878.38,
        "main_trend_prev": 3872.50,
        "trend_up": True,
        "ema5": 3929.17,
        "ema10": 3904.85,
        "ema20": 3901.02,
        "ema173": 3961.62,
        "ema193": 3947.80,
        "ema213": 3932.42,
        "bullish": True,
        "kline_type": "阴",
        "body": 30.19,
        "upper_shadow": 11.32,
        "lower_shadow": 2.33,
        "dx": 40.24,
        "dx_prev": 42.00,
        "dx_dir": "减弱",
        "buy_sig": False,
        "sell_sig": False,
        "kongpan": 0.5352,
        "kongpan_prev": 0.2838,
        "cai": 500.1468,
        "shen": 139.4270,
        "zhuangjin": False,
        "zhuangchu": False,
        "is_zt": False,
        "lht": False,
        "dianhuo": False,
        "ema3": 3941.11,
        "ema21": 3902.29,
        "jincha_kdj": True,
        "kdj_k": 87.11,
        "kdj_d": 81.40,
        "kdj_j": 98.54,
        "macd_bar": 43.60,
        "dif": -9.87,
        "dea": -31.67,
        "rsi6": 65.0,
        "rsi14": 54.0,
        "wr10": 10.0,
        "UB": 3969.47,
        "boll_ma": 3860.02,
        "LB": 3750.56,
        "ma5": 3937.55,
        "ma10": 3883.51,
        "ma20": 3860.02,
        "ma60": 3992.24,
        "nearest_support": 3659.44,
        "nearest_pressure": 4258.86,
        "pressure_1": 4258.86,
        "pressure_2": None,
        "downtrend_breakout_verified": False,
        "support_pressure_status": "双向撑压有效",
    }


def test_index_below_long_term_lines_and_unbroken_pressure_is_not_medium_bullish():
    result = MODULE.build_comprehensive_assessment(shanghai_index_fixture())

    assert result["applicable_subsystems"] == 11
    assert result["excluded_subsystems"] == [4, 9, 10, 11, 12]
    assert set(result["dimensions"]) == {
        "趋势结构",
        "短线动量",
        "参与强度",
        "进攻信号",
        "位置与风险",
    }
    assert result["rating"] not in {"中性偏多", "偏多", "强势偏多"}
    assert result["market_phase"] == "中期转强未确认的压力区震荡"
    assert result["primary_direction"] == "中期方向未确认，短线反弹受压"
    assert "不能判定中期偏强" in result["clear_conclusion"]
    assert result["medium_term_confirmation"]["status"] == "UNCONFIRMED"
    assert result["medium_term_confirmation"]["above_all_long_emas"] is False
    assert result["medium_term_confirmation"]["golden_pressure_broken"] is False
    assert result["medium_term_confirmation"]["downtrend_breakout_verified"] is False
    assert result["medium_term_confirmation"]["reasons"] == [
        "收盘未站稳全部中长期趋势线",
        "黄金分割压力位未突破",
        "下降趋势线突破未核验",
    ]
    assert result["bullish_trigger"]
    assert result["bearish_trigger"]
    assert result["invalidation"]
    provenance = result["conclusion_provenance"]
    assert provenance["method"] == "CURRENT_RUN_EVIDENCE_CLAUSES_V1"
    assert provenance["fallback_used"] is False
    assert provenance["legacy_fixed_conclusion_match"] is False
    assert provenance["fact_count"] >= 8
    assert "2026-" not in result["clear_conclusion"]  # fixture has no trade date to invent
    for token in ("3926.96", "3878.38", "3961.62", "4258.86", "40.24", "57分"):
        assert token in result["clear_conclusion"]
    assert "多空证据接近平衡，当前属于震荡等待确认" not in result["clear_conclusion"]


def test_unverified_zero_snapshot_cannot_replace_latest_persisted_bar():
    records = [
        {"date": "2026-08-14", "O": 3900.0, "H": 3940.0, "L": 3890.0, "C": 3927.18, "V": 400000000, "A": 900000000000.0},
        {"date": "2026-08-17", "O": 3930.10, "H": 3983.51, "L": 3924.47, "C": 3982.65, "V": 489834027, "A": 1112818560000.0},
    ]
    snapshot = {
        "Now": 0.0,
        "LastClose": 3927.18,
        "Open": 0.0,
        "Max": 0.0,
        "Min": 0.0,
        "Volume": 0,
        "Amount": 0.0,
        "Average": 3927.18,
        "Inside": 0,
        "Outside": 0,
    }

    quote = MODULE.resolve_quote_fields(
        records,
        snapshot,
        {"bar_source": "persisted_tdx_day_only", "snapshot_date_verified": False},
    )

    assert quote["close"] == 3982.65
    assert quote["open"] == 3930.10
    assert quote["high"] == 3983.51
    assert quote["low"] == 3924.47
    assert quote["last_close"] == 3927.18
    assert quote["volume"] == 489834027
    assert quote["amount"] == 111281856.0
    assert quote["source"] == "persisted_tdx_day_only"


def test_formatted_report_contains_decision_not_only_signal_rows():
    data = shanghai_index_fixture()
    data.update(
        {
            "name": "上证指数",
            "code": "000001",
            "trade_date": "2026-08-12",
            "formula_runtime_name": "大牛线撑压版",
            "bar_source": "persisted_tdx_day_only",
            "local_last_date": "2026-08-12",
            "snapshot_fetched_at": "2026-08-13T16:47:57",
            "n_persisted_records": 1219,
            "volume": 572793677,
            "amount": 116420312.0,
            "avg": 3909.87,
            "inside": 306319165,
            "outside": 266474534,
            "main_trend_tq": 3883.92,
            "ema173_tq": 3961.17,
            "ema193_tq": 3947.46,
            "ema213_tq": 3932.10,
            "float_cap": 0.0,
            "zt_price": 0.0,
            "dt_price": 0.0,
            "blocks": "",
            "j_zgb": 0.0,
            "j_jzc": 0.0,
            "j_mgjzc": 0.0,
            "j_mgsy": 0.0,
            "zjj_reserved_error": "",
            "zjj_v": {},
            "o3": "0.00",
            "o4": "0.00",
            "o5": "0.00",
            "o6": "0.00",
            "o9": "0.00",
            "cb_ratio": 1.0,
            "zt_13d": 0,
            "lht_ref_pp45": False,
            "lht_ref_pp20": False,
            "cp": 62.62,
            "support_1": 3659.44,
            "support_2": None,
            "pressure_1": 4258.86,
            "pressure_2": None,
            "output66": "核心黄金分割: 有效可见 防近线/防压缩",
        }
    )
    analyzer = object.__new__(MODULE.DaniuxianAnalyzer)

    report = analyzer.format_report(data)

    assert "短周期主趋势线向上，仅说明短线修复，不代表中期偏多" in report
    assert "五维综合评分" in report
    assert "市场阶段:中期转强未确认的压力区震荡" in report
    assert "主方向:中期方向未确认，短线反弹受压" in report
    assert "中期确认闸:UNCONFIRMED" in report
    assert "不能判定中期偏强" in report
    assert "核心矛盾:" in report
    assert "明确结论:" in report
    assert "转强条件:" in report
    assert "转弱条件:" in report
    assert "失效条件:" in report
