"""
Krishi Setu — Celery Tasks
All async jobs: crawling, scheduling, notifications.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from celery import shared_task
from celery.utils.log import get_task_logger

from app.celery_app import celery_app

logger = get_task_logger(__name__)


# ── Crawl task ─────────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    name="app.tasks.crawl_source_task",
)
def crawl_source_task(self, source_id: int, job_id: int) -> dict:
    """
    Execute a crawl for a specific source.
    Replaces the BackgroundTasks thread-based approach.
    """
    from app.database import SessionLocal
    from app.models.models import CrawlJob, CrawlJobStatus, Source
    from app.services.crawler import crawl_source

    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()

        if not source or not job:
            logger.error(f"Source {source_id} or Job {job_id} not found")
            return {"status": "error", "message": "Source or job not found"}

        # Store Celery task ID in job record
        job.celery_task_id = self.request.id
        db.commit()

        logger.info(f"Starting crawl for source {source_id} ({source.name})")
        crawl_source(source, job, db)

        return {
            "status": "completed",
            "source_id": source_id,
            "job_id": job_id,
            "urls_crawled": job.urls_crawled,
            "schemes_upserted": job.schemes_upserted,
        }

    except Exception as exc:
        logger.error(f"Crawl task failed for source {source_id}: {exc}")

        # Update job as failed
        try:
            job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
            if job:
                from app.models.models import CrawlJobStatus
                job.status = CrawlJobStatus.FAILED
                job.last_error = str(exc)
                job.attempts += 1
                db.commit()
        except Exception:
            pass

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 60)

    finally:
        db.close()


# ── Scheduler task (replaces APScheduler) ─────────────────────────────────────

@celery_app.task(name="app.tasks.schedule_due_crawls")
def schedule_due_crawls() -> dict:
    """
    Check for sources due for crawling and dispatch crawl tasks.
    Run by Celery Beat every 60 seconds.
    Replaces APScheduler's run_scheduled_crawls().
    """
    from app.database import SessionLocal
    from app.models.models import CrawlJob, CrawlJobStatus, CrawlJobType, Source

    db = SessionLocal()
    queued_count = 0

    try:
        now = datetime.now(timezone.utc)

        due_sources = (
            db.query(Source)
            .filter(
                Source.is_active == True,
                (Source.next_crawl_at == None) | (Source.next_crawl_at <= now),
            )
            .all()
        )

        for source in due_sources:
            # Check for active jobs
            active = (
                db.query(CrawlJob)
                .filter(
                    CrawlJob.source_id == source.id,
                    CrawlJob.status.in_([
                        CrawlJobStatus.QUEUED,
                        CrawlJobStatus.RUNNING,
                    ]),
                )
                .first()
            )

            if active:
                logger.info(f"Skipping source {source.id} — active job exists")
                continue

            # Create job record
            job = CrawlJob(
                source_id=source.id,
                status=CrawlJobStatus.QUEUED,
                job_type=CrawlJobType.INCREMENTAL,
                scheduled_at=now,
            )
            db.add(job)

            # Update next crawl time
            source.next_crawl_at = now + timedelta(hours=source.crawl_interval_hours)
            db.commit()
            db.refresh(job)

            # Dispatch Celery task
            crawl_source_task.delay(source.id, job.id)
            queued_count += 1
            logger.info(f"Queued crawl job {job.id} for source {source.id}")

        return {"queued": queued_count, "checked": len(due_sources)}

    except Exception as e:
        logger.error(f"schedule_due_crawls failed: {e}")
        return {"error": str(e)}
    finally:
        db.close()


# ── Notification task (future use) ────────────────────────────────────────────

@celery_app.task(name="app.tasks.send_eligibility_notification")
def send_eligibility_notification(
    farmer_id: int,
    scheme_id: int,
    result: str,
) -> dict:
    """
    Placeholder for farmer notification when eligibility result is ready.
    Future: integrate SMS (Twilio) or WhatsApp API.
    """
    logger.info(
        f"[notify] Farmer {farmer_id} — Scheme {scheme_id} — Result: {result}"
    )
    return {
        "farmer_id": farmer_id,
        "scheme_id": scheme_id,
        "result": result,
        "status": "logged",
    } 
