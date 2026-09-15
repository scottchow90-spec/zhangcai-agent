from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
from zoneinfo import ZoneInfo

import launch_lobster
import lobster_cli


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
STATE_DIR = launch_lobster.state_dir()
EXECUTION_RESULT_PATH = STATE_DIR / "stock_execution_result.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def fetch_json(url: str, timeout: float = 20.0) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"LOBSTER-AI/{launch_lobster.APP_VERSION}"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected JSON root from {url}")
    return payload


def normalize_symbol(raw_symbol: Any) -> str | None:
    digits = "".join(ch for ch in str(raw_symbol or "") if ch.isdigit())
    if len(digits) < 6:
        return None
    code = digits[:6]
    if code.startswith("6"):
        market = "SH"
    elif code.startswith(("0", "3")):
        market = "SZ"
    else:
        return None
    return f"{code}.{market}"


def is_eligible(item: dict[str, Any]) -> bool:
    symbol = normalize_symbol(item.get("symbol"))
    name = str(item.get("stock_chi_name") or "").strip()
    upper_name = name.upper()
    return bool(
        symbol
        and name
        and not item.get("is_new_stock")
        and "ST" not in upper_name
        and "退" not in name
        and not upper_name.startswith(("N", "C"))
    )


def latest_trade_date(items: list[dict[str, Any]]) -> str:
    timestamp_fields = (
        "first_limit_up",
        "last_limit_up",
        "first_limit_down",
        "last_limit_down",
    )
    timestamps: list[int] = []
    for item in items:
        for field in timestamp_fields:
            value = item.get(field)
            if isinstance(value, (int, float)) and value > 0:
                timestamps.append(int(value))
    if not timestamps:
        raise ValueError("No market timestamps were returned by the live pool")
    return datetime.fromtimestamp(max(timestamps), ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")


def select_target(
    items: list[dict[str, Any]],
    requested_symbol: str | None,
    requested_name: str | None,
) -> tuple[str, str]:
    eligible = [item for item in items if is_eligible(item)]
    if not eligible:
        raise ValueError("The live limit-up pool contains no eligible SH/SZ stock")

    if requested_symbol:
        normalized_requested = requested_symbol.strip().upper()
        matches = [item for item in eligible if normalize_symbol(item.get("symbol")) == normalized_requested]
        if not matches:
            raise ValueError(f"Requested symbol is not in the current eligible limit-up pool: {normalized_requested}")
        target = matches[0]
    else:
        target = sorted(eligible, key=lambda row: normalize_symbol(row.get("symbol")) or "999999.ZZ")[0]

    symbol = normalize_symbol(target.get("symbol"))
    name = str(target.get("stock_chi_name") or "").strip()
    if symbol is None or not name:
        raise ValueError("Selected target is missing a normalized symbol or name")
    if requested_name and name != requested_name.strip():
        raise ValueError(f"Target name mismatch: expected {requested_name.strip()}, got {name}")
    return symbol, name


def live_execution(symbol: str | None, name: str | None) -> dict[str, Any]:
    runtime_path = STATE_DIR / "runtime_status.json"
    runtime = read_json(runtime_path)
    if runtime.get("state") != "running":
        raise RuntimeError("LOBSTER AI local service is not running; run the launch command first")

    base_url = str(runtime.get("url") or "").rsplit("/", 1)[0]
    if not base_url.startswith("http://127.0.0.1:"):
        raise RuntimeError(f"Refusing a non-loopback runtime URL: {base_url}")

    health = fetch_json(f"{base_url}/health", timeout=5.0)
    if health.get("status") != "ok" or health.get("proxy_mode") != "same-origin":
        raise RuntimeError(f"Unexpected LOBSTER AI health payload: {health}")

    pool_url = f"{base_url}/api/pool?{urllib.parse.urlencode({'pool_name': 'limit_up'})}"
    pool_payload = fetch_json(pool_url)
    if pool_payload.get("code") != 20000:
        raise RuntimeError(f"Upstream pool returned an unexpected code: {pool_payload.get('code')}")
    data = pool_payload.get("data")
    if not isinstance(data, list):
        raise RuntimeError("Upstream pool data is not a list")
    items = [item for item in data if isinstance(item, dict)]
    selected_symbol, selected_name = select_target(items, symbol, name)
    trade_date = latest_trade_date(items)

    result = {
        "schema_version": "LOBSTER-AI-STOCK-EXECUTION-V1",
        "status": "PASS",
        "generated_at": now_iso(),
        "skill": "lobster-ai",
        "entry": str(Path(__file__).resolve()),
        "symbol": selected_symbol,
        "code": selected_symbol.split(".", 1)[0],
        "name": selected_name,
        "latest_trade_date": trade_date,
        "pool_name": "limit_up",
        "raw_count": len(items),
        "eligible_count": sum(1 for item in items if is_eligible(item)),
        "data_source": "local_same_origin_proxy",
        "dashboard_url": runtime.get("url"),
        "service_health": {
            "status": health.get("status"),
            "proxy_mode": health.get("proxy_mode"),
            "host": health.get("host"),
        },
        "stock_file_delivery": False,
        "recommendation": False,
        "boundary": "This execution binds the installed skill to a current stock identity and trade date; it is not an investment recommendation.",
    }
    lobster_cli.atomic_write_json(EXECUTION_RESULT_PATH, result)
    return result


def command_info(as_json: bool) -> int:
    payload = lobster_cli.build_info()
    payload["canonical_entry"] = str(Path(__file__).resolve())
    payload["execution_result_path"] = str(EXECUTION_RESULT_PATH)
    lobster_cli.emit(payload, as_json)
    return 0


def command_selftest(as_json: bool) -> int:
    payload = lobster_cli.run_selftest()
    payload["canonical_entry"] = str(Path(__file__).resolve())
    lobster_cli.emit(payload, as_json)
    return 0 if payload.get("status") == "PASS" else 1


def command_run(symbol: str | None, name: str | None, as_json: bool) -> int:
    try:
        payload = live_execution(symbol, name)
    except Exception as exc:
        payload = {
            "schema_version": "LOBSTER-AI-STOCK-EXECUTION-V1",
            "status": "FAIL",
            "generated_at": now_iso(),
            "skill": "lobster-ai",
            "entry": str(Path(__file__).resolve()),
            "error": f"{type(exc).__name__}: {exc}",
        }
        lobster_cli.atomic_write_json(EXECUTION_RESULT_PATH, payload)
        lobster_cli.emit(payload, as_json)
        return 1
    lobster_cli.emit(payload, as_json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Canonical Codex entry for the LOBSTER AI stock dashboard skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    info_parser = subparsers.add_parser("info", help="Show installed runtime information")
    info_parser.add_argument("--json", action="store_true")

    selftest_parser = subparsers.add_parser("selftest", help="Run the full local service and proxy self-test")
    selftest_parser.add_argument("--json", action="store_true")

    run_parser = subparsers.add_parser("run", help="Bind the live dashboard pool to a current SH/SZ stock identity")
    run_parser.add_argument("--symbol", help="Optional normalized symbol such as 001258.SZ")
    run_parser.add_argument("--name", help="Optional exact Chinese stock name paired with --symbol")
    run_parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "info":
        return command_info(args.json)
    if args.command == "selftest":
        return command_selftest(args.json)
    if args.command == "run":
        return command_run(args.symbol, args.name, args.json)
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
