import type { Conversation } from "../../types/chat";

interface ChatHeaderProps {
  conversation: Conversation;
}

export default function ChatHeader({ conversation }: ChatHeaderProps) {
  return (
    <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
      <div>
        <h2 className="text-lg font-semibold text-white">{conversation.name}</h2>
        <p className="text-sm text-gray-400">
          {conversation.online
            ? "Đang hoạt động"
            : conversation.lastSeenAt
              ? `Hoạt động lần cuối ${new Date(conversation.lastSeenAt).toLocaleString("vi-VN")}`
              : conversation.status ?? conversation.initials}
        </p>
      </div>
    </div>
  );
}
