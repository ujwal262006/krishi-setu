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
from app.routers import crawler, ministries, schemes, sources

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run startup tasks before serving requests."""
    # Only create tables in dev — production uses Alembic migrations
    if settings.APP_ENV == "development":
        create_tables()
    yield


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


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {"status": "ok", "service": "Krishi Setu API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "healthy"} 
