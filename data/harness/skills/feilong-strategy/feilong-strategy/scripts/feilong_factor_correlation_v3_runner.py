from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from feilong_deep_factor_research import load_verified_input
from feilong_factor_correlation_research import (
    add_context_features,
    build_daily_features,
    run_factor_correlation_research,
)
from feilong_resonance_exhaustive import normalize_bool_series


FORMULA_NAME = "飞龙在天"
TDX_ROOT = Path(r"C:\new_tdx_mock")


def _main_board(symbol: str) -> bool:
    code, _, market = str(symbol).partition(".")
    return (market == "SH" and code.startswith(("600", "601", "603", "605"))) or (
        market == "SZ" and code.startswith(("000", "001", "002", "003"))
    )


def run(*, events_csv: str | Path, source_manifest: str | Path, out_dir: str | Path) -> dict[str, Any]:
    events, _manifest, research = load_verified_input(events_csv, source_manifest)
    if research.get("formula", {}).get("name") != FORMULA_NAME:
        raise RuntimeError("current_formula_name_mismatch")
    primary = events.loc[
        normalize_bool_series(events["formula_signal"]).eq(True)
        & ~normalize_bool_series(events["one_price_board"]).fillna(False)
        & events["symbol"].astype(str).map(_main_board)
    ].copy()
    primary["first_board_date"] = primary["first_board_date"].astype(str).map(
        lambda value: re.sub(r"\D", "", value)[:8]
    )
    primary = primary.sort_values(["first_board_date", "symbol"], kind="mergesort").reset_index(drop=True)
    if len(primary) != 3728:
        raise RuntimeError(f"v3_primary_sample_drift:{len(primary)}")
    daily, evidence = build_daily_features(primary, TDX_ROOT)
    frame = add_context_features(primary, daily)
    return run_factor_correlation_research(
        primary=primary,
        tdx_root=TDX_ROOT,
        out_dir=Path(out_dir).resolve(),
        precomputed_frame=frame,
        precomputed_evidence=evidence,
    )

