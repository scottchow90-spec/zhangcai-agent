#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse, hashlib, json
from pathlib import Path
from PIL import Image
from poster_builder import BANNED_TEXT, CONCLUSION_KEYS, HEIGHT, POLICY, WIDTH

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate(poster: Path, audit: dict) -> list[str]:
    errors: list[str] = []
    with Image.open(poster) as image:
        if image.size != (WIDTH, HEIGHT): errors.append("poster_dimensions_invalid")
    if audit.get("schema") != "LONGHUBANG_POSTER_DRAFT_V2": errors.append("poster_audit_schema_invalid")
    if audit.get("policy") != POLICY: errors.append("poster_policy_invalid")
    font_audit = audit.get("font_scale_audit") or {}
    if font_audit.get("status") != "PASS" or float(font_audit.get("min_preview_px") or 0) < 22 or float(font_audit.get("body_preview_px") or 0) < 32 or float(font_audit.get("heading_preview_px") or 0) < 45 or float(font_audit.get("primary_preview_px") or 0) < 34: errors.append("poster_preview_font_size_invalid")
    readability = audit.get("readability_metrics") or {}
    if readability.get("status") != "CLEAN_PASS" or int(readability.get("poster_count") or 0) != len(audit.get("pages") or []): errors.append("poster_readability_metrics_invalid")
    if audit.get("visible_stock_count") != audit.get("stock_count"): errors.append("poster_stock_coverage_invalid")
    binding = audit.get("analysis_binding") or {}
    if binding.get("status") != "CLEAN_PASS" or binding.get("required_section_keys") != CONCLUSION_KEYS or not binding.get("conclusion_sha256"): errors.append("poster_analysis_binding_invalid")
    pages = audit.get("pages") or []; visible_keys = [key for page in pages for key in page.get("conclusion_keys", [])]
    if visible_keys != CONCLUSION_KEYS or audit.get("visible_conclusion_keys") != CONCLUSION_KEYS: errors.append("poster_conclusion_coverage_invalid")
    if any(not page.get("conclusion_texts") or any(not str(text).strip() for text in page.get("conclusion_texts", [])) for page in pages): errors.append("poster_conclusion_text_missing")
    visible = json.dumps({"binding": binding, "pages": pages}, ensure_ascii=False)
    if any(token in visible for token in BANNED_TEXT): errors.append("poster_placeholder_text_forbidden")
    current_hash = sha256(poster)
    if current_hash not in {str(page.get("candidate_sha256") or "") for page in pages}: errors.append("poster_hash_not_in_audit")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--poster", required=True); parser.add_argument("--audit", required=True)
    args = parser.parse_args(); poster = Path(args.poster); audit = json.loads(Path(args.audit).read_text(encoding="utf-8")); errors = validate(poster, audit)
    payload = {"status": "CLEAN_PASS" if not errors else "BLOCKED", "poster": str(poster.resolve()), "errors": errors}
    print(json.dumps(payload, ensure_ascii=False, indent=2)); return 0 if not errors else 2

if __name__ == "__main__": raise SystemExit(main())
