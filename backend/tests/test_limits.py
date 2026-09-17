from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from threading import Event
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app import limits, main
from app.main import app
from app.schemas import AIFeedback
from app.services import ai_feedback, pdf_parser


def make_pdf(pages=1):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    for _ in range(pages):
        pdf.drawString(72, 720, "Python developer")
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def analyze(client, contents=None, jd="Python Docker", ai=False):
    return client.post(
        "/analyze",
        files={"resume": ("synthetic.pdf", contents if contents is not None else make_pdf(), "application/pdf")},
        data={"job_description": jd, "include_ai": str(ai).lower()},
    )


@pytest.mark.parametrize("length,status", [(10_000, 200), (10_001, 422)])
def test_jd_boundary(length, status):
    with TestClient(app) as client:
        assert analyze(client, jd="x" * length).status_code == status


@pytest.mark.parametrize("pages,status", [(10, 200), (11, 422)])
def test_page_boundary(pages, status):
    with TestClient(app) as client:
        assert analyze(client, contents=make_pdf(pages)).status_code == status


@pytest.mark.parametrize("length,status", [(30_000, 200), (30_001, 422)])
def test_extracted_text_boundary(monkeypatch, length, status):
    # Simulate long extraction without making the test parse a huge PDF.
    page = Mock()
    page.extract_text.return_value = "x" * length
    document = Mock(pages=[page])
    from contextlib import nullcontext
    monkeypatch.setattr(pdf_parser.pdfplumber, "open", lambda _: nullcontext(document))
    with TestClient(app) as client:
        assert analyze(client).status_code == status


def test_request_limit_and_health_exemption():
    with TestClient(app) as client:
        for _ in range(10):
            assert analyze(client, contents=b"invalid").status_code == 400
        response = analyze(client)
        assert response.status_code == 429
        assert response.headers["retry-after"] == "60"
        assert client.get("/health").status_code == 200


def test_busy_request_rejected_then_slot_released(monkeypatch):
    started, release = Event(), Event()

    def slow_extract(_):
        started.set()
        assert release.wait(timeout=5)
        return "Python"

    monkeypatch.setattr(main, "extract_resume_text", slow_extract)
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(analyze, client)
        try:
            assert started.wait(timeout=5)
            assert analyze(client).status_code == 429
        finally:
            release.set()
        assert first.result(timeout=5).status_code == 200
        assert analyze(client).status_code == 200


def test_parser_error_releases_slot():
    with TestClient(app) as client:
        assert analyze(client, contents=b"invalid").status_code == 400
        assert analyze(client).status_code == 200


def test_rolling_minute_and_daily_allowances():
    now = [0.0]
    limiter = limits.UsageLimiter([(2, 60), (15, 86400)], clock=lambda: now[0])
    assert limiter.reserve()
    assert limiter.reserve()
    assert not limiter.reserve()
    now[0] = 59
    assert not limiter.reserve()
    now[0] = 60
    assert limiter.reserve()
    for _ in range(12):
        now[0] += 60
        assert limiter.reserve()
    now[0] += 60
    assert not limiter.reserve()  # 15 attempts still inside 24 hours.
    now[0] = 86400
    assert limiter.reserve()  # The first attempts have expired.


def test_parallel_ai_reservations_do_not_exceed_limit():
    limiter = limits.UsageLimiter([(2, 60)])
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(lambda _: limiter.reserve(), range(20))) == 2


def test_ai_allowance_preserves_skill_results(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("GEMINI_MODEL", "synthetic-model")
    assert limits.ai_usage.reserve()
    assert limits.ai_usage.reserve()
    provider = Mock(side_effect=AssertionError("Provider must not be called"))
    monkeypatch.setattr(ai_feedback.genai, "Client", provider)
    with TestClient(app) as client:
        response = analyze(client, ai=True)
    assert response.status_code == 200
    assert response.json()["ai_status"] == "unavailable"
    assert response.json()["ai_feedback"] is None
    assert response.json()["skill_match"]["matched_skills"] == ["python"]
    provider.assert_not_called()


def test_ai_success_route(monkeypatch):
    monkeypatch.setattr(main, "generate_ai_feedback", lambda *_: AIFeedback(
        summary="Python matches.", strengths=["Python"], gaps=["Docker"], suggestions=[]
    ))
    with TestClient(app) as client:
        response = analyze(client, ai=True)
    assert response.status_code == 200
    assert response.json()["ai_status"] == "available"
    assert response.json()["ai_feedback"]["strengths"] == ["Python"]
