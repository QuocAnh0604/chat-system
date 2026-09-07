"""Application settings loaded from the project environment file."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL: str | None = os.getenv("DATABASE_URL")
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _resolve_path(value: str) -> Path:
    """Resolve an upload path relative to the project root when necessary."""
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


upload_dir_value: str = os.getenv("UPLOAD_DIR", "static/uploads")
UPLOAD_DIR = _resolve_path(upload_dir_value)
ATTACHMENT_DIR = UPLOAD_DIR / "attachments"
