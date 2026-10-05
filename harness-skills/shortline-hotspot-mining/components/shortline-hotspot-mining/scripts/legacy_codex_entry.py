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
import py_compile
import subprocess
import sys
from pathlib import Path

SKILL = "shortline-hotspot-mining"
ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "scripts" / "run.py"
REQUIRED = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/business_spec.md",
    "references/workflow.md",
    "references/scoring_and_evidence.md",
    "scripts/run.py",
    "scripts/preflight.py",
    "scripts/tdx_sector_pct.py",
)
FORBIDDEN_SCRIPT_MARKERS = (
    ".openclaw\\workspace\\skills",
    ".openclaw/workspace/skills",
    "skills\\hotspot-mining\\",
    "skills/hotspot-mining/",
    "skills\\wf2-hotspot-mining\\",
    "skills/wf2-hotspot-mining/",
    "skills\\daily-hotspot-mine\\",
    "skills/daily-hotspot-mine/",
)


def selftest() -> int:
    errors: list[str] = []
    if ROOT.name != SKILL:
        errors.append(f"root_name:{ROOT.name}")
    for rel in REQUIRED:
        path = ROOT / rel
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"required_missing_or_empty:{rel}")
    scripts = sorted((ROOT / "scripts").glob("*.py"))
    for script in scripts:
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"compile:{script.name}:{exc.msg}")
        if script.resolve() == Path(__file__).resolve():
            continue
        text = script.read_text(encoding="utf-8-sig", errors="replace")
        for marker in FORBIDDEN_SCRIPT_MARKERS:
            if marker in text:
                errors.append(f"old_runtime_dependency:{script.name}:{marker}")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "skill": SKILL,
        "root": str(ROOT),
        "primary": str(PRIMARY),
        "compiled_scripts": len(scripts),
        "required_files": len(REQUIRED),
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def run_primary(extra: list[str]) -> int:
    if not PRIMARY.is_file():
        print(json.dumps({"status": "BLOCKED", "reason": f"missing {PRIMARY}"}, ensure_ascii=False))
        return 2
    return subprocess.run([sys.executable, str(PRIMARY), *extra], cwd=str(ROOT)).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="短线热点挖掘唯一 Codex 入口")
    parser.add_argument("command", choices=("info", "selftest", "run"), nargs="?", default="info")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command == "info":
        print(json.dumps({
            "skill": SKILL,
            "display_name": "短线热点挖掘",
            "root": str(ROOT),
            "primary": str(PRIMARY),
            "modes": ["full", "discovery", "daily"],
            "runtime": "Codex",
        }, ensure_ascii=False, indent=2))
        return 0
    if args.command == "selftest":
        return selftest()
    extra = args.args[1:] if args.args and args.args[0] == "--" else args.args
    return run_primary(extra)


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
