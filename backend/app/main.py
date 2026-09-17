import os
from typing import Annotated
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from app.services.pdf_parser import extract_resume_text, ResumeLimitExceeded
from app.limits import MAX_JD_CHARACTERS
from app.middleware import AnalysisLimitsMiddleware
from app.services.skill_matcher import compare_skills
from starlette.concurrency import run_in_threadpool
from pdfplumber.utils.exceptions import PdfminerException
from app.services.ai_feedback import (
    generate_ai_feedback,
    AIFeedbackUnavailable,
)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(AnalysisLimitsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if origin.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "resume-picker-api"
    }

@app.post("/analyze")
async def analyze_resume(resume: Annotated[UploadFile, File()], job_description: Annotated[str, Form()], include_ai: Annotated[bool, Form()] = False):
    try:
        max_bytes = 5*1024*1024
        if len(job_description) > MAX_JD_CHARACTERS:
            raise HTTPException(status_code=422, detail="Job description must be at most 10,000 characters.")
        if job_description is None or len(job_description.strip()) == 0:
            raise HTTPException(
                status_code=422,
                detail="Job description is required"
            )
        if resume.content_type != "application/pdf":
            raise HTTPException(
                status_code=415,
                detail="Unsupported file type. Please upload PDF format only."
            )
        contents = await resume.read(max_bytes+1)
        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded. Please upload a valid resume."
            )
        if len(contents) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds the limit of 5MB."
            )
        try:
            resume_text = await run_in_threadpool(extract_resume_text, contents)
        except ResumeLimitExceeded as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        except PdfminerException:
            raise HTTPException(
                status_code=400,
                detail="Unable to read this PDF. Please upload a valid PDF."
            )
        if resume_text == "":
            raise HTTPException(
                status_code=422,
                detail="No extractable text found. Please upload a text-based PDF."
            )
        skill_match = await run_in_threadpool(compare_skills, resume_text, job_description)
        ai_feedback = None
        ai_status = "not_requested"
        if include_ai:
            try:
                feedback = await run_in_threadpool(generate_ai_feedback,resume_text, job_description)
                ai_feedback = feedback.model_dump()
                ai_status = "available"
            except AIFeedbackUnavailable:
                ai_status = "unavailable"
        return {
            "status": 200,
            "filename": resume.filename,
            "size_bytes": len(contents),
            "jd_characters": len(job_description.strip()),
            "resume_text": resume_text,
            "skill_match": skill_match,
            "ai_feedback": ai_feedback,
            "ai_status": ai_status
        }
    finally:
        await resume.close()
