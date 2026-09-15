from docx import Document
from docx.oxml.ns import qn

from scripts.build_docx import add_stock_risk_notice_page


def test_risk_notice_does_not_add_redundant_manual_page_break():
    doc = Document()
    doc.add_paragraph("report body")

    add_stock_risk_notice_page(doc)

    page_breaks = doc._element.xpath("//w:br[@w:type='page']")
    assert page_breaks == []
