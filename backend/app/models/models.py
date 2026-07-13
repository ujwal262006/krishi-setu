"""
Krishi Setu — SQLAlchemy ORM Models
All 8 required tables with proper indexing and relationships.
"""

from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum, Float,
    ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ─── Enums ────────────────────────────────────────────────────────────────────

class CrawlJobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CrawlJobType(str, enum.Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    MANUAL = "manual"


class SourceFormat(str, enum.Enum):
    HTML = "html"
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    DOCX = "docx"
    XML = "xml"


class EligibilityResult(str, enum.Enum):
    MET = "met"
    NOT_MET = "not_met"
    NA = "na"


# ─── 1. Ministries ────────────────────────────────────────────────────────────

class Ministry(Base):
    __tablename__ = "ministries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    name_hindi = Column(String(255), nullable=True)
    acronym = Column(String(50), nullable=True)
    website_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    schemes = relationship("Scheme", back_populates="ministry")
    sources = relationship("Source", back_populates="ministry")

    def __repr__(self) -> str:
        return f"<Ministry id={self.id} name={self.name!r}>"


# ─── 2. Sources ───────────────────────────────────────────────────────────────

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ministry_id = Column(
        Integer, ForeignKey("ministries.id", ondelete="SET NULL"), nullable=True
    )
    name = Column(String(255), nullable=False)
    base_url = Column(String(500), nullable=False, unique=True)
    format = Column(Enum(SourceFormat), nullable=False, default=SourceFormat.HTML)

    # Crawl configuration (per-source, configurable at DB level)
    crawl_interval_hours = Column(Integer, nullable=False, default=24)
    max_depth = Column(Integer, nullable=False, default=3)
    rate_limit_rps = Column(Float, nullable=False, default=1.0)  # requests per second
    is_active = Column(Boolean, nullable=False, default=True)
    respect_robots_txt = Column(Boolean, nullable=False, default=True)

    last_crawled_at = Column(DateTime(timezone=True), nullable=True)
    next_crawl_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    ministry = relationship("Ministry", back_populates="sources")
    crawl_jobs = relationship("CrawlJob", back_populates="source")

    # Indexes
    __table_args__ = (
        Index("ix_sources_next_crawl_at", "next_crawl_at"),
        Index("ix_sources_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Source id={self.id} base_url={self.base_url!r}>"


# ─── 3. Schemes ───────────────────────────────────────────────────────────────

class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ministry_id = Column(
        Integer, ForeignKey("ministries.id", ondelete="SET NULL"), nullable=True
    )

    # Core fields
    name = Column(String(500), nullable=False)
    name_hindi = Column(String(500), nullable=True)
    slug = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    description_hindi = Column(Text, nullable=True)

    # Structured eligibility criteria stored as JSON
    # e.g. {"land_holding_acres": {"max": 2}, "caste": ["SC", "ST", "OBC"],
    #        "annual_income": {"max": 150000}, "state": ["all"]}
    eligibility_criteria = Column(JSON, nullable=True, default=dict)

    # Benefits and application
    benefits = Column(JSON, nullable=True, default=dict)
    application_url = Column(String(500), nullable=True)
    source_url = Column(String(500), nullable=True)

    # Synonym expansion for search
    # e.g. ["tractor subsidy", "कृषि यंत्र", "farm equipment loan"]
    search_synonyms = Column(JSON, nullable=True, default=list)

    # Crawl metadata
    url_hash = Column(String(64), nullable=True)          # SHA-256 of source_url
    content_hash = Column(String(64), nullable=True)       # SHA-256 of content
    is_active = Column(Boolean, nullable=False, default=True)
    last_updated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    ministry = relationship("Ministry", back_populates="schemes")
    eligibility_records = relationship("EligibilityRecord", back_populates="scheme")

    # Indexes — critical for search and eligibility queries
    __table_args__ = (
        Index("ix_schemes_slug", "slug"),
        Index("ix_schemes_is_active", "is_active"),
        Index("ix_schemes_ministry_id", "ministry_id"),
        Index("ix_schemes_url_hash", "url_hash"),
        Index("ix_schemes_content_hash", "content_hash"),
    )

    def __repr__(self) -> str:
        return f"<Scheme id={self.id} name={self.name!r}>"


# ─── 4. Crawl Jobs ────────────────────────────────────────────────────────────

class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_id = Column(
        Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )

    status = Column(
        Enum(CrawlJobStatus),
        nullable=False,
        default=CrawlJobStatus.QUEUED,
    )
    job_type = Column(
        Enum(CrawlJobType),
        nullable=False,
        default=CrawlJobType.FULL,
    )

    # Progress tracking
    urls_discovered = Column(Integer, nullable=False, default=0)
    urls_crawled = Column(Integer, nullable=False, default=0)
    schemes_upserted = Column(Integer, nullable=False, default=0)
    errors_count = Column(Integer, nullable=False, default=0)

    # Retry logic
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    last_error = Column(Text, nullable=True)

    # Celery task reference
    celery_task_id = Column(String(255), nullable=True)

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    source = relationship("Source", back_populates="crawl_jobs")

    # Indexes
    __table_args__ = (
        Index("ix_crawl_jobs_source_id", "source_id"),
        Index("ix_crawl_jobs_status", "status"),
        Index("ix_crawl_jobs_scheduled_at", "scheduled_at"),
        Index("ix_crawl_jobs_celery_task_id", "celery_task_id"),
    )

    def __repr__(self) -> str:
        return f"<CrawlJob id={self.id} source_id={self.source_id} status={self.status}>"


# ─── 5. Farmer Profiles ───────────────────────────────────────────────────────

class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Identity
    name = Column(String(255), nullable=False)
    phone = Column(String(15), nullable=True, unique=True)
    aadhaar_hash = Column(String(64), nullable=True, unique=True)  # hashed, never plain

    # Eligibility-relevant fields (compared against scheme criteria)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    land_holding_acres = Column(Float, nullable=True)
    caste = Column(String(50), nullable=True)         # General/OBC/SC/ST
    annual_income = Column(Integer, nullable=True)    # in INR
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    is_bpl = Column(Boolean, nullable=True)           # Below Poverty Line
    has_kisan_credit_card = Column(Boolean, nullable=True)
    primary_crop = Column(String(100), nullable=True)
    irrigation_type = Column(String(50), nullable=True)  # rainfed/irrigated/drip

    # Auth
    password_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    eligibility_records = relationship("EligibilityRecord", back_populates="farmer")
    search_logs = relationship("SearchLog", back_populates="farmer")

    # Indexes
    __table_args__ = (
        Index("ix_farmer_profiles_phone", "phone"),
        Index("ix_farmer_profiles_state", "state"),
        Index("ix_farmer_profiles_caste", "caste"),
    )

    def __repr__(self) -> str:
        return f"<FarmerProfile id={self.id} name={self.name!r}>"


# ─── 6. Search Logs ───────────────────────────────────────────────────────────

class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    farmer_id = Column(
        Integer, ForeignKey("farmer_profiles.id", ondelete="SET NULL"), nullable=True
    )

    query_raw = Column(Text, nullable=False)           # original query
    query_normalized = Column(Text, nullable=True)     # after synonym expansion
    results_count = Column(Integer, nullable=False, default=0)
    top_scheme_ids = Column(JSON, nullable=True)       # [id1, id2, id3...]
    session_id = Column(String(255), nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    farmer = relationship("FarmerProfile", back_populates="search_logs")

    # Indexes
    __table_args__ = (
        Index("ix_search_logs_farmer_id", "farmer_id"),
        Index("ix_search_logs_created_at", "created_at"),
        Index("ix_search_logs_session_id", "session_id"),
    )

    def __repr__(self) -> str:
        preview = repr(self.query_raw[:50])
        return f"<SearchLog id={self.id} query={preview}>"


# ─── 7. Eligibility Records ───────────────────────────────────────────────────

class EligibilityRecord(Base):
    __tablename__ = "eligibility_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    farmer_id = Column(
        Integer, ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False
    )
    scheme_id = Column(
        Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False
    )

    # Overall result
    overall_result = Column(Enum(EligibilityResult), nullable=False)

    # Per-criterion breakdown
    # e.g. {"land_holding": {"result": "met", "explanation": "Holds 1.5 acres ≤ 2 acres limit"},
    #        "caste": {"result": "not_met", "explanation": "OBC not eligible for this scheme"}}
    criteria_results = Column(JSON, nullable=False, default=dict)

    # Plain-language summary
    summary = Column(Text, nullable=True)

    checked_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    farmer = relationship("FarmerProfile", back_populates="eligibility_records")
    scheme = relationship("Scheme", back_populates="eligibility_records")

    # Indexes + unique constraint (one record per farmer-scheme pair)
    __table_args__ = (
        UniqueConstraint("farmer_id", "scheme_id", name="uq_eligibility_farmer_scheme"),
        Index("ix_eligibility_records_farmer_id", "farmer_id"),
        Index("ix_eligibility_records_scheme_id", "scheme_id"),
        Index("ix_eligibility_records_overall_result", "overall_result"),
    )

    def __repr__(self) -> str:
        return (
            f"<EligibilityRecord farmer={self.farmer_id} "
            f"scheme={self.scheme_id} result={self.overall_result}>"
        )


# ─── 8. Jobs (Async Job Queue) ────────────────────────────────────────────────

class Job(Base):
    __tablename__ = "jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    job_type = Column(String(100), nullable=False)   # crawl, notify, export, etc.
    status = Column(String(50), nullable=False, default="queued")
    payload = Column(JSON, nullable=False, default=dict)

    # Retry logic
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    last_error = Column(Text, nullable=True)

    # Celery reference
    celery_task_id = Column(String(255), nullable=True)

    # Scheduling
    run_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("ix_jobs_status_run_at", "status", "run_at"),
        Index("ix_jobs_job_type", "job_type"),
        Index("ix_jobs_celery_task_id", "celery_task_id"),
    )

    def __repr__(self) -> str:
        return f"<Job id={self.id} type={self.job_type} status={self.status}>"
