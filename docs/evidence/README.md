# Submission evidence

All files in this directory are generated from actual local runs. Test doubles are labelled explicitly; nothing here is a fabricated screenshot, log, or deployment result.

| File | Status | What it proves |
|---|---|---|
| `swagger-ui.png` | Captured from the locally running FastAPI app | `/docs` renders the interactive Swagger UI |
| `api-request-response.txt` | Captured from a real HTTP request to `127.0.0.1:4000/link-analysis` | End-to-end request/response, real website extraction, local mock LLM provider |
| `health-check.txt` | Captured from a real HTTP request to `127.0.0.1:4000/health` | Health endpoint works |
| `test-output.txt` | Captured from `python -m pytest -q` | Six automated tests pass |
| `deployment-verification.txt` | NOT DONE — applicant is deploying manually | Will contain real public URL checks only after deployment |
