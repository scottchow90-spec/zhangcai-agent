from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import subprocess
import sys
from pathlib import Path

SKILL = "stock-unified"
ROOT = Path(__file__).resolve().parents[1]
CODEX_ROOT = Path.home() / ".codex"


def run(command: list[str]) -> dict:
    p = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return {"command": command, "returncode": p.returncode, "stdout": p.stdout[-5000:], "stderr": p.stderr[-3000:]}


def main() -> int:
    commands = [
        [sys.executable, str(CODEX_ROOT / "hooks" / "skill_workflow_lock.py"), "check", "--skill", SKILL],
        [sys.executable, str(CODEX_ROOT / "hooks" / "stock_workflow_substantive_gate.py"), "check", "--skill", SKILL],
        [sys.executable, str(ROOT / "scripts" / "codex_entry.py"), "selftest"],
    ]
    steps = [run(command) for command in commands]
    ok = all(step["returncode"] == 0 for step in steps)
    payload = {
        "status": "CLEAN_PASS" if ok else "BLOCKED",
        "target_system": "Codex Desktop",
        "skill": SKILL,
        "canonical_entry": str(ROOT / "scripts" / "codex_entry.py"),
        "steps": steps,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
