#!/usr/bin/env python3
"""Synchronize stock execution contract hashes with their bound files."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import os
from pathlib import Path
from typing import Any

from stock_contract_catalog import (
    load_contract_inputs,
    synchronize_contract_payload,
)


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
CATALOG = ROOT / "references" / "stock_skill_ids.json"
CONTRACTS = ROOT / "references" / "stock_execution_contracts.json"
RUNTIME = ROOT.parent.parent / "scripts" / "stock_canonical_runtime.py"


def load_inputs() -> tuple[dict[str, Any], list[str]]:
    return load_contract_inputs(
        catalog_path=CATALOG,
        contracts_path=CONTRACTS,
    )


def synchronize(payload: dict[str, Any], skills: list[str]) -> list[dict[str, str]]:
    return synchronize_contract_payload(
        payload,
        skills,
        skills_root=SKILLS_ROOT,
        runtime_path=RUNTIME,
    )


def write_payload(payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temporary = CONTRACTS.with_suffix(CONTRACTS.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    readback = json.loads(temporary.read_text(encoding="utf-8"))
    readback_changes = synchronize(
        readback,
        json.loads(CATALOG.read_text(encoding="utf-8"))["skills"],
    )
    if readback_changes:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("contract_sync_readback_mismatch")
    os.replace(temporary, CONTRACTS)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check or synchronize stock execution contract hashes."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()

    payload, skills = load_inputs()
    changes = synchronize(payload, skills)
    if args.write and changes:
        write_payload(payload)

    result = {
        "schema": "STOCK_EXECUTION_CONTRACT_SYNC_V1",
        "status": "CLEAN_PASS" if args.write or not changes else "BLOCKED",
        "mode": "write" if args.write else "check",
        "contract_count": len(skills),
        "changed_field_count": len(changes),
        "changed_skill_count": len({row["skill_id"] for row in changes}),
        "contracts": str(CONTRACTS),
        "changes": changes,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
