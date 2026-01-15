"""
TERA Celery App Configuration
"""
from celery import Celery
from config.settings import settings

app = Celery(
    "tera",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks.scraping_tasks"]
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
