
from uuid import UUID

from BE.models.conservation_members import ConversationMember, MemberRole
from BE.models.conservations import Conversation
from BE.repositories.conversation_repository import ConversationRepository
from BE.repositories.user_repository import UserRepository
from BE.schemas.conservations import GroupCreate, GroupRename


class ConversationUserNotFoundError(Exception):
    """Raised when a requested conversation participant does not exist."""


class InvalidPrivateConversationError(Exception):
    """Raised when a private conversation request targets its creator."""


class InvalidGroupMembersError(Exception):
    """Raised when a group contains unknown or inactive members."""


class GroupNotFoundError(Exception):
    """Raised when a group conversation cannot be found."""


class GroupPermissionError(Exception):
    """Raised when a member lacks permission for a group action."""


class GroupMemberAlreadyExistsError(Exception):
    """Raised when an existing member is added to a group."""


class GroupMemberNotFoundError(Exception):
    """Raised when a requested group member does not exist."""


class GroupOwnerActionError(Exception):
    """Raised when an action would leave a group without its owner."""


class ConversationNotFoundError(Exception):
    """Raised when a requested conversation cannot be found."""


class ConversationAccessError(Exception):
    """Raised when a user is not a conversation member."""


class ConversationService:
    """Business operations for conversations and membership."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        user_repository: UserRepository,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._user_repository = user_repository

    async def create_private(
        self, creator_id: UUID, participant_id: UUID
    ) -> Conversation:
        if creator_id == participant_id:
            raise InvalidPrivateConversationError(
                "A private conversation requires a different user."
            )
        participant = await self._user_repository.get_by_id(participant_id)
        if participant is None or not participant.is_active:
            raise ConversationUserNotFoundError("Conversation user was not found.")

        existing = await self._conversation_repository.get_private_between(
            creator_id, participant_id
        )
        if existing is not None:
            return existing
        return await self._conversation_repository.create_private(
            creator_id, participant_id
        )

    async def list_for_user(
        self, user_id: UUID
    ) -> list[tuple[Conversation, MemberRole]]:
        return await self._conversation_repository.list_for_user(user_id)

    async def search_for_user(
        self, user_id: UUID, query: str, limit: int
    ) -> list[tuple[Conversation, MemberRole]]:
        return await self._conversation_repository.search_for_user(
            user_id, query, limit
        )

    async def ensure_member(self, conversation_id: UUID, user_id: UUID) -> None:
        conversation = await self._conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError("Conversation was not found.")
        membership = await self._conversation_repository.get_member(
            conversation_id, user_id
        )
        if membership is None:
            raise ConversationAccessError("You are not a member of this conversation.")

    async def create_group(self, owner_id: UUID, payload: GroupCreate) -> Conversation:
        member_ids = set(payload.member_ids)
        member_ids.add(owner_id)
        active_ids = await self._user_repository.get_active_ids(member_ids)
        if active_ids != member_ids:
            raise InvalidGroupMembersError(
                "Every group member must be an active user account."
            )
        return await self._conversation_repository.create_group(
            owner_id, payload.title, member_ids
        )

    async def rename_group(
        self, conversation_id: UUID, actor_id: UUID, payload: GroupRename
    ) -> Conversation:
        conversation, membership = await self._get_group_membership(
            conversation_id, actor_id
        )
        self._require_manager(membership)
        return await self._conversation_repository.update_group(
            conversation, {"title": payload.title}
        )

    async def change_group_avatar(
        self, conversation_id: UUID, actor_id: UUID, avatar_url: str
    ) -> Conversation:
        conversation, membership = await self._get_group_membership(
            conversation_id, actor_id
        )
        self._require_manager(membership)
        return await self._conversation_repository.update_group(
            conversation, {"avatar_url": avatar_url}
        )

    async def add_member(
        self, conversation_id: UUID, actor_id: UUID, user_id: UUID
    ) -> None:
        _, membership = await self._get_group_membership(conversation_id, actor_id)
        self._require_manager(membership)
        user = await self._user_repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise ConversationUserNotFoundError("Conversation user was not found.")
        existing_member = await self._conversation_repository.get_member(
            conversation_id, user_id
        )
        if existing_member is not None:
            raise GroupMemberAlreadyExistsError("User is already a group member.")
        await self._conversation_repository.add_member(conversation_id, user_id)

    async def remove_member(
        self, conversation_id: UUID, actor_id: UUID, user_id: UUID
    ) -> None:
        conversation, membership = await self._get_group_membership(
            conversation_id, actor_id
        )
        self._require_manager(membership)
        target_membership = await self._conversation_repository.get_member(
            conversation_id, user_id
        )
        if target_membership is None:
            raise GroupMemberNotFoundError("User is not a group member.")
        if target_membership.role == MemberRole.owner:
            raise GroupOwnerActionError("The group owner cannot be removed.")
        await self._conversation_repository.remove_member(target_membership)

    async def leave_group(self, conversation_id: UUID, actor_id: UUID) -> None:
        _, membership = await self._get_group_membership(conversation_id, actor_id)
        if membership.role == MemberRole.owner:
            raise GroupOwnerActionError(
                "The group owner cannot leave. Delete the group instead."
            )
        await self._conversation_repository.remove_member(membership)

    async def delete_group(self, conversation_id: UUID, actor_id: UUID) -> None:
        conversation, membership = await self._get_group_membership(
            conversation_id, actor_id
        )
        if membership.role != MemberRole.owner:
            raise GroupPermissionError("Only the group owner can delete the group.")
        await self._conversation_repository.delete_group(conversation)

    async def _get_group_membership(
        self, conversation_id: UUID, user_id: UUID
    ) -> tuple[Conversation, ConversationMember]:
        conversation = await self._conversation_repository.get_group(conversation_id)
        if conversation is None:
            raise GroupNotFoundError("Group conversation was not found.")
        membership = await self._conversation_repository.get_member(conversation_id, user_id)
        if membership is None:
            raise GroupPermissionError("You are not a member of this group.")
        return conversation, membership

    @staticmethod
    def _require_manager(membership: ConversationMember) -> None:
        if membership.role not in {MemberRole.owner, MemberRole.admin}:
            raise GroupPermissionError("Only a group owner or admin can do this.")
