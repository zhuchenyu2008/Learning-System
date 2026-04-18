from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import User
from app.schemas.auth import TokenPair
from app.services.settings_admin_service import SettingsAdminService


class AuthService:
    @staticmethod
    async def authenticate_user(session: AsyncSession, username: str, password: str) -> User | None:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    async def issue_tokens(session: AsyncSession, user: User, ip_address: str | None = None) -> TokenPair:
        user.last_login_at = datetime.now(timezone.utc)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        await SettingsAdminService.record_login_event(session, user=user, ip_address=ip_address)
        return TokenPair(
            access_token=create_access_token(user.username),
            refresh_token=create_refresh_token(user.username),
        )
