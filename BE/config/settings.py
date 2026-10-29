"""Application settings loaded from the project environment file."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL: str | None = os.getenv("DATABASE_URL")
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
JWT_SECRET_KEY: str | None = os.getenv("JWT_SECRET_KEY")
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
APP_ENV: str = os.getenv("APP_ENV", "development").lower()
PRESENCE_TTL_SECONDS = 30
HEARTBEAT_INTERVAL_SECONDS = 10
WS_AUTH_TIMEOUT_SECONDS = 5
WS_MAX_PENDING_AUTHENTICATIONS = 200
WS_SEND_TIMEOUT_SECONDS = 5
MESSAGE_CACHE_ENABLED = os.getenv("MESSAGE_CACHE_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
MESSAGE_CACHE_SIZE = int(os.getenv("MESSAGE_CACHE_SIZE", "50"))
MESSAGE_CACHE_TTL_SECONDS = int(os.getenv("MESSAGE_CACHE_TTL_SECONDS", "300"))

if MESSAGE_CACHE_SIZE < 1 or MESSAGE_CACHE_TTL_SECONDS < 1:
    raise ValueError("Message cache size and TTL must be positive integers.")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be configured in the environment.")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY must be configured in the environment.")
if APP_ENV != "development" and len(JWT_SECRET_KEY) < 32:
    raise ValueError("JWT_SECRET_KEY must be at least 32 characters outside development.")
if "*" in CORS_ORIGINS:
    raise ValueError("CORS_ORIGINS cannot contain '*' when credentials are enabled.")


def _resolve_path(value: str) -> Path:
    """Resolve an upload path relative to the project root when necessary."""
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


upload_dir_value: str = os.getenv("UPLOAD_DIR", "static/uploads")
UPLOAD_DIR = _resolve_path(upload_dir_value)
ATTACHMENT_DIR = UPLOAD_DIR / "attachments"
