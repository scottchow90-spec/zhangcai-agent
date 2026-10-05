#!/usr/bin/env python3
"""Run one point-in-time future-hotspot forecast and leader lineage chain."""
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
import os
import sys
import sys
from datetime import date, datetime, time
from pathlib import Path
from typing import Sequence
from zoneinfo import ZoneInfo

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_tdx_root

from catalyst_features import fuse_catalysts, validate_evidence_rows
from forecast_gate import (
    validate_delivery_manifest,
    validate_pipeline_lineage,
    write_delivery_manifest,
)
from forecast_model import forecast_with_provisional_models
from leader_ranker import rank_leaders
from market_features import build_market_features
from point_in_time_snapshot import SnapshotBlocked, build_point_in_time_snapshot


ROOT = Path(__file__).resolve().parents[1]
_TDX_ROOT = resolve_tdx_root()
BLOCKNEW_CANDIDATES = (_TDX_ROOT / "T0002" / "blocknew",)
VIPDOC_CANDIDATES = (_TDX_ROOT / "vipdoc",)


def _json_write(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _csv_value(value: object) -> object:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def _write_csv(path: Path, rows: Sequence[dict], fields: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})


def _top_forecasts(rows: list[dict], count: int = 5) -> list[dict]:
    selected: list[dict] = []
    for horizon in ("H1", "H2", "H3"):
        candidates = [row for row in rows if row["horizon"] == horizon]
        candidates.sort(key=lambda row: (-row["final_probability"], row["sector"]))
        for rank, row in enumerate(candidates, start=1):
            row["final_rank"] = rank
            if rank <= count:
                selected.append(row)
    return selected


def _backtest_placeholder(snapshot_id: str) -> dict:
    return {
        "schema": "SHORTLINE_WALK_FORWARD_BACKTEST_V1",
        "snapshot_id": snapshot_id,
        "forecast_status": "PROVISIONAL_FORECAST",
        "validated": False,
        "fold_count": 0,
        "status_reasons": [
            "historical_point_in_time_membership_not_accumulated",
            "minimum_252_train_60_validation_60_test_dates_not_proven",
            "sample_out_promotion_gates_not_run_for_current_model",
        ],
        "metrics": {},
        "predictions": [],
    }


def _report_text(
    *,
    requested_date: date,
    resolved_date: str,
    forecast_status: str,
    forecasts: list[dict],
    leaders: list[dict],
) -> str:
    lines = [
        "# A股短线热点未来预测",
        "",
        f"- 请求日期：{requested_date.isoformat()}",
        f"- 解析交易日：{resolved_date}",
        f"- 科学状态：`{forecast_status}`",
        "- 预测窗口：H1=T+1至T+3，H2=T+4至T+7，H3=T+8至T+10。",
        "- 当前概率来自透明 provisional 模型；未通过完整滚动样本外门槛，不得表述为已验证模型。",
        "- 本报告是可证伪研究预测，不构成买卖、仓位或收益承诺。",
        "",
        "## 预测板块",
        "",
        "| 窗口 | 排名 | 板块 | 市场概率 | 催化调整 | 最终概率 |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for row in forecasts:
        lines.append(
            f"| {row['horizon']} | {row['final_rank']} | {row['sector']} | "
            f"{row['market_probability']:.4f} | {row['catalyst_adjustment']:.4f} | "
            f"{row['final_probability']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## 候选内龙头",
            "",
            "| 窗口 | 板块 | 排名 | 代码 | 龙头概率 |",
            "|---|---|---:|---|---:|",
        ]
    )
    for row in leaders:
        lines.append(
            f"| {row.get('horizon') or ''} | {row['sector']} | {row['leader_rank']} | "
            f"{row['code']} | {row['leader_probability']:.4f} |"
        )
    return "\n".join(lines) + "\n"


def run_forecast(
    *,
    mode: str,
    requested_date: date,
    output_dir: Path,
    blocknew_dir: Path,
    vipdoc_roots: Sequence[Path],
    evidence_rows: Sequence[dict],
) -> dict:
    if mode not in {"all", "hotspot", "leader"}:
        raise ValueError(f"unknown_mode:{mode}")
    output_dir.mkdir(parents=True, exist_ok=False)
    snapshot = build_point_in_time_snapshot(
        requested_date=requested_date,
        cutoff_time=time(15, 0),
        blocknew_dir=blocknew_dir,
        vipdoc_roots=vipdoc_roots,
    )
    feature_snapshot = build_market_features(snapshot)
    provisional = forecast_with_provisional_models(feature_snapshot)
    if not provisional["forecasts"]:
        raise SnapshotBlocked("no_rank_eligible_forecast_sectors")
    cutoff = datetime.combine(
        date.fromisoformat(snapshot["resolved_trade_date"]),
        time(15, 0),
        tzinfo=ZoneInfo("Asia/Shanghai"),
    )
    normalized_evidence = validate_evidence_rows(evidence_rows, cutoff) if evidence_rows else []
    fused = fuse_catalysts(
        provisional["forecasts"],
        normalized_evidence,
        cutoff,
        provisional["forecast_status"],
    )
    candidates = _top_forecasts(fused)
    leaders = rank_leaders(snapshot, candidates)
    lineage = validate_pipeline_lineage(snapshot, feature_snapshot, candidates, leaders)
    if lineage["status"] != "PASS":
        raise SnapshotBlocked(";".join(lineage["errors"]))

    _json_write(output_dir / "forecast_snapshot.json", snapshot)
    _json_write(output_dir / "feature_snapshot.json", feature_snapshot)
    _write_csv(
        output_dir / "forecast_rank.csv",
        candidates,
        (
            "snapshot_id",
            "feature_cutoff_date",
            "sector",
            "horizon",
            "market_rank",
            "final_rank",
            "market_probability",
            "catalyst_score",
            "catalyst_adjustment",
            "final_probability",
            "evidence_ids",
            "model_version",
            "calibration_version",
            "feature_contributions",
            "forecast_status",
        ),
    )
    _write_csv(
        output_dir / "leader_rank.csv",
        leaders,
        (
            "snapshot_id",
            "resolved_trade_date",
            "sector",
            "horizon",
            "sector_forecast_probability",
            "sector_forecast_rank",
            "code",
            "leader_rank",
            "leader_score",
            "leader_probability",
            "sector_dependency",
            "member_of_frozen_sector",
            "reasons",
            "risks",
            "invalidation",
        ),
    )
    _json_write(
        output_dir / "evidence.json",
        {
            "schema": "SHORTLINE_CATALYST_EVIDENCE_V1",
            "snapshot_id": snapshot["snapshot_id"],
            "cutoff_time": cutoff.isoformat(),
            "evidence": normalized_evidence,
        },
    )
    _json_write(output_dir / "model_card.json", provisional["model_card"])
    backtest = _backtest_placeholder(snapshot["snapshot_id"])
    _json_write(output_dir / "backtest_report.json", backtest)
    audit = {
        "schema": "SHORTLINE_FORECAST_AUDIT_V1",
        "status": "PASS",
        "forecast_status": provisional["forecast_status"],
        "snapshot_id": snapshot["snapshot_id"],
        "resolved_trade_date": snapshot["resolved_trade_date"],
        "mode": mode,
        "checks": {
            "point_in_time_snapshot": "PASS",
            "feature_cutoff": "PASS",
            "catalyst_cutoff": "PASS",
            "candidate_lineage": "PASS",
            "leader_membership": "PASS",
            "sample_out_validation": "NOT_PROVEN",
        },
        "warnings": backtest["status_reasons"],
    }
    _json_write(output_dir / "audit.json", audit)
    (output_dir / "report.md").write_text(
        _report_text(
            requested_date=requested_date,
            resolved_date=snapshot["resolved_trade_date"],
            forecast_status=provisional["forecast_status"],
            forecasts=candidates,
            leaders=leaders,
        ),
        encoding="utf-8",
    )
    model_versions = sorted({row["model_version"] for row in candidates})
    manifest = write_delivery_manifest(
        output_dir,
        snapshot_id=snapshot["snapshot_id"],
        resolved_trade_date=snapshot["resolved_trade_date"],
        forecast_status=provisional["forecast_status"],
        model_version="+".join(model_versions),
    )
    gate = validate_delivery_manifest(manifest, output_dir)
    return {
        "schema": "MERGED_STOCK_SKILL_RESULT_V3",
        "skill_id": ROOT.name,
        "mode": mode,
        "status": gate["status"],
        "forecast_status": provisional["forecast_status"],
        "snapshot_id": snapshot["snapshot_id"],
        "resolved_trade_date": snapshot["resolved_trade_date"],
        "manifest_path": str((output_dir / "manifest.json").resolve()),
        "warnings": audit["warnings"],
        "errors": gate["errors"],
    }


def _parse_requested_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date_must_be_YYYYMMDD") from exc


def _resolve_live_sources() -> tuple[Path, list[Path]]:
    explicit_blocknew = os.environ.get("SHORTLINE_TDX_BLOCKNEW_DIR")
    explicit_vipdocs = os.environ.get("SHORTLINE_TDX_VIPDOC_ROOTS")
    blocknew = (
        Path(explicit_blocknew)
        if explicit_blocknew
        else next((path for path in BLOCKNEW_CANDIDATES if path.is_dir()), None)
    )
    vipdocs = (
        [Path(value) for value in explicit_vipdocs.split(os.pathsep) if value]
        if explicit_vipdocs
        else [path for path in VIPDOC_CANDIDATES if path.is_dir()]
    )
    if blocknew is None:
        raise SnapshotBlocked("tdx_blocknew_directory_missing")
    if not vipdocs:
        raise SnapshotBlocked("tdx_vipdoc_directory_missing")
    return blocknew, vipdocs


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=("all", "hotspot", "leader"),
        nargs="?",
        default="all",
    )
    parser.add_argument("--date", type=_parse_requested_date, default=date.today())
    parser.add_argument("--evidence-file")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    canonical_output = os.environ.get("SHORTLINE_CANONICAL_DELIVERABLES_DIR")
    output_dir = (
        Path(canonical_output)
        if canonical_output
        else Path(args.out)
        if args.out
        else ROOT
        / "reports"
        / "forecast-runs"
        / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    )
    try:
        evidence_rows: list[dict] = []
        if args.evidence_file:
            payload = json.loads(Path(args.evidence_file).read_text(encoding="utf-8"))
            evidence_rows = payload if isinstance(payload, list) else payload.get("evidence", [])
        blocknew, vipdocs = _resolve_live_sources()
        result = run_forecast(
            mode=args.mode,
            requested_date=args.date,
            output_dir=output_dir,
            blocknew_dir=blocknew,
            vipdoc_roots=vipdocs,
            evidence_rows=evidence_rows,
        )
    except Exception as exc:
        result = {
            "schema": "MERGED_STOCK_SKILL_RESULT_V3",
            "skill_id": ROOT.name,
            "mode": args.mode,
            "status": "BLOCKED",
            "forecast_status": "BLOCKED",
            "snapshot_id": None,
            "resolved_trade_date": None,
            "manifest_path": None,
            "warnings": [],
            "errors": [f"{type(exc).__name__}:{exc}"],
        }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
