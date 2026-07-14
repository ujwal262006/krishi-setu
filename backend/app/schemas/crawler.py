"""Pydantic schemas for Source, Ministry, and CrawlJob models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Ministry ──────────────────────────────────────────────────────────────────

class MinistryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    name_hindi: Optional[str] = None
    acronym: Optional[str] = Field(None, max_length=50)
    website_url: Optional[str] = None


class MinistryCreate(MinistryBase):
    pass


class MinistryUpdate(BaseModel):
    name: Optional[str] = None
    name_hindi: Optional[str] = None
    acronym: Optional[str] = None
    website_url: Optional[str] = None


class MinistryResponse(MinistryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ── Source ────────────────────────────────────────────────────────────────────

class SourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    base_url: str = Field(..., max_length=500)
    format: str = Field(default="html")
    crawl_interval_hours: int = Field(default=24, ge=1, le=8760)
    max_depth: int = Field(default=3, ge=1, le=10)
    rate_limit_rps: float = Field(default=1.0, ge=0.1, le=10.0)
    is_active: bool = True
    respect_robots_txt: bool = True
    ministry_id: Optional[int] = None


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    crawl_interval_hours: Optional[int] = None
    max_depth: Optional[int] = None
    rate_limit_rps: Optional[float] = None
    is_active: Optional[bool] = None


class SourceResponse(SourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_crawled_at: Optional[datetime]
    next_crawl_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ── CrawlJob ──────────────────────────────────────────────────────────────────

class CrawlJobTrigger(BaseModel):
    source_id: int
    job_type: str = Field(default="manual")


class CrawlJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    status: str
    job_type: str
    urls_discovered: int
    urls_crawled: int
    schemes_upserted: int
    errors_count: int
    attempts: int
    celery_task_id: Optional[str]
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime 
