import os

from dotenv import load_dotenv
from google import genai
from app.schemas import AIFeedback

load_dotenv()

with genai.Client(api_key=os.environ["GEMINI_API_KEY"]) as client:
    response = client.models.generate_content(
        model=os.environ["GEMINI_MODEL"],
        contents=(
            "Compare this resume with the job description. "
            "Give a summary, strengths, gaps, and actionable suggestions. "
            "Use only the supplied evidence; do not invent experience. "
            "A skill not mentioned is not proof the candidate lacks it.\n\n"
            "Resume: Built a FastAPI service in Python with automated tests.\n"
            "Job description: Seeking Python, FastAPI, SQL, and Docker experience."
        ),
        config={
            "response_mime_type": "application/json",
            "response_schema": AIFeedback,
        },
    )
    feedback = AIFeedback.model_validate_json(response.text)
    print(feedback.model_dump_json(indent=2))