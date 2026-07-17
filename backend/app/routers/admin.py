"""
Krishi Setu — Admin API endpoints.
Powers /admin, /crawler, and /master frontend pages.
No farmer JWT required — these are internal admin endpoints.
In production, protect with API key or admin role check.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import (
    CrawlJob,
    CrawlJobStatus,
    EligibilityRecord,
    FarmerProfile,
    Ministry,
    Scheme,
    SearchLog,
    Source,
)
from app.schemas.crawler import (
    CrawlJobResponse,
    MinistryCreate,
    MinistryResponse,
    MinistryUpdate,
    SourceCreate,
    SourceResponse,
    SourceUpdate,
)
from app.schemas.schemes import SchemeCreate, SchemeResponse, SchemeUpdate

router = APIRouter()


# ── Dashboard stats ────────────────────────────────────────────────────────────

@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)) -> dict:
    """
    Overview stats for the admin dashboard.
    """
    total_schemes = db.query(func.count(Scheme.id)).scalar()
    active_schemes = db.query(func.count(Scheme.id)).filter(Scheme.is_active == True).scalar()
    total_farmers = db.query(func.count(FarmerProfile.id)).scalar()
    active_farmers = db.query(func.count(FarmerProfile.id)).filter(FarmerProfile.is_active == True).scalar()
    total_sources = db.query(func.count(Source.id)).scalar()
    total_crawl_jobs = db.query(func.count(CrawlJob.id)).scalar()
    running_jobs = db.query(func.count(CrawlJob.id)).filter(CrawlJob.status == CrawlJobStatus.RUNNING).scalar()
    total_searches = db.query(func.count(SearchLog.id)).scalar()
    total_eligibility_checks = db.query(func.count(EligibilityRecord.id)).scalar()

    # Recent crawl jobs
    recent_jobs = (
        db.query(CrawlJob)
        .order_by(CrawlJob.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "schemes": {
            "total": total_schemes,
            "active": active_schemes,
            "inactive": total_schemes - active_schemes,
        },
        "farmers": {
            "total": total_farmers,
            "active": active_farmers,
        },
        "crawler": {
            "total_sources": total_sources,
            "total_jobs": total_crawl_jobs,
            "running_jobs": running_jobs,
        },
        "usage": {
            "total_searches": total_searches,
            "total_eligibility_checks": total_eligibility_checks,
        },
        "recent_crawl_jobs": [
            {
                "id": j.id,
                "source_id": j.source_id,
                "status": j.status,
                "urls_crawled": j.urls_crawled,
                "schemes_upserted": j.schemes_upserted,
                "created_at": j.created_at,
            }
            for j in recent_jobs
        ],
    }


# ── Scheme management ──────────────────────────────────────────────────────────

@router.get("/schemes", response_model=List[SchemeResponse])
def list_all_schemes(
    skip: int = 0,
    limit: int = 50,
    active_only: bool = False,
    ministry_id: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[Scheme]:
    query = db.query(Scheme)
    if active_only:
        query = query.filter(Scheme.is_active == True)
    if ministry_id:
        query = query.filter(Scheme.ministry_id == ministry_id)
    return query.order_by(Scheme.id).offset(skip).limit(limit).all()


@router.post("/schemes", response_model=SchemeResponse, status_code=status.HTTP_201_CREATED)
def create_scheme_admin(
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


@router.patch("/schemes/{scheme_id}", response_model=SchemeResponse)
def update_scheme_admin(
    scheme_id: int,
    payload: SchemeUpdate,
    db: Session = Depends(get_db),
) -> Scheme:
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme {scheme_id} not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(scheme, field, value)
    db.commit()
    db.refresh(scheme)
    return scheme


@router.delete("/schemes/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheme_admin(scheme_id: int, db: Session = Depends(get_db)) -> None:
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme {scheme_id} not found")
    db.delete(scheme)
    db.commit()


@router.patch("/schemes/{scheme_id}/toggle", response_model=SchemeResponse)
def toggle_scheme_active(scheme_id: int, db: Session = Depends(get_db)) -> Scheme:
    """Toggle a scheme's active/inactive status."""
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme {scheme_id} not found")
    scheme.is_active = not scheme.is_active
    db.commit()
    db.refresh(scheme)
    return scheme


# ── Source management ──────────────────────────────────────────────────────────

@router.get("/sources", response_model=List[SourceResponse])
def list_sources_admin(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[Source]:
    return db.query(Source).offset(skip).limit(limit).all()


@router.post("/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source_admin(
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


@router.patch("/sources/{source_id}", response_model=SourceResponse)
def update_source_admin(
    source_id: int,
    payload: SourceUpdate,
    db: Session = Depends(get_db),
) -> Source:
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source_admin(source_id: int, db: Session = Depends(get_db)) -> None:
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    db.delete(source)
    db.commit()


# ── Ministry management ────────────────────────────────────────────────────────

@router.get("/ministries", response_model=List[MinistryResponse])
def list_ministries_admin(
    db: Session = Depends(get_db),
) -> List[Ministry]:
    return db.query(Ministry).all()


@router.post("/ministries", response_model=MinistryResponse, status_code=status.HTTP_201_CREATED)
def create_ministry_admin(
    payload: MinistryCreate,
    db: Session = Depends(get_db),
) -> Ministry:
    existing = db.query(Ministry).filter(Ministry.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ministry '{payload.name}' already exists",
        )
    ministry = Ministry(**payload.model_dump())
    db.add(ministry)
    db.commit()
    db.refresh(ministry)
    return ministry


# ── Crawler management ─────────────────────────────────────────────────────────

@router.get("/crawl-jobs", response_model=List[CrawlJobResponse])
def list_crawl_jobs_admin(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[CrawlJobStatus] = None,
    source_id: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[CrawlJob]:
    query = db.query(CrawlJob)
    if status_filter:
        query = query.filter(CrawlJob.status == status_filter)
    if source_id:
        query = query.filter(CrawlJob.source_id == source_id)
    return query.order_by(CrawlJob.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/crawl-jobs/trigger/{source_id}", status_code=status.HTTP_202_ACCEPTED)
def trigger_crawl_admin(
    source_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Trigger a crawl job from the admin panel."""
    from app.models.models import CrawlJobType
    from app.tasks import crawl_source_task

    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    active_job = (
        db.query(CrawlJob)
        .filter(
            CrawlJob.source_id == source_id,
            CrawlJob.status.in_([CrawlJobStatus.QUEUED, CrawlJobStatus.RUNNING]),
        )
        .first()
    )
    if active_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job {active_job.id} already active for source {source_id}",
        )

    job = CrawlJob(
        source_id=source_id,
        status=CrawlJobStatus.QUEUED,
        job_type=CrawlJobType.MANUAL,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        task = crawl_source_task.delay(source_id, job.id)
        return {"job_id": job.id, "celery_task_id": task.id, "status": "queued"}
    except Exception as e:
        return {"job_id": job.id, "celery_task_id": None, "status": "queued", "note": str(e)}


# ── Farmer management ──────────────────────────────────────────────────────────

@router.get("/farmers")
def list_farmers_admin(
    skip: int = 0,
    limit: int = 50,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(FarmerProfile)
    if state:
        query = query.filter(FarmerProfile.state == state)
    total = query.count()
    farmers = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "farmers": [
            {
                "id": f.id,
                "name": f.name,
                "phone": f.phone,
                "state": f.state,
                "district": f.district,
                "land_holding_acres": f.land_holding_acres,
                "caste": f.caste,
                "is_active": f.is_active,
                "created_at": f.created_at,
            }
            for f in farmers
        ],
    }


# ── Search logs ────────────────────────────────────────────────────────────────

@router.get("/search-logs")
def list_search_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    total = db.query(func.count(SearchLog.id)).scalar()
    logs = (
        db.query(SearchLog)
        .order_by(SearchLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "logs": [
            {
                "id": l.id,
                "query_raw": l.query_raw,
                "results_count": l.results_count,
                "response_time_ms": l.response_time_ms,
                "farmer_id": l.farmer_id,
                "created_at": l.created_at,
            }
            for l in logs
        ],
    } 
