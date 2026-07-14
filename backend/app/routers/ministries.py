"""
Ministry CRUD endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Ministry
from app.schemas.crawler import MinistryCreate, MinistryResponse, MinistryUpdate

router = APIRouter()


@router.get("/", response_model=List[MinistryResponse])
def list_ministries(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[Ministry]:
    return db.query(Ministry).offset(skip).limit(limit).all()


@router.get("/{ministry_id}", response_model=MinistryResponse)
def get_ministry(
    ministry_id: int,
    db: Session = Depends(get_db),
) -> Ministry:
    ministry = db.query(Ministry).filter(Ministry.id == ministry_id).first()
    if not ministry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ministry {ministry_id} not found",
        )
    return ministry


@router.post("/", response_model=MinistryResponse, status_code=status.HTTP_201_CREATED)
def create_ministry(
    payload: MinistryCreate,
    db: Session = Depends(get_db),
) -> Ministry:
    existing = db.query(Ministry).filter(Ministry.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ministry with name '{payload.name}' already exists",
        )
    ministry = Ministry(**payload.model_dump())
    db.add(ministry)
    db.commit()
    db.refresh(ministry)
    return ministry


@router.patch("/{ministry_id}", response_model=MinistryResponse)
def update_ministry(
    ministry_id: int,
    payload: MinistryUpdate,
    db: Session = Depends(get_db),
) -> Ministry:
    ministry = db.query(Ministry).filter(Ministry.id == ministry_id).first()
    if not ministry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ministry {ministry_id} not found",
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ministry, field, value)
    db.commit()
    db.refresh(ministry)
    return ministry


@router.delete("/{ministry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ministry(
    ministry_id: int,
    db: Session = Depends(get_db),
) -> None:
    ministry = db.query(Ministry).filter(Ministry.id == ministry_id).first()
    if not ministry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ministry {ministry_id} not found",
        )
    db.delete(ministry)
    db.commit() 
