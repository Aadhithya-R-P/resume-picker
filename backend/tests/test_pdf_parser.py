import pytest
from pdfplumber.utils.exceptions import PdfminerException
from app.services.pdf_parser import extract_resume_text
from io import BytesIO
from reportlab.pdfgen import canvas

def test_invalid_pdf_raises():
    with pytest.raises(PdfminerException):
        extract_resume_text(b"This is not a PDF")

def test_blank_pdf_returns_empty_text():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.showPage()
    pdf.save()
    contents = buffer.getvalue()
    text = extract_resume_text(contents)
    assert text == ""

def test_text_pdf_returns_text():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, "Python backend developer")
    pdf.showPage()
    pdf.save()
    contents = buffer.getvalue()
    text = extract_resume_text(contents)
    assert text == "Python backend developer"

def test_multiple_pages_preserve_order():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, "First Page")
    pdf.showPage()
    pdf.drawString(72, 720, "Second Page")
    pdf.showPage()
    pdf.save()
    contents = buffer.getvalue()
    text = extract_resume_text(contents)
    assert text == "First Page\nSecond Page"