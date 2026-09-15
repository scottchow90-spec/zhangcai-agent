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
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def validate_delivery_capability() -> tuple[dict, int]:
    required = (
        ROOT / "SKILL.md",
        ROOT / "references" / "workflow.md",
        ROOT / "scripts" / "codex_entry.py",
        ROOT / "scripts" / "verify_a_share_sentiment_delivery.ps1",
    )
    missing = [str(path) for path in required if not path.is_file()]
    verifier = required[-1]
    errors = [f"missing:{path}" for path in missing]
    if verifier.is_file():
        text = verifier.read_text(encoding="utf-8-sig")
        for marker in ("DocxPath", "ExportAsFixedFormat", "scan-docx"):
            if marker not in text:
                errors.append(f"verifier_contract_missing:{marker}")
    payload = {
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "skill": ROOT.name,
        "capability": "receipt_bound_sentiment_word_delivery_validation",
        "required_input": "docx_path",
        "validated_files": [
            {
                "role": path.relative_to(ROOT).as_posix(),
                "relative_path": path.relative_to(ROOT).as_posix(),
                "exists": True,
                "contract_binding_required": True,
            }
            for path in required
            if path.is_file()
        ],
        "errors": errors,
    }
    return payload, 0 if not errors else 2


def main() -> int:
    if os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
        print("canonical_stock_legacy_entry_direct_execution_blocked", file=sys.stderr)
        return 2
    command = sys.argv[1] if len(sys.argv) > 1 else "run"
    if command not in {"info", "selftest", "run"}:
        print(json.dumps({"status": "BLOCKED", "error": f"unsupported_command:{command}"}, ensure_ascii=False))
        return 2
    payload, returncode = validate_delivery_capability()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
