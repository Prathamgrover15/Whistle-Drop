from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_moderator
from app.models import Moderator
from app.schemas import ModeratorLogin, TokenResponse, ModeratorCreate
from app.security import verify_password, create_access_token, hash_password

router = APIRouter(prefix="/moderator", tags=["moderator-auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: ModeratorLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Moderator).where(Moderator.username == payload.username))
    moderator = result.scalar_one_or_none()

    # Same error for "no such user" and "wrong password" so the API
    # doesn't leak which usernames exist.
    if moderator is None or not verify_password(payload.password, moderator.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(subject=str(moderator.id))
    return TokenResponse(access_token=token)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_moderator(
    payload: ModeratorCreate,
    db: AsyncSession = Depends(get_db),
    _: Moderator = Depends(get_current_moderator),  # must already be a logged-in moderator
):
    """
    Deliberately locked behind an existing moderator's token -- there's
    no public sign-up for moderator accounts. The very first moderator
    is created with scripts/seed_moderator.py instead.
    """
    existing = await db.execute(select(Moderator.id).where(Moderator.username == payload.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    moderator = Moderator(username=payload.username, hashed_password=hash_password(payload.password))
    db.add(moderator)
    await db.commit()

    token = create_access_token(subject=str(moderator.id))
    return TokenResponse(access_token=token)
