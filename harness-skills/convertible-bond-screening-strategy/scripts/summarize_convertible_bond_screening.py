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
from pathlib import Path

from runtime_utils import atomic_write_json, canonicalize_business_payload


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rounded_optional(value: object, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def source_binding(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "size": path.stat().st_size,
        "sha256": digest(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--verification", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    verification = json.loads(args.verification.read_text(encoding="utf-8"))
    if payload.get("status") != "PASS" or verification.get("status") != "PASS":
        raise RuntimeError("source scan or verification not PASS")
    if payload.get("schema") != "TDX-CONVERTIBLE-BOND-WEIGHTED-SCAN-V5":
        raise RuntimeError("summary requires weighted scan V5")
    if verification.get("schema") != "TDX-CONVERTIBLE-BOND-WEIGHTED-VERIFY-V5":
        raise RuntimeError("summary requires weighted verification V5")
    run_id = str(payload.get("run_id") or "")
    if not run_id or verification.get("run_id") != run_id or (args.run_id is not None and str(args.run_id) != run_id):
        raise RuntimeError("summary input run_id mismatch")
    if verification.get("input", {}).get("sha256") != digest(args.input):
        raise RuntimeError("verification does not bind the current scan")

    eligible = payload.get("all_results") or []
    excluded = payload.get("hard_excluded_results") or []
    if not (
        len(eligible) == int(payload.get("eligible_count", -1))
        == int(payload.get("ranked_count", -1))
        and len(excluded) == int(payload.get("hard_excluded_count", -1))
        and len(eligible) + len(excluded) == int(payload.get("evaluated_count", -1))
        == int(payload.get("universe_count", -1))
    ):
        raise RuntimeError("summary universe partition mismatch")
    if payload.get("ranking_top10") != eligible[:10] or len(payload.get("ranking_top10") or []) != 10:
        raise RuntimeError("summary Top10 partition mismatch")

    redemption_meta = payload.get("redemption_announcement_snapshot") or {}
    redemption_path = Path(str(redemption_meta.get("path") or ""))
    if not (
        redemption_path.is_file()
        and redemption_meta.get("status") == "PASS"
        and redemption_meta.get("current_universe_complete") is True
        and redemption_meta.get("run_id") == run_id
        and redemption_meta.get("cutoff") == payload.get("cutoff_trade_date")
        and int(redemption_meta.get("size", -1)) == redemption_path.stat().st_size
        and redemption_meta.get("sha256") == digest(redemption_path)
    ):
        raise RuntimeError("summary redemption snapshot binding mismatch")

    rows = []
    for item in payload["ranking_top10"]:
        components = item["score_components"]
        heat_raw = components["c9_sector_heat"]["raw_value"]
        best_concept = heat_raw.get("best_concept") or {}
        rows.append({
            "rank": item["rank"],
            "bond": f'{item["name"]}（{item["symbol"]}）',
            "symbol": item["symbol"],
            "underlying": f'{item["underlying_name"]}（{item["underlying_symbol"]}）',
            "underlying_symbol": item["underlying_symbol"],
            "score": round(float(item["score_total_raw"]), 2),
            "component_scores": {
                key: round(float(value["earned_score"]), 2) for key, value in components.items()
            },
            "bond_close": rounded_optional(item.get("bond_close")),
            "daily_return_pct": rounded_optional(item.get("daily_return_pct")),
            "bond_volume_ratio_5d": rounded_optional(item.get("bond_volume_ratio_5d")),
            "weekly_return_pct": rounded_optional(item.get("weekly_return_pct")),
            "remaining_yi": round(float(item["remaining_yi"]), 2),
            "premium_pct": rounded_optional(item.get("premium_pct")),
            "turnover_5d_pct": rounded_optional(item.get("turnover_5d_pct")),
            "scr90_change_1d_pp": rounded_optional(item.get("scr90_change_1d_pp"), 4),
            "early_redemption_status": item.get("early_redemption_status"),
            "hard_exclusion_pass": item.get("hard_exclusion_pass") is True,
            "industry": item.get("industry", {}).get("industry_name"),
            "industry_heat_score": item.get("industry", {}).get("heat_score"),
            "best_concept": best_concept.get("name"),
            "best_concept_heat_score": best_concept.get("heat_score"),
            "personal_kb_confirmation_quality": round(
                float(
                    (item.get("personal_kb_confirmation") or {}).get("quality_score")
                    or 0.0
                ),
                2,
            ),
            "personal_kb_confirmation_level": (
                item.get("personal_kb_confirmation") or {}
            ).get("level"),
            "personal_kb_confirmation_risk_labels": (
                item.get("personal_kb_confirmation") or {}
            ).get("risk_labels", []),
            "big_bull_red_preference": item["big_bull_red_preference"],
            "risk_level": item["risk_level"],
            "risk_labels": [*item.get("risk_veto_reasons", []), *item.get("risk_warning_labels", [])],
        })

    excluded_rows = [
        {
            "symbol": item["symbol"],
            "name": item["name"],
            "hard_exclusion_reasons": item["hard_exclusion_reasons"],
            "bond_close": rounded_optional(item.get("bond_close")),
            "daily_return_pct": rounded_optional(item.get("daily_return_pct")),
            "bond_volume_ratio_5d": rounded_optional(item.get("bond_volume_ratio_5d")),
            "scr90_change_1d_pp": rounded_optional(item.get("scr90_change_1d_pp"), 4),
            "turnover_5d_pct": rounded_optional(item.get("turnover_5d_pct")),
            "early_redemption_status": item.get("early_redemption_status"),
        }
        for item in excluded
    ]
    summary = {
        "schema": "CONVERTIBLE-BOND-SCREENING-SUMMARY-3",
        "status": "PASS",
        "run_id": run_id,
        "cutoff_trade_date": payload["cutoff_trade_date"],
        "universe_count": payload["universe_count"],
        "evaluated_count": payload["evaluated_count"],
        "eligible_count": payload["eligible_count"],
        "ranked_count": payload["ranked_count"],
        "hard_excluded_count": payload["hard_excluded_count"],
        "hard_exclusion_reason_counts": payload["hard_exclusion_reason_counts"],
        "unavailable_local_retained_count": payload.get("unavailable_local_retained_count", 0),
        "score_model": payload["score_model"],
        "hard_exclusion_model": payload["hard_exclusion_model"],
        "personal_kb_confirmation_model": payload[
            "personal_kb_confirmation_model"
        ],
        "top10": rows,
        "hard_excluded": excluded_rows,
        "source_bindings": {
            "scan": source_binding(args.input),
            "verification": source_binding(args.verification),
            "redemption_announcements": source_binding(redemption_path),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    summary = canonicalize_business_payload(summary)
    atomic_write_json(args.output, summary)
    readback = json.loads(args.output.read_text(encoding="utf-8"))
    if (
        readback.get("status") != "PASS"
        or len(readback.get("top10", [])) != 10
        or int(readback.get("eligible_count", -1)) + int(readback.get("hard_excluded_count", -1))
        != int(readback.get("universe_count", -2))
    ):
        raise RuntimeError("summary readback mismatch")
    print(json.dumps({
        "status": "PASS",
        "output": str(args.output),
        "size": args.output.stat().st_size,
        "sha256": digest(args.output),
        "eligible_count": summary["eligible_count"],
        "hard_excluded_count": summary["hard_excluded_count"],
        "top10": rows,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
