# ResumePicker

ResumePicker is an AI Resume / Job Description Analyzer in development. The current backend accepts a PDF resume and a job description, extracts the resume’s text, and validates the inputs.

This project is a hands-on way to learn backend development, testing, and eventually an end-to-end CI/CD workflow.

## Current functionality

- Health-check endpoint.
- PDF upload with a nonempty job description.
- Text extraction from single-page and multi-page PDFs.
- Validation for empty uploads, incorrect declared content types, and files larger than 5 MiB.
- Clear responses for unreadable PDFs and PDFs with no extractable text.
- PDF parsing in a worker thread to keep the event loop available.
- Automated tests using synthetic PDFs rather than personal resumes.

The job description is currently validated and counted; it is not compared against the resume yet.

## Tech stack

- Python 3.13+
- FastAPI
- pdfplumber
- uv for dependency management
- pytest and ReportLab for testing

## Setup and run

Install Python and uv, then run these commands in PowerShell:

```powershell
cd D:\Projects\ResumePicker\backend
uv sync
uv run fastapi dev app/main.py
```

Open the interactive API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## API endpoints

### `GET /health`

Returns the service status:

```json
{
  "status": "ok",
  "service": "resume-picker-api"
}
```

### `POST /analyze`

Accepts multipart form data:

| Field | Type | Description |
|---|---|---|
| `resume` | File | PDF with declared content type `application/pdf`, up to 5 MiB |
| `job_description` | Text | Nonempty job description; surrounding whitespace is ignored when counting characters |

A successful response includes:

- `status`: `200`
- `filename`: uploaded filename
- `size_bytes`: uploaded file size
- `jd_characters`: trimmed job description length
- `resume_text`: extracted text

Validation responses:

| HTTP status | Reason |
|---|---|
| `400` | Empty upload or PDF parsing failure |
| `413` | Upload exceeds 5 MiB |
| `415` | Declared content type is not `application/pdf` |
| `422` | Missing required fields, whitespace-only JD, or no extractable text |

## Run tests

From the `backend` directory:

```powershell
uv run python -m pytest -v
```

The current suite contains 12 tests covering PDF extraction, invalid PDFs, blank PDFs, successful API responses, and upload validation—including the 5 MiB boundary.

## Current limitations

- No OCR: scanned or image-only PDFs without a text layer cannot yield text.
- Extracted spacing and layout may differ from the original PDF.
- No structured resume fields, skill matching, scoring, or AI feedback yet.
- No database or React frontend yet.

## Planned work

- Compare resume content with job requirements.
- Add useful matching feedback.
- Build a React + Vite frontend.
- Add CI/CD.