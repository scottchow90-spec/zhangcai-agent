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
import datetime as dt
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]


def runtime_home(skill_dir: Path) -> Path:
    return skill_dir.parent


CODEX_HOME = runtime_home(SKILL_DIR)
SHORTLINE = CODEX_HOME / "shortline-hotspot-mining" / "scripts" / "codex_entry.py"
LIMITUP = CODEX_HOME / "a-share-limit-up-mining" / "scripts" / "codex_entry.py"
TDX_FORMULA = SKILL_DIR / "scripts" / "tdx_formula.py"
RESEARCH_SCHEMA = "BUZHANG-CANDIDATE-RESEARCH-V1"
HARD_RISK_KEYS = (
    "st_or_delisting",
    "suspension",
    "major_regulatory_action",
    "major_reduction_or_unlock",
    "major_financial_anomaly",
    "liquidity_anomaly",
)


def info() -> int:
    print(json.dumps({
        "skill": "buzhang-leader-mining",
        "display_name": "补涨龙头挖掘",
        "runtime": "Codex",
        "entry": str(Path(__file__).resolve()),
        "upstream": {
            "shortline": str(SHORTLINE),
            "limitup": str(LIMITUP),
            "hotspot_leader": str(SHORTLINE),
        },
        "output": "buzhang_result.json",
    }, ensure_ascii=False, indent=2))
    return 0


def selftest() -> int:
    required = [
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "references" / "spec.md",
        SHORTLINE,
        LIMITUP,
        TDX_FORMULA,
    ]
    missing = [str(p) for p in required if not p.is_file()]
    akshare_available = importlib.util.find_spec("akshare") is not None
    status = "PASS" if not missing and akshare_available else "BLOCKED"
    print(json.dumps({
        "status": status,
        "skill": "buzhang-leader-mining",
        "missing": missing,
        "akshare_available": akshare_available,
        "errors": [] if status == "PASS" else ["akshare dependency unavailable"] if not akshare_available else [],
    }, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


def latest_weekday() -> str:
    d = dt.date.today()
    if d.weekday() >= 5:
        d -= dt.timedelta(days=d.weekday() - 4)
    elif dt.datetime.now().strftime("%H%M") < "1505":
        d -= dt.timedelta(days=1)
        while d.weekday() >= 5:
            d -= dt.timedelta(days=1)
    return d.strftime("%Y%m%d")


def run_cmd(cmd: list[str], env: dict[str, str], timeout: int = 900) -> dict:
    try:
        p = subprocess.run(cmd, cwd=str(SKILL_DIR), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return {"ok": p.returncode == 0, "exit": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-2000:]}
    except Exception as exc:
        return {"ok": False, "exit": None, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}


def build_upstream_commands(trade_date: str, out: Path) -> dict[str, list[str]]:
    shortline_out = out / "shortline"
    limitup_out = out / "limitup"
    leader_out = out / "leader"
    return {
        "shortline": [
            sys.executable, str(SHORTLINE), "run", "--", "hotspot",
            "--date", trade_date,
            "--out", str(shortline_out),
        ],
        "limitup": [
            sys.executable, str(LIMITUP), "run", "--", "--mode", "daily",
            "--date", trade_date, "--manual-confirm", "--out", str(limitup_out),
        ],
        "hotspot_leader": [
            sys.executable, str(SHORTLINE), "run", "--", "leader",
            "--date", trade_date, "--out", str(leader_out),
        ],
    }


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def resolve_shortline_artifacts(steps: dict) -> dict[str, Path | None]:
    def canonical_payload(step_name: str) -> dict:
        raw = str((steps.get(step_name) or {}).get("stdout") or "").strip()
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    shortline_payload = canonical_payload("shortline")
    leader_payload = canonical_payload("hotspot_leader")
    manifest_value = str(shortline_payload.get("manifest_path") or "").strip()
    deliverables = (leader_payload.get("artifacts") or {}).get("deliverables") or {}
    leader_value = str(deliverables.get("leader_rank.csv") or "").strip()
    return {
        "manifest": Path(manifest_value) if manifest_value else None,
        "leader_rank": Path(leader_value) if leader_value else None,
    }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_research_evidence(raw_path: str | None, trade_date: str) -> dict:
    result = {"path": "", "sha256": "", "records": {}, "directions": {}, "errors": []}
    if not raw_path:
        result["errors"].append("research evidence missing")
        return result
    path = Path(raw_path).resolve()
    result["path"] = str(path)
    if not path.is_file():
        result["errors"].append(f"research evidence file missing: {path}")
        return result
    try:
        payload = read_json(path)
    except Exception as exc:
        result["errors"].append(f"research evidence unreadable: {type(exc).__name__}: {exc}")
        return result
    result["sha256"] = file_sha256(path)
    if payload.get("schema") != RESEARCH_SCHEMA:
        result["errors"].append("research evidence schema mismatch")
    if str(payload.get("trade_date") or "") != trade_date:
        result["errors"].append("research evidence trade date mismatch")
    if payload.get("status") != "PASS":
        result["errors"].append("research evidence status is not PASS")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        result["errors"].append("research evidence candidates must be a list")
        return result
    for record in candidates:
        if not isinstance(record, dict):
            continue
        code = str(record.get("code") or "").strip()
        mainline = str(record.get("mainline") or "").strip()
        if len(code) == 6 and mainline:
            result["records"][f"{mainline}|{code}"] = record
    direction_reviews = payload.get("direction_reviews")
    if not isinstance(direction_reviews, list):
        result["errors"].append("research evidence direction_reviews must be a list")
    else:
        for review in direction_reviews:
            if not isinstance(review, dict):
                continue
            mainline = str(review.get("mainline") or "").strip()
            if mainline:
                result["directions"][mainline] = review
    return result


def research_record_completeness_errors(record: dict | None, row: dict, mainline: str) -> list[str]:
    if not isinstance(record, dict):
        return ["逐股研究记录缺失"]
    errors = []
    if not isinstance(record.get("eligible"), bool):
        errors.append("候选资格结论缺失")
    if str(record.get("name") or "").strip() != str(row.get("name") or "").strip():
        errors.append("名称不一致")
    if str(record.get("mainline") or "").strip() != mainline:
        errors.append("主线不一致")
    for key, label in (
        ("direct_mapping", "直接题材映射缺失"),
        ("trigger", "当日触发证据缺失"),
        ("confirmation", "次日确认条件缺失"),
        ("invalidation", "失效条件缺失"),
        ("risk_conclusion", "风险结论缺失"),
    ):
        if not str(record.get(key) or "").strip():
            errors.append(label)
    evidence_ids = record.get("evidence_ids")
    if not isinstance(evidence_ids, list) or len({str(value).strip() for value in evidence_ids if str(value).strip()}) < 2:
        errors.append("独立证据不足2条")
    hard_checks = record.get("hard_risk_checks")
    if not isinstance(hard_checks, dict):
        errors.append("硬风险检查缺失")
    else:
        for key in HARD_RISK_KEYS:
            if key not in hard_checks:
                errors.append(f"硬风险字段缺失:{key}")
            elif not isinstance(hard_checks.get(key), bool):
                errors.append(f"硬风险字段不是布尔值:{key}")
    if record.get("eligible") is False and not record.get("exclusion_reasons"):
        errors.append("不合格候选缺少剔除原因")
    return errors


def research_record_errors(record: dict | None, row: dict, mainline: str) -> list[str]:
    errors = research_record_completeness_errors(record, row, mainline)
    if not isinstance(record, dict):
        return errors
    if record.get("eligible") is not True:
        reasons = record.get("exclusion_reasons") or []
        errors.append("候选不合格" + (f": {'；'.join(str(value) for value in reasons)}" if reasons else ""))
    hard_checks = record.get("hard_risk_checks") if isinstance(record.get("hard_risk_checks"), dict) else {}
    for key in HARD_RISK_KEYS:
        if hard_checks.get(key) is True:
            errors.append(f"硬风险命中:{key}")
    return errors


def cross_section_percentile(items: list[dict], field: str, target: dict) -> float:
    values = sorted(float(item.get(field) or 0) for item in items)
    if len(values) <= 1:
        return 1.0
    value = float(target.get(field) or 0)
    low = next(index for index, current in enumerate(values) if current >= value)
    high = len(values) - 1 - next(index for index, current in enumerate(reversed(values)) if current <= value)
    return ((low + high) / 2.0) / (len(values) - 1)


def build_dynamic_candidate(candidate: dict, pool: list[dict], sector: dict, zt_row: dict | None, record: dict) -> dict:
    flattened = []
    for item in pool:
        components = item.get("components") if isinstance(item.get("components"), dict) else {}
        flattened.append({
            "ladder": float(components.get("梯队质量") or 0),
            "capital": float(components.get("资金承接") or 0),
            "position": float(components.get("相对位置") or 0),
        })
    components = candidate.get("components") if isinstance(candidate.get("components"), dict) else {}
    current = {
        "ladder": float(components.get("梯队质量") or 0),
        "capital": float(components.get("资金承接") or 0),
        "position": float(components.get("相对位置") or 0),
    }
    score_breakdown = {
        "mainline_sync": round(25 * float(sector.get("dynamic_score") or 0) / 100, 4),
        "direct_mapping": 20.0,
        "ladder_quality": round(20 * cross_section_percentile(flattened, "ladder", current), 4),
        "capital_support": round(20 * cross_section_percentile(flattened, "capital", current), 4),
        "relative_position": round(10 * cross_section_percentile(flattened, "position", current), 4),
        "risk_execution": 5.0 if float(components.get("风险执行") or 0) > 0 else 0.0,
    }
    score = round(sum(score_breakdown.values()), 4)
    snapshot = candidate.get("market_snapshot") if isinstance(candidate.get("market_snapshot"), dict) else {}
    row = zt_row or {}
    code = str(candidate.get("stock_code") or "")[:6]
    return {
        "mainline": str(sector.get("sector") or ""),
        "code": code,
        "name": str(row.get("name") or record.get("name") or ""),
        "score": score,
        "score_breakdown": score_breakdown,
        "tdx_sort_key": candidate.get("score"),
        "tdx_components": components,
        "board_count": int(row.get("board_count") or 0),
        "first_limit_time": str(row.get("first_limit_time") or ""),
        "break_count": int(row.get("break_count") or 0),
        "turnover": row.get("turnover"),
        "amount": row.get("amount") if row else snapshot.get("amount"),
        "limit_capital": row.get("limit_capital") if row else 0,
        "close": snapshot.get("close"),
        "return_1d_pct": round(float(snapshot.get("return_1d") or 0) * 100, 4),
        "return_5d_pct": round(float(snapshot.get("return_5d") or 0) * 100, 4),
        "volume_ratio_5d": snapshot.get("volume_ratio_5d"),
        "amount_ratio_5d": snapshot.get("amount_ratio_5d"),
        "evidence_id": row.get("evidence_id") if row else f"{sector.get('trade_date')}:tdx_daily#{code}",
        "direct_mapping": record.get("direct_mapping"),
        "trigger": record.get("trigger"),
        "confirmation": record.get("confirmation"),
        "invalidation": record.get("invalidation"),
        "risk_flags": [],
        "risk_conclusion": record.get("risk_conclusion"),
        "research_evidence_ids": record.get("evidence_ids", []),
        "verification_status": "PASS",
    }


def read_limitup_rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_zt_rows(trade_date: str) -> list[dict]:
    try:
        import akshare as ak
        df = ak.stock_zt_pool_em(date=trade_date)
    except Exception:
        return []
    rows = []
    for _, r in df.iterrows():
        code = str(r.get("代码", "")).strip()
        name = str(r.get("名称", "")).strip()
        if len(code) != 6 or code.startswith(("4", "8", "9", "688")) or "ST" in name.upper() or "退" in name:
            continue
        rows.append({
            "code": code,
            "name": name,
            "board_count": int(r.get("连板数", 0) or 0),
            "first_limit_time": str(r.get("首次封板时间", "")),
            "break_count": int(r.get("炸板次数", 0) or 0),
            "turnover": float(r.get("换手率", 0) or 0),
            "amount": float(r.get("成交额", 0) or 0),
            "limit_capital": float(r.get("封板资金", 0) or 0),
            "industry": str(r.get("所属行业", "")),
            "evidence_id": f"{trade_date}:ak_zt_pool+ztc#{code}",
        })
    return rows


def score_catchup(row: dict, breadth: int) -> int:
    board = int(float(row.get("board_count") or 0))
    first = "".join(ch for ch in str(row.get("first_limit_time") or "") if ch.isdigit())
    breaks = int(float(row.get("break_count") or 0))
    turnover = float(row.get("turnover") or 0)
    amount = float(row.get("amount") or 0) / 1e8
    sync = min(25, breadth * 3 + (10 if board >= 2 else 5))
    ladder = 20 if first and first <= "100000" and breaks == 0 else 15 if first and first <= "110000" else 8
    capital = 20 if 1 <= amount <= 10 and 3 <= turnover <= 20 else 12 if amount >= 0.5 and turnover >= 2 else 5
    position = 10 if board == 1 else 6 if board == 2 else 0
    risk = 5 if breaks == 0 and turnover <= 20 else 2
    return min(100, sync + 20 + ladder + capital + position + risk)


def run(args: argparse.Namespace) -> int:
    if not args.manual_confirm:
        print(json.dumps({"status": "BLOCKED", "reason": "missing --manual-confirm"}, ensure_ascii=False))
        return 2
    trade_date = args.date or latest_weekday()
    today = dt.datetime.now().strftime("%Y%m%d")
    if trade_date >= today and dt.datetime.now().strftime("%H%M") < "1505":
        print(json.dumps({"status": "BLOCKED", "reason": "formal run requires after 15:05"}, ensure_ascii=False))
        return 2
    out = Path(args.out) if args.out else (SKILL_DIR / "runs" / trade_date)
    out.mkdir(parents=True, exist_ok=True)
    shortline_out = out / "shortline"
    limitup_out = out / "limitup"
    concept_out = out / "concept-rank"
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    commands = build_upstream_commands(trade_date, out)
    steps = {}
    steps["shortline"] = run_cmd(commands["shortline"], env)
    steps["limitup"] = run_cmd(commands["limitup"], env)
    steps["hotspot_leader"] = run_cmd(commands["hotspot_leader"], env)
    steps["concept_rank"] = run_cmd([sys.executable, str(TDX_FORMULA), "rank-block", "--manual-confirm", "--out", str(concept_out)], env)

    shortline_artifacts = resolve_shortline_artifacts(steps)
    manifest_path = shortline_artifacts["manifest"]
    score_path = limitup_out / "dragon_score.csv"
    leader_path = shortline_artifacts["leader_rank"]
    concept_rank_path = concept_out / "dynamic_hotspot_rank.json"
    role_sync_path = concept_out / "role_sync.json"
    blocked_reasons = []
    manifest = read_json(manifest_path) if manifest_path and manifest_path.is_file() else {}
    leader = read_limitup_rows(leader_path) if leader_path and leader_path.is_file() else []
    concept_rank = read_json(concept_rank_path) if concept_rank_path.is_file() else {}
    role_sync = read_json(role_sync_path) if role_sync_path.is_file() else {}
    rows = read_limitup_rows(score_path)
    all_zt_rows = load_zt_rows(trade_date)
    if all_zt_rows:
        rows = all_zt_rows
    if not manifest:
        blocked_reasons.append("shortline manifest missing")
    if not leader:
        blocked_reasons.append("hotspot leader report missing")
    if not concept_rank:
        blocked_reasons.append("dynamic concept rank missing")
    if not role_sync:
        blocked_reasons.append("dynamic role sync missing")
    if concept_rank and concept_rank.get("status") != "PASS":
        blocked_reasons.append("dynamic concept rank did not pass")
    no_signal = concept_rank.get("status") == "PASS" and int(concept_rank.get("hotspot_rank_count") or 0) == 0
    if role_sync and role_sync.get("status") != "PASS" and not no_signal:
        blocked_reasons.append("dynamic role sync did not pass")
    if not rows:
        blocked_reasons.append("dragon score missing")
    for step_name, step_result in steps.items():
        if not step_result.get("ok"):
            blocked_reasons.append(f"upstream step failed: {step_name}")

    rank_blocks = [
        item for item in concept_rank.get("rank_blocks", [])
        if item.get("sector_name") and item.get("dynamic_score") is not None
    ]
    selected_sectors = [
        {
            "rank": int(item.get("rank") or 0),
            "alias": str(item.get("alias") or ""),
            "sector": str(item.get("sector_name") or ""),
            "dynamic_score": float(item.get("dynamic_score") or 0),
            "metrics": item.get("metrics") or {},
            "percentiles": item.get("percentiles") or {},
            "member_count": int(item.get("member_count") or 0),
            "coverage_count": int(item.get("coverage_count") or 0),
            "trade_date": trade_date,
        }
        for item in rank_blocks[:3]
    ]
    if len(selected_sectors) != 3 and not no_signal:
        blocked_reasons.append("three strict dynamic concept mainlines unavailable")
    if concept_rank.get("hotspot_gate", {}).get("relative_fallback_used") is not False:
        blocked_reasons.append("dynamic concept rank used forbidden fallback")
    if str(concept_rank.get("trade_date") or "") != trade_date:
        blocked_reasons.append("dynamic concept rank date mismatch")

    research = (
        {"path": "", "sha256": "", "records": {}, "directions": {}, "errors": []}
        if no_signal
        else load_research_evidence(args.research_evidence, trade_date)
    )

    zt_by_code = {str(row.get("code") or ""): row for row in rows}
    candidate_pools = role_sync.get("candidate_pool_by_direction", {}) if isinstance(role_sync, dict) else {}
    catchup = []
    research_gaps = []
    excluded_candidates = []
    role_slots = []
    direction_reviews = []
    used_codes = set()
    recorded_exclusions = set()
    for sector in selected_sectors:
        alias = sector["alias"]
        name = sector["sector"]
        pool = candidate_pools.get(alias, []) if isinstance(candidate_pools, dict) else []
        review = research["directions"].get(name)
        review_errors = []
        if not isinstance(review, dict):
            review_errors.append("方向研究结论缺失")
            review = {}
        if review.get("status") != "PASS":
            review_errors.append("方向研究状态不是PASS")
        if not str(review.get("conclusion") or "").strip():
            review_errors.append("方向研究结论为空")
        reviewed_codes = {str(value).strip() for value in review.get("reviewed_codes", []) if len(str(value).strip()) == 6}
        pool_scored = []
        for candidate in pool:
            code = str(candidate.get("stock_code") or "")[:6]
            if len(code) != 6 or code in used_codes:
                continue
            record = research["records"].get(f"{name}|{code}")
            pool_scored.append(build_dynamic_candidate(candidate, pool, sector, zt_by_code.get(code), record or {}))
        pool_scored.sort(key=lambda item: (-float(item.get("score") or 0), -float(item.get("tdx_sort_key") or 0), str(item.get("code") or "")))
        unavailable_codes = set()
        encountered_codes = set()
        selected = []
        for role_index in (1, 2, 3):
            chosen = None
            for item in pool_scored:
                code = str(item.get("code") or "")
                if code in used_codes or code in unavailable_codes or float(item.get("score") or 0) < 65:
                    continue
                encountered_codes.add(code)
                record = research["records"].get(f"{name}|{code}")
                row = zt_by_code.get(code) or {"code": code, "name": record.get("name") if isinstance(record, dict) else item.get("name")}
                completeness_errors = research_record_completeness_errors(record, row, name)
                if completeness_errors:
                    research_gaps.append({"mainline": name, "code": code, "name": row.get("name"), "errors": completeness_errors})
                    unavailable_codes.add(code)
                    continue
                selection_errors = research_record_errors(record, row, name)
                if selection_errors:
                    if (name, code) not in recorded_exclusions:
                        excluded_candidates.append({
                            "mainline": name,
                            "code": code,
                            "name": row.get("name"),
                            "score": item.get("score"),
                            "errors": selection_errors,
                        })
                        recorded_exclusions.add((name, code))
                    unavailable_codes.add(code)
                    continue
                chosen = build_dynamic_candidate(
                    next(value for value in pool if str(value.get("stock_code") or "")[:6] == code),
                    pool,
                    sector,
                    zt_by_code.get(code),
                    record,
                )
                chosen["role"] = f"补涨龙{role_index}"
                selected.append(chosen)
                catchup.append(chosen)
                used_codes.add(code)
                break
            if chosen is None:
                vacancy_reason = str(review.get("vacancy_reason") or "达到该龙位动态门槛的候选均被题材、位置或硬风险闸门剔除")
                role_slots.append({
                    "mainline": name,
                    "role": f"补涨龙{role_index}",
                    "status": "VACANT",
                    "reason": vacancy_reason,
                })
            else:
                role_slots.append({
                    "mainline": name,
                    "role": f"补涨龙{role_index}",
                    "status": "PASS",
                    "code": chosen["code"],
                    "name": chosen["name"],
                    "score": chosen["score"],
                })
        missing_reviewed_codes = sorted(encountered_codes - reviewed_codes)
        if missing_reviewed_codes:
            review_errors.append(f"方向研究未覆盖动态门槛候选:{','.join(missing_reviewed_codes)}")
        if review_errors:
            research_gaps.append({"mainline": name, "errors": review_errors})
        direction_reviews.append({
            "mainline": name,
            "status": "PASS" if not review_errors else "OBSERVE",
            "conclusion": review.get("conclusion"),
            "vacancy_reason": review.get("vacancy_reason"),
            "reviewed_codes": sorted(reviewed_codes),
            "encountered_codes": sorted(encountered_codes),
            "selected_count": len(selected),
        })

    research_complete = no_signal or (
        not research["errors"]
        and not research_gaps
        and len(direction_reviews) == 3
        and all(item.get("status") == "PASS" for item in direction_reviews)
        and all(item.get("verification_status") == "PASS" for item in catchup)
    )
    status = "PASS" if not blocked_reasons and research_complete else "OBSERVE" if not blocked_reasons else "BLOCKED"
    latest_trade_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
    result = {
        "skill": "buzhang-leader-mining",
        "trade_date": trade_date,
        "latest_trade_date": latest_trade_date,
        "status": status,
        "decision_status": "NO_SIGNAL" if no_signal else "CANDIDATES_READY" if status == "PASS" else "RESEARCH_INCOMPLETE",
        "mainline_market_status": manifest.get("status"),
        "upstream_requires_research_completion": manifest.get("requires_research_completion"),
        "requires_research_completion": not research_complete,
        "mainlines": concept_rank.get("top10", [])[:10],
        "selected_mainlines": selected_sectors,
        "direction_reviews": direction_reviews,
        "role_slots": role_slots,
        "candidates": catchup,
        "candidate_count": len(catchup),
        "excluded_candidates": excluded_candidates,
        "blocked_reasons": blocked_reasons,
        "research_gaps": [*research["errors"], *research_gaps],
        "source_manifest": {
            "shortline": str(manifest_path or ""),
            "dragon_score": str(score_path),
            "hotspot_leader": str(leader_path or ""),
            "dynamic_concept_rank": str(concept_rank_path),
            "dynamic_role_sync": str(role_sync_path),
            "candidate_research": research["path"],
            "candidate_research_sha256": research["sha256"],
        },
        "step_status": {k: v.get("ok") for k, v in steps.items()},
        "readback": {
            "selected_mainline_count": len(selected_sectors),
            "candidate_count": len(catchup),
            "candidate_pass_count": sum(1 for item in catchup if item.get("verification_status") == "PASS"),
            "role_slot_count": len(role_slots),
            "vacant_role_count": sum(1 for item in role_slots if item.get("status") == "VACANT"),
            "excluded_candidate_count": len(excluded_candidates),
            "research_complete": research_complete,
            "selected_codes": [item.get("code") for item in catchup],
        },
    }
    (out / "buzhang_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "buzhang_candidates.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fields = [
            "mainline", "role", "code", "name", "score", "board_count", "first_limit_time",
            "break_count", "turnover", "amount", "limit_capital", "close", "return_1d_pct",
            "return_5d_pct", "volume_ratio_5d", "amount_ratio_5d", "tdx_sort_key", "evidence_id", "direct_mapping",
            "trigger", "confirmation", "invalidation", "risk_flags", "risk_conclusion",
            "research_evidence_ids", "verification_status",
        ]
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for item in catchup:
            row = dict(item)
            row["risk_flags"] = "|".join(item.get("risk_flags") or [])
            row["research_evidence_ids"] = "|".join(item.get("research_evidence_ids") or [])
            w.writerow(row)
    (out / "audit.json").write_text(json.dumps({
        "trade_date": trade_date,
        "status": status,
        "blocked_reasons": blocked_reasons,
        "research_evidence": {"path": research["path"], "sha256": research["sha256"], "errors": research["errors"]},
        "research_gaps": research_gaps,
        "direction_reviews": direction_reviews,
        "role_slots": role_slots,
        "excluded_candidates": excluded_candidates,
        "steps": steps,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    report_lines = [
        f"# 补涨龙头挖掘 {trade_date}",
        "",
        f"状态：{status}",
        f"动态热点方向：{'、'.join(item['sector'] for item in selected_sectors) or '无'}",
        "",
    ]
    for sector in selected_sectors:
        report_lines.append(f"## 第{sector['rank']}名 {sector['sector']}（动态分 {sector['dynamic_score']:.2f}）")
        for slot in [value for value in role_slots if value.get("mainline") == sector["sector"]]:
            if slot.get("status") == "PASS":
                report_lines.append(f"- {slot['role']}：{slot['code']} {slot['name']}，综合分 {slot['score']:.2f}")
            else:
                report_lines.append(f"- {slot['role']}：缺位；{slot['reason']}")
        report_lines.append("")
    (out / "report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(json.dumps({"status": status, "trade_date": trade_date, "candidate_count": len(catchup), "result": str(out / "buzhang_result.json"), "blocked_reasons": blocked_reasons}, ensure_ascii=False, indent=2))
    return 0 if status in {"PASS", "OBSERVE"} else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="补涨龙头挖掘唯一入口")
    sub = p.add_subparsers(dest="command")
    sub.add_parser("info")
    sub.add_parser("selftest")
    tdx = sub.add_parser("tdx-formula")
    tdx.add_argument("args", nargs=argparse.REMAINDER)
    r = sub.add_parser("run")
    r.add_argument("args", nargs=argparse.REMAINDER)
    return p


def main() -> int:
    p = build_parser()
    ns = p.parse_args()
    if ns.command == "info":
        return info()
    if ns.command == "selftest":
        return selftest()
    if ns.command == "tdx-formula":
        raw = ns.args[1:] if ns.args and ns.args[0] == "--" else ns.args
        script = SKILL_DIR / "scripts" / "tdx_formula.py"
        return subprocess.run([sys.executable, str(script), *raw], cwd=str(SKILL_DIR)).returncode
    if ns.command == "run":
        raw = ns.args[1:] if ns.args and ns.args[0] == "--" else ns.args
        rp = argparse.ArgumentParser(description="补涨龙头实战运行")
        rp.add_argument("--date")
        rp.add_argument("--manual-confirm", action="store_true")
        rp.add_argument("--out")
        rp.add_argument("--research-evidence")
        return run(rp.parse_args(raw))
    return info()


if __name__ == "__main__":
    raise SystemExit(main())
