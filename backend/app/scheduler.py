"""
Krishi Setu — Scheduled Crawling
Uses APScheduler to periodically check sources due for crawling
based on next_crawl_at and crawl_interval_hours stored in the DB.
Change-aware: only triggers crawl if next_crawl_at has passed.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.models import CrawlJob, CrawlJobStatus, CrawlJobType, Source


def _get_due_sources(db: Session) -> list[Source]:
    """
    Return all active sources whose next_crawl_at has passed
    or has never been set (never crawled before).
    """
    now = datetime.now(timezone.utc)
    return (
        db.query(Source)
        .filter(
            Source.is_active == True,
            (Source.next_crawl_at == None) | (Source.next_crawl_at <= now),
        )
        .all()
    )


def _has_active_job(source_id: int, db: Session) -> bool:
    """Check if a QUEUED or RUNNING job already exists for this source."""
    return (
        db.query(CrawlJob)
        .filter(
            CrawlJob.source_id == source_id,
            CrawlJob.status.in_([
                CrawlJobStatus.QUEUED,
                CrawlJobStatus.RUNNING,
            ]),
        )
        .first()
    ) is not None


def _schedule_next_crawl(source: Source, db: Session) -> None:
    """Update next_crawl_at based on the source's crawl_interval_hours."""
    source.next_crawl_at = datetime.now(timezone.utc) + timedelta(
        hours=source.crawl_interval_hours
    )
    db.commit()


def run_scheduled_crawls() -> None:
    """
    Called by APScheduler every minute.
    Checks for sources due for crawling and queues jobs for them.
    Actual crawl execution is handled by the background task mechanism.
    """
    from app.services.crawler import crawl_source

    db = SessionLocal()
    try:
        due_sources = _get_due_sources(db)

        if not due_sources:
            return

        print(f"[scheduler] {len(due_sources)} source(s) due for crawling")

        for source in due_sources:
            if _has_active_job(source.id, db):
                print(f"[scheduler] Skipping source {source.id} — job already active")
                continue

            # Create crawl job
            job = CrawlJob(
                source_id=source.id,
                status=CrawlJobStatus.QUEUED,
                job_type=CrawlJobType.INCREMENTAL,
                scheduled_at=datetime.now(timezone.utc),
            )
            db.add(job)
            db.commit()
            db.refresh(job)

            # Update next crawl time immediately to prevent duplicate scheduling
            _schedule_next_crawl(source, db)

            print(f"[scheduler] Queued job {job.id} for source {source.id} ({source.name})")

            # Execute crawl (in-process for now — Celery in production)
            try:
                crawl_source(source, job, db)
            except Exception as e:
                job.status = CrawlJobStatus.FAILED
                job.last_error = str(e)
                db.commit()
                print(f"[scheduler] Job {job.id} failed: {e}")

    except Exception as e:
        print(f"[scheduler] Unexpected error: {e}")
    finally:
        db.close()


# ── Scheduler singleton ────────────────────────────────────────────────────────

_scheduler: Optional[BackgroundScheduler] = None


def start_scheduler() -> None:
    """Start the APScheduler background scheduler."""
    global _scheduler

    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        run_scheduled_crawls,
        trigger=IntervalTrigger(minutes=1),
        id="scheduled_crawl",
        name="Check and run due crawl jobs",
        replace_existing=True,
        max_instances=1,  # Never run two scheduler checks concurrently
    )
    _scheduler.start()
    print("[scheduler] Started — checking for due crawls every 60 seconds")


def stop_scheduler() -> None:
    """Gracefully stop the scheduler on app shutdown."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("[scheduler] Stopped")
