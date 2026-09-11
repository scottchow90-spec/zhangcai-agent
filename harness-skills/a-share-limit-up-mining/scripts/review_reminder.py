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
from datetime import date, datetime
from pathlib import Path

ARCHIVE_ROOT = Path.home() / ".codex" / "reports" / "_archive" / "lianban_mining"


def main() -> int:
    parser = argparse.ArgumentParser(description="检查显式写入的连板挖掘复评到期日；不创建自动任务")
    parser.add_argument("action", choices=("check",), nargs="?", default="check")
    parser.add_argument("--as-of", default=date.today().isoformat())
    args = parser.parse_args()
    as_of = date.fromisoformat(args.as_of)
    due, pending, unresolved = [], [], []
    paths = ARCHIVE_ROOT.glob("*/*/archive_manifest.json") if ARCHIVE_ROOT.exists() else []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        manifest = payload.get("manifest", {})
        due_text = manifest.get("review_due_date")
        item = {"archive_manifest": str(path), "trade_date": manifest.get("trade_date"), "review_due_date": due_text}
        if not due_text:
            item["reason"] = "未提供交易所日历计算出的 review_due_date；禁止用自然日猜测 T+3"
            unresolved.append(item)
            continue
        due_date = date.fromisoformat(due_text)
        (due if due_date <= as_of else pending).append(item)
    result = {
        "status": "PASS",
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "as_of": as_of.isoformat(),
        "due": due,
        "pending": pending,
        "unresolved": unresolved,
        "automation_created": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
