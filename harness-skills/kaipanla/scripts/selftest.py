#!/usr/bin/env python
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "kaipanla.py"


def reports_root() -> Path:
    execution_root = os.environ.get("CODEX_STOCK_BUSINESS_RUN_DIR", "").strip()
    if execution_root:
        return Path(execution_root).resolve() / "reports"
    data_root = os.environ.get("ONESTOCK_STOCK_DATA_ROOT", "").strip()
    if data_root:
        return Path(data_root).resolve() / "reports"
    return ROOT.parents[1] / "reports"


REPORT = reports_root() / "kaipanla_openclaw_integration"


def main():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "probe"],
        text=True,
        capture_output=True,
        timeout=30,
    )
    payload = json.loads(result.stdout) if result.stdout.strip() else {}
    checks = {
        "skill_md_exists": (ROOT / "SKILL.md").is_file(),
        "script_exists": SCRIPT.is_file(),
        "probe_exit_zero": result.returncode == 0,
        "probe_status_pass": payload.get("status") == "PASS",
        "latest_probe_exists": (REPORT / "latest_probe.json").is_file(),
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    output = {
        "status": status,
        "checks": checks,
        "probe": payload,
        "stderr": result.stderr,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
