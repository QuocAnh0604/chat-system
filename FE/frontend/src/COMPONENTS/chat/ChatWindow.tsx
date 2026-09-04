import type { Conversation, Message } from "../../types/chat";
import ChatHeader from "./ChatHeader";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";

interface ChatWindowProps {
  conversation: Conversation;
  messages: Message[];
  draft: string;
  onDraftChange: (value: string) => void;
  onSend: () => void;
  onUpload: (file: File) => void;
}

export default function ChatWindow({ conversation, messages, draft, onDraftChange, onSend, onUpload }: ChatWindowProps) {
  return (
    <section className="flex-1 flex flex-col min-w-0">
      <ChatHeader conversation={conversation} />
      <MessageList
        messages={messages}
        activeId={conversation.id}
        senderColor={conversation.color}
        senderInitials={conversation.initials}
      />
      <MessageInput value={draft} onChange={onDraftChange} onSend={onSend} onUpload={onUpload} />
    </section>
  );
}