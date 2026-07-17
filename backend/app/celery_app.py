"""
Krishi Setu — Celery Application
Replaces BackgroundTasks for production-grade async job execution.
Broker: Redis (Upstash in production, local Redis in dev)
"""

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

# ── Celery app ─────────────────────────────────────────────────────────────────
# Upstash requires SSL cert params for rediss:// URLs
redis_url = settings.REDIS_URL
if redis_url.startswith("rediss://"):
    if "ssl_cert_reqs" not in redis_url:
        redis_url = redis_url + "?ssl_cert_reqs=CERT_NONE"

celery_app = Celery(
    "krishi_setu",
    broker=redis_url,
    backend=redis_url,
    include=["app.tasks"],
)

# ── Celery configuration ───────────────────────────────────────────────────────
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,

    # Task execution
    task_acks_late=True,           # Acknowledge after completion, not on receipt
    task_reject_on_worker_lost=True,  # Re-queue if worker dies mid-task
    worker_prefetch_multiplier=1,  # One task at a time per worker (crawls are heavy)

    # Result expiry
    result_expires=3600,           # Keep results for 1 hour

    # Retry defaults
    task_max_retries=3,
    task_default_retry_delay=60,   # 60 seconds between retries

    # Rate limiting
    task_annotations={
        "app.tasks.crawl_source_task": {
            "rate_limit": "10/h",  # Max 10 crawls per hour
        }
    },
)

# ── Celery Beat schedule (replaces APScheduler) ────────────────────────────────
celery_app.conf.beat_schedule = {
    "check-due-crawls-every-minute": {
        "task": "app.tasks.schedule_due_crawls",
        "schedule": 60.0,  # Every 60 seconds
    },
}
