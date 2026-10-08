from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import importlib.util
import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPORT = SKILL_ROOT / "reports" / "strong-leader-first-yin-latest.json"
SCANNER = SKILL_ROOT / "scripts" / "run_strong_leader_first_yin.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_scanner():
    spec = importlib.util.spec_from_file_location("strong_leader_first_yin", SCANNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    scanner = load_scanner()
    hub = scanner.load_tdx_hub()
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    assert payload["status"] == "CLEAN_PASS"
    assert payload["validation"]["selector_operational"] is True
    assert payload["universe"]["scan_stats"]["latest_trade_date"] > 1000

    replay = payload["historical_replay"]
    historical_total = (
        replay["strict_signal_count"]
        + replay["turnover_divergence_signal_count"]
        + replay["practical_signal_count"]
    )
    assert historical_total > 0

    selection = payload["selection"]
    groups = (
        ("S", selection["strict_candidates"], "strict_conditions"),
        ("T", selection["turnover_divergence_candidates"], "turnover_divergence_conditions"),
        ("A", selection["practical_candidates"], "practical_conditions"),
    )
    verified_candidates = []
    for grade, candidates, conditions_key in groups:
        for candidate in candidates:
            assert candidate["grade"] == grade
            assert all(candidate[conditions_key].values())
            assert candidate["name"] and "\ufffd" not in candidate["name"]
            source = Path(candidate["source"]["path"])
            assert source.stat().st_size == candidate["source"]["size"]
            assert sha256(source) == candidate["source"]["sha256"]
            rows = hub.read_records(source, hub.DAY_RECORD, hub.parse_day_record, 2)
            latest = rows[-1]
            metrics = candidate["metrics"]
            assert latest["date"] == metrics["date"] == payload["latest_trade_date"]
            for field in ("open", "high", "low", "close"):
                assert round(float(latest[field]), 2) == float(metrics[field])
            verified_candidates.append(
                {
                    "symbol": candidate["symbol"],
                    "name": candidate["name"],
                    "grade": grade,
                    "score": candidate["score"],
                    "technical_trade_ready": candidate["technical_trade_ready"],
                    "source_sha256": candidate["source"]["sha256"],
                }
            )

    assert len(verified_candidates) == (
        selection["strict_count"]
        + selection["turnover_divergence_count"]
        + selection["practical_count"]
    )
    result = {
        "status": "CLEAN_PASS",
        "report": str(REPORT),
        "report_size": REPORT.stat().st_size,
        "report_sha256": sha256(REPORT),
        "latest_trade_date": payload["latest_trade_date"],
        "latest_records": payload["universe"]["scan_stats"]["latest_trade_date"],
        "historical_signal_count": historical_total,
        "verified_candidates": verified_candidates,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
