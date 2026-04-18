from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.responses import success_response
from app.deps.auth import require_admin
from app.models.user import User
from app.services.review_scheduler_service import ReviewSchedulerService

router = APIRouter()


@router.get("/tasks")
async def list_scheduler_tasks(_: Annotated[User, Depends(require_admin)]) -> dict:
    return success_response(ReviewSchedulerService.get_registered_tasks())
