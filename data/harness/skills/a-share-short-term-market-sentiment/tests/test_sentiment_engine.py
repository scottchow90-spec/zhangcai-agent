from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "scripts" / "sentiment_engine.py"
LIVE_PATH = ROOT / "scripts" / "live_snapshot.py"
LEGACY_PATH = ROOT / "scripts" / "legacy_codex_entry.py"
RUNTIME_PATH = Path(r"D:\C盘转移\日志\codex\scripts\stock_canonical_runtime.py")
ASSET = Path(
    r"D:\C盘转移\日志\codex\skills\a-share-hotspot-sentiment-analysis\references\core-assets\三万字讲透_情绪周期.pdf"
)
ASSET_SHA256 = "8e3eaf9ab79b4d6c37b21810f68656dd1f6533794fdd23c54ce58ee6b505970e"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_pdf_strict_analysis_outputs_explicit_stage_without_numeric_score() -> None:
    engine = load_module(ENGINE_PATH, "sentiment_engine_test")
    result = engine.analyze_snapshot(engine.example_snapshot("mixed"))

    assert result["analysis_mode"] == "pdf_strict_multi_cycle"
    assert "score" not in result
    assert "sentiment_state" not in result
    assert "cycle_stage" not in result
    conclusion = result["single_stage_conclusion"]
    assert conclusion["status"] == "DETERMINED"
    assert conclusion["stage"] == "赚钱效应低迷"
    assert conclusion["conclusion"].startswith("当前中级周期处于")
    assert conclusion["evidence"]
    assert isinstance(conclusion["conflicts"], list)
    assert conclusion["conflict_statement"]
    short_stage = result["short_term_stage_conclusion"]
    assert short_stage["status"] == "DETERMINED"
    assert short_stage["stage"] == "分歧期"
    assert short_stage["conclusion"].startswith("当前短线市场情绪处于分歧期")
    assert short_stage["evidence"]
    assert isinstance(short_stage["conflicts"], list)
    assert short_stage["conflict_statement"]
    assert set(result["cycles"]) == {
        "index_cycle",
        "theme_cycle",
        "leader_cycle",
        "profit_loss_cycle",
        "intermediate_cycle",
    }
    assert result["cycles"]["index_cycle"]["stage_status"] == "INSUFFICIENT_EVIDENCE"
    assert "五类指数分时" in result["cycles"]["index_cycle"]["evidence_limit"]
    assert result["cycles"]["theme_cycle"]["stage_status"] == "DETERMINED"
    assert "具体题材内部" in result["cycles"]["theme_cycle"]["evidence_limit"]


def test_20260818_ice_and_fire_snapshot_is_divergence_and_emerging_loss() -> None:
    engine = load_module(ENGINE_PATH, "sentiment_engine_20260818_regression")
    snapshot = engine.example_snapshot("mixed")
    snapshot["trading_date"] = "2026-08-18"
    snapshot["market"].update(
        index_change_pct=0.192,
        advancers=2119,
        decliners=3292,
        total_amount_billion=24362.1,
        amount_change_pct=0.63,
        limit_up=79,
        limit_down=5,
        consecutive=18,
        max_board=4,
        seal_rate=77.5,
        broken_board=23,
        topic_top_count=23,
        topic_count_ge3=8,
    )
    snapshot["comparisons"] = {
        "previous_trading_day": {
            "advancers": 4336,
            "decliners": 1062,
            "limit_up": 106,
            "limit_down": 1,
            "consecutive": 15,
            "broken_board": 12,
            "seal_rate": 89.8,
        }
    }
    for source in snapshot["sources"].values():
        source["trading_date"] = "2026-08-18"
    snapshot["sources"]["lianban"]["reported_stage"] = "降温期"

    result = engine.analyze_snapshot(snapshot)

    assert result["short_term_stage_conclusion"]["stage"] == "分歧期"
    assert result["single_stage_conclusion"]["stage"] == "亏钱效应出现"
    for fact in ("106家降至79家", "89.8%降至77.5%", "12家升至23家", "1家升至5家"):
        assert fact in result["short_term_stage_conclusion"]["conclusion"]
        assert fact in result["single_stage_conclusion"]["conclusion"]
    for forbidden in ("核心延续，跟风转弱", "跟风弱于核心", "呈现冰火并存", "以当次多周期证据为准"):
        assert forbidden not in result["short_term_stage_conclusion"]["conclusion"]
        assert forbidden not in result["single_stage_conclusion"]["conclusion"]


def test_pdf_five_stage_examples_always_have_a_clear_conclusion() -> None:
    engine = load_module(ENGINE_PATH, "sentiment_engine_five_stages")
    expected = {
        "strong": ("赚钱效应高潮", "高潮期"),
        "mixed": ("赚钱效应低迷", "分歧期"),
        "retreat": ("亏钱效应炸裂", "退潮期"),
    }
    for name, (stage, short_stage) in expected.items():
        result = engine.analyze_snapshot(engine.example_snapshot(name))
        conclusion = result["single_stage_conclusion"]
        assert conclusion["status"] == "DETERMINED"
        assert conclusion["stage"] == stage
        assert conclusion["conclusion"]
        assert conclusion["confidence"] in {"HIGH", "MEDIUM", "LOW"}
        assert conclusion["evidence"]
        assert conclusion["conflict_statement"]
        assert result["short_term_stage_conclusion"]["stage"] == short_stage
        assert result["short_term_stage_conclusion"]["conclusion"]
        assert result["short_term_stage_conclusion"]["conflict_statement"]


def test_pdf_topic_cycle_can_conclude_fermentation_stage() -> None:
    engine = load_module(ENGINE_PATH, "sentiment_engine_fermentation")
    snapshot = engine.example_snapshot("mixed")
    snapshot["market"].update(
        index_change_pct=0.7,
        advancers=3500,
        decliners=1600,
        amount_change_pct=8,
        limit_up=70,
        limit_down=4,
        consecutive=16,
        max_board=5,
        seal_rate=78,
        broken_board=14,
        topic_top_count=13,
        topic_count_ge3=6,
    )
    snapshot["comparisons"]["previous_trading_day"].update(
        limit_up=50,
        limit_down=6,
        consecutive=18,
        seal_rate=80,
        broken_board=20,
    )
    result = engine.analyze_snapshot(snapshot)
    assert result["short_term_stage_conclusion"]["stage"] == "发酵期"


def test_missing_required_metric_fails_closed() -> None:
    engine = load_module(ENGINE_PATH, "sentiment_engine_missing")
    snapshot = engine.example_snapshot("strong")
    del snapshot["market"]["limit_down"]
    try:
        engine.analyze_snapshot(snapshot)
    except engine.SnapshotValidationError as exc:
        assert "limit_down" in str(exc)
    else:
        raise AssertionError("missing metric was accepted")


def test_missing_previous_metric_fails_closed_instead_of_reusing_current_value() -> None:
    engine = load_module(ENGINE_PATH, "sentiment_engine_missing_previous")
    snapshot = engine.example_snapshot("strong")
    del snapshot["comparisons"]["previous_trading_day"]["seal_rate"]
    try:
        engine.analyze_snapshot(snapshot)
    except engine.SnapshotValidationError as exc:
        assert "missing_previous_metrics:seal_rate" in str(exc)
    else:
        raise AssertionError("missing previous metric reused a current-day value")


def test_source_dates_must_match() -> None:
    engine = load_module(ENGINE_PATH, "sentiment_engine_dates")
    snapshot = engine.example_snapshot("strong")
    snapshot["sources"]["duanxianxia"]["trading_date"] = "2026-08-13"
    try:
        engine.analyze_snapshot(snapshot)
    except engine.SnapshotValidationError as exc:
        assert "source_date_mismatch" in str(exc)
    else:
        raise AssertionError("date mismatch was accepted")


def test_core_asset_is_a_unique_external_reference() -> None:
    metadata = json.loads((ROOT / "references" / "source-asset.json").read_text(encoding="utf-8"))
    assert Path(metadata["canonical_pdf"]) == ASSET
    assert metadata["sha256"] == ASSET_SHA256
    assert hashlib.sha256(ASSET.read_bytes()).hexdigest() == ASSET_SHA256
    assert not list(ROOT.rglob("*.pdf"))


def test_live_builder_uses_reported_previous_day_counts_without_price_threshold_guessing(
    tmp_path: Path,
) -> None:
    live = load_module(LIVE_PATH, "live_snapshot_test")
    lianban_path = tmp_path / "lianban-live.json"
    duanxian_path = tmp_path / "duanxian-live.json"
    tdx_root = tmp_path / "TDX"
    sh_lday = tdx_root / "vipdoc" / "sh" / "lday"
    sh_lday.mkdir(parents=True)
    for market in ("sz", "bj"):
        (tdx_root / "vipdoc" / market / "lday").mkdir(parents=True)

    def write_day(path: Path, closes: tuple[int, int, int]) -> None:
        rows = []
        for date_i, close_i in zip((20260812, 20260813, 20260814), closes):
            rows.append(
                live.DAY.pack(
                    date_i,
                    close_i,
                    close_i,
                    close_i,
                    close_i,
                    100_000_000.0,
                    1000,
                    0,
                )
            )
        path.write_bytes(b"".join(rows))

    write_day(sh_lday / "sh000001.day", (390000, 392000, 394000))
    for prefix in ("600", "601", "603"):
        for index in range(1000):
            closes = (
                (1000, 1001, 1002)
                if index % 2 == 0
                else (1002, 1001, 1000)
            )
            write_day(sh_lday / f"sh{prefix}{index:03d}.day", closes)

    lianban_path.write_text(
        json.dumps(
            {
                "status": "CLEAN_PASS",
                "target_date": "2026-08-14",
                "sources": {
                    "open_data": {"status_code": 200},
                    "page": {
                        "status_code": 200,
                        "url": "https://lianban.net/days/2026-08-14.html",
                    },
                },
                "market": {
                    "limit_up": 59,
                    "limit_down": 4,
                    "consecutive": 22,
                    "max_board": 5,
                    "seal_rate": 62.1,
                    "broken_board": 36,
                    "emotion_stage": "退潮期",
                },
                "topics": [{"name": "医药", "count": 14}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    duanxian_path.write_text(
        json.dumps(
            {
                "source_page": "https://duanxianxia.com/",
                "datasets": {
                    "ztcount": {"success": True, "data": {}},
                    "jinjidata": {
                        "success": True,
                        "data": {"date": "2026-08-14"},
                    },
                    "amount": {"success": True, "data": {}},
                    "ztpool": {
                        "success": True,
                        "data": {
                            "count": {
                                "zt": 59,
                                "limit_up_count": {
                                    "today": {"num": 59},
                                    "yesterday": {
                                        "num": 92,
                                        "lbnum": 22,
                                        "open_num": 12,
                                        "rate": 0.885,
                                    },
                                },
                                "limit_down_count": {
                                    "yesterday": {"num": 4}
                                },
                            },
                            "list": [],
                        },
                    },
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    snapshot = live.build_snapshot(
        lianban_path=lianban_path,
        duanxian_path=duanxian_path,
        tdx_root=tdx_root,
    )
    assert snapshot["trading_date"] == "2026-08-14"
    assert snapshot["sources"]["lianban"]["verified"] is True
    assert snapshot["sources"]["duanxianxia"]["verified"] is True
    assert snapshot["sources"]["tongdaxin"]["verified"] is True
    assert "prior_limit_up_threshold" not in LIVE_PATH.read_text(encoding="utf-8")
    assert "yesterday_limit_up_return" not in snapshot["market"]
    previous = snapshot["comparisons"]["previous_trading_day"]
    assert previous["consecutive"] == 22
    assert previous["limit_down"] == 4

    duan_payload = json.loads(duanxian_path.read_text(encoding="utf-8"))
    del duan_payload["datasets"]["ztpool"]["data"]["count"]["limit_up_count"]["yesterday"]["num"]
    duanxian_path.write_text(json.dumps(duan_payload, ensure_ascii=False), encoding="utf-8")
    try:
        live.build_snapshot(
            lianban_path=lianban_path,
            duanxian_path=duanxian_path,
            tdx_root=tdx_root,
        )
    except ValueError as exc:
        assert "duanxianxia_previous_metrics_missing" in str(exc)
    else:
        raise AssertionError("missing previous-day metric used a numeric fallback")


def test_direct_legacy_execution_is_blocked() -> None:
    env = {k: v for k, v in os.environ.items() if k != "ONESTOCK_STOCK_CANONICAL_CHILD"}
    completed = subprocess.run(
        [sys.executable, str(LEGACY_PATH), "run", "--snapshot", "missing.json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    assert completed.returncode == 2
    assert "canonical_stock_legacy_entry_direct_execution_blocked" in completed.stderr


def test_canonical_lianban_prefetch_can_resolve_latest_trading_day() -> None:
    runtime = load_module(RUNTIME_PATH, "stock_runtime_latest_test")
    command = runtime.lianban_client_command(
        Path(r"D:\C盘转移\日志\codex\scripts\lianban_daily_client.py"),
        Path(r"C:\temp\lianban-daily.json"),
        "2026-08-16",
        "latest_available",
    )
    assert "--date" not in command
    assert "--latest" in command
    assert command[-2:] == ["--output", r"C:\temp\lianban-daily.json"]
