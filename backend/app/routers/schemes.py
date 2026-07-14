"""
Scheme CRUD + search endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Scheme
from app.schemas.schemes import (
    SchemeCreate,
    SchemeResponse,
    SchemeSearchResponse,
    SchemeUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[SchemeResponse])
def list_schemes(
    skip: int = 0,
    limit: int = 50,
    ministry_id: int | None = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
) -> List[Scheme]:
    query = db.query(Scheme)
    if active_only:
        query = query.filter(Scheme.is_active == True)
    if ministry_id:
        query = query.filter(Scheme.ministry_id == ministry_id)
    return query.offset(skip).limit(limit).all()


@router.get("/search", response_model=SchemeSearchResponse)
def search_schemes(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> SchemeSearchResponse:
    """
    Search schemes by name, description, or synonyms.
    Handles colloquial Hindi queries via synonym matching.
    Full-text search will be added in Week 2 with pg_trgm.
    """
    search_term = f"%{q.lower()}%"

    from sqlalchemy import cast, Text

    query = db.query(Scheme).filter(
        Scheme.is_active == True,
        or_(
            func.lower(Scheme.name).like(search_term),
            func.lower(Scheme.description).like(search_term),
            func.lower(Scheme.name_hindi).like(search_term),
            func.lower(cast(Scheme.search_synonyms, Text)).like(search_term),
        ),
    )

    total = query.count()
    results = query.offset(offset).limit(limit).all()

    return SchemeSearchResponse(
        query=q,
        results=results,
        total=total,
    )


@router.get("/{scheme_id}", response_model=SchemeResponse)
def get_scheme(
    scheme_id: int,
    db: Session = Depends(get_db),
) -> Scheme:
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme {scheme_id} not found",
        )
    return scheme


@router.post("/", response_model=SchemeResponse, status_code=status.HTTP_201_CREATED)
def create_scheme(
    payload: SchemeCreate,
    db: Session = Depends(get_db),
) -> Scheme:
    existing = db.query(Scheme).filter(Scheme.slug == payload.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scheme with slug '{payload.slug}' already exists",
        )
    scheme = Scheme(**payload.model_dump())
    db.add(scheme)
    db.commit()
    db.refresh(scheme)
    return scheme


@router.patch("/{scheme_id}", response_model=SchemeResponse)
def update_scheme(
    scheme_id: int,
    payload: SchemeUpdate,
    db: Session = Depends(get_db),
) -> Scheme:
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme {scheme_id} not found",
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(scheme, field, value)
    db.commit()
    db.refresh(scheme)
    return scheme


@router.delete("/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheme(
    scheme_id: int,
    db: Session = Depends(get_db),
) -> None:
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme {scheme_id} not found",
        )
    db.delete(scheme)
    db.commit() 
