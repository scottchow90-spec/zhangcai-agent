# Shortline Hotspot Scientific Forecast Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Subagents are not authorized for this execution.

**Goal:** Replace the disconnected market scan and industry-count workflow with a point-in-time, multi-horizon future-hotspot forecast that preserves provisional versus validated scientific status and passes canonical receipt authorization.

**Architecture:** The canonical facade remains unchanged. A new top-level forecast pipeline freezes local TDX data, derives auditable cross-sectional features, predicts H1/H2/H3 top-decile activity probabilities, applies bounded catalyst evidence, ranks leaders only inside forecast sectors, and validates one manifest-bound deliverable set. Current component snapshots remain untouched for provenance.

**Tech Stack:** Python 3, standard library, NumPy 2.5, pandas 3.0, scikit-learn 1.9, local TDX binary day files, unittest, canonical stock runtime v3.

**Repository Note:** `D:\C盘转移\日志\codex` is not a Git repository. Replace commit steps with exact backup manifests and SHA-256 readback checkpoints.

---

### Task 1: Exact Backup And RED Test Harness

**Files:**
- Create: `D:\C盘转移\日志\codex\backups\shortline-hotspot-scientific-forecast-20260823-<time>\backup_manifest.json`
- Create: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\tests\test_scientific_forecast.py`
- Modify later: `D:\C盘转移\日志\codex\skills\stock-unified\tests\test_merged_sentiment_hotspot_skills.py`

- [ ] Copy only the existing files that will be modified: `SKILL.md`, `references/workflow.md`, `scripts/canonical_business_adapter.py`, `scripts/legacy_codex_entry.py`, `scripts/merged_workflow.py`, the merged-skill regression test, and `stock_execution_contracts.json`.
- [ ] Record source path, backup path, size and SHA-256 for every copied file; read back the manifest and require all hashes to match before editing.
- [ ] Add failing tests that import the planned modules and assert the following public contracts:

```python
def test_requested_weekend_resolves_to_latest_tdx_trade_date():
    assert resolve_trade_date(date(2026, 8, 23), [date(2026, 8, 20), date(2026, 8, 21)]) == date(2026, 8, 21)

def test_mixed_strong_data_dates_block_snapshot():
    with self.assertRaises(SnapshotBlocked):
        validate_strong_data_dates(date(2026, 8, 21), {date(2026, 8, 20), date(2026, 8, 21)})

def test_provisional_catalyst_adjustment_is_clamped():
    assert apply_catalyst_adjustment(0.30, 0.80, "PROVISIONAL_FORECAST") == 0.40

def test_hard_fail_cannot_increase_probability():
    assert apply_catalyst_adjustment(0.30, 0.80, "PROVISIONAL_FORECAST", "HARD_FAIL") <= 0.30

def test_leaders_are_limited_to_forecast_sector_members():
    rows = rank_leaders(snapshot, forecasts)
    assert {row["sector"] for row in rows} <= {row["sector"] for row in forecasts}

def test_incomplete_manifest_is_not_clean():
    result = validate_delivery_manifest(incomplete_manifest, output_dir)
    assert result["status"] == "BLOCKED"
```

- [ ] Run `python -B tests\test_scientific_forecast.py` and confirm RED import or assertion failures.

### Task 2: Point-In-Time TDX Snapshot

**Files:**
- Create: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\point_in_time_snapshot.py`
- Test: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\tests\test_scientific_forecast.py`

- [ ] Implement immutable data classes and fail-closed exceptions:

```python
class SnapshotBlocked(RuntimeError):
    pass

@dataclass(frozen=True)
class DailyBar:
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    amount: float
    volume: int

def resolve_trade_date(requested: date, available: Sequence[date]) -> date:
    eligible = sorted(value for value in set(available) if value <= requested)
    if not eligible:
        raise SnapshotBlocked("no_trade_date_on_or_before_request")
    return eligible[-1]
```

- [ ] Parse TDX `.day` records without mutating TDX files; retain per-file path and SHA-256.
- [ ] Load the complete registered `blocknew` universe without filename-order truncation.
- [ ] Freeze sector membership and build `snapshot_id` from canonical JSON containing resolved date, cutoff, member codes, file hashes and coverage.
- [ ] Require exact resolved-date bars for all strong-data rows; sectors below 80% coverage or five valid members remain auditable exclusions.
- [ ] Run the point-in-time tests and confirm GREEN.

### Task 3: Market Features And Future Labels

**Files:**
- Create: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\market_features.py`
- Create: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\future_labels.py`
- Test: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\tests\test_scientific_forecast.py`

- [ ] Add RED tests proving feature cutoff precedes label windows, a zero-coverage row cannot rank, and H1/H2/H3 use distinct future slices.
- [ ] Implement market features from bars at or before the cutoff only: relative returns, trend slope, breadth, amount ratio, limit-up density, leader concentration, persistence, volatility, drawdown and coverage flags.
- [ ] Use deterministic cross-sectional percentile ranks with stable tie handling and explicit missing indicators.
- [ ] Implement future activity labels with frozen members and exact weights:

```python
LABEL_WEIGHTS = {
    "excess_return": 0.30,
    "breadth_improvement": 0.20,
    "activity_expansion": 0.20,
    "limit_leader_continuity": 0.20,
    "persistence": 0.10,
}
HORIZONS = {"H1": (1, 3), "H2": (4, 7), "H3": (8, 10)}
```

- [ ] Mark the top 10% of each date/horizon cross-section positive and retain the continuous activity score.
- [ ] Run feature and label tests and confirm GREEN.

### Task 4: Forecast Model And Walk-Forward Validation

**Files:**
- Create: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\forecast_model.py`
- Create: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\walk_forward_backtest.py`
- Test: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\tests\test_scientific_forecast.py`

- [ ] Add RED tests for date-grouped folds, 10-day embargo, train-only preprocessing, independent horizon models and probability bounds.
- [ ] Implement a transparent provisional model that emits future probabilities immediately and records fixed coefficients in the model card.
- [ ] Implement scikit-learn regularized logistic baseline, histogram gradient boosting challenger and validation-fold probability calibration.
- [ ] Implement expanding walk-forward splits with at least 252 train, 60 validation, 60 test dates and 10 embargo dates.
- [ ] Compute Precision@Top5, PR-AUC, Rank IC, Brier Skill Score, ECE, regime metrics and block-bootstrap confidence intervals.
- [ ] Grant `VALIDATED_FORECAST` only when every threshold in the approved design passes; otherwise emit `PROVISIONAL_FORECAST` or `DEGRADED_FORECAST` with explicit reasons.
- [ ] Serialize promoted model metadata and coefficients under the F-authoritative skill tree; do not promote a challenger that fails gates.
- [ ] Run model tests and confirm GREEN.

### Task 5: Bounded Catalyst Fusion And Candidate-Bound Leader Ranking

**Files:**
- Create: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\catalyst_features.py`
- Create: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\leader_ranker.py`
- Test: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\tests\test_scientific_forecast.py`

- [ ] Add RED tests for post-cutoff evidence rejection, source grading, 0.10 provisional adjustment cap, `HARD_FAIL` monotonic decrease and leader lineage.
- [ ] Validate each evidence row has `evidence_id`, sector, published time, collected time, source grade, novelty, directness, magnitude, pollution state and counter-evidence.
- [ ] Fuse catalysts only after the market probability is produced; use a zero adjustment when no admissible evidence exists.
- [ ] Rank leaders only from Top forecast sectors using contribution, relative strength, amount ratio, limit-up continuity, persistence, second-tier support, volatility and drawdown penalties.
- [ ] Attach `snapshot_id`, sector forecast probability, reasons, risks and invalidation fields to every leader row.
- [ ] Run catalyst and leader tests and confirm GREEN.

### Task 6: Forecast Gate, Artifacts And Orchestration

**Files:**
- Create: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\forecast_gate.py`
- Rewrite: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\merged_workflow.py`
- Modify: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\legacy_codex_entry.py`
- Test: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\tests\test_scientific_forecast.py`

- [ ] Add RED integration tests for explicit `--date`, one `snapshot_id`, required artifacts, stale dates, candidate lineage and manifest hash mismatch.
- [ ] Parse `all|hotspot|leader`, `--date YYYYMMDD`, optional evidence file, and canonical output root; `all` must accept an explicit date.
- [ ] Execute one continuous chain and write exactly these deliverables under the canonical run directory:

```text
forecast_snapshot.json
feature_snapshot.json
forecast_rank.csv
leader_rank.csv
evidence.json
model_card.json
backtest_report.json
audit.json
manifest.json
report.md
```

- [ ] Build the manifest after all non-manifest artifacts, include path, size and SHA-256, then read it back and validate every binding.
- [ ] Return one JSON object with `status`, `forecast_status`, `snapshot_id`, `resolved_trade_date`, `manifest_path` and explicit warnings.
- [ ] Make `legacy_codex_entry.py selftest` compile and require every new module while preserving component source-manifest verification.
- [ ] Run integration tests and confirm GREEN.

### Task 7: Canonical Adapter And Execution Contract

**Files:**
- Modify: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\canonical_business_adapter.py`
- Modify: `D:\C盘转移\日志\codex\skills\stock-unified\references\stock_execution_contracts.json`
- Modify: `D:\C盘转移\日志\codex\skills\stock-unified\tests\test_merged_sentiment_hotspot_skills.py`
- Test: `D:\C盘转移\日志\codex\skills\stock-unified\tests\test_contract_catalog_integrity.py`

- [ ] Add RED tests proving the adapter preserves `forecast_status`, a provisional forecast can be operationally complete without being mislabeled validated, and missing forecast artifacts block the receipt.
- [ ] Pass the canonical `{run_dir}\deliverables` path to the child through a dedicated environment variable that user arguments cannot override.
- [ ] Parse the single child JSON result and copy `forecast_status`, `snapshot_id`, `resolved_trade_date` and manifest path into `STOCK_CANONICAL_BUSINESS_RESULT_V1`.
- [ ] Extend contract required artifacts to all ten deliverables and require `forecast_status` plus absence of `requires_research_completion`.
- [ ] Add every new module, the approved design and workflow reference to `workflow_guard.required_bindings`; run contract synchronization so all paths and hashes are canonical F paths.
- [ ] Update merged-skill regression tests to check candidate lineage and business artifact semantics, not only component order.
- [ ] Run contract sync check and contract/merged tests until GREEN.

### Task 8: Skill Instructions, Full Verification And Authorized Run

**Files:**
- Modify: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\SKILL.md`
- Modify: `D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\references\workflow.md`
- Verify: all files above

- [ ] Replace the old disconnected-component description with the approved point-in-time forecast, validation states and artifact contract.
- [ ] Run skill quick validation, entry selftest, scientific forecast tests, merged-skill tests, contract integrity tests and global contract preflight tests.
- [ ] Run contract synchronization `--check` and require zero changes.
- [ ] Run canonical completion for the requested/current natural date; the workflow must resolve a valid local TDX trade date without controlling TDX.
- [ ] Extract the receipt and run both conclusion authorization and `report.md` artifact authorization.
- [ ] Read back `forecast_status`, resolved trade date, manifest hashes, Top forecasts and leader lineage.
- [ ] Compare all modified source hashes against the backup manifest and list only intentional changes; preserve all historical component snapshots.
- [ ] Report `VALIDATED_FORECAST`, `PROVISIONAL_FORECAST`, `DEGRADED_FORECAST` or `BLOCKED` exactly as authorized. Do not claim scientific validation unless the sample-out gates passed.
