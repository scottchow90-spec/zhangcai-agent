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
import re
from pathlib import Path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a persisted intraday position-monitor result")
    parser.add_argument("--result", required=True)
    parser.add_argument("--validation", required=True)
    args = parser.parse_args()
    result_path = Path(args.result).resolve()
    validation_path = Path(args.validation).resolve()
    result = json.loads(result_path.read_text(encoding="utf-8"))
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    position = result["position"]
    checks = {
        "result_status": result.get("status") == "PASS",
        "validation_status": validation.get("status") == "PASS",
        "symbol_shape": re.fullmatch(r"\d{6}\.(SH|SZ)", str(result.get("symbol", ""))) is not None,
        "cost_basis_formula": position["cost_basis"] == round(position["cost"] * position["shares"], 2),
        "market_value_formula": position["market_value"] == round(position["last_price"] * position["shares"], 2),
        "pnl_formula": position["unrealized_pnl"] == round((position["last_price"] - position["cost"]) * position["shares"], 2),
        "downside_descending": [row["price"] for row in result["downside_alerts"]] == sorted((row["price"] for row in result["downside_alerts"]), reverse=True),
        "upside_ascending": [row["price"] for row in result["upside_observations"]] == sorted(row["price"] for row in result["upside_observations"]),
        "result_hash_bound": validation.get("result_sha256") == file_sha256(result_path),
        "result_size_bound": validation.get("result_size") == result_path.stat().st_size,
        "stock_skill_attestation_pass": validation.get("stock_skill_attestation", {}).get("status") == "PASS",
        "no_auto_order": result["monitor_contract"]["no_auto_order"] is True,
        "daemon_boundary": result["boundaries"]["continuous_realtime_daemon"] == "not verified",
    }
    status = "CLEAN_PASS" if all(checks.values()) else "BLOCKED"
    print(
        json.dumps(
            {
                "status": status,
                "skill": result.get("skill"),
                "symbol": result.get("symbol"),
                "last_price": position.get("last_price"),
                "unrealized_pnl": position.get("unrealized_pnl"),
                "downside_alerts": [row["price"] for row in result["downside_alerts"]],
                "upside_observations": [row["price"] for row in result["upside_observations"]],
                "checks": checks,
            },
            ensure_ascii=False,
        )
    )
    return 0 if status == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
