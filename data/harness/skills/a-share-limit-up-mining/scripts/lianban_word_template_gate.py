#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""连板挖掘 Word 模板硬闸 v2.1 — 15道可执行闸。
G7: 豁免T3涨停统计列。 G10: 允许日期带时间戳。 G14: 豁免已知AK补充股。
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import argparse, json, sys, zipfile, xml.etree.ElementTree as ET, re
from pathlib import Path
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
FORBIDDEN_TERMS = [
    "数据来源与最新性验收",
    "当日未形成可复核的核心标的，结论降级为观察",
    "本次不降低阈值，仅保留观察名单",
    "当日精品层未凑满5席，说明筛选后机会密度偏低",
    "因此不降阈值、不转为正式标的",
    "无合格候选",
    "当日无正式候选",
    "严格门槛未形成正式标的",
    "观察股未同时满足全部条件",
    "维持观察，不列入正式候选",
    "本段展示当日执行后的结构化结果",
    "涨停池、连板股、首板、一进二候选和精品层结论已根据当日数据写入",
    "默认结论",
    "固定措辞",
    "兜底判断",
    "上榜只能证明交易活跃和辨识度",
    "新闻主要用于确认",
    "高分不等于可交付候选",
    "当日应把“强度”和“可执行性”分开",
    "一进二必须同时观察",
    "当前更适合做条件化观察",
    "本节无可用数据",
]
PLAIN_LANGUAGE_FORBIDDEN_TERMS = [
    "完整复核链", "样本口径", "证据覆盖", "风险接口", "正文与全量数据分工",
    "板块映射", "D与D-1", "证据绑定", "盘外热度", "严格样本", "全量矩阵",
    "主线共振", "风险裁决", "分层影响", "验证口径", "裁决", "证据缺口",
    "复核状态", "数据完整性结论", "矩阵", "K线", "八因子", "深析范围",
    "本次裁决", "资金承接裁决",
    "资料齐全", "不足之处",
]
REQUIRED_STRUCTURE = ["最终结果","第一步","第二步","第三步","第四步","第五步","第六步","第七步","第八步","第九步","第十步"]
KPI_KEYWORDS = ["涨停池","连板股","首板","一进二候选","精品"]
FIRST_H1_MUST = "最终结果"
TODAY = datetime.now().strftime("%Y-%m-%d")
TEMPLATE_OLD_STOCKS = ["软通动力","北玻股份","粤电力","合锻智能","粤电力Ａ","模板字段"]
BLANK_PLACEHOLDERS = ["-", "--", "N/A", "n/a", "待核验", "缺失", ""]
# G7豁免: T3(涨停清单)C4=涨停统计(无昨日数据可空)
G7_EXEMPT = {(3,4), (3,9)}
# G14豁免: AK补充股
G14_KNOWN_EXTRA = {"600696"}


def cross_check_codes_with_ztc(document_codes, ztc_codes):
    """Return passive ZTC cross-check evidence without excluding document rows."""
    doc_set = {
        str(code).strip()
        for code in document_codes
        if str(code).strip().isdigit() and len(str(code).strip()) == 6
    }
    ztc_set = {
        str(code).strip()
        for code in ztc_codes
        if str(code).strip().isdigit()
        and len(str(code).strip()) == 6
        and str(code).strip() != "000000"
    }
    return {
        "reference_count": len(ztc_set),
        "intersection": sorted(doc_set & ztc_set),
        "conflicts": sorted(doc_set - ztc_set),
        "excluded_count": 0,
    }


QSYB_HEADERS = [
    "\u4ee3\u7801",
    "\u540d\u79f0",
    "\u62a5\u544a\u540d\u79f0",
    "\u8bc4\u7ea7",
    "\u673a\u6784",
    "\u884c\u4e1a",
    "\u65e5\u671f",
]
RDXZ_HEADERS = [
    "\u4ee3\u7801",
    "\u540d\u79f0",
    "\u65b0\u95fb\u6807\u9898",
    "\u65b0\u95fb\u5185\u5bb9",
    "\u53d1\u5e03\u65f6\u95f4",
    "\u6765\u6e90",
]
BOUND_BLANK_PLACEHOLDERS = {"", "-", "--", "N/A", "n/a", "\u5f85\u6838\u9a8c", "\u7f3a\u5931"}
GENERIC_MARKET_TERMS = [
    "\u8bc1\u5238\u805a\u7126",
    "\u4e1c\u65b9\u8d22\u5bcc\u8bc1\u5238\u805a\u7126",
    "\u6cdb\u5e02\u573a",
    "\u5e02\u573a\u70ed\u70b9",
]
GENERIC_RATING_TERMS = {"\u53c2\u8003", "\u6682\u65e0", "-", "--", ""}


def norm_cell(value) -> str:
    return re.sub(r"\s+", "", str(value or "").strip())


def is_blank_placeholder(value) -> bool:
    return norm_cell(value) in BOUND_BLANK_PLACEHOLDERS


def is_stock_code(value) -> bool:
    return re.fullmatch(r"\d{6}", norm_cell(value)) is not None


def has_chinese_name(value) -> bool:
    text = str(value or "").strip()
    return (not is_blank_placeholder(text)) and re.search(r"[\u4e00-\u9fff]", text) is not None


def find_table_by_exact_headers(tables, required_headers):
    required = [norm_cell(h) for h in required_headers]
    for ti, tbl in enumerate(tables):
        for hi, row in enumerate(tbl[:3]):
            cells = [norm_cell(c) for c in row]
            columns = {}
            for header in required:
                if header in cells:
                    columns[header] = cells.index(header)
            if len(columns) == len(required):
                return {"table_index": ti, "header_row": hi, "columns": columns, "header": row}
    return None


def cell_at(row, idx) -> str:
    if idx is None or idx >= len(row):
        return ""
    return str(row[idx] or "").strip()


def validate_bound_table_rows(tables, allow_empty_qsyb: bool = False) -> dict:
    blocks = []
    evidence = {}

    qsyb = find_table_by_exact_headers(tables, QSYB_HEADERS)
    evidence["qsyb_found"] = qsyb is not None
    if not qsyb:
        blocks.append("G16_BLOCKED_QSYB_TABLE_NOT_FOUND_BY_HEADERS")
    else:
        qcols = qsyb["columns"]
        qtbl = tables[qsyb["table_index"]]
        q_rows = qtbl[qsyb["header_row"] + 1:]
        bad_codes, bad_names, bad_blanks, generic_rows, bad_ratings = [], [], [], [], []
        for offset, row in enumerate(q_rows, start=1):
            label = f"T{qsyb['table_index']}R{qsyb['header_row'] + offset}"
            code = cell_at(row, qcols[QSYB_HEADERS[0]])
            name = cell_at(row, qcols[QSYB_HEADERS[1]])
            rating = cell_at(row, qcols[QSYB_HEADERS[3]])
            joined = "|".join(cell_at(row, qcols[h]) for h in QSYB_HEADERS)
            if not is_stock_code(code):
                bad_codes.append(f"{label}:code={repr(code)}")
            if not has_chinese_name(name):
                bad_names.append(f"{label}:name={repr(name)}")
            for h in QSYB_HEADERS:
                value = cell_at(row, qcols[h])
                if is_blank_placeholder(value):
                    bad_blanks.append(f"{label}:{h}={repr(value)}")
            if norm_cell(rating) in GENERIC_RATING_TERMS:
                bad_ratings.append(f"{label}:rating={repr(rating)}")
            if any(term in joined for term in GENERIC_MARKET_TERMS):
                generic_rows.append(f"{label}:generic_market_source")
        evidence["qsyb_table_index"] = qsyb["table_index"]
        evidence["qsyb_rows"] = len(q_rows)
        evidence["qsyb_bad_codes"] = bad_codes[:20]
        evidence["qsyb_bad_names"] = bad_names[:20]
        evidence["qsyb_blank_fields"] = bad_blanks[:20]
        evidence["qsyb_generic_market_rows"] = generic_rows[:20]
        evidence["qsyb_bad_ratings"] = bad_ratings[:20]
        evidence["qsyb_empty_allowed_for_zero_picks"] = bool(not q_rows and allow_empty_qsyb)
        if not q_rows and not allow_empty_qsyb:
            blocks.append("G16_BLOCKED_QSYB_NO_DATA_ROWS")
        if bad_codes:
            blocks.append(f"G16_BLOCKED_QSYB_CODE_NOT_BOUND: {len(bad_codes)} rows")
        if bad_names:
            blocks.append(f"G16_BLOCKED_QSYB_NAME_NOT_BOUND: {len(bad_names)} rows")
        if bad_blanks:
            blocks.append(f"G16_BLOCKED_QSYB_BLANK_FIELDS: {len(bad_blanks)} cells")
        if bad_ratings:
            blocks.append(f"G16_BLOCKED_QSYB_GENERIC_RATING: {len(bad_ratings)} rows")
        if generic_rows:
            blocks.append(f"G16_BLOCKED_QSYB_GENERIC_MARKET_SOURCE: {len(generic_rows)} rows")

    rdxz = find_table_by_exact_headers(tables, RDXZ_HEADERS)
    evidence["rdxz_found"] = rdxz is not None
    if not rdxz:
        blocks.append("G17_BLOCKED_RDXZ_TABLE_NOT_FOUND_BY_HEADERS")
    else:
        rcols = rdxz["columns"]
        rtbl = tables[rdxz["table_index"]]
        r_rows = rtbl[rdxz["header_row"] + 1:]
        bad_codes, bad_names, bad_blanks, unbound_news = [], [], [], []
        for offset, row in enumerate(r_rows, start=1):
            label = f"T{rdxz['table_index']}R{rdxz['header_row'] + offset}"
            code = cell_at(row, rcols[RDXZ_HEADERS[0]])
            name = cell_at(row, rcols[RDXZ_HEADERS[1]])
            title = cell_at(row, rcols[RDXZ_HEADERS[2]])
            content = cell_at(row, rcols[RDXZ_HEADERS[3]])
            searchable = title + "\n" + content
            if not is_stock_code(code):
                bad_codes.append(f"{label}:code={repr(code)}")
            if not has_chinese_name(name):
                bad_names.append(f"{label}:name={repr(name)}")
            for h in RDXZ_HEADERS:
                value = cell_at(row, rcols[h])
                if is_blank_placeholder(value):
                    bad_blanks.append(f"{label}:{h}={repr(value)}")
            if is_stock_code(code) and has_chinese_name(name) and code not in searchable and name not in searchable:
                unbound_news.append(f"{label}:news_mentions_neither_code_nor_name")
        evidence["rdxz_table_index"] = rdxz["table_index"]
        evidence["rdxz_rows"] = len(r_rows)
        evidence["rdxz_bad_codes"] = bad_codes[:20]
        evidence["rdxz_bad_names"] = bad_names[:20]
        evidence["rdxz_blank_fields"] = bad_blanks[:20]
        evidence["rdxz_unbound_news"] = unbound_news[:20]
        if not r_rows:
            blocks.append("G17_BLOCKED_RDXZ_NO_DATA_ROWS")
        if bad_codes:
            blocks.append(f"G17_BLOCKED_RDXZ_CODE_NOT_BOUND: {len(bad_codes)} rows")
        if bad_names:
            blocks.append(f"G17_BLOCKED_RDXZ_NAME_NOT_BOUND: {len(bad_names)} rows")
        if bad_blanks:
            blocks.append(f"G17_BLOCKED_RDXZ_BLANK_FIELDS: {len(bad_blanks)} cells")
        if unbound_news:
            blocks.append(f"G17_BLOCKED_RDXZ_NEWS_NOT_STOCK_BOUND: {len(unbound_news)} rows")

    return {"blocks": blocks, "evidence": evidence}


def extract_full(docx_path: Path):
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        root = ET.fromstring(xml.encode("utf-8"))
        paras = []
        for p in root.findall(".//w:p", NS):
            text = "".join(t.text or "" for t in p.findall(".//w:t", NS)).strip()
            st = ""
            ps = p.find("w:pPr/w:pStyle", NS)
            if ps is not None: st = ps.attrib.get(f"{{{NS['w']}}}val", "")
            if text: paras.append({"text": text, "style": st})
        body_paras = []
        body_sequence = []
        body = root.find("w:body", NS)
        if body is not None:
            table_index = 0
            for p in body.findall("w:p", NS):
                text = "".join(t.text or "" for t in p.findall(".//w:t", NS)).strip()
                st = ""
                ps = p.find("w:pPr/w:pStyle", NS)
                if ps is not None: st = ps.attrib.get(f"{{{NS['w']}}}val", "")
                if text: body_paras.append({"text": text, "style": st})
            for child in list(body):
                tag = child.tag.rsplit("}", 1)[-1]
                if tag == "p":
                    text = "".join(t.text or "" for t in child.findall(".//w:t", NS)).strip()
                    st = ""
                    ps = child.find("w:pPr/w:pStyle", NS)
                    if ps is not None: st = ps.attrib.get(f"{{{NS['w']}}}val", "")
                    if text: body_sequence.append({"kind": "p", "text": text, "style": st})
                elif tag == "tbl":
                    body_sequence.append({"kind": "tbl", "table_index": table_index})
                    table_index += 1
        tables = []
        for tbl in root.findall(".//w:tbl", NS):
            rows_data = []
            for tr in tbl.findall("w:tr", NS):
                cells = []
                for tc in tr.findall("w:tc", NS):
                    ct = "".join(t.text or "" for t in tc.findall(".//w:t", NS))
                    cells.append(ct)
                rows_data.append(cells)
            tables.append(rows_data)
        full_text = "\n".join(p["text"] for p in paras)
        h1s = [p for p in paras if p["style"] == "Heading1"]
        table_font_half_points = []
        exact_row_heights = 0
        for tbl in root.findall(".//w:tbl", NS):
            for size_node in tbl.findall(".//w:rPr/w:sz", NS):
                raw_size = size_node.attrib.get(f"{{{NS['w']}}}val", "")
                if str(raw_size).isdigit(): table_font_half_points.append(int(raw_size))
            for height_node in tbl.findall(".//w:trPr/w:trHeight", NS):
                if height_node.attrib.get(f"{{{NS['w']}}}hRule", "") == "exact": exact_row_heights += 1
        return {
            "path": str(docx_path), "size": docx_path.stat().st_size,
            "paras": paras, "body_paras": body_paras, "body_sequence": body_sequence,
            "full_text": full_text, "h1s": h1s, "tables": tables,
            "table_count": len(tables), "table_font_half_points": table_font_half_points,
            "exact_row_heights": exact_row_heights,
            "first_120": "\n".join(p["text"] for p in paras[:120]),
            "first_60": "\n".join(p["text"] for p in paras[:60]),
        }


def validate(docx_path: Path, audit_path: Path | None = None) -> dict:
    if not docx_path.exists():
        return {"status": "BLOCKED", "blocks": [f"docx not found: {docx_path}"], "evidence": {}}
    data = extract_full(docx_path)
    blocks = []; evidence = {}
    full = data["full_text"]; f120 = data["first_120"]; f60 = data["first_60"]; h1s = data["h1s"]
    formal_zero = re.search(r"正式候选(?:为)?0只", full) is not None
    evidence_zero = re.search(r"逐股裁决", full) is not None or ("证据缺口" in full and "技术结构" in full)
    allow_empty_qsyb = formal_zero and evidence_zero
    yijiner_zero = re.search(r"一进二(?:正式)?候选(?:池共|为)?0只", full) is not None

    # G13: 预构建审计
    audit_json = audit_path or Path(str(docx_path).replace(".docx", "_prebuild_audit.json"))
    evidence["g13_prebuild_audit_path"] = str(audit_json)
    evidence["g13_audit_found"] = audit_json.exists()
    if not audit_json.exists():
        blocks.append(f"G13_BLOCKED_NO_PREBUILD_AUDIT: {audit_json} not found")
    else:
        try:
            audit_data = json.loads(audit_json.read_text(encoding="utf-8"))
            evidence["g13_audit_status"] = audit_data.get("status", "UNKNOWN")
            if audit_data.get("status") != "AUDIT_CLEAN":
                blocks.append(f"G13_BLOCKED_PREBUILD_AUDIT_FAILED: {audit_data.get('blocks', [])}")
        except Exception as e:
            blocks.append(f"G13_BLOCKED_AUDIT_JSON_READ_ERROR: {type(e).__name__}")

    # G14: ZTC is a passive cross-check, not the current-day stock universe.
    try:
        ztc_content = Path(r"C:\new_tdx_mock\T0002\blocknew\ZTC.blk").read_text(encoding="gbk", errors="ignore")
        ztc_codes = []
        for line in ztc_content.splitlines():
            if line.strip():
                code = line.strip()[-6:] if len(line.strip()) >= 6 else line.strip()
                if code.isdigit() and len(code) == 6:
                    ztc_codes.append(code)
        document_codes = []
        if len(data["tables"]) > 3:
            t3 = data["tables"][3]
            for ri in range(1, len(t3)):
                if t3[ri]:
                    codes_in_cell = re.findall(r'\b(\d{6})\b', t3[ri][0].strip())
                    document_codes.extend(codes_in_cell)
        cross_check = cross_check_codes_with_ztc(document_codes, ztc_codes)
        evidence["g14_ztc_reference_count"] = cross_check["reference_count"]
        evidence["g14_ztc_intersection"] = cross_check["intersection"][:20]
        evidence["g14_ztc_conflicts"] = cross_check["conflicts"][:20]
        evidence["g14_excluded_count"] = cross_check["excluded_count"]
    except Exception as e:
        evidence["g14_error"] = str(e)[:200]

    # G15: 标题存在性
    title_ok = any("连板挖掘全流程选股报告" in p["text"] for p in data["paras"])
    evidence["g15_title_ok"] = title_ok
    if not title_ok: blocks.append("G15_BLOCKED_TITLE_NOT_FOUND")

    # G1
    evidence["g1_first_h1"] = h1s[0]["text"] if h1s else "NO_HEADING1"
    evidence["g1_result_in_first120"] = "最终结果" in f120
    if not h1s or h1s[0]["text"] != FIRST_H1_MUST:
        blocks.append(f"G1_BLOCKED_FIRST_H1_NOT_RESULT: got '{h1s[0]['text'] if h1s else 'NONE'}'")
    if not evidence["g1_result_in_first120"]: blocks.append("G1_BLOCKED_RESULT_NOT_IN_FIRST120")

    # G2
    forbidden_hits = [t for t in FORBIDDEN_TERMS if t in full]
    plain_language_hits = [t for t in PLAIN_LANGUAGE_FORBIDDEN_TERMS if t in full]
    english_hits = sorted(set(re.findall(r"[A-Za-z]", full)))
    evidence["g2_forbidden_hits"] = forbidden_hits
    evidence["g2_plain_language_hits"] = plain_language_hits
    evidence["g2_english_letters"] = english_hits
    if forbidden_hits: blocks.append(f"G2_BLOCKED_FORBIDDEN_TERMS: {forbidden_hits}")
    if plain_language_hits: blocks.append(f"G2_BLOCKED_PROCESS_OR_JARGON: {plain_language_hits}")
    if english_hits: blocks.append(f"G2_BLOCKED_ENGLISH_LETTERS: {english_hits}")

    # G3
    step_check = {s: s in full for s in ["第一步","第二步","第三步","第四步","第五步"]}
    evidence["g3_steps"] = step_check
    if missing := [k for k, v in step_check.items() if not v]: blocks.append(f"G3_BLOCKED_MISSING_STEPS: {missing}")

    # G4
    h1_texts = [h["text"] for h in h1s]
    evidence["g4_h1_texts"] = h1_texts
    matched = sum(1 for rs in REQUIRED_STRUCTURE if any(rs in h for h in h1_texts))
    evidence["g4_structure_match"] = f"{matched}/{len(REQUIRED_STRUCTURE)}"
    if matched < 8: blocks.append(f"G4_BLOCKED_STRUCTURE_MATCH: {matched}/11 < 8")
    narrative_paras = [p for p in data.get("body_paras", []) if not str(p.get("style", "")).startswith("Heading")]
    narrative_chars = sum(len(p.get("text", "")) for p in narrative_paras)
    overlong_paragraphs = [
        {"index": index, "length": len(p.get("text", "")), "text": p.get("text", "")[:80]}
        for index, p in enumerate(narrative_paras)
        if len(p.get("text", "")) > 220
    ]
    detail_markers = [
        "最近两天", "资金情况", "八项评分", "最新消息", "风险", "次日怎么看",
        "看了多少只", "资金数字", "资金结论", "研报判断", "新闻内容", "消息影响",
    ]
    missing_detail_markers = [marker for marker in detail_markers if marker not in full]
    reviewed_names = list(dict.fromkeys(re.findall(r"\d{6}\s+([^｜\r\n]+)｜资金判断", full)))
    shallow_stock_coverage = [name for name in reviewed_names if full.count(name) < 5]
    concrete_block_counts = {
        "资金数字": full.count("资金数字"),
        "资金结论": full.count("资金结论"),
        "研报判断": full.count("研报判断"),
        "新闻内容": full.count("新闻内容"),
        "消息影响": full.count("消息影响"),
        "最终结果": full.count("最终结果"),
    }
    expected_concrete_blocks = len(reviewed_names)
    insufficient_concrete_blocks = [
        name for name, count in concrete_block_counts.items()
        if expected_concrete_blocks < 5 or count < expected_concrete_blocks
    ]
    evidence["g4_narrative_paragraphs"] = len(narrative_paras)
    evidence["g4_narrative_characters"] = narrative_chars
    evidence["g4_overlong_paragraphs"] = overlong_paragraphs
    evidence["g4_missing_detail_markers"] = missing_detail_markers
    evidence["g4_shallow_stock_coverage"] = shallow_stock_coverage
    evidence["g4_reviewed_names"] = reviewed_names
    evidence["g4_expected_concrete_blocks"] = expected_concrete_blocks
    evidence["g4_concrete_block_counts"] = concrete_block_counts
    evidence["g4_insufficient_concrete_blocks"] = insufficient_concrete_blocks
    if len(narrative_paras) < 45: blocks.append(f"G4_BLOCKED_OUTLINE_LIKE_PARAGRAPHS: {len(narrative_paras)} < 45")
    if narrative_chars < 5000: blocks.append(f"G4_BLOCKED_OUTLINE_LIKE_CONTENT: {narrative_chars} < 5000 chars")
    if narrative_chars > 9500: blocks.append(f"G4_BLOCKED_NARRATIVE_TOO_LONG: {narrative_chars} > 9500 chars")
    if overlong_paragraphs: blocks.append(f"G4_BLOCKED_PARAGRAPH_TOO_LONG: {len(overlong_paragraphs)} paragraphs > 220 chars")
    if missing_detail_markers: blocks.append(f"G4_BLOCKED_MISSING_DETAILED_ANALYSIS: {missing_detail_markers}")
    if shallow_stock_coverage: blocks.append(f"G4_BLOCKED_SHALLOW_STOCK_COVERAGE: {shallow_stock_coverage}")
    if insufficient_concrete_blocks: blocks.append(f"G4_BLOCKED_GENERIC_ANALYSIS_BLOCKS: {insufficient_concrete_blocks}")

    # G4 layout: reject text-wall pages and end-loaded table dumps.
    sequence = data.get("body_sequence", [])
    first_table_position = next((i for i, item in enumerate(sequence) if item.get("kind") == "tbl"), -1)
    max_consecutive_tables = 0
    max_plain_paragraph_run = 0
    table_run = 0
    plain_run = 0
    current_section = "前置"
    section_table_counts = {}
    for item in sequence:
        if item.get("kind") == "tbl":
            table_run += 1
            plain_run = 0
            max_consecutive_tables = max(max_consecutive_tables, table_run)
            section_table_counts[current_section] = section_table_counts.get(current_section, 0) + 1
            continue
        table_run = 0
        style = str(item.get("style", ""))
        text = str(item.get("text", ""))
        if style == "Heading1":
            current_section = text
            section_table_counts.setdefault(current_section, 0)
            plain_run = 0
        elif style.startswith("Heading"):
            plain_run = 0
        else:
            plain_run += 1
            max_plain_paragraph_run = max(max_plain_paragraph_run, plain_run)
    required_section_tables = {
        "最终结果": 2, "第二步": 1, "第三步": 2, "第四步": 1, "第五步": 2,
        "第六步": 2, "第七步": 2, "第八步": 2, "第九步": 1, "第十步": 1,
    }
    missing_section_tables = []
    for prefix, minimum in required_section_tables.items():
        matched_count = sum(count for name, count in section_table_counts.items() if name.startswith(prefix))
        if matched_count < minimum:
            missing_section_tables.append(f"{prefix}:{matched_count}<{minimum}")
    table_sizes = data.get("table_font_half_points", [])
    min_table_font_pt = (min(table_sizes) / 2) if table_sizes else 0
    exact_row_heights = int(data.get("exact_row_heights", 0) or 0)
    evidence["g4_layout_first_table_position"] = first_table_position
    evidence["g4_layout_max_consecutive_tables"] = max_consecutive_tables
    evidence["g4_layout_max_plain_paragraph_run"] = max_plain_paragraph_run
    evidence["g4_layout_section_table_counts"] = section_table_counts
    evidence["g4_layout_missing_section_tables"] = missing_section_tables
    evidence["g4_layout_min_table_font_pt"] = min_table_font_pt
    evidence["g4_layout_exact_row_heights"] = exact_row_heights
    if first_table_position < 0 or first_table_position > 12:
        blocks.append(f"G4_BLOCKED_TABLES_END_LOADED: first table at {first_table_position}")
    if max_consecutive_tables > 2:
        blocks.append(f"G4_BLOCKED_TABLE_DUMP: {max_consecutive_tables} consecutive tables")
    if max_plain_paragraph_run > 9:
        blocks.append(f"G4_BLOCKED_TEXT_WALL: {max_plain_paragraph_run} consecutive plain paragraphs")
    if missing_section_tables:
        blocks.append(f"G4_BLOCKED_TABLES_NOT_NEAR_ANALYSIS: {missing_section_tables}")
    if min_table_font_pt < 8.5:
        blocks.append(f"G4_BLOCKED_TABLE_FONT_TOO_SMALL: {min_table_font_pt}pt < 8.5pt")
    if exact_row_heights:
        blocks.append(f"G4_BLOCKED_FIXED_ROW_HEIGHTS: {exact_row_heights}")

    # G5
    kpi_check = {k: k in f60 for k in KPI_KEYWORDS}
    evidence["g5_kpi"] = kpi_check
    if kpi_missing := [k for k, v in kpi_check.items() if not v]: blocks.append(f"G5_BLOCKED_KPI_MISSING_IN_OPENING: {kpi_missing}")

    # G6
    stocks = set(re.findall(r"\d{6}\s+\S+", full))
    evidence["g6_stock_count"] = len(stocks)
    if len(stocks) < 5: blocks.append(f"G6_BLOCKED_TOO_FEW_NAMED_STOCKS: {len(stocks)}")

    # G7: 豁免T3C4(涨停统计)
    blank_cells = []
    for ti, tbl in enumerate(data["tables"]):
        if len(tbl) < 2: continue
        for ri in range(1, len(tbl)):
            for ci, cell_text in enumerate(tbl[ri]):
                stripped = cell_text.strip()
                if (ti, ci) in G7_EXEMPT: continue
                if stripped in BLANK_PLACEHOLDERS:
                    blank_cells.append(f"T{ti}R{ri}C{ci}={repr(stripped)}")
    evidence["g7_blank_cells"] = blank_cells[:20]
    if blank_cells: blocks.append(f"G7_BLOCKED_BLANK_CELLS: {len(blank_cells)} cells. First: {blank_cells[:5]}")

    # G8: T6/T7代码
    for ti in [6,7]:
        if ti < len(data["tables"]):
            fake = []
            for ri in range(1, len(data["tables"][ti])):
                if data["tables"][ti][ri]:
                    code = data["tables"][ti][ri][0].strip()
                    if not re.match(r"^\d{6}$", code): fake.append(f"R{ri}: {repr(code)}")
            evidence[f"g8_t{ti}_fake_codes"] = fake[:10]
            if fake: blocks.append(f"G8_BLOCKED_T{ti}_FAKE_CODES: {len(fake)} rows")

    # G9: T6/T7名称
    for ti in [6,7]:
        if ti < len(data["tables"]):
            fake = []
            for ri in range(1, len(data["tables"][ti])):
                if len(data["tables"][ti][ri]) > 1:
                    name = data["tables"][ti][ri][1].strip()
                    if name in BLANK_PLACEHOLDERS or (not re.search(r"[\u4e00-\u9fff]", name)):
                        fake.append(f"R{ri}: {repr(name)}")
            evidence[f"g9_t{ti}_fake_names"] = fake[:10]
            if fake: blocks.append(f"G9_BLOCKED_T{ti}_FAKE_NAMES: {len(fake)} rows")

    # G10: 日期必须是真实日期。QSYB 是研报发布日期，不要求等于今天；RDXZ 是新闻发布时间，允许带时间戳。
    invalid_dates = []
    for ti, date_col in [(6,6),(7,4)]:
        if ti < len(data["tables"]):
            for ri in range(1, len(data["tables"][ti])):
                if date_col < len(data["tables"][ti][ri]):
                    dt = data["tables"][ti][ri][date_col].strip()
                    if not re.match(r"^\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}(?::\d{2})?)?$", dt):
                        invalid_dates.append(f"T{ti}R{ri}: {dt}")
    evidence["g10_invalid_dates"] = invalid_dates[:10]
    if invalid_dates: blocks.append(f"G10_BLOCKED_INVALID_DATES: {len(invalid_dates)} cells")

    # G11
    old_hits = [s for s in TEMPLATE_OLD_STOCKS if s in full]
    evidence["g11_template_residual"] = old_hits
    if old_hits: blocks.append(f"G11_BLOCKED_TEMPLATE_RESIDUAL: {old_hits}")

    # G12
    empty_tables = []
    for ti in [3,4,5,6,7,8,10,11]:
        if ti < len(data["tables"]) and len(data["tables"][ti]) < 2:
            if ti == 6 and allow_empty_qsyb:
                continue
            if ti == 11 and yijiner_zero:
                continue
            empty_tables.append(f"T{ti}")
    evidence["g12_empty_tables"] = empty_tables
    evidence["g12_qsyb_empty_allowed_for_zero_picks"] = allow_empty_qsyb
    evidence["g12_yijiner_empty_allowed_for_zero_candidates"] = yijiner_zero
    if empty_tables: blocks.append(f"G12_BLOCKED_EMPTY_TABLES: {empty_tables}")

    evidence["tables"] = data["table_count"]
    evidence["size"] = data["size"]

    bound_table_check = validate_bound_table_rows(data["tables"], allow_empty_qsyb=allow_empty_qsyb)
    evidence["g16_g17_bound_tables"] = bound_table_check["evidence"]
    blocks.extend(bound_table_check["blocks"])

    status = "CLEAN_PASS" if not blocks else "BLOCKED"
    return {"status": status, "blocks": blocks, "evidence": evidence}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docx", required=True)
    ap.add_argument("--audit-path", help="显式指定预构建审计旁证，便于验收复制后的最终 Word")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    res = validate(Path(args.docx), Path(args.audit_path) if args.audit_path else None)
    if args.json: print(json.dumps(res, ensure_ascii=False, indent=2))
    else: print(res["status"])
    if res["status"] == "BLOCKED": raise SystemExit(2)


if __name__ == "__main__": main()
