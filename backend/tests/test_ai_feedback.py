import pytest
import httpx
from unittest.mock import MagicMock
from google.genai import errors
from app.services import ai_feedback
from app import limits

from app.services.ai_feedback import AIFeedbackUnavailable, generate_ai_feedback

def test_missing_api_key_disables_feedback(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(
        AIFeedbackUnavailable,
        match="AI feedback is not configured",
    ):
        generate_ai_feedback("Python developer", "Python required")


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("GEMINI_MODEL", "synthetic-model")
    factory = MagicMock()
    monkeypatch.setattr(ai_feedback.genai, "Client", factory)
    return factory.return_value.__enter__.return_value.models.generate_content


def test_valid_feedback_and_output_cap(provider):
    provider.return_value.text = '{"summary":"Match", "strengths":["Python"], "gaps":[], "suggestions":[]}'
    result = generate_ai_feedback("Python developer", "Python required")
    assert result.strengths == ["Python"]
    assert provider.call_args.kwargs["config"]["max_output_tokens"] == 2048


@pytest.mark.parametrize("output", [None, "not JSON", '{"summary":42}'])
def test_empty_or_malformed_feedback(provider, output):
    provider.return_value.text = output
    with pytest.raises(AIFeedbackUnavailable):
        generate_ai_feedback("Python", "Python")


@pytest.mark.parametrize("failure", [httpx.ReadTimeout("synthetic private text"), errors.ClientError(429, {"error": {"message": "synthetic private text"}})])
def test_provider_failure_counts_and_logs_safely(provider, failure, caplog):
    provider.side_effect = failure
    with pytest.raises(AIFeedbackUnavailable):
        generate_ai_feedback("Python", "Python")
    assert "synthetic private text" not in caplog.text
    assert "AI feedback unavailable" in caplog.text
    assert limits.ai_usage.reserve()
    assert not limits.ai_usage.reserve()


@pytest.mark.parametrize("resume,jd", [("x" * 30_001, "Python"), ("Python", "x" * 10_001)])
def test_ai_rejects_excess_input_without_calling_provider(provider, resume, jd):
    with pytest.raises(AIFeedbackUnavailable):
        generate_ai_feedback(resume, jd)
    provider.assert_not_called()
