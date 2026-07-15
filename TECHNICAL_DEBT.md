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