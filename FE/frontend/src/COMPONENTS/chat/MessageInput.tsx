import type { KeyboardEvent } from "react";

interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onUpload: (file: File) => void;
}

export default function MessageInput({ value, onChange, onSend, onUpload }: MessageInputProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="flex items-center gap-3 px-6 py-4 border-t border-gray-200">
      <label className="text-sm text-gray-500 hover:text-gray-700 cursor-pointer shrink-0">
        Đính kèm tệp
        <input
          type="file"
          className="sr-only"
          accept="image/*,video/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onUpload(file);
            e.target.value = "";
          }}
        />
      </label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Nhập tin nhắn..."
        className="flex-1 bg-gray-100 rounded-full px-4 py-2.5 text-sm outline-none placeholder:text-gray-400 focus:ring-2 focus:ring-indigo-200"
      />
    </div>
  );
}