from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.deps.auth import require_admin
from app.integrations.obsidian_sync import ObsidianHeadlessSyncService
from app.models.user import User
from app.schemas.settings_admin import AdminUserRead, LoginEventRead
from app.services.settings_admin_service import SettingsAdminService

router = APIRouter()


@router.get("/users")
async def list_users(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    users = await SettingsAdminService.list_users(session)
    return success_response([AdminUserRead.model_validate(user).model_dump() for user in users])


@router.get("/user-activity")
async def list_user_activity(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await SettingsAdminService.build_user_activity(session)
    return success_response(data)


@router.get("/login-events")
async def list_login_events(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    events = await SettingsAdminService.list_login_events(session)
    return success_response([LoginEventRead.model_validate(event).model_dump() for event in events])


@router.post("/database/export")
async def export_database(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    try:
        result = await SettingsAdminService.export_database(session)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return success_response(
        {
            "status": "completed",
            "message": "Database export completed",
            "path": result["path"],
            "filename": result["filename"],
            "job_id": result["job_id"],
        }
    )


@router.post("/database/import")
async def import_database(
    file: UploadFile = File(...),
    _: Annotated[User, Depends(require_admin)] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> dict:
    try:
        result = await SettingsAdminService.import_database(session, file)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return success_response(
        {
            "status": "completed",
            "message": "Database import completed",
            "imported": result["imported"],
            "job_id": result["job_id"],
        }
    )


@router.post("/obsidian/sync")
async def trigger_obsidian_sync(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await SettingsAdminService.get_or_create_obsidian_setting(session)
    result = ObsidianHeadlessSyncService.sync()
    if not result.executed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.stderr or "Obsidian sync failed")
    return success_response(result.model_dump())
