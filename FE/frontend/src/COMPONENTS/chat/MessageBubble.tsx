import { Check, CheckCheck } from "lucide-react";
import type { Message } from "../../types/chat";

interface MessageBubbleProps {
  message: Message;
  senderColor: string;
  senderInitials: string;
}

export default function MessageBubble({ message: m, senderColor, senderInitials }: MessageBubbleProps) {
  return (
    <div className={`flex ${m.from === "me" ? "justify-end" : "items-end gap-2"}`}>
      {m.from === "them" && (
        <div
          className={`w-7 h-7 rounded-full ${senderColor} flex items-center justify-center text-[10px] font-semibold text-white shrink-0`}
        >
          {senderInitials}
        </div>
      )}
      <div className={`flex flex-col ${m.from === "me" ? "items-end" : "items-start"} max-w-[65%]`}>
        <div
          className={`px-4 py-2.5 text-sm leading-relaxed rounded-2xl ${
            m.from === "me"
              ? "bg-indigo-500 text-white rounded-br-md"
              : "bg-white text-gray-800 border border-gray-200 rounded-bl-md"
          }`}
        >
          {m.text}
        </div>
        <div className="flex items-center gap-1 mt-1 px-1">
          <span className="text-[11px] text-gray-400">{m.time}</span>
          {m.from === "me" &&
            (m.seen ? (
              <CheckCheck className="w-3.5 h-3.5 text-indigo-400" />
            ) : (
              <Check className="w-3.5 h-3.5 text-gray-400" />
            ))}
        </div>
      </div>
    </div>
  );
}