#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_ENTRY = ROOT / "scripts" / "entry_stock_analysis.py"
FUNDAMENTAL_ENTRY = ROOT / "merged_sources" / "stock-research-engine" / "scripts" / "run_stock_research_engine.py"
SENIOR_ENTRY = ROOT / "merged_sources" / "stock-study" / "scripts" / "run_stock_study.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified individual-stock analysis dispatcher")
    parser.add_argument("--mode", choices=("local-a-share", "fundamental-research", "senior-equity"), default="local-a-share")
    parser.add_argument("--route-check", action="store_true")
    args, extra = parser.parse_known_args()
    if extra and extra[0] == "--":
        extra = extra[1:]

    if args.mode == "local-a-share":
        target = LOCAL_ENTRY
        command = [sys.executable, str(target), *extra]
    else:
        target = FUNDAMENTAL_ENTRY if args.mode == "fundamental-research" else SENIOR_ENTRY
        if "--out" not in extra:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            out = ROOT / "reports" / "audit" / f"{args.mode}-{stamp}.json"
            extra.extend(["--out", str(out)])
        command = [sys.executable, str(target), *extra]

    if not target.is_file():
        print(json.dumps({"status": "BLOCKED", "mode": args.mode, "error": "absorbed_mode_entry_missing", "target": str(target)}, ensure_ascii=False))
        return 2
    if args.route_check:
        print(json.dumps({"status": "CLEAN_PASS", "mode": args.mode, "target": str(target), "target_size": target.stat().st_size}, ensure_ascii=False))
        return 0
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    return subprocess.run(command, cwd=str(ROOT), env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
