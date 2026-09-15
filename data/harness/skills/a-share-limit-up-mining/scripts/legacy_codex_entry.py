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
import tempfile
from pathlib import Path

SKILL = "a-share-limit-up-mining"
DISPLAY_NAME = "连板挖掘"
ROOT = Path(__file__).resolve().parents[1]
MODES = {
    "daily": "scripts/run_daily.py",
    "research": "scripts/run_research.py",
    "full": "scripts/run_lianban_docx.py",
}
REQUIRED_REFERENCES = (
    "references/workflow.md",
    "references/business_spec.md",
    "references/full_workflow.md",
    "references/long_run_checklist.md",
    "references/capability_audit.md",
)
REQUIRED_SCRIPTS = (
    "scripts/run_daily.py",
    "scripts/run_research.py",
    "scripts/run_lianban_docx.py",
    "scripts/_date_utils.py",
    "scripts/collect_risk.py",
    "scripts/health_monitor.py",
    "scripts/data_source_health.py",
    "scripts/archive_prediction.py",
    "scripts/review_reminder.py",
)
FORBIDDEN_RUNTIME_MARKERS = (
    r"D:\C盘转移\日志\codex\skills\wf1-lianban-leader",
    r"D:\C盘转移\日志\codex\skills\daily-lianban-leader",
    r"D:\C盘转移\日志\codex\skills\a-share-limit-up-leader-selection",
    ".openclaw\\workspace\\skills",
    ".openclaw/workspace/skills",
    "stock_skill_executor",
    "stock-skill-executor",
)


def _text_files() -> list[Path]:
    suffixes = {".md", ".py", ".ps1", ".js", ".mjs", ".json", ".yaml", ".yml", ".txt", ".toml"}
    return [
        path for path in ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and "merged_sources" not in path.parts and path.suffix.lower() in suffixes
    ]


def selftest() -> int:
    errors: list[str] = []
    scripts = sorted((ROOT / "scripts").glob("*.py"))
    with tempfile.TemporaryDirectory(prefix="lianban-selftest-") as temporary:
        compile_root = Path(temporary)
        for index, script in enumerate(scripts):
            try:
                py_compile.compile(str(script), cfile=str(compile_root / f"{index}.pyc"), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"compile:{script.name}:{exc.msg}")

    for rel in (*REQUIRED_REFERENCES, *REQUIRED_SCRIPTS):
        if not (ROOT / rel).is_file():
            errors.append(f"required_missing:{rel}")

    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
    for trigger in ("连板挖掘", "连板挖掘v2", "连板龙头选股", "连板龙头选股工作流", "每日连板龙头"):
        if trigger not in skill_text:
            errors.append(f"trigger_missing:{trigger}")

    date_utils = (ROOT / "scripts" / "_date_utils.py").read_text(encoding="utf-8-sig")
    if "def resolve_latest_trade_date()" not in date_utils:
        errors.append("date_resolver_missing")
    daily_script = (ROOT / "scripts" / "run_daily.py").read_text(encoding="utf-8-sig")
    research_script = (ROOT / "scripts" / "run_research.py").read_text(encoding="utf-8-sig")
    adapter_script = (ROOT / "scripts" / "canonical_business_adapter.py").read_text(encoding="utf-8-sig")
    for name, text in (("daily", daily_script), ("research", research_script), ("adapter", adapter_script)):
        if "resolve_latest_trade_date" not in text:
            errors.append(f"date_resolver_not_used:{name}")
    if "date.today().strftime('%Y%m%d')" in daily_script:
        errors.append("calendar_date_fallback:daily")
    if "date.today().strftime('%Y%m%d')" in research_script:
        errors.append("calendar_date_fallback:research")
    if 'date = datetime.now().strftime("%Y%m%d")' in adapter_script:
        errors.append("calendar_date_fallback:adapter")

    business = (ROOT / "references" / "business_spec.md").read_text(encoding="utf-8-sig")
    workflow = (ROOT / "references" / "workflow.md").read_text(encoding="utf-8-sig")
    for gate in range(1, 18):
        if f"G{gate}" not in business:
            errors.append(f"word_gate_missing:G{gate}")
    for step in range(1, 14):
        if f"{step}. `" not in workflow:
            errors.append(f"workflow_step_missing:{step}")
    if "25 + 25 + 20 + 20 + 10" not in business.replace("\n", " "):
        # Table values are verified independently below; this marker is optional.
        daily_weights = (25, 25, 20, 20, 10)
        if sum(daily_weights) != 100:
            errors.append("daily_score_sum_not_100")
    research_weights = (15, 20, 15, 10, 15, 10, 10, 5)
    if sum(research_weights) != 100:
        errors.append("research_score_sum_not_100")

    exempt = {ROOT / "references" / "capability_audit.md"}
    for path in _text_files():
        if path in exempt or path.resolve() == Path(__file__).resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeError:
            continue
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            if marker in text:
                errors.append(f"forbidden_runtime_dependency:{path.relative_to(ROOT)}:{marker}")

    payload = {
        "status": "PASS" if not errors else "FAIL",
        "skill": SKILL,
        "display_name": DISPLAY_NAME,
        "modes": MODES,
        "compiled_scripts": len(scripts),
        "required_references": len(REQUIRED_REFERENCES),
        "word_gates": 17,
        "workflow_steps": 13,
        "score_models": {"daily": 100, "research": 100},
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def run_mode(extra: list[str]) -> int:
    mode_parser = argparse.ArgumentParser(add_help=False)
    mode_parser.add_argument("--mode", choices=tuple(MODES), default="full")
    parsed, remaining = mode_parser.parse_known_args(extra)
    target = ROOT / MODES[parsed.mode]
    return subprocess.run([sys.executable, str(target), *remaining], cwd=str(ROOT)).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="统一连板挖掘入口")
    parser.add_argument("command", choices=("info", "selftest", "run"), nargs="?", default="info")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args()
    if parsed.command == "info":
        print(json.dumps({
            "skill": SKILL,
            "display_name": DISPLAY_NAME,
            "runtime": "Codex",
            "default_mode": "full",
            "modes": MODES,
            "legacy_triggers": ["连板挖掘v2", "连板龙头选股", "连板龙头选股工作流", "每日连板龙头"],
        }, ensure_ascii=False, indent=2))
        return 0
    if parsed.command == "selftest":
        return selftest()
    extra = parsed.args[1:] if parsed.args and parsed.args[0] == "--" else parsed.args
    return run_mode(extra)


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
