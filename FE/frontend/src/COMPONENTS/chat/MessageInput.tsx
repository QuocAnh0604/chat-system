import { Image as ImageIcon, Smile, Mic } from "lucide-react";
import type { KeyboardEvent } from "react";

interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
}

export default function MessageInput({ value, onChange, onSend }: MessageInputProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="flex items-center gap-3 px-6 py-4 border-t border-gray-200">
      <button aria-label="Gửi hình ảnh" className="text-gray-400 hover:text-gray-600 transition shrink-0">
        <ImageIcon className="w-5 h-5" />
      </button>
      <button aria-label="Chèn biểu tượng cảm xúc" className="text-gray-400 hover:text-gray-600 transition shrink-0">
        <Smile className="w-5 h-5" />
      </button>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Nhập tin nhắn..."
        className="flex-1 bg-gray-100 rounded-full px-4 py-2.5 text-sm outline-none placeholder:text-gray-400 focus:ring-2 focus:ring-indigo-200"
      />
      <button aria-label="Ghi âm" className="text-gray-400 hover:text-gray-600 transition shrink-0">
        <Mic className="w-5 h-5" />
      </button>
    </div>
  );
}