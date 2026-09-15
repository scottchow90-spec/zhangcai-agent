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
import shutil
from datetime import datetime
from pathlib import Path

ARCHIVE_ROOT = Path.home() / ".codex" / "reports" / "_archive" / "lianban_mining"
ALLOWED_FILES = (
    "candidate_pool.csv", "dragon_score.csv", "report.md", "audit_log.md",
    "run_manifest.json", "source_failure.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="归档连板挖掘原始预测快照")
    parser.add_argument("--from-manifest", required=True)
    args = parser.parse_args()
    source_manifest = Path(args.from_manifest).expanduser().resolve()
    if not source_manifest.is_file():
        raise SystemExit(f"manifest not found: {source_manifest}")
    manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
    required = ("trade_date", "workflow", "run_id", "evidence_dir", "operator")
    missing = [key for key in required if not manifest.get(key)]
    if missing:
        raise SystemExit(f"manifest missing fields: {missing}")
    evidence_dir = Path(manifest["evidence_dir"]).expanduser().resolve()
    if not evidence_dir.is_dir():
        raise SystemExit(f"evidence_dir not found: {evidence_dir}")
    date_key = str(manifest["trade_date"]).replace("-", "")
    run_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(manifest["run_id"]))
    destination = ARCHIVE_ROOT / date_key / run_id
    destination.mkdir(parents=True, exist_ok=True)
    files = []
    for name in ALLOWED_FILES:
        source = evidence_dir / name
        if not source.is_file():
            continue
        target = destination / name
        shutil.copy2(source, target)
        files.append({"name": name, "bytes": target.stat().st_size, "sha256": sha256(target)})
    receipt = {
        "status": "PASS",
        "archived_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_manifest": str(source_manifest),
        "archive_dir": str(destination),
        "manifest": manifest,
        "files": files,
    }
    receipt_path = destination / "archive_manifest.json"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "archive_manifest": str(receipt_path), "files": len(files)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
