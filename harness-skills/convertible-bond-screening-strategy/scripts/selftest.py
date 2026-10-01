from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import contextlib
import hashlib
import importlib.util
import inspect
import io
import json
import os
import py_compile
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime_utils import RunInProgressError, RunLock, atomic_write_json, run_process_tree


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
RUN = (Path(__import__("os").environ["ONESTOCK_STOCK_DATA_ROOT"]) / "convertible-bond-screening-strategy" if __import__("os").environ.get("ONESTOCK_STOCK_DATA_ROOT") else ROOT / "run")
SKILLS_ROOT = ROOT.parent
APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(APP_SCRIPTS))
from tdx_path_config import resolve_tdx_root

TDX_ROOT = resolve_tdx_root()
TDX_HUB_PATH = SKILLS_ROOT / "tdx-local-hub" / "scripts" / "tdx_hub.py"
DEPENDENCIES = (
    "stock-hard-gate",
    "tdx-local-hub",
    "golden-ignition",
    "feilong-strategy",
    "youzi-capital-monitoring",
    "big-bull-analysis-scoring-system",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "size_bytes": path.stat().st_size, "sha256": sha256(path)}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dependency_selftests() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for skill in DEPENDENCIES:
        entry = SKILLS_ROOT / skill / "scripts" / "codex_entry.py"
        if not entry.is_file():
            rows.append({"skill": skill, "status": "FAIL", "reason": "entry_missing", "entry": str(entry)})
            continue
        result = run_process_tree(
            [sys.executable, str(entry), "selftest"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            check=False,
        )
        accepted_status = any(
            token in result.stdout
            for token in (
                '"status": "PASS"',
                '"status":"PASS"',
                '"status": "CLEAN_PASS"',
                '"status":"CLEAN_PASS"',
            )
        )
        rows.append({
            "skill": skill,
            "status": "PASS" if result.returncode == 0 and accepted_status else "FAIL",
            "returncode": result.returncode,
            "entry": artifact(entry),
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-2000:],
        })
    return rows


def compile_scripts(script_paths: list[Path], compile_root: Path) -> list[str]:
    compile_root.mkdir(parents=True, exist_ok=True)
    compile_errors: list[str] = []
    for path in script_paths:
        cache_name = f"{path.stem}-{hashlib.sha256(str(path).encode('utf-8')).hexdigest()[:16]}.pyc"
        try:
            py_compile.compile(
                str(path),
                cfile=str(compile_root / cache_name),
                doraise=True,
            )
        except py_compile.PyCompileError as exc:
            compile_errors.append(f"{path.name}:{exc.msg}")
    return compile_errors


def main() -> int:
    parser = argparse.ArgumentParser(description="可转债筛选策略自检")
    parser.add_argument("--output", type=Path, default=RUN / "selftest.json")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    run_id = args.run_id or f"selftest-{uuid.uuid4().hex}"

    script_paths = sorted(SCRIPTS.glob("*.py"))
    RUN.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".selftest-compile-", dir=RUN) as compile_directory:
        compile_errors = compile_scripts(script_paths, Path(compile_directory))

    scanner = load_module(SCRIPTS / "run_convertible_bond_screening.py", "cb_screening_selftest_scanner")
    delivery_contract = load_module(
        SCRIPTS / "validate_delivery_contract.py",
        "cb_screening_selftest_delivery_contract",
    )
    entry_module = load_module(SCRIPTS / "legacy_codex_entry.py", "cb_screening_selftest_entry")
    heat_verifier = load_module(
        SCRIPTS / "independent_heat_verifier.py", "cb_screening_selftest_heat_verifier"
    )
    main_verifier = load_module(
        SCRIPTS / "verify_convertible_bond_screening.py", "cb_screening_selftest_main_verifier"
    )
    top1_validator = load_module(
        SCRIPTS / "validate_top1_fixed_skills.py", "cb_screening_selftest_top1_validator"
    )
    hub = load_module(TDX_HUB_PATH, "cb_screening_selftest_tdx_hub")
    expected_weights = dict(delivery_contract.SCORE_CRITERIA)
    weights = {item["id"]: float(item["weight"]) for item in scanner.SCORE_CRITERIA}

    benchmark_rows = scanner.read_day_records(hub, "999999.SH", 30)
    if not benchmark_rows:
        raise RuntimeError("cannot resolve latest local benchmark close for selftest")
    formula_cutoff = str(benchmark_rows[-1]["date"])
    benchmark_dates = scanner.benchmark_calendar(hub, formula_cutoff)
    benchmark_history_dates = [
        str(row["date"])
        for row in benchmark_rows
        if str(row["date"]) <= formula_cutoff
    ]
    if len(benchmark_dates) != 11 or len(benchmark_history_dates) < 12:
        raise RuntimeError("benchmark history cannot construct exact and stale SCR windows")
    required_scr_dates = benchmark_dates[-6:]

    bonds, _tnf, master_diagnostics = scanner.parse_bonds(formula_cutoff)
    sample = next(
        (
            bond
            for bond in bonds
            if hub.day_path(bond["symbol"]).is_file() and hub.day_path(bond["underlying_symbol"]).is_file()
        ),
        None,
    )
    if sample is None:
        raise RuntimeError("no current convertible-bond sample has both bond and stock day files")
    bond_symbol = sample["symbol"]
    stock_symbol = sample["underlying_symbol"]
    bond_path = hub.day_path(bond_symbol)
    stock_path = hub.day_path(stock_symbol)
    bond_chunk = bond_path.read_bytes()[-hub.DAY_RECORD.size:]
    stock_chunk = stock_path.read_bytes()[-hub.DAY_RECORD.size:]
    bond_raw_close = int.from_bytes(bond_chunk[16:20], "little")
    stock_raw_close = int.from_bytes(stock_chunk[16:20], "little")
    bond_parsed = hub.parse_day_record(bond_chunk, hub.day_price_divisor(bond_symbol))
    stock_parsed = hub.parse_day_record(stock_chunk, hub.day_price_divisor(stock_symbol))

    required_tdx_files = (
        TDX_ROOT / "T0002" / "hq_cache" / "speckzzdata.txt",
        TDX_ROOT / "T0002" / "hq_cache" / "shs.tnf",
        TDX_ROOT / "T0002" / "hq_cache" / "szs.tnf",
        TDX_ROOT / "T0002" / "hq_cache" / "tdxhy.cfg",
        TDX_ROOT / "T0002" / "hq_cache" / "tdxzs3.cfg",
        TDX_ROOT / "T0002" / "hq_cache" / "infoharbor_block.dat",
        TDX_ROOT / "PYPlugins" / "user" / "tqcenter.py",
        TDX_ROOT / "T0002" / "PriGS.dat",
    )
    tq_user = TDX_ROOT / "PYPlugins" / "user"
    if str(tq_user) not in sys.path:
        sys.path.insert(0, str(tq_user))
    golden_text = (SKILLS_ROOT / "golden-ignition" / "SKILL.md").read_text(encoding="utf-8-sig")
    dependency_runs = dependency_selftests()

    retry_contract_run_id = "selftest-retry-contract"

    def retry_event(script_name: str, schema: str, **overrides: Any) -> dict[str, Any]:
        event = {
            "schema": schema,
            "status": "FAIL",
            "failure_code": entry_module.TDX_DAY_UPDATE_RACE,
            "retryable": True,
            "script": str((SCRIPTS / script_name).resolve()),
            "run_id": retry_contract_run_id,
            "attempt": 2,
            "error": f"{entry_module.TDX_DAY_UPDATE_RACE}:source_changed:count=1",
            "mismatch_count": 1,
            "mismatch_paths": [str((TDX_ROOT / "vipdoc" / "sh" / "lday" / "sh999999.day").resolve())],
        }
        event.update(overrides)
        return event

    def child_failure(
        script_name: str,
        event: dict[str, Any] | str,
        *,
        returncode: int = 3,
    ) -> Any:
        stderr = event if isinstance(event, str) else json.dumps(event, ensure_ascii=False)
        return entry_module.ChildInvocationError(script_name, returncode, "", stderr, 0.01)

    retry_scan_event = retry_event(
        "run_convertible_bond_screening.py",
        "CONVERTIBLE-BOND-SCAN-FAILURE-1",
    )
    retry_verify_event = retry_event(
        "verify_convertible_bond_screening.py",
        "CONVERTIBLE-BOND-VERIFY-FAILURE-1",
    )
    retry_classifier_exact_scan = entry_module.retryable_day_race_event(
        child_failure("run_convertible_bond_screening.py", retry_scan_event),
        run_id=retry_contract_run_id,
        attempt=2,
    )
    retry_classifier_exact_verify = entry_module.retryable_day_race_event(
        child_failure("verify_convertible_bond_screening.py", retry_verify_event),
        run_id=retry_contract_run_id,
        attempt=2,
    )
    retry_classifier_wrong_binding_rejected = all(
        entry_module.retryable_day_race_event(
            child_failure(
                "run_convertible_bond_screening.py",
                retry_event(
                    "run_convertible_bond_screening.py",
                    "CONVERTIBLE-BOND-SCAN-FAILURE-1",
                    **override,
                ),
            ),
            run_id=retry_contract_run_id,
            attempt=2,
        ) is None
        for override in (
            {"run_id": "wrong-run"},
            {"attempt": 1},
            {"script": str((SCRIPTS / "verify_convertible_bond_screening.py").resolve())},
        )
    )
    retry_classifier_unstructured_rejected = bool(
        entry_module.retryable_day_race_event(
            child_failure("run_convertible_bond_screening.py", "TDX_DAY_UPDATE_RACE", returncode=3),
            run_id=retry_contract_run_id,
            attempt=2,
        ) is None
        and entry_module.retryable_day_race_event(
            child_failure("run_convertible_bond_screening.py", retry_scan_event, returncode=2),
            run_id=retry_contract_run_id,
            attempt=2,
        ) is None
    )
    retry_classifier_malformed_diagnostics_rejected = all(
        entry_module.retryable_day_race_event(
            child_failure(
                "run_convertible_bond_screening.py",
                retry_event(
                    "run_convertible_bond_screening.py",
                    "CONVERTIBLE-BOND-SCAN-FAILURE-1",
                    **override,
                ),
            ),
            run_id=retry_contract_run_id,
            attempt=2,
        ) is None
        for override in (
            {"mismatch_count": 0, "mismatch_paths": []},
            {"mismatch_count": 2, "mismatch_paths": ["one"]},
            {"error": "unstructured-race"},
        )
    )

    truncated_tnf_name = bytes.fromhex("c9cfd6a4d6d0c5cc455446d2d7b7bdb4")
    truncated_tnf_expected = truncated_tnf_name[:-1].decode("gb18030", errors="strict")
    scanner_accepts_tnf_tail_truncation = (
        scanner.decode_tnf_name(truncated_tnf_name) == truncated_tnf_expected
    )
    verifier_accepts_tnf_tail_truncation = (
        main_verifier.decode_tnf_name(truncated_tnf_name) == truncated_tnf_expected
    )
    invalid_tnf_name = b"A" * 14 + b"\xff\xff"
    tnf_internal_corruption_rejected = True
    for decoder in (scanner.decode_tnf_name, main_verifier.decode_tnf_name):
        try:
            decoder(invalid_tnf_name)
            tnf_internal_corruption_rejected = False
        except ValueError:
            pass

    with tempfile.TemporaryDirectory(prefix="cb-screening-selftest-") as temporary_dir:
        temporary_root = Path(temporary_dir)
        atomic_path = temporary_root / "atomic.json"
        atomic_write_json(atomic_path, {"run_id": run_id, "value": 1})
        atomic_write_json(atomic_path, {"run_id": run_id, "value": 2})
        atomic_replace_exact = json.loads(atomic_path.read_text(encoding="utf-8")) == {
            "run_id": run_id,
            "value": 2,
        }
        publication_source = temporary_root / "generation-summary.json"
        publication_target = temporary_root / "latest-summary.json"
        publication_payload = {
            "status": "PASS",
            "run_id": run_id,
            "market_attempt": 1,
        }
        publication_bytes = (
            json.dumps(publication_payload, ensure_ascii=False, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        publication_source.write_bytes(publication_bytes)
        original_latest_summary = entry_module.LATEST_SUMMARY
        entry_module.LATEST_SUMMARY = publication_target
        try:
            publication_evidence = entry_module.publish_latest_summary(
                publication_source,
                run_id=run_id,
                market_attempt=1,
            )
        finally:
            entry_module.LATEST_SUMMARY = original_latest_summary
        publication_bytes_match = publication_target.read_bytes() == publication_bytes
        publication_size_match = (
            publication_target.stat().st_size == publication_source.stat().st_size
            == publication_evidence.get("size_bytes")
        )
        publication_sha256_match = (
            sha256(publication_target) == sha256(publication_source)
            == publication_evidence.get("sha256")
        )
        publication_json_binding_match = (
            json.loads(publication_target.read_text(encoding="utf-8"))
            == publication_payload
            and publication_evidence.get("run_id") == run_id
            and publication_evidence.get("market_attempt") == 1
        )

        failure_target = temporary_root / "failed-latest-summary.json"
        original_latest_summary = entry_module.LATEST_SUMMARY
        original_atomic_write_bytes = entry_module.atomic_write_bytes

        def fail_atomic_write(_path: Path, _data: bytes) -> None:
            raise OSError("fixture atomic publication failure")

        entry_module.LATEST_SUMMARY = failure_target
        entry_module.atomic_write_bytes = fail_atomic_write
        try:
            try:
                entry_module.publish_latest_summary(
                    publication_source,
                    run_id=run_id,
                    market_attempt=1,
                )
                publication_failure_rejected = False
            except OSError:
                publication_failure_rejected = True
        finally:
            entry_module.atomic_write_bytes = original_atomic_write_bytes
            entry_module.LATEST_SUMMARY = original_latest_summary
        publication_failure_target_absent = not failure_target.exists()

        lock_path = temporary_root / ".run.lock"
        lock_rejects_concurrent = False
        with RunLock(lock_path):
            try:
                with RunLock(lock_path):
                    pass
            except RunInProgressError:
                lock_rejects_concurrent = True
        try:
            with RunLock(lock_path):
                lock_recovers_after_release = True
        except RunInProgressError:
            lock_recovers_after_release = False

        malformed_day_path = temporary_root / "vipdoc" / "sh" / "lday" / "sh600000.day"
        malformed_day_path.parent.mkdir(parents=True, exist_ok=True)
        malformed_day_path.write_bytes(b"invalid-layout")
        try:
            heat_verifier._read_day_records(temporary_root, "600000")
            malformed_day_rejected = False
        except ValueError:
            malformed_day_rejected = True

        empty_day_path = temporary_root / "vipdoc" / "sh" / "lday" / "sh600001.day"
        empty_day_path.write_bytes(b"")
        try:
            heat_verifier._read_day_records(temporary_root, "600001")
            empty_day_rejected = False
        except ValueError:
            empty_day_rejected = True

        prior_tdx_root = os.environ.get("TDX_ROOT")
        os.environ["TDX_ROOT"] = str(temporary_root)
        try:
            override_scanner = load_module(
                SCRIPTS / "run_convertible_bond_screening.py",
                "cb_screening_selftest_override_scanner",
            )
        finally:
            if prior_tdx_root is None:
                os.environ.pop("TDX_ROOT", None)
            else:
                os.environ["TDX_ROOT"] = prior_tdx_root
        scanner_ignores_tdx_root_environment = override_scanner.TDX_ROOT == TDX_ROOT
        scanner_skill_root_is_self_anchored = override_scanner.SKILL_ROOT == ROOT
        scanner_skills_root_is_self_anchored = override_scanner.SKILLS_ROOT == SKILLS_ROOT

        invalid_text_path = temporary_root / "invalid-gb18030.txt"
        invalid_text_path.write_bytes(b"\x81")
        try:
            heat_verifier._read_strict_text(invalid_text_path, "gb18030")
            invalid_text_rejected = False
        except ValueError:
            invalid_text_rejected = True

        empty_result_path = temporary_root / "empty-result.json"
        atomic_write_json(
            empty_result_path,
            {
                "status": "PASS",
                "schema": heat_verifier.EXPECTED_PRODUCTION_SCHEMA,
                "run_id": "empty-must-fail",
                "all_results": [],
                "ranking_top10": [],
                "universe_count": 0,
                "analyzed_count": 0,
                "ranked_count": 0,
                "score_model": {},
                "source_files": {},
            },
        )
        empty_result_report = heat_verifier.compare_latest_result(empty_result_path)
        alternate_root_report = heat_verifier.compare_latest_result(
            empty_result_path, tdx_root=temporary_root
        )

        redemption_bonds = [
            {"symbol": "110001.SH"},
            {"symbol": "123001.SZ"},
            {"symbol": "113001.SH"},
        ]
        redemption_records = [
            {
                "symbol": "110001.SH",
                "early_redemption_status": "NO_MATCH_AS_OF_CUTOFF",
            },
            {
                "symbol": "123001.SZ",
                "early_redemption_status": "ANNOUNCED_EARLY_REDEMPTION",
            },
            {
                "symbol": "113001.SH",
                "early_redemption_status": "UNVERIFIED",
            },
        ]
        redemption_snapshot_payload = {
            "schema": scanner.EARLY_REDEMPTION_SCHEMA,
            "status": "PASS",
            "run_id": run_id,
            "cutoff_trade_date": formula_cutoff,
            "current_universe_complete": True,
            "coverage": {"record_count": len(redemption_records)},
            "records": redemption_records,
        }
        redemption_snapshot_path = temporary_root / "redemption-announcements.json"
        atomic_write_json(redemption_snapshot_path, redemption_snapshot_payload)
        redemption_snapshot_size = redemption_snapshot_path.stat().st_size
        redemption_snapshot_sha256 = sha256(redemption_snapshot_path)
        loaded_redemption_records, loaded_redemption_meta = scanner.load_early_redemption_snapshot(
            redemption_snapshot_path.resolve(),
            run_id=run_id,
            cutoff=formula_cutoff,
            bonds=redemption_bonds,
        )
        verifier_redemption_map, verifier_redemption_map_well_formed = (
            main_verifier._redemption_record_map(redemption_snapshot_payload)
        )

        redemption_run_binding_rejected = False
        try:
            scanner.load_early_redemption_snapshot(
                redemption_snapshot_path.resolve(),
                run_id=f"{run_id}-wrong",
                cutoff=formula_cutoff,
                bonds=redemption_bonds,
            )
        except RuntimeError as exc:
            redemption_run_binding_rejected = "run_id mismatch" in str(exc)

        incomplete_redemption_path = temporary_root / "redemption-incomplete.json"
        atomic_write_json(
            incomplete_redemption_path,
            {
                **redemption_snapshot_payload,
                "coverage": {"record_count": len(redemption_records) - 1},
                "records": redemption_records[:-1],
            },
        )
        redemption_universe_incomplete_rejected = False
        try:
            scanner.load_early_redemption_snapshot(
                incomplete_redemption_path,
                run_id=run_id,
                cutoff=formula_cutoff,
                bonds=redemption_bonds,
            )
        except RuntimeError as exc:
            redemption_universe_incomplete_rejected = "universe incomplete" in str(exc)

        invalid_redemption_status_path = temporary_root / "redemption-invalid-status.json"
        atomic_write_json(
            invalid_redemption_status_path,
            {
                **redemption_snapshot_payload,
                "records": [
                    *redemption_records[:-1],
                    {
                        "symbol": "113001.SH",
                        "early_redemption_status": "UNKNOWN",
                    },
                ],
            },
        )
        redemption_invalid_status_rejected = False
        try:
            scanner.load_early_redemption_snapshot(
                invalid_redemption_status_path,
                run_id=run_id,
                cutoff=formula_cutoff,
                bonds=redemption_bonds,
            )
        except RuntimeError as exc:
            redemption_invalid_status_rejected = "invalid early-redemption status" in str(exc)

        hard_master = {"name": "普通转债"}
        hard_local = {
            "daily_return_pct": 0.0,
            "bond_volume_ratio_5d": 1.0,
            "turnover_5d_pct": 0.0,
            "bond_close": 100.0,
        }
        hard_scr = {"scr90_change_1d_pp": 0.0}
        hard_baseline = main_verifier._expected_hard_exclusion_reasons(
            hard_master, hard_local, hard_scr, "NO_MATCH_AS_OF_CUTOFF"
        )
        hard_z_prefix = main_verifier._expected_hard_exclusion_reasons(
            {"name": " z测试转债"}, hard_local, hard_scr, "NO_MATCH_AS_OF_CUTOFF"
        )
        hard_daily_ratio_boundary = main_verifier._expected_hard_exclusion_reasons(
            hard_master,
            {**hard_local, "daily_return_pct": 10.0, "bond_volume_ratio_5d": 4.0},
            hard_scr,
            "NO_MATCH_AS_OF_CUTOFF",
        )
        hard_daily_gain_boundary = main_verifier._expected_hard_exclusion_reasons(
            hard_master,
            {**hard_local, "daily_return_pct": 9.999999, "bond_volume_ratio_5d": 4.000001},
            hard_scr,
            "NO_MATCH_AS_OF_CUTOFF",
        )
        hard_daily_triggered = main_verifier._expected_hard_exclusion_reasons(
            hard_master,
            {**hard_local, "daily_return_pct": 10.0, "bond_volume_ratio_5d": 4.000001},
            hard_scr,
            "NO_MATCH_AS_OF_CUTOFF",
        )
        hard_scr90_zero = main_verifier._expected_hard_exclusion_reasons(
            hard_master, hard_local, {"scr90_change_1d_pp": 0.0}, "NO_MATCH_AS_OF_CUTOFF"
        )
        hard_scr90_positive = main_verifier._expected_hard_exclusion_reasons(
            hard_master, hard_local, {"scr90_change_1d_pp": 0.000001}, "NO_MATCH_AS_OF_CUTOFF"
        )
        hard_scr90_unavailable = main_verifier._expected_hard_exclusion_reasons(
            hard_master, hard_local, {"scr90_change_1d_pp": None}, "NO_MATCH_AS_OF_CUTOFF"
        )
        hard_turnover_boundary = main_verifier._expected_hard_exclusion_reasons(
            hard_master,
            {**hard_local, "turnover_5d_pct": 1000.0},
            hard_scr,
            "NO_MATCH_AS_OF_CUTOFF",
        )
        hard_turnover_triggered = main_verifier._expected_hard_exclusion_reasons(
            hard_master,
            {**hard_local, "turnover_5d_pct": 1000.000001},
            hard_scr,
            "NO_MATCH_AS_OF_CUTOFF",
        )
        hard_price_boundary = main_verifier._expected_hard_exclusion_reasons(
            hard_master,
            {**hard_local, "bond_close": 350.0},
            hard_scr,
            "NO_MATCH_AS_OF_CUTOFF",
        )
        hard_price_triggered = main_verifier._expected_hard_exclusion_reasons(
            hard_master,
            {**hard_local, "bond_close": 350.000001},
            hard_scr,
            "NO_MATCH_AS_OF_CUTOFF",
        )
        hard_announced = main_verifier._expected_hard_exclusion_reasons(
            hard_master, hard_local, hard_scr, "ANNOUNCED_EARLY_REDEMPTION"
        )
        hard_no_match = main_verifier._expected_hard_exclusion_reasons(
            hard_master, hard_local, hard_scr, "NO_MATCH_AS_OF_CUTOFF"
        )
        hard_unverified = main_verifier._expected_hard_exclusion_reasons(
            hard_master, hard_local, hard_scr, "UNVERIFIED"
        )

        dual_pool_eligible = {
            "symbol": "110001.SH",
            "rank": 1,
            "hard_exclusion_pass": True,
            "hard_exclusion_reasons": [],
        }
        dual_pool_excluded = {
            "symbol": "123001.SZ",
            "rank": None,
            "hard_exclusion_pass": False,
            "hard_exclusion_reasons": ["bond_close_gt_350"],
        }
        dual_pool_fixture = {
            "status": "PASS",
            "schema": heat_verifier.EXPECTED_PRODUCTION_SCHEMA,
            "run_id": run_id,
            "cutoff_trade_date": formula_cutoff,
            "source_binding_mode": heat_verifier.EXPECTED_SOURCE_BINDING_MODE,
            "day_input_binding_mode": heat_verifier.DAY_INPUT_BINDING_MODE,
            "all_results": [dual_pool_eligible],
            "hard_excluded_results": [dual_pool_excluded],
            "ranking_top10": [dual_pool_eligible],
            "universe_count": 2,
            "evaluated_count": 2,
            "eligible_count": 1,
            "ranked_count": 1,
            "hard_excluded_count": 1,
            "universe_partition_complete": True,
            "score_model": {
                "criteria": [{"id": "c9_sector_heat", "weight": 8.0}],
                "normalization_rules": {
                    "c9_sector_heat": heat_verifier.EXPECTED_C9_NORMALIZATION_RULE,
                },
            },
            "execution_policy": {"strong_redemption_announcements_verified": True},
            "redemption_announcement_snapshot": loaded_redemption_meta,
            "source_files": {},
        }
        dual_pool_checks = heat_verifier._production_contract_checks(
            dual_pool_fixture,
            tdx_root=heat_verifier.TRUSTED_TDX_ROOT,
            tdxhy_path=heat_verifier.TRUSTED_HEAT_SOURCES["industry_membership"],
            tdxzs_path=heat_verifier.TRUSTED_HEAT_SOURCES["industry_names"],
            concept_path=heat_verifier.TRUSTED_HEAT_SOURCES["concept_membership"],
        )
        dual_pool_flag_tamper = {
            **dual_pool_fixture,
            "hard_excluded_results": [
                {**dual_pool_excluded, "hard_exclusion_pass": True},
            ],
        }
        dual_pool_flag_tamper_checks = heat_verifier._production_contract_checks(
            dual_pool_flag_tamper,
            tdx_root=heat_verifier.TRUSTED_TDX_ROOT,
            tdxhy_path=heat_verifier.TRUSTED_HEAT_SOURCES["industry_membership"],
            tdxzs_path=heat_verifier.TRUSTED_HEAT_SOURCES["industry_names"],
            concept_path=heat_verifier.TRUSTED_HEAT_SOURCES["concept_membership"],
        )
        dual_pool_rank_tamper = {
            **dual_pool_fixture,
            "all_results": [{**dual_pool_eligible, "rank": 2}],
            "ranking_top10": [{**dual_pool_eligible, "rank": 2}],
        }
        dual_pool_rank_tamper_checks = heat_verifier._production_contract_checks(
            dual_pool_rank_tamper,
            tdx_root=heat_verifier.TRUSTED_TDX_ROOT,
            tdxhy_path=heat_verifier.TRUSTED_HEAT_SOURCES["industry_membership"],
            tdxzs_path=heat_verifier.TRUSTED_HEAT_SOURCES["industry_names"],
            concept_path=heat_verifier.TRUSTED_HEAT_SOURCES["concept_membership"],
        )

        malformed_result_path = temporary_root / "malformed-result.json"
        malformed_verification_path = temporary_root / "malformed-verification.json"
        malformed_result_path.write_text("{", encoding="utf-8")
        malformed_verifier_run = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "verify_convertible_bond_screening.py"),
                "--input",
                str(malformed_result_path),
                "--redemption-announcements",
                str(redemption_snapshot_path),
                "--output",
                str(malformed_verification_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        malformed_verification = (
            json.loads(malformed_verification_path.read_text(encoding="utf-8"))
            if malformed_verification_path.is_file()
            else {}
        )

        argument_failure_path = temporary_root / "argument-failure.json"
        argument_failure_run = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "verify_convertible_bond_screening.py"),
                "--output",
                str(argument_failure_path),
                "--unsupported-selftest-option",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        argument_failure = (
            json.loads(argument_failure_path.read_text(encoding="utf-8"))
            if argument_failure_path.is_file()
            else {}
        )

    formula_recent_dates = benchmark_dates[-2:]
    valid_formula_node = {
        "波": [
            {"Date": formula_recent_dates[0], "Value": 10},
            {"Date": formula_recent_dates[1], "Value": 11},
        ],
        "段": [
            {"Date": formula_recent_dates[0], "Value": 12},
            {"Date": formula_recent_dates[1], "Value": 10},
        ],
    }
    formula_valid = scanner.formula_field_coverage(
        {stock_symbol: valid_formula_node}, [stock_symbol], ("波", "段"), formula_cutoff, 2
    )
    formula_invalid = scanner.formula_field_coverage(
        {stock_symbol: {"波": valid_formula_node["波"]}},
        [stock_symbol],
        ("波", "段"),
        formula_cutoff,
        2,
    )

    def make_scr_series(dates: list[str], values: list[Any] | None = None) -> list[dict[str, Any]]:
        actual_values = values or [100.0 - index for index in range(len(dates))]
        return [
            {"Date": date, "Value": actual_values[index]}
            for index, date in enumerate(dates)
        ]

    scr_exact = scanner.validate_exact_formula_window(
        make_scr_series(required_scr_dates), formula_cutoff, required_scr_dates
    )
    scr_missing = scanner.validate_exact_formula_window(
        make_scr_series(required_scr_dates[:-1]), formula_cutoff, required_scr_dates
    )
    scr_off_calendar_dates = [benchmark_dates[-7], *required_scr_dates[1:]]
    scr_off_calendar = scanner.validate_exact_formula_window(
        make_scr_series(scr_off_calendar_dates), formula_cutoff, required_scr_dates
    )
    scr_duplicate_dates = list(required_scr_dates)
    scr_duplicate_dates[2] = scr_duplicate_dates[1]
    scr_duplicate = scanner.validate_exact_formula_window(
        make_scr_series(scr_duplicate_dates), formula_cutoff, required_scr_dates
    )
    scr_reverse = scanner.validate_exact_formula_window(
        make_scr_series(list(reversed(required_scr_dates))), formula_cutoff, required_scr_dates
    )
    scr_stale = scanner.validate_exact_formula_window(
        make_scr_series(benchmark_history_dates[-12:-6]), formula_cutoff, required_scr_dates
    )
    scr_nan_values: list[Any] = [100.0 - index for index in range(len(required_scr_dates))]
    scr_nan_values[3] = "NaN"
    scr_nan = scanner.validate_exact_formula_window(
        make_scr_series(required_scr_dates, scr_nan_values), formula_cutoff, required_scr_dates
    )
    scr_future = scanner.validate_exact_formula_window(
        [*make_scr_series(required_scr_dates), {"Date": "20991231", "Value": 1.0}],
        formula_cutoff,
        required_scr_dates,
    )
    scr_not_list = scanner.validate_exact_formula_window(
        None, formula_cutoff, required_scr_dates
    )
    scr_eval = scanner.eval_scr(
        {"SCR": make_scr_series(required_scr_dates, [30.0, 28.0, 26.0, 24.0, 22.0, 20.0])},
        {"SCR": make_scr_series(required_scr_dates, [20.0, 19.0, 18.0, 17.0, 16.5, 16.0])},
        formula_cutoff,
        required_scr_dates,
    )

    c4_bond = {"remaining_yi": 4.0}
    c4_local_no_cross = {
        "weekly_return_pct": 0.0,
        "premium_pct": 20.0,
        "stock_signal_available": True,
        "ignition_local_cross_dates_10": [],
        "ema3_latest": 9.0,
        "ema21_latest": 10.0,
        "youzi_buy_latest": None,
        "youzi_buy_prev": None,
        "youzi_recent_cross_dates_5": [],
        "turnover_5d_pct": None,
        "underlying_trend_score": 0.7,
        "bigbull_formula_diagnostic_hits": [{"field": "OUTPUT59", "date": formula_cutoff, "value": 1.0}],
    }
    c4_no_cross = scanner.build_score_components(
        c4_bond, c4_local_no_cross, {}, {}, {}, [], benchmark_dates
    )["c4_golden_ignition"]
    c4_local_formula_off = dict(c4_local_no_cross)
    c4_local_formula_off["bigbull_formula_diagnostic_hits"] = []
    c4_no_cross_formula_off = scanner.build_score_components(
        c4_bond, c4_local_formula_off, {}, {}, {}, [], benchmark_dates
    )["c4_golden_ignition"]
    c4_local_with_cross = dict(c4_local_no_cross)
    c4_local_with_cross["ignition_local_cross_dates_10"] = [required_scr_dates[-1]]
    c4_with_cross = scanner.build_score_components(
        c4_bond, c4_local_with_cross, {}, {}, {}, [], benchmark_dates
    )["c4_golden_ignition"]
    c9_adversarial_concepts = [
        {"name": "热度优先", "heat_score": 90.0, "mean_return_5d": -2.0, "up_ratio_5d": 0.0},
        {"name": "复合因子诱饵", "heat_score": 80.0, "mean_return_5d": 2.0, "up_ratio_5d": 1.0},
    ]
    c9_adversarial = scanner.build_score_components(
        c4_bond,
        c4_local_no_cross,
        {},
        {},
        {"heat_score": 50.0},
        c9_adversarial_concepts,
        benchmark_dates,
    )["c9_sector_heat"]
    c9_adversarial_best = c9_adversarial["raw_value"]["best_concept"]
    independent_c9 = heat_verifier._expected_c9_component(
        {"heat_score": 50.0}, c9_adversarial_concepts, 0.7
    )
    production_c9_core = {
        key: c9_adversarial.get(key)
        for key in independent_c9
    }
    tampered_c9 = dict(independent_c9)
    tampered_c9["earned_score"] = float(tampered_c9["earned_score"]) + 1.0

    scanner_main_source = inspect.getsource(scanner._main_impl)
    with tempfile.TemporaryDirectory(prefix="cb-screening-contract-") as contract_dir:
        contract_root = Path(contract_dir)
        fixture_source = contract_root / "speckzzdata.txt"
        fixture_fields = [""] * 18
        fixture_fields[0] = "1"
        fixture_fields[1] = "123456"
        fixture_fields[2] = "600000"
        fixture_fields[3] = "10.0"
        fixture_fields[10] = "20291231"
        fixture_fields[12] = "10000"
        maturity_cutoff_fields = list(fixture_fields)
        maturity_cutoff_fields[1] = "123457"
        maturity_cutoff_fields[10] = formula_cutoff
        last_trade_cutoff_fields = list(fixture_fields)
        last_trade_cutoff_fields[1] = "123458"
        last_trade_cutoff_fields[17] = formula_cutoff
        fixture_source.write_text(
            "\n".join(
                [
                    ",".join(fixture_fields),
                    ",".join(maturity_cutoff_fields),
                    ",".join(last_trade_cutoff_fields),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        original_bond_source = scanner.BOND_SOURCE
        original_parse_tnf = scanner.parse_tnf
        try:
            scanner.BOND_SOURCE = fixture_source
            scanner.parse_tnf = lambda _path: {}
            fixture_bonds, _fixture_tnf, fixture_diagnostics = scanner.parse_bonds(formula_cutoff)
        finally:
            scanner.BOND_SOURCE = original_bond_source
            scanner.parse_tnf = original_parse_tnf
        fixture_bond = fixture_bonds[0] if fixture_bonds else None

        class EmptyHistoryHub:
            @staticmethod
            def read_day_records(_symbol: str, _limit: int) -> list[dict[str, Any]]:
                return []

        empty_local, empty_reason = scanner.analyze_local(
            EmptyHistoryHub(), fixture_bond, formula_cutoff, benchmark_dates
        ) if fixture_bond else (None, "fixture_not_parsed")
        empty_score_components = scanner.build_score_components(
            fixture_bond, empty_local, {}, {}, {}, [], benchmark_dates
        ) if fixture_bond and empty_local else {}

        class TwoSessionBondHub:
            @staticmethod
            def read_day_records(symbol: str, _limit: int) -> list[dict[str, Any]]:
                if symbol != fixture_bond["symbol"]:
                    return []
                return [
                    {"date": benchmark_dates[-2], "close": 100.0, "volume": 10.0},
                    {"date": benchmark_dates[-1], "close": 110.0, "volume": 40.0},
                ]

        two_session_local, two_session_reason = scanner.analyze_local(
            TwoSessionBondHub(), fixture_bond, formula_cutoff, benchmark_dates
        ) if fixture_bond else (None, "fixture_not_parsed")

        class ManifestHub:
            def __init__(self, root: Path) -> None:
                self.root = root

            def day_path(self, symbol: str) -> Path:
                return self.root / f"{symbol.replace('.', '_')}.day"

            @staticmethod
            def day_price_divisor(symbol: str) -> float:
                return float(hub.day_price_divisor(symbol))

            @staticmethod
            def parse_day_record(chunk: bytes, divisor: float) -> dict[str, Any]:
                return hub.parse_day_record(chunk, divisor)

        manifest_hub = ManifestHub(contract_root)
        missing_day_manifest = scanner.build_day_input_manifest(
            manifest_hub, ["123456.SH"], run_id, formula_cutoff
        )
        invalid_day_path = manifest_hub.day_path("654321.SZ")
        invalid_day_path.write_bytes(b"invalid-layout")
        invalid_day_manifest = scanner.build_day_input_manifest(
            manifest_hub, ["654321.SZ"], run_id, formula_cutoff
        )
        snapshot_symbol = bond_symbol
        snapshot_path = manifest_hub.day_path(snapshot_symbol)
        snapshot_bytes = bond_path.read_bytes()[-2 * hub.DAY_RECORD.size :]
        snapshot_path.write_bytes(snapshot_bytes)
        frozen_hub, immutable_day_manifest = scanner.capture_day_input_snapshot(
            manifest_hub, [snapshot_symbol], run_id, formula_cutoff
        )
        snapshot_current_before, snapshot_before_diagnostics = (
            scanner.validate_day_input_manifest_current(
                manifest_hub,
                immutable_day_manifest,
                expected_run_id=run_id,
                expected_cutoff=formula_cutoff,
                trusted_day_root=contract_root,
            )
        )
        frozen_rows_before = frozen_hub.read_day_records(snapshot_symbol, 2)
        mutated_snapshot_bytes = bytearray(snapshot_bytes)
        mutated_snapshot_bytes[-1] ^= 1
        snapshot_path.write_bytes(mutated_snapshot_bytes)
        frozen_rows_after = frozen_hub.read_day_records(snapshot_symbol, 2)
        snapshot_current_after, snapshot_after_diagnostics = (
            scanner.validate_day_input_manifest_current(
                manifest_hub,
                immutable_day_manifest,
                expected_run_id=run_id,
                expected_cutoff=formula_cutoff,
                trusted_day_root=contract_root,
            )
        )
        frozen_limit_rejected = False
        try:
            frozen_hub.read_day_records(snapshot_symbol, scanner.DAY_INPUT_TAIL_RECORD_LIMIT + 1)
        except RuntimeError:
            frozen_limit_rejected = True

        class AliasManifestHub(ManifestHub):
            def day_path(self, symbol: str) -> Path:
                bare_symbol = str(symbol).split(".", 1)[0]
                return self.root / f"{bare_symbol}.day"

            @staticmethod
            def day_price_divisor(_symbol: str) -> float:
                return 100.0

        alias_manifest_hub = AliasManifestHub(contract_root)
        alias_raw_symbol = "000001"
        alias_suffix_symbol = "000001.SZ"
        alias_snapshot_path = alias_manifest_hub.day_path(alias_raw_symbol)
        alias_snapshot_path.write_bytes(snapshot_bytes)
        alias_frozen_hub, alias_day_manifest = scanner.capture_day_input_snapshot(
            alias_manifest_hub,
            [alias_raw_symbol, alias_suffix_symbol],
            run_id,
            formula_cutoff,
        )
        alias_snapshot_current, alias_snapshot_diagnostics = (
            scanner.validate_day_input_manifest_current(
                alias_manifest_hub,
                alias_day_manifest,
                expected_run_id=run_id,
                expected_cutoff=formula_cutoff,
                trusted_day_root=contract_root,
            )
        )
        alias_rows_match = alias_frozen_hub.read_day_records(
            alias_raw_symbol, 2
        ) == alias_frozen_hub.read_day_records(alias_suffix_symbol, 2)

        independent_raw_parts = heat_verifier._manifest_alias_parts(alias_raw_symbol)
        independent_suffix_parts = heat_verifier._manifest_alias_parts(alias_suffix_symbol)
        independent_alias_candidates_match = {
            str(path) for path in heat_verifier._trusted_day_candidates(alias_raw_symbol)
        } == {
            str(path) for path in heat_verifier._trusted_day_candidates(alias_suffix_symbol)
        }
        independent_frozen_reader = heat_verifier.FrozenDayInputSnapshot(
            manifest_path=contract_root / "independent-alias-manifest.json",
            manifest_raw=b"{}",
            manifest_stat=(2, 0),
            manifest_binding={},
            manifest={},
            nodes=[],
            raw_by_alias={
                alias_raw_symbol: snapshot_bytes,
                alias_suffix_symbol: snapshot_bytes,
            },
            path_by_alias={
                alias_raw_symbol: str(alias_snapshot_path),
                alias_suffix_symbol: str(alias_snapshot_path),
            },
        )
        independent_alias_rows_match = independent_frozen_reader.read_rows(
            alias_raw_symbol, 2
        ) == independent_frozen_reader.read_rows(alias_suffix_symbol, 2)
        independent_uncaptured_rejected = False
        try:
            independent_frozen_reader.read_rows("000002.SZ", 1)
        except ValueError:
            independent_uncaptured_rejected = True

        verifier_132_record = main_verifier.DAY_RECORD.pack(
            int(formula_cutoff),
            1234500,
            1234500,
            1234500,
            1234500,
            2000.0,
            1000,
            0,
        )
        verifier_frozen_reader = main_verifier.FrozenManifestDayReader(
            {"132001.SH": verifier_132_record},
            {"132001.SH": "selftest://132001.SH"},
        )
        verifier_132_rows_before = verifier_frozen_reader.read_rows("132001.SH", 1)
        live_mutation_decoy = bytearray(verifier_132_record)
        live_mutation_decoy[16] ^= 1
        verifier_132_rows_after = verifier_frozen_reader.read_rows("132001.SH", 1)
        verifier_uncaptured_rejected = False
        try:
            verifier_frozen_reader.read_rows("132002.SH", 1)
        except RuntimeError:
            verifier_uncaptured_rejected = True

        verifier_race_output = contract_root / "verifier-race.json"
        verifier_race_diagnostics = [
            {
                "path": str((TDX_ROOT / "vipdoc" / "sh" / "lday" / "sh999999.day").resolve()),
                "current": False,
                "contract": True,
                "mismatches": ["current_field:mtime_ns"],
            }
        ]
        verifier_race_stderr = io.StringIO()
        with contextlib.redirect_stderr(verifier_race_stderr):
            verifier_race_returncode = main_verifier.emit_day_update_race(
                verifier_race_output,
                retry_contract_run_id,
                2,
                {"day_input_manifest_current": False},
                verifier_race_diagnostics,
            )
        verifier_race_report = json.loads(verifier_race_output.read_text(encoding="utf-8"))
        verifier_race_event = json.loads(verifier_race_stderr.getvalue().strip().splitlines()[-1])

    day_manifest_sample = scanner.build_day_input_manifest(
        hub,
        [bond_symbol, stock_symbol],
        run_id,
        str(bond_parsed["date"]),
    )
    missing_component = scanner.score_component(
        "c1_price_activity",
        0.0,
        {"weekly_return_pct": None},
        "MISSING",
    )
    partial_component = scanner.score_component(
        "c9_sector_heat",
        0.2,
        {"industry_heat_score": 50.0, "best_concept": None},
        "PARTIAL",
        "selftest",
        0.3,
    )
    original_process_run = scanner.subprocess.run
    try:
        scanner.subprocess.run = lambda *call_args, **call_kwargs: subprocess.CompletedProcess(
            args=call_args[0] if call_args else [],
            returncode=0,
            stdout='INFO: No tasks are running which match the specified criteria.',
            stderr='',
        )
        try:
            scanner.require_tdx_client()
            missing_client_error_exact = False
        except RuntimeError as exc:
            missing_client_error_exact = str(exc) == "tdx_client_not_running:TdxW.exe"
    finally:
        scanner.subprocess.run = original_process_run
    compacted_diagnostic = entry_module.compact_child_diagnostic(
        "fallback stdout",
        "first line\nactual root cause",
    )
    working_output = io.StringIO()
    working_output_ok = entry_module.emit_best_effort(
        "working-output",
        stream=working_output,
    )

    class DisconnectedOutput:
        def write(self, _value: str) -> int:
            raise OSError(22, "detached output pipe")

        def flush(self) -> None:
            return None

    original_entry_runner = entry_module.run_process_tree
    detached_invoke_elapsed: float | None = None
    try:
        entry_module.run_process_tree = lambda *call_args, **call_kwargs: subprocess.CompletedProcess(
            args=call_args[0] if call_args else [],
            returncode=0,
            stdout="persisted child success\n",
            stderr="nonfatal child diagnostic\n",
        )
        with contextlib.redirect_stdout(DisconnectedOutput()), contextlib.redirect_stderr(
            DisconnectedOutput()
        ):
            detached_invoke_elapsed = entry_module.invoke(
                "selftest.py",
                [],
                timeout_seconds=1,
            )
    finally:
        entry_module.run_process_tree = original_entry_runner
    main_verifier_impl_source = inspect.getsource(main_verifier._main_impl)
    verifier_manifest_failfast_index = main_verifier_impl_source.index("if not day_inputs_current:")
    verifier_heat_recompute_index = main_verifier_impl_source.index("heat = recompute_heat(")
    verifier_final_freshness_index = main_verifier_impl_source.rindex(
        "validate_day_input_manifest("
    )
    independent_compare_source = inspect.getsource(heat_verifier.compare_latest_result)
    independent_manifest_load_index = independent_compare_source.index(
        "day_snapshot = _load_bound_day_input_snapshot(production)"
    )
    independent_heat_recompute_index = independent_compare_source.index(
        "recomputed = recompute_heat("
    )
    independent_final_freshness_index = independent_compare_source.index(
        "_assert_day_input_snapshot_current(day_snapshot)"
    )
    entry_run_source = inspect.getsource(entry_module.command_run)
    entry_publish_source = inspect.getsource(entry_module.publish_latest_summary)
    entry_write_status_source = inspect.getsource(entry_module.write_status)
    entry_status_readback_source = inspect.getsource(entry_module._command_status_impl)
    entry_status_source = inspect.getsource(entry_module.command_status)
    entry_deliver_source = inspect.getsource(entry_module.command_deliver)
    delivery_source = inspect.getsource(delivery_contract.build_delivery_payload)
    delivery_model_validation_source = inspect.getsource(
        delivery_contract._validate_score_model
    )
    delivery_authoritative_source = inspect.getsource(
        delivery_contract._validated_authoritative_paths
    )
    entry_top1_binding_source = inspect.getsource(entry_module.top1_evidence_binding_checks)
    finalizing_readback_index = entry_run_source.index(
        'expected_run_state="FINALIZING"'
    )
    publish_latest_summary_index = entry_run_source.index(
        "publish_latest_summary("
    )
    pass_commit_index = entry_run_source.index(
        'current_stage = "final_pass_commit"'
    )
    pass_readback_index = entry_run_source.index(
        'expected_run_state="PASS"'
    )
    top1_entry_resolver = getattr(top1_validator, "business_entry_for", None)
    top1_business_entries: dict[str, Path] = {}
    if callable(top1_entry_resolver):
        top1_business_entries = {
            skill: Path(top1_entry_resolver(skill)).resolve()
            for skill in DEPENDENCIES
        }
    top1_artifact_state = getattr(top1_validator, "artifact_state", None)
    missing_top1_artifact = Path(tempfile.gettempdir()) / f"cb-top1-missing-{uuid.uuid4().hex}.json"
    missing_top1_artifact_state = (
        top1_artifact_state(missing_top1_artifact)
        if callable(top1_artifact_state)
        else {}
    )

    scanner_confirmation = getattr(scanner, "build_personal_kb_confirmation", None)
    scanner_ranking_key = getattr(scanner, "ranking_key", None)
    main_confirmation = getattr(main_verifier, "recompute_personal_kb_confirmation", None)
    main_ranking_key = getattr(main_verifier, "personal_kb_ranking_key", None)
    independent_confirmation = getattr(
        heat_verifier, "_expected_personal_kb_confirmation", None
    )
    independent_ranking_key = getattr(
        heat_verifier, "_personal_kb_ranking_key", None
    )
    confirmation_functions = (
        scanner_confirmation,
        main_confirmation,
        independent_confirmation,
    )
    ranking_functions = (
        scanner_ranking_key,
        main_ranking_key,
        independent_ranking_key,
    )
    kb_complete_item = {
        "symbol": "110001.SH",
        "score_total_raw": 80.0,
        "big_bull_red_preference": False,
        "score_coverage_weight": 100.0,
        "score_missing_criteria": [],
        "score_partial_criteria": [],
        "bond_current": True,
        "stock_current": True,
        "bond_full_lookback": True,
        "stock_signal_available": True,
        "volume_structure_available": True,
        "volume_structure_pass": True,
        "sudden_abnormal_volume_contraction": False,
        "intraday_status": "STRONG",
        "turnover_5d_pct": 300.0,
        "remaining_yi": 3.0,
        "bond_close": 120.0,
        "premium_pct": 20.0,
        "daily_return_pct": 2.0,
        "early_redemption_status": "NO_MATCH_AS_OF_CUTOFF",
        "risk_level": "GREEN",
    }
    kb_missing_item = {
        **kb_complete_item,
        "symbol": "110002.SH",
        "score_coverage_weight": 0.0,
        "score_missing_criteria": list(expected_weights),
        "score_partial_criteria": ["c4_golden_ignition", "c5_feilong_cross"],
        "bond_current": False,
        "stock_current": False,
        "bond_full_lookback": False,
        "stock_signal_available": False,
        "volume_structure_available": False,
        "volume_structure_pass": False,
        "sudden_abnormal_volume_contraction": True,
        "intraday_status": "MISSING",
        "turnover_5d_pct": None,
        "remaining_yi": None,
        "bond_close": None,
        "premium_pct": None,
        "daily_return_pct": None,
        "early_redemption_status": "UNVERIFIED",
        "risk_level": "RED",
    }
    kb_red_item = {
        **kb_complete_item,
        "symbol": "110003.SH",
        "risk_level": "RED",
    }
    complete_before_score = kb_complete_item["score_total_raw"]
    confirmation_outputs = (
        [function(dict(kb_complete_item)) for function in confirmation_functions]
        if all(callable(function) for function in confirmation_functions)
        else []
    )
    missing_confirmation_outputs = (
        [function(dict(kb_missing_item)) for function in confirmation_functions]
        if all(callable(function) for function in confirmation_functions)
        else []
    )
    red_confirmation_outputs = (
        [function(dict(kb_red_item)) for function in confirmation_functions]
        if all(callable(function) for function in confirmation_functions)
        else []
    )
    ranking_contract_rows = [
        {
            "symbol": "110004.SH",
            "score_total_raw": 80.0,
            "personal_kb_confirmation": {"quality_score": 100.0},
            "big_bull_red_preference": True,
        },
        {
            "symbol": "110003.SH",
            "score_total_raw": 80.0,
            "personal_kb_confirmation": {"quality_score": 100.0},
            "big_bull_red_preference": False,
        },
        {
            "symbol": "110002.SH",
            "score_total_raw": 80.0,
            "personal_kb_confirmation": {"quality_score": 90.0},
            "big_bull_red_preference": True,
        },
        {
            "symbol": "110001.SH",
            "score_total_raw": 81.0,
            "personal_kb_confirmation": {"quality_score": 0.0},
            "big_bull_red_preference": False,
        },
        {
            "symbol": "110005.SH",
            "score_total_raw": 80.0,
            "personal_kb_confirmation": {"quality_score": 100.0},
            "big_bull_red_preference": True,
        },
    ]
    ranking_orders = (
        [
            [
                item["symbol"]
                for item in sorted(ranking_contract_rows, key=function)
            ]
            for function in ranking_functions
        ]
        if all(callable(function) for function in ranking_functions)
        else []
    )
    expected_ranking_order = [
        "110001.SH",
        "110004.SH",
        "110005.SH",
        "110003.SH",
        "110002.SH",
    ]
    confirmation_models = [
        getattr(module, "PERSONAL_KB_CONFIRMATION_MODEL", None)
        for module in (scanner, main_verifier, heat_verifier)
    ]

    checks = {
        "all_scripts_compile": not compile_errors,
        "personal_kb_confirmation_functions_available": all(
            callable(function) for function in confirmation_functions
        ),
        "personal_kb_ranking_functions_available": all(
            callable(function) for function in ranking_functions
        ),
        "personal_kb_model_metadata_exact": bool(
            len(confirmation_models) == 3
            and all(model == confirmation_models[0] for model in confirmation_models)
            and confirmation_models[0]
            == {
                "version": "CB-PERSONAL-A-SHARE-KB-CONFIRMATION-1",
                "knowledge_source": {
                    "id": "personal_a_share_investment_kb",
                    "scope": "accepted category-level A-share method principles",
                    "source_tables": ["knowledge_cards", "a_share_mappings"],
                    "snapshot_counts": {
                        "entities": 300,
                        "knowledge_cards": 300,
                        "claims": 900,
                        "a_share_mappings": 300,
                    },
                    "person_attribution": False,
                },
                "score_invariance": "does_not_modify_score_components_or_score_total_raw",
                "ranking_scope": "exact_score_total_raw_ties_only",
                "automatic_order": False,
            }
        ),
        "personal_kb_three_way_confirmation_exact": bool(
            len(confirmation_outputs) == 3
            and confirmation_outputs[0] == confirmation_outputs[1] == confirmation_outputs[2]
            and confirmation_outputs[0].get("quality_score") == 100.0
            and confirmation_outputs[0].get("level") == "HIGH"
        ),
        "personal_kb_missing_evidence_downgrades_low": bool(
            len(missing_confirmation_outputs) == 3
            and missing_confirmation_outputs[0]
            == missing_confirmation_outputs[1]
            == missing_confirmation_outputs[2]
            and missing_confirmation_outputs[0].get("level") == "LOW"
            and len(missing_confirmation_outputs[0].get("risk_labels") or []) >= 6
            and missing_confirmation_outputs[0].get("risk_labels")
            == [
                "kb_liquidity_capacity_fragile",
                "kb_trading_cost_or_slippage_risk",
                "kb_gap_jump_risk",
                "kb_suspension_or_stale_quote_risk",
                "kb_data_anomaly_integrity_risk",
                "kb_exit_delay_risk",
                "kb_recomputable_evidence_missing",
            ]
        ),
        "personal_kb_red_never_high_and_capped": bool(
            len(red_confirmation_outputs) == 3
            and red_confirmation_outputs[0]
            == red_confirmation_outputs[1]
            == red_confirmation_outputs[2]
            and red_confirmation_outputs[0].get("quality_score") <= 59.0
            and red_confirmation_outputs[0].get("level") != "HIGH"
        ),
        "personal_kb_score_total_raw_invariant": bool(
            kb_complete_item["score_total_raw"] == complete_before_score
            and all(
                output.get("model_version")
                == "CB-PERSONAL-A-SHARE-KB-CONFIRMATION-1"
                for output in confirmation_outputs
            )
        ),
        "personal_kb_ranking_contract_exact": bool(
            len(ranking_orders) == 3
            and ranking_orders[0] == ranking_orders[1] == ranking_orders[2]
            and ranking_orders[0] == expected_ranking_order
        ),
        "personal_kb_automatic_order_remains_false": bool(
            confirmation_models
            and confirmation_models[0]
            and confirmation_models[0].get("automatic_order") is False
            and '"automatic_order": False' in scanner_main_source
        ),
        "retry_classifier_accepts_exact_scanner_and_verifier_events": bool(
            retry_classifier_exact_scan == retry_scan_event
            and retry_classifier_exact_verify == retry_verify_event
        ),
        "retry_classifier_rejects_wrong_run_attempt_or_script": retry_classifier_wrong_binding_rejected,
        "retry_classifier_rejects_unstructured_or_wrong_exit": retry_classifier_unstructured_rejected,
        "retry_classifier_rejects_malformed_diagnostics": retry_classifier_malformed_diagnostics_rejected,
        "criteria_exactly_10": len(weights) == 10 and set(weights) == set(expected_weights),
        "weights_exact": weights == expected_weights,
        "weights_sum_100": abs(sum(weights.values()) - 100.0) < 1e-12,
        "delivery_model_version_exact": (
            delivery_contract.SCORE_MODEL_VERSION == "CB-WEIGHTED-10-V2"
        ),
        "delivery_criterion_count_exact": len(delivery_contract.SCORE_CRITERIA) == 10,
        "delivery_criterion_ids_and_order_exact": bool(
            tuple(delivery_contract.SCORE_COMPONENT_IDS) == tuple(expected_weights)
            and tuple(item["id"] for item in scanner.SCORE_CRITERIA)
            == tuple(expected_weights)
        ),
        "delivery_individual_weights_exact": bool(
            weights == expected_weights
            and tuple(delivery_contract.SCORE_COMPONENT_WEIGHTS)
            == tuple(expected_weights.values())
        ),
        "delivery_weight_sum_100": abs(
            sum(delivery_contract.SCORE_COMPONENT_WEIGHTS) - 100.0
        )
        < 1e-12,
        "delivery_big_bull_not_scored": bool(
            not any(
                "big_bull" in criterion_id.lower()
                for criterion_id in delivery_contract.SCORE_COMPONENT_IDS
            )
            and "big_bull_cannot_be_scored" in delivery_model_validation_source
            and "big_bull_tie_break_rule_missing"
            in delivery_model_validation_source
            and "big_bull_zero_score_rule_missing"
            in delivery_model_validation_source
        ),
        "delivery_automatic_order_false": '"automatic_order": False' in delivery_source,
        "delivery_authoritative_files_only": (
            delivery_contract.AUTHORITATIVE_FILENAMES
            == ("run_state", "status_readback", "skill_status", "latest_summary")
            and delivery_contract.AUTHORITATIVE_RELATIVE_PATHS
            == {
                "run_state": Path("run_state.json"),
                "status_readback": Path("status_readback.json"),
                "skill_status": Path("skill_status.json"),
                "latest_summary": Path("latest_summary.json"),
            }
            and "authoritative_sources:exact_names_and_order_required"
            in delivery_authoritative_source
        ),
        "delivery_cross_run_mixing_rejected": bool(
            "authoritative_sources:cross_run_mixing_rejected" in delivery_source
            and "authoritative_sources:cross_attempt_mixing_rejected"
            in delivery_source
        ),
        "delivery_old_latest_result_rejected": bool(
            'run_root / "generations" / run_id / f"attempt-{market_attempt}"'
            in delivery_source
            and 'generation_dir / "latest_result.json"' in delivery_source
            and 'run_root / "latest_result.json"' not in delivery_source
        ),
        "delivery_manual_override_forbidden": (
            '"manual_override_allowed": False' in delivery_source
            and '"cross_run_mixing_allowed": False' in delivery_source
        ),
        "delivery_entry_is_hard_gated": bool(
            "build_delivery_payload(RUN)" in entry_status_source
            and "build_delivery_payload(RUN)" in entry_deliver_source
            and '"status": "BLOCKED"' in entry_deliver_source
        ),
        "latest_benchmark_cutoff_used": formula_cutoff == str(benchmark_rows[-1]["date"]),
        "routine_dependency_set_exactly_six": len(DEPENDENCIES) == 6
        and "stock-unified" not in DEPENDENCIES
        and set(DEPENDENCIES) == {
            "stock-hard-gate",
            "tdx-local-hub",
            "golden-ignition",
            "feilong-strategy",
            "youzi-capital-monitoring",
            "big-bull-analysis-scoring-system",
        },
        "tdx_required_files_present": all(path.is_file() for path in required_tdx_files),
        "tqcenter_importable": importlib.util.find_spec("tqcenter") is not None,
        "bond_suffix_path_exact": bond_path.name.lower() == f'{bond_symbol.split(".")[1].lower()}{bond_symbol.split(".")[0]}.day',
        "bond_price_divisor_10000": hub.day_price_divisor(bond_symbol) == 10000.0,
        "stock_price_divisor_100": hub.day_price_divisor(stock_symbol) == 100.0,
        "bond_raw_price_matches_parser": abs(bond_parsed["close"] - bond_raw_close / 10000.0) < 1e-9,
        "stock_raw_price_matches_parser": abs(stock_parsed["close"] - stock_raw_close / 100.0) < 1e-9,
        "bond_master_integrity_complete": bool(master_diagnostics["integrity_complete"]),
        "tq_batch_size_320": scanner.TQ_BATCH_SIZE == 320,
        "long_formula_history_count_600": scanner.TQ_LONG_FORMULA_HISTORY_COUNT == 600,
        "tq_strategy_identity_is_current_python_file": scanner.TQ_STRATEGY_PATH == (SCRIPTS / "run_convertible_bond_screening.py").resolve()
        and scanner.TQ_STRATEGY_PATH.suffix.lower() == ".py"
        and scanner.TQ_STRATEGY_PATH != scanner.TDX_ROOT,
        "missing_tdx_client_error_exact": missing_client_error_exact,
        "child_diagnostic_preserves_root_cause": compacted_diagnostic == "first line | actual root cause",
        "entry_output_disconnect_does_not_poison_persisted_workflow": bool(
            working_output_ok
            and working_output.getvalue() == "working-output\n"
            and detached_invoke_elapsed is not None
            and detached_invoke_elapsed >= 0.0
            and "emit_best_effort" in inspect.getsource(entry_module.invoke)
            and "emit_best_effort" in inspect.getsource(entry_module.command_run)
        ),
        "entry_early_redemption_uses_fixed_four_workers": bool(
            '"--workers", "4"' in entry_run_source
            and '"--workers", "1"' not in entry_run_source
        ),
        "latest_summary_publication_order_is_fail_closed": bool(
            finalizing_readback_index
            < publish_latest_summary_index
            < pass_commit_index
            < pass_readback_index
        ),
        "latest_summary_pass_readback_checks_exact_generation": all(
            token in entry_status_readback_source
            for token in (
                "latest_summary_bytes_match_generation",
                "latest_summary_size_matches_generation",
                "latest_summary_sha256_matches_generation",
                "latest_summary_run_id_matches",
                "latest_summary_market_attempt_matches",
            )
        ),
        "latest_summary_publication_preserves_source_bytes": bool(
            "source.read_bytes()" in entry_publish_source
            and "atomic_write_bytes(LATEST_SUMMARY, source_bytes)"
            in entry_publish_source
            and "json.dumps(" not in entry_publish_source
        ),
        "latest_summary_dynamic_publication_exact": bool(
            publication_bytes_match
            and publication_size_match
            and publication_sha256_match
            and publication_json_binding_match
        ),
        "latest_summary_atomic_failure_is_rejected": bool(
            publication_failure_rejected
            and publication_failure_target_absent
        ),
        "entry_executes_binds_and_reads_independent_heat_verifier": bool(
            '"independent_heat_verifier.py"' in entry_run_source
            and '"--compare-result", str(paths.result)' in entry_run_source
            and '"--output", str(paths.independent_heat_verification)' in entry_run_source
            and '"--attempt", str(attempt)' in entry_run_source
            and "output_paths=(paths.independent_heat_verification,)" in entry_run_source
            and "production_result_binding" in entry_write_status_source
            and "day_input_manifest" in entry_write_status_source
            and "INDEPENDENT_HEAT_VERIFICATION" in entry_status_readback_source
            and "independent_heat_result_binding_matches" in entry_status_readback_source
            and entry_module.RETRYABLE_CHILD_FAILURE_SCHEMAS.get(
                "independent_heat_verifier.py"
            )
            == "CONVERTIBLE-BOND-VERIFY-FAILURE-1"
        ),
        "entry_top1_binding_uses_generation_paths": bool(
            "paths: GenerationPaths" in entry_top1_binding_source
            and "paths.top1_golden" in entry_top1_binding_source
            and "paths.top1_feilong" in entry_top1_binding_source
            and "paths.top1_bigbull" in entry_top1_binding_source
            and "paths.top1_run_logs" in entry_top1_binding_source
            and "TOP1_RUN_LOGS" not in entry_top1_binding_source
            and '"legacy_codex_entry.py"' in entry_top1_binding_source
            and '"codex_entry.py"' not in entry_top1_binding_source
            and "top1_evidence_binding_checks(top1, paths)" in entry_write_status_source
            and "top1_evidence_binding_checks(top1, paths)" in entry_status_readback_source
        ),
        "top1_dynamic_validation_uses_business_entries": bool(
            len(top1_business_entries) == len(DEPENDENCIES)
            and all(
                top1_business_entries.get(skill)
                == (SKILLS_ROOT / skill / "scripts" / "legacy_codex_entry.py").resolve()
                for skill in DEPENDENCIES
            )
        ),
        "top1_missing_artifact_is_structured": bool(
            missing_top1_artifact_state.get("path") == str(missing_top1_artifact.resolve())
            and missing_top1_artifact_state.get("exists") is False
            and missing_top1_artifact_state.get("size_bytes") is None
            and missing_top1_artifact_state.get("sha256") is None
        ),
        "atomic_json_replace_exact": atomic_replace_exact,
        "run_lock_rejects_concurrent": lock_rejects_concurrent,
        "run_lock_recovers_after_release": lock_recovers_after_release,
        "independent_day_parser_rejects_malformed_layout": malformed_day_rejected,
        "independent_day_parser_rejects_existing_empty_file": empty_day_rejected,
        "scanner_ignores_tdx_root_environment_override": scanner_ignores_tdx_root_environment,
        "scanner_skill_dependency_root_is_self_anchored": scanner_skill_root_is_self_anchored
        and scanner_skills_root_is_self_anchored,
        "independent_text_parser_rejects_invalid_encoding": invalid_text_rejected,
        "independent_verifier_rejects_empty_results": empty_result_report["status"] == "FAIL"
        and "result_pools_well_formed" in empty_result_report.get("failed_checks", []),
        "independent_verifier_rejects_alternate_tdx_root": alternate_root_report["status"] == "FAIL"
        and alternate_root_report.get("checks", {}).get("trusted_tdx_root_exact") is False,
        "redemption_snapshot_loads_and_binds_exact": bool(
            set(loaded_redemption_records) == {item["symbol"] for item in redemption_bonds}
            and all(
                loaded_redemption_records[item["symbol"]] == item
                for item in redemption_records
            )
            and loaded_redemption_meta.get("path") == str(redemption_snapshot_path.resolve())
            and loaded_redemption_meta.get("size") == redemption_snapshot_size
            and loaded_redemption_meta.get("sha256") == redemption_snapshot_sha256
            and loaded_redemption_meta.get("run_id") == run_id
            and loaded_redemption_meta.get("cutoff") == formula_cutoff
            and loaded_redemption_meta.get("status") == "PASS"
            and loaded_redemption_meta.get("current_universe_complete") is True
        ),
        "redemption_snapshot_status_map_exact": bool(
            verifier_redemption_map_well_formed
            and verifier_redemption_map
            == {
                "110001.SH": "NO_MATCH_AS_OF_CUTOFF",
                "123001.SZ": "ANNOUNCED_EARLY_REDEMPTION",
                "113001.SH": "UNVERIFIED",
            }
        ),
        "redemption_snapshot_rejects_wrong_binding_or_coverage": bool(
            redemption_run_binding_rejected
            and redemption_universe_incomplete_rejected
            and redemption_invalid_status_rejected
        ),
        "hard_exclusion_z_prefix_exact": hard_baseline == []
        and hard_z_prefix == ["bond_name_z_prefix"],
        "hard_exclusion_daily_gain_volume_ratio_strict": bool(
            hard_daily_ratio_boundary == []
            and hard_daily_gain_boundary == []
            and hard_daily_triggered == ["daily_gain_ge_10_and_volume_ratio_gt_4"]
        ),
        "hard_exclusion_scr90_daily_expansion_strict": bool(
            hard_scr90_zero == []
            and hard_scr90_positive == ["scr90_change_1d_positive"]
            and hard_scr90_unavailable == ["scr90_change_1d_unavailable"]
        ),
        "hard_exclusion_turnover_5d_strict": hard_turnover_boundary == []
        and hard_turnover_triggered == ["turnover_5d_gt_1000"],
        "hard_exclusion_bond_price_strict": hard_price_boundary == []
        and hard_price_triggered == ["bond_close_gt_350"],
        "hard_exclusion_redemption_statuses_exact": bool(
            hard_announced == ["early_redemption_announced"]
            and hard_no_match == []
            and hard_unverified == ["early_redemption_unverified"]
        ),
        "v5_dual_pool_partition_contract_exact": bool(
            all(
                dual_pool_checks[name]
                for name in {
                    "result_pools_well_formed",
                    "symbols_unique_nonempty",
                    "ranks_contiguous",
                    "declared_counts_match",
                    "universe_partition_complete",
                    "hard_exclusion_flags_exact",
                    "redemption_announcement_binding_shape",
                    "strong_redemption_announcements_verified",
                    "ranking_top10_exact",
                }
            )
            and dual_pool_flag_tamper_checks["hard_exclusion_flags_exact"] is False
            and dual_pool_rank_tamper_checks["ranks_contiguous"] is False
        ),
        "scanner_accepts_valid_tnf_tail_truncation": scanner_accepts_tnf_tail_truncation,
        "main_verifier_accepts_valid_tnf_tail_truncation": verifier_accepts_tnf_tail_truncation,
        "tnf_internal_corruption_still_rejected": tnf_internal_corruption_rejected,
        "main_verifier_persists_structured_failure": malformed_verifier_run.returncode == 2
        and malformed_verification.get("status") == "FAIL"
        and malformed_verification.get("schema") == "TDX-CONVERTIBLE-BOND-VERIFY-FAIL-1"
        and malformed_verification.get("error_type") == "JSONDecodeError"
        and malformed_verification.get("failed_checks") == ["structured_execution"],
        "main_verifier_persists_structured_argument_failure": argument_failure_run.returncode == 2
        and argument_failure.get("status") == "FAIL"
        and argument_failure.get("schema") == "TDX-CONVERTIBLE-BOND-VERIFY-FAIL-1"
        and argument_failure.get("error_type") == "SystemExit"
        and argument_failure.get("exit_code") == 2
        and argument_failure.get("failed_checks") == ["structured_execution"],
        "formula_field_coverage_accepts_complete": bool(formula_valid["complete"]),
        "formula_field_coverage_rejects_missing": not bool(formula_invalid["complete"]),
        "scr_exact_six_session_window_accepts_exact": bool(scr_exact["complete"])
        and scr_exact["actual_tail_dates"] == required_scr_dates,
        "scr_exact_six_session_window_rejects_missing": not bool(scr_missing["complete"]),
        "scr_exact_six_session_window_rejects_off_calendar": not bool(scr_off_calendar["complete"]),
        "scr_exact_six_session_window_rejects_duplicate": not bool(scr_duplicate["complete"]),
        "scr_exact_six_session_window_rejects_reverse": not bool(scr_reverse["complete"]),
        "scr_exact_six_session_window_rejects_stale": not bool(scr_stale["complete"]),
        "scr_exact_six_session_window_rejects_nan": not bool(scr_nan["complete"]),
        "scr_exact_six_session_window_rejects_future": not bool(scr_future["complete"])
        and "item_6_date_after_cutoff" in scr_future["reasons"],
        "scr_missing_series_has_canonical_empty_evidence": scr_not_list == {
            "complete": False,
            "reasons": ["series_not_list"],
            "required_dates": required_scr_dates,
            "actual_dates": [],
            "actual_tail_dates": [],
            "point_count": 0,
            "values": {},
        },
        "scr_eval_uses_required_window_endpoints": bool(scr_eval["window_complete"])
        and scr_eval["old_date"] == required_scr_dates[0]
        and scr_eval["latest_date"] == required_scr_dates[-1]
        and abs(float(scr_eval["shrink90_pp"]) - 10.0) < 1e-12
        and abs(float(scr_eval["relative_shrink90"]) - (1.0 / 3.0)) < 1e-12
        and scr_eval["pass90"] is True
        and abs(float(scr_eval["shrink70_pp"]) - 4.0) < 1e-12,
        "c4_only_local_ema_cross_scores": c4_no_cross["earned_score"] == 0.0
        and c4_no_cross == c4_no_cross_formula_off
        and c4_with_cross["earned_score"] > 0.0
        and "bigbull" not in inspect.signature(scanner.build_score_components).parameters,
        "source_current_missing_tnf_is_retained": len(fixture_bonds) == 1
        and fixture_bond is not None
        and fixture_bond["symbol"] == "123456.SH"
        and fixture_bond["tnf_confirmed"] is False
        and fixture_diagnostics["source_current_candidate_missing_tnf"] == ["123456.SH"]
        and fixture_diagnostics["tnf_reconciliation_complete"] is False
        and fixture_diagnostics["integrity_complete"] is True,
        "term_date_equal_cutoff_is_not_current": fixture_diagnostics["explained_not_current_rows"] == 2
        and {
            "matured_on_or_before_cutoff",
            "last_trade_on_or_before_cutoff",
        }
        == {
            reason
            for item in fixture_diagnostics["explained_not_current_sample"]
            for reason in item["reasons"]
        },
        "missing_local_history_keeps_rankable_placeholder": empty_reason is None
        and empty_local is not None
        and empty_local["bond_history_points"] == 0
        and empty_local["stock_history_points"] == 0
        and "bond_history_missing" in empty_local["risk_veto_reasons"]
        and "underlying_history_missing" in empty_local["risk_veto_reasons"]
        and len(empty_score_components) == 10,
        "daily_return_uses_two_sessions_while_volume_ratio_requires_six": bool(
            two_session_reason is None
            and two_session_local is not None
            and abs(float(two_session_local["daily_return_pct"]) - 10.0) < 1e-12
            and two_session_local["bond_volume_ratio_5d"] is None
            and two_session_local["bond_full_lookback"] is False
        ),
        "main_enforces_eligible_and_hard_excluded_pool_partition": all(
            token in scanner_main_source
            for token in (
                'results = [item for item in evaluated_results if item["hard_exclusion_pass"]]',
                'hard_excluded_results = [item for item in evaluated_results if not item["hard_exclusion_pass"]]',
                '"universe_partition_complete": universe_partition_complete',
                '"hard_excluded_results": hard_excluded_results',
            )
        ),
        "day_manifest_explicit_missing_is_complete": bool(missing_day_manifest["complete"])
        and missing_day_manifest["missing_input_count"] == 1
        and missing_day_manifest["all_existing_layouts_valid"] is True
        and missing_day_manifest["missing_inputs_explicit"] is True,
        "day_manifest_invalid_existing_layout_fails": not bool(invalid_day_manifest["complete"])
        and invalid_day_manifest["existing_input_count"] == 1
        and invalid_day_manifest["all_existing_layouts_valid"] is False,
        "day_input_manifest_sample_complete": bool(day_manifest_sample["complete"])
        and day_manifest_sample["input_count"] == 2,
        "immutable_day_snapshot_schema_and_binding_exact": bool(immutable_day_manifest["complete"])
        and immutable_day_manifest["schema"] == "CONVERTIBLE-BOND-DAY-INPUT-MANIFEST-2"
        and immutable_day_manifest["binding_mode"] == "immutable_tail_snapshot_pre_and_post"
        and immutable_day_manifest["stable_capture_passes"] == 2
        and immutable_day_manifest["tail_record_limit"] == 260,
        "immutable_day_snapshot_is_current_before_mutation": snapshot_current_before
        and all(item["current"] for item in snapshot_before_diagnostics),
        "immutable_day_snapshot_preserves_computed_bytes_after_mutation": frozen_rows_before
        == frozen_rows_after,
        "immutable_day_snapshot_detects_source_mutation": not snapshot_current_after
        and any(item["current"] is False for item in snapshot_after_diagnostics),
        "immutable_day_snapshot_rejects_uncaptured_history": frozen_limit_rejected,
        "immutable_day_snapshot_preserves_raw_and_suffixed_aliases": bool(
            alias_day_manifest["complete"]
            and alias_day_manifest["input_count"] == 1
            and alias_day_manifest["alias_count"] == 2
            and alias_day_manifest["inputs"][0]["lookup_symbols"]
            == [alias_raw_symbol, alias_suffix_symbol]
            and alias_snapshot_current
            and all(item["current"] for item in alias_snapshot_diagnostics)
            and alias_rows_match
        ),
        "independent_verifier_accepts_raw_and_suffixed_aliases": bool(
            independent_raw_parts[:2] == independent_suffix_parts[:2] == ("000001", "sz")
            and independent_alias_candidates_match
            and independent_alias_rows_match
            and independent_uncaptured_rejected
        ),
        "independent_verifier_freezes_then_recomputes_then_rechecks_freshness": bool(
            independent_manifest_load_index < independent_heat_recompute_index
            < independent_final_freshness_index
            and "day_reader=day_snapshot.read_rows" in independent_compare_source
            and "evaluated_list = [*row_list, *excluded_list]" in independent_compare_source
            and "production_result_post_recompute_unchanged" in independent_compare_source
        ),
        "main_verifier_frozen_reader_handles_132_and_rejects_uncaptured": bool(
            verifier_132_rows_before == verifier_132_rows_after
            and len(verifier_132_rows_before) == 1
            and abs(float(verifier_132_rows_before[0]["close"]) - 123.45) < 1e-12
            and verifier_uncaptured_rejected
        ),
        "main_verifier_day_race_event_is_structured_persisted_and_retryable": bool(
            verifier_race_returncode == 3
            and verifier_race_report.get("status") == "FAIL"
            and verifier_race_report.get("schema") == "TDX-CONVERTIBLE-BOND-VERIFY-FAIL-1"
            and verifier_race_report.get("retry_event") == verifier_race_event
            and verifier_race_event.get("failure_code") == entry_module.TDX_DAY_UPDATE_RACE
            and verifier_race_event.get("retryable") is True
            and verifier_race_event.get("run_id") == retry_contract_run_id
            and verifier_race_event.get("attempt") == 2
            and verifier_race_event.get("mismatch_count") == 1
        ),
        "main_verifier_fails_fast_then_recomputes_frozen_then_rechecks_freshness": bool(
            verifier_manifest_failfast_index < verifier_heat_recompute_index
            < verifier_final_freshness_index
            and "day_reader=frozen_day_reader.read_rows" in main_verifier_impl_source
        ),
        "missing_component_zero_and_unrenormalized": missing_component["earned_score"] == 0.0
        and missing_component["coverage_fraction"] == 0.0,
        "partial_component_coverage_exact": partial_component["coverage_fraction"] == 0.3,
        "c9_highest_heat_beats_composite_factor_decoy": bool(
            c9_adversarial_best["name"] == "热度优先"
            and c9_adversarial_best["normalized_heat"] == 0.9
            and "normalized_factor" not in c9_adversarial_best
            and abs(float(c9_adversarial["normalized_score"]) - 0.72) < 1e-12
            and abs(float(c9_adversarial["earned_score"]) - 5.76) < 1e-12
        ),
        "c9_normalization_rule_exact": scanner.C9_NORMALIZATION_RULE
        == "30% industry percentile heat + 40% highest concept heat score + 30% underlying trend",
        "independent_c9_matches_and_detects_tamper": heat_verifier._c9_component_matches(
            production_c9_core, independent_c9
        )
        and not heat_verifier._c9_component_matches(tampered_c9, independent_c9),
        "process_tree_runner_available": callable(run_process_tree),
        "golden_ignition_is_universal": "通用黄金点火" in golden_text and "可转债正股映射" in golden_text,
        "all_dependency_selftests_pass": all(item["status"] == "PASS" for item in dependency_runs),
    }
    payload = {
        "schema": "CONVERTIBLE-BOND-SCREENING-SELFTEST-2",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "run_id": run_id,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "checks": checks,
        "compile_errors": compile_errors,
        "weights": weights,
        "contract_readback": {
            "cutoff_trade_date": formula_cutoff,
            "required_scr_dates": required_scr_dates,
            "routine_dependencies": list(DEPENDENCIES),
            "source_missing_tnf_fixture_retained": [item["symbol"] for item in fixture_bonds],
            "missing_day_manifest_complete": missing_day_manifest["complete"],
            "invalid_day_manifest_complete": invalid_day_manifest["complete"],
            "immutable_day_manifest": immutable_day_manifest,
            "snapshot_current_before": snapshot_current_before,
            "snapshot_current_after": snapshot_current_after,
            "snapshot_after_diagnostics": snapshot_after_diagnostics,
            "independent_raw_alias_parts": independent_raw_parts,
            "independent_suffix_alias_parts": independent_suffix_parts,
            "main_verifier_132_rows": verifier_132_rows_before,
            "main_verifier_race_event": verifier_race_event,
            "main_verifier_race_report": verifier_race_report,
            "retry_classifier_exact_scanner_event": retry_classifier_exact_scan,
            "retry_classifier_exact_verifier_event": retry_classifier_exact_verify,
            "entry_output_disconnect_nonfatal": detached_invoke_elapsed is not None,
            "c9_adversarial_selected_concept": c9_adversarial_best,
            "c9_adversarial_earned_score": c9_adversarial["earned_score"],
            "redemption_snapshot_meta": loaded_redemption_meta,
            "redemption_status_map": verifier_redemption_map,
            "hard_exclusion_boundary_readback": {
                "z_prefix": hard_z_prefix,
                "daily_ratio_boundary": hard_daily_ratio_boundary,
                "daily_gain_boundary": hard_daily_gain_boundary,
                "daily_triggered": hard_daily_triggered,
                "scr90_zero": hard_scr90_zero,
                "scr90_positive": hard_scr90_positive,
                "scr90_unavailable": hard_scr90_unavailable,
                "turnover_boundary": hard_turnover_boundary,
                "turnover_triggered": hard_turnover_triggered,
                "price_boundary": hard_price_boundary,
                "price_triggered": hard_price_triggered,
                "announced": hard_announced,
                "no_match": hard_no_match,
                "unverified": hard_unverified,
            },
            "dual_pool_contract_checks": dual_pool_checks,
            "empty_result_failed_checks": empty_result_report.get("failed_checks", []),
            "alternate_root_failed_checks": alternate_root_report.get("failed_checks", []),
            "malformed_verification": malformed_verification,
            "argument_failure": argument_failure,
        },
        "tdx_readback": {
            "bond_path": str(bond_path),
            "bond_date": bond_parsed["date"],
            "bond_close": bond_parsed["close"],
            "stock_path": str(stock_path),
            "stock_date": stock_parsed["date"],
            "stock_close": stock_parsed["close"],
        },
        "dependency_selftests": dependency_runs,
        "source_artifacts": [
            artifact(path)
            for path in [ROOT / "SKILL.md", ROOT / "agents" / "openai.yaml", *script_paths]
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(args.output, payload)
    readback = json.loads(args.output.read_text(encoding="utf-8"))
    if readback.get("status") != payload["status"] or readback.get("checks") != checks:
        raise RuntimeError("selftest JSON readback mismatch")
    print(json.dumps({
        "status": payload["status"],
        "output": str(args.output.resolve()),
        "size_bytes": args.output.stat().st_size,
        "sha256": sha256(args.output),
        "checks": checks,
    }, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
