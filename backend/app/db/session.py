from collections.abc import AsyncGenerator
import asyncio
import os

from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_engine_cache: dict[tuple[str, int, int | None], object] = {}
_sessionmaker_cache: dict[tuple[str, int, int | None], async_sessionmaker[AsyncSession]] = {}


def _cache_key() -> tuple[str, int, int | None]:
    settings = get_settings()
    try:
        loop_id: int | None = id(asyncio.get_running_loop())
    except RuntimeError:
        loop_id = None
    return settings.database_url, os.getpid(), loop_id


def get_engine():
    settings = get_settings()
    key = _cache_key()
    engine = _engine_cache.get(key)
    if engine is None:
        engine = create_async_engine(
            settings.database_url,
            future=True,
            echo=False,
            poolclass=NullPool,
        )
        _engine_cache[key] = engine
    return engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    key = _cache_key()
    session_factory = _sessionmaker_cache.get(key)
    if session_factory is None:
        session_factory = async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
        _sessionmaker_cache[key] = session_factory
    return session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_sessionmaker()() as session:
        yield session
