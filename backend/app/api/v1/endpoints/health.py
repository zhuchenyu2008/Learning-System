from fastapi import APIRouter

from app.core.config import get_settings
from app.core.responses import success_response

router = APIRouter(prefix="/health")


@router.get("")
async def health_check() -> dict:
    settings = get_settings()
    return success_response(
        {
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
        }
    )
