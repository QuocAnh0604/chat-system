import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import authAPI from "../API/authAPI";
import conservationAPI from "../API/conservationAPI";
import messageAPI from "../API/messageAPI";
import userAPI from "../API/userAPI";
import { PRESENCE_POLL_INTERVAL_MS } from "../config";
import type {
  ApiMessage,
  Conversation,
  ConversationSummary,
  Message,
  PresenceStatus,
  User,
} from "../types/chat";
import { useChatSocket, type SocketEvent } from "../hooks/useChatSocket";
import ChatSidebar from "../COMPONENTS/chat/ChatSidebar";
import ChatWindow from "../COMPONENTS/chat/ChatWindow";

const colorPalette = [
  "bg-indigo-500",
  "bg-purple-500",
  "bg-pink-500",
  "bg-violet-500",
  "bg-amber-500",
  "bg-emerald-500",
  "bg-red-500",
];

const getInitials = (name: string): string => {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return "U";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return `${words[0][0]}${words[1][0]}`.toUpperCase();
};

const formatTime = (value?: string | null): string =>
  value
    ? new Date(value).toLocaleTimeString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

const formatLastMessage = (message: ApiMessage | null): string =>
  message?.content ?? (message ? `[${message.type}]` : "Chưa có tin nhắn");

const toMessage = (message: ApiMessage, currentUserId: string): Message => ({
  id: message.id,
  conversationId: message.conversation_id,
  senderId: message.sender_id,
  from: message.sender_id === currentUserId ? "me" : "them",
  text: message.content ?? `[${message.type}]`,
  time: formatTime(message.created_at),
  status: message.status,
  clientMessageId: message.client_message_id,
});

const toConversation = (
  summary: ConversationSummary,
  currentUserId: string,
  index: number,
): Conversation => {
  const otherMember = summary.members.find((member) => member.id !== currentUserId);
  const name = summary.is_group
    ? summary.title ?? "Nhóm chat"
    : otherMember?.display_name ?? otherMember?.username ?? "Người dùng";
  const otherPresence = otherMember
    ? summary.presence.find((item) => item.user_id === otherMember.id)
    : undefined;

  return {
    id: summary.id,
    conversationId: summary.id,
    targetUserId: undefined,
    name,
    initials: getInitials(name),
    color: colorPalette[index % colorPalette.length],
    avatarUrl: summary.is_group ? summary.avatar_url : otherMember?.avatar_url,
    lastMessage: formatLastMessage(summary.last_message),
    time: formatTime(summary.last_message?.created_at),
    unread: summary.unread_count,
    online: otherPresence?.is_online ?? false,
    lastSeenAt: otherPresence?.last_seen_at,
    status: summary.is_group ? "Nhóm" : undefined,
    members: summary.members,
  };
};

const toSearchUserConversation = (user: User, index: number): Conversation => ({
  id: `user:${user.id}`,
  targetUserId: user.id,
  name: user.display_name || user.username,
  initials: getInitials(user.display_name || user.username),
  color: colorPalette[index % colorPalette.length],
  avatarUrl: user.avatar_url,
  lastMessage: "Bắt đầu cuộc trò chuyện",
  time: "Mới",
  unread: 0,
  online: false,
  status: "Liên hệ trực tiếp",
});

const isApiMessage = (value: unknown): value is ApiMessage => {
  if (typeof value !== "object" || value === null) return false;
  const message = value as Partial<ApiMessage>;
  return typeof message.id === "string" && typeof message.conversation_id === "string";
};

interface PendingMessage {
  key: string;
  timer: number;
}

export default function ChatHomePage() {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [searchResults, setSearchResults] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messagesByConversation, setMessagesByConversation] = useState<Record<string, Message[]>>({});
  const [nextCursorByConversation, setNextCursorByConversation] = useState<Record<string, string | null>>({});
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [draft, setDraft] = useState("");
  const pendingRef = useRef(new Map<string, PendingMessage>());
  const { status: socketStatus, sendMessage, onEvent } = useChatSocket(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    navigate("/login");
  });

  const visibleConversations = query.trim() ? searchResults : conversations;
  const activeConversation = visibleConversations.find((item) => item.id === activeId) ?? null;
  const activeKey = activeConversation?.conversationId ?? (activeConversation?.targetUserId ? `user:${activeConversation.targetUserId}` : null);
  const activeMessages = activeKey ? messagesByConversation[activeKey] ?? [] : [];

  const applyPresence = useCallback((statuses: PresenceStatus[]) => {
    const byUserId = new Map(statuses.map((item) => [item.user_id, item]));
    const update = (items: Conversation[]) =>
      items.map((conversation) => {
        const status = conversation.targetUserId ? byUserId.get(conversation.targetUserId) : undefined;
        return status
          ? { ...conversation, online: status.is_online, lastSeenAt: status.last_seen_at }
          : conversation;
      });
    setConversations(update);
    setSearchResults(update);
  }, []);

  const loadPresence = useCallback(async () => {
    const userIds = [...conversations, ...searchResults]
      .map((item) => item.targetUserId)
      .filter((id): id is string => Boolean(id));
    const uniqueIds = [...new Set(userIds)];
    if (uniqueIds.length === 0) return;
    try {
      applyPresence(await userAPI.getPresence(uniqueIds));
    } catch {
      // Presence is best effort; the next poll retries it.
    }
  }, [applyPresence, conversations, searchResults]);

  useEffect(() => {
    const loadCurrentUser = async () => {
      try {
        const user = await userAPI.getMe();
        setCurrentUser(user);
      } catch {
        setError("Không thể tải thông tin người dùng.");
      }
    };
    void loadCurrentUser();
  }, []);

  useEffect(() => {
    if (!currentUser) return;
    const loadConversations = async () => {
      setLoadingConversations(true);
      try {
        const summaries = await conservationAPI.list();
        const mapped = summaries.map((summary, index) => toConversation(summary, currentUser.id, index));
        setConversations(mapped);
        setActiveId(mapped[0]?.id ?? null);
        setError(null);
      } catch {
        setError("Không thể tải danh sách hội thoại.");
      } finally {
        setLoadingConversations(false);
      }
    };
    void loadConversations();
  }, [currentUser]);

  useEffect(() => {
    const timer = window.setInterval(() => void loadPresence(), PRESENCE_POLL_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [loadPresence]);

  const loadMessages = useCallback(async (conversationId: string, older = false) => {
    setLoadingMessages(true);
    try {
      const cursor = older ? nextCursorByConversation[conversationId] ?? undefined : undefined;
      const page = await messageAPI.getMessages(conversationId, cursor);
      if (!currentUser) return;
      const incoming = page.messages.slice().reverse().map((message) => toMessage(message, currentUser.id));
      setMessagesByConversation((previous) => {
        const existing = previous[conversationId] ?? [];
        const combined = older ? [...incoming, ...existing] : incoming;
        return {
          ...previous,
          [conversationId]: [...new Map(combined.map((message) => [message.id, message])).values()],
        };
      });
      setNextCursorByConversation((previous) => ({ ...previous, [conversationId]: page.next_last_id }));
    } catch {
      setError("Không thể tải tin nhắn.");
    } finally {
      setLoadingMessages(false);
    }
  }, [currentUser, nextCursorByConversation]);

  useEffect(() => {
    const conversationId = activeConversation?.conversationId;
    if (conversationId && !messagesByConversation[conversationId]) {
      window.setTimeout(() => void loadMessages(conversationId), 0);
    }
  }, [activeConversation, loadMessages, messagesByConversation]);

  const replaceOptimisticMessage = useCallback((message: ApiMessage, clientMessageId: string, key: string) => {
    if (!currentUser) return;
    const actualKey = message.conversation_id;
    setMessagesByConversation((previous) => {
      const source = previous[key] ?? [];
      const replacement = toMessage(message, currentUser.id);
      const found = source.some((item) => item.clientMessageId === clientMessageId);
      const updated = found
        ? source.map((item) => (item.clientMessageId === clientMessageId ? replacement : item))
        : [...source, replacement];
      const next = { ...previous, [actualKey]: updated };
      if (key !== actualKey) delete next[key];
      return next;
    });
    setConversations((items) => items.map((item) => {
      if (item.id !== key && item.targetUserId !== message.sender_id) return item;
      return {
        ...item,
        id: actualKey,
        conversationId: actualKey,
        targetUserId: undefined,
        lastMessage: formatLastMessage(message),
        time: formatTime(message.created_at),
      };
    }));
    setSearchResults((items) => items.map((item) => {
      if (item.id !== key) return item;
      return { ...item, id: actualKey, conversationId: actualKey, targetUserId: undefined };
    }));
    setActiveId((previous) => (previous === key ? actualKey : previous));
  }, [currentUser]);

  const markFailed = useCallback((clientMessageId: string, key: string) => {
    setMessagesByConversation((previous) => ({
      ...previous,
      [key]: (previous[key] ?? []).map((message) =>
        message.clientMessageId === clientMessageId ? { ...message, status: "failed" } : message,
      ),
    }));
  }, []);

  const handleSocketEvent = useCallback((event: SocketEvent) => {
    if (!currentUser) return;
    if (event.event === "message.ack" && isApiMessage(event.message)) {
      const clientId = typeof event.client_message_id === "string" ? event.client_message_id : event.message.client_message_id;
      if (!clientId) return;
      const pending = pendingRef.current.get(clientId);
      if (pending) {
        window.clearTimeout(pending.timer);
        pendingRef.current.delete(clientId);
        replaceOptimisticMessage(event.message, clientId, pending.key);
      }
      return;
    }
    if (event.event === "message.created" && isApiMessage(event.message)) {
      const message = event.message;
      const uiMessage = toMessage(message, currentUser.id);
      setMessagesByConversation((previous) => {
        const existing = previous[message.conversation_id] ?? [];
        if (existing.some((item) => item.id === uiMessage.id || (uiMessage.clientMessageId && item.clientMessageId === uiMessage.clientMessageId))) {
          return previous;
        }
        return { ...previous, [message.conversation_id]: [...existing, uiMessage] };
      });
      setConversations((items) => items.map((item) => item.id === message.conversation_id
        ? { ...item, lastMessage: formatLastMessage(message), time: formatTime(message.created_at), unread: item.id === activeId ? 0 : item.unread + 1 }
        : item));
      return;
    }
    if (event.event === "presence.updated" && typeof event.user_id === "string") {
      applyPresence([{
        user_id: event.user_id,
        is_online: event.is_online === true,
        last_seen_at: typeof event.last_seen_at === "string" ? event.last_seen_at : null,
      }]);
    }
  }, [activeId, applyPresence, currentUser, replaceOptimisticMessage]);

  useEffect(() => {
    const unsubscribe = onEvent(handleSocketEvent);
    return () => {
      unsubscribe();
    };
  }, [handleSocketEvent, onEvent]);

  const fallbackSend = useCallback(async (conversation: Conversation, text: string, clientId: string, key: string) => {
    try {
      const message = conversation.targetUserId
        ? await messageAPI.sendMessageToUser(conversation.targetUserId, text, clientId)
        : conversation.conversationId
          ? await messageAPI.sendMessage(conversation.conversationId, text, clientId)
          : null;
      if (message) {
        const pending = pendingRef.current.get(clientId);
        if (pending) window.clearTimeout(pending.timer);
        pendingRef.current.delete(clientId);
        replaceOptimisticMessage(message, clientId, key);
      }
    } catch {
      pendingRef.current.delete(clientId);
      markFailed(clientId, key);
    }
  }, [markFailed, replaceOptimisticMessage]);

  const handleSend = useCallback(() => {
    const text = draft.trim();
    if (!text || !activeConversation || !currentUser) return;
    const clientId = crypto.randomUUID();
    const key = activeConversation.conversationId ?? `user:${activeConversation.targetUserId}`;
    const optimistic: Message = {
      id: `temp:${clientId}`,
      conversationId: activeConversation.conversationId ?? "",
      senderId: currentUser.id,
      from: "me",
      text,
      time: formatTime(new Date().toISOString()),
      status: "sending",
      clientMessageId: clientId,
    };
    setMessagesByConversation((previous) => ({ ...previous, [key]: [...(previous[key] ?? []), optimistic] }));
    setDraft("");
    const timer = window.setTimeout(() => {
      const pending = pendingRef.current.get(clientId);
      if (pending) void fallbackSend(activeConversation, text, clientId, key);
    }, 5000);
    pendingRef.current.set(clientId, { key, timer });
    const sent = sendMessage({
      conversation_id: activeConversation.conversationId,
      target_user_id: activeConversation.targetUserId,
      content: text,
      client_message_id: clientId,
    });
    if (!sent) {
      window.clearTimeout(timer);
      void fallbackSend(activeConversation, text, clientId, key);
    }
  }, [activeConversation, currentUser, draft, fallbackSend, sendMessage]);

  const handleRetry = useCallback((message: Message) => {
    if (!activeConversation || !message.clientMessageId) return;
    const key = activeConversation.conversationId ?? `user:${activeConversation.targetUserId}`;
    setMessagesByConversation((previous) => ({
      ...previous,
      [key]: (previous[key] ?? []).map((item) =>
        item.clientMessageId === message.clientMessageId ? { ...item, status: "sending" } : item,
      ),
    }));
    const timer = window.setTimeout(() => {
      const pending = pendingRef.current.get(message.clientMessageId as string);
      if (pending) void fallbackSend(activeConversation, message.text, message.clientMessageId as string, key);
    }, 5000);
    pendingRef.current.set(message.clientMessageId, { key, timer });
    const sent = sendMessage({
      conversation_id: activeConversation.conversationId,
      target_user_id: activeConversation.targetUserId,
      content: message.text,
      client_message_id: message.clientMessageId,
    });
    if (!sent) {
      window.clearTimeout(timer);
      void fallbackSend(activeConversation, message.text, message.clientMessageId, key);
    }
  }, [activeConversation, fallbackSend, sendMessage]);

  const handleSearch = useCallback(async (value: string) => {
    setQuery(value);
    if (!value.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      const [users, groups] = await Promise.all([
        userAPI.searchUsers(value, 10),
        conservationAPI.searchConversations(value, 10),
      ]);
      const mappedUsers = users.map((user, index) => toSearchUserConversation(user, index));
      const mappedGroups = groups.map((group, index) => currentUser ? toConversation(group, currentUser.id, index + 10) : null).filter((item): item is Conversation => item !== null);
      setSearchResults([...mappedUsers, ...mappedGroups]);
    } catch {
      setSearchResults([]);
    }
  }, [currentUser]);

  const handleUpload = async (file: File) => {
    if (!activeConversation?.conversationId) return;
    const request = file.type.startsWith("image/")
      ? messageAPI.uploadImage(activeConversation.conversationId, file)
      : file.type.startsWith("video/")
        ? messageAPI.uploadVideo(activeConversation.conversationId, file)
        : messageAPI.uploadFile(activeConversation.conversationId, file);
    await request.catch(() => setError("Không thể tải tệp lên."));
  };

  const handleLogout = async () => {
    try {
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) await authAPI.logout(refreshToken);
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      navigate("/login");
    }
  };

  const currentUserName = currentUser?.display_name || currentUser?.username || "User";
  const activeHasMore = activeKey ? Boolean(nextCursorByConversation[activeKey]) : false;

  return (
    <div className="flex h-screen w-full bg-white text-gray-900">
      <ChatSidebar
        conversations={visibleConversations}
        activeId={activeId ?? ""}
        onSelect={(id) => setActiveId(String(id))}
        query={query}
        onQueryChange={setQuery}
        onSearch={handleSearch}
        currentUserName={currentUserName}
        currentUserInitials={getInitials(currentUserName)}
        currentUserAvatar={currentUser?.avatar_url}
        onSettingsClick={() => navigate("/profile")}
        onLogout={() => void handleLogout()}
      />
      <main className="flex-1 flex flex-col min-w-0">
        {loadingConversations && <p className="p-4 text-sm text-gray-500">Đang tải hội thoại...</p>}
        {error && <p className="p-4 text-sm text-red-500">{error}</p>}
        <ChatWindow
          conversation={activeConversation}
          messages={activeMessages}
          draft={draft}
          onDraftChange={setDraft}
          onSend={handleSend}
          onUpload={handleUpload}
          onLoadMore={() => activeConversation?.conversationId && void loadMessages(activeConversation.conversationId, true)}
          hasMore={activeHasMore}
          loadingMessages={loadingMessages}
          onRetry={handleRetry}
        />
        <span className="sr-only">Socket: {socketStatus}</span>
      </main>
    </div>
  );
}
