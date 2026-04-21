from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.responses import success_response
from app.db.session import get_db_session
from app.deps.auth import require_admin, require_viewer_or_admin
from app.models.enums import ArtifactType
from app.models.user import User
from app.schemas.review import ArtifactGenerateRequest, ArtifactGenerateResponse, ArtifactListItem
from app.services.artifact_service import ArtifactService
from app.services.job_service import JobService
from app.worker.tasks import generate_summary as generate_summary_task

router = APIRouter()


@router.post("/generate")
async def generate_summary(
    payload: ArtifactGenerateRequest,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    settings = get_settings()
    job = await ArtifactService.create_summary_job(
        session,
        scope=payload.scope,
        note_ids=payload.note_ids,
        prompt_extra=payload.prompt_extra,
    )

    if settings.celery_task_always_eager:
        result = await ArtifactService.execute_summary_job(
            session=session,
            job_id=job.id,
            scope=payload.scope,
            note_ids=payload.note_ids,
            prompt_extra=payload.prompt_extra,
        )
        artifact_id = result["artifact"].id
        output_note_id = result["output_note"].id
        relative_path = result["relative_path"]
        status = result["artifact"].status
        celery_task_id = None
    else:
        async_result = generate_summary_task.delay(job.id)
        await JobService.attach_celery_task(session, job, async_result.id)
        await JobService.append_log(session, job, "info", "summary generation queued", queue_status="queued")
        artifact_id = None
        output_note_id = None
        relative_path = None
        status = "queued"
        celery_task_id = async_result.id

    response = ArtifactGenerateResponse(
        job_id=job.id,
        artifact_id=artifact_id,
        output_note_id=output_note_id,
        relative_path=relative_path,
        status=status,
        celery_task_id=celery_task_id,
    )
    return success_response(response.model_dump())


@router.get("")
async def list_summaries(
    _: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    artifacts = await ArtifactService.list_artifacts(session, ArtifactType.SUMMARY)
    return success_response([ArtifactListItem.model_validate(item).model_dump() for item in artifacts])


@router.delete("/{artifact_id}")
async def delete_summary(
    artifact_id: int,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    result = await ArtifactService.delete_artifact(session, ArtifactType.SUMMARY, artifact_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Summary artifact not found")
    return success_response(result)
