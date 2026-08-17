import { Camera } from "lucide-react";

interface ProfileHeaderProps {
  name: string;
  bio: string;
  initials: string;
  isOnline?: boolean;
}

export default function ProfileHeader({ name, bio, initials, isOnline = true }: ProfileHeaderProps) {
  return (
    <div className="relative">
      <div
        className="h-32 w-full bg-gradient-to-r from-indigo-500 to-violet-400"
        style={{
          backgroundImage:
            "radial-gradient(rgba(255,255,255,0.35) 1px, transparent 1px), linear-gradient(to right, #6366f1, #a78bfa)",
          backgroundSize: "16px 16px, 100% 100%",
        }}
      />
      <div className="flex flex-col items-center -mt-12">
        <div className="relative">
          <div className="w-24 h-24 rounded-full bg-indigo-500 border-4 border-white flex items-center justify-center text-white text-2xl font-bold shadow-sm">
            {initials}
          </div>
          {isOnline && (
            <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-emerald-400 border-2 border-white" />
          )}
          <button
            aria-label="Đổi ảnh đại diện"
            className="absolute bottom-0 right-0 w-7 h-7 rounded-full bg-white border border-gray-200 flex items-center justify-center text-gray-500 hover:text-gray-700 shadow-sm"
          >
            <Camera className="w-3.5 h-3.5" />
          </button>
        </div>

        <h1 className="text-lg font-bold text-gray-900 mt-3">{name}</h1>
        <p className="text-sm text-gray-500 mt-1">{bio}</p>
      </div>
    </div>
  );
}