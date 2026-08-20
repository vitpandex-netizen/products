"""GH Scout — зависимости БД."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from core.config import settings

# Асинхронный движок (для FastAPI)
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """FastAPI dependency — асинхронная сессия БД."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Синхронный движок (для APScheduler и скриптов)
sync_engine = create_engine(settings.database_url_sync, echo=settings.debug)


def get_sync_session():
    """Синхронная сессия (для cron/скриптов)."""
    from sqlalchemy.orm import sessionmaker
    SyncSession = sessionmaker(bind=sync_engine)
    session = SyncSession()
    return session


async def init_db():
    """Создать таблицы при старте."""
    async with async_engine.begin() as conn:
        from core.models import Base
        await conn.run_sync(Base.metadata.create_all)