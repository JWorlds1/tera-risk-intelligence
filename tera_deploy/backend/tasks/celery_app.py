"""
Celery Application Configuration
"""
from celery import Celery
from config.settings import settings

celery_app = Celery(
    "tera",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.scraping_tasks", "tasks.extraction_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

