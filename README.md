# ResumePicker

ResumePicker is a backend MVP that extracts text from a PDF resume, compares supported skills against a job description, and optionally requests structured feedback from Google Gemini.

This project is a hands-on way to learn backend development, testing, external API integration, and eventually CI/CD. The React frontend is planned next.

## Current functionality

- PDF text extraction, including multiple pages.
- Upload validation: nonempty PDF declared as `application/pdf`, up to 5 MiB, and a nonempty job description.
- Case-insensitive, whole-word skill matching with matched skills, missing skills, and coverage percentage.
- Optional AI summary, strengths, gaps, and suggestions, validated with Pydantic.
- Skill results remain available when a handled AI failure occurs.
- PDF parsing, matching, and synchronous Gemini requests run in worker threads.
- Upload cleanup on success and failure.
- CORS allows the local frontend at `http://localhost:5173` and `http://127.0.0.1:5173`.

## Tech stack

Python 3.13+, FastAPI, pdfplumber, Google Gen AI SDK, Pydantic, python-dotenv, and uv. Tests use pytest and ReportLab to create synthetic PDFs.

## Setup and run

Install Python and uv. From the repository root, run in PowerShell:

```powershell
cd backend
uv sync
uv run fastapi dev app/main.py
```

Open [Swagger UI](http://127.0.0.1:8000/docs) to try the endpoints. PDF extraction and skill matching work without a Gemini key.

### Optional Gemini setup

Create a key in [Google AI Studio](https://aistudio.google.com/apikey). From `backend`, copy the template if you do not already have a `.env` file:

```powershell
Copy-Item .env.example .env
```

Set these values in `.env`:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.6-flash
```

This model was used in the project's manual integration check. Availability and quotas depend on your account and can change. Restart the server after changing settings.

Keep the real key in `.env`, which Git ignores. Commit only the empty-key `.env.example` template.

Setting `include_ai=true` sends the extracted resume text and job description to Google. Use synthetic documents for experiments and review the provider's data-use terms before sending personal or confidential information. With `include_ai=false`, the route does not call Gemini.

## API

### `GET /health`

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
| `resume` | File, required | PDF declared as `application/pdf`, up to 5 MiB |
| `job_description` | Text, required | Must contain non-whitespace text |
| `include_ai` | Boolean, optional | Defaults to `false`; use `true` for Gemini feedback |

A successful response contains:

| Field | Meaning |
|---|---|
| `status` | `200` |
| `filename` | Uploaded filename |
| `size_bytes` | Uploaded file size |
| `jd_characters` | Job description length after trimming surrounding whitespace |
| `resume_text` | Extracted text |
| `skill_match` | Matched skills, missing skills, and supported-skill coverage |
| `ai_status` | `not_requested`, `available`, or `unavailable` |
| `ai_feedback` | Feedback object when available; otherwise `null` |

Example `skill_match` for a resume mentioning Python and SQL against a JD requesting Python, SQL, and Docker:

```json
{
  "matched_skills": ["python", "sql"],
  "missing_skills": ["docker"],
  "skill_coverage_percent": 66.7
}
```

When available, `ai_feedback` contains a `summary` string and three lists of strings: `strengths`, `gaps`, and `suggestions`.

### How skill coverage works

Supported skills: **Python, Java, JavaScript, FastAPI, React, SQL, Docker, and Git**.

Coverage = matched skill count / recognized JD skill count * 100, rounded to one decimal place. When no supported JD skills are recognized, coverage is `null`.

This measures supported-skill keyword coverage, not hiring probability or proficiency. Unsupported skills are excluded. For example, GitHub and Kubernetes are not currently recognized, and Git does not match inside GitHub. The matcher does not interpret context such as negation.

### Errors and AI fallback

| HTTP status | Reason |
|---|---|
| `400` | Empty upload or a handled PDF parsing failure |
| `413` | Upload exceeds 5 MiB |
| `415` | Declared content type is not `application/pdf` |
| `422` | Missing or invalid form fields, whitespace-only JD, or no extractable text |

Gemini requests use a 30-second SDK request timeout and one attempt, without automatic retries. Missing AI configuration, handled provider/network errors, empty AI responses, or invalid feedback structure produce `ai_status: "unavailable"` and `ai_feedback: null`. The route still returns HTTP `200` with the extracted text and skill results.

## Tests

From `backend`:

```powershell
uv run python -m pytest -v
```

The suite contains 23 tests covering PDF extraction, upload validation (including the 5 MiB boundary), skill matching, default AI behavior, missing AI configuration, and preservation of skill results when AI configuration is absent.

Tests use synthetic PDFs and do not require live Gemini requests. AI success has been checked manually. Provider timeouts, quota failures, and malformed AI responses are not yet covered by automated tests. Dependency deprecation warnings may appear during testing.

## Limitations and next steps

- No OCR: image-only PDFs without a text layer cannot yield text.
- Extracted spacing and layout may differ from the original PDF.
- Skill matching uses a small, fixed vocabulary rather than semantic understanding.
- Pydantic checks AI response structure, not factual accuracy; feedback can be wrong.
- This is a local MVP without authentication, application rate limiting, or a database.
- Next: build the React + Vite frontend, expand coverage where needed, and add CI/CD.
