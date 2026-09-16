import re

SUPPORTED_SKILLS = {
    "python", "java", "javascript", "fastapi",
    "react", "sql", "docker", "git",
}


def extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    skills = []
    for skill in SUPPORTED_SKILLS:
        pattern = rf"\b{re.escape(skill)}\b"
        if re.search(pattern, text_lower):
            skills.append(skill)
    return sorted(skills)

def compare_skills(resume_text: str, job_description: str) -> dict:
    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_description))
    matched_skills = resume_skills.intersection(job_skills)
    missing_skills = job_skills.difference(resume_skills)
    return {
        "matched_skills": sorted(matched_skills),
        "missing_skills": sorted(missing_skills),
        "skill_coverage_percent": round(len(matched_skills)/len(job_skills) * 100, 1) if job_skills else None
    }