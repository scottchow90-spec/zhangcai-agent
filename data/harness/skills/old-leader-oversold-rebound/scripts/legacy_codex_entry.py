from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import csv
import json
import tempfile
from pathlib import Path

from scan_old_leader_rebound import (
    Bar,
    limit_flags,
    load_fresh_limit_bars,
    market_for,
    max_streak,
    parse_trade_date,
    rolling_dates,
    scan,
    write_outputs,
)


SKILL_INFO = {
    "skill": "old-leader-oversold-rebound",
    "display_name": "老龙头超跌反弹",
    "version": "1.1.0",
    "entrypoints": ["info", "selftest", "run"],
    "criteria": {
        "strict_old_leader": ">=4 consecutive limit-ups",
        "compatible_old_leader": ">=4 limit-ups in 10 sessions and max streak <4",
        "old_cycle_rise": ">=100%",
        "drawdown": ">=30%",
        "peak_to_rebound": ">=10 sessions",
        "rebound": ">=2 consecutive limit-ups or >=2 limit-ups in 3 sessions",
        "limit_up": "10cm >=9.8%; 20cm >=19.8%; high=close",
    },
    "classification": ["核心", "观察", "剔除"],
    "catalyst_rule": "Only pre-launch or same-time catalysts can explain launch; later news is post-hoc reinforcement.",
}


def add_common_scan_arguments(
    parser: argparse.ArgumentParser,
    include_outputs: bool,
    require_as_of: bool,
) -> None:
    if require_as_of:
        parser.add_argument("--as-of", required=True, help="YYYY-MM-DD or YYYYMMDD")
    else:
        parser.add_argument("--as-of", default="2026-07-29", help="YYYY-MM-DD or YYYYMMDD")
    parser.add_argument("--tdx", type=Path, default=Path(r"C:\new_tdx_mock"))
    parser.add_argument("--fresh-limit-csv", type=Path)
    if include_outputs:
        parser.add_argument("--json", type=Path, required=True)
        parser.add_argument("--csv", type=Path, required=True)


def logic_selftest() -> None:
    bar = lambda day, close, high=None: Bar(day, close, high or close, close, close, 0.0, 0)
    ten = [bar(20260101, 10.0), bar(20260102, 10.98)]
    twenty = [bar(20260101, 10.0), bar(20260102, 11.98)]
    assert limit_flags(ten, "10cm") == [False, True]
    assert limit_flags(twenty, "20cm") == [False, True]
    assert market_for("sh", "688001") == "20cm"
    assert market_for("sh", "689009") == "20cm"
    assert max_streak([False, True, True, False, True], 0, 4) == 2
    assert parse_trade_date("2026-07-29") == 20260729
    assert rolling_dates(20260729) == (20250729, 20260601, 20250101)
    with tempfile.TemporaryDirectory(prefix="old-leader-input-test-") as tmp:
        invalid_csv = Path(tmp) / "invalid.csv"
        invalid_csv.write_text("wrong,header\n1,2\n", encoding="utf-8")
        try:
            load_fresh_limit_bars(invalid_csv, 20260729)
        except ValueError as exc:
            assert "missing columns" in str(exc)
        else:
            raise AssertionError("Invalid fresh limit-up CSV schema was accepted")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def regression_selftest(args: argparse.Namespace) -> dict:
    if args.baseline_csv is None:
        return {"status": "PASS", "logic_selftest": True, "regression": "not_requested"}
    if not args.baseline_csv.is_file():
        raise FileNotFoundError(f"Baseline CSV not found: {args.baseline_csv}")
    if args.fresh_limit_csv is not None and not args.fresh_limit_csv.is_file():
        raise FileNotFoundError(f"Fresh limit-up CSV not found: {args.fresh_limit_csv}")

    as_of = parse_trade_date(args.as_of)
    result = scan(args.tdx, as_of, args.fresh_limit_csv)
    with tempfile.TemporaryDirectory(prefix="old-leader-rebound-") as tmp:
        generated_csv = Path(tmp) / "generated.csv"
        write_outputs(result, Path(tmp) / "generated.json", generated_csv)
        actual = read_csv_rows(generated_csv)
        expected = read_csv_rows(args.baseline_csv)

    if actual != expected:
        first_difference = next(
            (index for index, pair in enumerate(zip(actual, expected), 1) if pair[0] != pair[1]),
            min(len(actual), len(expected)) + 1,
        )
        raise AssertionError(
            f"Regression mismatch: actual={len(actual)}, expected={len(expected)}, first_difference={first_difference}"
        )

    by_code = {row["code"]: row for row in actual}
    for code, name in (("600722", "金牛化工"), ("600227", "赤天化")):
        row = by_code.get(code)
        if row is None:
            raise AssertionError(f"Required correction sample missing: {name} ({code})")
        if row["old_class"] != "broken_4_in_10" or int(row["old_max_streak"]) >= 4:
            raise AssertionError(f"Required correction sample misclassified: {name} ({code})")

    if as_of == 20260729 and len(actual) != 42:
        raise AssertionError(f"2026-07-29 baseline must contain 42 candidates, got {len(actual)}")
    return {
        "status": "PASS",
        "logic_selftest": True,
        "regression": "exact_match",
        "as_of": as_of,
        "candidate_count": len(actual),
        "required_samples": {
            "600722": by_code["600722"]["old_class"],
            "600227": by_code["600227"]["old_class"],
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="old-leader-oversold-rebound")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("info", help="Show the fixed business contract")

    selftest = subparsers.add_parser("selftest", help="Run logic checks and optional baseline regression")
    add_common_scan_arguments(selftest, include_outputs=False, require_as_of=False)
    selftest.add_argument("--baseline-csv", type=Path)

    run = subparsers.add_parser("run", help="Run the mechanical candidate scan")
    add_common_scan_arguments(run, include_outputs=True, require_as_of=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "info":
        print(json.dumps(SKILL_INFO, ensure_ascii=False, indent=2))
        return
    if args.command == "selftest":
        logic_selftest()
        print(json.dumps(regression_selftest(args), ensure_ascii=False, indent=2))
        return

    as_of = parse_trade_date(args.as_of)
    result = scan(args.tdx, as_of, args.fresh_limit_csv)
    write_outputs(result, args.json, args.csv)
    print(json.dumps({
        "status": "PASS",
        "as_of": as_of,
        "max_trade_date": result["max_trade_date"],
        "files_scanned": result["files_scanned"],
        "candidate_count": result["candidate_count"],
        "json": str(args.json.resolve()),
        "csv": str(args.csv.resolve()),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    main()
