# ResumePicker

ResumePicker is a deployed portfolio project with a React frontend and FastAPI backend. It extracts text from a PDF resume, compares supported skills against a job description, and optionally requests structured feedback from Google Gemini.

**[Try ResumePicker](https://resume-picker.vercel.app/)** · **[API documentation](https://resume-picker-rxx1.onrender.com/docs)** · **[API health](https://resume-picker-rxx1.onrender.com/health)** · **[CI runs](https://github.com/Aadhithya-R-P/resume-picker/actions)**

The frontend is hosted on Vercel Hobby and the backend on Render Free. The backend can sleep after inactivity, so the first visit may need about a minute to connect. The page displays its connection status and offers Reconnect if startup takes longer. AI feedback shares a small allowance across visitors; skill comparison remains available when handled AI failures or exhausted AI quotas prevent feedback.

Use a synthetic resume when trying the demo. AI is off by default; enabling it sends extracted resume text and the job description to Google.

## Current functionality

- Browser form for PDF upload and job description entry, with loading and error states.
- Optional AI feedback checkbox, off by default, with an explanation that enabling it sends resume text and the job description to Google.
- On-page matched/missing skills, supported-skill coverage, and AI summary, strengths, gaps, and suggestions. Unavailable and unrequested AI feedback have separate messages.
- PDF text extraction, including multiple pages.
- Upload validation: nonempty PDF declared as `application/pdf`, up to 5 MiB, 10 pages, and 30,000 extracted characters; a nonempty job description of at most 10,000 characters.
- Case-insensitive, whole-word skill matching with matched skills, missing skills, and coverage percentage.
- Optional AI summary, strengths, gaps, and suggestions, validated with Pydantic.
- Skill results remain available when a handled AI failure occurs.
- PDF parsing, matching, and synchronous Gemini requests run in worker threads.
- Upload cleanup on success and failure.
- CORS defaults to the local frontend at `http://localhost:5173` and `http://127.0.0.1:5173`; set `CORS_ORIGINS` to a comma-separated list of exact frontend origins in production.

## Tech stack

- Frontend: React, JavaScript, Vite, and ESLint; Node.js and npm for development.
- Backend: Python 3.13+, FastAPI, pdfplumber, Google Gen AI SDK, Pydantic, python-dotenv, and uv.
- Backend tests: pytest and ReportLab to create synthetic PDFs.
- CI: GitHub Actions; hosting: Vercel and Render.

## Architecture and tradeoffs

```text
Browser (React frontend served by Vercel)
  |-- GET /health --> FastAPI on Render
  |-- POST /analyze (PDF + JD + AI choice)
                       |-- Shared request limit and single-analysis admission
                       |-- Validate input and extract PDF text with pdfplumber
                       |-- Match supported skills using whole-word regexes
                       |-- Optionally call Gemini and validate its JSON response
                       `-- Return skill results and available AI feedback
```

The browser calls Render directly. `VITE_API_URL` selects the backend during the frontend build, and `CORS_ORIGINS` allows the exact frontend origin. Gemini credentials exist only on the backend. The app does not intentionally retain uploaded resumes in a database or an uploads directory; multipart handling may use temporary files, and the upload is closed after processing.

Deterministic keyword matching keeps the core result understandable and independent of Gemini. Optional AI adds qualitative feedback but can be unavailable or inaccurate. Synchronous PDF parsing and Gemini calls run in worker threads so they do not block the event loop. One admitted analysis at a time limits concurrency on the small backend, at the cost of rejecting simultaneous visitors. Process-local limits avoid a database but reset when the process restarts; they are not durable usage accounting.

## Setup and run

Install Python, uv, and Node.js with npm. The frontend was developed using Node.js 22.12.0.

### Backend

From the repository root, run in PowerShell:

```powershell
cd backend
uv sync --locked
uv run fastapi dev app/main.py
```

Open [Swagger UI](http://127.0.0.1:8000/docs) to try the endpoints. PDF extraction and skill matching work without a Gemini key.

### Frontend

In a second PowerShell terminal, start from the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Keep both servers running and open [ResumePicker](http://localhost:5173). The frontend defaults to `http://localhost:8000`; set `VITE_API_URL` before building to use a deployed backend. This is public configuration, never a place for API keys. Use port 5173 for local development, matching the backend's default CORS configuration.

The frontend checks `/health` on opening and before each upload, waiting roughly 90 seconds for a sleeping backend. Analyze is disabled until the initial check succeeds, and Reconnect is offered if it fails. Upload requests time out after 60 seconds and are not automatically retried. A browser timeout does not guarantee cancellation of backend work.

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

This model was used in the project's manual integration check. The template currently names `gemini-2.5-flash`; replace it with the exact model ID available to your project. Availability and quotas depend on your account and can change. Restart the server after changing settings.

Keep the real key in `.env`, which Git ignores. Commit only the empty-key `.env.example` template.

Setting `include_ai=true` sends the extracted resume text and job description to Google. Use synthetic documents for experiments and review the provider's data-use terms before sending personal or confidential information. With `include_ai=false`, the route does not call Gemini.

## Deployment

The initial deployment uses `feat/resume-upload` on both hosts. Moving the production branches to `main` after the release merge remains a release task.

### Backend: Render Free

Create a Python Web Service connected to this GitHub repository:

| Setting | Value |
|---|---|
| Root directory | `backend` |
| Instance type | Free |
| Build command | `uv sync --locked --no-dev` |
| Start command | `.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1` |
| Health check path | `/health` |
| Auto-deploy | Select **After CI Checks Pass** |

The start command is for Render's Linux shell; Render supplies `$PORT`. Use one worker and one instance so the shared in-memory limits apply to the entire service.

Set these environment variables in Render:

| Variable | Value or purpose |
|---|---|
| `PYTHON_VERSION` | `3.13.1`, matching the initial deployment setup |
| `UV_VERSION` | `0.12.13` |
| `CORS_ORIGINS` | `https://resume-picker.vercel.app` (no trailing slash) |
| `GEMINI_API_KEY` | Your private key; enter directly in Render |
| `GEMINI_MODEL` | Exact model ID available to the key's project |

Save settings and redeploy. Check `/health` for `{"status":"ok","service":"resume-picker-api"}`. AI configuration is optional: missing configuration leaves skill matching available. For this demo, the owner confirmed a Gemini free-tier project with no billing account; provider limits remain project-specific and can change.

### Frontend: Vercel Hobby

Import the same repository and configure:

| Setting | Value |
|---|---|
| Framework | Vite |
| Root directory | `frontend` |
| Install command | `npm ci` |
| Build command | `npm run build` |
| Output directory | `dist` |
| `VITE_API_URL` | `https://resume-picker-rxx1.onrender.com` |

Set `VITE_API_URL` for the environments you deploy (Production and Preview in this setup), then build and deploy. Vite embeds this value into the JavaScript bundle: changing the environment variable requires a new build. Without it, the frontend falls back to localhost, which refers to the visitor's computer. Never put a Gemini key in a `VITE_` variable.

Ensure the selected branch contains `frontend`. If import selects an older default branch, set the project's production branch under **Settings → Environments → Production**, set the root directory under **Build and Deployment**, and create a fresh deployment from the intended branch.

Use the stable production domain for public sharing and CORS. Unique deployment URLs can require Vercel authentication and have different origins. If deploying your own copy, replace both URLs above with your own frontend/backend addresses and redeploy the affected services.

### CI and release flow

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on pushes, pull requests targeting `main`, and manual dispatch. Two independent Linux jobs run backend tests with Python 3.13/uv and frontend lint/build with Node.js 22.12.0. Dependency installation uses the lockfiles; tests require no Gemini credentials or live API calls.

CI checks code but does not itself deploy it or prevent merging. Configure required checks in GitHub where available, Render's **After CI Checks Pass** setting, and Vercel's production branch. Vercel's Git integration does not automatically wait for this workflow; merging only after CI passes is part of the release process.

After changes: push, review CI, merge when ready, and verify the hosts deployed the intended commit. Check the public page's connection status, a synthetic upload without AI, an optional AI submission, and a validation error. Confirm both hosts track `main` when completing the release.

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
| `job_description` | Text, required | Must contain non-whitespace text; at most 10,000 characters, including whitespace |
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
| `422` | JD exceeds 10,000 characters, PDF exceeds 10 pages, or extracted text exceeds 30,000 characters |
| `429` | Shared analysis request allowance exhausted, or another analysis is running; includes `Retry-After` |

Gemini requests use a 30-second SDK request timeout and one attempt, without automatic retries. Missing AI configuration, handled provider/network errors, empty AI responses, or invalid feedback structure produce `ai_status: "unavailable"` and `ai_feedback: null`. The route still returns HTTP `200` with the extracted text and skill results.

### Shared demo limits

- At most 10 analysis attempts per rolling minute across all visitors. Invalid and busy attempts count toward this allowance. Admission happens before multipart parsing; only one analysis request is admitted at a time, with no waiting queue. Health checks remain available.
- At most 2 AI attempts per rolling minute and 15 per rolling 24 hours. Failed provider attempts count; missing configuration and oversized input do not. An exhausted allowance preserves HTTP 200 and skill results with AI unavailable.
- AI output is capped at 2,048 tokens and requested to be concise. Truncated or malformed feedback follows the same unavailable fallback. Character limits are not exact token counts.
- Counters and the concurrency lock live in memory. Run **one worker on one instance** using the deployment command above. Sleeping, restarting, or redeploying resets counters. Multiple workers or instances would each have separate allowances. Google's project quota is the authoritative limit; use an unbilled free-tier project for a strictly free demo.
- These shared limits do not guarantee fair access: one visitor can consume the allowance. CORS is not authentication. File/page/text limits reduce ordinary resource use but are not a hard CPU/memory sandbox for hostile PDFs; multipart parsing and PDF internals can still consume resources before content limits are checked.
- Handled provider failures log only their exception class, not provider messages, uploaded contents, job descriptions, or API keys.

## Tests and frontend checks

### Backend tests

From `backend`:

```powershell
uv run python -m pytest -v
```

The suite contains 44 tests covering PDF extraction, upload validation (including the 5 MiB boundary), skill matching, JD/page/text boundaries, rolling usage windows, concurrent admission, AI success, and unavailable fallback.

Tests use synthetic PDFs and mocked Gemini responses without live API calls. Automated AI checks cover success, timeouts, quota errors, empty/malformed feedback, input rejection, output-cap configuration, and safe error logging. Extracted-text boundaries use mocked extraction. Actual provider quotas, model output quality, hostile-PDF resource behavior, process restarts, and deployed proxy behavior are not verified by this suite. Dependency deprecation warnings may appear during testing.

### Frontend checks

From `frontend`:

```powershell
npm run lint
npm run build
```

These check lint rules and the production build. Browser flows have been checked manually during development; there are no automated frontend interaction tests yet. Lint and build checks do not verify end-to-end behavior.

### Verification record — September 17, 2026

- Backend: all 44 tests passed after adding the demo safeguards. The original 23-test suite also passed before those additions.
- Frontend: lint and production build passed.
- Browser checks with synthetic files passed: missing resume, whitespace-only JD, successful upload (50% coverage), invalid PDF, blank PDF, recovery after validation errors, no recognized JD skills, and zero coverage.
- Loading disabled the Analyze button; completed requests restored it. Stopping the backend produced the request-failure message, cleared previous results, and restored the button.
- At a 375-pixel viewport, the form and skill results fit without horizontal overflow.
- GitHub CI passed for deployment commit `0921e8e` ([run](https://github.com/Aadhithya-R-P/resume-picker/actions/runs/35210580590)).
- Public frontend returned the ResumePicker page, Render `/health` returned HTTP 200, and CORS allowed the exact production frontend origin. The deployed frontend bundle was verified to use the Render URL, and a browser reached **Server ready** without console errors.
- The owner confirmed the deployed app was working after the API configuration fix. Separate public AI success and quota-fallback results have not been recorded here; the automated provider tests use mocks.

Local browser validation and the mobile layout check preceded the new safeguards; the owner subsequently checked the updated limit messages. A full public cold-start, reconnect, and error-flow regression is not recorded. There are no automated frontend interaction tests.

## Limitations and next steps

- No OCR: image-only PDFs without a text layer cannot yield text.
- Extracted spacing and layout may differ from the original PDF.
- Skill matching uses a small, fixed vocabulary rather than semantic understanding.
- Pydantic checks AI response structure, not factual accuracy; feedback can be wrong.
- This portfolio demo has no authentication or database. Shared process-local limits have the reset and fairness limitations described above.
- Free hosting introduces cold starts and resource limits; this is not a production hiring or applicant-ranking system.
- Release follow-up: finish recording public upload/AI/error checks, merge after CI passes, switch both production branches to `main`, and verify the resulting deployments.
- Automated frontend interaction tests remain future work.
