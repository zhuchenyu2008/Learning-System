from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_engine_cache: dict[str, object] = {}
_sessionmaker_cache: dict[str, async_sessionmaker[AsyncSession]] = {}


def get_engine():
    settings = get_settings()
    database_url = settings.database_url
    engine = _engine_cache.get(database_url)
    if engine is None:
        engine = create_async_engine(database_url, future=True, echo=False)
        _engine_cache[database_url] = engine
    return engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    database_url = settings.database_url
    session_factory = _sessionmaker_cache.get(database_url)
    if session_factory is None:
        session_factory = async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
        _sessionmaker_cache[database_url] = session_factory
    return session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_sessionmaker()() as session:
        yield session
