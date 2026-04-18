from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User

TEST_DB_URL = "sqlite+aiosqlite:///./test_learning_system.db"


@pytest.fixture
async def client(tmp_path: Path) -> AsyncGenerator[AsyncClient, None]:
    settings = get_settings()
    settings.database_url = TEST_DB_URL
    settings.workspace_root = str(tmp_path / "workspace")
    settings.redis_url = "redis://localhost:6379/15"
    settings.celery_broker_url = "memory://"
    settings.celery_result_backend = "cache+memory://"
    settings.celery_task_always_eager = True
    settings.celery_task_store_eager_result = True

    engine = create_async_engine(TEST_DB_URL, future=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        session.add(
            User(
                username="admin",
                email="admin@example.com",
                password_hash=get_password_hash("ChangeMe123!"),
                role=UserRole.ADMIN,
                is_active=True,
            )
        )
        await session.commit()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    from app.celery_app import configure_celery
    from app.main import create_app

    configure_celery()
    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as async_client:
        yield async_client

    await engine.dispose()


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    return tmp_path / "workspace"


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "ChangeMe123!"},
    )
    token = response.json()["data"]["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
