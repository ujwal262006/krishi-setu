"""
Single reused SQLAlchemy engine and session factory.
No duplicate connections per request.
"""

from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models.models import Base

settings = get_settings()

# ── Engine ─────────────────────────────────────────────────────────────────────
# pool_pre_ping: silently reconnect on stale connections
# pool_size / max_overflow: safe defaults for a single-instance deploy
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.APP_ENV == "development",
)

# ── Session factory ────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ── Dependency — one session per request, always closed after ─────────────────
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables. Only used for dev/testing — use Alembic in production."""
    Base.metadata.create_all(bind=engine) 
