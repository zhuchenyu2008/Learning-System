from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.session import get_engine, get_sessionmaker
from app.models.enums import UserRole
from app.models.system_setting import SystemSetting
from app.models.user import User


async def seed() -> None:
    settings = get_settings()
    engine = get_engine()
    session_factory = get_sessionmaker()

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.username == settings.initial_admin_username))
        user = result.scalar_one_or_none()
        if user is None:
            admin = User(
                username=settings.initial_admin_username,
                email=settings.initial_admin_email,
                password_hash=get_password_hash(settings.initial_admin_password),
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(admin)

        system_setting = await session.get(SystemSetting, 1)
        if system_setting is None:
            session.add(
                SystemSetting(
                    allow_registration=False,
                    workspace_root=str(Path.cwd()),
                    timezone="UTC",
                    review_retention_target=30,
                )
            )

        await session.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(seed())
