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
from datetime import datetime
from pathlib import Path
from typing import Any

import quality_track_live as live


HOLDING_DAYS = 5
ENTRY_COST_RATE = 0.0013
EXIT_COST_RATE = 0.0018


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema": "QUALITY-TRACK-PAPER-LEDGER-1",
            "automatic_order": False,
            "observations": [],
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "QUALITY-TRACK-PAPER-LEDGER-1":
        raise RuntimeError("paper ledger schema mismatch")
    return payload


def record(selection_path: Path, ledger_path: Path) -> dict[str, Any]:
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    source_hash = sha256(selection_path)
    ledger = load_ledger(ledger_path)
    if selection["status"] == "NO_TRADE":
        observation_date = str(selection["generated_at"])[:10]
        matching = [
            row for row in ledger["observations"]
            if row["selection_status"] == "NO_TRADE"
            and str(row["generated_at"])[:10] == observation_date
            and row["signal_complete_trade_date"] == selection["trade_date"]
        ]
        if matching:
            latest = max(matching, key=lambda row: str(row["generated_at"]))
            ledger["observations"] = [
                row for row in ledger["observations"]
                if row not in matching or row is latest
            ]
            latest.update({
                "generated_at": selection["generated_at"],
                "selection_sha256": source_hash,
                "selection_size": selection_path.stat().st_size,
                "positions": [],
                "state": "NO_TRADE_RECORDED",
                "settlement": None,
            })
            ledger["last_updated_at"] = datetime.now(live.CN_TZ).isoformat(timespec="seconds")
            ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
            return ledger
    existing = next((row for row in ledger["observations"] if row["selection_sha256"] == source_hash), None)
    if existing is not None:
        return ledger
    generated_at = datetime.fromisoformat(selection["generated_at"])
    positions = []
    for item in selection.get("selected_candidates") or []:
        positions.append({
            "symbol": item["symbol"],
            "code7": item["code7"],
            "name": item["name"],
            "paper_rank": item["paper_rank"],
            "reference_price": item["paper_plan"]["reference_price"],
            "entry_ceiling": item["paper_plan"]["entry_ceiling"],
            "initial_stop": item["paper_plan"]["initial_stop"],
            "portfolio_weight_pct": item["paper_plan"]["portfolio_scaled_weight_pct"],
            "state": "PENDING_ENTRY",
        })
    observation = {
        "observation_id": f"{generated_at.strftime('%Y%m%dT%H%M%S')}-{source_hash[:12]}",
        "generated_at": selection["generated_at"],
        "signal_complete_trade_date": selection["trade_date"],
        "selection_status": selection["status"],
        "selection_sha256": source_hash,
        "selection_size": selection_path.stat().st_size,
        "positions": positions,
        "state": "NO_TRADE_RECORDED" if not positions else "PENDING",
        "settlement": None,
    }
    ledger["observations"].append(observation)
    ledger["last_updated_at"] = datetime.now(live.CN_TZ).isoformat(timespec="seconds")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    return ledger


def settle(ledger_path: Path) -> dict[str, Any]:
    ledger = load_ledger(ledger_path)
    for observation in ledger["observations"]:
        if observation["state"] != "PENDING":
            continue
        observation_date = int(str(observation["generated_at"])[:10].replace("-", ""))
        completed: list[dict[str, Any]] = []
        still_pending = False
        for position in observation["positions"]:
            rows = live.read_day_rows(position["code7"])
            future = [row for row in rows if int(row["date"]) > observation_date]
            if len(future) < HOLDING_DAYS:
                still_pending = True
                continue
            entry_row = future[0]
            raw_entry = float(entry_row["open"])
            if raw_entry > float(position["entry_ceiling"]):
                position.update({"state": "SKIPPED_ENTRY_ABOVE_CEILING", "entry_date": int(entry_row["date"]), "entry_open": raw_entry})
                completed.append(position)
                continue
            entry_price = raw_entry * (1.0 + ENTRY_COST_RATE)
            stop_price = float(position["initial_stop"])
            exit_price: float | None = None
            exit_date: int | None = None
            exit_reason = "time_exit"
            for row in future[:HOLDING_DAYS]:
                if float(row["low"]) <= stop_price:
                    exit_price = stop_price * (1.0 - EXIT_COST_RATE)
                    exit_date = int(row["date"])
                    exit_reason = "stop"
                    break
            if exit_price is None:
                exit_row = future[HOLDING_DAYS - 1]
                exit_price = float(exit_row["close"]) * (1.0 - EXIT_COST_RATE)
                exit_date = int(exit_row["date"])
            position.update({
                "state": "SETTLED",
                "entry_date": int(entry_row["date"]),
                "entry_price_after_cost": round(entry_price, 6),
                "exit_date": exit_date,
                "exit_price_after_cost": round(exit_price, 6),
                "exit_reason": exit_reason,
                "net_return_pct": round((exit_price / entry_price - 1.0) * 100.0, 4),
            })
            completed.append(position)
        if not still_pending:
            returns = [float(item["net_return_pct"]) for item in completed if item["state"] == "SETTLED"]
            observation["state"] = "SETTLED"
            observation["settlement"] = {
                "position_count": len(completed),
                "settled_trade_count": len(returns),
                "average_net_return_pct": round(sum(returns) / len(returns), 4) if returns else None,
                "all_entries_after_observation_date": all(
                    int(item.get("entry_date", 0)) > observation_date for item in completed
                ),
            }
    ledger["last_updated_at"] = datetime.now(live.CN_TZ).isoformat(timespec="seconds")
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser(description="优质赛道纸面信号跟踪与结算")
    subparsers = parser.add_subparsers(dest="command", required=True)
    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--selection", type=Path, required=True)
    record_parser.add_argument("--ledger", type=Path, required=True)
    settle_parser = subparsers.add_parser("settle")
    settle_parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "record":
        result = record(args.selection, args.ledger)
    else:
        result = settle(args.ledger)
    states: dict[str, int] = {}
    for row in result["observations"]:
        states[row["state"]] = states.get(row["state"], 0) + 1
    print(f"QUALITY_TRACK_PAPER_LEDGER observations={len(result['observations'])} states={json.dumps(states, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
