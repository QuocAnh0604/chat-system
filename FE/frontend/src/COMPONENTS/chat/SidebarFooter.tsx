import { useState } from "react";
import { Settings, LogOut } from "lucide-react";

interface SidebarFooterProps {
  name: string;
  initials: string;
  avatarUrl?: string | null;
  status?: string;
  onSettingsClick?: () => void;
  onLogout?: () => void;
}

export default function SidebarFooter({
  name,
  initials,
  avatarUrl,
  status = "Đang hoạt động",
  onSettingsClick,
  onLogout,
}: SidebarFooterProps) {
  const [imageError, setImageError] = useState(false);
  const hasValidAvatar = Boolean(avatarUrl && avatarUrl.trim() && !imageError);

  return (
    <div className="flex items-center justify-between px-5 py-4 border-t border-gray-800">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-9 h-9 rounded-full bg-indigo-500 flex items-center justify-center text-xs font-semibold shrink-0 overflow-hidden">
          {hasValidAvatar && avatarUrl ? (
            <img
              src={avatarUrl}
              alt={name}
              className="w-full h-full object-cover"
              onError={() => setImageError(true)}
            />
          ) : (
            <span>{initials}</span>
          )}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold truncate">{name}</p>
          <p className="text-xs text-emerald-400 truncate">{status}</p>
        </div>
      </div>
      <div className="flex items-center gap-3 text-gray-400 shrink-0">
        <button aria-label="Cài đặt" onClick={onSettingsClick} className="hover:text-white transition">
          <Settings className="w-[18px] h-[18px]" />
        </button>
        <button aria-label="Đăng xuất" onClick={onLogout} className="hover:text-red-400 transition">
          <LogOut className="w-[18px] h-[18px]" />
        </button>
      </div>
    </div>
  );
}