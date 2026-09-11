from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]


def _load_collector():
    script = SKILL_ROOT / "scripts" / "collect_zt_lhb.py"
    spec = importlib.util.spec_from_file_location("limit_up_collector", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SnapshotFetcher:
    def __init__(self, snapshots):
        self.snapshots = list(snapshots)

    def __call__(self, *, date):
        assert date == "20260901"
        return self.snapshots.pop(0)


def _snapshot(*codes):
    return pd.DataFrame({"code": list(codes)})


def test_limit_up_pool_retries_duplicates_until_two_clean_snapshots_match():
    module = _load_collector()
    fetcher = SnapshotFetcher([
        _snapshot("000001", "000001"),
        _snapshot("000001", "000002"),
        _snapshot("000001", "000002"),
    ])

    result, diagnostics = module.fetch_stable_limit_up_pool(
        fetcher,
        "20260901",
        "code",
        max_attempts=3,
    )

    assert result["code"].tolist() == ["000001", "000002"]
    assert [item["status"] for item in diagnostics] == ["INCOMPLETE", "CLEAN", "CLEAN"]


def test_limit_up_pool_blocks_when_clean_snapshots_do_not_match():
    module = _load_collector()
    fetcher = SnapshotFetcher([
        _snapshot("000001", "000002"),
        _snapshot("000001", "000003"),
        _snapshot("000001", "000004"),
    ])

    with pytest.raises(RuntimeError, match="two matching duplicate-free snapshots"):
        module.fetch_stable_limit_up_pool(
            fetcher,
            "20260901",
            "code",
            max_attempts=3,
        )
