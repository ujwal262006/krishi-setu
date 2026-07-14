"""Pydantic schemas for FarmerProfile request/response models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FarmerProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=15)
    state: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    land_holding_acres: Optional[float] = Field(None, ge=0)
    caste: Optional[str] = Field(None, max_length=50)
    annual_income: Optional[int] = Field(None, ge=0)
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = Field(None, max_length=20)
    is_bpl: Optional[bool] = None
    has_kisan_credit_card: Optional[bool] = None
    primary_crop: Optional[str] = Field(None, max_length=100)
    irrigation_type: Optional[str] = Field(None, max_length=50)


class FarmerProfileCreate(FarmerProfileBase):
    password: str = Field(..., min_length=6)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.replace("+", "").replace("-", "").isdigit():
            raise ValueError("Invalid phone number format")
        return v


class FarmerProfileUpdate(BaseModel):
    name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    land_holding_acres: Optional[float] = None
    caste: Optional[str] = None
    annual_income: Optional[int] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    is_bpl: Optional[bool] = None
    has_kisan_credit_card: Optional[bool] = None
    primary_crop: Optional[str] = None
    irrigation_type: Optional[str] = None


class FarmerProfileResponse(FarmerProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class EligibilityCheckRequest(BaseModel):
    farmer_id: int
    scheme_ids: list[int] = Field(..., min_length=1, max_length=20)


class CriterionResult(BaseModel):
    result: str  # met / not_met / na
    explanation: str


class EligibilityCheckResponse(BaseModel):
    farmer_id: int
    scheme_id: int
    overall_result: str
    criteria_results: dict[str, CriterionResult]
    summary: str 
