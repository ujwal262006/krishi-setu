"""
Crawler API endpoints.
Crawl jobs dispatched via Celery tasks — not BackgroundTasks.
Falls back to BackgroundTasks if Celery/Redis is unavailable (dev mode).
"""

from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import CrawlJob, CrawlJobStatus, CrawlJobType, Source
from app.schemas.crawler import CrawlJobResponse

router = APIRouter()


def _dispatch_crawl(source_id: int, job_id: int, background_tasks: BackgroundTasks) -> None:
    """
    Try to dispatch via Celery. Fall back to BackgroundTasks if Redis unavailable.
    This pattern allows the app to run in dev without Redis running.
    """
    try:
        from app.tasks import crawl_source_task
        crawl_source_task.delay(source_id, job_id)
    except Exception:
        # Redis/Celery not available — fall back to background thread (dev only)
        from app.routers._crawler_bg import run_crawl_background
        background_tasks.add_task(run_crawl_background, source_id, job_id)


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
    Dispatches to Celery if available, falls back to background thread in dev.
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

    active_job = (
        db.query(CrawlJob)
        .filter(
            CrawlJob.source_id == source_id,
            CrawlJob.status.in_([
                CrawlJobStatus.QUEUED,
                CrawlJobStatus.RUNNING,
            ]),
        )
        .first()
    )
    if active_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Crawl job {active_job.id} is already queued or running for source {source_id}",
        )

    job = CrawlJob(
        source_id=source_id,
        status=CrawlJobStatus.QUEUED,
        job_type=CrawlJobType.MANUAL,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    _dispatch_crawl(source_id, job.id, background_tasks)

    return job


@router.get("/jobs", response_model=List[CrawlJobResponse])
def list_all_jobs(
    skip: int = 0,
    limit: int = 20,
    status_filter: CrawlJobStatus | None = None,
    db: Session = Depends(get_db),
) -> List[CrawlJob]:
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
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CrawlJob {job_id} not found",
        )
    return job