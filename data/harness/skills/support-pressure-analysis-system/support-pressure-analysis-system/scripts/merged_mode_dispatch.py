#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "scientific_engine.py"
MODES = ("pressure", "resistance", "technical")


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified support, resistance, and technical-analysis dispatcher")
    parser.add_argument("--mode", choices=MODES, default="pressure")
    parser.add_argument("--route-check", action="store_true")
    args, extra = parser.parse_known_args()
    if extra and extra[0] == "--":
        extra = extra[1:]
    target = ENGINE
    if not target.is_file():
        print(json.dumps({"status": "BLOCKED", "mode": args.mode, "error": "absorbed_mode_entry_missing", "target": str(target)}, ensure_ascii=False))
        return 2
    if args.route_check:
        print(json.dumps({"status": "CLEAN_PASS", "mode": args.mode, "target": str(target), "target_size": target.stat().st_size, "route": "single_scientific_engine"}, ensure_ascii=False))
        return 0
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, str(target), "--mode", args.mode, *extra], cwd=str(ROOT), env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
