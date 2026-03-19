"""
Generate invite tokens for the private beta.

Usage (run from backend/cr8_engine/):
    python -m scripts.generate_invite
    python -m scripts.generate_invite --count 5 --created-by "thamsanqa"
    python -m scripts.generate_invite --expiry-days 14
"""

import argparse
import asyncio
import os
import secrets
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.models import Invitation


async def generate_tokens(count: int, created_by: str | None, expiry_days: int):
    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        tokens = []
        for _ in range(count):
            token = secrets.token_hex(16)
            invitation = Invitation(
                token=token,
                created_by=created_by,
                expires_at=datetime.now(timezone.utc) + timedelta(days=expiry_days),
            )
            session.add(invitation)
            tokens.append(token)

        await session.commit()

    await engine.dispose()

    print(f"\nGenerated {count} invite token(s) (expires in {expiry_days} days):\n")
    for t in tokens:
        print(f"  {t}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Generate invite tokens for cr8 private beta")
    parser.add_argument("--count", type=int, default=1, help="Number of tokens to generate (default: 1)")
    parser.add_argument("--created-by", type=str, default=None, help="Who created these tokens (admin note)")
    parser.add_argument("--expiry-days", type=int, default=7, help="Days until token expires (default: 7)")
    args = parser.parse_args()

    asyncio.run(generate_tokens(args.count, args.created_by, args.expiry_days))


if __name__ == "__main__":
    main()
