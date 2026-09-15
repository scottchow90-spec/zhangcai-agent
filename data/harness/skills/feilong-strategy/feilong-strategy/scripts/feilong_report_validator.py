"""Validate and manifest a formatted Feilong stock-analysis Word report."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = ROOT.name
TEMPLATE_PATH = ROOT / "references" / "feilong-report-template.json"
REQUIRED_DATA_DIMENSIONS = (
    "identity",
    "effective_trading_date",
    "quote_kline",
    "fundamentals",
    "news_announcements",
    "sector_theme",
    "source_freshness",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evidence(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "size": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def load_json(path: Path, label: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label}_unreadable:{exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label}_not_object")
    return payload


def extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            required = {"[Content_Types].xml", "word/document.xml"}
            if not required.issubset(archive.namelist()):
                raise RuntimeError("docx_ooxml_parts_missing")
            root = ElementTree.fromstring(archive.read("word/document.xml"))
    except (OSError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise RuntimeError(f"docx_unreadable:{exc}") from exc
    return "".join(node.text or "" for node in root.iter() if node.tag.endswith("}t"))


def validate_receipt(path: Path, expected_date: str) -> list[str]:
    errors: list[str] = []
    receipt = load_json(path, "analysis_receipt")
    if receipt.get("skill_id") != SKILL_ID:
        errors.append("analysis_receipt_skill_mismatch")
    if receipt.get("status") != "CLEAN_PASS":
        errors.append("analysis_receipt_status_not_clean")
    readiness = receipt.get("production_readiness")
    if not isinstance(readiness, dict):
        errors.append("analysis_receipt_readiness_missing")
        return errors
    if readiness.get("status") != "CLEAN_PASS":
        errors.append("analysis_receipt_readiness_not_clean")
    if readiness.get("conclusion_eligible") is not True:
        errors.append("analysis_receipt_not_conclusion_eligible")
    gate = readiness.get("data_gate")
    if not isinstance(gate, dict):
        errors.append("analysis_receipt_data_gate_missing")
        return errors
    if gate.get("status") != "CLEAN_PASS" or gate.get("errors") != []:
        errors.append("analysis_receipt_data_gate_not_clean")
    if gate.get("effective_trading_date") != expected_date:
        errors.append("analysis_receipt_effective_date_mismatch")
    if gate.get("latest_required_trading_date") != expected_date:
        errors.append("analysis_receipt_required_date_mismatch")
    dimensions = gate.get("dimensions")
    if not isinstance(dimensions, dict):
        errors.append("analysis_receipt_dimensions_missing")
        return errors
    for name in REQUIRED_DATA_DIMENSIONS:
        row = dimensions.get(name)
        if not isinstance(row, dict) or row.get("status") != "CLEAN_PASS":
            errors.append(f"analysis_receipt_dimension_not_clean:{name}")
    return errors


def build_manifest(args: argparse.Namespace) -> dict[str, object]:
    errors: list[str] = []
    docx = Path(args.docx).resolve()
    pdf = Path(args.pdf).resolve()
    receipt = Path(args.analysis_receipt).resolve()
    output = Path(args.out_manifest).resolve()
    template = load_json(TEMPLATE_PATH, "report_template")

    for path, label in ((docx, "docx"), (pdf, "pdf"), (receipt, "analysis_receipt")):
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"{label}_missing_or_empty")
    if errors:
        return {"schema": "FEILONG_ANALYSIS_WORD_MANIFEST_V1", "status": "BLOCKED", "errors": errors}

    if docx.suffix.casefold() != ".docx":
        errors.append("artifact_extension_not_docx")
    if pdf.suffix.casefold() != ".pdf" or pdf.read_bytes()[:4] != b"%PDF":
        errors.append("pdf_invalid")
    if args.word_pages < int(template["layout_contract"]["min_pages"]):
        errors.append("word_page_count_below_minimum")
    if args.word_pages > int(template["layout_contract"]["max_pages"]):
        errors.append("word_page_count_above_maximum")

    try:
        text = extract_docx_text(docx)
    except RuntimeError as exc:
        text = ""
        errors.append(str(exc))
    required_groups = (
        template.get("required_sections", []),
        template.get("required_subsystems", []),
        template.get("required_risk_categories", []),
        template.get("required_terms", []),
    )
    required_terms = [str(term) for group in required_groups for term in group]
    errors.extend(f"required_term_missing:{term}" for term in required_terms if term not in text)
    errors.extend(
        f"forbidden_process_term_present:{term}"
        for term in template.get("forbidden_process_terms", [])
        if str(term) in text
    )
    errors.extend(validate_receipt(receipt, args.effective_date))
    for clean, label in (
        (args.word_opened, "word_opened"),
        (args.pdf_exported, "pdf_exported"),
        (args.visual_qa_clean, "visual_qa"),
    ):
        if not clean:
            errors.append(f"{label}_not_clean")

    status = "CLEAN_PASS" if not errors else "BLOCKED"
    return {
        "schema": "FEILONG_ANALYSIS_WORD_MANIFEST_V1",
        "status": status,
        "skill_id": SKILL_ID,
        "effective_trading_date": args.effective_date,
        "template": evidence(TEMPLATE_PATH),
        "rules_engine": evidence(Path(__file__)),
        "analysis_receipt": evidence(receipt),
        "artifact": evidence(docx),
        "pdf": evidence(pdf),
        "validation": {
            "status": status,
            "errors": errors,
            "word_opened": bool(args.word_opened),
            "word_pages": args.word_pages,
            "pdf_exported": bool(args.pdf_exported),
            "visual_qa_clean": bool(args.visual_qa_clean),
            "required_term_count": len(required_terms),
            "required_term_missing_count": sum(
                error.startswith("required_term_missing:") for error in errors
            ),
            "forbidden_term_hit_count": sum(
                error.startswith("forbidden_process_term_present:") for error in errors
            ),
        },
        "errors": errors,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", required=True)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--analysis-receipt", required=True)
    parser.add_argument("--effective-date", required=True)
    parser.add_argument("--word-pages", required=True, type=int)
    parser.add_argument("--word-opened", action="store_true")
    parser.add_argument("--pdf-exported", action="store_true")
    parser.add_argument("--visual-qa-clean", action="store_true")
    parser.add_argument("--out-manifest", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_manifest(args)
    output = Path(args.out_manifest).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0 if manifest.get("status") == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
