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
import math
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from attest_stock_execution import build_and_attest


ROOT = Path(__file__).resolve().parents[1]
SUPPORT_ENTRY = (Path.home() / ".codex" / "skills" / "support-pressure-analysis-system" / "scripts" / "codex_entry.py").resolve()


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def normalize_symbol(value: str) -> tuple[str, str]:
    code = value.strip().split(".")[0]
    if not (len(code) == 6 and code.isdigit()):
        raise ValueError("symbol must be a six-digit A-share code")
    market = "SH" if code.startswith(("5", "6", "9")) else "SZ"
    return code, f"{code}.{market}"


def default_benchmark(code: str) -> str:
    if code.startswith(("300", "301")):
        return "sz.399006"
    if code.startswith("688"):
        return "sh.000688"
    if code.startswith(("0", "2", "3")):
        return "sz.399001"
    return "sh.000001"


def finite_positive(value: float, label: str) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a positive finite number")
    return value


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_support_report(report: dict[str, Any]) -> dict[str, Any]:
    """Normalize the canonical scientific support report for monitor calculations."""
    if report.get("engine_version"):
        context = report.get("technical_context") or {}
        quality = report.get("data_quality") or {}
        provenance = report.get("data_provenance") or {}
        conclusion = report.get("conclusion") or {}

        def zone_center(name: str) -> float | None:
            zone = conclusion.get(name) or {}
            value = zone.get("center")
            return float(value) if isinstance(value, (int, float)) else None

        def trigger_price(name: str) -> float | None:
            trigger = conclusion.get(name) or {}
            value = trigger.get("price")
            return float(value) if isinstance(value, (int, float)) else None

        zones = []
        for name in (
            "primary_support_zone",
            "secondary_support_zone",
            "major_structural_support_zone",
            "primary_resistance_zone",
            "secondary_resistance_zone",
            "major_structural_resistance_zone",
        ):
            zone = conclusion.get(name) or {}
            center = zone.get("center")
            if isinstance(center, (int, float)):
                zones.append(
                    {
                        "level": float(center),
                        "strength": str(zone.get("final_grade_capped_by_walk_forward") or zone.get("local_grade") or ""),
                    }
                )
        return {
            "status": report.get("status"),
            "symbol": report.get("symbol"),
            "last_close": context.get("close"),
            "last_date": quality.get("end_date"),
            "data_source": provenance.get("source_type"),
            "kline_count": quality.get("bar_count"),
            "atr_14": context.get("atr14"),
            "primary_support_zone": zone_center("primary_support_zone"),
            "secondary_support_zone": zone_center("secondary_support_zone"),
            "primary_resistance_zone": zone_center("primary_resistance_zone"),
            "breakout_trigger": trigger_price("breakout_trigger"),
            "breakdown_trigger": trigger_price("breakdown_trigger"),
            "combined": {
                "method_scores": {},
                "overall_score": None,
                "signal_quality": conclusion.get("state"),
                "confluence_zones": zones,
            },
            "methods": {"gann": {"sq9_levels": []}},
            "scientific_engine_version": report.get("engine_version"),
            "scientific_methodology": report.get("methodology"),
            "validation_grade": (report.get("walk_forward_validation") or {}).get("validation_grade"),
        }
    return report


def add_candidate(target: list[dict[str, Any]], price: Any, source: str, priority: int, strength: str = "") -> None:
    if isinstance(price, (int, float)) and math.isfinite(float(price)) and float(price) > 0:
        target.append({"price": round(float(price), 2), "source": source, "priority": priority, "strength": strength})


def dedupe(candidates: list[dict[str, Any]], tolerance: float = 0.005, reverse: bool = False) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for candidate in sorted(candidates, key=lambda row: (-row["priority"], row["price"])):
        if any(abs(candidate["price"] - row["price"]) / max(row["price"], 0.01) <= tolerance for row in selected):
            continue
        selected.append(candidate)
    return sorted(selected, key=lambda row: row["price"], reverse=reverse)


def pnl(price: float, cost: float, shares: int) -> float:
    return round((price - cost) * shares, 2)


def derive_monitor(stock: dict[str, Any], cost: float, shares: int) -> dict[str, Any]:
    last = float(stock["last_close"])
    atr = float(stock.get("atr_14") or 0)
    combined = stock.get("combined", {})
    confluence = combined.get("confluence_zones", [])
    methods = stock.get("methods", {})
    gann_levels = methods.get("gann", {}).get("sq9_levels", [])

    below_confluence = sorted((row for row in confluence if float(row["level"]) <= last), key=lambda row: float(row["level"]), reverse=True)
    above_strong = sorted(
        (row for row in confluence if float(row["level"]) > last and row.get("strength") in {"high", "strongest"}),
        key=lambda row: float(row["level"]),
    )
    gann_below = sorted((row for row in gann_levels if row.get("direction") == "below" and float(row["level"]) < last), key=lambda row: float(row["level"]), reverse=True)[:2]
    gann_above = sorted((row for row in gann_levels if row.get("direction") == "above" and float(row["level"]) > last), key=lambda row: float(row["level"]))[:2]

    downside: list[dict[str, Any]] = []
    upside: list[dict[str, Any]] = []
    if below_confluence:
        row = below_confluence[0]
        add_candidate(downside, row["level"], "nearest_confluence_support", 70, row.get("strength", ""))
    for index, row in enumerate(gann_below, start=1):
        add_candidate(downside, row["level"], f"gann_sq9_below_{index}", 60)
    for index, row in enumerate(gann_above, start=1):
        add_candidate(upside, row["level"], f"gann_sq9_above_{index}", 60)
    if above_strong:
        row = above_strong[0]
        add_candidate(upside, row["level"], "nearest_high_confluence", 80, row.get("strength", ""))

    if cost <= last:
        add_candidate(downside, cost, "user_cost_anchor", 100)
    else:
        add_candidate(upside, cost, "user_cost_anchor", 100)
    primary_support = stock.get("primary_support_zone")
    if isinstance(primary_support, (int, float)) and float(primary_support) <= last:
        add_candidate(downside, primary_support, "primary_structural_support", 90)
    add_candidate(downside, stock.get("breakdown_trigger"), "breakdown_trigger", 90)
    add_candidate(upside, stock.get("primary_resistance_zone"), "primary_structural_resistance", 90)
    add_candidate(upside, stock.get("breakout_trigger"), "breakout_trigger", 90)

    downside = dedupe(downside, reverse=True)
    upside = dedupe(upside, reverse=False)
    for index, row in enumerate(downside, start=1):
        row["sequence"] = index
        row["pnl"] = pnl(row["price"], cost, shares)
        row.pop("priority", None)
    for index, row in enumerate(upside, start=1):
        row["sequence"] = index
        row["pnl"] = pnl(row["price"], cost, shares)
        row.pop("priority", None)

    raw_secondary = stock.get("secondary_support_zone")
    invalid_secondary = isinstance(raw_secondary, (int, float)) and float(raw_secondary) > last
    return {
        "position": {
            "cost": cost,
            "shares": shares,
            "cost_basis": round(cost * shares, 2),
            "last_price": round(last, 2),
            "market_value": round(last * shares, 2),
            "unrealized_pnl": pnl(last, cost, shares),
            "unrealized_return_pct": round((last / cost - 1) * 100, 2),
            "pnl_per_0_01": round(0.01 * shares, 2),
            "pnl_per_1_yuan": round(1.0 * shares, 2),
            "pnl_per_1pct_of_cost": round(cost * 0.01 * shares, 2),
        },
        "technical": {
            "last_date": stock.get("last_date"),
            "data_source": stock.get("data_source"),
            "kline_count": stock.get("kline_count"),
            "atr_14": atr,
            "method_scores": combined.get("method_scores", {}),
            "overall_score": combined.get("overall_score"),
            "signal_quality": combined.get("signal_quality"),
            "primary_support": stock.get("primary_support_zone"),
            "primary_resistance": stock.get("primary_resistance_zone"),
            "breakout_trigger": stock.get("breakout_trigger"),
            "breakdown_trigger": stock.get("breakdown_trigger"),
            "raw_secondary_support": raw_secondary,
            "raw_secondary_support_excluded": invalid_secondary,
        },
        "downside_alerts": downside,
        "upside_observations": upside,
        "monitor_contract": {
            "quote_cycle_seconds": 1,
            "indicator_cycle": "1-minute-bar-close",
            "stale_quote_seconds": 5,
            "dual_feed_divergence_pct": 0.3,
            "confirmation": ["fresh_data", "vwap", "volume", "persistence", "relative_strength"],
            "red_and_critical_acknowledgement": True,
            "no_auto_order": True,
        },
        "boundaries": {
            "continuous_realtime_daemon": "not verified",
            "windows_popup_delivery": "not verified",
            "broker_account_link": "not verified",
            "automatic_ordering": False,
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    position = result["position"]
    technical = result["technical"]
    lines = [
        f"# {result['symbol']} 盘中持仓监控方案",
        "",
        f"- 快照时间：{result['generated_at']}",
        f"- 行情日期：{technical['last_date']}",
        f"- 最新价：{position['last_price']:.2f} 元",
        f"- 成本：{position['cost']:.2f} 元",
        f"- 数量：{position['shares']} 股",
        f"- 市值：{position['market_value']:.2f} 元",
        f"- 浮动盈亏：{position['unrealized_pnl']:.2f} 元",
        f"- 综合信号：{technical['signal_quality']}（{technical['overall_score']}）",
        "",
        "## 下行监控线",
        "",
        "| 顺序 | 价格 | 持仓盈亏 | 来源 |",
        "|---:|---:|---:|---|",
    ]
    for row in result["downside_alerts"]:
        lines.append(f"| {row['sequence']} | {row['price']:.2f} | {row['pnl']:.2f} | {row['source']} |")
    lines.extend(["", "## 上行观察线", "", "| 顺序 | 价格 | 持仓盈亏 | 来源 |", "|---:|---:|---:|---|"])
    for row in result["upside_observations"]:
        lines.append(f"| {row['sequence']} | {row['price']:.2f} | {row['pnl']:.2f} | {row['source']} |")
    lines.extend(
        [
            "",
            "## 触发规则",
            "",
            "- 单一价格越线只产生预警，正式告警必须叠加行情时效、VWAP、成交量、持续时间和相对强弱确认。",
            "- 行情超过5秒未更新或双源偏差超过0.3%时进入数据故障状态。",
            "- 本方案不自动下单。",
            "",
            "## 未验证边界",
            "",
            "- 持续实时守护：not verified。",
            "- Windows弹窗送达：not verified。",
            "- 券商账户联动：not verified。",
            "",
            "> 仅用于研究与风险监控，不构成收益承诺或确定性买卖建议。",
        ]
    )
    return "\n".join(lines) + "\n"


def synthetic_selftest() -> int:
    stock = {
        "last_close": 27.42,
        "last_date": "2026-07-22",
        "data_source": "synthetic",
        "kline_count": 120,
        "atr_14": 2.32,
        "primary_support_zone": 23.92,
        "secondary_support_zone": 34.25,
        "primary_resistance_zone": 33.01,
        "breakout_trigger": 34.17,
        "breakdown_trigger": 22.76,
        "combined": {
            "method_scores": {"elliott": 85, "chan": 40, "fibonacci": 85, "gann": 50, "wyckoff": 0},
            "overall_score": 46.5,
            "signal_quality": "中性矛盾",
            "confluence_zones": [
                {"level": 26.92, "strength": "low"},
                {"level": 31.07, "strength": "high"},
            ],
        },
        "methods": {
            "gann": {
                "sq9_levels": [
                    {"level": 28.31, "direction": "above"},
                    {"level": 25.72, "direction": "below"},
                    {"level": 29.66, "direction": "above"},
                    {"level": 24.46, "direction": "below"},
                ]
            }
        },
    }
    result = derive_monitor(stock, 25.0, 200_000)
    down = [row["price"] for row in result["downside_alerts"]]
    up = [row["price"] for row in result["upside_observations"]]
    assert down == [26.92, 25.72, 25.0, 24.46, 23.92, 22.76]
    assert up == [28.31, 29.66, 31.07, 33.01, 34.17]
    assert result["position"]["cost_basis"] == 5_000_000
    assert result["position"]["unrealized_pnl"] == 484_000
    assert result["technical"]["raw_secondary_support_excluded"] is True
    assert result["monitor_contract"]["no_auto_order"] is True
    emit({"status": "CLEAN_PASS", "downside": down, "upside": up, "unrealized_pnl": 484000})
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a fresh A-share intraday holding-monitor plan")
    parser.add_argument("--symbol")
    parser.add_argument("--cost", type=float)
    parser.add_argument("--shares", type=int)
    parser.add_argument("--benchmark")
    parser.add_argument("--name", default="")
    parser.add_argument("--out-dir")
    parser.add_argument("--run-id")
    parser.add_argument("--stock-attestation", choices=("auto", "required", "off"), default="auto")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return synthetic_selftest()
    try:
        if args.symbol is None or args.cost is None or args.shares is None:
            raise ValueError("--symbol, --cost and --shares are required")
        code, canonical = normalize_symbol(args.symbol)
        cost = finite_positive(float(args.cost), "cost")
        if args.shares <= 0:
            raise ValueError("shares must be a positive integer")
        shares = int(args.shares)
        benchmark = args.benchmark or default_benchmark(code)
        run_id = args.run_id or f"monitor_{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        out_dir = Path(args.out_dir).resolve() if args.out_dir else ROOT / "reports" / "runs" / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        support_dir = out_dir / "support-analysis"
        command = [
            sys.executable,
            str(SUPPORT_ENTRY),
            "run",
            "--",
            "--mode",
            "pressure",
            "--symbols",
            canonical,
            "--out-dir",
            str(support_dir),
            "--run-id",
            run_id,
        ]
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=180,
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        if completed.returncode != 0:
            raise RuntimeError(f"support workflow failed: {completed.stderr[-800:]} {completed.stdout[-800:]}")
        summary_path = support_dir / "run_summary.json"
        if not summary_path.is_file():
            raise RuntimeError(f"support summary missing: {summary_path}")
        support_summary = json.loads(summary_path.read_text(encoding="utf-8"))
        item = next((row for row in support_summary.get("items", []) if row.get("symbol") == canonical), None)
        if item is None or item.get("status") != "PASS":
            raise RuntimeError(f"target analysis not PASS: {canonical}: {item}")
        report_path = Path(item["artifact"]["path"])
        if not report_path.is_file():
            raise RuntimeError(f"support report missing: {report_path}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report.get("status") != "PASS" or report.get("symbol") != canonical:
            raise RuntimeError(f"support report readback mismatch: {canonical}")
        stock = normalize_support_report(report)
        monitor = derive_monitor(stock, cost, shares)
        result = {
            "skill": "a-share-intraday-position-monitor",
            "status": "PASS",
            "run_id": run_id,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "symbol": canonical,
            "benchmark": benchmark,
            "support_skill": "support-pressure-analysis-system",
            "support_engine_version": report.get("engine_version"),
            "support_methodology": report.get("methodology"),
            "support_report": str(report_path),
            "support_report_sha256": file_sha256(report_path),
            **monitor,
        }
        result_path = out_dir / "monitor_result.json"
        summary_path = out_dir / "monitor_summary.md"
        validation_path = out_dir / "validation.json"
        result["result_path"] = str(result_path)
        result["summary_path"] = str(summary_path)
        result["validation_path"] = str(validation_path)
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        summary_path.write_text(render_markdown(result), encoding="utf-8")
        readback = json.loads(result_path.read_text(encoding="utf-8"))
        checks = {
            "status_pass": readback.get("status") == "PASS",
            "symbol_exact": readback.get("symbol") == canonical,
            "cost_exact": readback["position"]["cost"] == cost,
            "shares_exact": readback["position"]["shares"] == shares,
            "formula_cost_basis": readback["position"]["cost_basis"] == round(cost * shares, 2),
            "target_source_pass": report.get("status") == "PASS",
            "target_source_symbol_exact": report.get("symbol") == canonical,
            "canonical_scientific_executor": bool(report.get("engine_version")),
            "support_report_bound": readback.get("support_report_sha256") == file_sha256(report_path),
            "no_auto_order": readback["monitor_contract"]["no_auto_order"] is True,
            "runtime_boundary_visible": readback["boundaries"]["continuous_realtime_daemon"] == "not verified",
        }
        validation = {
            "status": "PASS" if all(checks.values()) else "BLOCKED",
            "checks": checks,
            "result_sha256": file_sha256(result_path),
            "result_size": result_path.stat().st_size,
            "summary_sha256": file_sha256(summary_path),
            "summary_size": summary_path.stat().st_size,
        }
        validation_path.write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")
        if validation["status"] != "PASS":
            raise RuntimeError(f"validation failed: {validation}")
        stock_attestation: dict[str, Any] = {"status": "OFF"}
        if args.stock_attestation != "off":
            primary_argv = [
                sys.executable,
                str(ROOT / "scripts" / "codex_entry.py"),
                "run",
                "--",
                "--symbol",
                code,
                "--cost",
                str(cost),
                "--shares",
                str(shares),
                "--benchmark",
                benchmark,
                "--out-dir",
                str(out_dir),
                "--run-id",
                run_id,
            ]
            if args.name:
                primary_argv.extend(["--name", args.name])
            stock_attestation = build_and_attest(
                result_path=result_path,
                support_report_path=report_path,
                support_argv=command,
                primary_argv=primary_argv,
                target_name=args.name or str(stock.get("name") or code),
                output_dir=out_dir,
            )
            if args.stock_attestation == "required" and stock_attestation.get("status") != "PASS":
                raise RuntimeError(f"stock attestation required: {stock_attestation}")
            validation["stock_skill_attestation"] = stock_attestation
            validation_path.write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")
        emit(
            {
                "status": "PASS",
                "skill": result["skill"],
                "symbol": canonical,
                "last_price": result["position"]["last_price"],
                "market_value": result["position"]["market_value"],
                "unrealized_pnl": result["position"]["unrealized_pnl"],
                "downside_alerts": [row["price"] for row in result["downside_alerts"]],
                "upside_observations": [row["price"] for row in result["upside_observations"]],
                "result_path": str(result_path),
                "validation_path": str(validation_path),
                "stock_skill_attestation": stock_attestation,
                "continuous_realtime_daemon": "not verified",
                "automatic_ordering": False,
            }
        )
        return 0
    except Exception as exc:
        emit({"status": "BLOCKED", "skill": "a-share-intraday-position-monitor", "error": f"{type(exc).__name__}: {exc}"})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
