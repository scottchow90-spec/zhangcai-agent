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
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_CREATOR = Path.home() / ".codex" / "skills" / ".system" / "skill-creator" / "scripts"
QUICK_VALIDATE = SKILL_CREATOR / "quick_validate.py"
ENTRY = ROOT / "scripts" / "codex_entry.py"
RESULT_VERIFIER = ROOT / "scripts" / "verify_result.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes())
    return digest.hexdigest()


def run(argv: list[str]) -> dict:
    completed = subprocess.run(
        argv,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-1000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the installed A-share intraday position-monitor skill")
    parser.add_argument("--forward-result", required=True)
    parser.add_argument("--forward-validation", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result_path = Path(args.forward_result).resolve()
    validation_path = Path(args.forward_validation).resolve()
    output_path = Path(args.output).resolve()
    expected_files = [
        ROOT / "SKILL.md",
        ROOT / "agents" / "openai.yaml",
        ROOT / "references" / "methodology.md",
        ROOT / "scripts" / "codex_entry.py",
        ROOT / "scripts" / "monitor_workflow.py",
        ROOT / "scripts" / "attest_stock_execution.py",
        ROOT / "scripts" / "verify_result.py",
        ROOT / "scripts" / "verify_installation.py",
    ]
    inventory = []
    for path in expected_files:
        if path.is_file():
            inventory.append({"path": str(path), "size": path.stat().st_size, "sha256": sha256(path)})
    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    agent_text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    quick = run([sys.executable, str(QUICK_VALIDATE), str(ROOT)])
    info = run([sys.executable, str(ENTRY), "info"])
    selftest = run([sys.executable, str(ENTRY), "selftest"])
    forward = run(
        [
            sys.executable,
            str(RESULT_VERIFIER),
            "--result",
            str(result_path),
            "--validation",
            str(validation_path),
        ]
    )
    checks = {
        "all_expected_files_present": len(inventory) == len(expected_files),
        "no_todo_placeholders": "TODO" not in skill_text,
        "frontmatter_name_present": "name: a-share-intraday-position-monitor" in skill_text,
        "display_heading_present": "# 持仓股监控技能" in skill_text,
        "trigger_present": "$a-share-intraday-position-monitor" in skill_text,
        "ui_display_name_present": 'display_name: "持仓股监控技能"' in agent_text,
        "ui_prompt_present": "$a-share-intraday-position-monitor" in agent_text,
        "quick_validate_pass": quick["returncode"] == 0 and "Skill is valid" in quick["stdout"],
        "entry_info_display_name_pass": info["returncode"] == 0 and '"display_name": "持仓股监控技能"' in info["stdout"],
        "entry_selftest_pass": selftest["returncode"] == 0 and '"status": "CLEAN_PASS"' in selftest["stdout"],
        "forward_result_pass": forward["returncode"] == 0 and '"status": "CLEAN_PASS"' in forward["stdout"],
        "forward_stock_attestation_pass": (
            validation_path.is_file()
            and json.loads(validation_path.read_text(encoding="utf-8-sig"))
            .get("stock_skill_attestation", {})
            .get("status") == "PASS"
        ),
    }
    record = {
        "status": "CLEAN_PASS" if all(checks.values()) else "BLOCKED",
        "skill": "a-share-intraday-position-monitor",
        "skill_root": str(ROOT),
        "checks": checks,
        "inventory": inventory,
        "quick_validate": quick,
        "entry_info": info,
        "entry_selftest": selftest,
        "forward_result": forward,
        "forward_result_path": str(result_path),
        "forward_validation_path": str(validation_path),
        "runtime_boundaries": {
            "continuous_realtime_daemon": "not verified",
            "windows_popup_delivery": "not verified",
            "broker_account_link": "not verified",
            "automatic_ordering": False,
            "current_task_ui_skill_refresh": "not verified",
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": record["status"], "output": str(output_path), "checks": checks}, ensure_ascii=False))
    return 0 if record["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
