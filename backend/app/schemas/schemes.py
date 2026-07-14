"""Pydantic schemas for Scheme request/response models."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SchemeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    name_hindi: Optional[str] = None
    description: Optional[str] = None
    description_hindi: Optional[str] = None
    eligibility_criteria: dict[str, Any] = Field(default_factory=dict)
    benefits: dict[str, Any] = Field(default_factory=dict)
    application_url: Optional[str] = None
    source_url: Optional[str] = None
    search_synonyms: list[str] = Field(default_factory=list)
    ministry_id: Optional[int] = None
    is_active: bool = True


class SchemeCreate(SchemeBase):
    slug: str = Field(..., min_length=1, max_length=255)


class SchemeUpdate(BaseModel):
    name: Optional[str] = None
    name_hindi: Optional[str] = None
    description: Optional[str] = None
    eligibility_criteria: Optional[dict[str, Any]] = None
    benefits: Optional[dict[str, Any]] = None
    search_synonyms: Optional[list[str]] = None
    is_active: Optional[bool] = None


class SchemeResponse(SchemeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    created_at: datetime
    updated_at: datetime


class SchemeSearchQuery(BaseModel):
    q: str = Field(..., min_length=1, max_length=500, description="Search query in any language")
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)


class SchemeSearchResponse(BaseModel):
    query: str
    results: list[SchemeResponse]
    total: int 
