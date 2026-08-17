import { Plus, SquarePen } from "lucide-react";

export default function SidebarHeader() {
  return (
    <div className="flex items-center justify-between px-5 pt-4 pb-2">
      <div></div>
      <div className="flex items-center gap-3 text-gray-400">
        <button aria-label="Cuộc trò chuyện mới" className="hover:text-white transition">
          <Plus className="w-5 h-5" />
        </button>
        <button aria-label="Soạn tin nhắn" className="hover:text-white transition">
          <SquarePen className="w-[18px] h-[18px]" />
        </button>
      </div>
    </div>
  );
}