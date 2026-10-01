#!/usr/bin/env python3
"""Validate and bind formatted artifacts from the merged sentiment workflow."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_BINDING = ROOT / "references" / "report_template_binding.json"
REPORT_NAME = "A股三日舆情解读结果_Codex自动生成.docx"
REDLINE_NAME = "a_share_sentiment_redline_audit.json"
DELIVERY_AUDIT_NAME = "a_share_sentiment_delivery_audit.json"
RENDER_AUDIT_NAME = "a_share_sentiment_word_render_audit.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json_root_not_object:{path}")
    return payload


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def validate(
    business_stdout: Path,
    output_path: Path,
) -> tuple[int, dict[str, Any]]:
    errors: list[str] = []
    try:
        business = load_json(business_stdout)
    except Exception as exc:
        business = {}
        errors.append(f"business_stdout_invalid:{type(exc).__name__}:{exc}")

    if business.get("schema") != "MERGED_STOCK_SKILL_RESULT_V2":
        errors.append("business_schema_invalid")
    if str(business.get("status", "")).upper() != "PASS":
        errors.append("business_status_not_pass")

    closure_value = business.get("closure_audit")
    closure_path_value = (
        closure_value.get("path")
        if isinstance(closure_value, dict)
        else None
    )
    closure_path = Path(str(closure_path_value)).resolve() if closure_path_value else None
    closure: dict[str, Any] = {}
    if closure_path is None or not closure_path.is_file():
        errors.append("closure_audit_missing")
    else:
        try:
            closure = load_json(closure_path)
        except Exception as exc:
            errors.append(f"closure_audit_invalid:{type(exc).__name__}:{exc}")
        if str(closure.get("status", "")).upper() != "PASS":
            errors.append("closure_audit_not_pass")
        if closure.get("reasons"):
            errors.append("closure_audit_has_reasons")

    report_candidates = [
        Path(str(value)).resolve()
        for value in closure.get("docx_paths", [])
        if Path(str(value)).name == REPORT_NAME
    ]
    report_path = report_candidates[0] if report_candidates else None
    if report_path is None or not report_path.is_file():
        errors.append("sentiment_report_missing")
    elif report_path.stat().st_size <= 20000:
        errors.append("sentiment_report_too_small")
    elif not zipfile.is_zipfile(report_path):
        errors.append("sentiment_report_not_valid_docx_container")
    else:
        with zipfile.ZipFile(report_path) as archive:
            if "word/document.xml" not in archive.namelist():
                errors.append("sentiment_report_document_xml_missing")

    sentiment_dir = report_path.parent if report_path is not None else None
    redline_path = sentiment_dir / REDLINE_NAME if sentiment_dir else None
    delivery_audit_path = (
        sentiment_dir / DELIVERY_AUDIT_NAME if sentiment_dir else None
    )
    render_audit_path = sentiment_dir / RENDER_AUDIT_NAME if sentiment_dir else None
    redline: dict[str, Any] = {}
    delivery_audit: dict[str, Any] = {}
    render_audit: dict[str, Any] = {}
    if redline_path is None or not redline_path.is_file():
        errors.append("redline_audit_missing")
    else:
        try:
            redline = load_json(redline_path)
        except Exception as exc:
            errors.append(f"redline_audit_invalid:{type(exc).__name__}:{exc}")
        if redline.get("ok") is not True:
            errors.append("redline_audit_not_ok")
        if redline.get("reasons"):
            errors.append("redline_audit_has_reasons")

    if delivery_audit_path is None or not delivery_audit_path.is_file():
        errors.append("delivery_audit_missing")
    else:
        try:
            delivery_audit = load_json(delivery_audit_path)
        except Exception as exc:
            errors.append(f"delivery_audit_invalid:{type(exc).__name__}:{exc}")
        if delivery_audit.get("ok") is not True:
            errors.append("delivery_audit_not_ok")
        report_record = delivery_audit.get("report")
        if report_path is not None and isinstance(report_record, dict):
            if str(report_record.get("sha256", "")).casefold() != sha256_file(
                report_path
            ):
                errors.append("delivery_audit_report_hash_mismatch")
        else:
            errors.append("delivery_audit_report_binding_missing")

    if render_audit_path is None or not render_audit_path.is_file():
        errors.append("word_render_audit_missing")
    else:
        try:
            render_audit = load_json(render_audit_path)
        except Exception as exc:
            errors.append(f"word_render_audit_invalid:{type(exc).__name__}:{exc}")
        if render_audit.get("status") != "PASS":
            errors.append("word_render_audit_not_pass")
        if render_audit.get("errors"):
            errors.append("word_render_audit_has_errors")
        render_report = render_audit.get("report")
        if report_path is None or not isinstance(render_report, dict):
            errors.append("word_render_report_binding_missing")
        elif str(render_report.get("sha256", "")).casefold() != sha256_file(report_path):
            errors.append("word_render_report_hash_mismatch")
        render_checks = render_audit.get("checks")
        required_render_checks = (
            "word_opened",
            "word_page_count_valid",
            "pdf_exported",
            "page_count_matches",
            "no_blank_pages",
            "no_bottom_edge_overflow",
            "contact_sheet_created",
        )
        if not isinstance(render_checks, dict) or not all(
            render_checks.get(name) is True for name in required_render_checks
        ):
            errors.append("word_render_checks_incomplete")
        pdf_record = render_audit.get("pdf")
        contact_record = render_audit.get("contact_sheet")
        for label, record in (("pdf", pdf_record), ("contact", contact_record)):
            if not isinstance(record, dict):
                errors.append(f"word_render_{label}_binding_missing")
                continue
            path = Path(str(record.get("path", "")))
            if not path.is_file() or sha256_file(path) != str(record.get("sha256", "")).casefold():
                errors.append(f"word_render_{label}_binding_invalid")

    template_binding: dict[str, Any] = {}
    try:
        template_binding = load_json(TEMPLATE_BINDING)
    except Exception as exc:
        errors.append(f"template_binding_invalid:{type(exc).__name__}:{exc}")
    template_record = template_binding.get("template")
    template_path: Path | None = None
    if isinstance(template_record, dict):
        template_path = Path(str(template_record.get("path", "")))
        if not template_path.is_absolute():
            template_path = ROOT / template_path
        template_path = template_path.resolve()
        expected_template_hash = str(
            template_record.get("sha256", "")
        ).casefold()
        if not template_path.is_file():
            errors.append("locked_template_missing")
        elif sha256_file(template_path) != expected_template_hash:
            errors.append("locked_template_hash_mismatch")
        locked_profile = delivery_audit.get("locked_template_profile")
        if (
            isinstance(locked_profile, dict)
            and str(locked_profile.get("sha256", "")).casefold()
            != expected_template_hash
        ):
            errors.append("delivery_audit_template_hash_mismatch")
    else:
        errors.append("template_record_missing")

    status = "PASS" if not errors else "BLOCKED"
    artifact_records = []
    for path in (
        report_path,
        redline_path,
        delivery_audit_path,
        render_audit_path,
        closure_path,
        TEMPLATE_BINDING,
        template_path,
    ):
        if path is not None and path.is_file():
            artifact_records.append(file_record(path))
    for record in (render_audit.get("pdf"), render_audit.get("contact_sheet")):
        if isinstance(record, dict):
            path = Path(str(record.get("path", "")))
            if path.is_file():
                artifact_records.append(file_record(path))

    payload = {
        "schema": "A_SHARE_SENTIMENT_FORMATTED_DELIVERY_MANIFEST_V1",
        "status": status,
        "artifacts": artifact_records,
        "validation": {
            "status": status,
            "errors": errors,
            "report": file_record(report_path)
            if report_path is not None and report_path.is_file()
            else None,
            "redline_audit": {
                "status": "PASS"
                if redline.get("ok") is True and not redline.get("reasons")
                else "BLOCKED",
                "errors": list(redline.get("reasons", [])),
            },
            "delivery_audit": {
                "status": "PASS"
                if delivery_audit.get("ok") is True
                else "BLOCKED",
                "errors": []
                if delivery_audit.get("ok") is True
                else ["delivery_audit_not_ok"],
            },
            "word_render_audit": {
                "status": "PASS"
                if render_audit.get("status") == "PASS" and not render_audit.get("errors")
                else "BLOCKED",
                "errors": list(render_audit.get("errors", [])),
                "checks": render_audit.get("checks", {}),
            },
            "closure_audit": {
                "status": str(closure.get("status", "BLOCKED")).upper(),
                "errors": list(closure.get("reasons", [])),
            },
        },
        "template_binding": template_binding,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return (0 if not errors else 2), payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--business-stdout", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    code, payload = validate(
        Path(args.business_stdout).resolve(),
        Path(args.output).resolve(),
    )
    print(json.dumps(payload, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
