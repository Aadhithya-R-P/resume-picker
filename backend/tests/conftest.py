import pytest
from app import limits


@pytest.fixture(autouse=True)
def isolated_usage_limits(monkeypatch):
    """Each test gets a fresh demo allowance, just like a fresh server process."""
    monkeypatch.setattr(limits, "analysis_admission", limits.AnalysisAdmission())
    monkeypatch.setattr(limits, "ai_usage", limits.UsageLimiter([(2, 60), (15, 86400)]))
