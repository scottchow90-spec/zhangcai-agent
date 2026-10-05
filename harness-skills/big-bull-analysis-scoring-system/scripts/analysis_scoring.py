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
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from poster_builder import (
    render_composite_model_poster,
    render_composite_poster,
    render_composite_structure_poster,
)
from scoring_mode_gate import normalize_business_args
from three_formula_composite_backtest import validate_cross_board_score_consistency


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ANALYSIS = SCRIPTS / "daniuxian_analysis.py"
SCORING = SCRIPTS / "big_bull_scoring.py"
DRAGON_BACKTEST = SCRIPTS / "dragon_pullback_formula_backtest.py"
COMPOSITE_BACKTEST = SCRIPTS / "three_formula_composite_backtest.py"
COMPOSITE_WEIGHTS = ROOT / "assets" / "three_formula_composite_weights.json"
LIGHT_BACKGROUND_GATE = (
    ROOT.parents[1] / "scripts" / "poster_light_background_gate.py"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_child(command: list[str], timeout: int = 300) -> dict[str, Any]:
    environment = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "ONESTOCK_STOCK_CANONICAL_CHILD": "1",
    }
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=environment,
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "returncode": 124,
            "stdout": stdout,
            "stderr": stderr + f"\nTIMEOUT after {timeout}s",
            "timed_out": True,
        }


def write_result(output_dir: Path, payload: dict[str, Any]) -> Path:
    path = output_dir / "result.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def last_json_object(text: str) -> dict[str, Any] | None:
    for line in reversed(text.splitlines()):
        candidate = line.strip()
        if not candidate.startswith("{"):
            continue
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def json_object_from_output(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text.strip())
    except json.JSONDecodeError:
        return last_json_object(text)
    return payload if isinstance(payload, dict) else None


def run_analysis(output_dir: Path, args: list[str]) -> dict[str, Any]:
    if not args:
        raise ValueError("分析模式必须提供股票代码")
    code = args[0]
    remaining = list(args[1:])
    report = output_dir / "analysis_report.txt"
    poster = output_dir / "poster.png"
    preview = output_dir / "poster-preview-1920x1080.png"
    poster_validation_path = output_dir / "analysis_poster_validation.json"
    if "--output" not in remaining and "-o" not in remaining:
        remaining.extend(["--output", str(report)])
    if "--poster" not in remaining:
        remaining.extend(["--poster", str(poster)])
    if "--poster-validation" not in remaining:
        remaining.extend(["--poster-validation", str(poster_validation_path)])
    command = [sys.executable, str(ANALYSIS), code, *remaining]
    child = run_child(command)
    stdout_path = output_dir / "analysis_stdout.txt"
    stderr_path = output_dir / "analysis_stderr.txt"
    stdout_path.write_text(child["stdout"], encoding="utf-8")
    stderr_path.write_text(child["stderr"], encoding="utf-8")
    poster_validation = None
    if poster_validation_path.is_file():
        poster_validation = json.loads(poster_validation_path.read_text(encoding="utf-8"))
    accepted = (
        child["returncode"] == 0
        and report.is_file()
        and poster.is_file()
        and preview.is_file()
        and isinstance(poster_validation, dict)
        and poster_validation.get("passed") is True
    )
    return {
        "schema": "BIG_BULL_ANALYSIS_SCORING_RESULT_V1",
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "mode": "分析",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "input": {"code": code},
        "business_process": {
            "command": command,
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
        },
        "artifacts": {
            "analysis_report": {
                "path": str(report),
                "sha256": sha256_file(report) if report.is_file() else None,
            },
            "poster": {
                "path": str(poster),
                "sha256": sha256_file(poster) if poster.is_file() else None,
                "validation": poster_validation,
            },
            "preview": {
                "path": str(preview),
                "sha256": sha256_file(preview) if preview.is_file() else None,
            },
            "poster_validation": {
                "path": str(poster_validation_path),
                "sha256": sha256_file(poster_validation_path)
                if poster_validation_path.is_file()
                else None,
            },
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        },
    }


def run_scoring(output_dir: Path, args: list[str]) -> dict[str, Any]:
    command = [sys.executable, str(SCORING), "--output-dir", str(output_dir), *args]
    child = run_child(command)
    stdout_path = output_dir / "scoring_stdout.txt"
    stderr_path = output_dir / "scoring_stderr.txt"
    stdout_path.write_text(child["stdout"], encoding="utf-8")
    stderr_path.write_text(child["stderr"], encoding="utf-8")
    ranking = output_dir / "ranking.json"
    poster = output_dir / "poster.png"
    accepted = child["returncode"] == 0 and ranking.is_file() and poster.is_file()
    return {
        "schema": "BIG_BULL_ANALYSIS_SCORING_RESULT_V1",
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "mode": "评分",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "business_process": {
            "command": command,
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
        },
        "artifacts": {
            "ranking": {
                "path": str(ranking),
                "sha256": sha256_file(ranking) if ranking.is_file() else None,
            },
            "poster": {
                "path": str(poster),
                "sha256": sha256_file(poster) if poster.is_file() else None,
            },
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        },
    }


def run_dragon_backtest(output_dir: Path, args: list[str]) -> dict[str, Any]:
    command = [
        sys.executable,
        str(DRAGON_BACKTEST),
        "--output-dir",
        str(output_dir),
        *args,
    ]
    child = run_child(command, timeout=1500)
    stdout_path = output_dir / "backtest_stdout.txt"
    stderr_path = output_dir / "backtest_stderr.txt"
    stdout_path.write_text(child["stdout"], encoding="utf-8")
    stderr_path.write_text(child["stderr"], encoding="utf-8")
    report = output_dir / "龙回头真实历史回测.md"
    summary = output_dir / "龙回头真实历史回测.json"
    events = output_dir / "龙回头真实历史明细.csv"
    accepted = (
        child["returncode"] == 0
        and report.is_file()
        and summary.is_file()
        and events.is_file()
    )
    return {
        "schema": "BIG_BULL_ANALYSIS_SCORING_RESULT_V1",
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "mode": "龙回头历史回测",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "business_process": {
            "command": command,
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
        },
        "artifacts": {
            "report": {
                "path": str(report),
                "sha256": sha256_file(report) if report.is_file() else None,
            },
            "summary": {
                "path": str(summary),
                "sha256": sha256_file(summary) if summary.is_file() else None,
            },
            "events": {
                "path": str(events),
                "sha256": sha256_file(events) if events.is_file() else None,
            },
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        },
    }


def run_composite_backtest(output_dir: Path, args: list[str]) -> dict[str, Any]:
    command = [
        sys.executable,
        str(COMPOSITE_BACKTEST),
        "--output-dir",
        str(output_dir),
        "--sync-model-state-to",
        str(COMPOSITE_WEIGHTS),
        *args,
    ]
    child = run_child(command, timeout=1800)
    stdout_path = output_dir / "composite_backtest_stdout.txt"
    stderr_path = output_dir / "composite_backtest_stderr.txt"
    stdout_path.write_text(child["stdout"], encoding="utf-8")
    stderr_path.write_text(child["stderr"], encoding="utf-8")
    report = output_dir / "三公式综合评分回测报告.md"
    summary = output_dir / "三公式综合评分回测证据.json"
    weights = output_dir / "三公式综合评分正式模型.json"
    rows = output_dir / "三公式综合评分样本外明细.csv"
    accepted = (
        child["returncode"] == 0
        and report.is_file()
        and summary.is_file()
        and weights.is_file()
        and rows.is_file()
    )
    return {
        "schema": "BIG_BULL_ANALYSIS_SCORING_RESULT_V1",
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "mode": "三公式综合评分历史回测",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "business_process": {
            "command": command,
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
        },
        "artifacts": {
            "report": {
                "path": str(report),
                "sha256": sha256_file(report) if report.is_file() else None,
            },
            "summary": {
                "path": str(summary),
                "sha256": sha256_file(summary) if summary.is_file() else None,
            },
            "weights": {
                "path": str(weights),
                "sha256": sha256_file(weights) if weights.is_file() else None,
            },
            "test_rows": {
                "path": str(rows),
                "sha256": sha256_file(rows) if rows.is_file() else None,
            },
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        },
    }


def run_composite_state_sync(output_dir: Path, args: list[str]) -> dict[str, Any]:
    if not args:
        raise ValueError("综合评分状态同步缺少V5正式状态源文件")
    source = Path(args[0]).expanduser().resolve()
    if len(args) > 1:
        raise ValueError(f"综合评分状态同步存在多余参数：{args[1:]}")
    command = [
        sys.executable,
        str(COMPOSITE_BACKTEST),
        "--output-dir",
        str(output_dir),
        "--sync-model-state-from",
        str(source),
        "--sync-model-state-to",
        str(COMPOSITE_WEIGHTS),
    ]
    child = run_child(command, timeout=60)
    stdout_path = output_dir / "composite_state_sync_stdout.txt"
    stderr_path = output_dir / "composite_state_sync_stderr.txt"
    stdout_path.write_text(child["stdout"], encoding="utf-8")
    stderr_path.write_text(child["stderr"], encoding="utf-8")
    receipt_path = output_dir / "三公式综合评分状态同步收据.json"
    snapshot_path = output_dir / "三公式综合评分同步后模型状态.json"
    receipt = (
        json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt_path.is_file()
        else None
    )
    accepted = (
        child["returncode"] == 0
        and isinstance(receipt, dict)
        and receipt.get("methodology_version")
        == "THREE_FORMULA_COMPOSITE_V5_TRADABLE_STABLE_OOS"
        and receipt.get("status") in {"CLEAN_PASS", "PREDICTIVE_REJECTED"}
        and receipt.get("target") == str(COMPOSITE_WEIGHTS.resolve())
        and snapshot_path.is_file()
        and COMPOSITE_WEIGHTS.is_file()
        and sha256_file(snapshot_path) == sha256_file(COMPOSITE_WEIGHTS)
    )
    return {
        "schema": "BIG_BULL_ANALYSIS_SCORING_RESULT_V1",
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "mode": "三公式综合评分正式状态同步",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "business_outcome": receipt,
        "business_process": {
            "command": command,
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
        },
        "artifacts": {
            "sync_receipt": {
                "path": str(receipt_path),
                "sha256": sha256_file(receipt_path) if receipt_path.is_file() else None,
            },
            "synced_state": {
                "path": str(snapshot_path),
                "sha256": sha256_file(snapshot_path) if snapshot_path.is_file() else None,
            },
            "formal_state": {
                "path": str(COMPOSITE_WEIGHTS),
                "sha256": sha256_file(COMPOSITE_WEIGHTS)
                if COMPOSITE_WEIGHTS.is_file()
                else None,
            },
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        },
    }


def run_composite_scoring(
    output_dir: Path,
    args: list[str],
    timeout: int = 900,
) -> dict[str, Any]:
    ranking_json = output_dir / "三公式综合评分最新排名.json"
    ranking_csv = output_dir / "三公式综合评分最新排名.csv"
    contributions = output_dir / "三公式综合评分30项贡献明细.csv"
    report = output_dir / "三公式综合评分最新排名报告.md"
    poster = output_dir / "三公式综合评分8K海报.png"
    preview = poster.with_name(f"{poster.stem}-preview-1920x1080.png")
    for path in (
        ranking_json,
        ranking_csv,
        contributions,
        report,
        poster,
        preview,
    ):
        path.unlink(missing_ok=True)
    command = [
        sys.executable,
        str(COMPOSITE_BACKTEST),
        "--output-dir",
        str(output_dir),
        "--score-only",
        "--weights-file",
        str(COMPOSITE_WEIGHTS),
        *args,
    ]
    child = run_child(command, timeout=timeout)
    stdout_path = output_dir / "composite_scoring_stdout.txt"
    stderr_path = output_dir / "composite_scoring_stderr.txt"
    stdout_path.write_text(child["stdout"], encoding="utf-8")
    stderr_path.write_text(child["stderr"], encoding="utf-8")
    child_payload = last_json_object(child["stdout"])
    poster_validation: dict[str, Any] | None = None
    poster_error: str | None = None
    if child["returncode"] == 0 and ranking_json.is_file():
        try:
            ranking_payload = json.loads(ranking_json.read_text(encoding="utf-8"))
            poster_validation = render_composite_poster(ranking_payload, poster)
        except Exception as exc:
            poster_error = f"{type(exc).__name__}:{exc}"
    accepted = (
        child["returncode"] == 0
        and ranking_json.is_file()
        and ranking_csv.is_file()
        and contributions.is_file()
        and report.is_file()
        and poster.is_file()
        and preview.is_file()
        and isinstance(poster_validation, dict)
        and poster_validation.get("passed") is True
    )
    return {
        "schema": "BIG_BULL_ANALYSIS_SCORING_RESULT_V1",
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "mode": "三公式综合评分",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "business_process": {
            "command": command,
            "returncode": child["returncode"],
            "timed_out": child["timed_out"],
        },
        "date_gate": (
            child_payload.get("date_gate")
            if isinstance(child_payload, dict)
            else None
        ),
        "error": (
            poster_error or child_payload.get("error")
            if isinstance(child_payload, dict)
            else poster_error
        ),
        "artifacts": {
            "ranking_json": {
                "path": str(ranking_json),
                "sha256": sha256_file(ranking_json) if ranking_json.is_file() else None,
            },
            "ranking_csv": {
                "path": str(ranking_csv),
                "sha256": sha256_file(ranking_csv) if ranking_csv.is_file() else None,
            },
            "contributions": {
                "path": str(contributions),
                "sha256": sha256_file(contributions) if contributions.is_file() else None,
            },
            "report": {
                "path": str(report),
                "sha256": sha256_file(report) if report.is_file() else None,
            },
            "poster": {
                "path": str(poster),
                "sha256": sha256_file(poster) if poster.is_file() else None,
                "validation": poster_validation,
            },
            "preview": {
                "path": str(preview),
                "sha256": sha256_file(preview) if preview.is_file() else None,
            },
            "weights": {
                "path": str(COMPOSITE_WEIGHTS),
                "sha256": sha256_file(COMPOSITE_WEIGHTS)
                if COMPOSITE_WEIGHTS.is_file()
                else None,
            },
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        },
    }


def run_research_composite_scoring(
    output_dir: Path,
    args: list[str],
    timeout: int = 900,
) -> dict[str, Any]:
    return run_composite_scoring(
        output_dir,
        ["--research-structural", *args],
        timeout=timeout,
    )


def run_cross_board_consistency_gate(
    output_dir: Path,
    args: list[str],
) -> dict[str, Any]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--ranking-json", action="append", required=True)
    parsed, extras = parser.parse_known_args(args)
    if extras:
        raise ValueError(f"跨板一致性门禁存在未知参数：{extras}")
    paths = [Path(value).expanduser().resolve() for value in parsed.ranking_json]
    if len(paths) < 2:
        raise ValueError("跨板一致性门禁至少需要两份排名")
    payloads = [_read_json_object(path) for path in paths]
    validation = validate_cross_board_score_consistency(payloads)
    return {
        "schema": "BIG_BULL_CROSS_BOARD_CONSISTENCY_V1",
        "status": "CLEAN_PASS",
        "mode": "固定30项跨板一致性门禁",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "validation": validation,
        "sources": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in paths
        ],
    }


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON根节点不是对象：{path}")
    return payload


def _receipt_bound_sha256(receipt: dict[str, Any], path: Path) -> str:
    for item in receipt.get("required_artifacts", []):
        candidate = Path(str(item.get("path", ""))).resolve()
        if candidate == path.resolve():
            return str(item.get("sha256", ""))
    raise ValueError(f"来源回执未绑定文件：{path.name}")


def _assert_artifact_binding(
    artifact: dict[str, Any],
    expected_path: Path,
    expected_sha256: str,
) -> None:
    if (
        Path(str(artifact.get("path", ""))).resolve() != expected_path.resolve()
        or str(artifact.get("sha256", "")) != expected_sha256
    ):
        raise ValueError(f"来源产物绑定不一致：{expected_path.name}")


def _validate_refresh_ranking(payload: dict[str, Any]) -> dict[str, Any]:
    if (
        payload.get("status") != "CLEAN_PASS"
        or payload.get("scoring_mode") != "RESEARCH_STRUCTURAL"
        or payload.get("research_only") is not True
        or payload.get("prediction_authorized") is not False
    ):
        raise ValueError("来源排名不是通过状态的研究型结构评分")
    today = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d")
    if str(payload.get("score_date", "")) != today:
        raise ValueError("来源排名不是北京时间当日评分")

    board = payload.get("board", {})
    board_path = Path(str(board.get("path", ""))).resolve()
    if not board_path.is_file() or sha256_file(board_path) != board.get("sha256"):
        raise ValueError("通达信板块文件已变化，禁止重绘旧排名")
    rows = list(payload.get("ranking", []))
    expected_count = int(board.get("constituent_count", -1))
    if (
        expected_count <= 0
        or int(payload.get("stock_count", -1)) != expected_count
        or len(rows) != expected_count
        or len({str(row.get("symbol", "")) for row in rows}) != expected_count
        or payload.get("delivery_validation", {}).get("status") != "PASS"
    ):
        raise ValueError("来源排名未完整覆盖当前板块成分")

    expected_item_counts = {
        "大牛线撑压版": 16,
        "飞龙在天": 10,
        "庄家资金监控": 4,
    }
    expected_weights = {
        "大牛线撑压版": 40.0,
        "飞龙在天": 35.0,
        "庄家资金监控": 25.0,
    }
    for row in rows:
        contributions = list(row.get("contributions", []))
        actual_counts = {
            name: sum(1 for item in contributions if item.get("formula") == name)
            for name in expected_item_counts
        }
        weights = row.get("fusion", {}).get("top_level_weights", {})
        if (
            len(contributions) != 30
            or actual_counts != expected_item_counts
            or any(float(weights.get(name, -1)) != value for name, value in expected_weights.items())
            or abs(sum(float(weights.get(name, 0)) for name in expected_weights) - 100.0) > 1e-8
        ):
            raise ValueError(f"来源排名30项或三体系权重不完整：{row.get('symbol')}")
    return {
        "board": board.get("name"),
        "stock_count": expected_count,
        "fixed_item_count": 30,
        "top_level_weights": expected_weights,
        "top_level_weight_sum": 100.0,
    }


def run_composite_poster_refresh(
    output_dir: Path,
    args: list[str],
) -> dict[str, Any]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--ranking-json", required=True)
    parser.add_argument("--source-receipt", required=True)
    parsed, extras = parser.parse_known_args(args)
    if extras:
        raise ValueError(f"重绘综合评分海报存在未知参数：{extras}")

    ranking_path = Path(parsed.ranking_json).expanduser().resolve()
    receipt_path = Path(parsed.source_receipt).expanduser().resolve()
    if not ranking_path.is_file() or not receipt_path.is_file():
        raise FileNotFoundError("来源排名或来源回执不存在")
    receipt = _read_json_object(receipt_path)
    if (
        receipt.get("status") != "CLEAN_PASS"
        or receipt.get("skill_id") != "big-bull-analysis-scoring-system"
        or int(receipt.get("returncode", -1)) != 0
        or not str(receipt.get("receipt_integrity", ""))
    ):
        raise ValueError("来源运行回执不是干净通过状态")
    source_run = Path(str(receipt.get("run_dir", ""))).resolve()
    if ranking_path.parent != source_run / "deliverables":
        raise ValueError("来源排名不属于来源回执运行目录")

    business_path = source_run / "business_result.json"
    source_result_path = source_run / "deliverables" / "result.json"
    for bound_path in (business_path, source_result_path):
        expected_sha = _receipt_bound_sha256(receipt, bound_path)
        if not bound_path.is_file() or sha256_file(bound_path) != expected_sha:
            raise ValueError(f"来源回执绑定文件已变化：{bound_path.name}")
    business = _read_json_object(business_path)
    source_result = _read_json_object(source_result_path)
    if business.get("status") != "CLEAN_PASS" or source_result.get("status") != "CLEAN_PASS":
        raise ValueError("来源业务结果不是干净通过状态")
    ranking_sha = sha256_file(ranking_path)
    _assert_artifact_binding(
        business.get("artifacts", {}).get("三公式综合评分最新排名.json", {}),
        ranking_path,
        ranking_sha,
    )
    _assert_artifact_binding(
        source_result.get("artifacts", {}).get("ranking_json", {}),
        ranking_path,
        ranking_sha,
    )

    ranking_payload = _read_json_object(ranking_path)
    source_validation = _validate_refresh_ranking(ranking_payload)
    poster = output_dir / "三公式综合评分8K海报.png"
    preview = poster.with_name(f"{poster.stem}-preview-1920x1080.png")
    poster.unlink(missing_ok=True)
    preview.unlink(missing_ok=True)
    poster_validation = render_composite_poster(ranking_payload, poster)
    gate_child = run_child(
        [
            sys.executable,
            str(LIGHT_BACKGROUND_GATE),
            "--input",
            str(poster),
            "--expected-width",
            "7680",
            "--expected-height",
            "4320",
        ],
        timeout=120,
    )
    light_gate = json_object_from_output(gate_child["stdout"])
    accepted = (
        poster.is_file()
        and preview.is_file()
        and poster_validation.get("passed") is True
        and gate_child["returncode"] == 0
        and isinstance(light_gate, dict)
        and light_gate.get("status") == "PASS"
    )
    leader = ranking_payload["ranking"][0]
    return {
        "schema": "BIG_BULL_ANALYSIS_SCORING_RESULT_V1",
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "mode": "已验证综合评分排名海报重绘",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "business_outcome": {
            "board": source_validation["board"],
            "stock_count": source_validation["stock_count"],
            "leader": {
                "name": leader.get("name"),
                "symbol": leader.get("symbol"),
                "score": leader.get("score"),
            },
        },
        "source": {
            "ranking_json": {"path": str(ranking_path), "sha256": ranking_sha},
            "receipt": {"path": str(receipt_path), "sha256": sha256_file(receipt_path)},
            "run_dir": str(source_run),
        },
        "source_validation": source_validation,
        "artifacts": {
            "poster": {
                "path": str(poster),
                "sha256": sha256_file(poster) if poster.is_file() else None,
                "validation": poster_validation,
                "light_background_gate": light_gate,
            },
            "preview": {
                "path": str(preview),
                "sha256": sha256_file(preview) if preview.is_file() else None,
            },
        },
        "error": None if accepted else "poster_or_light_background_gate_failed",
    }


def run_composite_model_poster(
    output_dir: Path,
    args: list[str],
) -> dict[str, Any]:
    if args:
        raise ValueError(f"模型海报模式不接受额外参数：{args}")
    poster = output_dir / "三公式综合评分因子权重标准8K海报.png"
    poster.unlink(missing_ok=True)
    payload = json.loads(COMPOSITE_WEIGHTS.read_text(encoding="utf-8"))
    if payload.get("status") != "CLEAN_PASS" or not isinstance(
        payload.get("model"),
        dict,
    ):
        return {
            "schema": "BIG_BULL_ANALYSIS_SCORING_RESULT_V1",
            "status": "BLOCKED",
            "mode": "三公式综合评分模型说明海报",
            "error": "正式预测模型未通过，禁止生成模型权重海报",
            "model": {
                "path": str(COMPOSITE_WEIGHTS),
                "sha256": sha256_file(COMPOSITE_WEIGHTS),
                "status": payload.get("status"),
                "methodology_version": payload.get("methodology_version"),
                "model_is_null": payload.get("model") is None,
            },
            "artifacts": {},
        }
    validation = render_composite_model_poster(payload, poster)
    accepted = poster.is_file() and validation.get("passed") is True
    return {
        "schema": "BIG_BULL_ANALYSIS_SCORING_RESULT_V1",
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "mode": "三公式综合评分模型说明海报",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "model": {
            "path": str(COMPOSITE_WEIGHTS),
            "sha256": sha256_file(COMPOSITE_WEIGHTS),
            "status": payload.get("status"),
            "methodology_version": payload.get("methodology_version"),
            "predictive_validation": payload.get("predictive_validation", {}).get("status"),
        },
        "artifacts": {
            "poster": {
                "path": str(poster),
                "sha256": sha256_file(poster) if poster.is_file() else None,
                "validation": validation,
            },
        },
    }


def run_composite_structure_poster(
    output_dir: Path,
    args: list[str],
) -> dict[str, Any]:
    if len(args) != 2 or args[0] != "--weight-source":
        raise ValueError("评分结构海报必须提供 --weight-source <已执行模型结果JSON>")
    source = Path(args[1]).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    source_payload = json.loads(source.read_text(encoding="utf-8"))
    if source_payload.get("status") != "CLEAN_PASS" or not isinstance(
        source_payload.get("model"),
        dict,
    ):
        raise ValueError("评分结构权重来源不是已执行通过状态")

    current_model = json.loads(COMPOSITE_WEIGHTS.read_text(encoding="utf-8"))
    poster = output_dir / "大牛线综合评分系统30项权重分值8K海报.png"
    poster.unlink(missing_ok=True)
    preview = poster.with_name(f"{poster.stem}-preview-1920x1080.png")
    preview.unlink(missing_ok=True)
    generated_at = str(source_payload.get("generated_at", ""))
    date_text = generated_at[:10] if generated_at else "未标注"
    structural_payload = {
        "status": "CLEAN_PASS",
        "model": source_payload["model"],
        "weight_source_date": date_text,
        "current_model_status": current_model.get("status"),
    }
    validation = render_composite_structure_poster(structural_payload, poster)
    accepted = poster.is_file() and preview.is_file() and validation.get("passed") is True
    return {
        "schema": "BIG_BULL_ANALYSIS_SCORING_RESULT_V1",
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "mode": "综合评分结构海报",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "current_model_status": current_model.get("status"),
        "weight_source": {
            "path": str(source),
            "sha256": sha256_file(source),
            "generated_at": source_payload.get("generated_at"),
        },
        "artifacts": {
            "poster": {
                "path": str(poster),
                "sha256": sha256_file(poster) if poster.is_file() else None,
                "validation": validation,
            },
            "preview": {
                "path": str(preview),
                "sha256": sha256_file(preview) if preview.is_file() else None,
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="大牛线分析评分系统统一调度")
    parser.add_argument("--output-dir", required=True)
    parsed, business_args = parser.parse_known_args()
    output_dir = Path(parsed.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "result.json"
    result_path.unlink(missing_ok=True)

    mode = "unresolved"
    try:
        normalized_business_args = normalize_business_args(
            business_args,
            inherited_legacy_authorization=(
                os.environ.get("CODEX_BIG_BULL_LEGACY_COMPAT_AUTHORIZED") == "1"
            ),
        )
        mode = normalized_business_args[0]
        mode_args = normalized_business_args[1:]
        if mode in {"analyze", "分析"}:
            result = run_analysis(output_dir, mode_args)
        elif mode in {"score-board", "score", "评分"}:
            result = run_scoring(output_dir, mode_args)
        elif mode in {"backtest-dragon", "回测龙回头"}:
            result = run_dragon_backtest(output_dir, mode_args)
        elif mode in {"backtest-composite", "回测综合评分"}:
            result = run_composite_backtest(output_dir, mode_args)
        elif mode in {"sync-composite-state", "同步综合评分状态"}:
            result = run_composite_state_sync(output_dir, mode_args)
        elif mode in {"score-composite", "综合评分"}:
            result = run_composite_scoring(output_dir, mode_args)
        elif mode in {"score-research-composite", "研究型综合评分"}:
            result = run_research_composite_scoring(output_dir, mode_args)
        elif mode in {"verify-cross-board-consistency", "跨板一致性门禁"}:
            result = run_cross_board_consistency_gate(output_dir, mode_args)
        elif mode in {"refresh-composite-poster", "重绘综合评分海报"}:
            result = run_composite_poster_refresh(output_dir, mode_args)
        elif mode in {"model-poster", "模型海报"}:
            result = run_composite_model_poster(output_dir, mode_args)
        elif mode in {"structure-poster", "评分结构海报"}:
            result = run_composite_structure_poster(output_dir, mode_args)
        else:
            raise ValueError(f"未知模式：{mode}")
    except Exception as exc:
        result = {
            "schema": "BIG_BULL_ANALYSIS_SCORING_RESULT_V1",
            "status": "BLOCKED",
            "mode": mode,
            "error": f"{type(exc).__name__}:{exc}",
        }
    write_result(output_dir, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "CLEAN_PASS" else 2


if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
