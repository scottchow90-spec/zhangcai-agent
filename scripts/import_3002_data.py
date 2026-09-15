#!/usr/bin/env python3
"""Import safe, read-only data snapshots from the untouched 3002 app.

The import is deliberately staged under ``app-data/imported-3002`` so the
3003 EXE can carry the source history without confusing it with the current
TDX snapshot.  The two canonical public/news ``latest.json`` files are
promoted only when the 3002 snapshot is for the same date and has at least as
many usable records; the previous 3003 files are backed up in the import
directory before promotion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


APP_ROOT = Path(os.environ.get("ZHANGCAI_APP_ROOT", Path(__file__).resolve().parents[1]))
SOURCE_ROOT = Path(os.environ.get("ZHANGCAI_3002_ROOT", APP_ROOT.parent / "zhangcai-demo"))
DATA_ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR", APP_ROOT / "app-data"))
IMPORT_ROOT = DATA_ROOT / "imported-3002"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_file(path: Path) -> bool:
    name = path.name.lower()
    # Do not move credentials, sessions or private runtime identities into a
    # future EXE data directory. The selected groups include public evidence,
    # completed task artifacts and operational logs, but exclude 3002 harness
    # jobs/sessions and formula worker sessions.
    blocked = (".env", "credential", "cookie", "token", "password", ".pem", ".key")
    return not any(part in name for part in blocked) and name not in {".anonymous-user-id"}


def iter_files(source_dir: Path, extensions: set[str] | None = None) -> Iterable[Path]:
    if not source_dir.is_dir():
        return
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or not safe_file(path):
            continue
        if extensions and path.suffix.lower() not in extensions:
            continue
        yield path


def copy_group(relative: str, extensions: set[str] | None = None) -> list[dict[str, Any]]:
    source_dir = SOURCE_ROOT / relative
    copied: list[dict[str, Any]] = []
    for source in iter_files(source_dir, extensions):
        source_rel = source.relative_to(SOURCE_ROOT).as_posix()
        target = IMPORT_ROOT / source_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append({
            "source": source_rel,
            "target": target.relative_to(DATA_ROOT).as_posix(),
            "bytes": target.stat().st_size,
            "sha256": sha256(target),
            "source_modified_at": datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds"),
        })
    return copied


def record_count(value: Any) -> int:
    if not isinstance(value, dict):
        return 0
    if isinstance(value.get("records"), list):
        return len(value["records"])
    data = value.get("data")
    if isinstance(data, dict):
        if isinstance(data.get("records"), list):
            return len(data["records"])
        if isinstance(data.get("pool"), list):
            return len(data["pool"])
    result = value.get("result")
    if isinstance(result, dict) and isinstance(result.get("data"), list):
        return len(result["data"])
    return 0


def source_catalog(imported_files: list[dict[str, Any]]) -> dict[str, Any]:
    public_path = IMPORT_ROOT / "data" / "public" / "latest.json"
    news_path = IMPORT_ROOT / "data" / "news" / "latest.json"
    public = read_json(public_path, {})
    news = read_json(news_path, {})
    source_rows: dict[str, Any] = {}
    if isinstance(public, dict):
        for name, value in (public.get("sources") or {}).items():
            source_rows[name] = {
                "status": value.get("status") if isinstance(value, dict) else None,
                "provider": value.get("provider") if isinstance(value, dict) else None,
                "method": value.get("method") if isinstance(value, dict) else None,
                "source_date": public.get("date"),
                "record_count": record_count(value),
                "snapshot": "imported-3002/data/public/latest.json",
            }
    news_source = news.get("source") if isinstance(news, dict) else {}
    source_rows["eastmoneyFastNews"] = {
        "status": news.get("status") if isinstance(news, dict) else None,
        "source_date": news.get("date") if isinstance(news, dict) else None,
        "record_count": news.get("sameDayRecordCount", 0) if isinstance(news, dict) else 0,
        "provider": "东方财富7x24快讯",
        "source_url": news_source.get("url") if isinstance(news_source, dict) else None,
        "snapshot": "imported-3002/data/news/latest.json",
    }
    groups = {
        "public_market": {
            "path": "imported-3002/data/public/",
            "latest": "imported-3002/data/public/latest.json",
            "date": public.get("date") if isinstance(public, dict) else None,
            "sources": sorted((public.get("sources") or {}).keys()) if isinstance(public, dict) else [],
        },
        "news": {
            "path": "imported-3002/data/news/",
            "latest": "imported-3002/data/news/latest.json",
            "date": news.get("date") if isinstance(news, dict) else None,
            "sources": ["东方财富7x24快讯"],
            "same_day_record_count": news.get("sameDayRecordCount", 0) if isinstance(news, dict) else 0,
        },
        "daily_context": {
            "path": "imported-3002/data/harness/context/",
            "latest": "imported-3002/data/harness/context/latest-data.json",
        },
        "runtime_status": {"path": "imported-3002/data/runtime/"},
        "operational_logs": {
            "path": "imported-3002/data/logs/",
            "note": "3002 运行诊断日志，仅作故障追溯，不作为行情事实",
        },
        "task_artifacts": {
            "path": "imported-3002/data/harness/tasks/",
            "note": "已完成 Harness 任务产物，仅作历史证据",
        },
        "data_reports": {"path": "imported-3002/data/reports/"},
        "strategy_results": {"path": "imported-3002/data/strategy-results/"},
        "historical_reports": {"path": "imported-3002/reports/"},
        "runtime_results": {"path": "imported-3002/runtime-results/"},
    }
    return {
        "schema": "ZHANGCAI_3002_SOURCE_CATALOG_V1",
        "status": "available" if imported_files else "missing",
        "imported_at": now(),
        "source_root": str(SOURCE_ROOT),
        "data_root": str(DATA_ROOT),
        "sources": groups,
        "provider_snapshots": source_rows,
        "file_count": len(imported_files),
        "read_policy": [
            "先核对 source_date/status/record_count，再将快照用于 Harness 上下文",
            "当前交易日以 3003 本地 TDX 日线归档为准，3002 快照不能覆盖更新日期",
            "导入目录是只读证据副本；应用运行产生的新数据仍写入 3003 app-data 的 canonical 目录",
        ],
    }


def write_compat_context(catalog: dict[str, Any]) -> None:
    """Expose a target-root context without leaking 3002 absolute paths."""
    public = read_json(DATA_ROOT / "public" / "latest.json", {})
    news = read_json(DATA_ROOT / "news" / "latest.json", {})
    date = str(public.get("date") or news.get("date") or "").replace("-", "")
    if len(date) == 8:
        date_text = f"{date[:4]}-{date[4:6]}-{date[6:]}"
    else:
        date_text = str(public.get("date") or news.get("date") or "")
    context = {
        "schema": "ZHANGCAI_HARNESS_DAILY_CONTEXT_V1",
        "date": date_text,
        "generatedAt": now(),
        "runtimeRoot": str(DATA_ROOT / "runtime"),
        "publicSnapshot": str(DATA_ROOT / "public" / "latest.json"),
        "newsSnapshot": str(DATA_ROOT / "news" / "latest.json"),
        "localDataPage": "harness/context/local-data-page.json",
        "imported3002Catalog": "imported-3002/source-catalog.json",
        "steps": [{
            "name": "3002 兼容数据导入",
            "status": "completed",
            "script": "import_3002_data.py",
            "finishedAt": catalog.get("imported_at"),
            "code": 0,
        }],
        "snapshots": {
            "publicMarket": {"status": public.get("sources", {}) and "available" or "missing", "path": "public/latest.json", "source": "3002 imported + 3003 canonical"},
            "news": {"status": news.get("status", "missing"), "path": "news/latest.json", "sameDayRecordCount": news.get("sameDayRecordCount", 0)},
            "imported3002": {"status": catalog.get("status", "missing"), "path": "imported-3002/source-catalog.json", "fileCount": catalog.get("file_count", 0)},
        },
        "harness": {"status": "pending", "note": "兼容导入上下文；下一次每日刷新会写入完整校验回执。"},
    }
    write_json(DATA_ROOT / "harness" / "context" / "latest-data.json", context)


def snapshot_value(path: Path) -> tuple[str, int, str]:
    value = read_json(path, {})
    if not isinstance(value, dict):
        return "", 0, ""
    date = str(value.get("date") or "").replace("-", "")
    count = int(value.get("sameDayRecordCount") or 0) if path.parts[-2:] == ("news", "latest.json") else 0
    if path.name == "latest.json" and "sources" in value:
        count = sum(record_count(v) for v in (value.get("sources") or {}).values())
    return date, count, sha256(path)


def promote_if_richer(kind: str) -> dict[str, Any]:
    source = IMPORT_ROOT / "data" / kind / "latest.json"
    target = DATA_ROOT / kind / "latest.json"
    if not source.is_file():
        return {"kind": kind, "status": "missing_source"}
    source_date, source_count, source_hash = snapshot_value(source)
    target_date, target_count, target_hash = snapshot_value(target) if target.is_file() else ("", 0, "")
    same_date = source_date and target_date and source_date == target_date
    promote = not target.is_file() or (same_date and source_count > target_count)
    result = {
        "kind": kind,
        "source": source.relative_to(DATA_ROOT).as_posix(),
        "target": target.relative_to(DATA_ROOT).as_posix(),
        "source_date": source_date,
        "target_date": target_date,
        "source_record_score": source_count,
        "target_record_score": target_count,
        "source_sha256": source_hash,
        "target_sha256_before": target_hash,
        "promoted": promote,
    }
    if not promote:
        result["reason"] = "目标已有同日且不少于导入快照的记录；导入副本仍完整保留。"
        return result
    if target.is_file():
        backup = IMPORT_ROOT / "target-before" / kind / "latest.json"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        result["backup"] = backup.relative_to(DATA_ROOT).as_posix()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    result["status"] = "promoted"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default="", help="3002 源目录，默认为相邻 zhangcai-demo")
    args = parser.parse_args()
    global SOURCE_ROOT
    if args.source_root:
        SOURCE_ROOT = Path(args.source_root).resolve()
    if not SOURCE_ROOT.is_dir():
        raise SystemExit(f"3002 源目录不存在：{SOURCE_ROOT}")
    IMPORT_ROOT.mkdir(parents=True, exist_ok=True)
    extensions = {".json", ".jsonl", ".md", ".txt", ".csv", ".docx", ".pdf"}
    log_extensions = extensions | {".log"}
    groups = [
        ("data/public", None),
        ("data/news", None),
        ("data/harness/context", {".json"}),
        ("data/harness/tasks", extensions),
        ("data/logs", log_extensions),
        ("data/reports", extensions),
        ("data/runtime", extensions),
        ("data/strategy-results", extensions),
        ("reports", extensions),
        ("runtime-results", extensions),
    ]
    copied: list[dict[str, Any]] = []
    for relative, allowed in groups:
        copied.extend(copy_group(relative, allowed))
    manifest = {
        "schema": "ZHANGCAI_3002_DATA_IMPORT_V1",
        "status": "available" if copied else "missing",
        "imported_at": now(),
        "source_root": str(SOURCE_ROOT),
        "data_root": str(DATA_ROOT),
        "target_root": "imported-3002/",
        "groups": [relative for relative, _ in groups],
        "file_count": len(copied),
        "bytes": sum(int(item["bytes"]) for item in copied),
        "files": copied,
        "promotion": [promote_if_richer("public"), promote_if_richer("news")],
        "safety": {
            "3002_modified": False,
            "credentials_copied": False,
            "harness_jobs_sessions_copied": False,
            "tdx_source_modified": False,
        },
    }
    write_json(IMPORT_ROOT / "manifest.json", manifest)
    catalog = source_catalog(copied)
    write_json(IMPORT_ROOT / "source-catalog.json", catalog)
    write_compat_context(catalog)
    print(json.dumps({"status": manifest["status"], "file_count": len(copied), "bytes": manifest["bytes"], "promotion": manifest["promotion"], "catalog": "imported-3002/source-catalog.json"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
