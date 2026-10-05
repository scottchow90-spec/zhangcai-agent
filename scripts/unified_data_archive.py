#!/usr/bin/env python3
"""Build and verify one EXE-friendly data-source archive index.

The existing collectors keep their raw payloads in source-specific folders.
This module does not replace those collectors or invent missing data.  It
creates a small, stable manifest that points Harness and a future EXE to all
available files, records the source coverage declared by the imported data
package, and explicitly marks sources that are only documented or not
configured.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


APP_ROOT = Path(os.environ.get("ZHANGCAI_APP_ROOT", Path(__file__).resolve().parents[1]))
DATA_ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR", APP_ROOT / "app-data"))
SOURCE_EVIDENCE_ROOT = DATA_ROOT / "evidence" / "sources"
PACKAGE_NAME = "A股行情资讯全接口与数据能力大全_WorkBuddy电脑版_20260908-014459.zip"
PACKAGE_PATH = APP_ROOT / "skill-archives" / PACKAGE_NAME


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(DATA_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def file_asset(path: Path, source: str, status: str = "available", **extra: Any) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "path": rel(path),
        "source": source,
        "status": status,
        "exists": path.is_file(),
    }
    if path.is_file():
        value.update({"bytes": path.stat().st_size, "sha256": sha256_file(path)})
    value.update(extra)
    if not path.is_file() and status == "available":
        value["status"] = "missing"
    return value


def public_research_asset(data_root: Path, target_date: str) -> tuple[Path, str, Dict[str, Any]]:
    """Prefer real dated news over a market-only fallback at the stable alias."""
    candidates = [
        data_root / "evidence" / "public" / "latest.json",
        data_root / "news" / "latest.json",
        data_root / "evidence" / "public" / "fallback-latest.json",
    ]
    inspected: list[tuple[Path, Dict[str, Any], list[Dict[str, Any]], str]] = []
    for path in candidates:
        value = read_json(path, {})
        if not isinstance(value, dict) or not value:
            continue
        snapshot = value.get("snapshot") if isinstance(value.get("snapshot"), dict) else value
        records = snapshot.get("records") if isinstance(snapshot.get("records"), list) else []
        if not records and isinstance(snapshot.get("providers"), dict):
            records = [row for provider in snapshot["providers"].values() if isinstance(provider, dict) for row in provider.get("records", []) if isinstance(row, dict)]
        if not records and isinstance(snapshot.get("source"), dict):
            records = snapshot["source"].get("records", []) if isinstance(snapshot["source"].get("records"), list) else []
        records = [row for row in records if isinstance(row, dict)]
        fallback_kind = str(value.get("fallback_kind") or "")
        inspected.append((path, value, records, fallback_kind))
    selected = next((item for item in inspected if item[2] and not item[3]), None)
    if selected is None:
        selected = next((item for item in inspected if item[3]), None)
    if selected is None:
        return candidates[0], "missing", {"context_record_count": 0, "same_day_record_count": 0, "source_date": "", "fallback_kind": ""}
    path, value, records, fallback_kind = selected
    date_pattern = re.compile(r"(\d{4}-\d{1,2}-\d{1,2})")
    record_dates = []
    same_day_count = 0
    for record in records:
        raw_date = str(record.get("source_timestamp") or record.get("publishedAt") or record.get("published_at") or record.get("publish_time") or record.get("date") or "")
        match = date_pattern.search(raw_date.replace("/", "-"))
        if not match:
            continue
        parts = match.group(1).split("-")
        record_date = f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        record_dates.append(record_date)
        if record_date == display_date(target_date):
            same_day_count += 1
    source_date = max(record_dates) if record_dates else str(value.get("source_date") or value.get("date") or "")
    status = "available" if records and same_day_count > 0 and not fallback_kind else "degraded"
    return path, status, {
        "context_record_count": len(records),
        "same_day_record_count": same_day_count,
        "source_date": source_date,
        "fallback_kind": fallback_kind,
        "target_date": display_date(target_date),
    }


def compact_date(value: str) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits if len(digits) == 8 else ""


def display_date(value: str) -> str:
    digits = compact_date(value)
    return f"{digits[:4]}-{digits[4:6]}-{digits[6:]}" if digits else ""


def latest_archive_date() -> str:
    for path in (
        DATA_ROOT / "status" / "tdx-daily-history.json",
        DATA_ROOT / "market" / "daily" / "<missing>" / "manifest.json",
    ):
        value = read_json(path, {})
        if isinstance(value, dict):
            date = compact_date(value.get("trade_date") or value.get("targetDate"))
            if date:
                return date
    root = DATA_ROOT / "market" / "daily"
    dates = sorted((p.name for p in root.iterdir() if p.is_dir() and compact_date(p.name)), reverse=True) if root.is_dir() else []
    return dates[0] if dates else ""


def zip_json(bundle: zipfile.ZipFile, name: str, default: Any) -> Any:
    try:
        return json.loads(bundle.read(name).decode("utf-8-sig"))
    except (KeyError, UnicodeDecodeError, ValueError):
        return default


def package_inventory() -> Dict[str, Any]:
    """Copy only the package's source inventory into app-data for Harness."""
    target = DATA_ROOT / "harness" / "context" / "package-source-inventory.json"
    if not PACKAGE_PATH.is_file():
        value = {
            "schema": "ZHANGCAI_PACKAGE_SOURCE_INVENTORY_V1",
            "status": "missing",
            "archive": str(PACKAGE_PATH),
            "error": "行情数据能力压缩包未找到",
            "generated_at": now_iso(),
        }
        write_json(target, value)
        return value
    try:
        with zipfile.ZipFile(PACKAGE_PATH) as bundle:
            manifest = zip_json(bundle, "package-manifest.json", {})
            inventory = zip_json(bundle, "references/接口与网站穷举清单.json", {})
        value = {
            "schema": "ZHANGCAI_PACKAGE_SOURCE_INVENTORY_V1",
            "status": "available" if isinstance(inventory, dict) else "degraded",
            "archive": str(PACKAGE_PATH),
            "archive_name": PACKAGE_NAME,
            "archive_version": manifest.get("version", "") if isinstance(manifest, dict) else "",
            "canonical_skill_count": inventory.get("canonical_skill_count", 0) if isinstance(inventory, dict) else 0,
            "site_host_count": inventory.get("site_host_count", 0) if isinstance(inventory, dict) else 0,
            "core_data_layers": inventory.get("core_data_layers", 0) if isinstance(inventory, dict) else 0,
            "core_endpoint_count": inventory.get("core_endpoint_count", 0) if isinstance(inventory, dict) else 0,
            "canonical_skill_ids": inventory.get("canonical_skill_ids", []) if isinstance(inventory, dict) else [],
            "sites": inventory.get("sites", []) if isinstance(inventory, dict) else [],
            "generated_at": now_iso(),
            "read_rule": "包内源码和接口地址只作为来源目录；是否可用以本清单的 runtime_status 和实际文件为准。",
        }
    except (OSError, zipfile.BadZipFile) as exc:
        value = {
            "schema": "ZHANGCAI_PACKAGE_SOURCE_INVENTORY_V1",
            "status": "degraded",
            "archive": str(PACKAGE_PATH),
            "error": f"{type(exc).__name__}: {exc}",
            "generated_at": now_iso(),
        }
    write_json(target, value)
    return value


def record_count(source: Dict[str, Any]) -> Optional[int]:
    data = source.get("data") if isinstance(source, dict) else None
    if not isinstance(data, dict):
        return None
    if isinstance(data.get("records"), list):
        return len(data["records"])
    nested = data.get("data")
    if isinstance(nested, dict) and isinstance(nested.get("pool"), list):
        return len(nested["pool"])
    result = data.get("result")
    if isinstance(result, dict) and isinstance(result.get("data"), list):
        return len(result["data"])
    return None


def public_source_status(public: Dict[str, Any], *names: str) -> str:
    sources = public.get("sources") if isinstance(public, dict) else {}
    sources = sources if isinstance(sources, dict) else {}
    values = [sources.get(name, {}) for name in names]
    available = sum(1 for item in values if isinstance(item, dict) and item.get("status") == "available")
    if available == len(names) and names:
        return "available"
    if available:
        return "partial"
    return "missing"


def package_gap_status(source_id: str, default: str = "declared_not_snapshotted") -> tuple[str, str, List[str]]:
    """Read the Harness package-gap contract when it has been generated."""
    report = read_json(DATA_ROOT / "harness" / "context" / "package-source-gap-report.json", {})
    rows = report.get("source_items", []) if isinstance(report, dict) else []
    row = next((item for item in rows if isinstance(item, dict) and item.get("id") == source_id), None)
    if not isinstance(row, dict):
        return default, "尚未生成压缩包来源缺口报告。", []
    status = str(row.get("current_status") or row.get("status") or default)
    reason = str(row.get("missing_reason") or "")
    paths = row.get("last_artifact") or []
    if isinstance(paths, str):
        paths = [paths]
    return status, reason, [str(path) for path in paths]


def source_row(source_id: str, name: str, layer: str, status: str, reason: str, paths: Iterable[str]) -> Dict[str, Any]:
    return {
        "id": source_id,
        "name": name,
        "layer": layer,
        "status": status,
        "reason": reason,
        "paths": list(paths),
    }


def build_source_matrix(public: Dict[str, Any], news: Dict[str, Any], date: str) -> List[Dict[str, Any]]:
    public_path = "public/latest.json"
    news_path = "news/latest.json"
    daily_manifest = read_json(DATA_ROOT / "market" / "daily" / date / "manifest.json", {})
    daily_path = str(daily_manifest.get("file") or "market/daily/aggregate/tdx-bars.jsonl") if isinstance(daily_manifest, dict) else "market/daily/aggregate/tdx-bars.jsonl"
    daily_delta = str(daily_manifest.get("delta_file") or "") if isinstance(daily_manifest, dict) else ""
    source_root = f"public/{date}" if date else "public/"
    news_root = f"news/{date}" if date else "news/"
    supplemental_path = DATA_ROOT / "evidence" / "supplemental" / date / "market.json"
    supplemental = read_json(supplemental_path, {})
    supplemental_coverage = supplemental.get("coverage", {}) if isinstance(supplemental, dict) else {}
    stock_summary = supplemental.get("stock_summary", {}) if isinstance(supplemental, dict) else {}
    stock_file_count = int(stock_summary.get("requested_count") or 0) if isinstance(stock_summary, dict) else 0
    supplemental_rel = f"evidence/supplemental/{date}/market.json"
    daily_index_path = DATA_ROOT / "market" / "daily" / "index" / "daily-data-index.json"
    daily_index = read_json(daily_index_path, {})
    daily_date_info = daily_index.get("dates", {}).get(date, {}) if isinstance(daily_index, dict) else {}
    public_status = public_source_status
    rows = [
        source_row("tdx-local", "本地通达信/TQ/mootdx 数据族", "行情、公式、基础资料", "available" if (DATA_ROOT / daily_path).is_file() else "missing", "以本地 TDX 日线归档和 TQ 现场回执为准；mootdx 文档接口不等于本运行时已全部暴露。", [daily_path, *([daily_delta] if daily_delta else []), f"market/security-master/{date}.jsonl", "evidence/formulas/"]),
        source_row("public-daily-fallback", "东方财富/腾讯公开历史日线降级层", "TDX 断开时的缺口日线", "available" if int(daily_date_info.get("available_fallback_records") or daily_date_info.get("fetched_count") or 0) > 0 else "missing", "只接受明确返回目标交易日的未复权 OHLCV；按 daily-data-index 合并使用并保持 quality=degraded，成交额缺失时留空，绝不估算。", ["market/daily/index/daily-data-index.json", f"market/daily/{date}/daily-data-index.json", f"market/daily/fallback/{date}/"]),
        source_row("eastmoney", "东方财富公开数据族", "涨停、龙虎榜、新闻及部分公开数据", "available" if public_status(public, "eastmoneyLimitUp", "eastmoneyLhb") == "available" else "partial" if public_status(public, "eastmoneyLimitUp", "eastmoneyLhb") == "partial" else "missing", "当前统一快照已落盘涨停池、龙虎榜和 7×24 快讯；研报、资金流、解禁、财务等其他端点仍未集中快照。", [public_path, f"public/limit-up/{display_date(date)}.json", f"public/lhb/{display_date(date)}.json", news_path]),
        source_row("lianban", "连板网", "涨停、连板、情绪补充", public_status(public, "lianban"), "同日开放数据快照。", [public_path, f"public/limit-up/{display_date(date)}.json"]),
        source_row("akshare", "AKShare 适配器", "龙虎榜、涨停池、席位明细", "available" if public_status(public, "akshareLhb", "akshareLhbSina", "akshareLhbStockStatistic", "akshareLimitUpPool", "akshareLhbStockDetail") == "available" else "partial" if public_status(public, "akshareLhb", "akshareLhbSina", "akshareLhbStockStatistic", "akshareLimitUpPool", "akshareLhbStockDetail") == "partial" else "missing", "可选依赖；每个适配器状态保存在公开行情快照。", [public_path, source_root]),
        source_row("tencent", "腾讯财经", "实时行情、估值、指数、ETF", *package_gap_status("tencent")),
        source_row("sina", "新浪财经", "复权因子、财报、期权、行业备援", *package_gap_status("sina")),
        source_row("baidu", "百度股市通", "带均线 K 线", *package_gap_status("baidu")),
        source_row("ths", "同花顺", "一致预期、热点、热榜、涨停原因", *package_gap_status("ths")),
        source_row("iwencai", "问财 IWencai", "自然语言研报与选股", *package_gap_status("iwencai", "blocked")),
        source_row("cls", "财联社", "全市场电报", *package_gap_status("cls")),
        source_row("baostock", "BaoStock", "历史估值、上市/退市日", *package_gap_status("baostock", "not_configured")),
        source_row("sw", "申万研究", "行业分类变迁史", *package_gap_status("sw")),
        source_row("cninfo", "巨潮资讯", "公告、互动易", *package_gap_status("cninfo")),
        source_row("exchange-official", "沪深交易所/HKEX 官方", "龙虎榜、公告、北向备援", *package_gap_status("exchange-official")),
        source_row("macro", "人民银行/国家统计局", "社融、PMI", *package_gap_status("macro")),
        source_row("public-web", "公开网页工具与舆情站点", "文章、RSS、社区与动态网页", *package_gap_status("public-web")),
        source_row("eastmoney-news", "东方财富 7×24 快讯", "市场新闻", "available" if news.get("status") == "available" else "missing", "当前统一新闻快照。", [news_path, f"evidence/public/news-{display_date(date)}.json", news_root]),
        source_row("sina-financial", "新浪财务三表", "个股财务", "partial" if stock_file_count else "on_demand", "财务三表按目标股票按需落盘；Harness 读取 evidence/supplemental/<date>/<code>.<market>.json，不能把未请求的全市场财务误报为缺失。", [supplemental_rel, f"evidence/supplemental/{date}/<code>.<market>.json"]),
        source_row("tencent-share-capital", "腾讯行情股本字段", "流通股本/总股本", "partial" if stock_file_count else "on_demand", "流通股本和总股本按目标股票按需落盘，保留原始报价哈希和字段映射。", [supplemental_rel, f"evidence/supplemental/{date}/<code>.<market>.json"]),
        source_row("tdx-index-daily", "通达信指数日线", "指数日线", "available" if supplemental_coverage.get("index_daily") is True else "missing", "主要指数日线来自本地 TDX .day，统一写入补充快照供 Harness 索引复用。", [supplemental_rel]),
        source_row("longhubang-snapshot", "东方财富/本地龙虎榜", "龙虎榜与席位", "available" if supplemental_coverage.get("longhubang_snapshot") is True else "missing", "同日全市场快照已落盘；目标股票没有记录时表示无上榜记录，不表示快照缺失。", [supplemental_rel, f"public/lhb/{display_date(date)}.json"]),
        source_row("eastmoney-margin", "东方财富融资融券明细", "融资融券快照", "available" if supplemental_coverage.get("margin_snapshot") is True else "missing", "融资融券按同日或最近可得日期落盘；exact_date=false 时 Harness 必须显示实际最近日期。", [supplemental_rel]),
    ]
    return rows


def snapshot(date_value: str) -> Dict[str, Any]:
    date = compact_date(date_value) or latest_archive_date()
    if not date:
        raise RuntimeError("尚无可识别的 TDX 归档交易日")
    public = read_json(DATA_ROOT / "public" / "latest.json", {})
    news = read_json(DATA_ROOT / "news" / "latest.json", {})
    package = package_inventory()
    daily_manifest = read_json(DATA_ROOT / "market" / "daily" / date / "manifest.json", {})
    daily_bars_rel = str(daily_manifest.get("file") or "market/daily/aggregate/tdx-bars.jsonl") if isinstance(daily_manifest, dict) else "market/daily/aggregate/tdx-bars.jsonl"
    daily_delta_rel = str(daily_manifest.get("delta_file") or "") if isinstance(daily_manifest, dict) else ""
    daily_bars_path = DATA_ROOT / daily_bars_rel
    daily_index_path = DATA_ROOT / "market" / "daily" / "index" / "daily-data-index.json"
    daily_date_index_path = DATA_ROOT / "market" / "daily" / date / "daily-data-index.json"
    tdx_symbol_index_path = DATA_ROOT / "market" / "daily" / "index" / "tdx-symbol-index.json"
    fallback_dir = DATA_ROOT / "market" / "daily" / "fallback" / date
    daily_index = read_json(daily_index_path, {})
    security_path = DATA_ROOT / "market" / "security-master" / f"{date}.jsonl"
    formula_manifest = DATA_ROOT / "evidence" / "formulas" / "package" / "manifest.json"
    public_path = DATA_ROOT / "public" / "latest.json"
    public_research_path, public_research_status, public_research_meta = public_research_asset(DATA_ROOT, date)
    news_path = DATA_ROOT / "news" / "latest.json"
    supplemental_path = DATA_ROOT / "evidence" / "supplemental" / date / "market.json"
    supplemental = read_json(supplemental_path, {})
    jsonl_integrity_path = DATA_ROOT / "runtime" / f"daily-jsonl-integrity-{date}.json"
    assets = [
        file_asset(daily_bars_path, "本地通达信 .day 全量/聚合归档", "available" if daily_manifest.get("status") == "available" else "degraded", record_count=daily_manifest.get("bar_records"), trade_date=daily_manifest.get("trade_date", date)),
        file_asset(DATA_ROOT / "market" / "daily" / date / "manifest.json", "本地通达信归档清单", "available" if daily_manifest else "missing", trade_date=daily_manifest.get("trade_date", date)),
        file_asset(daily_index_path, "统一日线可用性索引", "available" if daily_index_path.is_file() else "missing", trade_date=date, summary=daily_index.get("summary", {}) if isinstance(daily_index, dict) else {}),
        file_asset(daily_date_index_path, "交易日级日线索引", "available" if daily_date_index_path.is_file() else "missing", trade_date=date),
        file_asset(tdx_symbol_index_path, "通达信证券日线索引", "available" if tdx_symbol_index_path.is_file() else "missing", trade_date=date),
        file_asset(jsonl_integrity_path, "日线 JSONL 逐行结构校验报告", "available" if jsonl_integrity_path.is_file() else "missing", trade_date=date),
        file_asset(security_path, "通达信 TNF + 应用证券基线", "available" if security_path.is_file() else "missing", trade_date=date),
        file_asset(public_path, "东方财富/连板网/AKShare 公开行情快照", "available" if public.get("sources") else "missing", source_date=public.get("date", "")),
        file_asset(DATA_ROOT / "public" / "limit-up" / f"{display_date(date)}.json", "公开涨停池归档", "available"),
        file_asset(DATA_ROOT / "public" / "lhb" / f"{display_date(date)}.json", "公开龙虎榜归档", "available"),
        file_asset(news_path, "东方财富 7×24 快讯", "available" if news.get("status") == "available" else "missing", source_date=news.get("date", "")),
        file_asset(
            public_research_path,
            "公开研究统一快照",
            public_research_status,
            source_date=public_research_meta.get("source_date", ""),
            target_date=public_research_meta.get("target_date", display_date(date)),
            context_record_count=public_research_meta.get("context_record_count", 0),
            same_day_record_count=public_research_meta.get("same_day_record_count", 0),
            fallback_kind=public_research_meta.get("fallback_kind", ""),
        ),
        file_asset(supplemental_path, "财务/股本/指数日线/龙虎榜/融资融券统一补充快照", "available" if supplemental else "missing", trade_date=date, coverage=supplemental.get("coverage", {}) if isinstance(supplemental, dict) else {}),
        file_asset(
            formula_manifest,
            "本地 TDX/TQ 公式依赖镜像",
            str(read_json(formula_manifest, {}).get("status") or "missing") if formula_manifest.is_file() else "missing",
            missing_files=read_json(formula_manifest, {}).get("missing_files", []) if formula_manifest.is_file() else [],
        ),
        file_asset(DATA_ROOT / "harness" / "context" / "local-data-page.json", "Harness 本地数据页", "available"),
        file_asset(DATA_ROOT / "harness" / "context" / "package-source-inventory.json", "行情能力压缩包来源目录", package.get("status", "missing")),
        file_asset(DATA_ROOT / "harness" / "context" / "package-source-gap-report.json", "行情能力压缩包缺口清单", "available" if (DATA_ROOT / "harness" / "context" / "package-source-gap-report.json").is_file() else "missing"),
        file_asset(DATA_ROOT / "harness" / "context" / "package-data-routing.json", "行情能力压缩包数据路由", "available" if (DATA_ROOT / "harness" / "context" / "package-data-routing.json").is_file() else "missing"),
    ]
    if fallback_dir.is_dir():
        for fallback_file in sorted(fallback_dir.glob("*.jsonl")):
            assets.append(file_asset(fallback_file, "公开日线降级记录", "degraded", trade_date=date, source_date=date, quality="degraded"))
    if daily_delta_rel:
        assets.append(file_asset(DATA_ROOT / daily_delta_rel, "本次交易日 TDX 增量归档", "available", trade_date=date, record_count=daily_manifest.get("delta_records", 0)))
    manifest = {
        "schema": "ZHANGCAI_UNIFIED_DATA_ARCHIVE_V1",
        "status": "available" if all(item.get("exists") for item in assets[:4]) else "degraded",
        "generated_at": now_iso(),
        "trade_date": date,
        "source_date": display_date(date),
        "data_root": str(DATA_ROOT),
        "package_inventory": "harness/context/package-source-inventory.json",
        "assets": assets,
        "sources": build_source_matrix(public, news, date),
        "rules": [
            "统一清单只索引真实落盘文件；未取得或未配置的来源明确标记，不用模型补造。",
            "TDX 日线是历史和公式类技能主输入，公开行情不能替代日线。",
            "历史兼容目录不参与生产数据源清单、研究输入或报告生成。",
            "源码、接口清单和包存在不等于当前接口可用；以 status、source_date、sha256 和现场回执为准。",
        ],
    }
    target = SOURCE_EVIDENCE_ROOT / date / "manifest.json"
    write_json(target, manifest)
    write_json(SOURCE_EVIDENCE_ROOT / "latest.json", manifest)
    return {"status": manifest["status"], "manifest": rel(target), "latest": rel(SOURCE_EVIDENCE_ROOT / "latest.json"), "trade_date": date, "asset_count": len(assets), "source_count": len(manifest["sources"]), "available_source_count": sum(1 for item in manifest["sources"] if item.get("status") == "available")}


def verify(date_value: str) -> Dict[str, Any]:
    date = compact_date(date_value) or latest_archive_date()
    manifest_path = SOURCE_EVIDENCE_ROOT / date / "manifest.json"
    manifest = read_json(manifest_path, {})
    if not isinstance(manifest, dict) or manifest.get("schema") != "ZHANGCAI_UNIFIED_DATA_ARCHIVE_V1":
        raise RuntimeError(f"统一数据清单不存在：{rel(manifest_path)}")
    checks: List[Dict[str, Any]] = []
    for item in manifest.get("assets", []):
        if not isinstance(item, dict):
            continue
        path = DATA_ROOT / str(item.get("path", ""))
        exists = path.is_file()
        sha_ok = None
        if exists and item.get("sha256"):
            sha_ok = sha256_file(path) == item.get("sha256")
        ok = exists and (sha_ok is not False)
        checks.append({"path": item.get("path", ""), "status": "pass" if ok else "fail", "exists": exists, "sha256": "pass" if sha_ok is True else "not_checked" if sha_ok is None else "fail"})
    failed = [item for item in checks if item.get("status") != "pass"]
    source_rows = manifest.get("sources", []) if isinstance(manifest.get("sources"), list) else []
    declared_unavailable = [item.get("id") for item in source_rows if isinstance(item, dict) and item.get("status") not in {"available"}]
    status = "CLEAN_PASS" if not failed else "BLOCKED"
    result = {
        "schema": "ZHANGCAI_UNIFIED_DATA_ARCHIVE_VERIFICATION_V1",
        "status": status,
        "generated_at": now_iso(),
        "trade_date": date,
        "manifest": rel(manifest_path),
        "checks": checks,
        "failed_count": len(failed),
        "declared_sources_not_currently_snapshotted": declared_unavailable,
        "note": "本地文件与哈希校验通过不代表所有压缩包端点已现场取数；未集中快照来源已在 manifest.sources 中显式列出。",
    }
    target = SOURCE_EVIDENCE_ROOT / date / "verification.json"
    write_json(target, result)
    write_json(SOURCE_EVIDENCE_ROOT / "latest-verification.json", result)
    return {"status": status, "verification": rel(target), "trade_date": date, "checked_count": len(checks), "failed_count": len(failed), "not_snapshotted_count": len(declared_unavailable)}


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("--date", default="")
    check = sub.add_parser("verify")
    check.add_argument("--date", default="")
    sub.add_parser("status")
    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            value = snapshot(args.date)
        elif args.command == "verify":
            value = verify(args.date)
        else:
            value = {
                "status": "ok",
                "manifest": rel(SOURCE_EVIDENCE_ROOT / "latest.json"),
                "verification": rel(SOURCE_EVIDENCE_ROOT / "latest-verification.json"),
                "package_inventory": rel(DATA_ROOT / "harness" / "context" / "package-source-inventory.json"),
            }
        print(json.dumps(value, ensure_ascii=False))
        return 0 if value.get("status") not in {"BLOCKED", "error"} else 2
    except Exception as exc:
        print(json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
