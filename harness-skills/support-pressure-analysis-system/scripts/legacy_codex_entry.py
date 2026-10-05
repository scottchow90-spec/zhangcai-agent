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

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unified_five_theory_conclusion import (
    UnifiedConclusionError,
    enrich_analysis_summary,
    persist_enriched_summary,
)

SKILL = 'support-pressure-analysis-system'
SOURCE_ID = 'support-pressure-analysis-system'
ROOT = Path(__file__).resolve().parents[1]
PRIMARY_REL = 'scripts/scientific_engine.py'
DEFAULT_ARGS = []
FORBIDDEN = (".openclaw\\workspace\\skills", ".openclaw/workspace/skills", "stock_skill_executor", "stock-skill-executor")


def selftest() -> int:
    errors: list[str] = []
    current_entry = Path(__file__).resolve()
    scripts = sorted((ROOT / "scripts").glob("*.py"))
    for script in scripts:
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"compile:{script.name}:{exc.msg}")
    if PRIMARY_REL:
        primary = ROOT / PRIMARY_REL
        if not primary.is_file():
            errors.append(f"primary_missing:{primary}")
    for path in ROOT.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or "merged_sources" in path.parts:
            continue
        if path.resolve() == current_entry:
            continue
        if path.suffix.lower() not in {".md", ".py", ".ps1", ".js", ".mjs", ".json", ".yaml", ".yml", ".txt", ".toml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeError:
            continue
        if path.name == "SKILL.md" and "原始业务资产来自" in text:
            text = text.split("原始业务资产来自", 1)[0]
        for marker in FORBIDDEN:
            if marker in text:
                errors.append(f"forbidden_runtime_dependency:{path.relative_to(ROOT)}:{marker}")
    payload = {"status": "PASS" if not errors else "FAIL", "skill": SKILL, "source_id": SOURCE_ID, "primary": PRIMARY_REL, "compiled_scripts": len(scripts), "errors": errors}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def run_primary(extra: list[str]) -> int:
    if not PRIMARY_REL:
        print(json.dumps({"status": "PROCEDURAL", "skill": SKILL, "reason": "no independent local business script; follow SKILL.md and references"}, ensure_ascii=False, indent=2))
        return 0
    primary = ROOT / PRIMARY_REL
    args = extra if extra else [arg.replace("{workspace}", str(Path.home() / ".codex")) for arg in DEFAULT_ARGS]
    completed = subprocess.run(
        [sys.executable, str(primary), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        if completed.stdout:
            sys.stdout.write(completed.stdout)
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        return completed.returncode
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        if completed.stdout:
            sys.stdout.write(completed.stdout)
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        return completed.returncode
    is_standard_analysis = (
        isinstance(payload, dict)
        and payload.get("status") == "PASS"
        and isinstance(payload.get("items"), list)
    )
    if not is_standard_analysis:
        if completed.stdout:
            sys.stdout.write(completed.stdout)
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        return completed.returncode
    try:
        summary_artifact = payload.get("summary_artifact")
        if not isinstance(summary_artifact, dict) or not summary_artifact.get("path"):
            raise UnifiedConclusionError("analysis_summary_artifact_missing")
        enriched = enrich_analysis_summary(payload)
        final_summary = persist_enriched_summary(enriched, str(summary_artifact["path"]))
    except (UnifiedConclusionError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        blocked = {
            "status": "BLOCKED",
            "skill": SKILL,
            "error": f"unified_five_theory_delivery_failed:{type(exc).__name__}:{exc}",
        }
        print(json.dumps(blocked, ensure_ascii=False, indent=2))
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        return 2
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    print(json.dumps(final_summary, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("info", "selftest", "run"), nargs="?", default="info")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args()
    if parsed.command == "info":
        print(json.dumps({"skill": SKILL, "source_id": SOURCE_ID, "primary": PRIMARY_REL, "default_args": DEFAULT_ARGS, "runtime": "Codex"}, ensure_ascii=False, indent=2))
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
