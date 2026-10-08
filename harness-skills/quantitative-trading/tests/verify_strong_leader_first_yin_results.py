# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import importlib.util
import json
from pathlib import Path


SELECTOR = Path(r"D:\C盘转移\日志\codex\skills\dragon-pullback\reports\strong-leader-first-yin-latest.json")
BACKTEST = Path(r"D:\C盘转移\日志\codex\skills\quantitative-trading\reports\strong-leader-first-yin-backtest-latest.json")
RESEARCH = Path(r"D:\C盘转移\日志\codex\skills\quantitative-trading\reports\strong-leader-first-yin-walk-forward-research.json")
TDX_HUB = Path(r"D:\C盘转移\日志\codex\skills\tdx-local-hub\scripts\tdx_hub.py")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> None:
    selector = json.loads(SELECTOR.read_text(encoding="utf-8-sig"))
    backtest = json.loads(BACKTEST.read_text(encoding="utf-8"))
    research = json.loads(RESEARCH.read_text(encoding="utf-8"))

    selection = selector["selection"]
    turnover = selection["turnover_divergence_candidates"]
    practical = selection["practical_candidates"]
    assert selector["status"] == "CLEAN_PASS"
    assert selector["latest_trade_date"] == "20260722"
    assert selection["strict_count"] == 0
    assert selection["turnover_divergence_count"] == 1
    assert selection["practical_count"] == 1
    assert selection["technical_trade_ready_count"] == 0
    assert any(x["symbol"] == "002432.SZ" and x["name"] == "九安医疗" for x in turnover)
    assert any(x["symbol"] == "001369.SZ" and x["name"] == "双欣材料" for x in practical)

    assert backtest["status"] == "CLEAN_PASS"
    assert backtest["backtest_completed"] is True
    assert backtest["strategy_verdict"] == "FAIL"
    assert backtest["data"]["signal_period"] == {"start": "20230526", "end": "20260702"}
    ready = backtest["event_study"]["trade_ready_S_plus_T"]["adaptive_five_session"]
    portfolio = backtest["portfolio_simulation"]["trade_ready_S_plus_T"]
    assert ready["trades"] == 100
    assert ready["mean_net_return_pct"] == -1.4793
    assert ready["win_rate_pct"] == 30.0
    assert ready["profit_factor"] == 0.6871
    assert portfolio["total_return_pct"] == -13.1673
    assert portfolio["max_drawdown_pct"] == -18.958
    assert all(backtest["validation"].values())
    assert len(backtest["data"]["source_snapshot_sha256"]) == 64

    assert research["status"] == "CLEAN_PASS"
    assert research["research_verdict"] == "NO_ROBUST_VARIANT_FOUND"
    assert research["all_gate_pass_count"] == 0
    assert research["multiple_comparisons"] == 60

    hub = load_module(TDX_HUB, "tdx_hub_verify")
    tdx_rows = hub.read_records(hub.day_path("002432.SZ"), hub.DAY_RECORD, hub.parse_day_record, 1)
    assert len(tdx_rows) == 1
    assert str(tdx_rows[0]["date"]) == "20260722"
    assert float(tdx_rows[0]["close"]) == 81.64

    print(
        json.dumps(
            {
                "status": "PASS",
                "selector_latest_trade_date": "20260722",
                "selector_counts": {"S": 0, "T": 1, "A": 1, "trade_ready": 0},
                "turnover_candidate": "002432.SZ 九安医疗",
                "practical_candidate": "001369.SZ 双欣材料",
                "tdx_002432_latest": {"date": "20260722", "close": 81.64},
                "backtest_verdict": "FAIL",
                "trade_ready_adaptive": ready,
                "trade_ready_portfolio": {
                    "total_return_pct": portfolio["total_return_pct"],
                    "max_drawdown_pct": portfolio["max_drawdown_pct"],
                },
                "walk_forward_research": "NO_ROBUST_VARIANT_FOUND",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
