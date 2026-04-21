from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.responses import success_response
from app.db.session import get_db_session
from app.deps.auth import require_admin, require_viewer_or_admin
from app.models.review_card import ReviewCard
from app.models.user import User
from app.schemas.review import (
    ReviewBootstrapRequest,
    ReviewBootstrapResponse,
    ReviewCardAdminCreateRequest,
    ReviewCardAdminDeleteResponse,
    ReviewCardAdminItem,
    ReviewCardAdminUpdateRequest,
    ReviewCardGenerateResponse,
    ReviewGradeRequest,
    ReviewJudgeRequest,
    ReviewJudgeResult,
    ReviewLogCreateRequest,
    ReviewLogRead,
    ReviewOverview,
    ReviewQueueItem,
    ReviewSessionFinalizeRequest,
    ReviewSessionFinalizeResponse,
    ReviewSessionState,
    ReviewSubjectSummary,
)
from app.services.job_service import JobService
from app.services.review_service import ReviewService
from app.worker.tasks import generate_review_cards as generate_review_cards_task

router = APIRouter()


def _serialize_review_card(card: ReviewCard) -> dict:
    subject = ReviewService._extract_subject_from_note(card.knowledge_point.note)
    return {
        "card_id": card.id,
        "due_at": card.due_at,
        "suspended": card.suspended,
        "subject": subject,
        "knowledge_point": {
            "id": card.knowledge_point.id,
            "note_id": card.knowledge_point.note_id,
            "title": card.knowledge_point.title,
            "content_md": card.knowledge_point.content_md,
            "embedding_vector": card.knowledge_point.embedding_vector,
            "tags_json": card.knowledge_point.tags_json,
            "summary_text": card.knowledge_point.summary_text,
            "source_anchor": card.knowledge_point.source_anchor,
            "subject": subject,
            "created_at": card.knowledge_point.created_at,
            "updated_at": card.knowledge_point.updated_at,
        },
        "note": {
            "id": card.knowledge_point.note.id,
            "title": card.knowledge_point.note.title,
            "relative_path": card.knowledge_point.note.relative_path,
        },
    }


@router.get("/overview")
async def review_overview(
    _: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    overview = await ReviewService.get_overview(session)
    return success_response(ReviewOverview(**overview).model_dump())


@router.get("/queue")
async def review_queue(
    _: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=200),
    due_only: bool = True,
    subject: str | None = Query(default=None),
) -> dict:
    cards = await ReviewService.get_queue(session, limit=limit, due_only=due_only, subject=subject)
    payload = [ReviewQueueItem(**_serialize_review_card(card)).model_dump() for card in cards]
    return success_response(payload)


@router.get("/subjects")
async def review_subjects(
    _: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    payload = [ReviewSubjectSummary(**item).model_dump() for item in await ReviewService.list_subjects(session)]
    return success_response(payload)


@router.get("/cards/admin")
async def list_review_cards_admin(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    subject: str | None = Query(default=None),
    note_id: int | None = Query(default=None, ge=1),
    query: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    cards = await ReviewService.list_admin_cards(
        session,
        subject=subject,
        note_id=note_id,
        query=query,
        limit=limit,
        offset=offset,
    )
    payload = [ReviewCardAdminItem(**_serialize_review_card(card)).model_dump() for card in cards]
    return success_response(payload)


@router.post("/cards/admin")
async def create_review_card_admin(
    payload: ReviewCardAdminCreateRequest,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    card = await ReviewService.create_admin_card(
        session,
        note_id=payload.note_id,
        title=payload.title,
        content_md=payload.content_md,
        summary_text=payload.summary_text,
        source_anchor=payload.source_anchor,
        tags=payload.tags,
        subject=payload.subject,
        suspended=payload.suspended,
    )
    cards = await ReviewService.list_admin_cards(session, note_id=payload.note_id, limit=20, offset=0)
    matched = next(item for item in cards if item.id == card.id)
    return success_response(ReviewCardAdminItem(**_serialize_review_card(matched)).model_dump())


@router.patch("/cards/admin/{card_id}")
async def update_review_card_admin(
    card_id: int,
    payload: ReviewCardAdminUpdateRequest,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    card = await ReviewService.update_admin_card(
        session,
        card_id=card_id,
        title=payload.title,
        content_md=payload.content_md,
        summary_text=payload.summary_text,
        source_anchor=payload.source_anchor,
        tags=payload.tags,
        subject=payload.subject,
        suspended=payload.suspended,
    )
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review card not found")
    cards = await ReviewService.list_admin_cards(session, limit=200, offset=0)
    matched = next(item for item in cards if item.id == card.id)
    return success_response(ReviewCardAdminItem(**_serialize_review_card(matched)).model_dump())


@router.delete("/cards/admin/{card_id}")
async def delete_review_card_admin(
    card_id: int,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    result = await ReviewService.delete_admin_card(session, card_id=card_id)
    return success_response(ReviewCardAdminDeleteResponse(**result).model_dump())


@router.post("/cards/generate")
async def generate_review_cards(
    payload: ReviewBootstrapRequest,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    settings = get_settings()
    job = await ReviewService.create_review_card_job(
        session,
        note_ids=payload.note_ids,
        all_notes=payload.all_notes,
        parent_job_id=None,
        trigger="manual_api",
        source_job_type=None,
    )

    if settings.celery_task_always_eager:
        result = await ReviewService.execute_review_card_job(
            session=session,
            job_id=job.id,
            note_ids=payload.note_ids,
            all_notes=payload.all_notes,
            parent_job_id=None,
            trigger="manual_api",
            source_job_type=None,
        )
        response = ReviewCardGenerateResponse(
            job_id=job.id,
            status="completed",
            celery_task_id=None,
            created_knowledge_points=result["created_knowledge_points"],
            created_cards=result["created_cards"],
            note_ids=result["note_ids"],
            parent_job_id=result.get("parent_job_id"),
            trigger=result.get("trigger"),
            source_job_type=result.get("source_job_type"),
        )
    else:
        async_result = generate_review_cards_task.delay(job.id)
        await JobService.attach_celery_task(session, job, async_result.id)
        await JobService.append_log(session, job, "info", "review card generation queued", queue_status="queued")
        response = ReviewCardGenerateResponse(
            job_id=job.id,
            status="queued",
            celery_task_id=async_result.id,
            created_knowledge_points=0,
            created_cards=0,
            note_ids=payload.note_ids,
            parent_job_id=None,
            trigger="manual_api",
            source_job_type=None,
        )
    return success_response(response.model_dump())


@router.post("/cards/bootstrap")
async def bootstrap_review_cards(
    payload: ReviewBootstrapRequest,
    _: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    result = await ReviewService.bootstrap_cards(session, note_ids=payload.note_ids, all_notes=payload.all_notes)
    return success_response(ReviewBootstrapResponse(**result).model_dump())


@router.post("/session/{card_id}/start")
async def start_review_session(
    card_id: int,
    current_user: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    payload = await ReviewService.start_review_session(session, card_id=card_id, user=current_user)
    return success_response(ReviewSessionState(**payload).model_dump())


@router.post("/session/{card_id}/heartbeat")
async def heartbeat_review_session(
    card_id: int,
    current_user: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    payload = await ReviewService.heartbeat_review_session(session, card_id=card_id, user=current_user)
    return success_response(ReviewSessionState(**payload).model_dump())


@router.post("/session/{card_id}/finalize")
async def finalize_review_session(
    card_id: int,
    payload: ReviewSessionFinalizeRequest,
    current_user: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    result = await ReviewService.finalize_review_session(
        session,
        card_id=card_id,
        user=current_user,
        reported_duration_seconds=payload.duration_seconds,
    )
    return success_response(ReviewSessionFinalizeResponse(**result).model_dump())


@router.post("/session/{card_id}/judge")
async def judge_review_card(
    card_id: int,
    payload: ReviewJudgeRequest,
    current_user: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    result = await ReviewService.judge_answer(
        session,
        card_id=card_id,
        answer=payload.answer,
        user=current_user,
    )
    return success_response(ReviewJudgeResult(**result).model_dump())


@router.post("/session/{card_id}/grade")
async def grade_review_card(
    card_id: int,
    payload: ReviewGradeRequest,
    current_user: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    card, review_log = await ReviewService.grade_card(
        session,
        card_id=card_id,
        rating=payload.rating,
        duration_seconds=payload.duration_seconds,
        note=payload.note,
        user=current_user,
        answer=payload.answer,
        ai_judge=payload.ai_judge,
    )
    if card is None or review_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review card not found")
    return success_response(
        {
            "card": {
                "id": card.id,
                "state_json": card.state_json,
                "due_at": card.due_at,
                "last_reviewed_at": card.last_reviewed_at,
            },
            "review_log": ReviewLogRead.model_validate(review_log).model_dump(),
        }
    )


@router.get("/logs")
async def review_logs(
    _: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    logs = await ReviewService.list_review_logs(session, limit=limit)
    return success_response([ReviewLogRead.model_validate(log).model_dump() for log in logs])


@router.post("/logs")
async def create_review_log(
    payload: ReviewLogCreateRequest,
    current_user: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    review_log = await ReviewService.create_review_log(
        session,
        review_card_id=payload.review_card_id,
        rating=payload.rating,
        duration_seconds=payload.duration_seconds,
        note=payload.note,
        user=current_user,
    )
    return success_response(ReviewLogRead.model_validate(review_log).model_dump())
