from typing import Annotated
from fastapi import FastAPI, File, UploadFile, Form, HTTPException

app = FastAPI()

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "resume-picker-api"
    }

@app.post("/analyze")
async def analyze_resume(resume: Annotated[UploadFile, File()], job_description: Annotated[str, Form()]):
    try:
        max_bytes = 5*1024*1024
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
        return {
            "status": 200,
            "filename": resume.filename,
            "size_bytes": len(contents),
            "jd_characters": len(job_description.strip())
        }
    finally:
        await resume.close()
