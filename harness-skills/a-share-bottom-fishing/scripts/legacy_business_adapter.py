#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ENTRY = SCRIPTS / "抄底策略.py"
VALIDATOR = SCRIPTS / "validate_bottom_fishing_delivery.py"


def load_entry():
    spec = importlib.util.spec_from_file_location("bottom_fishing_legacy_entry", ENTRY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {ENTRY}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_entry()
    generated = module.generate_bottom_fishing_task()
    if not generated.get("ok"):
        print(json.dumps({"status": "BLOCKED", "stage": "generate", "generated": generated}, ensure_ascii=False, indent=2))
        return 1
    task_dir = Path(str(generated["task_dir"]))
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR), "--task-dir", str(task_dir)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    payload = {
        "status": "CLEAN_PASS" if completed.returncode == 0 else "BLOCKED",
        "stage": "generate_and_validate",
        "generated": generated,
        "validator_returncode": completed.returncode,
        "validator_stdout": completed.stdout,
        "validator_stderr": completed.stderr,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if completed.returncode == 0 else 1


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
