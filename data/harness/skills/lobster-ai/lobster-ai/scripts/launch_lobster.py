from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import functools
import hmac
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Sequence

import stock_dashboard

APP_VERSION = "1.2.0-local"
UPSTREAM_API = "https://flash-api.xuangubao.com.cn/api/pool/detail"
BREADTH_UPSTREAM_API = "https://flash-api.xuangubao.com.cn/api/market_indicator/line"
ALLOWED_POOLS = frozenset({"limit_up", "limit_down", "limit_up_broken"})
SOURCE_ARCHIVE_SHA256 = "1F07130DD1197207B69637345514F03B38D90B356A3A24F65817DC3018C21CA7"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
WEB_ROOT = SKILL_ROOT / "assets" / "web"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def state_dir() -> Path:
    override = os.environ.get("LOBSTER_AI_STATE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return base / "LOBSTER-AI"


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def find_chrome() -> Path | None:
    override = os.environ.get("LOBSTER_CHROME")
    candidates: list[Path] = []
    if override:
        candidates.append(Path(override))

    for key in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        value = os.environ.get(key)
        if value:
            candidates.append(Path(value) / "Google" / "Chrome" / "Application" / "chrome.exe")

    if os.name == "nt":
        try:
            import winreg

            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                try:
                    with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                        value, _ = winreg.QueryValueEx(key, None)
                        candidates.append(Path(value))
                except OSError:
                    pass
        except ImportError:
            pass

    seen: set[str] = set()
    for candidate in candidates:
        normalized = os.path.normcase(str(candidate.expanduser()))
        if normalized in seen:
            continue
        seen.add(normalized)
        if candidate.is_file():
            return candidate.resolve()
    return None


class LobsterServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler_class: type[SimpleHTTPRequestHandler],
        *,
        status_file: Path,
        test_shutdown_token: str | None,
    ) -> None:
        super().__init__(server_address, request_handler_class)
        self.status_file = status_file
        self.test_shutdown_token = test_shutdown_token


class LobsterHandler(SimpleHTTPRequestHandler):
    server: LobsterServer
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        if os.environ.get("LOBSTER_VERBOSE") == "1":
            super().log_message(format, *args)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if urllib.parse.urlparse(self.path).path.endswith((".html", ".js", ".css")):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_sse_event(self, event: str, payload: dict[str, Any], *, event_id: str | None = None) -> None:
        lines = []
        if event_id:
            lines.append(f"id: {event_id}")
        lines.append(f"event: {event}")
        lines.append(f"data: {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}")
        packet = ("\n".join(lines) + "\n\n").encode("utf-8")
        self.wfile.write(packet)
        self.wfile.flush()

    def stream_stock_result_events(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        self.close_connection = False
        try:
            self.wfile.write(b"retry: 1000\n\n")
            self.wfile.flush()
            previous = stock_dashboard.source_watch_signature()
            self.send_sse_event(
                "ready",
                {
                    "status": "connected",
                    "watch_signature": previous,
                    "change_detection_interval_ms": 350,
                },
            )
            heartbeat_at = time.monotonic()
            while True:
                time.sleep(0.35)
                current = stock_dashboard.source_watch_signature()
                if current != previous:
                    previous = current
                    self.send_sse_event(
                        "results-changed",
                        {
                            "status": "changed",
                            "watch_signature": current,
                            "detected_at": now_iso(),
                        },
                        event_id=str(time.time_ns()),
                    )
                if time.monotonic() - heartbeat_at >= 15:
                    self.wfile.write(f": heartbeat {int(time.time())}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    heartbeat_at = time.monotonic()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, TimeoutError):
            return

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        decoded_path = urllib.parse.unquote(parsed.path)
        if decoded_path != "/index.html" and decoded_path.startswith("/index.html"):
            suffix = decoded_path[len("/index.html") :].lstrip()
            if suffix.startswith(("，", ",", "。", ".", "PID")):
                self.send_response(302)
                self.send_header("Location", "/index.html")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return

        if parsed.path == "/health":
            self.send_json(
                200,
                {
                    "status": "ok",
                    "service": "lobster-ai",
                    "version": APP_VERSION,
                    "proxy_mode": "same-origin",
                    "breadth_endpoint": "/api/breadth",
                    "stock_dashboard_endpoint": "/api/stock-results",
                    "stock_dashboard_events_endpoint": "/api/stock-results/events",
                    "stock_dashboard_url": "/stock-dashboard.html",
                    "stock_dashboard_realtime_transport": "server_sent_events",
                    "stock_dashboard_change_detection_interval_ms": 350,
                    "web_root": str(WEB_ROOT),
                },
            )
            return

        if parsed.path == "/api/stock-results/events":
            self.stream_stock_result_events()
            return

        if parsed.path == "/api/stock-results":
            try:
                payload = stock_dashboard.build_snapshot(state_dir() / "stock_dashboard_snapshot.json")
            except Exception as exc:
                self.send_json(
                    500,
                    {
                        "status": "error",
                        "schema": stock_dashboard.SCHEMA_VERSION,
                        "message": f"{type(exc).__name__}: {exc}",
                    },
                )
                return
            self.send_json(200, payload)
            return

        if parsed.path == "/api/pool":
            pool_name = urllib.parse.parse_qs(parsed.query).get("pool_name", [""])[0]
            self.proxy_pool(pool_name)
            return

        if parsed.path == "/api/breadth":
            self.proxy_breadth()
            return

        if parsed.path == "/__test_shutdown__":
            supplied = urllib.parse.parse_qs(parsed.query).get("token", [""])[0]
            expected = self.server.test_shutdown_token
            if not expected or not hmac.compare_digest(supplied, expected):
                self.send_json(404, {"status": "not_found"})
                return
            self.send_json(200, {"status": "stopping"})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return

        super().do_GET()

    def proxy_pool(self, pool_name: str) -> None:
        if pool_name not in ALLOWED_POOLS:
            self.send_json(400, {"status": "error", "message": "不支持的行情池"})
            return

        query = urllib.parse.urlencode({"pool_name": pool_name, "_": int(time.time() * 1000)})
        request = urllib.request.Request(
            f"{UPSTREAM_API}?{query}",
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LOBSTER-AI/1.0",
                "Referer": "https://xuangubao.cn/",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read(12 * 1024 * 1024 + 1)
            if len(raw) > 12 * 1024 * 1024:
                raise ValueError("上游响应过大")
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict) or payload.get("code") != 20000 or not isinstance(payload.get("data"), list):
                raise ValueError("上游数据格式异常")
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            self.send_json(502, {"status": "error", "pool_name": pool_name, "message": str(exc)})
            return

        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def proxy_breadth(self) -> None:
        trade_date = datetime.now().astimezone().date().isoformat()
        query = urllib.parse.urlencode(
            {
                "fields": "rise_count,fall_count",
                "date": trade_date,
                "_": int(time.time() * 1000),
            }
        )
        request = urllib.request.Request(
            f"{BREADTH_UPSTREAM_API}?{query}",
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LOBSTER-AI/1.1",
                "Referer": "https://xuangubao.cn/",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError("上游广度响应过大")
            payload = json.loads(raw.decode("utf-8"))
            rows = payload.get("data") if isinstance(payload, dict) else None
            if payload.get("code") != 20000 or not isinstance(rows, list) or not rows:
                raise ValueError("上游广度数据格式异常")
            latest = max(
                (item for item in rows if isinstance(item, dict)),
                key=lambda item: int(item.get("timestamp") or 0),
            )
            rise_count = int(latest.get("rise_count"))
            fall_count = int(latest.get("fall_count"))
            timestamp = int(latest.get("timestamp"))
            if rise_count < 0 or fall_count < 0 or rise_count + fall_count <= 0 or timestamp <= 0:
                raise ValueError("上游广度数据值异常")
        except (urllib.error.URLError, TimeoutError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.send_json(502, {"status": "error", "source": "market_breadth", "message": str(exc)})
            return

        self.send_json(
            200,
            {
                "code": 20000,
                "message": "OK",
                "data": {
                    "rise_count": rise_count,
                    "fall_count": fall_count,
                    "timestamp": timestamp,
                    "trade_date": datetime.fromtimestamp(timestamp).astimezone().date().isoformat(),
                    "source": "xuangubao-market-indicator",
                },
                "points": len(rows),
            },
        )


def open_in_chrome(url: str) -> tuple[bool, str | None]:
    chrome = find_chrome()
    if chrome is None:
        return False, None
    subprocess.Popen(
        [str(chrome), "--new-tab", url],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True, str(chrome)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="启动 LOBSTER AI 本机网页面板")
    parser.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1", "localhost"))
    parser.add_argument("--port", default=0, type=int)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--status-file", type=Path)
    parser.add_argument("--test-shutdown-token", help=argparse.SUPPRESS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    required_assets = (
        WEB_ROOT / "index.html",
        WEB_ROOT / "lobster.ai.js",
        WEB_ROOT / "stock-dashboard.html",
        WEB_ROOT / "stock-dashboard.js",
    )
    if any(not path.is_file() for path in required_assets):
        print("[ERROR] LOBSTER AI 网页资产缺失。", file=sys.stderr)
        return 2

    status_file = (args.status_file or (state_dir() / "runtime_status.json")).expanduser().resolve()
    handler = functools.partial(LobsterHandler, directory=str(WEB_ROOT))
    server = LobsterServer(
        (args.host, args.port),
        handler,
        status_file=status_file,
        test_shutdown_token=args.test_shutdown_token,
    )
    port = int(server.server_address[1])
    url = f"http://127.0.0.1:{port}/index.html"
    chrome_opened = False
    chrome_path: str | None = str(find_chrome()) if find_chrome() else None

    status = {
        "service": "lobster-ai",
        "version": APP_VERSION,
        "state": "running",
        "started_at": now_iso(),
        "stopped_at": None,
        "pid": os.getpid(),
        "host": "127.0.0.1",
        "port": port,
        "url": url,
        "web_root": str(WEB_ROOT),
        "status_file": str(status_file),
        "chrome_path": chrome_path,
        "chrome_opened": False,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
    }
    atomic_write_json(status_file, status)

    print("LOBSTER AI 本地服务已启动。", flush=True)
    print(f"访问地址：{url}", flush=True)
    print("行情模式：本机同源代理 → 选股宝公开池", flush=True)

    if not args.no_browser:
        chrome_opened, chrome_path = open_in_chrome(url)
        status["chrome_opened"] = chrome_opened
        status["chrome_path"] = chrome_path
        atomic_write_json(status_file, status)
        if not chrome_opened:
            print("[WARN] 未找到 Google Chrome；请手动在 Chrome 打开上方地址。", flush=True)

    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        status["state"] = "stopped"
        status["stopped_at"] = now_iso()
        status["chrome_opened"] = chrome_opened
        status["chrome_path"] = chrome_path
        atomic_write_json(status_file, status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
