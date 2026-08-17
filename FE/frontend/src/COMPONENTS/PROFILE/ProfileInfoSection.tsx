import type { LucideIcon } from "lucide-react";

interface InfoItem {
  icon: LucideIcon;
  label: string;
  value: string;
}

interface ProfileInfoSectionProps {
  items: InfoItem[];
}

export default function ProfileInfoSection({ items }: ProfileInfoSectionProps) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <p className="text-xs font-semibold text-gray-400 tracking-wide px-5 pt-4 pb-2">
        THÔNG TIN
      </p>
      {items.map((item, i) => (
        <div
          key={item.label}
          className={`flex items-center gap-3 px-5 py-3.5 ${
            i !== items.length - 1 ? "border-b border-gray-50" : ""
          }`}
        >
          <div className="w-9 h-9 rounded-full bg-indigo-50 flex items-center justify-center shrink-0">
            <item.icon className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-gray-900">{item.label}</p>
            <p className="text-sm text-gray-400 truncate">{item.value}</p>
          </div>
        </div>
      ))}
    </div>
  );
}