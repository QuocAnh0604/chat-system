import type { LucideIcon } from "lucide-react";
import Toggle from "../common/Toggle";

interface SettingsToggleRowProps {
  icon: LucideIcon;
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
  bordered?: boolean;
}

export default function SettingsToggleRow({
  icon: Icon,
  label,
  checked,
  onChange,
  bordered = true,
}: SettingsToggleRowProps) {
  return (
    <div
      className={`flex items-center justify-between gap-3 px-5 py-3.5 ${
        bordered ? "border-b border-gray-50" : ""
      }`}
    >
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-9 h-9 rounded-full bg-indigo-50 flex items-center justify-center shrink-0">
          <Icon className="w-4 h-4 text-indigo-500" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-900">{label}</p>
          <p className="text-sm text-gray-400">{checked ? "Đang bật" : "Đang tắt"}</p>
        </div>
      </div>
      <Toggle checked={checked} onChange={onChange} label={label} />
    </div>
  );
}