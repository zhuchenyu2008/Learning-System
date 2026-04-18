from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import JobStatus, JobType
from app.models.job import Job


class JobService:
    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _append_log(job: Job, level: str, message: str, **extra: Any) -> list[dict[str, Any]]:
        current_logs = list(job.logs_json or [])
        entry: dict[str, Any] = {
            "timestamp": JobService._utcnow().isoformat(),
            "level": level,
            "message": message,
        }
        if extra:
            entry.update(extra)
        current_logs.append(entry)
        return current_logs[-100:]

    @staticmethod
    async def create_job(session: AsyncSession, job_type: JobType, payload: dict) -> Job:
        job = Job(
            job_type=job_type.value,
            status=JobStatus.PENDING.value,
            payload_json=payload,
            result_json={},
            logs_json=[],
        )
        job.logs_json = JobService._append_log(job, "info", "job created", status=job.status)
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

    @staticmethod
    async def attach_celery_task(session: AsyncSession, job: Job, celery_task_id: str | None) -> Job:
        job.celery_task_id = celery_task_id
        result_json = dict(job.result_json or {})
        if celery_task_id:
            result_json["celery_task_id"] = celery_task_id
        job.result_json = result_json
        job.logs_json = JobService._append_log(
            job,
            "info",
            "job dispatched to celery",
            celery_task_id=celery_task_id,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

    @staticmethod
    async def append_log(session: AsyncSession, job: Job, level: str, message: str, **extra: Any) -> Job:
        job.logs_json = JobService._append_log(job, level, message, **extra)
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

    @staticmethod
    async def mark_running(session: AsyncSession, job: Job) -> Job:
        job.status = JobStatus.RUNNING.value
        job.started_at = job.started_at or JobService._utcnow()
        job.error_message = None
        job.logs_json = JobService._append_log(job, "info", "job running", status=job.status)
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

    @staticmethod
    async def mark_completed(session: AsyncSession, job: Job, result: dict) -> Job:
        job.status = JobStatus.COMPLETED.value
        job.result_json = result
        job.finished_at = JobService._utcnow()
        job.logs_json = JobService._append_log(job, "info", "job completed", status=job.status)
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

    @staticmethod
    async def mark_failed(session: AsyncSession, job: Job, message: str) -> Job:
        job.status = JobStatus.FAILED.value
        job.error_message = message
        job.finished_at = JobService._utcnow()
        job.logs_json = JobService._append_log(job, "error", "job failed", status=job.status, error_message=message)
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job
