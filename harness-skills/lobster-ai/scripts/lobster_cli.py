from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import ast
import hashlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import launch_lobster


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
WEB_ROOT = SKILL_ROOT / "assets" / "web"
STATE_DIR = launch_lobster.state_dir()
SELFTEST_PATH = STATE_DIR / "last_selftest.json"
INFO_PATH = STATE_DIR / "last_info.json"
RUNTIME_TEST_PATH = STATE_DIR / "selftest_runtime.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    launch_lobster.atomic_write_json(path, payload)


def emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def build_info() -> dict[str, Any]:
    chrome = launch_lobster.find_chrome()
    files = []
    for relative in (
        "SKILL.md",
        "assets/web/index.html",
        "assets/web/lobster.ai.js",
        "assets/web/stock-dashboard.html",
        "assets/web/stock-dashboard.js",
        "scripts/launch_lobster.py",
        "scripts/stock_dashboard.py",
        "scripts/lobster_cli.py",
        "scripts/codex_entry.py",
    ):
        path = SKILL_ROOT / relative
        files.append(
            {
                "path": str(path),
                "exists": path.is_file(),
                "size": path.stat().st_size if path.is_file() else None,
                "sha256": file_sha256(path) if path.is_file() else None,
            }
        )
    return {
        "skill": "lobster-ai",
        "version": launch_lobster.APP_VERSION,
        "skill_root": str(SKILL_ROOT),
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "chrome": str(chrome) if chrome else None,
        "node": shutil.which("node"),
        "state_dir": str(STATE_DIR),
        "source_archive_sha256": launch_lobster.SOURCE_ARCHIVE_SHA256,
        "files": files,
    }


def read_json_url(url: str, timeout: float = 20.0) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})


def classify_upstream_error(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError) and 500 <= exc.code <= 599:
        return "UPSTREAM_5XX"
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return "TIMEOUT"
    if isinstance(exc, urllib.error.URLError) and isinstance(exc.reason, (socket.timeout, TimeoutError)):
        return "TIMEOUT"
    return "HEALTH_DEGRADED"


def probe_upstream_health(name: str, callback: Any) -> dict[str, Any]:
    try:
        outcome = callback()
    except Exception as exc:
        error_type = "socket.timeout" if isinstance(exc, (socket.timeout, TimeoutError)) else f"{type(exc).__module__}.{type(exc).__name__}"
        return {
            "name": name,
            "status": classify_upstream_error(exc),
            "error": f"{error_type}: {exc}",
        }

    if isinstance(outcome, dict) and "passed" in outcome:
        passed = bool(outcome["passed"])
        return {
            "name": name,
            "status": "HEALTHY" if passed else "HEALTH_DEGRADED",
            "detail": outcome.get("detail"),
        }
    return {"name": name, "status": "HEALTHY", "detail": outcome}


def build_selftest_result(
    started: str,
    checks: list[dict[str, Any]],
    upstream_probes: list[dict[str, Any]],
) -> dict[str, Any]:
    local_status = "PASS" if checks and all(check["status"] == "PASS" for check in checks) else "FAIL"
    upstream_status = (
        "HEALTHY"
        if all(probe.get("status") == "HEALTHY" for probe in upstream_probes)
        else "HEALTH_DEGRADED"
    )
    return {
        "skill": "lobster-ai",
        "status": local_status,
        "started_at": started,
        "finished_at": now_iso(),
        "skill_root": str(SKILL_ROOT),
        "state_file": str(SELFTEST_PATH),
        "runtime_state_file": str(RUNTIME_TEST_PATH),
        "checks": checks,
        "upstream_health": {
            "status": upstream_status,
            "probes": upstream_probes,
        },
    }


def run_selftest() -> dict[str, Any]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []
    upstream_probes: list[dict[str, Any]] = []
    started = now_iso()
    required = [
        SKILL_ROOT / "SKILL.md",
        WEB_ROOT / "index.html",
        WEB_ROOT / "lobster.ai.js",
        WEB_ROOT / "stock-dashboard.html",
        WEB_ROOT / "stock-dashboard.js",
        SCRIPT_DIR / "launch_lobster.py",
        SCRIPT_DIR / "stock_dashboard.py",
        SCRIPT_DIR / "lobster_cli.py",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    add_check(checks, "required_files", not missing, {"missing": missing})

    try:
        ast.parse((SCRIPT_DIR / "launch_lobster.py").read_text(encoding="utf-8"))
        ast.parse((SCRIPT_DIR / "lobster_cli.py").read_text(encoding="utf-8"))
        ast.parse((SCRIPT_DIR / "stock_dashboard.py").read_text(encoding="utf-8"))
        add_check(checks, "python_syntax", True, "launch_lobster.py, lobster_cli.py and stock_dashboard.py parsed")
    except (OSError, SyntaxError) as exc:
        add_check(checks, "python_syntax", False, str(exc))

    index_text = (WEB_ROOT / "index.html").read_text(encoding="utf-8") if (WEB_ROOT / "index.html").is_file() else ""
    js_text = (WEB_ROOT / "lobster.ai.js").read_text(encoding="utf-8") if (WEB_ROOT / "lobster.ai.js").is_file() else ""
    dashboard_text = (WEB_ROOT / "stock-dashboard.html").read_text(encoding="utf-8") if (WEB_ROOT / "stock-dashboard.html").is_file() else ""
    dashboard_js = (WEB_ROOT / "stock-dashboard.js").read_text(encoding="utf-8") if (WEB_ROOT / "stock-dashboard.js").is_file() else ""
    server_text = (SCRIPT_DIR / "launch_lobster.py").read_text(encoding="utf-8") if (SCRIPT_DIR / "launch_lobster.py").is_file() else ""
    panel_ok = "LOBSTER AI" in index_text and 'src="lobster.ai.js?v=1.1.0"' in index_text and "window.LobsterApp" in js_text
    proxy_ok = (
        'const POOL_API = "/api/pool?pool_name=";' in js_text
        and 'const BREADTH_API = "/api/breadth";' in js_text
        and "flash-api.xuangubao.com.cn" not in js_text
        and 'parsed.path == "/api/breadth"' in server_text
    )
    add_check(checks, "web_panel_assets", panel_ok, {"title": "LOBSTER AI" in index_text, "app_api": "window.LobsterApp" in js_text})
    dashboard_ok = (
        "本机选股结果总览" in dashboard_text
        and 'src="stock-dashboard.js?v=1.2.0"' in dashboard_text
        and 'const API = "/api/stock-results";' in dashboard_js
    )
    add_check(checks, "stock_dashboard_assets", dashboard_ok, {"html": bool(dashboard_text), "js": bool(dashboard_js)})
    realtime_ok = (
        'const EVENTS_API = "/api/stock-results/events";' in dashboard_js
        and "new EventSource(EVENTS_API)" in dashboard_js
        and 'parsed.path == "/api/stock-results/events"' in server_text
        and "source_watch_signature" in server_text
    )
    add_check(checks, "stock_dashboard_realtime_push", realtime_ok, {"transport": "server_sent_events", "fallback_seconds": 60})
    add_check(checks, "same_origin_proxy_binding", proxy_ok, ["/api/pool?pool_name=", "/api/breadth"])

    node = shutil.which("node")
    if node:
        syntax = subprocess.run([node, "--check", str(WEB_ROOT / "lobster.ai.js")], capture_output=True, text=True, encoding="utf-8")
        add_check(checks, "javascript_syntax", syntax.returncode == 0, syntax.stderr.strip() or "node --check PASS")
        dashboard_syntax = subprocess.run([node, "--check", str(WEB_ROOT / "stock-dashboard.js")], capture_output=True, text=True, encoding="utf-8")
        add_check(checks, "stock_dashboard_javascript_syntax", dashboard_syntax.returncode == 0, dashboard_syntax.stderr.strip() or "node --check PASS")
    else:
        add_check(checks, "javascript_syntax", False, "Node.js not found; syntax not verified")
        add_check(checks, "stock_dashboard_javascript_syntax", False, "Node.js not found; syntax not verified")

    chrome = launch_lobster.find_chrome()
    add_check(checks, "google_chrome", chrome is not None, str(chrome) if chrome else "not found")

    token = secrets.token_urlsafe(24)
    if RUNTIME_TEST_PATH.exists():
        RUNTIME_TEST_PATH.unlink()
    command = [
        sys.executable,
        str(SCRIPT_DIR / "launch_lobster.py"),
        "--no-browser",
        "--port",
        "0",
        "--status-file",
        str(RUNTIME_TEST_PATH),
        "--test-shutdown-token",
        token,
    ]
    process: subprocess.Popen[str] | None = None
    runtime_status: dict[str, Any] = {}
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if RUNTIME_TEST_PATH.is_file():
                try:
                    runtime_status = json.loads(RUNTIME_TEST_PATH.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    time.sleep(0.1)
                    continue
                if runtime_status.get("state") == "running" and runtime_status.get("url"):
                    break
            if process.poll() is not None:
                break
            time.sleep(0.1)

        service_ready = runtime_status.get("state") == "running" and bool(runtime_status.get("url"))
        add_check(checks, "service_start", service_ready, runtime_status or "runtime status missing")
        if service_ready:
            base = str(runtime_status["url"]).rsplit("/", 1)[0]
            health = read_json_url(f"{base}/health", timeout=5)
            add_check(
                checks,
                "health_endpoint",
                health.get("status") == "ok"
                and health.get("proxy_mode") == "same-origin"
                and health.get("stock_dashboard_events_endpoint") == "/api/stock-results/events"
                and health.get("stock_dashboard_realtime_transport") == "server_sent_events",
                health,
            )

            with urllib.request.urlopen(f"{base}/index.html", timeout=5) as response:
                served_index = response.read().decode("utf-8")
            add_check(checks, "web_panel_served", response.status == 200 and "LOBSTER AI" in served_index, {"http": response.status, "bytes": len(served_index.encode("utf-8"))})

            with urllib.request.urlopen(f"{base}/stock-dashboard.html", timeout=5) as dashboard_response:
                served_dashboard = dashboard_response.read().decode("utf-8")
            add_check(
                checks,
                "stock_dashboard_served",
                dashboard_response.status == 200 and "本机选股结果总览" in served_dashboard,
                {"http": dashboard_response.status, "bytes": len(served_dashboard.encode("utf-8"))},
            )
            dashboard_payload = read_json_url(f"{base}/api/stock-results", timeout=30)
            dashboard_summary = dashboard_payload.get("summary") if isinstance(dashboard_payload, dict) else None
            dashboard_api_ok = (
                dashboard_payload.get("schema") == "LOBSTER-STOCK-DASHBOARD-V1"
                and dashboard_payload.get("status") == "PASS"
                and isinstance(dashboard_summary, dict)
                and dashboard_summary.get("audited_skill_count") == 18
                and dashboard_payload.get("realtime_transport") == "server_sent_events"
                and dashboard_payload.get("change_detection_interval_ms") == 350
                and isinstance(dashboard_payload.get("sources"), list)
                and len(dashboard_payload.get("sources")) == 18
            )
            add_check(checks, "stock_dashboard_api", dashboard_api_ok, dashboard_summary or dashboard_payload)

            for pool_name in ("limit_up", "limit_down", "limit_up_broken"):
                def fetch_pool() -> dict[str, Any]:
                    payload = read_json_url(f"{base}/api/pool?pool_name={urllib.parse.quote(pool_name)}", timeout=20)
                    rows = payload.get("data") if isinstance(payload, dict) else None
                    passed = payload.get("code") == 20000 and isinstance(rows, list)
                    detail: dict[str, Any] = {"code": payload.get("code"), "count": len(rows) if isinstance(rows, list) else None}
                    if isinstance(rows, list) and rows:
                        timestamps = [
                            int(item.get("last_limit_up") or item.get("first_limit_up") or item.get("last_limit_down") or item.get("first_limit_down") or 0)
                            for item in rows
                            if isinstance(item, dict)
                        ]
                        detail["max_timestamp"] = max(timestamps, default=0)
                    return {"passed": passed, "detail": detail}

                upstream_probes.append(probe_upstream_health(pool_name, fetch_pool))

            def fetch_market_breadth() -> dict[str, Any]:
                breadth_payload = read_json_url(f"{base}/api/breadth", timeout=20)
                breadth = breadth_payload.get("data") if isinstance(breadth_payload, dict) else None
                breadth_passed = (
                    breadth_payload.get("code") == 20000
                    and isinstance(breadth, dict)
                    and isinstance(breadth.get("rise_count"), int)
                    and isinstance(breadth.get("fall_count"), int)
                    and int(breadth.get("rise_count") or 0) + int(breadth.get("fall_count") or 0) > 0
                    and int(breadth.get("timestamp") or 0) > 0
                )
                return {"passed": breadth_passed, "detail": breadth_payload}

            upstream_probes.append(probe_upstream_health("market_breadth", fetch_market_breadth))
            shutdown_url = f"{base}/__test_shutdown__?token={urllib.parse.quote(token)}"
            shutdown = read_json_url(shutdown_url, timeout=5)
            add_check(checks, "graceful_shutdown_request", shutdown.get("status") == "stopping", shutdown)
        else:
            add_check(checks, "health_endpoint", False, "service did not start")
            add_check(checks, "web_panel_served", False, "service did not start")
            add_check(checks, "stock_dashboard_served", False, "service did not start")
            add_check(checks, "stock_dashboard_api", False, "service did not start")
            add_check(checks, "graceful_shutdown_request", False, "service did not start")

        if process is not None:
            try:
                stdout, stderr = process.communicate(timeout=8)
            except subprocess.TimeoutExpired:
                process.terminate()
                stdout, stderr = process.communicate(timeout=5)
            runtime_exit_ok = process.returncode == 0
            add_check(checks, "service_exit", runtime_exit_ok, {"returncode": process.returncode, "stdout": stdout.strip(), "stderr": stderr.strip()})
    except Exception as exc:
        add_check(checks, "live_selftest", False, f"{type(exc).__name__}: {exc}")
    finally:
        if process is not None and process.poll() is None:
            try:
                if runtime_status.get("url"):
                    base = str(runtime_status["url"]).rsplit("/", 1)[0]
                    read_json_url(f"{base}/__test_shutdown__?token={urllib.parse.quote(token)}", timeout=5)
            except Exception:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    persisted_runtime: dict[str, Any] = {}
    if RUNTIME_TEST_PATH.is_file():
        try:
            persisted_runtime = json.loads(RUNTIME_TEST_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            persisted_runtime = {"error": str(exc)}
    add_check(checks, "persisted_runtime_readback", persisted_runtime.get("state") == "stopped", persisted_runtime)

    result = build_selftest_result(started, checks, upstream_probes)
    atomic_write_json(SELFTEST_PATH, result)
    return result


def read_status() -> dict[str, Any]:
    payload: dict[str, Any] = {"skill": "lobster-ai", "state_dir": str(STATE_DIR)}
    for label, path in (
        ("last_info", INFO_PATH),
        ("last_selftest", SELFTEST_PATH),
        ("runtime", STATE_DIR / "runtime_status.json"),
        ("selftest_runtime", RUNTIME_TEST_PATH),
    ):
        if path.is_file():
            try:
                payload[label] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                payload[label] = {"status": "INVALID_JSON", "error": str(exc), "path": str(path)}
        else:
            payload[label] = {"status": "MISSING", "path": str(path)}
    return payload


def open_running_panel() -> dict[str, Any]:
    runtime_path = STATE_DIR / "runtime_status.json"
    result: dict[str, Any] = {
        "skill": "lobster-ai",
        "status": "FAIL",
        "runtime_state_file": str(runtime_path),
        "opened_at": now_iso(),
    }
    if not runtime_path.is_file():
        result["error"] = "runtime_status.json 不存在；请先运行 launch"
        return result
    try:
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result["error"] = f"运行状态 JSON 无效：{exc}"
        return result
    url = runtime.get("url")
    if runtime.get("state") != "running" or not isinstance(url, str):
        result["error"] = "LOBSTER AI 服务当前未运行"
        result["runtime_state"] = runtime.get("state")
        return result
    try:
        health = read_json_url(url.rsplit("/", 1)[0] + "/health", timeout=5)
    except Exception as exc:
        result["error"] = f"本机服务健康检查失败：{type(exc).__name__}: {exc}"
        return result
    opened, chrome_path = launch_lobster.open_in_chrome(url)
    result.update({"status": "PASS" if opened else "FAIL", "url": url, "chrome_path": chrome_path, "health": health})
    if not opened:
        result["error"] = "未找到 Google Chrome"
        return result
    runtime["chrome_opened"] = True
    runtime["chrome_path"] = chrome_path
    runtime["last_opened_at"] = result["opened_at"]
    atomic_write_json(runtime_path, runtime)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LOBSTER AI 本机 Codex 固定入口")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("info", "selftest", "status", "open"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--json", action="store_true")
    launch = subparsers.add_parser("launch")
    launch.add_argument("--no-browser", action="store_true")
    launch.add_argument("--port", type=int, default=0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "info":
        result = build_info()
        result["status"] = "PASS" if result["chrome"] and all(item["exists"] for item in result["files"]) else "FAIL"
        result["checked_at"] = now_iso()
        atomic_write_json(INFO_PATH, result)
        emit(result, args.json)
        return 0 if result["status"] == "PASS" else 1
    if args.command == "selftest":
        result = run_selftest()
        emit(result, args.json)
        return 0 if result["status"] == "PASS" else 1
    if args.command == "status":
        emit(read_status(), args.json)
        return 0
    if args.command == "open":
        result = open_running_panel()
        emit(result, args.json)
        return 0 if result["status"] == "PASS" else 1
    if args.command == "launch":
        launch_args = ["--port", str(args.port)]
        if args.no_browser:
            launch_args.append("--no-browser")
        return launch_lobster.main(launch_args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
