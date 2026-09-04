import sys
from pathlib import Path

# Lấy đường dẫn thư mục cha (D:\Chat System) và thêm vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid5

from sqlalchemy import select

from BE.config.database import AsyncSessionLocal, engine
from BE.core.security import hash_password
from BE.models.conservation_members import ConversationMember, MemberRole
from BE.models.conservations import Conversation
from BE.models.messages import Message, MessageStatus, MessageType
from BE.models.users import User

SEED_NAMESPACE = UUID("b4e1c4ab-7f92-4c6c-b7e0-8f7c77e68d2a")
DEFAULT_PASSWORD = "SeedPassword123!"

USER_DATA = [
    ("nguyenminhanh", "Nguyễn Minh Anh", "nguyen.minhanh@example.com", "bg-indigo-500", True),
    ("lequochung", "Lê Quốc Hùng", "le.quochung@example.com", "bg-purple-500", False),
    ("phamthuha", "Phạm Thu Hà", "pham.thuha@example.com", "bg-pink-500", True),
    ("vothanhtung", "Võ Thanh Tùng", "vo.thanhtung@example.com", "bg-amber-500", False),
    ("hoanglananh", "Hoàng Lan Anh", "hoang.lananh@example.com", "bg-emerald-500", False),
    ("dinhvannam", "Đinh Văn Nam", "dinh.vannam@example.com", "bg-indigo-500", False),
    ("buithiyen", "Bùi Thị Yến", "bui.thiyen@example.com", "bg-red-500", False),
]

PRIVATE_CONVERSATIONS = [
    ("private-1-2", 0, 1),
    ("private-1-3", 0, 2),
    ("private-1-4", 0, 3),
    ("private-1-5", 0, 4),
    ("private-1-6", 0, 5),
    ("private-1-7", 0, 6),
]

MOCK_MESSAGES = [
    ("message-1", 1, "them", "Chào bạn! Bạn có khỏe không?", "10:00"),
    ("message-2", 0, "me", "Mình khỏe, cảm ơn bạn! Còn bạn?", "10:02"),
    ("message-3", 1, "them", "Mình cũng ổn. Dạo này bận không?", "10:05"),
    ("message-4", 0, "me", "Cũng bình thường thôi 😊", "10:06"),
    ("message-5", 1, "them", "Tối nay đi ăn không bạn? Mình muốn thử nhà hàng mới khai trương.", "10:08"),
    ("message-6", 0, "me", "Nghe hay đó! Mấy giờ bạn rảnh?", "10:09"),
    ("message-7", 1, "them", "Khoảng 7h tối được không?", "10:10"),
    ("message-8", 0, "me", "OK được, mình sẽ đến!", "10:11"),
    ("message-9", 1, "them", "Tuyệt! Hẹn gặp bạn tối nay nhé 😄", "10:12"),
]

PREVIEW_MESSAGES = [
    ("message-preview-3", 2, "OK, mình sẽ gửi file cho bạn nhé"),
    ("message-preview-4", 0, "Bạn đã xem phim Dune 3 chưa?"),
    ("message-preview-5", 0, "Cảm ơn bạn nhiều lắm nha!"),
    ("message-preview-6", 0, "Hẹn gặp lại bạn nhé 👋"),
    ("message-preview-7", 0, "Chúc bạn ngủ ngon! 🌙"),
    ("message-preview-group", 0, "Meeting lúc 3h chiều nha mn"),
]


def seed_id(value: str) -> UUID:
    return uuid5(SEED_NAMESPACE, value)


async def get_or_create_user(
    session, username: str, display_name: str, email: str, avatar_url: str | None
) -> User:
    user = await session.scalar(select(User).where(User.username == username))
    if user is not None:
        return user

    user = User(
        id=seed_id(f"user:{username}"),
        username=username,
        display_name=display_name,
        email=email,
        password_hash=hash_password(DEFAULT_PASSWORD),
        avatar_url=avatar_url,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


async def get_or_create_private_conversation(
    session, first_user: User, second_user: User
) -> Conversation:
    user_id_1, user_id_2 = sorted((first_user.id, second_user.id))
    conversation = await session.scalar(
        select(Conversation).where(
            Conversation.private_user_id_1 == user_id_1,
            Conversation.private_user_id_2 == user_id_2,
        )
    )
    if conversation is not None:
        return conversation

    conversation = Conversation(
        id=seed_id(f"conversation:private:{first_user.username}:{second_user.username}"),
        is_group=False,
        private_user_id_1=user_id_1,
        private_user_id_2=user_id_2,
    )
    session.add(conversation)
    await session.flush()
    await add_member(session, conversation, first_user, MemberRole.member)
    await add_member(session, conversation, second_user, MemberRole.member)
    return conversation


async def get_or_create_group(session, users: list[User]) -> Conversation:
    conversation = await session.scalar(
        select(Conversation).where(
            Conversation.is_group.is_(True), Conversation.title == "Dev Team"
        )
    )
    if conversation is None:
        conversation = Conversation(
            id=seed_id("conversation:group:dev-team"),
            is_group=True,
            title="Dev Team",
            owner_id=users[0].id,
        )
        session.add(conversation)
        await session.flush()

    for index, user in enumerate(users):
        await add_member(
            session,
            conversation,
            user,
            MemberRole.owner if index == 0 else MemberRole.member,
        )
    return conversation


async def add_member(session, conversation, user, role: MemberRole) -> None:
    member = await session.scalar(
        select(ConversationMember).where(
            ConversationMember.conversation_id == conversation.id,
            ConversationMember.user_id == user.id,
        )
    )
    if member is None:
        session.add(
            ConversationMember(
                conversation_id=conversation.id,
                user_id=user.id,
                role=role,
            )
        )
        await session.flush()


async def add_mock_messages(session, conversation: Conversation, users: list[User]) -> None:
    current_time = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0)
    last_message = None
    for index, (message_key, sender_index, _side, content, _display_time) in enumerate(MOCK_MESSAGES):
        message = await session.scalar(select(Message).where(Message.id == seed_id(message_key)))
        if message is None:
            message = Message(
                id=seed_id(message_key),
                conversation_id=conversation.id,
                sender_id=users[sender_index].id,
                content=content,
                type=MessageType.text,
                status=MessageStatus.sent,
                created_at=current_time + timedelta(minutes=index * 2),
            )
            session.add(message)
            await session.flush()
        last_message = message

    if last_message is not None:
        conversation.last_message_id = last_message.id
        await session.flush()


async def add_preview_message(
    session, conversation: Conversation, sender: User, message_key: str, content: str
) -> None:
    message = await session.scalar(select(Message).where(Message.id == seed_id(message_key)))
    if message is None:
        message = Message(
            id=seed_id(message_key),
            conversation_id=conversation.id,
            sender_id=sender.id,
            content=content,
            type=MessageType.text,
            status=MessageStatus.sent,
        )
        session.add(message)
        await session.flush()
    conversation.last_message_id = message.id
    await session.flush()


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        try:
            users = [
                await get_or_create_user(
                    session,
                    username,
                    display_name,
                    email,
                    None,
                )
                for username, display_name, email, _color, _online in USER_DATA
            ]

            private_conversations = [
                await get_or_create_private_conversation(session, users[first], users[second])
                for _key, first, second in PRIVATE_CONVERSATIONS
            ]
            group_conversation = await get_or_create_group(session, users[:3])
            await add_mock_messages(session, private_conversations[0], users[:2])
            for conversation, (message_key, sender_index, content) in zip(
                private_conversations[1:], PREVIEW_MESSAGES[:5], strict=True
            ):
                await add_preview_message(session, conversation, users[sender_index], message_key, content)
            await add_preview_message(
                session,
                group_conversation,
                users[0],
                PREVIEW_MESSAGES[-1][0],
                PREVIEW_MESSAGES[-1][2],
            )

            await session.commit()
            print(f"Seeded {len(users)} users and {len(private_conversations) + 1} conversations.")
            print("Seed login password for every user:", DEFAULT_PASSWORD)
        except Exception:
            await session.rollback()
            raise
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
