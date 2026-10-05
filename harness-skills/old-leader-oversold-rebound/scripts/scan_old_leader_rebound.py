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
import struct
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


RECORD = struct.Struct("<5If2I")
MIN_PEAK_TO_REBOUND_SESSIONS = 10

CSV_FIELDS = [
    "code", "name", "market", "mechanism", "old_kind", "old_class", "old_start", "old_end",
    "old_max_streak", "old_limit_up_count", "base_date", "base_close", "peak_date",
    "peak_high", "rise_pct", "trough_date", "trough_low", "drawdown_pct",
    "rebound_kind", "rebound_start", "rebound_end", "rebound_streak", "rebound_limit_dates",
    "old_to_rebound_sessions", "peak_to_rebound_sessions",
]


@dataclass(frozen=True)
class Bar:
    date: int
    open: float
    high: float
    low: float
    close: float
    amount: float
    volume: int


def load_names(path: Path) -> dict[str, str]:
    names: dict[str, str] = {}
    for line in path.read_text(encoding="gb18030", errors="replace").splitlines():
        parts = line.split("|", 2)
        if len(parts) >= 2 and len(parts[0]) == 6:
            names[parts[0]] = parts[1].strip()
    return names


def market_for(prefix: str, code: str) -> str | None:
    if prefix == "sh" and code.startswith(("600", "601", "603", "605")):
        return "10cm"
    if prefix == "sh" and code.startswith(("688", "689")):
        return "20cm"
    if prefix == "sz" and code.startswith(("000", "001", "002", "003")):
        return "10cm"
    if prefix == "sz" and code.startswith(("300", "301")):
        return "20cm"
    return None


def load_bars(path: Path, minimum_date: int, maximum_date: int) -> list[Bar]:
    raw = path.read_bytes()
    bars: list[Bar] = []
    for offset in range(0, len(raw) - RECORD.size + 1, RECORD.size):
        date, op, high, low, close, amount, volume, _ = RECORD.unpack_from(raw, offset)
        if date < minimum_date or date > maximum_date or not close:
            continue
        bars.append(Bar(date, op / 100, high / 100, low / 100, close / 100, amount, volume))
    return bars


def load_fresh_limit_bars(path: Path | None, fresh_date: int) -> dict[str, Bar]:
    if path is None:
        return {}
    if not path.is_file():
        raise FileNotFoundError(f"Fresh limit-up CSV not found: {path}")
    rows: dict[str, Bar] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"代码", "最新价", "数据确认"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Fresh limit-up CSV missing columns: {', '.join(sorted(missing))}")
        for row in reader:
            code = row.get("代码", "").strip()
            if len(code) != 6 or row.get("数据确认") != "当日涨停池确认":
                continue
            close = float(row["最新价"])
            rows[code] = Bar(
                date=fresh_date,
                open=close,
                high=close,
                low=close,
                close=close,
                amount=float(row.get("成交额") or 0),
                volume=0,
            )
    return rows


def limit_flags(bars: list[Bar], mechanism: str, known_limit_dates: set[int] | None = None) -> list[bool]:
    threshold = 1.198 if mechanism == "20cm" else 1.098
    known_limit_dates = known_limit_dates or set()
    flags = [False]
    for prev, cur in zip(bars, bars[1:]):
        inferred = cur.close / prev.close >= threshold and abs(cur.high - cur.close) < 0.0001
        flags.append(cur.date in known_limit_dates or inferred)
    return flags


def max_streak(flags: list[bool], start: int, end: int) -> int:
    best = run = 0
    for value in flags[start : end + 1]:
        run = run + 1 if value else 0
        best = max(best, run)
    return best


def old_events(flags: list[bool], start: int, end: int) -> list[tuple[int, int, str, int]]:
    events: set[tuple[int, int, str, int]] = set()
    run_start: int | None = None
    for i in range(start, end + 2):
        value = i <= end and flags[i]
        if value and run_start is None:
            run_start = i
        elif not value and run_start is not None:
            length = i - run_start
            if length >= 4:
                events.add((run_start, i - 1, "strict_4_plus", length))
            run_start = None
    for left in range(start, end + 1):
        right = min(left + 9, end)
        count = sum(flags[left : right + 1])
        if count >= 4:
            hit = [i for i in range(left, right + 1) if flags[i]]
            events.add((hit[0], hit[-1], "4_in_10", max_streak(flags, hit[0], hit[-1])))
    return sorted(events)


def recent_events(flags: list[bool], bars: list[Bar], start: int) -> list[tuple[int, int, str, list[int]]]:
    events: set[tuple[int, int, str, tuple[int, ...]]] = set()
    run_start: int | None = None
    for i in range(start, len(flags) + 1):
        value = i < len(flags) and flags[i]
        if value and run_start is None:
            run_start = i
        elif not value and run_start is not None:
            if i - run_start >= 2:
                hits = tuple(range(run_start, i))
                events.add((run_start, i - 1, "consecutive", hits))
            run_start = None
    for left in range(start, max(start, len(flags) - 2)):
        right = left + 2
        hits = tuple(i for i in range(left, right + 1) if flags[i])
        if len(hits) >= 2:
            events.add((hits[0], hits[-1], "2_in_3", hits))
    return [(a, b, kind, list(hits)) for a, b, kind, hits in sorted(events)]


def best_sequence(
    bars: list[Bar],
    flags: list[bool],
    recent: tuple[int, int, str, list[int]],
    start_idx: int,
    minimum_peak_to_rebound_sessions: int = MIN_PEAK_TO_REBOUND_SESSIONS,
):
    rebound_start, rebound_end, rebound_kind, rebound_hits = recent
    # Require at least one complete trading session between the old event and new rebound.
    events = old_events(flags, start_idx, rebound_start - 2)
    choices = []
    for old_start, old_end, old_kind, old_streak in events:
        # Use the last unaffected close before the first limit-up as the launch
        # price. A long lookback low materially overstates the speculation gain.
        if old_start == 0:
            continue
        base_idx = old_start - 1
        peak_idx = max(range(old_start, rebound_start - 1), key=lambda i: bars[i].high)
        # A leadership event cannot finish after its own cycle peak. Such windows
        # are overlapping slices of the current speculation cycle, not an old
        # leader followed by a separate pullback and rebound.
        if old_end > peak_idx:
            continue
        if peak_idx >= rebound_start - 1:
            continue
        trough_range = range(peak_idx + 1, rebound_start)
        if not trough_range:
            continue
        trough_idx = min(trough_range, key=lambda i: bars[i].low)
        if rebound_start - peak_idx < minimum_peak_to_rebound_sessions:
            continue
        rise = bars[peak_idx].high / bars[base_idx].close - 1
        drawdown = bars[trough_idx].low / bars[peak_idx].high - 1
        if rise < 1.0 or drawdown > -0.30:
            continue
        choices.append({
            "old_start": bars[old_start].date,
            "old_end": bars[old_end].date,
            "old_kind": old_kind,
            "old_class": "strict_4_plus" if old_streak >= 4 else "broken_4_in_10",
            "old_max_streak": old_streak,
            "old_limit_up_count": sum(flags[old_start : old_end + 1]),
            "base_date": bars[base_idx].date,
            "base_close": bars[base_idx].close,
            "peak_date": bars[peak_idx].date,
            "peak_high": bars[peak_idx].high,
            "rise_pct": round(rise * 100, 1),
            "trough_date": bars[trough_idx].date,
            "trough_low": bars[trough_idx].low,
            "drawdown_pct": round(drawdown * 100, 1),
            "rebound_kind": rebound_kind,
            "rebound_start": bars[rebound_start].date,
            "rebound_end": bars[rebound_end].date,
            "rebound_limit_dates": [bars[i].date for i in rebound_hits],
            "rebound_streak": max_streak(flags, rebound_start, rebound_end),
            "old_to_rebound_sessions": rebound_start - old_end,
            "peak_to_rebound_sessions": rebound_start - peak_idx,
        })
    if not choices:
        return None
    # Prefer the latest old leadership episode, then the strongest old streak.
    return max(choices, key=lambda x: (x["old_end"], x["old_max_streak"], x["rise_pct"]))


def parse_trade_date(value: str | int) -> int:
    compact = str(value).replace("-", "")
    parsed = datetime.strptime(compact, "%Y%m%d").date()
    return parsed.year * 10000 + parsed.month * 100 + parsed.day


def rolling_dates(as_of: int) -> tuple[int, int, int]:
    parsed = datetime.strptime(str(as_of), "%Y%m%d").date()
    try:
        start = parsed.replace(year=parsed.year - 1)
    except ValueError:
        start = parsed.replace(year=parsed.year - 1, day=28)
    if parsed.month == 1:
        recent = date(parsed.year - 1, 12, 1)
    else:
        recent = date(parsed.year, parsed.month - 1, 1)
    minimum_history = date(start.year, 1, 1)
    to_int = lambda item: item.year * 10000 + item.month * 100 + item.day
    return to_int(start), to_int(recent), to_int(minimum_history)


def validate_tdx_root(tdx: Path) -> None:
    required = [
        tdx / "T0002" / "hq_cache" / "infoharbor_ex.code",
        tdx / "vipdoc" / "sh" / "lday",
        tdx / "vipdoc" / "sz" / "lday",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Invalid TDX root; missing: {', '.join(missing)}")


def scan(tdx: Path, as_of: int, fresh_limit_csv: Path | None = None) -> dict:
    validate_tdx_root(tdx)
    start_date, recent_start, minimum_history = rolling_dates(as_of)
    names = load_names(tdx / "T0002" / "hq_cache" / "infoharbor_ex.code")
    if not names:
        raise ValueError("TDX security-name cache is empty")
    fresh_bars = load_fresh_limit_bars(fresh_limit_csv, as_of)
    rows = []
    files_scanned = 0
    max_date = 0
    for prefix in ("sh", "sz"):
        for path in sorted((tdx / "vipdoc" / prefix / "lday").glob(f"{prefix}*.day")):
            code = path.stem[2:]
            mechanism = market_for(prefix, code)
            if mechanism is None:
                continue
            name = names.get(code, "")
            if not name or "ST" in name.upper() or "退" in name:
                continue
            bars = load_bars(path, minimum_history, as_of)
            if len(bars) < 30:
                continue
            if code in fresh_bars and bars[-1].date < as_of:
                bars.append(fresh_bars[code])
            files_scanned += 1
            max_date = max(max_date, bars[-1].date)
            known_limit_dates = {as_of} if code in fresh_bars else set()
            flags = limit_flags(bars, mechanism, known_limit_dates)
            try:
                start_idx = next(i for i, bar in enumerate(bars) if bar.date >= start_date)
                recent_idx = next(i for i, bar in enumerate(bars) if bar.date >= recent_start)
            except StopIteration:
                continue
            sequences = []
            for recent in recent_events(flags, bars, recent_idx):
                sequence = best_sequence(bars, flags, recent, start_idx)
                if sequence:
                    sequences.append(sequence)
            if not sequences:
                continue
            best = max(sequences, key=lambda x: (x["rebound_end"], x["rebound_streak"], x["rise_pct"]))
            best.update({"code": code, "name": name, "market": prefix, "mechanism": mechanism})
            rows.append(best)
    if files_scanned == 0:
        raise ValueError(f"No eligible A-share daily files found under TDX root: {tdx}")
    rows.sort(key=lambda x: (x["rebound_end"], x["rebound_streak"], x["rise_pct"]), reverse=True)
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": "TDX vipdoc raw .day plus optional confirmed fresh limit-up CSV",
        "as_of": as_of,
        "start_date": start_date,
        "recent_start": recent_start,
        "max_trade_date": max_date,
        "files_scanned": files_scanned,
        "fresh_limit_count": len(fresh_bars),
        "candidate_count": len(rows),
        "criteria": {
            "old": "strict >=4 consecutive limit-ups OR >=4 limit-ups in 10 sessions",
            "rise": ">=100% from close before first limit-up to pre-rebound peak",
            "sequence": "old event -> peak -> >=30% drawdown trough -> rebound",
            "separation": f">={MIN_PEAK_TO_REBOUND_SESSIONS} sessions from old peak to rebound",
            "old_class": "strict >=4 consecutive; compatible = >=4 in 10 sessions with max streak <4",
            "rebound": f">=2 consecutive limit-ups OR >=2 limit-ups in 3 sessions since {recent_start}",
            "tracks": "10cm >=9.8%, 20cm >=19.8%, both require high=close",
        },
        "candidates": rows,
    }


def write_outputs(result: dict, json_path: Path, csv_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result["candidates"])


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", required=True, help="Target trade date: YYYY-MM-DD or YYYYMMDD")
    app_scripts = Path(__file__).resolve().parents[3] / "scripts"
    if str(app_scripts) not in sys.path:
        sys.path.insert(0, str(app_scripts))
    from tdx_path_config import resolve_tdx_root

    parser.add_argument("--tdx", type=Path, default=resolve_tdx_root())
    parser.add_argument("--fresh-limit-csv", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args(argv)
    as_of = parse_trade_date(args.as_of)
    result = scan(args.tdx, as_of, args.fresh_limit_csv)
    write_outputs(result, args.json, args.csv)
    print(json.dumps({k: result[k] for k in ("max_trade_date", "files_scanned", "candidate_count")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
