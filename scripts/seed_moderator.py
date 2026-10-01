"""
Create a moderator account directly against the database.

There is no public sign-up endpoint for moderators (see
app/routers/auth.py's /moderator/register, which requires an existing
moderator token). This script is how you create the very first one.

Usage:
    python -m scripts.seed_moderator alice "a-strong-password"
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.models import Moderator
from app.security import hash_password


async def create_moderator(username: str, password: str) -> None:
    async with AsyncSessionLocal() as db:
        moderator = Moderator(username=username, hashed_password=hash_password(password))
        db.add(moderator)
        await db.commit()
        print(f"Moderator '{username}' created.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a moderator account")
    parser.add_argument("username")
    parser.add_argument("password")
    args = parser.parse_args()
    asyncio.run(create_moderator(args.username, args.password))
