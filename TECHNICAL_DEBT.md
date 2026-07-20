# Technical Debt — Krishi Setu

Items identified during prototype development that require resolution before production hardening.

## 1. Crawler uses in-process background execution instead of Celery

Current: crawl jobs are scheduled using FastAPI BackgroundTasks. Each crawl creates an independent SQLAlchemy session and executes within the FastAPI application process.

Future: replace FastAPI BackgroundTasks execution with dedicated Celery workers using Redis as the message broker.

Risk: running crawl jobs can be interrupted if the FastAPI application process restarts, crashes, or is redeployed.

Target: Week 3 scalability hardening.

## 2. Improve HTML scheme candidate detection

Current: HTML scheme detection uses heuristic keyword matching and page structure analysis.

Future: improve deterministic candidate classification and structured field extraction, with optional Gemini-assisted enrichment for ambiguous content.

Risk: generic government portal pages may be incorrectly classified as agricultural schemes.

Target: Week 2 crawler and AI hardening.

## 3. Celery worker infrastructure is not yet configured

Current: Celery and Redis dependencies are installed and database job tracking is available, but no dedicated worker process is running.

Future: configure Celery application, Redis broker, worker process, and crawl task dispatch.

Target: Week 3 scalability hardening.

## 4. Scheduled crawling is not yet implemented

Current: crawl jobs are triggered manually through the crawler API.

Future: implement scheduled crawling based on next_crawl_at, crawl_interval_hours, and per-source configuration stored in the database.

Target: Week 1 crawler hardening.

## 5. API authentication and authorization are not yet implemented

Current: development API endpoints are accessible without authentication.

Future: implement JWT-based farmer authentication and protect administrative crawler and data-management endpoints.

Target: Week 2.

## 6. Scheme synonym search is not optimized for scale

Current: search_synonyms JSON content is cast to text and matched using case-insensitive pattern search.

Future: implement PostgreSQL full-text and trigram-based search with appropriate GIN/GiST indexing.

Risk: current search approach may become inefficient as the scheme dataset grows.

Target: Week 2 search hardening.

## 7. Crawled scheme records lack structured eligibility data

Current: automatically discovered scheme records may contain unstructured descriptions with empty or incomplete eligibility_criteria and benefits fields.

Future: implement structured extraction and validation of eligibility criteria and benefit information before records are used by the eligibility engine.

Target: Week 2.

## 8. Crawl job retry and failure recovery require hardening

Current: failed crawl jobs retain failure status and error information.

Future: implement controlled retry logic with exponential backoff, maximum retry limits, and dead-letter handling for permanently failed jobs.

Target: Week 3 scalability hardening.

## 9. Multi-format extractor validation coverage is incomplete

Current: HTML crawling has been validated against a live government source. PDF, OCR, CSV, JSON, XLSX, DOCX, and XML extractors are implemented but require dedicated format-specific integration testing.

Future: create representative extractor fixtures and automated tests for each supported ingestion format.

Target: Week 1/2 crawler hardening.

## 10. Duplicate crawl trigger endpoint removed

Previously: POST /api/v1/sources/{source_id}/crawl created a QUEUED job but did not execute the crawler.
Now: single execution path via POST /api/v1/crawler/trigger/{source_id}.
The sources router now only handles CRUD and job listing.

## 11. Duplicate job prevention race condition

Current: duplicate prevention checks QUEUED + RUNNING states, which reduces but does not fully eliminate race conditions under concurrent requests.

Future: enforce job concurrency at the database level using a unique partial index or distributed lock (e.g. Redis SETNX).

Target: Week 3 scalability hardening.

## 12. Eligibility evaluation cannot fully resolve scheme exclusion categories

Current: the deterministic eligibility engine evaluates criteria available in the farmer profile, including land holding, caste, income, age, state, BPL status, gender, and occupation-related rules.

Some schemes, including PM-KISAN, define exclusion categories such as income-tax payer status, government employment, constitutional posts, institutional land ownership, and professional categories. These fields are not currently represented in the farmer profile schema. The exclusion check therefore returns N/A, while the overall result may still appear MET based on evaluated fields alone.

Risk: schemes with unresolved exclusion criteria may receive an overall MET result while additional manual verification is still required from the farmer.

Future: extend farmer profile attributes for common exclusion criteria and make overall eligibility aggregation conservative when required criterion data is unavailable.

Target: Week 2 eligibility hardening.

## 13. Eligibility records represent latest state, not full history

Current: eligibility_records table uses a UNIQUE (farmer_id, scheme_id) constraint with upsert logic. Each check overwrites the previous result for the same farmer-scheme pair.

The GET /eligibility/my-results endpoint is therefore "latest saved results" not a complete audit history.

Future: if full audit history is required, add an append-only eligibility_audit_log table alongside the current upsert table.

Target: Week 2 if required by product scope.

## 14. Retrieval uses LIKE-based search, not semantic search

Current: scheme retrieval uses ILIKE pattern matching with JSON synonym search and word-level fallback.

Future: PostgreSQL Full Text Search (pg_trgm / GIN index) or embedding-based semantic retrieval for better recall and ranking.

Target: Week 2.

## 15. LLM output is not post-validated against retrieved schemes

Current: system prompt instructs Gemini to only reference retrieved schemes. Anti-hallucination is enforced at the prompt level only.

Risk: model could still accidentally mention scheme names outside the retrieved context.

Future: extract referenced scheme names from the Gemini response and verify every name exists in the retrieved context before returning the answer to the user.

Target: Week 2.

## 16. Admin endpoints require authentication

Current: all /api/v1/admin/* endpoints are publicly accessible without any authentication.

Future: protect admin endpoints with either a static API key (X-Admin-Key header) or a separate admin JWT role claim. Must be implemented before any public deployment.

Target: before production deployment.

## 17. README should stay implementation-synchronized

Current: documentation may temporarily describe planned production deployment components before they are fully configured.

Future: update README immediately whenever deployment architecture changes — specifically the deployment section and deliverables checklist.

Target: before final submission.

## 18. Gemini model name pinned to unstable version alias

Issue found during production handover testing: `gemini-2.5-flash` became unavailable
for the API key in production even though it worked in local development, causing
the AI assistant to fail with a 404 error.

Fix applied: switched to `gemini-flash-latest`, Google's stable rolling alias, which
automatically points to the latest available Flash model and is less likely to be
deprecated without notice.

Future: monitor Google's model deprecation announcements and re-verify the model
alias periodically, since "latest" aliases can still shift underlying model behavior
over time without code changes.