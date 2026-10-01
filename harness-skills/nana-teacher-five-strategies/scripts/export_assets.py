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


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "references" / "asset_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the fixed 5+5+5 Nana strategy asset package.")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd() / "outputs" / "娜娜老师5策略")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()) and not args.force:
        print(json.dumps({"status": "BLOCKED", "reason": "output directory is not empty; pass --force to overwrite only managed files", "path": str(output_dir)}, ensure_ascii=False))
        return 2
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    copied = []
    category_counts = {"formula": 0, "workflow": 0, "evidence": 0, "index": 0}
    failures = []
    for item in manifest.get("items", []):
        source = ROOT / str(item["path"])
        destination = output_dir / source.name
        shutil.copy2(source, destination)
        actual_hash = sha256(destination)
        actual_size = destination.stat().st_size
        ok = actual_hash == item["sha256"] and actual_size == item["size_bytes"]
        if not ok:
            failures.append(source.name)
        category = str(item["category"])
        category_counts[category] = category_counts.get(category, 0) + 1
        copied.append({"path": str(destination), "category": category, "sha256": actual_hash, "size_bytes": actual_size, "hash_match": ok})
    expected_counts = {"formula": 5, "workflow": 5, "evidence": 5, "index": 1}
    status = "PASS" if not failures and category_counts == expected_counts else "FAIL"
    receipt_path = output_dir / "nana_teacher_five_strategy_export_receipt.json"
    receipt = {
        "schema_version": 1,
        "kind": "NANA_TEACHER_FIVE_STRATEGY_EXPORT_V1",
        "status": status,
        "skill": "nana-teacher-five-strategies",
        "display_name": "娜娜老师5策略",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "output_dir": str(output_dir),
        "counts": category_counts,
        "items": copied,
        "failures": failures,
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": status, "output_dir": str(output_dir), "counts": category_counts, "receipt": str(receipt_path), "failures": failures}, ensure_ascii=False))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
