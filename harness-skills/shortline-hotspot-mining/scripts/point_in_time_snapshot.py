#!/usr/bin/env python3
"""Freeze local TDX sector membership and daily-bar provenance at a cutoff."""
from __future__ import annotations

import hashlib
import json
import re
import struct
from dataclasses import asdict, dataclass
from datetime import date, time
from pathlib import Path
from typing import Iterable, Sequence


DAY_RECORD = struct.Struct("<IIIIIfII")
MIN_HIGH_CONFIDENCE_COVERAGE = 0.80
MIN_HIGH_CONFIDENCE_MEMBERS = 5


class SnapshotBlocked(RuntimeError):
    """Raised when a point-in-time snapshot cannot be proven."""


@dataclass(frozen=True)
class DailyBar:
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    amount: float
    volume: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_trade_date(requested: date, available: Sequence[date]) -> date:
    eligible = sorted(value for value in set(available) if value <= requested)
    if not eligible:
        raise SnapshotBlocked("no_trade_date_on_or_before_request")
    return eligible[-1]


def validate_strong_data_dates(expected: date, observed: Iterable[date]) -> None:
    values = set(observed)
    if not values:
        raise SnapshotBlocked("strong_data_dates_missing")
    if values != {expected}:
        rendered = ",".join(sorted(value.isoformat() for value in values))
        raise SnapshotBlocked(
            f"strong_data_date_mismatch:expected={expected.isoformat()}:observed={rendered}"
        )


def _decode_trade_date(value: int) -> date:
    try:
        return date(value // 10000, value // 100 % 100, value % 100)
    except ValueError as exc:
        raise SnapshotBlocked(f"invalid_tdx_trade_date:{value}") from exc


def read_tdx_day_file(path: Path, *, cutoff_date: date | None = None) -> list[DailyBar]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise SnapshotBlocked(f"tdx_day_read_failed:{path}:{exc}") from exc
    if not raw or len(raw) % DAY_RECORD.size:
        raise SnapshotBlocked(f"tdx_day_record_size_invalid:{path}:{len(raw)}")

    bars: list[DailyBar] = []
    for offset in range(0, len(raw), DAY_RECORD.size):
        encoded_day, open_, high, low, close, amount, volume, _ = DAY_RECORD.unpack_from(
            raw,
            offset,
        )
        trade_day = _decode_trade_date(encoded_day)
        if cutoff_date is not None and trade_day > cutoff_date:
            continue
        bars.append(
            DailyBar(
                trade_date=trade_day,
                open=open_ / 100.0,
                high=high / 100.0,
                low=low / 100.0,
                close=close / 100.0,
                amount=float(amount),
                volume=int(volume),
            )
        )
    if any(left.trade_date >= right.trade_date for left, right in zip(bars, bars[1:])):
        raise SnapshotBlocked(f"tdx_day_dates_not_strictly_increasing:{path}")
    return bars


def _extract_codes(text: str) -> list[str]:
    codes: list[str] = []
    for line in text.splitlines():
        match = re.search(r"(?<!\d)(\d{6})(?!\d)", line.strip())
        if match:
            codes.append(match.group(1))
            continue
        digits = "".join(character for character in line if character.isdigit())
        if len(digits) in (6, 7):
            codes.append(digits[-6:])
    return list(dict.fromkeys(codes))


def _load_block_names(config_path: Path) -> dict[str, str]:
    if not config_path.is_file():
        raise SnapshotBlocked(f"blocknew_config_missing:{config_path}")
    raw = config_path.read_bytes()
    if not raw or len(raw) % 120:
        raise SnapshotBlocked(f"blocknew_config_size_invalid:{config_path}:{len(raw)}")
    names: dict[str, str] = {}
    for offset in range(0, len(raw), 120):
        record = raw[offset : offset + 120]
        name = record[:50].split(b"\x00", 1)[0].decode("gbk", errors="ignore").strip()
        alias = record[50:].split(b"\x00", 1)[0].decode("gbk", errors="ignore").strip()
        if name and alias:
            names[alias.casefold()] = name
    if not names:
        raise SnapshotBlocked(f"blocknew_config_has_no_registered_blocks:{config_path}")
    return names


def load_blocknew_universe(blocknew_dir: Path) -> list[dict]:
    names = _load_block_names(blocknew_dir / "blocknew.cfg")
    universe: list[dict] = []
    for path in sorted(blocknew_dir.glob("*.blk"), key=lambda item: item.name.casefold()):
        sector = names.get(path.stem.casefold())
        if sector is None:
            continue
        try:
            members = _extract_codes(path.read_text(encoding="gbk", errors="ignore"))
        except OSError as exc:
            raise SnapshotBlocked(f"block_file_read_failed:{path}:{exc}") from exc
        if not members:
            continue
        universe.append(
            {
                "sector": sector,
                "alias": path.stem,
                "members": members,
                "member_count": len(members),
                "block_path": str(path.resolve()),
                "block_sha256": sha256_file(path),
            }
        )
    if not universe:
        raise SnapshotBlocked(f"registered_block_universe_empty:{blocknew_dir}")
    return universe


def market_for_code(code: str) -> str:
    if code.startswith(("5", "6", "9")):
        return "sh"
    if code.startswith(("4", "8")):
        return "bj"
    return "sz"


def find_tdx_day_file(code: str, vipdoc_roots: Sequence[Path]) -> Path | None:
    market = market_for_code(code)
    for root in vipdoc_roots:
        for path in (
            root / "xinzeng" / market / "lday" / f"{market}{code}.day",
            root / market / "lday" / f"{market}{code}.day",
        ):
            if path.is_file() and path.stat().st_size >= DAY_RECORD.size:
                return path.resolve()
    return None


def _canonical_hash(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_point_in_time_snapshot(
    *,
    requested_date: date,
    cutoff_time: time,
    blocknew_dir: Path,
    vipdoc_roots: Sequence[Path],
) -> dict:
    universe = load_blocknew_universe(blocknew_dir)
    member_sources: dict[str, dict] = {}
    available_dates: list[date] = []
    for code in dict.fromkeys(
        code for sector in universe for code in sector["members"]
    ):
        path = find_tdx_day_file(code, vipdoc_roots)
        if path is None:
            continue
        bars = read_tdx_day_file(path, cutoff_date=requested_date)
        if not bars:
            continue
        latest = bars[-1]
        available_dates.append(latest.trade_date)
        member_sources[code] = {
            "code": code,
            "path": str(path),
            "sha256": sha256_file(path),
            "bar_count_at_cutoff": len(bars),
            "latest_available_date": latest.trade_date.isoformat(),
        }

    resolved_date = resolve_trade_date(requested_date, available_dates)
    sectors: list[dict] = []
    for sector in universe:
        current_members = [
            member_sources[code]
            for code in sector["members"]
            if code in member_sources
            and member_sources[code]["latest_available_date"] == resolved_date.isoformat()
        ]
        member_count = sector["member_count"]
        coverage_count = len(current_members)
        coverage_ratio = coverage_count / member_count if member_count else 0.0
        sectors.append(
            {
                **sector,
                "coverage_count": coverage_count,
                "coverage_ratio": round(coverage_ratio, 6),
                "eligible_for_high_confidence": (
                    coverage_count >= MIN_HIGH_CONFIDENCE_MEMBERS
                    and coverage_ratio >= MIN_HIGH_CONFIDENCE_COVERAGE
                ),
                "current_member_sources": current_members,
                "missing_or_stale_members": [
                    code
                    for code in sector["members"]
                    if code not in {item["code"] for item in current_members}
                ],
            }
        )

    frozen = {
        "requested_date": requested_date.isoformat(),
        "resolved_trade_date": resolved_date.isoformat(),
        "cutoff_time": cutoff_time.isoformat(),
        "market_phase": "close" if cutoff_time >= time(15, 0) else "intraday",
        "blocknew_config": {
            "path": str((blocknew_dir / "blocknew.cfg").resolve()),
            "sha256": sha256_file(blocknew_dir / "blocknew.cfg"),
        },
        "sectors": sectors,
    }
    return {
        "schema": "SHORTLINE_POINT_IN_TIME_SNAPSHOT_V1",
        "snapshot_id": _canonical_hash(frozen),
        **frozen,
    }


def serialize_bar(bar: DailyBar) -> dict:
    payload = asdict(bar)
    payload["trade_date"] = bar.trade_date.isoformat()
    return payload
