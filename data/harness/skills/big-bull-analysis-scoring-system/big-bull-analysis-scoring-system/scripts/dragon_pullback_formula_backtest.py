#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import csv
import json
import math
import os
import re
import struct
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


TDX_ROOT = Path(r"C:\new_tdx_mock")
TQ_USER_DIR = TDX_ROOT / "PYPlugins" / "user"
TQ_INIT_PATH = TQ_USER_DIR / "tdxdata_test.py"
FORMULA_SOURCE = TDX_ROOT / "T0002" / "gs_bak" / "大牛线.txt"
BIG_BULL_FORMULA = "大牛线撑压版"
BIG_BULL_SIGNAL_FIELD = "X7（图示四件套共同条件）"
FEILONG_FORMULA = "飞龙在天"
FEILONG_FIELDS = ("OUTPUT3", "OUTPUT4", "OUTPUT5", "OUTPUT6", "波", "段")
CAPITAL_FORMULA = "庄家资金监控"
CAPITAL_FIELDS = ("控盘程度", "控盘度")


def normalize_number(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("Value")
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def normalize_series(value: Any) -> list[float | None]:
    items = value if isinstance(value, list) else [value]
    return [normalize_number(item) for item in items]


def valid_stock_code(market: str, code: str) -> bool:
    if market == "sh":
        return code.startswith(("600", "601", "603", "605", "688", "689"))
    if market == "sz":
        return code.startswith(("000", "001", "002", "003", "300", "301"))
    if market == "bj":
        return code.startswith(("4", "8", "9"))
    return False


def discover_symbols(
    max_stocks: int, requested_symbols: str = ""
) -> list[tuple[str, Path]]:
    if requested_symbols.strip():
        found: list[tuple[str, Path]] = []
        for raw_symbol in requested_symbols.split(","):
            symbol = raw_symbol.strip().upper()
            match = re.fullmatch(r"(\d{6})\.(SH|SZ|BJ)", symbol)
            if not match:
                raise ValueError(f"股票代码格式错误:{raw_symbol}")
            code, market_upper = match.groups()
            market = market_upper.lower()
            path = TDX_ROOT / "vipdoc" / market / "lday" / f"{market}{code}.day"
            if not path.is_file():
                raise FileNotFoundError(path)
            found.append((symbol, path))
        return found
    found: list[tuple[str, Path]] = []
    for market in ("sh", "sz", "bj"):
        folder = TDX_ROOT / "vipdoc" / market / "lday"
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob(f"{market}*.day")):
            match = re.fullmatch(rf"{market}(\d{{6}})\.day", path.name, re.I)
            if not match:
                continue
            code = match.group(1)
            if not valid_stock_code(market, code):
                continue
            found.append((f"{code}.{market.upper()}", path))
            if max_stocks and len(found) >= max_stocks:
                return found
    return found


def read_day_file(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    data = path.read_bytes()
    for offset in range(0, len(data), 32):
        block = data[offset : offset + 32]
        if len(block) != 32:
            break
        date_int, open_i, high_i, low_i, close_i, amount, volume, _ = struct.unpack(
            "<IIIIIfII", block
        )
        if date_int <= 0 or min(open_i, high_i, low_i, close_i) <= 0:
            continue
        records.append(
            {
                "date": str(date_int),
                "open": open_i / 100.0,
                "high": high_i / 100.0,
                "low": low_i / 100.0,
                "close": close_i / 100.0,
                "amount": float(amount),
                "volume": int(volume),
            }
        )
    return records


def tdx_sma(values: list[float], period: int, weight: int) -> list[float]:
    if not values:
        return []
    result = [float(values[0])]
    for value in values[1:]:
        result.append(
            (weight * float(value) + (period - weight) * result[-1]) / period
        )
    return result


def exact_signal_indices(
    records: list[dict[str, Any]], count: int, start_date: str
) -> list[int]:
    closes = [float(row["close"]) for row in records]
    lows = [float(row["low"]) for row in records]
    gains = [
        max(closes[index] - closes[index - 1], 0.0) if index > 0 else 0.0
        for index in range(len(records))
    ]
    moves = [
        abs(closes[index] - closes[index - 1]) if index > 0 else 0.0
        for index in range(len(records))
    ]
    operation_gain = tdx_sma(gains, 2, 1)
    operation_move = tdx_sma(moves, 2, 1)
    cp_gain = tdx_sma(gains, 2, 1)
    cp_move = tdx_sma(moves, 2, 1)
    operation = [
        operation_gain[index] / operation_move[index] * 100
        if operation_move[index]
        else 0.0
        for index in range(len(records))
    ]
    cp = [
        cp_gain[index] / cp_move[index] * 100 if cp_move[index] else 0.0
        for index in range(len(records))
    ]
    operation_45 = [
        bool(index > 0 and operation[index] < 45 and operation[index - 1] > 45)
        for index in range(len(records))
    ]
    operation_20 = [
        bool(index > 0 and operation[index] < 20 and operation[index - 1] > 20)
        for index in range(len(records))
    ]
    cp_45 = [
        bool(index > 0 and cp[index] < 45 and cp[index - 1] > 45)
        for index in range(len(records))
    ]
    cp_20 = [
        bool(index > 0 and cp[index] < 20 and cp[index - 1] > 20)
        for index in range(len(records))
    ]
    limit_up = [
        bool(index > 0 and closes[index - 1] * 1.1 - closes[index] < 0.01)
        for index in range(len(records))
    ]
    hh = [
        any(limit_up[max(0, index - 12) : index + 1])
        for index in range(len(records))
    ]
    first_allowed = max(20, len(records) - count)
    result: list[int] = []
    for index, record in enumerate(records):
        if index < first_allowed or (start_date and record["date"] < start_date):
            continue
        x5 = bool(
            lows[index] > 0
            and index > 0
            and (operation_45[index - 1] or operation_20[index - 1])
            and hh[index]
        )
        x6 = bool(
            lows[index] > 0
            and index > 0
            and (cp_45[index - 1] or cp_20[index - 1])
            and hh[index]
        )
        if x5 and x6:
            result.append(index)
    return result


def initialize_tq():
    sys.path.insert(0, str(TQ_USER_DIR))
    sys.argv = ["tqcenter", "--run_tdx", "0"]
    from tqcenter import tq

    tq.initialize(str(TQ_INIT_PATH))
    return tq


def read_formula_source() -> str:
    raw = FORMULA_SOURCE.read_bytes()
    for encoding in ("utf-8-sig", "gb18030", "gbk"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError("大牛线公式文字无法读取")


def signal_source_context() -> list[dict[str, Any]]:
    lines = read_formula_source().splitlines()
    matched: set[int] = set()
    for index in range(149, min(len(lines), 205)):
        matched.add(index)
    patterns = (
        "龙回头",
        "DRAWICON",
        "DRAWTEXT",
        "COLORWHITE",
        "COLORRED",
        "'买'",
        '"买"',
    )
    for index, line in enumerate(lines):
        if any(pattern.upper() in line.upper() for pattern in patterns):
            for context_index in range(max(0, index - 2), min(len(lines), index + 3)):
                matched.add(context_index)
    return [
        {"行号": index + 1, "内容": lines[index].strip()}
        for index in sorted(matched)
        if lines[index].strip()
    ]


def write_source_check(output_dir: Path) -> int:
    context = signal_source_context()
    payload = {
        "状态": "PASS",
        "公式": BIG_BULL_FORMULA,
        "公式文件": str(FORMULA_SOURCE),
        "核对内容": context,
    }
    report_path = output_dir / "龙回头真实历史回测.md"
    summary_path = output_dir / "龙回头真实历史回测.json"
    events_path = output_dir / "龙回头真实历史明细.csv"
    report_lines = [
        "# 龙回头图示买点公式核对",
        "",
        "以下内容只用于核对本机大牛线公式如何画出白横杠、红点、红箭头和红色“买”字。",
        "",
    ]
    for row in context:
        report_lines.append(f"- 第{row['行号']}行：`{row['内容']}`")
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    summary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    events_path.write_text("", encoding="utf-8-sig")
    print(
        json.dumps(
            {
                "status": "PASS",
                "source_check": str(summary_path),
                "matched_lines": len(context),
            },
            ensure_ascii=False,
        )
    )
    return 0


def formula_values(
    tq,
    symbol: str,
    formula: str,
    count: int,
    dividend_type: int,
    *,
    capital_call: bool = False,
) -> dict[str, Any]:
    setup = tq.formula_set_data_info(
        symbol, count=count, dividend_type=dividend_type
    )
    if not isinstance(setup, dict) or str(setup.get("ErrorId")) != "0":
        raise RuntimeError(f"set_data_failed:{symbol}:{formula}:{setup}")
    code = symbol.split(".", 1)[0]
    if capital_call:
        result = tq.formula_zb(formula, code, xsflag=2)
    else:
        result = tq.formula_zb(formula, formula_arg=code)
    values = result.get("Value") if isinstance(result, dict) else None
    if not isinstance(values, dict) or not values:
        raise RuntimeError(f"formula_empty:{symbol}:{formula}:{result}")
    return values


def aligned_map(
    records: list[dict[str, Any]], values: dict[str, Any], fields: tuple[str, ...]
) -> dict[str, dict[str, float | None]]:
    series = {field: normalize_series(values.get(field)) for field in fields}
    lengths = [len(items) for items in series.values() if items]
    if not lengths:
        return {}
    width = min(min(lengths), len(records))
    if width <= 0:
        return {}
    dates = [item["date"] for item in records[-width:]]
    result: dict[str, dict[str, float | None]] = {}
    for index, date in enumerate(dates):
        result[date] = {
            field: series[field][-width:][index] for field in fields
        }
    return result


def parse_feilong_node(node: dict[str, Any]) -> dict[str, dict[str, float | None]]:
    by_date: dict[str, dict[str, float | None]] = defaultdict(dict)
    for field in FEILONG_FIELDS:
        items = node.get(field)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            date = re.sub(r"\D", "", str(item.get("Date") or ""))[:8]
            if len(date) == 8:
                by_date[date][field] = normalize_number(item.get("Value"))
    return dict(by_date)


def pct_change(end: float, start: float) -> float:
    return (end / start - 1.0) * 100.0 if start else 0.0


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_event(
    symbol: str,
    records: list[dict[str, Any]],
    signal_index: int,
    capital: dict[str, dict[str, float | None]],
) -> dict[str, Any] | None:
    entry_index = signal_index + 1
    if entry_index + 9 >= len(records) or signal_index < 20:
        return None
    signal = records[signal_index]
    entry = records[entry_index]
    close20 = [row["close"] for row in records[signal_index - 19 : signal_index + 1]]
    volume5 = [row["volume"] for row in records[signal_index - 4 : signal_index + 1]]
    previous = records[signal_index - 1]
    horizon_returns: dict[int, float] = {}
    for horizon in (3, 5, 10):
        exit_row = records[entry_index + horizon - 1]
        horizon_returns[horizon] = pct_change(exit_row["close"], entry["open"])
    five_rows = records[entry_index : entry_index + 5]
    body = abs(signal["close"] - signal["open"])
    lower_shadow = min(signal["open"], signal["close"]) - signal["low"]
    capital_today = capital.get(signal["date"], {})
    capital_degree = capital_today.get("控盘程度")
    capital_control = capital_today.get("控盘度")
    return {
        "股票": symbol,
        "买点日期": signal["date"],
        "买点当天收盘": round(signal["close"], 3),
        "次日开盘买入": round(entry["open"], 3),
        "买入日": entry["date"],
        "3天结果": round(horizon_returns[3], 4),
        "5天结果": round(horizon_returns[5], 4),
        "10天结果": round(horizon_returns[10], 4),
        "3天赚钱": horizon_returns[3] > 0,
        "5天赚钱": horizon_returns[5] > 0,
        "10天赚钱": horizon_returns[10] > 0,
        "5天内最高": round(
            pct_change(max(row["high"] for row in five_rows), entry["open"]), 4
        ),
        "5天内最低": round(
            pct_change(min(row["low"] for row in five_rows), entry["open"]), 4
        ),
        "次日高开幅度": round(pct_change(entry["open"], signal["close"]), 4),
        "买点当天涨跌": round(pct_change(signal["close"], previous["close"]), 4),
        "此前5天涨跌": round(
            pct_change(signal["close"], records[signal_index - 5]["close"]), 4
        ),
        "此前20天涨跌": round(
            pct_change(signal["close"], records[signal_index - 20]["close"]), 4
        ),
        "高于20天平均价": signal["close"] >= mean(close20),
        "离20天最高价不远": signal["close"] >= max(
            row["high"] for row in records[signal_index - 19 : signal_index + 1]
        )
        * 0.95,
        "当天上涨": signal["close"] >= previous["close"],
        "当天成交明显放大": signal["volume"] >= mean(volume5) * 1.5,
        "下影线明显": lower_shadow > max(body, signal["close"] * 0.01),
        "资金数一": capital_degree,
        "资金数二": capital_control,
        "资金数据可用": capital_degree is not None and capital_control is not None,
        "资金至少一项比前一天增加": False,
        "资金两项都为正": (
            capital_degree is not None
            and capital_control is not None
            and capital_degree > 0
            and capital_control > 0
        ),
        "飞龙金叉数据可用": False,
        "飞龙主动提示数据可用": False,
        "飞龙显示金叉": False,
        "飞龙至少一项亮起": False,
        "飞龙前后两组都亮起": False,
    }


def add_feilong_labels(events: list[dict[str, Any]], maps: dict[str, dict[str, dict]]):
    for event in events:
        values = maps.get(event["股票"], {}).get(event["买点日期"], {})
        event["飞龙主动提示数据可用"] = all(
            field in values for field in FEILONG_FIELDS[:4]
        )
        flags = {
            field: value is not None and value >= 99
            for field, value in values.items()
            if field in FEILONG_FIELDS[:4]
        }
        wave = values.get("波")
        segment = values.get("段")
        event["飞龙金叉数据可用"] = wave is not None and segment is not None
        event["飞龙显示金叉"] = bool(
            event["飞龙金叉数据可用"] and wave > segment
        )
        event["飞龙至少一项亮起"] = any(flags.values())
        event["飞龙前后两组都亮起"] = (
            (flags.get("OUTPUT5", False) or flags.get("OUTPUT6", False))
            and (flags.get("OUTPUT3", False) or flags.get("OUTPUT4", False))
        )


def add_capital_labels(
    events: list[dict[str, Any]], maps: dict[str, dict[str, dict[str, float | None]]]
):
    date_indexes = {
        symbol: {date: index for index, date in enumerate(values)}
        for symbol, values in maps.items()
    }
    ordered_dates = {
        symbol: list(values)
        for symbol, values in maps.items()
    }
    for event in events:
        symbol_values = maps.get(event["股票"], {})
        values = symbol_values.get(event["买点日期"], {})
        degree = values.get("控盘程度")
        control = values.get("控盘度")
        index = date_indexes.get(event["股票"], {}).get(event["买点日期"])
        previous_values: dict[str, float | None] = {}
        if index is not None and index > 0:
            previous_date = ordered_dates[event["股票"]][index - 1]
            previous_values = symbol_values.get(previous_date, {})
        previous_degree = previous_values.get("控盘程度")
        previous_control = previous_values.get("控盘度")
        event["资金数一"] = degree
        event["资金数二"] = control
        event["资金数据可用"] = degree is not None and control is not None
        event["资金至少一项比前一天增加"] = bool(
            event["资金数据可用"]
            and (
                (
                    previous_degree is not None
                    and degree is not None
                    and degree > previous_degree
                )
                or (
                    previous_control is not None
                    and control is not None
                    and control > previous_control
                )
            )
        )
        event["资金两项都为正"] = bool(
            event["资金数据可用"] and degree > 0 and control > 0
        )


def summarize_group(events: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(events)
    return {
        "次数": count,
        "3天赚钱比例": round(
            100 * sum(bool(row["3天赚钱"]) for row in events) / count, 2
        )
        if count
        else None,
        "5天赚钱比例": round(
            100 * sum(bool(row["5天赚钱"]) for row in events) / count, 2
        )
        if count
        else None,
        "10天赚钱比例": round(
            100 * sum(bool(row["10天赚钱"]) for row in events) / count, 2
        )
        if count
        else None,
        "5天平均结果": round(mean([float(row["5天结果"]) for row in events]), 2)
        if count
        else None,
        "5天内平均最高": round(mean([float(row["5天内最高"]) for row in events]), 2)
        if count
        else None,
        "5天内平均最低": round(mean([float(row["5天内最低"]) for row in events]), 2)
        if count
        else None,
    }


def condition_comparisons(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conditions = {
        "买点当天价格高于近20天平均价": lambda row: bool(row["高于20天平均价"]),
        "买点靠近近20天最高价": lambda row: bool(row["离20天最高价不远"]),
        "买点当天上涨": lambda row: bool(row["当天上涨"]),
        "买点当天成交明显放大": lambda row: bool(row["当天成交明显放大"]),
        "买点当天盘中一度跌得较深但收回": lambda row: bool(row["下影线明显"]),
        "买点前5天已经上涨": lambda row: float(row["此前5天涨跌"]) > 0,
        "买点前20天涨幅超过20%": lambda row: float(row["此前20天涨跌"]) > 20,
        "第二天开盘价比买点当天收盘高3%以上": lambda row: float(
            row["次日高开幅度"]
        )
        > 3,
        "飞龙至少一项亮起": lambda row: bool(row["飞龙至少一项亮起"]),
        "飞龙前后两组都亮起": lambda row: bool(row["飞龙前后两组都亮起"]),
        "飞龙在天给出向上支持（金叉）": lambda row: bool(
            row["飞龙显示金叉"]
        ),
        "资金两项都为正": lambda row: bool(row["资金两项都为正"]),
        "资金至少一项比前一天增加": lambda row: bool(
            row["资金至少一项比前一天增加"]
        ),
    }
    rows: list[dict[str, Any]] = []
    for name, predicate in conditions.items():
        population = events
        if name == "飞龙在天给出向上支持（金叉）":
            population = [row for row in events if row["飞龙金叉数据可用"]]
        elif name.startswith("飞龙"):
            population = [
                row for row in events if row["飞龙主动提示数据可用"]
            ]
        elif name.startswith("资金"):
            population = [row for row in events if row["资金数据可用"]]
        yes = [row for row in population if predicate(row)]
        no = [row for row in population if not predicate(row)]
        yes_summary = summarize_group(yes)
        no_summary = summarize_group(no)
        if not yes or not no:
            difference = None
        else:
            difference = round(
                float(yes_summary["5天赚钱比例"])
                - float(no_summary["5天赚钱比例"]),
                2,
            )
        rows.append(
            {
                "情况": name,
                "符合次数": len(yes),
                "不符合次数": len(no),
                "符合时5天赚钱比例": yes_summary["5天赚钱比例"],
                "不符合时5天赚钱比例": no_summary["5天赚钱比例"],
                "相差": difference,
            }
        )
    return rows


def format_rate(value: Any) -> str:
    return "无数据" if value is None else f"{float(value):.2f}%"


def render_report(summary: dict[str, Any]) -> str:
    all_stats = summary["分组结果"]["全部龙回头买点"]
    lines = [
        "# 大牛线图示龙回头买点真实历史回测",
        "",
        "## 先说清楚",
        "",
        "- 本报告只认大牛线撑压版公式实际画出的龙回头买点，也就是白色横杠、红点、红箭头和红色“买”字这一组标记。",
        "- 买点按本机通达信原公式中这四个图形共同使用的条件逐日核对，没有使用编号返回值代替。",
        "- 飞龙在天和庄家资金监控只做同一天的辅助比较，不参与产生龙回头买点。",
        "- 图形要到当天收盘后才能确认，所以按第二天开盘买入，更接近日常实际操作。",
        "",
        "## 回测范围",
        "",
        f"- 本机日线截止：{summary['本机日线截止']}",
        f"- 检查股票：{summary['检查股票数']}只",
        f"- 有足够本机日线：{summary['公式成功股票数']}只",
        f"- 共检测到图示买点：{summary['检测到的全部买点次数']}次",
        f"- 出现龙回头买点：{summary['出现买点股票数']}只股票，共{summary['有效买点次数']}次",
        f"- 买点日期范围：{summary['最早买点日期']} 至 {summary['最晚买点日期']}",
        f"- 公式每只股票读取最近{summary['每只股票读取天数']}个交易日",
        f"- 资金辅助能对上日期：{summary['资金辅助覆盖次数']}次",
        f"- 飞龙金叉能对上日期：{summary['飞龙辅助覆盖次数']}次",
        f"- 两个辅助统一按每只股票最近{summary['辅助每只股票读取天数']}个有交易日比较",
        "",
        "## 总体结果",
        "",
        f"- 买入后第3个交易日收盘仍赚钱：{format_rate(all_stats['3天赚钱比例'])}",
        f"- 买入后第5个交易日收盘仍赚钱：{format_rate(all_stats['5天赚钱比例'])}",
        f"- 买入后第10个交易日收盘仍赚钱：{format_rate(all_stats['10天赚钱比例'])}",
        f"- 买入后5天平均结果：{format_rate(all_stats['5天平均结果'])}",
        f"- 买入后5天内平均最高能到：{format_rate(all_stats['5天内平均最高'])}",
        f"- 买入后5天内平均最低会到：{format_rate(all_stats['5天内平均最低'])}",
        "",
        "## 两个辅助判断有没有帮助",
        "",
        "| 情况 | 次数 | 3天赚钱 | 5天赚钱 | 10天赚钱 | 5天平均结果 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, stats in summary["分组结果"].items():
        lines.append(
            f"| {name} | {stats['次数']} | {format_rate(stats['3天赚钱比例'])} | "
            f"{format_rate(stats['5天赚钱比例'])} | {format_rate(stats['10天赚钱比例'])} | "
            f"{format_rate(stats['5天平均结果'])} |"
        )
    lines.extend(
        [
            "",
            "说明：辅助公式只统计能准确对上同一天的样本。“金叉”是飞龙在天公式自己的固定叫法，本报告把它理解为飞龙给出向上支持；资金辅助重点看数值是否比前一天增加。",
            "",
            "## 哪些情况更容易成功，哪些情况更容易失败",
            "",
            "下面每一行都来自历史买点直接分组。相差为正，表示符合这项时更容易赚钱；相差为负，表示符合这项时更容易失败。",
            "",
            "| 实际情况 | 符合次数 | 符合时5天赚钱 | 不符合时5天赚钱 | 相差 |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    comparisons = [
        row
        for row in summary["情况对比"]
        if row["符合次数"] >= 20 and row["不符合次数"] >= 20
    ]
    for row in sorted(
        comparisons,
        key=lambda item: abs(float(item["相差"] or 0)),
        reverse=True,
    ):
        lines.append(
            f"| {row['情况']} | {row['符合次数']} | "
            f"{format_rate(row['符合时5天赚钱比例'])} | "
            f"{format_rate(row['不符合时5天赚钱比例'])} | "
            f"{format_rate(row['相差'])} |"
        )
    positive = sorted(
        [row for row in comparisons if float(row["相差"] or 0) >= 1],
        key=lambda item: float(item["相差"]),
        reverse=True,
    )[:4]
    negative = sorted(
        [row for row in comparisons if float(row["相差"] or 0) <= -1],
        key=lambda item: float(item["相差"]),
    )[:4]
    lines.extend(["", "### 更容易成功的历史情况", ""])
    if positive:
        for row in positive:
            lines.append(
                f"- {row['情况']}：5天赚钱比例比不符合时高{abs(float(row['相差'])):.2f}个百分点。"
            )
    else:
        lines.append("- 没有发现样本数量足够、而且差别清楚的加分情况。")
    lines.extend(["", "### 更容易失败的历史情况", ""])
    if negative:
        for row in negative:
            lines.append(
                f"- {row['情况']}：5天赚钱比例比不符合时低{abs(float(row['相差'])):.2f}个百分点。"
            )
    else:
        lines.append("- 没有发现样本数量足够、而且差别清楚的减分情况。")
    lines.extend(
        [
            "",
            "## 使用边界",
            "",
            "- 这是对本机已有真实日线的历史统计，不是对以后走势的保证。",
            "- 最后10个交易日内出现的买点，因为还看不到完整10天结果，没有计入有效胜率。",
            "- 停牌、涨跌停导致第二天无法按开盘价买到的情况，历史价格本身无法证明真实成交，使用时要额外留意。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, events: list[dict[str, Any]]):
    if not events:
        path.write_text("", encoding="utf-8-sig")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(events[0].keys()))
        writer.writeheader()
        writer.writerows(events)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--count", type=int, default=600)
    parser.add_argument("--max-stocks", type=int, default=0)
    parser.add_argument("--start-date", default="")
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--aux-days", type=int, default=80)
    parser.add_argument("--symbols", default="")
    parser.add_argument("--source-check-only", action="store_true")
    args = parser.parse_args()
    if args.count < 120:
        raise SystemExit("--count不能少于120")
    if args.aux_days < 20 or args.aux_days > args.count:
        raise SystemExit("--aux-days必须在20到count之间")
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.source_check_only:
        return write_source_check(output_dir)
    source_text = read_formula_source()
    required_source_parts = (
        "龙回头:=IF",
        "X7:=X5 AND X6",
        "DRAWTEXT(X7",
        "STICKLINE(A AND REF(PP1,1) AND HH",
        "CIRCLEDOT",
        "DRAWICON(A AND REF(PP",
    )
    missing_source_parts = [
        part for part in required_source_parts if part not in source_text
    ]
    if missing_source_parts:
        raise SystemExit(f"图示买点原文核对失败:{missing_source_parts}")
    symbols = discover_symbols(args.max_stocks, args.symbols)
    if not symbols:
        raise SystemExit("没有找到本机A股日线")

    started = time.time()
    events: list[dict[str, Any]] = []
    records_by_symbol: dict[str, list[dict[str, Any]]] = {}
    formula_ok = 0
    errors: list[dict[str, str]] = []
    latest_dates: list[str] = []
    detected_signals: list[dict[str, str]] = []
    for position, (symbol, path) in enumerate(symbols, start=1):
        try:
            records = read_day_file(path)
            if len(records) < 120:
                continue
            latest_dates.append(records[-1]["date"])
            formula_ok += 1
            signal_indices = exact_signal_indices(
                records, args.count, args.start_date
            )
            if not signal_indices:
                continue
            records_by_symbol[symbol] = records
            for index in signal_indices:
                detected_signals.append(
                    {"股票": symbol, "买点日期": records[index]["date"]}
                )
                event = build_event(symbol, records, index, {})
                if event is not None:
                    events.append(event)
        except Exception as exc:
            errors.append(
                {
                    "股票": symbol,
                    "错误": f"主买点:{type(exc).__name__}:{exc}",
                }
            )
        if position % 500 == 0:
            print(
                json.dumps(
                    {
                        "已检查": position,
                        "可用日线": formula_ok,
                        "检测买点": len(detected_signals),
                        "有效买点": len(events),
                        "错误": len(errors),
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
                flush=True,
            )

    if not events:
        raise SystemExit("本次没有得到可计算后续10天结果的龙回头买点")

    tq = initialize_tq()
    try:
        aux_cutoff_by_symbol = {
            symbol: records[-min(args.aux_days, len(records))]["date"]
            for symbol, records in records_by_symbol.items()
        }
        symbols_with_events = sorted(
            {
                row["股票"]
                for row in events
                if row["买点日期"] >= aux_cutoff_by_symbol[row["股票"]]
            }
        )
        capital_maps: dict[
            str, dict[str, dict[str, float | None]]
        ] = {}
        for symbol in symbols_with_events:
            try:
                capital_values = formula_values(
                    tq,
                    symbol,
                    CAPITAL_FORMULA,
                    args.count,
                    0,
                    capital_call=True,
                )
                capital_maps[symbol] = aligned_map(
                    records_by_symbol[symbol], capital_values, CAPITAL_FIELDS
                )
            except Exception as exc:
                errors.append(
                    {
                        "股票": symbol,
                        "错误": f"资金辅助:{type(exc).__name__}:{exc}",
                    }
                )
        add_capital_labels(events, capital_maps)

        feilong_maps: dict[str, dict[str, dict]] = {}
        for offset in range(0, len(symbols_with_events), args.batch_size):
            batch = symbols_with_events[offset : offset + args.batch_size]
            try:
                result = tq.formula_process_mul_zb(
                    FEILONG_FORMULA,
                    stock_list=batch,
                    count=0,
                    return_count=args.count,
                    return_date=True,
                    dividend_type=1,
                )
                for symbol in batch:
                    node = result.get(symbol, {}) if isinstance(result, dict) else {}
                    if isinstance(node, dict):
                        feilong_maps[symbol] = parse_feilong_node(node)
            except Exception as exc:
                for symbol in batch:
                    errors.append(
                        {
                            "股票": symbol,
                            "错误": f"飞龙辅助:{type(exc).__name__}:{exc}",
                        }
                    )
        add_feilong_labels(events, feilong_maps)
    finally:
        try:
            tq.close()
        except Exception:
            pass

    events.sort(key=lambda row: (row["买点日期"], row["股票"]))
    groups = {
        "全部龙回头买点": events,
        "飞龙向上支持有数据的全部买点": [
            row for row in events if row["飞龙金叉数据可用"]
        ],
        "飞龙在天给出向上支持（金叉）": [
            row for row in events if row["飞龙显示金叉"]
        ],
        "资金有数据的全部买点": [
            row for row in events if row["资金数据可用"]
        ],
        "资金两项都为正": [
            row for row in events if row["资金两项都为正"]
        ],
        "资金至少一项比前一天增加": [
            row for row in events if row["资金至少一项比前一天增加"]
        ],
        "两个辅助都有数据的全部买点": [
            row
            for row in events
            if row["飞龙金叉数据可用"] and row["资金数据可用"]
        ],
        "飞龙向上支持且资金至少一项增加": [
            row
            for row in events
            if row["飞龙显示金叉"]
            and row["资金至少一项比前一天增加"]
        ],
    }
    summary = {
        "生成时间": datetime.now().astimezone().isoformat(timespec="seconds"),
        "主公式": BIG_BULL_FORMULA,
        "主买点": "公式原文中白横杠、红点、红箭头和红色买字共同出现",
        "主买点字段": BIG_BULL_SIGNAL_FIELD,
        "辅助公式": [FEILONG_FORMULA, CAPITAL_FORMULA],
        "本机日线截止": max(latest_dates) if latest_dates else None,
        "检查股票数": len(symbols),
        "公式成功股票数": formula_ok,
        "检测到的全部买点次数": len(detected_signals),
        "出现买点股票数": len({row["股票"] for row in events}),
        "有效买点次数": len(events),
        "最早买点日期": min(row["买点日期"] for row in events),
        "最晚买点日期": max(row["买点日期"] for row in events),
        "每只股票读取天数": args.count,
        "辅助每只股票读取天数": args.aux_days,
        "资金辅助覆盖次数": sum(
            bool(row["资金数据可用"]) for row in events
        ),
        "飞龙辅助覆盖次数": sum(
            bool(row["飞龙金叉数据可用"]) for row in events
        ),
        "飞龙主动提示覆盖次数": sum(
            bool(row["飞龙主动提示数据可用"]) for row in events
        ),
        "辅助对比最早日期": min(
            (
                row["买点日期"]
                for row in events
                if row["飞龙金叉数据可用"] and row["资金数据可用"]
            ),
            default="无",
        ),
        "辅助对比最晚日期": max(
            (
                row["买点日期"]
                for row in events
                if row["飞龙金叉数据可用"] and row["资金数据可用"]
            ),
            default="无",
        ),
        "最近检测买点": detected_signals[-100:],
        "分组结果": {
            name: summarize_group(group_events)
            for name, group_events in groups.items()
        },
        "情况对比": condition_comparisons(events),
        "错误数量": len(errors),
        "错误样例": errors[:50],
        "运行秒数": round(time.time() - started, 2),
    }
    report_path = output_dir / "龙回头真实历史回测.md"
    summary_path = output_dir / "龙回头真实历史回测.json"
    events_path = output_dir / "龙回头真实历史明细.csv"
    report_path.write_text(render_report(summary), encoding="utf-8")
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv(events_path, events)
    print(
        json.dumps(
            {
                "status": "PASS",
                "report": str(report_path),
                "summary": str(summary_path),
                "events": str(events_path),
                "events_count": len(events),
                "formula_ok": formula_ok,
                "errors": len(errors),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
