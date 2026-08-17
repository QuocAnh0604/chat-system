import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Return a one-way bcrypt hash for a plaintext password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Safely verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: uuid.UUID) -> str:
    """Create a short-lived JWT used to authorize API requests."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return _encode_token({"sub": str(user_id), "type": "access", "exp": expires_at})


def create_refresh_token(user_id: uuid.UUID, token_id: uuid.UUID) -> tuple[str, datetime]:
    """Create a refresh JWT and return it with its expiration timestamp."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token = _encode_token(
        {
            "sub": str(user_id),
            "jti": str(token_id),
            "type": "refresh",
            "exp": expires_at,
        }
    )
    return token, expires_at


def decode_token(token: str, expected_type: str) -> dict[str, str]:
    """Decode a JWT and ensure that it is being used for its intended purpose."""
    try:
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token.") from exc

    if payload.get("type") != expected_type or not payload.get("sub"):
        raise ValueError("Invalid token type.")
    return payload


def _encode_token(payload: dict[str, object]) -> str:
    return jwt.encode(payload, _get_jwt_secret(), algorithm=JWT_ALGORITHM)


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY must be configured in the environment.")
    return secret
