# Krishi Setu

AI-driven Digital Public Infrastructure platform that helps Indian farmers discover government agricultural schemes, search them in plain/colloquial language, and check their own eligibility instantly.

---

**Live API:** https://krishi-setu-api.onrender.com  
**API Docs:** https://krishi-setu-api.onrender.com/docs

## Tech Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy ORM, Alembic migrations
- **Database:** PostgreSQL (Supabase)
- **Crawler:** Requests + BeautifulSoup4 (HTML), PyMuPDF + Tesseract OCR (PDF), openpyxl (XLSX), python-docx (DOCX), ElementTree (XML), csv/json (CSV/JSON)
- **AI Assistant:** Google Gemini 2.5 Flash (RAG pipeline)
- **Task Queue:** Celery + Redis (Upstash)
- **Scheduler:** Celery Beat (APScheduler fallback in dev)
- **Auth:** JWT (python-jose) + bcrypt password hashing
- **Frontend:** React.js + Vite PWA (Week 3)
- **Hosting:** Backend on Render, Frontend on Vercel (Week 3)

---

## Setup Instructions

### 1. Clone and install

```bash
git clone https://github.com/ujwal262006/krishi-setu.git
cd krishi-setu/backend
pip install -r requirements.txt
```

### 2. Environment variables

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

### 3. Database setup

Create a PostgreSQL database (Supabase recommended). Run migrations:

```bash
python -m alembic upgrade head
```

Seed initial data (5 ministries, 5 sources, 21 real schemes):

```bash
python -m app.seed
```

### 4. Run the API server

```bash
python -m uvicorn app.main:app --reload
```

API docs available at: `http://localhost:8000/docs`

### 5. Run Celery worker (for async crawling)

```bash
python -m celery -A app.celery_app worker --loglevel=info --pool=solo
```

### 6. Run Celery Beat (for scheduled crawling)

```bash
python -m celery -A app.celery_app beat --loglevel=info
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (pooled, port 6543 for Supabase) |
| `GEMINI_API_KEY` | Google Gemini API key — never hardcode |
| `REDIS_URL` | Redis connection string (Upstash: `rediss://...?ssl_cert_reqs=CERT_NONE`) |
| `SECRET_KEY` | JWT signing secret — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `APP_ENV` | `development` or `production` |
| `ALLOWED_ORIGINS` | JSON array of allowed CORS origins e.g. `["http://localhost:5173"]` |
| `DEFAULT_CRAWL_INTERVAL_HOURS` | Default crawl interval (overridable per source in DB) |
| `MAX_CRAWL_DEPTH` | Default max crawl depth |
| `REQUEST_TIMEOUT_SECONDS` | HTTP request timeout for crawler |

---

## API Endpoints

### Health
- `GET /` — health check
- `GET /health` — health check

### Schemes
- `GET /api/v1/schemes/` — list schemes
- `GET /api/v1/schemes/search?q=` — synonym-expanded search (handles Hindi/colloquial)
- `GET /api/v1/schemes/{id}` — get scheme by ID

### Farmers
- `POST /api/v1/farmers/register` — register farmer
- `POST /api/v1/farmers/login` — login, returns JWT
- `GET /api/v1/farmers/me` — get profile (JWT required)
- `PATCH /api/v1/farmers/me` — update profile (JWT required)

### Eligibility
- `POST /api/v1/eligibility/check` — check eligibility for scheme IDs (JWT required)
- `GET /api/v1/eligibility/my-results` — get saved results (JWT required)

### AI Assistant
- `POST /api/v1/assistant/query` — ask the AI assistant (optional JWT)
- `GET /api/v1/assistant/query/stream?q=` — streamed response
- `GET /api/v1/assistant/search?q=` — public scheme search

### Crawler
- `POST /api/v1/crawler/trigger/{source_id}` — trigger manual crawl
- `GET /api/v1/crawler/jobs` — list all crawl jobs
- `GET /api/v1/crawler/jobs/{id}` — get job status

### Admin
- `GET /api/v1/admin/stats` — dashboard overview stats
- `GET /api/v1/admin/schemes` — list all schemes
- `POST /api/v1/admin/schemes` — create scheme
- `PATCH /api/v1/admin/schemes/{id}` — update scheme
- `DELETE /api/v1/admin/schemes/{id}` — delete scheme
- `GET /api/v1/admin/sources` — list sources
- `POST /api/v1/admin/sources` — add source
- `GET /api/v1/admin/crawl-jobs` — list crawl jobs
- `POST /api/v1/admin/crawl-jobs/trigger/{source_id}` — trigger crawl
- `GET /api/v1/admin/farmers` — list farmers
- `GET /api/v1/admin/search-logs` — view search logs

---

## Database Schema

See `schema.sql` for the complete schema. Tables:

| Table | Purpose |
|---|---|
| `ministries` | Government ministries owning schemes |
| `sources` | Crawl sources with per-source rate limits and intervals |
| `schemes` | Agricultural schemes with structured eligibility JSON |
| `crawl_jobs` | Async crawl job tracking with Celery task ID |
| `farmer_profiles` | Farmer registration and eligibility attributes |
| `search_logs` | All AI assistant queries with response time |
| `eligibility_records` | Per-farmer per-scheme eligibility results |
| `jobs` | General async job queue |

---

## Scalability Decisions

**PostgreSQL with proper indexing** — every search, eligibility, and scheduling column is indexed. `url_hash` and `content_hash` on schemes for O(1) duplicate detection.

**Celery + Redis (Upstash)** — crawl jobs dispatched via Celery tasks, not blocking HTTP requests. Worker runs independently. Beat scheduler replaces cron for scheduled crawling.

**Stateless FastAPI routes** — no server-side session state. JWT tokens are self-contained. Any number of FastAPI instances can run behind a load balancer.

**Configurable per-source crawl settings** — `crawl_interval_hours`, `rate_limit_rps`, `max_depth`, `respect_robots_txt` are stored per source in the DB, not hardcoded. Change without redeployment.

**Change-aware crawling** — `content_hash` SHA-256 on scheme pages. Pages that haven't changed are skipped on re-crawl, saving bandwidth and DB writes.

**APScheduler fallback** — if Redis is unavailable (dev environment), APScheduler runs in-process. Production always uses Celery Beat.

---

## Known Limitations

See `TECHNICAL_DEBT.md` for the complete list. Key items:

1. **Celery worker must run separately** — crawl jobs fail silently if no worker is running. Production Render deployment needs a separate worker dyno.
2. **HTML scheme extraction is heuristic** — crawled pages use keyword detection, not structured extraction. Seeded schemes have complete eligibility data; crawled ones may have empty criteria.
3. **Eligibility exclusion categories** — PM-KISAN and similar schemes have exclusions (income tax payers, govt employees) that cannot be evaluated since farmer profiles don't capture these fields. Overall result may show MET while manual verification is still needed.
4. **No admin authentication** — admin endpoints are currently unprotected. Production deployment needs API key or role-based auth before exposing publicly.
5. **Retrieval uses LIKE search** — not semantic/embedding-based. Works well with synonyms but won't handle spelling variations or deep semantic similarity.
6. **LLM output not post-validated** — anti-hallucination is prompt-level only. A future improvement would verify every scheme name in the Gemini response against the retrieved set.

---

## Deliverables

- [x] GitHub repository (private) — shared with yuvi673758@gmail.com
- [x] Working prototype deployed (backend) — https://krishi-setu-api.onrender.com
- [x] Database schema SQL file — `schema.sql`
- [x] Alembic migrations — `backend/migrations/`
- [x] README — this file
- [ ] Loom walkthrough — Week 3 
