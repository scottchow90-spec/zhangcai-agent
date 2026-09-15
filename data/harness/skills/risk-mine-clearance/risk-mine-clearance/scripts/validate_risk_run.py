from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import csv
import json
import re
from pathlib import Path


REQUIRED_FILES = (
    "run_manifest.json",
    "source_health.csv",
    "front_candidates.csv",
    "confirmed_risk_candidates.csv",
    "evidence.jsonl",
    "front_source_shcpe_enterprise_notices.csv",
    "front_source_wage_arrears_gd.csv",
    "front_source_court_defaulters_recent.csv",
    "market_risk_warning.json",
)

CRITICAL_SOURCES = (
    "notices",
    "guarantees",
    "shcpe_enterprise_notices",
    "credit_gd_wage_arrears",
    "credit_gd_court_defaulters_recent",
    "eastmoney_comment",
    "xueqiu_tweet",
)

SPECIFIC_RISK_WORDS = re.compile(
    r"债务|逾期|冻结|查封|立案|诉讼|仲裁|重整|担保|减值|坏账|库存|停产|订单|份额|客户|借款|虚增|欠薪|票据"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _source_is_healthy(row: dict[str, str] | None) -> bool:
    if not row or row.get("status") != "ok":
        return False
    try:
        return int(float(row.get("rows", "0") or 0)) > 0
    except ValueError:
        return False


def evaluate_source_health(rows: list[dict[str, str]]) -> dict[str, object]:
    health = {row.get("name", ""): row for row in rows if row.get("name")}
    critical_failures = {
        name: health.get(name, {}).get("status", "missing")
        for name in CRITICAL_SOURCES
        if not _source_is_healthy(health.get(name))
    }
    lawsuit_ok = _source_is_healthy(health.get("lawsuits"))
    pledge_ok = any(
        _source_is_healthy(health.get(name))
        for name in ("pledge_ratio", "pledge_detail")
    )
    news_rows = [row for name, row in health.items() if name.startswith("news_")]
    deep_news_ok = bool(news_rows) and all(_source_is_healthy(row) for row in news_rows)
    domains = {
        "critical_sources": not critical_failures,
        "lawsuit": lawsuit_ok,
        "pledge": pledge_ok,
        "deep_news": deep_news_ok,
    }
    return {
        "ok": all(domains.values()),
        "domains": domains,
        "failed_domains": [name for name, ok in domains.items() if not ok],
        "critical_failures": critical_failures,
        "news_sources_checked": sorted(
            row.get("name", "") for row in news_rows if row.get("name")
        ),
    }


def evaluate_all_sources(rows: list[dict[str, str]]) -> dict[str, object]:
    failures = {
        row.get("name", ""): row.get("status", "missing")
        for row in rows
        if row.get("status") != "ok"
    }
    return {
        "ok": bool(rows) and not failures,
        "source_count": len(rows),
        "failure_count": len(failures),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    output = Path(args.output).resolve() if args.output else run_dir / "skill_validation.json"
    checks: dict[str, object] = {}

    missing = [name for name in REQUIRED_FILES if not (run_dir / name).is_file()]
    checks["required_files"] = {"ok": not missing, "missing": missing}
    if missing:
        payload = {"ok": False, "run_dir": str(run_dir), "checks": checks}
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8-sig"))
    front = read_csv(run_dir / "front_candidates.csv")
    confirmed = read_csv(run_dir / "confirmed_risk_candidates.csv")
    health_rows = read_csv(run_dir / "source_health.csv")
    market_warning = json.loads(
        (run_dir / "market_risk_warning.json").read_text(encoding="utf-8-sig")
    )
    checks["market_risk_warning"] = {
        "ok": market_warning.get("schema") == "INTEGRATED_RISK_WARNING_V1"
        and market_warning.get("status") == "CLEAN_PASS"
        and bool(market_warning.get("indexes")),
        "schema": market_warning.get("schema"),
        "status": market_warning.get("status"),
        "risk_level": market_warning.get("risk_level"),
    }

    evidence: list[dict[str, object]] = []
    with (run_dir / "evidence.jsonl").open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                evidence.append(json.loads(line))

    checks["all_sources"] = evaluate_all_sources(health_rows)
    checks["critical_sources"] = evaluate_source_health(health_rows)

    count_checks = {
        "front": len(front) == int(manifest.get("front_candidate_count", -1)),
        "confirmed": len(confirmed) == int(manifest.get("confirmed_risk_candidate_count", -1)),
        "evidence": len(evidence) == int(manifest.get("evidence_count", -1)),
    }
    checks["manifest_counts"] = {"ok": all(count_checks.values()), "items": count_checks}

    signatures: set[tuple[str, str, str, str, str]] = set()
    duplicates = 0
    incomplete = 0
    for item in evidence:
        signature = (
            str(item.get("code", "")),
            str(item.get("domain", "")),
            str(item.get("title", "")),
            re.sub(r"\s+", "", str(item.get("detail", "")))[:250],
            str(item.get("source", "")),
        )
        if not all(signature):
            incomplete += 1
        if signature in signatures:
            duplicates += 1
        signatures.add(signature)
    checks["evidence_integrity"] = {
        "ok": incomplete == 0 and duplicates == 0,
        "incomplete": incomplete,
        "duplicates": duplicates,
    }

    priority = [
        row
        for row in front
        if int(float(row.get("evidence_domains", "0") or 0)) >= 2
        and SPECIFIC_RISK_WORDS.search((row.get("top_reasons", "") + row.get("top_detail", "")))
    ]
    checks["priority_selection"] = {
        "ok": True,
        "specific_priority_count": len(priority),
        "codes": [row.get("code", "") for row in priority],
    }

    ok = all(bool(value.get("ok")) for value in checks.values() if isinstance(value, dict))
    payload = {
        "ok": ok,
        "run_dir": str(run_dir),
        "run_id": manifest.get("run_id"),
        "run_date": manifest.get("run_date"),
        "front_count": len(front),
        "confirmed_count": len(confirmed),
        "evidence_count": len(evidence),
        "checks": checks,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
