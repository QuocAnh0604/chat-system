import type { Conversation } from "../../types/chat";
import ConversationItem from "./ConversationItem";

interface ConversationListProps {
  conversations: Conversation[];
  activeId: number | string;
  onSelect: (id: number | string) => void;
}

export default function ConversationList({ conversations, activeId, onSelect }: ConversationListProps) {
  return (
    <div className="flex-1 overflow-y-auto">
      {conversations.map((c) => (
        <ConversationItem
          key={c.id}
          conversation={c}
          isActive={c.id === activeId}
          onClick={() => onSelect(c.id)}
        />
      ))}
    </div>
  );
}