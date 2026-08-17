import type { Conversation } from "../../types/chat";

interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  onClick: () => void;
}

export default function ConversationItem({ conversation: c, isActive, onClick }: ConversationItemProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 text-left transition border-b border-gray-800/50 ${
        isActive ? "bg-gray-800/80" : "hover:bg-gray-800/40"
      }`}
    >
      {/* Avatar */}
      <div className="relative shrink-0">
        <div
          className={`w-11 h-11 rounded-full ${c.color} flex items-center justify-center text-xs font-semibold text-white`}
        >
          {c.initials}
        </div>
        {c.online && (
          <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-gray-950" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 flex flex-col gap-0.5">
        <div className="flex items-baseline justify-between gap-2">
          <p className="text-sm font-semibold text-white truncate">{c.name}</p>
          <span className="text-[11px] text-gray-500 shrink-0">{c.time}</span>
        </div>
        <div className="flex items-center justify-between gap-2">
          <p className="text-xs text-gray-400 truncate">{c.lastMessage}</p>
          {c.unread > 0 && (
            <span className="shrink-0 min-w-[18px] h-[18px] px-1 rounded-full bg-indigo-500 text-[10px] font-bold leading-none flex items-center justify-center text-white">
              {c.unread}
            </span>
          )}
        </div>
      </div>
    </button>
  );
}