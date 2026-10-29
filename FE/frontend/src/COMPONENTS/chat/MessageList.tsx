import { useEffect, useRef } from "react";
import type { Message } from "../../types/chat";
import MessageBubble from "./MessageBubble";

interface MessageListProps {
  messages: Message[];
  activeId: number | string;
  senderColor: string;
  senderInitials: string;
  onLoadMore?: () => void;
  hasMore?: boolean;
  loading?: boolean;
  onRetry?: (message: Message) => void;
}

export default function MessageList({ messages, activeId, senderColor, senderInitials, onLoadMore, hasMore = false, loading = false, onRetry }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, activeId]);

  return (
    <div
      ref={scrollRef}
      onScroll={(event) => {
        if (event.currentTarget.scrollTop <= 10 && hasMore && !loading) onLoadMore?.();
      }}
      className="flex-1 overflow-y-auto px-6 py-5 bg-gray-50/50"
    >
      {loading && <p className="text-center text-xs text-gray-400 mb-3">Đang tải tin nhắn...</p>}
      <p className="text-center text-xs text-gray-400 mb-6">Hôm nay</p>

      <div className="flex flex-col gap-4">
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} senderColor={senderColor} senderInitials={senderInitials} onRetry={() => onRetry?.(m)} />
        ))}
      </div>
    </div>
  );
}
