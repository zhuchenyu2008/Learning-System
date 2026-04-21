from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.core.security import validate_token_type
from app.db.session import get_db_session
from app.deps.auth import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, UserRead
from app.schemas.settings_admin import SystemSettingsRead
from app.services.auth_service import AuthService
from app.services.settings_admin_service import SettingsAdminService

router = APIRouter()


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    user = await AuthService.authenticate_user(session, payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    tokens = await AuthService.issue_tokens(session, user, ip_address=request.client.host if request.client else None)
    return success_response({"user": UserRead.model_validate(user).model_dump(), "tokens": tokens.model_dump()})


@router.post("/register")
async def register(
    payload: RegisterRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    setting = await SettingsAdminService.get_or_create_system_setting(session)
    if not setting.allow_registration:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration is disabled")

    user = await AuthService.register_user(session, payload.username, payload.email, payload.password)
    tokens = await AuthService.issue_tokens(session, user, ip_address=request.client.host if request.client else None)
    return success_response({"user": UserRead.model_validate(user).model_dump(), "tokens": tokens.model_dump()})


@router.post("/refresh")
async def refresh_token(payload: RefreshRequest, session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict:
    try:
        token_payload = validate_token_type(payload.refresh_token, "refresh")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    username = token_payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    tokens = await AuthService.issue_tokens(session, user)
    return success_response({"tokens": tokens.model_dump()})


@router.post("/logout")
async def logout() -> dict:
    return success_response({"message": "Logged out"})


@router.get("/registration")
async def registration_status(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    setting = await SettingsAdminService.get_or_create_system_setting(session)
    payload = SystemSettingsRead.model_validate(setting).model_dump()
    return success_response(
        {
            "allow_registration": payload["allow_registration"],
            "workspace_root": payload["workspace_root"],
            "timezone": payload["timezone"],
            "review_retention_target": payload["review_retention_target"],
        }
    )


@router.get("/me")
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> dict:
    return success_response(UserRead.model_validate(current_user).model_dump())
