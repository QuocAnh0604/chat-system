import uuid
from dataclasses import dataclass
from pathlib import Path

import anyio
from fastapi import HTTPException, UploadFile, status

from BE.config.settings import ATTACHMENT_DIR, UPLOAD_DIR
from BE.models.messages import MessageType

MAX_AVATAR_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_FILE_SIZE = 25 * 1024 * 1024
MAX_VIDEO_SIZE = 100 * 1024 * 1024
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}


@dataclass(frozen=True)
class StoredAttachment:
    url: str
    path: Path


class UploadService:
    """Validate and persist files outside of the database layer."""

    async def save_avatar(self, file: UploadFile) -> str:
        content_type = file.content_type or ""
        extension = Path(file.filename or "").suffix.lower()
        if (
            not content_type.startswith("image/")
            or extension not in ALLOWED_IMAGE_EXTENSIONS
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Avatar must be a supported image file.",
            )

        await anyio.to_thread.run_sync(
            lambda: UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        )
        filename = f"{uuid.uuid4()}{extension}"
        destination = UPLOAD_DIR / filename
        total_size = 0

        try:
            async with await anyio.open_file(destination, "wb") as output_file:
                while chunk := await file.read(1024 * 1024):
                    total_size += len(chunk)
                    if total_size > MAX_AVATAR_SIZE:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Avatar must not exceed 5 MB.",
                        )
                    await output_file.write(chunk)
        except HTTPException:
            await self._remove_file(destination)
            raise
        except OSError as exc:
            await self._remove_file(destination)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Avatar could not be saved.",
            ) from exc
        finally:
            await file.close()

        return f"/static/uploads/{filename}"

    async def delete_by_url(self, url: str | None) -> None:
        if not url or not url.startswith("/static/uploads/"):
            return
        await self._remove_file(UPLOAD_DIR / Path(url).name)

    async def save_attachment(
        self, file: UploadFile, message_type: MessageType
    ) -> StoredAttachment:
        """Validate and persist a chat attachment outside the public static path."""
        extension = Path(file.filename or "").suffix.lower()
        content_type = file.content_type or ""
        max_size = self._validate_attachment_type(
            message_type, content_type, extension
        )
        await anyio.to_thread.run_sync(
            lambda: ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)
        )
        filename = f"{uuid.uuid4()}{extension}"
        destination = ATTACHMENT_DIR / filename
        await self._write_file(file, destination, max_size, "Attachment")
        return StoredAttachment(url=f"/attachments/{filename}", path=destination)

    async def get_attachment_path(self, url: str) -> Path | None:
        """Resolve an internal attachment URL to a local file path safely."""
        prefix = "/attachments/"
        if not url.startswith(prefix):
            return None
        filename = url.removeprefix(prefix)
        if not filename or filename != Path(filename).name:
            return None
        path = ATTACHMENT_DIR / filename
        if not await anyio.to_thread.run_sync(path.is_file):
            return None
        return path

    async def delete_attachment(self, url: str | None) -> None:
        if not url or not url.startswith("/attachments/"):
            return
        await self._remove_file(ATTACHMENT_DIR / Path(url).name)

    @staticmethod
    def _validate_attachment_type(
        message_type: MessageType, content_type: str, extension: str
    ) -> int:
        if not extension:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attachment must have a file extension.",
            )
        if message_type == MessageType.image:
            if (
                not content_type.startswith("image/")
                or extension not in ALLOWED_IMAGE_EXTENSIONS
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Attachment must be a supported image file.",
                )
            return MAX_IMAGE_SIZE
        if message_type == MessageType.video:
            if (
                not content_type.startswith("video/")
                or extension not in ALLOWED_VIDEO_EXTENSIONS
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Attachment must be a supported video file.",
                )
            return MAX_VIDEO_SIZE
        if message_type == MessageType.file and content_type:
            return MAX_FILE_SIZE
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported attachment type.",
        )

    async def _write_file(
        self, file: UploadFile, destination: Path, max_size: int, label: str
    ) -> None:
        total_size = 0
        try:
            async with await anyio.open_file(destination, "wb") as output_file:
                while chunk := await file.read(1024 * 1024):
                    total_size += len(chunk)
                    if total_size > max_size:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"{label} exceeds its maximum allowed size.",
                        )
                    await output_file.write(chunk)
        except HTTPException:
            await self._remove_file(destination)
            raise
        except OSError as exc:
            await self._remove_file(destination)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{label} could not be saved.",
            ) from exc
        finally:
            await file.close()

    @staticmethod
    async def _remove_file(path: Path) -> None:
        if await anyio.to_thread.run_sync(path.exists):
            await anyio.to_thread.run_sync(path.unlink)
