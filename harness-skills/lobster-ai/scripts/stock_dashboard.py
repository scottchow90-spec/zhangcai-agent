from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import csv
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "LOBSTER-STOCK-DASHBOARD-V1"
MAX_SOURCE_BYTES = 8 * 1024 * 1024
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
APP_ROOT = Path(__file__).resolve().parents[3]
SKILLS_ROOT = Path(os.environ.get("STOCK_SKILLS_ROOT", str(APP_ROOT / "harness-skills"))).resolve()
REPORTS_ROOT = Path(os.environ.get("STOCK_REPORTS_ROOT", str(APP_ROOT / "reports"))).resolve()
GLOBAL_SCORE_CONTRACT = SKILLS_ROOT / "stock-unified" / "references" / "short_term_strong_stock_scoring_contract.json"
SCORE_CONTRACT_VERSION = "A-SHARE-STRONG-26F-100-V6.1"


SOURCE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "skill": "a-share-15d-selection",
        "name": "短线强势股26因子",
        "kind": "stock",
        "primary": ((SKILLS_ROOT / "a-share-15d-selection", "reports/audit/**/a-share-15d-selection-*.json"),),
        "exclude": ("-freshness.json", "receipt.json"),
    },
    {
        "skill": "a-share-bottom-fishing",
        "name": "A股抄底",
        "kind": "stock",
        "primary": ((REPORTS_ROOT, "*bottom_fishing*/output/final_picks*_validated.json"),),
    },
    {
        "skill": "a-share-limit-up-leader-classification",
        "name": "涨停龙头分类",
        "kind": "stock",
        "primary": (
            (SKILLS_ROOT / "a-share-limit-up-leader-classification", "run/business_result.json"),
            (SKILLS_ROOT / "a-share-limit-up-leader-classification", "reports/**/business_result.json"),
        ),
    },
    {
        "skill": "a-share-limit-up-mining",
        "name": "连板挖掘",
        "kind": "stock",
        "primary": (
            (REPORTS_ROOT, "*lianban_mining*/business_result.json"),
            (REPORTS_ROOT, "*lianban_mining*/selection_result.json"),
        ),
        "fallback": ((REPORTS_ROOT, "*lianban_mining*/source_failure.json"),),
    },
    {
        "skill": "buzhang-leader-mining",
        "name": "补涨龙头",
        "kind": "stock",
        "primary": ((SKILLS_ROOT / "buzhang-leader-mining", "reports/**/buzhang_result.json"),),
    },
    {
        "skill": "chanlun-first-board",
        "name": "缠论首板",
        "kind": "stock",
        "primary": ((REPORTS_ROOT, "*limitup_firstboard_chan_standard/output/final_top_by_standard_buy_point.csv"),),
    },
    {
        "skill": "dragon-pullback",
        "name": "龙头回踩",
        "kind": "stock",
        "primary": (
            (SKILLS_ROOT / "dragon-pullback", "reports/strong-leader-first-yin-latest.json"),
            (SKILLS_ROOT / "dragon-pullback", "reports/strong-leader-first-yin-*.json"),
        ),
    },
    {
        "skill": "feilong-strategy",
        "name": "飞龙在天",
        "kind": "stock",
        "primary": (
            (SKILLS_ROOT / "feilong-strategy", "run/result.json"),
            (SKILLS_ROOT / "feilong-strategy", "reports/feilong-result-latest.json"),
        ),
    },
    {
        "skill": "five-dimension-resonance",
        "name": "五维共振",
        "kind": "stock",
        "primary": ((REPORTS_ROOT, "*five_dimension*/feilong_block_resonance_scan.json"),),
    },
    {
        "skill": "four-strategy-system",
        "name": "四套战法",
        "kind": "stock",
        "primary": ((SKILLS_ROOT / "four-strategy-system", "reports/four-strategy-*.json"),),
    },
    {
        "skill": "golden-ignition",
        "name": "黄金点火",
        "kind": "stock",
        "primary": ((REPORTS_ROOT, "*/golden-ignition/golden_ignition_report.json"),),
    },
    {
        "skill": "hotspot-leader",
        "name": "热点龙头",
        "kind": "theme",
        "primary": ((REPORTS_ROOT, "**/hotspot-leader/hotspot_leader_report.json"),),
    },
    {
        "skill": "limit-up-review",
        "name": "涨停复盘",
        "kind": "stock",
        "primary": ((REPORTS_ROOT, "*limit_up_review_closed_loop/business_result.json"),),
        "fallback": ((REPORTS_ROOT, "*limit_up_review_unified_smoke/entry_result.json"),),
    },
    {
        "skill": "nana-teacher-five-strategies",
        "name": "娜娜老师5策略",
        "kind": "stock",
        "primary": ((SKILLS_ROOT / "nana-teacher-five-strategies", "outputs/**/nana_five_strategy_scan.json"),),
    },
    {
        "skill": "oversold-first-board",
        "name": "超跌首板",
        "kind": "stock",
        "primary": ((SKILLS_ROOT / "oversold-first-board", "reports/oversold-first-board-*.json"),),
    },
    {
        "skill": "quality-track-stock-selection",
        "name": "优质赛道选股",
        "kind": "stock",
        "primary": ((SKILLS_ROOT / "quality-track-stock-selection", "run/practical_selection.json"),),
    },
    {
        "skill": "quant-strategy-bundle-chen",
        "name": "陈氏量化策略包",
        "kind": "stock",
        "primary": ((SKILLS_ROOT / "quant-strategy-bundle-chen", "reports/audit/quant-strategy-bundle-*.json"),),
    },
    {
        "skill": "shortline-hotspot-mining",
        "name": "短线热点挖掘",
        "kind": "theme",
        "primary": ((REPORTS_ROOT, "*shortline_hotspot_mining/market_scan.json"),),
    },
)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def source_fingerprint(sources: list[dict[str, Any]]) -> str:
    material = [
        {
            "skill": source.get("skill"),
            "state": source.get("state"),
            "source_path": source.get("source_path"),
            "source_sha256": source.get("source_sha256"),
            "result_count": source.get("result_count"),
            "trade_date": source.get("trade_date"),
        }
        for source in sources
    ]
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()[:16]


def _matched_files(patterns: Iterable[tuple[Path, str]], exclusions: Iterable[str]) -> list[Path]:
    excluded = tuple(item.casefold() for item in exclusions)
    matches: dict[str, Path] = {}
    for root, pattern in patterns:
        if not root.is_dir():
            continue
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            folded = path.name.casefold()
            if any(token in folded for token in excluded):
                continue
            matches[str(path.resolve()).casefold()] = path.resolve()
    return list(matches.values())


def _latest_path(spec: dict[str, Any]) -> tuple[Path | None, bool]:
    exclusions = spec.get("exclude", ())
    primary = _matched_files(spec.get("primary", ()), exclusions)
    if primary:
        return max(primary, key=lambda item: item.stat().st_mtime_ns), False
    fallback = _matched_files(spec.get("fallback", ()), exclusions)
    if fallback:
        return max(fallback, key=lambda item: item.stat().st_mtime_ns), True
    return None, False


def source_watch_signature() -> str:
    """Return a cheap signature for the currently selected allowlisted result files."""
    material: list[dict[str, Any]] = []
    for spec in SOURCE_SPECS:
        path, fallback = _latest_path(spec)
        entry: dict[str, Any] = {
            "skill": spec["skill"],
            "path": str(path) if path else None,
            "fallback": fallback,
        }
        if path is not None:
            try:
                stat = path.stat()
                entry.update({"size": stat.st_size, "mtime_ns": stat.st_mtime_ns})
            except OSError:
                entry.update({"size": None, "mtime_ns": None, "unavailable": True})
        material.append(entry)
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()[:16]


def _read_source(path: Path) -> Any:
    if path.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError(f"source_too_large:{path.stat().st_size}")
    if path.suffix.casefold() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    return json.loads(path.read_text(encoding="utf-8"))


def _dig(payload: Any, *keys: str) -> Any:
    value = payload
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _date_text(value: Any) -> str | None:
    if isinstance(value, (int, float)):
        value = str(int(value))
    if not isinstance(value, str):
        return None
    digits = re.sub(r"[^0-9]", "", value)
    if len(digits) >= 8 and digits[:4] in {"2024", "2025", "2026", "2027"}:
        return digits[:8]
    return None


def _source_trade_date(payload: Any, path: Path, records: list[dict[str, Any]]) -> str | None:
    candidates = []
    if isinstance(payload, dict):
        candidates.extend(
            (
                payload.get("trade_date"),
                payload.get("latest_trade_date"),
                payload.get("target_trade_date"),
                payload.get("requested_date"),
                payload.get("date"),
                _dig(payload, "data_cache", "trade_date"),
                _dig(payload, "facts", "trade_date"),
                _dig(payload, "run", "trade_date"),
            )
        )
    record_dates = [_date_text(row.get("signal_date") or row.get("trade_date")) for row in records]
    valid_record_dates = [item for item in record_dates if item]
    for value in candidates:
        normalized = _date_text(value)
        if normalized:
            return normalized
    if valid_record_dates:
        return max(valid_record_dates)
    path_dates = re.findall(r"20(?:24|25|26|27)[01][0-9][0-3][0-9]", str(path))
    return max(path_dates) if path_dates else None


def _generated_at(payload: Any, path: Path) -> str:
    if isinstance(payload, dict):
        for key in ("generated_at", "checked_at", "created_at", "finished_at"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")


def _score_value(row: dict[str, Any]) -> float | int | str | None:
    for key in ("final_score", "score", "preliminary_score", "quality_track_score", "chan_strength"):
        value = row.get(key)
        if isinstance(value, dict):
            value = value.get("total")
        if isinstance(value, (int, float)):
            return round(float(value), 2)
        if isinstance(value, str) and value.strip():
            try:
                return round(float(value), 2)
            except ValueError:
                return value.strip()[:40]
    return None


def _normal_symbol(value: Any) -> str:
    text = str(value or "").strip().upper()
    if re.fullmatch(r"\d{6}\.(SH|SZ|BJ)", text):
        return text
    match = re.search(r"(?<!\d)(\d{6})(?!\d)", text)
    if not match:
        return text[:32]
    code = match.group(1)
    market = "SH" if code.startswith(("5", "6", "9")) else "BJ" if code.startswith(("4", "8")) else "SZ"
    return f"{code}.{market}"


def _reason_text(row: dict[str, Any]) -> str:
    for key in ("conclusion", "rationale", "buy_type", "role", "grade", "review_reasons", "invalidation", "strategy"):
        value = row.get(key)
        if isinstance(value, list):
            value = "；".join(str(item) for item in value[:3])
        if isinstance(value, str) and value.strip():
            return value.strip()[:140]
    return "读取已落盘结果"


def _global_score_contract_sha256() -> str | None:
    try:
        return hashlib.sha256(GLOBAL_SCORE_CONTRACT.read_bytes()).hexdigest()
    except OSError:
        return None


def _verified_short_term_score_row(row: dict[str, Any], contract_sha256: str) -> bool:
    contract = row.get("score_contract", {})
    factors = row.get("positive_dimensions")
    if not isinstance(factors, list):
        factors = row.get("dimension_scores")
    risks = row.get("risks")
    if not isinstance(risks, list):
        risks = row.get("risk_items")
    hard_exclusions = row.get("hard_exclusions")
    return (
        isinstance(contract, dict)
        and contract.get("version") == SCORE_CONTRACT_VERSION
        and contract.get("global_contract_sha256") == contract_sha256
        and contract.get("fundamental_positive_weight") == 0
        and isinstance(factors, list) and len(factors) == 26
        and isinstance(risks, list) and len(risks) == 15
        and isinstance(hard_exclusions, list) and len(hard_exclusions) == 7
    )


def _normalize_record(
    skill: str,
    skill_name: str,
    row: dict[str, Any],
    tier: str,
    entity_type: str,
    source_trade_date: str | None = None,
) -> dict[str, Any]:
    symbol = _normal_symbol(row.get("symbol") or row.get("code") or row.get("stock_code") or row.get("leader_code"))
    name = str(row.get("name") or row.get("stock_name") or row.get("leader_name") or row.get("sector") or row.get("mainline") or "未命名").strip()
    strategy = str(row.get("strategy") or row.get("buy_type") or row.get("role") or row.get("sector") or row.get("mainline") or "").strip()
    signal_date = _date_text(row.get("signal_date") or row.get("trade_date") or source_trade_date)
    rank = row.get("rank") or row.get("enriched_rank") or row.get("preliminary_rank") or row.get("rank_in_type")
    stable = f"{skill}|{tier}|{entity_type}|{symbol}|{name}|{strategy}|{rank}"
    return {
        "id": hashlib.sha256(stable.encode("utf-8")).hexdigest()[:16],
        "skill": skill,
        "skill_name": skill_name,
        "tier": tier,
        "entity_type": entity_type,
        "symbol": symbol,
        "name": name,
        "strategy": strategy,
        "score": _score_value(row),
        "rank": rank,
        "signal_date": signal_date,
        "reason": _reason_text(row),
    }


def _raw_records(skill: str, payload: Any, fallback_source: bool) -> tuple[list[tuple[dict[str, Any], str, str]], str | None]:
    if fallback_source and skill == "a-share-limit-up-mining":
        return [], "blocked"
    if skill == "a-share-15d-selection":
        contract_sha256 = _global_score_contract_sha256()
        rows = [row for row in _as_list(_dig(payload, "top5")) if isinstance(row, dict)]
        if (
            not contract_sha256
            or _dig(payload, "source", "score_contract_sha256") != contract_sha256
            or not rows
            or not all(_verified_short_term_score_row(row, contract_sha256) for row in rows)
        ):
            return [], "blocked"
        return [(row, "selected", "stock") for row in rows], None
    if skill == "a-share-bottom-fishing":
        return [(row, "selected", "stock") for row in _as_list(payload) if isinstance(row, dict)], None
    if skill in {"a-share-limit-up-leader-classification", "a-share-limit-up-mining", "feilong-strategy"}:
        rows = _as_list(_dig(payload, "candidates")) or _as_list(_dig(payload, "selected_candidates")) or _as_list(_dig(payload, "top10"))
        return [(row, "selected", "stock") for row in rows if isinstance(row, dict)], None
    if skill == "buzhang-leader-mining":
        tier = "watch" if str(_dig(payload, "status") or "").upper() in {"OBSERVE", "WATCH"} else "selected"
        return [(row, tier, "stock") for row in _as_list(_dig(payload, "candidates")) if isinstance(row, dict)], None
    if skill == "chanlun-first-board":
        return [(row, "selected", "stock") for row in _as_list(payload) if isinstance(row, dict)], None
    if skill == "dragon-pullback":
        selected = [(row, "selected", "stock") for row in _as_list(_dig(payload, "selection", "technical_trade_ready_candidates")) if isinstance(row, dict)]
        watch = [(row, "watch", "stock") for row in _as_list(_dig(payload, "selection", "practical_candidates")) if isinstance(row, dict)]
        return selected + watch, None
    if skill == "five-dimension-resonance":
        contract_sha256 = _global_score_contract_sha256()
        rows = [row for row in _as_list(_dig(payload, "top3")) if isinstance(row, dict)]
        handoff = _dig(payload, "short_term_score")
        if (
            not contract_sha256
            or not isinstance(handoff, dict)
            or handoff.get("status") != "CLEAN_PASS"
            or handoff.get("version") != SCORE_CONTRACT_VERSION
            or handoff.get("global_contract_sha256") != contract_sha256
            or handoff.get("fundamental_positive_weight") != 0
            or not rows
            or not all(_verified_short_term_score_row(row, contract_sha256) for row in rows)
        ):
            return [], "blocked"
        return [(row, "selected", "stock") for row in rows], None
    if skill == "four-strategy-system":
        is_diagnostic = "smoke" in str(_dig(payload, "generated_at") or "").casefold() or bool(_dig(payload, "fallback_used")) or "FALLBACK" in str(_dig(payload, "status") or "").upper()
        if is_diagnostic:
            return [], "diagnostic"
        return [(row, "selected", "stock") for row in _as_list(_dig(payload, "rows")) if isinstance(row, dict)], None
    if skill == "golden-ignition":
        candidates = _as_list(_dig(payload, "candidates"))
        a_share = [row for row in candidates if isinstance(row, dict) and re.search(r"\d{6}", str(row.get("symbol") or row.get("code") or ""))]
        if not a_share and isinstance(_dig(payload, "quotes"), dict):
            return [], "wrong_target"
        return [(row, "selected", "stock") for row in a_share], None
    if skill == "hotspot-leader":
        rows = []
        for rank, item in enumerate(_as_list(_dig(payload, "top_sectors")), start=1):
            if not isinstance(item, dict):
                continue
            stocks = _as_list(item.get("stocks"))
            rows.append(
                (
                    {
                        "name": item.get("sector"),
                        "sector": item.get("sector"),
                        "score": item.get("count"),
                        "rank": rank,
                        "rationale": f"涨停 {item.get('count', 0)} 家：{'、'.join(str(stock) for stock in stocks[:4])}",
                    },
                    "theme",
                    "theme",
                )
            )
        return rows, None
    if skill == "limit-up-review":
        if fallback_source or not isinstance(payload, dict) or "watchlist" not in payload:
            return [], "diagnostic"
        return [(row, "watch", "stock") for row in _as_list(payload.get("watchlist")) if isinstance(row, dict)], None
    if skill == "nana-teacher-five-strategies":
        rows = []
        summaries = _dig(payload, "strategy_summary")
        if isinstance(summaries, dict):
            for strategy_name, summary in summaries.items():
                current = _dig(summary, "current_top20")
                for item in _as_list(current):
                    if isinstance(item, dict):
                        row = dict(item)
                        row.setdefault("strategy", strategy_name)
                        rows.append((row, "selected", "stock"))
        return rows, None
    if skill == "oversold-first-board":
        if bool(_dig(payload, "fallback_used")) or "smoke" in str(_dig(payload, "notes") or "").casefold():
            return [], "diagnostic"
        candidate = _dig(payload, "candidate")
        return ([(candidate, "selected", "stock")] if isinstance(candidate, dict) else []), None
    if skill == "quality-track-stock-selection":
        selected = [(row, "selected", "stock") for row in _as_list(_dig(payload, "selected_candidates")) if isinstance(row, dict)]
        watch = [(row, "watch", "stock") for row in _as_list(_dig(payload, "watch_candidates")) if isinstance(row, dict)]
        return selected + watch, None
    if skill == "quant-strategy-bundle-chen":
        if "FIXTURE" in str(_dig(payload, "mode") or "").upper() or _dig(payload, "fixture_boundary"):
            return [], "diagnostic"
        return [(row, "selected", "stock") for row in _as_list(_dig(payload, "candidates")) if isinstance(row, dict)], None
    if skill == "shortline-hotspot-mining":
        rows = []
        for item in _as_list(_dig(payload, "candidates")):
            if not isinstance(item, dict) or not isinstance(item.get("row"), dict):
                continue
            source = dict(item["row"])
            source["score"] = _dig(item, "score", "total")
            source["rank"] = item.get("rank")
            source["symbol"] = source.get("leader_code")
            leader_name = str(source.get("leader_name") or "").strip()
            source["name"] = leader_name if leader_name and leader_name != str(source.get("leader_code")) else f"{source.get('name', '板块')} 龙头"
            source["strategy"] = source.get("name")
            source["rationale"] = f"板块涨幅 {source.get('pct_change', '--')}% · 涨停 {source.get('limit_up_count', 0)} 家"
            rows.append((source, "theme", "theme"))
        return rows, None
    return [], "diagnostic"


def _source_note(state: str, payload: Any, records: list[dict[str, Any]], original_status: str | None) -> str:
    if state == "missing":
        return "尚未发现可消费的持久化业务结果"
    if state == "blocked":
        failures = _as_list(_dig(payload, "failures"))
        if failures and isinstance(failures[0], dict):
            return f"业务运行被阻断：{str(failures[0].get('message') or '数据源失败')[:90]}"
        return "业务运行被阻断，未生成候选"
    if state == "diagnostic":
        return "当前落盘文件仅为自检、预检或回退样本，已禁止进入候选表"
    if state == "wrong_target":
        return "当前落盘结果目标不是A股，已禁止进入候选表"
    if state == "empty":
        return "业务结果有效，本次严格条件下候选为0"
    if state == "observation":
        return "仅有观察项或主题结果，不等同于可交易候选"
    if records:
        return f"已读取 {len(records)} 条落盘结果；原始状态 {original_status or '未标注'}"
    return "已读取持久化业务结果"


def _build_source(spec: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    skill = spec["skill"]
    skill_name = spec["name"]
    installed = (SKILLS_ROOT / skill / "SKILL.md").is_file()
    path, fallback_source = _latest_path(spec)
    if path is None:
        source = {
            "skill": skill,
            "name": skill_name,
            "installed": installed,
            "state": "missing",
            "original_status": None,
            "trade_date": None,
            "generated_at": None,
            "freshness": "undated",
            "selected_count": 0,
            "watch_count": 0,
            "theme_count": 0,
            "result_count": 0,
            "source_file": None,
            "source_path": None,
            "source_size": None,
            "source_sha256": None,
            "note": "尚未发现可消费的持久化业务结果",
            "preview": [],
        }
        return source, []

    try:
        payload = _read_source(path)
        raw_records, forced_state = _raw_records(skill, payload, fallback_source)
        provisional_records = [item for item, _, _ in raw_records if isinstance(item, dict)]
        trade_date = _source_trade_date(payload, path, provisional_records)
        records = [
            _normalize_record(skill, skill_name, item, tier, entity_type, trade_date)
            for item, tier, entity_type in raw_records
            if isinstance(item, dict)
        ]
        selected_count = sum(1 for row in records if row["tier"] == "selected")
        watch_count = sum(1 for row in records if row["tier"] == "watch")
        theme_count = sum(1 for row in records if row["tier"] == "theme")
        if forced_state:
            state = forced_state
        elif selected_count:
            state = "available"
        elif watch_count or theme_count:
            state = "observation"
        else:
            state = "empty"
        original_status = None
        if isinstance(payload, dict):
            raw_status = payload.get("status") or payload.get("gate_status") or payload.get("current_state")
            original_status = str(raw_status) if raw_status is not None else None
        source = {
            "skill": skill,
            "name": skill_name,
            "installed": installed,
            "state": state,
            "original_status": original_status,
            "trade_date": trade_date,
            "generated_at": _generated_at(payload, path),
            "freshness": "undated",
            "selected_count": selected_count,
            "watch_count": watch_count,
            "theme_count": theme_count,
            "result_count": len(records),
            "source_file": path.name,
            "source_path": str(path),
            "source_size": path.stat().st_size,
            "source_sha256": file_sha256(path),
            "note": _source_note(state, payload, records, original_status),
            "preview": [{key: row[key] for key in ("symbol", "name", "tier")} for row in records[:4]],
        }
        return source, records
    except Exception as exc:
        source = {
            "skill": skill,
            "name": skill_name,
            "installed": installed,
            "state": "error",
            "original_status": None,
            "trade_date": None,
            "generated_at": None,
            "freshness": "undated",
            "selected_count": 0,
            "watch_count": 0,
            "theme_count": 0,
            "result_count": 0,
            "source_file": path.name,
            "source_path": str(path),
            "source_size": path.stat().st_size if path.is_file() else None,
            "source_sha256": file_sha256(path) if path.is_file() else None,
            "note": f"读取失败：{type(exc).__name__}: {exc}",
            "preview": [],
        }
        return source, []


def build_snapshot(snapshot_path: Path | None = None) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for spec in SOURCE_SPECS:
        source, records = _build_source(spec)
        sources.append(source)
        if source["state"] in {"available", "observation", "empty"}:
            candidates.extend(records)

    dated_business = [
        str(source["trade_date"])
        for source in sources
        if source["state"] in {"available", "observation", "empty"} and source.get("trade_date")
    ]
    latest_trade_date = max(dated_business) if dated_business else None
    for source in sources:
        trade_date = source.get("trade_date")
        if not trade_date or not latest_trade_date:
            source["freshness"] = "undated"
        elif trade_date == latest_trade_date:
            source["freshness"] = "latest"
        elif trade_date < latest_trade_date:
            source["freshness"] = "stale"
        else:
            source["freshness"] = "future"

    state_counts: dict[str, int] = {}
    for source in sources:
        state = str(source["state"])
        state_counts[state] = state_counts.get(state, 0) + 1

    payload = {
        "schema": SCHEMA_VERSION,
        "status": "PASS",
        "generated_at": now_iso(),
        "data_fingerprint": source_fingerprint(sources),
        "dynamic_policy": "rescan_allowlisted_skill_outputs_on_every_api_request",
        "auto_refresh_seconds": 60,
        "realtime_transport": "server_sent_events",
        "change_detection_interval_ms": 350,
        "latest_trade_date": latest_trade_date,
        "risk_notice": "仅展示本机技能已落盘结果，不构成投资建议；结果可能过期，空候选和诊断文件不会被包装成选股结论。",
        "source_policy": "explicit_allowlist_persisted_business_results_only",
        "summary": {
            "audited_skill_count": len(SOURCE_SPECS),
            "business_result_skill_count": sum(1 for source in sources if source["state"] in {"available", "observation", "empty"}),
            "selected_candidate_count": sum(1 for row in candidates if row["tier"] == "selected"),
            "watch_candidate_count": sum(1 for row in candidates if row["tier"] == "watch"),
            "theme_result_count": sum(1 for row in candidates if row["tier"] == "theme"),
            "problem_skill_count": sum(1 for source in sources if source["state"] in {"blocked", "missing", "diagnostic", "wrong_target", "error"}),
            "state_counts": state_counts,
        },
        "sources": sources,
        "candidates": candidates,
        "snapshot_path": str(snapshot_path) if snapshot_path else None,
    }
    if snapshot_path is not None:
        atomic_write_json(snapshot_path, payload)
    return payload
