import bcrypt
import jwt
from datetime import datetime, timezone
from .config import settings


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verify a plain password against a bcrypt hash."""
    if hashed_password is None:
        return False
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    """Create a JWT token with the user ID."""
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token


def verify_token(token: str) -> str | None:
    """Verify a JWT token and return the user ID, or None if invalid."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        return user_id
    except jwt.InvalidTokenError:
        return None
