from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings


celery_app = Celery("woven_recall")


def configure_celery() -> Celery:
    settings = get_settings()
    broker_url = settings.celery_broker_url or settings.redis_url
    result_backend = settings.celery_result_backend or broker_url

    celery_app.conf.update(
        broker_url=broker_url,
        result_backend=result_backend,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_always_eager=settings.celery_task_always_eager,
        task_store_eager_result=settings.celery_task_store_eager_result,
        beat_schedule={
            "review-maintenance": {
                "task": "app.worker.tasks.review_maintenance",
                "schedule": crontab(minute=0, hour="*/6"),
                "kwargs": {"trigger": "celery_beat"},
            }
        },
    )
    celery_app.autodiscover_tasks(["app.worker"])
    return celery_app


configure_celery()
