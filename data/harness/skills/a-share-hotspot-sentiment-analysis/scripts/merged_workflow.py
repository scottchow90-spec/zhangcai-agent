#!/usr/bin/env python3
"""Run the merged A-share hotspot and sentiment production workflows."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import os
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "references" / "merge-config.json"
FAILURE_TOKENS = (
    '"status": "BLOCKED"',
    '"status":"BLOCKED"',
    '"status": "FAILED"',
    '"status":"FAILED"',
    '"status": "FAIL"',
    '"status":"FAIL"',
    '"status": "ERROR"',
    '"status":"ERROR"',
    '"status": "PROCEDURAL"',
    '"status":"PROCEDURAL"',
    '"status": "DATA_REQUIRED"',
    '"status":"DATA_REQUIRED"',
    '"status": "DATA_STALE"',
    '"status":"DATA_STALE"',
    "Traceback (most recent call last)",
)
NON_BUSINESS_TOKENS = (
    '"mode": "doctor"',
    '"mode":"doctor"',
    "provide --input-dir and --out-dir",
)


def _windows_io_path(path: Path | str) -> Path:
    path = Path(path)
    absolute = str(path.absolute())
    if os.name == "nt" and len(absolute) >= 260 and not absolute.startswith("\\\\?\\"):
        return Path("\\\\?\\" + absolute)
    return path


def _write_text(path: Path | str, content: str) -> None:
    _windows_io_path(path).write_text(content, encoding="utf-8")


def _read_json(path: Path | str) -> dict:
    return json.loads(_windows_io_path(path).read_text(encoding="utf-8"))


def _component_step(
    name: str,
    source: str,
    args: list[str],
    required_artifacts: list[Path | str],
    timeout: int = 1800,
    fallback: str = "",
) -> dict:
    return {
        "name": name,
        "source": source,
        "args": args,
        "required_artifacts": [str(path) for path in required_artifacts],
        "timeout": timeout,
        "fallback": fallback,
    }


def _selected_modes(arguments: list[str]) -> tuple[str, list[str], list[str]]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    modes = config["modes"]
    aliases = {
        alias.casefold(): mode
        for mode, spec in modes.items()
        for alias in [mode, *spec.get("aliases", [])]
    }
    requested = arguments[0].casefold() if arguments else config["default_mode"]
    if requested == "all":
        if len(arguments) > 1:
            raise ValueError("all_mode_does_not_accept_component_specific_args")
        return "all", [], [
            mode
            for mode, spec in modes.items()
            if spec.get("include_in_all", True)
        ]
    mode = aliases.get(requested)
    if mode is None:
        raise ValueError(f"unknown_mode:{requested}")
    return mode, arguments[1:], [mode]


def build_execution_plan(
    arguments: list[str],
    *,
    run_root: Path,
    target_day: date,
) -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    requested_mode, extra, selected = _selected_modes(arguments)
    day = target_day.strftime("%Y%m%d")
    sentiment_dir = run_root / "sentiment"
    components: list[dict] = []

    for mode in selected:
        spec = config["modes"][mode]
        source = spec["source"]
        if extra and mode != "data":
            components.append({
                "mode": mode,
                "source": source,
                "display_name": spec["display_name"],
                "steps": [_component_step("custom", source, list(extra), [])],
            })
            continue
        if mode == "sentiment":
            artifacts = [
                sentiment_dir / "a_share_sentiment_event_pool.json",
                sentiment_dir / "a_share_sentiment_raw_event_pool.json",
                sentiment_dir / "a_share_sentiment_unified_event_pool.json",
                sentiment_dir / "a_share_sentiment_market_validation_pool.json",
                sentiment_dir / "a_share_sentiment_mandatory_sources_audit.json",
                sentiment_dir / "a_share_sentiment_market_cross_validation_audit.json",
                sentiment_dir / "a_share_sentiment_acquisition_preflight.json",
                sentiment_dir / "a_share_sentiment_acquisition_audit.json",
                sentiment_dir / "a_share_sentiment_clusters.json",
                sentiment_dir / "a_share_sentiment_scores.json",
                sentiment_dir / "a_share_sentiment_audit.json",
                sentiment_dir / "a_share_sentiment_redline_audit.json",
                sentiment_dir / "a_share_sentiment_delivery_audit.json",
                sentiment_dir / "a_share_sentiment_word_render_audit.json",
                sentiment_dir / "a_share_sentiment_source_integration_audit.json",
                sentiment_dir / "a_share_sentiment_daily_intel_view.json",
                sentiment_dir / "a_share_sentiment_short_term_sentiment_view.json",
                sentiment_dir / "a_share_sentiment_conflict_register.json",
                sentiment_dir / "A股三日舆情解读结果_Codex自动生成.docx",
            ]
            steps = [
                _component_step(
                    "generate",
                    source,
                    ["generate", "--out-dir", str(sentiment_dir)],
                    artifacts,
                    fallback="sentiment_public_readonly",
                )
            ]
        elif mode == "data":
            args = list(extra)
            output_path = run_root / "duanxianxia_public_snapshot.json"
            output_indexes = [
                index
                for index, value in enumerate(args)
                if value.casefold() == "-output"
            ]
            if output_indexes:
                output_index = output_indexes[-1]
                if output_index + 1 >= len(args):
                    raise ValueError("data_mode_output_path_missing")
                output_path = Path(args[output_index + 1])
            else:
                args.extend(["-Output", str(output_path)])
            steps = [
                _component_step(
                    "collect",
                    source,
                    args,
                    [output_path],
                    timeout=180,
                )
            ]
            steps[0]["runner"] = "powershell"
        else:
            raise ValueError(f"unsupported_mode:{mode}")
        components.append({
            "mode": mode,
            "source": source,
            "display_name": spec["display_name"],
            "steps": steps,
        })
    return {
        "mode": requested_mode,
        "target_date": day,
        "components": components,
        "closure_artifacts": [str(run_root / "merged_closure_audit.json")],
    }


def _fresh_matches(value: str, started_at: float) -> list[str]:
    path = Path(value)
    matches = list(path.parent.glob(path.name)) if "*" in path.name else [path]
    return [
        str(match)
        for match in matches
        if _windows_io_path(match).is_file()
        and _windows_io_path(match).stat().st_size > 0
        and _windows_io_path(match).stat().st_mtime >= started_at - 2
    ]


def is_business_success(
    returncode: int,
    stdout: str,
    stderr: str,
    required_artifacts: list[str],
    *,
    started_at: float,
) -> bool:
    combined = stdout + "\n" + stderr
    if returncode != 0:
        return False
    if any(token in combined for token in (*FAILURE_TOKENS, *NON_BUSINESS_TOKENS)):
        return False
    return all(_fresh_matches(value, started_at) for value in required_artifacts)


def sentiment_delivery_audit_is_closed(payload: dict) -> bool:
    sentiment = payload.get("short_term_sentiment") or {}
    return (
        payload.get("ok") is True
        and (payload.get("mandatory_sentiment_sources") or {}).get("ok") is True
        and (payload.get("market_cross_validation") or {}).get("ok") is True
        and sentiment.get("label")
        in {"强势", "偏强", "中性分化", "偏弱", "退潮"}
    )


def _run_step(step: dict, run_root: Path) -> dict:
    source = step["source"]
    if step.get("runner") == "powershell":
        component_root = ROOT
        entry = ROOT / "scripts" / "duanxianxia_client.ps1"
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(entry),
            *step["args"],
        ]
    else:
        component_root = ROOT / "components" / source
        entry = component_root / "scripts" / "legacy_codex_entry.py"
        command = [sys.executable, str(entry), "run", "--", *step["args"]]
    environment = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "ONESTOCK_STOCK_CANONICAL_CHILD": "1",
    }
    started_at = time.time()
    try:
        completed = subprocess.run(
            command,
            cwd=str(component_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=environment,
            timeout=step["timeout"],
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        stderr += f"\nTIMEOUT after {step['timeout']}s"
    stem = f"{source}.{step['name']}"
    stdout_path = run_root / f"{stem}.stdout.txt"
    stderr_path = run_root / f"{stem}.stderr.txt"
    _write_text(stdout_path, stdout)
    _write_text(stderr_path, stderr)
    artifacts = {
        value: _fresh_matches(value, started_at)
        for value in step["required_artifacts"]
    }
    accepted = is_business_success(
        returncode,
        stdout,
        stderr,
        step["required_artifacts"],
        started_at=started_at,
    )
    return {
        "name": step["name"],
        "command": command,
        "returncode": returncode,
        "status": "PASS" if accepted else "BLOCKED",
        "fallback": step.get("fallback", ""),
        "artifacts": artifacts,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }


def execute_plan(plan: dict, run_root: Path) -> list[dict]:
    results: list[dict] = []
    for component in plan["components"]:
        steps: list[dict] = []
        for step in component["steps"]:
            if steps and steps[-1]["status"] != "PASS":
                steps.append({
                    "name": step["name"],
                    "status": "BLOCKED",
                    "reason": "previous_step_failed",
                })
                break
            steps.append(_run_step(step, run_root))
        accepted = bool(steps) and all(step["status"] == "PASS" for step in steps)
        results.append({
            "mode": component["mode"],
            "source": component["source"],
            "display_name": component["display_name"],
            "status": "PASS" if accepted else "BLOCKED",
            "steps": steps,
        })
    return results


def write_closure_audit(plan: dict, results: list[dict], run_root: Path) -> dict:
    reasons: list[str] = []
    artifacts: list[str] = []
    for component in results:
        if component.get("status") != "PASS":
            reasons.append(f"component_not_pass:{component.get('mode', '')}")
        for step in component.get("steps", []):
            if step.get("status") != "PASS":
                reasons.append(
                    f"step_not_pass:{component.get('mode', '')}:{step.get('name', '')}"
                )
            for required, matches in (step.get("artifacts") or {}).items():
                if not matches:
                    reasons.append(f"fresh_artifact_missing:{required}")
                artifacts.extend(matches)
    sentiment_dir = run_root / "sentiment"
    json_checks = [
        (
            sentiment_dir / "a_share_sentiment_delivery_audit.json",
            sentiment_delivery_audit_is_closed,
            "sentiment_delivery_audit_not_ok",
        ),
        (
            sentiment_dir / "a_share_sentiment_redline_audit.json",
            lambda payload: payload.get("ok") is True,
            "sentiment_redline_audit_not_ok",
        ),
        (
            sentiment_dir / "a_share_sentiment_mandatory_sources_audit.json",
            lambda payload: payload.get("ok") is True,
            "sentiment_mandatory_sources_audit_not_ok",
        ),
        (
            sentiment_dir / "a_share_sentiment_market_cross_validation_audit.json",
            lambda payload: payload.get("ok") is True,
            "sentiment_market_cross_validation_audit_not_ok",
        ),
        (
            sentiment_dir / "a_share_sentiment_word_render_audit.json",
            lambda payload: (
                payload.get("status") == "PASS"
                and payload.get("errors") == []
                and bool(payload.get("checks"))
                and all((payload.get("checks") or {}).values())
            ),
            "sentiment_word_render_audit_not_ok",
        ),
        (
            sentiment_dir / "a_share_sentiment_source_integration_audit.json",
            lambda payload: (
                payload.get("ok") is True
                and payload.get("architecture") == "one_evidence_pool_multiple_derived_views"
                and payload.get("preset_sector_pool_used") is False
                and payload.get("runtime_dependencies_on_excluded_workflows") == []
                and all((payload.get("derived_view_checks") or {}).values())
            ),
            "sentiment_source_integration_audit_not_ok",
        ),
    ]
    selected_modes = {component.get("mode") for component in results}
    if "sentiment" not in selected_modes:
        json_checks = [
            item for item in json_checks
            if not str(item[0]).startswith(str(sentiment_dir))
        ]
    for path, predicate, reason in json_checks:
        try:
            payload = _read_json(path)
        except Exception as exc:
            reasons.append(f"{reason}:{type(exc).__name__}")
            continue
        if not predicate(payload):
            reasons.append(reason)
    docx_paths = []
    if "sentiment" in selected_modes:
        docx_paths.append(
            sentiment_dir / "A股三日舆情解读结果_Codex自动生成.docx"
        )
    for path in docx_paths:
        io_path = _windows_io_path(path)
        if not io_path.is_file() or io_path.stat().st_size <= 20000:
            reasons.append(f"docx_missing_or_too_small:{path}")
    payload = {
        "schema": "A_SHARE_HOTSPOT_SENTIMENT_CLOSURE_AUDIT_V1",
        "status": "PASS" if not reasons else "BLOCKED",
        "mode": plan["mode"],
        "target_date": plan["target_date"],
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "run_dir": str(run_root),
        "fresh_artifacts": sorted(set(artifacts)),
        "docx_paths": [str(path) for path in docx_paths],
        "reasons": reasons,
    }
    path = run_root / "merged_closure_audit.json"
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))
    payload["path"] = str(path)
    return payload


def main() -> int:
    data_root = Path(
        os.environ.get("ONESTOCK_STOCK_DATA_ROOT", str(ROOT / "reports"))
    ).resolve()
    run_root = (
        data_root
        / ROOT.name
        / "merged-components"
        / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    )
    try:
        plan = build_execution_plan(
            sys.argv[1:],
            run_root=run_root,
            target_day=date.today(),
        )
    except ValueError as exc:
        print(json.dumps({
            "schema": "MERGED_STOCK_SKILL_RESULT_V2",
            "skill_id": ROOT.name,
            "status": "BLOCKED",
            "errors": [str(exc)],
        }, ensure_ascii=False))
        return 2
    run_root.mkdir(parents=True, exist_ok=False)
    results = execute_plan(plan, run_root)
    closure = write_closure_audit(plan, results, run_root)
    accepted = (
        all(item["status"] == "PASS" for item in results)
        and closure["status"] == "PASS"
    )
    payload = {
        "schema": "MERGED_STOCK_SKILL_RESULT_V2",
        "skill_id": ROOT.name,
        "mode": plan["mode"],
        "target_date": plan["target_date"],
        "status": "PASS" if accepted else "BLOCKED",
        "components": results,
        "closure_audit": closure,
        "run_dir": str(run_root),
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if accepted else 2


if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
