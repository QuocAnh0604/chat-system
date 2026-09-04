from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from BE.config.database import get_db
from BE.core.dependencies import get_current_user
from BE.models.users import User
from BE.repositories.conversation_repository import ConversationRepository
from BE.repositories.message_repository import MessageRepository
from BE.repositories.user_repository import UserRepository
from BE.schemas.messages import (
    MessageCreate,
    LazyMessageCreate,
    MessagePageResponse,
    MessageResponse,
    MessageUpdate,
)
from BE.models.messages import MessageType
from BE.services.message_service import (
    AttachmentNotFoundError,
    MessageAccessError,
    MessageConversationNotFoundError,
    MessageCursorError,
    InvalidMessageContentError,
    MessageEditPermissionError,
    MessageDeletePermissionError,
    MessageNotFoundError,
    MessageTargetNotFoundError,
    MessageService,
)
from BE.websocket.manager import connection_manager
from BE.services.upload_service import UploadService

router = APIRouter(
    prefix="/conversations/{conversation_id}/messages", tags=["Messages"]
)
lazy_router = APIRouter(prefix="/messages", tags=["Messages"])
CurrentUser = Annotated[User, Depends(get_current_user)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


def _service(session: AsyncSession) -> MessageService:
    return MessageService(
        MessageRepository(session),
        ConversationRepository(session),
        connection_manager,
        UploadService(),
        UserRepository(session),
    )


@lazy_router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message_to_user(
    payload: LazyMessageCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> MessageResponse:
    """Create a private conversation only when its first message is sent."""
    try:
        message = await _service(session).send_message_to_user(
            current_user.id, MessageCreate(content=payload.content), payload.target_user_id
        )
    except MessageTargetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except InvalidMessageContentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return MessageResponse.model_validate(message)


@router.get("", response_model=MessagePageResponse)
async def get_messages(
    conversation_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
    last_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> MessagePageResponse:
    """Return messages newest first, using the previous page's last ID as cursor."""
    try:
        return await _service(session).get_messages(
            conversation_id, current_user.id, last_id, limit
        )
    except MessageConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except MessageAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except MessageCursorError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: UUID,
    payload: MessageCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> MessageResponse:
    """Persist a text message and notify connected conversation members."""
    try:
        message = await _service(session).send_message(
            conversation_id, current_user.id, payload
        )
    except MessageConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except MessageAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except InvalidMessageContentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return MessageResponse.model_validate(message)


@router.post(
    "/images", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
async def upload_image(
    conversation_id: UUID,
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentUser,
    session: DatabaseSession,
) -> MessageResponse:
    """Upload an image and create its message in one transaction flow."""
    try:
        message = await _service(session).send_attachment(
            conversation_id, current_user.id, file, MessageType.image
        )
    except MessageConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except MessageAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return MessageResponse.model_validate(message)


@router.post(
    "/files", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
async def upload_file(
    conversation_id: UUID,
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentUser,
    session: DatabaseSession,
) -> MessageResponse:
    """Upload a file and create its message in one transaction flow."""
    try:
        message = await _service(session).send_attachment(
            conversation_id, current_user.id, file, MessageType.file
        )
    except MessageConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except MessageAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return MessageResponse.model_validate(message)


@router.post(
    "/videos", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
async def upload_video(
    conversation_id: UUID,
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentUser,
    session: DatabaseSession,
) -> MessageResponse:
    """Upload a video and create its message in one transaction flow."""
    try:
        message = await _service(session).send_attachment(
            conversation_id, current_user.id, file, MessageType.video
        )
    except MessageConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except MessageAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return MessageResponse.model_validate(message)


@router.get("/{message_id}/attachment", response_class=FileResponse)
async def download_attachment(
    conversation_id: UUID,
    message_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> FileResponse:
    """Download an attachment after checking conversation membership."""
    try:
        path = await _service(session).get_attachment(
            conversation_id, current_user.id, message_id
        )
    except (MessageConversationNotFoundError, MessageNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except MessageAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except AttachmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return FileResponse(path=path, filename=path.name)


@router.post(
    "/{message_id}/replies",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reply_to_message(
    conversation_id: UUID,
    message_id: UUID,
    payload: MessageCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> MessageResponse:
    """Persist a reply to a message in the same conversation."""
    try:
        message = await _service(session).reply_to_message(
            conversation_id, current_user.id, message_id, payload
        )
    except (MessageConversationNotFoundError, MessageNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except MessageAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except InvalidMessageContentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return MessageResponse.model_validate(message)


@router.patch("/{message_id}", response_model=MessageResponse)
async def edit_message(
    conversation_id: UUID,
    message_id: UUID,
    payload: MessageUpdate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> MessageResponse:
    """Edit a message sent by the authenticated user."""
    try:
        message = await _service(session).edit_message(
            conversation_id, current_user.id, message_id, payload
        )
    except (MessageConversationNotFoundError, MessageNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (MessageAccessError, MessageEditPermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except InvalidMessageContentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return MessageResponse.model_validate(message)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    conversation_id: UUID,
    message_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> None:
    """Delete a message sent by the authenticated user."""
    try:
        await _service(session).delete_message(
            conversation_id, current_user.id, message_id
        )
    except (MessageConversationNotFoundError, MessageNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (MessageAccessError, MessageDeletePermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
