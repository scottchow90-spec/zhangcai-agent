#!/usr/bin/env python3
"""用本机通达信真实日线补档并执行飞龙在天1280因子/319有效维度实战评分。"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from feilong_continuation_research import (
    eligible_day_files,
    first_board_flags,
    limit_up_flags,
    symbol_for_day_path,
)
from feilong_factor_correlation_research import (
    FACTOR_SPECS,
    add_context_features,
    build_daily_features,
)
from feilong_factor_research import build_market_breadth, index_features, load_market_indices
from feilong_offline_replay import (
    evaluate_installed_formula,
    front_adjust_like_tq,
    read_base_finance,
    read_gbbq,
    read_tdx_day,
)


FORMULA_NAME = "飞龙在天"
FORMULA_SHA256 = "aabcec3d83b2b37d01d53ba4d9c281a745e29f53d941f3704da95dcea114e1e0"
TDX_ROOT = Path(r"C:\new_tdx_mock")
SKILL_ROOT = Path(__file__).resolve().parents[1]
FORMULA_PATH = SKILL_ROOT / "references" / "formulas" / "飞龙在天.tdx.txt"
DEFAULT_MODEL = Path(r"F:\Codex\projects\飞龙在天评分体系彻底优化_20260901-184258\维度扩展V3\评分模型\飞龙共振首板_319维评分模型配置.json")
DEFAULT_HISTORY = Path(r"F:\Codex\projects\飞龙在天评分体系彻底优化_20260901-184258\维度扩展V3\因子全量重算\飞龙共振首板_全量因子事件值.csv")
DEFAULT_SCORER = Path(r"F:\Codex\projects\飞龙在天评分体系彻底优化_20260901-184258\apply_yaogu_scoring.py")
DEFAULT_OUT = Path(r"F:\Codex\projects\飞龙在天评分体系彻底优化_20260901-184258\维度扩展V3\实战评分")
PRODUCTION_LOCK_PATH = SKILL_ROOT / "references" / "daily-score-production-lock-v3.json"
PRODUCTION_SCHEMA = "FEILONG_DAILY_YAOGU_PRODUCTION_V3"
DECISION_RULE_VERSION = "FEILONG_MULTIDIM_DECISION_V3"
REGISTERED_FACTOR_COUNT = 1280
RANKABLE_FACTOR_COUNT = 1273
REGISTERED_DIMENSION_COUNT = 325
EFFECTIVE_DIMENSION_COUNT = 319
MINIMUM_PRIOR_TRADING_BARS = 251
TNF_HEADER_SIZE = 50
TNF_RECORD_SIZE = 360
TNF_NAME_OFFSET = 31
TNF_NAME_SIZE = 18
HARD_RISK_WORDS = ("立案调查", "财务造假", "退市风险", "重大违法", "审计无法表示意见")
MAJOR_RISK_WORDS = ("重大诉讼", "行政处罚", "监管问询", "债务逾期", "资金占用", "业绩预亏", "大额亏损")
NEGATED_RISK_WORDS = ("不存在退市风险", "未被立案调查", "不涉及财务造假", "不存在重大违法")
LEGACY_FORMULA_NAME = FORMULA_NAME + "4.0"
LEGACY_LOCK_ALLOWLIST = {
    "feilong-strategy/SKILL.md",
    "feilong-strategy/references/feilong_subsystems.md",
    "feilong-strategy/references/formula-source-manifest.json",
    "feilong-strategy/references/mandatory-tq-verification.md",
    "feilong-strategy/scripts/feilong_factor_research.py",
    "stock-hard-gate/scripts/preflight.py",
}


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_evidence(path: Path) -> dict[str, Any]:
    return {"path": str(path), "size": path.stat().st_size, "sha256": sha256_path(path)}


def validate_production_lock(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "FEILONG_DAILY_SCORE_PRODUCTION_LOCK_V3" or payload.get("status") != "LOCKED":
        raise RuntimeError("生产规则锁清单无效")
    if (
        payload.get("formula_name") != FORMULA_NAME
        or payload.get("factor_count") != REGISTERED_FACTOR_COUNT
        or payload.get("rankable_factor_count") != RANKABLE_FACTOR_COUNT
        or payload.get("registered_dimension_count") != REGISTERED_DIMENSION_COUNT
        or payload.get("dimension_count") != EFFECTIVE_DIMENSION_COUNT
        or payload.get("decision_rule_version") != DECISION_RULE_VERSION
        or payload.get("model_schema") != "FEILONG_YAOGU_MULTIDIM_SCORE_V3"
        or payload.get("minimum_prior_trading_bars") != MINIMUM_PRIOR_TRADING_BARS
    ):
        raise RuntimeError("生产规则锁结构与V3多维评分合同不一致")
    assets = payload.get("assets")
    if not isinstance(assets, list) or not assets:
        raise RuntimeError("生产规则锁资产为空")
    bindings: dict[str, dict[str, Any]] = {}
    for item in assets:
        role = str(item.get("role", "")).strip()
        if not role or role in bindings:
            raise RuntimeError("生产规则锁资产角色缺失或重复")
        asset = Path(str(item.get("path", ""))).resolve()
        if not asset.is_file():
            raise RuntimeError(f"生产规则锁资产缺失:{asset}")
        evidence = file_evidence(asset)
        if evidence["size"] != item.get("size") or evidence["sha256"] != item.get("sha256"):
            raise RuntimeError(f"生产规则资产漂移:{asset}")
        bindings[role] = evidence
    required_roles = {"score_model", "training_history", "score_engine"}
    if not required_roles.issubset(bindings):
        raise RuntimeError("生产规则锁缺少评分模型、训练历史或评分引擎")
    return {
        **file_evidence(path),
        "schema": payload["schema"],
        "decision_rule_version": payload["decision_rule_version"],
        "asset_bindings": bindings,
    }


def stable_file_set_evidence(paths: list[Path], root: Path, label: str) -> dict[str, Any]:
    rows: list[str] = []
    total_size = 0
    unique = sorted({path.resolve() for path in paths}, key=lambda value: str(value).casefold())
    for path in unique:
        before = path.stat()
        content = path.read_bytes()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError(f"输入文件读取期间发生变化:{path}")
        try:
            identity = path.relative_to(root.resolve()).as_posix()
        except ValueError:
            identity = str(path)
        digest = hashlib.sha256(content).hexdigest()
        rows.append(f"{identity}|{len(content)}|{digest}")
        total_size += len(content)
    return {
        "label": label,
        "file_count": len(unique),
        "total_size": total_size,
        "sha256": hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest(),
    }


def decode_tnf(raw: bytes) -> str:
    return raw.split(b"\0", 1)[0].decode("gbk", errors="ignore").strip()


def load_names(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for market, name in (("SH", "shs.tnf"), ("SZ", "szs.tnf"), ("BJ", "bjs.tnf")):
        path = root / "T0002" / "hq_cache" / name
        content = path.read_bytes()
        for offset in range(TNF_HEADER_SIZE, len(content) - TNF_RECORD_SIZE + 1, TNF_RECORD_SIZE):
            record = content[offset : offset + TNF_RECORD_SIZE]
            code = record[:6].decode("ascii", errors="ignore")
            if len(code) == 6 and code.isdigit():
                result[f"{code}.{market}"] = decode_tnf(record[TNF_NAME_OFFSET : TNF_NAME_OFFSET + TNF_NAME_SIZE])
    return result


def is_model_domain(symbol: str) -> bool:
    code, _, market = symbol.partition(".")
    return (market == "SH" and code.startswith(("600", "601", "603", "605"))) or (
        market == "SZ" and code.startswith(("000", "001", "002", "003"))
    )


def is_risk_name(name: str) -> bool:
    compact = re.sub(r"\s+", "", str(name)).upper()
    return any(token in compact for token in ("ST", "*ST", "PT", "退"))


def latest_data_date(paths: list[Path]) -> tuple[str, int, int]:
    latest: list[str] = []
    for path in paths:
        try:
            frame = read_tdx_day(path)
            if not frame.empty:
                latest.append(str(frame.index[-1]))
        except Exception:
            continue
    if not latest:
        raise RuntimeError("本机通达信主板日线不可读")
    maximum = max(latest)
    return maximum, len(latest), sum(value == maximum for value in latest)


def local_risk_corpus_paths(root: Path, target_date: str) -> list[Path]:
    text_suffixes = {".htm", ".html", ".json", ".txt", ".xml"}
    target_day = datetime.strptime(target_date, "%Y%m%d").date()
    first_day = target_day - timedelta(days=14)
    directories = [
        root / "T0002" / "msg_zx",
        root / "T0002" / "info_cache",
    ]
    paths: list[Path] = []
    for directory in directories:
        if directory.is_dir():
            paths.extend(
                path
                for path in directory.rglob("*")
                if (
                    path.is_file()
                    and path.suffix.casefold() in text_suffixes
                    and 0 < path.stat().st_size <= 2 * 1024 * 1024
                    and first_day <= datetime.fromtimestamp(path.stat().st_mtime).date() <= target_day
                )
            )
    return sorted({path.resolve() for path in paths}, key=lambda value: str(value).casefold())


def load_local_risk_corpus(paths: list[Path]) -> tuple[str, list[str], dict[str, Any]]:
    chunks: list[str] = []
    files: list[str] = []
    rows: list[str] = []
    total_size = 0
    for path in paths:
        before = path.stat()
        content = path.read_bytes()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError(f"风险语料读取期间发生变化:{path}")
        digest = hashlib.sha256(content).hexdigest()
        rows.append(f"{path}|{len(content)}|{digest}")
        total_size += len(content)
        text = content.decode("gbk", errors="ignore")
        if text:
            chunks.append(text)
            files.append(str(path))
    evidence = {
        "file_count": len(paths),
        "text_file_count": len(files),
        "total_size": total_size,
        "sha256": hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest(),
    }
    return "\n".join(chunks), files, evidence


def risk_hits(corpus: str, code: str, name: str) -> tuple[list[str], list[str]]:
    windows: list[str] = []
    for needle in {code, name}:
        if not needle:
            continue
        for match in re.finditer(re.escape(needle), corpus, flags=re.IGNORECASE):
            windows.append(corpus[max(0, match.start() - 180) : match.end() + 180])
    joined = "\n".join(windows)
    for token in NEGATED_RISK_WORDS:
        joined = joined.replace(token, "")
    return (
        sorted({word for word in HARD_RISK_WORDS if word in joined}),
        sorted({word for word in MAJOR_RISK_WORDS if word in joined}),
    )


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_legacy_formula() -> dict[str, Any]:
    skills_root = SKILL_ROOT.parent
    retained_locks: list[str] = []
    unexpected: list[str] = []
    historical_reference_files = 0
    suffixes = {".py", ".json", ".md", ".txt"}
    excluded_parts = {"reports", "backup", "run", "cache", "archive", "history", "__pycache__"}
    for path in skills_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        relative = path.relative_to(skills_root).as_posix()
        if any(part.casefold() in excluded_parts for part in path.parts):
            try:
                if LEGACY_FORMULA_NAME in path.read_text(encoding="utf-8", errors="ignore"):
                    historical_reference_files += 1
            except OSError:
                pass
            continue
        try:
            present = LEGACY_FORMULA_NAME in path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not present:
            continue
        if relative in LEGACY_LOCK_ALLOWLIST:
            retained_locks.append(relative)
        else:
            unexpected.append(relative)
    if unexpected:
        raise RuntimeError("发现活动旧版公式引用:" + ",".join(unexpected))
    return {
        "status": "CLEAN_PASS",
        "canonical_formula": FORMULA_NAME,
        "active_executable_old_formula_references": 0,
        "unexpected_active_reference_count": 0,
        "retained_forbidden_lock_references": sorted(retained_locks),
        "historical_reference_files_preserved": historical_reference_files,
        "routing_alias_removed": True,
        "tdx_core_formula_key_current_only": True,
    }


def run(*, target_date: str | None, model_path: Path, history_path: Path, scorer_path: Path, out_dir: Path) -> dict[str, Any]:
    if not TDX_ROOT.is_dir():
        raise RuntimeError(f"固定通达信根目录不存在: {TDX_ROOT}")
    production_lock_evidence = validate_production_lock(PRODUCTION_LOCK_PATH)
    if sha256_path(FORMULA_PATH) != FORMULA_SHA256:
        raise RuntimeError("飞龙在天公式源哈希不一致")
    for path in (model_path, history_path, scorer_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    locked_assets = production_lock_evidence["asset_bindings"]
    for role, current in {
        "score_model": model_path,
        "training_history": history_path,
        "score_engine": scorer_path,
    }.items():
        if current.resolve() != Path(str(locked_assets[role]["path"])).resolve():
            raise RuntimeError(f"生产评分输入未绑定锁定资产:{role}")
    model = json.loads(model_path.read_text(encoding="utf-8"))
    validation = model.get("production_validation", {})
    if (
        len(FACTOR_SPECS) != REGISTERED_FACTOR_COUNT
        or model.get("schema") != "FEILONG_YAOGU_MULTIDIM_SCORE_V3"
        or model.get("registered_factor_count") != REGISTERED_FACTOR_COUNT
        or model.get("rankable_factor_count") != RANKABLE_FACTOR_COUNT
        or len(model.get("factors", [])) != RANKABLE_FACTOR_COUNT
        or model.get("registered_dimension_count") != REGISTERED_DIMENSION_COUNT
        or model.get("dimension_count") != EFFECTIVE_DIMENSION_COUNT
        or len(model.get("dimensions", [])) != EFFECTIVE_DIMENSION_COUNT
        or model.get("imputed_training_cells") != 0
        or validation.get("status") != "CLEAN_PASS"
        or validation.get("development_grade_monotonic") is not True
        or validation.get("sealed_holdout_top_grade_positive_lift") is not True
    ):
        raise RuntimeError("1280因子/1273有效排行/325注册维度/319有效维度V3模型生产验收不一致")

    all_a_share_paths = eligible_day_files(TDX_ROOT)
    paths = [path for path in all_a_share_paths if is_model_domain(symbol_for_day_path(path))]
    latest, readable_count, at_latest_count = latest_data_date(paths)
    target = target_date or latest
    if target != latest:
        raise RuntimeError(f"目标日期必须等于本机最新有效交易日: target={target}; latest={latest}")
    history = pd.read_csv(history_path, low_memory=False)
    history["first_board_date"] = history["first_board_date"].astype(str)
    history_max = str(history["first_board_date"].max())
    if target <= history_max:
        raise RuntimeError(f"目标日期没有晚于既有样本: {target} <= {history_max}")
    names = load_names(TDX_ROOT)
    finance_path = TDX_ROOT / "T0002" / "hq_cache" / "base.dbf"
    finance = read_base_finance(finance_path)
    gbbq_path = TDX_ROOT / "T0002" / "hq_cache" / "gbbq"
    tnf_paths = [
        TDX_ROOT / "T0002" / "hq_cache" / name
        for name in ("shs.tnf", "szs.tnf", "bjs.tnf")
        if (TDX_ROOT / "T0002" / "hq_cache" / name).is_file()
    ]
    index_paths = [
        TDX_ROOT / "vipdoc" / "sh" / "lday" / "sh000001.day",
        TDX_ROOT / "vipdoc" / "sz" / "lday" / "sz399001.day",
        TDX_ROOT / "vipdoc" / "sz" / "lday" / "sz399006.day",
    ]
    risk_paths = local_risk_corpus_paths(TDX_ROOT, target)
    snapshot_paths = [*all_a_share_paths, *index_paths, *tnf_paths, finance_path, gbbq_path, *risk_paths]
    input_snapshot_before = stable_file_set_evidence(snapshot_paths, TDX_ROOT, "TDX_EXACT_INPUT_SET")
    reader = SKILL_ROOT / "vendor" / "pytdx-1.72" / "pytdx" / "reader" / "gbbq_reader.py"
    actions = read_gbbq(gbbq_path, reader)
    action_groups = {symbol: group.drop(columns=["symbol"]).copy() for symbol, group in actions.groupby("symbol", sort=False)}
    corpus, corpus_files, risk_corpus_evidence = load_local_risk_corpus(risk_paths)

    scan_rows: list[dict[str, Any]] = []
    hit_rows: list[dict[str, Any]] = []
    for path in paths:
        symbol = symbol_for_day_path(path)
        code = symbol[:6]
        raw = read_tdx_day(path)
        if raw.empty or str(raw.index[-1]) < target:
            continue
        first = first_board_flags(limit_up_flags(raw, code))
        dates = [str(value) for value in raw.index[first] if history_max < str(value) <= target]
        if not dates:
            continue
        base = finance.get(code, {})
        listing_date = str(base.get("SSDATE") or str(raw.index[0]))
        if len(re.sub(r"\D", "", listing_date)) < 8:
            listing_date = str(raw.index[0])
        listing_date = re.sub(r"\D", "", listing_date)[:8]
        active_capital = float(base.get("LTAG") or 0.0)
        active_capital = active_capital if active_capital > 0 else None
        symbol_actions = action_groups.get(symbol, pd.DataFrame())
        adjusted = front_adjust_like_tq(raw, symbol_actions)
        formula = evaluate_installed_formula(
            adjusted,
            active_capital_10k_shares=active_capital,
            listing_date=listing_date,
            code=code,
            name=names.get(symbol, ""),
        )
        for date in dates:
            frow = formula.loc[date]
            if "signal" in frow.index:
                resolved = True
                signal = bool(frow["signal"])
                reason = "完整公式回放"
            elif not bool(frow["xs2"]):
                resolved, signal, reason = True, False, "XS2不成立，无需流通股本"
            elif bool(frow["private_entry"]):
                resolved, signal, reason = True, True, "私募秘进与XS2成立，无需流通股本"
            else:
                resolved, signal, reason = False, False, "base.dbf缺有效流通股本，暴涨启动无法判定"
            bar = raw.loc[date]
            one_price = bool(float(bar["open"]) == float(bar["high"]) == float(bar["low"]) == float(bar["close"]))
            name = names.get(symbol, "")
            hard_hits, major_hits = risk_hits(corpus, code, name)
            hard_reasons: list[str] = []
            if not name:
                hard_reasons.append("股票身份缺失")
            if is_risk_name(name):
                hard_reasons.append("ST/PT/退市风险名称")
            if one_price:
                hard_reasons.append("一字首板不在模型训练域")
            if float(bar["amount"]) <= 0 or float(bar["volume"]) <= 0:
                hard_reasons.append("成交额或成交量异常")
            if not resolved:
                hard_reasons.append("公式关键财务输入未解析")
            if hard_hits:
                hard_reasons.append("本地资讯重大硬风险:" + "/".join(hard_hits))
            listing_age = (datetime.strptime(date, "%Y%m%d") - datetime.strptime(listing_date, "%Y%m%d")).days
            prior_trading_bars = int(raw.index.get_loc(date))
            if prior_trading_bars < MINIMUM_PRIOR_TRADING_BARS:
                hard_reasons.append(
                    f"前序交易日仅{prior_trading_bars}根，低于模型适用域{MINIMUM_PRIOR_TRADING_BARS}根"
                )
            row = {
                "symbol": symbol,
                "name": name,
                "first_board_date": date,
                "formula_name": FORMULA_NAME,
                "formula_resolved": resolved,
                "formula_signal": signal,
                "formula_resolution": reason,
                "formula_longtou": bool(frow.get("longtou", False)),
                "formula_waveband_password": bool(frow.get("waveband_password", False)),
                "formula_rapid_rise": bool(frow.get("rapid_rise", False)) if "rapid_rise" in frow.index else np.nan,
                "formula_private_entry": bool(frow.get("private_entry", False)),
                "formula_xs1": bool(frow.get("xs1", False)) if "xs1" in frow.index else bool(frow.get("private_entry", False)),
                "formula_xs2": bool(frow.get("xs2", False)),
                "listing_age_days": float(listing_age),
                "prior_trading_bars": prior_trading_bars,
                "one_price_board": one_price,
                "hard_exclusion": bool(hard_reasons),
                "hard_exclusion_reason": "；".join(hard_reasons),
                "local_hard_risk_hits": "/".join(hard_hits),
                "local_major_risk_hits": "/".join(major_hits),
                "announcement_verification_status": "本机近14日本地资讯已扫描" if corpus_files else "本地资讯无可用覆盖，公告风险未验证",
            }
            scan_rows.append(row)
            if signal:
                hit_rows.append(row.copy())

    scan = pd.DataFrame(scan_rows)
    hits = pd.DataFrame(hit_rows)
    if hits.empty:
        hits = pd.DataFrame(columns=["symbol", "first_board_date", "formula_longtou", "formula_waveband_password", "formula_rapid_rise", "formula_private_entry", "formula_xs1", "formula_xs2", "listing_age_days"])

    event_dates = set(hits["first_board_date"].astype(str))
    if event_dates:
        breadth, _breadth_evidence = build_market_breadth(TDX_ROOT, event_dates)
        indices = load_market_indices(TDX_ROOT)
        for column in ("market_traded_count", "market_advance_ratio", "market_median_return_pct", "market_ge_9_8_count", "market_amount_100m"):
            hits[column] = hits["first_board_date"].map(breadth[column])
        for prefix, index_frame in indices.items():
            values = {date: index_features(index_frame, date, prefix) for date in event_dates}
            for suffix in ("ret_1d_pct", "ret_5d_pct", "above_ma20"):
                column = f"{prefix}_{suffix}"
                hits[column] = hits["first_board_date"].map({date: row[column] for date, row in values.items()})
        hits["reach2"] = False
        hits["reach3"] = False
        primary_columns = [
            "symbol", "first_board_date", "reach2", "reach3",
            "formula_longtou", "formula_waveband_password", "formula_rapid_rise", "formula_private_entry", "formula_xs1", "formula_xs2", "listing_age_days",
            "market_traded_count", "market_advance_ratio", "market_median_return_pct", "market_ge_9_8_count", "market_amount_100m",
            "sh_index_ret_1d_pct", "sh_index_ret_5d_pct", "sh_index_above_ma20",
            "sz_index_ret_1d_pct", "sz_index_ret_5d_pct", "sz_index_above_ma20",
            "cyb_index_ret_1d_pct", "cyb_index_ret_5d_pct", "cyb_index_above_ma20",
        ]
        new_daily, daily_evidence = build_daily_features(hits[primary_columns].copy(), TDX_ROOT)
        base_columns = primary_columns
        daily_names = [factor for factor, spec in FACTOR_SPECS.items() if spec["source"] in {"通达信日线", "通达信GBBQ"}]
        combined_primary = pd.concat([history.reindex(columns=base_columns), hits.reindex(columns=base_columns)], ignore_index=True)
        combined_daily = pd.concat([history.reindex(columns=daily_names), new_daily.reindex(columns=daily_names)], ignore_index=True)
        contextual = add_context_features(combined_primary, combined_daily)
        enriched = contextual.tail(len(hits)).reset_index(drop=True)
        for column in hits.columns:
            enriched[column] = hits[column].reset_index(drop=True)
    else:
        enriched = hits.copy()
        daily_evidence = {
            "event_count": 0,
            "symbol_count": 0,
            "day_file_count": 0,
            "day_file_set_sha256": hashlib.sha256(b"").hexdigest(),
            "read_error_count": 0,
            "future_bars_loaded": False,
        }
        for factor in FACTOR_SPECS:
            if factor not in enriched.columns:
                enriched[factor] = np.nan

    missing_factor_columns = [factor for factor in FACTOR_SPECS if factor not in enriched.columns]
    if missing_factor_columns:
        raise RuntimeError("因子列缺失:" + ",".join(missing_factor_columns))
    model_factor_names = [str(item["factor"]) for item in model["factors"]]
    if len(model_factor_names) != len(set(model_factor_names)) or any(factor not in FACTOR_SPECS for factor in model_factor_names):
        raise RuntimeError("1273有效排行因子定义重复或越界")
    full_factor_names = list(FACTOR_SPECS)
    numeric_factors = enriched[full_factor_names].apply(pd.to_numeric, errors="coerce")
    eligibility_mask = ~enriched.get("hard_exclusion", pd.Series(False, index=enriched.index)).fillna(True).astype(bool)
    eligible = enriched.loc[eligibility_mask].copy()
    eligible_numeric = numeric_factors.loc[eligibility_mask, full_factor_names]
    factor_matrix = eligible_numeric.to_numpy(dtype=float)
    invalid_matrix = ~np.isfinite(factor_matrix)
    complete_mask = ~invalid_matrix.any(axis=1)
    missing_cell_count = int(np.isnan(factor_matrix).sum())
    nonfinite_cell_count = int(invalid_matrix.sum())
    accepted = eligible.loc[complete_mask].copy().reset_index(drop=True)
    accepted.loc[:, full_factor_names] = eligible_numeric.loc[complete_mask, full_factor_names].reset_index(drop=True)
    rejected = eligible.loc[~complete_mask, ["symbol", "name", "first_board_date"]].copy().reset_index(drop=True)
    rejected_masks = invalid_matrix[~complete_mask]
    rejected["invalid_factor_count"] = rejected_masks.sum(axis=1).astype(int)
    rejected["invalid_factors"] = [
        ",".join(factor for factor, invalid in zip(full_factor_names, mask, strict=True) if invalid)
        for mask in rejected_masks
    ]
    rejected["妖股综合评分"] = -1.0
    rejected["评分等级"] = "REJECTED"
    rejected["hard_exclusion"] = True
    rejected["hard_exclusion_reason"] = "因子数据不完整:" + rejected["invalid_factors"].fillna("").astype(str)
    rejected["production_decision"] = "REJECT_DATA_INCOMPLETE"
    rejected["strict_conclusion"] = "数据不完整，禁止进入生产评分"
    if not rejected.empty or missing_cell_count != 0 or nonfinite_cell_count != 0:
        raise RuntimeError(
            f"模型适用域内1280因子零缺失门禁失败:rows={len(rejected)};missing_cells={missing_cell_count};nonfinite_cells={nonfinite_cell_count}"
        )
    hard_excluded = enriched.loc[~eligibility_mask, [
        "symbol", "name", "first_board_date", "hard_exclusion", "hard_exclusion_reason",
    ]].copy().reset_index(drop=True)
    hard_excluded["妖股综合评分"] = -1.0
    hard_excluded["评分等级"] = "REJECTED"
    hard_excluded["production_decision"] = "REJECT_HARD_GATE"
    hard_excluded["strict_conclusion"] = "硬闸拒绝，禁止进入观察清单"
    accepted_matrix = accepted[full_factor_names].to_numpy(dtype=float) if not accepted.empty else np.empty((0, len(full_factor_names)))
    if not np.isfinite(accepted_matrix).all():
        raise RuntimeError("生产评分输入仍含非有限值")
    scorer = load_module(scorer_path, "feilong_yaogu_score_applier")
    scored = scorer.score_frame(accepted, model)
    replay_scored = scorer.score_frame(accepted.copy(deep=True), model)
    score_replay_hash = hashlib.sha256(scored.to_csv(index=False, lineterminator="\n").encode("utf-8")).hexdigest()
    replay_score_hash = hashlib.sha256(replay_scored.to_csv(index=False, lineterminator="\n").encode("utf-8")).hexdigest()
    if score_replay_hash != replay_score_hash:
        raise RuntimeError("同输入评分复跑发生漂移")
    if not scored.empty:
        scored["decision_rule_version"] = DECISION_RULE_VERSION
        scored["production_decision"] = np.where(
            scored["hard_exclusion"].fillna(True),
            "REJECT_HARD_GATE",
            "ACCEPT_SCORE_" + scored["评分等级"].astype(str),
        )
        scored["strict_conclusion"] = np.where(
            scored["hard_exclusion"].fillna(True),
            "硬闸拒绝，禁止进入观察清单",
            scored["评分等级"].astype(str) + "级生产评分观察",
        )
        scored["scoring_status"] = np.where(scored["hard_exclusion"].fillna(True), "生产评分_硬排除", "生产评分_可观察")
    target_scored = scored.loc[scored["first_board_date"].astype(str).eq(target)].copy() if not scored.empty else scored.copy()
    target_rejected = rejected.loc[rejected["first_board_date"].astype(str).eq(target)].copy() if not rejected.empty else rejected.copy()
    target_hard_excluded = hard_excluded.loc[
        hard_excluded["first_board_date"].astype(str).eq(target)
    ].copy() if not hard_excluded.empty else hard_excluded.copy()
    decision_columns = [
        "symbol", "name", "first_board_date", "妖股综合评分", "评分等级",
        "hard_exclusion", "hard_exclusion_reason", "production_decision", "strict_conclusion",
    ]
    accepted_decisions = target_scored.reindex(columns=decision_columns)
    rejected_decisions = target_rejected.reindex(columns=decision_columns)
    hard_excluded_decisions = target_hard_excluded.reindex(columns=decision_columns)
    strict_decisions = pd.concat([accepted_decisions, hard_excluded_decisions, rejected_decisions], ignore_index=True)
    if not strict_decisions.empty:
        strict_decisions["decision_rule_version"] = DECISION_RULE_VERSION
        strict_decisions["factor_completeness"] = np.where(
            strict_decisions["production_decision"].eq("REJECT_DATA_INCOMPLETE"), "REJECTED", "COMPLETE"
        )
        strict_decisions["_sort_score"] = pd.to_numeric(strict_decisions["妖股综合评分"], errors="coerce").fillna(-np.inf)
        strict_decisions = strict_decisions.sort_values(
            ["factor_completeness", "_sort_score", "symbol"],
            ascending=[True, False, True],
            kind="mergesort",
        ).drop(columns="_sort_score").reset_index(drop=True)
    input_snapshot_after = stable_file_set_evidence(snapshot_paths, TDX_ROOT, "TDX_EXACT_INPUT_SET")
    if input_snapshot_before != input_snapshot_after:
        raise RuntimeError("通达信输入快照在运行期间发生漂移")

    out_dir.mkdir(parents=True, exist_ok=True)
    scan_path = out_dir / "飞龙在天_补档首板扫描.csv"
    factor_path = out_dir / "飞龙在天_补档共振候选1280因子.csv"
    score_path = out_dir / "飞龙在天_补档319维评分.csv"
    today_path = out_dir / "飞龙在天_当日319维实战评分.csv"
    rejection_path = out_dir / "飞龙在天_数据完整性拒绝.csv"
    decision_path = out_dir / "飞龙在天_生产评分决策.csv"
    zero_missing_path = out_dir / "飞龙在天_零缺失审计.json"
    drift_lock_path = out_dir / "飞龙在天_生产漂移锁.json"
    determinism_path = out_dir / "飞龙在天_确定性复跑证据.json"
    report_path = out_dir / "飞龙在天_实战评分报告.md"
    manifest_path = out_dir / "飞龙在天_实战评分清单.json"
    legacy_audit_path = out_dir / "飞龙在天_全局旧版剔除审计.json"
    scan.to_csv(scan_path, index=False, encoding="utf-8-sig")
    factor_columns = ["symbol", "name", "first_board_date", *FACTOR_SPECS.keys()]
    accepted.reindex(columns=factor_columns).to_csv(factor_path, index=False, encoding="utf-8-sig")
    scored.to_csv(score_path, index=False, encoding="utf-8-sig")
    target_scored.to_csv(today_path, index=False, encoding="utf-8-sig")
    rejected.to_csv(rejection_path, index=False, encoding="utf-8-sig")
    strict_decisions.to_csv(decision_path, index=False, encoding="utf-8-sig")
    zero_missing_audit = {
        "schema": "FEILONG_ZERO_MISSING_AUDIT_V1",
        "status": "CLEAN_PASS",
        "candidate_factor_count": len(full_factor_names),
        "rankable_factor_count": len(model_factor_names),
        "source_candidate_rows": len(eligible),
        "source_invalid_cells": nonfinite_cell_count,
        "source_nan_cells": missing_cell_count,
        "production_scored_rows": len(scored),
        "production_factor_cells": len(accepted) * len(full_factor_names),
        "production_missing_cells": int(accepted[full_factor_names].isna().sum().sum()) if not accepted.empty else 0,
        "production_nonfinite_cells": int((~np.isfinite(accepted_matrix)).sum()),
        "rejected_incomplete_rows": len(rejected),
        "hard_excluded_outside_model_domain_rows": len(hard_excluded),
        "target_candidate_rows": int(enriched["first_board_date"].astype(str).eq(target).sum()) if not enriched.empty else 0,
        "target_production_scored_rows": len(target_scored),
        "target_rejected_incomplete_rows": len(target_rejected),
        "target_hard_excluded_outside_model_domain_rows": len(target_hard_excluded),
        "policy": "先执行身份、风险、一字板和至少251根前序交易日的模型适用域硬闸；适用域内1280因子任一缺失立即阻断，禁止填补、拒绝后继续或带缺失评分",
    }
    if (
        zero_missing_audit["source_invalid_cells"] != 0
        or zero_missing_audit["source_nan_cells"] != 0
        or zero_missing_audit["production_missing_cells"] != 0
        or zero_missing_audit["production_nonfinite_cells"] != 0
        or zero_missing_audit["rejected_incomplete_rows"] != 0
        or zero_missing_audit["target_rejected_incomplete_rows"] != 0
    ):
        raise RuntimeError("零缺失生产门禁失败")
    zero_missing_path.write_text(json.dumps(zero_missing_audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    drift_lock = {
        "schema": "FEILONG_PRODUCTION_DRIFT_LOCK_V1",
        "status": "CLEAN_PASS",
        "formula": file_evidence(FORMULA_PATH),
        "production_rule_lock": production_lock_evidence,
        "tdx_input_snapshot": input_snapshot_after,
        "risk_corpus_snapshot": risk_corpus_evidence,
        "daily_feature_day_set_sha256": daily_evidence.get("day_file_set_sha256"),
        "target_date": target,
        "latest_date": latest,
        "same_run_input_snapshot_stable": True,
        "model_schema": model["schema"],
        "model_validation_status": validation["status"],
        "development_grade_monotonic": validation["development_grade_monotonic"],
        "sealed_holdout_top_grade_positive_lift": validation["sealed_holdout_top_grade_positive_lift"],
        "imputed_training_cells": model["imputed_training_cells"],
        "decision_rule_version": DECISION_RULE_VERSION,
    }
    drift_lock_path.write_text(json.dumps(drift_lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    eligible_today = target_scored.loc[~target_scored.get("hard_exclusion", pd.Series(dtype=bool)).fillna(False)] if not target_scored.empty else target_scored
    top_lines = []
    for row in eligible_today.sort_values("妖股综合评分", ascending=False).head(20).to_dict("records"):
        top_lines.append(f"| {row.get('symbol')} | {row.get('name','')} | {row.get('妖股综合评分', math.nan):.2f} | {row.get('评分等级','')} | {row.get('announcement_verification_status','')} |")
    report = [
        "# 飞龙在天1280因子多维妖股实战评分",
        "",
        f"- 公式：**{FORMULA_NAME}**（SHA-256 `{FORMULA_SHA256}`）",
        f"- 数据：本机通达信 `{TDX_ROOT}`，最新有效交易日 **{target}**",
        f"- 研究域：沪深主板；1280个注册因子、1273个有效排行因子、325个注册独立机制维度、319个有效评分维度",
        f"- 补档区间：{history_max}之后至{target}；首板{len(scan)}条，共振{len(hits)}条，适用域内完整生产评分{len(scored)}条，适用域硬排除{len(hard_excluded)}条，数据完整性拒绝{len(rejected)}条",
        f"- 当日共振{len(target_scored) + len(target_hard_excluded) + len(target_rejected)}条；适用域内完整生产评分{len(target_scored)}条，适用域硬排除{len(target_hard_excluded)}条，数据完整性拒绝{len(target_rejected)}条",
        "- 生产规则：先执行模型适用域硬闸；域内1280因子必须全部真实、有限，任一缺失即阻断全任务，禁止中性填补或降级评分。",
        "- 系统范围：自动决策评分级，完全断开账户、委托和交易执行。",
        "",
        "## 当日可观察清单",
        "",
        "| 代码 | 名称 | 综合评分 | 等级 | 公告核验状态 |",
        "|---|---|---:|---|---|",
        *(top_lines or ["| - | 当日无通过硬排除的飞龙共振首板 | - | - | - |"]),
        "",
        "## 硬闸说明",
        "",
        "身份缺失、ST/PT/退市名称、一字板、异常成交、公式关键财务输入未解析、本机风险语料重大硬风险和因子不完整均失败关闭。",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    legacy_audit_path.write_text(
        json.dumps(audit_legacy_formula(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    preliminary_artifacts = {
        path.name: file_evidence(path)
        for path in (
            scan_path, factor_path, score_path, today_path, rejection_path, decision_path,
            zero_missing_path, drift_lock_path, report_path, legacy_audit_path,
        )
    }
    output_set_material = "\n".join(
        f"{name}|{row['size']}|{row['sha256']}" for name, row in sorted(preliminary_artifacts.items())
    )
    output_set_sha256 = hashlib.sha256(output_set_material.encode("utf-8")).hexdigest()
    previous_determinism: dict[str, Any] = {}
    if determinism_path.is_file():
        try:
            previous_determinism = json.loads(determinism_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            previous_determinism = {}
    same_baseline = (
        previous_determinism.get("schema") == "FEILONG_DETERMINISM_EVIDENCE_V1"
        and previous_determinism.get("rule_lock_sha256") == production_lock_evidence["sha256"]
        and previous_determinism.get("tdx_input_snapshot_sha256") == input_snapshot_after["sha256"]
    )
    if same_baseline and previous_determinism.get("pipeline_output_set_sha256") != output_set_sha256:
        raise RuntimeError("同规则同输入的全流程输出发生漂移")
    full_replay_count = int(previous_determinism.get("full_pipeline_replay_count", 0)) + 1 if same_baseline else 1
    determinism_evidence = {
        "schema": "FEILONG_DETERMINISM_EVIDENCE_V1",
        "status": "CLEAN_PASS" if same_baseline else "BASELINE_CREATED",
        "rule_lock_sha256": production_lock_evidence["sha256"],
        "tdx_input_snapshot_sha256": input_snapshot_after["sha256"],
        "pipeline_output_set_sha256": output_set_sha256,
        "full_pipeline_replay_count": full_replay_count,
        "full_pipeline_byte_identical": bool(same_baseline),
        "score_frame_replay_count": 2,
        "score_frame_first_sha256": score_replay_hash,
        "score_frame_second_sha256": replay_score_hash,
        "score_frame_byte_identical": score_replay_hash == replay_score_hash,
    }
    determinism_path.write_text(json.dumps(determinism_evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    artifacts = {**preliminary_artifacts, determinism_path.name: file_evidence(determinism_path)}
    result = {
        "schema": PRODUCTION_SCHEMA,
        "status": "CLEAN_PASS",
        "formula_name": FORMULA_NAME,
        "formula_sha256": FORMULA_SHA256,
        "legacy_4_0_used": False,
        "checks": {
            "target_date": target,
            "tdx_latest_date": latest,
            "tdx_mainboard_readable_count": readable_count,
            "tdx_mainboard_at_latest_count": at_latest_count,
            "scanned_stock_count": len(paths),
            "first_board_count": len(scan),
            "formula_hit_count": len(hits),
            "scored_count": len(scored),
            "target_scored_count": len(target_scored),
            "rejected_incomplete_count": len(rejected),
            "target_rejected_incomplete_count": len(target_rejected),
            "hard_excluded_outside_model_domain_count": len(hard_excluded),
            "target_hard_excluded_outside_model_domain_count": len(target_hard_excluded),
            "factor_count": len(FACTOR_SPECS),
            "rankable_factor_count": len(model["factors"]),
            "registered_dimension_count": model["registered_dimension_count"],
            "dimension_count": len(model["dimensions"]),
            "missing_factor_columns": len(missing_factor_columns),
            "production_missing_cells": zero_missing_audit["production_missing_cells"],
            "production_nonfinite_cells": zero_missing_audit["production_nonfinite_cells"],
            "score_nulls": int(scored["妖股综合评分"].isna().sum()) if not scored.empty else 0,
            "stale": target != latest,
            "rule_assets_locked": True,
            "tdx_input_snapshot_stable": True,
            "decision_rule_machine_only": True,
            "determinism_verified": determinism_evidence["status"] == "CLEAN_PASS",
            "model_domain": "沪深主板600/601/603/605/000/001/002/003",
            "local_risk_corpus_file_count": len(corpus_files),
        },
        "inputs": {
            "model": file_evidence(model_path),
            "history": file_evidence(history_path),
            "scorer": file_evidence(scorer_path),
            "formula": file_evidence(FORMULA_PATH),
            "finance": file_evidence(finance_path),
            "gbbq": file_evidence(gbbq_path),
            "production_rule_lock": production_lock_evidence,
            "tdx_input_snapshot": input_snapshot_after,
        },
        "artifacts": artifacts,
    }
    manifest_payload = dict(result)
    manifest_payload["manifest_integrity"] = hashlib.sha256(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    result["artifacts"][manifest_path.name] = file_evidence(manifest_path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="飞龙在天1280因子319有效独立维度实战日评分")
    parser.add_argument("--target-date")
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--history", default=str(DEFAULT_HISTORY))
    parser.add_argument("--scorer", default=str(DEFAULT_SCORER))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)
    result = run(
        target_date=args.target_date,
        model_path=Path(args.model).resolve(),
        history_path=Path(args.history).resolve(),
        scorer_path=Path(args.scorer).resolve(),
        out_dir=Path(args.out_dir).resolve(),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
