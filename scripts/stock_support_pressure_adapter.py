#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label}_not_object")
    return value


def load_verified_support_candidates(summary_path: Path) -> dict[str, Any]:
    summary_path = Path(summary_path).resolve()
    summary = _require_mapping(
        json.loads(summary_path.read_text(encoding="utf-8-sig")), "summary"
    )
    items = summary.get("items")
    if summary.get("status") != "PASS" or not isinstance(items, list) or not items:
        raise ValueError("support_pressure_summary_not_pass")

    candidates: list[dict[str, Any]] = []
    for index, item_value in enumerate(items):
        item = _require_mapping(item_value, f"item_{index}")
        binding = _require_mapping(item.get("artifact"), f"item_{index}_artifact")
        if item.get("status") != "PASS" or binding.get("readback_status") != "PASS":
            raise ValueError(f"support_pressure_item_not_pass:{index}")
        artifact_path = Path(str(binding.get("path") or ""))
        if not artifact_path.is_absolute():
            artifact_path = summary_path.parent / artifact_path
        artifact_path = artifact_path.resolve()
        raw = artifact_path.read_bytes()
        if len(raw) != int(binding.get("size", -1)):
            raise ValueError(f"support_pressure_artifact_size_mismatch:{artifact_path}")
        digest = hashlib.sha256(raw).hexdigest()
        if digest != str(binding.get("sha256") or ""):
            raise ValueError(f"support_pressure_artifact_sha256_mismatch:{artifact_path}")

        report = _require_mapping(json.loads(raw.decode("utf-8-sig")), "report")
        provenance = _require_mapping(report.get("data_provenance"), "data_provenance")
        technical = _require_mapping(report.get("technical_context"), "technical_context")
        conclusion = _require_mapping(report.get("conclusion"), "conclusion")
        support_zone = _require_mapping(
            conclusion.get("primary_support_zone"), "primary_support_zone"
        )
        resistance_zone = _require_mapping(
            conclusion.get("primary_resistance_zone"), "primary_resistance_zone"
        )
        invalidation = _require_mapping(
            conclusion.get("support_scenario_invalidation"),
            "support_scenario_invalidation",
        )
        symbol = str(item.get("symbol") or report.get("symbol") or "")
        if (
            report.get("status") != "PASS"
            or not symbol
            or report.get("symbol") != symbol
            or provenance.get("source_type") != "tdx_local_hub"
            or provenance.get("history_scope") != "FULL_LOCAL_TDX_FILE"
            or provenance.get("full_history_verified") is not True
        ):
            raise ValueError(f"support_pressure_report_contract_failed:{index}")
        candidates.append(
            {
                "code": symbol,
                "name": symbol,
                "latest": technical.get("close"),
                "buy_low": support_zone.get("lower"),
                "invalid": invalidation.get("price"),
                "rsi14": technical.get("rsi14"),
                "location_state": conclusion.get("location_state"),
                "support_zone": support_zone,
                "resistance_zone": resistance_zone,
                "data_end_date": item.get("data_end_date"),
                "source": "support-pressure-analysis-system",
                "source_artifact": str(artifact_path),
                "source_artifact_sha256": digest,
                "tdx_data_path": provenance.get("data_path"),
                "tdx_data_sha256": provenance.get("data_sha256"),
            }
        )

    return {
        "candidates": candidates,
        "data_source": "support-pressure-analysis-system",
        "fallback_used": False,
        "summary_path": str(summary_path),
    }


def run_current_support_pressure(
    home: Path,
    out_dir: Path,
    *,
    symbols: list[str] | None = None,
    timeout: int = 600,
) -> dict[str, Any]:
    home = Path(home).resolve()
    out_dir = Path(out_dir).resolve()
    entry = (
        home
        / "skills"
        / "support-pressure-analysis-system"
        / "scripts"
        / "codex_entry.py"
    )
    if not entry.is_file():
        raise FileNotFoundError(entry)
    out_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(entry),
        "run",
        "--",
        "--mode",
        "pressure",
    ]
    if symbols:
        command.extend(["--symbols", ",".join(symbols)])
    command.extend(
        ["--limit", "0", "--out-dir", str(out_dir), "--run-id", out_dir.name]
    )
    completed = subprocess.run(
        command,
        cwd=str(home),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout)[-4000:]
        raise RuntimeError(
            f"support_pressure_canonical_run_failed:{completed.returncode}:{detail}"
        )
    summaries = list(out_dir.rglob("run_summary.json"))
    if len(summaries) != 1:
        raise RuntimeError(f"support_pressure_summary_count:{len(summaries)}")
    result = load_verified_support_candidates(summaries[0])
    result["canonical_entry"] = str(entry)
    return result
