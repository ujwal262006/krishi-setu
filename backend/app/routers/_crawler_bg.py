"""
Background thread fallback for crawling when Celery/Redis is unavailable.
Used in development only. Production uses Celery tasks exclusively.
"""


def run_crawl_background(source_id: int, job_id: int) -> None:
    from app.database import SessionLocal
    from app.models.models import CrawlJob, CrawlJobStatus, Source
    from app.services.crawler import crawl_source

    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if source and job:
            crawl_source(source, job, db)
    except Exception as e:
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if job:
            job.status = CrawlJobStatus.FAILED
            job.last_error = str(e)
            db.commit()
    finally:
        db.close() 
