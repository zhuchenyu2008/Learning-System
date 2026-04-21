from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from celery.utils.log import get_task_logger
from sqlalchemy import select

from app.celery_app import celery_app
from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.models.enums import ArtifactScopeType, JobStatus, JobType
from app.models.job import Job
from app.services.artifact_service import ArtifactService
from app.services.job_service import JobService
from app.services.note_generation_service import NoteGenerationService
from app.services.review_service import ReviewService

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
        await JobService.append_log(session, job, "error", "worker execution failed", task_name=task_name, celery_task_id=task_id, exception_type=exc.__class__.__name__, error_message=str(exc))
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
        review_job = await ReviewService.enqueue_note_review_card_generation(
            session,
            note_ids=result["generated_note_ids"],
            parent_job_id=job_id,
            trigger="note_generation",
            source_job_type=JobType.NOTE_GENERATION.value,
        )

    review_job_payload = None
    if review_job is not None:
        settings = get_settings()
        if settings.celery_task_always_eager:
            await _run_review_card_generation(review_job.id)
        else:
            async_result = generate_review_cards.delay(review_job.id)
            async with get_sessionmaker()() as session:
                persisted_review_job = await session.get(Job, review_job.id)
                if persisted_review_job is not None:
                    await JobService.attach_celery_task(session, persisted_review_job, async_result.id)
                    await JobService.append_log(
                        session,
                        persisted_review_job,
                        "info",
                        "review card generation queued",
                        queue_status="queued",
                        parent_job_id=job_id,
                    )
            review_job_payload = {
                "job_id": review_job.id,
                "status": "queued",
                "celery_task_id": async_result.id,
            }

    return {
        "generated_note_ids": result["generated_note_ids"],
        "written_paths": result["written_paths"],
        "review_card_job": review_job_payload,
    }


async def _run_review_card_generation(job_id: int) -> dict[str, Any]:
    job = await _get_job(job_id)
    await _ensure_job_running(job)
    if job is None:
        raise ValueError("job not found")
    if job.status == JobStatus.COMPLETED.value:
        return job.result_json or {}

    payload = job.payload_json or {}
    async with get_sessionmaker()() as session:
        result = await ReviewService.execute_review_card_job(
            session=session,
            job_id=job_id,
            note_ids=payload.get("note_ids", []),
            all_notes=bool(payload.get("all_notes", False)),
            parent_job_id=payload.get("parent_job_id"),
            trigger=payload.get("trigger", "manual"),
            source_job_type=payload.get("source_job_type"),
        )
    return result


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


async def _execute_task_with_worker_logging(
    *,
    job_id: int,
    task_id: str | None,
    task_name: str,
    runner: Callable[[int], Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    await _record_worker_start(job_id, task_id, task_name)
    try:
        return await runner(job_id)
    except Exception as exc:  # noqa: BLE001
        await _record_worker_failure(job_id, task_id, task_name, exc)
        raise


@celery_app.task(name="app.worker.tasks.generate_notes", bind=True)
def generate_notes(self, job_id: int) -> dict[str, Any]:
    logger.info("consume note generation job_id=%s task_id=%s", job_id, self.request.id)
    return asyncio.run(
        _execute_task_with_worker_logging(
            job_id=job_id,
            task_id=self.request.id,
            task_name="generate_notes",
            runner=_run_note_generation,
        )
    )


@celery_app.task(name="app.worker.tasks.generate_summary", bind=True)
def generate_summary(self, job_id: int) -> dict[str, Any]:
    logger.info("consume summary job_id=%s task_id=%s", job_id, self.request.id)
    return asyncio.run(
        _execute_task_with_worker_logging(
            job_id=job_id,
            task_id=self.request.id,
            task_name="generate_summary",
            runner=lambda resolved_job_id: _run_artifact(resolved_job_id, JobType.SUMMARY_GENERATION),
        )
    )


@celery_app.task(name="app.worker.tasks.generate_mindmap", bind=True)
def generate_mindmap(self, job_id: int) -> dict[str, Any]:
    logger.info("consume mindmap job_id=%s task_id=%s", job_id, self.request.id)
    return asyncio.run(
        _execute_task_with_worker_logging(
            job_id=job_id,
            task_id=self.request.id,
            task_name="generate_mindmap",
            runner=lambda resolved_job_id: _run_artifact(resolved_job_id, JobType.MINDMAP_GENERATION),
        )
    )


@celery_app.task(name="app.worker.tasks.generate_review_cards", bind=True)
def generate_review_cards(self, job_id: int) -> dict[str, Any]:
    logger.info("consume review card generation job_id=%s task_id=%s", job_id, self.request.id)
    return asyncio.run(
        _execute_task_with_worker_logging(
            job_id=job_id,
            task_id=self.request.id,
            task_name="generate_review_cards",
            runner=_run_review_card_generation,
        )
    )


@celery_app.task(name="app.worker.tasks.review_maintenance", bind=True)
def review_maintenance(self, trigger: str = "celery") -> dict[str, Any]:
    logger.info("run review maintenance trigger=%s task_id=%s", trigger, self.request.id)
    return asyncio.run(_run_review_maintenance(trigger=trigger))
