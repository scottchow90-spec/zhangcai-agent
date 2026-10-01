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
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

WORKSPACE = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
REFERENCES_DIR = SKILL_DIR / "references"
ASSETS_DIR = SKILL_DIR / "assets" / "formulas"
REGISTRY_JSON = REFERENCES_DIR / "formulas.json"
PYTHON_EXE = sys.executable
SKILL_NAME_DISPLAY = "白猫老师体系"
ENTRY_SCRIPT_NAME = "baimao-teacher-system.py"
ACCEPTANCE_SCRIPT = SCRIPTS_DIR / "baimao_workflow_acceptance.py"


def _strip_installation_fingerprints(value: Any, in_evidence: bool = False) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if in_evidence and key in {"size", "sha256"}:
                continue
            cleaned[key] = _strip_installation_fingerprints(
                item,
                in_evidence=in_evidence or key == "evidence",
            )
        return cleaned
    if isinstance(value, list):
        return [
            _strip_installation_fingerprints(item, in_evidence=in_evidence)
            for item in value
        ]
    return value


def _normalize_runtime_home_paths(value: Any, runtime_home: Path) -> Any:
    if isinstance(value, dict):
        return {
            key: _normalize_runtime_home_paths(item, runtime_home)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_runtime_home_paths(item, runtime_home) for item in value]
    if not isinstance(value, str):
        return value

    windows_home = str(runtime_home).replace("/", "\\").rstrip("\\")
    forward_home = windows_home.replace("\\", "/")
    variants = {windows_home, forward_home}
    variants.update(
        json.dumps(item, ensure_ascii=False)[1:-1] for item in tuple(variants)
    )
    normalized = value
    for variant in sorted(variants, key=len, reverse=True):
        normalized = re.sub(re.escape(variant), "<HOME>", normalized, flags=re.IGNORECASE)
    return normalized


def portable_business_capture(captured: dict[str, Any]) -> dict[str, Any]:
    result = dict(captured)
    stdout = str(result.get("stdout", ""))
    try:
        payload = json.loads(stdout)
    except (TypeError, json.JSONDecodeError):
        return result
    portable_payload = _normalize_runtime_home_paths(
        _strip_installation_fingerprints(payload),
        SKILL_DIR.parents[1],
    )
    result["stdout"] = json.dumps(
        portable_payload,
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    result["stdout_tail"] = result["stdout"][-1800:]
    return result


def run_capture(cmd: list[str], timeout: int = 120, cwd: Path | None = None) -> dict[str, Any]:
    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd or SKILL_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
        )
        return portable_business_capture({
            "ok": r.returncode == 0,
            "exit": r.returncode,
            "cmd": cmd,
            "stdout": r.stdout,
            "stderr": r.stderr,
            "stdout_tail": r.stdout[-1800:],
            "stderr_tail": r.stderr[-900:],
        })
    except Exception as exc:
        return {"ok": False, "cmd": cmd, "error": f"{type(exc).__name__}: {exc}"}


def load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_JSON.read_text(encoding="utf-8-sig"))


def parse_tdx_priloc(path: Path) -> list[str]:
    data = path.read_bytes()
    names: list[str] = []
    if len(data) <= 24:
        return names
    for offset in range(24, len(data), 56):
        rec = data[offset : offset + 56]
        if len(rec) < 20:
            continue
        raw = rec[:20].split(b"\x00", 1)[0]
        if not raw:
            continue
        name = raw.decode("gbk", errors="ignore").strip()
        if name:
            names.append(name)
    return names


def build_status() -> dict[str, Any]:
    registry = load_registry()
    tdx_root = Path(registry["tdx_root"])
    t0002 = tdx_root / "T0002"
    priloc = t0002 / "PriLoc.dat"
    installed = parse_tdx_priloc(priloc) if priloc.exists() else []
    formulas = registry.get("formulas", [])
    assets: list[dict[str, Any]] = []
    found: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    tdx_install_missing: list[dict[str, str]] = []
    for item in formulas:
        asset_path = SKILL_DIR / item["asset"]
        assets.append({
            "name": item["name"],
            "kind": item["kind"],
            "asset": str(asset_path),
            "exists": asset_path.exists(),
            "size": asset_path.stat().st_size if asset_path.exists() else 0,
        })
        row = {
            "name": item["name"],
            "kind": item["kind"],
            "installed_name": item["installed_name"],
        }
        asset_ok = asset_path.exists() and asset_path.stat().st_size > 0
        if asset_ok:
            found.append({**row, "asset": str(asset_path), "install_state": "asset_locked"})
        else:
            missing.append({**row, "asset": str(asset_path), "reason": "asset_missing"})
        if item["installed_name"] not in installed:
            tdx_install_missing.append(row)
    asset_missing = [a for a in assets if not a["exists"] or int(a["size"]) <= 0]
    ok = tdx_root.exists() and t0002.exists() and not missing and not asset_missing
    return {
        "skill": SKILL_DIR.name,
        "display_name": SKILL_NAME_DISPLAY,
        "tdx_root": str(tdx_root),
        "t0002": str(t0002),
        "priloc": str(priloc),
        "backup_dir": registry.get("backup_dir"),
        "expected_count": len(formulas),
        "registry_formula_count": len(installed),
        "tdx_installed_count": len(installed),
        "tdx_installed_names": installed,
        "tdx_install_missing": tdx_install_missing,
        "execution_formula_mode": "asset_locked_python_engine",
        "found": found,
        "missing": missing,
        "assets": assets,
        "asset_missing": asset_missing,
        "source_files": [{"name": f["name"], "source_file": f["source_file"]} for f in formulas],
        "status": "CLEAN_PASS" if ok else "BLOCKED",
    }


def cmd_info(_: argparse.Namespace) -> int:
    registry = load_registry()
    print(json.dumps({
        "skill": SKILL_DIR.name,
        "display_name": SKILL_NAME_DISPLAY,
        "skill_dir": str(SKILL_DIR),
        "entry": str(Path(__file__).resolve()),
        "acceptance_workflow": str(ACCEPTANCE_SCRIPT),
        "workflow": str(SKILL_DIR / "references" / "workflow.md"),
        "registry": str(REGISTRY_JSON),
        "tdx_root": registry.get("tdx_root"),
        "formula_count": len(registry.get("formulas", [])),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    registry = load_registry()
    print(json.dumps({
        "skill": SKILL_DIR.name,
        "formulas": registry.get("formulas", []),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    payload = build_status()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "CLEAN_PASS" else 1


def cmd_verify_installed(_: argparse.Namespace) -> int:
    payload = build_status()
    print(json.dumps({
        "skill": SKILL_DIR.name,
        "mode": "verify-executable-formulas",
        "tdx_root": payload["tdx_root"],
        "expected_count": payload["expected_count"],
        "found_count": len(payload["found"]),
        "missing": payload["missing"],
        "execution_formula_mode": payload["execution_formula_mode"],
        "tdx_installed_count": payload["tdx_installed_count"],
        "tdx_install_missing": payload["tdx_install_missing"],
        "asset_missing": payload["asset_missing"],
        "status": payload["status"],
    }, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "CLEAN_PASS" else 1


def cmd_run(args: argparse.Namespace) -> int:
    script = args.script
    if not script.endswith(".py"):
        script += ".py"
    target = SCRIPTS_DIR / script
    if not target.exists():
        print(f"run: script not found: {target}", file=sys.stderr)
        return 2
    return subprocess.run([PYTHON_EXE, str(target)] + (args.args or []), cwd=str(SKILL_DIR)).returncode


def cmd_score(args: argparse.Namespace) -> int:
    return subprocess.run(
        [PYTHON_EXE, str(SCRIPTS_DIR / "baimao_stock_score.py"), "score", args.symbol, "--limit", str(args.limit)],
        cwd=str(SKILL_DIR),
    ).returncode


def cmd_report(args: argparse.Namespace) -> int:
    return subprocess.run(
        [PYTHON_EXE, str(SCRIPTS_DIR / "baimao_stock_score.py"), "report", args.symbol, "--limit", str(args.limit)],
        cwd=str(SKILL_DIR),
    ).returncode


def cmd_batch(args: argparse.Namespace) -> int:
    cmd = [PYTHON_EXE, str(SCRIPTS_DIR / "baimao_stock_score.py"), "batch", "--limit", str(args.limit)]
    if args.file:
        cmd.extend(["--file", args.file])
    cmd.extend(args.symbols or [])
    return subprocess.run(cmd, cwd=str(SKILL_DIR)).returncode


def cmd_selftest(_: argparse.Namespace) -> int:
    steps: list[dict[str, Any]] = []
    status = build_status()
    steps.append({
        "step": "verify_installed",
        "ok": status["status"] == "CLEAN_PASS",
        "summary": {
            "expected_count": status["expected_count"],
            "found_count": len(status["found"]),
            "missing": status["missing"],
            "asset_missing": status["asset_missing"],
            "tdx_root": status["tdx_root"],
        },
    })
    steps.append({
        "step": "acceptance_workflow_present",
        "ok": ACCEPTANCE_SCRIPT.is_file(),
        "path": str(ACCEPTANCE_SCRIPT),
    })
    ok = all(s.get("ok") for s in steps)
    print(json.dumps({
        "skill": SKILL_DIR.name,
        "mode": "selftest",
        "status": "CLEAN_PASS" if ok else "BLOCKED",
        "steps": steps,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1



def infer_auto_status(ok, steps):
    if ok:
        return "CLEAN_PASS"
    text = json.dumps(steps, ensure_ascii=False)
    blocked_markers = ("BLOCKED", "BLOCKED_BY_", "DATA_STALE", "DATA_BLOCKED", "AUDIT_BLOCKED", "TIMEOUT")
    return "BLOCKED" if any(marker in text for marker in blocked_markers) else "FAILED"

def cmd_auto(_: argparse.Namespace | None) -> int:
    steps: list[dict[str, Any]] = []
    selftest = run_capture([PYTHON_EXE, str(Path(__file__).resolve()), "selftest"], timeout=240)
    selftest["step"] = "selftest"
    stdout = selftest.get("stdout", "") or selftest.get("stdout_tail", "")
    selftest["ok"] = selftest.get("ok") and ('"status": "CLEAN_PASS"' in stdout or '"all_ok": true' in stdout)
    steps.append(selftest)

    target = ACCEPTANCE_SCRIPT
    if not target.exists():
        steps.append({"step": "acceptance_workflow", "ok": False, "error": f"missing {target}"})
    else:
        r = run_capture([PYTHON_EXE, str(target)], timeout=480)
        r["step"] = "acceptance_workflow"
        r["script"] = target.name
        steps.append(r)

    ok = all(s.get("ok") for s in steps)
    print(json.dumps({
        "skill": SKILL_DIR.name,
        "mode": "auto",
        "entry_script": str(Path(__file__).resolve()),
        "acceptance_workflow": str(target),
        "executed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": infer_auto_status(ok, steps),
        "all_ok": ok,
        "steps": steps,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{SKILL_NAME_DISPLAY} Codex unique execution entry")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("info")
    sub.add_parser("list")
    sub.add_parser("status")
    sub.add_parser("verify-installed")
    score_p = sub.add_parser("score")
    score_p.add_argument("symbol")
    score_p.add_argument("--limit", type=int, default=260)
    report_p = sub.add_parser("report")
    report_p.add_argument("symbol")
    report_p.add_argument("--limit", type=int, default=260)
    batch_p = sub.add_parser("batch")
    batch_p.add_argument("symbols", nargs="*")
    batch_p.add_argument("--file", default="")
    batch_p.add_argument("--limit", type=int, default=260)
    sub.add_parser("selftest")
    sub.add_parser("auto")
    run_p = sub.add_parser("run")
    run_p.add_argument("script")
    run_p.add_argument("args", nargs=argparse.REMAINDER)
    return parser


def main() -> int:
    parser = build_parser()
    if len(sys.argv) == 1:
        return cmd_auto(None)
    args = parser.parse_args()
    if args.cmd == "info":
        return cmd_info(args)
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "verify-installed":
        return cmd_verify_installed(args)
    if args.cmd == "score":
        return cmd_score(args)
    if args.cmd == "report":
        return cmd_report(args)
    if args.cmd == "batch":
        return cmd_batch(args)
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
