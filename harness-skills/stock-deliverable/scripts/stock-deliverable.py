#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"
SUPPORTED = {".docx", ".pdf", ".pptx", ".xlsx", ".xlsm", ".xls", ".png", ".jpg", ".jpeg", ".mp4"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capability_check() -> tuple[dict, int]:
    required = (
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "references" / "workflow.md",
        SCRIPTS / "codex_entry.py",
        SCRIPTS / "canonical_business_adapter.py",
        SCRIPTS / "legacy_codex_entry.py",
    )
    errors = [f"missing:{path}" for path in required if not path.is_file()]
    payload = {
        "skill": SKILL_DIR.name,
        "mode": "capability-validation",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "supported_extensions": sorted(SUPPORTED),
        "validated_files": [
            {
                "role": path.relative_to(SKILL_DIR).as_posix(),
                "relative_path": path.relative_to(SKILL_DIR).as_posix(),
                "exists": True,
                "contract_binding_required": True,
            }
            for path in required
            if path.is_file()
        ],
        "errors": errors,
    }
    return payload, 0 if not errors else 2


def cmd_info(_: argparse.Namespace) -> int:
    payload, _ = capability_check()
    payload["entry"] = str(Path(__file__).resolve())
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_selftest(_: argparse.Namespace) -> int:
    payload, returncode = capability_check()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return returncode


def cmd_auto(_: argparse.Namespace) -> int:
    return cmd_selftest(argparse.Namespace())


def cmd_run(args: argparse.Namespace) -> int:
    path = Path(args.file).resolve()
    errors = []
    if not path.is_file():
        errors.append(f"artifact_missing:{path}")
    elif path.suffix.casefold() not in SUPPORTED:
        errors.append(f"unsupported_artifact_type:{path.suffix}")
    elif path.stat().st_size <= 0:
        errors.append("artifact_empty")
    payload = {
        "skill": SKILL_DIR.name,
        "mode": "artifact-validation",
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "artifact": str(path),
        "bytes": path.stat().st_size if path.is_file() else 0,
        "sha256": sha256_file(path) if path.is_file() else None,
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="stock-deliverable Codex locked entry")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("info")
    sub.add_parser("selftest")
    sub.add_parser("auto")
    run_p = sub.add_parser("run")
    run_p.add_argument("--file", required=True)
    return parser


def main() -> int:
    parser = build_parser()
    if len(sys.argv) == 1:
        return cmd_auto(argparse.Namespace())
    args = parser.parse_args()
    if args.cmd == "info":
        return cmd_info(args)
    if args.cmd == "selftest":
        return cmd_selftest(args)
    if args.cmd == "auto":
        return cmd_auto(args)
    if args.cmd == "run":
        return cmd_run(args)
    parser.print_help()
    return 0


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
