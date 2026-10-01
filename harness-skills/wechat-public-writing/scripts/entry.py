#!/usr/bin/env python3
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REFERENCES_DIR = SKILL_DIR / "references"
PROFILES_PATH = REFERENCES_DIR / "style-profiles.json"
CORPUS_PATH = REFERENCES_DIR / "source-corpus.json"
SKILL_ID = "wechat-public-writing"
DISPLAY_NAME = "公众号写作"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def file_binding(path: Path):
    data = path.read_bytes()
    return {
        "path": str(path),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def inspect_corpus():
    corpus = load_json(CORPUS_PATH)
    records = corpus.get("records", [])
    counts = Counter(record.get("account", "") for record in records)
    if len(records) != 200:
        raise ValueError(f"corpus record count must be 200, got {len(records)}")
    if sorted(counts.values()) != [100, 100]:
        raise ValueError(f"corpus account counts must be 100+100, got {dict(counts)}")
    return corpus, records, counts


def command_inspect(args):
    profiles = load_json(PROFILES_PATH)
    corpus, records, counts = inspect_corpus()
    result = {
        "status": "PASS",
        "skill_id": SKILL_ID,
        "display_name": DISPLAY_NAME,
        "profiles": sorted(profiles["profiles"].keys()),
        "record_count": len(records),
        "account_counts": dict(counts),
        "direct_samples_total": corpus.get("coverage", {}).get("direct_samples_total"),
        "backend_continuity_verified": corpus.get("coverage", {}).get("complete_backend_recent_200_verified", False),
        "corpus": file_binding(CORPUS_PATH),
        "skill_file": file_binding(SKILL_DIR / "SKILL.md"),
        "entrypoint": file_binding(Path(__file__).resolve()),
    }
    if args.out:
        write_json(Path(args.out), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def command_prepare(args):
    request_path = Path(args.request)
    request = load_json(request_path)
    topic = str(request.get("topic", "")).strip()
    if not topic:
        raise ValueError("request.topic is required")

    profiles = load_json(PROFILES_PATH)
    mode = request.get("mode", profiles.get("default_mode", "hybrid"))
    if mode not in profiles["profiles"]:
        raise ValueError(f"unsupported mode: {mode}")
    timeliness = request.get("timeliness", "current")
    if timeliness not in {"current", "evergreen"}:
        raise ValueError("request.timeliness must be current or evergreen")

    corpus, records, counts = inspect_corpus()
    target_length = int(request.get("target_length", 1200))
    if target_length < 600:
        raise ValueError("request.target_length must be at least 600 Chinese characters")

    brief = {
        "schema_version": 1,
        "status": "PREPARED",
        "skill_id": SKILL_ID,
        "display_name": DISPLAY_NAME,
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "request": request,
        "mode": mode,
        "profile": profiles["profiles"][mode],
        "fixed_outline": profiles["outline"],
        "non_negotiables": profiles["non_negotiables"],
        "fact_boundary": {
            "provided_fact_count": len(request.get("facts", [])),
            "current_information_requires_verified_sources": timeliness == "current",
            "instruction": "只把请求中已核验的 facts 或同轮研究产物写成事实；其他内容写成判断、条件或待验证观察。",
        },
        "validation": {
            "min_body_chars": max(600, int(target_length * 0.65)),
            "min_paragraphs": 6,
            "time_anchor_required": timeliness == "current",
            "conclusion_upfront_required": True,
            "conditional_logic_required": True,
            "action_required": True,
            "risk_boundary_required": True,
            "originality_required": True,
        },
        "corpus_binding": {
            **file_binding(CORPUS_PATH),
            "record_count": len(records),
            "account_counts": dict(counts),
            "direct_samples_total": corpus.get("coverage", {}).get("direct_samples_total"),
            "backend_continuity_verified": corpus.get("coverage", {}).get("complete_backend_recent_200_verified", False),
        },
        "request_binding": file_binding(request_path),
    }
    write_json(Path(args.out), brief)
    print(json.dumps(brief, ensure_ascii=False, indent=2))


def token_check(text, tokens):
    return any(token in text for token in tokens)


def command_validate(args):
    article_path = Path(args.article)
    brief_path = Path(args.brief)
    article = article_path.read_text(encoding="utf-8")
    brief = load_json(brief_path)
    if brief.get("skill_id") != SKILL_ID or brief.get("status") != "PREPARED":
        raise ValueError("brief was not prepared by this skill")

    lines = [line.rstrip() for line in article.splitlines()]
    nonempty = [line for line in lines if line.strip()]
    title_ok = bool(nonempty and nonempty[0].startswith("# ") and 4 <= len(nonempty[0][2:].strip()) <= 40)
    body_lines = lines[lines.index(nonempty[0]) + 1 :] if nonempty else []
    body = "\n".join(body_lines).strip()
    compact_chars = len(re.sub(r"\s+", "", body))
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
    opening = "\n".join(paragraphs[:2])
    ending = body[int(len(body) * 0.6) :] if body else ""
    profile = brief["profile"]
    time_tokens = ["今天", "今晚", "明天", "本周", "周末", "下周", "最近", "当前", "眼下"]
    conclusion_tokens = ["先说结论", "先说判断", "核心判断", "我的判断", "关键在于", "我认为", "大概率"]
    conditional_tokens = ["如果", "一旦", "只要", "除非", "前提", "反过来"]
    logic_tokens = profile.get("required_logic_terms", [])
    action_tokens = profile.get("required_action_terms", [])
    risk_tokens = profile.get("required_risk_terms", [])
    forbidden_names = load_json(PROFILES_PATH).get("source_names_for_impersonation_check", [])

    checks = [
        {"name": "markdown_title", "ok": title_ok, "actual": nonempty[0] if nonempty else ""},
        {"name": "body_length", "ok": compact_chars >= brief["validation"]["min_body_chars"], "actual": compact_chars, "minimum": brief["validation"]["min_body_chars"]},
        {"name": "paragraph_count", "ok": len(paragraphs) >= brief["validation"]["min_paragraphs"], "actual": len(paragraphs), "minimum": brief["validation"]["min_paragraphs"]},
        {"name": "conclusion_upfront", "ok": token_check(opening, conclusion_tokens)},
        {"name": "time_anchor", "ok": (not brief["validation"]["time_anchor_required"]) or token_check(opening, time_tokens)},
        {"name": "conditional_logic", "ok": token_check(body, conditional_tokens) and token_check(body, logic_tokens)},
        {"name": "actionable_ending", "ok": token_check(ending, action_tokens)},
        {"name": "risk_boundary", "ok": token_check(ending, risk_tokens)},
        {"name": "no_placeholders", "ok": not re.search(r"\{\{|\}\}|TODO|待补充|示例内容", article, re.IGNORECASE)},
        {"name": "no_source_impersonation", "ok": not token_check(article, forbidden_names)},
    ]
    passed = all(check["ok"] for check in checks)
    receipt = {
        "schema_version": 1,
        "status": "PASS" if passed else "FAIL",
        "skill_id": SKILL_ID,
        "display_name": DISPLAY_NAME,
        "mode": brief["mode"],
        "topic": brief["request"].get("topic"),
        "checks": checks,
        "article": file_binding(article_path),
        "brief": file_binding(brief_path),
        "corpus": brief["corpus_binding"],
        "validated_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(Path(args.out), receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    if not passed:
        return 2
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="公众号写作固定技能入口")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="检查技能、入口与200条语料绑定")
    inspect_parser.add_argument("--out", help="持久化检查结果 JSON")
    inspect_parser.set_defaults(handler=command_inspect)

    prepare_parser = subparsers.add_parser("prepare", help="从请求生成固定写作简报")
    prepare_parser.add_argument("--request", required=True)
    prepare_parser.add_argument("--out", required=True)
    prepare_parser.set_defaults(handler=command_prepare)

    validate_parser = subparsers.add_parser("validate", help="验收公众号 Markdown 成稿")
    validate_parser.add_argument("--article", required=True)
    validate_parser.add_argument("--brief", required=True)
    validate_parser.add_argument("--out", required=True)
    validate_parser.set_defaults(handler=command_validate)
    return parser


def main():
    args = build_parser().parse_args()
    try:
        result = args.handler(args)
        return 0 if result is None else result
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "skill_id": SKILL_ID, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
