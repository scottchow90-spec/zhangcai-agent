#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import os

from entry_limit_up_review import evaluate_date_gate


def main() -> int:
    if os.environ.get("CODEX_STOCK_CANONICAL_EXECUTION") != "1":
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "target_date": "",
                    "errors": ["canonical_execution_environment_missing"],
                }
            )
        )
        return 2
    try:
        gate = evaluate_date_gate("", "latest")
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "target_date": "",
                    "errors": [f"target_date_resolution_failed:{type(exc).__name__}:{exc}"],
                }
            )
        )
        return 2
    clean = gate.get("status") == "CLEAN_PASS" and bool(gate.get("target_date"))
    print(
        json.dumps(
            {
                "status": "CLEAN_PASS" if clean else "BLOCKED",
                "target_date": str(gate.get("target_date") or ""),
                "date_gate": gate,
                "errors": list(gate.get("blocks") or []),
            },
            ensure_ascii=False,
        )
    )
    return 0 if clean else 2


if __name__ == "__main__":
    raise SystemExit(main())
