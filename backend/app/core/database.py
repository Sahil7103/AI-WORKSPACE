"""
Database connection and session management.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


def _build_async_database_url(database_url: str) -> str:
    """Normalize sync database URLs to async SQLAlchemy URLs."""
    if database_url.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if database_url.startswith("sqlite://"):
        return database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return database_url


database_url = settings.sqlalchemy_db_url or settings.database_url

# Create async engine for async support
engine = create_async_engine(
    _build_async_database_url(database_url),
    echo=settings.debug,
    poolclass=NullPool,
)

# Create session factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Base class for all models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency to get a database session.
    Usage: async def my_route(db: AsyncSession = Depends(get_db))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    # Import models before create_all so SQLAlchemy knows every table.
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
