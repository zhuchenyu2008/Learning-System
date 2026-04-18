from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.deps.auth import require_viewer_or_admin
from app.models.review_card import ReviewCard
from app.models.user import User
from app.schemas.review import (
    ReviewBootstrapRequest,
    ReviewBootstrapResponse,
    ReviewGradeRequest,
    ReviewLogCreateRequest,
    ReviewLogRead,
    ReviewOverview,
    ReviewQueueItem,
)
from app.services.review_service import ReviewService

router = APIRouter()


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
) -> dict:
    cards = await ReviewService.get_queue(session, limit=limit, due_only=due_only)
    payload = [
        ReviewQueueItem(
            card_id=card.id,
            due_at=card.due_at,
            suspended=card.suspended,
            knowledge_point=card.knowledge_point,
            note={
                "id": card.knowledge_point.note.id,
                "title": card.knowledge_point.note.title,
                "relative_path": card.knowledge_point.note.relative_path,
            },
        ).model_dump()
        for card in cards
    ]
    return success_response(payload)


@router.post("/cards/bootstrap")
async def bootstrap_review_cards(
    payload: ReviewBootstrapRequest,
    _: Annotated[User, Depends(require_viewer_or_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    result = await ReviewService.bootstrap_cards(session, note_ids=payload.note_ids, all_notes=payload.all_notes)
    return success_response(ReviewBootstrapResponse(**result).model_dump())


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
