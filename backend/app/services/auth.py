"""
Krishi Setu — Authentication Service
Password hashing with bcrypt, JWT token creation and verification.
No hardcoded secrets — all from environment variables.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.models import FarmerProfile

settings = get_settings()

# ── Password hashing ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── JWT config ────────────────────────────────────────────────────────────────
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_farmer_by_phone(db: Session, phone: str) -> Optional[FarmerProfile]:
    return db.query(FarmerProfile).filter(FarmerProfile.phone == phone).first()


def get_farmer_by_id(db: Session, farmer_id: int) -> Optional[FarmerProfile]:
    return db.query(FarmerProfile).filter(FarmerProfile.id == farmer_id).first()


def authenticate_farmer(
    db: Session,
    phone: str,
    password: str,
) -> Optional[FarmerProfile]:
    farmer = get_farmer_by_phone(db, phone)
    if not farmer:
        return None
    if not farmer.password_hash:
        return None
    if not verify_password(password, farmer.password_hash):
        return None
    return farmer
