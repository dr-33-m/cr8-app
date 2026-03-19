"""
Async SQLAlchemy engine and session factory for PostgreSQL.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.services.config import DeploymentConfig

_engine = None
_session_factory = None


def get_engine():
    """Get or create the async SQLAlchemy engine (singleton)."""
    global _engine
    if _engine is None:
        config = DeploymentConfig.get()
        _engine = create_async_engine(
            config.DATABASE_URL,
            echo=False,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory (singleton)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
        )
    return _session_factory


async def get_db():
    """FastAPI dependency that yields an async DB session."""
    factory = get_session_factory()
    async with factory() as session:
        yield session
