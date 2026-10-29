from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from BE.config.database import get_db
from BE.core.dependencies import get_current_user
from BE.models.users import User
from BE.repositories.conversation_repository import ConversationRepository
from BE.repositories.message_repository import MessageRepository
from BE.repositories.user_repository import UserRepository
from BE.schemas.conservations import (
    ConversationListResponse,
    ConversationResponse,
    GroupCreate,
    GroupMemberAdd,
    GroupRename,
)
from BE.schemas.messages import MessageResponse
from BE.schemas.users import UserResponse
from BE.services.conversation_service import (
    ConversationService,
    ConversationUserNotFoundError,
    GroupNotFoundError,
    GroupMemberAlreadyExistsError,
    GroupMemberNotFoundError,
    GroupOwnerActionError,
    GroupPermissionError,
    InvalidGroupMembersError,
)
from BE.services.upload_service import UploadService
from BE.config.redis import redis_client
from BE.services.presence_service import PresenceService

router = APIRouter(prefix="/conversations", tags=["Conversations"])
CurrentUser = Annotated[User, Depends(get_current_user)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


def _service(session: AsyncSession) -> ConversationService:
    return ConversationService(ConversationRepository(session), UserRepository(session))


@router.get("/search", response_model=list[ConversationListResponse])
async def search_conversations(
    current_user: CurrentUser,
    session: DatabaseSession,
    q: Annotated[str, Query(min_length=1, max_length=100)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[ConversationListResponse]:
    """Search the current user's group conversations by name."""
    records = await _service(session).search_for_user(current_user.id, q, limit)
    return [
        ConversationListResponse(
            **ConversationResponse.model_validate(conversation).model_dump(),
            role=role.value,
        )
        for conversation, role in records
    ]


@router.patch("/{conversation_id}/group", response_model=ConversationResponse)
async def rename_group(
    conversation_id: UUID,
    payload: GroupRename,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ConversationResponse:
    """Rename a group as its owner or an admin."""
    try:
        conversation = await _service(session).rename_group(
            conversation_id, current_user.id, payload
        )
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except GroupPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return ConversationResponse.model_validate(conversation)


@router.post("/{conversation_id}/group/avatar", response_model=ConversationResponse)
async def change_group_avatar(
    conversation_id: UUID,
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ConversationResponse:
    """Upload and assign an avatar for a group managed by the current user."""
    upload_service = UploadService()
    avatar_url = await upload_service.save_avatar(file)
    try:
        conversation = await _service(session).change_group_avatar(
            conversation_id, current_user.id, avatar_url
        )
    except GroupNotFoundError as exc:
        await upload_service.delete_by_url(avatar_url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except GroupPermissionError as exc:
        await upload_service.delete_by_url(avatar_url)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return ConversationResponse.model_validate(conversation)


@router.post("/{conversation_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def add_group_member(
    conversation_id: UUID,
    payload: GroupMemberAdd,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> None:
    """Add an active user to a group as a member."""
    try:
        await _service(session).add_member(conversation_id, current_user.id, payload.user_id)
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConversationUserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except GroupMemberAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except GroupPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.delete("/{conversation_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_member(
    conversation_id: UUID,
    user_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> None:
    """Remove a non-owner member from a group."""
    try:
        await _service(session).remove_member(conversation_id, current_user.id, user_id)
    except (GroupNotFoundError, GroupMemberNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (GroupPermissionError, GroupOwnerActionError) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{conversation_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_group(
    conversation_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> None:
    """Leave a group when the current user is not its owner."""
    try:
        await _service(session).leave_group(conversation_id, current_user.id)
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (GroupPermissionError, GroupOwnerActionError) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.delete("/{conversation_id}/group", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    conversation_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> None:
    """Delete a group owned by the current user."""
    try:
        await _service(session).delete_group(conversation_id, current_user.id)
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except GroupPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/groups", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ConversationResponse:
    """Create a group conversation with the authenticated user as owner."""
    try:
        conversation = await _service(session).create_group(current_user.id, payload)
    except InvalidGroupMembersError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ConversationResponse.model_validate(conversation)


@router.get("", response_model=list[ConversationListResponse])
async def list_conversations(
    current_user: CurrentUser,
    session: DatabaseSession,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ConversationListResponse]:
    """List conversations in which the authenticated user is a member."""
    conversation_repository = ConversationRepository(session)
    user_repository = UserRepository(session)
    message_repository = MessageRepository(session)
    presence_service = PresenceService(user_repository, redis_client)
    records = await _service(session).list_for_user(
        current_user.id, offset=offset, limit=limit
    )
    summaries: list[ConversationListResponse] = []
    for conversation, role in records:
        member_ids = await conversation_repository.get_member_ids(conversation.id)
        members = await user_repository.get_by_ids(member_ids)
        membership = await conversation_repository.get_member(
            conversation.id, current_user.id
        )
        last_message = (
            await message_repository.get_by_id(conversation.last_message_id)
            if conversation.last_message_id is not None
            else None
        )
        last_read_message = (
            await message_repository.get_by_id(membership.last_read_message_id)
            if membership is not None and membership.last_read_message_id is not None
            else None
        )
        unread_count = await message_repository.count_unread(
            conversation.id, current_user.id, last_read_message
        )
        presence = await presence_service.get_statuses(members)
        summaries.append(
            ConversationListResponse(
                **ConversationResponse.model_validate(conversation).model_dump(),
                role=role.value,
                last_message=(
                    MessageResponse.model_validate(last_message)
                    if last_message is not None
                    else None
                ),
                unread_count=unread_count,
                members=[UserResponse.model_validate(member) for member in members],
                presence=presence,
            )
        )
    return summaries
