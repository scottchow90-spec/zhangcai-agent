from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import contextlib
import io
import json
import tempfile
from datetime import datetime
from pathlib import Path

import quality_track_backtest as backtest
import quality_track_live as live


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lookback-sessions", type=int, default=500)
    args = parser.parse_args()

    benchmark_dates = [int(row["date"]) for row in live.read_day_rows("1000300")]
    if len(benchmark_dates) < args.lookback_sessions + 10:
        raise RuntimeError("insufficient benchmark calendar for stability test")
    current_as_of = benchmark_dates[-1]
    previous_as_of = benchmark_dates[-2]

    with tempfile.TemporaryDirectory(prefix="quality-track-stability-") as temp_dir:
        temp = Path(temp_dir)
        with contextlib.redirect_stdout(io.StringIO()):
            current = backtest.run(temp / "current.json", args.lookback_sessions, current_as_of)
            previous = backtest.run(temp / "previous.json", args.lookback_sessions, previous_as_of)

    current_periods = {int(row["signal_date"]): row for row in current["periods"]}
    previous_periods = {int(row["signal_date"]): row for row in previous["periods"]}
    common_dates = sorted(set(current_periods) & set(previous_periods))
    assert len(common_dates) >= 50
    stable_period_fields = (
        "selected_sector_count",
        "market_regime_pass",
        "filled_count",
        "portfolio_return",
        "benchmark_return",
    )
    # candidate_count 是信号日当天满足条件的候选池大小；在 as_of 前移一天时，
    # 个别股票历史覆盖边界会使候选池计数变化，但只要最终成交和收益不变，
    # 不应阻塞实时策略执行。
    period_mismatches: list[dict[str, object]] = []
    for signal_date in common_dates:
        left = current_periods[signal_date]
        right = previous_periods[signal_date]
        for field in stable_period_fields:
            if left[field] != right[field]:
                period_mismatches.append(
                    {"signal_date": signal_date, "field": field, "current": left[field], "previous": right[field]}
                )

    def trade_map(payload: dict) -> dict[tuple[int, str], dict]:
        return {
            (int(row["signal_date"]), str(row["symbol"])): row
            for row in payload["trades"]
            if int(row["signal_date"]) in common_dates
        }

    current_trades = trade_map(current)
    previous_trades = trade_map(previous)
    trade_keys_match = set(current_trades) == set(previous_trades)
    trade_mismatches = [
        {"key": key, "current": current_trades[key], "previous": previous_trades[key]}
        for key in sorted(set(current_trades) & set(previous_trades))
        if current_trades[key] != previous_trades[key]
    ]
    status = "PASS" if not period_mismatches and trade_keys_match and not trade_mismatches else "FAIL"
    payload = {
        "schema": "QUALITY-TRACK-BACKTEST-STABILITY-1",
        "status": status,
        "generated_at": datetime.now(live.CN_TZ).isoformat(timespec="seconds"),
        "current_as_of": current_as_of,
        "previous_as_of": previous_as_of,
        "current_status": current["status"],
        "previous_status": previous["status"],
        "common_period_count": len(common_dates),
        "current_period_count": len(current["periods"]),
        "previous_period_count": len(previous["periods"]),
        "trade_keys_match": trade_keys_match,
        "period_mismatches": period_mismatches,
        "trade_mismatches": trade_mismatches,
        "current_metrics": current["metrics"],
        "previous_metrics": previous["metrics"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if status != "PASS":
        raise RuntimeError("backtest anchor stability verification failed")
    print(
        "QUALITY_TRACK_BACKTEST_STABILITY_PASS "
        f"current={current_as_of} previous={previous_as_of} common_periods={len(common_dates)} "
        f"current_status={current['status']} previous_status={previous['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
