# ResumePicker

ResumePicker is a local MVP with a React frontend and FastAPI backend. It extracts text from a PDF resume, compares supported skills against a job description, and optionally requests structured feedback from Google Gemini.

This project is a hands-on way to learn backend development, React, testing, external API integration, and eventually CI/CD.

## Current functionality

- Browser form for PDF upload and job description entry, with loading and error states.
- Optional AI feedback checkbox, off by default, with an explanation that enabling it sends resume text and the job description to Google.
- On-page matched/missing skills, supported-skill coverage, and AI summary, strengths, gaps, and suggestions. Unavailable and unrequested AI feedback have separate messages.
- PDF text extraction, including multiple pages.
- Upload validation: nonempty PDF declared as `application/pdf`, up to 5 MiB, and a nonempty job description.
- Case-insensitive, whole-word skill matching with matched skills, missing skills, and coverage percentage.
- Optional AI summary, strengths, gaps, and suggestions, validated with Pydantic.
- Skill results remain available when a handled AI failure occurs.
- PDF parsing, matching, and synchronous Gemini requests run in worker threads.
- Upload cleanup on success and failure.
- CORS allows the local frontend at `http://localhost:5173` and `http://127.0.0.1:5173`.

## Tech stack

- Frontend: React, JavaScript, Vite, and ESLint; Node.js and npm for development.
- Backend: Python 3.13+, FastAPI, pdfplumber, Google Gen AI SDK, Pydantic, python-dotenv, and uv.
- Backend tests: pytest and ReportLab to create synthetic PDFs.

## Setup and run

Install Python, uv, and Node.js with npm. The frontend was developed using Node.js 22.12.0.

### Backend

From the repository root, run in PowerShell:

```powershell
cd backend
uv sync
uv run fastapi dev app/main.py
```

Open [Swagger UI](http://127.0.0.1:8000/docs) to try the endpoints. PDF extraction and skill matching work without a Gemini key.

### Frontend

In a second PowerShell terminal, start from the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Keep both servers running and open [ResumePicker](http://localhost:5173). The frontend currently sends requests to `http://localhost:8000/analyze`. Use port 5173 for the frontend, matching the backend's local CORS configuration; if Vite selects another port, free port 5173 and restart it.

Upload a text-based PDF of up to 5 MiB, paste a job description, and select **Analyze**. Leave **Include AI Feedback** unchecked to use skill matching without Google. Enabling it requires the optional backend configuration below.

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

## Tests and frontend checks

### Backend tests

From `backend`:

```powershell
uv run python -m pytest -v
```

The suite contains 23 tests covering PDF extraction, upload validation (including the 5 MiB boundary), skill matching, default AI behavior, missing AI configuration, and preservation of skill results when AI configuration is absent.

Tests use synthetic PDFs and do not require live Gemini requests. AI success has been checked manually but has no automated success-path test. Provider timeouts, quota failures, and malformed AI responses are not yet covered by automated tests. Dependency deprecation warnings may appear during testing.

### Frontend checks

From `frontend`:

```powershell
npm run lint
npm run build
```

These check lint rules and the production build. Browser flows have been checked manually during development; there are no automated frontend interaction tests yet. Lint and build checks do not verify end-to-end behavior.

### Local release checks — September 17, 2026

- Backend: all 23 tests passed, with two dependency deprecation warnings.
- Frontend: lint and production build passed.
- Browser checks with synthetic files passed: missing resume, whitespace-only JD, successful upload (50% coverage), invalid PDF, blank PDF, recovery after validation errors, no recognized JD skills, and zero coverage.
- Loading disabled the Analyze button; completed requests restored it. Stopping the backend produced the request-failure message, cleared previous results, and restored the button.
- At a 375-pixel viewport, the form and skill results fit without horizontal overflow.
- Live Gemini behavior was not rerun in this pass. Earlier manual AI checks and the automated coverage gaps described above still apply. Public deployment verification remains pending.

## Limitations and next steps

- No OCR: image-only PDFs without a text layer cannot yield text.
- Extracted spacing and layout may differ from the original PDF.
- Skill matching uses a small, fixed vocabulary rather than semantic understanding.
- Pydantic checks AI response structure, not factual accuracy; feedback can be wrong.
- This is a local MVP without authentication, application rate limiting, or a database.
- Before public deployment: add input-length and request/AI usage limits, configure production CORS and the API URL, and review data-sharing consent.
- Next: add frontend and AI failure tests, CI, deployment, and safe error logging; improve matching with realistic synthetic examples.
