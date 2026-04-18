from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.deps.auth import require_admin
from app.models.enums import ProviderType
from app.models.user import User
from app.schemas.settings_admin import (
    AIProviderRead,
    AISettingsPayload,
    ObsidianSettingsRead,
    ObsidianSettingsUpdate,
    ProviderTestRequest,
    SystemSettingsRead,
    SystemSettingsUpdate,
)
from app.services.provider_probe_service import ProviderProbeService
from app.services.settings_admin_service import SettingsAdminService

router = APIRouter()


@router.get("/system")
async def get_system_settings(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    setting = await SettingsAdminService.get_or_create_system_setting(session)
    return success_response(SystemSettingsRead.model_validate(setting).model_dump())


@router.put("/system")
async def update_system_settings(
    payload: SystemSettingsUpdate,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    setting = await SettingsAdminService.update_system_setting(session, **payload.model_dump())
    return success_response(SystemSettingsRead.model_validate(setting).model_dump())


@router.get("/ai")
async def get_ai_settings(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    providers = await SettingsAdminService.list_ai_providers(session)
    data = {
        "providers": [
            AIProviderRead(
                provider_type=ProviderType(item.provider_type),
                base_url=item.base_url,
                api_key=item.api_key_encrypted,
                model_name=item.model_name,
                extra_json=item.extra_json,
                is_enabled=item.is_enabled,
            ).model_dump()
            for item in providers
        ]
    }
    return success_response(data)


@router.put("/ai")
async def update_ai_settings(
    payload: AISettingsPayload,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    providers = await SettingsAdminService.upsert_ai_providers(
        session,
        [item.model_dump() for item in payload.providers],
    )
    return success_response(
        {
            "providers": [
                AIProviderRead(
                    provider_type=ProviderType(item.provider_type),
                    base_url=item.base_url,
                    api_key=item.api_key_encrypted,
                    model_name=item.model_name,
                    extra_json=item.extra_json,
                    is_enabled=item.is_enabled,
                ).model_dump()
                for item in providers
            ]
        }
    )


@router.get("/obsidian")
async def get_obsidian_settings(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    setting = await SettingsAdminService.get_or_create_obsidian_setting(session)
    return success_response(ObsidianSettingsRead.model_validate(setting).model_dump())


@router.put("/obsidian")
async def update_obsidian_settings(
    payload: ObsidianSettingsUpdate,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    setting = await SettingsAdminService.update_obsidian_setting(session, payload.model_dump())
    return success_response(ObsidianSettingsRead.model_validate(setting).model_dump())


@router.post("/test-provider")
async def test_provider(
    payload: ProviderTestRequest,
    _: Annotated[User, Depends(require_admin)],
) -> dict:
    try:
        result = await ProviderProbeService.test_provider(**payload.model_dump())
    except httpx.HTTPError as exc:  # type: ignore[name-defined]
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if result["status"] != "ok":
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result["message"])
    return success_response(result)
