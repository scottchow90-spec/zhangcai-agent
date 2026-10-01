# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import importlib.util
from copy import deepcopy
from pathlib import Path

from PIL import Image
import pytest

import poster_builder
import daniuxian_analysis
import analysis_scoring


LIGHT_GATE_PATH = Path(__file__).resolve().parents[3] / "scripts" / "poster_light_background_gate.py"
LIGHT_GATE_SPEC = importlib.util.spec_from_file_location("poster_light_background_gate", LIGHT_GATE_PATH)
LIGHT_GATE = importlib.util.module_from_spec(LIGHT_GATE_SPEC)
assert LIGHT_GATE_SPEC.loader is not None
LIGHT_GATE_SPEC.loader.exec_module(LIGHT_GATE)


def index_payload() -> dict:
    names = [
        "主趋势线",
        "均线分层",
        "日线颜色信号",
        "流通市值",
        "短线动量",
        "参与与离场信号",
        "控盘程度",
        "财神短线",
        "庄进与庄出",
        "强势股识别",
        "龙头参与区",
        "龙回头",
        "点火信号",
        "起爆与题材共振",
        "布林线与多重均线",
        "核心黄金分割撑压",
    ]
    rows = []
    for number, name in enumerate(names, start=1):
        rows.append(
            {
                "序号": number,
                "子系统": name,
                "证据": f"{name}已取得当日证据",
                "状态": "偏强" if number not in {4, 9, 10, 11, 12} else "指数不适用",
                "结论": f"{name}按指数口径完成判断",
                "适用性/备注": "适用",
            }
        )
    rows[-1]["证据"] = (
        "支撑一3923.06，支撑二3659.44，压力一4258.86，压力二暂无，"
        "第五输出字段为核心黄金分割有效可见"
    )
    return {
        "status": "CLEAN_PASS",
        "name": "上证指数",
        "code": "000001",
        "trade_date": "2026-08-17",
        "close": 3982.65,
        "change_pct": 1.41,
        "data_source": "本机通达信持久日线",
        "subsystems": rows,
        "assessment": {
            "score": 57,
            "rating": "中性震荡",
            "applicable_subsystems": 11,
            "market_phase": "中期转强未确认的压力区震荡",
            "primary_direction": "中期方向未确认，短线反弹受压",
            "strength_character": "短线修复不等于中期趋势突破",
            "primary_conflict": "短周期主趋势线向上，但中期三项突破条件没有同时确认。",
            "clear_conclusion": (
                "2026-08-17收盘3982.65｜趋势线3895.60向上｜长期EMA最高3961.08、连续2日全站稳否｜"
                "黄金压力4258.86突破否｜下降线核验否｜DX36.26增强｜五维57分；"
                "三闸未齐，不能判定中期偏强，阶段=中期转强未确认的压力区震荡。"
            ),
            "conclusion_provenance": {
                "method": "CURRENT_RUN_EVIDENCE_CLAUSES_V1",
                "fallback_used": False,
                "legacy_fixed_conclusion_match": False,
                "fact_count": 10,
                "trade_date": "2026-08-17",
            },
            "bullish_trigger": "连续两个收盘站稳全部中长期线，突破黄金压力并核验下降趋势线突破。",
            "bearish_trigger": "跌破短期均线并失守主趋势线。",
            "invalidation": "跌破防守位且主趋势线转向下，当前短线修复失效。",
            "action_stance": "保持中性防守，等待三项中期突破条件同时确认。",
            "dimensions": {
                "趋势结构": {"score": 59.0},
                "短线动量": {"score": 71.0},
                "参与强度": {"score": 62.5},
                "进攻信号": {"score": 64.0},
                "位置与风险": {"score": 47.0},
            },
            "medium_term_confirmation": {"status": "UNCONFIRMED"},
        },
    }


def test_index_analysis_poster_is_full_8k_and_preview_readable(tmp_path: Path):
    output = tmp_path / "poster.png"

    validation = poster_builder.render_index_analysis_poster(index_payload(), output)

    preview = tmp_path / "poster-preview-1920x1080.png"
    assert output.is_file()
    assert preview.is_file()
    assert Image.open(output).size == (7680, 4320)
    assert Image.open(preview).size == (1920, 1080)
    assert validation["passed"] is True
    assert validation["subsystem_count"] == 16
    assert validation["minimum_preview_font_px"] >= 24
    assert validation["core_body_preview_font_px"] >= 32
    assert validation["primary_preview_font_px"] >= 34
    assert validation["overlaps"] == []
    assert validation["clipped_text"] == []
    assert validation["support_pressure_visible"] is True
    light_gate = LIGHT_GATE.validate_poster_file(output)
    assert light_gate["status"] == "PASS"
    assert light_gate["metrics"]["minimum_corner_luminance"] >= 230


def test_index_analysis_poster_rejects_unbound_or_legacy_conclusion(tmp_path: Path):
    payload = deepcopy(index_payload())
    payload["assessment"].pop("conclusion_provenance")

    with pytest.raises(RuntimeError, match="结论.*证据"):
        poster_builder.render_index_analysis_poster(payload, tmp_path / "poster.png")

    payload = deepcopy(index_payload())
    payload["assessment"]["conclusion_provenance"]["legacy_fixed_conclusion_match"] = True
    with pytest.raises(RuntimeError, match="结论.*固定"):
        poster_builder.render_index_analysis_poster(payload, tmp_path / "legacy.png")

    payload = deepcopy(index_payload())
    payload["assessment"].pop("clear_conclusion")
    with pytest.raises(RuntimeError, match="结论.*缺失"):
        poster_builder.render_index_analysis_poster(payload, tmp_path / "missing.png")


def test_analysis_payload_keeps_fixed_sixteen_rows_and_source_date():
    sample = index_payload()
    data = {
        "name": sample["name"],
        "code": sample["code"],
        "is_index": True,
        "trade_date": sample["trade_date"],
        "close": sample["close"],
        "change_pct": sample["change_pct"],
        "bar_source": "persisted_tdx_day_only",
        "n_persisted_records": 1222,
        "comprehensive_assessment": sample["assessment"],
        "trend_up": True,
        "main_trend": 3895.60,
        "main_trend_prev": 3889.06,
        "ema5": 3946.23,
        "ema10": 3925.01,
        "ema20": 3913.07,
        "ema173": 3961.08,
        "ema193": 3947.74,
        "ema213": 3932.79,
        "kline_type": "阳",
        "dx": 36.26,
        "dx_dir": "增强",
        "buy_sig": False,
        "sell_sig": False,
        "kongpan": 0.952,
        "kongpan_prev": 0.645,
        "cai": 948.39,
        "shen": 704.82,
        "dianhuo": False,
        "ema3": 3956.63,
        "ema21": 3913.50,
        "kdj_k": 86.98,
        "kdj_d": 83.39,
        "kdj_j": 94.15,
        "macd_bar": 38.32,
        "UB": 3991.44,
        "boll_ma": 3879.71,
        "LB": 3767.99,
        "ma5": 3943.51,
        "ma10": 3922.53,
        "ma20": 3879.71,
        "ma60": 3983.65,
        "support_1": 3923.06,
        "support_2": 3659.44,
        "pressure_1": 4258.86,
        "pressure_2": None,
        "output66": "核心黄金分割有效可见",
        "support_pressure_status": "双向撑压有效",
    }

    payload = daniuxian_analysis.build_analysis_poster_payload(data)

    assert payload["status"] == "CLEAN_PASS"
    assert payload["trade_date"] == "2026-08-17"
    assert payload["data_source"] == "本机通达信日线1222条｜当日栏persisted_tdx_day_only"
    assert [row["序号"] for row in payload["subsystems"]] == list(range(1, 17))
    assert payload["assessment"]["market_phase"] == "中期转强未确认的压力区震荡"


def test_save_analysis_poster_writes_preview_and_validation(tmp_path: Path):
    sample = index_payload()
    data = {
        "name": sample["name"],
        "code": sample["code"],
        "is_index": True,
        "trade_date": sample["trade_date"],
        "close": sample["close"],
        "change_pct": sample["change_pct"],
        "bar_source": "persisted_tdx_day_only",
        "n_persisted_records": 1222,
        "comprehensive_assessment": sample["assessment"],
        "support_1": 3923.06,
        "support_2": 3659.44,
        "pressure_1": 4258.86,
        "pressure_2": None,
        "output66": "核心黄金分割有效可见",
        "support_pressure_status": "双向撑压有效",
    }
    output = tmp_path / "poster.png"
    validation_path = tmp_path / "analysis_poster_validation.json"

    validation = daniuxian_analysis.save_analysis_poster(
        data,
        output,
        validation_path,
    )

    assert validation["passed"] is True
    assert output.is_file()
    assert (tmp_path / "poster-preview-1920x1080.png").is_file()
    assert validation_path.is_file()


def test_analysis_dispatch_requires_poster_and_validation(monkeypatch, tmp_path: Path):
    def fake_run_child(command, timeout=300):
        assert "--poster" in command
        assert "--poster-validation" in command
        report = Path(command[command.index("--output") + 1])
        poster = Path(command[command.index("--poster") + 1])
        validation = Path(command[command.index("--poster-validation") + 1])
        report.write_text("十六子系统完整报告", encoding="utf-8")
        poster.write_bytes(b"poster")
        poster.with_name("poster-preview-1920x1080.png").write_bytes(b"preview")
        validation.write_text('{"passed": true}', encoding="utf-8")
        return {"returncode": 0, "stdout": "ok", "stderr": "", "timed_out": False}

    monkeypatch.setattr(analysis_scoring, "run_child", fake_run_child)

    result = analysis_scoring.run_analysis(tmp_path, ["000001.SH"])

    assert result["status"] == "CLEAN_PASS"
    assert result["artifacts"]["poster"]["validation"]["passed"] is True
    assert Path(result["artifacts"]["poster"]["path"]).is_file()
    assert Path(result["artifacts"]["preview"]["path"]).is_file()
