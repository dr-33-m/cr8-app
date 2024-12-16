from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


# Create async engine
engine = create_async_engine(
    # Make sure this is an async-compatible URI (e.g., for PostgreSQL, use "postgresql+asyncpg://")
    settings.DATABASE_URI,
    echo=True,  # Set to False in production
    future=True
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# You can now use this engine and session for async database operations
async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
