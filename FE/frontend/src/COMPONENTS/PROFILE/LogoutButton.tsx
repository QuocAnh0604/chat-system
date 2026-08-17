import { LogOut } from "lucide-react";

interface LogoutButtonProps {
  onLogout?: () => void;
}

export default function LogoutButton({ onLogout }: LogoutButtonProps) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <button
        onClick={onLogout}
        className="w-full flex items-center gap-3 px-5 py-3.5 hover:bg-red-50/60 transition text-left"
      >
        <div className="w-9 h-9 rounded-full bg-red-50 flex items-center justify-center shrink-0">
          <LogOut className="w-4 h-4 text-red-500" />
        </div>
        <p className="text-sm font-semibold text-red-500">Đăng xuất</p>
      </button>
    </div>
  );
}