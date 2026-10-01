#!/usr/bin/env python3
"""Deterministic market-layer scan for the unified short-term hotspot skill."""
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
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

_app_scripts_dir = str(Path(__file__).resolve().parents[5] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_data_root, resolve_tdx_root

from tdx_sector_pct import sector_pct_from_tdx

GLOBAL_SCRIPTS = Path(__file__).resolve().parents[5] / "scripts"
if str(GLOBAL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(GLOBAL_SCRIPTS))

from industry_data_router import AllIndustrySourcesFailed, fetch_industry_snapshot

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
REPORTS = resolve_data_root() / "reports" / "skills" / "shortline-hotspot-mining"
BLOCKNEW_CANDIDATES = (resolve_tdx_root() / "T0002" / "blocknew",)
SOURCE_LABELS = {
    "tdx_local": "本地通达信",
    "akshare.stock_sector_spot:新浪行业": "新浪行业行情",
    "akshare.stock_board_industry_name_em": "东方财富行业行情",
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def find_blocknew() -> Path | None:
    return next((path for path in BLOCKNEW_CANDIDATES if path.is_dir()), None)


def extract_codes(text: str) -> list[str]:
    codes: list[str] = []
    for line in text.splitlines():
        match = re.search(r"(?<!\d)(\d{6})(?!\d)", line.strip())
        if match:
            codes.append(match.group(1))
            continue
        digits = "".join(char for char in line if char.isdigit())
        if len(digits) in (6, 7):
            codes.append(digits[-6:])
    return list(dict.fromkeys(codes))


def load_block_name_map(blocknew: Path) -> tuple[dict[str, str], dict]:
    cfg_path = blocknew / "blocknew.cfg"
    if not cfg_path.is_file():
        return {}, {"status": "FAIL", "path": str(cfg_path), "reason": "blocknew.cfg missing"}
    try:
        raw = cfg_path.read_bytes()
    except OSError as exc:
        return {}, {"status": "FAIL", "path": str(cfg_path), "reason": str(exc)}

    names: dict[str, str] = {}
    record_size = 120
    for offset in range(0, len(raw) - record_size + 1, record_size):
        record = raw[offset : offset + record_size]
        name = record[:50].split(b"\x00", 1)[0].decode("gbk", errors="ignore").strip()
        alias = record[50:].split(b"\x00", 1)[0].decode("gbk", errors="ignore").strip()
        if name and alias:
            names[alias.casefold()] = name
    return names, {"status": "PASS" if names else "FAIL", "path": str(cfg_path), "registered_count": len(names)}


def load_stock_name_map(hq_cache: Path) -> tuple[dict[str, str], dict]:
    names: dict[str, str] = {}
    loaded_files: list[str] = []
    failures: list[str] = []
    for filename in ("shs.tnf", "szs.tnf", "bjs.tnf"):
        path = hq_cache / filename
        if not path.is_file():
            failures.append(f"{filename}:missing")
            continue
        try:
            text = path.read_bytes().decode("gbk", errors="ignore")
        except OSError as exc:
            failures.append(f"{filename}:{exc}")
            continue
        loaded_files.append(str(path))
        for match in re.finditer(r"(\d{6})\x00{2,}([^\x00]{2,16})", text):
            code, stock_name = match.group(1), match.group(2).strip()
            if stock_name and code not in names:
                names[code] = stock_name
    return names, {
        "status": "PASS" if names else "FAIL",
        "path": str(hq_cache),
        "security_count": len(names),
        "loaded_files": loaded_files,
        "failures": failures,
    }


def source_label(source: object) -> str:
    raw = str(source or "").strip()
    return SOURCE_LABELS.get(raw, raw)


def load_local_blocks(limit: int) -> tuple[list[dict], dict]:
    blocknew = find_blocknew()
    if blocknew is None:
        return [], {"status": "FAIL", "reason": "TDX blocknew directory missing", "attempted": [str(p) for p in BLOCKNEW_CANDIDATES]}
    block_names, cfg_status = load_block_name_map(blocknew)
    if not block_names:
        return [], cfg_status
    blocks: list[dict] = []
    failures: list[str] = []
    skipped_unregistered: list[str] = []
    for path in sorted(blocknew.glob("*.blk"))[:limit]:
        block_name = block_names.get(path.stem.casefold())
        if not block_name:
            skipped_unregistered.append(path.name)
            continue
        try:
            raw = path.read_text(encoding="gbk", errors="ignore")
            codes = extract_codes(raw)
        except OSError as exc:
            failures.append(f"{path.name}:{exc}")
            continue
        if codes:
            blocks.append({"name": block_name, "codes": codes, "member_count": len(codes), "block_path": str(path)})
    return blocks, {
        "status": "PASS" if blocks else "FAIL",
        "path": str(blocknew),
        "config": cfg_status,
        "block_count": len(blocks),
        "read_failures": failures,
        "unregistered_blocks_skipped": skipped_unregistered,
    }


def scan_local_blocks(blocks: list[dict], stock_names: dict[str, str]) -> list[dict]:
    rows: list[dict] = []
    for block in blocks:
        snapshot = sector_pct_from_tdx(block["codes"])
        if snapshot is None:
            continue
        leader_code = snapshot["leader_code"]
        leader_name = stock_names.get(leader_code, "")
        rows.append({
            "name": block["name"],
            "source": source_label("tdx_local"),
            "latest_date": snapshot["latest_date"],
            "pct_change": snapshot["pct_change"],
            "median_pct": snapshot["median_pct"],
            "top5_mean_pct": snapshot["top5_mean_pct"],
            "leader_code": leader_code,
            "leader_name": leader_name,
            "leader_display": f"{leader_name}（{leader_code}）" if leader_name else leader_code,
            "leader_pct": snapshot["leader_pct"],
            "limit_up_count": snapshot["limit_up_count"],
            "up_count": snapshot["up_count"],
            "down_count": snapshot["down_count"],
            "up_ratio": snapshot["up_ratio"],
            "member_count": block["member_count"],
            "coverage_count": snapshot["coverage_count"],
            "coverage_ratio": round(snapshot["coverage_count"] / max(1, block["member_count"]), 4),
            "local_codes": block["codes"],
            "sample_paths": snapshot["sample_paths"],
            "needs_tdx_confirmation": False,
        })
    return rows


def load_public_industry_crosscheck() -> tuple[list[dict], dict]:
    return fetch_industry_snapshot()


def parse_date(value: object) -> date | None:
    text = str(value).strip()
    match = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", text)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def verify_news(symbol: str, trade_date: date) -> dict:
    empty = {"fresh_news_count": 0, "top_title": "", "published_at": None, "source": None}
    if not re.fullmatch(r"\d{6}", symbol):
        return empty
    try:
        import akshare as ak
        frame = ak.stock_news_em(symbol=symbol)
    except Exception:
        return empty
    fresh: list[dict] = []
    for _, item in frame.head(20).iterrows():
        published = next((parse_date(item.get(key)) for key in ("发布时间", "新闻时间", "日期", "时间") if item.get(key) is not None), None)
        if published is None or published > trade_date or (trade_date - published).days > 1:
            continue
        title = str(item.get("新闻标题", item.get("标题", ""))).strip()
        if title:
            fresh.append({"title": title[:100], "published": published.isoformat()})
    if not fresh:
        return empty
    return {
        "fresh_news_count": len(fresh),
        "top_title": fresh[0]["title"],
        "published_at": fresh[0]["published"],
        "source": "akshare.stock_news_em",
    }


def market_score(row: dict, news: dict) -> dict:
    pct = float(row.get("pct_change") or 0)
    if pct >= 5:
        pct_score = 30
    elif pct >= 3:
        pct_score = 24
    elif pct >= 1:
        pct_score = 18
    elif pct >= 0:
        pct_score = 12
    else:
        pct_score = max(0, round(6 + pct, 2))

    leader_pct = float(row.get("leader_pct") or 0)
    leader_part = 18 if leader_pct >= 9.5 else 12 if leader_pct >= 5 else 8 if leader_pct >= 2 else 0
    limit_count = row.get("limit_up_count")
    up_ratio = float(row.get("up_ratio") or 0)
    if isinstance(limit_count, int) and limit_count >= 2:
        breadth_part = 12
    elif isinstance(limit_count, int) and limit_count == 1:
        breadth_part = 8
    elif up_ratio >= 0.75:
        breadth_part = 10
    elif up_ratio >= 0.6:
        breadth_part = 6
    else:
        breadth_part = 0
    leader_score = min(30, leader_part + breadth_part)

    members = int(row.get("coverage_count") or row.get("member_count") or 0)
    scale_score = 20 if members >= 10 else 15 if members >= 5 else 10 if members >= 3 else 5
    fresh_news = int(news.get("fresh_news_count") or 0)
    event_score = 20 if fresh_news >= 3 else 14 if fresh_news >= 1 else 0
    return {
        "sector_change": pct_score,
        "leader_breadth": leader_score,
        "scale": scale_score,
        "event_validation": event_score,
        "total": round(pct_score + leader_score + scale_score + event_score, 2),
    }


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, mode: str, trade_date: str, scored: list[dict], audit: dict) -> None:
    data_dates = audit["sources"]["tdx_kline"].get("latest_dates", [])
    data_cutoff = ", ".join(data_dates) if data_dates else "未取得"
    lines = [
        f"# 短线热点挖掘市场扫描层（请求日期 {trade_date}）",
        "",
        f"- 模式：{mode}",
        f"- 生成时间：{now_iso()}",
        f"- 本地 TDX 数据截止：{data_cutoff}",
        "- 定位：本文件只证明市场异动层；完整/发现模式仍需补齐政策、产业、资金、舆情和反向证据。",
        "- 研究边界：不构成投资建议。",
        "",
        "## 市场强度 Top 10",
        "",
        "| 排名 | 板块 | 分数 | 等权涨幅 | 领涨 | 广度 | 来源 |",
        "|---:|---|---:|---:|---|---:|---|",
    ]
    for item in scored[:10]:
        row = item["row"]
        lines.append(
            f"| {item['rank']} | {row['name']} | {item['score']['total']:.2f} | "
            f"{float(row.get('pct_change') or 0):+.2f}% | {row.get('leader_display') or row.get('leader_name') or '-'} "
            f"({float(row.get('leader_pct') or 0):+.2f}%) | {float(row.get('up_ratio') or 0):.1%} | {row['source']} |"
        )
    lines += [
        "",
        "## 数据缺口与降级",
        "",
        f"- TDX 板块池：{audit['sources']['tdx_blocks']['status']}",
        f"- 公开行业交叉校验：{audit['sources']['public_industry']['status']}",
        "- 远程行业行仅作交叉校验，未完成 TDX 映射前不得进入强结论。",
        "- 新闻验证仅在能解析到 6 位领涨代码且发布时间距目标交易日不超过 1 天时计分。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="短线热点挖掘本地市场扫描")
    parser.add_argument("--mode", choices=("full", "discovery", "daily"), default="full")
    parser.add_argument("--date", default=date.today().strftime("%Y%m%d"), help="目标交易日 YYYYMMDD")
    parser.add_argument("--out", help="输出目录")
    parser.add_argument("--manual-confirm", action="store_true")
    parser.add_argument("--offline-only", action="store_true", help="不调用 akshare 交叉校验或新闻")
    parser.add_argument("--top-news-verify", type=int, default=10)
    parser.add_argument("--max-local-blocks", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true", help="仅检查参数和入口，不读取市场数据")
    args = parser.parse_args()

    if args.dry_run:
        print(json.dumps({"status": "PASS", "skill": ROOT.name, "mode": args.mode, "dry_run": True}, ensure_ascii=False, indent=2))
        return 0
    if not args.manual_confirm:
        print(json.dumps({"status": "BLOCKED", "reason": "missing --manual-confirm"}, ensure_ascii=False), file=sys.stderr)
        return 2
    if os.environ.get("OPENCLAW_CRON_RUN") == "1" or os.environ.get("OPENCLAW_AUTO_TRIGGER") == "1":
        print(json.dumps({"status": "BLOCKED", "reason": "automatic trigger is forbidden"}, ensure_ascii=False), file=sys.stderr)
        return 2
    if not re.fullmatch(r"20\d{6}", args.date):
        print(json.dumps({"status": "BLOCKED", "reason": "--date must be YYYYMMDD"}, ensure_ascii=False), file=sys.stderr)
        return 2
    if args.mode == "full" and args.offline_only:
        print(json.dumps({
            "status": "BLOCKED",
            "reason": "full mode requires a verified public-industry source; --offline-only is forbidden",
        }, ensure_ascii=False), file=sys.stderr)
        return 2
    trade_date = date(int(args.date[:4]), int(args.date[4:6]), int(args.date[6:]))
    output = Path(args.out) if args.out else REPORTS / f"{args.date}_shortline_hotspot_mining"
    output.mkdir(parents=True, exist_ok=True)

    audit = {
        "skill": ROOT.name,
        "mode": args.mode,
        "requested_date": args.date,
        "generated_at": now_iso(),
        "sources": {},
        "warnings": [],
        "outputs": {},
    }
    blocks, block_status = load_local_blocks(max(1, args.max_local_blocks))
    audit["sources"]["tdx_blocks"] = block_status
    hq_cache = find_blocknew().parent / "hq_cache" if find_blocknew() else Path()
    stock_names, stock_name_status = load_stock_name_map(hq_cache)
    audit["sources"]["tdx_security_names"] = stock_name_status
    local_rows = scan_local_blocks(blocks, stock_names)
    audit["sources"]["tdx_kline"] = {
        "status": "PASS" if local_rows else "FAIL",
        "candidate_count": len(local_rows),
        "latest_dates": sorted({row["latest_date"] for row in local_rows}),
    }
    if not local_rows:
        audit["status"] = "BLOCKED"
        audit["reason"] = "no TDX candidate has readable current daily bars"
        audit_path = output / "audit.json"
        audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": "BLOCKED", "audit": str(audit_path)}, ensure_ascii=False, indent=2))
        return 3

    latest_dates = audit["sources"]["tdx_kline"]["latest_dates"]
    if latest_dates != [trade_date.isoformat()]:
        audit["warnings"].append({
            "code": "TDX_DATE_DIFFERS_FROM_REQUEST",
            "requested_date": trade_date.isoformat(),
            "actual_latest_dates": latest_dates,
            "effect": "market scan is a prior-close or mixed-date snapshot, not a complete requested-date close",
        })

    remote_rows: list[dict] = []
    if args.offline_only:
        audit["sources"]["public_industry"] = {"status": "SKIPPED", "reason": "--offline-only"}
    else:
        try:
            remote_rows, remote_status = load_public_industry_crosscheck()
            for row in remote_rows:
                row["source"] = source_label(row.get("source"))
                if not row.get("leader_display"):
                    row["leader_display"] = row.get("leader_name") or row.get("leader_code") or ""
            audit["sources"]["public_industry"] = remote_status
        except AllIndustrySourcesFailed as exc:
            audit["sources"]["public_industry"] = {
                "status": "FAIL",
                "reason": str(exc),
                "attempts": exc.attempts,
            }
            audit["status"] = "BLOCKED"
            audit["reason"] = "full public-industry failover exhausted without real rows"
            audit_path = output / "audit.json"
            audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"status": "BLOCKED", "audit": str(audit_path)}, ensure_ascii=False, indent=2))
            return 4

    rows = local_rows + remote_rows
    news_budget = max(0, args.top_news_verify)
    scored: list[dict] = []
    for row in rows:
        news = {"fresh_news_count": 0, "top_title": "", "published_at": None, "source": None}
        if not args.offline_only and news_budget > 0 and row["source"] == source_label("tdx_local") and row.get("leader_code"):
            news = verify_news(row["leader_code"], trade_date)
            news_budget -= 1
        scored.append({"row": row, "news": news, "score": market_score(row, news)})
    scored.sort(key=lambda item: (-item["score"]["total"], -float(item["row"].get("pct_change") or 0)))
    for rank, item in enumerate(scored, 1):
        item["rank"] = rank

    candidate_rows = []
    score_rows = []
    for item in scored:
        row, score, news = item["row"], item["score"], item["news"]
        candidate_rows.append({
            "rank": item["rank"], "name": row["name"], "source": row["source"],
            "latest_date": row["latest_date"], "pct_change": row["pct_change"],
            "leader_name": row["leader_name"], "leader_code": row.get("leader_code", ""),
            "leader_display": row.get("leader_display") or row["leader_name"], "leader_pct": row["leader_pct"],
            "limit_up_count": row["limit_up_count"], "up_ratio": row["up_ratio"],
            "member_count": row["member_count"], "coverage_count": row["coverage_count"],
            "coverage_ratio": row["coverage_ratio"], "needs_tdx_confirmation": row["needs_tdx_confirmation"],
        })
        score_rows.append({
            "rank": item["rank"], "name": row["name"],
            "sector_change": score["sector_change"], "leader_breadth": score["leader_breadth"],
            "scale": score["scale"], "event_validation": score["event_validation"],
            "market_intensity_total": score["total"], "fresh_news_count": news["fresh_news_count"],
        })

    candidate_path = output / "candidate_pool.csv"
    score_path = output / "market_scan_score.csv"
    scan_path = output / "market_scan.json"
    report_path = output / "report.md"
    audit_path = output / "audit.json"
    manifest_path = output / "run_manifest.json"
    write_csv(candidate_path, candidate_rows, list(candidate_rows[0]))
    write_csv(score_path, score_rows, list(score_rows[0]))
    scan_payload = {
        "mode": args.mode,
        "requested_date": args.date,
        "generated_at": now_iso(),
        "score_role": "market-intensity pre-screen only; do not add to five-dimension final score",
        "candidates": scored,
    }
    scan_path.write_text(json.dumps(scan_payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    audit["status"] = "PASS"
    audit["candidate_count"] = len(scored)
    audit["local_candidate_count"] = len(local_rows)
    audit["remote_crosscheck_count"] = len(remote_rows)
    audit["outputs"] = {"candidate_pool": str(candidate_path), "market_score": str(score_path), "market_scan": str(scan_path), "report": str(report_path), "audit": str(audit_path), "manifest": str(manifest_path)}
    write_report(report_path, args.mode, args.date, scored, audit)
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "skill": ROOT.name,
        "mode": args.mode,
        "requested_date": args.date,
        "generated_at": now_iso(),
        "status": "MARKET_SCAN_COMPLETE",
        "data_dates": audit["sources"]["tdx_kline"]["latest_dates"],
        "warnings": audit["warnings"],
        "requires_research_completion": args.mode in ("full", "discovery"),
        "top_candidates": [
            {"rank": item["rank"], "name": item["row"]["name"], "market_intensity": item["score"]["total"], "source": item["row"]["source"]}
            for item in scored[:10]
        ],
        "outputs": audit["outputs"],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "mode": args.mode,
        "output_dir": str(output),
        "local_candidates": len(local_rows),
        "crosscheck_candidates": len(remote_rows),
        "top": manifest["top_candidates"][:5],
        "manifest": str(manifest_path),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
