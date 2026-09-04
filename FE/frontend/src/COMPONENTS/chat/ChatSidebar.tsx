import type { Conversation } from "../../types/chat";
import SidebarHeader from "./SidebarHeader";
import SidebarSearch from "./SidebarSearch";
import ConversationList from "./ConversationList";
import SidebarFooter from "./SidebarFooter";

interface ChatSidebarProps {
  conversations: Conversation[];
  activeId: number | string;
  onSelect: (id: number | string) => void;
  query: string;
  onQueryChange: (value: string) => void;
  onSearch: (value: string) => void;
  currentUserName: string;
  currentUserInitials: string;
  currentUserAvatar?: string | null;
  onSettingsClick?: () => void;
  onLogout?: () => void;
}

export default function ChatSidebar({
  conversations,
  activeId,
  onSelect,
  query,
  onQueryChange,
  onSearch,
  currentUserName,
  currentUserInitials,
  currentUserAvatar,
  onSettingsClick,
  onLogout,
}: ChatSidebarProps) {
  const filtered = conversations.filter((c) =>
    c.name.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <aside className="w-[300px] shrink-0 bg-gray-950 text-white flex flex-col">
      <SidebarHeader />
      <SidebarSearch value={query} onChange={onQueryChange} onSearch={onSearch} />
      <ConversationList conversations={filtered} activeId={activeId} onSelect={onSelect} />
      <SidebarFooter
        name={currentUserName}
        initials={currentUserInitials}
        avatarUrl={currentUserAvatar}
        onSettingsClick={onSettingsClick}
        onLogout={onLogout}
      />
    </aside>
  );
}