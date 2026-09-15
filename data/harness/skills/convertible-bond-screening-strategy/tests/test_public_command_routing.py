from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts" / "codex_entry.py"
ADAPTER = ROOT / "scripts" / "canonical_business_adapter.py"
RUNTIME_UTILS = ROOT / "scripts" / "runtime_utils.py"
ANNOUNCEMENT_FETCHER = ROOT / "scripts" / "fetch_early_redemption_announcements.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def shared_announcement_fixture(fetcher):
    cutoff, _cutoff_date, as_of = fetcher._parse_cutoff("20260821")
    bonds = [
        fetcher._normalize_bond(
            {
                "symbol": "123001.SZ",
                "bond_code": "123001",
                "bond_name": "测试转债",
                "underlying_code": "000001",
                "underlying_symbol": "000001.SZ",
                "listing_date": "2020-01-02",
            },
            0,
        )
    ]
    records = [
        {
            "symbol": "123001.SZ",
            "bond_code": "123001",
            "bond_name": "测试转债",
            "underlying_code": "000001",
            "underlying_symbol": "000001.SZ",
            "listing_date": "2020-01-02",
            "listing_date_source": "universe",
            "org_id": "gssz0000001",
            "early_redemption_status": "NO_MATCH_AS_OF_CUTOFF",
            "query_complete": True,
            "pages_fetched": 1,
            "total_announcements": 0,
            "announcements_fetched": 0,
            "exact_name_match_count": 0,
            "exclusion_match_count": 0,
            "non_exclusion_match_count": 0,
            "request_coverage": {"complete": True, "pages": []},
            "request_diagnostics": [],
            "announcements": [],
            "errors": [],
        }
    ]
    payload = {
        "schema": fetcher.SCHEMA,
        "status": "PASS",
        "run_id": "capture-run",
        "cutoff": cutoff,
        "as_of": as_of.isoformat(),
        "generated_at": "2026-08-23T20:00:00+08:00",
        "source": {"provider": "CNINFO"},
        "universe_source": {"mode": "fixture"},
        "universe_count": 1,
        "record_count": 1,
        "announced_count": 0,
        "no_match_count": 1,
        "unverified_count": 0,
        "current_universe_complete": True,
        "coverage": {
            "requested_count": 1,
            "completed_count": 1,
            "pages_fetched": 1,
            "announcements_fetched": 0,
            "complete": True,
        },
        "records": records,
        "errors": [],
        "records_sha256": fetcher._sha256_bytes(fetcher._canonical_bytes(records)),
    }
    return cutoff, as_of, bonds, records, payload


def test_business_payload_quantization_removes_only_float_runtime_tails() -> None:
    runtime_utils = load_module(RUNTIME_UTILS, "convertible_runtime_utils_quantization")

    python313_value = {"score": 1.0, "heat": 57.00000000000001}
    python311_value = {"score": 0.9999999999999999, "heat": 56.99999999999999}
    changed_business_value = {"score": 1.000000001, "heat": 57.0}

    canonical313 = runtime_utils.canonicalize_business_payload(python313_value)
    canonical311 = runtime_utils.canonicalize_business_payload(python311_value)
    changed = runtime_utils.canonicalize_business_payload(changed_business_value)

    assert json.dumps(canonical313, sort_keys=True) == json.dumps(
        canonical311,
        sort_keys=True,
    )
    assert canonical313 != changed


def test_business_score_total_sums_quantized_components_deterministically() -> None:
    runtime_utils = load_module(RUNTIME_UTILS, "convertible_runtime_utils_score_sum")
    earned_scores = [
        1.199764978787,
        4.047787560513,
        0.0,
        6.445242,
        0.0,
        3.0,
        15.0,
        0.427958677686,
        0.106666666667,
        3.531391251132,
    ]

    assert runtime_utils.canonical_business_sum(earned_scores) == 33.758811134785
    assert runtime_utils.canonical_business_sum(reversed(earned_scores)) == 33.758811134785


def test_shared_announcement_snapshot_is_rebound_without_mutating_source(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    fetcher = load_module(
        ANNOUNCEMENT_FETCHER,
        "convertible_shared_announcement_snapshot",
    )
    cutoff, as_of, bonds, records, source_payload = shared_announcement_fixture(
        fetcher
    )
    source_path = tmp_path / "early_redemption_announcements.json"
    source_path.write_text(
        json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    source_bytes = source_path.read_bytes()

    rebound = fetcher._load_shared_readonly_snapshot(
        source_path,
        bonds=bonds,
        run_id="production-run",
        cutoff=cutoff,
        as_of=as_of,
    )

    assert rebound["status"] == "PASS"
    assert rebound["run_id"] == "production-run"
    assert rebound["records"] == records
    assert rebound["records_sha256"] == source_payload["records_sha256"]
    assert rebound["source"]["input_mode"] == "shared_readonly_snapshot"
    assert rebound["source"]["input_snapshot"]["sha256"] == fetcher._sha256_bytes(
        source_bytes
    )
    assert source_path.read_bytes() == source_bytes


def test_fetcher_prefers_shared_readonly_snapshot_over_network(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    fetcher = load_module(
        ANNOUNCEMENT_FETCHER,
        "convertible_shared_announcement_main",
    )
    cutoff, _as_of, bonds, _records, source_payload = shared_announcement_fixture(
        fetcher
    )
    shared_root = tmp_path / "public"
    shared_path = (
        shared_root
        / "convertible-bond-screening-strategy"
        / "early_redemption_announcements.json"
    )
    shared_path.parent.mkdir(parents=True)
    shared_path.write_text(
        json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "output.json"
    monkeypatch.setenv("CODEX_PUBLIC_READONLY_SNAPSHOT_DIR", str(shared_root))
    monkeypatch.setattr(
        fetcher,
        "_load_universe",
        lambda _path, _cutoff: (bonds, {"mode": "fixture"}, True),
    )
    monkeypatch.setattr(
        fetcher,
        "_build_snapshot",
        lambda *_args, **_kwargs: pytest.fail("network snapshot builder was called"),
    )

    returncode = fetcher.main(
        [
            "--output",
            str(output),
            "--run-id",
            "production-run",
            "--cutoff",
            cutoff,
        ]
    )

    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert returncode == 0
    assert persisted["status"] == "PASS"
    assert persisted["run_id"] == "production-run"
    assert persisted["source"]["input_mode"] == "shared_readonly_snapshot"


def test_shared_announcement_snapshot_rejects_unknown_business_status(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    fetcher = load_module(
        ANNOUNCEMENT_FETCHER,
        "convertible_shared_announcement_unknown_status",
    )
    cutoff, as_of, bonds, records, payload = shared_announcement_fixture(fetcher)
    records[0]["early_redemption_status"] = "UNKNOWN_BUT_MARKED_COMPLETE"
    payload["no_match_count"] = 0
    payload["records_sha256"] = fetcher._sha256_bytes(fetcher._canonical_bytes(records))
    source_path = tmp_path / "early_redemption_announcements.json"
    source_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(fetcher.SnapshotError, match="record_status_invalid"):
        fetcher._load_shared_readonly_snapshot(
            source_path,
            bonds=bonds,
            run_id="production-run",
            cutoff=cutoff,
            as_of=as_of,
        )


@pytest.mark.parametrize(
    ("public_command", "business_action"),
    [
        ("selftest", "business-selftest"),
        ("status", "status"),
        ("deliver", "deliver"),
    ],
)
def test_special_public_commands_stay_inside_canonical_runtime(
    monkeypatch,
    public_command: str,
    business_action: str,
):
    entry = load_module(ENTRY, f"convertible_entry_{public_command}")
    calls: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(
        entry,
        "canonical_run",
        lambda entry_file, extra: calls.append((entry_file, extra)) or 17,
    )
    monkeypatch.setattr(sys, "argv", [str(ENTRY), public_command])

    assert entry.main() == 17
    assert calls == [(str(ENTRY), [business_action])]


def test_info_remains_on_the_canonical_facade(monkeypatch):
    entry = load_module(ENTRY, "convertible_entry_info")
    calls: list[str] = []
    monkeypatch.setattr(
        entry,
        "facade_main",
        lambda entry_file: calls.append(entry_file) or 19,
    )
    monkeypatch.setattr(sys, "argv", [str(ENTRY), "info"])

    assert entry.main() == 19
    assert calls == [str(ENTRY)]


@pytest.mark.parametrize(
    ("business_action", "legacy_action"),
    [
        ("business-selftest", "selftest"),
        ("status", "status"),
        ("deliver", "deliver"),
    ],
)
def test_adapter_maps_only_the_declared_business_actions(
    business_action: str,
    legacy_action: str,
    tmp_path: Path,
):
    adapter = load_module(ADAPTER, f"convertible_adapter_{business_action}")

    command = adapter.business_command(tmp_path, business_action)

    assert command == [
        sys.executable,
        str(ROOT / "scripts" / "legacy_codex_entry.py"),
        legacy_action,
    ]


def test_adapter_rejects_an_undeclared_business_action(tmp_path: Path):
    adapter = load_module(ADAPTER, "convertible_adapter_reject")

    with pytest.raises(ValueError, match="unsupported_business_action"):
        adapter.business_command(tmp_path, "inspect")
