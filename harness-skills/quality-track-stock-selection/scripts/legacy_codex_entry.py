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
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
BUSINESS_RUN_ROOT = os.environ.get("CODEX_STOCK_BUSINESS_RUN_DIR", "").strip()
RUN = Path(BUSINESS_RUN_ROOT).resolve() / ROOT.name if BUSINESS_RUN_ROOT else ROOT / "run"
SELECTION = RUN / "practical_selection.json"
BACKTEST = RUN / "execution_backtest.json"
LEDGER = RUN / "paper_ledger.json"
STATUS = RUN / "skill_status.json"
STATUS_READBACK = RUN / "status_readback.json"
SELFTEST = RUN / "selftest.json"
BACKTEST_STABILITY = RUN / "backtest_stability.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "size_bytes": path.stat().st_size, "sha256": sha256(path)}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def invoke(script: str, args: list[str], allowed: set[int]) -> subprocess.CompletedProcess[str]:
    command = [str(Path(sys.executable).resolve()), str(SCRIPTS / script), *args]
    result = subprocess.run(command, cwd=SCRIPTS, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode not in allowed:
        raise RuntimeError(f"{script} failed with exit code {result.returncode}")
    return result


def write_status() -> dict[str, Any]:
    selection = load_json(SELECTION)
    backtest = load_json(BACKTEST)
    ledger = load_json(LEDGER)
    stability = load_json(BACKTEST_STABILITY)
    result_files = [SELECTION, BACKTEST, BACKTEST_STABILITY, LEDGER, SELFTEST]
    payload = {
        "schema": "QUALITY-TRACK-STOCK-SELECTION-SKILL-1",
        "skill": "quality-track-stock-selection",
        "display_name": "优质赛道选股",
        "status": "PASS",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "target_system": "local Codex",
        "mode": "paper_selection_only",
        "automatic_order": False,
        "selection_status": selection["status"],
        "selection_generated_at": selection["generated_at"],
        "selection_trade_date": selection["trade_date"],
        "selection_counts": selection["counts"],
        "watch_candidates": [item["name"] for item in selection.get("watch_candidates") or []],
        "backtest_status": backtest["status"],
        "backtest_metrics": backtest["metrics"],
        "backtest_readiness_checks": backtest["readiness_checks"],
        "backtest_stability_status": stability["status"],
        "paper_ledger_states": [item["state"] for item in ledger.get("observations") or []],
        "deployment": {
            "real_money_authorized": False,
            "reason": "paper decision support only; automatic order disabled; backtest and evidence gates remain fail closed",
        },
        "artifacts": [artifact(path) for path in result_files],
    }
    RUN.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def command_info() -> int:
    print(json.dumps({
        "name": "quality-track-stock-selection",
        "display_name": "优质赛道选股",
        "entry": str(Path(__file__).resolve()),
        "run_dir": str(RUN),
        "commands": ["info", "selftest", "run", "status", "backtest", "settle"],
        "mode": "paper_selection_only",
        "automatic_order": False,
    }, ensure_ascii=False, indent=2))
    return 0


def command_selftest() -> int:
    RUN.mkdir(parents=True, exist_ok=True)
    invoke("selftest.py", ["--output", str(SELFTEST)], {0})
    persisted = load_json(SELFTEST)
    assert persisted["status"] == "PASS"
    print(f"QUALITY_TRACK_SKILL_SELFTEST_READBACK_PASS sha256={sha256(SELFTEST)} size={SELFTEST.stat().st_size}")
    return 0


def command_backtest(lookback_sessions: int) -> int:
    RUN.mkdir(parents=True, exist_ok=True)
    invoke(
        "quality_track_backtest.py",
        ["--output", str(BACKTEST), "--lookback-sessions", str(lookback_sessions)],
        {0, 2},
    )
    persisted = load_json(BACKTEST)
    invoke(
        "verify_backtest_stability.py",
        ["--output", str(BACKTEST_STABILITY), "--lookback-sessions", str(lookback_sessions)],
        {0},
    )
    stability = load_json(BACKTEST_STABILITY)
    assert stability["status"] == "PASS"
    print(
        "QUALITY_TRACK_SKILL_BACKTEST_READBACK "
        f"status={persisted['status']} sha256={sha256(BACKTEST)} size={BACKTEST.stat().st_size}"
    )
    return 0


def command_run(enrich_limit: int, final_limit: int, lookback_sessions: int) -> int:
    command_selftest()
    invoke(
        "quality_track_live.py",
        ["--output", str(SELECTION), "--enrich-limit", str(enrich_limit), "--final-limit", str(final_limit)],
        {0, 2},
    )
    command_backtest(lookback_sessions)
    invoke("paper_monitor.py", ["record", "--selection", str(SELECTION), "--ledger", str(LEDGER)], {0})
    payload = write_status()
    print(
        "QUALITY_TRACK_SKILL_RUN_PASS "
        f"selection={payload['selection_status']} watch={payload['selection_counts']['watch_candidates']} "
        f"selected={payload['selection_counts']['selected']} backtest={payload['backtest_status']} "
        f"status_sha256={sha256(STATUS)} status_size={STATUS.stat().st_size}"
    )
    return 0


def command_status() -> int:
    if not STATUS.is_file():
        raise RuntimeError("skill status missing; run the skill first")
    status = load_json(STATUS)
    checks: list[dict[str, Any]] = []
    for expected in status["artifacts"]:
        path = Path(expected["path"])
        actual = artifact(path) if path.is_file() else {"path": str(path), "missing": True}
        ok = bool(
            path.is_file()
            and actual["size_bytes"] == expected["size_bytes"]
            and actual["sha256"] == expected["sha256"]
        )
        checks.append({"ok": ok, "expected": expected, "actual": actual})
    selection = load_json(SELECTION)
    backtest = load_json(BACKTEST)
    backtest_stability = load_json(BACKTEST_STABILITY)
    business_ok = bool(
        status["selection_status"] == selection["status"]
        and status["selection_counts"] == selection["counts"]
        and status["backtest_status"] == backtest["status"]
        and status["backtest_stability_status"] == backtest_stability["status"]
        and backtest_stability["status"] == "PASS"
    )
    payload = {
        "schema": "QUALITY-TRACK-STOCK-SELECTION-READBACK-1",
        "status": "PASS" if business_ok and all(item["ok"] for item in checks) else "FAIL",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "business_state_matches": business_ok,
        "artifact_checks": checks,
        "selection_status": selection["status"],
        "selection_counts": selection["counts"],
        "backtest_status": backtest["status"],
        "backtest_stability_status": backtest_stability["status"],
        "backtest_stability_common_period_count": backtest_stability["common_period_count"],
        "backtest_stability_trade_keys_match": backtest_stability["trade_keys_match"],
    }
    STATUS_READBACK.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if payload["status"] != "PASS":
        raise RuntimeError("persisted skill status readback failed")
    print(
        "QUALITY_TRACK_SKILL_STATUS_PASS "
        f"selection={selection['status']} watch={selection['counts']['watch_candidates']} "
        f"selected={selection['counts']['selected']} backtest={backtest['status']} "
        f"backtest_stability={backtest_stability['status']} "
        f"readback_sha256={sha256(STATUS_READBACK)} readback_size={STATUS_READBACK.stat().st_size}"
    )
    return 0


def command_settle() -> int:
    if not LEDGER.is_file():
        raise RuntimeError("paper ledger missing; run the skill first")
    invoke("paper_monitor.py", ["settle", "--ledger", str(LEDGER)], {0})
    print(f"QUALITY_TRACK_SKILL_SETTLE_PASS sha256={sha256(LEDGER)} size={LEDGER.stat().st_size}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="优质赛道选股固定Codex入口")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("info")
    subparsers.add_parser("selftest")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--enrich-limit", type=int, default=30)
    run_parser.add_argument("--final-limit", type=int, default=5)
    run_parser.add_argument("--lookback-sessions", type=int, default=500)
    backtest_parser = subparsers.add_parser("backtest")
    backtest_parser.add_argument("--lookback-sessions", type=int, default=500)
    subparsers.add_parser("status")
    subparsers.add_parser("settle")
    args = parser.parse_args()

    if args.command == "info":
        return command_info()
    if args.command == "selftest":
        return command_selftest()
    if args.command == "run":
        return command_run(args.enrich_limit, args.final_limit, args.lookback_sessions)
    if args.command == "backtest":
        return command_backtest(args.lookback_sessions)
    if args.command == "status":
        return command_status()
    if args.command == "settle":
        return command_settle()
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
