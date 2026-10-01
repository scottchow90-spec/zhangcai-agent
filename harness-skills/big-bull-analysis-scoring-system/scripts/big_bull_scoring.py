#!/usr/bin/env python3
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
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_tdx_root

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
SKILLS_ROOT = Path(os.environ.get("STOCK_SKILLS_ROOT", str(ROOT.parent))).expanduser().resolve()
CORE_DIR = SKILLS_ROOT / "stock-unified" / "scripts"
TDX_ROOT = resolve_tdx_root()
TQ_USER_DIR = TDX_ROOT / "PYPlugins" / "user"
TQ_INIT = TQ_USER_DIR / "tdxdata_test.py"
DEFAULT_BLOCK_DIR = TDX_ROOT / "T0002" / "blocknew"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(CORE_DIR))

import stock_strategy_backtest as core  # noqa: E402
from poster_builder import render_poster  # noqa: E402
from scoring_engine import indicator_pack, recent_crosses, score_event  # noqa: E402


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_board_file(board_code: str, board_file: str | None) -> Path:
    path = Path(board_file).expanduser().resolve() if board_file else DEFAULT_BLOCK_DIR / f"{board_code}.blk"
    if not path.is_file():
        raise FileNotFoundError(f"通达信自定义板块文件不存在：{path}")
    return path


def board_symbols(path: Path) -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()
    for raw in path.read_text(encoding="ascii", errors="ignore").splitlines():
        value = raw.strip()
        if len(value) != 7 or not value.isdigit():
            continue
        code = value[1:]
        market = "SH" if value[0] == "1" else "SZ"
        symbol = f"{code}.{market}"
        if symbol not in seen:
            seen.add(symbol)
            symbols.append(symbol)
    if not symbols:
        raise ValueError(f"通达信自定义板块为空：{path}")
    return symbols


def current_tq_bars(symbols: list[str], count: int) -> dict[str, list[core.Bar]]:
    sys.path.insert(0, str(TQ_USER_DIR))
    from tqcenter import tq

    tq.initialize(str(TQ_INIT))
    try:
        market = tq.get_market_data(
            field_list=["Open", "High", "Low", "Close", "Amount", "Volume"],
            stock_list=symbols,
            count=count,
            dividend_type="none",
            period="1d",
            fill_data=True,
        )
    finally:
        tq.close()

    required = {"Open", "High", "Low", "Close", "Amount", "Volume"}
    if not isinstance(market, dict) or not required.issubset(market):
        raise RuntimeError("通达信运行态没有返回完整日线字段")

    output: dict[str, list[core.Bar]] = {}
    for symbol in symbols:
        bars: list[core.Bar] = []
        close_series = market["Close"][symbol]
        for date_value in close_series.index:
            values = [
                float(market[field].at[date_value, symbol])
                for field in ("Open", "High", "Low", "Close", "Amount", "Volume")
            ]
            if not all(math.isfinite(value) for value in values):
                continue
            bars.append(core.Bar(
                date=int(date_value.strftime("%Y%m%d")),
                open=values[0],
                high=values[1],
                low=values[2],
                close=values[3],
                amount=values[4],
                volume=int(values[5]),
            ))
        output[symbol] = bars
    return output


def common_score_date(
    bars_by_symbol: dict[str, list[core.Bar]],
    board_date: int,
) -> int:
    date_sets = [
        {bar.date for bar in bars if bar.date <= board_date}
        for bars in bars_by_symbol.values()
        if bars
    ]
    if not date_sets:
        raise RuntimeError("没有可用的通达信日线")
    common = set.intersection(*date_sets)
    if not common:
        raise RuntimeError("成分股没有统一评分日")
    return max(common)


def competition_ranks(rows: list[dict[str, Any]]) -> None:
    previous_key: tuple[bool, int] | None = None
    previous_rank = 0
    for position, row in enumerate(rows, start=1):
        key = (bool(row.get("eligible")), int(row.get("score", -1)))
        if key == previous_key:
            row["rank"] = previous_rank
        else:
            row["rank"] = position
            previous_rank = position
            previous_key = key


def build_rows(
    symbols: list[str],
    bars_by_symbol: dict[str, list[core.Bar]],
    score_date: int,
    lookback: int,
) -> list[dict[str, Any]]:
    names = core.load_names()
    day_paths = {symbol: Path(path) for symbol, path in core.universe_candidates("equity")}
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        name = names.get(symbol, symbol)
        bars = bars_by_symbol.get(symbol, [])
        date_to_index = {bar.date: index for index, bar in enumerate(bars)}
        index = date_to_index.get(score_date)
        if index is None or index < 239:
            rows.append({
                "symbol": symbol,
                "name": name,
                "score": -1,
                "eligible": False,
                "status": "数据不足",
                "signal_source": "未核对",
                "hard_reasons": ["统一评分日数据不足"],
                "components": {
                    "方向位置": 0,
                    "上涨劲头": 0,
                    "当天表现": 0,
                    "上下空间": 0,
                    "额外提醒": 0,
                },
            })
            continue

        pack = indicator_pack(bars)
        crosses = recent_crosses(bars, pack, index, lookback)
        total, components, hard_reasons, levels = score_event(bars, symbol, index, pack)
        signal_hit = bool(crosses)
        reasons = list(hard_reasons)
        if not signal_hit:
            reasons.append("板块快照附近未核对到黄金点火状态")
        day_path = day_paths.get(symbol)
        rows.append({
            "symbol": symbol,
            "name": name,
            "status": "已核对" if signal_hit else "状态待核对",
            "signal_source": "日线核对" if signal_hit else "板块成员",
            "score_date": str(score_date),
            "latest_trading_date": str(bars[-1].date),
            "latest_close": bars[-1].close,
            "score_close": bars[index].close,
            "score": int(total),
            "eligible": signal_hit and not reasons,
            "hard_reasons": reasons,
            "components": components,
            "levels": levels,
            "golden_ignition": {
                "recent_crosses": crosses,
                "lookback_days": lookback,
            },
            "daily_file": {
                "path": str(day_path) if day_path else None,
                "sha256": sha256_file(day_path) if day_path and day_path.is_file() else None,
            },
            "current_market_data": {
                "source": "本机通达信运行态",
                "period": "日线",
                "dividend_type": "不复权",
                "bar_count": len(bars),
                "latest_date": str(bars[-1].date),
                "tqcenter_path": str(TQ_USER_DIR / "tqcenter.py"),
                "tqcenter_sha256": sha256_file(TQ_USER_DIR / "tqcenter.py"),
            },
        })

    rows.sort(
        key=lambda row: (
            0 if row.get("eligible") else 1,
            -(row.get("score") if isinstance(row.get("score"), int) else -1),
            row["symbol"],
        )
    )
    competition_ranks(rows)
    return rows


def run(args: argparse.Namespace) -> dict[str, Any]:
    board_path = resolve_board_file(args.board_code, args.board_file)
    symbols = board_symbols(board_path)
    board_updated = datetime.fromtimestamp(board_path.stat().st_mtime).astimezone()
    board_date = int(board_updated.strftime("%Y%m%d"))
    bars_by_symbol = current_tq_bars(symbols, args.bar_count)
    score_date = common_score_date(bars_by_symbol, board_date)
    rows = build_rows(symbols, bars_by_symbol, score_date, args.lookback)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    ranking_path = output_dir / "ranking.json"
    poster_path = output_dir / "poster.png"
    ranking_path.unlink(missing_ok=True)
    poster_path.unlink(missing_ok=True)

    payload: dict[str, Any] = {
        "schema": "BIG_BULL_SCORING_SYSTEM_V1",
        "status": "CLEAN_PASS",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": "本机通达信",
        "board": {
            "name": args.board_name,
            "code": args.board_code,
            "path": str(board_path),
            "updated_at": board_updated.isoformat(timespec="seconds"),
            "updated_at_text": board_updated.strftime("%Y年%m月%d日%H时%M分%S秒"),
            "sha256": sha256_file(board_path),
            "constituent_count": len(symbols),
        },
        "score_date": str(score_date),
        "score_standard": {
            "方向位置": 30,
            "上涨劲头": 25,
            "当天表现": 20,
            "上下空间": 20,
            "额外提醒": 5,
        },
        "ranking_rule": "先看硬条件，再按总分从高到低排列；同分并列",
        "eligible_count": sum(1 for row in rows if row.get("eligible")),
        "rows": rows,
        "supplemental_source": {
            "name": "短线侠",
            "status": "不适用",
            "reason": "公开数据集不覆盖任意自定义板块成分股的逐股日线",
        },
        "limitations": [
            "分数只用于整理候选，不代表未来结果。",
            "上下空间使用历史高低位置和趋势线估算，不冒充原版专有撑压数值。",
            "板块快照日期晚于最新交易日时，统一采用不晚于板块快照的最近共同交易日。",
        ],
    }
    poster_validation = render_poster(payload, poster_path)
    payload["artifacts"] = {
        "poster": {
            "path": str(poster_path),
            "sha256": sha256_file(poster_path),
            "validation": poster_validation,
        },
        "ranking": {
            "path": str(ranking_path),
        },
    }
    ranking_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    result = {
        "schema": "BIG_BULL_SCORING_RUN_V1",
        "status": "CLEAN_PASS",
        "board": payload["board"],
        "score_date": payload["score_date"],
        "eligible_count": payload["eligible_count"],
        "ranking_path": str(ranking_path),
        "ranking_sha256": sha256_file(ranking_path),
        "poster_path": str(poster_path),
        "poster_sha256": sha256_file(poster_path),
        "poster_validation": poster_validation,
        "ranking": [
            {
                "rank": row["rank"],
                "symbol": row["symbol"],
                "name": row["name"],
                "score": row["score"],
                "eligible": row["eligible"],
                "hard_reasons": row["hard_reasons"],
            }
            for row in rows
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="大牛线评分系统")
    parser.add_argument("--board-name", default="黄金点火")
    parser.add_argument("--board-code", default="HJDH")
    parser.add_argument("--board-file")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--lookback", type=int, default=5)
    parser.add_argument("--bar-count", type=int, default=300)
    args = parser.parse_args()
    try:
        run(args)
        return 0
    except Exception as exc:
        print(json.dumps({
            "schema": "BIG_BULL_SCORING_RUN_V1",
            "status": "BLOCKED",
            "error": f"{type(exc).__name__}:{exc}",
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
