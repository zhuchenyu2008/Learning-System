from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.responses import success_response
from app.db.session import get_db_session
from app.deps.auth import require_admin, require_viewer_or_admin
from app.models.user import User
from app.schemas.ingestion import NoteDetail, NoteGenerateRequest, NoteRead, NoteWatchRequest
from app.services.job_service import JobService
from app.services.note_generation_service import NoteGenerationService
from app.services.note_lifecycle_service import NoteLifecycleService
from app.services.note_query_service import NoteQueryService
from app.services.review_service import ReviewService
from app.services.safe_file_service import SafeFileService
from app.worker.tasks import generate_notes as generate_notes_task
from app.worker.tasks import generate_review_cards as generate_review_cards_task

router = APIRouter()


@router.post("/generate")
async def generate_notes(
    payload: NoteGenerateRequest,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    settings = get_settings()
    job = await NoteGenerationService.create_job_for_assets(
        session,
        source_asset_ids=payload.source_asset_ids,
        note_directory=payload.note_directory,
        force_regenerate=payload.force_regenerate,
        sync_to_obsidian=payload.sync_to_obsidian,
    )

    if settings.celery_task_always_eager:
        result = await NoteGenerationService.execute_job_payload(
            session=session,
            job_id=job.id,
            source_asset_ids=payload.source_asset_ids,
            note_directory=payload.note_directory,
            force_regenerate=payload.force_regenerate,
            sync_to_obsidian=payload.sync_to_obsidian,
        )
        review_job = await ReviewService.enqueue_note_review_card_generation(
            session,
            note_ids=result["generated_note_ids"],
            parent_job_id=job.id,
            trigger="note_generation",
            source_job_type="note_generation",
        )
        review_job_payload = None
        if review_job is not None:
            review_result = await ReviewService.execute_review_card_job(
                session=session,
                job_id=review_job.id,
                note_ids=result["generated_note_ids"],
                all_notes=False,
                parent_job_id=job.id,
                trigger="note_generation",
                source_job_type="note_generation",
            )
            review_job_payload = {
                "job_id": review_job.id,
                "status": "completed",
                "created_knowledge_points": review_result["created_knowledge_points"],
                "created_cards": review_result["created_cards"],
            }
        data = {
            "job": job.id,
            "generated_note_ids": result["generated_note_ids"],
            "written_paths": result["written_paths"],
            "review_card_job": review_job_payload,
        }
    else:
        async_result = generate_notes_task.delay(job.id)
        await JobService.attach_celery_task(session, job, async_result.id)
        await JobService.append_log(session, job, "info", "note generation queued", queue_status="queued")
        data = {
            "job": job.id,
            "generated_note_ids": [],
            "written_paths": [],
            "status": "queued",
            "celery_task_id": async_result.id,
        }
    return success_response(data)


@router.get("")
async def list_notes(
    _: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    include_artifacts: bool = Query(default=False),
) -> dict:
    notes = await NoteQueryService.list_notes(session, include_artifacts=include_artifacts)
    return success_response([NoteRead.model_validate(note).model_dump() for note in notes])


@router.get("/tree")
async def notes_tree(
    _: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    include_artifacts: bool = Query(default=False),
) -> dict:
    notes = await NoteQueryService.list_notes(session, include_artifacts=include_artifacts)
    return success_response(NoteQueryService.build_tree(notes))


@router.get("/{note_id}")
async def get_note_detail(
    note_id: int,
    request: Request,
    _: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_viewer_or_admin)],
) -> dict:
    note = await NoteQueryService.get_note(session, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    content = SafeFileService.read_text(Path(note.relative_path))
    await ReviewService.record_user_activity(
        session,
        user=current_user,
        event_type="note_view",
        page_view_increment=1,
        note_view_increment=1,
    )
    await session.commit()
    payload = NoteRead.model_validate(note).model_dump()
    payload["content"] = content
    return success_response(payload)


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    result = await NoteLifecycleService.delete_note(session, note_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return success_response(
        {
            "id": result.deleted_note_id,
            "deleted_note_id": result.deleted_note_id,
            "deleted_artifact_id": result.deleted_artifact_id,
            "deleted_relative_paths": result.deleted_relative_paths,
        }
    )


@router.post("/{note_id}/watch")
async def report_note_watch_seconds(
    note_id: int,
    payload: NoteWatchRequest,
    request: Request,
    _: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_viewer_or_admin)],
) -> dict:
    note = await NoteQueryService.get_note(session, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    await ReviewService.record_user_activity(
        session,
        user=current_user,
        event_type="note_watch",
        watch_seconds=payload.watch_seconds,
    )
    await session.commit()
    return success_response({"note_id": note_id, "watch_seconds": payload.watch_seconds})
