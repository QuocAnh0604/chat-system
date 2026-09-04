from datetime import datetime
from uuid import UUID

from sqlalchemy import exists, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from BE.models.conservation_members import ConversationMember, MemberRole
from BE.models.conservations import Conversation
from BE.models.messages import Message


class ConversationRepository:
    """Database operations for conversations and their memberships."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

    async def get_private_between(
        self, first_user_id: UUID, second_user_id: UUID
    ) -> Conversation | None:
        user_id_1, user_id_2 = sorted((first_user_id, second_user_id))
        statement = select(Conversation).where(
            Conversation.is_group.is_(False),
            Conversation.private_user_id_1 == user_id_1,
            Conversation.private_user_id_2 == user_id_2,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def create_private(
        self, first_user_id: UUID, second_user_id: UUID
    ) -> Conversation:
        user_id_1, user_id_2 = sorted((first_user_id, second_user_id))
        statement = (
            insert(Conversation)
            .values(
                is_group=False,
                private_user_id_1=user_id_1,
                private_user_id_2=user_id_2,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    Conversation.private_user_id_1,
                    Conversation.private_user_id_2,
                ],
                index_where=text("is_group = false"),
            )
            .returning(Conversation.id)
        )
        result = await self._session.execute(statement)
        conversation_id = result.scalar_one_or_none()
        if conversation_id is None:
            conversation = await self.get_private_between(first_user_id, second_user_id)
            if conversation is None:
                raise RuntimeError("Private conversation could not be created.")
        else:
            conversation = await self.get_by_id(conversation_id)
            if conversation is None:
                raise RuntimeError("Private conversation could not be loaded.")

        await self._session.execute(
            insert(ConversationMember)
            .values(
                [
                    {
                        "conversation_id": conversation.id,
                        "user_id": first_user_id,
                        "role": MemberRole.member,
                    },
                    {
                        "conversation_id": conversation.id,
                        "user_id": second_user_id,
                        "role": MemberRole.member,
                    },
                ]
            )
            .on_conflict_do_nothing(
                index_elements=[
                    ConversationMember.conversation_id,
                    ConversationMember.user_id,
                ]
            )
        )
        await self._session.flush()
        return conversation

    async def list_for_user(
        self, user_id: UUID
    ) -> list[tuple[Conversation, MemberRole]]:
        statement = (
            select(Conversation, ConversationMember.role)
            .join(
                ConversationMember,
                ConversationMember.conversation_id == Conversation.id,
            )
            .where(ConversationMember.user_id == user_id)
            .where(
                exists(
                    select(Message.id).where(Message.conversation_id == Conversation.id)
                )
            )
            .order_by(Conversation.updated_at.desc())
        )
        result = await self._session.execute(statement)
        return list(result.all())

    async def search_for_user(
        self, user_id: UUID, query: str, limit: int
    ) -> list[tuple[Conversation, MemberRole]]:
        """Find group conversations available to a member by their title."""
        statement = (
            select(Conversation, ConversationMember.role)
            .join(
                ConversationMember,
                ConversationMember.conversation_id == Conversation.id,
            )
            .where(
                ConversationMember.user_id == user_id,
                Conversation.is_group.is_(True),
                Conversation.title.like(f"%{query}%"),
            )
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return list(result.all())

    async def create_group(
        self, owner_id: UUID, title: str, member_ids: set[UUID]
    ) -> Conversation:
        conversation = Conversation(is_group=True, title=title, owner_id=owner_id)
        self._session.add(conversation)
        await self._session.flush()
        self._session.add_all(
            [
                ConversationMember(
                    conversation_id=conversation.id,
                    user_id=owner_id,
                    role=MemberRole.owner,
                ),
                *[
                    ConversationMember(
                        conversation_id=conversation.id,
                        user_id=user_id,
                        role=MemberRole.member,
                    )
                    for user_id in member_ids
                    if user_id != owner_id
                ],
            ]
        )
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def get_group(self, conversation_id: UUID) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id, Conversation.is_group.is_(True)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_member(
        self, conversation_id: UUID, user_id: UUID
    ) -> ConversationMember | None:
        result = await self._session.execute(
            select(ConversationMember).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_last_read(
        self,
        membership: ConversationMember,
        message_id: UUID,
        read_at: datetime,
    ) -> ConversationMember:
        membership.last_read_message_id = message_id
        membership.last_read_at = read_at
        await self._session.commit()
        await self._session.refresh(membership)
        return membership

    async def update_group(
        self, conversation: Conversation, values: dict[str, str | None]
    ) -> Conversation:
        for field, value in values.items():
            setattr(conversation, field, value)
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def add_member(
        self, conversation_id: UUID, user_id: UUID
    ) -> ConversationMember:
        membership = ConversationMember(
            conversation_id=conversation_id,
            user_id=user_id,
            role=MemberRole.member,
        )
        self._session.add(membership)
        await self._session.commit()
        await self._session.refresh(membership)
        return membership

    async def remove_member(self, membership: ConversationMember) -> None:
        await self._session.delete(membership)
        await self._session.commit()

    async def delete_group(self, conversation: Conversation) -> None:
        await self._session.delete(conversation)
        await self._session.commit()
