#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import struct
import subprocess
import sys
from pathlib import Path
import sys

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_tdx_root


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "audit_entry.py"


def latest_trade_date() -> str:
    dates: list[str] = []
    for path in (
        resolve_tdx_root() / "vipdoc" / "sh" / "lday" / "sh000001.day",
        resolve_tdx_root() / "vipdoc" / "sz" / "lday" / "sz399001.day",
        resolve_tdx_root() / "vipdoc" / "sz" / "lday" / "sz000001.day",
    ):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if len(raw) >= 32 and len(raw) % 32 == 0:
            dates.append(str(struct.unpack("<I", raw[-32:-28])[0]))
    if not dates:
        raise RuntimeError("TDX benchmark data unavailable")
    return max(dates)


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified limit-up mining dispatcher", add_help=True)
    parser.add_argument("--variant", choices=("unified", "v2"), default="unified")
    parser.add_argument("--route-check", action="store_true")
    args, extra = parser.parse_known_args()
    if extra and extra[0] == "--":
        extra = extra[1:]
    variant = args.variant
    if "--mode" in extra:
        index = extra.index("--mode")
        if index + 1 < len(extra) and extra[index + 1] == "v2":
            variant = "v2"
            del extra[index:index + 2]

    if not TARGET.is_file():
        print(json.dumps({"status": "BLOCKED", "error": "unified_entry_missing", "target": str(TARGET)}, ensure_ascii=False))
        return 2
    if args.route_check:
        print(json.dumps({"status": "CLEAN_PASS", "variant": variant, "target": str(TARGET), "target_size": TARGET.stat().st_size}, ensure_ascii=False))
        return 0

    if variant == "v2":
        if "--mode" not in extra:
            extra = ["--mode", "daily", *extra]
        if "--date" not in extra:
            extra.extend(["--date", latest_trade_date()])
        if "--manual-confirm" not in extra:
            extra.append("--manual-confirm")

    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, str(TARGET), *extra], cwd=str(ROOT), env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
