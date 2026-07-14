"""
Source CRUD endpoints + crawl job trigger.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import CrawlJob, CrawlJobStatus, CrawlJobType, Source
from app.schemas.crawler import (
    CrawlJobResponse,
    CrawlJobTrigger,
    SourceCreate,
    SourceResponse,
    SourceUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[SourceResponse])
def list_sources(
    skip: int = 0,
    limit: int = 50,
    active_only: bool = False,
    db: Session = Depends(get_db),
) -> List[Source]:
    query = db.query(Source)
    if active_only:
        query = query.filter(Source.is_active == True)
    return query.offset(skip).limit(limit).all()


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
) -> Source:
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )
    return source


@router.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(
    payload: SourceCreate,
    db: Session = Depends(get_db),
) -> Source:
    existing = db.query(Source).filter(Source.base_url == payload.base_url).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Source with URL '{payload.base_url}' already exists",
        )
    source = Source(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.patch("/{source_id}", response_model=SourceResponse)
def update_source(
    source_id: int,
    payload: SourceUpdate,
    db: Session = Depends(get_db),
) -> Source:
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
) -> None:
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )
    db.delete(source)
    db.commit()


@router.post("/{source_id}/crawl", response_model=CrawlJobResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_crawl(
    source_id: int,
    db: Session = Depends(get_db),
) -> CrawlJob:
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )
    if not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source is inactive — activate it before triggering a crawl",
        )

    # Check for already-running job on this source
    running = (
        db.query(CrawlJob)
        .filter(
            CrawlJob.source_id == source_id,
            CrawlJob.status == CrawlJobStatus.RUNNING,
        )
        .first()
    )
    if running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Crawl job {running.id} is already running for this source",
        )

    job = CrawlJob(
        source_id=source_id,
        status=CrawlJobStatus.QUEUED,
        job_type=CrawlJobType.MANUAL,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{source_id}/jobs", response_model=List[CrawlJobResponse])
def list_crawl_jobs(
    source_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> List[CrawlJob]:
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )
    return (
        db.query(CrawlJob)
        .filter(CrawlJob.source_id == source_id)
        .order_by(CrawlJob.created_at.desc())
        .limit(limit)
        .all()
    ) 
