"""
Shared fixtures for the provisioning test suite. Only test files that request
`provisioning_db` are affected — it is NOT autouse, so it can't clobber the
storage tests' own DeploymentConfig handling.

Requires a real Postgres reachable at TEST_DATABASE_URL (defaults to a
throwaway local instance — see the plan / test docstrings for how to start
one: `docker run -d --rm -e POSTGRES_PASSWORD=test -e POSTGRES_DB=cr8_test
-p 55432:5432 postgres:16-alpine`, then `alembic upgrade head` with
DATABASE_URL pointed at it).
"""

import os

import pytest

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:test@localhost:55432/cr8_test"
)

_TABLES = [
    "teardown_intents", "instance_user_sessions", "provisioned_instances",
    "provisioning_events", "fast_launch_machines",
]


@pytest.fixture
async def provisioning_db():
    """Points DeploymentConfig/db.engine at the test Postgres for the duration
    of one test, truncates the provisioning tables first for isolation, and
    resets everything back to a clean singleton state afterward."""
    import app.db.engine as db_engine
    from app.services.config import DeploymentConfig

    prev_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    DeploymentConfig.reset()
    db_engine._engine = None
    db_engine._session_factory = None

    from sqlalchemy import text

    engine = db_engine.get_engine()
    async with engine.begin() as conn:
        for table in _TABLES:
            await conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))

    yield

    await db_engine.get_engine().dispose()
    db_engine._engine = None
    db_engine._session_factory = None
    DeploymentConfig.reset()
    if prev_database_url is not None:
        os.environ["DATABASE_URL"] = prev_database_url
    else:
        os.environ.pop("DATABASE_URL", None)
