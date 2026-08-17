from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from BE.config.database import get_db
from BE.core.dependencies import get_current_user
from BE.models.users import User
from BE.repositories.conversation_repository import ConversationRepository
from BE.repositories.message_repository import MessageRepository
from BE.schemas.messages import (
    MessageReadUpdate,
    ReadStatusResponse,
    UnreadCountResponse,
)
from BE.services.read_status_service import (
    ReadAccessError,
    ReadConversationNotFoundError,
    ReadMessageNotFoundError,
    ReadStatusService,
)
from BE.websocket.manager import connection_manager

router = APIRouter(prefix="/conversations/{conversation_id}", tags=["Read Status"])
CurrentUser = Annotated[User, Depends(get_current_user)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


def _service(session: AsyncSession) -> ReadStatusService:
    return ReadStatusService(
        ConversationRepository(session), MessageRepository(session), connection_manager
    )


@router.patch("/read", response_model=ReadStatusResponse)
async def mark_message_as_read(
    conversation_id: UUID,
    payload: MessageReadUpdate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ReadStatusResponse:
    """Advance the authenticated user's read cursor for a conversation."""
    try:
        return await _service(session).mark_as_read(
            conversation_id, current_user.id, payload.message_id
        )
    except (ReadConversationNotFoundError, ReadMessageNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ReadAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.get("/unread-count", response_model=UnreadCountResponse)
async def count_unread_messages(
    conversation_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> UnreadCountResponse:
    """Count unread messages from other users after the read cursor."""
    try:
        count = await _service(session).count_unread(conversation_id, current_user.id)
    except ReadConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ReadAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return UnreadCountResponse(count=count)
