# Verification

Run the test suite with `python -m pytest -q` from the project root. All 16 tests pass.

Live checks were run against the local server with a real Gemini key. Each URL returned HTTP 200 with five search queries, five services and content taken from the submitted page:

- `https://www.instagram.com/crestspot` (the reviewer's link) — brand `CREST #1`, 3 competitors
- `https://www.facebook.com/crestspot`
- `https://x.com/crestspot`
- `https://www.youtube.com/@crestspot`
- `https://www.linkedin.com/company/dxora-technologies`
- `https://example.com`

The full Instagram request and response are in `docs/evidence/social-live-analysis.txt`, including a final 6.2 s smoke run after cleanup. Invalid URLs return 400, private network addresses return 403, and pages with no readable text return 422.
