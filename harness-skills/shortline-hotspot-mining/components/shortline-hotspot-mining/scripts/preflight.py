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
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = Path.home() / ".codex" / "reports"
TDX_BLOCK_CANDIDATES = (
    Path(r"C:\new_tdx_mock\T0002\blocknew"),
    Path(r"C:\new_tdx\T0002\blocknew"),
    Path(r"C:\zd_tdx\T0002\blocknew"),
)
REQUIRED = (
    ROOT / "SKILL.md",
    ROOT / "references" / "business_spec.md",
    ROOT / "references" / "workflow.md",
    ROOT / "references" / "scoring_and_evidence.md",
    ROOT / "scripts" / "run.py",
    ROOT / "scripts" / "tdx_sector_pct.py",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="短线热点挖掘运行前检查")
    parser.add_argument("--strict", action="store_true", help="将可选数据源警告也视为失败")
    args = parser.parse_args()
    checks: list[dict] = []

    for path in REQUIRED:
        ok = path.is_file() and path.stat().st_size > 0
        checks.append({"name": f"required:{path.relative_to(ROOT)}", "status": "PASS" if ok else "FAIL", "path": str(path)})

    tdx = next((p for p in TDX_BLOCK_CANDIDATES if p.is_dir()), None)
    checks.append({
        "name": "tdx_block_pool",
        "status": "PASS" if tdx else "FAIL",
        "path": str(tdx) if tdx else None,
        "attempted": [str(p) for p in TDX_BLOCK_CANDIDATES],
    })

    try:
        import akshare  # noqa: F401
        ak_status, ak_detail = "PASS", "importable"
    except Exception as exc:
        ak_status, ak_detail = "WARN", f"{type(exc).__name__}: {exc}"
    checks.append({"name": "akshare_optional", "status": ak_status, "detail": ak_detail})

    try:
        REPORTS.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="shortline-hotspot-", dir=REPORTS, delete=True) as handle:
            handle.write(b"ok")
            handle.flush()
        checks.append({"name": "reports_writable", "status": "PASS", "path": str(REPORTS)})
    except Exception as exc:
        checks.append({"name": "reports_writable", "status": "FAIL", "path": str(REPORTS), "detail": str(exc)})

    failures = [c for c in checks if c["status"] == "FAIL"]
    warnings = [c for c in checks if c["status"] == "WARN"]
    ok = not failures and (not args.strict or not warnings)
    payload = {
        "status": "PASS" if ok else "FAIL",
        "skill": ROOT.name,
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "strict": args.strict,
        "checks": checks,
        "failure_count": len(failures),
        "warning_count": len(warnings),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

