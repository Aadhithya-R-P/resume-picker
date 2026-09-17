from app.services.skill_matcher import extract_skills, compare_skills

def test_extract_skills_normalizes_case_and_returns_unique_skills():
    assert extract_skills("Python, FASTAPI, Python and JavaScript") == ["fastapi", "javascript", "python"]

def test_extract_skills_avoids_partial_word_matches():
    assert extract_skills("javascript digital") == ["javascript"]

def test_extract_skills_handles_punctuation():
    assert extract_skills("Python/SQL, Docker.") == ["docker", "python", "sql"]

def test_extract_skills_returns_empty_for_empty_text():
    assert extract_skills("") == []

def test_extract_skills_returns_empty_when_no_skills_match():
    assert extract_skills("Communication and teamwork") == []

def test_compare_skills_partial_match():
    assert compare_skills("Python SQL", "Python SQL Docker") == {"matched_skills": ["python", "sql"], "missing_skills": ["docker"], "skill_coverage_percent": 66.7}

def test_compare_skills_full_match():
    assert compare_skills("Python SQL Git", "Python SQL") == {"matched_skills": ["python", "sql"], "missing_skills": [], "skill_coverage_percent": 100.0}

def test_compare_skills_no_match():
    assert compare_skills("Java", "Python") == {"matched_skills": [], "missing_skills": ["python"], "skill_coverage_percent": 0.0}

def test_compare_skills_no_recognized_jd_skills():
    assert compare_skills("Python", "Teamwork") == {"matched_skills": [], "missing_skills": [], "skill_coverage_percent": None} 