# Database Design

## Overview

Current architecture:

```text
FastAPI
  ↓
Service
  ↓
Repository
  ↓
PostgreSQL
```

Redis is used for recent-message caching and TTL-based online presence tracking.

## User

Stores user account information.

| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| username | String(50) | Unique username |
| display_name | String(100) | User display name |
| email | String(255) | Unique email |
| password_hash | String(255) | Hashed password |
| avatar_url | String(500) | Avatar image, nullable |
| is_active | Boolean | Account status |
| created_at | Timestamp | Account creation time |
| updated_at | Timestamp | Last profile update time |
| last_seen_at | Timestamp | Last time the user was seen online, nullable |

Indexes:

- Unique index on `username`
- Unique index on `email`

## Conversation

Represents a private chat or group chat.

| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| is_group | Boolean | `false` = private, `true` = group |
| title | String(100) | Group name, nullable |
| avatar_url | String(500) | Group avatar, nullable |
| owner_id | UUID | Group owner, nullable; `SET NULL` when the user is deleted |
| private_user_id_1 | UUID | First private-chat participant, nullable for groups |
| private_user_id_2 | UUID | Second private-chat participant, nullable for groups |
| last_message_id | UUID | Latest message, nullable |
| created_at | Timestamp | Created time |
| updated_at | Timestamp | Last update time |

Private conversations have a unique partial index on:

```text
(private_user_id_1, private_user_id_2) WHERE is_group = false
```

## ConversationMember

Stores members of each conversation.

Composite primary key:

```text
(conversation_id, user_id)
```

| Field | Type | Description |
|---|---|---|
| conversation_id | UUID | Conversation |
| user_id | UUID | User |
| role | Enum | `owner`, `admin`, or `member` |
| joined_at | Timestamp | Join time |
| last_read_message_id | UUID | Last read message, nullable |
| last_read_at | Timestamp | Last read time, nullable |

## Message

Stores chat messages.

| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| conversation_id | UUID | Conversation |
| sender_id | UUID | Sender, nullable after user deletion |
| client_message_id | String(100) | Client idempotency key, nullable |
| reply_to_message_id | UUID | Reply target, nullable |
| content | Text | Message content or attachment URL |
| type | Enum | `text`, `image`, `file`, `video`, `audio`, or `sticker` |
| status | Enum | `sending`, `sent`, or `failed` |
| created_at | Timestamp | Sent time |
| edited_at | Timestamp | Edit time, nullable |

Indexes:

- `(conversation_id, created_at)` for message pagination
- Unique partial index on `(sender_id, client_message_id)` when `client_message_id` is not null

## Relationships

```text
User 1 ─── * Conversation       (owner)
User 1 ─── * Message             (sender)
User 1 ─── * ConversationMember

Conversation 1 ─── * Message
Conversation 1 ─── * ConversationMember
Conversation 1 ─── 1 last_message

Message 1 ─── * reply messages  (self-reference)
ConversationMember 1 ─── 1 last_read_message
```

Private conversations also reference their two participants through
`private_user_id_1` and `private_user_id_2`.

## Cascade Rules

### Conversation deleted

```text
→ delete ConversationMember
→ delete Message
→ clear related conversation references
```

### User deleted

```text
→ owner_id becomes NULL
→ Message.sender_id becomes NULL
→ delete ConversationMember rows for that user
→ delete RefreshToken rows for that user
→ delete private conversations referencing that user
```

### Message deleted

```text
→ reply_to_message_id becomes NULL
→ Conversation.last_message_id becomes NULL when applicable
→ ConversationMember.last_read_message_id becomes NULL
```

## Current Features Supported

- Register and login
- JWT access-token refresh
- Private chat
- Group chat and member management
- Bidirectional WebSocket messaging
- Message reply
- Message edit
- Message recall/delete
- File, image, and video upload
- Read receipts and unread counts
- Redis caching for recent messages with TTL eviction
- TTL-based online presence with client heartbeats

## Future Features

- Push notifications
- Typing indicator
- Production load testing and benchmark documentation
