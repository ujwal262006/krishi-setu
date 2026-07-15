"""Pydantic schemas for authentication."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    farmer_id: int
    name: str


class TokenData(BaseModel):
    farmer_id: int | None = None
