import pytest

from app.services.ai_feedback import AIFeedbackUnavailable, generate_ai_feedback

def test_missing_api_key_disables_feedback(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(
        AIFeedbackUnavailable,
        match="AI feedback is not configured",
    ):
        generate_ai_feedback("Python developer", "Python required")