#!/usr/bin/env python3
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
import py_compile
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT.name
PRIMARY_REL = "scripts/merged_workflow.py"
PRIMARY = ROOT / PRIMARY_REL
CONFIG = ROOT / "references" / "merge-config.json"
MANIFEST = ROOT / "references" / "source-manifest.json"
REQUIRED = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/workflow.md",
    "references/merge-config.json",
    "references/source-manifest.json",
    "references/2026-08-23-scientific-forecast-design.md",
    "references/2026-08-23-scientific-forecast-implementation-plan.md",
    "scripts/codex_entry.py",
    "scripts/canonical_business_adapter.py",
    "scripts/legacy_codex_entry.py",
    PRIMARY_REL,
    "scripts/point_in_time_snapshot.py",
    "scripts/market_features.py",
    "scripts/future_labels.py",
    "scripts/forecast_model.py",
    "scripts/walk_forward_backtest.py",
    "scripts/catalyst_features.py",
    "scripts/leader_ranker.py",
    "scripts/forecast_gate.py",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selftest() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"required_missing_or_empty:{relative}")
    for script in sorted((ROOT / "scripts").glob("*.py")):
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"compile:{script.name}:{exc.msg}")
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        discoverable = sorted(
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("SKILL.md")
        )
        if discoverable != ["SKILL.md"]:
            errors.append(f"nested_discoverable_skills:{discoverable}")
        for source in manifest["sources"]:
            component_root = ROOT / "components" / source
            if not (component_root / "SOURCE_SKILL.md").is_file():
                errors.append(f"source_skill_snapshot_missing:{source}")
            entries = manifest["files"][source]
            actual = sorted(
                path.relative_to(component_root).as_posix()
                for path in component_root.rglob("*")
                if path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix.casefold() != ".pyc"
            )
            if actual != sorted(entries):
                errors.append(f"manifest_file_set_mismatch:{source}")
                continue
            for relative, expected in entries.items():
                if sha256_file(component_root / relative) != expected:
                    errors.append(f"manifest_hash_mismatch:{source}:{relative}")
    except Exception as exc:
        errors.append(f"manifest_error:{type(exc).__name__}:{exc}")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "skill": SKILL,
        "primary": PRIMARY_REL,
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def run_primary(extra: list[str]) -> int:
    return subprocess.run(
        [sys.executable, str(PRIMARY), *extra],
        cwd=str(ROOT),
    ).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("info", "selftest", "run"), nargs="?", default="info")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if parsed.command == "info":
        print(json.dumps({
            "skill": SKILL,
            "display_name": config["display_name"],
            "default_mode": config["default_mode"],
            "modes": ["all", *config["modes"]],
            "runtime": "Codex",
        }, ensure_ascii=False, indent=2))
        return 0
    if parsed.command == "selftest":
        return selftest()
    extra = parsed.args[1:] if parsed.args and parsed.args[0] == "--" else parsed.args
    return run_primary(extra)


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
