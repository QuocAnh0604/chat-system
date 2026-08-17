# Database Design

## Overview

Current architecture:

Layered Architecture

FastAPI
↓
Service
↓
Repository
↓
PostgreSQL

---

# User

Store user account information.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| username | String(50) | Unique username |
| display_name | String(100) | User display name |
| email | String(255) | Unique email |
| password_hash | String(255) | Hashed password |
| avatar_url | String(500) | Avatar image |
| is_active | Boolean | Account status |
| created_at | Timestamp | Account creation time |

---

# Conversation

Represents a private chat or group chat.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| is_group | Boolean | false = private, true = group |
| title | String | Group name (nullable) |
| avatar_url | String | Group avatar |
| owner_id | UUID | Group owner |
| last_message_id | UUID | Latest message |
| created_at | Timestamp | Created time |
| updated_at | Timestamp | Last update |

---

# ConversationMember

Stores members of each conversation.

Composite Primary Key:

(conversation_id, user_id)

## Fields

| Field | Type | Description |
|-------|------|-------------|
| conversation_id | UUID | Conversation |
| user_id | UUID | User |
| role | owner/admin/member | Member role |
| joined_at | Timestamp | Join time |
| last_read_message_id | UUID | Last read message |
| last_read_at | Timestamp | Last read time |

---

# Message

Stores chat messages.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| conversation_id | UUID | Conversation |
| sender_id | UUID | Sender |
| reply_to_message_id | UUID | Reply target |
| content | Text | Message content |
| type | text/image/file/video/audio/sticker | Message type |
| status | sending/sent/failed | Delivery status |
| created_at | Timestamp | Sent time |
| edited_at | Timestamp | Edit time |

---

# Relationships

User

1 ---- * Conversation (owner)

User

1 ---- * Message (sender)

Conversation

1 ---- * Message

Conversation

1 ---- * ConversationMember

User

1 ---- * ConversationMember

Message

1 ---- 1 Conversation.last_message

Message

1 ---- * Reply Message

ConversationMember

1 ---- 1 Last Read Message

---

# Cascade Rules

Conversation deleted

→ delete ConversationMember

→ delete Message

User deleted

→ sender_id becomes NULL

→ owner_id becomes NULL

Message deleted

→ reply_to_message_id becomes NULL

→ last_message_id becomes NULL

→ last_read_message_id becomes NULL

---

# Current Features Supported

✅ Register

✅ Login

✅ Private Chat

✅ Group Chat

✅ Reply Message

✅ Read Receipt

Future Features

- Message Edit
- Message Recall
- File Upload
- Notification
- Online Status
- Typing Indicator