# Session Handoff — 2026-05-12

## What was done

1. **README updated** — M001 status changed from "Planning complete" to "✅ Complete (286 tests)" with current test count.

2. **Frontend serving fixed** — Added FastAPI `StaticFiles` mount at `/` so `index.html` loads at `http://localhost:8000/` (was returning 404). Files are copied from project root to `api/../static/`.

3. **GraphQL query fix (partial)** — Fixed `get_user()` query:
   - `publicRepos` → `repositories(privacy: PUBLIC) { totalCount }`
   - `followers` → `followers { totalCount }` (connection syntax)
   - `following` → `following { totalCount }` (connection syntax)
   - Updated test fixtures to match new shapes
   - Fixed orphaned syntax error on line 1095 of `crawler/github_api.py`

4. **Smoke test results**:
   - `/health` ✅
   - `/profiles` ✅ (3 profiles returned)
   - Frontend at `/` ✅ (33KB HTML served)
   - `/score` ❌ — further GraphQL schema drift found: `reviewComments` on PullRequest

## What remains

- **Full GraphQL audit** — Multiple queries in `crawler/github_api.py` have stale field names against the current GitHub schema. The `/score` endpoint won't work with a real token until these are all updated.
- **Set a real GITHUB_TOKEN** and do a full end-to-end test with live data.

## Key files changed

| File | Change |
|------|--------|
| `README.md` | M001 status, test count |
| `api/main.py` | Added static frontend mount |
| `crawler/github_api.py` | GraphQL query fix, syntax error fix |
| `tests/test_crawler.py` | Mock fixture updates |
