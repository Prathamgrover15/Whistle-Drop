import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

CASE_CODE_PREFIX = "WD"


def generate_case_code() -> str:
    """
    secrets.token_urlsafe(18) gives 18 random bytes (144 bits of entropy)
    encoded as URL-safe base64. That's astronomically harder to guess
    than, say, a 6-digit tracking number -- brute forcing it is not
    practical.
    """
    return f"{CASE_CODE_PREFIX}-{secrets.token_urlsafe(18)}"


def hash_case_code(case_code: str) -> str:
    """
    SHA-256 is fine here (unlike passwords, case codes are already
    high-entropy random tokens, not something a human chose, so there's
    no dictionary/brute-force risk that would call for bcrypt/argon2).
    """
    return hashlib.sha256(case_code.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None
