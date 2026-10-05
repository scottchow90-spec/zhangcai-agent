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
import os
import py_compile
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_app_root, resolve_tdx_root

DUAN_CLIENT = resolve_app_root() / "harness-skills" / "a-share-hotspot-sentiment-analysis" / "scripts" / "duanxianxia_client.ps1"
sys.path.insert(0, str(SCRIPTS))
from live_snapshot import build_snapshot
from sentiment_engine import SnapshotValidationError, analyze_snapshot


def collect_duanxian(output: Path) -> None:
    command = (
        f"& '{DUAN_CLIENT}' -Dataset @('ztcount','ztpool','jinjidata','amount') "
        f"-Output '{output}'"
    )
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    if completed.returncode != 0 or not output.is_file():
        raise RuntimeError(f"duanxianxia_collection_failed:{completed.returncode}:{completed.stderr.strip()}")


def run(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = run_dir / "sentiment_snapshot.json"
    result_path = run_dir / "sentiment_result.json"
    try:
        if args.snapshot:
            snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        else:
            lianban_raw = os.environ.get("CODEX_LIANBAN_SNAPSHOT", "")
            if os.environ.get("CODEX_LIANBAN_STATUS") != "CLEAN_PASS" or not lianban_raw:
                raise RuntimeError("canonical_lianban_snapshot_missing_or_degraded")
            duan_path = run_dir / "duanxianxia-live.json"
            collect_duanxian(duan_path)
            snapshot = build_snapshot(Path(lianban_raw), duan_path, Path(args.tdx_root))
        snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result = analyze_snapshot(snapshot)
        result["artifacts"] = {"snapshot": str(snapshot_path), "result": str(result_path)}
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, SnapshotValidationError) as exc:
        blocked = {
            "schema": "SHORT_TERM_MARKET_SENTIMENT_V1",
            "status": "BLOCKED",
            "errors": [f"{type(exc).__name__}:{exc}"],
            "missing": ["required_current_market_evidence"],
        }
        result_path.write_text(json.dumps(blocked, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(blocked, ensure_ascii=False))
        return 2


def selftest() -> int:
    errors: list[str] = []
    for script in SCRIPTS.glob("*.py"):
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"compile:{script.name}:{exc.msg}")
    for path in (DUAN_CLIENT, ROOT / "references" / "source-asset.json"):
        if not path.is_file():
            errors.append(f"missing:{path}")
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "skill": ROOT.name, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--run-dir", required=True)
    run_parser.add_argument("--snapshot")
    run_parser.add_argument("--tdx-root", default=str(resolve_tdx_root()))
    sub.add_parser("selftest")
    args = parser.parse_args()
    return selftest() if args.command == "selftest" else run(args)


if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())

