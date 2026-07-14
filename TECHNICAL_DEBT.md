# Technical Debt — Krishi Setu

## 1. Crawler runs in background thread, not Celery
Current: background thread via FastAPI BackgroundTasks (dev-only pattern).
Future: replace with Celery + Redis worker for production.
Risk: if the FastAPI process restarts, running crawl jobs are lost.
Target: Week 3 scalability hardening.

## 2. HTML scheme extraction is heuristic-only
Current: keyword counting to detect scheme pages, first H1 as title.
Future: LLM-assisted structured extraction (Gemini) to parse eligibility
criteria and benefits into structured JSON automatically.
Risk: low-quality scheme data from crawled pages vs. seeded data.

## 3. No Celery worker yet
Current: jobs table exists, Celery dependency installed, but no worker process.
Future: celery worker -A app.celery_app --loglevel=info
Target: Week 3.

## 4. No scheduled crawling yet
Current: crawl is manual-trigger only via POST /api/v1/crawler/trigger/{source_id}.
Future: APScheduler or Celery Beat reading next_crawl_at from sources table.
Target: Day 4/5.

## 5. No authentication on API endpoints
Current: all endpoints are open — no API key or JWT auth.
Future: JWT auth for farmer-facing endpoints, API key for admin endpoints.
Target: Week 2 (farmer profile + auth).

## 6. search_synonyms JSON cast search is not full-text
Current: cast(search_synonyms, Text) LIKE '%query%' — works but slow at scale.
Future: PostgreSQL full-text search with pg_trgm extension and GIN index.
Target: Week 2.

## 7. Crawled scheme data lacks structured eligibility criteria
Current: crawled schemes have empty eligibility_criteria and benefits JSON.
Future: Gemini-assisted post-processing to extract structured fields from
raw description text.
Target: Week 2 AI assistant phase.

## 8. No error recovery for failed crawl jobs
Current: failed jobs stay in FAILED status with last_error set.
Future: retry logic with exponential backoff, dead-letter queue.
Target: Week 3.
