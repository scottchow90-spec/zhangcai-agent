from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import json
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "business_entry.py"
CANONICAL_ADAPTER = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "canonical_business_adapter.py"
)
CONTRACTS = (
    Path(__file__).resolve().parents[2]
    / "stock-unified"
    / "references"
    / "stock_execution_contracts.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("buzhang_runtime_home_test", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_canonical_adapter():
    spec = importlib.util.spec_from_file_location("buzhang_canonical_adapter_test", CANONICAL_ADAPTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_home_is_derived_from_relocated_skill_directory(tmp_path: Path):
    module = load_module()
    relocated_skill = tmp_path / "Home" / "skills" / "buzhang-leader-mining"

    assert module.runtime_home(relocated_skill) == tmp_path / "Home"


def test_upstream_commands_use_merged_hotspot_owner_and_current_modes(tmp_path: Path):
    module = load_module()
    commands = module.build_upstream_commands("20260818", tmp_path)

    assert commands["shortline"][4:6] == ["hotspot", "--date"]
    assert "--manual-confirm" not in commands["shortline"]
    assert "--mode" not in commands["shortline"]
    assert commands["hotspot_leader"][4:6] == ["leader", "--date"]
    assert "--out" in commands["hotspot_leader"]
    assert "--out-dir" not in commands["hotspot_leader"]
    assert commands["hotspot_leader"][1] == commands["shortline"][1]
    assert commands["limitup"][commands["limitup"].index("--mode") + 1] == "daily"
    assert "hotspot-leader" not in commands["hotspot_leader"][1]


def test_nested_canonical_outputs_bind_real_manifest_and_leader_rank(tmp_path: Path):
    module = load_module()
    manifest = tmp_path / "shortline-run" / "deliverables" / "manifest.json"
    leader_rank = tmp_path / "leader-run" / "deliverables" / "leader_rank.csv"
    steps = {
        "shortline": {
            "stdout": json.dumps({
                "status": "CLEAN_PASS",
                "manifest_path": str(manifest),
                "artifacts": {"deliverables": {"leader_rank.csv": "unused.csv"}},
            })
        },
        "hotspot_leader": {
            "stdout": json.dumps({
                "status": "CLEAN_PASS",
                "manifest_path": "unused.json",
                "artifacts": {"deliverables": {"leader_rank.csv": str(leader_rank)}},
            })
        },
    }

    paths = module.resolve_shortline_artifacts(steps)

    assert paths["manifest"] == manifest
    assert paths["leader_rank"] == leader_rank


def test_canonical_adapter_forwards_research_evidence_arguments(tmp_path: Path):
    module = load_canonical_adapter()
    evidence = tmp_path / "candidate_research.json"

    command = module.business_command(
        tmp_path / "run",
        ["--", "--date", "20260824", "--manual-confirm", "--research-evidence", str(evidence)],
    )

    assert command[-7:] == [
        "run",
        "--",
        "--date",
        "20260824",
        "--manual-confirm",
        "--research-evidence",
        str(evidence),
    ]


def test_canonical_adapter_parser_keeps_runtime_appended_business_args(tmp_path: Path):
    module = load_canonical_adapter()
    evidence = tmp_path / "candidate_research.json"

    args, business_args = module.parse_arguments([
        "--run-dir",
        str(tmp_path / "run"),
        "--timeout",
        "300",
        "--date",
        "20260824",
        "--manual-confirm",
        "--research-evidence",
        str(evidence),
    ])

    assert args.timeout == 300
    assert business_args == [
        "--date",
        "20260824",
        "--manual-confirm",
        "--research-evidence",
        str(evidence),
    ]


def test_contract_binds_the_real_nested_business_entry_chain():
    payload = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    contract = next(
        row for row in payload["contracts"]
        if row["skill_id"] == "buzhang-leader-mining"
    )
    assert {
        "scripts/audit_entry.py",
        "scripts/business_entry.py",
    }.issubset(set(contract["workflow_guard"]["required_bindings"]))
