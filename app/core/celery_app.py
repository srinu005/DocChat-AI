"""Celery application instance and shared task configuration."""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "docai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.qa_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)
