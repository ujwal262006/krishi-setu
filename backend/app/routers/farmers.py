"""
Farmer profile registration, login, and profile management.
JWT-protected endpoints for authenticated farmers.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import FarmerProfile
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.farmer import (
    FarmerProfileCreate,
    FarmerProfileResponse,
    FarmerProfileUpdate,
)
from app.services.auth import (
    authenticate_farmer,
    create_access_token,
    decode_access_token,
    get_farmer_by_id,
    get_farmer_by_phone,
    hash_password,
)

router = APIRouter()
security = HTTPBearer()


# ── Auth dependency ────────────────────────────────────────────────────────────

def get_current_farmer(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db),
) -> FarmerProfile:
    """Extract and validate JWT, return the current farmer."""
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    farmer_id: int | None = payload.get("farmer_id")
    if farmer_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    farmer = get_farmer_by_id(db, farmer_id)
    if not farmer or not farmer.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Farmer account not found or inactive",
        )

    return farmer

def get_current_farmer_optional(
    db: Session = Depends(get_db),
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(HTTPBearer(auto_error=False))] = None,
) -> Optional[FarmerProfile]:
    """Same as get_current_farmer but returns None instead of 401 for unauthenticated requests."""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        return None
    farmer_id: int | None = payload.get("farmer_id")
    if farmer_id is None:
        return None
    farmer = get_farmer_by_id(db, farmer_id)
    if not farmer or not farmer.is_active:
        return None
    return farmer


# ── Registration ───────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=FarmerProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_farmer(
    payload: FarmerProfileCreate,
    db: Session = Depends(get_db),
) -> FarmerProfile:
    """Register a new farmer profile."""
    if payload.phone:
        existing = get_farmer_by_phone(db, payload.phone)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A farmer with this phone number already exists",
            )

    farmer = FarmerProfile(
        name=payload.name,
        phone=payload.phone,
        state=payload.state,
        district=payload.district,
        land_holding_acres=payload.land_holding_acres,
        caste=payload.caste,
        annual_income=payload.annual_income,
        age=payload.age,
        gender=payload.gender,
        is_bpl=payload.is_bpl,
        has_kisan_credit_card=payload.has_kisan_credit_card,
        primary_crop=payload.primary_crop,
        irrigation_type=payload.irrigation_type,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return farmer


# ── Login ──────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login_farmer(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate farmer and return JWT token."""
    farmer = authenticate_farmer(db, payload.phone, payload.password)
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"farmer_id": farmer.id})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        farmer_id=farmer.id,
        name=farmer.name,
    )


# ── Profile ────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=FarmerProfileResponse)
def get_my_profile(
    current_farmer: Annotated[FarmerProfile, Depends(get_current_farmer)],
) -> FarmerProfile:
    """Get authenticated farmer's own profile."""
    return current_farmer


@router.patch("/me", response_model=FarmerProfileResponse)
def update_my_profile(
    payload: FarmerProfileUpdate,
    current_farmer: Annotated[FarmerProfile, Depends(get_current_farmer)],
    db: Session = Depends(get_db),
) -> FarmerProfile:
    """Update authenticated farmer's own profile."""
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_farmer, field, value)
    db.commit()
    db.refresh(current_farmer)
    return current_farmer


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_my_account(
    current_farmer: Annotated[FarmerProfile, Depends(get_current_farmer)],
    db: Session = Depends(get_db),
) -> None:
    """Soft-delete — deactivate farmer account."""
    current_farmer.is_active = False
    db.commit() 
