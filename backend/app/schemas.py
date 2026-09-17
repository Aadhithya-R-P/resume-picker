from pydantic import BaseModel

class AIFeedback(BaseModel):
    summary: str
    strengths: list[str]
    gaps: list[str]
    suggestions: list[str]