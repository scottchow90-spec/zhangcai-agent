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
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime_utils import atomic_write_json, atomic_write_text, run_process_tree


ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = ROOT.parent
HARD_GATE_VALIDATION_TEXT = (
    "逐字回读 用户原话 禁止默认替代 禁止任务扩展 禁止单源结论 "
    "禁止热替换 输出结构服从用户 禁止缩窄范围 禁止子代理跑偏 "
    "禁止假交付"
)
EXPECTED_TOP1_SKILLS = (
    "stock-hard-gate",
    "tdx-local-hub",
    "golden-ignition",
    "feilong-strategy",
    "youzi-capital-monitoring",
    "big-bull-analysis-scoring-system",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "size_bytes": path.stat().st_size, "sha256": sha256(path)}


def artifact_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "path": str(path.resolve()),
            "exists": False,
            "size_bytes": None,
            "sha256": None,
        }
    value = artifact(path)
    return {"path": value["path"], "exists": True, "size_bytes": value["size_bytes"], "sha256": value["sha256"]}


def business_entry_for(skill: str) -> Path:
    return SKILLS_ROOT / skill / "scripts" / "legacy_codex_entry.py"


def validate_fixed_skill_commands(commands: list[tuple[str, list[str]]]) -> None:
    actual = tuple(skill for skill, _args in commands)
    if actual != EXPECTED_TOP1_SKILLS:
        raise RuntimeError(
            "fixed skill sequence mismatch: "
            f"expected={EXPECTED_TOP1_SKILLS!r}, actual={actual!r}"
        )


def json_objects(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    result: list[dict[str, Any]] = []
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def find_object(run: dict[str, Any], required_key: str) -> dict[str, Any]:
    for item in run["json_objects"]:
        if required_key in item:
            return item
    return {}


def business_artifact_path(run: dict[str, Any], artifact_name: str) -> Path | None:
    payload = find_object(run, "artifacts")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        return None
    binding = artifacts.get(artifact_name)
    if not isinstance(binding, dict):
        return None
    path = str(binding.get("path") or "").strip()
    return Path(path).expanduser().resolve() if path else None


def run_skill(skill: str, args: list[str], run_logs: Path) -> dict[str, Any]:
    entry = business_entry_for(skill)
    command = [sys.executable, str(entry), *args]
    started = time.perf_counter()
    started_ns = time.time_ns()
    result = run_process_tree(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
        env={
            **os.environ,
            "ONESTOCK_STOCK_CANONICAL_CHILD": "1",
        },
    )
    run_logs.mkdir(parents=True, exist_ok=True)
    stdout_path = run_logs / f"{skill}.stdout.txt"
    stderr_path = run_logs / f"{skill}.stderr.txt"
    atomic_write_text(stdout_path, result.stdout)
    atomic_write_text(stderr_path, result.stderr)
    return {
        "skill": skill,
        "command": command,
        "entry": artifact_state(entry),
        "returncode": result.returncode,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "started_ns": started_ns,
        "stdout_binding": artifact(stdout_path),
        "stderr_binding": artifact(stderr_path),
        "json_objects": json_objects(result.stdout),
    }


def close(left: Any, right: Any, tolerance: float = 0.0011) -> bool:
    try:
        return abs(float(left) - float(right)) <= tolerance
    except (TypeError, ValueError):
        return False


def exact_tail_value(node: Any, trade_date: str) -> tuple[bool, Any]:
    """Select one strictly valid persisted tail10 value for an exact trade date."""
    if not isinstance(node, dict) or not isinstance(trade_date, str):
        return False, None
    tail = node.get("tail10")
    if not isinstance(tail, list) or not tail:
        return False, None
    seen: set[str] = set()
    previous_date: str | None = None
    matched: list[Any] = []
    for item in tail:
        if not isinstance(item, list) or len(item) != 2:
            return False, None
        item_date, item_value = item
        if not isinstance(item_date, str) or len(item_date) != 8 or not item_date.isdigit():
            return False, None
        try:
            datetime.strptime(item_date, "%Y%m%d")
        except ValueError:
            return False, None
        if item_date in seen or (previous_date is not None and item_date <= previous_date):
            return False, None
        if isinstance(item_value, bool):
            return False, None
        try:
            numeric_value = float(item_value)
        except (TypeError, ValueError):
            return False, None
        if not math.isfinite(numeric_value):
            return False, None
        seen.add(item_date)
        previous_date = item_date
        if item_date == trade_date:
            matched.append(item_value)
    return (True, matched[0]) if len(matched) == 1 else (False, None)


def valid_score_positive(value: Any) -> tuple[bool, bool]:
    if isinstance(value, bool):
        return False, False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False, False
    return (True, number > 0) if math.isfinite(number) else (False, False)


def golden_c4_consistency(golden_hit: bool, condition: Any, earned_score: Any) -> tuple[bool, bool]:
    score_valid, score_positive = valid_score_positive(earned_score)
    return (
        isinstance(condition, bool) and golden_hit == condition,
        score_valid and golden_hit == score_positive,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="动态Top1固定技能交叉验收")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--attempt", required=True, type=int)
    args = parser.parse_args()

    scan = json.loads(args.input.read_text(encoding="utf-8"))
    if scan.get("status") != "PASS" or not scan.get("ranking_top10"):
        raise RuntimeError("scan is not PASS or Top10 is empty")
    run_id = str(scan.get("run_id") or "")
    if not run_id or (args.run_id is not None and str(args.run_id) != run_id):
        raise RuntimeError("Top1 validation run_id mismatch")
    scan_attempt = scan.get("market_attempt", scan.get("scan_attempt"))
    if isinstance(args.attempt, bool) or args.attempt < 1 or scan_attempt != args.attempt:
        raise RuntimeError("Top1 validation market_attempt mismatch")
    top1_dir = args.output.parent / "top1"
    run_logs = top1_dir / "fixed_skill_runs"
    golden_output = top1_dir / "top1_golden_ignition.json"
    feilong_output = top1_dir / "top1_feilong.json"
    bigbull_output_dir = top1_dir / "top1_big_bull"
    bigbull_output = bigbull_output_dir / "analysis_report.txt"
    top = scan["ranking_top10"][0]
    cutoff = str(scan["cutoff_trade_date"])
    bond_symbol = str(top["symbol"])
    bond_code, bond_market = bond_symbol.split(".")
    stock_symbol = str(top["underlying_symbol"])
    stock_code, stock_market = stock_symbol.split(".")
    master_path = Path(scan["source_files"]["convertible_bond_master"]["path"])
    tdx_root = master_path.parents[2]
    stock_day = tdx_root / "vipdoc" / stock_market.lower() / "lday" / f"{stock_market.lower()}{stock_code}.day"

    for target in (golden_output, feilong_output, bigbull_output_dir):
        if target.exists():
            raise RuntimeError(f"Top1 generation target already exists: {target}")

    commands = [
        (
            "stock-hard-gate",
            ["run", "--", HARD_GATE_VALIDATION_TEXT, "top1-cross-validation"],
        ),
        ("tdx-local-hub", ["run", "--", "kline", bond_symbol, "--limit", "10"]),
        ("golden-ignition", ["run", "--", bond_symbol, "--lookback", "10", "--name", str(top["name"]), "--output", str(golden_output)]),
        ("feilong-strategy", ["run", "--", stock_code, "--json"]),
        ("youzi-capital-monitoring", ["run", "--", "--day", str(stock_day), "--count", "10"]),
        (
            "big-bull-analysis-scoring-system",
            [
                "run",
                "--",
                "--output-dir",
                str(bigbull_output_dir),
                "analyze",
                stock_code,
            ],
        ),
    ]
    validate_fixed_skill_commands(commands)
    runs = {skill: run_skill(skill, skill_args, run_logs) for skill, skill_args in commands}

    def fresh_file(path: Path, skill: str) -> bool:
        return bool(path.is_file() and path.stat().st_mtime_ns >= int(runs[skill]["started_ns"]))

    hard_gate = find_object(runs["stock-hard-gate"], "status")
    tdx = find_object(runs["tdx-local-hub"], "records")
    golden_summary = find_object(runs["golden-ignition"], "result_path")
    golden = json.loads(golden_output.read_text(encoding="utf-8-sig")) if golden_output.is_file() else {}
    feilong_summary = find_object(runs["feilong-strategy"], "analysis_json")
    feilong_path = Path(str(feilong_summary.get("analysis_json") or ""))
    feilong = json.loads(feilong_path.read_text(encoding="utf-8-sig")) if feilong_path.is_file() else {}
    atomic_write_json(feilong_output, feilong)
    youzi = find_object(runs["youzi-capital-monitoring"], "tail")
    youzi_tail = youzi.get("tail") or []
    bigbull_report = business_artifact_path(
        runs["big-bull-analysis-scoring-system"],
        "analysis_report",
    )
    bigbull_text = bigbull_output.read_text(encoding="utf-8-sig") if bigbull_output.is_file() else ""
    tdx_records = tdx.get("records") or []

    scan_feilong = top.get("feilong") or {}
    youzi_raw = ((top.get("score_components") or {}).get("c6_youzi_inflow") or {}).get("raw_value") or {}
    scan_conditions = top.get("conditions") if isinstance(top.get("conditions"), dict) else {}
    scan_c4_condition = scan_conditions.get("c4_recent_ignition")
    scan_c4 = ((top.get("score_components") or {}).get("c4_golden_ignition") or {})
    golden_hit = golden.get("signal_status") == "HIT"
    c4_condition_match, c4_score_match = golden_c4_consistency(
        golden_hit,
        scan_c4_condition,
        scan_c4.get("earned_score"),
    )
    feilong_outputs = feilong.get("latest_outputs") or {}
    wave_found, fixed_wave = exact_tail_value(feilong_outputs.get("波"), cutoff)
    segment_found, fixed_segment = exact_tail_value(feilong_outputs.get("段"), cutoff)
    bigbull_red = "红K" in bigbull_text
    expected_bond_path = str(tdx_root / "vipdoc" / bond_market.lower() / "lday" / f"{bond_market.lower()}{bond_code}.day")

    checks = {
        "all_fixed_entries_exit_zero": all(item["returncode"] == 0 for item in runs.values()),
        "stock_hard_gate_preflight_pass": bool(
            hard_gate.get("status") == "PASS"
            and hard_gate.get("warnings") == []
        ),
        "golden_output_fresh": fresh_file(golden_output, "golden-ignition"),
        "feilong_output_fresh": fresh_file(feilong_path, "feilong-strategy"),
        "bigbull_output_fresh": bool(
            bigbull_report == bigbull_output.resolve()
            and fresh_file(bigbull_output, "big-bull-analysis-scoring-system")
        ),
        "tdx_target_exact": tdx.get("symbol") == bond_symbol and tdx.get("path") == expected_bond_path,
        "tdx_date_and_close_match_scan": bool(tdx_records) and tdx_records[-1].get("date") == cutoff and close(tdx_records[-1].get("close"), top.get("bond_close")),
        "golden_target_mapping_exact": golden_summary.get("status") == "PASS" and golden.get("input_symbol") == bond_symbol and golden.get("analysis_symbol") == stock_symbol and golden.get("target_type") == "convertible_bond",
        "golden_date_matches_scan": str(golden.get("latest_trading_date") or "").replace("-", "") == cutoff,
        "golden_signal_matches_scan_c4_condition": c4_condition_match,
        "golden_signal_matches_scan_c4_score": c4_score_match,
        "feilong_target_and_date_match": feilong.get("symbol") == stock_symbol and wave_found and segment_found,
        "feilong_values_match_scan": close(fixed_wave, scan_feilong.get("latest_wave")) and close(fixed_segment, scan_feilong.get("latest_segment")),
        "youzi_target_and_date_match": youzi.get("path") == str(stock_day) and bool(youzi_tail) and youzi_tail[-1].get("date") == cutoff,
        "youzi_values_match_scan": len(youzi_tail) >= 2 and close(youzi_tail[-1].get("买方意向"), youzi_raw.get("buy_latest")) and close(youzi_tail[-2].get("买方意向"), youzi_raw.get("buy_prev")),
        "bigbull_target_and_date_match": stock_code in bigbull_text and datetime.strptime(cutoff, "%Y%m%d").strftime("%Y-%m-%d") in bigbull_text,
        "bigbull_red_matches_scan": bigbull_red == bool(top.get("big_bull_red_preference")),
    }
    payload = {
        "schema": "CONVERTIBLE-BOND-SCREENING-TOP1-FIXED-SKILLS-1",
        "run_id": run_id,
        "market_attempt": args.attempt,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "scan_input": artifact(args.input),
        "target": {
            "rank": top["rank"],
            "bond_symbol": bond_symbol,
            "bond_name": top["name"],
            "underlying_symbol": stock_symbol,
            "underlying_name": top["underlying_name"],
            "trade_date": cutoff,
        },
        "checks": checks,
        "business_readback": {
            "stock_hard_gate_status": hard_gate.get("status"),
            "bond_close": tdx_records[-1].get("close") if tdx_records else None,
            "golden_signal": golden.get("signal_status"),
            "feilong_wave": fixed_wave,
            "feilong_segment": fixed_segment,
            "youzi_latest": youzi_tail[-1].get("买方意向") if youzi_tail else None,
            "youzi_previous": youzi_tail[-2].get("买方意向") if len(youzi_tail) >= 2 else None,
            "bigbull_red": bigbull_red,
        },
        "skill_runs": [
            {
                "skill": skill,
                "command": run["command"],
                "entry": run["entry"],
                "returncode": run["returncode"],
                "elapsed_seconds": run["elapsed_seconds"],
                "stdout_binding": run["stdout_binding"],
                "stderr_binding": run["stderr_binding"],
            }
            for skill, run in runs.items()
        ],
        "result_artifacts": {
            "golden": artifact_state(golden_output),
            "feilong": artifact_state(feilong_output),
            "bigbull": artifact_state(bigbull_output),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(args.output, payload)
    readback = json.loads(args.output.read_text(encoding="utf-8"))
    if readback.get("status") != payload["status"] or readback.get("target") != payload["target"]:
        raise RuntimeError("Top1 fixed-skill validation readback mismatch")
    print(json.dumps({
        "status": payload["status"],
        "output": str(args.output.resolve()),
        "size_bytes": args.output.stat().st_size,
        "sha256": sha256(args.output),
        "target": payload["target"],
        "checks": checks,
    }, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
