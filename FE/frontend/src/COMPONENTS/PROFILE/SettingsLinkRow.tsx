import type { LucideIcon } from "lucide-react";
import { ChevronRight } from "lucide-react";

interface SettingsLinkRowProps {
  icon: LucideIcon;
  label: string;
  onClick?: () => void;
  bordered?: boolean;
}

export default function SettingsLinkRow({
  icon: Icon,
  label,
  onClick,
  bordered = true,
}: SettingsLinkRowProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between gap-3 px-5 py-3.5 hover:bg-gray-50 transition text-left ${
        bordered ? "border-b border-gray-50" : ""
      }`}
    >
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-9 h-9 rounded-full bg-indigo-50 flex items-center justify-center shrink-0">
          <Icon className="w-4 h-4 text-indigo-500" />
        </div>
        <p className="text-sm font-semibold text-gray-900">{label}</p>
      </div>
      <ChevronRight className="w-4 h-4 text-gray-300 shrink-0" />
    </button>
  );
}