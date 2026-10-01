import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Moderator
from app.security import decode_access_token

bearer_scheme = HTTPBearer()


async def get_current_moderator(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Moderator:
    subject = decode_access_token(credentials.credentials)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    try:
        moderator_id = uuid.UUID(subject)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(Moderator).where(Moderator.id == moderator_id))
    moderator = result.scalar_one_or_none()
    if moderator is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Moderator account not found")

    return moderator
