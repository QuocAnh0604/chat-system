import type { Conversation, Message } from "../../types/chat";
import ChatHeader from "./ChatHeader";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";

interface ChatWindowProps {
  conversation: Conversation | null;
  messages: Message[];
  draft: string;
  onDraftChange: (value: string) => void;
  onSend: () => void;
  onUpload: (file: File) => void;
  onLoadMore?: () => void;
  hasMore?: boolean;
  loadingMessages?: boolean;
  onRetry?: (message: Message) => void;
}

export default function ChatWindow({ conversation, messages, draft, onDraftChange, onSend, onUpload, onLoadMore, hasMore, loadingMessages, onRetry }: ChatWindowProps) {
  if (!conversation) {
    return <section className="flex-1 flex items-center justify-center text-gray-400">Chưa có cuộc trò chuyện</section>;
  }
  return (
    <section className="flex-1 flex flex-col min-w-0">
      <ChatHeader conversation={conversation} />
      <MessageList
        messages={messages}
        activeId={conversation.id}
        senderColor={conversation.color}
        senderInitials={conversation.initials}
        onLoadMore={onLoadMore}
        hasMore={hasMore}
        loading={loadingMessages}
        onRetry={onRetry}
      />
      <MessageInput value={draft} onChange={onDraftChange} onSend={onSend} onUpload={onUpload} />
    </section>
  );
}
