from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
import enum
from schemas.users import UserResponse
class MemberRole(str, enum.Enum):
    admin = "admin"
    member = "member"

class ConversationMemberBase(BaseModel):
    conversation_id: UUID
    user_id: UUID

    role: MemberRole
    joined_at: datetime

class ConversationMemberCreate(BaseModel):
    conversation_id: UUID
    user_id: UUID

class ConversationMemberResponse(ConversationMemberBase):
    user: UserResponse