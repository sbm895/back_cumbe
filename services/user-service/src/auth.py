import bcrypt
import jwt
from datetime import datetime, timezone
from .config import settings

ALLOWED_ROLES = {"user", "publisher"}


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verify a plain password against a bcrypt hash."""
    if hashed_password is None:
        return False
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def normalize_role(role: str | None) -> str:
    """Return a valid application role, defaulting old/missing values to user."""
    if role in ALLOWED_ROLES:
        return role
    return "user"


def create_access_token(user_id: str, role: str = "user") -> str:
    """Create a JWT token with the user ID and role."""
    payload = {
        "sub": user_id,
        "role": normalize_role(role),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token


def verify_token(token: str) -> dict[str, str] | None:
    """Verify a JWT token and return its user payload, or None if invalid."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            return None
        return {
            "user_id": user_id,
            "role": normalize_role(payload.get("role")),
        }
    except jwt.InvalidTokenError:
        return None
