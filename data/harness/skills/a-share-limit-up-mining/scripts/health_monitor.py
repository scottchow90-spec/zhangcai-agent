#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path.home() / ".codex" / "reports" / "_lianban_runtime" / "health"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def state_path(args: argparse.Namespace) -> Path:
    safe_workflow = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in args.workflow)
    safe_date = args.trade_date.replace("-", "")
    return ROOT / f"{safe_date}_{safe_workflow}_{args.run_id}.json"


def read_state(path: Path, args: argparse.Namespace) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "workflow": args.workflow,
        "trade_date": args.trade_date,
        "run_id": args.run_id,
        "started_at": None,
        "finished_at": None,
        "status": "not_started",
        "records": {},
    }


def write_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def parse_value(value: str):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def main() -> int:
    parser = argparse.ArgumentParser(description="连板挖掘显式运行状态记录器")
    parser.add_argument("action", choices=("start", "record", "finish", "show"))
    parser.add_argument("--workflow", default="lianban-mining-research")
    parser.add_argument("--trade-date", required=True)
    parser.add_argument("--run-id", default="01")
    parser.add_argument("--section", default="runtime")
    parser.add_argument("--key")
    parser.add_argument("--value")
    parser.add_argument("--status", choices=("healthy", "degraded", "failed"), default="healthy")
    args = parser.parse_args()
    path = state_path(args)
    state = read_state(path, args)
    timestamp = now_iso()
    if args.action == "start":
        state.update({"started_at": timestamp, "finished_at": None, "status": "running"})
    elif args.action == "record":
        if not args.key or args.value is None:
            parser.error("record requires --key and --value")
        state.setdefault("records", {}).setdefault(args.section, {})[args.key] = {
            "value": parse_value(args.value),
            "recorded_at": timestamp,
        }
    elif args.action == "finish":
        state.update({"finished_at": timestamp, "status": args.status})
    if args.action != "show":
        write_state(path, state)
    print(json.dumps({"status": "PASS", "state_path": str(path), "state": state}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
