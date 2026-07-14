"""
Crawler API endpoints.
Crawl jobs are queued — not blocking.
Actual crawling runs in background (Celery in production, thread in dev).
"""

import threading
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import CrawlJob, CrawlJobStatus, CrawlJobType, Source
from app.schemas.crawler import CrawlJobResponse
from app.services.crawler import crawl_source

router = APIRouter()


def _run_crawl_in_background(source_id: int, job_id: int) -> None:
    """
    Run crawl in a background thread for development.
    In production this is replaced by a Celery task.
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if source and job:
            crawl_source(source, job, db)
    except Exception as e:
        # Mark job as failed
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if job:
            job.status = CrawlJobStatus.FAILED
            job.last_error = str(e)
            db.commit()
        print(f"[crawl] Background task failed: {e}")
    finally:
        db.close()


@router.post(
    "/trigger/{source_id}",
    response_model=CrawlJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_crawl(
    source_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> CrawlJob:
    """
    Trigger a manual crawl for a source.
    Returns immediately with the queued job — crawl runs in background.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )
    if not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source is inactive",
        )

    # Prevent duplicate running jobs
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

    # Run in background — non-blocking
    background_tasks.add_task(_run_crawl_in_background, source_id, job.id)

    return job


@router.get("/jobs", response_model=List[CrawlJobResponse])
def list_all_jobs(
    skip: int = 0,
    limit: int = 20,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
) -> List[CrawlJob]:
    """List all crawl jobs across all sources."""
    query = db.query(CrawlJob)
    if status_filter:
        query = query.filter(CrawlJob.status == status_filter)
    return (
        query.order_by(CrawlJob.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/jobs/{job_id}", response_model=CrawlJobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
) -> CrawlJob:
    """Get a specific crawl job by ID."""
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CrawlJob {job_id} not found",
        )
    return job
