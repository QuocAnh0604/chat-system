import { Search } from "lucide-react";

interface SidebarSearchProps {
  value: string;
  onChange: (value: string) => void;
}

export default function SidebarSearch({ value, onChange }: SidebarSearchProps) {
  return (
    <div className="px-5 mb-2">
      <div className="relative">
        <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Tìm kiếm..."
          className="w-full bg-gray-900 text-sm placeholder:text-gray-500 rounded-xl pl-9 pr-3 py-2.5 outline-none border border-gray-800 focus:border-gray-700"
        />
      </div>
    </div>
  );
}