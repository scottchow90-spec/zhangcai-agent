#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_docx.py - Build lianban docx from template + analyzed data."""
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
import os
import re
import sys
import warnings
from pathlib import Path

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_data_root

_SKILL_ROOT = Path(__file__).resolve().parents[1]
_WORKSPACE_DATA = resolve_data_root() / "strategy-data" / "a-share-limit-up-mining"
_DEFAULT_TEMPLATE = _SKILL_ROOT / "assets" / "连板挖掘模板.docx"

warnings.filterwarnings('ignore')
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


def validate_risk_collection_scope(raw_data, zt_scored):
    """Validate risk review against the complete raw daily limit-up pool."""
    raw_codes = {
        str(row.get('code', '')).strip()
        for row in (raw_data.get('zt_pool') or [])
        if isinstance(row, dict) and str(row.get('code', '')).strip()
    }
    risk_collection = raw_data.get('risk_collection') or {}
    expected_scope = len(raw_codes)
    input_scope = int(risk_collection.get('input_zt_pool_codes', 0) or 0)
    probed_scope = int(risk_collection.get('codes_probed', 0) or 0)
    complete_scope = int(risk_collection.get('review_complete_codes', 0) or 0)
    has_expected_scope = expected_scope > 0

    return {
        'expected_scope': expected_scope,
        'filtered_scope': len(zt_scored),
        'input_scope': input_scope,
        'probed_scope': probed_scope,
        'complete_scope': complete_scope,
        'risk_errors': not bool(risk_collection.get('errors')),
        'risk_scope': (
            has_expected_scope
            and input_scope == expected_scope
            and probed_scope == expected_scope
        ),
        'risk_complete': has_expected_scope and complete_scope == expected_scope,
    }


def to_yi(amount):
    if amount is None or amount == 0:
        return '0'
    a = abs(amount)
    if a >= 1e8:
        return f"{amount/1e8:.2f}\u4ebf"
    if a >= 1e4:
        return f"{amount/1e4:.0f}\u4e07"
    return f"{amount:.0f}"


def sanitize_finance_chinese(value):
    text = str(value or '')
    replacements = {
        'Choice': '精选',
        'TOP': '前列',
        'Top': '前列',
        'PCB': '印制电路板',
        'CRO': '医药研发服务',
        'CXO': '医药研发生产服务',
        'CPO': '光电共封装',
        'CDMO': '医药研发生产外包',
        'ESMO': '欧洲肿瘤学会',
        'LBA': '重点报告',
        'AI': '人工智能',
        'A股': '沪深股票',
        '矩阵': '组合',
        'H1': '上半年',
        'H2': '下半年',
        'Q1': '一季度',
        'Q2': '二季度',
        'Q3': '三季度',
        'Q4': '四季度',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'\.(?:SH|SZ)\b', '', text)
    text = re.sub(r'(?<=\d)[A-Za-z]+(?=\d|\b)', '', text)
    text = re.sub(r'[A-Za-z]+', '', text)
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text


def sanitize_document_visible_text(doc):
    for paragraph in doc.paragraphs:
        cleaned = sanitize_finance_chinese(paragraph.text)
        if cleaned != paragraph.text:
            _set_para_text(paragraph, cleaned)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    cleaned = sanitize_finance_chinese(paragraph.text)
                    if cleaned != paragraph.text:
                        _set_para_text(paragraph, cleaned)


def _set_para_text(para, text, font_size=82, bold=False, color=None):
    for r in list(para.runs):
        r._element.getparent().remove(r._element)
    run = para.add_run(str(text))
    from docx.shared import Pt, RGBColor
    run.font.size = Pt(font_size / 10)
    run.font.bold = bool(bold)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    return para


def set_cell_text(cell, text, font_size=82, bold=False, color=None, replace=True):
    if replace:
        for p in cell.paragraphs[1:]:
            p._element.getparent().remove(p._element)
    return _set_para_text(cell.paragraphs[0], text, font_size, bold, color)


def add_row(table, n_cols):
    return table.add_row()


def remove_row(table, row_idx):
    row = table.rows[row_idx]
    row._element.getparent().remove(row._element)


def select_summary_rows(picks, zt_scored):
    return list((picks if picks else zt_scored)[:5])


def remove_unused_section_paragraphs(paragraphs, keep):
    """Remove template prose that was not replaced by the current run."""
    for paragraph in paragraphs:
        if keep is not None and paragraph._p is keep._p:
            continue
        parent = paragraph._p.getparent()
        if parent is not None:
            parent.remove(paragraph._p)


def fill_row(table, row_idx, values, color='1E1E28', size=82, bold_first=True):
    row = table.rows[row_idx]
    for ci, val in enumerate(values):
        if ci < len(row.cells):
            set_cell_text(row.cells[ci], str(val), font_size=size,
                          bold=(ci == 0 and bold_first), color=color)


def set_table_cell_shading(cell, fill):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd')
        tc_pr.append(shd)
    shd.set(qn('w:fill'), fill)


def set_table_cell_border(cell, color='D9E2EC', size='4'):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.find(qn('w:tcBorders'))
    if borders is None:
        borders = OxmlElement('w:tcBorders')
        tc_pr.append(borders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        tag = qn(f'w:{edge}')
        border = borders.find(tag)
        if border is None:
            border = OxmlElement(f'w:{edge}')
            borders.append(border)
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), size)
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), color)


def set_table_cell_margins(cell, top=70, start=90, bottom=70, end=90):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.find(qn('w:tcMar'))
    if tc_mar is None:
        tc_mar = OxmlElement('w:tcMar')
        tc_pr.append(tc_mar)
    for edge, value in (('top', top), ('start', start), ('bottom', bottom), ('end', end)):
        node = tc_mar.find(qn(f'w:{edge}'))
        if node is None:
            node = OxmlElement(f'w:{edge}')
            tc_mar.append(node)
        node.set(qn('w:w'), str(value))
        node.set(qn('w:type'), 'dxa')


def apply_compact_result_table_style(table):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

    for row_index, row in enumerate(table.rows):
        for cell in row.cells:
            set_table_cell_margins(cell, top=30, start=70, bottom=30, end=70)
            for para in cell.paragraphs:
                _set_para_text(
                    para,
                    para.text,
                    font_size=85,
                    bold=(row_index == 0),
                    color='FFFFFF' if row_index == 0 else '1F2933',
                )
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.line_spacing = 1.0


def keep_table_header_with_first_body_row(table):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    if len(table.rows) < 2:
        return
    for cell in table.rows[0].cells:
        for para in cell.paragraphs:
            para.paragraph_format.keep_with_next = True
    first_body_properties = table.rows[1]._tr.get_or_add_trPr()
    cant_split = first_body_properties.find(qn('w:cantSplit'))
    if cant_split is None:
        cant_split = OxmlElement('w:cantSplit')
        first_body_properties.append(cant_split)
    cant_split.set(qn('w:val'), 'true')


def requires_header_body_pagination(table_index):
    return table_index == 8 or 12 <= table_index <= 16


def set_para_style(para, size=90, bold=False, color='222222', align=None, space_after=4):
    from docx.shared import Pt, RGBColor
    from docx.oxml.ns import qn
    for run in para.runs:
        run.font.name = 'Microsoft YaHei'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
        run.font.size = Pt(size / 10)
        run.font.bold = bold
        run.font.color.rgb = RGBColor.from_string(color)
    if align is not None:
        para.alignment = align
    para.paragraph_format.space_after = Pt(space_after)


def polish_document_layout(doc):
    from docx.enum.section import WD_ORIENT
    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    for section in doc.sections:
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width = Inches(11.69)
        section.page_height = Inches(8.27)
        section.top_margin = Inches(0.62)
        section.bottom_margin = Inches(0.62)
        section.left_margin = Inches(0.68)
        section.right_margin = Inches(0.68)

    for style_name in ('Normal', 'Heading 1', 'Heading 2'):
        style = doc.styles[style_name]
        style.font.name = 'Microsoft YaHei'
        style._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    doc.styles['Normal'].font.size = Pt(10.5)
    doc.styles['Normal'].paragraph_format.space_after = Pt(5)
    doc.styles['Normal'].paragraph_format.line_spacing = 1.22
    doc.styles['Heading 1'].font.size = Pt(17)
    doc.styles['Heading 1'].font.bold = True
    doc.styles['Heading 1'].font.color.rgb = RGBColor.from_string('17324D')
    doc.styles['Heading 2'].font.size = Pt(12.5)
    doc.styles['Heading 2'].font.bold = True
    doc.styles['Heading 2'].font.color.rgb = RGBColor.from_string('17324D')

    width_weights = {
        0: [1, 1, 1, 1, 1],
        1: [0.7, 1.6, 1.1, 0.7, 1.0, 3.0],
        2: [1, 1, 1, 1, 1],
        3: [1.5, 1.0, 1.0, 0.55, 0.8, 0.8, 0.8, 0.55, 0.85, 0.75],
        4: [1.4, 1.0, 1.0, 0.55, 0.75, 0.75, 0.75, 0.55, 0.6, 2.2],
        5: [1.4, 0.6, 0.6, 0.6, 0.7, 0.9, 0.9, 0.7, 0.7],
        6: [0.8, 1.0, 2.6, 0.8, 1.1, 1.1, 0.9],
        7: [0.75, 0.9, 2.2, 4.0, 1.2, 1.2],
        8: [1.4, 0.9, 0.9, 0.55, 0.8, 0.75, 0.55, 0.75, 0.6, 1.8],
        9: [1.4, 1.2, 0.65, 0.65, 0.75, 1.0],
        10: [1.5, 0.9, 0.9, 0.75, 0.55, 0.75, 0.6, 2.5, 0.6],
        11: [0.5, 1.5, 0.9, 0.9, 0.75, 0.55, 0.9, 0.75, 0.6, 0.6],
        12: [1.4, 5.6], 13: [1.4, 5.6], 14: [1.4, 5.6],
        15: [1.4, 5.6], 16: [1.4, 5.6],
        17: [1.5, 0.9, 0.9, 0.55, 0.55, 0.75, 0.75, 2.2],
        18: [0.7, 6.3],
    }

    for ti, table in enumerate(doc.tables):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        usable_width = int(doc.sections[0].page_width - doc.sections[0].left_margin - doc.sections[0].right_margin)
        usable_twips = usable_width // 635
        table_indent_twips = 120
        target_twips = usable_twips - table_indent_twips
        base_widths = width_weights.get(ti) or [int(column.width or 1) for column in table.columns]
        base_total = sum(base_widths) or len(base_widths)
        scaled_twips = [max(1, int(target_twips * width / base_total)) for width in base_widths]
        scaled_twips[-1] += target_twips - sum(scaled_twips)
        scaled_widths = [width * 635 for width in scaled_twips]
        tbl_width = table._tbl.tblPr.find(qn('w:tblW'))
        if tbl_width is None:
            tbl_width = OxmlElement('w:tblW')
            table._tbl.tblPr.insert(0, tbl_width)
        tbl_width.set(qn('w:type'), 'dxa')
        tbl_width.set(qn('w:w'), str(target_twips))
        tbl_indent = table._tbl.tblPr.find(qn('w:tblInd'))
        if tbl_indent is None:
            tbl_indent = OxmlElement('w:tblInd')
            table._tbl.tblPr.append(tbl_indent)
        tbl_indent.set(qn('w:type'), 'dxa')
        tbl_indent.set(qn('w:w'), str(table_indent_twips))
        for ci, column in enumerate(table.columns):
            column.width = scaled_widths[ci]
            for cell in column.cells:
                cell.width = scaled_widths[ci]
        for ri, row in enumerate(table.rows):
            tr_pr = row._tr.get_or_add_trPr()
            for tr_height in list(tr_pr.findall(qn('w:trHeight'))):
                tr_pr.remove(tr_height)
            if ri == 0:
                tbl_header = tr_pr.find(qn('w:tblHeader'))
                if tbl_header is None:
                    tbl_header = OxmlElement('w:tblHeader')
                    tr_pr.append(tbl_header)
                tbl_header.set(qn('w:val'), 'true')
            for cell in row.cells:
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                set_table_cell_border(cell)
                set_table_cell_margins(cell)
                if ri == 0:
                    set_table_cell_shading(cell, '17324D')
                    for para in cell.paragraphs:
                        _set_para_text(para, para.text, font_size=90, bold=True, color='FFFFFF')
                        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        para.paragraph_format.space_before = Pt(2)
                        para.paragraph_format.space_after = Pt(2)
                else:
                    set_table_cell_shading(cell, 'F8FAFC' if ri % 2 == 0 else 'FFFFFF')
                    for para in cell.paragraphs:
                        table_font_size = 95 if ti in range(12, 17) else (90 if ti in (0, 1, 2, 5, 9, 18) else 85)
                        set_para_style(para, size=table_font_size,
                                       color='1F2933', space_after=0)
                        para.paragraph_format.line_spacing = 1.08
                        if ti in (0, 2, 5, 9, 18) or len(table.columns) <= 5:
                            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if ti == 18:
            apply_compact_result_table_style(table)
        if requires_header_body_pagination(ti):
            keep_table_header_with_first_body_row(table)


def scrub_template_process_terms(doc):
    replacements = {
        '涨停池、连板股、首板、一进二候选和精品层结论必须在执行后由脚本写入。':
            '涨停池、连板股、首板、一进二候选和精品层结论已根据当日数据写入。',
        '本段为流程锚点，业务数据由唯一入口脚本自动写入表格。':
            '本段展示当日执行后的结构化结果。',
    }

    def clean(text):
        out = str(text or '')
        for old, new in replacements.items():
            out = out.replace(old, new)
        return out

    for para in doc.paragraphs:
        new_text = clean(para.text)
        if new_text != para.text:
            _set_para_text(para, new_text, font_size=82, color='555555')

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    new_text = clean(para.text)
                    if new_text != para.text:
                        _set_para_text(para, new_text, font_size=82, color='555555')


def _insert_paragraph_after(paragraph, style='Normal'):
    from docx.oxml import OxmlElement
    from docx.text.paragraph import Paragraph
    new_p = OxmlElement('w:p')
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    new_para.style = style
    return new_para


def _insert_paragraph_after_element(element, body, style='Normal'):
    from docx.oxml import OxmlElement
    from docx.text.paragraph import Paragraph
    new_p = OxmlElement('w:p')
    element.addnext(new_p)
    new_para = Paragraph(new_p, body)
    new_para.style = style
    return new_para


def reflow_tables_to_sections(doc, original_tables, focus_stocks):
    """Move fixed template tables beside the section that explains them."""
    from docx.shared import Pt

    paragraphs = list(doc.paragraphs)
    h1_positions = [i for i, para in enumerate(paragraphs) if para.style.name == 'Heading 1']
    if len(h1_positions) < 11:
        raise ValueError(f"expected 11 Heading 1 sections, got {len(h1_positions)}")

    anchors = {}
    for section_index, start in enumerate(h1_positions[:11]):
        end = h1_positions[section_index + 1] if section_index + 1 < len(h1_positions) else len(paragraphs)
        candidates = [p for p in paragraphs[start + 1:end] if p.text.strip()]
        anchors[section_index] = candidates[-1] if candidates else paragraphs[start]

    table_plan = {
        0: [(0, '当日数字'), (1, '最终名单')],
        2: [(2, '全部股票概况')],
        3: [(3, '涨停股票明细'), (5, '热门方向')],
        4: [(4, '资金情况')],
        5: [(6, '个股研报'), (7, '个股新闻与公告')],
        6: [(8, '连板股情况')],
        7: [(9, '首板股情况')],
        8: [(10, '评分前30只'), (11, '首板次日名单')],
        9: [(17, '风险排除名单')],
        10: [(18, '十步结果')],
    }
    for index, stock in enumerate(focus_stocks[:5]):
        section_index = 6 if int(stock.get('lb', 0) or 0) >= 2 else 7
        table_plan[section_index].append(
            (12 + index, f"{stock.get('code')} {stock.get('name')}详细数据")
        )
    for index in range(len(focus_stocks), 5):
        table_plan[10].append((12 + index, '全部股票概况'))

    for section_index, planned_tables in table_plan.items():
        anchor_element = anchors[section_index]._p
        for table_index, caption_text in planned_tables:
            caption = _insert_paragraph_after_element(anchor_element, doc._body, 'Heading 2')
            _format_analysis_paragraph(caption, caption_text, style='Heading 2')
            caption.paragraph_format.space_before = Pt(6 if table_index == 18 else 10)
            caption.paragraph_format.space_after = Pt(2 if table_index == 18 else 4)
            table_element = original_tables[table_index]._tbl
            caption._p.addnext(table_element)
            anchor_element = table_element


def add_report_footer(doc, date_text):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor
    for section in doc.sections:
        para = section.footer.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in list(para.runs):
            run._element.getparent().remove(run._element)
        run = para.add_run(f"连板挖掘 | {date_text} | 盘后研究")
        run.font.name = 'Microsoft YaHei'
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor.from_string('6B7280')
        para.paragraph_format.space_before = Pt(3)
        para.paragraph_format.space_after = Pt(0)


def add_stock_risk_notice_page(doc):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor

    section = doc.sections[0]
    section.different_first_page_header_footer = True
    first_footer = section.first_page_footer.paragraphs[0]
    _set_para_text(first_footer, '', font_size=10)

    elements = []

    def make_band(lines, fill, colors, sizes, padding_points):
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_before = Pt(padding_points)
        para.paragraph_format.space_after = Pt(padding_points)
        para.paragraph_format.keep_together = True
        para.paragraph_format.keep_with_next = True
        p_pr = para._p.get_or_add_pPr()
        shading = p_pr.find(qn('w:shd'))
        if shading is None:
            shading = OxmlElement('w:shd')
            p_pr.append(shading)
        shading.set(qn('w:fill'), fill)
        for index, line in enumerate(lines):
            run = para.add_run(line)
            run.font.name = 'Microsoft YaHei'
            run._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), 'Microsoft YaHei')
            run.font.size = Pt(sizes[index] / 10)
            run.font.bold = True
            run.font.color.rgb = RGBColor.from_string(colors[index])
            if index + 1 < len(lines):
                run.add_break()
        elements.append(para._p)

    def make_spacer(points):
        para = doc.add_paragraph()
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.line_spacing = Pt(points)
        para.add_run('').font.size = Pt(1)
        elements.append(para._p)

    make_band(
        ['投资风险提示', '教学案例｜交流学习｜方法演示'],
        '0B2442', ['FFFFFF', 'FFD65A'], [280, 140], 14,
    )
    make_spacer(8)
    for warning in ('不作为股票推荐', '不构成投资建议', '不作为买卖依据'):
        make_band([warning], 'FFF1C7', ['D40000'], [185], 7)
        make_spacer(5)
    make_band(['授课方/作者不具备荐股资质'], '9D0000', ['FFFFFF'], [135], 9)
    make_spacer(5)
    make_band(
        ['学生不得据此直接买卖；需独立判断并严格根据规则训练'],
        '9D0000', ['FFFFFF'], [125], 11,
    )
    make_spacer(10)
    make_band(
        ['本页为教学案例风险提示，后续内容依据当前交易日数据计算。', '股市有风险，入市需谨慎'],
        '0B2442', ['FFFFFF', 'FFD65A'], [110, 175], 11,
    )

    body = doc._body._element
    for element in reversed(elements):
        body.remove(element)
        body.insert(0, element)


def embed_stock_data_evidence(doc, evidence_path, trade_date):
    evidence = Path(evidence_path)
    if not evidence.is_file():
        raise SystemExit(f"BUILD_BLOCKED_DATA_EVIDENCE_MISSING: {evidence}")
    evidence_sha256 = hashlib.sha256(evidence.read_bytes()).hexdigest()
    doc.core_properties.comments = (
        f"{evidence_sha256}\nSTOCK_DATA_TRADE_DATE={trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
    )


def split_analysis_paragraphs(text, label='', max_chars=220):
    """Split visible narrative text without dropping or rewriting evidence."""
    if max_chars < 1:
        raise ValueError('max_chars must be positive')
    remaining = str(text)
    current_label = str(label or '')
    if not remaining:
        return [(current_label, '')]

    paragraphs = []
    while remaining:
        prefix_length = len(current_label) + 1 if current_label else 0
        capacity = max_chars - prefix_length
        if capacity < 1:
            raise ValueError('label is too long for max_chars')
        if len(remaining) <= capacity:
            paragraphs.append((current_label, remaining))
            break

        boundary = max(
            (remaining.rfind(mark, 0, capacity + 1) + 1 for mark in '。！？；，、'),
            default=0,
        )
        if boundary < 1:
            boundary = capacity
        paragraphs.append((current_label, remaining[:boundary]))
        remaining = remaining[boundary:]
        current_label = ''
    return paragraphs


def _format_analysis_paragraph(para, text, label='', style='Normal', callout=False):
    from docx.shared import Pt, RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    para.style = style
    for run in list(para.runs):
        run._element.getparent().remove(run._element)
    if style == 'Heading 2':
        run = para.add_run(str(text))
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RGBColor.from_string('17324D')
        para.paragraph_format.space_before = Pt(10)
        para.paragraph_format.space_after = Pt(4)
        para.paragraph_format.left_indent = Pt(7)
        para.paragraph_format.keep_with_next = True
        p_pr = para._p.get_or_add_pPr()
        p_bdr = p_pr.find(qn('w:pBdr'))
        if p_bdr is None:
            p_bdr = OxmlElement('w:pBdr')
            p_pr.append(p_bdr)
        left = p_bdr.find(qn('w:left'))
        if left is None:
            left = OxmlElement('w:left')
            p_bdr.append(left)
        left.set(qn('w:val'), 'single')
        left.set(qn('w:sz'), '18')
        left.set(qn('w:space'), '5')
        left.set(qn('w:color'), '0B5D7A')
        return para

    if label:
        lead = para.add_run(f"{label}｜")
        lead.font.bold = True
        lead.font.color.rgb = RGBColor.from_string('0B5D7A')
    body = para.add_run(str(text))
    body.font.color.rgb = RGBColor.from_string('263746')
    for run in para.runs:
        run.font.name = 'Microsoft YaHei'
        run._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), 'Microsoft YaHei')
        run.font.size = Pt(10.5)
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    para.paragraph_format.line_spacing = 1.28
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.widow_control = True
    if callout:
        p_pr = para._p.get_or_add_pPr()
        shd = p_pr.find(qn('w:shd'))
        if shd is None:
            shd = OxmlElement('w:shd')
            p_pr.append(shd)
        shd.set(qn('w:fill'), 'EAF4F8')
        p_bdr = p_pr.find(qn('w:pBdr'))
        if p_bdr is None:
            p_bdr = OxmlElement('w:pBdr')
            p_pr.append(p_bdr)
        for edge_name in ('top', 'left', 'bottom', 'right'):
            edge = p_bdr.find(qn(f'w:{edge_name}'))
            if edge is None:
                edge = OxmlElement(f'w:{edge_name}')
                p_bdr.append(edge)
            edge.set(qn('w:val'), 'single')
            edge.set(qn('w:sz'), '5' if edge_name != 'left' else '14')
            edge.set(qn('w:space'), '3')
            edge.set(qn('w:color'), 'B8D6E2' if edge_name != 'left' else '0B5D7A')
        para.paragraph_format.left_indent = Pt(8)
        para.paragraph_format.right_indent = Pt(8)
        para.paragraph_format.space_before = Pt(5)
        para.paragraph_format.space_after = Pt(9)
    return para


def _format_analysis_item(para, item):
    style = item.get('style', 'Normal')
    chunks = split_analysis_paragraphs(item.get('text', ''), item.get('label', ''))
    cursor = para
    for index, (label, text) in enumerate(chunks):
        if index:
            cursor = _insert_paragraph_after(cursor, style)
        _format_analysis_paragraph(cursor, text, label, style, item.get('callout', False))
    return cursor


def select_focus_stocks(analyzed, limit=5):
    scored = sorted(
        analyzed.get('zt_scored', []),
        key=lambda item: float(item.get('score', 0) or 0),
        reverse=True,
    )
    priority = [
        *analyzed.get('picks', []),
        *analyzed.get('risky', []),
        *scored,
    ]
    ordered = []
    seen = set()

    def add_stock(stock):
        code = str(stock.get('code', ''))
        if not code or code in seen:
            return False
        ordered.append(stock)
        seen.add(code)
        return True

    for stock in analyzed.get('picks', []):
        if len(ordered) >= limit:
            break
        add_stock(stock)

    required_groups = (
        lambda stock: int(stock.get('lb', 0) or 0) >= 2,
        lambda stock: int(stock.get('lb', 0) or 0) == 1,
    )
    for matches_group in required_groups:
        if any(matches_group(stock) for stock in ordered):
            continue
        representative = next((stock for stock in scored if matches_group(stock)), None)
        if representative is None:
            continue
        if len(ordered) >= limit:
            removed = ordered.pop()
            seen.discard(str(removed.get('code', '')))
        add_stock(representative)

    for stock in priority:
        if len(ordered) >= limit:
            break
        add_stock(stock)
    return ordered


def build_result_summaries(
    *,
    data_date,
    zt_total,
    zt_lb,
    zt_first,
    picks_count,
    formal_text,
    observations_count,
    observation_preview,
    excluded,
):
    exclusion_summary = (
        f"排除{len(excluded)}只，完整名单及原因见第二步与第九步。"
    )
    opening_market = (
        f"数据日：{data_date}。"
        f"全市场涨停{zt_total}只，连板{zt_lb}只，首板{zt_first}只。"
    )
    opening_candidates = (
        f"正式候选{picks_count}只：{formal_text}。"
        f"观察{observations_count}只，得分前五为{observation_preview}。"
        f"{exclusion_summary}"
    )
    closing = (
        f"数据日：{data_date}。"
        f"正式候选{picks_count}只：{formal_text}；"
        f"观察{observations_count}只，前五为{observation_preview}；"
        f"{exclusion_summary}"
    )
    return opening_market, opening_candidates, closing


def set_section_narrative(paras, analyzed, raw_data, data_date):
    from docx.shared import Pt
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    summary = analyzed['summary']
    picks = analyzed['picks']
    lines = analyzed['lines']
    zt_scored = analyzed['zt_scored']
    risky = analyzed['risky']
    yijiner = analyzed.get('yijiner', [])
    rdxz = raw_data.get('rdxz', [])
    focus_stocks = select_focus_stocks(analyzed)
    qsyb = raw_data.get('qsyb', [])
    focus_lianban = [z for z in focus_stocks if int(z.get('lb', 0) or 0) >= 2]
    focus_first = [z for z in focus_stocks if int(z.get('lb', 0) or 0) == 1]

    factor_labels = {
        'board_ladder': ('连板高度', 15),
        'limit_quality': ('涨停牢固度', 20),
        'capital': ('买入力度', 15),
        'visibility': ('市场关注度', 10),
        'sector_main': ('热门方向', 15),
        'chip': ('持股稳定度', 10),
        'sentiment': ('市场热度', 10),
        'executable': ('次日条件', 5),
    }

    def fmt_num(value, digits=2):
        try:
            return f"{float(value):.{digits}f}"
        except Exception:
            return '未取得'

    def factor_text(z):
        factors = z.get('score_factors') or {}
        return '、'.join(
            f"{label}{factors.get(key, 0)}/{maximum}"
            for key, (label, maximum) in factor_labels.items()
        )

    def factor_diagnosis(z):
        factors = z.get('score_factors') or {}
        ratios = []
        for key, (label, maximum) in factor_labels.items():
            value = float(factors.get(key, 0) or 0)
            ratios.append((value / maximum if maximum else 0, label, int(value), maximum))
        strong = sorted(ratios, reverse=True)[:3]
        weak = sorted(ratios)[:3]
        return (
            '强项是' + '、'.join(f"{label}{value}/{maximum}" for _, label, value, maximum in strong)
            + '；弱项是' + '、'.join(f"{label}{value}/{maximum}" for _, label, value, maximum in weak)
        )

    def kline_text(z):
        detail = z.get('k_line_detail') or {}
        d = detail.get('d') or {}
        d1 = detail.get('d_minus_1') or {}
        if detail.get('status') != 'PASS' or not d:
            return '最近两天的价格没有查全，暂不设观察价。'
        previous_change = detail.get('d_minus_1_pct_change')
        previous_part = f"，前一交易日涨幅{previous_change:.2f}%" if previous_change is not None else ''
        return (
            f"{d.get('date')}开盘{fmt_num(d.get('open'))}元、最高{fmt_num(d.get('high'))}元、"
            f"最低{fmt_num(d.get('low'))}元、收盘{fmt_num(d.get('close'))}元，"
            f"当日涨幅{fmt_num(detail.get('d_pct_change'))}%且收盘等于最高价{previous_part}。"
            f"前收盘为{fmt_num(d1.get('close'))}元，最近两天走势已核对。"
        )

    def capital_text(z):
        return (
            f"第一次封住{z.get('first_seal', '-')}、最后一次封住{z.get('last_seal', '-')}，打开涨停{z.get('break_count', 0)}次；"
            f"收盘封单{to_yi(z.get('seal_funds', 0))}，换手率{fmt_num(z.get('turnover'))}%，"
            f"成交额{to_yi(z.get('amount', 0))}，流通市值{to_yi(z.get('float_cap', 0))}，"
            f"公开席位净买额{to_yi(z.get('lhb_net_buy', 0))}。"
        )

    def ratio_pct(numerator, denominator):
        try:
            denominator = float(denominator or 0)
            return float(numerator or 0) / denominator * 100 if denominator else 0.0
        except Exception:
            return 0.0

    def capital_judgment(z):
        seal_ratio = ratio_pct(z.get('seal_funds'), z.get('amount'))
        lhb_ratio = ratio_pct(z.get('lhb_net_buy'), z.get('amount'))
        break_count = int(z.get('break_count', 0) or 0)
        turnover = float(z.get('turnover', 0) or 0)
        first_seal = str(z.get('first_seal', '-'))
        last_seal = str(z.get('last_seal', '-'))
        facts = (
            f"封单占成交额{seal_ratio:.1f}%，公开席位净买占成交额{lhb_ratio:.1f}%；"
            f"第一次封住{first_seal}、最后一次封住{last_seal}、打开涨停{break_count}次、换手率{turnover:.2f}%。"
        )
        if (z.get('risk_result') or {}).get('final_action') == 'OUT':
            verdict = (
                f"封单占成交额仅{seal_ratio:.1f}%且盘中打开涨停{break_count}次，买盘不够稳；"
                "同时触发风险排除条件，因此剔除。"
            )
        elif turnover >= 30 or first_seal >= '14:30:00':
            verdict = (
                f"换手率{turnover:.2f}%说明当天买卖很激烈，封单只占成交额{seal_ratio:.1f}%；"
                "又是尾盘才封住，次日容易大幅波动。"
            )
        elif break_count >= 2:
            verdict = (
                f"从{first_seal}到{last_seal}打开涨停{break_count}次，封单占比{seal_ratio:.1f}%，"
                f"公开席位净买占比{lhb_ratio:.1f}%；买盘反复，连板数不能单独说明资金强弱。"
            )
        elif first_seal == last_seal and first_seal < '10:00:00' and seal_ratio >= 20:
            verdict = (
                f"早盘一次封住且未打开，封单占成交额{seal_ratio:.1f}%，公开席位净买占成交额{lhb_ratio:.1f}%；"
                "买盘最稳，但板数较高，仍要防冲高回落。"
            )
        else:
            verdict = (
                f"封单占成交额{seal_ratio:.1f}%、公开席位净买占成交额{lhb_ratio:.1f}%，"
                "买盘强度一般。"
            )
        return facts, verdict

    def stock_news(z, limit=3):
        rows = [row for row in rdxz if row.get('code') == z.get('code')]
        rows.sort(key=lambda row: str(row.get('published', '')), reverse=True)
        unique = []
        seen = set()
        for row in rows:
            title = sanitize_finance_chinese(row.get('title', '')).strip(' )）')
            if not title or title in seen:
                continue
            seen.add(title)
            unique.append((str(row.get('published', ''))[:16], title, sanitize_finance_chinese(row.get('source', ''))))
            if len(unique) >= limit:
                break
        return unique

    def stock_news_records(z, limit=8):
        rows = [row for row in rdxz if row.get('code') == z.get('code')]
        rows.sort(key=lambda row: str(row.get('published', '')), reverse=True)
        unique = []
        seen = set()
        for row in rows:
            title = sanitize_finance_chinese(row.get('title', '')).strip(' )）')
            if not title or title in seen:
                continue
            seen.add(title)
            unique.append({
                'published': str(row.get('published', ''))[:16],
                'title': title,
                'source': sanitize_finance_chinese(row.get('source', '')),
                'content': sanitize_finance_chinese(row.get('content', '')),
            })
            if len(unique) >= limit:
                break
        return unique

    def event_evidence_and_judgment(z):
        rows = stock_news_records(z)
        if not rows:
            return (
                '最近3天没有查到该股新闻。',
                '没有新消息支持上调结果。',
            )
        priority_terms = ('业绩', '净利', '风险', '异常波动', '连板', '涨停', '龙虎榜')
        prioritized = [row for row in rows if any(term in row['title'] for term in priority_terms)]
        selected = (prioritized + [row for row in rows if row not in prioritized])[:3]
        evidence = '；'.join(
            f"{row['published']}《{row['title']}》（{row['source']}）"
            for row in selected
        ) + '。'
        blob = ' '.join(row['title'] + ' ' + row['content'] for row in rows)
        risk_result = z.get('risk_result') or {}
        independent = sum((risk_result.get('independent_soft_event_counts') or {}).values())
        turnover = float(z.get('turnover', 0) or 0)
        if risk_result.get('final_action') == 'OUT':
            judgment = (
                f"最近公告中有{independent}组独立风险事项，"
                f"当天又打开涨停{z.get('break_count', 0)}次、换手率{turnover:.2f}%。"
                "风险与资金同时偏弱，因此剔除。"
            )
        elif any(term in blob for term in ('净利同比预降', '净利润同比下降', '盈利规模同比大幅缩水')):
            judgment = (
                f"公司盈利明显下滑，但股价仍是{z.get('lb')}板。"
                f"公开席位净买额{to_yi(z.get('lhb_net_buy', 0))}，不足以抵消业绩下滑；"
                "因此只观察，不列为正式候选。"
            )
        elif turnover >= 30:
            detail = z.get('k_line_detail') or {}
            judgment = (
                f"前一交易日涨幅{fmt_num(detail.get('d_minus_1_pct_change'))}%，当日涨幅{fmt_num(detail.get('d_pct_change'))}%，"
                f"换手率{turnover:.2f}%且{z.get('first_seal')}才封住，新闻没有带来订单或利润增长的新信息。"
                "当天波动很大，次日风险偏高。"
            )
        elif int(z.get('lb', 0) or 0) >= 3:
            judgment = (
                f"该股已到{z.get('lb')}连板，但新闻主要重复涨停和公开席位数据；"
                f"公开席位净买{to_yi(z.get('lhb_net_buy', 0))}、封单{to_yi(z.get('seal_funds', 0))}，"
                "没有新的利润或订单信息，因此只观察。"
            )
        else:
            judgment = (
                f"新闻已确认当日价格异动，但换手率{turnover:.2f}%、封单{to_yi(z.get('seal_funds', 0))}；"
                "没有新的利润或订单信息，因此不提高排名。"
            )
        return evidence, judgment

    def research_judgment(z):
        rows = [row for row in qsyb if row.get('code') == z.get('code')]
        if not rows:
            return (
                f"33条研报中没有{z['code']} {z['name']}。"
                "缺少盈利、订单和估值参考，因此不凭行业观点加分。"
            )
        rows.sort(key=lambda row: str(row.get('date', '')), reverse=True)
        latest = rows[0]
        return (
            f"{latest.get('date')}《{sanitize_finance_chinese(latest.get('report', ''))}》"
            f"（{sanitize_finance_chinese(latest.get('org', ''))}，评级{sanitize_finance_chinese(latest.get('rating', ''))}）。"
            "这条研报提供盈利和估值参考，但仍要同时看当天价格和资金。"
        )

    def news_text(z):
        items = stock_news(z)
        if not items:
            return '最近3天没有查到该股新闻，不加分。'
        return '；'.join(f"{date}《{title}》（{source}）" for date, title, source in items) + '。'

    def risk_text(z):
        result = z.get('risk_result') or {}
        flags = result.get('risk_flags') or []
        if not flags:
            return '最近5个交易日没有发现需要排除的风险公告。'
        details = []
        for flag in flags[:5]:
            details.append(
                f"{flag.get('event_date', '日期未明')}《{sanitize_finance_chinese(flag.get('title', '风险事项'))}》"
            )
        counts = result.get('independent_soft_event_counts') or {}
        category_cn = {
            'clarification': '澄清与异常波动类', 'financial': '财务类',
            'reduction': '减持类', 'unlock': '解禁类', 'litigation': '诉讼类',
            'regulatory': '监管类', 'delisting': '退市类', 'audit': '审计类',
        }
        count_text = '、'.join(f"{category_cn.get(key, '其他类')}{value}组" for key, value in counts.items()) or '未形成独立事件组'
        status_cn = {
            'PASS': '通过', 'OUT': '剔除', 'DOWNGRADE': '只观察',
            'REVIEW_REQUIRED': '待复查', 'UNVERIFIED': '未查全',
            'A': '规则一', 'B': '规则二', 'C': '规则三',
        }
        combo_text = status_cn.get(str(result.get('trigger_combo')), str(result.get('trigger_combo', '未验证')))
        action_text = status_cn.get(str(result.get('final_action')), str(result.get('final_action', '未验证')))
        return (
            '；'.join(details) + f"。独立风险事项为{count_text}，"
            f"触发{combo_text}，结果为{action_text}。"
        )

    def evidence_gap_text(z):
        gaps = []
        if not z.get('qsyb_bound'):
            gaps.append('没有该股研报')
        if not z.get('rdxz_bound'):
            gaps.append('没有最近3天该股新闻')
        if z.get('risk_review_complete') is not True:
            gaps.append('风险公告未查完')
        if z.get('score', 0) < 70:
            gaps.append(f"综合评分{z.get('score')}分低于70分")
        if (z.get('risk_result') or {}).get('final_action') == 'OUT':
            gaps.append('触发风险排除条件')
        return '；'.join(gaps)

    def plan_text(z):
        detail = z.get('k_line_detail') or {}
        if (z.get('risk_result') or {}).get('final_action') == 'OUT':
            return (
                '当前已排除。只有风险公告不再增加、最近两天走势和资金重新转强，才重新观察。'
            )
        if detail.get('status') != 'PASS':
            return '最近价格没有查全，暂不设观察价。'
        return (
            f"次日先看{fmt_num(detail.get('strong_open_reference'))}元能否守住，涨停参考价约{fmt_num(detail.get('next_limit_reference'))}元。"
            f"若跌破{fmt_num(detail.get('invalidation_reference'))}元，或打开涨停次数增加、公开席位转为净卖、风险公告增加，则停止观察。"
        )

    def stock_items(z):
        items = [
            {'style': 'Heading 2', 'text': f"{z['code']} {z['name']}｜{z['lb']}板｜{z['classification']}｜{z['score']}分"},
            {'label': '最近两天', 'text': kline_text(z)},
            {'label': '资金情况', 'text': capital_text(z)},
            {'label': '八项评分', 'text': factor_text(z) + '。' + factor_diagnosis(z) + '。'},
            {'label': '最新消息', 'text': news_text(z)},
            {'label': '风险', 'text': risk_text(z)},
        ]
        gap_text = evidence_gap_text(z)
        if gap_text:
            items.append({'label': '仍需注意', 'text': gap_text + '。'})
        items.append({'label': '次日怎么看', 'text': plan_text(z)})
        return items

    headings = [
        '最终结果', '第一步｜核心结论', '第二步｜数据范围与排除原因',
        '第三步｜连板高度与热门方向', '第四步｜资金强弱',
        '第五步｜研报与新闻', '第六步｜连板股逐只分析',
        '第七步｜首板股逐只分析', '第八步｜首板次日机会',
        '第九步｜风险排除', '第十步｜最终结论',
    ]

    observations = [z for z in zt_scored if z.get('classification') == '观察']
    excluded = [z for z in zt_scored if z.get('classification') == '剔除']
    formal_text = '、'.join(f"{z['code']} {z['name']}" for z in picks) or '无正式候选'
    observation_preview = '、'.join(f"{z['code']} {z['name']}({z['score']}分)" for z in observations[:5]) or '无'
    focus_text = '、'.join(f"{z['code']} {z['name']}" for z in focus_stocks)
    local_count = len(raw_data.get('ztc_local', []))
    risk_collection = raw_data.get('risk_collection') or {}
    risk_complete = int(risk_collection.get('review_complete_codes', 0) or 0)
    risk_errors = risk_collection.get('errors') or []
    risk_error_text = '、'.join(f"{item.get('code')}({item.get('error')})" for item in risk_errors) or '无'
    qsyb_bound = sum(1 for z in zt_scored if z.get('qsyb_bound'))
    news_bound = sum(1 for z in zt_scored if z.get('rdxz_bound'))
    line_text = '；'.join(
        f"{line['line']}：{line['count']}只、最高{line['max_lb']}板、收盘封单{to_yi(line['seal_funds'])}、公开席位净买{to_yi(line['lhb_net_buy'])}"
        for line in lines[:5]
    ) or '未形成可比较主线'
    opening_market_summary, opening_candidate_summary, closing_summary = build_result_summaries(
        data_date=data_date,
        zt_total=summary['zt_total'],
        zt_lb=summary['zt_lb'],
        zt_first=summary['zt_first'],
        picks_count=len(picks),
        formal_text=formal_text,
        observations_count=len(observations),
        observation_preview=observation_preview,
        excluded=excluded,
    )

    sections = [[] for _ in headings]
    sections[0] = [
        {
            'label': '市场与结果',
            'text': f"{opening_market_summary} {opening_candidate_summary}",
            'callout': True,
        },
    ]
    sections[1] = [
        {'label': '大盘', 'text': f"涨停{summary['zt_total']}只，其中首板{summary['zt_first']}只、连板{summary['zt_lb']}只。公开交易席位榜有{summary['lhb_total']}只股票，其中{summary['lhb_in_zt']}只是涨停股。"},
        {'label': '热门方向', 'text': line_text + '。'},
    ]
    for line in lines[:3]:
        sections[1].append({'label': line['line'], 'text': f"共{line['count']}只，最高{line['max_lb']}板，收盘封单{to_yi(line['seal_funds'])}，公开席位净买{to_yi(line['lhb_net_buy'])}。"})
    sections[2] = [
        {'style': 'Heading 2', 'text': f"{summary['zt_total']}只涨停，{len(zt_scored)}只纳入"},
        {'label': '看了多少只', 'text': f"全市场{summary['zt_total']}只涨停。本地通达信有{local_count}只，这{len(zt_scored)}只全部逐只查看；另外{summary['zt_total']-len(zt_scored)}只不在本地涨停池中，不参与。", 'callout': True},
        {'label': '资料是否齐', 'text': f"{len(zt_scored)}只都查了最近两天走势、新闻和风险公告；{qsyb_bound}只有个股研报，{len(zt_scored)-qsyb_bound}只没有个股研报。没有研报的不加分。"},
        {'label': '漏查数量', 'text': f"风险公告漏查{len(risk_errors)}只。"},
    ]
    ladder = sorted(focus_stocks, key=lambda z: (int(z.get('lb', 0) or 0), float(z.get('score', 0) or 0)), reverse=True)
    ladder_text = '；'.join(f"{z['name']}{z['lb']}板/{z['score']}分/{z['classification']}" for z in ladder)
    sections[3] = [
        {'label': '重点股位置', 'text': ladder_text + '。'},
        {'label': '热门方向', 'text': line_text + '。'},
    ]
    for z in ladder:
        sections[3].append({'label': z['name'], 'text': f"属于{z.get('line')}，{z.get('lb')}板。第一次封住{z.get('first_seal')}，最后一次封住{z.get('last_seal')}，打开涨停{z.get('break_count', 0)}次，收盘封单{to_yi(z.get('seal_funds', 0))}。{factor_diagnosis(z)}。"})
    sections[4] = [
        {'label': '资金强弱', 'text': '下面直接列出五只重点股的收盘封单、公开席位买卖和涨停是否牢固。', 'callout': True},
    ]
    for z in focus_stocks:
        facts, verdict = capital_judgment(z)
        sections[4].extend([
            {'style': 'Heading 2', 'text': f"{z['code']} {z['name']}｜资金判断"},
            {'label': '资金数字', 'text': capital_text(z) + facts},
            {'label': '资金结论', 'text': verdict},
        ])
    sections[5] = [
        {'label': '查到的资料', 'text': f"共有{summary['qsyb_total']}条研报，{qsyb_bound}只股票查到个股研报；共有{summary['rdxz_total']}条新闻，{news_bound}只股票查到近期消息。", 'callout': True},
    ]
    for z in focus_stocks:
        news_evidence, event_judgment = event_evidence_and_judgment(z)
        sections[5].extend([
            {'style': 'Heading 2', 'text': f"{z['code']} {z['name']}｜研报和消息"},
            {'label': '研报判断', 'text': research_judgment(z)},
            {'label': '新闻内容', 'text': news_evidence},
            {'label': '消息影响', 'text': event_judgment},
            {'label': '最终结果', 'text': f"结果为{z['classification']}，评分{z['score']}分。{evidence_gap_text(z)}。"},
        ])
    for z in focus_lianban:
        sections[6].extend(stock_items(z))
    for z in focus_first:
        sections[7].extend(stock_items(z))
    first_ranked = sorted([z for z in zt_scored if int(z.get('lb', 0) or 0) == 1], key=lambda z: float(z.get('score', 0) or 0), reverse=True)
    sections[8] = [
        {'label': '结果', 'text': f"首板次日正式候选{len(yijiner)}只。首板共{len(first_ranked)}只，得分前三为" + '、'.join(f"{z['code']} {z['name']}({z['score']}分)" for z in first_ranked[:3]) + '。'},
    ]
    for z in first_ranked[:3]:
        sections[8].extend([
            {'style': 'Heading 2', 'text': f"{z['code']} {z['name']}｜首板次日分析"},
            {'label': '最近两天和资金', 'text': kline_text(z) + capital_text(z)},
            {'label': '为什么入选或不入选', 'text': f"结果为{z['classification']}，{z['score']}分。{evidence_gap_text(z)}。{plan_text(z)}"},
        ])
    sections[9] = [
        {'label': '检查结果', 'text': f"{len(zt_scored)}只股票的风险公告全部查完；排除{len(excluded)}只，漏查{len(risk_errors)}只。", 'callout': True},
    ]
    for z in focus_stocks:
        sections[9].append({'label': f"{z['name']}风险", 'text': risk_text(z)})
    sections[10] = [
        {'label': '最后名单', 'text': closing_summary, 'callout': True},
    ]
    for z in focus_stocks:
        sections[10].append({
            'text': (
                f"结论：{z['code']} {z['name']}为{z['classification']}，评分{z['score']}分。"
                f"依据：{z['lb']}板，收盘封单{to_yi(z.get('seal_funds', 0))}，公开席位净买{to_yi(z.get('lhb_net_buy', 0))}。"
                f"反证：{evidence_gap_text(z)}。"
            )
        })

    original = list(paras)
    heading_positions = [i for i, para in enumerate(original) if para.style.name == 'Heading 1']
    for section_index, position in enumerate(heading_positions[:len(headings)]):
        heading = original[position]
        _set_para_text(heading, headings[section_index], font_size=170, bold=True, color='17324D')
        heading.paragraph_format.space_before = Pt(12)
        heading.paragraph_format.space_after = Pt(6)
        heading.paragraph_format.keep_with_next = True
        h_pr = heading._p.get_or_add_pPr()
        h_bdr = h_pr.find(qn('w:pBdr'))
        if h_bdr is None:
            h_bdr = OxmlElement('w:pBdr')
            h_pr.append(h_bdr)
        bottom = h_bdr.find(qn('w:bottom'))
        if bottom is None:
            bottom = OxmlElement('w:bottom')
            h_bdr.append(bottom)
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '10')
        bottom.set(qn('w:space'), '4')
        bottom.set(qn('w:color'), '0B5D7A')

        next_position = heading_positions[section_index + 1] if section_index + 1 < len(heading_positions) else len(original)
        anchor = next((p for p in original[position + 1:next_position] if p.style.name == 'Normal' and p.text.strip()), None)
        items = sections[section_index] or [{
            'label': '本次结果',
            'text': f"截至{data_date}，本次采集结果未形成可列入该部分的股票。",
        }]
        if anchor is None:
            anchor = _insert_paragraph_after(heading)
        remove_unused_section_paragraphs(original[position + 1:next_position], anchor)
        first = items[0]
        cursor = _format_analysis_item(anchor, first)
        for item in items[1:]:
            cursor = _insert_paragraph_after(cursor, item.get('style', 'Normal'))
            cursor = _format_analysis_item(cursor, item)


def _latest_trading_day():
    """Resolve the latest trading day from TDX local K-line files.

    NO hardcoded dates, NO filename regex guessing. Reads the last record
    of TDX .day files and picks the freshest mtime among valid candidates.
    Used only as the --date argparse default; the orchestrator always
    passes --date explicitly, so this default is a safety net.
    """
    try:
        from _date_utils import resolve_latest_trade_date
        return resolve_latest_trade_date()
    except Exception:
        # Last-resort safety: refuse to silently fall back to a hardcoded date.
        raise SystemExit(
            "build_docx: cannot determine trading date (no --date and TDX lookup failed). "
            "Refusing to use a hardcoded default."
        )


def main():
    from docx.shared import Pt

    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=_latest_trading_day(), help='交易日 YYYYMMDD (默认最近交易日)')
    ap.add_argument('--data', help='analyzed JSON path')
    ap.add_argument('--raw', help='raw JSON path')
    ap.add_argument('--template', help='template DOCX path')
    ap.add_argument('--out', help='output DOCX path')
    ap.add_argument('--data-evidence', required=True, help='股票数据新鲜度证据 JSON')
    args = ap.parse_args()

    template = args.template or str(_DEFAULT_TEMPLATE)
    workspace_data = _WORKSPACE_DATA
    data = args.data or str(workspace_data / f"analyzed2_{args.date}.json")
    raw = args.raw or str(workspace_data / f"raw4_{args.date}.json")
    if not args.out:
        date_pretty = f"{args.date[:4]}-{args.date[4:6]}-{args.date[6:8]}"
        args.out = str(resolve_data_root() / "reports" / "deliverables" / "a-share-limit-up-mining" / f"\u8fde\u677f\u6316\u6398_{date_pretty}.docx")

    print(f"date: {args.date}")
    print(f"tpl : {template}")
    print(f"data: {data}")
    print(f"raw : {raw}")
    print(f"out : {args.out}")

    if not Path(template).exists():
        sys.exit(f"ERROR: template not found")
    if not Path(data).exists():
        sys.exit(f"ERROR: data not found")

    analyzed = json.loads(Path(data).read_text(encoding='utf-8'))
    raw_data = json.loads(Path(raw).read_text(encoding='utf-8')) if Path(raw).exists() else {}

    zt_scored = analyzed['zt_scored']
    lines = analyzed['lines']
    picks = analyzed['picks']
    yijiner = analyzed['yijiner']
    risky = analyzed['risky']
    summary = analyzed['summary']
    lhb_in_zt = analyzed['lhb_in_zt']
    qsyb = raw_data.get('qsyb', [])
    rdxz = raw_data.get('rdxz', [])
    focus_stocks = select_focus_stocks(analyzed)

    risk_collection_checks = validate_risk_collection_scope(raw_data, zt_scored)
    collection_checks = {
        'date': str(raw_data.get('date', '')) == args.date,
        'qsyb': not (raw_data.get('qsyb_collection') or {}).get('errors'),
        'rdxz': not (raw_data.get('rdxz_collection') or {}).get('errors'),
        'risk_errors': risk_collection_checks['risk_errors'],
        'risk_complete': risk_collection_checks['risk_complete'],
        'risk_scope': risk_collection_checks['risk_scope'],
    }
    failed_collection_checks = [name for name, passed in collection_checks.items() if not passed]
    if failed_collection_checks:
        raise SystemExit(f"BUILD_BLOCKED_INCOMPLETE_DATA: {failed_collection_checks}")

    # Obfuscated strings used in output
    TITLE = '\u8fde\u677f\u6316\u6398\u5168\u6d41\u7a0b\u9009\u80a1\u62a5\u544a\uff5c\u6df1\u5ea6\u7814\u7a76\u7248'
    SUB_PRE = f"{args.date[:4]}\u5e74{args.date[4:6]}\u6708{args.date[6:8]}\u65e5"
    SUF = '\u6da8\u505c\u68af\u961f\u3001\u8d44\u91d1\u7ed3\u6784\u3001\u4e8b\u4ef6\u8bc1\u636e\u4e0e\u9010\u80a1\u98ce\u9669\u590d\u6838'
    PURE = '\u7eaf'
    WARN = '\u26a0'
    NONE = '\u65e0'
    RANK = '\u7b2c{0}\u540d\uff1a{1} {2}'

    from docx import Document
    doc = Document(template)
    scrub_template_process_terms(doc)
    tables = doc.tables
    paras = doc.paragraphs

    # Title + subtitle
    if len(paras) > 0:
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        _set_para_text(paras[0], TITLE, font_size=220, bold=True, color='17324D')
        paras[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        paras[0].paragraph_format.space_before = Pt(8)
        paras[0].paragraph_format.space_after = Pt(2)
    if len(paras) > 1:
        _set_para_text(paras[1], f"{SUB_PRE} \u00b7 {SUF}", font_size=110, bold=False, color='5E6B75')
        paras[1].alignment = WD_ALIGN_PARAGRAPH.LEFT
        paras[1].paragraph_format.space_after = Pt(10)

    # H2 picks update
    h2_picks = [p for p in paras if p.style.name == 'Heading 2' and '\u7b2c' in p.text and '\u540d' in p.text]
    for i, p in enumerate(h2_picks):
        if i < len(picks):
            z = picks[i]
            _set_para_text(p, RANK.format(i+1, z['code'], z['name']),
                           font_size=180, bold=True, color='1A1A2E')

    # T0: Cover KPI
    t = tables[0]
    vals = [str(summary['zt_total']), str(summary['zt_first']), str(summary['zt_lb']),
            str(min(summary['zt_first']//2, 10)), str(summary['pick_count'])]
    for ci, v in enumerate(vals):
        if ci < len(t.rows[1].cells):
            set_cell_text(t.rows[1].cells[ci], v, font_size=165, bold=True, color='1A1A2E')

    # T1: Picks summary
    t = tables[1]
    display_rows = select_summary_rows(picks, zt_scored)
    target_pick_rows = max(1, len(display_rows))
    while len(t.rows) > target_pick_rows + 1:
        remove_row(t, len(t.rows) - 1)
    while len(t.rows) < target_pick_rows + 1:
        add_row(t, 6)
    if display_rows:
        for i, z in enumerate(display_rows):
            cells = t.rows[i+1].cells
            if len(cells) < 6:
                continue
            set_cell_text(cells[0], f"{z.get('classification', '复核')}{i+1}", bold=True)
            set_cell_text(cells[1], f"{z['code']} {z['name']}", bold=True)
            set_cell_text(cells[2], z.get('industry', '-'))
            set_cell_text(cells[3], str(z['score']), bold=True)
            set_cell_text(cells[4], to_yi(z.get('lhb_net_buy', 0)))
            gaps = []
            if not z.get('qsyb_bound'):
                gaps.append('无个股绑定研报')
            if z.get('score', 0) < 70:
                gaps.append(f"评分{z.get('score')}分低于70分")
            if (z.get('risk_result') or {}).get('final_action') == 'OUT':
                gaps.append(f"风险规则{(z.get('risk_result') or {}).get('trigger_combo')}剔除")
            concrete = (
                f"收盘封单{to_yi(z.get('seal_funds', 0))}；"
                f"公开席位净买{to_yi(z.get('lhb_net_buy', 0))}"
            )
            core = f"{z['line']}；{z['lb']}板；第一次封住{z.get('first_seal', '')}；" + ('、'.join(gaps) or concrete)
            set_cell_text(cells[5], core)

    # T2: Match table
    t = tables[2]
    row1 = t.rows[1].cells
    vals = [str(summary['zt_total']), str(summary['zt_total']),
            str(summary['zt_first']), str(summary['zt_lb']), str(summary['risky_count'])]
    for ci, v in enumerate(vals):
        if ci < len(row1):
            set_cell_text(row1[ci], v, font_size=120, bold=True, color='1A1A2E')

    # T3: ZT pool
    t = tables[3]
    while len(t.rows) > len(zt_scored) + 1:
        remove_row(t, len(t.rows) - 1)
    while len(t.rows) < len(zt_scored) + 1:
        add_row(t, 10)
    for i, z in enumerate(zt_scored):
        fill_row(t, i+1, [
            f"{z['code']} {z['name']}", z['line'], z['industry'],
            str(z['lb']), z['lb_tj'], z['first_seal'], z['last_seal'],
            str(z['break_count']), to_yi(z['seal_funds']),
            f"{z['turnover']:.2f}%"
        ])

    # T4: LHB in ZT
    t = tables[4]
    zt_codes = {z['code'] for z in zt_scored}
    rows = [r for r in lhb_in_zt if r['code'] in zt_codes]
    while len(t.rows) > len(rows) + 1:
        remove_row(t, len(t.rows) - 1)
    while len(t.rows) < len(rows) + 1:
        add_row(t, 10)
    zt_map = {z['code']: z for z in zt_scored}
    for i, r in enumerate(rows):
        z = zt_map.get(r['code'])
        if not z:
            continue
        nb = r.get('net_buy', 0)
        lbl = PURE if nb > 0 else (WARN if nb < 0 else NONE)
        fill_row(t, i+1, [
            f"{r['code']} {r['name']}", z['line'], z['industry'],
            str(z['lb']), to_yi(nb), to_yi(nb), to_yi(nb),
            str(z['break_count']), lbl, r.get('reason', '')
        ])

    # T5: Line stats
    t = tables[5]
    while len(t.rows) > len(lines) + 1:
        remove_row(t, len(t.rows) - 1)
    while len(t.rows) < len(lines) + 1:
        add_row(t, 9)
    for i, ln in enumerate(lines):
        fill_row(t, i+1, [
            ln['line'], str(ln['count']), str(ln['first_count']),
            str(ln['lb_count']), str(ln['max_lb']),
            to_yi(ln['seal_funds']), to_yi(ln['lhb_net_buy']),
            str(ln['avg_break']), str(ln['score'])
        ], bold_first=True)

    # T6: QSYB
    t = tables[6]
    target_codes = zt_codes | {p['code'] for p in picks}
    qsyb_rows = [
        q for q in qsyb
        if q['code'] in target_codes
        and q.get('report', '').strip()
        and q.get('date', '').strip()
        and re.search(r'[\u4e00-\u9fff]', q.get('report', ''))
    ][:18]
    while len(t.rows) > len(qsyb_rows) + 1:
        remove_row(t, len(t.rows) - 1)
    while len(t.rows) < len(qsyb_rows) + 1:
        add_row(t, 7)
    for i, q in enumerate(qsyb_rows):
        rating = q.get('rating', '').strip() or '\u672a\u8bc4\u7ea7'
        fill_row(t, i+1, [
            q['code'], q['name'], sanitize_finance_chinese(q['report']), sanitize_finance_chinese(rating), sanitize_finance_chinese(q['org']),
            q['industry'], q['date']
        ], bold_first=False)

    # T7: RDXZ
    t = tables[7]
    rdxz_rows = [n for n in rdxz if n['code'] in target_codes][:18]
    while len(t.rows) > len(rdxz_rows) + 1:
        remove_row(t, len(t.rows) - 1)
    while len(t.rows) < len(rdxz_rows) + 1:
        add_row(t, 6)
    for i, n in enumerate(rdxz_rows):
        content = sanitize_finance_chinese(n['content'])
        if n['code'] not in content and n['name'] not in content:
            content = f"{n['name']}({n['code']}) " + content
        fill_row(t, i+1, [
            n['code'], n['name'], sanitize_finance_chinese(n['title']), content[:80],
            n['published'], sanitize_finance_chinese(n['source'])
        ], bold_first=False)

    # T8: Lianban diagnosis
    t = tables[8]
    lianban = [z for z in zt_scored if z['lb'] >= 2]
    while len(t.rows) > len(lianban) + 1:
        remove_row(t, len(t.rows) - 1)
    while len(t.rows) < len(lianban) + 1:
        add_row(t, 10)
    for i, z in enumerate(lianban):
        risky_flag = (z['lhb_net_buy'] < -2e7 or z['break_count'] > 7)
        color = 'C0392B' if risky_flag else '1E1E28'
        nb = z['lhb_net_buy']
        lbl = PURE if nb > 0 else (WARN if nb < 0 else NONE)
        diag = '\u98ce\u9669\u5e26\u52a8\uff0c\u4e0d\u53c2\u4e0e\u63a5\u529b' if risky_flag else PURE
        fill_row(t, i+1, [
            f"{z['code']} {z['name']}", z['line'], z['industry'],
            str(z['lb']), z['lb_tj'], z['first_seal'], str(z['break_count']),
            to_yi(nb), lbl, diag
        ], color=color)

    # T9: Firstban by line
    t = tables[9]
    fbls = []
    for ln in lines:
        fs = [z for z in zt_scored if z['line'] == ln['line'] and z['lb'] == 1]
        if not fs:
            continue
        fbls.append({
            'line': ln['line'],
            'topic': ln['topic'],
            'first_count': len(fs),
            'zero_break': sum(1 for z in fs if z['break_count'] == 0),
            'lhb_count': sum(1 for z in fs if z['lhb_net_buy'] > 0),
            'seal_funds': sum(z['seal_funds'] for z in fs),
        })
    while len(t.rows) > len(fbls) + 1:
        remove_row(t, len(t.rows) - 1)
    while len(t.rows) < len(fbls) + 1:
        add_row(t, 6)
    if not fbls:
        add_row(t, 6)
        fill_row(t, 1, ['无首板分类', '当日为空', '0', '0', '0', '0.00亿'])
    else:
        for i, ln in enumerate(fbls):
            fill_row(t, i+1, [
                ln['line'], ln['topic'], str(ln['first_count']),
                str(ln['zero_break']), str(ln['lhb_count']),
                to_yi(ln['seal_funds'])
            ])

    # T10: Top 30 pool
    t = tables[10]
    top = zt_scored[:30]
    while len(t.rows) > len(top) + 1:
        remove_row(t, len(t.rows) - 1)
    while len(t.rows) < len(top) + 1:
        add_row(t, 9)
    for i, z in enumerate(top):
        nb = z['lhb_net_buy']
        lbl = PURE if nb > 0 else (WARN if nb < 0 else NONE)
        if not lbl or lbl.strip() == '':
            lbl = NONE
        notes = z.get('score_notes') or '\u65e0\u7279\u522b\u4fe1\u53f7'
        fill_row(t, i+1, [
            f"{z['code']} {z['name']}", z['line'], z['industry'],
            z['first_seal'], str(z['break_count']), to_yi(nb),
            lbl, notes, str(z['score'])
        ])

    # T11: Yijiner Top 10
    t = tables[11]
    yj = yijiner[:10]
    while len(t.rows) > len(yj) + 1:
        remove_row(t, len(t.rows) - 1)
    while len(t.rows) < len(yj) + 1:
        add_row(t, 10)
    if yj:
        for i, z in enumerate(yj):
            sc = z['score']
            rating = '高' if sc >= 90 else ('中' if sc >= 80 else '低')
            fill_row(t, i+1, [
                str(i+1), f"{z['code']} {z['name']}", z['line'],
                z['industry'], z['first_seal'], str(z['break_count']),
                to_yi(z['seal_funds']), to_yi(z['lhb_net_buy']),
                rating, str(sc)
            ])

    # T12-T16: detailed deep-review cards and one cross-stock summary card.
    for i in range(5):
        t = tables[12 + i]
        while len(t.rows) > 7:
            remove_row(t, len(t.rows) - 1)
        while len(t.rows) < 7:
            add_row(t, 2)
        if i < len(focus_stocks):
            z = focus_stocks[i]
            risk_result = z.get('risk_result') or {}
            risk_label = (
                '触发风险排除条件'
                if risk_result.get('final_action') == 'OUT'
                else f"风险公告已查，独立风险事项{sum((risk_result.get('independent_soft_event_counts') or {}).values())}组"
            )
            q_text = '有个股研报' if z.get('qsyb_bound') else '无个股研报'
            n_text = '有个股新闻' if z.get('rdxz_bound') else '无个股新闻'
            kd = z.get('k_line_detail') or {}
            d = kd.get('d') or {}
            factor_values = z.get('score_factors') or {}
            rows = [
                ('代码与结论', f"{z['code']} {z['name']}｜{z.get('classification', '观察')}｜{z['score']}分"),
                ('最近两天走势', f"收盘{d.get('close', z.get('price', 0))}元；涨幅{kd.get('d_pct_change', z.get('pct_change', 0))}%；数据{'通过' if z.get('k_line_verify') == 'PASS' else '未通过'}"),
                ('涨停牢固度', f"{z['lb']}板；第一次封住{z.get('first_seal', '-')}；最后一次封住{z.get('last_seal', '-')}；打开涨停{z.get('break_count', 0)}次；收盘封单{to_yi(z.get('seal_funds', 0))}"),
                ('资金情况', f"成交额{to_yi(z.get('amount', 0))}；换手{z.get('turnover', 0):.2f}%；公开席位净买{to_yi(z.get('lhb_net_buy', 0))}"),
                ('八项评分', f"连板高度{factor_values.get('board_ladder', 0)}/15；涨停牢固度{factor_values.get('limit_quality', 0)}/20；买入力度{factor_values.get('capital', 0)}/15；热门方向{factor_values.get('sector_main', 0)}/15"),
                ('资料与风险', f"{q_text}；{n_text}；{risk_label}"),
            ]
            for ri, (label, value) in enumerate(rows, start=1):
                set_cell_text(t.rows[ri].cells[0], label, bold=True)
                set_cell_text(t.rows[ri].cells[1], value)
            continue
        summary_rows = [
            ('市场数字', f"涨停{summary['zt_total']}只；连板{summary['zt_lb']}只；首板{summary['zt_first']}只"),
            ('本地股票', f"逐只查看{len(zt_scored)}只；风险公告查完{sum(1 for z in zt_scored if z.get('risk_review_complete'))}/{len(zt_scored)}"),
            ('正式候选', f"正式候选{summary['pick_count']}只；观察{sum(1 for z in zt_scored if z.get('classification') == '观察')}只"),
            ('风险排除', f"排除{sum(1 for z in zt_scored if z.get('classification') == '剔除')}只"),
            ('资料情况', f"个股研报{sum(1 for z in zt_scored if z.get('qsyb_bound'))}/{len(zt_scored)}；个股新闻{sum(1 for z in zt_scored if z.get('rdxz_bound'))}/{len(zt_scored)}"),
            ('核心原则', '没有个股研报不加分；价格数据不全或触发风险条件直接排除'),
        ]
        for ri, (label, value) in enumerate(summary_rows, start=1):
            set_cell_text(t.rows[ri].cells[0], label, bold=True)
            set_cell_text(t.rows[ri].cells[1], value)

    # T17: Risky
    t = tables[17]
    while len(t.rows) > len(risky) + 1:
        remove_row(t, len(t.rows) - 1)
    while len(t.rows) < len(risky) + 1:
        add_row(t, 8)
    for i, z in enumerate(risky):
        reasons = []
        if z['lhb_net_buy'] < -2e7:
            reasons.append('\u9f99\u864e\u699c\u51c0\u5356>0.2\u4ebf')
        if z['break_count'] > 7:
            reasons.append('\u70b8\u677f>7\u6b21')
        nb = z['lhb_net_buy']
        fill_row(t, i+1, [
            f"{z['code']} {z['name']}", z['line'], z['industry'],
            str(z['lb']), str(z['break_count']),
            to_yi(nb), to_yi(nb),
            ';'.join(reasons) or '触发风险排除条件'
        ])

    # T18: Flow
    t = tables[18]
    flow = [
        ('第一至十步', f"涨停{summary['zt_total']}只、首板{summary['zt_first']}只、连板{summary['zt_lb']}只；公开交易席位榜交集{summary['lhb_in_zt']}只、热门方向{summary['line_count']}条；研报{summary['qsyb_total']}条、新闻{summary['rdxz_total']}条；逐只查看{len(zt_scored)}只、正式候选{summary['pick_count']}只、观察{sum(1 for z in zt_scored if z.get('classification') == '观察')}只、排除{summary['risky_count']}只"),
    ]
    while len(t.rows) > len(flow) + 1:
        remove_row(t, len(t.rows) - 1)
    while len(t.rows) < len(flow) + 1:
        add_row(t, 2)
    for i, (step_label, result) in enumerate(flow, start=1):
        if len(t.rows[i].cells) >= 2:
            set_cell_text(t.rows[i].cells[0], step_label, bold=True)
            set_cell_text(t.rows[i].cells[1], result)

    # Apply data-aware narratives and final layout only after all dynamic rows
    # have been materialized, so every generated row receives the same geometry.
    data_date = f"{args.date[:4]}-{args.date[4:6]}-{args.date[6:8]}"
    set_section_narrative(paras, analyzed, raw_data, data_date)
    sanitize_document_visible_text(doc)
    polish_document_layout(doc)
    reflow_tables_to_sections(doc, tables, focus_stocks)
    add_report_footer(doc, f"{args.date[:4]}-{args.date[4:6]}-{args.date[6:8]}")
    add_stock_risk_notice_page(doc)
    embed_stock_data_evidence(doc, args.data_evidence, args.date)

    # Word creates an implicit end paragraph when a document ends with a table.
    # Materialize it at minimum height so it cannot become a blank trailing page.
    end_para = doc.add_paragraph()
    end_para.paragraph_format.space_before = Pt(0)
    end_para.paragraph_format.space_after = Pt(0)
    end_para.paragraph_format.line_spacing = Pt(1)
    end_run = end_para.add_run('')
    end_run.font.size = Pt(1)

    # Save
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    doc.save(args.out)
    size = Path(args.out).stat().st_size
    print(f"\nSaved: {args.out} ({size} bytes)")


if __name__ == '__main__':
    main()
