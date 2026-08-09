"""
Krishi Setu — FastAPI application entry point.
Stateless routes, CORS configured, single DB session per request.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_tables
from app.routers import admin, assistant, crawler, eligibility, farmers, ministries, schemes, sources
from app.scheduler import start_scheduler, stop_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run startup tasks before serving requests."""
    if settings.APP_ENV == "development":
        create_tables()

    # Embed a Celery worker in this same web process, in a background
    # thread. This is a free-tier workaround so a paid, separate Render
    # Background Worker service is not required — the free web service
    # dyno hosts both the FastAPI app and the Celery worker together.
    # See TECHNICAL_DEBT.md for the tradeoffs of this approach.
    import threading
    from app.celery_app import celery_app

    def _run_embedded_worker() -> None:
        try:
            worker = celery_app.Worker(
                loglevel="info",
                pool="solo",  # safest pool for an embedded/threaded worker
                concurrency=1,
            )
            worker.start()
        except Exception as e:
            print(f"[startup] Embedded Celery worker failed to start: {e}")

    worker_thread = threading.Thread(target=_run_embedded_worker, daemon=True)
    worker_thread.start()
    print("[startup] Embedded Celery worker thread started")

    # APScheduler still runs as the scheduling trigger (in-process, works
    # regardless of Celery Beat availability)
    from app.scheduler import start_scheduler
    start_scheduler()

    yield

    from app.scheduler import stop_scheduler
    stop_scheduler()


app = FastAPI(
    title="Krishi Setu API",
    description="AI-driven Digital Public Infrastructure for Indian farmer scheme discovery",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(ministries.router, prefix="/api/v1/ministries", tags=["Ministries"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["Sources"])
app.include_router(schemes.router, prefix="/api/v1/schemes", tags=["Schemes"])
app.include_router(crawler.router, prefix="/api/v1/crawler", tags=["Crawler"])
app.include_router(farmers.router, prefix="/api/v1/farmers", tags=["Farmers"])
app.include_router(eligibility.router, prefix="/api/v1/eligibility", tags=["Eligibility"])
app.include_router(assistant.router, prefix="/api/v1/assistant", tags=["AI Assistant"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {"status": "ok", "service": "Krishi Setu API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "healthy"} 
