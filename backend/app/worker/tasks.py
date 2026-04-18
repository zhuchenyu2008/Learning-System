from __future__ import annotations

import asyncio
from typing import Any

from celery.utils.log import get_task_logger
from sqlalchemy import select

from app.celery_app import celery_app
from app.db.session import get_sessionmaker
from app.models.enums import ArtifactScopeType, JobStatus, JobType
from app.models.job import Job
from app.services.artifact_service import ArtifactService
from app.services.job_service import JobService
from app.services.note_generation_service import NoteGenerationService

logger = get_task_logger(__name__)


async def _get_job(job_id: int) -> Job | None:
    async with get_sessionmaker()() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()


async def _ensure_job_running(job: Job | None) -> None:
    if job is None:
        raise ValueError("job not found")
    if job.status == JobStatus.COMPLETED.value:
        return
    async with get_sessionmaker()() as session:
        persisted = await session.get(Job, job.id)
        if persisted is None:
            raise ValueError("job not found")
        if persisted.status == JobStatus.PENDING.value:
            await JobService.mark_running(session, persisted)
        else:
            await JobService.append_log(session, persisted, "info", "worker resumed existing job", status=persisted.status)


async def _record_worker_start(job_id: int, task_id: str | None, task_name: str) -> None:
    async with get_sessionmaker()() as session:
        job = await session.get(Job, job_id)
        if job is None:
            raise ValueError("job not found")
        if task_id and job.celery_task_id != task_id:
            await JobService.attach_celery_task(session, job, task_id)
        await JobService.append_log(session, job, "info", "worker accepted job", task_name=task_name, celery_task_id=task_id)


async def _record_worker_failure(job_id: int, task_id: str | None, task_name: str, exc: Exception) -> None:
    async with get_sessionmaker()() as session:
        job = await session.get(Job, job_id)
        if job is None:
            return
        if task_id and job.celery_task_id != task_id:
            await JobService.attach_celery_task(session, job, task_id)
        await JobService.append_log(session, job, "error", "worker execution failed", task_name=task_name, celery_task_id=task_id)
        await JobService.mark_failed(session, job, str(exc))


async def _run_note_generation(job_id: int) -> dict[str, Any]:
    job = await _get_job(job_id)
    await _ensure_job_running(job)
    if job is None:
        raise ValueError("job not found")
    if job.status == JobStatus.COMPLETED.value:
        return job.result_json or {}

    payload = job.payload_json or {}
    async with get_sessionmaker()() as session:
        result = await NoteGenerationService.execute_job_payload(
            session=session,
            job_id=job_id,
            source_asset_ids=payload.get("source_asset_ids", []),
            note_directory=payload.get("note_directory"),
            force_regenerate=bool(payload.get("force_regenerate", False)),
            sync_to_obsidian=bool(payload.get("sync_to_obsidian", False)),
        )
    return {
        "generated_note_ids": result["generated_note_ids"],
        "written_paths": result["written_paths"],
    }


async def _run_artifact(job_id: int, job_type: JobType) -> dict[str, Any]:
    job = await _get_job(job_id)
    await _ensure_job_running(job)
    if job is None:
        raise ValueError("job not found")
    if job.status == JobStatus.COMPLETED.value:
        return job.result_json or {}

    payload = job.payload_json or {}
    scope = ArtifactScopeType(payload.get("scope", ArtifactScopeType.MANUAL.value))
    async with get_sessionmaker()() as session:
        if job_type == JobType.SUMMARY_GENERATION:
            result = await ArtifactService.execute_summary_job(
                session=session,
                job_id=job_id,
                scope=scope,
                note_ids=payload.get("note_ids", []),
                prompt_extra=payload.get("prompt_extra"),
            )
        else:
            result = await ArtifactService.execute_mindmap_job(
                session=session,
                job_id=job_id,
                scope=scope,
                note_ids=payload.get("note_ids", []),
                prompt_extra=payload.get("prompt_extra"),
            )
    return {
        "artifact_id": result["artifact"].id,
        "output_note_id": result["output_note"].id,
        "relative_path": result["relative_path"],
        "status": result["artifact"].status,
    }


async def _run_review_maintenance(trigger: str = "celery") -> dict[str, Any]:
    async with get_sessionmaker()() as session:
        job = await JobService.create_job(
            session,
            JobType.SCHEDULED_REVIEW_MAINTENANCE,
            {"task_name": "review.maintenance", "trigger": trigger},
        )
        await JobService.mark_running(session, job)
        await JobService.mark_completed(
            session,
            job,
            {"task_name": "review.maintenance", "trigger": trigger, "status": "heartbeat_ok"},
        )
        return {"job_id": job.id, "status": "completed"}


@celery_app.task(name="app.worker.tasks.generate_notes", bind=True)
def generate_notes(self, job_id: int) -> dict[str, Any]:
    logger.info("consume note generation job_id=%s task_id=%s", job_id, self.request.id)
    asyncio.run(_record_worker_start(job_id, self.request.id, "generate_notes"))
    try:
        return asyncio.run(_run_note_generation(job_id))
    except Exception as exc:  # noqa: BLE001
        asyncio.run(_record_worker_failure(job_id, self.request.id, "generate_notes", exc))
        raise


@celery_app.task(name="app.worker.tasks.generate_summary", bind=True)
def generate_summary(self, job_id: int) -> dict[str, Any]:
    logger.info("consume summary job_id=%s task_id=%s", job_id, self.request.id)
    asyncio.run(_record_worker_start(job_id, self.request.id, "generate_summary"))
    try:
        return asyncio.run(_run_artifact(job_id, JobType.SUMMARY_GENERATION))
    except Exception as exc:  # noqa: BLE001
        asyncio.run(_record_worker_failure(job_id, self.request.id, "generate_summary", exc))
        raise


@celery_app.task(name="app.worker.tasks.generate_mindmap", bind=True)
def generate_mindmap(self, job_id: int) -> dict[str, Any]:
    logger.info("consume mindmap job_id=%s task_id=%s", job_id, self.request.id)
    asyncio.run(_record_worker_start(job_id, self.request.id, "generate_mindmap"))
    try:
        return asyncio.run(_run_artifact(job_id, JobType.MINDMAP_GENERATION))
    except Exception as exc:  # noqa: BLE001
        asyncio.run(_record_worker_failure(job_id, self.request.id, "generate_mindmap", exc))
        raise


@celery_app.task(name="app.worker.tasks.review_maintenance", bind=True)
def review_maintenance(self, trigger: str = "celery") -> dict[str, Any]:
    logger.info("run review maintenance trigger=%s task_id=%s", trigger, self.request.id)
    return asyncio.run(_run_review_maintenance(trigger=trigger))
