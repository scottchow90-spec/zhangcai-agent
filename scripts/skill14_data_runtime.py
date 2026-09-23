#!/usr/bin/env python3
"""Runtime-owned data archive and data-gate service for the 14 desktop skills.

This script deliberately does not infer market facts.  It snapshots local data,
records provenance, evaluates declared prerequisites and writes every result to
the application's writable data root.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import struct
import sys
import uuid
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APP_ROOT = Path(os.environ.get("ZHANGCAI_APP_ROOT", Path(__file__).resolve().parents[1]))
DATA_ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR", APP_ROOT / "app-data"))
_tdx_root_text = (
    os.environ.get("ZHANGCAI_TDX_ROOT")
    or os.environ.get("TDX_ROOT")
    or ""
).strip()
_packaged_runtime = os.environ.get("ZHANGCAI_PACKAGED") == "1"
# Path("") resolves to the process working directory. In the packaged EXE
# that made an unset TDX directory look like the resource-library root and
# allowed a status probe to overwrite a valid portable formula package with a
# missing manifest. Keep an explicit, impossible sentinel instead.
TDX_ROOT = Path(_tdx_root_text) if _tdx_root_text else (
    Path(os.environ.get("ZHANGCAI_DEV_TDX_ROOT", r"C:\new_tdx_mock"))
    if not _packaged_runtime
    else DATA_ROOT / "runtime" / "__tdx_root_not_configured__"
)
CATALOG_PATH = APP_ROOT / "config" / "skill14-catalog.json"
ARCHIVE_ROOT = Path(os.environ.get("ZHANGCAI_SKILL_ARCHIVE_DIR", APP_ROOT / "skill-archives"))
MARKET_BASELINE_PATH = APP_ROOT / "lib" / "market.json"
PACKAGE_SOURCE_DIR = Path(os.environ.get(
    "ZHANGCAI_MARKET_DATA_SKILL_DIR",
    APP_ROOT.parent / "技能导出电脑版" / "A股行情资讯全接口与数据能力大全_WorkBuddy电脑版_20260908-014459",
))
FORMULA_SOURCE_RELATIVE_PATHS = (
    "T0002/PriLoc.dat",
    "T0002/PriGS.dat",
    "T0002/PriCS.dat",
    "T0002/PriPack.dat",
    "T0002/gs_bak/大牛线撑压版.tn6",
    "T0002/gs_bak/飞龙在天.tn6",
    "T0002/gs_bak/游资资金监控.tn6",
    "T0002/gs_bak/机构资金监控.tn6",
    "T0002/gs_bak/庄家资金监控.tn6",
    "T0002/gs_bak/黄金点火选股.tn6",
    "PYPlugins/user/tdxdata_test.py",
)

# This is the source package's 12-source gap list, kept as data rather than
# inferred from a successful HTTP response.  The package explicitly requires
# separating "declared in source" from "snapshotted in this runtime".
PACKAGE_SOURCE_GAP_SPECS = (
    {"id": "tencent", "name": "腾讯财经", "capability": "实时行情、估值、换手率、股本", "adapter": "supplemental_data_sync.py::parse_tencent_quote", "output": "evidence/supplemental/<trade-date>/<code>.<market>.json"},
    {"id": "sina", "name": "新浪财经", "capability": "财报三表、复权因子、行情备援", "adapter": "supplemental_data_sync.py::financial_snapshot", "output": "evidence/supplemental/<trade-date>/<code>.<market>.json"},
    {"id": "baidu", "name": "百度股市通", "capability": "带均线日 K", "adapter": "scripts/package_source_sync.py::fetch_baidu", "output": "evidence/package-sources/<trade-date>/baidu/snapshot.json"},
    {"id": "ths", "name": "同花顺", "capability": "一致预期、热点、热榜、涨停原因", "adapter": "scripts/package_source_sync.py::fetch_ths; news_sync.py", "output": "evidence/package-sources/<trade-date>/ths/snapshot.json"},
    {"id": "iwencai", "name": "问财 IWencai", "capability": "自然语言选股/研报", "adapter": "blocked without explicit API key", "output": "evidence/package-sources/<trade-date>/iwencai/"},
    {"id": "cls", "name": "财联社", "capability": "7×24 电报", "adapter": "news_sync.py::cls_roll", "output": "news/<trade-date>/"},
    {"id": "baostock", "name": "BaoStock", "capability": "历史估值、上市/退市日", "adapter": "package catalog only; optional dependency", "output": "evidence/package-sources/<trade-date>/baostock/"},
    {"id": "sw", "name": "申万研究", "capability": "行业分类变迁史", "adapter": "scripts/package_source_sync.py::fetch_sw", "output": "evidence/package-sources/<trade-date>/sw/snapshot.json"},
    {"id": "cninfo", "name": "巨潮资讯", "capability": "公告、互动易", "adapter": "scripts/package_source_sync.py::fetch_cninfo", "output": "evidence/package-sources/<trade-date>/cninfo/snapshot.json"},
    {"id": "exchange-official", "name": "沪深交易所官方", "capability": "公告、监管、龙虎榜备援", "adapter": "package catalog only; official-source adapter pending", "output": "evidence/package-sources/<trade-date>/exchange-official/"},
    {"id": "macro", "name": "人民银行/国家统计局", "capability": "社融、PMI", "adapter": "scripts/package_source_sync.py::fetch_nbs/fetch_pbc", "output": "evidence/package-sources/<trade-date>/macro/snapshot.json"},
    {"id": "public-web", "name": "公开网页工具与舆情站点", "capability": "文章、RSS、社区和动态网页", "adapter": "public-web-toolkit catalog only; bounded on-demand", "output": "evidence/package-sources/<trade-date>/public-web/"},
)


def utc_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def tdx_root_available(root: Path = TDX_ROOT) -> bool:
    return root.is_dir() and (root / "vipdoc").is_dir() and (root / "T0002").is_dir()


def supplemental_stock_coverage(trade_date: str) -> dict[str, Any]:
    """Summarize code-level financial/share-capital snapshots already saved."""
    root = DATA_ROOT / "evidence" / "supplemental" / trade_date
    files = sorted(root.glob("[0-9][0-9][0-9][0-9][0-9][0-9].*.json")) if root.is_dir() else []
    financial_codes: list[str] = []
    share_codes: list[str] = []
    files_checked = 0
    for path in files:
        value = read_json(path, {})
        if not isinstance(value, dict):
            continue
        files_checked += 1
        code = str(value.get("stock", {}).get("code") or path.stem.split(".", 1)[0]) if isinstance(value.get("stock"), dict) else path.stem.split(".", 1)[0]
        coverage = value.get("coverage") if isinstance(value.get("coverage"), dict) else {}
        if coverage.get("financial") is True:
            financial_codes.append(code)
        if coverage.get("share_capital") is True:
            share_codes.append(code)
    status = "partial" if financial_codes or share_codes else "missing"
    return {
        "status": status,
        "trade_date": trade_date,
        "path": f"evidence/supplemental/{trade_date}/",
        "file_count": files_checked,
        "financial": {"status": "available" if financial_codes else "missing", "covered_codes": sorted(set(financial_codes)), "covered_count": len(set(financial_codes))},
        "share_capital": {"status": "available" if share_codes else "missing", "covered_codes": sorted(set(share_codes)), "covered_count": len(set(share_codes))},
        "reason": "已按股票落盘；未请求的股票仍按需补采。" if files_checked else "尚未生成目标交易日的个股财务/股本快照。",
    }


def package_source_gap_report() -> dict[str, Any]:
    """Bind the imported all-interface package to current Harness assets.

    The report is intentionally explicit: source code and endpoint examples
    from the package do not become available data until a dated local artifact
    exists and passes the normal provenance checks.
    """
    daily = read_json(DATA_ROOT / "status" / "tdx-daily-history.json", {})
    public = read_json(DATA_ROOT / "public" / "latest.json", {})
    trade_date = str((daily or {}).get("trade_date") or (public or {}).get("date") or "").replace("-", "")
    source_manifest = read_json(DATA_ROOT / "evidence" / "sources" / "latest.json", {})
    source_rows = source_manifest.get("sources", []) if isinstance(source_manifest, dict) else []
    source_status = {str(row.get("id")): row for row in source_rows if isinstance(row, dict)}
    stock_coverage = supplemental_stock_coverage(trade_date) if trade_date else {"status": "missing"}
    fallback_root = DATA_ROOT / "market" / "daily" / "fallback" / trade_date if trade_date else DATA_ROOT / "market" / "daily" / "fallback"
    fallback_files = len(list(fallback_root.glob("*.jsonl"))) if fallback_root.is_dir() else 0
    public_research = public_research_status()

    package_dir = PACKAGE_SOURCE_DIR if PACKAGE_SOURCE_DIR.is_dir() else DATA_ROOT / "skills" / "packages" / "market-data-capabilities"
    package_snapshot_root = DATA_ROOT / "evidence" / "package-sources" / trade_date if trade_date else DATA_ROOT / "evidence" / "package-sources"
    package_skill = read_json(package_dir / "references" / "接口与网站穷举清单.json", {})
    package_policy = read_json(package_dir / "references" / "authority" / "stock_data_source_policy.json", {})
    package_info = read_json(DATA_ROOT / "harness" / "context" / "package-source-inventory.json", {})
    source_items: list[dict[str, Any]] = []
    for spec in PACKAGE_SOURCE_GAP_SPECS:
        observed = source_status.get(spec["id"], {})
        runtime_status = str(observed.get("status") or "declared_not_snapshotted")
        package_artifact = package_snapshot_root / spec["id"] / "snapshot.json"
        package_value = read_json(package_artifact, {}) if package_artifact.is_file() else {}
        if package_artifact.is_file() and isinstance(package_value, dict):
            # A full SW history is genuinely available.  Code-batched
            # captures and latest-period macro snapshots are useful but only
            # partial for a production/full-market contract.
            if spec["id"] == "sw" and package_value.get("scope") == "full_history":
                runtime_status = "available" if package_value.get("status") == "available" else "degraded"
            else:
                runtime_status = "partial" if package_value.get("status") == "available" else str(package_value.get("status") or "degraded")
        if spec["id"] in {"tencent", "sina"} and stock_coverage.get("file_count", 0):
            # These adapters are intentionally per-stock.  A finite batch of
            # files must never be reported as full-market availability.
            runtime_status = "partial"
        if spec["id"] == "cls":
            runtime_status = "available" if public_research.get("multi_source_records", {}).get("cls", 0) else runtime_status
        artifact_paths = [str(package_artifact.relative_to(DATA_ROOT)).replace("\\", "/")] if package_artifact.is_file() else (observed.get("paths", []) if isinstance(observed, dict) else [])
        if spec["id"] in {"tencent", "sina"} and stock_coverage.get("file_count", 0):
            artifact_paths = [stock_coverage.get("path", f"evidence/supplemental/{trade_date}/")]
        if spec["id"] == "cls" and public_research.get("multi_source_records", {}).get("cls", 0):
            artifact_paths = [f"news/{trade_date}/multi-source-news-*.json"]
        source_items.append({
            **spec,
            "declared_status": runtime_status,
            "current_status": runtime_status,
            "source_package": str(package_dir),
            "package_policy_version": package_policy.get("version") if isinstance(package_policy, dict) else None,
            "last_artifact": artifact_paths,
            "missing_reason": {
                "blocked": "需要用户明确提供 API key；本地 Harness 不读取或导出密钥。",
                "not_configured": "压缩包仅提供接口/源码目录，3003 尚未配置安全只读适配器。",
                "declared_not_snapshotted": "已在包内声明，但尚无目标交易日可追溯快照。",
                "on_demand": "已有按股票按需适配器，尚未形成全市场覆盖。",
                "partial": "已有部分股票/字段快照，未覆盖全部目标范围。",
                "available": "",
            }.get(runtime_status, "需要先检查实际快照、source_date、retrieved_at 和 sha256。"),
        })

    data_gaps = [
        {"id": "v65_secondary_daily", "name": "V6.5 独立第二行情源日线核验", "status": "partial" if fallback_files else "missing", "action": "使用 daily_data_recovery.py 仅补明确目标交易日，并把 source/source_date/source_sha256 传入 Harness。", "path": f"market/daily/fallback/{trade_date}/"},
        {"id": "v65_industry_pit", "name": "行业六维历史时点数据", "status": "missing", "action": "需要同日行业成员、至少21根行业历史 K 线、资金和事件覆盖；当前仅有行业名称/当日聚合，不可补造。", "path": f"evidence/package-sources/{trade_date}/sw/"},
        {"id": "v65_consensus", "name": "生产授权与全市场双路共识", "status": "blocked", "action": "本地评分仍是研究性结果；需全市场主模型、独立二源、事件风险与生产验证全部闭合后才能授权。", "path": "reports/daily/<trade-date>/"},
        {"id": "public_research_same_day", "name": "目标交易日同日资讯证据", "status": public_research.get("status", "missing"), "action": "多源快讯按当前时点采集；历史源已过保留窗口时必须保留 0 条同日记录，不用后续新闻冒充。", "path": "evidence/public/"},
        {"id": "financial", "name": "个股财务三表", "status": stock_coverage.get("financial", {}).get("status", "missing") if isinstance(stock_coverage, dict) else "missing", "action": "使用新浪三表按股票补采，保留报告期并按目标日期过滤。", "path": f"evidence/supplemental/{trade_date}/<code>.<market>.json"},
        {"id": "share_capital", "name": "流通股本/总股本/市值", "status": stock_coverage.get("share_capital", {}).get("status", "missing") if isinstance(stock_coverage, dict) else "missing", "action": "使用腾讯公开报价按股票补采，必须保留 quote_time 与 source_sha256。", "path": f"evidence/supplemental/{trade_date}/<code>.<market>.json"},
    ]
    missing_items = [item for item in [*source_items, *data_gaps] if item.get("current_status", item.get("status")) not in {"available", "partial"}]
    report = {
        "schema": "ZHANGCAI_PACKAGE_SOURCE_GAP_REPORT_V1",
        "generated_at": utc_now(),
        "trade_date": trade_date,
        "package": {
            "root": str(package_dir),
            "archive": package_info.get("archive") if isinstance(package_info, dict) else "",
            "version": package_info.get("archive_version") if isinstance(package_info, dict) else None,
            "canonical_skill_count": package_info.get("canonical_skill_count") if isinstance(package_info, dict) else None,
            "site_host_count": package_info.get("site_host_count") if isinstance(package_info, dict) else None,
            "core_data_layers": package_info.get("core_data_layers") if isinstance(package_info, dict) else None,
            "core_endpoint_count": package_info.get("core_endpoint_count") if isinstance(package_info, dict) else None,
            "interface_inventory": "references/接口与网站穷举清单.json",
            "policy": "references/authority/stock_data_source_policy.json",
        },
        "source_items": source_items,
        "data_gaps": data_gaps,
        "missing_count": len(missing_items),
        "missing_items": missing_items,
        "supplemented": {
            "financial_share_capital": stock_coverage,
            "public_research": public_research,
            "secondary_daily_files": fallback_files,
        },
        "rules": [
            "包内源码/端点目录不等于现场可用数据。",
            "每个补充源必须保存 source、source_url_or_local_root、source_date、retrieved_at、status、error_or_reason、sha256。",
            "缺失数据只能显示 DEGRADED/BLOCKED，不能用模型、成交额或价格推算替代。",
            "问财、需要登录/密钥的连接器保持 blocked；不读取或导出凭据。",
            "当前日期与历史目标日期必须分开；后续快照不能覆盖历史交易日真值。",
        ],
    }
    write_json(DATA_ROOT / "harness" / "context" / "package-source-gap-report.json", report)
    write_json(DATA_ROOT / "harness" / "context" / "package-data-routing.json", {
        "schema": "ZHANGCAI_PACKAGE_DATA_ROUTING_V1",
        "generated_at": report["generated_at"],
        "package": report["package"],
        "routes": source_items,
        "data_gaps": data_gaps,
        "read_order": ["harness/context/local-data-page.json", "harness/context/package-data-routing.json", "harness/context/package-source-gap-report.json", "evidence/sources/<trade-date>/manifest.json", "对应数据快照"],
    })
    return report


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def catalog() -> dict[str, Any]:
    value = read_json(CATALOG_PATH)
    if not isinstance(value, dict) or not isinstance(value.get("skills"), list):
        raise RuntimeError(f"技能目录无效：{CATALOG_PATH}")
    return value


def compact_trade_date(value: Any) -> str:
    """Normalize a date-like value without accepting arbitrary timestamps."""
    text = str(value or "").strip()
    match = re.search(r"(20\d{2})[-/]?(\d{2})[-/]?(\d{2})", text)
    return "".join(match.groups()) if match else ""


def report_sort_timestamp(value: Any) -> float:
    """Return a comparable timestamp for mixed legacy report date formats."""
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except ValueError:
        pass
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 14:
        try:
            return datetime.strptime(digits[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            pass
    if len(digits) >= 8:
        try:
            return datetime.strptime(digits[:8], "%Y%m%d").replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            pass
    return 0.0


def known_market_trade_dates() -> list[str]:
    """Read dates already produced by the local market pipeline.

    This is intentionally local-only.  It does not use today's wall-clock
    date because a weekend, holiday, or a delayed close must not be treated as
    a new trading day.  The runtime market snapshot is the strongest signal;
    the public snapshot and the daily refresh state are supporting evidence.
    """
    candidates: list[str] = []
    sources = (
        (DATA_ROOT / "runtime" / "market-latest.json", ("tradeDate", "trade_date", "date")),
        (DATA_ROOT / "public" / "latest.json", ("date", "tradeDate", "trade_date")),
        (DATA_ROOT / "runtime" / "daily-refresh-state.json", ("date", "tradeDate", "trade_date")),
    )
    for path, fields in sources:
        value = read_json(path, {})
        if not isinstance(value, dict):
            continue
        for field in fields:
            date = compact_trade_date(value.get(field))
            if date:
                candidates.append(date)
        # A market snapshot can legitimately omit its top-level date while
        # still carrying a complete same-day stock universe.
        if path.name == "market-latest.json":
            rows = value.get("allStocks") or value.get("stocks") or []
            if isinstance(rows, list):
                candidates.extend(
                    date
                    for row in rows
                    if isinstance(row, dict)
                    for date in [compact_trade_date(row.get("date"))]
                    if date
                )
    daily_index = read_json(DATA_ROOT / "market" / "daily" / "index" / "daily-data-index.json", {})
    if isinstance(daily_index, dict) and isinstance(daily_index.get("dates"), dict):
        candidates.extend(
            compact_trade_date(key)
            for key, value in daily_index["dates"].items()
            if isinstance(value, dict) and (value.get("trade_date") or value.get("tdx_available"))
        )
    return sorted(set(date for date in candidates if date))


def expected_market_trade_date(daily: dict[str, Any] | None = None) -> str:
    """Return the latest locally observed analysis date, not wall-clock date."""
    requested = compact_trade_date(os.environ.get("ZHANGCAI_DAILY_REQUESTED_TRADE_DATE", ""))
    if requested:
        return requested
    candidates = known_market_trade_dates()
    if isinstance(daily, dict):
        archive_date = compact_trade_date(daily.get("trade_date"))
        if archive_date:
            candidates.append(archive_date)
    return max(candidates) if candidates else ""


def daily_archive_freshness(daily: dict[str, Any] | None) -> dict[str, Any]:
    """Select the newest usable local daily source without requiring today's bar.

    The bridge supplies the latest date physically present in the configured
    Tongdaxin ``.day`` files.  Prefer that source when it is newer than the
    resource-library archive, while retaining the archive as a fallback.  A
    date mismatch or partial universe is reported as DEGRADED, not as a
    missing daily-data gate; individual strategy contracts still validate
    their own history length, symbol coverage, formulas, and other evidence.
    """
    value = daily if isinstance(daily, dict) else {}
    archive_date = compact_trade_date(value.get("trade_date"))
    expected_date = expected_market_trade_date(value)
    issues: list[str] = []
    archive_file = str(value.get("file") or ("market/daily/aggregate/tdx-bars.jsonl" if archive_date else ""))
    archive_path = DATA_ROOT / archive_file if archive_file else DATA_ROOT / "__missing__"
    day_manifest_path = DATA_ROOT / "market" / "daily" / archive_date / "manifest.json" if archive_date else DATA_ROOT / "__missing__"
    day_manifest = read_json(day_manifest_path, {})

    raw_status = str(value.get("status") or "missing")
    if raw_status != "available":
        issues.append(f"TDX归档状态为 {value.get('status') or 'missing'}")
    if not archive_date:
        issues.append("权威归档没有 trade_date")
    if not archive_path.is_file() or archive_path.stat().st_size <= 0:
        issues.append(f"归档文件不存在或为空：{archive_file or '未声明'}")
    manifest_valid = isinstance(day_manifest, dict) and day_manifest.get("schema") == "ZHANGCAI_TDX_DAILY_ARCHIVE_V1"
    if not manifest_valid:
        issues.append(f"缺少 {archive_date or '目标日'} 的正式 manifest.json")
    else:
        if str(day_manifest.get("trade_date") or "") != archive_date:
            issues.append("日目录 manifest 的 trade_date 与权威状态不一致")
        if str(day_manifest.get("status") or "") != "available":
            issues.append("日目录 manifest 不是 available")
        if int(day_manifest.get("bar_records") or 0) != int(value.get("bar_records") or 0):
            issues.append("日目录 manifest 与权威状态的 bar_records 不一致")
    current_symbols = int(value.get("current_trade_date_symbols") or value.get("latest_date_source_files") or 0)
    archive_usable = bool(
        archive_date
        and archive_path.is_file()
        and archive_path.stat().st_size > 0
        and manifest_valid
        and str(day_manifest.get("trade_date") or "") == archive_date
        and str(day_manifest.get("status") or "") == "available"
        and int(value.get("bar_records") or day_manifest.get("bar_records") or 0) > 0
        and int(value.get("archived_symbols") or day_manifest.get("archived_symbols") or 0) > 0
    )
    try:
        live_symbols = max(0, int(os.environ.get("ZHANGCAI_TDX_LATEST_DAILY_SYMBOLS", "0") or 0))
    except (TypeError, ValueError):
        live_symbols = 0
    live_date = compact_trade_date(os.environ.get("ZHANGCAI_TDX_LATEST_DAILY_DATE", ""))
    live_root = str(os.environ.get("ZHANGCAI_TDX_ROOT") or os.environ.get("TDX_ROOT") or "").strip()
    live_usable = bool(live_date and live_symbols > 0 and live_root)
    use_live = live_usable and (not archive_usable or live_date > archive_date)
    selected_date = live_date if use_live else archive_date if archive_usable else ""
    selected_source = "tdx_live_day_files" if use_live else "resource_library_archive" if archive_usable else ""
    selected_symbols = live_symbols if use_live else current_symbols if archive_usable else 0
    coverage_complete = selected_symbols >= 3000
    date_mismatch = bool(expected_date and selected_date and selected_date != expected_date)
    archive_behind = bool(use_live and archive_date and live_date > archive_date)
    if not selected_date:
        status = "missing"
        reason = "；".join(issues) or "没有可用的本地日线文件或归档。"
    else:
        if date_mismatch:
            issues.append(f"请求日线 {expected_date} 尚未落盘，实际使用最新可用日线 {selected_date}")
        if archive_behind:
            issues.append(f"resource-library 归档截至 {archive_date}；本次优先读取通达信本地日线 {live_date}")
        if not coverage_complete:
            issues.append(f"当前日线覆盖 {selected_symbols} 个证券；全市场范围仍需由策略自身的数据契约校验")
        # A live TDX file set is not the same thing as a refreshed unified
        # archive. Keep that distinction visible even when the selected date
        # matches the requested trading date.
        status = "degraded" if date_mismatch or archive_behind or not coverage_complete or use_live else "available"
        reason = "；".join(issues) if status == "degraded" else ""
    return {
        "status": status,
        "usable": bool(selected_date),
        "expected_trade_date": expected_date,
        "archive_trade_date": archive_date,
        "requested_trade_date": expected_date,
        "selected_trade_date": selected_date,
        "fallback_trade_date": selected_date if date_mismatch or archive_behind else "",
        "selected_source": selected_source,
        "selected_source_root": live_root if use_live else str(DATA_ROOT),
        "live_tdx_trade_date": live_date,
        "live_tdx_symbol_count": live_symbols,
        "archive_usable": archive_usable,
        "archive_current_trade_date_symbols": current_symbols,
        "coverage_complete": coverage_complete,
        "selected_symbol_count": selected_symbols,
        "archive_file": archive_file,
        "manifest_path": f"market/daily/{archive_date}/manifest.json" if archive_date else "",
        "manifest_exists": day_manifest_path.is_file(),
        "file_exists": archive_path.is_file(),
        "current_trade_date_symbols": selected_symbols,
        "archived_symbols": int(value.get("archived_symbols") or 0),
        "bar_records": int(value.get("bar_records") or 0),
        "issues": issues,
        "reason": reason,
    }


def decorate_daily_asset(daily: Any) -> dict[str, Any]:
    """Attach date-aware usability state while preserving raw manifest fields."""
    value = dict(daily) if isinstance(daily, dict) else {
        "status": "missing", "asset": "tdx_daily_history", "reason": "尚未归档本地日线。"
    }
    freshness = daily_archive_freshness(value)
    value["archive_status"] = value.get("status", "missing")
    value["expected_trade_date"] = freshness.get("expected_trade_date", "")
    value["freshness_status"] = freshness.get("status", "missing")
    value["freshness_reason"] = freshness.get("reason", "")
    value["freshness"] = freshness
    if freshness.get("usable") and freshness["status"] == "degraded":
        value["status"] = "degraded"
        value["reason"] = freshness.get("reason") or "归档日期与当前本地行情不一致。"
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def baseline_security_metadata() -> dict[tuple[str, str], dict[str, Any]]:
    """Load the app's last-known identity fields without copying price history."""
    value = read_json(MARKET_BASELINE_PATH, {})
    rows = value.get("allStocks", []) if isinstance(value, dict) else []
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        code = str(row.get("code") or "")[-6:]
        market = str(row.get("market") or "").lower()
        if code and market:
            result[(code, market)] = row
    return result


def tdx_security_metadata() -> dict[tuple[str, str], dict[str, Any]]:
    """Read the read-only TDX security-name index (TNF) for current identities."""
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for market, filename in (("sh", "shs.tnf"), ("sz", "szs.tnf"), ("bj", "bjs.tnf")):
        path = TDX_ROOT / "T0002" / "hq_cache" / filename
        try:
            payload = path.read_bytes()
        except OSError:
            continue
        # TDX TNF uses fixed 360-byte rows; code and GBK name are stable in
        # the local files and reading them never changes the TDX source.
        for offset in range(0, max(0, len(payload) - 359), 360):
            code = payload[offset + 50:offset + 56].split(b"\x00", 1)[0].decode("ascii", "ignore")
            name = payload[offset + 81:offset + 145].split(b"\x00", 1)[0].decode("gbk", "ignore").strip()
            if len(code) == 6 and code.isdigit() and name:
                result[(code, market)] = {"name": name, "identity_source": str(path)}
    return result


def write_local_data_page(assets: dict[str, Any] | None = None) -> dict[str, Any]:
    """Write the stable path/index page consumed by Harness and future EXE builds."""
    daily_manifest = read_json(DATA_ROOT / "status" / "tdx-daily-history.json", {})
    daily_freshness = daily_archive_freshness(daily_manifest if isinstance(daily_manifest, dict) else {})
    trade_date = str(daily_manifest.get("trade_date") or "") if isinstance(daily_manifest, dict) else ""
    date_folder = trade_date or "<trade-date>"
    daily_file = str(daily_manifest.get("file") or "market/daily/aggregate/tdx-bars.jsonl") if isinstance(daily_manifest, dict) else "market/daily/aggregate/tdx-bars.jsonl"
    daily_manifest_file = f"market/daily/{date_folder}/manifest.json"
    aggregate_rel = "market/daily/aggregate/tdx-bars.jsonl"
    aggregate_path = DATA_ROOT / aggregate_rel
    daily_index = read_json(DATA_ROOT / "market" / "daily" / "index" / "daily-data-index.json", {})
    fallback_date = (daily_index.get("dates", {}).get(trade_date, {}) if isinstance(daily_index, dict) else {})
    supplemental_file = f"evidence/supplemental/{date_folder}/market.json"
    catalog_value = catalog()
    asset_specs = {item.get("id"): item for item in catalog_value.get("dataAssets", []) if isinstance(item, dict)}
    current_assets = assets or {}
    paths = {
        "tdx_daily_history": daily_file,
        "tdx_daily_manifest": daily_manifest_file,
        "tdx_daily_delta": str(daily_manifest.get("delta_file") or "") if isinstance(daily_manifest, dict) else "",
        "tdx_daily_index": "market/daily/index/tdx-symbol-index.json",
        "daily_data_index": "market/daily/index/daily-data-index.json",
        "tdx_daily_aggregate": aggregate_rel if aggregate_path.is_file() else daily_file,
        "tdx_daily_fallback": f"market/daily/fallback/{date_folder}/",
        "tdx_daily_fallback_bars": f"market/daily/fallback/{date_folder}/<symbol>.jsonl",
        "supplemental_market": supplemental_file,
        "supplemental_stock": f"evidence/supplemental/{date_folder}/<code>.<market>.json",
        "security_master": "market/security-master/",
        "limit_up_pool": "public/limit-up/",
        "lhb_data": "public/lhb/",
        "public_research": "evidence/public/",
        "tdx_tq_formula": "evidence/formulas/",
        "tdx_formula_source_archive": "evidence/formulas/package/",
        "unified_source_manifest": "evidence/sources/latest.json",
        "unified_source_verification": "evidence/sources/latest-verification.json",
        "package_source_inventory": "harness/context/package-source-inventory.json",
        "package_source_gap_report": "harness/context/package-source-gap-report.json",
        "package_data_routing": "harness/context/package-data-routing.json",
        "package_source_snapshots": f"evidence/package-sources/{date_folder}/",
        "execution_evidence": f"reports/daily/{date_folder}/",
        "market_latest_snapshot": "runtime/market-latest.json",
        "daily_refresh_state": "runtime/daily-refresh-state.json",
        "daily_jsonl_integrity": f"runtime/daily-jsonl-integrity-{date_folder}.json",
        "harness_context": "harness/context/latest-data.json",
        "harness_archive_context": f"harness/context/data-archive-{date_folder}.json",
        "harness_archive_latest": "harness/context/latest-archive.json",
        "harness_archive_validations": "harness/context/data-archive-validation-<trade-date>.json",
        "harness_jobs": "harness/jobs/",
        "skill_manifest": "skills/manifest.json",
        "status": "status/current.json",
        "runtime_policy": "harness/context/runtime-policy.json",
        "report_archive": "reports/archive/",
    }
    asset_view = {
        asset_id: {
            "name": spec.get("name", asset_id),
            "declared_path": spec.get("path", paths.get(asset_id, "")),
            "resolved_path": paths.get(asset_id, spec.get("path", "")),
            "status": current_assets.get(asset_id, {}).get("status", "unknown") if isinstance(current_assets.get(asset_id), dict) else "unknown",
            "reason": current_assets.get(asset_id, {}).get("reason", "") if isinstance(current_assets.get(asset_id), dict) else "",
        }
        for asset_id, spec in asset_specs.items()
    }
    # These are runtime contracts rather than one of the 14 catalog's legacy
    # prerequisite IDs, so expose them explicitly without changing skill
    # preflight semantics.
    runtime_asset_specs = {
        "tdx_daily_index": ("通达信日线证券索引", paths["tdx_daily_index"], DATA_ROOT / paths["tdx_daily_index"]),
        "daily_data_index": ("统一日线可用性索引", paths["daily_data_index"], DATA_ROOT / paths["daily_data_index"]),
        "tdx_daily_fallback": ("公开源日线降级层", paths["tdx_daily_fallback"], DATA_ROOT / paths["tdx_daily_fallback"]),
        "supplemental_market": ("统一补充数据快照", paths["supplemental_market"], DATA_ROOT / paths["supplemental_market"]),
        "supplemental_stock": ("个股财务与股本补充快照", paths["supplemental_stock"].replace("<code>.<market>.json", ""), DATA_ROOT / "evidence" / "supplemental" / date_folder),
        "daily_jsonl_integrity": ("日线 JSONL 逐行校验报告", paths["daily_jsonl_integrity"], DATA_ROOT / paths["daily_jsonl_integrity"]),
        "package_source_gap_report": ("压缩包来源缺口清单", paths["package_source_gap_report"], DATA_ROOT / paths["package_source_gap_report"]),
        "package_data_routing": ("压缩包数据路由", paths["package_data_routing"], DATA_ROOT / paths["package_data_routing"]),
        "package_source_snapshots": ("压缩包来源实际快照", paths["package_source_snapshots"], DATA_ROOT / paths["package_source_snapshots"]),
        "harness_archive_context": ("Harness 本地数据归档上下文", paths["harness_archive_context"], DATA_ROOT / paths["harness_archive_context"]),
        "harness_archive_latest": ("Harness 最新归档索引", paths["harness_archive_latest"], DATA_ROOT / paths["harness_archive_latest"]),
        "harness_archive_validations": ("Harness 归档校验回执", paths["harness_archive_validations"], DATA_ROOT / "harness" / "context"),
    }
    for asset_id, (name, declared_path, resolved) in runtime_asset_specs.items():
        asset_view[asset_id] = {
            "name": name, "declared_path": declared_path, "resolved_path": declared_path,
            "status": "available" if resolved.is_file() or resolved.is_dir() else "missing",
            "reason": "" if resolved.is_file() or resolved.is_dir() else "尚未生成该运行时资产",
        }
    runtime_policy_path = DATA_ROOT / "harness" / "context" / "runtime-policy.json"
    report_archive_path = DATA_ROOT / "reports" / "archive"
    asset_view["runtime_policy"] = {
        "name": "3003 自包含运行时政策",
        "declared_path": paths["runtime_policy"],
        "resolved_path": paths["runtime_policy"],
        "status": "available" if runtime_policy_path.is_file() else "missing",
        "reason": "" if runtime_policy_path.is_file() else "桥接器尚未写入运行时政策",
    }
    asset_view["report_archive"] = {
        "name": "本地 Harness 报告归档",
        "declared_path": paths["report_archive"],
        "resolved_path": paths["report_archive"],
        "status": "available" if report_archive_path.is_dir() else "missing",
        "reason": "" if report_archive_path.is_dir() else "尚未生成报告归档目录",
    }
    page = {
        "schema": "ZHANGCAI_LOCAL_DATA_PAGE_V1",
        "generated_at": utc_now(),
        "data_root": str(DATA_ROOT),
        "latest_tdx_trade_date": trade_date,
        "latest_tdx_archive": {
            "status": daily_manifest.get("status", "missing") if isinstance(daily_manifest, dict) else "missing",
            "archive_status": daily_manifest.get("status", "missing") if isinstance(daily_manifest, dict) else "missing",
            "freshness_status": daily_freshness.get("status", "missing"),
            "expected_trade_date": daily_freshness.get("expected_trade_date", ""),
            "requested_trade_date": daily_freshness.get("requested_trade_date", ""),
            "selected_trade_date": daily_freshness.get("selected_trade_date", ""),
            "fallback_trade_date": daily_freshness.get("fallback_trade_date", ""),
            "usable": daily_freshness.get("usable", False),
            "freshness_reason": daily_freshness.get("reason", ""),
            "path": paths["tdx_daily_history"],
            "manifest": paths["tdx_daily_manifest"],
            "bar_records": daily_manifest.get("bar_records", 0) if isinstance(daily_manifest, dict) else 0,
            "archived_symbols": daily_manifest.get("archived_symbols", 0) if isinstance(daily_manifest, dict) else 0,
            "history_days_requested": daily_manifest.get("history_days_requested", 0) if isinstance(daily_manifest, dict) else 0,
            "history_scope": daily_manifest.get("history_scope", "") if isinstance(daily_manifest, dict) else "",
            "sha256": daily_manifest.get("sha256", "") if isinstance(daily_manifest, dict) else "",
            "delta_file": daily_manifest.get("delta_file", "") if isinstance(daily_manifest, dict) else "",
            "delta_records": daily_manifest.get("delta_records", 0) if isinstance(daily_manifest, dict) else 0,
            "archive_mode": daily_manifest.get("archive_mode", "unknown") if isinstance(daily_manifest, dict) else "unknown",
            "incremental_from": daily_manifest.get("incremental_from", "") if isinstance(daily_manifest, dict) else "",
            "incremental_records": daily_manifest.get("incremental_records", 0) if isinstance(daily_manifest, dict) else 0,
            "incremental_trade_dates": daily_manifest.get("incremental_trade_dates", []) if isinstance(daily_manifest, dict) else [],
            "source_file_count": daily_manifest.get("source_file_count", 0) if isinstance(daily_manifest, dict) else 0,
            "symbol_index": paths["tdx_daily_index"],
            "daily_data_index": paths["daily_data_index"],
            "fallback_root": paths["tdx_daily_fallback"],
            "fallback_status": (fallback_date.get("fallback_status") or fallback_date.get("status", "missing")) if isinstance(fallback_date, dict) else "missing",
            "fallback_symbol_count": daily_index.get("summary", {}).get("fallback_symbol_count", 0) if isinstance(daily_index, dict) else 0,
            "fallback_record_count": daily_index.get("summary", {}).get("fallback_record_count", 0) if isinstance(daily_index, dict) else 0,
            "jsonl_integrity_report": paths["daily_jsonl_integrity"],
            "jsonl_integrity_status": "available" if (DATA_ROOT / paths["daily_jsonl_integrity"]).is_file() else "missing",
        },
        "read_order": [
            "先读取本页确认 data_root、latest_tdx_trade_date 与资产状态",
            "再读取 status/current.json 与各资产 manifest/快照，核对 status、source_date、retrieved_at、sha256",
            "历史价格与公式输入按 tdx_local_day → tdx_archive → public_daily_fallback 顺序读取；优先使用 latest_tdx_archive.path，公开降级记录只能按 daily_data_index 索引合并，不能伪装成 TDX 全历史",
            "个股日线索引先读 market/daily/index/tdx-symbol-index.json，再读 market/daily/index/daily-data-index.json；fallback 文件必须核对目标日期、source、source_date、status、source_sha256 和 missing_fields",
            "通达信不可用时允许读取 market/daily/fallback/<trade-date>/<symbol>.jsonl；仅日期完全匹配的公开 OHLCV 可作为 degraded 输入，缺失成交额不得用价格乘成交量估算",
            "需要全文件结构核验时读取 runtime/daily-jsonl-integrity-<trade-date>.json；该报告由流式逐行校验生成，不替代统一清单的 SHA-256 校验",
            "evidence/supplemental/<trade-date>/market.json 与 <code>.<market>.json 提供财务、股本、指数日线、龙虎榜、融资融券的统一补充快照",
            "公式安装包镜像读取 evidence/formulas/package/；现场计算回执读取 evidence/formulas/<trade-date>/",
            "统一来源清单读取 evidence/sources/latest.json；压缩包来源目录读取 harness/context/package-source-inventory.json",
            "公开源、新闻、连板和龙虎榜只能读取 3003 app-data 下已归档的当前来源快照；先核对日期和状态",
            "最后读取 reports/daily/<trade-date>/ 与 harness/jobs/<job-id>.json 作为执行回执",
        ],
        "assets": asset_view,
        "paths": paths,
        "integrated_sources": {},
        "provenance_required": ["source", "source_url_or_local_root", "source_date", "retrieved_at", "status", "error_or_reason", "sha256"],
        "truth_rules": [
            "包内源码/接口说明不等于接口可用；必须以本页和资产现场状态为准",
            "通达信本地日线是历史与公式类技能的主数据；公开源只能作为声明清楚的降级或辅助证据",
            "公开日线降级层只写入应用 data_root，不修改通达信源目录；TDX 断开时可以继续研究已补齐的明确交易日，但必须把 quality=degraded 和缺失字段传给 Harness",
            "不得读取或写入密钥、Cookie，不得修改通达信源目录，不得把推测写入快照",
            "历史兼容目录不属于生产数据源；当前结论只能引用 3003 app-data 下的当前日期资产",
        ],
    }
    write_json(DATA_ROOT / "harness" / "context" / "local-data-page.json", page)
    write_json(DATA_ROOT / "status" / "local-data-page.json", page)
    return page


def parse_day_record(raw: bytes) -> dict[str, Any] | None:
    if len(raw) != 32:
        return None
    date, open_, high, low, close, amount, volume, _reserved = struct.unpack("<IIIIIfII", raw)
    date_text = str(date)
    if len(date_text) != 8 or not date_text.isdigit():
        return None
    return {
        "date": date_text,
        "open": round(open_ / 100, 4),
        "high": round(high / 100, 4),
        "low": round(low / 100, 4),
        "close": round(close / 100, 4),
        "amount": round(float(amount), 4),
        "volume": int(volume),
    }


def latest_day_files() -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    for market in ("sh", "sz", "bj"):
        directory = TDX_ROOT / "vipdoc" / market / "lday"
        if not directory.is_dir():
            continue
        files.extend((market, path) for path in directory.glob("*.day"))
    return files


def rebuild_tdx_symbol_index(files: list[tuple[str, Path]], latest_records: list[tuple[str, Path, dict[str, Any]]]) -> dict[str, Any]:
    """Refresh the fast symbol index from the same .day files being archived."""
    latest_by_path = {(market, path): latest for market, path, latest in latest_records}
    symbols: dict[str, Any] = {}
    for market, path in files:
        latest = latest_by_path.get((market, path))
        try:
            size = path.stat().st_size
            record_count = size // 32
            if not latest or record_count <= 0 or size % 32:
                continue
            with path.open("rb") as stream:
                first = parse_day_record(stream.read(32))
            if not first:
                continue
            symbol = path.stem.lower()
            symbols[symbol] = {
                "symbol": f"{path.stem[-6:]}.{market.upper()}",
                "code": path.stem[-6:],
                "market": market.upper(),
                "file": str(path.relative_to(TDX_ROOT)).replace("\\", "/"),
                "record_count": record_count,
                "first_date": first["date"],
                "last_date": latest["date"],
            }
        except (OSError, ValueError):
            continue
    index = {
        "schema": "ZHANGCAI_TDX_SYMBOL_INDEX_V1",
        "generated_at": utc_now(),
        "source_root": str(TDX_ROOT),
        "source_kind": "Tongdaxin local .day files",
        "symbol_count": len(symbols),
        "symbols": symbols,
    }
    write_json(DATA_ROOT / "market" / "daily" / "index" / "tdx-symbol-index.json", index)
    return index


def rebuild_daily_data_index_from_archive(trade_date: str) -> dict[str, Any]:
    """Make the unified date index agree with the authoritative TDX archive."""
    try:
        # Reuse the recovery layer's index builder so fallback rows, TDX
        # boundaries, and the per-date index remain one compatible schema.
        from daily_data_recovery import load_index, rebuild_index

        index = load_index()
        date_info = index.get("dates", {}).get(trade_date, {}) if isinstance(index.get("dates"), dict) else {}
        rebuild_index(
            index,
            trade_date,
            int(date_info.get("requested_count") or 0),
            int(date_info.get("fetched_count") or 0),
            int(date_info.get("failed_count") or 0),
            True,
        )
        return {
            "status": "available",
            "path": "market/daily/index/daily-data-index.json",
            "date": trade_date,
            "summary": index.get("summary", {}),
        }
    except Exception as error:
        # A TDX archive must not be discarded merely because an optional
        # fallback index repair failed; expose the failure for Harness/UI.
        return {"status": "error", "date": trade_date, "reason": f"{type(error).__name__}: {error}"}


def iter_day_records_after(path: Path, after_date: str | None = None):
    """Yield valid TDX records after ``after_date`` or the whole file.

    TDX .day records are fixed 32-byte rows sorted by date.  A binary search
    finds the first row after the last archived date, so a missed weekend or
    several offline trading days are all recovered without rereading the old
    history into Python objects.
    """
    try:
        with path.open("rb") as source:
            if after_date:
                record_count = source.seek(0, os.SEEK_END) // 32
                low, high = 0, record_count
                while low < high:
                    middle = (low + high) // 2
                    source.seek(middle * 32)
                    raw = source.read(32)
                    if len(raw) != 32:
                        high = middle
                        continue
                    raw_date = str(int.from_bytes(raw[:4], "little"))
                    if raw_date <= after_date:
                        low = middle + 1
                    else:
                        high = middle
                source.seek(low * 32)
            else:
                source.seek(0)
            while raw := source.read(32):
                bar = parse_day_record(raw)
                if bar and (not after_date or bar["date"] > after_date):
                    yield bar
    except OSError:
        return


def read_jsonl_symbol_keys(path: Path) -> set[str]:
    """Read only symbol keys from a legacy JSONL archive.

    This is a one-time compatibility fallback for archives created before the
    canonical-symbol list was written to the manifest.  It keeps only a few
    thousand strings in memory and never materializes historical bars.
    """
    symbols: set[str] = set()
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                try:
                    value = json.loads(line)
                except (TypeError, ValueError):
                    continue
                symbol = str(value.get("symbol") or "").strip().lower() if isinstance(value, dict) else ""
                if symbol:
                    symbols.add(symbol)
    except OSError:
        return set()
    return symbols


def minute_data_status() -> dict[str, Any]:
    """Describe external LC5 availability without copying minute data.

    LC5 is deliberately not an application data asset.  It remains in the
    user-selected TDX directory and is read on demand only by skills that
    declare an optional minute-data dependency.
    """
    files = []
    total_bytes = 0
    for market in ("sh", "sz", "bj"):
        directory = TDX_ROOT / "vipdoc" / market / "fzline"
        if not directory.is_dir():
            continue
        try:
            for path in directory.glob("*.lc5"):
                try:
                    total_bytes += path.stat().st_size
                    files.append(path)
                except OSError:
                    continue
        except OSError:
            continue
    return {
        "asset": "tdx_lc5_external",
        "status": "available" if files else "missing",
        "mode": "external_on_demand",
        "packaged": False,
        "source_root": str(TDX_ROOT),
        "file_count": len(files),
        "bytes": total_bytes,
        "reason": "不写入 EXE；仅对声明需要分钟数据的技能按股票按需读取。" if files else "未发现外部 .lc5；普通日线任务不受影响，需要分钟特征的技能标记 DEGRADED。",
    }


def archive_daily(history_days: int) -> dict[str, Any]:
    files = latest_day_files()
    if not files:
        status = {
            "status": "missing",
            "asset": "tdx_daily_history",
            "checked_at": utc_now(),
            "source_root": str(TDX_ROOT),
            "reason": "未找到 vipdoc/{sh,sz,bj}/lday 日线目录。",
        }
        write_json(DATA_ROOT / "status" / "tdx-daily-history.json", status)
        update_status()
        return status

    # First pass reads only the final 32-byte record of every .day file.  Do
    # not materialize 5,000 × 420 Python dictionaries: that exceeded 1 GB in
    # a realistic local dataset and is unsuitable for the packaged app.
    latest_records: list[tuple[str, Path, dict[str, Any]]] = []
    dates: Counter[str] = Counter()
    for market, path in files:
        try:
            with path.open("rb") as stream:
                stream.seek(0, os.SEEK_END)
                if stream.tell() < 32:
                    continue
                stream.seek(-32, os.SEEK_END)
                latest = parse_day_record(stream.read(32))
            if not latest:
                continue
            dates[latest["date"]] += 1
            latest_records.append((market, path, latest))
        except OSError:
            continue

    if not latest_records:
        raise RuntimeError("可读取的通达信日线文件为空")
    trade_date, current_count = dates.most_common(1)[0]
    # Keep the fast lookup index in lockstep with the exact source files used
    # by this archive run.  The old index could remain at an earlier date even
    # after .day files had advanced, which made the fallback layer misleading.
    previous_symbol_index = read_json(DATA_ROOT / "market" / "daily" / "index" / "tdx-symbol-index.json", {})
    symbol_index = rebuild_tdx_symbol_index(files, latest_records)
    daily_root = DATA_ROOT / "market" / "daily" / trade_date
    daily_root.mkdir(parents=True, exist_ok=True)
    aggregate_file = DATA_ROOT / "market" / "daily" / "aggregate" / "tdx-bars.jsonl"
    previous_manifest = read_json(DATA_ROOT / "status" / "tdx-daily-history.json", {})
    previous_date = str(previous_manifest.get("trade_date") or "").replace("-", "") if isinstance(previous_manifest, dict) else ""
    previous_file_rel = str(previous_manifest.get("file") or "") if isinstance(previous_manifest, dict) else ""
    previous_bars_file = DATA_ROOT / previous_file_rel if previous_file_rel else None
    canonical_rel = str(aggregate_file.relative_to(DATA_ROOT)).replace("\\", "/")
    previous_canonical_file = (
        aggregate_file
        if previous_file_rel == canonical_rel and aggregate_file.is_file()
        else previous_bars_file
    )
    previous_bar_records = int(previous_manifest.get("bar_records") or 0) if isinstance(previous_manifest, dict) else 0
    previous_current_count = int(previous_manifest.get("current_trade_date_symbols") or 0) if isinstance(previous_manifest, dict) else 0
    previous_source_record_count = int(previous_manifest.get("source_record_count") or 0) if isinstance(previous_manifest, dict) else 0
    full_history_requested = history_days <= 0
    previous_history_days = int(previous_manifest.get("history_days_requested") or 0) if isinstance(previous_manifest, dict) else 0
    previous_archived_symbols = int(previous_manifest.get("archived_symbols") or 0) if isinstance(previous_manifest, dict) else 0
    previous_archived_symbol_keys = {
        str(value).strip().lower()
        for value in (previous_manifest.get("archived_symbol_keys") or [])
        if str(value).strip()
    } if isinstance(previous_manifest, dict) else set()
    if not previous_archived_symbol_keys and isinstance(previous_symbol_index, dict):
        previous_archived_symbol_keys = {
            str(value).strip().lower()
            for value in (previous_symbol_index.get("symbols") or {}).keys()
            if str(value).strip()
        }
    if not previous_archived_symbol_keys and previous_canonical_file and previous_canonical_file.is_file():
        previous_archived_symbol_keys = read_jsonl_symbol_keys(previous_canonical_file)
    current_symbol_keys = {
        str(value).strip().lower()
        for value in (symbol_index.get("symbols") or {}).keys()
        if str(value).strip()
    }
    new_symbol_keys = sorted(current_symbol_keys - previous_archived_symbol_keys)
    previous_source_symbols = previous_symbol_index.get("symbols", {}) if isinstance(previous_symbol_index, dict) else {}
    current_source_symbols = symbol_index.get("symbols", {}) if isinstance(symbol_index, dict) else {}
    history_reconcile_reasons: list[str] = []
    if previous_source_symbols and current_source_symbols:
        removed_symbols = sorted(set(previous_source_symbols) - set(current_source_symbols))
        if removed_symbols:
            history_reconcile_reasons.append(f"source_symbols_removed:{len(removed_symbols)}")
        for symbol in set(previous_source_symbols).intersection(current_source_symbols):
            before = previous_source_symbols.get(symbol) or {}
            after = current_source_symbols.get(symbol) or {}
            if int(after.get("record_count") or 0) < int(before.get("record_count") or 0):
                history_reconcile_reasons.append(f"source_record_count_decreased:{symbol}")
                break
            if str(after.get("first_date") or "") != str(before.get("first_date") or ""):
                history_reconcile_reasons.append(f"source_first_date_changed:{symbol}")
                break
    if full_history_requested and previous_history_days > 0:
        history_reconcile_reasons.append("history_window_expansion")
    history_reconcile_required = bool(history_reconcile_reasons)
    archive_mode = "full_rebuild_all_history" if full_history_requested else "full_rebuild"
    incremental_from = ""
    incremental_records = 0
    incremental_dates: set[str] = set()
    delta_file: Path | None = None
    incremental_base_file = ""
    written = 0
    covered_symbols = 0
    source_record_count = sum(int(item.get("record_count") or 0) for item in symbol_index.get("symbols", {}).values())
    source_changed = bool(previous_source_record_count and previous_source_record_count != source_record_count)

    # 首次归档默认读取每个 .day 文件的全部可用历史（可用 --history-days
    # 显式限制窗口）；之后只读取新增日期，新增证券只补自己的历史。
    # canonical aggregate 是唯一的主库，交易日目录只保存 manifest 和 delta，
    # 不再每天复制完整 tdx-bars.jsonl。
    can_increment = (
        isinstance(previous_manifest, dict)
        and previous_manifest.get("schema") == "ZHANGCAI_TDX_DAILY_ARCHIVE_V1"
        and previous_canonical_file is not None
        and previous_canonical_file.is_file()
        and previous_date
        and trade_date >= previous_date
        and not history_reconcile_required
    )
    if can_increment and (trade_date > previous_date or new_symbol_keys):
        aggregate_file.parent.mkdir(parents=True, exist_ok=True)
        if not aggregate_file.is_file():
            shutil.copyfile(previous_canonical_file, aggregate_file)
            incremental_base_file = previous_file_rel
        bars_file = aggregate_file
        delta_file = daily_root / "tdx-bars.jsonl"
        with bars_file.open("a", encoding="utf-8", newline="\n") as stream, delta_file.open("w", encoding="utf-8", newline="\n") as delta_stream:
            for market, path, latest in latest_records:
                symbol = path.stem.lower()
                if trade_date == previous_date and symbol not in new_symbol_keys:
                    continue
                after_date = None if symbol in new_symbol_keys else previous_date
                for bar in iter_day_records_after(path, after_date):
                    line = json.dumps({"symbol": symbol, "market": market, **bar}, ensure_ascii=False) + "\n"
                    stream.write(line)
                    delta_stream.write(line)
                    incremental_records += 1
                    incremental_dates.add(bar["date"])
        written = previous_bar_records + incremental_records
        covered_symbols = max(int(previous_manifest.get("archived_symbols") or 0), current_count)
        archive_mode = "incremental_append_new_symbols" if new_symbol_keys else "incremental_append"
        incremental_from = previous_date
    elif can_increment and trade_date == previous_date and previous_current_count == current_count and not source_changed and previous_canonical_file is not None and previous_canonical_file.is_file():
        # 同一交易日重复触发时保持原文件与哈希不变，避免无意义的全量重写。
        if not aggregate_file.is_file():
            aggregate_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(previous_canonical_file, aggregate_file)
            incremental_base_file = previous_file_rel
        bars_file = aggregate_file
        written = previous_bar_records
        covered_symbols = int(previous_manifest.get("archived_symbols") or current_count)
        archive_mode = "migrated_to_canonical" if incremental_base_file else "unchanged"
    else:
        # Reconcile into a sibling temporary file and atomically replace the
        # canonical store.  A failed rebuild therefore cannot truncate the
        # last known-good archive.
        aggregate_file.parent.mkdir(parents=True, exist_ok=True)
        rebuild_file = aggregate_file.with_name(f"{aggregate_file.name}.{uuid.uuid4().hex}.tmp")
        with rebuild_file.open("w", encoding="utf-8", newline="\n") as stream:
            for market, path, latest in latest_records:
                if not full_history_requested and latest["date"] != trade_date:
                    continue
                covered_symbols += 1
                symbol = path.stem.lower()
                try:
                    with path.open("rb") as source:
                        source.seek(0, os.SEEK_END)
                        size = source.tell()
                        offset = 0 if full_history_requested else max(0, size - history_days * 32)
                        offset -= offset % 32
                        source.seek(offset)
                        while raw := source.read(32):
                            bar = parse_day_record(raw)
                            if bar:
                                stream.write(json.dumps({"symbol": symbol, "market": market, **bar}, ensure_ascii=False) + "\n")
                                written += 1
                except OSError:
                    continue
        os.replace(rebuild_file, aggregate_file)
        bars_file = aggregate_file
    security_root = DATA_ROOT / "market" / "security-master"
    security_root.mkdir(parents=True, exist_ok=True)
    security_file = security_root / f"{trade_date}.jsonl"
    tdx_identity = tdx_security_metadata()
    identity = dict(tdx_identity)
    for key, row in baseline_security_metadata().items():
        merged = {**tdx_identity.get(key, {}), **row}
        if not str(row.get("name") or "").strip() and tdx_identity.get(key, {}).get("name"):
            merged["name"] = tdx_identity[key]["name"]
            merged["identity_source"] = tdx_identity[key]["identity_source"]
        identity[key] = merged
    named = 0
    with security_file.open("w", encoding="utf-8", newline="\n") as stream:
        for market, path, latest in latest_records:
            if latest["date"] == trade_date:
                symbol = path.stem.lower()
                code = symbol[-6:]
                known = identity.get((code, market), {})
                name = str(known.get("name") or "").strip()
                if name:
                    named += 1
                upper_name = name.upper()
                stream.write(json.dumps({
                    "symbol": symbol,
                    "code": code,
                    "market": market,
                    "name": name,
                    "instrument_type": "a_share_candidate",
                    "is_st": upper_name.startswith("ST") or upper_name.startswith("*ST"),
                    "listing_status": "active" if name else "unknown",
                    "limit_pct": known.get("limitPct"),
                    "industry_code": known.get("industryCode"),
                    "industry_name": known.get("industryName"),
                    "sector_code": known.get("sectorCode"),
                    "sector_name": known.get("sectorName"),
                    "identity_source": "lib/market.json" if name else "TDX day-file stem",
                    "source_snapshot_date": known.get("date", "") if known else "",
                    "as_of": trade_date,
                }, ensure_ascii=False) + "\n")
    expected_date = expected_market_trade_date(previous_manifest if isinstance(previous_manifest, dict) else {}) or trade_date
    freshness_status = "available" if expected_date == trade_date else "stale"
    freshness_reason = "" if freshness_status == "available" else f"最新本地行情为 {expected_date}，本次归档只发现 {trade_date}；等待源文件更新后重试。"
    manifest = {
        "schema": "ZHANGCAI_TDX_DAILY_ARCHIVE_V1",
        "status": "available" if current_count >= 3000 else "degraded",
        "asset": "tdx_daily_history",
        "trade_date": trade_date,
        "archived_at": utc_now(),
        "source_root": str(TDX_ROOT),
        "history_days_requested": 0 if full_history_requested else history_days,
        "history_scope": "all_available_source_history" if full_history_requested else f"latest_{history_days}_records_per_symbol",
        "current_trade_date_symbols": current_count,
        "archived_symbols": covered_symbols,
        "security_master_records": current_count,
        "security_master_named_records": named,
        "bar_records": written,
        "file": canonical_rel,
        "sha256": str(previous_manifest.get("sha256") or "") if archive_mode == "unchanged" else sha256_file(bars_file),
        "archive_mode": archive_mode,
        "incremental_from": incremental_from,
        "incremental_records": incremental_records,
        "incremental_trade_dates": sorted(incremental_dates),
        "incremental_base_file": incremental_base_file,
        "delta_file": str(delta_file.relative_to(DATA_ROOT)).replace("\\", "/") if delta_file else "",
        "delta_records": incremental_records,
        "source_file_count": len(files),
        "latest_date_source_files": current_count,
        "source_record_count": source_record_count,
        "source_changed_since_previous": source_changed,
        "source_change_mode": "history_reconcile" if history_reconcile_required else "append_only",
        "history_reconcile_required": history_reconcile_required,
        "history_reconcile_reasons": history_reconcile_reasons,
        "new_symbol_keys": new_symbol_keys,
        "archived_symbol_keys": sorted(current_symbol_keys),
        "symbol_index": "market/daily/index/tdx-symbol-index.json",
        "symbol_index_count": symbol_index.get("symbol_count", 0),
        "expected_trade_date": expected_date,
        "freshness_status": freshness_status,
        "freshness_reason": freshness_reason,
        "storage_rule": "首次读取本地 .day 全部可用历史（或显式指定窗口）写入唯一 canonical aggregate；后续只追加新增日期，新增证券只补该证券历史，交易日目录只保存 manifest/delta；原始全量快照不再生成。",
        "reason": "" if current_count >= 3000 else "同日股票覆盖不足 3000，只能作为降级数据集。",
    }
    write_json(DATA_ROOT / "status" / "tdx-daily-history.json", manifest)
    # Write the day manifest before rebuilding the unified index.  The index
    # builder reads both manifests and then updates the date-local index.
    day_manifest_path = daily_root / "manifest.json"
    write_json(day_manifest_path, manifest)
    daily_index_sync = rebuild_daily_data_index_from_archive(trade_date)
    manifest["daily_data_index_sync"] = daily_index_sync
    merged_day_manifest = read_json(day_manifest_path, {})
    if isinstance(merged_day_manifest, dict):
        merged_day_manifest["daily_data_index_sync"] = daily_index_sync
        write_json(day_manifest_path, merged_day_manifest)
    current_status = update_status()
    report = write_daily_archive_report(manifest, current_status.get("assets", {}))
    manifest["daily_report"] = report
    merged_day_manifest = read_json(day_manifest_path, {})
    if isinstance(merged_day_manifest, dict):
        merged_day_manifest["daily_report"] = report
        write_json(day_manifest_path, merged_day_manifest)
    # The final status/local-data page must be generated after the day
    # manifest and index are both durable, otherwise Harness can read a
    # one-run-old date while the archive itself is already current.
    update_status()
    return manifest


def write_daily_archive_report(manifest: dict[str, Any], assets: dict[str, Any] | None = None) -> str:
    """Create a human-readable daily data report beside the structured proof."""
    trade_date = str(manifest.get("trade_date") or datetime.now().strftime("%Y%m%d"))
    report_root = DATA_ROOT / "reports" / "daily" / trade_date
    report_id = "daily-data-archive"
    asset_summary = {
        asset_id: {
            "status": value.get("status"),
            "reason": value.get("reason", ""),
            "file": value.get("file", value.get("path", "")),
            "file_count": value.get("file_count"),
        }
        for asset_id, value in (assets or {}).items()
        if isinstance(value, dict)
    }
    value = {
        "schema": "ZHANGCAI_DAILY_DATA_ARCHIVE_REPORT_V1",
        "report_id": report_id,
        "status": manifest.get("status", "unknown"),
        "trade_date": trade_date,
        "created_at": utc_now(),
        "data_root": str(DATA_ROOT),
        "daily_archive": manifest,
        "assets": asset_summary,
        "note": "这是本地数据归档日报，不包含投资结论；后续技能预检和执行报告会引用该快照哈希。",
    }
    json_path = report_root / f"{report_id}.json"
    markdown_path = report_root / f"{report_id}.md"
    write_json(json_path, value)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join([
        f"# {trade_date} · 本地数据归档日报",
        "",
        f"- 状态：`{value['status']}`",
        f"- 同日股票覆盖：{manifest.get('current_trade_date_symbols', 0)}",
        f"- 已归档证券：{manifest.get('archived_symbols', 0)}",
        f"- 日线记录：{manifest.get('bar_records', 0)}",
        f"- 历史范围：`{manifest.get('history_scope', 'unknown')}`",
        f"- 归档模式：`{manifest.get('archive_mode', 'unknown')}` · 本次新增：{manifest.get('incremental_records', 0)} 条" + (f" · 从 {manifest.get('incremental_from')} 追加" if manifest.get('incremental_from') else "") + (f" · 覆盖 {len(manifest.get('incremental_trade_dates', []))} 个新增交易日" if manifest.get('incremental_trade_dates') else ""),
        f"- TDX 源文件：{manifest.get('source_file_count', 0)} 个 · 最新日覆盖：{manifest.get('latest_date_source_files', 0)} 个",
        f"- 归档文件：`{manifest.get('file', '')}`",
        f"- SHA-256：`{manifest.get('sha256', '')}`",
        "",
        "## 数据资产门禁",
        *[
            f"- {asset_id}：`{item.get('status', 'missing')}`" + (f" · {item['reason']}" if item.get("reason") else "")
            for asset_id, item in asset_summary.items()
        ],
        "",
        value["note"],
    ]) + "\n", encoding="utf-8")
    return str(json_path.relative_to(DATA_ROOT)).replace("\\", "/")


def _formula_package_state() -> dict[str, Any]:
    """Validate the portable formula mirror without touching the TDX source."""
    archive_root = DATA_ROOT / "evidence" / "formulas" / "package"
    manifest_path = archive_root / "manifest.json"
    manifest = read_json(manifest_path, {})
    required = manifest.get("required_files") if isinstance(manifest, dict) else None
    required_files = [str(item).replace("\\", "/") for item in required] if isinstance(required, list) else list(FORMULA_SOURCE_RELATIVE_PATHS)
    missing = [relative for relative in required_files if not (archive_root / relative).is_file()]
    copied = [relative for relative in required_files if (archive_root / relative).is_file()]
    return {
        "status": "available" if required_files and not missing else ("degraded" if copied else "missing"),
        "schema": manifest.get("schema", "") if isinstance(manifest, dict) else "",
        "path": str(archive_root.relative_to(DATA_ROOT)).replace("\\", "/"),
        "manifest_path": str(manifest_path.relative_to(DATA_ROOT)).replace("\\", "/"),
        "required_files": required_files,
        "copied_files": copied,
        "missing_files": missing,
        "source_root": manifest.get("source_root", "") if isinstance(manifest, dict) else "",
        "archived_at": manifest.get("archived_at", "") if isinstance(manifest, dict) else "",
    }


def formula_status() -> dict[str, Any]:
    registry = TDX_ROOT / "T0002" / "PriLoc.dat"
    formula_dir = TDX_ROOT / "T0002" / "gs_bak"
    files = [path.name for path in formula_dir.glob("*.tn6")] if formula_dir.is_dir() else []
    live_tdx = tdx_root_available()
    detected = live_tdx and registry.is_file() and bool(files)
    source_archive = archive_formula_sources()
    package_state = _formula_package_state()
    receipt_root = DATA_ROOT / "evidence" / "formulas"
    receipt_files = sorted(receipt_root.rglob("*.json")) if receipt_root.is_dir() else []
    valid_receipts: list[tuple[Path, dict[str, Any]]] = []
    for receipt_path in receipt_files:
        value = read_json(receipt_path, {})
        if not isinstance(value, dict) or value.get("schema") != "ZHANGCAI_TDX_TQ_FORMULA_RECEIPT_V1":
            continue
        formulas = value.get("formulas")
        failed = value.get("failed_formulas")
        if not isinstance(formulas, list) or len(formulas) < 5 or not isinstance(failed, list) or failed:
            continue
        if not all(isinstance(item, dict) and item.get("ok") is True for item in formulas):
            continue
        valid_receipts.append((receipt_path, value))
    valid_receipts.sort(key=lambda item: str(item[1].get("executed_at") or ""))
    latest_receipt = valid_receipts[-1] if valid_receipts else None
    if latest_receipt and source_archive.get("status") == "available":
        status = "available"
        reason = ""
    elif latest_receipt:
        status = "degraded"
        reason = "已有五公式现场回执，但公式安装包镜像仍有缺项，暂不标记为可移植完成。"
    elif detected:
        status = "degraded"
        reason = "已发现公式文件与注册表，但尚无包含五公式完整成功结果的 TQ Worker 现场回执。"
    elif source_archive.get("status") == "available":
        status = "degraded"
        reason = "数据包已包含完整公式镜像，但当前通达信目录未提供可核对的现场 TQ 回执；连接通达信并执行一次五公式校验后才可升级。"
    else:
        status = "missing"
        reason = "未发现可核对的 TQ 私有公式注册表或 .tn6 公式文件。"
    return {
        "status": status,
        "asset": "tdx_tq_formula",
        "checked_at": utc_now(),
        "source_root": str(TDX_ROOT) if live_tdx else "",
        "registry": str(registry) if live_tdx else "",
        "formula_files": files,
        "tdx_detected": detected,
        "portable_package": package_state,
        "receipt_root": str(receipt_root),
        "receipt_count": len(receipt_files),
        "valid_receipt_count": len(valid_receipts),
        "latest_receipt": str(latest_receipt[0].relative_to(DATA_ROOT)).replace("\\", "/") if latest_receipt else "",
        "latest_receipt_executed_at": latest_receipt[1].get("executed_at", "") if latest_receipt else "",
        "source_archive": source_archive,
        "required_formulas": ["大牛线4.0", "飞龙在天", "游资资金监控", "机构资金监控", "庄家资金监控"],
        "reason": reason,
    }


def package_status() -> dict[str, Any]:
    manifest = read_json(DATA_ROOT / "skills" / "manifest.json", {})
    installed = manifest.get("skills", []) if isinstance(manifest, dict) else []
    return {
        "status": "available" if len(installed) == 14 else "missing",
        "asset": "skill_packages",
        "checked_at": utc_now(),
        "installed_count": len(installed),
        "reason": "" if len(installed) == 14 else "14 个技能包尚未全部部署到应用数据目录。",
    }


def public_asset_state(asset_id: str, path: Path, label: str) -> dict[str, Any]:
    files = [file for file in path.rglob("*") if file.is_file()] if path.is_dir() else []
    return {
        "status": "available" if files else "missing",
        "asset": asset_id,
        "checked_at": utc_now(),
        "path": str(path.relative_to(DATA_ROOT)).replace("\\", "/"),
        "file_count": len(files),
        "reason": "" if files else f"尚未归档{label}。",
    }


def file_asset_state(asset_id: str, path: Path, label: str) -> dict[str, Any]:
    exists = path.is_file()
    return {
        "status": "available" if exists else "missing",
        "asset": asset_id,
        "checked_at": utc_now(),
        "path": str(path.relative_to(DATA_ROOT)).replace("\\", "/"),
        "file_count": 1 if exists else 0,
        "reason": "" if exists else f"尚未生成{label}。",
    }


def _compact_date(value: Any) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits[:8] if len(digits) >= 8 else ""


def _target_public_research_date() -> str:
    daily = read_json(DATA_ROOT / "status" / "tdx-daily-history.json", {})
    public = read_json(DATA_ROOT / "public" / "latest.json", {})
    raw = (daily or {}).get("trade_date") or (public or {}).get("date") or ""
    compact = _compact_date(raw)
    return f"{compact[:4]}-{compact[4:6]}-{compact[6:]}" if len(compact) == 8 else ""


def _news_record_time(record: Any) -> str:
    if not isinstance(record, dict):
        return ""
    for key in ("source_timestamp", "publishedAt", "published_at", "publish_time", "time", "date"):
        value = str(record.get(key) or "").strip().replace("/", "-")
        if value:
            match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", value)
            if match:
                parts = match.group(1).split("-")
                return f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
    return ""


def _news_snapshot_stats(value: Any, target_date: str) -> dict[str, Any]:
    """Read only 3003-local news snapshots without date spoofing."""
    if not isinstance(value, dict):
        return {"claimed_date": "", "same_day": 0, "provider_counts": {}, "record_count": 0}
    wrapper = value
    snapshot = value.get("snapshot") if isinstance(value.get("snapshot"), dict) else value
    claimed_raw = (
        wrapper.get("source_date") or wrapper.get("requested_date") or wrapper.get("date")
        or snapshot.get("source_date") or snapshot.get("requested_date") or snapshot.get("date")
    )
    claimed = str(claimed_raw or "").replace("/", "-")[:10]
    rows: list[dict[str, Any]] = []
    provider_default = ""
    providers = snapshot.get("providers")
    if isinstance(providers, dict):
        for provider, provider_value in providers.items():
            if not isinstance(provider_value, dict):
                continue
            provider_default = str(provider)
            provider_rows = provider_value.get("records") if isinstance(provider_value.get("records"), list) else []
            rows.extend({**row, "_provider": str(provider)} for row in provider_rows if isinstance(row, dict))
    top_rows = snapshot.get("records")
    if isinstance(top_rows, list) and top_rows:
        rows = [row for row in top_rows if isinstance(row, dict)]
        provider_default = ""
    source = snapshot.get("source")
    source_rows = source.get("records") if isinstance(source, dict) and isinstance(source.get("records"), list) else []
    if not rows and source_rows:
        provider_default = str(source.get("provider") or source.get("source") or "eastmoney")
        rows = [{**row, "_provider": provider_default} for row in source_rows if isinstance(row, dict)]
    same_day = [row for row in rows if _news_record_time(row) == target_date]
    provider_counts: Counter[str] = Counter()
    for row in same_day:
        provider = str(row.get("_provider") or row.get("provider") or provider_default or "unknown")
        provider_counts[provider] += 1
    return {
        "claimed_date": claimed,
        "same_day": len(same_day),
        "provider_counts": dict(sorted(provider_counts.items())),
        "record_count": len(rows),
    }


def _public_research_candidates(target_date: str) -> list[Path]:
    compact = _compact_date(target_date)
    candidates: list[Path] = []
    roots = [DATA_ROOT / "evidence" / "public", DATA_ROOT / "news"]
    for root in roots:
        if root.is_dir():
            candidates.extend(sorted(root.glob("*.json")))
            if compact:
                candidates.extend(sorted((root / compact).glob("*.json")))
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path.resolve())
        if path.is_file() and key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def _relative_data_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(DATA_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def select_public_research_snapshot(trade_date: str, current_snapshot: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """Choose the best same-day snapshot, preferring real dated evidence over rolling news."""
    target = str(trade_date or "").replace("/", "-")[:10]
    choices: list[tuple[int, int, str, Path, dict[str, Any], dict[str, Any]]] = []
    for path in _public_research_candidates(target):
        value = read_json(path, {})
        stats = _news_snapshot_stats(value, target)
        choices.append((int(stats["same_day"]), len(stats["provider_counts"]), str(path), path, value, stats))
    if current_snapshot:
        stats = _news_snapshot_stats(current_snapshot, target)
        choices.append((int(stats["same_day"]), len(stats["provider_counts"]), "", DATA_ROOT / "news" / "latest.json", current_snapshot, stats))
    valid = [item for item in choices if item[0] > 0]
    if valid:
        _, _, _, path, value, stats = max(valid, key=lambda item: (item[0], item[1], item[2]))
        return value, _relative_data_path(path), stats
    stats = _news_snapshot_stats(current_snapshot, target)
    return current_snapshot, _relative_data_path(DATA_ROOT / "news" / "latest.json"), stats


def public_research_status() -> dict[str, Any]:
    """Require actual same-day records, including traceable historical fallback evidence."""
    root = DATA_ROOT / "evidence" / "public"
    files = [file for file in root.glob("*.json")] if root.is_dir() else []
    target_date = _target_public_research_date()
    choices: list[tuple[int, int, str, Path, dict[str, Any]]] = []
    for path in _public_research_candidates(target_date):
        value = read_json(path, {})
        stats = _news_snapshot_stats(value, target_date)
        choices.append((int(stats["same_day"]), len(stats["provider_counts"]), str(path), path, stats))
    best = max(choices, key=lambda item: (item[0], item[1], item[2])) if choices else None
    same_day_records = int(best[0]) if best else 0
    selected_path = _relative_data_path(best[3]) if best else ""
    multi_source_records = best[4]["provider_counts"] if best else {}
    providers_succeeded = sorted(multi_source_records)
    dated_files = sum(1 for item in choices if item[4].get("claimed_date") == target_date and item[0] > 0)
    historical_fallback = False
    news_snapshot_count = len(choices)
    best_value = read_json(best[3], {}) if best else {}
    fallback_kind = str(best_value.get("fallback_kind") or "") if isinstance(best_value, dict) else ""
    if same_day_records > 0 and not fallback_kind:
        status = "available"
        reason = ""
    elif same_day_records > 0 and fallback_kind:
        status = "degraded"
        reason = "仅有公开市场快照降级证据；它可供研究上下文引用，但不等同于同日新闻、公告或舆情原文。"
    elif files or choices:
        status = "degraded"
        reason = "已保存公开资讯响应，但目标交易日可用同日记录为 0 条，不能把空快照当作研究证据。"
    else:
        status = "missing"
        reason = "尚未归档公开资讯与公告证据。"
    return {
        "status": status,
        "asset": "public_research",
        "checked_at": utc_now(),
        "path": "evidence/public/",
        "target_date": target_date,
        "file_count": len(files),
        "candidate_count": news_snapshot_count,
        "same_date_file_count": dated_files,
        "same_day_record_count": same_day_records,
        "multi_source_records": dict(sorted(multi_source_records.items())),
        "providers_succeeded": providers_succeeded,
        "news_snapshot_count": news_snapshot_count,
        "selected_snapshot": selected_path,
        "historical_fallback": historical_fallback,
        "fallback_kind": fallback_kind,
        "reason": reason,
    }


def build_public_research_fallback(public_snapshot: dict[str, Any], trade_date: str) -> dict[str, Any]:
    """Build an explicit market-evidence fallback; never present it as news."""
    if not isinstance(public_snapshot, dict):
        return {}
    sources = public_snapshot.get("sources") if isinstance(public_snapshot.get("sources"), dict) else {}
    fetched_at = str(public_snapshot.get("fetchedAt") or public_snapshot.get("fetched_at") or utc_now())
    records: list[dict[str, Any]] = []
    for provider, value in sources.items():
        if not isinstance(value, dict) or value.get("status") not in {"available", "partial"}:
            continue
        data = value.get("data") if isinstance(value.get("data"), dict) else {}
        rows = data.get("records") if isinstance(data.get("records"), list) else data.get("pool")
        if not isinstance(rows, list):
            rows = data.get("diff") if isinstance(data.get("diff"), list) else []
        kpi = data.get("kpi") if isinstance(data.get("kpi"), dict) else {}
        count = len(rows)
        if not count and not kpi:
            continue
        summary = {
            "provider": provider,
            "status": value.get("status"),
            "record_count": count,
            "kpi": kpi,
            "source_url": value.get("url") or value.get("source_url") or "",
        }
        records.append({
            "provider": "public_market",
            "source": provider,
            "title": f"Public market evidence fallback: {provider}",
            "content": json.dumps(summary, ensure_ascii=False, separators=(",", ":")),
            "source_timestamp": fetched_at,
            "source_date": trade_date,
            "kind": "market_snapshot",
            "degraded": True,
            "fallback_reason": "public_research source is unavailable; derived from the local public market snapshot only",
            "record_count": count,
            "source_url": summary["source_url"],
        })
    if not records:
        return {}
    return {
        "schema": "ZHANGCAI_PUBLIC_RESEARCH_FALLBACK_V1",
        "status": "degraded",
        "fallback_kind": "public_market_snapshot",
        "archived_at": utc_now(),
        "source_date": trade_date,
        "same_day_record_count": len(records),
        "provider_counts": {"public_market": len(records)},
        "historical_fallback": False,
        "data_boundary": "Market-only public evidence. No news, announcement, sentiment or same-day article is inferred.",
        "records": records,
        "snapshot": {
            "schema": "ZHANGCAI_PUBLIC_RESEARCH_FALLBACK_SNAPSHOT_V1",
            "date": trade_date,
            "source_date": trade_date,
            "fetchedAt": fetched_at,
            "records": records,
        },
    }


def stage_public_snapshots() -> dict[str, Any]:
    """Persist selected raw public snapshots into stable, EXE-friendly folders."""
    public_snapshot = read_json(DATA_ROOT / "public" / "latest.json", {})
    news_snapshot = read_json(DATA_ROOT / "news" / "latest.json", {})
    trade_date = str(public_snapshot.get("date") or news_snapshot.get("date") or datetime.now().strftime("%Y-%m-%d"))
    news_snapshot, news_source_path, news_stats = select_public_research_snapshot(trade_date, news_snapshot)
    sources = public_snapshot.get("sources") if isinstance(public_snapshot, dict) else {}
    sources = sources if isinstance(sources, dict) else {}
    staged: dict[str, Any] = {}
    groups = {
        "limit_up_pool": ["eastmoneyLimitUp", "akshareLimitUpPool", "lianban"],
        "lhb_data": ["eastmoneyLhb", "akshareLhb", "akshareLhbStockStatistic"],
    }
    for asset, names in groups.items():
        selected = {name: sources[name] for name in names if name in sources}
        target = DATA_ROOT / "public" / ("limit-up" if asset == "limit_up_pool" else "lhb") / f"{trade_date}.json"
        if selected:
            write_json(target, {"schema": "ZHANGCAI_PUBLIC_SOURCE_ARCHIVE_V1", "asset": asset, "archived_at": utc_now(), "source_date": trade_date, "sources": selected})
            staged[asset] = target
    if isinstance(news_snapshot, dict) and news_snapshot:
        target = DATA_ROOT / "evidence" / "public" / f"news-{trade_date}.json"
        staged_value = {
            "schema": "ZHANGCAI_PUBLIC_NEWS_ARCHIVE_V1",
            "archived_at": utc_now(),
            "source_date": trade_date,
            "source_path": news_source_path,
            "same_day_record_count": news_stats.get("same_day", 0),
            "provider_counts": news_stats.get("provider_counts", {}),
            "historical_fallback": False,
            "snapshot": news_snapshot,
        }
        write_json(target, staged_value)
        # Stable alias consumed by both the web page and Harness. Keep the
        # dated evidence file as the audit record and make the alias point to
        # the same snapshot in the unified resource library.
        write_json(DATA_ROOT / "evidence" / "public" / "latest.json", staged_value)
        staged["public_research"] = target
    fallback = build_public_research_fallback(public_snapshot, trade_date)
    if fallback:
        fallback_target = DATA_ROOT / "evidence" / "public" / "fallback-latest.json"
        write_json(fallback_target, fallback)
        current_path = DATA_ROOT / "evidence" / "public" / "latest.json"
        current = read_json(current_path, {})
        current_stats = _news_snapshot_stats(current, trade_date)
        current_is_real = isinstance(current, dict) and bool(current) and not current.get("fallback_kind") and current_stats.get("same_day", 0) > 0
        if not current_is_real:
            write_json(current_path, fallback)
            staged["public_research"] = fallback_target
        staged["public_research_fallback"] = fallback_target
    return staged


def security_master_status() -> dict[str, Any]:
    root = DATA_ROOT / "market" / "security-master"
    files = [file for file in root.glob("*.jsonl")] if root.is_dir() else []
    total = 0
    named = 0
    for file in files:
        try:
            with file.open("r", encoding="utf-8") as stream:
                for line in stream:
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    if not isinstance(row, dict):
                        continue
                    total += 1
                    if str(row.get("name") or "").strip():
                        named += 1
        except OSError:
            continue
    complete = total > 0 and named == total
    return {
        "status": "available" if complete else ("degraded" if files else "missing"),
        "asset": "security_master",
        "checked_at": utc_now(),
        "path": "market/security-master/",
        "file_count": len(files),
        "record_count": total,
        "named_record_count": named,
        "reason": "" if complete else ("已归档代码、市场、名称（可从应用基线匹配部分）、ST标记和属性字段；仍有未命名 TDX 标的，保持降级。" if files else "尚未归档证券基础资料。"),
    }


def archive_formula_sources() -> dict[str, Any]:
    """Mirror the safe TQ formula inputs into the writable app data root."""
    archive_root = DATA_ROOT / "evidence" / "formulas" / "package"
    manifest_path = archive_root / "manifest.json"
    existing = read_json(manifest_path, {})
    # A packaged EXE may start before TDX is configured. Preserve a complete
    # data-package mirror in that case; a health check must never destroy the
    # last known-good formula inputs by copying from the resource-library cwd.
    if not tdx_root_available():
        package_state = _formula_package_state()
        if package_state.get("status") in {"available", "degraded"}:
            if isinstance(existing, dict) and existing:
                preserved = dict(existing)
                # Recompute status from the files, not a stale status field
                # left by an earlier empty-root probe.
                preserved["status"] = package_state["status"]
                preserved["missing_files"] = package_state.get("missing_files", [])
                # Persist the repaired view as the canonical resource-library
                # manifest. Otherwise the Python preflight would see the
                # files, while the Node bridge could still read an old
                # `status=missing` value after a restart.
                write_json(manifest_path, preserved)
                return preserved
            preserved = {
                "schema": "ZHANGCAI_TDX_TQ_FORMULA_SOURCE_ARCHIVE_V1",
                "path": str(archive_root.relative_to(DATA_ROOT)).replace("\\", "/"),
                "required_files": package_state.get("required_files", []),
                "copied_files": [{"path": item} for item in package_state.get("copied_files", [])],
                "missing_files": package_state.get("missing_files", []),
                "status": package_state.get("status", "degraded"),
                "source_root": "",
                "archived_at": package_state.get("archived_at", ""),
            }
            write_json(manifest_path, preserved)
            return preserved
    copied: list[dict[str, Any]] = []
    missing: list[str] = []
    for relative in FORMULA_SOURCE_RELATIVE_PATHS:
        source = TDX_ROOT / relative
        target = archive_root / relative
        if not source.is_file():
            missing.append(relative)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append({
            "path": str(target.relative_to(DATA_ROOT)).replace("\\", "/"),
            "source": str(source),
            "bytes": target.stat().st_size,
            "sha256": sha256_file(target),
        })
    manifest = {
        "schema": "ZHANGCAI_TDX_TQ_FORMULA_SOURCE_ARCHIVE_V1",
        "archived_at": utc_now(),
        "source_root": str(TDX_ROOT) if tdx_root_available() else "",
        "path": str(archive_root.relative_to(DATA_ROOT)).replace("\\", "/"),
        "required_files": list(FORMULA_SOURCE_RELATIVE_PATHS),
        "copied_files": copied,
        "missing_files": missing,
        "status": "available" if not missing else ("degraded" if copied else "missing"),
    }
    write_json(archive_root / "manifest.json", manifest)
    return manifest


def update_status() -> dict[str, Any]:
    stage_public_snapshots()
    package_gaps = package_source_gap_report()
    daily_raw = read_json(DATA_ROOT / "status" / "tdx-daily-history.json", {"status": "missing", "asset": "tdx_daily_history", "reason": "尚未归档本地日线。"})
    daily = decorate_daily_asset(daily_raw)
    formula = formula_status()
    formula_archive = dict(formula.get("source_archive") or {})
    formula_archive.update({
        "asset": "tdx_formula_source_archive",
        "checked_at": utc_now(),
        "path": "evidence/formulas/package/",
        "reason": "" if formula_archive.get("status") == "available" else "公式依赖镜像仍有缺项。",
    })
    minute_data = minute_data_status()
    assets = {
        "tdx_daily_history": daily,
        "tdx_lc5_external": minute_data,
        "tdx_tq_formula": formula,
        "tdx_formula_source_archive": formula_archive,
        "unified_source_manifest": file_asset_state("unified_source_manifest", DATA_ROOT / "evidence" / "sources" / "latest.json", "统一数据源落盘清单"),
        "unified_source_verification": file_asset_state("unified_source_verification", DATA_ROOT / "evidence" / "sources" / "latest-verification.json", "统一数据源落盘校验"),
        "package_source_inventory": file_asset_state("package_source_inventory", DATA_ROOT / "harness" / "context" / "package-source-inventory.json", "行情能力包来源目录"),
        "package_source_gaps": {
            "status": "available" if package_gaps.get("missing_count", 0) == 0 else "degraded",
            "asset": "package_source_gaps",
            "checked_at": package_gaps.get("generated_at", utc_now()),
            "path": "harness/context/package-source-gap-report.json",
            "missing_count": package_gaps.get("missing_count", 0),
            "reason": f"已固化压缩包来源与数据缺口，共 {package_gaps.get('missing_count', 0)} 项未完全闭合。",
        },
        "package_data_routing": file_asset_state("package_data_routing", DATA_ROOT / "harness" / "context" / "package-data-routing.json", "压缩包数据路由"),
        "package_source_snapshots": public_asset_state("package_source_snapshots", DATA_ROOT / "evidence" / "package-sources", "压缩包来源实际快照"),
        "runtime_policy": file_asset_state("runtime_policy", DATA_ROOT / "harness" / "context" / "runtime-policy.json", "3003 自包含运行时政策"),
        "report_archive": public_asset_state("report_archive", DATA_ROOT / "reports" / "archive", "本地 Harness 报告归档"),
        "security_master": security_master_status(),
        "limit_up_pool": public_asset_state("limit_up_pool", DATA_ROOT / "public" / "limit-up", "涨停池"),
        "lhb_data": public_asset_state("lhb_data", DATA_ROOT / "public" / "lhb", "龙虎榜原始快照"),
        "public_research": public_research_status(),
        "supplemental_stock": supplemental_stock_coverage(str((daily or {}).get("trade_date") or "").replace("-", "")),
        "execution_evidence": public_asset_state("execution_evidence", DATA_ROOT / "reports" / "daily", "任务回执与报告"),
        "skill_packages": package_status(),
    }
    value = {"schema": "ZHANGCAI_SKILL14_DATA_STATUS_V1", "checked_at": utc_now(), "data_root": str(DATA_ROOT), "assets": assets, "minute_data": minute_data}
    data_page = write_local_data_page(assets)
    value["local_data_page"] = {
        "path": "harness/context/local-data-page.json",
        "schema": data_page.get("schema"),
        "latest_tdx_trade_date": data_page.get("latest_tdx_trade_date", ""),
    }
    write_json(DATA_ROOT / "status" / "current.json", value)
    return value


def prepare_packages() -> dict[str, Any]:
    skills_root = DATA_ROOT / "skills" / "packages"
    skills_root.mkdir(parents=True, exist_ok=True)
    installed = []
    for skill in catalog()["skills"]:
        archive = ARCHIVE_ROOT / str(skill["archive"])
        if not archive.is_file():
            installed.append({"id": skill["id"], "status": "missing_archive", "archive": str(archive)})
            continue
        destination = skills_root / skill["id"]
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(destination)
            nested = [entry for entry in bundle.namelist() if entry.lower().endswith(".zip")]
            for nested_name in nested:
                nested_destination = destination / "nested" / Path(nested_name).stem
                nested_destination.mkdir(parents=True, exist_ok=True)
                with bundle.open(nested_name) as source, zipfile.ZipFile(io.BytesIO(source.read())) as nested_bundle:
                    nested_bundle.extractall(nested_destination)
        installed.append({
            "id": skill["id"],
            "name": skill["name"],
            "status": "available",
            "archive": archive.name,
            "sha256": sha256_file(archive),
            "path": str(destination.relative_to(DATA_ROOT)).replace("\\", "/"),
        })
    manifest = {"schema": "ZHANGCAI_SKILL14_PACKAGE_MANIFEST_V1", "prepared_at": utc_now(), "skills": installed}
    write_json(DATA_ROOT / "skills" / "manifest.json", manifest)
    update_status()
    return manifest


def write_preflight(skill_id: str) -> dict[str, Any]:
    spec = next((item for item in catalog()["skills"] if item.get("id") == skill_id), None)
    if not spec:
        raise RuntimeError(f"未知技能：{skill_id}")
    current = update_status()
    assets = current["assets"]
    required_missing = [asset for asset in spec.get("required", []) if assets.get(asset, {}).get("status") != "available"]
    optional_missing = [asset for asset in spec.get("optional", []) if assets.get(asset, {}).get("status") != "available"]
    minute_spec = spec.get("minute_data") if isinstance(spec.get("minute_data"), dict) else {}
    minute_mode = str(minute_spec.get("mode") or "not_required")
    minute_data = current.get("minute_data") if isinstance(current.get("minute_data"), dict) else minute_data_status()
    minute_degraded = []
    resource_degraded = []
    # A complete portable formula mirror is usable as a resource-library
    # dependency even when a live TDX/TQ worker has not yet produced a current
    # receipt. Keep the run explicitly DEGRADED instead of reporting the whole
    # tdx_tq_formula asset as missing; live formula freshness remains visible.
    formula_asset = assets.get("tdx_tq_formula", {}) if isinstance(assets.get("tdx_tq_formula"), dict) else {}
    portable_formula = formula_asset.get("portable_package", {}) if isinstance(formula_asset.get("portable_package"), dict) else {}
    if "tdx_tq_formula" in required_missing and portable_formula.get("status") == "available":
        required_missing = [item for item in required_missing if item != "tdx_tq_formula"]
        resource_degraded.append("tdx_tq_formula@live_receipt")
    if minute_mode == "optional_degraded" and minute_data.get("status") != "available":
        minute_degraded.append("minute_data@external_tdx_lc5")
    daily_gate = assets.get("tdx_daily_history", {}).get("freshness", {}) if isinstance(assets.get("tdx_daily_history"), dict) else {}
    daily_usable = bool(daily_gate.get("usable")) or daily_gate.get("status") == "available"
    daily_degraded = daily_gate.get("status") == "degraded" and daily_usable
    if "tdx_daily_history" in spec.get("required", []):
        if daily_usable:
            # The selected local TDX day or a prior resource-library archive
            # is a valid degraded input. Do not turn a newer requested date
            # into a hard gate such as tdx_daily_history@20260922.
            required_missing = [item for item in required_missing if item != "tdx_daily_history"]
            if daily_degraded:
                selected = str(daily_gate.get("selected_trade_date") or daily_gate.get("archive_trade_date") or "unknown")
                source = str(daily_gate.get("selected_source") or "local daily source")
                resource_degraded.append(f"tdx_daily_history@{selected} ({source})")
        else:
            # Only a missing/incomplete archive is a hard gate.  A historical
            # archive that passes coverage and manifest checks is handled by
            # the degraded branch above.
            required_missing = [item for item in required_missing if item != "tdx_daily_history"]
            target = str(daily_gate.get("expected_trade_date") or "unknown")
            required_missing.append(f"tdx_daily_history@{target}")
    status = "BLOCKED" if required_missing else ("DEGRADED" if optional_missing or minute_degraded or resource_degraded else "READY_FOR_VALIDATED_RUN")
    requested_date = str(daily_gate.get("requested_trade_date") or daily_gate.get("expected_trade_date") or "")
    date = str(daily_gate.get("selected_trade_date") or daily_gate.get("archive_trade_date") or requested_date or assets.get("tdx_daily_history", {}).get("trade_date") or datetime.now().strftime("%Y%m%d"))
    report_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{skill_id}-{uuid.uuid4().hex[:8]}"
    report_root = DATA_ROOT / "reports" / "daily" / date
    evidence = {
        "schema": "ZHANGCAI_SKILL14_PREFLIGHT_V1",
        "report_id": report_id,
        "skill": spec,
        "status": status,
        "created_at": utc_now(),
        "data_root": str(DATA_ROOT),
        "required_missing": required_missing,
        "optional_missing": optional_missing,
        "degraded_missing": minute_degraded,
        "resource_degraded": resource_degraded,
        "minute_data": {
            **minute_data,
            "requirement": minute_mode,
            "purpose": str(minute_spec.get("purpose") or "普通任务不依赖 5 分钟线。"),
        },
        "assets": {key: assets.get(key, {}) for key in [*spec.get("required", []), *spec.get("optional", [])]},
        "target_trade_date": date,
        "requested_trade_date": requested_date,
        "selected_trade_date": date,
        "daily_source": daily_gate.get("selected_source", ""),
        "daily_data_degraded": daily_degraded,
        "daily_freshness": daily_gate,
        "degrade_policy": spec.get("degrade", ""),
        "execution_note": "本报告是网页适配层的真实数据预检与 resource-library 落盘运行单；未调用原始策略入口，因此不构成策略已执行或投资结论。",
    }
    write_json(report_root / f"{report_id}.json", evidence)
    markdown = [
        f"# {spec['name']} · 网页适配预检",
        "",
        f"- 状态：`{status}`",
        f"- 创建时间：{evidence['created_at']}",
        f"- 数据目录：`{DATA_ROOT}`",
        f"- 请求交易日：`{requested_date or '未识别'}`",
        f"- 实际使用日线：`{date}`",
        f"- 缺少必需数据：{'、'.join(required_missing) if required_missing else '无'}",
        f"- 缺少可降级数据：{'、'.join([*optional_missing, *minute_degraded, *resource_degraded]) if optional_missing or minute_degraded or resource_degraded else '无'}",
        f"- 日线新鲜度：`{daily_gate.get('status', 'unknown')}` · {daily_gate.get('reason', '') or '已核对目标日 manifest、文件和覆盖数。'}",
        "",
        "## 降级规则",
        spec.get("degrade", "无"),
        "",
        "## 执行边界",
        evidence["execution_note"],
    ]
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / f"{report_id}.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    update_status()
    return evidence


def list_reports() -> dict[str, Any]:
    root = DATA_ROOT / "reports" / "daily"
    reports = []
    if root.is_dir():
        for path in root.rglob("*.json"):
            value = read_json(path, {})
            if isinstance(value, dict) and value.get("schema") == "ZHANGCAI_SKILL14_PREFLIGHT_V1":
                reports.append({
                    "report_id": value.get("report_id"),
                    "skill_id": value.get("skill", {}).get("id"),
                    "skill_name": value.get("skill", {}).get("name"),
                    "status": value.get("status"),
                    "created_at": value.get("created_at"),
                    "updated_at": value.get("updated_at") or value.get("created_at"),
                    "path": str(path.relative_to(DATA_ROOT)).replace("\\", "/"),
                })
            elif isinstance(value, dict) and value.get("schema") == "ZHANGCAI_DAILY_DATA_ARCHIVE_REPORT_V1":
                reports.append({
                    "report_id": value.get("report_id"),
                    "skill_id": "daily-data-archive",
                    "skill_name": "本地数据归档日报",
                    "status": value.get("status"),
                    "created_at": value.get("created_at"),
                    "updated_at": value.get("updated_at") or value.get("created_at"),
                    "path": str(path.relative_to(DATA_ROOT)).replace("\\", "/"),
                })
    reports.sort(
        key=lambda item: (
            report_sort_timestamp(item.get("updated_at") or item.get("created_at")),
            str(item.get("report_id") or ""),
        ),
        reverse=True,
    )
    return {"status": "ok", "reports": reports[:60]}


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    archive_parser = subparsers.add_parser("archive-daily")
    archive_parser.add_argument("--history-days", type=int, default=0, help="每个证券保留的历史条数；0 表示读取本地 .day 全部可用历史")
    subparsers.add_parser("status")
    subparsers.add_parser("prepare-packages")
    subparsers.add_parser("write-daily-report")
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--skill-id", required=True)
    subparsers.add_parser("list-reports")
    args = parser.parse_args()
    try:
        if args.command == "archive-daily":
            result = archive_daily(0 if args.history_days <= 0 else min(args.history_days, 20000))
        elif args.command == "prepare-packages":
            result = prepare_packages()
        elif args.command == "preflight":
            result = write_preflight(args.skill_id)
        elif args.command == "write-daily-report":
            manifest = read_json(DATA_ROOT / "status" / "tdx-daily-history.json", {})
            if not isinstance(manifest, dict) or not manifest.get("trade_date"):
                raise RuntimeError("尚无可写入日报的日线归档清单")
            current_status = update_status()
            result = {"status": "ok", "report": write_daily_archive_report(manifest, current_status.get("assets", {}))}
        elif args.command == "list-reports":
            result = list_reports()
        else:
            result = update_status()
        sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False) + "\n").encode("utf-8"))
        return 0
    except Exception as error:  # Keep the bridge response typed and safe for UI display.
        sys.stdout.buffer.write((json.dumps({"status": "error", "error": f"{type(error).__name__}: {error}"}, ensure_ascii=False) + "\n").encode("utf-8"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
