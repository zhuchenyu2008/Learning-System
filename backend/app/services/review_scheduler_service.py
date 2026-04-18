from __future__ import annotations

from app.models.enums import JobStatus, JobType


class ReviewSchedulerService:
    @staticmethod
    def get_registered_tasks() -> list[dict]:
        return [
            {
                "name": "review.generate_summaries",
                "task": "app.worker.tasks.generate_summary",
                "job_type": JobType.SUMMARY_GENERATION.value,
                "schedule": "0 2 * * *",
                "enabled": False,
                "description": "Celery beat entry reserved for scheduled summary generation.",
            },
            {
                "name": "review.generate_mindmaps",
                "task": "app.worker.tasks.generate_mindmap",
                "job_type": JobType.MINDMAP_GENERATION.value,
                "schedule": "30 2 * * *",
                "enabled": False,
                "description": "Celery beat entry reserved for scheduled mindmap generation.",
            },
            {
                "name": "review.maintenance",
                "task": "app.worker.tasks.review_maintenance",
                "job_type": JobType.SCHEDULED_REVIEW_MAINTENANCE.value,
                "schedule": "0 */6 * * *",
                "enabled": True,
                "description": "Celery beat maintenance heartbeat task for review queue upkeep.",
            },
        ]

    @staticmethod
    def create_placeholder_job_payload(task_name: str) -> dict:
        return {
            "task_name": task_name,
            "scheduler": "celery_beat",
            "status": JobStatus.PENDING.value,
        }
