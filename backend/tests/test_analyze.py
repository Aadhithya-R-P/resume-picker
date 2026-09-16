from fastapi.testclient import TestClient
from app.main import app
from io import BytesIO
from reportlab.pdfgen import canvas

client = TestClient(app)

def test_invalid_pdf_returns_400():
    response = client.post(
        "/analyze",
        files={"resume": ("invalid.pdf", b"This is not a PDF", "application/pdf")},
        data={"job_description": "Python developer"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unable to read this PDF. Please upload a valid PDF."

def test_blank_pdf_returns_422():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.showPage()
    pdf.save()
    contents = buffer.getvalue()
    response = client.post(
        "/analyze",
        files={"resume": ("blank.pdf", contents, "application/pdf")},
        data={"job_description": "Python developer"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "No extractable text found. Please upload a text-based PDF."

def test_text_pdf_returns_200():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72,720, "FastAPI developer")
    pdf.showPage()
    pdf.save()
    contents = buffer.getvalue()
    response = client.post(
        "/analyze",
        files={"resume": ("resume.pdf", contents, "application/pdf")},
        data={"job_description": " Python developer "},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["resume_text"] == "FastAPI developer"
    assert body["filename"] == "resume.pdf"
    assert body["size_bytes"] == len(contents)
    assert body["jd_characters"] == len("Python developer")

def test_whitespace_jd_returns_422():
    response = client.post(
        "/analyze",
        files={"resume": ("resume.pdf", b"placeholder", "application/pdf")},
        data={"job_description": "   "},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Job description is required"

def test_non_pdf_content_type_returns_415():
    response = client.post(
        "/analyze",
        files={"resume": ("resume.txt", b"Some text", "text/plain")},
        data={"job_description": "SOme random"},
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported file type. Please upload PDF format only."

def test_empty_upload_returns_400():
    response = client.post(
        "/analyze",
        files={"resume": ("empty.pdf", b"", "application/pdf")},
        data={"job_description": "SOme random"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file uploaded. Please upload a valid resume."

def test_oversized_upload_returns_413():
    response = client.post(
        "/analyze",
        files={"resume": ("large.pdf", b"x"* (5 * 1024 * 1024 + 1), "application/pdf")},
        data={"job_description": "SOme random"},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File size exceeds the limit of 5MB."

def test_exact_size_limit_reaches_parser():
    response = client.post(
        "/analyze",
        files={"resume": ("limit.pdf", b"x"* (5 * 1024 * 1024), "application/pdf")},
        data={"job_description": "SOme random"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unable to read this PDF. Please upload a valid PDF."
    