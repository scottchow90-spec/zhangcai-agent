from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import json
import py_compile
from datetime import datetime
from pathlib import Path

import quality_track_live as live
import quality_track_backtest as backtest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = ROOT / "scripts"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "run" / "selftest.json")
    args = parser.parse_args()

    scripts = [
        SCRIPT_DIR / "codex_entry.py",
        SCRIPT_DIR / "quality_track_live.py",
        SCRIPT_DIR / "quality_track_backtest.py",
        SCRIPT_DIR / "paper_monitor.py",
        SCRIPT_DIR / "verify_backtest_stability.py",
        SCRIPT_DIR / "selftest.py",
    ]
    for path in scripts:
        py_compile.compile(str(path), doraise=True)

    names = live.load_names()
    concepts = live.load_concepts()
    news = live.load_news()
    trade_date, coverage = live.complete_trade_date()
    assert len(names) >= 5_000
    assert len(concepts) >= 100
    assert len(news) >= 50
    assert coverage["selected_coverage"] >= coverage["coverage_threshold"]
    assert trade_date <= coverage["latest_observed_date"]
    assert live.map_track("MicroLED") is None
    assert live.map_track("CPO概念") is not None

    assert backtest.matched_benchmark_return(0.10, 0) == 0.0
    assert backtest.matched_benchmark_return(0.10, 1) == backtest.GROSS_EXPOSURE * 0.10
    assert backtest.matched_benchmark_return(-0.10, 5) == backtest.GROSS_EXPOSURE * -0.10

    quote_fields = [""] * 39
    quote_fields[1] = "浦发银行"
    quote_fields[2] = "600000"
    quote_fields[3] = "9.01"
    quote_fields[4] = "8.95"
    quote_fields[5] = "8.93"
    quote_fields[30] = "20260722150634"
    quote_fields[33] = "9.01"
    quote_fields[34] = "8.78"
    quote_fields[35] = "9.01/793111/705276460"
    quote_fields[36] = "793111"
    quote_fields[37] = "70528"
    sample_batch = live.parse_tencent_batch_bars(
        f'v_sh600000="{"~".join(quote_fields)}";',
        20260722,
        {"sh600000": "1600000"},
    )
    assert sample_batch["1600000"]["amount"] == 705276460.0
    assert sample_batch["1600000"]["volume"] == 79311100

    routine = live.classify_announcement_title(
        "2025年度非经营性资金占用及其他关联资金往来情况汇总表"
    )
    assert routine["routine_fund_occupation_audit"] is True
    assert routine["severe_risk_terms"] == []

    role = live.verify_business_role(
        {"membership_evidence": [{"concept": "PCB概念"}]},
        {"latest_composition": [{"category": "按产品分类", "business": "印制电路板", "revenue_ratio": 0.94}]},
    )
    assert role["verified"] is True

    candidate_fixture = [
        {
            "symbol": "000001.SZ",
            "disposition": "PAPER_ELIGIBLE",
            "role_evidence": {"verified": True},
            "paper_plan": {"max_portfolio_weight_pct": 10.0, "portfolio_scaled_weight_pct": 10.0},
        },
        {
            "symbol": "000002.SZ",
            "disposition": "REVIEW",
            "role_evidence": {"verified": True},
            "paper_plan": {"max_portfolio_weight_pct": 0.0},
        },
        {
            "symbol": "000003.SZ",
            "disposition": "WATCH_ONLY",
            "role_evidence": {"verified": True},
            "paper_plan": {"max_portfolio_weight_pct": 0.0},
        },
        {
            "symbol": "000004.SZ",
            "disposition": "REVIEW",
            "role_evidence": {"verified": False},
            "paper_plan": {"max_portfolio_weight_pct": 0.0},
        },
        {
            "symbol": "000005.SZ",
            "disposition": "EXCLUDE",
            "role_evidence": {"verified": True},
            "paper_plan": {"max_portfolio_weight_pct": 0.0},
        },
    ]
    paper_eligible, selected, watch_candidates = live.partition_candidate_lists(candidate_fixture, 5)
    assert {item["symbol"] for item in selected} == {"000001.SZ"}
    assert {item["symbol"] for item in watch_candidates} == {"000002.SZ", "000003.SZ"}
    assert not ({item["symbol"] for item in selected} & {item["symbol"] for item in watch_candidates})
    candidate_counts = {
        "paper_eligible": len(paper_eligible),
        "selected": len(selected),
        "watch_candidates": len(watch_candidates),
    }
    live.validate_candidate_partitions(paper_eligible, selected, watch_candidates, candidate_counts)
    try:
        live.validate_candidate_partitions(
            paper_eligible,
            selected,
            [selected[0]],
            {"paper_eligible": 1, "selected": 1, "watch_candidates": 1},
        )
    except RuntimeError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("selected/watch overlap must fail validation")

    payload = {
        "schema": "QUALITY-TRACK-SKILL-SELFTEST-1",
        "status": "PASS",
        "generated_at": datetime.now(live.CN_TZ).isoformat(timespec="seconds"),
        "counts": {"equity_names": len(names), "concepts": len(concepts), "news": len(news)},
        "complete_trade_date": trade_date,
        "coverage": coverage,
        "scripts": [
            {"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in scripts
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        "QUALITY_TRACK_SKILL_SELFTEST_PASS "
        f"names={len(names)} concepts={len(concepts)} news={len(news)} trade_date={trade_date}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
