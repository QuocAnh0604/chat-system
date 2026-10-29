export interface User {
  id: string;
  username: string;
  email: string;
  display_name: string;
  avatar_url: string | null;
  is_active: boolean;
  created_at?: string;
}

export interface PresenceStatus {
  user_id: string;
  is_online: boolean;
  last_seen_at: string | null;
}

export type MessageType = "text" | "image" | "file" | "video" | "audio" | "sticker";
export type MessageStatus = "sending" | "sent" | "failed";

export interface ApiMessage {
  id: string;
  conversation_id: string;
  sender_id: string | null;
  reply_to_message_id: string | null;
  content: string | null;
  type: MessageType;
  status: MessageStatus;
  client_message_id: string | null;
  created_at: string;
  edited_at: string | null;
}

export interface MessagePage {
  messages: ApiMessage[];
  next_last_id: string | null;
}

export interface ConversationSummary {
  id: string;
  is_group: boolean;
  title: string | null;
  avatar_url: string | null;
  owner_id: string | null;
  created_at: string;
  updated_at: string;
  role: string;
  last_message: ApiMessage | null;
  unread_count: number;
  members: User[];
  presence: PresenceStatus[];
}

export interface Conversation {
  id: string;
  conversationId?: string;
  targetUserId?: string;
  name: string;
  initials: string;
  color: string;
  avatarUrl?: string | null;
  lastMessage: string;
  time: string;
  unread: number;
  online: boolean;
  lastSeenAt?: string | null;
  status?: string;
  members?: User[];
}

export type MessageDeliveryStatus = "sending" | "sent" | "failed";

export interface Message {
  id: string;
  conversationId: string;
  senderId: string | null;
  from: "me" | "them";
  text: string;
  time: string;
  status: MessageDeliveryStatus;
  clientMessageId?: string | null;
  seen?: boolean;
}
