import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import userAPI from "../API/userAPI";
import authAPI from "../API/authAPI";
import conservationAPI from "../API/conservationAPI";
import messageAPI from "../API/messageAPI";
import type { Conversation, Message } from "../types/chat";
import ChatSidebar from "../COMPONENTS/chat/ChatSidebar";
import ChatWindow from "../COMPONENTS/chat/ChatWindow";

// TODO: chuyển sang data/ hoặc gọi API sau
const conversations: Conversation[] = [
  {
    id: 1,
    name: "Nguyễn Minh Anh",
    initials: "MA",
    color: "bg-indigo-500",
    lastMessage: "Tuyệt! Hẹn gặp bạn tối nay nhé 😄",
    time: "2 phút",
    unread: 3,
    online: true,
    status: "Đang hoạt động",
  },
  {
    id: 2,
    name: "Lê Quốc Hùng",
    initials: "QH",
    color: "bg-purple-500",
    lastMessage: "Dự án xong chưa vậy?",
    time: "15 phút",
    unread: 1,
    online: false,
  },
  {
    id: 3,
    name: "Phạm Thu Hà",
    initials: "TH",
    color: "bg-pink-500",
    lastMessage: "OK, mình sẽ gửi file cho bạn nhé",
    time: "1 giờ",
    unread: 0,
    online: true,
  },
  {
    id: 4,
    name: "Dev Team",
    initials: "DT",
    color: "bg-violet-500",
    lastMessage: "Meeting lúc 3h chiều nha mn",
    time: "2 giờ",
    unread: 5,
    online: false,
  },
  {
    id: 5,
    name: "Võ Thanh Tùng",
    initials: "TT",
    color: "bg-amber-500",
    lastMessage: "Bạn đã xem phim Dune 3 chưa?",
    time: "Hôm qua",
    unread: 0,
    online: false,
  },
  {
    id: 6,
    name: "Hoàng Lan Anh",
    initials: "LA",
    color: "bg-emerald-500",
    lastMessage: "Cảm ơn bạn nhiều lắm nha!",
    time: "Hôm qua",
    unread: 0,
    online: false,
  },
  {
    id: 7,
    name: "Đinh Văn Nam",
    initials: "VN",
    color: "bg-indigo-500",
    lastMessage: "Hẹn gặp lại bạn nhé 👋",
    time: "2 ngày",
    unread: 0,
    online: false,
  },
  {
    id: 8,
    name: "Bùi Thị Yến",
    initials: "TY",
    color: "bg-red-500",
    lastMessage: "Chúc bạn ngủ ngon! 🌙",
    time: "3 ngày",
    unread: 0,
    online: false,
  },
];

const initialMessages: Message[] = [
  { id: 1, from: "them", text: "Chào bạn! Bạn có khỏe không?", time: "10:00" },
  { id: 2, from: "me", text: "Mình khỏe, cảm ơn bạn! Còn bạn?", time: "10:02", seen: true },
  { id: 3, from: "them", text: "Mình cũng ổn. Dạo này bận không?", time: "10:05" },
  { id: 4, from: "me", text: "Cũng bình thường thôi 😊", time: "10:06", seen: true },
  {
    id: 5,
    from: "them",
    text: "Tối nay đi ăn không bạn? Mình muốn thử nhà hàng mới khai trương.",
    time: "10:08",
  },
  { id: 6, from: "me", text: "Nghe hay đó! Mấy giờ bạn rảnh?", time: "10:09", seen: true },
  { id: 7, from: "them", text: "Khoảng 7h tối được không?", time: "10:10" },
  { id: 8, from: "me", text: "OK được, mình sẽ đến!", time: "10:11", seen: true },
  { id: 9, from: "them", text: "Tuyệt! Hẹn gặp bạn tối nay nhé 😄", time: "10:12" },
];

const getInitials = (name: string): string => {
  const cleanName = name.trim();
  if (!cleanName) return "U";

  const words = cleanName.split(/\s+/).filter(Boolean);
  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }

  return `${words[0][0]}${words[1][0]}`.toUpperCase();
};

const colorPalette = [
  "bg-indigo-500",
  "bg-purple-500",
  "bg-pink-500",
  "bg-violet-500",
  "bg-amber-500",
  "bg-emerald-500",
  "bg-red-500",
];

const buildSearchConversation = (item: any, index: number): Conversation => {
  const isGroup = Boolean(item.is_group || item.role);
  const name = item.display_name ?? item.title ?? item.name ?? "Unknown";
  const avatarUrl = item.avatar_url ?? "";

  return {
    id: item.id ?? `${isGroup ? "group" : "user"}-${index}`,
    conversationId: isGroup ? item.id : undefined,
    targetUserId: isGroup ? undefined : item.id,
    name,
    initials: avatarUrl ? getInitials(name) : getInitials(name),
    color: colorPalette[index % colorPalette.length],
    lastMessage: isGroup ? "Nhóm chat" : "Liên hệ trực tiếp",
    time: "Mới",
    unread: 0,
    online: item.is_active ?? true,
    status: isGroup ? "Nhóm" : "Đang hoạt động",
  };
};

export default function ChatHomePage() {
  const navigate = useNavigate();
  const [activeId, setActiveId] = useState<number | string>(1);
  const [query, setQuery] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [draft, setDraft] = useState<string>("");
  const [currentUserName, setCurrentUserName] = useState<string>("User");
  const [currentUserAvatar, setCurrentUserAvatar] = useState<string>("");
  const [currentUserInitials, setCurrentUserInitials] = useState<string>("U");
  const [searchResults, setSearchResults] = useState<Conversation[]>([]);
  const searchRequestId = useRef(0);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const user = await userAPI.getMe();
        const displayName = user.display_name || user.username || "User";
        const avatar = user.avatar_url?.trim() || "";

        setCurrentUserName(displayName);
        setCurrentUserAvatar(avatar);
        setCurrentUserInitials(getInitials(displayName));
      } catch (error) {
        console.error("Không thể lấy thông tin người dùng:", error);
      }
    };

    fetchCurrentUser();
  }, []);

  const handleSearch = async (value: string) => {
    setQuery(value);
    const trimmedQuery = value.trim();
    const requestId = ++searchRequestId.current;

    if (!trimmedQuery) {
      setSearchResults([]);
      return;
    }

    try {
      const [usersResponse, conversationsResponse] = await Promise.all([
        userAPI.searchUsers(trimmedQuery, 10).catch(() => []),
        conservationAPI.searchConversations(trimmedQuery, 10).catch(() => []),
      ]);

      if (requestId !== searchRequestId.current) return;

      const merged = [
        ...(Array.isArray(usersResponse) ? usersResponse : []).map((user, index) =>
          buildSearchConversation({ ...user, is_group: false }, index)
        ),
        ...(Array.isArray(conversationsResponse) ? conversationsResponse : []).map((conversation, index) =>
          buildSearchConversation(conversation, index + 20)
        ),
      ];

      setSearchResults(merged.slice(0, 20));
    } catch (error) {
      console.error("Search failed:", error);
      if (requestId === searchRequestId.current) {
        setSearchResults([]);
      }
    }
  };

  const visibleConversations = query.trim() ? searchResults.length > 0 ? searchResults : [] : conversations;
  const active = (visibleConversations.find((c) => c.id === activeId) ?? visibleConversations[0] ?? conversations[0]) as Conversation;

  const handleSend = async () => {
    const text = draft.trim();
    if (!text) return;

    try {
      const response = active.targetUserId
        ? await messageAPI.sendMessageToUser(active.targetUserId, text)
        : active.conversationId
          ? await messageAPI.sendMessage(active.conversationId, text)
          : null;
      if (!response) return;

      if (active.targetUserId && response.conversation_id) {
        setSearchResults((current) =>
          current.map((conversation) =>
            conversation.id === active.id
              ? {
                  ...conversation,
                  id: response.conversation_id,
                  conversationId: response.conversation_id,
                  targetUserId: undefined,
                }
              : conversation
          )
        );
        setActiveId(response.conversation_id);
      }
    } catch (error) {
      console.error("Could not send message:", error);
      return;
    }

    const time = new Date().toLocaleTimeString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
    });
    setMessages((prev) => [
      ...prev,
      { id: prev.length + 1, from: "me", text, time, seen: false },
    ]);
    setDraft("");
  };

  const handleUpload = async (file: File) => {
    if (!active.conversationId) {
      console.warn("Send a text message first to create this conversation.");
      return;
    }

    try {
      const uploadRequest = file.type.startsWith("image/")
        ? messageAPI.uploadImage(active.conversationId, file)
        : file.type.startsWith("video/")
          ? messageAPI.uploadVideo(active.conversationId, file)
          : messageAPI.uploadFile(active.conversationId, file);
      await uploadRequest;
    } catch (error) {
      console.error("Could not upload file:", error);
    }
  };

  const handleLogout = async () => {
    try {
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        await authAPI.logout(refreshToken);
      }
    } catch (error) {
      console.error("Logout failed:", error);
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("remember_username");
      navigate("/login");
    }
  };

  const handleSettingsClick = () => {
    navigate("/profile");
  };

  return (
    <div className="flex h-screen w-full bg-white text-gray-900">
      <ChatSidebar
        conversations={visibleConversations}
        activeId={activeId}
        onSelect={setActiveId}
        query={query}
        onQueryChange={setQuery}
        onSearch={handleSearch}
        currentUserName={currentUserName}
        currentUserInitials={currentUserInitials}
        currentUserAvatar={currentUserAvatar}
        onSettingsClick={handleSettingsClick}
        onLogout={handleLogout}
      />
      <ChatWindow
        conversation={active}
        messages={messages}
        draft={draft}
        onDraftChange={setDraft}
        onSend={handleSend}
        onUpload={handleUpload}
      />
    </div>
  );
}