export interface Conversation {
  id: number | string;
  conversationId?: string;
  targetUserId?: string;
  name: string;
  initials: string;
  color: string;
  lastMessage: string;
  time: string;
  unread: number;
  online: boolean;
  status?: string;
}

export interface Message {
  id: number;
  from: "me" | "them";
  text: string;
  time: string;
  seen?: boolean;
}