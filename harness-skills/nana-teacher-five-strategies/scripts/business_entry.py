#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
import py_compile
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_tdx_root


SKILL = "nana-teacher-five-strategies"
DISPLAY_NAME = "娜娜老师5策略"
ROOT = Path(__file__).resolve().parents[1]
FIXED_ENTRY = ROOT / "scripts" / "codex_entry.py"
REGISTRY_PATH = ROOT / "references" / "strategy_registry.json"
MANIFEST_PATH = ROOT / "references" / "asset_manifest.json"
RUNNER = ROOT / "scripts" / "run_nana_five.py"
EXPORTER = ROOT / "scripts" / "export_assets.py"
QUOTE_FETCHER = ROOT / "scripts" / "nana_quote_fetcher.py"
TDX_ROOT = resolve_tdx_root()
FRESHNESS_GATE = ROOT / "scripts" / "nana_market_data.py"
SELECTOR_FRESHNESS_GUARD = ROOT / "scripts" / "nana_freshness_guard.py"
DAY_RECORD = struct.Struct("<IIIIIfII")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_trade_date(value: object) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits if re.fullmatch(r"20\d{6}", digits) else ""


def infer_local_business_trade_date() -> tuple[str, int, int]:
    counts: Counter[str] = Counter()
    files = 0
    for market in ("sh", "sz"):
        folder = TDX_ROOT / "vipdoc" / market / "lday"
        for path in folder.glob(f"{market}*.day"):
            files += 1
            try:
                if path.stat().st_size < DAY_RECORD.size:
                    continue
                with path.open("rb") as handle:
                    handle.seek(-DAY_RECORD.size, 2)
                    value = str(DAY_RECORD.unpack(handle.read(DAY_RECORD.size))[0])
                if re.fullmatch(r"20\d{6}", value):
                    counts[value] += 1
            except (OSError, struct.error):
                continue
    if not counts:
        return "", files, 0
    coverage_floor = max(1000, int(files * 0.40))
    covered = [(value, count) for value, count in counts.items() if count >= coverage_floor]
    latest = max(value for value, _count in covered) if covered else counts.most_common(1)[0][0]
    return latest, files, counts[latest]


def quote_json_requested(extra: list[str]) -> bool:
    for index, value in enumerate(extra):
        if value == "--quote-json" and index + 1 < len(extra):
            return bool(str(extra[index + 1]).strip())
        if value.startswith("--quote-json="):
            return bool(value.split("=", 1)[1].strip())
    return False


def option_value(extra: list[str], option: str) -> str:
    for index, value in enumerate(extra):
        if value == option and index + 1 < len(extra):
            return str(extra[index + 1]).strip()
        if value.startswith(option + "="):
            return value.split("=", 1)[1].strip()
    return ""


def add_current_quote_route(extra: list[str], date_gate: dict) -> tuple[list[str], dict]:
    if quote_json_requested(extra):
        return extra, date_gate
    local_date = normalize_trade_date(date_gate.get("local_business_trade_date"))
    live_date = normalize_trade_date(date_gate.get("latest_market_trade_date"))
    if not live_date or local_date == live_date:
        return extra, date_gate
    output_dir_raw = option_value(extra, "--output-dir")
    output_dir = (
        Path(output_dir_raw).resolve()
        if output_dir_raw
        else (Path.cwd() / "outputs" / "娜娜老师5策略_运行").resolve()
    )
    quote_path = output_dir / f"nana_current_quotes_{live_date}.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(QUOTE_FETCHER),
            "--trade-date",
            live_date,
            "--output",
            str(quote_path),
        ],
        cwd=str(Path.cwd()),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
        check=False,
    )
    if completed.returncode != 0 or not quote_path.is_file():
        failed = dict(date_gate)
        failed["status"] = "BLOCKED"
        failed["reason"] = "CURRENT_QUOTE_FETCH_BLOCKED"
        failed["errors"] = [
            *(date_gate.get("errors") or []),
            f"quote_fetch_exit_code:{completed.returncode}",
            completed.stderr[-500:] or completed.stdout[-500:],
        ]
        return extra, failed
    routed = [*extra, "--target-date", live_date, "--quote-json", str(quote_path)]
    return routed, enforce_live_business_date(routed)


def requested_trade_date(extra: list[str], local_trade_date: str) -> str:
    explicit = ""
    quote_path = ""
    for index, value in enumerate(extra):
        if value == "--target-date" and index + 1 < len(extra):
            explicit = normalize_trade_date(extra[index + 1])
        elif value.startswith("--target-date="):
            explicit = normalize_trade_date(value.split("=", 1)[1])
        elif value == "--quote-json" and index + 1 < len(extra):
            quote_path = extra[index + 1]
        elif value.startswith("--quote-json="):
            quote_path = value.split("=", 1)[1]
    if explicit:
        return explicit
    if quote_path:
        try:
            quote_date = normalize_trade_date(load_json(Path(quote_path).resolve()).get("trade_date"))
            if quote_date:
                return quote_date
        except Exception:
            return ""
    return local_trade_date


def evaluate_business_date(
    local_trade_date: str,
    requested_date: str,
    live_trade_date: str,
    *,
    quote_route_requested: bool = False,
) -> dict:
    errors: list[str] = []
    if not local_trade_date:
        errors.append("local_business_trade_date_missing")
    if not requested_date:
        errors.append("requested_trade_date_missing")
    if not live_trade_date:
        errors.append("live_trade_date_missing")
    if (
        local_trade_date
        and live_trade_date
        and local_trade_date != live_trade_date
        and not quote_route_requested
    ):
        errors.append(f"stale_local_business_trade_date:{local_trade_date}!={live_trade_date}")
    if requested_date and live_trade_date and requested_date != live_trade_date:
        errors.append(f"stale_requested_trade_date:{requested_date}!={live_trade_date}")
    return {
        "status": "PASS" if not errors else "BLOCKED",
        "reason": None if not errors else "STALE_BUSINESS_DATA_DATE",
        "local_business_trade_date": local_trade_date,
        "requested_trade_date": requested_date,
        "latest_market_trade_date": live_trade_date,
        "quote_route_requested": quote_route_requested,
        "pending_data_route": (
            "validated_quote_append_inner_gate"
            if quote_route_requested
            else "local_day_inner_gate"
        ),
        "errors": errors,
    }


def enforce_live_business_date(extra: list[str]) -> dict:
    local_date, local_files, local_coverage = infer_local_business_trade_date()
    requested_date = requested_trade_date(extra, local_date)
    quote_route = quote_json_requested(extra)
    try:
        spec = importlib.util.spec_from_file_location("nana_stock_freshness_gate", FRESHNESS_GATE)
        if spec is None or spec.loader is None:
            raise RuntimeError("freshness_gate_loader_unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        snapshot = module.resolve_market_snapshot()
        live_date = normalize_trade_date(snapshot.get("latest_available_trade_date"))
        result = evaluate_business_date(
            local_date,
            requested_date,
            live_date,
            quote_route_requested=quote_route,
        )
        result.update({
            "schema": "nana-business-date-gate/v1",
            "skill": SKILL,
            "local_files": local_files,
            "local_latest_coverage": local_coverage,
            "market_snapshot": snapshot,
        })
        return result
    except Exception as exc:
        return {
            "schema": "nana-business-date-gate/v1",
            "status": "BLOCKED",
            "reason": "MARKET_DATE_UNVERIFIED",
            "skill": SKILL,
            "local_business_trade_date": local_date,
            "requested_trade_date": requested_date,
            "quote_route_requested": quote_route,
            "local_files": local_files,
            "local_latest_coverage": local_coverage,
            "errors": [f"market_snapshot_unavailable:{type(exc).__name__}:{exc}"],
        }


def info() -> int:
    registry = load_json(REGISTRY_PATH)
    payload = {
        "status": "READY",
        "skill": SKILL,
        "display_name": DISPLAY_NAME,
        "fixed_entry": str(FIXED_ENTRY),
        "commands": ["info", "selftest", "run", "export"],
        "strategy_count": len(registry.get("strategies", [])),
        "strategies": [item.get("name") for item in registry.get("strategies", [])],
        "runtime": "local Codex + C:\\new_tdx_mock",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def selftest() -> int:
    errors: list[str] = []
    compiled: list[str] = []
    with tempfile.TemporaryDirectory(prefix="nana-five-skill-compile-") as raw_temp:
        compile_dir = Path(raw_temp)
        for script in sorted((ROOT / "scripts").glob("*.py")):
            try:
                py_compile.compile(str(script), cfile=str(compile_dir / f"{script.stem}.pyc"), doraise=True)
                compiled.append(script.name)
            except py_compile.PyCompileError as exc:
                errors.append(f"compile:{script.name}:{exc.msg}")
    try:
        registry = load_json(REGISTRY_PATH)
    except Exception as exc:
        registry = {}
        errors.append(f"registry:{type(exc).__name__}:{exc}")
    try:
        manifest = load_json(MANIFEST_PATH)
    except Exception as exc:
        manifest = {}
        errors.append(f"manifest:{type(exc).__name__}:{exc}")

    strategies = registry.get("strategies") if isinstance(registry, dict) else None
    if not isinstance(strategies, list) or len(strategies) != 5:
        errors.append("strategy_count_not_5")
        strategies = []
    names = [str(item.get("name", "")) for item in strategies if isinstance(item, dict)]
    if names != ["元宝藏金", "地极破晓", "游龙吸水", "负阴抱阳", "黄金双响"]:
        errors.append(f"strategy_order_or_names:{names}")

    category_counts = {"formula": 0, "workflow": 0, "evidence": 0}
    for item in strategies:
        if not isinstance(item, dict):
            continue
        strategy = str(item.get("name", ""))
        formula = ROOT / str(item.get("formula", ""))
        workflow = ROOT / str(item.get("workflow", ""))
        evidence = ROOT / str(item.get("evidence", ""))
        for path, category in ((formula, "formula"), (workflow, "workflow"), (evidence, "evidence")):
            if not path.is_file():
                errors.append(f"missing_{category}:{path}")
            else:
                category_counts[category] += 1
        if formula.is_file():
            text = formula.read_text(encoding="utf-8-sig")
            for marker in item.get("required_formula_markers", []):
                if str(marker) not in text:
                    errors.append(f"formula_marker:{strategy}:{marker}")
        if workflow.is_file():
            text = workflow.read_text(encoding="utf-8-sig")
            if formula.name not in text:
                errors.append(f"workflow_formula_reference:{strategy}")
        if evidence.is_file():
            try:
                evidence_payload = load_json(evidence)
            except Exception as exc:
                errors.append(f"evidence_json:{strategy}:{exc}")
            else:
                if evidence_payload.get("strategy") != strategy:
                    errors.append(f"evidence_strategy:{strategy}")
                if not str(evidence_payload.get("status", "")).startswith("PASS"):
                    errors.append(f"evidence_status:{strategy}")
        source = Path(str(item.get("source_pptx", "")))
        expected_source_hash = str(item.get("source_sha256", ""))
        if not source.is_file():
            errors.append(f"source_missing:{source}")
        elif sha256(source) != expected_source_hash:
            errors.append(f"source_hash_mismatch:{source}")

    if category_counts != {"formula": 5, "workflow": 5, "evidence": 5}:
        errors.append(f"asset_counts:{category_counts}")

    manifest_items = manifest.get("items") if isinstance(manifest, dict) else None
    if not isinstance(manifest_items, list) or len(manifest_items) != 16:
        errors.append("asset_manifest_item_count_not_16")
        manifest_items = []
    for item in manifest_items:
        if not isinstance(item, dict):
            errors.append("asset_manifest_item_not_object")
            continue
        path = ROOT / str(item.get("path", ""))
        if not path.is_file():
            errors.append(f"manifest_missing:{path}")
            continue
        actual_hash = sha256(path)
        actual_size = path.stat().st_size
        if actual_hash != str(item.get("sha256", "")) or actual_size != int(item.get("size_bytes", -1)):
            errors.append(f"manifest_hash_or_size:{path.relative_to(ROOT)}")

    runtime = {
        "tdx_root_exists": TDX_ROOT.is_dir(),
        "vipdoc_exists": (TDX_ROOT / "vipdoc").is_dir(),
        "sh_day_exists": (TDX_ROOT / "vipdoc" / "sh" / "lday").is_dir(),
        "sz_day_exists": (TDX_ROOT / "vipdoc" / "sz" / "lday").is_dir(),
    }
    for name, passed in runtime.items():
        if not passed:
            errors.append(f"runtime:{name}")
    if evaluate_business_date("20260721", "20260721", "20260721")["status"] != "PASS":
        errors.append("business_date_gate_current_case_failed")
    stale_case = evaluate_business_date("20260720", "20260720", "20260721")
    if stale_case["status"] != "BLOCKED" or stale_case.get("reason") != "STALE_BUSINESS_DATA_DATE":
        errors.append("business_date_gate_stale_case_not_blocked")
    quote_route_case = evaluate_business_date(
        "20260720",
        "20260721",
        "20260721",
        quote_route_requested=True,
    )
    if quote_route_case["status"] != "PASS":
        errors.append("business_date_gate_validated_quote_route_not_deferred")
    stale_quote_route_case = evaluate_business_date(
        "20260720",
        "20260720",
        "20260721",
        quote_route_requested=True,
    )
    if stale_quote_route_case["status"] != "BLOCKED" or not any(
        str(item).startswith("stale_requested_trade_date:")
        for item in stale_quote_route_case.get("errors", [])
    ):
        errors.append("business_date_gate_stale_quote_route_not_blocked")
    try:
        guard_spec = importlib.util.spec_from_file_location(
            "nana_selector_freshness_guard_selftest", SELECTOR_FRESHNESS_GUARD
        )
        if guard_spec is None or guard_spec.loader is None:
            raise RuntimeError("selector_freshness_guard_loader_unavailable")
        guard_module = importlib.util.module_from_spec(guard_spec)
        guard_spec.loader.exec_module(guard_module)
        guard_selftest = guard_module.selftest()
        if guard_selftest.get("status") != "PASS":
            errors.append(f"selector_freshness_guard_selftest:{guard_selftest}")
    except Exception as exc:
        guard_selftest = {"status": "FAIL", "error": f"{type(exc).__name__}:{exc}"}
        errors.append(f"selector_freshness_guard_unavailable:{type(exc).__name__}:{exc}")
    try:
        scanner_path = ROOT / "scripts" / "nana_five_strategy_scanner.py"
        scanner_spec = importlib.util.spec_from_file_location(
            "nana_quality_scoring_selftest", scanner_path
        )
        if scanner_spec is None or scanner_spec.loader is None:
            raise RuntimeError("quality_scanner_loader_unavailable")
        scanner_module = importlib.util.module_from_spec(scanner_spec)
        scanner_spec.loader.exec_module(scanner_module)
        strong = {
            "close": 10.0,
            "ma5": 9.0,
            "ma10": 8.0,
            "ma20": 7.0,
            "pct_change": 3.0,
            "amount_yi": 10.0,
            "invalidation": 9.0,
        }
        weak = {
            "close": 10.0,
            "ma5": 11.0,
            "ma10": 12.0,
            "ma20": 13.0,
            "pct_change": -2.0,
            "amount_yi": 0.3,
            "invalidation": 5.0,
        }
        strong_metrics = {
            "forward_3d": {"average_pct": 1.0, "win_rate_pct": 55.0},
            "forward_5d": {"average_pct": 1.0, "win_rate_pct": 55.0},
        }
        weak_metrics = {
            "forward_3d": {"average_pct": -3.0, "win_rate_pct": 20.0},
            "forward_5d": {"average_pct": -3.0, "win_rate_pct": 20.0},
        }
        scanner_module.apply_quality_score(strong, strong_metrics)
        scanner_module.apply_quality_score(weak, weak_metrics)
        quality_checks = {
            "strong_passes": strong.get("quality_gate_pass") is True,
            "strong_is_priority": strong.get("quality_tier") == "优先复核",
            "weak_is_blocked": weak.get("quality_gate_pass") is False,
            "weak_is_observation": weak.get("quality_tier") == "观察",
            "strong_scores_above_weak": float(strong.get("quality_score", -1))
            > float(weak.get("quality_score", -1)),
            "scores_in_range": all(
                0.0 <= float(item.get("quality_score", -1)) <= 100.0
                for item in (strong, weak)
            ),
        }
        quality_selftest = {
            "status": "PASS" if all(quality_checks.values()) else "FAIL",
            "strong_score": strong.get("quality_score"),
            "weak_score": weak.get("quality_score"),
            "checks": quality_checks,
        }
        if quality_selftest["status"] != "PASS":
            errors.append(f"quality_scoring_selftest:{quality_selftest}")
    except Exception as exc:
        quality_selftest = {"status": "FAIL", "error": f"{type(exc).__name__}:{exc}"}
        errors.append(f"quality_scoring_unavailable:{type(exc).__name__}:{exc}")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "skill": SKILL,
        "display_name": DISPLAY_NAME,
        "strategy_count": len(strategies),
        "asset_counts": category_counts,
        "compiled_scripts": compiled,
        "manifest_item_count": len(manifest_items),
        "runtime": runtime,
        "selector_freshness_guard": guard_selftest,
        "quality_scoring": quality_selftest,
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def run_script(path: Path, extra: list[str]) -> int:
    if not path.is_file():
        print(json.dumps({"status": "FAIL", "reason": f"missing script: {path}"}, ensure_ascii=False))
        return 2
    return subprocess.run([sys.executable, str(path), *extra], cwd=str(Path.cwd())).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("info", "selftest", "run", "export"), nargs="?", default="info")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args()
    if parsed.command == "info":
        return info()
    if parsed.command == "selftest":
        return selftest()
    extra = parsed.args[1:] if parsed.args and parsed.args[0] == "--" else parsed.args
    if parsed.command == "run":
        date_gate = enforce_live_business_date(extra)
        extra, date_gate = add_current_quote_route(extra, date_gate)
        if date_gate.get("status") != "PASS":
            print(json.dumps(date_gate, ensure_ascii=False, indent=2))
            return 2
    return run_script(RUNNER if parsed.command == "run" else EXPORTER, extra)


if __name__ == "__main__":
    raise SystemExit(main())
