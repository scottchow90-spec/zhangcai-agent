#!/usr/bin/env python3
"""Local bridge for Tongdaxin process state, launch, and public data feeds."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from tdx_process import detect_tdx_process, summarize_tdx_processes

_tdx_root_text = (
    os.environ.get("ZHANGCAI_TDX_ROOT")
    or os.environ.get("TDX_ROOT")
    or ""
).strip()
_packaged_runtime = os.environ.get("ZHANGCAI_PACKAGED") == "1"
ROOT = Path(_tdx_root_text) if _tdx_root_text else (
    Path(os.environ.get("ZHANGCAI_DEV_TDX_ROOT", r"C:\new_tdx_mock"))
    if not _packaged_runtime
    else Path(os.environ.get("ZHANGCAI_DATA_DIR", Path.cwd())) / "runtime" / "__tdx_root_not_configured__"
)
USER = ROOT / "PYPlugins" / "user"
OUT = Path(os.environ.get("ZHANGCAI_DATA_DIR", Path(__file__).resolve().parents[1] / "data")) / "runtime"
FORMULAS = ["大牛线4.0", "飞龙在天", "游资资金监控", "机构资金监控", "庄家资金监控"]

def process_rows():
    return detect_tdx_process(ROOT).get("processes", [])

def process_state(rows=None):
    if rows is None:
        return detect_tdx_process(ROOT)
    return summarize_tdx_processes(rows, ROOT)

def executable_candidates():
    configured = os.environ.get("ZHANGCAI_TDX_EXE") or os.environ.get("TDX_EXE")
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.extend([
        ROOT / "TdxW.exe",
        ROOT / "TdxW" / "TdxW.exe",
        ROOT / "tdx.exe",
    ])
    seen = set()
    result = []
    for candidate in candidates:
        value = str(candidate)
        if value in seen:
            continue
        seen.add(value)
        result.append(candidate)
    return result

def open_tongdaxin():
    state = detect_tdx_process(ROOT)
    running = state.get("processes", [])
    if state.get("running") is True and state.get("rootMatches") is not False:
        return {"status": "already_open", "processes": state.get("matching") or running, "tdxRoot": str(ROOT), "rootMatches": state.get("rootMatches")}
    if state.get("running") is True:
        return {
            "status": "path_mismatch",
            "processes": running,
            "tdxRoot": str(ROOT),
            "runningRoots": state.get("runningRoots", []),
            "error": "检测到其他目录中的通达信正在运行。请在数据与设置中选择该通达信目录，或退出其他实例后重试。",
        }
    if state.get("running") is None:
        return {
            "status": "detection_unavailable",
            "tdxRoot": str(ROOT),
            "error": "当前系统无法确认通达信进程状态。为避免重复启动，请手动确认通达信后刷新运行环境。",
            "diagnostic": state.get("error", ""),
        }

    candidates = executable_candidates()
    executable = next((candidate for candidate in candidates if candidate.is_file()), None)
    if executable is None:
        return {
            "status": "missing_executable",
            "tdxRoot": str(ROOT),
            "candidates": [str(candidate) for candidate in candidates],
            "error": "未找到通达信客户端 TdxW.exe，请检查通达信安装目录或设置 ZHANGCAI_TDX_EXE",
        }

    creation_flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        child = subprocess.Popen(
            [str(executable)],
            cwd=str(executable.parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=creation_flags,
        )
    except OSError as error:
        return {
            "status": "launch_failed",
            "tdxRoot": str(ROOT),
            "executable": str(executable),
            "error": f"通达信启动失败：{error}",
        }

    # 启动器只负责拉起客户端，不等待客户端登录；短暂轮询用于区分
    # “已请求启动”和“进程根本没有拉起”，避免页面显示假成功。
    for _ in range(12):
        time.sleep(0.25)
        state = detect_tdx_process(ROOT)
        if state.get("rootMatches") is True:
            return {
                "status": "accepted",
                "pid": child.pid,
                "executable": str(executable),
                "processes": state.get("matching", []),
                "tdxRoot": str(ROOT),
            }
    return {
        "status": "accepted",
        "pid": child.pid,
        "executable": str(executable),
        "verified": False,
        "tdxRoot": str(ROOT),
        "message": "已请求打开通达信，进程尚未在短轮询内出现，请稍后重新检测",
    }

def latest(paths):
    rows = [p for p in paths if p.exists()]
    if not rows: return None
    p = max(rows, key=lambda x: x.stat().st_mtime)
    return {"path": str(p), "updatedAt": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"), "size": p.stat().st_size}

def status():
    cache = ROOT / "T0002" / "hq_cache"
    day = ROOT / "vipdoc" / "sh" / "lday" / "sh000001.day"
    formula_dir = ROOT / "T0002" / "gs_bak"
    formula_files = sorted({
        path.name
        for pattern in ("*.txt", "*.tn6", "*.tn5", "*.tnf")
        for path in formula_dir.glob(pattern)
    }) if formula_dir.is_dir() else []
    process_info = detect_tdx_process(ROOT)
    return {"generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"), "tdxRoot": str(ROOT), "processes": process_info.get("processes", []), "processState": process_info, "formulaRegistry": {"directory": str(formula_dir), "formulaFiles": formula_files}, "freshness": {"indexDay": latest([day]), "marketCache": latest([cache / "sh.tnf", cache / "sz.tnf", cache / "bj.tnf", cache / "tdxhy.cfg", cache / "infoharbor_block.dat"]), "blockPools": latest([ROOT / "T0002" / "blocknew" / "ZTC.blk", ROOT / "T0002" / "blocknew" / "FLZT.blk"]), "intradayAvailable": any((ROOT / "vipdoc" / market / "fzline").glob("*.lc5") for market in ("sh", "sz", "bj"))}, "tq": {"tqcenter": str(USER / "tqcenter.py"), "strategyConfig": (ROOT / "PYPlugins" / "py_strategy.cfg").read_text(encoding="utf-8", errors="replace") if (ROOT / "PYPlugins" / "py_strategy.cfg").exists() else "", "formulas": FORMULAS}}

def quote(symbol):
    state = detect_tdx_process(ROOT)
    if state.get("running") is False:
        raise RuntimeError(f"当前配置的通达信目录没有可用运行进程：{ROOT}")
    if state.get("rootMatches") is False:
        raise RuntimeError(f"检测到通达信运行目录与当前配置不一致：配置 {ROOT}；运行中 {state.get('runningRoots', [])}")
    sys.path.insert(0, str(USER)); os.chdir(ROOT)
    from tqcenter import tq
    tq.initialize(str(USER / "tdxdata_test.py"))
    data = tq.get_market_data(stock_list=[symbol], period="1m", count=1)
    row = {"symbol": symbol, "fetchedAt": datetime.now().astimezone().isoformat(timespec="seconds"), "source": "Tongdaxin TQ 1m"}
    for key, value in data.items():
        try:
            series = value[symbol] if hasattr(value, "__getitem__") else None
            latest_value = series.iloc[-1] if hasattr(series, "iloc") else None
            row[key.lower()] = float(latest_value) if latest_value is not None else None
        except Exception: pass
    tq.close()
    return row

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["status", "quote", "open"])
    parser.add_argument("--symbol")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "quote" and not args.symbol: parser.error("quote requires --symbol")
    payload = quote(args.symbol) if args.command == "quote" else open_tongdaxin() if args.command == "open" else status()
    if args.output:
        output = args.output
    elif args.command == "status":
        output = OUT / "tdx-runtime-status.json"
    elif args.command == "open":
        output = OUT / "tdx-open-result.json"
    else:
        # 行情查询保留为独立快照，不能覆盖客户端连接状态。
        stamp = datetime.now().strftime("%Y%m%d/%H%M%S")
        output = OUT / "quotes" / stamp.split("/")[0] / f"{args.symbol.replace('.', '_')}-{stamp.split('/')[1]}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))

if __name__ == "__main__": main()
