from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PrivateConversationCreate(BaseModel):
    user_id: UUID


class GroupCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    member_ids: list[UUID] = Field(default_factory=list)


class GroupRename(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class GroupMemberAdd(BaseModel):
    user_id: UUID


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_group: bool
    title: str | None
    avatar_url: str | None
    owner_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(ConversationResponse):
    role: str
